"""M02 area A: identity, references and immutable history.

Three layers must never collapse: a semantic id says *which thing* it is, a
content digest says *which bytes*, and an attempt id says *which try*. A rename,
a move and a retry all keep the semantic id; two different artifacts may share
bytes. Everything historical here is append-only: aliases retire, supersessions
point forward, and a transition receipt is the only way state moves.
"""

from __future__ import annotations

import re
import secrets
import time
from dataclasses import dataclass, field, replace
from typing import Any, Iterable
from uuid import UUID

from .base import Labeled, Record, of
from .errors import IdentityError, SchemaValidationError
from .limits import (
    MAX_ALIASES,
    MAX_LOCATOR_CHARS,
    MAX_METADATA_KEYS,
    MAX_RECEIPT_EVIDENCE,
    MAX_SUPERSESSION_CHAIN,
)
from .machines import StateMachine
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    SUPPORTED_CONTRACT_VERSIONS,
    canonical_json,
    require_bounded,
    require_digest,
    require_identifier,
    require_millis,
    require_metadata,
    require_reference,
    require_supported_version,
    require_text,
    require_unique,
    require_version_text,
)

__all__ = [
    "LIFECYCLE_SCHEMA_VERSION",
    "SUPPORTED_LIFECYCLE_SCHEMAS",
    "REVISION_SCHEMA_VERSION",
    "EntityKind",
    "ExternalRef",
    "Uuid7Generator",
    "new_id",
    "require_id",
    "ProjectLifecycleState",
    "PROJECT_LIFECYCLE",
    "AttemptState",
    "ATTEMPT_LIFECYCLE",
    "TERMINAL_ATTEMPT_STATES",
    "ProjectEnvelope",
    "ProductionPassport",
    "ArtifactIdentity",
    "RevisionRef",
    "AttemptIdentity",
    "AliasRef",
    "AliasLedger",
    "LocatorRef",
    "TransitionReceipt",
    "SupersessionRef",
    "SupersessionLedger",
]

LIFECYCLE_SCHEMA_VERSION = "iris-lifecycle-schema-v1"
SUPPORTED_LIFECYCLE_SCHEMAS: frozenset[str] = frozenset({LIFECYCLE_SCHEMA_VERSION})

REVISION_SCHEMA_VERSION = "iris-project-os-revision-v1"

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def require_id(value: Any, field: str) -> str:
    """A canonical UUID string. Format is validated; a UUID is never a content proof."""

    if isinstance(value, UUID):
        candidate = str(value)
    elif isinstance(value, str):
        candidate = value.strip().lower()
    else:
        raise SchemaValidationError(f"{field} must be a UUID or a canonical UUID string")
    if _UUID_PATTERN.fullmatch(candidate) is None:
        raise SchemaValidationError(
            f"{field} must be a canonical UUID string, got {value!r}"
        )
    return candidate


@dataclass(frozen=True)
class Uuid7Generator:
    """RFC 9562 UUIDv7 built from ``secrets``: no third-party dependency, no clock trust.

    The 48-bit millisecond prefix gives *creation locality* ordering only. It is
    explicitly not causal order: two workers on different machines may mint ids in
    any order, and nothing in M02 may read a timestamp as a dependency.
    """

    clock: Any = None
    _last_millis: int = 0

    def __post_init__(self) -> None:
        if self.clock is None:
            object.__setattr__(self, "clock", lambda: int(time.time() * 1000))
        object.__setattr__(self, "_last_millis", require_millis(self._last_millis, "_last_millis"))

    @property
    def last_millis(self) -> int:
        return self._last_millis

    def next_id(self) -> UUID:
        observed = require_millis(int(self.clock()), "clock()")
        # A backward clock step must not mint an id that looks older than one already issued.
        timestamp = max(observed, self._last_millis)
        object.__setattr__(self, "_last_millis", timestamp)
        rand_a = int.from_bytes(secrets.token_bytes(2), "big") & 0x0FFF
        rand_b = int.from_bytes(secrets.token_bytes(8), "big") & ((1 << 62) - 1)
        value = (
            (timestamp & ((1 << 48) - 1)) << 80
            | 0x7 << 76
            | rand_a << 64
            | 0b10 << 62
            | rand_b
        )
        return UUID(int=value)

    def next_id_text(self) -> str:
        return str(self.next_id())


