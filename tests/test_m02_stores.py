"""The store law §7 allows and §11 demands: append-only, ordered, bounded and never a singleton.

Three things make a repository safe to build evidence on, and each is a refusal here rather than a
prose promise: admitting identical content again is a retry, admitting different content under one key
is a conflict, and a store that runs out of room says so instead of forgetting something. The rest of
the file checks the parts a caller can otherwise get wrong quietly — that a revision cannot arrive for
an artifact nobody registered, that an artifact cannot be re-typed by writing a revision for it, and
that the kernel has exactly one snapshot repository rather than two competing ones.
"""

from __future__ import annotations

import ast
import inspect
import sys
import unittest
from types import MappingProxyType, SimpleNamespace
from typing import Any

from iris_project_os.analysis import DependencyDiscoveryReceipt
from iris_project_os.base import Record
from iris_project_os.branching import ForkReceipt
from iris_project_os.errors import (
    IdentityError,
    SchemaValidationError,
    StoreConflictError,
)
from iris_project_os.identity import (
    ArtifactIdentity,
    EntityKind,
    RevisionRef,
    TransitionReceipt,
)
from iris_project_os.snapshots import SnapshotStore
from iris_project_os.stores import (
    ArtifactRepository,
    InMemoryArtifactStore,
    InMemoryReceiptStore,
    ReceiptKind,
    ReceiptRepository,
    SnapshotRepository,
    listing_digest,
    missing_snapshots,
    receipt_id_of,
    receipt_kind_of,
    snapshots_held,
)

from tests import m02_kernel_support as k

PRODUCTION = k.new_id()
NOW = k.CACHE_NOW
VECTOR = k.ref(EntityKind.SEMANTIC_TYPE, "vector.svg")
RASTER = k.ref(EntityKind.SEMANTIC_TYPE, "raster.png")


def identity(**over: Any) -> ArtifactIdentity:
    payload: dict[str, Any] = dict(
        artifact_id=k.new_id(),
        production_id=PRODUCTION,
        semantic_type_ref=VECTOR,
        display_name="logo",
        created_at_ms=NOW,
    )
    payload.update(over)
    return ArtifactIdentity(**payload)


def revision_for(record: ArtifactIdentity, **over: Any) -> RevisionRef:
    payload: dict[str, Any] = dict(
        artifact_id=record.artifact_id,
        revision_id=k.new_id(),
        content_digest=k.digest("first bytes"),
        semantic_type_ref=record.semantic_type_ref,
        created_at_ms=NOW,
    )
    payload.update(over)
    return RevisionRef(**payload)


def registered(**over: Any) -> tuple[InMemoryArtifactStore, ArtifactIdentity]:
    store = InMemoryArtifactStore()
    record = store.register(identity(**over))
    return store, record


def fork_receipt(**over: Any) -> ForkReceipt:
    payload: dict[str, Any] = dict(
        fork_id=k.new_id(),
        source_branch_id=k.new_id(),
        source_snapshot_id=k.new_id(),
        new_branch_id=k.new_id(),
        reason_code="alternate-direction",
        created_at_ms=NOW,
    )
    payload.update(over)
    return ForkReceipt(**payload)


def discovery_receipt(**over: Any) -> DependencyDiscoveryReceipt:
    payload: dict[str, Any] = dict(
        discovery_id=k.new_id(),
        observed_by=k.ref(EntityKind.ATTEMPT, k.new_id()),
        attempt_id=k.new_id(),
        consumer_node_id="render.logo",
        observed_reference=k.ref(EntityKind.ARTIFACT, "asset.font"),
        observed_at_ms=NOW,
    )
    payload.update(over)
    return DependencyDiscoveryReceipt(**payload)


def transition_receipt(**over: Any) -> TransitionReceipt:
    payload: dict[str, Any] = dict(
        transition_id=k.new_id(),
        entity_kind=EntityKind.PRODUCTION,
        entity_id=PRODUCTION,
        from_state="DRAFT",
        to_state="ACTIVE",
        actor=k.component_version("m02.os", "1.0.0"),
        reason_code="first-promotion",
        timestamp_ms=NOW,
    )
    payload.update(over)
    return TransitionReceipt(**payload)


