"""F-M03-03 Minimum sufficient semantic slices (§15, §18).

The claim this module has to make good on is that a consumer can work on one part of a brief
without being handed the whole brief. That is easy to get wrong in two directions: slice too
wide and the token cost returns with nothing gained; slice too narrow and a downstream decision
is made without the constraint that governs it, which is worse than being expensive because it
looks correct.

So a slice is computed as a closure, not as a filter. The requested paths seed it, and
everything those statements and rules depend on — cited sources, the statements a derived
statement was built from, the constraints bound to the same path, the ambiguity that would
change the answer, the freedom zone that keeps a hole from being read as a gap — is pulled in
with a recorded reason. The reason matters as much as the item: a reviewer looking at a slice
that contains something unexpected needs to be told why, and "because the closure said so" is
not reviewable.

Minimality is asserted, not hoped for. :func:`require_slice_minimality` recomputes the closure
and refuses if the delivered slice either dropped a dependency or carried an unrelated item, so
a future edit that makes slicing sloppy fails a test rather than silently shipping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .ambiguity import AmbiguityAssessment, AmbiguityRecord, FreedomZone
from .base import Labeled, Record, of
from .constraints import Constraint, ConstraintBundle
from .errors import SchemaValidationError, ScopeError
from .fingerprints import SemanticEquivalenceProfile, DEFAULT_EQUIVALENCE_PROFILE
from .identity import RefKind, SemanticRef
from .intent import IntentModel, IntentStatement
from .limits import (
    MAX_AMBIGUITIES,
    MAX_CONSTRAINTS_PER_BUNDLE,
    MAX_METADATA_KEYS,
    MAX_PATHS_PER_SLICE,
    MAX_PROVENANCE_REFS,
    MAX_SLICE_STATEMENTS,
)
from .versions import (
    CONTRACT_VERSION,
    content_digest,
    require_contract_version,
    require_identifier,
    require_semantic_path,
    require_text,
)

__all__ = [
    "MinimumSufficientSemanticSlice",
    "SlicePurpose",
    "SemanticSliceRequest",
    "closure_for",
    "require_slice_minimality",
    "slice_intent",
    "structural_footprint",
]


class SlicePurpose(Labeled):
    """What the consumer intends to do with the slice.

    Purpose changes the closure rather than the label: a clarification slice must carry the
    ambiguity records and their candidate readings, a compilation slice must carry the admitted
    constraints and their protected anchors, and an audit slice must carry provenance. One
    purpose-blind slice would either over-fetch for every consumer or under-fetch for the one
    consumer that needed the extra half (§15, §16).
    """

    CLARIFY = "CLARIFY"
    COMPILE_QUALITY = "COMPILE_QUALITY"
    COMPILE_EXECUTION = "COMPILE_EXECUTION"
    RESOLVE_CONFLICT = "RESOLVE_CONFLICT"
    VALIDATE = "VALIDATE"
    LOCALIZE = "LOCALIZE"
    AUDIT = "AUDIT"

    @property
    def needs_constraints(self) -> bool:
        return self in {
            SlicePurpose.COMPILE_QUALITY,
            SlicePurpose.COMPILE_EXECUTION,
            SlicePurpose.RESOLVE_CONFLICT,
            SlicePurpose.VALIDATE,
        }

    @property
    def needs_ambiguity(self) -> bool:
        return self in {SlicePurpose.CLARIFY, SlicePurpose.RESOLVE_CONFLICT, SlicePurpose.AUDIT}

    @property
    def needs_provenance(self) -> bool:
        return self in {SlicePurpose.AUDIT, SlicePurpose.CLARIFY}


@dataclass(frozen=True)
class SemanticSliceRequest(Record):
    """One consumer's bounded ask against one brief revision.

    ``paths`` is required and non-empty: an empty request would mean "everything", which is the
    behaviour slicing exists to make unnecessary, and a caller who genuinely wants the whole
    model can ask for the root path explicitly.
    """

    request_id: str
    consumer_ref: SemanticRef
    purpose: str
    paths: tuple[str, ...]
    revision_ref: SemanticRef
    context: Mapping[str, str] = field(default_factory=dict)
    max_statements: int = MAX_SLICE_STATEMENTS
    include_optional: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", require_identifier(self.request_id, "request_id"))
        object.__setattr__(self, "consumer_ref", SemanticRef.coerce(self.consumer_ref, "consumer_ref"))
        object.__setattr__(self, "purpose", SlicePurpose.parse(self.purpose, "purpose").value)
        paths = tuple(sorted({require_semantic_path(item, "paths[]") for item in (self.paths or ())}))
        if not paths:
            raise ScopeError(
                f"slice request {self.request_id} names no path; an empty slice request means "
                "'the whole brief', which is the thing this fabric exists to avoid (§15)"
            )
        if len(paths) > MAX_PATHS_PER_SLICE:
            raise SchemaValidationError(
                f"slice request {self.request_id} spans {len(paths)} paths, above {MAX_PATHS_PER_SLICE}"
            )
        object.__setattr__(self, "paths", paths)
        object.__setattr__(self, "revision_ref", SemanticRef.coerce(self.revision_ref, "revision_ref"))
        context = {
            require_identifier(key, "context key"): require_text(value, f"context[{key}]", maximum=128)
            for key, value in sorted(dict(self.context or {}).items())
        }
        if len(context) > MAX_METADATA_KEYS:
            raise SchemaValidationError(f"request context exceeds {MAX_METADATA_KEYS} keys")
        object.__setattr__(self, "context", context)
        if not isinstance(self.max_statements, int) or isinstance(self.max_statements, bool) or self.max_statements < 1:
            raise SchemaValidationError("max_statements must be a positive integer")
        if self.max_statements > MAX_SLICE_STATEMENTS:
            raise SchemaValidationError(
                f"max_statements {self.max_statements} is above the admitted bound {MAX_SLICE_STATEMENTS}"
            )
        if not isinstance(self.include_optional, bool):
            raise SchemaValidationError("include_optional must be a boolean")
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=512))

    @property
    def purpose_enum(self) -> SlicePurpose:
        return SlicePurpose.parse(self.purpose)

    @property
    def context_digest(self) -> str | None:
        return None if not self.context else content_digest(dict(self.context))


SemanticSliceRequest.NESTED = {"consumer_ref": of(SemanticRef), "revision_ref": of(SemanticRef)}


@dataclass(frozen=True)
class MinimumSufficientSemanticSlice(Record):
    """A closed, self-explaining subset of one brief revision.

    ``inclusion_reasons`` is not decoration. A slice is consumed by something that cannot see
    the rest of the brief, and when it finds an item it did not ask for it has exactly two
    options: ignore it, or trust that the closure had a reason. Recording the reason turns that
    into an audit trail, and makes an accidental over-fetch visible in a diff (§16).
    """

    slice_id: str
    request_id: str
    purpose: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    paths: tuple[str, ...] = ()
    statements: tuple[IntentStatement, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    ambiguities: tuple[AmbiguityRecord, ...] = ()
    freedom_zones: tuple[FreedomZone, ...] = ()
    provenance_capsules: tuple[SemanticRef, ...] = ()
    inclusion_reasons: Mapping[str, str] = field(default_factory=dict)
    excluded_statement_ids: tuple[str, ...] = ()
    excluded_constraint_ids: tuple[str, ...] = ()
    profile_ref: SemanticRef | None = None
    contract_version: str = ""
    slice_digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "slice_id", require_identifier(self.slice_id, "slice_id"))
        object.__setattr__(self, "request_id", require_identifier(self.request_id, "request_id"))
        object.__setattr__(self, "purpose", SlicePurpose.parse(self.purpose, "purpose").value)
        object.__setattr__(self, "brief_ref", SemanticRef.coerce(self.brief_ref, "brief_ref"))
        object.__setattr__(self, "revision_ref", SemanticRef.coerce(self.revision_ref, "revision_ref"))
        paths = tuple(sorted({require_semantic_path(item, "paths[]") for item in (self.paths or ())}))
        if not paths:
            raise ScopeError("a slice with no paths is not a slice of anything")
        if len(paths) > MAX_PATHS_PER_SLICE:
            raise SchemaValidationError(f"slice {self.slice_id} spans {len(paths)} paths")
        object.__setattr__(self, "paths", paths)
        statements = _ordered(
            (IntentStatement.coerce(item, "statements[]") for item in (self.statements or ())),
            lambda item: item.statement_id,
            MAX_SLICE_STATEMENTS,
            "statements",
        )
        object.__setattr__(self, "statements", statements)
        constraints = _ordered(
            (Constraint.coerce(item, "constraints[]") for item in (self.constraints or ())),
            lambda item: item.constraint_id,
            MAX_CONSTRAINTS_PER_BUNDLE,
            "constraints",
        )
        object.__setattr__(self, "constraints", constraints)
        ambiguities = _ordered(
            (AmbiguityRecord.coerce(item, "ambiguities[]") for item in (self.ambiguities or ())),
            lambda item: item.ambiguity_id,
            MAX_AMBIGUITIES,
            "ambiguities",
        )
        object.__setattr__(self, "ambiguities", ambiguities)
        zones = _ordered(
            (FreedomZone.coerce(item, "freedom_zones[]") for item in (self.freedom_zones or ())),
            lambda item: item.zone_id,
            MAX_AMBIGUITIES,
            "freedom_zones",
        )
        object.__setattr__(self, "freedom_zones", zones)
        object.__setattr__(
            self,
            "provenance_capsules",
            _ordered(
                (SemanticRef.coerce(item, "provenance_capsules[]") for item in (self.provenance_capsules or ())),
                lambda item: item.text,
                MAX_PROVENANCE_REFS,
                "provenance_capsules",
            ),
        )
        for name, group in (("statement", statements), ("constraint", constraints)):
            for item in group:
                identity = getattr(item, f"{name}_id")
                if not _related_path(paths, item.semantic_path):
                    raise ScopeError(
                        f"slice {self.slice_id} carries {name} {identity} on {item.semantic_path}, "
                        f"outside its declared paths {list(paths)}; widen the request or drop the item, "
                        "because an undisclosed extra is how a slice stops being minimal"
                    )
        reasons = {
            require_identifier(key, "inclusion_reasons key"): require_text(value, "inclusion_reasons[]", maximum=256)
            for key, value in sorted(dict(self.inclusion_reasons or {}).items())
        }
        object.__setattr__(self, "inclusion_reasons", reasons)
        if len(reasons) > MAX_PATHS_PER_SLICE * 4:
            raise SchemaValidationError(
                f"slice {self.slice_id} carries {len(reasons)} inclusion reasons, above the bound"
            )
        object.__setattr__(
            self, "excluded_statement_ids", _tokens(self.excluded_statement_ids, "excluded_statement_ids")
        )
        object.__setattr__(
            self, "excluded_constraint_ids", _tokens(self.excluded_constraint_ids, "excluded_constraint_ids")
        )
        overlap = sorted(
            {item.statement_id for item in statements} & set(self.excluded_statement_ids)
        ) + sorted({item.constraint_id for item in constraints} & set(self.excluded_constraint_ids))
        if overlap:
            raise SchemaValidationError(
                f"slice {self.slice_id} lists {overlap} as both included and excluded"
            )
        if self.profile_ref is not None:
            object.__setattr__(self, "profile_ref", SemanticRef.coerce(self.profile_ref, "profile_ref"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )
        computed = content_digest(self.fingerprint_inputs())
        if self.slice_digest and self.slice_digest != computed:
            raise SchemaValidationError(
                f"slice {self.slice_id} declares a digest that does not match its content; the slice "
                "would be believed by consumers who could not tell it was stale"
            )
        object.__setattr__(self, "slice_digest", computed)

    @property
    def statement_ids(self) -> tuple[str, ...]:
        return tuple(item.statement_id for item in self.statements)

    @property
    def constraint_ids(self) -> tuple[str, ...]:
        return tuple(item.constraint_id for item in self.constraints)

    @property
    def blocking(self) -> bool:
        return any(record.consequence_class.blocks_completion for record in self.ambiguities)

    @property
    def size(self) -> dict[str, int]:
        return {
            "paths": len(self.paths),
            "statements": len(self.statements),
            "constraints": len(self.constraints),
            "ambiguities": len(self.ambiguities),
            "freedom_zones": len(self.freedom_zones),
        }

    def reason_for(self, identifier: str) -> str | None:
        return self.inclusion_reasons.get(require_identifier(identifier, "identifier"))

    def statement(self, statement_id: str) -> IntentStatement:
        wanted = require_identifier(statement_id, "statement_id")
        for item in self.statements:
            if item.statement_id == wanted:
                return item
        raise SchemaValidationError(
            f"slice {self.slice_id} does not carry statement {wanted}; resolve it against the full "
            "model rather than assuming the omission was deliberate"
        )

    def constraint(self, constraint_id: str) -> Constraint:
        wanted = require_identifier(constraint_id, "constraint_id")
        for item in self.constraints:
            if item.constraint_id == wanted:
                return item
        raise SchemaValidationError(f"slice {self.slice_id} does not carry constraint {wanted}")

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "purpose": self.purpose,
            "paths": list(self.paths),
            "statements": sorted(item.digest() for item in self.statements),
            "constraints": sorted(item.digest() for item in self.constraints),
            "ambiguities": sorted(item.digest() for item in self.ambiguities),
            "freedom_zones": sorted(item.digest() for item in self.freedom_zones),
            "revision": self.revision_ref.text,
        }

    def equivalent_to(self, other: "MinimumSufficientSemanticSlice") -> bool:
        """Same content under the same purpose, ignoring which request produced it.

        Two consumers asking for the same slice of the same revision should get one payload and
        one cache key; keeping ``request_id`` out of the comparison is what makes that true.
        """

        if not isinstance(other, MinimumSufficientSemanticSlice):
            raise SchemaValidationError("equivalence needs another slice")
        return self.slice_digest == other.slice_digest


MinimumSufficientSemanticSlice.NESTED = {
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "statements": of(IntentStatement),
    "constraints": of(Constraint),
    "ambiguities": of(AmbiguityRecord),
    "freedom_zones": of(FreedomZone),
    "provenance_capsules": of(SemanticRef),
    "profile_ref": of(SemanticRef),
}


def slice_intent(
    model: IntentModel,
    bundle: ConstraintBundle | None,
    request: SemanticSliceRequest,
    *,
    assessment: AmbiguityAssessment | None = None,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    slice_id: str | None = None,
) -> MinimumSufficientSemanticSlice:
    """Build the closure for one request.

    The order of expansion is deliberate: statements first, then whatever those statements cite,
    then the rules bound to those paths, then the ambiguity and freedom records that would change
    how the result is read. Expanding rules before statements would let a constraint pull in a
    path that nobody asked for, and that is the difference between a slice and a search.
    """

    if not isinstance(model, IntentModel):
        raise SchemaValidationError("slice_intent expects an IntentModel")
    if not isinstance(request, SemanticSliceRequest):
        raise SchemaValidationError("slice_intent expects a SemanticSliceRequest")
    if bundle is not None and not isinstance(bundle, ConstraintBundle):
        raise SchemaValidationError("slice_intent bundle must be a ConstraintBundle or None")
    by_id = {item.statement_id: item for item in model.statements}
    reasons: dict[str, str] = {}
    selected: dict[str, IntentStatement] = {}

    def take(statement: IntentStatement, reason: str) -> None:
        if statement.statement_id in selected:
            return
        if len(selected) >= request.max_statements:
            raise SchemaValidationError(
                f"slice for {request.request_id} needs more than the admitted {request.max_statements} "
                "statements; narrow the requested paths instead of raising the bound, because the bound "
                "is what keeps a slice a slice (§15)"
            )
        selected[statement.statement_id] = statement
        reasons.setdefault(statement.statement_id, reason)

    for statement in model.statements:
        if _related_path(request.paths, statement.semantic_path):
            take(statement, "requested path")
    # Dependencies of what was asked for, transitively, so no derived statement arrives alone.
    frontier = list(selected.values())
    while frontier:
        current = frontier.pop()
        for source_id in current.source_statement_ids:
            parent = by_id.get(source_id)
            if parent is None:
                raise SchemaValidationError(
                    f"statement {current.statement_id} cites {source_id}, which is not in the model; a "
                    "dangling citation would be silently dropped from the slice and the consumer could "
                    "not tell it was missing (§5.28)"
                )
            if parent.statement_id not in selected:
                take(parent, f"citation of {current.statement_id}")
                frontier.append(parent)
    paths = tuple(sorted({item.semantic_path for item in selected.values()} | set(request.paths)))

    constraints: list[Constraint] = []
    if bundle is not None and request.purpose_enum.needs_constraints:
        for constraint in bundle.constraints:
            if not _related_path(paths, constraint.semantic_path):
                continue
            if not constraint.is_active(request.context or None):
                continue
            constraints.append(constraint)
            reasons.setdefault(constraint.constraint_id, "bound to a sliced path")
            for anchor in constraint.protected_anchors:
                if anchor.statement_refs:
                    reasons.setdefault(constraint.constraint_id, "carries a protected anchor")
    constraints.sort(key=lambda item: item.constraint_id)

    ambiguities: list[AmbiguityRecord] = []
    zones: list[FreedomZone] = []
    if assessment is not None and request.purpose_enum.needs_ambiguity:
        identifiers = set(selected) | {item.constraint_id for item in constraints}
        for record in assessment.ambiguities:
            if identifiers & (set(record.affected_statement_ids) | set(record.affected_constraint_ids)) or any(
                record.touches(path) for path in paths
            ):
                ambiguities.append(record)
                reasons.setdefault(record.ambiguity_id, "affects sliced semantics")
        for zone in assessment.freedom_zones:
            if any(zone.covers(path) for path in paths):
                zones.append(zone)
                reasons.setdefault(zone.zone_id, "latitude over a sliced path")
    capsules = sorted(
        {
            item.provenance.capsule_ref
            for item in selected.values()
            if item.provenance is not None and request.purpose_enum.needs_provenance
        },
        key=lambda ref: ref.text,
    )
    excluded_statements = tuple(
        sorted(item.statement_id for item in model.statements if item.statement_id not in selected)
    )
    excluded_constraints = tuple(
        sorted(
            item.constraint_id
            for item in (bundle.constraints if bundle is not None else ())
            if item.constraint_id not in {each.constraint_id for each in constraints}
        )
    )
    return MinimumSufficientSemanticSlice(
        slice_id=slice_id or f"sliced-{request.request_id}",
        request_id=request.request_id,
        purpose=request.purpose,
        brief_ref=SemanticRef(kind=RefKind.BRIEF.value, ref_id=model.brief_id),
        revision_ref=SemanticRef(
            kind=RefKind.REVISION.value, ref_id=model.revision_id, version=f"v{model.revision_number}"
        ),
        paths=paths,
        statements=tuple(selected.values()),
        constraints=tuple(constraints),
        ambiguities=tuple(sorted(ambiguities, key=lambda item: item.ambiguity_id)),
        freedom_zones=tuple(sorted(zones, key=lambda item: item.zone_id)),
        provenance_capsules=capsules,
        inclusion_reasons=reasons,
        excluded_statement_ids=excluded_statements,
        excluded_constraint_ids=excluded_constraints,
        profile_ref=profile.ref,
        contract_version=CONTRACT_VERSION,
    )


def closure_for(
    model: IntentModel, paths: Iterable[str], *, statements_only: bool = False
) -> tuple[str, ...]:
    """Statement ids reachable from ``paths``, including transitive citations.

    Exposed separately because conflict resolution and staleness both need the closure without
    wanting a slice payload, and recomputing it by building and discarding a slice would make
    the two disagree about what "reachable" means.
    """

    wanted = tuple(sorted({require_semantic_path(item, "paths[]") for item in paths}))
    if not wanted:
        raise ScopeError("closure needs at least one path")
    by_id = {item.statement_id: item for item in model.statements}
    found: set[str] = set()
    frontier = [item for item in model.statements if _related_path(wanted, item.semantic_path)]
    while frontier:
        current = frontier.pop()
        if current.statement_id in found:
            continue
        found.add(current.statement_id)
        if statements_only:
            continue
        for source_id in current.source_statement_ids:
            parent = by_id.get(source_id)
            if parent is not None and parent.statement_id not in found:
                frontier.append(parent)
    return tuple(sorted(found))


def require_slice_minimality(
    delivered: MinimumSufficientSemanticSlice,
    model: IntentModel,
    bundle: ConstraintBundle | None,
    request: SemanticSliceRequest,
) -> None:
    """Recompute the closure and refuse a slice that over- or under-delivered.

    Both directions fail: a missing dependency means a downstream decision was made blind, and a
    superfluous item means the token claim is false. Reporting them through one exception keeps
    callers from handling only the half they expected.
    """

    expected = slice_intent(model, bundle, request)
    missing = sorted(set(expected.statement_ids) - set(delivered.statement_ids))
    extra = sorted(set(delivered.statement_ids) - set(expected.statement_ids))
    if missing or extra:
        raise SchemaValidationError(
            f"slice {delivered.slice_id} is not minimal: missing {missing}, unrelated {extra}; a "
            "slice that differs from its closure cannot be used to argue that a consumer saw "
            "enough context (§15)"
        )
    if bundle is not None and request.purpose_enum.needs_constraints:
        wanted = set(expected.constraint_ids)
        delivered_ids = set(delivered.constraint_ids)
        if wanted != delivered_ids:
            raise SchemaValidationError(
                f"slice {delivered.slice_id} constraint set diverges from its closure: "
                f"missing {sorted(wanted - delivered_ids)}, unrelated {sorted(delivered_ids - wanted)}"
            )


def structural_footprint(payload: Any) -> int:
    """Count of leaf values in a payload — the deterministic size measure.

    Deliberately structural rather than bytes: a byte count moves with key spelling and field
    ordering, so a test that compared byte lengths would "prove" savings that were really
    reformatting. Counting leaves answers the question the contract asks, which is how much
    context a consumer was handed (§15, §18).
    """

    if isinstance(payload, Mapping):
        return sum(structural_footprint(value) for value in payload.values()) or 1
    if isinstance(payload, (list, tuple)):
        return sum(structural_footprint(value) for value in payload)
    return 1


def _ordered(items: Iterable[Any], key: Any, limit: int, name: str) -> tuple[Any, ...]:
    values = sorted(items, key=key)
    if len(values) > limit:
        raise SchemaValidationError(f"slice carries {len(values)} {name}, above the bound of {limit}")
    identifiers = [key(item) for item in values]
    if len(set(identifiers)) != len(identifiers):
        raise SchemaValidationError(
            f"slice repeats a {name} identity; two entries under one id make an override or an "
            "explanation target ambiguous"
        )
    return tuple(values)


def _tokens(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{name} must be a list of identifiers")
    return tuple(sorted({require_identifier(item, f"{name}[]") for item in value}))


def _related_path(prefixes: tuple[str, ...], path: str) -> bool:
    if not path:
        return False
    return any(
        path == prefix or path.startswith(prefix + ".") or prefix.startswith(path + ".") or prefix == path
        for prefix in prefixes
    )
