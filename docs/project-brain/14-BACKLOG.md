# IRIS Backlog

Status: `M11_PLANNING_ACTIVE_M10_IMPLEMENTATION_NOT_ADMITTED`

## COMPLETED FOUNDATION
- M01-M09 implementations are durably closed.
- M09 contract `m09-contract-v1.0` is frozen and implemented through IRIS-WO-0013.
- M09 completion evidence records 83/83 surfaces, 15/15 absorbed components, 514/514 invariant proofs and FC-09-01..14.
- PR #65 was independently audited, protected-merged as `d4ebf87c266d6de04a4e978fa6b8ad8fa958618c`, and passed exact-main Governance `36016789990 / 107691278049`.
- PR #66 closure reconciliation passed exact-head Governance `36025800675 / 107721889592`, was protected squash-merged as `e8ab43f42981630bad244a1d932e60e4ac584b2e`, and passed exact-main Governance `36027974675 / 107729242412`.
- PR #67 reconciled the canonical checkpoint, passed exact-head Governance `36029267285 / 107733578946`, was protected squash-merged as `b6456670a7c61621db1d3b3fc6d55487adb9cd64`, and passed exact-main Governance `36029536926 / 107734488887`.
- M09 closure reconciliation is complete; no M09 implementation changes are active.

## COMPLETED PLANNING — M10
- Module: **M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield**.
- Issue: #68.
- Exact planning base: `b6456670a7c61621db1d3b3fc6d55487adb9cd64`.
- Admission Governance: `36029536926 / 107734488887`, PASS.
- S01 Workload Signature Engine: **COMPLETE_FOR_MODULE_PLANNING**; PR #69 exact-main Governance passed on `fc1a3c954a1629b9e9a4c45c4e557a7832c290d7` (`36031548275 / 107741264931`).
- S02 hardware-aware plan compilation: **COMPLETE_FOR_MODULE_PLANNING**; PR #70 exact head `0fa18f55d845192d4225751ec14316af08ec6dad` passed Governance `36032894812 / 107745773871`, merged as `8d068d1cf9ef604aef8506ec879b7a382ec1b738`, and passed exact-main Governance `36033011233 / 107746156289`.
- S03 predictive OOM, thermal and quality-risk models: **COMPLETE_FOR_MODULE_PLANNING**; PR #71 exact head `db9fc7e0f0e7615c075cfaee3debec3a3990697b` passed Governance `36034416554 / 107750841548`, merged as `8768661ee348815ec5b1eb6e32bc85505fa10b17`, and passed exact-main Governance `36034538318 / 107751237481`.
- S04 ECO/BALANCED/QUALITY/MAX/CUSTOM semantics: **COMPLETE_FOR_MODULE_PLANNING**; PR #72 exact head `add4344d6b1a495f1aeeb23af0d57fdcddde381e` passed Governance `36037625164 / 107761547909`, merged as `96aee147e701c6d716cfbcf5f2be524ee5d751e7`, and passed exact-main Governance `36037710495 / 107761836741`.
- S05 observed-result learning and explainable decisions: **COMPLETE_FOR_MODULE_PLANNING**; PR #73 exact head `fc1fa4959697b88fbfbe303736517aef52d9bc91` passed Governance `36038801813 / 107765474152`, merged as `54d85d3491d4cc21e95fc2f9042c53d2852ceb88`, and passed exact-main Governance `36038905218 / 107765823628`.
- Final Technology Review: **COMPLETE_FOR_M10_PLANNING**; PR #74 exact head `69762690f9368cf0f76f106d75330950862e532d` passed Governance `36039931359 / 107769276836`, merged as `e38912a57c2d452badd5a35a031eb78f95d0e899`, and passed exact-main Governance `36040044487 / 107769655432`.
- M11–M60 Forward Compatibility Scan: **COMPLETE_FOR_M10_CONTRACT_CANDIDATE**; PR #75 exact head `d55ea04a9663b648805b00ea0032773125c65642` passed Governance `36041422592 / 107774247740`, merged as `2328978175a59768e64687748b259027b3a79d4e`, and passed exact-main Governance `36041515972 / 107774565519`; coverage 50/50 at module-index level, with FC-10-01..12.
- Independent M10 planning audit: **APPROVED** at reviewed exact main `d8000229397138ed0d45133df456598cdd010ddf`; findings: HIGH 0, CRITICAL 0.
- M10 contract `m10-contract-v1.0`: **FROZEN_APPROVED**; PR #77 exact head `57dc0410e9c434a04657b8f57562febdeceb84f1` passed Governance `36043928118 / 107782644258`; protected squash merge `8a3e32de28ccc824c165e29bfa3da4f6cc305de0` passed exact-main Governance `36044190420 / 107783526436` (actor: KayzenRoot). M10 implementation remains NOT ADMITTED.
- M10 product/runtime implementation introduced: **NO**.

### M10 implementation proposal status
- IRIS-WO-0014 documentation proposal: PR #80 exact head f84ca2e00162a7869e31efcb217a962c1aa6ec2b passed Governance 36059070309 / 107833280091; protected squash merge 26c891fd53ac24e1e32b4ae84e162ea029f69366 passed exact-main Governance 36059177560 / 107833630952.
- PR #81 closeout exact head e0e1d4d648e66aa049a5c21551fdc948eb4d316c passed Governance 36059412524 / 107834422442; exact main 0014d23115f5fec60a77e5e32d5083e90069a918 passed Governance 36059512224 / 107834755459.
- Preflight remains BLOCKED; M10 implementation remains NOT_ADMITTED.

