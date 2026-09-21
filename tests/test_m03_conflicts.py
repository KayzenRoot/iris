"""The conflict law: detection decides nothing, authority decides everything, and nothing expires quietly.

A contradiction between two admitted rules is the easiest thing in the kernel to *notice* and the
easiest to make disappear. This file therefore proves three refusals rather than three features. The
first is that a disagreement cannot be closed by being later, being more specific, being more
confident or being filed by hand: the record has no winner field, the detector grants no authority,
and the exits a class offers are floors. The second is that weakening a rule is an act of authority
with a gradient: an inferred or recorded actor cannot relax a governed rule, an agent may propose and
may not approve, the reserved boundaries are out of reach of every actor including the human owner,
and a disable needs both the top of the ladder and an admitted human revision behind it. The third is
that an override is a fact with an expiry: once it lapses, everything that leaned on it is stale and
says so by name, and the debt it leaves is M03's own obligation rather than an M01 quality defect.
The last pair keeps the decision small: one conflict is resolvable from one locality, and a
resolution fingerprint reports which of its inputs moved instead of handing out a stale verdict.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_intent.authority import (
    AuthorityLevel,
    AuthorityPolicyGraph,
    default_reserved_boundaries,
    is_reserved_rule_class,
)
from iris_intent.conflicts import (
    ConflictClass,
    ConflictConsequence,
    ConflictResolutionState,
    MinimumSufficientConflictSlice,
    ScopeSplitProposal,
    SemanticConflict,
    SplitBranch,
    declare_conflict,
    detect_conflicts,
    escalate_conflict,
    resolve_conflict,
)
from iris_intent.constraints import Condition, ConstraintScope, ConstraintStrength
from iris_intent.errors import (
    AuthorityError,
    ConflictBlockedError,
    OverrideRefusedError,
    QualityAuthorityError,
    RefError,
    SchemaValidationError,
    ScopeError,
    StaleSemanticError,
)
from iris_intent.identity import RefKind
from iris_intent.overrides import (
    InvalidationTarget,
    OverrideAction,
    OverrideDebt,
    OverrideLedger,
    OverrideProposal,
    TemporaryOverrideLease,
    authorize_proposal,
    issue_override,
    propose_override,
)
from iris_quality.debt import QualityDebt

from tests import m03_kernel_support as S

GRAPH = S.authority_graph()
MODEL = S.model(S.admitted_revision(7))

#: The same policy, re-issued: one identity, moved content. A pin reads this as staleness, while a
#: graph under a different ``graph_id`` is the wrong object entirely and reads as a ref failure.
MOVED_GRAPH = replace(GRAPH, version="v2")

#: §6's canonical six, spelled out so a test fails when a boundary stops being reserved.
RESERVED_CLASSES = (
    "m01.fatal-gate",
    "m01.evaluator-authority",
    "m02.immutable-history",
    "governance.work-order",
    "rights.security",
    "platform.legal",
)


def detect(
    constraints: Any,
    *,
    ident: str = "t",
    context: Any = None,
    graph: Any = GRAPH,
    rule_class: str = "brand.logo",
) -> tuple:
    """Run the detector over a rule set the way a compiler would."""

    items = tuple(constraints)
    return detect_conflicts(
        bundle=S.bundle(items, ident=f"bundle.{ident}"),
        revision_ref=S.revision_ref(),
        context=context,
        graph=graph,
        rule_classes={item.constraint_id: rule_class for item in items},
        conflict_prefix=f"cnf.{ident}",
    )


def contradiction(**over: Any) -> Any:
    """One detected DIRECT_CONTRADICTION, built fresh so a test cannot leak state into a neighbour."""

    return S.detected_conflict(graph=over.pop("graph", GRAPH), **over)


def resolved_contradiction(**over: Any) -> Any:
    """The same conflict closed by a receipt, for the gates that only bite afterwards."""

    conflict = contradiction()
    payload: dict[str, Any] = {
        "state": ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE.value,
        "decided_by": S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
        "rationale": "the owner relaxed the mark requirement for this region under the brand policy",
        "recorded_in_revision": S.revision_ref("rev.9"),
        "graph": over.pop("graph", GRAPH),
        "receipt": over.pop("receipt", S.receipt(graph=GRAPH)),
        "human_decision": S.revision_ref("rev.9"),
    }
    payload.update(over)
    return resolve_conflict(conflict, **payload)


class ContradictionDetection(unittest.TestCase):
    """Proofs 1, 2 and 3: the detector names what it can prove and stays silent otherwise."""

    def test_require_and_forbid_on_one_path_is_a_blocking_direct_contradiction(self) -> None:
        conflict = contradiction()
        self.assertEqual(conflict.conflict_class, ConflictClass.DIRECT_CONTRADICTION.value)
        self.assertEqual(conflict.consequence, ConflictConsequence.BLOCKING.value)
        self.assertEqual(conflict.class_enum.default_consequence, ConflictConsequence.BLOCKING)
        self.assertTrue(conflict.blocks_contract)
        self.assertEqual(len(conflict.parties), 2)
        self.assertEqual(
            sorted(item.ref_id for item in conflict.parties), ["cn.forbid", "cn.require"]
        )
        self.assertEqual(conflict.semantic_paths, (S.LOGO,))

    def test_detection_is_deterministic_over_the_same_rule_set(self) -> None:
        pair = S.contradictory_pair()
        first = detect(pair, ident="stable")[0]
        second = detect(S.contradictory_pair(), ident="stable")[0]
        self.assertEqual(first.conflict_id, second.conflict_id)
        self.assertEqual(first.conflict_digest, second.conflict_digest)
        self.assertEqual(first.conflict_ref.text, second.conflict_ref.text)

    def test_the_kernel_derives_the_contradiction_and_no_hand_filing_of_it(self) -> None:
        self.assertTrue(ConflictClass.DIRECT_CONTRADICTION.detected_by_kernel)
        with self.assertRaises(ConflictBlockedError) as caught:
            declare_conflict(
                conflict_id="cnf.by.hand",
                conflict_class=ConflictClass.DIRECT_CONTRADICTION.value,
                parties=(S.constraint_ref("cn.a"), S.constraint_ref("cn.b")),
                semantic_paths=(S.LOGO,),
                evidence_refs=(S.policy_ref(),),
                rationale="somebody wrote down the contradiction instead of running the detector",
                revision_ref=S.revision_ref(),
            )
        self.assertIn("derivable", str(caught.exception))

    def test_rules_on_disjoint_paths_do_not_conflict(self) -> None:
        pair = (
            S.rule("cn.mark.require", S.LOGO),
            S.rule("cn.voice.forbid", S.TONE, polarity="FORBID", predicate="mentions_brand"),
        )
        self.assertFalse(pair[0].binds(pair[1]))
        self.assertEqual(detect(pair, ident="disjoint"), ())

    def test_non_overlapping_modalities_on_one_path_do_not_conflict(self) -> None:
        visual = S.rule("cn.logo.image", S.LOGO, modality="IMAGE")
        heard = S.rule("cn.logo.audio", S.LOGO, polarity="FORBID", modality="AUDIO")
        self.assertFalse(visual.binds(heard))
        self.assertEqual(detect([visual, heard], ident="channels"), ())

    def test_a_rule_inactive_under_the_context_raises_no_conflict(self) -> None:
        always = S.rule("cn.cond.require", S.LOGO)
        conditional = S.rule(
            "cn.cond.forbid",
            S.LOGO,
            polarity="FORBID",
            conditions=[Condition("destination", "EQ", ("broadcast",))],
        )
        teaser = detect([always, conditional], ident="conditional", context={"destination": "teaser"})
        self.assertEqual(teaser, ())
        self.assertEqual([item.constraint_id for item in teaser], [])
        broadcast = detect([always, conditional], ident="conditional", context={"destination": "broadcast"})
        self.assertEqual(len(broadcast), 1)
        self.assertEqual(broadcast[0].conflict_class, ConflictClass.DIRECT_CONTRADICTION.value)
        self.assertEqual(broadcast[0].conditions, conditional.conditions)

    def test_two_conditionally_inactive_rules_are_not_an_active_disagreement(self) -> None:
        left = S.rule(
            "cn.both.require",
            S.LOGO,
            conditions=[Condition("destination", "EQ", ("broadcast",))],
        )
        right = S.rule(
            "cn.both.forbid",
            S.LOGO,
            polarity="FORBID",
            conditions=[Condition("destination", "EQ", ("teaser",))],
        )
        self.assertEqual(detect([left, right], ident="both-inactive", context=None), ())
        self.assertEqual(
            detect([left, right], ident="both-inactive", context={"destination": "outdoor"}), ()
        )

    def test_the_detector_never_emits_a_speculative_conditional_collision(self) -> None:
        found = detect(S.contradictory_pair(), ident="classes")
        self.assertTrue(found)
        self.assertNotIn(
            ConflictClass.CONDITIONAL_COLLISION.value,
            {item.conflict_class for item in found},
        )
        self.assertTrue(ConflictClass.CONDITIONAL_COLLISION.detected_by_kernel)
        with self.assertRaises(ConflictBlockedError):
            declare_conflict(
                conflict_id="cnf.speculative",
                conflict_class=ConflictClass.CONDITIONAL_COLLISION.value,
                parties=(S.constraint_ref("cn.a"), S.constraint_ref("cn.b")),
                semantic_paths=(S.LOGO,),
                evidence_refs=(S.policy_ref(),),
                rationale="they might clash under a condition neither is active under",
                revision_ref=S.revision_ref(),
            )


class DetectionGrantsNoAuthority(unittest.TestCase):
    """Invariant 29: recency, specificity and confidence are evidence, never a verdict."""

    def test_a_later_recorded_rule_does_not_resolve_the_earlier_one(self) -> None:
        earlier = S.rule("cn.old.require", S.LOGO, metadata={"recorded_at": "2026-01-01"})
        later = S.rule(
            "cn.new.forbid",
            S.LOGO,
            polarity="FORBID",
            metadata={"recorded_at": "2026-09-02"},
            revision_ref=S.revision_ref("rev.9"),
        )
        conflict = detect([earlier, later], ident="recency")[0]
        self.assertEqual(conflict.resolution_state, ConflictResolutionState.UNRESOLVED.value)
        self.assertIsNone(conflict.resolution)
        self.assertFalse(conflict.resolved)
        self.assertEqual(
            sorted(conflict.party_ids), ["cn.new.forbid", "cn.old.require"]
        )
        self.assertIs(SemanticConflict.winner_chosen_by_recency, conflict.winner_chosen_by_recency)
        self.assertFalse(hasattr(conflict, "winner"))
        with self.assertRaises(ConflictBlockedError) as caught:
            conflict.require_resolved("compile the contract set")
        self.assertIn("DIRECT_CONTRADICTION", str(caught.exception))

    def test_the_conflict_record_carries_no_winner_field_at_all(self) -> None:
        conflict = contradiction()
        field_names = set(conflict.to_payload())
        self.assertNotIn("winner", field_names)
        self.assertNotIn("superseded_party", field_names)
        self.assertNotIn("priority", field_names)
        self.assertEqual(field_names & {"parties", "semantic_paths"}, {"parties", "semantic_paths"})

    def test_a_high_confidence_inference_cannot_outrank_an_explicit_human_rule(self) -> None:
        human = S.rule(
            "cn.owner.require",
            S.LOGO,
            authority=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
        )
        inferred = S.rule(
            "cn.model.forbid",
            S.LOGO,
            polarity="FORBID",
            strength=ConstraintStrength.ADVISORY.value,
            authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
        )
        conflict = detect([human, inferred], ident="confidence")[0]
        self.assertEqual(
            conflict.actor_levels,
            (AuthorityLevel.HUMAN_OWNER.value, AuthorityLevel.MODEL_INFERRED.value),
        )
        self.assertEqual(conflict.consequence, ConflictConsequence.BLOCKING.value)
        self.assertIs(conflict.uses_confidence, False)
        self.assertEqual(
            sorted(conflict.party_ids), ["cn.model.forbid", "cn.owner.require"]
        )
        with self.assertRaises(AuthorityError) as caught:
            resolve_conflict(
                conflict,
                state=ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY.value,
                decided_by=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
                rationale="the model is 0.99 sure and the other rule is only a person's",
                recorded_in_revision=S.revision_ref("rev.8"),
                graph=GRAPH,
            )
        self.assertIn("may not file one", str(caught.exception))

    def test_the_permission_decision_has_no_route_for_confidence(self) -> None:
        self.assertIs(AuthorityPolicyGraph.uses_confidence, False)
        self.assertIs(AuthorityPolicyGraph.priority_is_scalar, False)
        governed = S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value)
        inferred = S.authority_ref(AuthorityLevel.MODEL_INFERRED.value)
        allowed = GRAPH.evaluate(
            actor=governed,
            action=OverrideAction.RELAX.value,
            rule_class="brand.logo",
            semantic_path=S.LOGO,
        )
        denied = GRAPH.evaluate(
            actor=inferred,
            action=OverrideAction.RELAX.value,
            rule_class="brand.logo",
            semantic_path=S.LOGO,
        )
        self.assertTrue(allowed.may)
        self.assertFalse(denied.may)
        self.assertTrue(denied.requires_human)
        statement = S.statement("st.confident", S.LOGO, confidence=0.99)
        self.assertEqual(statement.confidence, 0.99)
        unchanged = GRAPH.evaluate(
            actor=inferred,
            action=OverrideAction.RELAX.value,
            rule_class="brand.logo",
            semantic_path=S.LOGO,
        )
        self.assertEqual(unchanged.decision_digest, denied.decision_digest)

    def test_escalation_is_not_a_resolution_and_leaves_the_work_blocked(self) -> None:
        conflict = contradiction()
        escalated = escalate_conflict(
            conflict,
            to_state=ConflictResolutionState.BLOCKED_UNOVERRIDABLE.value,
            rationale="no class in this graph may reach the mark rule; it goes to the owner",
        )
        self.assertEqual(
            escalated.resolution_state, ConflictResolutionState.BLOCKED_UNOVERRIDABLE.value
        )
        self.assertIsNone(escalated.resolution)
        self.assertTrue(escalated.open)
        self.assertIs(escalated.winner_chosen_by_recency, False)
        with self.assertRaises(ConflictBlockedError):
            escalated.require_resolved("release")
        with self.assertRaises(ConflictBlockedError):
            escalate_conflict(
                conflict,
                to_state=ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY.value,
                rationale="an escalation that closes the question is a resolution in disguise",
            )


class ResolutionNeedsGrounds(unittest.TestCase):
    """§13's exits: every closing move names the evidence that paid for it."""

    def test_a_blocking_conflict_cannot_close_on_an_override_without_a_receipt(self) -> None:
        conflict = contradiction()
        with self.assertRaises(OverrideRefusedError) as caught:
            resolve_conflict(
                conflict,
                state=ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE.value,
                decided_by=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
                rationale="we agreed to soften it",
                recorded_in_revision=S.revision_ref("rev.8"),
                graph=GRAPH,
            )
        self.assertIn("receipt", str(caught.exception))

    def test_a_policy_shaped_resolution_must_pin_the_graph_it_used(self) -> None:
        conflict = contradiction()
        with self.assertRaises(AuthorityError) as caught:
            resolve_conflict(
                conflict,
                state=ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY.value,
                decided_by=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                rationale="brand policy keeps the mark requirement",
                recorded_in_revision=S.revision_ref("rev.8"),
            )
        self.assertIn("policy graph", str(caught.exception))

    def test_compatibility_is_not_an_exit_for_a_direct_contradiction(self) -> None:
        conflict = contradiction()
        self.assertNotIn(
            ConflictResolutionState.RESOLVED_BY_COMPATIBILITY, conflict.admissible_resolutions
        )
        with self.assertRaises(ConflictBlockedError) as caught:
            resolve_conflict(
                conflict,
                state=ConflictResolutionState.RESOLVED_BY_COMPATIBILITY.value,
                decided_by=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
                rationale="both readings are satisfiable, honestly",
                recorded_in_revision=S.revision_ref("rev.8"),
            )
        self.assertIn("cannot be closed", str(caught.exception))

    def test_a_resolution_recorded_by_an_agent_is_refused(self) -> None:
        conflict = contradiction()
        for level in (
            AuthorityLevel.MODEL_INFERRED.value,
            AuthorityLevel.PROJECT_RECORD.value,
            AuthorityLevel.TEAM_ASSERTED.value,
        ):
            with self.subTest(level=level):
                with self.assertRaises(AuthorityError):
                    resolve_conflict(
                        conflict,
                        state=ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY.value,
                        decided_by=S.authority_ref(level),
                        rationale="the reading was arrived at carefully",
                        recorded_in_revision=S.revision_ref("rev.8"),
                        graph=GRAPH,
                    )

    def test_resolving_under_a_moved_policy_is_refused(self) -> None:
        conflict = contradiction()
        self.assertIsNotNone(conflict.graph_ref)
        with self.assertRaises(StaleSemanticError) as caught:
            resolve_conflict(
                conflict,
                state=ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY.value,
                decided_by=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                rationale="policy says the mark stays, under the policy of a different graph",
                recorded_in_revision=S.revision_ref("rev.8"),
                graph=S.authority_graph(graph_id="authority.moved"),
            )
        self.assertIn("re-detect", str(caught.exception))

    def test_a_closed_conflict_is_superseded_rather_than_re_decided(self) -> None:
        closed = resolved_contradiction()
        self.assertTrue(closed.resolved)
        with self.assertRaises(ConflictBlockedError):
            resolve_conflict(
                closed,
                state=ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY.value,
                decided_by=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
                rationale="a second verdict over the same disagreement",
                recorded_in_revision=S.revision_ref("rev.10"),
                graph=GRAPH,
            )
        with self.assertRaises(ConflictBlockedError):
            escalate_conflict(
                closed,
                to_state=ConflictResolutionState.NEEDS_HUMAN_DECISION.value,
                rationale="reopening a closed record by relabelling it",
            )

    def test_an_explicit_override_resolution_names_its_receipt_and_a_later_revision(self) -> None:
        before = contradiction()
        receipt = S.receipt(graph=GRAPH)
        after = resolved_contradiction(receipt=receipt)
        self.assertTrue(after.resolved)
        self.assertEqual(
            after.resolution_state, ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE.value
        )
        self.assertIsNotNone(after.resolution)
        self.assertEqual(after.resolution.receipt_ref.text, receipt.receipt_ref.text)
        self.assertEqual(after.resolution.receipt_ref.kind, RefKind.RECEIPT.value)
        self.assertEqual(after.resolution.recorded_in_revision.ref_id, "rev.9")
        self.assertNotEqual(
            after.resolution.recorded_in_revision.ref_id,
            before.detected_in_revision.ref_id,
        )
        self.assertIs(after.deletes_a_rule, False)
        self.assertIs(after.resolution.deletes_a_rule, False)
        self.assertEqual(after.parties, before.parties)
        self.assertEqual(receipt.deletes_original_rule, False)
        self.assertEqual(receipt.recorded_in_revision.ref_id, "rev.8")

    def test_a_scope_split_resolution_keeps_both_rules_in_force(self) -> None:
        conflict = contradiction()
        left, right = conflict.parties
        split = ScopeSplitProposal(
            split_id="split.mark",
            branches=(
                SplitBranch(
                    branch_id="branch.broadcast",
                    scope=ConstraintScope(subject_paths=(S.LOGO,), modalities=("IMAGE",)),
                    party_refs=(left,),
                ),
                SplitBranch(
                    branch_id="branch.social",
                    scope=ConstraintScope(subject_paths=(S.LOGO,), modalities=("AUDIO",)),
                    party_refs=(right,),
                ),
            ),
            rationale="each reading keeps force in one channel, so neither rule is deleted",
        )
        self.assertFalse(split.deletes_either_rule)
        resolved = resolve_conflict(
            conflict,
            state=ConflictResolutionState.RESOLVED_BY_SCOPE_SPLIT.value,
            decided_by=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
            rationale=split.rationale or "",
            recorded_in_revision=S.revision_ref("rev.8"),
            scope_split=split,
        )
        self.assertEqual(resolved.parties, conflict.parties)
        self.assertTrue(ConflictResolutionState.RESOLVED_BY_SCOPE_SPLIT.keeps_both_rules)
        self.assertIs(resolved.deletes_a_rule, False)
        with self.assertRaises(SchemaValidationError) as empty_branch:
            SplitBranch(
                branch_id="branch.empty",
                scope=ConstraintScope(subject_paths=(S.TONE,), modalities=("IMAGE",)),
            )
        self.assertIn("needs at least", str(empty_branch.exception))
        with self.assertRaises(ScopeError) as double_counted:
            ScopeSplitProposal(
                split_id="split.overlap",
                branches=(
                    SplitBranch(
                        branch_id="branch.first",
                        scope=ConstraintScope(subject_paths=(S.LOGO,), modalities=("IMAGE",)),
                        party_refs=(left, right),
                    ),
                    SplitBranch(
                        branch_id="branch.second",
                        scope=ConstraintScope(subject_paths=(S.TONE,), modalities=("IMAGE",)),
                        party_refs=(right,),
                    ),
                ),
                rationale="one rule filed in two regions, which is two rules reading one brief",
            )
        self.assertIn("in more than one branch", str(double_counted.exception))
        self.assertIn(right.ref_id, str(double_counted.exception))


