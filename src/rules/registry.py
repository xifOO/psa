from typing import Type
from rules.base import Rule

_RULE_REGISTRY: set[Type[Rule]] = set()


def register_rule(rule: Type[Rule]) -> Type[Rule]:
    _RULE_REGISTRY.add(rule)
    return rule


def get_registered_rule() -> list[Type[Rule]]:
    return list(_RULE_REGISTRY)