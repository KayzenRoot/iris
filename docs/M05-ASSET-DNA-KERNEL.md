# M05 Asset DNA Kernel

`iris_asset_dna/` implements the frozen `m05-contract-v1.0` provider-neutral identity kernel. It records persistent subject identity, immutable semantic revisions, explicit identity links, governed change, compatibility and package conformance. It does not generate assets, persist data, judge quality, approve releases or execute provider workflows.

## Authority boundaries

| Authority | M05 contract |
| --- | --- |
| M01 | Owns quality, evaluator and promotion decisions. M05 readiness reports semantic conformance only. |
| M02 | Owns projects, production graphs, builds, branches, release and rollback. M05 lineage is identity lineage. |
| M03 | Owns creative intent, constraints and override semantics. M05 stores admitted identity facts and references. |
| M04 | Owns provider-neutral scene/representation IR. M05 can pin M04 revisions and projection contracts. |
| M05 | Owns stable `dna_id`, canonical identity revisions, identity lineage and explicit identity-change records. |
| M06 | Owns operational persistence, reconstruction and production versioning. M05 has no storage backend. |
| M16 | Owns concrete provider/workflow compilation. M05 exposes a ref-only projection port. |
| M30/M37/M39/M40/M41/M43/M45/M46 | Retain motion, temporal, persona/runtime, voice/music/audio, canon, campaign and brand contents. |
| M53/M54 | Retain provenance/rights/consent and security/restricted-content authority. M05 carries minimized refs. |
| M55/M58/M59/M60 | Retain storage/observability, API/recovery, export/publishing and deployment/integration authority. |

The kernel imports no neighboring IRIS authority package. Linked-domain refs are versioned, owner-qualified and revision-pinned. A linked module cannot mutate canonical M05 identity through a reference or binding.

## Identity model

`AssetDNAIdentity` supplies an opaque stable `dna_id` and subject classification. Each `DNARevision` is immutable and contains a monotonically identified revision, family and identity level, canonical traits, anchors, component refs, external DNA refs, and provenance/policy/rights refs. An `DNAEnvelope` preserves the complete revision history and pins its head. A new identity break receives a new `dna_id`; split and consolidation records retain their source histories.

Each `DNATrait` declares a versioned schema, identity criticality, mutability, polarity and one of four applicability states: `PRESENT`, `UNKNOWN`, `NOT_APPLICABLE` or `INTENTIONALLY_UNCONSTRAINED`. Canonical facts require provenance or policy reachability. Observation/evidence records remain a separate reference plane; they do not become canonical values by themselves. Unknown mandatory schemas fail closed. Unknown optional schemas require an explicit preservation policy.

Identity fingerprints hash the canonical semantic payload. Display metadata, evidence refs, revision labels and storage/location data are excluded. Fingerprint equality is evidence for analysis, never an automatic equivalence or merge decision. Path-level change surfaces and fingerprint witnesses make included and excluded material inspectable.

## Identity subdomains

- **Anchors and projection:** `IdentityAnchor` carries its authority class and explicit target ref. Canonical rebind/revoke operations require M05 authority and policy and preserve lifecycle history. `DNAProjectionContract` declares required and optional trait paths; projection cannot silently omit required paths.
- **Context slices:** `DNAInterfaceCapsule` gives a compact semantic interface. `MinimumSufficientDNASlice` includes requested traits, dependency closure, related anchors/links and only the associated provenance/policy refs. Trait, edge and graph-depth limits bound construction.
- **Families and components:** versioned profiles reuse the common identity core. Typed Character, Creature, Object, Product and Environment records preserve asymmetric/non-human forms, contextual state and product identity levels. Persistent component IDs are independent of position, display name or M04 node IDs; replacement, split and merge are explicit governed transitions.
- **Cross-modal identity:** external `LinkedDomainDNARef` values pin owner, family, version and revision. Motion, Voice and Brand link records reference domain-owned content. `SceneIdentityDNA` identifies members through stable roles and explicit substitution policy; it is not M04 SceneIR or M43 Canon truth. Bindings and obligations are explicit graph records, not production or narrative graphs.
- **Drift and mutation:** path-level typed evidence reports dimensions and uncertainty without collapsing findings into one score. Mutation proposals do not change DNA. An explicit M05 decision with authority/policy refs admits a new immutable revision. Repair/provider output cannot self-admit a mutation.
- **Lineage and compatibility:** aliases, equivalence claims, identity breaks, splits and consolidations are separate non-destructive records. Compatibility is directional and multi-axis; unknown remains indeterminate. `DNAMigrationPlan` lists preserved, transformed, dropped and defaulted paths. Loss and identity breaks are visible in a deterministic receipt.
- **Packages and imports:** package IDs/versions are distinct from subject identities. Manifests contain typed extensions, dependency declarations and rights/provenance/security refs; they contain no executable payload. Dependency closure distinguishes required and optional inputs. Import moves through parse, validate, compatibility, external-policy check, proposal and governed admission. Existing canonical data is never silently overwritten; exact duplicates are no-op outcomes.
- **Risk radar:** one typed vocabulary covers the 12 frozen identity/package threats. Reports are deterministic and do not become rights, security or quality decisions.

