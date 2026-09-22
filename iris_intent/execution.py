"""F-M03-10 S04 provider-neutral execution intent.

S03 decided what M01 must be able to judge. S04 decides what kind of production *behaviour* the
brief requires — and stops there. The canonical artifact is an :class:`ExecutionIntentBundle`: a
statement of desired transformation, required capability, protected semantics and the explanation
path behind each of them. It is not a prompt, not a workflow, not an M02 ``ExecutionPlan``, and it
carries no field that could be mistaken for one.

Three structural choices carry most of the safety:

*Provider vocabulary is refused at the type boundary.* §7 forbids model checkpoint names, node
identifiers, DCC operators, endpoints, sampler names, accelerator choices, host ids, regions,
queue names and prompt-weight syntax from entering canonical execution semantics. A deny-list is
an honesty about what it can catch, so the check is versioned (:data:`PROVIDER_VOCABULARY_VERSION`)
and recorded in every fingerprint: a bundle compiled under an older vocabulary guard stays
distinguishable, and the guard is auditable rather than folklore.

*Availability is an observation, never an input to meaning.* Whether some provider can satisfy a
capability decides the bundle's *status* and produces gaps; it does not touch the fingerprint
(§20). That is what lets one bundle stay valid while execution strategy moves from a local box to
a cloud farm, and what makes "the provider cannot do it, so ask for less" unrepresentable rather
than merely discouraged (§8, D-M03-S04-004).

*Unmet requirements become gaps that keep their source.* A mandatory capability nobody can serve
is recorded with the refs that demanded it. Rewriting the intent to fit a weaker provider would
produce a bundle that reads as satisfiable while asking for less than the brief said.

The bundle also cannot authorize what M02 and M59 own: :class:`SideEffectClass` can express "this
should be published" and the approval boundary it needs, and nothing in this module can grant it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .errors import AdmissionRefusedError, CapabilityGapError, SchemaValidationError
from .identity import RefKind, SemanticRef, require_bound_ref
from .limits import (
    MAX_CAPABILITY_DEMANDS,
    MAX_ENTRIES_PER_FIELD,
    MAX_MUTATION_TARGETS,
    MAX_OBSERVATION_REFS,
    MAX_OPERATIONS_PER_BUNDLE,
    MAX_PROVENANCE_REFS,
    MAX_SCOPE_PATHS,
)
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    content_digest,
    require_contract_version,
    require_digest,
    require_identifier,
    require_semantic_path,
    require_text,
    require_unit_interval,
    require_version_text,
)

__all__ = [
    "BRANCH_POLICIES",
    "EXECUTION_COMPILER_VERSION",
    "FINGERPRINT_EXCLUSIONS",
    "PROVIDER_PHRASES",
    "PROVIDER_TERMS",
    "PROVIDER_VOCABULARY_VERSION",
    "BranchPolicy",
    "CapabilityDemand",
    "ExecutionGapClass",
    "ExecutionIntentBundle",
    "ExecutionIntentChangeClass",
    "ExecutionIntentDelta",
    "ExecutionIntentFingerprint",
    "ExecutionIntentGap",
    "ExecutionIntentSlice",
    "ExecutionIntentStatus",
    "ExplorationIntent",
    "ExplorationShape",
    "IntentCompletionSemantics",
    "IntentOperation",
    "IntentOperationFamily",
    "ProviderTranslationItem",
    "ProviderTranslationReceipt",
    "SemanticLossClass",
    "SemanticLossRule",
    "SemanticMutationClass",
    "SemanticMutationEnvelope",
    "SideEffectClass",
    "TranslationDisposition",
    "canonical_execution_digest",
    "compile_execution_intent",
    "execution_intent_delta",
    "execution_slice_for",
    "fingerprint_of_execution_intent",
    "find_provider_vocabulary",
    "reject_provider_admission",
    "reject_provider_vocabulary",
    "require_complete_execution_intent",
]

#: Versioned identity of this compiler, recorded in every fingerprint.
EXECUTION_COMPILER_VERSION = "m03-execution-compiler-v1"

#: Version of the §7 deny-list itself. Recording it is the difference between a guard someone can
#: audit and a filter nobody can date: vocabulary that was acceptable to an older guard must not
#: silently pass as though it had been checked by the current one.
PROVIDER_VOCABULARY_VERSION = "m03-provider-vocabulary-v1"


# --------------------------------------------------------------------------- #
# §7: the vocabulary that may not become canonical meaning
# --------------------------------------------------------------------------- #

#: Exact words that name an implementation rather than a semantic demand. Matched as whole tokens
#: after normalization, so ``capability`` is not caught by the ``abi`` inside it. Only unambiguous
#: names belong here: an over-eager list refuses legitimate semantics, and a refusal that fires on
#: ordinary English teaches integrators to route around the guard, which is worse than the gap.
PROVIDER_TERMS: frozenset[str] = frozenset(
    {
        "aws",
        "azure",
        "blender",
        "ckpt",
        "comfy",
        "comfyui",
        "controlnet",
        "cuda",
        "diffusers",
        "directml",
        "gcp",
        "gpt",
        "gpu",
        "houdini",
        "ipadapter",
        "lora",
        "maya",
        "midjourney",
        "nuke",
        "nvidia",
        "peft",
        "rocm",
        "runway",
        "sdxl",
        "seedream",
        "sora",
        "t5",
        "transformers",
        "unet",
        "vae",
        "vram",
    }
)

#: Multi-word or punctuation-bearing names that token equality cannot catch, including the
#: runtime-topology shapes §7 forbids (regions, buckets, endpoints), which are identifiable by
#: their form rather than by an ordinary word that would also appear in prose.
PROVIDER_PHRASES: frozenset[str] = frozenset(
    {
        "clip_vision",
        "clip-vision",
        "dall-e",
        "dalle-3",
        "elevenlabs",
        "huggingface",
        "k-sampler",
        "k_sampler",
        "ksampler",
        "model checkpoint",
        "prompt weight",
        "runwayml",
        "s3://",
        "safe-tensors",
        "safetensors",
        "stable diffusion",
        "stable-diffusion",
        "us-east-",
        "us-west-",
        "eu-central-",
        "worker-host-",
        "queue-",
    }
)

#: Prompt-weight and parameter syntax, which is a provider dialect rather than a semantic claim.
PROMPT_SYNTAX: tuple[str, ...] = (
    "--ar",
    "--no",
    "--seed",
    "::",
    ":1.",
    "((",
    "))",
)


def _normalize(text: str) -> str:
    return "".join(character if character.isalnum() else " " for character in text).lower()


def find_provider_vocabulary(value: Any) -> tuple[str, ...]:
    """Every provider-facing term found anywhere inside ``value``, sorted.

    Exposed for tests and audits rather than kept private: proof item 2 is a claim about the
    payload, and a claim nobody can re-check is a claim about the implementation.
    """

    strings: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, Mapping):
            for key, nested in item.items():
                if isinstance(key, str):
                    strings.append(key)
                walk(nested)
        elif isinstance(item, (list, tuple, set, frozenset)):
            for nested in item:
                walk(nested)

    walk(value)
    found: set[str] = set()
    for text in strings:
        lowered = text.lower()
        tokens = set(_normalize(text).split())
        found |= {term for term in PROVIDER_TERMS if term in tokens}
        found |= {phrase for phrase in PROVIDER_PHRASES if phrase in lowered}
        found |= {marker for marker in PROMPT_SYNTAX if marker in lowered}
    return tuple(sorted(found))


def reject_provider_vocabulary(value: Any, field_name: str) -> None:
    """Refuse canonical semantics that name an implementation (§7, D-M03-S04-002).

    The refusal is loud and names the offending terms, because a silent normalization would let a
    provider name through in whichever field nobody thought to check.
    """

    found = find_provider_vocabulary(value)
    if found:
        raise SchemaValidationError(
            f"{field_name} carries provider or runtime vocabulary {list(found)}, which §7 keeps out "
            "of canonical execution intent; name the capability the production needs and let a later "
            "compiler choose the implementation"
        )


# --------------------------------------------------------------------------- #
# §4, §5: operations
# --------------------------------------------------------------------------- #


class IntentOperationFamily(Labeled):
    """The ten semantic verbs S04 admits.

    These describe *what kind of change is wanted*, not how many graph nodes it takes. A family
    that implied a workflow shape would be M03 deciding M16's job through a field name.
    """

    CREATE = "CREATE"
    TRANSFORM = "TRANSFORM"
    COMPOSE = "COMPOSE"
    EXTEND = "EXTEND"
    REPAIR = "REPAIR"
    VARIATE = "VARIATE"
    SELECT = "SELECT"
    VALIDATE = "VALIDATE"
    PACKAGE = "PACKAGE"
    LOCALIZE = "LOCALIZE"

    @property
    def mutates_existing(self) -> bool:
        """Whether this family changes something that already exists.

        §12's reason for requiring a mutation envelope: a verb that edits an admitted subject can
        destroy the properties the brief protected, and only a verb that leaves the subject alone
        cannot.
        """

        return self in {
            IntentOperationFamily.TRANSFORM,
            IntentOperationFamily.REPAIR,
            IntentOperationFamily.VARIATE,
            IntentOperationFamily.EXTEND,
        }

    @property
    def requires_envelope(self) -> bool:
        return self in {
            IntentOperationFamily.TRANSFORM,
            IntentOperationFamily.REPAIR,
            IntentOperationFamily.VARIATE,
        }

    @property
    def requires_subject(self) -> bool:
        """Whether the operation is *about* something already governed.

        ``CREATE`` synthesizes a new governed subject, so it names a desired output type instead;
        every other verb operates on something the brief already admits, and an operation with no
        subject would be a demand for unattributed work.
        """

        return self is not IntentOperationFamily.CREATE

    @property
    def judges_rather_than_produces(self) -> bool:
        return self in {IntentOperationFamily.VALIDATE, IntentOperationFamily.SELECT}


class SemanticMutationClass(Labeled):
    """Families of semantic change an operation may permit or forbid.

    §5 asks for allowed and forbidden mutation classes without defining the alphabet, so this is
    M03's own provider-neutral one: axes a brief can care about, named the way the brief names
    them. Nothing here maps to a model control — "material" is a property of the work, not a knob.
    """

    IDENTITY = "IDENTITY"
    ANATOMY = "ANATOMY"
    GEOMETRY = "GEOMETRY"
    TOPOLOGY = "TOPOLOGY"
    SILHOUETTE = "SILHOUETTE"
    MATERIAL = "MATERIAL"
    TEXTURE = "TEXTURE"
    COLOR = "COLOR"
    LIGHTING = "LIGHTING"
    COMPOSITION = "COMPOSITION"
    CAMERA = "CAMERA"
    STYLE = "STYLE"
    BRAND = "BRAND"
    MOTION = "MOTION"
    TEMPORAL = "TEMPORAL"
    SPEECH = "SPEECH"
    VOICE = "VOICE"
    TEXT_LAYOUT = "TEXT_LAYOUT"
    AUDIO_MIX = "AUDIO_MIX"
    PLATFORM_FIT = "PLATFORM_FIT"
    METADATA = "METADATA"


class IntentCompletionSemantics(Labeled):
    """What "done" means for this operation, at the level of intent.

    Deliberately free of counts: how many candidates to try is a scheduling decision, and an
    intent that said "twelve" would be a compute budget wearing an obligation's clothes (§11).
    """

    ONE_SUFFICIENT_OUTPUT = "ONE_SUFFICIENT_OUTPUT"
    ALL_DECLARED_TARGETS = "ALL_DECLARED_TARGETS"
    EXPLICIT_SELECTION = "EXPLICIT_SELECTION"
    EXHAUST_WITHIN_ZONE = "EXHAUST_WITHIN_ZONE"

    @property
    def needs_a_choice(self) -> bool:
        """Whether completion requires somebody to pick, and therefore cannot self-certify."""

        return self is IntentCompletionSemantics.EXPLICIT_SELECTION


class SideEffectClass(Labeled):
    """How the result is meant to leave the system (§13).

    The classification is M03's; the authorization is not. ``EXTERNAL_PUBLICATION`` says the brief
    wants something published and therefore that an approval boundary stands in front of it — it
    never says the boundary has been crossed.
    """

    INTERNAL_MATERIALIZATION = "INTERNAL_MATERIALIZATION"
    CONTROLLED_EXPORT = "CONTROLLED_EXPORT"
    EXTERNAL_PUBLICATION = "EXTERNAL_PUBLICATION"

    @property
    def leaves_the_system(self) -> bool:
        return self is not SideEffectClass.INTERNAL_MATERIALIZATION

    @property
    def requires_governed_approval(self) -> bool:
        return self in {SideEffectClass.CONTROLLED_EXPORT, SideEffectClass.EXTERNAL_PUBLICATION}


class ExplorationShape(Labeled):
    """How wide the search should reach, as a shape rather than a number (§11)."""

    BROAD = "BROAD"
    NARROW = "NARROW"
    STRUCTURED = "STRUCTURED"


class BranchPolicy(Labeled):
    """Whether exploratory branches stand alone or refine one another (§11)."""

    INDEPENDENT = "INDEPENDENT"
    PROGRESSIVE = "PROGRESSIVE"


BRANCH_POLICIES = tuple(item.value for item in BranchPolicy)


class SemanticLossClass(Labeled):
    """One obligation's disposition under provider translation (§9).

    There is no aggregate meaning-loss score, on purpose: a single number would let a large
    approximation on one axis pay for an exactness requirement on another, which is not how any
    brief was ever written. Each obligation carries its own class and its own evidence expectation.
    """

    LOSSLESS_REQUIRED = "LOSSLESS_REQUIRED"
    BOUNDED_APPROXIMATION = "BOUNDED_APPROXIMATION"
    CREATIVE_FREEDOM = "CREATIVE_FREEDOM"
    ADVISORY = "ADVISORY"

    @property
    def requires_tolerance(self) -> bool:
        """Whether the class is meaningless without a stated bound.

        "Approximate it, within reasons" is a policy; "approximate it" is a licence. The tolerance
        has to be an admitted ref so a later reader can find the number that was agreed.
        """

        return self is SemanticLossClass.BOUNDED_APPROXIMATION

    @property
    def may_be_dropped(self) -> bool:
        return self is SemanticLossClass.ADVISORY

    @property
    def is_freedom(self) -> bool:
        return self is SemanticLossClass.CREATIVE_FREEDOM


class TranslationDisposition(Labeled):
    """What a provider compiler says it did with one semantic obligation (§10)."""

    REPRESENTED_EXACTLY = "REPRESENTED_EXACTLY"
    REPRESENTED_WITH_TOLERANCE = "REPRESENTED_WITH_TOLERANCE"
    DELEGATED_TO_VALIDATOR = "DELEGATED_TO_VALIDATOR"
    UNSUPPORTED = "UNSUPPORTED"
    INTENTIONALLY_IRRELEVANT = "INTENTIONALLY_IRRELEVANT"

    @property
    def satisfies_lossless(self) -> bool:
        """Whether this answer can stand behind a LOSSLESS_REQUIRED obligation.

        Only an exact representation, or a delegation to something that will check the exactness
        externally. "Approximated it" and "not my step" are both true statements about work that
        still has to be done.
        """

        return self in {
            TranslationDisposition.REPRESENTED_EXACTLY,
            TranslationDisposition.DELEGATED_TO_VALIDATOR,
        }

    @property
    def asserts_capability(self) -> bool:
        """Whether the answer claims the provider can do it.

        Used to decide whether the item may carry a capability claim at all: an
        ``INTENTIONALLY_IRRELEVANT`` item that also asserts a capability is self-contradictory.
        """

        return self in {
            TranslationDisposition.REPRESENTED_EXACTLY,
            TranslationDisposition.REPRESENTED_WITH_TOLERANCE,
            TranslationDisposition.DELEGATED_TO_VALIDATOR,
        }


class ExecutionGapClass(Labeled):
    """The §8 gap vocabulary, exactly.

    ``PROVIDER_TRANSLATION_LOSS`` and ``STALE_PROVIDER_CAPABILITY`` are the two that arrive from
    outside: a translation that lost meaning, or an advertised capability that has since gone
    stale. Both are observations M03 records — neither is something M03 repairs by editing intent.
    """

    MISSING_CAPABILITY = "MISSING_CAPABILITY"
    UNREPRESENTABLE_CONSTRAINT = "UNREPRESENTABLE_CONSTRAINT"
    INSUFFICIENT_REFERENCE_SUPPORT = "INSUFFICIENT_REFERENCE_SUPPORT"
    NO_QUALITY_EVIDENCE_PATH = "NO_QUALITY_EVIDENCE_PATH"
    SEMANTIC_TYPE_UNSUPPORTED = "SEMANTIC_TYPE_UNSUPPORTED"
    PROTECTED_ANCHOR_UNSUPPORTED = "PROTECTED_ANCHOR_UNSUPPORTED"
    SIDE_EFFECT_POLICY_UNRESOLVED = "SIDE_EFFECT_POLICY_UNRESOLVED"
    PROVIDER_TRANSLATION_LOSS = "PROVIDER_TRANSLATION_LOSS"
    STALE_PROVIDER_CAPABILITY = "STALE_PROVIDER_CAPABILITY"

    @property
    def observational(self) -> bool:
        """Whether the gap is a report about the world rather than a hole in this bundle.

        Observational gaps say "the requirement stands and here is what could not serve it".
        Structural gaps say "this bundle does not yet express what the brief asks", and only the
        structural kind can be closed by recompiling from the same brief.
        """

        return self in {
            ExecutionGapClass.PROVIDER_TRANSLATION_LOSS,
            ExecutionGapClass.STALE_PROVIDER_CAPABILITY,
        }


class ExecutionIntentStatus(Labeled):
    """Whether the bundle expresses everything the brief asked for."""

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"

    @property
    def fully_represented(self) -> bool:
        return self is ExecutionIntentStatus.COMPLETE


class ExecutionIntentChangeClass(Labeled):
    """How an execution-intent revision moved, as a class M02/M04/M16 can act on (§21).

    ``EXPLANATION_ONLY_CHANGE`` is the interesting one: it says the reasoning text was restated
    while every semantic claim held, so a downstream provider recompilation would be work done to
    produce the same answer.
    """

    NO_SEMANTIC_CHANGE = "NO_SEMANTIC_CHANGE"
    OPERATION_ADDED_REMOVED = "OPERATION_ADDED_REMOVED"
    CAPABILITY_DEMAND_CHANGE = "CAPABILITY_DEMAND_CHANGE"
    MUTATION_ENVELOPE_CHANGE = "MUTATION_ENVELOPE_CHANGE"
    PROTECTED_ANCHOR_CHANGE = "PROTECTED_ANCHOR_CHANGE"
    QUALITY_CONTRACT_REF_CHANGE = "QUALITY_CONTRACT_REF_CHANGE"
    DELIVERABLE_INTENT_CHANGE = "DELIVERABLE_INTENT_CHANGE"
    EXPLANATION_ONLY_CHANGE = "EXPLANATION_ONLY_CHANGE"

    @property
    def requires_provider_recompilation(self) -> bool:
        """Whether a provider compiler may not reuse what it already translated.

        Explanation-only and no-change revisions keep their translations valid; everything else
        changed something a workflow was built around.
        """

        return self not in {
            ExecutionIntentChangeClass.NO_SEMANTIC_CHANGE,
            ExecutionIntentChangeClass.EXPLANATION_ONLY_CHANGE,
        }


@dataclass(frozen=True)
class ExecutionIntentGap(Record):
    """One requirement this bundle could not attach to any satisfiable demand (§8).

    ``source_refs`` are required for the same reason as in S03: a gap that cannot name the
    requirement behind it is indistinguishable from a requirement that was quietly dropped.
    """

    gap_id: str
    class_name: str
    detail: str
    source_refs: tuple[SemanticRef, ...] = ()
    semantic_path: str | None = None
    capability_id: str | None = None
    operation_id: str | None = None
    anchor_ref: SemanticRef | None = None
    mandatory_origin: bool = True
    remedy: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_id", require_identifier(self.gap_id, "gap_id"))
        kind = ExecutionGapClass.parse(self.class_name, "class_name")
        object.__setattr__(self, "class_name", kind.value)
        refs = tuple(
            sorted(
                (SemanticRef.coerce(item, "source_refs[]") for item in (self.source_refs or ())),
                key=lambda item: item.text,
            )
        )
        if not refs:
            raise SchemaValidationError(
                f"gap {self.gap_id} names no source; §8's promise is that a gap keeps the "
                "requirement that produced it, and an unsourced gap is how that promise breaks"
            )
        if len(refs) > MAX_PROVENANCE_REFS:
            raise SchemaValidationError(
                f"gap {self.gap_id} cites {len(refs)} sources, above {MAX_PROVENANCE_REFS}"
            )
        object.__setattr__(self, "source_refs", refs)
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=1024))
        if self.semantic_path is not None:
            object.__setattr__(
                self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path")
            )
        if self.capability_id is not None:
            object.__setattr__(
                self, "capability_id", require_identifier(self.capability_id, "capability_id")
            )
        if self.operation_id is not None:
            object.__setattr__(
                self, "operation_id", require_identifier(self.operation_id, "operation_id")
            )
        if self.anchor_ref is not None:
            object.__setattr__(
                self,
                "anchor_ref",
                require_bound_ref(self.anchor_ref, "anchor_ref", kind=RefKind.ANCHOR),
            )
        if kind is ExecutionGapClass.MISSING_CAPABILITY and self.capability_id is None:
            raise SchemaValidationError(
                f"gap {self.gap_id} reports a missing capability without naming it; 'some capability "
                "is absent' cannot be handed to a routing module as a work item"
            )
        if kind is ExecutionGapClass.PROTECTED_ANCHOR_UNSUPPORTED and self.anchor_ref is None:
            raise SchemaValidationError(
                f"gap {self.gap_id} reports an unsupported protected anchor without naming which"
            )
        if not isinstance(self.mandatory_origin, bool):
            raise SchemaValidationError("mandatory_origin must be a boolean")
        if self.remedy is not None:
            object.__setattr__(self, "remedy", require_text(self.remedy, "remedy", maximum=512))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def class_enum(self) -> ExecutionGapClass:
        return ExecutionGapClass.parse(self.class_name)

    @property
    def blocks_completion(self) -> bool:
        return self.mandatory_origin

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "class": self.class_name,
            "capability": self.capability_id,
            "operation": self.operation_id,
            "mandatory": self.mandatory_origin,
            "sources": sorted(item.text for item in self.source_refs),
        }


ExecutionIntentGap.NESTED = {
    "source_refs": of(SemanticRef),
    "anchor_ref": of(SemanticRef),
}


@dataclass(frozen=True)
class CapabilityDemand(Record):
    """A required capability, stated as what the work must be able to do (§6).

    The id is a semantic slug — ``identity-preserving-image-synthesis``, not a vendor's model
    name — and the slug is checked against §7 at construction. Provider registries later
    advertise which demands they can serve; that answer is an observation about the world and
    never enters this record, because the same demand has to mean the same thing on a machine
    that can serve it and on one that cannot.
    """

    demand_id: str
    capability_id: str
    label: str
    mandatory: bool = True
    semantic_scope: tuple[str, ...] = ()
    input_type_refs: tuple[SemanticRef, ...] = ()
    output_type_refs: tuple[SemanticRef, ...] = ()
    fidelity_contract_refs: tuple[SemanticRef, ...] = ()
    preserved_constraint_refs: tuple[SemanticRef, ...] = ()
    protected_anchor_refs: tuple[SemanticRef, ...] = ()
    expected_evidence: tuple[str, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    source_refs: tuple[SemanticRef, ...] = ()
    notes: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "demand_id", require_identifier(self.demand_id, "demand_id"))
        capability = require_identifier(self.capability_id, "capability_id")
        reject_provider_vocabulary(capability, "capability_id")
        object.__setattr__(self, "capability_id", capability)
        object.__setattr__(self, "label", require_text(self.label, "label", maximum=200))
        if not isinstance(self.mandatory, bool):
            raise SchemaValidationError("mandatory must be a boolean")
        scope = _paths(self.semantic_scope, "semantic_scope")
        if not scope:
            raise SchemaValidationError(
                f"demand {self.demand_id} declares no semantic scope; an unscoped capability demand "
                "would be a request to make the whole production able to do it"
            )
        object.__setattr__(self, "semantic_scope", scope)
        for name in (
            "input_type_refs",
            "output_type_refs",
            "fidelity_contract_refs",
            "preserved_constraint_refs",
            "protected_anchor_refs",
            "policy_refs",
            "source_refs",
        ):
            object.__setattr__(self, name, _refs(getattr(self, name), name))
        if not self.source_refs:
            raise SchemaValidationError(
                f"demand {self.demand_id} cites no source; D-M03-S04-012 requires every capability "
                "demand to have an explanation path to admitted semantics or policy"
            )
        if not self.input_type_refs and not self.output_type_refs:
            raise SchemaValidationError(
                f"demand {self.demand_id} names neither an input nor an output semantic type; a "
                "capability that changes nothing and produces nothing cannot be routed to anything"
            )
        evidence = tuple(
            sorted({_text(item, "expected_evidence[]") for item in (self.expected_evidence or ())})
        )
        object.__setattr__(self, "expected_evidence", evidence)
        if self.notes is not None:
            reject_provider_vocabulary(self.notes, "notes")
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))
        reject_provider_vocabulary(self.label, "label")
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        reject_provider_vocabulary(self.metadata, "metadata")
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def blocking(self) -> bool:
        """Whether an unservable demand stops the bundle.

        An optional demand the world cannot serve is information; a mandatory one is a requirement
        with no path, and §8 keeps it in the record instead of relaxing it.
        """

        return self.mandatory

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "mandatory": self.mandatory,
            "scope": list(self.semantic_scope),
            "inputs": sorted(item.text for item in self.input_type_refs),
            "outputs": sorted(item.text for item in self.output_type_refs),
            "contracts": sorted(item.text for item in self.fidelity_contract_refs),
            "preserved": sorted(item.text for item in self.preserved_constraint_refs),
            "anchors": sorted(item.text for item in self.protected_anchor_refs),
            "evidence": list(self.expected_evidence),
            "policies": sorted(item.text for item in self.policy_refs),
            "sources": sorted(item.text for item in self.source_refs),
        }


CapabilityDemand.NESTED = {
    "input_type_refs": of(SemanticRef),
    "output_type_refs": of(SemanticRef),
    "fidelity_contract_refs": of(SemanticRef),
    "preserved_constraint_refs": of(SemanticRef),
    "protected_anchor_refs": of(SemanticRef),
    "policy_refs": of(SemanticRef),
    "source_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class SemanticMutationEnvelope(Record):
    """What an edit may change, what it may not, and by how much (§12).

    Protected and mutable property sets are required to be disjoint, which is the whole content of
    "preserve the character's identity while fixing the hand": the envelope is where M03 says so
    without naming a mask, a region, a model control or a tool. Geometry belongs to M04; the
    envelope stays a statement about properties.
    """

    envelope_id: str
    operation_id: str
    protected_properties: tuple[str, ...] = ()
    mutable_properties: tuple[str, ...] = ()
    conditionally_mutable_properties: tuple[str, ...] = ()
    allowed_mutation_classes: tuple[str, ...] = ()
    forbidden_mutation_classes: tuple[str, ...] = ()
    maximum_drift: float | None = None
    drift_policy_ref: SemanticRef | None = None
    reference_anchors: tuple[SemanticRef, ...] = ()
    reset_policy_ref: SemanticRef | None = None
    source_refs: tuple[SemanticRef, ...] = ()
    notes: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "envelope_id", require_identifier(self.envelope_id, "envelope_id"))
        object.__setattr__(self, "operation_id", require_identifier(self.operation_id, "operation_id"))
        protected = _paths(self.protected_properties, "protected_properties")
        mutable = _paths(self.mutable_properties, "mutable_properties")
        conditional = _paths(self.conditionally_mutable_properties, "conditionally_mutable")
        overlap = sorted(set(protected) & (set(mutable) | set(conditional)))
        if overlap:
            raise SchemaValidationError(
                f"envelope {self.envelope_id} declares {overlap} both protected and mutable; a "
                "property cannot be preserved and edited by the same operation, and the ambiguity "
                "would be resolved by whichever downstream module guessed first"
            )
        if not protected:
            raise SchemaValidationError(
                f"envelope {self.envelope_id} protects nothing; an envelope with no protected "
                "properties is a licence, not a boundary"
            )
        if not mutable and not conditional:
            raise SchemaValidationError(
                f"envelope {self.envelope_id} permits no change; an operation with an envelope that "
                "allows nothing mutable cannot accomplish the mutation it was declared for"
            )
        if len(protected) + len(mutable) + len(conditional) > MAX_MUTATION_TARGETS:
            raise SchemaValidationError(
                f"envelope {self.envelope_id} targets more properties than M03 supports; an envelope "
                "that wide is a whole-subject rewrite and should be declared as one operation per "
                "concern rather than as a boundary"
            )
        object.__setattr__(self, "protected_properties", protected)
        object.__setattr__(self, "mutable_properties", mutable)
        object.__setattr__(self, "conditionally_mutable_properties", conditional)
        allowed = _mutation_classes(self.allowed_mutation_classes, "allowed_mutation_classes")
        forbidden = _mutation_classes(self.forbidden_mutation_classes, "forbidden_mutation_classes")
        clash = sorted(set(allowed) & set(forbidden))
        if clash:
            raise SchemaValidationError(
                f"envelope {self.envelope_id} lists {clash} as both allowed and forbidden"
            )
        object.__setattr__(self, "allowed_mutation_classes", allowed)
        object.__setattr__(self, "forbidden_mutation_classes", forbidden)
        if self.maximum_drift is not None:
            drift = require_unit_interval(self.maximum_drift, "maximum_drift")
            object.__setattr__(self, "maximum_drift", drift)
            if self.drift_policy_ref is None:
                raise SchemaValidationError(
                    f"envelope {self.envelope_id} states a drift bound with no policy behind it; §12 "
                    "allows a maximum only "
                    "where a typed policy exists, and the ref is what makes the number checkable"
                )
        if self.drift_policy_ref is not None and self.maximum_drift is None:
            raise SchemaValidationError(
                f"envelope {self.envelope_id} cites a drift policy without a bound; the policy would "
                "be evidence for a claim the envelope never made"
            )
        for name in ("drift_policy_ref", "reset_policy_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        anchors = tuple(
            sorted(
                (
                    require_bound_ref(item, "reference_anchors[]", kind=RefKind.ANCHOR)
                    for item in (self.reference_anchors or ())
                ),
                key=lambda item: item.text,
            )
        )
        object.__setattr__(self, "reference_anchors", anchors)
        sources = _refs(self.source_refs, "source_refs")
        if not sources:
            raise SchemaValidationError(
                f"envelope {self.envelope_id} cites no source; a protection nobody can attribute is a "
                "protection a later revision can delete without argument"
            )
        object.__setattr__(self, "source_refs", sources)
        if self.notes is not None:
            reject_provider_vocabulary(self.notes, "notes")
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        reject_provider_vocabulary(self.metadata, "metadata")
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def mutates_anything(self) -> bool:
        return bool(self.mutable_properties or self.conditionally_mutable_properties)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "protected": list(self.protected_properties),
            "mutable": list(self.mutable_properties),
            "conditional": list(self.conditionally_mutable_properties),
            "allowed": list(self.allowed_mutation_classes),
            "forbidden": list(self.forbidden_mutation_classes),
            "maximum_drift": self.maximum_drift,
            "drift_policy": self.drift_policy_ref.text if self.drift_policy_ref else None,
            "anchors": sorted(item.text for item in self.reference_anchors),
            "reset_policy": self.reset_policy_ref.text if self.reset_policy_ref else None,
        }


SemanticMutationEnvelope.NESTED = {
    "drift_policy_ref": of(SemanticRef),
    "reset_policy_ref": of(SemanticRef),
    "reference_anchors": of(SemanticRef),
    "source_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class ExplorationIntent(Record):
    """A request to explore, with no compute attached to it (§11).

    Look for a candidate count, a seed or a budget: there is none, and there cannot be. This
    record says which zones may vary and which anchors hold while they do. Whether that is worth
    twelve tries or two is a decision for a module that knows what hardware exists, and putting
    the number here would be that module's answer written into the question.
    """

    exploration_id: str
    operation_id: str
    varies_zone_refs: tuple[SemanticRef, ...] = ()
    fixed_anchor_refs: tuple[SemanticRef, ...] = ()
    diversity_axes: tuple[str, ...] = ()
    shape: str = ExplorationShape.STRUCTURED.value
    branch_policy: str = BranchPolicy.INDEPENDENT.value
    selection_contract_refs: tuple[SemanticRef, ...] = ()
    selection_predicate_refs: tuple[SemanticRef, ...] = ()
    source_refs: tuple[SemanticRef, ...] = ()
    notes: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    #: §11 as structure: nothing this record carries may express compute.
    declares_compute = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "exploration_id", require_identifier(self.exploration_id, "exploration_id")
        )
        object.__setattr__(self, "operation_id", require_identifier(self.operation_id, "operation_id"))
        zones = _refs(self.varies_zone_refs, "varies_zone_refs")
        anchors = tuple(
            sorted(
                (
                    require_bound_ref(item, "fixed_anchor_refs[]", kind=RefKind.ANCHOR)
                    for item in (self.fixed_anchor_refs or ())
                ),
                key=lambda item: item.text,
            )
        )
        if not zones and not anchors:
            raise SchemaValidationError(
                f"exploration {self.exploration_id} declares neither a zone to vary nor an anchor to "
                "hold; an exploration with no shape is a request to change something unspecified"
            )
        clashing = sorted({item.text for item in zones} & {item.text for item in anchors})
        if clashing:
            raise SchemaValidationError(
                f"exploration {self.exploration_id} varies and fixes {clashing}; §7's freedom zones "
                "stay open on purpose, and the same ref cannot be both left free and held fixed"
            )
        object.__setattr__(self, "varies_zone_refs", zones)
        object.__setattr__(self, "fixed_anchor_refs", anchors)
        axes = tuple(sorted({_text(item, "diversity_axes[]") for item in (self.diversity_axes or ())}))
        reject_provider_vocabulary(axes, "diversity_axes")
        if len(axes) > MAX_ENTRIES_PER_FIELD:
            raise SchemaValidationError(
                f"exploration {self.exploration_id} declares {len(axes)} axes, above {MAX_ENTRIES_PER_FIELD}"
            )
        object.__setattr__(self, "diversity_axes", axes)
        object.__setattr__(self, "shape", ExplorationShape.parse(self.shape, "shape").value)
        object.__setattr__(
            self, "branch_policy", BranchPolicy.parse(self.branch_policy, "branch_policy").value
        )
        for name in ("selection_contract_refs", "selection_predicate_refs"):
            object.__setattr__(self, name, _refs(getattr(self, name), name))
        sources = _refs(self.source_refs, "source_refs")
        if not sources:
            raise SchemaValidationError(
                f"exploration {self.exploration_id} cites no source; latitude that cannot be traced "
                "to a statement is a default waiting to be mistaken for a decision"
            )
        object.__setattr__(self, "source_refs", sources)
        if self.notes is not None:
            reject_provider_vocabulary(self.notes, "notes")
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        reject_provider_vocabulary(self.metadata, "metadata")
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "zones": sorted(item.text for item in self.varies_zone_refs),
            "anchors": sorted(item.text for item in self.fixed_anchor_refs),
            "axes": list(self.diversity_axes),
            "shape": self.shape,
            "branch_policy": self.branch_policy,
            "selection_contracts": sorted(item.text for item in self.selection_contract_refs),
            "selection_predicates": sorted(item.text for item in self.selection_predicate_refs),
        }


ExplorationIntent.NESTED = {
    "varies_zone_refs": of(SemanticRef),
    "fixed_anchor_refs": of(SemanticRef),
    "selection_contract_refs": of(SemanticRef),
    "selection_predicate_refs": of(SemanticRef),
    "source_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class SemanticLossRule(Record):
    """One semantic item's disposition under translation (§9).

    The per-item shape is the point. A global tolerance would let a large approximation on one
    axis pay for exactness on another, and no brief ever said anything of the kind.
    """

    rule_id: str
    item_ref: SemanticRef
    loss_class: str
    tolerance_ref: SemanticRef | None = None
    policy_ref: SemanticRef | None = None
    expected_evidence: tuple[str, ...] = ()
    operation_ids: tuple[str, ...] = ()
    source_refs: tuple[SemanticRef, ...] = ()
    notes: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", require_identifier(self.rule_id, "rule_id"))
        object.__setattr__(self, "item_ref", SemanticRef.coerce(self.item_ref, "item_ref"))
        kind = SemanticLossClass.parse(self.loss_class, "loss_class")
        object.__setattr__(self, "loss_class", kind.value)
        for name in ("tolerance_ref", "policy_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        if kind.requires_tolerance and self.tolerance_ref is None:
            raise SchemaValidationError(
                f"rule {self.rule_id} allows approximation without naming the tolerance it is bounded "
                "by; §9 permits a bounded approximation, and the bound is the part that was agreed"
            )
        if kind.is_freedom and not self.source_refs:
            raise SchemaValidationError(
                f"rule {self.rule_id} declares creative freedom with no source; freedom the brief did "
                "not grant is a silent weakening of a requirement"
            )
        if self.tolerance_ref is not None and kind is not SemanticLossClass.BOUNDED_APPROXIMATION:
            raise SchemaValidationError(
                f"rule {self.rule_id} carries a tolerance under {kind.value}; a tolerance is only "
                "meaningful for the class that approximates within one"
            )
        object.__setattr__(
            self,
            "expected_evidence",
            tuple(sorted({_text(item, "expected_evidence[]") for item in (self.expected_evidence or ())})),
        )
        object.__setattr__(
            self,
            "operation_ids",
            tuple(sorted({require_identifier(item, "operation_ids[]") for item in (self.operation_ids or ())})),
        )
        object.__setattr__(self, "source_refs", _refs(self.source_refs, "source_refs"))
        if self.notes is not None:
            reject_provider_vocabulary(self.notes, "notes")
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def class_enum(self) -> SemanticLossClass:
        return SemanticLossClass.parse(self.loss_class)

    @property
    def blocks_provider_admission(self) -> bool:
        """Whether an unsupported translation of this item stops the provider.

        §10's rule in one line: only a LOSSLESS_REQUIRED obligation refuses a provider that cannot
        represent it. Everything else admits a bounded, delegated or advisory answer.
        """

        return self.class_enum is SemanticLossClass.LOSSLESS_REQUIRED

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "item": self.item_ref.text,
            "class": self.loss_class,
            "tolerance": self.tolerance_ref.text if self.tolerance_ref else None,
            "policy": self.policy_ref.text if self.policy_ref else None,
            "evidence": list(self.expected_evidence),
            "operations": list(self.operation_ids),
        }


SemanticLossRule.NESTED = {
    "item_ref": of(SemanticRef),
    "tolerance_ref": of(SemanticRef),
    "policy_ref": of(SemanticRef),
    "source_refs": of(SemanticRef),
}


# --------------------------------------------------------------------------- #
# Shared normalisation helpers
# --------------------------------------------------------------------------- #


def _text(value: Any, name: str) -> str:
    return require_text(value, name, maximum=256)


def _paths(value: Any, name: str) -> tuple[str, ...]:
    items = tuple(sorted({require_semantic_path(item, name) for item in (value or ())}))
    if len(items) > MAX_SCOPE_PATHS:
        raise SchemaValidationError(f"{name} holds {len(items)} paths, above {MAX_SCOPE_PATHS}")
    return items


def _refs(
    value: Any, name: str, *, limit: int = MAX_PROVENANCE_REFS
) -> tuple[SemanticRef, ...]:
    items = tuple(
        sorted(
            (SemanticRef.coerce(item, f"{name}[]") for item in (value or ())),
            key=lambda item: item.text,
        )
    )
    if len(items) > limit:
        raise SchemaValidationError(f"{name} cites {len(items)} refs, above {limit}")
    return items


def _ids(value: Any, name: str, *, limit: int = MAX_ENTRIES_PER_FIELD) -> tuple[str, ...]:
    items = tuple(sorted({require_identifier(item, name) for item in (value or ())}))
    if len(items) > limit:
        raise SchemaValidationError(f"{name} holds {len(items)} entries, above {limit}")
    return items


def _mutation_classes(value: Any, name: str) -> tuple[str, ...]:
    items = tuple(sorted({SemanticMutationClass.parse(item, name).value for item in (value or ())}))
    if len(items) > len(SemanticMutationClass):
        raise SchemaValidationError(f"{name} declares more classes than exist")
    return items


def _slug_set(value: Any, name: str) -> frozenset[str]:
    """A caller-supplied availability observation, normalized and provider-vocabulary-free.

    Capability registries speak in the same semantic slugs M03 demands in, so the observation is
    checked against §7 as well: a registry that advertises ``sdxl-checkpoint-fix`` is not making a
    statement about a capability, and M03 must not let that phrasing reach a fingerprint.
    """

    items = {require_identifier(item, name) for item in (value or ())}
    found = find_provider_vocabulary(sorted(items))
    if found:
        raise SchemaValidationError(
            f"{name} is expressed in provider vocabulary {list(found)}; capability availability must "
            "be advertised in the same semantic slugs the demands use, or the observation cannot be "
            "matched to them"
        )
    return frozenset(items)


# --------------------------------------------------------------------------- #
# §5: the operation record
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class IntentOperation(Record):
    """One provider-neutral desired transformation (§4).

    The contract is what §5 lists, and the interesting part is what is missing: there is no field
    for a workflow, a graph shape, a step count, a model or a prompt. The operation says what kind
    of change is wanted, which semantics must survive it, which capabilities it presumes, and
    which admitted statement or policy stands behind each of those claims.
    """

    intent_operation_id: str
    family: str
    purpose: str
    subject_refs: tuple[SemanticRef, ...] = ()
    source_refs: tuple[SemanticRef, ...] = ()
    output_type_refs: tuple[SemanticRef, ...] = ()
    deliverable_refs: tuple[SemanticRef, ...] = ()
    fidelity_contract_refs: tuple[SemanticRef, ...] = ()
    intent_slice_ref: SemanticRef | None = None
    constraint_slice_ref: SemanticRef | None = None
    protected_anchor_refs: tuple[SemanticRef, ...] = ()
    freedom_zone_refs: tuple[SemanticRef, ...] = ()
    capability_demand_ids: tuple[str, ...] = ()
    mutation_envelope_ref: str | None = None
    exploration_ref: str | None = None
    allowed_mutation_classes: tuple[str, ...] = ()
    forbidden_mutation_classes: tuple[str, ...] = ()
    required_explanation_refs: tuple[SemanticRef, ...] = ()
    provenance_refs: tuple[SemanticRef, ...] = ()
    originating_refs: tuple[SemanticRef, ...] = ()
    completion_semantics: str = IntentCompletionSemantics.ONE_SUFFICIENT_OUTPUT.value
    side_effect_class: str = SideEffectClass.INTERNAL_MATERIALIZATION.value
    approval_boundary_ref: SemanticRef | None = None
    rationale: str | None = None
    notes: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    #: §2, §13: an operation is a demand, never an authorization or an executable step.
    is_execution_plan = False
    authorizes_side_effects = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "intent_operation_id",
            require_identifier(self.intent_operation_id, "intent_operation_id"),
        )
        family = IntentOperationFamily.parse(self.family, "family")
        object.__setattr__(self, "family", family.value)
        reject_provider_vocabulary(self.purpose, "purpose")
        object.__setattr__(self, "purpose", require_text(self.purpose, "purpose", maximum=1024))
        for name in (
            "subject_refs",
            "source_refs",
            "output_type_refs",
            "deliverable_refs",
            "fidelity_contract_refs",
            "freedom_zone_refs",
            "required_explanation_refs",
            "provenance_refs",
            "originating_refs",
        ):
            object.__setattr__(self, name, _refs(getattr(self, name), name))
        anchors = tuple(
            sorted(
                (
                    require_bound_ref(item, "protected_anchor_refs[]", kind=RefKind.ANCHOR)
                    for item in (self.protected_anchor_refs or ())
                ),
                key=lambda item: item.text,
            )
        )
        object.__setattr__(self, "protected_anchor_refs", anchors)
        if family.requires_subject and not self.subject_refs:
            raise SchemaValidationError(
                f"operation {self.intent_operation_id} is a {family.value} with no subject; §5 "
                "requires the governed thing the change is about, or the operation cannot be traced "
                "back to what it must preserve"
            )
        if not family.judges_rather_than_produces and not self.output_type_refs:
            raise SchemaValidationError(
                f"operation {self.intent_operation_id} produces nothing it declares a semantic type "
                "for; a producing operation with no output type cannot be composed into a later step"
            )
        if not self.originating_refs:
            raise SchemaValidationError(
                f"operation {self.intent_operation_id} cites no admitted statement, constraint or "
                "policy; D-M03-S04-012 makes an explanation path a construction requirement, so a "
                "verb nobody asked for cannot be written into canonical intent"
            )
        if not self.required_explanation_refs:
            raise SchemaValidationError(
                f"operation {self.intent_operation_id} declares no required explanation links; §17 "
                "exists so a downstream system can ask why this verb and not another"
            )
        for name in ("intent_slice_ref", "constraint_slice_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        object.__setattr__(
            self, "capability_demand_ids", _ids(self.capability_demand_ids, "capability_demand_ids")
        )
        if self.mutation_envelope_ref is not None:
            object.__setattr__(
                self,
                "mutation_envelope_ref",
                require_identifier(self.mutation_envelope_ref, "mutation_envelope_ref"),
            )
        if family.requires_envelope and self.mutation_envelope_ref is None:
            raise SchemaValidationError(
                f"operation {self.intent_operation_id} is a {family.value} with no mutation envelope; "
                "§12 requires one precisely because this verb edits something already admitted — "
                "without it nothing states which properties the edit must survive"
            )
        if self.exploration_ref is not None:
            object.__setattr__(
                self, "exploration_ref", require_identifier(self.exploration_ref, "exploration_ref")
            )
        allowed = _mutation_classes(self.allowed_mutation_classes, "allowed_mutation_classes")
        forbidden = _mutation_classes(self.forbidden_mutation_classes, "forbidden_mutation_classes")
        clash = sorted(set(allowed) & set(forbidden))
        if clash:
            raise SchemaValidationError(
                f"operation {self.intent_operation_id} allows and forbids {clash}; the contradiction "
                "would be resolved downstream, which is where it should not be resolved"
            )
        object.__setattr__(self, "allowed_mutation_classes", allowed)
        object.__setattr__(self, "forbidden_mutation_classes", forbidden)
        varied = {item.text for item in self.freedom_zone_refs}
        held = {item.text for item in self.protected_anchor_refs}
        if varied & held:
            raise SchemaValidationError(
                f"operation {self.intent_operation_id} protects and leaves open "
                f"{sorted(varied & held)}"
            )
        object.__setattr__(
            self,
            "completion_semantics",
            IntentCompletionSemantics.parse(self.completion_semantics, "completion_semantics").value,
        )
        side_effect = SideEffectClass.parse(self.side_effect_class, "side_effect_class")
        object.__setattr__(self, "side_effect_class", side_effect.value)
        if self.approval_boundary_ref is not None:
            object.__setattr__(
                self,
                "approval_boundary_ref",
                SemanticRef.coerce(self.approval_boundary_ref, "approval_boundary_ref"),
            )
        for name in ("rationale", "notes"):
            value = getattr(self, name)
            if value is not None:
                reject_provider_vocabulary(value, name)
                object.__setattr__(self, name, require_text(value, name, maximum=1024))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        reject_provider_vocabulary(self.metadata, "metadata")
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def family_enum(self) -> IntentOperationFamily:
        return IntentOperationFamily.parse(self.family)

    @property
    def side_effect_enum(self) -> SideEffectClass:
        return SideEffectClass.parse(self.side_effect_class)

    @property
    def completion_enum(self) -> IntentCompletionSemantics:
        return IntentCompletionSemantics.parse(self.completion_semantics)

    @property
    def needs_approval_boundary(self) -> bool:
        """Whether something outside M03 must approve this before it means anything (§13).

        The field is optional on purpose: §13 lets M03 express the desire and the *need* for a
        boundary. Compilation turns a missing boundary into a
        ``SIDE_EFFECT_POLICY_UNRESOLVED`` gap, which is the honest representation — the wish is
        recorded and the authorization is visibly absent.
        """

        return self.side_effect_enum.requires_governed_approval and self.approval_boundary_ref is None

    @property
    def source_ref_texts(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    item.text
                    for group in (
                        self.subject_refs,
                        self.source_refs,
                        self.output_type_refs,
                        self.deliverable_refs,
                        self.fidelity_contract_refs,
                        self.protected_anchor_refs,
                        self.freedom_zone_refs,
                        self.originating_refs,
                        self.provenance_refs,
                    )
                    for item in group
                }
                + ([self.intent_slice_ref.text] if self.intent_slice_ref else [])
                + ([self.constraint_slice_ref.text] if self.constraint_slice_ref else [])
                + (
                    [self.approval_boundary_ref.text]
                    if self.approval_boundary_ref is not None
                    else []
                )
            )
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "subjects": sorted(item.text for item in self.subject_refs),
            "sources": sorted(item.text for item in self.source_refs),
            "outputs": sorted(item.text for item in self.output_type_refs),
            "deliverables": sorted(item.text for item in self.deliverable_refs),
            "contracts": sorted(item.text for item in self.fidelity_contract_refs),
            "intent_slice": self.intent_slice_ref.text if self.intent_slice_ref else None,
            "constraint_slice": self.constraint_slice_ref.text if self.constraint_slice_ref else None,
            "anchors": sorted(item.text for item in self.protected_anchor_refs),
            "zones": sorted(item.text for item in self.freedom_zone_refs),
            "demands": list(self.capability_demand_ids),
            "envelope": self.mutation_envelope_ref,
            "exploration": self.exploration_ref,
            "allowed": list(self.allowed_mutation_classes),
            "forbidden": list(self.forbidden_mutation_classes),
            "completion": self.completion_semantics,
            "side_effect": self.side_effect_class,
            "approval": self.approval_boundary_ref.text if self.approval_boundary_ref else None,
            "explanations": sorted(item.text for item in self.required_explanation_refs),
            "originating": sorted(item.text for item in self.originating_refs),
        }


IntentOperation.NESTED = {
    "subject_refs": of(SemanticRef),
    "source_refs": of(SemanticRef),
    "output_type_refs": of(SemanticRef),
    "deliverable_refs": of(SemanticRef),
    "fidelity_contract_refs": of(SemanticRef),
    "protected_anchor_refs": of(SemanticRef),
    "freedom_zone_refs": of(SemanticRef),
    "required_explanation_refs": of(SemanticRef),
    "provenance_refs": of(SemanticRef),
    "originating_refs": of(SemanticRef),
    "intent_slice_ref": of(SemanticRef),
    "constraint_slice_ref": of(SemanticRef),
    "approval_boundary_ref": of(SemanticRef),
}


# --------------------------------------------------------------------------- #
# §10: what a provider compiler owes back
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProviderTranslationItem(Record):
    """One obligation, and what the provider says it did with it."""

    item_ref: SemanticRef
    disposition: str
    tolerance_ref: SemanticRef | None = None
    delegate_ref: SemanticRef | None = None
    detail: str | None = None
    evidence_refs: tuple[SemanticRef, ...] = ()
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "item_ref", SemanticRef.coerce(self.item_ref, "item_ref"))
        kind = TranslationDisposition.parse(self.disposition, "disposition")
        object.__setattr__(self, "disposition", kind.value)
        for name in ("tolerance_ref", "delegate_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        if kind is TranslationDisposition.REPRESENTED_WITH_TOLERANCE and self.tolerance_ref is None:
            raise SchemaValidationError(
                f"{self.item_ref.text} is approximated with no tolerance cited; an approximation "
                "without a bound is a claim about the work, not a record of it"
            )
        if kind is TranslationDisposition.DELEGATED_TO_VALIDATOR and self.delegate_ref is None:
            raise SchemaValidationError(
                f"{self.item_ref.text} is delegated with nowhere it was delegated to; §10's delegation "
                "is to an external validator or repair loop, and an unnamed one checks nothing"
            )
        if kind is TranslationDisposition.INTENTIONALLY_IRRELEVANT and self.evidence_refs:
            raise SchemaValidationError(
                f"{self.item_ref.text} is declared irrelevant to this step and carries evidence anyway"
            )
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs"))
        if self.detail is not None:
            object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=1024))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def disposition_enum(self) -> TranslationDisposition:
        return TranslationDisposition.parse(self.disposition)


ProviderTranslationItem.NESTED = {
    "item_ref": of(SemanticRef),
    "tolerance_ref": of(SemanticRef),
    "delegate_ref": of(SemanticRef),
    "evidence_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class ProviderTranslationReceipt(Record):
    """A provider compiler's account of what it represented (§10).

    Note what this record is not allowed to do: it carries no field that changes the bundle it is
    about. §23's boundary is structural — a receipt that pinned a new constraint into canonical
    intent would be an untrusted provider editing the brief, and prompt-injected text reaching a
    production graph is exactly how that happens.
    """

    receipt_id: str
    bundle_ref: SemanticRef
    bundle_fingerprint_digest: str
    compiler_ref: SemanticRef
    provider_ref: SemanticRef
    items: tuple[ProviderTranslationItem, ...] = ()
    proposal_refs: tuple[SemanticRef, ...] = ()
    gap_refs: tuple[SemanticRef, ...] = ()
    observation_refs: tuple[SemanticRef, ...] = ()
    notes: str | None = None
    contract_version: str = ""

    #: §23: an observation about a bundle, never a mutation of one.
    mutates_bundle = False
    canonical_semantics = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt_id", require_identifier(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "bundle_ref", SemanticRef.coerce(self.bundle_ref, "bundle_ref"))
        object.__setattr__(
            self,
            "bundle_fingerprint_digest",
            require_digest(self.bundle_fingerprint_digest, "bundle_fingerprint_digest"),
        )
        for name in ("compiler_ref", "provider_ref"):
            object.__setattr__(self, name, SemanticRef.coerce(getattr(self, name), name))
        entries = tuple(
            sorted(
                (ProviderTranslationItem.coerce(item, "items[]") for item in (self.items or ())),
                key=lambda item: item.item_ref.text,
            )
        )
        counted: dict[str, int] = {}
        for item in entries:
            counted[item.item_ref.text] = counted.get(item.item_ref.text, 0) + 1
        duplicated = sorted(name for name, total in counted.items() if total > 1)
        if duplicated:
            raise SchemaValidationError(
                f"receipt {self.receipt_id} answers for {duplicated} twice; one obligation with two "
                "dispositions is not a partial answer but a contradictory one"
            )
        object.__setattr__(self, "items", entries)
        for name in ("proposal_refs", "gap_refs", "observation_refs"):
            object.__setattr__(
                self,
                name,
                _refs(
                    getattr(self, name),
                    name,
                    limit=MAX_OBSERVATION_REFS if name == "observation_refs" else MAX_PROVENANCE_REFS,
                ),
            )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def item_for(self) -> Mapping[str, ProviderTranslationItem]:
        return {item.item_ref.text: item for item in self.items}

    @property
    def exact_items(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.item_ref.text
                for item in self.items
                if item.disposition_enum is TranslationDisposition.REPRESENTED_EXACTLY
            )
        )

    @property
    def approximated_items(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.item_ref.text
                for item in self.items
                if item.disposition_enum is TranslationDisposition.REPRESENTED_WITH_TOLERANCE
            )
        )

    @property
    def unsupported_items(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.item_ref.text
                for item in self.items
                if item.disposition_enum is TranslationDisposition.UNSUPPORTED
            )
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "bundle": self.bundle_ref.text,
            "bundle_digest": self.bundle_fingerprint_digest,
            "compiler": self.compiler_ref.text,
            "items": [
                {
                    "item": item.item_ref.text,
                    "disposition": item.disposition,
                    "tolerance": item.tolerance_ref.text if item.tolerance_ref else None,
                    "delegate": item.delegate_ref.text if item.delegate_ref else None,
                }
                for item in self.items
            ],
        }


ProviderTranslationReceipt.NESTED = {
    "bundle_ref": of(SemanticRef),
    "compiler_ref": of(SemanticRef),
    "provider_ref": of(SemanticRef),
    "items": of(ProviderTranslationItem),
    "proposal_refs": of(SemanticRef),
    "gap_refs": of(SemanticRef),
    "observation_refs": of(SemanticRef),
}


# --------------------------------------------------------------------------- #
# §20: the fingerprint
# --------------------------------------------------------------------------- #

#: What the canonical fingerprint deliberately excludes, recorded so the exclusion is a fact a
#: reviewer can read rather than an absence someone has to notice. Cost, schedule, candidate
#: counts, host identity and provider choice are all absent because each one would make a
#: statement about meaning depend on something that changes when the machine changes.
FINGERPRINT_EXCLUSIONS: tuple[str, ...] = (
    "provider",
    "model",
    "checkpoint",
    "host",
    "region",
    "queue",
    "worker",
    "runtime_telemetry",
    "cost",
    "schedule",
    "candidate_count",
    "capability_availability",
    "translation_receipt",
)


@dataclass(frozen=True)
class ExecutionIntentFingerprint(Record):
    """The versioned digest S04 leaves for reuse and invalidation (§20).

    Provider availability is an input to the bundle's *status* and never to this digest. That
    asymmetry is what lets proof out that one brief compiles to one canonical intent: if the
    fingerprint moved when a registry added or dropped a capability, "the intent is unchanged" and
    "somebody can serve it" would be the same statement, and they are not.
    """

    fingerprint_id: str
    semantic_digest: str
    compiler_version: str
    provider_vocabulary_version: str
    excluded_inputs: tuple[str, ...] = FINGERPRINT_EXCLUSIONS
    contract_version: str = ""

    #: §20 as structure.
    provider_independent = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "fingerprint_id", require_identifier(self.fingerprint_id, "fingerprint_id")
        )
        object.__setattr__(self, "semantic_digest", require_digest(self.semantic_digest, "semantic_digest"))
        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(
            self,
            "provider_vocabulary_version",
            require_version_text(self.provider_vocabulary_version, "provider_vocabulary_version"),
        )
        excluded = tuple(
            sorted({require_identifier(item, "excluded_inputs[]") for item in (self.excluded_inputs or ())})
        )
        if not excluded:
            raise SchemaValidationError(
                "an execution fingerprint declares nothing excluded; the exclusion list is how a "
                "later reader learns that provider absence was deliberate"
            )
        object.__setattr__(self, "excluded_inputs", excluded)
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )


def _fingerprint_view(bundle: "ExecutionIntentBundle") -> dict[str, Any]:
    """Exactly §20's inputs, and nothing else.

    Written as an explicit whitelist of the bundle's own fields rather than as a filter over its
    payload, so a field added later cannot join the fingerprint by accident. A new semantic field
    has to be named here on purpose, which is the reviewable version of the decision.
    """

    return {
        "brief": bundle.brief_ref.text,
        "revision": bundle.revision_ref.text,
        "intent_digest": bundle.intent_fingerprint_digest,
        "constraint_digest": bundle.constraint_fingerprint_digest,
        "fidelity_digest": bundle.fidelity_fingerprint_digest,
        "contract_set": bundle.contract_set_ref.text if bundle.contract_set_ref else None,
        "deliverables": sorted(item.text for item in bundle.deliverable_refs),
        "operations": [item.fingerprint_inputs() for item in bundle.operations],
        "demands": [item.fingerprint_inputs() for item in bundle.capability_demands],
        "envelopes": [item.fingerprint_inputs() for item in bundle.mutation_envelopes],
        "explorations": [item.fingerprint_inputs() for item in bundle.explorations],
        "loss_rules": [item.fingerprint_inputs() for item in bundle.loss_rules],
        "intent_slices": sorted(item.text for item in bundle.intent_slice_refs),
        "constraint_slices": sorted(item.text for item in bundle.constraint_slice_refs),
        "policies": sorted(item.text for item in bundle.policy_refs),
        "side_effect_policy": (
            bundle.side_effect_policy_ref.text if bundle.side_effect_policy_ref else None
        ),
        "compiler_version": bundle.compiler_version,
        "vocabulary_version": bundle.provider_vocabulary_version,
        "contract_version": bundle.contract_version,
    }


def fingerprint_of_execution_intent(
    bundle: "ExecutionIntentBundle", *, fingerprint_id: str | None = None
) -> ExecutionIntentFingerprint:
    """Take §20's digest over a bundle."""

    return ExecutionIntentFingerprint(
        fingerprint_id=require_identifier(
            fingerprint_id or f"eif-{bundle.bundle_id}", "fingerprint_id"
        ),
        semantic_digest=content_digest(_fingerprint_view(bundle)),
        compiler_version=bundle.compiler_version,
        provider_vocabulary_version=bundle.provider_vocabulary_version,
        contract_version=bundle.contract_version,
    )


