"""The M03 -> M01 fidelity bridge: nothing is judged here, and nothing is quietly lowered here.

Fidelity compilation is the only place where IRIS turns an admitted creative brief into something a
quality kernel can verdict on, so every interesting property of it is a refusal. A rung may not travel
on an adjective or on a machine's remaining VRAM. An obligation the selected profile cannot carry may
not be dropped, only reported. Capability belongs to M01's registry and is never granted by the module
that asks for it. And what leaves the bridge has to be M01's own object, accepted by M01's own
serialization, or the compilation has no right to call itself complete.

The classes below follow that law: emission first, then the gap classes that stop emission, then the
no-downgrade shield, then the FATAL floor, then human review, then the set-level split.
"""

from __future__ import annotations

import unittest
from dataclasses import fields, replace

from iris_intent.errors import (
    AdmissionRefusedError,
    AuthorityError,
    CapabilityGapError,
    QualityAuthorityError,
    RefError,
    SchemaValidationError,
    UnsupportedVersionError,
)
from iris_intent.fidelity import (
    COMPILER_VERSION,
    EvidenceClass,
    FidelityCompilation,
    FidelityCompilationGap,
    FidelityCompilationStatus,
    FidelityContractMember,
    FidelityContractSpec,
    GapClass,
    QualityClassBasis,
    QualityIntentProjection,
    QualityObligationTrace,
    QualityChangeClass,
    QualityClassRequest,
    ReferenceRequest,
    ReferenceRole,
    ZoneRequest,
    compile_fidelity_contract,
    dimensions_for,
    quality_contract_delta,
    require_compilable,
    require_no_downgrade,
)
from iris_intent.identity import AuthorityLevel, RefKind, SemanticRef
from iris_intent.versions import content_digest
from iris_quality.contracts import FidelityContract, PromotionRule, QualityClass
from iris_quality.dimensions import DEFAULT_DIMENSION_REGISTRY, DimensionRegistry, FidelityDimension
from iris_quality.registry import DomainProfile, EvaluatorDescriptor, EvaluatorRegistry, TrustTier
from iris_quality.serialization import envelope, from_envelope, validate_payload
from iris_quality.versions import ComponentVersion

from tests import m03_kernel_support as S

IMAGE_PROFILE_ID = "profile.test.image"
AUDIO_PROFILE_ID = "profile.test.audio"
IMAGE_DIMENSIONS = ("identity-fidelity", "intent-adherence", "composition-framing")
AUDIO_DIMENSIONS = ("intent-adherence", "cross-modal-consistency", "perceptual-finish")

FATAL_CLASSES = ("subject-absent",)
MAJOR_CLASSES = ("geometry-break",)
MINOR_CLASSES = ("soft-detail",)
OBSERVATION_CLASSES = ("non-blocking-note",)


def ladder_rules(dimension_ids: tuple[str, ...]) -> tuple[PromotionRule, ...]:
    """A contiguous ladder over the profile's own axes, so no rung gap is incidental."""

    return tuple(
        PromotionRule(target_class=target, required_dimension_ids=tuple(dimension_ids))
        for target in QualityClass.ladder()[1:]
    )


def domain_profile(
    *,
    profile_id: str = IMAGE_PROFILE_ID,
    version: str = "1.0.0",
    dimension_ids: tuple[str, ...] = IMAGE_DIMENSIONS,
    human_review_dimension_ids: tuple[str, ...] = (),
    promotion_rules: tuple[PromotionRule, ...] | None = None,
    recommended_evaluators: tuple[ComponentVersion, ...] | None = None,
    dimension_registry: DimensionRegistry = DEFAULT_DIMENSION_REGISTRY,
) -> DomainProfile:
    """An M01 domain profile admitted the way M01 admits them."""

    return DomainProfile(
        profile_id=profile_id,
        version=version,
        summary="a profile used only to exercise the fidelity bridge",
        dimension_ids=tuple(dimension_ids),
        fatal_defect_classes=FATAL_CLASSES,
        major_defect_classes=MAJOR_CLASSES,
        minor_defect_classes=MINOR_CLASSES,
        observation_defect_classes=OBSERVATION_CLASSES,
        promotion_rules=ladder_rules(dimension_ids) if promotion_rules is None else promotion_rules,
        recommended_evaluators=(
            (ComponentVersion(f"eval.{profile_id}", "1.0.0"),)
            if recommended_evaluators is None
            else recommended_evaluators
        ),
        human_review_dimension_ids=tuple(human_review_dimension_ids),
        dimension_registry=dimension_registry,
    )


def registry_for(*profiles: DomainProfile, extra: tuple[EvaluatorDescriptor, ...] = ()) -> EvaluatorRegistry:
    """Register exactly the panel each profile recommends, covering its own axes."""

    descriptors = [
        EvaluatorDescriptor(
            component=component,
            dimension_ids=profile.dimension_ids,
            deterministic=False,
            trust_tier=TrustTier.CORE,
            dimension_registry=profile.dimension_registry,
        )
        for profile in profiles
        for component in profile.recommended_evaluators
    ]
    return EvaluatorRegistry(descriptors + list(extra))


def descriptor(
    component: ComponentVersion,
    dimension_ids: tuple[str, ...],
    *,
    deterministic: bool = False,
    registry: DimensionRegistry = DEFAULT_DIMENSION_REGISTRY,
) -> EvaluatorDescriptor:
    return EvaluatorDescriptor(
        component=component,
        dimension_ids=tuple(dimension_ids),
        deterministic=deterministic,
        trust_tier=TrustTier.CORE,
        dimension_registry=registry,
    )


def extension_registry(*dimension_ids: str) -> DimensionRegistry:
    """A registry carrying named non-canonical axes, as a contract freeze would."""

    return DimensionRegistry(
        extension_dimensions=tuple(
            FidelityDimension(item, label=item.replace("-", " ").title(), core=False)
            for item in dimension_ids
        )
    )


def profile_ref(profile: DomainProfile):
    return S.ref(RefKind.M01_DOMAIN_PROFILE.value, profile.profile_id, profile.version)


def class_request(
    *,
    requested_class: str = "REVIEW",
    basis: str = QualityClassBasis.EXPLICIT_HUMAN.value,
    authority=None,
    policy_ref=None,
) -> QualityClassRequest:
    return QualityClassRequest(
        requested_class=requested_class,
        basis=basis,
        authority=authority or S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
        policy_ref=policy_ref,
    )


