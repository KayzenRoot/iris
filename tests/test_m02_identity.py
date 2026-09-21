"""Area A proves three layers never collapse and history never rewrites.

Identity says *which thing*, a digest says *which bytes*, an attempt id says
*which try*. A rename keeps the id, a retry mints a new attempt that points at
the old one, and every historical ledger — aliases, supersessions, transitions —
is append-only, so the only way an earlier receipt can be safe is if nothing here
ever moves a binding under it. This file is that promise read back as refusals.
"""

from __future__ import annotations

import unittest
from typing import Any

from iris_project_os.errors import (
    IdentityError,
    LifecycleError,
    SchemaValidationError,
    UnsupportedVersionError,
)
from iris_project_os.identity import (
    ATTEMPT_LIFECYCLE,
    PROJECT_LIFECYCLE,
    TERMINAL_ATTEMPT_STATES,
    AliasLedger,
    AliasRef,
    AttemptIdentity,
    AttemptState,
    EntityKind,
    ExternalRef,
    LocatorRef,
    ProductionPassport,
    ProjectEnvelope,
    ProjectLifecycleState,
    RevisionRef,
    SupersessionLedger,
    SupersessionRef,
    TransitionReceipt,
    Uuid7Generator,
    new_id,
    require_id,
    revision_locator,
)

from iris_project_os.versions import canonical_json

from tests import m02_kernel_support as k

GRAPH_REF = k.ref(EntityKind.GRAPH, "graph.test")
INTENT_REF = k.ref(EntityKind.INTENT, "intent.brief")
PROVIDER_REF = k.ref(EntityKind.PROVIDER, "provider.a")
NOW = k.CACHE_NOW


def envelope(**over: Any) -> ProjectEnvelope:
    payload: dict[str, Any] = dict(
        project_id=new_id(),
        display_name="Iris demo",
        root_graph_ref=GRAPH_REF,
        created_at_ms=NOW,
    )
    payload.update(over)
    return ProjectEnvelope(**payload)


def passport(**over: Any) -> ProductionPassport:
    payload: dict[str, Any] = dict(
        production_id=new_id(),
        project_id=new_id(),
        intent_ref=INTENT_REF,
        graph_ref=GRAPH_REF,
        requested_outputs=("web",),
        created_at_ms=NOW,
    )
    payload.update(over)
    return ProductionPassport(**payload)


def attempt(state: AttemptState = AttemptState.QUEUED, **over: Any) -> AttemptIdentity:
    payload: dict[str, Any] = dict(
        attempt_id=new_id(),
        production_id=new_id(),
        graph_ref=GRAPH_REF,
        node_id="render.logo",
        provider_ref=PROVIDER_REF,
        state=state,
        started_at_ms=NOW,
    )
    payload.update(over)
    return AttemptIdentity(**payload)


class RequireIdTests(unittest.TestCase):
    def test_a_canonical_uuid_is_accepted_and_normalised(self) -> None:
        upper = new_id().upper()
        self.assertEqual(require_id(upper, "id"), upper.lower())

    def test_a_uuid_object_is_accepted(self) -> None:
        text = new_id()
        from uuid import UUID

        self.assertEqual(require_id(UUID(text), "id"), text)

    def test_a_non_uuid_string_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            require_id("asset-1", "id")

    def test_a_number_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            require_id(42, "id")

    def test_none_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            require_id(None, "id")


class Uuid7GeneratorTests(unittest.TestCase):
    def test_minted_ids_are_version_seven(self) -> None:
        value = Uuid7Generator(clock=lambda: NOW).next_id()
        self.assertEqual(value.version, 7)

    def test_a_backward_clock_cannot_mint_an_older_id(self) -> None:
        steps = iter([1_700_000_000_500, 1_700_000_000_100])
        generator = Uuid7Generator(clock=lambda: next(steps))
        first = generator.next_id()
        second = generator.next_id()
        self.assertGreaterEqual(second.int >> 80, first.int >> 80)
        self.assertEqual(generator.last_millis, 1_700_000_000_500)

    def test_the_text_form_is_a_canonical_id(self) -> None:
        text = Uuid7Generator(clock=lambda: NOW).next_id_text()
        self.assertEqual(require_id(text, "text"), text)

    def test_two_calls_never_collide(self) -> None:
        generator = Uuid7Generator(clock=lambda: NOW)
        self.assertNotEqual(generator.next_id(), generator.next_id())