def canonical_execution_digest(bundle: "ExecutionIntentBundle") -> str:
    """The whole-bundle digest, fingerprint and delta excluded to avoid self-reference.

    A provider receipt binds this rather than the semantic digest, so the receipt is invalidated
    by a change in the recorded gaps too: a translation of an incomplete intent is not a
    translation of the intent.
    """

    payload = bundle.to_payload()
    payload.pop("fingerprint", None)
    payload.pop("delta", None)
    return content_digest(payload)


# --------------------------------------------------------------------------- #
# §21: the delta
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ExecutionIntentDelta(Record):
    """A typed account of how one bundle revision moved, for M02/M04/M16 to act on (§21).

    M03 classifies and later modules decide. ``EXPLANATION_ONLY_CHANGE`` is the class that earns
    the record's existence: it tells a provider compiler its translation is still valid, which is
    the difference between a restated rationale costing nothing and costing a whole re-run.
    """

    delta_id: str
    class_name: str
    changed_inputs: tuple[str, ...] = ()
    affected_operation_ids: tuple[str, ...] = ()
    affected_capability_ids: tuple[str, ...] = ()
    explanation_refs: tuple[SemanticRef, ...] = ()
    before_fingerprint: str | None = None
    after_fingerprint: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "delta_id", require_identifier(self.delta_id, "delta_id"))
        kind = ExecutionIntentChangeClass.parse(self.class_name, "class_name")
        object.__setattr__(self, "class_name", kind.value)
        changed = tuple(sorted({_text(item, "changed_inputs[]") for item in (self.changed_inputs or ())}))
        if kind is ExecutionIntentChangeClass.NO_SEMANTIC_CHANGE and changed:
            raise SchemaValidationError(
                f"delta {self.delta_id} reports no semantic change while listing {list(changed)}; the "
                "two claims cannot both be made about one revision"
            )
        if kind is not ExecutionIntentChangeClass.NO_SEMANTIC_CHANGE and not changed:
            raise SchemaValidationError(
                f"delta {self.delta_id} reports {kind.value} with nothing that moved; a change class "
                "with no changed input is a guess, and M02 cannot scope rework from a guess"
            )
        object.__setattr__(self, "changed_inputs", changed)
        object.__setattr__(
            self,
            "affected_operation_ids",
            _ids(self.affected_operation_ids, "affected_operation_ids"),
        )
        object.__setattr__(
            self, "affected_capability_ids", _ids(self.affected_capability_ids, "affected_capability_ids")
        )
        object.__setattr__(self, "explanation_refs", _refs(self.explanation_refs, "explanation_refs"))
        for name in ("before_fingerprint", "after_fingerprint"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def class_enum(self) -> ExecutionIntentChangeClass:
        return ExecutionIntentChangeClass.parse(self.class_name)

    @property
    def requires_provider_recompilation(self) -> bool:
        return self.class_enum.requires_provider_recompilation


ExecutionIntentDelta.NESTED = {"explanation_refs": of(SemanticRef)}


#: The per-collection views compared field by field, and what a whole add/remove in each one means.
#: ``operations`` is the only collection whose *existence* is the semantic claim; adding a demand is
#: a capability change, not a new verb.
_DELTA_RECORD_VIEWS: tuple[str, ...] = (
    "operations",
    "demands",
    "envelopes",
    "explorations",
    "loss_rules",
)

#: What adding or removing a member of each collection means.
_DELTA_ADDED_REMOVED: dict[str, ExecutionIntentChangeClass] = MappingProxyType({
    "operations": ExecutionIntentChangeClass.OPERATION_ADDED_REMOVED,
    "demands": ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
    "envelopes": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "explorations": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "loss_rules": ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
})

#: What a change inside a collection means when the field itself says nothing narrower.
_DELTA_VIEW_DEFAULTS: dict[str, ExecutionIntentChangeClass] = MappingProxyType({
    "operations": ExecutionIntentChangeClass.DELIVERABLE_INTENT_CHANGE,
    "demands": ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
    "envelopes": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "explorations": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "loss_rules": ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
    "anchors": ExecutionIntentChangeClass.PROTECTED_ANCHOR_CHANGE,
    "contracts": ExecutionIntentChangeClass.QUALITY_CONTRACT_REF_CHANGE,
    "deliverables": ExecutionIntentChangeClass.DELIVERABLE_INTENT_CHANGE,
    "slices": ExecutionIntentChangeClass.DELIVERABLE_INTENT_CHANGE,
})

#: Fields whose move means something more specific than the collection carrying them. Classified by
#: field name rather than by which record held it, because ``anchors`` is an anchor change whether an
#: operation or a demand moved it.
_DELTA_FIELD_CLASSES: dict[str, ExecutionIntentChangeClass] = MappingProxyType({
    "family": ExecutionIntentChangeClass.OPERATION_ADDED_REMOVED,
    "anchors": ExecutionIntentChangeClass.PROTECTED_ANCHOR_CHANGE,
    "preserved": ExecutionIntentChangeClass.PROTECTED_ANCHOR_CHANGE,
    "contracts": ExecutionIntentChangeClass.QUALITY_CONTRACT_REF_CHANGE,
    "selection_contracts": ExecutionIntentChangeClass.QUALITY_CONTRACT_REF_CHANGE,
    "selection_predicates": ExecutionIntentChangeClass.QUALITY_CONTRACT_REF_CHANGE,
    "demands": ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
    "capability_id": ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
    "mandatory": ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
    "envelope": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "exploration": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "allowed": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "forbidden": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "zones": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "axes": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "shape": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    "branch_policy": ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
})

#: Bundle-level collections compared as whole sets.
_DELTA_SET_VIEWS: tuple[str, ...] = ("anchors", "contracts", "deliverables", "slices")

_DELTA_PRECEDENCE: tuple[ExecutionIntentChangeClass, ...] = (
    ExecutionIntentChangeClass.OPERATION_ADDED_REMOVED,
    ExecutionIntentChangeClass.CAPABILITY_DEMAND_CHANGE,
    ExecutionIntentChangeClass.MUTATION_ENVELOPE_CHANGE,
    ExecutionIntentChangeClass.PROTECTED_ANCHOR_CHANGE,
    ExecutionIntentChangeClass.QUALITY_CONTRACT_REF_CHANGE,
    ExecutionIntentChangeClass.DELIVERABLE_INTENT_CHANGE,
    ExecutionIntentChangeClass.EXPLANATION_ONLY_CHANGE,
    ExecutionIntentChangeClass.NO_SEMANTIC_CHANGE,
)

#: Keys that carry *why* a claim was made rather than the claim itself. The full operation and
#: demand views keep them, because §16 makes an explanation path part of what was emitted; the
#: delta has to look without them, or a revision that only restated its reasoning would compare
#: unequal as an operation and ``EXPLANATION_ONLY_CHANGE`` — the one class §21 exists to name —
#: would never be reachable.
_EXPLANATION_VIEW_KEYS: frozenset[str] = frozenset({"explanations", "originating", "sources"})


def _semantic_view(record: Any) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.fingerprint_inputs().items()
        if key not in _EXPLANATION_VIEW_KEYS
    }


