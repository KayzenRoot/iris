# M02 — Forward Compatibility Scan

Status: `PASS_WITH_EXTENSION_PORTS`
Scope: M03–M60 known future contracts

## Purpose

Ensure M02 freezes only the universal production substrate needed now and does not steal implementation ownership from future modules.

## M03 — Creative Brief / Constraint Compiler

M03 owns:
- brief schemas;
- intent/negative constraints;
- Fidelity Contract compilation;
- provider-neutral execution intent.

M02 consumes versioned `intent_ref`, `constraint_ref`, policy and Fidelity Contract references.

**Rule:** M02 never invents M03 brief semantics.

## M04 — Multimodal IR / Scene IR

M04 owns media/scene/character/camera/material/motion/audio/narrative IR schemas.

M02 owns typed port mechanics but port semantic type is a versioned external type reference.

**Required port:** `SemanticTypeRef` / schema-version capability.

This prevents the M02 graph kernel from hardcoding visual-only types.

## M05 — Asset DNA / Cross-Modal Identity

M05 owns identity anchors, DNA schemas, mutation boundaries and compatibility.

M02 owns protected-anchor enforcement hooks for variants/merge/promotion.

**Rule:** M02 references identity-anchor policy; it does not define face/body/voice/brand DNA fields.

## M06 — Production State, Versioning & Incremental Media Build

### Overlap hazard identified

The approved master map gives M06 names that overlap M02 S03–S05.

### Ownership boundary

**M02 freezes semantic law:**
- identity and revision relationships;
- graph dependency semantics;
- branch/variant/snapshot/rollback semantics;
- build/invalidation/reuse classes;
- lifecycle/promotion/release/archive semantics.

**M06 deepens operational persistence/materialization:**
- content-addressed revision implementation;
- immutable-master persistence;
- durable dependency fingerprint indexes;
- reconstruction/reproducibility receipts;
- lineage-aware cleanup execution;
- operational rollback/reconstruction mechanisms.

M06 MUST implement/extend M02 contracts, not create a competing second state/branch/build model.

Status: **PASS_WITH_OWNERSHIP_BOUNDARY**.

## M11/M12 — Workers & Compute

M02 defines Attempt, Build Plan, side-effect/reproducibility class and continuation contracts.

M11/M12 own:
- process lifecycle;
- worker registry;
- resource leases;
- cancellation/timeouts;
- scheduling/placement;
- remote/cloud execution.

**Required port:** `ExecutionProvider / WorkerCapabilityRef`.

No PID/GPU/process implementation enters M02 kernel.

## M13 — Performance / Cache

M02 defines reuse semantics and trust classes.

M13 owns:
- actual cache architecture;
- warm model/KV/provider state;
- performance algorithms;
- eviction/locality;
- runtime profiling.

**Rule:** M13 optimization cannot weaken M02 reuse admission.

## M16/M17 — Provider Compiler / ComfyUI

M16 compiles Definition/Bound Graph + M04 IR into provider workflows.
M17 implements ComfyUI queue/runtime adaptation.

**Required ports:**
- `ProviderCompiler`;
- `DependencyObserver`;
- `MaterializationIngestor`.

Providers cannot mutate a frozen graph revision silently.

## M18 — Model supply chain

Model identity/license/qualification changes participate in M02 causal fingerprints/gates by reference.

M18 owns actual acquisition/integrity/license qualification.

## M25–M35 — 3D/DCC/Web/Game

All domain workflows compile through M02 graph/branch/snapshot contracts.

Blender/ Maya / USD / WebGPU / engine details remain adapters/domain profiles.

No DCC path/name becomes semantic identity.

## M36/M37 — Film / Temporal continuity

Shot graphs may be domain subgraphs over M02.

M37 continuity state/evidence becomes typed graph values/gates.

Episode/shot branches use M02 lineage without redefining branching.

## M39/M40/M41 — Digital Human / Voice / Music

Persona/Voice/Music DNA own identity content.

M02 protects their anchors and tracks revisions/variants.

Corporate spokesperson public release uses M02 promotion port + M39/M53 domain gate.

## M43–M47 — Narrative / Content / Ads / Brand / Localization

These modules create domain-specific:
- production profiles;
- Variant Sets;
- branch baselines;
- promotion gates;
- context dependencies.

They cannot bypass M02 immutable snapshot and promotion semantics.

## M48/M49 — Quality / Repair

M48 owns real judges/Quality Court.
M49 owns repair engines.

M02 owns:
- QualityDecision as graph/gate value;
- Repair disposition/frontier contract.

**Required port:** `RepairProvider`.

## M52 — HIVE memory/context

M02 owns Context Fingerprint contract only.
M52 owns actual retrieval, minimum sufficient context and stale-context invalidation.

HIVE remains derived memory; it does not own project state.

## M53 — Rights / Provenance / Consent

M53 provides rights/provenance/consent gate values and receipts.

M02 promotion/release/archive consumes them by typed ref.

M02 does not implement legal policy engines.

## M55 — CAS / Storage / Archive

M55 owns bytes, CAS, hot/warm/cold tiers, GC and recovery.

M02 owns semantic revision/snapshot/archive contracts.

**Required ports:**
- `ArtifactStore`;
- `SnapshotStore`;
- `ReceiptStore`.

Storage must not collapse distinct semantic artifacts merely because content bytes deduplicate.

## M57 — Agents / Autonomy

Agents may:
- propose Graph Deltas;
- request promotions;
- plan builds;
- resolve permitted non-blocking decisions.

Agents do NOT:
- mutate frozen graph history directly;
- self-approve gates outside authority;
- bypass Stop Conditions.

## M59 — Export / Publishing

M59 owns destination profiles, packaging and publishing adapters.

M02 owns Release Transaction / side-effect reconciliation semantics.

**Required port:** `DeliveryProvider`.

## M60 — Final Integration

M60 validates that all modules obey M02 semantic contracts end-to-end.

## Extension ports required by freeze

M02 must expose versioned provider-neutral abstractions/refs for:
1. SemanticType / IR schema refs;
2. Policy/Fidelity Contract refs;
3. IdentityAnchor policy refs;
4. ExecutionProvider / WorkerCapability;
5. ProviderCompiler;
6. DependencyObserver;
7. MaterializationIngestor;
8. RepairProvider;
9. Artifact/Snapshot/Receipt stores;
10. Rights/Provenance gate providers;
11. DeliveryProvider;
12. Context source/fingerprint provider.

These are contracts, not implementations.

## Hazards checked

- visual-only graph types: **avoided**;
- provider lock-in: **avoided**;
- cache = truth conflation: **avoided**;
- attempt success = acceptance: **avoided**;
- branch = variant conflation: **avoided**;
- stochastic = deterministic conflation: **avoided**;
- duplicate M06 ownership: **bounded by explicit ownership rule**;
- HIVE becoming canonical state: **avoided**;
- agent self-approval: **avoided**;
- external publish blind retry: **avoided**;
- persona identity drifting through ordinary variants: **guarded**.

## Verdict

`PASS_WITH_EXTENSION_PORTS`

Proceed to Contract Freeze Candidate.
