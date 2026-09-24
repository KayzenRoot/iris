"""Finite resource-shape feasibility and provider-neutral control negotiation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import wraps
from threading import RLock
from typing import Callable, TypeVar

from .limits import DEFAULT_LIMITS, M09Limits
from .model import Confidence, EvidenceOrigin, MutationActorKind, MutationContext, ResourceSnapshot, content_digest, require_id

_F = TypeVar("_F", bound=Callable[..., object])


def _locked(method: _F) -> _F:
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper  # type: ignore[return-value]

__all__ = [
    "Precision", "ReplanSignal", "Shape", "QualityConstraintRef",
    "ShapeEnvelope", "ProviderCapabilities", "ProviderCapabilityAdapter",
    "ShapeEvaluation", "ControlEpoch", "AdaptationBudget", "evaluate_shape",
    "SpatialUnit", "TemporalUnit", "SeamPolicy", "SpatialTileContract", "TemporalChunkContract", "BatchItemSemantics",
    "BatchIsolationContract", "PrecisionCompatibilityClass", "PrecisionCompatibility",
    "ProviderAxisCapability", "ProviderNegotiation", "ControlFeedbackState",
    "ProviderControlFeedback", "ReversibilityClass", "ReversibilityDescriptor",
    "ShapeTransition", "ShapeTransitionLedger", "BoundedShapeSet",
    "ShapeSetEvaluation", "evaluate_shape_set",
]


class Precision(str, Enum):
    FP32 = "FP32"
    BF16 = "BF16"
    FP16 = "FP16"
    INT8 = "INT8"


class ReplanSignal(str, Enum):
    FIT = "FIT"
    NO_FIT = "NO_FIT"
    REQUIRE_REPLAN = "REQUIRE_REPLAN"
    REQUIRE_OFFLOAD = "REQUIRE_OFFLOAD"
    QUALITY_AUTH_REQUIRED = "QUALITY_AUTH_REQUIRED"
    UNKNOWN = "UNKNOWN"


_PRECISION_RANK = {Precision.FP32: 4, Precision.BF16: 3, Precision.FP16: 2, Precision.INT8: 1}
_BYTES_PER_ELEMENT = {Precision.FP32: 4, Precision.BF16: 2, Precision.FP16: 2, Precision.INT8: 1}
_MAX_ARITHMETIC = (1 << 63) - 1


class SpatialUnit(str, Enum):
    PIXEL = "PIXEL"
    VOXEL = "VOXEL"


class TemporalUnit(str, Enum):
    FRAME = "FRAME"
    SAMPLE = "SAMPLE"
    MILLISECOND = "MILLISECOND"


class SeamPolicy(str, Enum):
    DOMAIN_VALIDATED = "DOMAIN_VALIDATED"
    PRESERVE_CONTEXT = "PRESERVE_CONTEXT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SpatialTileContract:
    contract_ref: str
    unit: SpatialUnit
    overlap_x: int
    overlap_y: int
    seam_policy: SeamPolicy
    context_ref: str
    seam_evidence_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_ref", require_id(self.contract_ref, "contract_ref"))
        object.__setattr__(self, "context_ref", require_id(self.context_ref, "context_ref"))
        if self.seam_evidence_ref is not None:
            object.__setattr__(self, "seam_evidence_ref", require_id(self.seam_evidence_ref, "seam_evidence_ref"))
        if not isinstance(self.unit, SpatialUnit) or not isinstance(self.seam_policy, SeamPolicy):
            raise ValueError("spatial units and seam policy must be explicit")
        if any(type(value) is not int or value < 0 or value > 65_536 for value in (self.overlap_x, self.overlap_y)):
            raise ValueError("spatial overlap must be bounded and non-negative")
        if self.seam_policy is SeamPolicy.DOMAIN_VALIDATED and self.seam_evidence_ref is None:
            raise ValueError("domain-validated seam policy requires owning evidence")
        if self.seam_policy is SeamPolicy.UNKNOWN:
            raise ValueError("unknown seam semantics cannot authorize tiling")


@dataclass(frozen=True)
class TemporalChunkContract:
    contract_ref: str
    unit: TemporalUnit
    overlap_before: int
    overlap_after: int
    continuity_ref: str
    state_context_ref: str
    reset_permitted: bool = False

    def __post_init__(self) -> None:
        for field in ("contract_ref", "continuity_ref", "state_context_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.unit, TemporalUnit) or type(self.reset_permitted) is not bool:
            raise ValueError("temporal unit and reset policy must be explicit")
        if any(type(value) is not int or value < 0 or value > 1_000_000 for value in (self.overlap_before, self.overlap_after)):
            raise ValueError("temporal overlap must be bounded and non-negative")


@dataclass(frozen=True)
class BatchItemSemantics:
    item_id: str
    semantic_config_digest: str
    seed_identity_ref: str
    acceptance_ref: str

    def __post_init__(self) -> None:
        for field in ("item_id", "seed_identity_ref", "acceptance_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if len(self.semantic_config_digest) != 64 or any(char not in "0123456789abcdef" for char in self.semantic_config_digest):
            raise ValueError("batch semantic configuration must be bound by SHA-256")


@dataclass(frozen=True)
class BatchIsolationContract:
    contract_ref: str
    items: tuple[BatchItemSemantics, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_ref", require_id(self.contract_ref, "contract_ref"))
        items = tuple(self.items)
        if not items or len(items) > 1_000_000 or any(type(item) is not BatchItemSemantics for item in items):
            raise ValueError("batch isolation requires bounded per-item semantic identities")
        if len({item.item_id for item in items}) != len(items):
            raise ValueError("batch members cannot merge or duplicate item identity")
        object.__setattr__(self, "items", items)


class PrecisionCompatibilityClass(str, Enum):
    LOSSLESS_EQUIVALENT = "LOSSLESS_EQUIVALENT"
    QUALITY_SENSITIVE = "QUALITY_SENSITIVE"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PrecisionCompatibility:
    operation_ref: str
    context_ref: str
    source_precision: Precision
    target_precision: Precision
    classification: PrecisionCompatibilityClass
    authority_ref: str
    evidence_ref: str

    def __post_init__(self) -> None:
        for field in ("operation_ref", "context_ref", "authority_ref", "evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.source_precision, Precision) or not isinstance(self.target_precision, Precision) or not isinstance(self.classification, PrecisionCompatibilityClass):
            raise ValueError("precision compatibility must be typed")
        if self.classification is PrecisionCompatibilityClass.UNKNOWN:
            raise ValueError("unknown precision compatibility cannot be asserted as evidence")


@dataclass(frozen=True)
class ProviderAxisCapability:
    control: str
    minimum: int
    maximum: int
    step: int
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "control", require_id(self.control, "control"))
        object.__setattr__(self, "unit", require_id(self.unit, "unit"))
        if any(type(value) is not int or not 1 <= value <= 1_000_000 for value in (self.minimum, self.maximum, self.step)) or self.minimum > self.maximum:
            raise ValueError("provider control range and quantization step must be finite")


@dataclass(frozen=True)
class ProviderNegotiation:
    state: str
    shape_digest: str
    requested_values: tuple[tuple[str, int], ...]
    provider_values: tuple[tuple[str, int], ...]
    payload: tuple[tuple[str, str], ...]
    exact: bool


class ControlFeedbackState(str, Enum):
    REQUESTED = "REQUESTED"
    APPLIED = "APPLIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProviderControlFeedback:
    resource_key: str
    epoch: int
    shape_digest: str
    state: ControlFeedbackState
    requested_payload: tuple[tuple[str, str], ...]
    applied_payload: tuple[tuple[str, str], ...] | None
    evidence_ref: str | None
    observed_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource_key", require_id(self.resource_key, "resource_key"))
        if not isinstance(self.state, ControlFeedbackState) or type(self.epoch) is not int or self.epoch < 1:
            raise ValueError("control feedback state and epoch must be explicit")
        if len(self.shape_digest) != 64 or any(char not in "0123456789abcdef" for char in self.shape_digest):
            raise ValueError("control feedback must bind a shape digest")
        if self.evidence_ref is not None:
            object.__setattr__(self, "evidence_ref", require_id(self.evidence_ref, "evidence_ref"))
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("provider feedback requires a non-negative observation time")
        if self.state is not ControlFeedbackState.REQUESTED and self.evidence_ref is None:
            raise ValueError("provider feedback requires an evidence reference")
        if self.state in {ControlFeedbackState.REQUESTED, ControlFeedbackState.UNKNOWN, ControlFeedbackState.FAILED} and self.applied_payload is not None:
            raise ValueError("requested/unknown/failed provider feedback cannot assert applied values")
        if self.state in {ControlFeedbackState.APPLIED, ControlFeedbackState.VERIFIED} and self.applied_payload is None:
            raise ValueError("applied/verified provider feedback requires exact applied values")


class ReversibilityClass(str, Enum):
    REVERSIBLE = "REVERSIBLE"
    REQUIRES_RELOAD = "REQUIRES_RELOAD"
    MATERIAL = "MATERIAL"


@dataclass(frozen=True)
class ReversibilityDescriptor:
    classification: ReversibilityClass
    evidence_ref: str
    materiality_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.classification, ReversibilityClass):
            raise ValueError("control reversibility must be explicit")
        object.__setattr__(self, "evidence_ref", require_id(self.evidence_ref, "evidence_ref"))
        if self.materiality_ref is not None:
            object.__setattr__(self, "materiality_ref", require_id(self.materiality_ref, "materiality_ref"))
        if self.classification is ReversibilityClass.MATERIAL and self.materiality_ref is None:
            raise ValueError("material control transition requires M06 materiality evidence")


@dataclass(frozen=True)
class Shape:
    tile_width: int
    tile_height: int
    temporal_chunk: int
    batch_size: int
    precision: Precision
    channels: int = 4
    halo: int = 0
    isolated_batch_items: bool = True
    operation_ref: str = "operation:default"
    context_ref: str = "context:default"
    spatial_contract: SpatialTileContract | None = None
    temporal_contract: TemporalChunkContract | None = None
    batch_contract: BatchIsolationContract | None = None
    materiality_ref: str | None = None

    def __post_init__(self) -> None:
        for field in ("tile_width", "tile_height", "temporal_chunk", "batch_size", "channels"):
            value = getattr(self, field)
            if type(value) is not int or not 1 <= value <= 1_000_000:
                raise ValueError(f"{field} must be a positive bounded integer")
        if type(self.halo) is not int or not 0 <= self.halo <= 65_536:
            raise ValueError("halo must be bounded and non-negative")
        if not isinstance(self.precision, Precision):
            raise ValueError("precision must be explicit")
        if type(self.isolated_batch_items) is not bool:
            raise ValueError("batch isolation state must be explicit")
        object.__setattr__(self, "operation_ref", require_id(self.operation_ref, "operation_ref"))
        object.__setattr__(self, "context_ref", require_id(self.context_ref, "context_ref"))
        for field, expected in (("spatial_contract", SpatialTileContract), ("temporal_contract", TemporalChunkContract), ("batch_contract", BatchIsolationContract)):
            value = getattr(self, field)
            if value is not None and type(value) is not expected:
                raise ValueError(f"{field} must use its exact typed contract")
        if self.materiality_ref is not None:
            object.__setattr__(self, "materiality_ref", require_id(self.materiality_ref, "materiality_ref"))

    @property
    def estimated_bytes(self) -> int:
        overlap_x = max(self.halo, self.spatial_contract.overlap_x) if self.spatial_contract else self.halo
        overlap_y = max(self.halo, self.spatial_contract.overlap_y) if self.spatial_contract else self.halo
        temporal_extra = self.temporal_contract.overlap_before + self.temporal_contract.overlap_after if self.temporal_contract else 0
        width = self.tile_width + 2 * overlap_x
        height = self.tile_height + 2 * overlap_y
        temporal_extent = self.temporal_chunk + temporal_extra
        factors = (width, height, temporal_extent, self.batch_size, self.channels, _BYTES_PER_ELEMENT[self.precision])
        result = 1
        for factor in factors:
            if result > _MAX_ARITHMETIC // factor:
                raise ValueError("shape estimate overflows the bounded arithmetic envelope")
            result *= factor
        return result


@dataclass(frozen=True)
class QualityConstraintRef:
    authority_ref: str
    constraint_ref: str
    minimum_precision: Precision
    allow_degradation: bool = False
    consent_ref: str | None = None
    protected_semantics_ref: str | None = None
    operation_ref: str | None = None
    context_ref: str | None = None
    authorized_shape_digest: str | None = None
    consent_expires_at_ms: int | None = None
    quality_equivalence_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_ref", require_id(self.authority_ref, "authority_ref"))
        object.__setattr__(self, "constraint_ref", require_id(self.constraint_ref, "constraint_ref"))
        if self.authority_ref.split(":", 1)[0] not in {"M01", "M03"}:
            raise ValueError("quality constraint must be owned by M01 or M03")
        if not isinstance(self.minimum_precision, Precision) or type(self.allow_degradation) is not bool:
            raise ValueError("quality constraint precision/consent must be explicit")
        if self.consent_ref is not None:
            object.__setattr__(self, "consent_ref", require_id(self.consent_ref, "consent_ref"))
        if self.protected_semantics_ref is not None:
            object.__setattr__(self, "protected_semantics_ref", require_id(self.protected_semantics_ref, "protected_semantics_ref"))
        for field in ("operation_ref", "context_ref", "quality_equivalence_ref"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_id(value, field))
        if self.authorized_shape_digest is not None and (len(self.authorized_shape_digest) != 64 or any(char not in "0123456789abcdef" for char in self.authorized_shape_digest)):
            raise ValueError("authorized shape scope must be a SHA-256 digest")
        if self.allow_degradation and any(value is None for value in (self.consent_ref, self.operation_ref, self.context_ref, self.authorized_shape_digest, self.consent_expires_at_ms)):
            raise ValueError("degradation consent requires exact operation, context, shape and expiry scope")
        if self.operation_ref is None or self.context_ref is None:
            raise ValueError("quality constraints must bind an exact operation and context")
        if self.consent_expires_at_ms is not None and (type(self.consent_expires_at_ms) is not int or self.consent_expires_at_ms < 0):
            raise ValueError("degradation consent expiry must be a non-negative timestamp")
        if self.authority_ref.split(":", 1)[0] == "M03" and self.protected_semantics_ref is None:
            raise ValueError("M03 constraint must retain its protected-semantics reference")


@dataclass(frozen=True)
class ShapeEnvelope:
    max_allocatable_bytes: int | None
    minimum_tile_width: int
    minimum_tile_height: int
    minimum_temporal_chunk: int
    maximum_batch_size: int
    allowed_precisions: tuple[Precision, ...]
    envelope_ref: str
    evidence_ref: str
    resource_snapshot_digest: str
    resource_epoch: int

    def __post_init__(self) -> None:
        if self.max_allocatable_bytes is not None and (type(self.max_allocatable_bytes) is not int or self.max_allocatable_bytes < 0):
            raise ValueError("allocatable byte limit must be non-negative or unknown")
        for field in ("minimum_tile_width", "minimum_tile_height", "minimum_temporal_chunk", "maximum_batch_size"):
            value = getattr(self, field)
            if type(value) is not int or value < 1:
                raise ValueError(f"{field} must be positive")
        precisions = tuple(self.allowed_precisions)
        if not precisions or len(set(precisions)) != len(precisions) or any(not isinstance(item, Precision) for item in precisions):
            raise ValueError("allowed precision set must be finite, non-empty and unique")
        object.__setattr__(self, "allowed_precisions", tuple(sorted(precisions, key=lambda item: item.value)))
        object.__setattr__(self, "envelope_ref", require_id(self.envelope_ref, "envelope_ref"))
        object.__setattr__(self, "evidence_ref", require_id(self.evidence_ref, "evidence_ref"))
        if not self.evidence_ref.startswith("M08:"):
            raise ValueError("shape envelope capability evidence remains owned by M08")
        if len(self.resource_snapshot_digest) != 64 or any(char not in "0123456789abcdef" for char in self.resource_snapshot_digest):
            raise ValueError("shape envelope must bind the exact M09 resource snapshot digest")
        if type(self.resource_epoch) is not int or self.resource_epoch < 1:
            raise ValueError("shape envelope must bind a positive resource epoch")


@dataclass(frozen=True)
class ProviderCapabilities:
    adapter_ref: str
    supported_precisions: tuple[Precision, ...]
    precision_tokens: tuple[tuple[Precision, str], ...]
    max_batch_size: int
    supports_tile: bool
    supports_temporal_chunks: bool
    reversible_controls: tuple[str, ...]
    axis_capabilities: tuple[ProviderAxisCapability, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "adapter_ref", require_id(self.adapter_ref, "adapter_ref"))
        if type(self.max_batch_size) is not int or self.max_batch_size < 1:
            raise ValueError("provider batch ceiling must be positive")
        precisions = tuple(self.supported_precisions)
        if any(not isinstance(item, Precision) for item in precisions) or len(set(precisions)) != len(precisions):
            raise ValueError("provider precision capabilities must be typed and unique")
        tokens = tuple(self.precision_tokens)
        if {precision for precision, _ in tokens} != set(precisions) or len(tokens) != len(precisions):
            raise ValueError("provider precision token map must cover exact supported precision set")
        for _, token in tokens:
            object.__setattr__(self, "adapter_ref", require_id(self.adapter_ref, "adapter_ref"))
            if type(token) is not str or not token or len(token) > 64:
                raise ValueError("provider precision token must be bounded inert text")
        if type(self.supports_tile) is not bool or type(self.supports_temporal_chunks) is not bool:
            raise ValueError("provider shape capabilities must be explicit booleans")
        object.__setattr__(self, "precision_tokens", tuple(sorted(tokens, key=lambda item: item[0].value)))
        object.__setattr__(self, "reversible_controls", tuple(sorted({require_id(item, "reversible_control") for item in self.reversible_controls})))
        axes = tuple(self.axis_capabilities)
        if len(axes) > 8 or any(type(item) is not ProviderAxisCapability for item in axes) or len({item.control for item in axes}) != len(axes):
            raise ValueError("provider axis capabilities must be a bounded unique typed set")
        object.__setattr__(self, "axis_capabilities", tuple(sorted(axes, key=lambda item: item.control)))


@dataclass(frozen=True)
class ProviderCapabilityAdapter:
    """Maps finite canonical controls to declared inert provider tokens."""

    capabilities: ProviderCapabilities

    def __post_init__(self) -> None:
        if type(self.capabilities) is not ProviderCapabilities:
            raise ValueError("adapter requires an exact ProviderCapabilities record")

    def map(self, shape: Shape) -> tuple[tuple[str, str], ...] | None:
        negotiation = self.negotiate(shape)
        if negotiation is None or not negotiation.exact:
            return None
        return negotiation.payload

    def negotiate(self, shape: Shape) -> ProviderNegotiation | None:
        if type(shape) is not Shape or shape.precision not in self.capabilities.supported_precisions:
            return None
        if shape.batch_contract is None or len(shape.batch_contract.items) != shape.batch_size:
            return None
        if shape.tile_width > 1 or shape.tile_height > 1:
            if shape.spatial_contract is None or shape.spatial_contract.overlap_x < shape.halo or shape.spatial_contract.overlap_y < shape.halo:
                return None
        if shape.temporal_chunk > 1 and shape.temporal_contract is None:
            return None
        tokens = dict(self.capabilities.precision_tokens)
        requested = {"batch_size": shape.batch_size, "tile_height": shape.tile_height, "tile_width": shape.tile_width, "temporal_chunk": shape.temporal_chunk}
        controls = {"batch_size"}
        if self.capabilities.supports_tile:
            controls.update(("tile_height", "tile_width"))
        elif shape.tile_width != 1 or shape.tile_height != 1:
            return None
        if self.capabilities.supports_temporal_chunks:
            controls.add("temporal_chunk")
        elif shape.temporal_chunk != 1:
            return None
        declared = {item.control: item for item in self.capabilities.axis_capabilities}
        if not controls.issubset(declared):
            return None
        provider_values: dict[str, int] = {}
        for control in controls:
            axis = declared[control]
            expected_unit = "ITEM" if control == "batch_size" else (
                shape.spatial_contract.unit.value if control.startswith("tile_") and shape.spatial_contract else
                shape.temporal_contract.unit.value if control == "temporal_chunk" and shape.temporal_contract else
                None
            )
            if expected_unit is None or axis.unit != expected_unit:
                return None
            value = requested[control]
            if not axis.minimum <= value <= axis.maximum:
                return None
            provider_values[control] = axis.minimum + ((value - axis.minimum) // axis.step) * axis.step
        result = tuple((name, str(provider_values[name])) for name in ("batch_size", "tile_height", "tile_width", "temporal_chunk") if name in controls)
        result += (("precision", tokens[shape.precision]),)
        exact = all(requested[name] == provider_values[name] for name in controls)
        return ProviderNegotiation(
            "REQUESTED" if exact else "QUANTIZED_REQUESTED",
            content_digest(shape),
            tuple(sorted((name, requested[name]) for name in controls)),
            tuple(sorted(provider_values.items())),
            result,
            exact,
        )


@dataclass(frozen=True)
class ShapeEvaluation:
    signal: ReplanSignal
    shape_digest: str
    estimated_bytes: int | None
    provider_payload: tuple[tuple[str, str], ...]
    reason: str
    quality_authorization_ref: str | None
    resource_snapshot_digest: str | None = None
    synthetic_only: bool = False
    resource_key: str | None = None
    resource_epoch: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.signal, ReplanSignal):
            raise ValueError("shape evaluation signal must be explicit")
        if len(self.shape_digest) != 64 or any(char not in "0123456789abcdef" for char in self.shape_digest):
            raise ValueError("shape evaluation must bind a SHA-256 shape digest")
        if self.estimated_bytes is not None and (type(self.estimated_bytes) is not int or self.estimated_bytes < 0):
            raise ValueError("shape estimate must be non-negative or unknown")
        if type(self.synthetic_only) is not bool:
            raise ValueError("shape evidence origin must be explicit")
        if self.resource_snapshot_digest is not None and (len(self.resource_snapshot_digest) != 64 or any(char not in "0123456789abcdef" for char in self.resource_snapshot_digest)):
            raise ValueError("shape evaluation snapshot binding must be a SHA-256 digest")
        if self.resource_key is not None:
            object.__setattr__(self, "resource_key", require_id(self.resource_key, "resource_key"))
        if self.resource_epoch is not None and (type(self.resource_epoch) is not int or self.resource_epoch < 1):
            raise ValueError("shape evaluation resource epoch must be positive")


@dataclass(frozen=True)
class ControlEpoch:
    resource_key: str
    epoch: int
    changed_at_ms: int
    shape_digest: str
    previous_epoch: int | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource_key", require_id(self.resource_key, "resource_key"))
        if type(self.epoch) is not int or self.epoch < 1 or type(self.changed_at_ms) is not int or self.changed_at_ms < 0:
            raise ValueError("control epoch and time must be positive")
        if self.previous_epoch is not None and (type(self.previous_epoch) is not int or self.previous_epoch >= self.epoch):
            raise ValueError("previous control epoch must precede current epoch")


class AdaptationBudget:
    """Bounds control churn and enforces dwell time without selecting a workload plan."""

    def __init__(self, *, max_changes: int, window_ms: int, minimum_dwell_ms: int, max_magnitude: int = 4) -> None:
        if any(type(value) is not int or value < 1 for value in (max_changes, window_ms, max_magnitude)) or type(minimum_dwell_ms) is not int or minimum_dwell_ms < 0:
            raise ValueError("adaptation budget must be finite")
        self.max_changes = max_changes
        self.window_ms = window_ms
        self.minimum_dwell_ms = minimum_dwell_ms
        self.max_magnitude = max_magnitude
        self._changes: list[tuple[int, int]] = []
        self._last_change_ms: int | None = None
        self._lock = RLock()

    @_locked
    def allow(self, *, now_ms: int, magnitude: int) -> bool:
        if type(now_ms) is not int or now_ms < 0 or type(magnitude) is not int or magnitude < 1:
            return False
        self._changes = [(at, size) for at, size in self._changes if now_ms - at <= self.window_ms]
        if len(self._changes) >= self.max_changes or magnitude > self.max_magnitude:
            return False
        if self._last_change_ms is not None and now_ms - self._last_change_ms < self.minimum_dwell_ms:
            return False
        self._changes.append((now_ms, magnitude))
        self._last_change_ms = now_ms
        return True


@dataclass(frozen=True)
class ShapeTransition:
    transition_id: str
    idempotency_key: str
    resource_key: str
    resource_snapshot_digest: str
    resource_epoch: int
    prior_epoch: int
    requested_epoch: int
    requested_shape: Shape
    negotiation: ProviderNegotiation
    state: ControlFeedbackState
    authorization_ref: str
    causal_evidence_refs: tuple[str, ...]
    reversibility: ReversibilityDescriptor
    created_at_ms: int
    feedback_ref: str | None = None
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        if type(self.mutation_context) is not MutationContext:
            raise ValueError("shape transition requires explicit mutation attribution")
        if (self.mutation_context.authorization_ref, self.mutation_context.idempotency_key) != (self.authorization_ref, self.idempotency_key):
            raise ValueError("shape mutation context must bind exact authorization and idempotency identity")
        if self.mutation_context.causal_request_ref not in self.causal_evidence_refs:
            raise ValueError("shape mutation context causal request must be in the evidence references")


class ShapeTransitionLedger:
    """Append-only requested/applied/verified control history; it never invokes a provider."""

    def __init__(self, *, resource_key: str, initial_shape: Shape, initial_epoch: int, initial_resource_epoch: int = 1, max_history: int = 256) -> None:
        self.resource_key = require_id(resource_key, "resource_key")
        if type(initial_shape) is not Shape or type(initial_epoch) is not int or initial_epoch < 1 or type(initial_resource_epoch) is not int or initial_resource_epoch < 1 or type(max_history) is not int or not 1 <= max_history <= 4_096:
            raise ValueError("shape transition ledger bounds and initial state are explicit")
        self._shape = initial_shape
        self._epoch = initial_epoch
        self._resource_epoch = initial_resource_epoch
        self._max_history = max_history
        self._history: list[ShapeTransition] = []
        self._by_id: dict[str, int] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}
        self._feedback_replays: dict[tuple[str, ControlFeedbackState], tuple[str, int]] = {}
        self._last_event_ms = -1
        self._lock = RLock()

    @_locked
    def request(
        self,
        *,
        transition_id: str,
        idempotency_key: str,
        expected_epoch: int,
        expected_resource_epoch: int,
        shape: Shape,
        negotiation: ProviderNegotiation,
        evaluation: ShapeEvaluation,
        authorization_ref: str,
        causal_evidence_refs: tuple[str, ...],
        reversibility: ReversibilityDescriptor,
        now_ms: int,
        mutation_context: MutationContext | None = None,
    ) -> ShapeTransition:
        transition_id = require_id(transition_id, "transition_id")
        idempotency_key = require_id(idempotency_key, "idempotency_key")
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        refs = tuple(sorted(set(require_id(item, "causal_evidence_ref") for item in causal_evidence_refs)))
        context = mutation_context or MutationContext(
            MutationActorKind.INTERACTIVE, "M09:shape-client", authorization_ref,
            refs[0] if refs else "M09:missing-causal-ref", idempotency_key,
        )
        if not refs or type(shape) is not Shape or type(negotiation) is not ProviderNegotiation or type(evaluation) is not ShapeEvaluation or type(reversibility) is not ReversibilityDescriptor:
            raise ValueError("shape request requires exact evaluation, negotiation, authorization and causal evidence")
        if type(context) is not MutationContext or context.authorization_ref != authorization_ref or context.idempotency_key != idempotency_key or context.causal_request_ref not in refs:
            raise ValueError("shape mutation context must bind exact authorization, cause and idempotency identity")
        if negotiation.shape_digest != content_digest(shape) or type(now_ms) is not int or now_ms < 0:
            raise ValueError("shape request negotiation must bind its exact shape and time")
        if not negotiation.exact or evaluation.signal is not ReplanSignal.FIT or evaluation.synthetic_only or evaluation.shape_digest != negotiation.shape_digest or evaluation.provider_payload != negotiation.payload or evaluation.resource_key != self.resource_key or evaluation.resource_epoch != expected_resource_epoch or evaluation.resource_snapshot_digest is None:
            raise ValueError("only an exact production FIT bound to current resource evidence can be requested")
        if expected_resource_epoch != self._resource_epoch or now_ms < self._last_event_ms:
            raise ValueError("shape request uses stale resource epoch or non-monotonic event time")
        prior = self._idempotency.get(idempotency_key)
        request_digest = content_digest({"resource_key": self.resource_key, "expected_epoch": expected_epoch, "expected_resource_epoch": expected_resource_epoch, "shape": shape, "negotiation": negotiation, "evaluation": evaluation, "authorization_ref": authorization_ref, "causal_refs": refs, "reversibility": reversibility, "mutation_context": context})
        if prior is not None:
            if prior[0] != request_digest:
                raise ValueError("shape idempotency key binds conflicting transition semantics")
            return self._history[self._by_id[prior[1]]]
        if transition_id in self._by_id or expected_epoch != self._epoch:
            raise ValueError("shape transition identity or resource epoch is stale")
        if any(self._history[index].state in {ControlFeedbackState.REQUESTED, ControlFeedbackState.APPLIED, ControlFeedbackState.UNKNOWN} for index in self._by_id.values()):
            raise ValueError("a prior shape transition still lacks terminal provider evidence")
        if reversibility.classification is ReversibilityClass.MATERIAL and shape.materiality_ref != reversibility.materiality_ref:
            raise ValueError("M06 materiality evidence must bind the exact shape transition")
        if len(self._history) >= self._max_history:
            raise ValueError("shape transition history bound is exhausted")
        current = ShapeTransition(
            transition_id, idempotency_key, self.resource_key, evaluation.resource_snapshot_digest,
            expected_resource_epoch, self._epoch,
            self._epoch + 1, shape, negotiation, ControlFeedbackState.REQUESTED,
            authorization_ref, refs, reversibility, now_ms,
            mutation_context=context,
        )
        index = len(self._history)
        self._history.append(current)
        self._by_id[transition_id] = index
        self._idempotency[idempotency_key] = (request_digest, transition_id)
        self._last_event_ms = now_ms
        return current

    @_locked
    def record_feedback(self, transition_id: str, feedback: ProviderControlFeedback) -> ShapeTransition:
        transition_id = require_id(transition_id, "transition_id")
        index = self._by_id.get(transition_id)
        if index is None or type(feedback) is not ProviderControlFeedback:
            raise ValueError("provider feedback must refer to an existing shape request")
        current = self._history[index]
        if feedback.resource_key != self.resource_key or feedback.epoch != current.requested_epoch or feedback.shape_digest != current.negotiation.shape_digest:
            raise ValueError("provider feedback resource, epoch or shape digest is stale")
        if feedback.requested_payload != current.negotiation.payload:
            raise ValueError("provider feedback requested payload differs from the canonical request")
        if feedback.state is ControlFeedbackState.VERIFIED and feedback.applied_payload != current.negotiation.payload:
            raise ValueError("verified provider payload differs from the negotiated canonical values")
        if feedback.state is ControlFeedbackState.REQUESTED:
            raise ValueError("provider feedback cannot move a transition backwards to REQUESTED")
        replay_key = (transition_id, feedback.state)
        feedback_digest = content_digest(feedback)
        replay = self._feedback_replays.get(replay_key)
        if replay is not None:
            if replay[0] != feedback_digest:
                raise ValueError("provider feedback state cannot be overwritten with conflicting evidence")
            return self._history[replay[1]]
        if feedback.observed_at_ms < self._last_event_ms or feedback.observed_at_ms < current.created_at_ms:
            raise ValueError("provider feedback time is stale or non-monotonic")
        allowed = {
            ControlFeedbackState.REQUESTED: {ControlFeedbackState.APPLIED, ControlFeedbackState.VERIFIED, ControlFeedbackState.FAILED, ControlFeedbackState.UNKNOWN},
            ControlFeedbackState.APPLIED: {ControlFeedbackState.VERIFIED, ControlFeedbackState.FAILED, ControlFeedbackState.UNKNOWN},
            ControlFeedbackState.UNKNOWN: {ControlFeedbackState.APPLIED, ControlFeedbackState.VERIFIED, ControlFeedbackState.FAILED},
            ControlFeedbackState.FAILED: set(),
            ControlFeedbackState.VERIFIED: set(),
        }
        if feedback.state not in allowed[current.state]:
            raise ValueError("provider feedback transition is terminal or out of order")
        if len(self._history) >= self._max_history:
            raise ValueError("shape transition evidence history bound is exhausted")
        updated = ShapeTransition(
            current.transition_id, current.idempotency_key, current.resource_key,
            current.resource_snapshot_digest, current.resource_epoch,
            current.prior_epoch, current.requested_epoch, current.requested_shape,
            current.negotiation, feedback.state, current.authorization_ref,
            current.causal_evidence_refs, current.reversibility,
            current.created_at_ms, feedback.evidence_ref,
            mutation_context=current.mutation_context,
        )
        new_index = len(self._history)
        self._history.append(updated)
        self._by_id[transition_id] = new_index
        self._feedback_replays[replay_key] = (feedback_digest, new_index)
        self._last_event_ms = feedback.observed_at_ms
        if feedback.state is ControlFeedbackState.VERIFIED:
            self._shape = current.requested_shape
            self._epoch = current.requested_epoch
        return updated

    @_locked
    def current(self) -> tuple[Shape, int]:
        return self._shape, self._epoch

    @_locked
    def history(self) -> tuple[ShapeTransition, ...]:
        return tuple(self._history)


@dataclass(frozen=True)
class BoundedShapeSet:
    shapes: tuple[Shape, ...]
    maximum_candidates: int = 256

    def __post_init__(self) -> None:
        shapes = tuple(self.shapes)
        if type(self.maximum_candidates) is not int or not 1 <= self.maximum_candidates <= 4_096 or not shapes or len(shapes) > self.maximum_candidates:
            raise ValueError("shape candidate set must be explicitly finite and bounded")
        if any(type(item) is not Shape for item in shapes) or len({content_digest(item) for item in shapes}) != len(shapes):
            raise ValueError("shape candidate set must contain unique exact M09 shapes")
        object.__setattr__(self, "shapes", shapes)


@dataclass(frozen=True)
class ShapeSetEvaluation:
    candidate_digests: tuple[str, ...]
    evaluations: tuple[ShapeEvaluation, ...]
    steps: int
    truncated: bool


def evaluate_shape(
    shape: Shape,
    envelope: ShapeEnvelope,
    provider: ProviderCapabilities,
    *,
    quality: QualityConstraintRef | None,
    current_epoch: int,
    expected_epoch: int,
    current_snapshot: ResourceSnapshot,
    current_resource_epoch: int,
    now_ms: int,
    precision_compatibility: PrecisionCompatibility | None = None,
) -> ShapeEvaluation:
    digest = content_digest(shape)
    snapshot_digest = current_snapshot.digest if type(current_snapshot) is ResourceSnapshot else None
    synthetic = type(current_snapshot) is ResourceSnapshot and current_snapshot.evidence_origin is EvidenceOrigin.SYNTHETIC_FIXTURE

    def result(signal: ReplanSignal, estimate: int | None, payload: tuple[tuple[str, str], ...], reason: str, consent: str | None = None) -> ShapeEvaluation:
        resource_key = current_snapshot.identity.stable_key if type(current_snapshot) is ResourceSnapshot else None
        resource_epoch = current_resource_epoch if type(current_resource_epoch) is int and current_resource_epoch >= 1 else None
        return ShapeEvaluation(signal, digest, estimate, payload, reason, consent, snapshot_digest, synthetic, resource_key, resource_epoch)

    if expected_epoch != current_epoch:
        return result(ReplanSignal.REQUIRE_REPLAN, None, (), "stale control epoch")
    if type(current_snapshot) is not ResourceSnapshot or type(now_ms) is not int or now_ms < 0 or type(current_resource_epoch) is not int or current_resource_epoch < 1:
        return result(ReplanSignal.UNKNOWN, None, (), "exact current resource snapshot, epoch and clock are required")
    if envelope.resource_epoch != current_resource_epoch or envelope.resource_snapshot_digest != current_snapshot.digest:
        return result(ReplanSignal.REQUIRE_REPLAN, None, (), "shape envelope is bound to a stale resource snapshot or epoch")
    if current_snapshot.confidence in {Confidence.CONFLICTED, Confidence.QUARANTINED, Confidence.STALE}:
        return result(ReplanSignal.REQUIRE_REPLAN, None, (), "conflicted, quarantined or stale resource truth cannot authorize adaptation")
    if not current_snapshot.is_fresh(now_ms):
        return result(ReplanSignal.UNKNOWN, None, (), "current resource snapshot is not fresh observed truth")
    try:
        available_bytes = current_snapshot.capacity.available_bytes()
    except ValueError:
        return result(ReplanSignal.UNKNOWN, None, (), "unknown resource capacity cannot authorize shape feasibility")
    if envelope.max_allocatable_bytes is None:
        return result(ReplanSignal.UNKNOWN, None, (), "allocatable capacity is unknown")
    try:
        estimate = shape.estimated_bytes
    except ValueError:
        return result(ReplanSignal.NO_FIT, None, (), "bounded shape arithmetic overflow")
    if shape.spatial_contract is None or shape.spatial_contract.overlap_x < shape.halo or shape.spatial_contract.overlap_y < shape.halo:
        return result(ReplanSignal.NO_FIT, estimate, (), "tile overlap, axes or context contract is missing")
    if shape.temporal_contract is None or shape.temporal_contract.overlap_before + shape.temporal_contract.overlap_after >= shape.temporal_chunk:
        return result(ReplanSignal.NO_FIT, estimate, (), "temporal continuity, overlap or state-context contract is missing")
    if shape.batch_contract is None or len(shape.batch_contract.items) != shape.batch_size:
        return result(ReplanSignal.NO_FIT, estimate, (), "per-item batch identity/configuration/seed/acceptance contract is missing")
    if shape.tile_width < envelope.minimum_tile_width or shape.tile_height < envelope.minimum_tile_height or shape.temporal_chunk < envelope.minimum_temporal_chunk:
        return result(ReplanSignal.NO_FIT, estimate, (), "shape violates structural minimum")
    if shape.batch_size > min(envelope.maximum_batch_size, provider.max_batch_size) or not shape.isolated_batch_items:
        return result(ReplanSignal.NO_FIT, estimate, (), "batch limit or item isolation contract failed")
    if shape.precision not in envelope.allowed_precisions or shape.precision not in provider.supported_precisions:
        return result(ReplanSignal.REQUIRE_REPLAN, estimate, (), "provider and feasible envelope have no common precision")
    needs_precision_evidence = shape.precision is not Precision.FP32
    if needs_precision_evidence:
        if precision_compatibility is None:
            return result(ReplanSignal.QUALITY_AUTH_REQUIRED, estimate, (), "precision compatibility is unknown for the exact operation/context")
        if type(precision_compatibility) is not PrecisionCompatibility or precision_compatibility.target_precision is not shape.precision or precision_compatibility.operation_ref != shape.operation_ref or precision_compatibility.context_ref != shape.context_ref:
            return result(ReplanSignal.QUALITY_AUTH_REQUIRED, estimate, (), "precision compatibility does not bind the exact operation/context/target")
        if precision_compatibility.authority_ref.split(":", 1)[0] == "M09":
            return result(ReplanSignal.QUALITY_AUTH_REQUIRED, estimate, (), "M09 cannot author precision quality equivalence")
        if precision_compatibility.classification is PrecisionCompatibilityClass.UNSUPPORTED:
            return result(ReplanSignal.REQUIRE_REPLAN, estimate, (), "precision is unsupported for this operation/context")
        if precision_compatibility.classification is PrecisionCompatibilityClass.QUALITY_SENSITIVE and quality is None:
            return result(ReplanSignal.QUALITY_AUTH_REQUIRED, estimate, (), "quality-sensitive precision has no owning quality constraint")
    if quality is not None:
        if type(quality) is not QualityConstraintRef or quality.operation_ref != shape.operation_ref or quality.context_ref != shape.context_ref:
            return result(ReplanSignal.QUALITY_AUTH_REQUIRED, estimate, (), "quality constraint does not bind the exact operation and context")
        precision_crosses_minimum = _PRECISION_RANK[shape.precision] < _PRECISION_RANK[quality.minimum_precision]
        quality_sensitive = needs_precision_evidence and precision_compatibility is not None and precision_compatibility.classification is PrecisionCompatibilityClass.QUALITY_SENSITIVE
        if precision_crosses_minimum or quality_sensitive:
            if not quality.allow_degradation or quality.consent_ref is None or quality.authorized_shape_digest != digest or quality.consent_expires_at_ms is None or now_ms > quality.consent_expires_at_ms:
                return result(ReplanSignal.QUALITY_AUTH_REQUIRED, estimate, (), "quality degradation consent is absent, stale or outside exact shape scope")
    elif needs_precision_evidence and precision_compatibility is not None and precision_compatibility.classification is PrecisionCompatibilityClass.QUALITY_SENSITIVE:
        return result(ReplanSignal.QUALITY_AUTH_REQUIRED, estimate, (), "quality-sensitive precision has no owning quality constraint")
    safe_allocatable_bytes = min(envelope.max_allocatable_bytes, available_bytes)
    if estimate > safe_allocatable_bytes:
        return result(ReplanSignal.REQUIRE_OFFLOAD, estimate, (), "shape exceeds current known allocatable capacity after protected headroom")
    negotiation = ProviderCapabilityAdapter(provider).negotiate(shape)
    if negotiation is None:
        return result(ReplanSignal.REQUIRE_REPLAN, estimate, (), "provider cannot represent the exact declared shape contracts")
    if not negotiation.exact:
        return result(ReplanSignal.REQUIRE_REPLAN, estimate, negotiation.payload, "provider quantization requires an explicit new canonical shape request")
    return result(ReplanSignal.FIT, estimate, negotiation.payload, "finite current-resource and authority constraints satisfied", quality.consent_ref if quality and needs_precision_evidence else None)


def evaluate_shape_set(
    candidates: BoundedShapeSet,
    envelope: ShapeEnvelope,
    provider: ProviderCapabilities,
    *,
    quality: QualityConstraintRef | None,
    current_epoch: int,
    expected_epoch: int,
    current_snapshot: ResourceSnapshot,
    current_resource_epoch: int,
    now_ms: int,
    precision_compatibilities: tuple[PrecisionCompatibility | None, ...] | None = None,
    limits: M09Limits = DEFAULT_LIMITS,
) -> ShapeSetEvaluation:
    if type(candidates) is not BoundedShapeSet:
        raise ValueError("shape search requires an exact finite candidate set")
    steps = min(len(candidates.shapes), limits.max_search_steps)
    compatibilities = precision_compatibilities or tuple(None for _ in candidates.shapes)
    if len(compatibilities) != len(candidates.shapes):
        raise ValueError("each finite shape candidate requires a corresponding precision compatibility slot")
    evaluated = tuple(
        evaluate_shape(
            shape, envelope, provider, quality=quality,
            current_epoch=current_epoch, expected_epoch=expected_epoch,
            current_snapshot=current_snapshot, current_resource_epoch=current_resource_epoch,
            now_ms=now_ms, precision_compatibility=compatibilities[index],
        )
        for index, shape in enumerate(candidates.shapes[:steps])
    )
    return ShapeSetEvaluation(
        tuple(content_digest(item) for item in candidates.shapes[:steps]),
        evaluated, steps, steps < len(candidates.shapes),
    )
