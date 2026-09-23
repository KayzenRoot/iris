# IRIS M07 Hardware Genome and Runtime Discovery

## Purpose and authority

`iris_hardware_genome/` is the provider-neutral semantic kernel for reported hardware, runtime, capability, topology and telemetry evidence. It admits bounded, provenance-bearing facts and preserves uncertainty, scope and history. It does not execute a hardware probe by itself and does not decide what a workload should do.

The authority split is:

| Module | Authority retained by that module |
| --- | --- |
| M01 | Quality evaluation, evaluator results and promotion decisions |
| M02 | Project/build orchestration, ExecutionPlan and release |
| M03 | Creative intent, constraints and overrides |
| M04 | Provider-neutral structured production representation |
| M05 | Persistent Asset and Persona DNA |
| M06 | Explicitly declared reconstruction material and reproducibility contracts |
| M07 | Hardware and runtime observations, evidence, normalized capability and immutable snapshots |
| M16 | Concrete provider and workflow compilation |

M07 does not lower quality targets, choose devices, schedule or place work, create memory leases, mutate drivers or device state, compile provider workflows, generate media, or persist records in an external store. M07 facts are not M05 identities. M06 receives a named projection only when the exact M06 contract ID is declared as the fact's materiality source.

## Package surface

The root package exports the immutable records, closed enums, typed errors, validators and transformations from its modules. The public modules are:

- `base`, `versions`, `limits`, `errors`, `enums`
- `families`, `subjects`, `evidence`, `discovery`, `ports`
- `capabilities`, `precision`, `media`, `topology`
- `registry`, `telemetry`, `schema`, `genome`, `deltas`
- `projections`, `redaction`, `migration`, `recovery`, `validation`, `invariants`

All public modules declare `__all__`; package initialization rejects missing or ambiguous exports. Records are frozen dataclasses. Values admitted into payloads are bounded JSON data and closed M07 records/enums.

## Twenty technology surfaces

| Code | Surface | Main implementation |
| --- | --- | --- |
| HDF | Hardware Discovery Fabric | `discovery.py`, `ports.py` |
| ODG | Opaque Device Graph | `subjects.py`, `topology.py` |
| NAF | Negative Assertion Firewall | `evidence.py` |
| RSP | Runtime Substrate Passport | `subjects.py` |
| CEL | Capability Evidence Ladder | `capabilities.py` |
| BRM | Backend Relationship Matrix | `capabilities.py` |
| VSF | Version Separation Fabric | `capabilities.py` |
| DSG | Driver Skew Graph | `capabilities.py` |
| PFX | Precision Feature Lattice | `precision.py` |
| MEC | Media Engine Capability Matrix | `media.py` |
| TGE | Topology Graph Evidence | `topology.py` |
| TSL | Telemetry Semantics Ledger | `telemetry.py`, `registry.py` |
| MPF | Memory Pressure Fabric | `telemetry.py` |
| EDE | Evidence Derivation Engine | `telemetry.py` |
| SWG | Sampling Window Governor | `telemetry.py` |
| HGX | Hardware Genome Exchange | `genome.py`, `serialization.py` |
| MCD | Multidimensional Confidence Descriptor | `genome.py` |
| GDL | Genome Delta Ledger | `deltas.py` |
| RFP | Reproducibility Fingerprint Projection | `projections.py` |
| SCB | Schema Compatibility Barrier | `schema.py`, `migration.py` |

The five absorbed components are DCF (discovery conflicts), PDM (precision dimensions), CCG (capability conflicts), P2P (ordered pairwise path evidence), and TCR (thermal causality evidence). Their ownership is encoded in `families.py` and checked as part of the frozen surface catalog.

## Evidence and discovery

`HardwareSubjectRef` is an opaque subject ID with privacy-classified digest anchors. Mutable device locators and labels stay separate. `RuntimeSubjectRef` names an exact host, process, container, VM, WSL or sandbox scope. A passport retains host/process architecture separately and carries explicit visibility limitations.

Each positive `DiscoveryObservation` carries exact time, visibility, subject/runtime scope, normalized key, evidence digest, probe ID/version, source adapter ID/version, payload size and evidence strength. `UNKNOWN`, `UNAVAILABLE`, `PERMISSION_DENIED`, `UNSUPPORTED_PROBE`, `PARTIAL`, `STALE`, and `CONFLICTING` remain explicit states. `NOT_PRESENT_PROVEN` requires a capable probe, complete scope, fresh source and no truncation or permission gap. The batch's probe must be present in the exact versioned allowlist; non-declarative runtime probes also require a current permission grant bound to each observed subject and runtime.

An explicitly supplied `DiscoveryAdapterPort` returns a batch for the exact session and descriptor. M07 does not auto-import adapters, launch commands, inspect the host, access a provider SDK, or execute the adapter unless the caller explicitly invokes that port. Evidence digests establish content identity; they do not establish that a source's claim is semantically true.

## Capabilities, topology, media and telemetry

CUDA, ROCm, DirectML, Metal, CPU and portable backends are peers. A capability assertion binds one exact subject, runtime and observation; backend installation or package presence alone does not imply device operation. Evidence strength is explicit and cannot rise without new evidence. Version axes distinguish driver, runtime, toolkit, framework, loader and library. Driver-skew edges include an exact normalized compatibility observation.

