# IRIS GEF Execution Protocol

`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> AUDIT -> VERDICT -> CHECKPOINT DELTA -> MERGE -> NEXT`

Executor inspects exact state, reads admitted sources, implements only scope, runs tests, corrects introduced failures and provides base/head-bound evidence.
