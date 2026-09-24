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


# S03 — RAM/NVMe spill, offload and prefetch planning

Status: `S03_PLANNING_CANDIDATE`
S02 audit: `APPROVED` at `e4a5779de5183de1d21c238f73eb63c6a8344482`

## S03 objective
Define safe, evidence-bound movement of resource-resident material between VRAM, host RAM and eligible M55-backed spill targets. M09 owns resource-tier movement intent/state and bounded transfer contracts. M55 retains physical storage/CAS authority; M10 retains workload execution-plan authority; M11 retains worker/process execution.

## S03 technology surfaces

### RSO-01 — Tiered Resource Mobility Fabric
Defines typed movement between VRAM, RAM and eligible spill tiers with exact source/destination identities, units and lifecycle state.

### RSO-02 — Offload Transaction Protocol
Models PREPARED / COPYING / VERIFIED / COMMITTED / ABORTED offload transitions so source residency is not released before destination integrity is proven.

### RSO-03 — Spill Target Capability Contract
Consumes versioned M55 capability references for capacity, durability class, latency evidence and access constraints without turning M09 into a storage provider.

### RSO-04 — Transfer Integrity Seal
Binds moved material to exact artifact/revision/segment identity and integrity digest before residency ownership can transition.

### RSO-05 — Two-Phase Residency Handoff
Separates destination verification from source release to prevent destructive move-on-copy-failure behavior.

### RSO-06 — Prefetch Intent Fabric
Represents bounded prefetch requests and evidence, but M10 decides whether/when a workload plan should request them.

### RSO-07 — Prefetch Budget Governor
Caps speculative RAM/VRAM/spill occupancy and transfer concurrency so prefetch cannot consume protected headroom or starve admitted work.

### RSO-08 — Transfer Cost Evidence Model
Carries measured/estimated bandwidth, latency, serialization and synchronization cost with M08 provenance where applicable. It is evidence, not M10 scheduling policy.

### RSO-09 — Spill Encryption/Permission Binder
Requires storage/security authorization references for spill targets and preserves restricted-data constraints without taking M53/M54 authority.

### RSO-10 — Dirty-State & Writeback Contract
Distinguishes clean reproducible material from dirty state requiring verified writeback before release.

### RSO-11 — Partial Segment Mobility
Allows explicitly segmentable model/assets to move in bounded chunks while preserving exact segment map and completeness state.

### RSO-12 — Transfer Cancellation & Resume Ledger
Records bounded cancellation/resume checkpoints without assuming arbitrary provider resume support.

### RSO-13 — Transfer Idempotency Shield
Retry identities prevent duplicate copies from becoming duplicate commitments or conflicting residency truth.

### RSO-14 — Bandwidth Contention Sentinel
Represents transfer contention and external I/O pressure as evidence; it cannot throttle unrelated processes or become M12 orchestration.

### RSO-15 — Spill Wear & Endurance Evidence Port
Accepts optional device/endurance evidence and policy constraints for local NVMe without claiming hardware-health authority when telemetry is absent.

### RSO-16 — Data Locality Hint Channel
Exports current tier/locality evidence to M10/M12 while preserving their plan/placement authority.

### RSO-17 — Transfer Failure Quarantine
Incomplete, corrupt, identity-mismatched or permission-invalid destinations are quarantined and cannot authorize source eviction.

### RSO-18 — Resource Mobility Journal
Append-oriented causal journal linking lease, residency, source/destination, bytes, integrity, authorization and outcome.

### RSO-19 — Spill Garbage Eligibility Contract
Marks abandoned/expired spill artifacts as eligible for M55 cleanup but never deletes physical storage itself.

### RSO-20 — Zero-Fabrication Offload Firewall
If a required tier/provider/capability is unavailable, S03 returns explicit UNSUPPORTED/UNAVAILABLE/REQUIRE_REPLAN rather than pretending an offload occurred.

