# M03 — Final Technology Review

Status: `APPROVED_FOR_FORWARD_COMPATIBILITY`
Scope: `IRIS-ICX-001..090`
Module: `M03 Creative Brief, Intent & Constraint Compiler`
Review basis head: `c7c58c79da958a6dbfb78225031f7ed7c597ad9c`

## Executive verdict

The M03 technology registry is strong enough to proceed, but the 90 candidate names are **not** 90 independent technologies and are not novelty/patent claims.

The review consolidates them into a smaller set of contract-worthy technology families, marks generic industry patterns as references rather than proprietary inventions, and retains two deliberately speculative metrics as research-only.

The distinguishing IRIS value is the **composition**: immutable creative-intent semantics + first-class negative constraints + quality-contract compilation into M01 + provider-neutral execution intent + semantic-loss receipts + governed overrides/versioning + minimum-sufficient slices/fingerprints across the whole chain.

## External prior-art/reference scan

This is an architectural prior-art scan, not legal patentability advice.

### Structural schema validation
JSON Schema 2020-12 already provides a standard vocabulary for structural JSON validation. M03 should interoperate with or borrow structural-validation patterns where useful rather than market schema validation itself as proprietary.

Reference:
- JSON Schema specification / Validation vocabulary, Draft 2020-12.

### Graph/data constraints
W3C SHACL already defines constraints over RDF graphs using shapes, cardinality, datatype and extensible constraint mechanisms.

Implication:
- ICX constraint structures are not novel merely because they express typed constraints.
- IRIS differentiation is creative/media semantics, authority/provenance, negative-intent preservation, slicing, quality/execution compilation and cross-modal lineage.

### Policy engines
OPA/Rego already provides declarative policy evaluation over structured data.
Cedar already provides policy-based permit/forbid decisions with explicit scope and conditions, separate from application logic.

Implication:
- `Authority Policy Graph`, condition evaluation and permit/forbid-like semantics should be treated as domain-specific governance design, not a claim that IRIS invented policy languages.
- A later implementation MAY adapter-integrate a proven policy/expression engine, but the frozen M03 semantic contract must not depend on Rego/Cedar syntax.

### Safe expressions
CEL is an embedded, portable, safe expression language designed for fast repeated evaluation after compilation.

Implication:
- ICX conditional predicates need not invent a Turing-complete expression language.
- M03 canonical predicates remain bounded typed data. CEL-like engines are implementation candidates behind an adapter if later profiling justifies them.

### Provenance
W3C PROV/PROV-O already standardizes interoperable provenance concepts and derivation relationships.

Implication:
- IRIS provenance capsules/graphs should be exportable/mappable to general provenance standards where practical.
- The proprietary value is not generic “provenance exists”, but its binding to creative intent, constraint/quality/execution compilation, stale-context invalidation and selective slices.

### Three-way merge
Three-way merge and immutable revision history are established version-control patterns.

Implication:
- ICX-080 is an IRIS semantic application of a known pattern, not a standalone novel algorithm claim.

## Consolidated contract-worthy technology families

### F-M03-01 — Intent Semantic Core
Absorbs primarily:
`ICX-001,002,003,004,007,013,016`.

Keeps:
- raw/canonical twin;
- typed Intent Statements;
- origin/authority/confidence separation;
- Freedom Zones;
- multilingual anchors;
- human-meaning preservation.

Disposition: `ACCEPT_FOR_FREEZE`.

### F-M03-02 — Ambiguity & Clarification Core
Absorbs:
`ICX-005,006,082`.

Keeps consequence-typed ambiguity + minimum-question prioritization.

`ICX-014 Semantic Entropy Radar` remains `RESEARCH_ONLY` until empirically calibrated.

Disposition: `ACCEPT_WITH_RESEARCH_SPLIT`.

### F-M03-03 — Minimum Sufficient Semantic Slice Fabric
Consolidates:
`ICX-008,029,062,087`.

One generic slice contract with typed projections:
- intent;
- constraint;
- execution;
- conflict.

