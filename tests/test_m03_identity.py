"""The identity law §5.1-§5.6 and §18 hold the kernel to: what a brief *is* outlives how it is worded.

Five refusals make that true, and each one is asserted here rather than promised in prose. A rename is
metadata, so the stable identity still answers to the old name and the preserved source stays
byte-identical behind a rephrased statement. An admitted revision is frozen, so an in-place edit raises
and the only way forward is a new revision id that records its predecessor. Origin and authority are
separate axes, so an inference cannot borrow a human's standing and a human statement cannot be
satisfied by a model's confidence. And untrusted text cannot promote itself: the ceiling is a function
of how the words arrived, so a forged grant is a construction error rather than a plausible payload.
"""

from __future__ import annotations

import dataclasses
import unittest
from typing import Any

from iris_intent.admission import (
    AdmissionCheck,
    AdmissionDecision,
    AdmissionFinding,
    AdmissionReport,
    SemanticAdmissionShield,
    require_admitted,
)
from iris_intent.briefs import BriefRevision, RevisionKind, RevisionStatus, require_revision_identity
from iris_intent.errors import (
    AdmissionRefusedError,
    AuthorityError,
    RefError,
    RevisionFrozenError,
    SchemaValidationError,
)
from iris_intent.identity import (
    MAX_ALIASES,
    MAX_ANCESTORS,
    UNTRUSTED_SOURCES,
    VERSIONED_REF_KINDS,
    AuthorityLevel,
    BriefRevisionRef,
    CreativeBriefIdentity,
    RefKind,
    SemanticRef,
    SourceKind,
    ceiling_for,
    check_ancestry,
    is_untrusted,
    mint_id,
    require_authority,
    require_bound_ref,
)
from iris_intent.intent import (
    AuthorityBasis,
    IntentAuthorityRef,
    IntentModel,
    IntentOrigin,
    IntentStatement,
    StatementKind,
    authority_ceiling_for_origin,
)
from iris_intent.sources import (
    DerivationKind,
    ProvenanceCapsule,
    RawInputRef,
    SourceAnchor,
)

from tests import m03_kernel_support as S

QUOTED_TEXT = "the mark must be legible at 24px"


def restamped(revision: BriefRevision, **over: Any) -> BriefRevision:
    """The same revision re-decoded from its own payload with a few fields restated.

    Going through ``to_payload``/``from_payload`` rather than mutating a copy is the point: the digest
    is recomputed from the record's own bytes, so no field can be reworded underneath a citation.
    """

    return BriefRevision.from_payload({**revision.to_payload(), **over, "content_digest": None})


def source_of(kind: SourceKind, authority: AuthorityLevel, *, text: str = "") -> RawInputRef:
    return RawInputRef(
        source_id=f"src.{kind.value.lower()}",
        kind=kind.value,
        authority=authority.value,
        content_digest=S.digest(kind.value),
        transcription=text or None,
    )


class StableBriefIdentityTests(unittest.TestCase):
    def test_renaming_a_brief_leaves_its_stable_id_and_its_revisions_alone(self) -> None:
        identity = S.brief_identity()
        renamed = CreativeBriefIdentity(
            brief_id=S.BRIEF_ID, label="Iris launch, second name", aliases=("brief.iris.old",)
        )
        revision = S.admitted_revision()

        self.assertEqual(renamed.brief_id, identity.brief_id)
        self.assertTrue(renamed.known_as(S.BRIEF_ID))
        self.assertTrue(renamed.known_as("brief.iris.old"))
        self.assertFalse(renamed.known_as("brief.someone.else"))

        reworded = restamped(revision, label="renamed", notes="restated for the client")
        self.assertEqual(reworded.brief_id, revision.brief_id)
        self.assertEqual(reworded.brief_ref, revision.brief_ref)
        self.assertEqual(reworded.semantic_digest(), revision.semantic_digest())
        self.assertNotEqual(reworded.content_digest, revision.content_digest)
        require_revision_identity(renamed, revision)

    def test_an_alias_answers_to_the_brief_that_declared_it(self) -> None:
        identity = S.brief_identity(aliases=("brief.legacy", "brief.iris.old"))
        self.assertEqual(identity.aliases, ("brief.iris.old", "brief.legacy"))
        self.assertTrue(identity.known_as("brief.legacy"))

        with self.assertRaises(SchemaValidationError):
            S.brief_identity(aliases=("brief.dupe", "brief.dupe"))
        with self.assertRaises(SchemaValidationError):
            S.brief_identity(aliases=(S.BRIEF_ID,))
        with self.assertRaises(SchemaValidationError):
            S.brief_identity(aliases=("Not An Identifier",))
        with self.assertRaises(SchemaValidationError):
            S.brief_identity(aliases="brief.not-a-list")
        with self.assertRaises(SchemaValidationError):
            S.brief_identity(aliases=tuple(f"alias.{i}" for i in range(MAX_ALIASES + 1)))

    def test_identity_holds_no_brief_content_and_binds_only_an_m02_project(self) -> None:
        self.assertEqual(
            [item.name for item in dataclasses.fields(CreativeBriefIdentity)],
            ["brief_id", "label", "project_ref", "aliases"],
        )
        bound = CreativeBriefIdentity(
            brief_id=S.BRIEF_ID,
            label="Iris launch",
            project_ref=S.ref(RefKind.M02_PROJECT.value, "prod.1"),
        )
        self.assertEqual([item.kind for item in bound.references], [RefKind.M02_PROJECT.value])
        self.assertEqual(S.brief_identity().references, ())

        with self.assertRaises(RefError):
            CreativeBriefIdentity(
                brief_id=S.BRIEF_ID,
                label="Iris launch",
                project_ref=S.ref(RefKind.M02_PRODUCTION.value, "prod.1"),
            )

    def test_a_revision_of_a_different_brief_is_refused_by_the_identity_law(self) -> None:
        other = S.brief_identity(brief_id="brief.other", label="someone else's launch")
        with self.assertRaises(SchemaValidationError) as refused:
            require_revision_identity(other, S.admitted_revision())
        self.assertIn("brief.other", str(refused.exception))

    def test_a_draft_without_an_admission_is_refused_by_the_identity_law(self) -> None:
        admitted = S.admitted_revision()
        with self.assertRaises(SchemaValidationError):
            require_revision_identity(S.brief_identity(), restamped(admitted, admitted_by=None))

    def test_the_identity_round_trips_through_its_own_payload(self) -> None:
        identity = S.brief_identity(aliases=("brief.legacy",))
        rebuilt = CreativeBriefIdentity.from_payload(identity.to_payload())
        self.assertEqual(rebuilt.digest(), identity.digest())
        self.assertEqual(rebuilt.aliases, identity.aliases)
        self.assertEqual(rebuilt.label, identity.label)


