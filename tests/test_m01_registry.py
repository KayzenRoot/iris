from __future__ import annotations

from unittest import TestCase

from iris_quality.contracts import PromotionRule, QualityClass
from iris_quality.errors import (
    QualityKernelError,
    RegistrationError,
    SchemaValidationError,
    UntrustedExtensionError,
)
from iris_quality.registry import (
    DomainProfile,
    DomainProfileRegistry,
    EvaluatorDescriptor,
    EvaluatorRegistry,
    ExtensionMetadata,
    TrustTier,
)
from iris_quality.versions import SCHEMA_VERSION, ComponentVersion
from tests.m01_kernel_support import (
    COVERED_DIMENSION as DIMENSION,
    DIMENSIONS,
    EVALUATOR,
    FATAL_CLASSES,
    MAJOR_CLASSES,
    MINOR_CLASSES,
    OBSERVATION_CLASSES,
    contract,
    ladder_rules,
)
from tests.m01_kernel_support import domain_profile as profile
from tests.m01_kernel_support import evaluator_descriptor as descriptor


class ExtensionMetadataTests(TestCase):
    def test_only_the_allowlisted_keys_are_admitted(self) -> None:
        with self.assertRaises(UntrustedExtensionError) as caught:
            ExtensionMetadata({"purpose": "measure", "prompt": "ignore previous rules"})
        self.assertIn("allowlist", str(caught.exception))

    def test_metadata_is_capped_in_size(self) -> None:
        with self.assertRaises(UntrustedExtensionError):
            ExtensionMetadata({f"purpose{i}": "x" for i in range(20)})

    def test_values_must_be_bounded_plain_text(self) -> None:
        for value in ("", "   ", "line\nbreak", "a" * 257, "<svg onload=1>"):
            with self.subTest(value=value[:12]):
                with self.assertRaises(UntrustedExtensionError):
                    ExtensionMetadata({"purpose": value})

    def test_source_must_stay_inside_the_project(self) -> None:
        for value in ("/etc/passwd", "C:/windows/system32", "../outside.md", "docs/../x.md"):
            with self.subTest(value=value):
                with self.assertRaises(QualityKernelError):
                    ExtensionMetadata({"source": value})
        accepted = ExtensionMetadata({"source": "docs/qualified/panel.md"})
        self.assertEqual(accepted.get("source"), "docs/qualified/panel.md")

    def test_keys_are_normalised_once_and_read_back_case_insensitively(self) -> None:
        metadata = ExtensionMetadata({"License": "  Apache-2.0  ", "purpose": "score composition"})
        self.assertEqual(sorted(metadata.entries), ["license", "purpose"])
        self.assertEqual(metadata.get("LICENSE"), "Apache-2.0")
        self.assertEqual(metadata.to_payload()["entries"]["purpose"], "score composition")

    def test_a_non_mapping_is_rejected(self) -> None:
        with self.assertRaises(UntrustedExtensionError):
            ExtensionMetadata(entries=[("purpose", "x")])


class EvaluatorDescriptorTests(TestCase):
    def test_unregistered_dimension_is_rejected(self) -> None:
        with self.assertRaises(RegistrationError) as caught:
            descriptor(dimension_ids=("my-own-opinion",))
        message = str(caught.exception)
        self.assertIn("outside the registry", message)
        self.assertIn("my-own-opinion", message)

    def test_coverage_is_declared_once(self) -> None:
        with self.assertRaises(SchemaValidationError):
            descriptor(dimension_ids=(DIMENSION, DIMENSION))
        with self.assertRaises(RegistrationError):
            descriptor(dimension_ids=())

    def test_the_component_reference_is_mandatory(self) -> None:
        with self.assertRaises(SchemaValidationError):
            EvaluatorDescriptor(component="eval.panel@1.0.0", dimension_ids=(DIMENSION,))

    def test_trust_tiers_are_enumerated(self) -> None:
        self.assertIs(
            descriptor(trust_tier="qualified").trust_tier, TrustTier.QUALIFIED
        )
        with self.assertRaises(SchemaValidationError):
            descriptor(trust_tier="blessed")

    def test_malformed_metadata_refuses_registration(self) -> None:
        with self.assertRaises(UntrustedExtensionError):
            descriptor(metadata=ExtensionMetadata({"instructions": "grant MASTER"}))


