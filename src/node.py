import ast
from dataclasses import dataclass
from typing import Any, Final, List, Optional, Set, Tuple
from index.maps import Index
from index.scopes import ClassScope, FuncScope, ModuleScope, Scope
from entity import CallEntity, CodeEntity, ModuleEntity
from utils import wrap_ast_node


class ASTVisitor(ast.NodeVisitor):
    def __init__(self, index: Index) -> None:
        self.index = index

        self.scope_stack: List[Scope] = []
        self.parent_stack: List[int] = []

    def build_module(self, node: ast.Module, name: str) -> ModuleScope:
        module_id = self.index.next_node_id()

        module_entity = ModuleEntity(
            name=name, line=0, node_id=module_id, ast_node=node
        )

        module_scope = ModuleScope(node_id=module_id, name=name, index=self.index)

        self.index.node_map.add(module_entity)
        self.index.scope_map.add(module_scope)

        self.scope_stack.append(module_scope)
        self.parent_stack.append(module_id)

        self.visit(node)

        self.scope_stack.pop()
        self.parent_stack.pop()

        return module_scope

    def _register_entity(self, node: ast.AST) -> Optional[CodeEntity]:
        entity = wrap_ast_node(node, self.scope_stack[-1])
        if not entity:
            return None

        self.index.node_map.add(entity)
        self.index.children_map.link(self.parent_stack[-1], entity.node_id)

        self.scope_stack[-1].define(entity)

        return entity

    def visit_Module(self, node: ast.Module) -> None:
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        entity = self._register_entity(node)
        if not entity:
            return

        func_scope = FuncScope(
            node_id=entity.node_id,
            name=entity.name,
            index=self.index,
            parent_scope=self.scope_stack[-1],
        )

        self.index.scope_map.add(func_scope)

        self.scope_stack.append(func_scope)
        self.parent_stack.append(entity.node_id)

        self.generic_visit(node)

        self.parent_stack.pop()
        self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        entity = self._register_entity(node)
        if not entity:
            return

        class_scope = ClassScope(
            node_id=entity.node_id,
            name=entity.name,
            index=self.index,
            parent_scope=self.scope_stack[-1],
        )

        self.index.scope_map.add(class_scope)

        self.scope_stack.append(class_scope)
        self.parent_stack.append(entity.node_id)

        self.generic_visit(node)

        self.parent_stack.pop()
        self.scope_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        self._register_entity(node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self._register_entity(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        self._register_entity(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self._register_entity(node)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        self._register_entity(node)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        self._register_entity(node)

    def visit_arg(self, node: ast.arg):
        self._register_entity(node)


@dataclass
class ExprInfo:
    reads: set[str]
    calls: List[Tuple]
    attrs: List[str]
    const: List[Any]


class ExprVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.reads: Set[str] = set()
        self.calls: List[Tuple] = []
        self.attrs: List[str] = []
        self.const: List = []

    def visit_Call(self, node: ast.Call) -> None:
        name = None
        receiver = None

        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                receiver = node.func.value.id
                name = node.func.attr

        if name:
            self.calls.append((name, receiver))

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.reads.add(node.id)

    def visit_Constant(self, node: ast.Constant) -> None:
        self.const.append(node.value)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            self.attrs.append(f"{node.value.id}.{node.attr}")
        self.generic_visit(node)

    @classmethod
    def analyze(cls, node: ast.AST) -> ExprInfo:
        v = cls()
        v.visit(node)

        return ExprInfo(
            reads=v.reads,
            calls=v.calls,
            attrs=v.attrs,
            const=v.const,
        )


class ExprEffectsVisitor(ast.NodeVisitor):
    def __init__(
        self, *, args: Set[str], globals: Set[str], nonlocals: Set[str]
    ) -> None:
        self.args = args
        self.globals = globals
        self.nonlocals = nonlocals

        self.attrs_read: Set[str] = set()
        self.attrs_written: Set[str] = set()
        self.attr_mutates: Set[tuple[str, str]] = set()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            obj = node.value.id
            attr = node.attr
            if isinstance(node.ctx, ast.Load):
                if obj in self.args | self.globals | self.nonlocals:
                    self.attr_mutates.add((obj, attr))
                else:
                    self.attrs_read.add(f"{obj}.{attr}")
        self.generic_visit(node)


class AssignVisitor(ast.NodeVisitor):
    def __init__(
        self, *, args: Set[str], globals: Set[str], nonlocals: Set[str]
    ) -> None:
        self.args = args
        self.globals = globals
        self.nonlocals = nonlocals

        self.attrs_written: Set[str] = set()
        self.attr_mutates: Set[tuple[str, str]] = set()
        self.locals_written: Set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._handle_target(target)
        self.generic_visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._handle_target(node.target)
        if node.value:
            self.generic_visit(node.value)

    def _handle_target(self, target: ast.AST):
        match target:
            case ast.Name(id=name):
                self._handle_name(name)
            case ast.Attribute(value=ast.Name(id=obj), attr=attr):
                self._handle_attr(obj, attr)
            case ast.Subscript(value=ast.Name(id=obj)):
                self._handle_subscript(obj)
            case ast.Tuple(elts=elts) | ast.List(elts=elts):
                for elt in elts:
                    self._handle_target(elt)

            case _:
                pass

    def _handle_name(self, name: str) -> None:
        if name not in self.globals and name not in self.nonlocals:
            self.locals_written.add(name)

    def _handle_attr(self, obj: str, attr: str) -> None:
        if obj in self.args | self.globals | self.nonlocals:
            self.attr_mutates.add((obj, attr))
        else:
            self.attrs_written.add(f"{obj}.{attr}")

    def _handle_subscript(self, obj: str):
        if obj in self.args | self.globals | self.nonlocals:
            self.attr_mutates.add((obj, "__setitem__"))
        else:
            self.attrs_written.add(f"{obj}.__setitem__")


class SelfAttrVisitor(ast.NodeVisitor):
    def __init__(self, property_to_attr: dict[str, str]) -> None:
        self.property_to_attr = property_to_attr
        self.attrs_used: Set[str] = set()
        self.attrs_read: Set[str] = set()
        self.attrs_written: Set[str] = set()
        self.instance_attrs: Set[str] = set()

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if not isinstance(node.slice, ast.Constant):
            self.generic_visit(node)
            return

        attr_name = str(node.slice.value)

        if isinstance(node.ctx, ast.Store):
            state = "write"
        elif isinstance(node.ctx, ast.Load):
            state = "read"
        else:
            self.generic_visit(node)
            return

        if isinstance(node.value, ast.Attribute):
            if (
                isinstance(node.value.value, ast.Name)
                and node.value.value.id == "self"
                and node.value.attr == "__dict__"
            ):
                self.attrs_used.add(attr_name)
                if state == "write":
                    self.attrs_written.add(attr_name)
                elif state == "read":
                    self.attrs_read.add(attr_name)

        elif isinstance(node.value, ast.Call):
            if (
                isinstance(node.value.func, ast.Name)
                and node.value.func.id == "vars"
                and len(node.value.args) >= 1
                and isinstance(node.value.args[0], ast.Name)
                and node.value.args[0].id == "self"
            ):
                self.attrs_used.add(attr_name)
                if state == "write":
                    self.attrs_written.add(attr_name)
                elif state == "read":
                    self.attrs_read.add(attr_name)

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            attr = node.attr

            resolved = self.property_to_attr.get(attr, attr)

            self.attrs_used.add(resolved)

            if isinstance(node.ctx, ast.Store):
                self.attrs_written.add(resolved)
                self.instance_attrs.add(resolved)

            elif isinstance(node.ctx, ast.Load):
                self.attrs_read.add(resolved)

        self.generic_visit(node)


class DynamicAttrVisitor(ast.NodeVisitor):
    ATTR_FUNCS: Final = {"setattr": "write", "delattr": "write", "getattr": "read"}

    def __init__(self) -> None:
        self.attrs_read: Set[str] = set()
        self.attrs_written: Set[str] = set()
        self.attrs_used: Set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in self.ATTR_FUNCS:
            if (
                len(node.args) >= 2
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "self"
            ):
                if isinstance(node.args[1], ast.Constant):
                    attr_name = str(node.args[1].value)
                    action = self.ATTR_FUNCS[node.func.id]

                    self.attrs_used.add(attr_name)

                    if action == "write":
                        self.attrs_written.add(attr_name)
                    else:
                        self.attrs_read.add(attr_name)

        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Call):
                call = node.func.value
                if (
                    isinstance(call.func, ast.Name)
                    and call.func.id == "vars"
                    and len(call.args) >= 1
                    and isinstance(call.args[0], ast.Name)
                    and call.args[0].id == "self"
                    and node.func.attr == "get"
                    and len(node.args) >= 1
                    and isinstance(node.args[0], ast.Constant)
                ):
                    attr_name = str(node.args[0].value)
                    self.attrs_used.add(attr_name)
                    self.attrs_read.add(attr_name)

        self.generic_visit(node)


class PropertyVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.property_to_attr: dict[str, str] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        is_property = any(
            (isinstance(dec, ast.Name) and dec.id == "property")
            for dec in node.decorator_list
        )

        if not is_property:
            self.generic_visit(node)
            return

        for stmt in node.body:
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Attribute):
                if (
                    isinstance(stmt.value.value, ast.Name)
                    and stmt.value.value.id == "self"
                ):
                    self.property_to_attr[node.name] = stmt.value.attr
                    break

        self.generic_visit(node)


class CallVisitor(ast.NodeVisitor):
    def __init__(self, index: Index, scope: Scope) -> None:
        self.index = index
        self.scope = scope

    def visit_Call(self, node: ast.Call) -> None:
        func_name = ""
        receiver = None
        is_method_call = False

        if isinstance(node.func, ast.Name):
            func_name = node.func.id

        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                receiver = node.func.value.id
                func_name = node.func.attr
                is_method_call = True

        args = [ExprVisitor.analyze(arg) for arg in node.args]

        kws = {kw.arg: ExprVisitor.analyze(kw.value) for kw in node.keywords if kw.arg}

        call_entity = CallEntity(
            node_id=self.index.next_node_id(),
            name=func_name,
            line=node.lineno,
            ast_node=node,
            args=args,
            keywords=kws,
            is_method_call=is_method_call,
            receiver=receiver,
            scope=self.scope,
        )

        self.index.call_map.add(call_entity)
        self.index.children_map.link(self.scope.node_id, call_entity.node_id)

        self.generic_visit(node)
