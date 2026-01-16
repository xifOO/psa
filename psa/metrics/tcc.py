from typing import NamedTuple

from psa.index.maps import Index
from psa.metrics.classes import ClassMetrics, analyze_class, get_methods
from psa.metrics.base import Analyzer
from psa.entity import ClassEntity, CodeEntity


class TCC(NamedTuple):
    tcc_value: float

    method_count: int
    attr_count: int

    directly_connected_pairs: int
    total_method_pairs: int

    stateless_method_count: int


def _calculate_connected_pairs(usage: dict[str, frozenset[str]]) -> int:
    directly_connected_pairs = 0
    methods = list(usage.keys())
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            m1 = methods[i]
            m2 = methods[j]

            if usage[m1] & usage[m2]:
                directly_connected_pairs += 1

    return directly_connected_pairs


def _calculate_tcc(metrics: ClassMetrics) -> TCC:
    methods = get_methods(metrics)

    usage = {
        method: attrs
        for method, attrs in metrics.method_attr_usage.items()
        if method in methods
    }

    method_count = len(usage)
    attr_count = len(metrics.instance_attrs)

    if method_count < 2:
        return TCC(
            tcc_value=0.0,
            method_count=method_count,
            attr_count=attr_count,
            directly_connected_pairs=0,
            total_method_pairs=0,
            stateless_method_count=0,
        )

    stateless_method_count = sum(1 for attrs in usage.values() if len(attrs) == 0)
    total_method_pairs = method_count * (method_count - 1) // 2

    directly_connected_pairs = _calculate_connected_pairs(usage)

    tcc_value = (
        directly_connected_pairs / total_method_pairs if total_method_pairs > 0 else 0.0
    )

    return TCC(
        tcc_value=tcc_value,
        method_count=method_count,
        attr_count=attr_count,
        directly_connected_pairs=directly_connected_pairs,
        total_method_pairs=total_method_pairs,
        stateless_method_count=stateless_method_count,
    )


class TCCAnalyzer(Analyzer):
    def applies_to(self, entity: CodeEntity) -> bool:
        return isinstance(entity, ClassEntity)

    def analyze(self, index: Index, entity: ClassEntity) -> tuple[TCC, dict]:
        metrics = analyze_class(index, entity)
        tcc = _calculate_tcc(metrics)

        context = {
            "class_name": entity.name,
            "line_number": entity.line,
        }

        return tcc, context
