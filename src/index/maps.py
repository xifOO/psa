from itertools import count
from typing import List, Optional, Protocol, Set, TypeAlias, TypeVar, runtime_checkable
from entity import CallEntity, CodeEntity
from index.scopes import Scope


K = TypeVar("K", contravariant=True)
V = TypeVar("V", covariant=True)

ID: TypeAlias = int


@runtime_checkable
class Indexable(Protocol[K, V]):
    def get(self, key: K) -> Optional[V]: ...


class NodeMap(Indexable[ID, CodeEntity]):
    def __init__(self) -> None:
        self.node_map: dict[ID, CodeEntity] = {}

    def add(self, entity: CodeEntity) -> None:
        self.node_map[entity.node_id] = entity

    def get(self, key: ID) -> Optional[CodeEntity]:
        return self.node_map.get(key, None)


class ChildrenMap(Indexable[ID, List[ID]]):
    def __init__(self) -> None:
        self.parent_map: dict[ID, int] = {}
        self.children_map: dict[ID, List[int]] = {}

    def link(self, parent_id: ID, child_id: ID) -> None:
        self.parent_map[child_id] = parent_id
        self.children_map.setdefault(parent_id, []).append(child_id)

    def get(self, key: ID) -> Optional[List[int]]:
        return self.children_map.get(key, None)


class ScopeMap(Indexable[ID, Scope]):
    def __init__(self) -> None:
        self.scope_map: dict[ID, Scope] = {}
        self._root: Optional[Scope] = None

    def add(self, scope: Scope) -> None:
        self.scope_map[scope.node_id] = scope
        if scope.parent_scope is None:
            self._root = scope

    def get(self, key: ID) -> Optional[Scope]:
        return self.scope_map.get(key, None)

    def get_root(self) -> Optional[Scope]:
        return self._root


class CallMap(Indexable[ID, CallEntity]):
    def __init__(self) -> None:
        self.call_map: dict[ID, CallEntity] = {}

    def add(self, call: CallEntity):
        self.call_map[call.node_id] = call

    def get(self, key: ID) -> Optional[CallEntity]:
        return self.call_map.get(key, None)


class DataflowMap(Indexable[ID, Set[ID]]):
    def __init__(self) -> None:
        self.dataflow_map: dict[ID, Set[ID]] = {}

    def add(self, src: ID, dst: ID) -> None:
        self.dataflow_map.setdefault(src, set()).add(dst)

    def get(self, key: ID) -> Optional[Set[ID]]:
        return self.dataflow_map.get(key, None)


class Index:
    def __init__(self) -> None:
        self.node_map = NodeMap()
        self.children_map = ChildrenMap()
        self.scope_map = ScopeMap()
        self.call_map = CallMap()
        self.dataflow_map = DataflowMap()

        self._node_id_gen = count(1)

    def next_node_id(self) -> int:
        return next(self._node_id_gen)
