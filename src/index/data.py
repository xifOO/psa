import ast
from typing import Dict, Set

from entity import CallEntity, CodeEntity, ModuleEntity, VariableEntity
from index.call import CALL_MAP
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
    _convert_call_args,
    _convert_keywords,
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


def _build_module_dataflow(module_scope: Scope):
    for entity in module_scope.get_values():
        _build_variable_dependencies(module_scope, entity)
    for child_id in CHILDREN_MAP.get(module_scope.node_id, []):
        child_scope = SCOPE_MAP.get(child_id)
        if child_scope and child_scope is not module_scope:
            _build_module_dataflow(child_scope)


def _collect_calls(scope: Scope):
    for entity in scope.get_values():
        node = entity.ast_node
        if node is None:
            continue

        current_scope = SCOPE_MAP.get(entity.node_id, scope)

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = ""
                receiver = None
                is_method_call = False
                if isinstance(child.func, ast.Name):
                    func_name = child.func.id
                elif isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        receiver = current_scope.lookup(child.func.value.id)
                        func_name = child.func.attr
                        is_method_call = True

                call_entity = CallEntity(
                    node_id=next_node_id(),
                    name=func_name,
                    line=child.lineno,
                    ast_node=child,
                    args=_convert_call_args(child.args),
                    keywords=_convert_keywords(child.keywords),
                    is_method_call=is_method_call,
                    receiver=receiver.name if receiver else None,
                    scope=current_scope,
                )
                CALL_MAP[call_entity.node_id] = call_entity
                CHILDREN_MAP.setdefault(current_scope.node_id, []).append(
                    call_entity.node_id
                )

    for child_id in CHILDREN_MAP.get(scope.node_id, []):
        child_scope = SCOPE_MAP.get(child_id)
        if child_scope and child_scope is not scope:
            _collect_calls(child_scope)


def _process_node(node: ast.AST, current_scope: Scope, parent_id: int):
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
        _process_node(child, scope_for_children, parent_id=node_id)


def analyze_module(module_node: ast.Module, module_name: str):
    node_id = next_node_id()
    module_entity = ModuleEntity(
        name=module_name, line=0, node_id=node_id, ast_node=module_node
    )
    module_scope = ModuleScope(node_id, module_name)

    NODE_ID_MAP[node_id] = module_entity
    SCOPE_MAP[node_id] = module_scope
    MODULE_MAP[node_id] = module_entity

    _process_node(module_node, module_scope, parent_id=node_id)
    _build_module_dataflow(module_scope)
    _collect_calls(module_scope)
    return module_entity, module_scope
