# M05 S04 Research — Identity Anchors, Mutation Boundaries & Drift Detection

Date: 2026-09-23
Module: M05 — Asset DNA 2.0 & Cross-Modal Identity
Session: S04
Status: `COMPLETE_FOR_MODULE_PLANNING`
Issue: #37
Authorized baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Research question

How should IRIS distinguish normal variation, representation error, identity drift, authorized mutation and true identity break without allowing similarity scores, providers or downstream modules to rewrite canonical DNA?

## Key conclusion

M05 needs a typed identity-state transition model.

A difference between observation and canonical DNA can resolve to one of several different semantic outcomes:
- contextual variation;
- representation defect / repair-needed state;
- evidence-only uncertainty;
- bounded drift;
- mutation proposal;
- authorized same-identity mutation;
- identity break;
- identity split;
- identity equivalence/consolidation claim.

These outcomes are not interchangeable.

## Authority boundary

### M05
Owns:
- canonical identity anchors and their authority class;
- semantic mutation rules for M05 DNA;
- identity-drift evidence vocabulary;
- same-identity versus new-identity transition semantics;
- split/merge/equivalence proposal semantics;
- immutable DNA revision admission rules.

### M01
Retains:
- quality/evaluator/promotion authority;
- acceptance thresholds where an evaluator judges production quality;
- QualityDebt and North Star quality semantics.

M05 may route evidence to M01 or another evaluator but cannot become a parallel quality court.

### M37
Retains:
- temporal/shot continuity state and continuity QA;
- frame/shot artifact radar;
- temporal repair.

M37 can emit identity-related continuity evidence, but cannot mutate canonical M05 DNA.

### M39
Retains:
- digital-human / virtual-persona production;
- face/body/hair/clothing/acting continuity;
- digital-human cross-modal runtime behavior.

M05 remains the generic persistent identity root. M39 canonical persona/domain identity must bind to M05 rather than create a competing root identity system.

This overlap must be rechecked during M06-M60 Forward Compatibility Scan.

### M53 / M54
Retain provenance/rights/consent and security/identity/restricted-vault authority.

M05 references their evidence/policies and minimizes sensitive payloads.

## IdentityAnchor authority classes

S04 refines S01 anchors into explicit authority classes:

- `CANONICAL` — admitted semantic identity anchor;
- `BOUND_EXTERNAL` — explicitly governed external identity binding;
- `REPRESENTATION` — M04/runtime representation binding;
- `PROVENANCE` — lineage/attestation reference;
- `OBSERVATION` — evidence-only measurement;
- `PROPOSED` — candidate anchor awaiting admission;
- `REVOKED` — historically known but no longer valid for current use.

Anchor confidence never changes authority class by itself.

## Anchor lifecycle

Anchor operations are explicit:
- ADD;
- REBIND;
- SUPERSEDE;
- REVOKE;
- RESTORE;
- EXPIRE;
- INVALIDATE_EVIDENCE.

Every operation records:
- source DNA revision;
- target anchor;
- authority/policy ref;
- reason;
- evidence refs;
- resulting status.

Anchor deletion is not history erasure.

## Drift evidence model

S04 introduces `IdentityDriftEvidence`.

Drift evidence is path-level and typed:
- expected canonical trait/anchor;
- observed value/ref;
- comparison domain;
- magnitude/semantic delta;
- uncertainty;
- source modality;
- observation provenance;
- evaluator owner;
- timestamp/scope as evidence metadata;
- impacted criticality/mutability class.

Evidence does not mutate DNA.

## Drift dimensions

M05 must support at least:
- numeric/unit-aware trait drift;
- categorical drift;
- structural/component drift;
- topology/relation drift;
- anchor/link drift;
- cross-modal inconsistency;
- absence/missing-required-trait drift;
- family/profile drift;
- identity-level collision/split evidence.

A single scalar "identity score" is insufficient.

## Drift status

Candidate semantic statuses:
- `NO_DRIFT`;
- `WITHIN_DECLARED_VARIATION`;
- `OBSERVATION_UNCERTAIN`;
- `REPRESENTATION_DRIFT`;
- `IDENTITY_RELEVANT_DRIFT`;
- `MUTATION_CANDIDATE`;
- `IDENTITY_BREAK_CANDIDATE`;
- `COLLISION_OR_SPLIT_CANDIDATE`.

These are semantic findings, not M01 quality grades.

## Repair versus mutation

### Repair
Goal: make a representation/output conform again to the same canonical DNA revision.

