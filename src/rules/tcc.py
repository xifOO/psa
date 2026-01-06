from typing import Any
from config.rules import Config
from diff.tcc import TCCDiff
from rules.base import Rule, Violation


class TCCRule(Rule):
    def __init__(self, config: Config):
        self.rules = config.tcc

    def applies_to(self, diff: Any) -> bool:
        return isinstance(diff, TCCDiff)

    def check(self, diff: TCCDiff, context: dict[str, Any]) -> list[Violation]:
        violations = []

        if not self.rules.enabled:
            return violations

        class_name = context.get("class_name", "Unknown")

        if diff.tcc_increased and diff.tcc_value_delta > self.rules.max_tcc_increase:
            violations.append(
                Violation(
                    rule_id="TCC001",
                    severity=self.rules.severity_tcc_increase,
                    message=f"Cohesion decreased by {diff.tcc_value_delta:.3f} in {class_name}",
                    context=context,
                )
            )

        new_tcc = context.get("new_tcc_value", 0)
        if new_tcc > self.rules.max_tcc:
            violations.append(
                Violation(
                    rule_id="TCC002",
                    severity=self.rules.severity_high_tcc,
                    message=f"TCC value {new_tcc:.3f} exceeds threshold {self.rules.max_tcc} in {class_name}",
                    context=context,
                )
            )

        return violations
