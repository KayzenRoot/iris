# M02 S04 Research Baseline — Incremental Build, Cache & Context Reuse

Status: `RESEARCH_COMPLETE_FOR_S04`
Date: 2026-09-20

## Bazel remote cache
Bazel documents actions with explicit inputs/outputs, an Action Cache mapping action hashes to result metadata, and a CAS for output content. It notes that reproducible build outputs can safely be reused across machines, while untracked tools/environment can cause wrong cache sharing. IRIS adopts the separation of result lookup, CAS content and explicit correctness-relevant inputs, but adds generative-media reproducibility/trust classes.

Source: https://bazel.build/remote/caching

## Nix derivations / store
Nix derivations specify processes over precisely defined inputs to produce store objects, and the store holds immutable objects. Nix emphasizes determinism because transparent caching depends on it. IRIS adopts immutable materialization and explicit closure principles, while explicitly representing SEEDED, STOCHASTIC, HUMAN_DECISION and EXTERNAL_STATE nodes rather than falsely treating them as pure derivations.

Sources:
- https://nix.dev/manual/nix/2.35/store/derivation/index.html
- https://nix.dev/manual/nix/2.35/store/building.html

## Buck2 incremental actions
Buck2 documents incremental actions that reuse prior outputs, provided the previous result is available and the action can identify what changed and update the affected parts safely. This directly supports IRIS's Repair/Partial Reuse concept, with the additional requirement of a full/incremental truth oracle.

Source: https://buck2.build/docs/rule_authors/incremental_actions/

## DVC selective reproduction / run cache
DVC's pipeline model tracks dependencies and outputs and can rerun affected stages while reusing prior run results. IRIS takes the long-lived run-result reuse idea but requires dependency facets/slices finer than whole pipeline files for large multimodal projects.

Sources:
- https://dvc.org/
- https://dvc.org/blog/dvc-1-0-release/

## Transformer KV/prefix caches
Current Hugging Face Transformers documentation describes KV caches as reusing previously computed key/value attention state to avoid recomputing the full previous token context and includes prefilled prompt/prefix cache workflows. IRIS treats this strictly as runtime inference optimization bound to model/tokenizer/template/context compatibility, not as canonical production evidence.

Sources:
- https://huggingface.co/docs/transformers/en/kv_cache
- https://huggingface.co/docs/transformers/main/cache_explanation

## S04 conclusion

IRIS needs a broader build/cache model than software build systems because:
- many media operations are stochastic;
- quality/evidence may change without media bytes changing;
- rights/provenance/delivery can invalidate packaging but not generation;
- repair can be spatial/temporal/subasset-local;
- model/provider warm state and LLM KV cache are useful but ephemeral;
- exact material reuse and advisory/warm reuse have different trust;
- recurring virtual spokesperson/series production has unusually large reusable identity/context prefixes.

Therefore the Creative Build System should be based on causal correctness and reuse-class admission, not a single hash-cache abstraction.
