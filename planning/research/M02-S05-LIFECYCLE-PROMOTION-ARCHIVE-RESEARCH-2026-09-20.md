# M02 S05 Research Baseline — State, Promotion, Release & Archive

Status: `RESEARCH_COMPLETE_FOR_S05`
Date: 2026-09-20

## W3C SCXML
SCXML 1.0 is a W3C Recommendation defining generic state-machine semantics including transitions with events/conditions, final states, history states and parallel state regions. IRIS uses it as a semantic reference for orthogonal production-state regions and legal state configurations, not as a requirement to adopt XML or an SCXML interpreter.

Source: https://www.w3.org/TR/scxml/

## Temporal
Temporal documents durable execution where workflow history persists and execution can resume after process, network or infrastructure failures. IRIS adopts the durable-history/replay principle for attempts and transition receipts while keeping IRIS production records canonical.

Source: https://docs.temporal.io/

## Dagster
Dagster models persistent assets, explicit dependencies, lineage and materializations. IRIS uses this as a supporting precedent for separating the fact that an asset/materialization exists from the orchestration run that produced it.

Source: https://docs.dagster.io/

## OpenUSD
OpenUSD is designed for collaboratively constructing large animated/VFX scenes and provides non-destructive layered composition, references and variants. It demonstrates production-scale composition for film/VFX, but IRIS retains separate lifecycle/promotion/release governance above scene composition.

Sources:
- https://openusd.org/dev/index.html
- https://openusd.org/dev/glossary.html

## S05 conclusion

IRIS production lifecycle must:
- separate lifecycle phase from active execution and public release state;
- make promotion explicit and evidence-gated;
- preserve failed/cancelled attempt history without terminally corrupting production;
- make external publication a reconciliation-aware transaction;
- distinguish acceptance, release, withdrawal, supersession and archive;
- archive evidence/reproducibility contracts rather than merely files;
- reconstruct current state from immutable receipts;
- apply stricter release gates to persistent corporate avatars and other high-value public identities.
