"""The execution-intent law: meaning is provider-independent, and what cannot be served is recorded.

S04 states what behaviour a brief demands and stops there. This file proves the three structural
promises that make that statement safe to compile against. The first is that the canonical bundle
ordering and fingerprint do not move when the provider observations move, or when the same demands
arrive in another order: availability is an observation about the world, never an input to meaning.
The second is that an unmet requirement stays in the record as a gap that names its source instead
of being quietly relaxed to fit a weaker machine. The third is the boundary against the provider:
a mutation envelope keeps the protected anchors it was given, and a translation receipt is an
account of a bundle, never a change to one.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from typing import Any

from iris_intent.authority import AuthorityLevel
from iris_intent.errors import (
    AdmissionRefusedError,
    AuthorityError,
    CapabilityGapError,
    ExplanationError,
    RefError,
    SchemaValidationError,
    StaleSemanticError,
    UntrustedExtensionError,
)
from iris_intent.explanation import (
    compile_explanation_graph,
    explanation_cache_key,
    project_explanation,
    reachable_roots,
    require_cache_valid,
)
from iris_intent.execution import (
    CapabilityDemand,
    ExecutionIntentBundle,
    ExecutionIntentGap,
    ExecutionIntentSlice,
    ExecutionGapClass,
    IntentOperation,
    ProviderTranslationItem,
    ProviderTranslationReceipt,
    SemanticLossRule,
    SemanticMutationEnvelope,
    canonical_execution_digest,
    compile_execution_intent,
    execution_intent_delta,
    execution_slice_for,
    reject_provider_admission,
    require_complete_execution_intent,
)
from iris_intent.identity import RefKind, SemanticRef
from iris_intent.ports import ExtensionObservation, ExtensionRef
from iris_intent.sources import RawInputRef

from tests import m03_kernel_support as S

BRIEF_REF = S.ref(RefKind.BRIEF.value, S.BRIEF_ID)
REVISION_REF = S.revision_ref()
STATEMENT_REF = S.ref(RefKind.STATEMENT.value, "st.1")
POLICY_REF = S.policy_ref()
CONTRACT_SET_REF = S.ref(RefKind.CONTRACT_SET.value, "contracts.iris")
TYPE_IMAGE = S.ref(RefKind.SEMANTIC_TYPE.value, "type.still-image")
TYPE_MOTION = S.ref(RefKind.SEMANTIC_TYPE.value, "type.motion-sequence")
ANCHOR_IDENTITY = S.ref(RefKind.ANCHOR.value, "anchor.character-identity")
ANCHOR_LAYOUT = S.ref(RefKind.ANCHOR.value, "anchor.wordmark-layout")
FREEDOM_LIGHTING = S.ref(RefKind.FREEDOM_ZONE.value, "zone.lighting")
LOSS_ITEM = S.ref(RefKind.CONSTRAINT.value, "cn.logo")
IDENTITY_CAPABILITY = "identity-preserving-repair"
MOTION_CAPABILITY = "temporal-consistency-extension"


def demand(
    ident: str = "dem.identity-repair",
    *,
    capability: str = IDENTITY_CAPABILITY,
    mandatory: bool = True,
    path: str | None = None,
    anchors: tuple[Any, ...] = (ANCHOR_IDENTITY,),
    **over: Any,
) -> CapabilityDemand:
    """One required capability, stated as what the work must be able to do."""

    payload: dict[str, Any] = {
        "demand_id": ident,
        "capability_id": capability,
        "label": "repair the frame without changing who appears in it",
        "mandatory": mandatory,
        "semantic_scope": (path or S.LOGO,),
        "output_type_refs": (TYPE_IMAGE,),
        "protected_anchor_refs": anchors,
        "source_refs": (STATEMENT_REF,),
    }
    payload.update(over)
    return CapabilityDemand(**payload)


def envelope(
    ident: str = "env.repair",
    *,
    operation_id: str = "op.repair",
    protected: tuple[str, ...] = ("character.identity",),
    mutable: tuple[str, ...] = ("hand.geometry",),
    anchors: tuple[Any, ...] = (ANCHOR_IDENTITY,),
    **over: Any,
) -> SemanticMutationEnvelope:
    """What an edit may change, what it must not, and which anchors hold it honest."""

    payload: dict[str, Any] = {
        "envelope_id": ident,
        "operation_id": operation_id,
        "protected_properties": protected,
        "mutable_properties": mutable,
        "allowed_mutation_classes": ("ANATOMY",),
        "forbidden_mutation_classes": ("IDENTITY", "BRAND"),
        "reference_anchors": anchors,
        "source_refs": (STATEMENT_REF,),
    }
    payload.update(over)
    return SemanticMutationEnvelope(**payload)


def operation(
    ident: str = "op.repair",
    *,
    family: str = "REPAIR",
    demands: tuple[str, ...] = ("dem.identity-repair",),
    mutation_envelope: str | None = "env.repair",
    anchors: tuple[Any, ...] = (ANCHOR_IDENTITY,),
    **over: Any,
) -> IntentOperation:
    """One provider-neutral desired transformation with its explanation path attached."""

    payload: dict[str, Any] = {
        "intent_operation_id": ident,
        "family": family,
        "purpose": "restore the damaged hands of the launch frame",
        "subject_refs": (S.ref(RefKind.M02_BUILD.value, "build.hero"),),
        "output_type_refs": (TYPE_IMAGE,),
        "protected_anchor_refs": anchors,
        "fidelity_contract_refs": (CONTRACT_SET_REF,),
        "capability_demand_ids": demands,
        "mutation_envelope_ref": mutation_envelope,
        "originating_refs": (STATEMENT_REF,),
        "required_explanation_refs": (STATEMENT_REF,),
        "source_refs": (STATEMENT_REF,),
    }
    if family == "CREATE":
        payload["subject_refs"] = ()
    payload.update(over)
    return IntentOperation(**payload)


def loss_rule(
    ident: str = "lr.identity",
    *,
    item_ref: Any = None,
    loss_class: str = "LOSSLESS_REQUIRED",
    operations: tuple[str, ...] = ("op.repair",),
    **over: Any,
) -> SemanticLossRule:
    """One obligation's disposition under provider translation."""

    payload: dict[str, Any] = {
        "rule_id": ident,
        "item_ref": LOSS_ITEM if item_ref is None else item_ref,
        "loss_class": loss_class,
        "operation_ids": operations,
        "source_refs": (STATEMENT_REF,),
    }
    payload.update(over)
    return SemanticLossRule(**payload)


