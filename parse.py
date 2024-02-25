#!/usr/bin/env python3
import ast

class Finder(ast.NodeVisitor):
    def __init__(self, source_code: str):
        self.target_variable = None
        self.all_assignments = {}
        self.relevant_interactions = [] 
        self.function_parameters = {}
        self.source_code = source_code

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            if (node.func.attr == 'create' and
                    isinstance(node.func.value, ast.Attribute) and
                    node.func.value.attr == 'ChatCompletion' and
                    isinstance(node.func.value.value, ast.Name)):
                print("Found 'ChatCompletion.create' call at line:", node.lineno)
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
        print("Arguments:")
        for kw in node.keywords:
            if kw.arg == 'messages':
                if isinstance(kw.value, ast.Name): 
                    self.target_variable = kw.value.id
                    print("  - Keyword Arg: messages =", ast.dump(kw.value))
                elif isinstance(kw.value, ast.List):
                    print(f"  - Keyword Arg: messages = [")
                    for _, item in enumerate(kw.value.elts):
                        if isinstance(item, ast.Dict):
                            print("      {")
                            for key, value in zip(item.keys, item.values):
                                key_str = ast.dump(key)
                                value_str = ast.dump(value)
                                if isinstance(value, ast.Name) and value.id in self.all_assignments:
                                    self.target_variable = value.id
                                print(f"        {key_str}: {value_str}")
                            print("      }")
                    print("    ]")
            else: 
                print(f"  - Keyword Arg: {kw.arg} = {ast.dump(kw.value)}")
            
def find_openai_chatcompletions_calls(code):
    tree = ast.parse(code)
    finder = Finder(code)
    finder.visit(tree)
    return finder.relevant_interactions

def main():
    line = "('Shaunwei_RealChar_scripts_contrib_create_char.py', 'Shaunwei/RealChar', 'scripts/contrib/create_char.py')"
    fn, repo_name, repo_path = line.strip()[1:-1].split(', ')
    fn = fn[1:-1]
    with open(f'repos/{fn}', 'r') as f:
        code = f.read()

    interactions = find_openai_chatcompletions_calls(code)
    for interaction in interactions:
        print(interaction)

    #statistics: position/length, prompt length, number of insertions, position of insertions (exact position and percentage position), percentage of insertions within a prompt, the more flexible the insertions are the better, closer to the beginning

if __name__ == '__main__':
    main()