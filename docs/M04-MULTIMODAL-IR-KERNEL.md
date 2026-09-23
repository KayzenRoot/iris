# M04 Multimodal IR / Scene IR Kernel

`iris_multimodal_ir` is IRIS's provider-neutral, runtime-neutral representation kernel for structured production meaning. It stores authored semantics and explicit derived evidence. It does not execute production workflows or assume authority held by another IRIS module.

The implementation targets the frozen `m04-contract-v1.0` contract. Contract, schema, transport, validator, and lowering versions are explicit in `iris_multimodal_ir.versions`:

| Version | Value |
| --- | --- |
| Contract | `m04-contract-v1.0` |
| Core schema | `iris-m04-core-v1` |
| Transport | `iris-m04-json-v1` |
| Validator | `iris-m04-validator-v1` |
| Lowering | `iris-m04-lowering-v1` |

## Architecture and public API

The package exposes its intentional public surface through `iris_multimodal_ir.__all__`.

| Module | Public concepts |
| --- | --- |
| `identity.py`, `provenance.py` | Stable document/node/revision refs, semantic refs, opaque external/DNA/resource identities, traceability and fact traces |
| `graph.py`, `character.py` | `MultimodalIRDocument`, immutable `IRRevision`, `IRDocumentEnvelope`, scenes/entities/assets/characters/geometry/collections, fragments, prototypes, instances, containment and semantic relationship graphs, composition, skeletons, skin, morphs and attachment ports |
| `resources.py` | Interface capsules and ports, payload descriptors, resource requirements, deferred resource refs and texture resources |
| `schema.py` | Schema families/manifests, facets, dialects, explicit extensions and directional compatibility declarations |
| `spatial.py` | Typed quantities and units, spatial references, coordinate frames, authored transform chains, derived transforms, conversion receipts, camera and lighting semantics |
| `materials.py` | Typed material nodes, ports, connections, terminals, bindings, texture refs, color values/pipelines and conversion receipts |
| `temporal.py`, `media.py` | Rational time bases, time ranges, curves, motion, audio refs, music structure, local narrative projections, timeline/shot/sequence representations and synchronization relations |
| `lowering.py` | Capability manifests, semantic target profiles, legality findings, declarative lowering plans/rules, loss receipts, translation receipts and semantic capability debt |
| `validation.py`, `migration.py` | Deterministic validation profiles/findings/reports and immutable schema migration plans/receipts |
| `roundtrip.py` | Equivalence profiles, precomputed semantic witnesses, round-trip contracts/differences/receipts |
| `context.py` | Structural/subgraph/interface fingerprints, semantic deltas, IR/temporal/capability slices and canonical slice records |
| `serialization.py`, `versions.py` | Canonical JSON bytes/digests and versioned envelope transport |
| `readiness.py`, `limits.py`, `errors.py` | Evidence-only release-readiness report, explicit complexity limits and typed failures |

All canonical records are immutable data objects. Names, display paths and resource locations are descriptive fields; identity is carried by typed refs. Resource payload bytes remain outside the IR. The package adds no runtime dependency beyond Python's standard library and IRIS's existing public `iris_intent` value types used at the M03 boundary.

## Frozen concept and invariant coverage

`FROZEN_INVARIANT_PROOFS` maps all 80 numbered hard invariants to a family, proof target, and unique test ID (`test_m04_invariant_01` through `test_m04_invariant_80`). `validate_invariant_proof_index()` checks that all 20 families and all 80 proof IDs are represented.

| Family | Implemented concepts |
| --- | --- |
| `F-M04-01` | Semantic document/revision/node model and separate containment/transform versus relationship graphs |
| `F-M04-02` | M03/policy provenance, M01 obligation refs, and protected intent/quality authority boundaries |
| `F-M04-03` | Interface/payload/resource refs and metadata inspection without payload loading |
| `F-M04-04` | Explicit schema/facet/extension identities and unknown-field policy |
| `F-M04-05` | Character structures and opaque M05 identity/DNA refs |
| `F-M04-06` | Immutable fragments/prototypes, scoped instance overrides and explicit composition precedence |
| `F-M04-07` | Canonical/derived separation, localized record deltas and minimum-sufficient slices |
| `F-M04-08` | Unit-safe quantities, coordinate frames, transforms and conversion evidence |
| `F-M04-09` | Provider-neutral camera optics and explicit projection gaps/extensions |
| `F-M04-10` | Typed physical lighting and classified artistic controls |
| `F-M04-11` | Typed material graph, texture references, color semantics and preview/final obligations |
| `F-M04-12` | Rational time, typed motion targets, temporal layers and conversion receipts |
| `F-M04-13` | Audio representation and external media/voice identity refs |
| `F-M04-14` | Structural music representation independent of MIDI/DAW identity |
| `F-M04-15` | Local narrative projection, portable timeline and bounded sync relations |
| `F-M04-16` | Read-only representation capability and semantic legality analysis |
| `F-M04-17` | Traceable M03-to-M04 lowering, explicit loss rules and the M16 compiler boundary |
| `F-M04-18` | Multi-target semantic capability debt separated from M01 quality debt |
| `F-M04-19` | Canonical envelope, deterministic validation, schema versions and immutable migration |
| `F-M04-20` | Semantic round-trip witnesses and evidence-only readiness |

