"""Twenty-four deterministic original-source M14 FTR documentary regressions. No models/runtime."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.verify_m14_ftr import (
    ROOT, REPORT, FLAG_KEYS, M14FTRIntegrityError, mock_owner_claims,
    no_duplicate_keys, read_json, render_report, verify, verify_all
)

class M14FTRDocumentaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = read_json(ROOT)

    def fresh(self):
        return deepcopy(self.packet)

    def check(self, p=None, human=False):
        return verify(self.packet if p is None else p, ROOT, check_human=human)

    def test_01_exact_original_sources_and_report(self):
        self.assertEqual(verify_all(ROOT)["originalSourceRolesVerified"],15)

    def test_02_original_five_sessions(self):
        self.assertEqual(self.check()["originalSessionsVerified"],5)

    def test_03_original_open_questions(self):
        self.assertEqual(self.check()["originalOwnerQuestionsOpen"],100)

    def test_04_original_hypothetical_negative_designs(self):
        self.assertEqual(self.check()["originalFutureNegativesNotExecuted"],80)

    def test_05_twenty_original_alternatives_not_selected(self):
        self.assertEqual(self.check()["originalAlternativesUnselected"],20)

    def test_06_five_nonadopting_technology_families(self):
        self.assertEqual(self.check()["unselectedFamilies"],5)

    def test_07_seven_future_cross_session_threats(self):
        self.assertEqual(self.check()["unexecutedCrossSessionHazards"],7)

    def test_08_twelve_missing_qualified_owner_gates(self):
        self.assertEqual(self.check()["missingRealOwnerProofGates"],12)

    def test_09_m13_pending_and_owner_stop_unmodified(self):
        p=self.packet
        self.assertEqual((p["originalM13QuestionsOpen"],p["originalM13FutureNegativesNotExecuted"]),(96,74))
        self.assertEqual(p["moduleContract"],"NOT_FROZEN")
        self.assertEqual(p["registryRuntime"],"NOT_ADMITTED")

    def test_10_original_git_sha_forgery(self):
        p=self.fresh();p["sourceDocs"][0]["gitBlobSha1"]="0"*40
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_11_original_text_needle_forgery(self):
        p=self.fresh();p["sourceDocs"][1]["exactNeedle"]="fabricated original M14 owner approval"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_12_original_packet_sha_forgery(self):
        p=self.fresh();p["sessions"][0]["gitBlobSha1"]="f"*40
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_13_missing_original_file_typed_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(M14FTRIntegrityError,"original source unreadable: INDEX"):
                verify(self.fresh(),Path(d),check_human=False)

    def test_14_non_utf8_source_typed_error(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"planning/MASTER-MODULE-INDEX-CURRENT.md"
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes(b"\xff broken utf8")
            with self.assertRaisesRegex(M14FTRIntegrityError,"original source unreadable: INDEX"):
                verify(self.fresh(),Path(d),check_human=False)

    def test_15_original_open_question_id_forgery(self):
        p=self.fresh();p["sessions"][2]["ownerQuestions"][0]="M14-S03-FAKE"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_16_original_unexecuted_case_id_forgery(self):
        p=self.fresh();p["sessions"][4]["futureNegativeIds"][0]="M14-S05-N999"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_17_original_alternative_forgery(self):
        p=self.fresh();p["sessions"][1]["originalAlternatives"][0]="AUTO_SELECTED"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_18_selected_research_family_refused(self):
        p=self.fresh();p["families"][0]["status"]="SELECTED"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_19_invalid_cross_session_source_refused(self):
        p=self.fresh();p["seams"][0]["originalNegativeIds"][0]="M14-S05-N01"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_20_forged_executed_cross_session_hazard_refused(self):
        p=self.fresh();p["seams"][0]["executed"]=True
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_21_forged_qualified_owner_gate_refused(self):
        p=self.fresh();p["gates"][0]["status"]="ORIGINAL_OWNER_APPROVED"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_21b_every_gate_requires_actual_named_proof_issuers(self):
        # Protect ALL twelve independent gate signatures, even if a broad
        # ownerRoutes list is otherwise long enough to satisfy generic checks.
        from scripts.verify_m14_ftr import REQUIRED_GATE_OWNERS
        self.assertEqual(set(REQUIRED_GATE_OWNERS),{g["id"] for g in self.packet["gates"]})
        for gate in self.packet["gates"]:
            for required_owner in REQUIRED_GATE_OWNERS[gate["id"]]:
                with self.subTest(gate=gate["id"],required_owner=required_owner):
                    self.assertIn(required_owner,gate["ownerRoutes"])
                    p=self.fresh()
                    target=next(g for g in p["gates"] if g["id"]==gate["id"])
                    target["ownerRoutes"].remove(required_owner)
                    with self.assertRaises(M14FTRIntegrityError):
                        self.check(p)

    def test_22_fake_owner_rights_measurements_and_runtime_refused(self):
        for field,value in (
           ("ownerApproval","APPROVED"),("independentTechnologyAdoption","APPROVED"),
           ("moduleContract","FROZEN"),("selectedTechnology","PROVIDER_X"),
           ("realRightsApprovals",1),("realModelMeasurements",1),
           ("realLifecycleEvents",1),("registryRuntime","ADMITTED"),
           ("nativeRuntime","ADMITTED")):
            with self.subTest(field=field):
                p=self.fresh();p[field]=value
                with self.assertRaises(M14FTRIntegrityError):self.check(p)

    def test_23_mock_all_true_never_implies_real_approval(self):
        result=mock_owner_claims({key:True for key in FLAG_KEYS})
        self.assertEqual(result["uncheckedMock"],[])
        self.assertFalse(any(result[x] for x in (
           "qualifiedIndependentReview","m14Frozen","technologySelected",
           "realTenantRights","realHardwareFit","runtimeAdmitted")))

    def test_24_exact_human_json_duplicates_and_nested_typed_fail_closed(self):
        self.assertEqual((ROOT/REPORT).read_text(encoding="utf-8"),render_report(self.packet))
        p=self.fresh();p["families"][0]["scope"]+=" changed without matching human report."
        with self.assertRaisesRegex(M14FTRIntegrityError,"human M14 FTR"):
            self.check(p,human=True)
        with self.assertRaisesRegex(M14FTRIntegrityError,"duplicate machine JSON key"):
            no_duplicate_keys([("ownerApproval","NONE"),("ownerApproval","APPROVED")])
        for collection in ("sourceDocs","sessions","families","seams","gates"):
            for bad in (["non-object"],{"not":"a list"}):
                with self.subTest(collection=collection,bad=str(bad)):
                    p=self.fresh();p[collection]=bad
                    with self.assertRaises(M14FTRIntegrityError):self.check(p)
        for collection,key,bad in (
          ("sourceDocs","path",None),("sessions","ownerQuestions",[{}]),
          ("sessions","originalAlternatives",[{}]),
          ("families","scope",None),("families","originalOwnerRoutes",[{}]),
          ("seams","joins",[{},"S02"]),("seams","originalNegativeIds",[{},"M14-S02-N01"]),
          ("gates","missingActualEvidence",None),("gates","ownerRoutes",[{}])):
            with self.subTest(collection=collection,key=key):
                p=self.fresh();p[collection][0][key]=bad
                with self.assertRaises(M14FTRIntegrityError):self.check(p)
        p=self.fresh();p["stop"]="ALL REQUIREMENTS APPROVED"
        with self.assertRaises(M14FTRIntegrityError):self.check(p)

if __name__ == "__main__":
    unittest.main()
