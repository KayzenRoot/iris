"""Área E part 3: the release transaction, the ambiguity fence, and what a recall keeps.

Three claims organize these tests. A release phase states something about the outside world and
owes the proof its own name carries, so STAGED names a package and PUBLISHED names an effect that
landed. Ambiguity is a recorded state rather than a permission to retry, which is why an
idempotency key an inspection has not answered cannot be re-used by anything, and why leaving
UNKNOWN requires a report instead of a decision to move on. And a withdrawal is a new fact beside
the release, never an eraser: the published step stays, the exact snapshot ref stays exact, and
supersession moves only where a *future* consumer is pointed.

The destination is external, so nothing here is satisfied by a string that says the work shipped.
The positive paths walk the real gate law, and the negative ones are the shapes §15 and §16
exist to refuse.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_project_os.errors import (
    IdentityError,
    LifecycleError,
    PromotionBlockedError,
    ReleaseError,
    SchemaValidationError,
    StoreConflictError,
)
from iris_project_os.graph import SideEffectClass
from iris_project_os.identity import EntityKind, ExternalRef, TransitionReceipt, new_id
from iris_project_os.lifecycle import Phase, ProductionLedger, ReleaseCondition, initial_vector
from iris_project_os.limits import MAX_RELEASE_STEPS
from iris_project_os.promotion import (
    FreshnessBinding,
    GateDependency,
    GateKind,
    GateOutcome,
    GateResult,
    PromotionGate,
    PromotionRequest,
    promote,
)
from iris_project_os.release import (
    ACTION_LAW,
    RELEASE_LAW,
    ExternalAction,
    ReconciliationReport,
    ReleaseLedger,
    ReleasePhase,
    ReleaseProof,
    ReleaseRegistry,
    ReleaseStep,
    ReleaseTransaction,
    RemoteState,
    WithdrawalReason,
    WithdrawalReceipt,
    WithdrawalState,
    begin_release,
    sync_release_state,
)
from iris_project_os.snapshots import ExternalEffectState
from iris_project_os.versions import ComponentVersion

ACTOR = ComponentVersion("m02.test", "1.0.0")
SHIPPER = ComponentVersion("m02.ship", "1.0.0")
INSPECTOR = ComponentVersion("m02.inspect", "1.0.0")
NOW = 1_700_000_000_000
CANDIDATE = "c" * 64
DEST = ExternalRef(kind=EntityKind.DESTINATION, reference="cdn.primary")
OTHER_DEST = ExternalRef(kind=EntityKind.DESTINATION, reference="cdn.europe")
KEY = "key-iris-release-1"


def ref(kind: EntityKind = EntityKind.RECEIPT) -> ExternalRef:
    return ExternalRef(kind=kind, reference=new_id())


def package_ref() -> ExternalRef:
    return ref(EntityKind.ARTIFACT)


def accepted() -> ProductionLedger:
    """A production standing at ACCEPTED, the only place a release may begin."""

    production_id = new_id()
    ledger = ProductionLedger(production_id, initial_vector(production_id))
    ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
    ledger.advance(actor=ACTOR, phase=Phase.READY)
    ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
    ledger.advance(actor=ACTOR, phase=Phase.VALIDATING, review="PENDING")
    ledger.advance(
        actor=ACTOR,
        phase=Phase.ACCEPTED,
        review="APPROVED",
        review_receipt=ref(),
        promotion_ref=ref(EntityKind.EVIDENCE),
    )
    return ledger


def action(
    state: Any = ExternalEffectState.NOT_APPLIED,
    key: Any = KEY,
    *,
    kind: Any = SideEffectClass.EXTERNAL_MUTATION,
    destination: Any = DEST,
    **over: Any,
) -> ExternalAction:
    payload: dict[str, Any] = dict(
        action_id=new_id(),
        destination=destination,
        state=state,
        kind=kind,
        idempotency_key=key,
    )
    payload.update(over)
    return ExternalAction(**payload)


def restated(item: ExternalAction, **over: Any) -> ExternalAction:
    """The same request, re-listed with whatever the destination has since revealed."""

    payload: dict[str, Any] = dict(
        action_id=item.action_id,
        destination=item.destination,
        kind=item.kind,
        idempotency_key=item.idempotency_key,
        state=item.state,
    )
    payload.update(over)
    return ExternalAction(**payload)


def landed(item: ExternalAction, **over: Any) -> ExternalAction:
    return restated(
        item,
        state=ExternalEffectState.APPLIED,
        external_receipt_ref=ref(EntityKind.PROVENANCE),
        **over,
    )


def release_request(ledger: ProductionLedger) -> PromotionRequest:
    gates = tuple(
        PromotionGate(gate_id=f"gate.{kind.value.lower()}", kind=kind)
        for kind in (
            GateKind.DELIVERY,
            GateKind.EXTERNAL_SIDE_EFFECT,
            GateKind.PROVENANCE,
            GateKind.RIGHTS_CONSENT,
        )
    )
    return PromotionRequest(
        request_id=new_id(),
        production_id=ledger.production_id,
        candidate_snapshot_id=ledger.current.candidate_snapshot_id,
        candidate_digest=CANDIDATE,
        source_vector=ledger.current,
        requested_phase=Phase.RELEASED,
        actor=SHIPPER,
        gates=gates,
        quality_decision_refs=(ref(EntityKind.QUALITY_DECISION),),
        release_target=DEST,
    )


def unready_request() -> PromotionRequest:
    """A well-formed promotion that is not a release, for the phase check alone."""

    production_id = new_id()
    ledger = ProductionLedger(production_id, initial_vector(production_id))
    ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
    ledger.advance(actor=ACTOR, phase=Phase.READY)
    return PromotionRequest(
        request_id=new_id(),
        production_id=production_id,
        candidate_snapshot_id=new_id(),
        candidate_digest=CANDIDATE,
        source_vector=ledger.current,
        requested_phase=Phase.MATERIALIZED,
        actor=SHIPPER,
        gates=(PromotionGate(gate_id="gate.materialization", kind=GateKind.MATERIALIZATION),),
    )


def binding(request: PromotionRequest) -> FreshnessBinding:
    return FreshnessBinding(
        subject_digest=request.candidate_digest,
        dependencies=(GateDependency(reference="candidate", input_digest=request.candidate_digest, facet="SUBJECT"),),
        evaluated_at_ms=NOW,
    )


def answer(
    request: PromotionRequest,
    wanted: PromotionGate,
    evidence: tuple[ExternalRef, ...],
    outcome: Any = GateOutcome.PASS,
) -> GateResult:
    return GateResult(
        gate_id=wanted.gate_id,
        kind=wanted.kind,
        outcome=outcome,
        reason="checked against the package" if outcome is GateOutcome.PASS else "the check did not come back",
        authority=ACTOR,
        evidence_refs=evidence,
        binding=binding(request),
        observed_at_ms=NOW,
    )


def gate_answers(
    request: PromotionRequest,
    releases: ReleaseLedger,
    *,
    uncertain: GateKind | None = None,
) -> list[GateResult]:
    """One answer per release obligation, each citing the family that obligation admits."""

    family = {
        GateKind.DELIVERY: releases.transaction.delivery_evidence(),
        GateKind.EXTERNAL_SIDE_EFFECT: (ref(EntityKind.POLICY),),
        GateKind.PROVENANCE: (ref(EntityKind.PROVENANCE),),
        GateKind.RIGHTS_CONSENT: (ref(EntityKind.RIGHTS),),
    }
    return [
        answer(
            request,
            wanted,
            family[wanted.kind],
            outcome=GateOutcome.UNKNOWN if wanted.kind is uncertain else GateOutcome.PASS,
        )
        for wanted in request.gates
    ]


def begin(maximum: int = MAX_RELEASE_STEPS, **over: Any) -> tuple[ReleaseLedger, ProductionLedger]:
    """An accepted production and the release transaction prepared from it."""

    over.setdefault("release_snapshot_id", new_id())
    over.setdefault("destination", DEST)
    over.setdefault("actor", SHIPPER)
    production = over.pop("production", None) or accepted()
    ledger = begin_release(production, **over)
    if maximum != MAX_RELEASE_STEPS:
        ledger = ReleaseLedger(ledger.transaction, maximum=maximum)
    return ledger, production


def gated(**over: Any) -> tuple[ReleaseLedger, PromotionRequest, ProductionLedger]:
    ledger, production = begin(**over)
    request = release_request(production)
    ledger.validate_gates(request, gate_answers(request, ledger), now_ms=NOW)
    return ledger, request, production


def staged(**over: Any) -> ReleaseLedger:
    ledger, _, _ = gated(**over)
    ledger.advance(
        ReleasePhase.STAGED,
        evidence_refs=(package_ref(), ledger.transaction.snapshot_ref),
        now_ms=NOW,
    )
    return ledger


def submitted(**over: Any) -> tuple[ReleaseLedger, ExternalAction]:
    ledger = staged(**over)
    first = action()
    ledger.submit((first,), now_ms=NOW)
    return ledger, first


def receipted(**over: Any) -> tuple[ReleaseLedger, ExternalAction]:
    ledger, first = submitted(**over)
    arrived = landed(first)
    ledger.advance(ReleasePhase.RECEIPTED, actions=(arrived,), now_ms=NOW)
    return ledger, arrived


def published(**over: Any) -> tuple[ReleaseLedger, ExternalAction]:
    ledger, arrived = receipted(**over)
    ledger.advance(ReleasePhase.PUBLISHED, actions=(arrived,), now_ms=NOW)
    return ledger, arrived


def ambiguous(**over: Any) -> tuple[ReleaseLedger, ExternalAction]:
    """A submit that ended with the destination's state unknown."""

    ledger = staged(**over)
    pending = action(state=ExternalEffectState.RECONCILIATION_REQUIRED)
    ledger.submit((pending,), now_ms=NOW)
    return ledger, pending


