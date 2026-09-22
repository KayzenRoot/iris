"""F-M03-05/06 Constraint semantics: rules about the work, not syntax for a generator.

A constraint is a typed rule addressed at a semantic path, with a polarity, a strength, a
scope, and optionally a tolerance, an anti-reference or a protected anchor. None of those
fields is a fragment of negative-prompt syntax (§5.10): "FORBID lens_flare on still_frames at
HARD strength" is the rule, and whatever renders it for a given model is a derived artifact
produced later, by a layer that is allowed to be wrong about the model and is not allowed to
be wrong about the rule.

Polarity and strength are independent columns, deliberately, because every real team
discovers they need both: "prefer, but never exceed" and "forbid, softly, while we
experiment" are different instructions, and a kernel that collapsed them into one severity
ladder would have to invent a meaning for every cell it merged (§5.11).

Severity vocabulary is imported from M01 by object identity rather than re-declared. M01 is
the sole authority for how serious a defect is, so a private M03 scale would be a second one,
and the two would drift in whichever direction was least noticed.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from iris_quality.defects import DefectSeverity

from .base import Labeled, Record, of
from .errors import (
    AdmissionRefusedError,
    AuthorityError,
    LimitExceededError,
    PredicateError,
    RevisionFrozenError,
    ScopeError,
    SchemaValidationError,
    ToleranceError,
    UntrustedExtensionError,
)
from .identity import AuthorityLevel, RefKind, SemanticRef, require_bound_ref
from .intent import IntentAuthorityRef, ModalChannel
from .limits import (
    MAX_ANTI_REFERENCE_FACETS,
    MAX_CONDITIONS,
    MAX_CONSTRAINTS_PER_BUNDLE,
    MAX_PROTECTED_ZONES,
    MAX_PROVENANCE_REFS,
    MAX_RATIONALE_CHARS,
    MAX_SCOPE_PATHS,
    MAX_TEXT_CHARS,
    MAX_TOLERANCE_DIMENSIONS,
)
from .predicates import (
    PredicateCall,
    PredicateRegistry,
    reject_interpolation,
    require_known_predicate,
)
from .sources import ProvenanceCapsule, bounded_metadata, require_source_refs
from .versions import (
    content_digest,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "AntiReference",
    "Comparison",
    "Condition",
    "ConditionOperator",
    "Constraint",
    "ConstraintBundle",
    "ConstraintCoverage",
    "ConstraintPolarity",
    "ConstraintScope",
    "ConstraintStrength",
    "ConstraintViolationRef",
    "CoverageState",
    "CrossModalLink",
    "ProtectedAnchor",
    "ToleranceEnvelope",
    "channel_set",
    "require_no_authority_in_scope",
]

#: Modalities a constraint may address: every emit-able ``intent.ModalChannel`` minus the two
#: labels that name no channel. ``CROSS`` says "these channels must agree", which is a link
#: rather than a scope, and ``UNSPECIFIED`` says nobody ever said — a rule scoped to nothing is
#: enforced by nothing. Derived from the enum instead of hand-listed, because the previous
#: duplicate had drifted: MUSIC existed as a statement modality and not as a rule scope, so the
#: §6 narration-and-music brief could state a music fact but could not bind a rule to it.
KNOWN_CHANNELS = tuple(
    sorted({member.value for member in ModalChannel} - {ModalChannel.CROSS.value, ModalChannel.UNSPECIFIED.value})
)


def channel_set(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list of channel labels")
    labels = tuple(sorted({require_text(item, f"{field_name}[]", maximum=32).upper() for item in value}))
    unknown = sorted(set(labels) - set(KNOWN_CHANNELS))
    if unknown:
        raise SchemaValidationError(
            f"{field_name} names unknown channels {unknown}; a constraint scoped to a channel nothing "
            "can emit looks enforced and is simply lost"
        )
    return labels


class ConstraintPolarity(Labeled):
    """Whether the rule asks for something or refuses something.

    ``FORBID`` and ``AVOID`` are the negative half, and they stay first-class in the record
    rather than being folded into a positive rule with a flag. Inverting a prohibition into
    "prefer the opposite" is the quiet corruption §5.15 is about: a provider that cannot
    honour the negative still looks compliant.
    """

    REQUIRE = "REQUIRE"
    FORBID = "FORBID"
    PREFER = "PREFER"
    AVOID = "AVOID"
    ALLOW = "ALLOW"

    @property
    def negative(self) -> bool:
        return self in {ConstraintPolarity.FORBID, ConstraintPolarity.AVOID}

    @property
    def strictness(self) -> int:
        """Ordering for *conflict* analysis only, never for authority.

        Two rules on one path can disagree in polarity, and the resolver needs a direction to
        check first. Reusing this number as a measure of importance would let a preference
        outrank a prohibition in exactly the situations where the prohibition is the point.
        """

        return _POLARITY_STRICTNESS[self]


_POLARITY_STRICTNESS: Mapping[ConstraintPolarity, int] = {
    ConstraintPolarity.ALLOW: 0,
    ConstraintPolarity.PREFER: 1,
    ConstraintPolarity.AVOID: 2,
    ConstraintPolarity.REQUIRE: 3,
    ConstraintPolarity.FORBID: 4,
}


class ConstraintStrength(Labeled):
    """How much the work has to bend to satisfy the rule.

    Independent of polarity: ``FORBID`` plus ``EXPERIMENTAL`` is a real instruction ("do not,
    while we are still deciding whether this matters"), and it is not the same as
    ``FORBID`` plus ``HARD``, which is a boundary.
    """

    HARD = "HARD"
    GUARDED = "GUARDED"
    SOFT = "SOFT"
    ADVISORY = "ADVISORY"
    EXPERIMENTAL = "EXPERIMENTAL"

    @property
    def rank(self) -> int:
        return _STRENGTH_RANKS[self]

    @property
    def blocks_completion(self) -> bool:
        return self in {ConstraintStrength.HARD, ConstraintStrength.GUARDED}

    @property
    def requires_receipt_to_relax(self) -> bool:
        """Relaxing anything at GUARDED or above is a governed act, not a tuning decision.

        The two weakest strengths can be traded away inside a run — an advisory preference
        that costs too much is just dropped and reported. Hard and guarded rules are the ones
        somebody wrote down on purpose, so they need a receipt naming who gave permission
        (§5.30, §5.32).
        """

        return self.rank >= ConstraintStrength.GUARDED.rank


_STRENGTH_RANKS: Mapping[ConstraintStrength, int] = {
    ConstraintStrength.EXPERIMENTAL: 0,
    ConstraintStrength.ADVISORY: 1,
    ConstraintStrength.SOFT: 2,
    ConstraintStrength.GUARDED: 3,
    ConstraintStrength.HARD: 4,
}


class ConditionOperator(Labeled):
    EQ = "EQ"
    NOT_EQ = "NOT_EQ"
    IN = "IN"
    NOT_IN = "NOT_IN"
    EXISTS = "EXISTS"
    MISSING = "MISSING"


class Comparison(Labeled):
    """How a tolerance compares against its target.

    ``CLOSEST`` exists because some briefs want an optimum rather than a bound — a camera
    distance, a compression level — and expressing that as two inequalities would turn "as
    near this as practical" into "inside a range", which is a different claim to check.
    """

    EQ = "EQ"
    LTE = "LTE"
    GTE = "GTE"
    LT = "LT"
    GT = "GT"
    BETWEEN = "BETWEEN"
    CLOSEST = "CLOSEST"


@dataclass(frozen=True)
class ConstraintScope(Record):
    """Where a rule applies — and, by construction, what it says about authority.

    There is no authority field here and adding one is the bug this note exists to prevent:
    scope answers "which subjects", authority answers "who may require it", and §5.14 keeps
    them apart because a brief scoped to one deliverable must not become a project-wide rule
    merely because somebody wrote it in a broad-sounding place.
    """

    subject_paths: tuple[str, ...] = ()
    modalities: tuple[str, ...] = ()
    facets: tuple[str, ...] = ()
    phases: tuple[str, ...] = ()
    destinations: tuple[str, ...] = ()
    excluded_paths: tuple[str, ...] = ()
    excluded_modalities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        subjects = _paths(self.subject_paths, "subject_paths")
        if not subjects:
            raise ScopeError(
                "a scope with no subject paths applies everywhere; that is not a scope, it is an "
                "unbounded claim, and §5.14 exists because those read as authority"
            )
        excluded = _paths(self.excluded_paths, "excluded_paths")
        overlap = sorted(set(subjects) & set(excluded))
        if overlap:
            raise ScopeError(
                f"scope both includes and excludes {overlap}; decide, otherwise matching becomes "
                "order-dependent and fingerprints drift with it"
            )
        object.__setattr__(self, "subject_paths", subjects)
        object.__setattr__(self, "excluded_paths", excluded)
        object.__setattr__(self, "modalities", channel_set(self.modalities, "modalities"))
        object.__setattr__(self, "excluded_modalities", channel_set(self.excluded_modalities, "excluded_modalities"))
        object.__setattr__(self, "phases", _tokens(self.phases, "phases", 16))
        object.__setattr__(self, "destinations", _tokens(self.destinations, "destinations", 16))
        facets = _tokens(self.facets, "facets", MAX_ANTI_REFERENCE_FACETS)
        if facets != tuple(sorted(set(facets))):
            raise ScopeError("facets contains duplicates")
        object.__setattr__(self, "facets", facets)

    #: Presence of this attribute is the assertion §5.14 asks for: scope carries none.
    grants_authority = False

    def matches(self, context: Mapping[str, Any]) -> bool:
        """Whether a work context falls inside this scope.

        An exclusion wins over an inclusion without consulting specificity, because
        "everywhere except the teaser" must not flip into "the teaser" the moment somebody
        adds a deeper path to the subject list.
        """

        path = require_semantic_path(context.get("semantic_path", ""), "context.semantic_path")
        if any(_covered(path, excluded) for excluded in self.excluded_paths):
            return False
        if not any(_covered(path, subject) for subject in self.subject_paths):
            return False
        modality = str(context.get("modality", "")).upper()
        if modality in self.excluded_modalities:
            return False
        if self.modalities and modality and modality not in self.modalities:
            return False
        phase = str(context.get("phase", ""))
        if self.phases and phase and phase not in self.phases:
            return False
        destination = str(context.get("destination", ""))
        if self.destinations and destination and destination not in self.destinations:
            return False
        return True

    def intersects(self, other: "ConstraintScope") -> bool:
        """Whether two scopes can apply to one subject, which is what a conflict needs.

        Disjoint scopes must not conflict (§18), and the only honest test is whether any path
        or channel could fall in both — not whether the two lists look similar.
        """

        if not isinstance(other, ConstraintScope):
            raise SchemaValidationError("intersects expects a ConstraintScope")
        if self.excluded_modalities and other.excluded_modalities:
            paths_disjoint = not any(_related(a, b) for a in self.subject_paths for b in other.subject_paths)
            if paths_disjoint:
                return False
        if not any(_related(a, b) for a in self.subject_paths for b in other.subject_paths):
            return False
        return _channels_overlap(self, other)


def _covered(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + ".")


def _related(left: str, right: str) -> bool:
    return _covered(left, right) or _covered(right, left)


def _channels_overlap(left: ConstraintScope, right: ConstraintScope) -> bool:
    a, b = set(left.modalities), set(right.modalities)
    if not a or not b:
        return True
    return bool(a & b) or {"CROSS"} & a or {"CROSS"} & b


@dataclass(frozen=True)
class Condition(Record):
    """The circumstance under which a rule is active, typed and free of expressions.

    Conditions are matched against a context rather than evaluated, which is what lets
    §18's "inactive condition does not contaminate the active slice" hold: an inactive rule is
    absent from the slice and from its fingerprint, not present-and-flagged.
    """

    context_key: str
    operator: str
    values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        key = require_identifier(self.context_key, "context_key")
        reject_interpolation(key, "context_key")
        object.__setattr__(self, "context_key", key)
        operator = ConditionOperator.parse(self.operator, "operator")
        object.__setattr__(self, "operator", operator.value)
        values = tuple(sorted({require_text(item, "values[]", maximum=128) for item in (self.values or ())}))
        if operator in {ConditionOperator.IN, ConditionOperator.NOT_IN} and not values:
            raise SchemaValidationError(f"condition {operator.value} needs values to compare against")
        if operator in {ConditionOperator.EQ, ConditionOperator.NOT_EQ} and len(values) != 1:
            raise SchemaValidationError(
                f"condition {operator.value} needs exactly one value, got {len(values)}"
            )
        if operator in {ConditionOperator.EXISTS, ConditionOperator.MISSING} and values:
            raise SchemaValidationError(
                f"condition {operator.value} tests presence, so values make it ambiguous"
            )
        object.__setattr__(self, "values", values)

    def holds(self, context: Mapping[str, Any]) -> bool:
        operator = ConditionOperator.parse(self.operator)
        raw = context.get(self.context_key)
        if operator is ConditionOperator.EXISTS:
            return raw is not None
        if operator is ConditionOperator.MISSING:
            return raw is None
        present = () if raw is None else (raw if isinstance(raw, (list, tuple)) else (raw,))
        text = tuple(str(item).upper() for item in present)
        wanted = tuple(item.upper() for item in self.values)
        if operator is ConditionOperator.EQ:
            return len(text) == 1 and text[0] == wanted[0]
        if operator is ConditionOperator.NOT_EQ:
            return not (len(text) == 1 and text[0] == wanted[0])
        if operator is ConditionOperator.IN:
            return bool(set(text) & set(wanted))
        return not bool(set(text) & set(wanted))


#: Declared spelling -> (canonical unit, multiplier into it). Aliases exist so the same rule
#: written in ms or in seconds fingerprints alike; a domain measure such as "brand-compliance
#: points" is deliberately absent, because any conversion the kernel invented for it would be
#: a claim about a metric it does not own — those arrive as extensions with their own metric.
UNIT_ALIASES: Mapping[str, tuple[str, float]] = {
    "S": ("SECOND", 1.0),
    "SECOND": ("SECOND", 1.0),
    "SECONDS": ("SECOND", 1.0),
    "MS": ("SECOND", 0.001),
    "MILLISECOND": ("SECOND", 0.001),
    "MILLISECONDS": ("SECOND", 0.001),
    "PERCENT": ("PERCENT", 1.0),
    "PCT": ("PERCENT", 1.0),
    "RATIO": ("RATIO", 1.0),
    "DB": ("DECIBEL", 1.0),
    "DECIBEL": ("DECIBEL", 1.0),
    "DECIBELS": ("DECIBEL", 1.0),
    "LUX": ("LUX", 1.0),
    "PX": ("PIXEL", 1.0),
    "PIXEL": ("PIXEL", 1.0),
    "PIXELS": ("PIXEL", 1.0),
    "CHAR": ("CHARACTER", 1.0),
    "CHARACTER": ("CHARACTER", 1.0),
    "CHARACTERS": ("CHARACTER", 1.0),
    "WORD": ("WORD", 1.0),
    "WORDS": ("WORD", 1.0),
    "COUNT": ("COUNT", 1.0),
    "STOP": ("STOP", 1.0),
    "EV": ("STOP", 1.0),
    # Frame duration depends on the sequence's frame rate, which is project state M03 does not
    # own; the unit stays distinct so nobody can compare it against a seconds bound.
    "FRAME": ("FRAME", 1.0),
    "FRAMES": ("FRAME", 1.0),
}


@dataclass(frozen=True)
class ToleranceEnvelope(Record):
    """A numeric bound with the unit and the metric its target is actually measured in.

    Units are required, not inferred, and a metric ref must name how the measurement is
    taken. Both exist for the same reason: "under 5" is not a constraint until something says
    five of what, measured how — and a tolerance that cannot be checked is a preference with a
    number in it (§8, §18 units normalise deterministically).

    Conversion to the canonical unit happens at construction, so two envelopes written 500 ms
    and 0.5 s are the same object afterwards. Normalising at read time instead would leave the
    fingerprint free to depend on which spelling an author happened to type.
    """

    measure: str
    comparison: str
    unit: str
    metric_ref: SemanticRef
    target: float | None = None
    lower: float | None = None
    upper: float | None = None
    reference_frame: str | None = None
    hard_limit: bool = False
    declared_unit: str = ""

    def __post_init__(self) -> None:
        measure = require_identifier(self.measure, "measure")
        reject_interpolation(measure, "measure")
        object.__setattr__(self, "measure", measure)
        comparison = Comparison.parse(self.comparison, "comparison")
        object.__setattr__(self, "comparison", comparison.value)
        spelling = str(self.unit).strip().upper()
        entry = UNIT_ALIASES.get(spelling)
        if entry is None:
            raise ToleranceError(
                f"unit {self.unit!r} is not a canonical or alias unit; declare a domain measure "
                "through the extension registry with its own metric rather than letting a tolerance "
                "mean something only its author knows"
            )
        canonical, factor = entry
        if not self.declared_unit:
            object.__setattr__(self, "declared_unit", spelling)
        object.__setattr__(self, "unit", canonical)
        if factor != 1.0:
            scale = lambda value: None if value is None else value * factor  # noqa: E731
            object.__setattr__(self, "target", scale(self.target))
            object.__setattr__(self, "lower", scale(self.lower))
            object.__setattr__(self, "upper", scale(self.upper))
        object.__setattr__(
            self, "metric_ref", require_source_refs((self.metric_ref,), "metric_ref")[0]
        )
        for name in ("target", "lower", "upper"):
            value = getattr(self, name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ToleranceError(f"{name} must be a number, got {value!r}")
            if not math.isfinite(float(value)):
                raise ToleranceError(f"{name} must be a finite number, got {value!r}")
        if comparison is Comparison.BETWEEN:
            if self.lower is None or self.upper is None:
                raise ToleranceError("BETWEEN needs both lower and upper")
            if self.lower > self.upper:
                raise ToleranceError(f"BETWEEN bounds are inverted: {self.lower} > {self.upper}")
        elif self.lower is not None or self.upper is not None:
            raise ToleranceError(
                f"{comparison.value} carries lower/upper bounds it does not use; the extra numbers "
                "would be silently ignored, which is how an unintended bound becomes policy"
            )
        if comparison is not Comparison.BETWEEN and self.target is None:
            raise ToleranceError(f"{comparison.value} needs a target")
        if self.reference_frame is not None:
            object.__setattr__(
                self, "reference_frame", require_identifier(self.reference_frame, "reference_frame")
            )
        if not isinstance(self.hard_limit, bool):
            raise SchemaValidationError("hard_limit must be a boolean")

    @property
    def comparison_kind(self) -> Comparison:
        return Comparison.parse(self.comparison)

    @property
    def converted(self) -> bool:
        """Whether this envelope was declared in a non-canonical unit."""

        return self.declared_unit != self.unit

    def describes(self, value: float) -> bool:
        """Whether a measurement satisfies the envelope.

        Comparison happens in canonical units against a bound that is already normalised, so
        this method has no unit knowledge left to get wrong.
        """

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ToleranceError(f"measurement must be a number, got {value!r}")
        number = float(value)
        if not math.isfinite(number):
            raise ToleranceError(f"measurement must be a finite number, got {value!r}")
        value = number
        comparison = self.comparison_kind
        if comparison is Comparison.BETWEEN:
            return self.lower <= value <= self.upper
        if self.target is None:
            raise ToleranceError(f"{self.measure} envelope has no bound to compare {value} against")
        if comparison is Comparison.EQ:
            return value == self.target
        if comparison is Comparison.LTE:
            return value <= self.target
        if comparison is Comparison.GTE:
            return value >= self.target
        if comparison is Comparison.LT:
            return value < self.target
        return value > self.target

    def fingerprint_inputs(self) -> dict[str, Any]:
        """Canonical form used by constraint fingerprints.

        ``declared_unit`` is excluded on purpose: it records how the author wrote the number,
        and letting it into the fingerprint would mean a unit-spelling edit invalidated every
        downstream artifact that only ever read the canonical value (§5.45).
        """

        payload = self.to_payload()
        payload.pop("declared_unit", None)
        return payload


ToleranceEnvelope.NESTED = {"metric_ref": of(SemanticRef)}


@dataclass(frozen=True)
class AntiReference(Record):
    """What the work must not resemble, stated as facets rather than as a wholesale ban.

    ``facets`` is required and may not be a catch-all: "do not look like that brand" and "do
    not use their logo, typeface or palette" are different instructions, and the unselective
    version also suppresses dimensions the client may want borrowed — which is how a negative
    constraint silently grows into a bigger rule than anybody asked for (§8, §18).
    """

    anti_ref_id: str
    anchor_ref: SemanticRef
    facets: tuple[str, ...]
    modality: str | None = None
    severity_hint: str | None = None
    rationale: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "anti_ref_id", require_identifier(self.anti_ref_id, "anti_ref_id"))
        ref = SemanticRef.coerce(self.anchor_ref, "anchor_ref")
        if ref.content_digest is None and ref.version is None:
            raise UntrustedExtensionError(
                f"anti-reference {self.anti_ref_id} points at {ref.text} with neither a digest nor a "
                "version, so 'not this' cannot be re-checked after the thing it names changes"
            )
        object.__setattr__(self, "anchor_ref", ref)
        facets = _tokens(self.facets, "facets", MAX_ANTI_REFERENCE_FACETS)
        if not facets:
            raise SchemaValidationError(
                f"anti-reference {self.anti_ref_id} names no facet; a ban with no dimension of "
                "application is not selective, it is a suppression order"
            )
        catch_all = sorted(set(facets) & _CATCH_ALL_FACETS)
        if catch_all:
            raise SchemaValidationError(
                f"anti-reference {self.anti_ref_id} uses the catch-all facet {catch_all}; enumerate "
                "the dimensions that must not be imitated, since §18 requires facets to be selective"
            )
        object.__setattr__(self, "facets", facets)
        if self.modality is not None:
            object.__setattr__(self, "modality", channel_set((self.modality,), "modality")[0])
        if self.severity_hint is not None:
            object.__setattr__(
                self, "severity_hint", _m03_severity(self.severity_hint, "severity_hint")
            )
        if self.rationale is not None:
            reject_interpolation(self.rationale, "rationale")
            object.__setattr__(
                self, "rationale", require_text(self.rationale, "rationale", maximum=1024)
            )

    def applies_to(self, facet: str) -> bool:
        return require_text(facet, "facet", maximum=64).upper() in self.facets


_CATCH_ALL_FACETS = frozenset({"ANY", "ALL", "EVERYTHING"})

AntiReference.NESTED = {"anchor_ref": of(SemanticRef)}


class AnchorKind(Labeled):
    """What kind of thing is being held steady.

    ``LEGAL`` and ``SAFETY`` are in the core vocabulary because those anchors are the ones an
    override most often tries to relax, and a kernel that could not name them separately
    could not admit them separately either (§12.8, §12.9).
    """

    IDENTITY = "IDENTITY"
    CANON = "CANON"
    BRAND = "BRAND"
    VOICE = "VOICE"
    STORY = "STORY"
    LEGAL = "LEGAL"
    SAFETY = "SAFETY"
    DELIVERY = "DELIVERY"


class LossConsequence(Labeled):
    """What happens if this anchor does not survive translation into a provider artifact."""

    BLOCKING = "BLOCKING"
    QUALITY_CRITICAL = "QUALITY_CRITICAL"
    COST_CRITICAL = "COST_CRITICAL"
    DEBT = "DEBT"
    IGNORE = "IGNORE"


@dataclass(frozen=True)
class ProtectedAnchor(Record):
    """A semantic point that must survive translation into a provider artifact.

    ``must_survive_translation`` defaults to true because the failure this record exists for
    is silent loss: an anchor a provider could drop without anyone noticing is not protected,
    whatever the field next to it says. A provider that cannot carry it reports a gap, which
    is the only acceptable outcome under §5.15.
    """

    anchor_id: str
    semantic_path: str
    anchor_kind: str = "IDENTITY"
    statement_refs: tuple[SemanticRef, ...] = ()
    must_survive_translation: bool = True
    minimum_authority: str = "PROJECT_RECORD"
    dimension_ref: SemanticRef | None = None
    loss_consequence: str = "BLOCKING"

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchor_id", require_identifier(self.anchor_id, "anchor_id"))
        object.__setattr__(
            self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path")
        )
        kind = AnchorKind.parse(self.anchor_kind, "anchor_kind")
        object.__setattr__(self, "anchor_kind", kind.value)
        object.__setattr__(
            self, "statement_refs", require_source_refs(self.statement_refs, "statement_refs")
        )
        if not isinstance(self.must_survive_translation, bool):
            raise SchemaValidationError("must_survive_translation must be a boolean")
        level = AuthorityLevel.parse(self.minimum_authority, "minimum_authority")
        object.__setattr__(self, "minimum_authority", level.value)
        if self.dimension_ref is not None:
            ref = SemanticRef.coerce(self.dimension_ref, "dimension_ref")
            if ref.kind != RefKind.M01_DIMENSION.value:
                raise UntrustedExtensionError(
                    f"dimension_ref must reference {RefKind.M01_DIMENSION.value}; M03 does not own a "
                    "dimension namespace, and pointing at a private one would invent quality axes (§5.16)"
                )
            object.__setattr__(self, "dimension_ref", ref)
        consequence = LossConsequence.parse(self.loss_consequence, "loss_consequence")
        if consequence is LossConsequence.IGNORE and self.must_survive_translation:
            raise SchemaValidationError(
                f"anchor {self.anchor_id} must survive translation but declares its loss ignorable; "
                "pick one, because §5.15 refuses to let a protected point be dropped quietly"
            )
        object.__setattr__(self, "loss_consequence", consequence.value)

    @property
    def survival_required(self) -> bool:
        return self.must_survive_translation and self.loss_consequence in {
            LossConsequence.BLOCKING.value,
            LossConsequence.QUALITY_CRITICAL.value,
        }

    @property
    def authority_floor(self) -> AuthorityLevel:
        return AuthorityLevel.parse(self.minimum_authority)

    @property
    def anchor_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.ANCHOR.value, ref_id=self.anchor_id).with_digest(self.digest())

    def fingerprint_inputs(self) -> dict[str, Any]:
        return self.to_payload()


ProtectedAnchor.NESTED = {
    "statement_refs": of(SemanticRef),
    "dimension_ref": of(SemanticRef),
}


class ConsistencyClass(Labeled):
    """How tightly channels must agree — and therefore what may legitimately differ.

    ``INTERPRETED`` is the honest label for "the voice and the face should feel like the same
    person", which no measurement can pin to equality; marking it ``STRICT`` anyway would turn
    a judgement into a checkable claim, and the check would fail on work nobody would reject.
    """

    STRICT = "STRICT"
    DERIVED = "DERIVED"
    INTERPRETED = "INTERPRETED"


@dataclass(frozen=True)
class CrossModalLink(Record):
    """A requirement that two or more channels agree.

    Two channels minimum, because a "link" to one channel is a statement about that channel,
    and the extra record would imply a relationship that is not there.
    """

    link_id: str
    channels: tuple[str, ...]
    semantic_paths: tuple[str, ...]
    consistency: str = "STRICT"
    reference_channel: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "link_id", require_identifier(self.link_id, "link_id"))
        channels = channel_set(self.channels, "channels")
        if len(channels) < 2:
            raise SchemaValidationError(
                f"cross-modal link {self.link_id} covers {len(channels)} channel(s); agreement "
                "between one thing and itself is not a link"
            )
        object.__setattr__(self, "channels", channels)
        object.__setattr__(
            self, "semantic_paths", _paths(self.semantic_paths, "semantic_paths")
        )
        object.__setattr__(
            self, "consistency", ConsistencyClass.parse(self.consistency, "consistency").value
        )
        if self.reference_channel is not None:
            label = channel_set((self.reference_channel,), "reference_channel")[0]
            if label not in channels:
                raise SchemaValidationError(
                    f"reference_channel {label} is not one of the linked channels {list(channels)}"
                )
            object.__setattr__(self, "reference_channel", label)


@dataclass(frozen=True)
class Constraint(Record):
    """One typed rule addressed at a semantic path, with its authority and its escape hatches.

    A constraint states *what must be true of the work*, never how to detect it: detection,
    scoring and defect classification belong to M01, and this record therefore carries a
    predicate and a tolerance rather than a checker (§5.10, §5.12). The other half of its
    job is to be honest about how far it reaches, which is why scope, conditions and
    authority are three separate fields — a rule that is true only for the teaser, only when
    the destination is broadcast, and only because a named revision said so must not be
    recordable as a rule that is simply true.
    """

    constraint_id: str
    semantic_path: str
    predicate: PredicateCall
    polarity: str
    strength: str
    scope: ConstraintScope
    authority: IntentAuthorityRef
    conditions: tuple[Condition, ...] = ()
    tolerances: tuple[ToleranceEnvelope, ...] = ()
    anti_references: tuple[AntiReference, ...] = ()
    protected_anchors: tuple[ProtectedAnchor, ...] = ()
    cross_modal_links: tuple[CrossModalLink, ...] = ()
    subject_ref: SemanticRef | None = None
    modality: str = "UNSPECIFIED"
    mandatory: bool = False
    provenance: ProvenanceCapsule | None = None
    source_statement_ids: tuple[str, ...] = ()
    revision_ref: SemanticRef | None = None
    rationale: str | None = None
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "constraint_id", require_identifier(self.constraint_id, "constraint_id")
        )
        object.__setattr__(
            self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path")
        )
        polarity = ConstraintPolarity.parse(self.polarity, "polarity")
        object.__setattr__(self, "polarity", polarity.value)
        strength = ConstraintStrength.parse(self.strength, "strength")
        object.__setattr__(self, "strength", strength.value)
        object.__setattr__(self, "predicate", PredicateCall.coerce(self.predicate, "predicate"))
        scope = ConstraintScope.coerce(self.scope, "scope")
        require_no_authority_in_scope(scope, self.constraint_id)
        if not _covered(scope.subject_paths[0], self.semantic_path) and not _covered(
            self.semantic_path, scope.subject_paths[0]
        ):
            raise ScopeError(
                f"constraint {self.constraint_id} addresses {self.semantic_path} but is scoped to "
                f"{list(scope.subject_paths)}, so which subjects it binds depends on who reads it"
            )
        object.__setattr__(self, "scope", scope)
        object.__setattr__(
            self, "authority", IntentAuthorityRef.coerce(self.authority, "authority")
        )
        self._require_admissible_authority(strength)
        conditions = _seq(self.conditions, Condition, "conditions", MAX_CONDITIONS)
        object.__setattr__(self, "conditions", conditions)
        tolerances = _seq(self.tolerances, ToleranceEnvelope, "tolerances", MAX_TOLERANCE_DIMENSIONS)
        measures = [item.measure for item in tolerances]
        if len(set(measures)) != len(measures):
            raise ToleranceError(
                f"constraint {self.constraint_id} declares the measure "
                f"{sorted({m for m in measures if measures.count(m) > 1})} twice; two bounds on one "
                "measure need an explicit relation, not whichever one a reader meets first"
            )
        object.__setattr__(self, "tolerances", tolerances)
        object.__setattr__(
            self, "anti_references", _seq(self.anti_references, AntiReference, "anti_references", MAX_ANTI_REFERENCE_FACETS)
        )
        anchors = _seq(self.protected_anchors, ProtectedAnchor, "protected_anchors", MAX_PROTECTED_ZONES)
        paths = [item.semantic_path for item in anchors]
        if len(set(paths)) != len(paths):
            raise SchemaValidationError(
                f"constraint {self.constraint_id} protects the same path twice with separate anchors; "
                "merge them, or the stricter of the two becomes a matter of interpretation"
            )
        object.__setattr__(self, "protected_anchors", anchors)
        object.__setattr__(
            self,
            "cross_modal_links",
            _seq(self.cross_modal_links, CrossModalLink, "cross_modal_links", 16),
        )
        for name in ("subject_ref", "revision_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        if self.modality != "UNSPECIFIED":
            object.__setattr__(self, "modality", channel_set((self.modality,), "modality")[0])
        if not isinstance(self.mandatory, bool):
            raise SchemaValidationError("mandatory must be a boolean")
        if self.mandatory and strength is not ConstraintStrength.HARD:
            raise SchemaValidationError(
                f"constraint {self.constraint_id} is mandatory at {strength.value} strength; only a "
                "HARD rule may be declared mandatory, otherwise a preference becomes a blocker and "
                "the strength column stops meaning anything (§5.11)"
            )
        if self.provenance is not None:
            object.__setattr__(
                self, "provenance", ProvenanceCapsule.coerce(self.provenance, "provenance")
            )
        sources = _unique(self.source_statement_ids, "source_statement_ids")
        if sources and self.provenance is None:
            raise SchemaValidationError(
                f"constraint {self.constraint_id} cites statements without a provenance capsule; cite "
                "them through the capsule that recorded the derivation, so the explanation graph has "
                "one path to follow rather than two that can disagree (§5.28)"
            )
        object.__setattr__(self, "source_statement_ids", sources)
        for name, maximum in (("rationale", MAX_RATIONALE_CHARS), ("notes", MAX_TEXT_CHARS)):
            value = getattr(self, name)
            if value is not None:
                reject_interpolation(value, name)
                object.__setattr__(self, name, require_text(value, name, maximum=maximum))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    def _require_admissible_authority(self, strength: ConstraintStrength) -> None:
        """Refuse to let a low-authority claim bind the work hard.

        The predicate text itself is never authority, so the check is on the level the caller
        attached: anything a model inferred, retrieved or observed may state a preference, and
        anything stronger needs a project record behind it (§5.6, §5.14). This is also why
        ``IntentAuthorityRef`` makes the basis name a revision or a policy — the two checks
        close the same hole from opposite sides.
        """

        level = self.authority.level
        if level.rank >= AuthorityLevel.PROJECT_RECORD.rank:
            return
        if strength.rank >= ConstraintStrength.GUARDED.rank or self.mandatory:
            raise AuthorityError(
                f"constraint {self.constraint_id} asserts {strength.value}"
                + (" and mandatory" if self.mandatory else "")
                + f" authority from a {level.value} source; untrusted, retrieved, inferred and "
                "provider-observed input may propose a rule but cannot make it hard, because "
                "imperative text is exactly what an injection attack writes (§5.6)"
            )

    @property
    def polarity_enum(self) -> ConstraintPolarity:
        return ConstraintPolarity.parse(self.polarity)

    @property
    def strength_enum(self) -> ConstraintStrength:
        return ConstraintStrength.parse(self.strength)

    @property
    def is_negative(self) -> bool:
        return self.polarity_enum.negative

    @property
    def requires_receipt_to_relax(self) -> bool:
        return self.strength_enum.requires_receipt_to_relax

    @property
    def protected_survival(self) -> tuple[ProtectedAnchor, ...]:
        """Anchors on this rule that a provider may not drop silently (§5.15)."""

        return tuple(item for item in self.protected_anchors if item.survival_required)

    @property
    def constraint_ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.CONSTRAINT.value, ref_id=self.constraint_id
        ).with_digest(self.digest())

    def is_active(self, context: Mapping[str, Any] | None) -> bool:
        """Whether this rule binds the given work context.

        A rule with no conditions is always active; a rule with conditions is active only when
        all of them hold, which keeps "active" a single well-defined predicate instead of a
        per-reader judgement.
        """

        if not self.conditions:
            return True
        if context is None:
            return False
        return all(condition.holds(context) for condition in self.conditions)

    def applies_to(self, context: Mapping[str, Any]) -> bool:
        return self.is_active(context) and self.scope.matches(context)

    def binds(self, other: "Constraint") -> bool:
        """Whether two constraints could apply to one subject, i.e. whether they can conflict.

        Scope intersection and path agreement are both required: two rules on unrelated paths
        do not contradict each other merely because they share a channel (§18 disjoint scopes).
        """

        if not isinstance(other, Constraint):
            raise SchemaValidationError("binds expects a Constraint")
        if not (
            _covered(self.semantic_path, other.semantic_path)
            or _covered(other.semantic_path, self.semantic_path)
        ):
            return False
        return self.scope.intersects(other.scope)

    def tolerance_for(self, measure: str) -> ToleranceEnvelope | None:
        wanted = require_identifier(measure, "measure")
        return next((item for item in self.tolerances if item.measure == wanted), None)

    def satisfies(self, observations: Mapping[str, float]) -> bool:
        """Check declared tolerances against supplied measurements.

        M03 checks a rule against a number somebody hands it; it does not measure anything, and
        the difference is what keeps §5.16 and §5.17 intact — an M03 result never pretends to
        be an M01 evaluation.
        """

        for envelope in self.tolerances:
            value = observations.get(envelope.measure)
            if value is None:
                if envelope.hard_limit:
                    raise ToleranceError(
                        f"{self.constraint_id} has a hard limit on {envelope.measure} but no "
                        "measurement was supplied; an unmeasured hard bound is not satisfied, it is "
                        "unknown, and unknown fails closed"
                    )
                continue
            if not envelope.describes(float(value)):
                return False
        return True

    def fingerprint_inputs(self, *, active_only: bool = True) -> dict[str, Any]:
        """Canonical, order-stable form used by constraint fingerprints.

        ``rationale``, ``notes`` and ``metadata`` stay out: they are how a rule is explained,
        not what it requires, so rewording one keeps every downstream obligation intact (§5.45).
        When ``active_only`` is set and the rule's conditions do not hold, the caller omits it
        entirely rather than recording it as satisfied.
        """

        return {
            "constraint_id": self.constraint_id,
            "semantic_path": self.semantic_path,
            "predicate": self.predicate.fingerprint_inputs(),
            "polarity": self.polarity,
            "strength": self.strength,
            "scope": self.scope.to_payload(),
            "authority": self.authority.authority,
            "authority_basis": self.authority.basis,
            "mandatory": self.mandatory,
            "modality": self.modality,
            "conditions": [item.to_payload() for item in self.conditions],
            "tolerances": [item.fingerprint_inputs() for item in self.tolerances],
            "anti_references": [item.to_payload() for item in self.anti_references],
            "protected_anchors": [item.fingerprint_inputs() for item in self.protected_anchors],
            "cross_modal_links": [item.to_payload() for item in self.cross_modal_links],
        }


Constraint.NESTED = {
    "predicate": of(PredicateCall),
    "scope": of(ConstraintScope),
    "authority": of(IntentAuthorityRef),
    "conditions": of(Condition),
    "tolerances": of(ToleranceEnvelope),
    "anti_references": of(AntiReference),
    "protected_anchors": of(ProtectedAnchor),
    "cross_modal_links": of(CrossModalLink),
    "subject_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "provenance": of(ProvenanceCapsule),
}


class CoverageState(Labeled):
    """Whether a semantic path has a rule at all, and of what kind.

    ``UNRESOLVED`` is a state rather than an error because coverage is a question asked about a
    path set, and a path whose constraints are all inactive is genuinely uncovered-for-now,
    which is different from a path nobody ever wrote a rule about. Reporting both as an
    exception would erase the distinction the readiness report exists to surface.
    """

    COVERED = "COVERED"
    HARD_COVERED = "HARD_COVERED"
    NEGATIVE_COVERED = "NEGATIVE_COVERED"
    CONDITIONAL = "CONDITIONAL"
    GAP = "GAP"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class ConstraintCoverage(Record):
    """The rule situation for one semantic path inside one bundle."""

    semantic_path: str
    state: str
    constraint_ids: tuple[str, ...] = ()
    inactive_ids: tuple[str, ...] = ()
    explanation: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path")
        )
        state = CoverageState.parse(self.state, "state")
        object.__setattr__(self, "state", state.value)
        object.__setattr__(self, "constraint_ids", _unique(self.constraint_ids, "constraint_ids"))
        object.__setattr__(
            self, "inactive_ids", _unique(self.inactive_ids, "inactive_ids")
        )
        overlap = sorted(set(self.constraint_ids) & set(self.inactive_ids))
        if overlap:
            raise SchemaValidationError(
                f"coverage of {self.semantic_path} lists {overlap} as both active and inactive"
            )
        if state is CoverageState.GAP and self.constraint_ids:
            raise SchemaValidationError(
                f"{self.semantic_path} is reported as a gap while {list(self.constraint_ids)} "
                "actively cover it"
            )
        if self.explanation is not None:
            object.__setattr__(
                self,
                "explanation",
                require_text(self.explanation, "explanation", maximum=MAX_RATIONALE_CHARS),
            )

    @property
    def state_enum(self) -> CoverageState:
        return CoverageState.parse(self.state)

    @property
    def covered(self) -> bool:
        return self.state_enum is not CoverageState.GAP

    def fingerprint_inputs(self) -> dict[str, Any]:
        return self.to_payload()


@dataclass(frozen=True)
class ConstraintViolationRef(Record):
    """A pointer to a violation M01 established, never an M03 verdict about one.

    M03 records that a rule was reported broken so the explanation graph can reach it; the
    judgement, the severity and the defect lifecycle stay in M01 (§5.19, §5.34). The
    distinction is enforced by requiring a decision ref: a violation with no upstream verdict
    is an M03 opinion, which is precisely the thing this module may not hold.
    """

    violation_id: str
    constraint_ref: SemanticRef
    decision_ref: SemanticRef
    severity: str
    observed: Mapping[str, str] = field(default_factory=dict)
    measure: str | None = None
    recorded_by: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "violation_id", require_identifier(self.violation_id, "violation_id")
        )
        constraint = SemanticRef.coerce(self.constraint_ref, "constraint_ref")
        if constraint.kind != RefKind.CONSTRAINT.value:
            raise SchemaValidationError(
                f"constraint_ref must reference {RefKind.CONSTRAINT.value}, got {constraint.kind}"
            )
        object.__setattr__(self, "constraint_ref", constraint)
        object.__setattr__(
            self,
            "decision_ref",
            require_bound_ref(self.decision_ref, "decision_ref", kind=RefKind.RECEIPT),
        )
        object.__setattr__(self, "severity", _m03_severity(self.severity, "severity"))
        object.__setattr__(self, "observed", bounded_metadata(self.observed, "observed"))
        if self.measure is not None:
            object.__setattr__(self, "measure", require_identifier(self.measure, "measure"))
        if self.recorded_by is not None:
            object.__setattr__(
                self, "recorded_by", require_identifier(self.recorded_by, "recorded_by")
            )


ConstraintViolationRef.NESTED = {"constraint_ref": of(SemanticRef), "decision_ref": of(SemanticRef)}


@dataclass(frozen=True)
class ConstraintBundle(Record):
    """An immutable, versioned set of rules admitted for one brief revision.

    Versioning the bundle rather than mutating it is what makes an override auditable: S05 can
    say "this decision used bundle v7", and if today's bundle had been edited in place, that
    sentence would no longer mean anything (§3, §5.3).

    The bundle is the admission point for predicates. A single constraint cannot check its
    predicate against the registry without knowing which registry the project is using, and a
    bundle that admitted rules without checking them would let an unknown mandatory predicate
    reach compilation, which §5.13 forbids.
    """

    bundle_id: str
    brief_id: str
    revision_id: str
    version: str
    constraints: tuple[Constraint, ...] = ()
    admitted_by: SemanticRef | None = None
    supersedes_bundle_id: str | None = None
    recorded_at: str | None = None
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", require_identifier(self.bundle_id, "bundle_id"))
        object.__setattr__(self, "brief_id", require_identifier(self.brief_id, "brief_id"))
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        object.__setattr__(self, "version", require_version_text(self.version, "version"))
        items = _seq(self.constraints, Constraint, "constraints", MAX_CONSTRAINTS_PER_BUNDLE)
        ids = [item.constraint_id for item in items]
        if len(set(ids)) != len(ids):
            raise SchemaValidationError(
                f"bundle {self.bundle_id} repeats constraint ids "
                f"{sorted({i for i in ids if ids.count(i) > 1})}; a duplicate id means two rules "
                "claim one identity, and an override could then relax the wrong one"
            )
        object.__setattr__(
            self, "constraints", tuple(sorted(items, key=lambda item: item.constraint_id))
        )
        if self.admitted_by is not None:
            object.__setattr__(
                self,
                "admitted_by",
                require_bound_ref(self.admitted_by, "admitted_by", kind=RefKind.REVISION),
            )
        if self.supersedes_bundle_id is not None:
            previous = require_identifier(self.supersedes_bundle_id, "supersedes_bundle_id")
            if previous == self.bundle_id:
                raise SchemaValidationError("a bundle cannot supersede itself")
            object.__setattr__(self, "supersedes_bundle_id", previous)
        if self.recorded_at is not None:
            object.__setattr__(
                self, "recorded_at", require_text(self.recorded_at, "recorded_at", maximum=64)
            )
        if self.notes is not None:
            reject_interpolation(self.notes, "notes")
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=MAX_TEXT_CHARS))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def is_admitted(self) -> bool:
        return self.admitted_by is not None

    @property
    def empty(self) -> bool:
        return not self.constraints

    @property
    def constraint_ids(self) -> tuple[str, ...]:
        return tuple(item.constraint_id for item in self.constraints)

    def by_id(self, constraint_id: str) -> Constraint:
        wanted = require_identifier(constraint_id, "constraint_id")
        for item in self.constraints:
            if item.constraint_id == wanted:
                return item
        raise SchemaValidationError(
            f"bundle {self.bundle_id} has no constraint {wanted}; naming a rule that is not in the "
            "admitted bundle is how a decision ends up justified by a rule nobody admitted"
        )

    def require_admitted(self, action: str) -> None:
        if not self.is_admitted:
            raise AdmissionRefusedError(
                f"{action} needs bundle {self.bundle_id} to be admitted, but nothing authorized it; "
                "an unadmitted rule set may be explored but may not drive compilation (§5.30)"
            )

    def admit(self, *, registry: PredicateRegistry, admitted_by: SemanticRef) -> "ConstraintBundle":
        """Check every rule against the admitted registry, then pin the bundle.

        Refusal is aggregate rather than first-failure on purpose: a reviewer fixing a
        constraint set wants the whole list of what is wrong, and the outcome is identical
        either way because nothing is admitted until all of it passes.
        """

        self.require_editable("admit")
        refusals: list[str] = []
        for item in self.constraints:
            try:
                require_known_predicate(
                    registry, item.predicate, polarity=item.polarity, owner=item.constraint_id
                )
            except (PredicateError, UntrustedExtensionError) as error:
                refusals.append(str(error))
        if refusals:
            raise AdmissionRefusedError(
                f"bundle {self.bundle_id} is not admissible: " + " | ".join(sorted(refusals))
            )
        return ConstraintBundle(
            **{
                **{
                    key: value
                    for key, value in self.to_payload().items()
                    if key != "admitted_by"
                },
                "admitted_by": SemanticRef.coerce(admitted_by, "admitted_by"),
            }
        )

    def require_editable(self, action: str) -> None:
        if self.is_admitted:
            raise RevisionFrozenError(
                f"cannot {action} bundle {self.bundle_id}: it was admitted by "
                f"{self.admitted_by.text}, and rewriting an admitted rule set would change what "
                "earlier compilations were based on (§5.3)"
            )

    def supersede(self, *, bundle_id: str, constraints: Iterable[Constraint], **changes: Any) -> "ConstraintBundle":
        """Return a new-version bundle, leaving this one untouched (§5.3)."""

        return ConstraintBundle(
            bundle_id=require_identifier(bundle_id, "bundle_id"),
            brief_id=self.brief_id,
            revision_id=str(changes.pop("revision_id", self.revision_id)),
            version=str(changes.pop("version", _next_version(self.version))),
            constraints=tuple(constraints),
            supersedes_bundle_id=self.bundle_id,
            **changes,
        )

    def active_for(self, context: Mapping[str, Any] | None = None) -> tuple[Constraint, ...]:
        return tuple(item for item in self.constraints if item.is_active(context))

    def hard_constraints(self) -> tuple[Constraint, ...]:
        return tuple(
            item for item in self.constraints if item.strength_enum is ConstraintStrength.HARD
        )

    def negative_constraints(self) -> tuple[Constraint, ...]:
        """Negative rules as a first-class set, because they are the easiest to lose.

        Translation layers keep a handle on prohibitions specifically so a check can be made
        after compilation that none of them disappeared (§5.15, §18).
        """

        return tuple(item for item in self.constraints if item.is_negative)

    def mandatory_constraints(self) -> tuple[Constraint, ...]:
        return tuple(item for item in self.constraints if item.mandatory)

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted({item.semantic_path for item in self.constraints}))

    def on_path(self, semantic_path: str) -> tuple[Constraint, ...]:
        path = require_semantic_path(semantic_path, "semantic_path")
        return tuple(
            item
            for item in self.constraints
            if _covered(path, item.semantic_path) or _covered(item.semantic_path, path)
        )

    def covering(self, context: Mapping[str, Any]) -> tuple[Constraint, ...]:
        return tuple(item for item in self.constraints if item.applies_to(context))

    def conflicts_with(self, other: "ConstraintBundle") -> tuple[tuple[str, str], ...]:
        """Deterministic pairs of directly contradicting rules across two bundles.

        Only a same-path, same-subject, opposite-polarity pair between rules of equal strength
        counts; otherwise a merge would "resolve" a hard project rule against a soft default
        that was never in competition with it (§11, §5.29).
        """

        if not isinstance(other, ConstraintBundle):
            raise SchemaValidationError("conflicts_with expects a ConstraintBundle")
        pairs: list[tuple[str, str]] = []
        for left in self.constraints:
            for right in other.constraints:
                if not left.binds(right):
                    continue
                if left.polarity == right.polarity:
                    continue
                if _contradicts(left, right):
                    pairs.append(tuple(sorted((left.constraint_id, right.constraint_id))))
        return tuple(sorted(set(pairs)))

    def coverage(self, paths: Iterable[str]) -> tuple[ConstraintCoverage, ...]:
        """Coverage states for the named paths, computed deterministically.

        A path whose only rules are inactive is reported as CONDITIONAL, not COVERED: the
        constraint exists but does not currently bind, and flattening that into "covered" is
        how a brief looks protected while nothing in it applies (§8).
        """

        wanted = _paths(paths, "paths")
        result: list[ConstraintCoverage] = []
        for path in wanted:
            active = [item for item in self.on_path(path) if item.is_active(None)]
            inactive = [item for item in self.on_path(path) if not item.is_active(None)]
            identifiers = tuple(item.constraint_id for item in active)
            inactive_ids = tuple(item.constraint_id for item in inactive)
            if not active and not inactive:
                state = CoverageState.GAP
            elif not active:
                state = CoverageState.CONDITIONAL
            elif any(item.strength_enum is ConstraintStrength.HARD for item in active):
                state = CoverageState.HARD_COVERED
            elif any(item.is_negative for item in active):
                state = CoverageState.NEGATIVE_COVERED
            elif inactive:
                state = CoverageState.CONDITIONAL
            else:
                state = CoverageState.COVERED
            result.append(
                ConstraintCoverage(
                    semantic_path=path,
                    state=state.value,
                    constraint_ids=identifiers,
                    inactive_ids=inactive_ids,
                )
            )
        return tuple(result)

    def fingerprint_inputs(self, *, context: Mapping[str, Any] | None = None) -> list[Any]:
        return [
            item.fingerprint_inputs()
            for item in sorted(self.active_for(context), key=lambda item: item.constraint_id)
        ]

    @property
    def bundle_ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.BUNDLE.value, ref_id=self.bundle_id, version=self.version
        ).with_digest(self.digest())

    def digest_of(self) -> str:
        return content_digest(self.fingerprint_inputs())


ConstraintBundle.NESTED = {
    "constraints": of(Constraint),
    "admitted_by": of(SemanticRef),
}


def _contradicts(left: Constraint, right: Constraint) -> bool:
    """Whether two bound rules truly cannot both be satisfied.

    REQUIRE against FORBID on one path is a contradiction. REQUIRE against AVOID is not: an
    avoidance is satisfiable by producing the required thing carefully, and calling it a
    contradiction would block work that the brief actually asked for while looking rigorous.
    ALLOW against REQUIRE/FORBID is a contradiction only when strengths differ in kind, which
    is what §5.29 leaves to S05 rather than settling here.
    """

    strict = {ConstraintPolarity.REQUIRE, ConstraintPolarity.FORBID}
    return (
        ConstraintPolarity.parse(left.polarity) in strict
        and ConstraintPolarity.parse(right.polarity) in strict
        and left.polarity != right.polarity
    )


def _next_version(version: str) -> str:
    text = require_version_text(version, "version")
    if text.startswith("v") and text[1:].isdigit():
        return f"v{int(text[1:]) + 1}"
    raise SchemaValidationError(
        f"cannot derive the next version from {text!r}; supersede with an explicit version instead"
    )


def _m03_severity(value: Any, field: str) -> str:
    """Read M01's severity ladder without handing out M01's exception class.

    The rung is M01's and stays M01's; the refusal is M03's, because a caller auditing an
    intent kernel has one error hierarchy to catch and one place to look for what was rejected.
    """

    try:
        return DefectSeverity.parse(value).value
    except Exception as error:  # noqa: BLE001 - the parser belongs to M01, whose hierarchy is not M03's
        raise SchemaValidationError(f"{field}: {error}") from error


def require_no_authority_in_scope(scope: ConstraintScope, owner: str) -> None:
    """Guard the boundary §5.14 draws: a scope says where, never who.

    Checked structurally rather than by convention, because the fields that would break it —
    ``authority``, ``granted_by`` — are the ones a reviewer would otherwise have to remember to
    look for in every scope literal, and the failure mode is invisible: a broad scope silently
    reading as a mandate.
    """

    if not isinstance(scope, ConstraintScope):
        raise SchemaValidationError("scope must be a ConstraintScope")
    leaked = sorted(
        name
        for name in vars(scope)
        if any(token in name.lower() for token in ("authority", "granted", "approved", "admitted"))
    )
    if leaked or scope.grants_authority:
        raise ScopeError(
            f"constraint {owner} carries authority fields {leaked} inside its scope; scope answers "
            "'which subjects', and putting authority there lets breadth impersonate permission (§5.14)"
        )


def require_representative_coverage(
    bundle: ConstraintBundle, paths: Iterable[str], *, subject: str
) -> tuple[ConstraintCoverage, ...]:
    """Return coverage, refusing to call a required path covered by nothing.

    Used by S03/S04 before compiling: a quality obligation with no constraint behind it is a
    gap, and one with a constraint that is currently inactive is also a gap for this run — but
    reported differently, because the first needs a rule and the second needs a context.
    """

    if not isinstance(bundle, ConstraintBundle):
        raise SchemaValidationError("coverage needs a ConstraintBundle")
    label = require_text(subject, "subject", maximum=128)
    coverage = bundle.coverage(paths)
    gaps = [item.semantic_path for item in coverage if item.state_enum is CoverageState.GAP]
    if gaps:
        raise AdmissionRefusedError(
            f"{label} has no constraint covering {sorted(gaps)}; compile a gap explicitly rather "
            "than emitting a contract that looks protected and is silent (§8, §5.22)"
        )
    return coverage


def _tokens(value: Any, name: str, limit: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{name} must be a list of tokens")
    if len(value) > limit:
        raise LimitExceededError(f"{name} holds {len(value)} entries, above the bound of {limit}")
    items = tuple(sorted({require_text(item, f"{name}[]", maximum=64).upper() for item in value}))
    if any(not _HYPHENATED.fullmatch(item) for item in items):
        raise SchemaValidationError(
            f"{name}[] must match ^[A-Z0-9][A-Z0-9._-]*$, got "
            f"{[item for item in items if not _HYPHENATED.fullmatch(item)]}"
        )
    return items


def _paths(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{name} must be a list of semantic paths")
    if len(value) > MAX_SCOPE_PATHS:
        raise LimitExceededError(f"{name} holds {len(value)} paths, above the bound of {MAX_SCOPE_PATHS}")
    return tuple(sorted({require_semantic_path(item, f"{name}[]") for item in value}))


def _unique(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{name} must be a list of identifiers")
    items = tuple(sorted({require_identifier(item, f"{name}[]") for item in value}))
    if len(items) > MAX_PROVENANCE_REFS:
        raise LimitExceededError(f"{name} holds {len(items)} entries, above {MAX_PROVENANCE_REFS}")
    return items


def _seq(value: Any, kind: type, name: str, limit: int) -> tuple[Any, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{name} must be a list of {kind.__name__}")
    if len(value) > limit:
        raise LimitExceededError(f"{name} holds {len(value)} entries, above the bound of {limit}")
    items = tuple(kind.coerce(item, f"{name}[]") for item in value)
    identifiers = [getattr(item, _identity_field(kind)) for item in items]
    if len(set(identifiers)) != len(identifiers):
        raise SchemaValidationError(
            f"{name} repeats an identity; two entries claiming one id make an override target "
            "ambiguous, and an ambiguous target is resolved by whoever reads it first"
        )
    return tuple(sorted(items, key=lambda item: getattr(item, _identity_field(kind))))


_IDENTITY_FIELDS: Mapping[type, str] = {
    Condition: "context_key",
    ToleranceEnvelope: "measure",
    AntiReference: "anti_ref_id",
    ProtectedAnchor: "anchor_id",
    CrossModalLink: "link_id",
    Constraint: "constraint_id",
}


def _identity_field(kind: type) -> str:
    try:
        return _IDENTITY_FIELDS[kind]
    except KeyError as error:
        raise SchemaValidationError(f"{kind.__name__} has no declared identity field") from error


_HYPHENATED = re.compile(r"^[A-Z0-9][A-Z0-9._-]*$")
