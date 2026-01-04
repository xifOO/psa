import ast
from typing import List, NamedTuple, Set, TypeAlias

from entity import (
    CallEntity,
    FunctionEntity,
    GlobalDeclEntity,
    NonlocalDeclEntity,
    VariableEntity,
)
from index.call import CALL_MAP
from index.scopes import CHILDREN_MAP, NODE_ID_MAP


ArgName: TypeAlias = str
MethodName: TypeAlias = str
ObjectName: TypeAlias = str
AttrName: TypeAlias = str


class FuncMetrics(NamedTuple):
    args: frozenset[str]
    globals_written: frozenset[str]
    nonlocals_written: frozenset[str]
    attrs_read: frozenset[str]
    attrs_written: frozenset[str]
    attr_mutates: frozenset[tuple[ObjectName, AttrName]]
    arg_mutates: frozenset[tuple[ArgName, MethodName]]
    local_vars: frozenset[str]
    calls: frozenset[str]


MUTATING_METHODS = {
    "append",
    "extend",
    "insert",
    "remove",
    "pop",
    "update",
    "clear",
    "add",
    "discard",
}


def analyze_func(func: FunctionEntity) -> FuncMetrics:
    child_ids = CHILDREN_MAP.get(func.node_id, [])

    global_names: Set[str] = set()
    nonlocal_names: Set[str] = set()
    local_vars: Set[str] = set()
    attrs_read: Set[str] = set()
    attrs_written: Set[str] = set()
    attr_mutates: Set[tuple[str, str]] = set()
    arg_mutates: Set[tuple[str, str]] = set()
    calls: Set[str] = set()

    variable_entities: List[VariableEntity] = []

    for child_id in child_ids:
        ent = NODE_ID_MAP.get(child_id) or CALL_MAP.get(child_id)

        if isinstance(ent, VariableEntity):
            variable_entities.append(ent)

        elif isinstance(ent, CallEntity):
            calls.add(ent.name)
            arg_names = {arg.name for arg in func.args}
            if (
                ent.is_method_call
                and ent.receiver in arg_names
                and ent.name in MUTATING_METHODS
            ):
                arg_mutates.add((ent.receiver, ent.name))

        elif isinstance(ent, GlobalDeclEntity):
            global_names.update(ent.names)

        elif isinstance(ent, NonlocalDeclEntity):
            nonlocal_names.update(ent.names)

    arg_names_set = {arg.name for arg in func.args}
    for var in variable_entities:
        var_name = var.name
        if var_name not in global_names and var_name not in nonlocal_names:
            local_vars.add(var_name)

        node = var.ast_node
        target = None
        if isinstance(node, ast.Assign):
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            target = node.target

        if isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name):
                obj_name = target.value.id
                if obj_name in global_names | nonlocal_names | arg_names_set:
                    attr_mutates.add((obj_name, target.attr))
                else:
                    attrs_written.add(f"{obj_name}.{target.attr}")

        elif isinstance(target, ast.Subscript):
            value = target.value
            if isinstance(value, ast.Name):
                obj_name = value.id
                if obj_name in global_names | nonlocal_names | arg_names_set:
                    attr_mutates.add((obj_name, "__setitem__"))
                else:
                    attrs_written.add(f"{obj_name}.__setitem__")

    for node in ast.walk(func.ast_node):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if isinstance(node.value, ast.Name):
                obj_name = node.value.id
                if obj_name in arg_names_set | global_names | nonlocal_names:
                    attr_mutates.add((obj_name, node.attr))
                else:
                    attrs_read.add(f"{obj_name}.{node.attr}")

        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in global_names:
                attrs_read.add(node.id)

    metrics = FuncMetrics(
        args=frozenset(arg_names_set),
        globals_written=frozenset(global_names),
        nonlocals_written=frozenset(nonlocal_names),
        attrs_read=frozenset(attrs_read),
        attrs_written=frozenset(attrs_written),
        attr_mutates=frozenset(attr_mutates),
        arg_mutates=frozenset(arg_mutates),
        local_vars=frozenset(local_vars),
        calls=frozenset(calls),
    )

    return metrics