The focused suite uses one named test for each invariant. Tests also exercise the contract's acceptance paths for graph/composition, resources/character, spatial/camera/light, material/color, temporal/motion, audio/music/narrative, capability/lowering, schema/migration, serialization, round-trip and closed-runtime boundaries.

## Authority boundaries

- **M01** remains the quality, evaluator, promotion and `QualityDebt` authority. M04 stores quality-obligation refs but has no quality class, score, judge, or promotion operation.
- **M02** remains the project/build/history/`ExecutionPlan`/release authority. M04 revisions do not encode branch, build, release or execution-plan topology.
- **M03** remains the creative-intent, constraint and override authority. `lower_m03_bundle` reads the source bundle, requires traceability for correctness-relevant refs, emits a receipt, and does not edit the bundle or weaken mandatory/protected semantics.
- **M04** owns only provider-neutral structured production representation and declarative semantic lowering.
- **M05** owns persistent Asset/Persona DNA content and drift policy. M04 carries opaque, versioned refs/application points only.
- **M16** is the only concrete provider/workflow compiler. M04 target profiles and plans carry semantic schemas/capabilities; they contain no concrete provider workflow, model choice, runtime queue, DCC execution or GPU scheduling.
- M06/M55 storage, media generation, quality judges, rights/security engines, publishing and export runtimes remain outside this package.

Import-boundary checks keep provider, DCC, network, shell, database and persistence runtimes out of the semantic kernel. Schema values are decoded as declared data; the kernel does not evaluate schema-provided code.

## Serialization, validation and migration

`canonical_value`, `canonical_json`, `content_digest` and `canonical_bytes` serialize declared values deterministically. Mapping keys are sorted, fractions retain exact numerator/denominator form, and NaN/Infinity and unsupported value types fail with typed schema errors. `serialize_envelope` and `deserialize_envelope` use the separately versioned JSON transport. Core schema version and transport version are independent pins.

Validation is deterministic for the same revision, profile and validator version. It checks canonical identifiers, duplicate identities, cross references, graph constraints, extension policy and configured size/depth/fanout limits. Unknown mandatory schema elements fail closed; optional opaque preservation requires explicit policy.

`SchemaCompatibilityDeclaration` is directional. `migrate_revision` applies an admitted action plan to a new revision and returns a receipt that can recompute/verify the plan result. The source revision remains unchanged; a migration receipt is not a persistence or release record.

## Semantic round-trip

Build an `IREquivalenceProfile` and `SemanticWitnessSet` from the admitted source revision before inspecting any adapted result. `RoundTripContract` binds the source digest, witness set, equivalence profile and opaque adapter identity. `verify_round_trip` reports path-level missing, unexpected, changed/lost or explicitly tolerated semantics across the integrated records, including transform, camera, material, temporal and synchronization data.

The kernel cannot certify its own independent adapter qualification: `RoundTripReceipt.independently_qualified` must remain false. External qualification evidence can be referenced, but is not produced by this package. Parse success alone does not establish semantic equivalence.

## Context, slices and deterministic invalidation

`structural_fingerprint`, `subgraph_fingerprint` and `interface_fingerprint` expose digests for whole revisions, selected semantic graph neighborhoods, and interface-only inspection. `semantic_delta` includes path-scoped changes to multimodal records and resource digest invalidations. `build_ir_slice` carries only the requested graph neighborhood and associated canonical multimodal records/resource refs; `loaded_payload_bytes` is always zero. `build_temporal_slice` returns only points in an explicit range, and `build_capability_slice` selects declarations relevant to requested semantic refs.

These APIs make affected content and slice sizes measurable. No token-saving or latency percentage is claimed; there is no benchmark evidence for such a claim.

`IRLimits` supplies deterministic bounds for records, traversal, temporal samples and other adversarially amplifiable operations. Exceeding a bound raises `IRLimitError`; malformed canonical data raises a typed schema/integrity/admission error rather than invoking dynamic execution.

## Seven domain-neutral profiles

Run `python -m examples.m04_synthetic_profiles` from the repository root to serialize, deserialize and validate seven profiles through one revision builder and the same M04 public surface:

1. logo / brand / web visual scene;
2. product photography setup;
3. Nerim isometric game asset and scene;
4. film/commercial multi-shot sequence;
5. corporate spokesperson representation;
6. voice, narration and music production;
7. mixed visual, motion, audio and narrative scene.

The runner checks canonical round-trip, validation, common revision fields and one shared structural fingerprint. Profile IDs label authored fixture semantics; they do not select profile-specific kernel branches.

## Deferred ports and known limits

This package defines semantic records and receipts, not production integrations. Concrete adapters and independent adapter qualification, provider/DCC execution, M05 DNA storage/content, persistent CAS/database backends, external media loading, media generation, rendering, rigging/retargeting, editorial operations, real quality evaluation, rights/security engines and publishing/export remain deferred to their owning modules.

The synthetic harness is deterministic functional evidence, not a real media workload or performance benchmark. M04 readiness and lowering reports are evidence/planning artifacts only; downstream governance and independent review remain required. The implementation must be audited against the frozen acceptance contract before any checkpoint promotion or merge.
