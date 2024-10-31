import ast
import os
import argparse

class PythonAnalyzer(ast.NodeVisitor):
    def __init__(self, filepath):
        self.classes = []
        self.static_functions = []
        self.module_level_code = []
        self.imports = []
        self.from_imports = []
        self.filename = filepath
        self.filepath = os.path.dirname(os.path.abspath(filepath))

    def visit_ClassDef(self, node):
        self.classes.append({
            "node_name": node.name,
            "lineno" : node.lineno,
            "end_lineno": node.end_lineno
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if node.col_offset == 0:
            self.static_functions.append({
                "node_name": node.name,
                "lineno" : node.lineno,
                "end_lineno": node.end_lineno
            })
        self.generic_visit(node)

    def visit_Module(self, node):
        if node.body:
            first_child = None
            last_child = None
            
            for child in node.body:
                if(not isinstance(child, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))):
                    if(first_child == None):
                        first_child = child
                    else:
                        last_child = child
            
            if(first_child != None):
                first_lineno = getattr(first_child, 'lineno', None)
                last_end_lineno = getattr(first_child, 'end_lineno')
                if(last_child != None):
                    last_child_end_lineno = getattr(last_child, 'end_lineno', getattr(last_child, 'lineno', None))
                    if(last_end_lineno < last_child_end_lineno):
                        last_end_lineno = last_child_end_lineno
                
                if(first_child != None):
                    self.module_level_code.append({
                        'code': [ast.dump(child) for child in node.body if not isinstance(child, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))],
                        'first_lineno': first_lineno,
                        'last_end_lineno': last_end_lineno
                    })
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            module_path = os.path.join(self.filepath, alias.name+".py")
            is_local = os.path.exists(module_path)
            
            entry = {
                "import": f'import {alias.name}' + (f' as {alias.asname}' if alias.asname else ''),
            }
            
            if(is_local):
                entry['is_local'] = is_local
                entry['module_path'] = module_path
            
            self.imports.append(entry)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module else ''
        for alias in node.names:
            module_path = os.path.join(self.filepath, module+".py")
            is_local = os.path.exists(module_path)
            
            entry = {
                "import": f'from {module} import {alias.name}' + (f' as {alias.asname}' if alias.asname else ''),
            }
            
            if(is_local):
                entry['is_local'] = is_local
                entry['module_path'] = module_path
            
            self.from_imports.append(entry)
        self.generic_visit(node)

def analyze_python_file(file_path):
    with open(file_path, 'r') as file:
        source = file.read()
    
    tree = ast.parse(source)
    analyzer = PythonAnalyzer(file_path)
    analyzer.visit(tree)
    
    return {
        'classes': analyzer.classes,
        'static_functions': analyzer.static_functions,
        'module_level_code': analyzer.module_level_code,
        'imports': analyzer.imports,
        'from_imports': analyzer.from_imports
    }

class PyUnit:
    def __init__(self, path, analysis, visited, dep_counter = 0):
        self.path = path
        self.analysis = analysis
        self.visited = False
        self.dep_counter = dep_counter

def expand_units(units):
    for unit in units:
        if unit.visited:
            continue
        else:
            if(unit.analysis is None):
                    unit.analysis = analyze_python_file(unit.path)
                            
            for dep in unit.analysis["imports"]:
                if('is_local' in dep and dep['is_local']):
                    found_dep = next((obj for obj in units if obj.path == dep['module_path']), None)
                    if(found_dep == None):
                        units.append(PyUnit(dep['module_path'], None, False, 1))
                    else:
                        found_dep.dep_counter +=1
            for dep in unit.analysis["from_imports"]:
                if('is_local' in dep and dep['is_local']):
                    found_dep = next((obj for obj in units if obj.path == dep['module_path']), None)
                    if(found_dep == None):
                        units.append(PyUnit(dep['module_path'], None, False, 1))
                    else:
                        found_dep.dep_counter +=1
            
            unit.visited = True

def extract_text_range(path, lineno, end_lineno):
    if(not os.path.exists(path)
       or lineno == None or lineno < 0
       or end_lineno == None or end_lineno < 0):
        return ""
    lines = []
    with open(path, 'r') as file:
        for current_line_num, line in enumerate(file, start=1):
            if lineno <= current_line_num <= end_lineno:
                lines.append(line)
            elif current_line_num > end_lineno:
                break
    return lines
    
def main():
    parser = argparse.ArgumentParser(description='Analyze a Python file and output the result.')
    parser.add_argument('-i', '--input', help='The path to the input Python file.', required=True)
    parser.add_argument('-o', '--output', help='The name of the output file.', nargs='?', default="output.py")
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite without asking')
    
    args = parser.parse_args()
    
    args.input = os.path.abspath(args.input)
    
    if(os.path.dirname(args.output) != ''):
        args.output = os.path.abspath(args.output)
    else:
        args.output = os.path.join(os.path.dirname(args.input), args.output)
        
    if(args.input == args.output):
        if not args.force:
            overwrite = input("Input and output files are the same. Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                print("Operation cancelled.")
                return
            
    units = []
    analysis = analyze_python_file(args.input)
    units.append(PyUnit(os.path.abspath(args.input), analysis, False))
    while(any(obj.visited == False for obj in units)):
        expand_units(units)

    imports = []

    for unit in units:
        for imp in unit.analysis['imports']:
            if 'is_local' in imp and imp['is_local'] == True:
                continue
            else:
                found = False
                for _import in imports:
                    if imp['import'] in _import:
                        found = True
                if not found:
                    imports.append(imp['import'])
        for imp in unit.analysis['from_imports']:
            if 'is_local' in imp and imp['is_local'] == True:
                continue
            else:
                found = False
                for _import in imports:
                    if imp['import'] in _import:
                        found = True
                if not found:
                    imports.append(imp['import'])
                    
    with open(args.output, 'w') as file:
        for imp in imports:
            file.write(imp+"\n")
        file.write('\n')
        max_dep_count = max(unit.dep_counter for unit in units)
        while len(units) > 0:
            found_max_depcount = False
            for index in range(len(units)):
                unit = units[index]
                if unit.dep_counter == max_dep_count:
                    found_max_depcount = True
                    for cl in unit.analysis['classes']:
                        lineno = cl['lineno']
                        end_lineno = cl['end_lineno']
                        lines = extract_text_range(unit.path, lineno, end_lineno)
                        for line in lines:
                            file.write(line)
                        file.write("\n")
                    for cl in unit.analysis['static_functions']:
                        lineno = cl['lineno']
                        end_lineno = cl['end_lineno']
                        lines = extract_text_range(unit.path, lineno, end_lineno)
                        for line in lines:
                            file.write(line)
                        file.write("\n")
                        
                    file.flush()  # Ensure the content is written immediately
                    del units[index]
                    
                    if(max_dep_count == 0):
                        for mlc in unit.analysis['module_level_code']:
                            lineno = mlc['first_lineno']
                            end_lineno = mlc['last_end_lineno']
                            lines = extract_text_range(unit.path, lineno, end_lineno)
                            
                            file.write("\n\n")
                            for line in lines:
                                file.write(line)
                        file.flush()  # Ensure the content is written immediately
                            
                    break
            if not found_max_depcount:
                max_dep_count -= 1
        file.flush()  # Ensure the content is written immediately

if __name__ == '__main__':
    main()