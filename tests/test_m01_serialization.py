from __future__ import annotations

import json
from unittest import TestCase

from iris_quality.decision import DecisionEngine
from iris_quality.dimensions import GateState
from iris_quality.errors import SchemaValidationError, UnsupportedVersionError
from iris_quality.judging import ValidationCheck, ValidatorOutcome
from iris_quality.registry import (
    DomainProfileRegistry,
    EvaluatorDescriptor,
    EvaluatorRegistry,
    ExtensionMetadata,
)
from iris_quality.serialization import (
    ENVELOPE_KEYS,
    SERIALIZABLE_TYPES,
    dumps,
    envelope,
    from_envelope,
    loads,
    type_name,
    validate_payload,
)
from iris_quality.versions import SCHEMA_VERSION, ComponentVersion, content_digest
from iris_quality.zones import SemanticZone
from tests.m01_kernel_support import (
    EVALUATOR,
    SUBJECT,
    covered_assessments,
    contract,
    defect,
    debt,
    evidence,
    judge_result,
    promotion_authority,
)
from tests.m01_kernel_support import domain_profile as profile
from tests.m01_kernel_support import evaluator_descriptor as descriptor

def sample(name: str) -> object:
    """One representative value for every serializable kernel type."""

    if name not in _BUILDERS:
        raise AssertionError(f"no sample builder registered for {name}")
    return _BUILDERS[name]()


def _zone() -> SemanticZone:
    return SemanticZone("zone.sample", "Sample zone", ("geometry-integrity",))


def _validator_outcome() -> ValidatorOutcome:
    target = contract()
    return ValidatorOutcome(
        validator=ComponentVersion("validator.static", "1.0.0"),
        contract_reference=target.reference,
        subject=SUBJECT,
        checks=(
            ValidationCheck(
                check_id="check.topology",
                gate=GateState.PASS.value,
                summary="mesh closes and carries no non-planar face",
                dimension_id="geometry-integrity",
                evidence=(evidence("ev.topology", "geometry-integrity"),),
            ),
        ),
    )


def _decision() -> object:
    target = contract()
    return DecisionEngine().evaluate(target, SUBJECT, assessments=covered_assessments(), authority=promotion_authority(target))


def _evaluator_registry() -> EvaluatorRegistry:
    return EvaluatorRegistry([descriptor(), descriptor(identifier="eval.other")])


def _profile_registry() -> DomainProfileRegistry:
    return DomainProfileRegistry([profile(), profile(profile_id="profile.other")])


def _contract() -> object:
    return contract(zones=(_zone(),))


_BUILDERS: dict[str, object] = {
    "component_version": lambda: EVALUATOR,
    "subject_ref": lambda: SUBJECT,
    "evidence_ref": lambda: evidence("ev.sample", "intent-adherence"),
    "defect": lambda: defect("d.sample", "subject-absent"),
    "quality_debt": lambda: debt("d.sample", "subject-absent"),
    "dimension_assessment": lambda: covered_assessments()[0],
    "semantic_zone": _zone,
    "fidelity_contract": _contract,
    "judge_result": lambda: judge_result(contract(), covered_assessments()),
    "validator_outcome": _validator_outcome,
    "quality_decision": _decision,
    "extension_metadata": lambda: ExtensionMetadata(
        {"purpose": "measure composition", "license": "Apache-2.0"}
    ),
    "evaluator_descriptor": lambda: descriptor(),
    "evaluator_registry": _evaluator_registry,
    "domain_profile": profile,
    "domain_profile_registry": _profile_registry,
}


