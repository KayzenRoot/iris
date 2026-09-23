"""Cross-record conformance checks and explicit frozen-catalog validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import CanonicalRecord, require_sequence
from .dependencies import ImpactConeReceipt, ReverseDependencyIndex, validate_impact_cone
from .enums import CleanupState, DeletionAuthorizationState, IndexState, ReleaseClosureState
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateValidationError
from .families import M06_FAMILIES, validate_family_catalog
from .invariants import M06_INVARIANTS, validate_invariant_catalog
from .lineage import CleanupEligibilityReceipt, DeletionAuthorizationReceipt, LineageGraph
from .ports import M06_PORTS, validate_port_catalog
from .reconstruction import ReproducibilityReceipt, require_bounded_reproducibility
from .regeneration import ReuseAdmissionReceipt
from .release import ReleaseStateCapsule
from .revisions import IntegrityReceipt, MasterManifest, validate_master_admission
from .versions import CONTRACT_VERSION, VALIDATOR_VERSION, require_version

__all__ = [
    "ValidationFinding",
    "KernelValidationReport",
    "validate_kernel_catalog",
    "validate_master",
    "validate_impact",
    "validate_reuse",
    "validate_reproducibility",
    "validate_cleanup_eligibility",
    "validate_deletion_authorization",
    "validate_release_capsule",
]


@dataclass(frozen=True)
class ValidationFinding(CanonicalRecord):
    code: str
    subject: str
    message: str


@dataclass(frozen=True)
class KernelValidationReport(CanonicalRecord):
    contract_version: str
    validator_version: str
    family_count: int
    invariant_count: int
    port_count: int
    findings: tuple[ValidationFinding, ...]

    def __post_init__(self) -> None:
        require_version(self.contract_version, "contract_version")
        require_version(self.validator_version, "validator_version")
        findings = require_sequence(self.findings, "findings", maximum=1000, item_type=ValidationFinding)
        object.__setattr__(self, "findings", findings)
        for field in ("family_count", "invariant_count", "port_count"):
            if type(getattr(self, field)) is not int or getattr(self, field) < 0:
                raise ProductionStateValidationError(f"{field} must be a nonnegative exact integer")

    @property
    def valid(self) -> bool:
        return not self.findings and (self.family_count, self.invariant_count, self.port_count) == (25, 150, 20)


def validate_kernel_catalog() -> KernelValidationReport:
    findings: list[ValidationFinding] = []
    try:
        validate_family_catalog()
    except Exception as error:
        findings.append(ValidationFinding("FAMILY_CATALOG_INVALID", "families", str(error)))
    try:
        validate_invariant_catalog()
    except Exception as error:
        findings.append(ValidationFinding("INVARIANT_CATALOG_INVALID", "invariants", str(error)))
    try:
        validate_port_catalog()
    except Exception as error:
        findings.append(ValidationFinding("PORT_CATALOG_INVALID", "ports", str(error)))
    proof_targets = {item.proof_method for item in M06_FAMILIES}
    invariant_targets = {item.proof_target for item in M06_INVARIANTS}
    if not invariant_targets.issubset(proof_targets | {
        "test_s01_revision_master_invariants", "test_s02_dependency_impact_invariants", "test_s03_selective_rebuild_invariants",
        "test_s04_reconstruction_invariants", "test_s05_rollback_cleanup_release_invariants",
    }):
        findings.append(ValidationFinding("PROOF_TARGET_UNBOUND", "invariants", "one or more hard invariants lack an executable test target"))
    return KernelValidationReport(CONTRACT_VERSION, VALIDATOR_VERSION, len(M06_FAMILIES), len(M06_INVARIANTS), len(M06_PORTS), tuple(findings))


def validate_master(
    manifest: MasterManifest,
    *,
    m02_admission_ref: Any,
    quality_evidence_ref: Any,
    integrity_receipts: tuple[IntegrityReceipt, ...],
) -> MasterManifest:
    return validate_master_admission(
        manifest,
        m02_admission_ref=m02_admission_ref,
        quality_evidence_ref=quality_evidence_ref,
        integrity_receipts=integrity_receipts,
    )


def validate_impact(receipt: ImpactConeReceipt, index: ReverseDependencyIndex) -> ImpactConeReceipt:
    if type(receipt) is not ImpactConeReceipt or type(index) is not ReverseDependencyIndex:
        raise ProductionStateValidationError("impact validation requires exact immutable receipt and index")
    return validate_impact_cone(receipt, index)


def validate_reuse(receipt: ReuseAdmissionReceipt) -> ReuseAdmissionReceipt:
    if type(receipt) is not ReuseAdmissionReceipt:
        raise ProductionStateValidationError("reuse validation requires an exact immutable admission receipt")
    if not receipt.evidence_refs:
        raise ProductionStateAdmissionError("reuse receipt must retain positive evidence refs")
    if receipt.equivalence.value != "PROVEN":
        raise ProductionStateAdmissionError("reuse receipt lacks positive equivalence proof")
    return receipt


def validate_reproducibility(receipt: ReproducibilityReceipt) -> ReproducibilityReceipt:
    if type(receipt) is not ReproducibilityReceipt:
        raise ProductionStateValidationError("reproducibility validation requires an exact immutable receipt")
    require_bounded_reproducibility(receipt.manifest.expected_class, receipt.achieved_class)
    if receipt.achieved_class.value != "UNKNOWN" and not (receipt.current_rights_authorized and receipt.current_security_authorized):
        raise ProductionStateAdmissionError("successful reconstruction requires current rights and security authorization")
    return receipt


def validate_cleanup_eligibility(receipt: CleanupEligibilityReceipt, graph: LineageGraph) -> CleanupEligibilityReceipt:
    if type(receipt) is not CleanupEligibilityReceipt or type(graph) is not LineageGraph:
        raise ProductionStateValidationError("cleanup validation requires exact eligibility receipt and lineage graph")
    if (receipt.graph_id, receipt.graph_epoch, receipt.graph_fingerprint) != (graph.graph_id, graph.epoch, graph.fingerprint):
        raise ProductionStateIntegrityError("cleanup receipt is bound to a different lineage graph or epoch")
    if graph.state is not IndexState.COMPLETE_FRESH and receipt.state is CleanupState.ELIGIBLE:
        raise ProductionStateAdmissionError("partial, stale or corrupt lineage graph cannot prove cleanup eligibility")
    if receipt.state is CleanupState.ELIGIBLE and (receipt.reachable_paths or receipt.active_retention_pin_refs):
        raise ProductionStateIntegrityError("eligible cleanup receipt contains a protected path or active pin")
    return receipt


def validate_deletion_authorization(receipt: DeletionAuthorizationReceipt, graph: LineageGraph) -> DeletionAuthorizationReceipt:
    if type(receipt) is not DeletionAuthorizationReceipt:
        raise ProductionStateValidationError("deletion validation requires an exact M06 authorization receipt")
    validate_cleanup_eligibility(receipt.eligibility, graph)
    if receipt.state is DeletionAuthorizationState.AUTHORIZED and receipt.eligibility.state is not CleanupState.ELIGIBLE:
        raise ProductionStateAdmissionError("deletion authorization must bind a current positive eligibility receipt")
    return receipt


def validate_release_capsule(capsule: ReleaseStateCapsule) -> ReleaseStateCapsule:
    if type(capsule) is not ReleaseStateCapsule:
        raise ProductionStateValidationError("release validation requires an exact immutable capsule")
    if capsule.state is not ReleaseClosureState.CLOSED:
        raise ProductionStateAdmissionError("release capsule remains operationally incomplete")
    capsule._require_closed_evidence()
    return capsule