class WeakeningIsAuthorityGated(unittest.TestCase):
    """Invariants 31, 32 and 35, proofs 7, 8 and 12."""

    def relax(
        self,
        actor: Any,
        *,
        rule_class: str = "brand.logo",
        ident: str = "ovr.iris",
        **over: Any,
    ) -> Any:
        over.setdefault("graph", GRAPH)
        return S.receipt(actor=actor, rule_class=rule_class, ident=ident, **over)

    def test_an_inferred_actor_cannot_relax_a_governed_rule(self) -> None:
        with self.assertRaises(AuthorityError) as caught:
            self.relax(S.authority_ref(AuthorityLevel.MODEL_INFERRED.value))
        self.assertIn("RELAX refused", str(caught.exception))
        self.assertIn("MODEL_INFERRED", str(caught.exception))

    def test_a_project_record_cannot_relax_either(self) -> None:
        with self.assertRaises(AuthorityError):
            self.relax(S.authority_ref(AuthorityLevel.PROJECT_RECORD.value))

    def test_a_governed_policy_may_relax_only_the_rule_it_answers_for(self) -> None:
        governed = S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value)
        self.assertEqual(self.relax(governed).rule_class, "brand.logo")
        with self.assertRaises(AuthorityError) as caught:
            self.relax(governed, rule_class="brand.creative", ident="ovr.notmine")
        self.assertIn("edge", str(caught.exception))

    def test_disable_needs_the_human_owner_and_an_admitted_human_revision(self) -> None:
        human = S.authority_ref(AuthorityLevel.HUMAN_OWNER.value)
        with self.assertRaises(AuthorityError) as caught:
            self.relax(
                S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                action=OverrideAction.DISABLE.value,
                human_decision=S.revision_ref("rev.8"),
                ident="ovr.disable.policy",
            )
        self.assertIn("DISABLE", str(caught.exception))
        without_decision = GRAPH.evaluate(
            actor=human,
            action=OverrideAction.RELAX.value,
            rule_class="brand.creative",
            semantic_path=S.LOGO,
        )
        self.assertFalse(without_decision.may)
        self.assertTrue(without_decision.requires_human)
        self.assertIn("human-only", without_decision.reason)
        granted = S.receipt(
            graph=GRAPH,
            action=OverrideAction.DISABLE.value,
            actor=human,
            human_decision=S.revision_ref("rev.8"),
            ident="ovr.disable.owner",
        )
        self.assertEqual(granted.action, OverrideAction.DISABLE.value)
        self.assertEqual(granted.human_decision.ref_id, "rev.8")
        self.assertEqual(granted.actor.level, AuthorityLevel.HUMAN_OWNER)
        with self.assertRaises(AuthorityError) as gate:
            self.relax(
                human,
                rule_class="brand.creative",
                ident="ovr.humanonly",
            )
        self.assertIn("human-only", str(gate.exception))

    def test_a_relaxation_must_invalidate_every_mandatory_compiled_layer(self) -> None:
        hard, before, after = S.override_pair()
        with self.assertRaises(OverrideRefusedError) as caught:
            issue_override(
                override_id="ovr.partial",
                action=OverrideAction.RELAX.value,
                rule_class="brand.logo",
                semantic_path=S.LOGO,
                target_refs=(hard.constraint_ref,),
                actor=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                graph=GRAPH,
                reason="softened for the region, and only the fingerprints were told",
                previous_state=before,
                effective_state=after,
                recorded_in_revision=S.revision_ref("rev.8"),
                expires_after_revision=7,
                invalidation=(
                    InvalidationTarget.INTENT_FINGERPRINT.value,
                    InvalidationTarget.CONSTRAINT_FINGERPRINT.value,
                ),
            )
        self.assertIn("CONTRACT_SET", str(caught.exception))
        self.assertIn("EXECUTION_BUNDLE", str(caught.exception))

    def test_a_temporary_experiment_without_a_lease_is_refused(self) -> None:
        with self.assertRaises(OverrideRefusedError) as caught:
            S.receipt(
                graph=GRAPH,
                action=OverrideAction.TEMPORARY_EXPERIMENT.value,
                ident="ovr.endless",
            )
        self.assertIn("lease", str(caught.exception))

    def test_an_action_label_the_recorded_states_contradict_is_refused(self) -> None:
        hard, before, after = S.override_pair()
        policy = S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value)
        with self.assertRaises(OverrideRefusedError) as no_change:
            issue_override(
                override_id="ovr.noop",
                action=OverrideAction.RELAX.value,
                rule_class="brand.logo",
                semantic_path=S.LOGO,
                target_refs=(hard.constraint_ref,),
                actor=policy,
                graph=GRAPH,
                reason="a receipt for a decision nobody took",
                previous_state=before,
                effective_state=before,
                recorded_in_revision=S.revision_ref("rev.8"),
                invalidation=S.RELAXATION_TARGETS,
            )
        self.assertIn("changes nothing", str(no_change.exception))
        with self.assertRaises(OverrideRefusedError) as mislabelled:
            issue_override(
                override_id="ovr.mislabelled",
                action=OverrideAction.STRENGTHEN.value,
                rule_class="brand.logo",
                semantic_path=S.LOGO,
                target_refs=(hard.constraint_ref,),
                actor=policy,
                graph=GRAPH,
                reason="a softening filed under the safe-sounding label",
                previous_state=before,
                effective_state=after,
                recorded_in_revision=S.revision_ref("rev.8"),
            )
        self.assertIn("cannot describe movement", str(mislabelled.exception))

    def test_an_agent_may_propose_but_cannot_self_approve(self) -> None:
        hard, before, after = S.override_pair()
        proposal = propose_override(
            proposal_id="prop.mark",
            action=OverrideAction.RELAX.value,
            rule_class="brand.logo",
            semantic_path=S.LOGO,
            target_refs=(hard.constraint_ref,),
            proposed_by=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
            rationale="the mark reads better without the rule in this region",
            graph=GRAPH,
            previous_state=before,
            invalidation=S.RELAXATION_TARGETS,
        )
        self.assertTrue(proposal.requires_human)
        self.assertIs(OverrideProposal.approved, False)
        self.assertIs(OverrideProposal.carries_authority, False)
        self.assertIs(OverrideProposal.effective, False)
        self.assertIs(proposal.approved, False)
        self.assertFalse(proposal.preview(GRAPH).may)
        with self.assertRaises(AuthorityError) as self_approved:
            authorize_proposal(
                proposal,
                actor=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
                graph=GRAPH,
                recorded_in_revision=S.revision_ref("rev.9"),
                effective_state=after,
            )
        self.assertIn("human decision ref", str(self_approved.exception))
        with self.assertRaises(AuthorityError) as still_gated:
            authorize_proposal(
                proposal,
                actor=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                graph=GRAPH,
                recorded_in_revision=S.revision_ref("rev.9"),
                effective_state=after,
            )
        self.assertIn("human decision ref", str(still_gated.exception))
        honoured = authorize_proposal(
            proposal,
            actor=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
            graph=GRAPH,
            recorded_in_revision=S.revision_ref("rev.9"),
            effective_state=after,
            human_decision=S.revision_ref("rev.9"),
        )
        self.assertIsInstance(honoured.action, str)
        self.assertEqual(honoured.actor.level, AuthorityLevel.HUMAN_OWNER)
        self.assertNotEqual(honoured.actor.digest(), proposal.proposed_by.digest())
        self.assertIs(proposal.approved, False)
        self.assertTrue(proposal.requires_human)

    def test_a_proposal_cannot_claim_it_needs_no_human(self) -> None:
        hard, _before, _after = S.override_pair()
        with self.assertRaises(AuthorityError) as caught:
            OverrideProposal(
                proposal_id="prop.selfcleared",
                action=OverrideAction.RELAX.value,
                rule_class="brand.logo",
                semantic_path=S.LOGO,
                target_refs=(hard.constraint_ref,),
                proposed_by=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
                rationale="the model is confident, so nobody has to be asked",
                requires_human=False,
            )
        self.assertIn("human-free", str(caught.exception))


