"""F-M03-07 Semantic Admission Shield (§14, S02).

Admission is where M03 decides whether a piece of meaning may be believed at the weight its
author claims. Everything else in the kernel assumes the answer, which is why the checks live in
one module instead of being spread through the constructors: a rule that only fires when a
caller remembers to call it is not a shield, and the interesting failures here are
cross-object — a statement whose *source* is untrusted and whose *origin* says human-explicit
is fine alone and contradictory together.

The shield is a policy object that is passed in, never a module-level singleton. A global would
make "which policy admitted this?" unanswerable, and that question is the whole content of an
audit (§5.28, §5.30).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .ambiguity import AmbiguityAssessment
from .base import Labeled, Record, of
from .briefs import BriefRevision
from .constraints import Constraint, ConstraintBundle
from .errors import (
    AdmissionRefusedError,
    LimitExceededError,
    SchemaValidationError,
    StaleSemanticError,
    UntrustedExtensionError,
)
from .identity import (
    AuthorityLevel,
    RefKind,
    SemanticRef,
    SourceKind,
)
from .intent import IntentModel, IntentOrigin, IntentStatement
from .limits import (
    MAX_ADMISSION_CLAIMS,
    MAX_METADATA_KEYS,
    MAX_NESTING_DEPTH,
    MAX_PROVENANCE_REFS,
)
from .normalization import ConstraintNormalForm, normalize_bundle
from .predicates import PredicateRegistry, require_known_predicate
from .sources import RawInputRef
from .versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    content_digest,
    require_contract_version,
    require_identifier,
    require_semantic_path,
    require_supported,
    require_text,
    require_version_text,
)

__all__ = [
    "AdmissionCheck",
    "AdmissionDecision",
    "AdmissionFinding",
    "AdmissionReport",
    "SemanticAdmissionShield",
    "detect_cycle",
    "require_admitted",
    "require_bounded_nesting",
    "require_supported_versions",
]


class AdmissionDecision(Labeled):
    """Outcome for one claim.

    ``DEFERRED`` is not a soft refusal: it means the check could not run because something it
    depends on has not been decided yet, and it must not be able to flow downstream as if it
    were satisfied. Only ``ADMITTED`` releases a claim into compilation.
    """

    ADMITTED = "ADMITTED"
    DEFERRED = "DEFERRED"
    REFUSED = "REFUSED"


class AdmissionCheck(Labeled):
    """The §14 fail-closed catalogue, named so a report says which rule fired.

    Each member corresponds to a sentence in the frozen contract's security section, and a
    finding that could not name its check would be unreviewable: "refused" without the rule is
    indistinguishable from a bug.
    """

    SOURCE_AUTHORITY = "SOURCE_AUTHORITY"
    SELF_PROMOTED_RULE = "SELF_PROMOTED_RULE"
    UNKNOWN_PREDICATE = "UNKNOWN_PREDICATE"
    UNKNOWN_EXTENSION = "UNKNOWN_EXTENSION"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"
    BLOCKING_AMBIGUITY = "BLOCKING_AMBIGUITY"
    FREEDOM_AS_GAP = "FREEDOM_AS_GAP"
    QUALITY_DOWNGRADE = "QUALITY_DOWNGRADE"
    INSUFFICIENT_OVERRIDE_AUTHORITY = "INSUFFICIENT_OVERRIDE_AUTHORITY"
    NON_OVERRIDABLE = "NON_OVERRIDABLE"
    STALE_DERIVATION = "STALE_DERIVATION"
    STALE_VERSION = "STALE_VERSION"
    CANONICAL_MUTATION = "CANONICAL_MUTATION"
    RESOURCE_BOUNDS = "RESOURCE_BOUNDS"
    CYCLIC_AUTHORITY = "CYCLIC_AUTHORITY"
    INACTIVE_CONTAMINATION = "INACTIVE_CONTAMINATION"


@dataclass(frozen=True)
class AdmissionFinding(Record):
    """One check's verdict about one subject, with the evidence that produced it.

    ``evidence_refs`` is required and non-empty for a refusal. A refusal nobody can trace is a
    mystery the next reviewer re-litigates, and the trace is cheap here because the shield only
    fires on data it was handed.
    """

    finding_id: str
    check: str
    decision: str
    subject_ref: SemanticRef
    detail: str
    evidence_refs: tuple[SemanticRef, ...] = ()
    policy_ref: SemanticRef | None = None
    recoverable: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", require_identifier(self.finding_id, "finding_id"))
        object.__setattr__(self, "check", AdmissionCheck.parse(self.check, "check").value)
        decision = AdmissionDecision.parse(self.decision, "decision")
        object.__setattr__(self, "decision", decision.value)
        object.__setattr__(self, "subject_ref", SemanticRef.coerce(self.subject_ref, "subject_ref"))
        object.__setattr__(
            self, "detail", require_text(self.detail, "detail", maximum=1024)
        )
        refs = tuple(
            sorted(
                (SemanticRef.coerce(item, "evidence_refs[]") for item in (self.evidence_refs or ())),
                key=lambda item: item.text,
            )
        )
        if decision is AdmissionDecision.REFUSED and not refs:
            raise SchemaValidationError(
                f"refusal {self.finding_id} for check {self.check} carries no evidence ref; a "
                "refusal that cites nothing cannot be reviewed, only re-argued"
            )
        if len(refs) > MAX_PROVENANCE_REFS:
            raise LimitExceededError(
                f"finding {self.finding_id} cites {len(refs)} refs, above {MAX_PROVENANCE_REFS}"
            )
        object.__setattr__(self, "evidence_refs", refs)
        if self.policy_ref is not None:
            object.__setattr__(self, "policy_ref", SemanticRef.coerce(self.policy_ref, "policy_ref"))
        if not isinstance(self.recoverable, bool):
            raise SchemaValidationError("recoverable must be a boolean")

    @property
    def refused(self) -> bool:
        return self.decision == AdmissionDecision.REFUSED.value

    @property
    def deferred(self) -> bool:
        return self.decision == AdmissionDecision.DEFERRED.value

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "decision": self.decision,
            "subject": self.subject_ref.text,
            "evidence": sorted(item.text for item in self.evidence_refs),
            "recoverable": self.recoverable,
        }


AdmissionFinding.NESTED = {
    "subject_ref": of(SemanticRef),
    "evidence_refs": of(SemanticRef),
    "policy_ref": of(SemanticRef),
}


@dataclass(frozen=True)
class AdmissionReport(Record):
    """The aggregate verdict for one subject, version-pinned to what produced it.

    The pins matter as much as the findings: "admitted" is only meaningful alongside which
    registry, policy and contract versions made that true, otherwise a later reader cannot tell
    whether the world changed or the shield got laxer (§5.43).
    """

    report_id: str
    subject_ref: SemanticRef
    decision: str
    findings: tuple[AdmissionFinding, ...] = ()
    contract_version: str = ""
    schema_version: str = ""
    pins: Mapping[str, str] = field(default_factory=dict)
    checked_by: SemanticRef | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", require_identifier(self.report_id, "report_id"))
        object.__setattr__(self, "subject_ref", SemanticRef.coerce(self.subject_ref, "subject_ref"))
        decision = AdmissionDecision.parse(self.decision, "decision")
        object.__setattr__(self, "decision", decision.value)
        findings = tuple(
            sorted(
                (AdmissionFinding.coerce(item, "findings[]") for item in (self.findings or ())),
                key=lambda item: (item.check, item.subject_ref.text, item.finding_id),
            )
        )
        if len(findings) > MAX_ADMISSION_CLAIMS * 4:
            raise LimitExceededError(
                f"report {self.report_id} carries {len(findings)} findings, above the bound"
            )
        aggregate = _aggregate_decision(findings)
        if decision.value != aggregate:
            raise AdmissionRefusedError(
                f"report {self.report_id} declares {decision.value} but its findings aggregate to "
                f"{aggregate}; a report may not be more permissive than what it found (§5.6)"
            )
        object.__setattr__(self, "findings", findings)
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )
        object.__setattr__(
            self, "schema_version", require_supported("schema", self.schema_version or SCHEMA_VERSION, _SCHEMA_VERSIONS)
        )
        pins = {
            require_identifier(key, "pins key"): require_version_text(value, f"pins[{key}]")
            for key, value in sorted(dict(self.pins or {}).items())
        }
        if len(pins) > MAX_METADATA_KEYS:
            raise LimitExceededError(f"pins exceed {MAX_METADATA_KEYS} entries")
        object.__setattr__(self, "pins", pins)
        if self.checked_by is not None:
            object.__setattr__(self, "checked_by", SemanticRef.coerce(self.checked_by, "checked_by"))
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))

    @property
    def admitted(self) -> bool:
        return self.decision == AdmissionDecision.ADMITTED.value

    @property
    def refusals(self) -> tuple[AdmissionFinding, ...]:
        return tuple(item for item in self.findings if item.refused)

    @property
    def deferrals(self) -> tuple[AdmissionFinding, ...]:
        return tuple(item for item in self.findings if item.deferred)

    @property
    def checks_fired(self) -> tuple[str, ...]:
        return tuple(sorted({item.check for item in self.findings}))

    def detail_for(self, check: str) -> tuple[str, ...]:
        wanted = AdmissionCheck.parse(check, "check").value
        return tuple(item.detail for item in self.findings if item.check == wanted)

    def fingerprint_inputs(self) -> list[Any]:
        return [item.fingerprint_inputs() for item in self.findings]

    def digest_of(self) -> str:
        return content_digest(
            {
                "subject": self.subject_ref.text,
                "decision": self.decision,
                "findings": [item.fingerprint_inputs() for item in self.findings],
                "pins": dict(self.pins),
            }
        )


AdmissionReport.NESTED = {
    "subject_ref": of(SemanticRef),
    "findings": of(AdmissionFinding),
    "checked_by": of(SemanticRef),
}

_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})


def _aggregate_decision(findings: Sequence[AdmissionFinding]) -> str:
    if any(item.refused for item in findings):
        return AdmissionDecision.REFUSED.value
    if any(item.deferred for item in findings):
        return AdmissionDecision.DEFERRED.value
    return AdmissionDecision.ADMITTED.value


class SemanticAdmissionShield:
    """The gate every M03 subject passes through before it can drive compilation.

    Checks are methods returning findings rather than raising, so a caller can ask "what is
    wrong with this brief?" and get the whole list; the raising happens once, in
    :func:`require_admitted`, against the aggregate report. Splitting it that way keeps the
    fail-closed behaviour in one place instead of in fifteen call sites that might disagree
    about what "closed" means.
    """

    def __init__(
        self,
        *,
        registry: PredicateRegistry,
        policy_refs: Iterable[SemanticRef] = (),
        non_overridable_paths: Iterable[str] = (),
        required_authority: str = "TEAM_ASSERTED",
        pins: Mapping[str, str] | None = None,
        max_constraints: int = MAX_ADMISSION_CLAIMS * 8,
    ) -> None:
        if not isinstance(registry, PredicateRegistry):
            raise SchemaValidationError("the shield needs a PredicateRegistry; predicates cannot be checked against nothing")
        self.registry = registry
        self.policy_refs = tuple(
            sorted(
                (SemanticRef.coerce(item, "policy_refs[]") for item in policy_refs),
                key=lambda item: item.text,
            )
        )
        paths = tuple(sorted({require_semantic_path(item, "non_overridable_paths[]") for item in non_overridable_paths}))
        if len(paths) > MAX_ADMISSION_CLAIMS:
            raise LimitExceededError(
                f"non_overridable paths number {len(paths)}, above {MAX_ADMISSION_CLAIMS}"
            )
        self.non_overridable_paths = paths
        self.required_authority = AuthorityLevel.parse(required_authority, "required_authority").value
        self.pins = dict(pins or {})
        self.max_constraints = max_constraints

    # ------------------------------------------------------------------ helpers

    def _finding(
        self,
        check: AdmissionCheck,
        decision: AdmissionDecision,
        subject: SemanticRef,
        detail: str,
        evidence: Iterable[SemanticRef] = (),
        *,
        recoverable: bool = False,
    ) -> AdmissionFinding:
        refs = tuple(SemanticRef.coerce(item, "evidence") for item in evidence)
        return AdmissionFinding(
            finding_id=f"adm-{content_digest({'check': check.value, 'subject': subject.text, 'detail': detail, 'evidence': sorted(item.text for item in refs)})[:20]}",
            check=check.value,
            decision=decision.value,
            subject_ref=subject,
            detail=detail,
            evidence_refs=refs,
            policy_ref=self.policy_refs[0] if self.policy_refs else None,
            recoverable=recoverable,
        )

    @property
    def policy_authority(self) -> AuthorityLevel:
        return AuthorityLevel.parse(self.required_authority)

    # ------------------------------------------------------------------ checks

    def check_source_authority(self, sources: Iterable[RawInputRef]) -> list[AdmissionFinding]:
        """Refuse a source whose claimed authority outranks what its kind can carry.

        Constructors already cap this, so a finding here means a payload arrived whose ceiling
        does not match its kind — the shape a forged admission record takes (§14).
        """

        findings: list[AdmissionFinding] = []
        for source in sources:
            ref = SemanticRef(kind=RefKind.SOURCE.value, ref_id=source.source_id).with_digest(
                source.content_digest
            )
            kind = SourceKind.parse(source.kind)
            from .identity import ceiling_for

            ceiling = ceiling_for(kind)
            level = AuthorityLevel.parse(source.authority)
            if level.rank > ceiling.rank:
                findings.append(
                    self._finding(
                        AdmissionCheck.SOURCE_AUTHORITY,
                        AdmissionDecision.REFUSED,
                        ref,
                        f"source claims {level.value} but {kind.value} can carry at most "
                        f"{ceiling.value}; the ceiling mismatch means this admission was written, "
                        "not earned (§5.6)",
                        (ref,),
                    )
                )
        return findings

    def check_statements(self, statements: Iterable[IntentStatement]) -> list[AdmissionFinding]:
        """Catch the two ways a statement lies about itself: origin and authority.

        ``EXPLICIT`` claims a human said it, so it needs a level and a basis that could only come
        from a revision or a policy; a model output marked explicit is the single most valuable
        forgery available to an untrusted channel (§5.4, §5.6).
        """

        findings: list[AdmissionFinding] = []
        for statement in statements:
            ref = statement.statement_ref
            origin = IntentOrigin.parse(statement.origin)
            level = statement.authority.level
            if origin is IntentOrigin.EXPLICIT and level.rank < AuthorityLevel.TEAM_ASSERTED.rank:
                findings.append(
                    self._finding(
                        AdmissionCheck.SOURCE_AUTHORITY,
                        AdmissionDecision.REFUSED,
                        ref,
                        f"statement is declared EXPLICIT at {level.value} authority; explicit means a "
                        "human said it, which needs an admitted revision or a policy behind it (§5.6)",
                        (ref, SemanticRef(kind=RefKind.POLICY.value, ref_id=self.required_authority)),
                    )
                )
            if statement.mandatory and statement.provenance is None:
                findings.append(
                    self._finding(
                        AdmissionCheck.MISSING_PROVENANCE,
                        AdmissionDecision.REFUSED,
                        ref,
                        f"mandatory statement {statement.statement_id} cites no provenance; §5.28 "
                        "requires an explanation path for everything that can block completion",
                        (ref,),
                    )
                )
            if not level.self_asserting_is_enough and statement.confidence is not None:
                if statement.confidence > 0.9 and level.rank < self.policy_authority.rank:
                    findings.append(
                        self._finding(
                            AdmissionCheck.SELF_PROMOTED_RULE,
                            AdmissionDecision.REFUSED,
                            ref,
                            f"untrusted statement {statement.statement_id} reports confidence "
                            f"{statement.confidence} while holding {level.value} authority; confidence "
                            "is not authority and this pairing is how injected text promotes itself (§5.6, §5.29)",
                            (ref,),
                        )
                    )
        return findings

    def check_constraints(self, constraints: Iterable[Constraint]) -> list[AdmissionFinding]:
        """Predicate admission plus the negative-integrity and authority checks.

        Kept together because the two halves inform each other: an unknown predicate is only a
        problem because of what the constraint *does* with it, and a HARD rule from a retrieved
        source is a problem whatever its predicate says.
        """

        findings: list[AdmissionFinding] = []
        items = list(constraints)
        if len(items) > self.max_constraints:
            findings.append(
                self._finding(
                    AdmissionCheck.RESOURCE_BOUNDS,
                    AdmissionDecision.REFUSED,
                    SemanticRef(kind=RefKind.BUNDLE.value, ref_id="over-sized"),
                    f"{len(items)} constraints exceed the admitted bound of {self.max_constraints}; "
                    "a collection this large is either abuse or a mistake, and neither belongs in an "
                    "admitted bundle",
                )
            )
            return findings
        for constraint in items:
            ref = constraint.constraint_ref
            if constraint.subject_ref is not None:
                ref = constraint.subject_ref
            try:
                require_known_predicate(
                    self.registry,
                    constraint.predicate,
                    polarity=constraint.polarity,
                    owner=constraint.constraint_id,
                )
            except Exception as error:  # noqa: BLE001 - the shield reports any predicate refusal as a finding
                findings.append(
                    self._finding(
                        AdmissionCheck.UNKNOWN_PREDICATE
                        if not str(error).lower().startswith("polarity")
                        else AdmissionCheck.UNKNOWN_EXTENSION,
                        AdmissionDecision.REFUSED,
                        ref,
                        str(error),
                        (ref,),
                    )
                )
            if (
                constraint.strength_enum.requires_receipt_to_relax
                and constraint.authority.level.rank < AuthorityLevel.PROJECT_RECORD.rank
            ):
                findings.append(
                    self._finding(
                        AdmissionCheck.SELF_PROMOTED_RULE,
                        AdmissionDecision.REFUSED,
                        ref,
                        f"constraint {constraint.constraint_id} is "
                        f"{constraint.strength.value} on the word of a "
                        f"{constraint.authority.level.value} source; imperative text arriving through "
                        "an untrusted channel may not bind the work (§5.6, §14)",
                        (ref,),
                    )
                )
            for anchor in constraint.protected_survival:
                if self._covers_non_overridable(anchor.semantic_path):
                    continue
                if anchor.authority_floor.rank > constraint.authority.level.rank:
                    findings.append(
                        self._finding(
                            AdmissionCheck.INSUFFICIENT_OVERRIDE_AUTHORITY,
                            AdmissionDecision.REFUSED,
                            ref,
                            f"protected anchor {anchor.anchor_id} needs "
                            f"{anchor.authority_floor.value} authority to be carried by a rule held at "
                            f"{constraint.authority.level.value}",
                            (ref, anchor.anchor_ref),
                        )
                    )
            if constraint.is_negative and not (
                constraint.anti_references or constraint.predicate.arguments or constraint.protected_anchors
            ):
                findings.append(
                    self._finding(
                        AdmissionCheck.CANONICAL_MUTATION,
                        AdmissionDecision.DEFERRED,
                        ref,
                        f"negative constraint {constraint.constraint_id} states no target; a "
                        "prohibition with nothing attached cannot be shown to survive translation, so "
                        "it is deferred rather than trusted (§5.15)",
                        (ref,),
                    )
                )
        return findings

    def check_bundle_coverage(
        self, bundle: ConstraintBundle, required_paths: Iterable[str], *, form: ConstraintNormalForm | None = None
    ) -> list[AdmissionFinding]:
        """Refuse a bundle that leaves a required path unaddressed, in either direction.

        Two findings look similar and are not: a path with no rule at all is a gap, while a path
        whose only rules are inactive is a gap *for this run*. Merging them would let a bundle
        pass because somebody once wrote something about the path.
        """

        findings: list[AdmissionFinding] = []
        ref = bundle.bundle_ref
        normalized = form or normalize_bundle(bundle)
        by_path: dict[str, list[Any]] = {}
        for rule in normalized.rules:
            by_path.setdefault(rule.semantic_path, []).append(rule)
        for path in sorted({require_semantic_path(item, "required_paths[]") for item in required_paths}):
            covered = [rule for rules in by_path.values() for rule in rules if _path_related(path, rule.semantic_path)]
            if not covered:
                findings.append(
                    self._finding(
                        AdmissionCheck.RESOURCE_BOUNDS,
                        AdmissionDecision.REFUSED,
                        ref,
                        f"required path {path} has no constraint in bundle {bundle.bundle_id}; §5.22 "
                        "refuses a complete contract over an uncovered obligation",
                        (ref,),
                    )
                )
            elif all(rule.conditions and not rule.is_active(None) for rule in covered):
                findings.append(
                    self._finding(
                        AdmissionCheck.INACTIVE_CONTAMINATION,
                        AdmissionDecision.DEFERRED,
                        ref,
                        f"required path {path} is covered only by rules that are inactive "
                        f"({sorted(rule.rule_id for rule in covered)}); a rule that does not bind is "
                        "not coverage, and must not be fingerprinted as though it were",
                        (ref,),
                    )
                )
        return findings

    def check_ambiguity(self, assessment: AmbiguityAssessment | None) -> list[AdmissionFinding]:
        """Blocking ambiguity and creative freedom, from opposite directions.

        Freedom zones are reported as deferrals, never refusals: §5.7 insists an open creative
        choice is not missing data, so the shield may stop completion on it but must not call it
        an error.
        """

        if assessment is None:
            return []
        subject = SemanticRef(kind=RefKind.REVISION.value, ref_id=assessment.revision_id)
        findings: list[AdmissionFinding] = []
        for record in assessment.ambiguities:
            if not record.consequence_class.blocks_completion:
                continue
            ref = SemanticRef(kind=RefKind.AMBIGUITY.value, ref_id=record.ambiguity_id)
            findings.append(
                self._finding(
                    AdmissionCheck.BLOCKING_AMBIGUITY,
                    AdmissionDecision.REFUSED,
                    ref,
                    f"{record.consequence} ambiguity {record.ambiguity_id} on "
                    f"{list(record.semantic_paths)} blocks admission until it is resolved (§5.8)",
                    (ref, subject),
                    recoverable=True,
                )
            )
        for ambiguity_id in assessment.freedom_as_gap:
            ref = SemanticRef(kind=RefKind.AMBIGUITY.value, ref_id=ambiguity_id)
            findings.append(
                self._finding(
                    AdmissionCheck.FREEDOM_AS_GAP,
                    AdmissionDecision.REFUSED,
                    ref,
                    f"ambiguity {ambiguity_id} is recorded as creative freedom but falls outside "
                    "every granted zone, so it is being treated as a gap; open creative latitude is "
                    "a decision to leave it open, not an omission (§5.7)",
                    (ref, subject),
                )
            )
        return findings

    def check_versions(self, supplied: Mapping[str, str]) -> list[AdmissionFinding]:
        """Compare what a caller pins against what the shield was configured with.

        Mismatch is a refusal rather than a warning because compiled state carries its pins
        forward: admitting against one registry and later compiling against another would leave
        an artifact whose meaning changed without its fingerprint moving (§5.43, §5.44).
        """

        findings: list[AdmissionFinding] = []
        for name, version in sorted(dict(supplied or {}).items()):
            key = require_identifier(name, "pins key")
            wanted = require_version_text(version, f"pins[{key}]")
            expected = self.pins.get(key)
            subject = SemanticRef(kind=RefKind.POLICY.value, ref_id=key, version=wanted)
            if expected is None:
                findings.append(
                    self._finding(
                        AdmissionCheck.UNKNOWN_EXTENSION,
                        AdmissionDecision.REFUSED,
                        subject,
                        f"{key} is pinned but this shield admits no such component; an unknown "
                        "mandatory version reference fails closed (§5.13)",
                        (subject,),
                    )
                )
            elif expected != wanted:
                findings.append(
                    self._finding(
                        AdmissionCheck.STALE_VERSION,
                        AdmissionDecision.REFUSED,
                        subject,
                        f"{key} is pinned at {wanted} while the admitted version is {expected}; "
                        "compiling against a stale component silently changes what a fingerprint "
                        "means (§5.43)",
                        (subject,),
                        recoverable=True,
                    )
                )
        return findings

    def check_non_overridable(self, paths: Iterable[str]) -> list[AdmissionFinding]:
        """Name the protected paths an ordinary override is not allowed to touch (§5.31)."""

        findings: list[AdmissionFinding] = []
        for path in paths:
            wanted = require_semantic_path(path, "path")
            if self._covers_non_overridable(wanted):
                continue
            findings.append(
                self._finding(
                    AdmissionCheck.NON_OVERRIDABLE,
                    AdmissionDecision.REFUSED,
                    SemanticRef(kind=RefKind.POLICY.value, ref_id=wanted),
                    f"{wanted} is outside the non-overridable set and may not be claimed as "
                    "protected by an override receipt; protection is declared by policy, not by "
                    "whoever wants it (§5.31, §5.35)",
                )
            )
        return findings

    def check_authority_graph(self, edges: Mapping[str, Iterable[str]]) -> list[AdmissionFinding]:
        """Refuse a cyclic authority structure, naming the cycle rather than the suspicion.

        A cycle in an authority graph is not merely untidy: with ``A`` outranking ``B`` and ``B``
        outranking ``A``, every conflict resolves in whichever direction the resolver walked
        first, which is the last property an audit needs to be arbitrary about (§5.29).
        """

        try:
            cycle = detect_cycle(edges)
        except LimitExceededError as error:
            return [
                self._finding(
                    AdmissionCheck.RESOURCE_BOUNDS,
                    AdmissionDecision.REFUSED,
                    SemanticRef(kind=RefKind.POLICY.value, ref_id="authority-graph"),
                    str(error),
                )
            ]
        if not cycle:
            return []
        subject = SemanticRef(kind=RefKind.POLICY.value, ref_id=cycle[0])
        return [
            self._finding(
                AdmissionCheck.CYCLIC_AUTHORITY,
                AdmissionDecision.REFUSED,
                subject,
                "authority graph contains a cycle: " + " -> ".join(cycle),
                tuple(SemanticRef(kind=RefKind.POLICY.value, ref_id=node) for node in cycle),
            )
        ]

    def check_depth(self, payload: Any, *, subject: SemanticRef) -> list[AdmissionFinding]:
        findings: list[AdmissionFinding] = []
        try:
            require_bounded_nesting(payload)
        except (LimitExceededError, SchemaValidationError) as error:
            findings.append(
                self._finding(
                    AdmissionCheck.RESOURCE_BOUNDS,
                    AdmissionDecision.REFUSED,
                    subject,
                    str(error),
                    (subject,),
                )
            )
        return findings

    def _covers_non_overridable(self, path: str) -> bool:
        return any(path.startswith(prefix) or prefix.startswith(path) for prefix in self.non_overridable_paths)

    # ------------------------------------------------------------------ aggregate

    def assess(
        self,
        *,
        report_id: str,
        subject: SemanticRef,
        revision: BriefRevision | None = None,
        model: IntentModel | None = None,
        bundle: ConstraintBundle | None = None,
        assessment: AmbiguityAssessment | None = None,
        required_paths: Iterable[str] = (),
        pins: Mapping[str, str] | None = None,
        payload: Any = None,
    ) -> AdmissionReport:
        """Run every applicable check and return one aggregate report.

        ``revision``/``model``/``bundle`` are optional independently because admission happens at
        different stages for different subjects; what is not optional is that whatever is present
        gets checked completely. An assessment that skipped the constraints because the caller
        happened to pass a bundle would be a formality.
        """

        findings: list[AdmissionFinding] = []
        if revision is not None:
            findings += self.check_source_authority(revision.sources)
            findings += self.check_statements(revision.statements)
        if model is not None:
            findings += self.check_statements(model.statements)
        if bundle is not None:
            findings += self.check_constraints(bundle.constraints)
            if list(required_paths):
                findings += self.check_bundle_coverage(bundle, required_paths)
        findings += self.check_ambiguity(assessment)
        findings += self.check_versions(pins or {})
        if payload is not None:
            findings += self.check_depth(payload, subject=subject)
        decision = _aggregate_decision(findings)
        merged_pins = dict(self.pins)
        merged_pins.update(dict(pins or {}))
        return AdmissionReport(
            report_id=report_id,
            subject_ref=subject,
            decision=decision,
            findings=tuple(findings),
            contract_version=CONTRACT_VERSION,
            schema_version=SCHEMA_VERSION,
            pins=merged_pins,
            checked_by=self.policy_refs[0] if self.policy_refs else None,
        )


def require_admitted(report: AdmissionReport, action: str) -> None:
    """Turn a report into the gate it was always meant to be."""

    if not isinstance(report, AdmissionReport):
        raise SchemaValidationError(f"{action} needs an AdmissionReport")
    if report.admitted:
        return
    reasons = "; ".join(item.detail for item in report.refusals) or "nothing was refused, but the report is not ADMITTED"
    raise AdmissionRefusedError(
        f"cannot {action}: admission for {report.subject_ref.text} returned "
        f"{report.decision} ({reasons})"
    )


def detect_cycle(edges: Mapping[str, Iterable[str]]) -> tuple[str, ...]:
    """Return the first cycle found in a directed graph, in traversal order, or ``()``.

    Iterative on purpose: a recursive walk over a hostile graph turns the check for unbounded
    structure into the unbounded structure. Cycles are reported in the order discovered so the
    message is deterministic and can be asserted in a test.
    """

    if not isinstance(edges, Mapping):
        raise SchemaValidationError("detect_cycle needs a mapping of node -> neighbours")
    if len(edges) > MAX_ADMISSION_CLAIMS * 16:
        raise LimitExceededError(
            f"authority graph has {len(edges)} nodes, above the bound of {MAX_ADMISSION_CLAIMS * 16}"
        )
    graph = {
        require_identifier(node, "graph node"): tuple(
            sorted({require_identifier(item, "edge target") for item in (edges[node] or ())})
        )
        for node in sorted(edges)
    }
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {node: WHITE for node in graph}
    stack: list[str] = []

    def neighbours(node: str) -> tuple[str, ...]:
        targets = graph.get(node, ())
        unknown = sorted(set(targets) - set(graph))
        if unknown:
            raise SchemaValidationError(
                f"authority node {node} points at undeclared nodes {unknown}; a dangling edge makes "
                "cycle detection silently incomplete"
            )
        return targets

    for start in sorted(graph):
        if colour[start] != WHITE:
            continue
        colour[start] = GREY
        stack.append(start)
        while stack:
            node = stack[-1]
            advanced = False
            for target in neighbours(node):
                if colour[target] == WHITE:
                    colour[target] = GREY
                    stack.append(target)
                    advanced = True
                    break
                if colour[target] == GREY:
                    index = stack.index(target)
                    return tuple(stack[index:] + [target])
            if not advanced:
                colour[node] = BLACK
                stack.pop()
    return ()


def require_bounded_nesting(payload: Any, *, limit: int = MAX_NESTING_DEPTH, _depth: int = 0) -> int:
    """Measure a payload's nesting and refuse anything past the bound.

    Bounds are declared before traversal rather than after, so the check cannot be bypassed by a
    payload that is merely deep at some point the traversal would reach late.
    """

    if _depth > limit:
        raise LimitExceededError(
            f"semantic payload nests deeper than {limit}; refusing rather than risking a stack "
            "exhaustion on attacker-shaped input"
        )
    if isinstance(payload, Mapping):
        if len(payload) > MAX_METADATA_KEYS * 8:
            raise LimitExceededError(
                f"a payload mapping holds {len(payload)} keys, above the bound of {MAX_METADATA_KEYS * 8}"
            )
        return max(
            [require_bounded_nesting(value, limit=limit, _depth=_depth + 1) for value in payload.values()]
            or [_depth]
        )
    if isinstance(payload, (list, tuple)):
        if len(payload) > MAX_PROVENANCE_REFS * 64:
            raise LimitExceededError(
                f"a payload sequence holds {len(payload)} entries, above the bound of {MAX_PROVENANCE_REFS * 64}"
            )
        return max(
            [require_bounded_nesting(value, limit=limit, _depth=_depth + 1) for value in payload]
            or [_depth]
        )
    return _depth


def require_supported_versions(supplied: Mapping[str, str], admitted: Mapping[str, str]) -> None:
    """Public helper for callers that want the version check without the report object."""

    for name, version in sorted(dict(supplied).items()):
        expected = admitted.get(require_identifier(name, "version name"))
        if expected is None:
            raise UntrustedExtensionError(
                f"{name} is not an admitted component; §5.13 fails closed on unknown mandatory versions"
            )
        if expected != require_version_text(version, f"{name} version"):
            raise StaleSemanticError(
                f"{name} is {version} while {expected} is admitted; stale components may not compile"
            )


def _path_related(left: str, right: str) -> bool:
    return left == right or left.startswith(right + ".") or right.startswith(left + ".")