## Package surface

The root `iris_asset_dna` API is assembled from declared module `__all__` lists and rejects ambiguous exports. Public modules group the concepts as follows:

| Module | Public concepts |
| --- | --- |
| `identity`, `traits`, `enums`, `base` | identities, revisions/envelopes, refs, trait schemas, applicability and common immutable records |
| `anchors`, `context`, `families` | anchors, projections, interface/slice construction, profiles, subject families and components |
| `cross_modal`, `drift`, `analysis`, `transitions`, `lineage` | domain links, scene roles, obligations, drift, fingerprints/equivalence, mutation and identity lineage |
| `compatibility`, `migration` | directional compatibility and immutable migration plans/receipts |
| `packages`, `imports` | package manifests, dependency closure, conformance, staged import and collision resolution |
| `validation`, `readiness`, `risk` | semantic validation, M05-only readiness and consolidated identity-risk findings |
| `ports` | 22 versioned downstream ref contracts |
| `serialization`, `versions`, `limits`, `invariants`, `errors` | closed JSON transport, versions, resource bounds, frozen proof index and typed errors |

The transport registry contains 112 explicitly discovered canonical record types. Types are selected from code-owned module export lists; JSON `kind` values never drive imports or type loading.

## Serialization, validation and bounds

The deterministic transport is `iris-m05-json-v1`; canonical JSON uses normalized strings, sorted keys and compact separators. Deserialization rejects duplicate JSON keys, non-finite values, unknown fields/types, wrong expected types and unsupported transport versions. It constructs only statically registered records. It uses no `eval`, `exec`, dynamic imports, shell, network, database or provider SDK.

Schema/contract pins are `iris-m05-core-v1` and `m05-contract-v1.0`; validator and extension refs have explicit version pins. Records are immutable dataclasses with immutable copies of nested JSON values. SHA-256 content digests protect fingerprints, comparisons, reports, migration receipts and package-conformance evidence.

`DNARecordLimits` bounds traits, anchors, components, domain links, lineage edges, dependency edges, graph depth, canonical depth, inline bytes, text length and profile/package counts. Validation is deterministic and fails closed on limit excess or missing required semantics. The kernel adds no runtime dependency beyond Python's standard library and internal M05 modules.

## Extension/ref ports

These 22 port contracts preserve downstream ownership without implementing it: `ProductionStateRefPort`, `HardwareExecutionConstraintRef`, `WorkerPlacementIdentityContextPort`, `ModelCapabilityIdentityEvidencePort`, `ConcreteWorkflowIdentityProjectionPort`, `TrainingIdentityDatasetRefPort`, `ImageReferenceIdentityEvidencePort`, `GeometryAppearanceIdentityPort`, `MotionDNARefPort`, `RenderObservationPort`, `DCCIdentityBindingPort`, `DeliveryProjectionCompatibilityPort`, `TemporalContinuityEvidencePort`, `DigitalHumanPersonaBindingPort`, `VoiceMusicAudioDomainDNAPort`, `CanonContentCampaignBrandPort`, `LocalizationIdentityPreservationPort`, `QualityRepairProposalPort`, `HIVEMemoryIdentitySlicePort`, `RightsSecurityEvidencePort`, `StorageObservabilityAutomationPort` and `APIExportRecoveryIdentityPort`.

## Frozen-family and proof mapping

`invariants.py` indexes all 150 frozen statements (`IRIS-DNAX-001..150`) exactly once under `F-M05-01..25`. Each entry names its family behavior proof method. `validate_invariant_catalog()` checks the complete numeric range, all 25 family IDs and a non-empty proof target for every entry; `tests/test_m05_invariants.py` resolves every target to an executable test method.

The synthetic harness in `examples/m05_synthetic_profiles.py` uses one shared record builder for the eight domain-neutral profiles `corporate.spokesperson`, `asymmetric.creature`, `generic.object`, `product.identity.levels`, `persistent.environment`, `crossmodal.character`, `scene.identity.roles` and `portable.dna.package`.

Run the M05 tests, all tests, synthetic harness, compilation and static checks from the repository root:

```powershell
python -m unittest discover -s tests -p "test_m05_*.py"
python -m unittest discover -s tests -p "test_*.py"
python -m examples.m05_synthetic_profiles
python -c "import compileall; paths=('iris_asset_dna','tests','examples'); ok=all(compileall.compile_dir(path, quiet=1, force=True) for path in paths); print('compileall:', 'PASS' if ok else 'FAIL'); raise SystemExit(0 if ok else 1)"
ruff check iris_asset_dna tests/m05_support.py tests/test_m05_authority_ports.py tests/test_m05_compatibility_packages.py tests/test_m05_invariants.py tests/test_m05_serialization_security.py examples/m05_synthetic_profiles.py
```
