"""M02 area D (reuse): cache layers, reuse classes and the admission shield.

A cache hit is a claim, not a fact. Somebody, somewhere, once produced bytes that
looked like this node's output under *their* inputs, *their* producer version and
*their* rights situation. The kernel's job is to decide whether that claim still
describes the current production, and to say which of its checks refused when it
does not.

Three rules shape the module. Reuse class is never inferred from the mere existence
of a key: an entry carries the writer's claim and ``admit_reuse`` re-derives the
truth. Runtime warm state is a different kind of thing from a production result, so
the layers refuse to be conflated at construction time. And read trust is not write
trust: a local experiment may look at the shared cache long before it may add to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from iris_quality.contracts import QualityClass

from .analysis import FingerprintComponent
from .base import Labeled, Record
from .errors import BuildError, SchemaValidationError
from .identity import EntityKind, ExternalRef, new_id, require_id
from .limits import (
    MAX_CLOSURE_REFS,
    MAX_CONTEXT_SOURCES,
    MAX_FACETS,
    MAX_SCHEMA_REFS,
)
from .snapshots import RetentionReason
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    content_digest,
    require_bounded,
    require_component_version,
    require_digest,
    require_identifier,
    require_millis,
    require_optional_text,
    require_quality_class,
    require_supported_version,
    require_text,
)

__all__ = [
    "CACHE_KEY_SCHEMA",
    "CONTEXT_FINGERPRINT_SCHEMA",
    "QUARANTINE_SCOPES",
    "CacheCheck",
    "CacheEntry",
    "CacheKey",
    "CacheLayer",
    "CacheTrust",
    "CompatibilityKind",
    "CompatibilityRef",
    "ContextFingerprint",
    "ContextSource",
    "OriginClass",
    "PoisonCheck",
    "Qualification",
    "QuarantineLedger",
    "QuarantineRule",
    "ReuseClass",
    "ReuseRejection",
    "ReuseReceipt",
    "ReuseRequest",
    "admit_reuse",
    "evict",
    "eviction_rank",
]

CONTEXT_FINGERPRINT_SCHEMA = "iris-context-fingerprint-v1"
CACHE_KEY_SCHEMA = "iris-cache-key-v1"
QUARANTINE_SCOPES = ("key", "producer", "workflow")


class CacheLayer(Labeled):
    """Which of the six cache layers an entry lives in. They are not interchangeable.

    The bugs that destroy production truth all come from treating one layer as
    another: a KV block replayed as if it were an approved render, a planning memo
    trusted as evidence. So the pairing of layer and reuse class is checked here,
    which makes the confusion unrepresentable rather than merely discouraged.
    """

    PLANNING = "PLANNING"
    CONTEXT = "CONTEXT"
    WARM_STATE = "WARM_STATE"
    INTERMEDIATE = "INTERMEDIATE"
    FINAL = "FINAL"
    EVIDENCE = "EVIDENCE"

    @property
    def ordinal(self) -> int:
        return _LAYER_ORDINAL[self]

    @property
    def label(self) -> str:
        return f"L{self.ordinal}"

    @property
    def is_ephemeral(self) -> bool:
        """Losing this layer costs time and never costs truth."""

        return self in {CacheLayer.PLANNING, CacheLayer.CONTEXT, CacheLayer.WARM_STATE}

    @property
    def holds_runtime_state(self) -> bool:
        return self is CacheLayer.WARM_STATE

    @property
    def may_satisfy_a_production_output(self) -> bool:
        return self in {CacheLayer.INTERMEDIATE, CacheLayer.FINAL}

    @property
    def requires_receipt(self) -> bool:
        """A semantic result hit is a production fact and has to be evidenced."""

        return self in {CacheLayer.INTERMEDIATE, CacheLayer.FINAL, CacheLayer.EVIDENCE, CacheLayer.CONTEXT}

    @property
    def admits_classes(self) -> tuple["ReuseClass", ...]:
        return _LAYER_CLASSES[self]


_LAYER_ORDINAL: Mapping[CacheLayer, int] = {
    CacheLayer.PLANNING: 0,
    CacheLayer.CONTEXT: 1,
    CacheLayer.WARM_STATE: 2,
    CacheLayer.INTERMEDIATE: 3,
    CacheLayer.FINAL: 4,
    CacheLayer.EVIDENCE: 5,
}


class ReuseClass(Labeled):
    """What may actually be taken from a cache hit, in the kernel's own words."""

    EXACT_REUSE = "EXACT_REUSE"
    QUALIFIED_REUSE = "QUALIFIED_REUSE"
    PARTIAL_REUSE = "PARTIAL_REUSE"
    WARM_REUSE = "WARM_REUSE"
    ADVISORY_REUSE = "ADVISORY_REUSE"
    NO_REUSE = "NO_REUSE"

    @property
    def is_semantic_result(self) -> bool:
        """A production result is being reused, so a receipt is owed."""

        return self in {
            ReuseClass.EXACT_REUSE,
            ReuseClass.QUALIFIED_REUSE,
            ReuseClass.PARTIAL_REUSE,
        }

    @property
    def satisfies_a_node_output(self) -> bool:
        """Only these may stand in for a node's own material output.

        ``PARTIAL_REUSE`` reuses a bounded region or intermediate: the node still has
        work, so a plan that counted it as finished would report bytes it never made.
        """

        return self in {ReuseClass.EXACT_REUSE, ReuseClass.QUALIFIED_REUSE}

    @property
    def requires_receipt(self) -> bool:
        return self.is_semantic_result

    @property
    def may_be_admitted(self) -> bool:
        return self is not ReuseClass.NO_REUSE


_LAYER_CLASSES: Mapping[CacheLayer, tuple[ReuseClass, ...]] = {
    CacheLayer.PLANNING: (ReuseClass.ADVISORY_REUSE, ReuseClass.NO_REUSE),
    CacheLayer.CONTEXT: (
        ReuseClass.EXACT_REUSE,
        ReuseClass.QUALIFIED_REUSE,
        ReuseClass.PARTIAL_REUSE,
        ReuseClass.NO_REUSE,
    ),
    CacheLayer.WARM_STATE: (ReuseClass.WARM_REUSE, ReuseClass.NO_REUSE),
    CacheLayer.INTERMEDIATE: (
        ReuseClass.EXACT_REUSE,
        ReuseClass.QUALIFIED_REUSE,
        ReuseClass.PARTIAL_REUSE,
        ReuseClass.NO_REUSE,
    ),
    CacheLayer.FINAL: (
        ReuseClass.EXACT_REUSE,
        ReuseClass.QUALIFIED_REUSE,
        ReuseClass.NO_REUSE,
    ),
    CacheLayer.EVIDENCE: (ReuseClass.QUALIFIED_REUSE, ReuseClass.PARTIAL_REUSE, ReuseClass.NO_REUSE),
}


