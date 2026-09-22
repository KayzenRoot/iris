"""Construction helpers shared by the M03 kernel tests.

The kernel is verbose by design: every statement carries an authority and a provenance capsule, every
constraint carries a predicate and a scope, and no record can be built by asserting a fact nobody
stood behind. These helpers keep a test focused on the one property it is proving instead of spending
forty lines on a legal revision.

Everything here builds *admissible* material. That is the point: a fixture that had to be loosened to
construct is a fixture that quietly tests a weaker kernel, so the helpers obey the same rules the
production call sites do, and the refusal cases are asserted in the test files rather than simulated
here.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from iris_intent.ambiguity import AmbiguityConsequence, AmbiguityKind, AmbiguityRecord, OpenQuestion
from iris_intent.authority import (
    AuthorityLevel,
    AuthorityPolicyEdge,
    AuthorityPolicyGraph,
    AuthorityPolicyNode,
    default_reserved_boundaries,
)
from iris_intent.briefs import BriefRevision, RevisionKind, intent_model_for
from iris_intent.conflicts import (
    ConflictClass,
    ConflictConsequence,
    SemanticConflict,
    declare_conflict,
    detect_conflicts,
)
from iris_intent.constraints import (
    Constraint,
    ConstraintBundle,
    ConstraintPolarity,
    ConstraintScope,
    ConstraintStrength,
)
from iris_intent.fingerprints import (
    IntentDelta,
    SemanticEquivalenceProfile,
    diff_models,
    fingerprint_bundle,
    fingerprint_revision,
)
from iris_intent.freshness import (
    BriefFreshnessVector,
    DerivedArtifactKind,
    DerivedIntentDependency,
    FreshnessDimension,
    assess_freshness,
)
from iris_intent.identity import VERSIONED_REF_KINDS, CreativeBriefIdentity, RefKind, SemanticRef, SourceKind
from iris_intent.intent import AuthorityBasis, IntentAuthorityRef, IntentModel, IntentStatement
from iris_intent.overrides import (
    InvalidationTarget,
    OverrideAction,
    OverrideDebt,
    OverrideLedger,
    OverrideReceipt,
    SemanticStateSnapshot,
    issue_override,
)
from iris_intent.predicates import (
    PredicateArgument,
    PredicateCall,
    PredicateRegistry,
    PredicateSignature,
    ValueType,
)
from iris_intent.readiness import SemanticReleaseReadinessReport, assess_release_readiness
from iris_intent.reuse import ReusePassport, passport_for
from iris_intent.slicing import MinimumSufficientSemanticSlice, SemanticSliceRequest, slice_intent
from iris_intent.sources import (
    AnchorSpan,
    DerivationKind,
    ProvenanceCapsule,
    RawInputRef,
    SourceAnchor,
)
from iris_intent.versions import content_digest

__all__ = [
    "BRIEF_ID",
    "DIGEST_LEN",
    "ICON",
    "LOGO",
    "SPEC",
    "TONE",
    "admitted_revision",
    "ambiguity",
    "authority_graph",
    "authority_ref",
    "brief_identity",
    "bundle",
    "bundle_fingerprint",
    "capsule",
    "conflict",
    "constraint_ref",
    "contradictory_pair",
    "debt",
    "delta",
    "dependency",
    "detected_conflict",
    "digest",
    "draft_revision",
    "equivalence_profile",
    "fingerprint",
    "ledger",
    "model",
    "passage",
    "passport",
    "policy_ref",
    "predicate_registry",
    "question",
    "raw_source",
    "readiness",
    "receipt",
    "ref",
    "revision",
    "revision_chain",
    "revision_ref",
    "rule",
    "signature",
    "slice_for",
    "statement",
    "upstream_matching",
    "vector",
]

BRIEF_ID = "brief.brand.launch"
LOGO = "brief.visual.logo"
TONE = "brief.audio.tone"
ICON = "brief.visual.icon"
SPEC = "brief.visual.spec"
DIGEST_LEN = 64

RELAXATION_TARGETS = (
    InvalidationTarget.INTENT_FINGERPRINT.value,
    InvalidationTarget.CONSTRAINT_FINGERPRINT.value,
    InvalidationTarget.CONTRACT_SET.value,
    InvalidationTarget.EXECUTION_BUNDLE.value,
    InvalidationTarget.READINESS_REPORT.value,
)


def digest(seed: Any) -> str:
    """A real digest over anything, so no fixture has to invent a hex string."""

    return content_digest(seed)


def _is_versioned(kind: str) -> bool:
    try:
        member = RefKind(kind)
    except ValueError:
        return False
    return member in VERSIONED_REF_KINDS


def ref(kind: str, ident: str, version: str | None = None, *, digest_value: str | None = None) -> SemanticRef:
    """A bound citation. Versioned kinds are pinned here so a fixture cannot forget and fail later."""

    pinned = version
    if pinned is None and _is_versioned(kind):
        pinned = "v1"
    return SemanticRef(
        kind=kind, ref_id=ident, version=pinned, content_digest=digest_value or digest(ident)
    )


def policy_ref(ident: str = "policy.brand") -> SemanticRef:
    return ref(RefKind.POLICY.value, f"{ident}.v1", "1.0.0")


def revision_ref(ident: str = "rev.7") -> SemanticRef:
    return ref(RefKind.REVISION.value, ident)


def constraint_ref(ident: str) -> SemanticRef:
    return ref(RefKind.CONSTRAINT.value, ident)


def authority_ref(
    level: str = AuthorityLevel.HUMAN_OWNER.value,
    *,
    basis: str | None = None,
    granted_by: SemanticRef | None = None,
    policy: SemanticRef | None = None,
    rationale: str = "the owner said so in the brief",
) -> IntentAuthorityRef:
    """An authority citation with the basis its level requires, so the shield has something to read."""

    chosen = basis or (
        AuthorityBasis.POLICY.value
        if level == AuthorityLevel.GOVERNED_POLICY.value
        else AuthorityBasis.REVISION.value
        if level in {AuthorityLevel.HUMAN_OWNER.value, AuthorityLevel.TEAM_ASSERTED.value}
        else AuthorityBasis.PROJECT_RECORD.value
    )
    if chosen == AuthorityBasis.POLICY.value:
        return IntentAuthorityRef(
            authority=level, basis=chosen, policy_ref=policy or policy_ref(), rationale=rationale
        )
    if chosen == AuthorityBasis.REVISION.value:
        return IntentAuthorityRef(
            authority=level,
            basis=chosen,
            granted_by=granted_by or revision_ref(),
            rationale=rationale,
        )
    return IntentAuthorityRef(authority=level, basis=chosen)


def raw_source(
    *, source_id: str = "src.brief", kind: str = SourceKind.HUMAN_MESSAGE.value, language: str = "en"
) -> RawInputRef:
    return RawInputRef(
        source_id=source_id,
        kind=kind,
        authority=AuthorityLevel.HUMAN_OWNER.value,
        content_digest=digest(source_id),
        language=language,
    )


def capsule(
    *,
    capsule_id: str = "cap.brief",
    source: RawInputRef | None = None,
    derivation: str = DerivationKind.PARAPHRASED.value,
    anchors: Sequence[SourceAnchor] = (),
) -> ProvenanceCapsule:
    item = source or raw_source()
    return ProvenanceCapsule(
        capsule_id=capsule_id,
        derivation=derivation,
        source_refs=(item.source_ref,),
        anchors=tuple(anchors),
    )


def passage(text: str, *, source_id: str = "src.brief", start: int = 0) -> SourceAnchor:
    """A span inside a preserved source, for the fixtures that cite exact wording."""

    return SourceAnchor(
        anchor_id=f"an.{source_id}.{digest(text)[:8]}",
        source_id=source_id,
        quote_digest=digest(text),
        language="en",
        span=AnchorSpan(start=start, end=start + len(text)),
    )


def statement(
    ident: str,
    path: str = LOGO,
    *,
    assertion: str | None = None,
    mandatory: bool = False,
    authority: IntentAuthorityRef | None = None,
    source: RawInputRef | None = None,
    kind: str = "CONSTRAINT_SEMANTICS",
    value: Any = None,
    **over: Any,
) -> IntentStatement:
    origin = over.pop("origin", "EXPLICIT")
    return IntentStatement(
        statement_id=ident,
        semantic_path=path,
        kind=kind,
        assertion=assertion or f"{path} holds",
        origin=origin,
        authority=authority or authority_ref(),
        value={"state": "on"} if value is None else value,
        mandatory=mandatory,
        provenance=capsule(source=source, capsule_id=f"cap.{ident}"),
        **over,
    )


def brief_identity(
    *, brief_id: str = BRIEF_ID, label: str = "Iris launch", aliases: Sequence[str] = ()
) -> CreativeBriefIdentity:
    return CreativeBriefIdentity(brief_id=brief_id, label=label, aliases=tuple(aliases))


def revision(
    number: int,
    statements: Iterable[IntentStatement] = (),
    *,
    ident: str | None = None,
    brief_id: str = BRIEF_ID,
    status: str = "ADMITTED",
    kind: str = RevisionKind.CORRECTION.value,
    **over: Any,
) -> BriefRevision:
    """A revision whose ancestry names match the ids this module's :func:`revision_chain` produces."""

    items = tuple(statements)
    source_ids = sorted({capsule_source_id(item) for item in items}) or ["src.brief"]
    payload: dict[str, Any] = {
        "revision_id": ident if ident is not None else f"rev.{number}",
        "brief_id": brief_id,
        "revision_number": number,
        "kind": kind,
        "status": status,
        "statements": items,
        "sources": tuple(raw_source(source_id=name) for name in source_ids),
        "ancestor_revision_ids": ()
        if number == 1
        else tuple(f"rev.{index}" for index in range(1, number)),
        "predecessor_revision_id": None if number == 1 else f"rev.{number - 1}",
        "created_by": revision_ref(ident if ident is not None else f"rev.{number}"),
        "admitted_by": (
            None if status == "DRAFT" else revision_ref(ident if ident is not None else f"rev.{number}")
        ),
    }
    payload.update(over)
    return BriefRevision(**payload)


