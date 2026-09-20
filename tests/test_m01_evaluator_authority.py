"""IRIS-WO-0003-CORRECTION-01/02 F2: promotion inputs are bounded by declared *and registered* capability.

CORRECTION-01 introduced :class:`EvaluatorAuthority`. CORRECTION-02 removes its optional
tier: registration is no longer a stronger mode a caller may skip, it is what makes an
authority promotion-capable. A contract-declared evaluator that cannot be resolved in a
registry cannot influence a promotable decision, and the declaration-only preflight form is
refused by the engine instead of silently deciding on a weaker rule.

Nothing here is read out of a payload: an unnamed or unregistered component cannot buy
influence by producing well-formed assessments.
"""

from __future__ import annotations

from unittest import TestCase

from iris_quality.contracts import QualityClass
from iris_quality.decision import DecisionEngine
from iris_quality.defects import DefectSeverity
from iris_quality.errors import EvaluationInputError, RegistrationError
from iris_quality.registry import EvaluatorAuthority, EvaluatorRegistry
from iris_quality.versions import ComponentVersion
from tests.m01_kernel_support import (
    DIMENSIONS,
    EVALUATOR,
    JUDGE,
    SUBJECT,
    assessment,
    contract,
    covered_assessments,
    defect,
    evaluator_descriptor,
    judge_result,
    panel_registry,
    promotion_authority,
)

JUROR = ComponentVersion("jury.foreign", "0.1.0")


def panel(
    *,
    evaluator_coverage: tuple[str, ...] = DIMENSIONS,
    judge_coverage: tuple[str, ...] = DIMENSIONS,
    include_judge: bool = True,
    extra: tuple[ComponentVersion, ...] = (),
) -> EvaluatorRegistry:
    registry = EvaluatorRegistry()
    registry.register(
        evaluator_descriptor(identifier="test-evaluator", dimension_ids=evaluator_coverage)
    )
    if include_judge:
        registry.register(
            evaluator_descriptor(identifier="test-judge", dimension_ids=judge_coverage)
        )
    for component in extra:
        registry.register(
            evaluator_descriptor(
                identifier=component.identifier, version=component.version, dimension_ids=DIMENSIONS
            )
        )
    return registry


