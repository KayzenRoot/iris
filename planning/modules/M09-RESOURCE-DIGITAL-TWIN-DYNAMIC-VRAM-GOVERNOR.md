# M09 — Resource Digital Twin & Dynamic VRAM Governor

Status: `S01_PLANNING_CANDIDATE`
Planning base: `11db4286e77ec9d740f1e115bf8c537536bc2b85`
Issue: #61
Implementation: **NOT ADMITTED**

## Mission
M09 owns the resource-state and resource-control truth needed to keep IRIS productive on constrained and heterogeneous machines, with 8 GB VRAM-class hardware as a first-class target. It models observed/estimated/committed memory state, grants bounded resource leases and reservations, tracks residency, and later governs spill/offload/prefetch and memory-pressure recovery. Scarcity is explicit evidence; it never silently lowers M01 quality or protected M03 semantics.

## Canonical sessions
1. S01 Resource Digital Twin state model
2. S02 VRAM leases, reservations and model residency
3. S03 RAM/NVMe spill, offload and prefetch planning
4. S04 Dynamic tile/chunk/batch/precision control
5. S05 Memory-pressure recovery, cleanup and leak detection

# S01 — Resource Digital Twin state model

## S01 objective
Define a provider-neutral, versioned, uncertainty-aware digital twin of resource state. S01 models truth and admissibility primitives. It does not yet implement concrete lease arbitration, spill/offload execution, workload-plan compilation, worker supervision or cross-node placement.

## Authority boundary
- M07 owns discovered hardware/runtime facts and topology.
- M08 owns empirical benchmark/capability-envelope evidence.
- M09 owns transient resource state, reservations/leases/residency and memory-pressure resource policy.
- M10 owns adaptive execution plans, predictive OOM and thermal decisions.
- M11 owns worker/process lifecycle.
- M12 owns placement/orchestration.
- M14 owns model-specific empirical fitness.
- M55 owns physical storage/CAS/cache/archive.
- M56 owns observability aggregation.
- M01 remains quality authority; M03 protected semantics cannot be weakened by scarcity.

## S01 technology surfaces

### RDT-01 — Resource Digital Twin Fabric
Canonical immutable snapshot model for GPU VRAM, host RAM and eligible spill tiers. Every snapshot has stable identity, schema version, observation time, source refs and confidence/validity state.

### RDT-02 — Resource State Ledger
Append-oriented transition ledger connecting snapshots without rewriting historical observations. Transitions distinguish observation, reservation intent, commitment, release, reconciliation and invalidation.

### RDT-03 — Capacity Truth Partition
Separates physical capacity, OS/runtime reported capacity, allocatable capacity, reserved headroom, committed bytes, resident bytes, reclaimable bytes, unavailable/unknown bytes and externally consumed capacity. These values cannot collapse into one free-memory scalar.

### RDT-04 — Confidence & Unknown-State Lattice
Resource facts use explicit KNOWN / ESTIMATED / STALE / CONFLICTED / UNKNOWN / UNSUPPORTED semantics with provenance. Unknown capacity is never interpreted as zero or infinite capacity.

### RDT-05 — Resource Provenance Binder
Every material resource fact can reference M07 discovery evidence, M08 empirical evidence, runtime observation and calibration lineage without transferring their authority into M09.

### RDT-06 — Headroom Covenant
Represents operator-configurable workstation headroom for VRAM/RAM/CPU-adjacent resource pressure. Headroom is a protected constraint, not spare capacity available to IRIS.

### RDT-07 — Commitment Conservation Engine
Tracks committed/reserved/resident/reclaimable quantities with conservation predicates so double counting, negative availability and phantom releases fail closed.

### RDT-08 — Resource Identity Namespace
Stable resource identities distinguish device, memory heap/tier, runtime/provider context and host scope. Device reorder, display name change or process restart cannot silently create a new resource identity.

### RDT-09 — Observation Reconciliation Fabric
Combines asynchronous observations without pretending they are simultaneous. Carries observation windows, skew, source priority and conflict evidence.