def report(release_id: str, outcome: Any = RemoteState.LANDED, **over: Any) -> ReconciliationReport:
    parsed = RemoteState.parse(outcome)
    payload: dict[str, Any] = dict(
        report_id=new_id(),
        release_id=release_id,
        destination=DEST,
        inspector=INSPECTOR,
        outcome=parsed,
        evidence_refs=(ref(EntityKind.PROVENANCE),),
        inspected_at_ms=NOW,
    )
    if parsed is RemoteState.LANDED:
        payload["remote_reference"] = package_ref()
    payload.update(over)
    return ReconciliationReport(**payload)


def withdrawal(releases: ReleaseLedger, **over: Any) -> WithdrawalReceipt:
    payload: dict[str, Any] = dict(
        withdrawal_id=new_id(),
        release_id=releases.release_id,
        production_id=releases.production_id,
        release_snapshot_id=releases.transaction.release_snapshot_id,
        reason=WithdrawalReason.LEGAL_RIGHTS,
        actor=SHIPPER,
        requested_actions=(landed(action(key="key-take-down-1")),),
        provenance_refs=(releases.transaction.snapshot_ref,),
        confirmed_at_ms=NOW,
    )
    payload.update(over)
    return WithdrawalReceipt(**payload)


def receipt(step: dict[str, Any], **over: Any) -> TransitionReceipt:
    """The durable proof of a hand-assembled step, signed for exactly what the step claims."""

    payload: dict[str, Any] = dict(
        transition_id=step["step_id"],
        entity_kind=EntityKind.RELEASE,
        entity_id=step["release_id"],
        from_state=step["from_phase"].value,
        to_state=step["to_phase"].value,
        actor=SHIPPER,
        reason_code="release-step",
        timestamp_ms=NOW,
    )
    payload.update(over)
    return TransitionReceipt(**payload)


def hand_step(ledger: ReleaseLedger, **over: Any) -> ReleaseStep:
    """A step assembled outside the ledger, for the moves ``advance`` will not make."""

    fields: dict[str, Any] = dict(
        step_id=new_id(),
        release_id=ledger.release_id,
        production_id=ledger.production_id,
        from_phase=ledger.phase,
        to_phase=ReleasePhase.STAGED,
        actions=(),
        evidence_refs=(package_ref(),),
    )
    fields.update(over)
    parent = fields.pop("causal_parent_receipt_id", ledger.head_receipt_id)
    return ReleaseStep(receipt=receipt(fields, causal_parent_receipt_id=parent), **fields)


class ReleaseLawTests(unittest.TestCase):
    """§15's six phases, plus the one state an unproven submit leaves behind."""

    def test_the_admitted_targets_are_the_ones_that_carry_forward(self) -> None:
        self.assertEqual(
            RELEASE_LAW.legal_targets(ReleasePhase.PREPARING),
            (ReleasePhase.GATED, ReleasePhase.UNKNOWN),
        )
        self.assertEqual(
            RELEASE_LAW.legal_targets(ReleasePhase.RECEIPTED),
            (ReleasePhase.PUBLISHED, ReleasePhase.UNKNOWN),
        )

    def test_publication_is_the_only_dead_end(self) -> None:
        self.assertTrue(RELEASE_LAW.is_terminal(ReleasePhase.PUBLISHED))
        self.assertFalse(RELEASE_LAW.is_terminal(ReleasePhase.UNKNOWN))
        self.assertEqual(RELEASE_LAW.legal_targets(ReleasePhase.PUBLISHED), ())

    def test_ambiguity_leaves_only_the_two_inspected_answers(self) -> None:
        """Out of UNKNOWN there is what the destination reported, and nothing else."""

        self.assertEqual(
            set(RELEASE_LAW.legal_targets(ReleasePhase.UNKNOWN)),
            {ReleasePhase.STAGED, ReleasePhase.RECEIPTED},
        )
        self.assertFalse(RELEASE_LAW.is_legal(ReleasePhase.UNKNOWN, ReleasePhase.SUBMITTED))

    def test_a_phase_that_touched_the_destination_says_so(self) -> None:
        seen = {
            ReleasePhase.SUBMITTED,
            ReleasePhase.RECEIPTED,
            ReleasePhase.PUBLISHED,
            ReleasePhase.UNKNOWN,
        }
        for phase in ReleasePhase:
            self.assertEqual(phase.touches_destination, phase in seen, phase.value)

    def test_the_law_refuses_a_jump_over_the_destination(self) -> None:
        ledger, _ = begin()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(ReleasePhase.PUBLISHED, actions=(landed(action()),), now_ms=NOW)
        self.assertIn("not a legal transition", str(caught.exception))


