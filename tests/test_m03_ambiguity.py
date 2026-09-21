"""The ambiguity law §5.7-§5.8 and §18 enforce: an unresolved point is data, and latitude is not a gap.

Three separations hold this together, and each is a refusal rather than a hope. A BLOCKING record stops
completion through ``require_admissible``, and the kernel refuses to carry a blocker that cannot name
what it stops. A CREATIVE_FREEDOM record stops nothing and asks for no human: it is reported as a zone
the brief granted, never absorbed into a default, and a defaulted value that quietly closes a declared
zone is refused. And the clarification queue is an integer ordering over consequence, breadth and
specificity, so two runs over identical normalized inputs cannot disagree — a float-weighted queue
would look smarter and read as unauditable.
"""

from __future__ import annotations

import unittest
from typing import Any

from iris_intent.admission import SemanticAdmissionShield
from iris_intent.ambiguity import (
    AmbiguityAssessment,
    AmbiguityConsequence,
    AmbiguityKind,
    AmbiguityRecord,
    ClarificationCandidate,
    FreedomZone,
    LatitudeClass,
    OpenQuestion,
    QuestionStatus,
    rank_clarifications,
    require_freedom_honoured,
)
from iris_intent.briefs import BriefRevision
from iris_intent.errors import AmbiguityBlockedError, QualityAuthorityError, SchemaValidationError
from iris_intent.identity import AuthorityLevel, RefKind
from iris_intent.intent import (
    AuthorityBasis,
    IntentAuthorityRef,
    IntentOrigin,
    IntentStatement,
    StatementKind,
)
from iris_intent.versions import QualityClass

from tests import m03_kernel_support as S

DEEP = f"{S.LOGO}.mark.weight"
VAGUE = "the brief asks for something premium"


def record(
    ident: str = "am.iris",
    *,
    path: str = S.LOGO,
    kind: str = AmbiguityKind.TERM_OVERLOAD.value,
    consequence: str = AmbiguityConsequence.BLOCKING.value,
    readings: tuple[str, ...] = ("wordmark", "monogram"),
    statements: tuple[str, ...] = ("st.1",),
    **over: Any,
) -> AmbiguityRecord:
    """``S.ambiguity`` always demands a human, which no non-critical consequence may do (§5.7).

    This builder keeps the fixture shape identical and lets ``requires_human`` fall back to the value
    the kernel derives from the consequence, which is the field the law actually guards.
    """

    payload: dict[str, Any] = {
        "ambiguity_id": ident,
        "kind": kind,
        "consequence": consequence,
        "semantic_paths": (path,),
        "question": "Which reading is meant?",
        "candidate_readings": readings,
        "affected_statement_ids": statements,
    }
    payload.update(over)
    return AmbiguityRecord(**payload)


def zone(
    ident: str = "fz.logo",
    *,
    free: tuple[str, ...] = (S.LOGO,),
    fixed: tuple[str, ...] = (),
    **over: Any,
) -> FreedomZone:
    return FreedomZone(
        zone_id=ident,
        label=over.pop("label", "the mark may be drawn freely within the brand palette"),
        free_paths=free,
        fixed_paths=fixed,
        **over,
    )


def assessment(
    *,
    ambiguities: tuple[AmbiguityRecord, ...] = (),
    zones: tuple[FreedomZone, ...] = (),
    questions: tuple[OpenQuestion, ...] = (),
    statements: tuple[IntentStatement, ...] = (),
    revision: BriefRevision | None = None,
) -> AmbiguityAssessment:
    item = revision or S.admitted_revision()
    return AmbiguityAssessment(
        brief_id=item.brief_id,
        revision_id=item.revision_id,
        ambiguities=ambiguities,
        freedom_zones=zones,
        open_questions=questions,
        statements=statements,
    )


def defaulted(
    path: str = S.LOGO,
    *,
    ident: str = "st.defaulted",
    authority: IntentAuthorityRef | None = None,
    **over: Any,
) -> IntentStatement:
    """A value nobody was asked about, which is exactly what may not close a granted zone."""

    return S.statement(
        ident,
        path=path,
        origin=IntentOrigin.DEFAULTED.value,
        authority=authority or S.authority_ref(AuthorityLevel.PROJECT_RECORD.value),
        **over,
    )


