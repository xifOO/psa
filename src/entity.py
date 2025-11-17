from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class ArgumentEntity:
    name: str
    annotation: Optional[Any]
    default: Optional[Any]
    is_keyword_only: bool = False
    is_positional_only: bool = False


@dataclass
class CodeEntity:
    name: str
    line: int


@dataclass
class FunctionEntity(CodeEntity):
    args: List[ArgumentEntity]
    decorators: List[str]
    type_params: List[str]
    returns: Optional[Any] = None

    is_method: bool = False


@dataclass
class ClassEntity(CodeEntity):
    bases: List[str]
    methods: List[FunctionEntity]
    decorators: List[str]
    keywords: List[str]
    type_params: List[str]
