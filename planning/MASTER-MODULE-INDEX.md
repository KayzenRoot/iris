# IRIS 1.0 — MASTER MODULE INDEX

Status: `ACTIVE_DISCOVERY`
Version target: `IRIS 1.0`
Planning model: `FULL_VERSION_NO_MVP`
Modules: `61 (M00–M60)`
Sessions per module: `5`
Total planned module sessions: `305`

## Governing intent

IRIS 1.0 is planned as the complete first production version of Hive IRIS, not an MVP. Extreme output quality is a product invariant. Draft/preview lanes may trade quality for iteration speed, but a lower-quality draft never becomes a final master merely because it completed successfully.

This index carries forward the useful UGAS V2 vision while treating IRIS as a new product. Each module will be discussed and frozen through its five sessions before implementation work for that module is admitted.

## Planning rule for every module

Every S01–S05 cycle must produce or update, where applicable:
- requirements and scope;
- architecture/contracts;
- proprietary-technology candidates and prior-art status;
- hardware/performance strategy;
- quality metrics and benchmarks;
- security/provenance/rights constraints;
- tests/evidence obligations;
- dependencies and migration/recovery considerations;
- accepted decisions/ADRs;
- checkpoint delta.

No module is implemented merely because it appears in this index.

## AREA A — PRODUCT CONSTITUTION & PRODUCTION OS

### M00 — Product Constitution & IRIS 1.0 Contract
- S01 — S01 Vision, non-MVP boundary and complete V1 promise
- S02 — S02 Users, production domains and canonical terminology
- S03 — S03 Source hierarchy, governance and immutable principles
- S04 — S04 Product invariants, forbidden shortcuts and quality doctrine
- S05 — S05 V1 scope admission, freeze rules and module dependency map

### M01 — Extreme Quality North Star & Fidelity System
- S01 — S01 Quality dimensions and measurable fidelity vocabulary
- S02 — S02 Fidelity Contract and output classes
- S03 — S03 Human-perceptual quality, visual review and approval boundaries
- S04 — S04 Quality budgets, acceptance thresholds and uncertainty
- S05 — S05 Quality evidence, regression policy and North Star freeze

### M02 — Project OS & Production Graph
- S01 — S01 Project/production identity and lifecycle
- S02 — S02 Production Graph node/dependency model
- S03 — S03 Branches, variants, snapshots and rollback
- S04 — S04 Creative Build System and incremental rebuild semantics
- S05 — S05 Production state machine, promotion and archive

### M03 — Creative Brief, Intent & Constraint Compiler
- S01 — S01 Creative brief schema and intent capture
- S02 — S02 Constraint taxonomy and negative constraints
- S03 — S03 Fidelity Contract compilation
- S04 — S04 Provider-neutral execution intent and explainability
- S05 — S05 Conflict detection, override policy and brief versioning

### M04 — Multimodal IR / Scene IR
- S01 — S01 Scene, Character and Asset IR
- S02 — S02 Camera, Lighting, Material and Spatial IR
- S03 — S03 Motion, Audio, Music and Narrative IR
- S04 — S04 Representation Capability & Semantic Lowering (concrete Provider Compiler remains M16)
- S05 — S05 IR validation, versioning and round-trip guarantees

### M05 — Asset DNA 2.0 & Cross-Modal Identity
- S01 — S01 Asset DNA schema and identity invariants
- S02 — S02 Character, creature, object, product and environment DNA
- S03 — S03 SceneDNA, Motion DNA, Voice DNA and Brand DNA links
- S04 — S04 Identity anchors, mutation boundaries and drift detection
- S05 — S05 DNA branching, compatibility and reusable DNA marketplace contract

### M06 — Production State, Versioning & Incremental Media Build
- S01 — S01 Content-addressed revisions and immutable masters
- S02 — S02 Dependency fingerprints and impact analysis
- S03 — S03 Incremental regeneration and selective rebuild
- S04 — S04 Reproducibility receipts and deterministic reconstruction
- S05 — S05 Rollback, lineage-aware cleanup and release state

## AREA B — HARDWARE, COMPUTE & EXECUTION

