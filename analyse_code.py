#!/usr/bin/env python3

import requests
import json
import base64
from bs4 import BeautifulSoup
from pathlib import Path
import time
import sys
from datetime import datetime

with open('github_token', 'r') as f:
    TOKEN = f.readline().strip()

ACCEPT = 'application/vnd.github+json'
AUTHORISATION = f'Bearer {TOKEN}'
GITHUB_API_VERSION = '2022-11-28'
HEADERS = {'Accept': ACCEPT, 'Authorization': AUTHORISATION, 'X-GitHub-Api-Version': GITHUB_API_VERSION}

def read_github_file(url):
    response = requests.get(url, headers=HEADERS)
    print(response.text)
    # print(type(json.loads(response.text)))
    return json.loads(response.text)
    # else:
    #     raise Exception(f'Failed to fetch content from {url} with error code {response.status_code}')

file_name = sys.argv[1]

file = open(f'output/{file_name}', 'r')

file_contents = {}
for line in file.readlines()[:5]:
    try:
        repo_name, repo_path = line.strip().split(' ')
    except:
        continue

    link = f'https://api.github.com/repos/{repo_name}/contents/{repo_path}?ref=main'
    github_json = read_github_file(link)
    if 'content' in github_json:
        content = base64.b64decode(github_json['content']).decode('utf-8')
        print(content)
    else:
        link = f'https://api.github.com/repos/{repo_name}/contents/{repo_path}?ref=master'
        github_json = read_github_file(link)
        if 'content' in github_json:
            content = base64.b64decode(github_json['content']).decode('utf-8')
            print(content)
        else: 
            print('oop')
            continue

    if content is not None:
        # print(link)
        # print(content)
        file_contents[link] = content

count = 0
for link, content in file_contents.items():
    print(f"File from {link}:\n{content}")
    count += 1
    if count > 5: break