Disposition: `ACCEPT_CONSOLIDATED`.

### F-M03-04 — Semantic Fingerprint, Delta & Reuse Fabric
Consolidates:
`ICX-009,011,015,028,045,046,054,065,066,071,083,088,090`.

One versioned family for:
- semantic fingerprints;
- change/delta classification;
- freshness;
- reuse passports;
- source→compiled cascade binding.

Disposition: `ACCEPT_CONSOLIDATED`.

### F-M03-05 — Constraint Semantic Core
Consolidates:
`ICX-017,019,020,021,025,026,027,030,036`.

Keeps polarity/strength orthogonality, scope/facets, canonical normal form, conditions, tolerance, cross-modal binding, coverage and immutable bundles.

Disposition: `ACCEPT_FOR_FREEZE`.

### F-M03-06 — Negative / Protected Intent Integrity
Consolidates:
`ICX-018,023,024,032`.

Keeps first-class negative intent, faceted anti-reference, protected semantic zones and end-to-end negative leakage detection.

Disposition: `ACCEPT_CONSOLIDATED`.

### F-M03-07 — Semantic Admission Shield
Absorbs:
`ICX-035,061` plus relevant S01 provenance rules.

Keeps untrusted/retrieved/generated text from self-promoting into canonical intent/constraints.

Disposition: `ACCEPT_FOR_FREEZE`.

### F-M03-08 — M01 Fidelity Compilation Bridge
Consolidates:
`ICX-037,038,039,040,041,043,044,047,049,050,051`.

Keeps:
- non-authoritative Fidelity Contract Spec;
- profile capability matching;
- gap detection;
- M01 evaluator-authority firewall;
- canonical round-trip seal;
- multi-contract composition;
- typed strict references/zones/human-review obligations.

Disposition: `ACCEPT_FOR_FREEZE`.

### F-M03-09 — No-Downgrade Quality Shield
Consolidates duplicate:
`ICX-042 + ICX-052`.

Rule:
hardware/provider scarcity changes execution strategy, never the requested QualityClass.

Disposition: `ACCEPT_MERGED`.

### F-M03-10 — Explainability & Provenance Graph
Consolidates:
`ICX-012,033,039(trace projection),053,063,064`.

One canonical explanation/provenance graph with compact/referenceable projections.

Disposition: `ACCEPT_CONSOLIDATED`.

### F-M03-11 — Provider-Neutral Execution Intent Core
Consolidates:
`ICX-055,056,057,067,068`.

Keeps Execution Intent Bundle, Capability Demands, Semantic Mutation Envelope, exploration axes and protected-anchor propagation.

Disposition: `ACCEPT_FOR_FREEZE`.

### F-M03-12 — Semantic Loss & Provider Translation Integrity
Consolidates:
`ICX-058,059,060,069`.

Keeps per-obligation semantic-loss classes, translation receipts, provider drift/gap reporting.

ICX-060 remains an interface until M14-M18 supply empirical provider qualification.

Disposition: `ACCEPT_WITH_FUTURE_PROVIDER_DEPENDENCY`.

### F-M03-13 — Conflict & Override Governance
Consolidates:
`ICX-022,073,074,075,076,077,081`.

Keeps explicit conflict objects, Authority Policy Graph, no-last-writer-wins, Override Receipts, safety gradient and scope split.

“Hypergraph” is an implementation option, not a frozen storage requirement.

Disposition: `ACCEPT_CONSOLIDATED`.

### F-M03-14 — Temporary Override / Semantic Debt
Consolidates:
`ICX-078,079`.

Keeps expiring override leases and Override Debt distinct from M01 QualityDebt.

Disposition: `ACCEPT_FOR_FREEZE`.

### F-M03-15 — Semantic Revision, Merge, Migration & Restoration
Consolidates:
`ICX-080,084,085,086` plus F-M03-04 freshness/version chain.

M03 supplies semantic analysis/receipts; M02 remains actual branch/variant/rollback authority.

Disposition: `ACCEPT_FOR_FREEZE`.