### M07 — Hardware Genome & Runtime Discovery
- S01 — S01 GPU/CPU/RAM/storage/runtime discovery
- S02 — S02 CUDA/ROCm/DirectML/Metal capability mapping
- S03 — S03 Driver, precision, encoder/decoder and topology detection
- S04 — S04 Thermal, power and memory-pressure telemetry
- S05 — S05 Hardware Genome schema, versioning and confidence

### M08 — Microbenchmark Lab & Capability Envelope
- S01 — S01 First-run safe microbenchmarks
- S02 — S02 Image/video/3D/audio benchmark probes
- S03 — S03 Capability Envelope and safe workload limits
- S04 — S04 Continuous performance fingerprint and drift
- S05 — S05 Benchmark calibration, aging and invalidation

### M09 — Resource Digital Twin & Dynamic VRAM Governor
- S01 — S01 Resource Digital Twin state model
- S02 — S02 VRAM leases, reservations and model residency
- S03 — S03 RAM/NVMe spill, offload and prefetch planning
- S04 — S04 Dynamic tile/chunk/batch/precision control
- S05 — S05 Memory-pressure recovery, cleanup and leak detection

### M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield
- S01 — S01 Workload Signature Engine
- S02 — S02 Hardware-aware execution plan compilation
- S03 — S03 Predictive OOM, thermal and quality-risk models
- S04 — S04 ECO/BALANCED/QUALITY/MAX/CUSTOM policy semantics
- S05 — S05 Observed-result learning loop and explainable decisions

### M11 — Background Worker Fabric & Process Lifecycle
- S01 — S01 Long-lived supervisor and job process model
- S02 — S02 Headless/background worker startup and IPC
- S03 — S03 Concurrency limits, priorities and resource leases
- S04 — S04 Process reaper, zombie detection and shell-free execution
- S05 — S05 Cancellation, timeout, crash recovery and workstation coexistence

### M12 — Compute Orchestration: Local, Multi-GPU, LAN, Remote & Cloud
- S01 — S01 Worker registry and capability advertisements
- S02 — S02 Placement, queues, quotas and priority scheduling
- S03 — S03 Multi-GPU and heterogeneous execution
- S04 — S04 LAN/remote/cloud spillover and federated IRIS nodes
- S05 — S05 Failover, preemption, cost/quality placement and trust

### M13 — Performance, Cache & Execution Efficiency
- S01 — S01 Warm model/cache strategy and cache locality
- S02 — S02 Compilation, attention and backend selection
- S03 — S03 Intermediate reuse and generation delta cache
- S04 — S04 CPU/GPU overlap, I/O scheduling and storage efficiency
- S05 — S05 Performance budgets, profiling and anti-regression gates

## AREA C — MODEL & WORKFLOW INTELLIGENCE

### M14 — Model Registry & Empirical Model Cards
- S01 — S01 Model identity, versions, hashes, license and provenance
- S02 — S02 Capability Genome and task taxonomy
- S03 — S03 Empirical quality/latency/VRAM model cards
- S04 — S04 Hardware compatibility and reliability evidence
- S05 — S05 Model drift, deprecation and lifecycle governance

### M15 — Multi-Model Director & Champion/Challenger Routing
- S01 — S01 Task-model affinity graph
- S02 — S02 Candidate tournament and Pareto quality/cost routing
- S03 — S03 Champion/challenger and canary evaluation
- S04 — S04 Cascades, fallback, ensemble and escalation
- S05 — S05 Director Decision Ledger and learning loop

### M16 — Workflow Registry & Provider Compiler
- S01 — S01 Canonical workflow format and immutable revisions
- S02 — S02 Workflow capability contracts and required nodes
- S03 — S03 Provider compiler from IR/Fidelity Contract
- S04 — S04 Compatibility graph and workflow migration
- S05 — S05 Workflow qualification, signing and rollback

### M17 — ComfyUI Runtime Integration
- S01 — S01 Local ComfyUI server/API contract
- S02 — S02 Queue, websocket/progress and job state integration
- S03 — S03 Workflow submission, outputs and artifact ingestion
- S04 — S04 Version pinning, custom-node compatibility and canary upgrades
- S05 — S05 Resilience, health, unload/free-memory and recovery