def projection(
    ident: str = "prj.logo",
    obligation: str = "IDENTITY_FIDELITY",
    path: str = S.LOGO,
    **over,
) -> QualityIntentProjection:
    arguments = {"statement_ids": ("st.1",), "mandatory": True}
    arguments.update(over)
    return QualityIntentProjection(
        projection_id=ident, obligation=obligation, semantic_path=path, **arguments
    )


def image_profile() -> DomainProfile:
    return domain_profile()


IMAGE = domain_profile()
AUDIO = domain_profile(profile_id=AUDIO_PROFILE_ID, dimension_ids=AUDIO_DIMENSIONS)


def compile_with(**over):
    """One legal compilation, with every keyword replaceable by a test."""

    selected: DomainProfile = over.pop("profile", IMAGE)
    pinned = over.pop("profile_ref", None) or (
        profile_ref(selected)
        if selected is not None
        else S.ref(RefKind.M01_DOMAIN_PROFILE.value, IMAGE_PROFILE_ID, "1.0.0")
    )
    arguments = {
        "compilation_id": "cmp.hero",
        "subject_ref": S.ref(RefKind.SOURCE.value, "asset.hero.frame"),
        "brief_ref": S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
        "revision_ref": S.ref(RefKind.REVISION.value, "rev.7"),
        "model_fingerprint_digest": S.digest("model.hero"),
        "constraint_fingerprint_digest": S.digest("bundle.hero"),
        "profile": selected,
        "profile_ref": pinned,
        "evaluator_registry": (
            registry_for(selected) if selected is not None else EvaluatorRegistry()
        ),
        "class_request": class_request(),
        "intent_summary": "the hero frame must carry the approved mark",
        "projections": (projection(),),
    }
    arguments.update(over)
    return compile_fidelity_contract(**arguments)


def gap_of(compilation: FidelityCompilation, class_name: GapClass) -> FidelityCompilationGap:
    wanted = class_name.value
    matches = [item for item in compilation.gaps if item.class_name == wanted]
    if not matches:
        raise AssertionError(
            f"no {wanted} gap was recorded; the compilation reported {compilation.gap_classes}"
        )
    return matches[0]


def trace_of(compilation: FidelityCompilation, dimension: str) -> QualityObligationTrace:
    matches = [item for item in compilation.spec.traces if dimension in item.dimension_ids]
    if not matches:
        raise AssertionError(f"no trace binds dimension {dimension}")
    return matches[0]


class TestEmissionOfRealM01Contracts(unittest.TestCase):
    """An admitted brief plus an admitted profile yields M01's object, not a likeness of it."""

    def setUp(self) -> None:
        self.compilation = compile_with()

    def test_a_valid_admitted_profile_compiles_to_an_m01_fidelity_contract(self) -> None:
        self.assertEqual(self.compilation.status, FidelityCompilationStatus.COMPLETE.value)
        self.assertIsInstance(self.compilation.contract, FidelityContract)

    def test_the_emitted_contract_round_trips_through_m01_serialization(self) -> None:
        contract = self.compilation.contract
        payload = contract.to_payload()
        validate_payload("fidelity_contract", payload)
        self.assertEqual(FidelityContract.from_payload(payload), contract)

    def test_the_emitted_contract_round_trips_through_m01_envelopes(self) -> None:
        contract = self.compilation.contract
        self.assertEqual(from_envelope(envelope(contract)), contract)

    def test_the_compilation_validates_the_contract_it_emitted(self) -> None:
        # M03 owns no validation of its own, and refuses a contract that is not M01's type.
        with self.assertRaises(SchemaValidationError) as caught:
            FidelityCompilation(
                status=FidelityCompilationStatus.COMPLETE.value,
                spec=self.compilation.spec,
                contract=dict(self.compilation.contract.to_payload()),
            )
        self.assertIn("FidelityContract", str(caught.exception))

    def test_the_requested_rung_survives_into_the_emitted_contract(self) -> None:
        self.assertIs(self.compilation.contract.output_class, QualityClass.REVIEW)

    def test_the_emitted_panel_is_the_profile_recommendation_and_nothing_else(self) -> None:
        self.assertEqual(
            self.compilation.contract.evaluator_set, IMAGE.recommended_evaluators
        )

    def test_the_compiled_dimensions_are_exactly_the_profile_axes_the_traces_explain(self) -> None:
        spec = self.compilation.spec
        self.assertEqual(
            sorted(spec.dimension_ids), sorted(self.compilation.contract.dimension_ids)
        )

    def test_every_compiled_dimension_reaches_a_source_or_the_profile(self) -> None:
        for trace in self.compilation.spec.traces:
            if trace.covered:
                self.assertTrue(trace.sources, msg=trace.trace_id)

    def test_the_compilation_fingerprint_pins_the_emitted_contract(self) -> None:
        self.assertEqual(
            self.compilation.fingerprint.emitted_contract_digest,
            content_digest(self.compilation.contract.to_payload()),
        )
        self.assertEqual(self.compilation.fingerprint.compiler_version, COMPILER_VERSION)

    def test_a_spec_is_not_a_contract_and_carries_no_decision_authority(self) -> None:
        self.assertFalse(FidelityContractSpec.is_m01_contract)
        self.assertFalse(self.compilation.spec.is_m01_contract)

    def test_the_spec_carries_no_field_naming_an_evaluator(self) -> None:
        names = {item.name for item in fields(FidelityContractSpec)}
        self.assertFalse([item for item in names if "evaluator" in item])

    def test_require_compilable_hands_back_the_emitted_contract(self) -> None:
        self.assertIs(require_compilable(self.compilation), self.compilation.contract)

    def test_the_compilation_records_obligations_and_never_evidence(self) -> None:
        # A contract states what must be proven; proof arrives later through M01's judging path.
        names = {item.name for item in fields(FidelityCompilation)} | {
            item.name for item in fields(FidelityContractSpec)
        }
        self.assertFalse(
            [item for item in names if any(key in item for key in ("evidence", "verdict", "assessment"))]
        )


