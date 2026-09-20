from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Sequence

from .contracts import DEFECT_CLASS_FIELDS, FidelityContract, PromotionRule, QualityClass
from .debt import QualityDebtPolicy
from .dimensions import DEFAULT_DIMENSION_REGISTRY, DimensionRegistry
from .errors import (
    EvaluationInputError,
    RegistrationError,
    SchemaValidationError,
    UntrustedExtensionError,
)
from .evidence import require_relative_locator
from .versions import (
    SCHEMA_VERSION,
    ComponentVersion,
    require_identifier,
    require_text,
    require_unique,
)
from .zones import SemanticZone

__all__ = [
    "TrustTier",
    "ExtensionMetadata",
    "EvaluatorDescriptor",
    "EvaluatorRegistry",
    "EvaluatorAuthority",
    "DomainProfile",
    "DomainProfileRegistry",
]

MAX_REGISTRATIONS = 512
MAX_METADATA_KEYS = 16
ALLOWED_METADATA_KEYS: frozenset[str] = frozenset(
    {"purpose", "source", "license", "qualification", "limitations"}
)
ALLOWED_METADATA_VALUE_CHARACTERS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:;/_-()"
)


class TrustTier(Enum):
    """How much authority a registered component carries, independent of its score."""

    CORE = "CORE"
    QUALIFIED = "QUALIFIED"
    EXPERIMENTAL = "EXPERIMENTAL"

    @classmethod
    def parse(cls, value: Any) -> TrustTier:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise SchemaValidationError(
                f"trust_tier must be one of {sorted(item.value for item in cls)}"
            )
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise SchemaValidationError(
                f"trust_tier must be one of {sorted(item.value for item in cls)}"
            ) from error


