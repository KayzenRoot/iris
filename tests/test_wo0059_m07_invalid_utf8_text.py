"""WO0059: original frozen M07 OFFLINE text ingress cannot leak UnicodeEncodeError."""
from __future__ import annotations

import unittest

from iris_hardware_genome import (
    HardwareGenomeValidationError,
    canonical_deserialize,
    canonical_serialize,
)
from m07_support import genome


class TestWO0059M07InvalidUtf8Text(unittest.TestCase):
    def test_unpaired_high_surrogate_text_is_typed_refusal(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize("\ud800")

    def test_unpaired_low_surrogate_text_is_typed_refusal(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize("\udfff")

    def test_embedded_high_surrogate_json_text_is_typed_refusal(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize('{"format":"iris-m07-json-v1","record":"\ud800"}')

    def test_embedded_low_surrogate_json_text_is_typed_refusal(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize('{"format":"iris-m07-json-v1","record":"\udc00"}')

    def test_original_canonical_bytes_and_text_remain_equal(self):
        record = genome()
        original = canonical_serialize(record)
        self.assertEqual(canonical_deserialize(original), record)
        self.assertEqual(canonical_deserialize(original.decode("utf-8")), record)
        self.assertEqual(canonical_serialize(canonical_deserialize(original)), original)

    def test_invalid_utf8_bytes_keep_original_typed_refusal(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize(b"\xff\xfe")

    def test_duplicate_root_json_keys_keep_original_typed_refusal(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize('{"format":"iris-m07-json-v1","format":"iris-m07-json-v1","record":{}}')

    def test_invalid_transport_type_keep_original_typed_refusal(self):
        with self.assertRaises(HardwareGenomeValidationError):
            canonical_deserialize(bytearray(canonical_serialize(genome())))


if __name__ == "__main__":
    unittest.main()