class TestGapClassesThatStopCompilation(unittest.TestCase):
    """§17 and §18: a requirement that cannot be expressed is named, never quietly forgotten."""

    def test_no_profile_selected_blocks_even_describing_a_contract(self) -> None:
        compilation = compile_with(profile=None)
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        self.assertIsNone(compilation.spec)
        gap = gap_of(compilation, GapClass.MISSING_DOMAIN_PROFILE)
        self.assertIn("domain profile", gap.detail)
        self.assertTrue(gap.source_refs, msg="a gap with no source is a dropped requirement")

    def test_a_blocked_compilation_refuses_the_contract_by_naming_the_input(self) -> None:
        compilation = compile_with(profile=None)
        with self.assertRaises(AdmissionRefusedError) as caught:
            require_compilable(compilation)
        self.assertIn("MISSING_DOMAIN_PROFILE", str(caught.exception))

    def test_a_ref_pointing_at_another_profile_blocks_the_compilation(self) -> None:
        other = domain_profile(version="2.0.0")
        compilation = compile_with(profile_ref=profile_ref(other))
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        self.assertIn(
            GapClass.PROFILE_POLICY_CONFLICT.value, compilation.gap_classes
        )

    def test_an_unpinned_profile_ref_cannot_be_constructed(self) -> None:
        with self.assertRaises(RefError) as caught:
            SemanticRef(
                kind=RefKind.M01_DOMAIN_PROFILE.value,
                ref_id=IMAGE_PROFILE_ID,
                version=None,
                content_digest=S.digest(IMAGE_PROFILE_ID),
            )
        self.assertIn("pin the version", str(caught.exception))

    def test_a_registry_version_other_than_the_profiles_blocks_the_compilation(self) -> None:
        compilation = compile_with(dimension_registry_version="m01-dimension-registry-v9")
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        self.assertIn(GapClass.REGISTRY_VERSION_MISMATCH.value, compilation.gap_classes)

    def test_an_open_blocking_ambiguity_blocks_the_compilation(self) -> None:
        compilation = compile_with(blocking_ambiguity_refs=[S.ref(RefKind.AMBIGUITY.value, "am.iris")])
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        gap = gap_of(compilation, GapClass.BLOCKING_AMBIGUITY)
        self.assertIn("am.iris", gap.detail)

    def test_a_freshness_vector_for_another_brief_blocks_the_compilation(self) -> None:
        item = S.dependency("dep.other")
        vector = S.vector(
            [item],
            S.upstream_matching([item]),
        )
        # The vector describes BRIEF_ID, so compiling a different brief is a stale input by name.
        compilation = compile_with(
            freshness=vector,
            brief_ref=S.ref(RefKind.BRIEF.value, "brief.someone.else"),
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        self.assertIn(GapClass.STALE_COMPILATION_INPUT.value, compilation.gap_classes)

    def test_a_stale_source_dependency_blocks_the_compilation(self) -> None:
        item = S.dependency("dep.hero", path=S.LOGO)
        vector = S.vector([item], S.upstream_matching([item], moved=["src.art"]))
        compilation = compile_with(freshness=vector)
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        gap = gap_of(compilation, GapClass.STALE_COMPILATION_INPUT)
        self.assertIn("SOURCE_REVISION", gap.detail)

    def test_an_unknown_m01_contract_version_is_refused_before_anything_is_emitted(self) -> None:
        with self.assertRaises(UnsupportedVersionError) as caught:
            compile_with(m01_contract_version="m01-quality-contract-v9")
        self.assertIn("m01-quality-contract-v9", str(caught.exception))

    def test_a_registry_object_that_is_not_m01s_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compile_with(evaluator_registry={"evaluator": "granted"})
        self.assertIn("EvaluatorRegistry", str(caught.exception))


class TestUnknownDimensionsBlock(unittest.TestCase):
    """§6: an axis nobody admits stays a declared requirement, not a free-form string."""

    def test_an_unregistered_extension_dimension_stops_the_compilation(self) -> None:
        compilation = compile_with(projections=(projection("prj.voice", "VOICE_IDENTITY", S.TONE),))
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.INCOMPLETE)
        self.assertIsNone(compilation.contract)
        gap = gap_of(compilation, GapClass.MISSING_DIMENSION)
        self.assertEqual(gap.missing_dimension_id, "voice-identity")
        self.assertEqual(gap.obligation, "VOICE_IDENTITY")

    def test_the_uncompilable_obligation_is_still_carried_as_an_uncovered_trace(self) -> None:
        compilation = compile_with(projections=(projection("prj.voice", "VOICE_IDENTITY", S.TONE),))
        self.assertIn("VOICE_IDENTITY", compilation.unrepresentable_obligations)
        uncovered = [item for item in compilation.spec.traces if not item.covered]
        self.assertEqual(len(uncovered), 1)
        self.assertEqual(uncovered[0].gap_id, gap_of(compilation, GapClass.MISSING_DIMENSION).gap_id)

    def test_a_compilation_across_a_missing_dimension_refuses_to_emit(self) -> None:
        compilation = compile_with(projections=(projection("prj.voice", "VOICE_IDENTITY", S.TONE),))
        with self.assertRaises(CapabilityGapError) as caught:
            require_compilable(compilation)
        self.assertIn("MISSING_DIMENSION", str(caught.exception))

    def test_a_registered_extension_dimension_compiles(self) -> None:
        registry = extension_registry("voice-identity")
        profile = domain_profile(
            dimension_ids=IMAGE_DIMENSIONS + ("voice-identity",),
            human_review_dimension_ids=(),
            dimension_registry=registry,
        )
        compilation = compile_with(
            profile=profile,
            evaluator_registry=registry_for(profile),
            projections=(
                projection(),
                projection("prj.voice", "VOICE_IDENTITY", S.TONE, requested_dimensions=("voice-identity",)),
            ),
            model_fingerprint_digest=S.digest("model.voice"),
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.COMPLETE)
        self.assertIn("voice-identity", compilation.contract.dimension_ids)
        self.assertEqual(compilation.contract.dimension_registry.version, registry.version)

    def test_a_soft_obligation_the_profile_cannot_judge_is_reported_without_stopping_work(self) -> None:
        compilation = compile_with(
            projections=(projection("prj.voice", "VOICE_IDENTITY", S.TONE, mandatory=False),)
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.COMPLETE)
        gap = gap_of(compilation, GapClass.MISSING_DIMENSION)
        self.assertFalse(gap.mandatory_origin)
        self.assertFalse(gap.blocks_completion)
        self.assertIn("VOICE_IDENTITY", compilation.spec.uncovered_obligations)


