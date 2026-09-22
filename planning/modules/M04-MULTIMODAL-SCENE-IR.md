# M04 — Multimodal IR / Scene IR

Status: `PLANNING_COMPLETE_TECH_REVIEW_NEXT`
Module: `M04`
Area: `B — Semantic Production Representation`
Planning issue: `#26`
Authorized baseline: `c231dd61a210fe6d315126e755b4642a4fd2e9a3`

## Mission

M04 converts admitted M03 creative semantics into a detailed, provider-neutral, versioned multimodal intermediate representation that can describe what a production **is** before later modules decide how a provider, DCC, model, renderer or worker will realize it.

M04 is the semantic bridge between creative intent and concrete production adapters. It must be rich enough for high-fidelity image, 3D, character, film, motion and audio pipelines while remaining independent of Blender, ComfyUI, model prompts and vendor workflow graphs.

## Ownership boundary

### M04 owns
- canonical Multimodal IR documents/fragments and schema families;
- scene/entity/asset/character structural representation;
- later camera/light/material/spatial semantics;
- later motion/audio/music/narrative representation;
- semantic lowering from admitted M03 objects into M04 IR;
- IR-local validation, typed gaps and semantic-loss evidence;
- IR schema/version/round-trip rules;
- provider-neutral capability requirements emitted toward later compilers.

### M04 does not own
- M01 quality decision/promotion authority;
- M02 project/production graph, branch/variant/snapshot, build/release or ExecutionPlan authority;
- M03 Creative Brief, intent, constraint or override authority;
- M05 persistent Asset/Persona DNA policy;
- M06 persistence/CAS/database authority;
- M16 concrete provider/workflow compiler ownership;
- Blender/ComfyUI/Maya/provider-specific execution;
- worker placement, GPU/VRAM scheduling or runtime orchestration.

### Inter-module law

M03 remains canonical for **why/what is intended**.
M04 becomes canonical for **the provider-neutral structured production representation**.
M16 later owns **how that representation becomes a concrete provider/workflow program**.
M02 remains canonical for **which production/build/branch/release event owns or executes it**.
M01 remains canonical for **whether quality is acceptable**.

---

# S01 — Scene, Character and Asset IR

## 1. S01 goals

S01 must make these statements true:

1. one scene can be represented without choosing a DCC/provider;
2. characters and ordinary assets share one extensible entity substrate without flattening character-specific semantics;
3. large assets can be referenced through lightweight semantic interfaces without loading heavy payloads;
4. every correctness-relevant IR element is traceable back to admitted M03 semantics and relevant M01 obligations;
5. transform/containment topology cannot be confused with arbitrary semantic relationships;
6. external/provider representations cannot silently become canonical M04 truth;
7. downstream consumers can request a minimum sufficient IR subgraph rather than the entire production.

## 2. M04 document identity

### MultimodalIRDocument
Stable semantic identity for one coherent IR subject.

Fields proposed:
- `ir_document_id`;
- `subject_ref` to M02 production/graph subject;
- `root_scene_ref` where scene semantics exist;
- `schema_manifest_ref`;
- `source_intent_revision_refs`;
- `quality_contract_refs`;
- `rights_security_policy_refs`;
- `created_by`;
- `contract_version`.

### IRRevision
M04 representations are immutable revisions.

A revision binds:
- parent revision refs;
- canonical root(s);
- schema-family/version manifest;
- semantic lowering receipt;
- structural fingerprint;
- changed semantic paths;
- unresolved IR gaps;
- provenance/evidence refs.

M02 owns branch/history topology. M04 revision identity only says which immutable semantic representation exists; it does not create a second branch/version-control system.

## 3. Core graph model

S01 proposes a **Dual Graph IR**.

### 3.1 Containment/transform graph
A strict acyclic hierarchy used for:
- scene containment;
- parent/child transform inheritance;
- scene/assembly organization;
- prototype-instance placement.

A node may have at most one transform parent inside a resolved scene hierarchy.

### 3.2 Semantic relationship graph
A typed directed graph used for relationships that are not transform parenting:
- character wears asset;
- prop attaches to socket;
- camera targets subject;
- asset consumes resource;
- node is constrained by anchor;
- entity participates in narrative role;
- geometry is skinned by skeleton;
- material binds to geometry;
- audio belongs to shot/character/environment.

Cycle legality is edge-type-specific. A transform cycle is always illegal. Other relationship cycles are rejected unless a registered schema explicitly proves they are semantically valid.

## 4. IR Node substrate

Every canonical node has a small stable header:

- `ir_node_id`;
- `type_ref`;
- `schema_family`;
- `schema_version`;
- `semantic_name` as non-identity display data;
- `source_semantic_refs` into M03;
- `quality_obligation_refs` into M01 where applicable;
- `provenance_refs`;
- `policy_refs`;
- `facet_refs`;
- `resource_refs`;
- `status` = ACTIVE / DEFERRED / UNRESOLVED / SUPERSEDED;
- deterministic node fingerprint basis.

Names never become identity.

## 5. Type + facet system

M04 uses a small typed core plus versioned facets/dialects.

### Core node families
- `SceneIR`
- `EntityIR`
- `AssetIR`
- `CharacterIR`
- `GeometryIR`
- `CollectionIR`
- `PrototypeIR`
- `InstanceIR`
- `ResourceBindingIR`

### Applied facets
Examples:
- renderable;
- transformable;
- deformable;
- skinnable;
- attachable;
- material-bindable;
- animatable;
- identity-anchor-aware;
- narrative-participant;
- audio-emitter/listener;
- provenance-bearing.

A domain extension must register:
- family;
- version;
- compatible core types;
- required properties;
- invariants;
- validation hook contract;
- migration/upgrade policy;
- serialization namespace.

Unknown mandatory facets fail closed. Unknown optional facets remain opaque only when their declared loss policy permits it.

## 6. Scene IR

`SceneIR` represents provider-neutral scene structure.

It includes:
- root entities;
- subscene/fragment refs;
- assembly relationships;
- prototype/instance bindings;
- environment/resource refs;
- semantic collections/sets;
- unresolved scene gaps;
- external interoperability refs;
- structural fingerprint.

It does not include:
- Blender collections as canonical concepts;
- USD prim paths as canonical IDs;
- ComfyUI node IDs;
- provider prompt tokens;
- M02 branch/build state.

## 7. Scene fragments and composition

Large productions are assembled from immutable `IRFragment` objects.

Composition operations are explicit:
- INCLUDE;
- REFERENCE;
- INSTANCE;
- OVERLAY;
- MASK;
- BIND.

Every composition arc declares:
- source fragment;
- target scope;
- precedence class;
- allowed override surface;
- provenance;
- compatibility/version expectations.

No implicit “last file wins” or timestamp wins.

S05 will freeze complete composition/version/round-trip rules. S01 freezes only the need for explicit deterministic composition semantics.

## 8. Interface / payload split

S01 introduces two levels:

### IR Interface Capsule
Small always-addressable summary:
- stable IDs/types;
- semantic class;
- declared ports/bindings;
- bounds/spatial interface ref when available;
- identity/DNA anchor refs;
- dependency/resource summary;
- variant/capability summary refs;
- fingerprint;
- payload availability.

### Deferred Payload Ref
Points to heavy or late-bound content:
- geometry buffers;
- dense curves/particles;
- textures;
- volumetrics;
- simulation caches;
- media;
- dense animation;
- external DCC interchange.

The canonical interface never relies on loading the payload merely to know what the asset **is** or how it may connect.

M06 later owns persistence/CAS/storage mechanics.

## 9. Asset IR

`AssetIR` is a provider-neutral semantic asset representation.

Required concepts:
- semantic asset class;
- entity/interface identity;
- component/resource roles;
- attachment/binding ports;
- geometry/resource refs;
- material/spatial refs deferred to S02;
- motion/deformation refs;
- provenance/rights refs;
- M05 DNA/identity-anchor refs;
- declared supported representation/capability facets;
- completeness/gap state.

