from lxml import etree

class AddHeader:

    def __init__(self, file):
        """ A general class for replacing an old header with a new header.
            The details should be determined in the sub-classes.

        :param file: the file path of the file to change
        :type file: str
        """
        self.file = file
        self.root = etree.parse(file).getroot()
        self.ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def read_old(self):
        """ read the old header in

        :return: the teiHeader
        :rtype: etree._Element
        """
        return self.root.xpath('/tei:TEI/tei:teiHeader', namespaces=self.ns)[0]

    def replace_old(self, header):
        """

        :param header: the header to be changed
        :type header: etree._Element
        :return: the new TEI header
        :rtype: etree._Element
        """
        raise NotImplementedError("replace_old is not implemented in the base add_header class")

    def save_new(self):
        """ saves the new xml file with the new header

        """
        with open(self.file, mode="w") as f:
            f.write(etree.tostring(self.root, encoding='unicode', pretty_print=True))

    def run_all(self):
        """ a convenience function to run all steps

        """
        old_header = self.read_old()
        self.replace_old(old_header)
        self.save_new()

class First1kOld(AddHeader):

    def replace_old(self, header):
        """ replaces the header with the information for a file that was started before the beginning of First1KGreek

        :param header: the TEI header to be replaced
        :type header: etree._Element
        """
        new_header = etree.Element('titleStmt')
        fileDesc = header.xpath('tei:fileDesc', namespaces=self.ns)[0]
        for c in fileDesc.xpath('tei:titleStmt', namespaces=self.ns)[0].getchildren():
            if c.tag != '{http://www.tei-c.org/ns/1.0}respStmt':
                new_header.append(c)
        new_resps = (
            ('Gregory R. Crane', ['Editor-in-Chief, Perseus Digital Library']),
            ('Digital Divide Data', ['Corrected and encoded the text'], ['{http://www.w3.org/XML/1998/namespace}id', 'DDD']),
            ('Matt Munson', ['Project Manager (University of Leipzig), 2016 - present']),
            ('Annette Geßner', ['Project Assistant (University of Leipzig), 2015 - present']),
            ('Thibault Clérice', ['Lead Developer (University of Leipzig)']),
            ('Bruce Robertson', ['Technical Advisor']),
            ('Greta Franzini', ['Project Manager (University of Leipzig), 2013-2014']),
            ('Frederik Baumgardt', ['Technical Manager (University of Leipzig), 2013-2015']),
            ('Simona Stoyanova', ['Project Manager (University of Leipzig), 2015', 'Project Assistant (University of Leipzig), 2013-2014'])
    )
        for resp in new_resps:
            new = etree.SubElement(new_header, 'respStmt')
            pers = etree.SubElement(new, 'persName')
            pers.text = resp[0]
            for x in resp[1]:
                r = etree.SubElement(new, 'resp')
                r.text = x
            if len(resp) == 3:
                pers.set(resp[2][0], resp[2][1])
        fileDesc.replace(fileDesc.xpath('tei:titleStmt', namespaces=self.ns)[0], new_header)

    def save_new(self):
        """ saves the new xml file with the new header

        """
        s = etree.tostring(self.root, encoding='unicode', pretty_print=True)
        s = s.replace('<respStmt><persName', '<respStmt>\n          <persName')
        s = s.replace('</persName><resp>', '</persName>\n          <resp>')
        s = s.replace('</resp></respStmt><respStmt>', '</resp>\n        </respStmt>\n        <respStmt>')
        s = s.replace('</resp><resp>', '</resp>\n          <resp>')
        s = s.replace('</resp></respStmt></titleStmt>', '</resp>\n        </respStmt>\n      </titleStmt>\n      ')
        s = '<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="http://www.stoa.org/epidoc/schema/latest/tei-epidoc.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>\n' + s
        with open(self.file, mode="w") as f:
            f.write(s)