def capsule_source_id(item: IntentStatement) -> str:
    """The source a statement stands on, which is what a revision's source set is made of."""

    return item.provenance.source_refs[0].ref_id


def admitted_revision(number: int = 7, *, mandatory_paths: Sequence[str] = (LOGO,)) -> BriefRevision:
    """The revision most fixtures hang off: admitted, mandatory, and sourced from a human message."""

    items = tuple(
        statement(f"st.{index}", path, mandatory=path in mandatory_paths)
        for index, path in enumerate((LOGO, TONE), start=1)
    )
    return revision(number, items)


def draft_revision(number: int = 7) -> BriefRevision:
    return revision(number, (statement("st.logo", LOGO),), status="DRAFT")


def revision_chain(numbers: Iterable[int] = (1, 2, 3)) -> tuple[BriefRevision, ...]:
    """A chain whose ancestors the brief store will accept, built in order."""

    paths = (LOGO, TONE, ICON, SPEC)
    return tuple(
        revision(
            number,
            tuple(
                statement(f"st.{number}.{index}", path)
                for index, path in enumerate(paths[: max(1, number)], start=1)
            ),
        )
        for number in numbers
    )


def signature(
    predicate_id: str,
    *,
    path: str = LOGO,
    arguments: Sequence[tuple[str, str]] = (),
    version: str = "v1",
    trust: str = "CORE",
) -> PredicateSignature:
    return PredicateSignature(
        predicate_id=predicate_id,
        version=version,
        semantic_path=path,
        trust=trust,
        argument_types=tuple(
            PredicateArgument(
                name=name,
                type=kind,
                required=True,
                allowed_values=(),
                description=f"the {name} slot of {predicate_id}",
            )
            for name, kind in arguments
        ),
        interpretation=f"whether the artifact satisfies {predicate_id}",
    )