The asset may be a product, prop, environment piece, UI/world object, 2D element, 3D model, audio-bearing object or another future domain extension.

## 10. Character IR

`CharacterIR` specializes Entity/Asset semantics without owning persistent persona DNA.

S01 requires:
- character semantic root;
- body/face region refs;
- skeleton hierarchy;
- joint semantic identifiers;
- rest/bind pose refs;
- skin/deformation bindings;
- blend-shape/morph channel declarations;
- attachment/socket ports;
- clothing/prop relationships;
- identity-anchor refs to future M05;
- voice/persona/story refs as opaque future ports;
- provenance/consent refs;
- unresolved deformation/identity gaps.

### Control-rig boundary
M04 may describe semantic deformation/control **requirements and channels**, but provider/DCC control-rig graphs are not canonical M04 data. Rigify, Blender bone constraints, Maya control nodes, Unreal Control Rig or provider-specific systems belong to adapters/later modules.

## 11. Geometry boundary

S01 represents geometry semantics without requiring heavy buffers inline.

`GeometryIR` may describe:
- geometry class;
- topology family;
- primitive/component role;
- attribute schema refs;
- normal/tangent/UV/color-set semantics;
- skin/blend bindings;
- representation/payload refs;
- semantic regions/groups;
- geometric integrity requirements.

Actual dense vertex/index/voxel/splat/media payloads may live behind versioned resource refs.

S01 does not yet freeze camera/space/units/material detail; S02 owns those semantics.

## 12. Prototype and instance semantics

A prototype is immutable canonical source representation.

An instance:
- references one prototype;
- has independent instance identity;
- may bind placement/spatial data;
- may apply only explicitly permitted scoped overrides;
- cannot mutate the prototype;
- carries override provenance;
- has its own structural fingerprint contribution.

Provider-native instancing is an adapter optimization, not required canonical behavior.

## 13. Semantic attachments and ports

Assets/characters expose typed ports:
- socket/attachment;
- geometry/material binding;
- skeleton/skin;
- input/output relationship;
- semantic role;
- future camera/audio/narrative bindings.

A binding is valid only when port type/capability/schema constraints match.

This avoids free-form string linking such as “attach to hand_r” without a typed contract.

## 14. M03 → M04 lowering

Every admitted M04 revision carries a `SemanticLoweringReceipt`.

For each consumed M03 statement/constraint/operation:
- source semantic ref;
- produced IR node/property refs;
- lowering rule/version;
- loss class inherited from M03;
- representation status;
- gap/remedy if unrepresented;
- rationale/provenance.

Mandatory semantics can never disappear because the target schema has no field.

### Lowering states
- REPRESENTED_EXACTLY;
- REPRESENTED_BOUNDED;
- DEFERRED_TO_LATER_IR_LAYER;
- REQUIRES_EXTENSION;
- BLOCKED_UNREPRESENTABLE.

`LOSSLESS_REQUIRED + BLOCKED_UNREPRESENTABLE` blocks admission.

## 15. M01 quality binding

M04 does not score quality.

IR nodes may bind to M01:
- FidelityContract refs;
- dimension/obligation refs;
- protected semantic-zone refs;
- required evidence-type refs.

This lets later generation/evaluation answer which IR parts satisfy which quality obligations without giving M04 promotion authority.

## 16. M05 identity/DNA boundary

M04 provides only:
- `IdentityAnchorRef`;
- `AssetDNARef`;
- `PersonaDNARef`;
- anchor application points;
- anchor preservation obligations.

M05 later owns:
- persistent identity policy;
- canonical DNA contents;
- identity drift rules;
- cross-asset/persona continuity.

M04 cannot invent DNA values.

## 17. Resource identity

External/heavy content is referenced with typed `ResourceRef`:
- logical resource ID;
- resource kind;
- content digest when known;
- media/type metadata;
- required schema/decoder capability;
- provenance/rights refs;
- expected integrity/size metadata;
- optional M06 storage locator ref.

Location/path is not identity.

## 18. Context economy

M04 introduces `MinimumSufficientIRSlice`.

A consumer declares:
- root refs;
- required relationship families;
- required facets/properties;
- provenance depth;
- quality-obligation depth;
- payload/interface policy.

The slice compiler must exclude unrelated subgraphs without breaking dependency closure.

Examples:
- a face-rig task receives character/face/skeleton/identity anchors, not the whole city scene;
- a product material task receives the asset/material/spatial interface, not unrelated narrative/audio history.

## 19. Fingerprints and deltas

M04 owns semantic/structural fingerprints of IR content, not project-build identity.

Proposed:
- `IRStructuralFingerprint`;
- `IRSubgraphFingerprint`;
- `IRSemanticDelta`;
- `IRInterfaceFingerprint`.

M02 may include these fingerprints in causal build fingerprints.

Irrelevant source-only changes may preserve safe reuse only under explicit versioned equivalence rules.

## 20. Gap model

An `IRGap` is first-class:
- missing semantic representation;
- unresolved schema;
- missing resource;
- incompatible facet;
- unknown mandatory extension;
- lowering loss;
- invalid relationship;
- stale identity/DNA ref;
- incomplete character deformation semantics.

Each gap carries:
- severity/consequence;
- affected source semantic refs;
- affected IR refs;
- blocking state;
- remedy family;
- responsible future module/extension where known.

## 21. Security and resource limits

The core must be designed to reject:
- transform cycles;
- illegal ownership/containment cycles;
- duplicate canonical IDs;
- resource-ref digest mismatch;
- unknown mandatory schemas/facets;
- excessive nesting/fanout beyond deterministic configured limits;
- pathological relationship graphs;
- untrusted metadata attempting to self-register a schema;
- provider results attempting direct canonical mutation.

Schema registration is governed, not data-driven code execution.

## 22. S01 proprietary technology candidates

S01 introduces `IRIS-MIRX-001..030` as candidate internal technologies. They are design candidates, **not claims of novelty or patentability**. The registry is `planning/technology-registry/M04-TECHNOLOGIES.md`.

Core candidate families:
- Semantic Scene Graph Fabric;
- Dual-Graph Topology;
- Intent-to-IR Trace Spine;
- Interface Capsule / Deferred Payload;
- Lossless Obligation Coverage;
- typed facet/dialect registry;
- Character Semantic Skeleton Envelope;
- Identity Anchor Bridge;
- Prototype/Instance Integrity;
- Semantic Attachment Ports;
- Scene Fragment Composition;
- deterministic composition precedence;
- IR Gap Ledger;
- locality-preserving slices/deltas;
- provider-extension quarantine.

## 23. S01 proposed decisions

- **D-M04-001:** canonical M04 IR is IRIS-owned and provider-neutral.
- **D-M04-002:** containment/transform topology and semantic relationship topology are separate graphs.
- **D-M04-003:** every correctness-relevant M04 element is traceable to M03 source semantics or an admitted policy/default.
- **D-M04-004:** interface capsules are separable from heavy payloads.
- **D-M04-005:** M05 owns DNA/identity policy; M04 carries typed anchor refs only.
- **D-M04-006:** provider/DCC-specific fields are forbidden in the stable M04 core.
- **D-M04-007:** heavy geometry/media payloads are external typed resources, not mandatory inline canonical state.
- **D-M04-008:** M04 character representation includes deformation semantics but not provider/DCC control-rig graphs.
- **D-M04-009:** M04 composition does not create a second M02 branch/build/version-control system.
- **D-M04-010:** mandatory unrepresentable M03 semantics become blocking gaps, never silent drops.
- **D-M04-011:** provider capability does not mutate canonical IR or requested M01 QualityClass.
- **D-M04-012:** M04 revisions are immutable semantic representations; M02 remains authority for branch/history topology.
- **D-M04-013:** schema family/version is explicit for every canonical extension.
- **D-M04-014:** composition precedence is explicit; last-writer/timestamp wins is forbidden.
- **D-M04-015:** minimum sufficient IR slices preserve dependency closure and correctness.

## 24. S01 acceptance obligations