## S03 hard invariants
191. Every movement identifies exact source and destination resource tiers.
192. VRAM, RAM and spill tiers remain semantically distinct.
193. A movement intent is not evidence that bytes moved.
194. Offload state is explicit and typed.
195. Source residency cannot be released before destination verification.
196. Copy failure cannot silently become successful offload.
197. Destination integrity is checked before COMMITTED state.
198. Integrity failure quarantines the destination.
199. Quarantined destination cannot authorize source eviction.
200. Transfer identity binds exact artifact/revision.
201. Segmented movement binds exact segment identity/range.
202. Partial transfer cannot masquerade as complete residency.
203. Destination capacity must be admitted before hard transfer commitment.
204. Protected operator headroom applies to destination RAM/VRAM.
205. Prefetch cannot consume protected headroom.
206. Prefetch is bounded by explicit byte/concurrency/time budgets.
207. Speculative prefetch is distinguishable from required residency.
208. Prefetch intent cannot reorder an M10 workload plan.
209. M09 cannot infer future workload demand without an authorized request/hint.
210. Transfer cost evidence records observed versus estimated status.
211. M08-derived transfer evidence remains provenance-bound.
212. Estimated bandwidth cannot masquerade as measured bandwidth.
213. Unknown transfer cost remains UNKNOWN.
214. Unknown transfer cost cannot be coerced to zero.
215. M09 cannot invent a storage target absent M55 capability reference.
216. M55 retains physical storage allocation/CAS authority.
217. Spill path strings alone do not constitute trusted storage capability.
218. Storage durability class remains explicit.
219. Temporary spill cannot masquerade as durable persistence.
220. Spill authorization preserves security/permission references.
221. M09 cannot weaken M53 rights/provenance constraints.
222. M09 cannot weaken M54 security/restricted-content constraints.
223. Restricted material cannot spill to an unauthorized tier.
224. Encryption requirement is explicit when imposed by owning policy.
225. M09 does not invent cryptographic/security policy.
226. Dirty state is distinguishable from clean reproducible state.
227. Dirty state requiring writeback cannot be discarded as clean.
228. Writeback success requires destination verification.
229. Clean reproducible material may be marked reconstructible only with valid reconstruction reference.
230. Reconstruction reference does not replace M06 production/rebuild authority.
231. Cancellation leaves explicit transfer outcome/state.
232. Cancellation cannot silently release source residency.
233. Resume requires compatible provider/capability support.
234. Unsupported resume fails explicitly.
235. Retry uses stable idempotency identity.
236. Duplicate retry cannot multiply committed destination residency.
237. Conflicting idempotency reuse fails closed.
238. Transfer concurrency is bounded.
239. Transfer byte budget is bounded.
240. Transfer time/deadline semantics are explicit.
241. Unbounded retry is forbidden.
242. Bandwidth contention is evidence, not permission to throttle unrelated processes.
243. M09 cannot suspend/kill unrelated I/O consumers.
244. External I/O pressure remains explicit uncertainty/evidence.
245. NVMe endurance evidence is optional and provenance-bound.
246. Missing wear telemetry remains UNKNOWN.
247. Unknown wear cannot be fabricated as healthy or exhausted.
248. S03 cannot claim device-health authority.
249. Locality evidence identifies exact tier/resource.
250. Locality hint cannot become M12 placement decision.
251. Locality hint cannot become M10 execution plan.
252. Source/destination device identity survives enumeration reorder.
253. Cross-device transfers preserve both device identities.
254. Composite transfers preserve per-member outcome.
255. Partial composite success cannot masquerade as complete success.
256. Atomic-required composite transfer fails closed if any mandatory member fails.
257. Spill garbage eligibility is distinct from physical deletion.
258. M09 cannot delete M55 physical artifacts directly.
259. Cleanup eligibility records causal lease/residency refs.
260. Active referenced spill material cannot be marked garbage solely by age.
261. Transfer journal is append-auditable.
262. Historical transfer evidence cannot be rewritten to hide failure.
263. Provider-specific transfer fields remain versioned extensions.
264. Unknown mandatory mobility semantics fail closed.
265. Older readers cannot silently ignore unknown mandatory transfer semantics.
266. Synthetic transfer fixtures are distinguishable from physical transfers.
267. Synthetic success cannot authorize production source eviction.
268. Missing provider/runtime cannot fabricate transfer completion.
269. UNSUPPORTED and UNAVAILABLE remain distinct where actionable.
270. REQUIRE_REPLAN does not itself compile an M10 plan.
271. M10 retains adaptive execution planning.
272. M11 retains worker/process lifecycle.
273. M12 retains placement/orchestration.
274. M14 retains model fitness.
275. M55 retains storage/CAS/cache/archive authority.
276. M56 retains observability aggregation.
277. Offload cannot silently reduce precision/quality.
278. Offload cannot silently weaken M03 protected semantics.
279. 8 GB VRAM devices may use offload as a first-class resource strategy, not as unsupported fallback.
280. Smaller VRAM does not authorize unsafe overcommit.
281. RAM offload does not imply NVMe spill availability.
282. NVMe spill does not imply RAM residency.
283. Host RAM and VRAM transfer costs remain distinct.
284. Resource mobility state is versioned/exportable.
285. Every S03 acceptance proof identifies exact invariant IDs.
286. Shared proof targets explicitly enumerate claimed S03 invariant IDs.
287. Missing/orphan/duplicate S03 proof mappings fail validation.
288. S03 cannot grant new lease capacity by merely moving bytes.
289. Source lease/accounting is reconciled only after verified handoff.
290. S03 implementation remains forbidden until the full M09 contract is frozen and independently approved.

