"""WO0039: untrusted offline owner draft triage, NOT actual owner or OS proof."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.triage_m09_h03_untrusted_owner_reply import (
    ALWAYS_PENDING,DISPOSITIONS,MODULE_ISSUES,REQUIRED,REPORT_STATUSES,
    ROOT,ROUTES,PRIOR,SCHEMA,UntrustedReplyError,read_draft,read,triage,
    triage_verified_checkout,
)


class H03UntrustedOwnerReplyTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes=read(ROOT,ROUTES)
        cls.packets=read(ROOT,PRIOR)

    def candidate(self,module="M54",count=2):
        p=next(x for x in self.packets["sourceOwners"] if x["module"]==module)
        ids=[x["id"] for x in p["questions"]][:count]
        return {
            "schemaVersion":SCHEMA,
            "module":module,"issue":MODULE_ISSUES[module],
            "sourceCommit":"a"*40,
            "sourcePath":f"planning/contracts/{module}-DRAFT-NOT-APPROVED.md",
            "selfClaimedOwner":"synthetic-unverified-author",
            "selfClaimedReviewUrl":"https://github.com/KayzenRoot/iris/pull/999",
            "scopeAndExclusions":{
                "scope":"synthetic claimed subset to review",
                "exclusions":"no live permission and no runtime",
            },
            "questionDispositions":[
                {"questionId":x,"decision":"DEFER",
                 "rationale":"Synthetic open source-owner disposition only"}
                for x in ids
            ],
        }

    def inspect(self,c):
        return triage(c,self.packets,self.routes)

    def rejects(self,c):
        with self.assertRaises(UntrustedReplyError):
            self.inspect(c)

    def test_01_real_repository_source_and_prior_verifier_qualify(self):
        p=triage_verified_checkout(self.candidate())
        self.assertEqual(p["formatStatus"],"PARTIAL_DRAFT_FORMAT_ONLY")
        self.assertFalse(p["actualApprovedContract"])

    def test_02_each_owner_is_routed_to_exact_source_issue(self):
        for module,issue in MODULE_ISSUES.items():
            with self.subTest(owner=module):
                result=self.inspect(self.candidate(module,1))
                self.assertEqual(result["reviewIssue"],issue)
                self.assertEqual(result["submittedQuestionCount"],1)

    def test_03_full_synthetic_four_owner_queues_never_sign_off(self):
        for module,issue in MODULE_ISSUES.items():
            with self.subTest(owner=module):
                c=self.candidate(module,count=1000)
                r=self.inspect(c)
                self.assertEqual(r["formatStatus"],"COMPLETE_DRAFT_FORMAT_ONLY")
                self.assertFalse(r["actualApprovedContract"])
                self.assertFalse(r["permissionToPlacePublishUseOsOrExecute"])

    def test_04_partial_synthetic_queue_is_never_full_coverage(self):
        r=self.inspect(self.candidate("M54",2))
        self.assertEqual(r["submittedQuestionCount"],2)
        self.assertEqual(r["expectedQuestionCount"],39)
        self.assertEqual(len(r["remainingQuestionIds"]),37)

    def test_05_source_git_sha_string_is_not_fetched(self):
        r=self.inspect(self.candidate())
        self.assertFalse(r["claimedSourceWasFetched"])
        self.assertIn("SOURCE_COMMIT_AND_PATH_NOT_FETCHED",r["mandatoryWarnings"])

    def test_06_fake_issuer_and_pr_url_are_never_authentication(self):
        r=self.inspect(self.candidate())
        self.assertFalse(r["claimedOwnerAuthenticated"])
        self.assertFalse(r["claimedReviewIndependentlyVerified"])
        self.assertIn("OWNER_IDENTITY_NOT_AUTHENTICATED",r["mandatoryWarnings"])

    def test_07_source_joint_owners_are_listed_but_never_approved(self):
        m54=next(p for p in self.packets["sourceOwners"] if p["module"]=="M54")
        m12=next(p for p in self.packets["sourceOwners"] if p["module"]=="M12")
        overlap=next(q["id"] for q in m54["questions"]
                     if q["id"] in {z["id"] for z in m12["questions"]})
        c=self.candidate("M54",0)
        c["questionDispositions"]=[{
            "questionId":overlap,"decision":"DEFER",
            "rationale":"Synthetic overlapping original source question",
        }]
        r=self.inspect(c)
        self.assertIn("M12",r["otherQuestionOwnersRequiringIndependentProof"])
        self.assertFalse(r["otherOwnerSignaturesVerified"])

    def test_08_correct_distinct_original_question_order_is_preserved(self):
        c=self.candidate("M54",3)
        c["questionDispositions"].reverse()
        r=self.inspect(c)
        self.assertEqual(r["sourceQuestionIds"],
                         self.routes["routes"][1]["sourceQuestionIds"][:3])

    def test_09_duplicate_question_disposition_rejected(self):
        c=self.candidate()
        c["questionDispositions"].append(deepcopy(c["questionDispositions"][0]))
        self.rejects(c)

    def test_10_foreign_owner_question_id_rejected(self):
        c=self.candidate("M54",1)
        m12=set(self.routes["routes"][0]["sourceQuestionIds"])
        m54=set(self.routes["routes"][1]["sourceQuestionIds"])
        c["questionDispositions"][0]["questionId"]=next(iter(m12-m54))
        self.rejects(c)

    def test_11_wrong_review_issue_cannot_sign_another_owner(self):
        c=self.candidate()
        c["issue"]=146
        self.rejects(c)

    def test_12_wrong_or_unknown_module_rejected(self):
        c=self.candidate()
        c["module"]="M57"
        self.rejects(c)
        c=self.candidate()
        c["module"]=["M54"]
        self.rejects(c)

    def test_13_schema_mismatch_is_rejected(self):
        c=self.candidate()
        c["schemaVersion"]="future-approved-contract-v1"
        self.rejects(c)

    def test_14_top_level_approved_or_runtime_field_rejected(self):
        for forbidden in ("approved","runtimeAdmitted","permissionGranted"):
            c=self.candidate()
            c[forbidden]=True
            self.rejects(c)

    def test_15_disposition_status_must_never_be_approved_or_executed(self):
        for fake in ("APPROVED","EXECUTED_PASS","OWNER_SIGNED"):
            c=self.candidate()
            c["questionDispositions"][0]["decision"]=fake
            self.rejects(c)

    def test_16_no_free_text_disposition_extra_signature_fields(self):
        c=self.candidate()
        c["questionDispositions"][0]["signedBy"]="unverified-owner"
        self.rejects(c)

    def test_17_reason_must_be_present_even_if_deferred(self):
        c=self.candidate()
        c["questionDispositions"][0]["rationale"]="ok"
        self.rejects(c)

    def test_18_wrong_sha_format_rejected_not_confused_with_actual_git_fetch(self):
        for invalid in ("deadbeef","A"*40,"z"*40,123):
            c=self.candidate()
            c["sourceCommit"]=invalid
            self.rejects(c)

    def test_19_owner_source_path_cannot_point_at_another_module(self):
        c=self.candidate()
        c["sourcePath"]="planning/contracts/M58-DRAFT.md"
        self.rejects(c)

    def test_20_source_path_cannot_escape_owner_namespace(self):
        for fake in ("planning/contracts/M54-../../secrets.md",
                     "planning/contracts/M54-\\fake.md",
                     "planning/contracts/M54-//fake.md"):
            c=self.candidate()
            c["sourcePath"]=fake
            self.rejects(c)

    def test_21_spoofed_github_domain_or_different_repo_rejected(self):
        for fake in ("https://github.com.evil/KayzenRoot/iris/pull/999",
                     "https://github.com/Other/iris/pull/999",
                     "https://github.com/KayzenRoot/iris/issues/110",
                     "http://github.com/KayzenRoot/iris/pull/999"):
            c=self.candidate()
            c["selfClaimedReviewUrl"]=fake
            self.rejects(c)

    def test_22_valid_github_issue_comment_url_is_still_unverified(self):
        c=self.candidate()
        c["selfClaimedReviewUrl"]="https://github.com/KayzenRoot/iris/issues/145#issuecomment-5858913719"
        r=self.inspect(c)
        self.assertFalse(r["claimedReviewIndependentlyVerified"])

    def test_23_false_blank_or_nonstring_self_claimed_owner_rejected(self):
        for fake in ("x",123,"x\ny"):
            c=self.candidate()
            c["selfClaimedOwner"]=fake
            self.rejects(c)

    def test_24_missing_issuer_or_source_ref_is_incomplete_not_signed(self):
        c=self.candidate()
        c.pop("sourceCommit")
        c["selfClaimedOwner"]=""
        r=self.inspect(c)
        self.assertEqual(r["formatStatus"],"MISSING_FIELDS_NOT_REVIEWABLE")
        self.assertEqual(r["missingFields"],["selfClaimedOwner","sourceCommit"])
        self.assertFalse(r["actualApprovedContract"])

    def test_25_scope_and_explicit_exclusions_both_required(self):
        c=self.candidate()
        c["scopeAndExclusions"]={"scope":"synthetic example to review"}
        self.rejects(c)
        c=self.candidate()
        c["scopeAndExclusions"]["exclusions"]="none"
        self.rejects(c)

    def test_26_empty_dispositions_are_incomplete_no_positive_proof(self):
        c=self.candidate("M58",0)
        r=self.inspect(c)
        self.assertEqual(r["formatStatus"],"MISSING_FIELDS_NOT_REVIEWABLE")
        self.assertEqual(r["missingFields"],["questionDispositions"])
        self.assertFalse(r["permissionToPlacePublishUseOsOrExecute"])

    def test_27_false_prior_source_owner_signoff_fails_closed(self):
        p=deepcopy(self.packets)
        p["sourceOwners"][1]["actualSignedOwnerContract"]=True
        # WO0037 source validation must run before the triage on this input.
        from scripts.verify_m09_h03_owner_packets import (
            H03IntegrityError,verify_h03,
        )
        with self.assertRaises(H03IntegrityError):
            verify_h03(p,read(ROOT,
                ".engineering/evidence/M12-OWNER-INTAKE-C02.json"),
                read(ROOT,
                ".engineering/evidence/M12-OWNER-DECISION-REGISTER.json"),
                read(ROOT,
                ".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json"),
                read(ROOT,
                ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json"),
                ROOT,check_documents=False)

    def test_28_claimed_existing_route_approval_rejected(self):
        routes=deepcopy(self.routes)
        routes["routes"][2]["actualSignedOwnerDecision"]=True
        with self.assertRaises(UntrustedReplyError):
            triage(self.candidate("M58"),self.packets,routes)

    def test_29_duplicate_json_object_keys_rejected_at_local_parse(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"untrusted.json"
            path.write_text('{"module":"M54","module":"M58"}',
                            encoding="utf-8")
            with self.assertRaises(UntrustedReplyError):
                read_draft(path)

    def test_30_all_statuses_preserve_permanent_no_permission(self):
        candidates=(
            self.candidate("M12",0),
            self.candidate("M54",2),
            self.candidate("M60",1000),
        )
        self.assertEqual(tuple(self.inspect(c)["formatStatus"] for c in candidates),
                         REPORT_STATUSES)
        for c in candidates:
            r=self.inspect(c)
            self.assertEqual(tuple(r["mandatoryWarnings"]),ALWAYS_PENDING)
            self.assertEqual(r["h01h02h03h04"],
                             "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE")
            self.assertFalse(r["realNegativeTestsExecuted"])
            self.assertFalse(r["actualApprovedContract"])
            self.assertFalse(r["permissionToPlacePublishUseOsOrExecute"])


if __name__=="__main__":
    unittest.main()
