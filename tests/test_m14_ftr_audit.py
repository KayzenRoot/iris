"""Twenty fail-closed immutable-source WO0083 documentary audit regressions, offline only."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.verify_m14_ftr_audit import (
    ROOT, REPORT, REQUIRED, M14AuditIntegrityError, load, mock_positive_checkboxes,
    no_duplicate_keys, render_report, verify, load_json,
)

class M14FTRIndependentDocumentaryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet=load(ROOT)

    def fresh(self):
        return deepcopy(self.packet)

    def check(self, p=None, *, human=False, root=ROOT):
        return verify(self.packet if p is None else p,root,check_human=human)

    def test_01_complete_exact_original_audit(self):
        self.assertFalse(self.check(human=True)["realOwnerOrRuntimeGrant"])

    def test_02_five_original_ftr_blobs(self):
        self.assertEqual(self.check()["sourceFtrOriginalBlobsVerified"],5)

    def test_03_fifteen_original_source_roles(self):
        self.assertEqual(self.check()["originalSourceRolePinsVerified"],15)

    def test_04_original_five_sessions(self):
        self.assertEqual(self.check()["originalSessions"],5)

    def test_05_exact_original_100_open_and_80_unexecuted(self):
        proof=self.check()
        self.assertEqual((proof["originalOpenQuestions"],proof["unexecutedFutureCases"]),(100,80))

    def test_06_original_twenty_alternatives_unselected(self):
        self.assertEqual(self.check()["originalUnselectedAlternatives"],20)

    def test_07_families_seams_gates_remain_hypothetical(self):
        proof=self.check()
        self.assertEqual((proof["unselectedFtrFamilies"],proof["hypotheticalCrossSessionSeams"],
                          proof["unreceivedOwnerProofGates"]),(5,7,12))

    def test_08_original_eight_owner_issue_receipts_open(self):
        self.assertEqual(self.check()["openOriginalOwnerIssueReceiptsRecorded"],8)

    def test_09_all_favorable_mock_flags_never_grant(self):
        flags={key:True for key in ("gitPins","humanReport","allOwnerRoutes",
              "tenantClaims","hardwareClaims","externalReview")}
        proof=mock_positive_checkboxes(flags)
        self.assertEqual(proof["unchecked"],[])
        self.assertFalse(any(proof[k] for k in ("qualifiedOwner","technologyAdopted",
              "originalCasesExecuted","moduleFrozen","runtimeAllowed")))

    def test_10_forged_real_owner_module_rights_runtime_refused(self):
        for field,value in (("qualifiedM14OwnerReceipt","YES"),
           ("independentRealTechnologyAdoption","APPROVED"),
           ("realLicenseTenantRights","APPROVED"),("realHostBenchmarkCount",1),
           ("executedOriginalNegativeCount",80),("approvedGateCount",12),
           ("selectedTechnology","VENDOR"),("m14ModuleContract","FROZEN"),
           ("nativeRuntime","ADMITTED")):
            with self.subTest(field=field):
                p=self.fresh();p[field]=value
                with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_11_ftr_packet_original_sha_refusal(self):
        p=self.fresh();p["sourceFTR"]["packetSha"]="0"*40
        with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_12_ftr_human_report_original_sha_refusal(self):
        p=self.fresh();p["sourceFTR"]["reportSha"]="1"*40
        with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_13_original_session_blob_source_refusal(self):
        p=self.fresh();p["originalCaseRegister"][0]["blob"]="0"*40
        with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_14_forged_question_and_reassigned_future_id_refusal(self):
        for field,value in (("questionIds","M14-S01-U999"),
                            ("negativeIds","M14-S05-N01")):
            with self.subTest(field=field):
                p=self.fresh();p["originalCaseRegister"][0][field][0]=value
                with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_15_forged_original_alternative_selection_refusal(self):
        p=self.fresh();p["originalCaseRegister"][2]["originalAlternativeIds"][0]="APPROVED_PROVIDER"
        with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_16_hypothetical_cross_session_executed_refusal(self):
        p=self.fresh();p["sourceSeams"][0]["executed"]=True
        with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_17_every_required_original_proof_issuer_is_immutable(self):
        self.assertEqual(set(REQUIRED),{g["id"] for g in self.packet["gateAudit"]})
        for gate in self.packet["gateAudit"]:
            for issuer in REQUIRED[gate["id"]]:
                with self.subTest(gate=gate["id"],owner=issuer):
                    self.assertIn(issuer,gate["documentaryReviewRoutes"])
                    p=self.fresh()
                    row=next(x for x in p["gateAudit"] if x["id"]==gate["id"])
                    row["documentaryReviewRoutes"].remove(issuer)
                    with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_18_owner_gate_receipt_or_closed_issue_forgery(self):
        for field,value in (("ownerIssuedReceipt","FAKE_OWNER_SIGNATURE"),
                            ("status","ORIGINAL_OWNER_APPROVED"),("admission",True)):
            with self.subTest(field=field):
                p=self.fresh();p["gateAudit"][0][field]=value
                with self.assertRaises(M14AuditIntegrityError):self.check(p)
        p=self.fresh();p["unresolvedOriginalOwnerIssues"][0]["status"]="CLOSED"
        with self.assertRaises(M14AuditIntegrityError):self.check(p)

    def test_19_missing_and_non_utf8_immutable_source_refusal(self):
        # A corrupt top-level audit JSON must use the same typed integrity error
        # instead of leaking JSONDecodeError to callers.
        with tempfile.TemporaryDirectory() as d:
            malformed=Path(d)/"invalid-audit.json"
            malformed.write_text('{"originalCaseRegister": [}',encoding="utf-8")
            with self.assertRaisesRegex(M14AuditIntegrityError,"original source unreadable"):
                load_json(malformed)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(M14AuditIntegrityError,"original FTR source missing"):
                self.check(root=Path(d))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            original=self.packet["sourceFTR"]
            for key in ("packet","report","verifier","originalTests","originalManifest"):
                path=root/original[key+"Path"]
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b"\xffinvalidUTF8")
            with self.assertRaises(M14AuditIntegrityError):
                self.check(root=root)

    def test_20_machine_human_duplicate_json_and_nested_collection_refusals(self):
        self.assertEqual((ROOT/REPORT).read_text(encoding="utf-8"),render_report(self.packet))
        p=self.fresh();p["originalCaseRegister"][0]["ownerStatus"]+=" changed"
        with self.assertRaises(M14AuditIntegrityError):self.check(p)
        p=self.fresh();p["sourceFamilyIds"]=p["sourceFamilyIds"][:-1]
        with self.assertRaises(M14AuditIntegrityError):self.check(p)
        with self.assertRaisesRegex(M14AuditIntegrityError,"duplicate original-source JSON key"):
            no_duplicate_keys([("ownerReceipt","NONE"),("ownerReceipt","APPROVED")])
        for coll in ("sourceFTR","originalCaseRegister","sourceFamilyIds","sourceSeams",
                     "gateAudit","unresolvedOriginalOwnerIssues"):
            with self.subTest(collection=coll):
                p=self.fresh();p[coll]="corrupted"
                with self.assertRaises(M14AuditIntegrityError):self.check(p)
        # Each nested collection is validated before accessing row.get.
        for collection in ("sourceSeams","gateAudit","unresolvedOriginalOwnerIssues"):
            for bad in (None,"not a row",[],42):
                with self.subTest(collection=collection,invalid_row=str(bad)):
                    p=self.fresh();p[collection][0]=bad
                    with self.assertRaises(M14AuditIntegrityError):self.check(p)
        p=self.fresh();p["stop"]="ALL PROOFS APPROVED"
        with self.assertRaises(M14AuditIntegrityError):self.check(p)

if __name__=="__main__":
    unittest.main()
