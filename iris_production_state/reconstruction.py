"""Bounded reproducibility, reconstruction and divergence evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base import CanonicalRecord, require_exact_ref, require_sequence
from .enums import DivergenceKind, ReproducibilityClass
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS
from .revisions import ContentDigest, MaterializationRef, OperationalRevisionRef
from .versions import CORE_SCHEMA_VERSION, require_identifier, require_text, require_version

__all__ = [
    "ReconstructionMethod",
    "ReconstructionManifest",
    "DivergenceEvidence",
    "ReproducibilityReceipt",
    "HistoricalPermissionEvidence",
    "classify_reconstruction",
    "validate_historical_permission",
    "require_bounded_reproducibility",
]


class ReconstructionMethod(str, Enum):
    RESTORE_RETAINED = "RESTORE_RETAINED"
    REGENERATE = "REGENERATE"
    ROLLBACK = "ROLLBACK"


@dataclass(frozen=True)
class ReconstructionManifest(CanonicalRecord):
    manifest_id: str
    target_revision_ref: OperationalRevisionRef
    method: ReconstructionMethod
    exact_input_refs: tuple[Any, ...]
    dependency_fingerprint: str
    workflow_ref: Any | None
    model_ref: Any | None
    toolchain_ref: Any | None
    material_environment_facts: tuple[tuple[str, str], ...]
    policy_refs: tuple[Any, ...]
    expected_class: ReproducibilityClass
    equivalence_contract_ref: Any | None
    seed: str | None
    complete_material_inputs_evidence_ref: Any | None = None
    complete_execution_dimensions_evidence_ref: Any | None = None
    semantic_state_contract_ref: Any | None = None
    schema_version: str = CORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.manifest_id, "manifest_id")
        if type(self.target_revision_ref) is not OperationalRevisionRef:
            raise ProductionStateValidationError("reconstruction target must be an exact M06 revision ref")
        if not isinstance(self.method, ReconstructionMethod):
            object.__setattr__(self, "method", ReconstructionMethod(self.method))
        inputs = require_sequence(self.exact_input_refs, "exact_input_refs", maximum=DEFAULT_LIMITS.max_dependencies)
        for index, value in enumerate(inputs):
            require_exact_ref(value, f"exact_input_refs[{index}]")
        object.__setattr__(self, "exact_input_refs", inputs)
        if len(self.dependency_fingerprint) != 64 or any(char not in "0123456789abcdef" for char in self.dependency_fingerprint):
            raise ProductionStateValidationError("dependency_fingerprint must be a sha256 digest")
        for field in ("workflow_ref", "model_ref", "toolchain_ref"):
            value = getattr(self, field)
            if value is not None:
                require_exact_ref(value, field)
        facts = require_sequence(self.material_environment_facts, "material_environment_facts", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
        normalized: list[tuple[str, str]] = []
        for item in facts:
            if type(item) is not tuple or len(item) != 2:
                raise ProductionStateValidationError("environment facts must be key/value text pairs")
            normalized.append((require_identifier(item[0], "environment fact key"), require_text(item[1], "environment fact value", maximum=2048)))
        if len({key for key, _ in normalized}) != len(normalized):
            raise ProductionStateValidationError("material environment fact keys must be unique")
        object.__setattr__(self, "material_environment_facts", tuple(sorted(normalized)))
        policies = require_sequence(self.policy_refs, "policy_refs", maximum=DEFAULT_LIMITS.max_dependencies)
        for index, value in enumerate(policies):
            require_exact_ref(value, f"policy_refs[{index}]")
        object.__setattr__(self, "policy_refs", policies)
        if not isinstance(self.expected_class, ReproducibilityClass):
            object.__setattr__(self, "expected_class", ReproducibilityClass(self.expected_class))
        if self.equivalence_contract_ref is not None:
            require_exact_ref(self.equivalence_contract_ref, "equivalence_contract_ref")
        if self.seed is not None:
            require_text(self.seed, "seed", maximum=512)
        for field in ("complete_material_inputs_evidence_ref", "complete_execution_dimensions_evidence_ref", "semantic_state_contract_ref"):
            value = getattr(self, field)
            if value is not None:
                require_exact_ref(value, field)
        require_version(self.schema_version, "schema_version")
        if self.method is ReconstructionMethod.RESTORE_RETAINED and not any(type(value) is MaterializationRef for value in inputs):
            raise ProductionStateAdmissionError("retained restoration must bind an exact retained materialization input")
        if self.expected_class is ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT and self.equivalence_contract_ref is None:
            raise ProductionStateAdmissionError("equivalence-class reconstruction requires an explicit versioned equivalence contract")
        if self.expected_class is ReproducibilityClass.EXACT_SEMANTIC_STATE and self.semantic_state_contract_ref is None:
            raise ProductionStateAdmissionError("exact semantic-state reconstruction requires an explicit versioned semantic-state contract")
        if self.expected_class is ReproducibilityClass.EXACT_BYTES and self.method is ReconstructionMethod.REGENERATE:
            if self.workflow_ref is None or self.model_ref is None or self.toolchain_ref is None:
                raise ProductionStateAdmissionError("regeneration cannot claim exact bytes with mutable or unpinned execution refs")
            if self.complete_material_inputs_evidence_ref is None or self.complete_execution_dimensions_evidence_ref is None:
                raise ProductionStateAdmissionError("exact-byte regeneration requires positive completeness evidence for material inputs and execution dimensions")


@dataclass(frozen=True)
class DivergenceEvidence(CanonicalRecord):
    kind: DivergenceKind
    expected_digest: ContentDigest | None
    achieved_digest: ContentDigest | None
    evidence_ref: Any
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, DivergenceKind):
            object.__setattr__(self, "kind", DivergenceKind(self.kind))
        for field in ("expected_digest", "achieved_digest"):
            value = getattr(self, field)
            if value is not None and type(value) is not ContentDigest:
                raise ProductionStateValidationError(f"{field} must be exact digest evidence or None")
        require_exact_ref(self.evidence_ref, "evidence_ref")
        require_text(self.detail, "detail", maximum=4096, allow_empty=True)
        if self.kind is DivergenceKind.BYTE_DIVERGENCE and (
            self.expected_digest is None or self.achieved_digest is None or self.expected_digest == self.achieved_digest
        ):
            raise ProductionStateIntegrityError("byte divergence must bind two different known digests")
        if self.kind is DivergenceKind.NONE_PROVEN and self.expected_digest != self.achieved_digest:
            raise ProductionStateIntegrityError("no-divergence proof requires equal explicit digests")
        if self.kind is DivergenceKind.NONE_PROVEN and (self.expected_digest is None or self.achieved_digest is None):
            raise ProductionStateAdmissionError("no-divergence proof requires two explicit verified digests")


@dataclass(frozen=True)
class ReproducibilityReceipt(CanonicalRecord):
    receipt_id: str
    manifest: ReconstructionManifest
    achieved_class: ReproducibilityClass
    output_revision_ref: OperationalRevisionRef | None
    output_materialization_ref: MaterializationRef | None
    divergence: DivergenceEvidence
    evidence_refs: tuple[Any, ...]
    recorded_at_ms: int
    current_rights_authorized: bool
    current_security_authorized: bool
    quality_admission_ref: Any | None
    semantic_state_verification_ref: Any | None = None
    equivalence_verification_ref: Any | None = None

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        if type(self.manifest) is not ReconstructionManifest or type(self.divergence) is not DivergenceEvidence:
            raise ProductionStateValidationError("reproducibility receipt requires exact manifest and divergence evidence")
        if not isinstance(self.achieved_class, ReproducibilityClass):
            object.__setattr__(self, "achieved_class", ReproducibilityClass(self.achieved_class))
        if self.output_revision_ref is not None and type(self.output_revision_ref) is not OperationalRevisionRef:
            raise ProductionStateValidationError("output revision must be an exact M06 revision ref or None")
        if self.output_materialization_ref is not None and type(self.output_materialization_ref) is not MaterializationRef:
            raise ProductionStateValidationError("output materialization must be an exact M06 materialization ref or None")
        if self.output_materialization_ref is not None and self.output_materialization_ref.revision_ref != self.output_revision_ref:
            raise ProductionStateIntegrityError("output revision and materialization bindings do not match")
        refs = require_sequence(self.evidence_refs, "evidence_refs", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
        for index, ref in enumerate(refs):
            require_exact_ref(ref, f"evidence_refs[{index}]")
        object.__setattr__(self, "evidence_refs", refs)
        if type(self.recorded_at_ms) is not int or self.recorded_at_ms < 0:
            raise ProductionStateValidationError("recorded_at_ms must be a nonnegative exact integer")
        for field in ("current_rights_authorized", "current_security_authorized"):
            if type(getattr(self, field)) is not bool:
                raise ProductionStateValidationError(f"{field} must be a boolean")
        if self.quality_admission_ref is not None:
            require_exact_ref(self.quality_admission_ref, "quality_admission_ref")
        if self.semantic_state_verification_ref is not None:
            require_exact_ref(self.semantic_state_verification_ref, "semantic_state_verification_ref")
        if self.equivalence_verification_ref is not None:
            require_exact_ref(self.equivalence_verification_ref, "equivalence_verification_ref")
        if self.divergence.kind is DivergenceKind.UNKNOWN and self.achieved_class is not ReproducibilityClass.UNKNOWN:
            raise ProductionStateAdmissionError("unknown divergence cannot be reported as successful reproducibility")
        if self.achieved_class is ReproducibilityClass.EXACT_BYTES and self.divergence.kind is not DivergenceKind.NONE_PROVEN:
            raise ProductionStateAdmissionError("exact-byte reproducibility requires an explicit no-divergence proof")
        if self.achieved_class is ReproducibilityClass.EXACT_BYTES:
            if self.output_materialization_ref is None:
                raise ProductionStateAdmissionError("exact-byte reproducibility requires an exact output materialization")
            if self.output_materialization_ref.content_digest != self.divergence.achieved_digest:
                raise ProductionStateIntegrityError("exact-byte output materialization digest must match the observed digest")
            if self.manifest.method is ReconstructionMethod.RESTORE_RETAINED:
                retained_digests = {
                    item.content_digest for item in self.manifest.exact_input_refs if type(item) is MaterializationRef
                }
                if self.divergence.expected_digest not in retained_digests:
                    raise ProductionStateIntegrityError("retained restoration must prove the exact retained materialization digest")
        if self.achieved_class is ReproducibilityClass.EXACT_SEMANTIC_STATE:
            if self.manifest.semantic_state_contract_ref is None or self.semantic_state_verification_ref is None:
                raise ProductionStateAdmissionError("exact semantic-state reconstruction requires versioned contract and verification evidence")
            if self.semantic_state_verification_ref not in refs:
                raise ProductionStateAdmissionError("semantic-state verification evidence must be included in receipt evidence refs")
            if self.divergence.kind in {
                DivergenceKind.SEMANTIC_DIVERGENCE,
                DivergenceKind.EQUIVALENCE_CONTRACT_FAILURE,
                DivergenceKind.DEPENDENCY_UNAVAILABLE,
                DivergenceKind.TOOLCHAIN_UNAVAILABLE,
                DivergenceKind.POLICY_BLOCKED,
                DivergenceKind.UNKNOWN,
            }:
                raise ProductionStateAdmissionError("failed or unknown semantic checks cannot support exact semantic-state reconstruction")
        if self.achieved_class is ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT:
            if self.manifest.equivalence_contract_ref is None or self.equivalence_verification_ref is None:
                raise ProductionStateAdmissionError("equivalence reconstruction requires a versioned contract and observed verification evidence")
            if self.equivalence_verification_ref not in refs:
                raise ProductionStateAdmissionError("equivalence verification evidence must be included in receipt evidence refs")
            if self.divergence.kind in {
                DivergenceKind.SEMANTIC_DIVERGENCE,
                DivergenceKind.EQUIVALENCE_CONTRACT_FAILURE,
                DivergenceKind.DEPENDENCY_UNAVAILABLE,
                DivergenceKind.TOOLCHAIN_UNAVAILABLE,
                DivergenceKind.POLICY_BLOCKED,
                DivergenceKind.UNKNOWN,
            }:
                raise ProductionStateAdmissionError("failed or unavailable equivalence checks cannot support successful equivalence")
        if self.achieved_class not in {
            ReproducibilityClass.UNKNOWN,
            ReproducibilityClass.NON_RECONSTRUCTABLE,
            ReproducibilityClass.REFERENCE_RECONSTRUCTABLE,
        }:
            if self.output_revision_ref is None or self.output_revision_ref == self.manifest.target_revision_ref:
                raise ProductionStateAdmissionError("successful reconstruction must append a new operational revision")
        if self.achieved_class is not ReproducibilityClass.UNKNOWN and not (self.current_rights_authorized and self.current_security_authorized):
            raise ProductionStateAdmissionError("successful reconstruction requires current M53/M54 authorization")
        require_bounded_reproducibility(self.manifest.expected_class, self.achieved_class)


@dataclass(frozen=True)
class HistoricalPermissionEvidence(CanonicalRecord):
    historical_permission_ref: Any
    current_rights_ref: Any
    current_security_ref: Any
    current_rights_authorized: bool
    current_security_authorized: bool
    checked_at_ms: int

    def __post_init__(self) -> None:
        for field in ("historical_permission_ref", "current_rights_ref", "current_security_ref"):
            require_exact_ref(getattr(self, field), field)
        if type(self.current_rights_authorized) is not bool or type(self.current_security_authorized) is not bool:
            raise ProductionStateValidationError("current authority outcomes must be booleans")
        if type(self.checked_at_ms) is not int or self.checked_at_ms < 0:
            raise ProductionStateValidationError("checked_at_ms must be a nonnegative exact integer")


_CLASS_STRENGTH = {
    ReproducibilityClass.UNKNOWN: 0,
    ReproducibilityClass.NON_RECONSTRUCTABLE: 0,
    ReproducibilityClass.REFERENCE_RECONSTRUCTABLE: 1,
    ReproducibilityClass.STOCHASTIC_REEXECUTABLE: 2,
    ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT: 3,
    ReproducibilityClass.EXACT_SEMANTIC_STATE: 4,
    ReproducibilityClass.EXACT_BYTES: 5,
}


def require_bounded_reproducibility(expected: ReproducibilityClass, achieved: ReproducibilityClass) -> None:
    if not isinstance(expected, ReproducibilityClass):
        expected = ReproducibilityClass(expected)
    if not isinstance(achieved, ReproducibilityClass):
        achieved = ReproducibilityClass(achieved)
    if expected is ReproducibilityClass.UNKNOWN and achieved is not ReproducibilityClass.UNKNOWN:
        raise ProductionStateAdmissionError("unknown expected reproducibility cannot support a stronger achieved claim")
    if expected is ReproducibilityClass.NON_RECONSTRUCTABLE and achieved not in {ReproducibilityClass.NON_RECONSTRUCTABLE, ReproducibilityClass.UNKNOWN}:
        raise ProductionStateAdmissionError("non-reconstructable expectation cannot support a reconstruction claim")
    if achieved is not ReproducibilityClass.UNKNOWN and _CLASS_STRENGTH[achieved] > _CLASS_STRENGTH[expected]:
        raise ProductionStateAdmissionError("achieved reproducibility cannot exceed the manifest's admitted expectation")


def classify_reconstruction(receipt: ReproducibilityReceipt) -> DivergenceKind:
    if type(receipt) is not ReproducibilityReceipt:
        raise ProductionStateValidationError("receipt must be an exact ReproducibilityReceipt")
    return receipt.divergence.kind


def validate_historical_permission(evidence: HistoricalPermissionEvidence) -> HistoricalPermissionEvidence:
    if type(evidence) is not HistoricalPermissionEvidence:
        raise ProductionStateValidationError("permission evidence must be an exact immutable M06 record")
    if not evidence.current_rights_authorized or not evidence.current_security_authorized:
        raise ProductionStateAdmissionError("historical permission cannot bypass current M53/M54 authority")
    return evidence
