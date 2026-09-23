# IRIS M06 Production State Kernel

## Purpose and contract

`iris_production_state/` implements the provider-neutral operational state kernel for the frozen `m06-contract-v1.0`. It records immutable revisions and materializations, dependency and reuse evidence, reconstruction outcomes, lineage, rollback proposals, release closure, and versioned evidence-port contracts. It does not execute production workflows.

The package exposes 179 symbols through `iris_production_state.__all__`. The versioned family catalog contains 25 frozen families, the invariant catalog preserves all 150 source statements verbatim, and the port catalog contains 20 protocols. Catalog validation checks those counts and each family proof target. `tests/test_m06_invariants.py` compares the invariant text with the canonical planning source and verifies every family proof target exists in the M06 tests.

## Architecture and public surface

| Module | Main concepts |
| --- | --- |
| `base.py`, `versions.py`, `errors.py`, `limits.py` | Typed immutable records, canonical exact references, schema/version constants, strict primitives, and bounded processing errors |
| `enums.py`, `families.py`, `invariants.py`, `ports.py` | Closed contract vocabularies, the 25-family and 150-invariant catalogs, and 20 versioned evidence protocols |
| `revisions.py` | Operational revisions, digest algorithms, materializations, immutable masters, integrity/availability receipts, and migrations' source records |
| `dependencies.py` | Causal fingerprints, deltas, dependency slices, reverse indexes, impact cones, and dependency discovery |
| `regeneration.py` | Selective work decisions, M02 reuse admission, monotone frontiers, M02-bounded repair slices, and mixed reconstruction receipts |
| `reconstruction.py` | Explicit reproducibility classes, exact input manifests, divergence evidence, current-permission checks, and bounded reconstruction receipts |
| `lineage.py` | Complete lineage graphs, rollback receipts, protected cleanup closure, logical retirement, and M55 deletion authorization/completion evidence |
| `release.py` | Immutable release-state closure bound to exact M02 build, snapshot, and release transaction records |
| `migration.py`, `serialization.py`, `validation.py` | Literal data-only migration, deterministic allowlisted serialization and round trips, and kernel catalog/evidence validation |

The kernel uses Python standard-library facilities and exact records from the repository's M02 `iris_project_os` and M05 `iris_asset_dna` packages. It adds no runtime package dependency. M02 and M05 values are accepted as versioned references or their exact typed records; M06 does not take over their authorities.

## Frozen family and invariant coverage

| Contract section | Families | Invariants |
| --- | --- | --- |
| S01 revision and master state | RVF, IML, DAS, SEA, AVS | 1–30 |
| S02 dependencies and impact | CFM, MSI, HDS, ICX, RDI | 31–60 |
| S03 selective regeneration | SRE, RAP, FEX, MXR | 61–90 |
| S04 reconstruction and reproducibility | SDS, RCL, RXM, DRG, ESB, HPR | 91–120 |
| S05 lineage, rollback, cleanup, release | LRG, SGC, RRB, RSC, CRA | 121–150 |

The literal invariant inventory is sourced from `planning/modules/M06-PRODUCTION-STATE-VERSIONING-INCREMENTAL-MEDIA-BUILD.md`; family identities are checked against the frozen contract. Family tests exercise all 25 proof targets. Additional focused tests cover exact source text, versioned catalogs, authority boundaries, serialization, migrations, and resource limits.

## Authority boundaries

| Module | Preserved authority |
| --- | --- |
| M01 | Quality/evaluator evidence and promotion decisions. M06 transports evidence and never evaluates or promotes. |
| M02 | Project/build state, `BuildPlan`, `ExecutionPlan`, snapshots, lifecycle, and release transactions. M06 binds exact M02 evidence and does not create those decisions. |
| M03 | Creative intent, constraints, and overrides. M06 can bind references but does not author intent. |
| M04 | Provider-neutral structured production representation. M06 records operational state around it and does not compile provider workflows. |
| M05 | Persistent Asset/Persona DNA identity. M06 consumes exact identity references and does not mutate DNA. |
| M16 | Sole concrete provider/workflow compiler. M06 exposes versioned workflow-evidence ports only. |
| M53/M54/M55 | Current provenance/rights, security authorization, and physical storage/deletion remain external authorities. M06 records their exact receipts. |

All 20 M06 ports are versioned protocols returning requests, status, and evidence references. They do not authorize state transitions. Their domains cover hardware materiality, execution attempts, cache reuse, model/workflow revisions, domain materializations, narrative and campaign identity, quality evidence, repair outcomes, HIVE context, rights/consent, security, media storage and deletion/archive, observability, agent proposals, external contracts, publishing delivery, and system recovery. The interfaces do not implement those systems.

