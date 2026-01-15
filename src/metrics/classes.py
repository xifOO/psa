from typing import Dict, NamedTuple, Set

from entity import ClassEntity, FunctionEntity
from index.maps import Index
from node import PropertyVisitor, SelfAttrVisitor, DynamicAttrVisitor


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


def analyze_class(index: Index, cls: ClassEntity) -> ClassMetrics:
    child_ids = index.children_map.get(cls.node_id)

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

    property_visitor = PropertyVisitor()
    property_visitor.visit(cls.ast_node)
    property_to_attr = property_visitor.property_to_attr

    for child_id in child_ids if child_ids else []:
        ent = index.node_map.get(child_id)

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

            self_visitor = SelfAttrVisitor(property_to_attr=property_to_attr)
            self_visitor.visit(ent.ast_node)

            dynamic_visitor = DynamicAttrVisitor()
            dynamic_visitor.visit(ent.ast_node)

            all_attrs_used = self_visitor.attrs_used | dynamic_visitor.attrs_used
            for attr in all_attrs_used:
                method_attr_usage[method_name].add(attr)

            instance_attrs.update(self_visitor.instance_attrs)
            instance_attrs.update(dynamic_visitor.attrs_used)

            attrs_read.update(self_visitor.attrs_read)
            attrs_read.update(dynamic_visitor.attrs_read)

            attrs_written.update(self_visitor.attrs_written)
            attrs_written.update(dynamic_visitor.attrs_written)

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
