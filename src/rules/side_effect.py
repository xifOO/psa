from typing import Any
from config.rules import Config
from diff.side_effect import SideEffectDiff
from rules.base import Rule, Violation
from rules.registry import register_rule


@register_rule
class SideEffectRule(Rule):
    def __init__(self, config: Config):
        self.rules = config.sife_effects

    def applies_to(self, diff: Any) -> bool:
        return isinstance(diff, SideEffectDiff)

    def check(self, diff: SideEffectDiff, context: dict[str, Any]) -> list[Violation]:
        violations = []

        if not self.rules.enabled:
            return violations

        func_name = context.get("function_name", "Unknown")

        if len(diff.writes_added) > self.rules.max_global_writes:
            violations.append(Violation(
                rule_id="SE001",
                severity=self.rules.severity_global_write,
                message=f"Function {func_name} writes to global variables: {diff.writes_added}",
                context=context,
            ))

        if len(diff.arg_mutates_added) > self.rules.max_arg_mutations:
            violations.append(Violation(
                rule_id="SE002",
                severity=self.rules.severity_arg_mutation,
                message=f"Function {func_name} mutates {len(diff.arg_mutates_added)} arguments",
                context=context,
            ))

        return violations
