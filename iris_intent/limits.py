"""Resource bounds the M03 kernel enforces on structures it cannot measure otherwise.

The frozen M03 contract requires bounded collections wherever untrusted input could create
resource abuse, but names no numbers. These are therefore an explicit executor decision,
chosen the way M01 and M02 chose theirs: generous enough that no realistic brief in any of
the six required domains touches them, tight enough that a hostile payload is refused at
construction instead of exhausting memory mid-analysis. They bound abuse, not capability —
raising one is a contract amendment, never a tuning knob at a call site.

The asymmetry is intentional. Counts an *author* controls (statements in a brief,
constraints in a bundle) are roomy; counts an *untrusted source* controls (retrieved text,
extension metadata, proposed overrides, provider observation refs) are comparatively tight,
because those are the numbers an adversary picks.
"""

from __future__ import annotations

__all__ = [
    "MAX_STATEMENTS_PER_MODEL",
    "MAX_QUALITY_OBLIGATIONS",
    "MAX_AMBIGUITIES",
    "MAX_OPEN_QUESTIONS",
    "MAX_FREEDOM_ZONES",
    "MAX_CONSTRAINTS_PER_BUNDLE",
    "MAX_ANCESTORS",
    "MAX_ALIASES",
    "MAX_PROVENANCE_REFS",
    "MAX_RATIONALE_CHARS",
    "MAX_TEXT_CHARS",
    "MAX_LABEL_CHARS",
    "MAX_PATHS_PER_SLICE",
    "MAX_SLICE_STATEMENTS",
    "MAX_SEMANTIC_FINGERPRINT_INPUTS",
    "MAX_DELTA_ENTRIES",
    "MAX_EQUIVALENCE_RULES",
    "MAX_TOLERANCE_DIMENSIONS",
    "MAX_PREDICATE_ARGUMENTS",
    "MAX_ANTI_REFERENCE_FACETS",
    "MAX_PROTECTED_ZONES",
    "MAX_SCOPE_PATHS",
    "MAX_CONDITIONS",
    "MAX_ADMISSION_CLAIMS",
    "MAX_REGISTRY_EXTENSIONS",
    "MAX_METADATA_KEYS",
    "MAX_METADATA_VALUE_CHARS",
    "MAX_EXPLANATION_NODES",
    "MAX_EXPLANATION_EDGES",
    "MAX_EXPLANATION_DEPTH",
    "MAX_PROJECTION_NODES",
    "MAX_CONTRACTS_PER_SET",
    "MAX_DIMENSIONS_PER_SPEC",
    "MAX_OBLIGATION_TRACES",
    "MAX_OPERATIONS_PER_BUNDLE",
    "MAX_CAPABILITY_DEMANDS",
    "MAX_MUTATION_TARGETS",
    "MAX_OBSERVATION_REFS",
    "MAX_CONFLICTS",
    "MAX_CONFLICT_PARTIES",
    "MAX_AUTHORITY_NODES",
    "MAX_AUTHORITY_EDGES",
    "MAX_OVERRIDES",
    "MAX_OVERRIDE_DEBT",
    "MAX_MERGE_COMPONENTS",
    "MAX_READINESS_FINDINGS",
    "MAX_STORED_RECORDS",
    "MAX_NESTING_DEPTH",
]

# Intent and brief scale
MAX_STATEMENTS_PER_MODEL = 512
MAX_QUALITY_OBLIGATIONS = 256
MAX_AMBIGUITIES = 256
MAX_OPEN_QUESTIONS = 128
MAX_FREEDOM_ZONES = 64
MAX_CONSTRAINTS_PER_BUNDLE = 512
MAX_ANCESTORS = 1024
MAX_ALIASES = 64
MAX_PROVENANCE_REFS = 64
MAX_RATIONALE_CHARS = 4096
MAX_TEXT_CHARS = 8192
MAX_LABEL_CHARS = 160

# Slices, fingerprints and reuse
MAX_PATHS_PER_SLICE = 256
MAX_SLICE_STATEMENTS = 512
MAX_SEMANTIC_FINGERPRINT_INPUTS = 1024
MAX_DELTA_ENTRIES = 4096
MAX_EQUIVALENCE_RULES = 64
MAX_NESTING_DEPTH = 32

# Constraints
MAX_TOLERANCE_DIMENSIONS = 16
MAX_PREDICATE_ARGUMENTS = 16
MAX_ANTI_REFERENCE_FACETS = 32
MAX_PROTECTED_ZONES = 128
MAX_SCOPE_PATHS = 64
MAX_CONDITIONS = 32
MAX_ADMISSION_CLAIMS = 64
MAX_REGISTRY_EXTENSIONS = 256
MAX_METADATA_KEYS = 32
MAX_METADATA_VALUE_CHARS = 2048

# Explainability
MAX_EXPLANATION_NODES = 4096
MAX_EXPLANATION_EDGES = 16384
MAX_EXPLANATION_DEPTH = 512
MAX_PROJECTION_NODES = 1024

# Fidelity compilation
MAX_CONTRACTS_PER_SET = 64
MAX_DIMENSIONS_PER_SPEC = 128
MAX_OBLIGATION_TRACES = 1024

# Execution intent
MAX_OPERATIONS_PER_BUNDLE = 256
MAX_CAPABILITY_DEMANDS = 128
MAX_MUTATION_TARGETS = 256
MAX_OBSERVATION_REFS = 64

# Conflicts, overrides, merge and readiness
MAX_CONFLICTS = 512
MAX_CONFLICT_PARTIES = 16
MAX_AUTHORITY_NODES = 1024
MAX_AUTHORITY_EDGES = 4096
MAX_OVERRIDES = 256
MAX_OVERRIDE_DEBT = 256
MAX_MERGE_COMPONENTS = 512
MAX_READINESS_FINDINGS = 512

# Reference stores (test-support persistence; production persistence is M06/M55)
MAX_STORED_RECORDS = 65536