class GraecoArabic(AddHeader):
    def replace_old(self, header):
        """ replaces the header with the information for a file that come from http://www.graeco-arabic-studies.org/

        :param header: the TEI header to be replaced
        :type header: etree._Element
        """
        new_header = etree.Element('titleStmt')
        fileDesc = header.xpath('tei:fileDesc', namespaces=self.ns)[0]
        for c in fileDesc.xpath('tei:titleStmt', namespaces=self.ns)[0].getchildren():
            if c.tag != '{http://www.tei-c.org/ns/1.0}respStmt':
                new_header.append(c)
        new_resps = (
            ([['orgName', 'A Digital Corpus for Graeco-Arabic Studies, funded by the Andrew W. Mellon Foundation', ['ref', 'http://www.graeco-arabic-studies.org/']],
              ['persName', 'Mark Schiefsky, Harvard University'],
              ['persName', 'Gregory R. Crane, Universität Leipzig'],
              ['persName', 'Uwe Vagelpohl, University of Warwick']],
             ['Published original versions of the electronic texts']),
            ([['orgName', 'Digital Divide Data', ['{http://www.w3.org/XML/1998/namespace}id', 'DDD']]], ['Keyboarding']),
            ([['persName', 'Gregory R. Crane']], ['Editor-in-Chief, Perseus Digital Library']),
            ([['persName', 'Matt Munson']], ['Project Manager (University of Leipzig), 2016 - present']),
            ([['persName', 'Annette Geßner']], ['Project Assistant (University of Leipzig), 2015 - present']),
            ([['persName', 'Thibault Clérice']], ['Lead Developer (University of Leipzig)']),
            ([['persName', 'Bruce Robertson']], ['Technical Advisor'])
        )
        for resp in new_resps:
            new = etree.SubElement(new_header, 'respStmt')
            for x in resp[1]:
                r = etree.SubElement(new, 'resp')
                r.text = x
            for e in resp[0]:
                pers = etree.SubElement(new, e[0])
                pers.text = e[1]
                if len(e) == 3:
                    pers.set(e[2][0], e[2][1])
        fileDesc.replace(fileDesc.xpath('tei:titleStmt', namespaces=self.ns)[0], new_header)

    def save_new(self):
        """ saves the new xml file with the new header

        """
        s = etree.tostring(self.root, encoding='unicode', pretty_print=True)
        s = s.replace('<respStmt><resp', '<respStmt>\n          <resp')
        s = s.replace('</resp><persName', '</resp>\n          <persName')
        s = s.replace('</resp><orgName', '</resp>\n          <orgName')
        s = s.replace('Name><persName>', 'Name>\n          <persName>')
        s = s.replace('Name></respStmt><respStmt>', 'Name>\n        </respStmt>\n        <respStmt>')
        s = s.replace('</resp><resp>', '</resp>\n          <resp>')
        s = s.replace('Name></respStmt></titleStmt>', 'Name>\n        </respStmt>\n      </titleStmt>\n      ')
        s = '<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="http://www.stoa.org/epidoc/schema/latest/tei-epidoc.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>\n' + s
        with open(self.file, mode="w") as f:
            f.write(s)

class OldPerseus(First1kOld):
    def replace_old(self, header):
        """ replaces the header with the information for a file that was started before the beginning of First1KGreek

        :param header: the TEI header to be replaced
        :type header: etree._Element
        """
        new_header = etree.Element('titleStmt')
        fileDesc = header.xpath('tei:fileDesc', namespaces=self.ns)[0]
        for c in fileDesc.xpath('tei:titleStmt', namespaces=self.ns)[0].getchildren():
            if c.tag != '{http://www.tei-c.org/ns/1.0}respStmt':
                new_header.append(c)

        new_resps = (
            ('Gregory R. Crane', ['Editor-in-Chief, Perseus Digital Library']),
            ('Digital Divide Data', ['Corrected and encoded the text'],
             ['{http://www.w3.org/XML/1998/namespace}id', 'DDD']),
            ('Matt Munson', ['Project Manager (University of Leipzig), 2016 - present']),
            ('Annette Geßner', ['Project Assistant (University of Leipzig), 2015 - present']),
            ('Thibault Clérice', ['Lead Developer (University of Leipzig)']),
            ('Bruce Robertson', ['Technical Advisor'])
        )
        for resp in new_resps:
            new = etree.SubElement(new_header, 'respStmt')
            pers = etree.SubElement(new, 'persName')
            pers.text = resp[0]
            for x in resp[1]:
                r = etree.SubElement(new, 'resp')
                r.text = x
            if len(resp) == 3:
                pers.set(resp[2][0], resp[2][1])
        fileDesc.replace(fileDesc.xpath('tei:titleStmt', namespaces=self.ns)[0], new_header)