from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from iris_asset_dna.base import SemanticRef
from iris_asset_dna.identity import DNARevisionRef
from iris_project_os.identity import EntityKind, ExternalRef

from iris_production_state.base import freeze_json, require_exact_ref
from iris_production_state.dependencies import OperationalDependencyObservation, build_reverse_index
from iris_production_state.enums import DependencyKind, IndexState, MaterialityState, MigrationOperationKind
from iris_production_state.errors import ProductionStateAdmissionError, ProductionStateLimitError, ProductionStateValidationError
from iris_production_state.limits import ProductionStateLimits
from iris_production_state.migration import DataMigrationOperation, MigrationPlan, apply_migration
from iris_production_state.serialization import canonical_deserialize, canonical_fingerprint, canonical_serialize, semantic_round_trip

from m06_support import external, master_manifest, operational_revision, semantic_revision


ROOT = Path(__file__).resolve().parents[1]


class M06SerializationSecurityTests(unittest.TestCase):
    def test_m02_m05_m06_semantic_round_trip_and_fingerprints(self) -> None:
        source = semantic_revision("roundtrip-artifact", "roundtrip-revision")
        dna_revision = DNARevisionRef("dna-subject", "dna-r4", "a" * 64)
        semantic_ref = SemanticRef("m53", "rights.record", "rights-source", "r2")
        master, _ = master_manifest(operational_revision("roundtrip-operational", source))
        for value in (source, dna_revision, semantic_ref, master):
            with self.subTest(value_type=type(value).__name__):
                encoded = canonical_serialize(value)
                self.assertEqual(canonical_deserialize(encoded), value)
                self.assertEqual(canonical_serialize(value), encoded)
                self.assertEqual(canonical_fingerprint(value), canonical_fingerprint(semantic_round_trip(value)))

    def test_duplicate_unknown_and_noncanonical_payloads_fail_closed(self) -> None:
        source = semantic_revision("strict-artifact", "strict-revision")
        encoded = canonical_serialize(source)
        with self.assertRaises(ProductionStateValidationError):
            canonical_deserialize(b'{"format":"iris-m06-json-v1","format":"iris-m06-json-v1","record":{}}')
        payload = json.loads(encoded)
        payload["record"]["$record"] = "evil.module.Payload"
        with self.assertRaises(ProductionStateAdmissionError):
            canonical_deserialize(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        payload = json.loads(encoded)
        payload["record"]["fields"]["unknown"] = "payload"
        with self.assertRaises(ProductionStateAdmissionError):
            canonical_deserialize(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        with self.assertRaises(ProductionStateValidationError):
            canonical_deserialize(b'{"format":"iris-m06-json-v1","record":NaN}')

    def test_data_only_migration_is_immutable_and_bounded(self) -> None:
        original = {"schema_version": "schema-v1", "legacy": {"display": "asset"}, "keep": [1, 2]}
        plan = MigrationPlan(
            "migration-v1-v2",
            "schema-v1",
            "schema-v2",
            (
                DataMigrationOperation(MigrationOperationKind.RENAME, ("legacy", "display"), ("presentation", "label")),
                DataMigrationOperation(MigrationOperationKind.DEFAULT, ("presentation", "visible"), literal_value=True),
                DataMigrationOperation(MigrationOperationKind.DROP, ("legacy",)),
            ),
        )
        receipt = apply_migration(original, plan, receipt_id="migration-receipt", applied_at_ms=3)
        self.assertEqual(original["legacy"]["display"], "asset")
        self.assertEqual(receipt.migrated_document["presentation"]["label"], "asset")
        self.assertEqual(receipt.migrated_document["schema_version"], "schema-v2")
        with self.assertRaises(ProductionStateValidationError):
            DataMigrationOperation(MigrationOperationKind.DEFAULT, ("callable",), literal_value=lambda: None)
        with self.assertRaises(ProductionStateAdmissionError):
            apply_migration(original, MigrationPlan("wrong-schema", "other", "target", (DataMigrationOperation(MigrationOperationKind.DROP, ("keep",)),)), receipt_id="wrong", applied_at_ms=3)

    def test_resource_limits_and_unknown_dependency_index_states(self) -> None:
        limits = ProductionStateLimits(max_dependencies=2, max_json_depth=2, max_json_items=2)
        with self.assertRaises(ProductionStateLimitError):
            freeze_json({"a": {"b": {"c": 1}}}, limits=limits)
        consumer = operational_revision("limit-consumer")
        refs = (external("dep-a"), external("dep-b"), external("dep-c"))
        observations = tuple(
            OperationalDependencyObservation(consumer, ref, DependencyKind.REQUIRED, MaterialityState.MATERIAL, "facet", external(f"evidence-{index}"), index)
            for index, ref in enumerate(refs)
        )
        with self.assertRaises(ProductionStateLimitError):
            build_reverse_index("index-over-limit", "epoch", observations, limits=limits)
        self.assertEqual(IndexState.UNKNOWN.value, "UNKNOWN")

    def test_forbidden_imports_and_dynamic_execution_absent_from_kernel(self) -> None:
        forbidden_modules = {
            "bpy", "maya", "comfyui", "torch", "subprocess", "socket", "sqlite3", "requests", "httpx",
            "urllib", "sqlalchemy", "boto3", "iris_quality", "iris_m03", "iris_workflow_compiler", "iris_provider_sdk",
        }
        found: list[str] = []
        for path in (ROOT / "iris_production_state").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    names = []
                for imported in names:
                    if imported.split(".", 1)[0].casefold() in forbidden_modules:
                        found.append(f"{path.name}: import {imported}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                    found.append(f"{path.name}: dynamic {node.func.id}()")
        self.assertEqual(found, [])

    def test_external_version_refs_are_never_implicit_latest(self) -> None:
        with self.assertRaises(ProductionStateValidationError):
            require_exact_ref(ExternalRef(EntityKind.WORKFLOW, "workflow-current", version="latest"))
        with self.assertRaises(ProductionStateValidationError):
            require_exact_ref(ExternalRef(EntityKind.MODEL, "model-current", version="current"))


if __name__ == "__main__":
    unittest.main()
