from typing import Dict, Set

from entity import CallEntity, FunctionEntity
from index.scopes import CHILDREN_MAP, SCOPE_MAP, Scope


CALL_MAP: Dict[int, CallEntity] = {}


def collect_calls(scope: Scope):
    for entity in scope.entities.values():
        if isinstance(entity, CallEntity):
            CALL_MAP[entity.node_id] = entity
    
    for child_id in CHILDREN_MAP.get(scope.node_id, []):
        child_scope = SCOPE_MAP.get(child_id)
        if child_scope and child_scope is not scope:
            collect_calls(child_scope)


def build_call_graph() -> Dict[int, Set[int]]:
    graph: Dict[int, Set[int]] = {}

    for call_id, call_entity in CALL_MAP.items():
        call_scope = SCOPE_MAP.get(call_id)
        if not call_scope:
            continue
        
        caller_id = call_scope.node_id

        callee_entity = call_scope.lookup(call_entity.name)
        if callee_entity and isinstance(callee_entity, FunctionEntity):
            callee_id = callee_entity.node_id
        else:
            callee_id = call_entity.node_id

        graph.setdefault(caller_id, set()).add(callee_id)

    return graph
 



      