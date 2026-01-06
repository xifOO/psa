from typing import Any
from config.rules import Config
from diff.lcom import LCOMDiff
from rules.base import Rule, Violation


class LCOMRule(Rule):
    def __init__(self, config: Config):
        self.rules = config.lcom

    def applies_to(self, diff: Any) -> bool:
        return isinstance(diff, LCOMDiff)

    def check(self, diff: LCOMDiff, context: dict[str, Any]) -> list[Violation]:
        violations = []

        if not self.rules.enabled:
            return violations

        class_name = context.get("class_name", "Unknown")

        if diff.lcom_increased and diff.lcom_value_delta > self.rules.max_lcom_increase:
            violations.append(
                Violation(
                    rule_id="LCOM001",
                    severity=self.rules.severity_lcom_increase,
                    message=f"Cohesion decreased by {diff.lcom_value_delta:.3f} in {class_name}",
                    context=context,
                )
            )

        new_lcom = context.get("new_lcom_value", 0)
        if new_lcom > self.rules.max_lcom:
            violations.append(
                Violation(
                    rule_id="LCOM002",
                    severity=self.rules.severity_high_lcom,
                    message=f"LCOM value {new_lcom:.3f} exceeds threshold {self.rules.max_lcom} in {class_name}",
                    context=context,
                )
            )

        return violations
