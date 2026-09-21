"""Store abstractions and the deterministic in-memory references the kernel ships with.

§7 of the frozen contract allows M02 to provide reference repositories and forbids it from hardcoding a
database vendor; production content-addressed storage belongs to M55 and M06. So this file states the
*law* a store has to satisfy — as three protocols a later module can implement — and ships one faithful
in-memory implementation of each, which is what the kernel's own tests and the synthetic profiles run
against. Nothing here imports a driver, opens a socket or touches a path, and no module-level store
instance exists: store state belongs to an instance, because a singleton repository is a global mutable
authority of exactly the kind §11 forbids.

One admission law governs all three stores, and it is the law that makes a retry safe:

*admitting identical content again is a retry, not an event.* The row does not change, no duplicate
appears, and the caller gets back what the store holds.
*admitting different content under one key is a conflict.* The store refuses it and says which two
digests collided, because silently overwriting is how a cache starts asserting history nobody wrote.
*enumeration is ordered by key, never by arrival.* Two stores fed the same records in different orders
list identically, so a store's own digest can be quoted in evidence.
*capacity is refused, not degraded.* A bounded store that quietly drops the oldest row would turn a
memory limit into silent data loss.

Referential integrity is enforced where the kernel already has a vocabulary for it: an artifact revision
is admitted for an artifact this store has registered, and it has to carry the semantic type that
registration declared. A rename or a move is not this store's problem — ``AliasLedger`` in
:mod:`iris_project_os.identity` owns name binding, and duplicating that rule here is how two answers to
"what is this called?" get into circulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

from .analysis import DependencyDiscoveryReceipt
from .archive import RevivalReceipt
from .base import Labeled
from .branching import ForkReceipt
from .errors import IdentityError, SchemaValidationError, StoreConflictError
from .identity import ArtifactIdentity, RevisionRef, TransitionReceipt, require_id
from .limits import MAX_STORED_RECORDS
from .merge import MergeReceipt
from .release import WithdrawalReceipt
from .reuse import ReuseReceipt
from .snapshots import RollbackReceipt, Snapshot
from .versions import content_digest, require_digest

__all__ = [
    "ReceiptKind",
    "ArtifactRepository",
    "SnapshotRepository",
    "ReceiptRepository",
    "InMemoryArtifactStore",
    "InMemoryReceiptStore",
    "receipt_kind_of",
    "receipt_id_of",
    "listing_digest",
    "missing_snapshots",
    "snapshots_held",
]


class ReceiptKind(Labeled):
    """The kernel's receipts, named so one store can hold several kinds without losing either.

    Each receipt type already carries its own identity rules, so the store keys on the pair
    ``(kind, receipt_id)`` rather than inventing a common receipt record — a shared receipt shape would be
    a second receipt model, and §8 forbids exactly that competition.
    """

    TRANSITION = "TRANSITION"
    FORK = "FORK"
    MERGE = "MERGE"
    ROLLBACK = "ROLLBACK"
    WITHDRAWAL = "WITHDRAWAL"
    REVIVAL = "REVIVAL"
    REUSE = "REUSE"
    DEPENDENCY_DISCOVERY = "DEPENDENCY_DISCOVERY"

    @property
    def record_type(self) -> type:
        """Which frozen record this kind is the answer for."""

        return _RECEIPT_TYPES[self]


_RECEIPT_TYPES: Mapping[ReceiptKind, type] = MappingProxyType(
    {
        ReceiptKind.TRANSITION: TransitionReceipt,
        ReceiptKind.FORK: ForkReceipt,
        ReceiptKind.MERGE: MergeReceipt,
        ReceiptKind.ROLLBACK: RollbackReceipt,
        ReceiptKind.WITHDRAWAL: WithdrawalReceipt,
        ReceiptKind.REVIVAL: RevivalReceipt,
        ReceiptKind.REUSE: ReuseReceipt,
        ReceiptKind.DEPENDENCY_DISCOVERY: DependencyDiscoveryReceipt,
    }
)

_RECEIPT_ID_FIELDS: Mapping[ReceiptKind, str] = MappingProxyType(
    {
        ReceiptKind.TRANSITION: "transition_id",
        ReceiptKind.FORK: "fork_id",
        ReceiptKind.MERGE: "merge_id",
        ReceiptKind.ROLLBACK: "rollback_id",
        ReceiptKind.WITHDRAWAL: "withdrawal_id",
        ReceiptKind.REVIVAL: "revival_id",
        ReceiptKind.REUSE: "receipt_id",
        ReceiptKind.DEPENDENCY_DISCOVERY: "discovery_id",
    }
)


def receipt_kind_of(receipt: Any) -> ReceiptKind:
    """Which kind a receipt record is, read from its own type rather than from a caller's claim."""

    found = [item for item, cls in _RECEIPT_TYPES.items() if type(receipt) is cls]
    if not found:
        raise SchemaValidationError(
            f"{type(receipt).__name__} is not a kernel receipt; a store that accepted anything would stop "
            f"being able to answer what it holds ({', '.join(sorted(item.value for item in ReceiptKind))})"
        )
    return found[0]