class EnvelopeTests(TestCase):
    def test_every_kernel_type_round_trips_through_its_envelope(self) -> None:
        self.assertEqual(
            sorted(_BUILDERS),
            sorted(SERIALIZABLE_TYPES),
            "a new kernel type needs a sample and a round trip here",
        )
        for name in sorted(SERIALIZABLE_TYPES):
            with self.subTest(name=name):
                value = sample(name)
                record = envelope(value)
                self.assertEqual(set(record), set(ENVELOPE_KEYS))
                self.assertEqual(record["type"], name)
                self.assertEqual(record["schema_version"], SCHEMA_VERSION)
                self.assertEqual(record["payload_sha256"], content_digest(record["payload"]))
                rebuilt = from_envelope(record)
                self.assertIs(type(rebuilt), type(value))
                self.assertEqual(rebuilt.to_payload(), value.to_payload())

    def test_the_envelope_digest_is_the_sha256_of_the_canonical_payload(self) -> None:
        record = envelope(contract())
        self.assertRegex(record["payload_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            record["payload_sha256"],
            content_digest(json.loads(json.dumps(record["payload"], sort_keys=True))),
        )

    def test_an_altered_payload_is_detected_before_parsing(self) -> None:
        record = envelope(defect("d.sample", "subject-absent"))
        tampered = {**record, "payload": {**record["payload"], "severity": "OBSERVATION"}}
        with self.assertRaises(SchemaValidationError) as caught:
            from_envelope(tampered)
        self.assertIn("altered in transit", str(caught.exception))

    def test_envelopes_are_closed_records(self) -> None:
        record = envelope(EVALUATOR)
        with self.assertRaises(SchemaValidationError):
            from_envelope({**record, "note": "trust me"})
        with self.assertRaises(SchemaValidationError):
            from_envelope({k: v for k, v in record.items() if k != "type"})
        with self.assertRaises(SchemaValidationError):
            from_envelope({**record, "type": "contract_of_guesses"})
        with self.assertRaises(SchemaValidationError):
            from_envelope("not a mapping")

    def test_a_schema_this_kernel_cannot_read_is_refused(self) -> None:
        record = {**envelope(EVALUATOR), "schema_version": "m01-schema-v0.0"}
        with self.assertRaises(UnsupportedVersionError) as caught:
            from_envelope(record)
        self.assertIn("unsupported schema_version", str(caught.exception))


class TextSerializationTests(TestCase):
    def test_the_same_object_always_emits_the_same_bytes(self) -> None:
        value = sample("quality_decision")
        self.assertEqual(dumps(value), dumps(value))
        self.assertEqual(loads(dumps(value)).content_sha256, value.content_sha256)

    def test_emitted_text_is_canonical_json(self) -> None:
        text = dumps(contract())
        self.assertEqual(
            text, json.dumps(json.loads(text), sort_keys=True, ensure_ascii=False)
        )
        self.assertNotIn("\\u", text)

    def test_round_trips_are_stable_over_two_hops(self) -> None:
        for name in sorted(SERIALIZABLE_TYPES):
            with self.subTest(name=name):
                first = dumps(sample(name))
                self.assertEqual(first, dumps(loads(first)))

    def test_text_that_is_not_json_is_reported_not_raised_as_a_decode_error(self) -> None:
        with self.assertRaises(SchemaValidationError):
            loads("{not json, neither is}")
        with self.assertRaises(SchemaValidationError):
            loads(envelope(EVALUATOR))

    def test_type_name_only_accepts_kernel_types(self) -> None:
        self.assertEqual(type_name(EVALUATOR), "component_version")
        with self.assertRaises(SchemaValidationError) as caught:
            type_name({"identifier": "eval.panel", "version": "1.0.0"})
        self.assertIn("not a serializable kernel type", str(caught.exception))


class PayloadValidationTests(TestCase):
    def test_validate_payload_accepts_only_what_re_emits_unchanged(self) -> None:
        built = contract()
        self.assertEqual(validate_payload("fidelity_contract", built.to_payload()), built)

    def test_a_payload_that_normalises_on_the_way_in_is_not_canonical(self) -> None:
        loose = {**contract().to_payload(), "output_class": "master"}
        with self.assertRaises(SchemaValidationError) as caught:
            validate_payload("fidelity_contract", loose)
        self.assertIn("not canonical", str(caught.exception))

    def test_unknown_missing_and_unsupported_fields_are_all_refused(self) -> None:
        payload = contract().to_payload()
        with self.assertRaises(SchemaValidationError):
            validate_payload("fidelity_contract", {**payload, "score": 9.9})
        with self.assertRaises(SchemaValidationError):
            validate_payload(
                "fidelity_contract", {k: v for k, v in payload.items() if k != "intent"}
            )
        with self.assertRaises(UnsupportedVersionError):
            validate_payload("fidelity_contract", {**payload, "contract_version": "m01-v9.9"})
        with self.assertRaises(SchemaValidationError):
            validate_payload("contract_of_guesses", payload)

    def test_a_descriptor_is_only_reusable_when_its_metadata_stays_admitted(self) -> None:
        built = descriptor(
            metadata=ExtensionMetadata({"qualification": "calibrated against held-out review"})
        )
        self.assertEqual(
            EvaluatorDescriptor.from_payload(built.to_payload()),
            built,
        )