Later M04 implementation must prove at minimum:
- strict transform-cycle rejection;
- deterministic node/relationship serialization basis;
- stable IDs independent from display names/paths;
- provider-neutrality scan;
- unknown mandatory facet failure-closed;
- prototype cannot be mutated through instance override;
- interface-only asset can be inspected without payload access;
- character skeleton/skin/blend semantics round-trip;
- M03 mandatory semantics cannot disappear during lowering;
- M01 obligation refs remain refs and cannot grant M04 promotion authority;
- M05 DNA refs remain opaque/unowned;
- localized subgraph slice excludes unrelated scene content;
- structural fingerprints are deterministic;
- resource paths/URLs do not become canonical identity;
- hostile graph depth/fanout is bounded;
- provider result cannot self-author a canonical IR revision.

## 25. S01 disposition

`COMPLETE_FOR_MODULE_PLANNING`

No implementation is authorized.

Next legal planning session: **S02 — Camera, Lighting, Material and Spatial IR**.


---

# S02 — Camera, Lighting, Material and Spatial IR

## 26. S02 goals

S02 must make these statements true:

1. spatial quantities have explicit frames/units/conventions;
2. physical camera semantics are portable without renderer-specific tokens;
3. lighting has typed emitter/quantity/color/shaping semantics;
4. material/look development is a typed provider-neutral network;
5. color values cannot lose their color-space/encoding meaning;
6. preview approximations cannot silently replace final-quality semantics;
7. unsupported spatial/camera/light/material features become explicit gaps.

## 27. Spatial Reference Contract

M04 introduces `SpatialReferenceIR`.

Required fields/concepts:
- length unit and scale;
- handedness;
- up axis;
- forward/view convention;
- world/reference origin;
- angular unit;
- time base ref where spatial sampling depends on time;
- precision class;
- spatial schema version.

All spatial values are interpreted through a declared reference.

A consumer may convert references only through a deterministic `SpatialConversionReceipt`.

## 28. Quantity-safe values

Physical/spatial properties use typed quantities rather than unlabelled floats.

`QuantityIR` carries:
- numeric value;
- dimension;
- unit;
- precision/tolerance;
- authored vs derived state;
- provenance.

Examples:
- focal length;
- sensor size;
- distance;
- illuminance/radiance/luminance-related values;
- color temperature;
- angle;
- exposure values where semantically defined.

Dimensionally incompatible operations are invalid.

## 29. Coordinate frames

`CoordinateFrameIR` provides named/scoped frames:
- WORLD;
- SCENE;
- ASSET;
- CHARACTER;
- SKELETON;
- JOINT;
- CAMERA;
- LIGHT;
- MATERIAL/PROJECTION;
- CUSTOM versioned extension.

A frame binds to a transformable node/reference and declares scope.

Names are display/discovery labels, not global identity.

## 30. Transform IR

M04 represents authored transform intent separately from derived world transforms.

### TransformChainIR
Ordered typed operations:
- translation;
- rotation/quaternion;
- scale;
- pivot;
- shear where supported by the declared schema;
- explicit matrix operation when decomposition would lose authored meaning.

### ResolvedTransform
Derived/cacheable result for a particular frame evaluation.

Rules:
- operation order is explicit;
- transform parent comes from S01 containment graph;
- hidden DCC transform conventions are forbidden;
- lossy decomposition requires a receipt/gap;
- coordinate conversion is explicit.

## 31. Camera IR

`CameraIR` is an Entity facet with a `CameraOpticsIR`.

Core projection families:
- PERSPECTIVE;
- ORTHOGRAPHIC;
- extension-ref for fisheye/panoramic/nonlinear projection.

Physical/semantic fields include:
- filmback/sensor aperture;
- focal length or equivalent projection contract;
- lens shift/offset;
- near/far clipping policy;
- focus distance;
- aperture/f-number where depth of field is requested;
- depth-of-field enable/intent;
- camera gate/aspect intent;
- framing/composition constraint refs;
- focus/target relationship refs;
- optional lens-distortion/calibration extension refs.

Provider-specific lens names/presets are not canonical.

## 32. Camera exposure boundary

Photographic/render exposure semantics are explicit and versioned.

M04 may represent:
- aperture;
- shutter/exposure-time **reference** (detailed temporal shutter semantics finish in S03);
- ISO/sensitivity intent;
- exposure compensation;
- target exposure policy refs.

M04 does not dictate renderer tone mapping.

Color/output transforms are separate from scene exposure.

## 33. Lighting IR

`LightIR` separates emitter geometry, emission and artistic modifiers.

Core emitter families:
- POINT/SPHERE;
- DISK;
- RECT/AREA;
- DISTANT;
- ENVIRONMENT;
- MESH/GEOMETRY via facet;
- extension-ref.

Emission semantics:
- physically identified quantity/unit or declared normalized artistic quantity;
- exposure multiplier if used;
- color or spectral intent;
- color temperature with explicit basis;
- normalization policy;
- two-sided/directional behavior where relevant.

An untyped `intensity=1000` is invalid canonical final semantics.

## 34. Light shaping and influence

Separate facets:
- `LightShapingIR` — cone/spread/focus/profile/IES-like resource refs;
- `ShadowIntentIR` — shadow participation/softness/bias semantics at provider-neutral level;
- `LightInfluenceIR` — include/exclude semantic target sets;
- `LightFilterBindingIR` — filter/resource/network refs.

A renderer may approximate only when the loss policy permits it and a translation receipt records the difference.

## 35. Material IR

`MaterialIR` contains typed terminal families:
- SURFACE;
- VOLUME;
- DISPLACEMENT;
- EMISSION;
- extension terminal.

A material may expose:
- parameters;
- typed graph/network;
- texture/resource bindings;
- coordinate-space requirements;
- color-management refs;
- semantic purpose/profile;
- physical/non-physical flags where meaningful.

## 36. Material Graph IR

`MaterialGraphIR` uses:
- typed nodes;
- typed input/output ports;
- explicit connections;
- declared value types;
- node family/version;
- target-neutral semantics;
- deterministic graph validation;
- extension registry.

Arbitrary executable shader source is not canonical graph semantics.

MaterialX/OpenPBR-compatible families can later be mapped through adapters, but M04 cannot assume a renderer implements every node identically.

## 37. Material binding

`MaterialBindingIR` binds a material to:
- whole geometry/entity;
- semantic region/subset;
- collection;
- purpose profile.

Purpose classes may include:
- FINAL;
- PREVIEW;
- COLLISION/UTILITY where semantically relevant;
- domain extension.

A PREVIEW binding can never satisfy a FINAL requirement unless the owning M01/M03 contract explicitly accepts equivalence.

## 38. Texture/resource semantics

`TextureResourceIR` references:
- logical resource;
- sampling role;
- coordinate-set/frame ref;
- channel semantics;
- color space/encoding;
- alpha mode;
- wrap/filter intent where correctness-relevant;
- UDIM/tile/atlas extension refs;
- provenance/rights.

File extension does not define color space.

## 39. Color semantics

M04 introduces `ColorValueIR`:
- components/value;
- color-space ref;
- transfer/encoding ref when required;
- alpha association semantics;
- spectral/color-temperature source when applicable;
- precision.

`ColorPipelineRef` may point to an admitted OCIO-like configuration/profile, but M04 does not own global color-management software.

Conversions create `ColorConversionReceipt` with source/target profile/version and loss/tolerance.

## 40. Spatial regions and bounds

`SpatialRegionIR` may represent:
- bounding volume;
- semantic region;
- interaction/placement volume;
- camera safe/framing region;
- light influence region.

Bounds are labelled AUTHORED or DERIVED.

A stale derived bound cannot become canonical placement truth after geometry changes.

## 41. Provider-neutral physicality

S02 distinguishes:
- PHYSICAL;
- PHYSICALLY_BASED_APPROXIMATION;
- ARTISTIC_NON_PHYSICAL;
- UNKNOWN/UNDECLARED.

This classification applies where relevant to camera/light/material semantics.

