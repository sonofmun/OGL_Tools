__author__ = 'matt'

import requests
from lxml import etree
import re
from collections import defaultdict
import json

class GetMetadata:

    def __init__(self, orig, prefix='tlg', base_url='http://data.perseus.org/catalog/', coll='greekLit', first_col=8, dest=''):
        """
        extracts item-level metadata from the Perseus Catalog atom feeds
        :param orig: tab-delimited filename with original information
        :type orig: str
        :param prefix: the prefix to add on to the parts of the work ID
        :type prefix: str
        :param base_url: the base URL from which the atom data will be retrieved
        :type base_url: str
        :param coll: the CTS collection identifier from which the texts come
        :type coll: str
        :param first_col: first columns in the TSV file that has work information
        :type first_col: int
        :param dest: the file path to which the final TSV file should be written
        :type dest: str
        :return: new tab-delimited file with the library metadata information for each work
        :rtype: str
        """
        with open(orig) as f:
            self.orig = f.read().split('\n')
        self.prefix = prefix
        self.base_url = base_url
        self.coll = coll
        self.first_col = first_col
        self.result_dict = {}
        self.dest = dest

    def extractURN(self):
        """
        Constructs the URNs for every work based on the input from self.orig
        :return:
        :rtype:
        """
        p = re.compile(r'(\d+)\.(\d+):?')
        self.urns = []
        for volume in self.orig:
            try:
                works = volume.split('\t')[self.first_col:]
            except IndexError:
                print('{} does not appear to represent a volume'.format(volume))
                continue
            for work in works:
                m = p.search(work)
                try:
                    urn = 'urn:cts:{0}:{1}{2}.{1}{3}'.format(self.coll, self.prefix, m.group(1), m.group(2))
                    self.urns.append(urn)
                except:
                    continue
                self.result_dict[urn] = defaultdict(dict)

    def get_atom(self, urn):
        """
        Fetches the atom data from the Perseus catalog
        :param urn: the URN of the work in question
        :type urn: str
        :return:
        :rtype:
        """
        return requests.get('{}{}/atom'.format(self.base_url, urn)).text.encode('utf-8')

    def extract_metadata(self):
        """
        Extracts the necessary metadata from the Perseus catalog atom feeds
        :return:
        :rtype:
        """
        utf8_parser = etree.XMLParser(encoding='utf-8')
        ns_dict = {'atom': 'http://www.w3.org/2005/Atom', 'mods': 'http://www.loc.gov/mods/v3'}
        for work in self.result_dict.keys():
            try:
                items = etree.fromstring(self.get_atom(work), parser=utf8_parser).xpath('/atom:feed/atom:entry/atom:content/mods:mods', namespaces=ns_dict)
            except:
                print('Cannot parse atom feed for {}'.format(work))
                self.result_dict[work][1]['Title'] = ['No Catalog Information Found']
                self.result_dict[work][1]['Extent (pages)'] = ['No Catalog Information Found']
                self.result_dict[work][1]['Creator'] = ['No Catalog Information Found']
                self.result_dict[work][1]['Editor'] = ['No Catalog Information Found']
                self.result_dict[work][1]['WorldCat URL'] = ['No Catalog Information Found']
                continue
            item_num = 1
            for item in items:
                try:
                    self.result_dict[work][item_num]['WorldCat URL'] = item.xpath('./mods:relatedItem/mods:location/mods:url[@displayLabel="WorldCat"]', namespaces=ns_dict)[0].text
                except:
                    self.result_dict[work][item_num]['WorldCat URL'] = 'None Found'
                try:
                    self.result_dict[work][item_num]['Title'] = item.xpath('./mods:titleInfo/mods:title', namespaces=ns_dict)[0].text
                except:
                    self.result_dict[work][item_num]['Title'] = 'Unknown'
                try:
                    self.result_dict[work][item_num]['Extent (pages)'] = [x.text for x in item.xpath('./mods:part/mods:extent[@unit="pages"]', namespaces=ns_dict)[0].getchildren()]
                except:
                    self.result_dict[work][item_num]['Extent (pages)'] = 'Unknown'
                roles = {}
                try:
                    [roles.setdefault(x.xpath('./mods:role/mods:roleTerm', namespaces=ns_dict)[0].text, x.xpath('./mods:namePart', namespaces=ns_dict)[0].text) for x in item.xpath('./mods:name', namespaces=ns_dict)]
                    try:
                        self.result_dict[work][item_num]['Creator'] = roles['creator']
                    except:
                        self.result_dict[work][item_num]['Creator'] = 'None'
                    try:
                        self.result_dict[work][item_num]['Editor'] = roles['editor']
                    except:
                        self.result_dict[work][item_num]['Editor'] = 'None'
                except IndexError:
                    self.result_dict[work][item_num]['Creator'] = 'None'
                    self.result_dict[work][item_num]['Editor'] = 'None'
                '''try:
                    self.result_dict[work][item_num]['# of words'] = item.xpath('./mods:part/mods:extent[@unit="words"]/mods:total', namespaces=ns_dict)[0].text
                except:
                    self.result_dict[work][item_num]['# of words'] = 'Unknown'
                try:
                    self.result_dict[work][item_num]['CTS URN'] = item.xpath('./mods:identifier[@type="ctsurn"]', namespaces=ns_dict)[0].text
                except:
                    self.result_dict[work][item_num]['CTS URN'] = 'Unknown'
                try:
                    self.result_dict[work][item_num]['URLs'] = [x.text.strip('\n') for x in item.xpath('./mods:location/mods:url', namespaces=ns_dict)]
                except:
                    self.result_dict[work][item_num]['URLs'] = 'None'
                try:
                    edition = item.xpath('./mods:relatedItem', namespaces=ns_dict)[0]
                except IndexError:
                    item_num += 1
                    continue
                try:
                    self.result_dict[work][item_num]['titleInfo'] = [(x.tag.split('}')[-1], x.text.strip('\n')) for x in edition.xpath('./mods:titleInfo', namespaces=ns_dict)[0].getchildren()]
                except Exception as E:
                    self.result_dict[work][item_num]['titleInfo'] = 'No titleInfo'
                    print(E)
                    pass
                try:
                    self.result_dict[work][item_num]['Identifiers'] = [(x.get('type'), x.text) for x in edition.xpath('./mods:identifier', namespaces=ns_dict)]
                except:
                    self.result_dict[work][item_num]['Library IDs'] = 'No library IDs'
                self.result_dict[work][item_num]['Publication Date'] = [y.text for y in edition.xpath('./mods:originInfo/mods:dateIssued', namespaces=ns_dict)]
                '''
                item_num += 1

    def write_output(self):
        """
        Writes self.result_dict to a new TSV file at self.dest
        :return:
        :rtype:
        """
        with open(self.dest, mode='w') as f:
            f.write('URN\tCreator\tTitle\tEditor\tPages\tWorldCat URL(s)\n')
            for urn in self.urns:
                for item in self.result_dict[urn].keys():
                    f.write('{}\t{}\t{}\t{}\t{}\t{}\n'.format(urn,
                                                              self.result_dict[urn][item]['Creator'],
                                                              self.result_dict[urn][item]['Title'],
                                                              self.result_dict[urn][item]['Editor'],
                                                              self.result_dict[urn][item]['Extent (pages)'],
                                                              self.result_dict[urn][item]['WorldCat URL']))

    def run_all(self):
        """
        convenience function to automatically run all steps in the process
        :return:
        :rtype:
        """
        self.extractURN()
        self.extract_metadata()
        self.write_output()
        print('FINISHED')