### RDT-10 — Staleness & Expiry Governor
Resource state has explicit freshness windows and invalidation triggers. Stale state cannot authorize a resource commitment that requires fresh evidence.

### RDT-11 — External Consumption Sentinel
Models memory/resource use not controlled by IRIS as external consumption with uncertainty. It must not kill, suspend or evict unrelated processes.

### RDT-12 — Scarcity Non-Degradation Firewall
Resource scarcity can yield WAIT / REJECT / REQUIRE_REPLAN / REQUIRE_OFFLOAD / UNKNOWN outcomes but cannot silently lower quality, fidelity, protected semantics or acceptance thresholds.

### RDT-13 — Resource Claim Algebra
Defines typed claim units, scopes, exclusivity/shareability, hard/soft reservation semantics and compatibility predicates that S02 can use for leases without embedding scheduler policy.

### RDT-14 — Snapshot Consistency Seal
Deterministic digest over canonicalized resource snapshot semantics and provenance refs. It is resource-state identity only, not M06 production identity.

### RDT-15 — Resource Event Causality Graph
Links observation and state-transition causes so later M10/M11/M56 consumers can explain why capacity changed without M09 taking their authorities.

### RDT-16 — Pressure Signal Normalizer
Normalizes provider/runtime pressure signals into typed evidence. It reports pressure; S01 does not predict OOM or thermal outcomes.

### RDT-17 — Reconciliation Quarantine
Conflicting or impossible observations enter quarantine and cannot become commitment-authorizing truth until reconciled or explicitly invalidated.

### RDT-18 — Resource Safety Envelope
Defines hard structural bounds for resource-state arithmetic and future control operations: no negative capacity, overflow, unbounded reservation, implicit overcommit, or authority-free mutation.

