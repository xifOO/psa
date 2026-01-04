from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Type, TypeVar, Union

import yaml


T = TypeVar("T")


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
    max_lcom_increase: float = 0.2
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
class TCCConfig(RuleConfig):
    max_tcc: float = 0.85
    max_tcc_increase: float = 0.15
    min_cohesion_improvment: float = 0.0
    severity_tcc_increase: Severity = Severity.ERROR
    severity_high_tcc: Severity = Severity.WARNING


def from_dict(cls: Type[T], data: dict, nested: dict = None) -> T:
    field_names = {f.name for f in fields(cls)}
    filtered_data = {}

    for name in field_names:
        if nested and name in nested:
            value = nested[name]
        elif name in data:
            value = data[name]
        else:
            continue

        f_type = next(f.type for f in fields(cls) if f.name == name)
        if isinstance(f_type, type) and issubclass(f_type, Enum):
            value = f_type(value)

        filtered_data[name] = value

    return cls(**filtered_data)


@dataclass(frozen=True)
class Config:
    fail_on_error: bool = True
    fail_on_warning: bool = False
    lcom: LCOMConfig = field(default_factory=LCOMConfig)
    sife_effects: SideEffectConfig = field(default_factory=SideEffectConfig)
    tcc: TCCConfig = field(default_factory=TCCConfig)

    @classmethod
    def from_yaml(cls, filepath: Union[str, Path]) -> "Config":
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        settings = data.get("settings", {})

        lcom_data = data.get("lcom", {})
        lcom_thresholds = lcom_data.get("thresholds", {})
        lcom_severity = lcom_data.get("severity", {})
        lcom_rules = from_dict(
            LCOMConfig, lcom_data, nested={**lcom_thresholds, **lcom_severity}
        )

        se_data = data.get("side_effect", {})
        se_thresholds = se_data.get("thresholds", {})
        se_severity = se_thresholds.get("severity", {})
        se_rules = from_dict(
            SideEffectConfig, se_data, nested={**se_thresholds, **se_severity}
        )

        tcc_data = data.get("tcc", {})
        tcc_thresholds = tcc_data.get("thresholds", {})
        tcc_severity = tcc_data.get("severity", {})
        tcc_rules = from_dict(
            TCCConfig, tcc_data, nested={**tcc_thresholds, **tcc_severity}
        )

        return cls(
            fail_on_error=settings.get("fail_on_error", True),
            fail_on_warning=settings.get("fail_on_warning", False),
            lcom=lcom_rules,
            sife_effects=se_rules,
            tcc=tcc_rules,
        )
