"""Área E part 4: the archive contract, its tiers, its integrity audits and its revival fork.

§18 of the module spec defines an archive as a lifecycle state plus a retention contract, and
invariant 24 of the frozen contract says the same thing from the other side: completeness is a
manifest/evidence claim, never a filesystem location. So nothing in this file names a path, a
bucket or a folder. A manifest names the exact refs it stands for, the tier decides which of
those refs the kernel may demand (§19), an audit compares the promise against what could actually
be read (§22), and a reopening forks new lineage instead of editing the old one (§21, D-016).

Three laws do the work.

*A claim is checked against the refs present, never against a label.* ``ARCHIVE_REPRODUCIBLE`` is
refused when a restoration prerequisite carries no asset with a digest, and ``ARCHIVE_LEGAL_HOLD``
is refused when it cannot name the right it holds (§19). A tier is an obligation, so a tier with
nothing behind it is the relabelling mistake the snapshot classes already forbid.

*Damage and cold are different answers.* An object that could not be looked at produces ``UNKNOWN``,
which is not a pass, and an object that comes back with other bytes produces ``DAMAGED``, which no
later quiet audit erases: replacing the bytes of a sealed archive is a new archive under a new id
(§22, D-M02-S05-017).

*A restoration buys availability, not reproducibility.* Metadata that reopened successfully says
nothing about a model version nobody still has, so ``RestorationReport`` refuses to claim full
reproducibility while a prerequisite is missing, unreadable or contradicted by the audit (§20,
D-M02-S05-016).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .base import Labeled, Record, of
from .branching import RetentionPin
from .errors import ArchiveError, SchemaValidationError, StoreConflictError
from .identity import EntityKind, ExternalRef, new_id, require_id
from .lifecycle import Phase, ProductionLedger, initial_vector, phase_at_least
from .limits import (
    MAX_ARCHIVE_REFS,
    MAX_BUNDLE_ITEMS,
    MAX_RECEIPT_EVIDENCE,
    MAX_REVIVAL_OBLIGATIONS,
)
from .snapshots import Snapshot, SnapshotClass
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    require_bounded,
    require_component_version,
    require_digest,
    require_identifier,
    require_millis,
    require_optional_text,
    require_supported_version,
)

__all__ = [
    "ArchiveTier",
    "AssetRole",
    "StorageClass",
    "ProbeState",
    "RiskKind",
    "DamageKind",
    "IntegrityOutcome",
    "ArchiveRetention",
    "ArchiveObject",
    "AvailabilityRisk",
    "ArchiveManifest",
    "ObjectProbe",
    "IntegrityFinding",
    "IntegrityReport",
    "RestorationReport",
    "RevivalReceipt",
    "CleanupDecision",
    "CleanupPlan",
    "ArchiveLedger",
    "ArchiveRegistry",
    "audit_archive",
    "restore_archive",
    "revive_archive",
    "seal_archive",
]

class ArchiveTier(Labeled):
    """§19's four retention contracts. Each one is a demand on the manifest, not a folder name."""

    ARCHIVE_LIGHT = "ARCHIVE_LIGHT"
    ARCHIVE_REPRODUCIBLE = "ARCHIVE_REPRODUCIBLE"
    ARCHIVE_LEGAL_HOLD = "ARCHIVE_LEGAL_HOLD"
    ARCHIVE_GOLDEN = "ARCHIVE_GOLDEN"

    @property
    def omits_recomputables(self) -> bool:
        """Only LIGHT may leave recomputable intermediates out, and never the final artifacts."""

        return self is ArchiveTier.ARCHIVE_LIGHT

    @property
    def owes_asset_completeness(self) -> bool:
        """Whether every restoration prerequisite has to be an archived object with a digest."""

        return self in {ArchiveTier.ARCHIVE_REPRODUCIBLE, ArchiveTier.ARCHIVE_GOLDEN}

    @property
    def overrides_gc(self) -> bool:
        """§19: a legal hold overrides ordinary GC, and golden material is pinned by definition."""

        return self in {ArchiveTier.ARCHIVE_LEGAL_HOLD, ArchiveTier.ARCHIVE_GOLDEN}

    @property
    def owes_rights_evidence(self) -> bool:
        return self is ArchiveTier.ARCHIVE_LEGAL_HOLD


class AssetRole(Labeled):
    """Whether an archived object is the work, or something the work needed."""

    FINAL = "FINAL"
    INPUT = "INPUT"


class StorageClass(Labeled):
    """§20's materialisation answer: where the bytes are, stated as availability and nothing else."""

    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"
    OFFLINE = "OFFLINE"

    @property
    def needs_recall(self) -> bool:
        return self in {StorageClass.COLD, StorageClass.OFFLINE}

    @property
    def is_offloaded(self) -> bool:
        return self is StorageClass.OFFLINE


class ProbeState(Labeled):
    """What an inspection could actually see. ``UNREADABLE`` is deliberately not ``ABSENT``."""

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNREADABLE = "UNREADABLE"


class RiskKind(Labeled):
    """§20's named obstacles: availability facts the archive records but cannot itself settle."""

    EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"
    TOOL_VERSION = "TOOL_VERSION"
    MODEL_VERSION = "MODEL_VERSION"
    RIGHTS = "RIGHTS"

    @property
    def blocks_reproduction(self) -> bool:
        return self in {
            RiskKind.EXTERNAL_DEPENDENCY,
            RiskKind.TOOL_VERSION,
            RiskKind.MODEL_VERSION,
        }

    @property
    def blocks_use(self) -> bool:
        return self is RiskKind.RIGHTS


class DamageKind(Labeled):
    """§22's findings. Anything unverifiable is reported, and only ``UNVERIFIABLE`` spares a pass."""

    MISSING_OBJECT = "MISSING_OBJECT"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    UNREACHABLE_REFERENCE = "UNREACHABLE_REFERENCE"
    UNCITED_BLOCK = "UNCITED_BLOCK"
    UNVERIFIABLE = "UNVERIFIABLE"

    @property
    def damages(self) -> bool:
        return self is not DamageKind.UNVERIFIABLE


class IntegrityOutcome(Labeled):
    INTACT = "INTACT"
    DAMAGED = "DAMAGED"
    UNKNOWN = "UNKNOWN"

    @property
    def may_claim_complete(self) -> bool:
        """Only INTACT is a pass; §22 forbids a silent success over an archive nobody could read."""

        return self is IntegrityOutcome.INTACT


class ArchiveRetention(Labeled):
    """Why an archive may not be collected, one name per holding claim."""

    TIER_LEGAL_HOLD = "TIER_LEGAL_HOLD"
    TIER_GOLDEN = "TIER_GOLDEN"
    LIVE_PIN = "LIVE_PIN"
    RETENTION_NOT_EXPIRED = "RETENTION_NOT_EXPIRED"
    CITED_BY_REVIVAL = "CITED_BY_REVIVAL"
    OPEN_INTEGRITY_FINDING = "OPEN_INTEGRITY_FINDING"


