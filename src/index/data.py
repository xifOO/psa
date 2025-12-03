import ast
from typing import Dict, Set

from entity import CodeEntity, ModuleEntity, VariableEntity
from index.call import collect_calls
from index.scopes import (
    CHILDREN_MAP,
    MODULE_MAP,
    NODE_ID_MAP,
    PARENT_MAP,
    SCOPE_MAP,
    ClassScope,
    FuncScope,
    ModuleScope,
    Scope,
    next_node_id,
    wrap_ast_node,
)


DATAFLOW_MAP: Dict[int, Set[int]] = {}


def _build_variable_dependencies(scope: Scope, entity: CodeEntity):
    if not isinstance(entity, VariableEntity):
        return

    rhs = entity.value
    names = set()

    for node in ast.walk(rhs):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            names.add(node.id)

    if not names:
        return

    deps = set()

    for name in names:
        dep_entity = scope.lookup(name)
        if dep_entity:
            deps.add(dep_entity.node_id)

    if not deps:
        return

    DATAFLOW_MAP.setdefault(entity.node_id, set()).update(deps)


def build_module_dataflow(module_scope: Scope):
    for entity in module_scope.get_values():
        _build_variable_dependencies(module_scope, entity)
    for child_id in CHILDREN_MAP.get(module_scope.node_id, []):
        child_scope = SCOPE_MAP.get(child_id)
        if child_scope and child_scope is not module_scope:
            build_module_dataflow(child_scope)


def analyze_module(module_node: ast.Module, module_name: str):
    node_id = next_node_id()
    module_entity = ModuleEntity(name=module_name, line=0, node_id=node_id, ast_node=module_node)
    module_scope = ModuleScope(node_id, module_name)

    NODE_ID_MAP[node_id] = module_entity
    SCOPE_MAP[node_id] = module_scope
    MODULE_MAP[node_id] = module_entity

    process_node(module_node, module_scope, parent_id=node_id)
    build_module_dataflow(module_scope)
    collect_calls(module_scope)
    return module_entity, module_scope


def process_node(node: ast.AST, current_scope: Scope, parent_id: int):
    entity = wrap_ast_node(node, current_scope)
    if entity:
        node_id = entity.node_id
        NODE_ID_MAP[node_id] = entity
        PARENT_MAP[node_id] = parent_id
        CHILDREN_MAP.setdefault(parent_id, []).append(node_id)

        new_scope = None
        if isinstance(node, ast.FunctionDef):
            new_scope = FuncScope(node_id, node.name, parent_scope=current_scope)
        elif isinstance(node, ast.ClassDef):
            new_scope = ClassScope(node_id, node.name, parent_scope=current_scope)

        if new_scope is not None:
            SCOPE_MAP[node_id] = new_scope
            scope_to_use = new_scope
        else:
            scope_to_use = current_scope
        
        current_scope.define(entity)

        scope_for_children = scope_to_use
    else:
        scope_for_children = current_scope
        node_id = parent_id

    for child in ast.iter_child_nodes(node):
        process_node(child, scope_for_children, parent_id=node_id)