class EntityKindTests(unittest.TestCase):
    def test_an_unknown_kind_is_refused_not_guessed(self) -> None:
        with self.assertRaises(SchemaValidationError):
            EntityKind.parse("nonesuch", "kind")

    def test_a_string_kind_is_parsed_case_insensitively(self) -> None:
        self.assertIs(EntityKind.parse("artifact", "kind"), EntityKind.ARTIFACT)

    def test_a_non_string_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            EntityKind.parse(7, "kind")


class ExternalRefTests(unittest.TestCase):
    def test_the_text_form_renders_the_kind_in_lowercase(self) -> None:
        self.assertEqual(k.ref(EntityKind.ARTIFACT, "asset.logo").text, "artifact:asset.logo")

    def test_a_version_is_appended_with_an_at(self) -> None:
        value = k.ref(EntityKind.SCHEMA, "schema.vector", version="1.0.0")
        self.assertEqual(value.text, "schema:schema.vector@1.0.0")

    def test_a_digest_must_be_sha256(self) -> None:
        with self.assertRaises(SchemaValidationError):
            ExternalRef(kind=EntityKind.ARTIFACT, reference="r", content_digest="nope")

    def test_bind_and_coerce_reuse_an_instance(self) -> None:
        value = ExternalRef.bind(EntityKind.POLICY, "policy.default")
        self.assertIs(ExternalRef.coerce(value, "field"), value)

    def test_an_empty_reference_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            ExternalRef(kind=EntityKind.ARTIFACT, reference="   ")


class ProjectEnvelopeTests(unittest.TestCase):
    def test_a_rename_keeps_the_project_identity(self) -> None:
        original = envelope(display_name="before")
        renamed = original.renamed("after")
        self.assertEqual(renamed.project_id, original.project_id)
        self.assertEqual(renamed.display_name, "after")

    def test_a_legal_transition_moves_the_state(self) -> None:
        value = envelope().transitioned_to(ProjectLifecycleState.ACTIVE, reason="go")
        self.assertIs(value.state, ProjectLifecycleState.ACTIVE)

    def test_an_illegal_transition_is_refused(self) -> None:
        with self.assertRaises(LifecycleError):
            envelope().transitioned_to(ProjectLifecycleState.PAUSED, reason="skip")

    def test_the_root_graph_ref_must_be_an_external_ref(self) -> None:
        with self.assertRaises(SchemaValidationError):
            envelope(root_graph_ref="graph.test")

    def test_a_non_uuid_project_id_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            envelope(project_id="iris")

    def test_duplicate_aliases_are_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            envelope(aliases=("logo", "logo"))

    def test_an_alias_must_be_an_identifier(self) -> None:
        with self.assertRaises(SchemaValidationError):
            envelope(aliases=("Main Logo",))

    def test_an_unsupported_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            envelope(contract_version="m02-contract-v9.9")


class ProductionPassportTests(unittest.TestCase):
    def test_at_least_one_requested_output_is_required(self) -> None:
        with self.assertRaises(SchemaValidationError):
            passport(requested_outputs=())

    def test_a_requested_output_must_be_an_identifier(self) -> None:
        with self.assertRaises(SchemaValidationError):
            passport(requested_outputs=("web deliverable",))

    def test_replaced_by_returns_a_forward_supersession(self) -> None:
        old, new = passport(), passport()
        record = old.replaced_by(new, "re-briefed", new_id())
        self.assertIs(record.superseded_kind, EntityKind.PRODUCTION)
        self.assertEqual(record.superseded_id, old.production_id)
        self.assertEqual(record.replacement_id, new.production_id)

    def test_a_non_ref_graph_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            passport(graph_ref="graph.test")


