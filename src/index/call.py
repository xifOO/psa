from typing import Dict, Set

from entity import CallEntity
from index.scopes import ClassScope, FuncScope, Scope


CALL_MAP: Dict[int, CallEntity] = {}


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
