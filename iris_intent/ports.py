"""The twelve extension boundaries §12 of the frozen contract demands, as types rather than prose.

M03 is not a media generator, a project OS, a quality judge or a rights authority, and §12 of the
contract lists the twelve places where those modules still have to be able to answer. This file
states each of those questions and refuses every other one, so that "later modules plug in here" is
a shape a reviewer can check instead of a promise somebody has to remember. No provider is
implemented here, and none can be: nothing in this module runs, reads, polls or persists anything.

Four laws make the boundaries real rather than decorative.

*A provider answers only at the boundary it signed up for.* ``ProviderDescriptor`` records which
boundaries a component admits, and ``require_port`` is the single gate every call site passes
through. A rights service that starts reporting branch topology is a different component, not the
same one having an idea.

*An extension reference is evidence or it is nothing.* ``ExtensionRef`` refuses an unbound ref, so
a citation into a foreign namespace says what was there, not merely that something was. The pin
is what lets a stale answer be caught by :mod:`~.freshness` instead of discovered by a producer.

*A provider may report, never restate.* ``ExtensionObservation`` refuses a payload that carries
canonical-looking keys — statements, constraints, authority, ``admitted_by`` — because the failure
mode §14 names is a provider result that quietly *is* the intent. Answers arrive as gaps, refs and
identifier strings; the brief changes only through an admitted revision.

*The ref has to be the kind the boundary speaks.* Each ``ExtensionBoundary`` names the ``RefKind``
namespaces it may answer about, and ``ExtensionRef`` enforces the pairing. Handing a
``M02_BRANCH`` ref to the quality-profile port is refused at construction rather than answered with
a plausible-looking ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from .base import Labeled, Record, of
from .errors import (
    LimitExceededError,
    PortContractError,
    RefError,
    SchemaValidationError,
    UntrustedExtensionError,
)
from .identity import RefKind, SemanticRef, require_bound_ref
from .limits import (
    MAX_ADMISSION_CLAIMS,
    MAX_CAPABILITY_DEMANDS,
    MAX_ENTRIES_PER_FIELD,
    MAX_PROVENANCE_REFS,
)
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    require_contract_version,
    require_identifier,
    require_text,
)

__all__ = [
    "ExtensionBoundary",
    "ExtensionRef",
    "ProviderDescriptor",
    "ExtensionObservation",
    "ExtensionPorts",
    "PORT_BOUNDARIES",
    "PORT_PROTOCOLS",
    "CANONICAL_MUTATION_KEYS",
    "ProjectGraphPort",
    "SemanticTypePort",
    "IdentityAnchorPort",
    "QualityProfilePort",
    "CapabilityPort",
    "CanonPort",
    "ContextDependencyPort",
    "RightsPort",
    "SecurityAuthorityPort",
    "DestinationPort",
    "ExplanationExportPort",
    "DomainVocabularyPort",
    "boundaries_admitting",
    "require_port",
    "require_answered_ref",
]

#: Field names a provider may never use in its answer. The list is about shapes, not words: an
#: observation that reports a constraint has not answered a question, it has attempted an edit.
CANONICAL_MUTATION_KEYS = frozenset(
    {
        "admitted_by",
        "constraint",
        "constraints",
        "override",
        "patch",
        "revision",
        "statements",
        "supersede",
        "authority",
    }
)


class ExtensionBoundary(Labeled):
    """The twelve questions §12 allows M03 to ask somebody else.

    Membership is the contract's list, not a superset of what implementation found convenient: an
    extra boundary would be a place a later module can park authority M03 was never granted, and a
    missing one would force a real dependency through an ill-fitting door.
    """

    PROJECT_GRAPH = "PROJECT_GRAPH"
    SEMANTIC_TYPE = "SEMANTIC_TYPE"
    IDENTITY_ANCHOR = "IDENTITY_ANCHOR"
    QUALITY_PROFILE = "QUALITY_PROFILE"
    PROVIDER_CAPABILITY = "PROVIDER_CAPABILITY"
    CANON_STORY = "CANON_STORY"
    CONTEXT_DEPENDENCY = "CONTEXT_DEPENDENCY"
    PROVENANCE_RIGHTS = "PROVENANCE_RIGHTS"
    SECURITY_AUTHORITY = "SECURITY_AUTHORITY"
    DELIVERY_DESTINATION = "DELIVERY_DESTINATION"
    EXPLANATION_EXPORT = "EXPLANATION_EXPORT"
    DOMAIN_VOCABULARY = "DOMAIN_VOCABULARY"

    @property
    def ref_kinds(self) -> frozenset[str]:
        """Which ref namespaces this boundary is allowed to answer about."""

        return _BOUNDARY_KINDS[self]

    @property
    def speaks_for(self) -> str:
        """The one-line claim a refusal quotes, so an error says whose answer is missing."""

        return _BOUNDARY_CLAIMS[self]

    @property
    def resolves_in(self) -> str:
        """The module §12 expects to implement this, which is never M03."""

        return _BOUNDARY_OWNERS[self]

    def admits(self, reference: Any) -> bool:
        """Whether a ref of this kind may cross this boundary at all."""

        item = SemanticRef.coerce(reference, "reference")
        return item.kind in self.ref_kinds


_BOUNDARY_KINDS: Mapping[ExtensionBoundary, frozenset[str]] = {
    ExtensionBoundary.PROJECT_GRAPH: frozenset(
        {
            RefKind.M02_PROJECT.value,
            RefKind.M02_PRODUCTION.value,
            RefKind.M02_BRANCH.value,
            RefKind.M02_VARIANT.value,
            RefKind.M02_NODE.value,
            RefKind.M02_SNAPSHOT.value,
            RefKind.M02_BUILD.value,
            RefKind.M02_RELEASE.value,
        }
    ),
    ExtensionBoundary.SEMANTIC_TYPE: frozenset(
        {RefKind.SEMANTIC_TYPE.value, RefKind.EXTERNAL.value}
    ),
    ExtensionBoundary.IDENTITY_ANCHOR: frozenset({RefKind.ANCHOR.value, RefKind.POLICY.value}),
    ExtensionBoundary.QUALITY_PROFILE: frozenset(
        {
            RefKind.M01_DOMAIN_PROFILE.value,
            RefKind.M01_DIMENSION_REGISTRY.value,
            RefKind.M01_DIMENSION.value,
            RefKind.M01_EVALUATOR.value,
            RefKind.M01_CONTRACT.value,
        }
    ),
    ExtensionBoundary.PROVIDER_CAPABILITY: frozenset(
        {RefKind.CAPABILITY.value, RefKind.RECEIPT.value}
    ),
    ExtensionBoundary.CANON_STORY: frozenset({RefKind.CANON.value, RefKind.EXTERNAL.value}),
    ExtensionBoundary.CONTEXT_DEPENDENCY: frozenset(
        {
            RefKind.SOURCE.value,
            RefKind.REVISION.value,
            RefKind.FRESHNESS.value,
            RefKind.PASSPORT.value,
        }
    ),
    ExtensionBoundary.PROVENANCE_RIGHTS: frozenset(
        {RefKind.PROVENANCE.value, RefKind.POLICY.value, RefKind.SOURCE.value}
    ),
    ExtensionBoundary.SECURITY_AUTHORITY: frozenset(
        {RefKind.POLICY.value, RefKind.RECEIPT.value, RefKind.REVISION.value}
    ),
    ExtensionBoundary.DELIVERY_DESTINATION: frozenset(
        {RefKind.DESTINATION.value, RefKind.EXTERNAL.value}
    ),
    ExtensionBoundary.EXPLANATION_EXPORT: frozenset(
        {RefKind.BRIEF.value, RefKind.REVISION.value, RefKind.STATEMENT.value, RefKind.EXTERNAL.value}
    ),
    ExtensionBoundary.DOMAIN_VOCABULARY: frozenset(
        {RefKind.PREDICATE.value, RefKind.SEMANTIC_TYPE.value}
    ),
}

_BOUNDARY_CLAIMS: Mapping[ExtensionBoundary, str] = {
    ExtensionBoundary.PROJECT_GRAPH: "project, production, branch, variant and build state",
    ExtensionBoundary.SEMANTIC_TYPE: "the semantic types and IR schemas a downstream compiler defines",
    ExtensionBoundary.IDENTITY_ANCHOR: "identity anchors and the DNA policy that binds them",
    ExtensionBoundary.QUALITY_PROFILE: "domain profiles, dimension registries and evaluator capability",
    ExtensionBoundary.PROVIDER_CAPABILITY: "what a provider can do and what it did",
    ExtensionBoundary.CANON_STORY: "canon and story state M03 may cite but never edit",
    ExtensionBoundary.CONTEXT_DEPENDENCY: "context sources and the positions derived semantics came from",
    ExtensionBoundary.PROVENANCE_RIGHTS: "provenance, rights and consent policy",
    ExtensionBoundary.SECURITY_AUTHORITY: "security and authority policy",
    ExtensionBoundary.DELIVERY_DESTINATION: "destinations and delivery profiles",
    ExtensionBoundary.EXPLANATION_EXPORT: "rendering M03's explanation graph for a viewer",
    ExtensionBoundary.DOMAIN_VOCABULARY: "domain semantic paths and predicate extensions",
}

_BOUNDARY_OWNERS: Mapping[ExtensionBoundary, str] = {
    ExtensionBoundary.PROJECT_GRAPH: "M02",
    ExtensionBoundary.SEMANTIC_TYPE: "M04",
    ExtensionBoundary.IDENTITY_ANCHOR: "M05/M20",
    ExtensionBoundary.QUALITY_PROFILE: "M01",
    ExtensionBoundary.PROVIDER_CAPABILITY: "M02/M30",
    ExtensionBoundary.CANON_STORY: "M20/M21",
    ExtensionBoundary.CONTEXT_DEPENDENCY: "M40/HIVE",
    ExtensionBoundary.PROVENANCE_RIGHTS: "M53",
    ExtensionBoundary.SECURITY_AUTHORITY: "M54",
    ExtensionBoundary.DELIVERY_DESTINATION: "M59",
    ExtensionBoundary.EXPLANATION_EXPORT: "M50/M60",
    ExtensionBoundary.DOMAIN_VOCABULARY: "the domain registry that owns the vocabulary",
}

def boundaries_admitting(kind: Any) -> tuple[ExtensionBoundary, ...]:
    """Which boundaries will take an answer about a kind.

    Several, for ``POLICY`` and ``SOURCE``, and that is honest: the same rights document answers a
    provenance question and an authority one. The pairing is deliberately not inverted into a
    single "kind belongs to boundary" map, because inverting it would invent an owner for refs that
    have two, and the second reader would silently get the first one's answer.
    """

    wanted = RefKind.parse(kind, "kind").value
    return tuple(item for item in ExtensionBoundary if wanted in item.ref_kinds)


@dataclass(frozen=True)
class ExtensionRef(Record):
    """A pinned citation into a namespace M03 does not own, labelled with who may answer about it.

    The boundary is part of the identity rather than a hint: a ref is created to ask one kind of
    question, and reusing it as the answer to another is how a build id ends up read as a rights
    clearance. ``provider_id`` may be ``None``, which means exactly what it says — M03 holds a
    citation nobody has offered to resolve — and every port call refuses such a ref rather than
    guessing at a provider.
    """

    boundary: str
    reference: SemanticRef
    provider_id: str | None = None
    seen_in_revision: SemanticRef | None = None
    note: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    NESTED = {
        "reference": of(SemanticRef),
        "seen_in_revision": of(SemanticRef),
    }

    def __post_init__(self) -> None:
        parsed = ExtensionBoundary.parse(self.boundary, "boundary")
        object.__setattr__(self, "boundary", parsed.value)
        item = require_bound_ref(self.reference, "reference")
        if item.kind not in parsed.ref_kinds:
            raise RefError(
                f"{item.text} is a {item.kind} ref and {parsed.value} answers about "
                f"{sorted(parsed.ref_kinds)}; a citation asked at the wrong boundary gets an answer "
                "that means something else, which is worse than no answer"
            )
        object.__setattr__(self, "reference", item)
        if self.provider_id is not None:
            object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        if self.seen_in_revision is not None:
            object.__setattr__(
                self,
                "seen_in_revision",
                require_bound_ref(self.seen_in_revision, "seen_in_revision", kind=RefKind.REVISION),
            )
        if self.note is not None:
            object.__setattr__(self, "note", require_text(self.note, "note", maximum=1024))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def boundary_enum(self) -> ExtensionBoundary:
        return ExtensionBoundary.parse(self.boundary)

    @property
    def kind(self) -> str:
        return self.reference.kind

    @property
    def text(self) -> str:
        return self.reference.text

    @property
    def resolvable(self) -> bool:
        """Whether anybody has promised to answer about this ref."""

        return self.provider_id is not None

    def require_resolvable(self, action: str) -> "ExtensionRef":
        if self.provider_id is None:
            raise PortContractError(
                f"cannot {action}: {self.text} carries no provider, so §12's boundary has nothing on "
                "the other side of it and an invented answer would be M03 testifying for a module it "
                "does not implement"
            )
        return self

    def at_revision(self, revision_ref: SemanticRef) -> "ExtensionRef":
        """The same citation tagged with the M03 revision that was looking.

        Separate rather than optional-at-the-call-site because an observation without a revision is
        unauditable: §26's stale-policy checks need to know what the asker believed when it asked.
        """

        return ExtensionRef(
            boundary=self.boundary,
            reference=self.reference,
            provider_id=self.provider_id,
            seen_in_revision=revision_ref,
            note=self.note,
            metadata=self.metadata,
            contract_version=self.contract_version,
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "boundary": self.boundary,
            "reference": self.reference.text,
            "provider_id": self.provider_id,
            "seen_in_revision": None if self.seen_in_revision is None else self.seen_in_revision.text,
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True)
class ProviderDescriptor(Record):
    """What one component admits about itself: who it is, and which claims it is willing to make.

    The descriptor is the reason a port cannot quietly grow. A provider that answers at a boundary it
    never declared is refused by name, so wiring a new capability into a pipeline is a versioned
    change to this record rather than a change to whatever the code happens to call.
    """

    provider_id: str
    component: Any
    boundaries: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    contract_version: str = ""

    NESTED = {"component": of(ComponentVersion)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        if not isinstance(self.component, ComponentVersion):
            raise SchemaValidationError(
                "component must be a ComponentVersion; a provider that names no version cannot be "
                "caught when it changes under a decision that trusted it"
            )
        if len(self.boundaries) > MAX_ADMISSION_CLAIMS:
            raise LimitExceededError(
                f"a provider may claim at most {MAX_ADMISSION_CLAIMS} boundaries, not {len(self.boundaries)}; "
                "a component that answers everything is not a boundary but a second kernel"
            )
        declared = tuple(
            sorted(
                {ExtensionBoundary.parse(item, "boundaries[]") for item in (self.boundaries or ())},
                key=lambda item: item.value,
            )
        )
        object.__setattr__(self, "boundaries", tuple(item.value for item in declared))
        if len(self.capabilities) > MAX_CAPABILITY_DEMANDS:
            raise LimitExceededError(
                f"provider {self.provider_id} lists {len(self.capabilities)} capabilities, over "
                f"{MAX_CAPABILITY_DEMANDS}"
            )
        object.__setattr__(
            self,
            "capabilities",
            tuple(sorted({require_identifier(item, "capabilities[]") for item in (self.capabilities or ())})),
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def boundary_enums(self) -> tuple[ExtensionBoundary, ...]:
        return tuple(ExtensionBoundary.parse(item) for item in self.boundaries)

    def admits(self, boundary: Any) -> bool:
        return ExtensionBoundary.parse(boundary, "boundary").value in self.boundaries

    def supports(self, capability: Any) -> bool:
        return require_identifier(capability, "capability") in self.capabilities

    def may_speak_about(self, reference: Any) -> bool:
        """Whether this provider may answer about a ref, boundary and kind both checked."""

        item = ExtensionRef.coerce(reference, "reference")
        return self.admits(item.boundary) and item.boundary_enum.admits(item.reference)

    def require_admits(self, boundary: Any) -> ExtensionBoundary:
        parsed = ExtensionBoundary.parse(boundary, "boundary")
        if not self.admits(parsed):
            raise PortContractError(
                f"{self.provider_id} admits "
                f"{', '.join(self.boundaries) or 'nothing'}, not {parsed.value}, which speaks for "
                f"{parsed.speaks_for}; §12's boundaries are drawn per component, so an unrelated "
                "provider may not be wired in as a placeholder"
            )
        return parsed


@dataclass(frozen=True)
class ExtensionObservation(Record):
    """What a provider said, at which revision, and what it could not say (§12, §14).

    An observation is deliberately the weakest object in the kernel: it can carry gaps, refs and
    identifier strings, and nothing else. It cannot carry a statement, a constraint or an authority,
    because the provider half of §14's list is "provider output attempting canonical mutation", and
    the only reliable defence is a record that has nowhere to put the mutation.

    ``gaps`` is required in spirit rather than in fact: an observation that reports no gaps and no
    facts asserts a complete answer, which is why ``refuse_silent_gap`` exists for the call sites
    where completeness is what was asked for.
    """

    observation_id: str
    boundary: str
    provider_id: str
    about: ExtensionRef
    revision_ref: SemanticRef
    facts: Mapping[str, Any] = field(default_factory=dict)
    gaps: tuple[str, ...] = ()
    cites: tuple[SemanticRef, ...] = ()
    notes: str | None = None
    contract_version: str = ""

    NESTED = {"about": of(ExtensionRef), "revision_ref": of(SemanticRef), "cites": of(SemanticRef)}

    def __post_init__(self) -> None:
        parsed = ExtensionBoundary.parse(self.boundary, "boundary")
        object.__setattr__(self, "observation_id", require_identifier(self.observation_id, "observation_id"))
        object.__setattr__(self, "boundary", parsed.value)
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        item = ExtensionRef.coerce(self.about, "about")
        if item.boundary != parsed.value:
            raise RefError(
                f"observation {self.observation_id} is filed under {parsed.value} but asks about a "
                f"{item.boundary} ref; one record cannot straddle two boundaries and pretend to be one answer"
            )
        if item.provider_id is not None and item.provider_id != self.provider_id:
            raise RefError(
                f"observation {self.observation_id} comes from {self.provider_id} about a citation "
                f"assigned to {item.provider_id}; a handle belongs to the provider that minted it"
            )
        object.__setattr__(self, "about", item)
        object.__setattr__(
            self,
            "revision_ref",
            require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION),
        )
        facts = bounded_metadata(self.facts, "facts")
        attempted = sorted(set(key.lower() for key in facts) & CANONICAL_MUTATION_KEYS)
        if attempted:
            raise UntrustedExtensionError(
                f"observation {self.observation_id} reports {attempted}; a provider answers a "
                "question about the brief and cannot carry the brief itself, which would be a "
                "semantic mutation arriving through a port with no admitted revision behind it (§14)"
            )
        object.__setattr__(self, "facts", facts)
        if len(self.gaps) > MAX_ENTRIES_PER_FIELD:
            raise LimitExceededError(
                f"observation {self.observation_id} lists {len(self.gaps)} gaps, over {MAX_ENTRIES_PER_FIELD}"
            )
        object.__setattr__(
            self,
            "gaps",
            tuple(sorted({require_text(item, "gaps[]", maximum=512) for item in (self.gaps or ())})),
        )
        citations = tuple(
            sorted(
                (
                    require_bound_ref(one, "cites[]")
                    for one in (self.cites or ())
                ),
                key=lambda one: one.text,
            )
        )
        if len(citations) > MAX_PROVENANCE_REFS:
            raise LimitExceededError(
                f"observation {self.observation_id} cites {len(citations)} refs, over {MAX_PROVENANCE_REFS}"
            )
        object.__setattr__(self, "cites", citations)
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def boundary_enum(self) -> ExtensionBoundary:
        return ExtensionBoundary.parse(self.boundary)

    @property
    def complete(self) -> bool:
        return not self.gaps

    @property
    def identity(self) -> tuple[str, ...]:
        return (self.boundary, self.provider_id, self.about.text, self.revision_ref.text)

    def answer(self, key: str) -> Any:
        """A recorded fact, or the refusal that explains there is none.

        Returning ``None`` would let "the provider said nothing" and "the provider said this is
        absent" look identical to the caller, which is the confusion §14 refuses.
        """

        name = require_identifier(key, "key")
        if name not in self.facts:
            raise PortContractError(
                f"observation {self.observation_id} records no answer for {name}"
                + (f"; it reported {len(self.gaps)} gap(s)" if self.gaps else "")
            )
        return self.facts[name]

    def require_answered(self, key: str) -> Any:
        value = self.answer(key)
        if self.about.seen_in_revision is not None and self.about.seen_in_revision != self.revision_ref:
            raise RefError(
                f"observation {self.observation_id} was taken at {self.revision_ref.text} about a ref "
                f"last seen at {self.about.seen_in_revision.text}; the question and the answer are "
                "about different readings"
            )
        return value

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "boundary": self.boundary,
            "provider_id": self.provider_id,
            "about": self.about.fingerprint_inputs(),
            "revision_ref": self.revision_ref.text,
            "facts": dict(sorted(self.facts.items())),
            "gaps": list(self.gaps),
            "cites": [item.text for item in self.cites],
            "contract_version": self.contract_version,
        }


PORT_PROTOCOLS: Mapping[ExtensionBoundary, tuple[str, ...]] = MappingProxyType({
    ExtensionBoundary.PROJECT_GRAPH: ("production_of", "branch_of", "state_of"),
    ExtensionBoundary.SEMANTIC_TYPE: ("type_of", "carries_path"),
    ExtensionBoundary.IDENTITY_ANCHOR: ("anchor_for", "policy_for"),
    ExtensionBoundary.QUALITY_PROFILE: ("profile_for", "registry_of", "evaluator_for"),
    ExtensionBoundary.PROVIDER_CAPABILITY: ("capabilities_for", "translation_receipt"),
    ExtensionBoundary.CANON_STORY: ("canon_of", "is_canonical"),
    ExtensionBoundary.CONTEXT_DEPENDENCY: ("upstream_of", "position_of"),
    ExtensionBoundary.PROVENANCE_RIGHTS: ("provenance_of", "consent_state"),
    ExtensionBoundary.SECURITY_AUTHORITY: ("policy_for",),
    ExtensionBoundary.DELIVERY_DESTINATION: ("destination_for", "profiles_for"),
    ExtensionBoundary.EXPLANATION_EXPORT: ("render",),
    ExtensionBoundary.DOMAIN_VOCABULARY: ("signature_for", "path_of"),
})

PORT_BOUNDARIES: tuple[ExtensionBoundary, ...] = tuple(ExtensionBoundary)


@runtime_checkable
class ProjectGraphPort(Protocol):
    """Boundary 1: M02 owns projects, productions, branches, variants and builds (§12.1)."""

    def production_of(self, reference: ExtensionRef) -> ExtensionRef: ...

    def branch_of(self, reference: ExtensionRef) -> ExtensionRef: ...

    def state_of(self, reference: ExtensionRef) -> ExtensionObservation: ...


@runtime_checkable
class SemanticTypePort(Protocol):
    """Boundary 2: M04 defines SemanticTypes and IR schemas; M03 may only cite them (§12.2)."""

    def type_of(self, reference: ExtensionRef) -> ExtensionRef: ...

    def carries_path(self, reference: ExtensionRef, semantic_path: str) -> bool: ...


@runtime_checkable
class IdentityAnchorPort(Protocol):
    """Boundary 3: the anchor and DNA policy a spokesperson or persona is bound by (§12.3)."""

    def anchor_for(self, reference: ExtensionRef) -> ExtensionRef: ...

    def policy_for(self, reference: ExtensionRef) -> ExtensionRef: ...


@runtime_checkable
class QualityProfilePort(Protocol):
    """Boundary 4: M01's registry, profiles and evaluator capability (§12.4).

    M03 *consumes* this and grants nothing from it. The fidelity bridge refuses to compile a
    contract against a dimension this port cannot name, which is the difference between a quality
    target and an invented one.
    """

    def profile_for(self, reference: ExtensionRef) -> ExtensionRef: ...

    def registry_of(self, reference: ExtensionRef) -> ExtensionRef: ...

    def evaluator_for(self, dimension: ExtensionRef) -> ExtensionRef: ...


@runtime_checkable
class CapabilityPort(Protocol):
    """Boundary 5: what a provider can do, and what it says it did (§12.5)."""

    def capabilities_for(self, reference: ExtensionRef) -> ExtensionObservation: ...

    def translation_receipt(self, reference: ExtensionRef) -> ExtensionRef: ...


@runtime_checkable
class CanonPort(Protocol):
    """Boundary 6: canon and story state M03 cites but never edits (§12.6)."""

    def canon_of(self, reference: ExtensionRef) -> ExtensionRef: ...

    def is_canonical(self, reference: ExtensionRef) -> bool: ...


@runtime_checkable
class ContextDependencyPort(Protocol):
    """Boundary 7: context sources and the positions derived semantics were computed from (§12.7)."""

    def upstream_of(self, reference: ExtensionRef) -> ExtensionRef: ...

    def position_of(self, reference: ExtensionRef) -> ExtensionObservation: ...


@runtime_checkable
class RightsPort(Protocol):
    """Boundary 8: provenance, rights and consent (§12.8).

    A ``rights_ok``-shaped boolean is deliberately absent: the answer this port gives is a policy
    ref and a state string, which M03 can cite in a conflict and re-check when it moves. A boolean
    would be M03 making a rights decision on somebody else's behalf.
    """

    def provenance_of(self, reference: ExtensionRef) -> ExtensionRef: ...

    def consent_state(self, reference: ExtensionRef) -> str: ...


@runtime_checkable
class SecurityAuthorityPort(Protocol):
    """Boundary 9: security and authority policy (§12.9), resolved through the authority graph."""

    def policy_for(self, reference: ExtensionRef) -> ExtensionRef: ...


@runtime_checkable
class DestinationPort(Protocol):
    """Boundary 10: destinations and delivery profiles (§12.10)."""

    def destination_for(self, reference: ExtensionRef) -> ExtensionRef: ...

    def profiles_for(self, reference: ExtensionRef) -> tuple[str, ...]: ...


@runtime_checkable
class ExplanationExportPort(Protocol):
    """Boundary 11: rendering an explanation projection for a viewer (§12.11).

    The port returns text it was handed or a ref to it. Producing an explanation is M03's job
    (§:mod:`~.explanation`); displaying one is not, and a viewer that answers questions about the
    brief from its own copy of the graph is a second source of truth.
    """

    def render(self, reference: ExtensionRef) -> str: ...


@runtime_checkable
class DomainVocabularyPort(Protocol):
    """Boundary 12: domain semantic paths and predicate extensions (§12.12).

    ``signature_for`` returning ``None`` is a legitimate answer — an unknown optional predicate is
    simply not admitted — while a *mandatory* one is refused by
    :meth:`~.predicates.PredicateRegistry.require`. This port reports what exists; it never
    interprets it.
    """

    def signature_for(self, reference: ExtensionRef) -> ExtensionRef | None: ...

    def path_of(self, reference: ExtensionRef) -> str: ...


#: Every boundary and the port shape that answers it, used by :func:`require_port`.
_PORT_SHAPES: Mapping[ExtensionBoundary, tuple[type, tuple[str, ...]]] = MappingProxyType({
    ExtensionBoundary.PROJECT_GRAPH: (ProjectGraphPort, PORT_PROTOCOLS[ExtensionBoundary.PROJECT_GRAPH]),
    ExtensionBoundary.SEMANTIC_TYPE: (SemanticTypePort, PORT_PROTOCOLS[ExtensionBoundary.SEMANTIC_TYPE]),
    ExtensionBoundary.IDENTITY_ANCHOR: (IdentityAnchorPort, PORT_PROTOCOLS[ExtensionBoundary.IDENTITY_ANCHOR]),
    ExtensionBoundary.QUALITY_PROFILE: (QualityProfilePort, PORT_PROTOCOLS[ExtensionBoundary.QUALITY_PROFILE]),
    ExtensionBoundary.PROVIDER_CAPABILITY: (CapabilityPort, PORT_PROTOCOLS[ExtensionBoundary.PROVIDER_CAPABILITY]),
    ExtensionBoundary.CANON_STORY: (CanonPort, PORT_PROTOCOLS[ExtensionBoundary.CANON_STORY]),
    ExtensionBoundary.CONTEXT_DEPENDENCY: (
        ContextDependencyPort,
        PORT_PROTOCOLS[ExtensionBoundary.CONTEXT_DEPENDENCY],
    ),
    ExtensionBoundary.PROVENANCE_RIGHTS: (RightsPort, PORT_PROTOCOLS[ExtensionBoundary.PROVENANCE_RIGHTS]),
    ExtensionBoundary.SECURITY_AUTHORITY: (
        SecurityAuthorityPort,
        PORT_PROTOCOLS[ExtensionBoundary.SECURITY_AUTHORITY],
    ),
    ExtensionBoundary.DELIVERY_DESTINATION: (
        DestinationPort,
        PORT_PROTOCOLS[ExtensionBoundary.DELIVERY_DESTINATION],
    ),
    ExtensionBoundary.EXPLANATION_EXPORT: (
        ExplanationExportPort,
        PORT_PROTOCOLS[ExtensionBoundary.EXPLANATION_EXPORT],
    ),
    ExtensionBoundary.DOMAIN_VOCABULARY: (
        DomainVocabularyPort,
        PORT_PROTOCOLS[ExtensionBoundary.DOMAIN_VOCABULARY],
    ),
})


class ExtensionPorts:
    """A passed-in wiring of boundaries to providers, with no module-level instance.

    A singleton registry would let two compilations in one process disagree about who answers
    because of import order, and the fingerprints they produced would differ for a reason no record
    explains. So a wiring is an argument, exactly like :class:`~.predicates.PredicateRegistry`.
    """

    __slots__ = ("_by_boundary",)

    def __init__(self, **providers: Any) -> None:
        self._by_boundary: dict[str, Any] = {}
        for name, provider in providers.items():
            self.attach(name, provider)

    def attach(self, boundary: Any, provider: Any) -> "ExtensionPorts":
        """Wire a provider at a boundary, refusing a collision rather than replacing one."""

        parsed = ExtensionBoundary.parse(boundary, "boundary")
        if parsed.value in self._by_boundary:
            raise PortContractError(
                f"{parsed.value} already has a provider; swapping one out at runtime would let a "
                "later reader attribute an answer to a component that never gave it"
            )
        require_port(provider, parsed)
        self._by_boundary[parsed.value] = provider
        return self

    def provider_for(self, boundary: Any) -> Any:
        parsed = ExtensionBoundary.parse(boundary, "boundary")
        return self._by_boundary.get(parsed.value)

    def require(self, boundary: Any) -> Any:
        parsed = ExtensionBoundary.parse(boundary, "boundary")
        provider = self._by_boundary.get(parsed.value)
        if provider is None:
            raise PortContractError(
                f"no provider is wired for {parsed.value}, which speaks for {parsed.speaks_for}; "
                f"§12 expects {parsed.resolves_in} to answer, and M03 may not answer for it"
            )
        return provider

    @property
    def wired(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_boundary))

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(item.value for item in PORT_BOUNDARIES if item.value not in self._by_boundary)

    def extended(self, **providers: Any) -> "ExtensionPorts":
        """A new wiring with extra boundaries, leaving this one untouched."""

        clone = ExtensionPorts()
        clone._by_boundary = dict(self._by_boundary)
        for name, provider in providers.items():
            clone.attach(name, provider)
        return clone

    def __repr__(self) -> str:
        return f"ExtensionPorts(wired={list(self.wired)})"


def require_port(provider: Any, boundary: Any, *, capability: Any = None) -> ProviderDescriptor:
    """The one gate every port call passes through: this component, at this boundary, saying this.

    Three refusals, in the order a reviewer would want them: an unadmitted boundary, a provider
    whose shape cannot answer the question it claims to, and a missing capability. The shape check
    is against method names rather than ``isinstance`` because these ports describe a contract a
    later module implements in its own classes — an ``isinstance`` test would quietly require
    inheritance from an M03 protocol, which is M03 defining M04's class hierarchy.
    """

    parsed = ExtensionBoundary.parse(boundary, "boundary")
    if provider is None:
        raise PortContractError(
            f"no provider was wired for {parsed.value}, which speaks for {parsed.speaks_for}"
        )
    described = getattr(provider, "descriptor", None)
    if described is None:
        raise PortContractError(
            f"{type(provider).__name__} carries no ProviderDescriptor, so nothing can be checked "
            f"about what it admits at {parsed.value}"
        )
    descriptor = ProviderDescriptor.coerce(described, "descriptor")
    if not isinstance(descriptor, ProviderDescriptor):
        raise SchemaValidationError("descriptor must be a ProviderDescriptor or its payload")
    descriptor.require_admits(parsed)
    _, required = _PORT_SHAPES[parsed]
    absent = [name for name in required if not callable(getattr(provider, name, None))]
    if absent:
        raise PortContractError(
            f"{descriptor.provider_id} claims {parsed.value} but implements no {', '.join(absent)}; "
            "a boundary answered by half a port produces half an answer, which is what §12 exists "
            "to prevent"
        )
    if capability is not None and not descriptor.supports(capability):
        raise PortContractError(
            f"{descriptor.provider_id} does not support capability "
            f"{require_identifier(capability, 'capability')} at {parsed.value}"
        )
    return descriptor


def require_answered_ref(reference: Any, boundary: Any, provider: Any) -> ExtensionRef:
    """Check a citation is aimed at this boundary, has a provider, and that provider may answer."""

    item = ExtensionRef.coerce(reference, "reference")
    if not isinstance(item, ExtensionRef):
        raise SchemaValidationError("reference must be an ExtensionRef or its payload")
    parsed = ExtensionBoundary.parse(boundary, "boundary")
    if item.boundary != parsed.value:
        raise RefError(
            f"{item.text} is a {item.boundary} citation and this call answers {parsed.value}"
        )
    descriptor = require_port(provider, parsed)
    item.require_resolvable(f"ask {descriptor.provider_id} about {item.text}")
    if item.provider_id != descriptor.provider_id:
        raise RefError(
            f"{item.text} was minted by {item.provider_id} and this call would send it to "
            f"{descriptor.provider_id}; a handle belongs to the provider that issued it"
        )
    return item
