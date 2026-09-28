"""WO0055: existing M06 closed JSON tag-type defense, provider-neutral OFFLINE."""
from __future__ import annotations

import json
import unittest

from iris_production_state.errors import (
    ProductionStateAdmissionError, ProductionStateIntegrityError,
    ProductionStateValidationError,
)
from iris_production_state.serialization import canonical_serialize, canonical_deserialize
from iris_production_state.versions import TRANSPORT_VERSION
from m06_support import semantic_revision


class M06MalformedUntrustedTags(unittest.TestCase):
    @staticmethod
    def baseline():
        return semantic_revision("wo0055-offline-artifact", "wo0055-offline-revision")

    @staticmethod
    def record_input(tag):
        return json.dumps({
            "format": TRANSPORT_VERSION,
            "record": {"$record": tag, "fields": {}},
        })

    @classmethod
    def enum_input(cls, tag, *, as_value=False):
        envelope = json.loads(canonical_serialize(cls.baseline()))

        def change(node):
            if type(node) is dict:
                if set(node) == {"$enum", "value"}:
                    if as_value:
                        node["value"] = tag
                    else:
                        node["$enum"] = tag
                    return True
                return any(change(x) for x in node.values())
            if type(node) is list:
                return any(change(x) for x in node)
            return False

        if not change(envelope):
            raise AssertionError("canonical M06 baseline has no registered enum")
        return json.dumps(envelope)

    def test_01_list_record_tag_is_typed_validation(self):
        with self.assertRaisesRegex(ProductionStateValidationError, "record tag must be a string"):
            canonical_deserialize(self.record_input([]))

    def test_02_mapping_record_tag_is_typed_validation(self):
        with self.assertRaisesRegex(ProductionStateValidationError, "record tag must be a string"):
            canonical_deserialize(self.record_input({"fake": "record"}))

    def test_03_scalar_nonstring_record_tags_fail_closed(self):
        for tag in (None, False, True, 17, 1.25):
            with self.subTest(tag=tag):
                with self.assertRaises(ProductionStateValidationError):
                    canonical_deserialize(self.record_input(tag))

    def test_04_list_enum_tag_is_typed_validation(self):
        with self.assertRaisesRegex(ProductionStateValidationError, "enum tag must be a string"):
            canonical_deserialize(self.enum_input([]))

    def test_05_mapping_enum_tag_is_typed_validation(self):
        with self.assertRaisesRegex(ProductionStateValidationError, "enum tag must be a string"):
            canonical_deserialize(self.enum_input({"fake": "enum"}))

    def test_06_scalar_nonstring_enum_tags_fail_closed(self):
        for tag in (None, False, True, 17, 1.25):
            with self.subTest(tag=tag):
                with self.assertRaises(ProductionStateValidationError):
                    canonical_deserialize(self.enum_input(tag))

    def test_07_unknown_string_tags_preserve_admission_boundary(self):
        with self.assertRaises(ProductionStateAdmissionError):
            canonical_deserialize(self.record_input("builtins.eval"))
        with self.assertRaises(ProductionStateAdmissionError):
            canonical_deserialize(self.enum_input("builtins.eval"))

    def test_08_canonical_valid_bytes_and_noncanonical_rejection_remain(self):
        original = self.baseline()
        encoded = canonical_serialize(original)
        restored = canonical_deserialize(encoded)
        self.assertEqual(restored, original)
        self.assertEqual(canonical_serialize(restored), encoded)
        changed = encoded.replace(b'"format"', b'"format" ', 1)
        self.assertNotEqual(changed, encoded)
        with self.assertRaises(ProductionStateIntegrityError):
            canonical_deserialize(changed)

    def test_09_nested_nonstring_tag_inside_enum_value_is_not_reclassified(self):
        for malformed in ({"$enum": [], "value": "fake"},
                          {"$record": [], "fields": {}}):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ProductionStateValidationError):
                    canonical_deserialize(self.enum_input(malformed, as_value=True))

    def test_10_invalid_value_of_registered_enum_is_typed_validation(self):
        with self.assertRaises(ProductionStateValidationError):
            canonical_deserialize(self.enum_input("WO0055-INVALID-ENUM-VALUE", as_value=True))


    def test_11_unpaired_surrogate_in_text_is_typed_validation(self):
        with self.assertRaisesRegex(ProductionStateValidationError, "valid UTF-8"):
            canonical_deserialize(chr(0xD800))


if __name__ == "__main__":
    unittest.main()
