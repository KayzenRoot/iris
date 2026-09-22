# M04 S05 Research Baseline — Validation, Versioning and Round-Trip Guarantees

Status: `RESEARCH_COMPLETE_FOR_S05`
Date: 2026-09-22
Module: `M04 — Multimodal IR / Scene IR`
Issue: `#26`

## Purpose

Define how M04 IR can remain deterministic, migratable and semantically trustworthy across schema evolution and adapters.

## External prior art

### RFC 8785 JSON Canonicalization Scheme

RFC 8785 defines a deterministic JSON representation intended for repeatable hashing/signing by constraining input and sorting properties deterministically.

IRIS adopts the requirement for one deterministic canonical byte representation for each supported transport encoding. The frozen M04 contract does not require RFC 8785 itself as a dependency; it requires equivalent deterministic, finite-number-safe canonicalization semantics.

### OpenUSD schema versioning

OpenUSD's schema-versioning guidance treats preservation of downstream asset behavior as the primary reason to create a new schema version. It explicitly reasons about schema families and versions instead of assuming "latest" is behavior-compatible.

IRIS adopts:
- schema family + explicit version;
- behavior compatibility as the migration criterion;
- no automatic latest-version coercion;
- versioned migration/upgrade receipts.

### MLIR bytecode/dialect versioning

MLIR's bytecode is versioned, and dialects may carry their own versions and upgrade hooks.

IRIS adopts:
- transport format version distinct from schema/dialect version;
- per-family migration logic;
- explicit upgrade path with receipts;
- ability to read older supported versions without mutating historical artifacts in place.

## Research conclusions

1. transport version and semantic schema version are separate;
2. deterministic canonical bytes are required for fingerprints/signatures;
3. NaN/Infinity and ambiguous numeric encodings must not enter canonical hash material;
4. unknown mandatory schema/facet versions fail closed;
5. migrations create new revisions and immutable receipts;
6. "parse successfully" is weaker than "semantic round trip";
7. round-trip contracts must state which semantics must be identical, equivalent-with-tolerance or intentionally opaque;
8. adapter self-certification is insufficient; independent validation evidence is required;
9. derived caches/fingerprints can be rebuilt, canonical authored/lowered facts cannot be silently rewritten;
10. hostile graphs/resources require deterministic size/depth/fanout limits.

## S05 research gate

`PASS`

Proceed to freeze validation/versioning/round-trip architecture after Final Technology Review and Forward Compatibility Scan.
