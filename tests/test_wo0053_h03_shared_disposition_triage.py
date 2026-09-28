"""WO0053: exact original H03 shared-question *draft-label* mismatch triage only."""
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
    ALWAYS_PENDING, MODULE_ISSUES, PRIOR, ROOT, ROUTES, SCHEMA,
    UntrustedReplyError, main, read, triage_batch,
)


class SharedDraftDispositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets = read(ROOT, PRIOR)
        cls.routes = read(ROOT, ROUTES)
        cls.question_sets = {
            item["module"]:set(item["sourceQuestionIds"])
            for item in cls.routes["routes"]
        }
        cls.m54_m60 = sorted(cls.question_sets["M54"] & cls.question_sets["M60"])

    def draft(self, module, count=None):
        packet = next(x for x in self.packets["sourceOwners"]
                      if x["module"] == module)
        rows = packet["questions"] if count is None else packet["questions"][:count]
        return {
            "schemaVersion":SCHEMA, "module":module,
            "issue":MODULE_ISSUES[module], "sourceCommit":"a"*40,
            "sourcePath":f"planning/contracts/{module}-SYNTHETIC.md",
            "selfClaimedOwner":"synthetic-unverified-author",
            "selfClaimedReviewUrl":"https://github.com/KayzenRoot/iris/pull/999",
            "scopeAndExclusions":{
                "scope":"Synthetic owner source proposal not approved",
                "exclusions":"No identity verification or runtime permissions"},
            "questionDispositions":[
                {"questionId":q["id"],"decision":"DEFER",
                 "rationale":"Synthetic original question remains unapproved"}
                for q in rows],
        }

    def all_drafts(self):
        return [self.draft(m) for m in MODULE_ISSUES]

    def changed(self, drafts, module, qid, decision="PROPOSED_ANSWER"):
        target=next(d for d in drafts if d["module"] == module)
        row=next(x for x in target["questionDispositions"]
                 if x["questionId"] == qid)
        row["decision"]=decision
        row["rationale"]="Untrusted proposed new disposition pending real review"
        return drafts

    def run_batch(self, drafts):
        return triage_batch(drafts, self.packets, self.routes)

    def test_01_original_m54_m60_shared_source_has_eighteen_original_ids(self):
        self.assertEqual(len(self.m54_m60),18)
        self.assertEqual(len(set(self.m54_m60)),18)

    def test_02_all_matching_drafts_stay_format_only_not_approval(self):
        b=self.run_batch(self.all_drafts())
        self.assertEqual(b["batchFormatStatus"],
                         "FOUR_OWNER_DRAFTS_COMPLETE_FORMAT_ONLY")
        self.assertEqual(b["sharedQuestionDispositionMismatches"],[])
        self.assertEqual(b["sharedQuestionDispositionMismatchCount"],0)
        self.assertFalse(b["syntacticAgreementIsOwnerApproval"])
        self.assertEqual(b["mandatoryWarnings"],list(ALWAYS_PENDING))
        self.assertEqual(b["actualOwnerApprovals"],0)
        self.assertFalse(b["permissionToPlacePublishUseOsOrExecute"])

    def test_03_m54_m60_disagreeing_draft_codes_are_exposed(self):
        qid=self.m54_m60[0]
        b=self.run_batch(self.changed(self.all_drafts(),"M60",qid))
        mismatch=next(x for x in b["sharedQuestionDispositionMismatches"]
                      if x["questionId"]==qid)
        self.assertEqual(mismatch["untrustedDraftDispositions"]["M54"],"DEFER")
        self.assertEqual(mismatch["untrustedDraftDispositions"]["M60"],
                         "PROPOSED_ANSWER")
        self.assertEqual(mismatch["interpretation"],
                         "DRAFT_LABEL_MISMATCH_REQUIRES_INDEPENDENT_REVIEW")
        self.assertEqual(b["sharedQuestionDispositionMismatchCount"],1)
        self.assertEqual(b["batchFormatStatus"],
                         "FOUR_OWNER_DRAFTS_DISPOSITION_MISMATCH_FORMAT_ONLY")
        self.assertTrue(b["allFourDraftsCompleteFormatOnly"])
        self.assertFalse(b["actualApprovedContract"])

    def test_04_reversed_file_order_produces_same_canonical_mismatch_report(self):
        qid=self.m54_m60[1]
        drafts=self.changed(self.all_drafts(),"M60",qid)
        self.assertEqual(self.run_batch(drafts),
                         self.run_batch(list(reversed(deepcopy(drafts)))))

    def test_05_different_rationale_is_not_mistaken_for_formal_owner_conflict(self):
        qid=self.m54_m60[0]
        drafts=self.all_drafts()
        row=next(x for x in next(d for d in drafts if d["module"]=="M60")
                 ["questionDispositions"] if x["questionId"]==qid)
        row["rationale"]="Different synthetic owner rationale with same label"
        b=self.run_batch(drafts)
        self.assertEqual(b["sharedQuestionDispositionMismatches"],[])
        self.assertFalse(b["syntacticAgreementIsOwnerApproval"])

    def test_06_missing_coowner_draft_is_separate_from_disagreement(self):
        b=self.run_batch([self.draft("M54")])
        self.assertEqual(b["sharedQuestionDispositionMismatches"],[])
        gap=next(x for x in b["sharedQuestionsMissingOneOrMoreDraftDispositions"]
                 if x["questionId"]==self.m54_m60[0])
        self.assertIn("M60",gap["missingDraftDispositionsFrom"])
        self.assertEqual(b["batchFormatStatus"],
                         "INCOMPLETE_DRAFT_BATCH_FORMAT_ONLY")

    def test_07_partial_batch_reports_absent_original_third_coowner(self):
        # The unchanged original source has seven M12+M54+M60 shared IDs.
        # Use a genuine triple-owner ID, not a synthetic four-owner claim.
        qid=next(q for q in self.m54_m60
                 if q in self.question_sets["M12"]
                 and q not in self.question_sets["M58"])
        drafts=self.changed([self.draft("M54"),self.draft("M60")],
                            "M60",qid)
        b=self.run_batch(drafts)
        self.assertEqual(b["batchFormatStatus"],
                         "INCOMPLETE_DRAFT_BATCH_FORMAT_ONLY")
        self.assertEqual(b["sharedQuestionDispositionMismatchCount"],1)
        mismatch=next(x for x in b["sharedQuestionDispositionMismatches"]
                      if x["questionId"]==qid)
        self.assertEqual(mismatch["otherRequiredOwnerDraftsAbsent"],["M12"])
        self.assertEqual(mismatch["untrustedDraftDispositions"],
                         {"M54":"DEFER","M60":"PROPOSED_ANSWER"})
        missing=next(x for x in b["sharedQuestionsMissingOneOrMoreDraftDispositions"]
                     if x["questionId"]==qid)
        self.assertEqual(missing["missingDraftDispositionsFrom"],["M12"])
        self.assertFalse(b["allFourDraftsPresent"])
        self.assertFalse(b["actualApprovedContract"])

    def test_08_unique_original_question_draft_label_does_not_fake_mismatch(self):
        counts={}
        for questions in self.question_sets.values():
            for qid in questions:
                counts[qid]=counts.get(qid,0)+1
        unique=next((module,qid) for module,qs in self.question_sets.items()
                    for qid in sorted(qs) if counts[qid]==1)
        drafts=self.changed(self.all_drafts(),unique[0],unique[1])
        b=self.run_batch(drafts)
        self.assertEqual(b["sharedQuestionDispositionMismatches"],[])
        self.assertEqual(b["batchFormatStatus"],
                         "FOUR_OWNER_DRAFTS_COMPLETE_FORMAT_ONLY")

    def test_09_two_different_shared_ids_have_sorted_exact_original_ids(self):
        ids=self.m54_m60[:2]
        drafts=self.changed(self.all_drafts(),"M60",ids[1])
        drafts=self.changed(drafts,"M60",ids[0])
        b=self.run_batch(drafts)
        self.assertEqual([x["questionId"]
                          for x in b["sharedQuestionDispositionMismatches"]],ids)
        self.assertEqual(b["sharedQuestionDispositionMismatchCount"],2)

    def test_10_illegal_fake_owner_approval_still_rejects_entire_bundle(self):
        drafts=self.changed(self.all_drafts(),"M60",self.m54_m60[0])
        next(d for d in drafts if d["module"]=="M54")["actualOwnerApproved"]=True
        with self.assertRaises(UntrustedReplyError):
            self.run_batch(drafts)

    def test_11_all_proposed_synthetic_owners_are_never_real_owner_proof(self):
        drafts=self.all_drafts()
        for d in drafts:
            for row in d["questionDispositions"]:
                row["decision"]="PROPOSED_ANSWER"
        b=self.run_batch(drafts)
        self.assertEqual(b["sharedQuestionDispositionMismatchCount"],0)
        self.assertFalse(b["syntacticAgreementIsOwnerApproval"])
        for field in ("claimedOwnerAuthenticated","claimedSourceWasFetched",
                      "claimedReviewIndependentlyVerified",
                      "otherOwnerSignaturesVerified","actualApprovedContract",
                      "realNegativeTestsExecuted",
                      "permissionToPlacePublishUseOsOrExecute"):
            self.assertIs(b[field],False,field)

    def test_12_cli_exposes_mismatch_without_positive_authority_or_network(self):
        drafts=self.changed([self.draft("M54"),self.draft("M60")],
                            "M60",self.m54_m60[0])
        with TemporaryDirectory() as tmp:
            argv=["triage","--candidate"]
            for draft in drafts:
                path=Path(tmp)/(draft["module"]+".json")
                path.write_text(json.dumps(draft),encoding="utf-8")
                argv.append(str(path))
            output=StringIO()
            with patch("sys.argv",argv),redirect_stdout(output):
                code=main()
            self.assertEqual(code,0)
            report=json.loads(output.getvalue())
            self.assertEqual(report["sharedQuestionDispositionMismatchCount"],1)
            self.assertEqual(report["actualOwnerApprovals"],0)
            self.assertFalse(report["actualApprovedContract"])
            self.assertFalse(report["permissionToPlacePublishUseOsOrExecute"])


if __name__=="__main__":
    unittest.main()