def compiled(**over: Any) -> ExecutionIntentBundle:
    """A complete intent by default, so each test only states what it perturbs."""

    payload: dict[str, Any] = {
        "bundle_id": "eib.launch",
        "brief_ref": BRIEF_REF,
        "revision_ref": REVISION_REF,
        "intent_fingerprint_digest": S.digest("intent.model"),
        "constraint_fingerprint_digest": S.digest("constraint.bundle"),
        "fidelity_fingerprint_digest": S.digest("fidelity.contract"),
        "operations": (operation(),),
        "capability_demands": (demand(),),
        "mutation_envelopes": (envelope(),),
        "contract_set_ref": CONTRACT_SET_REF,
        "known_capabilities": (IDENTITY_CAPABILITY,),
    }
    payload.update(over)
    return compile_execution_intent(**payload)


def receipt(
    bundle: ExecutionIntentBundle,
    *,
    items: tuple[Any, ...] = (),
    provider: str = "provider.studio-a",
    compiler: str = "compiler.studio-a",
    **over: Any,
) -> ProviderTranslationReceipt:
    """A provider compiler's account of what it represented about ``bundle``."""

    payload: dict[str, Any] = {
        "receipt_id": f"ptr.{provider}",
        "bundle_ref": S.ref(RefKind.EXECUTION_BUNDLE.value, bundle.bundle_id),
        "bundle_fingerprint_digest": canonical_execution_digest(bundle),
        "compiler_ref": S.ref(RefKind.POLICY.value, compiler),
        "provider_ref": S.ref(RefKind.CAPABILITY.value, provider),
        "items": tuple(items),
    }
    payload.update(over)
    return ProviderTranslationReceipt(**payload)


def answered(
    bundle: ExecutionIntentBundle,
    item_ref: Any,
    disposition: str,
    *,
    provider: str = "provider.studio-a",
    compiler: str = "compiler.studio-a",
    **over: Any,
) -> ProviderTranslationReceipt:
    """A one-line answer to one obligation, which is most of what §10 has to read."""

    fields: dict[str, Any] = {}
    if disposition == "REPRESENTED_WITH_TOLERANCE":
        fields["tolerance_ref"] = S.ref(RefKind.POLICY.value, "policy.drift-bound")
    if disposition == "DELEGATED_TO_VALIDATOR":
        fields["delegate_ref"] = S.ref(RefKind.M01_EVALUATOR.value, "evaluator.human-review")
    fields.update(over)
    return receipt(
        bundle,
        provider=provider,
        compiler=compiler,
        items=(ProviderTranslationItem(item_ref=item_ref, disposition=disposition, **fields),),
    )


class AvailabilityNeverMovesMeaning(unittest.TestCase):
    """§20: what a machine can serve decides the status, never the semantic digest."""

    def test_a_registry_that_cannot_serve_the_demand_leaves_the_semantic_digest_intact(
        self,
    ) -> None:
        served = compiled(known_capabilities=(IDENTITY_CAPABILITY,))
        unserved = compiled(known_capabilities=())
        self.assertEqual(
            served.fingerprint.semantic_digest, unserved.fingerprint.semantic_digest
        )
        self.assertNotEqual(
            canonical_execution_digest(served), canonical_execution_digest(unserved)
        )
        self.assertEqual(served.status, "COMPLETE")
        self.assertEqual(unserved.status, "INCOMPLETE")

    def test_the_fingerprint_declares_provider_model_and_host_excluded_by_name(self) -> None:
        item = compiled()
        recorded = str(item.fingerprint.to_payload())
        self.assertTrue(item.fingerprint.provider_independent)
        for name in ("provider", "model", "host", "queue", "cost", "capability_availability"):
            self.assertIn(name, item.fingerprint.excluded_inputs)
        self.assertNotIn("provider.studio-a", recorded)
        self.assertNotIn("compiler.studio-a", recorded)

    def test_two_providers_answering_exactly_compile_to_the_same_artifact(self) -> None:
        base = compiled(loss_rules=(loss_rule(),))
        from_studio = compiled(
            loss_rules=(loss_rule(),),
            translation_receipts=(
                answered(
                    base, loss_rule().item_ref, "REPRESENTED_EXACTLY", provider="provider.studio-a"
                ),
            ),
        )
        from_farm = compiled(
            loss_rules=(loss_rule(),),
            translation_receipts=(
                answered(
                    base,
                    loss_rule().item_ref,
                    "REPRESENTED_EXACTLY",
                    provider="provider.render-farm-b",
                    compiler="compiler.worker-host-7",
                ),
            ),
        )
        self.assertEqual(
            from_studio.fingerprint.semantic_digest,
            from_farm.fingerprint.semantic_digest,
        )
        self.assertEqual(
            canonical_execution_digest(from_studio),
            canonical_execution_digest(from_farm),
        )
        self.assertEqual(from_studio.gaps, ())

    def test_availability_advertised_in_provider_vocabulary_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(known_capabilities=("sdxl-checkpoint-fix",))
        self.assertIn("sdxl", str(caught.exception))


