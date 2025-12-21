from typing import NamedTuple

from analysis.side_effect import SideEffect


class SideEffectDiff(NamedTuple):
    reads_added: frozenset[str]
    reads_removed: frozenset[str]
    writes_added: frozenset[str]
    writes_removed: frozenset[str]
    arg_mutates_added: frozenset[tuple[str, str]]
    arg_mutates_removed: frozenset[tuple[str, str]]
    attr_mutates_added: frozenset[tuple[str, str]]
    attr_mutates_removed: frozenset[tuple[str, str]]


def diff_side_effect(old: SideEffect, new: SideEffect) -> SideEffectDiff:
    return SideEffectDiff(
        reads_added=new.reads - old.reads,
        reads_removed=old.reads - new.reads,
        writes_added=new.writes - old.writes,
        writes_removed=old.writes - new.writes,
        arg_mutates_added=new.arg_mutates - old.arg_mutates,
        arg_mutates_removed=old.arg_mutates - new.arg_mutates,
        attr_mutates_added=new.attr_mutates - old.attr_mutates,
        attr_mutates_removed=old.attr_mutates - new.attr_mutates,
    )
