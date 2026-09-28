"""WO0061: original M04 OFFLINE parser deep JSON typed-refusal regressions."""
from __future__ import annotations

import json
import sys
import unittest
from unittest.mock import patch

from iris_multimodal_ir import (
    IRDocumentEnvelope, IRLimitError, IRLimits, IRSchemaError,
    MultimodalIRDocument, deserialize_envelope, serialize_envelope,
)
from tests.m04_support import DOCUMENT_ID, fixture_revision


class WO0061M04DeepJsonRefusalTests(unittest.TestCase):
    @staticmethod
    def _deep_array() -> str:
        return "[" * 2500 + "0" + "]" * 2500

    @staticmethod
    def _deep_object() -> str:
        return '{"a":' * 2500 + "0" + "}" * 2500

    def _assert_deep_json_typed(self, payload: str | bytes) -> None:
        # Use a controlled interpreter recursion limit so this real, unmocked
        # JSON fixture MUST fail during parsing rather than later M04 schema
        # checks. Restore any pre-existing process setting even on failure.
        previous_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(1000)
            with self.assertRaises(RecursionError):
                json.loads(payload)
            with self.assertRaises(IRSchemaError) as refusal:
                deserialize_envelope(payload)
            self.assertIsInstance(refusal.exception.__cause__, RecursionError)
        finally:
            sys.setrecursionlimit(previous_limit)

    def test_01_deep_json_array_text_typed(self):
        self._assert_deep_json_typed(self._deep_array())
        # Exercise the exact source-level exception branch deterministically.
        # Unlike real parser depth thresholds, this probe is interpreter-stable.
        with patch("iris_multimodal_ir.serialization.json.loads", side_effect=RecursionError("synthetic decoder depth")):
            with self.assertRaises(IRSchemaError) as failure:
                deserialize_envelope(b"{}")
        self.assertIsInstance(failure.exception.__cause__, RecursionError)

    def test_02_deep_json_array_bytes_typed(self):
        self._assert_deep_json_typed(self._deep_array().encode("utf-8"))

    def test_03_deep_json_object_text_typed(self):
        self._assert_deep_json_typed(self._deep_object())

    def test_04_deep_json_object_bytes_typed(self):
        self._assert_deep_json_typed(self._deep_object().encode("utf-8"))

    def test_05_original_invalid_utf8_still_typed(self):
        with self.assertRaises(IRSchemaError):
            deserialize_envelope(b"\xff")

    def test_06_original_malformed_json_still_typed(self):
        with self.assertRaises(IRSchemaError):
            deserialize_envelope(b'{"transport_version":')

    def test_07_original_duplicate_json_key_still_typed(self):
        with self.assertRaises(IRSchemaError):
            deserialize_envelope(b'{"a":1,"a":2}')

    def test_08_original_inline_byte_limit_still_typed(self):
        with self.assertRaises(IRLimitError):
            deserialize_envelope(b"{}", limits=IRLimits(max_inline_payload_bytes=1))

    def test_09_original_canonical_bytes_and_text_preserved(self):
        envelope = IRDocumentEnvelope(
            MultimodalIRDocument(DOCUMENT_ID, (fixture_revision(),))
        )
        original = serialize_envelope(envelope)
        from_bytes = deserialize_envelope(original)
        from_text = deserialize_envelope(original.decode("utf-8"))
        self.assertEqual(serialize_envelope(from_bytes), original)
        self.assertEqual(serialize_envelope(from_text), original)
