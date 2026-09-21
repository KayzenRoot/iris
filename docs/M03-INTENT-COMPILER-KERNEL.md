# M03 Creative Brief, Intent & Constraint Compiler — implementation note

Work Order: `IRIS-WO-0006` · Frozen contract: `m03-contract-v1.0` · Schema: `iris-intent-schema-v1`

This page documents the running code in `iris_intent/`. It is an implementation
note, not a planning document: the normative wording stays in
`planning/contracts/M03-MODULE-CONTRACT-FREEZE-CANDIDATE.md` and
`planning/modules/M03-CREATIVE-BRIEF-INTENT-CONSTRAINT-COMPILER.md`.

## Shape

The kernel is one package of 29 modules, organised along the five frozen semantic
areas (S01 brief/intent, S02 constraints, S03 fidelity, S04 execution intent,
S05 conflicts/overrides/versioning) plus the foundations and the boundaries later
modules implement. It runs no tool, imports no asset, renderer, cloud, database or
provider library, and holds no network, shell, clock or database call.

| Area | Module | Holds | Exports |
| --- | --- | --- | --- |
| — | `errors` | `IntentKernelError` and the twenty-one typed failures below it (`SchemaValidationError`, `UnsupportedVersionError`, `UntrustedExtensionError`, `RefError`, `AmbiguityBlockedError`, `AdmissionRefusedError`, `AuthorityError`, `PredicateError`, `ToleranceError`, `ScopeError`, `RevisionFrozenError`, `QualityAuthorityError`, `ProjectAuthorityError`, `CapabilityGapError`, `ConflictBlockedError`, `OverrideRefusedError`, `StaleSemanticError`, `ExplanationError`, `PortContractError`, `StoreConflictError`, `LimitExceededError`) | 22 |
| — | `base` | `Record`, `Labeled`, `encode_payload`/`decode_nested`, `of`/`union` schema markers | every value object |
| — | `versions` | `CONTRACT_VERSION`/`SCHEMA_VERSION` and their supported sets, `M01_CONTRACT_VERSION`, `ComponentVersion`, `canonical_json`, `content_digest`, the `require_*` guards | 19 |
| — | `limits` | the fifty `MAX_*` resource bounds the kernel enforces on structures it cannot otherwise measure | 51 |
| S01 | `identity` | `RefKind` (forty-five kinds), `SemanticRef`, `BriefRevisionRef`, `CreativeBriefIdentity`, `SourceKind`, `AuthorityLevel` with `ceiling_for`/`is_untrusted`/`require_authority`, the untrusted-source set | 16 |
| S01 | `intent` | `IntentStatement`, `IntentModel`, `StatementKind`, `IntentOrigin`, `ModalChannel`, `IntentAuthorityRef`, `authority_ceiling_for_origin` | 8 |
| S01 | `briefs` | `BriefRevision`, `RevisionKind`, `RevisionStatus`, `semantic_fields`, `intent_model_for` | 5 |
| S01 | `sources` | `RawInputRef`, `SourceAnchor`, `AnchorSpan`, `ProvenanceCapsule`, `DerivationKind` — raw input kept apart from the semantics derived from it | 7 |
| S01 | `ambiguity` | `AmbiguityRecord`, `AmbiguityKind`, `AmbiguityConsequence`, `OpenQuestion`, `ClarificationCandidate`, `FreedomZone`, `rank_clarifications`, `require_freedom_honoured` | 9 |
| S02 | `constraints` | `Constraint`, `ConstraintScope`, `ConstraintPolarity`, `ConstraintStrength`, `Condition`, `Comparison`, `ToleranceEnvelope`, `AntiReference`, `ProtectedAnchor`, `CrossModalLink`, `ConstraintBundle` + `admit()`, `ConstraintViolationRef`, `channel_set`, `require_no_authority_in_scope` | 17 |
| S02 | `predicates` | `PredicateRegistry`, `PredicateSignature`, `PredicateArgument`, `PredicateCall`, `ValueType`, `PredicateTrust`, `CORE_PREDICATES`, `reject_interpolation`, `require_known_predicate` | 11 |
| S02 | `normalization` | `ConstraintNormalForm`, `NormalizedRule`, `ReductionKind`, `normalize_bundle` — deterministic CNF, versioned | 6 |
| S02 | `admission` | `SemanticAdmissionShield`, `AdmissionCheck`, `AdmissionDecision`, `AdmissionFinding`, `AdmissionReport`, `require_admitted`, `detect_cycle`, `require_bounded_nesting`, `require_supported_versions` | 9 |
| S02 | `slicing` | `MinimumSufficientSemanticSlice`, `SemanticSliceRequest`, `SlicePurpose`, `closure_for`, `slice_intent`, `require_slice_minimality`, `structural_footprint` | 7 |
| S02 | `fingerprints` | `SemanticIntentFingerprint`, `ConstraintFingerprint`, `SemanticEquivalenceProfile`, `IntentDelta`, `SemanticChange`, `ChangeKind`, `DeltaSubjectKind`, the three `fingerprint_*` builders and `diff_*` | 14 |
| S02 | `freshness` | `BriefFreshnessVector`, `DerivedIntentDependency`, `FreshnessDimension`, `FreshnessBasis` + `REJECTED_FRESHNESS_BASES`, `assess_freshness`, `require_fresh`, `affected_paths` | 15 |
| S02 | `reuse` | `ReusePassport`, `ReuseAssessment`, `ReuseVerdict`, `RecomputeScope`, `passport_for`, `evaluate_reuse`, `require_reusable`, `requires_whole` | 8 |
| S03 | `fidelity` | `FidelityContractSpec`, `FidelityContractMember`, `FidelityCompilation` + status/gap/fingerprint, `GapClass`, `ReferenceRole`, `ZoneRequest`, `QualityClassRequest`/`QualityClassBasis`, `QualityIntentProjection`, `QualityObligationTrace`, `compile_fidelity_contract`, `require_compilable`, `require_no_downgrade`, `quality_contract_delta` | 27 |
| S04 | `execution` | `IntentOperation`, `IntentOperationFamily`, `SemanticLossClass`/`SemanticLossRule`, `CapabilityDemand`, `SemanticMutationClass`/`SemanticMutationEnvelope`, `BranchPolicy`, `SideEffectClass`, `ExecutionIntentBundle`/`Slice`/`Gap`/`Delta`/`Fingerprint`, `ProviderTranslationReceipt`, `compile_execution_intent`, `reject_provider_vocabulary`, `require_complete_execution_intent` | 38 |
| S04 | `explanation` | `IntentExplanationGraph`, `ExplanationNode`/`Edge`/`EdgeKind`/`NodeKind`, `ExplanationLevel`, `ExplanationProjection`, `ExplanationCacheKey`, `compile_explanation_graph`, `why_node`, `reachable_roots`, `explanation_cache_key`, `require_cache_valid` | 22 |
| S05 | `conflicts` | `SemanticConflict`, `ConflictClass`, `ConflictConsequence`, `ConflictResolution`/`State`/`Fingerprint`, `CandidateResolution`, `ExplorationFork`, `ScopeSplitProposal`, `MinimumSufficientConflictSlice`, `detect_conflicts`, `resolve_conflict`, `escalate_conflict`, `clarification_plan` | 20 |
| S05 | `authority` | `AuthorityPolicyGraph`/`Node`/`Edge`/`Ref`, `AuthorityDecision`, `OverrideAction`, `ReservedBoundary` + `default_reserved_boundaries`, `MANDATORY_RESERVED_KINDS`, `is_reserved_rule_class` | 13 |
| S05 | `overrides` | `OverrideProposal`, `OverrideReceipt`, `TemporaryOverrideLease`, `OverrideDebt`/`DebtKind`, `OverrideLedger`, `SemanticStateSnapshot`, `propose_override`, `authorize_proposal`, `issue_override`, `invalidation_targets` | 16 |
| S05 | `merge` | `BriefSemanticMergeAnalysis`, `MergeComponent`/`ComponentKind`/`Side`, `RestorationRevision`, `RevisionClassification`, `analyze_semantic_merge`, `classify_revision`, `meanings_agree` | 11 |
| S05 | `migration` | `MigrationReceipt`, `VersionVector`, `CompatibilityDeclaration`, `MigrationLoss`/`LossKind`, `MigrationComponentKind`, `migrate_revision`, `declare_compatible`, `require_declared`, `require_admissible` | 11 |
| S05 | `readiness` | `SemanticReleaseReadinessReport`, `ReadinessFinding`, `ReadinessFamily` (seven), `assess_release_readiness`, `require_semantically_ready` | 6 |
| — | `ports` | the twelve §12 extension boundaries as types: `ExtensionBoundary`, `ExtensionRef`, `ExtensionPorts`, `ProviderDescriptor`, `ExtensionObservation`, `PORT_BOUNDARIES`/`PORT_PROTOCOLS`, `require_port`, `require_answered_ref`, `boundaries_admitting` | 23 |
| — | `stores` | `RecordFamily`/`RECORD_FAMILIES`, `BriefRepository`/`SemanticRepository` protocols, deterministic `InMemoryBriefStore`/`InMemorySemanticStore`, `listing_digest` | 9 |
| — | `serialization` | the versioned envelope (`SerializationEnvelope`, `record_types`/`record_kinds`/`record_kind`, `envelope_for`/`from_envelope`, `serialize`/`deserialize`, `dumps`/`loads`) — the one place a payload states what it *is* | 11 |

