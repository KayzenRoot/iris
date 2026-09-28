"""WO0061: original M04 OFFLINE parser deep JSON typed-refusal regressions."""
from __future__ import annotations

import unittest

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

    def _assert_parser_recursion_typed(self, payload: str | bytes) -> None:
        with self.assertRaises(IRSchemaError) as failure:
            deserialize_envelope(payload)
        self.assertIsInstance(failure.exception.__cause__, RecursionError)

    def test_01_deep_json_array_text_typed(self):
        self._assert_parser_recursion_typed(self._deep_array())

    def test_02_deep_json_array_bytes_typed(self):
        self._assert_parser_recursion_typed(self._deep_array().encode("utf-8"))

    def test_03_deep_json_object_text_typed(self):
        self._assert_parser_recursion_typed(self._deep_object())

    def test_04_deep_json_object_bytes_typed(self):
        self._assert_parser_recursion_typed(self._deep_object().encode("utf-8"))

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
