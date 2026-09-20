"""IRIS-WO-0003-CORRECTION-01 F4: the bounded, versioned Dimension Registry contract.

The freeze promises non-visual Fidelity Vector growth. That growth is data declared
through :class:`iris_quality.dimensions.DimensionRegistry`, so the state machine in
``decision.py`` never learns a domain name and an unknown id still fails closed.
"""

from __future__ import annotations

from unittest import TestCase

from iris_quality.contracts import FidelityContract, QualityClass
from iris_quality.decision import DecisionEngine
from iris_quality.dimensions import (
    CANONICAL_FIDELITY_VECTOR,
    DEFAULT_DIMENSION_REGISTRY,
    DIMENSION_REGISTRY_VERSION,
    MAX_EXTENSION_DIMENSIONS,
    DimensionRegistry,
    FidelityDimension,
    GateState,
)
from iris_quality.errors import RegistrationError, SchemaValidationError
from iris_quality.judging import SubjectRef
from iris_quality.registry import DomainProfileRegistry
from iris_quality.zones import SemanticZone
from tests.m01_kernel_support import (
    DIMENSIONS,
    SUBJECT,
    contract,
    covered_assessments,
    domain_profile,
    evaluator_descriptor,
    extension_registry,
    ladder_rules,
)

AUDIO_DIMENSIONS = ("intent-adherence", "voice-identity", "audio-clarity")


