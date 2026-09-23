from __future__ import annotations

import dataclasses
import unittest

from iris_hardware_genome import (
    ChangeClass,
    CompatibilityLevel,
    ConfidenceAxis,
    ConfidenceDescriptor,
    ConfidenceLevel,
    ExtensionDisposition,
    ExtensionField,
    EvidenceStrength,
    FreshnessClass,
    GenomeClaimStatus,
    HardwareGenomeAdmissionError,
    HardwareGenomeIntegrityError,
    HardwareGenomeLimitError,
    HardwareGenomeLimits,
    HardwareGenomeCompatibilityError,
    HardwareGenomeValidationError,
    MigrationOperation,
    ObservationState,
    SchemaCompatibilityDeclaration,
    SchemaDescriptor,
    SchemaMigrationAction,
    SchemaMigrationPlan,
    SchemaReaderDeclaration,
    SchemaVersion,
    SemanticKeyDefinition,
    SemanticKeyRegistry,
    REGISTRY_VERSION,
    validate_genome,
    canonical_deserialize,
    canonical_fingerprint,
    canonical_serialize,
    compare_schema_versions,
    create_material_change_event,
    create_genome_delta,
    migrate_genome,
    require_reader_compatibility,
    semantic_round_trip,
    validate_genome_delta,
    validate_material_change_event,
    verify_migration_receipt,
)
from m07_support import SUBJECT, SUBJECT_1, evidence, genome, observation


