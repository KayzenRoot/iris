"""Deterministic structural validation reports for M07 snapshots and genomes."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record
from .discovery import DiscoverySnapshot
from .enums import ObservationState
from .errors import HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .families import validate_surface_catalog
from .genome import HardwareGenome, validate_hardware_genome
from .registry import SemanticKeyRegistry, validate_semantic_registry
from .topology import validate_topology_graph
from .versions import VALIDATOR_VERSION, require_identifier, require_version

__all__ = ["ValidationProfile", "ValidationFinding", "ValidationReport", "validate_discovery_snapshot", "validate_genome"]


@dataclass(frozen=True)
class ValidationProfile(M07Record):
    profile_id: str
    version: str
    require_complete_discovery: bool = False
    reject_stale_evidence: bool = False
    required_fact_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        for field in ("require_complete_discovery", "reject_stale_evidence"):
            if type(getattr(self, field)) is not bool:
                raise HardwareGenomeValidationError(f"{field} must be bool")
        from .versions import require_unique

        object.__setattr__(self, "required_fact_keys", require_unique(self.required_fact_keys, "required_fact_keys", maximum=10_000))


@dataclass(frozen=True, order=True)
class ValidationFinding(M07Record):
    finding_id: str
    code: str
    path: str
    severity: str
    message: str

    def __post_init__(self) -> None:
        for field in ("finding_id", "code", "path", "severity"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        from .versions import require_text

        object.__setattr__(self, "message", require_text(self.message, "message", maximum=2_048))
        if self.severity not in {"ERROR", "WARNING", "INFO"}:
            raise HardwareGenomeValidationError("validation finding severity must be ERROR, WARNING or INFO")


@dataclass(frozen=True)
class ValidationReport(M07Record):
    report_id: str
    validator_version: str
    subject_id: str
    findings: tuple[ValidationFinding, ...]
    valid: bool

    def __post_init__(self) -> None:
        for field in ("report_id", "subject_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "validator_version", require_version(self.validator_version, "validator_version"))
        findings = tuple(ValidationFinding.coerce(item, "findings[]") for item in self.findings)
        if len({item.finding_id for item in findings}) != len(findings):
            raise HardwareGenomeIntegrityError("validation finding ids must be unique")
        object.__setattr__(self, "findings", tuple(sorted(findings)))
        if type(self.valid) is not bool or self.valid != (not any(item.severity == "ERROR" for item in findings)):
            raise HardwareGenomeIntegrityError("validation report status differs from its findings")


def validate_discovery_snapshot(snapshot: DiscoverySnapshot, profile: ValidationProfile | None = None) -> ValidationReport:
    snapshot = DiscoverySnapshot.coerce(snapshot, "snapshot")
    resolved_profile = ValidationProfile.coerce(profile or ValidationProfile("default", VALIDATOR_VERSION), "profile")
    findings: list[ValidationFinding] = []
    if resolved_profile.require_complete_discovery and snapshot.completeness is not ObservationState.OBSERVED:
        findings.append(ValidationFinding("discovery-incomplete", "INCOMPLETE", "discovery.completeness", "ERROR", "profile requires complete scoped discovery"))
    fact_keys = {item.fact_key for item in snapshot.observations}
    for missing in sorted(set(resolved_profile.required_fact_keys) - fact_keys):
        findings.append(ValidationFinding(f"missing-{missing.replace('.', '-')}", "REQUIRED_FACT_MISSING", f"facts.{missing}", "ERROR", "required fact has no explicit observation"))
    if resolved_profile.reject_stale_evidence and any(item.state is ObservationState.STALE for item in snapshot.observations):
        findings.append(ValidationFinding("stale-evidence", "STALE", "observations", "ERROR", "profile rejects stale discovery evidence"))
    return ValidationReport(f"validation:{snapshot.snapshot_id}", VALIDATOR_VERSION, snapshot.snapshot_id, tuple(findings), not findings)


def validate_genome(
    genome: HardwareGenome,
    *,
    registry: SemanticKeyRegistry | None = None,
    profile: ValidationProfile | None = None,
) -> ValidationReport:
    genome = HardwareGenome.coerce(genome, "genome")
    validate_hardware_genome(genome)
    validate_surface_catalog()
    resolved_registry = SemanticKeyRegistry.coerce(registry, "registry") if registry is not None else genome.semantic_registry
    validate_semantic_registry(resolved_registry)
    if resolved_registry != genome.semantic_registry:
        raise HardwareGenomeIntegrityError("validator semantic registry must match the genome's immutable registry snapshot")
    resolved_profile = ValidationProfile.coerce(profile or ValidationProfile("default", VALIDATOR_VERSION), "profile")
    findings: list[ValidationFinding] = []
    if resolved_profile.require_complete_discovery and genome.discovery.completeness is not ObservationState.OBSERVED:
        findings.append(ValidationFinding("genome-incomplete", "INCOMPLETE", "discovery.completeness", "ERROR", "profile requires complete scoped discovery"))
    facts = {item.fact_key for item in genome.facts}
    for fact in genome.facts:
        definition = resolved_registry.find(fact.fact_key)
        if fact.registry_version != resolved_registry.version:
            findings.append(ValidationFinding(f"registry-version-{fact.observation.observation_id}", "REGISTRY_VERSION_MISMATCH", f"facts.{fact.fact_key}", "ERROR", "fact semantic registry version differs from the validator registry"))
        if definition is None:
            findings.append(ValidationFinding(f"unknown-semantic-key-{fact.observation.observation_id}", "SEMANTIC_KEY_UNKNOWN", f"facts.{fact.fact_key}", "ERROR", "fact key is absent from the core or explicitly governed semantic registry"))
            continue
        if fact.observation.state not in definition.allowed_states:
            findings.append(ValidationFinding(f"semantic-state-{fact.observation.observation_id}", "SEMANTIC_STATE_INVALID", f"facts.{fact.fact_key}", "ERROR", "fact state is not allowed by its semantic definition"))
        if not definition.prefix_match and fact.observation.unit != definition.unit:
            findings.append(ValidationFinding(f"semantic-unit-{fact.observation.observation_id}", "SEMANTIC_UNIT_INVALID", f"facts.{fact.fact_key}", "ERROR", "fact unit differs from its semantic definition"))
        if definition.evidence_required and fact.observation.state is ObservationState.OBSERVED and fact.observation.evidence is None:
            findings.append(ValidationFinding(f"semantic-evidence-{fact.observation.observation_id}", "SEMANTIC_EVIDENCE_MISSING", f"facts.{fact.fact_key}", "ERROR", "semantic definition requires positive evidence"))
    for missing in sorted(set(resolved_profile.required_fact_keys) - facts):
        findings.append(ValidationFinding(f"missing-{missing.replace('.', '-')}", "REQUIRED_FACT_MISSING", f"facts.{missing}", "ERROR", "required fact has no admitted envelope"))
    if resolved_profile.reject_stale_evidence and any(item.state is ObservationState.STALE for item in genome.discovery.observations):
        findings.append(ValidationFinding("stale-genome", "STALE", "discovery.observations", "ERROR", "profile rejects stale evidence"))
    validate_topology_graph(genome.topology)
    return ValidationReport(f"validation:{genome.genome_id}", VALIDATOR_VERSION, genome.genome_id, tuple(findings), not findings)