Repair does not:
- create a new canonical DNA revision by itself;
- authorize protected trait change;
- redefine identity.

### Mutation
Goal: change canonical DNA intentionally.

A mutation always requires:
- explicit proposal;
- source revision;
- typed trait/link/anchor changes;
- authority/policy refs;
- identity-impact classification;
- compatibility implications;
- evidence/reason;
- resulting immutable revision if admitted.

## DNAMutationProposal

Proposed fields/concepts:
- proposal ID;
- dna_id;
- source revision;
- requested change set;
- changed trait/anchor/link paths;
- mutation reason;
- requested continuity outcome;
- authority/policy refs;
- provenance/evidence refs;
- risk/impact summary;
- required external approvals;
- compatibility surface;
- expiry/validity if applicable.

A proposal is not a revision.

## IdentityMutationDecision

Candidate outcomes:
- `REJECT`;
- `REPAIR_INSTEAD`;
- `CONTEXTUAL_VARIATION_ONLY`;
- `ADMIT_SAME_IDENTITY_REVISION`;
- `REQUIRE_NEW_IDENTITY`;
- `REQUIRE_SPLIT`;
- `REQUEST_MORE_EVIDENCE`.

The decision authority is explicit and policy-bound.

Automated systems may produce proposals/findings, but protected mutations cannot be silently admitted from model output.

## Identity break

A change requires new identity when policy says the proposed state no longer satisfies same-identity continuity.

Identity break creates:
- new `dna_id`;
- explicit lineage relation;
- source revision ref;
- break reason;
- carried/inherited traits where permitted;
- no rewrite of the source identity history.

## Split

Split is needed when one historical identity record actually contains more than one persistent subject or intentionally forks into separately governed identities.

Rules:
- source identity remains historical;
- each resulting identity gets a new stable ID unless a policy explicitly preserves one branch as continuation;
- trait/component/link allocation is explicit;
- provenance remains reachable;
- no evidence is silently duplicated as authoritative canonical truth.

## Equivalence / consolidation

Two existing IDs that appear to refer to the same subject are not auto-merged.

S04 permits an `IdentityConsolidationProposal` / equivalence claim.

If admitted:
- both histories remain auditable;
- redirect/alias/equivalence semantics are explicit;
- one canonical continuation may be selected by policy;
- IDs are not physically erased;
- provenance and rights constraints survive.

Detailed portability/branching compatibility is finalized in S05.

## Identity continuity envelope

S04 introduces `IdentityContinuityEnvelope`.

It records the policy context for deciding whether a change preserves identity:
- identity-defining traits;
- bounded mutable traits;
- contextual traits;
- required anchors;
- required cross-modal links;
- allowed substitutions;
- forbidden transitions;
- evaluator/evidence requirements;
- decision authority refs.

This is not an M01 quality contract.

## Drift aggregation

Multiple evidence items may be summarized as an `IdentityDriftReport`.

Report requirements:
- preserves path-level evidence;
- cannot hide a fatal identity-defining conflict behind a good aggregate score;
- separates missing data from passing data;
- records uncertainty;
- records evaluator ownership;
- deterministic ordering/fingerprint.

## Confidence firewall

No threshold such as "98% face similarity" can alone:
- merge identities;
- admit a mutation;
- rebind canonical anchors;
- override an immutable trait;
- prove consent/rights;
- prove real-world personal identity.

Confidence can prioritize review only.

## Privacy-minimized drift

Drift detection must support references to restricted evidence without copying it into normal DNA history.

Examples:
- face embeddings;
- voiceprints;
- biometric-like templates;
- private reference media.

M54 can own restricted vault/access policy.
M53 owns consent/rights provenance.
M05 keeps minimal refs/status needed for semantic continuity.

## Threat model additions

S04 must defend against:
- similarity-score auto-merge;
- auto-admission from generative-model output;
- drift score averaging away identity-defining failures;
- provider changes causing false drift;
- contextual state causing false mutation;
- repair workflow accidentally rewriting DNA;
- stale anchor rebind without authority;
- split/merge erasing provenance;
- digital-human module creating a competing identity root;
- biometric evidence copied into normal canonical DNA;
- missing evidence interpreted as pass;
- arbitrary mutation authority hidden in a plugin/model.

## S04 outcome

S04 freezes mutation/drift/continuity semantics, not implementation thresholds.

S05 will finalize branching, compatibility, packaging, portability and marketplace contract.
