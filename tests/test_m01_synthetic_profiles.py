"""Contract tests for the three synthetic profiles demanded by the M01 freeze.

Each behaviour runs against all three profiles, so what is proven here is a
property of the kernel rather than of one hand-tuned fixture.
"""

from __future__ import annotations

import dataclasses
from unittest import TestCase

from examples.m01_synthetic_profiles import (
    GAME_ASSET_ZONES,
    GENERIC_IMAGE,
    ISOMETRIC_GAME_ASSET,
    EXTENSION_PROFILES,
    LOGO_VECTOR,
    NARRATION_REGISTRY,
    PROFILES,
    StaticValidator,
    ThresholdJudge,
    build_evaluator_registry,
    build_profile_registry,
    declare_evaluators,
    profile_for,
)
from iris_quality.contracts import FidelityContract, QualityClass
from iris_quality.decision import DecisionEngine, QualityDecision
from iris_quality.defects import Defect, DefectSeverity
from iris_quality.dimensions import (
    DimensionAssessment,
    GateState,
    UncertaintyState,
)
from iris_quality.errors import (
    EvaluationInputError,
    RegistrationError,
    SchemaValidationError,
)
from iris_quality.judging import (
    JudgeRequest,
    JudgeResult,
    SubjectRef,
    ValidatorOutcome,
    attach_contract_checks,
)
from iris_quality.registry import DomainProfile
from iris_quality.serialization import dumps, loads
from iris_quality.versions import ComponentVersion
from iris_quality.zones import SemanticZone

SUBJECT = SubjectRef(subject_id="asset.synthetic", content_sha256="1" * 64)
PROFILE_NAMES = ("generic-image", "nerim-isometric-asset", "logo-vector")

OBSERVATIONS = {
    "intent-adherence": 0.91,
    "identity-fidelity": 0.88,
    "anatomy-plausibility": 0.79,
    "geometry-integrity": 0.95,
    "silhouette-readability": 0.83,
    "composition-framing": 0.87,
    "material-pbr-fidelity": 0.8,
    "texture-detail-fidelity": 0.82,
    "lighting-shadow-fidelity": 0.86,
    "color-value-hierarchy": 0.84,
    "style-brand-consistency": 0.9,
    "cross-modal-consistency": 0.81,
    "technical-integrity": 0.99,
    "target-platform-fitness": 0.77,
    "perceptual-finish": 0.89,
}


def instantiate(name: str, output_class: QualityClass, **overrides: object) -> FidelityContract:
    return profile_for(name).instantiate(
        contract_id=f"contract.{name}",
        intent=f"deliver a {name} candidate",
        output_class=output_class,
        **overrides,
    )


def request_for(contract: FidelityContract, zone_ids: tuple[str, ...] = ()) -> JudgeRequest:
    return JudgeRequest(
        contract=contract,
        subject=SUBJECT,
        dimension_ids=contract.dimension_ids,
        zone_ids=zone_ids,
    )


def jury(
    contract: FidelityContract,
    *,
    confidence: float = 0.9,
    signed: tuple[str, ...] | None = None,
) -> tuple[ThresholdJudge, ...]:
    """Two jurors that sign off exactly the dimensions the contract reserves.

    Two rather than one because the logo profile demands two evidence items per
    dimension, which exercises the coverage rule instead of dodging it.
    """

    reviewed = tuple(contract.human_review_dimension_ids) if signed is None else signed
    return tuple(
        ThresholdJudge(
            f"jury.{label}",
            observations={
                dimension_id: min(1.0, value + offset)
                for dimension_id, value in OBSERVATIONS.items()
            },
            confidence=confidence,
            human_reviewed=reviewed,
        )
        for label, offset in (("alpha", 0.0), ("beta", 0.02))
    )


def judged(
    contract: FidelityContract,
    judges: tuple[ThresholdJudge, ...],
    zone_ids: tuple[str, ...] = (),
) -> tuple[JudgeResult, ...]:
    request = request_for(contract, zone_ids)
    return tuple(judge.evaluate(request) for judge in judges)


def authorized(
    contract: FidelityContract,
    *,
    results: tuple[JudgeResult, ...] = (),
    assessments: tuple[DimensionAssessment, ...] = (),
) -> FidelityContract:
    """Grant the contract exactly the evaluators that will speak in this fixture.

    Real integrators declare capability up front; the fixtures do the same so a passing profile
    test never depends on the kernel trusting an unnamed component.
    """

    speaking = [item.judge for item in results] + [item.evaluator for item in assessments]
    return declare_evaluators(contract, *speaking)


