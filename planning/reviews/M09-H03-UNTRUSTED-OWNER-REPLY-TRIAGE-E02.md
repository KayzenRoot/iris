# H03 E02: offline untrusted owner reply triage harness

**Purpose:** A real artifact for the next owner-response workflow, not another owner decision. Users can locally format-check an **UNTRUSTED DRAFT** reply for [M12 #128](https://github.com/KayzenRoot/iris/issues/128), [M54 #145](https://github.com/KayzenRoot/iris/issues/145), [M58 #146](https://github.com/KayzenRoot/iris/issues/146) or [M60 #147](https://github.com/KayzenRoot/iris/issues/147). The tool performs **no network request, GitHub comment fetch, identity verification, external security/OS review, contract adoption, runtime action or project status mutation**. Nothing from a draft can turn an owner issue into a genuine approval.

**Pinned historical starting point:** main `47a1a41096ebb3153e7e5918edeedb58a0706154`, exact-main [Governance #526](https://github.com/KayzenRoot/iris/actions/runs/36343355054) PASS **4260/4260**, protected [WO0038 PR #148](https://github.com/KayzenRoot/iris/pull/148), original source-locked four-owner packet and E01 route registry unchanged. Responsible user [selected B_FUTURE_OWNER_RECEIPT](https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032) for **future documentary M09→M11 direction only**, not M09 C01 adoption, M12 placement, M54 permission, M58 publication or M60 OS rights.

## 1. Source-locked question scope

| Owner | Existing real review issue | Exact original assigned questions | Source status |
|---|---|---:|---|
| M12 | [#128](https://github.com/KayzenRoot/iris/issues/128) | 72 | Proposed candidate, not frozen |
| M54 | [#145](https://github.com/KayzenRoot/iris/issues/145) | 39 | Master index only, no approved contract |
| M58 | [#146](https://github.com/KayzenRoot/iris/issues/146) | 9 | Master index only, no approved contract |
| M60 | [#147](https://github.com/KayzenRoot/iris/issues/147) | 27 | Master index only, no approved contract |

These **147 overlapping assignments / 91 unique original source questions** derive from E01 and WO0037, not free-form labels chosen by the draft author. The remaining original M12 questions outside these four queues are **not silently dropped**: all 110 original questions remain OPEN/UNRATED in their original register. Shared questions never count as approved by another owner simply because one draft lists them.

## 2. How to use the tool without granting authority

Create a local JSON file, for example `proposed-m54-reply.json`, using the **synthetic, not approved** illustrative shape below. Replace the placeholder values only with actual later reviewer submissions. A Git-looking SHA or issue comment is a *claim* that still needs independent verification.

```json
{
  "schemaVersion": "iris-h03-untrusted-reply-draft-v0",
  "module": "M54",
  "issue": 145,
  "sourceCommit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "sourcePath": "planning/contracts/M54-DRAFT-NOT-APPROVED.md",
  "selfClaimedOwner": "SYNTHETIC_UNVERIFIED_OWNER",
  "selfClaimedReviewUrl": "https://github.com/KayzenRoot/iris/pull/999",
  "scopeAndExclusions": {
    "scope": "Proposed principal and action constraints for discussion only",
    "exclusions": "No process launch, other owner approval, public API or OS permission"
  },
  "questionDispositions": [
    {
      "questionId": "M12-S01-U02",
      "decision": "DEFER",
      "rationale": "Requires an actual independent M54 and M60 identity proof"
    }
  ]
}
```

Run from the repo root: `python -m scripts.triage_m09_h03_untrusted_owner_reply --candidate proposed-m54-reply.json`. The CLI checks the existing immutable original owner registers and exact Git blob source fingerprints before reading a new local draft. It prints a JSON outcome; malformed or unscoped drafts fail closed with exit code 2. A draft missing required fields reports `MISSING_FIELDS_NOT_REVIEWABLE`, a syntactically complete subset `PARTIAL_DRAFT_FORMAT_ONLY`, and a syntactically complete exact full question queue `COMPLETE_DRAFT_FORMAT_ONLY`. **None of those statuses means accepted/approved/verified.**

## 3. What this harness actually enforces

- Only four source-known module/issue pairs can be submitted. Exact source-known original question IDs, disposition enum `PROPOSED_ANSWER`, `DEFER`, `UNSUPPORTED`, unique per-owner IDs, nontrivial rationale, proposed scope **and** exclusions must be present. It rejects altered foreign-module question IDs, duplicate or excess rows, unexpected fields like `approved` or `runtimeAdmitted`, forged `APPROVED`/`EXECUTED_PASS` dispositions, Git URL lookalikes and contract paths outside the owner namespace.
- It canonically reports remaining original per-module question IDs plus other overlapping owners who would need **separate** approval. An M54 response to `M12-S01-U02`, for example, visibly reports M60 as still pending. Even four syntactically complete drafts in separate files provide zero authenticated signatures or execution admission.
- It strictly treats all SHA strings, claimed source paths, claimed GitHub review URLs and self-identified authors as *unverified text*. Syntactic validation performs **no actual GitHub source fetch or reviewer authentication**, checks no credentials, reads no real OS process information, and does not choose issuer crypto, transport, TTL, OS or public API.
- It reuses the older independently governed static `verify_m09_h03_owner_routes.py`, which in turn validates original WO0037 owner/source routing and original M12 OPEN/UNRATED/NOT_EXECUTED status. Those source integrity checks are **not** a future contract-owner audit or GitHub live status watcher.

## 4. Negative/false-authority harness coverage

New **30 deterministic local synthetic and tampered-draft unit tests**, distinct from original 12 HX/6 LV/10 C08/8 PO-C02/80 M12 future negatives and 12 new H03-N design cases; *all original future tests and H03-N scenarios remain SPECIFIED_NOT_EXECUTED*. Tests cover four exact module/issue queues, synthetic partial/full/missing statuses, overlapping-co-owner notices, duplicate/foreign question IDs, fake approved/runtime fields, wrong source path, path traversal, spoofed GitHub URL, empty scope/exclusions, false owner signature, duplicate JSON keys, and permanent output no-authority guarantees. No process/GPU/OS/network/cloud integration scenarios run.

## 5. Future real signoff is a different, owner-qualified process

After receiving an actual claim, independently inspect the **claimed GitHub source commit/path** on the right actual owner's authorized branch, verify the claimed author's identity/rights and independent security/platform review as needed, compare exact owner question dispositions to real M09/M11/M12/M54/M58/M60 contract scopes, verify actual tests (not merely specified designs), and preserve any shared questions pending separate co-owner proof. That future work requires a separate source-locked Work Order and independently qualified evidence. An offline `COMPLETE_DRAFT_FORMAT_ONLY` result may help triage a review, but by design cannot change frozen contracts or open issue gates.

**HARD STOP:** H01 actual M11 authenticated liveness/ACK, H02 M09 atomic all-member joint snapshot+lease and at-use expiry/revocation, H03 actual M12/M54/M58/M60 owner contracts, and H04 exact M02/M06/M09/M11 work/attempt/action/epoch binding all remain **OPEN HIGH_FOR_FUTURE_FREEZE**. M09 v1.0 FROZEN unchanged; proposed C01 UNADOPTED_NOT_FROZEN. M11 v0.2 NOT_FROZEN 86 original questions OPEN, M12 v0.1 PROPOSED_NOT_FROZEN 110 original questions OPEN/80 future cases NOT_EXECUTED. M54/M58/M60 index-only with **no approved source contract**. M10/M11/M12 runtime NOT_ADMITTED, no actual OS/GPU/network/cloud/process actions, public M58 API, credential trust, placement/grant or false reviewer approval. Keep #82/#110/#112/#128/#145/#146/#147 OPEN.
