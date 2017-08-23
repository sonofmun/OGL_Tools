from lxml import etree


def reformat_XML(root):
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