from __future__ import annotations

import ast
import json
import unittest
from dataclasses import replace
from collections.abc import Mapping
from pathlib import Path

import iris_asset_dna as m05
from iris_asset_dna.analysis import (
    EquivalenceAxisResult,
    build_equivalence_witness,
    build_fingerprint_witness,
    compare_revisions,
    decide_equivalence,
    verify_fingerprint_witness,
)
from iris_asset_dna.errors import DNAAdmissionError, DNAIntegrityError, DNALimitError, DNAValidationError
from iris_asset_dna.identity import validate_revision
from iris_asset_dna.limits import DNARecordLimits
from iris_asset_dna.packages import conform_package
from iris_asset_dna.readiness import assess_dna_readiness
from iris_asset_dna.serialization import deserialize_record, registered_record_types, serialize_record
from iris_asset_dna.validation import validate_dna
from iris_asset_dna.versions import content_digest
from examples.m05_synthetic_profiles import public_summary, run_synthetic_profiles
from m05_support import AUTHORITY, EVIDENCE, POLICY, envelope, package_manifest, revision, trait


class TestM05SerializationSecurityAndBoundaries(unittest.TestCase):
    def test_canonicalization_rejects_custom_behavior_objects_without_iterating_them(self):
        accessed = []

        class HostileMapping(Mapping):
            def __getitem__(self, key):
                accessed.append("getitem")
                raise AssertionError("custom mapping executed")

            def __iter__(self):
                accessed.append("iter")
                raise AssertionError("custom mapping executed")

            def __len__(self):
                accessed.append("len")
                raise AssertionError("custom mapping executed")

        with self.assertRaises(DNAValidationError):
            m05.canonical_json(HostileMapping())
        with self.assertRaises(DNAValidationError):
            m05.freeze_json(HostileMapping())
        self.assertEqual(accessed, [])

        class HostileRecord(m05.CanonicalRecord):
            def __getattribute__(self, name):
                if name == "value":
                    accessed.append("record-field")
                    raise AssertionError("custom record executed")
                return object.__getattribute__(self, name)

        from dataclasses import dataclass

        HostileRecord = dataclass(frozen=True)(type("HostileRecord", (HostileRecord,), {"__annotations__": {"value": str}, "__module__": __name__}))
        value = object.__new__(HostileRecord)
        object.__setattr__(value, "value", "never-read")
        with self.assertRaises(DNAValidationError):
            m05.canonical_json(value)
        self.assertEqual(accessed, [])
        HostileRecord.__module__ = "iris_asset_dna.base"
        with self.assertRaises(DNAValidationError):
            m05.canonical_json(value)
        self.assertEqual(accessed, [])

    def test_digest_bearing_witnesses_and_reports_reject_recomputed_inconsistency(self):
        source = revision("dna-integrity-reports")
        witness = build_fingerprint_witness(source)
        witness_body = {
            "revision_ref": witness.revision_ref,
            "fingerprint": witness.fingerprint,
            "canonical_payload_digest": "0" * 64,
            "excluded_nonsemantic_fields": witness.excluded_nonsemantic_fields,
        }
        with self.assertRaises(DNAIntegrityError):
            replace(witness, canonical_payload_digest="0" * 64, witness_digest=content_digest(witness_body))

        report = validate_dna(envelope(source))
        with self.assertRaises(DNAIntegrityError):
            replace(report, report_digest="0" * 64)

        comparison = compare_revisions(source, revision("dna-integrity-reports", "r2", 2, parent_revision_refs=(source.ref,), traits=(trait("identity.signature", "green"),)))
        surface = comparison.change_surface
        surface_body = surface.to_payload()
        surface_body.pop("surface_digest")
        surface_body["semantic_changed"] = False
        forged_surface = replace(surface, semantic_changed=False, surface_digest=content_digest(surface_body))
        comparison_body = {
            "source_ref": comparison.source_ref,
            "target_ref": comparison.target_ref,
            "change_surface": forged_surface,
            "source_fingerprint": comparison.source_fingerprint,
            "target_fingerprint": comparison.target_fingerprint,
            "requires_governed_decision": comparison.requires_governed_decision,
        }
        with self.assertRaises(DNAIntegrityError):
            replace(comparison, change_surface=forged_surface, comparison_digest=content_digest(comparison_body))

    def test_canonical_json_is_deterministic_and_roundtrips_nested_records(self):
        source = revision("dna-transport", display_metadata={"asset_path": "private/local/a.png"}, evidence_refs=(EVIDENCE,))
        first_bytes = serialize_record(source)
        second_bytes = serialize_record(source)
        self.assertEqual(first_bytes, second_bytes)
        loaded = deserialize_record(first_bytes, expected_type=type(source))
        self.assertEqual(loaded, source)
        self.assertEqual(serialize_record(loaded), first_bytes)
        witness = build_fingerprint_witness(source)
        self.assertTrue(verify_fingerprint_witness(source, witness))
        self.assertEqual(deserialize_record(serialize_record(witness)), witness)

    def test_path_level_change_surface_and_equivalence_decisions(self):
        source = revision("dna-compare", "r1", 1, traits=(trait("identity.signature", "A"), trait("identity.name", "N", schema_family="identity.core")))
        changed = revision("dna-compare", "r2", 2, parent_revision_refs=(source.ref,), traits=(trait("identity.signature", "B"), trait("identity.name", "N", schema_family="identity.core")))
        comparison = compare_revisions(source, changed)
        self.assertEqual(comparison.change_surface.changed_trait_paths, ("identity.signature",))
        self.assertTrue(comparison.requires_governed_decision)
        self.assertEqual(deserialize_record(serialize_record(comparison)), comparison)
        other = revision("dna-compare-other", "r1", 1, traits=source.traits)
        axes = tuple(EquivalenceAxisResult(axis, "MATCH", (EVIDENCE,)) for axis in ("family", "identity_level", "schema", "traits", "components", "anchors", "domain_links"))
        witness = build_equivalence_witness(source, other, axes, (EVIDENCE,))
        decision = decide_equivalence(witness, authority_ref=AUTHORITY, policy_ref=POLICY, decision_evidence_refs=(EVIDENCE,))
        self.assertEqual(decision.outcome, "EQUIVALENT")
        self.assertEqual(deserialize_record(serialize_record(decision)), decision)

    def test_revision_package_validation_and_readiness_records_roundtrip(self):
        subject = revision("dna-valid")
        valid_envelope = envelope(subject)
        validation = validate_dna(valid_envelope)
        readiness = assess_dna_readiness(validation)
        self.assertTrue(validation.valid)
        self.assertEqual(readiness.state.value, "READY")
        self.assertFalse(readiness.quality_or_release_authority)
        self.assertEqual(deserialize_record(serialize_record(validation)), validation)
        self.assertEqual(deserialize_record(serialize_record(readiness)), readiness)
        manifest = package_manifest(subject)
        conformance = conform_package(manifest, (subject,), ())
        self.assertTrue(conformance.valid)
        self.assertEqual(deserialize_record(serialize_record(manifest)), manifest)
        self.assertEqual(deserialize_record(serialize_record(conformance)), conformance)

    def test_every_extension_port_is_a_versioned_roundtrip_record(self):
        m05.validate_port_catalog()
        self.assertEqual(len(m05.PORT_TYPES), 22)
        self.assertEqual(len(m05.DEFAULT_PORTS), 22)
        for port in m05.DEFAULT_PORTS:
            with self.subTest(port=port.port_name):
                self.assertEqual(deserialize_record(serialize_record(port)), port)
                self.assertEqual(port.port_version, m05.PORT_VERSION)

    def test_public_surface_and_transport_registry_are_closed_and_unambiguous(self):
        self.assertTrue(m05.__all__)
        self.assertEqual(len(m05.__all__), len(set(m05.__all__)))
        for module in m05._MODULES:
            self.assertTrue(module.__all__)
            for name in module.__all__:
                self.assertTrue(hasattr(module, name), (module.__name__, name))
        registry = registered_record_types()
        self.assertEqual(len(registry), len(set(registry)))
        self.assertEqual(len(registry), 112)
        self.assertTrue(all(issubclass(record_type, m05.CanonicalRecord) for record_type in registry.values()))

    def test_malformed_or_hostile_transport_fails_closed_without_dynamic_import(self):
        source = revision("dna-hostile")
        encoded = serialize_record(source).decode("utf-8")
        envelope_data = json.loads(encoded)
        envelope_data["kind"] = "builtins.eval"
        with self.assertRaises(DNAAdmissionError):
            deserialize_record(json.dumps(envelope_data))
        with self.assertRaises(DNAValidationError):
            deserialize_record(b'{"transport_version":"x","transport_version":"y","kind":"x","payload":{}}')
        with self.assertRaises(DNAValidationError):
            deserialize_record(b'{"transport_version":"iris-m05-json-v1","kind":"x","payload":{"value":NaN}}')
        envelope_data = json.loads(encoded)
        envelope_data["payload"]["unexpected"] = "must fail"
        with self.assertRaises(DNAValidationError):
            deserialize_record(json.dumps(envelope_data))
        with self.assertRaises(DNALimitError):
            serialize_record(source, limits=DNARecordLimits(max_inline_payload_bytes=1))
        with self.assertRaises(DNALimitError):
            serialize_record(source, limits=DNARecordLimits(max_text_chars=8))
        with self.assertRaises(DNALimitError):
            deserialize_record(encoded, limits=DNARecordLimits(max_text_chars=8))
        with self.assertRaises(DNALimitError):
            deserialize_record(encoded, limits=DNARecordLimits(max_canonical_depth=2))

    def test_unknown_required_schemas_and_wrong_expected_types_fail_closed(self):
        unknown = revision("dna-unknown-schema", traits=(trait("identity.future", schema_family="future.required"),))
        with self.assertRaises(DNAAdmissionError):
            validate_revision(unknown)
        known = revision("dna-known-schema")
        with self.assertRaises(DNAIntegrityError):
            deserialize_record(serialize_record(known), expected_type=m05.DNAEnvelope)

    def test_kernel_import_boundaries_exclude_providers_io_and_execution(self):
        root = Path(m05.__file__).resolve().parent
        forbidden_modules = {
            "bpy", "maya", "pymaya", "openai", "anthropic", "torch", "tensorflow", "requests", "httpx",
            "urllib", "socket", "subprocess", "sqlite3", "sqlalchemy", "psycopg", "stripe", "selenium",
        }
        forbidden_calls = {"eval", "exec", "compile", "__import__"}
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".", 1)[0] for alias in node.names}
                    self.assertFalse(roots & forbidden_modules, (path.name, roots & forbidden_modules))
                elif isinstance(node, ast.ImportFrom):
                    root_name = (node.module or "").split(".", 1)[0]
                    self.assertNotIn(root_name, forbidden_modules, (path.name, root_name))
                elif isinstance(node, ast.Call):
                    name = node.func.id if isinstance(node.func, ast.Name) else None
                    self.assertNotIn(name, forbidden_calls, (path.name, name))

    def test_eight_synthetic_profiles_use_the_single_builder(self):
        profiles = run_synthetic_profiles()
        summary = public_summary(profiles)
        self.assertEqual(summary["profile_count"], 8)
        self.assertEqual(set(summary["profile_ids"]), {
            "corporate.spokesperson", "asymmetric.creature", "generic.object",
            "product.identity.levels", "persistent.environment", "crossmodal.character",
            "scene.identity.roles", "portable.dna.package",
        })
        self.assertTrue(summary["same_builder"])
        self.assertEqual(sum(summary["subjects_per_profile"].values()), 13)
        self.assertEqual(summary["package_conformance"], {"portable.dna.package": True})
        self.assertEqual(len({profile.profile_id for profile in profiles}), 8)


if __name__ == "__main__":
    unittest.main()
