import os
import json
import pprint
import re

def filter_repos():
    with open('parse.json') as f:
        parse_results = json.load(f)

    final = {}
    for result in parse_results:
        if result['create_calls'] == []:
            continue

        if all("originates as a parameter in function" in call for call in result['create_calls']):
            continue
        
        final[result['url']] = result['create_calls']
    return final

def find_length(input_string):
    return len(re.findall(r'\w+', input_string))

def find_fstring_indices(input_string):
    matches = []
    for fstr in re.finditer(r'\{[^{}]*\}|%s', input_string):
        word_index = len(re.findall(r'\w+', input_string[:fstr.start()])) # supports .format method
        matches.append(word_index + 1)
    return matches

def main():
    repos = filter_repos()

    result = {}
    for repo, parse in repos.items():
        for line in parse:
            if 'originates' in line:
                pass
            if "Variable '" in line and " is assigned to: " in line:
                parts = line.split(" is assigned to: ")
                # variable_name = parts[0].replace("Variable '", "").replace("'", "")
                prompt_value = parts[1].strip()

                if prompt_value.startswith('['):
                    continue # not relevant prompts

                words = re.findall(r'\S+', prompt_value) # get rid of whitespaces
                prompt_value = ' '.join(words)

                if '\"content\"' in prompt_value or '\'content\'' in prompt_value:
                    for content in re.finditer(r'"content"\s*:\s*"([^"]*)"|\'content\'\s*:\s*\'([^\']*)\'', prompt_value):
                        matched = content.group(1) or content.group(2)
                        if matched not in result:
                            result[matched] = []
                        if repo not in result[matched]:
                            result[matched].append(repo)
                else:
                    if prompt_value not in result:
                        result[prompt_value] = []
                    if repo not in result[prompt_value]:
                        result[prompt_value].append(repo)
    # want statistics: position/length, prompt length, number of insertions, position of insertions (exact position and percentage position), percentage of insertions within a prompt, the more flexible the insertions are the better, closer to the beginning
    
    final_result = {}
    for prompt in result.keys():
        final_result[prompt] = {
            'repos': result[prompt], 
            'length': find_length(prompt),
            'indices': find_fstring_indices(prompt)
        }

    sorted_result = {k: v for k, v in sorted(final_result.items(), key=lambda item: len(item[0]), reverse=True)}

    with open('analysis.json', 'w') as file:
        json.dump(sorted_result, file, indent=4)

if __name__ == '__main__':
    main()