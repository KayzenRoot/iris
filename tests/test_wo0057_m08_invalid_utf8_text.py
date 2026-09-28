"""WO0057: frozen M08 offline document reader fails closed on nonencodable text."""
from __future__ import annotations
import json
import unittest
from iris_microbenchmark.errors import MicrobenchmarkSecurityError, MicrobenchmarkValidationError
from iris_microbenchmark.schema import SchemaDescriptor, SchemaVersion
from iris_microbenchmark.serialization import create_document, decode_document, encode_document

class TestM08InvalidUtf8Text(unittest.TestCase):
    @staticmethod
    def original_document():
        schema = SchemaDescriptor("iris-m08-wo0057-offline", SchemaVersion(1, 0, 0),
                                  ("synthetic",), ("compact_projection",), "canonical-json-v1")
        return create_document(schema, schema, created_at_ms=11)

    def test_01_high_unpaired_surrogate_typed_validation(self):
        with self.assertRaisesRegex(MicrobenchmarkValidationError, "valid UTF-8 text"):
            decode_document(chr(0xD800))

    def test_02_low_unpaired_surrogate_typed_validation(self):
        with self.assertRaisesRegex(MicrobenchmarkValidationError, "valid UTF-8 text"):
            decode_document(chr(0xDFFF))

    def test_03_existing_invalid_utf8_bytes_still_typed(self):
        with self.assertRaisesRegex(MicrobenchmarkValidationError, "bounded UTF-8 JSON"):
            decode_document(b"\xff")

    def test_04_valid_canonical_text_and_bytes_roundtrip_unchanged(self):
        source = self.original_document()
        encoded = encode_document(source)
        for payload in (encoded, encoded.encode("utf-8")):
            with self.subTest(kind=type(payload).__name__):
                restored = decode_document(payload)
                self.assertEqual(restored, source)
                self.assertEqual(encode_document(restored), encoded)

    def test_05_existing_duplicate_json_key_rejection_unchanged(self):
        encoded = encode_document(self.original_document())
        obj = json.loads(encoded)
        key = next(iter(obj))
        ambiguous = "{" + json.dumps(key) + ":" + json.dumps(obj[key]) + "," + encoded[1:]
        self.assertEqual(json.loads(ambiguous), obj)
        with self.assertRaisesRegex(MicrobenchmarkSecurityError, "repeats JSON key"):
            decode_document(ambiguous)

if __name__ == "__main__":
    unittest.main()