class ExternalActionTests(unittest.TestCase):
    """Each state carries the proof its own name claims and none of the others'."""

    def test_a_mutation_without_an_idempotency_key_is_not_a_request(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            action(key=None)
        self.assertIn("idempotency key", str(caught.exception))

    def test_a_read_needs_no_key_because_it_changes_nothing(self) -> None:
        quiet = action(key=None, kind=SideEffectClass.NO_SIDE_EFFECT)
        self.assertFalse(quiet.landed)
        self.assertTrue(quiet.settled)

    def test_a_state_that_claims_landing_names_the_remote_receipt(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            action(state=ExternalEffectState.APPLIED)
        self.assertIn("no remote receipt", str(caught.exception))

    def test_a_receipt_under_a_denied_state_is_a_contradiction(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            action(state=ExternalEffectState.NOT_APPLIED, external_receipt_ref=ref(EntityKind.PROVENANCE))
        self.assertIn("while reporting NOT_APPLIED", str(caught.exception))

    def test_reconciliation_and_compensation_do_not_overlap(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            action(
                state=ExternalEffectState.RECONCILIATION_REQUIRED,
                compensation_receipt_ref=ref(EntityKind.PROVENANCE),
            )
        self.assertIn("already compensated", str(caught.exception))
        with self.assertRaises(ReleaseError) as paid:
            action(state=ExternalEffectState.COMPENSATED)
        self.assertIn("without the receipt", str(paid.exception))

    def test_an_unresolved_request_must_be_matchable(self) -> None:
        """A side effect that needs no key generally needs one the moment it is unresolved."""

        with self.assertRaises(ReleaseError) as caught:
            action(
                state=ExternalEffectState.RECONCILIATION_REQUIRED,
                key=None,
                kind=SideEffectClass.CONTROLLED_OUTPUTS,
            )
        self.assertIn("never match it", str(caught.exception))

    def test_the_landing_predicates_answer_the_retries_question(self) -> None:
        self.assertTrue(landed(action()).landed)
        self.assertTrue(action(state=ExternalEffectState.IRREVERSIBLE, external_receipt_ref=ref()).landed)
        self.assertTrue(action(state=ExternalEffectState.RECONCILIATION_REQUIRED).unresolved)
        self.assertTrue(action(state=ExternalEffectState.COMPENSATED, compensation_receipt_ref=ref()).settled)

    def test_reopens_recognises_the_same_request_only_by_key(self) -> None:
        first = action(key="k-1")
        self.assertTrue(action(key="k-1").reopens(first))
        self.assertFalse(action(key="k-2").reopens(first))
        quiet = action(key=None, kind=SideEffectClass.NO_SIDE_EFFECT)
        self.assertFalse(quiet.reopens(quiet))

    def test_an_action_is_asked_of_a_destination_not_a_policy(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            action(destination=ref(EntityKind.POLICY))
        self.assertIn("DESTINATION", str(caught.exception))

    def test_the_action_law_forbids_the_rewrite_a_retry_would_attempt(self) -> None:
        self.assertTrue(
            ACTION_LAW.is_legal(ExternalEffectState.RECONCILIATION_REQUIRED, ExternalEffectState.NOT_APPLIED)
        )
        self.assertFalse(ACTION_LAW.is_legal(ExternalEffectState.APPLIED, ExternalEffectState.NOT_APPLIED))
        self.assertTrue(ACTION_LAW.is_terminal(ExternalEffectState.IRREVERSIBLE))
        self.assertEqual(ACTION_LAW.legal_targets(ExternalEffectState.APPLIED), (ExternalEffectState.COMPENSATED,))


class ReconciliationReportTests(unittest.TestCase):
    """The difference between an inspection and a resubmission."""

    def test_an_inspection_that_cites_nothing_is_a_retry_with_paperwork(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            report(new_id(), evidence_refs=())
        self.assertIn("cites nothing", str(caught.exception))

    def test_a_finding_that_says_landed_has_to_name_the_thing(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            report(new_id(), RemoteState.LANDED, remote_reference=None)
        self.assertIn("cannot name it", str(caught.exception))
        with self.assertRaises(ReleaseError) as clean:
            report(new_id(), RemoteState.NOT_LANDED, remote_reference=package_ref())
        self.assertIn("says nothing landed", str(clean.exception))

    def test_still_unknown_is_honest_and_resolves_nothing(self) -> None:
        finding = report(new_id(), RemoteState.STILL_UNKNOWN)
        self.assertFalse(finding.resolves)
        self.assertFalse(finding.justifies(ReleasePhase.STAGED))
        self.assertFalse(finding.justifies(ReleasePhase.RECEIPTED))

    def test_a_finding_justifies_only_its_own_move(self) -> None:
        self.assertTrue(report(new_id(), RemoteState.LANDED).justifies(ReleasePhase.RECEIPTED))
        self.assertFalse(report(new_id(), RemoteState.LANDED).justifies(ReleasePhase.STAGED))
        self.assertTrue(report(new_id(), RemoteState.NOT_LANDED).justifies(ReleasePhase.STAGED))
        self.assertFalse(report(new_id(), RemoteState.NOT_LANDED).justifies(ReleasePhase.PUBLISHED))

    def test_an_inspection_is_about_a_destination(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            report(new_id(), destination=ref(EntityKind.RELEASE))
        self.assertIn("must point at a DESTINATION", str(caught.exception))


class ReleaseTransactionTests(unittest.TestCase):
    """§15.1's declaration: which accepted candidate, which package, where."""

    def test_a_release_snapshot_is_not_the_candidate_renamed(self) -> None:
        ledger, _ = begin()
        claims = ledger.transaction.to_payload()
        claims["release_snapshot_id"] = claims["candidate_snapshot_id"]
        with self.assertRaises(ReleaseError) as caught:
            ReleaseTransaction(**claims)
        self.assertIn("candidate snapshot unchanged", str(caught.exception))

    def test_the_promotion_ref_is_an_evidence_bundle(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            begin(promotion_bundle_ref=ref(EntityKind.RECEIPT))
        self.assertIn("only a §8 bundle", str(caught.exception))

    def test_delivery_evidence_names_the_package_and_the_destination(self) -> None:
        ledger, _ = begin()
        self.assertEqual(
            ledger.transaction.delivery_evidence(),
            (
                ExternalRef(kind=EntityKind.RELEASE, reference=ledger.release_id),
                ExternalRef(kind=EntityKind.SNAPSHOT, reference=ledger.transaction.release_snapshot_id),
                DEST,
            ),
        )

    def test_begin_release_only_from_an_accepted_production(self) -> None:
        production_id = new_id()
        ledger = ProductionLedger(production_id, initial_vector(production_id))
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        with self.assertRaises(ReleaseError) as caught:
            begin_release(ledger, release_snapshot_id=new_id(), destination=DEST, actor=SHIPPER)
        self.assertIn("nothing to prepare", str(caught.exception))

    def test_begin_release_asks_who_is_shipping(self) -> None:
        """Whoever judged the candidate is not automatically whoever delivers it."""

        with self.assertRaises(ReleaseError) as caught:
            begin(actor=None)
        self.assertIn("names the component", str(caught.exception))

    def test_begin_release_expects_the_ledger_not_a_vector_of_one(self) -> None:
        ledger, production = begin()
        with self.assertRaises(SchemaValidationError):
            begin_release(production.current, release_snapshot_id=new_id(), destination=DEST, actor=SHIPPER)
        self.assertEqual(ledger.production_id, production.production_id)

    def test_the_project_is_carried_from_the_production_when_nobody_names_another(self) -> None:
        ledger, production = begin()
        self.assertEqual(ledger.transaction.project_id, production.current.project_id)


class PhaseEvidenceTests(unittest.TestCase):
    """Each target phase owes the evidence its own name states."""

    def test_gating_without_a_decision_cites_nothing(self) -> None:
        ledger, _ = begin()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(ReleasePhase.GATED, now_ms=NOW)
        self.assertIn("cites no decision", str(caught.exception))

    def test_staging_names_a_package(self) -> None:
        ledger, _, _ = gated()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(ReleasePhase.STAGED, evidence_refs=(ref(EntityKind.POLICY),), now_ms=NOW)
        self.assertIn("staged nothing", str(caught.exception))

    def test_submitting_without_an_external_effect_is_not_submitting(self) -> None:
        ledger = staged()
        with self.assertRaises(ReleaseError) as caught:
            ledger.submit((), now_ms=NOW)
        self.assertIn("performs external effects", str(caught.exception))
        with self.assertRaises(ReleaseError) as entered:
            ledger.advance(ReleasePhase.SUBMITTED, now_ms=NOW)
        self.assertIn("no external action", str(entered.exception))

    def test_a_submit_may_not_arrive_with_the_receipt_already_in_hand(self) -> None:
        ledger = staged()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(ReleasePhase.SUBMITTED, actions=(landed(action()),), now_ms=NOW)
        self.assertIn("already landed", str(caught.exception))

    def test_receipting_an_unresolved_action_is_not_reconciliation(self) -> None:
        ledger, _ = submitted()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(
                ReleasePhase.RECEIPTED,
                actions=(action(state=ExternalEffectState.RECONCILIATION_REQUIRED, key="key-two"),),
                now_ms=NOW,
            )
        self.assertIn("still unresolved", str(caught.exception))

    def test_publication_needs_the_success_it_claims(self) -> None:
        ledger, _ = receipted()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(ReleasePhase.PUBLISHED, actions=(action(key="key-two"),), now_ms=NOW)
        self.assertIn("without success criteria", str(caught.exception))

    def test_a_landed_state_without_a_remote_identifier_is_not_a_landing(self) -> None:
        ledger, arrived = receipted()
        with self.assertRaises(ReleaseError) as caught:
            restated(arrived, external_receipt_ref=None)
        self.assertIn("no remote receipt", str(caught.exception))

    def test_ambiguity_is_reported_never_chosen(self) -> None:
        ledger = staged()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(ReleasePhase.UNKNOWN, actions=(action(),), now_ms=NOW)
        self.assertIn("not chosen for comfort", str(caught.exception))

    def test_leaving_unknown_requires_the_inspection_that_answered(self) -> None:
        ledger, _ = ambiguous()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(ReleasePhase.STAGED, evidence_refs=(package_ref(),), now_ms=NOW)
        self.assertIn("leaves UNKNOWN on nothing", str(caught.exception))

    def test_a_step_may_not_move_further_than_the_inspection_said(self) -> None:
        ledger, pending = ambiguous()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(
                ReleasePhase.STAGED,
                evidence_refs=(package_ref(),),
                report=report(ledger.release_id, RemoteState.LANDED),
                actions=(restated(pending, state=ExternalEffectState.NOT_APPLIED),),
                now_ms=NOW,
            )
        self.assertIn("the inspection decided the destination", str(caught.exception))


class StepChainTests(unittest.TestCase):
    """History is appended, the parent is the head, and a step proves what its receipt proves."""

    def test_history_is_appended_not_spliced_in(self) -> None:
        ledger = staged()
        with self.assertRaises(ReleaseError) as caught:
            ledger.record(hand_step(ledger, from_phase=ReleasePhase.GATED))
        self.assertIn("history is appended", str(caught.exception))

    def test_a_step_cites_the_current_head_as_its_parent(self) -> None:
        ledger, _, _ = gated()
        with self.assertRaises(ReleaseError) as caught:
            ledger.record(hand_step(ledger, causal_parent_receipt_id=new_id()))
        self.assertIn("while the head is", str(caught.exception))

    def test_a_step_about_another_release_is_not_evidence_here(self) -> None:
        ledger, _, _ = gated()
        other, _ = begin()
        with self.assertRaises(ReleaseError) as caught:
            ledger.record(hand_step(ledger, release_id=other.release_id))
        self.assertIn("cannot be recorded on", str(caught.exception))

    def test_a_step_about_another_production_is_refused(self) -> None:
        ledger, _, _ = gated()
        other, _ = begin()
        with self.assertRaises(ReleaseError) as caught:
            ledger.record(hand_step(ledger, production_id=other.production_id))
        self.assertIn("on the release ledger of", str(caught.exception))

    def test_a_receipt_has_to_prove_the_release_it_is_filed_under(self) -> None:
        fields = dict(
            step_id=new_id(),
            release_id=new_id(),
            production_id=new_id(),
            from_phase=ReleasePhase.PREPARING,
            to_phase=ReleasePhase.GATED,
        )
        with self.assertRaises(ReleaseError) as wrong_kind:
            ReleaseStep(
                **fields,
                evidence_refs=(ref(EntityKind.EVIDENCE),),
                receipt=receipt(fields, entity_kind=EntityKind.SNAPSHOT),
            )
        self.assertIn("someone else's history", str(wrong_kind.exception))
        with self.assertRaises(ReleaseError) as wrong_id:
            ReleaseStep(
                **fields,
                evidence_refs=(ref(EntityKind.EVIDENCE),),
                receipt=receipt(fields, entity_id=new_id()),
            )
        self.assertIn("not the release it is filed under", str(wrong_id.exception))

    def test_a_step_and_its_receipt_describe_the_same_move(self) -> None:
        fields = dict(
            step_id=new_id(),
            release_id=new_id(),
            production_id=new_id(),
            from_phase=ReleasePhase.PREPARING,
            to_phase=ReleasePhase.GATED,
        )
        with self.assertRaises(ReleaseError) as caught:
            ReleaseStep(
                **fields,
                evidence_refs=(ref(EntityKind.EVIDENCE),),
                receipt=receipt(
                    fields,
                    from_state=ReleasePhase.GATED.value,
                    to_state=ReleasePhase.STAGED.value,
                ),
            )
        self.assertIn("the same move", str(caught.exception))

    def test_a_step_expects_a_transition_receipt_not_a_description_of_one(self) -> None:
        ledger, _, _ = gated()
        with self.assertRaises(SchemaValidationError):
            ReleaseStep(
                step_id=new_id(),
                release_id=ledger.release_id,
                production_id=ledger.production_id,
                from_phase=ReleasePhase.GATED,
                to_phase=ReleasePhase.STAGED,
                receipt={"transition_id": new_id()},
            )

    def test_a_release_cannot_grow_past_the_admitted_history(self) -> None:
        ledger = staged(maximum=3)
        ledger.submit((action(),), now_ms=NOW)
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(ReleasePhase.RECEIPTED, actions=(landed(action(key="key-two")),), now_ms=NOW)
        self.assertIn("is a workflow", str(caught.exception))

    def test_a_full_ledger_still_answers_its_own_commands(self) -> None:
        """The bound is on new history; re-reading what was already recorded is not growth."""

        ledger, _ = begin(maximum=2)
        bundle = ref(EntityKind.EVIDENCE)
        first = ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), command_id="cmd-full", now_ms=NOW)
        ledger.advance(ReleasePhase.STAGED, evidence_refs=(package_ref(),), now_ms=NOW)
        again = ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), command_id="cmd-full", now_ms=NOW)
        self.assertEqual(again.step_id, first.step_id)
        self.assertEqual(len(ledger), 2)


class GateValidationTests(unittest.TestCase):
    """§15.2 answers the release obligations with the same promotion law as everything else."""

    def test_gating_cites_the_decision_and_the_package_it_validated(self) -> None:
        ledger, request, _ = gated()
        step = ledger.steps[0]
        self.assertIs(step.to_phase, ReleasePhase.GATED)
        self.assertEqual(step.evidence_refs[0].kind, EntityKind.EVIDENCE)
        self.assertIn(DEST, step.evidence_refs)
        self.assertIs(request.requested_phase, Phase.RELEASED)

    def test_a_release_gate_set_is_answered_by_the_lanes_it_declares(self) -> None:
        ledger, production = begin()
        request = release_request(production)
        with self.assertRaises(PromotionBlockedError) as caught:
            ledger.validate_gates(
                request,
                [
                    replace(item, evidence_refs=(ref(EntityKind.PROVENANCE),))
                    if item.kind is GateKind.DELIVERY
                    else item
                    for item in gate_answers(request, ledger)
                ],
                now_ms=NOW,
            )
        self.assertIn("that family is answered by", str(caught.exception))

    def test_a_failing_lane_leaves_the_transaction_preparing(self) -> None:
        ledger, production = begin()
        request = release_request(production)
        answers = [
            replace(item, outcome=GateOutcome.FAIL, reason="the package is not there")
            if item.kind is GateKind.DELIVERY
            else item
            for item in gate_answers(request, ledger)
        ]
        with self.assertRaises(ReleaseError) as caught:
            ledger.validate_gates(request, answers, now_ms=NOW)
        self.assertIn("fails its release gates", str(caught.exception))
        self.assertIs(ledger.phase, ReleasePhase.PREPARING)

    def test_a_blocking_unknown_keeps_the_release_unvalidated(self) -> None:
        ledger, production = begin()
        request = release_request(production)
        with self.assertRaises(ReleaseError) as caught:
            ledger.validate_gates(
                request,
                gate_answers(request, ledger, uncertain=GateKind.PROVENANCE),
                now_ms=NOW,
            )
        self.assertIn("fails its release gates", str(caught.exception))
        self.assertIs(ledger.phase, ReleasePhase.PREPARING)

    def test_a_release_validates_the_gates_of_a_release(self) -> None:
        ledger, _ = begin()
        with self.assertRaises(ReleaseError) as caught:
            ledger.validate_gates(unready_request(), (), now_ms=NOW)
        self.assertIn("ACCEPTED -> RELEASED", str(caught.exception))

    def test_answers_about_another_production_judge_another_delivery(self) -> None:
        ledger, _ = begin()
        request = release_request(accepted())
        with self.assertRaises(ReleaseError) as caught:
            ledger.validate_gates(request, (), now_ms=NOW)
        self.assertIn("another production", str(caught.exception))

    def test_answers_about_another_candidate_are_not_about_this_package(self) -> None:
        production = accepted()
        ledger = ReleaseLedger(
            ReleaseTransaction(
                release_id=new_id(),
                production_id=production.production_id,
                candidate_snapshot_id=new_id(),
                release_snapshot_id=new_id(),
                destination=DEST,
                actor=SHIPPER,
            )
        )
        with self.assertRaises(ReleaseError) as caught:
            ledger.validate_gates(release_request(production), (), now_ms=NOW)
        self.assertIn("packages", str(caught.exception))

    def test_answers_about_another_destination_are_not_about_this_one(self) -> None:
        ledger, production = begin()
        request = replace(release_request(production), release_target=OTHER_DEST)
        with self.assertRaises(ReleaseError) as caught:
            ledger.validate_gates(request, (), now_ms=NOW)
        self.assertIn("prepared for", str(caught.exception))

    def test_validate_gates_expects_the_request_itself(self) -> None:
        ledger, _ = begin()
        with self.assertRaises(SchemaValidationError):
            ledger.validate_gates(ledger.transaction, (), now_ms=NOW)

    def test_the_gate_set_is_validated_once(self) -> None:
        ledger, request, _ = gated()
        with self.assertRaises(LifecycleError) as caught:
            ledger.validate_gates(request, gate_answers(request, ledger), now_ms=NOW)
        self.assertIn("not a legal transition", str(caught.exception))


class SubmitAndPublishTests(unittest.TestCase):
    """The honest path through §15, walked once and replayed."""

    def test_the_happy_path_ends_published_and_proven(self) -> None:
        ledger, _ = published()
        self.assertIs(ledger.phase, ReleasePhase.PUBLISHED)
        self.assertTrue(ledger.prove_state().is_proven)
        self.assertIs(ledger.replay(), ReleasePhase.PUBLISHED)
        self.assertIn(ledger.transaction.snapshot_ref, ledger.delivery_evidence())
        self.assertTrue(all(item.landed for item in ledger.current_actions()))

    def test_delivery_evidence_needs_a_staged_package(self) -> None:
        ledger, _, _ = gated()
        with self.assertRaises(ReleaseError) as caught:
            ledger.delivery_evidence()
        self.assertIn("has staged nothing", str(caught.exception))
        self.assertEqual(ledger.transaction.delivery_evidence()[0].kind, EntityKind.RELEASE)

    def test_side_effect_evidence_names_every_action_asked(self) -> None:
        ledger, first = submitted()
        self.assertEqual(ledger.side_effect_evidence(), (first.reference,))

    def test_the_phase_is_recomputed_from_the_steps_not_from_the_last_call(self) -> None:
        ledger, _ = published()
        rebuilt = ReleaseLedger(ledger.transaction, ledger.steps)
        self.assertIs(rebuilt.phase, ReleasePhase.PUBLISHED)
        self.assertIs(rebuilt.replay(), ledger.replay())
        self.assertEqual(rebuilt.head_receipt_id, ledger.head_receipt_id)
        self.assertEqual(rebuilt.steps, ledger.steps)

    def test_replaying_a_reversed_history_is_refused(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            ReleaseLedger(ledger.transaction, tuple(reversed(ledger.steps)))
        self.assertIn("history is appended", str(caught.exception))

    def test_a_rewritten_step_is_refused_by_its_own_receipt(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            replace(ledger.steps[2], to_phase=ReleasePhase.UNKNOWN)
        self.assertIn("the same move", str(caught.exception))

    def test_a_proof_of_a_release_that_no_longer_describes_itself_is_not_a_proof(self) -> None:
        with self.assertRaises(ReleaseError) as caught:
            ReleaseProof(
                release_id=new_id(),
                recorded_phase=ReleasePhase.STAGED,
                replayed_phase=ReleasePhase.SUBMITTED,
            )
        self.assertIn("no longer backs its state", str(caught.exception))

    def test_a_proof_counts_the_history_it_replayed(self) -> None:
        ledger, _ = published()
        proof = ledger.prove_state()
        self.assertEqual(proof.steps, len(ledger.steps))
        self.assertEqual(proof.head_receipt_id, ledger.steps[-1].receipt.transition_id)
        self.assertTrue(proof.is_proven)


class AmbiguityTests(unittest.TestCase):
    """§15: an unresolved submit is a state, and only an inspection ends it."""

    def test_an_unresolved_submit_moves_the_transaction_in_one_step(self) -> None:
        ledger, pending = ambiguous()
        self.assertIs(ledger.phase, ReleasePhase.UNKNOWN)
        self.assertIs(ledger.steps[-1].to_phase, ReleasePhase.UNKNOWN)
        self.assertEqual(ledger.steps[-1].receipt.reason_code, "external-state-unknown")
        self.assertEqual(ledger.current_actions(), (pending,))

    def test_the_law_refuses_to_resubmit_past_an_unanswered_ambiguity(self) -> None:
        ledger, _ = ambiguous()
        with self.assertRaises(LifecycleError) as caught:
            ledger.submit((action(),), now_ms=NOW)
        self.assertIn("UNKNOWN -> SUBMITTED is not a legal transition", str(caught.exception))

    def test_a_report_that_proves_nothing_keeps_the_transaction_where_it_was(self) -> None:
        ledger, _ = ambiguous()
        finding = report(ledger.release_id, RemoteState.STILL_UNKNOWN)
        self.assertIsNone(ledger.reconcile(finding, now_ms=NOW))
        self.assertIs(ledger.phase, ReleasePhase.UNKNOWN)
        self.assertEqual(len(ledger.reports), 1)
        self.assertEqual(len(ledger.steps), 3)
        self.assertIsNone(ledger.reconcile(finding, now_ms=NOW))
        self.assertEqual(len(ledger.reports), 1)
        self.assertEqual(len(ledger.steps), 3)

    def test_nothing_leaves_unknown_while_an_action_is_still_unresolved(self) -> None:
        ledger, _ = ambiguous()
        with self.assertRaises(ReleaseError) as caught:
            ledger.reconcile(report(ledger.release_id, RemoteState.NOT_LANDED), now_ms=NOW)
        self.assertIn("still unresolved", str(caught.exception))
        self.assertIs(ledger.phase, ReleasePhase.UNKNOWN)

    def test_a_landed_finding_receipts_without_repeating_the_publish(self) -> None:
        ledger, pending = ambiguous()
        answered = landed(pending)
        step = ledger.reconcile(report(ledger.release_id), actions=(answered,), now_ms=NOW)
        self.assertIs(step.to_phase, ReleasePhase.RECEIPTED)
        self.assertIs(ledger.phase, ReleasePhase.RECEIPTED)
        ledger.advance(ReleasePhase.PUBLISHED, actions=(answered,), now_ms=NOW)
        self.assertIs(ledger.phase, ReleasePhase.PUBLISHED)
        self.assertEqual(len([item for item in ledger.actions() if item.landed]), 2)

    def test_an_answered_finding_returns_to_the_package_and_lets_a_retry_run(self) -> None:
        ledger, pending = ambiguous()
        answered = restated(pending, state=ExternalEffectState.NOT_APPLIED)
        step = ledger.reconcile(report(ledger.release_id, RemoteState.NOT_LANDED), actions=(answered,), now_ms=NOW)
        self.assertIs(step.to_phase, ReleasePhase.STAGED)
        self.assertEqual(ledger.current_actions(), (answered,))
        ledger.submit((answered,), now_ms=NOW)
        self.assertIs(ledger.phase, ReleasePhase.SUBMITTED)

    def test_reconciliation_answers_only_an_ambiguity_this_release_has(self) -> None:
        ledger = staged()
        with self.assertRaises(ReleaseError) as caught:
            ledger.reconcile(report(ledger.release_id), now_ms=NOW)
        self.assertIn("does not have", str(caught.exception))

    def test_an_inspection_of_another_destination_is_not_an_inspection_of_this_one(self) -> None:
        ledger, _ = ambiguous()
        with self.assertRaises(ReleaseError) as caught:
            ledger.reconcile(
                report(ledger.release_id, RemoteState.NOT_LANDED, destination=OTHER_DEST),
                now_ms=NOW,
            )
        self.assertIn("not where", str(caught.exception))

    def test_one_report_id_cannot_conclude_two_things(self) -> None:
        ledger, _ = ambiguous()
        first = report(ledger.release_id, RemoteState.STILL_UNKNOWN)
        ledger.reconcile(first, now_ms=NOW)
        with self.assertRaises(StoreConflictError) as caught:
            ledger.reconcile(replace(first, outcome=RemoteState.NOT_LANDED), now_ms=NOW)
        self.assertIn("different conclusion", str(caught.exception))

    def test_a_report_about_another_release_is_not_evidence_here(self) -> None:
        ledger, pending = ambiguous()
        package = ref(EntityKind.ARTIFACT)
        other, _ = begin()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(
                ReleasePhase.STAGED,
                evidence_refs=(package,),
                report=report(other.release_id, RemoteState.NOT_LANDED),
                actions=(restated(pending, state=ExternalEffectState.NOT_APPLIED),),
                now_ms=NOW,
            )
        self.assertIn("reconciliation report about release", str(caught.exception))

    def test_the_step_that_leaves_unknown_carries_the_report_as_evidence(self) -> None:
        ledger, pending = ambiguous()
        finding = report(ledger.release_id, RemoteState.NOT_LANDED)
        step = ledger.reconcile(finding, actions=(restated(pending, state=ExternalEffectState.NOT_APPLIED),), now_ms=NOW)
        self.assertEqual(step.report, finding)
        self.assertIn(finding.reference, step.evidence_refs)
        self.assertEqual(step.receipt.reason_code, "reconciled")

    def test_the_ambiguous_submit_remains_the_only_record_of_the_lost_response(self) -> None:
        ledger, pending = ambiguous()
        self.assertEqual(len(ledger.steps[-1].actions), 1)
        self.assertIs(ledger.steps[-1].actions[0], pending)
        self.assertTrue(ledger.steps[-1].actions[0].unresolved)


class BlindRetryTests(unittest.TestCase):
    """D-M02-S05-011: the destination is inspected before a retry, and a key names one request."""

    def test_a_second_publish_under_one_key_is_a_duplicate_not_a_retry(self) -> None:
        ledger, arrived = receipted()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(
                ReleasePhase.PUBLISHED,
                actions=(arrived, action(key=arrived.idempotency_key)),
                now_ms=NOW,
            )
        self.assertIn("already landed", str(caught.exception))

    def test_a_key_still_unresolved_cannot_be_answered_and_retried_at_once(self) -> None:
        ledger, pending = ambiguous()
        with self.assertRaises(ReleaseError) as caught:
            ledger.reconcile(
                report(ledger.release_id, RemoteState.NOT_LANDED),
                actions=(restated(pending, state=ExternalEffectState.NOT_APPLIED), action(key=KEY)),
                now_ms=NOW,
            )
        self.assertIn("which is unresolved on this", str(caught.exception))
        self.assertIs(ledger.phase, ReleasePhase.UNKNOWN)

    def test_an_action_id_names_one_request_and_its_identity_does_not_move(self) -> None:
        for name, value in (("destination", OTHER_DEST), ("idempotency_key", "key-something-else")):
            with self.subTest(field=name):
                ledger, pending = ambiguous()
                with self.assertRaises(ReleaseError) as caught:
                    ledger.reconcile(
                        report(ledger.release_id, RemoteState.NOT_LANDED),
                        actions=(restated(pending, state=ExternalEffectState.NOT_APPLIED, **{name: value}),),
                        now_ms=NOW,
                    )
                self.assertIn("re-listed with a different", str(caught.exception))

    def test_a_remote_receipt_cannot_swap_under_a_steady_state(self) -> None:
        ledger, arrived = receipted()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(
                ReleasePhase.PUBLISHED,
                actions=(restated(arrived, external_receipt_ref=ref(EntityKind.PROVENANCE)),),
                now_ms=NOW,
            )
        self.assertIn("without changing its state", str(caught.exception))

    def test_what_the_outside_world_already_saw_is_not_rewritable(self) -> None:
        ledger, arrived = receipted()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(
                ReleasePhase.PUBLISHED,
                actions=(
                    restated(arrived, state=ExternalEffectState.NOT_APPLIED),
                    landed(action(key="key-iris-release-2")),
                ),
                now_ms=NOW,
            )
        self.assertIn("not rewritable by a later step", str(caught.exception))

    def test_work_may_not_be_sent_somewhere_the_release_never_named(self) -> None:
        ledger = staged()
        with self.assertRaises(ReleaseError) as caught:
            ledger.record(
                hand_step(
                    ledger,
                    to_phase=ReleasePhase.SUBMITTED,
                    evidence_refs=(),
                    actions=(action(destination=OTHER_DEST),),
                )
            )
        self.assertIn("delivers to the destination it named", str(caught.exception))

    def test_a_reconciliation_of_another_destination_is_refused_where_it_is_made(self) -> None:
        ledger, pending = ambiguous()
        with self.assertRaises(ReleaseError) as caught:
            ledger.advance(
                ReleasePhase.RECEIPTED,
                report=report(ledger.release_id, destination=OTHER_DEST, evidence_refs=(ref(EntityKind.PROVENANCE),)),
                actions=(landed(pending),),
                now_ms=NOW,
            )
        self.assertIn("not where", str(caught.exception))


class CommandIdempotencyTests(unittest.TestCase):
    """D-M02-S05-018: a transition command is idempotent or detectably conflicting."""

    def test_a_command_already_honoured_is_answered_from_history(self) -> None:
        ledger, _ = begin()
        bundle = ref(EntityKind.EVIDENCE)
        first = ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), command_id="cmd-1", now_ms=NOW)
        again = ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), command_id="cmd-1", now_ms=NOW)
        self.assertEqual(first.step_id, again.step_id)
        self.assertEqual(len(ledger), 1)

    def test_a_retry_is_anchored_where_the_original_left_the_release(self) -> None:
        ledger, _ = begin()
        bundle = ref(EntityKind.EVIDENCE)
        first = ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), command_id="cmd-1", now_ms=NOW)
        ledger.advance(ReleasePhase.STAGED, evidence_refs=(package_ref(),), now_ms=NOW)
        replayed = ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), command_id="cmd-1", now_ms=NOW)
        self.assertEqual(replayed.step_id, first.step_id)
        self.assertIs(ledger.phase, ReleasePhase.STAGED)
        self.assertEqual(len(ledger), 2)

    def test_one_command_cannot_carry_two_meanings(self) -> None:
        ledger, _ = begin()
        ledger.advance(ReleasePhase.GATED, evidence_refs=(ref(EntityKind.EVIDENCE),), command_id="cmd-1", now_ms=NOW)
        with self.assertRaises(StoreConflictError) as caught:
            ledger.advance(
                ReleasePhase.GATED,
                evidence_refs=(ref(EntityKind.EVIDENCE),),
                command_id="cmd-1",
                now_ms=NOW,
            )
        self.assertIn("already recorded", str(caught.exception))

    def test_a_step_without_a_command_is_never_answered_as_a_replay(self) -> None:
        """Idempotency is a property of a named command, not of similar-looking content."""

        ledger, _ = begin()
        bundle = ref(EntityKind.EVIDENCE)
        ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), now_ms=NOW)
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(ReleasePhase.GATED, evidence_refs=(bundle,), now_ms=NOW)
        self.assertIn("not a legal transition", str(caught.exception))

    def test_a_command_names_the_step_it_created(self) -> None:
        ledger, _ = begin()
        step = ledger.advance(
            ReleasePhase.GATED,
            evidence_refs=(ref(EntityKind.EVIDENCE),),
            command_id="cmd-9",
            now_ms=NOW,
        )
        self.assertEqual(step.command_id, "cmd-9")
        self.assertEqual(step.receipt.transition_id, step.step_id)
        self.assertIsNotNone(step.receipt.command_digest)
        self.assertIsNone(ledger.steps[0].causal_parent_receipt_id)


