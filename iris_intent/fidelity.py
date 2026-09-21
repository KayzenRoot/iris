"""F-M03-08 M01 fidelity compilation bridge, and F-M03-09 the no-downgrade shield.

This module translates admitted M03 semantics into something M01 can judge. It is a bridge in
the strict sense: every quality object it emits is constructed by M01's own code, from an M01
:class:`~iris_quality.registry.DomainProfile`, and validated by M01's own serialization before
the compilation claims success. Nothing here re-implements a decision engine, an evaluator
registry, a defect taxonomy or a debt policy, because a second implementation of any of those
would be a second authority — and the two would disagree in whichever direction nobody noticed
first.

Three structural choices carry most of the safety:

*The spec has no evaluator field.* M03 cannot grant capability, so the concept is not
representable: the emitted contract's ``evaluator_set`` is whatever the selected profile
recommends, and M01's own ``EvaluatorRegistry.resolve()`` stays the authority boundary that
decides whether that set can judge the contract.

*The quality class arrives with its basis attached.* "Cinematic", "premium" and "amazing" are
production adjectives, not rungs, and a machine running short of VRAM is not a reason to lower a
target. So a class request is refused unless its basis is one a human or a governed policy
asserted (:class:`QualityClassBasis`), and resource scarcity has no code path into the class at
all (§24, ADR-0008).

*Unrepresentable requirements become gaps, never omissions.* When the selected profile cannot
carry an obligation, the compilation records which requirement it could not express and stops
being COMPLETE. Dropping the requirement would produce a contract that looks finished and judges
less than the brief asked for, which is the failure this whole module exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from iris_quality import errors as m01_errors
from iris_quality.contracts import DEFECT_CLASS_FIELDS, FidelityContract, QualityClass
from iris_quality.debt import QualityDebtPolicy
from iris_quality.defects import DefectSeverity
from iris_quality.registry import DomainProfile, EvaluatorRegistry
from iris_quality.serialization import envelope, from_envelope, validate_payload
from iris_quality.zones import SemanticZone

from .base import Labeled, Record, of
from .constraints import ConstraintStrength
from .errors import (
    AdmissionRefusedError,
    CapabilityGapError,
    QualityAuthorityError,
    SchemaValidationError,
    StaleSemanticError,
    UnsupportedVersionError,
)
from .freshness import BriefFreshnessVector, require_fresh
from .identity import AuthorityLevel, RefKind, SemanticRef, require_authority, require_bound_ref
from .intent import IntentAuthorityRef
from .limits import (
    MAX_CONTRACTS_PER_SET,
    MAX_DIMENSIONS_PER_SPEC,
    MAX_ENTRIES_PER_FIELD,
    MAX_OBLIGATION_TRACES,
    MAX_PROVENANCE_REFS,
)
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    M01_CONTRACT_VERSION,
    content_digest,
    require_contract_version,
    require_digest,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "COMPILER_VERSION",
    "M01_DEFAULT_DISAGREEMENT",
    "REJECTED_CLASS_BASES",
    "EvidenceClass",
    "FidelityCompilation",
    "FidelityCompilationFingerprint",
    "FidelityCompilationGap",
    "FidelityCompilationStatus",
    "FidelityContractMember",
    "FidelityContractSetRef",
    "FidelityContractSpec",
    "GapClass",
    "QualityChangeClass",
    "QualityClassBasis",
    "QualityClassRequest",
    "QualityContractDelta",
    "QualityIntentProjection",
    "QualityObligationKind",
    "QualityObligationTrace",
    "ReferenceRequest",
    "ReferenceRole",
    "ZoneRequest",
    "compile_fidelity_contract",
    "dimensions_for",
    "quality_contract_delta",
    "require_compilable",
    "require_no_downgrade",
]

#: Versioned identity of this compiler. Recorded in every fingerprint so a contract compiled by
#: an older bridge stays distinguishable from one compiled by this one, forever.
COMPILER_VERSION = "m03-fidelity-compiler-v1"

#: M01's own default, restated here only so the bridge can tell "the brief said nothing about
#: disagreement" from "the brief asked for this number". The value is not M03's to choose, so a
#: spec carrying ``None`` hands this one to ``DomainProfile.instantiate`` and M01 keeps ownership.
M01_DEFAULT_DISAGREEMENT = 0.35


class QualityObligationKind(Labeled):
    """What the production requires to be true, in M03's own words.

    This is deliberately *not* M01's dimension vocabulary. Compilation maps each obligation onto
    dimensions the selected profile actually admits; keeping a separate name for the requirement
    is what lets the compiler say "this brief needs voice-identity and nothing here can judge it"
    instead of silently forgetting the requirement (§6, D-M03-S03-004).
    """

    INTENT_ADHERENCE = "INTENT_ADHERENCE"
    IDENTITY_FIDELITY = "IDENTITY_FIDELITY"
    ANATOMY = "ANATOMY"
    GEOMETRY = "GEOMETRY"
    SILHOUETTE_READ = "SILHOUETTE_READ"
    COMPOSITION = "COMPOSITION"
    MATERIAL = "MATERIAL"
    TEXTURE = "TEXTURE"
    LIGHTING = "LIGHTING"
    COLOR = "COLOR"
    STYLE_BRAND = "STYLE_BRAND"
    MOTION = "MOTION"
    TEMPORAL = "TEMPORAL"
    VFX = "VFX"
    TECHNICAL = "TECHNICAL"
    PLATFORM_FIT = "PLATFORM_FIT"
    CROSS_MODAL = "CROSS_MODAL"
    PERCEPTUAL_FINISH = "PERCEPTUAL_FINISH"
    VOICE_IDENTITY = "VOICE_IDENTITY"
    TEXT_LEGIBILITY = "TEXT_LEGIBILITY"


#: Obligation -> candidate M01 dimension ids, tried in order. Only ids M01 already knows appear
#: on the canonical side; ``voice-identity`` and ``text-legibility`` are extension ids that exist
#: only in a registry which has admitted them, which is the §6 example made executable.
_OBLIGATION_DIMENSIONS: Mapping[QualityObligationKind, tuple[str, ...]] = {
    QualityObligationKind.INTENT_ADHERENCE: ("intent-adherence",),
    QualityObligationKind.IDENTITY_FIDELITY: ("identity-fidelity",),
    QualityObligationKind.ANATOMY: ("anatomy-plausibility",),
    QualityObligationKind.GEOMETRY: ("geometry-integrity",),
    QualityObligationKind.SILHOUETTE_READ: ("silhouette-readability",),
    QualityObligationKind.COMPOSITION: ("composition-framing",),
    QualityObligationKind.MATERIAL: ("material-pbr-fidelity",),
    QualityObligationKind.TEXTURE: ("texture-detail-fidelity",),
    QualityObligationKind.LIGHTING: ("lighting-shadow-fidelity",),
    QualityObligationKind.COLOR: ("color-value-hierarchy",),
    QualityObligationKind.STYLE_BRAND: ("style-brand-consistency",),
    QualityObligationKind.MOTION: ("motion-deformation-quality",),
    QualityObligationKind.TEMPORAL: ("temporal-continuity",),
    QualityObligationKind.VFX: ("vfx-clarity-integration",),
    QualityObligationKind.TECHNICAL: ("technical-integrity",),
    QualityObligationKind.PLATFORM_FIT: ("target-platform-fitness",),
    QualityObligationKind.CROSS_MODAL: ("cross-modal-consistency",),
    QualityObligationKind.PERCEPTUAL_FINISH: ("perceptual-finish",),
    QualityObligationKind.VOICE_IDENTITY: ("voice-identity",),
    QualityObligationKind.TEXT_LEGIBILITY: ("text-legibility", "silhouette-readability"),
}


def dimensions_for(obligation: Any) -> tuple[str, ...]:
    """The candidate dimension ids M03 may ask for, given an obligation."""

    kind = QualityObligationKind.parse(obligation, "obligation")
    return _OBLIGATION_DIMENSIONS[kind]


class QualityClassBasis(Labeled):
    """Why this quality rung, of the reasons M03 is allowed to accept.

    The rejected spellings live in :data:`REJECTED_CLASS_BASES` so the refusal names what was
    attempted. Adjectives and scarcity are refused not because they are weak evidence but because
    they are evidence about something else: how a brief *sounds*, or what a machine can do in one
    pass. Neither is a statement about what the deliverable must be (§5, §24).
    """

    EXPLICIT_HUMAN = "EXPLICIT_HUMAN"
    PROJECT_POLICY = "PROJECT_POLICY"
    DELIVERY_POLICY = "DELIVERY_POLICY"
    PROFILE_RULE = "PROFILE_RULE"


REJECTED_CLASS_BASES = frozenset(
    {
        "ADJECTIVE_TEXT",
        "CINEMATIC_TEXT",
        "PREMIUM_TEXT",
        "MODEL_RECOMMENDATION",
        "PROVIDER_CAPABILITY",
        "HARDWARE_CONSTRAINT",
        "VRAM_CONSTRAINT",
        "COST_TARGET",
        "SCHEDULE_PRESSURE",
        "CONFIDENCE_SCORE",
    }
)


class ReferenceRole(Labeled):
    """What a reference is *for*, which decides whether it binds.

    ``INSPIRATION`` is the one non-strict role. A mood board that arrived as a must-match artifact
    would make every derivative work a defect, so the role — not the file type, not the folder —
    decides whether the reference reaches the M01 contract (§11, D-M03-S03-009).
    """

    IDENTITY_ANCHOR = "IDENTITY_ANCHOR"
    MUST_MATCH = "MUST_MATCH"
    APPROVED_BRAND = "APPROVED_BRAND"
    STRUCTURAL_TARGET = "STRUCTURAL_TARGET"
    QUALITY_BASELINE = "QUALITY_BASELINE"
    ANTI_REFERENCE_EVIDENCE = "ANTI_REFERENCE_EVIDENCE"
    INSPIRATION = "INSPIRATION"

    @property
    def strict(self) -> bool:
        return self is not ReferenceRole.INSPIRATION


class EvidenceClass(Labeled):
    """The kind of proof an obligation will need, stated without pretending it exists.

    ``HUMAN_DECISION`` names the obligation only. M03 has no type for a human verdict and never
    constructs one; producing the obligation and satisfying it are separated by module boundary
    on purpose (§14, D-M03-S03-012).
    """

    AUTOMATED_EVALUATOR = "AUTOMATED_EVALUATOR"
    DETERMINISTIC_VALIDATOR = "DETERMINISTIC_VALIDATOR"
    HUMAN_DECISION = "HUMAN_DECISION"


class FidelityCompilationStatus(Labeled):
    """Whether a compilation may be treated as a finished contract.

    ``BLOCKED`` means the inputs themselves are not sound enough to produce a specification;
    ``INCOMPLETE`` means the specification exists but no contract may be emitted from it. There
    is no "ready with caveats" state, because that is the state a reviewer reads as ready.
    """

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"

    @property
    def may_emit(self) -> bool:
        return self is FidelityCompilationStatus.COMPLETE

    @property
    def has_specification(self) -> bool:
        return self is not FidelityCompilationStatus.BLOCKED


class GapClass(Labeled):
    """The §17 gap vocabulary, exactly.

    Each member says which requirement could not be expressed and what would have to change. A
    gap is never repaired inside the compiler: the point of naming it is that the fix belongs to
    somebody else — a profile owner, a registry extension, a policy decision, a clarification.
    """

    MISSING_DOMAIN_PROFILE = "MISSING_DOMAIN_PROFILE"
    MISSING_DIMENSION = "MISSING_DIMENSION"
    MISSING_EVALUATOR_CAPABILITY = "MISSING_EVALUATOR_CAPABILITY"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
    UNSUPPORTED_QUALITY_CLASS = "UNSUPPORTED_QUALITY_CLASS"
    UNREPRESENTABLE_CONSTRAINT = "UNREPRESENTABLE_CONSTRAINT"
    PROFILE_POLICY_CONFLICT = "PROFILE_POLICY_CONFLICT"
    REGISTRY_VERSION_MISMATCH = "REGISTRY_VERSION_MISMATCH"
    BLOCKING_AMBIGUITY = "BLOCKING_AMBIGUITY"
    STALE_COMPILATION_INPUT = "STALE_COMPILATION_INPUT"

    @property
    def forbids_specification(self) -> bool:
        """Whether this gap makes even a specification unsound.

        The inputs in question — which profile was selected, whether the registry is the pinned
        one, whether the source revision still holds, whether a blocking ambiguity is open — are
        all preconditions of *describing* the contract, not just of emitting it.
        """

        return self in {
            GapClass.MISSING_DOMAIN_PROFILE,
            GapClass.REGISTRY_VERSION_MISMATCH,
            GapClass.BLOCKING_AMBIGUITY,
            GapClass.STALE_COMPILATION_INPUT,
            GapClass.PROFILE_POLICY_CONFLICT,
        }


class QualityChangeClass(Labeled):
    """How an emitted contract's obligations moved, as a class M02 can act on.

    M03 supplies the classification and M02 decides what to rebuild (§20). The distinction
    matters: ``NO_SEMANTIC_CHANGE`` on a brief edit that only reworded a rationale is information
    M02 should receive, not a reason to recompile — but the rebuild choice is not M03's to make.
    """

    NO_SEMANTIC_CHANGE = "NO_SEMANTIC_CHANGE"
    REFERENCE_CHANGE = "REFERENCE_CHANGE"
    DIMENSION_OBLIGATION_CHANGE = "DIMENSION_OBLIGATION_CHANGE"
    QUALITY_CLASS_CHANGE = "QUALITY_CLASS_CHANGE"
    ZONE_CHANGE = "ZONE_CHANGE"
    DELIVERY_PROFILE_CHANGE = "DELIVERY_PROFILE_CHANGE"
    POLICY_CHANGE = "POLICY_CHANGE"
    PROFILE_CHANGE = "PROFILE_CHANGE"
    REGISTRY_CHANGE = "REGISTRY_CHANGE"

    @property
    def changes_obligations(self) -> bool:
        return self not in {QualityChangeClass.NO_SEMANTIC_CHANGE}

    @property
    def invalidates_contract(self) -> bool:
        """Whether the previous contract still states the requirement.

        Only a delivery-profile move keeps the same obligations on a different target; every
        other class changes what has to be proven.
        """

        return self is not QualityChangeClass.NO_SEMANTIC_CHANGE


@dataclass(frozen=True)
class FidelityCompilationGap(Record):
    """One requirement this compilation could not express, pointing at the requirement.

    ``source_refs`` are required because §17's promise is that no gap is repaired by dropping the
    originating requirement — and a gap that cannot name its source is indistinguishable from a
    requirement that was quietly forgotten.
    """

    gap_id: str
    class_name: str
    detail: str
    source_refs: tuple[SemanticRef, ...] = ()
    semantic_path: str | None = None
    obligation: str | None = None
    missing_dimension_id: str | None = None
    mandatory_origin: bool = True
    remedy: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_id", require_identifier(self.gap_id, "gap_id"))
        kind = GapClass.parse(self.class_name, "class_name")
        object.__setattr__(self, "class_name", kind.value)
        refs = tuple(
            sorted(
                (SemanticRef.coerce(item, "source_refs[]") for item in (self.source_refs or ())),
                key=lambda item: item.text,
            )
        )
        if not refs:
            raise SchemaValidationError(
                f"gap {self.gap_id} names no source; a gap with no originating requirement is how "
                "§17's silent drop would be written"
            )
        if len(refs) > MAX_PROVENANCE_REFS:
            raise SchemaValidationError(
                f"gap {self.gap_id} cites {len(refs)} sources, above {MAX_PROVENANCE_REFS}"
            )
        object.__setattr__(self, "source_refs", refs)
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=1024))
        if self.semantic_path is not None:
            object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        if self.obligation is not None:
            object.__setattr__(
                self, "obligation", QualityObligationKind.parse(self.obligation, "obligation").value
            )
        if self.missing_dimension_id is not None:
            object.__setattr__(
                self, "missing_dimension_id", require_identifier(self.missing_dimension_id, "missing_dimension_id")
            )
        if kind is GapClass.MISSING_DIMENSION and self.missing_dimension_id is None:
            raise SchemaValidationError(
                f"gap {self.gap_id} reports a missing dimension without naming it; 'some dimension "
                "is absent' cannot be handed to a registry owner as a work item"
            )
        if not isinstance(self.mandatory_origin, bool):
            raise SchemaValidationError("mandatory_origin must be a boolean")
        if self.remedy is not None:
            object.__setattr__(self, "remedy", require_text(self.remedy, "remedy", maximum=512))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def class_enum(self) -> GapClass:
        return GapClass.parse(self.class_name)

    @property
    def blocks_completion(self) -> bool:
        """Only a non-mandatory requirement may leave the compilation COMPLETE.

        A soft preference the profile cannot judge is reported and carried; a mandatory one stops
        the compilation. Both are gaps either way, so nothing is lost — the difference is whether
        the brief's own strength lets the work proceed.
        """

        return self.mandatory_origin

    @property
    def forbids_specification(self) -> bool:
        return self.class_enum.forbids_specification

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "class": self.class_name,
            "obligation": self.obligation,
            "missing_dimension_id": self.missing_dimension_id,
            "mandatory": self.mandatory_origin,
            "sources": sorted(item.text for item in self.source_refs),
        }


FidelityCompilationGap.NESTED = {"source_refs": of(SemanticRef)}


@dataclass(frozen=True)
class QualityClassRequest(Record):
    """A quality rung together with the reason M03 is allowed to accept it.

    The basis travels with the class because the same string ``MASTER`` means different things
    depending on where it came from: from a human owner it is a target, from a provider's
    capability list it is a downgrade in disguise. Stripping the basis is what would make the
    two indistinguishable after one hop through a payload.
    """

    requested_class: str
    basis: str
    authority: IntentAuthorityRef
    policy_ref: SemanticRef | None = None
    rationale: str | None = None
    receipt_ref: SemanticRef | None = None
    contract_version: str = ""

    #: §24 as structure: nothing about this record can carry a resource limit.
    scarcity_can_change_class = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_class", QualityClass.parse(self.requested_class))
        basis = _parse_basis(self.basis)
        object.__setattr__(self, "basis", basis.value)
        object.__setattr__(self, "authority", IntentAuthorityRef.coerce(self.authority, "authority"))
        floor = {
            QualityClassBasis.EXPLICIT_HUMAN: AuthorityLevel.HUMAN_OWNER,
            QualityClassBasis.PROJECT_POLICY: AuthorityLevel.GOVERNED_POLICY,
            QualityClassBasis.DELIVERY_POLICY: AuthorityLevel.GOVERNED_POLICY,
            QualityClassBasis.PROFILE_RULE: AuthorityLevel.PROJECT_RECORD,
        }[basis]
        require_authority(
            self.authority.level, "authority", minimum=floor
        )
        for name in ("policy_ref", "receipt_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        if basis in {QualityClassBasis.PROJECT_POLICY, QualityClassBasis.DELIVERY_POLICY} and self.policy_ref is None:
            raise QualityAuthorityError(
                f"a {basis.value} quality target must cite the policy that set it; otherwise the "
                "record says a rule was followed without naming which, and no later reviewer can "
                "check that it still exists"
            )
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=1024))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def class_enum(self) -> QualityClass:
        return QualityClass.parse(self.requested_class)

    @property
    def basis_enum(self) -> QualityClassBasis:
        return QualityClassBasis.parse(self.basis)

    @property
    def rung(self) -> int:
        return self.class_enum.ladder_rank

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "requested_class": self.class_enum.value,
            "basis": self.basis,
            "authority": self.authority.level.value,
            "policy_ref": self.policy_ref.text if self.policy_ref else None,
        }


QualityClassRequest.NESTED = {
    "authority": of(IntentAuthorityRef),
    "policy_ref": of(SemanticRef),
    "receipt_ref": of(SemanticRef),
}


@dataclass(frozen=True)
class QualityIntentProjection(Record):
    """One admitted requirement, stated as a quality obligation (§3.1).

    Projections are provider-neutral by construction: there is no field here for a model, a
    workflow or a DCC name. If provider vocabulary is needed, it belongs to S04's execution
    intent, and a quality contract that mentions a provider is a contract that cannot outlive it.
    """

    projection_id: str
    obligation: str
    semantic_path: str
    mandatory: bool = True
    statement_ids: tuple[str, ...] = ()
    constraint_ids: tuple[str, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    destination_refs: tuple[SemanticRef, ...] = ()
    anchor_refs: tuple[SemanticRef, ...] = ()
    requested_dimensions: tuple[str, ...] = ()
    human_review_reason: str | None = None
    strength: str | None = None
    rationale: str | None = None
    notes: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "projection_id", require_identifier(self.projection_id, "projection_id"))
        kind = QualityObligationKind.parse(self.obligation, "obligation")
        object.__setattr__(self, "obligation", kind.value)
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        if not isinstance(self.mandatory, bool):
            raise SchemaValidationError("mandatory must be a boolean")
        object.__setattr__(self, "statement_ids", _ids(self.statement_ids, "statement_ids"))
        object.__setattr__(self, "constraint_ids", _ids(self.constraint_ids, "constraint_ids"))
        for name in ("policy_refs", "destination_refs", "anchor_refs"):
            object.__setattr__(self, name, _refs(getattr(self, name), name))
        if not (self.statement_ids or self.constraint_ids or self.policy_refs):
            raise SchemaValidationError(
                f"projection {self.projection_id} cites no statement, constraint or policy; an "
                "obligation nobody can trace to a decision is an invention by the compiler"
            )
        dimensions = _dimensions(self.requested_dimensions) or dimensions_for(kind)
        object.__setattr__(self, "requested_dimensions", dimensions)
        if self.strength is None:
            object.__setattr__(self, "strength", "HARD" if self.mandatory else "SOFT")
        object.__setattr__(
            self, "strength", ConstraintStrength.parse(self.strength, "strength").value
        )
        if self.human_review_reason is not None:
            object.__setattr__(
                self, "human_review_reason", require_text(self.human_review_reason, "human_review_reason", maximum=512)
            )
        for name in ("rationale", "notes"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_text(value, name, maximum=1024))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def obligation_enum(self) -> QualityObligationKind:
        return QualityObligationKind.parse(self.obligation)

    @property
    def source_refs(self) -> tuple[SemanticRef, ...]:
        out = [
            SemanticRef(kind=RefKind.STATEMENT.value, ref_id=item) for item in self.statement_ids
        ] + [
            SemanticRef(kind=RefKind.CONSTRAINT.value, ref_id=item) for item in self.constraint_ids
        ] + list(self.policy_refs)
        return tuple(sorted(out, key=lambda item: item.text))

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "obligation": self.obligation,
            "semantic_path": self.semantic_path,
            "mandatory": self.mandatory,
            "requested_dimensions": list(self.requested_dimensions),
            "statements": list(self.statement_ids),
            "constraints": list(self.constraint_ids),
            "policies": sorted(item.text for item in self.policy_refs),
            "destinations": sorted(item.text for item in self.destination_refs),
            "anchors": sorted(item.text for item in self.anchor_refs),
            "human_review": self.human_review_reason is not None,
        }


QualityIntentProjection.NESTED = {
    "policy_refs": of(SemanticRef),
    "destination_refs": of(SemanticRef),
    "anchor_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class ReferenceRequest(Record):
    """A reference and the role it plays, which is the only thing deciding whether it binds."""

    ref_id: str
    role: str
    semantic_path: str | None = None
    resolved: bool = True
    source_ref: SemanticRef | None = None
    notes: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref_id", require_identifier(self.ref_id, "ref_id"))
        role = ReferenceRole.parse(self.role, "role")
        object.__setattr__(self, "role", role.value)
        if self.semantic_path is not None:
            object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        if not isinstance(self.resolved, bool):
            raise SchemaValidationError("resolved must be a boolean")
        if self.source_ref is not None:
            object.__setattr__(self, "source_ref", SemanticRef.coerce(self.source_ref, "source_ref"))
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=512))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def role_enum(self) -> ReferenceRole:
        return ReferenceRole.parse(self.role)

    @property
    def strict(self) -> bool:
        return self.role_enum.strict

    @property
    def blocking(self) -> bool:
        """An unresolved strict reference stops emission; an unresolved mood does not.

        §11's distinction, as a predicate: a general inspiration image is not a fidelity
        requirement, so its absence cannot be a defect in the contract either.
        """

        return self.strict and not self.resolved


@dataclass(frozen=True)
class ZoneRequest(Record):
    """A semantic region to protect or emphasise, with no geometry whatsoever (§12).

    M03 says "the face and the logo clear-space matter more"; M04 and the domain modules decide
    where that is on a frame. A request that carried pixel data would be M03 owning something it
    cannot validate and M04 cannot regenerate.
    """

    zone_id: str
    label: str
    dimension_ids: tuple[str, ...]
    minimum_confidence: float | None = None
    severity_overrides: Mapping[str, str] = field(default_factory=dict)
    projection_id: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "zone_id", require_identifier(self.zone_id, "zone_id"))
        object.__setattr__(self, "label", require_text(self.label, "label", maximum=120))
        dimensions = tuple(sorted({require_identifier(item, "dimension_ids[]") for item in (self.dimension_ids or ())}))
        if not dimensions:
            raise SchemaValidationError(
                f"zone {self.zone_id} binds no dimension; a zone over nothing would be recorded "
                "and then judged as if it protected something"
            )
        if len(dimensions) > MAX_DIMENSIONS_PER_SPEC:
            raise SchemaValidationError(f"zone {self.zone_id} binds {len(dimensions)} dimensions")
        object.__setattr__(self, "dimension_ids", dimensions)
        if self.minimum_confidence is not None:
            value = float(self.minimum_confidence)
            if not 0.0 <= value <= 1.0:
                raise SchemaValidationError("minimum_confidence must be within [0, 1]")
            object.__setattr__(self, "minimum_confidence", value)
        overrides: dict[str, str] = {}
        for key, item in sorted(dict(self.severity_overrides or {}).items()):
            overrides[require_identifier(key, "severity_overrides key")] = DefectSeverity.parse(item).value
        object.__setattr__(self, "severity_overrides", overrides)
        if self.projection_id is not None:
            object.__setattr__(self, "projection_id", require_identifier(self.projection_id, "projection_id"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    def to_m01(self) -> SemanticZone:
        """Materialise as M01's own zone record, with M01's own validation.

        Only ever called with severities already checked against the profile, because a zone is
        allowed to raise what a defect costs and never to lower it.
        """

        return SemanticZone(
            zone_id=self.zone_id,
            label=self.label,
            dimension_ids=self.dimension_ids,
            severity_overrides={
                key: DefectSeverity.parse(value) for key, value in self.severity_overrides.items()
            },
            minimum_confidence=self.minimum_confidence,
        )


@dataclass(frozen=True)
class QualityObligationTrace(Record):
    """One link of ``source -> obligation -> dimension/rule -> evidence`` (§10).

    Every emitted dimension needs a trace, including the ones that came from the profile rather
    than from the brief. A dimension with no trace is a dimension nobody can explain, and "why are
    we judging this?" has to have a deterministic answer for every axis in the contract —
    including the axes the client never mentioned.
    """

    trace_id: str
    semantic_path: str | None
    obligation: str | None = None
    projection_id: str | None = None
    requested_dimension_ids: tuple[str, ...] = ()
    dimension_ids: tuple[str, ...] = ()
    statement_ids: tuple[str, ...] = ()
    constraint_ids: tuple[str, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    destination_refs: tuple[SemanticRef, ...] = ()
    reference_ids: tuple[str, ...] = ()
    zone_ids: tuple[str, ...] = ()
    promotion_targets: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    human_review_required: bool = False
    covered: bool = True
    gap_id: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace_id", require_identifier(self.trace_id, "trace_id"))
        if self.semantic_path is not None:
            object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        if self.obligation is not None:
            object.__setattr__(self, "obligation", QualityObligationKind.parse(self.obligation, "obligation").value)
        for name in ("projection_id", "gap_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_identifier(value, name))
        for name in ("requested_dimension_ids", "dimension_ids", "statement_ids", "constraint_ids", "reference_ids", "zone_ids"):
            object.__setattr__(self, name, _ids(getattr(self, name), name))
        for name in ("policy_refs", "destination_refs"):
            object.__setattr__(self, name, _refs(getattr(self, name), name))
        targets = tuple(
            sorted({QualityClass.parse(item).value for item in (self.promotion_targets or ())})
        )
        object.__setattr__(self, "promotion_targets", targets)
        evidence = tuple(
            sorted({EvidenceClass.parse(item, "evidence_requirements[]").value for item in (self.evidence_requirements or ())})
        )
        if self.covered and not evidence:
            raise SchemaValidationError(
                f"trace {self.trace_id} says an obligation is judged but names no evidence class; a "
                "dimension with no proof requirement is a checkbox nobody will tick"
            )
        object.__setattr__(self, "evidence_requirements", evidence)
        if not isinstance(self.human_review_required, bool):
            raise SchemaValidationError("human_review_required must be a boolean")
        if self.human_review_required and EvidenceClass.HUMAN_DECISION.value not in evidence:
            raise SchemaValidationError(
                f"trace {self.trace_id} requires human review without a HUMAN_DECISION evidence "
                "obligation; §14 compiles the requirement, it does not invent the answer"
            )
        if not isinstance(self.covered, bool):
            raise SchemaValidationError("covered must be a boolean")
        if self.covered and not self.dimension_ids:
            raise SchemaValidationError(
                f"trace {self.trace_id} claims coverage with no admitted dimension bound"
            )
        if self.covered and not (self.statement_ids or self.constraint_ids or self.policy_refs):
            raise SchemaValidationError(
                f"trace {self.trace_id} binds a dimension to nothing; every judged axis needs an "
                "explanation path back to a source decision or to the selected profile (§10)"
            )
        if not self.covered:
            if self.dimension_ids:
                raise SchemaValidationError(
                    f"trace {self.trace_id} reports itself uncovered while binding dimensions"
                )
            if self.gap_id is None:
                raise SchemaValidationError(
                    f"trace {self.trace_id} could not be represented and names no gap; that is the "
                    "silent drop §17 forbids"
                )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def sources(self) -> tuple[str, ...]:
        out = [f"statement:{item}" for item in self.statement_ids]
        out += [f"constraint:{item}" for item in self.constraint_ids]
        out += [item.text for item in self.policy_refs]
        return tuple(sorted(out))

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "obligation": self.obligation,
            "path": self.semantic_path,
            "dimensions": list(self.dimension_ids),
            "sources": list(self.sources),
            "covered": self.covered,
            "evidence": list(self.evidence_requirements),
            "human_review": self.human_review_required,
        }


QualityObligationTrace.NESTED = {"policy_refs": of(SemanticRef), "destination_refs": of(SemanticRef)}


@dataclass(frozen=True)
class FidelityContractSpec(Record):
    """The compiler-owned request for one M01 contract (§3.2).

    Look for the evaluator field and there is not one. That absence is the evaluator firewall
    (D-M03-S03-006) expressed as a schema: a spec that cannot name an evaluator cannot grant
    capability, and the only way capability enters the emitted contract is through the profile
    M01 itself admitted. The spec also cannot be submitted to a decision engine — M01's types do
    not accept it, which is the point rather than a limitation.
    """

    compilation_id: str
    subject_ref: SemanticRef
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    model_fingerprint_digest: str
    constraint_fingerprint_digest: str
    m01_contract_version: str
    profile_ref: SemanticRef
    dimension_registry_version: str
    class_request: QualityClassRequest
    intent_summary: str
    projections: tuple[QualityIntentProjection, ...] = ()
    traces: tuple[QualityObligationTrace, ...] = ()
    gaps: tuple[FidelityCompilationGap, ...] = ()
    reference_ids: tuple[str, ...] = ()
    inspiration_ref_ids: tuple[str, ...] = ()
    zone_requests: tuple[ZoneRequest, ...] = ()
    human_review_dimension_ids: tuple[str, ...] = ()
    debt_policy_ref: SemanticRef | None = None
    policy_refs: tuple[SemanticRef, ...] = ()
    destination_ref: SemanticRef | None = None
    target_platform: str = "unspecified"
    camera_profile: str = "unspecified"
    delivery_profile: str = "unspecified"
    max_judge_disagreement: float | None = None
    compiler_version: str = COMPILER_VERSION
    contract_version: str = ""

    #: §3.2: this record is not an M01 contract and has no decision authority.
    is_m01_contract = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "compilation_id", require_identifier(self.compilation_id, "compilation_id"))
        object.__setattr__(self, "subject_ref", SemanticRef.coerce(self.subject_ref, "subject_ref"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self, "revision_ref", require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION)
        )
        for name in ("model_fingerprint_digest", "constraint_fingerprint_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        object.__setattr__(
            self,
            "m01_contract_version",
            _require_m01_contract_version(self.m01_contract_version),
        )
        profile_ref = require_bound_ref(self.profile_ref, "profile_ref", kind=RefKind.M01_DOMAIN_PROFILE)
        if profile_ref.version is None:
            raise SchemaValidationError(
                f"profile ref {profile_ref.text} is not version-pinned; §18 requires the selected "
                "profile to be version-pinned, or a later compilation cannot tell which profile it "
                "inherited requirements from"
            )
        object.__setattr__(self, "profile_ref", profile_ref)
        object.__setattr__(
            self, "dimension_registry_version", require_version_text(self.dimension_registry_version, "dimension_registry_version")
        )
        object.__setattr__(self, "class_request", QualityClassRequest.coerce(self.class_request, "class_request"))
        object.__setattr__(
            self, "intent_summary", require_text(self.intent_summary, "intent_summary", maximum=1024)
        )
        projections = tuple(
            sorted(
                (QualityIntentProjection.coerce(item, "projections[]") for item in (self.projections or ())),
                key=lambda item: item.projection_id,
            )
        )
        if len({item.projection_id for item in projections}) != len(projections):
            raise SchemaValidationError(f"spec {self.compilation_id} repeats a projection id")
        object.__setattr__(self, "projections", projections)
        traces = tuple(
            sorted(
                (QualityObligationTrace.coerce(item, "traces[]") for item in (self.traces or ())),
                key=lambda item: item.trace_id,
            )
        )
        if len(traces) > MAX_OBLIGATION_TRACES:
            raise SchemaValidationError(
                f"spec {self.compilation_id} holds {len(traces)} traces, above {MAX_OBLIGATION_TRACES}"
            )
        object.__setattr__(self, "traces", traces)
        gaps = tuple(
            sorted(
                (FidelityCompilationGap.coerce(item, "gaps[]") for item in (self.gaps or ())),
                key=lambda item: (item.class_name, item.gap_id),
            )
        )
        object.__setattr__(self, "gaps", gaps)
        object.__setattr__(self, "reference_ids", _ids(self.reference_ids, "reference_ids"))
        object.__setattr__(self, "inspiration_ref_ids", _ids(self.inspiration_ref_ids, "inspiration_ref_ids"))
        overlap = sorted(set(self.reference_ids) & set(self.inspiration_ref_ids))
        if overlap:
            raise SchemaValidationError(
                f"spec {self.compilation_id} lists {overlap} as both strict and inspirational; one "
                "reference cannot both bind the contract and be allowed to drift"
            )
        zones = tuple(
            sorted(
                (ZoneRequest.coerce(item, "zone_requests[]") for item in (self.zone_requests or ())),
                key=lambda item: item.zone_id,
            )
        )
        if len({item.zone_id for item in zones}) != len(zones):
            raise SchemaValidationError(f"spec {self.compilation_id} repeats a zone id")
        judged = self._judged_dimensions
        outside = sorted({item for zone in zones for item in zone.dimension_ids} - judged)
        if outside:
            raise SchemaValidationError(
                f"spec {self.compilation_id} binds zones to dimensions it does not judge: {outside}; "
                "§12 allows emphasis only over admitted contract dimensions (D-M03-S03-010)"
            )
        object.__setattr__(self, "zone_requests", zones)
        review = _ids(self.human_review_dimension_ids, "human_review_dimension_ids")
        stray = sorted(set(review) - judged)
        if stray:
            raise SchemaValidationError(
                f"spec {self.compilation_id} requests human review for unjudged dimensions {stray}"
            )
        object.__setattr__(self, "human_review_dimension_ids", review)
        for name in ("debt_policy_ref", "destination_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        object.__setattr__(self, "policy_refs", _refs(self.policy_refs, "policy_refs"))
        for name in ("target_platform", "camera_profile", "delivery_profile"):
            object.__setattr__(self, name, require_text(getattr(self, name), name, maximum=120))
        if self.max_judge_disagreement is not None:
            value = float(self.max_judge_disagreement)
            if not 0.0 <= value <= 1.0:
                raise SchemaValidationError("max_judge_disagreement must be within [0, 1]")
            if self.debt_policy_ref is None and not self.policy_refs:
                raise SchemaValidationError(
                    f"spec {self.compilation_id} sets max_judge_disagreement with no policy source; "
                    "§16 requires the exact profile or policy a non-default setting came from, "
                    "because an unattributed threshold is a judgement nobody owns"
                )
            object.__setattr__(self, "max_judge_disagreement", value)
        object.__setattr__(self, "compiler_version", require_version_text(self.compiler_version, "compiler_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )
        _check_trace_coverage(self)

    @property
    def _judged_dimensions(self) -> frozenset[str]:
        return frozenset(
            {dimension for trace in self.traces for dimension in trace.dimension_ids}
        )

    @property
    def requested_class(self) -> QualityClass:
        return self.class_request.class_enum

    @property
    def blocking_gaps(self) -> tuple[FidelityCompilationGap, ...]:
        return tuple(item for item in self.gaps if item.blocks_completion)

    @property
    def uncovered_obligations(self) -> tuple[str, ...]:
        return tuple(sorted({item.obligation or "" for item in self.traces if not item.covered}))

    @property
    def dimension_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._judged_dimensions))

    @property
    def spec_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    def fingerprint_inputs(self) -> dict[str, Any]:
        """The correctness-relevant view of the spec.

        ``intent_summary`` and rationales are excluded: they are how the requirement is
        explained, and letting them into the digest would make a copy edit look like a change of
        obligations (§15, §20).
        """

        return {
            "subject": self.subject_ref.text,
            "brief": self.brief_ref.text,
            "revision": self.revision_ref.text,
            "model_fingerprint": self.model_fingerprint_digest,
            "constraint_fingerprint": self.constraint_fingerprint_digest,
            "m01_contract_version": self.m01_contract_version,
            "profile": self.profile_ref.text,
            "registry_version": self.dimension_registry_version,
            "class": self.class_request.fingerprint_inputs(),
            "projections": [item.fingerprint_inputs() for item in self.projections],
            "traces": [item.fingerprint_inputs() for item in self.traces],
            "gaps": [item.fingerprint_inputs() for item in self.gaps],
            "reference_ids": list(self.reference_ids),
            "zones": [
                {
                    "zone": item.zone_id,
                    "dimensions": list(item.dimension_ids),
                    "minimum_confidence": item.minimum_confidence,
                    "severities": dict(sorted(item.severity_overrides.items())),
                }
                for item in self.zone_requests
            ],
            "human_review": list(self.human_review_dimension_ids),
            "debt_policy": self.debt_policy_ref.text if self.debt_policy_ref else None,
            "policies": sorted(item.text for item in self.policy_refs),
            "destination": self.destination_ref.text if self.destination_ref else None,
            "platform": self.target_platform,
            "camera": self.camera_profile,
            "delivery": self.delivery_profile,
            "max_judge_disagreement": self.max_judge_disagreement,
            "compiler_version": self.compiler_version,
        }

    def explanation(self) -> dict[str, Any]:
        """The §25 packet: the questions a reviewer asks, answered by reference.

        Compact and re-referenceable on purpose — the alternative is downstream agents re-reading
        the whole brief to find out why a rung was requested.
        """

        return {
            "why_this_class": {
                "class": self.class_request.class_enum.value,
                "basis": self.class_request.basis,
                "authority": self.class_request.authority.level.value,
                "policy": self.class_request.policy_ref.text if self.class_request.policy_ref else None,
            },
            "why_each_dimension": {
                dimension: sorted(
                    {
                        source
                        for trace in self.traces
                        if dimension in trace.dimension_ids
                        for source in trace.sources
                    }
                )
                for dimension in self.dimension_ids
            },
            "why_strict_references": list(self.reference_ids),
            "why_not_strict": list(self.inspiration_ref_ids),
            "why_human_review": list(self.human_review_dimension_ids),
            "capabilities_expected": sorted(
                {item for trace in self.traces for item in trace.evidence_requirements}
            ),
            "unrepresentable": [
                {"class": item.class_name, "detail": item.detail, "obligation": item.obligation}
                for item in self.gaps
            ],
        }


FidelityContractSpec.NESTED = {
    "subject_ref": of(SemanticRef),
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "profile_ref": of(SemanticRef),
    "class_request": of(QualityClassRequest),
    "projections": of(QualityIntentProjection),
    "traces": of(QualityObligationTrace),
    "gaps": of(FidelityCompilationGap),
    "zone_requests": of(ZoneRequest),
    "debt_policy_ref": of(SemanticRef),
    "destination_ref": of(SemanticRef),
    "policy_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class FidelityCompilationFingerprint(Record):
    """The §19 fingerprint over correctness-relevant compilation inputs.

    Two compilations that agree here may be reused for the same work; a difference in any listed
    input is a stale-input signal M02 can act on without re-reading the brief.
    """

    fingerprint_id: str
    compilation_id: str
    semantic_digest: str
    model_fingerprint_digest: str
    constraint_fingerprint_digest: str
    profile_ref: SemanticRef
    dimension_registry_version: str
    m01_contract_version: str
    compiler_version: str
    requested_class: str
    destination_ref: SemanticRef | None = None
    policy_refs: tuple[SemanticRef, ...] = ()
    emitted_contract_digest: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "fingerprint_id", require_identifier(self.fingerprint_id, "fingerprint_id"))
        object.__setattr__(self, "compilation_id", require_identifier(self.compilation_id, "compilation_id"))
        for name in ("semantic_digest", "model_fingerprint_digest", "constraint_fingerprint_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        object.__setattr__(
            self, "profile_ref", require_bound_ref(self.profile_ref, "profile_ref", kind=RefKind.M01_DOMAIN_PROFILE)
        )
        object.__setattr__(
            self, "dimension_registry_version", require_version_text(self.dimension_registry_version, "dimension_registry_version")
        )
        object.__setattr__(
            self, "m01_contract_version", _require_m01_contract_version(self.m01_contract_version)
        )
        object.__setattr__(self, "compiler_version", require_version_text(self.compiler_version, "compiler_version"))
        object.__setattr__(self, "requested_class", QualityClass.parse(self.requested_class).value)
        if self.destination_ref is not None:
            object.__setattr__(self, "destination_ref", SemanticRef.coerce(self.destination_ref, "destination_ref"))
        object.__setattr__(self, "policy_refs", _refs(self.policy_refs, "policy_refs"))
        if self.emitted_contract_digest is not None:
            object.__setattr__(
                self, "emitted_contract_digest", require_digest(self.emitted_contract_digest, "emitted_contract_digest")
            )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def inputs(self) -> dict[str, str]:
        return {
            "model_fingerprint": self.model_fingerprint_digest,
            "constraint_fingerprint": self.constraint_fingerprint_digest,
            "profile": self.profile_ref.text,
            "dimension_registry_version": self.dimension_registry_version,
            "m01_contract_version": self.m01_contract_version,
            "compiler_version": self.compiler_version,
            "requested_class": self.requested_class,
            "destination": self.destination_ref.text if self.destination_ref else "none",
            "policies": ",".join(sorted(item.text for item in self.policy_refs)) or "none",
        }

    def changed_inputs_from(self, other: "FidelityCompilationFingerprint") -> tuple[str, ...]:
        """Named inputs that moved, so staleness is reportable rather than inferred.

        ``emitted_contract_digest`` is excluded: it is an output, and reading it as an input would
        report every recompilation as its own cause.
        """

        if not isinstance(other, FidelityCompilationFingerprint):
            raise SchemaValidationError("fingerprint comparison needs another fingerprint")
        mine, theirs = self.inputs, other.inputs
        return tuple(sorted(key for key in mine if mine[key] != theirs.get(key)))

    def is_stale_for(self, spec: FidelityContractSpec) -> bool:
        """Whether this fingerprint still describes what ``spec`` was compiled from."""

        return self.changed_inputs_from(fingerprint_of(spec)) != ()


FidelityCompilationFingerprint.NESTED = {
    "profile_ref": of(SemanticRef),
    "destination_ref": of(SemanticRef),
    "policy_refs": of(SemanticRef),
}


def fingerprint_of(spec: FidelityContractSpec, *, emitted_contract: FidelityContract | None = None) -> FidelityCompilationFingerprint:
    """Derive the §19 fingerprint for a spec, optionally pinning the emitted contract."""

    digest = content_digest(spec.fingerprint_inputs())
    return FidelityCompilationFingerprint(
        fingerprint_id=f"fp-{spec.compilation_id}",
        compilation_id=spec.compilation_id,
        semantic_digest=digest,
        model_fingerprint_digest=spec.model_fingerprint_digest,
        constraint_fingerprint_digest=spec.constraint_fingerprint_digest,
        profile_ref=spec.profile_ref,
        dimension_registry_version=spec.dimension_registry_version,
        m01_contract_version=spec.m01_contract_version,
        compiler_version=spec.compiler_version,
        requested_class=spec.class_request.class_enum.value,
        destination_ref=spec.destination_ref,
        policy_refs=spec.policy_refs,
        emitted_contract_digest=(
            content_digest(emitted_contract.to_payload()) if emitted_contract is not None else None
        ),
        contract_version=CONTRACT_VERSION,
    )


@dataclass(frozen=True)
class QualityContractDelta(Record):
    """A typed classification of how compiled obligations moved, for M02's impact analysis (§21).

    Most-significant-first, deliberately: a change touching both the quality rung and the
    delivery profile has to be reported as the rung change, because the weaker class would let a
    re-planned rebuild look like a re-tag. The ordering lives in ``_CLASS_PRECEDENCE`` and is
    asserted, never inferred from a dict insertion order.
    """

    delta_id: str
    class_name: str
    before_ref: SemanticRef
    after_ref: SemanticRef
    before_digest: str | None = None
    after_digest: str | None = None
    changed_inputs: tuple[str, ...] = ()
    affected_dimension_ids: tuple[str, ...] = ()
    explanation_paths: tuple[str, ...] = ()
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "delta_id", require_identifier(self.delta_id, "delta_id"))
        kind = QualityChangeClass.parse(self.class_name, "class_name")
        object.__setattr__(self, "class_name", kind.value)
        object.__setattr__(self, "before_ref", SemanticRef.coerce(self.before_ref, "before_ref"))
        object.__setattr__(self, "after_ref", SemanticRef.coerce(self.after_ref, "after_ref"))
        for name in ("before_digest", "after_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        if kind is QualityChangeClass.NO_SEMANTIC_CHANGE and self.changed_inputs:
            raise SchemaValidationError(
                f"delta {self.delta_id} reports no semantic change while listing changed inputs "
                f"{list(self.changed_inputs)}; that pairing is how stale work gets reused"
            )
        if kind is not QualityChangeClass.NO_SEMANTIC_CHANGE and not (
            self.changed_inputs or self.affected_dimension_ids or self.explanation_paths
        ):
            raise SchemaValidationError(
                f"delta {self.delta_id} claims {kind.value} with nothing changed and nothing "
                "affected; an unexplained delta is an argument for rework that cannot be audited"
            )
        object.__setattr__(self, "changed_inputs", _ids(self.changed_inputs, "changed_inputs", identifiers=False))
        object.__setattr__(
            self, "affected_dimension_ids", _ids(self.affected_dimension_ids, "affected_dimension_ids")
        )
        object.__setattr__(
            self, "explanation_paths", _ids(self.explanation_paths, "explanation_paths", identifiers=False)
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def class_enum(self) -> QualityChangeClass:
        return QualityChangeClass.parse(self.class_name)

    @property
    def invalidates_contract(self) -> bool:
        return self.class_enum.invalidates_contract


QualityContractDelta.NESTED = {"before_ref": of(SemanticRef), "after_ref": of(SemanticRef)}


@dataclass(frozen=True)
class FidelityContractMember(Record):
    """One contract inside a set, with the profile authority and the axes it owns."""

    subject_ref: SemanticRef
    contract_ref: SemanticRef
    profile_ref: SemanticRef
    requested_class: str
    dimension_ids: tuple[str, ...] = ()
    evaluator_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_ref", SemanticRef.coerce(self.subject_ref, "subject_ref"))
        object.__setattr__(
            self, "contract_ref", require_bound_ref(self.contract_ref, "contract_ref")
        )
        object.__setattr__(
            self,
            "profile_ref",
            require_bound_ref(self.profile_ref, "profile_ref", kind=RefKind.M01_DOMAIN_PROFILE),
        )
        if self.profile_ref.version is None:  # pragma: no cover - M01 pins profile refs
            raise SchemaValidationError(f"profile ref {self.profile_ref.text} is not version-pinned")
        object.__setattr__(self, "requested_class", QualityClass.parse(self.requested_class).value)
        object.__setattr__(self, "dimension_ids", _ids(self.dimension_ids, "dimension_ids"))
        if not self.dimension_ids:
            raise SchemaValidationError(
                f"contract member {self.subject_ref.text} judges no dimension; a member with no axes "
                "would be an empty obligation competing with the real ones"
            )
        object.__setattr__(
            self, "evaluator_refs", _ids(self.evaluator_refs, "evaluator_refs", identifiers=False)
        )


FidelityContractMember.NESTED = {
    "subject_ref": of(SemanticRef),
    "contract_ref": of(SemanticRef),
    "profile_ref": of(SemanticRef),
}


@dataclass(frozen=True)
class FidelityContractSetRef(Record):
    """Several subject-specific contracts under one brief revision, not one mega-contract (§22).

    The rule that earns its place is *one profile owns an axis once per set*. Two members may share a
    dimension when they come from different domain authorities — a shot contract and a voice contract
    both care whether the work adheres to the brief, and each asks a different evaluator about a
    different subject. The same profile judging the same axis from two members is the split nobody
    asked for: two verdicts for one requirement, which is precisely what the mega-contract was
    avoided to prevent.
    """

    set_id: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    members: tuple[FidelityContractMember, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "set_id", require_identifier(self.set_id, "set_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self, "revision_ref", require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION)
        )
        members = tuple(
            sorted(
                (FidelityContractMember.coerce(item, "members[]") for item in (self.members or ())),
                key=lambda item: item.subject_ref.text,
            )
        )
        if not members:
            raise SchemaValidationError(
                f"contract set {self.set_id} has no members; an empty set reads as coverage to a "
                "readiness check and as nothing to M01"
            )
        if len(members) > MAX_CONTRACTS_PER_SET:
            raise SchemaValidationError(
                f"contract set {self.set_id} holds {len(members)} contracts, above {MAX_CONTRACTS_PER_SET}"
            )
        for name in ("subject", "contract"):
            values = [getattr(item, f"{name}_ref").text for item in members]
            if len(set(values)) != len(values):
                raise SchemaValidationError(
                    f"contract set {self.set_id} repeats a {name} ref; two members pointing at one "
                    f"{name} would be two verdicts on one thing"
                )
        owner: dict[tuple[str, str], str] = {}
        for member in members:
            for dimension in member.dimension_ids:
                key = (member.profile_ref.text, dimension)
                if key in owner:
                    raise SchemaValidationError(
                        f"dimension {dimension} is judged twice by profile {member.profile_ref.text}, "
                        f"in {owner[key]} and {member.subject_ref.text}; §22 splits contracts by "
                        "subject, and a split that leaves one profile answering for one axis twice "
                        "produces two verdicts for one requirement"
                    )
                owner[key] = member.subject_ref.text
        object.__setattr__(self, "members", members)

    @property
    def dimension_ids(self) -> tuple[str, ...]:
        return tuple(sorted({item for member in self.members for item in member.dimension_ids}))

    @property
    def profile_refs(self) -> tuple[str, ...]:
        return tuple(sorted({item.profile_ref.text for item in self.members}))

    @property
    def contract_refs(self) -> tuple[str, ...]:
        return tuple(sorted({item.contract_ref.text for item in self.members}))

    def member_for(self, subject_ref: SemanticRef) -> FidelityContractMember:
        wanted = SemanticRef.coerce(subject_ref, "subject_ref").text
        for member in self.members:
            if member.subject_ref.text == wanted:
                return member
        raise SchemaValidationError(
            f"contract set {self.set_id} carries no member for {wanted}"
        )

    def set_digest(self) -> str:
        return content_digest(
            {
                "brief": self.brief_ref.text,
                "revision": self.revision_ref.text,
                "members": [
                    {
                        "subject": item.subject_ref.text,
                        "contract": item.contract_ref.text,
                        "profile": item.profile_ref.text,
                        "class": item.requested_class,
                        "dimensions": list(item.dimension_ids),
                        "evaluators": list(item.evaluator_refs),
                    }
                    for item in self.members
                ],
            }
        )


FidelityContractSetRef.NESTED = {
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "members": of(FidelityContractMember),
}


@dataclass(frozen=True)
class FidelityCompilation(Record):
    """The result of one compilation attempt: spec, gaps, and maybe a real M01 contract.

    ``status`` is derived from the gaps and from what the record carries, and construction that
    disagrees with that derivation is refused here rather than at some later read: ``COMPLETE``
    with nothing emitted, a contract carried past a blocking gap, and a ``BLOCKED`` result still
    holding a specification are each rejected. The last one is why ``spec`` is optional — §18
    reserves BLOCKED for inputs that cannot even *describe* a contract, and a record that let a
    blocked compilation carry a spec would hand a downstream agent something that looks judgeable.
    """

    status: str
    gaps: tuple[FidelityCompilationGap, ...] = ()
    spec: FidelityContractSpec | None = None
    fingerprint: FidelityCompilationFingerprint | None = None
    contract: FidelityContract | None = None
    delta: QualityContractDelta | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        status = FidelityCompilationStatus.parse(self.status, "status")
        gaps = tuple(
            sorted(
                (FidelityCompilationGap.coerce(item, "gaps[]") for item in (self.gaps or ())),
                key=lambda item: (item.class_name, item.gap_id),
            )
        )
        object.__setattr__(self, "gaps", gaps)
        spec = self.spec
        if spec is not None:
            spec = FidelityContractSpec.coerce(spec, "spec")
            if {item.gap_id for item in gaps} != {item.gap_id for item in spec.gaps}:
                raise SchemaValidationError(
                    "compilation reports gaps its spec does not carry; the two views of what could "
                    "not be expressed must be one list"
                )
        derived = _status_of(gaps, spec)
        if status is not derived:
            raise SchemaValidationError(
                f"compilation declares {status.value} where its gaps derive {derived.value}; §18 "
                "allows COMPLETE, INCOMPLETE or BLOCKED and no partial contract labelled ready"
            )
        object.__setattr__(self, "status", derived.value)
        if derived.has_specification and spec is None:
            raise SchemaValidationError(
                f"a {derived.value} compilation carries no specification; only a BLOCKED result may "
                "omit one, and then it must say which input made a spec impossible"
            )
        if not derived.has_specification and spec is not None:
            raise SchemaValidationError(
                "compilation reports BLOCKED while carrying a specification; §18 makes BLOCKED the "
                "state where the inputs cannot even describe a contract, and a spec that survives "
                "the state reads as a contract waiting for a decision"
            )
        contract = self.contract
        if contract is not None:
            if not isinstance(contract, FidelityContract):
                raise SchemaValidationError(
                    "compilation contract must be an iris_quality FidelityContract"
                )
            if derived is not FidelityCompilationStatus.COMPLETE:
                raise SchemaValidationError(
                    f"compilation carries an emitted contract while {derived.value}; a blocking gap "
                    "means the contract is not the requirement"
                )
            _verify_m01_round_trip(contract)
            _check_contract_matches_spec(spec, contract)
        if derived.may_emit and contract is None:
            raise SchemaValidationError(
                "compilation reports COMPLETE with nothing emitted"
            )
        fingerprint = self.fingerprint
        if fingerprint is None:
            object.__setattr__(
                self,
                "fingerprint",
                fingerprint_of(spec, emitted_contract=contract) if spec is not None else None,
            )
        else:
            fingerprint = FidelityCompilationFingerprint.coerce(fingerprint, "fingerprint")
            if spec is None:
                raise SchemaValidationError(
                    "a BLOCKED compilation carries a fingerprint; with no specification there is "
                    "nothing for a stale-input signal to be about"
                )
            emitted = content_digest(contract.to_payload()) if contract is not None else None
            if fingerprint.emitted_contract_digest != emitted:
                raise SchemaValidationError(
                    f"compilation fingerprint pins {fingerprint.emitted_contract_digest!r} where the "
                    "payload actually carried hashes to a different digest; the stale-input signal "
                    "would be false in whichever direction nobody checked"
                )
            if fingerprint.semantic_digest != spec.spec_digest:
                raise SchemaValidationError(
                    f"compilation fingerprint {fingerprint.fingerprint_id} was taken over different "
                    "semantics than the spec it is attached to"
                )
            object.__setattr__(self, "fingerprint", fingerprint)
        if self.delta is not None:
            if spec is None:
                raise SchemaValidationError(
                    "a BLOCKED compilation reports a quality contract delta; nothing was emitted, "
                    "so there is no change for M02 to analyse"
                )
            object.__setattr__(self, "delta", QualityContractDelta.coerce(self.delta, "delta"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def status_enum(self) -> FidelityCompilationStatus:
        return FidelityCompilationStatus.parse(self.status)

    @property
    def emitted(self) -> bool:
        return self.contract is not None

    @property
    def compilation_id(self) -> str | None:
        return self.spec.compilation_id if self.spec is not None else None

    @property
    def blocking_gaps(self) -> tuple[FidelityCompilationGap, ...]:
        return tuple(item for item in self.gaps if item.blocks_completion)

    @property
    def blocking_gap_ids(self) -> tuple[str, ...]:
        return tuple(sorted(item.gap_id for item in self.blocking_gaps))

    @property
    def gap_classes(self) -> tuple[str, ...]:
        return tuple(sorted({item.class_name for item in self.gaps}))

    @property
    def unrepresentable_obligations(self) -> tuple[str, ...]:
        return self.spec.uncovered_obligations if self.spec is not None else ()

    def explanation(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "spec": self.spec.explanation() if self.spec is not None else None,
            "emitted_contract": self.contract.contract_id if self.contract is not None else None,
            "fingerprint": self.fingerprint.semantic_digest if self.fingerprint else None,
            "changed_from_previous": (
                {"class": self.delta.class_name, "inputs": list(self.delta.changed_inputs)}
                if self.delta is not None
                else None
            ),
        }


FidelityCompilation.NESTED = {
    "spec": of(FidelityContractSpec),
    "gaps": of(FidelityCompilationGap),
    "fingerprint": of(FidelityCompilationFingerprint),
    "contract": of(FidelityContract),
    "delta": of(QualityContractDelta),
}

# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _parse_basis(value: Any) -> QualityClassBasis:
    """Resolve a class basis, naming the rejected spelling it was given.

    :data:`REJECTED_CLASS_BASES` is checked *before* the enum parse so the error reports which
    inadmissible reason was attempted. Folding both into one "unknown basis" message would make
    ``"basis": "cinematic"`` look like a typo, and only one of them is the failure §5 is about.
    """

    if isinstance(value, QualityClassBasis):
        return value
    if not isinstance(value, str):
        raise QualityAuthorityError(
            f"quality class basis must be one of [{QualityClassBasis.describe()}], got {value!r}"
        )
    token = value.strip().upper()
    if token in REJECTED_CLASS_BASES:
        raise QualityAuthorityError(
            f"a quality target cannot rest on {token}; §5 admits only [{QualityClassBasis.describe()}] "
            f"and {token} states how a brief sounds or what a machine can manage in one pass, which is "
            "not a statement about what the deliverable must be (§24, ADR-0008)"
        )
    return QualityClassBasis.parse(token, "basis")


def _require_m01_contract_version(value: Any) -> str:
    """Accept only the M01 contract version this bridge can actually validate."""

    text = require_version_text(value, "m01_contract_version")
    if text != M01_CONTRACT_VERSION:
        raise UnsupportedVersionError(
            f"this bridge emits {M01_CONTRACT_VERSION} and can read no other M01 contract version; it "
            f"was asked for {text!r}. Producing a contract against a version the bridge cannot "
            "round-trip would report success for an object nobody validated"
        )
    return text


def _ids(
    value: Any,
    field_name: str,
    *,
    identifiers: bool = True,
    limit: int = MAX_ENTRIES_PER_FIELD,
) -> tuple[str, ...]:
    """Normalise a bounded, unique, deterministically ordered text list.

    Sorting is not cosmetic: two compilations of the same brief must produce byte-identical payloads,
    or every digest comparison in §19 becomes a coin flip that loses work.
    """

    items = tuple(value or ())
    if len(items) > limit:
        raise SchemaValidationError(f"{field_name} holds {len(items)} entries, above {limit}")
    out: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise SchemaValidationError(
                f"{field_name} entries must be text, got {type(item).__name__}"
            )
        token = item.strip()
        if not token:
            raise SchemaValidationError(f"{field_name} holds an empty entry")
        out.append(
            require_identifier(token, field_name)
            if identifiers
            else require_text(token, field_name, maximum=256)
        )
    duplicates = sorted({token for token in out if out.count(token) > 1})
    if duplicates:
        raise SchemaValidationError(f"{field_name} repeats entries: {duplicates}")
    return tuple(sorted(out))


def _dimensions(
    value: Any, field_name: str = "dimension_ids", *, limit: int = MAX_DIMENSIONS_PER_SPEC
) -> tuple[str, ...]:
    return _ids(value, field_name, limit=limit)


def _refs(value: Any, field_name: str, *, limit: int = MAX_PROVENANCE_REFS) -> tuple[SemanticRef, ...]:
    items = tuple(SemanticRef.coerce(item, f"{field_name}[]") for item in (value or ()))
    if len(items) > limit:
        raise SchemaValidationError(f"{field_name} holds {len(items)} refs, above {limit}")
    unique = {item.text: item for item in items}
    return tuple(unique[key] for key in sorted(unique))


def _declared_severities(owner: Any) -> dict[str, DefectSeverity]:
    """defect class -> the severity its owning profile declares it at."""

    out: dict[str, DefectSeverity] = {}
    for name, severity in DEFECT_CLASS_FIELDS:
        for defect_class in getattr(owner, name):
            out[defect_class] = DefectSeverity.parse(severity)
    return out


def _rungs_requiring(profile: DomainProfile, dimension: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                rule.target_class.value
                for rule in profile.promotion_rules
                if dimension in rule.required_dimension_ids
            }
        )
    )


def _evidence_classes(
    dimension: str,
    *,
    evaluator_registry: EvaluatorRegistry,
    profile: DomainProfile,
    reviewed: bool,
) -> tuple[str, ...]:
    """What will prove this dimension, read off the registrations rather than asserted.

    The panel the profile recommends is preferred; when it names nothing for the axis the check falls
    back to every registered covering evaluator, so the record describes the capability that exists
    instead of one this module invented.
    """

    covering = evaluator_registry.covering(dimension)
    if not covering:
        return ()
    panel = {item.reference for item in profile.recommended_evaluators}
    selected = [item for item in covering if item.reference in panel] or list(covering)
    out = {
        EvidenceClass.DETERMINISTIC_VALIDATOR.value
        if all(item.deterministic for item in selected)
        else EvidenceClass.AUTOMATED_EVALUATOR.value
    }
    if reviewed:
        out.add(EvidenceClass.HUMAN_DECISION.value)
    return tuple(sorted(out))


def _check_trace_coverage(spec: FidelityContractSpec) -> None:
    """§10 and §18: every obligation traced, and no traced dimension nobody asked for.

    ``FidelityContractSpec`` derives its judged set from its traces, so a trace binding a dimension
    its projection never requested would add an axis to the contract through the explanation layer —
    the one route §6 forbids that a dimension-equality check on the emitted contract alone would miss.
    """

    traces = spec.traces
    identifiers = [item.trace_id for item in traces]
    if len(set(identifiers)) != len(identifiers):
        raise SchemaValidationError(f"spec {spec.compilation_id} repeats a trace id")
    projections = {item.projection_id: item for item in spec.projections}
    gap_ids = {item.gap_id for item in spec.gaps}
    traced: set[str] = set()
    for trace in traces:
        if trace.projection_id is None:
            if trace.obligation is not None:
                raise SchemaValidationError(
                    f"trace {trace.trace_id} carries obligation {trace.obligation} with no projection "
                    "behind it; an obligation nobody traced to a decision is the compiler inventing a "
                    "requirement (§10)"
                )
            continue
        projection = projections.get(trace.projection_id)
        if projection is None:
            raise SchemaValidationError(
                f"trace {trace.trace_id} cites projection {trace.projection_id!r}, which the spec does "
                "not carry; an explanation path to a projection that does not exist explains nothing"
            )
        if trace.obligation is not None and trace.obligation != projection.obligation:
            raise SchemaValidationError(
                f"trace {trace.trace_id} reports obligation {trace.obligation} for projection "
                f"{projection.projection_id}, which projects {projection.obligation}"
            )
        invented = sorted(set(trace.dimension_ids) - set(projection.requested_dimensions))
        if invented:
            raise SchemaValidationError(
                f"trace {trace.trace_id} binds dimensions {invented} that projection "
                f"{projection.projection_id} never asked for (§6); a profile-owned axis gets its own "
                "trace citing the profile, not a borrowed projection"
            )
        traced.add(trace.projection_id)
        if trace.covered and trace.gap_id is not None:
            raise SchemaValidationError(
                f"trace {trace.trace_id} claims coverage while naming gap {trace.gap_id}"
            )
        if not trace.covered and trace.gap_id not in gap_ids:
            raise SchemaValidationError(
                f"trace {trace.trace_id} names gap {trace.gap_id!r}, which the spec does not carry"
            )
    untraced = sorted(set(projections) - traced)
    if untraced:
        raise SchemaValidationError(
            f"spec {spec.compilation_id} projects obligations {untraced} with no trace; §18 requires "
            "rationale coverage for every compiled obligation"
        )


def _status_of(
    gaps: Iterable[FidelityCompilationGap], spec: FidelityContractSpec | None
) -> FidelityCompilationStatus:
    """Derive §18's completeness state from the gaps, never from a caller's optimism."""

    items = tuple(gaps)
    if any(item.forbids_specification for item in items):
        return FidelityCompilationStatus.BLOCKED
    if spec is None:
        raise SchemaValidationError(
            "a compilation with no specification must report a gap that forbids specifying; BLOCKED is "
            "the only state without a spec, and it has to name the input that made one impossible (§18)"
        )
    if any(item.blocks_completion for item in items):
        return FidelityCompilationStatus.INCOMPLETE
    return FidelityCompilationStatus.COMPLETE


def _verify_m01_round_trip(contract: FidelityContract) -> None:
    """Prove the emitted contract is M01's own, using M01's own code (§18, D-M03-S03-020).

    M03 has no authority to call something a valid contract because it constructed it, so the claim
    goes through M01's envelope and canonical-payload validation before ``COMPLETE`` is available.
    """

    try:
        payload = contract.to_payload()
        restored = from_envelope(envelope(contract))
        validate_payload("fidelity_contract", payload)
    except m01_errors.QualityKernelError as error:
        raise SchemaValidationError(
            f"emitted contract {contract.contract_id} failed M01's own validation: {error}"
        ) from error
    if restored != contract:
        raise SchemaValidationError(
            f"emitted contract {contract.contract_id} did not survive M01 round-trip unchanged; a "
            "contract that decodes into different obligations cannot be the compiled result"
        )


def _check_contract_matches_spec(spec: FidelityContractSpec, contract: FidelityContract) -> None:
    """Refuse an emitted contract that states something other than what was compiled."""

    if contract.output_class is not spec.requested_class:
        raise QualityAuthorityError(
            f"emitted contract carries {contract.output_class.value} where the compilation requested "
            f"{spec.requested_class.value}; M03 does not get to move the target on the way out (§5)"
        )
    judged = set(spec.dimension_ids)
    emitted = set(contract.dimension_ids)
    if emitted != judged:
        raise SchemaValidationError(
            f"emitted contract judges {sorted(emitted)} but the compilation traced {sorted(judged)}; "
            "an untraced dimension has no explanation path and an untraced one was dropped (§10, §17)"
        )
    if contract.dimension_registry.version != spec.dimension_registry_version:
        raise SchemaValidationError(
            f"emitted contract carries dimension registry {contract.dimension_registry.version} where "
            f"the compilation pinned {spec.dimension_registry_version}"
        )
    missing_refs = sorted(set(spec.reference_ids) - set(contract.reference_ids))
    if missing_refs:
        raise SchemaValidationError(
            f"strict references {missing_refs} are compiled but absent from the emitted contract"
        )
    smuggled = sorted(set(spec.inspiration_ref_ids) & set(contract.reference_ids))
    if smuggled:
        raise SchemaValidationError(
            f"inspirational references {smuggled} appear in the emitted contract's reference_ids; §11 "
            "keeps a mood reference from being promoted into a fidelity obligation"
        )
    extra_zones = sorted(
        {item.zone_id for item in contract.zones} - {item.zone_id for item in spec.zone_requests}
    )
    if extra_zones:
        raise SchemaValidationError(
            f"emitted contract carries zones {extra_zones} the compilation never requested"
        )
    unowned_review = sorted(
        set(spec.human_review_dimension_ids) - set(contract.human_review_dimension_ids)
    )
    if unowned_review:
        raise SchemaValidationError(
            f"human-review obligations {unowned_review} are not carried by the emitted contract; the "
            "list is profile-owned, so M03 may bind within it and never add to it (§14)"
        )
    for name in ("target_platform", "camera_profile", "delivery_profile"):
        if getattr(contract, name) != getattr(spec, name):
            raise SchemaValidationError(f"emitted contract {name} disagrees with the compilation")
    if (
        spec.max_judge_disagreement is not None
        and contract.max_judge_disagreement != spec.max_judge_disagreement
    ):
        raise SchemaValidationError(
            "emitted contract carries a different max_judge_disagreement than the compiled policy (§16)"
        )
    if contract.intent != spec.intent_summary:
        raise SchemaValidationError(
            "emitted contract intent differs from the compiled intent summary"
        )


# --------------------------------------------------------------------------- #
# Quality Contract Delta (§20, §21)
# --------------------------------------------------------------------------- #

#: Most-significant-first. A change touching both the rung and the delivery profile is reported as
#: the rung change, because the weaker class would let a re-planned rebuild read as a re-tag.
_CLASS_PRECEDENCE: tuple[QualityChangeClass, ...] = (
    QualityChangeClass.QUALITY_CLASS_CHANGE,
    QualityChangeClass.PROFILE_CHANGE,
    QualityChangeClass.REGISTRY_CHANGE,
    QualityChangeClass.DIMENSION_OBLIGATION_CHANGE,
    QualityChangeClass.ZONE_CHANGE,
    QualityChangeClass.REFERENCE_CHANGE,
    QualityChangeClass.POLICY_CHANGE,
    QualityChangeClass.DELIVERY_PROFILE_CHANGE,
    QualityChangeClass.NO_SEMANTIC_CHANGE,
)

#: Which change class each comparable field reports, listed in that same precedence order.
_DELTA_FIELDS: tuple[tuple[str, QualityChangeClass], ...] = (
    ("requested_class", QualityChangeClass.QUALITY_CLASS_CHANGE),
    ("profile", QualityChangeClass.PROFILE_CHANGE),
    ("dimension_registry_version", QualityChangeClass.REGISTRY_CHANGE),
    ("m01_contract_version", QualityChangeClass.REGISTRY_CHANGE),
    ("compiler_version", QualityChangeClass.REGISTRY_CHANGE),
    ("dimensions", QualityChangeClass.DIMENSION_OBLIGATION_CHANGE),
    ("obligations", QualityChangeClass.DIMENSION_OBLIGATION_CHANGE),
    ("zones", QualityChangeClass.ZONE_CHANGE),
    ("references", QualityChangeClass.REFERENCE_CHANGE),
    ("human_review", QualityChangeClass.POLICY_CHANGE),
    ("policies", QualityChangeClass.POLICY_CHANGE),
    ("max_judge_disagreement", QualityChangeClass.POLICY_CHANGE),
    ("destination", QualityChangeClass.DELIVERY_PROFILE_CHANGE),
    ("target_platform", QualityChangeClass.DELIVERY_PROFILE_CHANGE),
    ("camera_profile", QualityChangeClass.DELIVERY_PROFILE_CHANGE),
    ("delivery_profile", QualityChangeClass.DELIVERY_PROFILE_CHANGE),
)


def _view_of(value: Any, field_name: str) -> dict[str, Any]:
    """Reduce a spec, an emitted contract or a whole compilation to comparable fields.

    Comparing against a bare ``FidelityContract`` is the recompilation case where only the emitted
    object survived: fields that object does not carry come back ``None`` and are skipped rather than
    reported as changes, because "M03 cannot see it" and "it moved" are different claims.
    """

    if isinstance(value, FidelityCompilation):
        if value.spec is not None:
            return _view_of(value.spec, field_name)
        if value.contract is not None:
            return _view_of(value.contract, field_name)
        raise SchemaValidationError(
            f"{field_name}: a BLOCKED compilation carries nothing to compare; §21's delta describes "
            "what an emitted contract requires, and this one requires nothing yet"
        )
    if isinstance(value, FidelityContractSpec):
        return {
            "ref": value.revision_ref,
            "ident": value.compilation_id,
            "digest": value.spec_digest,
            "requested_class": value.requested_class.value,
            "profile": value.profile_ref.text,
            "dimension_registry_version": value.dimension_registry_version,
            "m01_contract_version": value.m01_contract_version,
            "compiler_version": value.compiler_version,
            "dimensions": set(value.dimension_ids),
            "references": set(value.reference_ids),
            "zones": {
                item.zone_id: (
                    set(item.dimension_ids),
                    item.minimum_confidence,
                    dict(item.severity_overrides),
                )
                for item in value.zone_requests
            },
            "human_review": set(value.human_review_dimension_ids),
            "policies": {item.text for item in value.policy_refs}
            | ({value.debt_policy_ref.text} if value.debt_policy_ref else set()),
            "max_judge_disagreement": value.max_judge_disagreement,
            "destination": value.destination_ref.text if value.destination_ref else "none",
            "target_platform": value.target_platform,
            "camera_profile": value.camera_profile,
            "delivery_profile": value.delivery_profile,
            "obligations": {
                item.projection_id: item.fingerprint_inputs() for item in value.projections
            },
        }
    if isinstance(value, FidelityContract):
        return {
            "ref": SemanticRef(
                kind=RefKind.M01_CONTRACT.value,
                ref_id=value.contract_id,
                version=value.contract_version,
                content_digest=content_digest(value.to_payload()),
            ),
            "ident": value.contract_id,
            "digest": content_digest(value.to_payload()),
            "requested_class": value.output_class.value,
            "profile": None,
            "dimension_registry_version": value.dimension_registry.version,
            "m01_contract_version": value.contract_version,
            "compiler_version": None,
            "dimensions": set(value.dimension_ids),
            "references": set(value.reference_ids),
            "zones": {
                item.zone_id: (
                    set(item.dimension_ids),
                    item.minimum_confidence,
                    {key: severity.value for key, severity in item.severity_overrides.items()},
                )
                for item in value.zones
            },
            "human_review": set(value.human_review_dimension_ids),
            "policies": None,
            "max_judge_disagreement": value.max_judge_disagreement,
            "destination": None,
            "target_platform": value.target_platform,
            "camera_profile": value.camera_profile,
            "delivery_profile": value.delivery_profile,
            "obligations": None,
        }
    raise SchemaValidationError(
        f"{field_name} must be a FidelityContractSpec, an emitted FidelityContract or a "
        f"FidelityCompilation, got {type(value).__name__}"
    )


def _moved(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    return left != right


def _zone_dimensions(*views: Mapping[str, Any]) -> set[str]:
    out: set[str] = set()
    for view in views:
        for entry in (view.get("zones") or {}).values():
            out |= set(entry[0])
    return out


def quality_contract_delta(
    before: Any, after: Any, *, delta_id: str | None = None
) -> QualityContractDelta:
    """Classify how compiled quality obligations moved, for M02's impact analysis (§21).

    Prose-only edits produce nothing here by construction: the comparable view is built from
    ``fingerprint_inputs``, which excludes intent summaries and rationales. That is what lets a copy
    revision advance without every downstream build being invalidated (§20).
    """

    left, right = _view_of(before, "before"), _view_of(after, "after")
    changed = tuple(key for key, _ in _DELTA_FIELDS if _moved(left.get(key), right.get(key)))
    detected = [kind for key, kind in _DELTA_FIELDS if key in changed]
    kind = (
        min(detected, key=_CLASS_PRECEDENCE.index)
        if detected
        else QualityChangeClass.NO_SEMANTIC_CHANGE
    )
    dimensions: set[str] = set()
    if "dimensions" in changed:
        dimensions |= left["dimensions"] ^ right["dimensions"]
    if "zones" in changed:
        dimensions |= _zone_dimensions(left, right)
    if "human_review" in changed:
        dimensions |= left["human_review"] ^ right["human_review"]
    paths = [f"delta:{key}" for key in changed]
    if "obligations" in changed:
        old, new = left["obligations"], right["obligations"]
        for identifier in sorted(set(old) | set(new)):
            if old.get(identifier) != new.get(identifier):
                entry = new.get(identifier) or old.get(identifier)
                paths.append(str(entry.get("semantic_path") or identifier))
    return QualityContractDelta(
        delta_id=(
            delta_id
            if delta_id is not None
            else f"qcd-{left['ident']}-to-{right['ident']}"
        ),
        class_name=kind.value,
        before_ref=left["ref"],
        after_ref=right["ref"],
        before_digest=left["digest"],
        after_digest=right["digest"],
        changed_inputs=changed,
        affected_dimension_ids=tuple(sorted(dimensions)),
        explanation_paths=tuple(paths),
        contract_version=CONTRACT_VERSION,
    )


def require_no_downgrade(previous: Any, requested: Any, *, basis: Any = None) -> QualityClass:
    """Refuse a lowered target unless a person or a governed policy is on the record for it.

    A change of mind is legal: an owner may lower a deliverable's rung, and the record then says who
    said so. What has no path here is a mechanical rule, a provider's capability list or a VRAM figure
    moving the target (§5 rule 3, §24, ADR-0008).
    """

    from_rung = QualityClass.parse(previous)
    to_rung = QualityClass.parse(requested)
    if to_rung.ladder_rank >= from_rung.ladder_rank:
        return to_rung
    kind = None if basis is None else _parse_basis(basis)
    if kind in {
        QualityClassBasis.EXPLICIT_HUMAN,
        QualityClassBasis.PROJECT_POLICY,
        QualityClassBasis.DELIVERY_POLICY,
    }:
        return to_rung
    raise QualityAuthorityError(
        f"the target moves from {from_rung.value} down to {to_rung.value} on "
        f"{'a' if kind else 'an'} {kind.value if kind else 'unstated'} basis; §5 and §24 keep hardware, provider capability, "
        "cost and schedule out of the quality class, and a profile rule cannot lower what an owner or a "
        "policy set. Restate the target from the authority that owns it — or compile the same rung and "
        "let the planners stage the work"
    )


def require_compilable(
    compilation: Any, *, action: str = "emit the fidelity contract"
) -> FidelityContract:
    """Hand back the emitted contract, or refuse naming the gaps that stopped it.

    The refusal quotes gap details because the caller's next step is a human conversation; an error
    naming only ``INCOMPLETE`` would send the caller off to find the list anyway.
    """

    result = FidelityCompilation.coerce(compilation, "compilation")
    status = result.status_enum
    if status is FidelityCompilationStatus.COMPLETE:
        contract = result.contract
        if contract is None:  # pragma: no cover - the record refuses this
            raise SchemaValidationError("a COMPLETE compilation carries no contract")
        return contract
    quoted = "; ".join(f"{item.class_name}: {item.detail}" for item in result.gaps[:4])
    if status is FidelityCompilationStatus.BLOCKED:
        raise AdmissionRefusedError(
            f"cannot {action} while BLOCKED — {quoted or 'no gap recorded'}; §18 refuses to compile "
            "across an input that cannot even describe a contract"
        )
    raise CapabilityGapError(
        f"cannot {action} while {status.value} — {quoted or 'no gap recorded'}; §18 forbids emitting a "
        "partial contract and §8 forbids inventing the missing capability to get one"
    )


# --------------------------------------------------------------------------- #
# The compiler
# --------------------------------------------------------------------------- #


def _projection_trace(
    projection: QualityIntentProjection,
    bound: tuple[str, ...],
    *,
    profile: DomainProfile,
    evaluator_registry: EvaluatorRegistry,
    reviewed: frozenset[str],
    zone_ids: tuple[str, ...],
    provenance: SemanticRef,
) -> QualityObligationTrace:
    """The covered case: this projection's obligation, on the axes that carry it."""

    evidence: set[str] = set()
    targets: set[str] = set()
    for dimension in bound:
        evidence |= set(
            _evidence_classes(
                dimension,
                evaluator_registry=evaluator_registry,
                profile=profile,
                reviewed=dimension in reviewed,
            )
        )
        targets |= set(_rungs_requiring(profile, dimension))
    return QualityObligationTrace(
        trace_id=f"tr-{projection.projection_id}",
        semantic_path=projection.semantic_path,
        obligation=projection.obligation,
        projection_id=projection.projection_id,
        requested_dimension_ids=projection.requested_dimensions,
        dimension_ids=bound,
        statement_ids=projection.statement_ids,
        constraint_ids=projection.constraint_ids,
        policy_refs=tuple(item for item in projection.policy_refs) or (provenance,),
        destination_refs=projection.destination_refs,
        reference_ids=tuple(item.ref_id for item in projection.anchor_refs),
        zone_ids=zone_ids,
        promotion_targets=tuple(sorted(targets)),
        evidence_requirements=tuple(sorted(evidence)),
        human_review_required=bool(reviewed & set(bound)),
        covered=True,
        contract_version=CONTRACT_VERSION,
    )


