import ast
from pathlib import Path
from typing import Optional

from entity import ModuleEntity
from index.scopes import (
    MODULE_MAP,
    NODE_ID_MAP,
    CHILDREN_MAP,
    SCOPE_MAP,
    ClassScope,
    FuncScope,
    ModuleScope,
    Scope,
    wrap_ast_node,
    next_node_id,
)


class Extractor:
    def __init__(self, root_path: Optional[Path] = None) -> None:
        self.root_path = root_path

    def extract_file(self, path: Path) -> ModuleEntity:
        tree = ast.parse(path.read_text(), filename=str(path))
        module_name = path.stem
        return self._extract_module(tree, module_name)

    def _extract_module(
        self, module_node: ast.Module, module_name: str
    ) -> ModuleEntity:
        node_id = next_node_id()
        module_entity = ModuleEntity(
            name=module_name, line=0, node_id=node_id, ast_node=module_node
        )
        module_scope = ModuleScope(node_id=node_id, name=module_name)

        NODE_ID_MAP[node_id] = module_entity
        SCOPE_MAP[node_id] = module_scope
        MODULE_MAP[node_id] = module_entity

        self._process_node(module_node, module_scope, parent_id=node_id)
        return module_entity

    def _process_node(self, node: ast.AST, current_scope: Scope, parent_id: int):
        entity = wrap_ast_node(node, current_scope)
        if entity:
            node_id = entity.node_id
            NODE_ID_MAP[node_id] = entity
            CHILDREN_MAP.setdefault(parent_id, []).append(node_id)

            if isinstance(node, ast.FunctionDef):
                new_scope = FuncScope(node_id, node.name, parent_scope=current_scope)
                SCOPE_MAP[node_id] = new_scope
                scope_for_children = new_scope
            elif isinstance(node, ast.ClassDef):
                new_scope = ClassScope(node_id, node.name, parent_scope=current_scope)
                SCOPE_MAP[node_id] = new_scope
                scope_for_children = new_scope
            else:
                scope_for_children = current_scope

            current_scope.define(entity)
        else:
            scope_for_children = current_scope
            node_id = parent_id

        for child in ast.iter_child_nodes(node):
            self._process_node(child, scope_for_children, parent_id=node_id)

    def extract_dir(self, path: Path):
        modules = []
        for py_file in path.rglob("*.py"):
            module = self.extract_file(py_file)
            modules.append(module)
        return modules
