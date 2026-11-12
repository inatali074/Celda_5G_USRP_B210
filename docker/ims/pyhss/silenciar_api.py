import ast,pathlib
p=pathlib.Path('/pyhss/services/apiService.py')
tree=ast.parse(p.read_text())
class Quiet(ast.NodeTransformer):
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='print':
   return ast.copy_location(ast.Pass(),n)
  return self.generic_visit(n)
p.write_text(ast.unparse(Quiet().visit(tree)))
