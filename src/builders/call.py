import ast
from entity import CallEntity
from index.maps import Index
from index.scopes import Scope
from utils import _convert_call_args, _convert_keywords


class CallBuilder:
    def __init__(self, index: Index) -> None:
        self.index = index

    def run(self, scope: Scope):
        self._collect_calls(scope)

        for child_scope in scope.children:
            self.run(child_scope)

    def _collect_calls(self, scope: Scope):
        assert isinstance(scope, Scope)
        for entity in scope.get_values():
            node = entity.ast_node

            if node is None:
                continue

            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func_name = ""
                    receiver = None
                    is_method_call = False

                    if isinstance(child.func, ast.Name):
                        func_name = child.func.id
                    elif isinstance(child.func, ast.Attribute):
                        if isinstance(child.func.value, ast.Name):
                            receiver_entity = scope.lookup(child.func.value.id)
                            receiver = receiver_entity.name if receiver_entity else None
                            func_name = child.func.attr
                            is_method_call = True

                    call_entity = CallEntity(
                        node_id=self.index.next_node_id(),
                        name=func_name,
                        line=child.lineno,
                        ast_node=child,
                        args=_convert_call_args(child.args),
                        keywords=_convert_keywords(child.keywords),
                        is_method_call=is_method_call,
                        receiver=receiver,
                        scope=scope,
                    )

                    self.index.call_map.add(call_entity)
                    self.index.children_map.link(scope.node_id, call_entity.node_id)