_GENERATOR = Uuid7Generator()


def new_id() -> str:
    """Mint a fresh semantic id. Callers may inject their own generator for determinism."""

    return _GENERATOR.next_id_text()


class EntityKind(Labeled):
    """What an opaque reference points at. Unknown kinds are refused, not guessed."""

    PROJECT = "PROJECT"
    PRODUCTION = "PRODUCTION"
    ARTIFACT = "ARTIFACT"
    REVISION = "REVISION"
    ATTEMPT = "ATTEMPT"
    GRAPH = "GRAPH"
    NODE = "NODE"
    PORT = "PORT"
    EDGE = "EDGE"
    SNAPSHOT = "SNAPSHOT"
    BRANCH = "BRANCH"
    VARIANT_SET = "VARIANT_SET"
    RELEASE = "RELEASE"
    ARCHIVE = "ARCHIVE"
    RECEIPT = "RECEIPT"
    DELTA = "DELTA"
    SUPERSESSION = "SUPERSESSION"
    ALIAS = "ALIAS"
    POLICY = "POLICY"
    FIDELITY_CONTRACT = "FIDELITY_CONTRACT"
    QUALITY_DECISION = "QUALITY_DECISION"
    EVIDENCE = "EVIDENCE"
    SEMANTIC_TYPE = "SEMANTIC_TYPE"
    SCHEMA = "SCHEMA"
    INTENT = "INTENT"
    MODEL = "MODEL"
    TOOL = "TOOL"
    PROVIDER = "PROVIDER"
    ENVIRONMENT = "ENVIRONMENT"
    DESTINATION = "DESTINATION"
    HIVE_CONTEXT = "HIVE_CONTEXT"
    RIGHTS = "RIGHTS"
    PROVENANCE = "PROVENANCE"
    CACHE_KEY = "CACHE_KEY"
    WORKFLOW = "WORKFLOW"


@dataclass(frozen=True)
class ExternalRef(Record):
    """An opaque pointer to something M02 does not own: a store row, a provider, a policy."""

    kind: EntityKind
    reference: str
    version: Any = None
    content_digest: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", EntityKind.parse(self.kind, "kind"))
        object.__setattr__(self, "reference", require_reference(self.reference, "reference"))
        if self.version is not None:
            object.__setattr__(self, "version", require_version_text(self.version, "version"))
        if self.content_digest is not None:
            object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))

    @property
    def text(self) -> str:
        if self.version is None:
            return f"{self.kind.value.lower()}:{self.reference}"
        return f"{self.kind.value.lower()}:{self.reference}@{self.version}"

    @classmethod
    def parse(cls, value: Any, field: str = "reference") -> "ExternalRef":
        return cls.coerce(value, field)

    @classmethod
    def bind(cls, kind: EntityKind, reference: str, **kwargs: Any) -> "ExternalRef":
        return cls(kind=kind, reference=reference, **kwargs)


