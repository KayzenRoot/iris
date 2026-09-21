"""The versioning law: history is append-only, meaning is pinned to a declared version, and nothing rewrites either.

§18 draws a hard line between *what an edit did* and *who is allowed to say it did it*. Two failures
sit on either side of that line. The first is a merge that invents a result: two branches moved one
path to two readings, and the tool that "resolved" it by picking the newer one shipped a decision
nobody made, which §7 forbids in as many words. The second is a roll-back that reaches into the past
and edits it: a restoration which rewrites a revision, or which revives the policy the older revision
was read under, silently undeats every rights and security decision taken since. Both are refused
structurally here. The merge analysis carries *both* readings of a dispute as two digests, and its
candidate merged state exists exactly when nothing is left to decide, so a divergent same-path edit
cannot be reported as a merge. A restoration is a new revision with a strictly greater ordinal whose
meaning must equal the older one's, and it cannot be built unless it names the schema, compiler,
profile and policy that interpreted it.

The third strand is §18's identity/provenance angle. Version strings are not decoration: the kernel
supports exactly one contract version and one schema version, refuses a foreign one by naming what it
accepts rather than coercing the bytes into the shape it knows, and pins every classification of an
edit to a versioned equivalence profile so that "the meaning did not move" is a claim a later reader
can re-check.

"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_intent.authority import AuthorityLevel
from iris_intent.briefs import BriefRevision, RevisionKind
from iris_intent.errors import (
    AdmissionRefusedError,
    AuthorityError,
    RefError,
    SchemaValidationError,
    StaleSemanticError,
    UnsupportedVersionError,
)
from iris_intent.fingerprints import ChangeKind, fingerprint_revision
from iris_intent.identity import RefKind
from iris_intent.merge import (
    MERGE_COMPILER_VERSION,
    BriefSemanticMergeAnalysis,
    MergeComponent,
    MergeComponentKind,
    MergeSide,
    RestorationRevision,
    RevisionClassification,
    analyze_semantic_merge,
    classify_revision,
    meanings_agree,
    restore_revision,
)
from iris_intent.migration import (
    MIGRATION_AXES,
    MIGRATION_COMPILER_VERSION,
    CompatibilityDeclaration,
    MigrationComponentKind,
    MigrationLoss,
    MigrationLossKind,
    MigrationReceipt,
    VersionVector,
    declare_compatible,
    migrate_revision,
    require_admissible,
    require_declared,
)
from iris_intent.serialization import (
    SerializationEnvelope,
    content_digest,
    deserialize,
    dumps,
    envelope_for,
    from_envelope,
    loads,
    record_kind,
    record_kinds,
    record_types,
    require_record_kind,
    serialize,
)
from iris_intent.versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    SUPPORTED_CONTRACT_VERSIONS,
    SUPPORTED_SCHEMA_VERSIONS,
    canonical_json,
    require_contract_version,
    require_schema_version,
)

from tests import m03_kernel_support as S

#: The four interpretation axes §19 names, pinned to the versions this kernel actually speaks.
def vector(**over: Any) -> Any:
    arguments: dict[str, str] = {
        "schema": SCHEMA_VERSION,
        "compiler": MIGRATION_COMPILER_VERSION,
        "profile": "v1",
        "policy": "1.0.0",
    }
    arguments.update(over)
    return VersionVector(**arguments)


def bumped(axis: str, value: str = "2.0.0") -> Any:
    """The same four versions with exactly one axis moved."""

    assert axis in MIGRATION_AXES
    return replace(vector(), **{axis: f"{getattr(vector(), axis)}-{value}"})


def envelope_over(payload: Any) -> Any:
    """Wrap a hand-written payload the way a foreign kernel would, digest included."""

    return SerializationEnvelope(
        schema_version=SCHEMA_VERSION,
        kind="BriefRevision",
        contract_version=CONTRACT_VERSION,
        payload=payload,
        payload_digest=content_digest(payload),
    )

#: The interpretation a restoration has to declare rather than inherit (§21).
RECOMPILED = {
    "schema": SCHEMA_VERSION,
    "compiler": MERGE_COMPILER_VERSION,
    "profile": "v1",
    "policy": "1.0.0",
}

OWNER = S.authority_ref(AuthorityLevel.HUMAN_OWNER.value)


def stamped(revision: Any) -> Any:
    """A revision's fingerprint under a stable id, which is what a path-level delta is taken from."""

    return S.fingerprint(revision, ident=f"fp.{revision.revision_id}")


def pair_delta(before: Any, after: Any, *, ident: str) -> Any:
    return S.delta(stamped(before), stamped(after), ident=ident)


def branch(number: int, *, logo: dict | None = None, tone: dict | None = None, **over: Any) -> Any:
    """A revision on the shared trunk carrying one reading per path."""

    return S.revision(
        number,
        (
            S.statement("st.mark", S.LOGO, value={"state": "on"} if logo is None else logo),
            S.statement("st.voice", S.TONE, value={"state": "on"} if tone is None else tone),
        ),
        **over,
    )


def merge(
    base: Any,
    left: Any,
    right: Any,
    *,
    ident: str,
    open_question_refs: Any = (),
    rule_classes: Any = None,
    graph: Any = None,
) -> Any:
    """Run the semantic merge reading the way a branch convergence would, from two deltas off one base."""

    return analyze_semantic_merge(
        analysis_id=f"ma.{ident}",
        base=base,
        left=left,
        right=right,
        left_delta=pair_delta(base, left, ident=f"delta.{ident}.left"),
        right_delta=pair_delta(base, right, ident=f"delta.{ident}.right"),
        open_question_refs=tuple(open_question_refs),
        graph=graph,
        rule_classes=rule_classes,
    )


def same_meaning_later(number: int, *, kind: str = RevisionKind.RESTORATION.value) -> Any:
    """A later revision holding exactly the meaning of an earlier one, which is what a restoration is."""

    return S.revision(number, (S.statement("st.mark", S.LOGO),), kind=kind)