def predicate_registry(*extra: PredicateSignature) -> PredicateRegistry:
    return PredicateRegistry(
        (
            signature("shows_logo"),
            signature("mentions_brand", path=TONE, arguments=(("phrase", ValueType.TEXT.value),)),
            signature("runs_at_least", path=TONE, arguments=(("seconds", ValueType.NUMBER.value),)),
            *extra,
        )
    )


def rule(
    ident: str,
    path: str = LOGO,
    *,
    strength: str = ConstraintStrength.HARD.value,
    polarity: str = ConstraintPolarity.REQUIRE.value,
    predicate: str = "shows_logo",
    arguments: dict[str, Any] | None = None,
    modality: str = "IMAGE",
    authority: IntentAuthorityRef | None = None,
    mandatory: bool = False,
    **over: Any,
) -> Constraint:
    return Constraint(
        constraint_id=ident,
        semantic_path=path,
        predicate=PredicateCall(predicate_id=predicate, version="v1", arguments=arguments or {}),
        polarity=polarity,
        strength=strength,
        scope=ConstraintScope(subject_paths=(path,), modalities=(modality,)),
        authority=authority or authority_ref(AuthorityLevel.PROJECT_RECORD.value),
        modality=modality,
        mandatory=mandatory,
        provenance=capsule(capsule_id=f"cap.{ident}"),
        **over,
    )