### M18 — Model Acquisition, Integrity, License & Supply Chain
- S01 — S01 Trusted model/source registry and hashes
- S02 — S02 Download/resume/storage and disk planning
- S03 — S03 License/commercial-use policy and rights gates
- S04 — S04 Malware/unsafe-code/custom-node supply-chain controls
- S05 — S05 Model package qualification and reproducible installation

### M19 — Fine-Tuning, LoRA, Adapters & Style/Identity Training
- S01 — S01 Training-use cases and when not to train
- S02 — S02 Dataset lineage, consent and quality curation
- S03 — S03 LoRA/adapter/style/identity training plans
- S04 — S04 Hardware-adaptive training/offload/checkpointing
- S05 — S05 Evaluation, overfit/drift gates and registry promotion

## AREA D — IMAGE & PHOTOGRAPHY

### M20 — Image & Photography Studio
- S01 — S01 Text-to-image and image-to-image master pipeline
- S02 — S02 Portrait, editorial, concept art and environment workflows
- S03 — S03 Product photography, key art, posters and thumbnails
- S04 — S04 Multi-candidate generation and composition planning
- S05 — S05 Production masters, variants and archival

### M21 — Reference Fusion, Pose, Depth, Edge & Segmentation Control
- S01 — S01 Multi-reference identity/style fusion
- S02 — S02 Pose and anatomy control
- S03 — S03 Depth/normal/edge/line control
- S04 — S04 Segmentation, masks and spatial constraints
- S05 — S05 Cross-control arbitration and reference-strength learning

### M22 — Composition, Typography, Product & Design Intelligence
- S01 — S01 Composition and visual hierarchy
- S02 — S02 Text/logo/layout fidelity and typography
- S03 — S03 Product geometry/packaging consistency
- S04 — S04 Brand-safe photographic direction and lighting intent
- S05 — S05 Design validation and reusable composition templates

### M23 — Image Repair, Retouch, Relight, Upscale & Transparency
- S01 — S01 Inpaint/outpaint and local defect repair
- S02 — S02 Relighting, color matching and restoration
- S03 — S03 Background removal, alpha quality and edge treatment
- S04 — S04 Super-resolution/detail enhancement without identity drift
- S05 — S05 Minimal-regeneration masks and revision provenance

### M24 — Image Quality Evals & Visual Acceptance
- S01 — S01 Anatomy, identity and composition judges
- S02 — S02 Artifact, clipping, text and transparency judges
- S03 — S03 Reference similarity and structural metrics
- S04 — S04 Human visual review protocol and contact sheets
- S05 — S05 Golden image corpus, drift and regression gates

## AREA E — 3D, BLENDER, MOTION & SPATIAL

### M25 — 3D & Spatial Asset Studio
- S01 — S01 Image/text-to-3D intake and target classes
- S02 — S02 Mesh, scene and environment generation strategies
- S03 — S03 Cross-view consistency and 2D-to-3D identity bridge
- S04 — S04 Spatial metadata, scale, pivots and collision intent
- S05 — S05 Production-ready master asset contract

### M26 — Blender 5.2 LTS Headless Automation & MCP
- S01 — S01 Blender 5.2 LTS production baseline and compatibility
- S02 — S02 `--background` worker architecture and Python/bpy jobs
- S03 — S03 MCP control plane for inspection and interactive tasks
- S04 — S04 Headless-first job isolation, timeouts and process cleanup
- S05 — S05 Blend-file integrity, security, recovery and version migration

### M27 — Geometry, Retopology, UV, LOD & Topology Quality
- S01 — S01 Mesh health, manifoldness and geometry standards
- S02 — S02 Automated/manual retopology strategies
- S03 — S03 UV unwrap, texel density and packing
- S04 — S04 Semantic LOD generation and silhouette preservation
- S05 — S05 Topology Quality Court and game/web budgets

### M28 — Materials, PBR, Textures & Baking
- S01 — S01 Material IR and PBR channel standards
- S02 — S02 AI texture generation and projection
- S03 — S03 UV-aware texture repair and seam handling
- S04 — S04 Bake maps, atlases, compression and variants
- S05 — S05 Material fidelity, cross-renderer consistency and QA

### M29 — Rigging, Skinning, Anatomy & Deformation
- S01 — S01 Skeleton/rig standards by asset class
- S02 — S02 Auto-rig and control-rig strategies
- S03 — S03 Skin weights and deformation quality
- S04 — S04 Anatomy constraints, joints, muscles and facial rigs
- S05 — S05 Deformation stress tests and repair