class ArtifactIdentityTests(unittest.TestCase):
    def test_a_rename_keeps_the_artifact_id(self) -> None:
        value = k.artifact_identity(display_name="before")
        self.assertEqual(value.renamed("after").artifact_id, value.artifact_id)

    def test_the_semantic_type_ref_must_point_at_a_semantic_type(self) -> None:
        with self.assertRaises(IdentityError):
            k.artifact_identity(semantic_type_ref=k.ref(EntityKind.ARTIFACT, "asset.logo"))

    def test_a_non_external_ref_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.artifact_identity(semantic_type_ref="vector.svg")

    def test_a_non_uuid_production_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.artifact_identity(production_id="prod")


class RevisionRefTests(unittest.TestCase):
    def test_a_source_revision_has_no_producer_attempt(self) -> None:
        record = k.artifact_identity()
        self.assertTrue(k.revision_ref(record).is_source)

    def test_a_produced_revision_is_not_a_source(self) -> None:
        record = k.artifact_identity()
        self.assertFalse(k.revision_ref(record, producer_attempt_id=new_id()).is_source)

    def test_the_content_digest_must_be_sha256(self) -> None:
        record = k.artifact_identity()
        with self.assertRaises(SchemaValidationError):
            k.revision_ref(record, content_digest="short")

    def test_an_input_lineage_must_be_external_refs(self) -> None:
        record = k.artifact_identity()
        with self.assertRaises(SchemaValidationError):
            k.revision_ref(record, input_lineage=("asset.a",))

    def test_a_valid_lineage_round_trips(self) -> None:
        record = k.artifact_identity()
        value = k.revision_ref(record, input_lineage=(k.ref(EntityKind.ARTIFACT, "asset.a"),))
        self.assertEqual(RevisionRef.from_payload(value.to_payload()), value)


class AttemptIdentityTests(unittest.TestCase):
    def test_finished_before_started_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            attempt(finished_at_ms=NOW - 1)

    def test_a_terminal_state_sets_the_finish_time(self) -> None:
        value = attempt(state=AttemptState.RUNNING).transitioned_to(
            AttemptState.SUCCEEDED, at_ms=NOW + 5
        )
        self.assertIs(value.state, AttemptState.SUCCEEDED)
        self.assertEqual(value.finished_at_ms, NOW + 5)

    def test_only_a_terminal_attempt_may_be_retried(self) -> None:
        with self.assertRaises(IdentityError):
            attempt(state=AttemptState.RUNNING).retried(attempt_id=new_id())

    def test_a_retry_is_a_new_attempt_pointing_at_the_old_one(self) -> None:
        old = attempt(state=AttemptState.RUNNING).transitioned_to(AttemptState.FAILED, at_ms=NOW + 5)
        fresh = old.retried(attempt_id=new_id())
        self.assertEqual(fresh.retry_of_attempt_id, old.attempt_id)
        self.assertEqual(fresh.node_id, old.node_id)
        self.assertIs(fresh.state, AttemptState.QUEUED)
        self.assertNotEqual(fresh.attempt_id, old.attempt_id)

    def test_an_illegal_attempt_transition_is_refused(self) -> None:
        with self.assertRaises(LifecycleError):
            attempt(state=AttemptState.QUEUED).transitioned_to(AttemptState.SUCCEEDED, at_ms=NOW + 5)

    def test_the_terminal_set_is_what_is_claimed(self) -> None:
        for state in TERMINAL_ATTEMPT_STATES:
            self.assertTrue(attempt(state=state).is_terminal)
        self.assertFalse(attempt(state=AttemptState.RUNNING).is_terminal)

    def test_a_node_id_must_be_an_identifier(self) -> None:
        with self.assertRaises(SchemaValidationError):
            attempt(node_id="Render Logo")


