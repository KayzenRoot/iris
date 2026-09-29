# M14 S01 | Model Identity, Version, Hash, License & Provenance

**SOURCE RESEARCH ONLY | IRIS-WO-0076 | issue #204 OPEN | NO owner adoption.**
No model install, download, current usage rights, actual signature validation, empirical fitness, provider selection or executable M14 registry is admitted.

## 1. Original source authority and precise S01 boundary

M14 is INDEX_ONLY in the active standalone M00–M60 index. M13 documentary FTR/FCS is research, not M14 owner approval. An upstream card/alias/hash is an input claim, not a verified composite model package, legal entitlement, safe code, hardware benchmark or resource/process grant.

Original source main: 5d864f7a37f14f7daccdd385aa2cba1d77cece39; tree: 0556959bba5f7bb897901e875d8663956ea55681. Source roles and original SHA1 Git blobs:

- **INDEX** [planning/MASTER-MODULE-INDEX-CURRENT.md](../../planning/MASTER-MODULE-INDEX-CURRENT.md) original Git blob 02e6394cc7e75d5466ab22801b4cc7dbe66500be; exact anchor: ### M14 — Model Registry & Empirical Model Cards.
- **FCS** [planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md](../../planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md) original Git blob 5bac62b5b1a07fb97e43ea5c76d20dc5419c2cec; exact anchor: ### M14: Model Registry & Empirical Model Cards.
- **FTR** [planning/reviews/M13-FINAL-TECHNOLOGY-REVIEW-DOCUMENTARY.md](../../planning/reviews/M13-FINAL-TECHNOLOGY-REVIEW-DOCUMENTARY.md) original Git blob a704684ece3cd28969e93eb2eb56d5efb995ad55; exact anchor: 96 NEW M13 open/UNRATED questions, 74 future real-world cases SPECIFIED_NOT_EXECUTED.
- **M02** [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) original Git blob a36fd73c03f06b7558f850a2ad515a0df37c243b; exact anchor: cache/warm-state loss changes performance, not production truth;.
- **M06** [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) original Git blob d6778684e0c34e55d05ddc06cf5aa47fe347c037; exact anchor: Digest equality proves byte equality under the declared digest domain only..
- **M08** [docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md](../../docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md) original Git blob 461e0f332d9be2af694634bbdc8cf67e29d56393; exact anchor: M08 records empirical performance evidence.
- **M09** [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) original Git blob d12b4f48030c1a57b8e6228df39f35dac8c2b20a; exact anchor: M09 is the provider-neutral resource-state.
- **M13S01** [.engineering/evidence/M13-S01-SOURCE-RESEARCH.json](../../.engineering/evidence/M13-S01-SOURCE-RESEARCH.json) original Git blob 5fe1b1ec36ce1e49a0810f553825c9d71b2af3e0; exact anchor: "module": "M13".
- **D01** [.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json](../../.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json) original Git blob 8877331a5004a3e816e4c42fb521ff3408bad08a; exact anchor: B_FUTURE_OWNER_RECEIPT.

## 2. Five conceptual model-component identity classes, none adopted

### COMP01_UPSTREAM_REPOSITORY_REVISION: Immutable upstream model repository identity, commit and advertised release label

- Evidence boundary: A mutable friendly name, branch or model-card field locates a candidate but is not a content-complete verified model revision.
- Original pending owners: M14/M18/M54
- Status: SOURCE_TAXONOMY_UNADOPTED

### COMP02_WEIGHT_SHARDS_AND_INDEX: Complete weight shard inventory, index and configuration content binding

- Evidence boundary: One shard or manifest digest is not a model package digest; absence or reordered shard index can alter the interpreted model.
- Original pending owners: M06/M14/M18
- Status: SOURCE_TAXONOMY_UNADOPTED

### COMP03_TOKENIZER_AND_PROCESSOR: Tokenizer, vocabulary, preprocessing and processor source identity

- Evidence boundary: Changed tokenizer or preprocessor can change semantic output with weight bytes unchanged; M06 evidence must bind an actual revision.
- Original pending owners: M06/M14/M16/M18
- Status: SOURCE_TAXONOMY_UNADOPTED

