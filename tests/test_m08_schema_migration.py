from __future__ import annotations

import unittest
from dataclasses import replace

from iris_microbenchmark import (
    CalibrationArtifact, CalibrationKind, CompatibilityLevel,
    ExtensionDisposition, ExtensionField, ExternalSchemaProjection, FreshnessAssessment,
    FreshnessState, MigrationAction, MigrationOperation, MicrobenchmarkAdmissionError,
    MicrobenchmarkIntegrityError, PrivacyClass, SchemaDescriptor, SchemaMigrationPlan,
    SchemaVersion, build_acceptance_evidence_bundle, content_digest, create_document,
    create_provenance_export_digest, decode_document, encode_document, migrate_document,
    negotiate_schema, verify_document, verify_migration_receipt,
)
from m08_support import envelope, fixture, measurement_result, probe, protocol, purpose


class TestExternalContracts(unittest.TestCase):
    def test_external_projection_and_acceptance_evidence_are_exact(self):
        selected_protocol = protocol()
        selected_fixture = fixture()
        selected_probe = probe(selected_protocol, selected_fixture)
        selected_probe = replace(selected_probe, adapter=replace(selected_probe.adapter, version="2.0.0"))
        result = measurement_result(protocol_value=selected_protocol)
        selected_envelope = envelope(result)
        calibration = CalibrationArtifact(
            "calibration-acceptance-v1", "1.0.0", result.protocol_id, result.protocol_version,
            result.metric.metric_id, result.metric.version, "calibration-reference-01",
            content_digest(result.binding), CalibrationKind.CORRECTION, "affine-v1", 1.5, 0.25, 0.02,
            0, 10_000, 10, "calibration-review-01",
        )
        from iris_microbenchmark import apply_calibration
        derived = apply_calibration(result, calibration, derived_id="derived-acceptance-v1", at_ms=50)
        subjects = (result.result_id, selected_envelope.envelope_id, calibration.calibration_id, derived.derived_id)
        freshness = tuple(FreshnessAssessment(subject, FreshnessState.CURRENT, 51, 1, (), None, True) for subject in subjects)
        bundle = build_acceptance_evidence_bundle(
            bundle_id="acceptance-bundle-v1", binding=result.binding,
            protocols=(selected_protocol,), fixtures=(selected_fixture,), probes=(selected_probe,),
            probe_result_pairs=((selected_probe.probe_id, result.result_id),),
            results=(result,), envelopes=(selected_envelope,), calibrations=(calibration,),
            calibrated_evidence=(derived,), freshness=freshness, evidence_purpose=purpose(), created_at_ms=51,
        )
        self.assertEqual(bundle.release_acceptance_decision, "EVIDENCE_ONLY")
        self.assertEqual(bundle.authority_namespace, "hardware-capability")
        self.assertEqual(bundle.binding_digest, content_digest(result.binding))
        self.assertEqual(len(bundle.protocol_refs[0]), 3)
        self.assertEqual(len(bundle.fixture_refs[0]), 3)
        self.assertEqual(len(bundle.probe_refs[0]), 4)
        self.assertEqual(bundle.freshness_states, tuple(sorted((item, FreshnessState.CURRENT) for item in subjects)))
        self.assertEqual(bundle.bundle_digest, content_digest({field: getattr(bundle, field) for field in (
            "bundle_id", "version", "authority_namespace", "binding_digest", "protocol_refs", "fixture_refs",
            "probe_refs", "probe_result_refs", "result_refs", "envelope_refs", "calibration_refs", "calibrated_evidence_refs",
            "freshness_states", "evidence_purpose", "release_acceptance_decision", "created_at_ms",
        )}))
        with self.assertRaises(MicrobenchmarkIntegrityError):
            replace(bundle, bundle_digest="0" * 64)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            replace(bundle, release_acceptance_decision="APPROVED_FOR_RELEASE")

        schema_v1 = SchemaDescriptor("iris-m08-external", SchemaVersion(1, 0, 0), ("acceptance_bundle",), ("compact_projection",), "canonical-json-v1")
        consumer = ExternalSchemaProjection(
            "consumer-projection-v1", "1.0.0", "consumer-test", schema_v1.schema_id,
            SchemaVersion(1, 0, 0), SchemaVersion(1, 2, 0), ("acceptance_bundle",),
            ("compact_projection",), (CompatibilityLevel.PATCH, CompatibilityLevel.MINOR),
        )
        accepted = negotiate_schema(schema_v1, consumer, producer_features=("acceptance_bundle", "compact_projection"), declared_level=CompatibilityLevel.PATCH)
        self.assertEqual(accepted.result, "ACCEPTED")
        rejected = negotiate_schema(schema_v1, consumer, producer_features=("compact_projection",), declared_level=CompatibilityLevel.PATCH)
        self.assertEqual(rejected.result, "REJECTED")

        extension = ExtensionField("consumer-test", "display_hint", "1.0.0", ExtensionDisposition.OPTIONAL_PRESERVE, {"mode": "compact"})
        document = create_document(schema_v1, bundle, extensions=(extension,), created_at_ms=51)
        encoded = encode_document(document)
        decoded = decode_document(encoded)
        self.assertTrue(verify_document(decoded))
        self.assertEqual(decoded, document)
        self.assertEqual(encode_document(decoded), encoded)

        schema_v2 = SchemaDescriptor("iris-m08-external", SchemaVersion(1, 0, 1), ("acceptance_bundle",), ("compact_projection",), "canonical-json-v1")
        rename = MigrationAction(
            "rename-display-hint", MigrationOperation.RENAME_OPTIONAL_EXTENSION,
            "consumer-test", "display_hint", "render_hint", None, "migration-policy-01",
        )
        plan = SchemaMigrationPlan(
            "schema-plan-v2", "1.0.0", document.document_digest, schema_v1, schema_v2,
            CompatibilityLevel.PATCH, (rename,), ("acceptance_bundle", "display_hint"), (), (), "schema-migration-grant-01",
        )
        migrated, receipt = migrate_document(document, plan, result_time_ms=52, receipt_id="migration-receipt-v2")
        self.assertNotEqual(migrated.document_digest, document.document_digest)
        self.assertEqual(migrated.parent_document_digest, document.document_digest)
        self.assertEqual(migrated.extensions[0].key, "render_hint")
        self.assertTrue(verify_migration_receipt(document, migrated, plan, receipt))
        self.assertEqual(document.extensions[0].key, "display_hint")
        with self.assertRaises(MicrobenchmarkIntegrityError):
            replace(receipt, receipt_digest="0" * 64)

        export_digest = create_provenance_export_digest(
            digest_id="provenance-export-v1", version="1.0.0", source_result_ids=(result.result_id,),
            evidence_purpose=purpose(), privacy_class=PrivacyClass.SYNTHETIC,
        )
        self.assertEqual(export_digest.digest, content_digest({
            "digest_id": export_digest.digest_id, "version": export_digest.version,
            "source_result_ids": export_digest.source_result_ids,
            "evidence_purpose": export_digest.evidence_purpose, "privacy_class": export_digest.privacy_class,
        }))


if __name__ == "__main__":
    unittest.main()
