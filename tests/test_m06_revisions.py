from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError


from iris_production_state.enums import AvailabilityState, IntegrityState
from iris_production_state.errors import ProductionStateAdmissionError, ProductionStateIntegrityError
from iris_production_state.invariants import M06_INVARIANTS
from iris_production_state.revisions import (
    AvailabilityReceipt,
    ContentDigest,
    IntegrityReceipt,
    OperationalRevisionRef,
    RevisionManifest,
    digest_bytes,
    validate_master_admission,
    verify_digest,
)
from iris_production_state.validation import validate_master

from m06_support import content_digest, external, master_manifest, materialization, operational_revision, semantic_revision


class M06RevisionMasterTests(unittest.TestCase):
    def test_s01_revision_master_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S01"), tuple(range(1, 31)))
        revision = operational_revision("op-s01")
        manifest, integrity = master_manifest(revision)
        self.assertIs(validate_master(manifest, m02_admission_ref=manifest.m02_admission_ref, quality_evidence_ref=manifest.quality_evidence_ref, integrity_receipts=(integrity,)), manifest)

    def test_family_rvf(self) -> None:
        source = semantic_revision("asset-rvf", "semantic-rvf")
        ref = OperationalRevisionRef("operational-rvf", source)
        record = RevisionManifest(ref, source, content_digest(), (source,), metadata={"facet": "image"})
        self.assertEqual(record.revision_ref.source_revision_ref, record.semantic_ref)
        with self.assertRaises(FrozenInstanceError):
            ref.revision_id = "rewritten"
        with self.assertRaises(ProductionStateIntegrityError):
            RevisionManifest(ref, semantic_revision("other", "other-r"), content_digest())

    def test_family_iml(self) -> None:
        revision = operational_revision("op-iml")
        manifest, integrity = master_manifest(revision, master_id="master-iml")
        self.assertIs(validate_master_admission(manifest, m02_admission_ref=manifest.m02_admission_ref, quality_evidence_ref=manifest.quality_evidence_ref, integrity_receipts=(integrity,)), manifest)
        with self.assertRaises(ProductionStateAdmissionError):
            validate_master_admission(manifest, m02_admission_ref=manifest.m02_admission_ref, quality_evidence_ref=manifest.quality_evidence_ref, integrity_receipts=())
        with self.assertRaises(ProductionStateAdmissionError):
            validate_master_admission(manifest, m02_admission_ref=external("wrong-m02-admission"), quality_evidence_ref=manifest.quality_evidence_ref, integrity_receipts=(integrity,))

    def test_family_das(self) -> None:
        payload = b"digest-agility"
        for algorithm in ("sha256", "sha512", "blake2b-256"):
            digest = digest_bytes(payload, algorithm, algorithm_version="1.0.0")
            self.assertTrue(verify_digest(payload, digest))
        future = ContentDigest("future-hash", "2.1.0", "opaque-provider-value")
        with self.assertRaises(ProductionStateAdmissionError):
            verify_digest(payload, future)
        unknown_version = ContentDigest("sha256", "2.0.0", "a" * 64)
        with self.assertRaises(ProductionStateAdmissionError):
            verify_digest(payload, unknown_version)

    def test_family_sea(self) -> None:
        shared = "a" * 64
        first = semantic_revision("artifact-one", "revision-one", shared)
        second = semantic_revision("artifact-two", "revision-two", shared)
        left = OperationalRevisionRef("op-one", first)
        right = OperationalRevisionRef("op-two", second)
        self.assertEqual(content_digest().algorithm, "sha256")
        self.assertNotEqual(left, right)
        self.assertNotEqual(materialization(left, "mat-one"), materialization(right, "mat-two"))

    def test_family_avs(self) -> None:
        revision = operational_revision("op-avs")
        material = materialization(revision, "mat-avs")
        verified = IntegrityReceipt(material, material.content_digest, IntegrityState.VERIFIED, 1)
        available = AvailabilityReceipt(material, AvailabilityState.KNOWN_AVAILABLE, verified, 1)
        self.assertEqual(available.state, AvailabilityState.KNOWN_AVAILABLE)
        for state in (AvailabilityState.KNOWN_MISSING, AvailabilityState.UNKNOWN, AvailabilityState.CORRUPT, AvailabilityState.POLICY_BLOCKED):
            with self.subTest(state=state):
                receipt = AvailabilityReceipt(material, state, None, 2)
                self.assertEqual(receipt.state, state)
        with self.assertRaises(ProductionStateAdmissionError):
            AvailabilityReceipt(material, AvailabilityState.KNOWN_AVAILABLE, None, 2)
        with self.assertRaises(ProductionStateIntegrityError):
            IntegrityReceipt(material, content_digest(b"different"), IntegrityState.VERIFIED, 2)


if __name__ == "__main__":
    unittest.main()