`examples/m03_synthetic_profiles.py`, `tests/m03_kernel_support.py` and the
`tests/test_m03_*.py` files sit outside the package on purpose: domain vocabulary
must never be reachable from `iris_intent/`.
`tests/test_m03_domain_neutrality.py` enforces that boundary mechanically by
parsing the syntax tree of every kernel file, discovered twice (filesystem and
import system) so an added module cannot hide from the scan.

## Public API

`iris_intent.__all__` is derived at import from each module's own `__all__` (431
distinct names from 437 module-level exports — six names are re-exported by two
modules and the package refuses two *different* objects under one name), not
hand-copied. The other failure mode is refused too: a module that exports nothing,
and a module that lists a name it does not define. So the table above and the
package cannot drift apart.

```python
from iris_intent import (
    CreativeBriefIdentity, BriefRevision, IntentStatement, IntentModel,   # S01 what the brief says
    AmbiguityRecord, FreedomZone, OpenQuestion,                           # S01 what it does not say
    Constraint, ConstraintBundle, PredicateRegistry,                      # S02 the rules it obeys
    SemanticAdmissionShield, MinimumSufficientSemanticSlice,              # S02 admitted + sliced
    SemanticIntentFingerprint, IntentDelta, ReusePassport,                # S02 comparable + reusable
    FidelityContractSpec, compile_fidelity_contract,                      # S03 M01 bridge
    ExecutionIntentBundle, compile_execution_intent,                      # S04 provider-neutral intent
    IntentExplanationGraph, why_node,                                     # S04 why anything is here
    SemanticConflict, OverrideLedger, analyze_semantic_merge,             # S05 disagreement
    assess_release_readiness, SerializationEnvelope,                      # S05 may it move
)
```

