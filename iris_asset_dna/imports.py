"""Staged fail-closed package import without persistence or silent canonical overwrite."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .compatibility import DNACompatibilityProfile
from .enums import CompatibilityOutcome, ImportAdmissionState, ImportCollisionOutcome
from .errors import DNAAdmissionError, DNAIntegrityError, DNAAuthorityError, DNAValidationError
from .identity import DNAEnvelope, DNARevisionRef
from .packages import DNAPackageConformanceReport, ReusableDNAPackageManifest
from .versions import content_digest, require_digest, require_identifier, require_text

__all__ = [
    "DNAImportCollision",
    "DNAImportCollisionResolution",
    "DNAImportAdmission",
    "create_import_admission",
    "find_import_collisions",
    "resolve_import_collision",
    "advance_import_admission",
]


@dataclass(frozen=True)
class DNAImportCollision(CanonicalRecord):
    incoming_ref: DNARevisionRef
    existing_ref: DNARevisionRef
    same_dna_id: bool
    reason: str
    resolution_required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.incoming_ref, DNARevisionRef) or not isinstance(self.existing_ref, DNARevisionRef):
            raise DNAValidationError("import collisions require pinned incoming and existing revisions")
        if not isinstance(self.same_dna_id, bool) or self.same_dna_id != (
            self.incoming_ref.dna_id == self.existing_ref.dna_id
        ):
            raise DNAIntegrityError("same_dna_id must reflect the pinned identity refs")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=96).upper())
        if not self.resolution_required:
            raise DNAAdmissionError("import collisions cannot auto-resolve")

    @property
    def collision_digest(self) -> str:
        return content_digest({
            "incoming_ref": self.incoming_ref,
            "existing_ref": self.existing_ref,
            "same_dna_id": self.same_dna_id,
            "reason": self.reason,
        })


@dataclass(frozen=True)
class DNAImportCollisionResolution(CanonicalRecord):
    collision_digest: str
    incoming_ref: DNARevisionRef
    existing_ref: DNARevisionRef
    outcome: ImportCollisionOutcome
    decision_ref: SemanticRef
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    evidence_refs: tuple[SemanticRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "collision_digest", require_digest(self.collision_digest, "collision_digest"))
        if not isinstance(self.incoming_ref, DNARevisionRef) or not isinstance(self.existing_ref, DNARevisionRef):
            raise DNAValidationError("collision resolution must bind incoming and existing pinned revisions")
        if not isinstance(self.outcome, ImportCollisionOutcome):
            object.__setattr__(self, "outcome", ImportCollisionOutcome(self.outcome))
        for name in ("decision_ref", "authority_ref", "policy_ref"):
            if not isinstance(getattr(self, name), SemanticRef):
                raise DNAAuthorityError(f"collision resolution requires {name}")
        if self.decision_ref.owner_module != "m05" or self.authority_ref.owner_module != "m05":
            raise DNAAuthorityError("identity collision decisions remain under M05 governance")
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        same_id = self.incoming_ref.dna_id == self.existing_ref.dna_id
        if self.outcome in {ImportCollisionOutcome.EXACT_DUPLICATE_NOOP, ImportCollisionOutcome.SAME_IDENTITY_CONTINUATION} and not same_id:
            raise DNAIntegrityError("same-identity collision outcome refers to distinct dna_id values")
        if self.outcome in {ImportCollisionOutcome.GOVERNED_EQUIVALENCE, ImportCollisionOutcome.KEEP_DISTINCT} and same_id:
            raise DNAIntegrityError("cross-identity collision outcome refers to the same dna_id")


@dataclass(frozen=True)
class DNAImportAdmission(CanonicalRecord):
    admission_id: str
    package_ref: SemanticRef
    package_digest: str
    state: ImportAdmissionState
    history_refs: tuple[SemanticRef, ...]
    collision_findings: tuple[DNAImportCollision, ...] = ()
    conformance_digest: str | None = None
    compatibility_profile_ref: SemanticRef | None = None
    external_policy_decision_refs: tuple[SemanticRef, ...] = ()
    authority_ref: SemanticRef | None = None
    admission_policy_ref: SemanticRef | None = None
    collision_resolutions: tuple[DNAImportCollisionResolution, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "admission_id", require_identifier(self.admission_id, "admission_id"))
        if not isinstance(self.package_ref, SemanticRef):
            raise DNAValidationError("package_ref must be a SemanticRef")
        from .versions import require_digest
        object.__setattr__(self, "package_digest", require_digest(self.package_digest, "package_digest"))
        if not isinstance(self.state, ImportAdmissionState):
            object.__setattr__(self, "state", ImportAdmissionState(self.state))
        object.__setattr__(self, "history_refs", require_refs(self.history_refs, "history_refs"))
        collisions = tuple(self.collision_findings)
        if any(not isinstance(item, DNAImportCollision) for item in collisions):
            raise DNAValidationError("collision_findings must contain DNAImportCollision records")
        object.__setattr__(self, "collision_findings", tuple(sorted(collisions, key=lambda item: (item.incoming_ref.dna_id, item.existing_ref.dna_id))))
        resolutions = tuple(self.collision_resolutions)
        if any(not isinstance(item, DNAImportCollisionResolution) for item in resolutions):
            raise DNAValidationError("collision_resolutions must contain typed decisions")
        if len({item.collision_digest for item in resolutions}) != len(resolutions):
            raise DNAIntegrityError("import admission has duplicate collision resolutions")
        object.__setattr__(self, "collision_resolutions", tuple(sorted(resolutions, key=lambda item: item.collision_digest)))
        if self.conformance_digest is not None:
            object.__setattr__(self, "conformance_digest", require_digest(self.conformance_digest, "conformance_digest"))
        for name in ("compatibility_profile_ref", "authority_ref", "admission_policy_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, SemanticRef):
                raise DNAValidationError(f"{name} must be a SemanticRef")
        object.__setattr__(self, "external_policy_decision_refs", require_refs(self.external_policy_decision_refs, "external_policy_decision_refs"))
        if any(ref.owner_module not in {"m53", "m54"} for ref in self.external_policy_decision_refs):
            raise DNAAuthorityError("import rights/security decisions remain owned by M53/M54")
        if self.state in {
            ImportAdmissionState.VALIDATED,
            ImportAdmissionState.COMPATIBILITY_CHECKED,
            ImportAdmissionState.POLICY_CHECKED,
            ImportAdmissionState.ADMISSION_PROPOSED,
            ImportAdmissionState.ADMITTED,
        } and self.conformance_digest is None:
            raise DNAAdmissionError("validated import states require a passing package conformance digest")
        if self.state in {
            ImportAdmissionState.COMPATIBILITY_CHECKED,
            ImportAdmissionState.POLICY_CHECKED,
            ImportAdmissionState.ADMISSION_PROPOSED,
            ImportAdmissionState.ADMITTED,
        } and self.compatibility_profile_ref is None:
            raise DNAAdmissionError("compatibility-checked import states require a directional profile ref")
        if self.state in {
            ImportAdmissionState.POLICY_CHECKED,
            ImportAdmissionState.ADMISSION_PROPOSED,
            ImportAdmissionState.ADMITTED,
        } and not self.external_policy_decision_refs:
            raise DNAAuthorityError("policy-checked import states require M53/M54 decision refs")
        if self.state in {ImportAdmissionState.ADMISSION_PROPOSED, ImportAdmissionState.ADMITTED}:
            if self.authority_ref is None or self.admission_policy_ref is None:
                raise DNAAuthorityError("proposed/admitted imports require explicit M05 authority and policy refs")
            if self.authority_ref.owner_module != "m05" or self.admission_policy_ref.owner_module != "m05":
                raise DNAAuthorityError("canonical import admission remains under M05 authority")
        if self.state is ImportAdmissionState.ADMITTED:
            resolved = {item.collision_digest: item for item in self.collision_resolutions}
            if any(item.collision_digest not in resolved for item in self.collision_findings):
                raise DNAAuthorityError("ADMITTED import requires a governed resolution for every identity collision")
            if any(
                (resolved[item.collision_digest].incoming_ref, resolved[item.collision_digest].existing_ref)
                != (item.incoming_ref, item.existing_ref)
                for item in self.collision_findings
            ):
                raise DNAIntegrityError("ADMITTED import collision resolutions must bind the exact revision pairs")
            if set(resolved) != {item.collision_digest for item in self.collision_findings}:
                raise DNAIntegrityError("ADMITTED import contains a resolution for an undeclared collision")
            if any(item.outcome is ImportCollisionOutcome.EXACT_DUPLICATE_NOOP for item in resolved.values()):
                raise DNAAdmissionError("an exact duplicate is a no-op and cannot overwrite or re-admit canonical DNA")


def create_import_admission(manifest: ReusableDNAPackageManifest, *, admission_id: str) -> DNAImportAdmission:
    if not isinstance(manifest, ReusableDNAPackageManifest):
        raise DNAValidationError("manifest must be a ReusableDNAPackageManifest")
    package_ref = SemanticRef(
        "m05", "reusable.package", manifest.package_id, manifest.version,
        content_digest=manifest.package_digest,
    )
    return DNAImportAdmission(
        require_identifier(admission_id, "admission_id"),
        package_ref,
        manifest.package_digest,
        ImportAdmissionState.PARSED,
        (),
    )


def find_import_collisions(
    manifest: ReusableDNAPackageManifest,
    existing_envelopes: tuple[DNAEnvelope, ...],
) -> tuple[DNAImportCollision, ...]:
    if not isinstance(manifest, ReusableDNAPackageManifest):
        raise DNAValidationError("manifest must be a ReusableDNAPackageManifest")
    existing_by_id: dict[str, DNAEnvelope] = {}
    by_fingerprint: dict[str, list[DNAEnvelope]] = {}
    for envelope in existing_envelopes:
        if not isinstance(envelope, DNAEnvelope):
            raise DNAValidationError("existing_envelopes must contain DNAEnvelope records")
        if envelope.identity.dna_id in existing_by_id:
            raise DNAIntegrityError("import collision scan received duplicate canonical dna_id envelopes")
        existing_by_id[envelope.identity.dna_id] = envelope
        by_fingerprint.setdefault(envelope.head.semantic_digest, []).append(envelope)
    for candidates in by_fingerprint.values():
        candidates.sort(key=lambda item: item.identity.dna_id)
    collisions: list[DNAImportCollision] = []
    for entry in manifest.entries:
        envelope = existing_by_id.get(entry.dna_id)
        if envelope is None:
            for candidate in by_fingerprint.get(entry.semantic_fingerprint, ()):
                collisions.append(DNAImportCollision(
                    entry.revision_ref,
                    candidate.head.ref,
                    False,
                    "SEMANTIC_FINGERPRINT_EQUIVALENCE_REVIEW_REQUIRED",
                ))
            continue
        matching = next((revision for revision in envelope.revisions if revision.ref == entry.revision_ref), None)
        if matching is not None:
            reason = "EXACT_REVISION_ALREADY_PRESENT"
        else:
            reason = "CANONICAL_DNA_ID_COLLISION"
        collisions.append(
            DNAImportCollision(entry.revision_ref, envelope.head.ref, True, reason)
        )
    return tuple(sorted(collisions, key=lambda item: (
        item.incoming_ref.dna_id,
        item.existing_ref.dna_id,
        item.incoming_ref.revision_id,
    )))


def advance_import_admission(
    admission: DNAImportAdmission,
    next_state: ImportAdmissionState,
    *,
    conformance: DNAPackageConformanceReport | None = None,
    compatibility: DNACompatibilityProfile | None = None,
    collision_findings: tuple[DNAImportCollision, ...] = (),
    external_policy_decision_refs: tuple[SemanticRef, ...] = (),
    authority_ref: SemanticRef | None = None,
    admission_policy_ref: SemanticRef | None = None,
    collision_resolutions: tuple[DNAImportCollisionResolution, ...] = (),
    reason: str,
) -> DNAImportAdmission:
    if not isinstance(admission, DNAImportAdmission):
        raise DNAValidationError("admission must be a DNAImportAdmission")
    if not isinstance(next_state, ImportAdmissionState):
        next_state = ImportAdmissionState(next_state)
    transitions = {
        ImportAdmissionState.PARSED: {ImportAdmissionState.VALIDATED, ImportAdmissionState.QUARANTINED, ImportAdmissionState.REJECTED},
        ImportAdmissionState.VALIDATED: {ImportAdmissionState.COMPATIBILITY_CHECKED, ImportAdmissionState.QUARANTINED, ImportAdmissionState.REJECTED},
        ImportAdmissionState.COMPATIBILITY_CHECKED: {ImportAdmissionState.POLICY_CHECKED, ImportAdmissionState.QUARANTINED, ImportAdmissionState.REJECTED},
        ImportAdmissionState.POLICY_CHECKED: {ImportAdmissionState.ADMISSION_PROPOSED, ImportAdmissionState.QUARANTINED, ImportAdmissionState.REJECTED},
        ImportAdmissionState.ADMISSION_PROPOSED: {ImportAdmissionState.ADMITTED, ImportAdmissionState.QUARANTINED, ImportAdmissionState.REJECTED},
    }
    if next_state not in transitions.get(admission.state, set()):
        raise DNAAdmissionError(f"invalid DNA import transition {admission.state.value} -> {next_state.value}")
    collisions = tuple(collision_findings) if collision_findings else admission.collision_findings
    resolutions = tuple(collision_resolutions) if collision_resolutions else admission.collision_resolutions
    conformance_digest = admission.conformance_digest
    compatibility_ref = admission.compatibility_profile_ref
    decisions = admission.external_policy_decision_refs
    if next_state is ImportAdmissionState.VALIDATED:
        if conformance is None or not conformance.valid or conformance.package_digest != admission.package_digest:
            raise DNAAdmissionError("VALIDATED import requires a passing conformance report for the exact package")
        conformance_digest = conformance.report_digest
    if next_state is ImportAdmissionState.COMPATIBILITY_CHECKED:
        if compatibility is None:
            raise DNAAdmissionError("COMPATIBILITY_CHECKED requires a directional multi-axis profile")
        if compatibility.outcome in {CompatibilityOutcome.BREAKING, CompatibilityOutcome.INDETERMINATE}:
            raise DNAAdmissionError(f"package compatibility is {compatibility.outcome.value}; quarantine or reject")
        compatibility_ref = SemanticRef(
            "m05", "compatibility.profile", compatibility.profile_id,
            "1", content_digest=content_digest(compatibility),
        )
    if next_state is ImportAdmissionState.POLICY_CHECKED:
        decisions = require_refs(external_policy_decision_refs, "external_policy_decision_refs")
        if not decisions:
            raise DNAAuthorityError("policy check must reference an external authority decision")
        if any(item.owner_module not in {"m53", "m54"} for item in decisions):
            raise DNAAuthorityError("rights/security policy decisions remain owned by M53/M54")
    if next_state is ImportAdmissionState.ADMISSION_PROPOSED:
        if conformance_digest is None or compatibility_ref is None or not decisions:
            raise DNAAdmissionError("admission proposal requires conformance, compatibility and policy evidence")
        if not isinstance(authority_ref, SemanticRef) or not isinstance(admission_policy_ref, SemanticRef):
            raise DNAAuthorityError("admission proposal requires explicit M05 authority and policy refs")
        if authority_ref.owner_module != "m05" or admission_policy_ref.owner_module != "m05":
            raise DNAAuthorityError("import admission proposal remains under M05 authority")
    if next_state is ImportAdmissionState.ADMITTED:
        by_digest = {item.collision_digest: item for item in resolutions}
        for collision in collisions:
            resolution = by_digest.get(collision.collision_digest)
            if resolution is None:
                raise DNAAdmissionError("canonical import collision must be resolved through explicit M05 governance")
            if (resolution.incoming_ref, resolution.existing_ref) != (collision.incoming_ref, collision.existing_ref):
                raise DNAIntegrityError("collision resolution must bind the exact incoming/existing revision pair")
            if resolution.outcome is ImportCollisionOutcome.EXACT_DUPLICATE_NOOP:
                raise DNAAdmissionError("exact duplicate import is a no-op and cannot be admitted again")
        if conformance_digest is None or compatibility_ref is None or not decisions:
            raise DNAAdmissionError("import admission requires conformance, compatibility and policy evidence")
        if not isinstance(authority_ref, SemanticRef) or not isinstance(admission_policy_ref, SemanticRef):
            raise DNAAuthorityError("canonical import requires explicit M05 authority and policy refs")
    event_ref = SemanticRef(
        "m05",
        "import.admission.event",
        f"{admission.admission_id}.{next_state.value.lower()}",
        "1",
        content_digest=content_digest({
            "admission_id": admission.admission_id,
            "from": admission.state.value,
            "to": next_state.value,
            "reason": require_text(reason, "reason", maximum=2048),
        }),
    )
    return DNAImportAdmission(
        admission.admission_id,
        admission.package_ref,
        admission.package_digest,
        next_state,
        admission.history_refs + (event_ref,),
        collisions,
        conformance_digest,
        compatibility_ref,
        decisions,
        authority_ref if authority_ref is not None else admission.authority_ref,
        admission_policy_ref if admission_policy_ref is not None else admission.admission_policy_ref,
        resolutions,
    )


def resolve_import_collision(
    collision: DNAImportCollision,
    *,
    outcome: ImportCollisionOutcome,
    decision_ref: SemanticRef,
    authority_ref: SemanticRef,
    policy_ref: SemanticRef,
    evidence_refs: tuple[SemanticRef, ...] = (),
) -> DNAImportCollisionResolution:
    if not isinstance(collision, DNAImportCollision):
        raise DNAValidationError("collision must be a DNAImportCollision")
    return DNAImportCollisionResolution(
        collision.collision_digest,
        collision.incoming_ref,
        collision.existing_ref,
        outcome,
        decision_ref,
        authority_ref,
        policy_ref,
        require_refs(evidence_refs, "evidence_refs"),
    )
