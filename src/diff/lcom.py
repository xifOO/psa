from typing import NamedTuple

from metrics.lcom import LCOM


class LCOMDiff(NamedTuple):
    lcom_value_delta: float
    method_count_delta: int
    attr_count_delta: int
    connected_components_delta: int
    stateless_method_count_delta: int
    avg_attrs_per_method_delta: float

    lcom_increased: bool
    cohesion_improved: bool


def diff_lcom(old: LCOM, new: LCOM) -> LCOMDiff:
    lcom_delta = new.lcom_value - old.lcom_value

    return LCOMDiff(
        lcom_value_delta=lcom_delta,
        method_count_delta=new.method_count - old.method_count,
        attr_count_delta=new.attr_count - old.attr_count,
        connected_components_delta=new.connected_components - old.connected_components,
        stateless_method_count_delta=new.stateless_method_count
        - old.stateless_method_count,
        avg_attrs_per_method_delta=new.avg_attrs_per_method - old.avg_attrs_per_method,
        lcom_increased=lcom_delta > 0,
        cohesion_improved=lcom_delta < 0,
    )
