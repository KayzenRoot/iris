"""Deterministic Constraint Normal Form (S02, §8).

Two briefs accumulate rules the way meeting notes accumulate: somebody restates a rule in
different words, somebody else narrows it, and a third adds the same requirement for another
destination. Compiling that pile directly would make the output depend on insertion order, and
an order-dependent rule set cannot be fingerprinted, diffed or overridden by ref — every one
of those would shift when a rule was merely re-entered.

Normal Form answers the question compilation actually needs: *for each semantic path and each
polarity, what does the work have to satisfy, and how strongly?* It is a derived view, never a
replacement: the bundle keeps the original constraints, their provenance and their authority,
and every normalized rule points back at the ids it came from. Nothing is invented here and
nothing is dropped — a rule that cannot be represented in the form is reported as an
unrepresentable residue rather than quietly optimised away, because the interesting failure of
a normaliser is the case it swallowed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .constraints import (
    Condition,
    Constraint,
    ConstraintBundle,
    ConstraintPolarity,
    ConstraintScope,
    ConstraintStrength,
    require_no_authority_in_scope,
)
from .errors import LimitExceededError, SchemaValidationError
from .identity import RefKind, SemanticRef
from .limits import (
    MAX_CONSTRAINTS_PER_BUNDLE,
    MAX_PATHS_PER_SLICE,
    MAX_PROVENANCE_REFS,
)
from .predicates import PredicateCall
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    content_digest,
    require_contract_version,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "ConstraintNormalForm",
    "NormalizedRule",
    "ReductionKind",
    "NORMAL_FORM_VERSION",
    "normalize_bundle",
    "require_same_normal_form",
]

#: Versioned because what counts as "the same rule" is a semantic decision, and a later
#: amendment that changes merge behaviour must not silently re-fingerprint old bundles.
NORMAL_FORM_VERSION = "m03-cnform-v1"


class ReductionKind(Labeled):
    """How a normalized rule relates to the constraints it came from.

    ``MERGED`` and ``NARROWED`` are reported separately from ``KEPT`` because they are the two
    reductions a reviewer needs to see: a merge means two authors asked for one thing, and a
    narrowing means one rule now only binds part of what another rule did. Both change what a
    downstream contract can claim, and neither is visible once the rules have been folded.
    """

    KEPT = "KEPT"
    MERGED = "MERGED"
    NARROWED = "NARROWED"


@dataclass(frozen=True)
class NormalizedRule(Record):
    """One requirement, as the compiler sees it: path, predicate, polarity, strength, scope.

    ``source_constraint_ids`` is mandatory and non-empty. A normalized rule with no citations
    would be a rule this module invented, and the whole point of the form is that it is a view
    over admitted constraints rather than a second source of truth.
    """

    rule_id: str
    semantic_path: str
    predicate: PredicateCall
    polarity: str
    strength: str
    scope: ConstraintScope
    conditions: tuple[Condition, ...] = ()
    source_constraint_ids: tuple[str, ...] = ()
    reduction: str = "KEPT"
    strongest_authority: str | None = None
    tolerances: tuple[Mapping[str, Any], ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", require_identifier(self.rule_id, "rule_id"))
        object.__setattr__(
            self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path")
        )
        object.__setattr__(self, "predicate", PredicateCall.coerce(self.predicate, "predicate"))
        polarity = ConstraintPolarity.parse(self.polarity, "polarity")
        object.__setattr__(self, "polarity", polarity.value)
        strength = ConstraintStrength.parse(self.strength, "strength")
        object.__setattr__(self, "strength", strength.value)
        scope = ConstraintScope.coerce(self.scope, "scope")
        require_no_authority_in_scope(scope, self.rule_id)
        object.__setattr__(self, "scope", scope)
        conditions = tuple(
            sorted(
                (Condition.coerce(item, "conditions[]") for item in (self.conditions or ())),
                key=lambda item: (item.context_key, item.operator, item.values),
            )
        )
        object.__setattr__(self, "conditions", conditions)
        sources = tuple(sorted({require_identifier(item, "source_constraint_ids[]") for item in (self.source_constraint_ids or ())}))
        if not sources:
            raise SchemaValidationError(
                f"normalized rule {self.rule_id} cites no constraint; a rule nobody wrote is this "
                "module inventing requirements"
            )
        if len(sources) > MAX_PROVENANCE_REFS:
            raise LimitExceededError(
                f"normalized rule {self.rule_id} cites {len(sources)} constraints, above {MAX_PROVENANCE_REFS}"
            )
        object.__setattr__(self, "source_constraint_ids", sources)
        reduction = ReductionKind.parse(self.reduction, "reduction")
        if reduction is not ReductionKind.KEPT and len(sources) < 1:
            raise SchemaValidationError(f"rule {self.rule_id} claims {reduction.value} with no sources")
        object.__setattr__(self, "reduction", reduction.value)
        if self.strongest_authority is not None:
            object.__setattr__(self, "strongest_authority", require_text(self.strongest_authority, "strongest_authority", maximum=32).upper())
        tolerances = tuple(
            sorted(
                (
                    bounded_metadata(item, "tolerances[]")
                    for item in (self.tolerances or ())
                ),
                key=lambda item: str(item.get("measure", "")),
            )
        )
        object.__setattr__(self, "tolerances", tolerances)
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=512))

    @property
    def polarity_enum(self) -> ConstraintPolarity:
        return ConstraintPolarity.parse(self.polarity)

    @property
    def strength_enum(self) -> ConstraintStrength:
        return ConstraintStrength.parse(self.strength)

    @property
    def negative(self) -> bool:
        return self.polarity_enum.negative

    @property
    def sort_key(self) -> tuple[Any, ...]:
        """Deterministic ordering: path, then least-permissive first, then identity.

        Strength descends and polarity uses its conflict ordering so that a hard prohibition
        sorts ahead of a soft preference on the same path. The final tie-break is the rule id,
        which is what keeps two runs over the same bundle producing byte-identical output
        without letting insertion order matter.
        """

        return (
            self.semantic_path,
            -self.strength_enum.rank,
            -self.polarity_enum.strictness,
            self.polarity,
            self.predicate.reference,
            self.rule_id,
        )

    def is_active(self, context: Mapping[str, Any] | None) -> bool:
        if not self.conditions:
            return True
        if context is None:
            return False
        return all(condition.holds(context) for condition in self.conditions)

    def applies_to(self, context: Mapping[str, Any]) -> bool:
        return self.is_active(context) and self.scope.matches(context)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "semantic_path": self.semantic_path,
            "predicate": self.predicate.fingerprint_inputs(),
            "polarity": self.polarity,
            "strength": self.strength,
            "scope": self.scope.to_payload(),
            "conditions": [item.to_payload() for item in self.conditions],
            "tolerances": [dict(item) for item in self.tolerances],
            "reduction": self.reduction,
        }


NormalizedRule.NESTED = {
    "predicate": of(PredicateCall),
    "scope": of(ConstraintScope),
    "conditions": of(Condition),
}


@dataclass(frozen=True)
class ConstraintNormalForm(Record):
    """The normalized view of one bundle version, with its own fingerprint.

    ``residues`` keeps the constraints that could not be folded into the form — rules whose
    scopes cross in a way the merge refuses to guess about. Reporting them is the difference
    between a normal form and a lossy compression: a reviewer reading an empty rule list must be
    able to tell "nothing was required" from "something was required and this module could not
    represent it" (§5.12, §5.27).
    """

    form_id: str
    bundle_ref: SemanticRef
    normal_form_version: str
    rules: tuple[NormalizedRule, ...] = ()
    residues: tuple[Mapping[str, str], ...] = ()
    contract_version: str = ""
    rule_count_source: int = 0
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "form_id", require_identifier(self.form_id, "form_id"))
        ref = SemanticRef.coerce(self.bundle_ref, "bundle_ref")
        if ref.kind != RefKind.BUNDLE.value:
            raise SchemaValidationError(
                f"bundle_ref must reference {RefKind.BUNDLE.value}, got {ref.kind}"
            )
        if ref.version is None:
            raise SchemaValidationError(
                "bundle_ref must carry the bundle version; an unversioned normal form cannot say "
                "which rules it folded (§5.43)"
            )
        object.__setattr__(self, "bundle_ref", ref)
        object.__setattr__(
            self,
            "normal_form_version",
            require_version_text(self.normal_form_version, "normal_form_version"),
        )
        rules = tuple(
            sorted(
                (NormalizedRule.coerce(item, "rules[]") for item in (self.rules or ())),
                key=lambda item: item.sort_key,
            )
        )
        if len(rules) > MAX_CONSTRAINTS_PER_BUNDLE:
            raise LimitExceededError(
                f"normal form holds {len(rules)} rules, above {MAX_CONSTRAINTS_PER_BUNDLE}"
            )
        ids = [item.rule_id for item in rules]
        if len(set(ids)) != len(ids):
            raise SchemaValidationError("normal form repeats a rule id")
        object.__setattr__(self, "rules", rules)
        residues = tuple(
            sorted(
                (
                    {
                        k: v
                        for k, v in bounded_metadata(item, "residues[]").items()
                    }
                    for item in (self.residues or ())
                ),
                key=lambda item: str(item.get("constraint_id", "")),
            )
        )
        for item in residues:
            if not item.get("constraint_id") or not item.get("reason"):
                raise SchemaValidationError(
                    "every residue must name its constraint_id and the reason it could not be "
                    "normalized; an unexplained omission is how a rule disappears"
                )
        object.__setattr__(self, "residues", residues)
        object.__setattr__(
            self,
            "contract_version",
            require_contract_version(self.contract_version or CONTRACT_VERSION),
        )
        if not isinstance(self.rule_count_source, int) or isinstance(self.rule_count_source, bool):
            raise SchemaValidationError("rule_count_source must be an integer")
        if self.rule_count_source < len({c for r in rules for c in r.source_constraint_ids}):
            raise SchemaValidationError(
                "rule_count_source is below the number of distinct cited constraints; the form would "
                "claim to have folded more rules than it was given"
            )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(sorted({item.semantic_path for item in self.rules}))

    @property
    def empty(self) -> bool:
        return not self.rules

    @property
    def fully_reduced(self) -> bool:
        return not self.residues

    def rules_for(self, semantic_path: str) -> tuple[NormalizedRule, ...]:
        path = require_semantic_path(semantic_path, "semantic_path")
        return tuple(item for item in self.rules if item.semantic_path == path)

    def active_rules(self, context: Mapping[str, Any] | None = None) -> tuple[NormalizedRule, ...]:
        return tuple(item for item in self.rules if item.is_active(context))

    def blocking_paths(self, context: Mapping[str, Any] | None = None) -> tuple[str, ...]:
        """Paths whose active rules can stop completion."""

        paths = {
            item.semantic_path
            for item in self.active_rules(context)
            if item.strength_enum.blocks_completion
        }
        return tuple(sorted(paths))

    def negative_rules(self) -> tuple[NormalizedRule, ...]:
        return tuple(item for item in self.rules if item.negative)

    def fingerprint_inputs(self, *, context: Mapping[str, Any] | None = None) -> list[Any]:
        return [item.fingerprint_inputs() for item in self.active_rules(context)]

    def digest_of(self) -> str:
        return content_digest(
            {
                "normal_form_version": self.normal_form_version,
                "bundle": self.bundle_ref.text,
                "rules": [item.fingerprint_inputs() for item in self.rules],
                "residues": [dict(item) for item in self.residues],
            }
        )

    def equivalent_to(self, other: "ConstraintNormalForm") -> bool:
        """Semantic equality, ignoring which bundle ids produced it.

        Deliberately excludes ids and citations: two briefs that require the same thing in
        different words must compare equal here, or the equivalence profile could never let a
        downstream artifact be reused (§5.45).
        """

        if not isinstance(other, ConstraintNormalForm):
            raise SchemaValidationError("equivalent_to expects a ConstraintNormalForm")
        if self.normal_form_version != other.normal_form_version:
            return False
        left = sorted(item.fingerprint_inputs() and _canonical(item) for item in self.rules)
        right = sorted(item.fingerprint_inputs() and _canonical(item) for item in other.rules)
        return left == right


ConstraintNormalForm.NESTED = {"bundle_ref": of(SemanticRef), "rules": of(NormalizedRule)}


def _canonical(rule: NormalizedRule) -> str:
    from .versions import canonical_json

    return canonical_json(rule.fingerprint_inputs())


def _identity_key(rule: NormalizedRule) -> tuple[Any, ...]:
    """What makes two constraints "the same requirement".

    Path, predicate reference, normalised arguments, polarity and strength: the fields that
    determine what compliance means. Authority, provenance and wording are excluded because two
    people asking for the same thing do not create two requirements — but the exclusion is only
    safe because the merged rule keeps both citations and takes the *stronger* authority, so
    nothing that was permitted by the pair is lost by the fold.
    """

    return (
        rule.semantic_path,
        rule.predicate.reference,
        content_digest({"arguments": rule.predicate.to_payload()["arguments"]}),
        rule.polarity,
        rule.strength,
    )


def normalize_bundle(bundle: ConstraintBundle, *, form_id: str | None = None) -> ConstraintNormalForm:
    """Fold one bundle version into its normal form.

    The fold is conservative: rules merge only when every correctness-relevant field agrees and
    their scopes are identical, and anything else is emitted separately or as a residue. A
    normaliser that merged two rules with different scopes would have to decide what the union
    or intersection means, and that decision belongs to whoever wrote the rules.
    """

    if not isinstance(bundle, ConstraintBundle):
        raise SchemaValidationError("normalize_bundle expects a ConstraintBundle")
    grouped: dict[tuple[Any, ...], list[Constraint]] = {}
    for item in bundle.constraints:
        grouped.setdefault(_identity_key(_as_rule(item)), []).append(item)
    rules: list[NormalizedRule] = []
    for key, group in sorted(grouped.items(), key=lambda pair: (str(pair[0]), pair[1][0].constraint_id)):
        ordered = sorted(group, key=lambda item: item.constraint_id)
        strongest = max((item.authority.level.rank for item in ordered))
        base = _as_rule(ordered[0])
        scopes = {content_digest(item.scope.to_payload()) for item in ordered}
        conditions = {content_digest([c.to_payload() for c in item.conditions]) for item in ordered}
        bounds = {content_digest([t.fingerprint_inputs() for t in item.tolerances]) for item in ordered}
        if len(scopes) > 1 or len(conditions) > 1 or len(bounds) > 1:
            rules.extend(_narrowed(ordered, strongest))
            continue
        rules.append(
            NormalizedRule(
                rule_id=form_id or base.rule_id,
                semantic_path=base.semantic_path,
                predicate=base.predicate,
                polarity=base.polarity,
                strength=base.strength,
                scope=base.scope,
                conditions=base.conditions,
                source_constraint_ids=tuple(item.constraint_id for item in ordered),
                reduction=ReductionKind.MERGED.value if len(ordered) > 1 else ReductionKind.KEPT.value,
                strongest_authority=_authority_label(strongest, ordered),
                tolerances=tuple(item.fingerprint_inputs() for item in ordered[0].tolerances),
            )
        )
    residues: list[Mapping[str, str]] = []
    folded = _reconcile_overlaps(rules, residues)
    folded.sort(key=lambda item: item.sort_key)
    if len(folded) > MAX_PATHS_PER_SLICE * 4:
        raise LimitExceededError(
            f"normal form produced {len(folded)} rules, above the reduction bound"
        )
    return ConstraintNormalForm(
        form_id=form_id or f"cnf-{bundle.bundle_id}-{bundle.version}",
        bundle_ref=bundle.bundle_ref,
        normal_form_version=NORMAL_FORM_VERSION,
        rules=tuple(folded),
        residues=tuple(residues),
        rule_count_source=len(bundle.constraints),
    )


def _authority_label(rank: int, group: Iterable[Constraint]) -> str:
    for item in group:
        if item.authority.level.rank == rank:
            return item.authority.level.value
    raise SchemaValidationError(
        "normal form lost the authority level it was about to record; report the group instead of "
        "guessing one, because a merged rule that invents its own authority is a privilege "
        "escalation written by a reducer"
    )


def _as_rule(constraint: Constraint) -> NormalizedRule:
    """View a constraint as a rule so identity and merging share one shape."""

    return NormalizedRule(
        rule_id=constraint.constraint_id,
        semantic_path=constraint.semantic_path,
        predicate=constraint.predicate,
        polarity=constraint.polarity,
        strength=constraint.strength,
        scope=constraint.scope,
        conditions=constraint.conditions,
        source_constraint_ids=(constraint.constraint_id,),
        reduction=ReductionKind.KEPT.value,
        strongest_authority=constraint.authority.authority,
        tolerances=tuple(item.fingerprint_inputs() for item in constraint.tolerances),
    )


def _narrowed(group: list[Constraint], strongest: int) -> list[NormalizedRule]:
    """Keep differing scopes/conditions as separate rules, marked as narrowed.

    Narrowing is reported rather than resolved: two rules that ask for the same thing over
    different subject sets genuinely both apply, and folding them would either widen the weaker
    one (inventing a requirement) or intersect them (dropping one).
    """

    return [
        NormalizedRule(
            rule_id=item.constraint_id,
            semantic_path=item.semantic_path,
            predicate=item.predicate,
            polarity=item.polarity,
            strength=item.strength,
            scope=item.scope,
            conditions=item.conditions,
            source_constraint_ids=(item.constraint_id,),
            reduction=ReductionKind.NARROWED.value,
            strongest_authority=item.authority.authority,
            tolerances=tuple(t.fingerprint_inputs() for t in item.tolerances),
        )
        for item in sorted(group, key=lambda item: item.constraint_id)
    ]


def _reconcile_overlaps(
    rules: list[NormalizedRule], residues: list[Mapping[str, str]]
) -> list[NormalizedRule]:
    """Drop a strictly-subsumed rule, and report what this module refused to fold.

    Subsumption here is exact: same identity key, and one scope wholly covered by the other at
    the same strength. Anything looser — partial overlap, or the same requirement at two
    strengths — is left as two rules, because choosing between them is an authority question
    that S05 answers with a receipt, not a normaliser answering with a heuristic.
    """

    kept: list[NormalizedRule] = []
    ordered = sorted(rules, key=lambda item: item.sort_key)
    for index, rule in enumerate(ordered):
        subsumed = False
        for other in ordered[:index] + ordered[index + 1 :]:
            if other is rule:
                continue
            if _identity_key(rule) != _identity_key(other):
                continue
            if _subsumes(other, rule):
                residues.append(
                    {
                        "constraint_id": rule.source_constraint_ids[0],
                        "reason": f"subsumed by {other.rule_id} whose scope covers it at equal strength",
                    }
                )
                subsumed = True
                break
        if not subsumed:
            kept.append(rule)
    return kept


def _subsumes(broader: NormalizedRule, narrower: NormalizedRule) -> bool:
    if broader.strength != narrower.strength:
        return False
    if set(broader.scope.modalities) and set(narrower.scope.modalities):
        if not set(narrower.scope.modalities) <= set(broader.scope.modalities):
            return False
    return all(
        any(_covers(subject, other) for other in broader.scope.subject_paths)
        for subject in narrower.scope.subject_paths
    ) and not (set(broader.scope.excluded_paths) - set(narrower.scope.excluded_paths))


def _covers(prefix: str, path: str) -> bool:
    return path == prefix or path.startswith(prefix + ".")


def require_same_normal_form(left: ConstraintNormalForm, right: ConstraintNormalForm, action: str) -> None:
    """Refuse to compare forms produced by different reduction rules.

    A version mismatch here means the two sides were not measured with the same yardstick, and
    reporting "no delta" from that would be a false negative about requirements — the one delta
    result nobody notices, because it looks like agreement.
    """

    if not isinstance(left, ConstraintNormalForm) or not isinstance(right, ConstraintNormalForm):
        raise SchemaValidationError(f"{action} needs ConstraintNormalForm values")
    if left.normal_form_version != right.normal_form_version:
        raise SchemaValidationError(
            f"{action} compares normal forms {left.normal_form_version} and "
            f"{right.normal_form_version}; the reduction rules changed, so a difference or a match "
            "between them says nothing about the requirements"
        )
    if left.contract_version != right.contract_version:
        raise SchemaValidationError(
            f"{action} compares normal forms across contract versions {left.contract_version} and "
            f"{right.contract_version}"
        )