class OriginClass(Labeled):
    """Who wrote the entry. Write trust is stricter than read trust by design."""

    TRUSTED_WORKER = "TRUSTED_WORKER"
    VALIDATED_CI = "VALIDATED_CI"
    PROMOTED_EXPERIMENT = "PROMOTED_EXPERIMENT"
    LOCAL_EXPERIMENT = "LOCAL_EXPERIMENT"
    UNKNOWN_SOURCE = "UNKNOWN_SOURCE"

    @property
    def may_read_shared_cache(self) -> bool:
        return self is not OriginClass.UNKNOWN_SOURCE

    @property
    def may_write_shared_cache(self) -> bool:
        return self in {
            OriginClass.TRUSTED_WORKER,
            OriginClass.VALIDATED_CI,
            OriginClass.PROMOTED_EXPERIMENT,
        }


class CompatibilityKind(Labeled):
    """The two opaque compatibility tokens the kernel stores but never interprets."""

    PROVIDER = "PROVIDER"
    CACHE = "CACHE"


@dataclass(frozen=True)
class CompatibilityRef(Record):
    """A provider's or a cache's own compatibility statement, held as a digest.

    M02 cannot know what makes one provider replay identically, and it must not
    pretend to by hashing fields it invented. So a later module hands over an opaque
    digest plus the schema version that produced it, and the kernel keeps the one
    rule it can: equal digests may reuse, different digests may not, and an absent
    digest is never read as "compatible".
    """

    kind: CompatibilityKind
    provider_id: str
    opaque_digest: str
    schema_version: str = "iris-compatibility-ref-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", CompatibilityKind.parse(self.kind, "kind"))
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        object.__setattr__(self, "opaque_digest", require_digest(self.opaque_digest, "opaque_digest"))
        object.__setattr__(self, "schema_version", require_identifier(self.schema_version, "schema_version"))

    @property
    def text(self) -> str:
        return (
            f"{self.kind.value.lower()}:{self.provider_id}@{self.schema_version}={self.opaque_digest[:16]}"
        )


@dataclass(frozen=True)
class ContextSource(Record):
    """One compiled context input, with the position it was retrieved in.

    Ordering is part of the fingerprint because prefix reuse is only safe when the
    prefix is literally the same sequence of tokens.
    """

    ref: ExternalRef
    ordinal: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", ExternalRef.coerce(self.ref, "ref"))
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 0:
            raise SchemaValidationError("ordinal must be a non-negative integer")

    @property
    def text(self) -> str:
        return f"source[{self.ordinal}]={self.ref.text}"


@dataclass(frozen=True)
class ContextFingerprint(Record):
    """Everything that decides which compiled context bytes a model call receives.

    Context compilation is a cacheable production input, so its key has to be as
    honest as a material fingerprint: a different retrieval, template, tokenizer,
    instruction policy or tool schema is a different context. A stale context
    masquerading as current truth is the failure this record exists to make visible.
    """

    sources: tuple[ContextSource, ...] = ()
    compiler: Any = None
    model: Any = None
    tokenizer: Any = None
    policy: Any = None
    profile: str = "default"
    tool_schemas: tuple[ExternalRef, ...] = ()
    compatibility: tuple[CompatibilityRef, ...] = ()
    components: tuple[FingerprintComponent, ...] = ()
    fingerprint: str = ""
    schema_version: str = CONTEXT_FINGERPRINT_SCHEMA

    def __post_init__(self) -> None:
        collected = require_bounded(self.sources, "sources", maximum=MAX_CONTEXT_SOURCES)
        given = tuple(ContextSource.coerce(item, "sources[]") for item in collected)
        ordinals = [item.ordinal for item in given]
        if len(set(ordinals)) != len(ordinals):
            raise SchemaValidationError("sources must name each retrieval position exactly once")
        object.__setattr__(self, "sources", tuple(sorted(given, key=lambda item: item.ordinal)))
        for name in ("compiler", "model", "tokenizer", "policy"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_component_version(value, name))
        object.__setattr__(self, "profile", require_identifier(self.profile, "profile"))
        schemas = require_bounded(self.tool_schemas, "tool_schemas", maximum=MAX_SCHEMA_REFS)
        object.__setattr__(
            self, "tool_schemas", tuple(ExternalRef.parse(item, "tool_schemas[]") for item in schemas)
        )
        tokens = require_bounded(self.compatibility, "compatibility", maximum=MAX_FACETS)
        object.__setattr__(
            self,
            "compatibility",
            tuple(sorted({_compatibility(item, "compatibility[]") for item in tokens}, key=lambda i: i.text)),
        )
        object.__setattr__(self, "schema_version", require_identifier(self.schema_version, "schema_version"))
        derived = self._derive_components()
        collected = require_bounded(self.components, "components", maximum=MAX_CONTEXT_SOURCES)
        declared = tuple(FingerprintComponent.coerce(item, "components[]") for item in collected)
        if declared and declared != derived:
            raise SchemaValidationError(
                "components do not match this context: a fingerprint is derived from its inputs, "
                "never supplied beside them"
            )
        object.__setattr__(self, "components", derived)
        recomputed = content_digest([item.text for item in derived])
        if self.fingerprint == "":
            object.__setattr__(self, "fingerprint", recomputed)
        elif self.fingerprint != recomputed:
            raise SchemaValidationError(
                "context fingerprint does not match its components: the record was altered"
            )

    def _derive_components(self) -> tuple[FingerprintComponent, ...]:
        items: list[FingerprintComponent] = []
        for source in self.sources:
            items.append(FingerprintComponent(kind="source", reference=source.text))
        if not self.sources:
            items.append(FingerprintComponent(kind="source", reference="none"))
        for name in ("compiler", "model", "tokenizer", "policy"):
            value = getattr(self, name)
            if value is not None:
                items.append(FingerprintComponent(kind=name, reference=value.reference))
        items.append(FingerprintComponent(kind="profile", reference=self.profile))
        for schema in self.tool_schemas:
            items.append(FingerprintComponent(kind="tool-schema", reference=schema.text))
        for token in self.compatibility:
            items.append(
                FingerprintComponent(kind=f"compat-{token.kind.value.lower()}", reference=token.text)
            )
        return tuple(sorted(items, key=lambda item: item.text))

    def differs_from(self, other: "ContextFingerprint") -> tuple[str, ...]:
        """Which named inputs moved, so a context miss can be explained, not just measured."""

        mine = {item.text for item in self.components}
        theirs = {item.text for item in other.components}
        return tuple(sorted(mine ^ theirs))

    @property
    def compatibility_digest(self) -> str:
        return content_digest([item.text for item in self.compatibility])

    @property
    def external_ref(self) -> ExternalRef:
        return ExternalRef(
            kind=EntityKind.HIVE_CONTEXT, reference=self.fingerprint, version=self.schema_version
        )