class WithdrawalTests(unittest.TestCase):
    """§16: a recall is appended beside the release, and the published step stays."""

    def test_a_withdrawal_recalls_the_exact_release_it_names(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            ledger.withdraw(withdrawal(ledger, release_id=new_id()))
        self.assertIn("not", str(caught.exception))
        with self.assertRaises(ReleaseError) as other:
            ledger.withdraw(withdrawal(ledger, release_snapshot_id=new_id()))
        self.assertIn("§16 keeps the exact release", str(other.exception))

    def test_a_withdrawal_that_asks_for_nothing_is_an_opinion(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            withdrawal(ledger, requested_actions=())
        self.assertIn("requests no action", str(caught.exception))

    def test_a_recall_without_provenance_preserves_nothing(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            withdrawal(ledger, provenance_refs=())
        self.assertIn("cites none", str(caught.exception))

    def test_a_superseding_recall_names_the_replacement(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            withdrawal(ledger, reason=WithdrawalReason.SUPERSEDING_RELEASE)
        self.assertIn("names no replacement", str(caught.exception))

    def test_withdrawal_is_not_deletion(self) -> None:
        ledger, _ = published()
        before = ledger.steps
        receipt = ledger.withdraw(withdrawal(ledger))
        self.assertIs(receipt.destination_state, WithdrawalState.WITHDRAWN)
        self.assertIs(ledger.phase, ReleasePhase.PUBLISHED)
        self.assertEqual(ledger.steps, before)
        self.assertTrue(ledger.is_withdrawn)
        self.assertEqual(len(ledger.withdrawals), 1)
        self.assertEqual(ledger.prove_state().steps, len(before))

    def test_a_recall_asked_of_the_wrong_destination_is_not_a_recall(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            ledger.withdraw(
                withdrawal(ledger, requested_actions=(landed(action(destination=OTHER_DEST, key="key-two")),))
            )
        self.assertIn("take down a release", str(caught.exception))

    def test_the_same_recall_written_twice_is_one_fact(self) -> None:
        ledger, _ = published()
        first = ledger.withdraw(withdrawal(ledger))
        self.assertEqual(ledger.withdraw(replace(first)), first)
        with self.assertRaises(StoreConflictError) as caught:
            ledger.withdraw(replace(first, statement="a different account of the same recall"))
        self.assertIn("different content", str(caught.exception))

    def test_there_is_nothing_to_withdraw_before_the_destination_saw_anything(self) -> None:
        ledger, _, _ = gated()
        with self.assertRaises(ReleaseError) as caught:
            ledger.withdraw(withdrawal(ledger))
        self.assertIn("invent history", str(caught.exception))

    def test_the_destination_state_reports_what_the_actions_answered(self) -> None:
        ledger, _ = published()
        half = (landed(action(key="key-w-1")), action(state=ExternalEffectState.RECONCILIATION_REQUIRED, key="key-w-2"))
        self.assertIs(
            ledger.withdraw(withdrawal(ledger, requested_actions=half)).destination_state,
            WithdrawalState.UNRESOLVED,
        )
        other, _ = published()
        self.assertIs(
            other.withdraw(
                withdrawal(other, requested_actions=(landed(action(key="key-w-3")), action(key="key-w-4")))
            ).destination_state,
            WithdrawalState.PARTIAL,
        )
        third, _ = published()
        self.assertIs(
            third.withdraw(withdrawal(third, requested_actions=(action(key="key-w-5"),))).destination_state,
            WithdrawalState.STILL_PUBLIC,
        )

    def test_a_recall_of_another_productions_release_is_refused(self) -> None:
        ledger, _ = published()
        with self.assertRaises(ReleaseError) as caught:
            ledger.withdraw(withdrawal(ledger, production_id=new_id()))
        self.assertIn("another production", str(caught.exception))


class SupersessionRegistryTests(unittest.TestCase):
    """§17: exact refs never move; only where a future consumer is pointed does."""

    def test_exact_lookups_never_follow_supersession(self) -> None:
        first, _ = published()
        second, _ = published()
        registry = ReleaseRegistry()
        registry.register(first)
        registry.register(second)
        registry.supersede(first.release_id, second.release_id, reason_code="newer-master")
        self.assertEqual(registry.exact(first.release_id), first.transaction)
        self.assertTrue(registry.is_superseded(first.release_id))

    def test_preferred_walks_the_chain_over_published_work(self) -> None:
        first, _ = published()
        second, _ = published()
        third, _ = published()
        registry = ReleaseRegistry()
        for ledger in (first, second, third):
            registry.register(ledger)
        registry.supersede(first.release_id, second.release_id, reason_code="rev-one")
        registry.supersede(second.release_id, third.release_id, reason_code="rev-two")
        self.assertEqual(registry.preferred(first.release_id), third.transaction)
        self.assertEqual(len(registry.chain_of(first.release_id)), 2)
        self.assertEqual(len(registry.records), 2)

    def test_an_unpublished_replacement_hides_the_work_instead_of_replacing_it(self) -> None:
        first, _ = published()
        registry = ReleaseRegistry()
        registry.register(first)
        draft, _ = begin()
        with self.assertRaises(ReleaseError) as unknown:
            registry.supersede(first.release_id, draft.release_id, reason_code="promised")
        self.assertIn("not a release this registry knows", str(unknown.exception))
        registry.register(draft)
        with self.assertRaises(ReleaseError) as unshipped:
            registry.supersede(first.release_id, draft.release_id, reason_code="promised")
        self.assertIn("has not published", str(unshipped.exception))

    def test_a_withdrawn_replacement_stops_being_the_preferred_one(self) -> None:
        first, _ = published()
        second, _ = published()
        registry = ReleaseRegistry()
        registry.register(first)
        registry.register(second)
        registry.supersede(first.release_id, second.release_id, reason_code="revoked-soon")
        self.assertEqual(registry.preferred(first.release_id), second.transaction)
        second.withdraw(withdrawal(second))
        registry.register(second)
        self.assertEqual(registry.preferred(first.release_id), first.transaction)

    def test_policy_bounds_the_walk(self) -> None:
        first, _ = published()
        second, _ = published()
        registry = ReleaseRegistry()
        registry.register(first)
        registry.register(second)
        registry.supersede(first.release_id, second.release_id, reason_code="not-admitted-here")
        self.assertEqual(registry.preferred(first.release_id, admitted=(first.release_id,)), first.transaction)
        self.assertEqual(registry.preferred(first.release_id, admitted=(second.release_id,)), second.transaction)

    def test_a_record_cannot_be_superseded_twice(self) -> None:
        first, _ = published()
        second, _ = published()
        third, _ = published()
        registry = ReleaseRegistry()
        for ledger in (first, second, third):
            registry.register(ledger)
        registry.supersede(first.release_id, second.release_id, reason_code="one")
        with self.assertRaises(IdentityError) as caught:
            registry.supersede(first.release_id, third.release_id, reason_code="two")
        self.assertIn("superseded twice", str(caught.exception))
        self.assertEqual(registry.preferred(first.release_id), second.transaction)

    def test_registering_the_same_release_twice_is_not_a_second_release(self) -> None:
        first, _ = published()
        registry = ReleaseRegistry()
        registry.register(first)
        self.assertEqual(registry.known, (first.release_id,))
        self.assertEqual(registry.register(first), first.transaction)
        with self.assertRaises(StoreConflictError) as caught:
            registry.register(
                ReleaseLedger(replace(first.transaction, release_snapshot_id=new_id()), first.steps)
            )
        self.assertIn("different claims", str(caught.exception))

    def test_the_registry_only_knows_ledgers(self) -> None:
        registry = ReleaseRegistry()
        with self.assertRaises(SchemaValidationError):
            registry.register("not a ledger")
        with self.assertRaises(ReleaseError):
            registry.exact(new_id())


class ProductionCompositionTests(unittest.TestCase):
    """The transaction records what the destination holds; the promotion decides what that means."""

    def test_the_release_transaction_moves_only_the_delivery_region(self) -> None:
        production = accepted()
        ledger = staged(production=production)
        move = sync_release_state(production, ledger, actor=SHIPPER, now_ms=NOW)
        self.assertIsNotNone(move)
        self.assertIs(production.current.release_condition, ReleaseCondition.STAGED)
        self.assertIs(production.current.phase, Phase.ACCEPTED)

    def test_syncing_twice_is_not_a_second_transition(self) -> None:
        production = accepted()
        ledger = staged(production=production)
        sync_release_state(production, ledger, actor=SHIPPER, now_ms=NOW)
        recorded = len(production)
        self.assertIsNone(sync_release_state(production, ledger, actor=SHIPPER, now_ms=NOW))
        self.assertEqual(len(production), recorded)

    def test_an_ambiguity_owes_the_production_nothing(self) -> None:
        production = accepted()
        ledger, _ = ambiguous(production=production)
        self.assertIsNone(sync_release_state(production, ledger, actor=SHIPPER, now_ms=NOW))
        self.assertIs(production.current.release_condition, ReleaseCondition.UNRELEASED)

    def test_a_release_of_another_production_cannot_state_this_ones_delivery(self) -> None:
        production = accepted()
        other, _ = begin()
        with self.assertRaises(ReleaseError) as caught:
            sync_release_state(production, other, actor=SHIPPER, now_ms=NOW)
        self.assertIn("cannot state the delivery of", str(caught.exception))

    def test_publication_is_refused_below_released(self) -> None:
        production = accepted()
        with self.assertRaises(LifecycleError) as caught:
            production.advance(actor=SHIPPER, release_condition=ReleaseCondition.PUBLISHED)
        self.assertIn("PUBLISHED", str(caught.exception))

    def test_a_delivery_judgement_then_the_proven_publication(self) -> None:
        """ACCEPTED -> RELEASED on the gates, and only then the destination fact on file."""

        production = accepted()
        release, _ = published(production=production)
        request = release_request(production)
        decision = promote(
            production,
            request,
            gate_answers(request, release),
            delivery_refs=release.delivery_evidence(),
            rights_refs=(ref(EntityKind.RIGHTS),),
            provenance_refs=(ref(EntityKind.PROVENANCE),),
            release_snapshot_id=release.transaction.release_snapshot_id,
            now_ms=NOW,
        )
        self.assertTrue(decision.admitted)
        self.assertIs(production.current.phase, Phase.RELEASED)
        sync_release_state(production, release, actor=SHIPPER, now_ms=NOW)
        self.assertIs(production.current.release_condition, ReleaseCondition.PUBLISHED)
        self.assertEqual(production.current.release_snapshot_id, release.transaction.release_snapshot_id)

    def test_a_recall_lands_on_the_production_without_touching_its_history(self) -> None:
        production = accepted()
        release, _ = published(production=production)
        request = release_request(production)
        promote(
            production,
            request,
            gate_answers(request, release),
            delivery_refs=release.delivery_evidence(),
            rights_refs=(ref(EntityKind.RIGHTS),),
            provenance_refs=(ref(EntityKind.PROVENANCE),),
            release_snapshot_id=release.transaction.release_snapshot_id,
            now_ms=NOW,
        )
        sync_release_state(production, release, actor=SHIPPER, now_ms=NOW)
        release.withdraw(withdrawal(release))
        sync_release_state(production, release, actor=SHIPPER, now_ms=NOW)
        self.assertIs(production.current.release_condition, ReleaseCondition.WITHDRAWN)
        self.assertIs(production.current.phase, Phase.RELEASED)
        self.assertIs(release.phase, ReleasePhase.PUBLISHED)

    def test_a_late_sync_records_the_staging_it_never_recorded(self) -> None:
        """PUBLISHED is still owed the STAGED move the production missed, so the sync walks there."""

        production = accepted()
        release, _ = published(production=production)
        request = release_request(production)
        promote(
            production,
            request,
            gate_answers(request, release),
            delivery_refs=release.delivery_evidence(),
            rights_refs=(ref(EntityKind.RIGHTS),),
            provenance_refs=(ref(EntityKind.PROVENANCE),),
            release_snapshot_id=release.transaction.release_snapshot_id,
            now_ms=NOW,
        )
        recorded = len(production)
        sync_release_state(production, release, actor=SHIPPER, now_ms=NOW)
        self.assertEqual(len(production), recorded + 2)
        self.assertEqual(
            [item.to_vector.release_condition for item in production.history[recorded:]],
            [ReleaseCondition.STAGED, ReleaseCondition.PUBLISHED],
        )
        self.assertIs(production.current.phase, Phase.RELEASED)

    def test_a_sync_obeys_the_transaction_rather_than_the_callers_claim(self) -> None:
        production = accepted()
        ledger = staged(production=production)
        with self.assertRaises(ReleaseError) as caught:
            sync_release_state(
                production,
                ledger,
                actor=SHIPPER,
                now_ms=NOW,
                release_condition=ReleaseCondition.PUBLISHED,
            )
        self.assertIn("proves", str(caught.exception))
        self.assertIs(production.current.release_condition, ReleaseCondition.UNRELEASED)

    def test_a_recall_of_an_unpublished_release_does_not_invent_a_publication(self) -> None:
        """The destination did hold the package, so the recall is real; the publication never was."""

        production = accepted()
        ledger, _ = receipted(production=production)
        sync_release_state(production, ledger, actor=SHIPPER, now_ms=NOW)
        ledger.withdraw(withdrawal(ledger))
        self.assertTrue(ledger.is_withdrawn)
        self.assertIsNone(sync_release_state(production, ledger, actor=SHIPPER, now_ms=NOW))
        self.assertIs(production.current.release_condition, ReleaseCondition.STAGED)

    def test_syncing_expects_the_two_ledgers_it_binds(self) -> None:
        production = accepted()
        ledger = staged(production=production)
        with self.assertRaises(SchemaValidationError):
            sync_release_state(ledger, ledger, actor=SHIPPER)
        with self.assertRaises(SchemaValidationError):
            sync_release_state(production, production, actor=SHIPPER)


if __name__ == "__main__":
    unittest.main()