class LosslessTranslationBlocksAdmission(unittest.TestCase):
    """§10: a provider that cannot represent a LOSSLESS_REQUIRED obligation is refused."""

    def bundle(self) -> ExecutionIntentBundle:
        return compiled(loss_rules=(loss_rule(),))

    def test_an_unsupported_answer_to_a_lossless_obmission_refuses_the_provider_plan(
        self,
    ) -> None:
        item = self.bundle()
        plan = answered(item, item.loss_rules[0].item_ref, "UNSUPPORTED")
        with self.assertRaises(AdmissionRefusedError) as caught:
            reject_provider_admission(plan, item, action="admit the provider plan")
        self.assertIn(item.lossless_items[0], str(caught.exception))
        self.assertIn("UNSUPPORTED", str(caught.exception))

    def test_silence_about_a_lossless_obligation_is_not_a_disposition(self) -> None:
        item = self.bundle()
        plan = receipt(item)
        with self.assertRaises(AdmissionRefusedError) as caught:
            reject_provider_admission(plan, item, action="admit the provider plan")
        self.assertIn("never answered", str(caught.exception))

    def test_a_tolerance_backed_approximation_still_refuses_a_lossless_obligation(self) -> None:
        item = self.bundle()
        plan = answered(item, item.loss_rules[0].item_ref, "REPRESENTED_WITH_TOLERANCE")
        with self.assertRaises(AdmissionRefusedError) as caught:
            reject_provider_admission(plan, item)
        self.assertIn("REPRESENTED_WITH_TOLERANCE", str(caught.exception))

    def test_an_exact_representation_admits_the_plan(self) -> None:
        item = self.bundle()
        plan = answered(item, item.loss_rules[0].item_ref, "REPRESENTED_EXACTLY")
        self.assertIs(reject_provider_admission(plan, item), plan)

    def test_a_delegation_to_a_validator_admits_because_somebody_still_checks_it(self) -> None:
        item = self.bundle()
        plan = answered(item, item.loss_rules[0].item_ref, "DELEGATED_TO_VALIDATOR")
        self.assertIsNotNone(plan.items[0].delegate_ref)
        self.assertIs(reject_provider_admission(plan, item), plan)

    def test_an_unsupported_advisory_obligation_does_not_block_admission(self) -> None:
        item = compiled(
            loss_rules=(loss_rule("lr.advisory", loss_class="ADVISORY"), loss_rule()),
        )
        plan = receipt(
            item,
            items=(
                ProviderTranslationItem(
                    item_ref=S.ref(RefKind.CONSTRAINT.value, "cn.tone"), disposition="UNSUPPORTED"
                ),
                ProviderTranslationItem(
                    item_ref=item.loss_rules[1].item_ref, disposition="REPRESENTED_EXACTLY"
                ),
            ),
        )
        self.assertEqual(item.lossless_items, (item.loss_rules[1].item_ref.text,))
        self.assertIs(reject_provider_admission(plan, item), plan)

    def test_a_translation_of_a_superseded_intent_is_not_a_translation_of_this_one(self) -> None:
        item = self.bundle()
        stale = answered(item, item.loss_rules[0].item_ref, "REPRESENTED_EXACTLY")
        moved = compiled(
            loss_rules=(loss_rule(),),
            capability_demands=(demand("dem.identity-repair", mandatory=False),),
        )
        self.assertNotEqual(stale.bundle_fingerprint_digest, canonical_execution_digest(moved))
        with self.assertRaises(AdmissionRefusedError) as caught:
            reject_provider_admission(stale, moved, action="admit the provider plan")
        self.assertIn("superseded", str(caught.exception))

    def test_a_lost_translation_is_recorded_as_an_observational_gap_not_a_relaxation(self) -> None:
        base = self.bundle()
        item = compiled(
            loss_rules=(loss_rule(),),
            translation_receipts=(answered(base, base.loss_rules[0].item_ref, "UNSUPPORTED"),),
        )
        losses = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.PROVIDER_TRANSLATION_LOSS.value
        ]
        self.assertEqual(len(losses), 1)
        self.assertFalse(losses[0].blocks_completion)
        self.assertTrue(losses[0].class_enum.observational)
        self.assertEqual(item.status, "COMPLETE")
        self.assertEqual(item.loss_rules, base.loss_rules)


class MutationEnvelopeHoldsItsAnchors(unittest.TestCase):
    """§12: an edit names what must survive it, and no downstream reader guesses."""

    def test_dropping_an_anchor_the_envelope_still_relies_on_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(operations=(operation(anchors=()),))
        self.assertIn(ANCHOR_IDENTITY.text, str(caught.exception))
        self.assertIn("does not itself protect", str(caught.exception))

    def test_overwriting_the_envelope_anchor_with_one_the_operation_never_named_is_refused(
        self,
    ) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(mutation_envelopes=(envelope(anchors=(ANCHOR_LAYOUT,)),))
        self.assertIn(ANCHOR_LAYOUT.text, str(caught.exception))

    def test_an_envelope_that_protects_nothing_is_a_licence_and_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(mutation_envelopes=(envelope(protected=()),))
        self.assertIn("protects nothing", str(caught.exception))

    def test_an_envelope_that_allows_nothing_mutable_cannot_accomplish_its_mutation(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(mutation_envelopes=(envelope(mutable=()),))
        self.assertIn("permits no change", str(caught.exception))

    def test_a_property_declared_both_protected_and_mutable_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(
                mutation_envelopes=(
                    envelope(protected=("character.identity",), mutable=("character.identity",)),
                )
            )
        self.assertIn("both protected and mutable", str(caught.exception))

    def test_a_drift_bound_without_a_policy_behind_it_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(mutation_envelopes=(envelope(maximum_drift=0.2),))
        self.assertIn("drift bound with no policy", str(caught.exception))

    def test_the_slice_carries_the_envelope_and_its_anchors_unchanged(self) -> None:
        item = compiled()
        view = execution_slice_for(item, "op.repair")
        self.assertEqual(view.mutation_envelope, item.mutation_envelopes[0])
        self.assertEqual(view.mutation_envelope.protected_properties, ("character.identity",))
        self.assertIn(
            ANCHOR_IDENTITY.text,
            [anchor.text for anchor in view.mutation_envelope.reference_anchors],
        )
        self.assertEqual(view.operation.protected_anchor_refs, (ANCHOR_IDENTITY,))

    def test_an_edit_of_an_admitted_subject_with_no_anchor_at_all_records_a_gap(self) -> None:
        item = compiled(
            operations=(operation(anchors=()),),
            mutation_envelopes=(envelope(anchors=()),),
        )
        gaps = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.INSUFFICIENT_REFERENCE_SUPPORT.value
        ]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].operation_id, "op.repair")
        self.assertEqual(item.status, "INCOMPLETE")