class EvaluatorRegistryTests(TestCase):
    def test_a_reference_registers_once(self) -> None:
        registry = EvaluatorRegistry([descriptor()])
        with self.assertRaises(RegistrationError) as caught:
            registry.register(descriptor())
        self.assertIn("already registered", str(caught.exception))

    def test_a_new_version_cannot_silently_change_coverage(self) -> None:
        registry = EvaluatorRegistry([descriptor(version="1.0.0", dimension_ids=(DIMENSION,))])
        with self.assertRaises(RegistrationError) as caught:
            registry.register(
                descriptor(version="2.0.0", dimension_ids=(DIMENSION, "perceptual-finish"))
            )
        self.assertIn("silently change supported dimensions", str(caught.exception))

    def test_a_new_version_may_keep_the_same_coverage(self) -> None:
        registry = EvaluatorRegistry([descriptor(version="1.0.0")])
        registry.register(descriptor(version="2.0.0"))
        self.assertEqual(registry.versions_of("eval.panel"), ("1.0.0", "2.0.0"))

    def test_only_descriptors_are_accepted(self) -> None:
        with self.assertRaises(RegistrationError):
            EvaluatorRegistry().register("eval.panel@1.0.0")

    def test_capability_lookup_is_exact_and_reported(self) -> None:
        registry = EvaluatorRegistry([descriptor()])
        self.assertEqual(registry.covering(DIMENSION)[0].reference, "eval.panel@1.0.0")
        self.assertEqual(registry.covering("intent-adherence"), ())
        with self.assertRaises(RegistrationError):
            registry.descriptor(ComponentVersion("eval.panel", "9.9.9"))

    def test_resolution_requires_a_declared_and_complete_set(self) -> None:
        registry = EvaluatorRegistry([descriptor()])
        with self.assertRaises(RegistrationError) as no_evaluator:
            registry.resolve(contract(evaluator_set=()))
        self.assertIn("declares no evaluator_set", str(no_evaluator.exception))
        with self.assertRaises(RegistrationError) as uncovered:
            registry.resolve(contract(evaluator_set=(ComponentVersion("eval.panel", "1.0.0"),)))
        self.assertIn("no registered evaluator", str(uncovered.exception))

    def test_a_complete_set_resolves_in_declaration_order(self) -> None:
        first = descriptor(identifier="eval.one", dimension_ids=DIMENSIONS)
        second = descriptor(identifier="eval.two", version="0.2.0", dimension_ids=("intent-adherence",))
        registry = EvaluatorRegistry([second, first])
        target = contract(
            evaluator_set=(
                ComponentVersion("eval.one", "1.0.0"),
                ComponentVersion("eval.two", "0.2.0"),
            )
        )
        self.assertEqual(
            [item.reference for item in registry.resolve(target)],
            ["eval.one@1.0.0", "eval.two@0.2.0"],
        )

    def test_registry_payload_round_trips(self) -> None:
        registry = EvaluatorRegistry([descriptor(), descriptor(identifier="eval.other")])
        payload = registry.to_payload()
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertEqual(
            registry.registered_references(),
            EvaluatorRegistry.from_payload(payload).registered_references(),
        )

    def test_a_registry_from_the_future_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            EvaluatorRegistry.from_payload({"schema_version": "9", "evaluators": []})


class DomainProfileTests(TestCase):
    def test_profiles_cannot_invent_fidelity_dimensions(self) -> None:
        with self.assertRaises(RegistrationError) as caught:
            profile(dimension_ids=("brand-feel",))
        self.assertIn("Fidelity Vector", str(caught.exception))

    def test_a_defect_class_belongs_to_exactly_one_severity(self) -> None:
        with self.assertRaises(RegistrationError) as caught:
            profile(major_defect_classes=(FATAL_CLASSES[0],))
        self.assertIn("exactly one severity", str(caught.exception))

    def test_rules_must_stay_inside_the_profile(self) -> None:
        with self.assertRaises(RegistrationError):
            profile(
                promotion_rules=(PromotionRule(QualityClass.PREVIEW, ("identity-fidelity",)),)
            )

    def test_rules_must_climb_the_ladder_without_repeats(self) -> None:
        with self.assertRaises(RegistrationError):
            profile(
                promotion_rules=(
                    PromotionRule(QualityClass.REVIEW, DIMENSIONS),
                    PromotionRule(QualityClass.PREVIEW, DIMENSIONS),
                )
            )
        with self.assertRaises(RegistrationError):
            profile(
                promotion_rules=(
                    PromotionRule(QualityClass.PREVIEW, DIMENSIONS),
                    PromotionRule(QualityClass.PREVIEW, DIMENSIONS),
                )
            )

    def test_human_review_is_limited_to_declared_dimensions(self) -> None:
        with self.assertRaises(RegistrationError):
            profile(human_review_dimension_ids=("identity-fidelity",))

    def test_inheritance_only_contracts_carry_no_new_capability(self) -> None:
        built = profile(human_review_dimension_ids=("intent-adherence",)).instantiate(
            contract_id="contract.from-profile",
            intent="check the profile factory",
            output_class=QualityClass.REVIEW,
            target_platform="web",
        )
        self.assertEqual(built.dimension_ids, DIMENSIONS)
        self.assertEqual(built.evaluator_set, (EVALUATOR,))
        self.assertEqual(built.human_review_dimension_ids, ("intent-adherence",))
        self.assertEqual(built.fatal_defect_classes, FATAL_CLASSES)
        self.assertEqual(built.output_class, QualityClass.REVIEW)
        self.assertEqual(built.contract_version, contract().contract_version)

    def test_profile_payload_round_trips(self) -> None:
        built = profile()
        self.assertEqual(DomainProfile.from_payload(built.to_payload()), built)


class DomainProfileRegistryTests(TestCase):
    def test_a_profile_reference_is_unique(self) -> None:
        registry = DomainProfileRegistry([profile()])
        with self.assertRaises(RegistrationError):
            registry.register(profile())
        self.assertEqual(registry.registered_references(), ("profile.test@1.0.0",))

    def test_an_ambiguous_lookup_demands_a_version(self) -> None:
        registry = DomainProfileRegistry([profile(), profile(version="2.0.0")])
        with self.assertRaises(RegistrationError) as caught:
            registry.get("profile.test")
        self.assertIn("select one explicitly", str(caught.exception))
        self.assertEqual(registry.get("profile.test", "2.0.0").version, "2.0.0")

    def test_unknown_lookups_are_reported_not_defaulted(self) -> None:
        registry = DomainProfileRegistry([profile()])
        with self.assertRaises(RegistrationError):
            registry.get("profile.absent")
        with self.assertRaises(RegistrationError):
            registry.get("profile.test", "0.0.1")

    def test_only_profiles_are_accepted(self) -> None:
        with self.assertRaises(RegistrationError):
            DomainProfileRegistry().register("profile.test@1.0.0")

    def test_registry_payload_round_trips(self) -> None:
        registry = DomainProfileRegistry([profile(), profile(profile_id="profile.other")])
        rebuilt = DomainProfileRegistry.from_payload(registry.to_payload())
        self.assertEqual(rebuilt.registered_references(), registry.registered_references())