class DimensionRegistryTests(TestCase):
    def test_the_canonical_vector_is_always_admitted(self) -> None:
        registry = DEFAULT_DIMENSION_REGISTRY
        self.assertEqual(registry.version, DIMENSION_REGISTRY_VERSION)
        self.assertEqual(registry.extension_ids, ())
        self.assertEqual(registry.dimension_ids, CANONICAL_FIDELITY_VECTOR)
        self.assertEqual(len(CANONICAL_FIDELITY_VECTOR), 18)
        self.assertTrue(all(registry.admits(item) for item in CANONICAL_FIDELITY_VECTOR))
        self.assertFalse(registry.admits("aura-fidelity"))

    def test_an_extension_is_admitted_without_touching_the_canonical_order(self) -> None:
        registry = extension_registry("voice-identity", "audio-clarity")
        self.assertEqual(
            registry.dimension_ids,
            CANONICAL_FIDELITY_VECTOR + ("audio-clarity", "voice-identity"),
        )
        self.assertEqual(registry.extension_ids, ("voice-identity", "audio-clarity"))
        dimension = registry.resolve("voice-identity")
        self.assertFalse(dimension.core)
        self.assertEqual(registry.resolve("geometry-integrity").dimension_id, "geometry-integrity")

    def test_an_unadmitted_dimension_never_resolves(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            DEFAULT_DIMENSION_REGISTRY.resolve("voice-identity")
        self.assertIn("not an admitted dimension", str(caught.exception))
        with self.assertRaises(SchemaValidationError) as outside:
            DEFAULT_DIMENSION_REGISTRY.require_admitted(["intent-adherence", "aura"], "contract x")
        self.assertIn("outside the registry", str(outside.exception))

    def test_canonical_dimensions_cannot_be_shadowed(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            DimensionRegistry(
                extension_dimensions=(
                    FidelityDimension("geometry-integrity", label="Mine now", core=False),
                )
            )
        self.assertIn("cannot be re-registered", str(caught.exception))

    def test_an_extension_has_to_declare_itself_non_core(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            DimensionRegistry(
                extension_dimensions=(FidelityDimension("aura-fidelity", label="Aura", core=True),)
            )
        self.assertIn("must declare core=False", str(caught.exception))

    def test_the_extension_set_is_bounded_and_unique(self) -> None:
        with self.assertRaises(SchemaValidationError) as capped:
            DimensionRegistry(
                extension_dimensions=tuple(
                    FidelityDimension(f"ext-{index}", label=f"Ext {index}", core=False)
                    for index in range(MAX_EXTENSION_DIMENSIONS + 1)
                )
            )
        self.assertIn("at most", str(capped.exception))
        with self.assertRaises(SchemaValidationError):
            DimensionRegistry(
                extension_dimensions=(
                    FidelityDimension("voice-identity", label="One", core=False),
                    FidelityDimension("voice-identity", label="Twice", core=False),
                )
            )

    def test_a_foreign_registry_version_is_refused_not_interpreted(self) -> None:
        payload = extension_registry("voice-identity").to_payload()
        payload["version"] = "m01-dimension-registry-v2"
        with self.assertRaises(SchemaValidationError) as caught:
            DimensionRegistry.from_payload(payload)
        self.assertIn("unsupported dimension registry version", str(caught.exception))
        with self.assertRaises(SchemaValidationError):
            DimensionRegistry.from_payload({"version": DIMENSION_REGISTRY_VERSION})

    def test_the_registry_round_trips_through_its_payload(self) -> None:
        registry = extension_registry("voice-identity", "audio-clarity")
        restored = DimensionRegistry.from_payload(registry.to_payload())
        self.assertEqual(restored.dimension_ids, registry.dimension_ids)
        self.assertEqual(restored.extension_ids, registry.extension_ids)
        self.assertEqual(DimensionRegistry.from_payload(restored), restored)


class RegistryBackedContractTests(TestCase):
    def test_a_contract_may_declare_its_registered_extensions(self) -> None:
        registry = extension_registry(*AUDIO_DIMENSIONS[1:])
        target = contract(
            dimension_ids=AUDIO_DIMENSIONS, dimension_registry=registry, output_class=QualityClass.REVIEW
        )
        self.assertEqual(target.extension_dimension_ids, ("voice-identity", "audio-clarity"))
        self.assertEqual(
            FidelityContract.from_payload(target.to_payload()).dimension_registry, registry
        )

    def test_an_unregistered_dimension_fails_closed_everywhere(self) -> None:
        with self.assertRaises(SchemaValidationError):
            contract(dimension_ids=("intent-adherence", "aura-fidelity"))
        with self.assertRaises(RegistrationError) as profile:
            domain_profile(dimension_ids=("intent-adherence", "aura-fidelity"))
        self.assertIn("outside the registry", str(profile.exception))
        with self.assertRaises(RegistrationError) as descriptor:
            evaluator_descriptor(dimension_ids=("aura-fidelity",))
        self.assertIn("outside the registry", str(descriptor.exception))

    def test_a_zone_cannot_smuggle_an_unregistered_dimension_in(self) -> None:
        registry = extension_registry("voice-identity")
        zone = SemanticZone(
            zone_id="zone.chorus",
            label="Chorus",
            dimension_ids=("voice-identity", "aura-fidelity"),
        )
        with self.assertRaises(SchemaValidationError):
            contract(dimension_ids=AUDIO_DIMENSIONS, dimension_registry=registry, zones=(zone,))

    def test_a_profile_carries_its_registry_into_every_contract(self) -> None:
        registry = extension_registry("voice-identity", "audio-clarity")
        profile = domain_profile(
            dimension_ids=AUDIO_DIMENSIONS,
            promotion_rules=ladder_rules(AUDIO_DIMENSIONS),
            dimension_registry=registry,
        )
        built = profile.instantiate(
            contract_id="contract.narration",
            intent="prove the extension path",
            output_class=QualityClass.REVIEW,
        )
        self.assertEqual(built.dimension_registry, registry)
        self.assertEqual(built.extension_dimension_ids, ("voice-identity", "audio-clarity"))
        catalogue = DomainProfileRegistry()
        catalogue.register(profile)
        self.assertEqual(catalogue.get("profile.test").dimension_ids, AUDIO_DIMENSIONS)

    def test_an_extension_dimension_gates_the_ladder_like_a_canonical_one(self) -> None:
        registry = extension_registry("voice-identity", "audio-clarity")
        target = contract(
            dimension_ids=AUDIO_DIMENSIONS,
            dimension_registry=registry,
            promotion_rules=ladder_rules(AUDIO_DIMENSIONS),
            output_class=QualityClass.MASTER,
        )
        decision = DecisionEngine().evaluate(
            target, SUBJECT, assessments=covered_assessments(AUDIO_DIMENSIONS)
        )
        self.assertEqual(decision.outcome.value, "PROMOTED")
        self.assertEqual(
            sorted(item.dimension_id for item in decision.dimensions), sorted(AUDIO_DIMENSIONS)
        )

    def test_a_failed_extension_dimension_bars_promotion(self) -> None:
        registry = extension_registry("voice-identity", "audio-clarity")
        target = contract(
            dimension_ids=AUDIO_DIMENSIONS,
            dimension_registry=registry,
            promotion_rules=ladder_rules(AUDIO_DIMENSIONS),
            output_class=QualityClass.MASTER,
        )
        assessments = list(covered_assessments(("intent-adherence", "audio-clarity")))
        assessments.append(
            covered_assessments(("voice-identity",), gate=GateState.FAIL)[0]
        )
        decision = DecisionEngine().evaluate(target, SUBJECT, assessments=tuple(assessments))
        self.assertEqual(decision.outcome.value, "NOT_PROMOTED")
        self.assertIn("dimension_gate_not_pass", decision.blocker_codes)
        failed = next(
            item for item in decision.dimensions if item.dimension_id == "voice-identity"
        )
        self.assertEqual(failed.gate, GateState.FAIL.value)
