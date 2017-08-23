from lxml import etree
from lxml.builder import ElementMaker
import datetime
import os.path

class CorrectXML:

    def __init__(self, f):
        """ corrects the typical errors in the files from the Harvard Greek-Arabic project (http://www.graeco-arabic-studies.org/home.html)

        :param f: the name of the file to be edited
        :type f: str
        """
        try:
            self.root = etree.parse(f).getroot()
        except Exception as E:
            print(f, E)
            return
        self.ns = {'tei': 'http://www.tei-c.org/ns/1.0',
                   'xml': 'http://www.w3.org/XML/1998/namespace'}
        self.file = f
        self.filename = f.split('/')[-1]
        self.lang = 'grc'

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
        text = text.replace('></teiHeader>', '>\n</teiHeader>')
        text = text.replace('><', '>\n<')
        text = xml_header + text
        return text

    def correct_header(self):
        """ Copies the information from the original teiHeader into a new, Epidoc-compliant teiHeader

        """
        self.root.tag = 'TEI'
        self.root.set('xmlns', "http://www.tei-c.org/ns/1.0")
        E = ElementMaker()
        keyboarding = E.respStmt(
            E.persName("Digital Divide Data", {'{http://www.w3.org/XML/1998/namespace}id': 'DDD'}),
            E.resp('Keyboarding')
        )
        new_header = E.teiHeader(
            E.fileDesc(
                E.titleStmt(),
                E.publicationStmt(
                    E.authority("A Digital Corpus for Graeco-Arabic Studies, funded by the Andrew W. Mellon Foundation"),
                    E.publisher("University of Leipzig"),
                    E.pubPlace("Germany"),
                    E.idno(self.filename, {'type': 'filename'}),
                    E.availability(
                        E.licence("Available under a Creative Commons Attribution-ShareAlike 4.0 International License",
                                  {'target': "https://creativecommons.org/licenses/by-sa/4.0/"})
                    ),
                    E.date(str(datetime.datetime.now().year))
                ),
                E.sourceDesc()
            ),
            E.encodingDesc(
                E.p('The following text is encoded in accordance with EpiDoc standards and with the CTS/CITE Architecture.'),
                E.refsDecl(
                    E.cRefPattern({'n': 'section',
                                   'matchPattern': '(\w+).(\w+).(\w+)',
                                   'replacementPattern': "#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2']/tei:div[@n='$3'])"}),
                    E.cRefPattern({'n': 'chapter',
                                   'matchPattern': '(\w+).(\w+)',
                                   'replacementPattern': "#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2'])"}),
                    E.cRefPattern({'n': 'book',
                                   'matchPattern': '(\w+)',
                                   'replacementPattern': "#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1'])"}),
                    {'n': 'CTS'})
            ),
            E.profileDesc()
        )
        c = self.root.xpath('/TEI/teiHeader/fileDesc/titleStmt', namespaces=self.ns)[0].getchildren()
        for x in c:
            new_header.xpath('/teiHeader/fileDesc/titleStmt')[0].append(x)
        new_header.xpath('/teiHeader/fileDesc/titleStmt')[0].append(keyboarding)
        c = self.root.xpath('/TEI/teiHeader/fileDesc/sourceDesc', namespaces=self.ns)[0].getchildren()
        for x in c:
            if x.tag != 'p':
                new_header.xpath('/teiHeader/fileDesc/sourceDesc')[0].append(x)
        c = self.root.xpath('/TEI/teiHeader/profileDesc', namespaces=self.ns)[0].getchildren()
        for x in c:
            for y in x.getchildren():
                y.set('ident', y.get('id'))
                del y.attrib['id']
            new_header.xpath('/teiHeader/profileDesc')[0].append(x)
        self.root.replace(self.root.xpath('/TEI/teiHeader', namespaces=self.ns)[0], new_header)

    def remove_attribs(self, element):
        """ removes all XML attributes from an element

        :param element: the element whose attributes are to be removed
        :type element: etree.Element
        """
        for a in element.keys():
            del element.attrib[a]

    def insert_edition(self):
        """ inserts a <div type="edition"> tag to enclose the text of the work

        """
        edition_tag = etree.Element('div')
        edition_tag.set('type', 'edition')
        edition_tag.set('{http://www.w3.org/XML/1998/namespace}lang', 'grc')
        edition_tag.set('n', 'urn:cts:greekLit:{}'.format(self.filename.replace('.xml', '')))
        body = self.root.xpath('/TEI/text/body')[0]
        children = list(body)
        # somehow the following loop also removes the children from body. I don't know why.
        for c in children:
            edition_tag.append(c)
        body.append(edition_tag)

    def replace_divX(self):
        """ replaces all div1, div2, etc., with regular <div> tags,
            moving all of the attributes to the correct one in the new tag

        """
        for number in ['//div1', '//div2', '//div3', '//div4']:
            for d in self.root.xpath(number):
                new_div = etree.Element('div')
                new_div.set('type', 'textpart')
                for a in d.keys():
                    if a == "type":
                        new_div.set('subtype', d.get('type'))
                    else:
                        new_div.set(a, d.get(a))
                for c in list(d):
                    new_div.append(c)
                new_div.text = d.text
                new_div.tail = d.tail
                #print(d.text, new_div.text)
                d.getparent().replace(d, new_div)

    def write_cts_files(self):
        E = ElementMaker(namespace='http://chs.harvard.edu/xmlns/cts',
                         nsmap={'ti': 'http://chs.harvard.edu/xmlns/cts',
                                'xml': 'http://www.w3.org/XML/1998/namespace'})
        group_path = '/'.join(self.file.split('/')[:-2])
        work_path = '/'.join(self.file.split('/')[:-1])
        author = self.root.xpath('/TEI/teiHeader/fileDesc/titleStmt/author')[0].text
        title = self.root.xpath('/TEI/teiHeader/fileDesc/titleStmt/title')[0].text
        urn = self.root.xpath('/TEI/text/body/div')[0].get('n')
        if not os.path.isfile('{}/__cts__.xml'.format(work_path)):
            if not os.path.isfile('{}/__cts__.xml'.format(group_path)):
                author_cts = E.textgroup(
                    E.groupname(
                        author,
                        {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}
                    ),
                    {'urn': '{}'.format(urn.split('.')[0])}
                )
                with open('{}/__cts__.xml'.format(group_path), mode='w') as f:
                    f.write(etree.tostring(author_cts, encoding='unicode', pretty_print=True))
            work_cts = E.work(
                E.title(title,
                        {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}),
                E.edition(
                    E.label(title,
                            {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}
                            ),
                    E.description(
                        '{}, {}'.format(author, title),
                        {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}
                    ),
                    {'workUrn': '.'.join(urn.split('.')[:-1]), 'urn': urn}
                ),
                {'groupUrn': urn.split('.')[0], 'urn': '.'.join(urn.split('.')[:-1]),
                 "{http://www.w3.org/XML/1998/namespace}lang": self.lang}
            )
            with open('{}/__cts__.xml'.format(work_path), mode='w') as f:
                f.write(etree.tostring(work_cts, encoding='unicode', pretty_print=True))
        else:
            root = etree.parse('{}/__cts__.xml'.format(work_path)).getroot()
            edition_cts = E.edition(
                E.label(title,
                        {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}
                        ),
                E.description(
                    '{}, {}'.format(author, title),
                    {"{http://www.w3.org/XML/1998/namespace}lang": 'eng'}
                ),
                {'workUrn': '.'.join(urn.split('.')[:-1]), 'urn': urn}
            )
            root.append(edition_cts)
            text = etree.tostring(root, encoding='unicode', pretty_print=True)
            text = text.replace('><', '>\n<')
            with open('{}/__cts__.xml'.format(work_path), mode='w') as f:
                f.write(text)

    def pipeline(self):
        """ a convenience function to run all steps

        """
        self.correct_header()
        self.remove_attribs(self.root.xpath('/TEI/text')[0])
        self.insert_edition()
        self.replace_divX()
        with open(self.file, mode='w') as f:
            f.write(self.reformat_XML(self.root))
        self.write_cts_files()