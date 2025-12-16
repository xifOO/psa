import ast
from typing import Dict, Set

from entity import CallEntity
from index.scopes import CHILDREN_MAP, SCOPE_MAP, ClassScope, FuncScope, Scope, _convert_call_args, _convert_keywords, next_node_id

CALL_MAP: Dict[int, CallEntity] = {}


def collect_calls(scope: Scope):
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
                    scope=current_scope
                )
                CALL_MAP[call_entity.node_id] = call_entity
                CHILDREN_MAP.setdefault(current_scope.node_id, []).append(call_entity.node_id)

    for child_id in CHILDREN_MAP.get(scope.node_id, []):
        child_scope = SCOPE_MAP.get(child_id)
        if child_scope and child_scope is not scope:
            collect_calls(child_scope)


def _get_scope_name(scope: Scope) -> str:
    if isinstance(scope, FuncScope) and isinstance(scope.parent_scope, ClassScope):
        return f"{scope.parent_scope.name}.{scope.name}"
    return scope.name

def build_call_graph() -> Dict[str, Set[str]]:
    graph: Dict[str, Set[str]] = {}

    for ce in CALL_MAP.values():
        if ce.is_method_call and ce.receiver:
            caller_name = ce.receiver
        else:
            caller_name = _get_scope_name(ce.scope)

        graph.setdefault(caller_name, set()).add(ce.name)

    return graph