class ReservedBoundariesAreOutOfRange(unittest.TestCase):
    """Invariant 31, proof 7: a boundary is not the top of the ladder."""

    def test_the_six_canonical_boundaries_are_reserved_without_a_graph(self) -> None:
        for rule_class in RESERVED_CLASSES:
            with self.subTest(rule_class=rule_class):
                self.assertTrue(is_reserved_rule_class(rule_class))
                self.assertTrue(is_reserved_rule_class(rule_class, ()))

    def test_default_boundaries_are_non_overridable_and_permanent(self) -> None:
        boundaries = default_reserved_boundaries(evidence_refs=(S.policy_ref(),))
        self.assertEqual(len(boundaries), 6)
        self.assertEqual(
            sorted(item.boundary_id for item in boundaries),
            [
                "reserved.m01_evaluator_authority",
                "reserved.m01_fatal_gate",
                "reserved.m02_immutable_history",
                "reserved.platform_legal",
                "reserved.project_governance",
                "reserved.rights_security",
            ],
        )
        for boundary in boundaries:
            self.assertTrue(boundary.non_overridable)
            self.assertTrue(boundary.kind_enum.permanent)
            self.assertTrue(boundary.evidence_refs)

    def test_no_actor_can_disable_a_reserved_rule_class(self) -> None:
        for actor in (
            S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
            S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
        ):
            for rule_class in RESERVED_CLASSES:
                with self.subTest(actor=actor.authority, rule_class=rule_class):
                    decision = GRAPH.evaluate(
                        actor=actor,
                        action=OverrideAction.DISABLE.value,
                        rule_class=rule_class,
                        human_decision=S.revision_ref("rev.8"),
                    )
                    self.assertFalse(decision.may)
                    self.assertIsNotNone(decision.reserved_by)
                    with self.assertRaises(OverrideRefusedError):
                        GRAPH.authorize(
                            actor=actor,
                            action=OverrideAction.DISABLE.value,
                            rule_class=rule_class,
                            human_decision=S.revision_ref("rev.8"),
                        )
                    with self.assertRaises(OverrideRefusedError):
                        S.receipt(
                            graph=GRAPH,
                            actor=actor,
                            rule_class=rule_class,
                            action=OverrideAction.DISABLE.value,
                            human_decision=S.revision_ref("rev.8"),
                            ident=f"ovr.reserved.{rule_class}",
                        )

    def test_an_override_may_not_target_a_reserved_policy_directly(self) -> None:
        hard, before, after = S.override_pair()
        reserved_policy = S.ref(RefKind.POLICY.value, "rights.security", "1.0.0")
        with self.assertRaises(OverrideRefusedError) as caught:
            issue_override(
                override_id="ovr.bypass",
                action=OverrideAction.RELAX.value,
                rule_class="brand.logo",
                semantic_path=S.LOGO,
                target_refs=(reserved_policy,),
                actor=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
                human_decision=S.revision_ref("rev.8"),
                graph=GRAPH,
                reason="relaxing the rights boundary itself, quietly",
                previous_state=before,
                effective_state=after,
                recorded_in_revision=S.revision_ref("rev.8"),
                invalidation=S.RELAXATION_TARGETS,
            )
        self.assertIn("reserved policy", str(caught.exception))