def _compatibility(value: Any, field_name: str) -> CompatibilityRef:
    if isinstance(value, CompatibilityRef):
        return value
    if isinstance(value, Mapping):
        return CompatibilityRef.from_payload(value)
    raise SchemaValidationError(f"{field_name} must be a CompatibilityRef or its payload")


class PoisonCheck(Labeled):
    """The eight cache-poisoning questions, plus the cross-project identity rule.

    Named so a refusal is machine-readable: "poisoned" is never a log line a planner
    has to guess at, and an audit can count which check fired.
    """

    PRODUCER_ADMISSION = "PRODUCER_ADMISSION"
    KEY_SCHEMA = "KEY_SCHEMA"
    DIGEST_VERIFICATION = "DIGEST_VERIFICATION"
    CLOSURE_COMPLETENESS = "CLOSURE_COMPLETENESS"
    QUALIFICATION_EXPIRY = "QUALIFICATION_EXPIRY"
    RIGHTS_PROVENANCE_DRIFT = "RIGHTS_PROVENANCE_DRIFT"
    EVIDENCE_QUALIFICATION = "EVIDENCE_QUALIFICATION"
    WRITE_TRUST = "WRITE_TRUST"
    CROSS_PROJECT_IDENTITY = "CROSS_PROJECT_IDENTITY"

    @property
    def spec_origin(self) -> str:
        return "S04 §12" if self is PoisonCheck.CROSS_PROJECT_IDENTITY else "S04 §11"


@dataclass(frozen=True)
class CacheCheck(Record):
    """One shield question and its answer, kept whether or not it passed."""

    name: PoisonCheck
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", PoisonCheck.parse(self.name, "name"))
        if not isinstance(self.passed, bool):
            raise SchemaValidationError("passed must be a boolean")
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=512))

    @property
    def text(self) -> str:
        return f"{self.name.value}={'ok' if self.passed else 'refused'}: {self.detail}"


