"""IRIS-WO-0003-CORRECTION-01 F2: promotion inputs are bounded by declared capability.

A contract names the versioned evaluators allowed to speak about it, and an
:class:`EvaluatorRegistry` narrows each one to the dimensions it was registered for.
Neither is inferred from a payload: an unnamed component cannot buy influence by
producing well-formed assessments.
"""

from __future__ import annotations

from unittest import TestCase

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

    def decide(self, *, results=(), assessments=(), authority=None):
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
            self.decide(results=(result,), authority=EvaluatorAuthority(self.target, panel(extra=(JUROR,))))

    def test_a_declared_judge_that_is_not_registered_is_refused(self) -> None:
        result = judge_result(self.target, covered_assessments())
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(
                results=(result,), authority=EvaluatorAuthority(self.target, panel(include_judge=False))
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
            self.decide(assessments=(rogue,))
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

    def test_declaration_alone_is_enforced_when_no_registry_is_supplied(self) -> None:
        result = judge_result(self.target, covered_assessments())
        self.assertEqual(self.decide(results=(result,)).outcome.value, "PROMOTED")
        stranger = judge_result(self.target, covered_assessments(), judge=JUROR)
        with self.assertRaises(EvaluationInputError):
            self.decide(results=(stranger,))

    def test_authority_cannot_be_issued_for_an_unregistered_panel(self) -> None:
        with self.assertRaises(RegistrationError) as caught:
            EvaluatorAuthority.resolved(self.target, EvaluatorRegistry())
        self.assertIn("not registered", str(caught.exception))

    def test_authority_issued_for_another_contract_is_refused(self) -> None:
        other = contract(contract_id="contract.other")
        with self.assertRaises(EvaluationInputError) as caught:
            self.decide(assessments=covered_assessments(), authority=EvaluatorAuthority(other))
        self.assertIn("issued for another contract", str(caught.exception))

    def test_defects_spoken_by_an_unnamed_judge_are_refused(self) -> None:
        result = judge_result(
            self.target,
            (),
            judge=JUROR,
            defects=(defect("d.geo", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),),
        )
        with self.assertRaises(EvaluationInputError):
            self.decide(results=(result,))
