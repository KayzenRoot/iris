# IRIS Review Auto-Fix Policy

Status: `ACTIVE`
Version: `1.1`

## Rule

Every independent code/repository review MUST classify each finding before producing a corrective executor prompt.

### CHAT_FIXABLE

A finding is `CHAT_FIXABLE` when ChatGPT has sufficient repository access and objective evidence to make the correction safely in the current review flow, including when:

- the change is bounded and local to the reviewed repository/branch/PR;
- GitHub repository tools can apply it without workstation-only access;
- the correction does not require unavailable secrets, local DCC state, GPU execution, external interactive UI or destructive operations;
- tests, static checks, exact-head CI or other deterministic evidence can validate it;
- the fix does not silently expand the frozen Work Order or alter an approved contract.

For `CHAT_FIXABLE` findings, ChatGPT MUST:
1. correct the finding directly in the same branch/PR when safe;
2. add/update regression tests or governance evidence when applicable;
3. run/observe the relevant validation and exact-head CI;
4. continue the review from the corrected state;
5. avoid sending a Codex/Coder/Zcode corrective prompt merely for work already safely completed by chat.

### EXECUTOR_REQUIRED

A finding is `EXECUTOR_REQUIRED` when safe correction materially depends on capabilities unavailable to the chat review environment, such as:

- workstation/local filesystem state not represented in Git;
- Blender, ComfyUI, Maya, GPU, driver or hardware execution;
- local services, credentials or secrets unavailable to the reviewer;
- interactive application state;
- generated/binary/media artifacts that cannot be produced or validated here;
- a broad implementation/refactor whose correctness cannot be sufficiently proved using repository/CI evidence available to the reviewer.

For `EXECUTOR_REQUIRED` findings, ChatGPT MUST compile a bounded Correction Delta and provide the executor prompt as a downloadable PDF, preserving the same Work Order/PR where safe.

## Review verdict behavior

- A local correction does not automatically mean APPROVED. Re-audit after the fix.
- HIGH/CRITICAL findings remain merge-blocking until objective evidence passes.
- Never weaken a frozen contract to make tests pass.
- Never claim a local fix succeeded without evidence.
- Preserve STOP CONDITIONs.
- Prefer the smallest safe repair surface.

## Post-review continuation

After an APPROVED review:
- perform repository-side checkpoint/evidence cleanup directly when it is `CHAT_FIXABLE`;
- merge through the governed PR flow when allowed and evidence passes;
- proceed to the next planning increment;
- generate a new executor PDF only when the next implementation gate is actually reached.

This policy is repository-canonical and applies to every ChatGPT conversation operating on Hive IRIS.


## Mandatory cross-chat enforcement

This policy is mandatory for every current and future ChatGPT conversation operating on Hive IRIS.

Before any Codex/Coder/Zcode correction prompt is produced, the reviewer MUST first classify each finding as `CHAT_FIXABLE` or `EXECUTOR_REQUIRED`.

Producing an executor correction for a `CHAT_FIXABLE` finding without first attempting the safe direct repository repair and objective validation is a governance violation.

A new IRIS chat performing review MUST read this policy through `.engineering/SOURCE-HIERARCHY.md` before deciding whether to escalate a finding.

Only `EXECUTOR_REQUIRED` findings may be escalated to a corrective executor PDF. When all findings are `CHAT_FIXABLE`, the review stays in chat through repair, CI/evidence, re-audit and final verdict.