### Compiling one brief

The four calls every domain goes through, verbatim from
`examples/m03_synthetic_profiles.py::run_kernel`:

```python
revision = BriefRevision(...)                        # S01: frozen, admitted, immutable
bundle = ConstraintBundle(...).admit(registry=..., admitted_by=...)   # S02: unknown predicate fails closed
slice_ = slice_intent(SemanticSliceRequest(                          # S02/S04: minimum sufficient closure
    revision=revision, purpose=SlicePurpose.COMPILE_QUALITY.value, paths=profile.paths, context=ctx,
))
quality = compile_fidelity_contract(                                 # S03: M01 spec or recorded gaps
    profile=m01_profile, revision=revision, bundle=bundle, contract_id=..., debt_policy=...,
)
execution = compile_execution_intent(bundle=bundle, revision=revision, ...)   # S04: semantics, not prompts
readiness = assess_release_readiness(report_id=..., revision=revision,         # S05: seven families, all assessed
                                    conflicts=conflicts, questions=questions, **inputs)
```

## Invariants the kernel enforces

The frozen contract lists 46 hard invariants in §5. Each one is implemented by a
mechanism, not by a comment; the grouping below is the shape the code actually
enforces, and every line is exercised by `tests/test_m03_*.py`.

1. **Identity is two things and the kernel says which.** `CreativeBriefIdentity`
   is stable; `BriefRevision` is immutable and versioned, and only
   `VERSIONED_REF_KINDS` may carry a revision. An admitted revision that is
   edited raises `RevisionFrozenError`, and the edit lands as a strictly later
   revision — `restore_revision` and `migrate_revision` append history rather than
   rewriting it (§5.2, §5.3, §5.36, §5.37).