class GetURNs(GetMetadata):

    def __init__(self, orig, base_url='http://data.perseus.org/catalog/', dest='', series='', language=''):
        """
        extracts item-level metadata from the Perseus Catalog atom feeds
        :param orig: text file with \n separated list of incomplete URNs
        :type orig: str
        :param base_url: the base URL from which the atom data will be retrieved
        :type base_url: str
        :param coll: the CTS collection identifier from which the texts come
        :type coll: str
        :param dest: the file path to which the final list of full URNs should be written
        :type dest: str
        :param series: the series in which the editions being searched for are located
        :type series: str
        :param language: the language code for the editions, e.g., "grc" or "lat"
        :type language: str
        """
        with open(orig) as f:
            self.orig = f.read().split('\n')
        self.base_url = base_url
        self.result_dict = {}
        self.dest = dest
        self.series = series
        self.new_urns = []
        self.not_in_cat = ['Work URN\tSuggested Edition URN']
        self.suggested_URNs = ['Work URN\tSuggested Edition URN']
        self.language = language

    def extractURN(self):
        raise NotImplementedError('extractURN is not implemented in GetURNs')

    def extract_metadata(self):
        """
        Extracts the edition-level identifier if one exists
        :return:
        :rtype:
        """
        utf8_parser = etree.XMLParser(encoding='utf-8')
        ns_dict = {'atom': 'http://www.w3.org/2005/Atom', 'mods': 'http://www.loc.gov/mods/v3'}
        for work in self.orig:
            x = 0
            if len(work.split('.')) == 2:
                try:
                    items = etree.fromstring(self.get_atom(work), parser=utf8_parser).xpath('/atom:feed/atom:entry/atom:content/mods:mods', namespaces=ns_dict)
                except:
                    self.new_urns.append(work + '.opp-{}1'.format(self.language))
                    self.not_in_cat.append(work + '\t' + work + '.opp-{}1'.format(self.language))
                    continue
                for item in items:
                    if item.xpath('./mods:relatedItem/mods:relatedItem/mods:titleInfo/mods:title[text()="{}"]'.format(self.series), namespaces=ns_dict):  # I think there may be a problem with this xpath
                        x = 1
                        try:
                            self.new_urns.append(item.xpath('./mods:identifier[@type="ctsurn"]', namespaces=ns_dict)[0].text)
                            print('PL version ' + work)
                        except:
                            self.new_urns.append(work + '.opp-{}-tmp'.format(self.language))
                if x == 0:
                    existing = [int(x.text[-1]) for x in item.xpath('//mods:identifier[@type="ctsurn"]', namespaces=ns_dict) if 'opp-{}'.format(self.language) in x.text]
                    try:
                        new = max(existing) + 1
                    except:
                        new = 1
                    self.new_urns.append(work + '.opp-{}{}'.format(self.language, new))
                    print('New URN: ' + (work + '.opp-{}{}'.format(self.language, new)))
                    self.suggested_URNs.append(work + '\t' + work + '.opp-{}{}'.format(self.language, new))
            else:
                self.new_urns.append(work)

    def write_output(self):
        """
        writes self.new_urns to a new \n-separated .txt file
        :return:
        :rtype:
        """
        with open(self.dest, mode='w') as f:
            [f.write('{}\n'.format(x)) for x in self.new_urns]
        dir = '/'.join(self.dest.split('/')[:-1])
        print(dir)
        with open(dir + '/Not_in_cat.txt', mode='w') as f:
            [f.write('{}\n'.format(x)) for x in self.not_in_cat]
        with open(dir + '/suggested_new_URNs.txt', mode='w') as f:
            [f.write('{}\n'.format(x)) for x in self.suggested_URNs]

    def run_all(self):
        """
        convenience function to automatically run all steps in the process
        :return:
        :rtype:
        """
        self.extract_metadata()
        self.write_output()
        print('FINISHED')