def decide(
    contract: FidelityContract,
    results: tuple[JudgeResult, ...],
    defects: tuple[Defect, ...] = (),
) -> QualityDecision:
    return DecisionEngine().evaluate(
        authorized(contract, results=results), SUBJECT, results=results, defects=defects
    )


def reported_defect(
    results: tuple[JudgeResult, ...],
    defect_class: str,
    severity: DefectSeverity = DefectSeverity.FATAL,
    zone_id: str | None = None,
) -> tuple[JudgeResult, ...]:
    """Attach one profile-declared defect to the last juror's report."""

    defect = Defect(
        defect_id=f"defect.{defect_class}",
        defect_class=defect_class,
        severity=severity,
        summary="fixture-reported defect",
        dimension_id=results[-1].assessments[0].dimension_id,
        zone_id=zone_id,
    )
    return results[:-1] + (dataclasses.replace(results[-1], defects=(defect,)),)


class ProfileCatalogueTests(TestCase):
    def test_three_domains_are_registered_and_distinct(self) -> None:
        self.assertEqual(len(PROFILES), 3)
        coverage = {name: set(profile_for(name).dimension_ids) for name in PROFILE_NAMES}
        self.assertNotEqual(coverage["generic-image"], coverage["logo-vector"])
        self.assertNotEqual(coverage["generic-image"], coverage["nerim-isometric-asset"])
        self.assertGreaterEqual(
            coverage["nerim-isometric-asset"] - coverage["logo-vector"],
            {"anatomy-plausibility", "geometry-integrity"},
        )

    def test_the_catalogue_is_reachable_only_through_the_registry(self) -> None:
        registry = build_profile_registry()
        self.assertEqual(
            registry.registered_references(),
            tuple(sorted(f"{item.profile_id}@{item.version}" for item in PROFILES.values())),
        )
        with self.assertRaises(RegistrationError):
            registry.register(profile_for("generic-image"))

    def test_an_unknown_domain_is_reported_not_defaulted(self) -> None:
        with self.assertRaises(KeyError):
            profile_for("cinema")


class ProfileContractTests(TestCase):
    def test_every_profile_instantiates_a_legal_contract_per_output_class(self) -> None:
        for name in PROFILE_NAMES:
            for output_class in QualityClass.ladder()[1:]:
                with self.subTest(profile=name, output_class=output_class.value):
                    built = instantiate(name, output_class)
                    self.assertEqual(built.output_class, output_class)
                    self.assertEqual(
                        [rule.target_class.value for rule in built.promotion_rules],
                        [rung.value for rung in QualityClass.ladder()[1:]],
                    )

    def test_every_profile_declares_the_evaluators_it_needs(self) -> None:
        registry = build_evaluator_registry()
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                built = instantiate(name, QualityClass.MASTER)
                covered = {
                    dimension
                    for item in registry.resolve(built)
                    for dimension in item.dimension_ids
                }
                self.assertEqual(set(built.dimension_ids) - covered, set())

    def test_a_profile_cannot_borrow_an_unregistered_evaluator(self) -> None:
        stranger = dataclasses.replace(
            profile_for("generic-image"),
            recommended_evaluators=(ComponentVersion("eval.not-registered", "0.1.0"),),
        )
        with self.assertRaises(RegistrationError):
            build_evaluator_registry().resolve(
                stranger.instantiate(
                    contract_id="contract.stranger",
                    intent="borrow capability the registry never saw",
                    output_class=QualityClass.PREVIEW,
                )
            )


