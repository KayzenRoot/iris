from __future__ import annotations

import unittest
from dataclasses import replace

from iris_microbenchmark.invariants import M08_INVARIANTS
from m08_invariant_proofs import PROOF_TARGET_CLAIMS
from scripts.validate_m08_invariants import (
    canonical_invariants, validate_frozen_invariant_records, validate_proof_claims,
)


class TestInvariantProofValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.canonical = canonical_invariants()

    def test_missing_invariant_id_fails_closed(self):
        with self.assertRaises(SystemExit):
            validate_frozen_invariant_records(M08_INVARIANTS[:-1], self.canonical)

    def test_duplicate_invariant_id_fails_closed(self):
        duplicate = replace(M08_INVARIANTS[1], number=1)
        records = (M08_INVARIANTS[0], duplicate, *M08_INVARIANTS[2:])
        with self.assertRaises(SystemExit):
            validate_frozen_invariant_records(records, self.canonical)

    def test_frozen_text_drift_fails_closed(self):
        changed = replace(M08_INVARIANTS[0], frozen_text="1. changed contract text")
        records = (changed, *M08_INVARIANTS[1:])
        with self.assertRaises(SystemExit):
            validate_frozen_invariant_records(records, self.canonical)

    def test_frozen_text_digest_drift_fails_closed(self):
        changed = replace(M08_INVARIANTS[0], text_digest="0" * 64)
        records = (changed, *M08_INVARIANTS[1:])
        with self.assertRaises(SystemExit):
            validate_frozen_invariant_records(records, self.canonical)

    def test_claim_without_target_declaration_fails_closed(self):
        claims = {target: values for target, values in PROOF_TARGET_CLAIMS.items()}
        target = next(iter(claims))
        claims[target] = claims[target][1:]
        with self.assertRaises(SystemExit):
            validate_proof_claims(M08_INVARIANTS, claims, set(claims))

    def test_duplicate_claim_and_orphan_target_fail_closed(self):
        claims = {target: values for target, values in PROOF_TARGET_CLAIMS.items()}
        target = next(iter(claims))
        claims[target] = (*claims[target], claims[target][0])
        with self.assertRaises(SystemExit):
            validate_proof_claims(M08_INVARIANTS, claims, set(claims))

        claims = {**PROOF_TARGET_CLAIMS, "tests/orphan.py::Orphan::test_orphan": ()}
        with self.assertRaises(SystemExit):
            validate_proof_claims(M08_INVARIANTS, claims, set(PROOF_TARGET_CLAIMS))

    def test_claim_predicate_without_matching_proof_declaration_fails_closed(self):
        claims = {target: values for target, values in PROOF_TARGET_CLAIMS.items()}
        target = next(iter(claims))
        number, _ = claims[target][0]
        claims[target] = ((number, "unregistered-predicate"), *claims[target][1:])
        with self.assertRaises(SystemExit):
            validate_proof_claims(M08_INVARIANTS, claims, set(claims))

    def test_target_without_executable_assertions_fails_closed(self):
        target = next(iter(PROOF_TARGET_CLAIMS))
        with self.assertRaises(SystemExit):
            validate_proof_claims(
                M08_INVARIANTS,
                PROOF_TARGET_CLAIMS,
                set(PROOF_TARGET_CLAIMS) - {target},
            )


if __name__ == "__main__":
    unittest.main()