## Required S03 proof classes
- verified two-phase offload and source-retention on failure;
- integrity mismatch/quarantine;
- bounded prefetch and headroom preservation;
- measured-vs-estimated transfer evidence;
- M55/M53/M54 authority firewalls;
- dirty/writeback/reconstructible semantics;
- cancellation/resume/idempotent retry;
- bounded concurrency/bytes/time/retries;
- segmented/composite partial-failure semantics;
- synthetic-vs-physical transfer separation;
- garbage-eligibility without physical deletion;
- invariant-to-proof integrity.

## S03 risks
- Offload may be treated as a successful move before bytes are durable/usable. Mitigation: two-phase handoff + integrity verification.
- NVMe spill can accidentally turn M09 into a storage layer. Mitigation: M55 capability contract and cleanup eligibility only.
- Prefetch can consume the very headroom intended to keep the workstation usable. Mitigation: independent speculative budgets.
- Transfer benchmarks can be stale/context-specific. Mitigation: M08 provenance plus measured/estimated/unknown distinction.
- Partial model movement can create false residency. Mitigation: exact segment maps and completeness state.

## S03 acceptance gate
S03 may advance to S04 planning only when:
- S01/S02 approved semantics remain intact;
- all 20 S03 surfaces and invariants 191-290 are explicit;
- source release requires verified destination handoff;
- prefetch and transfer operations are bounded;
- M55/M53/M54/M10/M11/M12 boundaries remain intact;
- no silent quality/precision degradation is authorized;
- no implementation code is introduced;
- independent review reports zero unresolved HIGH/CRITICAL findings.

## STOP CONDITION
Stop at S03 planning. Do not implement M09. Do not deep-plan S04 until S03 receives independent review.


# S04 — Dynamic tile/chunk/batch/precision control

Status: `S04_PLANNING_CANDIDATE`
S03 audit: `APPROVED` at `4aeee77d62476cf48f4e1b5c6b4dcd798f7a8e17`

## S04 objective
Define bounded resource-shaping controls that expose feasible tile, chunk, batch and precision alternatives under current M09 resource truth. S04 may derive resource-feasible control bounds and apply an explicitly authorized control choice. M10 remains owner of execution-plan selection; M01/M14 and domain owners remain quality/fitness authorities. No resource pressure may silently reduce fidelity.

## S04 technology surfaces

### RSC-01 — Adaptive Resource Shape Fabric
Represents provider-neutral shape dimensions such as tile extent, chunk extent, batch cardinality and precision mode as typed, bounded control axes.

### RSC-02 — Feasible Shape Envelope
Derives conservative resource-feasible ranges from M08 evidence plus current M09 state without claiming that a feasible shape is optimal or quality-approved.

### RSC-03 — Quality Constraint Binder
Requires every lossy/precision-affecting control to carry explicit M01/domain quality authorization or remain unavailable.

### RSC-04 — Precision Safety Matrix
Classifies precision transitions as lossless-equivalent, quality-sensitive, unsupported or unknown for the declared operation/context, with evidence refs rather than global assumptions.

### RSC-05 — Tile Boundary Integrity Contract
Defines overlap/halo/seam/context requirements so resource-driven tiling cannot silently create spatial discontinuities.

### RSC-06 — Temporal Chunk Integrity Contract
Defines overlap/state/context boundaries for temporal chunking so video/audio/animation continuity obligations remain explicit.

### RSC-07 — Batch Isolation Governor
Ensures batch resizing changes resource aggregation only and cannot silently alter per-item semantic settings, seeds, identity or acceptance criteria.

### RSC-08 — Shape Transition Ledger
Records requested/applied resource-shape transitions, causal pressure evidence, authorization and resulting resource state.