2. **Origin sets the authority ceiling; confidence never does.** Each
   `IntentOrigin` has a floor and a ceiling (`EXPLICIT` TEAM_ASSERTED..HUMAN_OWNER,
   `DERIVED`/`DEFAULTED` PROJECT_RECORD..GOVERNED_POLICY, `INFERRED`
   UNTRUSTED..MODEL_INFERRED), and `SemanticAdmissionShield` refuses a `HARD`
   constraint backed by a machine level. A confidence number on a
   provider-observed statement is reported, not promoted (§5.4, §5.5, §5.6).
3. **Nothing may cite itself into authority.** `AuthorityLevel` knows which levels
   are self-asserting (only `GOVERNED_POLICY` and `HUMAN_OWNER`); everything else —
   retrieved context, model output, provider results — arrives in
   `UNTRUSTED_SOURCES` and is capped. Scope is not authority:
   `require_no_authority_in_scope` rejects a rule that tries to settle its own
   basis (§5.6, §5.14).
4. **Constraints are rules, not generator syntax.** A `Constraint` is a
   `PredicateCall` over a bounded `PredicateSignature` with typed
   `PredicateArgument`s; `reject_interpolation` refuses text that looks like code
   or a template, and the registry knows `CORE_PREDICATES` plus declared
   extensions only. Polarity (`REQUIRE`/`PREFER`/`ADVISORY`-vs-`FORBID` family) and
   strength (`ADVISORY`..`HARD`) are separate fields with separate fingerprint
   inputs. An unknown predicate fails closed at `bundle.admit()`; a mandatory one
   cannot be admitted at all (§5.9-§5.13).
5. **A slice carries what its purpose needs and nothing else.**
   `SlicePurpose` declares which closures it owes — `needs_constraints`,
   `needs_ambiguity`, `needs_provenance` — so an `AUDIT` slice pulls provenance
   capsules a `COMPILE_QUALITY` slice must not pay for, and
   `require_slice_minimality` refuses a slice that carries an unrelated statement
   (§15, §18).
6. **A fingerprint is semantics; a provider is not.** `semantic_digest` excludes
   the `FINGERPRINT_EXCLUSIONS` (provider, model, host, worker, runtime, cost and
   availability observations), so switching backends leaves the digest intact and a
   semantic edit does not. Equivalence across a source-only rewording is granted
   only by an explicit versioned `SemanticEquivalenceProfile`; without it the
   verdict is `RECOMPILE` (§5.24, §5.25, §5.45).