### M30 — Animation & Motion Studio
- S01 — S01 Motion DNA and semantic motion briefs
- S02 — S02 Locomotion, combat, loops and cinematic motion
- S03 — S03 Mocap, motion transfer and retargeting
- S04 — S04 Facial animation, lip motion and expression
- S05 — S05 Motion continuity, foot sliding/jitter and smoothness QA

### M31 — Camera, Lighting & Rendering
- S01 — S01 Camera Intent Engine and shot framing
- S02 — S02 Lighting IR, rigs and relighting
- S03 — S03 Cycles/EEVEE strategy and hardware-aware renderer choice
- S04 — S04 Render layers, AOVs, denoise and compositing inputs
- S05 — S05 Render fidelity, noise, color-management and master validation

### M32 — VFX, Physics, Particles & Geometry Nodes
- S01 — S01 VFX graph and reusable effect families
- S02 — S02 Geometry Nodes procedural generation
- S03 — S03 Physics, cloth, hair, rigid/soft body and simulation
- S04 — S04 Particles, fluids, smoke, fire and stylized effects
- S05 — S05 Cache, deterministic simulation, performance and QA

### M33 — Maya & DCC Interoperability
- S01 — S01 DCC adapter contract and capability discovery
- S02 — S02 Maya bridge/MCP strategy when installed
- S03 — S03 USD, Alembic, FBX, glTF and interchange semantics
- S04 — S04 Round-trip fidelity and naming/unit/material mapping
- S05 — S05 DCC version compatibility, validation and fallback

### M34 — Web 3D / WebGPU Asset Compiler
- S01 — S01 Web asset budgets and scene targets
- S02 — S02 glTF/GLB, Draco/Meshopt/KTX2 pipeline
- S03 — S03 LOD, texture streaming and runtime variants
- S04 — S04 Three.js/R3F/WebGPU integration contracts
- S05 — S05 Web performance, visual parity and device fallback

### M35 — Game Engine Asset Delivery
- S01 — S01 Godot/Unity/Unreal destination profiles
- S02 — S02 Import presets, skeleton/material and coordinate mapping
- S03 — S03 Collision, LOD, animation and asset bundle packaging
- S04 — S04 Engine-side validation and round-trip testing
- S05 — S05 Isometric/2.5D/3D game production profiles and Neryn-class requirements

## AREA F — VIDEO & CINEMA

### M36 — Video & Cinema Studio
- S01 — S01 Shot planning and production timeline
- S02 — S02 Text/image/video-to-video routing
- S03 — S03 Camera motion, scene extension and transitions
- S04 — S04 Upscale, stabilization and master render
- S05 — S05 Long-form assembly, shot graph and delivery masters

### M37 — Temporal Consistency & Shot Continuity
- S01 — S01 Temporal Identity Lock and character continuity
- S02 — S02 Shot Continuity Graph and temporal state memory
- S03 — S03 Object/environment continuity and camera-state continuity
- S04 — S04 Temporal artifact radar and selective frame repair
- S05 — S05 Cross-shot quality, continuity scoring and acceptance

### M38 — Editing, Compositing, Color & Encode
- S01 — S01 Editorial timeline and shot selection
- S02 — S02 Compositing/VFX integration and mattes
- S03 — S03 Color pipeline, grading and display transforms
- S04 — S04 Codec/container/bitrate and proxy/master strategy
- S05 — S05 Subtitle/caption/timing, QC and render packaging

## AREA G — DIGITAL HUMANS & AUDIO

### M39 — Digital Humans & Virtual Identity
- S01 — S01 M05-bound Persona Continuity Engine and canonical persona
- S02 — S02 Face/body/hair/skin/clothing consistency
- S03 — S03 Expression, gesture, mannerism and acting system
- S04 — S04 Cross-modal identity binding for image/3D/video/voice
- S05 — S05 Virtual influencer/avatar/streamer/corporate spokesperson continuity and rights

### M40 — Voice Studio & Dubbing
- S01 — S01 Voice DNA and authorized voice design/cloning
- S02 — S02 TTS, speech-to-speech and narration
- S03 — S03 Emotion, prosody, pacing and character direction
- S04 — S04 Multilingual voice persistence and dubbing
- S05 — S05 Voice drift, intelligibility, rights and audio QA