class TestEvaluatorCapabilityFirewall(unittest.TestCase):
    """§8: capability is resolved by M01's registry, and M03 has no field for granting it."""

    def test_an_axis_no_registered_evaluator_covers_blocks_emission(self) -> None:
        thin = EvaluatorRegistry(
            [descriptor(IMAGE.recommended_evaluators[0], IMAGE.dimension_ids[:1])]
        )
        compilation = compile_with(evaluator_registry=thin)
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.INCOMPLETE)
        gap = gap_of(compilation, GapClass.MISSING_EVALUATOR_CAPABILITY)
        self.assertIn(gap.missing_dimension_id, IMAGE.dimension_ids)

    def test_a_missing_capability_refuses_to_emit_and_names_the_dimension(self) -> None:
        thin = EvaluatorRegistry(
            [descriptor(IMAGE.recommended_evaluators[0], ("identity-fidelity",))]
        )
        compilation = compile_with(evaluator_registry=thin)
        with self.assertRaises(CapabilityGapError) as caught:
            require_compilable(compilation)
        self.assertIn("intent-adherence", str(caught.exception))

    def test_a_requirement_stays_declared_when_nobody_can_prove_it(self) -> None:
        thin = EvaluatorRegistry(
            [descriptor(IMAGE.recommended_evaluators[0], ("identity-fidelity",))]
        )
        compilation = compile_with(evaluator_registry=thin)
        gap = gap_of(compilation, GapClass.MISSING_EVALUATOR_CAPABILITY)
        self.assertIn(
            gap.missing_dimension_id, {"intent-adherence", "composition-framing"}
        )
        citing = [item for item in compilation.spec.traces if item.gap_id == gap.gap_id]
        self.assertTrue(citing, msg="the unprovable axis left no trace at all")

    def test_m03_cannot_widen_the_panel_to_get_past_a_capability_refusal(self) -> None:
        # The bridge has no argument that appends an evaluator, so the only route is M01's registry.
        import inspect

        parameters = inspect.signature(compile_fidelity_contract).parameters
        self.assertFalse([name for name in parameters if "evaluator" in name and name != "evaluator_registry"])
        self.assertEqual(
            set(require_compilable(compile_with()).evaluator_set),
            set(IMAGE.recommended_evaluators),
        )

    def test_a_deterministic_registration_changes_the_evidence_class_not_the_authority(self) -> None:
        profile = IMAGE
        panel = descriptor(profile.recommended_evaluators[0], profile.dimension_ids, deterministic=True)
        compilation = compile_with(
            profile=profile, evaluator_registry=EvaluatorRegistry([panel])
        )
        trace = trace_of(compilation, "identity-fidelity")
        self.assertEqual(trace.evidence_requirements, (EvidenceClass.DETERMINISTIC_VALIDATOR.value,))

    def test_an_automated_registration_records_an_automated_evidence_class(self) -> None:
        trace = trace_of(compile_with(), "identity-fidelity")
        self.assertEqual(trace.evidence_requirements, (EvidenceClass.AUTOMATED_EVALUATOR.value,))


