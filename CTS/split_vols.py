__author__ = 'matt'

from glob import glob
from lxml import etree
import os


class do_split:
    def __init__(self, orig='.', xpath='/tei:TEI/tei:text/tei:body/tei:div[@type="edition"]'):
        """

        :param orig:
        :param xpath:
        """

        self.xmls = [x for x in glob('{}/*.xml'.format(orig)) if 'grc' not in x]
        self.xpath = xpath
        self.namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
        self.results = {}
        self.orig = orig

    def extract_works(self):
        """ Goes through every XML file in self.xmls and extracts the sections that
        match self.xpath as well as the header information and save it in a
        dictionary of all of these objects
        """
        for xml in self.xmls:
            counter = 0
            try:
                root = etree.parse(xml).getroot()
            except Exception as E:
                print('File: {}, Error: {}'.format(xml, E))
                continue
            header = root.xpath('/tei:TEI/tei:teiHeader',
                                namespaces=self.namespaces)
            for work in root.xpath(self.xpath, namespaces=self.namespaces):
                work_base = ''
                if work.get('n'):
                    if len(work.get('n').split(':')) > 1:
                        title = work.get('n').split(':')[-1]
                    else:
                        title = work.get('n').replace('-', '.')
                else:
                    work_base = '{}_{}'.format(os.path.splitext(os.path.basename(xml))[0], counter)
                    try:
                        title = work[0][0].text[:20]
                    except:
                        title = 'UNKNOWN'
                if not title:
                    title = 'UNKNOWN'
                if title.startswith('LIBER'):
                    try:
                        previous = work.getprevious()
                        subtitle = previous[0][0].text
                        while subtitle.startswith('LIBER'):
                            previous = previous.getprevious()
                            subtitle = previous[0][0].text
                    except:
                        subtitle = 'UNKNOWN'
                    title = '_'.join([title, subtitle])
                    print(title)
                if work_base:
                    work_base = '_'.join([work_base, title])
                else:
                    work_base = title
                while work_base in self.results.keys():
                    work_base += '_1'
                self.results[work_base] = {'header': header, 'text': work}
                counter += 1


    def build_xml(self):
        """ Puts the different parts of the original file together into their own
        xml files
        """


    def save_works(self):
        """ Saves the different XML entities to their own files
        """
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="http://www.stoa.org/epidoc/schema/latest/tei-epidoc.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>'
        for k in self.results:
            root = etree.Element('{http://www.tei-c.org/ns/1.0}TEI',
                                 nsmap={None: 'http://www.tei-c.org/ns/1.0'})
            root.append(self.results[k]['header'][0])
            if not root.xpath('/tei:TEI/tei:teiHeader/tei:encodingDesc/tei:refsDecl', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
                refsDecl = etree.Element('{http://www.tei-c.org/ns/1.0}refsDecl',
                                     nsmap={None: 'http://www.tei-c.org/ns/1.0'})
                level3 = etree.Element('{http://www.tei-c.org/ns/1.0}cRefPattern',
                                     nsmap={None: 'http://www.tei-c.org/ns/1.0'})
                level3.set('n', '')
                level3.set('matchPattern', "(.+).(.+).(.+)")
                level3.set('replacementPattern', "#xpath(/tei:TEI/tei:text/tei:body/tei:div[@type='edition']/tei:div[@n='$1']/tei:div[@n='$2']/tei:div[@n='$3'])")
                level2 = etree.Element('{http://www.tei-c.org/ns/1.0}cRefPattern',
                                     nsmap={None: 'http://www.tei-c.org/ns/1.0'})
                level2.set('n', '')
                level2.set('matchPattern', "(.+).(.+)")
                level2.set('replacementPattern', "#xpath(/tei:TEI/tei:text/tei:body/tei:div[@type='edition']/tei:div[@n='$1']/tei:div[@n='$2'])")
                level1 = etree.Element('{http://www.tei-c.org/ns/1.0}cRefPattern',
                                     nsmap={None: 'http://www.tei-c.org/ns/1.0'})
                level1.set('n', '')
                level1.set('matchPattern', "(.+)")
                level1.set('replacementPattern', "#xpath(/tei:TEI/tei:text/tei:body/tei:div[@type='edition']/tei:div[@n='$1'])")
                refsDecl.append(level3)
                refsDecl.append(level2)
                refsDecl.append(level1)
                root.xpath('/tei:TEI/tei:teiHeader/tei:encodingDesc', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0].append(refsDecl)
            etree.SubElement(root, '{http://www.tei-c.org/ns/1.0}text')
            etree.SubElement(root[1], '{http://www.tei-c.org/ns/1.0}body')
            root[1][0].append(self.results[k]['text'])
            for x in root[1][0][0].attrib:
                del root[1][0][0].attrib[x]
            root[1][0][0].set('type', 'edition')
            root[1][0][0].set('n', k)
            os.makedirs('{}/split/{}'.format(self.orig, k.split('_')[0]), exist_ok=True)
            text = etree.tostring(root, encoding='unicode', pretty_print=True)
            text = text.replace('<refsDecl n="CTS">',
                                        '  <refsDecl n="CTS">')
            text = text.replace('><cRefPattern',
                                        '>\n        <cRefPattern')
            text = text.replace('></refsDecl>',
                                        '>\n      </refsDecl>\n    ')
            text = text.replace('<teiHeader>', '<teiHeader>\n    ')
            text = text.replace('  </teiHeader>', '</teiHeader>\n')
            text = xml_header + text
            y = '.1'
            while os.path.isfile('{}/split/{}/{}.xml'.format(self.orig, k.split('_')[0], k)):
                k += y
            with open('{}/split/{}/{}.xml'.format(self.orig, k.split('_')[0], k.replace('\t', ' ').replace('\n', ' ')), mode='w') as f:
                f.write(text)