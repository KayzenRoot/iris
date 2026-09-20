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
