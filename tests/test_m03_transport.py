"""The transport and persistence law of M03: §12's boundaries, §13's serialization, §14's refusals.

Four claims are proven here, and each one is a refusal rather than a promise.

*What a store holds is decided by the record's own type.* A store that filed a record wherever a
caller pointed could be told that a constraint bundle is an intent model, and every later reader
would repeat the lie. So :func:`~iris_intent.stores.family_of` reads the type, and the family table
is the closed set it may answer about (§13).

*Admission is append-only, ordered and bounded.* Retrying an identical record is not an event;
writing different content under one id is a conflict; a full store refuses instead of forgetting;
and enumeration is by key, so a store's digest can be quoted in evidence without also quoting the
order the rows happened to arrive in (§13, §15).

*A document has to say what it is before anything reads what it means.* Every M03 record leaves the
kernel inside an envelope naming the schema version, the kind and the contract version, sealed with
a digest checked before decoding, and the kind map is derived from the package itself so a record
cannot be forgotten on the wire (§13).

*The neighbours keep their own namespaces.* Refs into M01/M02 are citations M03 receives, never
identities M03 mints; HIVE memory is derived context (§5.40); a provider observation can report a
gap but cannot carry a statement, a constraint or an authority (§5.42); and wanting something
published is not the authority to publish it (§5.41). Branch, variant and rollback topology stay
with M02, and no store here claims to know which revision is in force (§5.39).

Domain neutrality (§6) and the six-domain run are proven in ``tests/test_m03_domain_neutrality.py``.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import pkgutil
import unittest
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any

import iris_intent
from iris_intent.base import Record
from iris_intent.briefs import BriefRevision
from iris_intent.errors import (
    AuthorityError,
    IntentKernelError,
    PortContractError,
    PredicateError,
    RefError,
    SchemaValidationError,
    StoreConflictError,
    UntrustedExtensionError,
    UnsupportedVersionError,
)
from iris_intent.execution import (
    ExecutionGapClass,
    ExecutionIntentStatus,
    IntentOperation,
    SideEffectClass,
    compile_execution_intent,
)
from iris_intent.fingerprints import SemanticIntentFingerprint
from iris_intent.identity import (
    UNTRUSTED_SOURCES,
    VERSIONED_REF_KINDS,
    AuthorityLevel,
    CreativeBriefIdentity,
    RefKind,
    SemanticRef,
    SourceKind,
    ceiling_for,
    is_untrusted,
)
from iris_intent.intent import IntentStatement, ModalChannel, StatementKind
from iris_intent.ports import (
    CANONICAL_MUTATION_KEYS,
    PORT_BOUNDARIES,
    PORT_PROTOCOLS,
    ExtensionBoundary,
    ExtensionObservation,
    ExtensionPorts,
    ExtensionRef,
    ProviderDescriptor,
    boundaries_admitting,
    require_answered_ref,
    require_port,
)
from iris_intent.predicates import PredicateCall, PredicateRegistry
from iris_intent.serialization import (
    SerializationEnvelope,
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
from iris_intent.slicing import structural_footprint
from iris_intent.sources import AnchorSpan, RawInputRef
from iris_intent.stores import (
    RECORD_FAMILIES,
    BriefRepository,
    InMemoryBriefStore,
    InMemorySemanticStore,
    RecordFamily,
    SemanticRepository,
    family_of,
    listing_digest,
    record_id_of,
)
from iris_intent.versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    ComponentVersion,
    canonical_json,
    content_digest,
)

from tests import m03_kernel_support as S

KERNEL = Path(iris_intent.__file__).resolve().parent

#: The twelve namespaces §12 of the contract allows M03 to ask somebody else about.
CONTRACT_BOUNDARIES = frozenset(
    {
        "PROJECT_GRAPH",
        "SEMANTIC_TYPE",
        "IDENTITY_ANCHOR",
        "QUALITY_PROFILE",
        "PROVIDER_CAPABILITY",
        "CANON_STORY",
        "CONTEXT_DEPENDENCY",
        "PROVENANCE_RIGHTS",
        "SECURITY_AUTHORITY",
        "DELIVERY_DESTINATION",
        "EXPLANATION_EXPORT",
        "DOMAIN_VOCABULARY",
    }
)

DELETION_VOCABULARY = {"delete", "remove", "pop", "clear", "discard", "update", "replace", "truncate"}


# --------------------------------------------------------------------------- #
# fixtures local to this file: the store law needs real lineages, not single rows
# --------------------------------------------------------------------------- #


def brief(ident: str = S.BRIEF_ID, *, aliases: tuple[str, ...] = ()) -> CreativeBriefIdentity:
    return S.brief_identity(brief_id=ident, aliases=aliases)


def registered(*aliases: str) -> InMemoryBriefStore:
    """A store holding one brief and its first three revisions — a lineage the law accepts."""

    store = InMemoryBriefStore()
    store.register(brief(aliases=tuple(aliases)))
    for item in S.revision_chain((1, 2, 3)):
        store.admit(item)
    return store


def numbered(
    number: int,
    *,
    ident: str,
    brief_id: str = S.BRIEF_ID,
    predecessor: str | None = None,
    ancestors: tuple[str, ...] = (),
    statements: tuple[Any, ...] | None = None,
    **over: Any,
) -> BriefRevision:
    """A revision whose claimed lineage is spelled out rather than assumed by the helper."""

    return S.revision(
        number,
        statements if statements is not None else (S.statement(f"st.{ident}", S.LOGO),),
        ident=ident,
        brief_id=brief_id,
        predecessor_revision_id=predecessor,
        ancestor_revision_ids=ancestors,
        **over,
    )


def vocabulary_provider(**over: Any) -> ProviderDescriptor:
    arguments: dict[str, Any] = {
        "provider_id": "m04.ir",
        "component": ComponentVersion(identifier="m04-semantic-type-registry", version="1.0.0"),
        "boundaries": ("SEMANTIC_TYPE",),
        "capabilities": ("carries_paths",),
    }
    arguments.update(over)
    return ProviderDescriptor(**arguments)


class VocabularyStub:
    """A §12.2 provider answering exactly the two questions that boundary asks."""

    def __init__(self, descriptor: ProviderDescriptor) -> None:
        self.descriptor = descriptor

    def type_of(self, reference: Any) -> Any:
        return reference

    def carries_path(self, reference: Any, semantic_path: str) -> bool:
        return False


class HalfPortStub(VocabularyStub):
    """A provider that claims a boundary it cannot actually answer."""

    carries_path = None  # type: ignore[assignment]


class DomainVocabularyStub:
    """A §12.12 provider: it answers the domain's vocabulary questions and nothing else."""

    def __init__(self, descriptor: ProviderDescriptor) -> None:
        self.descriptor = descriptor

    def signature_for(self, reference: Any) -> Any:
        return reference

    def path_of(self, reference: Any) -> Any:
        return reference


def semantic_type_ref() -> SemanticRef:
    return S.ref(RefKind.SEMANTIC_TYPE.value, "type.iso.scene")


def extension_ref(*, provider: str | None = "m04.ir") -> ExtensionRef:
    return ExtensionRef(boundary="SEMANTIC_TYPE", reference=semantic_type_ref(), provider_id=provider)


def observation(**over: Any) -> ExtensionObservation:
    arguments: dict[str, Any] = {
        "observation_id": "obs.type.iso",
        "boundary": "SEMANTIC_TYPE",
        "provider_id": "m04.ir",
        "about": extension_ref(),
        "revision_ref": S.revision_ref("rev.3"),
        "facts": {"carrier": "m04-scene-ir"},
    }
    arguments.update(over)
    return ExtensionObservation(**arguments)


def compiled_execution(ident: str = "xb.iris", operations: Any = None, **over: Any):
    revision = S.admitted_revision()
    return compile_execution_intent(
        bundle_id=ident,
        brief_ref=revision.brief_ref,
        revision_ref=revision.revision_ref,
        intent_fingerprint_digest=S.fingerprint(revision, ident=f"fp.{ident}").semantic_digest,
        constraint_fingerprint_digest=S.bundle_fingerprint(
            S.bundle([S.rule("cn.logo")]), ident=f"bfp.{ident}"
        ).semantic_digest,
        fidelity_fingerprint_digest=content_digest(f"fidelity.{ident}"),
        operations=tuple(operations or (validating_operation(revision),)),
        **over,
    )


def validating_operation(revision: Any, ident: str = "io.validate", **over: Any) -> IntentOperation:
    arguments: dict[str, Any] = {
        "intent_operation_id": ident,
        "family": "VALIDATE",
        "purpose": "check the admitted mark against the compiled contract",
        "subject_refs": (revision.brief_ref,),
        "originating_refs": (S.ref(RefKind.STATEMENT.value, revision.statement_ids[0]),),
        "required_explanation_refs": (S.ref(RefKind.PROVENANCE.value, "cap.st.1"),),
        "fidelity_contract_refs": (S.ref(RefKind.CONTRACT_SET.value, "contracts.iris"),),
    }
    arguments.update(over)
    return IntentOperation(**arguments)


