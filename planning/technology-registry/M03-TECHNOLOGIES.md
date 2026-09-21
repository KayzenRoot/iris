# M03 — Technology Registry

Status: `S02_ACTIVE`
Module: `M03 Creative Brief, Intent & Constraint Compiler`

This registry tracks IRIS-owned technology candidates for M03. Names describe internal design concepts, not patent claims. Prior-art/external-reference review remains mandatory before Final Technology Review and Contract Freeze.

## IRIS-ICX-001 — Intent Lattice
**Purpose:** represent creative intent as typed semantic statements with provenance, authority, confidence and scope instead of one flat prompt.
**Production benefit:** reusable, explainable intent across image/video/3D/audio.
**Performance/token benefit:** downstream consumers request only relevant semantic slices.
**Risk:** schema fragmentation if semantic paths are not governed.
**Status:** PROPOSED_S01.

## IRIS-ICX-002 — Raw-to-Canonical Twin
**Purpose:** preserve original wording/assets beside canonical normalized intent.
**Benefit:** prevents lossy normalization and allows re-compilation when the compiler improves.
**Risk:** sensitive source material requires M53/M54 policy.
**Status:** PROPOSED_S01.

## IRIS-ICX-003 — Intent Origin Ledger
**Purpose:** make EXPLICIT / DERIVED / INFERRED / DEFAULTED origin machine-verifiable.
**Benefit:** prevents an AI guess from masquerading as user intent.
**Risk:** excessive bookkeeping unless compactly serialized.
**Status:** PROPOSED_S01.

## IRIS-ICX-004 — Authority × Confidence Matrix
**Purpose:** separate “who has the right to say this?” from “how certain is the interpretation?”.
**Benefit:** deterministic conflict policy later in S05.
**Risk:** authority models can become organization-specific; keep core extensible.
**Status:** PROPOSED_S01.

## IRIS-ICX-005 — Ambiguity Budget
**Purpose:** quantify unresolved ambiguity by consequence class rather than generic confidence.
**Benefit:** spend clarification effort where it prevents quality/cost failures.
**Risk:** false precision; values must be ordinal/policy-driven unless empirical calibration exists.
**Status:** PROPOSED_S01.

## IRIS-ICX-006 — Clarification Oracle
**Purpose:** rank the smallest set of questions that maximally reduces blocking/quality-critical ambiguity.
**Benefit:** fewer user interruptions and less token waste.
**Dependencies:** Intent Lattice + Ambiguity Budget.
**Risk:** premature implementation as an LLM-only heuristic; final design should permit deterministic rules and learned ranking.
**Status:** PROPOSED_S01.

## IRIS-ICX-007 — Creative Freedom Map
**Purpose:** encode intentionally unconstrained dimensions.
**Benefit:** preserves exploration diversity and prevents over-constrained generations.
**Risk:** later provider compilers might ignore freedom zones and overfit to defaults.
**Status:** PROPOSED_S01.

## IRIS-ICX-008 — Minimum Sufficient Intent Slice
**Purpose:** compile consumer-specific intent views with only declared semantic dependencies.
**Benefit:** lower tokens, faster reasoning, smaller context poisoning surface and better cache locality.
**Dependencies:** M02 dependency-slice semantics; M52 retrieval later.
**Risk:** under-slicing could omit a hidden dependency; fail closed on discovered reads.
**Status:** PROPOSED_S01.

## IRIS-ICX-009 — Semantic Intent Fingerprint
**Purpose:** versioned digest over normalized correctness-relevant brief semantics.
**Benefit:** safe reuse/invalidation and M02 causal integration.
**Risk:** compiler/schema changes can make old/new fingerprints incomparable without version tagging.
**Status:** PROPOSED_S01.

## IRIS-ICX-010 — Consumer-Scoped Semantic Equivalence
**Purpose:** determine equivalence relative to a declared consumer/profile rather than globally.
**Benefit:** maximizes cache/reuse without pretending all paraphrases are identical.
**Risk:** unsafe equivalence if profile dependency surface is incomplete.
**Status:** PROPOSED_S01.

