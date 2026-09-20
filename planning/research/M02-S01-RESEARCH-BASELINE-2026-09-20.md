# M02 S01 Research Baseline — 2026-09-20

Status: `RESEARCH_COMPLETE_FOR_S01`

## Purpose
Identify proven patterns relevant to IRIS project/production identity and lifecycle without importing another product's architecture wholesale.

## Sources and implications

### RFC 9562 / UUIDv7
RFC 9562 standardizes UUIDv7 as a Unix-epoch time-ordered UUID. IRIS can use UUIDv7 as a default decentralized semantic/runtime identity while keeping timestamps non-authoritative for causal ordering.

Source: RFC Editor, RFC 9562.

### Bazel
Bazel models declared dependencies as a graph, generates an action graph and uses action keys/cache to avoid rebuilding unchanged work. Relevant to M02 because IRIS will need explicit declared dependencies, impact analysis and incremental materialization. The media-production graph cannot copy Bazel literally because IRIS also handles stochastic generation, human review and quality evidence.

Sources: Bazel Concepts / Dependencies / Glossary.

### Nix
Nix derivations describe reproducible build processes from explicit inputs and store results immutably. Relevant to immutable revision identity, reproducibility receipts and later CAS/cache semantics. IRIS must support reproducibility classes because many generative-media paths are not perfectly deterministic.

Source: official NixOS wiki/reference material on derivations and store.

### Temporal
Temporal provides durable workflow execution with persistent workflow history and resume after failures. Relevant to IRIS production continuation and retry semantics. S01 adopts the durable-history principle, not a decision to depend on Temporal.

Source: Temporal official documentation.

### Dagster
Dagster treats persistent assets and their dependencies as primary abstractions, with lineage, checks and reconciliation. Relevant because IRIS should reason about produced assets/materializations, not merely transient tasks.

Source: Dagster official docs on assets and orchestration.

### OpenUSD
OpenUSD composes scene description through references, payloads, variants and other arcs, with dependency tracking/change processing. Relevant to later non-destructive media variants, lightweight interfaces and scene/asset composition. USD remains a domain provider/interchange format, not IRIS universal identity authority.

Source: OpenUSD official composition documentation.

## Research conclusion

S01 should combine:
- UUIDv7-style decentralized semantic identity;
- Git/Nix-style immutable history/content separation;
- Temporal-style durable lifecycle history;
- Dagster-style asset/materialization thinking;
- Bazel-style explicit causal dependencies for later S02/S04;
- OpenUSD-style non-destructive variant/composition ideas for later S03.

The IRIS core must remain provider-neutral and must not hard-depend on these products merely to obtain their architectural lessons.


# S02 Research Addendum — Production Graph dependencies

## Bazel
Bazel documentation distinguishes actual from declared dependencies and describes its dependency graph as a DAG. Its extension model also separates analysis from execution: rules declare actions/outputs before execution. IRIS adopts the explicit-dependency discipline and logical-vs-execution separation, while adding media/quality/provenance semantics.

Sources:
- https://bazel.build/versions/8.1.0/concepts/dependencies
- https://bazel.build/extending/concepts

## Ninja
Ninja distinguishes explicit, implicit, order-only and validation dependencies and supports dynamically discovered dependencies through dyndep. IRIS uses this as evidence that dependency kinds materially affect rebuild semantics, then generalizes the concept to production facets such as quality/rights/provenance.

Source:
- https://ninja-build.org/manual.html

## OpenUSD
OpenUSD Pcp retains dependencies discovered during composition, uses them to propagate changes/invalidate cached computations, and supports change processing/namespace editing. USD documentation also recommends marking downstream clients dirty and deferring updates until necessary. IRIS adopts these principles for selective production invalidation, not USD's scene-specific graph as the universal core.

Sources:
- https://openusd.org/dev/api/pcp_page_front.html
- https://openusd.org/dev/glossary.html
- https://openusd.org/dev/api/dependencies_8h.html

## Dagster
Dagster emphasizes asset-centric orchestration with lineage and explicit dependencies. This reinforces IRIS treating persistent materializations/artifacts as first-class production results rather than viewing the system only as transient tasks.

Source:
- https://docs.dagster.io/

## DVC
DVC pipelines explicitly declare dependencies and outputs and derive a DAG used to decide which stages need rerunning. IRIS adopts the explicit deps/outs discipline but requires finer semantic/facet slices because a media project is often too coarse to invalidate at whole-file granularity.

Source:
- https://dvc.org/

## Temporal
Temporal's durable workflow history remains relevant to later execution/resume semantics. S02 deliberately keeps execution history separate from the logical Production Graph, so IRIS can use durable workflow engines without making their workflow model the product's canonical graph.

Source:
- https://docs.temporal.io/


# S03 Research Addendum — Branches, variants, snapshots and rollback

## Git
Git stores commits as snapshots and treats a branch as a lightweight movable pointer/reference to a commit. IRIS adopts this useful separation between mutable branch refs and immutable history, but media payloads/revisions may live in IRIS CAS rather than Git.

Sources:
- https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell
- https://git-scm.com/book/en/v2/Git-Internals-Git-References

## OpenUSD VariantSets
OpenUSD VariantSets package discrete alternatives and allow downstream selection to non-destructively compose one variant. IRIS generalizes this idea into typed cross-domain Variant Sets with compatibility constraints and lazy materialization.

Sources:
- https://openusd.org/dev/glossary.html
- https://openusd.org/dev/api/class_usd_variant_set.html

## Perforce Streams
Perforce Streams model explicit parent/child development lines and managed propagation/merging and are widely positioned for concurrent large-project development. IRIS uses the architectural lesson that branch relationships and flow policy should be explicit, while avoiding depot/path-specific coupling.

Sources:
- https://help.perforce.com/helix-core/cloud/current/Content/Cloud/admin-set-up-streams.html
- https://www.perforce.com/products/perforce-streams

## S03 conclusion
IRIS should combine:
- Git-like movable branch refs over immutable snapshots;
- USD-like non-destructive variants;
- managed branch lineage/propagation inspired by large-project VCS;
- IRIS-specific semantic merge, quality/rights conflict types, CAS structural sharing and external-side-effect rollback fencing.

No external VCS/DCC becomes IRIS's canonical production model.
