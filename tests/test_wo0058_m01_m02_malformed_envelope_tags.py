"""WO0058: frozen M01/M02 typed refusal of malformed transport version/type tags.

Uses each original kernel's actual accepted public record fixture. Pure OFFLINE.
"""
from __future__ import annotations

import json
import unittest

from iris_quality import serialization as m01
from iris_project_os import serialization as m02
from iris_quality.errors import (
    SchemaValidationError as M01ValidationError,
    UnsupportedVersionError as M01VersionError,
)
from iris_project_os.errors import (
    SchemaValidationError as M02ValidationError,
    UnsupportedVersionError as M02VersionError,
)
from iris_project_os.identity import EntityKind
from tests import m01_kernel_support as q
from tests import m02_kernel_support as p


class _MalformedEnvelopeTags:
    """Shared helpers; not a TestCase, so only concrete module tests count."""
    codec = None
    validation_error = None
    version_error = None
    build_original = None

    def baseline(self):
        original = self.build_original()
        text = self.codec.dumps(original)
        document = json.loads(text)
        self.assertIs(type(document), dict)
        self.assertIs(type(document["schema_version"]), str)
        self.assertIs(type(document["type"]), str)
        return original, text, document

    def assert_both_ingress_refuse(self, document, error_type, expression):
        for label, reader, payload in (
            ("text", self.codec.loads, json.dumps(document)),
            ("mapping", self.codec.from_envelope, document),
        ):
            with self.subTest(ingress=label):
                with self.assertRaisesRegex(error_type, expression):
                    reader(payload)

    def test_01_unhashable_list_schema_version_typed(self):
        _, _, document = self.baseline()
        document["schema_version"] = []
        self.assert_both_ingress_refuse(
            document, self.validation_error, "schema_version must be a string"
        )

    def test_02_unhashable_mapping_schema_version_typed(self):
        _, _, document = self.baseline()
        document["schema_version"] = {"future": "not-a-version"}
        self.assert_both_ingress_refuse(
            document, self.validation_error, "schema_version must be a string"
        )

    def test_03_other_nonstring_schema_versions_typed(self):
        for malformed in (None, False, True, 5, 2.75):
            with self.subTest(malformed=malformed):
                _, _, document = self.baseline()
                document["schema_version"] = malformed
                self.assert_both_ingress_refuse(
                    document, self.validation_error, "schema_version must be a string"
                )

    def test_04_unhashable_list_record_type_typed(self):
        _, _, document = self.baseline()
        document["type"] = []
        self.assert_both_ingress_refuse(
            document, self.validation_error, "envelope type must be a string"
        )

    def test_05_unhashable_mapping_record_type_typed(self):
        _, _, document = self.baseline()
        document["type"] = {"future": "not-a-kind"}
        self.assert_both_ingress_refuse(
            document, self.validation_error, "envelope type must be a string"
        )

    def test_06_other_nonstring_record_types_typed(self):
        for malformed in (None, False, True, 5, 2.75):
            with self.subTest(malformed=malformed):
                _, _, document = self.baseline()
                document["type"] = malformed
                self.assert_both_ingress_refuse(
                    document, self.validation_error, "envelope type must be a string"
                )

    def test_07_direct_validate_payload_helper_typed(self):
        _, _, document = self.baseline()
        for malformed in ([], {}, None, False, 5):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(
                    self.validation_error, "kernel type must be a string"
                ):
                    self.codec.validate_payload(malformed, document["payload"])

    def test_08_unknown_well_formed_version_still_unsupported(self):
        _, _, document = self.baseline()
        document["schema_version"] = "iris-unknown-future-version-wo0058"
        self.assert_both_ingress_refuse(
            document, self.version_error, "unsupported schema_version"
        )

    def test_09_unknown_well_formed_type_still_schema_refusal(self):
        _, _, document = self.baseline()
        document["type"] = "future_unsupported_type_wo0058"
        self.assert_both_ingress_refuse(
            document, self.validation_error, "unknown envelope type"
        )

    def test_10_canonical_pretty_and_direct_helper_roundtrip_unchanged(self):
        original, text, document = self.baseline()
        self.assertEqual(self.codec.loads(text), original)
        self.assertEqual(self.codec.dumps(self.codec.loads(text)), text)
        self.assertEqual(self.codec.from_envelope(document), original)
        self.assertEqual(
            self.codec.validate_payload(document["type"], document["payload"]),
            original,
        )
        pretty = self.codec.dumps(original, indent=2)
        self.assertEqual(self.codec.loads(pretty), original)

    def test_11_existing_digest_tampering_still_refused(self):
        _, _, document = self.baseline()
        document["payload_sha256"] = "0" * 64
        self.assert_both_ingress_refuse(
            document, self.validation_error, "does not match payload_sha256"
        )


class TestM01MalformedEnvelopeTags(_MalformedEnvelopeTags, unittest.TestCase):
    codec = m01
    validation_error = M01ValidationError
    version_error = M01VersionError
    build_original = staticmethod(lambda: q.EVALUATOR)


class TestM02MalformedEnvelopeTags(_MalformedEnvelopeTags, unittest.TestCase):
    codec = m02
    validation_error = M02ValidationError
    version_error = M02VersionError
    build_original = staticmethod(lambda: p.ref(EntityKind.ARTIFACT, "asset.wo0058"))


if __name__ == "__main__":
    unittest.main()