def bundle(
    constraints: Iterable[Constraint] = (),
    *,
    ident: str = "bundle.iris",
    brief_id: str = BRIEF_ID,
    revision_id: str = "rev.7",
) -> ConstraintBundle:
    return ConstraintBundle(
        bundle_id=ident,
        brief_id=brief_id,
        revision_id=revision_id,
        version="v1",
        constraints=tuple(constraints),
        admitted_by=revision_ref(revision_id),
    )


def equivalence_profile(*, profile_id: str = "profile.iris", **over: Any) -> SemanticEquivalenceProfile:
    arguments: dict[str, Any] = {"profile_id": profile_id, "version": "v1"}
    arguments.update(over)
    return SemanticEquivalenceProfile(**arguments)


def fingerprint(
    item: BriefRevision,
    *,
    profile: SemanticEquivalenceProfile | None = None,
    ident: str = "fp.model",
):
    return fingerprint_revision(item, profile=profile or equivalence_profile(), fingerprint_id=ident)


def bundle_fingerprint(
    item: ConstraintBundle,
    *,
    profile: SemanticEquivalenceProfile | None = None,
    ident: str = "fp.bundle",
):
    return fingerprint_bundle(item, profile=profile or equivalence_profile(), fingerprint_id=ident)


def delta(before, after, *, ident: str = "delta.iris") -> IntentDelta:
    return diff_models(before, after, delta_id=ident)


def model(revision_item: BriefRevision, *, ident: str = "model.iris", **over: Any) -> IntentModel:
    return intent_model_for(revision_item, model_id=ident, **over)


def slice_for(
    model_item: IntentModel,
    bundle_item: ConstraintBundle | None,
    paths: Sequence[str] = (LOGO,),
    *,
    request_id: str = "req.iris",
    purpose: str = "COMPILE_QUALITY",
    consumer: str = "contracts.iris",
    **over: Any,
) -> MinimumSufficientSemanticSlice:
    return slice_intent(
        model_item,
        bundle_item,
        SemanticSliceRequest(
            request_id=request_id,
            consumer_ref=ref(RefKind.CONTRACT_SET.value, consumer),
            purpose=purpose,
            paths=tuple(paths),
            revision_ref=revision_ref(model_item.revision_id),
            **over,
        ),
    )


