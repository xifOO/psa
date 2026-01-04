import ast
from types import EllipsisType
from typing import Dict, NamedTuple, Optional, Set, TypeAlias, Tuple, Union

from entity import ClassEntity, FunctionEntity
from index.scopes import CHILDREN_MAP, NODE_ID_MAP


STATE: TypeAlias = str
ATTR_NAME: TypeAlias = Union[str, bytes, bool, int, float, complex, None, EllipsisType]
DYNAMIC_ATTRS_TUPLE: TypeAlias = Tuple[STATE, ATTR_NAME]
ATTR_FUNCS = {"setattr": "write", "delattr": "write", "getattr": "read"}


class ClassMetrics(NamedTuple):
    instance_attrs: frozenset[str]
    class_attrs: frozenset[str]
    public_methods: frozenset[str]
    private_methods: frozenset[str]
    static_methods: frozenset[str]
    class_methods: frozenset[str]
    property_methods: frozenset[str]
    base_classes: frozenset[str]
    attrs_read: frozenset[str]
    attrs_written: frozenset[str]

    method_attr_usage: dict[str, frozenset[str]]


CLASS_METRICS_MAP: Dict[int, ClassMetrics] = {}


def track_dynamic_attr_usage(node: ast.Call) -> Optional[DYNAMIC_ATTRS_TUPLE]:
    if isinstance(node.func, ast.Name):
        if node.func.id in ATTR_FUNCS:
            if (
                len(node.args) >= 2
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "self"
            ):
                if isinstance(node.args[1], ast.Constant):
                    attr_name = node.args[1].value
                    action = ATTR_FUNCS[node.func.id]
                    return (action, attr_name)

    elif isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Call):
            call = node.func.value
            if (
                isinstance(call.func, ast.Name)
                and call.func.id == "vars"
                and len(call.args) >= 1
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id == "self"
            ):
                method = node.func.attr
                if method == "get" and len(node.args) >= 1:
                    if isinstance(node.args[0], ast.Constant):
                        return ("read", node.args[0].value)

    return None


def track_subscript_attr_access(node: ast.Subscript) -> Optional[DYNAMIC_ATTRS_TUPLE]:
    if not isinstance(node.slice, ast.Constant):
        return None

    attr_name = node.slice.value

    if isinstance(node.ctx, ast.Store):
        state = "write"
    elif isinstance(node.ctx, ast.Load):
        state = "read"
    else:
        return None

    if isinstance(node.value, ast.Attribute):
        if (
            isinstance(node.value.value, ast.Name)
            and node.value.value.id == "self"
            and node.value.attr == "__dict__"
        ):
            return (state, attr_name)

    elif isinstance(node.value, ast.Call):
        if (
            isinstance(node.value.func, ast.Name)
            and node.value.func.id == "vars"
            and len(node.value.args) >= 1
            and isinstance(node.value.args[0], ast.Name)
            and node.value.args[0].id == "self"
        ):
            return (state, attr_name)

    return None


def get_methods(metrics: ClassMetrics) -> Set[str]:
    all_methods = metrics.public_methods.union(metrics.private_methods)

    exclude = metrics.static_methods.union(
        metrics.class_methods.union(metrics.property_methods)
    )

    methods = set()

    for method in all_methods:
        if method.startswith("__") and method.endswith("__"):
            continue

        if method in exclude:
            continue

        methods.add(method)

    return methods


def analyze_class(cls: ClassEntity) -> ClassMetrics:
    child_ids = CHILDREN_MAP.get(cls.node_id, [])

    instance_attrs: Set[str] = set()
    class_attrs: Set[str] = set()
    public_methods: Set[str] = set()
    private_methods: Set[str] = set()
    static_methods: Set[str] = set()
    class_methods: Set[str] = set()
    property_methods: Set[str] = set()
    method_attr_usage: Dict[str, Set[str]] = dict()

    attrs_read: Set[str] = set()
    attrs_written: Set[str] = set()

    property_to_attr: dict[str, str] = dict()

    for child_id in child_ids:
        ent = NODE_ID_MAP.get(child_id)

        if isinstance(ent, FunctionEntity) and ent.is_method:
            method_name = ent.name

            if method_name not in method_attr_usage:
                method_attr_usage[method_name] = set()

            if method_name.startswith("_") and not method_name.startswith("__"):
                private_methods.add(method_name)
            else:
                public_methods.add(method_name)

            if "staticmethod" in ent.decorators:
                static_methods.add(method_name)
            if "classmethod" in ent.decorators:
                class_methods.add(method_name)
            if "property" in ent.decorators:
                property_methods.add(method_name)

            for node in ast.walk(ent.ast_node):
                if isinstance(node, ast.Call):
                    dynamic_attr = track_dynamic_attr_usage(node)
                    if dynamic_attr is not None:
                        state, attr_name = dynamic_attr

                        method_attr_usage[method_name].add(str(attr_name))
                        instance_attrs.add(str(attr_name))

                        if state == "write":
                            attrs_written.add(str(attr_name))
                        elif state == "read":
                            attrs_read.add(str(attr_name))

                elif (
                    isinstance(node, ast.FunctionDef) and node.name in property_methods
                ):
                    for stmt in node.body:
                        if isinstance(stmt, ast.Return) and isinstance(
                            stmt.value, ast.Attribute
                        ):
                            if (
                                isinstance(stmt.value.value, ast.Name)
                                and stmt.value.value.id == "self"
                            ):
                                attr = stmt.value.attr
                                property_to_attr[node.name] = attr

                elif isinstance(node, ast.Subscript):
                    subscript_attr = track_subscript_attr_access(node)
                    if subscript_attr is not None:
                        state, attr_name = subscript_attr
                        method_attr_usage[method_name].add(str(attr_name))
                        instance_attrs.add(str(attr_name))

                        if state == "write":
                            attrs_written.add(str(attr_name))
                        elif state == "read":
                            attrs_read.add(str(attr_name))

                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name) and node.value.id == "self":
                        attr = node.attr
                        if attr in property_to_attr:
                            method_attr_usage[method_name].add(property_to_attr[attr])
                        else:
                            method_attr_usage[method_name].add(attr)

                        if isinstance(node.ctx, ast.Store):
                            attrs_written.add(attr)
                            instance_attrs.add(attr)

                        elif isinstance(node.ctx, ast.Load):
                            attrs_read.add(attr)

    frozen_method_attr_usage = {
        method: frozenset(attrs) for method, attrs in method_attr_usage.items()
    }

    return ClassMetrics(
        instance_attrs=frozenset(instance_attrs),
        class_attrs=frozenset(class_attrs),
        public_methods=frozenset(public_methods),
        private_methods=frozenset(private_methods),
        static_methods=frozenset(static_methods),
        class_methods=frozenset(class_methods),
        property_methods=frozenset(property_methods),
        base_classes=frozenset(cls.bases),
        attrs_read=frozenset(attrs_read),
        attrs_written=frozenset(attrs_written),
        method_attr_usage=frozen_method_attr_usage,
    )
