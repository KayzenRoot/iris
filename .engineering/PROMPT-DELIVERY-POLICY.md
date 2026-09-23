# IRIS Prompt Delivery Policy

Status: `ACTIVE`
Version: `1.0`

## Purpose

Make executor-prompt delivery consistent across every current and future ChatGPT conversation operating on Hive IRIS.

## Mandatory rule

Any **complete prompt intended to be executed by Codex, Coder, Zcode or another external/local executor** MUST be delivered to the user as a **downloadable PDF artifact**.

The PDF is the primary and canonical user-facing delivery format for executor prompts.

## Prohibited primary delivery

Do NOT deliver the complete executor prompt primarily as:

- a copyable writing box;
- a Markdown code block;
- a long inline chat message intended for copy/paste;
- a plain-text attachment when a PDF can be produced.

A chat response may summarize what the prompt will do, but the executable prompt itself must be provided as a PDF download.

## Allowed inline content

Inline text is allowed for:

- short explanations;
- review findings;
- status updates;
- tiny command fragments;
- non-executor examples;
- brief correction deltas that are not themselves the complete executor prompt.

If the user asks for the actual full prompt, the final artifact must still be a PDF.

## Review / correction behavior

This policy does not change `.engineering/REVIEW-AUTOFIX-POLICY.md`.

- `CHAT_FIXABLE`: fix directly in chat/repository where safe; do not generate an unnecessary executor prompt.
- `EXECUTOR_REQUIRED`: produce the bounded executor/correction prompt as a downloadable PDF.
- A next-step implementation prompt is also a downloadable PDF whenever an executor is actually required.

## File naming

Prefer stable descriptive names such as:

- `IRIS-WO-0008-M04-MULTIMODAL-IR.pdf`
- `IRIS-WO-0008-CORRECTION-DELTA-01.pdf`

When a Work Order ID exists, include it in the PDF filename.

## Cross-chat enforcement

This policy is repository-canonical and applies to **every current and future ChatGPT conversation operating on Hive IRIS**.

A new chat must read this policy through `.engineering/SOURCE-HIERARCHY.md` / `AGENTS.md` before choosing how to deliver an executor prompt.

If a chat starts from repository context and this policy conflicts with remembered conversation preferences, this repository policy wins.

## Evidence rule

Do not claim that a PDF was created unless the artifact actually exists and a working download link can be provided.