def question(
    ident: str = "q.iris",
    *,
    blocking: bool = True,
    paths: Sequence[str] = (LOGO,),
    status: str = "OPEN",
    answer: SemanticRef | None = None,
    text: str = "Which of the two marks is the client's?",
) -> OpenQuestion:
    return OpenQuestion(
        question_id=ident,
        text=text,
        consequence=(
            AmbiguityConsequence.BLOCKING.value
            if blocking
            else AmbiguityConsequence.NON_BLOCKING.value
        ),
        status=status,
        semantic_paths=tuple(paths),
        blocking=blocking,
        addressed_to="owner",
        answer_ref=answer,
    )


def ambiguity(
    ident: str = "am.iris",
    *,
    path: str = LOGO,
    kind: str = AmbiguityKind.TERM_OVERLOAD.value,
    consequence: str = AmbiguityConsequence.BLOCKING.value,
    readings: Sequence[str] = ("wordmark", "monogram"),
    statements: Sequence[str] = ("st.1",),
) -> AmbiguityRecord:
    return AmbiguityRecord(
        ambiguity_id=ident,
        kind=kind,
        consequence=consequence,
        semantic_paths=(path,),
        question="Which reading is meant?",
        candidate_readings=tuple(readings),
        affected_statement_ids=tuple(statements),
        requires_human=True,
    )


def authority_graph(*, graph_id: str = "authority.iris", human_only: bool = True) -> AuthorityPolicyGraph:
    return AuthorityPolicyGraph(
        graph_id=graph_id,
        version="v1",
        nodes=(
            AuthorityPolicyNode(
                node_id="owner",
                authority_level=AuthorityLevel.HUMAN_OWNER.value,
                rule_classes=("brand.creative",),
                human_only=human_only,
            ),
            AuthorityPolicyNode(
                node_id="brand-policy",
                authority_level=AuthorityLevel.GOVERNED_POLICY.value,
                rule_classes=("brand.logo",),
            ),
        ),
        edges=(
            AuthorityPolicyEdge(
                edge_id="owner-over-brand",
                subject_node_id="owner",
                object_node_id="brand-policy",
                actions=(
                    OverrideAction.RELAX.value,
                    OverrideAction.DISABLE.value,
                    OverrideAction.REPLACE.value,
                ),
            ),
        ),
        reserved_boundaries=default_reserved_boundaries(evidence_refs=(policy_ref(),)),
        admitted_by=revision_ref(),
    )


def conflict(
    ident: str = "cnf.iris",
    *,
    path: str = LOGO,
    klass: str = ConflictClass.QUALITY_POLICY_CONFLICT.value,
    consequence: str = ConflictConsequence.BLOCKING.value,
    parties: Sequence[SemanticRef] | None = None,
    revision_cited: SemanticRef | None = None,
) -> SemanticConflict:
    """A conflict the kernel cannot derive on its own, filed with the evidence that says who could."""

    return declare_conflict(
        conflict_id=ident,
        conflict_class=klass,
        parties=tuple(parties or (constraint_ref(f"{ident}.a"), constraint_ref(f"{ident}.b"))),
        semantic_paths=(path,),
        evidence_refs=(policy_ref(),),
        authority_refs=(policy_ref(),),
        rationale=f"{path} carries two readings that cannot both hold",
        revision_ref=revision_cited or revision_ref(),
        consequence=consequence,
    )


def contradictory_pair(path: str = LOGO, *, ident: str = "cn") -> tuple[Constraint, Constraint]:
    """Two hard rules the kernel can only read as a contradiction."""

    return (
        rule(f"{ident}.require", path),
        rule(f"{ident}.forbid", path, polarity=ConstraintPolarity.FORBID.value),
    )


