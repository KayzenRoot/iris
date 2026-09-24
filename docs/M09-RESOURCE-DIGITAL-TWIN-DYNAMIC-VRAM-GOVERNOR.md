# M09 Resource Digital Twin & Dynamic VRAM Governor

Contract: `m09-contract-v1.0`  
Package: `iris_resource_twin/`  
Schema: `iris-resource-twin/1.0.0`  
Execution model: immutable values and bounded in-memory ledgers; no hardware or provider side effects.

## Responsibility

M09 is the provider-neutral resource-state and memory-governance kernel. It records resource truth with provenance and confidence, calculates conservative capacity, tracks claims and leases, describes mobility and shape-control protocols, and keeps pressure/recovery evidence auditable. Every state change is a request or a typed evidence transition. A successful M09 result does not itself execute a copy, invoke a provider, reclaim capacity, or change a quality decision.

Unknown, stale, conflicting, unsupported, or quarantined facts stay distinct. They cannot authorize a fresh-only commitment. Synthetic fixtures remain labelled synthetic and never authorize production leases or source release.

## Package and public API

`iris_resource_twin.__all__` is the public API. The package initializer checks that each module declares its exports and rejects undefined or ambiguous public names. The API is grouped by these implementation areas:

| Area | Module | Main concepts |
| --- | --- | --- |
| Resource truth | `model.py`, `twin.py` | `ResourceIdentity`, `CapacityTruth`, `ResourceSnapshot`, `ResourceEvent`, `ResourceTwin`, reconciliation and quarantine |
| Claims and residency | `leases.py` | typed claim algebra, `LeaseBook`, reservation intent, epochs/tombstones, compatible shared residency, cooperative preemption |
| Mobility | `mobility.py` | `SpillTargetCapability`, `TransferRequest`, segmented offload transactions, prefetch intents and two-phase release authorization |
| Shape control | `shaping.py` | finite `Shape` evaluation, spatial/temporal/batch contracts, quality constraints, provider capability negotiation and feedback ledger |
| Pressure and recovery | `recovery.py` | pressure hysteresis, leak evidence, stale commitment reconciliation, cooperative release, recovery budgets, resource debt and safe-failure records |
| Schema and interchange | `schema.py`, `serialization.py`, `versioning.py`, `migration.py` | schema negotiation, deterministic canonical JSON, immutable versioned documents, migration receipts and semantic round trips |
| Catalog and qualification | `families.py`, `invariants.py`, `evidence.py`, `limits.py`, `errors.py` | frozen catalogs, proof index, deterministic evidence projection, resource bounds and typed errors |

State-changing request and event records carry a `MutationContext` with actor kind, actor/workflow reference, authorization reference, causal request, idempotency key, and (for automation) an explicit automation-origin reference. Automated grant, lease transition, residency, mobility, shape, resource-event, and recovery paths fail closed when those fields are missing. This context records attribution; it does not grant authority by itself.

## Frozen coverage

The implementation preserves the frozen catalogs exactly:

| Session | Independent technology surfaces |
| --- | ---: |
| S01 Resource Digital Twin state | 16 |
| S02 leases, reservations and residency | 16 |
| S03 mobility, spill and prefetch | 16 |
| S04 resource shaping and provider negotiation | 17 |
| S05 pressure, recovery and leak evidence | 18 |
| **Total** | **83** |

The 15 absorbed components remain cross-cutting parts of those surfaces: Resource Provenance Binder; Snapshot Consistency Seal; Lease Token & Epoch Protocol; Residency Identity Binder; Lease Authorization Binder; Commitment Idempotency Shield; Spill Encryption/Permission Binder; Transfer Idempotency Shield; Spill Wear & Endurance Evidence Port; Resource Mobility Journal; Shape Transition Ledger; Quality-Neutral Preference Channel; Shape Evidence Projection; Recovery Idempotency Shield; and Leak Trend Evidence Port.

`M09_INVARIANTS` preserves the canonical text, session, and SHA-256 fingerprint for invariants 1–514. Every invariant points to an assertion wrapper and a semantic proof target. `tests/m09_proof_claims.py` explicitly enumerates every invariant claimed by each shared semantic target. `scripts/validate_m09_invariants.py` compares the catalogs with the frozen planning sources and rejects gaps, duplicates, orphan IDs, wrong targets, or missing assertions.

## Compatibility handshakes

All FC-09-01..14 are represented in invariants 501–514 and exercised by focused proofs:

