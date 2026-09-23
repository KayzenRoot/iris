"""Exact base/target-bound immutable Hardware Genome deltas and change events."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record, content_digest
from .enums import ChangeClass, CompatibilityLevel
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .evidence import FactEnvelope
from .genome import HardwareGenome
from .schema import compare_schema_versions
from .versions import require_identifier, require_version

__all__ = [
    "FactChange", "SectionChange", "GenomeDelta", "MaterialChangeEvent", "create_genome_delta",
    "validate_genome_delta", "create_material_change_event", "validate_material_change_event",
]


def _fact_key(fact: FactEnvelope) -> str:
    observation = fact.observation
    subject = observation.subject.subject_id if observation.subject is not None else ""
    runtime = observation.runtime.runtime_id if observation.runtime is not None else ""
    return f"{subject}::{runtime}::{fact.fact_key}"


@dataclass(frozen=True)
class FactChange(M07Record):
    key: str
    before: FactEnvelope | None
    after: FactEnvelope | None
    change_class: ChangeClass

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", require_identifier(self.key, "key"))
        if self.before is None and self.after is None:
            raise HardwareGenomeValidationError("fact change must bind a before or after fact")
        if self.before is not None:
            object.__setattr__(self, "before", FactEnvelope.coerce(self.before, "before"))
        if self.after is not None:
            object.__setattr__(self, "after", FactEnvelope.coerce(self.after, "after"))
        if type(self.change_class) is not ChangeClass:
            raise HardwareGenomeValidationError("fact change class must use the closed M07 vocabulary")
        for item in (self.before, self.after):
            if item is not None and _fact_key(item) != self.key:
                raise HardwareGenomeIntegrityError("fact change key differs from its bound fact envelope")


@dataclass(frozen=True)
class SectionChange(M07Record):
    section: str
    before_digest: str
    after_digest: str
    change_class: ChangeClass

    def __post_init__(self) -> None:
        from .versions import require_digest

        object.__setattr__(self, "section", require_identifier(self.section, "section"))
        object.__setattr__(self, "before_digest", require_digest(self.before_digest, "before_digest"))
        object.__setattr__(self, "after_digest", require_digest(self.after_digest, "after_digest"))
        if type(self.change_class) is not ChangeClass:
            raise HardwareGenomeValidationError("section change class must use the closed M07 vocabulary")
        if self.before_digest == self.after_digest:
            raise HardwareGenomeIntegrityError("section change must reflect different immutable section digests")


@dataclass(frozen=True)
class GenomeDelta(M07Record):
    delta_id: str
    base_genome_id: str
    target_genome_id: str
    source_schema_version: str
    target_schema_version: str
    fact_changes: tuple[FactChange, ...]
    section_changes: tuple[SectionChange, ...]
    invalidated_fact_keys: tuple[str, ...]
    change_classes: tuple[ChangeClass, ...]
    created_at_ms: int

    def __post_init__(self) -> None:
        for field in ("delta_id", "base_genome_id", "target_genome_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if self.base_genome_id == self.target_genome_id:
            raise HardwareGenomeValidationError("genome delta requires distinct exact base and target ids")
        for field in ("source_schema_version", "target_schema_version"):
            object.__setattr__(self, field, require_version(getattr(self, field), field))
        facts = tuple(FactChange.coerce(item, "fact_changes[]") for item in self.fact_changes)
        sections = tuple(SectionChange.coerce(item, "section_changes[]") for item in self.section_changes)
        if len({item.key for item in facts}) != len(facts) or len({item.section for item in sections}) != len(sections):
            raise HardwareGenomeIntegrityError("delta fact keys and section names must be unique")
        object.__setattr__(self, "fact_changes", tuple(sorted(facts, key=lambda item: item.key)))
        object.__setattr__(self, "section_changes", tuple(sorted(sections, key=lambda item: item.section)))
        keys = tuple(sorted(set(require_identifier(item, "invalidated_fact_keys[]") for item in self.invalidated_fact_keys)))
        object.__setattr__(self, "invalidated_fact_keys", keys)
        classes = tuple(sorted(set(self.change_classes), key=lambda item: item.value))
        if any(type(item) is not ChangeClass for item in classes):
            raise HardwareGenomeValidationError("delta change classes must use the closed M07 vocabulary")
        object.__setattr__(self, "change_classes", classes)
        from .versions import require_nonnegative_int

        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))


@dataclass(frozen=True)
class MaterialChangeEvent(M07Record):
    event_id: str
    version: str
    prior_genome_id: str
    current_genome_id: str
    delta_id: str
    change_classes: tuple[ChangeClass, ...]

    def __post_init__(self) -> None:
        for field in ("event_id", "prior_genome_id", "current_genome_id", "delta_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        classes = tuple(sorted(set(self.change_classes), key=lambda item: item.value))
        if any(type(item) is not ChangeClass for item in classes):
            raise HardwareGenomeValidationError("material change classes must use the closed M07 vocabulary")
        object.__setattr__(self, "change_classes", classes)


def _class_for_fact(key: str) -> ChangeClass:
    fact = key.rsplit("::", 1)[-1]
    if fact.startswith("runtime."):
        return ChangeClass.RUNTIME_SUBSTRATE
    if fact.startswith(("driver.", "compute.api", "runtime.backend")):
        return ChangeClass.DRIVER_RUNTIME
    if fact.startswith(("precision.", "media.")):
        return ChangeClass.MEDIA_PRECISION
    if fact.startswith("topology."):
        return ChangeClass.TOPOLOGY
    if fact.startswith(("memory.", "hardware.gpu.dedicated_vram", "hardware.cpu.")):
        return ChangeClass.MEMORY_CAPACITY
    if fact.startswith("telemetry."):
        return ChangeClass.TELEMETRY_ONLY
    if fact.startswith(("visibility.", "permission.")):
        return ChangeClass.VISIBILITY_PERMISSION
    if fact.startswith("identity."):
        return ChangeClass.IDENTITY
    return ChangeClass.CAPABILITY


def _fact_map(genome: HardwareGenome) -> dict[str, FactEnvelope]:
    result: dict[str, FactEnvelope] = {}
    for item in genome.facts:
        key = _fact_key(item)
        if key in result:
            raise HardwareGenomeIntegrityError("one genome cannot contain duplicate normalized fact identity")
        result[key] = item
    return result


def _section_values(genome: HardwareGenome) -> dict[str, tuple[object, ChangeClass]]:
    return {
        "capabilities": (genome.capabilities, ChangeClass.CAPABILITY),
        "backend_relationships": (genome.backend_relationships, ChangeClass.DRIVER_RUNTIME),
        "versions": (genome.version_facts, ChangeClass.DRIVER_RUNTIME),
        "driver_skew": (genome.driver_skew, ChangeClass.DRIVER_RUNTIME),
        "precision": (genome.precision_features, ChangeClass.MEDIA_PRECISION),
        "media": (genome.media_capabilities, ChangeClass.MEDIA_PRECISION),
        "topology": (genome.topology, ChangeClass.TOPOLOGY),
        "telemetry": (genome.telemetry, ChangeClass.TELEMETRY_ONLY),
        "conflicts": (genome.conflicts, ChangeClass.CONFIDENCE_EVIDENCE),
        "schema": (genome.schema, ChangeClass.SCHEMA_ONLY),
    }


def create_genome_delta(base: HardwareGenome, target: HardwareGenome, *, delta_id: str, created_at_ms: int) -> GenomeDelta:
    base = HardwareGenome.coerce(base, "base")
    target = HardwareGenome.coerce(target, "target")
    if base.genome_id == target.genome_id:
        raise HardwareGenomeValidationError("base and target genomes must be distinct immutable snapshots")
    if base.schema.schema_id != target.schema.schema_id:
        raise HardwareGenomeAdmissionError("genome delta cannot cross unrelated schema families")
    compatibility = compare_schema_versions(base.schema.version, target.schema.version)
    if compatibility is CompatibilityLevel.MAJOR:
        raise HardwareGenomeAdmissionError("major schema changes require an explicit migration before delta comparison")
    before, after = _fact_map(base), _fact_map(target)
    changes: list[FactChange] = []
    for key in sorted(set(before) | set(after)):
        old, new = before.get(key), after.get(key)
        if old is not None and new is not None and content_digest(old) == content_digest(new):
            continue
        changes.append(FactChange(key, old, new, _class_for_fact(key)))
    section_changes: list[SectionChange] = []
    section_classes: set[ChangeClass] = set()
    old_sections, new_sections = _section_values(base), _section_values(target)
    for section in sorted(old_sections):
        old_value, change_class = old_sections[section]
        new_value, _ = new_sections[section]
        old_digest, new_digest = content_digest(old_value), content_digest(new_value)
        if old_digest != new_digest:
            section_changes.append(SectionChange(section, old_digest, new_digest, change_class))
            section_classes.add(change_class)
    classes = {item.change_class for item in changes} | section_classes
    invalidated = {item.key for item in changes if item.before is not None}
    return GenomeDelta(
        delta_id,
        base.genome_id,
        target.genome_id,
        str(base.schema.version),
        str(target.schema.version),
        tuple(changes),
        tuple(section_changes),
        tuple(sorted(invalidated)),
        tuple(sorted(classes, key=lambda item: item.value)),
        created_at_ms,
    )


def validate_genome_delta(delta: GenomeDelta, base: HardwareGenome, target: HardwareGenome) -> None:
    delta = GenomeDelta.coerce(delta, "delta")
    base = HardwareGenome.coerce(base, "base")
    target = HardwareGenome.coerce(target, "target")
    if (delta.base_genome_id, delta.target_genome_id) != (base.genome_id, target.genome_id):
        raise HardwareGenomeIntegrityError("genome delta is not authoritative for these exact base/target snapshots")
    expected = create_genome_delta(base, target, delta_id=delta.delta_id, created_at_ms=delta.created_at_ms)
    if expected != delta:
        raise HardwareGenomeIntegrityError("genome delta does not match the exact source snapshots")


def create_material_change_event(
    prior: HardwareGenome,
    current: HardwareGenome,
    delta: GenomeDelta,
    *,
    event_id: str,
    version: str,
) -> MaterialChangeEvent:
    prior, current = HardwareGenome.coerce(prior, "prior"), HardwareGenome.coerce(current, "current")
    delta = GenomeDelta.coerce(delta, "delta")
    validate_genome_delta(delta, prior, current)
    return MaterialChangeEvent(event_id, version, prior.genome_id, current.genome_id, delta.delta_id, delta.change_classes)


def validate_material_change_event(
    event: MaterialChangeEvent,
    delta: GenomeDelta,
    prior: HardwareGenome,
    current: HardwareGenome,
) -> None:
    event = MaterialChangeEvent.coerce(event, "event")
    delta = GenomeDelta.coerce(delta, "delta")
    prior, current = HardwareGenome.coerce(prior, "prior"), HardwareGenome.coerce(current, "current")
    validate_genome_delta(delta, prior, current)
    if (
        event.prior_genome_id,
        event.current_genome_id,
        event.delta_id,
        event.change_classes,
    ) != (prior.genome_id, current.genome_id, delta.delta_id, delta.change_classes):
        raise HardwareGenomeIntegrityError("material-change event differs from its exact prior/current genomes and delta")