## S01 hard invariants
1. Every Resource Digital Twin snapshot is immutable once emitted.
2. Every snapshot has schema version, snapshot identity and observation timestamp/window.
3. Resource facts preserve source/provenance references.
4. Physical, reported, allocatable, reserved, committed, resident, reclaimable, external and unknown capacity remain semantically distinct.
5. Unknown is never coerced to zero.
6. Unknown is never coerced to unlimited capacity.
7. Estimated state is distinguishable from directly observed state.
8. Stale state is distinguishable from fresh state.
9. Conflicted state cannot authorize a fresh-only commitment.
10. Unsupported telemetry remains explicit.
11. Capacity arithmetic cannot produce negative available capacity.
12. Capacity arithmetic is overflow/bounds checked.
13. A release cannot free more commitment than its causal claim owns.
14. The same commitment cannot be counted twice.
15. Reconciliation cannot rewrite historical snapshots.
16. Every state transition identifies its causal predecessor(s).
17. Resource identity is independent of enumeration order.
18. Display-name changes do not silently change resource identity.
19. Runtime/process restart alone does not silently create new physical-resource identity.
20. Provider/runtime context identity remains distinct from physical device identity.
21. M07 discovery evidence is consumed by reference and not mutated.
22. M08 empirical evidence is consumed by reference and not reclassified as M09 observation.
23. M09 cannot emit M08 benchmark/capability-envelope authority.
24. M09 cannot compile an M10 execution plan.
25. M09 cannot claim predictive OOM authority.
26. M09 cannot claim thermal decision authority.
27. M09 cannot supervise/kill/restart M11 workers.
28. M09 cannot place jobs across M12 compute targets.
29. M09 cannot claim M14 model fitness.
30. M09 cannot become M55 physical storage authority.
31. M09 cannot replace M56 observability aggregation.
32. Operator-reserved headroom is never counted as IRIS allocatable capacity.
33. External consumption is represented even when ownership is unknown.
34. M09 cannot kill, suspend or evict unrelated external processes to reclaim capacity.
35. Scarcity cannot silently lower M01 quality thresholds.
36. Scarcity cannot silently weaken protected M03 semantics.
37. Scarcity outcome must be explicit and machine-readable.
38. A snapshot digest covers canonical semantic fields and provenance references.
39. Snapshot digest excludes nondeterministic serialization artifacts.
40. Conflicting observations produce conflict evidence.
41. Observation timestamps from different sources are not assumed simultaneous.
42. Reconciliation records source skew/window information where material.
43. Staleness policy is versioned.
44. Freshness requirements are purpose-sensitive and explicit.
45. State invalidation records reason and scope.
46. Invalidated state remains auditable.
47. Resource claims use typed units.
48. Unit conversion is explicit and loss-aware.
49. Claim scope identifies target resource/tier/context.
50. Claim exclusivity/shareability is explicit.
51. Hard and soft reservation semantics remain distinct.
52. S01 claim algebra cannot silently grant a lease.
53. Lease arbitration remains S02 authority.
54. Residency mutation remains S02 authority.
55. Spill/offload/prefetch execution remains S03 authority.
56. Tile/chunk/batch/precision control remains S04 authority.
57. Recovery/cleanup/leak-control actions remain S05 authority.
58. Pressure signals are evidence, not predictive OOM decisions.
59. Pressure normalization preserves original source/value/unit.
60. Impossible state enters quarantine rather than normalization-by-guess.
61. Quarantined state cannot authorize commitments.
62. Reconciliation from quarantine is explicit and auditable.
63. Resource-state mutation requires an authorized transition type.
64. No arbitrary executable callback is stored in canonical state.
65. Canonical state is provider-neutral.
66. Provider-specific fields remain versioned extension evidence.
67. Missing provider telemetry cannot fabricate measurements.
68. Synthetic fixtures are explicitly distinguishable from physical observations.
69. Test/synthetic state cannot masquerade as production resource truth.
70. 8 GB VRAM-class devices are valid first-class resources.
71. Small capacity alone is not an unsupported-device reason.
72. Multi-GPU state preserves per-device capacity and identity.
73. Host RAM and VRAM are not fungible without an explicit later transfer/offload contract.
74. NVMe/spill capacity is not counted as RAM or VRAM.
75. Reclaimable capacity is not equivalent to immediately free capacity.
76. Resident bytes are not automatically owned/evictable by IRIS.
77. Reserved bytes are not automatically resident bytes.
78. Committed bytes are not automatically physically allocated bytes.
79. External use uncertainty contributes to conservative availability.
80. Resource facts material to reproducibility require explicit M06 materiality reference, not implicit coupling.
81. Security/permission restrictions remain explicit when telemetry is unavailable.
82. Automation has the same authorization and provenance requirements as interactive control.
83. Resource state export is versioned.
84. Unknown mandatory schema semantics fail closed.
85. Older readers cannot silently ignore unknown mandatory resource semantics.
86. Every acceptance proof can identify the exact S01 invariant(s) exercised.
87. Shared proof targets explicitly enumerate all invariant IDs they claim.
88. Missing/orphan/duplicate invariant proof mappings fail validation.
89. Canonical invariant text drift requires a versioned planning amendment.
90. S01 implementation remains forbidden until the full M09 contract is frozen and independently approved.

## Required S01 proof classes
- deterministic snapshot serialization/digest;
- arithmetic conservation and bounds;
- unknown/stale/conflicted/quarantine behavior;
- provenance and identity stability;
- headroom/external-consumption semantics;
- cross-module authority firewall;
- claim algebra without lease grant;
- provider-neutral extension behavior;
- synthetic-vs-physical separation;
- invariant-to-proof integrity.

## S01 risks
- Driver/runtime telemetry may disagree or arrive at different times. Mitigation: reconciliation windows + conflict quarantine.
- “Free VRAM” can be misleading due to caches/reserved pools. Mitigation: capacity truth partition and conservative uncertainty.
- Overengineering S01 into a scheduler. Mitigation: claim algebra only; arbitration is S02 and execution planning is M10.
- Workstation usability can be destroyed by aggressive reclamation. Mitigation: protected headroom and no unrelated-process eviction.
- Resource scarcity can accidentally become a quality-degradation mechanism. Mitigation: explicit non-degradation firewall.

