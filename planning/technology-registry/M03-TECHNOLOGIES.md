# M03 — Technology Registry

Status: `S04_ACTIVE`
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


## IRIS-ICX-037 — Quality Obligation Compiler
**Purpose:** translate admitted intent/constraints into M01-compatible quality obligations without duplicating M01 authority.
**Benefit:** “creative intent” becomes machine-enforceable quality requirements.
**Risk:** bad semantic mappings could over/under-constrain quality; every mapping needs traceability.
**Status:** PROPOSED_S03.

## IRIS-ICX-038 — Fidelity Contract Spec
**Purpose:** non-authoritative intermediate representation between M03 semantics and M01 FidelityContract.
**Benefit:** keeps compiler concerns separate from the frozen M01 schema and supports gap analysis before contract emission.
**Status:** PROPOSED_S03.

## IRIS-ICX-039 — Quality Obligation Trace
**Purpose:** map every emitted dimension/reference/rule back to source intent, constraint or policy.
**Benefit:** deterministic “why is this required?” explanations and safer audits.
**Token benefit:** downstream systems can receive compact traces instead of full conversations.
**Status:** PROPOSED_S03.

## IRIS-ICX-040 — Profile Capability Matcher
**Purpose:** select only admitted M01 DomainProfiles whose dimension/capability surface covers mandatory obligations.
**Benefit:** avoids nearest-text profile guessing and hidden quality loss.
**Status:** PROPOSED_S03.

## IRIS-ICX-041 — Quality Gap Sentinel
**Purpose:** classify missing profile/dimension/evaluator/reference/registry coverage and fail closed.
**Benefit:** prevents silent requirement deletion.
**Status:** PROPOSED_S03.

## IRIS-ICX-042 — Quality-Class Truth Lock
**Purpose:** prevent hardware/provider limitations or vague adjectives from silently changing the requested M01 QualityClass.
**Benefit:** preserves master quality targets across constrained hardware.
**Status:** PROPOSED_S03.

## IRIS-ICX-043 — Evaluator Authority Firewall Bridge
**Purpose:** guarantee M03 never grants evaluator capability; promotion-capable authority remains resolved by M01 registry mechanisms.
**Benefit:** blocks fabricated judge capability from compiler/agent outputs.
**Status:** PROPOSED_S03.

## IRIS-ICX-044 — Contract Round-Trip Seal
**Purpose:** require emitted M01 contracts to validate, serialize, digest and reconstruct canonically before admission.
**Benefit:** catches schema/compiler drift before execution.
**Status:** PROPOSED_S03.

## IRIS-ICX-045 — Fidelity Compilation Fingerprint
**Purpose:** digest source semantics + profile/registry/policy/compiler versions + emitted contract payload.
**Benefit:** stale detection, reuse and precise M02 invalidation.
**Status:** PROPOSED_S03.

## IRIS-ICX-046 — Quality Contract Delta
**Purpose:** classify the semantic effect of brief changes on quality obligations.
**Benefit:** avoids re-evaluating/regenerating unrelated work.
**Status:** PROPOSED_S03.

## IRIS-ICX-047 — Multi-Contract Composer
**Purpose:** compile one multimodal brief into subject-specific M01 contracts linked as a governed set.
**Benefit:** avoids unsafe mega-contracts mixing incompatible evaluator domains.
**Status:** PROPOSED_S03.

## IRIS-ICX-048 — Quality Policy Overlay Resolver
**Purpose:** resolve project/domain/brand/persona/destination quality layers to one explicit contract result with provenance.
**Benefit:** no hidden inheritance and deterministic policy composition.
**Risk:** precedence is partly S05-owned and must remain authority-aware.
**Status:** PROPOSED_S03.

## IRIS-ICX-049 — Strict Reference Role Compiler
**Purpose:** distinguish inspiration, must-match, identity-anchor and quality-baseline references before M01 binding.
**Benefit:** prevents loose inspiration from accidentally becoming strict similarity obligation.
**Status:** PROPOSED_S03.

## IRIS-ICX-050 — Semantic Zone Request Bridge
**Purpose:** express quality-critical semantic zones without owning pixel/mesh geometry.
**Benefit:** later domain modules can materialize zones while M01 keeps quality semantics.
**Status:** PROPOSED_S03.

## IRIS-ICX-051 — Human Review Obligation Bridge
**Purpose:** compile authorized human-review requirements into M01-compatible contract obligations without creating approval evidence.
**Benefit:** preserves human boundaries for identity/brand/public-release workflows.
**Status:** PROPOSED_S03.

## IRIS-ICX-052 — No-Downgrade Quality Shield
**Purpose:** make any attempted quality-class weakening caused by compute/provider scarcity an explicit blocking event.
**Benefit:** 8 GB hardware stays supported through smarter execution rather than lower hidden quality.
**Status:** PROPOSED_S03.

## IRIS-ICX-053 — Contract Explainability Capsule
**Purpose:** compact why-class/why-dimension/why-reference/why-review packet linked to immutable source IDs.
**Benefit:** auditability with strong token economy.
**Status:** PROPOSED_S03.

## IRIS-ICX-054 — Compilation Reuse Passport
**Purpose:** prove whether a prior Fidelity Contract compilation can be reused after a brief/constraint revision.
**Benefit:** skips redundant LLM/compiler work while preserving stale-context safety.
**Dependencies:** ICX-009/028/045/046 and M02 reuse semantics.
**Status:** PROPOSED_S03.

