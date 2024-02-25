import os
import json

def main():
    with open('parse.json') as f:
        parse_results = json.load(f)

if __name__ == '__main__':
    main()