"""WO0041: bounded offline four-owner DRAFT bundle; no H03 authority."""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from scripts.triage_m09_h03_untrusted_owner_reply import (
    ALWAYS_PENDING, MAX_DRAFT_BYTES, MODULE_ISSUES, PRIOR, ROOT, ROUTES,
    SCHEMA, UntrustedReplyError, main, read, read_draft, triage_batch,
)


class H03OfflineBatchTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes=read(ROOT,ROUTES)
        cls.packets=read(ROOT,PRIOR)

    def draft(self,module,count=999):
        packet=next(x for x in self.packets["sourceOwners"] if x["module"]==module)
        return {
            "schemaVersion":SCHEMA,"module":module,"issue":MODULE_ISSUES[module],
            "sourceCommit":"a"*40,
            "sourcePath":f"planning/contracts/{module}-DRAFT-NOT-APPROVED.md",
            "selfClaimedOwner":"untrusted-synthetic-claim",
            "selfClaimedReviewUrl":"https://github.com/KayzenRoot/iris/pull/999",
            "scopeAndExclusions":{
                "scope":"Synthetic source response draft only",
                "exclusions":"No owner signoff or real resource permission"},
            "questionDispositions":[
                {"questionId":q["id"],"decision":"DEFER",
                 "rationale":"Unverified proposed owner response remains pending"}
                for q in packet["questions"][:count]],
        }

    def run_batch(self,*drafts):
        return triage_batch(list(drafts),self.packets,self.routes)

    def test_01_four_syntactically_complete_drafts_never_prove_authority(self):
        result=self.run_batch(*(self.draft(m) for m in MODULE_ISSUES))
        self.assertEqual(result["batchFormatStatus"],
                         "FOUR_OWNER_DRAFTS_COMPLETE_FORMAT_ONLY")
        self.assertEqual(result["originalSourceAssignmentCount"],147)
        self.assertEqual(result["uniqueOriginalSourceQuestionCount"],91)
        self.assertEqual(result["actualOwnerApprovals"],0)
        self.assertEqual(result["mandatoryWarnings"],list(ALWAYS_PENDING))
        self.assertFalse(result["actualApprovedContract"])
        self.assertFalse(result["permissionToPlacePublishUseOsOrExecute"])
        self.assertFalse(result["realNegativeTestsExecuted"])

    def test_02_batch_output_order_is_canonical_even_when_inputs_reverse(self):
        result=self.run_batch(*(self.draft(m) for m in reversed(MODULE_ISSUES)))
        self.assertEqual([x["module"] for x in result["drafts"]],
                         list(MODULE_ISSUES))
        self.assertEqual(result["receivedDraftModules"],list(MODULE_ISSUES))

    def test_03_two_drafts_expose_two_absent_owner_responses(self):
        result=self.run_batch(self.draft("M58"),self.draft("M54"))
        self.assertEqual(result["missingDraftModules"],["M12","M60"])
        self.assertFalse(result["allFourDraftsPresent"])
        self.assertFalse(result["allFourDraftsCompleteFormatOnly"])

    def test_04_shared_original_question_missing_draft_is_reported(self):
        full=self.run_batch(*(self.draft(m) for m in MODULE_ISSUES))
        self.assertEqual(full["sharedQuestionsMissingOneOrMoreDraftDispositions"],[])
        short=self.run_batch(self.draft("M12",1),
                             self.draft("M54"),self.draft("M58"),self.draft("M60"))
        self.assertTrue(short["sharedQuestionsMissingOneOrMoreDraftDispositions"])
        self.assertFalse(short["allFourDraftsCompleteFormatOnly"])

    def test_05_duplicate_owner_draft_rejects_whole_bundle(self):
        with self.assertRaisesRegex(UntrustedReplyError,"duplicate draft"):
            self.run_batch(self.draft("M54"),self.draft("M54"))

    def test_06_empty_batch_is_not_valid_owner_review(self):
        with self.assertRaises(UntrustedReplyError):
            triage_batch([],self.packets,self.routes)

    def test_07_more_than_four_untrusted_drafts_rejected(self):
        with self.assertRaises(UntrustedReplyError):
            self.run_batch(*(self.draft("M54") for _ in range(5)))
        # The real CLI must reject before opening any path in an oversized list.
        args=["triage","--candidate",*(f"nonexistent-{i}.json" for i in range(5))]
        out=StringIO()
        with patch("sys.argv",args):
            with redirect_stdout(out):
                code=main()
        self.assertEqual(code,2)
        self.assertIn("one to four separate",json.loads(out.getvalue())["reason"])

    def test_08_one_foreign_or_wrong_issue_rejects_everything(self):
        bad=self.draft("M60")
        bad["issue"]=145
        with self.assertRaises(UntrustedReplyError):
            self.run_batch(self.draft("M12"),bad)

    def test_09_false_approval_claim_cannot_poison_complete_bundle(self):
        bad=self.draft("M58")
        bad["actualApprovedContract"]=True
        with self.assertRaises(UntrustedReplyError):
            self.run_batch(self.draft("M12"),self.draft("M54"),bad,
                           self.draft("M60"))

    def test_10_all_public_batch_trust_and_permission_flags_false(self):
        result=self.run_batch(*(self.draft(m) for m in MODULE_ISSUES))
        for field in ("claimedOwnerAuthenticated","claimedSourceWasFetched",
                      "claimedReviewIndependentlyVerified",
                      "otherOwnerSignaturesVerified","realNegativeTestsExecuted",
                      "actualApprovedContract",
                      "permissionToPlacePublishUseOsOrExecute"):
            self.assertIs(result[field],False,field)
        self.assertEqual(result["h01h02h03h04"],
                         "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE")

    def test_11_untrusted_file_exceeding_one_mib_rejected_before_json_parse(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"big.json"
            p.write_bytes(b"{" + b"x"*(MAX_DRAFT_BYTES))
            with self.assertRaisesRegex(UntrustedReplyError,"one-MiB"):
                read_draft(p)

    def test_12_small_valid_utf8_file_remains_accepted(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"draft.json"
            expected=self.draft("M54",1)
            expected["scopeAndExclusions"]["scope"]="quoted brackets "+("["*150)
            p.write_text(json.dumps(expected,ensure_ascii=False),encoding="utf-8")
            self.assertEqual(read_draft(p),expected)

    def test_13_non_utf8_bytes_rejected_as_untrusted_draft_error(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"not-utf8.json"
            p.write_bytes(b'{"module":"M54","bad":"\xff"}')
            with self.assertRaisesRegex(UntrustedReplyError,"UTF-8"):
                read_draft(p)

    def test_14_excessive_json_nesting_rejected_without_traceback(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"nested.json"
            p.write_text("["*3000 + "0" + "]"*3000,encoding="utf-8")
            with self.assertRaisesRegex(UntrustedReplyError,"nesting"):
                read_draft(p)

    def test_15_nonstandard_json_nan_rejected(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"nan.json"
            p.write_text('{"module":"M54","issue":NaN}',encoding="utf-8")
            with self.assertRaisesRegex(UntrustedReplyError,"non-standard"):
                read_draft(p)

    def test_16_nested_duplicate_json_keys_rejected(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"duplicate.json"
            p.write_text('{"module":"M54","scope":{"a":1,"a":2}}',
                         encoding="utf-8")
            with self.assertRaisesRegex(UntrustedReplyError,"duplicate"):
                read_draft(p)

    def test_17_legacy_single_file_cli_retains_original_result_schema(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"m54.json"
            p.write_text(json.dumps(self.draft("M54",1)),encoding="utf-8")
            out=StringIO()
            with patch("sys.argv",["triage","--candidate",str(p)]):
                with redirect_stdout(out):
                    code=main()
            self.assertEqual(code,0)
            result=json.loads(out.getvalue())
            self.assertEqual(result["module"],"M54")
            self.assertNotIn("batchFormatStatus",result)
            self.assertFalse(result["actualApprovedContract"])

    def test_18_multi_file_cli_returns_deterministic_format_only_batch(self):
        with TemporaryDirectory() as tmp:
            args=["triage","--candidate"]
            for module in ("M60","M12"):
                p=Path(tmp)/(module+".json")
                p.write_text(json.dumps(self.draft(module,1)),encoding="utf-8")
                args.append(str(p))
            out=StringIO()
            with patch("sys.argv",args):
                with redirect_stdout(out):
                    code=main()
            self.assertEqual(code,0)
            result=json.loads(out.getvalue())
            self.assertEqual(result["receivedDraftModules"],["M12","M60"])
            self.assertEqual(result["missingDraftModules"],["M54","M58"])
            self.assertFalse(result["permissionToPlacePublishUseOsOrExecute"])


if __name__=="__main__":
    unittest.main()
