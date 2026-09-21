"""Área E part 2: typed gates, the request that compiles them, and the bundle they leave.

Three claims organize these tests. What a promotion owes is compiled from the rungs it
crosses, so a waived ladder still pays every skipped obligation. A ``PASS`` is three things
at once — an authority, evidence of the right family, and the exact inputs it stood on — so
§7 can retire it later without asking anyone to remember. And the human-review lane is
answered by the approvals on file, never by a result a caller wrote, because mandatory
review that a string can satisfy is not mandatory.

M01 appears here as a real ``QualityDecision`` produced by the real engine. That is the only
way to prove the integration WO §6 asks for: M02 composes the judgement and never re-decides
it.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_quality.contracts import QualityClass
from iris_quality.decision import DecisionEngine, QualityDecision
from iris_quality.dimensions import UncertaintyState
from iris_quality.judging import SubjectRef

from iris_project_os.errors import LifecycleError, PromotionBlockedError, SchemaValidationError
from iris_project_os.identity import EntityKind, ExternalRef, new_id
from iris_project_os.lifecycle import (
    AuthorizedJump,
    Phase,
    ProductionLedger,
    Release,
    Review,
    TransitionProfile,
    initial_vector,
)
from iris_project_os.promotion import (
    EVIDENCE_KINDS,
    REQUIRED_GATES,
    FreshnessBinding,
    GateDependency,
    GateKind,
    GateOutcome,
    GateResult,
    HumanApproval,
    PromotionDecision,
    PromotionEvidenceBundle,
    PromotionGate,
    PromotionRequest,
    admit_promotion,
    attempt_result,
    bundle_for,
    compile_gates,
    promote,
    quality_result,
    rungs_crossed,
)
from iris_project_os.versions import ComponentVersion, content_digest

from tests import m01_kernel_support as m01

ACTOR = ComponentVersion("m02.test", "1.0.0")
REVIEWER = ComponentVersion("m02.review", "1.0.0")
SECOND_REVIEWER = ComponentVersion("m02.legal", "1.0.0")
NOW = 1_700_000_000_000
CANDIDATE = "b" * 64
MOVED = "c" * 64

ACCEPTANCE_GATES: tuple[GateKind, ...] = (
    GateKind.QUALITY,
    GateKind.HUMAN_REVIEW,
    GateKind.RIGHTS_CONSENT,
    GateKind.PROVENANCE,
    GateKind.SECURITY,
)

FAMILY_REF: dict[GateKind, EntityKind] = {
    GateKind.RIGHTS_CONSENT: EntityKind.RIGHTS,
    GateKind.PROVENANCE: EntityKind.PROVENANCE,
    GateKind.SECURITY: EntityKind.POLICY,
    GateKind.DELIVERY: EntityKind.DESTINATION,
    GateKind.EXTERNAL_SIDE_EFFECT: EntityKind.POLICY,
    GateKind.MATERIALIZATION: EntityKind.ARTIFACT,
    GateKind.STRUCTURAL: EntityKind.GRAPH,
}


def ref(kind: EntityKind = EntityKind.RECEIPT) -> ExternalRef:
    return ExternalRef(kind=kind, reference=new_id())


def rights() -> tuple[ExternalRef, ...]:
    return (ref(EntityKind.RIGHTS),)


def provenances() -> tuple[ExternalRef, ...]:
    return (ref(EntityKind.PROVENANCE),)


def decision_for(
    digest: str = CANDIDATE,
    *,
    assessments: Any = None,
    **contract_overrides: Any,
) -> QualityDecision:
    """One real M01 verdict: the engine decides, this module only reads it."""

    contract = m01.contract(**contract_overrides)
    subject = SubjectRef(subject_id="asset.subject", content_sha256=digest)
    return DecisionEngine().evaluate(
        contract,
        subject,
        assessments=m01.covered_assessments(contract.dimension_ids) if assessments is None else assessments,
        authority=m01.promotion_authority(contract),
    )


def ladder(profile: TransitionProfile | None = None) -> ProductionLedger:
    """A ledger standing on VALIDATING, the rung acceptance is asked from."""

    production_id = new_id()
    ledger = ProductionLedger(production_id, initial_vector(production_id), profile=profile)
    ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
    ledger.advance(actor=ACTOR, phase=Phase.READY)
    ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
    ledger.advance(actor=ACTOR, phase=Phase.VALIDATING, review="PENDING")
    return ledger


def at_ready(profile: TransitionProfile | None = None) -> ProductionLedger:
    production_id = new_id()
    ledger = ProductionLedger(production_id, initial_vector(production_id), profile=profile)
    ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
    ledger.advance(actor=ACTOR, phase=Phase.READY, review="PENDING")
    return ledger


def gate(kind: GateKind, gate_id: str, **over: Any) -> PromotionGate:
    payload: dict[str, Any] = dict(gate_id=gate_id, kind=kind)
    payload.update(over)
    return PromotionGate(**payload)


def binding_for(digest: str = CANDIDATE, dependencies: tuple[GateDependency, ...] | None = None) -> FreshnessBinding:
    return FreshnessBinding(
        subject_digest=digest,
        dependencies=(
            (GateDependency(reference="candidate", input_digest=digest, facet="SUBJECT"),)
            if dependencies is None
            else dependencies
        ),
        evaluated_at_ms=NOW,
    )


def passing(
    wanted: PromotionGate,
    kind_ref: EntityKind = EntityKind.POLICY,
    *,
    digest: str = CANDIDATE,
    authority: Any = ACTOR,
    binding: Any = None,
) -> GateResult:
    return GateResult(
        gate_id=wanted.gate_id,
        kind=wanted.kind,
        outcome=GateOutcome.PASS,
        reason="an external check with a name on it",
        authority=authority,
        evidence_refs=(ExternalRef(kind=kind_ref, reference=new_id()),),
        binding=binding_for(digest) if binding is None else binding,
        observed_at_ms=NOW,
    )


def approval_for(request: PromotionRequest, reviewer: ComponentVersion = REVIEWER, **over: Any) -> HumanApproval:
    payload: dict[str, Any] = dict(
        approval_id=new_id(),
        production_id=request.production_id,
        snapshot_id=request.candidate_snapshot_id,
        reviewer=reviewer,
        decision="APPROVED",
        covered_kinds=(GateKind.HUMAN_REVIEW,),
        statement="looked at the render",
        receipt_ref=ref(),
        timestamp_ms=NOW,
    )
    payload.update(over)
    return HumanApproval(**payload)


def acceptance_request(
    ledger: ProductionLedger,
    decision: QualityDecision,
    **over: Any
) -> PromotionRequest:
    """A request that already owes everything VALIDATING -> ACCEPTED compiles."""

    gates = list(over.pop("gates", None) or [])
    if not gates:
        gates = [
            gate(
                GateKind.QUALITY,
                "gate.quality",
                minimum_quality_class=QualityClass.MASTER,
                authority=decision.engine,
            )
        ]
        gates += [gate(kind, f"gate.{kind.value.lower()}") for kind in ACCEPTANCE_GATES if kind is not GateKind.QUALITY]
    payload: dict[str, Any] = dict(
        request_id=new_id(),
        production_id=ledger.production_id,
        candidate_snapshot_id=ledger.current.candidate_snapshot_id or new_id(),
        candidate_digest=CANDIDATE,
        source_vector=ledger.current,
        requested_phase=Phase.ACCEPTED,
        actor=ACTOR,
        gates=tuple(gates),
        quality_decision_refs=(ref(EntityKind.QUALITY_DECISION),),
        required_reviewers=(REVIEWER,),
        policy_refs=(ref(EntityKind.POLICY),),
    )
    payload.update(over)
    return PromotionRequest(**payload)


def answers_for(request: PromotionRequest, decision: QualityDecision) -> list[GateResult]:
    """One passing answer per non-review obligation the request declared."""

    collected: list[GateResult] = []
    for wanted in request.gates:
        if wanted.kind is GateKind.HUMAN_REVIEW:
            continue
        if wanted.kind is GateKind.QUALITY:
            collected.append(
                quality_result(
                    decision=decision,
                    gate=wanted,
                    candidate_digest=request.candidate_digest,
                    evidence_ref=request.quality_decision_refs[0],
                    observed_at_ms=NOW,
                )
            )
            continue
        collected.append(passing(wanted, FAMILY_REF.get(wanted.kind, EntityKind.POLICY)))
    return collected


class GateCompilationTests(unittest.TestCase):
    def test_a_rung_lists_the_obligations_it_owes(self) -> None:
        self.assertEqual(
            compile_gates(Phase.VALIDATING, Phase.ACCEPTED),
            (
                GateKind.QUALITY,
                GateKind.HUMAN_REVIEW,
                GateKind.RIGHTS_CONSENT,
                GateKind.PROVENANCE,
                GateKind.SECURITY,
            ),
        )

    def test_the_crossed_rungs_are_included_and_the_standing_one_is_not(self) -> None:
        self.assertEqual(rungs_crossed(Phase.VALIDATING, Phase.ACCEPTED), (Phase.ACCEPTED,))
        self.assertEqual(rungs_crossed(Phase.READY, Phase.VALIDATING), (Phase.MATERIALIZED, Phase.VALIDATING))

    def test_a_backwards_or_standing_promotion_compiles_nothing(self) -> None:
        self.assertEqual(rungs_crossed(Phase.ACCEPTED, Phase.READY), ())
        self.assertEqual(compile_gates(Phase.READY, Phase.READY), ())
        self.assertEqual(compile_gates(Phase.RELEASED, Phase.RELEASED), ())

    def test_skipping_a_rung_still_owes_what_that_rung_owed(self) -> None:
        """The whole point of compiling: a waiver carries proof, never a discount."""

        skipped = compile_gates(Phase.READY, Phase.ACCEPTED)
        walked = compile_gates(Phase.VALIDATING, Phase.ACCEPTED)
        for kind in walked:
            self.assertIn(kind, skipped)
        self.assertIn(GateKind.MATERIALIZATION, skipped)
        self.assertIn(GateKind.STRUCTURAL, skipped)

    def test_a_release_from_scratch_owes_the_acceptance_gates_it_leaps_over(self) -> None:
        owed = compile_gates(Phase.DRAFT, Phase.RELEASED)
        for kind in (GateKind.QUALITY, GateKind.HUMAN_REVIEW, GateKind.DELIVERY):
            self.assertIn(kind, owed)
        self.assertEqual(len(owed), len(set(owed)), "an obligation is stated once")

    def test_every_rung_is_declared_even_when_it_owes_nothing(self) -> None:
        self.assertEqual(REQUIRED_GATES[Phase.DRAFT], ())
        self.assertEqual(REQUIRED_GATES[Phase.SUPERSEDED], (GateKind.STRUCTURAL, GateKind.EXTERNAL_SIDE_EFFECT))

    def test_only_the_quality_family_may_stand_on_m01s_ladder(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            gate(GateKind.SECURITY, "gate.security", minimum_quality_class=QualityClass.MASTER)
        self.assertIn("only the QUALITY family", str(caught.exception))
        self.assertTrue(gate(GateKind.QUALITY, "gate.quality", minimum_quality_class="master").demands_quality)

    def test_an_obligation_states_whether_it_blocks_and_whether_an_unknown_may_pass(self) -> None:
        strict = gate(GateKind.SECURITY, "gate.security")
        self.assertTrue(strict.required)
        self.assertTrue(strict.blocking_unknown)
        lenient = gate(GateKind.SECURITY, "gate.lenient", required=False, blocking_unknown=False)
        self.assertFalse(lenient.required)
        self.assertFalse(lenient.blocking_unknown)
        with self.assertRaises(SchemaValidationError):
            gate(GateKind.SECURITY, "gate.security", required="yes")


class GateResultLawTests(unittest.TestCase):
    def test_a_pass_names_its_authority(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            GateResult(
                gate_id="gate.security",
                kind=GateKind.SECURITY,
                outcome=GateOutcome.PASS,
                reason="someone said so",
                evidence_refs=(ref(EntityKind.POLICY),),
                binding=binding_for(),
            )
        self.assertIn("no authority", str(caught.exception))

    def test_a_pass_cites_something(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            GateResult(
                gate_id="gate.security",
                kind=GateKind.SECURITY,
                outcome=GateOutcome.PASS,
                reason="a display badge is not evidence",
                authority=ACTOR,
                evidence_refs=(),
                binding=binding_for(),
            )
        self.assertIn("citing nothing", str(caught.exception))

    def test_a_pass_names_what_it_evaluated(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            GateResult(
                gate_id="gate.security",
                kind=GateKind.SECURITY,
                outcome=GateOutcome.PASS,
                reason="an approval that cannot be retracted is a vote",
                authority=ACTOR,
                evidence_refs=(ref(EntityKind.POLICY),),
            )
        self.assertIn("without naming what it evaluated", str(caught.exception))

    def test_evidence_must_belong_to_the_family_it_answers(self) -> None:
        wanted = gate(GateKind.RIGHTS_CONSENT, "gate.rights")
        with self.assertRaises(PromotionBlockedError) as caught:
            passing(wanted, EntityKind.POLICY)
        self.assertIn("RIGHTS", str(caught.exception))

    def test_each_family_names_its_own_evidence(self) -> None:
        self.assertEqual(EVIDENCE_KINDS[GateKind.QUALITY], (EntityKind.QUALITY_DECISION,))
        self.assertIn(EntityKind.DESTINATION, EVIDENCE_KINDS[GateKind.DELIVERY])
        self.assertNotIn(GateKind.SECURITY, EVIDENCE_KINDS, "a family with no declared evidence is open")

    def test_declaring_an_obligation_not_applicable_is_still_a_claim(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            GateResult(
                gate_id="gate.delivery",
                kind=GateKind.DELIVERY,
                outcome=GateOutcome.NOT_APPLICABLE,
                reason="nothing was delivered",
            )
        self.assertIn("nobody on record", str(caught.exception))

    def test_an_absent_lane_can_be_waived_by_a_named_authority(self) -> None:
        waived = GateResult(
            gate_id="gate.delivery",
            kind=GateKind.DELIVERY,
            outcome=GateOutcome.NOT_APPLICABLE,
            reason="this production has no external destination",
            authority=ACTOR,
        )
        self.assertFalse(waived.is_passing)
        self.assertIsNone(gate(GateKind.DELIVERY, "gate.delivery", required=False).blocks(waived))
        self.assertIn(
            "cannot be waived",
            gate(GateKind.DELIVERY, "gate.delivery", required=True).blocks(waived) or "",
        )

    def test_a_result_survives_the_payload_round_trip(self) -> None:
        result = passing(gate(GateKind.SECURITY, "gate.security"))
        self.assertEqual(GateResult.from_payload(result.to_payload()), result)

    def test_an_authority_is_a_component_and_not_a_string(self) -> None:
        with self.assertRaises(SchemaValidationError):
            GateResult(
                gate_id="gate.security",
                kind=GateKind.SECURITY,
                outcome=GateOutcome.FAIL,
                reason="failed",
                authority="trusted-enough",
            )

    def test_a_gate_and_its_answer_cannot_disagree_about_the_family(self) -> None:
        owed = gate(GateKind.PROVENANCE, "gate.provenance")
        other = gate(GateKind.SECURITY, "gate.provenance")
        self.assertIn("not the PROVENANCE obligation", owed.blocks(passing(other, EntityKind.POLICY)) or "")

    def test_an_unadmitted_authority_does_not_answer_the_obligation(self) -> None:
        wanted = gate(GateKind.SECURITY, "gate.security", authority=ComponentVersion("m02.scanner", "3.0.0"))
        reason = wanted.blocks(passing(wanted, EntityKind.POLICY, authority=ACTOR))
        self.assertIn("admits only", reason or "")

    def test_a_blocking_unknown_stays_blocking(self) -> None:
        unknown = GateResult(
            gate_id="gate.security",
            kind=GateKind.SECURITY,
            outcome=GateOutcome.UNKNOWN,
            reason="the scanner is down",
            authority=ACTOR,
        )
        self.assertIn("blocking unknown", gate(GateKind.SECURITY, "gate.security").blocks(unknown) or "")
        lenient = gate(GateKind.SECURITY, "gate.security", blocking_unknown=False)
        self.assertIsNone(lenient.blocks(unknown))

    def test_a_fail_reason_is_carried_into_the_refusal(self) -> None:
        failed = GateResult(
            gate_id="gate.security",
            kind=GateKind.SECURITY,
            outcome=GateOutcome.FAIL,
            reason="the archive carries an unsigned binary",
            authority=ACTOR,
        )
        self.assertIn("unsigned binary", gate(GateKind.SECURITY, "gate.security").blocks(failed) or "")

    def test_an_obligation_may_not_claim_inputs_the_answer_never_read(self) -> None:
        declared = GateDependency(reference="m02.font", input_digest=MOVED)
        wanted = gate(GateKind.SECURITY, "gate.security", depends_on=(declared,))
        self.assertIn("without binding", wanted.blocks(passing(wanted, EntityKind.POLICY)) or "")

    def test_a_passing_answer_that_read_what_was_declared_is_enough(self) -> None:
        declared = GateDependency(reference="m02.font", input_digest=MOVED)
        wanted = gate(GateKind.SECURITY, "gate.security", depends_on=(declared,))
        answer = passing(
            wanted,
            EntityKind.POLICY,
            binding=binding_for(
                dependencies=(declared, GateDependency(reference="candidate", input_digest=CANDIDATE, facet="SUBJECT"))
            ),
        )
        self.assertIsNone(wanted.blocks(answer))


class FreshnessTests(unittest.TestCase):
    def test_a_binding_names_one_facet_per_input(self) -> None:
        with self.assertRaises(SchemaValidationError):
            FreshnessBinding(
                subject_digest=CANDIDATE,
                dependencies=(
                    GateDependency(reference="candidate", input_digest=CANDIDATE, facet="SUBJECT"),
                    GateDependency(reference="candidate", input_digest=MOVED, facet="THUMBNAIL"),
                ),
            )

    def test_dependencies_are_sorted_so_an_equal_binding_reads_equal(self) -> None:
        first = GateDependency(reference="m02.font", input_digest=MOVED)
        second = GateDependency(reference="candidate", input_digest=CANDIDATE)
        left = FreshnessBinding(subject_digest=CANDIDATE, dependencies=(first, second))
        right = FreshnessBinding(subject_digest=CANDIDATE, dependencies=(second, first))
        self.assertEqual(left.dependencies, right.dependencies)
        self.assertEqual(left.text, "subject " + CANDIDATE[:12] + " over 2 input(s)")

    def test_a_moved_input_is_named_by_its_key(self) -> None:
        self.assertEqual(binding_for().staled_by({"candidate#SUBJECT": MOVED}), ("candidate#SUBJECT",))

    def test_a_report_may_name_the_input_without_the_facet(self) -> None:
        self.assertEqual(binding_for().staled_by({"candidate": MOVED}), ("candidate",))

    def test_an_input_that_did_not_move_is_not_reported(self) -> None:
        self.assertEqual(binding_for().staled_by({"candidate": CANDIDATE}), ())

    def test_an_unobserved_input_is_not_claimed_unchanged(self) -> None:
        self.assertEqual(binding_for().staled_by({"something.else": MOVED}), ())

    def test_reporting_an_input_as_unknown_revives_nothing(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            binding_for().staled_by({"candidate": None})
        self.assertIn("reported as unknown", str(caught.exception))

    def test_an_input_report_must_be_a_digest(self) -> None:
        with self.assertRaises(SchemaValidationError):
            binding_for().staled_by({"candidate": "moved"})

    def test_an_input_digest_is_grammar_checked_as_data(self) -> None:
        with self.assertRaises(SchemaValidationError):
            GateDependency(reference="candidate", input_digest="nope")

    def test_a_result_with_no_binding_cannot_go_stale(self) -> None:
        bare = GateResult(
            gate_id="gate.security",
            kind=GateKind.SECURITY,
            outcome=GateOutcome.UNKNOWN,
            reason="the scanner is down",
        )
        self.assertEqual(bare.staled_by({"candidate": MOVED}), ())

    def test_a_stale_pass_is_a_missing_answer_and_not_a_fifth_verdict(self) -> None:
        self.assertEqual(GateOutcome.members(), ["FAIL", "NOT_APPLICABLE", "PASS", "UNKNOWN"])

    def test_a_binding_is_reusable_as_data(self) -> None:
        binding = binding_for()
        self.assertEqual(FreshnessBinding.from_payload(binding.to_payload()), binding)



    def test_a_lifecycle_obligation_cannot_be_declared_optional(self) -> None:
        quality = decision_for()
        ledger = ladder()
        gates = list(acceptance_request(ledger, quality).gates)
        gates = [
            replace(item, required=False) if item.kind is GateKind.QUALITY else item
            for item in gates
        ]
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(ledger, quality, gates=tuple(gates))
        self.assertIn("cannot be weakened", str(caught.exception))

    def test_a_required_lifecycle_gate_cannot_make_unknown_non_blocking(self) -> None:
        quality = decision_for()
        ledger = ladder()
        gates = list(acceptance_request(ledger, quality).gates)
        gates = [
            replace(item, blocking_unknown=False) if item.kind is GateKind.QUALITY else item
            for item in gates
        ]
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(ledger, quality, gates=tuple(gates))
        self.assertIn("fail closed", str(caught.exception))


class QualityCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quality = decision_for()
        self.ledger = ladder()
        self.request = acceptance_request(self.ledger, self.quality)
        self.wanted = self.request.gates_of(GateKind.QUALITY)[0]

    def answer(self, decision: QualityDecision | None = None, **over: Any) -> GateResult:
        return quality_result(
            decision=decision or self.quality,
            gate=self.wanted,
            candidate_digest=over.pop("candidate_digest", self.request.candidate_digest),
            evidence_ref=over.pop("evidence_ref", self.request.quality_decision_refs[0]),
            observed_at_ms=NOW,
            **over,
        )

    def test_the_awarded_class_carries_the_gate(self) -> None:
        answer = self.answer()
        self.assertIs(answer.outcome, GateOutcome.PASS)
        self.assertEqual(answer.authority, self.quality.engine)
        self.assertIn("MASTER", answer.reason)
        self.assertIn("passed by", answer.summary)

    def test_a_decision_about_other_bytes_certifies_nothing(self) -> None:
        answer = self.answer(decision_for(digest=MOVED))
        self.assertIs(answer.outcome, GateOutcome.FAIL)
        self.assertIn("not this candidate", answer.reason)

    def test_an_under_qualified_decision_cannot_satisfy_a_higher_gate(self) -> None:
        """WO §6: M01's class is the claim; a lower one does not negotiate its way up."""

        preview = self.answer(decision_for(output_class=QualityClass.PREVIEW))
        self.assertIs(preview.outcome, GateOutcome.FAIL)
        self.assertIn("an under-qualified decision cannot satisfy a higher gate", preview.reason)

    def test_a_decision_m01_will_not_certify_without_a_human_stays_unknown(self) -> None:
        owed = decision_for(assessments=m01.covered_assessments(
            m01.DIMENSIONS, uncertainty=UncertaintyState.HUMAN_REVIEW
        ))
        self.assertTrue(owed.requires_human_review)
        answer = self.answer(owed)
        self.assertIs(answer.outcome, GateOutcome.UNKNOWN)
        self.assertIn("human review", answer.reason)

    def test_a_quality_gate_refuses_an_attempt_receipt_as_evidence(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            self.answer(evidence_ref=ref(EntityKind.ATTEMPT))
        self.assertIn("an attempt receipt proves a process ended", str(caught.exception))

    def test_a_quality_gate_refuses_an_attempt_outcome_entirely(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            attempt_result(gate=self.wanted, attempt_id=new_id(), provider=ACTOR, succeeded=True)
        self.assertIn("proves that attempt", str(caught.exception))

    def test_an_attempt_success_is_recorded_and_still_answers_nothing(self) -> None:
        other = gate(GateKind.MATERIALIZATION, "gate.materialization")
        answer = attempt_result(gate=other, attempt_id=new_id(), provider=ACTOR, succeeded=True)
        self.assertIs(answer.outcome, GateOutcome.UNKNOWN)
        self.assertIn("blocking unknown", other.blocks(answer) or "")
        failed = attempt_result(gate=other, attempt_id=new_id(), provider=ACTOR, succeeded=False)
        self.assertIs(failed.outcome, GateOutcome.FAIL)
        self.assertIn("process failure", failed.reason)

    def test_the_binding_carries_the_evaluator_so_a_new_version_retires_it(self) -> None:
        answer = self.answer()
        key = f"m01.evaluator#{self.quality.engine.identifier}#VERSION"
        self.assertIn(key, [item.key for item in answer.binding.dependencies])
        self.assertIn(key, answer.staled_by({key: content_digest("m01-decision-engine-2.0.0")}))

    def test_the_binding_carries_the_contract_so_a_policy_change_retires_it(self) -> None:
        answer = self.answer()
        key = f"m01.contract#{self.quality.contract_id}#VERSION"
        self.assertIn(key, [item.key for item in answer.binding.dependencies])

    def test_only_a_quality_obligation_may_be_answered_by_a_decision(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            quality_result(
                decision=self.quality,
                gate=gate(GateKind.PROVENANCE, "gate.provenance"),
                candidate_digest=CANDIDATE,
                evidence_ref=ref(EntityKind.QUALITY_DECISION),
            )
        self.assertIn("only QUALITY", str(caught.exception))

    def test_quality_result_expects_the_m01_record_it_claims_to_read(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.answer(decision="MASTER")

    def test_the_quality_ladder_and_the_lifecycle_phase_stay_separate_axes(self) -> None:
        """D-M02-S05-007: M01 awarded a class; that is not the same claim as a phase."""

        self.assertEqual(self.quality.awarded_class.value, "MASTER")
        self.assertIs(self.ledger.current.phase, Phase.VALIDATING)

    def test_extra_inputs_a_gate_reads_can_be_bound(self) -> None:
        answer = self.answer(extra_dependencies=(GateDependency(reference="m02.font", input_digest=MOVED),))
        self.assertIn("m02.font#CONTENT", [item.key for item in answer.binding.dependencies])


    def test_a_generic_quality_pass_cannot_impersonate_m01(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            GateResult(
                gate_id=self.wanted.gate_id,
                kind=GateKind.QUALITY,
                outcome=GateOutcome.PASS,
                reason="trust me",
                authority=self.quality.engine,
                evidence_refs=(self.request.quality_decision_refs[0],),
                binding=binding_for(),
                observed_at_ms=NOW,
            )
        self.assertIn("M01 QualityDecision", str(caught.exception))

    def test_a_hand_built_quality_result_cannot_lie_about_the_floor(self) -> None:
        preview = decision_for(output_class=QualityClass.PREVIEW)
        forged = GateResult(
            gate_id=self.wanted.gate_id,
            kind=GateKind.QUALITY,
            outcome=GateOutcome.PASS,
            reason="pretends preview is master",
            authority=preview.engine,
            evidence_refs=(self.request.quality_decision_refs[0],),
            binding=FreshnessBinding(
                subject_digest=preview.subject.content_sha256,
                dependencies=(GateDependency(reference="candidate", input_digest=preview.subject.content_sha256),),
                evaluated_at_ms=NOW,
            ),
            quality_decision=preview,
            observed_at_ms=NOW,
        )
        self.assertIn("this promotion demands", self.wanted.blocks(forged) or "")


class HumanReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quality = decision_for()
        self.ledger = ladder()
        self.request = acceptance_request(self.ledger, self.quality)
        self.results = answers_for(self.request, self.quality)

    def admit(self, approvals: Any = (), **over: Any) -> PromotionDecision:
        return admit_promotion(self.request, self.results, approvals=approvals, now_ms=NOW, **over)

    def test_a_request_may_not_write_its_own_human_review_answer(self) -> None:
        forged = GateResult(
            gate_id="gate.human_review",
            kind=GateKind.HUMAN_REVIEW,
            outcome=GateOutcome.PASS,
            reason="trust me",
            authority=ACTOR,
            evidence_refs=(ref(),),
            binding=binding_for(),
        )
        with self.assertRaises(PromotionBlockedError) as caught:
            admit_promotion(self.request, self.results + [forged], approvals=(), now_ms=NOW)
        self.assertIn("hand-written human-review answer", str(caught.exception))

    def test_a_missing_review_blocks(self) -> None:
        refused = self.admit()
        self.assertFalse(refused.admitted)
        self.assertIn("still owes", refused.blocking_reasons[0])
        self.assertIn(REVIEWER.identifier, refused.blocking_reasons[0])

    def test_one_named_approval_answers_the_lane(self) -> None:
        granted = self.admit((approval_for(self.request),))
        self.assertTrue(granted.admitted)
        answer = next(item for item in granted.gate_results if item.kind is GateKind.HUMAN_REVIEW)
        self.assertIs(answer.outcome, GateOutcome.PASS)
        self.assertEqual(answer.authority, REVIEWER)

    def test_every_required_reviewer_must_have_signed(self) -> None:
        widen = replace(self.request, required_reviewers=(REVIEWER, SECOND_REVIEWER))
        refused = admit_promotion(widen, self.results, approvals=(approval_for(widen),), now_ms=NOW)
        self.assertFalse(refused.admitted)
        self.assertIn(SECOND_REVIEWER.identifier, refused.blocking_reasons[0])

    def test_two_approvals_are_carried_as_evidence_not_picked_from(self) -> None:
        widen = replace(self.request, required_reviewers=(REVIEWER, SECOND_REVIEWER))
        granted = admit_promotion(
            widen,
            answers_for(widen, self.quality),
            approvals=(approval_for(widen), approval_for(widen, SECOND_REVIEWER)),
            now_ms=NOW,
        )
        answer = next(item for item in granted.gate_results if item.kind is GateKind.HUMAN_REVIEW)
        self.assertIs(answer.outcome, GateOutcome.PASS)
        self.assertEqual(len(answer.evidence_refs), 4, "each approval names itself and its receipt")

    def test_a_review_of_another_candidate_is_recorded_and_counts_for_nothing(self) -> None:
        stranger = approval_for(self.request, snapshot_id=new_id())
        refused = self.admit((stranger,))
        self.assertFalse(refused.admitted)
        self.assertIn("not the candidate this promotion asks about", refused.unresolved[0])
        self.assertIn("still owes", refused.blocking_reasons[0])

    def test_an_approval_for_another_production_is_a_misuse_not_a_judgement(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            self.admit((approval_for(self.request, production_id=new_id()),))
        self.assertIn("another production", str(caught.exception))

    def test_a_rejection_blocks_and_is_not_washed_out_by_an_approval(self) -> None:
        asked = approval_for(self.request, decision="CHANGES_REQUIRED", covered_kinds=())
        refused = self.admit((approval_for(self.request), asked))
        self.assertFalse(refused.admitted)
        self.assertIn("asked for changes", refused.blocking_reasons[0])

    def test_an_approval_that_covered_another_lane_does_not_answer_review(self) -> None:
        elsewhere = approval_for(self.request, covered_kinds=(GateKind.DELIVERY,))
        refused = self.admit((elsewhere,))
        self.assertFalse(refused.admitted)
        self.assertIn("not the human-review lane", refused.unresolved[0])

    def test_an_approval_records_the_digest_of_what_it_read(self) -> None:
        signed = approval_for(self.request)
        review = next(
            item for item in self.admit((signed,)).gate_results if item.kind is GateKind.HUMAN_REVIEW
        )
        self.assertIn(f"approval#{signed.approval_id}#RECORD", [item.key for item in review.binding.dependencies])
        self.assertTrue(review.staled_by({f"approval#{signed.approval_id}": MOVED}))

    def test_a_review_lane_that_names_nobody_is_refused_as_data(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(self.ledger, self.quality, required_reviewers=())
        self.assertIn("mandatory review is a person", str(caught.exception))

    def test_a_pinned_review_lane_is_answered_only_by_that_reviewer(self) -> None:
        pinned = gate(GateKind.HUMAN_REVIEW, "gate.human_review", authority=SECOND_REVIEWER)
        lanes = tuple(item if item.kind is not GateKind.HUMAN_REVIEW else pinned for item in self.request.gates)
        request = replace(self.request, gates=lanes, required_reviewers=(SECOND_REVIEWER,))
        answers = answers_for(request, self.quality)
        refused = admit_promotion(request, answers, approvals=(approval_for(request),), now_ms=NOW)
        self.assertFalse(refused.admitted)
        self.assertIn(SECOND_REVIEWER.identifier, refused.blocking_reasons[0])
        granted = admit_promotion(
            request, answers, approvals=(approval_for(request, SECOND_REVIEWER),), now_ms=NOW
        )
        self.assertTrue(granted.admitted)

    def test_an_approval_must_say_what_it_signed_for(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            approval_for(self.request, covered_kinds=())
        self.assertIn("a signature without a meaning", str(caught.exception))

    def test_an_approval_is_not_a_pending_or_a_note(self) -> None:
        for decision in ("PENDING", "NOT_REQUESTED"):
            with self.assertRaises(PromotionBlockedError):
                approval_for(self.request, decision=decision)


class PromotionRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quality = decision_for()
        self.ledger = ladder()

    def test_a_request_binds_the_exact_candidate_it_asks_about(self) -> None:
        request = acceptance_request(self.ledger, self.quality)
        self.assertEqual(request.candidate_snapshot_id, self.ledger.current.candidate_snapshot_id)
        self.assertEqual(request.rungs, (Phase.ACCEPTED,))
        self.assertEqual(request.obligations, compile_gates(Phase.VALIDATING, Phase.ACCEPTED))
        self.assertIn("VALIDATING -> ACCEPTED", request.summary)

    def test_a_candidate_digest_must_be_a_digest(self) -> None:
        with self.assertRaises(SchemaValidationError):
            acceptance_request(self.ledger, self.quality, candidate_digest="draft")

    def test_a_request_may_not_promote_another_productions_state(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(self.ledger, self.quality, production_id=new_id())
        self.assertIn("another production's state", str(caught.exception))

    def test_a_request_that_judges_the_wrong_candidate_is_refused(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(self.ledger, self.quality, candidate_snapshot_id=new_id())
        self.assertIn("standing on", str(caught.exception))

    def test_a_promotion_moves_forward_only(self) -> None:
        for phase, needle in ((Phase.READY, "moves forward"), (Phase.VALIDATING, "moves forward"), (Phase.DRAFT, "where every production starts")):
            with self.assertRaises(PromotionBlockedError) as caught:
                acceptance_request(self.ledger, self.quality, requested_phase=phase)
            self.assertIn(needle, str(caught.exception))

    def test_an_under_declared_request_is_refused_by_the_compiled_floor(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(self.ledger, self.quality, gates=(gate(GateKind.QUALITY, "gate.quality"),))
        self.assertIn("without gates answering HUMAN_REVIEW", str(caught.exception))

    def test_a_declared_gate_id_cannot_be_reused(self) -> None:
        duplicated = (gate(GateKind.SECURITY, "gate.same"), gate(GateKind.PROVENANCE, "gate.same"))
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(self.ledger, self.quality, gates=duplicated)
        self.assertIn("one gate id twice", str(caught.exception))

    def test_a_quality_gate_cites_m01_or_does_not_exist(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(self.ledger, self.quality, quality_decision_refs=())
        self.assertIn("a render that finished", str(caught.exception))

    def test_a_release_names_where_it_delivers(self) -> None:
        standing = self.ledger.advance(
            actor=ACTOR, phase=Phase.ACCEPTED, promotion_ref=ref(EntityKind.EVIDENCE)
        ).to_vector
        owed = tuple(
            gate(kind, f"gate.{kind.value.lower()}") for kind in compile_gates(Phase.ACCEPTED, Phase.RELEASED)
        )
        with self.assertRaises(PromotionBlockedError) as caught:
            PromotionRequest(
                request_id=new_id(),
                production_id=self.ledger.production_id,
                candidate_snapshot_id=standing.candidate_snapshot_id,
                candidate_digest=CANDIDATE,
                source_vector=standing,
                requested_phase=Phase.RELEASED,
                actor=ACTOR,
                gates=owed,
                quality_decision_refs=(ref(EntityKind.QUALITY_DECISION),),
            )
        self.assertIn("names no destination", str(caught.exception))

    def test_a_waived_ladder_may_only_cross_edges_its_profile_authorizes(self) -> None:
        profile = TransitionProfile(
            profile_id="profile.narrow",
            terminal_phase=Phase.RELEASED,
            obligations=("a waiver that does not reach acceptance",),
            jumps=(AuthorizedJump(source=Phase.READY, target=Phase.VALIDATING, proof_refs=(ref(),)),),
        )
        moved = at_ready(profile)
        owed = tuple(gate(kind, f"gate.{kind.value.lower()}") for kind in compile_gates(Phase.READY, Phase.ACCEPTED))
        with self.assertRaises(PromotionBlockedError) as caught:
            PromotionRequest(
                request_id=new_id(),
                production_id=moved.production_id,
                candidate_snapshot_id=new_id(),
                candidate_digest=CANDIDATE,
                source_vector=moved.current,
                requested_phase=Phase.ACCEPTED,
                actor=ACTOR,
                gates=owed,
                profile=profile,
                quality_decision_refs=(ref(EntityKind.QUALITY_DECISION),),
                required_reviewers=(REVIEWER,),
            )
        self.assertIn("does not authorize", str(caught.exception))

    def test_a_multi_rung_promotion_without_a_profile_is_refused(self) -> None:
        """A skip is a policy decision with proof, so nobody compiles one by naming a far rung."""

        with self.assertRaises(PromotionBlockedError) as caught:
            acceptance_request(self.ledger, self.quality, requested_phase=Phase.RELEASED)
        self.assertIn("with no profile", str(caught.exception))

    def test_a_request_survives_the_payload_round_trip(self) -> None:
        request = acceptance_request(self.ledger, self.quality)
        self.assertEqual(PromotionRequest.from_payload(request.to_payload()), request)

    def test_a_request_reference_is_a_receipt_and_its_own_id(self) -> None:
        request = acceptance_request(self.ledger, self.quality)
        self.assertIs(request.reference.kind, EntityKind.RECEIPT)
        self.assertEqual(request.reference.reference, request.request_id)

    def test_a_request_needs_its_actors_identity(self) -> None:
        with self.assertRaises(SchemaValidationError):
            acceptance_request(self.ledger, self.quality, actor="the-team")



    def test_distinct_human_review_lanes_each_require_only_their_named_authority(self) -> None:
        quality = decision_for()
        ledger = ladder()
        base = acceptance_request(ledger, quality)
        lanes = tuple(
            item for item in base.gates if item.kind is not GateKind.HUMAN_REVIEW
        ) + (
            gate(GateKind.HUMAN_REVIEW, "gate.review.creative", authority=REVIEWER),
            gate(GateKind.HUMAN_REVIEW, "gate.review.legal", authority=SECOND_REVIEWER),
        )
        request = acceptance_request(
            ledger,
            quality,
            gates=lanes,
            required_reviewers=(REVIEWER, SECOND_REVIEWER),
        )
        answers = answers_for(request, quality)
        decision = admit_promotion(
            request,
            answers,
            approvals=(
                approval_for(request, REVIEWER),
                approval_for(request, SECOND_REVIEWER),
            ),
            now_ms=NOW,
        )
        self.assertTrue(decision.admitted)
        review_results = [item for item in decision.gate_results if item.kind is GateKind.HUMAN_REVIEW]
        self.assertEqual(len(review_results), 2)
        self.assertTrue(all(item.outcome is GateOutcome.PASS for item in review_results))


class AdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quality = decision_for()
        self.ledger = ladder()
        self.request = acceptance_request(self.ledger, self.quality)
        self.results = answers_for(self.request, self.quality)
        self.approvals = (approval_for(self.request),)

    def admit(self, **over: Any) -> PromotionDecision:
        payload: dict[str, Any] = dict(approvals=self.approvals, now_ms=NOW, results=self.results)
        payload.update(over)
        results = payload.pop("results")
        return admit_promotion(self.request, results, **payload)

    def test_a_complete_answer_set_admits(self) -> None:
        decision = self.admit()
        self.assertTrue(decision.admitted)
        self.assertEqual(decision.blocking_reasons, ())
        self.assertIn("may enter ACCEPTED", decision.summary)
        self.assertEqual(decision.decided_at_ms, NOW)

    def test_an_unanswered_required_gate_blocks(self) -> None:
        missing = [item for item in self.results if item.kind is not GateKind.PROVENANCE]
        decision = self.admit(results=missing)
        self.assertFalse(decision.admitted)
        self.assertIn("was never answered", decision.blocking_reasons[0])

    def test_a_failed_gate_carries_its_reason_into_the_refusal(self) -> None:
        failed = GateResult(
            gate_id="gate.security",
            kind=GateKind.SECURITY,
            outcome=GateOutcome.FAIL,
            reason="an unsigned binary in the archive",
            authority=ACTOR,
        )
        swapped = [item if item.gate_id != "gate.security" else failed for item in self.results]
        decision = self.admit(results=swapped)
        self.assertFalse(decision.admitted)
        self.assertIn("unsigned binary", decision.blocking_reasons[0])

    def test_a_stale_pass_blocks_and_is_listed(self) -> None:
        decision = self.admit(current_digests={"candidate": MOVED})
        self.assertFalse(decision.admitted)
        self.assertIn("never silently inherited", decision.blocking_reasons[0])
        self.assertEqual(len(decision.stale_gates), 5)

    def test_an_owed_family_cannot_be_weakened_to_optional(self) -> None:
        lenient = gate(GateKind.SECURITY, "gate.security", required=False)
        lanes = tuple(item if item.kind is not GateKind.SECURITY else lenient for item in self.request.gates)
        with self.assertRaises(PromotionBlockedError) as caught:
            replace(self.request, gates=lanes)
        self.assertIn("cannot be weakened", str(caught.exception))

    def test_an_owed_family_cannot_make_unknown_non_blocking(self) -> None:
        lenient = gate(GateKind.SECURITY, "gate.security", required=True, blocking_unknown=False)
        lanes = tuple(item if item.kind is not GateKind.SECURITY else lenient for item in self.request.gates)
        with self.assertRaises(PromotionBlockedError) as caught:
            replace(self.request, gates=lanes)
        self.assertIn("fail closed", str(caught.exception))

    def test_a_single_explanation_is_offered_per_blocked_family(self) -> None:
        missing = [item for item in self.results if item.kind is not GateKind.SECURITY]
        decision = self.admit(results=missing)
        self.assertEqual(len([item for item in decision.blocking_reasons if "SECURITY" in item]), 1)

    def test_one_gate_cannot_be_answered_twice(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            self.admit(results=list(self.results) + [self.results[0]])
        self.assertIn("answered twice", str(caught.exception))

    def test_a_decision_cannot_admit_and_still_complain(self) -> None:
        base = dict(
            decision_id=new_id(),
            request_id=self.request.request_id,
            production_id=self.request.production_id,
            requested_phase=Phase.ACCEPTED,
        )
        with self.assertRaises(PromotionBlockedError) as caught:
            PromotionDecision(admitted=False, blocking_reasons=(), **base)
        self.assertIn("name its blocker", str(caught.exception))
        with self.assertRaises(PromotionBlockedError):
            PromotionDecision(admitted=True, blocking_reasons=("something",), **base)

    def test_a_decision_without_evidence_says_so(self) -> None:
        decision = self.admit()
        self.assertFalse(decision.has_evidence)
        with self.assertRaises(PromotionBlockedError):
            decision.require_evidence()

    def test_a_decision_survives_the_payload_round_trip(self) -> None:
        decision = self.admit()
        self.assertEqual(PromotionDecision.from_payload(decision.to_payload()), decision)


class BundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quality = decision_for()
        self.ledger = ladder()
        self.request = acceptance_request(self.ledger, self.quality)
        self.results = answers_for(self.request, self.quality)
        self.approvals = (approval_for(self.request),)
        self.decision = admit_promotion(self.request, self.results, approvals=self.approvals, now_ms=NOW)
        self.transition = self.ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(EntityKind.EVIDENCE),
            review_receipt=self.approvals[0].receipt_ref,
        )

    def bundle(self, **over: Any) -> PromotionEvidenceBundle:
        payload: dict[str, Any] = dict(
            rights_refs=rights(),
            provenance_refs=provenances(),
            approvals=self.approvals,
            result_snapshot_id=new_id(),
        )
        payload.update(over)
        return bundle_for(self.request, self.decision, self.transition, **payload)

    def test_a_bundle_names_both_vectors_and_the_move_that_granted_them(self) -> None:
        built = self.bundle()
        self.assertEqual(built.source_vector, self.transition.from_vector)
        self.assertEqual(built.target_vector, self.transition.to_vector)
        self.assertEqual(built.transition_receipt_id, self.transition.receipt.transition_id)
        self.assertIs(built.actor, ACTOR)
        self.assertIs(built.authority, ACTOR)
        self.assertIn("1 approval(s)", built.summary)
        self.assertEqual(built.passed_kinds[:2], (GateKind.HUMAN_REVIEW, GateKind.PROVENANCE))

    def test_acceptance_carries_quality_rights_and_provenance(self) -> None:
        built = self.bundle()
        self.assertEqual(built.quality_decision_refs, self.request.quality_decision_refs)
        self.assertTrue(built.rights_refs)
        self.assertTrue(built.provenance_refs)
        self.assertIs(built.reference.kind, EntityKind.EVIDENCE)

    def test_a_bundle_of_no_gate_results_is_the_relabeling_iris_forbids(self) -> None:
        empty = replace(self.decision, gate_results=())
        with self.assertRaises(PromotionBlockedError) as caught:
            bundle_for(self.request, empty, self.transition)
        self.assertIn("no gate results", str(caught.exception))

    def test_a_refused_promotion_leaves_nothing_to_bundle(self) -> None:
        refused = admit_promotion(self.request, self.results, approvals=(), now_ms=NOW)
        with self.assertRaises(PromotionBlockedError) as caught:
            bundle_for(self.request, refused, self.transition)
        self.assertIn("refused the promotion", str(caught.exception))

    def test_evidence_of_a_different_promotion_certifies_nothing(self) -> None:
        further = self.ledger.advance(
            actor=ACTOR,
            phase=Phase.RELEASED,
            release_snapshot_id=new_id(),
            promotion_ref=ref(EntityKind.EVIDENCE),
        )
        with self.assertRaises(PromotionBlockedError) as caught:
            bundle_for(self.request, self.decision, further)
        self.assertIn("the recorded move arrived at", str(caught.exception))

    def test_an_approval_for_another_candidate_cannot_be_bundled_as_evidence(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            self.bundle(approvals=(approval_for(self.request, snapshot_id=new_id()),))
        self.assertIn("another candidate", str(caught.exception))

    def test_a_move_that_stands_on_another_candidate_refuses_the_bundle(self) -> None:
        """Same production, same phase, different bytes: the evidence would describe another promotion."""

        shared = new_id()
        walking = ProductionLedger(shared, initial_vector(shared))
        walking.advance(actor=ACTOR, phase=Phase.PLANNED)
        walking.advance(actor=ACTOR, phase=Phase.READY)
        walking.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
        walking.advance(actor=ACTOR, phase=Phase.VALIDATING)
        move = walking.advance(actor=ACTOR, phase=Phase.ACCEPTED, promotion_ref=ref(EntityKind.EVIDENCE))
        standing = initial_vector(shared, phase=Phase.VALIDATING, candidate_snapshot_id=new_id())
        request = acceptance_request(
            self.ledger,
            self.quality,
            production_id=shared,
            candidate_snapshot_id=standing.candidate_snapshot_id,
            source_vector=standing,
        )
        decision = admit_promotion(
            request, answers_for(request, self.quality), approvals=(approval_for(request),), now_ms=NOW
        )
        self.assertTrue(decision.admitted)
        with self.assertRaises(PromotionBlockedError) as caught:
            bundle_for(request, decision, move)
        self.assertIn("stands on", str(caught.exception))

    def test_a_release_bundle_owes_delivery_evidence(self) -> None:
        release_transition = self.ledger.advance(
            actor=ACTOR,
            phase=Phase.RELEASED,
            release_snapshot_id=new_id(),
            release_condition="STAGED",
            promotion_ref=ref(EntityKind.EVIDENCE),
        )
        release_request = replace(
            self.request,
            request_id=new_id(),
            source_vector=self.transition.to_vector,
            requested_phase=Phase.RELEASED,
            gates=tuple(
                gate(kind, f"gate.{kind.value.lower()}")
                for kind in compile_gates(Phase.ACCEPTED, Phase.RELEASED)
            ),
            release_target=ref(EntityKind.DESTINATION),
            required_reviewers=(),
        )
        release_decision = admit_promotion(
            release_request, answers_for(release_request, self.quality), now_ms=NOW
        )
        self.assertTrue(release_decision.admitted)
        with self.assertRaises(PromotionBlockedError) as caught:
            bundle_for(
                release_request,
                release_decision,
                release_transition,
                rights_refs=rights(),
                provenance_refs=provenances(),
            )
        self.assertIn("no delivery evidence", str(caught.exception))
        built = bundle_for(
            release_request,
            release_decision,
            release_transition,
            rights_refs=rights(),
            provenance_refs=provenances(),
            delivery_refs=(ref(EntityKind.DESTINATION),),
        )
        self.assertIn("RELEASED", built.summary)

    def test_a_bundle_survives_the_payload_round_trip(self) -> None:
        built = self.bundle()
        self.assertEqual(PromotionEvidenceBundle.from_payload(built.to_payload()), built)

    def test_a_second_answer_for_one_gate_is_two_answers_to_no_question(self) -> None:
        doubled = replace(
            self.decision, gate_results=list(self.decision.gate_results) + [self.decision.gate_results[0]]
        )
        with self.assertRaises(PromotionBlockedError) as caught:
            bundle_for(self.request, doubled, self.transition)
        self.assertIn("one gate twice", str(caught.exception))

    def test_a_bundle_that_carries_another_productions_vector_is_refused(self) -> None:
        built = self.bundle()
        other = ladder()
        with self.assertRaises(PromotionBlockedError) as caught:
            replace(built, production_id=other.production_id)
        self.assertIn("another production's source vector", str(caught.exception))


class PromotionMoveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quality = decision_for()
        self.ledger = ladder()
        self.request = acceptance_request(self.ledger, self.quality)
        self.results = answers_for(self.request, self.quality)
        self.approvals = (approval_for(self.request),)

    def promote(self, **over: Any) -> PromotionDecision:
        payload: dict[str, Any] = dict(
            approvals=self.approvals,
            now_ms=NOW,
            rights_refs=rights(),
            provenance_refs=provenances(),
            results=self.results,
        )
        payload.update(over)
        results = payload.pop("results")
        return promote(self.ledger, self.request, results, **payload)

    def test_a_granted_promotion_moves_the_state_and_leaves_the_bundle(self) -> None:
        before = self.ledger.current
        decision = self.promote()
        self.assertTrue(decision.admitted)
        self.assertIs(self.ledger.current.phase, Phase.ACCEPTED)
        self.assertIs(self.ledger.current.review, Review.APPROVED)
        self.assertEqual(decision.bundle.target_vector, self.ledger.current)
        self.assertEqual(decision.transition.from_vector, before)
        self.assertEqual(decision.require_evidence(), decision.bundle)

    def test_the_transition_and_its_evidence_point_at_each_other(self) -> None:
        decision = self.promote()
        self.assertEqual(decision.transition.promotion_ref, decision.bundle.reference)
        self.assertEqual(decision.bundle.transition_receipt_id, decision.transition.receipt.transition_id)

    def test_a_review_free_acceptance_cannot_even_be_asked_for(self) -> None:
        lanes = tuple(item for item in self.request.gates if item.kind is not GateKind.HUMAN_REVIEW)
        with self.assertRaises(PromotionBlockedError) as caught:
            replace(self.request, gates=lanes)
        self.assertIn("without gates answering HUMAN_REVIEW", str(caught.exception))

    def test_an_approval_with_no_receipt_behind_it_moves_no_review(self) -> None:
        """The gates can be satisfied while the state machine keeps the last word."""

        bare = replace(self.approvals[0], approval_id=new_id(), receipt_ref=None)
        with self.assertRaises(LifecycleError) as caught:
            self.promote(approvals=(bare,))
        self.assertIn("no review receipt", str(caught.exception))
        self.assertIs(self.ledger.current.phase, Phase.VALIDATING)
        self.assertEqual(len(self.ledger), 4)

    def test_a_refused_promotion_records_no_transition_and_no_evidence(self) -> None:
        length = len(self.ledger)
        refused = self.promote(approvals=())
        self.assertFalse(refused.admitted)
        self.assertFalse(refused.has_evidence)
        self.assertIsNone(refused.transition)
        self.assertEqual(len(self.ledger), length)
        self.assertIs(self.ledger.current.phase, Phase.VALIDATING)

    def test_a_promotion_compiled_against_a_moved_state_answers_nothing(self) -> None:
        stale = acceptance_request(self.ledger, self.quality)
        self.ledger.advance(actor=ACTOR, review="CHANGES_REQUIRED")
        with self.assertRaises(PromotionBlockedError) as caught:
            promote(self.ledger, stale, self.results, approvals=(approval_for(stale),), now_ms=NOW)
        self.assertIn("no longer this one", str(caught.exception))

    def test_a_promotion_needs_a_ledger_and_not_a_promise(self) -> None:
        with self.assertRaises(SchemaValidationError):
            promote(object(), self.request, self.results, approvals=self.approvals)

    def test_a_promotion_through_another_productions_ledger_is_refused(self) -> None:
        with self.assertRaises(PromotionBlockedError) as caught:
            promote(ladder(), self.request, self.results, approvals=self.approvals, now_ms=NOW)
        self.assertIn("through the ledger of", str(caught.exception))

    def test_history_replays_to_the_promoted_state(self) -> None:
        self.promote()
        proof = self.ledger.prove_state()
        self.assertEqual(proof.recorded_state, proof.replayed_state)
        self.assertEqual(proof.transitions, len(self.ledger))

    def test_accepted_and_released_are_distinct_claims(self) -> None:
        """D-M02-S05-008: acceptance is a judgement; release is a delivery transaction."""

        self.promote()
        self.assertIs(self.ledger.current.phase, Phase.ACCEPTED)
        self.assertIs(self.ledger.current.release_condition, Release.UNRELEASED)
        self.assertIsNone(self.ledger.current.release_snapshot_id)
        self.assertNotIn(GateKind.DELIVERY, self.request.obligations)

    def test_a_release_promotion_owes_the_delivery_and_side_effect_families(self) -> None:
        self.promote()
        owed = compile_gates(Phase.ACCEPTED, Phase.RELEASED)
        self.assertIn(GateKind.DELIVERY, owed)
        self.assertIn(GateKind.EXTERNAL_SIDE_EFFECT, owed)
        self.assertNotIn(GateKind.QUALITY, owed, "the acceptance it stands on already paid that")

    def test_a_waived_rung_still_owes_every_gate_it_skipped(self) -> None:
        profile = TransitionProfile(
            profile_id="profile.fastlane",
            terminal_phase=Phase.RELEASED,
            obligations=("a waived candidate phase is still judged on evidence",),
            jumps=(AuthorizedJump(source=Phase.READY, target=Phase.ACCEPTED, proof_refs=(ref(EntityKind.POLICY),)),),
            human_review_phases=(Phase.ACCEPTED,),
        )
        ledger = at_ready(profile)
        owed = tuple(gate(kind, f"gate.{kind.value.lower()}") for kind in compile_gates(Phase.READY, Phase.ACCEPTED))
        request = PromotionRequest(
            request_id=new_id(),
            production_id=ledger.production_id,
            candidate_snapshot_id=new_id(),
            candidate_digest=CANDIDATE,
            source_vector=ledger.current,
            requested_phase=Phase.ACCEPTED,
            actor=ACTOR,
            gates=owed,
            profile=profile,
            quality_decision_refs=(ref(EntityKind.QUALITY_DECISION),),
            required_reviewers=(REVIEWER,),
        )
        decision = promote(
            ledger,
            request,
            answers_for(request, self.quality),
            approvals=(approval_for(request),),
            now_ms=NOW,
            rights_refs=rights(),
            provenance_refs=provenances(),
        )
        self.assertTrue(decision.admitted)
        self.assertIs(ledger.current.phase, Phase.ACCEPTED)
        self.assertEqual(ledger.current.candidate_snapshot_id, request.candidate_snapshot_id)
        cited = [item.reference for item in decision.transition.receipt.evidence_refs]
        self.assertIn(profile.jump_between(Phase.READY, Phase.ACCEPTED).proof_refs[0].reference, cited)
        for kind in (GateKind.MATERIALIZATION, GateKind.STRUCTURAL):
            self.assertIn(kind, [item.kind for item in decision.gate_results])

    def test_a_promotion_declares_debts_and_observations_it_leaves_open(self) -> None:
        decision = self.promote(
            debts=(ref(EntityKind.POLICY),),
            consent_refs=rights(),
            result_snapshot_id=new_id(),
        )
        self.assertEqual(len(decision.bundle.debts), 1)
        self.assertEqual(len(decision.bundle.consent_refs), 1)
        self.assertIsNotNone(decision.bundle.result_snapshot_id)

    def test_a_promotion_can_be_given_a_stable_bundle_id(self) -> None:
        identity = new_id()
        decision = self.promote(bundle_id=identity)
        self.assertEqual(decision.bundle.bundle_id, identity)
        self.assertEqual(decision.transition.promotion_ref.reference, identity)

    def test_a_bundle_id_that_is_not_an_id_is_refused_as_data(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.promote(bundle_id="promotion-of-the-week")


if __name__ == "__main__":
    unittest.main()
