# IRIS-WO-0065 | Context Lock Git mode guard

**Status:** PROPOSED / SOURCE_LOCKED_AUTHOR_TIME, not promoted to main.
**Issue:** #186. **Trusted base:** `2285cb16ebc6f28d909880e72611c2bbca4388e3` (tree `033f9583e5e7cdaa74388693ed8ea1deb25d9b69`). **Last verified exact-main Governance:** #36503569711, 4667/4667 plus same-main Socket Project Report success.
**Original-source manifest anchor:** `.engineering/context-locks/IRIS-WO-0064-WO0063-CANONICAL-CLOSEOUT.json` Git blob `1e0788cb1643ab71e60a91be77232faf9b63c364`; preserve all 26 original paths plus that anchor, prior real-Git verifier regression file and actual workflow source (29/29 exact original Git blobs). **Strict allowlist:** six exact paths; no current checkpoint, historical WO0063/0064 evidence or previously frozen module edits.

## Authorized bounded code correction
The current verifier considers every original-base Git kind ``blob` a pin-worthy document. Git represents a symlink as ``120000 blob` and executable files as ``100755 blob`, so matching SHA alone is insufficient to ensure an admitted canonical source is a regular non-executable Git repository document.

1. Collect exact ``ls-tree -r -z` modes alongside existing original-base IDs without trusting workspace bytes.
2. Require ``100644` for **every pinned critical source at the trusted base**, including the newest anchor; fail closed on symlink or executable sources.
3. Require ``100644 blob` for each newly changed HEAD Context Lock **before** ``git show` / strict duplicate-key JSON parsing.
4. Preserve prior pure ``verify_lock` callers with an optional modes argument, and preserve Dependabot single-SHA pin exception, all latest-manifest inherited path checks, exact base/head SHA, tree/source identity and strict diff gating.
5. New six offline tests: real Git valid case; original-base pinned symlink/executable rejection; HEAD lock symlink/executable rejection; pure exact-mode negative.

## Verification gates and stop condition
Exact-head Governance including all 4673 tests, mode-specific negatives and positive, IRIS validator, GEF/HIVE pinned offline bridge; both exact-head Socket successes; final CodeRabbit external review with no uncorrected actionable findings, zero unresolved threads; guarded protected squash only after reviewing exact current head/base; independent exact-new-main Governance all 4673 and same-main Socket; then factual receipt and close #186. No admission of M10–M13 runtime or H01–H04 HIGH closure; actual owner #82/#110/#112/#128/#145/#146/#147/#155 remain OPEN, B_FUTURE_OWNER_RECEIPT direction-only, C01 unadopted, HIVE MCP offline. Historical own-CI/merge fields remain PENDING at authoring; authoritative GitHub postmerge receipt, not a recursive canonical checkpoint update, records the outcome.
