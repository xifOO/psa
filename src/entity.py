import ast
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from index.scopes import Scope


class CodeEntity:
    def __init__(self, node_id: int, name: str, line: int, ast_node: ast.AST) -> None:
        self.node_id = node_id
        self.name = name
        self.line = line
        self.ast_node = ast_node

    def __str__(self) -> str:
        return self.name


class ArgumentEntity(CodeEntity):
    __slots__ = (
        "name",
        "node_id",
        "ast_node",
        "annotation",
        "default",
        "is_keyword_only",
        "is_positional_only",
    )

    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        ast_node: ast.AST,
        annotation: Optional[Any],
        default: Optional[Any],
        is_keyword_only: bool = False,
        is_positional_only: bool = False,
    ) -> None:
        self.annotation = annotation
        self.default = default
        self.is_keyword_only = is_keyword_only
        self.is_positional_only = is_positional_only
        super().__init__(node_id, name, line, ast_node)


class FunctionEntity(CodeEntity):
    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        ast_node: ast.AST,
        args: List[ArgumentEntity],
        decorators: List[str],
        returns: Optional[Any] = None,
        is_method: bool = False,
    ) -> None:
        self.args = args
        self.decorators = decorators
        self.returns = returns
        self.is_method = is_method
        super().__init__(node_id, name, line, ast_node)


class ClassEntity(CodeEntity):
    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        ast_node: ast.AST,
        bases: List[str],
        decorators: List[str],
        keywords: List[str],
    ) -> None:
        self.bases = bases
        self.decorators = decorators
        self.keywords = keywords
        super().__init__(node_id, name, line, ast_node)


class ModuleEntity(CodeEntity):
    def __init__(self, node_id: int, name: str, line: int, ast_node: ast.AST) -> None:
        super().__init__(node_id, name, line, ast_node)

    def get_classes(self) -> List[ClassEntity]: ...

    def get_functions(self) -> List[FunctionEntity]: ...

    def find_node_by_name(self, name: str) -> Optional[CodeEntity]: ...


class ImportEntity(CodeEntity):
    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        ast_node: ast.AST,
        module_name: str,
        alias: Optional[str],
    ) -> None:
        self.module_name = module_name
        self.alias = alias
        super().__init__(node_id, name, line, ast_node)


class VariableEntity(CodeEntity):
    def __init__(
        self, node_id: int, name: str, line: int, ast_node: ast.AST, value: Any
    ) -> None:
        self.value = value
        super().__init__(node_id, name, line, ast_node)


class GlobalDeclEntity(CodeEntity):
    def __init__(
        self, node_id: int, names: list[str], line: int, ast_node: ast.Global
    ) -> None:
        self.names = names
        super().__init__(node_id, "<global>", line, ast_node)


class NonlocalDeclEntity(CodeEntity):
    def __init__(
        self, node_id: int, names: list[str], line: int, ast_node: ast.Nonlocal
    ) -> None:
        self.names = names
        super().__init__(node_id, "<nonlocal>", line, ast_node)


class CallEntity(CodeEntity):
    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        ast_node: ast.AST,
        args: List[str],
        keywords: List[str],
        scope: "Scope",
        is_method_call: bool,
        receiver: Optional[str] = None,
    ) -> None:
        self.args = args
        self.keywords = keywords
        self.is_method_call = is_method_call
        self.receiver = receiver
        self.scope = scope
        super().__init__(node_id, name, line, ast_node)
