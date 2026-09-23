"""Named, versioned consumer projections and reproducibility fingerprints."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record, content_digest
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .evidence import FactEnvelope
from .genome import HardwareGenome
from .versions import FINGERPRINT_VERSION, require_identifier, require_unique, require_version

__all__ = [
    "ProjectionContract", "ProjectionOmission", "ConsumerProjection", "project_genome",
    "validate_projection", "project_to_m06",
]


@dataclass(frozen=True)
class ProjectionContract(M07Record):
    contract_id: str
    version: str
    consumer_id: str
    fact_keys: tuple[str, ...]
    required_fact_keys: tuple[str, ...]
    include_capabilities: bool = False

    def __post_init__(self) -> None:
        for field in ("contract_id", "consumer_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        keys = tuple(sorted(require_unique(self.fact_keys, "fact_keys", maximum=10_000)))
        required = tuple(sorted(require_unique(self.required_fact_keys, "required_fact_keys", maximum=10_000)))
        if not set(required).issubset(keys):
            raise HardwareGenomeValidationError("required projection facts must be explicitly selected")
        object.__setattr__(self, "fact_keys", keys)
        object.__setattr__(self, "required_fact_keys", required)
        if type(self.include_capabilities) is not bool:
            raise HardwareGenomeValidationError("include_capabilities must be bool")


@dataclass(frozen=True)
class ProjectionOmission(M07Record):
    fact_key: str
    reason: str
    captured_in_source: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "fact_key", require_identifier(self.fact_key, "fact_key"))
        reason = require_identifier(self.reason, "reason")
        if reason not in {"NOT_SELECTED_BY_CONTRACT", "NOT_CAPTURED_IN_SOURCE"}:
            raise HardwareGenomeValidationError("projection omission reason must be explicit")
        object.__setattr__(self, "reason", reason)
        if type(self.captured_in_source) is not bool:
            raise HardwareGenomeValidationError("captured_in_source must be bool")
        if self.captured_in_source != (reason == "NOT_SELECTED_BY_CONTRACT"):
            raise HardwareGenomeIntegrityError("projection omission cannot imply a captured fact")


@dataclass(frozen=True)
class ConsumerProjection(M07Record):
    projection_id: str
    fingerprint_version: str
    contract: ProjectionContract
    source_genome_id: str
    source_schema_version: str
    source_registry_version: str
    facts: tuple[FactEnvelope, ...]
    omissions: tuple[ProjectionOmission, ...]
    capability_assertion_ids: tuple[str, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        from .versions import require_digest

        object.__setattr__(self, "projection_id", require_identifier(self.projection_id, "projection_id"))
        object.__setattr__(self, "fingerprint_version", require_version(self.fingerprint_version, "fingerprint_version"))
        object.__setattr__(self, "contract", ProjectionContract.coerce(self.contract, "contract"))
        for field in ("source_genome_id", "source_schema_version", "source_registry_version"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        facts = tuple(FactEnvelope.coerce(item, "facts[]") for item in self.facts)
        omissions = tuple(ProjectionOmission.coerce(item, "omissions[]") for item in self.omissions)
        if len({(item.fact_key, item.observation.subject.subject_id if item.observation.subject else None, item.observation.runtime.runtime_id if item.observation.runtime else None) for item in facts}) != len(facts):
            raise HardwareGenomeIntegrityError("projection fact identities must be unique")
        object.__setattr__(self, "facts", tuple(sorted(facts, key=lambda item: (item.fact_key, item.observation.observation_id))))
        object.__setattr__(self, "omissions", tuple(sorted(omissions, key=lambda item: item.fact_key)))
        object.__setattr__(self, "capability_assertion_ids", tuple(sorted(set(require_identifier(item, "capability_assertion_ids[]") for item in self.capability_assertion_ids))))
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))


def _projection_material(contract: ProjectionContract, genome: HardwareGenome, facts: tuple[FactEnvelope, ...], omissions: tuple[ProjectionOmission, ...], capability_ids: tuple[str, ...]) -> dict[str, object]:
    return {
        "fingerprint_version": FINGERPRINT_VERSION,
        "contract": contract,
        "source_schema_version": str(genome.schema.version),
        "source_registry_version": genome.semantic_registry.version,
        "facts": facts,
        "omissions": omissions,
        "capability_assertion_ids": capability_ids,
    }


def project_genome(genome: HardwareGenome, contract: ProjectionContract) -> ConsumerProjection:
    genome = HardwareGenome.coerce(genome, "genome")
    contract = ProjectionContract.coerce(contract, "contract")
    selected = tuple(item for item in genome.facts if item.fact_key in contract.fact_keys)
    present_keys = {item.fact_key for item in selected}
    source_keys = {item.fact_key for item in genome.facts}
    missing_required = set(contract.required_fact_keys) - source_keys
    if missing_required:
        raise HardwareGenomeAdmissionError(f"projection source lacks required fact keys: {sorted(missing_required)}")
    omitted_by_contract = tuple(
        ProjectionOmission(key, "NOT_SELECTED_BY_CONTRACT", True)
        for key in sorted(source_keys - set(contract.fact_keys))
    )
    not_captured = tuple(
        ProjectionOmission(key, "NOT_CAPTURED_IN_SOURCE", False)
        for key in sorted(set(contract.fact_keys) - present_keys)
    )
    omissions = (*omitted_by_contract, *not_captured)
    capability_ids = tuple(
        item.assertion_id for item in genome.capabilities
        if contract.include_capabilities and item.capability_key in contract.fact_keys
    )
    digest = content_digest(_projection_material(contract, genome, selected, omissions, capability_ids))
    projection_id = f"m07-projection:{digest}"
    return ConsumerProjection(
        projection_id, FINGERPRINT_VERSION, contract, genome.genome_id, str(genome.schema.version),
        genome.semantic_registry.version, selected, omissions, capability_ids, digest,
    )


def validate_projection(projection: ConsumerProjection, genome: HardwareGenome) -> None:
    projection = ConsumerProjection.coerce(projection, "projection")
    expected = project_genome(genome, projection.contract)
    if projection != expected:
        raise HardwareGenomeIntegrityError("consumer projection does not preserve its exact source/contract binding")


def project_to_m06(genome: HardwareGenome, contract: ProjectionContract) -> ConsumerProjection:
    contract = ProjectionContract.coerce(contract, "contract")
    if contract.consumer_id != "M06":
        raise HardwareGenomeAdmissionError("M06 projection requires an explicitly named M06 consumer contract")
    projection = project_genome(genome, contract)
    if any(item.materiality_declared_by != contract.contract_id for item in projection.facts):
        raise HardwareGenomeAdmissionError("M06 reconstruction material requires explicit declaration by the exact projection contract")
    return projection
