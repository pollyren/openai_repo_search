import ast  # Documentation: https://docs.python.org/3/library/ast.html
import json
import os
from urllib.request import urlopen

class Finder(ast.NodeVisitor):
    def __init__(self, source_code: str):
        self.target_variable = None
        self.all_assignments = {}
        self.relevant_interactions = [] 
        self.function_parameters = {}
        self.source_code = source_code
        self.current_function = None

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            if (node.func.attr == 'create' and
                    isinstance(node.func.value, ast.Attribute) and
                    node.func.value.attr == 'ChatCompletion' and
                    isinstance(node.func.value.value, ast.Name)):
                # print("Found 'ChatCompletion.create' call at line:", node.lineno)
                self.print_arguments(node)
                self.filter_interactions()
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # print('visit assign', node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                # print(target.id)
                assignment_str = ast.get_source_segment(self.source_code, node.value)
                self.all_assignments[target.id] = assignment_str
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        for arg in node.args.args:
            self.function_parameters[arg.arg] = node.name
        self.generic_visit(node)

    def trace_variable_origin(self, variable, seen_vars: set):
        # print(f'tracing for {variable}')
        if variable in seen_vars:
            return

        if variable in self.function_parameters:
            func_name = self.function_parameters[variable]
            self.relevant_interactions.append(f"'{variable}' originates as a parameter in function '{func_name}'")
            seen_vars.add(variable)
            return

        if variable in self.all_assignments:
            assigned_value = self.all_assignments[variable]
            self.relevant_interactions.append(f"Variable '{variable}' is assigned to: {assigned_value}")
            seen_vars.add(variable)

            if assigned_value.startswith("f"):
                self.handle_f_string(assigned_value, seen_vars)
            else:
                for node in ast.walk(ast.parse(assigned_value)):
                    if isinstance(node, ast.Name) and node.id in self.all_assignments and node.id not in seen_vars:
                        self.trace_variable_origin(node.id, seen_vars)

    def handle_f_string(self, f_string, seen_vars):
        try:
            parsed = ast.parse(f_string)
            for node in ast.walk(parsed):
                if isinstance(node, ast.FormattedValue):
                    if isinstance(node.value, ast.Name) and node.value.id not in seen_vars:
                        self.trace_variable_origin(node.value.id, seen_vars)
        except SyntaxError:
            print(f"syntax error while parsing f-string: {f_string}")

    def filter_interactions(self):
        if self.target_variable:
            # print('TARGET VARIABlEfJLSFJDL', self.target_variable)
            self.trace_variable_origin(self.target_variable, set())

    def print_arguments(self, node: ast.Call):
        # print("Arguments:")
        for kw in node.keywords:
            if kw.arg == 'messages':
                if isinstance(kw.value, ast.Name): 
                    self.target_variable = kw.value.id
                    # print("  - Keyword Arg: messages =", ast.dump(kw.value))
                elif isinstance(kw.value, ast.List):
                    # print(f"  - Keyword Arg: messages = [")
                    for _, item in enumerate(kw.value.elts):
                        if isinstance(item, ast.Dict):
                            # print("      {")
                            for key, value in zip(item.keys, item.values):
                                key_str = ast.dump(key)
                                value_str = ast.dump(value)
                                if isinstance(value, ast.Name) and value.id in self.all_assignments:
                                    self.target_variable = value.id
                    #             print(f"        {key_str}: {value_str}")
                    #         print("      }")
                    # print("    ]")
            else: 
                print(f"  - Keyword Arg: {kw.arg} = {ast.dump(kw.value)}")
            
def find_openai_chatcompletions_calls(code):
    tree = ast.parse(code)
    finder = Finder(code)
    finder.visit(tree)
    return finder.relevant_interactions

def parse_py_files_from_json(json_file):
    with open(json_file, 'r') as file:
        urls = json.load(file)
    py_urls = [url for url in urls["raw_urls"] if ".py" in url]  # Adjusted to include URLs containing ".py"
    return py_urls

def save_results_to_json(results, file_path):
    with open(file_path, 'w') as file:
        json.dump(results, file, indent=4)

def main():
    # Main processing logic
    py_urls = parse_py_files_from_json('code_search/raw_data_all.json')
    # py_urls = ["https://raw.githubusercontent.com/MLNLP-World/AI-Paper-Collector/477ef2aec293e07156f386d7dccd27fa2c1af295/app.py"]
    results = []
    
    for url in py_urls:
        try:
            response = urlopen(url)
            content = response.read().decode('utf-8')
            interactions = find_openai_chatcompletions_calls(content)
            results.append({
                "url": url,
                "create_calls": interactions
            })
        except Exception as e:
            print(f"Error downloading or parsing {url}: {e}")
            pass

    # Specify the desired output JSON file name
    output_file_name = 'code_search/parse.json'
    save_results_to_json(results, output_file_name)

if __name__ == '__main__':
    main()