def receipt_id_of(receipt: Any) -> str:
    kind = receipt_kind_of(receipt)
    return require_id(getattr(receipt, _RECEIPT_ID_FIELDS[kind]), f"{kind.value.lower()}_id")


def _admit(
    items: dict[str, Any], key: str, record: Any, *, what: str, capacity: int = MAX_STORED_RECORDS
) -> Any:
    """The one admission law every store shares, applied to one key.

    Returning the stored row instead of the caller's equal row keeps identity stable: two callers that
    admitted the same content now hold the same object, so a later mutation attempt on either is visible.
    """

    existing = items.get(key)
    if existing is not None:
        if existing.digest() != record.digest():
            raise StoreConflictError(
                f"{what} {key} is already stored at {existing.digest()[:12]} and this copy says "
                f"{record.digest()[:12]}; the store keeps what it was given and refuses to overwrite it"
            )
        return existing
    if len(items) >= capacity:
        raise StoreConflictError(
            f"{what} store holds its admitted maximum of {capacity} records; a reference store bounds "
            "growth rather than evicting, because eviction is M55's decision to make"
        )
    items[key] = record
    return record


def listing_digest(records: Iterable[Any]) -> str:
    """A digest over the ordered content of a whole store, so an audit can quote one number.

    Ordered by the caller's enumeration, which is itself key-ordered; a digest that depended on arrival
    order would report a different value for one store.
    """

    return content_digest([item.digest() for item in records])


# --- the three abstractions a later module implements --------------------------------------------
#
# Each is a Protocol, so a production repository in M55 satisfies it without importing M02's
# implementation. The snapshot abstraction is deliberately the shape ``iris_project_os.snapshots
# .SnapshotStore`` already has: the kernel has one snapshot repository and §8 forbids a second competing
# one, so this file states the contract it satisfies instead of shipping an alternative.


@runtime_checkable
class ArtifactRepository(Protocol):
    """Holds artifact identities and the immutable content revisions registered against them."""

    def register(self, identity: ArtifactIdentity) -> ArtifactIdentity: ...

    def admit(self, revision: RevisionRef) -> RevisionRef: ...

    def identity(self, artifact_id: str) -> ArtifactIdentity | None: ...

    def revision(self, revision_id: str) -> RevisionRef | None: ...


@runtime_checkable
class SnapshotRepository(Protocol):
    """Holds committed snapshots. Callers may read and add, never replace.

    ``get`` reports a missing snapshot rather than returning nothing: a restore that quietly skipped an
    absent snapshot would hand back a partial history and call it the original.
    """

    def commit(self, snapshot: Any) -> Snapshot: ...

    def get(self, snapshot_id: str) -> Snapshot: ...

    @property
    def snapshot_ids(self) -> tuple[str, ...]: ...


@runtime_checkable
class ReceiptRepository(Protocol):
    """Holds the kernel's receipts so a retry can find the one it already made."""

    def record(self, receipt: Any) -> Any: ...

    def get(self, kind: Any, receipt_id: str) -> Any | None: ...

    def of_kind(self, kind: Any) -> tuple[Any, ...]: ...


def snapshots_held(store: SnapshotRepository) -> tuple[Snapshot, ...]:
    """Everything a snapshot repository holds, in id order, whatever its own enumeration looks like."""

    return tuple(store.get(item) for item in sorted(store.snapshot_ids))


def missing_snapshots(store: SnapshotRepository, snapshot_ids: Iterable[str]) -> tuple[str, ...]:
    """Which of the ids this store cannot produce.

    The archive layer asks this before it certifies a manifest: an archive naming a snapshot nobody can
    hand back is damaged material, and finding that out during a restore is the wrong time.
    """

    held = {item for item in store.snapshot_ids}
    return tuple(sorted({require_id(item, "snapshot_id") for item in snapshot_ids if item not in held}))


# --- reference implementations --------------------------------------------------------------------