## IRIS-ICX-011 — Semantic Delta Brief
**Purpose:** represent changes between brief revisions as typed semantic deltas.
**Benefit:** precise M02 impact cones and partial regeneration.
**Risk:** requires stable semantic path versioning.
**Status:** PROPOSED_S01.

## IRIS-ICX-012 — Intent Provenance Capsule
**Purpose:** compact evidence bundle proving the source/rationale of normalized statements.
**Benefit:** explainability, audit and safer agent automation.
**Token benefit:** downstream LLMs can receive compact provenance summaries plus references instead of full history.
**Status:** PROPOSED_S01.

## IRIS-ICX-013 — Multilingual Semantic Anchor
**Purpose:** bind source-language wording, normalized language-neutral semantics and translation provenance.
**Benefit:** avoids translation drift before M47 full localization.
**Risk:** some culturally dependent meanings cannot be language-neutralized safely.
**Status:** PROPOSED_S01.

## IRIS-ICX-014 — Semantic Entropy Radar
**Purpose:** estimate where a brief has too many plausible interpretations.
**Benefit:** targets clarification and candidate diversity.
**Risk:** must not be marketed as objective information-theoretic entropy unless mathematically calibrated.
**Status:** RESEARCH_CANDIDATE.

## IRIS-ICX-015 — Brief Cache Passport
**Purpose:** package schema/compiler/fingerprint/equivalence metadata needed to decide whether a normalized brief or slice is reusable.
**Benefit:** avoids repeated LLM normalization for unchanged intent.
**Dependencies:** M02 reuse/trust contracts.
**Risk:** stale policy/context refs must invalidate reuse.
**Status:** PROPOSED_S01.

## IRIS-ICX-016 — Human Meaning Preservation Gate
**Purpose:** compare normalized/compiled intent against explicit source statements and flag strengthening, weakening or invented commitments.
**Benefit:** reduces silent semantic drift caused by automated normalization.
**Risk:** high-quality semantic comparison may require later evaluator integration; kernel contract should stay provider-neutral.
**Status:** PROPOSED_S01.

## S01 technology disposition

Accepted as M03 design candidates for continued planning:
`IRIS-ICX-001..016`.

No candidate is frozen or claimed novel yet. S02-S05 may merge, supersede or reject candidates. Final prior-art/technology review is required before contract freeze.


## IRIS-ICX-017 — Constraint Algebra
**Purpose:** canonical provider-neutral polarity/strength/predicate composition.
**Benefit:** one semantic rule can compile to prompts, masks, graph exclusions or validators without changing meaning.
**Risk:** algebra can become too expressive; arbitrary code is forbidden.
**Status:** PROPOSED_S02.

## IRIS-ICX-018 — Negative Intent Firewall
**Purpose:** preserve MUST-NOT semantics as first-class rules and verify that provider compilation does not drop them.
**Benefit:** negative intent survives model/workflow changes.
**Risk:** some providers cannot guarantee negative requirements; compiler must report capability gaps.
**Status:** PROPOSED_S02.

## IRIS-ICX-019 — Constraint Scope Mesh
**Purpose:** map every rule to precise project/production/artifact/region/time/audience scopes.
**Benefit:** smaller invalidation and prompt surfaces.
**Status:** PROPOSED_S02.

## IRIS-ICX-020 — Constraint Facet Index
**Purpose:** index rules by affected semantic facets for M02 impact analysis and M04 compilation.
**Benefit:** faster selective rebuild and cache reuse.
**Status:** PROPOSED_S02.

## IRIS-ICX-021 — Constraint Normal Form
**Purpose:** deterministic canonicalization of units, aliases, sets and compound rules.
**Benefit:** stable fingerprints and conflict analysis.
**Risk:** normalization must never change meaning.
**Status:** PROPOSED_S02.

## IRIS-ICX-022 — Conflict Candidate Radar
**Purpose:** detect potentially incompatible normalized constraints without deciding precedence.
**Benefit:** prepares S05 conflict resolution early.
**Risk:** false positives if semantic compatibility is approximated too aggressively.
**Status:** PROPOSED_S02.

