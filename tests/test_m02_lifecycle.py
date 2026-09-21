"""Área E: the production state vector, the law over it, and the ledger that replays it.

Three claims organize these tests. A state is four orthogonal answers that must agree with
each other; a move is legal only when the table, the authority and the receipt all agree;
and current state is whatever durable history replays to, never whatever a caller last said.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_project_os.errors import LifecycleError, SchemaValidationError, StoreConflictError
from iris_project_os.identity import EntityKind, ExternalRef, new_id
from iris_project_os.lifecycle import (
    LIFECYCLE_TABLES,
    PRODUCTION_EXECUTION,
    PRODUCTION_PHASES,
    PRODUCTION_RELEASE,
    PRODUCTION_REVIEW,
    AuthorizedJump,
    Blocker,
    BlockerKind,
    BlockerLedger,
    CompletionProfile,
    Execution,
    Phase,
    ProductionLedger,
    ProductionStateVector,
    Release,
    Review,
    StateTransition,
    TransitionProfile,
    advance,
    attempt_outcome,
    completion_of,
    initial_vector,
    lifecycle_tables,
    phase_at_least,
    phase_rank,
    start_attempt,
)
from iris_project_os.versions import ComponentVersion, content_digest

ACTOR = ComponentVersion("m02.test", "1.0.0")
JUDGE = ComponentVersion("m02.judge", "2.0.0")
NOW = 1_700_000_000_000
LADDER = (
    Phase.DRAFT,
    Phase.PLANNED,
    Phase.READY,
    Phase.MATERIALIZED,
    Phase.VALIDATING,
    Phase.ACCEPTED,
    Phase.RELEASED,
    Phase.SUPERSEDED,
    Phase.ARCHIVED,
)


def ref(kind: EntityKind = EntityKind.RECEIPT) -> ExternalRef:
    return ExternalRef(kind=kind, reference=new_id())


def web_profile(**over: Any) -> TransitionProfile:
    base: dict[str, Any] = dict(
        profile_id="profile.web",
        terminal_phase=Phase.RELEASED,
        obligations=("release published",),
        human_review_phases=(Phase.ACCEPTED,),
    )
    base.update(over)
    return TransitionProfile(**base)


def fastlane_profile(**over: Any) -> TransitionProfile:
    base: dict[str, Any] = dict(
        profile_id="profile.fastlane",
        terminal_phase=Phase.RELEASED,
        obligations=("a waived candidate phase is still judged on evidence",),
        jumps=(
            AuthorizedJump(
                source=Phase.READY,
                target=Phase.ACCEPTED,
                proof_refs=(ExternalRef(kind=EntityKind.POLICY, reference="policy.waiver.granted"),),
                obligations=("the candidate is on file",),
            ),
        ),
    )
    base.update(over)
    return TransitionProfile(**base)


def at(production_id: str, profile: TransitionProfile | None = None, **claims: Any) -> ProductionLedger:
    return ProductionLedger(production_id, initial_vector(production_id, **claims), profile=profile)


def ready(profile: TransitionProfile | None = None) -> ProductionLedger:
    """A ledger standing on READY, the rung a waiver is allowed to skip over."""

    ledger = at(new_id(), profile)
    ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
    ledger.advance(actor=ACTOR, phase=Phase.READY)
    return ledger


def walked(profile: TransitionProfile | None = None) -> ProductionLedger:
    """DRAFT to VALIDATING through every rung, so a test starts from a real state."""

    ledger = at(new_id(), profile)
    ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
    ledger.advance(actor=ACTOR, phase=Phase.READY)
    ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
    ledger.advance(actor=ACTOR, phase=Phase.VALIDATING, review="PENDING")
    return ledger


def accepted(profile: TransitionProfile | None = None) -> ProductionLedger:
    ledger = walked(profile)
    ledger.advance(
        actor=ACTOR,
        phase=Phase.ACCEPTED,
        review="APPROVED",
        promotion_ref=ref(),
        review_receipt=ref(),
    )
    return ledger


def released(profile: TransitionProfile | None = None) -> ProductionLedger:
    ledger = accepted(profile)
    ledger.advance(
        actor=ACTOR,
        phase=Phase.RELEASED,
        release_snapshot_id=new_id(),
        release_condition="STAGED",
        promotion_ref=ref(),
    )
    ledger.advance(actor=ACTOR, release_condition="PUBLISHED")
    return ledger


class VectorLawTests(unittest.TestCase):
    def test_a_state_is_four_orthogonal_answers(self) -> None:
        vector = initial_vector(new_id())
        self.assertIs(vector.phase, Phase.DRAFT)
        self.assertIs(vector.execution, Execution.IDLE)
        self.assertIs(vector.review, Review.NOT_REQUESTED)
        self.assertIs(vector.release_condition, Release.UNRELEASED)
        self.assertEqual(vector.summary, "DRAFT/IDLE/NOT_REQUESTED/UNRELEASED")

    def test_states_are_parsed_not_trusted(self) -> None:
        vector = initial_vector(new_id(), phase="planned", execution="blocked", review="pending")
        self.assertIs(vector.phase, Phase.PLANNED)
        self.assertEqual(vector.summary, "PLANNED/BLOCKED/PENDING/UNRELEASED")

    def test_an_unknown_state_names_the_enum_that_refused_it(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            initial_vector(new_id(), phase="ALMOST_DONE")
        self.assertIn("phase must be one of", str(caught.exception))

    def test_a_production_id_is_a_uuid_and_not_a_claim(self) -> None:
        with self.assertRaises(SchemaValidationError):
            initial_vector("production-one")

    def test_every_impossible_vector_is_refused(self) -> None:
        production = new_id()
        cases = {
            "materialized with nothing materialized": dict(phase=Phase.MATERIALIZED),
            "approved before anything exists to review": dict(phase=Phase.VALIDATING, review=Review.APPROVED),
            "staged without being accepted": dict(
                phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id(), release_condition=Release.STAGED
            ),
            "published without being released": dict(
                phase=Phase.ACCEPTED,
                candidate_snapshot_id=new_id(),
                review=Review.APPROVED,
                release_condition=Release.PUBLISHED,
            ),
            "released with no release snapshot": dict(
                phase=Phase.RELEASED,
                candidate_snapshot_id=new_id(),
                review=Review.APPROVED,
                release_condition=Release.UNRELEASED,
            ),
            "superseded by nobody": dict(
                phase=Phase.SUPERSEDED,
                candidate_snapshot_id=new_id(),
                release_snapshot_id=new_id(),
                review=Review.APPROVED,
            ),
            "work running while archived": dict(
                phase=Phase.ARCHIVED,
                candidate_snapshot_id=new_id(),
                release_snapshot_id=new_id(),
                review=Review.APPROVED,
                execution=Execution.ACTIVE,
            ),
            "an attempt on the floor while idle": dict(
                phase=Phase.PLANNED, execution=Execution.IDLE, active_attempt_id=new_id()
            ),
        }
        for label, claims in cases.items():
            with self.subTest(label):
                with self.assertRaises(LifecycleError):
                    initial_vector(production, **claims)

    def test_a_claim_alone_is_never_enough_to_reach_a_phase(self) -> None:
        vector = initial_vector(
            new_id(),
            phase=Phase.RELEASED,
            candidate_snapshot_id=new_id(),
            release_snapshot_id=new_id(),
            review=Review.APPROVED,
            release_condition=Release.PUBLISHED,
        )
        self.assertIs(vector.phase, Phase.RELEASED)
        self.assertTrue(phase_at_least(vector.phase, Phase.ACCEPTED))

    def test_moved_validates_the_whole_vector_not_just_the_change(self) -> None:
        vector = initial_vector(new_id(), phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
        with self.assertRaises(LifecycleError):
            vector.moved(release_condition=Release.STAGED)

    def test_moved_rejects_a_field_that_does_not_exist(self) -> None:
        with self.assertRaises(SchemaValidationError):
            initial_vector(new_id()).moved(phaze=Phase.READY)

    def test_the_vector_survives_a_payload_round_trip(self) -> None:
        vector = initial_vector(
            new_id(),
            phase=Phase.VALIDATING,
            candidate_snapshot_id=new_id(),
            review=Review.PENDING,
            superseded_by_ref=ref(),
        )
        self.assertEqual(ProductionStateVector.from_payload(vector.to_payload()), vector)

    def test_rank_orders_the_ladder_and_at_least_is_inclusive(self) -> None:
        self.assertLess(phase_rank(Phase.DRAFT), phase_rank(Phase.ARCHIVED))
        self.assertTrue(phase_at_least(Phase.ACCEPTED, Phase.ACCEPTED))
        self.assertFalse(phase_at_least(Phase.VALIDATING, Phase.ACCEPTED))


class LadderTests(unittest.TestCase):
    def test_the_table_is_total_over_the_ladder(self) -> None:
        for phase in LADDER:
            with self.subTest(phase.value):
                self.assertIsInstance(PRODUCTION_PHASES.legal_targets(phase), tuple)
        self.assertEqual(
            set(PRODUCTION_PHASES.states), set(LADDER), "the machine must know every phase the ladder has"
        )
        self.assertEqual({item.value for item in PRODUCTION_PHASES.terminals}, {"ARCHIVED"})

    def test_the_ladder_is_reachable_from_draft(self) -> None:
        reachable = set(PRODUCTION_PHASES.reachable(Phase.DRAFT))
        self.assertEqual(reachable, set(LADDER))

    def test_each_rung_admits_exactly_the_next_one(self) -> None:
        for before, after in zip(LADDER, LADDER[1:]):
            with self.subTest(f"{before.value} -> {after.value}"):
                self.assertTrue(PRODUCTION_PHASES.is_legal(before, after))

    def test_archived_is_terminal(self) -> None:
        self.assertTrue(PRODUCTION_PHASES.is_terminal(Phase.ARCHIVED))
        self.assertEqual(PRODUCTION_PHASES.legal_targets(Phase.ARCHIVED), ())

    def test_a_forward_skip_is_refused_even_when_the_target_would_be_coherent(self) -> None:
        ledger = walked()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(
                actor=ACTOR,
                phase=Phase.RELEASED,
                release_snapshot_id=new_id(),
                promotion_ref=ref(),
            )
        self.assertIn("skips a rung with no transition profile", str(caught.exception))
        governed = walked(web_profile())
        with self.assertRaises(LifecycleError) as caught:
            governed.advance(
                actor=ACTOR,
                phase=Phase.RELEASED,
                release_snapshot_id=new_id(),
                promotion_ref=ref(),
            )
        self.assertIn("profile profile.web does not authorize VALIDATING -> RELEASED", str(caught.exception))

    def test_an_impossible_target_is_refused_before_the_ladder_is_consulted(self) -> None:
        ledger = walked()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, phase=Phase.RELEASED, promotion_ref=ref())
        self.assertIn("no release snapshot", str(caught.exception))

    def test_a_walk_backwards_is_refused(self) -> None:
        ledger = accepted()
        with self.assertRaises(LifecycleError):
            ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED)

    def test_a_declared_jump_is_admissible(self) -> None:
        ledger = ready(fastlane_profile())
        ledger.advance(actor=ACTOR, review="PENDING")
        moved = ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            candidate_snapshot_id=new_id(),
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
        )
        self.assertIs(moved.to_vector.phase, Phase.ACCEPTED)
        self.assertEqual(moved.moved_regions, ("review", "phase"))

    def test_a_jump_carries_its_own_proof_into_the_receipt(self) -> None:
        ledger = ready(fastlane_profile())
        ledger.advance(actor=ACTOR, review="PENDING")
        moved = ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            candidate_snapshot_id=new_id(),
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
        )
        self.assertIn(
            "policy.waiver.granted", [item.reference for item in moved.receipt.evidence_refs]
        )

    def test_a_waiver_may_skip_rungs_but_may_not_manufacture_an_approval(self) -> None:
        ledger = ready(fastlane_profile())
        ledger.advance(actor=ACTOR, review="PENDING")
        ledger.advance(actor=ACTOR, phase=Phase.ACCEPTED, candidate_snapshot_id=new_id(), promotion_ref=ref())
        self.assertIs(ledger.current.review, Review.PENDING)
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, review="APPROVED")
        self.assertIn("no review receipt behind it", str(caught.exception))

    def test_a_jump_cannot_license_a_walk_backwards(self) -> None:
        ledger = ready(fastlane_profile())
        ledger.advance(actor=ACTOR, review="PENDING")
        ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            candidate_snapshot_id=new_id(),
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
        )
        with self.assertRaises(LifecycleError):
            ledger.advance(actor=ACTOR, phase=Phase.VALIDATING)

    def test_a_jump_never_crosses_the_acceptance_gate(self) -> None:
        with self.assertRaises(LifecycleError) as caught:
            AuthorizedJump(
                source=Phase.MATERIALIZED,
                target=Phase.RELEASED,
                proof_refs=(ref(EntityKind.POLICY),),
            )
        self.assertIn("acceptance gate is an invariant", str(caught.exception))

    def test_a_jump_that_restates_the_ladder_is_refused(self) -> None:
        with self.assertRaises(LifecycleError):
            AuthorizedJump(source=Phase.VALIDATING, target=Phase.ACCEPTED, proof_refs=(ref(EntityKind.POLICY),))

    def test_a_jump_without_proof_is_refused(self) -> None:
        with self.assertRaises(LifecycleError):
            AuthorizedJump(source=Phase.READY, target=Phase.ACCEPTED, proof_refs=())

    def test_a_jump_out_of_the_archive_is_refused(self) -> None:
        with self.assertRaises(LifecycleError) as caught:
            AuthorizedJump(source=Phase.ARCHIVED, target=Phase.SUPERSEDED, proof_refs=(ref(EntityKind.POLICY),))
        self.assertIn("revival fork", str(caught.exception))

    def test_a_profile_admits_only_what_it_declares(self) -> None:
        profile = fastlane_profile()
        self.assertTrue(profile.admits(Phase.READY, Phase.ACCEPTED))
        self.assertTrue(profile.admits(Phase.ACCEPTED, Phase.RELEASED))
        self.assertFalse(profile.admits(Phase.READY, Phase.RELEASED))
        self.assertIsNone(profile.jump_between(Phase.READY, Phase.RELEASED))

    def test_a_profile_may_not_authorize_the_same_jump_twice(self) -> None:
        jump = AuthorizedJump(source=Phase.READY, target=Phase.ACCEPTED, proof_refs=(ref(EntityKind.POLICY),))
        with self.assertRaises(LifecycleError):
            TransitionProfile(profile_id="profile.twice", jumps=(jump, jump))

    def test_the_whole_law_is_data_that_hashes(self) -> None:
        self.assertEqual(set(lifecycle_tables()), set(LIFECYCLE_TABLES))
        self.assertEqual(content_digest(lifecycle_tables()), content_digest(lifecycle_tables()))
        first = PRODUCTION_PHASES.legal_targets(Phase.DRAFT)
        self.assertEqual(first, PRODUCTION_PHASES.legal_targets(Phase.DRAFT))


class AuthorityTests(unittest.TestCase):
    def test_acceptance_without_a_bundle_is_refused(self) -> None:
        ledger = walked()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, phase=Phase.ACCEPTED, review="APPROVED", review_receipt=ref())
        self.assertIn("promotion evidence bundle", str(caught.exception))

    def test_release_without_a_bundle_is_refused(self) -> None:
        ledger = accepted()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, phase=Phase.RELEASED, release_snapshot_id=new_id())
        self.assertIn("promotion evidence bundle", str(caught.exception))

    def test_supersession_without_a_replacement_is_refused(self) -> None:
        ledger = released()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, phase=Phase.SUPERSEDED, superseded_by_ref=ref())
        self.assertIn("no replacement named", str(caught.exception))

    def test_staying_in_a_governed_phase_does_not_recite_its_evidence(self) -> None:
        ledger = walked()
        ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
        )
        staged = ledger.advance(actor=ACTOR, review="PENDING")
        self.assertIs(staged.to_vector.phase, Phase.ACCEPTED)

    def test_entering_blocked_names_the_blocker(self) -> None:
        ledger = walked()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, execution="BLOCKED")
        self.assertIn("nothing blocking it", str(caught.exception))

    def test_leaving_blocked_names_what_it_cleared(self) -> None:
        ledger = walked()
        blocker = ref()
        ledger.advance(actor=ACTOR, execution="BLOCKED", blocker_ref=blocker)
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, execution="IDLE")
        self.assertIn("erase the fact", str(caught.exception))
        cleared = ledger.advance(actor=ACTOR, execution="IDLE", blocker_ref=blocker)
        self.assertIs(cleared.to_vector.execution, Execution.IDLE)

    def test_a_profile_can_make_human_review_mandatory_on_more_phases(self) -> None:
        strict = web_profile(human_review_phases=(Phase.ACCEPTED, Phase.RELEASED))
        ledger = accepted(strict)
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(
                actor=ACTOR,
                phase=Phase.RELEASED,
                release_snapshot_id=new_id(),
                promotion_ref=ref(),
            )
        self.assertIn("requires a human review receipt to enter RELEASED", str(caught.exception))

    def test_an_approval_retracted_and_regranted_needs_a_fresh_receipt(self) -> None:
        ledger = accepted()
        ledger.advance(actor=ACTOR, review="PENDING")
        ledger.advance(actor=ACTOR, review="CHANGES_REQUIRED")
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, review="APPROVED")
        self.assertIn("rejection is answered by a decision", str(caught.exception))
        granted = ledger.advance(actor=ACTOR, review="APPROVED", review_receipt=ref())
        self.assertIs(granted.to_vector.review, Review.APPROVED)

    def test_a_withdrawal_goes_back_through_pending(self) -> None:
        ledger = accepted()
        with self.assertRaises(LifecycleError):
            ledger.advance(actor=ACTOR, review="CHANGES_REQUIRED")
        self.assertIs(ledger.current.review, Review.APPROVED)
        ledger.advance(actor=ACTOR, review="PENDING")
        self.assertIs(ledger.current.review, Review.PENDING)


class ClaimImmutabilityTests(unittest.TestCase):
    def test_a_claim_may_not_be_repointed_without_moving_state(self) -> None:
        ledger = walked()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, candidate_snapshot_id=new_id())
        self.assertIn("moves no governed state", str(caught.exception))

    def test_a_claim_may_not_be_repointed_during_another_move(self) -> None:
        ledger = accepted()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(
                actor=ACTOR,
                release_condition="STAGED",
                candidate_snapshot_id=new_id(),
            )
        self.assertIn("re-points candidate_snapshot_id", str(caught.exception))

    def test_a_candidate_is_filled_once_and_never_substituted(self) -> None:
        ledger = at(new_id(), web_profile())
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        ledger.advance(actor=ACTOR, phase=Phase.READY)
        moved = ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
        self.assertIsNotNone(moved.to_vector.candidate_snapshot_id)
        with self.assertRaises(LifecycleError):
            ledger.advance(
                actor=ACTOR, phase=Phase.VALIDATING, review="PENDING", candidate_snapshot_id=new_id()
            )


class ReceiptAgreementTests(unittest.TestCase):
    def rebuild(self, transition: StateTransition, **over: Any) -> StateTransition:
        """Re-issue a recorded move with one part of it changed, which is what a forgery is."""

        parts: dict[str, Any] = {
            "transition_id": transition.transition_id,
            "production_id": transition.production_id,
            "from_vector": transition.from_vector,
            "to_vector": transition.to_vector,
            "receipt": transition.receipt,
            "profile": transition.profile,
            "promotion_ref": transition.promotion_ref,
            "review_receipt": transition.review_receipt,
            "replacement_ref": transition.replacement_ref,
            "blocker_ref": transition.blocker_ref,
        }
        parts.update(over)
        return StateTransition(**parts)

    def acceptance(self, ledger: ProductionLedger) -> StateTransition:
        return advance(
            ledger.current,
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
            parent_receipt_id=ledger.head_receipt_id,
        )

    def test_the_receipt_and_the_vectors_describe_the_same_move(self) -> None:
        ledger = walked()
        moved = ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
        )
        self.assertEqual(moved.receipt.from_state, Phase.VALIDATING.value)
        self.assertEqual(moved.receipt.to_state, Phase.ACCEPTED.value)
        self.assertEqual(moved.receipt.entity_id, ledger.production_id)
        self.assertIs(moved.receipt.entity_kind, EntityKind.PRODUCTION)

    def test_a_receipt_for_another_production_is_refused(self) -> None:
        ledger = walked()
        moved = ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
        )
        with self.assertRaises(LifecycleError) as caught:
            self.rebuild(moved, receipt=replace(moved.receipt, entity_id=new_id()))
        self.assertIn("records a receipt for production", str(caught.exception))

    def test_a_receipt_that_disagrees_about_where_it_came_from_is_refused(self) -> None:
        ledger = walked()
        moved = self.acceptance(ledger)
        with self.assertRaises(LifecycleError) as caught:
            self.rebuild(moved, receipt=replace(moved.receipt, from_state=Phase.DRAFT.value))
        self.assertIn("the vector came from", str(caught.exception))

    def test_a_receipt_filed_against_an_attempt_is_refused(self) -> None:
        ledger = walked()
        moved = self.acceptance(ledger)
        with self.assertRaises(LifecycleError) as caught:
            self.rebuild(moved, receipt=replace(moved.receipt, entity_kind=EntityKind.ATTEMPT))
        self.assertIn("not a production", str(caught.exception))

    def test_a_receipt_carrying_another_transitions_identity_is_refused(self) -> None:
        ledger = walked()
        moved = self.acceptance(ledger)
        with self.assertRaises(LifecycleError) as caught:
            self.rebuild(moved, receipt=replace(moved.receipt, transition_id=new_id()))
        self.assertIn("carries a receipt for", str(caught.exception))

    def test_a_command_digest_is_the_target_state_not_a_promise(self) -> None:
        ledger = walked()
        transition = advance(
            ledger.current,
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
            command_id="cmd-accept",
        )
        self.assertEqual(transition.receipt.command_digest, content_digest(transition.to_vector.to_payload()))

    def test_a_command_id_without_a_digest_is_refused(self) -> None:
        transition = advance(
            walked().current,
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
            command_id="cmd-accept",
        )
        with self.assertRaises(SchemaValidationError):
            self.rebuild(transition, receipt=replace(transition.receipt, command_digest=None))

    def test_a_transition_survives_a_payload_round_trip(self) -> None:
        ledger = walked()
        moved = ledger.advance(
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
            evidence_refs=(ref(EntityKind.QUALITY_DECISION),),
        )
        self.assertEqual(StateTransition.from_payload(moved.to_payload()), moved)

    def test_reason_codes_are_identifiers_not_prose(self) -> None:
        with self.assertRaises(SchemaValidationError):
            advance(walked().current, actor=ACTOR, phase=Phase.ACCEPTED, reason_code="it looks fine to me")


class AttemptTests(unittest.TestCase):
    def test_starting_an_attempt_names_the_run_and_the_state_move_at_once(self) -> None:
        ledger = walked()
        attempt = new_id()
        started = start_attempt(ledger.current, attempt_id=attempt, actor=ACTOR)
        self.assertIs(started.to_vector.execution, Execution.ACTIVE)
        self.assertEqual(started.to_vector.active_attempt_id, attempt)
        self.assertEqual(started.moved_regions, ("execution",))

    def test_a_process_that_ended_well_proves_that_attempt_and_nothing_about_acceptance(self) -> None:
        ledger = walked()
        started = ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())
        finished = attempt_outcome(
            ledger.current,
            attempt_id=started.to_vector.active_attempt_id,
            succeeded=True,
            actor=JUDGE,
        )
        self.assertIs(finished.to_vector.phase, Phase.VALIDATING)
        self.assertIs(finished.to_vector.execution, Execution.IDLE)
        self.assertIsNone(finished.to_vector.active_attempt_id)
        self.assertEqual(finished.receipt.reason_code, "attempt_succeeded")

    def test_an_attempt_outcome_may_not_move_the_phase(self) -> None:
        ledger = walked()
        started = ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())
        with self.assertRaises(LifecycleError) as caught:
            attempt_outcome(
                ledger.current,
                attempt_id=started.to_vector.active_attempt_id,
                succeeded=True,
                actor=JUDGE,
                phase=Phase.ACCEPTED,
                promotion_ref=ref(),
            )
        self.assertIn("nothing about acceptance", str(caught.exception))

    def test_an_outcome_must_name_the_attempt_that_is_on_the_floor(self) -> None:
        ledger = walked()
        ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())
        with self.assertRaises(LifecycleError) as caught:
            attempt_outcome(ledger.current, attempt_id=new_id(), succeeded=True, actor=JUDGE)
        self.assertIn("cannot end", str(caught.exception))

    def test_a_failed_attempt_leaves_the_phase_exactly_where_it_was(self) -> None:
        ledger = walked()
        started = ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())
        failed = attempt_outcome(
            ledger.current,
            attempt_id=started.to_vector.active_attempt_id,
            succeeded=False,
            actor=JUDGE,
        )
        self.assertEqual(failed.receipt.reason_code, "attempt_failed")
        self.assertIs(failed.to_vector.phase, ledger.current.phase)

    def test_a_blocked_attempt_outcome_cites_the_blocker_and_the_attempt(self) -> None:
        ledger = walked()
        attempt = new_id()
        ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=attempt)
        blocker = ref(EntityKind.RECEIPT)
        blocked = attempt_outcome(
            ledger.current, attempt_id=attempt, succeeded=False, actor=JUDGE, blocked_by=blocker
        )
        self.assertIs(blocked.to_vector.execution, Execution.BLOCKED)
        self.assertEqual(blocked.blocker_ref, blocker)
        self.assertIn(attempt, [item.reference for item in blocked.receipt.evidence_refs])

    def test_an_attempt_cannot_be_started_twice_without_the_state_saying_so(self) -> None:
        ledger = walked()
        ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())
        with self.assertRaises(LifecycleError):
            ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())


class LedgerTests(unittest.TestCase):
    def test_a_ledger_replays_from_draft_not_from_where_someone_claims_it_is(self) -> None:
        production = new_id()
        with self.assertRaises(LifecycleError) as caught:
            at(production, web_profile(), phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
        self.assertIn("history that starts mid-ladder", str(caught.exception))

    def test_a_ledger_refuses_another_productions_history(self) -> None:
        ledger = walked()
        outsider = new_id()
        with self.assertRaises(LifecycleError) as caught:
            ProductionLedger(outsider, initial_vector(outsider), profile=web_profile()).record(ledger.history[0])
        self.assertIn("cannot record a transition for", str(caught.exception))

    def test_a_seed_vector_for_another_production_is_refused(self) -> None:
        outsider = new_id()
        with self.assertRaises(LifecycleError) as caught:
            ProductionLedger(outsider, initial_vector(new_id()))
        self.assertIn("belongs to another production", str(caught.exception))

    def test_history_is_appended_not_spliced_in(self) -> None:
        ledger = walked()
        skipped = advance(
            ledger.current,
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
            parent_receipt_id=None,
        )
        with self.assertRaises(LifecycleError) as caught:
            ledger.record(skipped)
        self.assertIn("appended, not spliced", str(caught.exception))

    def test_a_stale_proposal_is_refused_rather_than_applied(self) -> None:
        ledger = walked()
        before = ledger.current
        ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())
        stale = advance(
            before,
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
            parent_receipt_id=ledger.head_receipt_id,
        )
        with self.assertRaises(LifecycleError) as caught:
            ledger.record(stale)
        self.assertIn("re-read the state", str(caught.exception))

    def test_a_profile_cannot_change_mid_history(self) -> None:
        ledger = walked(web_profile())
        move = advance(
            ledger.current,
            actor=ACTOR,
            phase=Phase.ACCEPTED,
            review="APPROVED",
            promotion_ref=ref(),
            review_receipt=ref(),
            profile=fastlane_profile(),
            parent_receipt_id=ledger.head_receipt_id,
        )
        with self.assertRaises(LifecycleError) as caught:
            ledger.record(move)
        self.assertIn("change the profile by starting a new production", str(caught.exception))

    def test_a_transition_bound_is_enforced(self) -> None:
        production = new_id()
        ledger = ProductionLedger(
            production,
            initial_vector(production),
            profile=web_profile(),
            maximum=3,
        )
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        ledger.advance(actor=ACTOR, phase=Phase.READY)
        ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, phase=Phase.VALIDATING, review="PENDING")
        self.assertIn("admitted bound", str(caught.exception))

    def test_a_repeated_command_returns_the_move_it_already_made(self) -> None:
        ledger = released()
        first = ledger.advance(actor=ACTOR, review="PENDING", command_id="cmd-reopen")
        again = ledger.advance(actor=ACTOR, review="PENDING", command_id="cmd-reopen")
        self.assertEqual(first.transition_id, again.transition_id)
        self.assertEqual(len(ledger), len(ledger.history))

    def test_an_idempotent_retry_still_works_at_the_transition_bound(self) -> None:
        production = new_id()
        ledger = ProductionLedger(production, initial_vector(production), maximum=1)
        first = ledger.advance(actor=ACTOR, phase=Phase.PLANNED, command_id="cmd-only")
        again = ledger.advance(actor=ACTOR, phase=Phase.PLANNED, command_id="cmd-only")
        self.assertEqual(first.transition_id, again.transition_id)
        self.assertEqual(len(ledger), 1)

    def test_a_repeated_command_with_a_new_meaning_is_a_conflict(self) -> None:
        ledger = released()
        ledger.advance(actor=ACTOR, review="PENDING", command_id="cmd-reopen")
        with self.assertRaises(StoreConflictError) as caught:
            ledger.advance(actor=ACTOR, review="APPROVED", review_receipt=ref(), command_id="cmd-reopen")
        self.assertIn("already recorded", str(caught.exception))

    def test_a_command_id_must_be_text(self) -> None:
        with self.assertRaises(SchemaValidationError):
            walked().advance(actor=ACTOR, review="APPROVED", review_receipt=ref(), command_id=17)

    def test_a_transition_names_who_made_it(self) -> None:
        with self.assertRaises(LifecycleError) as caught:
            walked().advance(phase=Phase.ACCEPTED)
        self.assertIn("names the actor", str(caught.exception))

    def test_replay_and_projection_agree_over_a_whole_life(self) -> None:
        ledger = released()
        ledger.advance(actor=ACTOR, phase=Phase.SUPERSEDED, superseded_by_ref=ref(), replacement_ref=ref())
        ledger.advance(actor=ACTOR, phase=Phase.ARCHIVED)
        proof = ledger.prove_state()
        self.assertTrue(proof.matches)
        self.assertEqual(ledger.replay(), ledger.current)
        self.assertIsInstance(proof.head_receipt_id, str)
        self.assertEqual(proof.transitions, len(ledger))
        self.assertIn("matches replay", proof.text)

    def test_a_ledger_rebuilt_from_history_reproduces_the_state(self) -> None:
        ledger = released()
        rebuilt = ProductionLedger(
            ledger.production_id,
            initial_vector(ledger.production_id),
            profile=web_profile(),
            transitions=ledger.history,
        )
        self.assertEqual(rebuilt.current, ledger.current)
        self.assertEqual(len(rebuilt), len(ledger))
        self.assertTrue(rebuilt.prove_state().matches)

    def test_record_rejects_a_payload_that_is_not_a_complete_transition(self) -> None:
        ledger = walked()
        with self.assertRaises(SchemaValidationError):
            ledger.record({"transition_id": new_id()})

    def test_the_head_moves_with_every_recorded_step(self) -> None:
        ledger = at(new_id(), web_profile())
        self.assertIsNone(ledger.head_receipt_id)
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        self.assertEqual(ledger.head_receipt_id, ledger.history[-1].receipt.transition_id)


class BlockerTests(unittest.TestCase):
    def blocker(self, production: str, **over: Any) -> Blocker:
        base: dict[str, Any] = dict(
            blocker_id=new_id(),
            production_id=production,
            kind=BlockerKind.MISSING_RIGHTS,
            reason="consent for the spokesperson voice is not on file",
            raised_at_ms=NOW,
            stale_gate_refs=(ExternalRef(kind=EntityKind.RECEIPT, reference="gate.rights"),),
        )
        base.update(over)
        return Blocker(**base)

    def test_a_blocker_is_a_uuid_identity_with_a_kind_and_a_reason(self) -> None:
        found = self.blocker(new_id())
        self.assertTrue(found.is_cleared is False)
        self.assertIn("open: MISSING_RIGHTS", found.text)

    def test_an_empty_reason_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.blocker(new_id(), reason="   ")

    def test_the_same_blocker_may_be_reported_twice_but_not_rewritten(self) -> None:
        found = self.blocker(new_id())
        ledger = BlockerLedger([found])
        self.assertIs(ledger.add(found), found)
        with self.assertRaises(StoreConflictError):
            ledger.add(replace(found, reason="a different story about the same stop"))

    def test_clearing_creates_new_history_rather_than_deleting(self) -> None:
        found = self.blocker(new_id())
        ledger = BlockerLedger([found])
        cleared = ledger.clear(found.blocker_id, at_ms=NOW + 1000, actor=ACTOR)
        self.assertTrue(cleared.is_cleared)
        self.assertEqual(ledger.size, 1)
        self.assertEqual(ledger.open_for(found.production_id), ())
        self.assertEqual(len(ledger.blockers_of(found.production_id)), 1)

    def test_a_blocker_cannot_be_cleared_before_it_was_raised(self) -> None:
        found = self.blocker(new_id())
        ledger = BlockerLedger([found])
        with self.assertRaises(LifecycleError):
            ledger.clear(found.blocker_id, at_ms=NOW - 1000, actor=ACTOR)

    def test_an_unknown_blocker_cannot_be_cleared(self) -> None:
        with self.assertRaises(LifecycleError):
            BlockerLedger().clear(new_id(), at_ms=NOW, actor=ACTOR)

    def test_clearing_keeps_the_gates_the_blocker_staled(self) -> None:
        found = self.blocker(new_id())
        ledger = BlockerLedger([found])
        cleared = ledger.clear(found.blocker_id, at_ms=NOW + 5, actor=ACTOR)
        self.assertEqual(cleared.stale_gate_refs, found.stale_gate_refs)

    def test_blockers_are_ordered_by_when_they_were_raised(self) -> None:
        production = new_id()
        late = self.blocker(production, raised_at_ms=NOW + 10, kind=BlockerKind.MISSING_MODEL)
        early = self.blocker(production, raised_at_ms=NOW, kind=BlockerKind.SECURITY_POLICY)
        ledger = BlockerLedger([late, early])
        self.assertEqual([item.kind for item in ledger.open_for(production)], [BlockerKind.SECURITY_POLICY, BlockerKind.MISSING_MODEL])

    def test_a_blocker_belongs_to_exactly_one_production(self) -> None:
        ledger = BlockerLedger([self.blocker(new_id())])
        self.assertEqual(ledger.open_for(new_id()), ())


class CompletionTests(unittest.TestCase):
    def test_completion_is_derived_from_a_profile_never_a_state_name(self) -> None:
        profile = web_profile(terminal_phase=Phase.ACCEPTED, obligations=("a judgement on file",))
        ledger = accepted(profile)
        claim = ledger.completion(profile)
        self.assertTrue(claim.satisfied)
        self.assertIn("COMPLETED under profile profile.web", claim.summary)
        self.assertIn("a judgement on file", claim.summary)

    def test_a_terminal_phase_beyond_the_profiles_is_still_complete(self) -> None:
        profile = web_profile(terminal_phase=Phase.RELEASED)
        claim = completion_of(released().current, profile)
        self.assertTrue(claim.satisfied)

    def test_an_outstanding_review_blocks_completion(self) -> None:
        profile = web_profile(terminal_phase=Phase.VALIDATING, obligations=())
        ledger = at(new_id(), profile)
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        ledger.advance(actor=ACTOR, phase=Phase.READY)
        ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
        ledger.advance(actor=ACTOR, phase=Phase.VALIDATING, review="PENDING")
        claim = ledger.completion(profile)
        self.assertFalse(claim.satisfied)
        self.assertIn("a review request is unanswered", claim.outstanding)

    def test_work_on_the_floor_is_outstanding(self) -> None:
        profile = web_profile(terminal_phase=Phase.PLANNED, obligations=())
        ledger = at(new_id(), profile)
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        ledger.advance(actor=ACTOR, execution="ACTIVE", active_attempt_id=new_id())
        self.assertIn("execution is ACTIVE", ledger.completion(profile).outstanding)

    def test_a_staged_release_that_never_shipped_is_outstanding(self) -> None:
        profile = web_profile(terminal_phase=Phase.RELEASED, obligations=())
        ledger = accepted(profile)
        ledger.advance(
            actor=ACTOR,
            phase=Phase.RELEASED,
            release_snapshot_id=new_id(),
            release_condition="STAGED",
            promotion_ref=ref(),
        )
        self.assertIn(
            "a release is staged and never published or withdrawn",
            ledger.completion(profile).outstanding,
        )

    def test_a_blocker_holds_completion_even_at_the_terminal_phase(self) -> None:
        profile = web_profile(terminal_phase=Phase.PLANNED, obligations=())
        ledger = at(new_id(), profile)
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        found = Blocker(
            blocker_id=new_id(),
            production_id=ledger.production_id,
            kind=BlockerKind.EXTERNAL_UNAVAILABLE,
            reason="the render provider is unreachable",
            raised_at_ms=NOW,
        )
        claim = ledger.completion(profile, open_blockers=(found,))
        self.assertFalse(claim.satisfied)
        self.assertIn("blocker EXTERNAL_UNAVAILABLE", claim.outstanding)

    def test_a_blocker_on_another_production_cannot_be_judged_here(self) -> None:
        profile = web_profile(terminal_phase=Phase.PLANNED, obligations=())
        ledger = at(new_id(), profile)
        ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
        stranger = Blocker(
            blocker_id=new_id(),
            production_id=new_id(),
            kind=BlockerKind.MISSING_ASSET,
            reason="another production is stopped",
            raised_at_ms=NOW,
        )
        with self.assertRaises(LifecycleError):
            ledger.completion(profile, open_blockers=(stranger,))

    def test_a_completion_cannot_claim_success_while_something_is_outstanding(self) -> None:
        with self.assertRaises(LifecycleError):
            CompletionProfile(
                production_id=new_id(),
                profile_id="profile.web",
                terminal_phase=Phase.RELEASED,
                reached_phase=Phase.RELEASED,
                satisfied=True,
                outstanding=("a release is staged",),
            )

    def test_a_completion_short_of_its_terminal_phase_is_refused(self) -> None:
        with self.assertRaises(LifecycleError):
            CompletionProfile(
                production_id=new_id(),
                profile_id="profile.web",
                terminal_phase=Phase.RELEASED,
                reached_phase=Phase.MATERIALIZED,
                satisfied=True,
            )

    def test_completion_survives_a_payload_round_trip(self) -> None:
        claim = released().completion(web_profile())
        self.assertEqual(CompletionProfile.from_payload(claim.to_payload()), claim)


class RegionMachineTests(unittest.TestCase):
    def test_execution_may_stop_for_work_or_a_blocker_but_never_from_blocked_directly_on(self) -> None:
        self.assertTrue(PRODUCTION_EXECUTION.is_legal(Execution.IDLE, Execution.ACTIVE))
        self.assertTrue(PRODUCTION_EXECUTION.is_legal(Execution.ACTIVE, Execution.BLOCKED))
        self.assertFalse(PRODUCTION_EXECUTION.is_legal(Execution.BLOCKED, Execution.ACTIVE))
        self.assertTrue(PRODUCTION_EXECUTION.is_legal(Execution.BLOCKED, Execution.IDLE))

    def test_review_must_be_asked_before_it_is_answered(self) -> None:
        self.assertFalse(PRODUCTION_REVIEW.is_legal(Review.NOT_REQUESTED, Review.APPROVED))
        self.assertTrue(PRODUCTION_REVIEW.is_legal(Review.PENDING, Review.APPROVED))
        self.assertTrue(PRODUCTION_REVIEW.is_legal(Review.APPROVED, Review.PENDING))

    def test_a_published_release_is_withdrawn_never_replaced_by_unreleased(self) -> None:
        self.assertTrue(PRODUCTION_RELEASE.is_legal(Release.PUBLISHED, Release.WITHDRAWN))
        self.assertFalse(PRODUCTION_RELEASE.is_legal(Release.PUBLISHED, Release.UNRELEASED))
        self.assertTrue(PRODUCTION_RELEASE.is_legal(Release.STAGED, Release.UNRELEASED))
        self.assertTrue(PRODUCTION_RELEASE.is_terminal(Release.WITHDRAWN))

    def test_a_region_move_that_the_table_refuses_never_reaches_the_ledger(self) -> None:
        ledger = walked()
        with self.assertRaises(LifecycleError):
            ledger.advance(actor=ACTOR, release_condition="PUBLISHED")
        self.assertIs(ledger.current.release_condition, Release.UNRELEASED)

    def test_a_no_op_move_is_refused(self) -> None:
        ledger = walked()
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, phase=Phase.VALIDATING)
        self.assertIn("changes nothing", str(caught.exception))

    def test_advance_without_anything_to_move_is_refused(self) -> None:
        with self.assertRaises(LifecycleError):
            advance(walked().current, actor=ACTOR)

    def test_the_withdrawn_release_is_the_end_of_that_region(self) -> None:
        ledger = released()
        withdrawn = ledger.advance(actor=ACTOR, release_condition="WITHDRAWN")
        self.assertIs(withdrawn.to_vector.release_condition, Release.WITHDRAWN)
        self.assertTrue(phase_at_least(withdrawn.to_vector.phase, Phase.RELEASED))


import unittest  # noqa: E402  placed last so the helpers above read as the fixture they are

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
