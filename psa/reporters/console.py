from typing import Any

from psa.diff.lcom import LCOMDiff
from psa.diff.side_effect import SideEffectDiff
from psa.reporters.base import BaseReporter


class ConsoleReporter(BaseReporter):
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self._handlers = {
            "lcom": self._report_lcom,
            "side_effect": self._report_side_effect,
        }

    def report(self, diff_type: str, diff: Any, context: dict[str, Any]) -> str:
        handler = self._handlers.get(diff_type)
        if handler:
            return handler(diff, context)
        else:
            return self._report_generic(diff_type, diff, context)

    def _report_lcom(self, diff: LCOMDiff, context: dict[str, Any]):
        class_name = context.get("class_name", "Unknown")
        lines = [f"\n LCOM: {class_name}"]

        if diff.cohesion_improved:
            lines.append(f"Cohesion improved by {abs(diff.lcom_value_delta):.3f}")
        elif diff.lcom_increased:
            lines.append(f"Cohesion decreased by {diff.lcom_value_delta:.3f}")

        if self.verbose:
            lines.append(f"  Methods: {diff.method_count_delta:+d}")
            lines.append(f"  Attributes: {diff.attr_count_delta:+d}")

        return "\n".join(lines)

    def _report_side_effect(self, diff: SideEffectDiff, context) -> str:
        func_name = context.get("function_name", "Unknown")
        lines = [f"\n Side Effects: {func_name}"]

        if diff.reads_added:
            lines.append(f"  +Reads: {', '.join(diff.reads_added)}")
        if diff.writes_added:
            lines.append(f"  +Writes: {', '.join(diff.writes_added)}")

        return "\n".join(lines)

    def _report_generic(self, diff_type: str, diff: Any, context: dict) -> str:
        return f"[{diff_type}] {diff}"

    def format_summary(self, results: list[tuple[str, Any, dict]]) -> str:
        lines = ["=" * 60, "ANALYSIS SUMMARY", "=" * 60]

        for diff_type, diff, context in results:
            lines.append(self.report(diff_type, diff, context))

        return "\n".join(lines)
