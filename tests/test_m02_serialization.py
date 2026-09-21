"""The transport layer: versioned, tamper-evident, and derived from the kernel rather than listed.

§12 of the module spec asks for deterministic, schema-versioned serialisation, and two failures sit on
either side of it. One is a byte string that means different things to two readers, which the envelope
and its digest answer. The other is a type map that quietly forgets the next record someone adds, which
is answered by deriving the map from the kernel itself: an omission becomes impossible, and two records
that would claim one wire name stop the package from importing at all — the only moment at which that
can still be fixed cheaply.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from types import MappingProxyType, SimpleNamespace
from typing import Any

from iris_project_os.analysis import CausalFingerprint, FingerprintComponent, ImpactCone
from iris_project_os.archive import ArchiveObject
from iris_project_os.base import Record
from iris_project_os.branching import IdentityAnchorPolicy, RetentionPin
from iris_project_os.build import JournalEvent, JournalKind, RepairTarget
from iris_project_os.diffing import DiffCategory, DiffEntry, DiffOperation
from iris_project_os.errors import SchemaValidationError, UnsupportedVersionError
from iris_project_os.identity import AliasRef, ArtifactIdentity, EntityKind, LocatorRef
from iris_project_os.lifecycle import ProductionStateVector
from iris_project_os.merge import ConflictKind, MergeConflict
from iris_project_os.ports import (
    DependencyObservation,
    PortBoundary,
    ProviderDescriptor,
    ProviderHandle,
)
from iris_project_os.promotion import GateKind, PromotionGate
from iris_project_os.release import ReleasePhase, ReleaseProof
from iris_project_os.serialization import (
    ENVELOPE_KEYS,
    SERIALIZABLE_TYPES,
    dumps,
    envelope,
    from_envelope,
    loads,
    transport_name,
    type_name,
    validate_payload,
)
from iris_project_os.versions import SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS, content_digest

from tests import m01_kernel_support as q
from tests import m02_kernel_support as k

NOW = k.CACHE_NOW
GRAPH = k.bound(records=k.chain_records())
FINGERPRINT_PART = FingerprintComponent(kind="definition", reference=k.digest("graph bytes"))


def sample(name: str) -> Any:
    """One representative value for each transport name the battery below covers."""

    if name not in BUILDERS:
        raise AssertionError(f"no sample builder registered for {name!r}")
    return BUILDERS[name]()


BUILDERS: dict[str, Any] = {
    # identity
    "external_ref": lambda: k.ref(EntityKind.ARTIFACT, "asset.logo"),
    "artifact_identity": lambda: k.artifact_identity(),
    "revision_ref": lambda: k.revision_ref(k.artifact_identity()),
    "alias_ref": lambda: AliasRef(alias="logo", entity_kind=EntityKind.ARTIFACT, entity_id=k.new_id()),
    "locator_ref": lambda: LocatorRef(project_id=k.new_id()),
    "transition_receipt": lambda: k.transition_receipt(),
    # graph
    "semantic_type_ref": lambda: k.semantic_type("vector.svg"),
    "semantic_port": lambda: k.output("out"),
    "graph_node": lambda: k.source(),
    "graph_edge": lambda: k.edge("edge.render", "source.logo", "render.logo"),
    "graph_definition": lambda: k.chain_definition(),
    "graph_revision": lambda: k.chain_revision(),
    "graph_delta": lambda: k.delta([k.mutation()]),
    "materialization_record": lambda: k.materialization("render.logo"),
    "materialization_graph": lambda: GRAPH,
    "dependency_slice": lambda: k.DependencySlice(axis="region", values=("left",)),
    "side_effect_policy": lambda: k.SideEffectPolicy(
        idempotency_key_ref=k.ref(EntityKind.POLICY, "policy.idempotency")
    ),
    # analysis
    "fingerprint_context": lambda: k.context(),
    "change": lambda: k.change("render.logo"),
    "impact_cone": lambda: ImpactCone(roots=("render.logo",), facets=(k.DependencyFacet.CONTENT,)),
    "causal_fingerprint": lambda: CausalFingerprint(
        node_id="render.logo", graph_digest=k.digest("graph bytes"), components=(FINGERPRINT_PART,)
    ),
    "fingerprint_component": lambda: FINGERPRINT_PART,
    # snapshots
    "snapshot_closure_manifest": lambda: k.closure(production_id="prod.test", graph=GRAPH),
    "snapshot": lambda: k.snapshot(
        production_id="prod.test", closure_value=k.closure(production_id="prod.test", graph=GRAPH)
    ),
    # branching
    "fork_receipt": lambda: k.fork_receipt(),
    "retention_pin": lambda: RetentionPin(pin_id=k.new_id(), target=k.ref(EntityKind.SNAPSHOT, k.new_id())),
    "identity_anchor_policy": lambda: IdentityAnchorPolicy(
        anchor_id="anchor.persona",
        policy_ref=k.ref(EntityKind.POLICY, "policy.identity"),
        baseline_digest=k.digest("baseline"),
    ),
    # diffing and merge
    "diff_entry": lambda: DiffEntry(
        category=DiffCategory.GRAPH_TOPOLOGY, operation=DiffOperation.ADDED, subject="render.logo"
    ),
    "merge_conflict": lambda: MergeConflict(
        conflict_id=k.new_id(), kind=ConflictKind.NODE_DEFINITION_CONFLICT, subject="render.logo"
    ),
    # build
    "journal_event": lambda: JournalEvent(
        event_id=k.new_id(),
        attempt_id=k.new_id(),
        kind=JournalKind.NODE_STARTED,
        sequence=1,
        node_id="render.logo",
    ),
    "repair_target": lambda: RepairTarget(
        node_id="render.logo",
        slice=k.DependencySlice(axis="region", values=("left",)),
        facets=(k.DependencyFacet.CONTENT,),
        reasons=("input digest moved",),
    ),
    # reuse
    "context_source": lambda: k.ContextSource(ref=k.ref(EntityKind.HIVE_CONTEXT, "brief.front"), ordinal=0),
    "context_fingerprint": lambda: k.cache_context(),
    "cache_entry": lambda: k.cache_entry(GRAPH, "render.logo"),
    "cache_key": lambda: k.cache_entry(GRAPH, "render.logo").key,
    "cache_trust": lambda: k.cache_trust(),
    "qualification": lambda: k.cache_qualification(),
    "reuse_request": lambda: k.reuse_request(GRAPH, "render.logo"),
    "reuse_receipt": lambda: k.admitted_receipt(GRAPH, "render.logo"),
    # lifecycle, promotion, release, archive
    "production_state_vector": lambda: ProductionStateVector(project_id=k.new_id(), production_id=k.new_id()),
    "promotion_gate": lambda: PromotionGate(gate_id=k.new_id(), kind=GateKind.HUMAN_REVIEW),
    "release_proof": lambda: ReleaseProof(
        release_id=k.new_id(), recorded_phase=ReleasePhase.RECEIPTED, replayed_phase=ReleasePhase.RECEIPTED
    ),
    "archive_object": lambda: ArchiveObject(
        ref=k.ref(EntityKind.ARTIFACT, "asset.logo"), digest=k.digest("archived bytes")
    ),
    # ports
    "provider_handle": lambda: ProviderHandle(
        boundary=PortBoundary.PROVIDER_COMPILER,
        provider_id="provider.test",
        opaque_reference="tmp/step-one",
        issued_at_ms=NOW,
        expires_at_ms=NOW + 60_000,
    ),
    "provider_descriptor": lambda: ProviderDescriptor(
        provider_id="provider.test",
        component=k.component_version("m02.provider", "1.0.0"),
        boundaries=(PortBoundary.PROVIDER_COMPILER,),
    ),
    "dependency_observation": lambda: DependencyObservation(
        revision_id=k.chain_revision().revision_id,
        node_id="render.logo",
        observed=(k.ref(EntityKind.ARTIFACT, "asset.logo"),),
    ),
}


class DerivedTypeMapTests(unittest.TestCase):
    def test_the_map_is_frozen_after_import(self) -> None:
        self.assertIsInstance(SERIALIZABLE_TYPES, MappingProxyType)
        with self.assertRaises(TypeError):
            SERIALIZABLE_TYPES["invented_record"] = AliasRef  # type: ignore[index]

    def test_every_entry_is_a_kernel_record_naming_itself(self) -> None:
        for name, cls in sorted(SERIALIZABLE_TYPES.items()):
            with self.subTest(name=name):
                self.assertTrue(issubclass(cls, Record))
                self.assertTrue(cls.__module__.startswith("iris_project_os."), cls.__module__)
                self.assertEqual(name, transport_name(cls))
                self.assertNotIn(".", cls.__qualname__, f"{name} is nested, so its wire name is ambiguous")

    def test_a_foreign_record_is_not_serializable_here(self) -> None:
        """M01 owns its own envelope; a kernel that could carry the other's types has two truths."""

        with self.assertRaises(SchemaValidationError) as caught:
            type_name(q.contract())
        self.assertIn("not a serializable kernel type", str(caught.exception))

    def test_no_two_records_claim_one_transport_name(self) -> None:
        by_class = {id(cls): name for name, cls in SERIALIZABLE_TYPES.items()}
        self.assertEqual(len(by_class), len(SERIALIZABLE_TYPES))

    def test_the_map_covers_every_area_the_kernel_ships(self) -> None:
        areas = {cls.__module__.rsplit(".", 1)[-1] for cls in SERIALIZABLE_TYPES.values()}
        self.assertEqual(
            areas,
            {
                "analysis", "archive", "branching", "build", "diffing", "graph", "identity",
                "lifecycle", "merge", "ports", "promotion", "release", "reuse", "snapshots",
            },
        )

    def test_transport_name_follows_the_class_not_its_module(self) -> None:
        self.assertEqual(transport_name(AliasRef), "alias_ref")
        self.assertEqual(transport_name(RelocatedSample), "relocated_sample")

    def test_the_battery_reaches_every_kernel_module(self) -> None:
        built = {SERIALIZABLE_TYPES[name].__module__ for name in BUILDERS}
        shipped = {cls.__module__ for cls in SERIALIZABLE_TYPES.values()}
        self.assertEqual(built, shipped)


