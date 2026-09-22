# M04 — Multimodal IR / Scene IR

Status: `S02_COMPLETE_S03_NEXT`
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