### M41 — Music Studio
- S01 — S01 Artist DNA, Music DNA and sonic identity
- S02 — S02 Composition, arrangement and instrumental generation
- S03 — S03 Vocals, stems, remix and versioning
- S04 — S04 Adaptive scores, game music and album continuity
- S05 — S05 Mix/master, loudness, rights and music QA

### M42 — Sound Design & Audio Post
- S01 — S01 SFX/Foley generation and libraries
- S02 — S02 Ambience, environmental and spatial audio
- S03 — S03 Layering, cleanup, denoise and restoration
- S04 — S04 Game/cinematic audio packaging and loudness
- S05 — S05 Audio Quality Court and cross-media sync

## AREA H — STORY, CONTENT, BRAND & COMMERCIAL MEDIA

### M43 — Narrative, Script & Canon Engine
- S01 — S01 Concept, synopsis, script and scene structure
- S02 — S02 Canon Graph, Story State Ledger and world state
- S03 — S03 Character arcs, dialogue and episode memory
- S04 — S04 Narrative contradiction and continuity detection
- S05 — S05 Branching narrative, series bible and production binding

### M44 — Faceless Content Factory
- S01 — S01 Channel DNA, niche and content strategy
- S02 — S02 Research/topic pipeline and script generation
- S03 — S03 Narration/presenter, scenes, B-roll, music and subtitles
- S04 — S04 Shorts/long-form/series compilation and differentiation
- S05 — S05 Trend scout, fatigue/repetition monitor and autonomous channel modes

### M45 — Advertising & Synthetic UGC Studio
- S01 — S01 Campaign DNA, Creative Genome and audience intents
- S02 — S02 Hooks, CTA, persistent virtual spokesperson and product demonstration
- S03 — S03 Creative families, variants and platform crops
- S04 — S04 Campaign twin, attribution, fatigue and creative evolution
- S05 — S05 Autonomous campaign operation, offer optimization and approval boundaries

### M46 — Brand & IP Studio
- S01 — S01 Brand DNA, visual/sonic/verbal identity
- S02 — S02 Typography, palette, photography and style constraints
- S03 — S03 Character/IP asset graph and approved references
- S04 — S04 Cross-media Brand Lock and forbidden patterns
- S05 — S05 Brand Consistency Court, IP governance and reusable brand packs

### M47 — Localization & Culturalization Studio
- S01 — S01 Translation, terminology and locale profiles
- S02 — S02 Dubbing/subtitle/lip adaptation
- S03 — S03 Image text replacement and localized graphics
- S04 — S04 Cultural context/risk, currency/measurement/local references
- S05 — S05 Cross-language identity lock and multilingual timing QA

## AREA I — QUALITY, REPAIR & BENCHMARKS

### M48 — Quality Court & Automated Review
- S01 — S01 Judge architecture and evidence contracts
- S02 — S02 Identity/anatomy/composition/temporal/3D/audio judges
- S03 — S03 Confidence arbitration and uncertainty
- S04 — S04 Human Approval Boundary and escalation
- S05 — S05 Quality Evidence Bundle, promotion and regression memory

### M49 — Self-Correction, Partial Repair & Minimal Regeneration
- S01 — S01 Defect localization and failure fingerprints
- S02 — S02 Error-to-Action Compiler and repair planning
- S03 — S03 Region/frame/mesh/audio selective repair
- S04 — S04 Alternate model/parameter/constraint mutation
- S05 — S05 Repair cost, proof of improvement and revalidation

### M50 — Render Cascade & Cost-to-Quality Optimization
- S01 — S01 Draft→Preview→Evaluate→Select→Enhance→Master cascade
- S02 — S02 Candidate Tournament and selective enhancement
- S03 — S03 Cost-to-Quality Predictor and quality budget allocator
- S04 — S04 Waste render detector and compute ROI
- S05 — S05 Escalation to remote/API compute without lowering final quality

### M51 — Benchmark Lab, Evals & Regression Corpus
- S01 — S01 Golden multimodal benchmark corpus
- S02 — S02 Visual/anatomy/motion/3D/audio benchmark suites
- S03 — S03 Hardware/model/workflow comparative harness
- S04 — S04 Quality/performance regression radar
- S05 — S05 Benchmark governance, reproducibility and release gates

