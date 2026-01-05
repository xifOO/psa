import ast
from typing import Dict, ItemsView, List, Optional, ValuesView

from entity import (
    ArgumentEntity,
    CodeEntity,
    ImportEntity,
    VariableEntity,
)

from maps import Index


class Scope:
    def __init__(
        self,
        node_id: int,
        name: str,
        index: Index,
        parent_scope: Optional["Scope"] = None,
    ) -> None:
        self.node_id = node_id
        self.name = name
        self.index = index
        self.parent_scope = parent_scope
        self.entities: Dict[str, CodeEntity] = {}

    def define(self, entity: CodeEntity) -> None:
        self.entities[entity.name] = entity

    def lookup(self, name: str) -> Optional[CodeEntity]:
        entity = self.entities.get(name, None)
        if not entity:
            if self.parent_scope:
                entity = self.parent_scope.lookup(name)

        return entity

    def get_values(self) -> ValuesView[CodeEntity]:
        return self.entities.values()

    def get_items(self) -> ItemsView[str, CodeEntity]:
        return self.entities.items()

    def __str__(self) -> str:
        return self.name


class ModuleScope(Scope):
    def __init__(
        self,
        node_id: int,
        name: str,
        index: Index,
        parent_scope: Optional["Scope"] = None,
    ) -> None:
        super().__init__(node_id, name, index, parent_scope)

    def get_imports(self) -> List[CodeEntity]:
        imports = []
        childrens = self.index.children_map.get(self.node_id) or []
        for child_id in childrens:
            child = self.index.node_map.get(child_id)
            if isinstance(child, ImportEntity):
                imports.append(child)

        return imports

    def get_variables(self) -> List[VariableEntity]:
        vars = []
        childrens = self.index.children_map.get(self.node_id) or []
        for child_id in childrens:
            child = self.index.node_map.get(child_id)
            if isinstance(child, ast.Store):
                vars.append(child)

        return vars


class ClassScope(Scope):
    def __init__(
        self,
        node_id: int,
        name: str,
        index: Index,
        parent_scope: Optional["Scope"] = None,
    ) -> None:
        super().__init__(node_id, name, index, parent_scope)

    def define_method(self, entity: CodeEntity):
        self.define(entity)


class FuncScope(Scope):
    def __init__(
        self,
        node_id: int,
        name: str,
        index: Index,
        parent_scope: Optional["Scope"] = None,
    ) -> None:
        super().__init__(node_id, name, index, parent_scope)

    def get_arguments(self) -> List[ArgumentEntity]:
        args = []
        childrens = self.index.children_map.get(self.node_id) or []

        for child_id in childrens:
            child = self.index.node_map.get(child_id)
            if isinstance(child, ArgumentEntity):
                args.append(child)

        return args
