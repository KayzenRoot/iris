"""Six domains, one kernel: the §6 neutrality proof, executed rather than asserted in prose.

The contract's neutrality claim is that M03 carries no domain vocabulary, and a claim like that is
easy to write and hard to fake. What this file pins is the table a reviewer can actually check: six
briefs from six different production worlds, each reaching the same four kernel calls, each producing
a different artifact, and none of them reaching a kernel branch that knows what a lens, a mesh or a
prompt is. The rows disagree where they should — one carries a blocking contradiction, one waits on a
human answer, four are ready — because a table whose rows all say the same thing proves only that the
fixture was written to pass.

Everything here reads :mod:`examples.m03_synthetic_profiles` as data. Nothing in this file compiles a
brief by hand, so if the example stops being admissible the failure lands in one place.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from examples import m03_synthetic_profiles as X
from iris_intent.briefs import BriefRevision
from iris_intent.conflicts import ConflictConsequence
from iris_intent.constraints import KNOWN_CHANNELS, ConstraintBundle
from iris_intent.fingerprints import SemanticIntentFingerprint
from iris_intent.intent import IntentStatement, ModalChannel, StatementKind
from iris_intent.readiness import READINESS_FAMILIES, SemanticReleaseReadinessReport
from iris_intent.slicing import MinimumSufficientSemanticSlice

PROFILE_IDS = (
    "logo-brand-web",
    "product-photography",
    "isometric-game-asset",
    "film-commercial",
    "spokesperson-digital-human",
    "voice-narration-music",
)

#: The example lives beside the kernel, so a reader may want to delete it. That is only safe if the
#: kernel never looks back, which is the claim the import scan below checks.
KERNEL_PACKAGE = Path(__file__).resolve().parent.parent / "iris_intent"


class ProfileTable(unittest.TestCase):
    """The six rows exist, are distinct, and are the six §6 names."""

    def test_the_six_contract_domains_are_all_present(self) -> None:
        self.assertEqual(tuple(item.profile_id for item in X.BRIEFS), PROFILE_IDS)

    def test_every_profile_is_a_frozen_kernel_record_set(self) -> None:
        for profile in X.BRIEFS:
            with self.subTest(profile=profile.profile_id):
                self.assertIsInstance(profile.revision, BriefRevision)
                self.assertIsInstance(profile.bundle, ConstraintBundle)
                self.assertTrue(profile.revision.admitted)
                self.assertTrue(profile.bundle.is_admitted)

    def test_a_profile_lookup_accepts_both_spellings(self) -> None:
        for identifier in PROFILE_IDS:
            self.assertIs(X.profile_for(identifier), X.profile_for(f"profile.{identifier}"))
        with self.assertRaises(KeyError) as unknown:
            X.profile_for("brief.not-a-domain")
        self.assertIn("unknown synthetic brief", str(unknown.exception))

    def test_channel_lookup_finds_the_domains_that_speak_it(self) -> None:
        image = {item.profile_id for item in X.profiles_by_channel(ModalChannel.IMAGE.value)}
        audio = {item.profile_id for item in X.profiles_by_channel(ModalChannel.AUDIO.value)}
        self.assertIn("logo-brand-web", image)
        self.assertIn("product-photography", image)
        self.assertIn("film-commercial", audio)
        self.assertEqual(X.profiles_by_channel("nonexistent-channel"), ())
        self.assertNotEqual(image, audio, "a channel index that matched everything indexes nothing")


class KernelPass(unittest.TestCase):
    """Each profile survives the four calls, and the calls are the same four for all six."""

    def setUp(self) -> None:
        self.artifacts = {item.profile_id: X.run_kernel(item) for item in X.BRIEFS}

    def test_the_four_artifacts_are_real_records_for_every_domain(self) -> None:
        for profile in X.BRIEFS:
            with self.subTest(profile=profile.profile_id):
                artifacts = self.artifacts[profile.profile_id]
                self.assertIsInstance(artifacts["slice"], MinimumSufficientSemanticSlice)
                self.assertIsInstance(artifacts["fingerprint"], SemanticIntentFingerprint)
                self.assertIsInstance(artifacts["readiness"], SemanticReleaseReadinessReport)
                self.assertIsInstance(artifacts["conflicts"], tuple)

    def test_the_semantic_digest_identifies_exactly_one_domain(self) -> None:
        digests = [
            self.artifacts[identifier]["fingerprint"].semantic_digest
            for identifier in self.artifacts
        ]
        self.assertEqual(len(set(digests)), len(PROFILE_IDS))
        for digest in digests:
            self.assertEqual(len(digest), 64)

    def test_the_kernel_is_repeatable_across_two_runs(self) -> None:
        for profile in X.BRIEFS:
            with self.subTest(profile=profile.profile_id):
                again = X.run_kernel(profile)
                first = self.artifacts[profile.profile_id]
                self.assertEqual(
                    first["slice"].slice_digest, again["slice"].slice_digest
                )
                self.assertEqual(
                    first["fingerprint"].semantic_digest,
                    again["fingerprint"].semantic_digest,
                )
                self.assertEqual(
                    first["readiness"].report_digest, again["readiness"].report_digest
                )

    def test_every_readiness_report_assesses_all_seven_families(self) -> None:
        for identifier, artifacts in self.artifacts.items():
            with self.subTest(profile=identifier):
                self.assertEqual(
                    set(artifacts["readiness"].assessed_families),
                    {family.value for family in READINESS_FAMILIES},
                )

    def test_the_table_disagrees_where_the_briefs_differ(self) -> None:
        blocking = {
            identifier
            for identifier, artifacts in self.artifacts.items()
            if artifacts["readiness"].blocking_families == ("BLOCKING_CONFLICT",)
        }
        waiting = {
            identifier
            for identifier, artifacts in self.artifacts.items()
            if artifacts["readiness"].blocking_families == ("HUMAN_DECISION_REQUIRED",)
        }
        self.assertEqual(blocking, {"product-photography"})
        self.assertEqual(waiting, {"spokesperson-digital-human"})
        ready = {
            identifier
            for identifier, artifacts in self.artifacts.items()
            if artifacts["readiness"].ready
        }
        self.assertEqual(ready, set(PROFILE_IDS) - blocking - waiting)

    def test_a_blocking_contradiction_is_recorded_not_resolved_by_the_kernel(self) -> None:
        conflict = self.artifacts["product-photography"]["conflicts"][0]
        self.assertTrue(conflict.blocks_contract)
        self.assertIsNone(conflict.resolution)
        self.assertEqual(
            conflict.consequence, ConflictConsequence.BLOCKING.value
        )

    def test_a_slice_never_carries_an_unrelated_statement(self) -> None:
        for profile in X.BRIEFS:
            with self.subTest(profile=profile.profile_id):
                sliced = X.run_kernel(profile)["slice"]
                requested = set(sliced.paths)
                for statement in sliced.statements:
                    self.assertTrue(
                        statement.semantic_path in requested
                        or statement.statement_id in sliced.inclusion_reasons,
                        f"{statement.statement_id} arrived without a recorded reason",
                    )
                self.assertEqual(
                    set(sliced.statement_ids) & set(sliced.excluded_statement_ids), set()
                )

    def test_purpose_changes_the_closure_for_every_domain_the_same_way(self) -> None:
        """A compilation slice carries rules, an audit slice carries provenance.

        Checked on all six rather than on one: if the purpose switch needed a domain's help, the
        six would not agree on which half they were handed.
        """

        for profile in X.BRIEFS:
            with self.subTest(profile=profile.profile_id):
                compiled = X.run_kernel(profile)["slice"]
                audited = X.audit_slice(profile)
                self.assertTrue(compiled.constraints)
                self.assertEqual(compiled.provenance_capsules, ())
                self.assertTrue(audited.provenance_capsules)
                self.assertEqual(audited.constraints, ())
                for statement in audited.statements:
                    self.assertIsNotNone(statement.provenance)
                    self.assertTrue(statement.provenance.source_refs)


class VocabularyBoundary(unittest.TestCase):
    """The kernel's own words contain no domain, and no kernel file reaches for one."""

    def test_channel_labels_come_from_the_kernel_enum(self) -> None:
        declared = {
            channel for profile in X.BRIEFS for channel in profile.channels
        }
        self.assertTrue(declared <= {member.value for member in ModalChannel})
        self.assertTrue(declared <= set(KNOWN_CHANNELS))

    def test_statement_kinds_are_all_kernel_vocabulary(self) -> None:
        kinds = {
            statement.kind
            for profile in X.BRIEFS
            for statement in profile.revision.statements
        }
        self.assertTrue(kinds <= {member.value for member in StatementKind})
        for profile in X.BRIEFS:
            for statement in profile.revision.statements:
                self.assertIsInstance(statement, IntentStatement)

    def test_no_kernel_module_imports_the_examples(self) -> None:
        offenders = [
            path.name
            for path in sorted(KERNEL_PACKAGE.glob("*.py"))
            if "examples" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [], "a kernel that imports its own fixture is not deletable")

    def test_the_kernel_vocabulary_carries_no_domain_word(self) -> None:
        """§18's neutrality bullet, checked against the enums rather than against a file list."""

        forbidden = (
            "PIXEL",
            "LENS",
            "MESH",
            "POLYGON",
            "PROMPT",
            "SEED",
            "CAMERA",
            "BLENDER",
            "COMFY",
            "MAYA",
            "DIFFUSION",
            "TRIANGLE",
        )
        labels = {member.value for member in ModalChannel} | {
            member.value for member in StatementKind
        } | {member.value for member in X.SourceKind}
        self.assertEqual(
            sorted({word for word in forbidden for label in labels if word in label}), []
        )


class PayloadRoundTrip(unittest.TestCase):
    """What the example compiles is what a store would persist."""

    def test_a_revision_round_trips_into_the_digest_that_identified_it(self) -> None:
        for profile in X.BRIEFS:
            with self.subTest(profile=profile.profile_id):
                payload: dict[str, Any] = profile.revision.to_payload()
                rebuilt = BriefRevision.from_payload(payload)
                self.assertEqual(rebuilt, profile.revision)
                self.assertEqual(
                    rebuilt.revision_ref.content_digest,
                    profile.revision.revision_ref.content_digest,
                )

    def test_a_bundle_round_trips_with_every_rule_intact(self) -> None:
        for profile in X.BRIEFS:
            with self.subTest(profile=profile.profile_id):
                rebuilt = ConstraintBundle.from_payload(profile.bundle.to_payload())
                self.assertEqual(
                    [item.constraint_id for item in rebuilt.constraints],
                    [item.constraint_id for item in profile.bundle.constraints],
                )
                self.assertEqual(rebuilt.bundle_ref, profile.bundle.bundle_ref)


if __name__ == "__main__":
    unittest.main()
