"""Closed data-only records and canonical JSON primitives for M06."""

from __future__ import annotations

import json
import math
import sys
import unicodedata
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, ClassVar

from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateLimitError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS, ProductionStateLimits

__all__ = [
    "CanonicalRecord",
    "freeze_json",
    "thaw_json",
    "canonical_value",
    "canonical_json",
    "canonical_bytes",
    "record_tag",
    "require_sequence",
    "exact_ref_key",
    "require_exact_ref",
    "require_m02_build_plan",
]


class CanonicalRecord:
    """Mixin for frozen M06 records with inert fields and explicit serialization."""

    __all__: ClassVar[tuple[str, ...]] = ()

    def to_payload(self) -> dict[str, Any]:
        if not is_dataclass(self):
            raise ProductionStateValidationError("canonical records must be dataclasses")
        return {
            item.name: canonical_value(getattr(self, item.name))
            for item in fields(self)
            if item.init and not item.metadata.get("canonical_exclude", False)
        }

    @classmethod
    def coerce(cls, value: Any, field: str = "value"):
        if isinstance(value, cls):
            return value
        if type(value) is dict:
            names = {item.name for item in fields(cls) if item.init}
            if set(value) - names:
                raise ProductionStateValidationError(f"{field} contains unknown {cls.__name__} fields")
            required = {
                item.name for item in fields(cls)
                if item.init and item.default is MISSING and item.default_factory is MISSING
            }
            if required - set(value):
                raise ProductionStateValidationError(f"{field} is missing required {cls.__name__} fields")
            try:
                return cls(**value)
            except (TypeError, ValueError) as error:
                raise ProductionStateValidationError(f"{field} is not a valid {cls.__name__}: {error}") from error
        raise ProductionStateValidationError(f"{field} must be a {cls.__name__} record")


_TRUSTED_MODULE_PREFIXES = ("iris_production_state.", "iris_project_os.", "iris_asset_dna.")


def _is_bound_package_type(candidate: type) -> bool:
    module_name = type.__getattribute__(candidate, "__module__")
    if not module_name.startswith(_TRUSTED_MODULE_PREFIXES):
        return False
    module = sys.modules.get(module_name)
    if module is None or type.__getattribute__(candidate, "__qualname__") != type.__getattribute__(candidate, "__name__"):
        return False
    return vars(module).get(type.__getattribute__(candidate, "__name__")) is candidate


def record_tag(value: Any) -> str:
    candidate = type(value)
    if not _is_bound_package_type(candidate) or not is_dataclass(candidate):
        raise ProductionStateAdmissionError(f"unregistered record type {candidate.__name__}")
    return f"{candidate.__module__}.{candidate.__qualname__}"


def freeze_json(value: Any, field: str = "value", *, depth: int = 0, limits: ProductionStateLimits = DEFAULT_LIMITS) -> Any:
    """Copy JSON values into immutable containers; reject behavior and resource bombs."""
    if depth > limits.max_json_depth:
        raise ProductionStateLimitError(f"{field} exceeds maximum nesting depth {limits.max_json_depth}")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ProductionStateValidationError(f"{field} contains a non-finite number")
        return value
    if type(value) is str:
        normalized = unicodedata.normalize("NFC", value)
        if len(normalized) > limits.max_text_chars or any(unicodedata.category(c) in {"Cc", "Cf"} for c in normalized):
            raise ProductionStateValidationError(f"{field} contains an oversized or control string")
        return normalized
    if type(value) is dict or type(value) is MappingProxyType:
        limits.require("max_json_items", len(value))
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ProductionStateValidationError(f"{field} mapping keys must be strings")
            normalized = unicodedata.normalize("NFC", key)
            if not normalized or normalized in result:
                raise ProductionStateValidationError(f"{field} has empty or normalization-colliding keys")
            result[normalized] = freeze_json(item, f"{field}.{normalized}", depth=depth + 1, limits=limits)
        return MappingProxyType(dict(sorted(result.items())))
    if type(value) in (tuple, list):
        limits.require("max_json_items", len(value))
        return tuple(freeze_json(item, f"{field}[]", depth=depth + 1, limits=limits) for item in value)
    raise ProductionStateValidationError(f"{field} must contain JSON data, got {type(value).__name__}")


