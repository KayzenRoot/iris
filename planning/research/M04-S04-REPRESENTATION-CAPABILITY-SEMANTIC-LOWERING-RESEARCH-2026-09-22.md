# M04 S04 Research Baseline — Representation Capability & Semantic Lowering

Status: `RESEARCH_COMPLETE_FOR_S04`
Date: 2026-09-22
Module: `M04 — Multimodal IR / Scene IR`
Issue: `#26`

## Purpose

Resolve the historical M04/M16 "Provider Compiler" overlap and identify prior-art patterns for capability declaration, target legality and safe semantic lowering.

## Ownership conflict discovered

The Master Module Index historically names M04 S04 "Provider Compiler and capability downgrade planning", while M16 is explicitly **Workflow Registry & Provider Compiler** and owns "Provider compiler from IR/Fidelity Contract".

These cannot both own the concrete provider compiler.

### Resolution proposed by S04

M04 S04 is narrowed to:

**Representation Capability & Semantic Lowering Planning**

M04 owns:
- what semantic/schema/facet capabilities an M04 representation requires/uses;
- whether a declared target representation can preserve those semantics;
- analysis of exact/bounded/unrepresentable lowering;
- typed loss/gap/adaptation proposals;
- provider-neutral lowering receipts/contracts.

M16 owns:
- concrete provider/workflow selection;
- workflow graph compilation;
- model/node/provider parameters;
- provider-specific extensions;
- workflow qualification/signing/migration/rollback.

The word "provider compiler" is therefore legacy wording for M04 and must not appear in the frozen ownership contract.

## External prior art

### glTF required vs used extensions

glTF distinguishes extensions an asset uses from extensions that are required to load/render it correctly. Required extensions are a subset of used extensions.

IRIS adopts the semantic pattern:
- every IR document can declare schema/facet capabilities it uses;
- correctness-critical capabilities are explicitly required;
- unsupported required capability fails closed.

IRIS does not adopt glTF extension naming or delivery semantics as canonical M04 schema.

### MLIR dialect conversion

MLIR's dialect conversion distinguishes legal, dynamically legal, illegal and unknown operations and supports analysis-only, partial and full conversion modes.

IRIS adopts the architectural distinction between:
- capability/legality analysis;
- a planned semantic conversion;
- an actual concrete compiler.

M04 may perform provider-neutral **analysis/semantic legalization planning**. M16 performs provider/workflow compilation.

### OpenUSD schema families/versioning

OpenUSD's schema registry reasons about schema family, identifier and version, and its schema-versioning guidance treats behavior compatibility of downstream assets as a first-class concern.

IRIS adopts explicit schema-family/version compatibility declarations, not automatic "latest schema wins".

## Research conclusions

1. M04 and M16 must have separate ownership.
2. M04 can analyze target representability without selecting or compiling a provider.
3. required capability is different from merely used/optional capability.
4. unknown mandatory capability fails closed.
5. "downgrade" is forbidden terminology for M01 QualityClass; only an explicitly admitted semantic approximation may occur.
6. target capability observations never rewrite canonical IR.
7. compatibility analysis needs exact schema/facet/version/profile identity.
8. partial lowering is only legal for semantics whose loss policy allows it.
9. any adaptation that changes canonical meaning requires a new governed M03/M04 revision, not a compiler side effect.
10. M16 must receive a deterministic provider-neutral contract from M04 rather than reverse-engineering intent.

## S04 research gate

`PASS_WITH_OWNERSHIP_RENAME_REQUIRED`

The M04 frozen contract should rename/narrow S04 ownership before implementation admission.