class CanonicalOrdering(unittest.TestCase):
    """§25 proof item 1: the same demands arrive in any order and compile to one artifact."""

    def hero(self, demands: tuple[str, ...] = ("dem.image",)) -> IntentOperation:
        return operation(
            "op.hero",
            family="CREATE",
            mutation_envelope=None,
            anchors=(),
            demands=demands,
            subject_refs=(),
        )

    def check(self) -> IntentOperation:
        return operation(
            "op.check",
            family="VALIDATE",
            mutation_envelope=None,
            anchors=(),
            demands=(),
            output_type_refs=(),
        )

    def test_permuting_the_operations_leaves_the_canonical_digest_unchanged(self) -> None:
        forward = compiled(
            operations=(self.hero(), self.check()),
            capability_demands=(demand("dem.image"),),
            mutation_envelopes=(),
            known_capabilities=(IDENTITY_CAPABILITY,),
        )
        backward = compiled(
            operations=(self.check(), self.hero()),
            capability_demands=(demand("dem.image"),),
            mutation_envelopes=(),
            known_capabilities=(IDENTITY_CAPABILITY,),
        )
        self.assertEqual(forward.operation_ids, ("op.check", "op.hero"))
        self.assertEqual(canonical_execution_digest(forward), canonical_execution_digest(backward))
        self.assertEqual(
            forward.fingerprint.semantic_digest, backward.fingerprint.semantic_digest
        )

    def test_permuting_the_availability_observations_leaves_the_semantic_digest_unchanged(
        self,
    ) -> None:
        served = compiled(
            operations=(self.hero(("dem.image", "dem.motion")), self.check()),
            capability_demands=(
                demand("dem.image"),
                demand("dem.motion", capability=MOTION_CAPABILITY, path=S.TONE),
            ),
            mutation_envelopes=(),
            known_capabilities=(IDENTITY_CAPABILITY, MOTION_CAPABILITY),
        )
        reordered = compiled(
            operations=(self.hero(("dem.image", "dem.motion")), self.check()),
            capability_demands=(
                demand("dem.image"),
                demand("dem.motion", capability=MOTION_CAPABILITY, path=S.TONE),
            ),
            mutation_envelopes=(),
            known_capabilities=(MOTION_CAPABILITY, IDENTITY_CAPABILITY),
        )
        self.assertEqual(served.gaps, ())
        self.assertEqual(served.status, "COMPLETE")
        self.assertEqual(
            canonical_execution_digest(served), canonical_execution_digest(reordered)
        )


class AvailabilityIsAnObservation(unittest.TestCase):
    """§8: what nobody can serve is recorded with its source, never relaxed away."""

    def test_a_mandatory_capability_no_provider_can_serve_becomes_a_recorded_gap(self) -> None:
        item = compiled(known_capabilities=())
        missing = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.MISSING_CAPABILITY.value
        ]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].capability_id, IDENTITY_CAPABILITY)
        self.assertTrue(missing[0].blocks_completion)
        self.assertIn(STATEMENT_REF.text, [ref.text for ref in missing[0].source_refs])
        self.assertEqual(item.status, "INCOMPLETE")
        self.assertEqual([d.capability_id for d in item.capability_demands], [IDENTITY_CAPABILITY])

    def test_an_unmet_mandatory_demand_refuses_downstream_consumption_by_name(self) -> None:
        item = compiled(known_capabilities=())
        with self.assertRaises(CapabilityGapError) as caught:
            require_complete_execution_intent(item, action="hand the plan to M02")
        self.assertIn(IDENTITY_CAPABILITY, str(caught.exception))
        self.assertIn("INCOMPLETE", str(caught.exception))


