"""Semantic witnesses and externally qualified round-trip comparison."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar

from .base import IRRecord, many, one
from .common import deep_freeze, require_enum
from .enums import EquivalenceKind
from .errors import IRAdmissionError, IRIntegrityError, IRSchemaError
from .graph import IRRevision
from .identity import ExternalIdentityRef
from .versions import VALIDATOR_VERSION, canonical_value, content_digest, require_digest, require_finite_number, require_identifier, require_text, require_version

__all__ = [
    "ComparisonTolerance", "IREquivalenceProfile", "SemanticWitness", "SemanticWitnessSet",
    "RoundTripContract", "RoundTripDifference", "RoundTripReceipt", "build_witness_set",
    "build_round_trip_contract", "verify_round_trip",
]


@dataclass(frozen=True)
class ComparisonTolerance(IRRecord):
    path: str
    amount: float
    domain: str
    unit_or_reference: str
    color_space: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_text(self.path, "path", maximum=1024))
        amount = float(require_finite_number(self.amount, "amount"))
        if amount < 0:
            raise IRSchemaError("comparison tolerance cannot be negative")
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "domain", require_text(self.domain, "domain", maximum=32))
        if self.domain not in {"SCALAR", "LENGTH", "ANGLE", "COLOR", "TIME", "TRANSFORM"}:
            raise IRSchemaError("unknown tolerant comparison domain")
        object.__setattr__(self, "unit_or_reference", require_identifier(self.unit_or_reference, "unit_or_reference"))
        if self.domain == "COLOR" and self.color_space is None:
            raise IRSchemaError("color tolerance must pin a color space")
        if self.color_space is not None:
            object.__setattr__(self, "color_space", require_identifier(self.color_space, "color_space"))


@dataclass(frozen=True)
class IREquivalenceProfile(IRRecord):
    profile_id: str
    kind: EquivalenceKind
    tolerances: tuple[ComparisonTolerance, ...] = ()
    opaque_paths: tuple[str, ...] = ()
    one_way_reason: str | None = None

    NESTED: ClassVar = {"tolerances": many(ComparisonTolerance)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "kind", require_enum(self.kind, EquivalenceKind, "kind"))
        tolerances = tuple(ComparisonTolerance.coerce(item, "tolerances[]") for item in self.tolerances)
        if len({item.path for item in tolerances}) != len(tolerances):
            raise IRSchemaError("comparison tolerance paths must be unique")
        if tolerances and self.kind is not EquivalenceKind.TOLERANT:
            raise IRSchemaError("unit-aware tolerances require TOLERANT equivalence class")
        object.__setattr__(self, "tolerances", tuple(sorted(tolerances, key=lambda item: item.path)))
        object.__setattr__(self, "opaque_paths", tuple(sorted(set(require_text(item, "opaque_paths[]", maximum=1024) for item in self.opaque_paths))))
        if self.kind is EquivalenceKind.ONE_WAY and not self.one_way_reason:
            raise IRSchemaError("ONE_WAY equivalence requires an explicit reason")
        if self.one_way_reason is not None:
            object.__setattr__(self, "one_way_reason", require_text(self.one_way_reason, "one_way_reason", maximum=1024))


@dataclass(frozen=True)
class SemanticWitness(IRRecord):
    path: str
    semantic_kind: str
    value: Any
    value_digest: str
    required: bool = True
    opaque: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_text(self.path, "path", maximum=1024))
        object.__setattr__(self, "semantic_kind", require_text(self.semantic_kind, "semantic_kind", maximum=128))
        frozen = deep_freeze(self.value, "value")
        object.__setattr__(self, "value", frozen)
        object.__setattr__(self, "value_digest", require_digest(self.value_digest, "value_digest"))
        if content_digest(canonical_value(frozen)) != self.value_digest:
            raise IRIntegrityError("semantic witness digest does not match its value")
        if not isinstance(self.required, bool) or not isinstance(self.opaque, bool):
            raise IRSchemaError("witness flags must be bool")


@dataclass(frozen=True)
class SemanticWitnessSet(IRRecord):
    set_id: str
    source_revision_digest: str
    profile_id: str
    witnesses: tuple[SemanticWitness, ...]
    generated_before_adapter_inspection: bool = True
    witness_digest: str | None = None

    NESTED: ClassVar = {"witnesses": many(SemanticWitness)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "set_id", require_identifier(self.set_id, "set_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        witnesses = tuple(SemanticWitness.coerce(item, "witnesses[]") for item in self.witnesses)
        if len({item.path for item in witnesses}) != len(witnesses):
            raise IRSchemaError("semantic witness paths must be unique")
        object.__setattr__(self, "witnesses", tuple(sorted(witnesses, key=lambda item: item.path)))
        if self.generated_before_adapter_inspection is not True:
            raise IRIntegrityError("witness set must be derived before adapter-result inspection")
        if self.witness_digest is not None and self.witness_digest != self.digest:
            raise IRIntegrityError("witness-set digest mismatch")

    @property
    def digest(self) -> str:
        return content_digest({"set_id": self.set_id, "source_revision_digest": self.source_revision_digest, "profile_id": self.profile_id, "witnesses": self.witnesses, "phase": "PRE_ADAPTER_RESULT"})


def build_witness_set(revision: IRRevision, profile: IREquivalenceProfile, *, set_id: str) -> SemanticWitnessSet:
    """Derive expected canonical witnesses only from admitted source revision and profile."""
    revision, profile = IRRevision.coerce(revision, "revision"), IREquivalenceProfile.coerce(profile, "profile")
    values: dict[str, tuple[str, Any, bool]] = {}
    values["scene/representation"] = ("SCENE_REPRESENTATION", revision.scene, True)
    for node in revision.nodes:
        prefix = f"nodes/{node.ref.node_id}"
        values[f"{prefix}/representation"] = ("NODE_REPRESENTATION", node, True)
        values[f"{prefix}/kind"] = ("NODE_KIND", node.kind.value, True)
        values[f"{prefix}/attributes"] = ("NODE_ATTRIBUTES", node.attributes or {}, True)
        values[f"{prefix}/semantic_refs"] = ("SEMANTIC_REFS", tuple(item.text for item in node.semantic_refs), True)
        values[f"{prefix}/trace"] = ("TRACE", node.trace, True)
        values[f"{prefix}/quality_obligations"] = ("M01_OBLIGATIONS", tuple(item.text for item in node.quality_obligation_refs), True)
        values[f"{prefix}/resources"] = ("RESOURCE_REFS", tuple(sorted((item.identity_key for item in node.resource_refs), key=repr)), True)
        if node.interface is not None:
            values[f"{prefix}/interface"] = ("INTERFACE", node.interface, True)
    values["graph/containment"] = ("CONTAINMENT", revision.containment, True)
    values["graph/relationships"] = ("RELATIONSHIPS", revision.relationships, True)
    for field_name, records, key_name in (
        ("fragments", revision.fragments, "fragment_id"),
        ("prototypes", revision.prototypes, "prototype_id"),
        ("instances", revision.instances, "instance_id"),
        ("extensions", revision.extensions, None),
        ("spatial_references", revision.spatial_references, "reference_id"),
        ("coordinate_frames", revision.coordinate_frames, "frame_id"),
        ("transform_chains", revision.transform_chains, "chain_id"),
        ("spatial_conversion_receipts", revision.spatial_conversion_receipts, "conversion_id"),
        ("cameras", revision.cameras, None),
        ("lights", revision.lights, None),
        ("spatial_regions", revision.spatial_regions, "region_id"),
        ("materials", revision.materials, "material_id"),
        ("texture_resources", revision.texture_resources, None),
        ("material_bindings", revision.material_bindings, "binding_id"),
        ("color_values", revision.color_values, None),
        ("color_conversion_receipts", revision.color_conversion_receipts, "receipt_id"),
        ("temporal_references", revision.temporal_references, "reference_id"),
        ("temporal_markers", revision.temporal_markers, "marker_id"),
        ("temporal_relations", revision.temporal_relations, "relation_id"),
        ("temporal_samplings", revision.temporal_samplings, "sampling_id"),
        ("temporal_conversion_receipts", revision.temporal_conversion_receipts, "receipt_id"),
        ("motions", revision.motions, "motion_id"),
        ("motion_layers", revision.motion_layers, "layer_id"),
        ("audio", revision.audio, "audio_id"),
        ("audio_bindings", revision.audio_bindings, "binding_id"),
        ("music", revision.music, "music_id"),
        ("narrative_projections", revision.narrative_projections, "projection_id"),
        ("timelines", revision.timelines, "timeline_id"),
        ("sync_relations", revision.sync_relations, "relation_id"),
    ):
        for item in records:
            if key_name is not None:
                item_key = str(getattr(item, key_name))
            elif field_name == "cameras":
                item_key = item.camera_ref.node_id
            elif field_name == "lights":
                item_key = item.light_ref.node_id
            elif field_name == "texture_resources":
                item_key = item.resource.resource_id
            elif field_name == "color_values":
                semantic_ref = getattr(item, "semantic_ref", None)
                item_key = semantic_ref.text if semantic_ref is not None else f"index.{records.index(item)}"
            else:
                item_key = content_digest(item)
            values[f"{field_name}/{item_key}"] = (field_name.upper(), item, True)
    values["schema/manifest"] = ("SCHEMA_MANIFEST", revision.schema_manifest, True)
    opaque_paths = set(profile.opaque_paths)
    witnesses = tuple(
        SemanticWitness(path, kind, value, content_digest(canonical_value(value)), required=required, opaque=path in opaque_paths)
        for path, (kind, value, required) in sorted(values.items())
    )
    return SemanticWitnessSet(set_id, revision.revision_digest, profile.profile_id, witnesses)


@dataclass(frozen=True)
class RoundTripContract(IRRecord):
    contract_id: str
    source_revision_digest: str
    witness_set: SemanticWitnessSet
    profile: IREquivalenceProfile
    adapter_ref: ExternalIdentityRef
    independent_qualification_refs: tuple[ExternalIdentityRef, ...] = ()
    contract_version: str = "roundtrip-v1"

    NESTED: ClassVar = {"witness_set": one(SemanticWitnessSet), "profile": one(IREquivalenceProfile), "adapter_ref": one(ExternalIdentityRef), "independent_qualification_refs": many(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", require_identifier(self.contract_id, "contract_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "witness_set", SemanticWitnessSet.coerce(self.witness_set, "witness_set"))
        object.__setattr__(self, "profile", IREquivalenceProfile.coerce(self.profile, "profile"))
        if self.witness_set.source_revision_digest != self.source_revision_digest or self.witness_set.profile_id != self.profile.profile_id:
            raise IRIntegrityError("round-trip contract must bind the precomputed witness set/profile/source")
        adapter = ExternalIdentityRef.coerce(self.adapter_ref, "adapter_ref")
        if adapter.authority != "m04.adapter_identity":
            raise IRSchemaError("adapter ref must be an opaque adapter identity")
        object.__setattr__(self, "adapter_ref", adapter)
        evidence = tuple(ExternalIdentityRef.coerce(item, "independent_qualification_refs[]") for item in self.independent_qualification_refs)
        if any(item.authority != "m04.independent_qualification" for item in evidence):
            raise IRSchemaError("round-trip qualification evidence must come from the independent qualification namespace")
        object.__setattr__(self, "independent_qualification_refs", tuple(sorted(evidence, key=lambda item: (item.ref_id, item.version))))
        object.__setattr__(self, "contract_version", require_version(self.contract_version))

    @property
    def digest(self) -> str:
        return content_digest(self.to_payload())


@dataclass(frozen=True, order=True)
class RoundTripDifference(IRRecord):
    path: str
    expected_digest: str | None
    actual_digest: str | None
    classification: str
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_text(self.path, "path", maximum=1024))
        for name in ("expected_digest", "actual_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        object.__setattr__(self, "classification", require_text(self.classification, "classification", maximum=32))
        if self.classification not in {"LOSS", "MISSING", "UNEXPECTED", "TOLERATED"}:
            raise IRSchemaError("unknown round-trip difference classification")
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=1024))


@dataclass(frozen=True)
class RoundTripReceipt(IRRecord):
    receipt_id: str
    contract_digest: str
    source_revision_digest: str
    adapted_revision_digest: str
    differences: tuple[RoundTripDifference, ...]
    semantic_match: bool
    independently_qualified: bool
    verifier_version: str = VALIDATOR_VERSION

    NESTED: ClassVar = {"differences": many(RoundTripDifference)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt_id", require_identifier(self.receipt_id, "receipt_id"))
        for name in ("contract_digest", "source_revision_digest", "adapted_revision_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        differences = tuple(RoundTripDifference.coerce(item, "differences[]") for item in self.differences)
        object.__setattr__(self, "differences", tuple(sorted(differences, key=lambda item: (item.path, item.classification))))
        if not isinstance(self.semantic_match, bool) or not isinstance(self.independently_qualified, bool):
            raise IRSchemaError("round-trip outcome flags must be bool")
        if self.independently_qualified:
            raise IRAdmissionError("the semantic IR kernel cannot self-certify independent adapter qualification")
        if self.semantic_match != (not any(item.classification in {"LOSS", "MISSING", "UNEXPECTED"} for item in differences)):
            raise IRIntegrityError("round-trip semantic_match does not agree with path differences")
        object.__setattr__(self, "verifier_version", require_version(self.verifier_version))


def build_round_trip_contract(revision: IRRevision, profile: IREquivalenceProfile, *, contract_id: str, adapter_ref: ExternalIdentityRef, independent_qualification_refs: tuple[ExternalIdentityRef, ...] = ()) -> RoundTripContract:
    witnesses = build_witness_set(revision, profile, set_id=f"witness.{contract_id}")
    return RoundTripContract(contract_id, revision.revision_digest, witnesses, profile, adapter_ref, independent_qualification_refs)


def verify_round_trip(contract: RoundTripContract, adapted_revision: IRRevision, *, receipt_id: str) -> RoundTripReceipt:
    """Compare an adapter result against pre-result witnesses; adapter claims are not inputs."""
    contract, adapted_revision = RoundTripContract.coerce(contract, "contract"), IRRevision.coerce(adapted_revision, "adapted_revision")
    if contract.witness_set.digest is None:
        raise IRIntegrityError("round-trip witness digest is unavailable")
    actual = build_witness_set(adapted_revision, contract.profile, set_id=f"result.{receipt_id}")
    expected_by_path = {item.path: item for item in contract.witness_set.witnesses}
    actual_by_path = {item.path: item for item in actual.witnesses}
    differences: list[RoundTripDifference] = []
    tolerated = {item.path: item for item in contract.profile.tolerances}
    for path in sorted(set(expected_by_path) | set(actual_by_path)):
        expected, observed = expected_by_path.get(path), actual_by_path.get(path)
        if expected is None or observed is None:
            witness = expected or observed
            if witness is not None and (witness.required or not witness.opaque):
                differences.append(RoundTripDifference(path, expected.value_digest if expected else None, observed.value_digest if observed else None, "MISSING" if expected else "UNEXPECTED", "required canonical witness path is absent or newly introduced"))
            continue
        if expected.value_digest == observed.value_digest:
            continue
        tolerance = tolerated.get(path) if contract.profile.kind.value == "TOLERANT" else None
        if tolerance is not None and _within_tolerance(expected.value, observed.value, tolerance):
            differences.append(RoundTripDifference(path, expected.value_digest, observed.value_digest, "TOLERATED", f"difference falls within declared {tolerance.domain} tolerance {tolerance.amount} {tolerance.unit_or_reference}"))
        elif expected.opaque and path in contract.profile.opaque_paths:
            differences.append(RoundTripDifference(path, expected.value_digest, observed.value_digest, "LOSS", "opaque payload preservation digest changed"))
        else:
            differences.append(RoundTripDifference(path, expected.value_digest, observed.value_digest, "LOSS", "canonical semantic witness changed"))
    semantic_match = not any(item.classification in {"LOSS", "MISSING", "UNEXPECTED"} for item in differences)
    return RoundTripReceipt(
        receipt_id, contract.digest, contract.source_revision_digest, adapted_revision.revision_digest,
        tuple(differences), semantic_match, False,
    )


def _within_tolerance(expected: Any, observed: Any, tolerance: ComparisonTolerance) -> bool:
    """Compare one witness under an explicit semantic domain and reference pin."""
    tolerance = ComparisonTolerance.coerce(tolerance, "tolerance")
    return _compare_tolerant_value(expected, observed, tolerance)


def _compare_tolerant_value(expected: Any, observed: Any, tolerance: ComparisonTolerance) -> bool:
    from .materials import ColorValueIR
    from .spatial import QuantityIR, TransformOperation, convert_quantity
    from .temporal import DurationIR, TimePointIR, TimeRangeIR

    if type(expected) is not type(observed):
        return False

    if tolerance.domain in {"LENGTH", "ANGLE"} and isinstance(expected, QuantityIR):
        expected_dimension = "LENGTH" if tolerance.domain == "LENGTH" else "ANGLE"
        if expected.dimension.value != expected_dimension or observed.dimension != expected.dimension:
            return False
        try:
            left, _ = convert_quantity(expected, tolerance.unit_or_reference, "roundtrip.tolerance.left")
            right, _ = convert_quantity(observed, tolerance.unit_or_reference, "roundtrip.tolerance.right")
        except (IRIntegrityError, IRSchemaError):
            return False
        if left.semantic_ref != right.semantic_ref:
            return False
        return abs(float(left.value) - float(right.value)) <= tolerance.amount

    if tolerance.domain == "COLOR" and isinstance(expected, ColorValueIR):
        if (
            expected.color_space != observed.color_space
            or expected.color_space != tolerance.color_space
            or expected.encoding != observed.encoding
            or expected.encoding != tolerance.unit_or_reference
            or expected.alpha_mode != observed.alpha_mode
            or expected.semantic_ref != observed.semantic_ref
            or len(expected.components) != len(observed.components)
        ):
            return False
        return all(abs(left - right) <= tolerance.amount for left, right in zip(expected.components, observed.components))

    if tolerance.domain == "TIME" and isinstance(expected, TimePointIR):
        if (
            expected.reference_id != observed.reference_id
            or expected.reference_id != tolerance.unit_or_reference
            or expected.layer != observed.layer
        ):
            return False
        return abs(float(expected.ticks - observed.ticks)) <= tolerance.amount

    if tolerance.domain == "TIME" and isinstance(expected, DurationIR):
        if expected.reference_id != observed.reference_id or expected.reference_id != tolerance.unit_or_reference:
            return False
        return abs(float(expected.ticks - observed.ticks)) <= tolerance.amount

    if tolerance.domain == "TIME" and isinstance(expected, TimeRangeIR):
        return (
            _compare_tolerant_value(expected.start, observed.start, tolerance)
            and _compare_tolerant_value(expected.end, observed.end, tolerance)
        )

    if tolerance.domain == "TRANSFORM" and isinstance(expected, TransformOperation):
        if (
            expected.operation_id != observed.operation_id
            or expected.operation != observed.operation
            or len(expected.values) != len(observed.values)
        ):
            return False
        if expected.operation == "scale":
            if observed.unit is not None or expected.unit is not None or tolerance.unit_or_reference not in {"1", "unitless"}:
                return False
            return all(abs(left - right) <= tolerance.amount for left, right in zip(expected.values, observed.values))
        dimension = "LENGTH" if expected.operation == "translate" else "ANGLE"
        if expected.unit is None or observed.unit is None:
            return False
        try:
            left_values = tuple(
                float(convert_quantity(QuantityIR(value, expected.unit, dimension), tolerance.unit_or_reference, f"roundtrip.transform.left.{index}")[0].value)
                for index, value in enumerate(expected.values)
            )
            right_values = tuple(
                float(convert_quantity(QuantityIR(value, observed.unit, dimension), tolerance.unit_or_reference, f"roundtrip.transform.right.{index}")[0].value)
                for index, value in enumerate(observed.values)
            )
        except (IRIntegrityError, IRSchemaError):
            return False
        return all(abs(left - right) <= tolerance.amount for left, right in zip(left_values, right_values))

    if tolerance.domain == "SCALAR" and _is_number(expected) and _is_number(observed):
        return abs(float(expected) - float(observed)) <= tolerance.amount

    if is_dataclass(expected) and not isinstance(expected, type):
        return all(
            _compare_tolerant_value(getattr(expected, item.name), getattr(observed, item.name), tolerance)
            for item in fields(expected)
        )

    if isinstance(expected, Mapping):
        if set(expected) != set(observed):
            return False
        return all(_compare_tolerant_value(expected[key], observed[key], tolerance) for key in sorted(expected))

    if isinstance(expected, (tuple, list)):
        return len(expected) == len(observed) and all(
            _compare_tolerant_value(left, right, tolerance)
            for left, right in zip(expected, observed)
        )

    return canonical_value(expected) == canonical_value(observed)


def _is_number(value: Any) -> bool:
    from fractions import Fraction
    from decimal import Decimal

    return not isinstance(value, bool) and isinstance(value, (int, float, Fraction, Decimal))
