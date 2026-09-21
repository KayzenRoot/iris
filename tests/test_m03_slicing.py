"""The slicing, fingerprint, reuse and explainability kernel: a consumer sees enough and nothing more.

§15 sells M03 on a token economy, and the economy is worthless if the saving comes from withholding
a governing constraint, so this file proves both halves at once. A slice is a closure: one requested
path never carries an unrelated path's statements, every included item records the reason it was
included, a dangling citation is refused rather than silently dropped, and a rule whose conditions
do not hold in the work context is absent from both the slice and its digest. A fingerprint is the
only thing allowed to say "nothing relevant changed", so equivalence is declared rather than
assumed: rationale moves no digest, strength and polarity always do, and a profile that names a
core field presentational is refused. Reuse then turns on testimony rather than resemblance: an edit
an admitted delta reports as presentation-only still reuses, an untestified digest change
recompiles, a provider move rebuilds carriage only, and a stale dependency invalidates just the
paths it says it feeds. Finally an explanation is a graph, not a sentence: every emitted obligation
walks to an admitted source or policy ref, and every §18 level renders the same canonical facts.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_intent.ambiguity import AmbiguityAssessment, FreedomZone
from iris_intent.execution import IntentOperation, compile_execution_intent
from iris_intent.constraints import Condition, ProtectedAnchor
from iris_intent.authority import AuthorityLevel
from iris_intent.errors import (
    ExplanationError,
    SchemaValidationError,
    ScopeError,
    StaleSemanticError,
    UnsupportedVersionError,
)
from iris_intent.fingerprints import (
    DEFAULT_EQUIVALENCE_PROFILE,
    ChangeKind,
    IntentDelta,
    SemanticChange,
    diff_bundles,
    fingerprint_model,
    require_same_profile,
)
from iris_intent.freshness import (
    DerivedArtifactKind,
    assess_freshness,
    DerivedIntentDependency,
    DerivedScope,
    FreshnessDimension,
    FreshnessEvidence,
    FreshnessSignal,
    FreshnessState,
    affected_dependency_ids,
    affected_paths,
    require_fresh,
    requires_whole_artifact,
)
from iris_intent.explanation import (
    ROOT_CLASSIFICATION,
    ExplanationCacheKey,
    ExplanationEdge,
    ExplanationEdgeKind,
    ExplanationLevel,
    ExplanationNode,
    ExplanationNodeKind,
    IntentExplanationGraph,
    compile_explanation_graph,
    explanation_cache_key,
    explanation_levels,
    ground_kind_for,
    project_explanation,
    reachable_roots,
    require_cache_valid,
    why_node,
)
from iris_intent.identity import RefKind
from iris_intent.reuse import (
    ReusePassport,
    RecomputeScope,
    ReuseVerdict,
    evaluate_reuse,
    passport_for,
    require_reusable,
    requires_whole,
)
from iris_intent.slicing import (
    MinimumSufficientSemanticSlice,
    SemanticSliceRequest,
    SlicePurpose,
    closure_for,
    require_slice_minimality,
    slice_intent,
    structural_footprint,
)
from iris_intent.versions import content_digest

from tests import m03_kernel_support as S

MODEL = S.model(S.admitted_revision(7))
BUNDLE = S.bundle((S.rule("cn.logo", S.LOGO, mandatory=True), S.rule("cn.tone", S.TONE)))


def request_for(paths: Any, *, purpose: str = SlicePurpose.COMPILE_QUALITY.value, **over: Any):
    """One consumer ask against the shared model, spelled once so each test names only its variation."""

    return SemanticSliceRequest(
        request_id=over.pop("request_id", "req.iris"),
        consumer_ref=S.ref(RefKind.CONTRACT_SET.value, "contracts.iris"),
        purpose=purpose,
        paths=tuple(paths),
        revision_ref=S.revision_ref("rev.7"),
        **over,
    )


def sliced(paths: Any = (S.LOGO,), model: Any = MODEL, bundle: Any = BUNDLE, **over: Any):
    return slice_intent(model, bundle, request_for(paths, **over))


def fp(item: Any, *, ident: str = "fp.t", profile: Any = DEFAULT_EQUIVALENCE_PROFILE):
    """A fingerprint under the admitted default profile, where rationale is prose and not meaning."""

    return S.fingerprint(item, profile=profile, ident=ident)


def _bundle_delta(before: Any, after: Any) -> IntentDelta:
    return diff_bundles(before, after, profile=DEFAULT_EQUIVALENCE_PROFILE, delta_id="delta.t")


class TestSliceExcludesUnrelatedSemantics(unittest.TestCase):
    def test_a_request_for_one_path_carries_no_statement_from_another(self):
        result = sliced((S.LOGO,))
        self.assertEqual(("st.1",), result.statement_ids)
        self.assertIn("st.2", result.excluded_statement_ids)
        self.assertEqual(("cn.logo",), result.constraint_ids)
        self.assertIn("cn.tone", result.excluded_constraint_ids)

    def test_every_included_item_records_why_it_was_included(self):
        result = sliced((S.LOGO,))
        for statement in result.statements:
            self.assertEqual("requested path", result.reason_for(statement.statement_id))
        for constraint in result.constraints:
            self.assertTrue(result.reason_for(constraint.constraint_id))

    def test_a_dangling_citation_refuses_to_slice_rather_than_drop_the_dependency(self):
        broken = S.model(
            S.revision(
                7,
                (
                    S.statement("st.parent", S.LOGO),
                    S.statement("st.child", S.TONE, source_statement_ids=("st.ghost",)),
                ),
            )
        )
        with self.assertRaises(SchemaValidationError) as caught:
            slice_intent(broken, None, request_for((S.TONE,), purpose=SlicePurpose.VALIDATE.value))
        self.assertIn("dangling citation", str(caught.exception))

    def test_a_derived_statement_pulls_in_the_statement_it_cites(self):
        layered = S.model(
            S.revision(
                7,
                (
                    S.statement("st.parent", S.LOGO),
                    S.statement("st.child", S.TONE, source_statement_ids=("st.parent",)),
                ),
            )
        )
        result = S.slice_for(layered, None, (S.TONE,))
        self.assertEqual(("st.child", "st.parent"), result.statement_ids)
        self.assertEqual("citation of st.child", result.reason_for("st.parent"))

    def test_a_transitive_citation_chain_is_closed_in_full(self):
        deep = S.model(
            S.revision(
                7,
                (
                    S.statement("st.a", S.LOGO),
                    S.statement("st.b", S.ICON, source_statement_ids=("st.a",)),
                    S.statement("st.c", S.SPEC, source_statement_ids=("st.b",)),
                ),
            )
        )
        result = S.slice_for(deep, None, (S.SPEC,))
        self.assertEqual(("st.a", "st.b", "st.c"), result.statement_ids)
        self.assertIn("citation of st.b", result.reason_for("st.a"))

    def test_closure_for_reaches_the_same_ids_as_the_slice_without_building_one(self):
        layered = S.model(
            S.revision(
                7,
                (
                    S.statement("st.parent", S.LOGO),
                    S.statement("st.child", S.TONE, source_statement_ids=("st.parent",)),
                ),
            )
        )
        self.assertEqual(
            ("st.child", "st.parent"), closure_for(layered, (S.TONE,))
        )
        self.assertEqual(("st.child",), closure_for(layered, (S.TONE,), statements_only=True))

    def test_a_parent_path_request_carries_the_children_it_governs(self):
        wide = S.model(
            S.revision(
                3,
                (
                    S.statement("st.clearspace", "brief.visual.logo.clearspace"),
                    S.statement("st.palette", "brief.visual.logo.palette"),
                    S.statement("st.pace", "brief.audio.tone.pace"),
                ),
            )
        )
        result = S.slice_for(wide, None, ("brief.visual.logo",))
        self.assertEqual(("st.clearspace", "st.palette"), result.statement_ids)
        self.assertIn("st.pace", result.excluded_statement_ids)

    def test_an_unrequested_path_never_arrives_through_a_constraint(self):
        rules = S.bundle((S.rule("cn.logo", S.LOGO), S.rule("cn.tone", S.TONE)))
        result = S.slice_for(MODEL, rules, (S.LOGO,))
        self.assertEqual(("cn.logo",), result.constraint_ids)
        self.assertEqual((S.LOGO,), result.paths)


class TestSliceContextAndPurpose(unittest.TestCase):
    def test_a_rule_inactive_under_the_context_is_excluded_from_the_slice(self):
        conditional = S.bundle(
            (
                S.rule("cn.eu", S.LOGO, conditions=(Condition("region", "EQ", ("eu",)),)),
                S.rule("cn.us", S.LOGO, conditions=(Condition("region", "EQ", ("us",)),)),
            )
        )
        european = sliced((S.LOGO,), bundle=conditional, context={"region": "eu"})
        self.assertEqual(("cn.eu",), european.constraint_ids)
        self.assertEqual(("cn.us",), european.excluded_constraint_ids)

    def test_an_inactive_rule_is_absent_from_the_digest_rather_than_flagged(self):
        conditional = S.bundle(
            (
                S.rule("cn.eu", S.LOGO, conditions=(Condition("region", "EQ", ("eu",)),)),
                S.rule("cn.us", S.LOGO, conditions=(Condition("region", "EQ", ("us",)),)),
            )
        )
        european = sliced((S.LOGO,), bundle=conditional, context={"region": "eu"})
        american = sliced((S.LOGO,), bundle=conditional, context={"region": "us"}, request_id="req.us")
        self.assertNotEqual(european.slice_digest, american.slice_digest)

    def test_no_context_means_the_conditional_rule_is_not_active(self):
        conditional = S.bundle((S.rule("cn.eu", S.LOGO, conditions=(Condition("region", "EQ", ("eu",)),)),))
        result = sliced((S.LOGO,), bundle=conditional)
        self.assertEqual((), result.constraint_ids)
        self.assertEqual(("cn.eu",), result.excluded_constraint_ids)

    def test_a_compilation_purpose_carries_rules_and_no_provenance_packets(self):
        result = sliced((S.LOGO,), purpose=SlicePurpose.COMPILE_QUALITY.value)
        self.assertEqual(("cn.logo",), result.constraint_ids)
        self.assertEqual((), result.provenance_capsules)

    def test_an_audit_purpose_carries_provenance_and_no_compiled_rules(self):
        result = sliced((S.LOGO,), purpose=SlicePurpose.AUDIT.value)
        self.assertEqual((), result.constraints)
        self.assertEqual(1, len(result.provenance_capsules))
        self.assertEqual("cap.st.1", result.provenance_capsules[0].ref_id)

    def test_a_clarification_purpose_carries_the_ambiguity_that_would_change_the_answer(self):
        assessment = AmbiguityAssessment(
            brief_id=S.BRIEF_ID,
            revision_id="rev.7",
            ambiguities=(S.ambiguity("am.logo", path=S.LOGO), S.ambiguity("am.tone", path=S.TONE, statements=("st.2",))),
            freedom_zones=(
                FreedomZone(zone_id="fz.logo", label="mark latitude", free_paths=(S.LOGO,)),
            ),
        )
        clarify = slice_intent(MODEL, BUNDLE, request_for((S.LOGO,), purpose=SlicePurpose.CLARIFY.value), assessment=assessment)
        self.assertEqual(("am.logo",), tuple(item.ambiguity_id for item in clarify.ambiguities))
        self.assertIn("am.tone", tuple(item.ambiguity_id for item in assessment.ambiguities))
        self.assertEqual(("fz.logo",), tuple(item.zone_id for item in clarify.freedom_zones))
        self.assertEqual("affects sliced semantics", clarify.reason_for("am.logo"))
        self.assertTrue(clarify.blocking)

    def test_a_compilation_purpose_does_not_fetch_ambiguity_records(self):
        assessment = AmbiguityAssessment(
            brief_id=S.BRIEF_ID,
            revision_id="rev.7",
            ambiguities=(S.ambiguity("am.logo", path=S.LOGO),),
        )
        compile_slice = slice_intent(
            MODEL, BUNDLE, request_for((S.LOGO,), purpose=SlicePurpose.COMPILE_EXECUTION.value), assessment=assessment
        )
        self.assertEqual((), compile_slice.ambiguities)

    def test_a_slice_without_rules_reports_its_size_honestly(self):
        result = sliced((S.LOGO,), bundle=None)
        self.assertEqual(
            {"paths": 1, "statements": 1, "constraints": 0, "ambiguities": 0, "freedom_zones": 0},
            result.size,
        )

    def test_a_bounded_slice_refuses_to_widen_itself_to_fit(self):
        with self.assertRaises(SchemaValidationError) as caught:
            sliced((S.LOGO, S.TONE), max_statements=1)
        self.assertIn("narrow the requested paths", str(caught.exception))

    def test_an_empty_request_asks_for_nothing_and_is_refused(self):
        with self.assertRaises(ScopeError) as caught:
            request_for(())
        self.assertIn("names no path", str(caught.exception))

    def test_an_unrelated_statement_cannot_be_smuggled_into_a_narrow_slice(self):
        result = sliced((S.LOGO,))
        extra = tuple(item for item in MODEL.statements if item.statement_id == "st.2")
        with self.assertRaises(ScopeError) as caught:
            replace(result, statements=result.statements + extra)
        self.assertIn("outside its declared paths", str(caught.exception))

    def test_an_id_cannot_be_both_included_and_excluded(self):
        result = sliced((S.LOGO,))
        with self.assertRaises(SchemaValidationError) as caught:
            replace(result, excluded_statement_ids=("st.1", "st.2"))
        self.assertIn("both included and excluded", str(caught.exception))

    def test_a_declared_digest_that_disagrees_with_the_content_is_refused(self):
        result = sliced((S.LOGO,))
        with self.assertRaises(SchemaValidationError) as caught:
            replace(result, statements=(), excluded_statement_ids=tuple(sorted(set(result.excluded_statement_ids))))
        self.assertIn("does not match its content", str(caught.exception))


class TestSliceMinimalityAndDeterminism(unittest.TestCase):
    def test_the_same_inputs_produce_the_same_slice_digest(self):
        self.assertEqual(sliced((S.LOGO,)).slice_digest, sliced((S.LOGO,)).slice_digest)

    def test_two_consumers_asking_for_one_slice_get_equivalent_payloads(self):
        first = sliced((S.LOGO,), request_id="req.a")
        second = sliced((S.LOGO,), request_id="req.b")
        self.assertTrue(first.equivalent_to(second))
        self.assertNotEqual(first.request_id, second.request_id)

    def test_a_mandatory_semantic_change_moves_the_slice_digest(self):
        before = sliced((S.LOGO,))
        after_model = S.model(
            S.revision(
                7,
                (
                    S.statement("st.1", S.LOGO, mandatory=True, value={"state": "off"}),
                    S.statement("st.2", S.TONE),
                ),
            )
        )
        self.assertNotEqual(before.slice_digest, sliced((S.LOGO,), model=after_model).slice_digest)

    def test_a_delivered_slice_that_dropped_a_dependency_fails_minimality(self):
        request = request_for((S.TONE,))
        model = S.model(
            S.revision(
                7,
                (
                    S.statement("st.parent", S.LOGO),
                    S.statement("st.child", S.TONE, source_statement_ids=("st.parent",)),
                ),
            )
        )
        complete = slice_intent(model, None, request)
        short = MinimumSufficientSemanticSlice(
            slice_id="short",
            request_id=request.request_id,
            purpose=request.purpose,
            brief_ref=complete.brief_ref,
            revision_ref=complete.revision_ref,
            paths=complete.paths,
            statements=tuple(item for item in complete.statements if item.statement_id == "st.child"),
            inclusion_reasons={"st.child": "requested path"},
        )
        with self.assertRaises(SchemaValidationError) as caught:
            require_slice_minimality(short, model, None, request)
        self.assertIn("missing ['st.parent']", str(caught.exception))

    def test_a_delivered_slice_matching_its_closure_passes_minimality(self):
        request = request_for((S.LOGO,))
        complete = slice_intent(MODEL, BUNDLE, request)
        require_slice_minimality(complete, MODEL, BUNDLE, request)
        self.assertEqual(complete.constraint_ids, slice_intent(MODEL, BUNDLE, request).constraint_ids)

    def test_a_missing_statement_is_reported_rather_than_returned_as_none(self):
        result = sliced((S.LOGO,))
        with self.assertRaises(SchemaValidationError) as caught:
            result.statement("st.2")
        self.assertIn("does not carry statement st.2", str(caught.exception))

    def test_a_missing_constraint_names_the_slice_that_lacks_it(self):
        result = sliced((S.LOGO,))
        with self.assertRaises(SchemaValidationError) as caught:
            result.constraint("cn.tone")
        self.assertIn("does not carry constraint cn.tone", str(caught.exception))

    def test_the_footprint_measure_counts_leaves_rather_than_bytes(self):
        self.assertEqual(1, structural_footprint("one leaf"))
        self.assertEqual(0, structural_footprint(()))
        self.assertEqual(2, structural_footprint({"a": {"b": 1, "c": 2}}))

    def test_a_slice_names_the_revision_and_brief_it_was_computed_against(self):
        result = sliced((S.LOGO,))
        self.assertEqual(RefKind.REVISION.value, result.revision_ref.kind)
        self.assertEqual("rev.7", result.revision_ref.ref_id)
        self.assertEqual(S.BRIEF_ID, result.brief_ref.ref_id)
        narrow = structural_footprint(result.to_payload())
        self.assertLess(narrow, structural_footprint(sliced((S.LOGO, S.TONE)).to_payload()))
        self.assertEqual(narrow, structural_footprint(sliced((S.LOGO,)).to_payload()))

    def test_an_unknown_purpose_is_refused_before_anything_is_fetched(self):
        with self.assertRaises(Exception) as caught:
            request_for((S.LOGO,), purpose="TELEPORT")
        self.assertIn("purpose", str(caught.exception))


class TestFingerprintEquivalence(unittest.TestCase):
    def test_identical_inputs_fingerprint_identically(self):
        first = S.fingerprint(S.admitted_revision(7), ident="fp.a")
        second = S.fingerprint(S.admitted_revision(7), ident="fp.b")
        self.assertEqual(first.semantic_digest, second.semantic_digest)
        self.assertTrue(first.is_equivalent_to(second))

    def test_a_rationale_rewording_leaves_the_semantic_digest_alone(self):
        plain = S.revision(7, (S.statement("st.1", S.LOGO),))
        annotated = S.revision(
            7,
            (
                S.statement(
                    "st.1",
                    S.LOGO,
                    authority=S.authority_ref(rationale="the owner repeated the same mark rule aloud"),
                ),
            ),
        )
        self.assertEqual(fp(plain).semantic_digest, fp(annotated).semantic_digest)
        self.assertTrue(fp(plain).is_equivalent_to(fp(annotated, ident="fp.other")))

    def test_a_mandatory_value_change_moves_the_path_digest(self):
        before = S.fingerprint(S.admitted_revision(7))
        after = S.fingerprint(
            S.revision(
                7,
                (
                    S.statement("st.1", S.LOGO, mandatory=True, value={"state": "off"}),
                    S.statement("st.2", S.TONE),
                ),
            )
        )
        self.assertNotEqual(before.semantic_digest, after.semantic_digest)
        self.assertEqual([S.LOGO], list(before.changed_paths(after)))

    def test_a_per_path_digest_lets_an_unrelated_path_be_carried_over(self):
        before = fp(S.admitted_revision(7))
        after = fp(
            S.revision(
                7,
                (
                    S.statement("st.1", S.LOGO, mandatory=True),
                    S.statement("st.2", S.TONE, value={"state": "warmer"}),
                ),
            ),
            ident="fp.b",
        )
        self.assertEqual(before.digest_for(S.LOGO), after.digest_for(S.LOGO))
        self.assertNotEqual(before.digest_for(S.TONE), after.digest_for(S.TONE))
        self.assertEqual([S.TONE], list(before.changed_paths(after)))

    def test_a_model_fingerprint_and_a_revision_fingerprint_agree_on_paths(self):
        revision = S.admitted_revision(7)
        model_fp = fingerprint_model(
            S.model(revision), profile=DEFAULT_EQUIVALENCE_PROFILE, revision_ref=S.revision_ref("rev.7")
        )
        revision_fp = fp(revision)
        self.assertEqual(sorted(model_fp.path_digests), sorted(revision_fp.path_digests))

    def test_a_bundle_fingerprint_is_blind_to_rule_insertion_order(self):
        one = S.bundle((S.rule("cn.a"), S.rule("cn.b", S.TONE, predicate="mentions_brand", arguments={"phrase": "x"})))
        other = S.bundle((S.rule("cn.b", S.TONE, predicate="mentions_brand", arguments={"phrase": "x"}), S.rule("cn.a")))
        left = S.bundle_fingerprint(one)
        right = S.bundle_fingerprint(other)
        self.assertEqual(left.form_digest, right.form_digest)
        self.assertTrue(left.is_equivalent_to(right))

    def test_a_bundle_fingerprint_counts_hards_and_negatives_from_the_rules(self):
        item = S.bundle_fingerprint(
            S.bundle(
                (
                    S.rule("cn.hard"),
                    S.rule("cn.soft", strength="ADVISORY"),
                    S.rule("cn.forbid", polarity="FORBID"),
                )
            )
        )
        self.assertEqual(3, item.constraint_count)
        self.assertEqual(1, item.negative_count)
        self.assertEqual(2, item.hard_count)

    def test_counts_that_disagree_with_each_other_are_refused(self):
        item = S.bundle_fingerprint(S.bundle((S.rule("cn.a"),)))
        with self.assertRaises(SchemaValidationError) as caught:
            replace(item, negative_count=4)
        self.assertIn("cannot outnumber the total", str(caught.exception))

    def test_a_profile_cannot_declare_strength_presentational(self):
        with self.assertRaises(SchemaValidationError) as caught:
            S.equivalence_profile(presentation_fields=("strength",))
        self.assertIn("admitted presentational set", str(caught.exception))

    def test_a_profile_cannot_declare_polarity_or_authority_presentational(self):
        for field in ("polarity", "authority", "predicate", "mandatory"):
            with self.subTest(field=field):
                with self.assertRaises(SchemaValidationError) as caught:
                    S.equivalence_profile(presentation_fields=(field,))
                self.assertIn("admitted presentational set", str(caught.exception))

    def test_a_declared_ignored_metadata_key_hides_only_that_key(self):
        profile = S.equivalence_profile(ignored_metadata_keys=("ticket",))
        self.assertIn("ticket", profile.ignored_metadata_keys)
        self.assertFalse(profile.is_default)

    def test_comparing_fingerprints_across_profiles_is_refused(self):
        revision = S.admitted_revision(7)
        ours = S.fingerprint(revision, profile=S.equivalence_profile(profile_id="profile.a"))
        theirs = S.fingerprint(revision, profile=S.equivalence_profile(profile_id="profile.b"))
        with self.assertRaises(UnsupportedVersionError) as caught:
            require_same_profile(ours.profile_ref, theirs.profile_ref, "compare model fingerprints")
        self.assertIn("equivalence rules differ", str(caught.exception))
        with self.assertRaises(UnsupportedVersionError):
            S.delta(ours, theirs)

    def test_a_fingerprint_records_counts_that_describe_the_revision(self):
        item = S.fingerprint(S.admitted_revision(7))
        self.assertEqual(2, item.statement_count)
        self.assertEqual(1, item.mandatory_count)
        self.assertEqual(sorted([S.LOGO, S.TONE]), sorted(item.path_digests))

    def test_a_path_digest_that_is_not_a_digest_is_refused(self):
        item = S.fingerprint(S.admitted_revision(7))
        with self.assertRaises(SchemaValidationError):
            replace(item, path_digests={S.LOGO: "not-a-digest"})


class TestDeltaClassification(unittest.TestCase):
    def test_a_reworded_rule_reports_restated_and_stays_reusable(self):
        before = S.bundle((S.rule("cn.logo", rationale="the mark must appear"),))
        after = S.bundle((S.rule("cn.logo", rationale="show the mark on screen"),))
        delta = _bundle_delta(before, after)
        self.assertEqual((ChangeKind.RESTATED.value,), tuple(item.kind for item in delta.changes))
        self.assertFalse(delta.correctness_relevant)
        self.assertTrue(delta.empty is False)

    def test_a_rule_edit_is_classified_by_what_actually_changed(self):
        cases = (
            (
                {"strength": "ADVISORY"},
                ChangeKind.RELAXED.value,
                True,
                "a relaxation reported by diff, not by receipt",
            ),
            ({"polarity": "FORBID"}, ChangeKind.POLARITY_FLIPPED.value, True, None),
            ({"modality": "VIDEO"}, ChangeKind.RESCOPED.value, True, None),
            (
                {"authority": S.authority_ref(AuthorityLevel.HUMAN_OWNER.value)},
                ChangeKind.REAUTHORED.value,
                False,
                None,
            ),
        )
        for over, kind, relevant, note in cases:
            with self.subTest(kind=kind):
                delta = _bundle_delta(
                    S.bundle((S.rule("cn.logo"),)), S.bundle((S.rule("cn.logo", **over),))
                )
                self.assertEqual((kind,), tuple(item.kind for item in delta.changes))
                self.assertEqual(relevant, delta.correctness_relevant)
                if note:
                    self.assertIn(note, delta.changes[0].note)

    def test_a_changed_predicate_argument_is_not_read_as_a_rewording(self):
        delta = _bundle_delta(
            S.bundle((S.rule("cn.tone", S.TONE, predicate="runs_at_least", arguments={"seconds": 5}),)),
            S.bundle((S.rule("cn.tone", S.TONE, predicate="runs_at_least", arguments={"seconds": 9}),)),
        )
        self.assertEqual((ChangeKind.REPREDICATED.value,), tuple(item.kind for item in delta.changes))

    def test_a_dropped_rule_reports_removed_and_a_new_one_reports_added(self):
        delta = _bundle_delta(
            S.bundle((S.rule("cn.gone"),)), S.bundle((S.rule("cn.new", S.TONE, predicate="mentions_brand", arguments={"phrase": "x"}),))
        )
        self.assertEqual(
            [ChangeKind.ADDED.value, ChangeKind.REMOVED.value],
            sorted(item.kind for item in delta.changes),
        )

    def test_a_renamed_rule_is_not_reported_as_a_removal_plus_an_addition(self):
        delta = _bundle_delta(S.bundle((S.rule("cn.old"),)), S.bundle((S.rule("cn.new"),)))
        self.assertEqual(1, len(delta.changes))
        self.assertEqual(ChangeKind.REPREDICATED.value, delta.changes[0].kind)
        self.assertEqual((S.LOGO,), delta.touched_paths)

    def test_a_lost_protected_anchor_is_reported_separately_from_the_rule_change(self):
        anchor = ProtectedAnchor(
            anchor_id="an.logo", semantic_path=S.LOGO, statement_refs=(S.ref(RefKind.STATEMENT.value, "st.1"),)
        )
        delta = _bundle_delta(
            S.bundle((S.rule("cn.logo", protected_anchors=(anchor,), rationale="kept for the relaunch"),)),
            S.bundle((S.rule("cn.logo"),)),
        )
        kinds = [item.kind for item in delta.changes]
        self.assertIn(ChangeKind.ANCHOR_LOST.value, kinds)
        self.assertIn("no longer carried", " ".join(item.note or "" for item in delta.changes if item.note))

    def test_an_unchanged_rule_set_deltas_to_nothing(self):
        delta = _bundle_delta(S.bundle((S.rule("cn.logo"),)), S.bundle((S.rule("cn.logo"),)))
        self.assertTrue(delta.empty)
        self.assertFalse(delta.correctness_relevant)
        self.assertEqual((), delta.relevant_paths())

    def test_a_delta_recomputes_its_safety_flag_from_its_changes(self):
        before = S.fingerprint(S.admitted_revision(7))
        after = S.fingerprint(S.admitted_revision(7))
        lying = IntentDelta(
            delta_id="delta.lying",
            subject_kind="INTENT",
            before_ref=before.model_ref,
            after_ref=after.model_ref,
            profile_ref=before.profile_ref,
            changes=(
                SemanticChange(
                    change_id="chg.strength",
                    kind=ChangeKind.STRENGTHENED.value,
                    semantic_path=S.LOGO,
                    before_digest=content_digest("before"),
                    after_digest=content_digest("after"),
                ),
            ),
            correctness_relevant=False,
        )
        self.assertTrue(lying.correctness_relevant)

    def test_a_change_that_reports_movement_with_identical_digests_is_refused(self):
        with self.assertRaises(SchemaValidationError) as caught:
            SemanticChange(
                change_id="chg.invented",
                kind=ChangeKind.REPREDICATED.value,
                semantic_path=S.LOGO,
                before_digest=content_digest("same"),
                after_digest=content_digest("same"),
            )
        self.assertIn("identical digests", str(caught.exception))

    def test_a_model_delta_reports_the_paths_that_moved(self):
        before = fp(S.admitted_revision(7), ident="fp.m1")
        after = fp(
            S.revision(
                7,
                (
                    S.statement("st.1", S.LOGO, mandatory=True),
                    S.statement("st.2", S.TONE, value={"state": "warmer"}),
                ),
            ),
            ident="fp.m2",
        )
        delta = S.delta(before, after)
        self.assertEqual((S.TONE,), delta.touched_paths)
        self.assertEqual([S.TONE], list(delta.relevant_paths()))
        self.assertTrue(delta.correctness_relevant)

    def test_a_delta_digest_is_a_function_of_its_changes(self):
        before = S.fingerprint(S.admitted_revision(7))
        moved = S.fingerprint(
            S.revision(7, (S.statement("st.1", S.LOGO, value={"state": "off"}), S.statement("st.2", S.TONE)))
        )
        first = S.delta(before, moved, ident="delta.one")
        second = S.delta(before, moved, ident="delta.two")
        self.assertEqual(first.delta_digest, second.delta_digest)


def _bundle_delta(before: Any, after: Any) -> IntentDelta:
    from iris_intent.fingerprints import diff_bundles

    return diff_bundles(before, after, profile=S.equivalence_profile(), delta_id="delta.t")


def derived_dependency(
    ident: str = "dep.src",
    *,
    upstream_id: str = "src.art",
    path: Any = S.SPEC,
    dimension: FreshnessDimension = FreshnessDimension.SOURCE_REVISION,
    derived: Any = None,
    valid_through: Any = 7,
    **over: Any,
):
    """One legal dependency, with exactly the knobs a staleness test needs spelled out."""

    digest_value = over.pop("digest", S.digest(upstream_id))
    version = over.pop("version", "v1")
    bases = over.pop("match_on", ("DIGEST",))
    arguments: dict[str, Any] = {
        "dependency_id": ident,
        "derived_ref": derived or S.ref(RefKind.CONTRACT_SET.value, "contracts.iris"),
        "derived_kind": DerivedArtifactKind.CONTRACT_SET.value,
        "upstream_ref": upstream_ref_for(dimension, upstream_id),
        "dimension": dimension.value if hasattr(dimension, "value") else dimension,
        "invalidates": over.pop("invalidates", dimension.staleness_scope.value),
        "match_on": tuple(bases),
        "last_known_digest": digest_value if "DIGEST" in bases else None,
        "last_known_version": version if "VERSION" in bases else None,
        "valid_through_revision": valid_through if "REVISION_LEASE" in bases else None,
        "partial": over.pop("partial", True),
        "affected_paths": over.pop("paths", (path,) if path else ()),
        "protected_paths": over.pop("protected", ()),
        "rationale": f"the contract set was derived from {upstream_id}",
    }
    arguments.update(over)
    return DerivedIntentDependency(**arguments)


def upstream_ref_for(dimension: Any, upstream_id: str) -> Any:
    if dimension is FreshnessDimension.PROVIDER_CAPABILITY:
        return S.ref(RefKind.CAPABILITY.value, upstream_id, "v1")
    if dimension is FreshnessDimension.CONSTRAINT_BUNDLE:
        return S.ref(RefKind.BUNDLE.value, upstream_id)
    return S.ref(RefKind.SOURCE.value, upstream_id)


def freshness_for(deps: Any, *, moved: Any = (), **over: Any):
    """A vector over the given dependencies, with the listed upstream ids reported as moved."""

    items = tuple(deps)
    upstream = over.pop("upstream", None)
    if upstream is None:
        changed = set(moved)
        upstream = {
            item.upstream_key: {
                "digest": S.digest(item.upstream_ref.ref_id + (".moved" if item.upstream_ref.ref_id in changed else "")),
                "version": item.last_known_version or "v1",
                "present": True,
            }
            for item in items
        }
    return assess_freshness(
        vector_id=over.pop("vector_id", "fv.t"),
        brief_ref=S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
        revision_ref=S.revision_ref(),
        subject_ref=items[0].derived_ref,
        dependencies=items,
        upstream=upstream,
        **over,
    )


def changed_delta(kind: Any) -> IntentDelta:
    return IntentDelta(
        delta_id=f"delta.{kind.value.lower()}",
        subject_kind="INTENT",
        before_ref=S.ref(RefKind.REVISION.value, "rev.7"),
        after_ref=S.ref(RefKind.REVISION.value, "rev.8"),
        profile_ref=DEFAULT_EQUIVALENCE_PROFILE.ref,
        changes=(
            SemanticChange(
                change_id=f"chg.{kind.value.lower()}",
                kind=kind.value,
                semantic_path=S.LOGO,
                before_digest=S.digest("before"),
                after_digest=S.digest("after"),
            ),
        ),
    )


def presentation_delta() -> IntentDelta:
    """A delta whose only entry says the wording moved and nothing else did."""

    return changed_delta(ChangeKind.RESTATED)


def carriage_passport(revision: Any, *, ident: str = "pp.carriage", mapping: Any = None):
    """A passport that also depends on provider carriage, which is what makes the ladder turn."""

    ours = S.fingerprint(revision, ident=f"fp.{ident}")
    deps = (
        derived_dependency(f"dep.src.{ident}", path=S.ICON, derived=ours.model_ref),
        derived_dependency(
            f"dep.provider.{ident}",
            upstream_id="provider.capability",
            dimension=FreshnessDimension.PROVIDER_CAPABILITY,
            path=S.SPEC,
            derived=ours.model_ref,
        ),
        derived_dependency(
            f"dep.model.{ident}",
            upstream_id=f"model.{ident}",
            dimension=FreshnessDimension.SEMANTIC_MODEL,
            path=S.SPEC,
            derived=ours.model_ref,
        ),
    )
    return passport_for(
        ours,
        passport_id=ident,
        brief_ref=S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
        revision_ref=revision.revision_ref,
        dependencies=deps,
        mapping_digest=mapping if mapping is not None else S.digest("provider.mapping"),
    )


def execution_bundle(ident: str = "xb.t"):
    """A compiled execution intent over one admitted revision, for the explanation tests."""

    revision = S.admitted_revision(7)
    return compile_execution_intent(
        bundle_id=ident,
        brief_ref=revision.brief_ref,
        revision_ref=revision.revision_ref,
        intent_fingerprint_digest=fp(revision, ident=f"fp.{ident}").semantic_digest,
        constraint_fingerprint_digest=S.bundle_fingerprint(
            S.bundle([S.rule("cn.logo")]), ident=f"bfp.{ident}"
        ).semantic_digest,
        fidelity_fingerprint_digest=content_digest(f"fidelity.{ident}"),
        operations=(validating_operation(revision),),
    )


def validating_operation(revision: Any, ident: str = "io.validate") -> Any:
    return IntentOperation(
        intent_operation_id=ident,
        family="VALIDATE",
        purpose="check the admitted mark against the compiled contract",
        subject_refs=(revision.brief_ref,),
        originating_refs=(S.ref(RefKind.STATEMENT.value, "st.1"),),
        required_explanation_refs=(S.ref(RefKind.PROVENANCE.value, "cap.st.1"),),
        fidelity_contract_refs=(S.ref(RefKind.CONTRACT_SET.value, "contracts.iris"),),
    )


class TestPassportAndReuseVerdicts(unittest.TestCase):
    def setUp(self):
        self.revision = S.admitted_revision(7)
        self.passport = S.passport(self.revision, (derived_dependency("dep.src", path=S.ICON),), ident="pp.t")
        self.current = S.upstream_matching(self.passport.dependencies)

    def evaluate(self, **over):
        arguments = {
            "assessment_id": "as.t",
            "vector_id": "fv.t",
            "semantic_digest": self.passport.semantic_digest,
            "profile_ref": self.passport.profile_ref,
            "upstream": self.current,
            "revision_ordinal": 7,
        }
        arguments.update(over)
        return evaluate_reuse(self.passport, **arguments)

    def test_a_checked_passport_with_equal_digests_reuses_as_is(self):
        verdict = self.evaluate()
        self.assertEqual(ReuseVerdict.REUSE.value, verdict.verdict)
        self.assertEqual(RecomputeScope.NONE.value, verdict.recompute_scope)
        self.assertEqual((), verdict.invalidated_paths)
        self.assertTrue(verdict.reuses_semantics)
        require_reusable(verdict, action="keep the compiled contract")

    def test_a_source_only_rewording_that_a_delta_testifies_as_equivalent_still_reuses(self):
        verdict = self.evaluate(
            semantic_digest=S.digest("re-entered from the same bytes"), delta=presentation_delta()
        )
        self.assertEqual(ReuseVerdict.REUSE_EQUIVALENT.value, verdict.verdict)
        self.assertTrue(verdict.delta_testified)
        self.assertFalse(verdict.semantic_equal)
        self.assertEqual((), verdict.invalidated_paths)
        self.assertEqual(sorted([S.ICON, S.SPEC]), sorted(verdict.preserved_paths))
        require_reusable(verdict, action="keep the compiled contract")

    def test_the_same_moved_digest_without_testimony_recompiles_the_whole_artifact(self):
        verdict = self.evaluate(semantic_digest=S.digest("re-entered from the same bytes"))
        self.assertEqual(ReuseVerdict.RECOMPILE.value, verdict.verdict)
        self.assertEqual(RecomputeScope.ARTIFACT.value, verdict.recompute_scope)
        self.assertIn("no admitted delta testifies", " ".join(verdict.reasons))
        self.assertFalse(verdict.reuses_semantics)
        with self.assertRaises(StaleSemanticError) as caught:
            require_reusable(verdict, action="keep the compiled contract")
        self.assertIn("cannot keep the compiled contract", str(caught.exception))

    def test_a_correctness_relevant_delta_does_not_buy_a_reuse(self):
        verdict = self.evaluate(
            semantic_digest=S.digest("a different requirement"), delta=changed_delta(ChangeKind.STRENGTHENED)
        )
        self.assertEqual(ReuseVerdict.RECOMPILE.value, verdict.verdict)
        self.assertFalse(verdict.delta_testified)

    def test_a_moved_equivalence_profile_invalidates_comparison_itself(self):
        verdict = self.evaluate(profile_ref=S.equivalence_profile(profile_id="profile.other").ref)
        self.assertEqual(ReuseVerdict.RECOMPILE.value, verdict.verdict)
        self.assertTrue(verdict.profile_changed)
        self.assertIn("not comparable", " ".join(verdict.reasons))

    def test_an_input_that_cannot_be_checked_is_refused_rather_than_assumed_current(self):
        verdict = self.evaluate(
            upstream={key: value for key, value in self.current.items() if "src.art" not in key}
        )
        self.assertEqual(ReuseVerdict.REFUSE_UNVERIFIED.value, verdict.verdict)
        self.assertIn(FreshnessDimension.SOURCE_REVISION.value, verdict.unknown_dimensions)
        self.assertFalse(verdict.reuses_semantics)

    def test_a_moved_source_invalidates_only_the_paths_its_dependency_feeds(self):
        verdict = self.evaluate(upstream=S.upstream_matching(self.passport.dependencies, moved=("src.art",)))
        self.assertEqual(ReuseVerdict.RECOMPILE.value, verdict.verdict)
        self.assertEqual(RecomputeScope.PATHS.value, verdict.recompute_scope)
        self.assertEqual((S.ICON,), verdict.invalidated_paths)
        self.assertEqual((S.SPEC,), verdict.preserved_paths)
        self.assertEqual([S.ICON], list(verdict.rebuilds))
        self.assertIn(FreshnessDimension.SOURCE_REVISION.value, verdict.stale_dimensions)

    def test_a_total_dependency_takes_the_whole_artifact_with_it(self):
        total = derived_dependency("dep.total", paths=(), partial=False)
        passport = S.passport(self.revision, (total,), ident="pp.total")
        verdict = evaluate_reuse(
            passport,
            assessment_id="as.total",
            vector_id="fv.total",
            semantic_digest=passport.semantic_digest,
            profile_ref=passport.profile_ref,
            upstream=S.upstream_matching(passport.dependencies, moved=("src.art",)),
            revision_ordinal=7,
        )
        self.assertEqual(RecomputeScope.ARTIFACT.value, verdict.recompute_scope)
        self.assertTrue(requires_whole(passport, verdict.freshness))
        self.assertEqual((S.SPEC,), verdict.invalidated_paths)
        self.assertEqual((), verdict.preserved_paths)
        self.assertEqual(("*",), verdict.rebuilds)

    def test_a_provider_move_rebuilds_carriage_and_leaves_the_requirement_alone(self):
        passport = carriage_passport(self.revision)
        verdict = evaluate_reuse(
            passport,
            assessment_id="as.carriage",
            vector_id="fv.carriage",
            semantic_digest=passport.semantic_digest,
            profile_ref=passport.profile_ref,
            mapping_digest=S.digest("an older mapping"),
            upstream=S.upstream_matching(passport.dependencies, moved=("provider.capability",)),
            revision_ordinal=7,
        )
        self.assertEqual(ReuseVerdict.REUSE_SEMANTICS_ONLY.value, verdict.verdict)
        self.assertEqual(RecomputeScope.MAPPING.value, verdict.recompute_scope)
        self.assertTrue(verdict.semantic_equal)
        self.assertEqual((), verdict.invalidated_paths)
        self.assertTrue(verdict.freshness.semantics_hold)
        self.assertEqual(sorted([S.ICON, S.SPEC]), sorted(verdict.preserved_paths))

    def test_a_passport_that_declares_no_inputs_cannot_earn_reuse(self):
        with self.assertRaises(SchemaValidationError) as caught:
            ReusePassport(
                passport_id="pp.bare",
                subject_ref=self.passport.subject_ref,
                subject_kind=self.passport.subject_kind,
                brief_ref=self.passport.brief_ref,
                revision_ref=self.passport.revision_ref,
                profile_ref=self.passport.profile_ref,
                semantic_digest=self.passport.semantic_digest,
                dependencies=(),
            )
        self.assertIn("declares no dependencies", str(caught.exception))

    def test_a_passport_must_cite_the_revision_and_model_it_came_from(self):
        ours = S.fingerprint(self.revision, ident="fp.bare")
        with self.assertRaises(SchemaValidationError) as caught:
            passport_for(
                ours,
                passport_id="pp.model.only",
                brief_ref=S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
                revision_ref=self.revision.revision_ref,
                dependencies=(
                    derived_dependency(
                        "dep.model", dimension=FreshnessDimension.SEMANTIC_MODEL, derived=ours.model_ref
                    ),
                ),
            )
        self.assertIn("declares no dependency on", str(caught.exception))

    def test_a_dependency_of_another_artifact_cannot_license_this_one(self):
        ours = S.fingerprint(self.revision, ident="fp.foreign")
        with self.assertRaises(SchemaValidationError) as caught:
            ReusePassport(
                passport_id="pp.foreign",
                subject_ref=ours.model_ref,
                subject_kind=DerivedArtifactKind.CONTRACT_SET.value,
                brief_ref=S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
                revision_ref=self.revision.revision_ref,
                profile_ref=ours.profile_ref,
                semantic_digest=ours.semantic_digest,
                dependencies=(
                    derived_dependency("dep.other", derived=S.ref(RefKind.CONTRACT_SET.value, "contracts.other")),
                    derived_dependency("dep.model", dimension=FreshnessDimension.SEMANTIC_MODEL),
                    derived_dependency("dep.rev"),
                ),
            )
        self.assertIn("other artifacts", str(caught.exception))

    def test_an_assessment_cannot_pair_a_reuse_verdict_with_a_whole_rebuild(self):
        verdict = self.evaluate()
        with self.assertRaises(SchemaValidationError) as caught:
            replace(verdict, recompute_scope=RecomputeScope.ARTIFACT.value)
        self.assertIn("is not one of", str(caught.exception))

    def test_an_assessment_cannot_report_staleness_its_vector_did_not_see(self):
        verdict = self.evaluate()
        with self.assertRaises(SchemaValidationError) as caught:
            replace(verdict, stale_dimensions=(FreshnessDimension.POLICY_VERSION.value,))
        self.assertIn("where its vector says", str(caught.exception))

    def test_a_reuse_decision_nobody_can_explain_is_refused(self):
        verdict = self.evaluate()
        with self.assertRaises(SchemaValidationError) as caught:
            replace(verdict, reasons=())
        self.assertIn("carries no reason", str(caught.exception))

    def test_the_provider_neutral_half_of_two_derivations_is_comparable(self):
        first = carriage_passport(self.revision, ident="pp.a")
        second = carriage_passport(self.revision, ident="pp.b", mapping=S.digest("provider.other"))
        self.assertEqual(first.provider_neutral_key, second.provider_neutral_key)
        self.assertNotEqual(first.full_key, second.full_key)
        self.assertEqual(first.semantic_paths, second.semantic_paths)
        self.assertTrue(first.carries_mapping and second.carries_mapping)


class TestFreshnessEvidence(unittest.TestCase):
    def test_a_declared_axis_that_was_never_checked_reports_unknown_and_blocks(self):
        item = derived_dependency("dep.src")
        vector = assess_freshness(
            vector_id="fv.gap",
            brief_ref=S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
            revision_ref=S.revision_ref(),
            subject_ref=item.derived_ref,
            dependencies=(item,),
            upstream=S.upstream_matching((item,)),
            declared_dimensions=(
                FreshnessDimension.SOURCE_REVISION.value,
                FreshnessDimension.AUTHORITY_POLICY.value,
            ),
        )
        self.assertEqual(
            FreshnessState.UNKNOWN.value, vector.state_for(FreshnessDimension.AUTHORITY_POLICY.value)
        )
        self.assertIn(FreshnessDimension.AUTHORITY_POLICY.value, vector.unknown_dimensions)
        self.assertEqual([FreshnessDimension.AUTHORITY_POLICY.value], list(vector.unreported_dimensions))
        with self.assertRaises(StaleSemanticError) as caught:
            require_fresh(vector, action="compile the contract")
        self.assertIn("could not be checked", str(caught.exception))

    def test_a_moved_digest_is_stale_and_the_comparison_names_which_side_moved(self):
        item = derived_dependency("dep.src")
        vector = freshness_for((item,), moved=("src.art",))
        self.assertEqual(
            FreshnessState.STALE.value, vector.state_for(FreshnessDimension.SOURCE_REVISION.value)
        )
        self.assertEqual([FreshnessEvidence.DIGEST_MISMATCH.value], list(vector.decisive_evidence))
        self.assertFalse(vector.timestamp_only)
        self.assertEqual([FreshnessDimension.SOURCE_REVISION.value], list(vector.stale_dimensions))
        self.assertEqual((item.dependency_id,), affected_dependency_ids((item,), vector))
        require_fresh(freshness_for((item,)), action="compile the contract")

    def test_a_mapping_axis_never_reaches_the_requirement_itself(self):
        item = derived_dependency(
            "dep.provider", upstream_id="provider.capability", dimension=FreshnessDimension.PROVIDER_CAPABILITY
        )
        vector = freshness_for((item,), moved=("provider.capability",))
        self.assertTrue(vector.mapping_only_stale)
        self.assertFalse(vector.semantic_stale)
        self.assertEqual(DerivedScope.MAPPING.value, item.invalidates)
        with self.assertRaises(StaleSemanticError) as refused:
            require_fresh(vector, action="re-derive the semantics")
        self.assertIn("only carriage is stale", str(refused.exception))
        require_fresh(vector, action="redo the carriage", allow_mapping_stale=True)

    def test_a_dependency_on_a_lease_expires_by_position_not_by_clock(self):
        item = derived_dependency("dep.lease", match_on=("REVISION_LEASE",), valid_through=7)
        current = freshness_for((item,), revision_ordinal=7)
        self.assertEqual(FreshnessState.CURRENT.value, current.worst_state.value)
        expired = freshness_for((item,), revision_ordinal=9)
        self.assertEqual(FreshnessState.EXPIRED.value, expired.worst_state.value)
        self.assertIn(FreshnessEvidence.LEASE_EXCEEDED.value, expired.decisive_evidence)
        unbounded = freshness_for((item,))
        self.assertEqual(FreshnessState.UNKNOWN.value, unbounded.worst_state.value)

    def test_the_rework_split_follows_the_declared_scope_of_each_dependency(self):
        semantics = derived_dependency("dep.src", path=S.ICON)
        carriage = derived_dependency(
            "dep.provider", upstream_id="provider.capability", dimension=FreshnessDimension.PROVIDER_CAPABILITY
        )
        bundle_dep = derived_dependency(
            "dep.bundle",
            upstream_id="bundle.t",
            dimension=FreshnessDimension.CONSTRAINT_BUNDLE,
            path=S.TONE,
        )
        vector = freshness_for(
            (semantics, carriage, bundle_dep), moved=("src.art", "provider.capability", "bundle.t")
        )
        split = affected_paths((semantics, carriage, bundle_dep), vector)
        self.assertEqual(tuple(sorted([S.ICON, S.TONE])), split[DerivedScope.SEMANTICS.value])
        self.assertEqual((S.SPEC,), split[DerivedScope.MAPPING.value])
        self.assertFalse(requires_whole_artifact((semantics, carriage, bundle_dep), vector))

    def test_a_dependency_that_cannot_say_what_it_checked_is_refused(self):
        cases = (
            (
                {"dimension": FreshnessDimension.SOURCE_REVISION, "invalidates": DerivedScope.MAPPING.value},
                "whose staleness reaches",
            ),
            ({"match_on": ()}, "declares no basis"),
            ({"match_on": ("TIMESTAMP",)}, "timestamps are never sufficient"),
            ({"match_on": ("DIGEST",), "digest": None}, "without recording the digest"),
            ({"match_on": ("VERSION",), "version": None}, "without recording the version"),
            ({"match_on": ("REVISION_LEASE",), "valid_through": None}, "with no bound"),
            ({"partial": True, "paths": ()}, "naming no affected path"),
            ({"partial": False, "paths": (S.ICON,)}, "total invalidation"),
            ({"paths": (S.ICON,), "protected": (S.ICON,)}, "both invalidates and protects"),
        )
        for over, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(SchemaValidationError) as caught:
                    derived_dependency("dep.bad", **over)
                self.assertIn(message, str(caught.exception))

    def test_a_signal_whose_operands_disagree_with_its_own_verdict_is_refused(self):
        with self.assertRaises(SchemaValidationError) as caught:
            FreshnessSignal(
                signal_id="sig.lie",
                dimension=FreshnessDimension.SOURCE_REVISION.value,
                evidence=FreshnessEvidence.DIGEST_MATCH.value,
                expected=S.digest("one thing"),
                observed=S.digest("another thing"),
            )
        self.assertIn("contradict it", str(caught.exception))
        with self.assertRaises(SchemaValidationError) as empty:
            FreshnessSignal(
                signal_id="sig.nooperands",
                dimension=FreshnessDimension.SOURCE_REVISION.value,
                evidence=FreshnessEvidence.DIGEST_MISMATCH.value,
            )
        self.assertIn("without both digests", str(empty.exception))

    def test_a_vector_that_declares_nothing_is_a_pass_slot_rather_than_a_check(self):
        item = derived_dependency("dep.src")
        vector = freshness_for((item,))
        with self.assertRaises(SchemaValidationError) as caught:
            replace(vector, declared_dimensions=())
        self.assertIn("declares no axes", str(caught.exception))
        with self.assertRaises(SchemaValidationError) as orphan:
            replace(vector, dependency_ids=())
        self.assertIn("undeclared dependencies", str(orphan.exception))

    def test_a_missing_upstream_is_reported_as_missing_and_not_as_current(self):
        item = derived_dependency("dep.src")
        signals = item.signals({"somewhere.else": {}}, None)
        self.assertEqual(1, len(signals))
        self.assertEqual(FreshnessEvidence.ABSENT.value, signals[0].evidence)
        self.assertEqual(FreshnessState.MISSING.value, item.check({"somewhere.else": {}}).state.value)
        self.assertTrue(item.semantics_at_risk)
        self.assertEqual(item.affected_paths, item.rework_paths)
        total = derived_dependency("dep.total", paths=(), partial=False)
        self.assertEqual((), total.rework_paths)
        self.assertTrue(requires_whole_artifact((total,), freshness_for((total,), moved=("src.art",))))

    def test_the_same_positions_on_the_same_axes_are_the_same_vector(self):
        first = derived_dependency("dep.src", path=S.ICON)
        second = derived_dependency("dep.src.two", path=S.ICON)
        left = freshness_for((first,))
        right = freshness_for((second,))
        self.assertEqual(left.states, right.states)
        self.assertNotEqual(left.vector_ref, right.vector_ref)
        self.assertFalse(left.covers(second.dependency_id))
        self.assertTrue(left.covers(first.dependency_id))

    def test_an_assessment_over_a_moved_model_rebuilds_only_the_model_half(self):
        revision = S.admitted_revision(7)
        passport = S.passport(revision, (derived_dependency("dep.src", path=S.ICON),), ident="pp.chain")
        moved_model = f"model.{passport.passport_id}"
        verdict = evaluate_reuse(
            passport,
            assessment_id="as.chain",
            vector_id="fv.chain",
            semantic_digest=passport.semantic_digest,
            profile_ref=passport.profile_ref,
            upstream=S.upstream_matching(passport.dependencies, moved=(moved_model,)),
            revision_ordinal=7,
        )
        self.assertEqual(ReuseVerdict.RECOMPILE.value, verdict.verdict)
        self.assertEqual((S.SPEC,), verdict.invalidated_paths)
        self.assertEqual((S.ICON,), verdict.preserved_paths)
        self.assertIn(FreshnessDimension.SEMANTIC_MODEL.value, verdict.stale_dimensions)


class TestExplanationReachability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = execution_bundle()
        cls.graph = compile_explanation_graph(cls.bundle, graph_id="ieg.t")

    def operation_node(self):
        return next(item for item in self.graph.emitted_nodes if item.kind == ExplanationNodeKind.INTENT_OPERATION.value)

    def test_every_compiled_obligation_walks_to_an_admitted_ground(self):
        facts = self.graph.canonical_facts()
        self.assertEqual(sorted(item.node_id for item in self.graph.emitted_nodes), sorted(facts))
        for node in self.graph.emitted_nodes:
            path = self.graph.path_to_ground(node.node_id)
            self.assertGreaterEqual(len(path), 2)
            self.assertTrue(self.graph.node(path[-1]).is_ground)
            self.assertIn(self.graph.node(path[-1]).subject_text, facts[node.node_id])

    def test_the_grounds_are_sources_or_policy_never_m03_bookkeeping(self):
        for node in self.graph.ground_nodes:
            self.assertIn(node.subject_ref.kind, ROOT_CLASSIFICATION)
            self.assertEqual(node.record_digest, node.subject_ref.content_digest)
        self.assertEqual(
            ExplanationNodeKind.RAW_SOURCE.value, ground_kind_for(S.ref(RefKind.SOURCE.value, "src.brief"))
        )
        self.assertEqual(ExplanationNodeKind.GOVERNED_POLICY.value, ground_kind_for(S.policy_ref()))

    def test_a_capability_cannot_be_its_own_reason(self):
        for kind in (RefKind.CAPABILITY.value, RefKind.RECEIPT.value, RefKind.PASSPORT.value):
            with self.subTest(kind=kind):
                with self.assertRaises(ExplanationError) as caught:
                    ground_kind_for(S.ref(kind, f"thing.{kind.lower()}"))
                self.assertIn("cannot ground a claim", str(caught.exception))

    def test_an_operation_stranded_from_its_grounds_cannot_be_explained(self):
        node = self.operation_node()
        with self.assertRaises(ExplanationError) as caught:
            replace(
                self.graph,
                graph_id="ieg.stranded",
                edges=tuple(item for item in self.graph.edges if item.from_node != node.node_id),
            )
        self.assertIn("no path to admitted source semantics", str(caught.exception))

    def test_an_edge_pointing_at_nothing_is_refused_rather_than_ignored(self):
        node = self.operation_node()
        edge = ExplanationEdge(
            edge_id="e.nowhere",
            relation=ExplanationEdgeKind.DERIVED_FROM.value,
            from_node=node.node_id,
            to_node="n-not-here",
        )
        with self.assertRaises(ExplanationError) as caught:
            replace(self.graph, graph_id="ieg.dangling", edges=self.graph.edges + (edge,))
        self.assertIn("which this graph does not carry", str(caught.exception))

    def test_a_loop_of_reasons_answers_why_with_because(self):
        first = ExplanationNode(
            node_id="n.op.a", kind=ExplanationNodeKind.INTENT_OPERATION.value, record_digest=S.digest("a"), label="op a"
        )
        second = ExplanationNode(
            node_id="n.demand.b",
            kind=ExplanationNodeKind.CAPABILITY_DEMAND.value,
            record_digest=S.digest("b"),
            label="demand b",
        )
        with self.assertRaises(ExplanationError) as caught:
            IntentExplanationGraph(
                graph_id="ieg.cycle",
                bundle_ref=self.graph.bundle_ref,
                bundle_digest=self.graph.bundle_digest,
                semantic_digest=self.graph.semantic_digest,
                nodes=(first, second),
                edges=(
                    ExplanationEdge(
                        edge_id="e.ab",
                        relation=ExplanationEdgeKind.REQUIRED_BY.value,
                        from_node="n.op.a",
                        to_node="n.demand.b",
                    ),
                    ExplanationEdge(
                        edge_id="e.ba",
                        relation=ExplanationEdgeKind.REQUIRED_BY.value,
                        from_node="n.demand.b",
                        to_node="n.op.a",
                    ),
                ),
            )
        self.assertIn("cyclic at", str(caught.exception))

    def test_an_edge_that_explains_a_node_with_itself_is_refused(self):
        with self.assertRaises(SchemaValidationError) as caught:
            ExplanationEdge(
                edge_id="e.self",
                relation=ExplanationEdgeKind.DERIVED_FROM.value,
                from_node="n.op.a",
                to_node="n.op.a",
            )
        self.assertIn("explains n.op.a with itself", str(caught.exception))

    def test_a_ground_that_disagrees_with_the_ref_it_cites_is_refused(self):
        ground = self.graph.ground_nodes[0]
        with self.assertRaises(SchemaValidationError) as caught:
            replace(ground, record_digest=S.digest("a stale copy"))
        self.assertIn("disagrees with the ref it cites", str(caught.exception))

    def test_an_emitted_node_may_not_carry_a_second_pointer(self):
        node = self.operation_node()
        with self.assertRaises(SchemaValidationError) as caught:
            replace(node, subject_ref=S.ref(RefKind.STATEMENT.value, "st.1"))
        self.assertIn("carries a subject ref", str(caught.exception))

    def test_why_a_node_exists_is_answered_by_a_path_not_by_prose(self):
        node = self.operation_node()
        answer = why_node(self.graph, node.node_id)
        self.assertEqual(node.node_id, answer["node"])
        self.assertEqual(ExplanationNodeKind.INTENT_OPERATION.value, answer["kind"])
        self.assertEqual(len(answer["path"]) - 1, len(answer["relations"]))
        self.assertTrue(answer["reasons"])
        self.assertTrue(set(answer["relations"]) <= {item.value for item in ExplanationEdgeKind})
        self.assertIn(ExplanationEdgeKind.DERIVED_FROM.value, self.graph.relation_kinds)
        self.assertTrue(reachable_roots(self.graph, node.node_id))

    def test_a_request_for_a_walk_from_a_ground_reports_that_it_reaches_no_ground(self):
        ground = self.graph.ground_nodes[0]
        with self.assertRaises(ExplanationError) as caught:
            self.graph.path_to_ground(ground.node_id)
        self.assertIn("reaches no ground", str(caught.exception))
        with self.assertRaises(ExplanationError) as missing:
            self.graph.node("n.never-compiled")
        self.assertIn("carries no node", str(missing.exception))

    def test_every_explanation_level_renders_the_same_canonical_facts(self):
        projections = {level.value: project_explanation(self.graph, level.value) for level in ExplanationLevel}
        self.assertEqual(4, len(projections))
        for level, projection in projections.items():
            self.assertEqual(self.graph.canonical_facts(), projection.canonical_facts, level)
            self.assertEqual(self.graph.node_count, projection.rendered_node_count)
            projection.verify_against(self.graph)
        self.assertEqual(explanation_levels(), tuple(projections))

    def test_a_machine_trace_may_not_smuggle_a_narrative(self):
        packet = project_explanation(self.graph, ExplanationLevel.TRACE_ID_ONLY.value)
        self.assertEqual((), tuple(item for item in packet.entries if item.label or item.narrative))
        with self.assertRaises(SchemaValidationError) as caught:
            replace(
                packet,
                projection_id="eip.smuggled",
                entries=tuple(replace(item, narrative="because the owner said so") for item in packet.entries),
            )
        self.assertIn("at level TRACE_ID_ONLY", str(caught.exception))

    def test_the_audit_level_is_the_only_one_that_carries_the_chain(self):
        audit = project_explanation(self.graph, ExplanationLevel.AUDIT.value)
        human = project_explanation(self.graph, ExplanationLevel.HUMAN.value)
        for entry in audit.entries:
            self.assertTrue(entry.provenance)
        self.assertIn("compiler", audit.entries[0].provenance)
        with self.assertRaises(SchemaValidationError) as caught:
            replace(
                audit,
                projection_id="eip.bare",
                entries=tuple(replace(item, provenance={}) for item in audit.entries),
            )
        self.assertIn("claims AUDIT with no provenance", str(caught.exception))
        self.assertNotEqual(human.render(), audit.render())

    def test_a_projection_served_after_the_graph_moved_is_refused(self):
        packet = project_explanation(self.graph, ExplanationLevel.COMPACT.value)
        cited = S.ref(RefKind.CONSTRAINT.value, "cn.extra")
        extra = ExplanationNode(
            node_id="n.extra-ground",
            kind=ExplanationNodeKind.CONSTRAINT.value,
            record_digest=cited.content_digest,
            subject_ref=cited,
        )
        moved = replace(self.graph, graph_id="ieg.moved", nodes=self.graph.nodes + (extra,))
        with self.assertRaises(StaleSemanticError) as caught:
            packet.verify_against(moved)
        self.assertIn("rendered from a different graph", str(caught.exception))

    def test_a_bounded_rendering_says_so_instead_of_looking_short(self):
        packet = project_explanation(self.graph, ExplanationLevel.COMPACT.value, projection_id="eip.t")
        self.assertFalse(packet.is_bounded_rendering)
        with self.assertRaises(SchemaValidationError) as caught:
            replace(packet, canonical_facts={})
        self.assertIn("carries no canonical facts", str(caught.exception))

    def test_an_empty_explanation_would_imply_an_intent_needing_no_reason(self):
        with self.assertRaises(SchemaValidationError) as caught:
            replace(self.graph, graph_id="ieg.empty", nodes=(), edges=())
        self.assertIn("explains nothing", str(caught.exception))

    def test_a_graph_whose_bundle_pointer_and_digest_disagree_is_refused(self):
        with self.assertRaises(SchemaValidationError) as caught:
            replace(self.graph, bundle_digest=S.digest("a different compilation"))
        self.assertIn("while recording bundle digest", str(caught.exception))


class TestExplanationCacheKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = execution_bundle()
        cls.graph = compile_explanation_graph(cls.bundle, graph_id="ieg.cache")

    def test_the_key_ignores_wording_and_publishes_what_it_ignores(self):
        key = explanation_cache_key(self.bundle, self.graph, level=ExplanationLevel.COMPACT.value)
        for excluded in ("revision_text", "raw_input_digest", "provider_receipt", "explanation_rendering"):
            self.assertIn(excluded, key.excluded_inputs)
        self.assertTrue(key.describes(bundle=self.bundle, graph=self.graph))
        require_cache_valid(key, bundle=self.bundle, graph=self.graph, action="serve the cached trace")

    def test_a_key_for_another_level_does_not_describe_this_packet(self):
        compact = explanation_cache_key(self.bundle, self.graph, level=ExplanationLevel.COMPACT.value)
        audit = explanation_cache_key(self.bundle, self.graph, level=ExplanationLevel.AUDIT.value)
        self.assertNotEqual(compact.token, audit.token)
        self.assertNotEqual(compact.level, audit.level)
        other = execution_bundle(ident="xb.other")
        with self.assertRaises(StaleSemanticError) as caught:
            require_cache_valid(compact, bundle=other, graph=compile_explanation_graph(other), action="serve the cached trace")
        self.assertIn("are no longer the ones in graph", str(caught.exception))

    def test_a_key_over_a_graph_that_explains_another_intent_is_refused(self):
        other = execution_bundle(ident="xb.other")
        mismatched = compile_explanation_graph(other, graph_id="ieg.other")
        with self.assertRaises(ExplanationError) as caught:
            explanation_cache_key(self.bundle, mismatched)
        self.assertIn("while bundle", str(caught.exception))

    def test_a_key_that_ignores_semantics_would_cache_a_lie_forever(self):
        with self.assertRaises(SchemaValidationError) as caught:
            ExplanationCacheKey(key_id="eck.bare", source_fingerprints=(), operation_fingerprint=S.digest("ops"))
        self.assertIn("keyed on no source fingerprint", str(caught.exception))
        with self.assertRaises(SchemaValidationError) as open_ended:
            ExplanationCacheKey(
                key_id="eck.open",
                source_fingerprints=(S.digest("fp"),),
                operation_fingerprint=S.digest("ops"),
                excluded_inputs=(),
            )
        self.assertIn("declares nothing excluded", str(open_ended.exception))

    def test_two_runs_of_one_intent_produce_one_cache_token(self):
        again = compile_explanation_graph(self.bundle, graph_id="ieg.again")
        first = explanation_cache_key(self.bundle, self.graph)
        second = explanation_cache_key(self.bundle, again)
        self.assertEqual(first.token, second.token)
        self.assertEqual(first.fingerprint_inputs(), second.fingerprint_inputs())


if __name__ == "__main__":
    unittest.main()
