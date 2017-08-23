__author__ = 'matt'

from lxml import etree
from glob import glob
from os.path import basename, isfile
import roman
from lxml.builder import ElementMaker

class GetMetadata:

    def __init__(self, orig, out, lang):
        """
        Cycles through all edition-level XML files in a Capitains-compliant repository structure to extract title, author, editor, publisher, publication year, and CTS URNs
        :param orig: the root data folder in which all author-level directories are found
        :type orig: str
        :param out: either "csv" or "cts"
        :type out: str
        :param lang: the three letter code for the original language of the work, e.g., "grc" or "lat"
        :type lang: str
        :return:
        :rtype:
        """
        self.orig = orig
        self.ns_dict = {'tei': 'http://www.tei-c.org/ns/1.0'}
        self.xpath_base = 'tei:teiHeader/tei:fileDesc/tei:sourceDesc//tei:biblStruct/tei:monogr'
        self.out = out
        self.lang = lang

    def get_files(self):
        """
        Gets the list of XML files from the orig folder
        :return: list of filenames
        :rtype: list
        """
        files = glob('{}/*/*/*.xml'.format(self.orig))
        self.files = sorted([x for x in files if '__cts__' not in x])

    def get_lang(self, xpath):
        """ retrieves the @xml:lang attribute for the text from the <div type="edition"> element

        :return: three-letter language tag
        :rtype: str
        """
        try:
            return self.root.xpath(xpath, namespaces=self.ns_dict)[0].get('{http://www.w3.org/XML/1998/namespace}lang')
        except:
            return None

    def get_title(self):
        """
        extracts the title from the appropriate work
        :return: the work's title, the @xml:lang attribute of the title
        :rtype: str, str
        """
        try:
            t = self.root.xpath('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title',
                                namespaces=self.ns_dict)[0].text.replace('\t', ' ').replace('\n', ' ').title()
            l = self.get_lang('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title')
            return t, l
        except:
            return 'None', None

    def get_author(self):
        """
        extracts the original author from the work
        :return: author name
        :rtype: str
        """
        try:
            a = self.root.xpath('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author',
                                namespaces=self.ns_dict)[0].text.replace('\t', ' ').replace('\n', ' ').title()
            l = self.get_lang('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author')
            return a, l
        except:
            return 'None', None

    def get_editor(self):
        """
        extracts editor's name from the work
        :return: editor's name
        :rtype: str
        """
        ed = self.root.xpath('{}/tei:editor/tei:persName/tei:name'.format(self.xpath_base), namespaces=self.ns_dict)
        l = self.get_lang('{}/tei:editor/tei:persName/tei:name'.format(self.xpath_base))
        if not ed:
            ed = self.root.xpath('{}/tei:editor'.format(self.xpath_base), namespaces=self.ns_dict)
            l = self.get_lang('{}/tei:editor'.format(self.xpath_base))
        try:
            return ed[0].text.title(), l
        except:
            return 'None', None

    def get_publisher(self):
        """
        extracts the name of the publisher from the work
        :return: publisher's name
        :rtype: str
        """
        try:
            p = self.root.xpath('{}/tei:imprint/tei:publisher'.format(self.xpath_base), namespaces=self.ns_dict)[0].text.title()
            l = self.get_lang('{}/tei:imprint/tei:publisher'.format(self.xpath_base))
            return p, l
        except:
            return 'None', None

    def get_year(self):
        """
        extracts the publication year from the work
        :return: publication year
        :rtype: str
        """
        try:
            return self.root.xpath('{}/tei:imprint/tei:date'.format(self.xpath_base), namespaces=self.ns_dict)[0].text
        except:
            return 'None'

    def get_URN(self):
        """
        extracts the CTS URN from the work
        :return: CTS URN
        :rtype: str
        """
        try:
            return self.root.xpath('tei:text/tei:body/tei:div[@type="edition"]', namespaces=self.ns_dict)[0].get('n').replace('\t', ' ').replace('\n', ' ')
        except:
            return 'None'

    def construct_CSV(self, info):
        """
        puts the information together in a CSV file and saves
        :param info: list of metadata strings for each edition
        :type info: list
        :return: CSV file
        :rtype:
        """
        with open('{}/edition_metadata.csv'.format(self.orig), mode='w') as f:
            f.write('\t'.join(['Filename', 'URN', 'Title', 'Author', 'Editor', 'Publisher', 'Publication Year']))
            for x in info:
                f.write('\n{}'.format(x))

    def get_citations(self):
        """ Finds all CTS-citable units in the file

        """
        ed = self.root.xpath('tei:text/tei:body/tei:div', namespaces=self.ns_dict)
        levels = []
        level1 = list(set(', '.join([x.tag.split('}')[1], str(x.get('subtype'))]) for x in ed[0].getchildren() if x.get('n') and x.text))
        if level1:
            level2 = list(set((', '.join([x.tag.split('}')[1], str(x.get('subtype'))]),
                               ', '.join([y.tag.split('}')[1], str(y.get('subtype'))]))
                              for x in ed[0].getchildren()
                              for y in x.getchildren()
                              if y.get('n') and x.get('n') and y.text))
            levels.append([x for x in level1])
            depth = 0
            if level2:
                level3 = list(set((', '.join([x.tag.split('}')[1], str(x.get('subtype'))]),
                                   ', '.join([y.tag.split('}')[1], str(y.get('subtype'))]),
                                   ', '.join([z.tag.split('}')[1], str(z.get('subtype'))]))
                                  for x in ed[0].getchildren()
                                  for y in x.getchildren()
                                  for z in y.getchildren()
                                  if y.get('n') and x.get('n') and z.get('n') and z.text))
                levels.append([x for x in level2])
                depth = 1
                if level3:
                    level4 = list(set((', '.join([x.tag.split('}')[1], str(x.get('subtype'))]),
                                       ', '.join([y.tag.split('}')[1], str(y.get('subtype'))]),
                                       ', '.join([z.tag.split('}')[1], str(z.get('subtype'))]),
                                       ', '.join([a.tag.split('}')[1], str(a.get('subtype'))]))
                                      for x in ed[0].getchildren()
                                      for y in x.getchildren()
                                      for z in y.getchildren()
                                      for a in z.getchildren()
                                      if y.get('n') and x.get('n') and z.get('n') and a.get('n') and a.text))
                    levels.append([x for x in level3])
                    depth = 2
                    if level4:
                        level5 = list(set((', '.join([x.tag.split('}')[1], str(x.get('subtype'))]),
                                           ', '.join([y.tag.split('}')[1], str(y.get('subtype'))]),
                                           ', '.join([z.tag.split('}')[1], str(z.get('subtype'))]),
                                           ', '.join([a.tag.split('}')[1], str(a.get('subtype'))]),
                                           ', '.join([b.tag.split('}')[1], str(b.get('subtype'))]))
                                          for x in ed[0].getchildren()
                                          for y in x.getchildren()
                                          for z in y.getchildren()
                                          for a in z.getchildren()
                                          for b in y.getchildren()
                                          if y.get('n') and x.get('n') and z.get('n') and a.get('n') and b.get('n') and b.text))
                        levels.append([x for x in level4])
                        depth = 3
                        if level5:
                            levels.append([x for x in level5])
                            depth = 4
        if levels:
            return levels[depth]
        else:
            return 'No citable units founds'

    def write_cts_files(self, urn, author, work, editor, publisher, year, lang, author_lang, title_lang, ed_lang, pub_lang):
        ns = {'ti': 'http://chs.harvard.edu/xmlns/cts',
              'xml': 'http://www.w3.org/XML/1998/namespace',
              'dc': "http://purl.org/dc/elements/1.1",
              'cpt': 'http://capitains.github.io/xmlns',
              'dct': 'http://purl.org/dc/terms/'}
        A = ElementMaker(namespace='http://chs.harvard.edu/xmlns/cts', nsmap={'ti': 'http://chs.harvard.edu/xmlns/cts'})
        E = ElementMaker(namespace='http://chs.harvard.edu/xmlns/cts', nsmap=ns)
        D = ElementMaker(namespace='http://purl.org/dc/elements/1.1', nsmap=ns)
        C = ElementMaker(namespace='http://capitains.github.io/xmlns', nsmap=ns)
        T = ElementMaker(namespace='http://purl.org/dc/terms/', nsmap=ns)
        if lang == self.lang:
            EDITION = E.edition
        else:
            EDITION = E.translation
        a_urn = urn.split('.')[-3].split(':')[-1]
        w_urn = urn.split('.')[-2]
        if not isfile('{0}/{1}/{2}/__cts__.xml'.format(self.orig, a_urn, w_urn)):
            author_cts = A.textgroup(
                A.groupname(author.title(), {"{http://www.w3.org/XML/1998/namespace}lang": author_lang}),
                urn='{}'.format(urn.split('.')[0]))
            with open('{0}/{1}/__cts__.xml'.format(self.orig, a_urn), mode='w') as f:
                f.write(etree.tostring(author_cts, encoding='unicode', pretty_print=True))
            work_cts = E.work(
                E.title(work,
                        {"{http://www.w3.org/XML/1998/namespace}lang": title_lang}),
                EDITION(
                    E.label(work, {"{http://www.w3.org/XML/1998/namespace}lang": title_lang}),
                    E.description('{}, {}, {}, {}, {}'.format(author, work, editor, publisher, year),
                                  {"{http://www.w3.org/XML/1998/namespace}lang": 'mul'}),
                    C(
                        "structured-metadata",
                        D.creator(author, {"{http://www.w3.org/XML/1998/namespace}lang": author_lang}),
                        D.title(work, {"{http://www.w3.org/XML/1998/namespace}lang": title_lang}),
                        D.contributor(editor, {"{http://www.w3.org/XML/1998/namespace}lang": ed_lang}),
                        D.publisher(publisher, {"{http://www.w3.org/XML/1998/namespace}lang": pub_lang}),
                        T.dateCopyrighted(year)
                    ),
                    {'workUrn': '.'.join(urn.split('.')[:-1]),
                     'urn': urn,
                     "{http://www.w3.org/XML/1998/namespace}lang": lang}),
                {'groupUrn': urn.split('.')[0],
                 'urn': '.'.join(urn.split('.')[:-1]),
                 "{http://www.w3.org/XML/1998/namespace}lang": self.lang})
            s = etree.tostring(work_cts, encoding='unicode', pretty_print=True)
            s = s.replace('><ti:title', '>\n  <ti:title')
            s = s.replace('><ti:edition', '>\n  <ti:edition')
            s = s.replace('><ti:label', '>\n    <ti:label')
            s = s.replace('><ti:description', '>\n    <ti:description')
            s = s.replace('></ti:edition', '>\n  </ti:edition')
            s = s.replace('></ti:work', '>\n</ti:work')
            with open('{0}/{1}/{2}/__cts__.xml'.format(self.orig, a_urn, w_urn), mode='w') as f:
                f.write(s)
        else:
            root = etree.parse('{0}/{1}/{2}/__cts__.xml'.format(self.orig, a_urn, w_urn)).getroot()
            edition_cts = E.edition(
                E.label(work, {"{http://www.w3.org/XML/1998/namespace}lang": 'lat'}),
                E.description('{}, {}, {}, {}, {}'.format(author, work, editor, publisher, year),
                              {"{http://www.w3.org/XML/1998/namespace}lang": 'lat'}),
                {'workUrn': '.'.join(urn.split('.')[:-1]),
                 'urn': urn})
            root.append(edition_cts)
            s = etree.tostring(root, encoding='unicode', pretty_print=True)
            s = s.replace('><ti:title', '>\n  <ti:title')
            s = s.replace('><ti:edition', '>\n  <ti:edition')
            s = s.replace('><ti:label', '>\n    <ti:label')
            s = s.replace('><ti:description', '>\n    <ti:description')
            s = s.replace('></ti:edition', '>\n  </ti:edition')
            s = s.replace('></ti:work', '>\n</ti:work')
            s = s.replace('\n<ti:edition', '\n  <ti:edition')
            with open('{0}/{1}/{2}/__cts__.xml'.format(self.orig, a_urn, w_urn), mode='w') as f:
                f.write(s)

    def run_all(self):
        """ Runs all functions

        """
        self.get_files()
        info = []
        for f in self.files:
            try:
                self.root = etree.parse(f).getroot()
            except:
                print('Cannot parse {}'.format(f))
                continue
            lang = self.get_lang('tei:text/tei:body/tei:div[@type="edition"]')
            if lang is None:
                lang = self.lang
            #get title and author language tags as well
            title, title_lang = self.get_title()
            if title_lang is None:
                title_lang = 'eng'
            author, author_lang = self.get_author()
            if author_lang is None:
                author_lang = 'eng'
            editor, ed_lang = self.get_editor()
            if ed_lang is None:
                ed_lang = 'eng'
            publisher, pub_lang = self.get_publisher()
            if pub_lang is None:
                pub_lang = 'eng'
            try:
                year = roman.fromRoman(self.get_year().strip('.'))
            except:
                year = self.get_year()
            urn = self.get_URN()
            scheme = self.get_citations()
            try:
                info.append('\t'.join([str(basename(f)), str(urn), str(title), str(author), str(editor), str(publisher), str(year), str(scheme)]))
                if self.out == "cts":
                    self.write_cts_files(urn, author, title, editor, publisher, str(year), lang, author_lang, title_lang, ed_lang, pub_lang)
            except Exception as E:
                print(E, f)
                print(type(basename(f)), type(urn), type(title), type(author), type(editor), type(publisher), type(year), type(scheme))
        if self.out == 'csv':
            self.construct_CSV(info)