class ReceiptKindTests(unittest.TestCase):
    def test_every_kind_names_the_record_it_stores(self) -> None:
        self.assertEqual(len(ReceiptKind.members()), 8)
        for item in ReceiptKind:
            self.assertTrue(issubclass(item.record_type, Record))

    def test_the_kind_maps_are_frozen(self) -> None:
        from iris_project_os import stores

        self.assertIsInstance(stores._RECEIPT_TYPES, MappingProxyType)
        self.assertIsInstance(stores._RECEIPT_ID_FIELDS, MappingProxyType)
        with self.assertRaises(TypeError):
            stores._RECEIPT_TYPES[ReceiptKind.FORK] = dict  # type: ignore[index]

    def test_a_kind_is_read_from_the_record_not_from_a_claim(self) -> None:
        self.assertIs(receipt_kind_of(fork_receipt()), ReceiptKind.FORK)
        self.assertIs(receipt_kind_of(discovery_receipt()), ReceiptKind.DEPENDENCY_DISCOVERY)

    def test_a_non_receipt_is_refused_rather_than_stored(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            receipt_kind_of(k.ref(EntityKind.ARTIFACT, "asset.logo"))
        self.assertIn("not a kernel receipt", str(caught.exception))

    def test_receipt_id_reads_the_field_that_kind_uses(self) -> None:
        value = fork_receipt()
        self.assertEqual(receipt_id_of(value), value.fork_id)
        found = discovery_receipt()
        self.assertEqual(receipt_id_of(found), found.discovery_id)

    def test_unknown_kind_text_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            ReceiptKind.parse("TELEMETRY", "kind")


class AdmissionLawTests(unittest.TestCase):
    def test_admitting_the_same_row_twice_is_a_retry(self) -> None:
        store, record = registered()
        first = store.admit(revision_for(record))
        again = store.admit(first)
        self.assertIs(first, again)
        self.assertEqual(store.size, 2)

    def test_an_equal_copy_under_one_id_is_the_stored_row(self) -> None:
        store, record = registered()
        value = revision_for(record)
        self.assertIs(store.admit(value), store.admit(RevisionRef.from_payload(value.to_payload())))

    def test_different_content_under_one_id_is_a_conflict(self) -> None:
        store, record = registered()
        value = revision_for(record)
        store.admit(value)
        rewritten = RevisionRef.from_payload({**value.to_payload(), "format_version": "2.0.0"})
        with self.assertRaises(StoreConflictError) as caught:
            store.admit(rewritten)
        self.assertIn("refuses to overwrite", str(caught.exception))

    def test_a_full_store_refuses_rather_than_evicting(self) -> None:
        store = InMemoryArtifactStore(capacity=1)
        store.register(identity())
        with self.assertRaises(StoreConflictError) as caught:
            store.register(identity())
        self.assertIn("bounds growth rather than evicting", str(caught.exception))

    def test_capacity_bounds_revisions_separately_from_identities(self) -> None:
        store = InMemoryArtifactStore(capacity=1)
        record = store.register(identity())
        store.admit(revision_for(record))
        with self.assertRaises(StoreConflictError):
            store.admit(revision_for(record, revision_id=k.new_id(), content_digest=k.digest("other")))


class ArtifactStoreIntegrityTests(unittest.TestCase):
    def test_a_revision_for_an_unregistered_artifact_is_refused(self) -> None:
        store = InMemoryArtifactStore()
        with self.assertRaises(IdentityError) as caught:
            store.admit(revision_for(identity()))
        self.assertIn("never registered", str(caught.exception))

    def test_a_revision_cannot_retype_the_artifact_it_writes_to(self) -> None:
        store, record = registered()
        with self.assertRaises(IdentityError) as caught:
            store.admit(revision_for(record, semantic_type_ref=RASTER))
        self.assertIn("change what an artifact means", str(caught.exception))

    def test_registration_accepts_a_payload_and_refuses_a_stranger(self) -> None:
        value = identity()
        store = InMemoryArtifactStore()
        self.assertEqual(store.register(value.to_payload()), value)
        with self.assertRaises(SchemaValidationError):
            store.register("asset.logo")

    def test_re_registering_a_renamed_artifact_is_a_conflict(self) -> None:
        store, record = registered()
        with self.assertRaises(StoreConflictError):
            store.register(record.renamed("logo-alt"))

    def test_lookup_requires_a_real_id(self) -> None:
        store, _ = registered()
        with self.assertRaises(SchemaValidationError):
            store.identity("logo")

    def test_a_missing_id_reads_as_nothing(self) -> None:
        store, _ = registered()
        self.assertIsNone(store.identity(k.new_id()))
        self.assertIsNone(store.revision(k.new_id()))
        self.assertFalse(store.has_identity(k.new_id()))


class ArtifactStoreEnumerationTests(unittest.TestCase):
    def test_artifacts_are_listed_by_id_not_by_arrival(self) -> None:
        first, second = identity(), identity()
        forward = InMemoryArtifactStore()
        backward = InMemoryArtifactStore()
        for store, record in ((forward, first), (forward, second), (backward, second), (backward, first)):
            store.register(record)
        self.assertEqual(forward.artifacts(), backward.artifacts())
        self.assertEqual(forward.listing_digest(), backward.listing_digest())

    def test_history_is_ordered_by_time_then_id(self) -> None:
        store, record = registered()
        late = store.admit(revision_for(record, revision_id=k.new_id(), created_at_ms=NOW + 10))
        early = store.admit(
            revision_for(record, revision_id=k.new_id(), content_digest=k.digest("older"), created_at_ms=NOW - 10)
        )
        self.assertEqual(store.history(), (early, late))

    def test_the_same_bytes_in_two_artifacts_stay_two_facts(self) -> None:
        store = InMemoryArtifactStore()
        shared = k.digest("one payload")
        first = store.register(identity())
        second = store.register(identity())
        a = store.admit(revision_for(first, content_digest=shared))
        b = store.admit(revision_for(second, content_digest=shared))
        self.assertEqual(store.locate(shared), tuple(sorted((a, b), key=lambda item: (item.created_at_ms, item.revision_id))))
        self.assertEqual(store.artifacts_holding(shared), tuple(sorted({first.artifact_id, second.artifact_id})))

    def test_revisions_of_one_artifact_ignore_the_others(self) -> None:
        store = InMemoryArtifactStore()
        first = store.register(identity())
        second = store.register(identity())
        store.admit(revision_for(first))
        store.admit(revision_for(second, revision_id=k.new_id(), content_digest=k.digest("other")))
        self.assertEqual([item.artifact_id for item in store.revisions_of(first.artifact_id)], [first.artifact_id])

    def test_for_production_selects_by_owner(self) -> None:
        store, record = registered()
        store.register(identity(production_id=k.new_id()))
        self.assertEqual(store.for_production(PRODUCTION), (record,))
        with self.assertRaises(SchemaValidationError):
            store.for_production("my production")

    def test_digests_are_unique_and_sorted(self) -> None:
        store, record = registered()
        first = k.digest("one")
        second = k.digest("two")
        store.admit(revision_for(record, content_digest=second))
        store.admit(revision_for(record, revision_id=k.new_id(), content_digest=first))
        self.assertEqual(store.digests(), tuple(sorted({first, second})))

    def test_listing_digest_changes_when_content_changes(self) -> None:
        store, record = registered()
        before = store.listing_digest()
        store.admit(revision_for(record))
        self.assertNotEqual(before, store.listing_digest())

    def test_listing_digest_helper_reads_record_content(self) -> None:
        value = identity()
        self.assertEqual(listing_digest([value]), listing_digest([value]))
        self.assertNotEqual(listing_digest([value]), listing_digest([value.renamed("other")]))


class ReceiptStoreTests(unittest.TestCase):
    def test_records_are_kept_by_kind_and_id(self) -> None:
        store = InMemoryReceiptStore()
        value = fork_receipt()
        store.record(value)
        self.assertIs(store.get(ReceiptKind.FORK, value.fork_id), value)
        self.assertTrue(store.holds("fork", value.fork_id))
        self.assertFalse(store.holds("merge", value.fork_id))

    def test_one_id_under_two_kinds_stays_two_claims(self) -> None:
        store = InMemoryReceiptStore()
        shared = k.new_id()
        first = store.record(fork_receipt(fork_id=shared))
        second = store.record(discovery_receipt(discovery_id=shared))
        self.assertEqual(store.size, 2)
        self.assertIs(store.get(ReceiptKind.FORK, shared), first)
        self.assertIs(store.get(ReceiptKind.DEPENDENCY_DISCOVERY, shared), second)

    def test_recording_the_same_receipt_twice_is_a_retry(self) -> None:
        store = InMemoryReceiptStore()
        value = transition_receipt()
        self.assertIs(store.record(value), store.record(value))
        self.assertEqual(store.size, 1)

    def test_a_full_receipt_store_refuses(self) -> None:
        store = InMemoryReceiptStore(capacity=1)
        store.record(fork_receipt())
        with self.assertRaises(StoreConflictError):
            store.record(transition_receipt())

    def test_every_kind_is_counted_even_at_zero(self) -> None:
        store = InMemoryReceiptStore()
        store.record(fork_receipt())
        counts = dict(store.counts())
        self.assertEqual(len(counts), len(ReceiptKind.members()))
        self.assertEqual(counts["FORK"], 1)
        self.assertEqual(counts["MERGE"], 0)

    def test_of_kind_and_receipts_are_ordered_by_id(self) -> None:
        store = InMemoryReceiptStore()
        ids = sorted([k.new_id(), k.new_id()])
        for value in (fork_receipt(fork_id=ids[1]), fork_receipt(fork_id=ids[0])):
            store.record(value)
        self.assertEqual([receipt_id_of(item) for item in store.of_kind("fork")], ids)
        self.assertEqual([receipt_id_of(item) for item in store.receipts()], ids)

    def test_a_non_receipt_never_enters_the_store(self) -> None:
        store = InMemoryReceiptStore()
        with self.assertRaises(SchemaValidationError):
            store.record(SimpleNamespace(receipt_id=k.new_id()))

    def test_lookup_by_an_unknown_kind_is_refused(self) -> None:
        store = InMemoryReceiptStore()
        with self.assertRaises(SchemaValidationError):
            store.get("teleportation", k.new_id())

    def test_a_single_kind_holds_each_receipt_type(self) -> None:
        store = InMemoryReceiptStore()
        for value in (fork_receipt(), discovery_receipt(), transition_receipt()):
            store.record(value)
        self.assertEqual({type(item) for item in store.receipts()}, {ForkReceipt, DependencyDiscoveryReceipt, TransitionReceipt})


class RepositoryProtocolTests(unittest.TestCase):
    def test_the_reference_stores_satisfy_their_own_protocols(self) -> None:
        self.assertIsInstance(InMemoryArtifactStore(), ArtifactRepository)
        self.assertIsInstance(InMemoryReceiptStore(), ReceiptRepository)

    def test_the_kernels_snapshot_store_is_the_one_snapshot_repository(self) -> None:
        self.assertIsInstance(SnapshotStore(), SnapshotRepository)

    def test_a_store_missing_a_method_is_not_a_repository(self) -> None:
        self.assertNotIsInstance(SimpleNamespace(register=lambda *a: None), ArtifactRepository)
        self.assertNotIsInstance(SimpleNamespace(), ReceiptRepository)

    def test_snapshots_held_is_ordered_whatever_the_backing_store_does(self) -> None:
        graph = k.bound(records=k.chain_records())
        sealed = k.snapshot(production_id="prod.test", closure_value=k.closure(production_id="prod.test", graph=graph))
        other = k.snapshot(
            production_id="prod.other", closure_value=k.closure(production_id="prod.other", graph=graph)
        )
        store = SnapshotStore()
        for value in (sealed, other):
            store.commit(value)
        self.assertEqual(snapshots_held(store), tuple(sorted((sealed, other), key=lambda item: item.snapshot_id)))

    def test_missing_snapshots_names_what_the_store_cannot_produce(self) -> None:
        graph = k.bound(records=k.chain_records())
        sealed = k.snapshot(production_id="prod.test", closure_value=k.closure(production_id="prod.test", graph=graph))
        store = SnapshotStore()
        store.commit(sealed)
        absent = k.new_id()
        self.assertEqual(missing_snapshots(store, [absent, sealed.snapshot_id]), (absent,))
        self.assertEqual(missing_snapshots(store, []), ())

    def test_missing_snapshots_refuses_a_malformed_id(self) -> None:
        with self.assertRaises(SchemaValidationError):
            missing_snapshots(SnapshotStore(), ["head"])


class StoreNeutralityTests(unittest.TestCase):
    tree = ast.parse(inspect.getsource(__import__("iris_project_os.stores", fromlist=["stores"])))

    def roots(self) -> set[str]:
        found: set[str] = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".", 1)[0])
        return found

    def calls(self) -> set[str]:
        found: set[str] = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                target = node.func
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    found.add(f"{target.value.id}.{target.attr}")
                elif isinstance(target, ast.Name):
                    found.add(target.id)
        return found

    def test_the_store_layer_imports_only_the_kernel_and_the_standard_library(self) -> None:
        self.assertLessEqual(self.roots(), set(sys.stdlib_module_names) | {"iris_project_os"})
        for vendor in ("sqlalchemy", "psycopg", "boto3", "pymongo", "redis", "requests", "httpx", "openai"):
            self.assertNotIn(vendor, self.roots())

    def test_the_store_layer_never_opens_a_socket_a_shell_or_a_file(self) -> None:
        for forbidden in ("socket.socket", "socket.create_connection", "subprocess.run", "os.system", "open"):
            self.assertNotIn(forbidden, self.calls(), f"stores.py reaches for {forbidden}")

    def test_no_module_level_store_instance_exists(self) -> None:
        from iris_project_os import stores

        for name, value in vars(stores).items():
            self.assertNotIsInstance(
                value, (InMemoryArtifactStore, InMemoryReceiptStore, SnapshotStore),
                f"stores.{name} is a global mutable store",
            )


class StoreIsolationTests(unittest.TestCase):
    def test_two_stores_share_no_state(self) -> None:
        first, first_record = registered()
        before = first.listing_digest()
        second = InMemoryArtifactStore()
        mine = second.register(identity())
        second.admit(revision_for(mine))
        self.assertEqual(first.listing_digest(), before)
        self.assertEqual((first.size, second.size), (1, 2))
        with self.assertRaises(IdentityError):
            first.admit(revision_for(mine, revision_id=k.new_id()))


if __name__ == "__main__":
    unittest.main()
