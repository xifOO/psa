from typing import Final, FrozenSet, NamedTuple, Set, Tuple, TypeAlias

from psa.entity import (
    CallEntity,
    FunctionEntity,
    GlobalDeclEntity,
    NonlocalDeclEntity,
)
from psa.index.maps import Index
from psa.nodes import AssignVisitor, ExprEffectsVisitor


ArgName: TypeAlias = str
MethodName: TypeAlias = str
ObjectName: TypeAlias = str
AttrName: TypeAlias = str


MUTATING_METHODS: Final = {
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


class FuncMetrics(NamedTuple):
    args: FrozenSet[str]
    globals_written: FrozenSet[str]
    nonlocals_written: FrozenSet[str]
    attrs_read: FrozenSet[str]
    attrs_written: FrozenSet[str]
    attr_mutates: FrozenSet[Tuple[ObjectName, AttrName]]
    arg_mutates: FrozenSet[Tuple[ArgName, MethodName]]
    local_vars: FrozenSet[str]
    calls: FrozenSet[str]


def analyze_func(index: Index, func: FunctionEntity) -> FuncMetrics:
    child_ids = index.children_map.get(func.node_id)

    global_names: Set[str] = set()
    nonlocal_names: Set[str] = set()
    arg_names_set = {arg.name for arg in func.args}
    calls: Set[str] = set()
    arg_mutates: Set[Tuple[str, str]] = set()

    for child_id in child_ids if child_ids else []:
        ent = index.node_map.get(child_id) or index.call_map.get(child_id)

        if isinstance(ent, CallEntity):
            calls.add(ent.name)
            if (
                ent.is_method_call
                and ent.receiver in arg_names_set
                and ent.name in MUTATING_METHODS
            ):
                arg_mutates.add((ent.receiver, ent.name))

        elif isinstance(ent, GlobalDeclEntity):
            global_names.update(ent.names)

        elif isinstance(ent, NonlocalDeclEntity):
            nonlocal_names.update(ent.names)

    assign_visitor = AssignVisitor(
        args=arg_names_set,
        globals=global_names,
        nonlocals=nonlocal_names,
    )
    assign_visitor.visit(func.ast_node)

    expr_visitor = ExprEffectsVisitor(
        args=arg_names_set,
        globals=global_names,
        nonlocals=nonlocal_names,
    )
    expr_visitor.visit(func.ast_node)

    attr_mutates = assign_visitor.attr_mutates | expr_visitor.attr_mutates

    metrics = FuncMetrics(
        args=frozenset(arg_names_set),
        globals_written=frozenset(global_names),
        nonlocals_written=frozenset(nonlocal_names),
        attrs_read=frozenset(expr_visitor.attrs_read),
        attrs_written=frozenset(assign_visitor.attrs_written),
        attr_mutates=frozenset(attr_mutates),
        arg_mutates=frozenset(arg_mutates),
        local_vars=frozenset(assign_visitor.locals_written),
        calls=frozenset(calls),
    )

    return metrics