class VersionPinning(unittest.TestCase):
    """§18 identity/revision/provenance: the kernel speaks one version and says which."""

    def test_the_kernel_admits_exactly_one_contract_and_one_schema_version(self) -> None:
        self.assertEqual(SUPPORTED_CONTRACT_VERSIONS, frozenset({CONTRACT_VERSION}))
        self.assertEqual(SUPPORTED_SCHEMA_VERSIONS, frozenset({SCHEMA_VERSION}))
        self.assertEqual(require_contract_version(CONTRACT_VERSION), CONTRACT_VERSION)
        self.assertEqual(require_schema_version(SCHEMA_VERSION), SCHEMA_VERSION)

    def test_a_foreign_schema_version_is_refused_naming_what_the_kernel_accepts(self) -> None:
        with self.assertRaises(UnsupportedVersionError) as caught:
            require_schema_version("iris-intent-schema-v0")
        message = str(caught.exception)
        self.assertIn("unsupported schema version", message)
        self.assertIn(SCHEMA_VERSION, message)

    def test_a_foreign_contract_version_is_not_coerced_into_the_current_one(self) -> None:
        for foreign in ("m03-contract-v0.9", "1.0", "v1", "m03-contract-v2.0"):
            with self.subTest(version=foreign):
                with self.assertRaises(UnsupportedVersionError) as caught:
                    require_contract_version(foreign)
                self.assertIn("unsupported contract version", str(caught.exception))
                self.assertNotIn(foreign, SUPPORTED_CONTRACT_VERSIONS)

    def test_an_unsupported_version_is_not_a_schema_complaint_the_caller_might_retry(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            require_contract_version("m03-contract-v9.9")
        self.assertTrue(issubclass(UnsupportedVersionError, Exception))
        self.assertFalse(issubclass(UnsupportedVersionError, SchemaValidationError))
        with self.assertRaises(SchemaValidationError):
            require_contract_version("")
        with self.assertRaises(SchemaValidationError):
            require_contract_version("m03-contract-v1.0 " * 30)


class HistoryClasses(unittest.TestCase):
    """§18's versioning bullets: say what an edit did, from the two records and not from a commit note."""

    def setUp(self) -> None:
        self.first, self.second, self.third = S.revision_chain((1, 2, 3))

    def test_a_revision_that_moves_a_path_is_a_semantic_change(self) -> None:
        outcome = classify_revision(self.first, self.second)
        self.assertIs(outcome, RevisionClassification.SEMANTIC_CHANGE)
        self.assertTrue(outcome.invalidates_compiled_artifacts)
        self.assertFalse(outcome.preserves_semantic_fingerprint)

    def test_a_revision_that_only_adds_a_raw_input_is_a_source_only_change(self) -> None:
        quieter = S.revision(
            4,
            tuple(self.third.statements),
            sources=[
                S.raw_source(source_id="src.brief"),
                S.raw_source(source_id="src.client.reply"),
            ],
        )
        self.assertTrue(meanings_agree(self.third, quieter))
        outcome = classify_revision(self.third, quieter)
        self.assertIs(outcome, RevisionClassification.SOURCE_ONLY_CHANGE)
        self.assertTrue(outcome.preserves_semantic_fingerprint)
        self.assertFalse(outcome.invalidates_compiled_artifacts)

    def test_a_meaningful_edit_under_a_moved_policy_is_reported_as_a_policy_change(self) -> None:
        same = S.revision(2, tuple(self.first.statements))
        self.assertTrue(meanings_agree(self.first, same))
        self.assertIs(
            classify_revision(self.first, same, policy_context_changed=True),
            RevisionClassification.POLICY_CONTEXT_CHANGE,
        )
        self.assertTrue(RevisionClassification.POLICY_CONTEXT_CHANGE.invalidates_compiled_artifacts)

    def test_a_merge_is_not_reclassified_by_the_fact_that_it_reproduced_the_base(self) -> None:
        replayed = S.revision(4, tuple(self.first.statements))
        self.assertIs(
            classify_revision(self.first, replayed, is_merge=True),
            RevisionClassification.MERGE_REVISION,
        )
        self.assertIs(
            classify_revision(self.first, replayed, is_restoration=True),
            RevisionClassification.RESTORATION_REVISION,
        )
        self.assertIs(
            classify_revision(self.first, replayed, is_migration=True),
            RevisionClassification.MIGRATION_REVISION,
        )
        for governed in (
            RevisionClassification.MERGE_REVISION,
            RevisionClassification.RESTORATION_REVISION,
            RevisionClassification.MIGRATION_REVISION,
        ):
            self.assertTrue(governed.created_by_governance)
            self.assertTrue(governed.invalidates_compiled_artifacts)
        self.assertFalse(RevisionClassification.SEMANTIC_CHANGE.created_by_governance)

    def test_one_revision_may_not_be_created_by_two_governance_events_at_once(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            classify_revision(self.first, self.second, is_merge=True, is_migration=True)
        self.assertIn("two governance events", str(caught.exception))

    def test_an_earlier_revision_cannot_be_classified_as_an_edit_of_a_later_one(self) -> None:
        with self.assertRaises(StaleSemanticError) as caught:
            classify_revision(self.third, self.first)
        self.assertIn("append-only", str(caught.exception))
        with self.assertRaises(StaleSemanticError):
            classify_revision(self.second, self.second)

    def test_a_revision_from_another_brief_cannot_be_read_against_this_one(self) -> None:
        other = S.revision(9, (S.statement("st.other", S.LOGO),), brief_id="brief.other.client")
        with self.assertRaises(RefError) as caught:
            classify_revision(self.first, other)
        self.assertIn("brief.other.client", str(caught.exception))
        with self.assertRaises(RefError):
            meanings_agree(self.first, other)

    def test_meanings_agree_reads_meaning_and_not_bytes(self) -> None:
        moved_source = S.revision(
            2,
            tuple(self.first.statements),
            sources=[S.raw_source(source_id="src.brief"), S.raw_source(source_id="src.channel")],
        )
        self.assertNotEqual(self.first.digest(), moved_source.digest())
        self.assertTrue(meanings_agree(self.first, moved_source))
        with self.assertRaises(SchemaValidationError):
            meanings_agree(self.first, S.model(self.second))  # type: ignore[arg-type]


class RestorationAddsARevision(unittest.TestCase):
    """§21, proof 18: rolling back means coming after, under today's policy, and saying so."""

    def test_a_restoration_is_admitted_as_a_later_revision_holding_the_older_meaning(self) -> None:
        older = same_meaning_later(3, kind=RevisionKind.INITIAL.value)
        newer = same_meaning_later(9)
        record = restore_revision(
            restoration_id="rst.mark",
            new_revision=newer,
            restores_from=older,
            decided_by=OWNER,
            reason="the client wants the earlier mark reading back, with every later decision kept",
            current_policy_refs=(S.policy_ref(),),
            recompiled_with=RECOMPILED,
            profile=S.equivalence_profile(),
        )
        self.assertIsInstance(record, RestorationRevision)
        self.assertEqual(record.new_revision_ref.ref_id, "rev.9")
        self.assertEqual(record.restores_from.ref_id, "rev.3")
        self.assertNotEqual(record.new_revision_ref.text, record.restores_from.text)
        self.assertIs(RestorationRevision.rewrites_history, False)
        self.assertIs(RestorationRevision.revives_old_policy, False)
        self.assertIs(RestorationRevision.m02_owns_production_rollback, True)
        self.assertEqual(record.ref.kind, RefKind.REVISION.value)
        self.assertEqual(len(record.restoration_digest), S.DIGEST_LEN)

    def test_a_restoration_that_changes_the_meaning_is_refused_as_an_edit(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            restore_revision(
                restoration_id="rst.edit",
                new_revision=S.revision(9, (S.statement("st.other", S.LOGO, mandatory=True),)),
                restores_from=same_meaning_later(3),
                decided_by=OWNER,
                reason="the same mark, plus a change nobody is being asked to approve",
                current_policy_refs=(S.policy_ref(),),
                recompiled_with=RECOMPILED,
                profile=S.equivalence_profile(),
            )
        self.assertIn("edit rather than a restoration", str(caught.exception))

    def test_a_restoration_may_not_write_backwards_or_onto_another_brief(self) -> None:
        newer = same_meaning_later(9)
        with self.assertRaises(StaleSemanticError) as backwards:
            restore_revision(
                restoration_id="rst.backwards",
                new_revision=same_meaning_later(2),
                restores_from=newer,
                decided_by=OWNER,
                reason="unwinding the history rather than adding to it",
                current_policy_refs=(S.policy_ref(),),
                recompiled_with=RECOMPILED,
                profile=S.equivalence_profile(),
            )
        self.assertIn("append-only", str(backwards.exception))
        foreign = S.revision(9, (S.statement("st.mark", S.LOGO),), brief_id="brief.other.client")
        with self.assertRaises(RefError) as cross_brief:
            restore_revision(
                restoration_id="rst.foreign",
                new_revision=foreign,
                restores_from=newer,
                decided_by=OWNER,
                reason="returning a brief to another client's meaning",
                current_policy_refs=(S.policy_ref(),),
                recompiled_with=RECOMPILED,
                profile=S.equivalence_profile(),
            )
        self.assertIn("its own meaning", str(cross_brief.exception))

    def test_a_restoration_must_name_every_interpretation_it_recompiled_under(self) -> None:
        for missing in sorted(RECOMPILED):
            with self.subTest(missing=missing):
                withheld = {key: value for key, value in RECOMPILED.items() if key != missing}
                with self.assertRaises(SchemaValidationError) as caught:
                    restore_revision(
                        restoration_id=f"rst.no.{missing}",
                        new_revision=same_meaning_later(9),
                        restores_from=same_meaning_later(3),
                        decided_by=OWNER,
                        reason="the earlier reading, under settings this record leaves out",
                        current_policy_refs=(S.policy_ref(),),
                        recompiled_with=withheld,
                        profile=S.equivalence_profile(),
                    )
                self.assertIn(f"which {missing} interpreted it", str(caught.exception))

    def test_a_restoration_may_not_declare_an_interpretation_component_that_is_not_one(self) -> None:
        smuggled = dict(RECOMPILED, history="rev.3")
        with self.assertRaises(SchemaValidationError) as caught:
            restore_revision(
                restoration_id="rst.smuggled",
                new_revision=same_meaning_later(9),
                restores_from=same_meaning_later(3),
                decided_by=OWNER,
                reason="an older history pin dressed up as an interpretation setting",
                current_policy_refs=(S.policy_ref(),),
                recompiled_with=smuggled,
                profile=S.equivalence_profile(),
            )
        self.assertIn("interpretation components", str(caught.exception))

    def test_a_restoration_cannot_document_an_equivalence_it_did_not_perform(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            restore_revision(
                restoration_id="rst.wrong.profile",
                new_revision=same_meaning_later(9),
                restores_from=same_meaning_later(3),
                decided_by=OWNER,
                reason="the reading was taken under v2 but the receipt files v1",
                current_policy_refs=(S.policy_ref(),),
                recompiled_with=dict(RECOMPILED, profile="v9"),
                profile=S.equivalence_profile(),
            )
        self.assertIn("did not perform", str(caught.exception))

    def test_an_inferred_actor_may_not_restore_a_prior_meaning_on_its_own_assertion(self) -> None:
        for level in (
            AuthorityLevel.MODEL_INFERRED.value,
            AuthorityLevel.PROJECT_RECORD.value,
            AuthorityLevel.TEAM_ASSERTED.value,
            AuthorityLevel.RETRIEVED.value,
        ):
            with self.subTest(level=level):
                with self.assertRaises(AuthorityError) as caught:
                    restore_revision(
                        restoration_id=f"rst.{level}",
                        new_revision=same_meaning_later(9),
                        restores_from=same_meaning_later(3),
                        decided_by=S.authority_ref(level),
                        reason="the earlier wording tested better, so it goes back",
                        current_policy_refs=(S.policy_ref(),),
                        recompiled_with=RECOMPILED,
                        profile=S.equivalence_profile(),
                    )
                self.assertIn("may not restore a prior meaning", str(caught.exception))

    def test_a_restoration_cannot_cite_the_revision_it_restores_as_its_own_new_one(self) -> None:
        older = same_meaning_later(3)
        with self.assertRaises(SchemaValidationError) as caught:
            RestorationRevision(
                restoration_id="rst.noop",
                brief_ref=older.brief_ref,
                new_revision_ref=older.revision_ref,
                restores_from=older.revision_ref,
                reason="a no-op filed as an event",
                decided_by=OWNER,
                current_policy_refs=(S.policy_ref(),),
                recompiled_with=RECOMPILED,
            )
        self.assertIn("no-op", str(caught.exception))


class ThreeWaySemanticMerge(unittest.TestCase):
    """§16, proofs 13-14: M03 reads the two branches; M02 owns the merge."""

    def setUp(self) -> None:
        self.base = branch(1)
        self.left = branch(2, logo={"state": "off"})
        self.right = branch(3, logo={"state": "reversed"})

    def test_two_branches_that_moved_one_path_apart_are_reported_as_a_dispute(self) -> None:
        analysis = merge(self.base, self.left, self.right, ident="divergent")
        self.assertEqual(
            [item.kind for item in analysis.components], [MergeComponentKind.CONFLICTING.value]
        )
        component = analysis.components[0]
        self.assertEqual(component.side, MergeSide.BOTH.value)
        self.assertEqual(component.semantic_paths, (S.LOGO,))
        left_change = pair_delta(self.base, self.left, ident="check.left").changes[0]
        right_change = pair_delta(self.base, self.right, ident="check.right").changes[0]
        self.assertEqual(component.before_digest, left_change.before_digest)
        self.assertEqual(component.after_digest, left_change.after_digest)
        self.assertEqual(component.other_digest, right_change.after_digest)
        self.assertNotEqual(component.after_digest, component.other_digest)
        self.assertIs(component.decides_nothing, True)
        self.assertTrue(component.needs_a_decision)
        self.assertFalse(component.kind_enum.ships_in_the_candidate)

    def test_a_divergent_merge_hands_over_no_candidate_state(self) -> None:
        analysis = merge(self.base, self.left, self.right, ident="divergent")
        self.assertIsNone(analysis.merged_candidate_digest)
        self.assertFalse(analysis.clean)
        self.assertEqual(analysis.paths_in_dispute, (S.LOGO,))
        self.assertEqual(len(analysis.conflicting_changes), 1)
        with self.assertRaises(SchemaValidationError) as caught:
            replace(analysis, merged_candidate_digest=S.digest("assembled"))
        self.assertIn("a decision nobody made", str(caught.exception))

    def test_disjoint_edits_are_each_taken_without_a_decision(self) -> None:
        quieter_right = branch(3, tone={"state": "quieter"})
        analysis = merge(self.base, self.left, quieter_right, ident="disjoint")
        self.assertTrue(analysis.clean)
        self.assertIsNotNone(analysis.merged_candidate_digest)
        self.assertEqual(
            sorted(item.side for item in analysis.components),
            sorted([MergeSide.LEFT.value, MergeSide.RIGHT.value]),
        )
        self.assertEqual(len(analysis.safe_changes), 2)
        self.assertEqual(analysis.conflicting_changes, ())
        for component in analysis.components:
            self.assertTrue(component.kind_enum.ships_in_the_candidate)
            self.assertEqual(len(component.semantic_paths), 1)
        self.assertEqual({item.semantic_paths[0] for item in analysis.safe_changes}, {S.LOGO, S.TONE})

    def test_both_sides_reaching_the_same_reading_are_taken_once(self) -> None:
        same_right = branch(3, logo={"state": "off"})
        analysis = merge(self.base, self.left, same_right, ident="same")
        self.assertEqual(len(analysis.equivalent_changes), 1)
        self.assertEqual(analysis.conflicting_changes, ())
        component = analysis.equivalent_changes[0]
        self.assertEqual(component.kind, MergeComponentKind.EQUIVALENT.value)
        self.assertEqual(component.side, MergeSide.BOTH.value)
        self.assertFalse(component.needs_a_decision)
        self.assertTrue(analysis.clean)
        self.assertIsNotNone(analysis.merged_candidate_digest)
        self.assertIn("takes it once", component.reason)

    def test_an_open_question_on_both_branches_blocks_the_candidate(self) -> None:
        analysis = merge(
            self.base,
            branch(2, tone={"state": "quieter"}),
            branch(3, logo={"state": "reversed"}),
            ident="questions",
            open_question_refs=(S.ref(RefKind.OPEN_QUESTION.value, "q.mark.ownership"),),
        )
        self.assertEqual(len(analysis.unresolved_questions), 1)
        self.assertTrue(analysis.needs_human_decision)
        self.assertFalse(analysis.clean)
        self.assertIsNone(analysis.merged_candidate_digest)
        question = analysis.unresolved_questions[0]
        self.assertEqual(question.subject_ids, ("q.mark.ownership",))
        self.assertEqual(question.side, MergeSide.BOTH.value)
        self.assertEqual(question.semantic_paths, ())

    def test_the_reading_is_deterministic_and_addresses_itself_to_m02(self) -> None:
        first = merge(self.base, self.left, self.right, ident="stable")
        second = merge(self.base, self.left, self.right, ident="stable")
        self.assertEqual(first.analysis_digest, second.analysis_digest)
        self.assertEqual(first.ref.text, second.ref.text)
        self.assertEqual(
            [item.component_id for item in first.components],
            [item.component_id for item in second.components],
        )
        self.assertIs(BriefSemanticMergeAnalysis.decides_merge, False)
        self.assertIs(BriefSemanticMergeAnalysis.implements_merge_mechanics, False)
        self.assertIs(BriefSemanticMergeAnalysis.m02_owns_branch_history, True)
        self.assertIs(BriefSemanticMergeAnalysis.prefers_recency, False)
        self.assertIs(BriefSemanticMergeAnalysis.uses_priority, False)
        self.assertEqual(first.ref.kind, RefKind.MERGE_ANALYSIS.value)
        self.assertEqual(
            (first.schema_version, first.contract_version, first.compiler_version),
            (SCHEMA_VERSION, CONTRACT_VERSION, MERGE_COMPILER_VERSION),
        )

    def test_a_merge_reads_the_branches_through_the_delta_and_not_through_a_commit_note(self) -> None:
        analysis = merge(self.base, self.left, self.right, ident="components")
        self.assertEqual(
            [item.change_kinds for item in analysis.components],
            [(ChangeKind.REPREDICATED.value,)],
        )
        self.assertEqual(analysis.left_delta.touched_paths, (S.LOGO,))
        self.assertEqual(analysis.right_delta.touched_paths, (S.LOGO,))
        self.assertTrue(analysis.left_delta.correctness_relevant)
        self.assertEqual(
            analysis.components[0].change_kinds, (analysis.left_delta.changes[0].kind,)
        )


class MergeRefusals(unittest.TestCase):
    """The shape of a three-way reading that would be a merge pretending to be an analysis."""

    def setUp(self) -> None:
        self.base = branch(1)
        self.left = branch(2, logo={"state": "off"})
        self.right = branch(3, logo={"state": "reversed"})
        self.analysis = merge(self.base, self.left, self.right, ident="refusals")

    def test_a_base_nobody_branched_from_is_refused(self) -> None:
        with self.assertRaises(StaleSemanticError) as caught:
            replace(self.analysis, base_revision_number=4)
        self.assertIn("common ancestor", str(caught.exception))

    def test_two_deltas_from_different_bases_are_two_changelogs(self) -> None:
        with self.assertRaises(StaleSemanticError) as caught:
            replace(
                self.analysis,
                right_delta=pair_delta(branch(1, tone={"state": "quieter"}), self.right, ident="other"),
            )
        self.assertIn("three-way merge", str(caught.exception))

    def test_a_merge_may_not_compare_the_intent_layer_against_the_rule_layer(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            replace(self.analysis, right_delta=replace(self.analysis.right_delta, subject_kind="CONSTRAINT"))
        self.assertIn("two layers", str(caught.exception))

    def test_a_policy_claim_about_a_subject_this_merge_never_moved_is_refused(self) -> None:
        with self.assertRaises(RefError) as caught:
            merge(
                self.base,
                self.left,
                self.right,
                ident="stray",
                rule_classes={"cn.not.here": "brand.logo"},
            )
        self.assertIn("neither delta moved", str(caught.exception))

    def test_the_three_revisions_must_belong_to_one_brief(self) -> None:
        with self.assertRaises(RefError) as caught:
            merge(
                self.base,
                self.left,
                branch(3, logo={"state": "reversed"}, brief_id="brief.other.client"),
                ident="cross.brief",
            )
        self.assertIn("no common base", str(caught.exception))

    def test_a_component_that_pretends_two_sides_agree_is_refused(self) -> None:
        shared = S.digest("one reading")
        with self.assertRaises(SchemaValidationError) as invented:
            MergeComponent(
                component_id="merge.invented",
                kind=MergeComponentKind.CONFLICTING.value,
                side=MergeSide.BOTH.value,
                semantic_paths=(S.LOGO,),
                after_digest=shared,
                other_digest=shared,
                reason="a dispute staged to stop a merge that could have gone through",
            )
        self.assertIn("one reading twice", str(invented.exception))
        with self.assertRaises(SchemaValidationError) as one_sided:
            MergeComponent(
                component_id="merge.half",
                kind=MergeComponentKind.EQUIVALENT.value,
                side=MergeSide.LEFT.value,
                semantic_paths=(S.LOGO,),
                reason="an equivalence claim about a branch that spoke alone",
            )
        self.assertIn("needs both sides", str(one_sided.exception))
        with self.assertRaises(SchemaValidationError) as both_sides:
            MergeComponent(
                component_id="merge.too.safe",
                kind=MergeComponentKind.NON_OVERLAPPING_SAFE.value,
                side=MergeSide.BOTH.value,
                semantic_paths=(S.LOGO,),
                reason="safe on one side, or equivalent on two, and this claims both at once",
            )
        self.assertIn("one side only", str(both_sides.exception))

    def test_a_clean_reading_may_not_withhold_the_candidate_it_promised(self) -> None:
        clean = merge(self.base, self.left, branch(3, tone={"state": "quieter"}), ident="clean")
        self.assertTrue(clean.clean)
        with self.assertRaises(SchemaValidationError) as caught:
            replace(clean, merged_candidate_digest=None)
        self.assertIn("withholds a candidate", str(caught.exception))

    def test_repeated_component_ids_are_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            replace(self.analysis, components=(self.analysis.components[0],) * 2)
        self.assertIn("repeats component ids", str(caught.exception))


class MigrationAddsATarget(unittest.TestCase):
    """§19-§20, proof 16: a version bump reads the old revision and adds a new one."""

    def setUp(self) -> None:
        self.source = S.revision(
            3,
            (
                S.statement("st.mark", S.LOGO, mandatory=True),
                S.statement("st.voice", S.TONE),
            ),
        )
        self.target = S.revision(
            4,
            (
                S.statement("st.mark", S.LOGO, mandatory=True, value={"state": "re-expressed"}),
                S.statement("st.voice", S.TONE),
            ),
        )

    def loss(
        self,
        *,
        ident: str = "loss.mark",
        path: str = S.LOGO,
        statement_id: str = "st.mark",
        mandatory: bool | None = None,
    ) -> Any:
        found = self.source.statement(statement_id)
        return MigrationLoss(
            loss_id=ident,
            semantic_path=path,
            element_ref=found.statement_ref,
            kind=MigrationLossKind.UNREPRESENTABLE.value,
            mandatory=found.mandatory if mandatory is None else mandatory,
            detail="the target schema has no construct that carries this reading",
        )

    def migrate(
        self,
        *,
        ident: str = "mig.recompile",
        component: str = "COMPILER",
        axis: str | None = None,
        losses: Any = (),
    ) -> Any:
        return migrate_revision(
            migration_id=ident,
            source=self.source,
            target=self.target,
            source_versions=vector(),
            target_versions=bumped(axis or component.lower()),
            component=component,
            validation_refs=(S.ref(RefKind.SOURCE.value, "val.m03.upgrade"),),
            losses=tuple(losses),
        )

    def test_a_migration_names_both_revisions_and_rewrites_neither(self) -> None:
        receipt = self.migrate()
        self.assertIsInstance(receipt, MigrationReceipt)
        self.assertEqual(receipt.source_revision_ref.ref_id, "rev.3")
        self.assertEqual(receipt.target_revision_ref.ref_id, "rev.4")
        self.assertNotEqual(receipt.source_revision_ref.text, receipt.target_revision_ref.text)
        self.assertIs(MigrationReceipt.rewrites_source, False)
        self.assertIs(MigrationReceipt.admits_itself, False)
        self.assertEqual(receipt.source_versions, vector())
        self.assertEqual(receipt.moved_axes, (MigrationComponentKind.COMPILER,))
        self.assertEqual(receipt.transformed_paths, (S.LOGO,))
        self.assertEqual(receipt.unchanged_paths, (S.TONE,))
        self.assertEqual(receipt.accounts_for(S.LOGO), "TRANSFORMED")
        self.assertEqual(receipt.accounts_for(S.TONE), "UNCHANGED")
        self.assertEqual(receipt.accounts_for(S.ICON), "ABSENT")
        self.assertTrue(receipt.changed)
        self.assertFalse(receipt.blocks_admission)
        self.assertEqual(receipt.ref.kind, RefKind.MIGRATION.value)
        self.assertEqual(
            require_admissible(receipt, source=self.source, target=self.target), receipt
        )

    def test_the_migrated_result_is_classified_as_a_new_revision(self) -> None:
        receipt = self.migrate()
        self.assertEqual(
            classify_revision(self.source, self.target, is_migration=True),
            RevisionClassification.MIGRATION_REVISION,
        )
        self.assertGreater(self.target.revision_number, self.source.revision_number)
        self.assertNotEqual(receipt.source_fingerprint_digest, receipt.target_fingerprint_digest)
        self.assertEqual(len(receipt.source_fingerprint_digest), S.DIGEST_LEN)

    def test_a_migration_into_the_same_revision_is_a_rewrite_and_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            replace(receipt := self.migrate(), target_revision_ref=receipt.source_revision_ref)
        self.assertIn("rewrite of an admitted record", str(caught.exception))

    def test_a_migration_may_not_run_backwards_or_across_briefs(self) -> None:
        with self.assertRaises(StaleSemanticError) as backwards:
            migrate_revision(
                migration_id="mig.backwards",
                source=self.target,
                target=self.source,
                source_versions=vector(),
                target_versions=bumped("compiler"),
                component="COMPILER",
                validation_refs=(S.ref(RefKind.SOURCE.value, "val.m03.upgrade"),),
            )
        self.assertIn("append-only", str(backwards.exception))
        foreign = S.revision(9, tuple(self.source.statements), brief_id="brief.other.client")
        with self.assertRaises(RefError) as cross_brief:
            migrate_revision(
                migration_id="mig.foreign",
                source=self.source,
                target=foreign,
                source_versions=vector(),
                target_versions=bumped("compiler"),
                component="COMPILER",
                validation_refs=(S.ref(RefKind.SOURCE.value, "val.m03.upgrade"),),
            )
        self.assertIn("migrates its own meaning", str(cross_brief.exception))

    def test_a_receipt_cannot_credit_an_axis_that_never_moved(self) -> None:
        with self.assertRaises(UnsupportedVersionError) as caught:
            self.migrate(component="POLICY", axis="compiler")
        self.assertIn("moved between the two vectors", str(caught.exception))
        with self.assertRaises(UnsupportedVersionError) as nothing:
            migrate_revision(
                migration_id="mig.stillborn",
                source=self.source,
                target=self.target,
                source_versions=vector(),
                target_versions=vector(),
                component="SCHEMA",
                validation_refs=(S.ref(RefKind.SOURCE.value, "val.m03.upgrade"),),
            )
        self.assertIn("nothing moved", str(nothing.exception))

    def test_a_path_may_not_be_reported_as_both_moved_and_untouched(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            replace(self.migrate(), transformed_paths=(S.TONE,), unchanged_paths=(S.TONE,))
        self.assertIn("both transformed and unchanged", str(caught.exception))

    def test_a_mandatory_loss_is_recorded_and_refuses_admission(self) -> None:
        receipt = self.migrate(losses=(self.loss(),))
        self.assertEqual(receipt.lost_paths, (S.LOGO,))
        self.assertTrue(receipt.blocks_admission)
        self.assertEqual(len(receipt.mandatory_losses), 1)
        self.assertEqual(receipt.mandatory_losses[0].element_ref.ref_id, "st.mark")
        with self.assertRaises(AdmissionRefusedError) as caught:
            require_admissible(receipt, source=self.source, target=self.target)
        message = str(caught.exception)
        self.assertIn("lost mandatory elements", message)
        self.assertIn(S.LOGO, message)
        self.assertIn("st.mark", message)

    def test_a_loss_must_point_at_a_statement_the_source_actually_carries(self) -> None:
        with self.assertRaises(RefError) as absent:
            self.migrate(
                losses=(
                    replace(
                        self.loss(),
                        element_ref=S.ref(RefKind.STATEMENT.value, "st.not.here"),
                    ),
                )
            )
        self.assertIn("does not carry", str(absent.exception))
        with self.assertRaises(RefError) as unpinned:
            self.migrate(
                losses=(
                    replace(
                        self.loss(),
                        element_ref=S.ref(RefKind.STATEMENT.value, "st.mark", digest_value=S.digest("other")),
                    ),
                )
            )
        self.assertIn("digests as", str(unpinned.exception))
        with self.assertRaises(SchemaValidationError) as wrong_kind:
            self.migrate(
                losses=(
                    replace(
                        self.loss(),
                        element_ref=S.ref(RefKind.CONSTRAINT.value, "cn.mark"),
                    ),
                )
            )
        self.assertIn("not an admitted statement", str(wrong_kind.exception))

    def test_a_loss_understating_mandatory_or_sitting_on_an_unchanged_path_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as understated:
            self.migrate(losses=(self.loss(mandatory=False),))
        self.assertIn("re-derived from the source", str(understated.exception))
        with self.assertRaises(SchemaValidationError) as misplaced:
            self.migrate(losses=(self.loss(ident="loss.voice", path=S.TONE, statement_id="st.voice"),))
        self.assertIn("declares unchanged", str(misplaced.exception))

    def test_admission_re_checks_the_record_it_was_handed_rather_than_trusting_the_paper(self) -> None:
        receipt = self.migrate()
        with self.assertRaises(RefError) as wrong_source:
            require_admissible(receipt, source=self.target)
        self.assertIn("different source", str(wrong_source.exception))
        with self.assertRaises(RefError) as wrong_target:
            require_admissible(receipt, source=self.source, target=self.source)
        self.assertIn("does not describe target revision", str(wrong_target.exception))
        forged = replace(receipt, source_fingerprint_digest=S.digest("looked fine at the time"))
        with self.assertRaises(StaleSemanticError) as stale:
            require_admissible(forged, source=self.source)
        self.assertIn("not the record being admitted against", str(stale.exception))
        with self.assertRaises(SchemaValidationError):
            require_admissible(receipt, source="rev.3")  # type: ignore[arg-type]


class CompatibilityIsDeclaredNotAssumed(unittest.TestCase):
    """§19's other route: an axis moved and the admitted meaning demonstrably did not."""

    def setUp(self) -> None:
        self.revision = S.revision(3, (S.statement("st.mark", S.LOGO),))

    def declare(self, *, axes: Any = None, declarer: Any = OWNER, **over: Any) -> Any:
        arguments: dict[str, Any] = {
            "declaration_id": "cmp.compiler",
            "revision": self.revision,
            "from_versions": vector(),
            "to_versions": bumped("compiler"),
            "declared_by": declarer,
            "evidence_refs": (S.policy_ref(),),
        }
        if axes is not None:
            arguments["axes"] = tuple(axes)
        arguments.update(over)
        return declare_compatible(**arguments)

    def test_a_declared_compatibility_keeps_the_revision_in_service_without_creating_one(self) -> None:
        declaration = self.declare()
        self.assertIsInstance(declaration, CompatibilityDeclaration)
        self.assertIs(CompatibilityDeclaration.creates_no_revision, True)
        self.assertIs(CompatibilityDeclaration.meaning_changed, False)
        self.assertIs(CompatibilityDeclaration.rewrites_source, False)
        self.assertEqual(declaration.axes, (MigrationComponentKind.COMPILER.value,))
        self.assertTrue(declaration.covers("COMPILER"))
        self.assertFalse(declaration.covers("POLICY"))
        self.assertEqual(declaration.revision_ref.ref_id, "rev.3")
        self.assertEqual(
            declaration.semantic_digest,
            fingerprint_revision(self.revision).semantic_digest,
        )
        self.assertIs(require_declared(declaration, revision=self.revision), declaration)

    def test_a_declaration_about_no_movement_is_noise(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            self.declare(to_versions=vector())
        self.assertIn("identical version vectors", str(caught.exception))

    def test_an_axis_left_out_of_a_compatibility_claim_is_an_axis_someone_assumes_was_checked(self) -> None:
        with self.assertRaises(SchemaValidationError) as too_narrow:
            self.declare(axes=(MigrationComponentKind.POLICY.value,))
        self.assertIn("an axis left out of a compatibility claim", str(too_narrow.exception))
        broadened = self.declare(
            to_versions=replace(bumped("compiler"), policy="2.0.0"),
            axes=(
                MigrationComponentKind.COMPILER.value,
                MigrationComponentKind.POLICY.value,
            ),
        )
        self.assertEqual(
            broadened.axes,
            (MigrationComponentKind.COMPILER.value, MigrationComponentKind.POLICY.value),
        )

    def test_compatibility_is_a_governed_act_and_not_an_observation_about_ones_own_inputs(self) -> None:
        with self.assertRaises(AuthorityError) as unsigned:
            self.declare(declarer=None)
        self.assertIn("no declarer", str(unsigned.exception))
        for level in (
            AuthorityLevel.MODEL_INFERRED.value,
            AuthorityLevel.PROJECT_RECORD.value,
            AuthorityLevel.RETRIEVED.value,
        ):
            with self.subTest(level=level):
                with self.assertRaises(AuthorityError) as caught:
                    self.declare(declarer=S.authority_ref(level))
                self.assertIn("may not declare an older reading compatible", str(caught.exception))
        self.assertEqual(
            self.declare(
                declarer=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value)
            ).declared_by.authority,
            AuthorityLevel.GOVERNED_POLICY.value,
        )

    def test_a_declaration_needs_evidence_and_a_revision_it_covers(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            self.declare(evidence_refs=())
        self.assertIn("at least 1 bound ref", str(caught.exception))
        other = S.revision(4, (S.statement("st.mark", S.LOGO),))
        with self.assertRaises(RefError) as wrong_revision:
            require_declared(self.declare(), revision=other)
        self.assertIn("covers a different revision", str(wrong_revision.exception))

    def test_a_pinned_digest_is_re_derived_instead_of_trusted(self) -> None:
        invented = replace(self.declare(), semantic_digest=S.digest("checked once, long ago"))
        with self.assertRaises(StaleSemanticError) as caught:
            require_declared(invented, revision=self.revision)
        self.assertIn("is not the one on file", str(caught.exception))
        with self.assertRaises(AuthorityError):
            CompatibilityDeclaration(
                declaration_id="cmp.unsigned",
                brief_ref=self.revision.brief_ref,
                revision_ref=self.revision.revision_ref,
                from_versions=vector(),
                to_versions=bumped("compiler"),
                semantic_digest=S.digest("x"),
                evidence_refs=(S.policy_ref(),),
            )

    def test_the_version_vector_is_four_axes_or_it_is_not_a_vector(self) -> None:
        plain = vector()
        self.assertEqual(
            sorted(plain.as_mapping()),
            ["compiler", "policy", "profile", "schema"],
        )
        self.assertTrue(plain.same_as(vector()))
        self.assertEqual(plain.moved_axes(bumped("policy")), (MigrationComponentKind.POLICY,))
        self.assertEqual(plain.moved_axes(plain), ())
        self.assertEqual(len(plain.vector_digest), S.DIGEST_LEN)
        self.assertNotEqual(plain.vector_digest, bumped("schema").vector_digest)
        with self.assertRaises(SchemaValidationError):
            VersionVector(schema="", compiler="c", profile="p", policy="q")
        with self.assertRaises(TypeError):
            VersionVector(schema=SCHEMA_VERSION, compiler="c", profile="p")  # type: ignore[call-arg]


class TransportPinsWhatAPayloadIs(unittest.TestCase):
    """§18 identity/provenance: nothing is decoded before its version and kind are checked."""

    def setUp(self) -> None:
        self.revision = S.revision(3, (S.statement("st.mark", S.LOGO),))

    def test_a_record_leaves_the_kernel_pinned_to_the_schema_it_understands(self) -> None:
        envelope = envelope_for(self.revision)
        self.assertEqual(envelope.schema_version, SCHEMA_VERSION)
        self.assertEqual(envelope.contract_version, CONTRACT_VERSION)
        self.assertEqual(envelope.kind, "BriefRevision")
        self.assertIs(envelope.record_type, BriefRevision)
        self.assertEqual(envelope.payload_digest, content_digest(envelope.payload))
        self.assertEqual(deserialize(envelope), envelope.decode())
        self.assertIsInstance(from_envelope(envelope.to_payload()), BriefRevision)
        self.assertEqual(loads(dumps(self.revision)).revision_id, self.revision.revision_id)
        self.assertEqual(loads(dumps(self.revision)).digest(), self.revision.digest())

    def test_a_foreign_schema_version_is_refused_by_name_instead_of_being_coerced(self) -> None:
        payload = self.revision.to_payload()
        with self.assertRaises(UnsupportedVersionError) as caught:
            SerializationEnvelope(
                schema_version="iris-intent-schema-v0",
                kind="BriefRevision",
                contract_version=CONTRACT_VERSION,
                payload=payload,
                payload_digest=content_digest(payload),
            )
        message = str(caught.exception)
        self.assertIn("unsupported schema version", message)
        self.assertIn(SCHEMA_VERSION, message)

    def test_a_record_stamped_with_a_foreign_contract_version_cannot_leave_the_kernel(self) -> None:
        receipt = migrate_revision(
            migration_id="mig.foreign.stamp",
            source=S.revision(3, (S.statement("st.mark", S.LOGO),)),
            target=S.revision(4, (S.statement("st.mark", S.LOGO, value={"state": "off"}),)),
            source_versions=vector(),
            target_versions=bumped("schema"),
            component="SCHEMA",
            validation_refs=(S.ref(RefKind.SOURCE.value, "val.m03.upgrade"),),
        )
        self.assertEqual(receipt.contract_version, CONTRACT_VERSION)
        envelope = envelope_for(receipt)
        self.assertEqual(envelope.contract_version, CONTRACT_VERSION)
        with self.assertRaises(UnsupportedVersionError) as caught:
            envelope_for(replace(receipt, contract_version="m03-contract-v0.9"))
        self.assertIn("unsupported contract version", str(caught.exception))
        # The schema pin is the envelope's own claim about what read the bytes, so a record carrying a
        # foreign schema stamp still leaves inside this kernel's schema version.
        self.assertEqual(
            envelope_for(replace(receipt, schema_version="iris-intent-schema-v9")).schema_version,
            SCHEMA_VERSION,
        )

    def test_an_unknown_wire_kind_is_refused_by_name(self) -> None:
        payload = self.revision.to_payload()
        with self.assertRaises(SchemaValidationError) as caught:
            SerializationEnvelope(
                schema_version=SCHEMA_VERSION,
                kind="BriefRevisionV2",
                contract_version=CONTRACT_VERSION,
                payload=payload,
                payload_digest=content_digest(payload),
            )
        self.assertIn("is not an M03 record kind", str(caught.exception))
        with self.assertRaises(SchemaValidationError) as also_unknown:
            require_record_kind("MigrationReceiptV3")
        self.assertIn("record_kinds()", str(also_unknown.exception))

    def test_the_kind_map_is_derived_so_a_new_module_cannot_be_forgotten(self) -> None:
        kinds = record_kinds()
        self.assertGreater(len(kinds), 50)
        for kind in (
            "BriefRevision",
            "BriefSemanticMergeAnalysis",
            "MergeComponent",
            "RestorationRevision",
            "MigrationReceipt",
            "CompatibilityDeclaration",
            "SerializationEnvelope",
        ):
            with self.subTest(kind=kind):
                self.assertIn(kind, kinds)
                self.assertEqual(record_types()[kind].__name__, kind)
        self.assertEqual(tuple(sorted(record_types())), kinds)
        self.assertIs(record_types()["MigrationReceipt"], MigrationReceipt)
        self.assertIs(record_types()["RestorationRevision"], RestorationRevision)
        self.assertIs(record_kind(self.revision), "BriefRevision")
        with self.assertRaises(TypeError) as frozen:
            record_types()["SomethingNew"] = MigrationReceipt
        self.assertIn("does not support item assignment", str(frozen.exception))
        with self.assertRaises(SchemaValidationError) as foreign:
            record_kind(object())
        self.assertIn("is not a record this kernel defines", str(foreign.exception))

    def test_an_envelope_cannot_be_built_around_a_payload_its_own_kind_would_reject(self) -> None:
        truncated = dict(self.revision.to_payload())
        truncated.pop("statements")
        with self.assertRaises(SchemaValidationError) as caught:
            envelope_over(truncated)
        self.assertIn("missing keys", str(caught.exception))
        tampered = dict(self.revision.to_payload())
        tampered["revision_number"] = "three"
        with self.assertRaises(SchemaValidationError) as not_a_number:
            envelope_over(tampered)
        self.assertIn("revision_number", str(not_a_number.exception))
        foreign_field = dict(self.revision.to_payload())
        foreign_field["a_field_from_a_newer_kernel"] = True
        with self.assertRaises(SchemaValidationError) as extra:
            envelope_over(foreign_field)
        self.assertIn("a_field_from_a_newer_kernel", str(extra.exception))

    def test_a_digest_that_does_not_match_its_bytes_is_refused_at_construction(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            SerializationEnvelope(
                schema_version=SCHEMA_VERSION,
                kind="BriefRevision",
                contract_version=CONTRACT_VERSION,
                payload=self.revision.to_payload(),
                payload_digest=content_digest("some other document"),
            )
        self.assertIn("never read them", str(caught.exception))

    def test_transport_text_is_read_as_an_envelope_or_not_at_all(self) -> None:
        document = dumps(self.revision)
        self.assertEqual(document, dumps(loads(document)))
        self.assertEqual(document, canonical_json(serialize(self.revision)))
        for text in ("[1, 2]", '"just a string"', "42", "not json at all", '{"kind": "BriefRevision"}'):
            with self.subTest(text=text):
                with self.assertRaises(SchemaValidationError):
                    loads(text)
        with self.assertRaises(SchemaValidationError) as already:
            deserialize(self.revision)
        self.assertIn("already a record", str(already.exception))


if __name__ == "__main__":
    unittest.main()