7. **Freshness is evidence about dependencies, not a clock.** `assess_freshness`
   walks `DerivedIntentDependency` records (`SOURCE_REVISION`, `SEMANTIC_MODEL`, …)
   against last-known digests, and `REJECTED_FRESHNESS_BASES` refuses
   timestamp-only and ordinal-only bases; `require_revision_ordinal` orders events
   without claiming recency. A partial dependency invalidates only
   `affected_paths`; a total one invalidates the artifact (§5.38, §5.44).
8. **M03 asks M01; it does not answer for M01.** `compile_fidelity_contract`
   builds a `FidelityContractSpec` from admitted dimension ids that exist in the
   pinned M01 registry (`dimensions_for`), and it calls
   `evaluator_registry.resolve(contract)` as the authority boundary — a missing
   panel member becomes a `MISSING_EVALUATOR_CAPABILITY` gap, never a
   self-granted capability. `require_no_downgrade` refuses a `QualityClassRequest`
   whose basis is scarcity, cost or provider convenience, and a spec with blocking
   gaps returns `INCOMPLETE` with the gaps instead of emitting a weaker contract
   (§5.16-§5.22).
9. **Execution intent is not a plan and not a prompt.** `IntentOperation` carries
   semantics with `SemanticMutationClass`/`SemanticMutationEnvelope` protecting
   identity anchors; provider vocabulary is scanned out (`PROVIDER_TERMS`,
   `find_provider_vocabulary`, `reject_provider_admission`), and a mandatory
   capability a provider cannot honour is recorded as an `ExecutionGapClass` item —
   `LOSSLESS_REQUIRED` refusals keep silent approximation out (§5.23, §5.26,
   §5.27). Translation in and out is a `ProviderTranslationReceipt`: an
   observation, not a mutation of canonical state (§5.42).
10. **Every compiled object has an explanation path.**
    `compile_explanation_graph` emits nodes that must each walk to a ground
    (`GROUND_NODE_KINDS`); a stranded, dangling, cyclic or ungroundable reference
    raises `ExplanationError`. `why_node`, `reachable_roots` and
    `explanation_cache_key` are projections over that same graph, so a summary
    cannot claim more than the graph proves (§5.28).
11. **Conflict resolution needs standing, and overrides need a receipt.**
    `resolve_conflict` accepts a `CandidateResolution` only when its basis is an
    authority the `AuthorityPolicyGraph` grants — recency, specificity and LLM
    confidence are not bases (§5.29). Agents may `propose_override` but only an
    authorized `issue_override` produces an immutable `OverrideReceipt`;
    `ReservedBoundary` marks rights/security and M01/M02 invariants
    non-overridable (§5.30-§5.32, §5.35), an expired `TemporaryOverrideLease`
    invalidates dependent compiled state (§5.33), and `OverrideDebt` is its own
    family, distinct from M01 `QualityDebt` (§5.34).
12. **Neighbour authority is borrowed, never duplicated.** Branch, variant and
    rollback topology come from M02 through `ports.ProjectGraphPort` refs and the
    kernel only reads them (§5.39). HIVE-shaped sources are untrusted derived
    context (§5.40). A publishing or delivery desire is a
    `SideEffectClass` question answered by `ports.DestinationPort` —
    `require_answered_ref` refuses an unanswered one, so wanting a release is not
    authorization for one (§5.41).
13. **Unknown versions, enums and sizes fail closed.** `require_contract_version`
    and `require_schema_version` accept only the pinned sets, `SerializationEnvelope`
    re-validates its payload, every `Labeled` parse raises on an unknown value, and
    each collection and text field is checked against `limits.MAX_*` — including
    `require_bounded_nesting` for condition trees a payload could otherwise use as
    a stack amplifier (§5.43).
