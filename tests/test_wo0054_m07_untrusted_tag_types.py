"""WO0054: malformed M07 closed JSON tags must fail with typed errors."""
from __future__ import annotations

import json
import unittest

from iris_hardware_genome import (
    HardwareGenomeAdmissionError,
    HardwareGenomeIntegrityError,
    HardwareGenomeValidationError,
    canonical_deserialize,
    canonical_serialize,
)
from iris_hardware_genome.versions import TRANSPORT_VERSION
from m07_support import genome


class M07UntrustedTagTypeTests(unittest.TestCase):
    @staticmethod
    def record_input(tag):
        return json.dumps({
            "format": TRANSPORT_VERSION,
            "record": {"$record": tag, "fields": {}},
        })

    @staticmethod
    def enum_input(tag):
        # Mutate only the closed type tag in a canonical, existing M07 record.
        envelope = json.loads(canonical_serialize(genome()))

        def replace_first_enum(node):
            if isinstance(node, dict):
                if set(node) == {"$enum", "value"}:
                    node["$enum"] = tag
                    return True
                return any(replace_first_enum(v) for v in node.values())
            if isinstance(node, list):
                return any(replace_first_enum(v) for v in node)
            return False

        if not replace_first_enum(envelope):
            raise AssertionError("canonical M07 fixture lacks enum")
        return json.dumps(envelope)

    def test_01_list_record_tag_is_typed_validation(self):
        with self.assertRaisesRegex(HardwareGenomeValidationError,
                                    "record tag must be a string"):
            canonical_deserialize(self.record_input([]))

    def test_02_mapping_record_tag_is_typed_validation(self):
        with self.assertRaisesRegex(HardwareGenomeValidationError,
                                    "record tag must be a string"):
            canonical_deserialize(self.record_input({"fake": "record"}))

    def test_03_scalar_nonstring_record_tags_fail_closed(self):
        for tag in (None, False, True, 17, 1.25):
            with self.subTest(tag=repr(tag)):
                with self.assertRaises(HardwareGenomeValidationError):
                    canonical_deserialize(self.record_input(tag).encode("utf-8"))

    def test_04_list_enum_tag_is_typed_validation(self):
        with self.assertRaisesRegex(HardwareGenomeValidationError,
                                    "enum tag must be a string"):
            canonical_deserialize(self.enum_input([]))

    def test_05_mapping_enum_tag_is_typed_validation(self):
        with self.assertRaisesRegex(HardwareGenomeValidationError,
                                    "enum tag must be a string"):
            canonical_deserialize(self.enum_input({"fake": "enum"}))

    def test_06_scalar_nonstring_enum_tags_fail_closed(self):
        for tag in (None, False, True, 17, 1.25):
            with self.subTest(tag=repr(tag)):
                with self.assertRaises(HardwareGenomeValidationError):
                    canonical_deserialize(self.enum_input(tag).encode("utf-8"))

    def test_07_unknown_string_record_remains_admission_error(self):
        with self.assertRaises(HardwareGenomeAdmissionError):
            canonical_deserialize(self.record_input("builtins.eval"))

    def test_08_unknown_string_enum_remains_admission_error(self):
        with self.assertRaises(HardwareGenomeAdmissionError):
            canonical_deserialize(self.enum_input("builtins.eval"))

    def test_09_valid_canonical_genome_byte_roundtrip_is_unchanged(self):
        original = genome()
        encoded = canonical_serialize(original)
        restored = canonical_deserialize(encoded)
        self.assertEqual(restored, original)
        self.assertEqual(canonical_serialize(restored), encoded)

    def test_10_noncanonical_valid_record_still_fails_integrity(self):
        encoded = canonical_serialize(genome())
        altered = encoded.replace(b'"format"', b'"format" ', 1)
        self.assertNotEqual(encoded, altered)
        with self.assertRaises(HardwareGenomeIntegrityError):
            canonical_deserialize(altered)


if __name__ == "__main__":
    unittest.main()
