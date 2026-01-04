from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from config.rules import Config, Severity


@dataclass
class Violation:
    rule_id: str
    severity: Severity
    message: str
    context: dict[str, Any]


class Rule(ABC):
    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def applies_to(self, diff: Any) -> bool: ...

    @abstractmethod
    def check(self, diff: Any, context: dict[str, Any]) -> list[Violation]: ...
