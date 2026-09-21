# M03 — Technology Registry

Status: `S01_ACTIVE`
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