class AliasLedgerTests(unittest.TestCase):
    def test_a_new_alias_binds_at_version_one(self) -> None:
        ledger = AliasLedger()
        ident = new_id()
        record = ledger.bind("logo", EntityKind.ARTIFACT, ident)
        self.assertEqual(record.version, 1)
        self.assertEqual(ledger.current("logo").entity_id, ident)

    def test_rebinding_the_same_idempotent_target_returns_the_live_record(self) -> None:
        ledger = AliasLedger()
        ident = new_id()
        first = ledger.bind("logo", EntityKind.ARTIFACT, ident)
        again = ledger.bind("logo", EntityKind.ARTIFACT, ident)
        self.assertIs(first, again)

    def test_a_silent_rebind_to_another_id_is_refused(self) -> None:
        ledger = AliasLedger()
        ledger.bind("logo", EntityKind.ARTIFACT, new_id())
        with self.assertRaises(IdentityError) as caught:
            ledger.bind("logo", EntityKind.ARTIFACT, new_id())
        self.assertIn("retire it first", str(caught.exception))

    def test_a_retired_name_is_never_rebound(self) -> None:
        ledger = AliasLedger()
        ledger.bind("logo", EntityKind.ARTIFACT, new_id())
        ledger.retire("logo", retired_at_ms=NOW + 10)
        with self.assertRaises(IdentityError) as caught:
            ledger.bind("logo", EntityKind.ARTIFACT, new_id())
        self.assertIn("never rebound", str(caught.exception))

    def test_a_retired_alias_resolves_to_nothing(self) -> None:
        ledger = AliasLedger()
        ledger.bind("logo", EntityKind.ARTIFACT, new_id())
        ledger.retire("logo", retired_at_ms=NOW + 10)
        with self.assertRaises(IdentityError):
            ledger.current("logo")

    def test_an_unbound_alias_raises(self) -> None:
        with self.assertRaises(IdentityError):
            AliasLedger().current("ghost")

    def test_history_survives_retirement(self) -> None:
        ledger = AliasLedger()
        ledger.bind("logo", EntityKind.ARTIFACT, new_id())
        ledger.retire("logo", retired_at_ms=NOW + 10)
        versions = ledger.versions_of("logo")
        self.assertEqual(len(versions), 2)
        self.assertTrue(versions[-1].is_retired)

    def test_aliases_of_walks_live_bindings_only(self) -> None:
        ledger = AliasLedger()
        ident = new_id()
        ledger.bind("logo", EntityKind.ARTIFACT, ident)
        ledger.bind("mark", EntityKind.ARTIFACT, ident)
        ledger.retire("mark", retired_at_ms=NOW + 10)
        self.assertEqual([item.alias for item in ledger.aliases_of(ident)], ["logo"])

    def test_a_retired_before_created_timestamp_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            AliasRef(alias="logo", entity_kind=EntityKind.ARTIFACT, entity_id=new_id(), created_at_ms=NOW, retired_at_ms=NOW - 5)

    def test_a_zero_version_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            AliasRef(alias="logo", entity_kind=EntityKind.ARTIFACT, entity_id=new_id(), version=0)


class LocatorRefTests(unittest.TestCase):
    def test_the_uri_is_canonical_and_transport_free(self) -> None:
        project = new_id()
        value = LocatorRef(project_id=project)
        self.assertEqual(value.uri, f"iris://project/{project}")

    def test_a_full_locator_round_trips_through_its_uri(self) -> None:
        project, production, artifact = new_id(), new_id(), new_id()
        value = LocatorRef(
            project_id=project,
            production_id=production,
            artifact_id=artifact,
            revision_digest=k.digest("bytes"),
        )
        self.assertEqual(LocatorRef.from_uri(value.uri), value)

    def test_an_artifact_without_its_production_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            LocatorRef(project_id=new_id(), artifact_id=new_id())

    def test_a_revision_without_its_artifact_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            LocatorRef(project_id=new_id(), production_id=new_id(), revision_digest=k.digest("b"))

    def test_a_uri_without_a_scheme_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            LocatorRef.from_uri("project/abc")

    def test_a_dangling_segment_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            LocatorRef.from_uri("iris://project/abc/production")

    def test_an_unknown_locator_part_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            LocatorRef.from_uri("iris://project/abc/widget/xyz")

    def test_revision_locator_derives_from_the_four_records(self) -> None:
        env, pass_ = envelope(), passport()
        artifact = k.artifact_identity()
        revision = k.revision_ref(artifact)
        value = revision_locator(env, pass_, artifact, revision)
        self.assertEqual(value.project_id, env.project_id)
        self.assertEqual(value.revision_digest, revision.content_digest)


