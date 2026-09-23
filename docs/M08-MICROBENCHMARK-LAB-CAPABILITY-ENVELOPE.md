# M08 Microbenchmark Lab & Capability Envelope

Status: implementation for `IRIS-WO-0012`, contract `m08-contract-v1.0`
Package: `iris_microbenchmark/`
Authority namespace: `hardware-capability`

M08 records empirical performance evidence for one exact M07 hardware/runtime binding. It describes bounded benchmark protocols, immutable raw results, capability envelopes, performance fingerprints, drift, calibration, aging and invalidation. It does not execute a provider, schedule production work, or decide whether an asset or release is good enough.

## Authority boundaries

| Owner | Authority retained outside M08 |
| --- | --- |
| M01 | Creative quality, evaluator and promotion authority |
| M02 | Project/build, ExecutionPlan and release authority |
| M03 | Creative intent, constraints and overrides |
| M04 | Provider-neutral structured production representation |
| M05 | Persistent Asset/Persona DNA |
| M06 | Production state and reproducibility |
| M07 | Hardware discovery and Hardware Genome truth |
| M08 | Bounded benchmark evidence, capability envelopes, fingerprints/drift and calibration/freshness/invalidation |
| M09+ | Leases, residency, execution planning, lifecycle, placement, provider workflows, evaluation, rights/security, storage, observability, orchestration and release acceptance |
| M16 | The only concrete provider/workflow compiler |

M08 does not create quality scores, downgrade canonical quality, mint leases, select placement, predict production OOM or thermal behavior, schedule rechecks, diagnose hardware health causally, store or delete assets, or make M60 release decisions. Consumers receive evidence and qualification states; their policies remain external.

## Package and public surface

The package exports its declared public API through `iris_microbenchmark.__all__`; each module also declares `__all__`. Records are frozen dataclasses with closed enums and explicit versions. Inputs that are persisted or hashed contain inert JSON-compatible values only.

| Module | Public concepts |
| --- | --- |
| `base`, `versions`, `limits`, `errors`, `enums` | Immutable record coercion, canonical JSON/SHA-256, strict identifiers and versions, closed vocabularies, typed failures and configurable hard ceilings |
| `provenance` | Exact M07 Genome or named-projection binding, evidence purpose, execution context, external references, consumer projections and privacy-scoped provenance export digests |
| `protocols` | Safety budgets, metric semantics, authorization/security receipts, automation origin, immutable protocols, protocol admission and first-run batch-budget validation |
| `probes` | Deterministic fixture manifests, declaration-only backend capsules, generic probes and separate image/video/3D/audio/transfer probe descriptors |
| `evidence` | Raw samples, independent correctness evidence, uncertainty, interference/contamination, cancellation/abort and immutable benchmark results |
| `envelopes` | Demonstrated/conservative/unknown/unsupported/invalidated dimensions, bounded-search traces, memory/concurrency/sustainability evidence and requirement qualification |
| `fingerprints` | Purpose-qualified privacy projections, named baselines and explicit promotion/supersession, metric noise guards, non-causal drift and authorization-gated recheck decisions |
| `calibration` | Derived calibration lineage, aging/freshness, append-only scoped invalidation, monotonic timing qualification and explicitly non-normative named-reference normalization |
| `schema`, `serialization`, `migration` | External schema capability negotiation, closed deterministic JSON decoding, immutable versioned documents and loss-accounted immutable extension migration |
| `contracts` | Deterministic acceptance evidence bundle binding exact protocol, fixture, probe/result, M07, envelope, calibration and freshness references while returning `EVIDENCE_ONLY` |
| `families`, `invariants` | Frozen 40-surface, 15-component and 330-invariant catalogs with executable focused-test targets |

The implementation uses only the Python standard library at runtime. No physical benchmark adapter, provider/model SDK, GPU runtime, database, CAS or persistence backend is installed by this package.

## Measurement and safety semantics

