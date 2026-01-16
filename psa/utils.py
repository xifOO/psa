import ast
from typing import List, Optional

from psa.entity import (
    ArgumentEntity,
    ClassEntity,
    FunctionEntity,
    GlobalDeclEntity,
    ImportEntity,
    NonlocalDeclEntity,
    VariableEntity,
)
from itertools import count

from psa.index.scopes import ClassScope, Scope


_node_id_gen = count(1)
next_node_id = lambda: next(_node_id_gen)  # later move to builders


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
            name="<global>",
            node_id=next_node_id(),
            names=node.names,
            line=node.lineno,
            ast_node=node,
        )

    elif isinstance(node, ast.Nonlocal):
        return NonlocalDeclEntity(
            name="<nonlocal>",
            node_id=next_node_id(),
            names=node.names,
            line=node.lineno,
            ast_node=node,
        )

    return None