## ACTIVE PLANNING — M11
- Module: **M11 — Background Worker Fabric & Process Lifecycle**.
- Issue: #82; planning Work Order: IRIS-WO-0015.
- Exact planning base: 0014d23115f5fec60a77e5e32d5083e90069a918; admission Governance: 36059512224 / 107834755459, PASS.
- Five canonical sessions: S01 supervisor/job model; S02 background startup/IPC; S03 concurrency/priorities/leases; S04 reaper/zombie detection/shell-free execution; S05 cancellation/timeouts/recovery/workstation coexistence.
- Current state: planning admitted; S01-S05 COMPLETE_FOR_MODULE_PLANNING; M11 owner contract NOT_FROZEN. PR #95 exact head 77dccb7e350d51d66f8b5cc135566becf0537dcc passed Governance #418 (36257428623 / 108446767119; 3,940/3,940), was protected squash-merged as 091361e71e2d55f05b2623163bd6f8c7234eb5b8, and passed exact-main Governance #419 (36258590273 / 108449958757; 3,940/3,940). S04-U01..U21 and S05-U01..U23 remain open; M12-M60 owner contracts remain pending. M11/M10 implementation NOT_ADMITTED; m10-contract-v1.0 FROZEN; WO-0014 BLOCKED.
- Available owner sources checked: M02, M06, M09, M10. M12–M60 owner-specific details remain pending until each canonical contract exists.
- S03 exact proposal head 778218c04fb9481cab75122001deb87814ce3e68 passed Governance 36189044035 / 108249450672 (3940/3940 tests); PR #89 was protected squash-merged as ad3c4ac4aa84890248fbc7e6250bea2de271fd65 and exact-main Governance 36189379137 / 108250522233 passed (3940/3940 tests; actor KayzenRoot). Its Context Lock matched 68/68 sources; the documentation audit found 0 HIGH/CRITICAL/residual findings. The S03 checkpoint/evidence closeout passed exact-main Governance before S04 began. S04 closeout PR #93 was HEDS APPROVED on exact head 6e9e717ecacacfbef787a53ffbf0254f1188323c, protected squash-merged as e0d8aeeea676d884e9c6a716df42a363f0765020, and passed exact-main Governance #415 (36244566768 / 108411232665; 3940/3940 tests); its closeout Context Lock matched 77/77. S05 proposal PR #94 exact head c2478c757814df72ca7e5b03fe530e27674f5694 received HEDS APPROVED in separate read-only task /root/s05_heds_review (confidence 0.92; zero findings; owner-specific residuals pending), was protected squash-merged as 2e6c0b89b67230b2b39c4bbb37ff51648d061060, and passed exact-main Governance #417 (36254017572 / 108437249087; 3940/3940 tests). The PDF-listed run ID 36250417572 returned 404; 36254017572 is the verified #417 run. Closeout PR #95 exact head 77dccb7e350d51d66f8b5cc135566becf0537dcc passed Governance #418 (36257428623 / 108446767119), was protected squash-merged as 091361e71e2d55f05b2623163bd6f8c7234eb5b8, and passed exact-main Governance #419 (36258590273 / 108449958757; 3,940/3,940 tests). S05 is COMPLETE_FOR_MODULE_PLANNING; unresolved policies and owner contracts remain pending.
- M11 implementation: NOT_ADMITTED. M10 contract remains m10-contract-v1.0; M10 implementation remains NOT_ADMITTED and WO-0014 preflight BLOCKED.

## NECESSARY NEXT

IRIS-WO-0021 executor-context guidance PR #127 exact head ae9830c179fd8fc2c1592a8fdbf030c14c80553f, Governance #482 run 36324221232/job 108633744853 PASS 3979/3979 with 34/34 base sources and 10/10 authorized files; protected squash merged e3fc858d3c92a8a3eba3c7c6119fc490c4098129 (tree 171bb58cec6a327a2cdab8a9b63bcc78a32363a0), exact-main Governance #483 run 36324303557/job 108633979540 PASS 3979/3979. Issue #126 CLOSED, old stale PR #91 CLOSED SUPERSEDED WITHOUT MERGE; HIVE v1.0.3 read-only context is reference only, runtime pinned HIVE v1.0.0 unchanged. New parallel M12 S01 documentation-only planning IRIS-WO-0022 / Issue #128 admits a source-backed worker registry/capability advertisement research proposal with 40/40 exact main Git blob SHA-1 pins, 12/12 strict allowed files and 18 open/unrated source-routed M12-S01 questions, plus 12 future negative/ambiguity scenarios SPECIFIED_NOT_EXECUTED. It is not a verified M12 contract or executable registry; require its own exact-head Governance 3979/3979, separate bounded review, protected squash merge and exact-main. M12 S02–S05, technology selection, FTR, FCS, contract freeze and implementation remain NOT_STARTED/NOT_ADMITTED. M09 owner Issue #110 still OPEN: A/B/C NONE_SELECTED, joint snapshot+lease H02 unproven, reverse liveness H01 unauthenticated, H03/H04 future owner/identity gates unresolved, four HIGH_FOR_FUTURE_FREEZE remain OPEN, six LV/12 HX/ten C08/eight PO-C02 all NOT_EXECUTED. M09 v1.0 remains FROZEN 83/15/514 and C01 UNADOPTED_NOT_FROZEN; M11 v0.2 NOT_FROZEN with 86/86 questions OPEN/UNRATED; M10/M11 implementation NOT_ADMITTED, processes DISABLED, M12–M60 individual owner contracts otherwise PENDING/UNRATED and #82/#110/#112 OPEN.

## IMPLEMENTATION GATE
No M11 runtime/process-control code is authorized during the planning cycle. No M10 product/runtime code is authorized; m10-contract-v1.0 remains frozen, M10 implementation remains NOT_ADMITTED, and a separate implementation Work Order, Context Lock, Evidence package and successful preflight would be required for any future M10 admission.