class RevisionImmutabilityTests(unittest.TestCase):
    def test_an_admitted_revision_refuses_edit_in_place(self) -> None:
        admitted = S.admitted_revision()
        draft = S.draft_revision()

        for action in ("relabel", "append a statement", "withdraw"):
            with self.assertRaises(RevisionFrozenError) as refused:
                admitted.require_editable(action)
            self.assertIn(action, str(refused.exception))
            self.assertIn("immutable", str(refused.exception))

        draft.require_editable("relabel")
        self.assertEqual(
            [(status.value, status.editable) for status in RevisionStatus],
            [("DRAFT", True), ("ADMITTED", False), ("SUPERSEDED", False), ("WITHDRAWN", False)],
        )

    def test_admission_freezes_a_draft_without_touching_it(self) -> None:
        draft = S.draft_revision()
        admitted = draft.admit(admitted_by=S.revision_ref("rev.7"))

        self.assertEqual(draft.status, RevisionStatus.DRAFT.value)
        self.assertEqual(admitted.status, RevisionStatus.ADMITTED.value)
        self.assertEqual(admitted.revision_id, draft.revision_id)
        self.assertNotEqual(admitted.content_digest, draft.content_digest)
        self.assertEqual(admitted.admitted_by, S.revision_ref("rev.7"))
        self.assertTrue(admitted.admitted)
        self.assertFalse(draft.admitted)

    def test_admission_refuses_an_unbound_grant_and_an_empty_revision(self) -> None:
        with self.assertRaises(SchemaValidationError) as unbound:
            S.draft_revision().admit(
                admitted_by=SemanticRef(kind=RefKind.REVISION.value, ref_id="rev.7")
            )
        self.assertIn("digest", str(unbound.exception))

        blank = S.revision(7, (), status=RevisionStatus.DRAFT.value)
        with self.assertRaises(SchemaValidationError) as empty:
            blank.admit(admitted_by=S.revision_ref("rev.7"))
        self.assertIn("no statements", str(empty.exception))

        with self.assertRaises(RevisionFrozenError):
            S.admitted_revision().admit(admitted_by=S.revision_ref("rev.7"))

    def test_supersede_produces_a_new_revision_under_the_same_brief(self) -> None:
        admitted = S.admitted_revision()
        follow_up = admitted.supersede(revision_id="rev.8", kind=RevisionKind.CORRECTION.value)

        self.assertEqual(follow_up.revision_id, "rev.8")
        self.assertNotEqual(follow_up.revision_id, admitted.revision_id)
        self.assertEqual(follow_up.brief_id, admitted.brief_id)
        self.assertEqual(follow_up.revision_number, admitted.revision_number + 1)
        self.assertEqual(follow_up.predecessor_revision_id, admitted.revision_id)
        self.assertEqual(follow_up.ancestor_revision_ids[-1], admitted.revision_id)
        self.assertEqual(follow_up.status, RevisionStatus.DRAFT.value)
        self.assertIsNone(follow_up.admitted_by)

        self.assertEqual(admitted.status, RevisionStatus.ADMITTED.value)
        self.assertEqual(admitted.statements, follow_up.statements)
        self.assertEqual(admitted.sources, follow_up.sources)
        with self.assertRaises(RevisionFrozenError):
            admitted.supersede(revision_id=admitted.revision_id, kind=RevisionKind.CORRECTION.value)

    def test_a_rewording_moves_the_content_digest_but_not_the_meaning(self) -> None:
        admitted = S.admitted_revision()
        reworded = restamped(
            admitted, label="renamed", notes="restated", recorded_at="2026-01-02T00:00:00Z"
        )

        self.assertTrue(admitted.semantically_equal(reworded))
        self.assertEqual(admitted.semantic_digest(), reworded.semantic_digest())
        self.assertEqual(
            admitted.wording_only_delta(reworded), ("label", "notes", "recorded_at")
        )
        self.assertNotEqual(admitted.content_digest, reworded.content_digest)

        meaning_moved = restamped(
            admitted,
            statements=[
                {**admitted.to_payload()["statements"][0], "value": {"state": "off"}},
                *admitted.to_payload()["statements"][1:],
            ],
        )
        self.assertFalse(admitted.semantically_equal(meaning_moved))
        self.assertEqual(admitted.wording_only_delta(meaning_moved), ())
        with self.assertRaises(SchemaValidationError):
            admitted.semantically_equal(admitted.statements[0])

    def test_rewriting_a_record_under_its_old_digest_is_refused(self) -> None:
        payload = S.admitted_revision().to_payload()
        payload["notes"] = "added after the digest was taken"

        with self.assertRaises(SchemaValidationError) as tampered:
            BriefRevision.from_payload(payload)
        self.assertIn("altered after it was digested", str(tampered.exception))

    def test_a_revision_round_trips_byte_identically(self) -> None:
        admitted = S.admitted_revision()
        rebuilt = BriefRevision.from_payload(admitted.to_payload())

        self.assertEqual(rebuilt.digest(), admitted.digest())
        self.assertEqual(rebuilt.to_payload(), admitted.to_payload())
        self.assertEqual(rebuilt.content_digest, admitted.content_digest)
        self.assertEqual(rebuilt.statement_ids, admitted.statement_ids)
        self.assertEqual(rebuilt.admitted_by, admitted.admitted_by)
        self.assertEqual(
            [item.authority.authority for item in rebuilt.statements],
            [item.authority.authority for item in admitted.statements],
        )
        self.assertEqual(
            rebuilt.supersede(revision_id="rev.8", kind=RevisionKind.RESTATEMENT.value).digest(),
            admitted.supersede(revision_id="rev.8", kind=RevisionKind.RESTATEMENT.value).digest(),
        )