## S01 acceptance gate
S01 may advance to S02 planning only when:
- all 18 technology surfaces have explicit purpose/boundary/proof intent;
- all 90 invariants are present and non-contradictory;
- M07/M08/M10/M11/M12/M14/M55/M56 authority boundaries remain intact;
- 8 GB VRAM and operator headroom remain first-class;
- no implementation code is introduced;
- independent review reports zero unresolved HIGH/CRITICAL planning findings.

## STOP CONDITION
Stop at S01 planning. Do not implement M09. Do not deep-plan S02 until S01 receives independent review.


# S02 — VRAM leases, reservations and model residency

Status: `S02_PLANNING_CANDIDATE`
S01 audit: `APPROVED` at `d166781af7c3829e8101b385ed77ee062eac8537`

## S02 objective
Turn S01 resource claims into bounded, auditable VRAM/RAM resource leases and residency state without becoming the M10 workload scheduler or M11 process supervisor. S02 owns admission/arbitration of resource commitments on a target resource and the semantic lifecycle of residency.

## S02 technology surfaces

### RLG-01 — Lease Grant Fabric
Creates immutable lease grants from authorized claims only when capacity truth, freshness, headroom and conflict predicates permit commitment.

### RLG-02 — Reservation Intent Queue
Represents pending hard/soft reservation intents with stable identity, priority class supplied by policy input, deadlines and causal request refs. Queue semantics do not select workload execution order for M10.

### RLG-03 — Lease Token & Epoch Protocol
Every grant carries opaque lease identity, resource scope, quantity, epoch, validity window and owner principal. Stale epochs cannot mutate current commitment state.

### RLG-04 — Atomic Capacity Committer
Reservation-to-commit transitions are atomic at the M09 semantic boundary, preventing double grants under concurrent admission.

### RLG-05 — Model Residency Registry
Tracks model/component residency as explicit NONE / LOADING / RESIDENT / PARTIAL / EVICTING / EVICTED / UNKNOWN state with resource, lease, revision and evidence refs.

### RLG-06 — Residency Identity Binder
Binds resident material to exact model/artifact identity and revision without declaring model quality/fitness or taking M55 storage identity authority.

### RLG-07 — Shared Residency Refcounter
Supports safe shared residency across compatible consumers through ownership/ref semantics. A consumer release cannot evict residency still held by another valid owner.

### RLG-08 — Lease Renewal Gate
Renewal revalidates freshness, capacity, headroom, ownership and policy instead of silently extending stale grants.

### RLG-09 — Lease Expiry & Tombstone Ledger
Expired/revoked/released leases remain auditable tombstones so identifiers cannot be ambiguously reused.

### RLG-10 — Anti-Overcommit Firewall
Hard commitments cannot exceed conservative allocatable capacity after protected headroom and uncertainty deductions unless a later explicitly versioned overcommit policy is separately authorized.

### RLG-11 — Fairness & Starvation Evidence Fabric
Records wait age, denial reasons and repeated displacement so starvation is visible and machine-checkable. S02 exposes evidence; cross-workload scheduling remains M10.

### RLG-12 — Priority Inversion Sentinel
Detects resource-priority inversion conditions and emits evidence/required-replan signals without reordering M10 execution plans itself.

### RLG-13 — Lease Preemption Contract
Defines whether a lease is non-preemptible, cooperative-preemptible or revocable, with explicit authorization and grace semantics. It never kills a worker or unrelated process.

### RLG-14 — Residency Compatibility Matrix
Determines whether residency can be shared based on exact artifact/revision/runtime/device/precision-layout compatibility. Compatibility is resource reuse semantics, not M14 fitness.

### RLG-15 — Fragmentation Evidence Mapper
Represents allocatable-vs-contiguous/segment uncertainty and fragmentation evidence when providers expose it. Missing fragmentation telemetry remains UNKNOWN.

### RLG-16 — Warm Residency Hint Channel
Exports versioned residency/warmth hints to M10/M13 consumers without converting warmth into execution or provider-selection authority.

