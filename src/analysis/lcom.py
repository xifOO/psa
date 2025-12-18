from typing import NamedTuple


class LCOM(NamedTuple):
    lcom_value: float
    method_count: int
    attr_count: int
    shared_attrs: int

