"""Resource bounds the M02 kernel enforces on structures it cannot measure otherwise.

The frozen M02 contract requires bounded collection sizes wherever untrusted
input could create resource abuse, but the module spec names no numbers. These are
therefore an explicit executor decision, chosen the same way M01 chose its limits:
generous enough that no realistic production of the five required domain profiles
touches them, tight enough that a hostile payload is refused at construction
instead of exhausting memory during analysis. They bound abuse, not capability;
raising one is a contract amendment, not a tuning knob.
"""

from __future__ import annotations

__all__ = [
    "MAX_METADATA_KEYS",
    "MAX_ALIASES",
    "MAX_LOCATOR_CHARS",
    "MAX_RECEIPT_EVIDENCE",
    "MAX_NODES",
    "MAX_EDGES",
    "MAX_PORTS",
    "MAX_NODE_METADATA_KEYS",
    "MAX_FACETS",
    "MAX_SLICE_VALUES",
    "MAX_SCHEMA_REFS",
    "MAX_EXTERNAL_NODES",
    "MAX_GRAPH_DEPTH",
    "MAX_IMPACT_NODES",
    "MAX_EXPLAIN_STEPS",
    "MAX_SNAPSHOT_NODES",
    "MAX_CLOSURE_REFS",
    "MAX_VARIANT_SETS",
    "MAX_VARIANT_OPTIONS",
    "MAX_VARIANT_SELECTIONS",
    "MAX_DIFF_ENTRIES",
    "MAX_CONFLICTS",
    "MAX_MERGE_INPUT_NODES",
    "MAX_PIN_REASONS",
    "MAX_DIRTY_NODES",
    "MAX_REPAIR_TARGETS",
    "MAX_BUILD_PLAN_STEPS",
    "MAX_SLICES_PER_NODE",
    "MAX_FINGERPRINT_INPUTS",
    "MAX_CONTEXT_SOURCES",
    "MAX_TRANSITIONS",
    "MAX_EVENTS",
    "MAX_GATES",
    "MAX_GATE_EVIDENCE",
    "MAX_BLOCKERS",
    "MAX_BUNDLE_ITEMS",
    "MAX_RELEASE_STEPS",
    "MAX_DESTINATIONS",
    "MAX_SUPERSESSION_CHAIN",
    "MAX_ARCHIVE_REFS",
    "MAX_REVIVAL_OBLIGATIONS",
    "MAX_COMMAND_HISTORY",
    "MAX_PORT_CAPABILITIES",
    "MAX_PORT_BOUNDARIES",
    "MAX_COMPILED_STEPS",
    "MAX_OBSERVED_DEPENDENCIES",
    "MAX_STORED_RECORDS",
]

# Identity and history
MAX_METADATA_KEYS = 32
MAX_ALIASES = 64
MAX_LOCATOR_CHARS = 1024
MAX_RECEIPT_EVIDENCE = 64
MAX_COMMAND_HISTORY = 4096

# Production graph
MAX_NODES = 4096
MAX_EDGES = 16384
MAX_PORTS = 64
MAX_NODE_METADATA_KEYS = 32
MAX_FACETS = 8
MAX_SLICE_VALUES = 64
MAX_SCHEMA_REFS = 32
MAX_EXTERNAL_NODES = 1024
MAX_GRAPH_DEPTH = 512
MAX_IMPACT_NODES = 4096
MAX_EXPLAIN_STEPS = 256
MAX_FINGERPRINT_INPUTS = 512

# Branches, variants and snapshots
MAX_SNAPSHOT_NODES = 4096
MAX_CLOSURE_REFS = 4096
MAX_VARIANT_SETS = 128
MAX_VARIANT_OPTIONS = 128
MAX_VARIANT_SELECTIONS = 128
MAX_DIFF_ENTRIES = 8192
MAX_DIFF_SUBJECT_CHARS = 1024
MAX_CONFLICTS = 512
MAX_MERGE_INPUT_NODES = 4096
MAX_PIN_REASONS = 32

# Incremental build
MAX_DIRTY_NODES = 4096
MAX_REPAIR_TARGETS = 512
MAX_BUILD_PLAN_STEPS = 4096
MAX_CONTEXT_SOURCES = 128
MAX_SLICES_PER_NODE = 64

# Lifecycle, promotion and archive
MAX_TRANSITIONS = 256
MAX_EVENTS = 65536
MAX_GATES = 64
MAX_GATE_EVIDENCE = 64
MAX_BLOCKERS = 64
MAX_BUNDLE_ITEMS = 128
MAX_RELEASE_STEPS = 64
MAX_DESTINATIONS = 64
MAX_SUPERSESSION_CHAIN = 1024
MAX_ARCHIVE_REFS = 2048
MAX_REVIVAL_OBLIGATIONS = 64

# Extension ports and reference stores
MAX_PORT_CAPABILITIES = 32
MAX_PORT_BOUNDARIES = 16
MAX_COMPILED_STEPS = 4096
MAX_OBSERVED_DEPENDENCIES = 1024
MAX_STORED_RECORDS = 65536