class RevisionLineageTests(unittest.TestCase):
    def test_the_first_revision_names_no_ancestors_and_no_predecessor(self) -> None:
        first = S.revision(1, (S.statement("st.1"),), kind=RevisionKind.INITIAL.value)
        self.assertEqual(first.ancestor_revision_ids, ())
        self.assertIsNone(first.predecessor_revision_id)

        with self.assertRaises(SchemaValidationError) as ancestors:
            S.revision(1, (S.statement("st.1"),), ancestor_revision_ids=("rev.0",))
        self.assertIn("cannot have ancestors", str(ancestors.exception))
        with self.assertRaises(SchemaValidationError) as predecessor:
            S.revision(1, (S.statement("st.1"),), predecessor_revision_id="rev.0")
        self.assertIn("cannot have a predecessor", str(predecessor.exception))

    def test_a_later_revision_without_a_chain_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            S.revision(
                4, (S.statement("st.4"),), ancestor_revision_ids=(), predecessor_revision_id=None
            )
        self.assertIn("no ancestor chain", str(refused.exception))

    def test_the_predecessor_must_be_the_last_ancestor(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            S.revision(
                3,
                (S.statement("st.3"),),
                ancestor_revision_ids=("rev.1", "rev.2"),
                predecessor_revision_id="rev.1",
            )
        self.assertIn("not the last ancestor", str(refused.exception))

        honest = S.revision(3, (S.statement("st.3"),), predecessor_revision_id="rev.2")
        self.assertEqual(honest.ancestor_revision_ids, ("rev.1", "rev.2"))

    def test_a_revision_cannot_appear_in_its_own_history(self) -> None:
        with self.assertRaises(RevisionFrozenError) as circular:
            S.revision(
                2,
                (S.statement("st.2"),),
                ancestor_revision_ids=("rev.2",),
                predecessor_revision_id=None,
            )
        self.assertIn("own ancestry", str(circular.exception))

        with self.assertRaises(RevisionFrozenError) as self_predecessor:
            S.revision(
                2,
                (S.statement("st.2"),),
                ancestor_revision_ids=("rev.2",),
                predecessor_revision_id="rev.2",
            )
        self.assertIn("own predecessor", str(self_predecessor.exception))

    def test_check_ancestry_refuses_repeats_junk_and_an_unbounded_chain(self) -> None:
        self.assertEqual(check_ancestry(["rev.2", "rev.1"]), ("rev.2", "rev.1"))

        with self.assertRaises(SchemaValidationError) as cycle:
            check_ancestry(["rev.1", "rev.2", "rev.1"])
        self.assertIn("repeats revisions", str(cycle.exception))
        with self.assertRaises(SchemaValidationError):
            check_ancestry("rev.1")
        with self.assertRaises(SchemaValidationError):
            check_ancestry(["rev.1", "Not An Id"])
        with self.assertRaises(SchemaValidationError) as too_long:
            check_ancestry([f"rev.{i}" for i in range(MAX_ANCESTORS + 1)])
        self.assertIn(str(MAX_ANCESTORS), str(too_long.exception))
        self.assertEqual(
            len(check_ancestry([f"rev.{i}" for i in range(1, MAX_ANCESTORS + 1)])), MAX_ANCESTORS
        )

    def test_revision_numbers_order_history_only_within_one_brief(self) -> None:
        first, second = S.revision_chain((1, 2))
        self.assertTrue(first.ref.precedes(second.ref))
        self.assertFalse(second.ref.precedes(first.ref))
        self.assertEqual(first.ref.text, f"{S.BRIEF_ID}#1:rev.1")
        self.assertEqual(first.ref.revision_ref.kind, RefKind.REVISION.value)
        self.assertEqual(first.ref.bind_semantics(S.digest("sem")).semantic_digest, S.digest("sem"))

        stranger = BriefRevisionRef(
            brief_id="brief.other", revision_id="rev.9", revision_number=9
        )
        with self.assertRaises(RefError):
            first.ref.precedes(stranger)
        with self.assertRaises(SchemaValidationError):
            BriefRevisionRef(brief_id=S.BRIEF_ID, revision_id="rev.1", revision_number=0)
        with self.assertRaises(SchemaValidationError):
            BriefRevisionRef(brief_id=S.BRIEF_ID, revision_id="rev.1", revision_number=True)


class RawSourcePreservationTests(unittest.TestCase):
    def test_normalising_wording_keeps_the_preserved_source_untouched(self) -> None:
        source = RawInputRef(
            source_id="src.brief",
            kind=SourceKind.HUMAN_MESSAGE.value,
            authority=AuthorityLevel.HUMAN_OWNER.value,
            content_digest=S.digest("src.brief"),
            language="en",
            transcription=QUOTED_TEXT,
        )
        verbatim = S.statement("st.1", source=source, assertion=QUOTED_TEXT)
        revision = restamped(S.revision(2, (verbatim,)), sources=[source.to_payload()])
        reworded = revision.supersede(
            revision_id="rev.8",
            kind=RevisionKind.RESTATEMENT.value,
            statements=(
                IntentStatement.from_payload(
                    {**verbatim.to_payload(), "assertion": "The mark stays legible small."}
                ),
            ),
        )

        self.assertEqual(reworded.sources, revision.sources)
        self.assertEqual(reworded.sources[0].transcription, QUOTED_TEXT)
        self.assertEqual(reworded.sources[0].content_digest, revision.sources[0].content_digest)
        self.assertNotEqual(reworded.statements[0].assertion, revision.statements[0].assertion)
        self.assertTrue(reworded.source("src.brief").holds(QUOTED_TEXT))
        self.assertTrue(reworded.statements[0].provenance.reaches("src.brief"))
        self.assertIsNone(reworded.source("src.nobody"))

    def test_a_source_digest_is_a_real_digest(self) -> None:
        source = S.raw_source()
        self.assertEqual(len(source.content_digest), S.DIGEST_LEN)
        self.assertTrue(all(item in "0123456789abcdef" for item in source.content_digest))
        self.assertEqual(source.content_digest, S.digest("src.brief"))
        self.assertNotEqual(
            source.content_digest, S.raw_source(source_id="src.other").content_digest
        )
        self.assertEqual(source.source_ref.content_digest, source.content_digest)

        for forged in ("nothex", "0" * 16, "", "f" * 65):
            with self.assertRaises(SchemaValidationError, msg=forged):
                RawInputRef(
                    source_id="src.brief",
                    kind=SourceKind.HUMAN_MESSAGE.value,
                    authority=AuthorityLevel.HUMAN_OWNER.value,
                    content_digest=forged,
                )

    def test_a_statement_may_not_cite_a_source_the_revision_does_not_preserve(self) -> None:
        revision = S.revision(3, (S.statement("st.1", source=S.raw_source(source_id="src.far")),))
        self.assertEqual([item.source_id for item in revision.sources], ["src.far"])

        with self.assertRaises(SchemaValidationError) as refused:
            restamped(revision, sources=[S.raw_source(source_id="src.brief").to_payload()])
        self.assertIn("src.far", str(refused.exception))

    def test_sources_are_kept_separate_ordered_and_unique(self) -> None:
        revision = S.revision(
            3,
            (
                S.statement("st.a", source=S.raw_source(source_id="src.second")),
                S.statement("st.b", source=S.raw_source(source_id="src.first")),
            ),
        )
        self.assertEqual([item.source_id for item in revision.sources], ["src.first", "src.second"])
        self.assertEqual(S.capsule_source_id(revision.statements[1]), "src.first")

        with self.assertRaises(SchemaValidationError) as duplicated:
            restamped(
                revision,
                sources=[
                    S.raw_source(source_id="src.first").to_payload(),
                    S.raw_source(source_id="src.second").to_payload(),
                    S.raw_source(source_id="src.first").to_payload(),
                ],
            )
        self.assertIn("duplicate source_ids", str(duplicated.exception))

    def test_quoted_provenance_must_point_at_preserved_text(self) -> None:
        anchor = S.passage(QUOTED_TEXT)
        quoted = S.capsule(derivation=DerivationKind.QUOTED.value, anchors=[anchor])

        self.assertIsInstance(quoted.anchors[0], SourceAnchor)
        self.assertEqual(quoted.anchors[0].quote_digest, S.digest(QUOTED_TEXT))
        self.assertEqual(quoted.anchors[0].span.end - quoted.anchors[0].span.start, len(QUOTED_TEXT))
        self.assertTrue(quoted.reaches("src.brief"))
        self.assertTrue(quoted.authoritative_basis)
        with self.assertRaises(SchemaValidationError) as unanchored:
            S.capsule(derivation=DerivationKind.QUOTED.value)
        self.assertIn("anchor", str(unanchored.exception))

        with self.assertRaises(SchemaValidationError) as void:
            ProvenanceCapsule(
                capsule_id="cap.void", derivation=DerivationKind.PARAPHRASED.value, source_refs=()
            )
        self.assertIn("no source", str(void.exception))

    def test_an_explicit_statement_without_provenance_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as refused:
            IntentStatement(
                statement_id="st.lost",
                semantic_path=S.LOGO,
                kind=StatementKind.DIRECTION.value,
                assertion="keep the mark left-aligned",
                origin=IntentOrigin.EXPLICIT.value,
                authority=S.authority_ref(),
                provenance=None,
            )
        self.assertIn("provenance", str(refused.exception))

    def test_the_original_language_survives_normalisation(self) -> None:
        revision = restamped(
            S.admitted_revision(),
            sources=[
                {
                    **S.raw_source(source_id="src.brief").to_payload(),
                    "language": "pt-br",
                    "transcription": "a marca deve ser legível a 24px",
                }
            ],
        )

        self.assertEqual([item.source_id for item in revision.sources], ["src.brief"])
        self.assertEqual(revision.sources[0].language, "pt-br")
        self.assertEqual(revision.statements[0].assertion, f"{S.TONE} holds")
        self.assertEqual(revision.statements[0].provenance.source_refs[0].ref_id, "src.brief")
        self.assertNotEqual(
            revision.semantic_digest(), S.admitted_revision().semantic_digest()
        )
        self.assertEqual(
            revision.semantic_digest(), restamped(revision, notes="translated aside").semantic_digest()
        )


class OriginIntegrityTests(unittest.TestCase):
    def four_statements(self) -> tuple[IntentStatement, ...]:
        return (
            S.statement("st.explicit"),
            S.statement(
                "st.derived",
                origin=IntentOrigin.DERIVED.value,
                authority=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                source_statement_ids=("st.explicit",),
            ),
            S.statement(
                "st.inferred",
                origin=IntentOrigin.INFERRED.value,
                authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
                source_statement_ids=("st.explicit",),
                confidence=0.4,
            ),
            S.statement(
                "st.defaulted",
                path=S.TONE,
                origin=IntentOrigin.DEFAULTED.value,
                authority=S.authority_ref(AuthorityLevel.PROJECT_RECORD.value),
            ),
        )

    def test_the_four_origins_round_trip_without_being_conflated(self) -> None:
        revision = S.revision(5, self.four_statements())
        rebuilt = BriefRevision.from_payload(revision.to_payload())

        self.assertEqual(
            {item.origin for item in rebuilt.statements}, {item.value for item in IntentOrigin}
        )
        for original, restored in zip(revision.statements, rebuilt.statements):
            self.assertEqual(original.origin, restored.origin)
            self.assertEqual(original.authority.authority, restored.authority.authority)
            self.assertEqual(original.confidence, restored.confidence)
        self.assertEqual(rebuilt.digest(), revision.digest())

        model = S.model(revision)
        self.assertEqual(
            {item.statement_id for item in model.inferred_or_defaulted},
            {"st.inferred", "st.defaulted"},
        )
        self.assertEqual(
            [item.statement_id for item in model.explicit_statements], ["st.explicit"]
        )
        self.assertEqual(
            [item.statement_id for item in model.by_origin(IntentOrigin.DERIVED.value)],
            ["st.derived"],
        )

    def test_each_origin_has_a_ceiling_written_down_once(self) -> None:
        self.assertEqual(
            {
                origin.value: authority_ceiling_for_origin(origin).value
                for origin in IntentOrigin
            },
            {
                "EXPLICIT": "HUMAN_OWNER",
                "DERIVED": "GOVERNED_POLICY",
                "INFERRED": "MODEL_INFERRED",
                "DEFAULTED": "GOVERNED_POLICY",
            },
        )
        self.assertTrue(IntentOrigin.EXPLICIT.is_user_asserted)
        self.assertEqual(
            {origin for origin in IntentOrigin if origin.needs_ancestor},
            {IntentOrigin.DERIVED, IntentOrigin.INFERRED},
        )
        with self.assertRaises(SchemaValidationError):
            authority_ceiling_for_origin("GUESSED")

    def test_an_inference_cannot_hold_human_authority(self) -> None:
        with self.assertRaises(AuthorityError) as promoted:
            S.statement(
                "st.bad",
                origin=IntentOrigin.INFERRED.value,
                authority=S.authority_ref(AuthorityLevel.HUMAN_OWNER.value),
                source_statement_ids=("st.explicit",),
            )
        self.assertIn("ceiling MODEL_INFERRED", str(promoted.exception))

        with self.assertRaises(AuthorityError) as thin:
            S.statement(
                "st.thin",
                origin=IntentOrigin.EXPLICIT.value,
                authority=S.authority_ref(AuthorityLevel.PROJECT_RECORD.value),
            )
        self.assertIn("at least TEAM_ASSERTED", str(thin.exception))

    def test_a_derived_or_inferred_statement_must_name_what_it_came_from(self) -> None:
        cases = (
            (IntentOrigin.DERIVED.value, AuthorityLevel.GOVERNED_POLICY.value),
            (IntentOrigin.INFERRED.value, AuthorityLevel.MODEL_INFERRED.value),
        )
        for origin, level in cases:
            with self.assertRaises(SchemaValidationError) as refused:
                S.statement("st.orphan", origin=origin, authority=S.authority_ref(level))
            self.assertIn("names no ancestor", str(refused.exception))

        capsule = ProvenanceCapsule.from_payload(
            {
                **S.capsule(capsule_id="cap.ancestry").to_payload(),
                "ancestor_refs": [S.ref(RefKind.STATEMENT.value, "st.explicit").to_payload()],
            }
        )
        anchored = IntentStatement(
            statement_id="st.anchored",
            semantic_path=S.LOGO,
            kind=StatementKind.DIRECTION.value,
            assertion="the mark keeps its clearance",
            origin=IntentOrigin.INFERRED.value,
            authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
            provenance=capsule,
            source_statement_ids=(),
        )
        self.assertEqual(
            [item.ref_id for item in anchored.provenance.ancestor_refs], ["st.explicit"]
        )
        self.assertEqual(anchored.provenance.derivation, DerivationKind.PARAPHRASED.value)

        model = S.model(
            S.revision(
                6,
                (
                    S.statement("st.explicit"),
                    anchored,
                    S.statement(
                        "st.downstream",
                        origin=IntentOrigin.DERIVED.value,
                        authority=S.authority_ref(AuthorityLevel.GOVERNED_POLICY.value),
                        source_statement_ids=("st.anchored",),
                    ),
                ),
            )
        )
        self.assertEqual(model.ancestors_of("st.downstream"), ("st.anchored",))
        self.assertEqual(model.dependents_of("st.anchored"), ("st.downstream",))

    def test_a_statement_may_not_be_its_own_source(self) -> None:
        with self.assertRaises(RefError) as refused:
            S.statement(
                "st.loop",
                origin=IntentOrigin.INFERRED.value,
                authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
                source_statement_ids=("st.loop",),
            )
        self.assertIn("its own source", str(refused.exception))

    def test_authority_and_confidence_stay_independent(self) -> None:
        owner = S.statement("st.owner", origin=IntentOrigin.EXPLICIT.value, confidence=0.05)
        guess = S.statement(
            "st.guess",
            path=S.TONE,
            origin=IntentOrigin.INFERRED.value,
            authority=S.authority_ref(AuthorityLevel.MODEL_INFERRED.value),
            source_statement_ids=("st.owner",),
            confidence=0.99,
        )
        team = S.statement(
            "st.team",
            path=S.ICON,
            origin=IntentOrigin.EXPLICIT.value,
            authority=S.authority_ref(AuthorityLevel.TEAM_ASSERTED.value),
        )

        self.assertEqual(owner.origin, IntentOrigin.EXPLICIT.value)
        self.assertEqual(guess.origin, IntentOrigin.INFERRED.value)
        self.assertTrue(owner.explicit)
        self.assertFalse(guess.explicit)
        self.assertFalse(team.explicit)
        self.assertGreater(guess.confidence, owner.confidence)
        self.assertLess(guess.authority_level.rank, owner.authority_level.rank)

        model = S.model(S.revision(7, (owner, guess, team)))
        self.assertEqual(model.max_authority, AuthorityLevel.HUMAN_OWNER)
        self.assertEqual([item.statement_id for item in model.explicit_statements], ["st.owner"])
        self.assertEqual(model.dependents_of("st.owner"), ("st.guess",))

    def test_the_intent_model_is_bound_to_the_revision_it_came_from(self) -> None:
        revision = S.admitted_revision()
        model = S.model(revision)

        self.assertEqual(
            (model.brief_id, model.revision_id, model.revision_number),
            (revision.brief_id, revision.revision_id, revision.revision_number),
        )
        self.assertEqual(model.paths, tuple(sorted({item.semantic_path for item in revision.statements})))
        self.assertEqual(model.mandatory_paths, (S.LOGO,))
        self.assertEqual(IntentModel.from_payload(model.to_payload()).model_digest, model.model_digest)
        self.assertEqual(model.require_statement("st.1").statement_id, "st.1")
        with self.assertRaises(RefError):
            model.require_statement("st.nobody")

        with self.assertRaises(SchemaValidationError):
            IntentModel.from_payload({**model.to_payload(), "statements": []})
        with self.assertRaises(SchemaValidationError) as tampered:
            IntentModel.from_payload({**model.to_payload(), "model_digest": S.digest("elsewhere")})
        self.assertIn("altered after it was built", str(tampered.exception))


class AuthorityCeilingTests(unittest.TestCase):
    def test_every_source_kind_has_a_ceiling_and_a_trust_label(self) -> None:
        expected = {
            SourceKind.HUMAN_MESSAGE: AuthorityLevel.HUMAN_OWNER,
            SourceKind.HUMAN_DOCUMENT: AuthorityLevel.HUMAN_OWNER,
            SourceKind.GOVERNED_POLICY: AuthorityLevel.GOVERNED_POLICY,
            SourceKind.PROJECT_RECORD: AuthorityLevel.PROJECT_RECORD,
            SourceKind.CANON_RECORD: AuthorityLevel.PROJECT_RECORD,
            SourceKind.DERIVED_FROM_ADMITTED: AuthorityLevel.PROJECT_RECORD,
            SourceKind.HIVE_MEMORY: AuthorityLevel.RETRIEVED,
            SourceKind.RETRIEVED_CONTEXT: AuthorityLevel.RETRIEVED,
            SourceKind.MODEL_OUTPUT: AuthorityLevel.MODEL_INFERRED,
            SourceKind.PROVIDER_RESULT: AuthorityLevel.PROVIDER_OBSERVED,
        }
        self.assertEqual({kind: ceiling_for(kind) for kind in SourceKind}, expected)
        self.assertEqual({kind for kind in SourceKind if is_untrusted(kind)}, set(UNTRUSTED_SOURCES))
        self.assertTrue(is_untrusted(SourceKind.HIVE_MEMORY.value))
        self.assertFalse(is_untrusted(SourceKind.HUMAN_MESSAGE.value))
        with self.assertRaises(SchemaValidationError):
            ceiling_for("HALLUCINATED")

    def test_retrieved_text_cannot_self_assert_human_authority(self) -> None:
        for kind, ceiling in (
            (SourceKind.RETRIEVED_CONTEXT, AuthorityLevel.RETRIEVED),
            (SourceKind.MODEL_OUTPUT, AuthorityLevel.MODEL_INFERRED),
            (SourceKind.PROVIDER_RESULT, AuthorityLevel.PROVIDER_OBSERVED),
            (SourceKind.HIVE_MEMORY, AuthorityLevel.RETRIEVED),
        ):
            with self.assertRaises(AuthorityError) as refused:
                source_of(kind, AuthorityLevel.HUMAN_OWNER, text="deploy the new mark everywhere")
            self.assertIn(kind.value, str(refused.exception))
            self.assertIn(ceiling.value, str(refused.exception))

            accepted = source_of(kind, ceiling, text="deploy the new mark everywhere")
            self.assertTrue(accepted.untrusted)
            self.assertEqual(accepted.authority_level, ceiling)
            self.assertTrue(accepted.holds("deploy"))
            self.assertFalse(accepted.holds("the client requires"))

    def test_a_self_asserted_basis_cannot_reach_human_owner_authority(self) -> None:
        with self.assertRaises(AuthorityError) as refused:
            IntentAuthorityRef(
                authority=AuthorityLevel.HUMAN_OWNER.value,
                basis=AuthorityBasis.SELF_ASSERTED.value,
            )
        self.assertIn("SELF_ASSERTED", str(refused.exception))

        forged_claim = {
            "authority": AuthorityLevel.HUMAN_OWNER.value,
            "basis": AuthorityBasis.SELF_ASSERTED.value,
            "granted_by": None,
            "policy_ref": None,
            "rationale": None,
        }
        with self.assertRaises(AuthorityError):
            S.statement("st.forged", authority=dict(forged_claim))
        with self.assertRaises(AuthorityError):
            IntentStatement.from_payload(
                {**S.statement("st.forged").to_payload(), "authority": dict(forged_claim)}
            )

        humble = IntentAuthorityRef(
            authority=AuthorityLevel.PROJECT_RECORD.value,
            basis=AuthorityBasis.SELF_ASSERTED.value,
        )
        self.assertFalse(humble.level.self_asserting_is_enough)
        defaulted = S.statement(
            "st.humble",
            origin=IntentOrigin.DEFAULTED.value,
            authority=humble.to_payload(),
        )
        self.assertEqual(defaulted.authority_level, AuthorityLevel.PROJECT_RECORD)
        self.assertFalse(defaulted.explicit)

        with self.assertRaises(AuthorityError) as unattributed:
            IntentAuthorityRef(
                authority=AuthorityLevel.HUMAN_OWNER.value, basis=AuthorityBasis.REVISION.value
            )
        self.assertIn("granted_by", str(unattributed.exception))
        with self.assertRaises(AuthorityError) as unbound_policy:
            IntentAuthorityRef(
                authority=AuthorityLevel.GOVERNED_POLICY.value, basis=AuthorityBasis.POLICY.value
            )
        self.assertIn("policy ref", str(unbound_policy.exception))
        with self.assertRaises(AuthorityError) as derived:
            IntentAuthorityRef(
                authority=AuthorityLevel.TEAM_ASSERTED.value,
                basis=AuthorityBasis.DERIVATION.value,
            )
        self.assertIn("DERIVATION", str(derived.exception))

    def test_scope_and_source_kind_never_grant_authority_by_themselves(self) -> None:
        granted = S.authority_ref(AuthorityLevel.HUMAN_OWNER.value)
        self.assertEqual(granted.level, AuthorityLevel.HUMAN_OWNER)
        self.assertTrue(granted.level.self_asserting_is_enough)
        with self.assertRaises(RefError):
            IntentAuthorityRef(
                authority=AuthorityLevel.GOVERNED_POLICY.value,
                basis=AuthorityBasis.POLICY.value,
                policy_ref=S.ref(RefKind.REVISION.value, "rev.7"),
            )

    def test_require_authority_ranks_and_refuses_junk(self) -> None:
        self.assertEqual(
            [level.value for level in sorted(AuthorityLevel, key=lambda item: item.rank)],
            [
                "UNTRUSTED",
                "PROVIDER_OBSERVED",
                "RETRIEVED",
                "MODEL_INFERRED",
                "PROJECT_RECORD",
                "TEAM_ASSERTED",
                "GOVERNED_POLICY",
                "HUMAN_OWNER",
            ],
        )
        self.assertTrue(AuthorityLevel.HUMAN_OWNER.at_least(AuthorityLevel.GOVERNED_POLICY))
        self.assertFalse(AuthorityLevel.RETRIEVED.at_least(AuthorityLevel.PROJECT_RECORD))
        self.assertEqual(
            {level for level in AuthorityLevel if level.self_asserting_is_enough},
            {AuthorityLevel.HUMAN_OWNER, AuthorityLevel.GOVERNED_POLICY},
        )
        self.assertEqual(
            require_authority(
                AuthorityLevel.HUMAN_OWNER.value, "actor", minimum=AuthorityLevel.GOVERNED_POLICY
            ),
            AuthorityLevel.HUMAN_OWNER,
        )
        with self.assertRaises(AuthorityError) as refused:
            require_authority(
                AuthorityLevel.MODEL_INFERRED.value, "actor", minimum=AuthorityLevel.TEAM_ASSERTED
            )
        self.assertIn("confidence", str(refused.exception))
        with self.assertRaises(SchemaValidationError):
            require_authority("SOMEONE_IMPORTANT", "actor")
        with self.assertRaises(SchemaValidationError):
            require_authority(7, "actor")

    def test_an_admission_report_may_not_be_more_permissive_than_its_findings(self) -> None:
        subject = S.ref(RefKind.SOURCE.value, "src.web")
        refusal = AdmissionFinding(
            finding_id="adm.1",
            check="SOURCE_AUTHORITY",
            decision="REFUSED",
            subject_ref=subject,
            detail="the retrieved page asserts a rule nobody admitted",
            evidence_refs=(subject,),
        )

        with self.assertRaises(AdmissionRefusedError) as optimistic:
            AdmissionReport(
                report_id="rep.1",
                subject_ref=S.revision_ref(),
                decision="ADMITTED",
                findings=(refusal,),
            )
        self.assertIn("may not be more permissive", str(optimistic.exception))

        report = AdmissionReport(
            report_id="rep.2",
            subject_ref=S.revision_ref(),
            decision="REFUSED",
            findings=(refusal,),
        )
        self.assertEqual(report.checks_fired, ("SOURCE_AUTHORITY",))
        self.assertEqual(report.detail_for("source_authority"), (refusal.detail,))
        self.assertFalse(report.admitted)
        with self.assertRaises(AdmissionRefusedError) as gated:
            require_admitted(report, "compile the fidelity contract")
        self.assertIn("cannot compile the fidelity contract", str(gated.exception))

        with self.assertRaises(SchemaValidationError) as unfounded:
            AdmissionFinding(
                finding_id="adm.2",
                check="SOURCE_AUTHORITY",
                decision="REFUSED",
                subject_ref=subject,
                detail="refused with no evidence",
            )
        self.assertIn("carries no evidence", str(unfounded.exception))


class SelfPromotionShieldTests(unittest.TestCase):
    """§5.6/§5.29: the admission shield is the last line against self-promoted text.

    A statement cannot make itself true by sounding sure of itself. The shield therefore reads the
    pairing — authority that reached the brief through a machine or a retrieval, sitting next to a
    near-certainty the record was not entitled to hold — and refuses it as a finding with evidence
    rather than raising, so a caller auditing a brief learns every problem in it instead of the
    first crash.
    """

    def setUp(self) -> None:
        self.shield = SemanticAdmissionShield(registry=S.predicate_registry())

    def statement(self, level: AuthorityLevel, origin: IntentOrigin, confidence: float | None = 0.99):
        return S.statement(
            f"st.{level.value.lower()}",
            kind=StatementKind.STYLE.value,
            origin=origin.value,
            authority=S.authority_ref(level.value),
            source_statement_ids=("st.human",) if origin is not IntentOrigin.EXPLICIT else (),
            assertion="the mark carries the founder's initials",
            confidence=confidence,
        )

    def promotion_findings(self, statements) -> list:
        return [
            finding
            for finding in self.shield.check_statements(tuple(statements))
            if finding.check == AdmissionCheck.SELF_PROMOTED_RULE.value
        ]

    def test_a_machine_channel_claiming_near_certainty_is_refused(self) -> None:
        for level in (
            AuthorityLevel.UNTRUSTED,
            AuthorityLevel.PROVIDER_OBSERVED,
            AuthorityLevel.RETRIEVED,
            AuthorityLevel.MODEL_INFERRED,
        ):
            with self.subTest(level=level.value):
                findings = self.promotion_findings(
                    (self.statement(level, IntentOrigin.INFERRED),)
                )
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].decision, AdmissionDecision.REFUSED.value)
                self.assertIn("confidence is not authority", findings[0].detail)
                self.assertTrue(findings[0].evidence_refs)

    def test_a_humans_certainty_does_not_read_as_self_promotion(self) -> None:
        for level in (AuthorityLevel.HUMAN_OWNER, AuthorityLevel.GOVERNED_POLICY):
            origin = (
                IntentOrigin.EXPLICIT
                if level is AuthorityLevel.HUMAN_OWNER
                else IntentOrigin.DEFAULTED
            )
            with self.subTest(level=level.value):
                self.assertEqual(
                    self.promotion_findings((self.statement(level, origin),)),
                    [],
                    f"{level.value} may stand behind its own claim, so confidence adds nothing",
                )

    def test_the_guard_needs_the_pairing_rather_than_the_level_alone(self) -> None:
        modest = self.statement(
            AuthorityLevel.MODEL_INFERRED, IntentOrigin.INFERRED, confidence=0.4
        )
        self.assertEqual(self.promotion_findings((modest,)), [])

    def test_no_admissible_authority_level_makes_the_guard_raise(self) -> None:
        """Regression: the guard once parsed an authority level as a source kind and crashed.

        A shield that raises cannot report the rest of the brief's findings, so an injected brief
        would have been half-audited and looked fully audited.
        """

        admissible = {
            IntentOrigin.EXPLICIT: (
                AuthorityLevel.TEAM_ASSERTED,
                AuthorityLevel.GOVERNED_POLICY,
                AuthorityLevel.HUMAN_OWNER,
            ),
            IntentOrigin.DERIVED: (AuthorityLevel.PROJECT_RECORD, AuthorityLevel.GOVERNED_POLICY),
            IntentOrigin.INFERRED: tuple(
                level
                for level in AuthorityLevel
                if level.rank <= AuthorityLevel.MODEL_INFERRED.rank
            ),
            IntentOrigin.DEFAULTED: (
                AuthorityLevel.PROJECT_RECORD,
                AuthorityLevel.GOVERNED_POLICY,
            ),
        }
        for origin, levels in admissible.items():
            for level in levels:
                with self.subTest(level=level.value, origin=origin.value):
                    findings = self.shield.check_statements(
                        (self.statement(level, origin),)
                    )
                    self.assertIsInstance(findings, list)

    def test_a_project_record_is_still_not_a_self_asserting_authority(self) -> None:
        findings = self.promotion_findings(
            (self.statement(AuthorityLevel.PROJECT_RECORD, IntentOrigin.DEFAULTED),)
        )
        self.assertEqual(len(findings), 1, "a filed note about what someone said is not a grant")


