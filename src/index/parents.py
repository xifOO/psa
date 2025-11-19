import ast
from typing import Dict, List, Optional, Type

from entity import (
    ArgumentEntity,
    ClassEntity,
    CodeEntity,
    FunctionEntity,
    ImportEntity,
    ModuleEntity,
)

NODE_ID_MAP: Dict[int, CodeEntity] = {}
PARENT_MAP: Dict[int, int] = {}
CHILDREN_MAP: Dict[int, List[int]] = {}
SCOPE_MAP: Dict[int, "Scope"] = {}
TYPE_MAP: Dict[int, Type] = {}
MODULE_MAP: Dict[int, ModuleEntity] = {}


class Scope:
    def __init__(self, node_id: int, parent_scope: Optional["Scope"] = None) -> None:
        self.node_id = node_id
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

    def get_all_names(self) -> List[str]:
        names = list(self.entities.keys())

        if self.parent_scope:
            names.extend(self.parent_scope.get_all_names())

        return list(set(names))


class ModuleScope(Scope):
    def __init__(self, node_id: int, parent_scope: Optional[Scope] = None) -> None:
        super().__init__(node_id, parent_scope)

    def get_imports(self) -> List[CodeEntity]:
        imports = []

        for child_id in CHILDREN_MAP[self.node_id]:
            child = NODE_ID_MAP[child_id]
            if isinstance(child, ImportEntity):
                imports.append(child)

        return imports


class ClassScope(Scope):
    def __init__(self, node_id: int, parent_scope: Optional[Scope] = None) -> None:
        super().__init__(node_id, parent_scope)

    def define_method(self, entity: CodeEntity):
        self.define(entity)


class FuncScope(Scope):
    def __init__(self, node_id: int, parent_scope: Optional[Scope] = None) -> None:
        super().__init__(node_id, parent_scope)

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
    args = []
    for arg_node in args_node.args:
        arg_entity = ArgumentEntity(
            name=arg_node.arg,
            node_id=next_node_id(),
            line=arg_node.lineno,
            annotation=arg_node.annotation,
            default=None,
            is_keyword_only=False,
            is_positional_only=False,
        )
        args.append(arg_entity)

    return args


def _convert_decorators(decorator_list: List[ast.expr]) -> List[str]:
    decorators = []
    for dec in decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec)

    return decorators


def _convert_type_params(type_params_nodes: List[ast.type_param]) -> List[str]:
    result = []
    for node in type_params_nodes:
        if isinstance(node, ast.Name):
            result.append(node.id)
    return result


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
            args=_convert_args(node.args),
            decorators=_convert_decorators(node.decorator_list),
            type_params=_convert_type_params(node.type_params),
            returns=node.returns,
            is_method=is_method,
        )
    elif isinstance(node, ast.ClassDef):
        return ClassEntity(
            name=node.name,
            node_id=next_node_id(),
            line=node.lineno,
            bases=_convert_bases(node.bases),
            methods=[],
            decorators=_convert_decorators(node.decorator_list),
            keywords=_convert_keywords(node.keywords),
            type_params=_convert_type_params(node.type_params),
        )
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        return ImportEntity(
            name="import",
            node_id=next_node_id(),
            line=node.lineno,
            module_name="...",
            alias=_convert_import_aliases(node.names),
        )
    elif isinstance(node, ast.arg):
        return ArgumentEntity(
            name=node.arg,
            node_id=next_node_id(),
            line=node.lineno,
            annotation=None,
            default=None,
        )

    return None


def analyze_module(module_node: ast.Module, module_name: str):
    node_id = next_node_id()
    module_entity = ModuleEntity(name=module_name, line=0, node_id=node_id)
    module_scope = ModuleScope(node_id)

    NODE_ID_MAP[node_id] = module_entity
    SCOPE_MAP[node_id] = module_scope
    MODULE_MAP[node_id] = module_entity

    process_node(module_node, module_scope, parent_id=node_id)

    return module_entity, module_scope


def process_node(node: ast.AST, current_scope: Scope, parent_id: int):
    entity = wrap_ast_node(node, current_scope)
    if entity:
        node_id = entity.node_id
        NODE_ID_MAP[node_id] = entity
        PARENT_MAP[node_id] = parent_id
        CHILDREN_MAP.setdefault(parent_id, []).append(node_id)

        if isinstance(node, ast.FunctionDef):
            scope = FuncScope(node_id, parent_scope=current_scope)
        elif isinstance(node, ast.ClassDef):
            scope = ClassScope(node_id, parent_scope=current_scope)
        else:
            scope = current_scope

        SCOPE_MAP[node_id] = scope
        current_scope.define(entity)
    else:
        scope = current_scope
        node_id = parent_id

    for child in ast.iter_child_nodes(node):
        process_node(child, scope, parent_id=node_id)
