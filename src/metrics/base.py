from abc import ABC, abstractmethod
from typing import Any, List, Type

_ANALYZER_REGISTRY: set[Type["Analyzer"]] = set()


class Analyzer(ABC):
    def __init_subclass__(cls, **kwargs) -> None:
        """Register analyzer to registry."""
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            _ANALYZER_REGISTRY.add(cls)

    @abstractmethod
    def applies_to(self, entity: Any) -> bool: ...
    @abstractmethod
    def analyze(self, entity: Any) -> Any: ...


def get_registered_analyzers() -> List[Type[Analyzer]]:
    return list(_ANALYZER_REGISTRY)
