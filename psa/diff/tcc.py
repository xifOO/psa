from typing import NamedTuple, Optional, Self

from psa.metrics.tcc import TCC


class TCCDiff(NamedTuple):
    tcc_value_delta: float
    method_count_delta: int
    attr_count_delta: int
    directly_connected_pairs_delta: int
    total_method_pairs_delta: int
    stateless_method_count_delta: int

    tcc_increased: bool
    cohesion_improved: bool

    @classmethod
    def from_metrics(cls, old: Optional[TCC], new: TCC) -> Self:
        if old is None:
            tcc_delta = 0.0
            stateless_delta = 0
            cohesion_improved = False
            return cls(
                tcc_value_delta=tcc_delta,
                method_count_delta=0,
                attr_count_delta=0,
                directly_connected_pairs_delta=0,
                total_method_pairs_delta=0,
                stateless_method_count_delta=0,
                tcc_increased=False,
                cohesion_improved=cohesion_improved,
            )

        tcc_delta = new.tcc_value - old.tcc_value
        stateless_delta = old.stateless_method_count - new.stateless_method_count
        cohesion_improved = (tcc_delta > 0) or (stateless_delta > 0)

        return cls(
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
