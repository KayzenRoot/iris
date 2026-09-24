"""Frozen M09 schema and contract version boundaries."""

from __future__ import annotations

from .versioning import SchemaDescriptor

__all__ = ["M09_CONTRACT_VERSION", "M09_SCHEMA", "SUPPORTED_SCHEMA_IDS", "require_supported_schema"]

M09_CONTRACT_VERSION = "m09-contract-v1.0"
M09_SCHEMA = SchemaDescriptor("iris-resource-twin", 1, 0, 0)
SUPPORTED_SCHEMA_IDS = (M09_SCHEMA.schema_id,)


def require_supported_schema(schema: SchemaDescriptor) -> SchemaDescriptor:
    if type(schema) is not SchemaDescriptor or schema.schema_id not in SUPPORTED_SCHEMA_IDS:
        raise ValueError("schema identity is unsupported by M09")
    return schema