def _explanation_texts(bundle: "ExecutionIntentBundle") -> tuple[str, ...]:
    return sorted(
        {
            entry.text
            for item in bundle.operations
            for entry in item.required_explanation_refs + item.originating_refs
        }
        | {
            entry.text
            for item in bundle.capability_demands
            for entry in item.source_refs
        }
    )


def _delta_view(bundle: "ExecutionIntentBundle") -> dict[str, Any]:
    """The comparable projection of a bundle: coarse sets first, per-operation detail second."""

    return {
        "operations": {item.intent_operation_id: _semantic_view(item) for item in bundle.operations},
        "demands": {item.demand_id: _semantic_view(item) for item in bundle.capability_demands},
        "envelopes": {item.envelope_id: item.fingerprint_inputs() for item in bundle.mutation_envelopes},
        "explorations": {
            item.exploration_id: item.fingerprint_inputs() for item in bundle.explorations
        },
        "loss_rules": {item.rule_id: item.fingerprint_inputs() for item in bundle.loss_rules},
        "anchors": sorted(
            {
                anchor.text
                for item in bundle.operations
                for anchor in item.protected_anchor_refs
            }
            | {
                anchor.text
                for item in bundle.mutation_envelopes
                for anchor in item.reference_anchors
            }
        ),
        "contracts": sorted(
            {
                contract.text
                for item in bundle.operations
                for contract in item.fidelity_contract_refs
            }
            | (
                set()
                if bundle.contract_set_ref is None
                else {bundle.contract_set_ref.text}
            )
        ),
        "deliverables": sorted(item.text for item in bundle.deliverable_refs),
        "slices": sorted(
            {item.text for item in bundle.intent_slice_refs}
            | {item.text for item in bundle.constraint_slice_refs}
        ),
        "explanations": _explanation_texts(bundle),
    }


