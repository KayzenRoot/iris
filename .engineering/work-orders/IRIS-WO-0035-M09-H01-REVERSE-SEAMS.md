# IRIS-WO-0035: H01 source-only synthetic reverse-liveness and cooperative-ACK seams

Status: ADMITTED_FOR_EXISTING_INPROCESS_SYNTHETIC_SEMANTIC_PROBES_ONLY | Issues #82/#110/#112/#128 OPEN
Exact source base `a50686bfb551d5b106957685aa30a9c0f4e8c86e`, tree `cc1d12622621989321b3d69212c9ec5cd095e78a`, exact-main Governance #515 run 36338892948/job 108674961779 PASS 4158/4158. Actual responsible user chose B_FUTURE_OWNER_RECEIPT **documentary future M09→M11 forward read-only receipt direction ONLY** at https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032. B does NOT authenticate reverse M11→M09 liveness or a response/ACK.

## Bounded substantive work
Add **20 deterministic synthetic in-memory probes** `H01-P01..P20` using unchanged existing frozen M09 `OwnerLivenessRef`, `confirm_leak`, `StaleCommitmentReaper` and `evaluate_cooperative_release`. These demonstrate source-text issuer-prefix acceptance (not authentication), a naive local `confirm_leak(TERMINATED)` positive using user-authored M11-prefixed liveness and appropriately structured local evidence (not real external proof), UNKNOWN/wrong owner/stale/synthetic proof refusal, locally accepted caller-authored ACK whose pre-request timestamp is not lower-bound checked, missing/wrong/late/replayed responses and the permanent no-reclaim safety rule. Add **8** source/history integrity regressions that separate these H01-P tests from the six original future LV tests. Write a source-bound H01 seam report, machine proof inventory, historical planning checkpoint/backlog and next concrete owner proof needs, without choosing an issuer/transport/crypto/OS provider or other owner contract.

## 24/24 pinned exact-base Git source SHA-1, 10/10 strict allowlist
Source pins include all 8 project authority roots; frozen M09 source `recovery.py`, `leases.py`, `model.py` and original test supports; original C01/C02 historical evidence, real B-direction D01, M11 C09 and v0.2 candidate, M02/M06 contract candidates, previous WO0034 closed-merge evidence/H02 report and backlog. Only these **10 paths** may change:

- `.engineering/context-locks/IRIS-WO-0035-M09-H01-REVERSE-SEAMS.json`
- `.engineering/evidence/IRIS-WO-0035.json`
- `.engineering/evidence/M09-H01-REVERSE-SEAM-EVIDENCE.json`
- `.engineering/work-orders/IRIS-WO-0035-M09-H01-REVERSE-SEAMS.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/checkpoints/IRIS-WO-0035-M09-H01-REVERSE-SEAMS.md`
- `planning/reviews/IRIS-WO-0035-M09-H01-REVERSE-AUDIT-TARGET.md`
- `planning/reviews/M09-H01-SYNTHETIC-REVERSE-SEAM-PROBE.md`
- `tests/test_m09_h01_reverse_integrity.py`
- `tests/test_m09_h01_synthetic_reverse_seams.py`

Original M09 code/frozen contract, historical C01/C02, original LV/HX tests, real D01 owner decision/ADR, canonical checkpoint and public status remain unchanged; the authoritative next step remains real proof/owner decision. Historical previous WO0034 #514/#515 receipts are reconciled within this substantive H01 test increment only.

## Testing, audit and merge
Expected full exact-head Governance **4186/4186** (4158 base + 20 H01-P source-level deterministic probes + 8 new integrity regressions); Context Lock **24/24**, changed-path allowlist **10/10**, IRIS governance, pinned GEF/IRIS bridges. Perform separate bounded exact-head read-only same-assistant audit honestly **not** independent human/security/issuer audit, no new HIGH/CRITICAL in scoped docs/tests, four inherited HIGH freeze gates still OPEN. Protected squash exact reviewed head only, separate exact-main CI and issue receipt before closeout.

## HARD STOP
Newly executed H01-P tests are NOT original LV-01..06 (remain SPECIFIED_NOT_EXECUTED), HX-01..12, C08 ten, PO-C02 eight or M12 80 future test designs; do not claim actual M11 process producer, M54 principal or M60 OS capability verified. H01 OPEN_OWNER_EVIDENCE_REQUIRED; H02 M09 owner atomic joint cut OPEN; H03 M12/M54/M58/M60 real contracts OPEN; H04 exact M02/M06/M09/M11 work/attempt/epoch binding OPEN; all HIGH_FOR_FUTURE_FREEZE. M09 v1.0 FROZEN unchanged; C01 UNADOPTED_NOT_FROZEN; M11 v0.2 NOT_FROZEN 86 OPEN; M12 v0.1 PREPARED_FOR_OWNER_REVIEW_ONLY/NOT_FROZEN 110 OPEN and 80 future negatives NOT_EXECUTED. M10/M11/M12 implementation NOT_ADMITTED; process, OS, GPU, IPC, network and cloud actions DISABLED. Keep #82/#110/#112/#128 OPEN. No positive real capacity reclamation or cross-boundary trust may follow from a synthetic source-only fixture.
