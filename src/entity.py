import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional


if TYPE_CHECKING:
    from node import ExprInfo
    from index.scopes import Scope


@dataclass(slots=True, kw_only=True)
class CodeEntity:
    node_id: int
    name: str
    line: int
    ast_node: ast.AST = field(repr=False)

    def __str__(self) -> str:
        return self.name


@dataclass(slots=True, kw_only=True)
class ArgumentEntity(CodeEntity):
    annotation: Optional[Any] = None
    default: Optional[Any] = None
    is_keyword_only: bool = False
    is_positional_only: bool = False


@dataclass(slots=True, kw_only=True)
class FunctionEntity(CodeEntity):
    args: List[ArgumentEntity] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    returns: Optional[Any] = None
    is_method: bool = False


@dataclass(slots=True, kw_only=True)
class ClassEntity(CodeEntity):
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class ModuleEntity(CodeEntity): ...


@dataclass(slots=True, kw_only=True)
class ImportEntity(CodeEntity):
    module_name: str
    alias: Optional[str] = None


@dataclass(slots=True, kw_only=True)
class VariableEntity(CodeEntity):
    value: Any = None


@dataclass(slots=True, kw_only=True)
class GlobalDeclEntity(CodeEntity):
    names: List[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class NonlocalDeclEntity(CodeEntity):
    names: List[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class CallEntity(CodeEntity):
    args: List["ExprInfo"] = field(default_factory=list)
    keywords: Dict[str, "ExprInfo"] = field(default_factory=dict)
    scope: "Scope" = field(repr=False)
    is_method_call: bool = False
    receiver: Optional[str] = None
