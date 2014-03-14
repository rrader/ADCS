import ast


class Visit(ast.NodeVisitor):
    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.vars = []

    def visit_Name(self, node):
        if not node.id.startswith('_'):
            self.vars.append(node.id)

text = "_not(_and(b,d))"
tree = ast.parse(text)
v = Visit()
v.visit(tree)
print(v.vars)
