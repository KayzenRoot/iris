"""Reference stores: what the M03 kernel may hold, and what it must never decide.

§13 of the frozen contract lets M03 ship registries and in-memory stores "for tests" and leaves
production persistence to M06/M55, so this file states the *law* a store has to satisfy — as two
protocols a later module can implement — and ships one faithful in-memory implementation of each.
Nothing here imports a driver, opens a socket or touches a path, and there is no module-level store
instance: a singleton repository is a global mutable authority, which the Work Order forbids by name.

Two laws govern every record this file admits, and they are the laws that make a retry safe:

*admitting identical content again is a retry, not an event.* The row does not change, no duplicate
appears, and the caller gets back the object the store holds.
*admitting different content under one key is a conflict.* The store refuses and names both digests,
because overwriting quietly is how a cache starts asserting history nobody wrote.

Two more laws make an M03 store different from a dict:

*enumeration is ordered by key, never by arrival.* Two stores fed the same records in different
orders list identically, so a store's own digest can be quoted in evidence.
*capacity is refused, not degraded.* A bounded store that dropped its oldest row would turn a
memory limit into silent data loss; eviction is M55's decision, not this one's.

And the law specific to briefs: **a revision is admitted only into the lineage it claims.** A
revision naming a predecessor or an ancestor this store never recorded is refused, because the only
honest reading of that citation is that the store is being asked to testify to a history it does not
hold. Name binding stays with :class:`CreativeBriefIdentity`: the store searches by alias but keys by
``brief_id``, so a rename cannot move a row.

Records are keyed by the identity they *carry*, read from their own type rather than from a caller's
claim about which family they belong to. That is the difference between a store that can answer "what
do you hold?" and one that can only repeat what it was told.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

from .admission import AdmissionReport
from .ambiguity import AmbiguityRecord, OpenQuestion
from .authority import AuthorityPolicyGraph
from .base import Labeled, Record
from .briefs import BriefRevision
from .conflicts import SemanticConflict
from .constraints import ConstraintBundle
from .errors import RefError, SchemaValidationError, StoreConflictError
from .execution import ExecutionIntentBundle
from .explanation import IntentExplanationGraph
from .fidelity import FidelityCompilationFingerprint, FidelityContractSpec
from .fingerprints import (
    ConstraintFingerprint,
    IntentDelta,
    SemanticEquivalenceProfile,
    SemanticIntentFingerprint,
)
from .freshness import BriefFreshnessVector, DerivedIntentDependency
from .identity import CreativeBriefIdentity
from .intent import IntentModel
from .limits import MAX_STORED_RECORDS
from .merge import BriefSemanticMergeAnalysis, RestorationRevision
from .migration import MigrationReceipt
from .overrides import OverrideDebt, OverrideLedger, OverrideReceipt
from .ports import ExtensionObservation
from .readiness import SemanticReleaseReadinessReport
from .reuse import ReuseAssessment, ReusePassport
from .slicing import MinimumSufficientSemanticSlice
from .sources import ProvenanceCapsule
from .versions import content_digest, require_identifier

__all__ = [
    "RecordFamily",
    "RECORD_FAMILIES",
    "family_of",
    "record_id_of",
    "listing_digest",
    "BriefRepository",
    "SemanticRepository",
    "InMemoryBriefStore",
    "InMemorySemanticStore",
]


class RecordFamily(Labeled):
    """The M03 records a store may be handed, named so one store holds many without losing either.

    Each family is exactly one frozen record type plus the field that identifies it, because the
    records already carry their own identity rules and a flattened "generic M03 row" shape would be a
    second record model competing with the real ones. A type nobody may store is not a family:
    value objects that only ever live inside a parent record (a ``PredicateCall``, a
    ``SemanticRef``) have no independent existence to key, and admitting them would let a store hold
    citations that outlived the record which made them meaningful.
    """

    INTENT_MODEL = "INTENT_MODEL"
    CONSTRAINT_BUNDLE = "CONSTRAINT_BUNDLE"
    SEMANTIC_SLICE = "SEMANTIC_SLICE"
    INTENT_FINGERPRINT = "INTENT_FINGERPRINT"
    CONSTRAINT_FINGERPRINT = "CONSTRAINT_FINGERPRINT"
    SEMANTIC_DELTA = "SEMANTIC_DELTA"
    EQUIVALENCE_PROFILE = "EQUIVALENCE_PROFILE"
    FRESHNESS_VECTOR = "FRESHNESS_VECTOR"
    DEPENDENCY = "DEPENDENCY"
    REUSE_PASSPORT = "REUSE_PASSPORT"
    REUSE_ASSESSMENT = "REUSE_ASSESSMENT"
    CONTRACT_SPEC = "CONTRACT_SPEC"
    COMPILATION_FINGERPRINT = "COMPILATION_FINGERPRINT"
    EXECUTION_BUNDLE = "EXECUTION_BUNDLE"
    EXPLANATION_GRAPH = "EXPLANATION_GRAPH"
    CONFLICT = "CONFLICT"
    OVERRIDE_RECEIPT = "OVERRIDE_RECEIPT"
    OVERRIDE_LEDGER = "OVERRIDE_LEDGER"
    OVERRIDE_DEBT = "OVERRIDE_DEBT"
    MERGE_ANALYSIS = "MERGE_ANALYSIS"
    RESTORATION_REVISION = "RESTORATION_REVISION"
    MIGRATION_RECEIPT = "MIGRATION_RECEIPT"
    READINESS_REPORT = "READINESS_REPORT"
    ADMISSION_REPORT = "ADMISSION_REPORT"
    AUTHORITY_GRAPH = "AUTHORITY_GRAPH"
    PROVENANCE_CAPSULE = "PROVENANCE_CAPSULE"
    EXTENSION_OBSERVATION = "EXTENSION_OBSERVATION"
    OPEN_QUESTION = "OPEN_QUESTION"
    AMBIGUITY = "AMBIGUITY"

    @property
    def record_type(self) -> type[Record]:
        """Which frozen record this family is the storage of."""

        return _FAMILY_TYPES[self]

    @property
    def id_field(self) -> str:
        """Which field carries the record's own identity, and therefore the store's key."""

        return _FAMILY_ID_FIELDS[self]


RECORD_FAMILIES: tuple[RecordFamily, ...] = tuple(RecordFamily)

_FAMILY_TYPES: Mapping[RecordFamily, type[Record]] = MappingProxyType(
    {
        RecordFamily.INTENT_MODEL: IntentModel,
        RecordFamily.CONSTRAINT_BUNDLE: ConstraintBundle,
        RecordFamily.SEMANTIC_SLICE: MinimumSufficientSemanticSlice,
        RecordFamily.INTENT_FINGERPRINT: SemanticIntentFingerprint,
        RecordFamily.CONSTRAINT_FINGERPRINT: ConstraintFingerprint,
        RecordFamily.SEMANTIC_DELTA: IntentDelta,
        RecordFamily.EQUIVALENCE_PROFILE: SemanticEquivalenceProfile,
        RecordFamily.FRESHNESS_VECTOR: BriefFreshnessVector,
        RecordFamily.DEPENDENCY: DerivedIntentDependency,
        RecordFamily.REUSE_PASSPORT: ReusePassport,
        RecordFamily.REUSE_ASSESSMENT: ReuseAssessment,
        RecordFamily.CONTRACT_SPEC: FidelityContractSpec,
        RecordFamily.COMPILATION_FINGERPRINT: FidelityCompilationFingerprint,
        RecordFamily.EXECUTION_BUNDLE: ExecutionIntentBundle,
        RecordFamily.EXPLANATION_GRAPH: IntentExplanationGraph,
        RecordFamily.CONFLICT: SemanticConflict,
        RecordFamily.OVERRIDE_RECEIPT: OverrideReceipt,
        RecordFamily.OVERRIDE_LEDGER: OverrideLedger,
        RecordFamily.OVERRIDE_DEBT: OverrideDebt,
        RecordFamily.MERGE_ANALYSIS: BriefSemanticMergeAnalysis,
        RecordFamily.RESTORATION_REVISION: RestorationRevision,
        RecordFamily.MIGRATION_RECEIPT: MigrationReceipt,
        RecordFamily.READINESS_REPORT: SemanticReleaseReadinessReport,
        RecordFamily.ADMISSION_REPORT: AdmissionReport,
        RecordFamily.AUTHORITY_GRAPH: AuthorityPolicyGraph,
        RecordFamily.PROVENANCE_CAPSULE: ProvenanceCapsule,
        RecordFamily.EXTENSION_OBSERVATION: ExtensionObservation,
        RecordFamily.OPEN_QUESTION: OpenQuestion,
        RecordFamily.AMBIGUITY: AmbiguityRecord,
    }
)

_FAMILY_ID_FIELDS: Mapping[RecordFamily, str] = MappingProxyType(
    {
        RecordFamily.INTENT_MODEL: "model_id",
        RecordFamily.CONSTRAINT_BUNDLE: "bundle_id",
        RecordFamily.SEMANTIC_SLICE: "slice_id",
        RecordFamily.INTENT_FINGERPRINT: "fingerprint_id",
        RecordFamily.CONSTRAINT_FINGERPRINT: "fingerprint_id",
        RecordFamily.SEMANTIC_DELTA: "delta_id",
        RecordFamily.EQUIVALENCE_PROFILE: "profile_id",
        RecordFamily.FRESHNESS_VECTOR: "vector_id",
        RecordFamily.DEPENDENCY: "dependency_id",
        RecordFamily.REUSE_PASSPORT: "passport_id",
        RecordFamily.REUSE_ASSESSMENT: "assessment_id",
        RecordFamily.CONTRACT_SPEC: "compilation_id",
        RecordFamily.COMPILATION_FINGERPRINT: "fingerprint_id",
        RecordFamily.EXECUTION_BUNDLE: "bundle_id",
        RecordFamily.EXPLANATION_GRAPH: "graph_id",
        RecordFamily.CONFLICT: "conflict_id",
        RecordFamily.OVERRIDE_RECEIPT: "override_id",
        RecordFamily.OVERRIDE_LEDGER: "ledger_id",
        RecordFamily.OVERRIDE_DEBT: "debt_id",
        RecordFamily.MERGE_ANALYSIS: "analysis_id",
        RecordFamily.RESTORATION_REVISION: "restoration_id",
        RecordFamily.MIGRATION_RECEIPT: "migration_id",
        RecordFamily.READINESS_REPORT: "report_id",
        RecordFamily.ADMISSION_REPORT: "report_id",
        RecordFamily.AUTHORITY_GRAPH: "graph_id",
        RecordFamily.PROVENANCE_CAPSULE: "capsule_id",
        RecordFamily.EXTENSION_OBSERVATION: "observation_id",
        RecordFamily.OPEN_QUESTION: "question_id",
        RecordFamily.AMBIGUITY: "ambiguity_id",
    }
)

_FAMILIES_BY_TYPE: Mapping[type, RecordFamily] = MappingProxyType(
    {cls: item for item, cls in _FAMILY_TYPES.items()}
)


def family_of(record: Any) -> RecordFamily:
    """Which family a record belongs to, read from its own type rather than from a caller's claim.

    Exact type identity, not ``isinstance``: a future subclass would otherwise be admitted under its
    parent's key while carrying fields the parent's id field does not name.
    """

    found = _FAMILIES_BY_TYPE.get(type(record))
    if found is None:
        raise SchemaValidationError(
            f"{type(record).__name__} is not a storable M03 record; a store that accepted anything would "
            f"stop being able to answer what it holds ({RecordFamily.describe()})"
        )
    return found


def record_id_of(record: Any) -> str:
    """The identifier a record carries for itself, which is the only key a store may use."""

    item = family_of(record)
    return require_identifier(getattr(record, item.id_field), item.id_field)


def listing_digest(records: Iterable[Any]) -> str:
    """A digest over the content of a whole listing, so an audit can quote one number.

    Ordered by the caller's enumeration, which is itself key-ordered; a digest that depended on
    arrival order would report a different value for one store.
    """

    return content_digest([item.digest() for item in records])


def _admit(
    items: dict[Any, Any], key: Any, record: Any, *, what: str, capacity: int = MAX_STORED_RECORDS
) -> Any:
    """The one admission law every store shares, applied to one key.

    Returning the stored row instead of the caller's equal row keeps identity stable: two callers that
    admitted the same content now hold the same object, so a later disagreement between them is visible
    rather than silent.
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