def producing_operation(revision: Any, ident: str = "io.package", **over: Any) -> IntentOperation:
    arguments: dict[str, Any] = {
        "intent_operation_id": ident,
        "family": "PACKAGE",
        "purpose": "deliver the approved mark",
        "subject_refs": (revision.brief_ref,),
        "output_type_refs": (S.ref(RefKind.SEMANTIC_TYPE.value, "type.delivery.package"),),
        "originating_refs": (S.ref(RefKind.STATEMENT.value, revision.statement_ids[0]),),
        "required_explanation_refs": (S.ref(RefKind.PROVENANCE.value, "cap.st.1"),),
        "fidelity_contract_refs": (S.ref(RefKind.CONTRACT_SET.value, "contracts.iris"),),
    }
    arguments.update(over)
    return IntentOperation(**arguments)


def wide_revision(ident: str = "rev.3") -> BriefRevision:
    """A four-path revision, so a slice has something honest to leave behind (§15)."""

    items = tuple(
        IntentStatement(
            statement_id=f"st.{index}",
            semantic_path=path,
            kind=StatementKind.DIRECTION.value,
            assertion=f"{path} holds",
            origin="EXPLICIT",
            authority=S.authority_ref(),
            value={"state": "on"},
            modality=modality,
            provenance=S.capsule(capsule_id=f"cap.{ident}.{index}"),
        )
        for index, (path, modality) in enumerate(
            (
                ("visual.logo.clearspace", ModalChannel.IMAGE.value),
                ("visual.logo.palette", ModalChannel.IMAGE.value),
                ("audio.tone.pace", ModalChannel.AUDIO.value),
                ("identity.spokesperson.name", ModalChannel.TEXT.value),
            )
        )
    )
    return S.revision(3, items, ident=ident)


def record_inventory() -> dict[str, Any]:
    """One instance of every M03 record this test layer can build lawfully."""

    revision = S.admitted_revision()
    model = S.model(revision)
    bundle = S.bundle([S.rule("cn.logo")])
    fingerprint = S.fingerprint(revision, ident="fp.rev")
    other = S.fingerprint(revision, ident="fp.other")
    dependency = S.dependency("dep.art")
    receipt = S.receipt(graph=S.authority_graph())
    debt = S.debt(override_ids=(receipt.override_id,))
    carried = compiled_execution()
    return {
        "SemanticRef": S.ref(RefKind.BRIEF.value, S.BRIEF_ID),
        "BriefRevisionRef": revision.ref,
        "CreativeBriefIdentity": brief(),
        "AnchorSpan": AnchorSpan(selector="take-04"),
        "SourceAnchor": S.passage("the mark must stay legible"),
        "RawInputRef": S.raw_source(),
        "ProvenanceCapsule": S.capsule(),
        "IntentStatement": S.statement("st.inventory"),
        "IntentAuthorityRef": S.authority_ref(),
        "BriefRevision": revision,
        "IntentModel": model,
        "Constraint": S.rule("cn.inventory"),
        "ConstraintBundle": bundle,
        "PredicateSignature": S.signature("shows_logo"),
        "PredicateCall": S.signature("shows_logo").bind({}),
        "MinimumSufficientSemanticSlice": S.slice_for(model, bundle),
        "SemanticIntentFingerprint": fingerprint,
        "ConstraintFingerprint": S.bundle_fingerprint(bundle, ident="fp.bundle"),
        "IntentDelta": S.delta(fingerprint, other),
        "SemanticEquivalenceProfile": S.equivalence_profile(),
        "AmbiguityRecord": S.ambiguity(),
        "OpenQuestion": S.question(),
        "AuthorityPolicyGraph": S.authority_graph(),
        "SemanticConflict": S.conflict(),
        "OverrideReceipt": receipt,
        "OverrideDebt": debt,
        "OverrideLedger": S.ledger([receipt], [debt]),
        "DerivedIntentDependency": dependency,
        "BriefFreshnessVector": S.vector([dependency], S.upstream_matching([dependency])),
        "ReusePassport": S.passport(revision, [dependency]),
        "SemanticReleaseReadinessReport": S.readiness(revision),
        "ExecutionIntentBundle": carried,
        "IntentOperation": validating_operation(revision),
        "ProviderDescriptor": vocabulary_provider(),
        "ExtensionRef": extension_ref(),
        "ExtensionObservation": observation(),
        "SerializationEnvelope": envelope_for(carried),
    }


# --------------------------------------------------------------------------- #
# §13: the family table
# --------------------------------------------------------------------------- #


class RecordFamilyTableTests(unittest.TestCase):
    def test_every_family_names_a_real_record_and_the_field_that_ids_it(self) -> None:
        self.assertEqual(len(RECORD_FAMILIES), 29)
        self.assertEqual(tuple(RecordFamily), RECORD_FAMILIES)
        for item in RECORD_FAMILIES:
            with self.subTest(family=item.value):
                self.assertTrue(issubclass(item.record_type, Record))
                self.assertTrue(is_dataclass(item.record_type))
                self.assertIn(item.id_field, {field.name for field in fields(item.record_type)})

    def test_one_record_type_belongs_to_exactly_one_family(self) -> None:
        types = [item.record_type for item in RECORD_FAMILIES]
        self.assertEqual(len(types), len(set(types)), "a record type filed under two families")

    def test_a_record_is_filed_from_its_own_type_not_from_a_claim(self) -> None:
        cases = (
            (S.bundle([S.rule("cn.logo")]), RecordFamily.CONSTRAINT_BUNDLE),
            (S.model(S.admitted_revision()), RecordFamily.INTENT_MODEL),
            (S.conflict(), RecordFamily.CONFLICT),
            (S.authority_graph(), RecordFamily.AUTHORITY_GRAPH),
            (S.capsule(), RecordFamily.PROVENANCE_CAPSULE),
        )
        for record, expected in cases:
            with self.subTest(record=type(record).__name__):
                self.assertIs(family_of(record), expected)

    def test_a_record_outside_the_table_is_refused(self) -> None:
        strangers = (
            S.statement("st.stranger"),
            S.rule("cn.stranger"),
            S.raw_source(),
            S.signature("shows_logo"),
            "bundle.iris",
        )
        for stranger in strangers:
            with self.subTest(record=type(stranger).__name__):
                with self.assertRaises(SchemaValidationError) as caught:
                    family_of(stranger)
                self.assertIn("not a storable M03 record", str(caught.exception))

    def test_record_id_reads_the_field_the_family_declares(self) -> None:
        cases = (
            (S.bundle([S.rule("cn.logo")]), "bundle_id"),
            (S.model(S.admitted_revision()), "model_id"),
            (S.fingerprint(S.admitted_revision()), "fingerprint_id"),
            (S.dependency("dep.id"), "dependency_id"),
            (S.authority_graph(), "graph_id"),
            (S.question("q.id"), "question_id"),
        )
        for record, name in cases:
            with self.subTest(record=type(record).__name__):
                self.assertIs(family_of(record).id_field, name)
                self.assertEqual(record_id_of(record), getattr(record, name))

    def test_the_family_tables_are_frozen(self) -> None:
        from iris_intent import stores

        self.assertIsInstance(stores._FAMILY_TYPES, MappingProxyType)
        self.assertIsInstance(stores._FAMILY_ID_FIELDS, MappingProxyType)
        self.assertIsInstance(stores._FAMILIES_BY_TYPE, MappingProxyType)
        with self.assertRaises(TypeError):
            stores._FAMILY_TYPES[RecordFamily.CONFLICT] = dict  # type: ignore[index]

    def test_a_family_accepts_its_own_text_and_refuses_a_stranger(self) -> None:
        self.assertIs(RecordFamily.parse("conflict", "family"), RecordFamily.CONFLICT)
        with self.assertRaises(SchemaValidationError):
            RecordFamily.parse("TELEMETRY", "family")


