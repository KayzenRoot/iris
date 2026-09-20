# IRIS-WO-0002 — IRIS 1.0 Research Baseline + Master Module Map

Status: `COMPLETED_APPROVED`

## OBJECTIVE
Create the first canonical IRIS 1.0 product-planning baseline: research findings, UGAS V1/V2 carryover, quality/runtime invariants and the complete module/session map.

## CONTEXT
Authorized base: `f41c85f64f764400cc600eb52d98cadd0f78a49e`. IRIS-WO-0001 completed repository bootstrap and promoted `PRODUCT_DISCOVERY_READY`.

## SCOPE
- inspect UGAS V1 evidence and current repository;
- recover UGAS V2 blueprint;
- research current ComfyUI/Blender production direction;
- establish explicit no-MVP/full-V1 rule;
- establish extreme-quality and 8 GB hardware invariants;
- define headless-first Blender/runtime direction;
- map all relevant UGAS V2 capabilities into IRIS;
- create M00–M60 with exactly five planning sessions each;
- update canonical requirements/scope/decisions/backlog/checkpoint.

## OUT OF SCOPE
- product implementation;
- model downloads;
- starting Blender/ComfyUI on the user's workstation;
- freezing individual module architecture beyond cross-cutting decisions explicitly authorized by the user;
- declaring candidate proprietary technologies novel without prior-art research.

## FILES/SOURCES TO READ
- IRIS canonical Project Brain at the authorized base;
- `KayzenRoot/ugas` main `0169f84248703931bb7578177d9773bce319c14e`;
- `UGAS-V2-MASTER-BLUEPRINT.md` v0.3.0;
- current official Blender and ComfyUI documentation/release surfaces.

## REQUIREMENTS
- 61 modules, IDs M00–M60;
- five sessions per module;
- all 30 UGAS V2 categories have an IRIS destination;
- former UGAS V2 important/future ideas requested by the user are not silently dropped;
- no-MVP and extreme-quality rules are canonical;
- 8 GB VRAM class is a first-class supported target;
- background/headless execution is a first-class architecture requirement;
- Git remains authoritative; HIVE context remains derived.

## ACCEPTANCE CRITERIA
- Master Module Index contains exactly 61 modules and 305 sessions.
- UGAS carryover map covers all 30 categories and named cross-cutting technologies.
- Research baseline records current external toolchain direction without freezing replaceable models.
- Decisions/requirements/scope/checkpoint are internally consistent.
- No product code is introduced.
- Exact-head Governance CI is green.
- Audit finds no unresolved HIGH/CRITICAL/blocking MEDIUM issue.

## TESTS / EVIDENCE
- existing Governance CI on exact PR head;
- structural count/audit of M00–M60 and five sessions each;
- diff audit proving planning-only mutation;
- source/carryover completeness review.

## DELIVERABLES
Canonical discovery baseline, module map, carryover map, quality/runtime principles, updated Project Brain and Evidence Bundle.

## REVIEW FORMAT
Português brasileiro; findings by severity; verdict `APPROVED`, `CORRECTION REQUIRED` or `BLOCKED`.

## EVIDENCE
- Authorized base: `f41c85f64f764400cc600eb52d98cadd0f78a49e`.
- Audited planning head: `d9d644d5fe110ec12326b6e2372eef9470223300`.
- Exact-head Governance run: `35518970773` / job `106099623155` / SUCCESS.
- Exact-head assertion: expected = actual = `d9d644d5fe110ec12326b6e2372eef9470223300`.
- Governance validator: PASS.
- Bridge tests: 8/8 PASS.
- Structural audit: 61/61 modules; M00-M60; 305/305 sessions; 61/61 modules with exactly five sessions.
- UGAS V2 carryover audit: 30/30 categories mapped.
- Diff audit: 15/15 changed files limited to planning/docs/.engineering; product code changed: 0.
- CRITICAL: 0; HIGH: 0; blocking MEDIUM: 0.

## STOP CONDITION
Satisfied for the research/module-map baseline. Product implementation remains gated. The next legal increment is M00 S01 planning.
