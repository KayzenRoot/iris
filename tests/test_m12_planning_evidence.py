"""Pure and source-mutation tests for non-authorizing M12 planning evidence."""
from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.verify_m12_planning_evidence import (
    M12EvidenceError, SESSION_SPECS, REQUIRED_DEPENDENCIES,
    research_rows, unique_json, verify_register, verify_ftr, verify_fcs,
    verify_c02, verify_all, ROOT,
)


class ExtractorTests(unittest.TestCase):
    def setUp(self):
        self.src = SESSION_SPECS[0][4]
        self.q = [dict(id="M12-S01-U01", session="S01", owners="M12/M54", question="Who owns this?",
                       status="OPEN_UNRATED_PENDING_OWNER", source=self.src)]
        self.n = [dict(id="WR-01", session="S01", trigger="Stale claim",
                       safetyOracle="No admission", owners="M09", status="SPECIFIED_NOT_EXECUTED", source=self.src)]

    def valid(self):
        return "| M12-S01-U01 | M12/M54 | Who owns this? |\n| WR-01 | Stale claim | No admission | M09 |\n"

    def extract(self, md):
        return research_rows(md, "S01", "WR", 1, 1, self.src)

    def test_extract_valid_exact_semantics(self):
        self.assertEqual(self.extract(self.valid()), (self.q, self.n))

    def test_missing_question_fails_closed(self):
        with self.assertRaisesRegex(M12EvidenceError, "questions"):
            self.extract("| WR-01 | Stale claim | No admission | M09 |")

    def test_duplicate_question_fails_closed(self):
        with self.assertRaisesRegex(M12EvidenceError, "questions"):
            self.extract(self.valid() + "| M12-S01-U01 | M12/M54 | Fake |")

    def test_non_contiguous_question_id_fails_closed(self):
        with self.assertRaisesRegex(M12EvidenceError, "questions"):
            self.extract(self.valid().replace("M12-S01-U01", "M12-S01-U02"))

    def test_missing_negative_fails_closed(self):
        with self.assertRaisesRegex(M12EvidenceError, "scenarios"):
            self.extract("| M12-S01-U01 | M12/M54 | Who owns this? |")

    def test_duplicate_negative_fails_closed(self):
        with self.assertRaisesRegex(M12EvidenceError, "scenarios"):
            self.extract(self.valid() + "| WR-01 | Fake | Unsafe | M09 |")

    def test_negative_id_not_contiguous(self):
        with self.assertRaisesRegex(M12EvidenceError, "scenarios"):
            self.extract(self.valid().replace("WR-01", "WR-02"))

    def test_source_fields_trim_not_invented(self):
        q, n = self.extract("| M12-S01-U01 |  M12/M54  |  Who owns this?  |\n| WR-01 |  Stale claim  | No admission  |  M09 |")
        self.assertEqual(q, self.q)
        self.assertEqual(n, self.n)

    def test_empty_question_fails_closed(self):
        with self.assertRaisesRegex(M12EvidenceError, "empty"):
            self.extract(self.valid().replace("Who owns this?", " "))

    def test_empty_future_oracle_fails_closed(self):
        with self.assertRaisesRegex(M12EvidenceError, "incomplete"):
            self.extract(self.valid().replace("No admission", " "))