class ProfileDecisionTests(TestCase):
    def test_a_clean_candidate_reaches_its_requested_class(self) -> None:
        for name in PROFILE_NAMES:
            for output_class in (QualityClass.PREVIEW, QualityClass.MASTER):
                with self.subTest(profile=name, output_class=output_class.value):
                    built = instantiate(name, output_class)
                    decision = decide(built, judged(built, jury(built)))
                    self.assertIs(decision.awarded_class, output_class)
                    self.assertEqual(decision.outcome.value, "PROMOTED")
                    self.assertEqual(decision.blockers, ())
                    self.assertEqual(len(decision.judge_references), 2)

    def test_archival_master_stops_until_a_human_decides(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                built = instantiate(name, QualityClass.ARCHIVAL_MASTER)
                held = decide(built, judged(built, jury(built, confidence=1.0)))
                self.assertIs(held.awarded_class, QualityClass.MASTER)
                self.assertIn("human_review_not_recorded", held.blocker_codes)
                self.assertFalse(all(item.human_decision_recorded for item in held.dimensions))

                signed = decide(
                    built,
                    judged(built, jury(built, confidence=1.0, signed=tuple(built.dimension_ids))),
                )
                self.assertIs(signed.awarded_class, QualityClass.ARCHIVAL_MASTER)
                self.assertTrue(all(item.human_decision_recorded for item in signed.dimensions))

    def test_a_fatal_class_from_the_profile_rejects_the_asset(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                built = instantiate(name, QualityClass.MASTER)
                fatal = profile_for(name).fatal_defect_classes[0]
                decision = decide(built, reported_defect(judged(built, jury(built)), fatal))
                self.assertIs(decision.awarded_class, QualityClass.DRAFT)
                self.assertEqual(decision.outcome.value, "REJECTED")
                self.assertIn("fatal_defect_firewall", decision.blocker_codes)

    def test_an_unmeasured_dimension_abstains_instead_of_guessing(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                built = instantiate(name, QualityClass.MASTER)
                missing = built.dimension_ids[0]
                blind = ThresholdJudge(
                    "jury.blind",
                    observations={
                        key: value for key, value in OBSERVATIONS.items() if key != missing
                    },
                    human_reviewed=tuple(built.human_review_dimension_ids),
                )
                results = judged(built, (blind,))
                self.assertEqual([item.dimension_id for item in results[0].abstentions], [missing])
                decision = decide(built, results)
                self.assertIs(decision.awarded_class, QualityClass.DRAFT)
                state = next(item for item in decision.dimensions if item.dimension_id == missing)
                self.assertEqual(state.uncertainty, UncertaintyState.UNKNOWN.value)
                self.assertEqual(state.evidence_count, 0)
                self.assertEqual(state.evaluated_by, ())

    def test_insufficient_machine_confidence_stays_unresolved(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                built = instantiate(name, QualityClass.MASTER)
                reviewed = built.human_review_dimension_ids[0]
                shaky = ThresholdJudge(
                    "jury.shaky",
                    observations=OBSERVATIONS,
                    uncertain_dimensions=(reviewed,),
                    human_reviewed=tuple(
                        item for item in built.human_review_dimension_ids if item != reviewed
                    ),
                )
                decision = decide(built, judged(built, (shaky,)))
                self.assertIs(decision.awarded_class, QualityClass.DRAFT)
                self.assertIn("insufficient_certainty", decision.blocker_codes)
                state = next(item for item in decision.dimensions if item.dimension_id == reviewed)
                self.assertEqual(state.uncertainty, UncertaintyState.UNKNOWN.value)

    def test_jurors_may_not_disagree_past_the_contract_tolerance(self) -> None:
        built = instantiate("nerim-isometric-asset", QualityClass.MASTER)
        wide = (
            ThresholdJudge("jury.wide-a", observations=OBSERVATIONS),
            ThresholdJudge(
                "jury.wide-b",
                observations={key: max(0.0, value - 0.6) for key, value in OBSERVATIONS.items()},
            ),
        )
        decision = decide(built, judged(built, wide))
        self.assertTrue(decision.disagreements)
        self.assertIn("judge_disagreement", decision.blocker_codes)
        self.assertEqual(decision.outcome.value, "HUMAN_REVIEW")


class ProfileValidatorPortTests(TestCase):
    def test_a_failed_structural_check_forces_the_gate(self) -> None:
        built = instantiate("logo-vector", QualityClass.MASTER)
        outcome = StaticValidator(
            results={"technical-integrity": False, "perceptual-finish": True}
        ).validate(built, SUBJECT)
        assessments = attach_contract_checks(built, SUBJECT, outcome)
        technical = next(item for item in assessments if item.dimension_id == "technical-integrity")
        self.assertIs(technical.gate, GateState.FAIL)
        self.assertEqual(technical.uncertainty, UncertaintyState.KNOWN)
        decision = DecisionEngine().evaluate(
            authorized(built, assessments=assessments), SUBJECT, assessments=assessments
        )
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        self.assertIn("dimension_gate_not_pass", decision.blocker_codes)

    def test_an_outcome_from_another_contract_or_asset_is_refused(self) -> None:
        built = instantiate("generic-image", QualityClass.MASTER)
        outcome = StaticValidator(results={"technical-integrity": True}).validate(built, SUBJECT)
        self.assertEqual(
            [item.gate for item in attach_contract_checks(built, SUBJECT, outcome)],
            [GateState.PASS],
        )
        with self.assertRaises(EvaluationInputError):
            attach_contract_checks(built, SUBJECT, _retargeted(outcome, "contract.other"))
        with self.assertRaises(EvaluationInputError):
            attach_contract_checks(
                built, SubjectRef(subject_id="asset.other", content_sha256="2" * 64), outcome
            )

    def test_a_validator_defect_uses_the_profile_severity_not_its_own(self) -> None:
        built = instantiate("nerim-isometric-asset", QualityClass.MASTER)
        outcome = StaticValidator(
            results={"geometry-integrity": False},
            defect_for_failure=("defect.topology", "broken-topology", DefectSeverity.MINOR),
        ).validate(built, SUBJECT)
        assessments = attach_contract_checks(built, SUBJECT, outcome)
        decision = DecisionEngine().evaluate(
            authorized(built, assessments=assessments),
            SUBJECT,
            assessments=assessments,
            defects=outcome.defects,
        )
        finding = decision.findings[0]
        self.assertIs(finding.reported_severity, DefectSeverity.MINOR)
        self.assertIs(finding.effective_severity, DefectSeverity.FATAL)
        self.assertEqual(decision.outcome.value, "REJECTED")


def _retargeted(outcome: ValidatorOutcome, reference: str) -> ValidatorOutcome:
    return dataclasses.replace(outcome, contract_reference=reference)


class SemanticZoneContractTests(TestCase):
    def test_a_zone_tightens_the_profile_it_attaches_to(self) -> None:
        built = instantiate("nerim-isometric-asset", QualityClass.MASTER, zones=GAME_ASSET_ZONES)
        zone_ids = tuple(zone.zone_id for zone in GAME_ASSET_ZONES)
        decision = decide(built, judged(built, jury(built, confidence=0.7), zone_ids))
        self.assertTrue(decision.requires_human_review)
        self.assertIn("zone_confidence_floor", decision.blocker_codes)
        floored = {
            item.dimension_id for item in decision.blockers if item.code == "zone_confidence_floor"
        }
        self.assertIn("anatomy-plausibility", floored)
        self.assertIn("silhouette-readability", floored)

    def test_an_ocular_anatomy_break_is_fatal_inside_the_zone(self) -> None:
        built = instantiate("nerim-isometric-asset", QualityClass.MASTER, zones=GAME_ASSET_ZONES)
        results = judged(built, jury(built), ("zone.ocular",))
        decision = decide(
            built,
            reported_defect(
                results, "anatomy-break", severity=DefectSeverity.MINOR, zone_id="zone.ocular"
            ),
        )
        finding = decision.findings[0]
        self.assertIs(finding.effective_severity, DefectSeverity.FATAL)
        self.assertEqual(finding.zone_ids, ("zone.ocular",))
        self.assertEqual(decision.outcome.value, "REJECTED")

    def test_a_zone_cannot_be_attached_to_an_undeclared_dimension(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            instantiate(
                "logo-vector",
                QualityClass.MASTER,
                zones=(SemanticZone("zone.eyes", "Eyes", ("anatomy-plausibility",)),),
            )
        self.assertIn("outside the contract", str(caught.exception))


class ProfileRecordTests(TestCase):
    def test_the_three_domains_keep_their_own_thresholds(self) -> None:
        floors = {
            name: [
                (rule.target_class.value, rule.minimum_evidence_count)
                for rule in profile_for(name).promotion_rules
            ]
            for name in PROFILE_NAMES
        }
        self.assertEqual(floors["logo-vector"][0], ("PREVIEW", 2))
        self.assertEqual(floors["generic-image"][0], ("PREVIEW", 1))
        self.assertEqual(floors["nerim-isometric-asset"][0], ("PREVIEW", 1))

    def test_a_profile_decision_survives_serialisation_unchanged(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                built = instantiate(name, QualityClass.MASTER)
                decision = decide(built, judged(built, jury(built)))
                rebuilt = loads(dumps(decision))
                self.assertEqual(rebuilt.content_sha256, decision.content_sha256)
                self.assertEqual(rebuilt.contract_reference, built.reference)

    def test_the_fixture_domains_are_the_only_ones_this_file_knows(self) -> None:
        self.assertEqual(GENERIC_IMAGE.profile_id, "profile.generic-image")
        self.assertEqual(ISOMETRIC_GAME_ASSET.profile_id, "profile.nerim-isometric-asset")
        self.assertEqual(LOGO_VECTOR.profile_id, "profile.logo-vector")
        self.assertNotIn("anatomy-plausibility", LOGO_VECTOR.dimension_ids)
        self.assertIn("cross-modal-consistency", LOGO_VECTOR.dimension_ids)
        self.assertIn("target-platform-fitness", ISOMETRIC_GAME_ASSET.dimension_ids)


class NonVisualProfileTests(TestCase):
    """F4: a domain the kernel has never heard of, admitted through the dimension registry.

    Promotion here is produced by the same ``DecisionEngine`` that serves the three visual
    profiles, with no branch on a dimension name anywhere in the kernel.
    """

    AUDIO_OBSERVATIONS = {
        "voice-identity": 0.88,
        "audio-clarity": 0.94,
        "music-coherence": 0.86,
        "narrative-continuity": 0.9,
    }

    def setUp(self) -> None:
        self.built = instantiate("narration-audio", QualityClass.MASTER)

    def _judges(self, audio: dict | None = None) -> tuple[ThresholdJudge, ...]:
        measured = dict(self.AUDIO_OBSERVATIONS if audio is None else audio)
        measured["intent-adherence"] = OBSERVATIONS["intent-adherence"]
        measured["technical-integrity"] = OBSERVATIONS["technical-integrity"]
        return (
            ThresholdJudge("jury.audio-a", observations=measured),
            ThresholdJudge(
                "jury.audio-b",
                observations={key: min(1.0, value + 0.01) for key, value in measured.items()},
            ),
        )

    def test_the_extension_profile_sits_outside_the_frozen_three(self) -> None:
        self.assertEqual(len(PROFILES), 3)
        self.assertEqual(tuple(EXTENSION_PROFILES), ("profile.narration-audio",))
        self.assertEqual(self.built.dimension_registry, NARRATION_REGISTRY)
        self.assertEqual(
            self.built.extension_dimension_ids,
            ("voice-identity", "audio-clarity", "music-coherence", "narrative-continuity"),
        )
        self.assertEqual(build_profile_registry().registered_references(), 
            tuple(sorted(f"{item.profile_id}@{item.version}" for item in PROFILES.values())))

    def test_a_non_visual_domain_promotes_without_any_kernel_edit(self) -> None:
        results = judged(self.built, self._judges())
        decision = decide(self.built, results)
        self.assertEqual(decision.outcome.value, "PROMOTED")
        self.assertIs(decision.awarded_class, QualityClass.MASTER)
        self.assertEqual(decision.blocker_codes, ())
        self.assertEqual(
            [item.dimension_id for item in decision.dimensions], sorted(self.built.dimension_ids)
        )

    def test_a_silent_extension_dimension_bars_promotion(self) -> None:
        partial = {key: value for key, value in self.AUDIO_OBSERVATIONS.items() if key != "audio-clarity"}
        decision = decide(self.built, judged(self.built, self._judges(partial)))
        self.assertNotEqual(decision.outcome.value, "PROMOTED")
        self.assertIn("insufficient_certainty", decision.blocker_codes)
        state = next(
            item for item in decision.dimensions if item.dimension_id == "audio-clarity"
        )
        self.assertEqual(state.uncertainty, UncertaintyState.UNKNOWN.value)
        self.assertEqual(state.evaluated_by, ())

    def test_the_extension_panel_covers_every_admitted_dimension(self) -> None:
        resolved = build_evaluator_registry().resolve(self.built)
        self.assertEqual(
            sorted(item.reference for item in resolved),
            ["eval.loudness-meter@0.1.0", "eval.narration-panel@0.1.0"],
        )
        covered = {dimension for item in resolved for dimension in item.dimension_ids}
        self.assertEqual(covered, set(self.built.dimension_ids))

    def test_an_unnamed_audio_jury_is_refused_like_any_other(self) -> None:
        results = judged(self.built, self._judges())
        with self.assertRaises(EvaluationInputError):
            DecisionEngine().evaluate(self.built, SUBJECT, results=results)

    def test_a_non_visual_dimension_cannot_be_invented_at_registration_time(self) -> None:
        with self.assertRaises(RegistrationError) as caught:
            DomainProfile(
                profile_id="profile.aura",
                version="0.1.0",
                summary="an attempt to smuggle an unadmitted dimension in",
                dimension_ids=("voice-identity", "aura-fidelity"),
                dimension_registry=NARRATION_REGISTRY,
            )
        self.assertIn("outside the registry", str(caught.exception))

    def test_the_non_visual_record_round_trips(self) -> None:
        decision = decide(self.built, judged(self.built, self._judges()))
        self.assertEqual(loads(dumps(decision)).content_sha256, decision.content_sha256)
        rebuilt = FidelityContract.from_payload(self.built.to_payload())
        self.assertEqual(rebuilt.dimension_registry, self.built.dimension_registry)
        self.assertEqual(
            rebuilt.extension_dimension_ids, self.built.extension_dimension_ids
        )
