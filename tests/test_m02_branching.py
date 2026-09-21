"""Area C branch law: a ref moves, an identity does not, and a variant cannot smuggle an anchor.

Three failures are the reason this file exists. A branch that can be re-registered
with different identity data lets a project rewrite its own history; a head that
advances without an expected-value check lets two workers overwrite each other; and
a variant axis that carries a spokesperson's face lets an "outfit switch" change who
the production is. Each is a refusal here, not a convention in a docstring.

Variants are validated before anything is built, because the expensive part of a
production is the render, and an illegal combination that only fails during
execution has already cost the project a day.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_project_os.branching import (
    Branch,
    BranchLedger,
    BranchProfile,
    BranchRef,
    BranchState,
    ConstraintKind,
    ExperimentPlan,
    ForkReceipt,
    IdentityAnchorPolicy,
    PinReason,
    RetentionPin,
    VariantConstraint,
    VariantOption,
    VariantSelection,
    VariantSet,
    anchor_rulings,
    anchor_violations,
    resolve_selection,
    selection_rulings,
    validate_selection,
)
from iris_project_os.errors import (
    GraphValidationError,
    IdentityError,
    SchemaValidationError,
    UnsupportedVersionError,
)
from iris_project_os.graph import DependencyFacet
from iris_project_os.identity import EntityKind, new_id
from iris_project_os.versions import CONTRACT_VERSION

from tests import m02_kernel_support as k

PROD = "prod.logo"


def option(option_id: str = "web", *, seed: str | None = None, **over: Any) -> VariantOption:
    payload: dict[str, Any] = dict(option_id=option_id, content_digest=k.digest(seed or f"option.{option_id}"))
    payload.update(over)
    return VariantOption(**payload)


def variant_set(set_id: str = "variant.outfit", **over: Any) -> VariantSet:
    payload: dict[str, Any] = dict(
        variant_set_id=set_id,
        purpose="switches the delivery treatment",
        options=(option("web"), option("print")),
    )
    payload.update(over)
    return VariantSet(**payload)


def anchor(**over: Any) -> IdentityAnchorPolicy:
    payload: dict[str, Any] = dict(
        anchor_id="anchor.persona",
        policy_ref=k.ref(EntityKind.POLICY, "policy.persona"),
        baseline_digest=k.digest("face.baseline"),
    )
    payload.update(over)
    return IdentityAnchorPolicy(**payload)


def selection(pairs: Any = (), **over: Any) -> VariantSelection:
    payload: dict[str, Any] = dict(selection_id=new_id(), pairs=tuple(pairs))
    payload.update(over)
    return VariantSelection(**payload)


def constraint(**over: Any) -> VariantConstraint:
    payload: dict[str, Any] = dict(
        constraint_id="constraint.keynote-launch",
        kind=ConstraintKind.REQUIRES,
        when_set="variant.outfit",
        when_option="print",
        target_set="variant.quality",
        target_options=("master",),
    )
    payload.update(over)
    return VariantConstraint(**payload)


def branch_ref(**over: Any) -> BranchRef:
    payload: dict[str, Any] = dict(branch_id=new_id())
    payload.update(over)
    return BranchRef(**payload)


def branch(**over: Any) -> Branch:
    payload: dict[str, Any] = dict(
        branch_id=new_id(),
        project_id=new_id(),
        production_id=new_id(),
        profile=BranchProfile.CANONICAL,
        created_at_ms=k.CACHE_NOW,
    )
    payload.update(over)
    return Branch(**payload)


def plan(**over: Any) -> ExperimentPlan:
    payload: dict[str, Any] = dict(
        experiment_id=new_id(),
        origin_snapshot_id=new_id(),
        hypothesis="a warmer grade tests better on the launch page",
    )
    payload.update(over)
    return ExperimentPlan(**payload)


def pin(**over: Any) -> RetentionPin:
    payload: dict[str, Any] = dict(
        pin_id=new_id(),
        target=k.ref(EntityKind.SNAPSHOT, new_id()),
    )
    payload.update(over)
    return RetentionPin(**payload)


class BranchProfileTests(unittest.TestCase):
    def test_only_an_experiment_is_bounded_by_a_plan(self) -> None:
        self.assertTrue(BranchProfile.EXPERIMENT.is_bounded)
        for profile in (BranchProfile.CANONICAL, BranchProfile.CAMPAIGN, BranchProfile.EPISODE_SHOT, BranchProfile.RELEASE):
            self.assertFalse(profile.is_bounded)

    def test_only_release_and_canonical_may_hold_a_release(self) -> None:
        self.assertTrue(BranchProfile.RELEASE.may_hold_release)
        self.assertTrue(BranchProfile.CANONICAL.may_hold_release)
        self.assertFalse(BranchProfile.EXPERIMENT.may_hold_release)
        self.assertFalse(BranchProfile.CAMPAIGN.may_hold_release)

    def test_surrounding_space_is_not_part_of_a_profile_name(self) -> None:
        self.assertIs(BranchProfile.parse("  canonical  "), BranchProfile.CANONICAL)
        with self.assertRaises(SchemaValidationError):
            BranchProfile.parse("episode shot")
        with self.assertRaises(SchemaValidationError):
            BranchProfile.parse("side-branch")


class BranchStateTests(unittest.TestCase):
    def test_only_active_accepts_an_advance(self) -> None:
        self.assertTrue(BranchState.ACTIVE.accepts_advance)
        for state in (BranchState.FROZEN, BranchState.ABANDONED, BranchState.ARCHIVED):
            self.assertFalse(state.accepts_advance)


class IdentityAnchorPolicyTests(unittest.TestCase):
    def test_the_baseline_is_reachable_through_a_uuid_anchor_id(self) -> None:
        value = anchor(baseline_option_id="web")
        self.assertEqual(value.anchor_id, "anchor.persona")
        self.assertEqual(value.policy_ref.kind, EntityKind.POLICY)

    def test_a_malformed_policy_reference_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            anchor(policy_ref="policy.persona")

    def test_an_unprotected_digest_never_drifts(self) -> None:
        value = anchor()
        self.assertFalse(value.drifts(None))
        self.assertFalse(value.drifts(k.digest("face.baseline")))
        self.assertTrue(value.drifts(k.digest("face.other")))

    def test_no_drift_needs_no_authority(self) -> None:
        self.assertTrue(anchor().authorize(k.digest("face.baseline"), ()))
        self.assertTrue(anchor().authorize(None, ()))

    def test_drift_is_authorised_by_any_valid_migration_receipt(self) -> None:
        receipt = new_id()
        self.assertTrue(anchor().authorize(k.digest("face.other"), (receipt,)))
        self.assertFalse(anchor().authorize(k.digest("face.other"), ()))

    def test_a_forged_migration_receipt_is_refused_not_ignored(self) -> None:
        with self.assertRaises(SchemaValidationError):
            anchor().authorize(k.digest("face.other"), ("not-a-uuid",))


class VariantOptionTests(unittest.TestCase):
    def test_the_text_form_names_both_halves_of_the_switch(self) -> None:
        value = option("web", seed="bytes.web")
        self.assertEqual(value.text, f"web={k.digest('bytes.web')}")

    def test_a_content_digest_must_be_a_digest(self) -> None:
        with self.assertRaises(SchemaValidationError):
            VariantOption(option_id="web", content_digest="sha256:abc")

    def test_free_text_may_not_be_parked_in_the_intent_field(self) -> None:
        with self.assertRaises(SchemaValidationError):
            option("web", intent_ref="brief.v3")

    def test_the_anchor_digest_uses_the_same_grammar(self) -> None:
        with self.assertRaises(SchemaValidationError):
            option("web", anchor_digest="FACE")


class VariantSetTests(unittest.TestCase):
    def test_options_are_ordered_by_id_so_the_digest_is_stable(self) -> None:
        first = variant_set(options=(option("print"), option("web")))
        second = variant_set(options=(option("web"), option("print")))
        self.assertEqual(first.options, second.options)
        self.assertEqual(first.option_ids, ("print", "web"))

    def test_duplicate_options_would_make_the_axis_ambiguous(self) -> None:
        with self.assertRaises(GraphValidationError):
            variant_set(options=(option("web"), option("web", seed="other")))

    def test_a_default_outside_the_offered_options_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            variant_set(default_option_id="cinema")

    def test_an_empty_axis_switches_nothing(self) -> None:
        with self.assertRaises(GraphValidationError):
            variant_set(options=())

    def test_an_axis_must_declare_what_it_affects(self) -> None:
        with self.assertRaises(GraphValidationError):
            variant_set(affected_facets=())

    def test_facets_are_deduplicated_and_sorted(self) -> None:
        value = variant_set(
            affected_facets=(DependencyFacet.RIGHTS, DependencyFacet.CONTENT, DependencyFacet.CONTENT)
        )
        self.assertEqual(value.affected_facets, (DependencyFacet.CONTENT, DependencyFacet.RIGHTS))

    def test_an_unknown_option_names_what_the_axis_does_offer(self) -> None:
        value = variant_set()
        with self.assertRaises(GraphValidationError) as caught:
            value.option("cinema")
        self.assertIn("it offers", str(caught.exception))
        self.assertIn("'web'", str(caught.exception))

    def test_the_option_count_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            variant_set(options=tuple(option(f"opt-{index}") for index in range(129)))

    def test_a_protected_axis_refuses_an_option_nobody_checked(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            variant_set(
                identity_anchor=anchor(),
                options=(
                    option("web", anchor_digest=k.digest("face.baseline"), migration_receipt_id=None),
                    option("print"),
                ),
            )
        self.assertIn("a protected axis cannot carry an alternative nobody checked", str(caught.exception))

    def test_a_protected_axis_must_name_the_option_that_preserves_the_anchor(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            variant_set(
                identity_anchor=anchor(),
                options=(
                    option("web", anchor_digest=k.digest("face.other"), migration_receipt_id=new_id()),
                    option("print", anchor_digest=k.digest("face.baseline")),
                ),
            )
        self.assertIn("must name the baseline option that preserves it", str(caught.exception))

    def test_drifting_the_anchor_without_a_migration_is_refused(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            variant_set(
                identity_anchor=anchor(baseline_option_id="web"),
                options=(
                    option("web", anchor_digest=k.digest("face.baseline")),
                    option("print", anchor_digest=k.digest("face.other")),
                ),
            )
        self.assertIn("without naming the identity migration that authorises the change", str(caught.exception))

    def test_a_protected_axis_is_buildable_when_every_drift_is_authorised(self) -> None:
        value = variant_set(
            identity_anchor=anchor(baseline_option_id="web"),
            options=(
                option("web", anchor_digest=k.digest("face.baseline")),
                option("print", anchor_digest=k.digest("face.other"), migration_receipt_id=new_id()),
            ),
        )
        self.assertEqual(value.identity_anchor.baseline_option_id, "web")

    def test_an_unsupported_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            variant_set(contract_version="m02-contract-v0.9")

    def test_the_current_contract_version_is_accepted(self) -> None:
        self.assertEqual(variant_set(contract_version=CONTRACT_VERSION).variant_set_id, "variant.outfit")


class VariantConstraintTests(unittest.TestCase):
    def test_an_empty_target_would_forbid_everything(self) -> None:
        with self.assertRaises(GraphValidationError):
            constraint(target_options=())

    def test_targets_are_deduplicated_and_sorted(self) -> None:
        value = constraint(target_options=("master", "preview", "master"))
        self.assertEqual(value.target_options, ("master", "preview"))

    def test_a_satisfied_requirement_reports_nothing(self) -> None:
        value = constraint()
        self.assertIsNone(value.violation({"variant.outfit": "print", "variant.quality": "master"}))

    def test_an_inert_constraint_is_not_checked(self) -> None:
        value = constraint()
        self.assertIsNone(value.violation({"variant.outfit": "web", "variant.quality": "draft"}))

    def test_a_missing_required_target_is_reported_in_prose(self) -> None:
        reason = constraint().violation({"variant.outfit": "print"})
        self.assertIn("requires variant.quality to be selected", reason)

    def test_a_wrong_required_target_names_what_was_chosen(self) -> None:
        reason = constraint().violation({"variant.outfit": "print", "variant.quality": "preview"})
        self.assertIn("not preview", reason)

    def test_a_prohibited_target_is_named(self) -> None:
        reason = constraint(kind=ConstraintKind.PROHIBITS).violation(
            {"variant.outfit": "print", "variant.quality": "master"}
        )
        self.assertIn("prohibits variant.quality=master", reason)


class VariantSelectionTests(unittest.TestCase):
    def test_a_selection_pair_must_have_two_halves(self) -> None:
        with self.assertRaises(SchemaValidationError):
            selection(pairs=(("variant.outfit",),))

    def test_two_options_on_one_axis_is_refused_not_resolved(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            selection(pairs=(("variant.outfit", "web"), ("variant.outfit", "print")))
        self.assertIn("chooses one option per set", str(caught.exception))

    def test_pairs_are_canonicalised_by_set_id(self) -> None:
        value = selection(pairs=(("variant.quality", "master"), ("variant.outfit", "web")))
        self.assertEqual(value.pairs[0][0], "variant.outfit")

    def test_a_repeated_pair_is_still_two_claims_on_one_axis(self) -> None:
        with self.assertRaises(GraphValidationError):
            selection(pairs=(("variant.outfit", "web"), ("variant.outfit", "web")))

    def test_the_accessor_view_is_derived_never_stored_twice(self) -> None:
        value = selection(pairs=(("variant.outfit", "web"),))
        self.assertEqual(value.as_map(), {"variant.outfit": "web"})
        self.assertEqual(value.option_of("variant.outfit"), "web")
        self.assertIsNone(value.option_of("variant.quality"))

    def test_with_option_replaces_one_axis_and_keeps_the_rest(self) -> None:
        value = selection(pairs=(("variant.outfit", "web"), ("variant.quality", "master")))
        moved = value.with_option("variant.outfit", "print")
        self.assertEqual(moved.option_of("variant.outfit"), "print")
        self.assertEqual(moved.option_of("variant.quality"), "master")
        self.assertEqual(value.option_of("variant.outfit"), "web")

    def test_without_drops_one_axis(self) -> None:
        value = selection(pairs=(("variant.outfit", "web"), ("variant.quality", "master")))
        self.assertEqual(value.without("variant.outfit").pairs, (("variant.quality", "master"),))

    def test_the_digest_covers_the_pairs_and_nothing_else(self) -> None:
        first = selection(pairs=(("variant.outfit", "web"),), created_at_ms=10)
        second = selection(pairs=(("variant.outfit", "web"),), created_at_ms=99)
        self.assertEqual(first.digest, second.digest)
        self.assertNotEqual(first.digest, selection(pairs=(("variant.outfit", "print"),)).digest)

    def test_the_migration_receipt_set_is_deduplicated(self) -> None:
        receipt = new_id()
        self.assertEqual(selection(migration_receipt_ids=(receipt, receipt)).migration_receipt_ids, (receipt,))

    def test_a_forged_migration_receipt_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            selection(migration_receipt_ids=("receipt-1",))

    def test_the_selection_width_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            selection(pairs=tuple((f"variant.axis-{index}", "web") for index in range(129)))


class ExperimentPlanTests(unittest.TestCase):
    def test_an_experiment_must_allow_at_least_one_attempt(self) -> None:
        for budget in (0, -1, True, "8"):
            with self.assertRaises(SchemaValidationError):
                plan(max_attempts=budget)

    def test_attempts_are_numbered_from_one(self) -> None:
        value = plan(max_attempts=3)
        self.assertTrue(value.admits_attempt(1))
        self.assertTrue(value.admits_attempt(3))
        self.assertFalse(value.admits_attempt(0))
        self.assertFalse(value.admits_attempt(4))

    def test_retention_expiry_is_a_boundary_not_a_vibe(self) -> None:
        value = plan(retention_expires_at_ms=1_700_000_100_000)
        self.assertFalse(value.expired(1_700_000_100_000))
        self.assertTrue(value.expired(1_700_000_100_001))
        self.assertFalse(plan().expired(9_999_999_999_999))

    def test_an_open_experiment_carries_no_expiry_claim(self) -> None:
        self.assertIsNone(plan().retention_expires_at_ms)

    def test_provider_admissions_are_bounded(self) -> None:
        with self.assertRaises(GraphValidationError):
            plan(allowed_provider_refs=tuple(k.ref(EntityKind.TOOL, f"tool.{index}") for index in range(65)))


class RetentionPinTests(unittest.TestCase):
    def test_a_pin_must_state_why_it_exists(self) -> None:
        with self.assertRaises(GraphValidationError):
            pin(reasons=())

    def test_a_pin_target_must_be_a_reference(self) -> None:
        with self.assertRaises(SchemaValidationError):
            pin(target="snapshot-1")

    def test_reasons_are_deduplicated_and_sorted(self) -> None:
        value = pin(reasons=(PinReason.AUDIT, PinReason.GOLDEN, PinReason.AUDIT))
        self.assertEqual(value.reasons, (PinReason.AUDIT, PinReason.GOLDEN))

    def test_expiry_before_creation_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            pin(created_at_ms=200, expires_at_ms=100)

    def test_coverage_is_by_reference_not_by_display(self) -> None:
        value = pin()
        self.assertTrue(value.covers(value.target))
        self.assertFalse(value.covers(k.ref(EntityKind.SNAPSHOT, new_id())))

    def test_a_pin_without_expiry_is_live_forever(self) -> None:
        self.assertTrue(pin().is_live(4_000_000_000_000))
        self.assertFalse(pin(expires_at_ms=100).is_live(101))

    def test_an_expired_ttl_pin_may_release(self) -> None:
        value = pin(reasons=(PinReason.RETENTION_TTL,), expires_at_ms=100)
        self.assertTrue(value.may_release(101))
        self.assertFalse(value.may_release(50))

    def test_a_rights_or_audit_pin_never_releases_on_a_clock(self) -> None:
        for reason in (PinReason.RIGHTS, PinReason.AUDIT):
            self.assertFalse(pin(reasons=(reason,), expires_at_ms=100).may_release(10_000))


class BranchTests(unittest.TestCase):
    def test_an_experiment_without_a_plan_is_unbounded_spend(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            branch(profile=BranchProfile.EXPERIMENT)
        self.assertIn("is an EXPERIMENT without a plan", str(caught.exception))

    def test_a_plan_on_a_quiet_branch_is_refused_too(self) -> None:
        with self.assertRaises(GraphValidationError):
            branch(profile=BranchProfile.CANONICAL, experiment=plan())

    def test_duplicate_aliases_are_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            branch(aliases=("main", "main"))

    def test_aliases_are_canonicalised(self) -> None:
        self.assertEqual(branch(aliases=("release", "main")).aliases, ("main", "release"))

    def test_a_rename_keeps_the_branch_identity(self) -> None:
        original = branch(display_name="before")
        renamed = original.renamed("after")
        self.assertEqual(renamed.branch_id, original.branch_id)
        self.assertEqual(renamed.production_id, original.production_id)
        self.assertEqual(renamed.display_name, "after")

    def test_an_empty_display_name_becomes_absence(self) -> None:
        self.assertIsNone(branch(display_name="   ").display_name)

    def test_with_alias_is_idempotent(self) -> None:
        value = branch().with_alias("main")
        self.assertEqual(value.with_alias("main").aliases, value.aliases)
        self.assertEqual(value.aliases, ("main",))

    def test_the_identity_fields_are_uuids(self) -> None:
        with self.assertRaises(SchemaValidationError):
            branch(project_id="iris")


class BranchRefTests(unittest.TestCase):
    def test_a_branch_cannot_be_its_own_parent(self) -> None:
        identity = new_id()
        with self.assertRaises(IdentityError):
            branch_ref(branch_id=identity, parent_branch_id=identity)

    def test_a_version_zero_has_never_existed(self) -> None:
        with self.assertRaises(SchemaValidationError):
            branch_ref(version=0)

    def test_a_ref_without_a_head_is_detached(self) -> None:
        self.assertTrue(branch_ref().is_detached)
        self.assertFalse(branch_ref(head_snapshot_id=new_id()).is_detached)

    def test_a_forged_head_reference_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            branch_ref(head_snapshot_id="head-1")


class ForkReceiptTests(unittest.TestCase):
    def test_a_fork_that_rebinds_its_source_is_not_a_fork(self) -> None:
        source = new_id()
        with self.assertRaises(IdentityError):
            k.fork_receipt(source_branch_id=source, new_branch_id=source)

    def test_a_fork_must_state_why(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.fork_receipt(reason_code="Planned Fork")

    def test_the_starting_selection_is_carried_as_a_selection(self) -> None:
        chosen = selection(pairs=(("variant.outfit", "web"),))
        value = ForkReceipt(
            fork_id=new_id(),
            source_branch_id=new_id(),
            source_snapshot_id=new_id(),
            new_branch_id=new_id(),
            reason_code="planned-fork",
            initial_selection=chosen,
        )
        self.assertEqual(value.initial_selection, chosen)

    def test_a_string_in_the_selection_field_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.fork_receipt(initial_selection="variant.outfit=web")


class SelectionResolutionTests(unittest.TestCase):
    def test_declared_defaults_are_filled_in(self) -> None:
        sets = (variant_set(default_option_id="web"), variant_set("variant.quality", options=(option("master"),), default_option_id="master"))
        effective = resolve_selection(sets, selection(pairs=(("variant.outfit", "print"),)))
        self.assertEqual(effective, {"variant.outfit": "print", "variant.quality": "master"})

    def test_an_unselectable_axis_stays_absent(self) -> None:
        sets = (variant_set(allow_unselected=True),)
        self.assertEqual(resolve_selection(sets, selection()), {})

    def test_validation_reports_instead_of_raising(self) -> None:
        found = validate_selection((variant_set(),), (), selection(pairs=(("variant.outfit", "cinema"),)))
        self.assertIsInstance(found, tuple)
        self.assertTrue(found)

    def test_a_clean_selection_reports_nothing(self) -> None:
        sets = (variant_set(default_option_id="web"),)
        self.assertEqual(validate_selection(sets, (), selection()), ())

    def test_an_unknown_axis_is_addressed_by_name(self) -> None:
        found = dict(selection_rulings((variant_set(),), (), selection(pairs=(("variant.other", "web"),))))
        self.assertIn("variant:variant.other", found)
        self.assertIn("unknown variant set", found["variant:variant.other"])

    def test_a_mandatory_axis_says_so(self) -> None:
        rulings = selection_rulings((variant_set(),), (), selection())
        addresses = dict(rulings)
        self.assertIn("variant-set:variant.outfit", addresses)
        self.assertIn("is mandatory", addresses["variant-set:variant.outfit"])

    def test_a_constraint_violation_is_addressed_by_constraint_id(self) -> None:
        sets = (
            variant_set(options=(option("web"), option("print"))),
            variant_set("variant.quality", options=(option("draft"), option("master"))),
        )
        chosen = selection(pairs=(("variant.outfit", "print"), ("variant.quality", "draft")))
        found = selection_rulings(sets, (constraint(),), chosen)
        self.assertIn(
            "variant-constraint:constraint.keynote-launch",
            {address for address, _ in found},
        )

    def test_rulings_are_deduplicated_and_sorted(self) -> None:
        sets = (variant_set(),)
        chosen = selection(pairs=(("variant.outfit", "cinema"), ("variant.other", "web")))
        found = selection_rulings(sets, (), chosen)
        self.assertEqual(len(found), len(set(found)))
        self.assertEqual(found, tuple(sorted(found)))

    def test_duplicate_variant_sets_are_a_structure_error(self) -> None:
        with self.assertRaises(GraphValidationError):
            validate_selection((variant_set(), variant_set()), (), selection())

    def test_the_variant_set_count_is_bounded(self) -> None:
        sets = tuple(
            variant_set(f"variant.axis-{index}", options=(option("web"),), default_option_id="web")
            for index in range(129)
        )
        with self.assertRaises(GraphValidationError) as caught:
            validate_selection(sets, (), selection())
        self.assertIn("at most 128 variant sets", str(caught.exception))


class AnchorGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = new_id()
        self.sets = (
            variant_set(
                identity_anchor=anchor(baseline_option_id="web"),
                options=(
                    option("web", anchor_digest=k.digest("face.baseline")),
                    option(
                        "print",
                        anchor_digest=k.digest("face.other"),
                        migration_receipt_id=self.receipt,
                    ),
                ),
            ),
        )

    def test_the_baseline_option_never_needs_a_migration(self) -> None:
        chosen = selection(pairs=(("variant.outfit", "web"),))
        self.assertEqual(anchor_violations(self.sets, chosen), ())

    def test_a_drifting_option_is_refused_without_its_receipt(self) -> None:
        chosen = selection(pairs=(("variant.outfit", "print"),))
        found = anchor_violations(self.sets, chosen)
        self.assertEqual(len(found), 1)
        self.assertIn("moves protected identity anchor anchor.persona", found[0])

    def test_the_named_migration_receipt_clears_the_guard(self) -> None:
        chosen = selection(pairs=(("variant.outfit", "print"),), migration_receipt_ids=(self.receipt,))
        self.assertEqual(anchor_violations(self.sets, chosen), ())

    def test_a_ruling_carries_the_anchor_address_a_merge_needs(self) -> None:
        chosen = selection(pairs=(("variant.outfit", "print"),))
        rulings = anchor_rulings(self.sets, chosen)
        self.assertEqual(rulings[0][0], "anchor:anchor.persona")

    def test_an_unprotected_axis_is_never_reported(self) -> None:
        self.assertEqual(anchor_rulings((variant_set(),), selection(pairs=(("variant.outfit", "web"),))), ())

    def test_the_guard_is_part_of_the_ordinary_selection_check(self) -> None:
        chosen = selection(pairs=(("variant.outfit", "print"),))
        found = validate_selection(self.sets, (), chosen)
        self.assertTrue(any("protected identity anchor" in item for item in found))


class BranchLedgerRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BranchLedger()
        self.identity = branch()
        self.ledger.register(self.identity)

    def test_a_registered_branch_starts_detached(self) -> None:
        reference = self.ledger.ref(self.identity.branch_id)
        self.assertTrue(reference.is_detached)
        self.assertEqual(reference.version, 1)

    def test_re_registering_the_same_identity_is_a_retry(self) -> None:
        self.assertIs(self.ledger.register(self.identity), self.ledger.ref(self.identity.branch_id))
        self.assertEqual(len(self.ledger), 1)

    def test_re_registering_with_different_identity_data_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            self.ledger.register(replace(self.identity, display_name="quietly different"))
        self.assertIn("already exists with different identity data", str(caught.exception))

    def test_a_second_main_line_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            self.ledger.register(branch())
        self.assertIn("would be a second CANONICAL branch", str(caught.exception))

    def test_a_competing_direction_is_an_experiment_not_a_main_line(self) -> None:
        other = branch(profile=BranchProfile.EXPERIMENT, experiment=plan())
        self.ledger.register(other)
        self.assertEqual(len(self.ledger), 2)
        self.assertEqual(len(self.ledger.branches(profile=BranchProfile.CANONICAL)), 1)

    def test_an_unknown_branch_has_no_ref(self) -> None:
        with self.assertRaises(GraphValidationError):
            self.ledger.ref(new_id())
        self.assertFalse(self.ledger.has_branch(new_id()))

    def test_a_head_snapshot_makes_the_branch_attached(self) -> None:
        head = new_id()
        reference = self.ledger.register(branch(profile=BranchProfile.CAMPAIGN), head_snapshot_id=head, actor=k.component_version())
        self.assertEqual(self.ledger.head(reference.branch_id), head)
        self.assertIsNotNone(reference.last_transition_id)

    def test_a_head_without_a_known_creator_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.ledger.register(branch(profile=BranchProfile.CAMPAIGN), head_snapshot_id=new_id())

    def test_the_head_of_a_detached_branch_is_a_refusal(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            self.ledger.head(self.identity.branch_id)
        self.assertIn("is detached and has no head snapshot", str(caught.exception))

    def test_an_alias_resolves_to_an_identity_never_to_a_name(self) -> None:
        self.ledger.alias(self.identity.branch_id, "main")
        self.assertEqual(self.ledger.resolve("main"), self.identity.branch_id)
        self.assertEqual(self.ledger.aliases(self.identity.branch_id)[0].alias, "main")

    def test_a_second_branch_cannot_claim_a_lived_alias(self) -> None:
        self.ledger.alias(self.identity.branch_id, "main")
        other = branch(profile=BranchProfile.CAMPAIGN)
        with self.assertRaises(IdentityError):
            self.ledger.register(replace(other, aliases=("main",)))

    def test_a_rename_keeps_the_alias_pointing_at_the_same_branch(self) -> None:
        self.ledger.alias(self.identity.branch_id, "main")
        renamed = self.ledger.rename(self.identity.branch_id, "After")
        self.assertEqual(renamed.branch_id, self.identity.branch_id)
        self.assertEqual(self.ledger.resolve("main"), self.identity.branch_id)

    def test_a_forged_alias_is_refused_before_it_is_bound(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.ledger.alias(self.identity.branch_id, "Main Line")


class BranchLedgerForkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BranchLedger()
        self.source = branch()
        self.ledger.register(self.source, head_snapshot_id=new_id(), actor=k.component_version())
        self.head = self.ledger.head(self.source.branch_id)

    def fork(self, **over: Any):
        payload: dict[str, Any] = dict(
            new_branch_id=new_id(),
            profile=BranchProfile.EXPERIMENT,
            experiment=plan(),
            actor=k.component_version("m02.os", "1.0.0"),
        )
        payload.update(over)
        return self.ledger.fork(self.source.branch_id, self.head, **payload)

    def test_a_fork_must_name_who_created_it(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            self.fork(actor=None)
        self.assertIn("actor must be a ComponentVersion", str(caught.exception))

    def test_a_fork_records_the_exact_snapshot_it_left_from(self) -> None:
        new_branch, reference, receipt = self.fork()
        self.assertEqual(receipt.source_snapshot_id, self.head)
        self.assertEqual(reference.head_snapshot_id, self.head)
        self.assertEqual(reference.fork_point_snapshot_id, self.head)
        self.assertEqual(reference.parent_branch_id, self.source.branch_id)
        self.assertEqual(new_branch.production_id, self.source.production_id)

    def test_a_fork_never_moves_the_source(self) -> None:
        before = self.ledger.ref(self.source.branch_id)
        self.fork()
        self.assertEqual(self.ledger.ref(self.source.branch_id), before)

    def test_the_fork_may_only_be_read_back_for_a_forked_branch(self) -> None:
        _, _, receipt = self.fork()
        self.assertIs(self.ledger.fork_receipt(receipt.new_branch_id), receipt)
        with self.assertRaises(GraphValidationError) as caught:
            self.ledger.fork_receipt(self.source.branch_id)
        self.assertIn("was not created by a recorded fork", str(caught.exception))

    def test_pinning_survives_a_fork_as_an_inherited_claim(self) -> None:
        target = k.ref(EntityKind.SNAPSHOT, self.head)
        self.ledger.pin_reference(self.source.branch_id, target)
        _, reference, receipt = self.fork()
        self.assertEqual(receipt.inherited_pin_refs, (target,))
        self.assertEqual(self.ledger.pins(reference.branch_id), (target,))

    def test_a_fork_from_an_unregistered_branch_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            self.ledger.fork(new_id(), self.head, new_branch_id=new_id(), profile=BranchProfile.CAMPAIGN)

    def test_forking_onto_a_floating_current_is_impossible(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.ledger.fork(
                self.source.branch_id, None, new_branch_id=new_id(), profile=BranchProfile.CAMPAIGN
            )

    def test_parentage_is_walkable_in_both_directions(self) -> None:
        _, reference, _ = self.fork()
        self.assertEqual(self.ledger.ancestry(reference.branch_id), (reference.branch_id, self.source.branch_id))
        self.assertEqual(self.ledger.descendants(self.source.branch_id), (reference.branch_id,))


class BranchLedgerAdvanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BranchLedger()
        self.actor = k.component_version("m02.os", "1.0.0")
        self.identity = branch()
        self.start = new_id()
        self.ledger.register(self.identity, head_snapshot_id=self.start, actor=self.actor)

    def advance(self, head: str | None = None, **over: Any):
        payload: dict[str, Any] = dict(actor=self.actor)
        payload.update(over)
        return self.ledger.advance(self.identity.branch_id, head or new_id(), **payload)

    def test_moving_the_head_bumps_the_version(self) -> None:
        moved, receipt = self.advance()
        self.assertEqual(moved.version, 2)
        self.assertEqual(moved.head_snapshot_id, receipt.to_state)
        self.assertEqual(self.ledger.ref(self.identity.branch_id).version, 2)

    def test_a_no_op_move_keeps_the_version(self) -> None:
        moved, receipt = self.advance(head=self.start)
        self.assertEqual(moved.version, 1)
        self.assertEqual(moved.head_snapshot_id, self.start)
        self.assertEqual(len(self.ledger.transitions(self.identity.branch_id)), 2)
        self.assertIs(self.ledger.transition(receipt.transition_id), receipt)

    def test_a_stale_expectation_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            self.advance(expected_head_snapshot_id=new_id())
        self.assertIn("moved: expected head ", str(caught.exception))
        self.assertIn("re-read the head instead of forcing it", str(caught.exception))

    def test_a_met_expectation_advances(self) -> None:
        moved, _ = self.advance(expected_head_snapshot_id=self.start)
        self.assertEqual(moved.version, 2)

    def test_a_frozen_branch_may_not_advance(self) -> None:
        self.ledger.set_state(self.identity.branch_id, BranchState.FROZEN, actor=self.actor)
        with self.assertRaises(GraphValidationError) as caught:
            self.advance()
        self.assertIn("is FROZEN and may not advance its head", str(caught.exception))

    def test_the_causal_parent_is_the_previous_receipt(self) -> None:
        first, first_receipt = self.advance()
        _, second_receipt = self.advance()
        self.assertEqual(second_receipt.causal_parent_receipt_id, first_receipt.transition_id)
        self.assertEqual(first.version, 2)

    def test_an_identical_command_is_replayed_not_double_counted(self) -> None:
        command = "cmd-merge-1"
        digest = k.digest("payload")
        head = new_id()
        _, first = self.advance(head=head, command_id=command, command_digest=digest)
        reference, second = self.advance(head=head, command_id=command, command_digest=digest)
        self.assertIs(first, second)
        self.assertEqual(reference.version, 2)
        self.assertEqual(len(self.ledger.transitions(self.identity.branch_id)), 2)

    def test_a_command_reused_against_a_different_target_is_refused(self) -> None:
        command = "cmd-merge-1"
        digest = k.digest("payload")
        self.advance(command_id=command, command_digest=digest)
        with self.assertRaises(GraphValidationError) as caught:
            self.advance(command_id=command, command_digest=digest)
        self.assertIn("is not replayable", str(caught.exception))
        self.assertIn("different to_state", str(caught.exception))

    def test_the_same_command_cannot_carry_two_meanings(self) -> None:
        command = "cmd-merge-1"
        head = new_id()
        self.advance(head=head, command_id=command, command_digest=k.digest("first"))
        with self.assertRaises(GraphValidationError) as caught:
            self.advance(head=head, command_id=command, command_digest=k.digest("second"))
        self.assertIn("different semantic digest", str(caught.exception))

    def test_an_advance_needs_a_known_creator(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.ledger.advance(self.identity.branch_id, new_id(), actor="m02.os")

    def test_evidence_and_policy_travel_with_the_receipt(self) -> None:
        evidence = k.ref(EntityKind.RECEIPT, new_id())
        policy = k.ref(EntityKind.POLICY, "policy.advance")
        _, receipt = self.advance(evidence_refs=(evidence,), policy_ref=policy)
        stored = self.ledger.transition(receipt.transition_id)
        self.assertEqual(stored.evidence_refs, (evidence,))
        self.assertEqual(stored.policy_ref, policy)

    def test_an_unknown_transition_receipt_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            self.ledger.transition(new_id())


class BranchLedgerStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BranchLedger()
        self.actor = k.component_version("m02.os", "1.0.0")
        self.identity = branch()
        self.ledger.register(self.identity, head_snapshot_id=new_id(), actor=self.actor)

    def test_setting_the_state_twice_writes_one_receipt(self) -> None:
        first = self.ledger.set_state(self.identity.branch_id, BranchState.FROZEN, actor=self.actor)
        second = self.ledger.set_state(self.identity.branch_id, BranchState.FROZEN, actor=self.actor)
        self.assertIs(first, second)
        self.assertEqual(first.version, 2)

    def test_a_state_change_is_distinguishable_from_a_head_move(self) -> None:
        moved = self.ledger.set_state(self.identity.branch_id, BranchState.ABANDONED, actor=self.actor)
        receipts = self.ledger.transitions(self.identity.branch_id)
        self.assertEqual(receipts[-1].reason_code, "branch-state")
        self.assertEqual(receipts[-1].from_state, "ACTIVE")
        self.assertEqual(moved.state, BranchState.ABANDONED)

    def test_history_is_ordered_by_causality_not_by_id(self) -> None:
        self.ledger.advance(self.identity.branch_id, new_id(), actor=self.actor)
        self.ledger.advance(self.identity.branch_id, new_id(), actor=self.actor)
        receipts = self.ledger.transitions(self.identity.branch_id)
        self.assertEqual(len(receipts), 3)
        for earlier, later in zip(receipts, receipts[1:]):
            self.assertEqual(later.causal_parent_receipt_id, earlier.transition_id)

    def test_a_tampered_receipt_chain_is_refused(self) -> None:
        self.ledger.advance(self.identity.branch_id, new_id(), actor=self.actor)
        first, second = self.ledger.transitions(self.identity.branch_id)
        self.ledger._receipts[first.transition_id] = replace(
            first, causal_parent_receipt_id=second.transition_id
        )
        with self.assertRaises(IdentityError) as caught:
            self.ledger.transitions(self.identity.branch_id)
        self.assertIn("receipt chain cycles at", str(caught.exception))

    def test_a_cycle_in_parentage_is_refused(self) -> None:
        other = branch(profile=BranchProfile.CAMPAIGN)
        self.ledger.register(other)
        self.ledger._refs[self.identity.branch_id] = replace(
            self.ledger.ref(self.identity.branch_id), parent_branch_id=other.branch_id
        )
        self.ledger._refs[other.branch_id] = replace(
            self.ledger.ref(other.branch_id), parent_branch_id=self.identity.branch_id
        )
        with self.assertRaises(IdentityError) as caught:
            self.ledger.ancestry(self.identity.branch_id)
        self.assertIn("branch parentage cycles at", str(caught.exception))


class BranchLedgerPinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BranchLedger()
        self.identity = branch()
        self.ledger.register(self.identity)
        self.target = k.ref(EntityKind.SNAPSHOT, new_id())

    def test_a_pin_is_idempotent(self) -> None:
        once = self.ledger.pin_reference(self.identity.branch_id, self.target)
        twice = self.ledger.pin_reference(self.identity.branch_id, self.target)
        self.assertIs(once, twice)
        self.assertEqual(self.ledger.pins(self.identity.branch_id), (self.target,))

    def test_a_pin_record_shares_the_ref_target(self) -> None:
        moved = self.ledger.pin(self.identity.branch_id, pin(target=self.target))
        self.assertEqual(moved.pin_refs, (self.target,))

    def test_unpinning_something_never_pinned_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            self.ledger.unpin(self.identity.branch_id, self.target)
        self.assertIn("never pinned", str(caught.exception))

    def test_unpinning_a_real_pin_keeps_the_others(self) -> None:
        other = k.ref(EntityKind.SNAPSHOT, new_id())
        self.ledger.pin_reference(self.identity.branch_id, self.target)
        self.ledger.pin_reference(self.identity.branch_id, other)
        moved = self.ledger.unpin(self.identity.branch_id, self.target)
        self.assertEqual(moved.pin_refs, (other,))


class BranchLedgerReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BranchLedger()
        self.actor = k.component_version("m02.os", "1.0.0")
        self.identity = branch()
        self.start = new_id()
        self.ledger.register(self.identity, head_snapshot_id=self.start, actor=self.actor)

    def test_a_quiet_branch_replays_to_its_stored_ref(self) -> None:
        self.assertEqual(self.ledger.replay(self.identity.branch_id), self.ledger.ref(self.identity.branch_id))

    def test_a_moved_head_replays_with_bumps_in_order(self) -> None:
        self.ledger.advance(self.identity.branch_id, new_id(), actor=self.actor)
        self.ledger.advance(self.identity.branch_id, new_id(), actor=self.actor)
        self.assertEqual(self.ledger.replay(self.identity.branch_id), self.ledger.ref(self.identity.branch_id))

    def test_a_state_change_replays_as_state_not_as_history(self) -> None:
        self.ledger.set_state(self.identity.branch_id, BranchState.FROZEN, actor=self.actor)
        replayed = self.ledger.replay(self.identity.branch_id)
        self.assertEqual(replayed.state, BranchState.FROZEN)
        self.assertEqual(replayed.head_snapshot_id, self.start)

    def test_a_ref_that_disagrees_with_its_own_receipts_is_refused(self) -> None:
        self.ledger._refs[self.identity.branch_id] = replace(self.ledger.ref(self.identity.branch_id), version=9)
        with self.assertRaises(GraphValidationError) as caught:
            self.ledger.replay(self.identity.branch_id)
        self.assertIn("does not replay from its receipts", str(caught.exception))

    def test_a_detached_branch_replays_to_detached(self) -> None:
        quiet = branch(profile=BranchProfile.CAMPAIGN)
        self.ledger.register(quiet)
        self.assertTrue(self.ledger.replay(quiet.branch_id).is_detached)


class LedgerIsolationTests(unittest.TestCase):
    def test_the_module_exposes_no_global_ledger(self) -> None:
        import iris_project_os.branching as module

        self.assertFalse(any(isinstance(value, BranchLedger) for value in vars(module).values()))

    def test_two_ledgers_do_not_share_branches(self) -> None:
        left, right = BranchLedger(), BranchLedger()
        value = branch()
        left.register(value)
        self.assertTrue(left.has_branch(value.branch_id))
        self.assertFalse(right.has_branch(value.branch_id))