@dataclass(frozen=True)
class CacheKey(Record):
    """The three digests that decide whether a cached result is for *this* node.

    A causal fingerprint alone is not enough: context bytes and a provider's own
    compatibility statement change what a node emits while leaving the graph intact.
    Anything irrelevant to these three is, by construction, unable to invalidate a hit.
    """

    node_id: str
    build_fingerprint: str
    context_fingerprint: str
    compatibility_digest: str
    layer: CacheLayer
    schema_version: str = CACHE_KEY_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        for name in ("build_fingerprint", "context_fingerprint", "compatibility_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        object.__setattr__(self, "layer", CacheLayer.parse(self.layer, "layer"))
        object.__setattr__(self, "schema_version", require_identifier(self.schema_version, "schema_version"))

    @classmethod
    def of(
        cls,
        node_id: str,
        *,
        build_fingerprint: str,
        context: ContextFingerprint | None = None,
        layer: CacheLayer = CacheLayer.FINAL,
        schema_version: str = CACHE_KEY_SCHEMA,
    ) -> "CacheKey":
        """Derive the key from a causal fingerprint and, when there is one, a context."""

        return cls(
            node_id=node_id,
            build_fingerprint=build_fingerprint,
            context_fingerprint=context.fingerprint if context is not None else content_digest("no-context"),
            compatibility_digest=context.compatibility_digest if context is not None else content_digest([]),
            layer=layer,
            schema_version=schema_version,
        )

    @property
    def address(self) -> str:
        """The digest a store addresses this key by: the whole claim, nothing else."""

        return content_digest(
            [
                self.node_id,
                self.build_fingerprint,
                self.context_fingerprint,
                self.compatibility_digest,
                self.layer.value,
                self.schema_version,
            ]
        )

    @property
    def external_ref(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.CACHE_KEY, reference=self.address, version=self.schema_version)

    def schema_matches(self, schema_version: Any) -> bool:
        """Compare against one admitted key schema, the only shape a policy states."""

        return self.schema_version == schema_version

    def differs_from(self, other: "CacheKey") -> tuple[str, ...]:
        mine, theirs = self.to_payload(), other.to_payload()
        return tuple(
            f"{name}: {str(mine[name])[:12]} is now {str(theirs[name])[:12]}"
            for name in ("build_fingerprint", "context_fingerprint", "compatibility_digest", "layer")
            if mine[name] != theirs[name]
        )


@dataclass(frozen=True)
class Qualification(Record):
    """The model/tool/environment qualifications an entry was produced under, and their expiry."""

    refs: tuple[ExternalRef, ...] = ()
    expires_at_ms: int = 0

    def __post_init__(self) -> None:
        collected = require_bounded(self.refs, "refs", maximum=MAX_SCHEMA_REFS)
        resolved = tuple(sorted((_qualified(item) for item in collected), key=lambda item: item.text))
        object.__setattr__(self, "refs", resolved)
        object.__setattr__(self, "expires_at_ms", require_millis(self.expires_at_ms, "expires_at_ms"))

    def expired_at(self, now_ms: int) -> bool:
        return self.expires_at_ms <= require_millis(now_ms, "now_ms")

    @property
    def address(self) -> str:
        """Qualification identity: the same certificates and the same expiry, or a different claim."""

        return content_digest([[item.text for item in self.refs], self.expires_at_ms])


_QUALIFIED_KINDS = frozenset(
    {
        EntityKind.MODEL,
        EntityKind.TOOL,
        EntityKind.ENVIRONMENT,
        EntityKind.PROVIDER,
        EntityKind.WORKFLOW,
        EntityKind.SCHEMA,
        EntityKind.POLICY,
    }
)


def _qualified(value: Any) -> ExternalRef:
    ref = ExternalRef.coerce(value, "refs[]")
    if ref.kind not in _QUALIFIED_KINDS:
        raise SchemaValidationError(
            "a qualification may only reference a model, tool, environment, provider, workflow, "
            f"schema or policy, got {ref.kind.value}"
        )
    return ref


@dataclass(frozen=True)
class CacheEntry(Record):
    """What a cache store claims about one produced result.

    This is the untrusted side of the boundary: it arrives from a worker, a store row
    or a restored archive, and every field of it is a request to be believed.
    ``admit_reuse`` is therefore the only path that turns an entry into work avoided.
    """

    entry_id: str
    key: CacheKey
    reuse_class: ReuseClass
    producer: Any
    writer_origin: OriginClass
    project_id: str
    result_digest: str
    revision_ref: ExternalRef
    dependency_closure: tuple[str, ...] = ()
    closure_digest: str = ""
    environment_fingerprint: Any = None
    rights_digest: Any = None
    provenance_digest: Any = None
    identity_refs: tuple[ExternalRef, ...] = ()
    qualification: Qualification = field(default_factory=Qualification)
    evaluator: Any = None
    quality_class: Any = None
    observed_digest: Any = None
    retained_for: tuple[RetentionReason, ...] = ()
    recorded_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_id", require_id(self.entry_id, "entry_id"))
        object.__setattr__(self, "key", CacheKey.coerce(self.key, "key"))
        claimed = ReuseClass.parse(self.reuse_class, "reuse_class")
        layer = self.key.layer
        if claimed not in layer.admits_classes:
            raise BuildError(
                f"{layer.label} ({layer.value}) cannot hold a {claimed.value} entry; the classes admitted "
                f"here are {', '.join(item.value for item in layer.admits_classes)}"
            )
        object.__setattr__(self, "reuse_class", claimed)
        object.__setattr__(self, "producer", require_component_version(self.producer, "producer"))
        object.__setattr__(self, "writer_origin", OriginClass.parse(self.writer_origin, "writer_origin"))
        object.__setattr__(self, "project_id", require_identifier(self.project_id, "project_id"))
        object.__setattr__(self, "result_digest", require_digest(self.result_digest, "result_digest"))
        object.__setattr__(self, "revision_ref", _revision(self.revision_ref))
        closure = require_bounded(self.dependency_closure, "dependency_closure", maximum=MAX_CLOSURE_REFS)
        object.__setattr__(
            self,
            "dependency_closure",
            tuple(sorted({require_text(item, "dependency_closure[]", maximum=256) for item in closure})),
        )
        derived = content_digest(list(self.dependency_closure))
        if self.closure_digest == "":
            object.__setattr__(self, "closure_digest", derived)
        elif self.closure_digest != derived:
            raise BuildError(
                f"entry {self.entry_id[:8]} claims closure digest {self.closure_digest[:12]} for "
                f"{len(self.dependency_closure)} declared dependencies, which is not what they hash to"
            )
        for name in ("environment_fingerprint", "rights_digest", "provenance_digest", "observed_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        identities = require_bounded(self.identity_refs, "identity_refs", maximum=MAX_SCHEMA_REFS)
        object.__setattr__(
            self,
            "identity_refs",
            tuple(sorted({ExternalRef.parse(item, "identity_refs[]") for item in identities},
                          key=lambda item: item.text)),
        )
        object.__setattr__(self, "qualification", Qualification.coerce(self.qualification, "qualification"))
        if self.evaluator is not None:
            object.__setattr__(self, "evaluator", require_component_version(self.evaluator, "evaluator"))
        if self.quality_class is not None:
            object.__setattr__(self, "quality_class", require_quality_class(self.quality_class).value)
        reasons = require_bounded(self.retained_for, "retained_for", maximum=MAX_FACETS)
        object.__setattr__(
            self,
            "retained_for",
            tuple(sorted({RetentionReason.parse(item) for item in reasons}, key=lambda item: item.value)),
        )
        object.__setattr__(self, "recorded_at_ms", require_millis(self.recorded_at_ms, "recorded_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})
        self._require_layer_coherence()

    def _require_layer_coherence(self) -> None:
        """Warm state is not a result, and a result cannot be an anonymous side effect.

        These are the two conflations the module spec names as the source of cache bugs,
        so they are refused where the entry is built rather than at the call site.
        """

        layer = self.key.layer
        if layer.holds_runtime_state:
            if self.observed_digest is not None or self.quality_class is not None:
                raise BuildError(
                    f"WARM_STATE entry {self.entry_id[:8]} carries an observed digest or a quality class: "
                    "runtime KV and model residency are optimization state, never canonical evidence"
                )
            return
        if self.reuse_class.satisfies_a_node_output and self.observed_digest is None:
            raise BuildError(
                f"{self.reuse_class.value} entry {self.entry_id[:8]} names no observed bytes; a reuse that "
                "cannot point at what it would hand back is a guess, not a cache hit"
            )
        if layer is CacheLayer.EVIDENCE and self.evaluator is None:
            raise BuildError(
                f"EVIDENCE entry {self.entry_id[:8]} cites no evaluator, so nothing could invalidate it later"
            )

    @property
    def is_protected(self) -> bool:
        """Release- or provenance-required content survives every eviction policy."""

        return bool(self.retained_for)

    @property
    def text(self) -> str:
        return f"{self.key.node_id}={self.result_digest[:12]}@{self.key.layer.value}"


def _revision(value: Any) -> ExternalRef:
    ref = ExternalRef.coerce(value, "revision_ref")
    if ref.kind is not EntityKind.REVISION:
        raise SchemaValidationError(f"revision_ref must reference a REVISION, got {ref.kind.value}")
    return ref


@dataclass(frozen=True)
class CacheTrust(Record):
    """Which origins may populate which layers, and which producers are known at all.

    Read and write trust are separate fields on purpose: the spec's own example is CI
    and validated workers filling a shared cache while local experiments only read it,
    and one boolean could not state that policy without lying.
    """

    readers: tuple[OriginClass, ...] = tuple(
        sorted((item for item in OriginClass if item.may_read_shared_cache), key=lambda item: item.value)
    )
    writers: tuple[OriginClass, ...] = (OriginClass.TRUSTED_WORKER, OriginClass.VALIDATED_CI)
    allowed_producers: tuple[ComponentVersion, ...] = ()
    admitted_key_schemas: tuple[str, ...] = (CACHE_KEY_SCHEMA,)
    allow_cross_project: bool = False
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        def origins(values: Any, name: str) -> tuple[OriginClass, ...]:
            collected = require_bounded(values, name, maximum=len(OriginClass))
            return tuple(sorted({OriginClass.parse(item, f"{name}[]") for item in collected},
                                key=lambda item: item.value))

        object.__setattr__(self, "readers", origins(self.readers, "readers"))
        object.__setattr__(self, "writers", origins(self.writers, "writers"))
        producers = require_bounded(self.allowed_producers, "allowed_producers", maximum=MAX_CLOSURE_REFS)
        object.__setattr__(
            self,
            "allowed_producers",
            tuple(sorted((require_component_version(item, "allowed_producers[]") for item in producers),
                          key=lambda item: item.reference)),
        )
        schemas = require_bounded(self.admitted_key_schemas, "admitted_key_schemas", maximum=MAX_FACETS)
        object.__setattr__(
            self,
            "admitted_key_schemas",
            tuple(sorted({require_identifier(item, "admitted_key_schemas[]") for item in schemas})),
        )
        if not isinstance(self.allow_cross_project, bool):
            raise SchemaValidationError("allow_cross_project must be a boolean")
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def may_read(self, origin: Any) -> bool:
        return OriginClass.parse(origin, "origin") in self.readers

    def may_write(self, origin: Any) -> bool:
        return OriginClass.parse(origin, "origin") in self.writers

    def knows(self, producer: Any) -> bool:
        wanted = require_component_version(producer, "producer")
        return wanted.reference in {item.reference for item in self.allowed_producers}


@dataclass(frozen=True)
class ReuseRequest(Record):
    """The current truth a cache entry has to match before it may stand in for work."""

    node_id: str
    key: CacheKey
    project_id: str
    now_ms: int
    closure_digest: str
    rights_digest: Any = None
    provenance_digest: Any = None
    environment_fingerprint: Any = None
    required_quality_class: Any = None
    qualified_evaluators: tuple[ComponentVersion, ...] = ()
    protected_identity: bool = False
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "key", CacheKey.coerce(self.key, "key"))
        if self.key.node_id != self.node_id:
            raise SchemaValidationError(
                f"the request is for node {self.node_id} but the key was derived for {self.key.node_id}"
            )
        object.__setattr__(self, "project_id", require_identifier(self.project_id, "project_id"))
        object.__setattr__(self, "now_ms", require_millis(self.now_ms, "now_ms"))
        object.__setattr__(self, "closure_digest", require_digest(self.closure_digest, "closure_digest"))
        for name in ("rights_digest", "provenance_digest", "environment_fingerprint"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        if self.required_quality_class is not None:
            object.__setattr__(
                self, "required_quality_class", require_quality_class(self.required_quality_class, "required_quality_class").value
            )
        evaluators = require_bounded(self.qualified_evaluators, "qualified_evaluators", maximum=MAX_FACETS)
        object.__setattr__(
            self,
            "qualified_evaluators",
            tuple(sorted({_producer(item, "qualified_evaluators[]") for item in evaluators})),
        )
        if not isinstance(self.protected_identity, bool):
            raise SchemaValidationError("protected_identity must be a boolean")
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def requires_evidence(self) -> bool:
        return self.required_quality_class is not None


def _producer(value: Any, field: str) -> str:
    """Store a producer as its reference text, the only form a payload can carry.

    ``ComponentVersion`` is M01's type and has no ``coerce`` that accepts an already
    normalised string, so re-decoding a stored request would otherwise refuse itself.
    """

    if isinstance(value, str):
        return require_text(value, field, maximum=256)
    return require_component_version(value, field).reference


@dataclass(frozen=True)
class ReuseReceipt(Record):
    """The admission evidence behind one semantic cache hit.

    The module spec lists what a receipt must answer, and every one of those fields is
    here, because a hit that cannot say *why* it was safe is indistinguishable from the
    bug where a stale render was served for six episodes.
    """

    receipt_id: str
    node_id: str
    reuse_class: ReuseClass
    source_revision: ExternalRef
    key: CacheKey
    producer: Any
    trust_rule: ExternalRef
    writer_origin: OriginClass
    reason: str
    entry_environment: Any = None
    request_environment: Any = None
    environment_verdict: str = ""
    rights_status: str = "UNCHANGED"
    provenance_status: str = "UNCHANGED"
    validators_required: tuple[ExternalRef, ...] = ()
    validators_performed: tuple[ExternalRef, ...] = ()
    observed_digest: str = ""
    result_digest: str = ""
    producer_attempt_id: Any = None
    admitted_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt_id", require_id(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        claimed = ReuseClass.parse(self.reuse_class, "reuse_class")
        if not claimed.requires_receipt:
            raise BuildError(
                f"{claimed.value} is not semantic result reuse, so it must not carry a production receipt; "
                "warm and advisory state belongs in the runtime's own accounting"
            )
        object.__setattr__(self, "reuse_class", claimed)
        object.__setattr__(self, "source_revision", _revision(self.source_revision))
        object.__setattr__(self, "key", CacheKey.coerce(self.key, "key"))
        if self.key.node_id != self.node_id:
            raise SchemaValidationError(
                f"the receipt is for node {self.node_id} but its key was derived for {self.key.node_id}"
            )
        object.__setattr__(self, "producer", require_component_version(self.producer, "producer"))
        rule = ExternalRef.coerce(self.trust_rule, "trust_rule")
        if rule.kind is not EntityKind.POLICY:
            raise SchemaValidationError(
                f"trust_rule must reference the POLICY that admitted this reuse, got {rule.kind.value}"
            )
        object.__setattr__(self, "trust_rule", rule)
        object.__setattr__(self, "writer_origin", OriginClass.parse(self.writer_origin, "writer_origin"))
        for name in ("entry_environment", "request_environment"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        for name in ("rights_status", "provenance_status", "environment_verdict"):
            value = getattr(self, name)
            if value:
                object.__setattr__(self, name, require_text(value, name, maximum=64).upper())
        if getattr(self, "environment_verdict", "") == "":
            same = self.entry_environment == self.request_environment
            object.__setattr__(self, "environment_verdict", "IDENTICAL" if same else "QUALIFIED_DIFFERENCE")
        for name in ("validators_required", "validators_performed"):
            collected = require_bounded(getattr(self, name), name, maximum=MAX_FACETS)
            object.__setattr__(
                self, name, tuple(sorted({ExternalRef.parse(item, f"{name}[]").text for item in collected}))
            )
        for name in ("observed_digest", "result_digest"):
            value = getattr(self, name)
            if value:
                object.__setattr__(self, name, require_digest(value, name))
        if self.observed_digest and self.result_digest and self.observed_digest != self.result_digest:
            raise BuildError(
                f"the receipt for {self.node_id} reports observed bytes that are not the admitted result"
            )
        if self.reason.strip() == "":
            raise BuildError(
                f"a {claimed.value} receipt for {self.node_id} states no reason; an unexplained cache hit is "
                "exactly the opaque smart-cache decision this kernel forbids"
            )
        if self.producer_attempt_id is not None:
            object.__setattr__(
                self, "producer_attempt_id", require_id(self.producer_attempt_id, "producer_attempt_id")
            )
        object.__setattr__(self, "admitted_at_ms", require_millis(self.admitted_at_ms, "admitted_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_exact(self) -> bool:
        return self.reuse_class is ReuseClass.EXACT_REUSE

    @property
    def satisfies_output(self) -> bool:
        return self.reuse_class.satisfies_a_node_output

    def satisfies(self, node_id: str, digest: str) -> bool:
        """Whether this receipt may stand in for ``node_id`` producing ``digest``."""

        return (
            self.satisfies_output
            and self.node_id == require_identifier(node_id, "node_id")
            and self.result_digest == require_digest(digest, "digest")
        )


@dataclass(frozen=True)
class ReuseRejection(Record):
    """Every shield check, passed or not, so a miss is explainable and countable."""

    node_id: str
    key: CacheKey
    checks: tuple[CacheCheck, ...] = ()
    claimed_class: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "key", CacheKey.coerce(self.key, "key"))
        collected = require_bounded(self.checks, "checks", maximum=len(PoisonCheck))
        items = tuple(CacheCheck.coerce(item, "checks[]") for item in collected)
        if not items:
            raise SchemaValidationError("a rejection must carry the checks it ran")
        names = [item.name for item in items]
        if len(set(names)) != len(names):
            raise SchemaValidationError("checks name one shield question twice")
        object.__setattr__(self, "checks", tuple(sorted(items, key=lambda item: item.name.value)))
        if self.claimed_class is not None:
            object.__setattr__(self, "claimed_class", ReuseClass.parse(self.claimed_class, "claimed_class").value)
        if self.is_admitted:
            raise SchemaValidationError(
                f"every check passed for {self.node_id}; this is an admission, so return the receipt instead"
            )

    @property
    def is_admitted(self) -> bool:
        return all(item.passed for item in self.checks)

    @property
    def refused_by(self) -> tuple[PoisonCheck, ...]:
        return tuple(item.name for item in self.checks if not item.passed)

    @property
    def reasons(self) -> tuple[str, ...]:
        return tuple(item.text for item in self.checks if not item.passed)

    @property
    def text(self) -> str:
        return f"{self.node_id}: " + "; ".join(self.reasons)


def admit_reuse(
    entry: Any,
    request: Any,
    *,
    trust: Any = None,
    quarantine: "QuarantineLedger | None" = None,
    rights_grant_ref: Any = None,
    identity_clearance_ref: Any = None,
) -> ReuseReceipt | ReuseRejection:
    """Run the shield: turn a cache claim into a receipt, or into a named refusal.

    Every check reports even when it passes, because a "no" without a reason is the
    same opacity as an unlogged "yes". The checks do not short-circuit on purpose: a
    planner has to see all of them before deciding whether to fix the entry,
    quarantine the key, or just rebuild.
    """

    claimed = CacheEntry.coerce(entry, "entry")
    wanted = ReuseRequest.coerce(request, "request")
    policy = CacheTrust.coerce(trust) if trust is not None else CacheTrust()
    checks: dict[PoisonCheck, CacheCheck] = {}

    def add(name: PoisonCheck, passed: bool, detail: str) -> None:
        checks[name] = CacheCheck(name=name, passed=bool(passed), detail=detail)

    admitted_producer = policy.knows(claimed.producer)
    add(
        PoisonCheck.PRODUCER_ADMISSION,
        admitted_producer,
        f"producer {claimed.producer.reference} is listed as an admitted writer"
        if admitted_producer
        else f"producer {claimed.producer.reference} is unknown to this trust policy, which names "
        f"{len(policy.allowed_producers)} admitted producers",
    )
    if quarantine is not None:
        blocked = quarantine.blocking(claimed)
        if blocked:
            add(
                PoisonCheck.PRODUCER_ADMISSION,
                False,
                ("quarantined after an earlier mismatch: " + "; ".join(blocked))[:512],
            )
    if not claimed.reuse_class.may_be_admitted:
        add(
            PoisonCheck.PRODUCER_ADMISSION,
            False,
            f"producer {claimed.producer.reference} recorded this entry as {claimed.reuse_class.value}: the "
            "class is the entry's own declaration of what may be taken, and a matching key never overrides it",
        )
    schema_ok = any(claimed.key.schema_matches(item) for item in policy.admitted_key_schemas)
    same_claim = claimed.key == wanted.key
    if schema_ok and same_claim:
        key_detail = f"key {claimed.key.schema_version} is admitted and addresses this exact claim"
    else:
        moved = list(claimed.key.differs_from(wanted.key))
        if not schema_ok:
            moved.append(f"key schema {claimed.key.schema_version} is not one of the admitted schemas")
        if claimed.key.node_id != wanted.key.node_id:
            moved.append(f"the entry belongs to node {claimed.key.node_id}")
        key_detail = ("this entry is keyed to a different claim: " + "; ".join(moved))[:512]
    add(PoisonCheck.KEY_SCHEMA, schema_ok and same_claim, key_detail)
    observed = claimed.observed_digest
    verified = observed is not None and observed == claimed.result_digest
    add(
        PoisonCheck.DIGEST_VERIFICATION,
        verified,
        f"bytes verified at {str(observed)[:12]}"
        if verified
        else f"stored bytes hash to {str(observed)[:12]} while the entry claims {claimed.result_digest[:12]}",
    )
    same_cause = claimed.key.build_fingerprint == wanted.key.build_fingerprint
    closure_ok = bool(claimed.dependency_closure) and same_cause and claimed.closure_digest == wanted.closure_digest
    add(
        PoisonCheck.CLOSURE_COMPLETENESS,
        closure_ok,
        "causal fingerprint and dependency closure match the current build"
        if closure_ok
        else f"entry was keyed to build fingerprint {claimed.key.build_fingerprint[:12]} over closure "
        f"{claimed.closure_digest[:12]} with {len(claimed.dependency_closure)} declared inputs; this node "
        f"now builds at {wanted.key.build_fingerprint[:12]} over {wanted.closure_digest[:12]}",
    )
    expired = claimed.qualification.expired_at(wanted.now_ms)
    add(
        PoisonCheck.QUALIFICATION_EXPIRY,
        not expired and _qualifications_cover(claimed, wanted),
        f"{len(claimed.qualification.refs)} qualifications still in force"
        if not expired
        else f"qualification expired at {claimed.qualification.expires_at_ms}, reuse requested at "
        f"{wanted.now_ms}",
    )
    drift = _rights_drift(claimed, wanted)
    add(PoisonCheck.RIGHTS_PROVENANCE_DRIFT, not drift, "; ".join(drift) or "rights and provenance unchanged")
    evidence_ok, evidence_detail = _evidence_qualified(claimed, wanted)
    add(PoisonCheck.EVIDENCE_QUALIFICATION, evidence_ok, evidence_detail)
    readable = policy.may_read(claimed.writer_origin)
    writable = policy.may_write(claimed.writer_origin)
    add(
        PoisonCheck.WRITE_TRUST,
        readable and writable,
        f"writer {claimed.writer_origin.value} may read the shared cache={readable}, "
        f"may populate it={writable}",
    )
    same_project = claimed.project_id == wanted.project_id
    cleared = rights_grant_ref is not None and (
        not claimed.identity_refs or identity_clearance_ref is not None
    )
    identity_ok = same_project or (policy.allow_cross_project and cleared)
    if same_project:
        identity_detail = f"same project {wanted.project_id}"
    elif identity_ok:
        identity_detail = "cleared by an explicit rights grant" + (
            ", and an identity clearance" if claimed.identity_refs else ""
        )
    elif not cleared:
        identity_detail = "no rights grant" + (
            ", and no clearance for its protected identity refs" if claimed.identity_refs else ""
        )
    else:
        identity_detail = "cross-project reuse is not allowed by this trust policy"
    add(PoisonCheck.CROSS_PROJECT_IDENTITY, identity_ok, identity_detail)
    if any(not item.passed for item in checks.values()):
        return ReuseRejection(
            node_id=wanted.node_id,
            key=wanted.key,
            checks=tuple(checks.values()),
            claimed_class=claimed.reuse_class,
        )
    return ReuseReceipt(
        receipt_id=new_id(),
        node_id=wanted.node_id,
        reuse_class=claimed.reuse_class,
        source_revision=claimed.revision_ref,
        key=claimed.key,
        producer=claimed.producer,
        trust_rule=ExternalRef(
            kind=EntityKind.POLICY, reference="reuse.admission", version=policy.contract_version
        ),
        writer_origin=claimed.writer_origin,
        entry_environment=claimed.environment_fingerprint,
        request_environment=wanted.environment_fingerprint,
        observed_digest=claimed.observed_digest or "",
        result_digest=claimed.result_digest,
        reason=_admission_reason(claimed, wanted),
        admitted_at_ms=wanted.now_ms,
    )


def _qualifications_cover(entry: CacheEntry, request: ReuseRequest) -> bool:
    """An entry produced under no qualification at all proves nothing about this environment."""

    if not entry.qualification.refs:
        return False
    if request.environment_fingerprint is None:
        return True
    return entry.environment_fingerprint == request.environment_fingerprint


def _rights_drift(entry: CacheEntry, request: ReuseRequest) -> tuple[str, ...]:
    drift: list[str] = []
    for name in ("rights", "provenance"):
        before = getattr(entry, f"{name}_digest")
        current = getattr(request, f"{name}_digest")
        if before is None and current is None:
            continue
        if before is None or current is None:
            drift.append(
                f"{name} is stated on one side only: the entry says {before is not None}, "
                f"the request says {current is not None}"
            )
        elif before != current:
            drift.append(
                f"{name} changed since the entry was written: {str(before)[:12]} is now {str(current)[:12]}"
            )
    return tuple(drift)


def _evidence_qualified(entry: CacheEntry, request: ReuseRequest) -> tuple[bool, str]:
    """Ask the M01 ladder whether cached evidence still reaches what the node now requires.

    This is the only place the module reads a quality class, and it reads M01's own
    ``ladder_rank``: re-scoring a decision or inventing a second ranking is exactly how
    a cache hit would come to look good enough to promote.
    """

    if request.required_quality_class is None:
        if entry.quality_class is None:
            return True, "no evidence requirement was stated and the entry claims none"
        return False, "the entry claims a quality class the request never asked about"
    required = QualityClass(request.required_quality_class)
    if entry.quality_class is None:
        return False, f"the output must reach {required.value} but the entry records no quality class"
    if entry.evaluator is None:
        return False, f"a {required.value} reuse cites a class with no evaluator behind it"
    if entry.evaluator.reference not in request.qualified_evaluators:
        return False, f"evaluator {entry.evaluator.reference} is no longer qualified under this policy"
    recorded = QualityClass(entry.quality_class)
    if recorded.ladder_rank < required.ladder_rank:
        return False, (
            f"the cached evidence reaches only {recorded.value}, below the required {required.value}; "
            "M01 owns that ladder and it is not re-scored here"
        )
    return True, f"evidence at {recorded.value} from qualified evaluator {entry.evaluator.reference}"


def _admission_reason(entry: CacheEntry, request: ReuseRequest) -> str:
    """Why this hit may stand in for the work, in the words an auditor asks for.

    The key already matched exactly (``KEY_SCHEMA`` refuses anything else), so the only
    difference an admission may cross is the environment, and that is what
    ``QUALIFIED_REUSE`` exists to state.
    """

    return (
        f"{entry.reuse_class.value} at {entry.key.layer.label} on identical causal, context and "
        f"compatibility inputs from {entry.producer.reference}"
    )


@dataclass(frozen=True)
class QuarantineRule(Record):
    """One poisoned subject, and how far the refusal should spread."""

    rule_id: str
    value: str
    scope: str
    expires_at_ms: int = 0
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", require_id(self.rule_id, "rule_id"))
        object.__setattr__(self, "value", require_text(self.value, "value", maximum=512))
        resolved = require_identifier(self.scope, "scope")
        if resolved not in QUARANTINE_SCOPES:
            raise SchemaValidationError(
                f"scope must be one of {', '.join(QUARANTINE_SCOPES)}, got {self.scope!r}"
            )
        object.__setattr__(self, "scope", resolved)
        object.__setattr__(self, "expires_at_ms", require_millis(self.expires_at_ms, "expires_at_ms"))
        object.__setattr__(self, "reason", require_optional_text(self.reason, "reason", maximum=512) or "")

    def blocks(self, entry: Any, now_ms: int) -> bool:
        claimed = CacheEntry.coerce(entry, "entry")
        if self.expires_at_ms and self.expires_at_ms <= require_millis(now_ms, "now_ms"):
            return False
        if self.scope == "key":
            return self.value == claimed.key.address
        if self.scope == "producer":
            return self.value == claimed.producer.reference
        return self.value == claimed.revision_ref.reference


@dataclass(frozen=True)
class QuarantineLedger:
    """Mismatch memory: a bad hit widens what the planner will refuse to trust later.

    Held per caller, never as a module singleton, because two productions with
    different rights situations must not quarantine each other's caches by accident.
    """

    rules: tuple[QuarantineRule, ...] = ()
    now_ms: int = 0

    def __post_init__(self) -> None:
        collected = require_bounded(self.rules, "rules", maximum=MAX_CLOSURE_REFS)
        object.__setattr__(
            self,
            "rules",
            tuple(sorted((QuarantineRule.coerce(item, "rules[]") for item in collected),
                          key=lambda item: (item.scope, item.value))),
        )
        object.__setattr__(self, "now_ms", require_millis(self.now_ms, "now_ms"))

    def widened(self, entry: Any, reason: str, *, expires_at_ms: int = 0) -> "QuarantineLedger":
        """Quarantine the key, then the producer and workflow that made it.

        A digest mismatch is never only that key's problem: the same producer under the
        same qualification keeps producing the same wrong bytes, so the refusal has to
        travel with the things that could have caused it.
        """

        claimed = CacheEntry.coerce(entry, "entry")
        made = list(self.rules)
        for scope, value in (
            ("key", claimed.key.address),
            ("producer", claimed.producer.reference),
            ("workflow", claimed.revision_ref.reference),
        ):
            made.append(
                QuarantineRule(
                    rule_id=new_id(),
                    value=value,
                    scope=scope,
                    expires_at_ms=expires_at_ms,
                    reason=require_text(reason, "reason", maximum=512),
                )
            )
        return QuarantineLedger(rules=tuple(made), now_ms=self.now_ms)

    def blocking(self, entry: Any) -> tuple[str, ...]:
        claimed = CacheEntry.coerce(entry, "entry")
        return tuple(
            rule.reason or f"{rule.scope}:{rule.value}"
            for rule in self.rules
            if rule.blocks(claimed, self.now_ms)
        )

    def advanced(self, now_ms: int) -> "QuarantineLedger":
        moved = require_millis(now_ms, "now_ms")
        return QuarantineLedger(rules=self.rules, now_ms=max(self.now_ms, moved))


_RANK_BY_LAYER: Mapping[CacheLayer, int] = {
    CacheLayer.WARM_STATE: 0,
    CacheLayer.PLANNING: 1,
    CacheLayer.CONTEXT: 2,
    CacheLayer.INTERMEDIATE: 3,
    CacheLayer.EVIDENCE: 4,
    CacheLayer.FINAL: 5,
}


def eviction_rank(entry: Any) -> int:
    """Cheapest to lose first. Warm state is disposable; protected content is not.

    The rank is about cost, never about truth: an evicted entry gets recomputed, and a
    protected one is kept whatever the budget, because the archive contract outranks any
    cache policy.
    """

    claimed = CacheEntry.coerce(entry, "entry")
    if claimed.is_protected:
        return -1
    return _RANK_BY_LAYER[claimed.key.layer]


def evict(
    entries: Iterable[Any],
    *,
    keep: int,
    protected: Sequence[str] = (),
) -> tuple[CacheEntry, ...]:
    """Return the entries a policy may drop, dropping the cheapest to recompute first.

    ``keep`` counts what stays. Protected ids are never returned whatever the budget:
    eviction that deletes release- or provenance-required content is data loss wearing a
    performance policy.
    """

    resolved = tuple(CacheEntry.coerce(item, "entries[]") for item in entries)
    if isinstance(keep, bool) or not isinstance(keep, int) or keep < 0:
        raise SchemaValidationError("keep must be a non-negative integer")
    guarded = set(protected) | {item.entry_id for item in resolved if item.is_protected}
    candidates = tuple(item for item in resolved if item.entry_id not in guarded)
    ranked = sorted(
        candidates,
        key=lambda item: (eviction_rank(item), item.recorded_at_ms, item.entry_id),
    )
    return tuple(sorted(ranked[: max(0, len(ranked) - keep)], key=lambda item: item.entry_id))