def execution_intent_delta(
    before: Any,
    after: Any,
    *,
    delta_id: str | None = None,
) -> ExecutionIntentDelta:
    """Classify the move between two execution-intent revisions (§21).

    Both sides are bundles, and the comparison runs over the semantic views: gaps, status and the
    availability observations that produced them are deliberately not inputs. A provider registry
    learning what it can serve is not the brief changing its mind, and a delta that conflated the
    two would tell M16 to recompile workflows whose demands never moved.
    """

    left = ExecutionIntentBundle.coerce(before, "before")
    right = ExecutionIntentBundle.coerce(after, "after")
    left_view = _delta_view(left)
    right_view = _delta_view(right)
    detected: dict[str, ExecutionIntentChangeClass] = {}
    affected_operations: set[str] = set()

    for view_key in _DELTA_RECORD_VIEWS:
        old, new = left_view[view_key], right_view[view_key]
        for ident in sorted(set(old) ^ set(new)):
            detected[f"{view_key}[{ident}]"] = _DELTA_ADDED_REMOVED[view_key]
            if view_key == "operations":
                affected_operations.add(ident)
        for ident in sorted(set(old) & set(new)):
            moved = [
                attribute
                for attribute in sorted(set(old[ident]) | set(new[ident]))
                if old[ident].get(attribute) != new[ident].get(attribute)
            ]
            if not moved:
                continue
            for attribute in moved:
                detected[f"{view_key}[{ident}].{attribute}"] = _DELTA_FIELD_CLASSES.get(
                    attribute, _DELTA_VIEW_DEFAULTS[view_key]
                )
            if view_key == "operations":
                affected_operations.add(ident)

    for view_key in _DELTA_SET_VIEWS:
        if left_view[view_key] != right_view[view_key]:
            detected[view_key] = _DELTA_VIEW_DEFAULTS[view_key]

    if set(left_view["explanations"]) != set(right_view["explanations"]):
        detected["explanations"] = ExecutionIntentChangeClass.EXPLANATION_ONLY_CHANGE

    # Which capabilities a recompile must re-advertise: every demand whose own content moved, plus
    # both sides of a demand that appeared or disappeared. A caller that only relisted provenance
    # moves nothing here, because provenance is not part of the demand's semantic view.
    left_caps = {item.demand_id: item.capability_id for item in left.capability_demands}
    right_caps = {item.demand_id: item.capability_id for item in right.capability_demands}
    affected_capabilities = {
        table[ident]
        for ident in set(left_caps) | set(right_caps)
        for table in (left_caps, right_caps)
        if ident in table
        and left_view["demands"].get(ident) != right_view["demands"].get(ident)
    }

    if not detected:
        classification = ExecutionIntentChangeClass.NO_SEMANTIC_CHANGE
        changed_inputs: tuple[str, ...] = ()
    else:
        semantic = {
            label: kind
            for label, kind in detected.items()
            if kind is not ExecutionIntentChangeClass.EXPLANATION_ONLY_CHANGE
        }
        if not semantic:
            classification = ExecutionIntentChangeClass.EXPLANATION_ONLY_CHANGE
            changed_inputs = ("explanations",)
        else:
            classification = min(
                semantic.values(), key=lambda kind: _DELTA_PRECEDENCE.index(kind)
            )
            labels = set(semantic)
            if "explanations" in detected:
                labels.add("explanations")
            changed_inputs = tuple(sorted(labels))

    operation_ids = sorted(affected_operations & set(right_view["operations"]))
    return ExecutionIntentDelta(
        delta_id=require_identifier(
            delta_id or f"eid-{left.bundle_id}-to-{right.bundle_id}", "delta_id"
        ),
        class_name=classification.value,
        changed_inputs=changed_inputs,
        affected_operation_ids=tuple(operation_ids),
        affected_capability_ids=tuple(sorted(affected_capabilities)),
        explanation_refs=tuple(
            sorted(
                {
                    entry.text: entry
                    for item in right.operations
                    for entry in item.required_explanation_refs
                }.values(),
                key=lambda item: item.text,
            )
        )[:MAX_PROVENANCE_REFS],
        before_fingerprint=left.fingerprint.semantic_digest if left.fingerprint else None,
        after_fingerprint=right.fingerprint.semantic_digest if right.fingerprint else None,
        contract_version=right.contract_version,
    )


