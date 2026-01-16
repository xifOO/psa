from abc import ABC, abstractmethod
from typing import Any


class BaseReporter(ABC):
    @abstractmethod
    def report(self, diff_type: str, diff: Any, context: dict[str, Any]) -> str: ...

    @abstractmethod
    def format_summary(self, results: list[tuple[str, Any, dict]]) -> str: ...