14. **Readiness is a report with teeth.**
    `assess_release_readiness` returns a `SemanticReleaseReadinessReport` whose
    `ready` is true only with zero findings **and** all seven `ReadinessFamily`
    members assessed; a family nobody supplied data for is recorded as unassessed,
    which keeps "not asked" from looking like "clean". It remains a semantic gate
    and never a substitute for the downstream M01/M02 gates (§5.46).

## M01 and M02 boundary

M03 borrows quality vocabulary rather than rebuilding it:
`iris_intent.versions.QualityClass` **is** `iris_quality.contracts.QualityClass`
(same object), and the fidelity bridge imports `iris_quality` for the ladder, the
canonical JSON form, the `QualityDebtPolicy`, the `DefectSeverity` vocabulary its
blocking gaps are measured in, and the `DomainProfile`/`EvaluatorRegistry` it
consults but does not own. It imports exactly one M01 failure family —
`iris_quality.errors` — to classify a refusal it did not invent. M03 never
computes a score, never registers an evaluator, never extends a dimension registry,
and never weakens a FATAL gate: the bridge's whole authority is "here is a spec
M01 can check".

M02 owns project state: graph topology, branch/variant/rollback, snapshots, build
and lifecycle. M03 reads it through refs and cites it; `ports.ProjectGraphPort`
is a read boundary and `SemanticMutationClass` says which dimensions an edit moves,
not what the tree looks like afterwards. Where the two disagree about who decides,
the kernel's failure mode is a typed gap or refusal naming the owning module.

## Ports and stores

`ports` names the twelve §12 extension boundaries as types, not prose:
`ProjectGraphPort`, `SemanticTypePort`, `IdentityAnchorPort`, `QualityProfilePort`,
`CapabilityPort`, `CanonPort`, `ContextDependencyPort`, `RightsPort`,
`SecurityAuthorityPort`, `DestinationPort`, `ExplanationExportPort` and
`DomainVocabularyPort`. A real provider, DCC, rights system or brand store
implements one from the outside and crosses as an opaque, versioned
`ExtensionRef`; `ExtensionObservation` is what comes back — data the kernel can
record and fingerprint, never canonical state it must obey. An unanswered ref is
refused by `require_answered_ref` rather than treated as agreement.

`stores` says what a repository has to satisfy (`BriefRepository`,
`SemanticRepository`) and ships two deterministic in-memory references. It
enumerates `RECORD_FAMILIES` so a caller can ask what kind of thing a record is,
and `listing_digest` lets a store be compared without a database. Nothing in the
core imports either side's implementation, and no store mints a decision: the
families are storage categories, not authorities.

## Six synthetic profiles

§6 requires the same core to represent six production domains.
`examples/m03_synthetic_profiles.py` defines them as frozen `BriefProfile`
records built only from kernel primitives, and `run_kernel(profile)` pushes each
through the six calls above. The table is the real output:

| Profile | Channels | Statements | Constraints | Slice (stmts/rules) | Conflicts | Families assessed | Ready | Blockers | Intent digest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `logo-brand-web` | IMAGE, BRAND | 4 | 4 | 1 / 3 | 0 | 7 | yes | — | `62b972f101ac` |
| `product-photography` | IMAGE | 3 | 3 | 1 / 2 | 1 | 7 | no | `BLOCKING_CONFLICT` | `10508e92bcf0` |
| `isometric-game-asset` | GEOMETRY, MATERIAL | 3 | 3 | 1 / 1 | 0 | 7 | yes | — | `435bd71c2ad3` |
| `film-commercial` | VIDEO, MOTION, AUDIO | 4 | 4 | 1 / 1 | 0 | 7 | yes | — | `0934e1acb17a` |
| `spokesperson-digital-human` | VIDEO, SPEECH, BRAND | 3 | 3 | 1 / 1 | 0 | 7 | no | `HUMAN_DECISION_REQUIRED` | `8dd450852f60` |
| `voice-narration-music` | SPEECH, MUSIC, TEXT | 3 | 3 | 1 / 1 | 0 | 7 | yes | — | `a72489a1cf44` |

