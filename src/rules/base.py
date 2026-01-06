from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Type

from config.rules import Config, Severity

_RULE_REGISTRY: set[Type["Rule"]] = set()


@dataclass
class Violation:
    rule_id: str
    severity: Severity
    message: str
    context: dict[str, Any]


class Rule(ABC):
    def __init__(self, config: Config) -> None:
        self.config = config

    def __init_subclass__(cls, **kwargs) -> None:
        """Register rule to registry."""
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            _RULE_REGISTRY.add(cls)

    @abstractmethod
    def applies_to(self, diff: Any) -> bool: ...
    @abstractmethod
    def check(self, diff: Any, context: dict[str, Any]) -> list[Violation]: ...


def get_registered_rule() -> list[Type[Rule]]:
    return list(_RULE_REGISTRY)
