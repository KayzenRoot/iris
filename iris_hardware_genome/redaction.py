"""Privacy-safe, source-linked capability advertisements."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record, content_digest
from .enums import BackendFamily, EvidenceStrength, FreshnessClass, ObservationState
from .errors import HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .genome import HardwareGenome
from .versions import require_identifier, require_unique, require_version

__all__ = ["RedactionPolicy", "RedactedSubject", "AdvertisedCapability", "RedactedGenomeView", "redact_genome_view"]


@dataclass(frozen=True)
class RedactionPolicy(M07Record):
    policy_id: str
    version: str
    withheld_fact_keys: tuple[str, ...] = ()
    redact_locators: bool = True
    redact_labels: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", require_identifier(self.policy_id, "policy_id"))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        object.__setattr__(self, "withheld_fact_keys", tuple(sorted(require_unique(self.withheld_fact_keys, "withheld_fact_keys", maximum=10_000))))
        for field in ("redact_locators", "redact_labels"):
            if type(getattr(self, field)) is not bool:
                raise HardwareGenomeValidationError(f"{field} must be bool")
            if not getattr(self, field):
                raise HardwareGenomeValidationError("capability advertisement policy must redact locators and display labels")


@dataclass(frozen=True)
class RedactedSubject(M07Record):
    pseudonymous_subject_id: str
    subject_kind: str
    evidence_anchor_count: int
    locator_values_included: bool = False
    display_label_included: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "pseudonymous_subject_id", require_identifier(self.pseudonymous_subject_id, "pseudonymous_subject_id"))
        object.__setattr__(self, "subject_kind", require_identifier(self.subject_kind, "subject_kind"))
        if isinstance(self.evidence_anchor_count, bool) or not isinstance(self.evidence_anchor_count, int) or self.evidence_anchor_count < 0:
            raise HardwareGenomeValidationError("evidence_anchor_count must be a non-negative integer")
        if self.locator_values_included or self.display_label_included:
            raise HardwareGenomeIntegrityError("capability advertisements cannot carry raw locator values or labels")


@dataclass(frozen=True)
class AdvertisedCapability(M07Record):
    pseudonymous_subject_id: str
    backend: BackendFamily
    capability_key: str
    state: ObservationState
    evidence_strength: EvidenceStrength | None
    freshness: FreshnessClass

    def __post_init__(self) -> None:
        for field in ("pseudonymous_subject_id", "capability_key"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.backend) is not BackendFamily or type(self.state) is not ObservationState or type(self.freshness) is not FreshnessClass:
            raise HardwareGenomeValidationError("advertised capability must preserve typed evidence state/freshness")
        if self.evidence_strength is not None and type(self.evidence_strength) is not EvidenceStrength:
            raise HardwareGenomeValidationError("advertised evidence strength must use the closed ladder")


@dataclass(frozen=True)
class RedactedGenomeView(M07Record):
    view_id: str
    source_genome_id: str
    redaction_policy: RedactionPolicy
    subjects: tuple[RedactedSubject, ...]
    capabilities: tuple[AdvertisedCapability, ...]
    preserved_fact_states: tuple[tuple[str, ObservationState, FreshnessClass], ...]
    withheld_fact_keys: tuple[str, ...]
    is_canonical_content_identity: bool = False

    def __post_init__(self) -> None:
        for field in ("view_id", "source_genome_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "redaction_policy", RedactionPolicy.coerce(self.redaction_policy, "redaction_policy"))
        subjects = tuple(RedactedSubject.coerce(item, "subjects[]") for item in self.subjects)
        caps = tuple(AdvertisedCapability.coerce(item, "capabilities[]") for item in self.capabilities)
        object.__setattr__(self, "subjects", tuple(sorted(subjects, key=lambda item: item.pseudonymous_subject_id)))
        object.__setattr__(self, "capabilities", tuple(sorted(caps, key=lambda item: (item.pseudonymous_subject_id, item.backend.value, item.capability_key))))
        states = tuple(self.preserved_fact_states)
        if any(type(key) is not str or type(state) is not ObservationState or type(freshness) is not FreshnessClass for key, state, freshness in states):
            raise HardwareGenomeValidationError("redacted views must preserve typed semantic states and freshness")
        object.__setattr__(self, "preserved_fact_states", tuple(sorted(states, key=lambda item: item[0])))
        object.__setattr__(self, "withheld_fact_keys", tuple(sorted(set(require_identifier(item, "withheld_fact_keys[]") for item in self.withheld_fact_keys))))
        if self.is_canonical_content_identity:
            raise HardwareGenomeIntegrityError("a redacted view cannot claim identity with canonical genome content")


def redact_genome_view(genome: HardwareGenome, policy: RedactionPolicy) -> RedactedGenomeView:
    genome = HardwareGenome.coerce(genome, "genome")
    policy = RedactionPolicy.coerce(policy, "policy")
    pseudonyms = {
        subject.subject_id: f"subject:{content_digest({'genome': genome.genome_id, 'subject': subject.subject_id, 'policy': policy.policy_id, 'version': policy.version})[:32]}"
        for subject in genome.subjects
    }
    subjects = tuple(RedactedSubject(pseudonyms[item.subject_id], item.kind.value, len(item.identity_anchors)) for item in genome.subjects)
    capabilities = tuple(
        AdvertisedCapability(
            pseudonyms[item.subject.subject_id], item.backend, item.capability_key, item.state,
            item.evidence_strength, item.observation.freshness,
        )
        for item in genome.capabilities
        if item.subject.subject_id in pseudonyms
    )
    withheld = set(policy.withheld_fact_keys)
    preserved = tuple(
        (fact.fact_key, fact.observation.state, fact.observation.freshness)
        for fact in genome.facts
        if fact.fact_key not in withheld
    )
    material = {
        "source_genome_id": genome.genome_id,
        "policy": policy,
        "subjects": subjects,
        "capabilities": capabilities,
        "preserved_fact_states": preserved,
        "withheld_fact_keys": tuple(sorted(withheld)),
    }
    return RedactedGenomeView(
        f"m07-redacted:{content_digest(material)}", genome.genome_id, policy, subjects,
        capabilities, preserved, tuple(sorted(withheld)), False,
    )
