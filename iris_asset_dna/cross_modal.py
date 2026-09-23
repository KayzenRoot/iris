"""Revision-pinned cross-domain links and reusable scene identity composition."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import (
    DNAFamily,
    LinkFreshness,
    LinkRequirement,
    ObligationExpectation,
)
from .errors import DNAAdmissionError, DNAIntegrityError, DNAValidationError
from .identity import DNARevisionRef
from .versions import require_identifier, require_semantic_path, require_text, require_version

__all__ = [
    "LinkedDomainDNARef",
    "MotionDNALink",
    "VoiceDNALink",
    "BrandDNALink",
    "IdentityRoleSlot",
    "SceneIdentityMember",
    "SceneIdentityDNA",
    "CrossModalIdentityObligation",
    "CrossModalIdentityBinding",
    "CrossModalEdge",
    "CrossModalDNAGraph",
    "revision_node_ref",
    "validate_scene_identity",
    "validate_crossmodal_binding",
    "validate_crossmodal_graph",
]


@dataclass(frozen=True)
class LinkedDomainDNARef(CanonicalRecord):
    link_id: str
    owner_module: str
    family: str
    external_dna_id: str
    revision_id: str
    version: str
    requirement: LinkRequirement
    bound_trait_paths: tuple[str, ...]
    preservation_obligations: tuple[str, ...]
    expectation: ObligationExpectation = ObligationExpectation.EXACT
    freshness: LinkFreshness = LinkFreshness.CURRENT
    validity_ref: SemanticRef | None = None
    policy_refs: tuple[SemanticRef, ...] = ()
    rights_refs: tuple[SemanticRef, ...] = ()
    provenance_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        for name in ("link_id", "owner_module", "family", "external_dna_id", "revision_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        if self.revision_id.casefold() == "latest":
            raise DNAAdmissionError("canonical external DNA refs cannot use implicit latest")
        object.__setattr__(self, "version", require_version(self.version, "version"))
        for name, enum_type in (
            ("requirement", LinkRequirement),
            ("expectation", ObligationExpectation),
            ("freshness", LinkFreshness),
        ):
            value = getattr(self, name)
            if not isinstance(value, enum_type):
                object.__setattr__(self, name, enum_type(value))
        for name in ("bound_trait_paths", "preservation_obligations"):
            values = tuple(sorted({require_semantic_path(item, f"{name}[]") for item in getattr(self, name)}))
            object.__setattr__(self, name, values)
        if self.validity_ref is not None and not isinstance(self.validity_ref, SemanticRef):
            raise DNAValidationError("validity_ref must be a SemanticRef")
        for name in ("policy_refs", "rights_refs", "provenance_refs"):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))

    @property
    def pinned_ref(self) -> SemanticRef:
        return SemanticRef(
            self.owner_module,
            self.family,
            self.external_dna_id,
            self.version,
            revision_id=self.revision_id,
        )

    def validate_required_freshness(self) -> None:
        if self.requirement is LinkRequirement.REQUIRED and self.freshness is not LinkFreshness.CURRENT:
            raise DNAAdmissionError(
                f"required external DNA link {self.link_id} is {self.freshness.value.lower()}"
            )


@dataclass(frozen=True)
class MotionDNALink(CanonicalRecord):
    reference: LinkedDomainDNARef
    motion_role: str
    body_component_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_domain_link(self.reference, "m30", "motion.dna")
        object.__setattr__(self, "motion_role", require_identifier(self.motion_role, "motion_role"))
        object.__setattr__(self, "body_component_paths", tuple(sorted({require_semantic_path(p) for p in self.body_component_paths})))


@dataclass(frozen=True)
class VoiceDNALink(CanonicalRecord):
    reference: LinkedDomainDNARef
    voice_role: str
    language_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_domain_link(self.reference, "m40", "voice.dna")
        object.__setattr__(self, "voice_role", require_identifier(self.voice_role, "voice_role"))
        object.__setattr__(self, "language_scope", tuple(sorted({require_identifier(item, "language_scope[]") for item in self.language_scope})))


@dataclass(frozen=True)
class BrandDNALink(CanonicalRecord):
    reference: LinkedDomainDNARef
    brand_role: str
    association_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_domain_link(self.reference, "m46", "brand.dna")
        object.__setattr__(self, "brand_role", require_identifier(self.brand_role, "brand_role"))
        object.__setattr__(self, "association_paths", tuple(sorted({require_semantic_path(p) for p in self.association_paths})))


def _require_domain_link(reference: LinkedDomainDNARef, owner: str, family: str) -> None:
    if not isinstance(reference, LinkedDomainDNARef):
        raise DNAValidationError("domain link wrapper requires LinkedDomainDNARef")
    if reference.owner_module != owner or reference.family != family:
        raise DNAAdmissionError(
            f"domain link must point to {owner}:{family}; got {reference.owner_module}:{reference.family}"
        )
    if reference.revision_id.casefold() == "latest":
        raise DNAAdmissionError("canonical domain DNA links must pin a revision and cannot use latest")


@dataclass(frozen=True)
class IdentityRoleSlot(CanonicalRecord):
    role_id: str
    accepted_families: tuple[DNAFamily, ...]
    required_trait_paths: tuple[str, ...] = ()
    minimum_members: int = 1
    maximum_members: int = 1
    substitution_policy_ref: SemanticRef | None = None
    allowed_substitute_role_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", require_identifier(self.role_id, "role_id"))
        families = tuple(item if isinstance(item, DNAFamily) else DNAFamily(item) for item in self.accepted_families)
        if not families or len(families) != len(set(families)):
            raise DNAValidationError("accepted_families must be non-empty and unique")
        object.__setattr__(self, "accepted_families", tuple(sorted(families, key=lambda item: item.value)))
        object.__setattr__(self, "required_trait_paths", tuple(sorted({require_semantic_path(p) for p in self.required_trait_paths})))
        if (
            isinstance(self.minimum_members, bool)
            or isinstance(self.maximum_members, bool)
            or not isinstance(self.minimum_members, int)
            or not isinstance(self.maximum_members, int)
            or self.minimum_members < 0
            or self.maximum_members < self.minimum_members
        ):
            raise DNAValidationError("role slot cardinality must satisfy 0 <= minimum <= maximum")
        if self.substitution_policy_ref is not None and not isinstance(self.substitution_policy_ref, SemanticRef):
            raise DNAValidationError("substitution_policy_ref must be a SemanticRef")
        substitutes = tuple(sorted({require_identifier(item, "allowed_substitute_role_ids[]") for item in self.allowed_substitute_role_ids}))
        object.__setattr__(self, "allowed_substitute_role_ids", substitutes)
        if substitutes and self.substitution_policy_ref is None:
            raise DNAAdmissionError("role substitution requires an explicit policy reference")


@dataclass(frozen=True)
class SceneIdentityMember(CanonicalRecord):
    role_id: str
    revision_ref: DNARevisionRef
    family: DNAFamily
    substitution_source_role: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", require_identifier(self.role_id, "role_id"))
        if not isinstance(self.revision_ref, DNARevisionRef):
            raise DNAValidationError("revision_ref must be a DNARevisionRef")
        if not isinstance(self.family, DNAFamily):
            object.__setattr__(self, "family", DNAFamily(self.family))
        if self.substitution_source_role is not None:
            object.__setattr__(self, "substitution_source_role", require_identifier(self.substitution_source_role, "substitution_source_role"))


@dataclass(frozen=True)
class SceneIdentityDNA(CanonicalRecord):
    scene_revision_ref: DNARevisionRef
    role_slots: tuple[IdentityRoleSlot, ...]
    members: tuple[SceneIdentityMember, ...]
    environment_ref: LinkedDomainDNARef | None = None
    scene_ir_projection_ref: SemanticRef | None = None
    canon_refs: tuple[SemanticRef, ...] = ()
    continuity_relations: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.scene_revision_ref, DNARevisionRef):
            raise DNAValidationError("scene_revision_ref must be a DNARevisionRef")
        if self.environment_ref is not None and not isinstance(self.environment_ref, LinkedDomainDNARef):
            raise DNAValidationError("environment_ref must be a LinkedDomainDNARef")
        if self.scene_ir_projection_ref is not None:
            if not isinstance(self.scene_ir_projection_ref, SemanticRef) or self.scene_ir_projection_ref.owner_module != "m04":
                raise DNAAdmissionError("SceneIR projection refs must remain owned by M04")
        slots, members = tuple(self.role_slots), tuple(self.members)
        if any(not isinstance(item, IdentityRoleSlot) for item in slots):
            raise DNAValidationError("role_slots must contain IdentityRoleSlot records")
        if any(not isinstance(item, SceneIdentityMember) for item in members):
            raise DNAValidationError("members must contain SceneIdentityMember records")
        if len({slot.role_id for slot in slots}) != len(slots):
            raise DNAIntegrityError("scene identity contains duplicate role slots")
        object.__setattr__(self, "role_slots", tuple(sorted(slots, key=lambda item: item.role_id)))
        object.__setattr__(self, "members", tuple(sorted(members, key=lambda item: (item.role_id, item.revision_ref.dna_id, item.revision_ref.revision_id))))
        object.__setattr__(self, "canon_refs", require_refs(self.canon_refs, "canon_refs"))
        object.__setattr__(self, "continuity_relations", require_refs(self.continuity_relations, "continuity_relations"))
        self.validate_members()

    def validate_members(self) -> None:
        by_role: dict[str, list[SceneIdentityMember]] = {}
        for member in self.members:
            by_role.setdefault(member.role_id, []).append(member)
        known_roles = {slot.role_id for slot in self.role_slots}
        if set(by_role) - known_roles:
            raise DNAAdmissionError(f"scene members use undeclared role slots: {sorted(set(by_role) - known_roles)}")
        for slot in self.role_slots:
            members = by_role.get(slot.role_id, [])
            if not slot.minimum_members <= len(members) <= slot.maximum_members:
                raise DNAAdmissionError(f"role slot {slot.role_id} violates its declared cardinality")
            for member in members:
                if member.family not in slot.accepted_families:
                    raise DNAAdmissionError(f"member family does not satisfy role slot {slot.role_id}")
                if member.substitution_source_role is not None and (
                    slot.substitution_policy_ref is None
                    or member.substitution_source_role not in slot.allowed_substitute_role_ids
                ):
                    raise DNAAdmissionError(f"role substitution for {slot.role_id} is not governed by policy")


@dataclass(frozen=True)
class CrossModalIdentityObligation(CanonicalRecord):
    obligation_id: str
    participant_link_ids: tuple[str, ...]
    expectation: ObligationExpectation
    required: bool
    evaluator_owner_ref: SemanticRef
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "obligation_id", require_identifier(self.obligation_id, "obligation_id"))
        participants = tuple(sorted({require_identifier(item, "participant_link_ids[]") for item in self.participant_link_ids}))
        if not participants:
            raise DNAValidationError("cross-modal obligation needs at least one participant")
        object.__setattr__(self, "participant_link_ids", participants)
        if not isinstance(self.expectation, ObligationExpectation):
            object.__setattr__(self, "expectation", ObligationExpectation(self.expectation))
        if not isinstance(self.required, bool):
            raise DNAValidationError("required must be a bool")
        if not isinstance(self.evaluator_owner_ref, SemanticRef):
            raise DNAAdmissionError("cross-modal evidence must identify its owning evaluator/authority")
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))


@dataclass(frozen=True)
class CrossModalIdentityBinding(CanonicalRecord):
    binding_id: str
    m05_revision_ref: DNARevisionRef
    domain_links: tuple[LinkedDomainDNARef, ...]
    anchors: tuple[SemanticRef, ...]
    obligations: tuple[CrossModalIdentityObligation, ...]
    provenance_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "binding_id", require_identifier(self.binding_id, "binding_id"))
        if not isinstance(self.m05_revision_ref, DNARevisionRef):
            raise DNAValidationError("m05_revision_ref must be a DNARevisionRef")
        links = tuple(self.domain_links)
        if any(not isinstance(item, LinkedDomainDNARef) for item in links):
            raise DNAValidationError("domain_links must contain LinkedDomainDNARef records")
        if len({item.link_id for item in links}) != len(links):
            raise DNAIntegrityError("cross-modal binding contains duplicate domain link IDs")
        object.__setattr__(self, "domain_links", tuple(sorted(links, key=lambda item: item.link_id)))
        object.__setattr__(self, "anchors", require_refs(self.anchors, "anchors"))
        obligations = tuple(self.obligations)
        if any(not isinstance(item, CrossModalIdentityObligation) for item in obligations):
            raise DNAValidationError("obligations must contain CrossModalIdentityObligation records")
        object.__setattr__(self, "obligations", tuple(sorted(obligations, key=lambda item: item.obligation_id)))
        object.__setattr__(self, "provenance_refs", require_refs(self.provenance_refs, "provenance_refs"))
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))


@dataclass(frozen=True)
class CrossModalEdge(CanonicalRecord):
    edge_id: str
    relation: str
    source_ref: SemanticRef
    target_ref: SemanticRef
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_id", require_identifier(self.edge_id, "edge_id"))
        relation = require_text(self.relation, "relation", maximum=64).upper()
        allowed = {
            "HAS_MOTION_IDENTITY", "HAS_VOICE_IDENTITY", "BOUND_TO_BRAND",
            "MEMBER_OF_SCENE_IDENTITY", "PERFORMS_ROLE", "REPRESENTED_BY",
        }
        if relation not in allowed:
            raise DNAAdmissionError("CrossModalDNAGraph accepts identity-link edges only")
        object.__setattr__(self, "relation", relation)
        if not isinstance(self.source_ref, SemanticRef) or not isinstance(self.target_ref, SemanticRef):
            raise DNAValidationError("graph edges require typed semantic refs")
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))


@dataclass(frozen=True)
class CrossModalDNAGraph(CanonicalRecord):
    graph_id: str
    revision_refs: tuple[DNARevisionRef, ...]
    edges: tuple[CrossModalEdge, ...]
    schema_version: str = "iris-m05-crossmodal-v1"
    external_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        refs = tuple(self.revision_refs)
        if any(not isinstance(item, DNARevisionRef) for item in refs):
            raise DNAValidationError("revision_refs must contain DNARevisionRef values")
        if len({(item.dna_id, item.revision_id) for item in refs}) != len(refs):
            raise DNAIntegrityError("cross-modal graph contains duplicate revision nodes")
        object.__setattr__(self, "revision_refs", tuple(sorted(refs)))
        edges = tuple(self.edges)
        if any(not isinstance(item, CrossModalEdge) for item in edges):
            raise DNAValidationError("edges must contain CrossModalEdge values")
        if len({item.edge_id for item in edges}) != len(edges):
            raise DNAIntegrityError("cross-modal graph contains duplicate edge IDs")
        object.__setattr__(self, "edges", tuple(sorted(edges, key=lambda item: item.edge_id)))
        object.__setattr__(self, "schema_version", require_version(self.schema_version, "schema_version"))
        object.__setattr__(self, "external_refs", require_refs(self.external_refs, "external_refs"))
        validate_crossmodal_graph(self)


def revision_node_ref(revision_ref: DNARevisionRef) -> SemanticRef:
    if not isinstance(revision_ref, DNARevisionRef):
        raise DNAValidationError("revision_node_ref requires a pinned DNARevisionRef")
    return SemanticRef(
        "m05",
        "dna.revision",
        revision_ref.dna_id,
        "m05-contract-v1.0",
        revision_id=revision_ref.revision_id,
        content_digest=revision_ref.revision_digest,
    )


def validate_crossmodal_binding(binding: CrossModalIdentityBinding) -> None:
    if not isinstance(binding, CrossModalIdentityBinding):
        raise DNAValidationError("binding must be a CrossModalIdentityBinding")
    links = {item.link_id: item for item in binding.domain_links}
    for link in binding.domain_links:
        link.validate_required_freshness()
    for obligation in binding.obligations:
        missing = set(obligation.participant_link_ids) - set(links)
        if missing and obligation.required:
            raise DNAAdmissionError(f"required cross-modal participants are missing: {sorted(missing)}")
        for link_id in obligation.participant_link_ids:
            link = links.get(link_id)
            if link is not None and obligation.required and link.freshness is not LinkFreshness.CURRENT:
                raise DNAAdmissionError(f"required cross-modal link {link_id} is not current")


def validate_scene_identity(
    scene: SceneIdentityDNA,
    revisions: tuple[object, ...],
) -> None:
    """Bind each role member to its exact revision and satisfy the role's trait contract."""
    from .identity import DNARevision

    if not isinstance(scene, SceneIdentityDNA):
        raise DNAValidationError("scene must be a SceneIdentityDNA")
    by_ref: dict[DNARevisionRef, DNARevision] = {}
    for revision in revisions:
        if not isinstance(revision, DNARevision):
            raise DNAValidationError("revisions must contain DNARevision records")
        if revision.ref in by_ref:
            raise DNAIntegrityError("scene validation received duplicate immutable revision refs")
        by_ref[revision.ref] = revision
    scene_revision = by_ref.get(scene.scene_revision_ref)
    if scene_revision is None or scene_revision.family is not DNAFamily.SCENE:
        raise DNAAdmissionError("SceneIdentityDNA must bind its exact M05 scene-identity revision")
    slots = {slot.role_id: slot for slot in scene.role_slots}
    for member in scene.members:
        revision = by_ref.get(member.revision_ref)
        if revision is None:
            raise DNAAdmissionError(f"scene member {member.role_id} references an unavailable pinned revision")
        if revision.family is not member.family:
            raise DNAIntegrityError(f"scene member {member.role_id} family does not match the pinned revision")
        missing = set(slots[member.role_id].required_trait_paths) - set(revision.trait_map())
        if missing:
                raise DNAAdmissionError(f"scene role {member.role_id} is missing required identity traits: {sorted(missing)}")