class TestQualityClassBasis(unittest.TestCase):
    """§5, §24: a rung is a decision, so it has to arrive with the authority that made it."""

    def test_a_hardware_basis_cannot_be_attached_to_a_target_at_all(self) -> None:
        with self.assertRaises(QualityAuthorityError) as caught:
            class_request(basis="HARDWARE_CONSTRAINT")
        self.assertIn("HARDWARE_CONSTRAINT", str(caught.exception))

    def test_a_provider_capability_list_cannot_set_a_rung(self) -> None:
        with self.assertRaises(QualityAuthorityError) as caught:
            class_request(basis="PROVIDER_CAPABILITY")
        self.assertIn("PROVIDER_CAPABILITY", str(caught.exception))

    def test_every_scarcity_and_adjective_spelling_is_refused_by_name(self) -> None:
        for token in (
            "ADJECTIVE_TEXT",
            "CINEMATIC_TEXT",
            "PREMIUM_TEXT",
            "MODEL_RECOMMENDATION",
            "VRAM_CONSTRAINT",
            "COST_TARGET",
            "SCHEDULE_PRESSURE",
            "CONFIDENCE_SCORE",
        ):
            with self.subTest(basis=token):
                with self.assertRaises(QualityAuthorityError) as caught:
                    class_request(basis=token)
                self.assertIn(token, str(caught.exception))

    def test_a_policy_rung_has_to_cite_the_policy_that_set_it(self) -> None:
        with self.assertRaises(QualityAuthorityError) as caught:
            class_request(basis=QualityClassBasis.PROJECT_POLICY.value)
        self.assertIn("must cite the policy", str(caught.exception))

    def test_a_governed_policy_rung_with_its_ref_compiles(self) -> None:
        request = class_request(
            basis=QualityClassBasis.DELIVERY_POLICY.value, policy_ref=S.policy_ref()
        )
        self.assertIs(request.class_enum, QualityClass.REVIEW)
        self.assertTrue(request.policy_ref.text.startswith("POLICY"))

    def test_an_inferred_authority_cannot_grant_itself_a_quality_target(self) -> None:
        with self.assertRaises(AuthorityError) as caught:
            class_request(
                authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
            )
        self.assertIn("HUMAN_OWNER", str(caught.exception))

    def test_a_project_record_may_rest_a_profile_rule_rung(self) -> None:
        request = QualityClassRequest(
            requested_class="PREVIEW",
            basis=QualityClassBasis.PROFILE_RULE.value,
            authority=S.authority_ref(AuthorityLevel.PROJECT_RECORD.value),
        )
        self.assertIs(request.class_enum, QualityClass.PREVIEW)

    def test_a_project_record_cannot_set_the_owner_rung(self) -> None:
        with self.assertRaises(AuthorityError):
            QualityClassRequest(
                requested_class="MASTER",
                basis=QualityClassBasis.EXPLICIT_HUMAN.value,
                authority=S.authority_ref(AuthorityLevel.PROJECT_RECORD.value),
            )

    def test_no_field_of_a_target_request_can_carry_a_resource_limit(self) -> None:
        names = {item.name for item in fields(QualityClassRequest)}
        self.assertFalse(
            [item for item in names if any(key in item for key in ("vram", "hardware", "cost", "budget"))]
        )
        self.assertFalse(QualityClassRequest.scarcity_can_change_class)

    def test_a_stated_rung_is_returned_unchanged_when_nothing_moves(self) -> None:
        self.assertIs(
            require_no_downgrade(QualityClass.MASTER, "MASTER", basis="HARDWARE_CONSTRAINT"),
            QualityClass.MASTER,
        )

    def test_a_profile_rule_cannot_lower_what_an_owner_set(self) -> None:
        with self.assertRaises(QualityAuthorityError) as caught:
            require_no_downgrade(
                QualityClass.MASTER, QualityClass.REVIEW, basis=QualityClassBasis.PROFILE_RULE.value
            )
        self.assertIn("PROFILE_RULE", str(caught.exception))

    def test_a_governed_policy_may_lower_a_rung_owns(self) -> None:
        self.assertIs(
            require_no_downgrade(
                QualityClass.MASTER,
                QualityClass.REVIEW,
                basis=QualityClassBasis.DELIVERY_POLICY.value,
            ),
            QualityClass.REVIEW,
        )

    def test_an_unstated_basis_is_refused_rather_than_guessed(self) -> None:
        with self.assertRaises(QualityAuthorityError) as caught:
            require_no_downgrade(QualityClass.MASTER, QualityClass.DRAFT)
        self.assertIn("unstated", str(caught.exception))

    def test_a_rung_the_profile_cannot_earn_is_reported_instead_of_lowered(self) -> None:
        truncated = domain_profile(
            promotion_rules=ladder_rules(IMAGE_DIMENSIONS)[:1],
        )
        compilation = compile_with(profile=truncated)
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.INCOMPLETE)
        self.assertIsNone(compilation.contract)
        gap = gap_of(compilation, GapClass.UNSUPPORTED_QUALITY_CLASS)
        self.assertIn("REVIEW", gap.detail)
        self.assertIs(compilation.spec.requested_class, QualityClass.REVIEW)

    def test_a_recompiled_lower_rung_without_the_right_authority_is_refused(self) -> None:
        previous = compile_with(class_request=class_request(requested_class="MASTER"))
        self.assertIs(previous.status_enum, FidelityCompilationStatus.COMPLETE)
        lowered = compile_with(
            class_request=class_request(
                requested_class="REVIEW", basis=QualityClassBasis.PROFILE_RULE.value
            ),
            previous=previous,
        )
        self.assertIs(lowered.status_enum, FidelityCompilationStatus.INCOMPLETE)
        self.assertIsNone(lowered.contract)
        gap = gap_of(lowered, GapClass.UNSUPPORTED_QUALITY_CLASS)
        self.assertIn("down", gap.detail)

    def test_an_owner_may_recompile_a_lower_rung_it_now_states(self) -> None:
        previous = compile_with(class_request=class_request(requested_class="MASTER"))
        moved = compile_with(
            class_request=class_request(requested_class="REVIEW"), previous=previous
        )
        self.assertIs(moved.status_enum, FidelityCompilationStatus.COMPLETE)
        self.assertIs(moved.contract.output_class, QualityClass.REVIEW)

    def test_a_contract_may_not_arrive_on_a_lower_rung_than_it_compiled(self) -> None:
        compilation = compile_with()
        weakened = replace(compilation.contract, output_class=QualityClass.PREVIEW)
        with self.assertRaises(QualityAuthorityError) as caught:
            FidelityCompilation(
                status=FidelityCompilationStatus.COMPLETE.value,
                spec=compilation.spec,
                contract=weakened,
            )
        self.assertIn("does not get to move the target", str(caught.exception))

    def test_a_contract_may_not_judge_an_axis_the_compilation_never_traced(self) -> None:
        compilation = compile_with()
        smuggled = replace(
            compilation.contract,
            dimension_ids=compilation.contract.dimension_ids + ("lighting-shadow-fidelity",),
        )
        with self.assertRaises(SchemaValidationError) as caught:
            FidelityCompilation(
                status=FidelityCompilationStatus.COMPLETE.value,
                spec=compilation.spec,
                contract=smuggled,
            )
        self.assertIn("lighting-shadow-fidelity", str(caught.exception))