class TestGenome(unittest.TestCase):
    def test_genome_identity_is_canonical_and_records_are_immutable(self):
        first = genome()
        second = genome()
        self.assertEqual(first.genome_id, second.genome_id)
        self.assertEqual(canonical_serialize(first), canonical_serialize(second))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.created_at_ms = 9
        with self.assertRaises(TypeError):
            first.extensions["mutate"] = True

    def test_semantic_round_trip_and_fingerprints_are_deterministic(self):
        original = genome(extensions={"vendor.x": {"b": 2, "a": 1}})
        encoded = canonical_serialize(original)
        restored = canonical_deserialize(encoded)
        self.assertEqual(restored, original)
        self.assertEqual(semantic_round_trip(original), original)
        self.assertEqual(canonical_fingerprint(original), canonical_fingerprint(restored))
        self.assertEqual(encoded, canonical_serialize(restored))

    def test_transport_rejects_duplicate_keys_unknown_tags_and_noncanonical_bytes(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize('{"format":"iris-m07-json-v1","format":"iris-m07-json-v1","record":{}}')
        with self.assertRaises(HardwareGenomeAdmissionError):
            canonical_deserialize('{"format":"iris-m07-json-v1","record":{"$record":"builtins.eval","fields":{}}}')
        encoded = canonical_serialize(genome())
        with self.assertRaises(HardwareGenomeIntegrityError):
            canonical_deserialize(encoded.replace(b'"format"', b'"format" ', 1))

    def test_payloads_are_inert_bounded_json_and_never_executed(self):
        with self.assertRaises(HardwareGenomeValidationError):
            observation(value=object())
        with self.assertRaises(HardwareGenomeValidationError):
            observation(value=float("nan"))
        extension = ExtensionField("vendor", "metadata", "1.0", {"command": "shell: arbitrary", "label": "safe"}, ExtensionDisposition.OPTIONAL_PRESERVE)
        self.assertEqual(extension.value["command"], "shell: arbitrary")
        with self.assertRaises(HardwareGenomeAdmissionError):
            ExtensionField("vendor", "state", "1.0", {"value": "bad"}, ExtensionDisposition.OPTIONAL_PRESERVE)
        self.assertEqual(extension.value["label"], "safe")

    def test_confidence_is_multidimensional_and_cannot_exceed_its_evidence(self):
        source = observation(evidence_strength=EvidenceStrength.DECLARED)
        weak = genome((source,))
        self.assertIs(weak.confidence.level_for(ConfidenceAxis.EVIDENCE_STRENGTH), ConfidenceLevel.LOW)
        inflated = ConfidenceDescriptor(
            tuple((axis, ConfidenceLevel.VERIFIED) for axis in ConfidenceAxis),
            (source.evidence.evidence_id,), 0, 0,
        )
        with self.assertRaises(HardwareGenomeIntegrityError):
            genome((source,), confidence=inflated)

    def test_material_conflicts_lower_agreement_and_stay_attached(self):
        from iris_hardware_genome import DiscoveryConflict
        one = observation(observation_id="conflict-one", value="x")
        two = observation(observation_id="conflict-two", value="y", evidence_ref=evidence("conflict-two-e"))
        conflict = DiscoveryConflict("conflict", one.fact_key, (one.observation_id, two.observation_id), "MATERIAL_DISAGREEMENT")
        conflicted = observation(one.fact_key, observation_id="conflict-normalized", state=ObservationState.CONFLICTING)
        from iris_hardware_genome import FactEnvelope, REGISTRY_VERSION
        value = genome((one, two, conflicted), conflicts=(conflict,), facts=(FactEnvelope(conflicted.fact_key, conflicted, REGISTRY_VERSION),))
        self.assertEqual(value.conflicts, (conflict,))
        self.assertIs(value.confidence.level_for(ConfidenceAxis.SOURCE_AGREEMENT), ConfidenceLevel.LOW)
        self.assertEqual(canonical_deserialize(canonical_serialize(value)), value)
        from iris_hardware_genome import RedactionPolicy, redact_genome_view
        redacted = redact_genome_view(value, RedactionPolicy("conflict-view", "1.0"))
        self.assertIn((one.fact_key, ObservationState.CONFLICTING, one.freshness), redacted.preserved_fact_states)
        target_schema = dataclasses.replace(value.schema, version=SchemaVersion(1, 0, 1))
        declaration = SchemaCompatibilityDeclaration("conflict-patch", value.schema.version, target_schema.version, CompatibilityLevel.PATCH, True, False, "canonicalization-metadata")
        plan = SchemaMigrationPlan("conflict-migration", value.genome_id, str(value.schema.version), target_schema, declaration, ())
        migrated, _ = migrate_genome(value, plan, result_time_ms=2_000, receipt_id="conflict-receipt")
        self.assertEqual(migrated.conflicts, value.conflicts)
        self.assertIs(migrated.facts[0].observation.state, ObservationState.CONFLICTING)

    def test_fact_identity_is_unique_per_subject_runtime_and_semantic_key(self):
        one = observation(observation_id="duplicate-one", value="x")
        two = observation(observation_id="duplicate-two", value="y", evidence_ref=evidence("duplicate-two-e"))
        with self.assertRaises(HardwareGenomeIntegrityError):
            genome((one, two))

    def test_schema_reader_barrier_and_compatibility_axes_fail_closed(self):
        base = SchemaVersion(1, 0, 0)
        self.assertIs(compare_schema_versions(base, SchemaVersion(1, 0, 1)), CompatibilityLevel.PATCH)
        self.assertIs(compare_schema_versions(base, SchemaVersion(1, 1, 0)), CompatibilityLevel.MINOR)
        self.assertIs(compare_schema_versions(base, SchemaVersion(2, 0, 0)), CompatibilityLevel.MAJOR)
        with self.assertRaises(HardwareGenomeAdmissionError):
            SchemaCompatibilityDeclaration("bad-patch", base, SchemaVersion(1, 0, 1), CompatibilityLevel.PATCH, False, True, "semantic-change")
        descriptor = SchemaDescriptor("iris-m07-core-v1", SchemaVersion(1, 1, 0), ("new-required",), (), "iris-m07-canonical-v1")
        reader = SchemaReaderDeclaration("old-reader", 1, 1, (), True, True)
        with self.assertRaises(HardwareGenomeCompatibilityError):
            require_reader_compatibility(descriptor, reader)

    def test_unknown_optional_extension_is_namespaced_and_cannot_shadow_core(self):
        good = ExtensionField("vendor", "plugin-metadata", "1.0", {"opaque": "value"}, ExtensionDisposition.OPTIONAL_PRESERVE)
        self.assertEqual(good.namespace, "vendor")
        with self.assertRaises(HardwareGenomeAdmissionError):
            ExtensionField("vendor", "state", "1.0", {"value": "bad"}, ExtensionDisposition.OPTIONAL_PRESERVE)

    def test_semantic_registry_pins_prefixes_units_and_governed_extensions(self):
        registry = SemanticKeyRegistry()
        self.assertIsNotNone(registry.find("compute.api.cuda"))
        self.assertIsNotNone(registry.find("precision.fp8_e4m3.arithmetic"))
        definition = SemanticKeyDefinition(
            "vendor.sensor", "finite_number", "watt", (ObservationState.OBSERVED,),
            FreshnessClass.DYNAMIC, True, "vendor", True,
        )
        governed = SemanticKeyRegistry(REGISTRY_VERSION, (*registry.definitions, definition), ("vendor",))
        sensor = observation("vendor.sensor.power", observation_id="vendor-power", value=50.0, unit="watt", freshness=FreshnessClass.DYNAMIC)
        from iris_hardware_genome import FactEnvelope
        value = genome((sensor,), facts=(FactEnvelope(sensor.fact_key, sensor, governed.version),), semantic_registry=governed)
        self.assertTrue(validate_genome(value).valid)
        shadow = SemanticKeyDefinition(
            "hardware.shadow", "reported_hardware_fact", None, tuple(ObservationState),
            FreshnessClass.UNKNOWN_VOLATILITY, True, "hardware", True,
        )
        with self.assertRaises(HardwareGenomeAdmissionError):
            SemanticKeyRegistry(REGISTRY_VERSION, (*registry.definitions, shadow), ("hardware",))

    def test_immutable_lossless_migration_has_lineage_and_receipt(self):
        source = genome(extensions={"vendor.old": {"keep": True}})
        target_schema = SchemaDescriptor("iris-m07-core-v1", SchemaVersion(1, 1, 0), ("evidence-envelope-v1", "unknown-state-v1"), ("telemetry-v1", "redacted-advertisement-v1", "safe-extension-v1"), "iris-m07-canonical-v1")
        declaration = SchemaCompatibilityDeclaration("compat-minor", source.schema.version, target_schema.version, CompatibilityLevel.MINOR, True, False, "optional-extension-addition")
        action = SchemaMigrationAction("add-safe", MigrationOperation.ADD_OPTIONAL_EXTENSION, target_key="vendor.new", value={"added": True})
        plan = SchemaMigrationPlan("plan", source.genome_id, str(source.schema.version), target_schema, declaration, (action,))
        migrated, receipt = migrate_genome(source, plan, result_time_ms=2_000, receipt_id="receipt")
        self.assertNotEqual(source.genome_id, migrated.genome_id)
        self.assertEqual(migrated.parent_genome_id, source.genome_id)
        self.assertEqual(migrated.extensions["vendor.old"], {"keep": True})
        self.assertEqual(receipt.loss_classification, "LOSSLESS")
        self.assertTrue(verify_migration_receipt(source, migrated, plan, receipt))
        with self.assertRaises(HardwareGenomeIntegrityError):
            verify_migration_receipt(migrated, source, plan, receipt)

    def test_major_or_nonoptional_loss_is_not_implicit(self):
        with self.assertRaises(HardwareGenomeAdmissionError):
            SchemaCompatibilityDeclaration("invalid-major", SchemaVersion(1, 0, 0), SchemaVersion(2, 0, 0), CompatibilityLevel.MAJOR, True, False, "unsafe")
        with self.assertRaises(HardwareGenomeAdmissionError):
            SchemaMigrationAction("drop-required", MigrationOperation.DROP_OPTIONAL_EXTENSION, source_key="vendor.required", optional_only=False)

    def test_caller_limits_apply_to_full_genome_and_extensions(self):
        with self.assertRaises(HardwareGenomeLimitError):
            genome(subjects=(SUBJECT, SUBJECT_1), limits=HardwareGenomeLimits(max_subjects=1))
        with self.assertRaises(HardwareGenomeLimitError):
            genome(extensions={"vendor.a": {}, "vendor.b": {}}, limits=HardwareGenomeLimits(max_extension_fields=1))

    def test_delta_is_bound_to_exact_base_and_target_snapshots(self):
        base_observation = observation(observation_id="delta-a", value="vendor-a")
        target_observation = observation(observation_id="delta-b", value="vendor-b", evidence_ref=evidence("delta-b-e"))
        base = genome((base_observation,))
        target = genome((target_observation,))
        delta = create_genome_delta(base, target, delta_id="delta", created_at_ms=2_000)
        validate_genome_delta(delta, base, target)
        self.assertEqual(delta.base_genome_id, base.genome_id)
        self.assertEqual(delta.target_genome_id, target.genome_id)
        self.assertIn(ChangeClass.CAPABILITY, delta.change_classes)
        event = create_material_change_event(base, target, delta, event_id="event", version="1.0")
        validate_material_change_event(event, delta, base, target)
        with self.assertRaises(HardwareGenomeIntegrityError):
            validate_genome_delta(delta, target, base)
        with self.assertRaises(HardwareGenomeIntegrityError):
            validate_material_change_event(event, delta, target, base)

    def test_snapshot_claim_status_is_typed_and_historical_is_explicit(self):
        historical = genome(claim_status=GenomeClaimStatus.HISTORICAL)
        self.assertIs(historical.claim_status, GenomeClaimStatus.HISTORICAL)
        with self.assertRaises(HardwareGenomeValidationError):
            genome(claim_status="CURRENT_AT_CAPTURE")

    def test_stale_evidence_stays_stale_through_transport_and_migration(self):
        stale = observation(
            "telemetry.gpu.power", observation_id="old-power", state=ObservationState.STALE,
            freshness=FreshnessClass.DYNAMIC, unit="watt",
        )
        source = genome((stale,))
        restored = canonical_deserialize(canonical_serialize(source))
        self.assertIs(restored.facts[0].observation.state, ObservationState.STALE)
        target_schema = dataclasses.replace(source.schema, version=SchemaVersion(1, 0, 1))
        declaration = SchemaCompatibilityDeclaration("stale-patch", source.schema.version, target_schema.version, CompatibilityLevel.PATCH, True, False, "reader-metadata")
        plan = SchemaMigrationPlan("stale-plan", source.genome_id, str(source.schema.version), target_schema, declaration, ())
        migrated, _ = migrate_genome(source, plan, result_time_ms=2_000, receipt_id="stale-receipt")
        self.assertIs(migrated.facts[0].observation.state, ObservationState.STALE)


if __name__ == "__main__":
    unittest.main()
