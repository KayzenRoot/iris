"""Deterministic evidence projection for M09 qualification and independent audit."""

from __future__ import annotations

from dataclasses import dataclass

from .families import validate_surface_catalog
from .invariants import validate_invariant_catalog
from .model import content_digest, require_id
from .schema import M09_CONTRACT_VERSION

__all__ = ["EvidenceBundle", "create_evidence_bundle", "verify_evidence_bundle"]


@dataclass(frozen=True)
class EvidenceBundle:
    work_order: str
    contract_version: str
    base_sha: str
    head_sha: str
    changed_files: tuple[str, ...]
    surface_count: int
    absorbed_component_count: int
    invariant_count: int
    invariant_proof_count: int
    invariant_map_digest: str
    schema_version: str
    public_api: tuple[str, ...]
    runtime_dependencies: tuple[str, ...]
    import_boundary_digest: str
    validation_facts: tuple[tuple[str, str, str], ...]
    authority_boundaries: tuple[tuple[str, str], ...]
    synthetic_profiles: tuple[tuple[str, int, bool], ...]
    serialization_digest: str
    migration_digest: str
    round_trip_digest: str
    security_limits: tuple[tuple[str, int], ...]
    context_lock_digest: str
    conflicts_or_failures_fixed: tuple[str, ...]
    risks: tuple[str, ...]
    deferred_ports: tuple[str, ...]
    checkpoint_delta_proposed: str
    bundle_digest: str = ""

    def __post_init__(self) -> None:
        for field in ("work_order", "base_sha", "head_sha", "schema_version", "context_lock_digest"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.contract_version != M09_CONTRACT_VERSION:
            raise ValueError("evidence must bind the frozen M09 contract version")
        if (self.surface_count, self.absorbed_component_count, self.invariant_count, self.invariant_proof_count) != (83, 15, 514, 514):
            raise ValueError("M09 evidence must state the complete catalog/proof counts")
        if any(status not in {"PASS", "FAIL", "PENDING", "NOT_RUN"} for _, status, _ in self.validation_facts):
            raise ValueError("validation evidence status must be explicit")
        material = self.semantic_payload()
        expected = content_digest(material)
        if self.bundle_digest and self.bundle_digest != expected:
            raise ValueError("evidence bundle digest mismatch")
        object.__setattr__(self, "bundle_digest", expected)

    def semantic_payload(self) -> dict[str, object]:
        return {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "bundle_digest"
        }


def create_evidence_bundle(**values: object) -> EvidenceBundle:
    validate_surface_catalog()
    validate_invariant_catalog()
    values.setdefault("contract_version", M09_CONTRACT_VERSION)
    return EvidenceBundle(**values)  # type: ignore[arg-type]


def verify_evidence_bundle(bundle: EvidenceBundle, *, expected_head: str | None = None) -> bool:
    if type(bundle) is not EvidenceBundle or bundle.contract_version != M09_CONTRACT_VERSION:
        raise ValueError("evidence bundle has an unsupported contract")
    if expected_head is not None and bundle.head_sha != expected_head:
        raise ValueError("evidence is not bound to the requested exact head")
    if content_digest(bundle.semantic_payload()) != bundle.bundle_digest:
        raise ValueError("evidence bundle has been modified")
    if not bundle.checkpoint_delta_proposed:
        raise ValueError("evidence must distinguish a proposed checkpoint delta")
    return True