## S03 technology disposition

Continue planning with `IRIS-ICX-037..054`. No S03 candidate is frozen or claimed novel yet. Final Technology Review must assess overlap, prior art, implementation value and merge/supersession opportunities across ICX-001..054.


## IRIS-ICX-055 — Execution Intent Bundle
**Purpose:** immutable provider-neutral description of desired production behavior linked to brief/constraints/Fidelity Contracts.
**Benefit:** provider portability without semantic drift.
**Status:** PROPOSED_S04.

## IRIS-ICX-056 — Capability Demand Graph
**Purpose:** express required capabilities and semantic dependencies without provider identities.
**Benefit:** supports empirical routing across ComfyUI, Blender, APIs, LAN/cloud providers later.
**Status:** PROPOSED_S04.

## IRIS-ICX-057 — Semantic Mutation Envelope
**Purpose:** explicitly separate protected, mutable and conditionally mutable semantic regions/properties.
**Benefit:** safer variations, repair and partial regeneration.
**Status:** PROPOSED_S04.

## IRIS-ICX-058 — Semantic Loss Firewall
**Purpose:** classify obligations as lossless/approximable/free/advisory and block silent loss of required meaning.
**Benefit:** provider changes cannot quietly degrade intent.
**Status:** PROPOSED_S04.

## IRIS-ICX-059 — Provider Translation Receipt
**Purpose:** require later compilers to report exact/approximate/delegated/unsupported mapping for each semantic obligation.
**Benefit:** makes provider compilation auditable and testable.
**Status:** PROPOSED_S04.

## IRIS-ICX-060 — Provider Drift Sentinel
**Purpose:** detect when a previously capable provider/version can no longer represent required execution semantics.
**Benefit:** safer upgrades/canaries and automatic rerouting.
**Dependencies:** M14-M18 qualification data later.
**Status:** PROPOSED_S04.

## IRIS-ICX-061 — Prompt Ephemerality Guard
**Purpose:** enforce that provider prompt text is derived output, never canonical project intent.
**Benefit:** avoids prompt-centric lock-in and prompt injection promotion.
**Status:** PROPOSED_S04.

## IRIS-ICX-062 — Minimum Sufficient Execution Slice
**Purpose:** compile only operation-relevant intent/constraints/quality/provenance into downstream context.
**Benefit:** major LLM token/context savings and reduced cross-task contamination.
**Status:** PROPOSED_S04.

## IRIS-ICX-063 — Intent Explanation Graph
**Purpose:** canonical provenance graph connecting source statements to constraints, quality obligations, operations and capability demands.
**Benefit:** deterministic explainability for users, agents and audits.
**Status:** PROPOSED_S04.

## IRIS-ICX-064 — Explainability Projection Engine
**Purpose:** render TRACE_ID_ONLY/COMPACT/HUMAN/AUDIT views over the same explanation graph.
**Benefit:** high auditability without paying full-context token cost everywhere.
**Status:** PROPOSED_S04.

## IRIS-ICX-065 — Execution Intent Fingerprint
**Purpose:** provider-independent digest of semantic execution demand.
**Benefit:** reuse survives provider/worker/location changes.
**Status:** PROPOSED_S04.

## IRIS-ICX-066 — Execution Intent Delta
**Purpose:** classify operation/capability/mutation/quality-reference changes between revisions.
**Benefit:** selective M04/M16 recompilation and smaller M02 impact cones.
**Status:** PROPOSED_S04.

## IRIS-ICX-067 — Exploration Axis Compiler
**Purpose:** translate Freedom Zones into explicit variation axes without selecting candidate counts/seeds/providers.
**Benefit:** diversity is intentional rather than random prompt noise.
**Status:** PROPOSED_S04.

## IRIS-ICX-068 — Protected Anchor Propagation
**Purpose:** ensure identity/brand/product anchors are carried through every relevant operation slice.
**Benefit:** reduces cross-stage identity drift.
**Status:** PROPOSED_S04.

## IRIS-ICX-069 — Execution Gap Matrix
**Purpose:** structured gap model for missing capability, translation loss, evidence path and semantic-type support.
**Benefit:** failures become routable engineering facts rather than vague “provider could not do it”.
**Status:** PROPOSED_S04.

## IRIS-ICX-070 — Semantic Side-Effect Boundary
**Purpose:** distinguish desired external delivery intent from actual authorization/execution.
**Benefit:** preserves M02/M59 side-effect safety and reconciliation.
**Status:** PROPOSED_S04.

## IRIS-ICX-071 — Intent Slice Cache Passport
**Purpose:** prove reuse safety for compact downstream execution slices using semantic/compiler fingerprints.
**Benefit:** avoids repeated prompt/context construction and reduces LLM cost.
**Status:** PROPOSED_S04.

## IRIS-ICX-072 — Capability-Neutral Retry Intent
**Purpose:** preserve retry/repair semantic goals while allowing later modules to change provider/strategy.
**Benefit:** failed providers do not force semantic rewrite or duplicated user prompting.
**Status:** PROPOSED_S04.

## S04 technology disposition

Continue planning with `IRIS-ICX-055..072`. No S04 candidate is frozen or claimed novel yet. Final Technology Review must assess consolidation and prior art across ICX-001..072.