class RegistryTests(unittest.TestCase):
    def valid(self):
        q, n = research_rows("| M12-S01-U01 | M12 | q |\n| WR-01 | t | o | M09 |",
                             "S01", "WR", 1, 1, SESSION_SPECS[0][4])
        return dict(schemaVersion="iris-m12-owner-readiness-v0.1",
                    workOrder="IRIS-WO-0028", issue=128, status="UNADOPTED_NOT_FROZEN_OWNER_DECISIONS_PENDING",
                    selectedTopology="NONE", publicOrExecutablePort="NONE", implementationStatus="NOT_ADMITTED",
                    counts=dict(sessions=5, ownerQuestions=110, futureNegativeScenarios=80,
                                laterIndexModules=48, technologyRecords=16),
                    questions=deepcopy(q), negativeScenarios=deepcopy(n), unresolvedHardDependencies=sorted(REQUIRED_DEPENDENCIES)), q, n

    def check(self, alter):
        reg, q, n = self.valid()
        alter(reg)
        verify_register(reg, q, n)

    def test_valid_reference_only_register(self):
        self.check(lambda x: None)

    def test_owner_decision_promoted_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "falsely promoted"):
            self.check(lambda x: x.update(status="FROZEN"))

    def test_executable_port_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "unapproved port"):
            self.check(lambda x: x.update(publicOrExecutablePort="READY"))

    def test_missing_high_dependency_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "dependency"):
            self.check(lambda x: x["unresolvedHardDependencies"].remove("C02_FR_H02_OPEN"))

    def test_duplicate_dependency_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "dependency"):
            self.check(lambda x: x["unresolvedHardDependencies"].append("C02_FR_H01_OPEN"))

    def test_executed_case_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "negative-case"):
            self.check(lambda x: x["negativeScenarios"][0].update(status="PASS"))

    def test_approved_question_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "owner register"):
            self.check(lambda x: x["questions"][0].update(status="ACCEPTED"))

    def test_fake_question_wording_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "owner register"):
            self.check(lambda x: x["questions"][0].update(question="Self-approved"))

    def test_bad_count_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "count"):
            self.check(lambda x: x["counts"].update(ownerQuestions=109))

    def test_json_duplicate_key_fails(self):
        with self.assertRaisesRegex(M12EvidenceError, "duplicate JSON key"):
            json.loads('{"status":"OPEN","status":"APPROVED"}', object_pairs_hook=unique_json)


class ReferenceTests(unittest.TestCase):
    def test_ftr_exact_16_from_canonical_repo(self):
        verify_ftr((ROOT / "planning/reviews/M12-FINAL-TECHNOLOGY-REVIEW.md").read_text(encoding="utf-8"))

    def test_ftr_duplicate_id_rejected(self):
        ftr = (ROOT / "planning/reviews/M12-FINAL-TECHNOLOGY-REVIEW.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(M12EvidenceError, "FTR"):
            verify_ftr(ftr.replace("FTR-02", "FTR-01"))

    def test_ftr_unsupported_status_rejected(self):
        ftr = (ROOT / "planning/reviews/M12-FINAL-TECHNOLOGY-REVIEW.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(M12EvidenceError, "FTR"):
            verify_ftr(ftr.replace("| ACCEPT_REFERENCE |", "| ADOPTED_FOR_RUNTIME |", 1))

    def test_fcs_canonical_48_modules(self):
        verify_fcs((ROOT / "planning/MASTER-MODULE-INDEX.md").read_text(encoding="utf-8"),
                   (ROOT / "planning/compatibility/M12-FORWARD-COMPATIBILITY-SCAN.md").read_text(encoding="utf-8"))

    def test_fcs_missing_module_fails(self):
        index = (ROOT / "planning/MASTER-MODULE-INDEX.md").read_text(encoding="utf-8")
        fcs = (ROOT / "planning/compatibility/M12-FORWARD-COMPATIBILITY-SCAN.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(M12EvidenceError, "FCS"):
            verify_fcs(index, "\n".join(s for s in fcs.splitlines() if not s.startswith("| M54 |")))

    def test_fcs_false_owner_approval_fails(self):
        index = (ROOT / "planning/MASTER-MODULE-INDEX.md").read_text(encoding="utf-8")
        fcs = (ROOT / "planning/compatibility/M12-FORWARD-COMPATIBILITY-SCAN.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(M12EvidenceError, "FCS owner gate"):
            verify_fcs(index, fcs.replace("INDEX_ONLY / OWNER_CONTRACT_PENDING", "OWNER_APPROVED", 1))

    def test_c02_current_open_blockers(self):
        data = json.loads((ROOT / ".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json").read_text(encoding="utf-8"))
        verify_c02(data)

    def test_c02_owner_selection_requires_explicit_re_review(self):
        data = json.loads((ROOT / ".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json").read_text(encoding="utf-8"))
        data["issue110OwnerDecision"] = "A"
        with self.assertRaisesRegex(M12EvidenceError, "owner decision"):
            verify_c02(data)

    def test_c02_closing_high_without_proof_fails(self):
        data = json.loads((ROOT / ".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json").read_text(encoding="utf-8"))
        data["futureFreezeBlockers"][0]["status"] = "CLOSED"
        with self.assertRaisesRegex(M12EvidenceError, "falsely closed"):
            verify_c02(data)

    def test_real_repository_integrity(self):
        self.assertEqual(verify_all(ROOT), dict(questions=110, negative=80, ftr=16, fcs=48,
                                                invariants=24, c02HighOpen=4))


if __name__ == "__main__":
    unittest.main()
