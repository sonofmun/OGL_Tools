import requests
import json
import time

class CreateIssues():
    def __init__(self, org, repo, token, issues, uname, ignore):
        """

        :param org:
        :type org:
        :param repo:
        :type repo:
        :param token: Github OAuth token (in the form, e.g., 97cc6b...1102ba)
        :type token:
        :param issues: the dictionary containing the issues, {file: [list of issues in str format]}
        :type issues: dict
        :param uname:
        :type uname:
        :param ignore:
        :type ignore:
        """

        # self.org = org
        self.base = 'https://api.github.com/repos/{}/{}/issues'.format(org, repo)
        self.auth = 'token {0}'.format(token)
        self.issues = issues
        self.uname = uname
        self.ignore = ignore
        self.problems = []

    def createissues(self):
        for k, v in self.issues.items():
            params = {'title': k, 'body': '\n'.join(v)}
            reply = requests.post(self.base, data=json.dumps(params),
                                  headers={'Authorization': self.auth})
            if reply.status_code != 201:
                self.problems.append('{} {}: {}'.format(k, reply.text))
                time.sleep(600)
            time.sleep(60)