IRIS does not ban artistic controls. It prevents an artistic control from masquerading as a physical quantity and contaminating cross-provider translation.

## 42. Quality and approximation shield

Every S02 semantic feature carries or inherits a loss policy.

Rules:
- final-quality LOSSLESS_REQUIRED obligations block on unsupported translation;
- preview-only bounded approximation is allowed only when explicitly admitted;
- provider scarcity cannot rewrite canonical camera/light/material semantics;
- final M01 QualityClass is never lowered by M04;
- approximation receipts remain traceable to exact IR features affected.

## 43. S02 proprietary technology candidates

S02 extends the registry with `IRIS-MIRX-031..060`.

Key families:
- Unit-Safe Spatial Ledger;
- Frame/Transform Integrity;
- Physical Camera Envelope;
- Lens Extension Registry;
- Photometric/Spectral Light Contract;
- Influence/Shaping Graph;
- Material Semantic Graph;
- purpose-aware material binding;
- color-space tagged values;
- color-pipeline receipt;
- Preview/Final Separation Shield;
- physicality classification;
- approximation impact map.

## 44. S02 proposed decisions

- **D-M04-016:** all correctness-relevant spatial values are interpreted under an explicit SpatialReferenceIR.
- **D-M04-017:** authored transform chains and derived world matrices are separate facts.
- **D-M04-018:** camera/lens semantics are physical/provider-neutral first, provider preset second.
- **D-M04-019:** untyped light intensity is insufficient for canonical final semantics.
- **D-M04-020:** artistic non-physical lighting/material controls are allowed only when explicitly classified.
- **D-M04-021:** MaterialIR is IRIS-owned; MaterialX is an adapter/reference, not canonical dependency.
- **D-M04-022:** material binding is typed by target/subset/purpose.
- **D-M04-023:** every color/texture value that requires interpretation carries color-space/encoding identity.
- **D-M04-024:** preview semantics cannot silently satisfy final obligations.
- **D-M04-025:** coordinate/color/unit conversions produce receipts.
- **D-M04-026:** unsupported mandatory camera/light/material semantics become gaps, never dropped fields.
- **D-M04-027:** provider capabilities cannot mutate canonical physical values.
- **D-M04-028:** S03 owns detailed temporal shutter/motion sampling semantics.
- **D-M04-029:** S02 spatial semantics do not create M02 production-graph topology.
- **D-M04-030:** renderer-specific shader source/options live behind future adapters/extensions.

## 45. S02 acceptance obligations

Later implementation must prove:
- unit mismatch detection;
- deterministic coordinate conversion;
- transform-chain order preservation;
- transform-cycle remains impossible;
- camera physical properties survive canonical round-trip;
- unsupported nonlinear lens is a typed extension/gap rather than coerced perspective;
- light quantities cannot be confused across incompatible units;
- non-physical light modifiers are explicit;
- material graph type/port validation;
- material-binding purpose separation;
- MaterialX-style adapter can be added without core rewrite;
- color-space tags survive texture/material binding;
- untagged correctness-critical color is rejected or explicitly UNKNOWN according to policy;
- preview material cannot satisfy final requirement by default;
- conversion/approximation receipts identify affected IR paths;
- no renderer/DCC/provider package is required by core.

## 46. S02 disposition

`COMPLETE_FOR_MODULE_PLANNING`

Next legal planning session: **S03 — Motion, Audio, Music and Narrative IR**.


---

# S03 — Motion, Audio, Music and Narrative IR

## 47. S03 goals

S03 must make these statements true:

1. time is represented explicitly and consistently across modalities;
2. motion can target semantic IR properties without choosing a DCC animation system;
3. audio can be placed, related and spatially described without embedding a DAW/runtime graph;
4. music can carry structural/performance semantics without making MIDI canonical;
5. narrative can bind production realization to story/canon references without making M04 the Story Engine;
6. cross-modal synchronization can be represented and validated;
7. temporal resampling/baking/conversion loss is explicit.

## 48. Temporal Reference Contract

M04 introduces `TemporalReferenceIR`.

It declares:
- rational `ticks_per_second` or equivalent exact time scale;
- optional display frame-rate profile;
- optional SMPTE/timecode interpretation profile;
- timeline epoch/origin;
- range semantics;
- subframe precision;
- schema/version.

Canonical time is rational/integer-domain where practical. Floating timestamps are not the only source of temporal identity.

Display frame numbers never become universal canonical time.

## 49. Time primitives

Core primitives:
- `TimePointIR`;
- `TimeRangeIR`;
- `DurationIR`;
- `TemporalMarkerIR`;
- `TemporalRelationIR`;
- `TemporalTransformReceipt`.

Temporal conversions must state source/target bases and rounding/loss.

## 50. Temporal layers

M04 distinguishes:

### Semantic production time
Meaningful event/shot/cue timing.

### Authored animation time
Curves, key events and interpolation.

### Sampled/baked time
Dense samples, simulation caches, mocap/audio/media alignment.

### Editorial presentation time
Clip placement, trims, transitions and sequence relationships.

These layers may reference each other but are not silently collapsed.

M36/M38 own production/editorial operations. M04 only represents their portable result/intent substrate.

## 51. Motion IR

`MotionIR` binds time-varying behavior to canonical targets.

Core:
- target node/ref;
- target semantic property/path;
- value type;
- temporal range;
- authored representation kind;
- interpolation/extrapolation policy;
- source/provenance;
- loss policy;
- payload/clip refs;
- fingerprint.

Representation kinds:
- KEYED;
- CURVE;
- SAMPLED;
- CLIP_REFERENCE;
- PROCEDURAL_REQUIREMENT_REF;
- EVENT_DRIVEN_EXTENSION.

## 52. Motion channels

`MotionChannelIR` may target:
- transform properties;
- skeleton joints;
- blend-shape/morph weights;
- material/light/camera properties;
- future simulation/control parameters admitted by extensions.

The target must be type-compatible with the channel value type.

No arbitrary string-path execution.

## 53. Curve semantics

`AnimationCurveIR` supports provider-neutral:
- knots/key points;
- tangent/interpolation family;
- pre/post extrapolation;
- loop/repeat intent;
- units/value type;
- discontinuity/held state.

If a provider cannot preserve curve shape under a lossless obligation, it reports a gap.

M30 later owns how curves/motion are generated, retargeted or repaired.

## 54. Motion clips and layering

`MotionClipIR` is an immutable reusable temporal fragment.

It can declare:
- source time range;
- target mapping;
- time scale/offset;
- loop policy;
- blend region/weight semantics;
- channel set;
- root-motion semantics ref;
- provenance.

`MotionLayerIR` combines clips/channels with explicit composition rules.

It does not define a DCC NLA system or animation state machine implementation.

## 55. Skeleton/deformation time binding

S03 extends S01 CharacterIR with temporal bindings:
- skeletal pose channels;
- morph/blend-shape channels;
- visibility/state events;
- attachment changes;
- semantic performance events.

M29 owns rig/deformation standards and M30 owns animation production. M04 represents the resulting canonical temporal semantics.

## 56. Shutter and temporal sampling

S03 completes the S02 camera shutter boundary.

`TemporalSamplingIR` may declare:
- shutter/open-close interval;
- sampling window;
- motion-blur intent;
- rolling/global-shutter extension refs;
- sample distribution intent;
- source/target time basis.

Renderer-specific motion-blur samples/settings are adapter concerns.

## 57. Audio IR

`AudioIR` separates semantic audio object/role from media payload.

Core audio entity classes:
- DIALOGUE;
- VOICE;
- MUSIC;
- SFX;
- FOLEY;
- AMBIENCE;
- ROOM_TONE;
- UI;
- NARRATIVE_GUIDE;
- extension.

An audio entity may bind:
- media/resource ref;
- time range/placement;
- source language;
- speaker/persona refs;
- loudness/level intent refs;
- channel/object/spatial representation profile;
- provenance/rights/consent refs;
- M01 quality obligations;
- M03 semantic sources.

## 58. Audio object and spatial semantics

