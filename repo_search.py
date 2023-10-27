#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path
import time
import sys
from datetime import datetime

with open('github_token', 'r') as f:
    TOKEN = f.readline()

ACCEPT = 'application/vnd.github+json'
AUTHORISATION = f'Bearer {TOKEN}'
GITHUB_API_VERSION = '2022-11-28'
HEADERS = {'Accept': ACCEPT, 'Authorization': AUTHORISATION, 'X-GitHub-Api-Version': GITHUB_API_VERSION}

query = sys.argv[1]
url = f'https://api.github.com/search/code?q={query}&ref=advsearch&per_page=100&page='

repos = {}
# id_list = []
with requests.session() as s:
    for page in range(1, 11):
        while True: # sleep the timeout
            res = s.get(url + str(page), headers=HEADERS)
            if res.status_code != 200:
                # print('---------break at '+str(page)+'---'+str(res.status_code))
                time.sleep(5)
                continue
            break   
        res_json = json.loads(str(res.content, 'utf-8'))
        res_items = res_json['items']
        for repo in res_items:
            # score = repo['score']
            # repo_name = repo['repository']['full_name']
            repo_id = repo['repository']['id']
            repo_url = repo['repository']['html_url']
            repo_path = repo['path']
            repos[repo_id] = (repo_url, repo_path)
            # if repo_id not in id_list:
            #     repo_dict[repo_id] = {'name':repo_name, 'url':repo_url}
            #     id_list.append(repo_id)
            # else:
            #     print(f'Duplicated: {repo_name}')

print(f'{len(list(repos.keys()))} repositories found.')
print('writing to file...', end='')

with open(f'output/{datetime.now()}.txt', 'w') as f:
    for repo_url, repo_path in repos.values():
        f.write(f'{repo_url} {repo_path}\n')
print('done.')