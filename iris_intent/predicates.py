"""F-M03-05 predicate vocabulary: bounded, typed, and incapable of carrying code.

A constraint predicate is a named signature the kernel already understands, not an
expression it is asked to evaluate (§5.12). The distinction is not stylistic: the moment a
constraint may hold arbitrary logic, "the brief says no" stops being auditable, because
answering it requires running the thing. So arguments declare a type from a closed set,
values are validated against that type, and the only interpretation available is the one the
signature describes.

Extension predicates enter through a versioned registry with a trust tier, which is what
makes §5.13 enforceable: a *mandatory* constraint whose predicate is unknown cannot be
skipped, because skipping it would silently satisfy a requirement nobody checked. Unknown and
optional is a gap to report; unknown and mandatory is a refusal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, encode_payload, of
from .errors import (
    LimitExceededError,
    PredicateError,
    SchemaValidationError,
    UntrustedExtensionError,
)
from .identity import SemanticRef
from .limits import MAX_PREDICATE_ARGUMENTS, MAX_REGISTRY_EXTENSIONS
from .versions import require_identifier, require_semantic_path, require_text

__all__ = [
    "CORE_PREDICATES",
    "MAX_PREDICATE_ARGUMENTS",
    "MAX_REGISTRY_EXTENSIONS",
    "PredicateArgument",
    "PredicateCall",
    "PredicateRegistry",
    "PredicateSignature",
    "PredicateTrust",
    "ValueType",
    "reject_interpolation",
    "require_known_predicate",
]


class ValueType(Labeled):
    """The closed set of argument types a predicate may declare.

    There is deliberately no ``CODE``, ``EXPRESSION`` or ``TEMPLATE`` member. The absence is
    the invariant: an author who wants to write a rule that cannot be expressed as one of
    these values is asking for a language, and a language in a constraint set is a
    second kernel that nobody reviews (§5.12).
    """

    TEXT = "TEXT"
    IDENTIFIER = "IDENTIFIER"
    PATH = "PATH"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    DIGEST = "DIGEST"
    REF = "REF"
    CHOICE = "CHOICE"

    @classmethod
    def validate(cls, value: Any, type_name: "ValueType", field_name: str, allowed: tuple[str, ...] = ()) -> Any:
        if type_name is ValueType.TEXT:
            return require_text(value, field_name, maximum=2048)
        if type_name is ValueType.IDENTIFIER:
            return require_identifier(value, field_name)
        if type_name is ValueType.PATH:
            return require_semantic_path(value, field_name)
        if type_name is ValueType.NUMBER:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise PredicateError(f"{field_name} must be a number, got {value!r}")
            return float(value)
        if type_name is ValueType.BOOLEAN:
            if not isinstance(value, bool):
                raise PredicateError(f"{field_name} must be a boolean, got {value!r}")
            return value
        if type_name is ValueType.DIGEST:
            from .versions import require_digest

            return require_digest(value, field_name)
        if type_name is ValueType.REF:
            return SemanticRef.coerce(value, field_name)
        if type_name is ValueType.CHOICE:
            choice = require_text(value, field_name, maximum=128)
            if allowed and choice not in allowed:
                raise PredicateError(
                    f"{field_name} must be one of {sorted(allowed)}, got {choice!r}"
                )
            return choice
        raise PredicateError(f"{field_name} declares unsupported type {type_name.value}")


class PredicateTrust(Labeled):
    """How much weight an extension predicate carries inside M03.

    Namespaced apart from M01's evaluator trust tiers on purpose: M03's tiers govern whether a
    *semantic* predicate may be relied upon, and sharing one ladder with M01 would let a
    qualified evaluator registration imply that a predicate is core, which is a grant of
    capability M03 is not allowed to make (§5.17).
    """

    CORE = "CORE"
    QUALIFIED = "QUALIFIED"
    EXPERIMENTAL = "EXPERIMENTAL"
    QUARANTINED = "QUARANTINED"

    @property
    def may_be_mandatory(self) -> bool:
        """An experimental predicate can be asked for; a quarantined one cannot be relied on at all.

        Mandatory-plus-experimental is allowed and then flagged, because banning it outright
        would mean a project could not write a requirement against a predicate its own team is
        piloting — while a *quarantined* predicate has already been found unreliable, and
        treating it as load-bearing would launder that finding.
        """

        return self is not PredicateTrust.QUARANTINED


#: Polarity labels a signature admits unless it narrows them itself. Spelled here and in
#: ``constraints`` from the same words so a signature cannot silently admit a polarity the
#: constraint layer does not define.
_ALL_POLARITIES = ("ALLOW", "AVOID", "FORBID", "PREFER", "REQUIRE")

# Marker sequences that would mean something to a downstream interpolating renderer. A
# constraint value is data; if it carries a template or expression marker the value is not
# data any more, it is a payload aimed at whatever reads it last.
_INTERPOLATION_MARKERS = ("${", "{{", "{%", "<%", "%>")
_CONTROL_ESCAPE = re.compile(r"\\[nrt]")


def reject_interpolation(value: str, field_name: str) -> None:
    for marker in _INTERPOLATION_MARKERS:
        if marker in value:
            raise UntrustedExtensionError(
                f"{field_name} contains the interpolation marker {marker!r}; M03 constraint values are "
                "data and are never spliced into a template, so a value shaped like one is a payload "
                "aimed at a later renderer rather than a rule about the work"
            )
    if _CONTROL_ESCAPE.search(value):
        raise UntrustedExtensionError(
            f"{field_name} carries an escaped control sequence; write the value plainly or not at all"
        )


@dataclass(frozen=True)
class PredicateArgument(Record):
    """One declared slot of a predicate signature.

    ``allowed_values`` makes ``CHOICE`` finite, which is the difference between a predicate
    the kernel can decide and a string it has to develop an opinion about.
    """

    name: str
    type: str
    required: bool = True
    allowed_values: tuple[str, ...] = ()
    description: str | None = None

    def __post_init__(self) -> None:
        name = require_identifier(self.name, "name")
        reject_interpolation(name, "name")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "type", ValueType.parse(self.type, "type").value)
        if not isinstance(self.required, bool):
            raise SchemaValidationError("required must be a boolean")
        allowed = tuple(sorted({require_text(item, "allowed_values[]", maximum=128) for item in (self.allowed_values or ())}))
        if self.type == ValueType.CHOICE.value and not allowed:
            raise PredicateError(
                f"argument {name} is a CHOICE with no admitted values, so no call could satisfy it"
            )
        object.__setattr__(self, "allowed_values", allowed)
        if self.description is not None:
            object.__setattr__(self, "description", require_text(self.description, "description", maximum=512))

    @property
    def type_name(self) -> ValueType:
        return ValueType.parse(self.type)

    def accept(self, value: Any, predicate: str) -> Any:
        try:
            return ValueType.validate(value, self.type_name, f"{predicate}.{self.name}", self.allowed_values)
        except (TypeError, ValueError) as error:
            raise PredicateError(f"{predicate}.{self.name} is not a valid {self.type}: {error}") from error


@dataclass(frozen=True)
class PredicateSignature(Record):
    """A named, versioned predicate the kernel knows how to interpret.

    ``interpretation`` is a declared description of what satisfying the predicate means,
    stored rather than implied: two teams that disagree about what ``matches_palette`` should
    check need the disagreement visible in the registry, not reconstructed from a diff of
    call sites.
    """

    predicate_id: str
    version: str
    semantic_path: str
    trust: str = "CORE"
    argument_types: tuple[PredicateArgument, ...] = ()
    polarity_admitted: tuple[str, ...] = ()
    interpretation: str | None = None
    extension_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        predicate_id = require_identifier(self.predicate_id, "predicate_id")
        reject_interpolation(predicate_id, "predicate_id")
        object.__setattr__(self, "predicate_id", predicate_id)
        object.__setattr__(self, "version", require_text(self.version, "version", maximum=64))
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        object.__setattr__(self, "trust", PredicateTrust.parse(self.trust, "trust").value)
        arguments = tuple(
            PredicateArgument.coerce(item, "argument_types[]") for item in _seq(self.argument_types, "argument_types")
        )
        if len(arguments) > MAX_PREDICATE_ARGUMENTS:
            raise LimitExceededError(f"argument_types exceeds {MAX_PREDICATE_ARGUMENTS}")
        names = [item.name for item in arguments]
        duplicates = sorted({item for item in names if names.count(item) > 1})
        if duplicates:
            raise SchemaValidationError(f"argument_types contains duplicate names: {duplicates}")
        object.__setattr__(self, "argument_types", tuple(sorted(arguments, key=lambda item: item.name)))
        polarities = tuple(sorted({_polarity_token(item) for item in _seq(self.polarity_admitted, "polarity_admitted")}))
        object.__setattr__(self, "polarity_admitted", polarities or _ALL_POLARITIES)
        if self.interpretation is not None:
            reject_interpolation(self.interpretation, "interpretation")
            object.__setattr__(self, "interpretation", require_text(self.interpretation, "interpretation", maximum=1024))
        if self.extension_ref is not None:
            object.__setattr__(self, "extension_ref", SemanticRef.coerce(self.extension_ref, "extension_ref"))

    @property
    def reference(self) -> str:
        return f"{self.predicate_id}@{self.version}"

    @property
    def is_core(self) -> bool:
        return PredicateTrust.parse(self.trust) is PredicateTrust.CORE

    @property
    def trust_tier(self) -> PredicateTrust:
        return PredicateTrust.parse(self.trust)

    def accepts_polarity(self, polarity: str) -> bool:
        return _polarity_token(polarity) in self.polarity_admitted

    def bind(self, arguments: Any, *, mandatory: bool = False) -> "PredicateCall":
        return PredicateCall(
            predicate_id=self.predicate_id,
            version=self.version,
            arguments=dict(arguments or {}),
            mandatory=mandatory,
        )


PredicateSignature.NESTED = {"argument_types": of(PredicateArgument), "extension_ref": of(SemanticRef)}


@dataclass(frozen=True)
class PredicateCall(Record):
    """A predicate applied to typed arguments — the executable-looking half that cannot execute.

    The call records the signature version it was built against, so a constraint compiled
    under ``matches_palette@1`` keeps meaning that rule after the registry ships version two.
    Without the pin, updating a predicate definition would silently reinterpret every brief
    that ever used it.
    """

    predicate_id: str
    version: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    mandatory: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "predicate_id", require_identifier(self.predicate_id, "predicate_id"))
        object.__setattr__(self, "version", require_text(self.version, "version", maximum=64))
        if not isinstance(self.arguments, Mapping):
            raise SchemaValidationError("arguments must be a mapping of argument name to value")
        object.__setattr__(
            self,
            "arguments",
            dict(sorted((require_identifier(key, "arguments key"), _scalar(value)) for key, value in self.arguments.items())),
        )
        if not isinstance(self.mandatory, bool):
            raise SchemaValidationError("mandatory must be a boolean")

    @property
    def reference(self) -> str:
        return f"{self.predicate_id}@{self.version}"

    def validate_against(self, signature: PredicateSignature) -> "PredicateCall":
        """Type-check the call and return it normalised, refusing anything unannounced."""

        declared = {item.name: item for item in signature.argument_types}
        unexpected = sorted(set(self.arguments) - set(declared))
        if unexpected:
            raise PredicateError(
                f"{self.reference} does not declare {unexpected}; a predicate cannot gain an argument at "
                "a call site, because nobody reviewing the signature would see it"
            )
        missing = sorted(name for name, item in declared.items() if item.required and name not in self.arguments)
        if missing:
            raise PredicateError(f"{self.reference} is missing required arguments: {missing}")
        normalized = {
            name: declared[name].accept(value, self.predicate_id) for name, value in self.arguments.items()
        }
        if signature.reference != self.reference:
            raise PredicateError(
                f"{self.reference} was validated against {signature.reference}; a call must name the "
                "signature version it was built against or the check proves nothing"
            )
        return PredicateCall(
            predicate_id=self.predicate_id,
            version=self.version,
            arguments=normalized,
            mandatory=self.mandatory,
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        """Canonical form for fingerprints: the pinned reference plus sorted arguments.

        Arguments arrive already sorted by name, so the payload is stable; the version stays in
        because re-interpreting a rule under a new signature version is a semantic change, not a
        reformatting (§5.43).
        """

        return {"predicate": self.reference, "arguments": encode_payload(self.arguments), "mandatory": self.mandatory}


def _scalar(value: Any) -> Any:
    if isinstance(value, SemanticRef):
        return value.to_payload()
    if isinstance(value, bool) or isinstance(value, (str, int, float)) or value is None:
        return value
    raise PredicateError(
        f"predicate argument values must be scalars, a ref or None, got {type(value).__name__}; a "
        "nested structure here is a schema someone else will have to invent a meaning for"
    )


class PredicateRegistry:
    """Versioned lookup for admitted predicates, with no mutable global instance.

    Registries are passed in, never reached for. A module-level singleton would let two
    compilations in one process disagree about what a predicate means depending on import
    order, and the resulting fingerprints would differ for reasons no record explains.
    """

    def __init__(self, signatures: Iterable[PredicateSignature] = ()) -> None:
        self._by_reference: dict[str, PredicateSignature] = {}
        self._latest: dict[str, str] = {}
        for signature in signatures:
            self.register(signature)

    def register(self, signature: Any) -> "PredicateRegistry":
        item = PredicateSignature.coerce(signature, "signature")
        if item is not signature and not isinstance(signature, PredicateSignature):
            raise SchemaValidationError("signature must be a PredicateSignature or its payload")
        if len(self._by_reference) >= MAX_REGISTRY_EXTENSIONS:
            raise LimitExceededError(
                f"predicate registry is capped at {MAX_REGISTRY_EXTENSIONS} entries; a vocabulary "
                "that large is not reviewable and should be split by domain"
            )
        existing = self._by_reference.get(item.reference)
        if existing is not None and existing != item:
            raise UntrustedExtensionError(
                f"{item.reference} is already registered with a different definition; re-registering "
                "one version under two meanings would make every constraint that used it ambiguous"
            )
        self._by_reference[item.reference] = item
        current = self._latest.get(item.predicate_id)
        if current is None or _version_key(item.version) >= _version_key(current):
            self._latest[item.predicate_id] = item.version
        return self

    def extended(self, signatures: Iterable[Any]) -> "PredicateRegistry":
        """Return a new registry with extra signatures, leaving this one untouched."""

        clone = PredicateRegistry()
        clone._by_reference = dict(self._by_reference)
        clone._latest = dict(self._latest)
        for signature in signatures:
            clone.register(signature)
        return clone

    def get(self, predicate_id: str, version: str | None = None) -> PredicateSignature | None:
        identifier = require_identifier(predicate_id, "predicate_id")
        if version is None:
            latest = self._latest.get(identifier)
            return None if latest is None else self._by_reference.get(f"{identifier}@{latest}")
        return self._by_reference.get(f"{identifier}@{require_text(version, 'version', maximum=64)}")

    def require(self, call: Any) -> PredicateSignature:
        """Resolve a call's signature or refuse, naming what is missing.

        The refusal is the interesting branch: it fires for a mandatory constraint whose
        predicate nobody admitted (§5.13), which is the case a permissive lookup would turn
        into a silently unchecked requirement.
        """

        item = PredicateCall.coerce(call, "call")
        if not isinstance(item, PredicateCall):
            raise PredicateError("call must be a PredicateCall")
        signature = self.get(item.predicate_id, item.version)
        if signature is None:
            if item.mandatory:
                raise PredicateError(
                    f"{item.reference} is not an admitted predicate and the constraint carrying it is "
                    f"mandatory; M03 cannot check a rule it has no interpretation for, and skipping it "
                    f"would report the requirement as satisfied"
                )
            raise PredicateError(f"{item.reference} is not an admitted predicate")
        return signature

    @property
    def references(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_reference))

    @property
    def predicate_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._latest))

    def is_admitted(self, call: Any) -> bool:
        item = PredicateCall.coerce(call, "call")
        return isinstance(item, PredicateCall) and self.get(item.predicate_id, item.version) is not None

    def quarantined(self) -> tuple[str, ...]:
        return tuple(sorted(ref for ref, item in self._by_reference.items() if item.trust == PredicateTrust.QUARANTINED.value))


def _version_key(version: str) -> tuple[int, ...]:
    digits = re.findall(r"\d+", version)
    return tuple(int(item) for item in digits) or (0,)


def require_known_predicate(
    registry: PredicateRegistry,
    call: Any,
    *,
    polarity: str,
    owner: str,
) -> PredicateSignature:
    """Resolve a predicate, then check it against the polarity being applied to it.

    Two separate refusals live here because they fail differently: an unknown predicate is a
    vocabulary problem, while a known predicate used under a polarity its signature does not
    admit (``FORBID`` on something declared ``REQUIRE``-only) is a statement the registry has
    no reading for — and a rule nobody can read is not a rule.
    """

    signature = registry.require(call)
    if not signature.accepts_polarity(polarity):
        raise PredicateError(
            f"{owner} applies polarity {polarity} to {signature.reference}, whose signature admits "
            f"{sorted(signature.polarity_admitted)}"
        )
    if signature.trust_tier is PredicateTrust.QUARANTINED:
        raise UntrustedExtensionError(
            f"{owner} relies on quarantined predicate {signature.reference}; quarantine is a finding "
            "about the predicate, not a suggestion to double-check it"
        )
    return signature


def _polarity_token(value: Any) -> str:
    """Normalise a polarity label against the vocabulary ``constraints`` defines.

    Checked here rather than passed through, because a signature that admits a polarity the
    constraint layer does not define would accept a constraint it can never be applied to.
    """

    token = require_text(value, "polarity", maximum=32).upper().replace("-", "_")
    if token not in _ALL_POLARITIES:
        raise PredicateError(
            f"polarity must be one of {list(_ALL_POLARITIES)}, got {value!r}"
        )
    return token


def _seq(value: Any, field_name: str) -> Iterable[Any]:
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list")
    return value


#: A deliberately small core vocabulary, chosen so the six required domains can express
#: their semantics without the kernel importing any of them. Everything richer arrives as a
#: versioned extension signature (§6, §12.12), which is what keeps "domain-neutral" a claim
#: about the dependency graph rather than about how general-purpose the wording looks.
CORE_PREDICATES: tuple[PredicateSignature, ...] = (
    PredicateSignature(
        predicate_id="conforms_to",
        version="v1",
        semantic_path="style.conformance",
        argument_types=(
            PredicateArgument(name="target", type="IDENTIFIER"),
            PredicateArgument(name="degree", type="CHOICE", required=False, allowed_values=("STRICT", "ADAPTIVE", "LOOSE")),
        ),
        interpretation="the subject must conform to the named reference set, to at least the stated degree",
    ),
    PredicateSignature(
        predicate_id="matches",
        version="v1",
        semantic_path="identity.anchor",
        argument_types=(
            PredicateArgument(name="anchor", type="IDENTIFIER"),
            PredicateArgument(name="facets", type="IDENTIFIER", required=False),
        ),
        interpretation="the subject must match the anchored identity or style on the named facets only",
    ),
    PredicateSignature(
        predicate_id="present_in",
        version="v1",
        semantic_path="scope.presence",
        argument_types=(PredicateArgument(name="scope", type="IDENTIFIER"),),
        interpretation="the subject must be present within the named scope",
    ),
    PredicateSignature(
        predicate_id="absent_from",
        version="v1",
        semantic_path="scope.absence",
        argument_types=(PredicateArgument(name="scope", type="IDENTIFIER"),),
        interpretation="the subject must not appear within the named scope",
    ),
    PredicateSignature(
        predicate_id="quantity_within",
        version="v1",
        semantic_path="quantity.bound",
        argument_types=(
            PredicateArgument(name="measure", type="IDENTIFIER"),
            PredicateArgument(name="target", type="NUMBER"),
            PredicateArgument(name="unit", type="IDENTIFIER"),
        ),
        interpretation="a named measure must stay inside the tolerance envelope attached to the constraint",
    ),
    PredicateSignature(
        predicate_id="precedes",
        version="v1",
        semantic_path="temporal.order",
        argument_types=(
            PredicateArgument(name="before", type="IDENTIFIER"),
            PredicateArgument(name="in_sequence", type="IDENTIFIER", required=False),
        ),
        interpretation="one semantic subject must occur before another within the named sequence",
    ),
    PredicateSignature(
        predicate_id="speaks",
        version="v1",
        semantic_path="language.use",
        argument_types=(
            PredicateArgument(name="language", type="IDENTIFIER"),
            PredicateArgument(name="register", type="IDENTIFIER", required=False),
        ),
        interpretation="delivered language must be in the named language and register",
    ),
    PredicateSignature(
        predicate_id="refers_to",
        version="v1",
        semantic_path="reference.binding",
        argument_types=(
            PredicateArgument(name="ref", type="REF"),
            PredicateArgument(name="role", type="IDENTIFIER", required=False),
        ),
        interpretation="the subject must refer to the bound external record, in the stated role",
    ),
)