## Serialization, migration, and semantic round trip

Canonical transport uses `iris-m06-json-v1`. Records are serialized from a closed type registry with stable field and map ordering, normalized text, finite numeric values, and deterministic UTF-8 JSON. Deserialization rejects duplicate keys, unknown record types or fields, non-canonical values, and over-limit input. Fingerprints bind the selected record and versioned schema; digest algorithms and materialization references are explicit.

The semantic round-trip API validates M02 and M05 typed references alongside M06 records. A successful round trip must preserve the typed value and its canonical fingerprint.

Migrations use immutable input documents and an allowlisted set of data operations: rename, default, and drop at bounded JSON paths. Values are literal data; callables, expression evaluation, and runtime execution are not accepted. Each result is a separate receipt, and the original document remains unchanged.

## Dependency context, reuse, and reconstruction

Fingerprints declare materiality for every dependency dimension. Unknown materiality blocks a positive absence/reuse proof. A slice accounts for every base dimension as included or omitted with positive non-material evidence; it does not silently discard omitted dimensions. Deltas compare only compatible scopes and versions.

Reverse-index state defaults to `UNKNOWN`. `COMPLETE_FRESH` requires exact completeness evidence; stale, partial, corrupt, hidden, or unknown dependency evidence cannot prove no impact. Impact traversal has a node limit and reports an unknown frontier when that bound is reached. An impact receipt embeds its exact source index so validation can recompute the result.

Reuse admission binds an exact M02 `BuildPlan`, its reuse step and `ReuseReceipt`, the M06 candidate materialization, and verified evidence for every fingerprint dimension. Partial repair binds an exact M02 repair node and `DependencySlice`; M06 cannot widen that slice. Mixed reconstruction retains both rebuilt and reused ancestry.

Reproducibility is an explicit class. Exact-byte regeneration requires pinned workflow/model/toolchain references and positive completeness evidence for material inputs and execution dimensions. A seed alone is not proof. Retained restoration requires an exact materialization; exact-byte success binds the output materialization digest to observed digest evidence. Exact semantic-state claims bind a versioned semantic contract and result verification. Historical permission never substitutes for current M53/M54 authorization.

## Lineage, rollback, cleanup, and release

Lineage graphs bind a complete fresh graph to exact closure evidence and reject cycles. Cleanup evaluates the protected closure categories, explicit roots, active retention pins, and exact graph epoch/fingerprint. Unknown, partial, stale, or protected state is not eligible for cleanup. M06 records logical retirement and M55 authorization/completion evidence; it does not delete bytes.

Rollback targets exact M02 snapshots and produces new history instead of rewriting old masters. Release capsules bind exact M02 build/snapshot/transaction records, master integrity, dependencies, and current external authority evidence. M06 validates closure; it does not publish, release, or promote.

## Resource and execution security

`ProductionStateLimits` bounds records, references, dependencies, lineage nodes/edges, fingerprint dimensions, JSON depth/items, text, and inline payload size. Traversals and parsers fail closed or return an unknown state at their explicit limit. Exact reference types prevent implicit `latest`/`current` resolution.

The semantic package contains no `eval`/`exec`, shell, network, database, GPU, provider SDK, DCC, media-generation, or quality-judge integration. Static boundary checks scan imports and dynamic-execution calls. The synthetic harness constructs typed evidence only and does not generate media.

## Domain-neutral synthetic harness

`python -m examples.m06_domain_neutral_profiles` runs eight deterministic profiles:

1. image partial repair with dependency lineage;
2. 3D mesh/material/LOD state;
3. video mixed rebuilt and reused segments;
4. audio voice/music mix;
5. metadata dependent on canon references;
6. stochastic production with bounded reproducibility;
7. retained-materialization restoration;
8. release, archive, rollback, and cleanup state.

The profile harness verifies semantic kernel behavior across domains without selecting a provider or invoking a media tool.

## Required local gates

```powershell
python -m compileall -q iris_production_state tests examples
python -m unittest discover -s tests -p "test_m06_*.py"
python -m examples.m06_domain_neutral_profiles
python scripts/validate_governance.py
python -m unittest discover -s tests -p "test_*.py"
ruff check iris_production_state tests examples/m06_domain_neutral_profiles.py
```

The exact-head hosted Governance result is recorded separately in `.engineering/evidence/IRIS-WO-0010.json`; a local pass does not substitute for that run or independent review.
