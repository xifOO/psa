from abc import ABC, abstractmethod
from typing import Any, Iterator, Type

from entity import CodeEntity
from index.maps import Index


class Analyzer(ABC):
    _ANALYZER_REGISTRY: set[Type["Analyzer"]] = set()

    def __init_subclass__(cls, **kwargs) -> None:
        """Register analyzer to registry."""
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            cls._ANALYZER_REGISTRY.add(cls)

    @abstractmethod
    def applies_to(self, entity: Any) -> bool: ...
    @abstractmethod
    def analyze(self, index: Index, entity: Any) -> Any: ...

    @classmethod
    def for_entity(cls, entity: CodeEntity) -> Iterator["Analyzer"]:
        for analyzer in cls._ANALYZER_REGISTRY:
            analyzer = analyzer()
            if analyzer.applies_to(entity):
                yield analyzer