def detected_conflict(
    constraints: Sequence[Constraint] | None = None,
    *,
    ident: str = "logo",
    graph: AuthorityPolicyGraph | None = None,
    rule_class: str = "brand.logo",
) -> SemanticConflict:
    """A conflict the kernel derives itself, which is the only honest route to some blockers."""

    items = tuple(constraints or contradictory_pair())
    found = detect_conflicts(
        bundle=bundle(items, ident=f"bundle.{ident}"),
        revision_ref=revision_ref(),
        graph=graph or authority_graph(),
        rule_classes={item.constraint_id: rule_class for item in items},
        conflict_prefix=f"cnf.{ident}",
    )
    if not found:
        raise AssertionError(f"the kernel derived no conflict from {ident}")
    return found[0]


def override_pair(path: str = LOGO, *, ident: str = "cn.logo"):
    """Before/after snapshots for a relaxation, with the ids ``issue_override`` insists on."""

    hard = rule(ident, path)
    soft = rule(ident, path, strength=ConstraintStrength.ADVISORY.value)
    return (
        hard,
        SemanticStateSnapshot.of_constraint(hard, snapshot_id=f"snap.{ident}.before"),
        SemanticStateSnapshot.of_constraint(soft, snapshot_id=f"snap.{ident}.after"),
    )


def receipt(
    *,
    ident: str = "ovr.iris",
    path: str = LOGO,
    rule_class: str = "brand.logo",
    expires: int = 7,
    graph: AuthorityPolicyGraph | None = None,
    actor: IntentAuthorityRef | None = None,
    action: str = OverrideAction.RELAX.value,
    human_decision: SemanticRef | None = None,
) -> OverrideReceipt:
    hard, before, after = override_pair(path, ident=f"cn.{ident}")
    return issue_override(
        override_id=ident,
        action=action,
        rule_class=rule_class,
        semantic_path=path,
        target_refs=(hard.constraint_ref,),
        actor=actor or authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
        graph=graph or authority_graph(),
        reason="the brand policy admits a softened reading for this region",
        previous_state=before,
        effective_state=after if action == OverrideAction.RELAX.value else None,
        recorded_in_revision=revision_ref("rev.8"),
        human_decision=human_decision,
        expires_after_revision=expires,
        invalidation=RELAXATION_TARGETS,
    )


def debt(
    ident: str = "debt.iris",
    *,
    blocks: bool = True,
    closed: bool = False,
    paths: Sequence[str] = (LOGO,),
    override_ids: Sequence[str] = ("ovr.iris",),
) -> OverrideDebt:
    item = OverrideDebt(
        debt_id=ident,
        kind="TEMPORARY_BRAND_EXCEPTION",
        override_refs=tuple(ref(RefKind.RECEIPT.value, name) for name in override_ids),
        opened_at_revision=5,
        expires_after_revision=9,
        affected_paths=tuple(paths),
        blocks_release=blocks,
    )
    if closed:
        return item.close(closed_by=revision_ref("rev.9"), reason="the exception was folded into policy")
    return item


def ledger(
    receipts: Iterable[OverrideReceipt] = (),
    debts: Iterable[OverrideDebt] = (),
    *,
    ledger_id: str = "ledger.iris",
) -> OverrideLedger:
    return OverrideLedger(
        ledger_id=ledger_id,
        brief_ref=ref(RefKind.BRIEF.value, BRIEF_ID),
        revision_ref=revision_ref(),
        receipts=tuple(receipts),
        debts=tuple(debts),
    )


