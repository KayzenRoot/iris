"""WO0051 original 47-module full index documentary scan regression tests."""
from __future__ import annotations
from copy import deepcopy
import unittest
from scripts.verify_m14_m60_fcs import (
    ROOT, REPORT, FCSIntegrityError, read_packet, mock_compatibility_evidence,
    validate, verify_all,
)

class M14M60DocumentaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = read_packet()

    def audit(self, value=None, *, human=False, md=None):
        return validate(self.p if value is None else value, ROOT,
                        check_human=human, human_text=md)

    def test_01_all_47_exact_original_modules_and_full_human_packet(self):
        self.assertEqual(verify_all()["originalModules"], 47)

    def test_02_all_235_original_module_sessions_source_exact(self):
        self.assertEqual(self.audit()["exactOriginalModuleSessions"], 235)

    def test_03_47_module_specific_unqualified_actual_owner_routes(self):
        self.assertEqual(self.audit()["sourceSpecificUnqualifiedActualOwnerRoutes"], 47)

    def test_04_ten_unexecuted_original_cross_area_interlocks(self):
        self.assertEqual(self.audit()["newCrossAreaUnexecutedInterlocks"], 10)

    def test_05_original_m13_96_questions_still_open(self):
        self.assertEqual(self.audit()["previousM13OpenQuestions"], 96)

    def test_06_original_m13_74_negative_cases_not_executed(self):
        self.assertEqual(self.audit()["previousFutureNegativesNotExecuted"], 74)

    def test_07_zero_owner_approval_and_no_runtime(self):
        report = self.audit()
        self.assertFalse(report["independentFCSApproval"])
        self.assertFalse(report["m13Frozen"])
        self.assertEqual(report["qualifiedRealOwners"], 0)
        self.assertEqual(report["runtime"], "NOT_ADMITTED")

    def test_08_original_index_git_blob_tamper_rejected(self):
        q = deepcopy(self.p); q["masterIndex"]["gitBlobSha1"] = "0"*40
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_09_original_ftr_git_blob_tamper_rejected(self):
        q = deepcopy(self.p); q["sourceFTR"]["gitBlobSha1"] = "0"*40
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_10_missing_47th_module_rejected(self):
        q = deepcopy(self.p); q["modules"].pop()
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_11_swapped_original_module_name_rejected(self):
        q = deepcopy(self.p); q["modules"][0]["title"] = "GPU Autonomous Owner"
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_12_missing_original_5th_subsession_rejected(self):
        q = deepcopy(self.p); q["modules"][12]["originalSessions"].pop()
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_13_source_area_reassignment_rejected(self):
        q = deepcopy(self.p); q["modules"][24]["area"] = "AREA UNKNOWN"
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_14_unsupported_m13_technology_family_rejected(self):
        q = deepcopy(self.p)
        q["modules"][0]["candidateM13Families"] = ["CUDA_ADOPTED"]
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_15_fake_approved_actual_module_contract_rejected(self):
        q = deepcopy(self.p)
        q["modules"][0]["currentOwnModuleSourceContract"] = "FROZEN"
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_16_fake_real_owner_signature_rejected(self):
        q = deepcopy(self.p); q["modules"][0]["ownerApproval"] = "SIGNED"
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_17_future_negative_claim_executed_rejected(self):
        q = deepcopy(self.p); q["modules"][0]["futureNegativeStatus"] = "PASS"
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_18_original_cross_area_module_route_changed_rejected(self):
        q = deepcopy(self.p); q["interlocks"][0]["indexModuleIds"].pop()
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_19_original_cross_area_interlock_fake_executed_rejected(self):
        q = deepcopy(self.p); q["interlocks"][0]["status"] = "EXECUTED"
        with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_20_h01_h04_owner_b_c01_and_runtime_cannot_advance(self):
        for k, value in (
            ("h01h02h03h04", "CLOSED"), ("ownerB", "RUNTIME_APPROVED"),
            ("c01", "FROZEN"), ("runtime", "ADMITTED"),
            ("independentQualifiedFCSApproval", "APPROVED"),
            ("moduleContractFreeze", "FROZEN"),
            ("technologySelection", "FLASHATTENTION"),
        ):
            with self.subTest(key=k):
                q = deepcopy(self.p); q[k] = value
                with self.assertRaises(FCSIntegrityError): self.audit(q)

    def test_21_human_full_packet_machine_appendix_tamper_rejected(self):
        md = (ROOT / REPORT).read_text(encoding="utf-8")
        md = md.replace('"runtime": "NOT_ADMITTED"',
                        '"runtime": "ADMITTED"', 1)
        with self.assertRaises(FCSIntegrityError):
            self.audit(human=True, md=md)

    def test_22_fake_all_seven_owners_performance_rights_still_no_approval(self):
        flags = {k: True for k in (
            "originalIndex", "moduleOwnerProof", "sourceValidM08",
            "currentRights", "h01toH04", "securityOSAndStorage",
            "independentReviewer",
        )}
        a = mock_compatibility_evidence(flags)
        self.assertEqual(a["missingMock"], [])
        self.assertEqual(a["disposition"],
                         "INDEX_COVERAGE_ONLY_REAL_OWNERS_AND_INTEGRATION_PENDING")
        self.assertFalse(a["independentFCSApproved"])
        self.assertFalse(a["m13Approved"])
        self.assertFalse(a["runtimeAuthorized"])

    def test_23_missing_mock_actual_rights_is_still_non_authorizing(self):
        flags = {k: True for k in (
            "originalIndex", "moduleOwnerProof", "sourceValidM08",
            "currentRights", "h01toH04", "securityOSAndStorage",
            "independentReviewer",
        )}
        flags["currentRights"] = False
        a = mock_compatibility_evidence(flags)
        self.assertEqual(a["missingMock"], ["currentRights"])
        self.assertEqual(a["actualIntegrationTestsRun"], 0)
        self.assertFalse(a["runtimeAuthorized"])

    def test_24_invalid_or_missing_mock_boolean_rejected(self):
        flags = {k: True for k in (
            "originalIndex", "moduleOwnerProof", "sourceValidM08",
            "currentRights", "h01toH04", "securityOSAndStorage",
            "independentReviewer",
        )}
        flags["sourceValidM08"] = "valid"
        with self.assertRaises(FCSIntegrityError):
            mock_compatibility_evidence(flags)
        flags.pop("sourceValidM08")
        with self.assertRaises(FCSIntegrityError):
            mock_compatibility_evidence(flags)

if __name__ == "__main__":
    unittest.main()
