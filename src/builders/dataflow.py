import ast
from index.maps import Index
from index.scopes import Scope
from entity import CodeEntity, VariableEntity


class DataflowBuilder:
    def __init__(self, index: Index) -> None:
        self.index = index

    def run(self, scope: Scope):
        for entity in scope.get_values():
            self._build_variable_dependencies(scope, entity)

        for child_scope in scope.children:
            self.run(child_scope)

    def _build_variable_dependencies(self, scope: Scope, entity: CodeEntity):
        if not isinstance(entity, VariableEntity):
            return

        deps = set()

        if entity.value is None:
            return

        for node in ast.walk(entity.value):
            if isinstance(node, ast.Name):
                dep = scope.lookup(node.id)
                if dep:
                    deps.add(dep.node_id)

        for dep in deps:
            self.index.dataflow_map.add(entity.node_id, dep)