`AudioSpatialIR` may describe:
- channel-based;
- object-based;
- scene/HOA-like;
- binaural;
- custom extension representation.

Object-based audio can bind:
- source entity;
- position/orientation/spread;
- coordinate-frame ref;
- motion ref;
- divergence/diffuse intent;
- rendering-zone/profile refs.

M42 later owns sound design/spatial-audio production and rendering choices.

## 59. Audio clip placement

`AudioClipBindingIR` represents:
- media ref;
- source range;
- timeline range;
- trim;
- loop;
- fades/crossfade intent;
- gain/level envelope ref;
- sync relation;
- semantic role.

Media bytes stay external.

Editing operations and mix/render graphs belong to M38/M42.

## 60. Voice/persona boundary

Audio/voice IR may carry:
- `VoiceIdentityRef`;
- `PersonaRef`;
- `SpeakerRef`;
- language/locale;
- dialogue/text source ref;
- performance/prosody requirement refs.

M39/M40 own identity/voice design, generation, cloning authorization, dubbing and drift QA.

M04 does not synthesize or infer a voice identity.

## 61. Music IR

`MusicIR` provides a provider-neutral structural representation that may be sparse or detailed.

Core:
- musical work/cue identity ref;
- timeline placement;
- tempo map;
- meter map;
- key/tonal-context ref when applicable;
- section/form markers;
- part/track/instrument-role refs;
- performance-event streams;
- harmony/chord extension refs;
- lyric/text refs;
- media/render refs;
- provenance/rights.

Music IR supports non-tonal/non-metered material by allowing these fields to be absent/explicitly inapplicable.

## 62. Music events

Optional `MusicEventIR` dialect may represent:
- note/pitch event;
- duration;
- velocity/dynamics;
- articulation;
- expression/controller intent;
- per-note modulation;
- semantic role.

MIDI 1/2 import/export is an adapter path. MIDI channel/message identity is not canonical M04 identity.

M41 owns composition, arrangement, Music DNA and final mix/master decisions.

## 63. Narrative Projection IR

M04 introduces `NarrativeProjectionIR`, not a Canon engine.

It binds a production representation to external/future story semantics:
- story/canon ref;
- scene/sequence/beat ref;
- character role ref;
- action/dialogue/event projection;
- emotional/performance intent refs;
- continuity dependency refs;
- narrative time/order refs;
- source revision/provenance.

When M43 exists, M43 remains authoritative for story/canon/world state/arcs/dialogue truth.

M04 only records how a current production scene realizes or references that truth.

## 64. Local narrative cues

For workflows before M43 exists, M04 may carry bounded `NarrativeCueIR` objects derived from M03:
- BEAT;
- ACTION;
- DIALOGUE_CUE;
- REACTION;
- REVEAL;
- TRANSITION_INTENT;
- CONTINUITY_REQUIREMENT.

These cues are production-local and cannot self-promote into global canon.

## 65. Timeline IR

`TimelineIR` is a provider-neutral temporal container, not an editor.

It can contain:
- tracks/layers by semantic role;
- clips/fragments;
- gaps;
- transitions as semantic refs/contracts;
- markers;
- nested sequences;
- sync groups;
- external media refs.

M36 owns shot planning/production timeline strategy.
M38 owns editing/cut/compositing/encode operations.

M04 owns only the portable representation substrate those modules may use.

## 66. Shot / sequence boundary

M04 may define:
- `ShotRepresentationIR`;
- `SequenceRepresentationIR`;
- shot range;
- scene/camera refs;
- involved entity refs;
- audio/music/narrative bindings;
- continuity dependency refs;
- transition intent refs.

Shot selection, edit decisions and long-form assembly algorithms remain M36/M38.

## 67. Cross-modal synchronization

`SyncRelationIR` supports typed relations:
- EXACT_START;
- EXACT_END;
- OFFSET;
- LOCKED_DURATION;
- LIP_SYNC_REQUIREMENT;
- BEAT_SYNC;
- EVENT_SYNC;
- CAMERA_MOTION_SYNC;
- CUSTOM_EXTENSION.

A sync relation identifies:
- source/target temporal refs;
- tolerance;
- authority;
- loss policy;
- provenance.

A provider cannot silently drift a mandatory sync relation.

## 68. Temporal continuity boundary

M04 stores continuity dependency refs and state projections but M37 owns:
- temporal identity lock;
- shot continuity graph;
- cross-shot object/environment/camera continuity evaluation;
- artifact radar and repair;
- continuity scoring.

M04 is the transport/representation layer for continuity-relevant facts, not their judge.

## 69. Temporal lowering and loss

Every temporal transformation can emit:
- `TemporalResampleReceipt`;
- `MotionBakeReceipt`;
- `AudioConformReceipt`;
- `TimelineProjectionReceipt`.

Receipts identify:
- source/target bases;
- affected channels/events;
- interpolation/resampling policy;
- quantization/rounding;
- dropped/approximated semantics;
- M03 loss class;
- M01 obligations affected.

Lossless-required timing/sync semantics cannot be rounded away silently.

## 70. Context economy for time

`MinimumSufficientTemporalSlice` selects:
- time range;
- target roots;
- channel/event families;
- sync closure;
- narrative/audio/music dependencies;
- provenance/quality depth.

A lip-sync repair task should not require the whole film timeline.
A foot-contact fix should not require unrelated dialogue/music tracks.

## 71. S03 proprietary technology candidates

S03 extends the registry with `IRIS-MIRX-061..090`.

Key families:
- Unified Temporal Reference Fabric;
- authored/sample/editorial time partition;
- Motion Channel Contract;
- Motion Clip Semantic Layering;
- Cross-Modal Sync Graph;
- Audio Object Semantic Envelope;
- Music Structural IR;
- Narrative Projection Firewall;
- Temporal Loss Receipts;
- Context-Budgeted Temporal Slice.

## 72. S03 proposed decisions

- **D-M04-031:** canonical time basis is explicit and separate from display frame numbering.
- **D-M04-032:** semantic/authored/sampled/editorial time are distinct layers.
- **D-M04-033:** MotionIR targets typed semantic properties rather than DCC path strings.
- **D-M04-034:** M04 represents motion but M30 owns motion generation/retargeting/repair.
- **D-M04-035:** detailed rig/control systems remain M29/provider/DCC responsibility.
- **D-M04-036:** S03 temporal sampling completes but does not replace S02 camera semantics.
- **D-M04-037:** audio bytes/media remain external resources.
- **D-M04-038:** M04 audio representation does not own mix/post/render algorithms.
- **D-M04-039:** MIDI is an adapter/interchange route, not canonical Music IR.
- **D-M04-040:** M41 owns composition/Music DNA/mix-master; M04 owns portable music representation.
- **D-M04-041:** NarrativeProjectionIR cannot become global Canon truth.
- **D-M04-042:** M43 will remain narrative/canon authority.
- **D-M04-043:** TimelineIR is representation, not editorial authority.
- **D-M04-044:** M36/M38 own shot planning/editing/assembly operations.
- **D-M04-045:** mandatory cross-modal sync loss blocks when outside admitted tolerance.

## 73. S03 acceptance obligations

Later implementation must prove:
- rational time conversion determinism;
- no hidden frame-rate assumption;
- typed motion-target validation;
- curve/interpolation round trip;
- clip time-scale/offset determinism;
- sampled payload may remain deferred;
- audio resource externalization;
- object/spatial audio bindings remain coordinate-frame aware;
- music event representation does not require MIDI;
- non-metered/non-tonal music remains representable;
- narrative local cue cannot self-promote to Canon;
- timeline nested-range validation;
- exact sync tolerance failure-closed;
- temporal resample/bake receipt identifies loss;
- localized temporal slice excludes unrelated timeline regions;
- no animation/audio/music/editorial/story runtime dependency in core.

## 74. S03 disposition

`COMPLETE_FOR_MODULE_PLANNING`

Next legal planning session: **S04 — Provider Compiler and capability downgrade planning**.


---