### COMP04_ADAPTERS_AND_DEPENDENCIES: LoRA/adapter/base-model closure and exact compatibility revisions

- Evidence boundary: Adapter and base-model aliases cannot imply compatibility, rights, safe loading or provenance; reference and dependency graph need proof.
- Original pending owners: M14/M18/M19/M54
- Status: SOURCE_TAXONOMY_UNADOPTED

### COMP05_OPERATOR_CONFIG_AND_CUSTOM_CODE: Config, scheduler/precision/operator declarations and any executable custom code

- Evidence boundary: Registry data must not import/execute arbitrary code or treat an upstream package metadata digest as supply-chain trust.
- Original pending owners: M14/M16/M17/M18/M60
- Status: SOURCE_TAXONOMY_UNADOPTED

## 3. Five distinct licensing and rights facets, all unverified

An SPDX expression is metadata, not a finding that an ML model and every tokenizer, adapter, code package, input or output is legally deployable. Future M18/M53/M54 owner evidence must qualify actual terms and tenant scope.

- **RIGHTS01_WEIGHTS**: Weight-specific license and redistribution/commercial-use terms | pending M18/M53 | NOT_OWNER_VERIFIED | RIGHTS_UNVERIFIED.
- **RIGHTS02_TOKENIZER_DATA**: Tokenizer, vocabulary, processor data and training-data rights declarations | pending M18/M53 | NOT_OWNER_VERIFIED | RIGHTS_UNVERIFIED.
- **RIGHTS03_ADAPTER_BASE**: Adapter, base model and fine-tuned derivative compatibility terms | pending M18/M19/M53 | NOT_OWNER_VERIFIED | RIGHTS_UNVERIFIED.
- **RIGHTS04_EXECUTABLE_DEPENDENCIES**: Native libraries, custom nodes, code, transitive package and platform permission | pending M16/M17/M18/M54/M60 | NOT_OWNER_VERIFIED | RIGHTS_UNVERIFIED.
- **RIGHTS05_OUTPUT_AND_PERSONA**: Output obligations, consent, likeness/persona and tenant-specific rights | pending M53/M54/M58 | NOT_OWNER_VERIFIED | RIGHTS_UNVERIFIED.

## 4. Four alternative identity/receipt designs, none selected

### ALT01_UPSTREAM_LABEL_ONLY: Upstream tags/model-card-only reference

- Hypothesis and limit: May help discovery but mutable labels and self-reported license/capability cannot satisfy immutable identity or rights.
- Missing independent owner evidence: M14/M18
- Status: RESEARCH_REFERENCE_NOT_DEPLOYABLE, selected=False.

### ALT02_PINNED_COMPOSITE_DIGEST: Explicit commit and all-component digest manifest

- Hypothesis and limit: Potential reproducibility for bytes only; signature, authentic issuer, license, graph closure and operational rights remain absent.
- Missing independent owner evidence: M06/M14/M18
- Status: RESEARCH_CANDIDATE_ONLY, selected=False.

### ALT03_ISSUER_QUALIFIED_SBOM: Versioned signed source manifest/SBOM and bounded issuer verification

- Hypothesis and limit: Requires future qualified M18 supply and M54 authentic principal/tenant trust, M53 rights and lifecycle revocation.
- Missing independent owner evidence: M18/M53/M54
- Status: RESEARCH_CANDIDATE_ONLY, selected=False.

### ALT04_OWNER_QUALIFIED_LOCAL_RECEIPT: At-use owner-qualified local verification receipt bound to exact component graph

- Hypothesis and limit: Cannot be issued without original owner proof, current revocation, verified host M60 and hardware M07/M08 actual empirical evidence.
- Missing independent owner evidence: M07/M08/M14/M18/M53/M54/M60
- Status: RESEARCH_CANDIDATE_ONLY, selected=False.

## 5. Sixteen NEW OPEN/UNRATED M14 S01 owner questions

All questions below are newly proposed, not owner answers or risk findings. Earlier M11 86, M12 110/80, M13 96/74 and H01–H04 remain unchanged.

### M14-S01-U01 | M14/M02/M18

What exact immutable model repository/release/revision identifier and version boundary can M14 own without reassigning M02 production identity?

