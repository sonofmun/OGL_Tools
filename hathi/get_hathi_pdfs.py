__author__ = 'matt'

import requests
import subprocess


class get_pdfs:
    def __init__(self, ids, refer_dest='./',
                 download_script='download-everything.sh', pdf_dest='./pdfs/',
                 cooks='./cooks/'):
        '''
		ids should either be a comma-delimited string containing Hathi IDs
		or a Python list of Hathi IDs
		:param ids:
		:param refer_dest:
		:param download_script:
		:param pdf_dest:
		:param cooks:
		:return:
		'''
        if isinstance(ids, str):
            self.ids = ids.split(',')
        elif isinstance(ids, list):
            self.ids = ids
        else:
            AssertionError(
                '"ids" must either be a comma-delimited string or a list')
        self.refer_dest = refer_dest
        self.script = download_script
        self.dest = pdf_dest
        self.cooks = cooks

    def get_refers(self):
        '''
		Downloads and saves the .refer files for the Hathi IDs
		:return:
		'''
        params = {'method': 'ris'}
        url = 'http://catalog.hathitrust.org/Search/SearchExport'
        for n in self.ids:
            params['handpicked'] = n
            with open('{}/{}.refer'.format(self.refer_dest, n), mode='w') as f:
                f.write(requests.get(url, params=params).text)

    def get_files(self):
        s = subprocess.run(
            [self.script, self.refer_dest, self.dest, self.cooks],
            universal_newlines=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        with open('{}/output.txt'.format(self.dest), mode='w') as f:
            f.write(s.stdout)