Precision is represented across representation, arithmetic, reported acceleration, accumulation, conversion, framework exposure and conformance. FP8 encodings are separate. Media facts bind codec, encode/decode direction, engine, API path and reported limits. Interop facts bind both API paths and their exact device/runtime. Topology edges carry exact source evidence. Peer access is ordered, pairwise and runtime-bound. PCIe maximum link capability, negotiated link state and independently measured bandwidth are separate records; one does not imply another.

Static memory capacity is distinct from dynamic availability and pressure. Telemetry samples bind metric key, unit, source, sequence, time window, expiry and subject/runtime. Temperature names a sensor. Counter-derived rates retain their input sample IDs, interval and versioned rule; resets and regressions fail closed. Memory-pressure facts require source evidence or an explicit derivation rule. Sampling is bounded by rate, count, window and timeout and cannot escalate privilege.

## Registry, schema and immutable Genome

Every Genome captures its semantic registry snapshot. Exact core keys declare semantic type, permitted states, unit and freshness; versioned prefix rules cover structured core families; plugins use explicitly governed namespaces and cannot shadow core keys. Fact envelopes carry the exact registry version. Genome construction rejects unregistered keys, disallowed states and unit mismatches.

The core schema is `iris-m07-core-v1` at `1.0.0`; producer, schema, registry, validator, transport, fingerprint and migration versions remain separate. Readers fail closed on unknown required features and must preserve unknown optional features when the contract says so. PATCH preserves semantics, MINOR advances compatibly, and incompatible changes use a declared MAJOR migration. Migration actions are declarative JSON operations; they cannot carry executable callbacks. A migration creates a new immutable Genome, retains the exact parent ID and emits a verifiable loss receipt. A lossy migration never replaces its source.

The canonical JSON transport is `iris-m07-json-v1`. It uses a closed static registry of tags, sorted object fields and maps, normalized text, exact schema fields and bounded nesting/items/bytes. Duplicate JSON keys, unknown tags, noncanonical bytes, non-finite numbers and arbitrary object values fail closed. The SHA-256 `GenomeId` binds canonical content. Consumer projections bind a named/versioned contract, schema, facts and omission reasons. Their static fingerprint excludes dynamic telemetry while retaining the source Genome ID as separate lineage metadata.

Genome deltas carry exact base and target Genome IDs, fact/section digests, invalidations and typed change classes. Material-change events are validated against that same delta and pair of snapshots. Change classes report evidence changes; they do not prescribe scheduler, quality or release actions.

Confidence is a deterministic vector over source authority, subject binding, evidence strength, freshness, agreement, semantic completeness, visibility completeness and derivation depth. The vector is recomputed from admitted observations; caller-supplied confidence that exceeds that evidence is rejected. Conflicts require one normalized `CONFLICTING` fact plus the source observations that disagree.

Redacted advertisements retain evidence state/freshness and reference the source Genome and redaction policy. They omit raw locators/labels and cannot claim canonical-content identity. Recovery returns historical references only. A current-state claim after recovery requires a newer, complete snapshot with an observed exact hardware subject.

## Complexity and security limits

Defaults are 2,048 subjects; 50,000 observations; 20,000 capabilities and topology nodes; 80,000 topology edges; 10,000 conflicts; 20,000 telemetry samples; 256 probes; 30 seconds per probe; 2 MB probe output; 8 MB evidence and serialized payload; JSON depth 48; 100,000 JSON items; 16,384 text characters; 2,000 extension fields; 10,000 samples per telemetry window; and topology depth 128. Callers may lower limits. Records reject booleans as integer sizes, non-finite numbers, empty/duplicate IDs, unknown enum values, malformed digests, and namespace collisions.

The package boundary scan rejects provider SDK, shell, network, database and arbitrary dynamic-execution imports/calls. The scanner is `scripts/validate_m07_boundaries.py`. No hardware providers or native device probes run in the synthetic harness.

## Synthetic profiles and verification

`examples/m07_domain_neutral_profiles.py` builds seven reproducible profiles: CPU-only, 8 GiB accelerator, multiple adapters, shared plus dedicated memory, guest-visible partial topology, permission-limited/stale facts, and conflict plus stale telemetry. They are synthetic and do not describe the workstation running the tests.

Focused proof files are `tests/test_m07_discovery.py`, `test_m07_capabilities.py`, `test_m07_hardware_surfaces.py`, `test_m07_telemetry.py`, `test_m07_genome.py`, and `test_m07_authority.py`. `tests/m07_support.py` contains shared deterministic fixtures. `iris_hardware_genome/invariants.py` preserves all 235 literal frozen requirements and maps them to these focused suites; `scripts/validate_m07_invariants.py` compares the complete catalog against the planning source.

Run from the repository root:

```powershell
python scripts/validate_m07_invariants.py
python scripts/validate_m07_boundaries.py
python -m unittest discover -s tests -p "test_m07_*.py"
python examples/m07_domain_neutral_profiles.py
python -m compileall -q iris_hardware_genome tests examples scripts/validate_m07_invariants.py scripts/validate_m07_boundaries.py
python scripts/validate_governance.py
python -m unittest discover -s tests -p "test_*.py"
ruff check iris_hardware_genome tests/m07_support.py tests/test_m07_*.py examples/m07_domain_neutral_profiles.py scripts/validate_m07_invariants.py scripts/validate_m07_boundaries.py
mypy iris_hardware_genome
```

The frozen invariant statements are maintained in `planning/modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md`. This package implements the provider-neutral data/evidence contract only. Native probes, evidence-source authentication, benchmark characterization, OS scheduling, hardware mutation, physical storage, long-term persistence, and concrete provider workflows remain deferred to their owning ports/modules.