class ExpiredOverridesStopSteeringWork(unittest.TestCase):
    """Invariant 33, proof 9: a lapsed permission may not keep a compiled state alive."""

    def test_expiry_is_counted_in_admitted_revisions(self) -> None:
        receipt = S.receipt(graph=GRAPH, expires=7)
        self.assertFalse(receipt.expired_at(7))
        self.assertTrue(receipt.expired_at(8))
        self.assertTrue(receipt.is_temporary)
        receipt.require_live(7, "compile the contract set")
        with self.assertRaises(StaleSemanticError) as caught:
            receipt.require_live(8, "compile the contract set")
        message = str(caught.exception)
        self.assertIn("ovr.iris", message)
        self.assertIn(InvalidationTarget.CONTRACT_SET.value, message)
        self.assertIn(InvalidationTarget.EXECUTION_BUNDLE.value, message)

    def test_the_ledger_reports_live_and_expired_receipts_separately(self) -> None:
        receipt = S.receipt(graph=GRAPH, expires=7)
        book = S.ledger([receipt], [S.debt(override_ids=(receipt.override_id,))])
        self.assertEqual([item.override_id for item in book.live_at(7)], ["ovr.iris"])
        self.assertEqual([item.override_id for item in book.expired_at(8)], ["ovr.iris"])
        self.assertEqual(book.for_path(S.LOGO), (receipt,))
        self.assertEqual(book.for_path(S.TONE), ())
        book.require_no_expired_reliance(7, "release")
        with self.assertRaises(StaleSemanticError) as caught:
            book.require_no_expired_reliance(8, "release")
        self.assertIn("ovr.iris", str(caught.exception))
        self.assertEqual(
            [item.debt_id for item in book.release_blocking_debts()], ["debt.iris"]
        )

    def test_the_release_gate_reads_the_weakening_that_may_not_ship(self) -> None:
        """Documents what ``relaxing_at`` actually collects: liveness plus ``may_release``.

        Recorded as behaviour rather than as intent: a permanent RELAX has
        ``action_enum.may_release`` true and so is absent from the list, while a temporary
        experiment is present. The relaxation is not lost from the release picture —
        ``expired_at`` and the readiness report's EXPIRED_OVERRIDE family both still name it —
        but a caller that treated ``relaxing_at`` as "everything currently relaxed" would read a
        narrower list than the ledger holds.
        """

        relaxed = S.receipt(graph=GRAPH, expires=7, ident="ovr.relax")
        hard, before, after = S.override_pair()
        experiment = issue_override(
            override_id="ovr.experiment",
            action=OverrideAction.TEMPORARY_EXPERIMENT.value,
            rule_class="brand.logo",
            semantic_path=S.LOGO,
            target_refs=(hard.constraint_ref,),
            actor=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
            graph=GRAPH,
            reason="two revisions without the mark rule, under a lease that ends",
            previous_state=before,
            effective_state=after,
            recorded_in_revision=S.revision_ref("rev.8"),
            issued_at_revision=7,
            expires_after_revision=8,
            lease_id="lease.experiment",
            invalidation=S.RELAXATION_TARGETS,
        )
        self.assertTrue(relaxed.weakens)
        self.assertTrue(relaxed.action_enum.may_release)
        self.assertTrue(experiment.weakens)
        self.assertFalse(experiment.action_enum.may_release)
        book = OverrideLedger(
            ledger_id="ledger.iris",
            brief_ref=S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
            revision_ref=S.revision_ref(),
            receipts=(relaxed, experiment),
            leases=(
                TemporaryOverrideLease(
                    lease_id="lease.experiment",
                    override_ids=("ovr.experiment",),
                    issued_at_revision=7,
                    expires_after_revision=8,
                    scope_paths=(S.LOGO,),
                ),
            ),
        )
        self.assertEqual([item.override_id for item in book.relaxing_at(7)], ["ovr.experiment"])
        self.assertEqual([item.override_id for item in book.relaxing_at(9)], [])
        self.assertEqual(
            sorted(item.override_id for item in book.expired_at(9)),
            ["ovr.experiment", "ovr.relax"],
        )

    def test_a_lease_must_expire_and_never_renews_itself(self) -> None:
        lease = TemporaryOverrideLease(
            lease_id="lease.mark",
            override_ids=("ovr.iris",),
            expires_after_revision=7,
            issued_at_revision=6,
            scope_paths=(S.LOGO,),
        )
        self.assertTrue(lease.live_at(7))
        self.assertTrue(lease.expired_at(8))
        self.assertIs(TemporaryOverrideLease.renews_automatically, False)
        lease.require_live(7, "carry the experiment forward")
        with self.assertRaises(StaleSemanticError):
            lease.require_live(8, "carry the experiment forward")
        with self.assertRaises(OverrideRefusedError):
            lease.require_not_released("release the candidate")
        with self.assertRaises(OverrideRefusedError) as endless:
            TemporaryOverrideLease(lease_id="lease.endless", override_ids=("ovr.iris",))
        self.assertIn("no expiry", str(endless.exception))

    def test_a_receipt_re_checking_against_a_moved_policy_reports_staleness(self) -> None:
        receipt = S.receipt(graph=GRAPH)
        self.assertIs(receipt.verify_against(GRAPH), receipt)
        moved = MOVED_GRAPH
        with self.assertRaises(StaleSemanticError):
            receipt.verify_against(moved)
        self.assertEqual(S.ledger([receipt]).verify(moved), ("ovr.iris",))
        self.assertEqual(S.ledger([receipt]).verify(GRAPH), ())
        self.assertEqual(S.ledger([receipt]).verify(GRAPH, revision_ordinal=9), ("ovr.iris",))
        with self.assertRaises(StaleSemanticError):
            S.ledger([receipt]).require_no_expired_reliance(9, "release the candidate")

    def test_a_receipt_cannot_be_read_as_authority_for_its_own_actor(self) -> None:
        receipt = S.receipt(graph=GRAPH)
        self.assertIs(receipt.grants_self_authority, False)
        self.assertIs(receipt.overrides_m01_quality, False)
        self.assertIs(receipt.overrides_m02_history, False)
        self.assertIs(receipt.deletes_original_rule, False)
        self.assertEqual(
            sorted(receipt.invalidation), sorted(S.RELAXATION_TARGETS)
        )