@dataclass
class InMemoryArtifactStore:
    """The reference artifact store: append-only, content-addressed, ordered by id.

    Revisions are keyed by their own immutable id, not by artifact, because one artifact has many
    revisions and "the current one" is a branch-head question this store must not answer — that is how a
    store would start owning history.

    Re-registering an artifact under a new display name is a conflict, not an update. The identity record
    is what the first registration asserted, and names move through ``AliasLedger``; letting a store row
    mutate would mean the same artifact id has meant two things to whoever read it in between.
    """

    capacity: int = MAX_STORED_RECORDS
    _identities: dict[str, ArtifactIdentity] = field(default_factory=dict, repr=False)
    _revisions: dict[str, RevisionRef] = field(default_factory=dict, repr=False)

    def register(self, identity: ArtifactIdentity) -> ArtifactIdentity:
        wanted = self._as_identity(identity)
        return _admit(self._identities, wanted.artifact_id, wanted, what="artifact", capacity=self.capacity)

    def admit(self, revision: RevisionRef) -> RevisionRef:
        wanted = revision if isinstance(revision, RevisionRef) else RevisionRef.from_payload(revision)
        owner = self._identities.get(wanted.artifact_id)
        if owner is None:
            raise IdentityError(
                f"revision {wanted.revision_id} belongs to artifact {wanted.artifact_id}, which this store "
                "never registered; admitting it would leave content no artifact owns"
            )
        if owner.semantic_type_ref.text != wanted.semantic_type_ref.text:
            raise IdentityError(
                f"revision {wanted.revision_id} declares {wanted.semantic_type_ref.text} while artifact "
                f"{owner.artifact_id} is a {owner.semantic_type_ref.text}; re-typing an artifact by writing a "
                "revision for it would let bytes change what an artifact means"
            )
        return _admit(self._revisions, wanted.revision_id, wanted, what="revision", capacity=self.capacity)

    @staticmethod
    def _as_identity(value: Any) -> ArtifactIdentity:
        if isinstance(value, ArtifactIdentity):
            return value
        if isinstance(value, Mapping):
            return ArtifactIdentity.from_payload(value)
        raise SchemaValidationError(
            f"an artifact identity must be an ArtifactIdentity or its payload, got {type(value).__name__}"
        )

    def identity(self, artifact_id: str) -> ArtifactIdentity | None:
        return self._identities.get(require_id(artifact_id, "artifact_id"))

    def revision(self, revision_id: str) -> RevisionRef | None:
        return self._revisions.get(require_id(revision_id, "revision_id"))

    def has_identity(self, artifact_id: str) -> bool:
        return self.identity(artifact_id) is not None

    def revisions_of(self, artifact_id: str) -> tuple[RevisionRef, ...]:
        wanted = require_id(artifact_id, "artifact_id")
        return tuple(item for item in self.history() if item.artifact_id == wanted)

    def history(self) -> tuple[RevisionRef, ...]:
        """Every revision ever admitted, oldest id first by digest rather than by arrival."""

        return tuple(sorted(self._revisions.values(), key=lambda item: (item.created_at_ms, item.revision_id)))

    def locate(self, content_digest_value: Any) -> tuple[RevisionRef, ...]:
        """Every revision holding these exact bytes — the same-bytes, different-artifact answer.

        Content addressing deliberately does not deduplicate into one row: two artifacts that happen to
        hash alike are two facts about two artifacts, and collapsing them would lose which run made which.
        """

        wanted = require_digest(content_digest_value, "content_digest")
        return tuple(item for item in self.history() if item.content_digest == wanted)

    def artifacts_holding(self, content_digest_value: Any) -> tuple[str, ...]:
        return tuple(sorted({item.artifact_id for item in self.locate(content_digest_value)}))

    def for_production(self, production_id: str) -> tuple[ArtifactIdentity, ...]:
        wanted = require_id(production_id, "production_id")
        return tuple(item for item in self.artifacts() if item.production_id == wanted)

    def artifacts(self) -> tuple[ArtifactIdentity, ...]:
        return tuple(self._identities[key] for key in sorted(self._identities))

    def digests(self) -> tuple[str, ...]:
        return tuple(sorted({item.content_digest for item in self._revisions.values()}))

    @property
    def size(self) -> int:
        return len(self._identities) + len(self._revisions)

    def listing_digest(self) -> str:
        return listing_digest((*self.artifacts(), *self.history()))


@dataclass
class InMemoryReceiptStore:
    """The reference receipt store, keyed by ``(kind, receipt_id)``.

    Ids are UUIDs so a collision across kinds is impossible in practice, but the compound key is still
    what the type states: a fork receipt and a merge receipt are different claims even if a caller hands
    over one identifier twice, and a store that flattened them would answer "what proved this?" wrongly.
    """

    capacity: int = MAX_STORED_RECORDS
    _items: dict[tuple[str, str], Any] = field(default_factory=dict, repr=False)

    def record(self, receipt: Any) -> Any:
        kind = receipt_kind_of(receipt)
        key = (kind.value, receipt_id_of(receipt))
        return _admit(self._items, key, receipt, what=f"{kind.value} receipt", capacity=self.capacity)

    def get(self, kind: Any, receipt_id: str) -> Any | None:
        parsed = ReceiptKind.parse(kind, "kind")
        return self._items.get((parsed.value, require_id(receipt_id, "receipt_id")))

    def holds(self, kind: Any, receipt_id: str) -> bool:
        return self.get(kind, receipt_id) is not None

    def of_kind(self, kind: Any) -> tuple[Any, ...]:
        parsed = ReceiptKind.parse(kind, "kind")
        return tuple(self._items[key] for key in sorted(self._items) if key[0] == parsed.value)

    def receipts(self) -> tuple[Any, ...]:
        return tuple(self._items[key] for key in sorted(self._items))

    def counts(self) -> tuple[tuple[str, int], ...]:
        """How many of each kind, always listing every kind so a zero stays visible."""

        return tuple(
            (item.value, sum(1 for key in self._items if key[0] == item.value)) for item in ReceiptKind
        )

    @property
    def size(self) -> int:
        return len(self._items)

    def listing_digest(self) -> str:
        return listing_digest(self.receipts())
