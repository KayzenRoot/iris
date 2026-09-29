# M09 handoff C02: owner-compatible forward and reverse handshake scan

**Status:** PROPOSED_DOC_ONLY, M09 owner adoption PENDING | **Work Order:** IRIS-WO-0016 | **Issues:** #112 / #110 / #82
Source main `452aff2f09e3f9130c26eb2068401b385cea67d1`, tree `84c9b89179c0eddcc617524e20ea122966679085`. Base contains the reviewed C01 versioned **NONFROZEN** candidate `m09-evidence-handoff-candidate-v0.1` from PR #115 (head Governance #459, protected merge `452aff2f09e3f9130c26eb2068401b385cea67d1`, exact-main Governance #460, 3,940/3,940 tests). This scan audits compatibility; it does not amend C01, choose an option or freeze an owner port.

## Substantive finding: C01's direction is not the full M09/M11 handshake

C01 concerns M09 → M11 read-only exact-request grant evidence. The frozen M09 FC-09-03 additionally requires **M11 → M09** owner-liveness evidence with freshness and `UNKNOWN`, and the frozen M09 compatibility matrix calls for cooperative-release requests to M11 and responses back to M09. These are separate logical boundaries: adding a grant receipt to C01 cannot silently solve process liveness, recovery or release.

The existing `iris_resource_twin/recovery.py` already defines **in-process typed** `OwnerLivenessRef(owner_ref, state, authority_ref, observed_at_ms, evidence_ref)`, state `ALIVE|TERMINATED|UNKNOWN`. For non-UNKNOWN the type requires the `authority_ref` **string prefix** to be `M11`; this is source validation, **not proof** that a remote/current M11 owner really issued or can authenticate that statement. `confirm_leak` additionally checks owner match, fresh age and production-observed resource evidence; that deterministic algorithm is not an admitted external liveness port or process permission. M09 also exposes `CooperativeReleaseRequest`, `CooperativeReleaseResponse` and `evaluate_cooperative_release`. A matched `ACCEPTED` is explicitly `ACCEPTED_AWAITING_RESOURCE_RECONCILIATION`, with `capacity_reclaimed=false`; a timeout never proves a process ended. Preserve these truths without promoting raw structs to cross-owner wire contracts.

## Complete FC-09-01..14 additive-compatibility matrix

Original normative source: `planning/compatibility/M09-FORWARD-COMPATIBILITY-SCAN.md`, Git blob `17064850e8d3cb15685d26499b75177f19e45252`. Existing M09 canonical doc says FC-09-01..14 are exercised by frozen invariant proofs 501–514. This C02 scan tests whether a **new** M09→M11 evidence interface would violate or depend on them; it does not rerun implementation proofs.

| FC | Normative intersecting boundary | Owner(s) | C02 result |
| --- | --- | --- | --- |
| FC-09-01 | Exact resource claim consumer/schema, hard/soft quantity and source refs | M09/M02/M11 | OPEN_OWNER: C01 exact-work logical role is proposed; real consumer claim handoff and exact M02 binding require owner review |
| FC-09-02 | Quality constraint provenance | M01/M03/M09 | PRESERVE: Preserve existing frozen constraint semantics; no domain quality trade from this interface |
| FC-09-03 | Reverse M11 owner-liveness typed reference with freshness and UNKNOWN | M11/M09/M54/M60 | REVERSE_BLOCKED: M09 OwnerLivenessRef exists only as typed in-process value; independent M11 verifier/transport absent |
| FC-09-04 | Placement-neutral M09 resource identity | M09/M12 | OWNER_PENDING: Existing identity must not be rewritten when M12 eventually binds host/target; placement still pending |
| FC-09-05 | Provider capability negotiation | M09/M17/M26 | OUT_OF_SCOPE: No provider action in read-only receipt; preserve frozen capability negotiation |
| FC-09-06 | Domain context descriptor | M09/domain owners | OUT_OF_SCOPE: No chunk/tile/temporal policy selected; maintain opaque domain refs |
| FC-09-07 | Composite claims/grants/transfers atomicity and member outcomes | M09/M12 | COMPOSITE_BLOCKED: Actual candidate mentions composite claims but lacks owner-adopted coherent mandatory/optional proof for full grant |
| FC-09-08 | External quality/fitness evidence namespaces | M01/M14/M24/M48/M51 | PRESERVE: Do not recode quality or fitness evidence as resource grant |
| FC-09-09 | Versioned public evidence projection and redaction | M09/M54/M58 | PUBLISH_BLOCKED: FC projection and M09 qualification EvidenceBundle are not current per-request grant verifier |
| FC-09-10 | Automation-origin mutation attribution | M09/M54/M57 | PRESERVE: Read-only is never authority to grant/revoke/release; preserve MutationContext |
| FC-09-11 | Storage/cleanup capability refs | M09/M55 | OUT_OF_SCOPE: No deletion from liveness, lease release response or receipt |
| FC-09-12 | Observed resource events and M56 epoch/provenance | M09/M56/M54 | OWNER_PENDING: Telemetry/event publication not trusted current grant or M11 liveness proof |
| FC-09-13 | Material resource impact owner refs | M09/M06 | OWNER_PENDING: M09 materiality refs cannot create M06 attempt/materialization success |
| FC-09-14 | Exact-head acceptance proof and physical/synthetic distinction | M09/M60 | SEPARATE_QUALIFICATION: 12 HX + 6 LV planning tests unexecuted; 514 frozen proofs preserved but not newly qualified for extension |

