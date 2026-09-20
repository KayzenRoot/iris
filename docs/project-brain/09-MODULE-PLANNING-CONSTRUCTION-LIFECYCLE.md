# IRIS — Module Planning & Construction Lifecycle

Status: `ACTIVE`
Version: `1.0`

## Official cycle

For every M00–M60 module:

1. **Slow Planning** — discuss every canonical session deeply.
2. **Technology Discovery** — evaluate existing technology, internal reuse and proprietary candidates.
3. **Final Technology Review** — ACCEPT / SUPERSEDE / REJECT candidates with rationale.
4. **Forward Compatibility Scan** — inspect known future module contracts/dependencies without deep-planning those modules.
5. **Module Contract Freeze** — freeze interfaces, invariants, acceptance criteria and dependency assumptions needed for implementation.
6. **Executor Work Order** — compile bounded implementation instructions and context lock.
7. **Executor PDF** — produce the execution prompt as a downloadable PDF for the user's selected coding executor.
8. **Implementation** — executor inspects repo, changes only approved scope and provides evidence.
9. **Tests / Benchmarks / Evidence** — risk-appropriate verification.
10. **Independent Review** — APPROVED / CORRECTION REQUIRED / BLOCKED.
11. **Correction Loop** — same WO/PR where safe until evidence satisfies acceptance.
12. **Checkpoint Promotion** — merge only approved evidence and update canonical checkpoint.
13. **Next Module** — only after current module's implementation state is explicit.

## IRIS-ARCH-001 — Future Contract Shield

Future modules expose only minimum known contracts before their deep planning. The active module checks these contracts before implementation.

The shield contains:
- expected asset/input/output families;
- known interface consumers/providers;
- invariants that must survive;
- extension points;
- compatibility hazards;
- assumptions explicitly marked as revisitable.

It does NOT prematurely design future module internals.

## IRIS-ARCH-002 — Evolution Ports

Major integrations use versioned interfaces/providers instead of embedding vendor/runtime assumptions in the core.

Initial port families include:
- QualityJudge
- AssetValidator
- GeneratorProvider
- DCCProvider
- RendererProvider
- ModelProvider
- StorageProvider
- MemoryProvider
- OrchestrationProvider
- ExportProvider

Ports must expose capabilities and limitations. Unsupported behavior fails explicitly rather than silently degrading.

## Executor selection

The Work Order is executor-neutral. Codex, Coder, Zcode or another qualified coding executor may perform it. The repository contract, tests and evidence define correctness, not the executor brand.

## PDF rule

When a module reaches the implementation gate, ChatGPT produces the executor prompt in PDF. The PDF is executable instruction, includes STOP CONDITION, and is reviewed against the frozen module contract before delivery.

## Anti-pattern

Do not:
- implement from chat memory;
- deep-plan all future modules before evidence exists;
- implement a module without a forward compatibility scan;
- make future modules depend on undocumented implementation details;
- silently alter a frozen contract during implementation.


## Review Auto-Fix Rule

Independent review follows `.engineering/REVIEW-AUTOFIX-POLICY.md`.

A reviewer classifies every correction as `CHAT_FIXABLE` or `EXECUTOR_REQUIRED`. Safe bounded repository fixes that can be applied and objectively validated by chat are corrected directly in the same branch/PR. Executor correction PDFs are reserved for findings that require unavailable local/runtime capabilities or cannot be safely proven from repository/CI evidence.

After a direct fix, the reviewer re-audits before issuing APPROVED. HIGH/CRITICAL findings never become non-blocking merely because the fix was performed by chat.
