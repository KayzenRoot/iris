"""WO0057: frozen M05 offline JSON reader fails closed on nonencodable string input."""
from __future__ import annotations
import json
import unittest
from iris_asset_dna.errors import DNAValidationError
from iris_asset_dna.serialization import deserialize_record, serialize_record
from m05_support import revision

class TestM05InvalidUtf8Text(unittest.TestCase):
    def test_01_high_unpaired_surrogate_typed_validation(self):
        with self.assertRaisesRegex(DNAValidationError, "valid UTF-8 text"):
            deserialize_record(chr(0xD800))

    def test_02_low_unpaired_surrogate_typed_validation(self):
        with self.assertRaisesRegex(DNAValidationError, "valid UTF-8 text"):
            deserialize_record(chr(0xDFFF))

    def test_03_existing_invalid_utf8_bytes_still_typed(self):
        with self.assertRaisesRegex(DNAValidationError, "valid UTF-8"):
            deserialize_record(b"\xff")

    def test_04_valid_canonical_bytes_and_text_roundtrip_unchanged(self):
        original = revision("dna-wo0057-offline")
        encoded = serialize_record(original)
        for payload in (encoded, encoded.decode("utf-8"), bytearray(encoded), memoryview(encoded)):
            with self.subTest(kind=type(payload).__name__):
                restored = deserialize_record(payload, expected_type=type(original))
                self.assertEqual(restored, original)
                self.assertEqual(serialize_record(restored), encoded)

    def test_05_existing_duplicate_json_key_rejection_unchanged(self):
        encoded = serialize_record(revision("dna-wo0057-duplicate")).decode("utf-8")
        obj = json.loads(encoded)
        key = next(iter(obj))
        ambiguous = "{" + json.dumps(key) + ":" + json.dumps(obj[key]) + "," + encoded[1:]
        self.assertEqual(json.loads(ambiguous), obj)
        with self.assertRaisesRegex(DNAValidationError, "duplicate JSON object key"):
            deserialize_record(ambiguous)

if __name__ == "__main__":
    unittest.main()