def thaw_json(value: Any) -> Any:
    if type(value) in (dict, MappingProxyType):
        return {key: thaw_json(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [thaw_json(item) for item in value]
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise ProductionStateValidationError(f"cannot thaw unsupported JSON value type {type(value).__name__}")


def canonical_value(value: Any, *, depth: int = 0, limits: ProductionStateLimits = DEFAULT_LIMITS) -> Any:
    if depth > limits.max_json_depth:
        raise ProductionStateLimitError(f"canonical value exceeds maximum depth {limits.max_json_depth}")
    candidate = type(value)
    if isinstance(value, Enum):
        if not _is_bound_package_type(candidate):
            raise ProductionStateAdmissionError(f"unregistered enum type {candidate.__name__}")
        return canonical_value(value.value, depth=depth + 1, limits=limits)
    if type(value) is dict or type(value) is MappingProxyType:
        limits.require("max_json_items", len(value))
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            if type(key) is not str:
                raise ProductionStateValidationError("canonical mappings require string keys")
            canonical_key = unicodedata.normalize("NFC", key)
            if canonical_key in normalized:
                raise ProductionStateValidationError("canonical mapping keys collide after Unicode normalization")
            normalized[canonical_key] = canonical_value(value[key], depth=depth + 1, limits=limits)
        return normalized
    if type(value) in (tuple, list):
        limits.require("max_json_items", len(value))
        return [canonical_value(item, depth=depth + 1, limits=limits) for item in value]
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        normalized = unicodedata.normalize("NFC", value)
        if len(normalized) > limits.max_text_chars or any(unicodedata.category(c) in {"Cc", "Cf"} for c in normalized):
            raise ProductionStateValidationError("canonical string is too long or contains control characters")
        return normalized
    if type(value) is float:
        if not math.isfinite(value):
            raise ProductionStateValidationError("non-finite JSON numbers are forbidden")
        return value
    if is_dataclass(candidate):
        tag = record_tag(value)
        del tag
        stored = object.__getattribute__(value, "__dict__")
        if type(stored) is not dict:
            raise ProductionStateValidationError("canonical records must store inert dataclass fields")
        payload: dict[str, Any] = {}
        for item in fields(candidate):
            if item.init and not item.metadata.get("canonical_exclude", False):
                if item.name not in stored:
                    raise ProductionStateIntegrityError(f"canonical record lacks field {item.name!r}")
                payload[item.name] = canonical_value(stored[item.name], depth=depth + 1, limits=limits)
        return payload
    raise ProductionStateValidationError(f"unsupported canonical value type {candidate.__name__}")


def canonical_json(value: Any, *, limits: ProductionStateLimits = DEFAULT_LIMITS) -> str:
    try:
        return json.dumps(
            canonical_value(value, limits=limits),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, RecursionError) as error:
        if isinstance(error, ProductionStateValidationError):
            raise
        raise ProductionStateValidationError(f"value cannot be represented as canonical JSON: {error}") from error


def canonical_bytes(value: Any, *, limits: ProductionStateLimits = DEFAULT_LIMITS) -> bytes:
    encoded = canonical_json(value, limits=limits).encode("utf-8")
    limits.require("max_inline_payload_bytes", len(encoded))
    return encoded


def require_sequence(value: Any, field: str, *, maximum: int, item_type: type | tuple[type, ...] | None = None) -> tuple[Any, ...]:
    if not isinstance(value, (tuple, list)):
        raise ProductionStateValidationError(f"{field} must be a sequence")
    if len(value) > maximum:
        raise ProductionStateLimitError(f"{field} exceeds maximum length {maximum}")
    result = tuple(value)
    if item_type is not None and any(not isinstance(item, item_type) for item in result):
        raise ProductionStateValidationError(f"{field} contains a value of the wrong type")
    return result


def require_exact_ref(value: Any, field: str = "reference") -> Any:
    """Accept only stable public, versioned M02/M05 refs or M06 immutable refs."""
    try:
        from iris_project_os.identity import ExternalRef, RevisionRef
        from iris_asset_dna.base import SemanticRef
        from iris_asset_dna.identity import DNARevisionRef
        accepted = (ExternalRef, RevisionRef, SemanticRef, DNARevisionRef)
    except ImportError as error:
        raise ProductionStateAdmissionError("stable M02/M05 reference types are unavailable") from error
    if type(value) not in accepted and type(value) not in _m06_reference_types():
        raise ProductionStateValidationError(f"{field} must be an exact, versioned M02/M05/M06 reference")
    if isinstance(value, ExternalRef) and (
        value.version is None or (type(value.version) is str and value.version.casefold() in {"latest", "current"})
    ):
        raise ProductionStateValidationError(f"{field} must pin an explicit, non-latest version")
    if isinstance(value, SemanticRef) and not value.revision_pinned:
        raise ProductionStateValidationError(f"{field} must pin an explicit semantic revision")
    if isinstance(value, RevisionRef) and (not value.revision_id or not value.content_digest):
        raise ProductionStateValidationError(f"{field} must identify an exact M02 revision and digest")
    return value


def _m06_reference_types() -> tuple[type, ...]:
    try:
        from .revisions import M06_REFERENCE_TYPES
    except ImportError as error:
        raise ProductionStateAdmissionError("stable M06 reference types are unavailable") from error
    return M06_REFERENCE_TYPES


def require_m02_build_plan(value: Any, field: str = "build_plan") -> Any:
    try:
        from iris_project_os.build import BuildPlan
    except ImportError as error:
        raise ProductionStateAdmissionError("stable M02 BuildPlan type is unavailable") from error
    if type(value) is not BuildPlan:
        raise ProductionStateValidationError(f"{field} must be an exact immutable M02 BuildPlan")
    return value


def exact_ref_key(value: Any) -> str:
    require_exact_ref(value)
    return f"{type(value).__module__}.{type(value).__qualname__}:{canonical_json(value)}"