### RSC-09 — Hysteresis & Thrash Guard
Prevents repeated up/down resource-shape oscillation under noisy pressure by bounded hysteresis/cooldown evidence.

### RSC-10 — Resource Control Epoch
Binds shape controls to a current resource-state epoch so stale pressure cannot mutate a newer execution context.

### RSC-11 — Provider Capability Adapter
Maps canonical shape controls to provider-supported knobs and reports unsupported/quantized ranges explicitly.

### RSC-12 — Control Reversibility Descriptor
Declares whether a shape/precision transition is reversible, requires restart/reload, or changes reproducibility/materiality.

### RSC-13 — Quality-Neutral Preference Channel
Allows M09 to expose resource-cheaper alternatives only when quality-equivalence is already established by owning evidence; it does not establish equivalence itself.

### RSC-14 — Minimum Viable Shape Guard
Prevents resource adaptation below provider/domain structural minima even when smaller shapes would appear to fit memory.

### RSC-15 — Shape Compatibility Matrix
Captures incompatible combinations among tile/chunk/batch/precision controls and provider/runtime constraints.

### RSC-16 — Adaptation Budget Governor
Bounds number, frequency and cumulative magnitude of control changes within an execution context.

### RSC-17 — Degradation Consent Gate
Quality-sensitive precision or shape degradation requires explicit authorized consent/policy reference and cannot be inferred from scarcity.

### RSC-18 — Replan Signal Fabric
Emits typed FIT / NO_FIT / REQUIRE_REPLAN / REQUIRE_OFFLOAD / QUALITY_AUTH_REQUIRED / UNKNOWN outcomes to M10 without selecting the plan.

### RSC-19 — Shape Evidence Projection
Exports exact state/envelope/control/provenance refs for reproducibility and M56 observation without transferring authority.

### RSC-20 — Scarcity Escape Hatch Firewall
When no safe feasible shape exists, fails closed with explicit evidence rather than entering unbounded search, unsafe overcommit or silent quality reduction.

