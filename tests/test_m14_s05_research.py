"""IRIS-WO-0080: 24 strictly offline original-source S05 lifecycle integrity regressions."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.verify_m14_s05_research import (
    ROOT, REPORT, M14S05IntegrityError, read_json, render_report,
    unique_json_keys, verify_packet, verify_all
)

class M14S05SourceResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = read_json(ROOT)

    def cp(self):
        return deepcopy(self.packet)

    def audit(self, p=None, *, markdown=False):
        return verify_packet(self.packet if p is None else p, ROOT, verify_markdown=markdown)

    def test_01_exact_original_source_and_human_projection(self):
        self.assertEqual(verify_all(ROOT)["originalSourcePinsVerified"], 20)

    def test_02_twenty_original_source_roles(self):
        self.assertEqual(self.audit()["originalSourcePinsVerified"], 20)

    def test_03_eight_lifecycle_facets_nonadopted(self):
        self.assertEqual(self.audit()["nonadoptedFacets"], 8)

    def test_04_five_states_are_only_vocabulary(self):
        self.assertEqual(self.audit()["futureEvidenceLabelsOnly"], 5)

    def test_05_four_alternatives_unselected(self):
        self.assertEqual(self.audit()["unselectedAlternatives"], 4)

    def test_06_twenty_four_owner_questions_open(self):
        self.assertEqual(self.audit()["newOpenOwnerQuestions"], 24)
        self.assertTrue(all(x["risk"] == "UNRATED" and x["ownerAnswer"] is None
                            for x in self.packet["questions"]))

    def test_07_twenty_future_hostile_designs_not_executed(self):
        self.assertEqual(self.audit()["futureNegativesNotExecuted"], 20)

    def test_08_all_prior_pending_owner_counts_unchanged(self):
        p=self.packet
        self.assertEqual(tuple(p[k] for k in ("priorS01QuestionsOpen","priorS01FutureCases",
            "priorS02QuestionsOpen","priorS02FutureCases","priorS03QuestionsOpen","priorS03FutureCases",
            "priorS04QuestionsOpen","priorS04FutureCases","priorM13QuestionsOpen","priorM13FutureCases")),
            (16,12,18,14,20,16,22,18,96,74))

    def test_09_zero_real_lifecycle_and_runtime_events(self):
        self.assertEqual(self.audit()["realLifecycleObservations"], 0)
        self.assertFalse(self.packet["registryRuntimeAdmitted"])

    def test_10_corrupted_original_blob_sha_rejected(self):
        p=self.cp();p["sourceDocs"][0]["gitBlobSha1"]="0"*40
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_11_forged_original_text_anchor_rejected(self):
        p=self.cp();p["sourceDocs"][1]["exactNeedle"]="fabricated accepted owner approval"
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_12_missing_original_source_has_typed_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(M14S05IntegrityError,"original source unreadable: INDEX") as ctx:
                verify_packet(self.cp(),Path(d),verify_markdown=False)
            self.assertIsInstance(ctx.exception.__cause__,FileNotFoundError)

    def test_13_nonutf8_original_source_has_typed_error(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"planning/MASTER-MODULE-INDEX-CURRENT.md"
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b"\xff broken utf8")
            with self.assertRaisesRegex(M14S05IntegrityError,"original source unreadable: INDEX") as ctx:
                verify_packet(self.cp(),Path(d),verify_markdown=False)
            self.assertIsInstance(ctx.exception.__cause__,UnicodeDecodeError)

    def test_14_truncated_lifecycle_caveat_rejected(self):
        p=self.cp();p["facets"][0]["caveat"]="supported"
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_15_future_lifecycle_label_cannot_claim_real(self):
        p=self.cp();p["states"][0]["status"]="OBSERVED_OWNER_SIGNED"
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_16_selected_or_truncated_alternative_rejected(self):
        for key,value in (("selected",True),("tradeoffs","not enough")):
            with self.subTest(key=key):
                p=self.cp();p["alternatives"][0][key]=value
                with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_17_missing_owner_question_rejected(self):
        p=self.cp();p["questions"].pop()
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_18_forged_owner_answer_rejected(self):
        p=self.cp();p["questions"][0]["ownerAnswer"]="signed"
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_19_forged_risk_rank_rejected(self):
        p=self.cp();p["questions"][0]["risk"]="LOW"
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_20_unadmitted_registry_authority_rejected(self):
        p=self.cp();p["questions"][0]["executionAuthority"]="REGISTRY_RUN_ALLOWED"
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_21_false_real_lifecycle_transition_rejected(self):
        p=self.cp();p["negativeScenarios"][0]["status"]="OBSERVED_REVOCATION_PASS"
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_22_nonlocal_owner_question_reference_rejected(self):
        p=self.cp();p["negativeScenarios"][0]["questionIds"]=["M14-S04-U01"]
        with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_23_fake_lifecycle_receipts_or_owner_rights_rejected(self):
        for field,value in (("observedModelDriftEvents",1),("realLifecycleTransitions",1),
            ("realRevocationActions",1),("realProviderTests",1),("realGpuBenchmarks",1),
            ("ownerApproval","APPROVED"),("lifecycleContractAdopted",True),
            ("registryRuntimeAdmitted",True)):
            with self.subTest(field=field):
                p=self.cp();p[field]=value
                with self.assertRaises(M14S05IntegrityError):self.audit(p)

    def test_24_exact_report_duplicates_and_nested_typed_failures(self):
        self.assertEqual((ROOT/REPORT).read_text(encoding="utf-8"),render_report(self.packet))
        p=self.cp();p["questions"][0]["question"]+=" altered report only."
        with self.assertRaisesRegex(M14S05IntegrityError,"human S05 report"):self.audit(p,markdown=True)
        with self.assertRaisesRegex(M14S05IntegrityError,"duplicate JSON key"):
            unique_json_keys([("ownerApproval","NONE"),("ownerApproval","APPROVED")])
        for field in ("facets","states","alternatives","questions","negativeScenarios"):
            for malformed in (["not a dict"],{"id":"not a list"}):
                with self.subTest(field=field,malformed=str(malformed)):
                    p=self.cp();p[field]=malformed
                    with self.assertRaises(M14S05IntegrityError):self.audit(p)
        for field,key,bad in (("facets","title",None),("facets","caveat",None),
            ("alternatives","title",None),("alternatives","tradeoffs",None),
            ("questions","question",None),("questions","sourceRoles",[{},"INDEX"]),
            ("negativeScenarios","trigger",None),("negativeScenarios","questionIds",[{}])):
            with self.subTest(field=field,key=key):
                p=self.cp();p[field][0][key]=bad
                with self.assertRaises(M14S05IntegrityError):self.audit(p)

if __name__ == "__main__":
    unittest.main()