class ProjectLifecycleState(Labeled):
    """Project-level lifecycle. Archival preserves identity; deletion is not a lifecycle step."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


PROJECT_LIFECYCLE = StateMachine(
    name="project-lifecycle",
    state_type=ProjectLifecycleState,
    transitions={
        ProjectLifecycleState.CREATED: (
            ProjectLifecycleState.ACTIVE,
            ProjectLifecycleState.ARCHIVED,
        ),
        ProjectLifecycleState.ACTIVE: (
            ProjectLifecycleState.PAUSED,
            ProjectLifecycleState.ARCHIVED,
        ),
        ProjectLifecycleState.PAUSED: (
            ProjectLifecycleState.ACTIVE,
            ProjectLifecycleState.ARCHIVED,
        ),
        ProjectLifecycleState.ARCHIVED: (),
    },
)


class AttemptState(Labeled):
    """Attempt mechanics. M11 schedules the work; M02 owns only the durable semantics."""

    QUEUED = "QUEUED"
    LEASED = "LEASED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ABANDONED = "ABANDONED"


TERMINAL_ATTEMPT_STATES: frozenset[AttemptState] = frozenset(
    {
        AttemptState.SUCCEEDED,
        AttemptState.FAILED,
        AttemptState.CANCELLED,
        AttemptState.ABANDONED,
    }
)

ATTEMPT_LIFECYCLE = StateMachine(
    name="attempt-lifecycle",
    state_type=AttemptState,
    transitions={
        AttemptState.QUEUED: (AttemptState.LEASED, AttemptState.CANCELLED, AttemptState.ABANDONED),
        AttemptState.LEASED: (
            AttemptState.RUNNING,
            AttemptState.QUEUED,
            AttemptState.CANCELLED,
            AttemptState.ABANDONED,
        ),
        AttemptState.RUNNING: tuple(TERMINAL_ATTEMPT_STATES),
    },
)


def _freeze_aliases(values: Any, field_name: str) -> tuple[str, ...]:
    return require_bounded(require_unique(values, field_name), field_name, maximum=MAX_ALIASES)


def _freeze_refs(values: Any, field_name: str, *, maximum: int) -> tuple[ExternalRef, ...]:
    collected = require_bounded(values, field_name, maximum=maximum)
    return tuple(ExternalRef.parse(item, f"{field_name}[]") for item in collected)


@dataclass(frozen=True)
class ProjectEnvelope(Record):
    """The durable identity of a project plus the references a production needs."""

    project_id: str
    display_name: str
    root_graph_ref: ExternalRef
    state: ProjectLifecycleState = ProjectLifecycleState.CREATED
    domain_profile_refs: tuple[ExternalRef, ...] = ()
    canonical_policy_refs: tuple[ExternalRef, ...] = ()
    aliases: tuple[str, ...] = ()
    hive_namespace: Any = None
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {
        "root_graph_ref": of(ExternalRef),
        "domain_profile_refs": of(ExternalRef),
        "canonical_policy_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", require_id(self.project_id, "project_id"))
        object.__setattr__(self, "display_name", require_text(self.display_name, "display_name", maximum=256))
        if not isinstance(self.root_graph_ref, ExternalRef):
            raise SchemaValidationError("root_graph_ref must be an ExternalRef")
        object.__setattr__(self, "state", ProjectLifecycleState.parse(self.state, "state"))
        object.__setattr__(self, "domain_profile_refs", _freeze_refs(self.domain_profile_refs, "domain_profile_refs", maximum=64))
        object.__setattr__(self, "canonical_policy_refs", _freeze_refs(self.canonical_policy_refs, "canonical_policy_refs", maximum=64))
        object.__setattr__(self, "aliases", _freeze_aliases(self.aliases, "aliases"))
        if self.hive_namespace is not None:
            object.__setattr__(self, "hive_namespace", require_identifier(self.hive_namespace, "hive_namespace"))
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS))

    def renamed(self, display_name: str) -> "ProjectEnvelope":
        """A rename is a new value of the same identity, never a new project."""

        return replace(self, display_name=display_name)

    def transitioned_to(self, state: ProjectLifecycleState, *, reason: str = "") -> "ProjectEnvelope":
        PROJECT_LIFECYCLE.require(self.state, state, reason=reason)
        return replace(self, state=state)


@dataclass(frozen=True)
class SupersessionRef(Record):
    """An append-only pointer from a retired record to the record that replaces it."""

    superseded_id: str
    superseded_kind: EntityKind
    replacement_id: str
    replacement_kind: EntityKind
    reason_code: str
    receipt_id: Any = None
    effective_at_ms: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "superseded_id", require_id(self.superseded_id, "superseded_id"))
        object.__setattr__(self, "replacement_id", require_id(self.replacement_id, "replacement_id"))
        object.__setattr__(self, "superseded_kind", EntityKind.parse(self.superseded_kind, "superseded_kind"))
        object.__setattr__(self, "replacement_kind", EntityKind.parse(self.replacement_kind, "replacement_kind"))
        object.__setattr__(self, "reason_code", require_identifier(self.reason_code, "reason_code"))
        if self.receipt_id is not None:
            object.__setattr__(self, "receipt_id", require_id(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "effective_at_ms", require_millis(self.effective_at_ms, "effective_at_ms"))
        if self.superseded_id == self.replacement_id:
            raise IdentityError("a record cannot supersede itself")


@dataclass(frozen=True)
class ProductionPassport(Record):
    """Why a production exists, what it promised, and which graph and contracts bind it."""

    production_id: str
    project_id: str
    intent_ref: ExternalRef
    graph_ref: ExternalRef
    requested_outputs: tuple[str, ...] = ()
    quality_contract_refs: tuple[ExternalRef, ...] = ()
    policy_refs: tuple[ExternalRef, ...] = ()
    supersession: Any = None
    creation_reason: str = "initial-request"
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {
        "intent_ref": of(ExternalRef),
        "graph_ref": of(ExternalRef),
        "quality_contract_refs": of(ExternalRef),
        "policy_refs": of(ExternalRef),
        "supersession": of(SupersessionRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "project_id", require_id(self.project_id, "project_id"))
        for name in ("intent_ref", "graph_ref"):
            if not isinstance(getattr(self, name), ExternalRef):
                raise SchemaValidationError(f"{name} must be an ExternalRef")
        outputs = require_bounded(self.requested_outputs, "requested_outputs", maximum=128)
        object.__setattr__(
            self,
            "requested_outputs",
            tuple(require_identifier(item, "requested_outputs[]") for item in outputs),
        )
        if not self.requested_outputs:
            raise SchemaValidationError("requested_outputs must name at least one requested target")
        object.__setattr__(self, "quality_contract_refs", _freeze_refs(self.quality_contract_refs, "quality_contract_refs", maximum=64))
        object.__setattr__(self, "policy_refs", _freeze_refs(self.policy_refs, "policy_refs", maximum=64))
        if self.supersession is not None and not isinstance(self.supersession, SupersessionRef):
            raise SchemaValidationError("supersession must be a SupersessionRef or None")
        object.__setattr__(self, "creation_reason", require_text(self.creation_reason, "creation_reason", maximum=512))
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS))

    def replaced_by(self, replacement: "ProductionPassport", reason_code: str, receipt_id: str) -> SupersessionRef:
        """Return the supersession record a replacement production must carry forward."""

        return SupersessionRef(
            superseded_id=self.production_id,
            superseded_kind=EntityKind.PRODUCTION,
            replacement_id=replacement.production_id,
            replacement_kind=EntityKind.PRODUCTION,
            reason_code=reason_code,
            receipt_id=receipt_id,
            effective_at_ms=replacement.created_at_ms,
        )

    @property
    def supersedes(self) -> Any:
        return self.supersession


@dataclass(frozen=True)
class ArtifactIdentity(Record):
    """A semantic artifact: stable across rename, move and re-render."""

    artifact_id: str
    production_id: str
    semantic_type_ref: ExternalRef
    display_name: str = "artifact"
    aliases: tuple[str, ...] = ()
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {"semantic_type_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_id", require_id(self.artifact_id, "artifact_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        if not isinstance(self.semantic_type_ref, ExternalRef):
            raise SchemaValidationError("semantic_type_ref must be an ExternalRef")
        if self.semantic_type_ref.kind is not EntityKind.SEMANTIC_TYPE:
            raise IdentityError(
                f"semantic_type_ref must reference a SEMANTIC_TYPE, got {self.semantic_type_ref.kind.value}"
            )
        object.__setattr__(self, "display_name", require_text(self.display_name, "display_name", maximum=256))
        object.__setattr__(self, "aliases", _freeze_aliases(self.aliases, "aliases"))
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS))

    def renamed(self, display_name: str) -> "ArtifactIdentity":
        return replace(self, display_name=display_name)


@dataclass(frozen=True)
class RevisionRef(Record):
    """One immutable content revision of one artifact, with the lineage that made it."""

    artifact_id: str
    revision_id: str
    content_digest: str
    semantic_type_ref: ExternalRef
    producer_attempt_id: Any = None
    input_lineage: tuple[ExternalRef, ...] = ()
    quality_contract_ref: Any = None
    quality_decision_ref: Any = None
    provenance_refs: tuple[ExternalRef, ...] = ()
    format_version: str = "1.0.0"
    schema_version: str = REVISION_SCHEMA_VERSION
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {
        "semantic_type_ref": of(ExternalRef),
        "input_lineage": of(ExternalRef),
        "quality_contract_ref": of(ExternalRef),
        "quality_decision_ref": of(ExternalRef),
        "provenance_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_id", require_id(self.artifact_id, "artifact_id"))
        object.__setattr__(self, "revision_id", require_id(self.revision_id, "revision_id"))
        object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))
        if not isinstance(self.semantic_type_ref, ExternalRef):
            raise SchemaValidationError("semantic_type_ref must be an ExternalRef")
        if self.producer_attempt_id is not None:
            object.__setattr__(self, "producer_attempt_id", require_id(self.producer_attempt_id, "producer_attempt_id"))
        object.__setattr__(self, "input_lineage", _freeze_refs(self.input_lineage, "input_lineage", maximum=1024))
        for name in ("quality_contract_ref", "quality_decision_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, ExternalRef):
                raise SchemaValidationError(f"{name} must be an ExternalRef or None")
        object.__setattr__(self, "provenance_refs", _freeze_refs(self.provenance_refs, "provenance_refs", maximum=128))
        object.__setattr__(self, "format_version", require_version_text(self.format_version, "format_version"))
        object.__setattr__(self, "schema_version", require_version_text(self.schema_version, "schema_version"))
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS))

    @property
    def is_source(self) -> bool:
        """A source revision was admitted, not produced; it still needs provenance."""

        return self.producer_attempt_id is None


@dataclass(frozen=True)
class AttemptIdentity(Record):
    """One try at one node in one production. Retrying always mints a new attempt."""

    attempt_id: str
    production_id: str
    graph_ref: ExternalRef
    node_id: str
    provider_ref: ExternalRef
    state: AttemptState = AttemptState.QUEUED
    branch_id: Any = None
    retry_of_attempt_id: Any = None
    outcome_code: Any = None
    started_at_ms: int = 0
    finished_at_ms: Any = None
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {"graph_ref": of(ExternalRef), "provider_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", require_id(self.attempt_id, "attempt_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        if not isinstance(self.graph_ref, ExternalRef):
            raise SchemaValidationError("graph_ref must be an ExternalRef")
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        if not isinstance(self.provider_ref, ExternalRef):
            raise SchemaValidationError("provider_ref must be an ExternalRef")
        object.__setattr__(self, "state", AttemptState.parse(self.state, "state"))
        for name in ("branch_id", "retry_of_attempt_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_id(value, name))
        if self.outcome_code is not None:
            object.__setattr__(self, "outcome_code", require_identifier(self.outcome_code, "outcome_code"))
        object.__setattr__(self, "started_at_ms", require_millis(self.started_at_ms, "started_at_ms"))
        if self.finished_at_ms is not None:
            object.__setattr__(self, "finished_at_ms", require_millis(self.finished_at_ms, "finished_at_ms"))
            if self.finished_at_ms < self.started_at_ms:
                raise SchemaValidationError("finished_at_ms precedes started_at_ms")
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS))

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_ATTEMPT_STATES

    def transitioned_to(self, state: AttemptState, *, at_ms: int, reason: str = "") -> "AttemptIdentity":
        ATTEMPT_LIFECYCLE.require(self.state, state, reason=reason)
        target = AttemptState.parse(state, "state")
        if target in TERMINAL_ATTEMPT_STATES:
            return replace(self, state=target, finished_at_ms=require_millis(at_ms, "at_ms"))
        return replace(self, state=target)

    def retried(self, *, attempt_id: str, provider_ref: Any = None, started_at_ms: int = 0) -> "AttemptIdentity":
        """A retry is a new attempt that references the one it replaces, never a rewrite."""

        if not self.is_terminal:
            raise IdentityError(
                f"attempt {self.attempt_id} is {self.state.value}; only a terminal attempt may be retried"
            )
        return AttemptIdentity(
            attempt_id=attempt_id,
            production_id=self.production_id,
            graph_ref=self.graph_ref,
            node_id=self.node_id,
            provider_ref=provider_ref or self.provider_ref,
            state=AttemptState.QUEUED,
            branch_id=self.branch_id,
            retry_of_attempt_id=self.attempt_id,
            started_at_ms=started_at_ms,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class AliasRef(Record):
    """A human-facing name bound to one id. Retired aliases never silently rebind."""

    alias: str
    entity_kind: EntityKind
    entity_id: str
    version: int = 1
    created_at_ms: int = 0
    retired_at_ms: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "alias", require_identifier(self.alias, "alias"))
        object.__setattr__(self, "entity_kind", EntityKind.parse(self.entity_kind, "entity_kind"))
        object.__setattr__(self, "entity_id", require_id(self.entity_id, "entity_id"))
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise SchemaValidationError("version must be a positive integer")
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        if self.retired_at_ms is not None:
            object.__setattr__(self, "retired_at_ms", require_millis(self.retired_at_ms, "retired_at_ms"))
            if self.retired_at_ms < self.created_at_ms:
                raise SchemaValidationError("retired_at_ms precedes created_at_ms")

    @property
    def is_retired(self) -> bool:
        return self.retired_at_ms is not None


@dataclass
class AliasLedger:
    """Versioned alias bindings where the newest record decides what is live.

    Retirement is permanent for a name: rebinding an alias would silently move
    references an earlier receipt already froze, and reusing a retired name would
    make two histories answer to the same label.
    """

    _records: dict[str, list[AliasRef]] = field(default_factory=dict)

    def bind(
        self,
        alias: str,
        entity_kind: EntityKind,
        entity_id: str,
        *,
        created_at_ms: int = 0,
    ) -> AliasRef:
        name = require_identifier(alias, "alias")
        wanted = require_id(entity_id, "entity_id")
        history = self._records.get(name, [])
        if history:
            newest = history[-1]
            if newest.is_retired:
                raise IdentityError(
                    f"alias {name!r} was retired at version {newest.version}; a retired name is "
                    "never rebound, so publish a new alias instead"
                )
            if newest.entity_id == wanted and newest.entity_kind is EntityKind.parse(entity_kind):
                return newest
            raise IdentityError(
                f"alias {name!r} already binds {newest.entity_id}; retire it first, because a "
                "silent rebind would rewrite what earlier receipts asserted"
            )
        record = AliasRef(
            alias=name, entity_kind=entity_kind, entity_id=wanted, created_at_ms=created_at_ms
        )
        self._records[name] = [record]
        return record

    def current(self, alias: str) -> AliasRef:
        name = require_identifier(alias, "alias")
        history = self._records.get(name)
        if not history:
            raise IdentityError(f"alias {name!r} is not bound to any identity")
        newest = history[-1]
        if newest.is_retired:
            raise IdentityError(f"alias {name!r} is retired and resolves to nothing")
        return newest

    resolve = current

    def retire(self, alias: str, *, retired_at_ms: int) -> AliasRef:
        live = self.current(alias)
        retired = replace(live, retired_at_ms=retired_at_ms, version=live.version + 1)
        self._records[live.alias].append(retired)
        return retired

    def aliases_of(self, entity_id: str) -> tuple[AliasRef, ...]:
        wanted = require_id(entity_id, "entity_id")
        found: list[AliasRef] = []
        for name in sorted(self._records):
            try:
                live = self.current(name)
            except IdentityError:
                continue
            if live.entity_id == wanted:
                found.append(live)
        return tuple(found)

    def versions_of(self, alias: str) -> tuple[AliasRef, ...]:
        """Every binding ever recorded, so history stays auditable after retirement."""

        return tuple(self._records.get(require_identifier(alias, "alias"), ()))

    @property
    def size(self) -> int:
        return len(self._records)


@dataclass(frozen=True)
class LocatorRef(Record):
    """Canonical, transport-free locator: where a revision lives is not what it is."""

    project_id: str
    production_id: Any = None
    artifact_id: Any = None
    revision_digest: Any = None
    scheme: str = "iris"

    LOCATOR_SEGMENTS = ("project", "production", "artifact", "revision")

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", require_id(self.project_id, "project_id"))
        for name in ("production_id", "artifact_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_id(value, name))
        if self.revision_digest is not None:
            object.__setattr__(self, "revision_digest", require_digest(self.revision_digest, "revision_digest"))
        if self.revision_digest is not None and self.artifact_id is None:
            raise SchemaValidationError("a revision locator requires its artifact id")
        if self.artifact_id is not None and self.production_id is None:
            raise SchemaValidationError("an artifact locator requires its production id")
        object.__setattr__(self, "scheme", require_identifier(self.scheme, "scheme"))

    @property
    def uri(self) -> str:
        parts = [f"{self.scheme}://project/{self.project_id}"]
        if self.production_id:
            parts.append(f"production/{self.production_id}")
        if self.artifact_id:
            parts.append(f"artifact/{self.artifact_id}")
        if self.revision_digest:
            parts.append(f"revision/{self.revision_digest}")
        return "/".join(parts)

    @classmethod
    def from_uri(cls, uri: Any) -> "LocatorRef":
        text = require_text(uri, "uri", maximum=MAX_LOCATOR_CHARS)
        scheme, _, rest = text.partition("://")
        if not rest:
            raise SchemaValidationError(f"{uri!r} is not a locatable URI with a scheme")
        segments = [item for item in rest.split("/") if item]
        if len(segments) % 2:
            raise SchemaValidationError(f"{uri!r} has a dangling segment")
        pairs = dict(zip(segments[0::2], segments[1::2]))
        unexpected = set(pairs) - {"project", *cls.LOCATOR_SEGMENTS[1:]}
        if unexpected:
            raise SchemaValidationError(f"{uri!r} has unknown locator parts: {sorted(unexpected)}")
        return cls(
            scheme=scheme,
            project_id=pairs.get("project", ""),
            production_id=pairs.get("production"),
            artifact_id=pairs.get("artifact"),
            revision_digest=pairs.get("revision"),
        )


@dataclass(frozen=True)
class TransitionReceipt(Record):
    """The only durable proof that state moved, chained to the receipt before it."""

    transition_id: str
    entity_kind: EntityKind
    entity_id: str
    to_state: str
    actor: ComponentVersion
    state_schema: str = LIFECYCLE_SCHEMA_VERSION
    reason_code: str = "unspecified"
    timestamp_ms: int = 0
    from_state: Any = None
    causal_parent_receipt_id: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    policy_ref: Any = None
    command_id: Any = None
    command_digest: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "actor": of(ComponentVersion),
        "evidence_refs": of(ExternalRef),
        "policy_ref": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "transition_id", require_id(self.transition_id, "transition_id"))
        object.__setattr__(self, "entity_kind", EntityKind.parse(self.entity_kind, "entity_kind"))
        object.__setattr__(self, "entity_id", require_id(self.entity_id, "entity_id"))
        object.__setattr__(self, "to_state", require_text(self.to_state, "to_state", maximum=64))
        if self.from_state is not None:
            object.__setattr__(
                self, "from_state", require_text(self.from_state, "from_state", maximum=64)
            )
        object.__setattr__(self, "state_schema", require_supported_version("state schema", self.state_schema, SUPPORTED_LIFECYCLE_SCHEMAS))
        object.__setattr__(self, "reason_code", require_identifier(self.reason_code, "reason_code"))
        if not isinstance(self.actor, ComponentVersion):
            raise SchemaValidationError("actor must be a ComponentVersion identifying who made the change")
        object.__setattr__(self, "timestamp_ms", require_millis(self.timestamp_ms, "timestamp_ms"))
        if self.causal_parent_receipt_id is not None:
            object.__setattr__(self, "causal_parent_receipt_id", require_id(self.causal_parent_receipt_id, "causal_parent_receipt_id"))
            if self.causal_parent_receipt_id == self.transition_id:
                raise IdentityError("a receipt cannot be its own causal parent")
        object.__setattr__(self, "evidence_refs", _freeze_refs(self.evidence_refs, "evidence_refs", maximum=MAX_RECEIPT_EVIDENCE))
        if self.policy_ref is not None and not isinstance(self.policy_ref, ExternalRef):
            raise SchemaValidationError("policy_ref must be an ExternalRef or None")
        for name in ("command_id", "command_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_text(value, name, maximum=128))
        if (self.command_id is None) != (self.command_digest is None):
            raise SchemaValidationError("command_id and command_digest are issued together or not at all")
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)

    @property
    def is_initial(self) -> bool:
        return self.from_state is None

    def conflicts_with(self, other: "TransitionReceipt") -> Any:
        """Return the mismatch between two commands, or ``None`` when they are idempotent."""

        if self.command_id is None or other.command_id is None:
            return "at least one receipt carries no command identity"
        if self.command_id != other.command_id:
            return None if self.command_digest == other.command_digest else "different commands recorded the same target"
        if self.command_digest != other.command_digest:
            return "the same command id carries a different semantic digest"
        for name in ("entity_id", "to_state", "entity_kind"):
            if getattr(self, name) != getattr(other, name):
                return f"command {self.command_id} was replayed against a different {name}"
        return None

    def key(self) -> str:
        return canonical_json(self.to_payload())


@dataclass
class SupersessionLedger:
    """Append-only supersession with a policy-resolved 'latest admitted' view."""

    _records: list[SupersessionRef] = field(default_factory=list)

    def record(self, ref: SupersessionRef) -> SupersessionRef:
        if not isinstance(ref, SupersessionRef):
            raise SchemaValidationError("SupersessionLedger.record expects a SupersessionRef")
        for existing in self._records:
            if existing.superseded_id == ref.superseded_id:
                if existing == ref:
                    return existing
                raise IdentityError(
                    f"{ref.superseded_id} is already superseded by {existing.replacement_id}; "
                    "a record cannot be superseded twice"
                )
        self._resolve(ref.replacement_id)
        self._records.append(ref)
        return ref

    def _resolve(self, identifier: str) -> SupersessionRef | None:
        for item in self._records:
            if item.superseded_id == identifier:
                return item
        return None

    def chain(self, identifier: str) -> tuple[SupersessionRef, ...]:
        walked: list[SupersessionRef] = []
        seen: set[str] = {require_id(identifier, "identifier")}
        current = require_id(identifier, "identifier")
        while True:
            ref = self._resolve(current)
            if ref is None:
                return tuple(walked)
            if ref.replacement_id in seen:
                raise IdentityError(f"supersession cycle detected at {ref.replacement_id}")
            if len(walked) >= MAX_SUPERSESSION_CHAIN:
                raise IdentityError(
                    f"supersession chain from {identifier} exceeds the admitted maximum {MAX_SUPERSESSION_CHAIN}"
                )
            walked.append(ref)
            seen.add(ref.replacement_id)
            current = ref.replacement_id

    def is_superseded(self, identifier: str) -> bool:
        return self._resolve(require_id(identifier, "identifier")) is not None

    def latest(self, identifier: str, *, admitted: Iterable[str] | None = None) -> str:
        """Follow supersession to the current record, honouring an admission predicate.

        ``admitted`` is evaluated against each candidate id; a replacement that is
        not admitted stops the walk, so 'latest' is always policy-bounded.
        """

        wanted = require_id(identifier, "identifier")
        admitted_set = None if admitted is None else frozenset(admitted)
        current = wanted
        for ref in self.chain(wanted):
            if admitted_set is not None and ref.replacement_id not in admitted_set:
                break
            current = ref.replacement_id
        return current

    @property
    def records(self) -> tuple[SupersessionRef, ...]:
        return tuple(self._records)

    def history_of(self, identifier: str) -> frozenset[str]:
        wanted = require_id(identifier, "identifier")
        predecessors = {
            item.superseded_id for item in self._records if item.replacement_id == wanted
        }
        for item in self._records:
            if item.replacement_id in predecessors:
                predecessors |= self.history_of(item.superseded_id)
        return frozenset(predecessors | {wanted})


def revision_locator(
    envelope: ProjectEnvelope,
    passport: ProductionPassport,
    artifact: ArtifactIdentity,
    revision: RevisionRef,
) -> LocatorRef:
    """Derive the canonical locator; storage schemes stay behind ``LocatorRef.scheme``."""

    return LocatorRef(
        project_id=envelope.project_id,
        production_id=passport.production_id,
        artifact_id=artifact.artifact_id,
        revision_digest=revision.content_digest,
    )
