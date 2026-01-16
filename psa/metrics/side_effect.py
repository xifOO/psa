from typing import NamedTuple

from psa.entity import CodeEntity, FunctionEntity
from psa.index.maps import Index
from psa.metrics.base import Analyzer
from psa.metrics.funcs import analyze_func


class SideEffect(NamedTuple):
    reads: frozenset[str]
    writes: frozenset[str]
    arg_mutates: frozenset[tuple[str, str]]
    attr_mutates: frozenset[tuple[str, str]]


class SideEffectAnalyzer(Analyzer):
    def applies_to(self, entity: CodeEntity) -> bool:
        return isinstance(entity, FunctionEntity)

    def analyze(self, index: Index, entity: FunctionEntity) -> tuple[SideEffect, dict]:
        metrics = analyze_func(index, entity)

        side_effect = SideEffect(
            reads=metrics.attrs_read,
            writes=metrics.attrs_written
            | metrics.globals_written
            | metrics.nonlocals_written,
            arg_mutates=metrics.arg_mutates,
            attr_mutates=metrics.attr_mutates,
        )

        context = {
            "function_name": entity.name,
            "line_number": entity.line,
            "args": metrics.args,
            "local_vars": metrics.local_vars,
            "calls": metrics.calls,
        }

        return side_effect, context