Six domains, six different intent digests, six different channel sets, and two
different non-trivial verdicts — a contradiction that blocks a contract and a
question only a human may answer. That asymmetry is the point: it is what shows
the kernel deriving consequences rather than echoing input. `Film` is the domain
where a conditional rule activates only because the request says a cut count
exists, which is also why the slice column is not a constant. And the
`isometric`/`voice` rows are the reason `MATERIAL`, `GEOMETRY` and `MUSIC` had to
be legal rule scopes at all.

`tests/test_m03_synthetic_profiles.py` drives the table (18 tests) and
`tests/test_m03_domain_neutrality.py` (24 tests) asserts the negative side: the
runner contains no branch on a profile id, the kernel never names any identifier
the fixtures introduce, and a seventh invented domain compiles through the same
calls with no kernel change.

## Design decisions inside the freeze

- **The package surface is derived, not copied** (see Public API): a hand-listed
  430-name `__all__` is a second API that drifts invisibly.
- **`KNOWN_CHANNELS` is computed from `ModalChannel`**, minus `CROSS` (a link, not a
  scope) and `UNSPECIFIED` (no scope). The hand-listed version had drifted: `MUSIC`
  was a statement modality and not a rule scope, so a brief could state a music
  fact and not bind a rule to it. Deriving it makes the drift structurally
  impossible.
- **A `ConstraintBundle` is admitted in two steps** — construct, then
  `.admit(registry=, admitted_by=)` — because admission is an event with a
  witness, and an object that is "half admitted" is how a rule enters a build
  without a predicate check.
- **`DEFAULTED` floors at `PROJECT_RECORD`, not at the inference ceiling.** A
  default is not an inference: someone has to stand behind the value the brief
  never stated, and a model suggestion cannot be that someone.
- **Post-spec emission gaps rebuild the spec** (`replace(spec, gaps=…)`) rather
  than returning the stale one. The invariant that a compilation's gaps and its
  spec's gaps are one list is right; an M01 refusal that happens after the spec is
  built just has to honour it. Previously that path raised `SchemaValidationError`
  instead of reporting the refusal — the crash hid the gap the caller needed.
- **Contract concept names map onto the code as follows**: §3's
  `ConstraintPredicate` is `predicates.PredicateSignature` + `PredicateCall`;
  `ConditionalConstraint` is `Constraint.conditions`;
  `ProtectedSemanticZone`/`AnchorRef` is `constraints.ProtectedAnchor`;
  `MinimumSufficientExecutionSlice` is `execution.ExecutionIntentSlice`;
  `SemanticDelta` is `fingerprints.IntentDelta`. The contract's wording is kept in
  each module's docstring so a reader searching for the contract name lands here.
- **`RefKind` grew the kinds the §3 concepts need** (`PROVENANCE`, `OBLIGATION`,
  `CONTRACT_SET`, `READINESS`, `LEASE`, `RECEIPT`, …) rather than overloading an
  existing kind, because a ref that names its kind wrongly is the one thing a
  trust boundary cannot recover from.

## What M03 deliberately does not do

Per §19: no media generation, no pixel/CV inference, no Blender/ComfyUI/Maya or
any provider execution, no real worker scheduling, no hardware discovery or
resource placement, no model routing/training/download, no Scene/Asset/Camera/
Material IR, no Asset/Persona/Voice/Music/Brand DNA store, no narrative canon
engine, no real image/video/3D/audio evaluators, no HIVE retrieval
implementation, no universal media provenance/C2PA, no security/RBAC engine, no
storage/CAS/database, no publishing/export APIs, and no M04+ domain
implementation. The six profiles in `examples/` are fixtures whose predicates are
arithmetic and string comparisons; the providers that will satisfy them arrive
later through the ports above. This branch does not merge and does not start M04.