class BlockingAmbiguityTests(unittest.TestCase):
    def test_a_blocking_record_stops_completion(self) -> None:
        blocked = assessment(ambiguities=(record(),))

        self.assertTrue(blocked.blocks_completion)
        self.assertEqual([item.ambiguity_id for item in blocked.blocking_ambiguities], ["am.iris"])
        with self.assertRaises(AmbiguityBlockedError) as refused:
            blocked.require_admissible("compile the fidelity contract")
        message = str(refused.exception)
        self.assertIn("cannot compile the fidelity contract", message)
        self.assertIn("am.iris", message)
        self.assertIn(S.BRIEF_ID, message)

    def test_resolving_a_blocking_record_lifts_the_block(self) -> None:
        resolved = record(
            resolution_ref=S.ref(RefKind.RESOLUTION.value, "res.1"),
            notes="the owner chose the wordmark",
        )
        cleared = assessment(ambiguities=(resolved,))

        self.assertTrue(resolved.resolved)
        self.assertFalse(resolved.blocks())
        self.assertTrue(resolved.consequence_class.blocks_completion)
        self.assertEqual(cleared.blocking_ambiguities, ())
        self.assertFalse(cleared.blocks_completion)
        self.assertIsNone(cleared.require_admissible("compile"))

    def test_an_open_question_blocks_without_any_record(self) -> None:
        blocked = assessment(questions=(S.question(),))

        self.assertEqual(blocked.ambiguities, ())
        self.assertTrue(blocked.blocks_completion)
        self.assertEqual([item.question_id for item in blocked.blocking_questions], ["q.iris"])
        with self.assertRaises(AmbiguityBlockedError) as refused:
            blocked.require_admissible("admit the revision")
        self.assertIn("q.iris", str(refused.exception))

    def test_answering_a_question_with_a_ref_is_the_only_way_past_it(self) -> None:
        answered = S.question(
            blocking=False, status=QuestionStatus.ANSWERED.value, answer=S.revision_ref("rev.8")
        )
        cleared = assessment(questions=(answered,))

        self.assertFalse(cleared.blocks_completion)
        self.assertFalse(answered.is_open)
        self.assertEqual(answered.answer_ref.ref_id, "rev.8")

        with self.assertRaises(SchemaValidationError) as still_blocking:
            S.question(status=QuestionStatus.ANSWERED.value, answer=S.revision_ref("rev.8"))
        self.assertIn("clear the blocking flag", str(still_blocking.exception))
        with self.assertRaises(SchemaValidationError) as unrecorded:
            S.question(blocking=False, status=QuestionStatus.ANSWERED.value)
        self.assertIn("answer_ref", str(unrecorded.exception))
        with self.assertRaises(SchemaValidationError) as mismatched:
            OpenQuestion(
                question_id="q.mixed",
                text="Which mark is the client's?",
                consequence=AmbiguityConsequence.NON_BLOCKING.value,
                blocking=True,
            )
        self.assertIn("flagged blocking", str(mismatched.exception))

    def test_the_block_survives_serialisation(self) -> None:
        blocked = assessment(ambiguities=(record(),), questions=(S.question(),))
        rebuilt = AmbiguityAssessment.from_payload(blocked.to_payload())

        self.assertEqual(rebuilt.digest(), blocked.digest())
        self.assertTrue(rebuilt.blocks_completion)
        with self.assertRaises(AmbiguityBlockedError):
            rebuilt.require_admissible("compile")

    def test_a_blocking_record_that_affects_nothing_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            record(statements=())
        self.assertIn("blocks nothing", str(refused.exception))

        named_a_rule = record(statements=(), affected_constraint_ids=("cn.logo",))
        self.assertEqual(named_a_rule.breadth, 1)
        self.assertTrue(named_a_rule.blocks())

        named_an_obligation = record(
            statements=(), affected_obligation_ids=("ob.legibility",)
        )
        self.assertEqual(named_an_obligation.affected_statement_ids, ())
        self.assertTrue(named_an_obligation.blocks())

    def test_a_blocking_record_must_name_a_semantic_path(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            record(semantic_paths=())
        self.assertIn("names no semantic path", str(refused.exception))
        with self.assertRaises(SchemaValidationError):
            record(semantic_paths="brief.visual.logo")
        with self.assertRaises(SchemaValidationError):
            record(semantic_paths=("not a path",))

    def test_the_assessment_refuses_two_records_under_one_id(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            assessment(ambiguities=(record("am.dup"), record("am.dup", consequence="NON_BLOCKING")))
        self.assertIn("duplicate ids", str(refused.exception))

    def test_only_the_blocking_class_stops_the_work(self) -> None:
        self.assertEqual(
            [
                item.value
                for item in sorted(AmbiguityConsequence, key=lambda each: each.rank)
                if item.blocks_completion
            ],
            [AmbiguityConsequence.BLOCKING.value],
        )
        for consequence in (
            AmbiguityConsequence.QUALITY_CRITICAL,
            AmbiguityConsequence.COST_CRITICAL,
        ):
            ident = f"am.{consequence.name.lower()}"
            critical = assessment(ambiguities=(record(ident, consequence=consequence.value),))
            self.assertFalse(critical.blocks_completion)
            self.assertIsNone(critical.require_admissible("compile"))
            self.assertTrue(record(ident, consequence=consequence.value).requires_human)
        self.assertEqual(
            [item.ambiguity_id for item in assessment(
                ambiguities=(
                    record("am.quality", consequence="QUALITY_CRITICAL"),
                    record("am.cost", consequence="COST_CRITICAL"),
                )
            ).quality_critical],
            ["am.quality"],
        )


class ShieldBlockingAmbiguityTests(unittest.TestCase):
    """§5.8: a blocking ambiguity must produce a refusal *finding*, not an exception.

    ``AmbiguityAssessment.require_admissible`` is the law that stops compilation, and the admission
    shield reports the same condition as a traceable finding so a caller can see everything wrong
    with a brief in one pass. The two agree, and neither one decides the ambiguity: it stays open
    until an admitted revision answers it.
    """

    def setUp(self) -> None:
        self.shield = SemanticAdmissionShield(registry=S.predicate_registry())

    def test_the_shield_reports_a_creative_freedom_gap_without_crashing(self) -> None:
        stranded = assessment(ambiguities=(record(consequence="CREATIVE_FREEDOM", statements=()),))
        findings = self.shield.check_ambiguity(stranded)

        self.assertEqual(
            [(item.check, item.decision) for item in findings], [("FREEDOM_AS_GAP", "REFUSED")]
        )
        self.assertIn("creative freedom", findings[0].detail)

    def test_the_shield_reports_a_blocking_ambiguity_as_a_refusal(self) -> None:
        blocked = assessment(ambiguities=(record("am.blocking"),))
        self.assertTrue(blocked.blocks_completion)
        with self.assertRaises(AmbiguityBlockedError):
            blocked.require_admissible("compile")

        findings = self.shield.check_ambiguity(blocked)
        reported = [(item.check, item.decision) for item in findings]
        self.assertIn(("BLOCKING_AMBIGUITY", "REFUSED"), reported)
        refusal = findings[0]
        self.assertIn("BLOCKING", refusal.detail)
        self.assertIn("am.blocking", refusal.detail)
        self.assertTrue(refusal.recoverable, "an open question is answerable, a typo is not")
        self.assertTrue(refusal.evidence_refs)


class CreativeFreedomTests(unittest.TestCase):
    def test_creative_freedom_stops_nothing_and_asks_for_no_human(self) -> None:
        free = record(consequence=AmbiguityConsequence.CREATIVE_FREEDOM.value, statements=())
        opened = assessment(ambiguities=(free,), zones=(zone(),))

        self.assertEqual(free.consequence_class.rank, 0)
        self.assertFalse(free.requires_human)
        self.assertFalse(free.blocks())
        self.assertFalse(opened.blocks_completion)
        self.assertEqual(opened.blocking_ambiguities, ())
        self.assertEqual(opened.quality_critical, ())
        self.assertEqual(opened.cost_critical, ())
        self.assertIsNone(opened.require_admissible("compile the execution bundle"))

    def test_a_declared_zone_is_not_reported_as_a_gap(self) -> None:
        opened = assessment(
            ambiguities=(record(consequence="CREATIVE_FREEDOM", statements=()),), zones=(zone(),)
        )
        shield = SemanticAdmissionShield(registry=S.predicate_registry())

        self.assertEqual(opened.freedom_as_gap, ())
        self.assertEqual(shield.check_ambiguity(opened), [])
        report = shield.assess(
            report_id="adm.free", subject=S.revision_ref(), assessment=opened
        )
        self.assertEqual(report.decision, "ADMITTED")
        self.assertTrue(report.admitted)

    def test_a_freedom_outside_every_zone_is_named_not_absorbed(self) -> None:
        stranded = assessment(ambiguities=(record(consequence="CREATIVE_FREEDOM", statements=()),))
        shield = SemanticAdmissionShield(registry=S.predicate_registry())
        findings = shield.check_ambiguity(stranded)

        self.assertEqual(stranded.freedom_as_gap, ("am.iris",))
        self.assertFalse(stranded.blocks_completion)
        self.assertEqual([(item.check, item.decision) for item in findings], [("FREEDOM_AS_GAP", "REFUSED")])
        self.assertIn("creative freedom", findings[0].detail)
        report = shield.assess(
            report_id="adm.gap", subject=S.revision_ref(), assessment=stranded
        )
        self.assertEqual(report.decision, "REFUSED")

    def test_a_missing_value_and_a_declared_freedom_are_different_facts(self) -> None:
        gap = assessment(
            ambiguities=(
                record("am.gap", kind=AmbiguityKind.MISSING_VALUE.value, consequence="BLOCKING"),
            )
        )
        latitude = assessment(
            ambiguities=(
                record(
                    "am.gap", kind=AmbiguityKind.MISSING_VALUE.value, consequence="CREATIVE_FREEDOM", statements=()
                ),
            ),
            zones=(zone(),),
        )

        self.assertTrue(gap.blocks_completion)
        self.assertFalse(latitude.blocks_completion)
        self.assertEqual(latitude.freedom_as_gap, ())
        self.assertEqual(
            latitude.ambiguities[0].kind, AmbiguityKind.MISSING_VALUE.value
        )
        self.assertEqual(gap.ambiguities[0].kind, latitude.ambiguities[0].kind)

    def test_an_ambiguity_may_not_borrow_a_policy_claim(self) -> None:
        for consequence in ("NON_BLOCKING", "CREATIVE_FREEDOM"):
            with self.assertRaises(SchemaValidationError) as refused:
                record(consequence=consequence, requires_human=True)
            self.assertIn("policy claim", str(refused.exception))

        self.assertTrue(record("am.b", consequence="BLOCKING").requires_human)
        self.assertFalse(record("am.n", consequence="NON_BLOCKING").requires_human)


class FreedomZoneDataTests(unittest.TestCase):
    def test_a_zone_states_what_is_free_and_what_is_fixed(self) -> None:
        declared = zone(fixed=(DEEP,), free=("brief.audio.tone", S.LOGO))
        opened = assessment(
            zones=(declared, zone("fz.spec", free=(S.SPEC,)))
        )

        self.assertEqual(declared.free_paths, ("brief.audio.tone", "brief.visual.logo"))
        self.assertEqual(declared.fixed_paths, (DEEP,))
        self.assertTrue(declared.covers(S.LOGO))
        self.assertTrue(declared.covers("brief.visual.logo.mark"))
        self.assertFalse(declared.covers(DEEP))
        self.assertFalse(declared.covers(S.SPEC))
        self.assertEqual(
            opened.free_paths(), tuple(sorted({S.TONE, S.LOGO, S.SPEC}))
        )

    def test_a_zone_that_frees_nothing_is_a_constraint_bundle(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            zone(free=())
        self.assertIn("frees nothing", str(refused.exception))
        with self.assertRaises(SchemaValidationError):
            zone(label="")
        with self.assertRaises(SchemaValidationError):
            zone(free=("not a path",))

    def test_a_path_cannot_be_both_free_and_fixed(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            zone(free=(S.LOGO, DEEP), fixed=(DEEP, S.SPEC))
        self.assertIn("both fixes and frees", str(refused.exception))

    def test_a_fixed_path_inside_a_free_prefix_is_not_covered(self) -> None:
        bounded = zone(free=(S.LOGO,), fixed=(DEEP,))
        self.assertTrue(bounded.covers("brief.visual.logo.mark"))
        self.assertFalse(bounded.covers(DEEP))
        self.assertFalse(bounded.covers(f"{DEEP}.stroke"))

    def test_latitude_is_typed_data(self) -> None:
        self.assertEqual(zone().latitude, "OPEN_WITHIN_BOUNDS")
        for kind in LatitudeClass:
            self.assertEqual(zone(latitude=kind.value).latitude, kind.value)
        self.assertEqual(FreedomZone.latitude_kind(" any_within_bounds "), LatitudeClass.ANY_WITHIN_BOUNDS.value)
        with self.assertRaises(SchemaValidationError):
            zone(latitude="DO_WHATEVER")

    def test_a_zone_is_first_class_and_round_trips(self) -> None:
        declared = zone(granted_by=S.policy_ref(), expires_with_revision=9, rationale="the client owns the mark, not its drawing")
        rebuilt = FreedomZone.from_payload(declared.to_payload())

        self.assertEqual(rebuilt.digest(), declared.digest())
        self.assertEqual(rebuilt.granted_by.ref_id, "policy.brand.v1")
        self.assertEqual(rebuilt.expires_with_revision, 9)
        self.assertEqual(rebuilt.zone_ref.kind, RefKind.FREEDOM_ZONE.value)
        self.assertEqual(rebuilt.zone_ref.content_digest, declared.digest())
        with self.assertRaises(SchemaValidationError):
            zone(expires_with_revision=0)
        with self.assertRaises(SchemaValidationError):
            zone(expires_with_revision=True)

    def test_the_assessment_keeps_zones_ordered_unique_and_bounded(self) -> None:
        opened = assessment(zones=(zone("fz.b"), zone("fz.a")))
        self.assertEqual([item.zone_id for item in opened.freedom_zones], ["fz.a", "fz.b"])

        with self.assertRaises(SchemaValidationError) as duplicated:
            assessment(zones=(zone("fz.a"), zone("fz.a", free=(S.ICON,))))
        self.assertIn("duplicate zone_ids", str(duplicated.exception))

    def test_covered_statements_names_what_the_zone_lets_through(self) -> None:
        opened = assessment(
            zones=(zone(),),
            statements=(
                S.statement("st.logo"),
                S.statement("st.deep", path=DEEP),
                S.statement("st.tone", path=S.TONE),
            ),
        )
        self.assertEqual(opened.covered_statements(), ("st.deep", "st.logo"))
        self.assertEqual(assessment(zones=(zone(),)).covered_statements(), ())
        self.assertEqual(assessment(statements=(S.statement("st.logo"),)).free_paths(), ())

    def test_a_critical_ambiguity_inside_a_zone_is_reported_contested(self) -> None:
        contested = assessment(
            ambiguities=(
                record("am.deep", path=DEEP, consequence="QUALITY_CRITICAL"),
                record("am.other", path=S.TONE, consequence="QUALITY_CRITICAL"),
            ),
            zones=(zone(free=(S.LOGO,)),),
        )
        self.assertEqual(contested.freedom_zones_contested, ("fz.logo",))
        self.assertFalse(contested.blocks_completion)

        quiet = assessment(
            ambiguities=(record("am.free", consequence="CREATIVE_FREEDOM", statements=()),),
            zones=(zone(),),
        )
        self.assertEqual(quiet.freedom_zones_contested, ())


class FreedomHonouredTests(unittest.TestCase):
    def test_defaulting_a_value_inside_a_zone_is_refused(self) -> None:
        with self.assertRaises(AmbiguityBlockedError) as refused:
            require_freedom_honoured([zone()], [defaulted()])
        self.assertIn("st.defaulted", str(refused.exception))
        self.assertIn("fz.logo", str(refused.exception))
        self.assertIn("PROJECT_RECORD", str(refused.exception))

    def test_a_zone_and_a_statement_may_arrive_as_payloads(self) -> None:
        with self.assertRaises(AmbiguityBlockedError):
            require_freedom_honoured(
                [zone().to_payload()], [defaulted().to_payload()]
            )
        with self.assertRaises(SchemaValidationError):
            require_freedom_honoured([zone()], ["not a statement"])

    def test_a_governed_default_may_close_a_zone(self) -> None:
        by_level = defaulted(
            authority=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value)
        )
        self.assertIsNone(require_freedom_honoured([zone()], [by_level]))

        by_basis = defaulted(
            authority=IntentAuthorityRef(
                authority=AuthorityLevel.PROJECT_RECORD.value,
                basis=AuthorityBasis.POLICY.value,
                policy_ref=S.policy_ref(),
            )
        )
        self.assertIsNone(require_freedom_honoured([zone()], [by_basis]))

    def test_a_human_choice_inside_a_zone_is_what_the_zone_is_for(self) -> None:
        chosen = (
            S.statement("st.human", origin=IntentOrigin.EXPLICIT.value),
            S.statement(
                "st.derived",
                origin=IntentOrigin.DERIVED.value,
                authority=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                source_statement_ids=("st.human",),
            ),
            S.statement(
                "st.guess",
                path=S.ICON,
                origin=IntentOrigin.INFERRED.value,
                authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
                source_statement_ids=("st.human",),
            ),
        )
        self.assertIsNone(require_freedom_honoured([zone(free=(S.LOGO, S.ICON))], list(chosen)))

    def test_a_default_outside_every_zone_is_not_refused(self) -> None:
        self.assertIsNone(require_freedom_honoured([zone()], [defaulted(path=S.ICON)]))
        self.assertIsNone(require_freedom_honoured([], [defaulted()]))
        self.assertIsNone(require_freedom_honoured([zone()], []))

    def test_a_zone_survives_a_superseding_revision_unchanged(self) -> None:
        admitted = S.admitted_revision()
        opened = assessment(
            zones=(zone(),),
            ambiguities=(record(consequence="CREATIVE_FREEDOM", statements=()),),
            revision=admitted,
        )
        follow_up = admitted.supersede(revision_id="rev.8", kind="CLARIFICATION")
        later = assessment(
            zones=tuple(FreedomZone.from_payload(item.to_payload()) for item in opened.freedom_zones),
            ambiguities=tuple(
                AmbiguityRecord.from_payload({**item.to_payload(), "affected_statement_ids": ()})
                for item in opened.ambiguities
            ),
            revision=follow_up,
        )

        self.assertEqual(later.revision_id, "rev.8")
        self.assertEqual(later.freedom_zones, opened.freedom_zones)
        self.assertEqual(later.freedom_as_gap, ())
        self.assertFalse(later.blocks_completion)


class ClarificationRankingTests(unittest.TestCase):
    def queue(self) -> tuple[AmbiguityRecord, ...]:
        return (
            record("am.wide", statements=("st.1", "st.2", "st.3")),
            record("am.narrow", statements=("st.1",)),
            record("am.quality", consequence="QUALITY_CRITICAL", statements=("st.1",)),
            record("am.cost", consequence="COST_CRITICAL", statements=("st.1",)),
            record("am.plain", consequence="NON_BLOCKING", statements=()),
        )

    def test_identical_normalized_inputs_rank_identically(self) -> None:
        first = rank_clarifications(self.queue())
        second = rank_clarifications(self.queue())

        self.assertEqual([item.ambiguity_id for item in first], [item.ambiguity_id for item in second])
        self.assertEqual(first, second)

        shouty = tuple(
            AmbiguityRecord.from_payload(
                {
                    **item.to_payload(),
                    "semantic_paths": [f"  {path.upper()}  " for path in item.semantic_paths],
                }
            )
            for item in self.queue()
        )
        self.assertEqual(
            [item.ambiguity_id for item in rank_clarifications(shouty)],
            [item.ambiguity_id for item in first],
        )

    def test_arrival_order_does_not_move_the_queue(self) -> None:
        forward = [item.ambiguity_id for item in rank_clarifications(self.queue())]
        backward = [item.ambiguity_id for item in rank_clarifications(tuple(reversed(self.queue())))]
        self.assertEqual(forward, backward)
        self.assertEqual(forward, ["am.wide", "am.narrow", "am.quality", "am.cost", "am.plain"])

    def test_a_wording_only_change_does_not_move_the_queue(self) -> None:
        reworded = tuple(
            AmbiguityRecord.from_payload(
                {
                    **item.to_payload(),
                    "question": "Could you say which one you mean?",
                    "candidate_readings": tuple(reversed(item.candidate_readings)),
                    "notes": "restated for the client",
                }
            )
            for item in self.queue()
        )
        self.assertEqual(
            [item.ambiguity_id for item in rank_clarifications(reworded)],
            [item.ambiguity_id for item in rank_clarifications(self.queue())],
        )

    def test_the_order_is_consequence_then_breadth_then_specificity_then_id(self) -> None:
        self.assertEqual(
            [item.sort_key for item in rank_clarifications(self.queue())],
            [(-4, -3, -3, "am.wide"), (-4, -1, -3, "am.narrow"), (-3, -1, -3, "am.quality"), (-2, -1, -3, "am.cost"), (-1, 0, -3, "am.plain")],
        )
        deep = record("am.deep", path=DEEP, statements=("st.1", "st.2"))
        shallow = record("am.shallow", path=S.TONE, statements=("st.1", "st.2"))
        self.assertEqual(
            [item.ambiguity_id for item in rank_clarifications([shallow, deep])],
            ["am.deep", "am.shallow"],
        )
        tie_a = record("am.a", statements=("st.1",))
        tie_b = record("am.b", statements=("st.1",))
        self.assertEqual(
            [item.ambiguity_id for item in rank_clarifications([tie_b, tie_a])], ["am.a", "am.b"]
        )

    def test_the_candidate_carries_only_countable_facts(self) -> None:
        candidate = rank_clarifications([record("am.one", statements=("st.1", "st.2"))])[0]

        self.assertIsInstance(candidate, ClarificationCandidate)
        self.assertEqual(
            sorted(candidate.to_payload()),
            ["ambiguity_id", "breadth", "consequence", "question", "semantic_paths", "specificity"],
        )
        self.assertEqual((candidate.breadth, candidate.specificity), (2, 3))
        self.assertTrue(all(isinstance(item, int) for item in candidate.sort_key[:3]))
        self.assertIsInstance(candidate.sort_key[3], str)
        self.assertEqual(
            ClarificationCandidate.from_payload(candidate.to_payload()).sort_key, candidate.sort_key
        )

    def test_the_assessment_queue_is_the_same_ranking(self) -> None:
        opened = assessment(ambiguities=self.queue())
        self.assertEqual(
            opened.clarification_queue, rank_clarifications(opened.ambiguities)
        )
        self.assertEqual(
            [item.ambiguity_id for item in opened.clarification_queue][:2], ["am.wide", "am.narrow"]
        )
        self.assertEqual(rank_clarifications([]), ())


class AmbiguityVocabularyTests(unittest.TestCase):
    def test_the_nine_kinds_parse_and_refuse_junk(self) -> None:
        self.assertEqual(
            AmbiguityKind.members(),
            [
                "AMBIGUOUS_SCOPE",
                "CONTRADICTION_WITHIN_SOURCE",
                "MISSING_AUTHORITY_BASIS",
                "MISSING_MODALITY",
                "MISSING_VALUE",
                "TERM_OVERLOAD",
                "UNBOUNDED_TOLERANCE",
                "UNRESOLVED_REFERENCE",
                "VAGUE_QUALIFIER",
            ],
        )
        self.assertEqual(len(AmbiguityKind), 9)
        for kind in AmbiguityKind:
            self.assertEqual(AmbiguityKind.parse(kind.value, "kind"), kind)
            self.assertEqual(record(kind=kind.value, consequence="NON_BLOCKING", statements=()).kind, kind.value)
        for junk in ("HUNCH", "", 5, None):
            with self.assertRaises(SchemaValidationError, msg=repr(junk)):
                AmbiguityKind.parse(junk, "kind")

    def test_the_consequence_ladder_is_closed_and_ordered(self) -> None:
        self.assertEqual(
            [(item.value, item.rank) for item in sorted(AmbiguityConsequence, key=lambda each: each.rank)],
            [
                ("CREATIVE_FREEDOM", 0),
                ("NON_BLOCKING", 1),
                ("COST_CRITICAL", 2),
                ("QUALITY_CRITICAL", 3),
                ("BLOCKING", 4),
            ],
        )
        self.assertEqual(len(AmbiguityConsequence), 5)
        for consequence in AmbiguityConsequence:
            parsed = AmbiguityConsequence.parse(f" {consequence.value.lower()} ")
            self.assertEqual(parsed, consequence)
            self.assertEqual(parsed.blocks_completion, consequence is AmbiguityConsequence.BLOCKING)
            self.assertEqual(
                parsed.needs_human,
                consequence
                in {
                    AmbiguityConsequence.BLOCKING,
                    AmbiguityConsequence.QUALITY_CRITICAL,
                    AmbiguityConsequence.COST_CRITICAL,
                },
            )
        with self.assertRaises(SchemaValidationError):
            AmbiguityConsequence.parse("MILDLY_ANNOYING", "consequence")

    def test_a_record_stores_the_canonical_label_not_what_was_typed(self) -> None:
        typed = record("am.typed", consequence="  blocking ", kind="term_overload")
        self.assertEqual(typed.consequence, "BLOCKING")
        self.assertEqual(typed.kind, "TERM_OVERLOAD")
        self.assertEqual(typed.consequence_class, AmbiguityConsequence.BLOCKING)
        with self.assertRaises(SchemaValidationError):
            record("am.bad", consequence="BLOCKING", kind="a feeling")
        with self.assertRaises(SchemaValidationError):
            record("am.worse", consequence="SOMETIMES")

    def test_question_status_is_a_closed_vocabulary(self) -> None:
        self.assertEqual(
            QuestionStatus.members(),
            ["ANSWERED", "DEFERRED", "OPEN", "WAIVED_AS_FREEDOM"],
        )
        waived = S.question(
            blocking=False, status=QuestionStatus.WAIVED_AS_FREEDOM.value
        )
        self.assertTrue(waived.is_open is False)
        self.assertEqual(waived.consequence, AmbiguityConsequence.NON_BLOCKING.value)
        with self.assertRaises(SchemaValidationError):
            S.question(status="FORGOTTEN")


class AmbiguityRecordIntegrityTests(unittest.TestCase):
    def test_paths_are_canonicalised_deduplicated_and_bounded(self) -> None:
        item = record(semantic_paths=(S.TONE, S.LOGO, f" {S.LOGO.upper()} "), path=S.LOGO)
        self.assertEqual(item.semantic_paths, (S.TONE, S.LOGO))
        self.assertEqual(
            record(semantic_paths=tuple(f"brief.path.{i}" for i in range(32))).semantic_paths,
            tuple(sorted({f"brief.path.{i}" for i in range(32)})),
        )
        with self.assertRaises(SchemaValidationError) as too_many:
            record(semantic_paths=tuple(f"brief.path.{i}" for i in range(33)))
        self.assertIn("exceeds 32", str(too_many.exception))

    def test_candidate_readings_are_ordered_and_bounded(self) -> None:
        item = record(readings=("monogram", "wordmark", "letterform"))
        self.assertEqual(item.candidate_readings, ("letterform", "monogram", "wordmark"))
        with self.assertRaises(SchemaValidationError) as too_many:
            record(readings=tuple(f"reading {i}" for i in range(9)))
        self.assertIn("exceeds 8", str(too_many.exception))

    def test_breadth_counts_each_affected_record_once(self) -> None:
        item = record(
            statements=("st.1", "st.2", "st.1"),
            affected_constraint_ids=("cn.a",),
            affected_obligation_ids=("ob.1", "cn.a"),
        )
        self.assertEqual(item.breadth, 4)
        self.assertEqual(item.affected_statement_ids, ("st.1", "st.2"))
        self.assertEqual(item.affected_obligation_ids, ("cn.a", "ob.1"))
        with self.assertRaises(SchemaValidationError):
            record(statements=("Not An Id",))

    def test_touches_follows_the_path_hierarchy(self) -> None:
        item = record(path="brief.visual.logo.mark")
        self.assertTrue(item.touches("brief.visual.logo"))
        self.assertTrue(item.touches("brief.visual.logo.mark"))
        self.assertTrue(item.touches("brief.visual.logo.mark.weight"))
        self.assertFalse(item.touches(S.TONE))
        with self.assertRaises(SchemaValidationError):
            item.touches("Logo Mark")

    def test_the_record_survives_serialisation(self) -> None:
        item = record(
            "am.full",
            consequence="QUALITY_CRITICAL",
            readings=("wordmark",),
            statements=("st.1", "st.2"),
            raised_by=S.ref(RefKind.STATEMENT.value, "st.1"),
            notes="asked twice already",
        )
        rebuilt = AmbiguityRecord.from_payload(item.to_payload())
        self.assertEqual(rebuilt.digest(), item.digest())
        self.assertEqual(rebuilt.consequence, item.consequence)
        self.assertEqual(rebuilt.requires_human, item.requires_human)
        self.assertEqual(rebuilt.affected_statement_ids, item.affected_statement_ids)
        self.assertEqual(rebuilt.raised_by, item.raised_by)
        self.assertEqual(rebuilt.ambiguity_ref.kind, RefKind.AMBIGUITY.value)
        self.assertEqual(rebuilt.ambiguity_ref.content_digest, item.digest())

    def test_an_ambiguity_about_a_vague_term_stays_an_ambiguity(self) -> None:
        vague = record(
            "am.vague",
            kind=AmbiguityKind.VAGUE_QUALIFIER.value,
            consequence="NON_BLOCKING",
            statements=(),
            question=VAGUE,
        )
        opened = assessment(ambiguities=(vague,), zones=(zone(),))
        model = S.model(S.admitted_revision())

        self.assertEqual(vague.kind, AmbiguityKind.VAGUE_QUALIFIER.value)
        self.assertIsNone(model.requested_quality_class)
        self.assertEqual(model.quality_requests(), ())
        self.assertFalse(opened.blocks_completion)
        self.assertEqual(len(opened.ambiguities), 1)


class VagueAdjectiveTests(unittest.TestCase):
    def test_a_named_rung_needs_an_explicit_statement_behind_it(self) -> None:
        revision = S.admitted_revision()
        model = S.model(revision)

        self.assertIsNone(model.requested_quality_class)
        with self.assertRaises(QualityAuthorityError) as refused:
            S.model(revision, requested_quality_class=QualityClass.MASTER.value)
        self.assertIn("vague adjectives", str(refused.exception))

    def test_a_quality_target_must_name_a_rung(self) -> None:
        with self.assertRaises(SchemaValidationError) as unstructured:
            S.statement("st.wish", kind=StatementKind.QUALITY_TARGET.value, value={"note": "premium"})
        self.assertIn("names no rung", str(unstructured.exception))

        named = S.statement(
            "st.rung", kind=StatementKind.QUALITY_TARGET.value, value={"quality_class": "master"}
        )
        self.assertEqual(named.value["quality_class"], "MASTER")
        self.assertTrue(named.quality_class_is_admissible())
        self.assertEqual(S.model(S.revision(9, (named,))).quality_requests(), (named,))

    def test_an_inferred_quality_target_is_not_admissible(self) -> None:
        guessed = S.statement(
            "st.guess",
            kind=StatementKind.QUALITY_TARGET.value,
            origin=IntentOrigin.INFERRED.value,
            authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
            source_statement_ids=("st.rung",),
            value={"quality_class": QualityClass.MASTER.value},
            confidence=0.99,
        )
        self.assertEqual(guessed.origin, IntentOrigin.INFERRED.value)
        self.assertFalse(guessed.quality_class_is_admissible())
        with self.assertRaises(QualityAuthorityError) as refused:
            S.model(S.revision(9, (guessed,)), requested_quality_class=QualityClass.MASTER.value)
        self.assertIn("no explicit QUALITY_TARGET statement", str(refused.exception))

    def test_a_non_target_statement_may_not_claim_a_rung(self) -> None:
        style = S.statement("st.style", kind=StatementKind.STYLE.value, assertion="make it premium")
        self.assertNotIn("quality_class", style.value)
        with self.assertRaises(SchemaValidationError) as refused:
            style.quality_class_is_admissible()
        self.assertIn("cannot carry a quality-class request", str(refused.exception))
        with self.assertRaises(QualityAuthorityError) as model_refused:
            S.model(S.revision(9, (style,)), requested_quality_class=QualityClass.MASTER.value)
        self.assertIn("no explicit QUALITY_TARGET statement", str(model_refused.exception))

    def test_the_requested_rung_can_be_neither_raised_nor_lowered(self) -> None:
        asked = S.statement(
            "st.rung", kind=StatementKind.QUALITY_TARGET.value, value={"quality_class": "MASTER"}
        )
        revision = S.revision(9, (asked,))

        self.assertEqual(
            S.model(revision, requested_quality_class="MASTER").requested_quality_class, "MASTER"
        )
        with self.assertRaises(QualityAuthorityError) as lowered:
            S.model(revision, requested_quality_class="REVIEW")
        self.assertIn("scarcity", str(lowered.exception))
        with self.assertRaises(QualityAuthorityError) as raised:
            S.model(revision, requested_quality_class="ARCHIVAL_MASTER")
        self.assertIn("exceeds the highest explicitly requested", str(raised.exception))

    def test_a_vague_ambiguity_never_becomes_a_quality_request(self) -> None:
        revision = S.admitted_revision()
        opened = assessment(
            ambiguities=(
                record(
                    "am.vague",
                    kind=AmbiguityKind.VAGUE_QUALIFIER.value,
                    consequence="QUALITY_CRITICAL",
                    statements=("st.1",),
                    question=VAGUE,
                ),
            )
        )
        self.assertTrue(
            record(
                "am.vague",
                kind=AmbiguityKind.VAGUE_QUALIFIER.value,
                consequence="QUALITY_CRITICAL",
            ).requires_human
        )
        self.assertFalse(opened.blocks_completion)
        self.assertEqual([item.ambiguity_id for item in opened.quality_critical], ["am.vague"])
        self.assertIsNone(S.model(revision).requested_quality_class)
        with self.assertRaises(QualityAuthorityError) as refused:
            S.model(revision, requested_quality_class="MASTER")
        self.assertIn("vague adjectives", str(refused.exception))

    def test_the_ladder_belongs_to_m01(self) -> None:
        import iris_quality.contracts as m01

        self.assertIs(QualityClass, m01.QualityClass)
        self.assertEqual(
            [item.value for item in QualityClass.ladder()],
            ["DRAFT", "PREVIEW", "REVIEW", "MASTER", "ARCHIVAL_MASTER"],
        )
        self.assertLess(QualityClass.REVIEW.ladder_rank, QualityClass.MASTER.ladder_rank)


if __name__ == "__main__":
    unittest.main()