1. A caller supplies a versioned protocol, exact M07 binding and active authorization receipt before an admission record can be returned.
2. The protocol fixes domain, operation family, metrics, clock source, aggregation, warmup semantics, cancellation route, interference policy and bounded budget.
3. The result binds the exact protocol version and M07 context. Correctness must pass before a result can be `VALID`; raw samples, uncertainty, interference and abort evidence remain immutable.
4. First-run protocols are individually bounded and `validate_first_run_batch` caps their cumulative wall-clock budget. Stress/destructive protocols are rejected; first-run sustained protocols are rejected.
5. Unknown telemetry, contamination, cancellation, thermal/resource abort, unsupported, partial and stale states remain distinct. None can be silently promoted to positive capability evidence.

The default local ceilings include 15 seconds per first-run protocol, 60 seconds per first-run batch, 20,000 iterations, 256 MiB host/device allocation, eight-way concurrency, one retry, 64 boundary-search attempts, 4,000,000 inline payload bytes, 2,000 raw samples per result, 2,048 fixtures, 4,096 probes, 20,000 invalidation nodes and 40,000 invalidation edges. Callers may tighten these ceilings but may not exceed the hard ceilings in `limits.py`. A zero device-allocation budget is valid for CPU-only subjects.

The semantic kernel does not launch work. `BackendAdapterCapsule` declares backend mechanics only and contains no execute/schedule/allocate method. External adapters remain deferred and must enforce the admitted protocol budgets before any measurement occurs.

## Multimodal probes

Fixtures are content-addressed and distinguish deterministic synthetic data from explicitly licensed public fixtures. Probes never require private user media, microphone capture or speaker playback. The bank separates:

- image codec, color model, dimensions, channels, type and direction;
- video codec/container, encode versus decode, software versus hardware path, profile, bit depth, chroma and bounded stream/frame/GOP counts;
- 3D buffer/texture/dispatch primitives, with no arbitrary-scene FPS or renderer-fitness claim;
- audio sample rate, channels, format, bounded frames and numeric correctness contracts;
- host/device/peer transfer direction, exact peer subjects, payload size, synchronization and memory semantics.

Backend fallback is a distinct probe/backend identity; results from different adapters cannot be merged by changing a label. Adapter identity/version is included in the exact probe record digest in acceptance evidence.

## Capability envelope

Envelopes keep every dimension independent and retain exact source result IDs. `DEMONSTRATED` requires valid direct evidence; `CONSERVATIVE_BOUND` requires multiple sources, a nonzero declared margin and either in-range interpolation or a direction-aware margin calculation. `EXTRAPOLATION` is rejected. Higher-is-better margins lower the measured lower bound; lower-is-better margins expand the measured upper bound. Missing dimensions remain unknown.

Boundary search records ordered attempts, elapsed time, workload size, observed allocation, success/failure/abort/unsupported outcomes and exact abort references. Search inherits a protocol budget and stops at its attempt, wall-clock and allocation ceilings. Abort/unsupported outcomes are terminal. Memory, concurrency and sustainability records are observations; they cannot become leases, placement decisions, thermal guarantees or production limits. `SUSTAINED_OBSERVED` requires at least a 60-second observation plus thermal context; burst evidence cannot exceed five seconds.

Consumer qualification returns `SATISFIED`, `UNSATISFIED`, `UNKNOWN` or `INCOMPARABLE` with reasons. Stale, invalidated, superseded and unknown freshness cannot satisfy positive qualification. Synthetic-only evidence cannot satisfy a physical-evidence requirement.

## Fingerprints, drift and calibration

Fingerprints bind exact result identities/digests, protocol versions, metric semantics, projection and purpose. Included context values are stored only as per-axis digests; unselected context axes are recorded as excluded. Public/synthetic projections cannot expose stable subject tokens, local projections require an opaque pseudonym, and sensitive projections are rejected.

Comparisons require compatible protocol and projection semantics, exact metric version/unit and a per-metric sample/noise guard. Context changes require explicitly allowed delta references. Binding changes fail closed unless both cross-subject and cross-runtime comparability are explicitly granted. Variance drift compares squared dispersion; context attribution stays correlational. Baseline replacement has a receipt that names the exact superseded baseline. Recheck evaluation never schedules work and still requires benchmark authorization.

