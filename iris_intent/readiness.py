"""F-M03-15 S05 release readiness: the §28 evidence gate a production passes before release.

§28 lists seven things that make a production semantically unready, and this module's job is to
report them and nothing more. The line is drawn by M03's own authority: M02, M01, M53, M54 and M59
hold promotion and release authority, so a report here that *granted* release would be a compiler
promoting its own output — the failure mode §14 and §24 exist to prevent. Hence the constants on the
record: this is evidence for those gates, never a substitute for them.

Two design choices carry most of the weight.

The first is that nothing here is decided twice. Whether a conflict still blocks work, whether an
override has lapsed, whether a derived dependency's freshness held, whether a compiled artifact may
be carried over — each of those is already computed once, from the objects themselves, in the module
that owns it. Re-deriving them here would give the kernel two answers to the same question and a
place for them to disagree, which is how a gate gets bypassed by finding the softer one.

The second is that a family which was not *assessed* is not a family that passed. A report that
listed no blockers because nobody handed it the conflicts would be worse than no report at all,
because it would read like a clean bill of health. So the record carries the families it actually
looked at, and ``ready`` refuses to be true while any of §28's seven is missing from that list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .ambiguity import OpenQuestion, QuestionStatus
from .authority import AuthorityPolicyGraph, AuthorityPolicyGraphRef
from .base import Labeled, Record, of
from .briefs import BriefRevision
from .conflicts import (
    ConflictClass,
    ConflictConsequence,
    ConflictResolutionState,
    SemanticConflict,
)
from .errors import (
    AdmissionRefusedError,
    LimitExceededError,
    RefError,
    SchemaValidationError,
)
from .fingerprints import (
    DEFAULT_EQUIVALENCE_PROFILE,
    SemanticEquivalenceProfile,
    fingerprint_revision,
)
from .freshness import BriefFreshnessVector, DerivedIntentDependency, FreshnessState
from .identity import RefKind, SemanticRef, require_bound_ref
from .limits import (
    MAX_PATHS_PER_SLICE,
    MAX_RATIONALE_CHARS,
    MAX_READINESS_FINDINGS,
)
from .overrides import OverrideLedger, bound_paths, bound_refs
from .reuse import ReuseAssessment
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    content_digest,
    require_digest,
    require_identifier,
    require_text,
)

__all__ = [
    "READINESS_COMPILER_VERSION",
    "ReadinessFamily",
    "ReadinessFinding",
    "SemanticReleaseReadinessReport",
    "assess_release_readiness",
    "require_semantically_ready",
]

READINESS_COMPILER_VERSION = "m03-readiness-1.0"


class ReadinessFamily(Labeled):
    """§28's seven readiness blockers, one member per bullet in the spec's list.

    The enumeration is closed rather than open because §28 is a *list*: a family somebody added
    later would be a new gate requirement, and the mapping from the seven bullets to the seven
    members is the thing a reviewer checks. Each member is named for the condition it reports, not
    for the object that carries it, because one conflict record can raise two families.
    """

    BLOCKING_CONFLICT = "BLOCKING_CONFLICT"
    RIGHTS_SECURITY_CONFLICT = "RIGHTS_SECURITY_CONFLICT"
    EXPIRED_OVERRIDE = "EXPIRED_OVERRIDE"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"
    STALE_MANDATORY_SEMANTICS = "STALE_MANDATORY_SEMANTICS"
    RELEASE_BLOCKING_DEBT = "RELEASE_BLOCKING_DEBT"
    COMPILED_ARTIFACT_STALE = "COMPILED_ARTIFACT_STALE"

    @property
    def subject_kinds(self) -> frozenset[str]:
        """The kinds of record this family may cite as its subject.

        Checked rather than cosmetic: a finding is the report's only claim that something was
        looked at, and a blocker filed against the wrong sort of object is a ref a reviewer cannot
        follow back to the thing that needs clearing.
        """

        if self is ReadinessFamily.BLOCKING_CONFLICT:
            return frozenset({RefKind.CONFLICT.value})
        if self is ReadinessFamily.RIGHTS_SECURITY_CONFLICT:
            return frozenset({RefKind.CONFLICT.value})
        if self is ReadinessFamily.EXPIRED_OVERRIDE:
            return frozenset({RefKind.RECEIPT.value})
        if self is ReadinessFamily.HUMAN_DECISION_REQUIRED:
            return frozenset({RefKind.OPEN_QUESTION.value, RefKind.CONFLICT.value})
        if self is ReadinessFamily.STALE_MANDATORY_SEMANTICS:
            return frozenset({RefKind.FRESHNESS.value})
        if self is ReadinessFamily.RELEASE_BLOCKING_DEBT:
            return frozenset({RefKind.DEBT.value})
        return frozenset({RefKind.PASSPORT.value})

    @property
    def cleared_by(self) -> str:
        """Who holds the authority to clear this family (§28's division of labour).

        Recorded so that a reader of an unready report learns where to take it, not merely that it
        is unready. M03 never appears in this list: it reports, and the decision belongs elsewhere.
        """

        return {
            ReadinessFamily.BLOCKING_CONFLICT: "a governed authority decision or an admitted revision (§13)",
            ReadinessFamily.RIGHTS_SECURITY_CONFLICT: "the human owner or governed rights policy (§13, §14)",
            ReadinessFamily.EXPIRED_OVERRIDE: "a re-authorised override or the restored rule (§11)",
            ReadinessFamily.HUMAN_DECISION_REQUIRED: "the human owner (§5.6, §13)",
            ReadinessFamily.STALE_MANDATORY_SEMANTICS: "a recompile against the current dependencies (§15)",
            ReadinessFamily.RELEASE_BLOCKING_DEBT: "closure of the debt by the authority that opened it (§12)",
            ReadinessFamily.COMPILED_ARTIFACT_STALE: "a recompile, or a testified equivalence (§15, §27)",
        }[self]


#: §28's bullets, in the order the spec lists them. Report order follows this.
READINESS_FAMILIES = tuple(ReadinessFamily)

_FAMILY_ORDER = {item.value: index for index, item in enumerate(READINESS_FAMILIES)}


@dataclass(frozen=True)
class ReadinessFinding(Record):
    """One §28 blocker, pinned to the record that raises it.

    ``subject_ref`` is bound and its kind is checked against the family, so a finding cannot be
    attached to an object of convenience, and ``detail`` is capped: a readiness report is read at
    the moment someone is deciding whether to release, and a blocker that needs three screens to
    explain has stopped being an alarm.
    """

    finding_id: str
    family: str
    subject_ref: SemanticRef
    detail: str
    semantic_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", require_identifier(self.finding_id, "finding_id"))
        family = ReadinessFamily.parse(self.family, "family")
        subject = require_bound_ref(self.subject_ref, "subject_ref")
        if subject.kind not in family.subject_kinds:
            raise RefError(
                f"finding {self.finding_id} reports {family.value} against a {subject.kind}; that "
                "family belongs to a different record, and a blocker a reviewer cannot follow to its "
                "subject is not evidence (§28)"
            )
        object.__setattr__(self, "family", family.value)
        object.__setattr__(self, "subject_ref", subject)
        paths = bound_paths(self.semantic_paths, "semantic_paths")
        if len(paths) > MAX_PATHS_PER_SLICE:
            raise LimitExceededError(
                f"finding {self.finding_id} names {len(paths)} paths, above {MAX_PATHS_PER_SLICE}"
            )
        object.__setattr__(self, "semantic_paths", paths)
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=MAX_RATIONALE_CHARS))

    @property
    def family_enum(self) -> ReadinessFamily:
        return ReadinessFamily.parse(self.family)

    @property
    def cleared_by(self) -> str:
        return self.family_enum.cleared_by

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "family": self.family,
            "subject": self.subject_ref.text,
            "semantic_paths": sorted(self.semantic_paths),
            "detail": self.detail,
        }


ReadinessFinding.NESTED = {"subject_ref": of(SemanticRef)}


@dataclass(frozen=True)
class SemanticReleaseReadinessReport(Record):
    """The §28 report: which readiness families were assessed, and what each one found.

    The report is evidence about one revision at one set of versions. It pins the source semantic
    fingerprint and the equivalence profile so a later reader can tell whether the report still
    describes what is on the table, and it records ``assessed_families`` so that "nothing was
    found" can never be confused with "nothing was looked at".
    """

    report_id: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    source_fingerprint_digest: str
    profile_ref: SemanticRef
    assessed_families: tuple[str, ...] = ()
    findings: tuple[ReadinessFinding, ...] = ()
    evidence_refs: tuple[SemanticRef, ...] = ()
    graph_ref: AuthorityPolicyGraphRef | None = None
    compiler_version: str = READINESS_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §28: readiness is evidence for the downstream gates, not a replacement for them.
    grants_release = False
    replaces_m01_quality_decision = False
    replaces_m02_promotion = False
    #: Reporting a conflict is not resolving it (§13, D-M03-S05-001).
    decides_conflicts = False
    #: A report records an assessment; it cannot admit itself.
    admits_itself = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", require_identifier(self.report_id, "report_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self, "revision_ref", require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION)
        )
        object.__setattr__(
            self,
            "source_fingerprint_digest",
            require_digest(self.source_fingerprint_digest, "source_fingerprint_digest"),
        )
        object.__setattr__(self, "profile_ref", require_bound_ref(self.profile_ref, "profile_ref"))
        assessed = tuple(
            sorted(
                {ReadinessFamily.parse(item, "assessed_families[]").value for item in (self.assessed_families or ())},
                key=lambda value: _FAMILY_ORDER[value],
            )
        )
        if not assessed:
            raise SchemaValidationError(
                f"readiness report {self.report_id} assessed no family at all; a report that looked "
                "at nothing is noise filed as governance"
            )
        object.__setattr__(self, "assessed_families", assessed)
        findings = tuple(
            sorted(
                (ReadinessFinding.coerce(item, "findings[]") for item in (self.findings or ())),
                key=lambda item: (_FAMILY_ORDER[item.family], item.finding_id),
            )
        )
        if len(findings) > MAX_READINESS_FINDINGS:
            raise LimitExceededError(
                f"readiness report {self.report_id} carries {len(findings)} findings, above "
                f"{MAX_READINESS_FINDINGS}; §28 is a gate, not a licence to enumerate forever"
            )
        unassessed = sorted({item.family for item in findings} - set(assessed))
        if unassessed:
            raise SchemaValidationError(
                f"readiness report {self.report_id} reports findings for {unassessed} without "
                "assessing those families; a finding for something that was never looked at is a "
                "claim about an absence of evidence"
            )
        duplicates = sorted({item.finding_id for item in findings if [x.finding_id for x in findings].count(item.finding_id) > 1})
        if duplicates:
            raise SchemaValidationError(f"findings contains duplicate finding_ids: {duplicates}")
        object.__setattr__(self, "findings", findings)
        object.__setattr__(self, "evidence_refs", bound_refs(self.evidence_refs, "evidence_refs", minimum=0))
        if self.graph_ref is not None:
            object.__setattr__(self, "graph_ref", AuthorityPolicyGraphRef.coerce(self.graph_ref, "graph_ref"))
        if self.notes is not None:
            object.__setattr__(
                self, "notes", require_text(self.notes, "notes", maximum=MAX_RATIONALE_CHARS)
            )
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def ready(self) -> bool:
        """§28's condition: every family assessed, and none of them found anything.

        Both halves, because the alternative reads as a pass. A production whose conflicts were
        never looked at is not semantically ready; it is unexamined, and the difference is the whole
        content of ``assessed_families``.
        """

        return not self.findings and len(self.assessed_families) == len(READINESS_FAMILIES)

    @property
    def unassessed_families(self) -> tuple[str, ...]:
        return tuple(item.value for item in READINESS_FAMILIES if item.value not in self.assessed_families)

    @property
    def blocking_families(self) -> tuple[str, ...]:
        return tuple(
            sorted({item.family for item in self.findings}, key=lambda value: _FAMILY_ORDER[value])
        )

    @property
    def counts(self) -> dict[str, int]:
        return {item.value: sum(1 for finding in self.findings if finding.family == item.value) for item in READINESS_FAMILIES}

    @property
    def blocking_paths(self) -> tuple[str, ...]:
        return tuple(sorted({path for item in self.findings for path in item.semantic_paths}))

    @property
    def report_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    @property
    def ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.READINESS.value, ref_id=self.report_id).with_digest(self.report_digest)

    def findings_for(self, family: Any) -> tuple[ReadinessFinding, ...]:
        wanted = ReadinessFamily.parse(family, "family").value
        return tuple(item for item in self.findings if item.family == wanted)

    def assessed(self, family: Any) -> bool:
        return ReadinessFamily.parse(family, "family").value in self.assessed_families

    def reasons(self) -> tuple[str, ...]:
        """What stands in the way, one line per finding, plus what was never assessed.

        Kept as text because a human reads this at a release decision: the count of blockers matters
        less than being told which door to go back to.
        """

        lines = [
            f"{item.family}: {item.detail} — clear it via {item.cleared_by}" for item in self.findings
        ]
        for family in self.unassessed_families:
            lines.append(f"{family} was never assessed, so nothing here rules it out")
        return tuple(lines)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "brief_ref": self.brief_ref.text,
            "revision_ref": self.revision_ref.text,
            "source_fingerprint_digest": self.source_fingerprint_digest,
            "profile_ref": self.profile_ref.text,
            "assessed_families": sorted(self.assessed_families),
            "findings": [item.fingerprint_inputs() for item in self.findings],
            "evidence_refs": sorted(item.text for item in self.evidence_refs),
            "graph_ref": None if self.graph_ref is None else self.graph_ref.pin_id,
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }


SemanticReleaseReadinessReport.NESTED = {
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "profile_ref": of(SemanticRef),
    "findings": of(ReadinessFinding),
    "evidence_refs": of(SemanticRef),
    "graph_ref": of(AuthorityPolicyGraphRef),
}

def _finding(
    family: ReadinessFamily,
    subject: SemanticRef,
    paths: Iterable[str],
    detail: str,
) -> ReadinessFinding:
    item = require_bound_ref(subject, "subject_ref")
    return ReadinessFinding(
        finding_id=f"rf-{family.value.lower()}-{item.ref_id}",
        family=family.value,
        subject_ref=item,
        semantic_paths=tuple(paths),
        detail=detail,
    )


def _conflict_findings(
    conflicts: Iterable[SemanticConflict],
) -> tuple[tuple[ReadinessFinding, ...], tuple[ReadinessFinding, ...], tuple[ReadinessFinding, ...]]:
    """Split the conflict records into §28's three conflict-shaped families.

    A rights/security conflict is reported once, under its own family, rather than also as a plain
    blocker: the two bullets in §28 are different alarms with different owners, and a reader who sees
    one conflict twice learns that the report double-counts.
    """

    rights: list[ReadinessFinding] = []
    blocking: list[ReadinessFinding] = []
    human: list[ReadinessFinding] = []
    for conflict in conflicts:
        item = SemanticConflict.coerce(conflict, "conflicts[]")
        if item.resolved:
            continue
        critical = (
            item.consequence_enum is ConflictConsequence.RIGHTS_SECURITY_CRITICAL
            or item.class_enum is ConflictClass.RIGHTS_SECURITY_CONFLICT
        )
        if critical:
            rights.append(
                _finding(
                    ReadinessFamily.RIGHTS_SECURITY_CONFLICT,
                    item.conflict_ref,
                    item.semantic_paths,
                    f"{item.class_enum.value} on {list(item.semantic_paths)} between "
                    f"{list(item.party_ids)} is unresolved and touches rights or security, so no "
                    "production may be released on it",
                )
            )
        elif item.consequence_enum.blocks_contract:
            blocking.append(
                _finding(
                    ReadinessFamily.BLOCKING_CONFLICT,
                    item.conflict_ref,
                    item.semantic_paths,
                    f"{item.class_enum.value} on {list(item.semantic_paths)} is "
                    f"{item.state_enum.value} with consequence {item.consequence_enum.value}",
                )
            )
        if item.state_enum is ConflictResolutionState.NEEDS_HUMAN_DECISION:
            human.append(
                _finding(
                    ReadinessFamily.HUMAN_DECISION_REQUIRED,
                    item.conflict_ref,
                    item.semantic_paths,
                    f"conflict {item.conflict_id} was escalated to a person and nothing has come "
                    "back; policy and recency are not allowed to answer it",
                )
            )
    return tuple(rights), tuple(blocking), tuple(human)


def _derived_findings(
    dependencies: Iterable[DerivedIntentDependency],
    freshness: BriefFreshnessVector,
    mandatory_paths: frozenset[str],
    revision: BriefRevision,
) -> tuple[ReadinessFinding, ...]:
    """Mandatory semantics whose declared dependencies no longer hold (§15, §28).

    A whole-artifact dependency (one that is not ``partial``) counts against every mandatory path,
    because it cannot say which part it spoils. A dependency the vector never declared its dimension
    for is reported as unknown rather than skipped: "we did not check that axis" is the sentence
    §28's list exists to force somebody to say.
    """

    out: list[ReadinessFinding] = []
    states = freshness.states
    for dependency in dependencies:
        item = DerivedIntentDependency.coerce(dependency, "dependencies[]")
        if item.dimension_enum.value not in states:
            state = FreshnessState.UNKNOWN.value
            detail = (
                f"derived element {item.derived_ref.ref_id} depends on {item.dimension} and "
                f"vector {freshness.vector_id} never declared that dimension"
            )
        else:
            state = states[item.dimension_enum.value]
            detail = (
                f"derived element {item.derived_ref.ref_id} is {state} on {item.dimension} "
                f"(last verified through revision {item.valid_through_revision}, this is "
                f"{revision.revision_number})"
            )
        if state == "CURRENT":
            continue
        touched = item.rework_paths or tuple(mandatory_paths)
        affected = tuple(sorted(set(touched) & mandatory_paths))
        if not affected:
            continue
        out.append(
            _finding(
                ReadinessFamily.STALE_MANDATORY_SEMANTICS,
                item.dependency_ref,
                affected,
                detail + f"; the mandatory semantics at {list(affected)} are carried by it",
            )
        )
    return tuple(out)


def assess_release_readiness(
    *,
    report_id: str,
    revision: BriefRevision,
    conflicts: Iterable[SemanticConflict] | None = None,
    ledger: OverrideLedger | None = None,
    questions: Iterable[OpenQuestion] | None = None,
    dependencies: Iterable[DerivedIntentDependency] | None = None,
    freshness: BriefFreshnessVector | None = None,
    assessments: Iterable[ReuseAssessment] | None = None,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    graph: AuthorityPolicyGraph | None = None,
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> SemanticReleaseReadinessReport:
    """Assess §28's families against one admitted revision, from the records that own each answer.

    Supplying a family's input is what puts that family on ``assessed_families``; leaving it out is
    a visible gap, not a pass. Nothing is decided here that the owning module has not already
    computed: conflicts answer their own resolution state, the ledger answers which overrides have
    lapsed and which debts block, the freshness vector answers which dimensions held, and the reuse
    assessments answer whether an artifact may be carried over.

    ``dependencies`` without ``freshness`` is refused rather than guessed at. Staleness is a
    comparison against recorded positions, so declaring the family while withholding the positions
    would produce either a clean report or a false one, and both are worse than an error.
    """

    if not isinstance(revision, BriefRevision):
        raise SchemaValidationError("assess_release_readiness expects revision to be a BriefRevision")
    if not revision.admitted:
        raise SchemaValidationError(
            f"revision {revision.revision_id} is {revision.status}; §28 asks whether an admitted "
            "production is ready, and a draft is not a production whose readiness can be reported"
        )
    if not isinstance(profile, SemanticEquivalenceProfile):
        raise SchemaValidationError(
            "profile must be a SemanticEquivalenceProfile; the fingerprint this report pins means "
            "one only under a named equivalence rule (§12)"
        )
    if dependencies is not None and freshness is None:
        raise SchemaValidationError(
            f"readiness report {report_id} declares derived dependencies to assess but no freshness "
            "vector; nothing has been compared, so the family cannot be reported either way"
        )
    if freshness is not None and dependencies is None:
        raise SchemaValidationError(
            f"readiness report {report_id} supplies a freshness vector with no dependencies to "
            "check it against; pass the dependencies the vector covers or leave the family unassessed"
        )

    assessed: list[ReadinessFamily] = []
    findings: list[ReadinessFinding] = []
    evidence: list[SemanticRef] = []

    if conflicts is not None:
        items = tuple(conflicts)
        assessed += [
            ReadinessFamily.BLOCKING_CONFLICT,
            ReadinessFamily.RIGHTS_SECURITY_CONFLICT,
            ReadinessFamily.HUMAN_DECISION_REQUIRED,
        ]
        rights, blocking, escalated = _conflict_findings(items)
        findings += list(rights) + list(blocking) + list(escalated)

    if questions is not None:
        if ReadinessFamily.HUMAN_DECISION_REQUIRED not in assessed:
            assessed.append(ReadinessFamily.HUMAN_DECISION_REQUIRED)
        for question in questions:
            item = OpenQuestion.coerce(question, "questions[]")
            if not item.blocking or QuestionStatus.parse(item.status) is QuestionStatus.ANSWERED:
                continue
            findings.append(
                _finding(
                    ReadinessFamily.HUMAN_DECISION_REQUIRED,
                    item.question_ref,
                    item.semantic_paths,
                    f"{item.text} was asked of {item.addressed_to or 'the human owner'} and is "
                    f"{item.status}; the answer is what unblocks {list(item.semantic_paths)}",
                )
            )

    if ledger is not None:
        assessed += [ReadinessFamily.EXPIRED_OVERRIDE, ReadinessFamily.RELEASE_BLOCKING_DEBT]
        evidence.append(ledger.ledger_ref)
        for receipt in ledger.expired_at(revision.revision_number):
            findings.append(
                _finding(
                    ReadinessFamily.EXPIRED_OVERRIDE,
                    receipt.receipt_ref,
                    (receipt.semantic_path,),
                    f"override {receipt.override_id} relaxed {receipt.rule_class} only through "
                    f"revision {receipt.expires_after_revision} and is read at "
                    f"{revision.revision_number}; the rule is in force again and "
                    f"{sorted(receipt.invalidation)} must be recompiled",
                )
            )
        for debt in ledger.release_blocking_debts():
            findings.append(
                _finding(
                    ReadinessFamily.RELEASE_BLOCKING_DEBT,
                    debt.debt_ref,
                    debt.affected_paths,
                    f"override debt {debt.debt_id} ({debt.kind}) is still open and policy marks it "
                    "release-blocking",
                )
            )

    if dependencies is not None and freshness is not None:
        assessed.append(ReadinessFamily.STALE_MANDATORY_SEMANTICS)
        evidence.append(freshness.vector_ref)
        mandatory = frozenset(
            item.semantic_path for item in revision.statements if item.mandatory
        )
        findings += list(_derived_findings(dependencies, freshness, mandatory, revision))

    if assessments is not None:
        assessed.append(ReadinessFamily.COMPILED_ARTIFACT_STALE)
        for assessment in assessments:
            item = ReuseAssessment.coerce(assessment, "assessments[]")
            if item.reuses_semantics:
                continue
            findings.append(
                _finding(
                    ReadinessFamily.COMPILED_ARTIFACT_STALE,
                    item.passport_ref,
                    item.invalidated_paths,
                    f"compiled artifact {item.passport_ref.ref_id} is {item.verdict} "
                    f"({item.recompute_scope}): {'; '.join(item.reasons) or 'no reason recorded'}",
                )
            )

    unique: dict[str, ReadinessFinding] = {}
    for item in findings:
        unique[item.finding_id] = item
    findings = list(unique.values())

    return SemanticReleaseReadinessReport(
        report_id=report_id,
        brief_ref=revision.brief_ref,
        revision_ref=revision.revision_ref,
        source_fingerprint_digest=fingerprint_revision(revision, profile=profile).semantic_digest,
        profile_ref=profile.ref,
        assessed_families=tuple(assessed),
        findings=tuple(findings),
        evidence_refs=tuple(evidence),
        graph_ref=None if graph is None else graph.pin(),
        notes=notes,
        metadata=metadata or {},
    )


def require_semantically_ready(report: SemanticReleaseReadinessReport, *, action: str) -> SemanticReleaseReadinessReport:
    """Refuse an action §28 gates until the report is clean, naming what has to change.

    The refusal is the report's only force. It stops work; it does not decide the case, and the
    message says who may.
    """

    if not isinstance(report, SemanticReleaseReadinessReport):
        raise SchemaValidationError("require_semantically_ready expects a SemanticReleaseReadinessReport")
    if report.ready:
        return report
    raise AdmissionRefusedError(
        f"cannot {action} for {report.revision_ref.ref_id} (§28): "
        + "; ".join(report.reasons())[: MAX_RATIONALE_CHARS - 64]
    )