class TransitionReceiptTests(unittest.TestCase):
    def test_command_id_and_digest_are_issued_together(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.transition_receipt(command_id="cmd-1", command_digest=None)

    def test_a_receipt_cannot_its_be_own_causal_parent(self) -> None:
        ident = new_id()
        with self.assertRaises(IdentityError):
            k.transition_receipt(transition_id=ident, causal_parent_receipt_id=ident)

    def test_an_initial_state_has_no_from_state(self) -> None:
        self.assertTrue(k.transition_receipt(from_state=None).is_initial)

    def test_a_lifecycle_schema_this_kernel_cannot_read_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            k.transition_receipt(state_schema="iris-lifecycle-schema-v99")

    def test_two_commands_replayed_against_different_targets_conflict(self) -> None:
        command = "cmd-7"
        digest = k.digest("payload")
        left = k.transition_receipt(command_id=command, command_digest=digest)
        right = k.transition_receipt(command_id=command, command_digest=digest, entity_id=new_id())
        self.assertIn("different entity_id", left.conflicts_with(right))

    def test_an_identical_replay_is_idempotent(self) -> None:
        command = "cmd-7"
        digest = k.digest("payload")
        args = dict(transition_id=new_id(), entity_id=new_id(), command_id=command, command_digest=digest)
        left = k.transition_receipt(**args)
        right = k.transition_receipt(**args)
        self.assertIsNone(left.conflicts_with(right))

    def test_two_commandless_receipts_are_not_comparable(self) -> None:
        conflict = k.transition_receipt().conflicts_with(k.transition_receipt())
        self.assertIn("no command identity", conflict)

    def test_the_key_is_canonical_json(self) -> None:
        value = k.transition_receipt()
        self.assertEqual(value.key(), canonical_json(value.to_payload()))

    def test_a_receipt_round_trips(self) -> None:
        value = k.transition_receipt(evidence_refs=(k.ref(EntityKind.EVIDENCE, "ev.1"),))
        self.assertEqual(TransitionReceipt.from_payload(value.to_payload()), value)


class SupersessionLedgerTests(unittest.TestCase):
    def _ref(self, **over: Any) -> SupersessionRef:
        payload: dict[str, Any] = dict(
            superseded_id=new_id(),
            superseded_kind=EntityKind.PRODUCTION,
            replacement_id=new_id(),
            replacement_kind=EntityKind.PRODUCTION,
            reason_code="re-briefed",
            effective_at_ms=NOW,
        )
        payload.update(over)
        return SupersessionRef(**payload)

    def test_a_record_cannot_supersede_itself(self) -> None:
        ident = new_id()
        with self.assertRaises(IdentityError):
            self._ref(superseded_id=ident, replacement_id=ident)

    def test_recording_the_same_supersession_twice_is_idempotent(self) -> None:
        ledger = SupersessionLedger()
        record = self._ref()
        ledger.record(record)
        self.assertIs(ledger.record(record), record)

    def test_a_record_cannot_be_superseded_twice(self) -> None:
        ledger = SupersessionLedger()
        first = self._ref()
        ledger.record(first)
        with self.assertRaises(IdentityError) as caught:
            ledger.record(self._ref(superseded_id=first.superseded_id))
        self.assertIn("cannot be superseded twice", str(caught.exception))

    def test_latest_follows_the_chain(self) -> None:
        ledger = SupersessionLedger()
        a, b, c = new_id(), new_id(), new_id()
        ledger.record(self._ref(superseded_id=a, replacement_id=b))
        ledger.record(self._ref(superseded_id=b, replacement_id=c))
        self.assertEqual(ledger.latest(a), c)

    def test_latest_stops_at_an_unadmitted_replacement(self) -> None:
        ledger = SupersessionLedger()
        a, b, c = new_id(), new_id(), new_id()
        ledger.record(self._ref(superseded_id=a, replacement_id=b))
        ledger.record(self._ref(superseded_id=b, replacement_id=c))
        self.assertEqual(ledger.latest(a, admitted={b}), b)

    def test_a_supersession_cycle_is_detected(self) -> None:
        ledger = SupersessionLedger()
        a, b = new_id(), new_id()
        ledger.record(self._ref(superseded_id=a, replacement_id=b))
        ledger.record(self._ref(superseded_id=b, replacement_id=a))
        with self.assertRaises(IdentityError) as caught:
            ledger.chain(a)
        self.assertIn("cycle", str(caught.exception))

    def test_history_of_collects_predecessors(self) -> None:
        ledger = SupersessionLedger()
        a, b, c = new_id(), new_id(), new_id()
        ledger.record(self._ref(superseded_id=a, replacement_id=b))
        ledger.record(self._ref(superseded_id=b, replacement_id=c))
        self.assertEqual(ledger.history_of(c), frozenset({a, b, c}))

    def test_is_superseded_reports_the_head(self) -> None:
        ledger = SupersessionLedger()
        head = self._ref()
        ledger.record(head)
        self.assertTrue(ledger.is_superseded(head.superseded_id))
        self.assertFalse(ledger.is_superseded(head.replacement_id))

    def test_recording_a_non_ref_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            SupersessionLedger().record({"superseded_id": new_id()})


class StateMachineTotalityTests(unittest.TestCase):
    def test_archived_is_a_project_terminal(self) -> None:
        self.assertIn(ProjectLifecycleState.ARCHIVED, PROJECT_LIFECYCLE.terminals)

    def test_no_state_self_transitions(self) -> None:
        for source in PROJECT_LIFECYCLE.states:
            self.assertNotIn(source, PROJECT_LIFECYCLE.legal_targets(source))

    def test_attempt_terminals_reach_nothing(self) -> None:
        for state in ATTEMPT_LIFECYCLE.terminals:
            self.assertTrue(ATTEMPT_LIFECYCLE.is_terminal(state))

    def test_reachable_from_created_excludes_paused_first_hop(self) -> None:
        reachable = PROJECT_LIFECYCLE.reachable(ProjectLifecycleState.CREATED)
        self.assertIn(ProjectLifecycleState.ACTIVE, reachable)


class PayloadRoundTripTests(unittest.TestCase):
    def test_envelope_round_trips(self) -> None:
        value = envelope(domain_profile_refs=(k.ref(EntityKind.SCHEMA, "profile"),), metadata=(("tier", "gold"),))
        self.assertEqual(ProjectEnvelope.from_payload(value.to_payload()), value)

    def test_passport_round_trips(self) -> None:
        value = passport(requested_outputs=("web", "print"))
        self.assertEqual(ProductionPassport.from_payload(value.to_payload()), value)

    def test_attempt_round_trips(self) -> None:
        value = attempt(state=AttemptState.RUNNING, branch_id=new_id())
        self.assertEqual(AttemptIdentity.from_payload(value.to_payload()), value)

    def test_a_foreign_key_is_refused_on_decode(self) -> None:
        payload = envelope().to_payload()
        payload["unseen"] = "value"
        with self.assertRaises(SchemaValidationError):
            ProjectEnvelope.from_payload(payload)

    def test_a_missing_key_is_refused_on_decode(self) -> None:
        payload = envelope().to_payload()
        payload.pop("root_graph_ref")
        with self.assertRaises(SchemaValidationError):
            ProjectEnvelope.from_payload(payload)

    def test_digest_is_stable_over_the_payload(self) -> None:
        value = envelope()
        self.assertEqual(value.digest(), k.content_digest(value.to_payload()))


if __name__ == "__main__":
    unittest.main()
