"""Versioned, guard-driven state machines shared by every M02 lifecycle region.

The module spec models IRIS states on SCXML semantics (explicit transitions,
guards, orthogonal regions, fail-closed on unknown events) without adopting an
SCXML runtime. ``StateMachine`` is that contract in miniature: the legal
transition table is data, it is total over its state enum, and an unlisted edge
is refused rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from .base import Labeled
from .errors import LifecycleError

__all__ = ["StateMachine", "closure_reachable", "topological_order"]


@dataclass(frozen=True)
class StateMachine:
    """A total transition table over one ``Labeled`` enum."""

    name: str
    state_type: type
    transitions: Mapping[Labeled, Sequence[Labeled]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise LifecycleError("a state machine needs a name")
        if not (isinstance(self.state_type, type) and issubclass(self.state_type, Labeled)):
            raise LifecycleError(f"{self.name}: state_type must be a Labeled enum")
        members = {item for item in self.state_type}
        table: dict[Labeled, tuple[Labeled, ...]] = {}
        for source, targets in self.transitions.items():
            if source not in members:
                raise LifecycleError(f"{self.name}: unknown source state {source!r}")
            resolved = tuple(self.state_type.parse(target, f"{self.name}.targets") for target in targets)
            if len(set(resolved)) != len(resolved):
                raise LifecycleError(f"{self.name}: duplicate targets for {source.value}")
            if source in resolved:
                raise LifecycleError(f"{self.name}: {source.value} may not self-transition")
            table[source] = resolved
        for source in members:
            if source not in table:
                table[source] = ()
        object.__setattr__(self, "transitions", table)

    @property
    def states(self) -> tuple[Labeled, ...]:
        return tuple(self.state_type)

    @property
    def terminals(self) -> tuple[Labeled, ...]:
        return tuple(state for state, targets in self.transitions.items() if not targets)

    def is_terminal(self, state: Labeled) -> bool:
        return not self.legal_targets(state)

    def legal_targets(self, state: Labeled) -> tuple[Labeled, ...]:
        resolved = self.state_type.parse(state, f"{self.name}.state")
        return self.transitions[resolved]

    def is_legal(self, source: Labeled, target: Labeled) -> bool:
        resolved = self.state_type.parse(source, f"{self.name}.state")
        wanted = self.state_type.parse(target, f"{self.name}.state")
        return wanted in self.transitions[resolved]

    def require(self, source: Labeled, target: Labeled, *, reason: str = "") -> None:
        """Fail closed on an unlisted edge, naming the edges that were available."""

        if self.is_legal(source, target):
            return
        available = ", ".join(item.value for item in self.legal_targets(source)) or "none (terminal)"
        suffix = f"; reason given: {reason}" if reason else ""
        raise LifecycleError(
            f"{self.name}: {source.value} -> {target.value} is not a legal transition "
            f"(admitted from {source.value}: {available}){suffix}"
        )

    def reachable(self, start: Labeled) -> frozenset[Labeled]:
        resolved = self.state_type.parse(start, f"{self.name}.state")
        seen: set[Labeled] = {resolved}
        frontier: list[Labeled] = [resolved]
        while frontier:
            for target in self.transitions[frontier.pop()]:
                if target not in seen:
                    seen.add(target)
                    frontier.append(target)
        return frozenset(seen)


def closure_reachable(start: str, edges: Mapping[str, Iterable[str]]) -> frozenset[str]:
    """Transitive successors of ``start`` over an adjacency mapping, cycle-safe."""

    seen: set[str] = set()
    frontier = [start]
    while frontier:
        for target in edges.get(frontier.pop(), ()):
            if target not in seen:
                seen.add(target)
                frontier.append(target)
    return frozenset(seen)


def topological_order(nodes: Sequence[str], edges: Mapping[str, Iterable[str]]) -> tuple[str, ...]:
    """Order nodes so producers precede consumers; report the first cycle when stuck.

    ``edges`` maps a node to the nodes it depends on, which is the direction the
    graph kernel stores causality in.
    """

    unknown = {target for deps in edges.values() for target in deps if target not in set(nodes)}
    if unknown:
        raise LifecycleError(f"topological order references undeclared nodes: {sorted(unknown)[:8]}")
    remaining = {node: set(edges.get(node, ())) for node in nodes}
    ordered: list[str] = []
    while remaining:
        ready = sorted(node for node, deps in remaining.items() if not deps)
        if not ready:
            raise LifecycleError(
                f"cyclic dependency detected among nodes: {sorted(remaining)[:8]}"
            )
        for node in ready:
            remaining.pop(node)
        ordered.extend(ready)
        for deps in remaining.values():
            deps.difference_update(ready)
    return tuple(ordered)