Rows marked preserve/out-of-scope remain existing M09 frozen behavior, **not** approvals for M11 consumption. New external owner ports M12/M54/M58/M60 have index-only contract depth; their missing policies and interface risks remain UNRATED.

## Independent owner-source boundary matrix

| Owner | Available source depth | Constraint for C01 and later |
| --- | --- | --- |
| M02 | ACCEPTED owner source | Exact plan/work identity and accepted-state evidence, not M10 proposal |
| M06 | ACCEPTED owner source | Attempt/materiality/outcome are externally owned and not inferred from exit/grant |
| M09 | FROZEN owner source | Resource truth/claim, owner grant, epoch, composite atomicity, lease release and recovery |
| M10 | FROZEN advisory | Advice never equals owner grant, placement or dispatch |
| M11 | NONFROZEN proposal | Future verified liveness producer, process capability and cooperative-release consumer |
| M12 | INDEX ONLY | Placement/locality and quota/host target owner contract unavailable |
| M53 | INDEX ONLY | Provenance/rights constraints conditional; M09 cannot adopt rights policy |
| M54 | INDEX ONLY | Trusted issuer, actor, action, redaction and transport policy unavailable |
| M55 | INDEX ONLY | Physical storage/CAS and cleanup scope unresolved if persistent receipts selected |
| M56 | INDEX ONLY | Event aggregation only, cannot mutate M09 truth |
| M58 | INDEX ONLY | Public API/SDK/MCP schema negotiation and publication owner unavailable |
| M60 | INDEX ONLY | Platform/OS process capability and full system qualification details pending |

M02/M06/M09/M10 existing versioned contracts and original M09 83/15/514 remain unchanged. No indexed later module's heading is treated as an accepted data schema or policy.

## Four HIGH future-freeze blockers, not findings of executable code

| ID | Missing owner proof | Explicit no-authority interim disposition |
| --- | --- | --- |
| C02-FR-H01 | M11-authenticated, versioned, fresh liveness and cooperative-release *reverse* handoff (FC-09-03). Raw M11 string prefix is not issuer verification. | Unknown owner liveness; no automatic reclaim/release, leak promotion or process control. |
| C02-FR-H02 | M09-controlled **atomic** joint snapshot+lease proof, including FC-09-07 all mandatory composite members and separate optional member statuses, with epoch/revocation/time-of-use checks. | No positive from independent locks, partial grants or `active()` membership. |
| C02-FR-H03 | Separate M12 placement, M54 issuer/auth/redaction, M58 public surface and M60 platform/trust decisions; M12/M54/M58/M60 remain INDEX_ONLY. | No published owner-adopted port, placement, resource commitment or OS dispatch. |
| C02-FR-H04 | Exact M02 accepted work/M06 materiality and attempt mapping across M09 resource decision and M11 action, plus owner-validity race/recheck resolution. | Preserve independent opaque facts; no plan promotion, inferred outcome or cached grant. |

**These four are blocking future contract freeze, not residual HIGH findings in this documentation-only source scan.** The scan cannot close them by citing a previous in-process M09 test or a GitHub documentation CI result.

## Six extra reverse-handshake proof oracles

The linked machine-readable `.engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json` defines `LV-01..06` as **SPECIFIED_NOT_EXECUTED**, in addition to 12 old HX, 10 C08 and eight PO-C02 cases. Coverage: untrusted M11 string prefix, UNKNOWN/stale/foreign liveness, ACCEPTED cooperative response without actual reclaimed bytes, timeout/mismatched response, partially valid composite grant, and revocation/lease-epoch or process-liveness conflict. All demand **no process action and no M09 lease mutation**. Even accepted synthetic future tests do not certify OS/GPU/cross-host physical performance.

## Next owner decision and STOP

Under [Issue #110](https://github.com/KayzenRoot/iris/issues/110), request two independent dispositions rather than forcing B by assumption: (1) M09-owned read-only evidence topology A/B/C including joint cut and revocation; (2) an independently planned M11-authored FC-09-03 reverse liveness/cooperative-release proof and transport, if and only if future M54/M60 owners authorize it. Source code for recovery already exists as in-process semantics, so **reuse its state distinctions rather than duplicating recovery policy in M11**. C02 may be merged only as compatibility evidence after 79/79 source-lock, ten-path scope, exact-head Governance, separate bounded review and exact-main Governance. Do not change the current C01 candidate, frozen M09, 86 open M11 questions, owner status, or runtime.