class EvaluatorAuthorityTests(TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.target = contract()

    def decide(self, *, results=(), assessments=(), authority):
        return self.engine.evaluate(
            self.target, SUBJECT, assessments=assessments, results=results, authority=authority
        )

    def test_a_judge_version_the_contract_never_declared_is_refused(self) -> None:
        result = judge_result(
            self.target, covered_assessments(), judge=ComponentVersion("test-judge", "2.0.0")
        )
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(
                results=(result,),
                authority=EvaluatorAuthority(
                    self.target,
                    panel(extra=(ComponentVersion("test-judge", "2.0.0"),)),
                ),
            )
        message = str(caught.exception)
        self.assertIn("test-judge@2.0.0 is not declared by contract contract.test", message)
        self.assertIn("does not infer capability from a result payload", message)

    def test_a_strange_judge_is_refused_even_when_its_panel_is_registered(self) -> None:
        result = judge_result(self.target, covered_assessments(), judge=JUROR)
        with self.assertRaises(EvaluationInputError):
            self.decide(
                results=(result,), authority=EvaluatorAuthority(self.target, panel(extra=(JUROR,)))
            )

    def test_a_declared_judge_that_is_not_registered_is_refused(self) -> None:
        result = judge_result(self.target, covered_assessments())
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(
                results=(result,),
                authority=EvaluatorAuthority(self.target, panel(include_judge=False)),
            )
        self.assertIn("not registered", str(caught.exception))

    def test_a_judge_may_not_opine_outside_its_registered_coverage(self) -> None:
        result = judge_result(self.target, covered_assessments())
        authority = EvaluatorAuthority(self.target, panel(judge_coverage=("intent-adherence",)))
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(results=(result,), authority=authority)
        message = str(caught.exception)
        self.assertIn("outside its declared coverage", message)
        self.assertIn("geometry-integrity", message)

    def test_a_direct_assessment_from_an_undeclared_evaluator_is_refused(self) -> None:
        rogue = assessment("intent-adherence", evaluator=ComponentVersion("eval.rogue", "0.1.0"))
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(assessments=(rogue,), authority=promotion_authority(self.target))
        self.assertIn("assessment evaluator eval.rogue@0.1.0 is not declared", str(caught.exception))

    def test_a_direct_assessment_may_not_exceed_its_registered_coverage(self) -> None:
        authority = EvaluatorAuthority(self.target, panel(evaluator_coverage=("intent-adherence",)))
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(assessments=covered_assessments(), authority=authority)
        self.assertIn("outside its declared coverage", str(caught.exception))

    def test_a_declared_and_registered_panel_reaches_a_verdict(self) -> None:
        result = judge_result(self.target, covered_assessments())
        authority = EvaluatorAuthority.resolved(self.target, panel())
        decision = self.decide(results=(result,), authority=authority)
        self.assertEqual(decision.outcome.value, "PROMOTED")
        self.assertEqual(decision.judge_references, (JUDGE.reference,))
        self.assertEqual(
            authority.declared_references(),
            tuple(sorted([EVALUATOR.reference, JUDGE.reference])),
        )

    def test_authority_cannot_be_issued_for_an_unregistered_panel(self) -> None:
        with self.assertRaises(RegistrationError) as caught:
            EvaluatorAuthority.resolved(self.target, EvaluatorRegistry())
        self.assertIn("is not registered", str(caught.exception))

    def test_authority_cannot_be_issued_for_an_incompletely_covered_panel(self) -> None:
        with self.assertRaises(RegistrationError) as caught:
            EvaluatorAuthority.resolved(
                self.target,
                EvaluatorRegistry(
                    [
                        evaluator_descriptor(identifier="test-evaluator"),
                        evaluator_descriptor(identifier="test-judge", dimension_ids=("intent-adherence",)),
                    ]
                ),
            )
        self.assertIn("no registered evaluator", str(caught.exception))

    def test_authority_issued_for_another_contract_is_refused(self) -> None:
        other = contract(contract_id="contract.other")
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(assessments=covered_assessments(), authority=promotion_authority(other))
        self.assertIn("issued for another contract", str(caught.exception))

    def test_defects_spoken_by_an_unnamed_judge_are_refused(self) -> None:
        result = judge_result(
            self.target,
            (),
            judge=JUROR,
            defects=(defect("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),),
        )
        with self.assertRaises(EvaluationInputError):
            self.decide(results=(result,), authority=promotion_authority(self.target))


class MandatoryAuthorityTests(TestCase):
    """CORRECTION-02 §6: a missing registry is a fail-closed condition, not permission."""

    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.target = contract()

    def assert_refused(self, error: BaseException) -> None:
        message = str(error)
        self.assertIn("fail-closed condition, not permission", message)
        self.assertIn("EvaluatorAuthority.resolved(contract, registry)", message)

    def test_a_declared_judge_with_no_registry_fails_closed(self) -> None:
        result = judge_result(self.target, covered_assessments())
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(
                self.target,
                SUBJECT,
                results=(result,),
                authority=EvaluatorAuthority.preflight(self.target),
            )
        self.assertIn("declaration-only", str(caught.exception))
        self.assertIn("EvaluatorAuthority.preflight", str(caught.exception))

    def test_a_declared_direct_assessment_with_no_registry_fails_closed(self) -> None:
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(
                self.target,
                SUBJECT,
                assessments=covered_assessments(),
                authority=EvaluatorAuthority.preflight(self.target),
            )
        self.assertIn("declaration-only", str(caught.exception))

    def test_no_authority_at_all_fails_closed(self) -> None:
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(
                self.target, SUBJECT, assessments=covered_assessments(), authority=None
            )
        self.assert_refused(caught.exception)

    def test_a_preflight_authority_never_awards_anything_above_draft(self) -> None:
        # It refuses to decide at all, so no class can be awarded through the weak path.
        self.assertFalse(EvaluatorAuthority.preflight(self.target).promotion_capable)
        self.assertTrue(promotion_authority(self.target).promotion_capable)
        with self.assertRaises(EvaluationInputError):
            self.engine.evaluate(
                self.target, SUBJECT, assessments=covered_assessments(), authority=None
            )

    def test_a_declared_judge_absent_from_a_supplied_registry_fails_closed(self) -> None:
        result = judge_result(self.target, covered_assessments())
        registry = EvaluatorRegistry(
            [evaluator_descriptor(identifier="test-evaluator", dimension_ids=DIMENSIONS)]
        )
        authority = EvaluatorAuthority(self.target, registry)
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(self.target, SUBJECT, results=(result,), authority=authority)
        self.assertIn("test-judge@1.0.0 is declared by contract", str(caught.exception))
        self.assertIn("but not registered", str(caught.exception))

    def test_a_registered_coverage_mismatch_fails_closed(self) -> None:
        result = judge_result(self.target, covered_assessments())
        narrow = evaluator_descriptor(
            identifier="test-judge", dimension_ids=("intent-adherence", "geometry-integrity")
        )
        registry = panel_registry(self.target, narrow)
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(
                self.target, SUBJECT, results=(result,), authority=EvaluatorAuthority(self.target, registry)
            )
        self.assertIn("outside its declared coverage", str(caught.exception))
        self.assertIn("perceptual-finish", str(caught.exception))

    def test_an_undeclared_evaluator_stays_rejected_even_when_registered(self) -> None:
        registry = panel_registry(self.target)
        registry.register(evaluator_descriptor(identifier="eval.rogue", dimension_ids=DIMENSIONS))
        rogue = assessment("intent-adherence", evaluator=ComponentVersion("eval.rogue", "0.1.0"))
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(
                self.target, SUBJECT, assessments=(rogue,), authority=EvaluatorAuthority(self.target, registry)
            )
        self.assertIn("is not declared by contract", str(caught.exception))

    def test_the_preflight_authority_still_answers_who_is_declared(self) -> None:
        preflight = EvaluatorAuthority.preflight(self.target)
        self.assertEqual(
            preflight.declared_references(),
            tuple(sorted([EVALUATOR.reference, JUDGE.reference])),
        )
        preflight.authorize(JUDGE, DIMENSIONS, role="judge")
        with self.assertRaises(EvaluationInputError):
            preflight.authorize(JUROR, DIMENSIONS, role="judge")

    def test_a_promotion_run_needs_no_caller_supplied_registry_beyond_the_panel(self) -> None:
        decision = self.engine.evaluate(
            self.target,
            SUBJECT,
            assessments=covered_assessments(),
            authority=promotion_authority(self.target),
        )
        self.assertEqual(decision.outcome.value, "PROMOTED")
        self.assertIs(decision.requested_class, QualityClass.MASTER)