# --------------------------------------------------------------------------- #
# §14: the slice a downstream compiler actually consumes
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ExecutionIntentSlice(Record):
    """The minimum sufficient execution intent for one operation (§14).

    Minimality here is checked, not promised: every ref the slice carries has to be reachable from
    the operation it is scoped to, and the slice holds exactly one operation. A "minimum sufficient"
    view that quietly included the rest of the campaign would be the token-blowup this exists to
    avoid, wearing a name that said otherwise.
    """

    slice_id: str
    bundle_ref: SemanticRef
    bundle_digest: str
    operation: IntentOperation
    capability_demands: tuple[CapabilityDemand, ...] = ()
    mutation_envelope: SemanticMutationEnvelope | None = None
    exploration: ExplorationIntent | None = None
    loss_rules: tuple[SemanticLossRule, ...] = ()
    gap_ids: tuple[str, ...] = ()
    explanation_refs: tuple[SemanticRef, ...] = ()
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "slice_id", require_identifier(self.slice_id, "slice_id"))
        object.__setattr__(self, "bundle_ref", SemanticRef.coerce(self.bundle_ref, "bundle_ref"))
        object.__setattr__(self, "bundle_digest", require_digest(self.bundle_digest, "bundle_digest"))
        object.__setattr__(self, "operation", IntentOperation.coerce(self.operation, "operation"))
        demands = tuple(
            sorted(
                (
                    CapabilityDemand.coerce(item, "capability_demands[]")
                    for item in (self.capability_demands or ())
                ),
                key=lambda item: item.demand_id,
            )
        )
        if len({item.demand_id for item in demands}) != len(demands):
            raise SchemaValidationError(f"slice {self.slice_id} repeats a capability demand")
        declared = set(self.operation.capability_demand_ids)
        carried = {item.demand_id for item in demands}
        missing = sorted(declared - carried)
        if missing:
            raise SchemaValidationError(
                f"slice {self.slice_id} omits demands {missing} that its operation declares; a slice "
                "missing a demand its own operation named would be compiled against less than the "
                "brief asked for"
            )
        surplus = sorted(carried - declared)
        if surplus:
            raise SchemaValidationError(
                f"slice {self.slice_id} carries demands {surplus} its operation never named; §14's "
                "minimum is minimum in both directions, and smuggled scope is what re-inflates every "
                "downstream call"
            )
        object.__setattr__(self, "capability_demands", demands)
        if self.mutation_envelope is not None:
            envelope = SemanticMutationEnvelope.coerce(self.mutation_envelope, "mutation_envelope")
            if envelope.operation_id != self.operation.intent_operation_id:
                raise SchemaValidationError(
                    f"slice {self.slice_id} carries an envelope belonging to "
                    f"{envelope.operation_id}; another operation's protections do not travel with this one"
                )
            object.__setattr__(self, "mutation_envelope", envelope)
        if self.exploration is not None:
            exploration = ExplorationIntent.coerce(self.exploration, "exploration")
            if exploration.operation_id != self.operation.intent_operation_id:
                raise SchemaValidationError(
                    f"slice {self.slice_id} carries an exploration belonging to "
                    f"{exploration.operation_id}"
                )
            object.__setattr__(self, "exploration", exploration)
        rules = tuple(
            sorted(
                (SemanticLossRule.coerce(item, "loss_rules[]") for item in (self.loss_rules or ())),
                key=lambda item: item.rule_id,
            )
        )
        for rule in rules:
            if rule.operation_ids and self.operation.intent_operation_id not in rule.operation_ids:
                raise SchemaValidationError(
                    f"slice {self.slice_id} carries loss rule {rule.rule_id}, which names other "
                    "operations only; another operation's tolerance is not this one's to inherit"
                )
        object.__setattr__(self, "loss_rules", rules)
        object.__setattr__(self, "gap_ids", _ids(self.gap_ids, "gap_ids"))
        object.__setattr__(self, "explanation_refs", _refs(self.explanation_refs, "explanation_refs"))
        if not self.explanation_refs:
            raise SchemaValidationError(
                f"slice {self.slice_id} carries no explanation refs; §14 lists explanation and "
                "provenance refs as part of what a downstream compiler must receive"
            )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def included_ref_texts(self) -> frozenset[str]:
        """Every ref the slice speaks of, which is what minimality is checked against."""

        return frozenset(
            {
                entry.text
                for group in (
                    self.operation.source_ref_texts,
                    tuple(entry.text for demand in self.capability_demands for entry in demand.source_refs),
                    tuple(entry.text for rule in self.loss_rules for entry in rule.source_refs),
                    tuple(entry.text for entry in self.explanation_refs),
                    tuple(
                        entry.text
                        for envelope in (self.mutation_envelope,)
                        if envelope is not None
                        for entry in envelope.source_refs
                    ),
                )
                for entry in group
            }
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "operation": self.operation.fingerprint_inputs(),
            "demands": [item.fingerprint_inputs() for item in self.capability_demands],
            "envelope": (
                self.mutation_envelope.fingerprint_inputs() if self.mutation_envelope else None
            ),
            "exploration": self.exploration.fingerprint_inputs() if self.exploration else None,
            "loss_rules": [item.fingerprint_inputs() for item in self.loss_rules],
            "gaps": list(self.gap_ids),
        }