def validate_crossmodal_graph(graph: CrossModalDNAGraph) -> None:
    if not isinstance(graph, CrossModalDNAGraph):
        raise DNAValidationError("graph must be a CrossModalDNAGraph")
    nodes = {revision_node_ref(item) for item in graph.revision_refs} | set(graph.external_refs)
    for edge in graph.edges:
        if edge.source_ref not in nodes or edge.target_ref not in nodes:
            raise DNAAdmissionError(f"cross-modal edge {edge.edge_id} references an undeclared identity node")
        if edge.relation in {"HAS_MOTION_IDENTITY", "HAS_VOICE_IDENTITY", "BOUND_TO_BRAND", "MEMBER_OF_SCENE_IDENTITY", "PERFORMS_ROLE", "REPRESENTED_BY"}:
            if edge.source_ref.owner_module != "m05":
                raise DNAAdmissionError("cross-modal identity edges must originate at an M05 identity node")
        target_owner_family = {
            "HAS_MOTION_IDENTITY": ("m30", "motion.dna"),
            "HAS_VOICE_IDENTITY": ("m40", "voice.dna"),
            "BOUND_TO_BRAND": ("m46", "brand.dna"),
            "MEMBER_OF_SCENE_IDENTITY": ("m05", "scene.identity"),
            "PERFORMS_ROLE": ("m05", "scene.role"),
        }.get(edge.relation)
        if target_owner_family is not None and (
            edge.target_ref.owner_module,
            edge.target_ref.family,
        ) != target_owner_family:
            raise DNAAdmissionError(f"cross-modal edge {edge.edge_id} violates its external authority boundary")
        if edge.relation == "REPRESENTED_BY" and edge.target_ref.owner_module != "m04":
            raise DNAAdmissionError("representation edges remain owned by M04")
