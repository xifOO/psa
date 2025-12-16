import ast
from typing import Dict, NamedTuple, Set

from entity import CallEntity, FunctionEntity, GlobalDeclEntity, NonlocalDeclEntity, VariableEntity
from index.scopes import CHILDREN_MAP, NODE_ID_MAP


class SideEffect(NamedTuple):
    reads: frozenset[str]
    writes: frozenset[str]
    mutates: frozenset[tuple[str, str]]
    rebinds: frozenset[str]


MUTATING_METHODS = {
    "append", "extend", "insert", "remove", "pop",
    "update", "clear", "add", "discard"
}

SIDE_EFFECT_MAP: Dict[int, SideEffect] = {}


def _collect_rebinds(func: FunctionEntity, global_names, nonlocal_names):
    rebinds: Set[str] = set()

    for node in ast.walk(func.ast_node):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    if t.id not in global_names and t.id not in nonlocal_names:
                        rebinds.add(t.id)
        
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                if node.target.id not in global_names and node.target.id not in nonlocal_names:
                    rebinds.add(node.target.id)

        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name):
                if node.target.id not in global_names and node.target.id not in nonlocal_names:
                    rebinds.add(node.target.id)

        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                if node.target.id not in global_names and node.target.id not in nonlocal_names:
                    rebinds.add(node.target.id)

        elif isinstance(node, ast.withitem):
            if isinstance(node.optional_vars, ast.Name):
                if node.optional_vars.id not in global_names and node.optional_vars.id not in nonlocal_names:
                    rebinds.add(node.optional_vars.id)

        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                if node.name not in global_names and node.name not in nonlocal_names:
                    rebinds.add(node.name)

    return rebinds

def analyze_function(func: FunctionEntity):
    local_names = {arg.name for arg in func.args}

    child_ids = CHILDREN_MAP.get(func.node_id, [])

    global_names: Set[str] = set()
    nonlocal_names: Set[str] = set()
    variable_entities = []

    local_bindings: Set[str] = {arg.name for arg in func.args}

    writes: Set[str] = set()
    mutated_arguments: Set[tuple[str, str]] = set()
    mutated_attributes: Set[tuple[str, str]] = set()
    reads: Set[str] = set()

    for child_id in child_ids:
        ent = NODE_ID_MAP.get(child_id)
        if isinstance(ent, VariableEntity):
            variable_entities.append(ent)
            if isinstance(ent.value, ast.Call):
                if isinstance(ent.value.func, ast.Attribute):
                    attr = ent.value.func.attr
                    if attr in MUTATING_METHODS:
                        if isinstance(ent.value.func.value, ast.Name):
                            obj_name = ent.value.func.value.id
                            if obj_name in {arg.name for arg in func.args}:
                                mutated_arguments.add((obj_name, attr))

        elif isinstance(ent, CallEntity):
            arg_names = {arg.name for arg in func.args}
            if ent.is_method_call and ent.receiver in arg_names:
                if ent.name in MUTATING_METHODS:
                    mutated_arguments.add(ent.receiver)

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
                mutated_attributes.add((target.value.id, target.attr))

    for child in ast.walk(func.ast_node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            if child.id not in global_names and child.id not in nonlocal_names:
                local_bindings.add(child.id)

    for node in ast.walk(func.ast_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in global_names:
            reads.add(node.id)

    info = SideEffect(
        reads=frozenset(reads),
        writes=frozenset(writes),
        mutates=frozenset(mutated_arguments.union(mutated_attributes)),
        rebinds=frozenset(_collect_rebinds(func, global_names, nonlocal_names))
    )

    return info