ExecutionIntentSlice.NESTED = {
    "bundle_ref": of(SemanticRef),
    "operation": of(IntentOperation),
    "capability_demands": of(CapabilityDemand),
    "mutation_envelope": of(SemanticMutationEnvelope),
    "exploration": of(ExplorationIntent),
    "loss_rules": of(SemanticLossRule),
    "explanation_refs": of(SemanticRef),
}


# --------------------------------------------------------------------------- #
# §3: the bundle
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ExecutionIntentBundle(Record):
    """The canonical S04 artifact: what behaviour the production requires (§3).

    Three flags say most of what this type is not. ``is_m02_execution_plan`` is False because M02
    owns the causal production graph and the plan that comes back through its port (§2);
    ``may_dispatch`` is False because nothing here names a worker, a queue or a command;
    ``authorizes_side_effects`` is False because §13 lets M03 express a publication desire and the
    boundary in front of it, never the crossing of it.

    The bundle is also the reason a provider cannot quietly lower the ask: capability availability
    arrives as an argument to :func:`compile_execution_intent` and lands in ``status`` and ``gaps``,
    and no field of the fingerprint accepts it.
    """

    bundle_id: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    intent_fingerprint_digest: str
    constraint_fingerprint_digest: str
    fidelity_fingerprint_digest: str
    contract_set_ref: SemanticRef | None = None
    deliverable_refs: tuple[SemanticRef, ...] = ()
    operations: tuple[IntentOperation, ...] = ()
    capability_demands: tuple[CapabilityDemand, ...] = ()
    mutation_envelopes: tuple[SemanticMutationEnvelope, ...] = ()
    explorations: tuple[ExplorationIntent, ...] = ()
    loss_rules: tuple[SemanticLossRule, ...] = ()
    intent_slice_refs: tuple[SemanticRef, ...] = ()
    constraint_slice_refs: tuple[SemanticRef, ...] = ()
    explanation_graph_ref: SemanticRef | None = None
    side_effect_policy_ref: SemanticRef | None = None
    policy_refs: tuple[SemanticRef, ...] = ()
    gaps: tuple[ExecutionIntentGap, ...] = ()
    status: str = ExecutionIntentStatus.COMPLETE.value
    fingerprint: ExecutionIntentFingerprint | None = None
    delta: ExecutionIntentDelta | None = None
    compiler_version: str = EXECUTION_COMPILER_VERSION
    provider_vocabulary_version: str = PROVIDER_VOCABULARY_VERSION
    contract_version: str = ""

    #: §2 and §13, as structure rather than as policy.
    is_m02_execution_plan = False
    may_dispatch = False
    authorizes_side_effects = False
    canonical_semantics = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", require_identifier(self.bundle_id, "bundle_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self,
            "revision_ref",
            require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION),
        )
        for name in (
            "intent_fingerprint_digest",
            "constraint_fingerprint_digest",
            "fidelity_fingerprint_digest",
        ):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        for name in ("contract_set_ref", "explanation_graph_ref", "side_effect_policy_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, SemanticRef.coerce(value, name))
        operations = tuple(
            sorted(
                (IntentOperation.coerce(item, "operations[]") for item in (self.operations or ())),
                key=lambda item: item.intent_operation_id,
            )
        )
        if not operations:
            raise SchemaValidationError(
                f"bundle {self.bundle_id} carries no operation; an execution intent that asks for no "
                "behaviour is an empty claim about the production and would read as coverage"
            )
        if len(operations) > MAX_OPERATIONS_PER_BUNDLE:
            raise SchemaValidationError(
                f"bundle {self.bundle_id} carries {len(operations)} operations, above "
                f"{MAX_OPERATIONS_PER_BUNDLE}; a bundle that wide is a campaign pretending to be one "
                "intent, and §14's slices are the supported way to keep each one addressable"
            )
        duplicated = _duplicates(item.intent_operation_id for item in operations)
        if duplicated:
            raise SchemaValidationError(f"bundle {self.bundle_id} repeats operations {duplicated}")
        object.__setattr__(self, "operations", operations)

        demands = tuple(
            sorted(
                (
                    CapabilityDemand.coerce(item, "capability_demands[]")
                    for item in (self.capability_demands or ())
                ),
                key=lambda item: item.demand_id,
            )
        )
        duplicated = _duplicates(item.demand_id for item in demands)
        if duplicated:
            raise SchemaValidationError(f"bundle {self.bundle_id} repeats capability demands {duplicated}")
        if len(demands) > MAX_CAPABILITY_DEMANDS:
            raise SchemaValidationError(
                f"bundle {self.bundle_id} carries {len(demands)} capability demands, above "
                f"{MAX_CAPABILITY_DEMANDS}; §6's demands are required capabilities, and a list this "
                "long has started describing a runtime instead"
            )
        demand_ids = {item.demand_id for item in demands}
        for operation in operations:
            unknown = sorted(set(operation.capability_demand_ids) - demand_ids)
            if unknown:
                raise SchemaValidationError(
                    f"operation {operation.intent_operation_id} names demands {unknown} the bundle "
                    "does not carry; a dangling demand ref would compile as a step with no capability "
                    "requirement, which is the silent weakening §8 refuses"
                )
        used = {
            demand_id for operation in operations for demand_id in operation.capability_demand_ids
        }
        orphaned = sorted(demand_ids - used)
        if orphaned:
            raise SchemaValidationError(
                f"bundle {self.bundle_id} carries demands {orphaned} no operation names; a capability "
                "nobody asked for would still be advertised to a provider as part of this intent"
            )
        object.__setattr__(self, "capability_demands", demands)

        envelopes = tuple(
            sorted(
                (
                    SemanticMutationEnvelope.coerce(item, "mutation_envelopes[]")
                    for item in (self.mutation_envelopes or ())
                ),
                key=lambda item: item.envelope_id,
            )
        )
        duplicated = _duplicates(item.envelope_id for item in envelopes)
        if duplicated:
            raise SchemaValidationError(f"bundle {self.bundle_id} repeats envelopes {duplicated}")
        by_operation = {item.intent_operation_id: item for item in operations}
        for envelope in envelopes:
            owner = by_operation.get(envelope.operation_id)
            if owner is None:
                raise SchemaValidationError(
                    f"envelope {envelope.envelope_id} belongs to {envelope.operation_id}, which this "
                    "bundle does not carry"
                )
            if owner.mutation_envelope_ref != envelope.envelope_id:
                raise SchemaValidationError(
                    f"envelope {envelope.envelope_id} names operation {owner.intent_operation_id}, "
                    "which references a different envelope; two accounts of one protection are "
                    "resolved by whoever reads first, and neither reading is the brief's"
                )
            conflict = sorted(
                set(envelope.allowed_mutation_classes) & set(owner.forbidden_mutation_classes)
            )
            if conflict:
                raise SchemaValidationError(
                    f"envelope {envelope.envelope_id} allows {conflict}, which operation "
                    f"{owner.intent_operation_id} forbids"
                )
            uncovered = sorted(
                {
                    anchor.text
                    for anchor in envelope.reference_anchors
                    if anchor.ref_id not in {item.ref_id for item in owner.protected_anchor_refs}
                }
            )
            if uncovered and owner.family_enum.requires_envelope:
                raise SchemaValidationError(
                    f"envelope {envelope.envelope_id} anchors on {uncovered}, which operation "
                    f"{owner.intent_operation_id} does not itself protect; an anchor the operation "
                    "never named cannot be preserved by it"
                )
        object.__setattr__(self, "mutation_envelopes", envelopes)

        explorations = tuple(
            sorted(
                (
                    ExplorationIntent.coerce(item, "explorations[]")
                    for item in (self.explorations or ())
                ),
                key=lambda item: item.exploration_id,
            )
        )
        duplicated = _duplicates(item.exploration_id for item in explorations)
        if duplicated:
            raise SchemaValidationError(f"bundle {self.bundle_id} repeats explorations {duplicated}")
        for exploration in explorations:
            owner = by_operation.get(exploration.operation_id)
            if owner is None:
                raise SchemaValidationError(
                    f"exploration {exploration.exploration_id} belongs to an operation this bundle "
                    "does not carry"
                )
            if owner.exploration_ref != exploration.exploration_id:
                raise SchemaValidationError(
                    f"exploration {exploration.exploration_id} is not referenced by "
                    f"{owner.intent_operation_id}, the operation it varies"
                )
            strays = sorted(
                {item.text for item in exploration.varies_zone_refs}
                - {item.text for item in owner.freedom_zone_refs}
            )
            if strays:
                raise SchemaValidationError(
                    f"exploration {exploration.exploration_id} varies zones {strays} the operation "
                    "did not declare free; §7's latitude is granted by the brief, not widened by an "
                    "exploration request"
                )
        object.__setattr__(self, "explorations", explorations)

        rules = tuple(
            sorted(
                (SemanticLossRule.coerce(item, "loss_rules[]") for item in (self.loss_rules or ())),
                key=lambda item: item.rule_id,
            )
        )
        duplicated = _duplicates(item.rule_id for item in rules)
        if duplicated:
            raise SchemaValidationError(f"bundle {self.bundle_id} repeats loss rules {duplicated}")
        for rule in rules:
            unknown = sorted(set(rule.operation_ids) - set(by_operation))
            if unknown:
                raise SchemaValidationError(
                    f"loss rule {rule.rule_id} names operations {unknown} this bundle does not carry"
                )
        object.__setattr__(self, "loss_rules", rules)

        for name in ("deliverable_refs", "intent_slice_refs", "constraint_slice_refs", "policy_refs"):
            object.__setattr__(self, name, _refs(getattr(self, name), name, limit=MAX_ENTRIES_PER_FIELD))

        gaps = tuple(
            sorted(
                (ExecutionIntentGap.coerce(item, "gaps[]") for item in (self.gaps or ())),
                key=lambda item: (item.class_name, item.gap_id),
            )
        )
        duplicated = _duplicates(item.gap_id for item in gaps)
        if duplicated:
            raise SchemaValidationError(f"bundle {self.bundle_id} repeats gaps {duplicated}")
        object.__setattr__(self, "gaps", gaps)

        derived = ExecutionIntentStatus(
            ExecutionIntentStatus.COMPLETE.value
            if not any(item.blocks_completion for item in gaps)
            else ExecutionIntentStatus.INCOMPLETE.value
        )
        supplied = ExecutionIntentStatus.parse(self.status, "status")
        if supplied is not derived:
            raise SchemaValidationError(
                f"bundle {self.bundle_id} declares {supplied.value} while its blocking gaps say "
                f"{derived.value}; §8's gaps exist so an unmet requirement stays visible, and a "
                "status that overrules them is how the visibility is lost"
            )
        object.__setattr__(self, "status", derived.value)

        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(
            self,
            "provider_vocabulary_version",
            require_version_text(self.provider_vocabulary_version, "provider_vocabulary_version"),
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

        _reject_provider_in_bundle(self)

        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", fingerprint_of_execution_intent(self))
        else:
            fingerprint = ExecutionIntentFingerprint.coerce(self.fingerprint, "fingerprint")
            if fingerprint.semantic_digest != content_digest(_fingerprint_view(self)):
                raise SchemaValidationError(
                    f"fingerprint {fingerprint.fingerprint_id} was taken over different execution "
                    "semantics than the bundle it is attached to"
                )
            if fingerprint.compiler_version != self.compiler_version:
                raise SchemaValidationError(
                    f"bundle {self.bundle_id} was compiled by {self.compiler_version} but carries a "
                    f"{fingerprint.compiler_version} fingerprint"
                )
            object.__setattr__(self, "fingerprint", fingerprint)
        if self.delta is not None:
            object.__setattr__(self, "delta", ExecutionIntentDelta.coerce(self.delta, "delta"))

    @property
    def status_enum(self) -> ExecutionIntentStatus:
        return ExecutionIntentStatus.parse(self.status)

    @property
    def operation_ids(self) -> tuple[str, ...]:
        return tuple(item.intent_operation_id for item in self.operations)

    @property
    def blocking_gaps(self) -> tuple[ExecutionIntentGap, ...]:
        return tuple(item for item in self.gaps if item.blocks_completion)

    @property
    def gap_classes(self) -> tuple[str, ...]:
        return tuple(sorted({item.class_name for item in self.gaps}))

    @property
    def mandatory_capability_ids(self) -> tuple[str, ...]:
        return tuple(sorted({item.capability_id for item in self.capability_demands if item.mandatory}))

    @property
    def lossless_items(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                rule.item_ref.text
                for rule in self.loss_rules
                if rule.blocks_provider_admission
            )
        )

    def operation(self, operation_id: str) -> IntentOperation:
        wanted = require_identifier(operation_id, "operation_id")
        for item in self.operations:
            if item.intent_operation_id == wanted:
                return item
        raise SchemaValidationError(
            f"bundle {self.bundle_id} carries no operation {wanted}"
        )

    def explanation(self) -> dict[str, Any]:
        """The §17 questions this bundle can answer without a provider's help."""

        return {
            "operations": {
                item.intent_operation_id: {
                    "family": item.family,
                    "because": sorted(entry.text for entry in item.originating_refs),
                    "explains": sorted(entry.text for entry in item.required_explanation_refs),
                    "completion": item.completion_semantics,
                    "side_effect": item.side_effect_class,
                    "needs_approval": item.needs_approval_boundary,
                }
                for item in self.operations
            },
            "capabilities": {
                item.demand_id: {
                    "capability": item.capability_id,
                    "mandatory": item.mandatory,
                    "because": sorted(entry.text for entry in item.source_refs),
                }
                for item in self.capability_demands
            },
            "why_nothing_lower": {
                "compiler": self.compiler_version,
                "excluded_from_fingerprint": list(FINGERPRINT_EXCLUSIONS),
            },
            "unrepresented": [
                {"class": item.class_name, "detail": item.detail, "capability": item.capability_id}
                for item in self.gaps
            ],
        }


ExecutionIntentBundle.NESTED = {
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "contract_set_ref": of(SemanticRef),
    "deliverable_refs": of(SemanticRef),
    "operations": of(IntentOperation),
    "capability_demands": of(CapabilityDemand),
    "mutation_envelopes": of(SemanticMutationEnvelope),
    "explorations": of(ExplorationIntent),
    "loss_rules": of(SemanticLossRule),
    "intent_slice_refs": of(SemanticRef),
    "constraint_slice_refs": of(SemanticRef),
    "explanation_graph_ref": of(SemanticRef),
    "side_effect_policy_ref": of(SemanticRef),
    "policy_refs": of(SemanticRef),
    "gaps": of(ExecutionIntentGap),
    "fingerprint": of(ExecutionIntentFingerprint),
    "delta": of(ExecutionIntentDelta),
}


def _duplicates(values: Iterable[Any]) -> list[str]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sorted(name for name, total in counts.items() if total > 1)


def _reject_provider_in_bundle(bundle: ExecutionIntentBundle) -> None:
    """§7 over everything the bundle asserts, with its own diagnostics excluded.

    Gap details are M03's prose about what failed, and a sentence like "no provider can serve
    this" must not be refused for containing the word it is about. Everything the bundle *claims*
    — operations, demands, envelopes, explorations, loss rules, refs and ids — is scanned.
    """

    scan = {
        "operations": [item.to_payload() for item in bundle.operations],
        "demands": [item.to_payload() for item in bundle.capability_demands],
        "envelopes": [item.to_payload() for item in bundle.mutation_envelopes],
        "explorations": [item.to_payload() for item in bundle.explorations],
        "loss_rules": [item.to_payload() for item in bundle.loss_rules],
        "refs": sorted(
            {entry.text for group in (
                bundle.deliverable_refs,
                bundle.intent_slice_refs,
                bundle.constraint_slice_refs,
                bundle.policy_refs,
            ) for entry in group}
            | {
                optional.text
                for optional in (
                    bundle.contract_set_ref,
                    bundle.explanation_graph_ref,
                    bundle.side_effect_policy_ref,
                )
                if optional is not None
            }
        ),
        "ids": [bundle.bundle_id, *bundle.operation_ids]
        + [item.demand_id for item in bundle.capability_demands],
    }
    found = find_provider_vocabulary(scan)
    if found:
        raise SchemaValidationError(
            f"bundle {bundle.bundle_id} carries provider or runtime vocabulary {list(found)}; §7 "
            "keeps implementation names out of canonical execution intent, and a later compiler "
            "chooses them"
        )


# --------------------------------------------------------------------------- #
# §14, §10: consumption boundaries
# --------------------------------------------------------------------------- #


def execution_slice_for(bundle: Any, operation_id: str) -> ExecutionIntentSlice:
    """Project the minimum sufficient execution intent for one operation (§14).

    Everything carried here is reachable from that operation: its own refs, the demands it names,
    the envelope and exploration that bind it, and the loss rules that address it. The slice
    cannot grow, because it is built from one operation's declarations and nothing else.
    """

    source = ExecutionIntentBundle.coerce(bundle, "bundle")
    wanted = require_identifier(operation_id, "operation_id")
    operation = source.operation(wanted)
    demands = tuple(
        sorted(
            (
                item
                for item in source.capability_demands
                if item.demand_id in set(operation.capability_demand_ids)
            ),
            key=lambda item: item.demand_id,
        )
    )
    envelope = next(
        (item for item in source.mutation_envelopes if item.envelope_id == operation.mutation_envelope_ref),
        None,
    )
    exploration = next(
        (item for item in source.explorations if item.exploration_id == operation.exploration_ref),
        None,
    )
    rules = tuple(
        sorted(
            (
                item
                for item in source.loss_rules
                if not item.operation_ids or wanted in item.operation_ids
            ),
            key=lambda item: item.rule_id,
        )
    )
    relevant = {rule.item_ref.text for rule in rules}
    for anchor in operation.protected_anchor_refs:
        relevant.add(anchor.text)
    gap_ids = tuple(
        sorted(
            item.gap_id
            for item in source.gaps
            if item.operation_id in {None, wanted}
            and (item.operation_id == wanted or item.capability_id in {d.capability_id for d in demands})
        )
    )
    explanations = tuple(
        sorted(
            {
                entry.text: entry
                for entry in tuple(operation.required_explanation_refs)
                + tuple(operation.originating_refs)
            }.values(),
            key=lambda item: item.text,
        )
    )
    return ExecutionIntentSlice(
        slice_id=f"slice-{source.bundle_id}-{wanted}",
        bundle_ref=SemanticRef(
            kind=RefKind.EXECUTION_BUNDLE.value,
            ref_id=source.bundle_id,
            content_digest=canonical_execution_digest(source),
        ),
        bundle_digest=canonical_execution_digest(source),
        operation=operation,
        capability_demands=demands,
        mutation_envelope=envelope,
        exploration=exploration,
        loss_rules=rules,
        gap_ids=gap_ids,
        explanation_refs=explanations,
        contract_version=source.contract_version,
    )


def require_complete_execution_intent(bundle: Any, *, action: str) -> ExecutionIntentBundle:
    """Gate downstream consumption on the intent being fully represented.

    The error quotes the gaps rather than summarizing them, because the useful information is
    *which* requirement has no path — that is the thing a routing module can act on.
    """

    source = ExecutionIntentBundle.coerce(bundle, "bundle")
    label = require_text(action, "action", maximum=64)
    if source.status_enum.fully_represented:
        return source
    blocking = source.blocking_gaps
    quoted = "; ".join(f"{item.class_name}: {item.detail}" for item in blocking[:4])
    raise CapabilityGapError(
        f"cannot {label} while the execution intent is {source.status}: {quoted}"
        + (f" (+{len(blocking) - 4} more)" if len(blocking) > 4 else "")
    )


def reject_provider_admission(receipt: Any, bundle: Any, *, action: str = "admit the provider plan") -> ProviderTranslationReceipt:
    """Refuse a provider plan whose translation lost required meaning (§10).

    A ``LOSSLESS_REQUIRED`` item the provider did not answer for is treated as unrepresented, not
    as unanswered: silence is not a disposition, and the admission decision cannot depend on
    whether somebody happened to fill in a row.
    """

    answer = ProviderTranslationReceipt.coerce(receipt, "receipt")
    source = ExecutionIntentBundle.coerce(bundle, "bundle")
    label = require_text(action, "action", maximum=64)
    if answer.bundle_fingerprint_digest != canonical_execution_digest(source):
        raise AdmissionRefusedError(
            f"cannot {label}: receipt {answer.receipt_id} attests to bundle digest "
            f"{answer.bundle_fingerprint_digest} while the bundle now hashes to "
            f"{canonical_execution_digest(source)}; a translation of a superseded intent is not a "
            "translation of this one"
        )
    answered = answer.item_for
    failures: list[str] = []
    for item_ref in source.lossless_items:
        entry = answered.get(item_ref)
        if entry is None:
            failures.append(f"{item_ref} was never answered for")
        elif not entry.disposition_enum.satisfies_lossless:
            failures.append(f"{item_ref} came back {entry.disposition}")
    if failures:
        raise AdmissionRefusedError(
            f"cannot {label}: §10 refuses a provider that cannot represent a LOSSLESS_REQUIRED "
            f"obligation — {'; '.join(failures)}. The intent stays as it is; routing may find "
            "another provider or workflow"
        )
    return answer


# --------------------------------------------------------------------------- #
# §8: compilation
# --------------------------------------------------------------------------- #


def compile_execution_intent(
    *,
    bundle_id: str,
    brief_ref: Any,
    revision_ref: Any,
    intent_fingerprint_digest: Any,
    constraint_fingerprint_digest: Any,
    fidelity_fingerprint_digest: Any,
    operations: Iterable[Any],
    capability_demands: Iterable[Any] = (),
    mutation_envelopes: Iterable[Any] = (),
    explorations: Iterable[Any] = (),
    loss_rules: Iterable[Any] = (),
    deliverable_refs: Iterable[Any] = (),
    contract_set_ref: Any = None,
    intent_slice_refs: Iterable[Any] = (),
    constraint_slice_refs: Iterable[Any] = (),
    explanation_graph_ref: Any = None,
    side_effect_policy_ref: Any = None,
    policy_refs: Iterable[Any] = (),
    known_capabilities: Iterable[str] = (),
    stale_capabilities: Iterable[str] = (),
    supported_semantic_types: Iterable[str] = (),
    unservable_anchor_refs: Iterable[Any] = (),
    translation_receipts: Iterable[Any] = (),
    previous: Any = None,
    compiler_version: str = EXECUTION_COMPILER_VERSION,
    provider_vocabulary_version: str = PROVIDER_VOCABULARY_VERSION,
    status: str | None = None,
    fingerprint: Any = None,
) -> ExecutionIntentBundle:
    """Compile admitted semantics into an execution intent, or into the gaps that stop it.

    Capability availability enters here and only here. It is matched against the demands, and what
    it can change is the bundle's status and gap list — never an operation, never a demand, never
    the fingerprint. That is the difference between "no provider can do this yet" and "the
    production does not need it", and only the first one is true.
    """

    ident = require_identifier(bundle_id, "bundle_id")
    operation_records = tuple(
        sorted(
            (IntentOperation.coerce(item, "operations[]") for item in (operations or ())),
            key=lambda item: item.intent_operation_id,
        )
    )
    demand_records = tuple(
        sorted(
            (
                CapabilityDemand.coerce(item, "capability_demands[]")
                for item in (capability_demands or ())
            ),
            key=lambda item: item.demand_id,
        )
    )
    envelope_records = tuple(
        sorted(
            (
                SemanticMutationEnvelope.coerce(item, "mutation_envelopes[]")
                for item in (mutation_envelopes or ())
            ),
            key=lambda item: item.envelope_id,
        )
    )
    exploration_records = tuple(
        sorted(
            (ExplorationIntent.coerce(item, "explorations[]") for item in (explorations or ())),
            key=lambda item: item.exploration_id,
        )
    )
    rule_records = tuple(
        sorted(
            (SemanticLossRule.coerce(item, "loss_rules[]") for item in (loss_rules or ())),
            key=lambda item: item.rule_id,
        )
    )
    receipt_records = tuple(
        sorted(
            (
                ProviderTranslationReceipt.coerce(item, "translation_receipts[]")
                for item in (translation_receipts or ())
            ),
            key=lambda item: item.receipt_id,
        )
    )
    previous_bundle = ExecutionIntentBundle.coerce(previous, "previous") if previous is not None else None
    served = _slug_set(known_capabilities, "known_capabilities")
    out_of_date = _slug_set(stale_capabilities, "stale_capabilities")
    typed = _slug_set(supported_semantic_types, "supported_semantic_types")
    unservable_anchors = _refs(unservable_anchor_refs, "unservable_anchor_refs")
    unservable_anchor_ids = {item.ref_id for item in unservable_anchors}

    gaps: list[ExecutionIntentGap] = []

    def record(
        class_name: ExecutionGapClass,
        detail: str,
        *,
        refs: Iterable[Any] = (),
        capability_id: str | None = None,
        operation_id: str | None = None,
        anchor: SemanticRef | None = None,
        mandatory: bool = True,
        remedy: str | None = None,
        path: str | None = None,
    ) -> ExecutionIntentGap:
        item = ExecutionIntentGap(
            gap_id=f"{ident}-gap-{len(gaps) + 1:03d}",
            class_name=class_name.value,
            detail=detail,
            source_refs=tuple(refs) or tuple(_all_refs(operation_records, demand_records)),
            semantic_path=path,
            capability_id=capability_id,
            operation_id=operation_id,
            anchor_ref=anchor,
            mandatory_origin=mandatory,
            remedy=remedy,
            contract_version=CONTRACT_VERSION,
        )
        gaps.append(item)
        return item

    # --- §8: capability availability, matched demand by demand in sorted order ---- #
    # Iterating the demands rather than the availability list is what makes the result
    # independent of the order the observations arrived in (§25 proof item 1).
    unserved: set[str] = set()
    for demand in demand_records:
        sources = tuple(demand.source_refs)
        if demand.capability_id in out_of_date:
            record(
                ExecutionGapClass.STALE_PROVIDER_CAPABILITY,
                f"the advertised support for {demand.capability_id} is stale, so nothing here can be "
                "trusted to still hold; the demand stands and the observation is what is refused",
                refs=sources,
                capability_id=demand.capability_id,
                mandatory=False,
                remedy="re-check the capability registry; a stale observation is not an absent capability",
                path=demand.semantic_scope[0],
            )
        if demand.capability_id in served and demand.capability_id not in out_of_date:
            continue
        unserved.add(demand.capability_id)
        for anchor in demand.protected_anchor_refs:
            if anchor.ref_id in unservable_anchor_ids:
                record(
                    ExecutionGapClass.PROTECTED_ANCHOR_UNSUPPORTED,
                    f"{demand.capability_id} would have to preserve anchor {anchor.text}, which no "
                    "known capability can hold; §8 records the hole instead of dropping the anchor",
                    refs=tuple(sources) + (anchor,),
                    capability_id=demand.capability_id,
                    anchor=anchor,
                    mandatory=demand.mandatory,
                    remedy="a capability that preserves the anchor, or an admitted revision that "
                    "releases it",
                )
        record(
            ExecutionGapClass.MISSING_CAPABILITY,
            f"no known capability satisfies {demand.capability_id}, which this bundle demands for "
            f"{', '.join(demand.semantic_scope)}; §8 keeps the demand intact — routing may find "
            "another provider, workflow or budget, and required meaning does not move",
            refs=sources,
            capability_id=demand.capability_id,
            mandatory=demand.mandatory,
            remedy="register a capability that serves the demand, or have the requirement's owner "
            "change it through governed revision",
            path=demand.semantic_scope[0],
        )

    # --- §8: semantic types nothing can carry ------------------------------------ #
    if typed:
        for operation in operation_records:
            for entry in operation.output_type_refs:
                if entry.ref_id not in typed:
                    record(
                        ExecutionGapClass.SEMANTIC_TYPE_UNSUPPORTED,
                        f"operation {operation.intent_operation_id} outputs semantic type "
                        f"{entry.text}, which no declared type registry carries; the output cannot be "
                        "composed anywhere, so the gap is recorded rather than the type rewritten",
                        refs=tuple(operation.originating_refs) + (entry,),
                        operation_id=operation.intent_operation_id,
                        path=None,
                        remedy="admit the semantic type, or re-express the deliverable in an admitted one",
                    )

    # --- §8: references that carry nothing -------------------------------------- #
    declared_demands = {item.demand_id for item in demand_records}
    for operation in operation_records:
        if operation.family_enum.mutates_existing and not operation.protected_anchor_refs:
            anchored = any(
                item.reference_anchors
                for item in envelope_records
                if item.operation_id == operation.intent_operation_id
            )
            if not anchored:
                record(
                    ExecutionGapClass.INSUFFICIENT_REFERENCE_SUPPORT,
                    f"operation {operation.intent_operation_id} edits an admitted subject while "
                    "nothing anchors what it must stay; §12's envelope protects properties, and with "
                    "no reference anchor at all the protection has nothing to be checked against",
                    refs=operation.originating_refs,
                    operation_id=operation.intent_operation_id,
                    remedy="cite the identity or structural anchors the edit must preserve",
                )
        if not operation.fidelity_contract_refs and contract_set_ref is None:
            record(
                ExecutionGapClass.NO_QUALITY_EVIDENCE_PATH,
                f"operation {operation.intent_operation_id} has no Fidelity Contract to satisfy and "
                "the bundle names no contract set; §8 records the missing evidence path instead of "
                "shipping work nobody will judge",
                refs=operation.originating_refs,
                operation_id=operation.intent_operation_id,
                remedy="compile and link the S03 contract for this subject",
            )
        dangling = sorted(set(operation.capability_demand_ids) - declared_demands)
        if dangling:
            raise SchemaValidationError(
                f"operation {operation.intent_operation_id} names demands {dangling} that this "
                "compilation was not given; the requirement exists in the brief and has no carrier "
                "here, so the compilation is malformed rather than the world short"
            )

    # --- §13: the approval boundary a desire cannot replace --------------------- #
    for operation in operation_records:
        if operation.needs_approval_boundary and side_effect_policy_ref is None:
            record(
                ExecutionGapClass.SIDE_EFFECT_POLICY_UNRESOLVED,
                f"operation {operation.intent_operation_id} asks for "
                f"{operation.side_effect_class} with no approval boundary named; §13 is explicit that "
                "a brief saying 'publish it' expresses a desire and not a permission, and M02/M59 "
                "keep the authority either way",
                refs=operation.originating_refs,
                operation_id=operation.intent_operation_id,
                remedy="bind the governed side-effect policy or an explicit approval ref",
            )

    # --- §10: translation that lost meaning ------------------------------------ #
    for receipt in receipt_records:
        answered = receipt.item_for
        for rule in rule_records:
            entry = answered.get(rule.item_ref.text)
            if entry is None or entry.disposition_enum.satisfies_lossless:
                continue
            if not rule.blocks_provider_admission:
                continue
            record(
                ExecutionGapClass.PROVIDER_TRANSLATION_LOSS,
                f"provider translation returned {entry.disposition} for {rule.item_ref.text}, which "
                "this bundle marks LOSSLESS_REQUIRED; §10 refuses the plan and §23 forbids repairing "
                "the gap by relaxing the obligation",
                refs=tuple(rule.source_refs),
                mandatory=False,
                remedy="another provider, a repair loop, or an authorized policy change",
            )

    # --- §8, §9: an obligation that has no possible representation --------------- #
    for rule in rule_records:
        if rule.blocks_provider_admission and rule.item_ref.kind == RefKind.FREEDOM_ZONE.value:
            record(
                ExecutionGapClass.UNREPRESENTABLE_CONSTRAINT,
                f"loss rule {rule.rule_id} demands {rule.item_ref.text} be represented losslessly, "
                "and that item is a Freedom Zone; §9 gives the provider the choice inside a zone, so "
                "there is no fixed answer a translation could carry. The obligation is unrepresentable "
                "as written and is not quietly reclassified",
                refs=tuple(rule.source_refs),
                remedy="declare the zone's contents CREATIVE_FREEDOM, or restate the requirement as "
                "an admitted constraint with an anchor the operation protects",
            )

    if any(item.blocks_completion for item in gaps):
        derived_status = ExecutionIntentStatus.INCOMPLETE.value
    else:
        derived_status = ExecutionIntentStatus.COMPLETE.value
    if status is not None and ExecutionIntentStatus.parse(status, "status").value != derived_status:
        raise SchemaValidationError(
            f"compilation of {ident} was handed {status} while its gaps say {derived_status}"
        )

    candidate = ExecutionIntentBundle(
        bundle_id=ident,
        brief_ref=brief_ref,
        revision_ref=revision_ref,
        intent_fingerprint_digest=intent_fingerprint_digest,
        constraint_fingerprint_digest=constraint_fingerprint_digest,
        fidelity_fingerprint_digest=fidelity_fingerprint_digest,
        contract_set_ref=contract_set_ref,
        deliverable_refs=_refs(deliverable_refs, "deliverable_refs", limit=MAX_ENTRIES_PER_FIELD),
        operations=operation_records,
        capability_demands=demand_records,
        mutation_envelopes=envelope_records,
        explorations=exploration_records,
        loss_rules=rule_records,
        intent_slice_refs=_refs(intent_slice_refs, "intent_slice_refs"),
        constraint_slice_refs=_refs(constraint_slice_refs, "constraint_slice_refs"),
        explanation_graph_ref=explanation_graph_ref,
        side_effect_policy_ref=side_effect_policy_ref,
        policy_refs=_refs(policy_refs, "policy_refs"),
        gaps=tuple(gaps),
        status=derived_status,
        delta=None,
        compiler_version=compiler_version,
        provider_vocabulary_version=provider_vocabulary_version,
        fingerprint=fingerprint,
        contract_version=CONTRACT_VERSION,
    )
    if previous_bundle is None:
        return candidate
    # Rebuilt through the constructor rather than patched in place, so the delta is validated by
    # the same rules that govern a hand-authored one. The fingerprint view excludes ``delta``,
    # so the recompiled bundle keeps the digest the gap analysis was run over.
    return replace(
        candidate, delta=execution_intent_delta(previous_bundle, candidate)
    )


def _all_refs(
    operations: Iterable[IntentOperation], demands: Iterable[CapabilityDemand]
) -> tuple[SemanticRef, ...]:
    """Fallback provenance for a gap that could not inherit a more specific source."""

    out: dict[str, SemanticRef] = {}
    for item in operations:
        for entry in item.originating_refs:
            out[entry.text] = entry
    for item in demands:
        for entry in item.source_refs:
            out[entry.text] = entry
    return tuple(out[key] for key in sorted(out))
