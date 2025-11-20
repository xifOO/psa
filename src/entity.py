from typing import Any, List, Optional


class CodeEntity:
    def __init__(self, node_id: int, name: str, line: int) -> None:
        self.node_id = node_id
        self.name = name
        self.line = line

    def __str__(self) -> str:
        return self.name


class ArgumentEntity(CodeEntity):
    __slots__ = (
        "name",
        "node_id",
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
        annotation: Optional[Any],
        default: Optional[Any],
        is_keyword_only: bool = False,
        is_positional_only: bool = False,
    ) -> None:
        self.annotation = annotation
        self.default = default
        self.is_keyword_only = is_keyword_only
        self.is_positional_only = is_positional_only
        super().__init__(node_id, name, line)


class FunctionEntity(CodeEntity):
    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        args: List[ArgumentEntity],
        decorators: List[str],
        returns: Optional[Any] = None,
        is_method: bool = False,
    ) -> None:
        self.args = args
        self.decorators = decorators
        self.returns = returns
        self.is_method = is_method
        super().__init__(node_id, name, line)


class ClassEntity(CodeEntity):
    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        bases: List[str],
        decorators: List[str],
        keywords: List[str],
    ) -> None:
        self.bases = bases
        self.decorators = decorators
        self.keywords = keywords
        super().__init__(node_id, name, line)


class ModuleEntity(CodeEntity):
    def __init__(self, node_id: int, name: str, line: int) -> None:
        super().__init__(node_id, name, line)

    def get_classes(self) -> List[ClassEntity]: ...

    def get_functions(self) -> List[FunctionEntity]: ...

    def find_node_by_name(self, name: str) -> Optional[CodeEntity]: ...


class ImportEntity(CodeEntity):
    def __init__(
        self, node_id: int, name: str, line: int, module_name: str, alias: Optional[str]
    ) -> None:
        self.module_name = module_name
        self.alias = alias
        super().__init__(node_id, name, line)


class VariableEntity(CodeEntity):
    def __init__(self, node_id: int, name: str, line: int, value: Any) -> None:
        self.value = value
        super().__init__(node_id, name, line)


class CallEntity(CodeEntity):
    def __init__(
        self,
        node_id: int,
        name: str,
        line: int,
        args: List[str],
        keywords: List[str],
        is_method_call: bool,
    ) -> None:
        self.args = args
        self.keywords = keywords
        self.is_method_call = is_method_call
        super().__init__(node_id, name, line)