@dataclass(frozen=True)
class ExtensionMetadata:
    """Closed, bounded key set. Anything richer is refused rather than interpreted."""

    entries: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.entries, Mapping):
            raise UntrustedExtensionError("extension metadata must be a mapping")
        if len(self.entries) > MAX_METADATA_KEYS:
            raise UntrustedExtensionError(
                f"extension metadata accepts at most {MAX_METADATA_KEYS} keys"
            )
        normalized: dict[str, str] = {}
        for key, value in self.entries.items():
            if not isinstance(key, str) or key.strip().lower() not in ALLOWED_METADATA_KEYS:
                raise UntrustedExtensionError(
                    f"extension metadata key {key!r} is not in the allowlist {sorted(ALLOWED_METADATA_KEYS)}"
                )
            name = key.strip().lower()
            if not isinstance(value, str):
                raise UntrustedExtensionError(f"extension metadata {name!r} must be a string")
            text = value.strip()
            if not text:
                raise UntrustedExtensionError(f"extension metadata {name!r} must not be empty")
            if len(text) > 256:
                raise UntrustedExtensionError(f"extension metadata {name!r} exceeds 256 characters")
            if any(character not in ALLOWED_METADATA_VALUE_CHARACTERS for character in text):
                raise UntrustedExtensionError(
                    f"extension metadata {name!r} contains characters outside the admitted alphabet"
                )
            if name == "source":
                try:
                    normalized[name] = require_relative_locator(
                        text, "extension metadata source"
                    )
                except SchemaValidationError as error:
                    raise UntrustedExtensionError(str(error)) from error
            else:
                normalized[name] = text
        object.__setattr__(self, "entries", normalized)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.entries.get(key.strip().lower(), default)

    def to_payload(self) -> dict[str, Any]:
        return {"entries": dict(sorted(self.entries.items()))}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ExtensionMetadata:
        if not isinstance(payload, Mapping):
            raise UntrustedExtensionError("ExtensionMetadata must be a mapping")
        expected = {"entries"}
        unexpected = set(payload) - expected
        if unexpected:
            raise UntrustedExtensionError(f"ExtensionMetadata has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise UntrustedExtensionError(f"ExtensionMetadata is missing keys: {sorted(missing)}")
        entries = payload["entries"]
        if not isinstance(entries, Mapping):
            raise UntrustedExtensionError("ExtensionMetadata entries must be a mapping")
        return cls(entries=dict(entries))


@dataclass(frozen=True)
class EvaluatorDescriptor:
    """Registration-time declaration of what a versioned evaluator claims to cover."""

    component: ComponentVersion
    dimension_ids: tuple[str, ...]
    deterministic: bool = False
    trust_tier: TrustTier = TrustTier.EXPERIMENTAL
    metadata: ExtensionMetadata = field(default_factory=ExtensionMetadata)
    dimension_registry: DimensionRegistry = DEFAULT_DIMENSION_REGISTRY

    def __post_init__(self) -> None:
        if not isinstance(self.component, ComponentVersion):
            raise SchemaValidationError("component must be a ComponentVersion")
        if not isinstance(self.dimension_registry, DimensionRegistry):
            raise SchemaValidationError("dimension_registry must be a DimensionRegistry")
        dimensions = require_unique(self.dimension_ids, "dimension_ids")
        if not dimensions:
            raise RegistrationError("an evaluator must declare at least one supported dimension")
        try:
            self.dimension_registry.require_admitted(dimensions, f"evaluator {self.component.reference}")
        except SchemaValidationError as error:
            raise RegistrationError(str(error)) from error
        object.__setattr__(self, "dimension_ids", dimensions)
        if not isinstance(self.deterministic, bool):
            raise SchemaValidationError("deterministic must be a bool")
        object.__setattr__(self, "trust_tier", TrustTier.parse(self.trust_tier))
        if not isinstance(self.metadata, ExtensionMetadata):
            raise UntrustedExtensionError("metadata must be ExtensionMetadata")

    @property
    def reference(self) -> str:
        return self.component.reference

    def supports(self, dimension_id: str) -> bool:
        return dimension_id in self.dimension_ids

    def to_payload(self) -> dict[str, Any]:
        return {
            "component": self.component.to_payload(),
            "dimension_ids": list(self.dimension_ids),
            "deterministic": self.deterministic,
            "trust_tier": self.trust_tier.value,
            "metadata": self.metadata.to_payload(),
            "dimension_registry": self.dimension_registry.to_payload(),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> EvaluatorDescriptor:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("EvaluatorDescriptor must be a mapping")
        expected = {
            "component",
            "dimension_ids",
            "deterministic",
            "trust_tier",
            "metadata",
            "dimension_registry",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"EvaluatorDescriptor has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"EvaluatorDescriptor is missing keys: {sorted(missing)}")
        dimension_ids = payload["dimension_ids"]
        if not isinstance(dimension_ids, list):
            raise SchemaValidationError("dimension_ids must be a list")
        return cls(
            component=ComponentVersion.from_payload(payload["component"]),
            dimension_ids=tuple(dimension_ids),
            deterministic=payload["deterministic"],
            trust_tier=TrustTier.parse(payload["trust_tier"]),
            metadata=ExtensionMetadata.from_payload(payload["metadata"]),
            dimension_registry=DimensionRegistry.from_payload(payload["dimension_registry"]),
        )


class EvaluatorRegistry:
    """Fail-closed catalogue of versioned evaluators; the kernel never guesses capability."""

    def __init__(self, descriptors: Iterable[EvaluatorDescriptor] = ()) -> None:
        self._by_reference: dict[str, EvaluatorDescriptor] = {}
        for descriptor in descriptors:
            self.register(descriptor)

    def register(self, descriptor: EvaluatorDescriptor) -> EvaluatorDescriptor:
        if not isinstance(descriptor, EvaluatorDescriptor):
            raise RegistrationError("only EvaluatorDescriptor instances can be registered")
        if len(self._by_reference) >= MAX_REGISTRATIONS:
            raise RegistrationError(f"registry is capped at {MAX_REGISTRATIONS} evaluators")
        existing = self._by_reference.get(descriptor.reference)
        if existing is not None:
            raise RegistrationError(
                f"evaluator reference {descriptor.reference} is already registered"
            )
        conflicting = sorted(
            reference
            for reference in self._by_reference
            if reference.split("@")[0] == descriptor.component.identifier
            and self._by_reference[reference].dimension_ids != descriptor.dimension_ids
        )
        if conflicting:
            raise RegistrationError(
                f"evaluator {descriptor.component.identifier} is registered under "
                f"{conflicting} with a different coverage declaration; versioned releases of the "
                "same evaluator must not silently change supported dimensions"
            )
        self._by_reference[descriptor.reference] = descriptor
        return descriptor

    def registered_references(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_reference))

    def descriptor(self, component: ComponentVersion) -> EvaluatorDescriptor:
        if not isinstance(component, ComponentVersion):
            raise RegistrationError("component must be a ComponentVersion")
        try:
            return self._by_reference[component.reference]
        except KeyError as error:
            raise RegistrationError(
                f"evaluator {component.reference} is not registered"
            ) from error

    def versions_of(self, identifier: str) -> tuple[str, ...]:
        name = require_identifier(identifier, "identifier")
        return tuple(
            sorted(
                reference.split("@", 1)[1]
                for reference in self._by_reference
                if reference.split("@", 1)[0] == name
            )
        )

    def covering(self, dimension_id: str) -> tuple[EvaluatorDescriptor, ...]:
        return tuple(
            self._by_reference[reference]
            for reference in sorted(self._by_reference)
            if self._by_reference[reference].supports(dimension_id)
        )

    def resolve(self, contract: FidelityContract) -> tuple[EvaluatorDescriptor, ...]:
        """Every declared evaluator must exist and the declared set must cover the contract."""

        if not isinstance(contract, FidelityContract):
            raise RegistrationError("contract must be a FidelityContract")
        if not contract.evaluator_set:
            raise RegistrationError(
                f"contract {contract.contract_id} declares no evaluator_set; capability cannot be inferred"
            )
        resolved: list[EvaluatorDescriptor] = []
        for component in contract.evaluator_set:
            resolved.append(self.descriptor(component))
        covered = {dimension for item in resolved for dimension in item.dimension_ids}
        missing = sorted(set(contract.dimension_ids) - covered)
        if missing:
            raise RegistrationError(
                f"contract {contract.contract_id} declares dimensions with no registered evaluator "
                f"in its evaluator_set: {missing}"
            )
        return tuple(resolved)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "evaluators": [
                self._by_reference[reference].to_payload()
                for reference in sorted(self._by_reference)
            ],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> EvaluatorRegistry:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("EvaluatorRegistry must be a mapping")
        expected = {"schema_version", "evaluators"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"EvaluatorRegistry has unknown keys: {sorted(unexpected)}")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise SchemaValidationError("unsupported registry schema_version")
        evaluators = payload["evaluators"]
        if not isinstance(evaluators, list):
            raise SchemaValidationError("evaluators must be a list")
        return cls(EvaluatorDescriptor.from_payload(item) for item in evaluators)


@dataclass(frozen=True)
class EvaluatorAuthority:
    """Bounded proof of which versioned evaluator may speak about which dimension.

    A promotion-capable authority always carries an :class:`EvaluatorRegistry` that has already
    been resolved against the whole declared panel: an authority over a registry that is missing
    a declared evaluator, or a version of one, cannot be constructed at all. So no public
    constructor is weaker than :meth:`resolved`, and an absent evaluator is never read as consent.
    The registry-less form is reachable only through :meth:`preflight`, checks declaration alone,
    and is refused by ``DecisionEngine``.
    """

    contract: FidelityContract
    registry: Optional[EvaluatorRegistry]

    def __post_init__(self) -> None:
        if not isinstance(self.contract, FidelityContract):
            raise RegistrationError("contract must be a FidelityContract")
        if self.registry is not None and not isinstance(self.registry, EvaluatorRegistry):
            raise RegistrationError("registry must be an EvaluatorRegistry or None")
        if self.registry is not None:
            # A non-null registry is only evidence of capability once it has been resolved:
            # without this the direct constructor would trust a panel that omits a declared
            # evaluator, and an evaluator that never speaks is invisible to authorize().
            self.registry.resolve(self.contract)

    @classmethod
    def preflight(cls, contract: FidelityContract) -> "EvaluatorAuthority":
        """Declaration-only authority for inspection before any panel is registered.

        It answers "which components does this contract admit?" and nothing else. It can never
        produce a promotable decision: missing registration is a fail-closed condition, not
        permission, so :class:`~iris_quality.decision.DecisionEngine` refuses it.
        """

        return cls(contract=contract, registry=None)

    @property
    def promotion_capable(self) -> bool:
        return self.registry is not None

    @classmethod
    def resolved(
        cls, contract: FidelityContract, registry: EvaluatorRegistry
    ) -> "EvaluatorAuthority":
        """Issue authority for a contract whose declared panel is registered and complete.

        The dataclass enforces the same resolution, so this is the semantic name for that
        guarantee rather than a second, stricter policy path.
        """

        return cls(contract=contract, registry=registry)

    def declared_references(self) -> tuple[str, ...]:
        return tuple(sorted({item.reference for item in self.contract.evaluator_set}))

    def authorize(
        self,
        component: ComponentVersion,
        dimension_ids: Sequence[str],
        role: str = "evaluator",
    ) -> Optional[EvaluatorDescriptor]:
        if not isinstance(component, ComponentVersion):
            raise EvaluationInputError(f"{role} must be a ComponentVersion")
        declared = {item.reference for item in self.contract.evaluator_set}
        if component.reference not in declared:
            raise EvaluationInputError(
                f"{role} {component.reference} is not declared by contract "
                f"{self.contract.contract_id}; its evaluator_set is {sorted(declared)} and the "
                "kernel does not infer capability from a result payload"
            )
        if self.registry is None:
            # Preflight inspection only: declaration is enforced, registration cannot be seen, and
            # no decision engine accepts this authority.
            return None
        try:
            descriptor = self.registry.descriptor(component)
        except RegistrationError as error:
            raise EvaluationInputError(
                f"{role} {component.reference} is declared by contract "
                f"{self.contract.contract_id} but not registered: {error}"
            ) from error
        outside = sorted(set(dimension_ids) - set(descriptor.dimension_ids))
        if outside:
            raise EvaluationInputError(
                f"{role} {component.reference} is registered for "
                f"{sorted(descriptor.dimension_ids)} but opined on dimensions outside its "
                f"declared coverage: {outside}"
            )
        return descriptor


@dataclass(frozen=True)
class DomainProfile:
    """A reusable, versioned statement of what a domain cares about."""

    profile_id: str
    version: str
    summary: str
    dimension_ids: tuple[str, ...]
    fatal_defect_classes: tuple[str, ...] = ()
    major_defect_classes: tuple[str, ...] = ()
    minor_defect_classes: tuple[str, ...] = ()
    observation_defect_classes: tuple[str, ...] = ()
    promotion_rules: tuple[PromotionRule, ...] = ()
    recommended_evaluators: tuple[ComponentVersion, ...] = ()
    human_review_dimension_ids: tuple[str, ...] = ()
    dimension_registry: DimensionRegistry = DEFAULT_DIMENSION_REGISTRY

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "version", require_text(self.version, "version", maximum=64))
        object.__setattr__(self, "summary", require_text(self.summary, "summary", maximum=512))
        if not isinstance(self.dimension_registry, DimensionRegistry):
            raise RegistrationError("dimension_registry must be a DimensionRegistry")
        dimensions = require_unique(self.dimension_ids, "dimension_ids")
        if not dimensions:
            raise RegistrationError("a domain profile must declare at least one dimension")
        try:
            self.dimension_registry.require_admitted(
                dimensions, f"profile {self.profile_id}"
            )
        except SchemaValidationError as error:
            raise RegistrationError(
                f"{error}; extend the Fidelity Vector through the contract dimension registry, "
                "never by inventing an id at evaluation time"
            ) from error
        object.__setattr__(self, "dimension_ids", dimensions)
        for name, _ in DEFECT_CLASS_FIELDS:
            object.__setattr__(self, name, require_unique(getattr(self, name), name))
        seen: dict[str, str] = {}
        for name, severity in DEFECT_CLASS_FIELDS:
            overlap = sorted(set(seen) & set(getattr(self, name)))
            if overlap:
                raise RegistrationError(
                    f"profile {self.profile_id} declares defect classes at exactly one severity: "
                    f"{overlap}"
                )
            seen.update({item: severity for item in getattr(self, name)})
        rules = tuple(self.promotion_rules)
        for rule in rules:
            if not isinstance(rule, PromotionRule):
                raise RegistrationError("promotion_rules entries must be PromotionRule")
            stray = sorted(set(rule.required_dimension_ids) - set(dimensions))
            if stray:
                raise RegistrationError(
                    f"profile {self.profile_id} rule {rule.target_class.value} requires dimensions "
                    f"the profile does not declare: {stray}"
                )
        targets = [rule.target_class for rule in rules]
        if len(targets) != len(set(targets)):
            raise RegistrationError("profile promotion rules must name each target once")
        ranks = [target.ladder_rank for target in targets]
        if ranks != sorted(ranks):
            raise RegistrationError("profile promotion rules must ascend the quality ladder")
        object.__setattr__(self, "promotion_rules", rules)
        evaluators = tuple(self.recommended_evaluators)
        for evaluator in evaluators:
            if not isinstance(evaluator, ComponentVersion):
                raise RegistrationError("recommended_evaluators entries must be ComponentVersion")
        identifiers = [item.identifier for item in evaluators]
        if len(identifiers) != len(set(identifiers)):
            raise RegistrationError("recommended_evaluator identifiers must be unique")
        object.__setattr__(self, "recommended_evaluators", evaluators)
        review = require_unique(self.human_review_dimension_ids, "human_review_dimension_ids")
        stray = sorted(set(review) - set(dimensions))
        if stray:
            raise RegistrationError(
                f"profile {self.profile_id} requests human review for undeclared dimensions: {stray}"
            )
        object.__setattr__(self, "human_review_dimension_ids", review)

    @property
    def reference(self) -> str:
        return f"{self.profile_id}@{self.version}"

    def instantiate(
        self,
        *,
        contract_id: str,
        intent: str,
        output_class: QualityClass,
        target_platform: str = "unspecified",
        camera_profile: str = "unspecified",
        delivery_profile: str = "unspecified",
        reference_ids: Sequence[str] = (),
        zones: Sequence[SemanticZone] = (),
        debt_policy: Optional[QualityDebtPolicy] = None,
        max_judge_disagreement: float = 0.35,
    ) -> FidelityContract:
        """Build a contract from the profile without adding capabilities the profile lacks."""

        return FidelityContract(
            contract_id=contract_id,
            intent=intent,
            output_class=output_class,
            dimension_ids=self.dimension_ids,
            reference_ids=tuple(reference_ids),
            fatal_defect_classes=self.fatal_defect_classes,
            major_defect_classes=self.major_defect_classes,
            minor_defect_classes=self.minor_defect_classes,
            observation_defect_classes=self.observation_defect_classes,
            evaluator_set=self.recommended_evaluators,
            target_platform=target_platform,
            camera_profile=camera_profile,
            delivery_profile=delivery_profile,
            zones=tuple(zones),
            promotion_rules=self.promotion_rules,
            human_review_dimension_ids=self.human_review_dimension_ids,
            dimension_registry=self.dimension_registry,
            debt_policy=debt_policy if debt_policy is not None else QualityDebtPolicy(),
            max_judge_disagreement=max_judge_disagreement,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "summary": self.summary,
            "dimension_ids": list(self.dimension_ids),
            "fatal_defect_classes": list(self.fatal_defect_classes),
            "major_defect_classes": list(self.major_defect_classes),
            "minor_defect_classes": list(self.minor_defect_classes),
            "observation_defect_classes": list(self.observation_defect_classes),
            "promotion_rules": [rule.to_payload() for rule in self.promotion_rules],
            "recommended_evaluators": [item.to_payload() for item in self.recommended_evaluators],
            "human_review_dimension_ids": list(self.human_review_dimension_ids),
            "dimension_registry": self.dimension_registry.to_payload(),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> DomainProfile:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("DomainProfile must be a mapping")
        expected = {
            "profile_id",
            "version",
            "summary",
            "dimension_ids",
            "fatal_defect_classes",
            "major_defect_classes",
            "minor_defect_classes",
            "observation_defect_classes",
            "promotion_rules",
            "recommended_evaluators",
            "human_review_dimension_ids",
            "dimension_registry",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"DomainProfile has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"DomainProfile is missing keys: {sorted(missing)}")
        lists = {
            key: payload[key]
            for key in (
                "dimension_ids",
                "fatal_defect_classes",
                "major_defect_classes",
                "minor_defect_classes",
                "observation_defect_classes",
                "promotion_rules",
                "recommended_evaluators",
                "human_review_dimension_ids",
            )
        }
        for key, value in lists.items():
            if not isinstance(value, list):
                raise SchemaValidationError(f"{key} must be a list")
        return cls(
            profile_id=payload["profile_id"],
            version=payload["version"],
            summary=payload["summary"],
            dimension_ids=tuple(lists["dimension_ids"]),
            fatal_defect_classes=tuple(lists["fatal_defect_classes"]),
            major_defect_classes=tuple(lists["major_defect_classes"]),
            minor_defect_classes=tuple(lists["minor_defect_classes"]),
            observation_defect_classes=tuple(lists["observation_defect_classes"]),
            promotion_rules=tuple(PromotionRule.from_payload(item) for item in lists["promotion_rules"]),
            recommended_evaluators=tuple(
                ComponentVersion.from_payload(item) for item in lists["recommended_evaluators"]
            ),
            human_review_dimension_ids=tuple(lists["human_review_dimension_ids"]),
            dimension_registry=DimensionRegistry.from_payload(payload["dimension_registry"]),
        )


class DomainProfileRegistry:
    """Versioned profile catalogue. One reference, one profile, no silent replacement."""

    def __init__(self, profiles: Iterable[DomainProfile] = ()) -> None:
        self._by_reference: dict[str, DomainProfile] = {}
        for profile in profiles:
            self.register(profile)

    def register(self, profile: DomainProfile) -> DomainProfile:
        if not isinstance(profile, DomainProfile):
            raise RegistrationError("only DomainProfile instances can be registered")
        if len(self._by_reference) >= MAX_REGISTRATIONS:
            raise RegistrationError(f"registry is capped at {MAX_REGISTRATIONS} profiles")
        reference = profile.reference
        if reference in self._by_reference:
            raise RegistrationError(f"domain profile {reference} is already registered")
        self._by_reference[reference] = profile
        return profile

    def registered_references(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_reference))

    def get(self, profile_id: str, version: Optional[str] = None) -> DomainProfile:
        identifier = require_identifier(profile_id, "profile_id")
        if version is None:
            matches = [
                profile
                for reference, profile in self._by_reference.items()
                if reference.split("@", 1)[0] == identifier
            ]
            if not matches:
                raise RegistrationError(f"domain profile {identifier} is not registered")
            if len(matches) > 1:
                raise RegistrationError(
                    f"domain profile {identifier} has {len(matches)} registered versions; "
                    "select one explicitly"
                )
            return matches[0]
        try:
            return self._by_reference[f"{identifier}@{require_text(version, 'version', maximum=64)}"]
        except KeyError as error:
            raise RegistrationError(f"domain profile {identifier}@{version} is not registered") from error

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "profiles": [
                self._by_reference[reference].to_payload()
                for reference in sorted(self._by_reference)
            ],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> DomainProfileRegistry:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("DomainProfileRegistry must be a mapping")
        expected = {"schema_version", "profiles"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"DomainProfileRegistry has unknown keys: {sorted(unexpected)}")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise SchemaValidationError("unsupported registry schema_version")
        profiles = payload["profiles"]
        if not isinstance(profiles, list):
            raise SchemaValidationError("profiles must be a list")
        return cls(DomainProfile.from_payload(item) for item in profiles)