class PLMeta(GetMetadata):

    def get_files(self):
        """
        Gets the list of XML files from the orig folder
        :return: list of filenames
        :rtype: list
        """
        files = glob('{}/*/*.xml'.format(self.orig))
        self.files = sorted([x for x in files if '__cts__' not in x])

    def get_author(self):
        """
        extracts the original author from the work
        :return: author name
        :rtype: str
        """
        try:
            return "{}\t{}".format(self.root.xpath('//tei:author', namespaces=self.ns_dict)[0].text.replace('\t', ' ').replace('\n', ' ').title(),
                                   self.root.xpath('//tei:author', namespaces=self.ns_dict)[0].get("ref").split('/')[-1])
        except:
            return 'None\tNone'

    def construct_CSV(self, info):
        """
        puts the information together in a CSV file and saves
        :param info: list of metadata strings for each edition
        :type info: list
        :return: CSV file
        :rtype:
        """
        with open('{}/edition_metadata.csv'.format(self.orig), mode='w') as f:
            f.write('\t'.join(['Filename', 'URN', 'Title', 'Author', 'Author URN', 'Editor', 'Publisher', 'Publication Year']))
            for x in info:
                f.write('\n{}'.format(x))

    def get_title(self):
        """
        extracts the title from the appropriate work
        :return: the work's title
        :rtype: str
        """
        try:
            return self.root.xpath('tei:text/tei:body/tei:div/tei:head/tei:title', namespaces=self.ns_dict)[
                0].text.replace('\t', ' ').replace('\n', ' ').title()
        except:
            return 'None'