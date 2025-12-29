from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class RuleConfig:
    enabled: bool = True
    ignore: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LCOMConfig(RuleConfig):
    max_lcom: float = 0.8
    max_lcom_increased: float = 0.2
    min_cohesion_improvment: float = 0.0
    severity_lcom_increase: Severity = Severity.ERROR
    severity_high_lcom: Severity = Severity.WARNING


@dataclass(frozen=True)
class SideEffectConfig(RuleConfig):
    max_global_writes: int = 0
    max_arg_mutations: int = 2
    severity_global_write: Severity = Severity.ERROR
    severity_arg_mutation: Severity = Severity.WARNING


@dataclass(frozen=True)
class Config:
    fail_on_error: bool = True
    fail_on_warning: bool = False
    lcom: LCOMConfig = field(default_factory=LCOMConfig)
    sife_effects: SideEffectConfig = field(default_factory=SideEffectConfig)