class OverrideDebtIsNotQualityDebt(unittest.TestCase):
    """Invariant 34, proof 10: two ledgers, two owners, one conversion that always refuses."""

    def test_the_two_debt_types_are_different_types(self) -> None:
        debt = S.debt()
        self.assertIsInstance(debt, OverrideDebt)
        self.assertNotIsInstance(debt, QualityDebt)
        self.assertIsNot(type(debt), QualityDebt)
        self.assertIs(debt.is_quality_debt, False)
        self.assertEqual(debt.owner_module, "M03")
        self.assertTrue(issubclass(QualityDebt, object))
        self.assertNotEqual(QualityDebt.__module__, OverrideDebt.__module__)

    def test_the_conversion_method_refuses_rather_than_adapting(self) -> None:
        debt = S.debt()
        with self.assertRaises(QualityAuthorityError) as caught:
            debt.as_m01_quality_debt()
        self.assertIn("M01", str(caught.exception))
        self.assertIn(debt.debt_id, str(caught.exception))

    def test_a_debt_may_not_cite_m01_state_or_non_receipts(self) -> None:
        with self.assertRaises(QualityAuthorityError) as borrowed:
            OverrideDebt(
                debt_id="debt.borrowed",
                kind="TEMPORARY_BRAND_EXCEPTION",
                override_refs=(S.ref(RefKind.M01_CONTRACT.value, "contract.quality"),),
                opened_at_revision=5,
                expires_after_revision=9,
            )
        self.assertIn("M01", str(borrowed.exception))
        with self.assertRaises(RefError):
            OverrideDebt(
                debt_id="debt.wish",
                kind="TEMPORARY_BRAND_EXCEPTION",
                override_refs=(S.ref(RefKind.CONSTRAINT.value, "cn.logo"),),
                opened_at_revision=5,
                expires_after_revision=9,
            )

    def test_an_open_debt_blocks_release_and_closing_writes_a_new_record(self) -> None:
        opened = S.debt()
        closed = opened.close(
            closed_by=S.revision_ref("rev.9"), reason="the exception was folded into brand policy"
        )
        self.assertTrue(opened.blocks_release_now)
        self.assertTrue(opened.is_open)
        self.assertFalse(closed.blocks_release_now)
        self.assertFalse(closed.is_open)
        self.assertEqual(closed.closed_by.ref_id, "rev.9")
        self.assertEqual(opened.closed_by, None)
        self.assertNotEqual(opened.digest(), closed.digest())
        self.assertFalse(S.debt(closed=True).blocks_release_now)


