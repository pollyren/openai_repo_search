#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path
import time
import sys
from datetime import datetime
import openai

def create_prompt(code):
    prompt = r'''
    Please answer the following questions regarding the code. Please indicate the question each portions of the response is answering. Please do not use any additional sentences providing explanation other that what is asked by the question. Each question should be answerable in less than 20 words. Do not answer in complete sentences. There is an example below for what a response should look like. 
    1. Does the ChatCompletions API call use both a system and user for the conversation? 
    2. Which inputs are static and which are dynamic? Please indicate whether the inputs are for the system or for the user. A static input refers to a constant string, while a dynamic input uses user input and variables to create the string.
    3. How many static words are in the user content prompt? How many dynamic tokens are in the user input?
    4. Where are the dynamic tokens located within the prompt template? Are they located at the beginning of the template, in the middle, or at the end?
    5. How many steps are there between the command line input and the final dynamic tokens? What types of steps are they (i.e., concatenation, slicing, random generator)?

    Example 1: 
    #!/usr/bin/env python3

    import openai
    import sys
    import os
    import configparser

    # Get config dir from environment or default to ~/.config
    CONFIG_DIR = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    API_KEYS_LOCATION = os.path.join(CONFIG_DIR, 'openaiapirc')

    # Read the organization_id and secret_key from the ini file ~/.config/openaiapirc
    # The format is:
    # [openai]
    # organization_id=<your organization ID>
    # secret_key=<your secret key>

    # If you don't see your organization ID in the file you can get it from the
    # OpenAI web site: https://openai.com/organizations
    def create_template_ini_file():
        """
        If the ini file does not exist create it and add the organization_id and
        secret_key
        """
        if not os.path.isfile(API_KEYS_LOCATION):
            with open(API_KEYS_LOCATION, 'w') as f:
                f.write('[openai]\n')
                f.write('organization_id=\n')
                f.write('secret_key=\n')
                f.write('model=gpt-3.5-turbo-0613\n')

            print('OpenAI API config file created at {}'.format(API_KEYS_LOCATION))
            print('Please edit it and add your organization ID and secret key')
            print('If you do not yet have an organization ID and secret key, you\n'
                'need to register for OpenAI Codex: \n'
                    'https://openai.com/blog/openai-codex/')
            sys.exit(1)


    def initialize_openai_api():
        """
        Initialize the OpenAI API
        """
        # Check if file at API_KEYS_LOCATION exists
        create_template_ini_file()
        config = configparser.ConfigParser()
        config.read(API_KEYS_LOCATION)

        openai.organization_id = config['openai']['organization_id'].strip('"').strip("'")
        openai.api_key = config['openai']['secret_key'].strip('"').strip("'")

        if 'model' in config['openai']:
            model = config['openai']['model'].strip('"').strip("'")
        else:
            model = 'gpt-3.5-turbo'

        return model

    model = initialize_openai_api()

    cursor_position_char = int(sys.argv[1])

    # Read the input prompt from stdin.
    buffer = sys.stdin.read()
    prompt_prefix = 'Here is the code: #!/bin/zsh\n\n' + buffer[:cursor_position_char]
    prompt_suffix = buffer[cursor_position_char:]
    full_command = prompt_prefix + prompt_suffix
    response = openai.ChatCompletion.create(model=model, messages=[
        {
            "role":'system',
            "content": "You are a zsh shell expert, please help me complete the following command, you should only output the completed command, no need to include any other explanation",
        },
        {
            "role":'user',
            "content": full_command,
        }
    ])
    completed_command = response['choices'][0]['message']['content']

    sys.stdout.write(f"\n{completed_command.replace(prompt_prefix, '', 1)}")
    An example response to Example 1 would be as follows:
    1. Yes.
    2. The system prompt is static. The user prompt is dynamic. The dynamic variables for the user prompt are 
    3. 5 static word in user input.
    4. At the end of the user prompt.
    5. There are 3 total operations: 2 slicing operations of the command line input, 1 concatenation operation on the two results. 

    Example 2: 
    import sys, re
    from pathlib import Path
    from os import path

    sys.path.append(str(Path(__file__).parent.parent.parent))

    import g4f

    def read_code(text):
        if match := re.search(r"```(python|py|)\n(?P<code>[\S\s]+?)\n```", text):
            return match.group("code")
        
    path = input("Path: ")

    with open(path, "r") as file:
        code = file.read()

    prompt = f"""
    Improve the code in this file:
    ```py
    {code}
    ```
    Don't remove anything.
    Add typehints if possible.
    Don't add any typehints to kwargs.
    Don't remove license comments.
    """

    print("Create code...")
    response = []
    for chunk in g4f.ChatCompletion.create(
        model=g4f.models.gpt_35_long,
        messages=[{"role": "user", "content": prompt}],
        timeout=300,
        stream=True
    ):
        response.append(chunk)
        print(chunk, end="", flush=True)
    print()
    response = "".join(response)

    if code := read_code(response):
        with open(path, "w") as file:
            file.write(code)
    An example response to Example 2 would be as follows:
    1. No.
    2. No system prompt. The user prompt is dynamic. The dynamic variables for the user prompt is `path`.
    3. There are 23 static words in the user input.
    4. The dynamic tokens are located in the middle of the user prompt.
    5. There are 2 steps between the command line input and the final dynamic tokens. The steps are: reading the code from the file and inserting the code into the prompt.
    '''
    return f'The following is a piece of code: {code}\n' + prompt

with open('openai_token', 'r') as f:
    OPENAI_KEY = f.readline().strip()
openai.api_key = OPENAI_KEY

with open('repos/repos.txt', 'r') as f:
    lines = f.readlines()

for line in lines:
    fn, repo_name, repo_path = line.strip()[1:-1].split(', ')
    fn = fn[1:-1]
    repo_name = repo_name[1:-1]
    repo_path = repo_path[1:-1]
    with open(f'repos/{fn}', 'r') as f:
        code = f.read()
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        temperature=0.2,
        messages=[
            {'role': 'system', 'content': 'You are a helpful code tracer.'}, 
            {'role': 'user', 'content': create_prompt(code)}
        ]
    )
    print(completion.choices[0].message.content)