## IRIS-ICX-023 — Faceted Anti-Reference
**Purpose:** specify exactly which properties of an anti-reference must be avoided.
**Benefit:** avoids blanket negative similarity and preserves useful unrelated characteristics.
**Status:** PROPOSED_S02.

## IRIS-ICX-024 — Protected Semantic Zone
**Purpose:** bind hard no-mutation areas such as approved logo geometry, identity anchors or product claims.
**Benefit:** safer partial regeneration and repair.
**Dependencies:** M05/M39/M46 identity/brand anchors later.
**Status:** PROPOSED_S02.

## IRIS-ICX-025 — Tolerance Envelope
**Purpose:** typed deviation windows with explicit units/metric refs.
**Benefit:** expresses “close enough” without ambiguous provider weights.
**Status:** PROPOSED_S02.

## IRIS-ICX-026 — Conditional Constraint Router
**Purpose:** activate constraints from explicit semantic conditions rather than hidden workflow branching.
**Benefit:** explainable destination/profile-aware rules.
**Status:** PROPOSED_S02.

## IRIS-ICX-027 — Cross-Modal Constraint Binder
**Purpose:** one semantic rule can target image/video/3D/voice/music identity simultaneously.
**Benefit:** consistency for digital humans, brands and products.
**Status:** PROPOSED_S02.

## IRIS-ICX-028 — Constraint Delta Fingerprint
**Purpose:** identify exactly which normalized constraint semantics changed between brief revisions.
**Benefit:** precise M02 impact cones and minimal regeneration.
**Status:** PROPOSED_S02.

## IRIS-ICX-029 — Minimum Sufficient Constraint Slice
**Purpose:** emit only constraints relevant to a declared downstream consumer.
**Benefit:** lower tokens, lower context noise, smaller cache keys.
**Risk:** hidden dependencies must be discovered and fail closed.
**Status:** PROPOSED_S02.

## IRIS-ICX-030 — Constraint Coverage Heatmap
**Purpose:** expose CONSTRAINED/FREEDOM_ZONE/UNKNOWN/NOT_APPLICABLE regions of a brief.
**Benefit:** detects both under-specification and over-constraint.
**Status:** PROPOSED_S02.

## IRIS-ICX-031 — Constraint Cost Signal
**Purpose:** attach provider-neutral cost/complexity impact classes to semantic demands.
**Benefit:** lets M07-M13 plan compute without M03 owning hardware policy.
**Status:** PROPOSED_S02.

## IRIS-ICX-032 — Negative Leakage Detector
**Purpose:** later verify that hard FORBID semantics survived compilation into a provider plan.
**Benefit:** catches silent loss of negative requirements.
**Dependencies:** S04/provider compiler evidence.
**Status:** PROPOSED_S02.

## IRIS-ICX-033 — Constraint Evidence Capsule
**Purpose:** compact provenance/authority/rationale packet for a rule or slice.
**Benefit:** explainability with low token overhead.
**Status:** PROPOSED_S02.

## IRIS-ICX-034 — Creative Elasticity Budget
**Purpose:** quantify how much of a solution space is intentionally free vs constrained without pretending to be a universal numeric creativity score.
**Benefit:** prevents creative collapse from excessive hard rules.
**Status:** RESEARCH_CANDIDATE.

## IRIS-ICX-035 — Constraint Admission Shield
**Purpose:** reject imperative text from untrusted/retrieved sources unless an authorized source explicitly admits it as a rule.
**Benefit:** prompt-injection/context-poisoning resistance for future HIVE/web/reference integrations.
**Status:** PROPOSED_S02.

## IRIS-ICX-036 — Immutable Constraint Pack
**Purpose:** versioned reusable bundles for brand/persona/product/destination policy.
**Benefit:** deterministic reuse and compact references instead of repeating large constraint sets.
**Status:** PROPOSED_S02.

## S02 technology disposition

Continue planning with `IRIS-ICX-017..036`. No S02 candidate is frozen yet. S03-S05 and Final Technology Review may merge/supersede/reject candidates.
