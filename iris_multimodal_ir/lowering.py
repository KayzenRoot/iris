"""Provider-neutral capability analysis and auditable M03-to-M04 lowering ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Mapping

from iris_intent.execution import ExecutionIntentBundle
from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one, optional
from .common import require_enum
from .enums import RepresentationState, RequirementLevel, SemanticLossClass, SupportState
from .errors import IRAdmissionError, IRIntegrityError, IRSchemaError
from .graph import IRRevision
from .identity import IRNodeRef
from .provenance import Traceability
from .versions import LOWERING_VERSION, content_digest, require_digest, require_identifier, require_text, require_version

__all__ = [
    "CapabilityDeclaration", "CapabilitySupport", "RepresentationCapabilityManifest", "TargetRepresentationProfile",
    "LegalityFinding", "SemanticLegalityReport", "SemanticLoweringRule", "SemanticLoweringReceipt",
    "SemanticLoweringPlan", "AdaptationProposal", "RepresentationGap", "IRTranslationReceipt",
    "SemanticCapabilityDebt", "LoweringBundlePlan", "M03ToM04Mapping", "lower_m03_bundle", "analyze_legality",
    "plan_semantic_lowering",
]


@dataclass(frozen=True)
class CapabilityDeclaration(IRRecord):
    capability_id: str
    version: str
    requirement: RequirementLevel
    semantic_refs: tuple[SemanticRef, ...]
    trace: Traceability

    NESTED: ClassVar = {"semantic_refs": many(SemanticRef), "trace": one(Traceability)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "capability_id", require_identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "requirement", require_enum(self.requirement, RequirementLevel, "requirement"))
        refs = tuple(SemanticRef.coerce(item, "semantic_refs[]") for item in self.semantic_refs)
        if self.requirement is RequirementLevel.REQUIRED and not refs:
            raise IRAdmissionError("required capability declaration needs M03 semantic refs")
        object.__setattr__(self, "semantic_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        object.__setattr__(self, "trace", Traceability.coerce(self.trace, "trace"))
        self.trace.require_admitted(f"capability {self.capability_id}")


@dataclass(frozen=True)
class CapabilitySupport(IRRecord):
    capability_id: str
    state: SupportState
    evidence_refs: tuple[SemanticRef, ...] = ()
    tolerance_ref: SemanticRef | None = None
    loss_rule_ref: SemanticRef | None = None

    NESTED: ClassVar = {"evidence_refs": many(SemanticRef), "tolerance_ref": optional(SemanticRef), "loss_rule_ref": optional(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "capability_id", require_identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "state", require_enum(self.state, SupportState, "state"))
        refs = tuple(SemanticRef.coerce(item, "evidence_refs[]") for item in self.evidence_refs)
        object.__setattr__(self, "evidence_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        for name in ("tolerance_ref", "loss_rule_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        if self.state is SupportState.BOUNDED and (self.tolerance_ref is None or self.loss_rule_ref is None):
            raise IRAdmissionError("bounded capability support requires upstream tolerance and loss-rule authorization")


@dataclass(frozen=True)
class RepresentationCapabilityManifest(IRRecord):
    manifest_id: str
    profile_id: str
    profile_version: str
    declarations: tuple[CapabilityDeclaration, ...]
    support: tuple[CapabilitySupport, ...] = ()
    provider_observation_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"declarations": many(CapabilityDeclaration), "support": many(CapabilitySupport), "provider_observation_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        for name in ("manifest_id", "profile_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        object.__setattr__(self, "profile_version", require_version(self.profile_version))
        declarations = tuple(CapabilityDeclaration.coerce(item, "declarations[]") for item in self.declarations)
        if len({item.capability_id for item in declarations}) != len(declarations):
            raise IRSchemaError("capability declarations must have unique ids")
        support = tuple(CapabilitySupport.coerce(item, "support[]") for item in self.support)
        if len({item.capability_id for item in support}) != len(support):
            raise IRSchemaError("capability support entries must have unique ids")
        known = {item.capability_id for item in declarations}
        if {item.capability_id for item in support} - known:
            raise IRIntegrityError("support record refers to undeclared capability")
        object.__setattr__(self, "declarations", tuple(sorted(declarations, key=lambda item: item.capability_id)))
        object.__setattr__(self, "support", tuple(sorted(support, key=lambda item: item.capability_id)))
        refs = tuple(SemanticRef.coerce(item, "provider_observation_refs[]") for item in self.provider_observation_refs)
        object.__setattr__(self, "provider_observation_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))

    def support_for(self, capability_id: str) -> CapabilitySupport:
        return next((item for item in self.support if item.capability_id == capability_id), CapabilitySupport(capability_id, SupportState.UNKNOWN))


@dataclass(frozen=True)
class TargetRepresentationProfile(IRRecord):
    profile_id: str
    version: str
    manifest: RepresentationCapabilityManifest
    schema_families: tuple[str, ...] = ()

    NESTED: ClassVar = {"manifest": one(RepresentationCapabilityManifest)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "manifest", RepresentationCapabilityManifest.coerce(self.manifest, "manifest"))
        if self.manifest.profile_id != self.profile_id or self.manifest.profile_version != self.version:
            raise IRIntegrityError("target profile and capability manifest identities differ")
        object.__setattr__(self, "schema_families", tuple(sorted(set(require_identifier(item, "schema_families[]") for item in self.schema_families))))


@dataclass(frozen=True, order=True)
class LegalityFinding(IRRecord):
    finding_id: str
    capability_id: str
    state: SupportState
    requirement: RequirementLevel
    reason: str
    blocks: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", require_identifier(self.finding_id, "finding_id"))
        object.__setattr__(self, "capability_id", require_identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "state", require_enum(self.state, SupportState, "state"))
        object.__setattr__(self, "requirement", require_enum(self.requirement, RequirementLevel, "requirement"))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=1024))
        if not isinstance(self.blocks, bool):
            raise IRSchemaError("blocks must be bool")


@dataclass(frozen=True)
class SemanticLegalityReport(IRRecord):
    report_id: str
    source_revision_digest: str
    profile: TargetRepresentationProfile
    findings: tuple[LegalityFinding, ...]
    report_digest: str | None = None

    NESTED: ClassVar = {"profile": one(TargetRepresentationProfile), "findings": many(LegalityFinding)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", require_identifier(self.report_id, "report_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "profile", TargetRepresentationProfile.coerce(self.profile, "profile"))
        findings = tuple(LegalityFinding.coerce(item, "findings[]") for item in self.findings)
        object.__setattr__(self, "findings", tuple(sorted(findings, key=lambda item: (item.capability_id, item.finding_id))))
        if self.report_digest is not None and self.report_digest != self.digest:
            raise IRIntegrityError("legality report digest does not match its canonical findings")

    @property
    def digest(self) -> str:
        return content_digest({"report_id": self.report_id, "source_revision_digest": self.source_revision_digest, "profile": self.profile, "findings": self.findings})

    @property
    def legal(self) -> bool:
        return not any(item.blocks for item in self.findings)


def analyze_legality(manifest: RepresentationCapabilityManifest, *, report_id: str, source_revision_digest: str) -> SemanticLegalityReport:
    """Read-only deterministic capability report; never changes source IR or M01 obligations."""
    manifest = RepresentationCapabilityManifest.coerce(manifest, "manifest")
    findings: list[LegalityFinding] = []
    for declaration in manifest.declarations:
        support = manifest.support_for(declaration.capability_id)
        blocks = declaration.requirement is RequirementLevel.REQUIRED and support.state in {SupportState.UNSUPPORTED, SupportState.UNKNOWN}
        if support.state is SupportState.BOUNDED and (support.tolerance_ref is None or support.loss_rule_ref is None):
            blocks = declaration.requirement is RequirementLevel.REQUIRED
        if support.state is SupportState.EXACT:
            reason = "declared exact semantic representation support"
        elif support.state is SupportState.BOUNDED:
            reason = "bounded support has explicit tolerance and upstream loss authorization"
        elif support.state is SupportState.UNSUPPORTED:
            reason = "target profile declares this representation unsupported"
        else:
            reason = "support is unknown; unknown required capability fails closed"
        findings.append(LegalityFinding(
            finding_id=f"legality.{declaration.capability_id}", capability_id=declaration.capability_id,
            state=support.state, requirement=declaration.requirement, reason=reason, blocks=blocks,
        ))
    return SemanticLegalityReport(report_id, source_revision_digest, TargetRepresentationProfile(manifest.profile_id, manifest.profile_version, manifest), tuple(findings))


@dataclass(frozen=True)
class SemanticLoweringRule(IRRecord):
    rule_id: str
    semantic_ref: SemanticRef
    state: RepresentationState
    loss_class: SemanticLossClass
    tolerance_ref: SemanticRef | None = None
    loss_rule_ref: SemanticRef | None = None
    policy_ref: SemanticRef | None = None
    explanation: str = ""

    NESTED: ClassVar = {"semantic_ref": one(SemanticRef), "tolerance_ref": optional(SemanticRef), "loss_rule_ref": optional(SemanticRef), "policy_ref": optional(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", require_identifier(self.rule_id, "rule_id"))
        object.__setattr__(self, "semantic_ref", SemanticRef.coerce(self.semantic_ref, "semantic_ref"))
        object.__setattr__(self, "state", require_enum(self.state, RepresentationState, "state"))
        object.__setattr__(self, "loss_class", require_enum(self.loss_class, SemanticLossClass, "loss_class"))
        for name in ("tolerance_ref", "loss_rule_ref", "policy_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        object.__setattr__(self, "explanation", require_text(self.explanation or "No semantic loss declared", "explanation", maximum=1024))
        if self.state is RepresentationState.BOUNDED:
            if self.loss_class is not SemanticLossClass.BOUNDED_APPROXIMATION or self.tolerance_ref is None or self.loss_rule_ref is None:
                raise IRAdmissionError("bounded lowering requires upstream BOUNDED_APPROXIMATION, tolerance, and loss-rule refs")
        if self.loss_class is SemanticLossClass.LOSSLESS_REQUIRED and self.state in {RepresentationState.BOUNDED, RepresentationState.DEFERRED, RepresentationState.EXTENSION_REQUIRED}:
            raise IRAdmissionError("LOSSLESS_REQUIRED semantics cannot be weakened or silently deferred")


@dataclass(frozen=True)
class SemanticLoweringReceipt(IRRecord):
    receipt_id: str
    m03_bundle_id: str
    source_revision_digest: str
    result_revision_digest: str
    rules: tuple[SemanticLoweringRule, ...]
    lowering_version: str = LOWERING_VERSION
    explanation_reachability_digest: str | None = None

    NESTED: ClassVar = {"rules": many(SemanticLoweringRule)}

    def __post_init__(self) -> None:
        for name in ("receipt_id", "m03_bundle_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        for name in ("source_revision_digest", "result_revision_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        rules = tuple(SemanticLoweringRule.coerce(item, "rules[]") for item in self.rules)
        if len({item.rule_id for item in rules}) != len(rules):
            raise IRSchemaError("lowering receipt rule ids must be unique")
        object.__setattr__(self, "rules", tuple(sorted(rules, key=lambda item: item.rule_id)))
        object.__setattr__(self, "lowering_version", require_version(self.lowering_version))
        if self.explanation_reachability_digest is not None:
            object.__setattr__(self, "explanation_reachability_digest", require_digest(self.explanation_reachability_digest, "explanation_reachability_digest"))


@dataclass(frozen=True)
class RepresentationGap(IRRecord):
    gap_id: str
    semantic_ref: SemanticRef
    state: RepresentationState
    required: bool
    reason: str
    remedy: str | None = None

    NESTED: ClassVar = {"semantic_ref": one(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_id", require_identifier(self.gap_id, "gap_id"))
        object.__setattr__(self, "semantic_ref", SemanticRef.coerce(self.semantic_ref, "semantic_ref"))
        object.__setattr__(self, "state", require_enum(self.state, RepresentationState, "state"))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=1024))
        if self.remedy is not None:
            object.__setattr__(self, "remedy", require_text(self.remedy, "remedy", maximum=1024))
        if not isinstance(self.required, bool):
            raise IRSchemaError("required must be bool")


@dataclass(frozen=True)
class AdaptationProposal(IRRecord):
    proposal_id: str
    semantic_ref: SemanticRef
    target_profile_id: str
    proposed_rule: SemanticLoweringRule
    requires_upstream_admission: bool = True

    NESTED: ClassVar = {"semantic_ref": one(SemanticRef), "proposed_rule": one(SemanticLoweringRule)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", require_identifier(self.proposal_id, "proposal_id"))
        object.__setattr__(self, "semantic_ref", SemanticRef.coerce(self.semantic_ref, "semantic_ref"))
        object.__setattr__(self, "target_profile_id", require_identifier(self.target_profile_id, "target_profile_id"))
        object.__setattr__(self, "proposed_rule", SemanticLoweringRule.coerce(self.proposed_rule, "proposed_rule"))
        if self.proposed_rule.semantic_ref != self.semantic_ref:
            raise IRIntegrityError("adaptation proposal must address its named semantic ref")
        if not isinstance(self.requires_upstream_admission, bool) or not self.requires_upstream_admission:
            raise IRAdmissionError("adaptation is a proposal and always requires upstream admission")


@dataclass(frozen=True)
class SemanticCapabilityDebt(IRRecord):
    debt_id: str
    target_profile_id: str
    semantic_refs: tuple[SemanticRef, ...]
    required: bool
    reason: str
    evidence_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"semantic_refs": many(SemanticRef), "evidence_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "debt_id", require_identifier(self.debt_id, "debt_id"))
        object.__setattr__(self, "target_profile_id", require_identifier(self.target_profile_id, "target_profile_id"))
        for name in ("semantic_refs", "evidence_refs"):
            refs = tuple(SemanticRef.coerce(item, f"{name}[]") for item in getattr(self, name))
            object.__setattr__(self, name, tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        if not self.semantic_refs:
            raise IRSchemaError("semantic capability debt must name at least one semantic ref")
        if not isinstance(self.required, bool):
            raise IRSchemaError("required must be bool")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=1024))


@dataclass(frozen=True)
class SemanticLoweringPlan(IRRecord):
    plan_id: str
    source_revision_digest: str
    target: TargetRepresentationProfile
    rules: tuple[SemanticLoweringRule, ...]
    gaps: tuple[RepresentationGap, ...]
    capability_debt: tuple[SemanticCapabilityDebt, ...] = ()
    plan_version: str = LOWERING_VERSION

    NESTED: ClassVar = {"target": one(TargetRepresentationProfile), "rules": many(SemanticLoweringRule), "gaps": many(RepresentationGap), "capability_debt": many(SemanticCapabilityDebt)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_identifier(self.plan_id, "plan_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "target", TargetRepresentationProfile.coerce(self.target, "target"))
        for name, kind in (("rules", SemanticLoweringRule), ("gaps", RepresentationGap), ("capability_debt", SemanticCapabilityDebt)):
            values = tuple(kind.coerce(item, f"{name}[]") for item in getattr(self, name))
            object.__setattr__(self, name, tuple(sorted(values, key=lambda item: getattr(item, {"rules": "rule_id", "gaps": "gap_id", "capability_debt": "debt_id"}[name]))))
        object.__setattr__(self, "plan_version", require_version(self.plan_version))
        if any(rule.state is RepresentationState.BLOCKED for rule in self.rules):
            return

    @property
    def blocked(self) -> bool:
        return any(rule.state is RepresentationState.BLOCKED for rule in self.rules) or any(gap.required and gap.state is RepresentationState.BLOCKED for gap in self.gaps)


@dataclass(frozen=True)
class LoweringBundlePlan(IRRecord):
    bundle_id: str
    source_revision_digest: str
    plans: tuple[SemanticLoweringPlan, ...]
    shared_semantic_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"plans": many(SemanticLoweringPlan), "shared_semantic_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", require_identifier(self.bundle_id, "bundle_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        plans = tuple(SemanticLoweringPlan.coerce(item, "plans[]") for item in self.plans)
        if not plans or len({item.target.profile_id for item in plans}) != len(plans):
            raise IRSchemaError("lowering bundle requires unique target profiles")
        if any(item.source_revision_digest != self.source_revision_digest for item in plans):
            raise IRIntegrityError("lowering bundle plans must share one immutable source digest")
        object.__setattr__(self, "plans", tuple(sorted(plans, key=lambda item: item.target.profile_id)))
        refs = tuple(SemanticRef.coerce(item, "shared_semantic_refs[]") for item in self.shared_semantic_refs)
        object.__setattr__(self, "shared_semantic_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))


@dataclass(frozen=True)
class IRTranslationReceipt(IRRecord):
    receipt_id: str
    source_digest: str
    result_digest: str
    target_profile_id: str
    path_differences: Mapping[str, str]
    loss_refs: tuple[SemanticRef, ...] = ()
    lowering_plan_digest: str | None = None

    NESTED: ClassVar = {"loss_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        from .common import deep_freeze
        object.__setattr__(self, "receipt_id", require_identifier(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "source_digest", require_digest(self.source_digest, "source_digest"))
        object.__setattr__(self, "result_digest", require_digest(self.result_digest, "result_digest"))
        object.__setattr__(self, "target_profile_id", require_identifier(self.target_profile_id, "target_profile_id"))
        object.__setattr__(self, "path_differences", deep_freeze(self.path_differences, "path_differences"))
        refs = tuple(SemanticRef.coerce(item, "loss_refs[]") for item in self.loss_refs)
        object.__setattr__(self, "loss_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        if self.lowering_plan_digest is not None:
            object.__setattr__(self, "lowering_plan_digest", require_digest(self.lowering_plan_digest, "lowering_plan_digest"))


@dataclass(frozen=True)
class M03ToM04Mapping(IRRecord):
    operation_id: str
    output_node_refs: tuple[IRNodeRef, ...]
    loss_rule_ids: tuple[str, ...] = ()
    explanation_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"output_node_refs": many(IRNodeRef), "explanation_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_id", require_identifier(self.operation_id, "operation_id"))
        refs = tuple(IRNodeRef.coerce(item, "output_node_refs[]") for item in self.output_node_refs)
        if not refs or len(set(refs)) != len(refs):
            raise IRSchemaError("each M03 operation mapping needs unique output node refs")
        object.__setattr__(self, "output_node_refs", tuple(sorted(refs)))
        object.__setattr__(self, "loss_rule_ids", tuple(sorted(set(require_identifier(item, "loss_rule_ids[]") for item in self.loss_rule_ids))))
        explanation = tuple(SemanticRef.coerce(item, "explanation_refs[]") for item in self.explanation_refs)
        object.__setattr__(self, "explanation_refs", tuple(sorted({item.text: item for item in explanation}.values(), key=lambda item: item.text)))


def lower_m03_bundle(bundle: ExecutionIntentBundle, revision: IRRevision, mappings: tuple[M03ToM04Mapping, ...] | list[M03ToM04Mapping], *, receipt_id: str) -> SemanticLoweringReceipt:
    """Bind every admitted M03 operation/loss rule to immutable, traced M04 output nodes."""
    if not isinstance(bundle, ExecutionIntentBundle):
        raise IRSchemaError("bundle must be the stable M03 ExecutionIntentBundle")
    revision = IRRevision.coerce(revision, "revision")
    mappings = tuple(M03ToM04Mapping.coerce(item, "mappings[]") for item in mappings)
    by_operation = {item.operation_id: item for item in mappings}
    operation_ids = {item.intent_operation_id for item in bundle.operations}
    if len(by_operation) != len(mappings) or set(by_operation) != operation_ids:
        raise IRIntegrityError("M03-to-M04 mapping must cover every operation exactly once")
    nodes = {node.identity_key: node for node in revision.nodes}
    all_loss_rule_ids = {item.rule_id for item in bundle.loss_rules}
    loss_rules_by_id = {item.rule_id: item for item in bundle.loss_rules}
    assigned_loss_rules = [loss_id for mapping in mappings for loss_id in mapping.loss_rule_ids]
    if set(assigned_loss_rules) != all_loss_rule_ids or len(assigned_loss_rules) != len(set(assigned_loss_rules)):
        raise IRIntegrityError("every M03 semantic loss rule must be assigned exactly once")
    for operation_id, mapping in by_operation.items():
        for loss_rule_id in mapping.loss_rule_ids:
            operation_ids_for_rule = set(loss_rules_by_id[loss_rule_id].operation_ids)
            if operation_ids_for_rule and operation_id not in operation_ids_for_rule:
                raise IRIntegrityError(f"M03 loss rule {loss_rule_id} is assigned to an unrelated operation")
    output_rules: list[SemanticLoweringRule] = []
    for operation in bundle.operations:
        mapping = by_operation[operation.intent_operation_id]
        traced_refs: set[str] = set()
        for node_ref in mapping.output_node_refs:
            node = nodes.get((node_ref.document_id, node_ref.node_id))
            if node is None:
                raise IRIntegrityError(f"M03 operation {operation.intent_operation_id} maps to missing M04 node")
            traced_refs.update(item.text for item in node.trace.source_refs)
            traced_refs.update(item.text for item in node.trace.policy_refs)
            traced_refs.update(item.text for item in node.semantic_refs)
        semantic_refs: list[SemanticRef] = []
        for name in (
            "subject_refs", "source_refs", "output_type_refs", "deliverable_refs", "fidelity_contract_refs",
            "protected_anchor_refs", "freedom_zone_refs", "required_explanation_refs", "provenance_refs", "originating_refs",
        ):
            semantic_refs.extend(getattr(operation, name, ()))
        for name in ("intent_slice_ref", "constraint_slice_ref", "approval_boundary_ref"):
            value = getattr(operation, name, None)
            if value is not None:
                semantic_refs.append(value)
        unique_semantic_refs = {item.text: item for item in semantic_refs}
        required_refs = set(unique_semantic_refs)
        explanation_refs = {item.text for item in mapping.explanation_refs}
        if not required_refs.issubset(traced_refs) and not required_refs.issubset(explanation_refs):
            raise IRAdmissionError(f"operation {operation.intent_operation_id} loses M03 explanation reachability")
        for semantic_ref in sorted(unique_semantic_refs.values(), key=lambda item: item.text):
            output_rules.append(SemanticLoweringRule(
                rule_id=f"operation.{operation.intent_operation_id}.{content_digest(semantic_ref.text)[:16]}",
                semantic_ref=semantic_ref,
                state=RepresentationState.EXACT,
                loss_class=SemanticLossClass.LOSSLESS_REQUIRED,
                explanation="M03 operation mapped to traced immutable M04 node",
            ))
    for loss_rule in bundle.loss_rules:
        loss_class = SemanticLossClass(loss_rule.class_enum.value)
        if loss_class is SemanticLossClass.LOSSLESS_REQUIRED:
            state = RepresentationState.EXACT
        elif loss_class is SemanticLossClass.BOUNDED_APPROXIMATION:
            state = RepresentationState.BOUNDED
        elif loss_class is SemanticLossClass.CREATIVE_FREEDOM:
            state = RepresentationState.DEFERRED
        else:
            state = RepresentationState.DEFERRED
        output_rules.append(SemanticLoweringRule(
            rule_id=f"loss.{loss_rule.rule_id}", semantic_ref=loss_rule.item_ref, state=state,
            loss_class=loss_class, tolerance_ref=loss_rule.tolerance_ref,
            loss_rule_ref=SemanticRef(kind="POLICY", ref_id=loss_rule.rule_id, version=loss_rule.contract_version),
            policy_ref=loss_rule.policy_ref,
            explanation="disposition copied from the admitted M03 semantic loss rule",
        ))
    explanation_digest = content_digest({key: value.explanation_refs for key, value in by_operation.items()})
    return SemanticLoweringReceipt(
        receipt_id=receipt_id, m03_bundle_id=bundle.bundle_id,
        source_revision_digest=content_digest({"m03_bundle": bundle.to_payload()}),
        result_revision_digest=revision.revision_digest, rules=tuple(output_rules),
        explanation_reachability_digest=explanation_digest,
    )


def plan_semantic_lowering(
    manifest: RepresentationCapabilityManifest,
    profile: TargetRepresentationProfile,
    semantic_refs: Mapping[str, SemanticLossClass],
    *, plan_id: str, source_revision_digest: str,
) -> SemanticLoweringPlan:
    """Plan provider-neutral semantic representation from named capabilities/loss policies."""
    manifest, profile = RepresentationCapabilityManifest.coerce(manifest, "manifest"), TargetRepresentationProfile.coerce(profile, "profile")
    if manifest != profile.manifest:
        raise IRIntegrityError("target capability manifest differs from profile manifest")
    support_by_id = {item.capability_id: item for item in manifest.support}
    rules: list[SemanticLoweringRule] = []
    gaps: list[RepresentationGap] = []
    debts: list[SemanticCapabilityDebt] = []
    for ref_text, loss_class in sorted(semantic_refs.items()):
        # SemanticRef textual identity is carried by callers; resolve it only from the target manifest.
        declaration = next((item for item in manifest.declarations if any(ref.text == ref_text for ref in item.semantic_refs)), None)
        ref = next((ref for item in manifest.declarations for ref in item.semantic_refs if ref.text == ref_text), None)
        if ref is None:
            raise IRAdmissionError(f"semantic ref {ref_text} has no admitted capability declaration")
        support = support_by_id.get(declaration.capability_id)  # type: ignore[union-attr]
        if support is None:
            from .enums import SupportState
            support = CapabilitySupport(declaration.capability_id, SupportState.UNKNOWN)  # type: ignore[union-attr]
        loss_class = require_enum(loss_class, SemanticLossClass, "loss_class")
        mapped = {
            SupportState.EXACT: RepresentationState.EXACT,
            SupportState.BOUNDED: RepresentationState.BOUNDED,
            SupportState.UNSUPPORTED: RepresentationState.BLOCKED if declaration.requirement is RequirementLevel.REQUIRED else RepresentationState.EXTENSION_REQUIRED,  # type: ignore[union-attr]
            SupportState.UNKNOWN: RepresentationState.BLOCKED if declaration.requirement is RequirementLevel.REQUIRED else RepresentationState.DEFERRED,  # type: ignore[union-attr]
        }[support.state]
        rule = SemanticLoweringRule(
            rule_id=f"profile.{profile.profile_id}.{declaration.capability_id}",  # type: ignore[union-attr]
            semantic_ref=ref, state=mapped, loss_class=loss_class,
            tolerance_ref=support.tolerance_ref, loss_rule_ref=support.loss_rule_ref,
            explanation=f"{support.state.value} support in target representation profile {profile.profile_id}",
        )
        rules.append(rule)
        if support.state is not SupportState.EXACT:
            gaps.append(RepresentationGap(
                gap_id=f"gap.{profile.profile_id}.{declaration.capability_id}", semantic_ref=ref,
                state=mapped, required=declaration.requirement is RequirementLevel.REQUIRED,
                reason=f"target capability {declaration.capability_id} is {support.state.value.lower()}",
                remedy="extend the target semantic profile or admit a bounded loss rule upstream",
            ))
            debts.append(SemanticCapabilityDebt(
                debt_id=f"debt.{profile.profile_id}.{declaration.capability_id}", target_profile_id=profile.profile_id,
                semantic_refs=(ref,), required=declaration.requirement is RequirementLevel.REQUIRED,
                reason=f"capability {declaration.capability_id} is {support.state.value.lower()}", evidence_refs=support.evidence_refs,
            ))
    return SemanticLoweringPlan(plan_id, source_revision_digest, profile, tuple(rules), tuple(gaps), tuple(debts))
