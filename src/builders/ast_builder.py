import ast
from index.maps import Index
from index.scopes import ClassScope, FuncScope, ModuleScope, Scope
from entity import ModuleEntity
from utils import wrap_ast_node


class ASTBuilder:
    def __init__(self, index: Index) -> None:
        self.index = index

    def build_module(self, node: ast.Module, name: str) -> ModuleScope:
        module_id = self.index.next_node_id()

        module_entity = ModuleEntity(
            name=name, line=0, node_id=module_id, ast_node=node
        )

        module_scope = ModuleScope(node_id=module_id, name=name, index=self.index)

        self.index.node_map.add(module_entity)
        self.index.scope_map.add(module_scope)

        self._process_node(node, module_scope, parent_id=module_id)

        return module_scope

    def _process_node(self, node: ast.AST, scope: Scope, parent_id: int):
        entity = wrap_ast_node(node, scope)

        if entity:
            self.index.node_map.add(entity)
            self.index.children_map.link(parent_id, entity.node_id)
            scope.define(entity)

            new_scope = None
            if isinstance(node, ast.FunctionDef):
                new_scope = FuncScope(entity.node_id, entity.name, self.index, scope)
            elif isinstance(node, ast.ClassDef):
                new_scope = ClassScope(entity.node_id, entity.name, self.index, scope)

            if new_scope:
                self.index.scope_map.add(new_scope)
                scope = new_scope
                parent_id = entity.node_id

        for child in ast.iter_child_nodes(node):
            self._process_node(child, scope, parent_id)
