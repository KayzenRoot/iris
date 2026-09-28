"""WO0056: source-exact M01/M02/M03 canonical JSON ingress forbids duplicate keys.

One neutral synthetic fixture per already-implemented frozen kernel; no runtime.
"""
from __future__ import annotations

import json
import re
import unittest

from iris_quality import serialization as m01
from iris_project_os import serialization as m02
from iris_intent import serialization as m03
from iris_quality.errors import SchemaValidationError as M01ValidationError
from iris_project_os.errors import SchemaValidationError as M02ValidationError
from iris_intent.errors import SchemaValidationError as M03ValidationError
from iris_project_os.identity import EntityKind
from tests import m01_kernel_support as q
from tests import m02_kernel_support as p
from tests import m03_kernel_support as i


class _ClosedDuplicateJsonIngress:
    """No TestCase base: only the concrete three module harnesses are counted."""
    codec = None
    error_type = None
    build_fixture = None

    def normal(self):
        source = self.build_fixture()
        encoded = self.codec.dumps(source)
        value = json.loads(encoded)
        self.assertIs(type(value), dict)
        self.assertIs(type(value["payload"]), dict)
        return source, encoded, value

    @staticmethod
    def duplicate_at_root(encoded, key, value):
        # Put the same key/value BEFORE the original canonical root entry.
        # Previously last-wins parsing silently collapsed this malformed wire.
        prefix = json.dumps(key, ensure_ascii=False) + ":" + json.dumps(
            value, ensure_ascii=False, separators=(",", ":")
        ) + ","
        return "{" + prefix + encoded[1:]

    def test_01_repeated_identical_top_level_key_is_refused(self):
        _source, encoded, obj = self.normal()
        key = next(iter(obj))
        attack = self.duplicate_at_root(encoded, key, obj[key])
        self.assertEqual(json.loads(attack), obj)
        with self.assertRaisesRegex(self.error_type, "duplicate JSON object key"):
            self.codec.loads(attack)

    def test_02_repeated_identical_nested_payload_key_is_refused(self):
        _source, encoded, obj = self.normal()
        payload = obj["payload"]
        key = next(iter(payload))
        nested = json.dumps(key, ensure_ascii=False) + ":" + json.dumps(
            payload[key], ensure_ascii=False, separators=(",", ":")
        ) + ","
        attack, count = re.subn(
            r'("payload"\s*:\s*\{)',
            lambda m: m.group(1) + nested,
            encoded,
            count=1,
        )
        self.assertEqual(count, 1, "frozen envelope must have one object payload")
        self.assertEqual(json.loads(attack), obj)
        with self.assertRaisesRegex(self.error_type, "duplicate JSON object key"):
            self.codec.loads(attack)

    def test_03_conflicting_duplicate_top_level_key_is_refused(self):
        _source, encoded, obj = self.normal()
        key = next(iter(obj))
        attack = self.duplicate_at_root(encoded, key, None)
        self.assertEqual(json.loads(attack), obj)
        with self.assertRaisesRegex(self.error_type, "duplicate JSON object key"):
            self.codec.loads(attack)

    def test_04_valid_canonical_and_pretty_roundtrip_unchanged(self):
        original, encoded, obj = self.normal()
        self.assertEqual(self.codec.loads(encoded), original)
        self.assertEqual(self.codec.dumps(self.codec.loads(encoded)), encoded)
        # M01/M02 already support pretty JSON; M03's single canonical dumps
        # remains unchanged, but its reader still supports formatted JSON.
        pretty = json.dumps(obj, indent=2, ensure_ascii=False)
        self.assertEqual(self.codec.loads(pretty), original)


class TestM01DuplicateJsonIngress(_ClosedDuplicateJsonIngress, unittest.TestCase):
    codec = m01
    error_type = M01ValidationError
    build_fixture = staticmethod(lambda: q.EVALUATOR)


class TestM02DuplicateJsonIngress(_ClosedDuplicateJsonIngress, unittest.TestCase):
    codec = m02
    error_type = M02ValidationError
    build_fixture = staticmethod(lambda: p.ref(EntityKind.ARTIFACT, "asset.wo0056"))


class TestM03DuplicateJsonIngress(_ClosedDuplicateJsonIngress, unittest.TestCase):
    codec = m03
    error_type = M03ValidationError
    build_fixture = staticmethod(lambda: i.brief_identity())


if __name__ == "__main__":
    unittest.main()