class TestHardGateAndFatalSemantics(unittest.TestCase):
    """§13: a brief may sharpen what a defect costs, and never blunt it."""

    def test_a_zone_cannot_relabel_a_profile_fatal_class(self) -> None:
        zone = ZoneRequest(
            zone_id="zone.clearspace",
            label="logo clear space",
            dimension_ids=("identity-fidelity",),
            severity_overrides={"subject-absent": "MINOR"},
        )
        compilation = compile_with(zone_requests=[zone])
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        self.assertIsNone(compilation.spec)
        gap = gap_of(compilation, GapClass.PROFILE_POLICY_CONFLICT)
        self.assertIn("subject-absent", gap.detail)
        self.assertIn("FATAL", gap.detail)

    def test_relaxing_any_profile_declared_severity_is_refused(self) -> None:
        for defect_class, weaker in (
            ("geometry-break", "OBSERVATION"),
            ("soft-detail", "OBSERVATION"),
            ("subject-absent", "OBSERVATION"),
        ):
            with self.subTest(defect_class=defect_class):
                with self.assertRaises(AdmissionRefusedError) as caught:
                    require_compilable(
                        compile_with(
                            zone_requests=[
                                ZoneRequest(
                                    zone_id="zone.relax",
                                    label="relax",
                                    dimension_ids=("identity-fidelity",),
                                    severity_overrides={defect_class: weaker},
                                )
                            ]
                        )
                    )
                self.assertIn("below the profile's own severity", str(caught.exception))

    def test_a_zone_may_raise_what_a_defect_costs(self) -> None:
        zone = ZoneRequest(
            zone_id="zone.face",
            label="the face",
            dimension_ids=("identity-fidelity",),
            severity_overrides={"soft-detail": "MAJOR"},
        )
        compilation = compile_with(zone_requests=[zone])
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.COMPLETE)
        emitted = compilation.contract.zones[0]
        self.assertEqual(emitted.zone_id, "zone.face")

    def test_a_raised_zone_severity_never_relaxes_the_declared_class(self) -> None:
        from iris_quality.defects import DefectSeverity
        from iris_quality.zones import SemanticZone

        zone = ZoneRequest(
            zone_id="zone.face",
            label="the face",
            dimension_ids=("identity-fidelity",),
            severity_overrides={"soft-detail": "MAJOR"},
        )
        emitted = compile_with(zone_requests=[zone]).contract.zones[0]
        self.assertIs(
            emitted.effective_severity("soft-detail", DefectSeverity.MINOR), DefectSeverity.MAJOR
        )
        # And the floor holds even against a zone someone built by hand: M01 never reads down.
        blunt = SemanticZone(
            zone_id="zone.blunt",
            label="an attempted relaxation",
            dimension_ids=("identity-fidelity",),
            severity_overrides={"subject-absent": DefectSeverity.MINOR},
        )
        self.assertIs(
            blunt.effective_severity("subject-absent", DefectSeverity.FATAL), DefectSeverity.FATAL
        )

    def test_an_override_for_an_undeclared_defect_class_cannot_be_represented(self) -> None:
        compilation = compile_with(
            zone_requests=[
                ZoneRequest(
                    zone_id="zone.ghost",
                    label="a class nobody declares",
                    dimension_ids=("identity-fidelity",),
                    severity_overrides={"never-declared": "FATAL"},
                )
            ]
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.INCOMPLETE)
        self.assertIn(GapClass.UNREPRESENTABLE_CONSTRAINT.value, compilation.gap_classes)

    def test_a_zone_over_an_unjudged_axis_is_a_missing_dimension_not_silence(self) -> None:
        compilation = compile_with(
            zone_requests=[
                ZoneRequest(
                    zone_id="zone.light",
                    label="lighting",
                    dimension_ids=("lighting-shadow-fidelity",),
                )
            ]
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.INCOMPLETE)
        gap = gap_of(compilation, GapClass.MISSING_DIMENSION)
        self.assertEqual(gap.missing_dimension_id, "lighting-shadow-fidelity")

    def test_a_zone_cannot_be_declared_over_nothing(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            ZoneRequest(zone_id="zone.empty", label="nothing", dimension_ids=())
        self.assertIn("binds no dimension", str(caught.exception))

    def test_a_zone_cannot_smuggle_a_confidence_floor_out_of_range(self) -> None:
        with self.assertRaises(SchemaValidationError):
            ZoneRequest(
                zone_id="zone.face",
                label="the face",
                dimension_ids=("identity-fidelity",),
                minimum_confidence=1.4,
            )

    def test_the_compiled_contract_keeps_every_profile_hard_gate(self) -> None:
        profile = domain_profile(
            promotion_rules=(
                PromotionRule(
                    target_class=QualityClass.PREVIEW,
                    required_dimension_ids=IMAGE_DIMENSIONS,
                ),
                PromotionRule(
                    target_class=QualityClass.REVIEW,
                    required_dimension_ids=IMAGE_DIMENSIONS,
                    hard_gate_dimension_ids=("identity-fidelity",),
                ),
                PromotionRule(
                    target_class=QualityClass.MASTER,
                    required_dimension_ids=IMAGE_DIMENSIONS,
                ),
                PromotionRule(
                    target_class=QualityClass.ARCHIVAL_MASTER,
                    required_dimension_ids=IMAGE_DIMENSIONS,
                ),
            )
        )
        contract = compile_with(profile=profile).contract
        rule = contract.rule_for(QualityClass.REVIEW)
        self.assertEqual(rule.hard_gate_dimension_ids, ("identity-fidelity",))

    def test_no_compilation_argument_drops_a_profile_promotion_rule(self) -> None:
        contract = compile_with().contract
        self.assertEqual(contract.promotion_rules, IMAGE.promotion_rules)
        self.assertFalse(contract.promotion_rules[0].requires_human_review)

    def test_the_compiled_contract_never_shares_a_fatal_class_as_a_minor_one(self) -> None:
        contract = compile_with().contract
        self.assertEqual(contract.fatal_defect_classes, FATAL_CLASSES)
        self.assertFalse(set(contract.fatal_defect_classes) & set(contract.minor_defect_classes))


class TestHumanReviewObligations(unittest.TestCase):
    """§14: the bridge compiles the requirement that a person must answer, and never answers it."""

    def setUp(self) -> None:
        self.profile = domain_profile(human_review_dimension_ids=("identity-fidelity",))

    def compile(self, **over):
        arguments = {
            "profile": self.profile,
            "evaluator_registry": registry_for(self.profile),
            "human_review_dimension_ids": ["identity-fidelity"],
        }
        arguments.update(over)
        return compile_with(**arguments)

    def test_a_routed_dimension_reaches_the_contract_as_a_review_obligation(self) -> None:
        compilation = self.compile()
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.COMPLETE)
        self.assertEqual(
            compilation.contract.human_review_dimension_ids, ("identity-fidelity",)
        )

    def test_the_obligation_names_the_evidence_it_still_waits_for(self) -> None:
        trace = trace_of(self.compile(), "identity-fidelity")
        self.assertIn(EvidenceClass.HUMAN_DECISION.value, trace.evidence_requirements)
        self.assertTrue(trace.human_review_required)

    def test_requesting_a_review_invents_no_verdict(self) -> None:
        payload = self.compile().contract.to_payload()
        self.assertTrue(payload["human_review_dimension_ids"])
        self.assertFalse([key for key in payload if "assessment" in key or "decision" in key])
        self.assertFalse([key for key in dir(FidelityCompilation) if key == "verdict"])

    def test_an_unjudged_axis_cannot_be_protected_by_a_review(self) -> None:
        compilation = self.compile(human_review_dimension_ids=["voice-identity"])
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.INCOMPLETE)
        gap = gap_of(compilation, GapClass.MISSING_DIMENSION)
        self.assertEqual(gap.missing_dimension_id, "voice-identity")

    def test_m03_cannot_add_a_review_obligation_m01_would_not_honour(self) -> None:
        unrouted = domain_profile()
        compilation = self.compile(
            profile=unrouted,
            evaluator_registry=registry_for(unrouted),
            human_review_dimension_ids=["identity-fidelity"],
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.BLOCKED)
        self.assertIn(GapClass.PROFILE_POLICY_CONFLICT.value, compilation.gap_classes)

    def test_a_compiled_review_obligation_cannot_be_dropped_on_the_way_out(self) -> None:
        compilation = self.compile()
        silent = replace(compilation.contract, human_review_dimension_ids=())
        with self.assertRaises(SchemaValidationError) as caught:
            FidelityCompilation(
                status=FidelityCompilationStatus.COMPLETE.value,
                spec=compilation.spec,
                contract=silent,
            )
        self.assertIn("identity-fidelity", str(caught.exception))

    def test_a_trace_cannot_claim_a_review_it_never_asks_for_as_evidence(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            QualityObligationTrace(
                trace_id="tr.ghost",
                semantic_path=S.LOGO,
                obligation="IDENTITY_FIDELITY",
                dimension_ids=("identity-fidelity",),
                statement_ids=("st.1",),
                evidence_requirements=(EvidenceClass.AUTOMATED_EVALUATOR.value,),
                human_review_required=True,
            )
        self.assertIn("HUMAN_DECISION", str(caught.exception))


class TestReferenceRoles(unittest.TestCase):
    """§11: the role decides whether a reference binds, so a mood board cannot become a gate."""

    def test_an_unresolved_must_match_reference_stops_emission(self) -> None:
        compilation = compile_with(
            references=[
                ReferenceRequest(
                    ref_id="ref.brandmark",
                    role=ReferenceRole.MUST_MATCH.value,
                    resolved=False,
                    source_ref=S.ref(RefKind.SOURCE.value, "src.brandmark"),
                    semantic_path=S.LOGO,
                )
            ]
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.INCOMPLETE)
        gap = gap_of(compilation, GapClass.UNRESOLVED_REFERENCE)
        self.assertIn("ref.brandmark", gap.detail)
        with self.assertRaises(CapabilityGapError):
            require_compilable(compilation)

    def test_a_resolved_strict_reference_reaches_the_contract(self) -> None:
        compilation = compile_with(
            references=[
                ReferenceRequest(
                    ref_id="ref.brandmark", role=ReferenceRole.IDENTITY_ANCHOR.value
                )
            ]
        )
        self.assertIn("ref.brandmark", compilation.contract.reference_ids)

    def test_an_unresolved_inspiration_neither_blocks_nor_binds(self) -> None:
        compilation = compile_with(
            references=[
                ReferenceRequest(
                    ref_id="ref.mood", role=ReferenceRole.INSPIRATION.value, resolved=False
                )
            ]
        )
        self.assertIs(compilation.status_enum, FidelityCompilationStatus.COMPLETE)
        self.assertEqual(compilation.spec.inspiration_ref_ids, ("ref.mood",))
        self.assertNotIn("ref.mood", compilation.contract.reference_ids)

    def test_an_inspiration_cannot_be_promoted_into_a_fidelity_obligation(self) -> None:
        compilation = compile_with(
            references=[ReferenceRequest(ref_id="ref.mood", role=ReferenceRole.INSPIRATION.value)]
        )
        promoted = replace(
            compilation.contract,
            reference_ids=compilation.contract.reference_ids + ("ref.mood",),
        )
        with self.assertRaises(SchemaValidationError) as caught:
            FidelityCompilation(
                status=FidelityCompilationStatus.COMPLETE.value,
                spec=compilation.spec,
                contract=promoted,
            )
        self.assertIn("ref.mood", str(caught.exception))

    def test_only_inspiration_is_non_strict(self) -> None:
        self.assertFalse(ReferenceRole.INSPIRATION.strict)
        for role in (
            ReferenceRole.IDENTITY_ANCHOR,
            ReferenceRole.MUST_MATCH,
            ReferenceRole.QUALITY_BASELINE,
            ReferenceRole.ANTI_REFERENCE_EVIDENCE,
        ):
            with self.subTest(role=role.value):
                self.assertTrue(role.strict)


def member_for(compilation: FidelityCompilation, subject_id: str) -> FidelityContractMember:
    return FidelityContractMember(
        subject_ref=S.ref(RefKind.SOURCE.value, subject_id),
        contract_ref=S.ref(RefKind.M01_CONTRACT.value, compilation.contract.contract_id),
        profile_ref=profile_ref_of(compilation),
        requested_class=compilation.contract.output_class.value,
        dimension_ids=compilation.contract.dimension_ids,
        evaluator_refs=[item.reference for item in compilation.contract.evaluator_set],
    )


def profile_ref_of(compilation: FidelityCompilation):
    return compilation.spec.profile_ref


class TestDomainSeparatedContractSets(unittest.TestCase):
    """§22: a multimodal brief compiles to several contracts, one per subject and authority."""

    def compile_pair(self):
        shot = compile_with()
        voice = compile_with(
            compilation_id="cmp.voice",
            profile=AUDIO,
            evaluator_registry=registry_for(AUDIO),
            subject_ref=S.ref(RefKind.SOURCE.value, "asset.voice.track"),
            projections=(projection("prj.voice", "CROSS_MODAL", S.TONE),),
            model_fingerprint_digest=S.digest("model.voice"),
            constraint_fingerprint_digest=S.digest("bundle.voice"),
            intent_summary="the narration must hold the approved reading",
        )
        return shot, voice

    def build_set(self, **over):
        from iris_intent.fidelity import FidelityContractSetRef

        shot, voice = self.compile_pair()
        arguments = {
            "set_id": "set.launch",
            "brief_ref": S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
            "revision_ref": S.ref(RefKind.REVISION.value, "rev.7"),
            "members": [
                member_for(shot, "asset.hero.frame"),
                member_for(voice, "asset.voice.track"),
            ],
        }
        arguments.update(over)
        return FidelityContractSetRef(**arguments)

    def test_a_multimodal_brief_emits_two_real_contracts(self) -> None:
        shot, voice = self.compile_pair()
        self.assertIsInstance(shot.contract, FidelityContract)
        self.assertIsInstance(voice.contract, FidelityContract)
        self.assertNotEqual(shot.contract.contract_id, voice.contract.contract_id)
        self.assertEqual(voice.contract.dimension_ids, AUDIO_DIMENSIONS)

    def test_two_profiles_may_ask_the_same_question_about_two_subjects(self) -> None:
        target = self.build_set()
        self.assertEqual(len(target.members), 2)
        self.assertIn("intent-adherence", target.dimension_ids)
        self.assertEqual(len(target.profile_refs), 2)
        self.assertEqual(len(target.contract_refs), 2)

    def test_one_profile_answering_one_axis_twice_is_refused(self) -> None:
        from iris_intent.fidelity import FidelityContractMember

        shot, _ = self.compile_pair()
        duplicate = FidelityContractMember(
            subject_ref=S.ref(RefKind.SOURCE.value, "asset.second.frame"),
            contract_ref=S.ref(RefKind.M01_CONTRACT.value, "contract-second"),
            profile_ref=profile_ref_of(shot),
            requested_class=shot.contract.output_class.value,
            dimension_ids=("identity-fidelity",),
        )
        with self.assertRaises(SchemaValidationError) as caught:
            self.build_set(members=list(self.build_set().members) + [duplicate])
        self.assertIn("judged twice", str(caught.exception))

    def test_the_set_digest_is_stable_under_member_order(self) -> None:
        forward = self.build_set()
        backward = self.build_set(members=list(reversed(self.build_set().members)))
        self.assertEqual(forward.set_digest(), backward.set_digest())

    def test_an_empty_set_is_refused(self) -> None:
        from iris_intent.fidelity import FidelityContractSetRef

        with self.assertRaises(SchemaValidationError) as caught:
            FidelityContractSetRef(
                set_id="set.empty",
                brief_ref=S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
                revision_ref=S.ref(RefKind.REVISION.value, "rev.7"),
            )
        self.assertIn("no members", str(caught.exception))

    def test_two_members_may_not_point_at_one_subject(self) -> None:
        first, second = self.build_set().members
        with self.assertRaises(SchemaValidationError) as caught:
            self.build_set(members=[first, replace(second, subject_ref=first.subject_ref)])
        self.assertIn("repeats a subject", str(caught.exception))

    def test_a_member_judging_nothing_is_refused(self) -> None:
        first = self.build_set().members[0]
        with self.assertRaises(SchemaValidationError) as caught:
            self.build_set(members=[replace(first, dimension_ids=()), *self.build_set().members[1:]])
        self.assertIn("judges no dimension", str(caught.exception))

    def test_the_set_names_the_subject_it_holds_a_contract_for(self) -> None:
        target = self.build_set()
        held = target.member_for(S.ref(RefKind.SOURCE.value, "asset.voice.track"))
        self.assertEqual(held.profile_ref.ref_id, AUDIO_PROFILE_ID)
        with self.assertRaises(SchemaValidationError) as caught:
            target.member_for(S.ref(RefKind.SOURCE.value, "asset.nobody.asked"))
        self.assertIn("asset.nobody.asked", str(caught.exception))


class TestRecompilationDeltas(unittest.TestCase):
    """§20, §21: M03 classifies what moved, and M02 decides what to rebuild."""

    def test_a_reworded_summary_changes_no_obligation(self) -> None:
        first = compile_with()
        second = compile_with(previous=first, intent_summary="the mark must be the approved one")
        self.assertIs(second.delta.class_enum, QualityChangeClass.NO_SEMANTIC_CHANGE)
        self.assertFalse(second.delta.invalidates_contract)

    def test_a_delivery_change_is_reported_as_a_delivery_change(self) -> None:
        first = compile_with()
        second = compile_with(previous=first, delivery_profile="festival-4k-cinema")
        self.assertIs(second.delta.class_enum, QualityChangeClass.DELIVERY_PROFILE_CHANGE)
        self.assertIn("delivery_profile", second.delta.changed_inputs)

    def test_a_moved_rung_is_reported_as_the_rung_change(self) -> None:
        first = compile_with()
        second = compile_with(
            previous=first, class_request=class_request(requested_class="MASTER")
        )
        self.assertIs(second.delta.class_enum, QualityChangeClass.QUALITY_CLASS_CHANGE)
        self.assertIn("requested_class", second.delta.changed_inputs)

    def test_a_profile_change_outranks_an_obligation_change(self) -> None:
        first = compile_with()
        second = compile_with(
            previous=first,
            profile=AUDIO,
            evaluator_registry=registry_for(AUDIO),
            projections=(projection("prj.voice", "CROSS_MODAL", S.TONE),),
        )
        self.assertIs(second.delta.class_enum, QualityChangeClass.PROFILE_CHANGE)

    def test_a_fingerprint_reports_which_input_moved(self) -> None:
        first = compile_with()
        second = compile_with(previous=first, model_fingerprint_digest=S.digest("model.moved"))
        self.assertEqual(
            second.fingerprint.changed_inputs_from(first.fingerprint), ("model_fingerprint",)
        )
        self.assertTrue(first.fingerprint.is_stale_for(second.spec))

    def test_an_unchanged_compilation_is_not_stale_for_itself(self) -> None:
        first = compile_with()
        self.assertFalse(first.fingerprint.is_stale_for(first.spec))


class TestObligationVocabulary(unittest.TestCase):
    """§6: M03 asks in its own words, and may only ever name axes M01 can answer about."""

    def test_every_obligation_maps_onto_admitted_or_declared_extension_ids(self) -> None:
        from iris_intent.fidelity import QualityObligationKind
        from iris_quality.dimensions import CANONICAL_FIDELITY_VECTOR

        declared_extensions = {"voice-identity", "text-legibility"}
        for kind in QualityObligationKind:
            with self.subTest(obligation=kind.value):
                candidates = dimensions_for(kind)
                self.assertTrue(candidates)
                for item in candidates:
                    self.assertIn(item, set(CANONICAL_FIDELITY_VECTOR) | declared_extensions)

    def test_an_extension_first_obligation_offers_a_canonical_fallback(self) -> None:
        self.assertEqual(
            dimensions_for("TEXT_LEGIBILITY"), ("text-legibility", "silhouette-readability")
        )

    def test_an_unspelled_obligation_is_refused_rather_than_guessed(self) -> None:
        with self.assertRaises(SchemaValidationError):
            dimensions_for("MAYBE_THE_BRAND")

    def test_a_projection_cannot_be_an_invention_of_the_compiler(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            projection("prj.ghost", statement_ids=(), constraint_ids=())
        self.assertIn("nobody can trace", str(caught.exception))

    def test_the_delta_compares_two_specs_without_a_compilation_wrapper(self) -> None:
        first = compile_with()
        second = compile_with(delivery_profile="festival-4k-cinema")
        moved = quality_contract_delta(first.spec, second.spec)
        self.assertIs(moved.class_enum, QualityChangeClass.DELIVERY_PROFILE_CHANGE)
        self.assertTrue(moved.invalidates_contract)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
