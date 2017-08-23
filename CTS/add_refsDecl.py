__author__ = 'matt'

from lxml import etree
from lxml.builder import ElementMaker
from collections import defaultdict
from glob import glob
from os.path import isdir, basename, splitext
import os
from re import search, sub
import multiprocessing


class CTS_refs:
    def __init__(self, orig_dir, tsv_file, filename_col, author_col, uri_col, title_col, urn_col, levels_col, root_tag, lang):
        """

        :param orig_dir: the directory with the XML files to be edited
        :type orig_dir: str
        :param tsv_file: the path and filename for the TSV file with the information about the individual works
        :type tsv_file: str
        :param filename_col: the column in the TSV file that contains the filename in which the work is contained
        :type filename_col: int
        :param author_col: the column in the TSV file with the author's name
        :type author_col: int
        :param uri_col: the column in the TSV file with the work ID (not the full URN but only {authorID}.{workID})
        :type uri_col: int
        :param title_col: the column in the TSV file with the work's title
        :type title_col: int
        :param urn_col: the column in the TSV file with the edition's full URN (e.g., urn:cts:latinLit:stoa0270.stoa001.opp-lat1)
        :type urn_col: int
        :param levels_col: the column in the TSV file with the names of the citation levels
        :type levels_col: int
        :param root_tag: the root tag in the XML document, normally 'TEI'
        :type root_tag: str
        :param lang: the xml:lang code for the original language of the work (e.g., 'lat', 'grc')
        :type lang: str
        :return:
        :rtype:
        """
        with open(tsv_file) as f:
            lines = f.read().split('\n')
        self.refsD = defaultdict(dict)
        # assumes a header line. Delete [1:] if no header line exists.
        for line in lines[1:]:
            try:
                k = line.split('\t')[filename_col].replace(' ', '')
                if k:
                    '''if uri_col:
                        k = '-'.join([volume, line.split('\t')[uri_col]])
                        if k in self.refsD.keys():
                            k += '.1'
                    else:
                        uri = '.'.join(line.split('\t')[urn_col].split(':')[-1].split('.')[:-1])
                        k = '-'.join([volume, uri])
                        if k in self.refsD.keys():
                            k += '.1'
                    '''
                    self.refsD[k]['levels'] = line.split('\t')[levels_col].split(', ')
                    self.refsD[k]['urn'] = line.split('\t')[urn_col]
                    self.refsD[k]['title'] = line.split('\t')[title_col]
                    self.refsD[k]['author'] = line.split('\t')[author_col]
                    self.refsD[k]['uri'] = line.split('\t')[uri_col].split(':')[-1]
            except Exception as E:
                print(len(line.split('\t')), E)
                continue
        self.root_tag = root_tag
        self.orig_dir = orig_dir
        self.lang = lang
        self.not_changed = []

    def add_refsDecl(self):
        for uri in self.refsD:
            RD = etree.Element('refsDecl')
            RD.set('n', 'CTS')
            for i, level in enumerate(self.refsD[uri]['levels']):
                if i == 0:
                    mp = '(.+)'
                    if level.lower() == 'line':
                        rp = "#xpath(/tei:{0}/tei:text/tei:body/tei:div/tei:l[@n='$1'])".format(self.root_tag, level.lower())
                    elif level.lower() == 'p':
                        rp = "#xpath(/tei:{0}/tei:text/tei:body/tei:div/tei:p[@n='$1'])".format(self.root_tag, level.lower())
                    else:
                        rp = "#xpath(/tei:{0}/tei:text/tei:body/tei:div/tei:div[@n='$1'])".format(self.root_tag, level.lower())
                c = etree.Element('cRefPattern')
                if level.lower() == 'p':
                    c.set('n', 'paragraph')
                else:
                    c.set('n', level.lower())
                c.set('matchPattern', mp)
                c.set('replacementPattern', rp)
                RD.insert(0, c)
                mp += '.(.+)'
                # I need to insert the lower levels of reference at position 0.
                try:
                    if self.refsD[uri]['levels'][i + 1].lower() == 'line':
                        rp = rp.replace(')', "/tei:l[@n='${1}'])".format(self.refsD[uri]['levels'][i + 1].lower(), i + 2))
                    elif self.refsD[uri]['levels'][i + 1].lower() == 'p':
                        rp = rp.replace(')', "/tei:p[@n='${1}'])".format(self.refsD[uri]['levels'][i + 1].lower(), i + 2))
                    else:
                        rp = rp.replace(')', "/tei:div[@n='${1}'])".format(self.refsD[uri]['levels'][i + 1].lower(), i + 2))
                except IndexError:
                    continue
            self.refsD[uri]['refsDecl'] = RD

    def create_dir_structure(self):
        data_dir = '{}/data'.format(self.orig_dir)
        os.makedirs(data_dir)
        for k in self.refsD.keys():
            try:
                author, work = self.refsD[k]['uri'].split('.')
            except ValueError:
                print('No URI for {}'.format(k))
                continue
            try:
                os.makedirs('{0}/{1}/{2}'.format(data_dir, author, work))
            except OSError as E:
                print(k, E)
                continue

    def insert_refsDecl(self, root, uri, file):
        """
        inserts the refsDecl constructed in self.add_refsDecl to the teiHeader
        :param root: the XML tree
        :type root: etree.Element
        :param uri: the URI for the work represented in the file
        :type uri: str
        :param file: the XML filename
        :type file: str
        :return: new root
        :rtype: etree.Element
        """
        for decl in root.xpath('//tei:encodingDesc/tei:refsDecl', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            p = decl.getparent()
            p.remove(decl)
        try:
            root.xpath('//tei:encodingDesc', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].append(self.refsD[uri]['refsDecl'])
        except KeyError:
            self.not_changed.append('{}, bad URI'.format(file))
            pass
        except IndexError:
            self.not_changed.append('{}, no encodingDesc'.format(file))
            pass
        return root

    def insert_URN(self, root, uri, file):
        """
        inserts the correct URN in the @n attribute of the <div type="edition" node
        :param root: the XML tree
        :type root: etree.Element
        :param uri: the URI for the work represented in the file
        :type uri: str
        :param file: the XML filename
        :type file: str
        :return: new root
        :rtype: etree.Element
        """
        try:
            root.xpath('//tei:div[@type="edition"]', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].set('n', self.refsD[uri]['urn'])
        except IndexError:
            self.not_changed.append('{}, URN not changed'.format(file))
        return root

    def remove_div_subtype_work(self, root, uri, file):
        """
        removes the <div type="textpart" subtype="work"> node
        :param root: the XML tree
        :type root: etree.Element
        :param uri: the URI for the work represented in the file
        :type uri: str
        :param file: the XML filename
        :type file: str
        :return: new root
        :rtype: etree.Element
        """
        try:
            c = root.xpath('//tei:div[@type="textpart" and @subtype="work"]', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].getchildren()
            p = root.xpath('//tei:div[@type="textpart" and @subtype="work"]', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].getparent()
            p.remove(root.xpath('//tei:div[@type="textpart" and @subtype="work"]', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0])
            for x in c:
                p.append(x)
        except IndexError:
            self.not_changed.append('{}, no <div subtype="work" to remove'.format(file))
        return root

    def insert_teiHeader(self, root, uri, file):
        """
        replaces the root node's first child node with teiHeader and fills it with the original child's contents
        :param root: the XML tree
        :type root: etree.Element
        :param uri: the URI for the work represented in the file
        :type uri: str
        :param file: the XML filename
        :type file: str
        :return: new root
        :rtype: etree.Element
        """
        try:
            c = root[0].getchildren()
            root.replace(root[0], etree.Element('teiHeader'))
            for x in c:
                root[0].append(x)
            try:
                titleStmt = root.xpath('/tei:{}/tei:teiHeader/tei:fileDesc/tei:titleStmt'.format(self.root_tag), namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0]
                try:
                    titleStmt.xpath('./tei:title', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].set('ref', 'http://data.perseus.org/catalog/{}'.format(self.refsD[uri]['urn']))
                    titleStmt.xpath('./tei:title', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].text = self.refsD[uri]['title']
                except IndexError:
                    etree.SubElement(titleStmt, "{'http://www.tei-c.org/ns/1.0'}title", nsmap={None: 'http://www.tei-c.org/ns/1.0'}).text = self.refsD[uri]['title']
                    titleStmt.xpath('./tei:title', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].set('ref', 'http://data.perseus.org/catalog/{}'.format(self.refsD[uri]['urn']))
                try:
                    titleStmt.xpath('./tei:author', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].set('ref','http://data.perseus.org/catalog/{}'.format(''.join(self.refsD[uri]['urn'].split('.')[:-1])))
                    titleStmt.xpath('./tei:author', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].text = self.refsD[uri]['author']
                except IndexError:
                    etree.SubElement(titleStmt, "{'http://www.tei-c.org/ns/1.0'}author", nsmap={None: 'http://www.tei-c.org/ns/1.0'}).text = self.refsD[uri]['author']
                    titleStmt.xpath('./tei:author', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].set('ref', 'http://data.perseus.org/catalog/{}'.format(''.join(self.refsD[uri]['urn'].split('.')[:-1])))
            except IndexError:
                self.not_changed.append('{}, title and author information not added'.format(file))
        except IndexError:
            self.not_changed.append('{}, no teiHeader'.format(file))
        return root

    def reformat_XML(self, root):
        """
        creates a human-readable string representation of the XML tree
        :param root: the XML tree
        :type root: etree.Element
        :return: reformatted string representation of the tree
        :rtype: str
        """
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="http://www.stoa.org/epidoc/schema/latest/tei-epidoc.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
        text = etree.tostring(root, encoding='unicode', pretty_print=True)
        text = text.replace('<refsDecl n="CTS">', '  <refsDecl n="CTS">')
        text = text.replace('><cRefPattern', '>\n        <cRefPattern')
        text = text.replace('></refsDecl>', '>\n      </refsDecl>\n    ')
        text = text.replace('<teiHeader>', '<teiHeader>\n    ')
        text = text.replace('  </teiHeader>', '</teiHeader>\n')
        text = xml_header + text
        # text = text.replace('></teiHeader>', '>\n</teiHeader>')
        return text

    def make_files(self):
        for filename in self.refsD.keys():
            file = '{}/{}/{}'.format(self.orig_dir, filename.split('_')[0], filename)
            if 'none needed' in self.refsD[filename]['uri']:
                os.renames(file, '{}/NOT_NEEDED/{}'.format(self.orig_dir, filename))
                continue
            uri = self.refsD[filename]['uri']
            with open(file) as f:
                try:
                    root = etree.parse(f).getroot()
                except Exception as E:
                    print(filename, E)
                    continue
            if len(root.xpath('/tei:{0}/tei:text/tei:body'.format(self.root_tag), namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})) > 1:
                for pattern in self.refsD[filename]['refsDecl']:
                    pattern.set('replacementPattern',
                                pattern.get('replacementPattern').replace('tei:body/tei:div',
                                                                          'tei:body/tei:div[@type=\'edition\']'))
                    print('Changed {}'.format(uri))
            root = self.insert_refsDecl(root, filename, file)
            root = self.insert_URN(root, filename, file)
            root = self.remove_div_subtype_work(root, filename, file)
            root = self.insert_teiHeader(root, filename, file)

            for retract in root.xpath("//tei:div[@subtype='retractationes']", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
                retract.set('n', 'retractationes')
                retract.set('subtype', 'section')
            author = uri.split('.')[0].split('-')[-1]
            try:
                work = uri.split('.')[1]
            except IndexError:
                print(uri)
                continue
            new_d = '{0}/data/{1}/{2}'.format(self.orig_dir, author, work)
            new_file = '{0}/{1}.xml'.format(new_d, self.refsD[filename]['urn'].split(':')[-1])
            while os.path.isfile(new_file):
                new_file += '_1'
            text = self.reformat_XML(root)
            with open(new_file, mode='w') as f:
                f.write(text)
            self.write_cts_files(root, filename, author, work)
            os.remove(file)

    def write_cts_files(self, root, uri, author, work):
        E = ElementMaker(namespace='http://chs.harvard.edu/xmlns/cts', nsmap={'ti': 'http://chs.harvard.edu/xmlns/cts', 'xml': 'http://www.w3.org/XML/1998/namespace'})
        if not os.path.isfile('{0}/data/{1}/{2}/__cts__.xml'.format(self.orig_dir, author, work)):
            author_cts = E.textgroup(E.groupname(self.refsD[uri]['author'], {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}), urn='{}'.format(self.refsD[uri]['urn'].split('.')[0]))
            with open('{0}/data/{1}/__cts__.xml'.format(self.orig_dir, author), mode='w') as f:
                f.write(etree.tostring(author_cts, encoding='unicode', pretty_print=True))
            text = self.refsD[uri]['title']
            work_cts = E.work(
                E.title(text,
                        {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}),
                E.edition(
                    E.label(text, {
                        "{http://www.w3.org/XML/1998/namespace}lang": 'eng'}),
                    E.description(
                        '{}, {}'.format(self.refsD[uri]['author'], text),
                        {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}),
                    {'workUrn': '.'.join(
                        self.refsD[uri]['urn'].split('.')[:-1]),
                     'urn': self.refsD[uri]['urn']}),
                {'groupUrn': self.refsD[uri]['urn'].split('.')[0],
                 'urn': '.'.join(self.refsD[uri]['urn'].split('.')[:-1]),
                 "{http://www.w3.org/XML/1998/namespace}lang": self.lang})
            with open('{0}/data/{1}/{2}/__cts__.xml'.format(self.orig_dir,
                                                            author, work),
                      mode='w') as f:
                f.write(etree.tostring(work_cts, encoding='unicode',
                                       pretty_print=True))
        else:
            root = etree.parse(
                '{0}/data/{1}/{2}/__cts__.xml'.format(self.orig_dir, author,
                                                      work)).getroot()
            text = self.refsD[uri]['title']
            edition_cts = E.edition(
                E.label(text,
                        {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}),
                E.description('{}, {}'.format(self.refsD[uri]['author'], text),
                              {
                                  "{http://www.w3.org/XML/1998/namespace}lang": 'eng'}),
                {'workUrn': '.'.join(self.refsD[uri]['urn'].split('.')[:-1]),
                 'urn': self.refsD[uri]['urn']})
            root.append(edition_cts)
            with open('{0}/data/{1}/{2}/__cts__.xml'.format(self.orig_dir,
                                                            author, work),
                      mode='w') as f:
                f.write(etree.tostring(root, encoding='unicode',
                                       pretty_print=True))

    def run_all(self):
        """

        :return:
        :rtype:
        """
        self.add_refsDecl()
        self.create_dir_structure()
        self.make_files()


class fix_refsDecl:
    def __init__(self, orig, tests=('doubleslash', 'subtype')):
        self.files = glob('{}/*/*/*[0-9a-zA-Z].xml'.format(orig))
        self.changes = defaultdict(list)
        self.tests = tests

    def check_patterns(self, filename, r, o, n, test):
        o_res = r.xpath(o, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
        n_res = r.xpath(n, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
        if o_res != n_res:
            self.changes[filename].append({'test': test, 'old': o, 'new': n,
                                           'only_old': [(x.get('n'),
                                                         x.get('subtype'),
                                                         x.getparent()) for x
                                                        in (
                                                   set(o_res) - set(n_res))],
                                           'only_new': [(x.get('n'),
                                                         x.get('subtype'),
                                                         x.getparent()) for x
                                                        in (
                                                   set(n_res) - set(o_res))]})
            return o
        else:
            return n

    def file_loop(self):
        for file in self.files:
            try:
                root = etree.parse(file).getroot()
            except Exception as E:
                print(file, E)
                continue
            xpaths = root.xpath(
                '/tei:TEI/tei:teiHeader/tei:encodingDesc/tei:refsDecl/tei:cRefPattern',
                namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
            for p in xpaths:
                r = p.get('replacementPattern')
                x = r.replace('#xpath', '').strip('()')
                # x = sub(r'\@n=\'\$[0-9]\' and ', '', x)
                x = sub(r'n=\'\$[0-9]\'', r'n', x)
                if 'doubleslash' in self.tests:
                    pattern = x.replace('//tei', '/tei')
                    if pattern == self.check_patterns(file, root, x, pattern,
                                                      'doubleslash'):
                        p.set('replacementPattern',
                              p.get('replacementPattern').replace('//tei',
                                                                  '/tei'))
                if 'subtype' in self.tests:
                    x = p.get('replacementPattern').replace('#xpath',
                                                            '').strip('()')
                    x = sub(r'n=\'\$[0-9]\'', r'n', x)
                    pattern = sub(r'( and )?\@subtype=\'\w*?\'', '', x)
                    if pattern == self.check_patterns(file, root, x, pattern,
                                                      'subtype'):
                        p.set('replacementPattern',
                              sub(r'( and )?\@subtype=\'\w*?\'', '',
                                  p.get('replacementPattern')))
            with open(file, mode='w') as f:
                f.write(etree.tostring(root, encoding='unicode',
                                       pretty_print=True))