# S04 — Representation Capability & Semantic Lowering Planning

> Historical index label: "Provider Compiler and capability downgrade planning".
>
> S04 resolves that overlap by reserving concrete provider/workflow compilation to M16.

## 75. S04 goals

S04 must make these statements true:

1. M04 can state exactly which representation capabilities a document requires and uses;
2. a future target/profile can be checked for semantic representability without compiling a workflow;
3. mandatory unsupported semantics fail closed;
4. bounded approximation is permitted only when upstream loss policy explicitly allows it;
5. canonical IR is never rewritten to fit provider scarcity;
6. M01 QualityClass is never downgraded by M04;
7. M16 receives a deterministic semantic compilation contract.

## 76. Representation Capability Manifest

Every M04 document/revision can emit a `RepresentationCapabilityManifest`.

It contains:
- schema families/versions used;
- mandatory facets/extensions;
- optional facets/extensions;
- value/type capabilities;
- spatial/temporal/material/audio/narrative feature families used;
- payload/codec/interchange requirements where semantically required;
- lossless-required feature set;
- bounded-approximation-eligible feature set;
- resource-limit assumptions;
- fingerprint.

This is capability metadata about **the representation**, not a provider hardware/model card.

## 77. Required vs optional semantics

Capability disposition:
- REQUIRED;
- USED_OPTIONAL;
- ADVISORY;
- EXTENSION_OPAQUE_ALLOWED.

Rules:
- every REQUIRED capability must be understood and preserved by a lossless target or produce a blocking gap;
- an optional unknown capability can remain opaque only when its loss policy permits;
- metadata cannot relabel a required feature as optional to make compilation pass.

## 78. Target Representation Profile

M04 defines a provider-neutral `TargetRepresentationProfile`.

It may describe a semantic destination family such as:
- generic 3D interchange;
- image/render scene;
- animation interchange;
- editorial interchange;
- game/web asset representation;
- audio object metadata;
- future provider-compiler input profile.

It declares:
- profile identity/version;
- supported schema/facet families/versions;
- supported value/relationship types;
- semantic limits;
- extension support;
- exact vs bounded support classes;
- unsupported features;
- evidence/qualification refs.

A profile cannot claim concrete runtime/provider support without later M16/M14 qualification evidence.

## 79. Capability support states

For each required IR feature, analysis yields:
- EXACT;
- BOUNDED;
- EXTENSION_REQUIRED;
- OPAQUE_PRESERVABLE;
- UNSUPPORTED;
- UNKNOWN.

`BOUNDED` requires:
- explicit allowed loss class;
- tolerance/affected paths;
- adaptation rule identity;
- downstream obligation impact.

UNSUPPORTED/UNKNOWN on a mandatory lossless feature blocks.

## 80. Semantic Legality Analysis

`SemanticLegalityReport` is analysis-only.

It identifies:
- legal/exact features;
- dynamically legal features under stated constraints;
- illegal/unrepresentable features;
- unknown features;
- required extensions;
- possible adaptation routes;
- blocking gaps;
- quality/constraint obligations affected.

It does not rewrite the IR.

This is the M04 analogue of "can this semantics be lowered?", not "compile it now".

## 81. Semantic Lowering Plan

When analysis permits, M04 may produce an immutable `SemanticLoweringPlan`.

It contains:
- source IR revision/fingerprint;
- target representation profile;
- ordered semantic lowering/adaptation rules;
- expected outputs at semantic family level;
- required extensions;
- expected approximation/loss;
- validation obligations;
- rollback/source trace;
- compiler-contract version.

The plan contains no:
- model selection;
- ComfyUI nodes;
- Blender Python;
- provider URLs;
- worker/GPU placement;
- secret/API keys;
- concrete runtime queue plan.

## 82. Semantic Lowering Rule

A `SemanticLoweringRule` is declarative and versioned.

It states:
- source schema/facet/type pattern;
- target semantic family;
- preconditions;
- exact/bounded result class;
- preserved obligations;
- affected/lost obligations;
- required extension;
- validation obligations;
- provenance/version.

It is not arbitrary executable code.

M16/provider adapters later implement executable realization of accepted rule contracts.

## 83. Adaptation proposals

When exact representation is impossible, M04 can emit an `AdaptationProposal`:
- split representation;
- bake/flatten a representable derived artifact;
- replace with admitted bounded approximation;
- retain an opaque extension;
- defer to another target;
- require provider escalation;
- request new M03/M04 revision.

An adaptation proposal is not self-authorizing.

If meaning/quality intent changes, a governed upstream revision is required.

## 84. No-Downgrade Shield

S04 freezes the distinction:

### Forbidden
- lowering M01 QualityClass because target/provider is weak;
- deleting mandatory semantics to make a target pass;
- converting REQUIRED to OPTIONAL;
- changing protected M03 constraints;
- accepting a preview representation as final without explicit equivalence.

### Potentially allowed
- provider-neutral bounded approximation already authorized by M03 loss class/tolerance;
- alternate target/profile selection by future M15/M16;
- escalation to another representation/provider;
- multi-pass or split representation;
- additional extension requirement.

Scarcity produces **capability debt/gap**, not quality redefinition.

## 85. Capability Gap Ledger

`RepresentationGap` records:
- feature/path;
- required support;
- observed target support;
- blocking state;
- upstream loss policy;
- M01 obligation refs;
- M03 constraint refs;
- suggested remedy;
- future owner;
- evidence/profile version.

Gap resolution never mutates original evidence.

## 86. Translation receipt boundary

M03 already defines provider-neutral ProviderTranslationReceipt contracts.

M04 extends this into a representation-specific `IRTranslationReceipt` that records:
- source M04 fingerprint;
- target representation profile/version;
- lowering-plan fingerprint;
- exact/bounded/extension outcomes per feature;
- validation results;
- unresolved gaps.

M16 later emits the concrete provider/workflow translation receipt linked to this semantic receipt.

## 87. Provider observation quarantine

A future provider may report:
- supported;
- unsupported;
- approximation;
- runtime failure;
- version drift.

Those observations are evidence.

They cannot:
- rewrite the M04 IR;
- upgrade their own capability status;
- relax required semantics;
- alter M01/M03 authority.

Qualification belongs to M14/M16 and governance.

## 88. Selection boundary with M14/M15/M16

- M14 owns empirical Model Cards/Capability Genome.
- M15 owns model/provider routing and champion/challenger decisions.
- M16 owns workflow registry and concrete provider compiler.
- M17+ own provider runtime integrations.
- M07-M13 own hardware/runtime/performance planning.

M04 only emits the semantic/capability contract these modules consume.

## 89. Semantic target families

M04 target profiles are **semantic destinations**, not vendor products.

Examples:
- SCENE_INTERCHANGE;
- WEB_GAME_INTERCHANGE;
- DCC_INTERCHANGE;
- RENDER_SCENE;
- EDITORIAL_TIMELINE;
- AUDIO_METADATA;
- SYMBOLIC_MUSIC;
- PROVIDER_COMPILER_INPUT;
- CUSTOM_VERSIONED_EXTENSION.

Concrete USD/glTF/MaterialX/OTIO/MIDI/provider formats are adapters/profiles admitted later.

## 90. Multi-target lowering

One M04 source may require multiple target representations.

`LoweringBundlePlan` can declare:
- target profiles;
- shared obligations;
- target-specific obligations;
- equivalence requirements;
- cross-target identity bindings;
- validation matrix.

This supports, for example, web/game/DCC variants without pretending one lossy target is the master canonical representation.

M02 owns build/variant production topology.

## 91. Semantic Capability Debt

M04 may record `SemanticCapabilityDebt` when:
- a non-blocking authorized approximation is accepted;
- an optional extension is unavailable;
- an interim representation requires later replacement.

This debt is not M01 QualityDebt and cannot waive M01 gates.

It records:
- affected IR paths;
- authority/acceptance ref;
- expiry/review condition;
- remedy;
- downstream invalidation scope.

## 92. Context-efficient compatibility