### F-M03-16 — Semantic Release Readiness
Absorbs:
`ICX-089`.

Readiness is a report/evidence bundle only; never replaces M01/M02/M53/M54/M59 gates.

Disposition: `ACCEPT_BOUNDARY_ONLY`.

## Boundary-only / informational candidates

### ICX-031 — Constraint Cost Signal
Retain only as provider-neutral metadata/interface. Actual cost/resource planning belongs to M07-M13.

Disposition: `BOUNDARY_ONLY`.

### ICX-070 — Semantic Side-Effect Boundary
Retain as a boundary rule. Actual side-effect/release semantics remain M02/M59.

Disposition: `BOUNDARY_ONLY`.

### ICX-072 — Capability-Neutral Retry Intent
Absorb into F-M03-11 as semantic retry/repair intent. Attempt/retry execution semantics remain M02/M11/M12.

Disposition: `MERGED_NOT_STANDALONE`.

## Research-only candidates

### ICX-014 — Semantic Entropy Radar
Potentially useful, but “entropy” risks false mathematical precision without calibrated distributions.

Disposition: `RESEARCH_ONLY_NOT_IN_FREEZE_CORE`.

### ICX-034 — Creative Elasticity Budget
Useful conceptually for over-constraint detection, but a universal scalar creativity metric would be misleading.

Disposition: `RESEARCH_ONLY_NOT_IN_FREEZE_CORE`.

The core keeps qualitative/typed Freedom Zone + coverage semantics without freezing a universal numeric score.

## Rejected approaches

The Final Technology Review rejects these design directions:
- canonical provider prompt as source of truth;
- arbitrary executable code inside canonical constraints;
- unrestricted user-authored policy expressions in the core;
- global scalar “quality” or “meaning loss” score that can hide hard failures;
- LLM confidence as authority;
- last-writer-wins conflict resolution;
- provider availability driving quality-class downgrade;
- generic provenance system invented from scratch where standard mapping suffices;
- M03-owned branch/worker/provider execution machinery;
- silent dropping of unsupported constraints/capabilities.

## External technology posture for implementation

Potential later implementation references:
- JSON Schema: structural payload validation/interchange;
- W3C PROV: provenance interoperability/export;
- OPA/Rego or Cedar: inspiration/adapter candidates for policy evaluation where appropriate;
- CEL: candidate bounded expression evaluator for explicitly admitted conditions;
- SHACL: reference pattern for graph/shape constraints.

No external engine is frozen as a mandatory M03 dependency in this review.

## Performance / token-economy findings

The highest-value M03 efficiency mechanisms are:
1. F-M03-03 Minimum Sufficient Semantic Slice Fabric;
2. F-M03-04 fingerprints/deltas/reuse passports;
3. F-M03-10 compact explanation projections;
4. F-M03-11 provider-neutral intent preserving reuse across provider changes;
5. conflict-local slices instead of replaying full project/chat history.

These should be implementation-priority invariants, not optional optimizations.

## Security findings

Must remain hard requirements:
- source authority cannot be self-asserted by retrieved/generated content;
- arbitrary executable constraints are forbidden;
- provider prompts/results cannot mutate canonical intent;
- evaluator capability stays M01-resolved;
- agent proposals cannot self-approve restricted overrides;
- stale authority/policy/context invalidates dependent semantic decisions.

## Final verdict

`APPROVED_FOR_FORWARD_COMPATIBILITY`

M03 S01-S05 are coherent after consolidation.

The Contract Freeze must refer primarily to the **16 consolidated families F-M03-01..16**, while keeping `IRIS-ICX-001..090` as the detailed design registry/history.

No M03 implementation is authorized yet.

## Sources consulted

- JSON Schema Draft 2020-12 core/validation specification.
- W3C SHACL Recommendation.
- W3C PROV-O Recommendation.
- Open Policy Agent / Rego official policy-language documentation.
- Cedar official policy-language reference.
- Common Expression Language official documentation.

These sources are architectural references/prior art only and are not dependencies unless a later Work Order explicitly admits them.
