from typing import Any

from psa.config.rules import Config, Severity
from psa.rules.base import Rule, Violation, get_registered_rule


class RuleEngine:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.violations: list[Violation] = []
        self.rules: list[Rule] = [rule(config) for rule in get_registered_rule()]

    def checks(self, diffs: list[Any], context: dict[str, Any]) -> list[Violation]:
        self.violations.clear()

        for diff in diffs:
            for rule in self.rules:
                if rule.applies_to(diff):
                    self.violations.extend(rule.check(diff, context))

        return self.violations

    def _has_errors(self) -> bool:
        return any(v.severity == Severity.ERROR for v in self.violations)

    def _has_warnings(self) -> bool:
        return any(v.severity == Severity.WARNING for v in self.violations)

    def should_fail(self) -> bool:
        if self.config.fail_on_error and self._has_errors():
            return True

        if self.config.fail_on_warning and self._has_warnings():
            return True

        return False