class ProviderVocabularyCannotBecomeMeaning(unittest.TestCase):
    """§7: an implementation name is not a statement about the work, in any field."""

    def test_a_capability_named_after_a_runtime_control_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            demand("dem.depth", capability="controlnet-depth-hold")
        self.assertIn("controlnet", str(caught.exception))

    def test_an_operation_id_naming_a_vendor_is_refused_when_the_bundle_closes(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(
                operations=(operation("op.midjourney-pass"),),
                mutation_envelopes=(envelope(operation_id="op.midjourney-pass"),),
            )
        self.assertIn("midjourney", str(caught.exception))
        self.assertIn("§7", str(caught.exception))

    def test_a_purpose_written_in_prompt_weight_syntax_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            operation("op.repair", purpose="restore the hands ::1.2 --ar 16:9")
        self.assertIn("--ar", str(caught.exception))

    def test_an_envelope_note_naming_a_model_checkpoint_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            envelope("env.repair", notes="hold it through the model checkpoint")
        self.assertIn("model checkpoint", str(caught.exception))

    def test_a_host_shape_in_a_capability_label_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            demand("dem.image", label="render it on worker-host-12")
        self.assertIn("worker-host-", str(caught.exception))

    def test_a_gap_that_speaks_about_providers_is_m03_prose_and_survives(self) -> None:
        item = compiled(known_capabilities=())
        self.assertIn("provider", item.gaps[0].detail.lower())
        self.assertIsInstance(item, ExecutionIntentBundle)


class ProviderTextCannotCreateCanonicalIntent(unittest.TestCase):
    """§14, D-M03-S04-011: what a model or a provider wrote never outranks who asked."""

    def test_a_provider_result_cannot_claim_human_owner_authority(self) -> None:
        with self.assertRaises(AuthorityError) as caught:
            S.raw_source(source_id="src.provider-answer", kind="PROVIDER_RESULT")
        self.assertIn("PROVIDER_RESULT", str(caught.exception))
        self.assertIn("ceiling", str(caught.exception))

    def test_a_retrieved_page_cannot_carry_governed_policy_authority(self) -> None:
        with self.assertRaises(AuthorityError) as caught:
            RawInputRef(
                source_id="src.retrieved",
                kind="RETRIEVED_CONTEXT",
                authority=AuthorityLevel.GOVERNED_POLICY.value,
                content_digest=S.digest("src.retrieved"),
            )
        self.assertIn("RETRIEVED_CONTEXT", str(caught.exception))
        self.assertIn("GOVERNED_POLICY", str(caught.exception))

    def test_an_inferred_reading_cannot_be_recorded_as_an_explicit_human_claim(self) -> None:
        with self.assertRaises(AuthorityError) as caught:
            S.statement(
                "st.guess",
                S.LOGO,
                origin="INFERRED",
                authority=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
            )
        self.assertIn("INFERRED", str(caught.exception))
        self.assertIn(AuthorityLevel.MODEL_INFERRED.value, str(caught.exception))

    def test_a_provider_authored_source_holds_a_statement_only_to_its_ceiling(self) -> None:
        origin = RawInputRef(
            source_id="src.provider-answer",
            kind="PROVIDER_RESULT",
            authority=AuthorityLevel.PROVIDER_OBSERVED.value,
            content_digest=S.digest("src.provider-answer"),
        )
        self.assertTrue(origin.untrusted)
        self.assertEqual(origin.authority_level, AuthorityLevel.PROVIDER_OBSERVED)
        with self.assertRaises(AuthorityError) as promoted:
            S.statement(
                "st.promoted",
                S.LOGO,
                origin="DERIVED",
                authority=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
                source=origin,
            )
        self.assertIn("HUMAN_OWNER", str(promoted.exception))
        with self.assertRaises(AuthorityError) as self_admitted:
            S.statement(
                "st.self-admitted",
                S.LOGO,
                origin="EXPLICIT",
                authority=S.authority_ref(
                    AuthorityLevel.PROVIDER_OBSERVED.value, basis="PROJECT_RECORD"
                ),
                source=origin,
            )
        self.assertIn(AuthorityLevel.TEAM_ASSERTED.value, str(self_admitted.exception))

    def test_an_anchor_nobody_pinned_cannot_be_declared_protected(self) -> None:
        loose = SemanticRef(kind=RefKind.ANCHOR.value, ref_id="anchor.loose")
        with self.assertRaises(RefError) as caught:
            operation("op.repair", protected_anchor_refs=(loose,))
        self.assertIn("content digest", str(caught.exception))

    def test_a_verb_nobody_asked_for_cannot_be_written_into_canonical_intent(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            operation("op.unasked", originating_refs=())
        self.assertIn("no admitted statement", str(caught.exception))

    def test_a_capability_demand_without_a_source_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            demand("dem.orphan", source_refs=())
        self.assertIn("cites no source", str(caught.exception))


class ProviderResultsCannotEditTheBrief(unittest.TestCase):
    """§23: a provider answers about a bundle; it does not write one."""

    def observation(self, **over: Any) -> ExtensionObservation:
        payload: dict[str, Any] = {
            "observation_id": "obs.type.iso",
            "boundary": "SEMANTIC_TYPE",
            "provider_id": "m04.ir",
            "about": ExtensionRef(
                boundary="SEMANTIC_TYPE",
                reference=S.ref(RefKind.SEMANTIC_TYPE.value, "type.iso.scene"),
                provider_id="m04.ir",
            ),
            "revision_ref": S.revision_ref("rev.3"),
            "facts": {"carrier": "m04-scene-ir"},
        }
        payload.update(over)
        return ExtensionObservation(**payload)

    def test_a_translation_receipt_has_no_field_that_could_change_canonical_state(self) -> None:
        item = compiled()
        plan = answered(item, LOSS_ITEM, "UNSUPPORTED")
        fields = set(plan.to_payload())
        for name in ("operations", "capability_demands", "gaps", "status", "loss_rules"):
            self.assertNotIn(name, fields)
        self.assertFalse(plan.mutates_bundle)
        self.assertFalse(plan.canonical_semantics)

    def test_a_receipt_is_as_frozen_as_the_bundle_it_answers_about(self) -> None:
        plan = answered(compiled(), LOSS_ITEM, "UNSUPPORTED")
        with self.assertRaises(FrozenInstanceError):
            plan.notes = "the provider decided to restate the obligation"
        self.assertIsNone(plan.notes)

    def test_a_failing_translation_leaves_the_demands_byte_for_byte_intact(self) -> None:
        base = compiled(loss_rules=(loss_rule(),))
        after = compiled(
            loss_rules=(loss_rule(),),
            translation_receipts=(answered(base, base.loss_rules[0].item_ref, "UNSUPPORTED"),),
        )
        self.assertEqual(
            [item.to_payload() for item in after.capability_demands],
            [item.to_payload() for item in base.capability_demands],
        )
        self.assertEqual(after.operations, base.operations)
        self.assertEqual(after.loss_rules, base.loss_rules)

    def test_a_bundle_keeps_no_slot_for_a_provider_answer(self) -> None:
        payload = compiled().to_payload()
        for name in ("translation_receipts", "receipts", "provider", "model", "host"):
            self.assertNotIn(name, payload)
        self.assertTrue(ExecutionIntentBundle.canonical_semantics)

    def test_an_execution_intent_carries_no_authority_to_dispatch_or_publish(self) -> None:
        item = compiled()
        self.assertFalse(item.is_m02_execution_plan)
        self.assertFalse(item.may_dispatch)
        self.assertFalse(item.authorizes_side_effects)
        self.assertFalse(IntentOperation.authorizes_side_effects)

    def test_an_observation_that_reports_a_constraint_is_an_attempted_edit(self) -> None:
        with self.assertRaises(UntrustedExtensionError) as caught:
            self.observation(facts={"constraints": "shows_logo at all times"})
        self.assertIn("constraints", str(caught.exception))
        self.assertIn("semantic mutation", str(caught.exception))

    def test_an_observation_that_reports_a_fact_is_admitted_as_an_observation(self) -> None:
        seen = self.observation(gaps=("the carrier has no motion channel",))
        self.assertEqual(seen.facts, {"carrier": "m04-scene-ir"})
        self.assertEqual(seen.gaps, ("the carrier has no motion channel",))


class ExplanationPathsReachAdmittedGround(unittest.TestCase):
    """§16, §17: every claim points back to who made it, and the graph writes nothing back."""

    def graph(self, item: ExecutionIntentBundle | None = None):
        return compile_explanation_graph(item or compiled())

    def node_for(self, graph: Any, kind: str, label: str):
        found = [
            node for node in graph.nodes if node.kind == kind and node.label == label
        ]
        self.assertEqual(len(found), 1, f"expected exactly one {kind} node for {label}")
        return found[0]

    def test_every_operation_explains_itself_back_to_an_admitted_statement(self) -> None:
        graph = self.graph()
        op = self.node_for(graph, "INTENT_OPERATION", "op.repair")
        roots = reachable_roots(graph, op.node_id)
        self.assertTrue(roots)
        self.assertIn(STATEMENT_REF.text, [node.subject_ref.text for node in roots])
        self.assertTrue(all(node.is_ground for node in roots))

    def test_the_graph_is_cited_by_digest_and_holds_no_writable_reference(self) -> None:
        item = compiled()
        graph = self.graph(item)
        self.assertEqual(graph.semantic_digest, item.fingerprint.semantic_digest)
        self.assertEqual(graph.bundle_digest, canonical_execution_digest(item))
        self.assertEqual(graph.bundle_ref.content_digest, canonical_execution_digest(item))
        self.assertFalse(graph.mutates_bundle)
        self.assertFalse(graph.is_execution_plan)

    def test_an_unrepresented_requirement_appears_as_its_own_explanation_node(self) -> None:
        item = compiled(known_capabilities=())
        graph = self.graph(item)
        gap = self.node_for(graph, "EXECUTION_GAP", ExecutionGapClass.MISSING_CAPABILITY.value)
        self.assertIn(IDENTITY_CAPABILITY, gap.detail)
        self.assertIn(STATEMENT_REF.text, [node.text for node in gap.provenance_refs])
        roots = reachable_roots(graph, gap.node_id)
        self.assertIn(STATEMENT_REF.text, [node.subject_ref.text for node in roots])

    def test_a_receipt_about_another_bundle_is_refused_from_the_explanation(self) -> None:
        item = compiled()
        other = compiled(bundle_id="eib.other", loss_rules=(loss_rule(),))
        plan = answered(other, loss_rule().item_ref, "REPRESENTED_EXACTLY")
        with self.assertRaises(ExplanationError) as caught:
            compile_explanation_graph(item, receipts=(plan,))
        self.assertIn("superseded", str(caught.exception))

    def test_a_receipt_that_represents_nothing_explains_nothing(self) -> None:
        item = compiled()
        with self.assertRaises(ExplanationError) as caught:
            compile_explanation_graph(item, receipts=(receipt(item),))
        self.assertIn("no obligation", str(caught.exception))

    def test_compact_and_audit_renderings_agree_on_the_same_canonical_facts(self) -> None:
        graph = self.graph()
        compact = project_explanation(graph, "COMPACT")
        audit = project_explanation(graph, "AUDIT")
        self.assertEqual(dict(compact.canonical_facts), dict(audit.canonical_facts))
        self.assertEqual(compact.rendered_node_count, audit.rendered_node_count)
        self.assertTrue(all(entry.narrative is None for entry in compact.entries))
        self.assertTrue(any(entry.narrative for entry in audit.entries))
        self.assertTrue(any(entry.provenance for entry in audit.entries))
        self.assertIs(compact.verify_against(graph), compact)

    def test_a_trace_only_rendering_carries_no_labels_at_all(self) -> None:
        trace = project_explanation(self.graph(), "TRACE_ID_ONLY")
        self.assertTrue(all(entry.label is None for entry in trace.entries))
        self.assertTrue(all(entry.relations for entry in trace.entries) or trace.entries)

    def test_the_explanation_cache_survives_an_unchanged_intent(self) -> None:
        item = compiled()
        graph = self.graph(item)
        key = explanation_cache_key(item, graph, level="COMPACT")
        self.assertTrue(key.describes(bundle=item, graph=graph))
        self.assertIs(
            require_cache_valid(key, bundle=item, graph=graph, action="serve the answer"), key
        )

    def test_the_explanation_cache_goes_stale_when_a_requirement_is_added(self) -> None:
        item = compiled()
        key = explanation_cache_key(item, self.graph(item), level="COMPACT")
        moved = compiled(loss_rules=(loss_rule(),))
        with self.assertRaises(StaleSemanticError) as caught:
            require_cache_valid(
                key, bundle=moved, graph=self.graph(moved), action="serve the answer"
            )
        self.assertIn(key.key_id, str(caught.exception))

    def test_a_cache_key_over_a_mismatched_bundle_and_graph_is_refused(self) -> None:
        item = compiled()
        moved = compiled(loss_rules=(loss_rule(),))
        with self.assertRaises(ExplanationError) as caught:
            explanation_cache_key(moved, self.graph(item), level="COMPACT")
        self.assertIn("mismatched pair", str(caught.exception))

    def test_the_bundle_answers_why_this_verb_without_a_providers_help(self) -> None:
        account = compiled().explanation()
        self.assertEqual(
            account["operations"]["op.repair"]["because"], [STATEMENT_REF.text]
        )
        self.assertEqual(
            account["capabilities"]["dem.identity-repair"]["capability"], IDENTITY_CAPABILITY
        )
        self.assertIn("provider", account["why_nothing_lower"]["excluded_from_fingerprint"])
        self.assertEqual(account["unrepresented"], [])


class RevisionDeltasSayWhatMoved(unittest.TestCase):
    """§21: a restated reason costs nothing; a moved demand costs a recompilation."""

    def test_an_identical_recompile_reports_no_semantic_change(self) -> None:
        before = compiled()
        after = compiled(previous=before)
        self.assertEqual(after.delta.class_name, "NO_SEMANTIC_CHANGE")
        self.assertEqual(after.delta.changed_inputs, ())
        self.assertFalse(after.delta.requires_provider_recompilation)

    def test_relisting_only_the_reasoning_costs_no_provider_recompilation(self) -> None:
        before = compiled()
        after = compiled(
            previous=before,
            operations=(operation("op.repair", required_explanation_refs=(POLICY_REF,)),),
        )
        self.assertEqual(after.delta.class_name, "EXPLANATION_ONLY_CHANGE")
        self.assertEqual(after.delta.changed_inputs, ("explanations",))
        self.assertFalse(after.delta.requires_provider_recompilation)
        self.assertNotEqual(
            before.fingerprint.semantic_digest, after.fingerprint.semantic_digest
        )

    def test_a_demand_that_loosens_is_a_capability_change_not_a_rewording(self) -> None:
        before = compiled()
        after = compiled(previous=before, capability_demands=(demand(mandatory=False),))
        self.assertEqual(after.delta.class_name, "CAPABILITY_DEMAND_CHANGE")
        self.assertIn(IDENTITY_CAPABILITY, after.delta.affected_capability_ids)
        self.assertTrue(after.delta.requires_provider_recompilation)

    def test_a_new_operation_is_reported_as_a_moved_verb(self) -> None:
        before = compiled()
        hero = operation(
            "op.hero",
            family="CREATE",
            subject_refs=(),
            anchors=(),
            demands=("dem.hero",),
            mutation_envelope=None,
        )
        after = compiled(
            previous=before,
            operations=(operation(), hero),
            capability_demands=(demand(), demand("dem.hero")),
        )
        self.assertEqual(after.delta.class_name, "OPERATION_ADDED_REMOVED")
        self.assertEqual(after.delta.affected_operation_ids, ("op.hero",))
        self.assertTrue(after.delta.requires_provider_recompilation)

    def test_a_protected_anchor_swapped_out_is_reported_as_an_anchor_change(self) -> None:
        before = compiled(
            operations=(operation(anchors=(ANCHOR_IDENTITY,)),),
            mutation_envelopes=(envelope(anchors=()),),
        )
        after = compiled(
            previous=before,
            operations=(operation(anchors=(ANCHOR_LAYOUT,)),),
            mutation_envelopes=(envelope(anchors=()),),
        )
        delta = execution_intent_delta(before, after)
        self.assertEqual(delta.class_name, "PROTECTED_ANCHOR_CHANGE")
        self.assertIn("anchors", delta.changed_inputs)
        self.assertEqual(delta.affected_operation_ids, ("op.repair",))

    def test_a_registry_learning_a_capability_is_not_the_brief_changing_its_mind(self) -> None:
        before = compiled(known_capabilities=())
        after = compiled(previous=before, known_capabilities=(IDENTITY_CAPABILITY,))
        delta = execution_intent_delta(before, after)
        self.assertEqual(delta.class_name, "NO_SEMANTIC_CHANGE")
        self.assertNotEqual(before.status, after.status)


class SlicesStayMinimum(unittest.TestCase):
    """§14: a downstream compiler receives one operation's sufficiency, not the campaign."""

    def campaign(self) -> ExecutionIntentBundle:
        hero = operation(
            "op.hero",
            family="CREATE",
            subject_refs=(),
            anchors=(),
            demands=("dem.hero",),
            mutation_envelope=None,
            output_type_refs=(TYPE_MOTION,),
        )
        return compiled(
            operations=(operation(), hero),
            capability_demands=(demand(), demand("dem.hero", path=S.TONE)),
            loss_rules=(
                loss_rule(
                    "lr.hero",
                    item_ref=S.ref(RefKind.CONSTRAINT.value, "cn.tone"),
                    operations=("op.hero",),
                ),
                loss_rule(),
            ),
        )

    def test_a_slice_carries_only_the_demands_its_operation_named(self) -> None:
        item = self.campaign()
        view = execution_slice_for(item, "op.repair")
        self.assertEqual([d.demand_id for d in view.capability_demands], ["dem.identity-repair"])
        self.assertEqual([rule.rule_id for rule in view.loss_rules], ["lr.identity"])
        self.assertEqual(view.operation.family, "REPAIR")

    def test_a_slice_omitting_a_demand_its_own_operation_named_is_refused(self) -> None:
        item = compiled()
        with self.assertRaises(SchemaValidationError) as caught:
            ExecutionIntentSlice(
                slice_id="slice.thin",
                bundle_ref=S.ref(RefKind.EXECUTION_BUNDLE.value, item.bundle_id),
                bundle_digest=canonical_execution_digest(item),
                operation=item.operations[0],
                capability_demands=(),
                explanation_refs=(STATEMENT_REF,),
            )
        self.assertIn("omits demands", str(caught.exception))

    def test_a_slice_smuggling_in_a_surplus_demand_is_refused(self) -> None:
        item = compiled()
        with self.assertRaises(SchemaValidationError) as caught:
            ExecutionIntentSlice(
                slice_id="slice.fat",
                bundle_ref=S.ref(RefKind.EXECUTION_BUNDLE.value, item.bundle_id),
                bundle_digest=canonical_execution_digest(item),
                operation=item.operations[0],
                capability_demands=(demand(), demand("dem.extra", path=S.TONE)),
                explanation_refs=(STATEMENT_REF,),
            )
        self.assertIn("never named", str(caught.exception))

    def test_a_slice_carrying_another_operation_s_envelope_is_refused(self) -> None:
        item = self.campaign()
        with self.assertRaises(SchemaValidationError) as caught:
            ExecutionIntentSlice(
                slice_id="slice.borrowed",
                bundle_ref=S.ref(RefKind.EXECUTION_BUNDLE.value, item.bundle_id),
                bundle_digest=canonical_execution_digest(item),
                operation=item.operation("op.hero"),
                capability_demands=(demand("dem.hero", path=S.TONE),),
                mutation_envelope=envelope("env.repair", operation_id="op.repair"),
                explanation_refs=(STATEMENT_REF,),
            )
        self.assertIn("belonging to op.repair", str(caught.exception))

    def test_a_slice_is_addressed_to_the_exact_bundle_it_came_from(self) -> None:
        item = self.campaign()
        view = execution_slice_for(item, "op.repair")
        self.assertEqual(view.bundle_digest, canonical_execution_digest(item))
        self.assertEqual(view.bundle_ref.ref_id, item.bundle_id)
        self.assertEqual(view.gap_ids, ())
        blocked = compiled(known_capabilities=())
        self.assertEqual(
            execution_slice_for(blocked, "op.repair").gap_ids,
            tuple(gap.gap_id for gap in blocked.gaps),
        )


class GapVocabularyKeepsItsSource(unittest.TestCase):
    """§8, §13: each hole is named, sourced, and unrepairable by editing the ask down."""

    def test_an_anchor_no_capability_can_hold_is_recorded_against_that_anchor(self) -> None:
        item = compiled(known_capabilities=(), unservable_anchor_refs=(ANCHOR_IDENTITY,))
        gaps = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.PROTECTED_ANCHOR_UNSUPPORTED.value
        ]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].anchor_ref, ANCHOR_IDENTITY)
        self.assertEqual(gaps[0].capability_id, IDENTITY_CAPABILITY)
        self.assertTrue(gaps[0].blocks_completion)

    def test_a_gap_reporting_a_missing_capability_without_naming_it_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            ExecutionIntentGap(
                gap_id="gap.nameless",
                class_name=ExecutionGapClass.MISSING_CAPABILITY.value,
                detail="something the production needs is absent",
                source_refs=(STATEMENT_REF,),
            )
        self.assertIn("without naming it", str(caught.exception))

    def test_a_gap_that_cannot_name_its_requirement_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            ExecutionIntentGap(
                gap_id="gap.unsourced",
                class_name=ExecutionGapClass.NO_QUALITY_EVIDENCE_PATH.value,
                detail="nothing will judge this work",
                source_refs=(),
            )
        self.assertIn("names no source", str(caught.exception))

    def test_a_publish_desire_without_an_approval_boundary_stays_unresolved(self) -> None:
        item = compiled(
            operations=(operation("op.repair", side_effect_class="EXTERNAL_PUBLICATION"),),
        )
        gaps = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.SIDE_EFFECT_POLICY_UNRESOLVED.value
        ]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].operation_id, "op.repair")
        self.assertEqual(item.status, "INCOMPLETE")
        self.assertTrue(item.operations[0].needs_approval_boundary)
        self.assertFalse(item.authorizes_side_effects)

    def test_a_named_policy_and_approval_ref_closes_the_side_effect_gap(self) -> None:
        item = compiled(
            operations=(
                operation(
                    "op.repair",
                    side_effect_class="EXTERNAL_PUBLICATION",
                    approval_boundary_ref=S.ref(RefKind.DESTINATION.value, "destination.channel"),
                ),
            ),
            side_effect_policy_ref=S.policy_ref("policy.publish"),
        )
        self.assertEqual(
            [gap.class_name for gap in item.gaps], []
        )
        self.assertFalse(item.operations[0].needs_approval_boundary)
        self.assertEqual(item.status, "COMPLETE")

    def test_a_lossless_obligation_written_on_a_freedom_zone_is_unrepresentable(self) -> None:
        item = compiled(
            loss_rules=(
                loss_rule(
                    "lr.zone",
                    item_ref=FREEDOM_LIGHTING,
                    operations=("op.repair",),
                ),
            )
        )
        gaps = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.UNREPRESENTABLE_CONSTRAINT.value
        ]
        self.assertEqual(len(gaps), 1)
        self.assertIn("Freedom Zone", gaps[0].detail)
        self.assertTrue(item.loss_rules[0].blocks_provider_admission)
        self.assertEqual(item.loss_rules[0].item_ref, FREEDOM_LIGHTING)

    def test_a_semantic_type_nothing_can_carry_is_recorded_not_rewritten(self) -> None:
        item = compiled(
            operations=(operation("op.repair", output_type_refs=(TYPE_MOTION,)),),
            supported_semantic_types=("type.still-image",),
        )
        gaps = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.SEMANTIC_TYPE_UNSUPPORTED.value
        ]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].operation_id, "op.repair")
        self.assertEqual(item.operations[0].output_type_refs, (TYPE_MOTION,))

    def test_a_stale_capability_observation_refuses_the_observation_not_the_demand(self) -> None:
        item = compiled(
            known_capabilities=(IDENTITY_CAPABILITY,),
            stale_capabilities=(IDENTITY_CAPABILITY,),
        )
        stale = [
            gap
            for gap in item.gaps
            if gap.class_name == ExecutionGapClass.STALE_PROVIDER_CAPABILITY.value
        ]
        self.assertEqual(len(stale), 1)
        self.assertFalse(stale[0].blocks_completion)
        self.assertTrue(stale[0].class_enum.observational)
        self.assertEqual([d.capability_id for d in item.capability_demands], [IDENTITY_CAPABILITY])

    def test_a_status_that_overrules_its_own_blocking_gaps_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            compiled(known_capabilities=(), status="COMPLETE")
        self.assertIn("INCOMPLETE", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