### RLG-17 — Lease Authorization Binder
Every lease mutation binds actor/automation identity, permission reference and causal request. Automation receives no broader authority than interactive actors.

### RLG-18 — Orphan Lease Reconciler
Detects lease ownership that can no longer be proven and quarantines/reconciles it through bounded policy. It does not inspect/kill processes as M11.

### RLG-19 — Residency Transition Journal
Append-oriented causal journal for load/resident/partial/evict transitions, preserving failure and rollback evidence.

### RLG-20 — Commitment Idempotency Shield
Idempotency keys and causal identities prevent retry storms from multiplying reservations, grants, releases or residency mutations.

## S02 hard invariants
91. A lease can be granted only from an explicit authorized resource claim.
92. Lease grant records resource identity, quantity/unit, owner, epoch and validity.
93. Lease identifiers are globally unambiguous within their authority namespace.
94. Expired lease IDs cannot be silently reused for a different commitment.
95. Hard lease admission uses conservative allocatable capacity after protected headroom.
96. Hard commitments cannot silently exceed conservative allocatable capacity.
97. Unknown capacity cannot authorize a hard lease.
98. Stale capacity cannot authorize a fresh-only hard lease.
99. Conflicted/quarantined capacity cannot authorize a lease.
100. Lease grant is atomic relative to competing grants on the same commitment domain.
101. Concurrent admission cannot double-spend the same capacity.
102. Failed grant attempts do not mutate committed capacity.
103. Reservation intent is distinct from granted lease.
104. Soft reservation is distinct from hard commitment.
105. Pending reservation is not counted as resident memory.
106. Lease renewal is an explicit transition.
107. Renewal revalidates current resource evidence.
108. Renewal cannot bypass operator headroom.
109. Renewal cannot extend a revoked authorization.
110. Stale lease epochs cannot mutate current state.
111. Release is idempotent.
112. Duplicate release cannot increase available capacity twice.
113. Revocation is distinct from release and expiry.
114. Revocation records authority and reason.
115. Expiry records a durable tombstone.
116. Lease lifecycle remains auditable after release/expiry/revocation.
117. Model residency state is explicit and typed.
118. LOADING is not equivalent to RESIDENT.
119. PARTIAL is not equivalent to RESIDENT.
120. UNKNOWN residency cannot masquerade as RESIDENT.
121. Residency binds exact artifact/model identity and revision.
122. Residency identity does not claim M14 empirical model fitness.
123. Residency identity does not replace M55 physical storage/CAS identity.
124. Residency binds target device/resource context.
125. Cross-device residency cannot be inferred from one device.
126. Shared residency requires explicit compatibility.
127. Shared residency requires ownership/reference accounting.
128. One consumer release cannot evict another consumer's valid residency.
129. Reference count cannot become negative.
130. Orphan references enter reconciliation/quarantine.
131. Orphan reconciliation cannot fabricate a live owner.
132. M09 cannot kill a worker to resolve an orphan lease.
133. M09 cannot kill/suspend unrelated processes for residency.
134. Preemption class is explicit per lease.
135. Non-preemptible leases cannot be silently revoked for convenience.
136. Cooperative preemption requires a bounded grace contract.
137. Lease preemption cannot directly implement M11 process termination.
138. Preemption evidence can request M10 replan but cannot compile that plan.
139. Priority input is explicit and provenance-bound.
140. S02 cannot invent business/workload priority absent authorized policy input.
141. Fairness evidence records wait age and denial causes.
142. Starvation evidence is not itself permission to violate capacity safety.
143. Priority inversion evidence is explicit.
144. S02 cannot reorder M10 workload execution as a hidden scheduler.
145. Residency warmth is a hint, not provider/model selection authority.
146. Warmth cannot override M01 quality policy.
147. Warmth cannot override M14 empirical fitness.
148. Compatibility requires exact declared artifact/revision semantics.
149. Unknown compatibility fails closed for sharing.
150. Precision/layout compatibility is explicit.
151. S02 cannot silently change precision to fit memory.
152. Precision changes remain S04/M10 governed decisions with quality constraints.
153. Fragmentation evidence remains separate from total free capacity.
154. Unknown fragmentation cannot be fabricated as contiguous capacity.
155. Provider-specific allocator facts remain extension evidence.
156. Lease mutation requires actor/automation authorization reference.
157. Automation cannot receive implicit elevated lease authority.
158. Idempotency identity is required for retryable commitment mutations.
159. Duplicate grant request with same idempotency identity cannot multiply commitment.
160. Conflicting reuse of an idempotency identity fails closed.
161. Residency transitions are append-auditable.
162. Failed residency transition remains recorded as failure evidence.
163. Residency journal cannot rewrite historical transitions.
164. Lease/residency state exports are versioned.
165. Unknown mandatory lease schema semantics fail closed.
166. Older readers cannot silently ignore unknown mandatory lease semantics.
167. M07 hardware facts remain referenced, not mutated.
168. M08 envelopes may constrain admission but are not reauthored by M09.
169. M09 lease state does not become M06 production identity.
170. Material lease/residency effects on reproducibility require explicit M06 materiality reference.
171. M10 retains workload-plan and predictive OOM authority.
172. M11 retains process/worker lifecycle authority.
173. M12 retains compute placement authority.
174. M14 retains model fitness authority.
175. M55 retains physical storage/cache authority.
176. M56 retains observability aggregation authority.
177. Scarcity denial cannot silently lower M01 quality.
178. Scarcity denial cannot silently weaken M03 semantics.
179. 8 GB VRAM devices use the same safety semantics as larger devices.
180. Small devices cannot be rejected solely because they require tighter lease sizing.
181. Multi-GPU leases remain per-resource unless an explicit composite claim is declared.
182. Composite claims preserve each member resource identity and quantity.
183. A composite grant fails atomically if its required hard members cannot be committed.
184. Partial composite grant cannot masquerade as complete.
185. Reservation deadlines use explicit clock semantics.
186. Clock uncertainty/skew material to expiry remains represented.
187. Lease validity cannot depend on wall-clock text parsing alone.
188. Every S02 acceptance proof identifies exact invariant IDs.
189. Shared proof targets explicitly enumerate claimed S02 invariant IDs.
190. Missing/orphan/duplicate S02 proof mappings fail validation.