## S04 hard invariants
291. Tile/chunk/batch/precision are distinct typed control axes.
292. A feasible resource shape is not automatically a selected execution plan.
293. A resource-feasible shape is not automatically quality-approved.
294. M10 retains execution-plan selection authority.
295. M01/domain quality authority remains binding.
296. M14 model fitness evidence remains external authority.
297. Resource pressure cannot silently reduce precision.
298. Resource pressure cannot silently reduce spatial fidelity.
299. Resource pressure cannot silently reduce temporal fidelity.
300. Resource pressure cannot silently alter protected M03 semantics.
301. Quality-sensitive control requires explicit authorization/evidence.
302. Absence of quality authorization fails closed for lossy adaptation.
303. Unknown quality effect fails closed for automatic lossy adaptation.
304. Quality-equivalent status must reference owning evidence.
305. M09 cannot self-declare quality equivalence merely because memory use decreases.
306. Precision modes are explicit and versioned.
307. Precision transition compatibility is context-specific.
308. Unknown precision compatibility is not assumed safe.
309. Unsupported precision mode fails explicitly.
310. Precision change cannot silently mutate model/artifact identity.
311. Material precision change carries reproducibility/materiality evidence.
312. Tile dimensions use explicit units/axes.
313. Tile overlap/halo requirements are explicit.
314. Tiling cannot discard required spatial context silently.
315. Tile seam obligations remain explicit.
316. Tile shape below structural minimum is rejected.
317. Temporal chunk dimensions use explicit time/frame/sample semantics.
318. Temporal overlap/context requirements are explicit.
319. Chunking cannot silently reset required temporal state.
320. Chunking cannot silently break continuity obligations.
321. Chunk size below structural minimum is rejected.
322. Batch cardinality is explicit.
323. Batch resizing cannot alter per-item semantic configuration.
324. Batch resizing cannot silently alter deterministic seed identity where seed is material.
325. Batch resizing cannot merge distinct item identities.
326. Batch isolation failures fail closed.
327. Feasible shape derivation uses current versioned resource evidence.
328. Stale resource epoch cannot authorize a shape mutation.
329. Conflicted/quarantined resource state cannot authorize automatic adaptation.
330. Unknown resource feasibility remains UNKNOWN.
331. M08 capability evidence is referenced, not rewritten.
332. M09 state can narrow feasibility but cannot expand M08 evidence without new evidence.
333. Provider capability mapping is explicit.
334. Unsupported provider knob cannot be fabricated.
335. Provider quantization/step constraints are represented.
336. Canonical requested value and provider-applied value remain distinguishable.
337. Applied control is verified where provider feedback exists.
338. Missing provider feedback remains UNKNOWN, not assumed applied.
339. Shape transitions are append-auditable.
340. Transition records causal pressure/evidence.
341. Transition records authorization source.
342. Transition records prior and resulting control state.
343. Hysteresis policy is explicit/versioned.
344. Cooldown policy is explicit/versioned.
345. Noisy pressure cannot cause unbounded adaptation thrash.
346. Adaptation count is bounded per execution context.
347. Adaptation frequency is bounded.
348. Cumulative adaptation magnitude is bounded where meaningful.
349. Unbounded search across shape combinations is forbidden.
350. Feasible search uses declared finite domains/bounds.
351. Compatibility matrix rejects known-invalid control combinations.
352. Unknown mandatory compatibility fails closed.
353. Reversibility is explicit.
354. Irreversible/material transitions require explicit authorization.
355. Restart/reload-required transition cannot masquerade as live-safe.
356. Resource-shape control cannot directly restart/kill workers.
357. M11 retains process lifecycle.
358. M12 retains placement/orchestration.
359. M55 retains storage/CAS authority.
360. M56 retains observability aggregation.
361. S04 cannot silently invoke S03 offload.
362. REQUIRE_OFFLOAD is a signal/request, not proof offload occurred.
363. S04 cannot silently grant S02 leases.
364. Shape application must respect current valid lease/headroom constraints.
365. Operator headroom cannot be consumed by adaptation.
366. 8 GB VRAM remains first-class for bounded shaping.
367. Small VRAM does not justify violating provider structural minima.
368. Small VRAM does not justify unsafe overcommit.
369. If no safe shape fits, result is explicit NO_FIT/REQUIRE_REPLAN rather than degradation.
370. Degradation consent is scoped to exact operation/context.
371. Consent for one precision/shape change cannot authorize unrelated degradation.
372. Revoked/expired consent cannot authorize new adaptation.
373. Automation has no broader degradation authority than interactive actors.
374. Quality-neutral preference may be used only with valid equivalence evidence.
375. Warm residency/resource cost hints cannot override quality constraints.
376. Shape evidence export is versioned.
377. Unknown mandatory shape schema semantics fail closed.
378. Older readers cannot silently ignore mandatory control semantics.
379. Synthetic shape tests are distinguishable from production application.
380. Synthetic fit cannot authorize production resource commitment.
381. Applied shape state distinguishes REQUESTED / APPLIED / VERIFIED / FAILED / UNKNOWN.
382. REQUESTED cannot masquerade as APPLIED.
383. APPLIED without verification cannot masquerade as VERIFIED.
384. Failed adaptation cannot silently mutate canonical current control state.
385. Retry of shape application uses idempotency/epoch semantics.
386. Stale retry cannot overwrite newer applied state.
387. Shape change affecting reproducibility carries explicit M06 materiality reference.
388. Every S04 acceptance proof identifies exact invariant IDs.
389. Shared proof targets explicitly enumerate claimed S04 invariant IDs.
390. Missing/orphan/duplicate S04 proof mappings fail validation.

## Required S04 proof classes
- finite feasible-envelope derivation under current resource state;
- quality-authorization and unknown-quality fail-closed behavior;
- precision compatibility and provider quantization;
- spatial tile overlap/seam/context constraints;
- temporal chunk continuity/context constraints;
- batch isolation and deterministic identity;
- epoch/hysteresis/adaptation-budget anti-thrash;
- requested/applied/verified provider feedback states;
- no-fit/replan/offload signaling without hidden execution;
- 8 GB VRAM bounded-shaping scenarios;
- cross-module authority firewall;
- invariant-to-proof integrity.

## S04 risks
- “Adaptive” can become a euphemism for silent quality loss. Mitigation: quality constraint binder + degradation consent gate.
- Tile/chunk shrinking can introduce seams or temporal discontinuity. Mitigation: explicit spatial/temporal integrity contracts.
- Runtime pressure can cause oscillating settings. Mitigation: hysteresis, epochs and bounded adaptation budgets.
- Provider knobs differ in units/steps/meaning. Mitigation: capability adapter with requested/applied/verified separation.
- Searching every combination can become expensive/unbounded. Mitigation: finite domains and hard search bounds.

