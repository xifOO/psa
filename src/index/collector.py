from .maps import Index
from entity import CodeEntity
from index.scopes import Scope


class EntityCollector:
    def __init__(self, index: Index) -> None:
        self._index = index

    def collect(self) -> list[CodeEntity]:
        root = self._index.scope_map.get_root()

        if not root:
            return []

        entities: list[CodeEntity] = []
        self._collect_scope(root, entities)
        return entities

    def _collect_scope(self, scope: Scope, out: list[CodeEntity]) -> None:
        out.extend(scope.get_values())

        for child in scope.children:
            self._collect_scope(child, out)
