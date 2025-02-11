import ast

def extract_method_lines(src_code):
        methods = []
        tree = ast.parse(src_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append( (node.lineno, node.end_lineno) )
        methods = sorted(methods, key=lambda x: x[0])
        return methods

class ParameterVisitor(ast.NodeVisitor):
     def __init__(self):
          self.parameters = []


     def visit_FunctionDef(self, node):
          for arg in node.args.args:   
            self.parameters.append(arg.arg)
          
def get_param_names(ast_code_tree):
    param_visitor = ParameterVisitor()
    param_visitor.visit(ast_code_tree)
    return param_visitor.parameters
    