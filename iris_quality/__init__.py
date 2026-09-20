"""IRIS M01 Quality Kernel.

Domain-neutral, typed and deterministic quality reasoning. This package holds no
inference code and imports no asset, renderer or model-provider library: real
evaluators live in their destination modules and reach the kernel through the
ports in :mod:`iris_quality.judging`.
"""

from __future__ import annotations

from .contracts import FidelityContract, PromotionRule, QualityClass
from .debt import DebtRuling, QualityDebt, QualityDebtPolicy
from .decision import (
    Blocker,
    DecisionEngine,
    DecisionOutcome,
    DimensionOutcome,
    EffectiveFinding,
    QualityDecision,
    merge_assessments,
)
from .defects import Defect, DefectSeverity
from .dimensions import (
    CANONICAL_FIDELITY_VECTOR,
    DimensionAssessment,
    FidelityDimension,
    GateState,
    MeasurementRange,
    UncertaintyState,
    canonical_dimension,
)
from .errors import (
    ContractValidationError,
    EvaluationInputError,
    PromotionBlockedError,
    QualityKernelError,
    RegistrationError,
    SchemaValidationError,
    UntrustedExtensionError,
    UnsupportedVersionError,
)
from .evidence import EVIDENCE_KINDS, EvidenceRef
from .judging import (
    Abstention,
    AssetValidator,
    JudgeRequest,
    JudgeResult,
    QualityJudge,
    SubjectRef,
    ValidationCheck,
    ValidatorOutcome,
    attach_contract_checks,
    numeric_spread,
)
from .registry import (
    DomainProfile,
    DomainProfileRegistry,
    EvaluatorDescriptor,
    EvaluatorRegistry,
    ExtensionMetadata,
    TrustTier,
)
from .serialization import dumps, envelope, from_envelope, loads, validate_payload
from .versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    ComponentVersion,
    canonical_json,
    content_digest,
)
from .zones import SemanticZone

__version__ = "0.1.0"

__all__ = [
    "Abstention",
    "AssetValidator",
    "Blocker",
    "CANONICAL_FIDELITY_VECTOR",
    "CONTRACT_VERSION",
    "ComponentVersion",
    "ContractValidationError",
    "DebtRuling",
    "DecisionEngine",
    "DecisionOutcome",
    "Defect",
    "DefectSeverity",
    "DimensionAssessment",
    "DimensionOutcome",
    "DomainProfile",
    "DomainProfileRegistry",
    "EVIDENCE_KINDS",
    "EffectiveFinding",
    "EvaluationInputError",
    "EvidenceRef",
    "EvaluatorDescriptor",
    "EvaluatorRegistry",
    "ExtensionMetadata",
    "FidelityContract",
    "FidelityDimension",
    "GateState",
    "JudgeRequest",
    "JudgeResult",
    "MeasurementRange",
    "PromotionBlockedError",
    "PromotionRule",
    "QualityClass",
    "QualityDecision",
    "QualityDebt",
    "QualityDebtPolicy",
    "QualityJudge",
    "QualityKernelError",
    "RegistrationError",
    "SCHEMA_VERSION",
    "SchemaValidationError",
    "SemanticZone",
    "SubjectRef",
    "TrustTier",
    "UncertaintyState",
    "UntrustedExtensionError",
    "UnsupportedVersionError",
    "ValidationCheck",
    "ValidatorOutcome",
    "__version__",
    "attach_contract_checks",
    "canonical_dimension",
    "canonical_json",
    "content_digest",
    "dumps",
    "envelope",
    "from_envelope",
    "loads",
    "merge_assessments",
    "numeric_spread",
    "validate_payload",
]
