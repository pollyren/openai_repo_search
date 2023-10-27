#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path
import time
import sys

with open('github_token', 'r') as f:
    token = f.readline()

# token = "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"
#url = "https://api.github.com/search/repositories?q=gpt%20application&type=repositories&per_page=100&page="
query = sys.argv[1]

url = f'https://api.github.com/search/code?q={query}&ref=advsearch&per_page=100&page='

accept = "application/vnd.github+json"
authorization = "Bearer "+token
x_GitHub_Api_Version = "2022-11-28"
headers = {"Accept":accept, "Authorization":authorization, "X-GitHub-Api-Version":x_GitHub_Api_Version}
payload = {'Authorization': "Bearer "+token}

repo_dict = {}
id_list = []
with requests.session() as s:
    # for url in url_list:
    for page in range(1,11):
        while True: #sleep the timeout
            res = s.get(url+str(page), headers=headers)
            print(res.status_code)
            if res.status_code != 200:
                print("---------break at "+str(page)+"---"+str(res.status_code))
                time.sleep(5)
                continue
            break   
        res_json = json.loads(str(res.content,'utf-8'))
        res_items = res_json['items']
        for repo in res_items:
            score = repo["score"]
            repo_name = repo["name"]
            repo_id = repo["repository"]["id"]
            repo_url = repo["repository"]["html_url"]
            if repo_id not in id_list:
                repo_dict[repo_id] = {"score":score,
                                        "name":repo_name,
                                        "url":repo_url}
                id_list.append(repo_id)
            else:
                print("Duplicated:",repo_name)
    print(len(list(repo_dict.keys())))
print(len(list(repo_dict.keys())))
dump_path = open("output/1000.json", "w")
json.dump(repo_dict,dump_path,indent=4) 
dump_path.close()