from __future__ import annotations

import unittest
from dataclasses import replace

from iris_resource_twin import (
    CompatibilityLevel,
    ExtensionField,
    MigrationAction,
    MigrationOperation,
    MigrationPlan,
    SchemaDescriptor,
    VersionedDocument,
    create_document,
    content_digest,
    deserialize,
    migrate_document,
    round_trip,
    serialize,
    verify_document,
    verify_migration_receipt,
)


class TestM09Versioning(unittest.TestCase):
    def _source(self) -> VersionedDocument:
        schema = SchemaDescriptor("iris-resource-twin", 1, 0, 0)
        return create_document(
            schema,
            {"snapshot_id": "snapshot-1", "capacity": {"physical_bytes": 8 * 1024**3, "unknown_bytes": None}},
            document_id="document-v1", created_at_ms=1_000,
            extensions=(
                ExtensionField("org.example", "optional-label", "1.0.0", False, {"name": "GPU"}),
                ExtensionField("iris.core", "required-contract", "1.0.0", True, ["capacity", "provenance"]),
            ),
        )

    def test_document_digest_is_canonical_immutable_and_round_trips(self) -> None:
        document = self._source()
        self.assertTrue(verify_document(document))
        self.assertEqual(round_trip(document), document)
        self.assertEqual(serialize(document), serialize(deserialize(serialize(document))))
        with self.assertRaises(ValueError):
            create_document(document.schema, {"not-json": object()}, document_id="invalid-document", created_at_ms=1)

    def test_minor_migration_preserves_body_required_features_and_lineage(self) -> None:
        source = self._source()
        target_schema = SchemaDescriptor("iris-resource-twin", 1, 1, 0)
        plan = MigrationPlan(
            "plan-rename", source.document_digest, source.schema, target_schema,
            CompatibilityLevel.MINOR,
            (MigrationAction("rename-label", MigrationOperation.RENAME_OPTIONAL, "org.example", "optional-label", "display-label"),),
            ("snapshot-core", "iris.core:required-contract"), (), ("display-label",), "M09:migration-authorization",
        )
        result, receipt = migrate_document(source, plan, result_id="document-v1-1", result_time_ms=2_000, receipt_id="receipt-1")
        self.assertEqual(result.parent_document_digest, source.document_digest)
        self.assertEqual(result.schema, target_schema)
        self.assertEqual(result.body, source.body)
        self.assertIn(("org.example", "display-label"), {(item.namespace, item.key) for item in result.extensions})
        self.assertIn(("iris.core", "required-contract"), {(item.namespace, item.key) for item in result.extensions})
        self.assertTrue(verify_migration_receipt(source, result, plan, receipt))
        self.assertNotEqual(source.document_digest, result.document_digest)

    def test_optional_loss_must_be_explicit_and_required_fields_cannot_be_dropped(self) -> None:
        source = self._source()
        target = SchemaDescriptor("iris-resource-twin", 2, 0, 0)
        illegal = MigrationPlan(
            "plan-required-drop", source.document_digest, source.schema, target,
            CompatibilityLevel.MAJOR,
            (MigrationAction("drop-required", MigrationOperation.DROP_OPTIONAL, "iris.core", "required-contract"),),
            ("snapshot-core",), ("iris.core:required-contract",), (), "M09:migration-authorization",
        )
        with self.assertRaisesRegex(ValueError, "required extensions cannot be dropped"):
            migrate_document(source, illegal, result_id="bad-result", result_time_ms=2_000, receipt_id="bad-receipt")

        undeclared_loss = MigrationPlan(
            "plan-undeclared-loss", source.document_digest, source.schema, target,
            CompatibilityLevel.MAJOR,
            (MigrationAction("drop-optional", MigrationOperation.DROP_OPTIONAL, "org.example", "optional-label"),),
            ("snapshot-core",), (), (), "M09:migration-authorization",
        )
        with self.assertRaisesRegex(ValueError, "explicit loss declaration"):
            migrate_document(source, undeclared_loss, result_id="bad-result-2", result_time_ms=2_000, receipt_id="bad-receipt-2")

    def test_declared_optional_loss_has_a_lossy_receipt(self) -> None:
        source = self._source()
        target = SchemaDescriptor("iris-resource-twin", 2, 0, 0)
        plan = MigrationPlan(
            "plan-loss", source.document_digest, source.schema, target, CompatibilityLevel.MAJOR,
            (MigrationAction("drop-optional", MigrationOperation.DROP_OPTIONAL, "org.example", "optional-label"),),
            ("required-contract",), ("org.example:optional-label",), (), "M09:migration-authorization",
        )
        result, receipt = migrate_document(source, plan, result_id="document-v2", result_time_ms=2_000, receipt_id="receipt-loss")
        self.assertEqual(receipt.loss_classification, "LOSSY")
        self.assertEqual(result.extensions[0].key, "required-contract")
        self.assertTrue(verify_migration_receipt(source, result, plan, receipt))

    def test_migration_receipt_rejects_rehashed_semantic_extension_tampering(self) -> None:
        source = self._source()
        target_schema = SchemaDescriptor("iris-resource-twin", 1, 1, 0)
        plan = MigrationPlan(
            "plan-tamper", source.document_digest, source.schema, target_schema,
            CompatibilityLevel.MINOR,
            (MigrationAction("rename-label", MigrationOperation.RENAME_OPTIONAL, "org.example", "optional-label", "display-label"),),
            ("snapshot-core", "iris.core:required-contract"), (), (), "M09:migration-authorization",
        )
        result, receipt = migrate_document(source, plan, result_id="document-v1-tampered", result_time_ms=2_000, receipt_id="receipt-tampered")
        tampered_extensions = tuple(
            ExtensionField(item.namespace, item.key, item.version, item.required, {"name": "tampered"})
            if item.namespace == "org.example" else item
            for item in result.extensions
        )
        tampered = create_document(
            result.schema, result.body, document_id=result.document_id, created_at_ms=result.created_at_ms,
            extensions=tampered_extensions, parent_document_digest=source.document_digest,
        )
        tampered_receipt_digest = content_digest({
            "receipt_id": receipt.receipt_id,
            "plan_id": plan.plan_id,
            "source": source.document_digest,
            "result": tampered.document_digest,
            "actions": receipt.action_results,
            "loss": "LOSSY" if plan.loss_features else "LOSSLESS",
            "preserved": plan.preserved_features,
            "loss_features": plan.loss_features,
            "defaults": plan.defaulted_features,
        })
        forged_receipt = replace(
            receipt, result_document_digest=tampered.document_digest,
            receipt_digest=tampered_receipt_digest,
        )
        with self.assertRaisesRegex(ValueError, "result extensions do not match"):
            verify_migration_receipt(source, tampered, plan, forged_receipt)
        self.assertIn(("org.example", "optional-label"), {(item.namespace, item.key) for item in source.extensions})
        self.assertEqual(source.document_digest, self._source().document_digest)

    def test_serializer_rejects_unknown_type_tags_duplicate_keys_and_unbounded_payloads(self) -> None:
        with self.assertRaisesRegex(ValueError, "unregistered record"):
            deserialize('{"$record":"os.system","fields":{}}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            deserialize('{"$record":"x","$record":"y","fields":{}}')
        with self.assertRaisesRegex(ValueError, "maximum byte length"):
            deserialize(" " * 4_000_001)

    def test_serializer_is_unicode_canonical_and_rejects_ambiguous_numbers_and_keys(self) -> None:
        decomposed = "e\u0301"
        composed = "\u00e9"
        self.assertEqual(serialize(decomposed), serialize(composed))
        self.assertEqual(deserialize(serialize(decomposed)), composed)
        with self.assertRaisesRegex(ValueError, "normalization"):
            serialize({decomposed: 1, composed: 2})
        with self.assertRaisesRegex(ValueError, "non-canonical"):
            deserialize('"e\\u0301"')
        with self.assertRaisesRegex(ValueError, "finite"):
            serialize(float("inf"))
        with self.assertRaisesRegex(ValueError, "finite"):
            deserialize("1e999")
        with self.assertRaisesRegex(ValueError, "non-marker"):
            deserialize('{"$mapping":{"$hidden":1}}')


if __name__ == "__main__":
    unittest.main()