# --- the two abstractions a later module implements -------------------------------------------------
#
# Each is a Protocol, so a persistence layer in M06 or M55 satisfies it without importing this file's
# implementation. The read side of the law is the part worth stating: ``get`` answers ``None`` for a
# key it has never held, and the caller decides whether absence is a retry, a gap or an error. A store
# that raised on absence would make "we never recorded this" indistinguishable from "we lost it".


@runtime_checkable
class BriefRepository(Protocol):
    """Holds brief identities and the immutable revisions registered against them."""

    def register(self, identity: CreativeBriefIdentity) -> CreativeBriefIdentity: ...

    def admit(self, revision: BriefRevision) -> BriefRevision: ...

    def identity(self, brief_id: str) -> CreativeBriefIdentity | None: ...

    def revision(self, revision_id: str) -> BriefRevision | None: ...

    def resolve(self, identifier: str) -> CreativeBriefIdentity | None: ...


@runtime_checkable
class SemanticRepository(Protocol):
    """Holds the derived records a revision produced, keyed by the family and id each one carries."""

    def put(self, record: Any) -> Any: ...

    def get(self, family: Any, record_id: str) -> Any | None: ...

    def of_family(self, family: Any) -> tuple[Any, ...]: ...


# --- reference implementations ----------------------------------------------------------------------


