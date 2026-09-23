"""Portable non-executable DNA package, dependency, marketplace and lifecycle contracts."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, freeze_json, require_refs
from .enums import DependencyKind, DNAFamily, PackageLifecycle, PortabilityLevel
from .errors import DNAAdmissionError, DNAIntegrityError, DNAValidationError
from .identity import DNARevision, DNARevisionRef
from .limits import DEFAULT_LIMITS, DNARecordLimits
from .traits import TraitSchemaRegistry, TraitSchemaRef, DEFAULT_TRAIT_SCHEMAS
from .versions import content_digest, require_identifier, require_text, require_version

__all__ = [
    "DNAPackageEntry",
    "PackageDependency",
    "PackageExtension",
    "ReusableDNAPackageManifest",
    "DNAMarketplaceContract",
    "DNAPackageConformanceReport",
    "PackageLifecycleEvent",
    "DNAInterfaceOnlyProjection",
    "DependencyClosure",
    "resolve_dependency_closure",
    "conform_package",
    "project_package_interface",
    "transition_package_lifecycle",
    "verify_package_conformance_report",
]


@dataclass(frozen=True)
class DNAPackageEntry(CanonicalRecord):
    dna_id: str
    revision_ref: DNARevisionRef
    family: DNAFamily
    semantic_fingerprint: str
    profile_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        if not isinstance(self.revision_ref, DNARevisionRef) or self.revision_ref.dna_id != self.dna_id:
            raise DNAIntegrityError("package DNA entry must pin a revision of its dna_id")
        if not isinstance(self.family, DNAFamily):
            object.__setattr__(self, "family", DNAFamily(self.family))
        from .versions import require_digest
        object.__setattr__(self, "semantic_fingerprint", require_digest(self.semantic_fingerprint, "semantic_fingerprint"))
        if self.profile_ref is not None and not isinstance(self.profile_ref, SemanticRef):
            raise DNAValidationError("profile_ref must be a SemanticRef")


@dataclass(frozen=True)
class PackageDependency(CanonicalRecord):
    dependency_id: str
    kind: DependencyKind
    target_ref: SemanticRef
    depends_on_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependency_id", require_identifier(self.dependency_id, "dependency_id"))
        if not isinstance(self.kind, DependencyKind):
            object.__setattr__(self, "kind", DependencyKind(self.kind))
        if not isinstance(self.target_ref, SemanticRef):
            raise DNAValidationError("target_ref must be a SemanticRef")
        deps = tuple(sorted({require_identifier(item, "depends_on_ids[]") for item in self.depends_on_ids}))
        if self.dependency_id in deps:
            raise DNAIntegrityError("package dependency cannot depend on itself")
        if self.kind is DependencyKind.REQUIRED_EXTERNAL_DNA and not self.target_ref.revision_pinned:
            raise DNAAdmissionError("required external DNA dependencies must pin an exact revision")
        object.__setattr__(self, "depends_on_ids", deps)

    @property
    def required(self) -> bool:
        return self.kind in {
            DependencyKind.REQUIRED_CANONICAL,
            DependencyKind.REQUIRED_EXTERNAL_DNA,
            DependencyKind.POLICY_REF,
            DependencyKind.SCHEMA_REF,
        }


@dataclass(frozen=True)
class PackageExtension(CanonicalRecord):
    schema_ref: TraitSchemaRef
    value: object
    preservation_policy_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema_ref, TraitSchemaRef):
            raise DNAValidationError("schema_ref must be a TraitSchemaRef")
        object.__setattr__(self, "value", freeze_json(self.value, "package extension"))
        if self.preservation_policy_ref is not None and not isinstance(self.preservation_policy_ref, SemanticRef):
            raise DNAValidationError("preservation_policy_ref must be a SemanticRef")


@dataclass(frozen=True)
class ReusableDNAPackageManifest(CanonicalRecord):
    package_id: str
    version: str
    portability: PortabilityLevel
    entries: tuple[DNAPackageEntry, ...]
    dependencies: tuple[PackageDependency, ...]
    compatibility_refs: tuple[SemanticRef, ...]
    migration_capability_refs: tuple[SemanticRef, ...]
    rights_refs: tuple[SemanticRef, ...]
    provenance_refs: tuple[SemanticRef, ...]
    security_refs: tuple[SemanticRef, ...]
    conformance_refs: tuple[SemanticRef, ...]
    metadata: object
    executable_payload_refs: tuple[SemanticRef, ...] = ()
    extensions: tuple[PackageExtension, ...] = ()
    schema_version: str = "iris-m05-package-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_id", require_identifier(self.package_id, "package_id"))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        if not isinstance(self.portability, PortabilityLevel):
            object.__setattr__(self, "portability", PortabilityLevel(self.portability))
        entries = tuple(self.entries)
        if not entries or any(not isinstance(item, DNAPackageEntry) for item in entries):
            raise DNAValidationError("package manifest requires one or more typed DNA entries")
        if len({item.dna_id for item in entries}) != len(entries):
            raise DNAIntegrityError("multi-identity packages must declare each dna_id exactly once")
        object.__setattr__(self, "entries", tuple(sorted(entries, key=lambda item: item.dna_id)))
        dependencies = tuple(self.dependencies)
        if any(not isinstance(item, PackageDependency) for item in dependencies):
            raise DNAValidationError("dependencies must contain PackageDependency records")
        if len({item.dependency_id for item in dependencies}) != len(dependencies):
            raise DNAIntegrityError("package manifest contains duplicate dependency IDs")
        object.__setattr__(self, "dependencies", tuple(sorted(dependencies, key=lambda item: item.dependency_id)))
        for name in (
            "compatibility_refs", "migration_capability_refs", "rights_refs",
            "provenance_refs", "security_refs", "conformance_refs", "executable_payload_refs",
        ):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))
        if self.executable_payload_refs:
            raise DNAAdmissionError("canonical DNA packages are non-executable; executable payload refs are forbidden")
        if any(ref.owner_module != "m53" for ref in self.rights_refs):
            raise DNAAdmissionError("rights/license/consent refs must remain owned by M53")
        if any(ref.owner_module != "m54" for ref in self.security_refs):
            raise DNAAdmissionError("security/restricted-content refs must remain owned by M54")
        extensions = tuple(self.extensions)
        if any(not isinstance(item, PackageExtension) for item in extensions):
            raise DNAValidationError("extensions must contain PackageExtension records")
        object.__setattr__(self, "extensions", tuple(sorted(extensions, key=lambda item: (item.schema_ref.family, item.schema_ref.version))))
        object.__setattr__(self, "metadata", freeze_json(self.metadata, "package metadata"))
        object.__setattr__(self, "schema_version", require_version(self.schema_version, "schema_version"))

    @property
    def package_digest(self) -> str:
        return content_digest(self)

    @property
    def subject_identity_ids(self) -> tuple[str, ...]:
        return tuple(item.dna_id for item in self.entries)


@dataclass(frozen=True)
class DNAMarketplaceContract(CanonicalRecord):
    package_ref: SemanticRef
    family: DNAFamily
    consumer_capability_refs: tuple[SemanticRef, ...]
    compatibility_refs: tuple[SemanticRef, ...]
    rights_refs: tuple[SemanticRef, ...]
    provenance_refs: tuple[SemanticRef, ...]
    security_refs: tuple[SemanticRef, ...]
    use_restriction_refs: tuple[SemanticRef, ...] = ()
    derivative_policy_refs: tuple[SemanticRef, ...] = ()
    attribution_refs: tuple[SemanticRef, ...] = ()
    lifecycle: PackageLifecycle = PackageLifecycle.ACTIVE

    def __post_init__(self) -> None:
        if not isinstance(self.package_ref, SemanticRef):
            raise DNAValidationError("package_ref must be a SemanticRef")
        if self.package_ref.owner_module != "m05" or self.package_ref.family != "reusable.package":
            raise DNAAdmissionError("marketplace contract must pin an M05 reusable package interface")
        if not isinstance(self.family, DNAFamily):
            object.__setattr__(self, "family", DNAFamily(self.family))
        if not isinstance(self.lifecycle, PackageLifecycle):
            object.__setattr__(self, "lifecycle", PackageLifecycle(self.lifecycle))
        for name in (
            "consumer_capability_refs", "compatibility_refs", "rights_refs", "provenance_refs",
            "security_refs", "use_restriction_refs", "derivative_policy_refs", "attribution_refs",
        ):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))
        if any(ref.owner_module != "m53" for ref in self.rights_refs):
            raise DNAAdmissionError("marketplace metadata cannot self-authorize rights or consent")
        if any(ref.owner_module != "m54" for ref in self.security_refs):
            raise DNAAdmissionError("marketplace metadata cannot self-prove security clearance")


@dataclass(frozen=True)
class DNAPackageConformanceReport(CanonicalRecord):
    package_id: str
    package_digest: str
    valid: bool
    findings: tuple[str, ...]
    missing_required_dependencies: tuple[str, ...]
    missing_optional_dependencies: tuple[str, ...]
    verified_entry_refs: tuple[DNARevisionRef, ...]
    checks_legal_rights: bool = False
    checks_semantic_equivalence: bool = False
    report_digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_id", require_identifier(self.package_id, "package_id"))
        from .versions import require_digest
        object.__setattr__(self, "package_digest", require_digest(self.package_digest, "package_digest"))
        if not isinstance(self.valid, bool):
            raise DNAValidationError("valid must be a bool")
        object.__setattr__(self, "findings", tuple(sorted({require_text(item, "findings[]", maximum=96).upper() for item in self.findings})))
        object.__setattr__(self, "missing_required_dependencies", tuple(sorted({require_identifier(item, "missing_required_dependencies[]") for item in self.missing_required_dependencies})))
        object.__setattr__(self, "missing_optional_dependencies", tuple(sorted({require_identifier(item, "missing_optional_dependencies[]") for item in self.missing_optional_dependencies})))
        refs = tuple(self.verified_entry_refs)
        if any(not isinstance(item, DNARevisionRef) for item in refs):
            raise DNAValidationError("verified_entry_refs must contain DNARevisionRef records")
        object.__setattr__(self, "verified_entry_refs", tuple(sorted(refs)))
        if self.checks_legal_rights or self.checks_semantic_equivalence:
            raise DNAAdmissionError("conformance is not legal-rights or semantic-equivalence proof")
        if self.valid and self.findings:
            raise DNAIntegrityError("a passing conformance report cannot contain findings")
        if not self.report_digest:
            raise DNAValidationError("conformance report requires a deterministic report_digest")
        object.__setattr__(self, "report_digest", require_digest(self.report_digest, "report_digest"))
        body = {
            "package_id": self.package_id,
            "package_digest": self.package_digest,
            "valid": self.valid,
            "findings": self.findings,
            "missing_required_dependencies": self.missing_required_dependencies,
            "missing_optional_dependencies": self.missing_optional_dependencies,
            "verified_entry_refs": self.verified_entry_refs,
        }
        if content_digest(body) != self.report_digest:
            raise DNAIntegrityError("package conformance report digest does not match its findings")


@dataclass(frozen=True)
class PackageLifecycleEvent(CanonicalRecord):
    package_ref: SemanticRef
    previous: PackageLifecycle
    next: PackageLifecycle
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    reason: str
    replacement_refs: tuple[SemanticRef, ...] = ()
    history_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        for name in ("previous", "next"):
            value = getattr(self, name)
            if not isinstance(value, PackageLifecycle):
                object.__setattr__(self, name, PackageLifecycle(value))
        if not isinstance(self.package_ref, SemanticRef) or not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAdmissionError("package lifecycle requires package, authority, and policy refs")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))
        object.__setattr__(self, "replacement_refs", require_refs(self.replacement_refs, "replacement_refs"))
        object.__setattr__(self, "history_refs", require_refs(self.history_refs, "history_refs"))
        if self.previous not in {
            PackageLifecycle.ACTIVE: set(),
            PackageLifecycle.DEPRECATED: {PackageLifecycle.ACTIVE},
            PackageLifecycle.SECURITY_RESTRICTED: {PackageLifecycle.ACTIVE, PackageLifecycle.DEPRECATED},
            PackageLifecycle.RETIRED: {PackageLifecycle.ACTIVE, PackageLifecycle.DEPRECATED, PackageLifecycle.SECURITY_RESTRICTED},
        }[self.next]:
            raise DNAAdmissionError("package lifecycle event does not represent an allowed forward transition")
        if self.next is PackageLifecycle.DEPRECATED and not self.replacement_refs:
            raise DNAAdmissionError("deprecation must carry explicit replacement refs")
        if self.next is PackageLifecycle.RETIRED and not self.history_refs:
            raise DNAAdmissionError("retirement must preserve explicit package history refs")


@dataclass(frozen=True)
class DNAInterfaceOnlyProjection(CanonicalRecord):
    package_id: str
    package_version: str
    subject_ids: tuple[str, ...]
    revision_refs: tuple[DNARevisionRef, ...]
    semantic_fingerprints: tuple[str, ...]
    rights_refs: tuple[SemanticRef, ...]
    security_refs: tuple[SemanticRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_id", require_identifier(self.package_id, "package_id"))
        object.__setattr__(self, "package_version", require_version(self.package_version, "package_version"))
        revisions = tuple(self.revision_refs)
        fingerprints = tuple(self.semantic_fingerprints)
        if len(revisions) != len(fingerprints) or any(not isinstance(item, DNARevisionRef) for item in revisions):
            raise DNAValidationError("interface projection requires one fingerprint per pinned revision")
        from .versions import require_digest
        fingerprints = tuple(require_digest(item, "semantic_fingerprints[]") for item in fingerprints)
        paired = sorted(zip(revisions, fingerprints), key=lambda pair: pair[0].dna_id)
        subject_ids = tuple(pair[0].dna_id for pair in paired)
        declared_ids = tuple(sorted({require_identifier(item, "subject_ids[]") for item in self.subject_ids}))
        if declared_ids != subject_ids:
            raise DNAIntegrityError("interface projection subject IDs must match its pinned revision refs")
        if len(set(subject_ids)) != len(subject_ids):
            raise DNAIntegrityError("interface projection must retain each declared DNA identity exactly once")
        object.__setattr__(self, "subject_ids", subject_ids)
        object.__setattr__(self, "revision_refs", tuple(pair[0] for pair in paired))
        object.__setattr__(self, "semantic_fingerprints", tuple(pair[1] for pair in paired))
        object.__setattr__(self, "rights_refs", require_refs(self.rights_refs, "rights_refs"))
        object.__setattr__(self, "security_refs", require_refs(self.security_refs, "security_refs"))
        if any(ref.owner_module != "m53" for ref in self.rights_refs):
            raise DNAAdmissionError("interface projection cannot assume M53 rights authority")
        if any(ref.owner_module != "m54" for ref in self.security_refs):
            raise DNAAdmissionError("interface projection cannot assume M54 security authority")


@dataclass(frozen=True)
class DependencyClosure(CanonicalRecord):
    ordered_dependency_ids: tuple[str, ...]
    resolved_refs: tuple[SemanticRef, ...]
    missing_required_ids: tuple[str, ...]
    missing_optional_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        ordered = tuple(require_identifier(item, "ordered_dependency_ids[]") for item in self.ordered_dependency_ids)
        if len(ordered) != len(set(ordered)):
            raise DNAIntegrityError("dependency closure contains duplicate dependency IDs")
        object.__setattr__(self, "ordered_dependency_ids", ordered)
        object.__setattr__(self, "resolved_refs", require_refs(self.resolved_refs, "resolved_refs"))
        object.__setattr__(self, "missing_required_ids", tuple(sorted({require_identifier(item, "missing_required_ids[]") for item in self.missing_required_ids})))
        object.__setattr__(self, "missing_optional_ids", tuple(sorted({require_identifier(item, "missing_optional_ids[]") for item in self.missing_optional_ids})))
        if set(self.missing_required_ids) & set(self.missing_optional_ids):
            raise DNAIntegrityError("dependency cannot be both required and optional")


def resolve_dependency_closure(
    manifest: ReusableDNAPackageManifest,
    available_refs: tuple[SemanticRef, ...],
    *,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> DependencyClosure:
    if not isinstance(manifest, ReusableDNAPackageManifest):
        raise DNAValidationError("manifest must be a ReusableDNAPackageManifest")
    limits.require("max_dependencies", len(manifest.dependencies))
    limits.require("max_profile_count", len(manifest.entries))
    limits.require("max_dependencies", len(available_refs))
    known = {item.dependency_id: item for item in manifest.dependencies}
    for dependency in manifest.dependencies:
        unknown = set(dependency.depends_on_ids) - set(known)
        if unknown:
            raise DNAAdmissionError(f"package dependency closure references unknown dependencies: {sorted(unknown)}")
    resolved = set(available_refs)
    visited: set[str] = set()
    active: set[str] = set()
    ordered: list[str] = []

    def visit(current: str, depth: int) -> None:
        limits.require("max_graph_depth", depth)
        if current in active:
            raise DNAIntegrityError(f"package dependency cycle reaches {current}")
        if current in visited:
            return
        active.add(current)
        for dependency_id in known[current].depends_on_ids:
            visit(dependency_id, depth + 1)
        active.remove(current)
        visited.add(current)
        ordered.append(current)
        limits.require("max_dependencies", len(visited))

    for dependency_id in sorted(known):
        visit(dependency_id, 1)
    missing_required = tuple(sorted(
        item.dependency_id for item in manifest.dependencies
        if item.required and item.target_ref not in resolved
    ))
    missing_optional = tuple(sorted(
        item.dependency_id for item in manifest.dependencies
        if not item.required and item.target_ref not in resolved
    ))
    return DependencyClosure(
        tuple(ordered),
        require_refs(tuple(known[item].target_ref for item in ordered if known[item].target_ref in resolved), "resolved_refs"),
        missing_required,
        missing_optional,
    )


def conform_package(
    manifest: ReusableDNAPackageManifest,
    revisions: tuple[DNARevision, ...],
    available_dependency_refs: tuple[SemanticRef, ...],
    *,
    schemas: TraitSchemaRegistry = DEFAULT_TRAIT_SCHEMAS,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> DNAPackageConformanceReport:
    if not isinstance(manifest, ReusableDNAPackageManifest):
        raise DNAValidationError("manifest must be a ReusableDNAPackageManifest")
    limits.require("max_dependencies", len(manifest.dependencies))
    limits.require("max_profile_count", len(manifest.entries))
    limits.require("max_profile_count", len(revisions))
    closure = resolve_dependency_closure(manifest, available_dependency_refs, limits=limits)
    revision_by_id: dict[str, DNARevision] = {}
    for revision in revisions:
        if not isinstance(revision, DNARevision):
            raise DNAValidationError("revisions must contain DNARevision records")
        if revision.dna_id in revision_by_id:
            raise DNAIntegrityError("package conformance received multiple candidate revisions for one dna_id")
        revision_by_id[revision.dna_id] = revision
    findings: set[str] = set()
    verified: list[DNARevisionRef] = []
    for entry in manifest.entries:
        revision = revision_by_id.get(entry.dna_id)
        if revision is None:
            findings.add("MISSING_CANONICAL_ENTRY")
            continue
        if revision.ref != entry.revision_ref or revision.semantic_digest != entry.semantic_fingerprint:
            findings.add("ENTRY_FINGERPRINT_OR_REVISION_MISMATCH")
            continue
        if revision.family is not entry.family:
            findings.add("ENTRY_FAMILY_MISMATCH")
            continue
        try:
            from .identity import validate_revision
            validate_revision(revision, schemas=schemas, limits=limits)
        except (DNAAdmissionError, DNAIntegrityError, DNAValidationError):
            findings.add("UNKNOWN_OR_INVALID_MANDATORY_SEMANTICS")
            continue
        verified.append(revision.ref)
    if closure.missing_required_ids:
        findings.add("MISSING_REQUIRED_DEPENDENCY")
    for extension in manifest.extensions:
        known_extension = (extension.schema_ref.family, extension.schema_ref.version) in {
            (item.family, item.version) for item in schemas.registered
        }
        if not known_extension and extension.schema_ref.mandatory:
            findings.add("UNKNOWN_MANDATORY_PACKAGE_EXTENSION")
        elif not known_extension and extension.preservation_policy_ref is None:
            findings.add("UNPRESERVED_OPTIONAL_PACKAGE_EXTENSION")
    if not manifest.rights_refs and manifest.portability is PortabilityLevel.RESTRICTED_REFERENCE:
        findings.add("RESTRICTED_PACKAGE_MISSING_RIGHTS_REFERENCE")
    if not manifest.security_refs and manifest.portability is PortabilityLevel.RESTRICTED_REFERENCE:
        findings.add("RESTRICTED_PACKAGE_MISSING_SECURITY_REFERENCE")
    valid = not findings and len(verified) == len(manifest.entries)
    body = {
        "package_id": manifest.package_id,
        "package_digest": manifest.package_digest,
        "valid": valid,
        "findings": tuple(sorted(findings)),
        "missing_required_dependencies": closure.missing_required_ids,
        "missing_optional_dependencies": closure.missing_optional_ids,
        "verified_entry_refs": tuple(sorted(verified)),
    }
    return DNAPackageConformanceReport(
        manifest.package_id,
        manifest.package_digest,
        valid,
        body["findings"],
        closure.missing_required_ids,
        closure.missing_optional_ids,
        body["verified_entry_refs"],
        report_digest=content_digest(body),
    )


def transition_package_lifecycle(
    current: PackageLifecycle,
    next_state: PackageLifecycle,
    *,
    package_ref: SemanticRef,
    authority_ref: SemanticRef,
    policy_ref: SemanticRef,
    reason: str,
    replacement_refs: tuple[SemanticRef, ...] = (),
    history_refs: tuple[SemanticRef, ...] = (),
) -> PackageLifecycleEvent:
    if not isinstance(current, PackageLifecycle):
        current = PackageLifecycle(current)
    if not isinstance(next_state, PackageLifecycle):
        next_state = PackageLifecycle(next_state)
    allowed = {
        PackageLifecycle.ACTIVE: {PackageLifecycle.DEPRECATED, PackageLifecycle.SECURITY_RESTRICTED, PackageLifecycle.RETIRED},
        PackageLifecycle.DEPRECATED: {PackageLifecycle.SECURITY_RESTRICTED, PackageLifecycle.RETIRED},
        PackageLifecycle.SECURITY_RESTRICTED: {PackageLifecycle.DEPRECATED, PackageLifecycle.RETIRED},
        PackageLifecycle.RETIRED: set(),
    }
    if next_state not in allowed[current]:
        raise DNAAdmissionError(f"package lifecycle cannot transition {current.value} -> {next_state.value}")
    if next_state is PackageLifecycle.DEPRECATED and not replacement_refs:
        raise DNAAdmissionError("deprecation must carry explicit replacement refs")
    if next_state is PackageLifecycle.RETIRED and not history_refs:
        raise DNAAdmissionError("retirement must preserve explicit package history refs")
    return PackageLifecycleEvent(
        package_ref, current, next_state, authority_ref, policy_ref, reason, replacement_refs, history_refs
    )


def project_package_interface(manifest: ReusableDNAPackageManifest) -> DNAInterfaceOnlyProjection:
    """Expose pinned identity interfaces without serializing canonical DNA payloads."""
    if not isinstance(manifest, ReusableDNAPackageManifest):
        raise DNAValidationError("manifest must be a ReusableDNAPackageManifest")
    return DNAInterfaceOnlyProjection(
        manifest.package_id,
        manifest.version,
        tuple(item.dna_id for item in manifest.entries),
        tuple(item.revision_ref for item in manifest.entries),
        tuple(item.semantic_fingerprint for item in manifest.entries),
        manifest.rights_refs,
        manifest.security_refs,
    )


def verify_package_conformance_report(report: DNAPackageConformanceReport) -> bool:
    if not isinstance(report, DNAPackageConformanceReport):
        raise DNAValidationError("report must be a DNAPackageConformanceReport")
    body = {
        "package_id": report.package_id,
        "package_digest": report.package_digest,
        "valid": report.valid,
        "findings": report.findings,
        "missing_required_dependencies": report.missing_required_dependencies,
        "missing_optional_dependencies": report.missing_optional_dependencies,
        "verified_entry_refs": report.verified_entry_refs,
    }
    return content_digest(body) == report.report_digest