class ConflictSliceStaysLocal(unittest.TestCase):
    """Invariant 30 and proofs 20, 21: one conflict, one locality, one re-checkable fingerprint."""

    def slice_for(self, conflict: Any, paths: tuple = (S.LOGO,)) -> Any:
        return MinimumSufficientConflictSlice(
            slice_id=f"cslice.{conflict.conflict_id}",
            conflict_ref=conflict.conflict_ref,
            semantic_slice=S.slice_for(
                MODEL, None, paths, request_id="req.conflict", purpose="RESOLVE_CONFLICT"
            ),
        )

    def test_a_conflict_is_decidable_from_its_own_locality(self) -> None:
        conflict = contradiction()
        item = self.slice_for(conflict)
        self.assertEqual(item.paths, (S.LOGO,))
        self.assertIs(item.require_local(conflict), item)
        self.assertIs(MinimumSufficientConflictSlice.includes_project_history, False)
        self.assertIs(MinimumSufficientConflictSlice.carries_full_brief, False)
        self.assertIs(item.includes_project_history, False)
        self.assertTrue(item.touches(S.LOGO))
        self.assertFalse(item.touches(S.TONE))

    def test_a_slice_carrying_an_unrelated_path_is_refused(self) -> None:
        conflict = contradiction()
        wider = self.slice_for(conflict, (S.LOGO, S.TONE))
        with self.assertRaises(ScopeError) as caught:
            wider.require_local(conflict)
        self.assertIn("is not about", str(caught.exception))

    def test_a_slice_cut_for_another_purpose_cannot_decide_a_conflict(self) -> None:
        conflict = contradiction()
        with self.assertRaises(ScopeError) as caught:
            MinimumSufficientConflictSlice(
                slice_id="cslice.wrong",
                conflict_ref=conflict.conflict_ref,
                semantic_slice=S.slice_for(
                    MODEL, None, (S.LOGO,), request_id="req.audit", purpose="AUDIT"
                ),
            )
        self.assertIn("was cut for AUDIT", str(caught.exception))

    def test_a_slice_checked_against_the_wrong_conflict_is_refused(self) -> None:
        ours = contradiction()
        theirs = contradiction(ident="other")
        with self.assertRaises(RefError) as caught:
            self.slice_for(ours).require_local(theirs)
        self.assertIn("being checked against", str(caught.exception))

    def test_policy_edges_must_speak_to_the_disagreement(self) -> None:
        conflict = contradiction()
        edge = next(item for item in GRAPH.edges if item.edge_id == "owner-over-brand")
        item = MinimumSufficientConflictSlice(
            slice_id="cslice.edges",
            conflict_ref=conflict.conflict_ref,
            semantic_slice=S.slice_for(
                MODEL, None, (S.LOGO,), request_id="req.edges", purpose="RESOLVE_CONFLICT"
            ),
            policy_edges=(edge,),
        )
        self.assertEqual(item.edge_ids, ("owner-over-brand",))
        self.assertIs(item.require_edges_relevant(conflict, GRAPH), item)
        scenery = contradiction(ident="audio", rule_class="brand.audio")
        with self.assertRaises(ScopeError) as caught:
            MinimumSufficientConflictSlice(
                slice_id="cslice.scenery",
                conflict_ref=scenery.conflict_ref,
                semantic_slice=S.slice_for(
                    MODEL, None, (S.LOGO,), request_id="req.scenery", purpose="RESOLVE_CONFLICT"
                ),
                policy_edges=(edge,),
            ).require_edges_relevant(scenery, GRAPH)
        self.assertIn("policy scenery", str(caught.exception))

    def test_a_resolution_fingerprint_is_current_until_the_policy_moves(self) -> None:
        conflict = contradiction()
        fingerprint = conflict.resolution_fingerprint(fingerprint_id="fpr.mark")
        self.assertFalse(fingerprint.decided)
        self.assertTrue(fingerprint.describes(conflict))
        self.assertEqual(fingerprint.stale_inputs(conflict, GRAPH), ())
        self.assertIs(fingerprint.require_current(conflict, GRAPH), fingerprint)
        with self.assertRaises(StaleSemanticError) as caught:
            fingerprint.require_current(conflict, S.authority_graph(graph_id="authority.moved"))
        self.assertIn("authority_policy", str(caught.exception))

    def test_a_resolution_fingerprint_names_the_resolution_that_arrived_later(self) -> None:
        conflict = contradiction()
        fingerprint = conflict.resolution_fingerprint(fingerprint_id="fpr.mark.later")
        resolved = resolved_contradiction()
        self.assertTrue(fingerprint.describes(resolved))
        drift = fingerprint.stale_inputs(resolved, GRAPH)
        self.assertIn("resolution", drift)
        self.assertNotIn("conflict", drift)
        with self.assertRaises(StaleSemanticError) as caught:
            fingerprint.require_current(resolved, GRAPH, action="reuse the verdict")
        self.assertIn("re-derived", str(caught.exception))
        fresh = resolved.resolution_fingerprint(fingerprint_id="fpr.mark.decided")
        self.assertTrue(fresh.decided)
        self.assertEqual(fresh.stale_inputs(resolved, GRAPH), ())
        self.assertEqual(fresh.receipt_refs, (resolved.resolution.receipt_ref.text,))

    def test_a_resolved_conflict_is_only_current_under_the_policy_it_used(self) -> None:
        resolved = resolved_contradiction()
        self.assertIs(resolved.require_current(GRAPH, "release"), resolved)
        with self.assertRaises(StaleSemanticError):
            resolved.require_current(MOVED_GRAPH, "release")
        with self.assertRaises(StaleSemanticError):
            resolved.resolution.require_current_policy(MOVED_GRAPH)


if __name__ == "__main__":
    unittest.main()