@dataclass
class InMemoryBriefStore:
    """The reference brief store: identities first, then revisions that prove where they came from.

    A revision is admitted only into a lineage the store already holds. ``predecessor_revision_id``
    and ``ancestor_revision_ids`` are citations to revisions, and a store that accepted them without
    checking would certify that a brief has a history it cannot produce — which is worse than an
    error, because the resulting chain looks auditable.

    The store never answers "which revision is in force". :meth:`newest` reports the highest
    revision number it holds, which is a lookup; whether that revision is what a production runs is
    M02's branch head, and a store that decided it would be owning project history.
    """

    capacity: int = MAX_STORED_RECORDS
    _identities: dict[str, CreativeBriefIdentity] = field(default_factory=dict, repr=False)
    _revisions: dict[str, BriefRevision] = field(default_factory=dict, repr=False)

    def register(self, identity: Any) -> CreativeBriefIdentity:
        item = CreativeBriefIdentity.coerce(identity, "identity")
        claimed = sorted(
            {
                other.brief_id
                for alias in item.aliases
                for other in self._identities.values()
                if other.brief_id != item.brief_id and other.known_as(alias)
            }
        )
        if claimed:
            raise RefError(
                f"brief {item.brief_id} claims a name already registered by {claimed}; one alias "
                "answering to two briefs is a lookup that returns whichever was stored first"
            )
        return _admit(
            self._identities, item.brief_id, item, what="brief identity", capacity=self.capacity
        )

    def admit(self, revision: Any) -> BriefRevision:
        item = BriefRevision.coerce(revision, "revision")
        owner = self._identities.get(item.brief_id)
        if owner is None:
            raise RefError(
                f"revision {item.revision_id} belongs to brief {item.brief_id}, which this store never "
                "registered; admitting it would leave content no brief owns"
            )
        predecessor = (
            None if item.predecessor_revision_id is None else self._revisions.get(item.predecessor_revision_id)
        )
        if item.predecessor_revision_id is not None and predecessor is None:
            raise RefError(
                f"revision {item.revision_id} says it supersedes {item.predecessor_revision_id}, which "
                "this store does not hold; the lineage would read as auditable while being unverifiable"
            )
        if predecessor is not None and predecessor.brief_id != item.brief_id:
            raise RefError(
                f"revision {item.revision_id} of brief {item.brief_id} cites predecessor "
                f"{predecessor.revision_id}, which belongs to brief {predecessor.brief_id}; superseding "
                "across briefs would merge two intents by writing one row"
            )
        if predecessor is not None and item.revision_number <= predecessor.revision_number:
            raise RefError(
                f"revision {item.revision_id} is numbered {item.revision_number} behind predecessor "
                f"{predecessor.revision_id} at {predecessor.revision_number}; lineage that does not move "
                "forward is a cycle wearing a number"
            )
        absent = sorted(set(item.ancestor_revision_ids) - set(self._revisions))
        if absent:
            raise RefError(
                f"revision {item.revision_id} lists ancestors {absent} that this store never admitted; "
                "a lineage is only evidence if every step of it can be produced"
            )
        return _admit(self._revisions, item.revision_id, item, what="revision", capacity=self.capacity)

    def identity(self, brief_id: str) -> CreativeBriefIdentity | None:
        return self._identities.get(require_identifier(brief_id, "brief_id"))

    def revision(self, revision_id: str) -> BriefRevision | None:
        return self._revisions.get(require_identifier(revision_id, "revision_id"))

    def holds(self, revision_id: str) -> bool:
        return self.revision(revision_id) is not None

    def resolve(self, identifier: str) -> CreativeBriefIdentity | None:
        """Find a brief by id or by any alias it declared.

        Aliases are searchable but never keys: two briefs that both claimed one alias is a conflict
        between identities, and :meth:`register` is where that is refused.
        """

        wanted = require_identifier(identifier, "identifier")
        direct = self._identities.get(wanted)
        if direct is not None:
            return direct
        matches = tuple(item for item in self._identities.values() if item.known_as(wanted))
        return matches[0] if matches else None

    def aliases_held_by(self, alias: str) -> tuple[str, ...]:
        wanted = require_identifier(alias, "alias")
        return tuple(sorted(item.brief_id for item in self._identities.values() if wanted in item.aliases))

    def revisions_of(self, brief_id: str) -> tuple[BriefRevision, ...]:
        """Every revision of one brief, by revision number then id, whatever order they arrived in."""

        wanted = require_identifier(brief_id, "brief_id")
        return tuple(
            sorted(
                (item for item in self._revisions.values() if item.brief_id == wanted),
                key=lambda item: (item.revision_number, item.revision_id),
            )
        )

    def admitted_revisions(self, brief_id: str) -> tuple[BriefRevision, ...]:
        return tuple(item for item in self.revisions_of(brief_id) if item.admitted)

    def newest(self, brief_id: str) -> BriefRevision | None:
        """The highest-numbered revision held — the newest recorded, not the one in force."""

        items = self.revisions_of(brief_id)
        return items[-1] if items else None

    def brief_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._identities))

    def revision_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._revisions))

    def missing_revisions(self, revision_ids: Iterable[str]) -> tuple[str, ...]:
        """Which of these ids the store cannot produce.

        Gates ask this before quoting a lineage: a readiness report citing a revision nobody holds is
        damaged evidence, and finding that out during an audit is the wrong time.
        """

        wanted = {require_identifier(item, "revision_id") for item in revision_ids}
        return tuple(sorted(wanted - set(self._revisions)))

    @property
    def size(self) -> int:
        return len(self._identities) + len(self._revisions)

    def listing_digest(self) -> str:
        return listing_digest(
            (*self.identities(), *(self._revisions[key] for key in self.revision_ids()))
        )

    def identities(self) -> tuple[CreativeBriefIdentity, ...]:
        return tuple(self._identities[key] for key in sorted(self._identities))


