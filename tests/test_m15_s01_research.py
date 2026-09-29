"""Twenty WO0084 source-only M15 S01 original-owner and immutable-Git regressions."""
from __future__ import annotations
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.verify_context_lock import (
    ContextLockError, WO0084_LOCK, WO0084_ADDITIONAL_SOURCE_PATHS,
    WO0084_EXACT_CHANGED_PATHS, verify_lock,
)
from scripts.verify_m15_s01_research import (
    EXPECTED, M15S01IntegrityError, ROOT, REPORT,
    exactly_typed, git_blob, load, load_json, no_duplicate_keys,
    render_report, verify,
)

class M15S01OriginalSourceResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet=load(ROOT)

    def fresh(self):
        return deepcopy(self.packet)

    def check(self, p=None, *, root=ROOT, human=False):
        return verify(self.packet if p is None else p,root,check_human=human)

    def test_01_complete_exact_original_source_and_human(self):
        proof=self.check(human=True)
        self.assertEqual(proof["originalSourceRolesVerified"],15)
        self.assertFalse(proof["runtimeAllowed"])

    def test_02_fifteen_original_git_blob_and_text_roles(self):
        self.assertEqual(len(self.packet["sourceDocs"]),15)
        for row in self.packet["sourceDocs"]:
            with self.subTest(path=row["path"]):
                raw=(ROOT/row["path"]).read_bytes()
                self.assertEqual(git_blob(raw),row["gitBlobSha1"])
                self.assertIn(row["exactNeedle"],raw.decode("utf-8"))

    def test_03_original_m13_m14_historical_stop_counts(self):
        proof=self.check()
        self.assertEqual((proof["originalM14OpenQuestions"],proof["originalM14UnexecutedCases"]),(100,80))
        self.assertEqual((proof["historicM13OpenQuestions"],proof["historicM13UnexecutedCases"]),(96,74))

    def test_04_sixteen_new_owner_questions_all_open_unrated(self):
        proof=self.check()
        self.assertEqual(proof["newM15OpenQuestions"],16)
        self.assertEqual({x["status"] for x in self.packet["questions"]},
                         {"OPEN_UNRATED_PENDING_QUALIFIED_OWNER"})

    def test_05_twelve_new_unexecuted_original_future_designs(self):
        self.assertEqual(self.check()["newM15FutureUnexecutedCases"],12)
        self.assertTrue(all(x["executed"] is False for x in self.packet["negativeScenarios"]))

    def test_06_four_original_unselected_affinity_alternatives(self):
        self.assertEqual(self.check()["unselectedAlternatives"],4)
        self.assertTrue(all(x["selected"] is False for x in self.packet["alternatives"]))

    def test_07_six_dimensions_have_no_empirical_or_routing_grant(self):
        self.assertEqual(self.check()["unobservedAffinityDimensions"],6)
        self.assertTrue(all(x["routingGranted"] is False for x in self.packet["affinityDimensions"]))

    def test_08_all_original_owner_question_issuer_routes_are_explicit(self):
        for row in self.packet["questions"]:
            with self.subTest(question=row["id"]):
                self.assertEqual(row["requiredOriginalIssuers"][0],"M15")
                self.assertEqual(len(set(row["requiredOriginalIssuers"])),
                                 len(row["requiredOriginalIssuers"]))

    def test_09_positive_owner_license_rank_runtime_claims_refused(self):
        forged=[
            ("qualifiedOriginalOwner","APPROVED"),("ownerContract","FROZEN"),
            ("technologySelected","MODEL"),("modelRankSelected","WINNER"),
            ("modelRuntime","RUNNING"),("actualTenantLicenseRights","APPROVED"),
            ("realHostBenchmarks",1),("executedNegativeCases",12),
            ("approvedOriginalOwnerProofGates",12),("m10","EXECUTE"),
            ("m11m12m13","NATIVE_RUNTIME_ADMITTED"),
        ]
        for key,value in forged:
            with self.subTest(key=key):
                p=self.fresh();p[key]=value
                with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_10_bool_numeric_substitutions_cannot_pass_recursive_type_check(self):
        self.assertTrue(exactly_typed(self.packet,EXPECTED))
        for key,bad in (("approvedOriginalOwnerProofGates",False),
                        ("realHostBenchmarks",False),("executedNegativeCases",False)):
            with self.subTest(key=key):
                p=self.fresh();p[key]=bad
                with self.assertRaises(M15S01IntegrityError):self.check(p)
        p=self.fresh();p["alternatives"][0]["selected"]=0
        with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_11_forged_original_role_blob_rejected(self):
        p=self.fresh();p["sourceDocs"][0]["gitBlobSha1"]="0"*40
        with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_12_forged_original_role_text_rejected(self):
        p=self.fresh();p["sourceDocs"][0]["exactNeedle"]="fake new M15 original owner approval"
        with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_13_original_question_id_reassignment_rejected(self):
        p=self.fresh();p["questions"][0]["id"]="M15-S01-Q99"
        with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_14_missing_original_required_issuer_or_forged_answer_rejected(self):
        for key,value in (("requiredOriginalIssuers",["M15"]),("ownerAnswer","YES"),
                          ("risk","LOW"),("status","APPROVED")):
            with self.subTest(field=key):
                p=self.fresh();p["questions"][3][key]=value
                with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_15_negative_future_cases_execution_or_fake_association_rejected(self):
        for key,value in (("status","EXECUTED"),("executed",True),
                          ("relatedOriginalQuestionIds",["M15-S01-Q99"])):
            with self.subTest(field=key):
                p=self.fresh();p["negativeScenarios"][0][key]=value
                with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_16_unselected_alternative_forged_selection_refused(self):
        p=self.fresh();p["alternatives"][0]["selected"]=True
        with self.assertRaises(M15S01IntegrityError):self.check(p)
        p=self.fresh();p["alternatives"].pop()
        with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_17_affinity_dimension_forged_observation_and_route_refused(self):
        for key,value in (("currentQualifiedObservation","MEASURED"),("routingGranted",True)):
            with self.subTest(field=key):
                p=self.fresh();p["affinityDimensions"][0][key]=value
                with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_18_exact_machine_human_projection_and_stop_refusal(self):
        self.assertEqual((ROOT/REPORT).read_text(encoding="utf-8"),
                         render_report(self.packet))
        p=self.fresh();p["stop"]="APPROVED FOR LIVE MODEL ROUTING"
        with self.assertRaises(M15S01IntegrityError):self.check(p)
        p=self.fresh();p["sourceDocs"].reverse()
        with self.assertRaises(M15S01IntegrityError):self.check(p)

    def test_19_typed_missing_malformed_and_duplicate_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaises(M15S01IntegrityError):self.check(root=root)
            malformed=root/"source.json"
            malformed.write_text('{"questions": [}',encoding="utf-8")
            with self.assertRaises(M15S01IntegrityError):load_json(malformed)
            malformed.write_bytes(b"\xff")
            with self.assertRaises(M15S01IntegrityError):load_json(malformed)
            malformed.write_text("[]",encoding="utf-8")
            with self.assertRaises(M15S01IntegrityError):load_json(malformed)
        with self.assertRaisesRegex(M15S01IntegrityError,"duplicate original JSON key"):
            no_duplicate_keys([("ownerAnswer",None),("ownerAnswer","APPROVED")])

    def test_20_wo0084_fixed_77_original_source_and_14_diff_fail_closed(self):
        previous=load_json(ROOT/".engineering/context-locks/IRIS-WO-0083-M14-INDEPENDENT-DOCUMENTARY-AUDIT.json")
        submitted=load_json(ROOT/WO0084_LOCK)
        inherited={x["path"] for x in previous["criticalSources"]}
        base_blobs={x["path"]:x["gitBlobSha1"] for x in submitted["criticalSources"]}
        base_modes={path:"100644" for path in base_blobs}
        self.assertEqual((len(inherited),len(WO0084_ADDITIONAL_SOURCE_PATHS),
                          len(WO0084_EXACT_CHANGED_PATHS)),(72,5,14))
        def check_scope(proposal, *, changed=None, blobs=None):
            actual_blobs=base_blobs if blobs is None else blobs
            verify_lock(proposal,base_sha=EXPECTED["sourceBaseSha"],
                base_tree_sha=EXPECTED["sourceBaseTreeSha"],base_blobs=actual_blobs,
                base_modes={path:"100644" for path in actual_blobs},
                changed_paths=set(WO0084_EXACT_CHANGED_PATHS) if changed is None else changed,
                lock_path=WO0084_LOCK,inherited_source_paths=inherited)
        check_scope(submitted)
        # Preserve count and mode while replacing an actual nonmandatory original.
        forged=deepcopy(submitted)
        displaced="planning/reviews/M14-FTR-INDEPENDENT-DOCUMENTARY-AUDIT.md"
        fake="planning/reviews/FAKE-QUALIFIED-OWNER-FTR.md"
        row=next(x for x in forged["criticalSources"] if x["path"]==displaced)
        row["path"]=fake
        with self.assertRaisesRegex(ContextLockError,"fixed 77-original-source-path membership"):
            check_scope(forged,blobs={**base_blobs,fake:row["gitBlobSha1"]})
        added=deepcopy(submitted)
        other="planning/reviews/FAKE-M15-OWNER-RECEIPT.md"
        added["authorizedChangedFiles"].append(other)
        with self.assertRaisesRegex(ContextLockError,"fixed exact 14 authorized"):
            check_scope(added,changed=set(WO0084_EXACT_CHANGED_PATHS)|{other})
        removed=deepcopy(submitted)
        missing="planning/reviews/IRIS-WO-0084-BOUNDED-AUDIT-TARGET.md"
        removed["authorizedChangedFiles"].remove(missing)
        with self.assertRaisesRegex(ContextLockError,"fixed exact 14 authorized"):
            check_scope(removed,changed=set(WO0084_EXACT_CHANGED_PATHS)-{missing})
        with self.assertRaisesRegex(ContextLockError,"actual Git diff differs"):
            check_scope(submitted,changed=set(WO0084_EXACT_CHANGED_PATHS)-{missing})
        badOwner=deepcopy(submitted);badOwner["issue"]=204
        with self.assertRaises(ContextLockError):check_scope(badOwner)

if __name__=="__main__":
    unittest.main()