`CapabilitySlice` contains only:
- features used by selected IR roots;
- required schema/facets;
- loss policies;
- obligations;
- target profile evidence.

Compatibility analysis should not require the entire project or provider catalog.

## 93. S04 proprietary technology candidates

S04 extends the registry with `IRIS-MIRX-091..120`.

Key families:
- Representation Capability Manifest;
- Required/Used Capability Split;
- Semantic Legality Analyzer;
- Target Representation Profile;
- Semantic Lowering Plan;
- Declarative Lowering Rule Registry;
- No-Downgrade Shield;
- Adaptation Proposal Ledger;
- Capability Gap Ledger;
- Semantic/Concrete Compiler Split;
- Provider Observation Quarantine.

## 94. S04 proposed decisions

- **D-M04-046:** M04 S04 is renamed/narrowed to Representation Capability & Semantic Lowering; M16 solely owns concrete Provider Compiler/workflow compilation.
- **D-M04-047:** M04 performs semantic legality/representability analysis without selecting runtime providers.
- **D-M04-048:** required and merely-used capabilities are separate classes.
- **D-M04-049:** unknown mandatory capability fails closed.
- **D-M04-050:** bounded support is valid only under an upstream-authorized loss class/tolerance.
- **D-M04-051:** M04 cannot lower M01 QualityClass for scarcity/cost/provider limitations.
- **D-M04-052:** M04 cannot relax M03 protected/mandatory constraints.
- **D-M04-053:** target profiles are semantic and versioned, not vendor product identities.
- **D-M04-054:** lowering rules are declarative contracts, not executable provider code.
- **D-M04-055:** provider observations are evidence and cannot mutate canonical truth.
- **D-M04-056:** M14/M15/M16 own empirical capability, routing and concrete compilation respectively.
- **D-M04-057:** exact source IR remains canonical even when a target requires approximation.
- **D-M04-058:** multi-target lowering preserves canonical master semantics and explicit equivalence obligations.
- **D-M04-059:** SemanticCapabilityDebt is distinct from M01 QualityDebt.
- **D-M04-060:** any adaptation that changes semantic intent requires governed upstream revision.

## 95. S04 acceptance obligations

Later implementation must prove:
- deterministic capability manifest;
- required/optional split cannot be forged downstream;
- unknown mandatory facet/profile capability blocks;
- legality analysis makes no canonical mutation;
- exact support vs bounded support distinguishable;
- bounded support requires loss authorization;
- lowering plan contains no provider/runtime/DCC/workflow implementation data;
- target-profile version participates in fingerprint;
- provider observation cannot self-promote capability;
- M01 QualityClass unchanged under target scarcity;
- protected M03 constraints unchanged;
- multi-target bundle exposes target-specific gaps;
- capability slice excludes unrelated IR families;
- concrete provider compilation remains outside M04 imports/dependencies.

## 96. S04 disposition

`COMPLETE_FOR_MODULE_PLANNING`

Next legal planning session: **S05 — IR validation, versioning and round-trip guarantees**.


---

# S05 — IR Validation, Versioning and Round-Trip Guarantees

## 97. S05 goals

S05 must make these statements true:

1. every canonical IR document declares its transport and semantic schema versions;
2. canonical serialization is deterministic and hashable;
3. validation is layered and fail-closed for correctness-critical unknowns;
4. migrations never rewrite old admitted IR in place;
5. round-trip fidelity is measured semantically, not by byte equality alone;
6. extension/facet evolution cannot silently change behavior;
7. adapter/provider output cannot self-certify semantic equivalence;
8. resource limits prevent pathological IR from exhausting the validator.

## 98. Canonical IR Envelope

`IRDocumentEnvelope` wraps a canonical payload with:
- IRIS M04 contract version;
- transport format/version;
- root schema family/version;
- schema manifest fingerprint;
- document/revision identity;
- payload canonical digest;
- dependency manifest digest;
- extension capability manifest;
- provenance/security refs;
- canonicalization profile/version.

Envelope metadata cannot contradict values derivable from the payload.

## 99. Transport vs schema version

Separate axes:
- M04 contract version;
- transport encoding version;
- core schema version;
- facet/dialect family versions;
- lowering-rule version;
- validation-profile version.

A compatibility declaration names every relevant axis.

A newer parser does not imply a newer schema is semantically acceptable.

## 100. Canonical serialization

Canonical serialization requirements:
- deterministic field/property order;
- deterministic set/list policy per field;
- stable enum/token encoding;
- finite numeric values only unless a schema explicitly represents a non-finite concept symbolically;
- normalized explicit units/types;
- stable Unicode handling policy;
- no duplicate map/object keys;
- no location/path-dependent identity;
- canonical bytes yield stable digest across compliant implementations.

Human-readable formatting is not canonical hash material.

## 101. Validation pipeline

M04 validation is phased:

1. `TRANSPORT_VALIDATION`
2. `SCHEMA_VALIDATION`
3. `STRUCTURAL_VALIDATION`
4. `REFERENCE_VALIDATION`
5. `SEMANTIC_VALIDATION`
6. `AUTHORITY_POLICY_VALIDATION`
7. `CAPABILITY_VALIDATION`
8. `RESOURCE_LIMIT_VALIDATION`
9. `ROUND_TRIP_VALIDATION` where an adapter/interchange claim exists.

Each phase returns typed findings, not booleans only.

A fatal earlier-phase failure can short-circuit later expensive phases while preserving diagnostics.

## 102. Validation finding

`IRValidationFinding` carries:
- stable finding code;
- severity/consequence;
- IR path/ref;
- schema family/version;
- evidence;
- source semantic refs;
- quality obligation refs;
- remediation class;
- blocking state;
- validator identity/version.

No free-form-only errors for contract-critical failures.

## 103. Validation profiles

`IRValidationProfile` defines:
- required phases;
- required schema/facet families;
- allowed optional/opaque extensions;
- resource limits;
- round-trip requirements;
- target representation profile refs;
- applicable M01/M03 obligation refs.

Profiles are versioned.

FINAL and PREVIEW profiles cannot be implicitly substituted.

## 104. Schema family evolution

Every canonical schema/facet family declares:
- family identity;
- version;
- compatibility predecessors/successors;
- migration availability;
- deprecation state;
- unknown-field policy;
- behavior compatibility statement;
- extension ownership.

A schema version changes when downstream semantic behavior can change in a way that requires old assets to retain old behavior.

Cosmetic/documentation-only changes need not force semantic schema versions.

## 105. Compatibility classes

`SchemaCompatibilityDeclaration` may state:
- READ_COMPATIBLE;
- WRITE_COMPATIBLE;
- ROUND_TRIP_COMPATIBLE;
- BEHAVIOR_EQUIVALENT;
- MIGRATION_REQUIRED;
- INCOMPATIBLE;
- UNKNOWN.

Compatibility is directional and version-pinned.

No automatic "latest is compatible".

## 106. Unknown field / extension policy

Unknown data classes:
- UNKNOWN_REQUIRED_SCHEMA;
- UNKNOWN_REQUIRED_FACET;
- UNKNOWN_OPTIONAL_OPAQUE;
- UNKNOWN_ADVISORY_METADATA.

Rules:
- required unknowns fail closed;
- optional opaque data can survive only if declared opaque-preservable and not correctness-critical;
- unknown data must not gain authority simply because it survived a round trip;
- serializers must preserve opaque payload identity when preservation is promised.

## 107. Migration

`IRMigrationPlan` declares:
- source family/version;
- target family/version;
- migration steps/rules;
- preconditions;
- semantic equivalence/loss expectations;
- affected paths;
- validation obligations.

Executing a migration creates:
- new IRRevision;
- immutable `IRMigrationReceipt`;
- old revision unchanged.

## 108. Migration receipt

`IRMigrationReceipt` records:
- source/target revision fingerprints;
- source/target schema manifests;
- rule versions;
- changed semantic paths;
- exact/equivalent/lost semantics;
- unresolved gaps;
- validator evidence;
- actor/tool identity.

