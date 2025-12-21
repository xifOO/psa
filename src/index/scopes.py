import ast
from typing import Dict, ItemsView, List, Optional, Type, ValuesView

from entity import (
    ArgumentEntity,
    ClassEntity,
    CodeEntity,
    FunctionEntity,
    GlobalDeclEntity,
    ImportEntity,
    ModuleEntity,
    NonlocalDeclEntity,
    VariableEntity,
)


NODE_ID_MAP: Dict[int, CodeEntity] = {}
PARENT_MAP: Dict[int, int] = {}
CHILDREN_MAP: Dict[int, List[int]] = {}
SCOPE_MAP: Dict[int, "Scope"] = {}
TYPE_MAP: Dict[int, Type] = {}
MODULE_MAP: Dict[int, ModuleEntity] = {}


class Scope:
    def __init__(
        self, node_id: int, name: str, parent_scope: Optional["Scope"] = None
    ) -> None:
        self.node_id = node_id
        self.name = name
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
        self, node_id: int, name: str, parent_scope: Optional[Scope] = None
    ) -> None:
        super().__init__(node_id, name, parent_scope)

    def get_imports(self) -> List[CodeEntity]:
        imports = []

        for child_id in CHILDREN_MAP[self.node_id]:
            child = NODE_ID_MAP[child_id]
            if isinstance(child, ImportEntity):
                imports.append(child)

        return imports

    def get_variables(self) -> List[VariableEntity]:
        vars = []

        for child_id in CHILDREN_MAP[self.node_id]:
            child = NODE_ID_MAP[child_id]
            if isinstance(child, ast.Store):
                vars.append(child)

        return vars


class ClassScope(Scope):
    def __init__(
        self, node_id: int, name: str, parent_scope: Optional[Scope] = None
    ) -> None:
        super().__init__(node_id, name, parent_scope)

    def define_method(self, entity: CodeEntity):
        self.define(entity)


class FuncScope(Scope):
    def __init__(
        self, node_id: int, name: str, parent_scope: Optional[Scope] = None
    ) -> None:
        super().__init__(node_id, name, parent_scope)

    def get_arguments(self) -> List[ArgumentEntity]:
        args = []

        for child_id in CHILDREN_MAP[self.node_id]:
            child = NODE_ID_MAP[child_id]
            if isinstance(child, ArgumentEntity):
                args.append(child)

        return args


from itertools import count

_node_id_gen = count(1)
next_node_id = lambda: next(_node_id_gen)


def _convert_args(args_node: ast.arguments) -> List[ArgumentEntity]:
    args: List[ArgumentEntity] = []

    for arg in args_node.posonlyargs:
        args.append(
            ArgumentEntity(
                name=arg.arg,
                node_id=next_node_id(),
                line=arg.lineno,
                ast_node=arg,
                annotation=arg.annotation,
                default=None,
                is_keyword_only=False,
                is_positional_only=True,
            )
        )

    for arg in args_node.args:
        args.append(
            ArgumentEntity(
                name=arg.arg,
                node_id=next_node_id(),
                line=arg.lineno,
                ast_node=arg,
                annotation=arg.annotation,
                default=None,
                is_keyword_only=False,
                is_positional_only=False,
            )
        )

    if args_node.vararg:
        arg = args_node.vararg
        args.append(
            ArgumentEntity(
                name=arg.arg,
                node_id=next_node_id(),
                line=arg.lineno,
                ast_node=arg,
                annotation=arg.annotation,
                default=None,
                is_keyword_only=False,
                is_positional_only=False,
            )
        )

    for arg in args_node.kwonlyargs:
        args.append(
            ArgumentEntity(
                name=arg.arg,
                node_id=next_node_id(),
                line=arg.lineno,
                ast_node=arg,
                annotation=arg.annotation,
                default=None,
                is_keyword_only=True,
                is_positional_only=False,
            )
        )

    if args_node.kwarg:
        arg = args_node.kwarg
        args.append(
            ArgumentEntity(
                name=arg.arg,
                node_id=next_node_id(),
                line=arg.lineno,
                ast_node=arg,
                annotation=arg.annotation,
                default=None,
                is_keyword_only=True,
                is_positional_only=False,
            )
        )

    return args


def _convert_decorators(decorator_list: List[ast.expr]) -> List[str]:
    decorators = []
    for dec in decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)

    return decorators


def _convert_keywords(keywords: List[ast.keyword]) -> List[str]:
    kws = []
    for kw in keywords:
        if kw.arg is not None:
            kws.append(kw.arg)
    return kws


def _convert_bases(bases_nodes: List[ast.expr]) -> List[str]:
    result = []
    for base in bases_nodes:
        if isinstance(base, ast.Name):
            result.append(base.id)
        elif isinstance(base, ast.Attribute):
            parts = []
            curr = base
            while isinstance(curr, ast.Attribute):
                parts.append(curr.attr)
                curr = curr.value
            if isinstance(curr, ast.Name):
                parts.append(curr.id)
            result.append(".".join(reversed(parts)))
        else:
            result.append(None)
    return result


def _convert_import_aliases(names: List[ast.alias]) -> Optional[str]:
    if not names:
        return None
    first = names[0]
    return first.asname if first.asname is not None else first.name


def _convert_call_args(args: List[ast.expr]) -> List[str]:
    args_list = []
    for node in args:
        if isinstance(node, ast.Constant):
            args_list.append(node.value)
        if isinstance(node, ast.Name):
            args_list.append(node.id)
    return args_list


def _convert_func_info(func: ast.expr):
    if isinstance(func, ast.Name):
        return ("name", func.id)

    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name):
            return ("attr", func.value.id, func.attr)
        return None

    return None


def wrap_ast_node(node: ast.AST, parent_scope: Optional[Scope] = None):
    if isinstance(node, ast.FunctionDef):
        is_method = isinstance(parent_scope, ClassScope)
        return FunctionEntity(
            name=node.name,
            node_id=next_node_id(),
            line=node.lineno,
            ast_node=node,
            args=_convert_args(node.args),
            decorators=_convert_decorators(node.decorator_list),
            returns=node.returns,
            is_method=is_method,
        )

    elif isinstance(node, ast.ClassDef):
        return ClassEntity(
            name=node.name,
            node_id=next_node_id(),
            line=node.lineno,
            ast_node=node,
            bases=_convert_bases(node.bases),
            decorators=_convert_decorators(node.decorator_list),
            keywords=_convert_keywords(node.keywords),
        )

    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        return ImportEntity(
            name="import",
            node_id=next_node_id(),
            line=node.lineno,
            ast_node=node,
            module_name=parent_scope.__module__,
            alias=_convert_import_aliases(node.names),
        )

    elif isinstance(node, ast.arg):
        return ArgumentEntity(
            name=node.arg,
            node_id=next_node_id(),
            line=node.lineno,
            ast_node=node,
            annotation=None,
            default=None,
        )

    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        var_name = ""  # пока заглушка
        if isinstance(target, ast.Name):
            var_name = target.id

        return VariableEntity(
            name=var_name,
            node_id=next_node_id(),
            line=node.lineno,
            ast_node=node,
            value=node.value,
        )

    elif isinstance(node, ast.Global):
        return GlobalDeclEntity(
            node_id=next_node_id(), names=node.names, line=node.lineno, ast_node=node
        )

    elif isinstance(node, ast.Nonlocal):
        return NonlocalDeclEntity(
            node_id=next_node_id(), names=node.names, line=node.lineno, ast_node=node
        )

    return None
