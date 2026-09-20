from __future__ import annotations

import dataclasses
from unittest import TestCase

from iris_quality.contracts import PromotionRule, QualityClass
from iris_quality.decision import DecisionEngine, QualityDecision, merge_assessments
from iris_quality.defects import Defect, DefectSeverity
from iris_quality.dimensions import GateState, UncertaintyState
from iris_quality.errors import (
    EvaluationInputError,
    PromotionBlockedError,
    SchemaValidationError,
)
from iris_quality.evidence import EvidenceRef
from iris_quality.judging import JudgeResult, SubjectRef
from iris_quality.versions import ComponentVersion
from iris_quality.zones import SemanticZone
from tests.m01_kernel_support import (
    DIMENSIONS,
    EVALUATOR,
    JUDGE,
    SUBJECT,
    assessment,
    authorized,
    contract,
    covered_assessments,
    defect,
    debt,
    evidence,
    judge_result,
    ladder_rules,
)

DIGEST = "d" * 64


class DeterministicRecordTests(TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.target = contract()
        self.assessments = covered_assessments()

    def test_identical_inputs_produce_identical_records(self) -> None:
        first = self.engine.evaluate(self.target, SUBJECT, assessments=self.assessments)
        second = self.engine.evaluate(self.target, SUBJECT, assessments=self.assessments)
        self.assertEqual(first.content_sha256, second.content_sha256)
        self.assertEqual(first.to_payload(), second.to_payload())

    def test_a_different_asset_produces_a_different_record(self) -> None:
        baseline = self.engine.evaluate(self.target, SUBJECT, assessments=self.assessments)
        other = self.engine.evaluate(
            self.target,
            SubjectRef("asset.other", DIGEST),
            assessments=self.assessments,
        )
        self.assertNotEqual(baseline.content_sha256, other.content_sha256)

    def test_evidence_ordering_does_not_change_the_record(self) -> None:
        unordered = tuple(
            dataclasses.replace(item, evidence=tuple(reversed(item.evidence)))
            for item in covered_assessments(evidence_count=2)
        )
        ordered = covered_assessments(evidence_count=2)
        first = self.engine.evaluate(self.target, SUBJECT, assessments=unordered)
        second = self.engine.evaluate(self.target, SUBJECT, assessments=ordered)
        self.assertEqual(first.content_sha256, second.content_sha256)

    def test_the_engine_records_the_version_that_decided(self) -> None:
        decision = self.engine.evaluate(self.target, SUBJECT, assessments=self.assessments)
        self.assertEqual(decision.engine.identifier, "m01-decision-engine")
        self.assertEqual(decision.contract_reference, self.target.reference)


class FatalFirewallTests(TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.target = contract()
        self.assessments = covered_assessments()

    def test_fatal_defect_rejects_regardless_of_perfect_measurements(self) -> None:
        decision = self.engine.evaluate(
            self.target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.fatal", "subject-absent", DefectSeverity.FATAL),),
        )
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        self.assertEqual(decision.outcome.value, "REJECTED")
        self.assertIn("fatal_defect_firewall", decision.blocker_codes)

    def test_contract_severity_authority_beats_a_soft_report(self) -> None:
        decision = self.engine.evaluate(
            self.target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.fatal", "subject-absent", DefectSeverity.OBSERVATION),),
        )
        finding = decision.findings[0]
        self.assertIs(finding.contract_severity, DefectSeverity.FATAL)
        self.assertIs(finding.reported_severity, DefectSeverity.OBSERVATION)
        self.assertIs(finding.effective_severity, DefectSeverity.FATAL)
        self.assertEqual(decision.outcome.value, "REJECTED")

    def test_a_fatal_finding_cannot_be_bought_off_with_debt(self) -> None:
        decision = self.engine.evaluate(
            self.target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.fatal", "subject-absent", DefectSeverity.FATAL),),
            debts=(debt("d.fatal", "subject-absent", DefectSeverity.FATAL),),
        )
        self.assertFalse(decision.findings[0].deferred)
        self.assertEqual(decision.accepted_debt_ids, ())
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)

    def test_zone_policy_can_escalate_a_major_class_to_fatal(self) -> None:
        zone = SemanticZone(
            "zone.eyes",
            "Eyes",
            ("geometry-integrity",),
            {"geometry-break": DefectSeverity.FATAL},
        )
        target = contract(zones=(zone,))
        decision = DecisionEngine().evaluate(
            target,
            SUBJECT,
            assessments=covered_assessments(),
            defects=(
                defect("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity", "zone.eyes"),
            ),
        )
        self.assertIs(decision.findings[0].effective_severity, DefectSeverity.FATAL)
        self.assertEqual(decision.findings[0].zone_ids, ("zone.eyes",))
        self.assertEqual(decision.outcome.value, "REJECTED")


class SeverityPolicyTests(TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.assessments = covered_assessments()

    def test_major_defects_bar_master_but_not_review(self) -> None:
        target = contract(output_class=QualityClass.MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.major", "geometry-break", DefectSeverity.MAJOR),),
        )
        self.assertIs(decision.awarded_class, QualityClass.REVIEW)
        self.assertIn("major_defect_without_debt", decision.blocker_codes)

    def test_accepted_debt_carries_a_major_defect_to_master(self) -> None:
        target = contract(output_class=QualityClass.MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.major", "geometry-break", DefectSeverity.MAJOR),),
            debts=(debt("d.major"),),
        )
        self.assertIs(decision.awarded_class, QualityClass.MASTER)
        self.assertEqual(decision.outcome.value, "PROMOTED")
        self.assertEqual(decision.accepted_debt_ids, ("debt.d.major@policy-v1",))
        self.assertTrue(decision.findings[0].deferred)

    def test_debt_for_a_different_severity_is_not_accepted(self) -> None:
        target = contract(output_class=QualityClass.MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.major", "geometry-break", DefectSeverity.MAJOR),),
            debts=(debt("d.major", "geometry-break", DefectSeverity.MINOR),),
        )
        self.assertIs(decision.awarded_class, QualityClass.REVIEW)
        self.assertEqual(
            decision.findings[0].debt_note,
            "debt_severity_MINOR_does_not_match_effective_severity_MAJOR",
        )

    def test_minor_defects_only_bar_archival_master(self) -> None:
        target = contract(output_class=QualityClass.ARCHIVAL_MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.minor", "soft-detail", DefectSeverity.MINOR),),
        )
        self.assertIs(decision.awarded_class, QualityClass.MASTER)
        self.assertIn("minor_defect_without_debt", decision.blocker_codes)

    def test_observations_never_block(self) -> None:
        target = contract(output_class=QualityClass.ARCHIVAL_MASTER)
        assessments = covered_assessments(evidence_count=4)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=assessments,
            defects=(
                defect("d.obs", "non-blocking-note", DefectSeverity.OBSERVATION),
                defect("d.obs2", "optional-annotation", DefectSeverity.OBSERVATION),
            ),
        )
        self.assertEqual(decision.outcome.value, "PROMOTED")
        self.assertIs(decision.awarded_class, QualityClass.ARCHIVAL_MASTER)
        self.assertEqual(decision.blockers, ())
        self.assertEqual(
            {item.effective_severity.value for item in decision.findings}, {"OBSERVATION"}
        )

    def test_a_reporter_cannot_dilute_a_declared_class_with_observation(self) -> None:
        target = contract(output_class=QualityClass.ARCHIVAL_MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=covered_assessments(evidence_count=4),
            defects=(defect("d.soft", "soft-detail", DefectSeverity.OBSERVATION),),
        )
        finding = decision.findings[0]
        self.assertIs(finding.reported_severity, DefectSeverity.OBSERVATION)
        self.assertIs(finding.effective_severity, DefectSeverity.MINOR)
        self.assertIs(decision.awarded_class, QualityClass.MASTER)
        self.assertIn("minor_defect_without_debt", decision.blocker_codes)


class UncertaintyBehaviourTests(TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.target = contract()

    def test_missing_assessments_never_fabricate_certainty(self) -> None:
        decision = self.engine.evaluate(self.target, SUBJECT)
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        self.assertEqual(decision.outcome.value, "NOT_PROMOTED")
        for dimension_id in DIMENSIONS:
            state = next(item for item in decision.dimensions if item.dimension_id == dimension_id)
            self.assertEqual(state.gate, GateState.UNVERIFIED.value)
            self.assertEqual(state.uncertainty, UncertaintyState.UNKNOWN.value)
            self.assertEqual(state.evidence_count, 0)
            self.assertEqual(state.evaluated_by, ())
        self.assertIn("insufficient_certainty", decision.blocker_codes)

    def test_explicit_unknown_state_blocks_promotion(self) -> None:
        assessments = tuple(
            assessment(
                dimension_id,
                uncertainty=UncertaintyState.UNKNOWN,
                confidence=None,
                value=None,
                evidence_items=[evidence(f"ev.{dimension_id}", dimension_id)],
            )
            for dimension_id in DIMENSIONS
        )
        decision = self.engine.evaluate(self.target, SUBJECT, assessments=assessments)
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        self.assertFalse(decision.requires_human_review)

    def test_judge_abstention_is_inherited_as_unknown(self) -> None:
        partial = judge_result(
            self.target,
            (assessment("intent-adherence", evidence_items=[evidence("ev.i", "intent-adherence")]),),
        )
        decision = self.engine.evaluate(self.target, SUBJECT, results=(partial,))
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)

    def test_zone_confidence_floor_sends_the_asset_to_human_review(self) -> None:
        zone = SemanticZone(
            "zone.hands", "Hands", ("geometry-integrity",), minimum_confidence=0.95
        )
        target = contract(zones=(zone,))
        decision = self.engine.evaluate(target, SUBJECT, assessments=covered_assessments())
        self.assertTrue(decision.requires_human_review)
        self.assertEqual(decision.outcome.value, "HUMAN_REVIEW")
        self.assertIn("zone_confidence_floor", decision.blocker_codes)

    def test_human_review_dimension_requires_a_recorded_decision(self) -> None:
        target = contract(human_review_dimension_ids=("intent-adherence",))
        blocked = DecisionEngine().evaluate(target, SUBJECT, assessments=covered_assessments())
        self.assertEqual(blocked.outcome.value, "NOT_PROMOTED")
        self.assertIn("human_review_missing_for_dimension", blocked.blocker_codes)

        signed = covered_assessments()
        human = EvidenceRef(
            evidence_id="ev.human",
            kind="HUMAN_DECISION",
            locator="fixtures/human.json",
            content_sha256=DIGEST,
            produced_by=ComponentVersion("review-board", "1.0.0"),
            dimension_id="intent-adherence",
        )
        signed = tuple(
            dataclasses.replace(item, evidence=item.evidence + (human,))
            if item.dimension_id == "intent-adherence"
            else item
            for item in signed
        )
        promoted = DecisionEngine().evaluate(target, SUBJECT, assessments=signed)
        self.assertEqual(promoted.outcome.value, "PROMOTED")

    def test_a_jury_rung_can_demand_a_decision_on_every_dimension(self) -> None:
        rules = tuple(
            dataclasses.replace(rule, requires_human_review=rule.target_class is QualityClass.ARCHIVAL_MASTER)
            for rule in ladder_rules()
        )
        target = contract(
            output_class=QualityClass.ARCHIVAL_MASTER,
            promotion_rules=rules,
        )
        plain = DecisionEngine().evaluate(
            target, SUBJECT, assessments=covered_assessments(evidence_count=2)
        )
        self.assertIs(plain.awarded_class, QualityClass.MASTER)
        self.assertIn("human_review_not_recorded", plain.blocker_codes)


class PromotionLadderTests(TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()

    def test_the_ladder_stops_at_the_first_unmet_rung(self) -> None:
        rules = (
            PromotionRule(QualityClass.PREVIEW, DIMENSIONS, minimum_evidence_count=3),
            PromotionRule(QualityClass.REVIEW, DIMENSIONS, minimum_evidence_count=1),
            PromotionRule(QualityClass.MASTER, DIMENSIONS, minimum_evidence_count=1),
        )
        target = contract(promotion_rules=rules)
        decision = self.engine.evaluate(
            target, SUBJECT, assessments=covered_assessments(evidence_count=1)
        )
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        self.assertTrue(all(item.target_class == "PREVIEW" for item in decision.blockers))

    def test_a_draft_can_never_be_relabelled_master(self) -> None:
        target = contract()
        decision = self.engine.evaluate(target, SUBJECT, assessments=covered_assessments())
        self.assertIs(decision.awarded_class, QualityClass.MASTER)
        degraded = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=tuple(
                assessment(
                    item.dimension_id,
                    gate=GateState.FAIL,
                    evidence_items=list(item.evidence),
                )
                for item in covered_assessments()
            ),
        )
        self.assertIs(degraded.awarded_class, QualityClass.DRAFT)
        with self.assertRaises(PromotionBlockedError):
            degraded.require_promotable()
        self.assertIs(decision.require_promotable(), decision)

    def test_high_scores_cannot_outvote_a_failed_hard_gate(self) -> None:
        rules = ladder_rules(hard_gates=("geometry-integrity",))
        target = contract(promotion_rules=rules)
        assessments = tuple(
            assessment(
                dimension_id,
                gate=GateState.FAIL if dimension_id == "geometry-integrity" else GateState.PASS,
                value=0.99,
                confidence=0.99,
                evidence_items=[evidence(f"ev.{dimension_id}", dimension_id)],
            )
            for dimension_id in DIMENSIONS
        )
        decision = self.engine.evaluate(target, SUBJECT, assessments=assessments)
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        self.assertIn("hard_gate_failed", decision.blocker_codes)

    def test_hard_gates_are_not_carried_by_debt(self) -> None:
        rules = ladder_rules(hard_gates=("geometry-integrity",))
        target = contract(promotion_rules=rules)
        assessments = tuple(
            assessment(
                dimension_id,
                gate=GateState.FAIL if dimension_id == "geometry-integrity" else GateState.PASS,
                evidence_items=[evidence(f"ev.{dimension_id}", dimension_id)],
            )
            for dimension_id in DIMENSIONS
        )
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=assessments,
            defects=(
                defect("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),
            ),
            debts=(debt("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),),
        )
        self.assertTrue(decision.findings[0].deferred)
        self.assertIn("hard_gate_failed", decision.blocker_codes)
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)

    def test_ordinary_gates_may_be_carried_by_accepted_debt(self) -> None:
        target = contract()
        assessments = tuple(
            assessment(
                dimension_id,
                gate=GateState.FAIL if dimension_id == "geometry-integrity" else GateState.PASS,
                evidence_items=[evidence(f"ev.{dimension_id}", dimension_id)],
            )
            for dimension_id in DIMENSIONS
        )
        blocked = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=assessments,
            defects=(defect("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),),
        )
        self.assertIn("dimension_gate_not_pass", blocked.blocker_codes)
        carried = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=assessments,
            defects=(defect("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),),
            debts=(debt("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),),
        )
        self.assertNotIn("dimension_gate_not_pass", carried.blocker_codes)
        self.assertIs(carried.awarded_class, QualityClass.MASTER)


class JuryDisagreementTests(TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.target = authorized(
            contract(max_judge_disagreement=0.15),
            ComponentVersion("jury-one", "1.0.0"),
            ComponentVersion("jury-two", "2.0.0"),
        )

    def _jury(self, first: float, second: float) -> tuple[JudgeResult, JudgeResult]:
        return (
            judge_result(
                self.target,
                covered_assessments(value=first, confidence=0.9),
                judge=ComponentVersion("jury-one", "1.0.0"),
            ),
            judge_result(
                self.target,
                covered_assessments(value=second, confidence=0.8),
                judge=ComponentVersion("jury-two", "2.0.0"),
            ),
        )

    def test_disagreement_beyond_tolerance_forces_human_review(self) -> None:
        first, second = self._jury(0.9, 0.4)
        decision = self.engine.evaluate(self.target, SUBJECT, results=(first, second))
        self.assertTrue(decision.requires_human_review)
        self.assertEqual(decision.outcome.value, "HUMAN_REVIEW")
        self.assertIn("judge_disagreement", decision.blocker_codes)
        self.assertEqual(decision.judge_references, ("jury-one@1.0.0", "jury-two@2.0.0"))
        self.assertTrue(decision.disagreements)

    def test_agreeing_jurors_reach_a_verdict(self) -> None:
        first, second = self._jury(0.9, 0.92)
        decision = self.engine.evaluate(self.target, SUBJECT, results=(first, second))
        self.assertEqual(decision.outcome.value, "PROMOTED")
        self.assertEqual(decision.disagreements, ())

    def test_consensus_keeps_the_worst_gate_and_lowest_confidence(self) -> None:
        pessimistic = judge_result(
            self.target,
            covered_assessments(gate=GateState.FAIL, confidence=0.6),
            judge=ComponentVersion("jury-two", "2.0.0"),
        )
        optimistic = judge_result(
            self.target,
            covered_assessments(gate=GateState.PASS, confidence=0.99),
            judge=ComponentVersion("jury-one", "1.0.0"),
        )
        merged = merge_assessments(self.target, SUBJECT, (optimistic, pessimistic))
        self.assertEqual({item.gate for item in merged}, {GateState.FAIL})
        self.assertEqual({item.confidence for item in merged}, {0.6})
        self.assertEqual({item.evaluator.identifier for item in merged}, {"jury-consensus"})

    def test_results_must_agree_on_contract_and_subject(self) -> None:
        foreign = judge_result(
            contract(contract_id="contract.other"),
            covered_assessments(),
        )
        with self.assertRaises(EvaluationInputError):
            self.engine.evaluate(self.target, SUBJECT, results=(foreign,))
        with self.assertRaises(EvaluationInputError):
            self.engine.evaluate(
                self.target, SubjectRef("asset.other", DIGEST), results=(foreign,)
            )

    def test_a_dimension_may_not_arrive_from_two_sources(self) -> None:
        result = judge_result(self.target, covered_assessments())
        with self.assertRaises(EvaluationInputError):
            self.engine.evaluate(
                self.target, SUBJECT, results=(result,), assessments=covered_assessments()
            )

    def test_undeclared_defect_class_fails_closed(self) -> None:
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(
                self.target, SUBJECT, assessments=covered_assessments(), defects=(defect("d.x", "vibes-off"),)
            )
        self.assertIn("not declared by contract", str(caught.exception))

    def test_two_jurors_cannot_report_the_same_defect_differently(self) -> None:
        first = judge_result(self.target, (), defects=(defect("d.dup", "geometry-break", DefectSeverity.MAJOR),))
        second = judge_result(
            self.target,
            (),
            judge=ComponentVersion("jury-two", "2.0.0"),
            defects=(defect("d.dup", "geometry-break", DefectSeverity.MINOR),),
        )
        with self.assertRaises(EvaluationInputError):
            self.engine.evaluate(self.target, SUBJECT, results=(first, second))
