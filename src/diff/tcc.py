from typing import NamedTuple

from analysis.tcc import TCC


class TCCDiff(NamedTuple):
    tcc_value_delta: float
    method_count_delta: int
    attr_count_delta: int
    directly_connected_pairs_delta: int
    total_method_pairs_delta: int
    stateless_method_count_delta: int

    tcc_increased: bool
    cohesion_improved: bool


def diff_tcc(old: TCC, new: TCC) -> TCCDiff:
    tcc_delta = new.tcc_value - old.tcc_value
    stateless_delta = old.stateless_method_count - new.stateless_method_count

    cohesion_improved = (tcc_delta > 0) or (stateless_delta > 0)

    return TCCDiff(
        tcc_value_delta=tcc_delta,
        method_count_delta=new.method_count - old.method_count,
        attr_count_delta=new.attr_count - old.attr_count,
        directly_connected_pairs_delta=new.directly_connected_pairs
        - old.directly_connected_pairs,
        total_method_pairs_delta=new.total_method_pairs - old.total_method_pairs,
        stateless_method_count_delta=new.stateless_method_count
        - old.stateless_method_count,
        tcc_increased=tcc_delta > 0,
        cohesion_improved=cohesion_improved,
    )