Raw results are never rewritten. Calibration creates a derived record binding source result, raw digest, calibration identity/version, output and lineage digest. Freshness distinguishes `CURRENT`, `AGING`, `STALE`, `INVALIDATED`, `SUPERSEDED` and `UNKNOWN_FRESHNESS`. Invalidation events are attributable, reasoned, append-only and scoped; global invalidation needs explicit scope evidence. The graph is acyclic, bounded, and propagated deterministically. Recalibration creates another derived lineage. Named-reference normalization is not a universal hardware score.

## Schema, migration and acceptance bundle

Canonical serialization sorts object keys, normalizes Unicode, rejects non-finite values, duplicate JSON keys and reserved-marker collisions, enforces depth/item/byte limits, and decodes only exact registered M08 dataclass/enum tags. Document digests cover schema, record, extensions, timestamp and parent digest. Unknown required extension semantics fail closed.

Migration changes immutable documents; it does not mutate the source record. Plans bind the exact source digest and schema, preserve the canonical schema identity, classify compatibility, account for preservation/loss/defaults and require explicit authorization. Receipt verification recomputes the exact extension transformation and lineage. Dropping or renaming required semantics is rejected.

The acceptance bundle binds protocol and fixture record digests, full probe/result digests, exact M07 binding digest, envelopes, calibration artifacts and derived calibration lineage, and explicit freshness state for every included evidence artifact. A missing assessment is recorded as `UNKNOWN_FRESHNESS`. The bundle's fixed decision is `EVIDENCE_ONLY`; M60 remains the release authority.

## Frozen implementation and proof map

- **40/40 technology surfaces:** BPF, SBG, EPB, ICD, AEG, CMF, UQF, FRB, MPB, COG, TPE, MEE, GPK, APK, DFM, BAC, CEF, CBD, BSE, MEM, CCM, SCM, ECC, ELF, PFF, DED, BLR, RTE, NGF, DAG, PFP, DCP, CAF, EAL, IAG, RCF, TCB, FDF, FPE and NNF.
- **15/15 absorbed components:** Benchmark Authorization Receipt; Metric Semantics Registry; Measurement Clock Descriptor; Envelope Invalidation Dependency Map; Evidence Consumer Projection Descriptor; Evidence Purpose Descriptor; Execution Context Descriptor; Requirement Qualification Handshake; External Invalidation Reference; Authority Namespace Descriptor; Provenance Export Digest; Security Authorization Reference; Automation Origin Descriptor; External Schema Projection; Acceptance Evidence Bundle.
- **330/330 hard invariants:** `scripts/validate_m08_invariants.py` parses the frozen planning source, checks exact contiguous numbering and section binding, verifies catalogs and resolves every invariant, surface and component proof target to an existing focused test method.
- **Boundary firewall:** `scripts/validate_m08_boundaries.py` rejects provider/GPU/DCC, shell, network, database and downstream-authority imports/calls, arbitrary code execution/I/O and M09+ authority symbols.

Focused suites are `tests/test_m08_protocol_safety.py`, `tests/test_m08_probes.py`, `tests/test_m08_envelopes.py`, `tests/test_m08_fingerprints.py`, `tests/test_m08_calibration.py`, `tests/test_m08_schema_migration.py` and `tests/test_m08_harness.py`. Shared test constructors are in `tests/m08_support.py`.

## Synthetic profile harness and deferred ports

`examples/m08_domain_neutral_profiles.py` builds seven deterministic profiles, including CPU-only, a synthetic 8 GB device declaration, bounded concurrency, observed interference and unknown telemetry. Every result is tagged as synthetic semantic evidence; `physical_measurements_performed` is false. The harness does not allocate the declared device capacity, start an adapter or claim physical performance.

Deferred ports are live host/device timing adapters, vendor codec/graphics/audio adapters, OS and driver telemetry, physical calibration sources, persistence/CAS, provider workflows, production resource control, quality judges, rights/security engines and release decisions. Synthetic profiles validate software semantics only.
