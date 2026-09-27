"""WO0042: no synthetic H03 signature from a blank local worksheet."""
from __future__ import annotations
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from copy import deepcopy

from scripts.scaffold_m09_h03_owner_drafts import FILES, ScaffoldError, build, write, main
from scripts.triage_m09_h03_untrusted_owner_reply import MODULE_ISSUES, REQUIRED, triage_batch, UntrustedReplyError
from scripts.verify_m09_h03_owner_routes import ROOT, PRIOR, ROUTES, read


class WO0042BlankOwnerWorksheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets = read(ROOT, PRIOR)
        cls.routes = read(ROOT, ROUTES)
        cls.files = build(cls.packets, cls.routes)

    def candidate(self, module):
        return json.loads(self.files[f"{module}-draft.json"])

    def test_01_nine_strict_output_paths(self):
        self.assertEqual(set(self.files), FILES)
        self.assertEqual(len(self.files), 9)

    def test_02_exact_147_assignments_91_unique(self):
        queues = [[q["questionId"] for q in self.candidate(m)["questionDispositions"]]
                  for m in MODULE_ISSUES]
        self.assertEqual([len(q) for q in queues], [72, 39, 9, 27])
        self.assertEqual(sum(map(len, queues)), 147)
        self.assertEqual(len(set().union(*(set(q) for q in queues))), 91)

    def test_03_all_four_routes_and_original_ids_exact(self):
        for module, issue in MODULE_ISSUES.items():
            draft = self.candidate(module)
            expected = next(x for x in self.packets["sourceOwners"]
                            if x["module"] == module)
            self.assertEqual(draft["issue"], issue)
            self.assertEqual([q["questionId"] for q in draft["questionDispositions"]],
                             [q["id"] for q in expected["questions"]])

    def test_04_blank_decisions_and_empty_unverified_fields(self):
        for module in MODULE_ISSUES:
            candidate = self.candidate(module)
            self.assertEqual(set(candidate), REQUIRED)
            for field in ("sourceCommit", "sourcePath", "selfClaimedOwner",
                          "selfClaimedReviewUrl"):
                self.assertEqual(candidate[field], "")
            self.assertEqual(candidate["scopeAndExclusions"],
                             {"scope": "", "exclusions": ""})
            self.assertTrue(all(q["decision"] == "" and q["rationale"] == ""
                                for q in candidate["questionDispositions"]))

    def test_05_empty_four_draft_batch_never_passes_format_or_auth(self):
        with self.assertRaises(UntrustedReplyError):
            triage_batch([self.candidate(m) for m in MODULE_ISSUES],
                         self.packets, self.routes)

    def test_06_full_original_question_wording_and_source_paths_in_guides(self):
        for owner in self.packets["sourceOwners"]:
            guide = self.files[f"{owner['module']}-questions.md"]
            for q in owner["questions"]:
                self.assertIn(q["originalQuestion"], guide)
                self.assertIn(q["source"], guide)

    def test_07_shared_questions_link_to_other_owners(self):
        self.assertIn("M60", self.files["M54-questions.md"])
        self.assertIn("M54", self.files["M60-questions.md"])
        self.assertIn("M54", self.files["M58-questions.md"])

    def test_08_build_is_deterministic_and_requires_unapproved_sources(self):
        self.assertEqual(self.files, build(self.packets, self.routes))
        tampered = deepcopy(self.packets)
        tampered["sourceOwners"][0]["actualSignedOwnerContract"] = True
        with self.assertRaisesRegex(ScaffoldError,"forged approval"):
            build(tampered, self.routes)

    def test_09_write_nine_local_files_only(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated"
            write(output, self.files)
            self.assertEqual({x.name for x in output.iterdir()}, FILES)
            self.assertEqual(json.loads((output / "M58-draft.json").read_text())["issue"],146)

    def test_10_existing_target_cannot_be_overwritten(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "existing"
            output.mkdir()
            (output / "keep").write_text("user data",encoding="utf-8")
            with self.assertRaisesRegex(ScaffoldError,"never overwrite"):
                write(output, self.files)
            self.assertEqual((output / "keep").read_text(),"user data")

    def test_11_unsafe_manifest_and_missing_parent_fail_before_write(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "new"
            changed = dict(self.files)
            changed["../escape.json"] = changed.pop("M54-draft.json")
            with self.assertRaisesRegex(ScaffoldError,"manifest"):
                write(output, changed)
            with self.assertRaisesRegex(ScaffoldError,"parent"):
                write(output / "missing" / "nested",self.files)
            self.assertFalse(output.exists())

    def test_12_cli_success_refuses_to_claim_any_auth(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "forms"
            stream = StringIO()
            with patch("sys.argv",["scaffold","--output-dir",str(output)]):
                with redirect_stdout(stream):
                    status = main()
            self.assertEqual(status,0)
            result=json.loads(stream.getvalue())
            self.assertEqual(result["originalAssignments"],147)
            self.assertEqual(result["realOwnerAnswers"],0)
            self.assertIs(result["actualApprovedContract"],False)
            self.assertFalse(result["permissionToPlacePublishUseOsOrExecute"])

    def test_13_canonical_checkpoint_mirror_is_factual_wo41_not_fake_wo42_merge(self):
        cp=(ROOT/"docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        mirror=(ROOT/".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
        machine=json.loads((ROOT/".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))
        self.assertEqual(cp,mirror)
        self.assertEqual(cp.split("## NEXT STEP\n",1)[1].strip(),machine["nextStep"])
        self.assertIn("IRIS-WO-0041",cp)
        self.assertIn("36347498096",cp)
        self.assertIn("4313/4313",cp)
        self.assertIn("COMPLETE_DRAFT_FORMAT_ONLY is never approval",machine["nextStep"])
        self.assertIn("SPECIFIED_NOT_EXECUTED",machine["nextStep"])
        self.assertIn("OPEN HIGH_FOR_FUTURE_FREEZE",machine["nextStep"])
        self.assertNotIn("WO0042 merged",machine["nextStep"])


if __name__=="__main__":
    unittest.main()
