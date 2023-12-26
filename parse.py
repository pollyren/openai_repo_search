#!/usr/bin/env python3
import ast

class Finder(ast.NodeVisitor):
    def __init__(self, source_code: str):
        self.target_variable = None
        self.all_assignments = []  # Track all assignments
        self.relevant_interactions = []  # Filtered interactions relevant to the target variable
        self.source_code = source_code

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            if (node.func.attr == 'create' and
                    isinstance(node.func.value, ast.Attribute) and
                    node.func.value.attr == 'ChatCompletion' and
                    isinstance(node.func.value.value, ast.Name)):
                print("Found 'ChatCompletion.create' call at line:", node.lineno)
                self.print_arguments(node)
                self.filter_interactions()  # Filter interactions after target_variable is set
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        assignment_str = ast.get_source_segment(self.source_code, node)
        self.all_assignments.append((node.targets, assignment_str))
        self.generic_visit(node)

    def filter_interactions(self):
        for targets, assignment_str in self.all_assignments:
            for target in targets:
                if isinstance(target, ast.Name) and target.id == self.target_variable:
                    self.relevant_interactions.append(f"Assignment to '{self.target_variable}': {assignment_str}")

    def print_arguments(self, node: ast.Call):
        print("Arguments:")
        for kw in node.keywords:
            if kw.arg == 'messages':
                if isinstance(kw.value, ast.Name):  # Check if keyword argument is a variable
                    self.target_variable = kw.value.id
                self.print_messages_argument(kw.value)
            else: 
                print(f"  - Keyword Arg: {kw.arg} = {ast.dump(kw.value)}")

    def print_messages_argument(self, messages_arg: ast.Name | ast.expr):
        if isinstance(messages_arg, ast.List):
            print(f"  - Keyword Arg: messages = [")
            for idx, item in enumerate(messages_arg.elts):
                if isinstance(item, ast.Dict):
                    print("      {")
                    for key, value in zip(item.keys, item.values):
                        key_str = ast.dump(key)
                        value_str = ast.dump(value)
                        print(f"        {key_str}: {value_str}")
                    print("      }")
            print("    ]")
        else:
            print("  - Keyword Arg: messages =", ast.dump(messages_arg))

def find_openai_chatcompletions_calls(code):
    tree = ast.parse(code)
    finder = Finder(code)
    finder.visit(tree)
    return finder.relevant_interactions

def main():
    line = "('yoheinakajima_babyagi_classic_babyfoxagi_skills_drawing.py', 'yoheinakajima/babyagi', 'classic/babyfoxagi/skills/drawing.py')"
    fn, repo_name, repo_path = line.strip()[1:-1].split(', ')
    fn = fn[1:-1]
    with open(f'repos/{fn}', 'r') as f:
        code = f.read()

    interactions = find_openai_chatcompletions_calls(code)
    for interaction in interactions:
        print(interaction)

if __name__ == '__main__':
    main()