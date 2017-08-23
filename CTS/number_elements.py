from lxml import etree

def number_elements(orig, xpath, parent=None):

    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    root = etree.parse(orig).getroot()
    if parent:
        for p in root.xpath(parent, namespaces=ns):
            x = 1
            for e in p.xpath(xpath, namespaces=ns):
                e.set('n', str(x))
                x += 1
    else:
        x = 1
        for e in root.xpath(xpath, namespaces=ns):
            e.set('n', str(x))
            x += 1
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="http://www.stoa.org/epidoc/schema/latest/tei-epidoc.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
    text = etree.tostring(root, encoding='unicode', pretty_print=True)
    text = text.replace('<refsDecl n="CTS">', '  <refsDecl n="CTS">')
    text = text.replace('><cRefPattern', '>\n        <cRefPattern')
    text = text.replace('></refsDecl>', '>\n      </refsDecl>\n    ')
    text = text.replace('<teiHeader>', '<teiHeader>\n    ')
    text = text.replace('  </teiHeader>', '</teiHeader>\n')
    text = xml_header + text
    return text