class BriefStoreAdmissionTests(unittest.TestCase):
    def test_a_revision_arrives_only_for_a_registered_brief(self) -> None:
        store = InMemoryBriefStore()
        with self.assertRaises(RefError) as caught:
            store.admit(numbered(1, ident="rev.1"))
        self.assertIn("never registered", str(caught.exception))

    def test_a_revision_arrives_only_after_its_predecessor(self) -> None:
        store = InMemoryBriefStore()
        store.register(brief())
        store.admit(numbered(1, ident="rev.1"))
        with self.assertRaises(RefError) as caught:
            store.admit(numbered(3, ident="rev.3", predecessor="rev.2", ancestors=("rev.1", "rev.2")))
        self.assertIn("which this store does not hold", str(caught.exception))

    def test_the_full_ancestor_chain_has_to_be_producible(self) -> None:
        store = InMemoryBriefStore()
        store.register(brief())
        store.admit(numbered(1, ident="rev.1"))
        store.admit(numbered(2, ident="rev.2", predecessor="rev.1", ancestors=("rev.1",)))
        admitted = store.admit(
            numbered(3, ident="rev.3", predecessor="rev.2", ancestors=("rev.1", "rev.2"))
        )
        self.assertEqual(admitted.revision_id, "rev.3")
        self.assertEqual(
            [item.revision_id for item in store.revisions_of(S.BRIEF_ID)], ["rev.1", "rev.2", "rev.3"]
        )

    def test_revision_numbers_have_to_move_forward(self) -> None:
        store = registered()
        with self.assertRaises(RefError) as caught:
            store.admit(numbered(2, ident="rev.back", predecessor="rev.3", ancestors=("rev.1", "rev.3")))
        self.assertIn("behind predecessor", str(caught.exception))

    def test_a_predecessor_from_another_brief_is_refused(self) -> None:
        store = registered()
        store.register(brief("brief.other"))
        with self.assertRaises(RefError) as caught:
            store.admit(
                numbered(
                    4,
                    ident="rev.other.4",
                    brief_id="brief.other",
                    predecessor="rev.3",
                    ancestors=("rev.3",),
                )
            )
        self.assertIn("belongs to brief", str(caught.exception))

    def test_admitting_the_same_revision_again_returns_the_stored_object(self) -> None:
        store = registered()
        held = store.revision("rev.2")
        self.assertIs(store.admit(held), held)
        self.assertIs(store.admit(BriefRevision.from_payload(held.to_payload())), held)
        self.assertEqual(store.size, 4)

    def test_different_content_under_one_revision_id_is_a_conflict(self) -> None:
        store = registered()
        held = store.revision("rev.2")
        rewritten = numbered(
            2,
            ident="rev.2",
            predecessor="rev.1",
            ancestors=("rev.1",),
            statements=(S.statement("st.quiet.edit", S.TONE),),
        )
        self.assertNotEqual(rewritten.digest(), held.digest())
        with self.assertRaises(StoreConflictError) as caught:
            store.admit(rewritten)
        self.assertIn("refuses to overwrite", str(caught.exception))
        self.assertIs(store.revision("rev.2"), held)

    def test_a_relabelled_identity_does_not_move_its_row(self) -> None:
        store = registered()
        held = store.identity(S.BRIEF_ID)
        renamed = CreativeBriefIdentity.from_payload({**held.to_payload(), "label": "Iris, take two"})
        with self.assertRaises(StoreConflictError):
            store.register(renamed)
        self.assertEqual(store.brief_ids(), (S.BRIEF_ID,))
        self.assertIs(store.identity(S.BRIEF_ID), held)

    def test_one_alias_cannot_be_claimed_by_two_briefs(self) -> None:
        store = registered("names.launch")
        with self.assertRaises(RefError) as caught:
            store.register(brief("brief.rival", aliases=("names.launch",)))
        self.assertIn("already registered", str(caught.exception))
        self.assertEqual(store.aliases_held_by("names.launch"), (S.BRIEF_ID,))
        self.assertIs(store.resolve("names.launch"), store.identity(S.BRIEF_ID))
        self.assertIsNone(store.resolve("brief.rival"))

    def test_a_tiny_store_refuses_instead_of_evicting(self) -> None:
        store = InMemoryBriefStore(capacity=2)
        store.register(brief("brief.one"))
        store.register(brief("brief.two"))
        with self.assertRaises(StoreConflictError) as caught:
            store.register(brief("brief.three"))
        self.assertIn("bounds growth rather than evicting", str(caught.exception))
        self.assertEqual(store.brief_ids(), ("brief.one", "brief.two"))

    def test_capacity_bounds_revisions_separately_from_identities(self) -> None:
        store = InMemoryBriefStore(capacity=2)
        store.register(brief())
        store.admit(numbered(1, ident="rev.1"))
        store.admit(numbered(2, ident="rev.2", predecessor="rev.1", ancestors=("rev.1",)))
        with self.assertRaises(StoreConflictError):
            store.admit(
                numbered(3, ident="rev.3", predecessor="rev.2", ancestors=("rev.1", "rev.2"))
            )
        self.assertEqual(len(store.brief_ids()), 1)

    def test_registration_accepts_a_payload_and_lookup_demands_a_real_id(self) -> None:
        store = InMemoryBriefStore()
        value = brief()
        self.assertEqual(store.register(value.to_payload()), value)
        with self.assertRaises(SchemaValidationError):
            store.identity("Iris launch")
        self.assertIsNone(store.identity("brief.never.held"))
        self.assertIsNone(store.revision("rev.never.held"))
        self.assertFalse(store.holds("rev.never.held"))

    def test_the_store_appends_and_never_deletes(self) -> None:
        for store in (InMemoryBriefStore(), InMemorySemanticStore()):
            with self.subTest(store=type(store).__name__):
                names = {name for name in dir(store) if not name.startswith("_")}
                self.assertEqual(names & DELETION_VOCABULARY, set())


class BriefStoreEnumerationTests(unittest.TestCase):
    def test_ids_are_listed_by_key_not_by_arrival(self) -> None:
        forward = InMemoryBriefStore()
        backward = InMemoryBriefStore()
        for store, item in (
            (forward, brief("brief.a")),
            (forward, brief("brief.b")),
            (backward, brief("brief.b")),
            (backward, brief("brief.a")),
        ):
            store.register(item)
        self.assertEqual(forward.brief_ids(), ("brief.a", "brief.b"))
        self.assertEqual(forward.brief_ids(), backward.brief_ids())
        self.assertEqual(forward.listing_digest(), backward.listing_digest())

    def test_revision_ids_ignore_arrival_order(self) -> None:
        store = InMemoryBriefStore()
        store.register(brief())
        store.admit(numbered(1, ident="rev.z"))
        store.admit(numbered(2, ident="rev.y", predecessor="rev.z", ancestors=("rev.z",)))
        self.assertEqual(store.revision_ids(), ("rev.y", "rev.z"))
        self.assertEqual(
            [item.revision_id for item in store.revisions_of(S.BRIEF_ID)], ["rev.z", "rev.y"]
        )
        self.assertEqual(
            [item.revision_number for item in store.revisions_of(S.BRIEF_ID)], [1, 2]
        )

    def test_revisions_of_a_brief_are_ordered_by_number_then_id(self) -> None:
        store = registered()
        self.assertEqual(
            [item.revision_id for item in store.revisions_of(S.BRIEF_ID)],
            ["rev.1", "rev.2", "rev.3"],
        )
        self.assertEqual(store.revisions_of("brief.never.held"), ())

    def test_admitted_revisions_separate_a_draft_from_history(self) -> None:
        store = InMemoryBriefStore()
        store.register(brief())
        store.admit(numbered(1, ident="rev.1"))
        draft = numbered(2, ident="rev.2", predecessor="rev.1", ancestors=("rev.1",), status="DRAFT")
        store.admit(draft)
        self.assertEqual(
            [item.revision_id for item in store.revisions_of(S.BRIEF_ID)], ["rev.1", "rev.2"]
        )
        self.assertEqual(
            [item.revision_id for item in store.admitted_revisions(S.BRIEF_ID)], ["rev.1"]
        )
        self.assertFalse(store.revision("rev.2").admitted)
        self.assertTrue(store.revision("rev.1").admitted)

    def test_missing_revisions_names_what_the_store_cannot_produce(self) -> None:
        store = registered()
        self.assertEqual(store.missing_revisions(["rev.9", "rev.2"]), ("rev.9",))
        self.assertEqual(store.missing_revisions([]), ())
        with self.assertRaises(SchemaValidationError):
            store.missing_revisions(["Rev 9"])

    def test_listing_digest_is_stable_and_moves_only_with_content(self) -> None:
        store = registered()
        before = store.listing_digest()
        self.assertEqual(before, store.listing_digest())
        store.admit(
            numbered(4, ident="rev.4", predecessor="rev.3", ancestors=("rev.1", "rev.2", "rev.3"))
        )
        self.assertNotEqual(before, store.listing_digest())

    def test_listing_digest_helper_reads_record_content_in_the_given_order(self) -> None:
        first, second = S.revision_chain((1, 2))
        self.assertEqual(listing_digest([first, second]), listing_digest([first, second]))
        self.assertNotEqual(listing_digest([first, second]), listing_digest([second, first]))
        self.assertNotEqual(listing_digest([first, second]), listing_digest([first]))
        self.assertEqual(len(listing_digest([])), S.DIGEST_LEN)

    def test_newest_is_a_lookup_and_never_a_claim_about_what_is_in_force(self) -> None:
        """Invariant 39: branch/variant/rollback topology stays with M02."""

        store = registered()
        self.assertEqual(store.newest(S.BRIEF_ID).revision_id, "rev.3")
        names = {name for name in dir(store) if not name.startswith("_")}
        self.assertEqual(
            names & {"head", "current", "in_force", "active", "promote", "rollback", "branch_of"}, set()
        )
        self.assertIsNone(store.newest("brief.never.held"))