## Required S02 proof classes
- concurrent atomic grant/double-spend prevention;
- idempotent grant/release/retry;
- expiry/revocation/renewal epoch behavior;
- headroom and unknown/stale/conflicted denial;
- residency lifecycle and exact identity binding;
- shared residency/reference safety;
- orphan/preemption safety without process control;
- fairness/starvation/priority-inversion evidence;
- fragmentation and compatibility fail-closed behavior;
- multi-GPU/composite atomicity;
- cross-module authority firewall;
- invariant-to-proof integrity.

## S02 risks
- Lease logic can accidentally become a scheduler. Mitigation: M09 admits resource claims; M10 owns workload ordering/plans.
- Provider allocators may report misleading free/fragmented capacity. Mitigation: conservative truth partition plus explicit UNKNOWN fragmentation.
- Shared model residency can cause use-after-evict behavior. Mitigation: exact compatibility + owner refs + atomic release semantics.
- Aggressive preemption can damage active work. Mitigation: explicit preemption classes and M11 process boundary.
- Retry storms can multiply commitments. Mitigation: idempotency shield and epoch protocol.

## S02 acceptance gate
S02 may advance to S03 planning only when:
- S01 remains unchanged except additive clarification;
- all 20 S02 surfaces and invariants 91-190 are explicit;
- lease/residency semantics remain distinct from M10 scheduling and M11 process control;
- no hidden precision/quality degradation is authorized;
- concurrent/idempotent/composite commitment behavior is proofable;
- no implementation code is introduced;
- independent review reports zero unresolved HIGH/CRITICAL findings.

## STOP CONDITION
Stop at S02 planning. Do not implement M09. Do not deep-plan S03 until S02 receives independent review.
