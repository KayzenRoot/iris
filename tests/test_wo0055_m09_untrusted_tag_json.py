"""WO0055: existing M09 closed JSON tag and UTF-8 defense, OFFLINE only."""
from __future__ import annotations

import json
import unittest

from iris_resource_twin.serialization import deserialize, serialize, round_trip
from m09_support import make_snapshot


class M09MalformedUntrustedTags(unittest.TestCase):
    @staticmethod
    def record_input(tag):
        return json.dumps({"$record": tag, "fields": {}})

    @staticmethod
    def enum_input(tag):
        return json.dumps({"$enum": tag, "name": "VRAM"})

    @staticmethod
    def mutate_nested_snapshot(node):
        snapshot = json.loads(serialize(make_snapshot()))
        # Existing frozen ResourceSnapshot -> ResourceIdentity -> ResourceTier.
        identity = snapshot["fields"]["identity"]
        if not (type(identity) is dict and "$record" in identity
                and type(identity.get("fields")) is dict
                and "tier" in identity["fields"]):
            raise AssertionError("original M09 ResourceIdentity typed fixture drift")
        identity["fields"]["tier"] = node
        return json.dumps(snapshot)

    def test_01_list_record_tag_is_bounded_value_error(self):
        with self.assertRaisesRegex(ValueError, "record tag must be a string"):
            deserialize(self.record_input([]))

    def test_02_mapping_record_tag_is_bounded_value_error(self):
        with self.assertRaisesRegex(ValueError, "record tag must be a string"):
            deserialize(self.record_input({"fake": "record"}))

    def test_03_scalar_nonstring_record_tags_are_rejected(self):
        for tag in (None, False, True, 17, 1.25):
            with self.subTest(tag=tag):
                with self.assertRaises(ValueError):
                    deserialize(self.record_input(tag).encode("utf-8"))

    def test_04_list_enum_tag_is_bounded_value_error(self):
        with self.assertRaisesRegex(ValueError, "enum tag must be a string"):
            deserialize(self.enum_input([]))

    def test_05_mapping_enum_tag_is_bounded_value_error(self):
        with self.assertRaisesRegex(ValueError, "enum tag must be a string"):
            deserialize(self.enum_input({"fake": "enum"}))

    def test_06_scalar_nonstring_enum_tags_are_rejected(self):
        for tag in (None, False, True, 17, 1.25):
            with self.subTest(tag=tag):
                with self.assertRaises(ValueError):
                    deserialize(self.enum_input(tag).encode("utf-8"))

    def test_07_nested_malformed_tags_are_caught_before_record_construction(self):
        for malformed in ({"$enum": [], "name": "VRAM"},
                          {"$record": [], "fields": {}}):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    deserialize(self.mutate_nested_snapshot(malformed))

    def test_08_invalid_utf8_bytes_have_typed_value_error(self):
        for malformed in (b"\xff", b'{"payload":"\xff"}'):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(ValueError, "valid UTF-8"):
                    deserialize(malformed)

    def test_09_unknown_string_tags_remain_rejected(self):
        with self.assertRaises(ValueError):
            deserialize(self.record_input("builtins.eval"))
        with self.assertRaises(ValueError):
            deserialize(self.enum_input("builtins.eval"))

    def test_10_original_snapshot_roundtrips_without_changing_canonical_bytes(self):
        source = make_snapshot()
        encoded = serialize(source)
        self.assertEqual(serialize(deserialize(encoded)), encoded)
        self.assertEqual(round_trip(source), source)


    def test_11_unpaired_surrogate_in_text_is_typed_value_error(self):
        with self.assertRaisesRegex(ValueError, "valid UTF-8"):
            deserialize("\\ud800")


if __name__ == "__main__":
    unittest.main()
