"""M02 area C (branching): branch refs, typed variants, retention pins, anchors.

Four concepts stay separate here because collapsing them is the classic way a
version control system rots: a *branch* is a mutable ref, a *snapshot* is an
immutable closure (``snapshots.py``), a *variant* is a switchable alternative
inside one semantic identity, and a *rollback* is new history pointing at old
state. An outfit is a variant; a competing creative direction is a branch.

Variant sets are typed and constrained so an illegal combination fails while it
is still a selection, before any expensive render. Protected identity anchors are
an explicit policy on a variant set: drifting a spokesperson's face through an
"outfit switch" is refused, because an option that moves the anchor has to name
the identity migration that authorises it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from .base import Labeled, Record, of
from .errors import GraphValidationError, IdentityError, SchemaValidationError
from .graph import DependencyFacet
from .identity import (
    AliasLedger,
    AliasRef,
    EntityKind,
    ExternalRef,
    TransitionReceipt,
    new_id,
    require_id,
)
from .limits import (
    MAX_ALIASES,
    MAX_METADATA_KEYS,
    MAX_PIN_REASONS,
    MAX_VARIANT_OPTIONS,
    MAX_VARIANT_SELECTIONS,
    MAX_VARIANT_SETS,
)
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    content_digest,
    require_bounded,
    require_digest,
    require_identifier,
    require_metadata,
    require_component_version,
    require_optional_text,
    require_millis,
    require_supported_version,
    require_text,
)

__all__ = [
    "BranchProfile",
    "BranchState",
    "PinReason",
    "ConstraintKind",
    "IdentityAnchorPolicy",
    "VariantOption",
    "VariantSet",
    "VariantConstraint",
    "VariantSelection",
    "ExperimentPlan",
    "RetentionPin",
    "Branch",
    "BranchRef",
    "ForkReceipt",
    "BranchLedger",
    "resolve_selection",
    "validate_selection",
    "anchor_violations",
    "anchor_rulings",
    "selection_rulings",
]


def _refs(value: Iterable[Any], field: str, *, maximum: int) -> tuple[ExternalRef, ...]:
    collected = tuple(value)
    if len(collected) > maximum:
        raise GraphValidationError(f"{field} exceeds the admitted {maximum} entries")
    unique = {ExternalRef.coerce(item, f"{field}[]") for item in collected}
    return tuple(sorted(unique, key=lambda item: item.text))


def _identifiers(values: Any, field: str) -> tuple[str, ...]:
    collected = require_bounded(values, field, maximum=MAX_VARIANT_OPTIONS, kind="identifier")
    return tuple(require_identifier(item, f"{field}[]") for item in collected)


class BranchProfile(Labeled):
    """Policy profiles over one branch mechanism, never five branch systems."""

    CANONICAL = "CANONICAL"
    EXPERIMENT = "EXPERIMENT"
    CAMPAIGN = "CAMPAIGN"
    EPISODE_SHOT = "EPISODE_SHOT"
    RELEASE = "RELEASE"

    @property
    def is_bounded(self) -> bool:
        """An experiment must carry a budget and a retention deadline."""

        return self is BranchProfile.EXPERIMENT

    @property
    def may_hold_release(self) -> bool:
        return self in {BranchProfile.RELEASE, BranchProfile.CANONICAL}


class BranchState(Labeled):
    """Where a branch ref stands. History never moves; only the ref does."""

    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    ABANDONED = "ABANDONED"
    ARCHIVED = "ARCHIVED"

    @property
    def accepts_advance(self) -> bool:
        return self is BranchState.ACTIVE


class ConstraintKind(Labeled):
    """Compatibility rules kept apart from the variant values they constrain."""

    REQUIRES = "REQUIRES"
    PROHIBITS = "PROHIBITS"


class PinReason(Labeled):
    """Why something is retained. Cleanup may only discard what is neither pinned nor reachable."""

    GOLDEN = "GOLDEN"
    BENCHMARK = "BENCHMARK"
    RIGHTS = "RIGHTS"
    AUDIT = "AUDIT"
    RELEASE = "RELEASE"
    RETENTION_TTL = "RETENTION_TTL"
    OPEN_EXPERIMENT = "OPEN_EXPERIMENT"


@dataclass(frozen=True)
class IdentityAnchorPolicy(Record):
    """A protected identity that ordinary variants may not move.

    The guard is a digest comparison plus an explicit migration receipt: an option
    that keeps the anchor carries the baseline digest, and anything else has to be
    covered by the identity migration that authorises the change.
    """

    anchor_id: str
    policy_ref: ExternalRef
    baseline_digest: str
    baseline_option_id: Any = None
    description: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {"policy_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchor_id", require_identifier(self.anchor_id, "anchor_id"))
        object.__setattr__(self, "baseline_digest", require_digest(self.baseline_digest, "baseline_digest"))
        if self.baseline_option_id is not None:
            object.__setattr__(
                self, "baseline_option_id", require_identifier(self.baseline_option_id, "baseline_option_id")
            )
        if not isinstance(self.policy_ref, ExternalRef):
            raise SchemaValidationError("policy_ref must be an ExternalRef naming the anchor policy")
        object.__setattr__(self, "description", require_optional_text(self.description, "description", maximum=512))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def drifts(self, candidate_digest: Any) -> bool:
        return candidate_digest is not None and candidate_digest != self.baseline_digest

    def authorize(self, candidate_digest: Any, migration_receipt_ids: Sequence[str]) -> bool:
        if not self.drifts(candidate_digest):
            return True
        return any(require_id(item, "migration_receipt_id") for item in migration_receipt_ids)


@dataclass(frozen=True)
class VariantOption(Record):
    """One switchable alternative inside a single semantic identity."""

    option_id: str
    content_digest: str
    anchor_digest: Any = None
    migration_receipt_id: Any = None
    intent_ref: Any = None
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {"intent_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "option_id", require_identifier(self.option_id, "option_id"))
        object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))
        if self.anchor_digest is not None:
            object.__setattr__(self, "anchor_digest", require_digest(self.anchor_digest, "anchor_digest"))
        if self.migration_receipt_id is not None:
            object.__setattr__(
                self, "migration_receipt_id", require_id(self.migration_receipt_id, "migration_receipt_id")
            )
        if self.intent_ref is not None and not isinstance(self.intent_ref, ExternalRef):
            raise SchemaValidationError("intent_ref must be an ExternalRef or None")
        object.__setattr__(
            self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS)
        )

    @property
    def text(self) -> str:
        return f"{self.option_id}={self.content_digest}"


@dataclass(frozen=True)
class VariantSet(Record):
    """A typed axis of alternatives: options, defaults, cost, and anchor protection."""

    variant_set_id: str
    purpose: str
    options: tuple[VariantOption, ...]
    default_option_id: Any = None
    allow_unselected: bool = False
    affected_facets: tuple[DependencyFacet, ...] = (DependencyFacet.CONTENT,)
    affected_ports: tuple[str, ...] = ()
    requires_rebuild: bool = True
    requires_revalidation: bool = True
    identity_anchor: Any = None
    metadata: tuple[tuple[str, Any], ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "options": of(VariantOption),
        "identity_anchor": of(IdentityAnchorPolicy),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "variant_set_id", require_identifier(self.variant_set_id, "variant_set_id"))
        object.__setattr__(self, "purpose", require_text(self.purpose, "purpose", maximum=512))
        collected = _options(self.options)
        ids = [item.option_id for item in collected]
        clash = sorted({item for item in ids if ids.count(item) > 1})
        if clash:
            raise GraphValidationError(f"variant set {self.variant_set_id} declares duplicate options: {clash}")
        object.__setattr__(self, "options", tuple(sorted(collected, key=lambda item: item.option_id)))
        if self.default_option_id is not None:
            default = require_identifier(self.default_option_id, "default_option_id")
            if default not in ids:
                raise GraphValidationError(
                    f"variant set {self.variant_set_id} defaults to {default!r}, which is not one of its options"
                )
            object.__setattr__(self, "default_option_id", default)
        facets = tuple(
            sorted(
                {DependencyFacet.parse(item, "affected_facets[]") for item in self.affected_facets},
                key=lambda item: item.value,
            )
        )
        if not facets:
            raise GraphValidationError("a variant set must declare the facets it affects")
        object.__setattr__(self, "affected_facets", facets)
        object.__setattr__(self, "affected_ports", tuple(sorted(set(_identifiers(self.affected_ports, "affected_ports")))))
        if self.identity_anchor is not None and not isinstance(self.identity_anchor, IdentityAnchorPolicy):
            raise SchemaValidationError("identity_anchor must be an IdentityAnchorPolicy or None")
        object.__setattr__(
            self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS)
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})
        self._validate_anchor()

    def _validate_anchor(self) -> None:
        anchor = self.identity_anchor
        if anchor is None:
            return
        unchecked = sorted(item.option_id for item in self.options if item.anchor_digest is None)
        if unchecked:
            raise IdentityError(
                f"variant set {self.variant_set_id} is anchor-protected but options {unchecked} declare no "
                "anchor_digest: a protected axis cannot carry an alternative nobody checked"
            )
        drifted = sorted(item.option_id for item in self.options if anchor.drifts(item.anchor_digest))
        if drifted and anchor.baseline_option_id is None:
            raise IdentityError(
                f"variant set {self.variant_set_id} offers {drifted}, which move the anchor, so the policy "
                "must name the baseline option that preserves it"
            )
        unprotected = sorted(
            item.option_id
            for item in self.options
            if anchor.drifts(item.anchor_digest) and item.migration_receipt_id is None
        )
        if unprotected:
            raise IdentityError(
                f"anchor options {unprotected} move {anchor.anchor_id} without naming the identity "
                "migration that authorises the change"
            )

    def option(self, option_id: str) -> VariantOption:
        wanted = require_identifier(option_id, "option_id")
        for item in self.options:
            if item.option_id == wanted:
                return item
        raise GraphValidationError(
            f"variant set {self.variant_set_id} has no option {wanted!r}: it offers "
            f"{[item.option_id for item in self.options]}"
        )

    @property
    def option_ids(self) -> tuple[str, ...]:
        return tuple(item.option_id for item in self.options)


def _options(values: Any) -> list[VariantOption]:
    collected = require_bounded(values, "options", maximum=MAX_VARIANT_OPTIONS)
    resolved = [VariantOption.coerce(item, "options[]") for item in collected]
    if not resolved:
        raise GraphValidationError("a variant set with no options switches nothing")
    return resolved


@dataclass(frozen=True)
class VariantConstraint(Record):
    """One compatibility rule between variant axes, checked before any execution."""

    constraint_id: str
    kind: ConstraintKind
    when_set: str
    when_option: str
    target_set: str
    target_options: tuple[str, ...]
    reason_code: str = "compatibility"
    enforcement_note: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraint_id", require_identifier(self.constraint_id, "constraint_id"))
        object.__setattr__(self, "kind", ConstraintKind.parse(self.kind, "kind"))
        for name in ("when_set", "when_option", "target_set"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        collected = _identifiers(self.target_options, "target_options")
        if not collected:
            raise GraphValidationError(
                f"constraint {self.constraint_id} names no target options, so it would forbid everything"
            )
        object.__setattr__(self, "target_options", tuple(sorted(set(collected))))
        object.__setattr__(self, "reason_code", require_identifier(self.reason_code, "reason_code"))
        object.__setattr__(
            self,
            "enforcement_note",
            require_optional_text(self.enforcement_note, "enforcement_note", maximum=512),
        )

    def violation(self, selection: Mapping[str, str]) -> str | None:
        """Describe why this constraint is unsatisfied, or ``None`` when it holds."""

        if selection.get(self.when_set) != self.when_option:
            return None
        chosen = selection.get(self.target_set)
        if self.kind is ConstraintKind.REQUIRES:
            if chosen is None:
                return (
                    f"{self.when_set}={self.when_option} requires {self.target_set} to be selected from "
                    f"{list(self.target_options)}"
                )
            if chosen not in self.target_options:
                return (
                    f"{self.when_set}={self.when_option} requires {self.target_set} to be one of "
                    f"{list(self.target_options)}, not {chosen}"
                )
            return None
        if chosen is not None and chosen in self.target_options:
            return f"{self.when_set}={self.when_option} prohibits {self.target_set}={chosen}"
        return None


@dataclass(frozen=True)
class VariantSelection(Record):
    """A chosen option per variant set. Selecting never edits the set itself."""

    selection_id: str
    pairs: tuple[tuple[str, str], ...] = ()
    migration_receipt_ids: tuple[str, ...] = ()
    actor: Any = None
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {"actor": of(ComponentVersion)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "selection_id", require_id(self.selection_id, "selection_id"))
        collected = require_bounded(self.pairs, "pairs", maximum=MAX_VARIANT_SELECTIONS, kind="selection")
        frozen: list[tuple[str, str]] = []
        for item in collected:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise SchemaValidationError("pairs must be (variant_set_id, option_id) two-item sequences")
            frozen.append(
                (require_identifier(item[0], "pairs[0]"), require_identifier(item[1], "pairs[1]"))
            )
        keys = [key for key, _ in frozen]
        clash = sorted({key for key in keys if keys.count(key) > 1})
        if clash:
            raise GraphValidationError(f"a variant selection chooses one option per set, got {clash}")
        object.__setattr__(self, "pairs", tuple(sorted(frozen)))
        object.__setattr__(
            self,
            "migration_receipt_ids",
            tuple(sorted({require_id(item, "migration_receipt_ids[]") for item in self.migration_receipt_ids})),
        )
        if self.actor is not None and not isinstance(self.actor, ComponentVersion):
            raise SchemaValidationError("actor must be a ComponentVersion or None")
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def as_map(self) -> dict[str, str]:
        return {key: value for key, value in self.pairs}

    def option_of(self, variant_set_id: str) -> str | None:
        return self.as_map().get(require_identifier(variant_set_id, "variant_set_id"))

    def with_option(self, variant_set_id: str, option_id: str) -> "VariantSelection":
        """Return a new selection; the frozen one is what earlier snapshots recorded."""

        set_id = require_identifier(variant_set_id, "variant_set_id")
        option = require_identifier(option_id, "option_id")
        rest = tuple(item for item in self.pairs if item[0] != set_id)
        return replace(self, pairs=tuple(sorted(rest + ((set_id, option),))))

    def without(self, variant_set_id: str) -> "VariantSelection":
        set_id = require_identifier(variant_set_id, "variant_set_id")
        return replace(self, pairs=tuple(item for item in self.pairs if item[0] != set_id))

    @property
    def digest(self) -> str:
        return content_digest(self.pairs)


def _set_index(sets: Sequence[VariantSet]) -> dict[str, VariantSet]:
    index: dict[str, VariantSet] = {}
    for item in sets:
        variant_set = VariantSet.coerce(item, "sets[]")
        if variant_set.variant_set_id in index:
            raise GraphValidationError(f"duplicate variant set {variant_set.variant_set_id}")
        index[variant_set.variant_set_id] = variant_set
    if len(index) > MAX_VARIANT_SETS:
        raise GraphValidationError(f"a production may declare at most {MAX_VARIANT_SETS} variant sets")
    return index


def resolve_selection(sets: Sequence[VariantSet], selection: VariantSelection) -> dict[str, str]:
    """The effective selection, with declared defaults filled in."""

    index = _set_index(sets)
    effective = {key: value for key, value in selection.pairs}
    for set_id, variant_set in index.items():
        if set_id in effective or variant_set.allow_unselected:
            continue
        if variant_set.default_option_id is not None:
            effective[set_id] = variant_set.default_option_id
    return effective


def anchor_rulings(
    sets: Sequence[VariantSet],
    selection: VariantSelection,
    effective: Mapping[str, str] | None = None,
) -> tuple[tuple[str, str], ...]:
    """Refuse a protected identity anchor drifting through an ordinary variant.

    Each ruling is paired with the anchor it addresses, because a merge has to turn
    it into a conflict a reviewer can settle by id rather than a sentence to re-read.
    """

    selection = VariantSelection.coerce(selection, "selection")
    chosen = dict(effective if effective is not None else resolve_selection(sets, selection))
    found: list[tuple[str, str]] = []
    for variant_set in sets:
        anchor = variant_set.identity_anchor
        if anchor is None:
            continue
        anchor = IdentityAnchorPolicy.coerce(anchor, "identity_anchor")
        option_id = chosen.get(variant_set.variant_set_id)
        if option_id is None or option_id == anchor.baseline_option_id:
            continue
        try:
            option = variant_set.option(option_id)
        except GraphValidationError:
            continue  # the choice names an option this axis no longer has; that ruling is reported once, elsewhere
        if not anchor.drifts(option.anchor_digest):
            continue
        if option.migration_receipt_id in selection.migration_receipt_ids:
            continue
        found.append(
            (
                f"anchor:{anchor.anchor_id}",
                f"variant {variant_set.variant_set_id}={option_id} moves protected identity anchor "
                f"{anchor.anchor_id} (policy {anchor.policy_ref.text}) without its migration receipt "
                f"{option.migration_receipt_id}",
            )
        )
    return tuple(found)


def anchor_violations(
    sets: Sequence[VariantSet],
    selection: VariantSelection,
    effective: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    return tuple(sorted(reason for _, reason in anchor_rulings(sets, selection, effective)))


def selection_rulings(
    sets: Sequence[VariantSet],
    constraints: Sequence[VariantConstraint],
    selection: VariantSelection,
) -> tuple[tuple[str, str], ...]:
    """Every reason this selection may not be built, each naming what has to change.

    The address is the part a merge needs: "axis variant.outfit", "constraint
    constraint.keynote-launch", "anchor anchor.persona.face". The reason is prose for
    the reviewer. Both come from exactly the rules ``validate_selection`` applies, so
    a gate and a merge can never disagree about what is legal.
    """

    index = _set_index(sets)
    selection = VariantSelection.coerce(selection, "selection")
    found: list[tuple[str, str]] = []
    for set_id, option_id in selection.pairs:
        variant_set = index.get(set_id)
        if variant_set is None:
            found.append((f"variant:{set_id}", f"selection names unknown variant set {set_id!r}"))
            continue
        try:
            variant_set.option(option_id)
        except GraphValidationError as error:
            found.append((f"variant:{set_id}", str(error)))
    effective = resolve_selection(sets, selection)
    for set_id, variant_set in index.items():
        if set_id not in effective and not variant_set.allow_unselected and variant_set.default_option_id is None:
            found.append(
                (
                    f"variant-set:{set_id}",
                    f"variant set {set_id} is mandatory: it allows no unselected state and declares no default",
                )
            )
    for item in constraints:
        constraint = VariantConstraint.coerce(item, "constraints[]")
        reason = constraint.violation(effective)
        if reason is not None:
            found.append(
                (f"variant-constraint:{constraint.constraint_id}", f"constraint {constraint.constraint_id}: {reason}")
            )
    found.extend(anchor_rulings(sets, selection, effective))
    return tuple(sorted(set(found)))


def validate_selection(
    sets: Sequence[VariantSet],
    constraints: Sequence[VariantConstraint],
    selection: VariantSelection,
) -> tuple[str, ...]:
    """Every reason this selection may not be built, so a cost is never paid first.

    Violations are returned rather than raised: a merge needs the whole list to
    type its conflicts, a build gate needs the first one in an error message, and
    both must be decided by exactly these rules.
    """

    return tuple(sorted({reason for _, reason in selection_rulings(sets, constraints, selection)}))


@dataclass(frozen=True)
class ExperimentPlan(Record):
    """The bound an EXPERIMENT branch carries: hypothesis, cost, providers, retention."""

    experiment_id: str
    origin_snapshot_id: str
    hypothesis: str
    max_attempts: int = 8
    allowed_provider_refs: tuple[ExternalRef, ...] = ()
    acceptance_criterion_refs: tuple[ExternalRef, ...] = ()
    retention_expires_at_ms: Any = None
    actor: Any = None

    NESTED = {
        "allowed_provider_refs": of(ExternalRef),
        "acceptance_criterion_refs": of(ExternalRef),
        "actor": of(ComponentVersion),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "experiment_id", require_id(self.experiment_id, "experiment_id"))
        object.__setattr__(
            self, "origin_snapshot_id", require_id(self.origin_snapshot_id, "origin_snapshot_id")
        )
        object.__setattr__(self, "hypothesis", require_text(self.hypothesis, "hypothesis", maximum=1024))
        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int) or self.max_attempts < 1:
            raise SchemaValidationError("max_attempts must be a positive integer budget")
        object.__setattr__(
            self, "allowed_provider_refs", _refs(self.allowed_provider_refs, "allowed_provider_refs", maximum=64)
        )
        object.__setattr__(
            self,
            "acceptance_criterion_refs",
            _refs(self.acceptance_criterion_refs, "acceptance_criterion_refs", maximum=64),
        )
        if self.retention_expires_at_ms is not None:
            object.__setattr__(
                self,
                "retention_expires_at_ms",
                require_millis(self.retention_expires_at_ms, "retention_expires_at_ms"),
            )
        if self.actor is not None and not isinstance(self.actor, ComponentVersion):
            raise SchemaValidationError("actor must be a ComponentVersion or None")

    def admits_attempt(self, index: int) -> bool:
        return 1 <= index <= self.max_attempts

    def expired(self, now_ms: int) -> bool:
        return self.retention_expires_at_ms is not None and now_ms > self.retention_expires_at_ms


@dataclass(frozen=True)
class RetentionPin(Record):
    """A statement that something must survive cleanup, with the reason that says why."""

    pin_id: str
    target: ExternalRef
    reasons: tuple[PinReason, ...] = (PinReason.AUDIT,)
    actor: Any = None
    created_at_ms: int = 0
    expires_at_ms: Any = None
    note: Any = None

    NESTED = {"target": of(ExternalRef), "actor": of(ComponentVersion)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "pin_id", require_id(self.pin_id, "pin_id"))
        if not isinstance(self.target, ExternalRef):
            raise SchemaValidationError("target must be an ExternalRef to the pinned object")
        reasons = require_bounded(self.reasons, "reasons", maximum=MAX_PIN_REASONS)
        resolved = tuple(
            sorted({PinReason.parse(item, "reasons[]") for item in reasons}, key=lambda item: item.value)
        )
        if not resolved:
            raise GraphValidationError("a retention pin must state at least one reason")
        object.__setattr__(self, "reasons", resolved)
        if self.actor is not None and not isinstance(self.actor, ComponentVersion):
            raise SchemaValidationError("actor must be a ComponentVersion or None")
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        if self.expires_at_ms is not None:
            if self.expires_at_ms <= self.created_at_ms:
                raise SchemaValidationError("expires_at_ms must follow created_at_ms")
            object.__setattr__(self, "expires_at_ms", require_millis(self.expires_at_ms, "expires_at_ms"))
        object.__setattr__(self, "note", require_optional_text(self.note, "note", maximum=512))

    def covers(self, reference: Any) -> bool:
        return self.target == ExternalRef.coerce(reference, "reference")

    def is_live(self, now_ms: int) -> bool:
        return self.expires_at_ms is None or now_ms <= self.expires_at_ms

    def may_release(self, now_ms: int) -> bool:
        """Only a TTL pin ever releases; rights, audit and golden pins do not expire quietly."""

        if PinReason.RIGHTS in self.reasons or PinReason.AUDIT in self.reasons:
            return False
        return self.expires_at_ms is not None and now_ms > self.expires_at_ms


@dataclass(frozen=True)
class Branch(Record):
    """Stable branch identity. Renaming it never produces a different branch."""

    branch_id: str
    project_id: str
    production_id: str
    profile: BranchProfile
    display_name: Any = None
    aliases: tuple[str, ...] = ()
    policy_refs: tuple[ExternalRef, ...] = ()
    creator: Any = None
    created_at_ms: int = 0
    experiment: Any = None
    metadata: tuple[tuple[str, Any], ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "policy_refs": of(ExternalRef),
        "creator": of(ComponentVersion),
        "experiment": of(ExperimentPlan),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_id", require_id(self.branch_id, "branch_id"))
        for name in ("project_id", "production_id"):
            object.__setattr__(self, name, require_id(getattr(self, name), name))
        object.__setattr__(self, "profile", BranchProfile.parse(self.profile, "profile"))
        object.__setattr__(self, "display_name", require_optional_text(self.display_name, "display_name", maximum=256))
        aliases = require_bounded(self.aliases, "aliases", maximum=MAX_ALIASES, kind="alias")
        resolved = tuple(require_identifier(item, "aliases[]") for item in aliases)
        clash = sorted({item for item in resolved if resolved.count(item) > 1})
        if clash:
            raise GraphValidationError(f"branch declares duplicate aliases: {clash}")
        object.__setattr__(self, "aliases", tuple(sorted(set(resolved))))
        object.__setattr__(self, "policy_refs", _refs(self.policy_refs, "policy_refs", maximum=64))
        if self.creator is not None and not isinstance(self.creator, ComponentVersion):
            raise SchemaValidationError("creator must be a ComponentVersion or None")
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        if self.experiment is not None and not isinstance(self.experiment, ExperimentPlan):
            raise SchemaValidationError("experiment must be an ExperimentPlan or None")
        if self.profile is BranchProfile.EXPERIMENT and self.experiment is None:
            raise GraphValidationError(
                f"branch {self.branch_id} is an EXPERIMENT without a plan: an unbounded experiment is how a "
                "project pays for the same render forever"
            )
        if self.profile is not BranchProfile.EXPERIMENT and self.experiment is not None:
            raise GraphValidationError("only an EXPERIMENT branch may carry an experiment plan")
        object.__setattr__(
            self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS)
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def renamed(self, display_name: str) -> "Branch":
        return replace(self, display_name=require_text(display_name, "display_name", maximum=256))

    def with_alias(self, alias: str) -> "Branch":
        name = require_identifier(alias, "alias")
        if name in self.aliases:
            return self
        return replace(self, aliases=tuple(sorted({*self.aliases, name})))


@dataclass(frozen=True)
class BranchRef(Record):
    """The mutable part of a branch: which immutable snapshot is head right now."""

    branch_id: str
    head_snapshot_id: Any = None
    fork_point_snapshot_id: Any = None
    parent_branch_id: Any = None
    state: BranchState = BranchState.ACTIVE
    version: int = 1
    last_transition_id: Any = None
    pin_refs: tuple[ExternalRef, ...] = ()
    updated_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {"pin_refs": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_id", require_id(self.branch_id, "branch_id"))
        for name in ("head_snapshot_id", "fork_point_snapshot_id", "parent_branch_id", "last_transition_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_id(value, name))
        if self.parent_branch_id == self.branch_id:
            raise IdentityError("a branch cannot be its own parent")
        object.__setattr__(self, "state", BranchState.parse(self.state, "state"))
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise SchemaValidationError("version must be a positive integer")
        object.__setattr__(self, "pin_refs", _refs(self.pin_refs, "pin_refs", maximum=64))
        object.__setattr__(self, "updated_at_ms", require_millis(self.updated_at_ms, "updated_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_detached(self) -> bool:
        return self.head_snapshot_id is None


@dataclass(frozen=True)
class ForkReceipt(Record):
    """Proof of exactly where a branch started, because 'from current' is not a fact."""

    fork_id: str
    source_branch_id: str
    source_snapshot_id: str
    new_branch_id: str
    reason_code: str
    initial_selection: Any = None
    inherited_pin_refs: tuple[ExternalRef, ...] = ()
    actor: Any = None
    created_at_ms: int = 0

    NESTED = {"initial_selection": of(VariantSelection), "actor": of(ComponentVersion)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "fork_id", require_id(self.fork_id, "fork_id"))
        for name in ("source_branch_id", "source_snapshot_id", "new_branch_id"):
            object.__setattr__(self, name, require_id(getattr(self, name), name))
        if self.new_branch_id == self.source_branch_id:
            raise IdentityError("a fork creates a new branch identity, it does not rebind the source")
        object.__setattr__(self, "reason_code", require_identifier(self.reason_code, "reason_code"))
        object.__setattr__(
            self, "inherited_pin_refs", _refs(self.inherited_pin_refs, "inherited_pin_refs", maximum=64)
        )
        if self.actor is not None and not isinstance(self.actor, ComponentVersion):
            raise SchemaValidationError("actor must be a ComponentVersion or None")
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        if self.initial_selection is not None and not isinstance(self.initial_selection, VariantSelection):
            raise SchemaValidationError("initial_selection must be a VariantSelection or None")


_ESTABLISHING: frozenset[str] = frozenset({"branch-register", "branch-fork"})


class BranchLedger:
    """Branch identities, refs and aliases. Refs move; nothing else does.

    This is a store, not a semantic authority: it is passed explicitly, has no
    global instance, and never edits a snapshot or a branch identity in place.
    """

    def __init__(self) -> None:
        self._branches: dict[str, Branch] = {}
        self._refs: dict[str, BranchRef] = {}
        self._aliases = AliasLedger()
        self._receipts: dict[str, TransitionReceipt] = {}
        self._commands: dict[str, TransitionReceipt] = {}
        self._forks: dict[str, ForkReceipt] = {}

    def register(
        self,
        branch: Branch,
        *,
        head_snapshot_id: Any = None,
        fork_point_snapshot_id: Any = None,
        parent_branch_id: Any = None,
        pin_refs: Sequence[ExternalRef] = (),
        actor: Any = None,
        reason_code: str = "branch-register",
        now_ms: int = 0,
    ) -> BranchRef:
        branch = Branch.coerce(branch, "branch")
        if branch.branch_id in self._branches:
            stored = self._branches[branch.branch_id]
            if stored != branch:
                raise GraphValidationError(
                    f"branch {branch.branch_id} already exists with different identity data"
                )
            return self._refs[branch.branch_id]
        if branch.profile is BranchProfile.CANONICAL and any(
            item.profile is BranchProfile.CANONICAL for item in self._branches.values()
        ):
            raise GraphValidationError(
                f"{branch.branch_id} would be a second CANONICAL branch: a competing direction is an "
                "EXPERIMENT or CAMPAIGN branch, never a second main line"
            )
        for alias in branch.aliases:
            self._aliases.bind(alias, EntityKind.BRANCH, branch.branch_id, created_at_ms=branch.created_at_ms)
        self._branches[branch.branch_id] = branch
        reference = BranchRef(
            branch_id=branch.branch_id,
            head_snapshot_id=head_snapshot_id,
            fork_point_snapshot_id=fork_point_snapshot_id,
            parent_branch_id=parent_branch_id,
            pin_refs=tuple(pin_refs),
            updated_at_ms=now_ms,
        )
        if head_snapshot_id is not None:
            receipt = TransitionReceipt(
                transition_id=new_id(),
                entity_kind=EntityKind.BRANCH,
                entity_id=branch.branch_id,
                to_state=require_id(head_snapshot_id, "head_snapshot_id"),
                actor=require_component_version(actor if actor is not None else branch.creator, "actor"),
                reason_code=reason_code,
                timestamp_ms=now_ms,
            )
            self._receipts[receipt.transition_id] = receipt
            reference = replace(reference, last_transition_id=receipt.transition_id)
        self._refs[branch.branch_id] = reference
        return reference

    def branch(self, branch_id: str) -> Branch:
        wanted = require_id(branch_id, "branch_id")
        try:
            return self._branches[wanted]
        except KeyError as error:
            raise GraphValidationError(f"unknown branch {wanted!r}") from error

    def has_branch(self, branch_id: str) -> bool:
        return require_id(branch_id, "branch_id") in self._branches

    def ref(self, branch_id: str) -> BranchRef:
        wanted = require_id(branch_id, "branch_id")
        try:
            return self._refs[wanted]
        except KeyError as error:
            raise GraphValidationError(f"unknown branch {wanted!r}") from error

    def head(self, branch_id: str) -> str:
        reference = self.ref(branch_id)
        if reference.head_snapshot_id is None:
            raise GraphValidationError(f"branch {reference.branch_id} is detached and has no head snapshot")
        return reference.head_snapshot_id

    def branches(self, *, profile: Any = None) -> tuple[Branch, ...]:
        found = tuple(self._branches[key] for key in sorted(self._branches))
        if profile is None:
            return found
        wanted = BranchProfile.parse(profile, "profile")
        return tuple(item for item in found if item.profile is wanted)

    def resolve(self, alias: str) -> str:
        """An alias answers with an identity. The name is never the identity."""

        return self._aliases.resolve(alias).entity_id

    def aliases(self, branch_id: str) -> tuple[AliasRef, ...]:
        return self._aliases.aliases_of(require_id(branch_id, "branch_id"))

    def rename(self, branch_id: str, display_name: str) -> Branch:
        branch = self.branch(branch_id)
        renamed = branch.renamed(display_name)
        self._branches[branch.branch_id] = renamed
        return renamed

    def alias(self, branch_id: str, alias: str, *, now_ms: int = 0) -> Branch:
        branch = self.branch(branch_id)
        name = require_identifier(alias, "alias")
        self._aliases.bind(name, EntityKind.BRANCH, branch.branch_id, created_at_ms=now_ms)
        bound = branch.with_alias(name)
        self._branches[branch.branch_id] = bound
        return bound

    def fork(
        self,
        source_branch_id: str,
        source_snapshot_id: str,
        *,
        new_branch_id: str,
        profile: Any,
        display_name: Any = None,
        reason_code: str = "planned-fork",
        initial_selection: VariantSelection | None = None,
        actor: Any = None,
        aliases: Sequence[str] = (),
        experiment: ExperimentPlan | None = None,
        now_ms: int = 0,
    ) -> tuple[Branch, BranchRef, ForkReceipt]:
        """Fork from one exact immutable snapshot, never from a floating 'current'."""

        source = self.branch(source_branch_id)
        snapshot_id = require_id(source_snapshot_id, "source_snapshot_id")
        fork = ForkReceipt(
            fork_id=new_id(),
            source_branch_id=source.branch_id,
            source_snapshot_id=snapshot_id,
            new_branch_id=require_id(new_branch_id, "new_branch_id"),
            reason_code=reason_code,
            initial_selection=initial_selection,
            inherited_pin_refs=self.ref(source.branch_id).pin_refs,
            actor=actor,
            created_at_ms=now_ms,
        )
        branch = Branch(
            branch_id=fork.new_branch_id,
            project_id=source.project_id,
            production_id=source.production_id,
            profile=profile,
            display_name=display_name,
            aliases=tuple(aliases),
            policy_refs=source.policy_refs,
            creator=actor,
            created_at_ms=now_ms,
            experiment=experiment,
        )
        reference = self.register(
            branch,
            head_snapshot_id=snapshot_id,
            fork_point_snapshot_id=snapshot_id,
            parent_branch_id=source.branch_id,
            pin_refs=fork.inherited_pin_refs,
            actor=actor,
            reason_code="branch-fork",
            now_ms=now_ms,
        )
        self._forks[branch.branch_id] = fork
        return branch, reference, fork

    def fork_receipt(self, branch_id: str) -> ForkReceipt:
        wanted = require_id(branch_id, "branch_id")
        try:
            return self._forks[wanted]
        except KeyError as error:
            raise GraphValidationError(f"branch {wanted!r} was not created by a recorded fork") from error

    def advance(
        self,
        branch_id: str,
        new_head_snapshot_id: str,
        *,
        actor: Any,
        reason_code: str = "committed",
        expected_head_snapshot_id: Any = None,
        evidence_refs: Sequence[ExternalRef] = (),
        policy_ref: ExternalRef | None = None,
        command_id: str | None = None,
        command_digest: str | None = None,
        now_ms: int = 0,
    ) -> tuple[BranchRef, TransitionReceipt]:
        """Move one branch ref onto a snapshot that already exists.

        A duplicate command is idempotent; a command racing a moved head is a
        conflict. Either way the ref never jumps silently.
        """

        reference = self.ref(branch_id)
        target = require_id(new_head_snapshot_id, "new_head_snapshot_id")
        if not reference.state.accepts_advance:
            raise GraphValidationError(
                f"branch {reference.branch_id} is {reference.state.value} and may not advance its head"
            )
        if expected_head_snapshot_id is not None and require_id(
            expected_head_snapshot_id, "expected_head_snapshot_id"
        ) != reference.head_snapshot_id:
            raise GraphValidationError(
                f"branch {reference.branch_id} moved: expected head {expected_head_snapshot_id} but its head "
                f"is {reference.head_snapshot_id}; re-read the head instead of forcing it"
            )
        receipt = TransitionReceipt(
            transition_id=new_id(),
            entity_kind=EntityKind.BRANCH,
            entity_id=reference.branch_id,
            from_state=reference.head_snapshot_id,
            to_state=target,
            actor=require_component_version(actor),
            reason_code=reason_code,
            timestamp_ms=now_ms,
            causal_parent_receipt_id=reference.last_transition_id,
            evidence_refs=tuple(evidence_refs),
            policy_ref=policy_ref,
            command_id=command_id,
            command_digest=command_digest,
        )
        if command_id is not None:
            earlier = self._commands.get(command_id)
            if earlier is not None:
                conflict = receipt.conflicts_with(earlier)
                if conflict is not None:
                    raise GraphValidationError(f"command {command_id} is not replayable: {conflict}")
                return reference, earlier
        self._receipts[receipt.transition_id] = receipt
        if command_id is not None:
            self._commands[command_id] = receipt
        if reference.head_snapshot_id == target:
            self._refs[reference.branch_id] = replace(
                reference, last_transition_id=receipt.transition_id, updated_at_ms=now_ms
            )
            return self._refs[reference.branch_id], receipt
        moved = replace(
            reference,
            head_snapshot_id=target,
            version=reference.version + 1,
            last_transition_id=receipt.transition_id,
            updated_at_ms=now_ms,
        )
        self._refs[reference.branch_id] = moved
        return moved, receipt

    def transition(self, transition_id: str) -> TransitionReceipt:
        wanted = require_id(transition_id, "transition_id")
        try:
            return self._receipts[wanted]
        except KeyError as error:
            raise GraphValidationError(f"unknown transition receipt {wanted!r}") from error

    def transitions(self, branch_id: str) -> tuple[TransitionReceipt, ...]:
        """The branch history, walked through causal parents, not through ids.

        A UUIDv7 sorts by the wall clock that minted it, which is this process's
        clock, not the production's logical time. The chain is the order.
        """

        reference = self.ref(require_id(branch_id, "branch_id"))
        chain: list[TransitionReceipt] = []
        cursor = reference.last_transition_id
        seen: set[str] = set()
        while cursor is not None:
            if cursor in seen:
                raise IdentityError(f"branch {reference.branch_id} receipt chain cycles at {cursor}")
            seen.add(str(cursor))
            receipt = self.transition(cursor)
            chain.append(receipt)
            cursor = receipt.causal_parent_receipt_id
        return tuple(reversed(chain))

    def set_state(
        self, branch_id: str, state: Any, *, actor: Any, now_ms: int = 0, reason_code: str = "branch-state"
    ) -> BranchRef:
        reference = self.ref(branch_id)
        wanted = BranchState.parse(state, "state")
        if wanted is reference.state:
            return reference
        receipt = TransitionReceipt(
            transition_id=new_id(),
            entity_kind=EntityKind.BRANCH,
            entity_id=reference.branch_id,
            from_state=reference.state.value,
            to_state=wanted.value,
            actor=require_component_version(actor),
            reason_code=reason_code,
            timestamp_ms=now_ms,
            causal_parent_receipt_id=reference.last_transition_id,
        )
        self._receipts[receipt.transition_id] = receipt
        moved = replace(
            reference,
            state=wanted,
            version=reference.version + 1,
            last_transition_id=receipt.transition_id,
            updated_at_ms=now_ms,
        )
        self._refs[reference.branch_id] = moved
        return moved

    def pin(self, branch_id: str, pin: Any, *, now_ms: int = 0) -> BranchRef:
        wanted = RetentionPin.coerce(pin, "pin")
        return self.pin_reference(branch_id, wanted.target, now_ms=now_ms)

    def pin_reference(self, branch_id: str, target: Any, *, now_ms: int = 0) -> BranchRef:
        reference = self.ref(branch_id)
        wanted = ExternalRef.coerce(target, "target")
        if wanted in reference.pin_refs:
            return reference
        moved = replace(
            reference,
            pin_refs=tuple(sorted({*reference.pin_refs, wanted}, key=lambda item: item.text)),
            updated_at_ms=now_ms,
        )
        self._refs[reference.branch_id] = moved
        return moved

    def unpin(self, branch_id: str, target: Any, *, now_ms: int = 0) -> BranchRef:
        reference = self.ref(branch_id)
        wanted = ExternalRef.coerce(target, "target")
        if wanted not in reference.pin_refs:
            raise GraphValidationError(f"branch {reference.branch_id} never pinned {wanted.text}")
        moved = replace(
            reference,
            pin_refs=tuple(item for item in reference.pin_refs if item != wanted),
            updated_at_ms=now_ms,
        )
        self._refs[reference.branch_id] = moved
        return moved

    def pins(self, branch_id: str) -> tuple[ExternalRef, ...]:
        return self.ref(branch_id).pin_refs

    def descendants(self, branch_id: str) -> tuple[str, ...]:
        wanted = require_id(branch_id, "branch_id")
        self.branch(wanted)
        return tuple(key for key in sorted(self._refs) if self._refs[key].parent_branch_id == wanted)

    def ancestry(self, branch_id: str) -> tuple[str, ...]:
        chain: list[str] = []
        cursor: Any = require_id(branch_id, "branch_id")
        seen: set[str] = set()
        while cursor is not None:
            if cursor in seen:
                raise IdentityError(f"branch parentage cycles at {cursor}")
            seen.add(cursor)
            chain.append(cursor)
            cursor = self.ref(cursor).parent_branch_id
        return tuple(chain)

    def replay(self, branch_id: str) -> BranchRef:
        """Rebuild the ref from its receipts and prove current state is reconstructable."""

        wanted = require_id(branch_id, "branch_id")
        reference = self.ref(wanted)
        head: Any = None
        parent: Any = None
        version = 1
        state = BranchState.ACTIVE
        for receipt in self.transitions(wanted):
            parent = receipt.transition_id
            if receipt.reason_code in _ESTABLISHING:
                head = receipt.to_state
                continue
            if receipt.from_state == receipt.to_state:
                continue
            version += 1
            if receipt.reason_code == "branch-state":
                state = BranchState.parse(receipt.to_state, "state")
                continue
            head = receipt.to_state
        rebuilt = BranchRef(
            branch_id=wanted,
            head_snapshot_id=head,
            fork_point_snapshot_id=reference.fork_point_snapshot_id,
            parent_branch_id=reference.parent_branch_id,
            state=state,
            version=version,
            last_transition_id=parent,
            pin_refs=reference.pin_refs,
            updated_at_ms=reference.updated_at_ms,
        )
        if rebuilt != reference:
            raise GraphValidationError(
                f"branch {wanted} does not replay from its receipts: the stored ref disagrees with its history"
            )
        return rebuilt

    def __len__(self) -> int:
        return len(self._branches)
