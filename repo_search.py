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
with requests.session() as s:
    for page in range(1, 11):
        while True: # sleep the timeout
            res = s.get(url + str(page), headers=HEADERS)
            if res.status_code != 200:
                time.sleep(5)
                continue
            break   
        res_json = json.loads(str(res.content, 'utf-8'))
        res_items = res_json['items']
        for repo in res_items:
            repo_path = repo['path']
            if repo_path[-3:] == '.md': # skip markdown files
                continue
            repo_name = repo['repository']['full_name']
            repo_id = repo['repository']['id']
            # repo_url = repo['repository']['html_url']
            repos[str(repo_id) + repo_path] = (repo_name, repo_path)

print(f'{len(list(repos.keys()))} repositories found.')
print('writing to file...', end='')

with open(f'output/{datetime.now()}.txt', 'w') as f:
    for repo_url, repo_path in repos.values():
        f.write(f'{repo_url} {repo_path}\n')
print('done.')