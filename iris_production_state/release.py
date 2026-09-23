"""Immutable operational closure capsules for M02 release and archive lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from iris_project_os.build import BuildPlan
from iris_project_os.release import ReleaseTransaction
from iris_project_os.snapshots import Snapshot

from .base import CanonicalRecord, require_exact_ref, require_sequence
from .enums import IntegrityState, ReleaseClosureState
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS
from .revisions import IntegrityReceipt, MasterManifest
from .versions import CORE_SCHEMA_VERSION, require_identifier, require_version

__all__ = ["ReleaseStateCapsule", "ReleaseSupersessionReceipt", "validate_release_state_closure"]


@dataclass(frozen=True)
class ReleaseStateCapsule(CanonicalRecord):
    capsule_id: str
    transaction: ReleaseTransaction
    release_snapshot: Snapshot
    build_plan: BuildPlan
    master_manifest: MasterManifest
    dependency_fingerprint: str
    integrity_receipts: tuple[IntegrityReceipt, ...]
    current_authority_refs: tuple[Any, ...]
    state: ReleaseClosureState
    recorded_at_ms: int
    schema_version: str = CORE_SCHEMA_VERSION
    supersedes_capsule_id: str | None = None

    def __post_init__(self) -> None:
        require_identifier(self.capsule_id, "capsule_id")
        if type(self.transaction) is not ReleaseTransaction or type(self.release_snapshot) is not Snapshot or type(self.build_plan) is not BuildPlan:
            raise ProductionStateValidationError("release capsule requires exact M02 transaction, snapshot and build plan")
        if type(self.master_manifest) is not MasterManifest:
            raise ProductionStateValidationError("release capsule requires an exact immutable M06 master manifest")
        if len(self.dependency_fingerprint) != 64 or any(char not in "0123456789abcdef" for char in self.dependency_fingerprint):
            raise ProductionStateValidationError("dependency_fingerprint must be sha256")
        integrity = require_sequence(self.integrity_receipts, "integrity_receipts", maximum=DEFAULT_LIMITS.max_records, item_type=IntegrityReceipt)
        object.__setattr__(self, "integrity_receipts", integrity)
        authorities = require_sequence(self.current_authority_refs, "current_authority_refs", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
        for index, value in enumerate(authorities):
            require_exact_ref(value, f"current_authority_refs[{index}]")
        object.__setattr__(self, "current_authority_refs", authorities)
        if not isinstance(self.state, ReleaseClosureState):
            object.__setattr__(self, "state", ReleaseClosureState(self.state))
        if type(self.recorded_at_ms) is not int or self.recorded_at_ms < 0:
            raise ProductionStateValidationError("recorded_at_ms must be a nonnegative exact integer")
        require_version(self.schema_version, "schema_version")
        if self.supersedes_capsule_id is not None:
            require_identifier(self.supersedes_capsule_id, "supersedes_capsule_id")
            if self.supersedes_capsule_id == self.capsule_id:
                raise ProductionStateIntegrityError("release capsule cannot supersede itself")
        if self.transaction.release_snapshot_id != self.release_snapshot.snapshot_id:
            raise ProductionStateIntegrityError("release transaction and snapshot must bind the same immutable snapshot id")
        if self.state is ReleaseClosureState.CLOSED:
            self._require_closed_evidence()

    def _require_closed_evidence(self) -> None:
        checked = {
            item.materialization_ref
            for item in self.integrity_receipts
            if item.state is IntegrityState.VERIFIED
        }
        if any(item not in checked for item in self.master_manifest.materializations):
            raise ProductionStateAdmissionError("closed release state requires verified integrity for every master materialization")
        if not self.current_authority_refs:
            raise ProductionStateAdmissionError("closed release state requires current external authority refs")
        if self.build_plan.blocked:
            raise ProductionStateAdmissionError("M06 cannot close operational release state while its M02 build plan has blocked nodes")


@dataclass(frozen=True)
class ReleaseSupersessionReceipt(CanonicalRecord):
    receipt_id: str
    previous_capsule_id: str
    new_capsule: ReleaseStateCapsule
    correction_ref: Any
    recorded_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        require_identifier(self.previous_capsule_id, "previous_capsule_id")
        if type(self.new_capsule) is not ReleaseStateCapsule or self.new_capsule.supersedes_capsule_id != self.previous_capsule_id:
            raise ProductionStateIntegrityError("release correction must create a new capsule explicitly superseding the prior one")
        require_exact_ref(self.correction_ref, "correction_ref")
        if type(self.recorded_at_ms) is not int or self.recorded_at_ms < 0:
            raise ProductionStateValidationError("recorded_at_ms must be a nonnegative exact integer")


def validate_release_state_closure(capsule: ReleaseStateCapsule) -> ReleaseStateCapsule:
    if type(capsule) is not ReleaseStateCapsule:
        raise ProductionStateValidationError("capsule must be an exact immutable ReleaseStateCapsule")
    if capsule.state is not ReleaseClosureState.CLOSED:
        raise ProductionStateAdmissionError("incomplete release capsule cannot be represented as a closed operational release")
    # The capsule records state only; M02 promotes/releases and M59 publishes/delivers.
    return capsule