Original-source roles: INDEX, M02, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U02 | M14/M06/M18

Which complete weight-shard, index and config digest closure must an M14 record bind, including absent, duplicated and renamed shards?

Original-source roles: M06, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U03 | M14/M06/M16/M18

What is the canonical tokenizer, vocabulary and processor identity and how must stale or foreign semantic processing be marked UNKNOWN?

Original-source roles: INDEX, M06. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U04 | M14/M18/M19

How may adapter/LoRA/base-model revisions form an exact dependency graph, with incompatible or missing component refusal?

Original-source roles: INDEX, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U05 | M14/M16/M17/M18/M60

Which runtime-facing code/config declarations are safe metadata versus separately authorized custom-node execution under M18/M60?

Original-source roles: INDEX, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U06 | M14/M18/M53

How must per-component weight/tokenizer/adapter/license claims be expressed without treating a repository badge or SPDX label as legal approval?

Original-source roles: INDEX, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U07 | M14/M18/M54

Which signed issuer, key rotation, revocation and tenant-specific trust source can verify future model evidence without inventing M54 signoff?

Original-source roles: FCS, D01. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U08 | M14/M18/M55/M60

What registry identity and lifetime must distinguish upstream candidate, mirrored bytes, verified local installation and runnable provider instance?

Original-source roles: INDEX, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U09 | M14/M02/M06

Which M02/M06 accepted production/attempt/revision identifiers must accompany a future model revision without upgrading a cached alias to master?

Original-source roles: M02, M06. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U10 | M14/M18/M53/M54

How are conflicting card/license/source claims, missing terms or revoked derivative permissions represented without allowing commercial output?

Original-source roles: FCS, M06. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U11 | M14/M07/M08

Which source-qualified hardware fingerprint and M08 benchmark protocol are needed before any latency/VRAM/quality card is asserted?

Original-source roles: M08, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U12 | M13/M14/M09/M11/M12

When may M13 warm/model-cache hint cite M14 identity without proving model availability, M09 grant, M11 process rights or M12 placement?

Original-source roles: M13S01, M09, D01. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U13 | M14/M19/M53/M54

What provenance and versioning must cover fine-tuned derivative training input, consent and revocation when M19/M53 owners are future only?

Original-source roles: INDEX, FCS. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U14 | M14/M53/M54

How must namespace/tenant ownership and provenance prevent foreign-tenant references, inference and re-use across protected project boundaries?

Original-source roles: FCS, M02. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U15 | M14/M18/M54/M58/M60

Which signed actual owner decisions would permit any future registry endpoint, publisher or provider loading under M58/M60?

Original-source roles: FCS, D01. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

### M14-S01-U16 | M14/M15/M18/M53/M54

How should changed license text, revoked source or stale card invalidate downstream M15 routing, M13 prefetch and previously generated derivatives?

Original-source roles: INDEX, FCS, M13S01. Status: OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.

## 6. Twelve hostile/ambiguity future-case designs, NOT_EXECUTED

### M14-S01-N01

- Proposed hostile input: A stable marketing tag resolves to a different upstream commit while a stale model card still names the old revision.
- Required non-authorizing oracle: REFUSE_IDENTITY_EQUIVALENCE_OR_LOAD.
- Source question links: M14-S01-U01, M14-S01-U08.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N02

- Proposed hostile input: Only one shard digest matches but the index or a second weight shard is missing or replaced.
- Required non-authorizing oracle: NO_COMPOSITE_MODEL_ADOPTION.
- Source question links: M14-S01-U02.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N03

- Proposed hostile input: Weights remain identical but a newer tokenizer/processor silently alters input semantics.
- Required non-authorizing oracle: REJECT_UNVERIFIED_SEMANTIC_COMPATIBILITY.
- Source question links: M14-S01-U03, M14-S01-U09.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N04

- Proposed hostile input: A compatible-looking adapter names an unverifiable or conflicting base model revision.
- Required non-authorizing oracle: NO_ADAPTER_BASE_VERSION_PROMOTION.
- Source question links: M14-S01-U04.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N05