A migration receipt cannot prove itself valid merely by existing.

## 109. Round-trip contract

`RoundTripContract` states what an adapter/interchange path promises.

Per semantic family/path, requirement can be:
- BYTE_STABLE where meaningful;
- STRUCTURALLY_IDENTICAL;
- SEMANTICALLY_EQUIVALENT;
- EQUIVALENT_WITH_TOLERANCE;
- OPAQUE_PRESERVED;
- LOSS_ALLOWED;
- ONE_WAY_ONLY.

The contract identifies:
- source/target profile versions;
- adapter identity/version;
- tolerance/equivalence profile;
- required witness set;
- disallowed loss.

## 110. Round-trip receipt

`RoundTripReceipt` records:
- source fingerprint;
- exported/intermediate fingerprint;
- reimported fingerprint;
- adapter chain;
- schema/profile versions;
- path-by-path comparison;
- tolerated differences;
- lost/unmapped data;
- witness evidence;
- validation results.

It is evidence, not automatic promotion authority.

## 111. Semantic witness set

`SemanticWitnessSet` is a compact set of invariants used to prove round-trip fidelity.

Examples:
- stable entity/asset identity;
- transform/spatial equivalence;
- skeleton hierarchy/joint semantic identity;
- material terminal/binding equivalence;
- camera physical properties;
- light physical/intent properties;
- temporal markers/ranges;
- audio/music sync;
- protected M03 constraints;
- M01 quality-obligation bindings.

Witnesses must be generated from canonical sources, not hand-written after seeing output.

## 112. Equivalence profile

`IREquivalenceProfile` states:
- fields/paths compared;
- exact vs tolerant comparison;
- canonical unit/color/time conversions;
- ordering significance;
- opaque-extension policy;
- floating/quantity tolerances;
- semantic ignore rules.

Equivalence profiles are versioned and cannot omit mandatory paths silently.

## 113. Derived vs canonical data

Data classes:
- CANONICAL_AUTHORED;
- CANONICAL_LOWERED;
- DERIVED_REBUILDABLE;
- CACHE_ONLY;
- EXTERNAL_OBSERVATION.

Derived/cache values may be regenerated.
Canonical authored/lowered values require governed revision/migration.

Provider observation never becomes canonical merely because it is newer.

## 114. Integrity and fingerprints

M04 supports:
- document canonical digest;
- schema manifest digest;
- subgraph digest;
- interface digest;
- resource manifest digest;
- translation/lowering-plan digest;
- validation evidence digest.

Digest algorithm/profile is versioned.

A digest mismatch fails before semantic trust.

## 115. Resource and complexity limits

Validator profiles bound:
- node count;
- edge count;
- containment depth;
- graph fanout;
- schema/facet count;
- property count/size;
- string/blob metadata size;
- temporal sample count;
- recursion/nesting;
- external reference count;
- total inline payload size.

Limits are deterministic and configurable by admitted profile.

Exceeding a limit is a typed refusal/gap, not an uncontrolled crash.

## 116. Cycle and reachability validation

Mandatory graph checks:
- containment/transform acyclic;
- schema inheritance/application cycles rejected where illegal;
- explanation/lowering provenance reachability;
- semantic relationship cycles evaluated by edge-family policy;
- no dangling required refs;
- no duplicate canonical IDs;
- no prototype/instance self-reference loops;
- no migration ancestry loops.

## 117. Validation determinism

Same canonical input + same validator/profile/version must yield:
- same findings;
- same finding order;
- same fingerprints;
- same readiness result.

Clock time, hash-map order, filesystem path and network/provider state cannot alter deterministic validation unless explicitly supplied as versioned evidence input.

## 118. IR readiness report

`IRReleaseReadinessReport` aggregates:
- validation phases assessed;
- blocking findings;
- unresolved gaps;
- mandatory capability coverage;
- stale refs/dependencies;
- round-trip obligations where required;
- provenance/rights/security handoff refs.

It is M04 evidence only.

It cannot replace:
- M01 quality promotion;
- M02 build/release promotion;
- M53 rights/provenance;
- M54 security;
- M59 side-effect authorization.

## 119. Adapter qualification boundary

A round-trip-capable adapter must be qualified later under the owning integration module.

M04 defines qualification evidence contract:
- supported source/target profiles;
- schema versions;
- witness coverage;
- deterministic test corpus;
- known losses;
- failure modes;
- adapter hash/version;
- qualification status/ref.

M04 does not ship provider/DCC adapters in the semantic kernel merely to test the contract.

## 120. Serialization formats

The frozen semantic model is transport-neutral.

Initial implementation may select one canonical repository serialization if architecture/tests justify it, but:
- semantic identity is not tied to JSON field layout;
- binary transport can be added later through versioned encoding;
- encoding version is separate from schema version;
- canonical bytes/fingerprint rules must be explicit.

## 121. Fuzz / adversarial validation obligations

Later implementation must include hostile cases:
- duplicate IDs/keys;
- non-finite numbers;
- invalid Unicode/encoding where applicable;
- deeply nested facets;
- huge graphs/fanout;
- cycle bombs;
- unknown mandatory extensions;
- digest mismatch;
- stale migration receipts;
- forged adapter qualification;
- round-trip receipts that omit required witnesses;
- downgrade of mandatory semantics during import.

## 122. S05 proprietary technology candidates

S05 extends the registry with `IRIS-MIRX-121..150`.

Key families:
- Multi-Axis Version Vector;
- Canonical IR Envelope;
- Layered Validator;
- Schema Evolution Ledger;
- Immutable Migration Receipt;
- Semantic Round-Trip Contract;
- Witness-Driven Round-Trip Proof;
- Equivalence Profile;
- Canonical/Derived Data Firewall;
- Adversarial Complexity Shield;
- Deterministic Readiness Evidence.

## 123. S05 proposed decisions

- **D-M04-061:** transport encoding version and semantic schema versions are independent.
- **D-M04-062:** canonical serialization is deterministic, finite-number-safe and hashable.
- **D-M04-063:** validation is layered with typed stable findings.
- **D-M04-064:** required unknown schemas/facets fail closed.
- **D-M04-065:** optional opaque data survives only under an explicit preservation policy.
- **D-M04-066:** schema compatibility is directional/version-pinned and never inferred from "latest".
- **D-M04-067:** semantic behavior change is the primary trigger for schema version/migration.
- **D-M04-068:** migrations create new immutable revisions and receipts.
- **D-M04-069:** round-trip success is semantic, not merely parse/byte success.
- **D-M04-070:** round-trip contracts declare exact/tolerant/opaque/loss semantics per path/family.
- **D-M04-071:** witness sets are derived from canonical obligations before adapter output exists.
- **D-M04-072:** adapters cannot self-certify qualification/equivalence.
- **D-M04-073:** derived/cache/provider observations cannot overwrite canonical authored/lowered facts.
- **D-M04-074:** resource/depth/fanout limits are deterministic validation inputs.
- **D-M04-075:** IR readiness is evidence and never replaces M01/M02/M53/M54/M59 authority.

## 124. S05 acceptance obligations

Later implementation must prove:
- deterministic canonical serialization/digest;
- NaN/Infinity refusal;
- duplicate key/ID refusal;
- schema-family/version pinning;
- unknown mandatory schema/facet failure;
- optional opaque extension preservation only under policy;
- directional compatibility;
- migration creates new revision and leaves source bytes/fingerprint unchanged;
- migration receipt cannot self-authorize invalid result;
- exact semantic witness set is reproducible;
- round-trip comparison catches material/camera/transform/time/sync loss;
- tolerance comparison is unit/color/time aware;
- adapter cannot omit required witnesses;
- derived cache is rebuildable and not canonical authority;
- complexity limits reject pathological graphs deterministically;
- deterministic finding order;
- release-readiness report cannot claim M01/M02 promotion.

## 125. S05 disposition

`COMPLETE_FOR_MODULE_PLANNING`

S01-S05 are now complete for planning.

Next legal gate: **Final Technology Review**. No M04 implementation is authorized.