## S04 acceptance gate
S04 may advance to S05 planning only when:
- S01-S03 approved semantics remain intact;
- all 20 S04 surfaces and invariants 291-390 are explicit;
- quality-sensitive adaptation always requires owning authorization/evidence;
- M10 remains execution-plan owner and M11 remains lifecycle owner;
- tile/chunk/batch/precision controls are bounded and provider-aware;
- no implementation code is introduced;
- independent review reports zero unresolved HIGH/CRITICAL findings.

## STOP CONDITION
Stop at S04 planning. Do not implement M09. Do not deep-plan S05 until S04 receives independent review.


# S05 — Memory-pressure recovery, cleanup and leak detection

Status: `S05_PLANNING_CANDIDATE`
S04 audit: `APPROVED` at `204370ff4fd53f0f6de793cb0ed44a3e1fb5abc0`

## S05 objective
Complete M09 with bounded recovery semantics for resource pressure, stale commitments, leaked resource ownership and cleanup eligibility. S05 detects and reconciles M09-owned resource state; it does not become M11 process supervision, M55 physical deletion, M10 predictive planning or M56 observability aggregation.

## S05 technology surfaces

### RPR-01 — Memory Pressure State Machine
Normalizes resource pressure into explicit NORMAL / ELEVATED / HIGH / CRITICAL / UNKNOWN states with source, scope, freshness and confidence evidence.

### RPR-02 — Recovery Action Contract
Defines bounded M09-owned recovery actions such as deny-new-lease, release-expired-commitment, request-cooperative-release, mark-spill-cleanup-eligible and emit replan/offload signals.

### RPR-03 — Leak Suspicion Engine
Detects discrepancies between M09 commitment/residency ledgers and current evidence, producing suspicion with confidence rather than declaring a leak from one missing sample.

### RPR-04 — Leak Confirmation Protocol
Requires multi-source/temporal evidence or explicit owner loss before a suspected resource leak can become CONFIRMED.

### RPR-05 — Ownership Liveness Binder
Consumes owner/process liveness references from M11 or authorized provider evidence without taking process-lifecycle authority.

### RPR-06 — Stale Commitment Reaper
Reconciles expired/revoked/orphaned M09 commitments through idempotent ledger transitions. It never kills processes to reclaim memory.

### RPR-07 — Cooperative Release Handshake
Requests release from valid owners with deadline/result evidence while preserving owner authority and bounded waiting.

### RPR-08 — Recovery Escalation Ladder
Orders only M09-owned safety responses from least disruptive to fail-closed outcomes; cross-module actions are emitted as requests/signals.

### RPR-09 — Cleanup Eligibility Fabric
Marks M09-created spill/residency artifacts or metadata as cleanup-eligible with causal proof; M55 performs physical deletion.

### RPR-10 — False-Leak Quarantine
Ambiguous ownership, telemetry gaps or delayed provider accounting enter quarantine instead of destructive cleanup.

### RPR-11 — Pressure Hysteresis Governor
Uses versioned entry/exit thresholds, dwell windows and cooldowns so noisy telemetry cannot flap recovery state.

### RPR-12 — Recovery Budget Governor
Bounds recovery attempts, retries, elapsed time and resource churn per incident.

### RPR-13 — Incident Causality Capsule
Binds pressure episode, snapshots, leases, residency, transfers, shape changes, owner refs, recovery attempts and outcome into deterministic evidence.

### RPR-14 — Resource Debt Ledger
Tracks unresolved committed/reclaimable/unknown resource discrepancies as explicit debt rather than silently restoring capacity.

### RPR-15 — Post-Recovery Reconciliation Gate
Requires fresh state reconciliation after recovery before reclaimed capacity can authorize new hard commitments.

### RPR-16 — Recovery Idempotency Shield
Stable incident/action identities prevent duplicate retries from releasing/reaping/accounting the same resource twice.

### RPR-17 — External Pressure Protection Firewall
External/unowned pressure may constrain IRIS admission but cannot authorize termination, suspension or eviction of unrelated workloads.

### RPR-18 — Recovery Quality Firewall
Recovery may pause/deny/request-replan but cannot silently degrade M01 quality, M03 semantics or precision/fidelity.

### RPR-19 — Leak Trend Evidence Port
Exports bounded leak/pressure trend evidence to M56/M10 without becoming global telemetry aggregation or predictive OOM authority.