## AREA J — MEMORY, PROVENANCE, SECURITY & DATA

### M52 — HIVE Multimodal Memory & Creative RAG Integration
- S01 — S01 IRIS↔HIVE project/context contract
- S02 — S02 Asset/reference/image/audio/3D metadata retrieval
- S03 — S03 Creator/project/character/production memory
- S04 — S04 Minimum sufficient context, caching and token economy
- S05 — S05 Provenance-aware retrieval, checkpoint handoff and stale-context invalidation

### M53 — Provenance, Rights, Consent & C2PA
- S01 — S01 Media Provenance Graph and transformation ledger
- S02 — S02 Model/reference/prompt/seed/parameter lineage
- S03 — S03 Rights, license and consent ledger
- S04 — S04 Content credentials/C2PA bridge and export policy
- S05 — S05 Provenance confidence, audit and lineage-safe derivatives

### M54 — Security, Identity & Restricted Content
- S01 — S01 Threat model, RBAC/capabilities and project isolation
- S02 — S02 Secrets, provider credentials and local trust boundaries
- S03 — S03 Untrusted model/node/DCC file sandbox policy
- S04 — S04 Likeness/identity/consent protections and restricted vaults
- S05 — S05 Policy-aware generation/export, audit and incident response

### M55 — Media CAS, Storage, Cache & Archive Fabric
- S01 — S01 Content-addressable media store and immutable masters
- S02 — S02 Perceptual dedup and generation delta storage
- S03 — S03 Hot/warm/cold tiers, proxies and previews
- S04 — S04 Adaptive cache, reference locality and disk budgets
- S05 — S05 Lineage-aware garbage collection, archive and recovery

## AREA K — CONTROL CENTER, AUTONOMY, APIs & RELEASE

### M56 — Observability, Telemetry & IRIS Control Center
- S01 — S01 Executive/project/production dashboard
- S02 — S02 GPU/VRAM/RAM/CPU/thermal/worker observability
- S03 — S03 Model/workflow quality, latency and cost analytics
- S04 — S04 Production Graph, Quality Court, provenance and storage views
- S05 — S05 Bottleneck intelligence, quality drift radar and zero-invented-data policy

### M57 — Automation, Agents & Autonomous Production
- S01 — S01 Production Director and task decomposition
- S02 — S02 Render/review/repair/content agents
- S03 — S03 Multi-agent Production Graph and scope guard
- S04 — S04 Autonomous creative loop, trend hunting and real-time avatar modes
- S05 — S05 Stop Conditions, human approval boundaries and safe autonomy

### M58 — API, SDK, MCP & Plugin Ecosystem
- S01 — S01 Stable domain APIs and contracts
- S02 — S02 MCP surfaces for IRIS, Blender and external executors
- S03 — S03 Python/TypeScript SDKs and job/event clients
- S04 — S04 Plugin/provider/DCC extension lifecycle and permissions
- S05 — S05 Compatibility, versioning, conformance tests and developer docs

### M59 — Export, Publishing & Adaptive Delivery Compiler
- S01 — S01 Destination Capability Profiles
- S02 — S02 Adaptive Media Compiler for game/web/mobile/social
- S03 — S03 Resolution/aspect/codec/texture/3D/audio variant generation
- S04 — S04 Publishing packages, metadata, thumbnails and platform policies
- S05 — S05 Export Quality Gate, rollback and delivery provenance

### M60 — Deployment, Recovery, System Integration & IRIS 1.0 Final Acceptance
- S01 — S01 Local installation/update/uninstall and background services
- S02 — S02 Backup, restore, migration and disaster recovery
- S03 — S03 Full HIVE↔CORE↔IRIS integration validation
- S04 — S04 End-to-end production acceptance on 8 GB and higher hardware classes
- S05 — S05 Security/performance/quality final audit, release freeze and IRIS 1.0 completion

## Cross-module completion rule

IRIS 1.0 is complete only when all NECESSARY V1 modules have their admitted implementation completed, tested, documented, deployed and validated against the final Definition of Done. No known HIGH/CRITICAL finding may remain open.