@dataclass(frozen=True)
class RelocatedSample(Record):
    """A record defined outside the kernel modules, to prove the map only claims what the kernel owns."""

    value: str = "x"


class EnvelopeTests(unittest.TestCase):
    def test_the_envelope_is_exactly_four_keys(self) -> None:
        found = envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        self.assertEqual(set(found), set(ENVELOPE_KEYS))
        self.assertEqual(found["schema_version"], SCHEMA_VERSION)
        self.assertEqual(found["type"], "external_ref")

    def test_the_digest_is_of_the_canonical_payload(self) -> None:
        found = envelope(k.chain_definition())
        self.assertEqual(found["payload_sha256"], content_digest(found["payload"]))

    def test_every_built_sample_survives_the_envelope(self) -> None:
        for name in sorted(BUILDERS):
            with self.subTest(name=name):
                value = sample(name)
                self.assertEqual(from_envelope(envelope(value)), value)

    def test_an_altered_payload_is_detected_before_parsing(self) -> None:
        found = envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        found["payload"]["reference"] = "asset.someone-elses"
        with self.assertRaises(SchemaValidationError) as caught:
            from_envelope(found)
        self.assertIn("altered in transit", str(caught.exception))

    def test_a_forged_digest_does_not_make_the_payload_true(self) -> None:
        found = envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        found["payload_sha256"] = k.digest("whatever")
        with self.assertRaises(SchemaValidationError):
            from_envelope(found)

    def test_a_type_this_kernel_does_not_own_is_refused(self) -> None:
        found = envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        found["type"] = "nonesuch_record"
        found["payload_sha256"] = content_digest(found["payload"])
        with self.assertRaises(SchemaValidationError) as caught:
            from_envelope(found)
        self.assertIn("does not know how to read it", str(caught.exception))

    def test_a_schema_version_this_kernel_cannot_read_is_refused(self) -> None:
        found = envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        found["schema_version"] = "iris-project-os-schema-v99"
        with self.assertRaises(UnsupportedVersionError):
            from_envelope(found)

    def test_the_envelope_is_a_closed_record(self) -> None:
        found = envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        with self.assertRaises(SchemaValidationError):
            from_envelope({**found, "signed_by": "whoever"})
        for key in sorted(ENVELOPE_KEYS):
            with self.subTest(key=key):
                stripped = {item: value for item, value in found.items() if item != key}
                with self.assertRaises(SchemaValidationError):
                    from_envelope(stripped)

    def test_a_non_mapping_envelope_is_refused(self) -> None:
        for value in ("envelope", 7, [envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))]):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(SchemaValidationError):
                    from_envelope(value)

    def test_a_non_mapping_payload_is_refused(self) -> None:
        found = envelope(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        found["payload"] = "asset.logo"
        found["payload_sha256"] = content_digest(found["payload"])
        with self.assertRaises(SchemaValidationError):
            from_envelope(found)

    def test_only_the_declared_schema_versions_are_readable(self) -> None:
        self.assertEqual(SUPPORTED_SCHEMA_VERSIONS, frozenset({SCHEMA_VERSION}))

    def test_an_envelope_is_not_itself_serializable(self) -> None:
        with self.assertRaises(SchemaValidationError):
            envelope(envelope(k.ref(EntityKind.ARTIFACT, "asset.logo")))


class TypeNamingTests(unittest.TestCase):
    def test_a_stranger_has_no_name(self) -> None:
        for value in (SimpleNamespace(), 42, "snapshot", k.SideEffectClass.NO_SIDE_EFFECT, RelocatedSample()):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(SchemaValidationError):
                    type_name(value)

    def test_every_built_sample_names_itself(self) -> None:
        for name in sorted(BUILDERS):
            with self.subTest(name=name):
                self.assertEqual(type_name(sample(name)), name)


class TextSerializationTests(unittest.TestCase):
    def test_one_object_emits_one_byte_string(self) -> None:
        value = k.chain_definition()
        self.assertEqual(dumps(value), dumps(value))
        self.assertEqual(dumps(value, indent=2), dumps(value, indent=2))

    def test_emitted_text_is_canonical_json(self) -> None:
        text = dumps(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        self.assertEqual(text, json.dumps(json.loads(text), ensure_ascii=False, sort_keys=True))
        self.assertNotIn("\n", text)

    def test_round_trips_are_stable_over_two_hops(self) -> None:
        again = loads(dumps(GRAPH))
        self.assertEqual(loads(dumps(again)), GRAPH)

    def test_text_that_is_not_json_is_reported(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            loads("{not json")
        self.assertIn("not valid JSON", str(caught.exception))

    def test_loads_refuses_what_was_never_text(self) -> None:
        for value in (None, 12, ["a"], {"schema_version": SCHEMA_VERSION}):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(SchemaValidationError):
                    loads(value)  # type: ignore[arg-type]

    def test_indentation_changes_nothing_about_the_decoded_object(self) -> None:
        self.assertEqual(loads(dumps(k.cache_trust(), indent=4)), k.cache_trust())

    def test_two_equal_records_emit_the_same_bytes(self) -> None:
        first = k.artifact_identity()
        again = ArtifactIdentity.from_payload(first.to_payload())
        self.assertIsNot(first, again)
        self.assertEqual(dumps(first), dumps(again))


class PayloadValidationTests(unittest.TestCase):
    def test_a_payload_is_valid_only_when_it_re_emits_unchanged(self) -> None:
        value = k.ref(EntityKind.ARTIFACT, "asset.logo")
        self.assertEqual(validate_payload("external_ref", value.to_payload()), value)

    def test_a_payload_that_normalises_on_the_way_in_is_not_canonical(self) -> None:
        value = DependencyObservation(
            revision_id=k.chain_revision().revision_id,
            node_id="render.logo",
            observed=(k.ref(EntityKind.ARTIFACT, "asset.b"), k.ref(EntityKind.ARTIFACT, "asset.a")),
        )
        payload = value.to_payload()
        self.assertEqual([item["reference"] for item in payload["observed"]], ["asset.a", "asset.b"])
        scrambled = {**payload, "observed": list(reversed(payload["observed"]))}
        with self.assertRaises(SchemaValidationError) as caught:
            validate_payload("dependency_observation", scrambled)
        self.assertIn("not canonical", str(caught.exception))

    def test_an_unknown_type_name_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_payload("a_record_nobody_wrote", {})

    def test_an_untrusted_field_is_refused(self) -> None:
        value = k.ref(EntityKind.ARTIFACT, "asset.logo")
        with self.assertRaises(SchemaValidationError):
            validate_payload("external_ref", {**value.to_payload(), "signed_by": "me"})

    def test_a_missing_required_field_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_payload("external_ref", {"reference": "asset.logo"})

    def test_decoding_re_runs_the_construction_laws(self) -> None:
        """Stored bytes get no exemption: an unknown kind is refused on the way back in."""

        with self.assertRaises(SchemaValidationError):
            validate_payload("external_ref", {"kind": "NOT_A_KIND", "reference": "asset.logo"})


if __name__ == "__main__":
    unittest.main()