@dataclass
class InMemorySemanticStore:
    """The reference store for derived records, keyed by ``(family, record_id)``.

    The compound key is the type's own claim: two families can legitimately use the same identifier
    string — an intent fingerprint and a constraint fingerprint are different facts about different
    collections — and a store that flattened them would answer "what produced this?" wrongly.

    Nothing is derived from what is stored here. This class answers "do you hold X, and can you hand
    it back byte-identically"; it does not decide whether a record is *correct*, which is the kernel's
    job and happened before the record could be constructed at all.
    """

    capacity: int = MAX_STORED_RECORDS
    _items: dict[tuple[str, str], Any] = field(default_factory=dict, repr=False)

    def put(self, record: Any, *, family: Any = None) -> Any:
        derived = family_of(record)
        wanted = RecordFamily.parse(family, "family") if family is not None else derived
        if wanted is not derived:
            raise SchemaValidationError(
                f"{type(record).__name__} is a {derived.value}, not {wanted.value}; a store that filed "
                "records where a caller pointed would let a bundle be read back as a model"
            )
        key = (wanted.value, record_id_of(record))
        return _admit(self._items, key, record, what=wanted.value, capacity=self.capacity)

    def get(self, family: Any, record_id: str) -> Any | None:
        parsed = RecordFamily.parse(family, "family")
        return self._items.get((parsed.value, require_identifier(record_id, "record_id")))

    def holds(self, family: Any, record_id: str) -> bool:
        return self.get(family, record_id) is not None

    def of_family(self, family: Any) -> tuple[Any, ...]:
        parsed = RecordFamily.parse(family, "family")
        return tuple(
            self._items[key] for key in sorted(self._items) if key[0] == parsed.value
        )

    def ids_of(self, family: Any) -> tuple[str, ...]:
        parsed = RecordFamily.parse(family, "family")
        return tuple(key[1] for key in sorted(self._items) if key[0] == parsed.value)

    def missing(self, family: Any, record_ids: Iterable[str]) -> tuple[str, ...]:
        """Which ids of one family this store cannot hand back."""

        parsed = RecordFamily.parse(family, "family")
        wanted = {require_identifier(item, "record_id") for item in record_ids}
        held = {key[1] for key in self._items if key[0] == parsed.value}
        return tuple(sorted(wanted - held))

    def families_held(self) -> tuple[str, ...]:
        return tuple(sorted({key[0] for key in self._items}))

    def counts(self) -> tuple[tuple[str, int], ...]:
        """How many of each family, always listing every family so a zero stays visible."""

        return tuple((item.value, sum(1 for key in self._items if key[0] == item.value)) for item in RecordFamily)

    def records(self) -> tuple[Any, ...]:
        return tuple(self._items[key] for key in sorted(self._items))

    @property
    def size(self) -> int:
        return len(self._items)

    def listing_digest(self) -> str:
        return listing_digest(self.records())
