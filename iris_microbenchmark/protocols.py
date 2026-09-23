"""Immutable benchmark protocols, metric semantics, and fail-closed admission."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M08Record, content_digest, require_sequence
from .enums import (
    Aggregation, AuthorizationState, AutomationKind, BenchmarkClass, Directionality,
    Domain, PrivacyClass, QuantityKind, TimingSource,
)
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkAuthorityError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError, MicrobenchmarkValidationError
from .limits import DEFAULT_LIMITS, M08Limits
from .provenance import EvidencePurposeDescriptor, ExternalContextReference, M07ProvenanceBinding
from .versions import require_digest, require_identifier, require_nonnegative_int, require_version

__all__ = [
    "SafetyBudget", "MetricSemantics", "BenchmarkAuthorizationReceipt", "SecurityAuthorizationReference",
    "AutomationOriginDescriptor", "ProtocolDescriptor", "ProtocolAdmission", "admit_protocol", "validate_first_run_batch",
]


@dataclass(frozen=True)
class SafetyBudget(M08Record):
    max_wall_ms: int
    max_warmup_ms: int
    max_iterations: int
    max_host_allocation_bytes: int
    max_device_allocation_bytes: int
    max_output_bytes: int
    max_concurrency: int
    max_retries: int
    cooldown_ms: int
    first_run: bool

    def validate_against(self, limits: M08Limits = DEFAULT_LIMITS) -> None:
        values = {
            "max_protocol_duration_ms": self.max_wall_ms,
            "max_warmup_ms": self.max_warmup_ms,
            "max_iterations": self.max_iterations,
            "max_host_allocation_bytes": self.max_host_allocation_bytes,
            "max_device_allocation_bytes": self.max_device_allocation_bytes,
            "max_output_bytes": self.max_output_bytes,
            "max_concurrency": self.max_concurrency,
            "max_retries": self.max_retries,
            "max_cooldown_ms": self.cooldown_ms,
        }
        for name, value in values.items():
            limits.require(name, value)
        if self.max_wall_ms < 1 or self.max_iterations < 1:
            raise MicrobenchmarkValidationError("active benchmark duration and iteration bounds must be positive")
        if self.max_concurrency < 1 or self.max_warmup_ms > self.max_wall_ms:
            raise MicrobenchmarkValidationError("benchmark concurrency must be positive and warmup must fit inside its wall-clock budget")
        if type(self.first_run) is not bool:
            raise MicrobenchmarkValidationError("first_run must be bool")
        if self.first_run:
            limits.require("max_first_run_protocol_ms", self.max_wall_ms)

    def __post_init__(self) -> None:
        self.validate_against()


@dataclass(frozen=True)
class MetricSemantics(M08Record):
    metric_id: str
    version: str
    quantity_kind: QuantityKind
    unit: str
    directionality: Directionality
    aggregation: Aggregation
    warmup_policy: str
    minimum_samples: int
    timing_source: TimingSource
    uncertainty_required: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "metric_id", require_identifier(self.metric_id, "metric_id"))
        object.__setattr__(self, "version", require_version(self.version))
        for field, enum_type in (("quantity_kind", QuantityKind), ("directionality", Directionality), ("aggregation", Aggregation), ("timing_source", TimingSource)):
            if not isinstance(getattr(self, field), enum_type):
                raise MicrobenchmarkValidationError(f"{field} must be {enum_type.__name__}")
        object.__setattr__(self, "unit", require_identifier(self.unit, "unit"))
        object.__setattr__(self, "warmup_policy", require_identifier(self.warmup_policy, "warmup_policy"))
        minimum = require_nonnegative_int(self.minimum_samples, "minimum_samples")
        if minimum < 1 or minimum > DEFAULT_LIMITS.max_samples_per_result:
            raise MicrobenchmarkLimitError("minimum_samples must fit the admitted sample ceiling")
        object.__setattr__(self, "minimum_samples", minimum)
        if type(self.uncertainty_required) is not bool:
            raise MicrobenchmarkValidationError("uncertainty_required must be bool")


@dataclass(frozen=True)
class BenchmarkAuthorizationReceipt(M08Record):
    receipt_id: str
    policy_ref: str
    protocol_id: str
    protocol_version: str
    protocol_digest: str
    subject_id: str
    runtime_id: str
    binding_digest: str
    issued_at_ms: int
    expires_at_ms: int
    state: AuthorizationState
    purpose_id: str

    def __post_init__(self) -> None:
        for field in ("receipt_id", "policy_ref", "protocol_id", "subject_id", "runtime_id", "purpose_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "protocol_version", require_version(self.protocol_version, "protocol_version"))
        object.__setattr__(self, "protocol_digest", require_digest(self.protocol_digest, "protocol_digest"))
        object.__setattr__(self, "binding_digest", _digest(self.binding_digest))
        object.__setattr__(self, "issued_at_ms", require_nonnegative_int(self.issued_at_ms, "issued_at_ms"))
        object.__setattr__(self, "expires_at_ms", require_nonnegative_int(self.expires_at_ms, "expires_at_ms"))
        if self.expires_at_ms <= self.issued_at_ms:
            raise MicrobenchmarkValidationError("authorization expiry must follow issuance")
        if not isinstance(self.state, AuthorizationState):
            raise MicrobenchmarkValidationError("state must be AuthorizationState")


def _digest(value: str) -> str:
    return require_digest(value, "binding_digest")


@dataclass(frozen=True)
class SecurityAuthorizationReference(M08Record):
    authorization_id: str
    policy_ref: str
    protocol_id: str
    protocol_version: str
    binding_digest: str
    purpose_id: str
    subject_id: str
    runtime_id: str
    state: AuthorizationState
    expires_at_ms: int

    def __post_init__(self) -> None:
        for field in ("authorization_id", "policy_ref", "protocol_id", "purpose_id", "subject_id", "runtime_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "protocol_version", require_version(self.protocol_version, "protocol_version"))
        object.__setattr__(self, "binding_digest", require_digest(self.binding_digest, "binding_digest"))
        if not isinstance(self.state, AuthorizationState):
            raise MicrobenchmarkValidationError("state must be AuthorizationState")
        object.__setattr__(self, "expires_at_ms", require_nonnegative_int(self.expires_at_ms, "expires_at_ms"))


@dataclass(frozen=True)
class AutomationOriginDescriptor(M08Record):
    origin_id: str
    actor_ref: str
    kind: AutomationKind
    requested_at_ms: int
    request_ref: str

    def __post_init__(self) -> None:
        for field in ("origin_id", "actor_ref", "request_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.kind, AutomationKind):
            raise MicrobenchmarkValidationError("kind must be AutomationKind")
        object.__setattr__(self, "requested_at_ms", require_nonnegative_int(self.requested_at_ms, "requested_at_ms"))


@dataclass(frozen=True)
class ProtocolDescriptor(M08Record):
    protocol_id: str
    version: str
    domain: Domain
    operation_family: str
    safety_class: BenchmarkClass
    binding: M07ProvenanceBinding
    metrics: tuple[MetricSemantics, ...]
    budget: SafetyBudget
    thermal_abort_condition: str | None
    cancellation_path: str
    cooldown_policy: str
    interference_policy: str
    privacy_class: PrivacyClass
    result_schema_id: str
    invalidation_refs: tuple[ExternalContextReference, ...]
    evidence_purpose: EvidencePurposeDescriptor
    authorization_id: str
    security_authorization_required: bool
    security_authorization_ref: SecurityAuthorizationReference | None
    automation_origin: AutomationOriginDescriptor | None
    authority_namespace: str = "hardware-capability"

    def __post_init__(self) -> None:
        for field in ("protocol_id", "operation_family", "cancellation_path", "cooldown_policy", "interference_policy", "result_schema_id", "authorization_id", "authority_namespace"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        if not isinstance(self.domain, Domain) or not isinstance(self.safety_class, BenchmarkClass):
            raise MicrobenchmarkValidationError("protocol domain and safety class must use closed M08 vocabularies")
        object.__setattr__(self, "binding", M07ProvenanceBinding.coerce(self.binding, "binding"))
        metrics = tuple(sorted((MetricSemantics.coerce(item, "metrics[]") for item in self.metrics), key=lambda item: item.metric_id))
        DEFAULT_LIMITS.require("max_metrics_per_protocol", len(metrics))
        if not metrics or len({item.metric_id for item in metrics}) != len(metrics):
            raise MicrobenchmarkIntegrityError("a protocol needs unique metric semantics")
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "budget", SafetyBudget.coerce(self.budget, "budget"))
        self.budget.validate_against()
        if self.budget.first_run and self.safety_class in {BenchmarkClass.SUSTAINED, BenchmarkClass.DESTRUCTIVE_OR_STRESS}:
            raise MicrobenchmarkAdmissionError("first-run protocols cannot be sustained or stress-class")
        if self.safety_class is BenchmarkClass.DESTRUCTIVE_OR_STRESS:
            raise MicrobenchmarkAdmissionError("destructive or stress protocols are prohibited by the M08 core")
        if self.safety_class is BenchmarkClass.SUSTAINED and not self.budget.cooldown_ms:
            raise MicrobenchmarkAdmissionError("sustained protocols require explicit cooldown")
        if self.thermal_abort_condition is not None:
            object.__setattr__(self, "thermal_abort_condition", require_identifier(self.thermal_abort_condition, "thermal_abort_condition"))
        if not isinstance(self.privacy_class, PrivacyClass):
            raise MicrobenchmarkValidationError("privacy_class must be PrivacyClass")
        object.__setattr__(self, "invalidation_refs", tuple(sorted((ExternalContextReference.coerce(item, "invalidation_refs[]") for item in self.invalidation_refs), key=lambda item: (item.namespace, item.reference_id, item.version))))
        if len(self.invalidation_refs) > DEFAULT_LIMITS.max_external_refs:
            raise MicrobenchmarkLimitError("protocol invalidation references exceed the hard ceiling")
        object.__setattr__(self, "evidence_purpose", EvidencePurposeDescriptor.coerce(self.evidence_purpose, "evidence_purpose"))
        if type(self.security_authorization_required) is not bool:
            raise MicrobenchmarkValidationError("security_authorization_required must be bool")
        if self.security_authorization_ref is not None:
            object.__setattr__(self, "security_authorization_ref", SecurityAuthorizationReference.coerce(self.security_authorization_ref, "security_authorization_ref"))
        if self.automation_origin is not None:
            object.__setattr__(self, "automation_origin", AutomationOriginDescriptor.coerce(self.automation_origin, "automation_origin"))
        if self.authority_namespace != "hardware-capability":
            raise MicrobenchmarkAuthorityError("M08 protocols require the hardware-capability authority namespace")
        if self.security_authorization_required and self.security_authorization_ref is None:
            raise MicrobenchmarkAdmissionError("required security authorization reference is absent")
        if self.security_authorization_ref is not None:
            security = self.security_authorization_ref
            if (
                security.protocol_id != self.protocol_id
                or security.protocol_version != self.version
                or security.binding_digest != content_digest(self.binding)
                or security.purpose_id != self.evidence_purpose.purpose_id
                or security.subject_id != self.binding.subject_id
                or security.runtime_id != self.binding.runtime_id
            ):
                raise MicrobenchmarkAdmissionError("security authorization must bind the exact protocol version, M07 context and purpose")


@dataclass(frozen=True)
class ProtocolAdmission(M08Record):
    protocol_id: str
    protocol_version: str
    binding_digest: str
    authorization_receipt_id: str
    authorization_receipt: BenchmarkAuthorizationReceipt
    security_authorization_id: str | None
    admitted_at_ms: int
    authority_namespace: str = "hardware-capability"

    def __post_init__(self) -> None:
        for field in ("protocol_id", "authorization_receipt_id", "authority_namespace"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if self.security_authorization_id is not None:
            object.__setattr__(self, "security_authorization_id", require_identifier(self.security_authorization_id, "security_authorization_id"))
        object.__setattr__(self, "authorization_receipt", BenchmarkAuthorizationReceipt.coerce(self.authorization_receipt, "authorization_receipt"))
        object.__setattr__(self, "protocol_version", require_version(self.protocol_version))
        object.__setattr__(self, "binding_digest", _digest(self.binding_digest))
        object.__setattr__(self, "admitted_at_ms", require_nonnegative_int(self.admitted_at_ms, "admitted_at_ms"))
        if self.authority_namespace != "hardware-capability":
            raise MicrobenchmarkAuthorityError("protocol admission cannot change M08 authority namespace")
        receipt = self.authorization_receipt
        if (
            (receipt.protocol_id, receipt.protocol_version, receipt.receipt_id, receipt.binding_digest)
            != (self.protocol_id, self.protocol_version, self.authorization_receipt_id, self.binding_digest)
            or receipt.state is not AuthorizationState.GRANTED
            or not receipt.issued_at_ms <= self.admitted_at_ms < receipt.expires_at_ms
        ):
            raise MicrobenchmarkIntegrityError("protocol admission must retain the exact active authorization receipt")


def admit_protocol(
    protocol: ProtocolDescriptor,
    receipt: BenchmarkAuthorizationReceipt,
    *,
    at_ms: int,
    limits: M08Limits = DEFAULT_LIMITS,
) -> ProtocolAdmission:
    protocol = ProtocolDescriptor.coerce(protocol, "protocol")
    receipt = BenchmarkAuthorizationReceipt.coerce(receipt, "receipt")
    at_ms = require_nonnegative_int(at_ms, "at_ms")
    protocol.budget.validate_against(limits)
    binding_digest = content_digest(protocol.binding)
    if (
        receipt.protocol_id != protocol.protocol_id
        or receipt.protocol_version != protocol.version
        or receipt.protocol_digest != content_digest(protocol)
        or receipt.subject_id != protocol.binding.subject_id
        or receipt.runtime_id != protocol.binding.runtime_id
        or receipt.binding_digest != binding_digest
        or receipt.purpose_id != protocol.evidence_purpose.purpose_id
        or protocol.authorization_id != receipt.receipt_id
    ):
        raise MicrobenchmarkAdmissionError("authorization receipt does not bind the exact protocol, provenance and evidence purpose")
    if receipt.state is not AuthorizationState.GRANTED or not receipt.issued_at_ms <= at_ms < receipt.expires_at_ms:
        raise MicrobenchmarkAdmissionError("authorization is absent, denied, expired or not yet active")
    security_id = None
    if protocol.security_authorization_required:
        security = protocol.security_authorization_ref
        if security is None or security.state is not AuthorizationState.GRANTED:
            raise MicrobenchmarkAdmissionError("security authorization is missing or denied")
        if (
            security.protocol_id, security.protocol_version, security.binding_digest,
            security.purpose_id, security.subject_id, security.runtime_id,
        ) != (
            protocol.protocol_id, protocol.version, binding_digest,
            protocol.evidence_purpose.purpose_id, protocol.binding.subject_id, protocol.binding.runtime_id,
        ):
            raise MicrobenchmarkAdmissionError("security authorization is bound to another protocol or subject")
        if at_ms >= security.expires_at_ms:
            raise MicrobenchmarkAdmissionError("security authorization has expired")
        security_id = security.authorization_id
    return ProtocolAdmission(protocol.protocol_id, protocol.version, binding_digest, receipt.receipt_id, receipt, security_id, at_ms)


def validate_first_run_batch(protocols: tuple[ProtocolDescriptor, ...], *, limits: M08Limits = DEFAULT_LIMITS) -> int:
    values = tuple(ProtocolDescriptor.coerce(item, "protocols[]") for item in require_sequence(protocols, "protocols", maximum=limits.max_protocols))
    if not values:
        raise MicrobenchmarkValidationError("first-run benchmark batch cannot be empty")
    if any(not item.budget.first_run for item in values):
        raise MicrobenchmarkAdmissionError("first-run budget validation accepts only explicitly marked first-run protocols")
    total = sum(item.budget.max_wall_ms for item in values)
    limits.require("max_first_run_total_ms", total)
    return total