class SemanticStoreTests(unittest.TestCase):
    def test_the_family_is_derived_from_the_record_type(self) -> None:
        store = InMemorySemanticStore()
        bundle = S.bundle([S.rule("cn.logo")])
        self.assertIs(store.put(bundle), bundle)
        self.assertIs(store.get(RecordFamily.CONSTRAINT_BUNDLE, "bundle.iris"), bundle)
        self.assertEqual(store.families_held(), ("CONSTRAINT_BUNDLE",))
        self.assertTrue(store.holds("constraint_bundle", "bundle.iris"))

    def test_a_caller_supplied_family_that_mismatches_is_refused(self) -> None:
        store = InMemorySemanticStore()
        bundle = S.bundle([S.rule("cn.logo")])
        with self.assertRaises(SchemaValidationError) as caught:
            store.put(bundle, family="INTENT_MODEL")
        self.assertIn("is a CONSTRAINT_BUNDLE, not INTENT_MODEL", str(caught.exception))
        self.assertEqual(store.size, 0)

    def test_a_matching_explicit_family_is_the_same_admission(self) -> None:
        store = InMemorySemanticStore()
        bundle = S.bundle([S.rule("cn.logo")])
        self.assertIs(store.put(bundle, family=RecordFamily.CONSTRAINT_BUNDLE), store.put(bundle))

    def test_counts_reports_every_family_including_the_empty_ones(self) -> None:
        store = InMemorySemanticStore()
        store.put(S.bundle([S.rule("cn.logo")]))
        counts = dict(store.counts())
        self.assertEqual(len(counts), len(RECORD_FAMILIES))
        self.assertEqual(counts["CONSTRAINT_BUNDLE"], 1)
        self.assertEqual(counts["READINESS_REPORT"], 0)
        self.assertEqual([name for name, _ in store.counts()], [item.value for item in RecordFamily])

    def test_enumeration_stays_key_ordered(self) -> None:
        store = InMemorySemanticStore()
        revision = S.revision(1, (S.statement("st.1", S.LOGO),), ident="rev.1")
        first = store.put(S.fingerprint(revision, ident="fp.a"))
        second = store.put(S.fingerprint(revision, ident="fp.b"))
        self.assertEqual(store.ids_of("INTENT_FINGERPRINT"), ("fp.a", "fp.b"))
        self.assertEqual(
            [item.fingerprint_id for item in store.of_family("INTENT_FINGERPRINT")], ["fp.a", "fp.b"]
        )
        self.assertEqual([item.fingerprint_id for item in store.records()], ["fp.a", "fp.b"])
        self.assertIs(store.of_family("INTENT_FINGERPRINT")[0], first)
        self.assertIs(store.of_family("INTENT_FINGERPRINT")[1], second)

    def test_one_id_under_two_families_stays_two_facts(self) -> None:
        store = InMemorySemanticStore()
        revision = S.admitted_revision()
        intent = store.put(S.fingerprint(revision, ident="shared"))
        constraint = store.put(
            S.bundle_fingerprint(S.bundle([S.rule("cn.logo")]), ident="shared")
        )
        self.assertEqual(store.size, 2)
        self.assertIs(store.get("INTENT_FINGERPRINT", "shared"), intent)
        self.assertIs(store.get("CONSTRAINT_FINGERPRINT", "shared"), constraint)
        self.assertEqual(store.missing("INTENT_FINGERPRINT", ["shared", "absent"]), ("absent",))

    def test_retry_is_not_an_event_and_a_rewrite_is(self) -> None:
        store = InMemorySemanticStore()
        value = S.equivalence_profile()
        again = S.SemanticEquivalenceProfile.from_payload(value.to_payload())
        self.assertIs(store.put(value), store.put(again))
        self.assertEqual(store.size, 1)
        with self.assertRaises(StoreConflictError):
            store.put(S.equivalence_profile(version="v2"))

    def test_a_bounded_store_refuses_rather_than_dropping_a_record(self) -> None:
        store = InMemorySemanticStore(capacity=2)
        store.put(S.question("q.1"))
        store.put(S.question("q.2"))
        with self.assertRaises(StoreConflictError):
            store.put(S.question("q.3"))
        self.assertEqual(store.ids_of("OPEN_QUESTION"), ("q.1", "q.2"))

    def test_an_unstoreable_object_or_family_never_enters(self) -> None:
        store = InMemorySemanticStore()
        with self.assertRaises(SchemaValidationError):
            store.put(SimpleNamespace(model_id="m.stranger"))
        with self.assertRaises(SchemaValidationError):
            store.get("NOT_A_FAMILY", "anything")
        self.assertEqual(store.size, 0)

    def test_the_reference_stores_satisfy_their_protocols_and_a_stub_does_not(self) -> None:
        self.assertIsInstance(InMemoryBriefStore(), BriefRepository)
        self.assertIsInstance(InMemorySemanticStore(), SemanticRepository)
        self.assertNotIsInstance(SimpleNamespace(put=lambda *a: None), SemanticRepository)
        self.assertNotIsInstance(SimpleNamespace(), BriefRepository)

    def test_two_stores_share_no_state(self) -> None:
        first = InMemorySemanticStore()
        second = InMemorySemanticStore()
        value = S.equivalence_profile()
        first.put(value)
        self.assertEqual(second.size, 0)
        self.assertIsNone(second.get("EQUIVALENCE_PROFILE", "profile.iris"))
        self.assertIs(first.get("EQUIVALENCE_PROFILE", "profile.iris"), value)


# --------------------------------------------------------------------------- #
# §13: the transport envelope
# --------------------------------------------------------------------------- #