def _freeze_refs(value: Iterable[Any], *, field: str, maximum: int = MAX_ARCHIVE_REFS) -> tuple[ExternalRef, ...]:
    collected = require_bounded(tuple(value), field, maximum=maximum, kind="reference")
    unique = {ExternalRef.coerce(item, f"{field}[]") for item in collected}
    return tuple(sorted(unique, key=lambda item: item.text))


def _freeze_ids(value: Iterable[Any], *, field: str, maximum: int = MAX_ARCHIVE_REFS) -> tuple[str, ...]:
    collected = require_bounded(tuple(value), field, maximum=maximum, kind="id")
    return tuple(sorted({require_id(item, f"{field}[]") for item in collected}))


def _snapshot_identity(snapshot: Any) -> str:
    """Which canonical snapshot an archive closes over, from a ``Snapshot`` or a reference to one."""

    if isinstance(snapshot, Snapshot):
        return snapshot.snapshot_id
    reference = ExternalRef.coerce(snapshot, "snapshot")
    if reference.kind is not EntityKind.SNAPSHOT:
        raise ArchiveError(
            f"{reference.text} is a {reference.kind.value}, not a snapshot; no archive closes over it, so no "
            "archive retains it"
        )
    return reference.reference


@dataclass(frozen=True)
class ArchiveObject(Record):
    """One object the archive promises to still hold, the digest it promises, and where it lives."""

    ref: ExternalRef
    digest: str
    role: AssetRole = AssetRole.FINAL
    storage: StorageClass = StorageClass.HOT

    NESTED = {"ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        if not isinstance(self.ref, ExternalRef):
            raise SchemaValidationError("ref must be an ExternalRef to the archived object")
        if self.ref.kind is EntityKind.SNAPSHOT:
            raise ArchiveError(
                f"{self.ref.text} is a snapshot, not an archived object; the manifest already names the snapshot "
                "this archive closes over, and a digest for it belongs to the audit"
            )
        object.__setattr__(self, "digest", require_digest(self.digest, "digest"))
        object.__setattr__(self, "role", AssetRole.parse(self.role, "role"))
        object.__setattr__(self, "storage", StorageClass.parse(self.storage, "storage"))

    @property
    def needs_recall(self) -> bool:
        return self.storage.needs_recall


@dataclass(frozen=True)
class AvailabilityRisk(Record):
    """A named obstacle to reopening, recorded at seal time rather than discovered at restore time."""

    kind: RiskKind
    subject: ExternalRef
    detail: Any = None

    NESTED = {"subject": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", RiskKind.parse(self.kind, "kind"))
        if not isinstance(self.subject, ExternalRef):
            raise SchemaValidationError("subject must be an ExternalRef to what may be unavailable")
        if self.kind is RiskKind.RIGHTS and self.subject.kind not in {
            EntityKind.RIGHTS,
            EntityKind.POLICY,
            EntityKind.EVIDENCE,
        }:
            raise ArchiveError(
                f"a rights block cannot be filed against {self.subject.text}; name the right or the policy that "
                "blocks use, not the artifact it blocks"
            )
        object.__setattr__(self, "detail", require_optional_text(self.detail, "detail", maximum=512))

    @property
    def blocks_reproduction(self) -> bool:
        return self.kind.blocks_reproduction

    @property
    def blocks_use(self) -> bool:
        return self.kind.blocks_use


@dataclass(frozen=True)
class ArchiveManifest(Record):
    """§18's binding: which canonical snapshot, which evidence, which tier, and what reopening needs.

    The refs are carried instead of pointed at from a store path because the archive outlives every
    store that held it. What a manifest may *claim* is derived from the refs it actually carries, so
    the tier cannot be typed in ahead of the evidence — the same law that makes a
    ``VALIDATED_SNAPSHOT`` impossible without the decisions that validate it.
    """

    archive_id: str
    project_id: str
    production_id: str
    snapshot_ref: ExternalRef
    graph_revision_id: str
    tier: ArchiveTier = ArchiveTier.ARCHIVE_LIGHT
    intent_ref: Any = None
    release_refs: tuple[ExternalRef, ...] = ()
    provenance_refs: tuple[ExternalRef, ...] = ()
    rights_refs: tuple[ExternalRef, ...] = ()
    quality_refs: tuple[ExternalRef, ...] = ()
    policy_refs: tuple[ExternalRef, ...] = ()
    assets: tuple[ArchiveObject, ...] = ()
    restoration_prerequisites: tuple[ExternalRef, ...] = ()
    risks: tuple[AvailabilityRisk, ...] = ()
    pins: tuple[RetentionPin, ...] = ()
    retention_expires_at_ms: int = 0
    sealed_by: Any = None
    sealed_at_ms: int = 0
    evidence_refs: tuple[ExternalRef, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "snapshot_ref": of(ExternalRef),
        "intent_ref": of(ExternalRef),
        "release_refs": of(ExternalRef),
        "provenance_refs": of(ExternalRef),
        "rights_refs": of(ExternalRef),
        "quality_refs": of(ExternalRef),
        "policy_refs": of(ExternalRef),
        "restoration_prerequisites": of(ExternalRef),
        "assets": of(ArchiveObject),
        "risks": of(AvailabilityRisk),
        "pins": of(RetentionPin),
        "evidence_refs": of(ExternalRef),
        "sealed_by": of(ComponentVersion),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "archive_id", require_id(self.archive_id, "archive_id"))
        object.__setattr__(self, "project_id", require_identifier(self.project_id, "project_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "tier", ArchiveTier.parse(self.tier, "tier"))
        if not isinstance(self.snapshot_ref, ExternalRef) or self.snapshot_ref.kind is not EntityKind.SNAPSHOT:
            raise ArchiveError(
                "snapshot_ref must be an ExternalRef of kind SNAPSHOT; an archive that names no canonical "
                "snapshot is a retention policy, not an archive"
            )
        object.__setattr__(self, "graph_revision_id", require_id(self.graph_revision_id, "graph_revision_id"))
        if self.intent_ref is not None:
            object.__setattr__(self, "intent_ref", ExternalRef.coerce(self.intent_ref, "intent_ref"))
        for name in ("release_refs", "provenance_refs", "rights_refs", "quality_refs", "policy_refs"):
            object.__setattr__(self, name, _freeze_refs(getattr(self, name), field=name))
        for name in ("restoration_prerequisites", "evidence_refs"):
            object.__setattr__(self, name, _freeze_refs(getattr(self, name), field=name))
        assets = require_bounded(self.assets, "assets", maximum=MAX_ARCHIVE_REFS, kind="asset")
        resolved = tuple(ArchiveObject.coerce(item, "assets[]") for item in assets)
        keyed: dict[str, ArchiveObject] = {}
        for item in resolved:
            clash = keyed.get(item.ref.text)
            if clash is not None and clash.digest != item.digest:
                raise ArchiveError(
                    f"{item.ref.text} is archived twice with two digests ({clash.digest[:12]} and "
                    f"{item.digest[:12]}); an archive that contradicts itself about the bytes cannot be audited"
                )
            keyed[item.ref.text] = item
        object.__setattr__(self, "assets", tuple(sorted(keyed.values(), key=lambda item: item.ref.text)))
        risks = require_bounded(self.risks, "risks", maximum=MAX_BUNDLE_ITEMS, kind="risk")
        object.__setattr__(
            self,
            "risks",
            tuple(
                sorted(
                    {AvailabilityRisk.coerce(item, "risks[]") for item in risks},
                    key=lambda item: (item.kind.value, item.subject.text),
                )
            ),
        )
        pins = require_bounded(self.pins, "pins", maximum=MAX_BUNDLE_ITEMS, kind="pin")
        held = {item.text for item in self._pinnable_refs()}
        resolved_pins = []
        for item in pins:
            pin = RetentionPin.coerce(item, "pins[]")
            if pin.target.text not in held:
                raise ArchiveError(
                    f"pin {pin.pin_id} retains {pin.target.text}, which this archive does not hold; a pin on an "
                    "unrelated object keeps that object alive and says nothing about this one"
                )
            resolved_pins.append(pin)
        object.__setattr__(self, "pins", tuple(sorted(resolved_pins, key=lambda item: item.pin_id)))

        if not any(item.role is AssetRole.FINAL for item in self.assets):
            raise ArchiveError(
                f"{self.archive_id} archives no final artifact; §19 lets LIGHT omit recomputable intermediates and "
                "nothing else, because a hold over metadata alone proves the content was never preserved"
            )
        if not self.provenance_refs:
            raise ArchiveError(
                f"{self.archive_id} carries no provenance reference; §18 binds provenance because an archive that "
                "cannot say where the work came from is unusable as evidence"
            )
        if not self.quality_refs:
            raise ArchiveError(
                f"{self.archive_id} carries no M01 quality evidence; the archive is what a later Quality Court "
                "calibrates against, and there is nothing to calibrate here"
            )
        if self.tier.owes_rights_evidence and not self.rights_refs:
            raise ArchiveError(
                f"{self.tier.value} over {self.archive_id} names no right; a legal hold that cannot say what it "
                "holds cannot be honoured by whoever operates the store"
            )
        missing = self.outstanding_prerequisites()
        if missing and self.tier.owes_asset_completeness:
            raise ArchiveError(
                f"{self.tier.value} requires every restoration prerequisite to be archived, and these are not: "
                f"{', '.join(item.text for item in missing)}; either carry them with a digest or seal this as "
                f"{ArchiveTier.ARCHIVE_LIGHT.value}"
            )
        if self.sealed_by is not None:
            object.__setattr__(self, "sealed_by", require_component_version(self.sealed_by, "sealed_by"))
        object.__setattr__(self, "sealed_at_ms", require_millis(self.sealed_at_ms, "sealed_at_ms"))
        object.__setattr__(self, "retention_expires_at_ms", require_millis(self.retention_expires_at_ms, "retention_expires_at_ms"))
        if self.retention_expires_at_ms:
            if self.tier.overrides_gc:
                raise ArchiveError(
                    f"{self.tier.value} cannot carry a retention expiry; {self.archive_id} would expire quietly, "
                    "which is the ordinary GC this tier exists to override"
                )
            if self.retention_expires_at_ms <= self.sealed_at_ms:
                raise ArchiveError(
                    f"retention_expires_at_ms must follow sealed_at_ms on {self.archive_id}"
                )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.ARCHIVE, reference=self.archive_id)

    def _pinnable_refs(self) -> tuple[ExternalRef, ...]:
        return (
            (self.reference, self.snapshot_ref)
            + self.assets_refs()
            + self.provenance_refs
            + self.rights_refs
            + self.quality_refs
            + self.policy_refs
            + self.release_refs
            + self.restoration_prerequisites
        )

    def required_refs(self) -> tuple[ExternalRef, ...]:
        """Every reference §22 says an audit must be able to reach.

        Risk subjects are in here on purpose: a manifest that records "this model version may be
        gone" and then never inspects it is describing a problem it chose not to look at.
        """

        return _freeze_refs(
            (self.snapshot_ref,)
            + self.assets_refs()
            + self.provenance_refs
            + self.quality_refs
            + self.rights_refs
            + self.policy_refs
            + self.restoration_prerequisites
            + tuple(item.subject for item in self.risks),
            field="required_refs",
        )

    def assets_refs(self) -> tuple[ExternalRef, ...]:
        return tuple(item.ref for item in self.assets)

    def object_for(self, reference: Any) -> ArchiveObject | None:
        wanted = ExternalRef.coerce(reference, "reference")
        return next((item for item in self.assets if item.ref == wanted), None)

    def covers(self, reference: Any) -> bool:
        return self.object_for(reference) is not None

    def outstanding_prerequisites(self) -> tuple[ExternalRef, ...]:
        """Prerequisites reopening needs that this manifest carries no archived object for."""

        return tuple(item for item in self.restoration_prerequisites if not self.covers(item))

    def blocking_risks(self, *, for_use: bool = False) -> tuple[AvailabilityRisk, ...]:
        wanted = (lambda item: item.blocks_use) if for_use else (lambda item: item.blocks_reproduction)
        return tuple(item for item in self.risks if wanted(item))

    def revival_obligations(self) -> tuple[ExternalRef, ...]:
        """§21's revalidation list: what a reopening has to re-check before it may run the work again.

        Tools, models and external dependencies because the versions may be gone, policies and rights
        because a hold that was in force at seal time may not be in force now.
        """

        return _freeze_refs(
            self.restoration_prerequisites
            + tuple(item.subject for item in self.risks)
            + self.policy_refs
            + self.rights_refs,
            field="revival_obligations",
        )

    def retention(self, *, now_ms: int = 0) -> tuple[ArchiveRetention, ...]:
        found: set[ArchiveRetention] = set()
        if self.tier is ArchiveTier.ARCHIVE_LEGAL_HOLD:
            found.add(ArchiveRetention.TIER_LEGAL_HOLD)
        if self.tier is ArchiveTier.ARCHIVE_GOLDEN:
            found.add(ArchiveRetention.TIER_GOLDEN)
        if any(not pin.may_release(now_ms) for pin in self.pins):
            found.add(ArchiveRetention.LIVE_PIN)
        if self.retention_expires_at_ms and now_ms <= self.retention_expires_at_ms:
            found.add(ArchiveRetention.RETENTION_NOT_EXPIRED)
        return tuple(sorted(found, key=lambda item: item.value))

    def may_collect(self, *, now_ms: int = 0) -> bool:
        return not self.retention(now_ms=now_ms)


@dataclass(frozen=True)
class ObjectProbe(Record):
    """One inspection result: what was looked for, and what the inspection could say about it."""

    ref: ExternalRef
    state: ProbeState
    observed_digest: Any = None
    inspected_at_ms: int = 0

    NESTED = {"ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        if not isinstance(self.ref, ExternalRef):
            raise SchemaValidationError("ref must be an ExternalRef to the object probed")
        object.__setattr__(self, "state", ProbeState.parse(self.state, "state"))
        if self.state is ProbeState.PRESENT:
            if self.observed_digest is None:
                raise ArchiveError(
                    f"{self.ref.text} is reported PRESENT with no observed_digest; presence you cannot check is "
                    "the silent success §22 forbids"
                )
            object.__setattr__(self, "observed_digest", require_digest(self.observed_digest, "observed_digest"))
        elif self.observed_digest is not None:
            raise ArchiveError(
                f"{self.ref.text} is reported {self.state.value} while carrying an observed_digest; a missing or "
                "unreadable object has no bytes to hash"
            )
        object.__setattr__(self, "inspected_at_ms", require_millis(self.inspected_at_ms, "inspected_at_ms"))


@dataclass(frozen=True)
class IntegrityFinding(Record):
    """One thing an audit could not reconcile with what the manifest promised."""

    kind: DamageKind
    subject: ExternalRef
    detail: Any = None

    NESTED = {"subject": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", DamageKind.parse(self.kind, "kind"))
        if not isinstance(self.subject, ExternalRef):
            raise SchemaValidationError("subject must be an ExternalRef to what was found")
        object.__setattr__(self, "detail", require_optional_text(self.detail, "detail", maximum=512))

    @property
    def damages(self) -> bool:
        return self.kind.damages


@dataclass(frozen=True)
class IntegrityReport(Record):
    """§22's verdict over one manifest, with the digest of the bytes the verdict was read from.

    ``outcome`` is derived from the findings, so a report cannot describe damage it did not name or
    hide a finding behind an ``INTACT`` label. ``manifest_digest`` is what makes a later tampering
    readable: an audit that saw other bytes was not an audit of this archive.
    """

    report_id: str
    archive_id: str
    manifest_digest: str
    inspector: Any
    findings: tuple[IntegrityFinding, ...] = ()
    checked_at_ms: int = 0
    evidence_refs: tuple[ExternalRef, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "inspector": of(ComponentVersion),
        "findings": of(IntegrityFinding),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", require_id(self.report_id, "report_id"))
        object.__setattr__(self, "archive_id", require_id(self.archive_id, "archive_id"))
        object.__setattr__(self, "manifest_digest", require_digest(self.manifest_digest, "manifest_digest"))
        object.__setattr__(self, "inspector", require_component_version(self.inspector, "inspector"))
        findings = require_bounded(self.findings, "findings", maximum=MAX_ARCHIVE_REFS, kind="finding")
        object.__setattr__(
            self,
            "findings",
            tuple(
                sorted(
                    {IntegrityFinding.coerce(item, "findings[]") for item in findings},
                    key=lambda item: (item.subject.text, item.kind.value),
                )
            ),
        )
        object.__setattr__(self, "checked_at_ms", require_millis(self.checked_at_ms, "checked_at_ms"))
        object.__setattr__(
            self,
            "evidence_refs",
            _freeze_refs(self.evidence_refs, field="evidence_refs", maximum=MAX_RECEIPT_EVIDENCE),
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def outcome(self) -> IntegrityOutcome:
        if any(item.damages for item in self.findings):
            return IntegrityOutcome.DAMAGED
        if self.findings:
            return IntegrityOutcome.UNKNOWN
        return IntegrityOutcome.INTACT

    @property
    def is_clean(self) -> bool:
        return self.outcome.may_claim_complete

    @property
    def damaged(self) -> tuple[IntegrityFinding, ...]:
        return tuple(item for item in self.findings if item.damages)

    @property
    def unverified(self) -> tuple[IntegrityFinding, ...]:
        return tuple(item for item in self.findings if not item.damages)

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.report_id)


@dataclass(frozen=True)
class RestorationReport(Record):
    """§20's four answers kept apart: metadata, recalled material, lost material, and rights.

    The two claims a reader most wants — ``usable`` and ``fully_reproducible`` — are fields so that a
    caller can state them, which is exactly why they are checked: a report that claims
    reproducibility while naming a lost or unretrieved prerequisite, or an audit that was not clean,
    is refused at construction.
    """

    restoration_id: str
    archive_id: str
    audit: IntegrityReport
    actor: Any
    recalled: tuple[ExternalRef, ...] = ()
    not_recalled: tuple[ExternalRef, ...] = ()
    lost: tuple[ExternalRef, ...] = ()
    blocked_by_rights: tuple[ExternalRef, ...] = ()
    usable: bool = True
    fully_reproducible: bool = False
    checked_at_ms: int = 0
    evidence_refs: tuple[ExternalRef, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "audit": of(IntegrityReport),
        "actor": of(ComponentVersion),
        "recalled": of(ExternalRef),
        "not_recalled": of(ExternalRef),
        "lost": of(ExternalRef),
        "blocked_by_rights": of(ExternalRef),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "restoration_id", require_id(self.restoration_id, "restoration_id"))
        object.__setattr__(self, "archive_id", require_id(self.archive_id, "archive_id"))
        object.__setattr__(self, "audit", IntegrityReport.coerce(self.audit, "audit"))
        if self.audit.archive_id != self.archive_id:
            raise ArchiveError(
                f"{self.restoration_id} restores archive {self.archive_id} on an audit of "
                f"{self.audit.archive_id}; the integrity check has to be about the thing being reopened"
            )
        object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        for name in ("recalled", "not_recalled", "lost", "blocked_by_rights"):
            object.__setattr__(self, name, _freeze_refs(getattr(self, name), field=name, maximum=MAX_ARCHIVE_REFS))
        claimed = set(self.recalled) & (set(self.not_recalled) | set(self.lost))
        if claimed:
            raise ArchiveError(
                f"{self.restoration_id} lists {', '.join(sorted(item.text for item in claimed))} as both recalled "
                "and unavailable; a restoration cannot be two answers about one object"
            )
        if not isinstance(self.usable, bool) or not isinstance(self.fully_reproducible, bool):
            raise SchemaValidationError("usable and fully_reproducible must be booleans")
        if self.fully_reproducible:
            if not self.audit.is_clean:
                raise ArchiveError(
                    f"{self.restoration_id} claims full reproducibility over an audit that came back "
                    f"{self.audit.outcome.value}; §22 makes an unreadable object an explicit unknown, not a pass"
                )
            if self.lost or self.not_recalled:
                raise ArchiveError(
                    f"{self.restoration_id} claims full reproducibility while "
                    f"{len(self.lost) + len(self.not_recalled)} object(s) are lost or were never retrieved; "
                    "reopening metadata buys availability and nothing else (§20)"
                )
        if self.usable and self.blocked_by_rights:
            raise ArchiveError(
                f"{self.restoration_id} claims the material is usable while rights block "
                f"{', '.join(item.text for item in self.blocked_by_rights)}"
            )
        object.__setattr__(self, "checked_at_ms", require_millis(self.checked_at_ms, "checked_at_ms"))
        object.__setattr__(
            self,
            "evidence_refs",
            _freeze_refs(self.evidence_refs, field="evidence_refs", maximum=MAX_RECEIPT_EVIDENCE),
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def metadata_available(self) -> bool:
        """The one thing a restoration always proves, stated so the weaker claims cannot hide it."""

        return True

    @property
    def materials_available(self) -> bool:
        return not self.lost and not self.not_recalled

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.restoration_id)


@dataclass(frozen=True)
class RevivalReceipt(Record):
    """§21's governed reopening: new lineage from one exact historical point.

    The archived production is not mentioned by this receipt as something it changes. What it does
    carry is the exact snapshot the new line forks from, the obligations the archive owed before that
    line may run, and which of them the caller actually revalidated.
    """

    revival_id: str
    archive_id: str
    source_production_id: str
    source_snapshot_ref: ExternalRef
    revived_production_id: str
    revived_branch_id: str
    obligations: tuple[ExternalRef, ...] = ()
    revalidated: tuple[ExternalRef, ...] = ()
    actor: Any = None
    confirmed_at_ms: int = 0
    evidence_refs: tuple[ExternalRef, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "source_snapshot_ref": of(ExternalRef),
        "obligations": of(ExternalRef),
        "revalidated": of(ExternalRef),
        "actor": of(ComponentVersion),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "revival_id", require_id(self.revival_id, "revival_id"))
        object.__setattr__(self, "archive_id", require_id(self.archive_id, "archive_id"))
        for name in ("source_production_id", "revived_production_id", "revived_branch_id"):
            object.__setattr__(self, name, require_id(getattr(self, name), name))
        if self.revived_production_id == self.source_production_id:
            raise ArchiveError(
                f"{self.revival_id} revives {self.source_production_id} into itself; a revival that reuses the "
                "archived id rewrites the history it claims to leave untouched (§21)"
            )
        if not isinstance(self.source_snapshot_ref, ExternalRef) or self.source_snapshot_ref.kind is not EntityKind.SNAPSHOT:
            raise ArchiveError(
                "source_snapshot_ref must name the exact snapshot the new lineage forks from; 'the old one' is not "
                "a historical point"
            )
        object.__setattr__(self, "obligations", _freeze_refs(self.obligations, field="obligations"))
        object.__setattr__(self, "revalidated", _freeze_refs(self.revalidated, field="revalidated"))
        unknown = sorted({item.text for item in self.revalidated} - {item.text for item in self.obligations})
        if unknown:
            raise ArchiveError(
                f"{self.revival_id} revalidated {', '.join(unknown)}, which this archive never owed; a claim to "
                "have rechecked something unrelated is how a revalidation list stops meaning anything"
            )
        if len(self.outstanding) > MAX_REVIVAL_OBLIGATIONS:
            raise ArchiveError(
                f"{self.revival_id} leaves {len(self.outstanding)} obligations outstanding, over the admitted "
                f"{MAX_REVIVAL_OBLIGATIONS}; a revival that has not rechecked this much is a new production built "
                "from scratch"
            )
        if self.actor is not None:
            object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        object.__setattr__(self, "confirmed_at_ms", require_millis(self.confirmed_at_ms, "confirmed_at_ms"))
        object.__setattr__(
            self,
            "evidence_refs",
            _freeze_refs(self.evidence_refs, field="evidence_refs", maximum=MAX_RECEIPT_EVIDENCE),
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def outstanding(self) -> tuple[ExternalRef, ...]:
        done = {item.text for item in self.revalidated}
        return tuple(item for item in self.obligations if item.text not in done)

    @property
    def may_activate(self) -> bool:
        """§24's ACTIVE-while-archived exception belongs to the restoration, never to a revival."""

        return not self.outstanding

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.revival_id)


@dataclass(frozen=True)
class CleanupDecision(Record):
    """One archive's GC answer, with the claims that produced it."""

    archive_id: str
    reasons: tuple[ArchiveRetention, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "archive_id", require_id(self.archive_id, "archive_id"))
        reasons = require_bounded(self.reasons, "reasons", maximum=MAX_BUNDLE_ITEMS)
        resolved = tuple(sorted({ArchiveRetention.parse(item, "reasons[]") for item in reasons}, key=lambda item: item.value))
        if not resolved:
            raise ArchiveError("a cleanup decision with no reason is a collectable, which has its own list")
        object.__setattr__(self, "reasons", resolved)

    @property
    def held(self) -> bool:
        return bool(self.reasons)


@dataclass(frozen=True)
class CleanupPlan(Record):
    """M02's GC answer over an archive registry: what stays, what may go, and why. M55 executes."""

    kept: tuple[CleanupDecision, ...] = ()
    collectable: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        kept = require_bounded(self.kept, "kept", maximum=MAX_ARCHIVE_REFS, kind="decision")
        resolved = tuple(sorted({CleanupDecision.coerce(item, "kept[]") for item in kept}, key=lambda item: item.archive_id))
        object.__setattr__(self, "kept", resolved)
        object.__setattr__(self, "collectable", _freeze_ids(self.collectable, field="collectable"))
        overlap = {item.archive_id for item in resolved} & set(self.collectable)
        if overlap:
            raise ArchiveError(
                f"{', '.join(sorted(overlap))} is both held and collectable; a cleanup plan that contradicts "
                "itself is not a plan"
            )

    @property
    def holds(self) -> tuple[str, ...]:
        return tuple(item.archive_id for item in self.kept)

    def reason_for(self, archive_id: str) -> tuple[ArchiveRetention, ...]:
        wanted = require_id(archive_id, "archive_id")
        return next((item.reasons for item in self.kept if item.archive_id == wanted), ())


def audit_archive(
    manifest: Any,
    probes: Iterable[Any] = (),
    *,
    inspector: Any,
    now_ms: int = 0,
    evidence_refs: Iterable[Any] = (),
    report_id: str | None = None,
) -> IntegrityReport:
    """Compare what the manifest promised against what an inspection could actually see.

    Objects the caller never probed become ``UNVERIFIABLE`` findings rather than silence, which is
    why §22's "never silent success" is a rule about omission and not only about corruption.
    """

    wanted = ArchiveManifest.coerce(manifest, "manifest")
    resolved: dict[str, ObjectProbe] = {}
    required = {item.text for item in wanted.required_refs()}
    for item in probes:
        probe = ObjectProbe.coerce(item, "probes[]")
        if probe.ref.text not in required:
            raise ArchiveError(
                f"{probe.ref.text} is not a reference this archive holds, so inspecting it is not evidence about "
                f"{wanted.archive_id}"
            )
        previous = resolved.get(probe.ref.text)
        if previous is not None and previous.state is not probe.state:
            raise ArchiveError(
                f"{probe.ref.text} was probed twice with two answers ({previous.state.value} and {probe.state.value}); "
                "an integrity report cannot average contradictory inspections"
            )
        resolved[probe.ref.text] = probe
    findings: list[IntegrityFinding] = []
    for item in wanted.required_refs():
        probe = resolved.get(item.text)
        if item.text == wanted.snapshot_ref.text:
            findings.extend(_snapshot_findings(wanted, probe))
            continue
        asset = wanted.object_for(item)
        if asset is not None:
            findings.extend(_asset_findings(asset, probe))
            continue
        findings.extend(_reference_findings(item, probe))
    cited = {item.text for item in wanted.rights_refs}
    for risk in wanted.blocking_risks(for_use=True):
        if risk.subject.text not in cited:
            findings.append(
                IntegrityFinding(
                    kind=DamageKind.UNCITED_BLOCK,
                    subject=risk.subject,
                    detail="a rights block is recorded against evidence this manifest does not carry",
                )
            )
    return IntegrityReport(
        report_id=report_id or new_id(),
        archive_id=wanted.archive_id,
        manifest_digest=wanted.digest(),
        inspector=inspector,
        findings=tuple(findings),
        checked_at_ms=now_ms,
        evidence_refs=tuple(evidence_refs),
    )


def _asset_findings(asset: ArchiveObject, probe: ObjectProbe | None) -> tuple[IntegrityFinding, ...]:
    if probe is None:
        return (
            IntegrityFinding(
                kind=DamageKind.UNVERIFIABLE,
                subject=asset.ref,
                detail="no inspection was made of this archived object",
            ),
        )
    if probe.state is ProbeState.ABSENT:
        return (
            IntegrityFinding(
                kind=DamageKind.MISSING_OBJECT,
                subject=asset.ref,
                detail=f"the archive promised {asset.digest[:12]} and the store holds nothing",
            ),
        )
    if probe.state is ProbeState.UNREADABLE:
        return (
            IntegrityFinding(
                kind=DamageKind.UNVERIFIABLE,
                subject=asset.ref,
                detail=f"{asset.storage.value} material that was not retrieved cannot be certified",
            ),
        )
    if probe.observed_digest != asset.digest:
        return (
            IntegrityFinding(
                kind=DamageKind.DIGEST_MISMATCH,
                subject=asset.ref,
                detail=f"the bytes now hash to {probe.observed_digest[:12]}, not the archived {asset.digest[:12]}",
            ),
        )
    return ()


def _reference_findings(ref: ExternalRef, probe: ObjectProbe | None) -> tuple[IntegrityFinding, ...]:
    """What an inspection says about a reference the archive cites but does not hold as material."""

    if probe is None:
        return (
            IntegrityFinding(
                kind=DamageKind.UNVERIFIABLE,
                subject=ref,
                detail="no inspection was made of this reference",
            ),
        )
    if probe.state is ProbeState.UNREADABLE:
        return (
            IntegrityFinding(
                kind=DamageKind.UNVERIFIABLE,
                subject=ref,
                detail="the store could not be read, so this reference is neither here nor gone",
            ),
        )
    if probe.state is ProbeState.ABSENT:
        return (
            IntegrityFinding(
                kind=DamageKind.UNREACHABLE_REFERENCE,
                subject=ref,
                detail="the evidence this archive stands on is gone",
            ),
        )
    if ref.content_digest is not None and probe.observed_digest != ref.content_digest:
        return (
            IntegrityFinding(
                kind=DamageKind.DIGEST_MISMATCH,
                subject=ref,
                detail=f"it now hashes to {probe.observed_digest[:12]}, not the sealed {ref.content_digest[:12]}",
            ),
        )
    return ()


def _snapshot_findings(manifest: ArchiveManifest, probe: ObjectProbe | None) -> tuple[IntegrityFinding, ...]:
    """§22's first question: is the canonical snapshot this archive stands for still what it was.

    The manifest carries the snapshot's own digest, so a store that hands back other bytes under the
    same id is caught here rather than at the point someone trusts the archive.
    """

    ref = manifest.snapshot_ref
    if probe is None:
        return (
            IntegrityFinding(
                kind=DamageKind.UNVERIFIABLE,
                subject=ref,
                detail="the canonical snapshot this archive closes over was never inspected",
            ),
        )
    if probe.state is ProbeState.ABSENT:
        return (
            IntegrityFinding(
                kind=DamageKind.MISSING_OBJECT,
                subject=ref,
                detail="the archive names a canonical snapshot the store no longer holds",
            ),
        )
    if probe.state is ProbeState.UNREADABLE:
        return (
            IntegrityFinding(
                kind=DamageKind.UNVERIFIABLE,
                subject=ref,
                detail="the canonical snapshot could not be read, so nothing about this archive is confirmed",
            ),
        )
    if ref.content_digest is not None and probe.observed_digest != ref.content_digest:
        return (
            IntegrityFinding(
                kind=DamageKind.DIGEST_MISMATCH,
                subject=ref,
                detail=f"the snapshot now hashes to {probe.observed_digest[:12]}, not the sealed "
                f"{ref.content_digest[:12]}",
            ),
        )
    return ()


def restore_archive(
    manifest: Any,
    probes: Iterable[Any] = (),
    *,
    actor: Any,
    now_ms: int = 0,
    evidence_refs: Iterable[Any] = (),
    restoration_id: str | None = None,
    report_id: str | None = None,
) -> RestorationReport:
    """Ask what reopening would buy, and let the answer be "availability, not reproducibility".

    The audit runs as part of the restoration because §22 checks archives on access: a report that
    skipped it would be a claim about bytes nobody looked at.
    """

    wanted = ArchiveManifest.coerce(manifest, "manifest")
    resolved = tuple(ObjectProbe.coerce(item, "probes[]") for item in probes)
    audit = audit_archive(
        wanted,
        resolved,
        inspector=require_component_version(actor, "actor"),
        now_ms=now_ms,
        evidence_refs=evidence_refs,
        report_id=report_id,
    )
    seen = {item.ref.text: item for item in resolved}
    recalled: list[ExternalRef] = []
    not_recalled: list[ExternalRef] = []
    lost: list[ExternalRef] = []
    material = [(wanted.snapshot_ref, False)] + [(item.ref, item.needs_recall) for item in wanted.assets]
    for ref, needs_recall in material:
        probe = seen.get(ref.text)
        if probe is None:
            continue
        if probe.state is ProbeState.ABSENT:
            lost.append(ref)
        elif probe.state is ProbeState.UNREADABLE:
            not_recalled.append(ref)
        elif needs_recall:
            recalled.append(ref)
    blocked: list[ExternalRef] = []
    for risk in wanted.blocking_risks(for_use=True):
        probe = seen.get(risk.subject.text)
        if probe is not None and probe.state is ProbeState.PRESENT:
            blocked.append(risk.subject)
    usable = audit.outcome is not IntegrityOutcome.DAMAGED and not blocked
    fully_reproducible = (
        wanted.tier.owes_asset_completeness
        and audit.is_clean
        and not lost
        and not not_recalled
        and not blocked
    )
    return RestorationReport(
        restoration_id=restoration_id or new_id(),
        archive_id=wanted.archive_id,
        audit=audit,
        actor=actor,
        recalled=tuple(recalled),
        not_recalled=tuple(not_recalled),
        lost=tuple(lost),
        blocked_by_rights=tuple(blocked),
        usable=usable,
        fully_reproducible=fully_reproducible,
        checked_at_ms=now_ms,
        evidence_refs=evidence_refs,
    )


def revive_archive(
    manifest: Any,
    archived: ProductionLedger,
    *,
    revived_production_id: str,
    revived_branch_id: str,
    revalidated: Iterable[Any] = (),
    actor: Any,
    now_ms: int = 0,
    evidence_refs: Iterable[Any] = (),
    revival_id: str | None = None,
    profile: Any = None,
) -> tuple[RevivalReceipt, ProductionLedger]:
    """Fork a new lineage from an archived production's exact snapshot, and change nothing about it.

    The returned ledger starts at DRAFT on purpose. Reaching the state the archived production was in
    is work that has to be re-walked and re-accepted, which is the only way §21's "does not mutate
    the archived historical production" survives contact with someone who wants a shortcut.
    """

    wanted = ArchiveManifest.coerce(manifest, "manifest")
    if not isinstance(archived, ProductionLedger):
        raise SchemaValidationError("revive_archive expects the ProductionLedger the archive was sealed from")
    if wanted.production_id != archived.production_id:
        raise ArchiveError(
            f"{wanted.archive_id} is the archive of {wanted.production_id} and cannot be revived as "
            f"{archived.production_id}"
        )
    phase = archived.current.phase
    if phase not in {Phase.SUPERSEDED, Phase.ARCHIVED}:
        raise ArchiveError(
            f"{archived.production_id} is {phase.value}; §21 reopens an archived or superseded production, and "
            "forking a live one is a normal branch, not a revival"
        )
    receipt = RevivalReceipt(
        revival_id=revival_id or new_id(),
        archive_id=wanted.archive_id,
        source_production_id=archived.production_id,
        source_snapshot_ref=wanted.snapshot_ref,
        revived_production_id=revived_production_id,
        revived_branch_id=revived_branch_id,
        obligations=wanted.revival_obligations(),
        revalidated=tuple(revalidated),
        actor=actor,
        confirmed_at_ms=now_ms,
        evidence_refs=evidence_refs,
    )
    ledger = ProductionLedger(
        revived_production_id,
        initial_vector(revived_production_id, wanted.project_id),
        profile=profile,
    )
    return receipt, ledger


class ArchiveLedger:
    """One sealed manifest plus every finding, restoration and revival ever made about it.

    §22's "never silent success" is a rule about this ledger as much as about an audit: a finding is
    appended and stays, so an archive that was caught damaged cannot be talked back into ``INTACT``
    by a later report that found nothing. The bytes changed, which is a new archive under a new id.
    """

    def __init__(self, manifest: Any, *, audits: Iterable[Any] = (), restorations: Iterable[Any] = (), revivals: Iterable[Any] = ()) -> None:
        self._manifest = ArchiveManifest.coerce(manifest, "manifest")
        self._audits: dict[str, IntegrityReport] = {}
        self._restorations: dict[str, RestorationReport] = {}
        self._revivals: dict[str, RevivalReceipt] = {}
        for item in audits:
            self.append_audit(item)
        for item in restorations:
            self.record_restoration(item)
        for item in revivals:
            self.record_revival(item)

    @property
    def manifest(self) -> ArchiveManifest:
        return self._manifest

    @property
    def archive_id(self) -> str:
        return self._manifest.archive_id

    @property
    def production_id(self) -> str:
        return self._manifest.production_id

    @property
    def tier(self) -> ArchiveTier:
        return self._manifest.tier

    @property
    def audits(self) -> tuple[IntegrityReport, ...]:
        return tuple(self._audits.values())

    @property
    def restorations(self) -> tuple[RestorationReport, ...]:
        return tuple(self._restorations.values())

    @property
    def revivals(self) -> tuple[RevivalReceipt, ...]:
        return tuple(self._revivals.values())

    @property
    def condition(self) -> IntegrityOutcome:
        """The last inspection's answer, with damage never forgotten and UNKNOWN never a pass.

        Damage is monotone because a replaced byte is a fact no later reading undoes, and the ledger
        refuses an ``INTACT`` report that arrives after one anyway. An unknown is not a fact about the
        material but about how far the inspection got, so a later audit that did reach every reference
        answers it: cold material that was recalled and verified is intact, not unknown forever.
        """

        found = [item.outcome for item in self.audits]
        if not found:
            return IntegrityOutcome.UNKNOWN
        if IntegrityOutcome.DAMAGED in found:
            return IntegrityOutcome.DAMAGED
        return found[-1]

    @property
    def is_verified(self) -> bool:
        return self.condition is IntegrityOutcome.INTACT

    def append_audit(self, report: Any) -> IntegrityReport:
        wanted = IntegrityReport.coerce(report, "report")
        self._require_here(wanted.archive_id, "audit")
        if wanted.manifest_digest != self._manifest.digest():
            raise ArchiveError(
                f"{wanted.report_id} audited a manifest whose digest is {wanted.manifest_digest[:12]}, not the "
                f"{self._manifest.digest()[:12]} sealed under {self.archive_id}; the bytes of a sealed archive "
                "were rewritten, which is the damage §22 is about"
            )
        existing = self._audits.get(wanted.report_id)
        if existing is not None:
            if existing == wanted:
                return existing
            raise StoreConflictError(
                f"audit {wanted.report_id} is already recorded with a different conclusion"
            )
        if self.condition is IntegrityOutcome.DAMAGED and wanted.outcome is IntegrityOutcome.INTACT:
            raise ArchiveError(
                f"{self.archive_id} was already found damaged; an audit reporting nothing wrong now is evidence "
                "that the objects were replaced, and a replacement is sealed as a new archive that supersedes "
                "this one, never recorded over the damage"
            )
        self._audits[wanted.report_id] = wanted
        return wanted

    def record_restoration(self, report: Any) -> RestorationReport:
        wanted = RestorationReport.coerce(report, "report")
        self._require_here(wanted.archive_id, "restoration")
        existing = self._restorations.get(wanted.restoration_id)
        if existing is not None:
            if existing == wanted:
                return existing
            raise StoreConflictError(
                f"restoration {wanted.restoration_id} is already recorded with a different outcome"
            )
        self.append_audit(wanted.audit)
        self._restorations[wanted.restoration_id] = wanted
        return wanted

    def record_revival(self, receipt: Any) -> RevivalReceipt:
        wanted = RevivalReceipt.coerce(receipt, "receipt")
        self._require_here(wanted.archive_id, "revival")
        if wanted.source_snapshot_ref != self._manifest.snapshot_ref:
            raise ArchiveError(
                f"{wanted.revival_id} forks from {wanted.source_snapshot_ref.text} while {self.archive_id} sealed "
                f"{self._manifest.snapshot_ref.text}; a revival from a different point is a different archive's work"
            )
        existing = self._revivals.get(wanted.revival_id)
        if existing is not None:
            if existing == wanted:
                return existing
            raise StoreConflictError(
                f"revival {wanted.revival_id} is already recorded with a different lineage"
            )
        self._revivals[wanted.revival_id] = wanted
        return wanted

    def _require_here(self, archive_id: str, kind: str) -> None:
        if archive_id != self.archive_id:
            raise ArchiveError(
                f"this {kind} is about {archive_id} and cannot be recorded on the ledger of {self.archive_id}"
            )

    def retention_reasons(self, *, now_ms: int = 0) -> tuple[ArchiveRetention, ...]:
        """Every claim that keeps this archive out of a cleanup run, tier and findings included.

        An open damage finding holds too, and deliberately so: §22's damage is a fact about the
        material, and collecting the rest of it while the question is unresolved is how a corpus
        loses the evidence that something went wrong.
        """

        found = set(self._manifest.retention(now_ms=now_ms))
        if self._revivals:
            found.add(ArchiveRetention.CITED_BY_REVIVAL)
        if self.condition is IntegrityOutcome.DAMAGED:
            found.add(ArchiveRetention.OPEN_INTEGRITY_FINDING)
        return tuple(sorted(found, key=lambda item: item.value))

    def may_collect(self, *, now_ms: int = 0) -> bool:
        return not self.retention_reasons(now_ms=now_ms)

    def replay(self) -> tuple[IntegrityReport, ...]:
        """The audits in the order they were appended, for whoever checks this ledger's own history."""

        return self.audits


class ArchiveRegistry:
    """Sealed archives, and the GC answer M06 and M55 will carry out.

    Sealing is idempotent for the same manifest and conflicting for a second one under the same id,
    which is the same rule every other store in M02 applies: an archive is written once. Beyond
    that, the registry exists so a cleanup question can be answered over all the holds at once —
    ``plan_cleanup`` is where §19's tiers and §22's findings become a decision.
    """

    def __init__(self, archives: Iterable[Any] = ()) -> None:
        self._items: dict[str, ArchiveLedger] = {}
        for item in archives:
            self.seal(item)

    def seal(self, archive: Any) -> ArchiveLedger:
        ledger = archive if isinstance(archive, ArchiveLedger) else ArchiveLedger(archive)
        existing = self._items.get(ledger.archive_id)
        if existing is not None:
            if existing.manifest.digest() == ledger.manifest.digest():
                return existing
            raise StoreConflictError(
                f"archive {ledger.archive_id} is already sealed with different content; history is written once, "
                "so mint a new archive id and supersede the old one"
            )
        self._items[ledger.archive_id] = ledger
        return ledger

    def get(self, archive_id: str) -> ArchiveLedger:
        wanted = require_id(archive_id, "archive_id")
        try:
            return self._items[wanted]
        except KeyError:
            raise ArchiveError(f"no archive is sealed under {wanted}") from None

    @property
    def known(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def for_production(self, production_id: str) -> tuple[ArchiveLedger, ...]:
        wanted = require_id(production_id, "production_id")
        return tuple(item for item in self._items.values() if item.production_id == wanted)

    def holds_snapshot(self, snapshot: Any) -> bool:
        """Whether some archive closes over this snapshot, which is a retention claim on it.

        The answer keys on the snapshot's identity rather than on its bytes: a sealed archive whose
        canonical snapshot now hashes differently is the damage §22 reports on the ledger, and
        answering "not held" here would let exactly that archive be collected.
        """

        wanted = _snapshot_identity(snapshot)
        return any(item.manifest.snapshot_ref.reference == wanted for item in self._items.values())

    def retention_reasons(self, archive_id: str, *, now_ms: int = 0) -> tuple[ArchiveRetention, ...]:
        return self.get(archive_id).retention_reasons(now_ms=now_ms)

    def plan_cleanup(self, *, now_ms: int = 0) -> CleanupPlan:
        kept = []
        collectable = []
        for item in self._items.values():
            reasons = item.retention_reasons(now_ms=now_ms)
            if reasons:
                kept.append(CleanupDecision(archive_id=item.archive_id, reasons=reasons))
            else:
                collectable.append(item.archive_id)
        return CleanupPlan(kept=tuple(kept), collectable=tuple(sorted(collectable)))

    def collectable(self, *, now_ms: int = 0) -> tuple[str, ...]:
        return self.plan_cleanup(now_ms=now_ms).collectable


def seal_archive(
    production: ProductionLedger,
    snapshot: Any,
    *,
    tier: Any,
    actor: Any,
    assets: Iterable[Any] = (),
    restoration_prerequisites: Iterable[Any] = (),
    risks: Iterable[Any] = (),
    pins: Iterable[Any] = (),
    release_refs: Iterable[Any] = (),
    retention_expires_at_ms: int = 0,
    now_ms: int = 0,
    evidence_refs: Iterable[Any] = (),
    archive_id: str | None = None,
    project_id: str | None = None,
) -> ArchiveManifest:
    """Close a canonical snapshot into an archive, taking the evidence from the closure that has it.

    The manifest's provenance, rights, quality and policy refs are read out of the snapshot rather
    than retyped by the caller. That is the difference between an archive that inherits what was
    proven at acceptance and one that merely repeats whatever a script asserted about it.
    """

    if not isinstance(production, ProductionLedger):
        raise SchemaValidationError("seal_archive expects a ProductionLedger, the authority over the production")
    wanted = Snapshot.coerce(snapshot, "snapshot")
    closure = wanted.closure
    if closure.production_id != production.production_id:
        raise ArchiveError(
            f"{wanted.snapshot_id} is a closure over {closure.production_id} and cannot be archived as "
            f"{production.production_id}"
        )
    current = production.current
    if not phase_at_least(current.phase, Phase.ACCEPTED):
        raise ArchiveError(
            f"{production.production_id} is {current.phase.value}; what has not been accepted has no canonical "
            "state to archive, so this would be a backup, not an archive"
        )
    parsed = ArchiveTier.parse(tier, "tier")
    if parsed.owes_asset_completeness and not wanted.snapshot_class.at_least(SnapshotClass.VALIDATED_SNAPSHOT):
        raise ArchiveError(
            f"{parsed.value} over {wanted.snapshot_id} is refused: the snapshot is "
            f"{wanted.snapshot_class.value}, which carries no validated closure to reproduce; a reproducible "
            "archive starts from a closure that proves what it claims"
        )
    if not wanted.snapshot_class.at_least(SnapshotClass.MATERIALIZED_SNAPSHOT):
        raise ArchiveError(
            f"{parsed.value} would archive {wanted.snapshot_class.value}, which closes over nothing material"
        )
    return ArchiveManifest(
        archive_id=archive_id or new_id(),
        project_id=project_id or closure.project_id,
        production_id=production.production_id,
        snapshot_ref=ExternalRef(
            kind=EntityKind.SNAPSHOT,
            reference=wanted.snapshot_id,
            content_digest=wanted.digest,
        ),
        graph_revision_id=closure.graph.revision.revision_id,
        tier=parsed,
        intent_ref=closure.intent_ref,
        release_refs=tuple(release_refs),
        provenance_refs=closure.provenance_refs,
        rights_refs=closure.rights_refs,
        quality_refs=closure.quality_decisions,
        policy_refs=closure.policy_refs,
        assets=tuple(assets),
        restoration_prerequisites=tuple(restoration_prerequisites),
        risks=tuple(risks),
        pins=tuple(pins),
        retention_expires_at_ms=retention_expires_at_ms,
        sealed_by=actor,
        sealed_at_ms=now_ms,
        evidence_refs=tuple(evidence_refs),
    )
