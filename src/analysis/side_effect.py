import ast
from typing import Dict, List, NamedTuple, Set, TypeAlias

from entity import CallEntity, FunctionEntity, GlobalDeclEntity, NonlocalDeclEntity, VariableEntity
from index.call import CALL_MAP
from index.scopes import CHILDREN_MAP, NODE_ID_MAP


ArgName: TypeAlias = str
MethodName: TypeAlias = str

ObjectName: TypeAlias = str
AttrName: TypeAlias = str


class SideEffect(NamedTuple):
    reads: frozenset[str]
    writes: frozenset[str]
    mutates: frozenset[tuple[str, str]]


MUTATING_METHODS = {
    "append", "extend", "insert", "remove", "pop",
    "update", "clear", "add", "discard"
}

SIDE_EFFECT_MAP: Dict[int, SideEffect] = {}


def analyze_function(func: FunctionEntity):
    child_ids = CHILDREN_MAP.get(func.node_id, [])

    global_names: Set[str] = set()
    nonlocal_names: Set[str] = set()
    local_names: Set[str] = {arg.name for arg in func.args}
    variable_entities: List[VariableEntity] = []

    writes: Set[str] = set()
    mutated_arguments: Set[tuple[ArgName, MethodName]] = set()
    mutated_attributes: Set[tuple[ObjectName, AttrName]] = set()
    reads: Set[str] = set()

    for child_id in child_ids:
        ent = NODE_ID_MAP.get(child_id) or CALL_MAP.get(child_id)
        
        if isinstance(ent, VariableEntity):
            variable_entities.append(ent)
                
        elif isinstance(ent, CallEntity):
            arg_names = {arg.name for arg in func.args}
            if ent.is_method_call and ent.receiver in arg_names:
                mutated_arguments.add((ent.receiver, ent.name))

        elif isinstance(ent, GlobalDeclEntity):
            global_names.update(ent.names)

        elif isinstance(ent, NonlocalDeclEntity):
            nonlocal_names.update(ent.names)

    for var in variable_entities:
        if var.name in global_names:
            writes.add(var.name)
            continue

        target = None
        node = var.ast_node
        if isinstance(node, ast.Assign):
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            target = node.target

        if isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name):
                attr = target.value.id
                if attr in global_names or attr in nonlocal_names or attr in {arg.name for arg in func.args}:
                    mutated_attributes.add((attr, target.attr))

    for node in ast.walk(func.ast_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in global_names:
            reads.add(node.id)

    info = SideEffect(
        reads=frozenset(reads),
        writes=frozenset(writes),
        mutates=frozenset(mutated_arguments.union(mutated_attributes))
    )

    return info