### RPR-20 — Safe Failure Capsule
When safe recovery cannot be proven, emits a complete fail-closed incident package and preserves uncertain accounting instead of fabricating free capacity.

## S05 hard invariants
391. Pressure state is explicit and scoped to a resource/context.
392. Pressure state records freshness/confidence/source evidence.
393. UNKNOWN pressure cannot masquerade as NORMAL.
394. One transient sample cannot alone confirm a resource leak.
395. Leak suspicion and leak confirmation remain distinct.
396. Leak confirmation records its evidence basis.
397. Missing telemetry can increase uncertainty but cannot fabricate a leak.
398. Delayed provider accounting is representable.
399. Ambiguous leak state enters quarantine.
400. Quarantine cannot authorize destructive cleanup.
401. M09 recovery actions are explicitly enumerated/versioned.
402. Unknown recovery action fails closed.
403. Recovery cannot kill/restart a worker.
404. M11 retains process/worker lifecycle authority.
405. M09 may consume owner-liveness evidence by reference.
406. Missing owner-liveness evidence remains UNKNOWN.
407. Unknown owner liveness cannot be treated as dead.
408. Expired lease alone does not prove an external process can be terminated.
409. Stale commitment reconciliation is ledger/accounting action only.
410. Reaping is idempotent.
411. Duplicate reap cannot free capacity twice.
412. Revoked/released commitment cannot be reaped as a new release.
413. Cooperative release request has stable identity.
414. Cooperative release has bounded wait/deadline semantics.
415. Timeout is explicit and not equivalent to successful release.
416. Failed cooperative release cannot fabricate reclaimed capacity.
417. Recovery escalation begins with least disruptive M09-owned safe actions.
418. Escalation steps requiring M10/M11/M55 authority are requests/signals only.
419. M09 cannot compile an M10 recovery execution plan.
420. M09 cannot execute M55 physical deletion.
421. Cleanup eligibility is distinct from cleanup completion.
422. Cleanup eligibility records exact artifact/state/causal refs.
423. Active referenced artifacts cannot be marked cleanup-eligible without valid release semantics.
424. Unknown reference state fails closed for cleanup eligibility.
425. Physical deletion evidence, if returned by M55, remains external evidence.
426. External/unowned pressure constrains allocatable capacity conservatively.
427. External pressure cannot authorize killing/suspending unrelated processes.
428. External pressure cannot authorize stealing externally owned memory.
429. Headroom remains protected during recovery.
430. Recovery cannot consume protected headroom to “fix” pressure.
431. Pressure entry thresholds are versioned.
432. Pressure exit thresholds are versioned.
433. Entry/exit hysteresis is explicit.
434. Dwell/cooldown semantics are bounded.
435. Noisy pressure cannot create unbounded recovery flapping.
436. Recovery attempts are bounded.
437. Recovery retry count is bounded.
438. Recovery elapsed time is bounded.
439. Recovery resource churn is bounded.
440. Unbounded cleanup/recovery loops are forbidden.
441. Incident identity is stable and unambiguous.
442. Incident evidence links exact relevant snapshots.
443. Incident evidence links exact leases/residency/transfers where material.
444. Incident evidence links exact shape-control transitions where material.
445. Incident evidence preserves failed recovery attempts.
446. Historical incident evidence cannot be rewritten to hide failure.
447. Resource debt is explicit.
448. Resource debt cannot be silently converted into free capacity.
449. Debt records quantity/unit/resource scope and uncertainty.
450. Debt reconciliation is an explicit transition.
451. Post-recovery capacity cannot authorize new hard commitments before required fresh reconciliation.
452. Reconciliation uses current epoch/state.
453. Stale recovery result cannot overwrite newer resource truth.
454. Recovery actions use idempotency identities.
455. Duplicate recovery request cannot multiply state mutation.
456. Conflicting idempotency reuse fails closed.
457. Recovery cannot silently lower precision.
458. Recovery cannot silently lower spatial/temporal fidelity.
459. Recovery cannot silently weaken M03 protected semantics.
460. Recovery cannot silently lower M01 acceptance thresholds.
461. Quality-sensitive alternative requires the same S04 authorization gates.
462. REQUIRE_REPLAN is a signal, not an M10 plan.
463. REQUIRE_OFFLOAD is a signal, not proof S03 offload occurred.
464. Lease denial is not permission to alter workload semantics.
465. 8 GB VRAM remains first-class under recovery policy.
466. Small VRAM alone is not evidence of a leak.
467. Small VRAM alone is not justification for aggressive cleanup.
468. Recovery preserves S02 lease ownership semantics.
469. Recovery preserves S03 verified-handoff semantics.
470. Recovery preserves S04 quality/adaptation semantics.
471. M07 hardware facts remain external referenced truth.
472. M08 empirical evidence remains external referenced truth.
473. M10 retains predictive OOM/thermal and execution planning.
474. M11 retains lifecycle/process control.
475. M12 retains placement/orchestration.
476. M14 retains model fitness.
477. M53/M54 retain rights/security authority.
478. M55 retains physical storage/CAS/delete authority.
479. M56 retains global observability aggregation.
480. Leak trend export is evidence only.
481. Trend evidence does not itself predict future OOM.
482. Trend evidence includes observation windows/sample semantics.
483. Unknown trend gaps remain explicit.
484. Synthetic pressure/leak fixtures are distinguishable from production incidents.
485. Synthetic recovery cannot authorize production capacity reclamation.
486. Missing provider/runtime cannot fabricate recovery success.
487. Recovery result distinguishes REQUESTED / ATTEMPTED / VERIFIED / FAILED / UNKNOWN.
488. REQUESTED cannot masquerade as ATTEMPTED.
489. ATTEMPTED cannot masquerade as VERIFIED.
490. FAILED/UNKNOWN cannot authorize reclaimed capacity.
491. Safe failure preserves uncertain accounting.
492. Safe failure emits machine-readable reason/evidence.
493. Safe failure cannot silently reset the Resource Digital Twin to a healthy state.
494. Resource recovery exports are versioned.
495. Unknown mandatory recovery semantics fail closed.
496. Older readers cannot silently ignore mandatory recovery semantics.
497. Material recovery effects on reproducibility carry explicit M06 materiality refs.
498. Every S05 acceptance proof identifies exact invariant IDs.
499. Shared proof targets explicitly enumerate claimed S05 invariant IDs.
500. Missing/orphan/duplicate S05 proof mappings fail validation.

