from os.path import basename
from HookTest.test import Test
from pickle import dump

class runTests:

    def __init__(self, orig, scheme='epidoc', verbose=True, workers=1, finder=''):
        """ run HookTest locally on a selected folder

        :param orig: the folder where the data directory is stored
        :type orig: str
        :param scheme: the XML schema to use, can be 'epidoc' or 'TEI'
        :type scheme: str
        :param verbose: whether to produce verbose or short output
        :type verbose: bool
        :param workers: the number of workers that HookTest will use
        :type workers: int
        """
        self.orig = orig
        self.scheme = scheme
        self.verbose = verbose
        self.workers = workers
        self.results = {}
        self.finder = finder

    def run(self):
        """ runs the tests

        """
        pipe = Test(self.orig, scheme=self.scheme, verbose=self.verbose, workers=self.workers, countwords=True, finderoptions={"include": self.finder})
        pipe.run()
        self.results = pipe.report
        with open("{}/hook_results.pickle".format(self.orig), mode="wb") as f:
            dump(self.results, f)