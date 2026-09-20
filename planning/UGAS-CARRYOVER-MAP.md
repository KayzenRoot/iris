# UGAS → IRIS 1.0 Carryover Map

Status: `CANONICAL_DISCOVERY_MAP`

## Reuse classification

- `REUSE_AS_IS`: concept/contract already strong enough to preserve substantially.
- `ADAPTER`: preserve semantics but adapt naming/contracts to IRIS.
- `REWRITE`: goal retained, implementation/architecture must be redesigned.
- `REFERENCE_ONLY`: useful evidence, not a V1 IRIS contract.
- `RETIRE`: intentionally not carried forward.

## UGAS V1 evidence reuse

| UGAS V1 capability | IRIS treatment | Destination |
|---|---|---|
| Model manifest with hashes/license/hardware evidence | ADAPTER | M14, M18 |
| ComfyUI dependency-free HTTP client patterns | ADAPTER | M17 |
| FAST/QUALITY model lanes | ADAPTER | M15, M50 |
| Master asset spec / Art DNA | ADAPTER | M05, M20 |
| Candidate hard gates + human visual approval boundary | REUSE_AS_IS concept | M24, M48 |
| Provenance/revision evidence | REUSE_AS_IS concept | M53 |
| GPU/VRAM/process telemetry | ADAPTER | M07, M09, M56 |
| Fail-closed UNKNOWN/GAP states | REUSE_AS_IS concept | all governed runtime modules |
| Docker always-on observability pattern | ADAPTER | M56, M60 |
| V1 scope blocks on Blender/3D/audio | RETIRE | superseded by complete IRIS 1.0 scope |
| Version-specific model parameters | REFERENCE_ONLY | M14 empirical model cards |

## UGAS V2 30-category carryover

| UGAS V2 category | IRIS 1.0 destination |
|---|---|
| 01 Project & Production OS | M02, M06 |
| 02 Hardware Intelligence & Adaptive Compute | M07–M10 |
| 03 Compute Orchestration Fabric | M11–M13 |
| 04 Model Registry & Model Intelligence | M14 |
| 05 Multi-Model Director | M15 |
| 06 Multimodal Intermediate Representation | M04, M16 |
| 07 Asset DNA 2.0 | M05 |
| 08 Digital Human & Virtual Identity | M39 |
| 09 Image & Photography Studio | M20–M24 |
| 10 Video & Cinema Studio | M36–M38 |
| 11 Animation & Motion Studio | M30 |
| 12 3D & Spatial Asset Studio | M25–M35 |
| 13 Voice Studio | M40 |
| 14 Music Studio | M41 |
| 15 Sound Design & Audio Post | M42 |
| 16 Narrative, Script & Story Engine | M43 |
| 17 Faceless Content Factory | M44 |
| 18 Advertising & Synthetic UGC | M45 |
| 19 Brand & IP | M46 |
| 20 Localization & Culturalization | M47 |
| 21 Quality Court | M48 |
| 22 Regeneration, Repair & Self-Correction | M49 |
| 23 Render Cascade & Cost Optimization | M50 |
| 24 Memory, RAG & Creative Intelligence | M52 |
| 25 Provenance, Rights & Content Credentials | M53 |
| 26 Security, Identity & Restricted Content | M54 |
| 27 Storage, Cache & Media Data Fabric | M55 |
| 28 Observability, Telemetry & Dashboard | M56 |
| 29 Automation, Agents & Autonomous Production | M57 |
| 30 Platform Export, Publishing & Delivery | M59 |

## Former V2 'important/future' ideas promoted into IRIS 1.0 planning

The user explicitly requested the complete V2 vision in IRIS 1.0. Therefore these are not silently discarded:
- advanced multi-node/federated compute → M12;
- advanced localization/culturalization → M47;
- advanced 3D → M25–M35;
- automatic creative experimentation → M15, M50, M57;
- richer publishing integrations → M59;
- autonomous channels and trend hunting → M44, M57;
- virtual/real-time avatar/streamer modes → M39, M57;
- campaign automation/optimization → M45, M57;
- reusable DNA marketplace contract → M05, M58;
- federated IRIS nodes → M12.

## Proprietary technology carryover register

The following UGAS V2 candidate concepts remain explicitly represented in IRIS planning and require prior-art review before novelty claims:

Asset DNA 2.0; Hardware Genome; Adaptive Execution Fabric; Dynamic VRAM Governor; Hardware-Aware Model Resolver; Precision Auto-Tuner; Adaptive Offload Planner; First-Run Microbenchmark; Continuous Performance Fingerprint; Thermal-Aware Scheduler; Model Capability Genome; Empirical Model Card; Multi-Model Director; Scene IR; Provider Compiler; Constraint Compiler; Persistent Identity Engine; Identity Anchor Mesh; Cross-Modal Identity Binding; Temporal Identity Lock; SceneDNA; Motion DNA; Voice DNA; Artist DNA; Music DNA; Brand DNA; Channel DNA; Campaign DNA; Narrative Continuity Engine; Canon Graph; Production Graph; Creative Build System; Incremental Media Rebuild; Quality Court; Quality Evidence Bundle; Defect Localization Engine; Partial Repair Planner; Minimal Regeneration Engine; Render Cascade Engine; Cost-to-Quality Predictor; Quality Budget Allocator; Creator Memory Engine; Multimodal Reference Retrieval; Media Provenance Graph; Rights Ledger; Consent-Bound Generation; Media Content-Addressable Storage; Generation Delta Storage; Adaptive Media Cache; Adaptive Media Compiler.

IRIS may rename, merge or supersede these mechanisms only through an explicit decision recorded during module planning.