def _uncovered_trace(
    projection: QualityIntentProjection,
    *,
    gap_id: str,
    dimension: str | None = None,
    requested: tuple[str, ...] | None = None,
    provenance: SemanticRef,
) -> QualityObligationTrace:
    """The requirement stands, unrepresented, and says which gap carries it (§17)."""

    suffix = f"-{dimension}" if dimension else ""
    return QualityObligationTrace(
        trace_id=f"tr-{projection.projection_id}{suffix}",
        semantic_path=projection.semantic_path,
        obligation=projection.obligation,
        projection_id=projection.projection_id,
        requested_dimension_ids=requested or projection.requested_dimensions,
        statement_ids=projection.statement_ids,
        constraint_ids=projection.constraint_ids,
        policy_refs=tuple(item for item in projection.policy_refs) or (provenance,),
        destination_refs=projection.destination_refs,
        reference_ids=tuple(item.ref_id for item in projection.anchor_refs),
        covered=False,
        gap_id=gap_id,
        contract_version=CONTRACT_VERSION,
    )


def compile_fidelity_contract(
    *,
    compilation_id: str,
    subject_ref: Any,
    brief_ref: Any,
    revision_ref: Any,
    model_fingerprint_digest: Any,
    constraint_fingerprint_digest: Any,
    profile: DomainProfile | None,
    profile_ref: Any,
    evaluator_registry: EvaluatorRegistry,
    class_request: Any,
    intent_summary: str,
    projections: Iterable[Any] = (),
    references: Iterable[Any] = (),
    zone_requests: Iterable[Any] = (),
    human_review_dimension_ids: Iterable[str] = (),
    policy_refs: Iterable[Any] = (),
    destination_ref: Any = None,
    debt_policy: QualityDebtPolicy | None = None,
    debt_policy_ref: Any = None,
    dimension_registry_version: str | None = None,
    m01_contract_version: str = M01_CONTRACT_VERSION,
    compiler_version: str = COMPILER_VERSION,
    target_platform: str = "unspecified",
    camera_profile: str = "unspecified",
    delivery_profile: str = "unspecified",
    max_judge_disagreement: float | None = None,
    blocking_ambiguity_refs: Iterable[Any] = (),
    freshness: BriefFreshnessVector | None = None,
    previous: FidelityCompilation | None = None,
    contract_id: str | None = None,
) -> FidelityCompilation:
    """Compile admitted M03 semantics into an M01 contract, or into the gaps that stop it.

    The order is deliberate. Precondition failures — which profile, which registry, is the revision
    still current, is a blocking ambiguity still open — settle first, because they decide whether a
    specification can be described at all. Requirements are then mapped onto dimensions the selected
    profile actually carries, every unmapped requirement recorded as a gap that keeps its own source
    refs. Capability is checked where it is owned (:class:`EvaluatorRegistry`), and the emitted
    contract is validated by M01 before ``COMPLETE`` is available. Nowhere does this function lower a
    target, drop a dimension or add an evaluator to make a step pass.

    Mapping-only staleness is tolerated on purpose: a provider or a translation changing cannot
    invalidate provider-neutral quality semantics (§18, and S03's reason for existing).
    """

    ident = require_identifier(compilation_id, "compilation_id")
    subject = SemanticRef.coerce(subject_ref, "subject_ref")
    brief = require_bound_ref(brief_ref, "brief_ref", kind=RefKind.BRIEF)
    revision = require_bound_ref(revision_ref, "revision_ref", kind=RefKind.REVISION)
    if not isinstance(evaluator_registry, EvaluatorRegistry):
        raise SchemaValidationError(
            "compile_fidelity_contract needs M01's EvaluatorRegistry; capability is resolved there and "
            "never inferred here (§8)"
        )
    request = QualityClassRequest.coerce(class_request, "class_request")
    projection_records = tuple(
        sorted(
            (QualityIntentProjection.coerce(item, "projections[]") for item in (projections or ())),
            key=lambda item: item.projection_id,
        )
    )
    if len({item.projection_id for item in projection_records}) != len(projection_records):
        raise SchemaValidationError(f"compilation {ident} repeats a projection id")
    reference_records = tuple(
        sorted(
            (ReferenceRequest.coerce(item, "references[]") for item in (references or ())),
            key=lambda item: item.ref_id,
        )
    )
    if len({item.ref_id for item in reference_records}) != len(reference_records):
        raise SchemaValidationError(f"compilation {ident} repeats a reference id")
    zone_records = tuple(
        sorted(
            (ZoneRequest.coerce(item, "zone_requests[]") for item in (zone_requests or ())),
            key=lambda item: item.zone_id,
        )
    )
    if len({item.zone_id for item in zone_records}) != len(zone_records):
        raise SchemaValidationError(f"compilation {ident} repeats a zone id")
    policy_sources = _refs(policy_refs, "policy_refs")
    destination = (
        SemanticRef.coerce(destination_ref, "destination_ref") if destination_ref is not None else None
    )
    debt_ref = (
        SemanticRef.coerce(debt_policy_ref, "debt_policy_ref") if debt_policy_ref is not None else None
    )
    if debt_policy is not None and debt_ref is None:
        raise SchemaValidationError(
            "a QualityDebtPolicy may only be bound through its approved ref (§15); handing the compiler "
            "a policy object with no provenance is exactly the unattributed setting §16 refuses"
        )

    gaps: list[FidelityCompilationGap] = []

    def record(
        class_name: GapClass,
        detail: str,
        *,
        refs: Iterable[Any] = (),
        obligation: str | None = None,
        missing_dimension_id: str | None = None,
        mandatory: bool = True,
        remedy: str | None = None,
        path: str | None = None,
    ) -> FidelityCompilationGap:
        item = FidelityCompilationGap(
            gap_id=f"{ident}-gap-{len(gaps) + 1:03d}",
            class_name=class_name.value,
            detail=detail,
            source_refs=tuple(refs) or (revision,),
            semantic_path=path,
            obligation=obligation,
            missing_dimension_id=missing_dimension_id,
            mandatory_origin=mandatory,
            remedy=remedy,
            contract_version=CONTRACT_VERSION,
        )
        gaps.append(item)
        return item

    # --- preconditions: can a contract even be described? -------------------- #
    if profile is None:
        record(
            GapClass.MISSING_DOMAIN_PROFILE,
            "no domain profile was selected; the dimensions, promotion rules and evaluator panel a "
            "contract inherits are all profile-owned, so nothing can be described without one",
            refs=(revision,),
            remedy="select and admit an M01 domain profile for this subject",
        )
        return FidelityCompilation(status=FidelityCompilationStatus.BLOCKED.value, gaps=tuple(gaps))
    if not isinstance(profile, DomainProfile):
        raise SchemaValidationError(
            f"profile must be an iris_quality DomainProfile, got {type(profile).__name__}"
        )
    pinned = require_bound_ref(profile_ref, "profile_ref", kind=RefKind.M01_DOMAIN_PROFILE)
    if pinned.ref_id != profile.profile_id or pinned.version != profile.version:
        record(
            GapClass.PROFILE_POLICY_CONFLICT,
            f"profile_ref {pinned.text} does not name the profile handed to the compiler "
            f"({profile.reference}); §18 requires the version-pinned selected profile, and a ref "
            "pointing elsewhere attributes these obligations to the wrong owner",
            refs=(pinned, revision),
            remedy="pin the ref to the profile actually used, or pass the profile the ref names",
        )
    registry = profile.dimension_registry
    declared_registry = require_version_text(
        dimension_registry_version or registry.version, "dimension_registry_version"
    )
    if declared_registry != registry.version:
        record(
            GapClass.REGISTRY_VERSION_MISMATCH,
            f"the compilation declares dimension registry {declared_registry} while the selected profile "
            f"resolves against {registry.version}",
            refs=(pinned, revision),
            remedy="recompile against the registry the profile was admitted with",
        )
    _require_m01_contract_version(m01_contract_version)

    ambiguities = _refs(blocking_ambiguity_refs, "blocking_ambiguity_refs")
    if ambiguities:
        record(
            GapClass.BLOCKING_AMBIGUITY,
            f"{len(ambiguities)} blocking ambiguity still stands: "
            f"{', '.join(item.text for item in ambiguities)}; §18 will not compile a contract across a "
            "requirement nobody has decided",
            refs=ambiguities,
            remedy="resolve the ambiguity, admit the new revision, then compile",
        )
    if freshness is not None:
        if freshness.brief_ref.ref_id != brief.ref_id:
            record(
                GapClass.STALE_COMPILATION_INPUT,
                f"the freshness vector {freshness.vector_id} describes brief "
                f"{freshness.brief_ref.text}, not the {brief.text} being compiled",
                refs=(freshness.vector_ref,),
                remedy="assess freshness for this brief revision",
            )
        else:
            try:
                require_fresh(
                    freshness,
                    action="compile the fidelity contract",
                    allow_mapping_stale=True,
                )
            except StaleSemanticError as error:
                record(
                    GapClass.STALE_COMPILATION_INPUT,
                    str(error),
                    refs=(freshness.vector_ref,),
                    remedy="refresh the reuse passport or recompile against the current revision",
                )

    admitted = set(profile.dimension_ids)
    severities = _declared_severities(profile)

    # --- evaluator capability (§8) ------------------------------------------ #
    # Recorded before traces so an axis nobody can prove becomes an uncovered
    # obligation citing this gap, rather than a covered trace with no evidence class.
    unprovable: dict[str, FidelityCompilationGap] = {}
    for dimension in sorted(admitted):
        if not evaluator_registry.covering(dimension):
            unprovable[dimension] = record(
                GapClass.MISSING_EVALUATOR_CAPABILITY,
                f"no registered evaluator covers {dimension}, which profile {profile.reference} judges; "
                "§8 blocks execution and promotion for that contract, and the dimension stays rather "
                "than being dropped so the requirement survives the refusal",
                refs=(pinned, revision),
                missing_dimension_id=dimension,
                remedy="register a versioned evaluator for the dimension in M01",
            )

    # --- human review (§14) -------------------------------------------------- #
    reviewable = set(profile.human_review_dimension_ids)
    review_kept: list[str] = []
    for dimension in _dimensions(human_review_dimension_ids, "human_review_dimension_ids"):
        if dimension in reviewable:
            review_kept.append(dimension)
        elif dimension not in admitted:
            record(
                GapClass.MISSING_DIMENSION,
                f"human review requested for {dimension}, which the selected profile does not judge at "
                "all; a review obligation over an unjudged axis protects nothing",
                refs=(revision,),
                missing_dimension_id=dimension,
                remedy="select a profile carrying the dimension",
            )
        else:
            record(
                GapClass.PROFILE_POLICY_CONFLICT,
                f"human review requested for {dimension}, which profile {profile.reference} judges "
                "without routing it to a human; §14 keeps the review list M01's, and M03 cannot add an "
                "obligation M01 would not honour",
                refs=(revision, pinned),
                remedy="an admitted profile version that routes the dimension to human review",
            )
    reviewed = frozenset(review_kept)

    # --- zones (§12) and defect severity (§13) ------------------------------ #
    zones_kept: list[ZoneRequest] = []
    for zone in zone_records:
        outside = sorted(set(zone.dimension_ids) - admitted)
        if outside:
            record(
                GapClass.MISSING_DIMENSION,
                f"zone {zone.zone_id} protects dimensions {outside} that the selected profile does not "
                "judge; emphasis over an unjudged axis would be recorded and then silently ignored",
                refs=(revision,),
                missing_dimension_id=outside[0],
                remedy="choose a profile that judges the protected axes, or drop the protection from "
                "the brief",
            )
            continue
        weaker = sorted(
            name
            for name, severity in zone.severity_overrides.items()
            if name in severities and DefectSeverity.parse(severity).rank < severities[name].rank
        )
        if weaker:
            record(
                GapClass.PROFILE_POLICY_CONFLICT,
                f"zone {zone.zone_id} declares {weaker} below the profile's own severity; §13 forbids a "
                "brief relabelling a profile-declared FATAL or MAJOR class, and M01's zone semantics "
                "only ever tighten, so the relaxation could not bite even if it were admitted",
                refs=(revision, pinned),
                remedy="an authorized versioned policy change (an S05 override), never a zone request",
            )
            continue
        inert = sorted(name for name in zone.severity_overrides if name not in severities)
        if inert:
            record(
                GapClass.UNREPRESENTABLE_CONSTRAINT,
                f"zone {zone.zone_id} overrides severities for {inert}, which the profile declares at no "
                "severity; M01 can only raise a defect the contract admits, so the emphasis cannot be "
                "expressed as an obligation",
                refs=(revision, pinned),
                remedy="declare the defect class in an admitted profile version, or remove the override",
            )
            continue
        zones_kept.append(zone)

    # --- references (§11) --------------------------------------------------- #
    strict = tuple(item for item in reference_records if item.strict)
    inspirational = tuple(item for item in reference_records if not item.strict)
    for reference in strict:
        if reference.resolved:
            continue
        record(
            GapClass.UNRESOLVED_REFERENCE,
            f"strict reference {reference.ref_id} (role {reference.role}) is unresolved; a must-match or "
            "identity-anchor obligation cannot be judged against something that has not arrived",
            refs=(reference.source_ref or revision,),
            remedy="resolve the reference and admit the revision that cites it",
            path=reference.semantic_path,
        )

    # --- requirement -> admitted dimension (§6) ----------------------------- #
    traces: list[QualityObligationTrace] = []
    covered: set[str] = set()
    for projection in projection_records:
        bound = tuple(
            item for item in projection.requested_dimensions if item in admitted and registry.admits(item)
        )
        zone_ids = tuple(
            sorted(zone.zone_id for zone in zones_kept if zone.projection_id == projection.projection_id)
        )
        if not bound:
            known = [item for item in projection.requested_dimensions if registry.admits(item)]
            cause = (
                f"the registry {registry.version} admits none of {list(projection.requested_dimensions)}"
                if not known
                else f"the registry admits {known} but the selected profile {profile.reference} does not "
                "carry them"
            )
            gap = record(
                GapClass.MISSING_DIMENSION,
                f"obligation {projection.obligation} on {projection.semantic_path} cannot compile: "
                f"{cause}. §6 keeps it a declared unresolved requirement instead of a free-form dimension "
                "string in a production contract",
                refs=projection.source_refs,
                obligation=projection.obligation,
                missing_dimension_id=projection.requested_dimensions[0],
                mandatory=projection.mandatory,
                remedy="register the extension dimension through M01's dimension-registry contract, or "
                "re-select a profile that carries it",
                path=projection.semantic_path,
            )
            traces.append(
                _uncovered_trace(projection, gap_id=gap.gap_id, provenance=pinned)
            )
            continue
        provable = tuple(item for item in bound if item not in unprovable)
        covered.update(provable)
        if provable:
            traces.append(
                _projection_trace(
                    projection,
                    provable,
                    profile=profile,
                    evaluator_registry=evaluator_registry,
                    reviewed=reviewed,
                    zone_ids=zone_ids,
                    provenance=pinned,
                )
            )
        for dimension in bound:
            if dimension in unprovable:
                traces.append(
                    _uncovered_trace(
                        projection,
                        gap_id=unprovable[dimension].gap_id,
                        dimension=dimension,
                        requested=(dimension,),
                        provenance=pinned,
                    )
                )

    # --- promotion integrity (§9) and the no-downgrade shield (§5, §24) ----- #
    targets = {rule.target_class for rule in profile.promotion_rules}
    needed = [
        rung for rung in QualityClass.ladder()[1:] if rung.ladder_rank <= request.class_enum.ladder_rank
    ]
    missing_rungs = sorted(rung.value for rung in needed if rung not in targets)
    if missing_rungs:
        record(
            GapClass.UNSUPPORTED_QUALITY_CLASS,
            f"profile {profile.reference} has no promotion rules for {missing_rungs}, which stand between "
            f"DRAFT and the requested {request.requested_class.value}; §5 rule 5 reports the gap instead "
            "of lowering the target to fit what can currently be proven",
            refs=(pinned, request.authority.granted_by or revision),
            remedy="admit profile promotion rules covering the rung, or have the target's owner restate "
            "the class with an explicit basis",
        )
    if previous is not None and previous.spec is not None:
        try:
            require_no_downgrade(previous.spec.requested_class, request.class_enum, basis=request.basis)
        except QualityAuthorityError as error:
            record(
                GapClass.UNSUPPORTED_QUALITY_CLASS,
                str(error),
                refs=(revision, previous.spec.revision_ref),
                remedy="keep the previous target, or restate it from the authority that owns it",
            )
    if max_judge_disagreement is not None and not policy_sources and debt_ref is None:
        record(
            GapClass.UNREPRESENTABLE_CONSTRAINT,
            "a non-default max_judge_disagreement was requested with no policy or profile source; §16 "
            "requires the exact setting's provenance, and an unattributed threshold is a judgement "
            "nobody owns",
            refs=(revision,),
            remedy="cite the governed policy or admitted profile rule that set it",
        )
        max_judge_disagreement = None

    for dimension in sorted(admitted - covered):
        gap = unprovable.get(dimension)
        if gap is not None:
            traces.append(
                QualityObligationTrace(
                    trace_id=f"tr-profile-{dimension}",
                    semantic_path=None,
                    dimension_ids=(),
                    policy_refs=(pinned,),
                    covered=False,
                    gap_id=gap.gap_id,
                    contract_version=CONTRACT_VERSION,
                )
            )
            continue
        traces.append(
            QualityObligationTrace(
                trace_id=f"tr-profile-{dimension}",
                semantic_path=None,
                dimension_ids=(dimension,),
                policy_refs=(pinned,),
                promotion_targets=_rungs_requiring(profile, dimension),
                evidence_requirements=_evidence_classes(
                    dimension,
                    evaluator_registry=evaluator_registry,
                    profile=profile,
                    reviewed=dimension in reviewed,
                ),
                human_review_required=dimension in reviewed,
                covered=True,
                contract_version=CONTRACT_VERSION,
            )
        )

    # --- BLOCKED: the inputs cannot describe a contract --------------------- #
    if any(item.forbids_specification for item in gaps):
        return FidelityCompilation(status=FidelityCompilationStatus.BLOCKED.value, gaps=tuple(gaps))

    spec = FidelityContractSpec(
        compilation_id=ident,
        subject_ref=subject,
        brief_ref=brief,
        revision_ref=revision,
        model_fingerprint_digest=require_digest(model_fingerprint_digest, "model_fingerprint_digest"),
        constraint_fingerprint_digest=require_digest(
            constraint_fingerprint_digest, "constraint_fingerprint_digest"
        ),
        m01_contract_version=m01_contract_version,
        profile_ref=pinned,
        dimension_registry_version=declared_registry,
        class_request=request,
        intent_summary=intent_summary,
        projections=projection_records,
        traces=tuple(sorted(traces, key=lambda item: item.trace_id)),
        gaps=tuple(gaps),
        reference_ids=tuple(item.ref_id for item in strict),
        inspiration_ref_ids=tuple(item.ref_id for item in inspirational),
        zone_requests=tuple(zones_kept),
        human_review_dimension_ids=tuple(sorted(review_kept)),
        debt_policy_ref=debt_ref,
        policy_refs=policy_sources,
        destination_ref=destination,
        target_platform=target_platform,
        camera_profile=camera_profile,
        delivery_profile=delivery_profile,
        max_judge_disagreement=max_judge_disagreement,
        compiler_version=compiler_version,
        contract_version=CONTRACT_VERSION,
    )

    if any(item.blocks_completion for item in gaps):
        return FidelityCompilation(
            status=FidelityCompilationStatus.INCOMPLETE.value, gaps=tuple(gaps), spec=spec
        )

    # --- emission: M01 instantiates and validates --------------------------- #
    try:
        contract = profile.instantiate(
            contract_id=require_identifier(contract_id or f"contract-{ident}", "contract_id"),
            intent=spec.intent_summary,
            output_class=spec.requested_class,
            target_platform=spec.target_platform,
            camera_profile=spec.camera_profile,
            delivery_profile=spec.delivery_profile,
            reference_ids=spec.reference_ids,
            zones=tuple(item.to_m01() for item in spec.zone_requests),
            debt_policy=debt_policy,
            max_judge_disagreement=(
                M01_DEFAULT_DISAGREEMENT
                if spec.max_judge_disagreement is None
                else spec.max_judge_disagreement
            ),
        )
    except m01_errors.QualityKernelError as error:
        record(
            GapClass.UNREPRESENTABLE_CONSTRAINT,
            f"the selected profile refused to instantiate the compiled contract: {error}",
            refs=(pinned, revision),
            remedy="align the request with what the admitted profile represents; M03 does not get to "
            "rewrite M01's schema to fit the brief",
        )
        return FidelityCompilation(
            status=FidelityCompilationStatus.INCOMPLETE.value, gaps=tuple(gaps), spec=spec
        )
    try:
        evaluator_registry.resolve(contract)
    except m01_errors.QualityKernelError as error:
        record(
            GapClass.MISSING_EVALUATOR_CAPABILITY,
            f"M01 refused to resolve the profile's evaluator panel for the compiled contract: {error}",
            refs=(pinned, revision),
            remedy="register the missing evaluator version in M01; §8 keeps resolve() the authority "
            "boundary, and M03 does not add a panel member to get past it",
        )
        return FidelityCompilation(
            status=FidelityCompilationStatus.INCOMPLETE.value, gaps=tuple(gaps), spec=spec
        )

    delta = (
        quality_contract_delta(previous.spec, spec)
        if previous is not None and previous.spec is not None
        else None
    )
    return FidelityCompilation(
        status=FidelityCompilationStatus.COMPLETE.value,
        gaps=tuple(gaps),
        spec=spec,
        contract=contract,
        delta=delta,
    )