def dependency(
    ident: str,
    *,
    upstream_id: str = "src.art",
    path: str = SPEC,
    dimension: FreshnessDimension = FreshnessDimension.SOURCE_REVISION,
    derived: SemanticRef | None = None,
    valid_through: int = 7,
) -> DerivedIntentDependency:
    return DerivedIntentDependency(
        dependency_id=ident,
        derived_ref=derived or ref(RefKind.CONTRACT_SET.value, "contracts.iris"),
        derived_kind=DerivedArtifactKind.CONTRACT_SET.value,
        upstream_ref=ref(RefKind.SOURCE.value, upstream_id),
        dimension=dimension.value,
        invalidates=dimension.staleness_scope.value,
        match_on=("DIGEST",),
        last_known_digest=digest(upstream_id),
        valid_through_revision=valid_through,
        partial=True,
        affected_paths=(path,),
        rationale=f"the contract set was derived from {upstream_id}",
    )


def upstream_matching(
    dependencies: Iterable[DerivedIntentDependency], *, moved: Iterable[str] = ()
) -> dict[str, dict[str, Any]]:
    """An upstream position report that either matches the recorded digests or says it moved."""

    changed = set(moved)
    return {
        item.upstream_ref.text: {
            "digest": digest(
                item.upstream_ref.ref_id + (".moved" if item.upstream_ref.ref_id in changed else "")
            )
        }
        for item in dependencies
    }


def vector(
    dependencies: Iterable[DerivedIntentDependency],
    upstream: dict[str, Any],
    *,
    ident: str = "fv.iris",
    declared: Iterable[FreshnessDimension] = (FreshnessDimension.SOURCE_REVISION,),
    revision_ordinal: int = 7,
) -> BriefFreshnessVector:
    items = tuple(dependencies)
    return assess_freshness(
        vector_id=ident,
        brief_ref=ref(RefKind.BRIEF.value, BRIEF_ID),
        revision_ref=revision_ref(),
        subject_ref=items[0].derived_ref,
        dependencies=items,
        upstream=upstream,
        revision_ordinal=revision_ordinal,
        declared_dimensions=tuple(item.value for item in declared),
    )


def passport(
    revision_item: BriefRevision,
    dependencies: Iterable[DerivedIntentDependency],
    *,
    ident: str = "pp.iris",
    profile: SemanticEquivalenceProfile | None = None,
) -> ReusePassport:
    """A passport over the artifact plus the revision and model it was compiled from.

    The two are not optional detail: a passport that cites only a source file cannot tell "nothing
    moved" from "the model was rebuilt from the same bytes", which is the difference reuse turns on.
    """

    fingerprint_item = fingerprint(revision_item, profile=profile, ident=f"fp.{ident}")
    items = tuple(dependencies) + (
        dependency(
            f"dep.model.{ident}",
            upstream_id=f"model.{ident}",
            dimension=FreshnessDimension.SEMANTIC_MODEL,
            derived=fingerprint_item.model_ref,
        ),
    )
    return passport_for(
        fingerprint_item,
        passport_id=ident,
        brief_ref=ref(RefKind.BRIEF.value, BRIEF_ID),
        revision_ref=revision_item.revision_ref,
        dependencies=tuple(
            item
            if item.derived_ref.text == fingerprint_item.model_ref.text
            else DerivedIntentDependency.coerce(
                {
                    **item.to_payload(),
                    "derived_ref": fingerprint_item.model_ref.to_payload(),
                }
            )
            for item in items
        ),
    )


def readiness(
    revision_item: BriefRevision,
    *,
    ident: str = "rr.iris",
    profile: SemanticEquivalenceProfile | None = None,
    **inputs: Any,
) -> SemanticReleaseReadinessReport:
    """A report over the given inputs, defaulting to one open question.

    The kernel refuses a report that assessed no family at all, so a bare call has to carry
    something; an unanswered question is the smallest honest input.
    """

    if not any(value is not None for value in inputs.values()):
        inputs["questions"] = [question()]
    return assess_release_readiness(
        report_id=ident,
        revision=revision_item,
        profile=profile or equivalence_profile(),
        **inputs,
    )
