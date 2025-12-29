from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Union

import yaml


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

    @classmethod
    def from_yaml(cls, filepath: Union[str, Path]) -> "Config":
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        settings = data.get("settings", {})
        
        lcom_data = data.get("lcom", {})
        lcom_thresholds = lcom_data.get("thresholds", {})
        lcom_severity = lcom_data.get("severity", {})
        
        lcom_rules = LCOMConfig(
            enabled=lcom_data.get("enabled", True),
            max_lcom=lcom_thresholds.get("max_lcom", 0.8),
            max_lcom_increased=lcom_thresholds.get("max_lcom_increase", 0.2),
            severity_lcom_increase=Severity(lcom_severity.get("lcom_increase", "error")),
            severity_high_lcom=Severity(lcom_severity.get("high_lcom", "warning")),
            ignore=lcom_data.get("ignore", [])
        )

        se_data = data.get("side_effect", {})
        se_thresholds = se_data.get("thresholds", {})
        se_severity = se_thresholds.get("severity", {}) 

        se_rules = SideEffectConfig(
            enabled=se_data.get("enabled", True),
            max_global_writes=se_thresholds.get("max_global_writes", 0),
            max_arg_mutations=se_thresholds.get("max_arg_mutations", 2),
            severity_global_write=Severity(se_severity.get("global_write", "error")),
            severity_arg_mutation=Severity(se_severity.get("arg_mutation", "warning")),
            ignore=se_data.get("ignore", [])
        )

        return cls(
            fail_on_error=settings.get("fail_on_error", True),
            fail_on_warning=settings.get("fail_on_warning", False),
            lcom=lcom_rules,
            sife_effects=se_rules
        )