1. Requirement claims bind consumer, schema, quantity/unit, hard/soft semantics, purpose and provenance.
2. Quality-sensitive shaping requires external versioned quality constraints and explicit authority state.
3. Owner liveness remains typed external evidence with freshness and `UNKNOWN` semantics.
4. Resource identity and claims stay placement-neutral.
5. Provider control is capability-negotiated and unsupported mandatory semantics fail closed.
6. Spatial/temporal boundary descriptors are explicit and supplied by their owning domain.
7. Composite claims, grants and transfers report atomicity and per-member outcomes.
8. External quality/fitness evidence remains in its owning authority namespace.
9. Public evidence is deterministic and does not expose mutable provider-private state as truth.
10. Automated mutations preserve origin, actor/workflow, authorization, cause and stable idempotency identity.
11. M55 spill capability and cleanup references never imply physical deletion.
12. Resource events carry schema, identity, time, epoch, provenance and verification status.
13. Material effects carry explicit M06 reproducibility references.
14. Acceptance evidence binds the exact tested implementation revision, frozen proof counts, and synthetic-versus-physical status.

## Authority boundaries

| Authority | Boundary retained by M09 |
| --- | --- |
| M01 | Owns quality evaluation, evaluator and promotion decisions. M09 cannot lower thresholds. |
| M02 | Owns project/build, `ExecutionPlan` and release authority. M09 emits constraints/signals only. |
| M03 | Owns creative intent, constraints and overrides. M09 cannot rewrite protected semantics. |
| M05 | Owns persistent Asset/Persona DNA. M09 holds references and transient residency facts only. |
| M07 / M08 | Own discovery facts and empirical capability/benchmark evidence; M09 consumes references without reauthoring them. |
| M10 / M11 / M12 / M14 | Own execution planning, worker lifecycle, placement and model fitness respectively. M09 does not execute, kill, place, or judge. |
| M53 / M54 / M55 / M56 | Own permission, security, physical storage/deletion and observability aggregation. M09 records references and eligibility only. |
| M16 | Remains the only concrete provider/workflow compiler. M09 has no provider SDK or concrete workflow implementation. |

There are no imports from M05 or later implementation packages, no provider/model SDK imports, and no filesystem, shell, network, database, GPU, or arbitrary-code execution in the semantic package. `scripts/validate_m09_boundaries.py` checks those boundaries statically.

## Serialization, schemas and migration

Canonical serialization is deterministic: mapping keys are sorted; strings are NFC-normalized on write; non-finite numbers, ambiguous marker keys, normalization collisions, and unsupported value types are rejected. Deserialization requires canonical Unicode and finite numeric values. Payload size, nesting depth, item count and text length are bounded.

Documents use explicit schema descriptors and required-feature declarations. Unknown mandatory semantics fail closed. Migration produces a new immutable document plus a receipt. Receipt verification reapplies the declared actions to the exact source and compares the resulting semantic document; it does not trust a recomputed receipt digest as proof of a valid transformation. Round-trip checks compare semantic values and lineage.

## Resource and security bounds

`DEFAULT_LIMITS` applies finite defaults: 10,000 resources; 20,000 events; 1,024 claims; 10,000 leases; 4,096 transfers; 256 segments; 256 candidate shapes; 32 recovery actions; 512 evidence references; JSON depth 32; 50,000 JSON items; 8,192 text characters; 4,000,000 serialized payload bytes; and 10,000 search steps. The API permits caller-selected bounds only up to hard ceilings declared in `limits.py`.

Transfers additionally bound active bytes, per-target concurrency, retry count, segment count, and deadlines. Recovery actions and churn have finite budgets, cooldowns and idempotency rules. Lease and residency state is protected by locks for in-process atomic transitions. These are in-memory semantic controls, not persistence or cross-process coordination guarantees.

The kernel never reports capacity reclaimed from an owner request, timeout, cleanup eligibility, failed/unknown action, or synthetic transfer. Fresh reported resource truth is required to verify a recovery result. Source residency is released only after full digest/length verification and a fresh matching destination snapshot.

## Seven synthetic acceptance profiles

`examples/m09_resource_twin_profiles.py` emits seven deterministic, domain-neutral fixtures: CPU-only host; 8 GiB VRAM; 8 GiB VRAM with protected headroom; 16 GiB VRAM; 24 GiB VRAM; 8 GiB with unknown telemetry; and 8 GiB with conflicting observations. The harness asserts that unknown/conflicting truth cannot authorize a commitment, that 8 GiB is a supported first-class class, and that no physical measurement occurred. It does not query the host or hardware.

## Validation commands

The focused test command is:

```powershell
python -m unittest discover -s tests -p "test_m09_*.py"
```

Required qualification also includes compilation of package/tests/examples, `python scripts/validate_m09_invariants.py`, `python scripts/validate_m09_boundaries.py`, `python scripts/validate_governance.py`, the complete `python -m unittest discover -s tests -p "test_*.py"` suite, available lint/static checks, the seven-profile harness, and exact-head GitHub Governance. The Evidence Bundle records the measured revision and each result; a result is not inferred from this command list.

## Deferred integrations and risks

Real telemetry adapters, physical allocation/copy/readback, M55 storage and deletion, M53/M54 permission/security decisions, M11 worker lifecycle, M12 placement, M10 planning, M14 fitness, M01 quality judging, persistent storage/CAS, cross-process locking, and concrete provider execution remain deferred to their owning modules. Synthetic profiles establish deterministic semantic behavior only; they are not physical hardware qualification.