class RefBindingTests(unittest.TestCase):
    def test_minted_ids_are_unique_and_shaped_like_identifiers(self) -> None:
        first = mint_id("brief")
        second = mint_id("brief")

        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("brief-"))
        self.assertEqual(len(first.split("-")[1]), 32)
        self.assertTrue(mint_id().startswith("m03-"))
        for identifier in (first, second, mint_id("rev")):
            self.assertEqual(
                CreativeBriefIdentity(brief_id=identifier, label="fresh").brief_id, identifier
            )

    def test_require_bound_ref_demands_a_digest_and_the_named_kind(self) -> None:
        revision = S.revision_ref("rev.7")
        self.assertIs(require_bound_ref(revision, "created_by", kind=RefKind.REVISION), revision)
        self.assertTrue(revision.pinned)

        with self.assertRaises(RefError) as wrong_kind:
            require_bound_ref(S.constraint_ref("cn.a"), "created_by", kind=RefKind.REVISION)
        self.assertIn("must reference REVISION", str(wrong_kind.exception))
        with self.assertRaises(RefError) as unpinned:
            require_bound_ref(
                SemanticRef(kind=RefKind.REVISION.value, ref_id="rev.7"), "created_by"
            )
        self.assertIn("no content digest", str(unpinned.exception))
        with self.assertRaises(SchemaValidationError):
            require_bound_ref("REVISION@rev.7", "created_by")

    def test_an_admitted_ref_cannot_be_rebound(self) -> None:
        bound = S.ref(RefKind.REVISION.value, "rev.7")
        rebound = bound.bind(S.digest("rev.7"), "v2")

        self.assertEqual(rebound.content_digest, bound.content_digest)
        self.assertEqual(rebound.version, "v2")
        with self.assertRaises(RefError) as refused:
            bound.bind(S.digest("something else"), "v2")
        self.assertIn("already bound", str(refused.exception))

    def test_namespaces_that_change_under_one_id_must_be_version_pinned(self) -> None:
        with self.assertRaises(RefError) as unpinned:
            SemanticRef(kind=RefKind.M01_DOMAIN_PROFILE.value, ref_id="profile.visual")
        self.assertIn("pin the version", str(unpinned.exception))

        pinned = S.ref(RefKind.M01_DOMAIN_PROFILE.value, "profile.visual")
        self.assertEqual(pinned.version, "v1")
        self.assertFalse(pinned.unversioned)
        for kind in sorted(VERSIONED_REF_KINDS, key=lambda item: item.value):
            self.assertEqual(S.ref(kind.value, f"{kind.value.lower()}.1").version, "v1")
        self.assertEqual(
            SemanticRef(kind=RefKind.REVISION.value, ref_id="rev.7").text, "REVISION@rev.7"
        )

    def test_the_vocabulary_parses_one_way_and_refuses_everything_else(self) -> None:
        self.assertEqual(AuthorityLevel.parse(" human_owner "), AuthorityLevel.HUMAN_OWNER)
        self.assertEqual(RefKind.parse("revision"), RefKind.REVISION)
        self.assertEqual(SourceKind.parse("HIVE_MEMORY").value, "HIVE_MEMORY")
        self.assertEqual(StatementKind.parse("quality_target"), StatementKind.QUALITY_TARGET)
        self.assertEqual(IntentOrigin.parse(IntentOrigin.EXPLICIT), IntentOrigin.EXPLICIT)
        self.assertIn("PROVIDER_RESULT", SourceKind.describe())
        self.assertEqual(RefKind.members(), sorted(RefKind.members()))
        self.assertIn(RefKind.M02_PROJECT.value, RefKind.members())

        for junk in ("authority-is-borrowed", "", 4, None):
            with self.assertRaises(SchemaValidationError, msg=repr(junk)):
                AuthorityLevel.parse(junk, "authority")


if __name__ == "__main__":
    unittest.main()