- Proposed hostile input: A model package metadata field suggests importing remote custom Python code during registry discovery.
- Required non-authorizing oracle: NO_EXECUTION_OR_PROVIDER_ADMISSION.
- Source question links: M14-S01-U05, M14-S01-U15.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N06

- Proposed hostile input: A repository badge claims permissive licensing while component terms are absent or incompatible.
- Required non-authorizing oracle: RIGHTS_UNKNOWN_NO_COMMERCIAL_GRANT.
- Source question links: M14-S01-U06, M14-S01-U10.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N07

- Proposed hostile input: A signed-looking manifest has an unverified issuer or revoked signing material.
- Required non-authorizing oracle: NO_AUTHENTIC_PRINCIPAL_OR_TRUST_INFERENCE.
- Source question links: M14-S01-U07.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N08

- Proposed hostile input: A copied local archive exists but no original-qualified manifest, storage rights or installed code proof is present.
- Required non-authorizing oracle: NO_LOCAL_PACKAGE_QUALIFICATION.
- Source question links: M14-S01-U08.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N09

- Proposed hostile input: A prior accepted M02 master points to stale M06 result revisions while a cache aliases its model identifier.
- Required non-authorizing oracle: NO_ACCEPTED_MASTER_OR_REUSE_INFERENCE.
- Source question links: M14-S01-U09.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N10

- Proposed hostile input: A model card reports zero latency and tiny VRAM from a nonrepresentative, unverified machine.
- Required non-authorizing oracle: NO_EMPIRICAL_PERFORMANCE_OR_GPU_FIT_CLAIM.
- Source question links: M14-S01-U11.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N11

- Proposed hostile input: A cached warm-model hint is incorrectly interpreted as a live joint lease and worker dispatch permission.
- Required non-authorizing oracle: NO_M09_GRANT_OR_M11_DISPATCH.
- Source question links: M14-S01-U12.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

### M14-S01-N12

- Proposed hostile input: A foreign tenant provides model metadata and a revoked license while a proposed public endpoint attempts to publish it.
- Required non-authorizing oracle: NO_CROSS_TENANT_PUBLICATION_OR_REUSE.
- Source question links: M14-S01-U10, M14-S01-U14, M14-S01-U15, M14-S01-U16.
- Status: SPECIFIED_NOT_EXECUTED; no provider, filesystem, GPU, OS or network test was executed.

## 7. External reference examples only, no specification adopted

These official format references are vocabulary candidates, not IRIS contract choices, proof of current commercial permission, actual vendor compatibility or offline test execution.

- **SPDX_LICENSE_EXPRESSIONS**: https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/ | REFERENCE_ONLY_NOT_ADOPTED_OR_LEGAL_PROOF.
- **HUGGINGFACE_MODEL_CARD_SCHEMA**: https://github.com/huggingface/hub-docs/blob/main/modelcard.md | REFERENCE_ONLY_NOT_ADOPTED_OR_LEGAL_PROOF.
- **OCI_IMAGE_MANIFEST_REFERENCE**: https://specs.opencontainers.org/image-spec/manifest/ | REFERENCE_ONLY_NOT_ADOPTED_OR_LEGAL_PROOF.

## 8. Boundary, actual owner questions and STOP

- M09 B: B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY; C01: UNADOPTED_NOT_FROZEN; four highs: ALL_OPEN_HIGH_FOR_FUTURE_FREEZE.
- Current cross-module native runtime: NOT_ADMITTED; historical M13: 96 open questions and 74 unexecuted future tests.
- S02–S05, empirical measurement, qualified license/supply-chain review and M14 contract freeze require distinct admitted work and real owners.
- STOP: All M14 S01 identities, component classes, license facets, versions and manifest options are NONBINDING planning only. M14 owner questions stay OPEN/UNRATED and future hostile cases SPECIFIED_NOT_EXECUTED. No source owner contract, SPDX legal permission, registry or package install, model download, native custom code, empirical benchmark, model eligibility, M09 grant, M11/M12 process dispatch, OS/GPU/storage/cloud/network rights or other M10-M13 runtime is ADMITTED. Qualified M14/M18/M53/M54/M60 owner gates and original H01-H04 remain separately blocked. M10-M13 native runtime remains NOT_ADMITTED.