## Required S05 proof classes
- pressure state/hysteresis and UNKNOWN behavior;
- suspicion-vs-confirmed leak evidence;
- owner-liveness UNKNOWN safety;
- idempotent stale-commitment reconciliation;
- cooperative release timeout/failure;
- bounded recovery escalation and budgets;
- cleanup eligibility without physical deletion;
- resource debt and no fabricated reclamation;
- fresh post-recovery reconciliation gate;
- external-pressure non-interference;
- recovery quality firewall;
- requested/attempted/verified/failed state separation;
- safe-failure capsule;
- invariant-to-proof integrity.

## S05 risks
- False leak detection can corrupt accounting or active work. Mitigation: suspicion/confirmation split and quarantine.
- Recovery logic can drift into process management. Mitigation: M11 liveness references and signal-only cross-authority escalation.
- “Cleanup” can become destructive storage behavior. Mitigation: M09 marks eligibility; M55 owns deletion.
- Pressure oscillation can cause churn. Mitigation: hysteresis, dwell/cooldown and incident budgets.
- Recovery can fabricate free capacity after uncertain failure. Mitigation: Resource Debt Ledger + fresh reconciliation gate.

## S05 acceptance gate
S05 completes session-level M09 planning only when:
- S01-S04 approved semantics remain intact;
- all 20 S05 surfaces and invariants 391-500 are explicit;
- uncertain ownership/reclamation always fails closed;
- M11/M55/M10/M56 boundaries remain intact;
- recovery is bounded, idempotent and non-destructive outside M09 authority;
- no silent quality degradation is authorized;
- no implementation code is introduced;
- independent review reports zero unresolved HIGH/CRITICAL findings.

## M09 session-planning totals after S05
- canonical sessions: 5/5 planned;
- technology surfaces: 98;
- hard invariants: 500;
- implementation code: 0;
- implementation authority: NOT ADMITTED.

## NEXT GATE
After independent S05 audit, perform the M09 Final Technology Review. Consolidate overlaps, classify mandatory independent surfaces vs absorbed components, then run the M10-M60 Forward Compatibility Scan. Do not freeze or implement M09 before those gates complete.

## STOP CONDITION
Stop at S05 planning. Do not implement M09. Do not start M10 deep planning. Final Technology Review requires a separate independent gate.
