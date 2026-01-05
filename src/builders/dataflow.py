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

        for child_id in self.index.children_map.get(scope.node_id) or []:
            child_scope = self.index.scope_map.get(child_id)
            if child_scope:
                self.run(child_scope)

    def _build_variable_dependencies(self, scope: Scope, entity: CodeEntity):
        if not isinstance(entity, VariableEntity):
            return

        deps = set()
        for node in ast.walk(entity.value):
            if isinstance(node, ast.Name):
                dep = scope.lookup(node.id)
                if dep:
                    deps.add(dep.node_id)

        for dep in deps:
            self.index.dataflow_map.add(entity.node_id, dep)