class TransportRoundTripTests(unittest.TestCase):
    def inventory(self) -> dict[str, Any]:
        return record_inventory()

    def test_every_buildable_record_survives_serialize_and_deserialize(self) -> None:
        seen = self.inventory()
        self.assertGreaterEqual(len(seen), 30)
        for kind, record in sorted(seen.items()):
            with self.subTest(record=kind):
                self.assertEqual(record_kind(record), kind)
                payload = serialize(record)
                self.assertIsInstance(payload, dict)
                self.assertEqual(deserialize(payload), record)
                self.assertEqual(deserialize(envelope_for(record)), record)
                self.assertEqual(from_envelope(payload), record)

    def test_canonical_json_refuses_nonfinite_numbers(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(SchemaValidationError) as caught:
                    canonical_json({"number": value})
                self.assertIn("not canonical data", str(caught.exception))

    def test_dumps_is_canonical_json_and_loads_round_trips(self) -> None:
        for kind, record in sorted(self.inventory().items()):
            with self.subTest(record=kind):
                text = dumps(record)
                self.assertEqual(text, canonical_json(json.loads(text)))
                self.assertEqual(text, dumps(record))
                self.assertEqual(loads(text), record)

    def test_the_wire_bytes_and_the_quoted_digest_are_one_definition(self) -> None:
        for kind, record in sorted(self.inventory().items()):
            with self.subTest(record=kind):
                envelope = envelope_for(record)
                self.assertEqual(envelope.payload_digest, record.digest())
                self.assertEqual(envelope.digest(), content_digest(json.loads(dumps(record))))
                self.assertEqual(len(envelope.payload_digest), S.DIGEST_LEN)

    def test_an_envelope_is_itself_a_transportable_record(self) -> None:
        envelope = envelope_for(S.equivalence_profile())
        self.assertEqual(record_kind(envelope), "SerializationEnvelope")
        rebuilt = loads(dumps(envelope))
        self.assertIsInstance(rebuilt, SerializationEnvelope)
        self.assertEqual(rebuilt, envelope)
        self.assertEqual(rebuilt.decode(), envelope.decode())

    def test_a_record_is_never_mistaken_for_a_document(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            deserialize(S.equivalence_profile())
        self.assertIn("already a record", str(caught.exception))

    def test_compiled_records_carry_the_frozen_contract_version(self) -> None:
        """Invariant 43: what leaves the kernel says which contract admitted it."""

        pinned = {
            kind: record
            for kind, record in self.inventory().items()
            if getattr(record, "contract_version", None) is not None
        }
        for kind in (
            "SemanticIntentFingerprint",
            "MinimumSufficientSemanticSlice",
            "ExecutionIntentBundle",
            "ReusePassport",
            "ExtensionObservation",
            "SerializationEnvelope",
        ):
            self.assertIn(kind, pinned)
        for kind, record in sorted(pinned.items()):
            with self.subTest(record=kind):
                self.assertEqual(record.contract_version, CONTRACT_VERSION)

    def test_every_envelope_names_the_record_it_carries(self) -> None:
        for kind, record in sorted(self.inventory().items()):
            with self.subTest(record=kind):
                envelope = envelope_for(record)
                self.assertEqual(envelope.kind, kind)
                self.assertIs(envelope.record_type, type(record))
                self.assertEqual(envelope.schema_version, SCHEMA_VERSION)


class EnvelopeRefusalTests(unittest.TestCase):
    def envelope(self) -> SerializationEnvelope:
        return envelope_for(S.bundle([S.rule("cn.logo")]))

    def test_a_tampered_payload_is_refused_by_its_own_digest(self) -> None:
        held = self.envelope()
        tampered = {**held.to_payload(), "payload": {**held.payload, "version": "v2"}}
        with self.assertRaises(SchemaValidationError) as caught:
            SerializationEnvelope(**tampered)
        self.assertIn("hashes to", str(caught.exception))

    def test_a_truncated_payload_is_refused_even_with_an_honest_digest(self) -> None:
        held = self.envelope()
        short = {key: value for key, value in held.payload.items() if key != "constraints"}
        honest = {**held.to_payload(), "payload": short, "payload_digest": content_digest(short)}
        with self.assertRaises(SchemaValidationError) as caught:
            SerializationEnvelope(**honest)
        self.assertIn("missing keys", str(caught.exception))

    def test_an_unknown_kind_is_refused_by_name(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            require_record_kind("M02_SNAPSHOT", "kind")
        self.assertIn("is not an M03 record kind", str(caught.exception))
        held = self.envelope()
        with self.assertRaises(SchemaValidationError):
            SerializationEnvelope(**{**held.to_payload(), "kind": "IntentModel2"})
        self.assertEqual(require_record_kind("ConstraintBundle"), "ConstraintBundle")

    def test_an_unsupported_schema_version_is_unsupported_not_invalid(self) -> None:
        held = self.envelope()
        with self.assertRaises(UnsupportedVersionError) as caught:
            SerializationEnvelope(**{**held.to_payload(), "schema_version": "iris-intent-schema-v2"})
        self.assertIn("unsupported schema version", str(caught.exception))

    def test_an_unsupported_contract_version_is_unsupported_not_invalid(self) -> None:
        held = self.envelope()
        with self.assertRaises(UnsupportedVersionError) as caught:
            SerializationEnvelope(**{**held.to_payload(), "contract_version": "m03-contract-v9.9"})
        self.assertIn("unsupported contract version", str(caught.exception))
        profile = S.equivalence_profile()
        with self.assertRaises(UnsupportedVersionError):
            SerializationEnvelope(
                schema_version=SCHEMA_VERSION,
                kind="SemanticEquivalenceProfile",
                contract_version="m02-contract-v1.0",
                payload=profile.to_payload(),
                payload_digest=profile.digest(),
            )

    def test_an_envelope_cannot_be_built_around_a_payload_its_kind_rejects(self) -> None:
        wrong = S.model(S.admitted_revision()).to_payload()
        with self.assertRaises(SchemaValidationError) as caught:
            SerializationEnvelope(
                schema_version=SCHEMA_VERSION,
                kind="ConstraintBundle",
                contract_version=CONTRACT_VERSION,
                payload=wrong,
                payload_digest=content_digest(wrong),
            )
        self.assertIn("unknown keys", str(caught.exception))

    def test_a_payload_that_is_not_a_mapping_is_refused(self) -> None:
        listed = [S.bundle([S.rule("cn.logo")]).to_payload()]
        with self.assertRaises(SchemaValidationError) as caught:
            SerializationEnvelope(
                schema_version=SCHEMA_VERSION,
                kind="ConstraintBundle",
                contract_version=CONTRACT_VERSION,
                payload=listed,
                payload_digest=content_digest(listed),
            )
        self.assertIn("must be a mapping of record fields", str(caught.exception))

    def test_a_payload_that_cannot_be_canonically_hashed_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            SerializationEnvelope(
                schema_version=SCHEMA_VERSION,
                kind="SemanticEquivalenceProfile",
                contract_version=CONTRACT_VERSION,
                payload={"unencodable": {1, 2}},
                payload_digest=content_digest("anything"),
            )
        self.assertIn("not canonical data", str(caught.exception))

    def test_a_digest_that_is_not_hex_is_refused(self) -> None:
        held = self.envelope()
        with self.assertRaises(SchemaValidationError):
            SerializationEnvelope(**{**held.to_payload(), "payload_digest": "zz" * 32})

    def test_loads_refuses_anything_that_is_not_an_envelope(self) -> None:
        for text in ("", "not json", "[]", "3", '"bundle.iris"', "{}"):
            with self.subTest(text=text):
                with self.assertRaises(SchemaValidationError):
                    loads(text)
        with self.assertRaises(SchemaValidationError):
            loads(None)
        with self.assertRaises(SchemaValidationError):
            loads({"kind": "ConstraintBundle"})

    def test_every_refusal_stays_inside_the_kernel_error_surface(self) -> None:
        held = self.envelope()
        attempts = (
            lambda: SerializationEnvelope(**{**held.to_payload(), "payload": {"a": 1}}),
            lambda: require_record_kind(7, "kind"),
            lambda: record_kind(SimpleNamespace()),
            lambda: loads(dumps(held)[: -4]),
            lambda: deserialize([1, 2]),
        )
        for attempt in attempts:
            with self.assertRaises(IntentKernelError):
                attempt()


class RecordKindCoverageTests(unittest.TestCase):
    def scanned(self) -> dict[str, type[Record]]:
        """An independent scan: every Record subclass the package defines, wherever it lives."""

        found: dict[str, type[Record]] = {}
        for info in pkgutil.iter_modules(iris_intent.__path__):
            module = importlib.import_module(f"iris_intent.{info.name}")
            for name, member in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(member, Record)
                    and member is not Record
                    and member.__module__ == module.__name__
                ):
                    found[name] = member
        return found

    def test_no_record_the_package_defines_is_missing_from_the_kind_map(self) -> None:
        scanned = self.scanned()
        self.assertTrue(scanned)
        self.assertEqual(sorted(set(scanned) - set(record_kinds())), [])
        self.assertEqual(set(scanned), set(record_kinds()))
        for name, member in sorted(scanned.items()):
            with self.subTest(record=name):
                self.assertIs(record_types()[name], member)

    def test_the_kind_map_is_sorted_read_only_and_unduplicated(self) -> None:
        kinds = record_kinds()
        self.assertEqual(kinds, tuple(sorted(kinds)))
        self.assertEqual(len(kinds), len(set(kinds)))
        self.assertEqual(len(kinds), len(record_types()))
        self.assertIsInstance(record_types(), MappingProxyType)
        with self.assertRaises(TypeError):
            record_types()["ConstraintBundle"] = dict  # type: ignore[index]

    def test_every_storable_family_can_also_travel(self) -> None:
        kinds = set(record_kinds())
        for item in RECORD_FAMILIES:
            with self.subTest(family=item.value):
                self.assertIn(item.record_type.__name__, kinds)

    def test_the_serializer_catalogues_its_own_envelope(self) -> None:
        self.assertIn("SerializationEnvelope", record_kinds())

    def test_a_record_defined_outside_the_package_has_no_kind(self) -> None:
        outsider = type("OutsiderRecord", (Record,), {"__annotations__": {"outsider_id": str}})
        with self.assertRaises(SchemaValidationError):
            record_kind(outsider())
        with self.assertRaises(SchemaValidationError):
            require_record_kind("OutsiderRecord")


# --------------------------------------------------------------------------- #
# §12 / §14: opaque refs and extension boundaries
# --------------------------------------------------------------------------- #


class OpaqueRefBoundaryTests(unittest.TestCase):
    def neighbour_owned_kinds(self) -> frozenset[str]:
        return frozenset(
            item.value for item in RefKind if item.value.startswith(("M01_", "M02_"))
        )

    def constructed_ref_kinds(self) -> list[tuple[str, str, str]]:
        """Every (module, RefKind used, ref_id shape) the kernel builds a SemanticRef with."""

        found: list[tuple[str, str, str]] = []
        for path in sorted(KERNEL.glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not isinstance(node, ast.Call):
                    continue
                target = node.func
                name = target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")
                if name != "SemanticRef":
                    continue
                keywords = {item.arg: item.value for item in node.keywords if item.arg}
                kind = keywords.get("kind")
                if not (
                    isinstance(kind, ast.Attribute)
                    and kind.attr == "value"
                    and isinstance(kind.value, ast.Attribute)
                    and isinstance(kind.value.value, ast.Name)
                    and kind.value.value.id == "RefKind"
                ):
                    continue
                ref_id = keywords.get("ref_id")
                found.append((path.name, kind.value.attr, type(ref_id).__name__))
        return found

    def test_a_versioned_kind_cannot_be_cited_without_a_pin(self) -> None:
        self.assertTrue(VERSIONED_REF_KINDS)
        for item in sorted(VERSIONED_REF_KINDS, key=lambda one: one.value):
            with self.subTest(kind=item.value):
                with self.assertRaises(RefError) as caught:
                    SemanticRef(kind=item.value, ref_id="unpinned.thing")
                self.assertIn("pin the version", str(caught.exception))
                pinned = SemanticRef(kind=item.value, ref_id="pinned.thing", version="v3")
                self.assertFalse(pinned.unversioned)
                self.assertTrue(pinned.pinned)

    def test_a_kind_that_changes_only_with_its_bytes_needs_no_pin(self) -> None:
        loose = SemanticRef(kind=RefKind.BRIEF.value, ref_id=S.BRIEF_ID)
        self.assertTrue(loose.unversioned)
        self.assertFalse(loose.pinned)
        bound = loose.with_digest(S.digest("x"))
        self.assertTrue(bound.pinned)
        self.assertEqual(bound.text, f"{loose.text}@{S.digest('x')}")

        # Exact-content identity must never collapse merely because two digests share a prefix.
        prefix = "0123456789abcdef"
        first = SemanticRef(kind=RefKind.SOURCE.value, ref_id="src.same", content_digest=prefix + "0" * 48)
        second = SemanticRef(kind=RefKind.SOURCE.value, ref_id="src.same", content_digest=prefix + "f" * 48)
        self.assertNotEqual(first.text, second.text)
        self.assertNotEqual(first.text.split("@")[-1], second.text.split("@")[-1])

    def test_malformed_ref_ids_are_refused(self) -> None:
        for ident in ("", "   ", "Brief.Launch", "two words", "a<b", "a|b", "x" * 129):
            with self.subTest(ref_id=ident):
                with self.assertRaises(SchemaValidationError):
                    SemanticRef(kind=RefKind.SOURCE.value, ref_id=ident)
        with self.assertRaises(SchemaValidationError):
            SemanticRef(kind="HIVE_WORKSPACE", ref_id="workspace.iris")
        with self.assertRaises(SchemaValidationError):
            SemanticRef(kind=RefKind.SOURCE.value, ref_id="src.1", content_digest="zz" * 32)
        with self.assertRaises(SchemaValidationError):
            SemanticRef(kind=RefKind.SOURCE.value, ref_id="src.1", version="   ")

    def test_m03_never_mints_a_ref_into_a_neighbours_namespace(self) -> None:
        """Invariants 39 and 40: M01/M02 namespaces are cited, never populated by M03."""

        owned = self.neighbour_owned_kinds()
        self.assertTrue(owned)
        constructions = self.constructed_ref_kinds()
        minted = {kind for _, kind, _ in constructions}
        self.assertTrue(minted)
        self.assertEqual(minted & {item for item in owned if item.startswith("M02_")}, set())
        for module, kind, ref_id_shape in constructions:
            with self.subTest(module=module, kind=kind):
                if kind in owned:
                    self.assertEqual(
                        ref_id_shape,
                        "Attribute",
                        f"{module} invents a {kind} id instead of reading it off the neighbour's record",
                    )

    def test_the_kernel_never_mints_an_identifier_it_cannot_replay(self) -> None:
        callers = set()
        for path in sorted(KERNEL.glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call):
                    target = node.func
                    name = target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")
                    if name == "mint_id":
                        callers.add(path.name)
        self.assertEqual(callers, set())

    def test_an_admitted_ref_cannot_be_rebound_to_other_bytes(self) -> None:
        bound = S.ref(RefKind.SOURCE.value, "src.brief")
        self.assertEqual(bound.bind(S.digest("src.brief"), "v1").content_digest, bound.content_digest)
        with self.assertRaises(RefError) as caught:
            bound.bind(S.digest("something else"), "v1")
        self.assertIn("already bound", str(caught.exception))

    def test_a_brief_refuses_a_project_ref_of_the_wrong_kind(self) -> None:
        right = S.ref(RefKind.M02_PROJECT.value, "project.iris", "1.0.0")
        bound = CreativeBriefIdentity(brief_id="brief.bound", label="Iris launch", project_ref=right)
        self.assertEqual(bound.project_ref, right)
        self.assertEqual(bound.references, (right,))
        with self.assertRaises(RefError) as caught:
            CreativeBriefIdentity(
                brief_id="brief.bound",
                label="Iris launch",
                project_ref=S.ref(RefKind.M02_BRANCH.value, "branch.main"),
            )
        self.assertIn("claim the wrong scope", str(caught.exception))
        self.assertEqual(CreativeBriefIdentity(brief_id="brief.plain", label="Iris").references, ())

    def test_hive_memory_is_derived_context_and_cannot_self_promote(self) -> None:
        """Invariant 40: HIVE is input, never canonical intent state."""

        self.assertIn(SourceKind.HIVE_MEMORY, UNTRUSTED_SOURCES)
        self.assertTrue(is_untrusted(SourceKind.HIVE_MEMORY.value))
        self.assertIs(ceiling_for(SourceKind.HIVE_MEMORY.value), AuthorityLevel.RETRIEVED)

        def remembered(kind: str, authority: str) -> RawInputRef:
            return RawInputRef(
                source_id="src.hive",
                kind=kind,
                authority=authority,
                content_digest=S.digest("src.hive"),
            )

        allowed = remembered(SourceKind.HIVE_MEMORY.value, AuthorityLevel.RETRIEVED.value)
        self.assertTrue(allowed.untrusted)
        self.assertIs(allowed.authority_level, AuthorityLevel.RETRIEVED)
        with self.assertRaises(AuthorityError) as caught:
            remembered(SourceKind.HIVE_MEMORY.value, AuthorityLevel.HUMAN_OWNER.value)
        self.assertIn("Raising it takes an admitted revision", str(caught.exception))
        self.assertIs(ceiling_for(SourceKind.MODEL_OUTPUT.value), AuthorityLevel.MODEL_INFERRED)
        with self.assertRaises(AuthorityError):
            remembered(SourceKind.MODEL_OUTPUT.value, AuthorityLevel.PROJECT_RECORD.value)
        self.assertIs(ceiling_for(SourceKind.PROVIDER_RESULT.value), AuthorityLevel.PROVIDER_OBSERVED)
        with self.assertRaises(AuthorityError):
            remembered(SourceKind.PROVIDER_RESULT.value, AuthorityLevel.TEAM_ASSERTED.value)
        self.assertFalse(is_untrusted(SourceKind.HUMAN_MESSAGE.value))
        self.assertIs(ceiling_for(SourceKind.HUMAN_MESSAGE.value), AuthorityLevel.HUMAN_OWNER)

    def test_a_provider_observation_cannot_carry_the_brief_itself(self) -> None:
        """Invariant 42: results report; only an admitted revision mutates."""

        for key in sorted(CANONICAL_MUTATION_KEYS):
            with self.subTest(key=key):
                with self.assertRaises(UntrustedExtensionError) as caught:
                    observation(facts={key: "whatever the provider believes"})
                self.assertIn("cannot carry the brief itself", str(caught.exception))
        clean = observation()
        self.assertEqual(clean.answer("carrier"), "m04-scene-ir")
        self.assertTrue(clean.complete)
        with self.assertRaises(PortContractError):
            clean.answer("absent")

    def test_an_observation_about_another_providers_handle_is_refused(self) -> None:
        with self.assertRaises(RefError):
            observation(about=extension_ref(provider="someone.else"))
        with self.assertRaises(RefError):
            observation(boundary="PROJECT_GRAPH")
        with self.assertRaises(SchemaValidationError):
            observation(facts={"carrier": {"nested": "payload"}})


class ExtensionPortBoundaryTests(unittest.TestCase):
    def test_the_twelve_boundaries_are_the_contracts_list_and_nobody_else(self) -> None:
        self.assertEqual({item.value for item in PORT_BOUNDARIES}, set(CONTRACT_BOUNDARIES))
        self.assertEqual(set(PORT_PROTOCOLS), set(PORT_BOUNDARIES))
        self.assertEqual(len(PORT_BOUNDARIES), 12)
        kinds = {member.value for member in RefKind}
        for item in PORT_BOUNDARIES:
            with self.subTest(boundary=item.value):
                self.assertNotIn("M03", item.resolves_in)
                self.assertTrue(item.speaks_for)
                self.assertIsInstance(item.ref_kinds, frozenset)
                self.assertTrue(item.ref_kinds)
                self.assertTrue(item.ref_kinds <= kinds)
                for kind in item.ref_kinds:
                    self.assertIn(item, boundaries_admitting(kind))
                methods = PORT_PROTOCOLS[item]
                self.assertEqual(len(set(methods)), len(methods))

    def test_a_ref_may_only_cross_the_boundary_that_speaks_its_kind(self) -> None:
        branch = S.ref(RefKind.M02_BRANCH.value, "branch.exploration")
        self.assertTrue(ExtensionBoundary.PROJECT_GRAPH.admits(branch))
        self.assertFalse(ExtensionBoundary.QUALITY_PROFILE.admits(branch))
        self.assertIn(
            ExtensionBoundary.SEMANTIC_TYPE, boundaries_admitting(RefKind.SEMANTIC_TYPE.value)
        )
        self.assertEqual(
            boundaries_admitting(RefKind.M02_BRANCH.value), (ExtensionBoundary.PROJECT_GRAPH,)
        )
        with self.assertRaises(RefError):
            ExtensionRef(boundary="QUALITY_PROFILE", reference=semantic_type_ref())

    def test_an_unbound_citation_is_not_evidence(self) -> None:
        unpinned = SemanticRef(kind=RefKind.SEMANTIC_TYPE.value, ref_id="type.iso", version="v1")
        with self.assertRaises(RefError):
            ExtensionRef(boundary="SEMANTIC_TYPE", reference=unpinned)

    def test_ports_are_wired_by_argument_and_never_globally(self) -> None:
        wiring = ExtensionPorts()
        self.assertEqual(wiring.missing, tuple(item.value for item in PORT_BOUNDARIES))
        self.assertEqual(wiring.wired, ())
        stub = VocabularyStub(vocabulary_provider())
        wiring.attach("SEMANTIC_TYPE", stub)
        self.assertEqual(wiring.wired, ("SEMANTIC_TYPE",))
        with self.assertRaises(PortContractError):
            wiring.require("PROJECT_GRAPH")
        with self.assertRaises(PortContractError):
            wiring.attach("SEMANTIC_TYPE", stub)
        grown = wiring.extended(
            DOMAIN_VOCABULARY=DomainVocabularyStub(
                vocabulary_provider(provider_id="domain.registry", boundaries=("DOMAIN_VOCABULARY",))
            )
        )
        self.assertEqual(wiring.wired, ("SEMANTIC_TYPE",))
        self.assertEqual(grown.wired, ("DOMAIN_VOCABULARY", "SEMANTIC_TYPE"))
        self.assertEqual(len(grown.missing), 10)
        self.assertEqual(len(wiring.missing), 11)

    def test_a_provider_is_checked_against_what_it_admits_and_what_it_can_do(self) -> None:
        descriptor = vocabulary_provider()
        self.assertIs(require_port(VocabularyStub(descriptor), "SEMANTIC_TYPE"), descriptor)
        with self.assertRaises(PortContractError):
            require_port(VocabularyStub(descriptor), "QUALITY_PROFILE")
        with self.assertRaises(PortContractError):
            require_port(HalfPortStub(descriptor), "SEMANTIC_TYPE")
        with self.assertRaises(PortContractError):
            require_port(None, "SEMANTIC_TYPE")
        with self.assertRaises(PortContractError):
            require_port(object(), "SEMANTIC_TYPE")
        with self.assertRaises(PortContractError):
            require_port(VocabularyStub(descriptor), "SEMANTIC_TYPE", capability="reads_pixels")
        self.assertTrue(descriptor.may_speak_about(extension_ref()))

    def test_a_citation_without_a_provider_is_not_an_answer(self) -> None:
        bare = extension_ref(provider=None)
        with self.assertRaises(PortContractError) as unasked:
            bare.require_resolvable("resolve the semantic type")
        self.assertIn("carries no provider", str(unasked.exception))
        answered = require_answered_ref(
            extension_ref(), "SEMANTIC_TYPE", VocabularyStub(vocabulary_provider())
        )
        self.assertEqual(answered.text, bare.text)
        self.assertEqual(answered.provider_id, "m04.ir")
        with self.assertRaises(PortContractError) as caught:
            require_answered_ref(bare, "SEMANTIC_TYPE", VocabularyStub(vocabulary_provider()))
        self.assertIn("carries no provider", str(caught.exception))
        with self.assertRaises(RefError):
            require_answered_ref(extension_ref(), "CANON_STORY", VocabularyStub(vocabulary_provider()))
        with self.assertRaises(RefError) as hijacked:
            require_answered_ref(
                ExtensionRef.from_payload({**answered.to_payload(), "provider_id": "somewhere.else"}),
                "SEMANTIC_TYPE",
                VocabularyStub(vocabulary_provider()),
            )
        self.assertIn("belongs to the provider that issued it", str(hijacked.exception))

    def test_domain_semantics_enter_through_a_versioned_registry_that_cannot_be_edited_in_place(
        self,
    ) -> None:
        core = PredicateRegistry()
        core.register(S.signature("shows_logo", trust="CORE"))
        grown = core.extended(
            [S.signature("iso_projection", path="iso.projection", version="v2", trust="QUALIFIED")]
        )
        self.assertEqual(core.predicate_ids, ("shows_logo",))
        self.assertEqual(grown.predicate_ids, ("iso_projection", "shows_logo"))
        self.assertIsNone(core.get("iso_projection", "v2"))
        self.assertTrue(
            grown.is_admitted(
                PredicateCall(predicate_id="iso_projection", version="v2", arguments={})
            )
        )
        self.assertFalse(
            core.is_admitted(PredicateCall(predicate_id="iso_projection", version="v2", arguments={}))
        )
        with self.assertRaises(UntrustedExtensionError):
            grown.register(
                S.signature("iso_projection", path="iso.projection", version="v2", trust="CORE")
            )
        with self.assertRaises(PredicateError):
            core.require(
                PredicateCall(predicate_id="iso_projection", version="v2", arguments={}, mandatory=True)
            )


# --------------------------------------------------------------------------- #
# §15 token economy, §17 side effects, and the package surface
# --------------------------------------------------------------------------- #


class TokenEconomyTests(unittest.TestCase):
    def test_a_localized_slice_carries_only_what_it_was_asked_for(self) -> None:
        revision = wide_revision()
        model = S.model(revision)
        slice_item = S.slice_for(model, None, paths=("visual.logo.clearspace",))
        self.assertEqual(slice_item.paths, ("visual.logo.clearspace",))
        self.assertEqual([item.statement_id for item in slice_item.statements], ["st.0"])
        self.assertLess(
            structural_footprint(slice_item.to_payload()),
            structural_footprint(model.to_payload()),
        )
        self.assertEqual(len(slice_item.excluded_statement_ids), 3)

    def test_a_fingerprint_quotes_a_whole_revision_in_one_digest(self) -> None:
        fingerprint = S.fingerprint(wide_revision(), ident="fp.wide")
        self.assertIsInstance(fingerprint, SemanticIntentFingerprint)
        self.assertEqual(len(fingerprint.semantic_digest), S.DIGEST_LEN)
        self.assertEqual(len(fingerprint.path_digests), 4)
        self.assertEqual(fingerprint.statement_count, 4)
        self.assertEqual(fingerprint.modalities, ("AUDIO", "IMAGE", "TEXT"))
        self.assertEqual(listing_digest([fingerprint]), listing_digest([fingerprint]))
        self.assertNotEqual(
            listing_digest([fingerprint]), listing_digest([S.fingerprint(wide_revision(), ident="fp.other")])
        )

    def test_a_store_listing_is_quotable_by_one_digest(self) -> None:
        store = registered()
        rows = [*store.identities(), *(store.revision(item) for item in store.revision_ids())]
        self.assertEqual(len(rows), 4)
        self.assertEqual(store.listing_digest(), listing_digest(rows))
        self.assertEqual(len(store.listing_digest()), S.DIGEST_LEN)
        self.assertEqual(store.listing_digest(), listing_digest(rows))


class SideEffectAuthorizationTests(unittest.TestCase):
    def test_a_publication_desire_records_a_gap_not_a_permission(self) -> None:
        """Invariant 41: §13's side-effect classes are M03's vocabulary, M02/M59's authority."""

        self.assertTrue(SideEffectClass.EXTERNAL_PUBLICATION.requires_governed_approval)
        self.assertTrue(SideEffectClass.CONTROLLED_EXPORT.leaves_the_system)
        self.assertFalse(SideEffectClass.INTERNAL_MATERIALIZATION.leaves_the_system)
        revision = S.admitted_revision()
        operation = producing_operation(
            revision, side_effect_class=SideEffectClass.EXTERNAL_PUBLICATION.value
        )
        self.assertTrue(operation.needs_approval_boundary)
        refused = compiled_execution("xb.publish", operations=(operation,))
        self.assertEqual(
            [item.class_name for item in refused.gaps],
            [ExecutionGapClass.SIDE_EFFECT_POLICY_UNRESOLVED.value],
        )
        self.assertEqual(refused.status, ExecutionIntentStatus.INCOMPLETE.value)
        approved = compiled_execution(
            "xb.publish.approved",
            operations=(operation,),
            side_effect_policy_ref=S.ref(RefKind.POLICY.value, "policy.side_effects"),
        )
        self.assertEqual([item.class_name for item in approved.gaps], [])
        self.assertEqual(approved.status, ExecutionIntentStatus.COMPLETE.value)
        self.assertEqual(
            approved.side_effect_policy_ref.kind, RefKind.POLICY.value
        )

    def test_an_explicit_approval_ref_replaces_the_gap_but_not_the_authority(self) -> None:
        revision = S.admitted_revision()
        approval = S.ref(RefKind.RECEIPT.value, "ovr.publish")
        operation = producing_operation(
            revision,
            side_effect_class=SideEffectClass.EXTERNAL_PUBLICATION.value,
            approval_boundary_ref=approval,
        )
        self.assertFalse(operation.needs_approval_boundary)
        compiled = compiled_execution("xb.approved.op", operations=(operation,))
        self.assertEqual([item.class_name for item in compiled.gaps], [])
        self.assertIs(compiled.operations[0].approval_boundary_ref, approval)


class PackageSurfaceTests(unittest.TestCase):
    def test_the_public_surface_is_derived_sorted_and_resolves(self) -> None:
        surface = iris_intent.__all__
        self.assertGreater(len(surface), 300)
        self.assertEqual(surface[-1], "__version__")
        self.assertEqual(surface[:-1], sorted(surface[:-1]))
        self.assertEqual(len(surface), len(set(surface)))
        for name in surface:
            with self.subTest(symbol=name):
                self.assertTrue(hasattr(iris_intent, name), f"{name} is promised but absent")
        self.assertEqual(iris_intent.__version__, "0.1.0")
        self.assertIn("SerializationEnvelope", surface)
        self.assertIn("InMemorySemanticStore", surface)

    def test_the_package_borrows_quality_vocabulary_by_object_identity(self) -> None:
        from iris_quality.contracts import QualityClass as Foreign
        from iris_quality.versions import ComponentVersion as ForeignComponent

        self.assertIs(Foreign, iris_intent.QualityClass)
        self.assertIs(ForeignComponent, iris_intent.ComponentVersion)

    def test_importing_the_kernel_creates_no_global_store_or_registry(self) -> None:
        singletons = (InMemoryBriefStore, InMemorySemanticStore, ExtensionPorts, PredicateRegistry)
        modules = [iris_intent] + [
            importlib.import_module(f"iris_intent.{info.name}")
            for info in pkgutil.iter_modules(iris_intent.__path__)
        ]
        for module in modules:
            for name, value in vars(module).items():
                with self.subTest(module=module.__name__, symbol=name):
                    self.assertNotIsInstance(
                        value, singletons, f"{module.__name__}.{name} is a global mutable authority"
                    )

    def test_module_level_registries_are_frozen_lookups(self) -> None:
        from iris_intent import identity, stores, versions

        for label, value in (
            ("identity.VERSIONED_REF_KINDS", identity.VERSIONED_REF_KINDS),
            ("identity.UNTRUSTED_SOURCES", identity.UNTRUSTED_SOURCES),
            ("stores.RECORD_FAMILIES", stores.RECORD_FAMILIES),
            ("stores._FAMILY_TYPES", stores._FAMILY_TYPES),
            ("stores._FAMILY_ID_FIELDS", stores._FAMILY_ID_FIELDS),
            ("stores._FAMILIES_BY_TYPE", stores._FAMILIES_BY_TYPE),
            ("versions.SUPPORTED_CONTRACT_VERSIONS", versions.SUPPORTED_CONTRACT_VERSIONS),
            ("versions.HEX_DIGEST_LENGTHS", versions.HEX_DIGEST_LENGTHS),
        ):
            with self.subTest(lookup=label):
                self.assertIsInstance(value, (frozenset, tuple, MappingProxyType))
        self.assertEqual(versions.SUPPORTED_CONTRACT_VERSIONS, frozenset({CONTRACT_VERSION}))
        self.assertEqual(versions.SUPPORTED_SCHEMA_VERSIONS, frozenset({SCHEMA_VERSION}))

    def test_static_semantic_law_tables_are_read_only(self) -> None:
        """Core classification and mapping law cannot drift by mutating imported tables."""

        from iris_intent import ambiguity, conflicts, constraints, execution, explanation, fidelity, freshness, readiness

        protected = (
            ambiguity._CONSEQUENCE_RANKS,
            conflicts._CONSEQUENCE_RANK,
            conflicts._CONSEQUENCE_SEVERITY,
            conflicts._CLASS_CONSEQUENCE,
            conflicts._CLASS_RESOLUTIONS,
            constraints._POLARITY_STRICTNESS,
            constraints._STRENGTH_RANKS,
            constraints.UNIT_ALIASES,
            constraints._IDENTITY_FIELDS,
            execution._DELTA_ADDED_REMOVED,
            execution._DELTA_VIEW_DEFAULTS,
            execution._DELTA_FIELD_CLASSES,
            explanation._ENTRY_FIELDS_BY_LEVEL,
            explanation.ROOT_CLASSIFICATION,
            explanation._NARRATIVE,
            fidelity._OBLIGATION_DIMENSIONS,
            freshness._DIMENSION_SCOPES,
            freshness._EVIDENCE_BASES,
            freshness._STATE_RANKS,
            freshness._EVIDENCE_STATES,
            readiness._FAMILY_ORDER,
        )
        for table in protected:
            with self.subTest(table=repr(table)[:80]):
                self.assertIsInstance(table, MappingProxyType)
                with self.assertRaises(TypeError):
                    table[next(iter(table))] = object()

    def test_authority_and_boundary_policy_lookups_are_read_only(self) -> None:
        """Permission semantics cannot drift because a caller mutates an imported module constant."""

        from iris_intent import authority, identity, intent, overrides, ports

        protected = (
            identity._AUTHORITY_RANKS,
            identity._SOURCE_CEILINGS,
            intent._ORIGIN_CEILINGS,
            intent._ORIGIN_FLOORS,
            authority._ACTION_FLOORS,
            authority._BOUNDARY_OWNERS,
            authority._RESERVED_DEFAULT_RULE_CLASSES,
            ports._BOUNDARY_KINDS,
            ports._BOUNDARY_CLAIMS,
            ports._BOUNDARY_OWNERS,
            overrides._ACTION_MOVEMENTS,
        )
        for table in protected:
            with self.subTest(table=repr(table)[:80]):
                self.assertIsInstance(table, MappingProxyType)
                with self.assertRaises(TypeError):
                    table[next(iter(table))] = object()

    def test_the_port_contract_tables_are_read_only(self) -> None:
        """The twelve extension contracts are frozen lookup data, never runtime authority state."""

        from iris_intent import ports

        self.assertIsInstance(ports.PORT_PROTOCOLS, MappingProxyType)
        self.assertIsInstance(ports._PORT_SHAPES, MappingProxyType)
        for boundary, methods in ports.PORT_PROTOCOLS.items():
            with self.subTest(boundary=boundary.value):
                self.assertIsInstance(methods, tuple)
                self.assertEqual(ports._PORT_SHAPES[boundary][1], methods)
        with self.assertRaises(TypeError):
            ports.PORT_PROTOCOLS[ExtensionBoundary.SEMANTIC_TYPE] = ("invented",)
        with self.assertRaises(TypeError):
            ports._PORT_SHAPES[ExtensionBoundary.SEMANTIC_TYPE] = (object, ("invented",))

    def test_a_modality_is_declared_never_assumed(self) -> None:
        """§6: the channel alphabet is open vocabulary a statement cites, with no visual default."""

        self.assertEqual(
            ModalChannel.members(),
            ["AUDIO", "BRAND", "CROSS", "GEOMETRY", "IMAGE", "INTERFACE", "MATERIAL", "MOTION", "MUSIC", "SPEECH", "TEXT", "UNSPECIFIED", "VIDEO"],
        )
        self.assertEqual(S.statement("st.plain").modality, ModalChannel.UNSPECIFIED.value)
        self.assertIs(ModalChannel.parse("music"), ModalChannel.MUSIC)
        with self.assertRaises(SchemaValidationError):
            ModalChannel.parse("holodeck")


if __name__ == "__main__":
    unittest.main()
