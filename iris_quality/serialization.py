from __future__ import annotations

import json
from typing import Any, Mapping

from .contracts import FidelityContract
from .debt import QualityDebt
from .decision import QualityDecision
from .defects import Defect
from .dimensions import DimensionAssessment
from .errors import SchemaValidationError, UnsupportedVersionError
from .evidence import EvidenceRef
from .judging import JudgeResult, SubjectRef, ValidatorOutcome
from .registry import (
    DomainProfile,
    DomainProfileRegistry,
    EvaluatorDescriptor,
    EvaluatorRegistry,
    ExtensionMetadata,
)
from .versions import (
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    ComponentVersion,
    canonical_json,
    content_digest,
)
from .zones import SemanticZone

__all__ = [
    "ENVELOPE_KEYS",
    "SERIALIZABLE_TYPES",
    "dumps",
    "loads",
    "envelope",
    "from_envelope",
    "validate_payload",
    "type_name",
]

ENVELOPE_KEYS = frozenset({"schema_version", "type", "payload", "payload_sha256"})

SERIALIZABLE_TYPES: Mapping[str, Any] = {
    "component_version": ComponentVersion,
    "subject_ref": SubjectRef,
    "evidence_ref": EvidenceRef,
    "defect": Defect,
    "quality_debt": QualityDebt,
    "dimension_assessment": DimensionAssessment,
    "semantic_zone": SemanticZone,
    "fidelity_contract": FidelityContract,
    "judge_result": JudgeResult,
    "validator_outcome": ValidatorOutcome,
    "quality_decision": QualityDecision,
    "extension_metadata": ExtensionMetadata,
    "evaluator_descriptor": EvaluatorDescriptor,
    "evaluator_registry": EvaluatorRegistry,
    "domain_profile": DomainProfile,
    "domain_profile_registry": DomainProfileRegistry,
}

_TYPE_NAMES: Mapping[type, str] = {cls: name for name, cls in SERIALIZABLE_TYPES.items()}


def type_name(value: Any) -> str:
    name = _TYPE_NAMES.get(type(value))
    if name is None:
        raise SchemaValidationError(
            f"{type(value).__name__} is not a serializable kernel type; known types are "
            f"{sorted(_TYPE_NAMES.values())}"
        )
    return name


def envelope(value: Any) -> dict[str, Any]:
    """Wrap a kernel object in its versioned, tamper-evident transport record."""

    name = type_name(value)
    payload = value.to_payload()
    return {
        "schema_version": SCHEMA_VERSION,
        "type": name,
        "payload": payload,
        "payload_sha256": content_digest(payload),
    }


def from_envelope(record: Mapping[str, Any]) -> Any:
    if not isinstance(record, Mapping):
        raise SchemaValidationError("an envelope must be a mapping")
    unexpected = set(record) - set(ENVELOPE_KEYS)
    if unexpected:
        raise SchemaValidationError(f"envelope has unknown keys: {sorted(unexpected)}")
    missing = set(ENVELOPE_KEYS) - set(record)
    if missing:
        raise SchemaValidationError(f"envelope is missing keys: {sorted(missing)}")
    version = record["schema_version"]
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"unsupported schema_version {version!r}; this kernel reads {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    name = record["type"]
    handler = SERIALIZABLE_TYPES.get(name)
    if handler is None:
        raise SchemaValidationError(
            f"unknown envelope type {name!r}; this kernel accepts {sorted(SERIALIZABLE_TYPES)}"
        )
    payload = record["payload"]
    if not isinstance(payload, Mapping):
        raise SchemaValidationError("envelope payload must be a mapping")
    if content_digest(payload) != record["payload_sha256"]:
        raise SchemaValidationError(
            "envelope payload does not match payload_sha256; the record was altered in transit"
        )
    return handler.from_payload(payload)


def validate_payload(name: str, payload: Mapping[str, Any]) -> Any:
    """Rebuild then re-emit, so a payload is only valid when it round-trips unchanged."""

    handler = SERIALIZABLE_TYPES.get(name)
    if handler is None:
        raise SchemaValidationError(f"unknown kernel type {name!r}")
    value = handler.from_payload(payload)
    if value.to_payload() != json.loads(canonical_json(payload)):
        raise SchemaValidationError(
            f"{name} payload is not canonical: it changed shape when re-serialised"
        )
    return value


def dumps(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(
        envelope(value), ensure_ascii=False, sort_keys=True, indent=indent
    )


def loads(text: str) -> Any:
    if not isinstance(text, str):
        raise SchemaValidationError("loads expects JSON text")
    try:
        record = json.loads(text)
    except json.JSONDecodeError as error:
        raise SchemaValidationError(f"kernel payload is not valid JSON: {error.msg}") from error
    return from_envelope(record)
