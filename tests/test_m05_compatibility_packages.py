from __future__ import annotations

import unittest

from iris_asset_dna.compatibility import REQUIRED_COMPATIBILITY_AXES, CompatibilityAxisResult, DNACompatibilityProfile
from iris_asset_dna.enums import (
    CompatibilityAxisState,
    DependencyKind,
    IdentityContinuity,
    MigrationActionKind,
    PackageLifecycle,
    PortabilityLevel,
    TraitCriticality,
    TraitMutability,
)
from iris_asset_dna.errors import DNAAdmissionError, DNAIntegrityError, DNALimitError, DNAValidationError
from iris_asset_dna.limits import DNARecordLimits
from iris_asset_dna.migration import DNAMigrationPlan, MigrationAction, apply_migration, verify_migration_receipt
from iris_asset_dna.packages import (
    DNAPackageConformanceReport,
    PackageDependency,
    PackageExtension,
    conform_package,
    project_package_interface,
    resolve_dependency_closure,
    transition_package_lifecycle,
    verify_package_conformance_report,
)
from iris_asset_dna.traits import TraitSchemaRef
from m05_support import AUTHORITY, POLICY, package_manifest, ref, revision, trait


class TestM05CompatibilityAndPackages(unittest.TestCase):
    def test_migration_preserves_renames_drops_and_defaults_as_separate_surfaces(self):
        source_traits = (
            trait("identity.signature", "blue", criticality=TraitCriticality.IDENTITY_DEFINING, mutability=TraitMutability.IMMUTABLE),
            trait("identity.context.nickname", "old", schema_family="identity.core", criticality=TraitCriticality.CONTEXTUAL, mutability=TraitMutability.CONTEXTUAL_VARIANT),
        )
        source = revision("dna-migrate-surfaces", traits=source_traits)
        default = trait("identity.presentation.style", "neutral", schema_family="identity.appearance", criticality=TraitCriticality.CONTEXTUAL, mutability=TraitMutability.CONTEXTUAL_VARIANT)
        plan = DNAMigrationPlan(
            "migration-surfaces",
            source.ref,
            "iris-m05-core",
            source.schema_version,
            source.family,
            "iris-m05-core",
            "iris-m05-core-v2",
            (
                MigrationAction(MigrationActionKind.PRESERVE, "identity.signature", "identity.signature"),
                MigrationAction(MigrationActionKind.RENAME, "identity.context.alias", "identity.context.nickname"),
                MigrationAction(MigrationActionKind.DEFAULT, "identity.presentation.style", default_trait=default),
            ),
            IdentityContinuity.PRESERVE,
            AUTHORITY,
            POLICY,
        )
        result = apply_migration(source, plan, new_revision_id="r2", new_revision_number=2)
        self.assertEqual(result.receipt.preserved_paths, ("identity.signature",))
        self.assertEqual(result.receipt.transformed_paths, ("identity.context.nickname",))
        self.assertEqual(result.receipt.defaulted_paths, ("identity.presentation.style",))
        self.assertFalse(result.receipt.dropped_paths)
        self.assertTrue(verify_migration_receipt(result.receipt))
        self.assertEqual(source.trait_map()["identity.context.nickname"].value, "old")

    def test_explicit_loss_and_identity_break_are_never_hidden(self):
        source = revision("dna-break", traits=(trait("identity.signature"), trait("identity.context.state", "temporary", schema_family="identity.core", criticality=TraitCriticality.CONTEXTUAL, mutability=TraitMutability.CONTEXTUAL_VARIANT)))
        lossy_plan = DNAMigrationPlan(
            "migration-loss",
            source.ref,
            "iris-m05-core",
            source.schema_version,
            source.family,
            "iris-m05-core",
            "iris-m05-core-v2",
            (
                MigrationAction(MigrationActionKind.PRESERVE, "identity.signature", "identity.signature"),
                MigrationAction(MigrationActionKind.DROP, "identity.context.state", "identity.context.state", loss_declared=True, loss_reason="context deliberately removed"),
            ),
            IdentityContinuity.PRESERVE,
            AUTHORITY,
            POLICY,
        )
        lossy = apply_migration(source, lossy_plan, new_revision_id="r2", new_revision_number=2)
        self.assertEqual(lossy.receipt.dropped_paths, ("identity.context.state",))
        self.assertEqual(lossy.receipt.identity_continuity, IdentityContinuity.PRESERVE)
        break_plan = DNAMigrationPlan(
            "migration-break",
            source.ref,
            "iris-m05-core",
            source.schema_version,
            source.family,
            "iris-m05-core",
            "iris-m05-core-v3",
            (
                MigrationAction(MigrationActionKind.DROP, "identity.signature", "identity.signature", loss_declared=True, loss_reason="identity discontinuity"),
                MigrationAction(MigrationActionKind.DROP, "identity.context.state", "identity.context.state", loss_declared=True, loss_reason="context retired"),
                MigrationAction(MigrationActionKind.DEFAULT, "identity.core.new_identity_marker", default_trait=trait("identity.core.new_identity_marker", "child", schema_family="identity.core")),
            ),
            IdentityContinuity.BREAK_REQUIRED,
            AUTHORITY,
            POLICY,
        )
        broken = apply_migration(source, break_plan, new_revision_id="r1", new_revision_number=1, new_dna_id="dna-break-child")
        self.assertNotEqual(broken.identity.dna_id, source.dna_id)
        self.assertEqual(broken.receipt.identity_continuity, IdentityContinuity.BREAK_REQUIRED)
        self.assertTrue(verify_migration_receipt(broken.receipt))
        with self.assertRaises(DNAIntegrityError):
            apply_migration(source, break_plan, new_revision_id="r2", new_revision_number=2, new_dna_id="dna-break-child")

    def test_lossy_compatibility_requires_a_path_surface_and_unknown_stays_unknown(self):
        subject = revision()
        results = [CompatibilityAxisResult(axis, CompatibilityAxisState.COMPATIBLE, "verified") for axis in REQUIRED_COMPATIBILITY_AXES]
        results[2] = CompatibilityAxisResult("traits", CompatibilityAxisState.LOSS, "one path omitted", ("identity.signature",))
        profile = DNACompatibilityProfile("lossy", subject.ref, ref("m34", "consumer.capability", "small-target"), tuple(results))
        self.assertEqual(profile.outcome.value, "COMPATIBLE_WITH_LOSS")
        partial = DNACompatibilityProfile("unknown", subject.ref, ref("m34", "consumer.capability", "unknown-target"), tuple(results[:-1]))
        self.assertEqual(partial.outcome.value, "INDETERMINATE")
        with self.assertRaises(DNAValidationError):
            CompatibilityAxisResult("traits", CompatibilityAxisState.LOSS, "missing path not declared")

    def test_package_extensions_dependencies_and_conformance_fail_closed(self):
        subject = revision()
        unknown_mandatory = PackageExtension(TraitSchemaRef("future.package.extension", "1", True), {"value": "opaque"})
        mandatory_report = conform_package(package_manifest(subject, extensions=(unknown_mandatory,)), (subject,), ())
        self.assertFalse(mandatory_report.valid)
        self.assertIn("UNKNOWN_MANDATORY_PACKAGE_EXTENSION", mandatory_report.findings)
        unknown_optional = PackageExtension(TraitSchemaRef("future.optional.extension", "1", False), {"value": "opaque"})
        unpreserved_report = conform_package(package_manifest(subject, extensions=(unknown_optional,)), (subject,), ())
        self.assertIn("UNPRESERVED_OPTIONAL_PACKAGE_EXTENSION", unpreserved_report.findings)
        preserved = PackageExtension(unknown_optional.schema_ref, unknown_optional.value, POLICY)
        preserved_report = conform_package(package_manifest(subject, extensions=(preserved,)), (subject,), ())
        self.assertTrue(preserved_report.valid)
        self.assertTrue(verify_package_conformance_report(preserved_report))
        self.assertFalse(preserved_report.checks_legal_rights)
        self.assertFalse(preserved_report.checks_semantic_equivalence)
        with self.assertRaises(DNAAdmissionError):
            DNAPackageConformanceReport("bad", "0" * 64, True, (), (), (), (), True, False, "0" * 64)

        required = PackageDependency("dep-required", DependencyKind.REQUIRED_CANONICAL, ref("m05", "schema.ref", "schema-v1"), ("dep-optional",))
        optional = PackageDependency("dep-optional", DependencyKind.OPTIONAL_EXTERNAL_DNA, ref("m40", "voice.dna", "voice-ref"))
        manifest = package_manifest(subject, dependencies=(required, optional))
        closure = resolve_dependency_closure(manifest, ())
        self.assertEqual(closure.missing_required_ids, ("dep-required",))
        self.assertEqual(closure.missing_optional_ids, ("dep-optional",))
        cycle_a = PackageDependency("cycle-a", DependencyKind.REQUIRED_CANONICAL, ref("m05", "schema.ref", "a"), ("cycle-b",))
        cycle_b = PackageDependency("cycle-b", DependencyKind.REQUIRED_CANONICAL, ref("m05", "schema.ref", "b"), ("cycle-a",))
        with self.assertRaises(DNAIntegrityError):
            resolve_dependency_closure(package_manifest(subject, dependencies=(cycle_a, cycle_b)), ())

    def test_interface_projection_and_lifecycle_preserve_authority_and_history(self):
        subject = revision()
        manifest = package_manifest(subject, portability=PortabilityLevel.INTERFACE_ONLY)
        projection = project_package_interface(manifest)
        self.assertEqual(projection.subject_ids, (subject.dna_id,))
        self.assertFalse(hasattr(projection, "traits"))
        retired = transition_package_lifecycle(
            PackageLifecycle.ACTIVE,
            PackageLifecycle.RETIRED,
            package_ref=ref("m05", "reusable.package", manifest.package_id, version=manifest.version),
            authority_ref=AUTHORITY,
            policy_ref=POLICY,
            reason="retire while preserving history",
            history_refs=(ref("m05", "package.history", manifest.package_id, version=manifest.version),),
        )
        self.assertEqual(retired.next, PackageLifecycle.RETIRED)
        with self.assertRaises(DNAAdmissionError):
            transition_package_lifecycle(PackageLifecycle.ACTIVE, PackageLifecycle.DEPRECATED, package_ref=ref("m05", "reusable.package", "x"), authority_ref=AUTHORITY, policy_ref=POLICY, reason="no replacement")

    def test_adversarial_limits_bound_migration_packages_and_identity_history(self):
        source = revision(traits=(trait("identity.one"), trait("identity.two", schema_family="identity.core")))
        with self.assertRaises(DNALimitError):
            apply_migration(
                source,
                DNAMigrationPlan(
                    "limits-plan", source.ref, "core", source.schema_version, source.family, "core", "core-v2",
                    (MigrationAction(MigrationActionKind.PRESERVE, "identity.one", "identity.one"), MigrationAction(MigrationActionKind.PRESERVE, "identity.two", "identity.two")),
                    IdentityContinuity.PRESERVE, AUTHORITY, POLICY,
                ),
                new_revision_id="r2", new_revision_number=2,
                limits=DNARecordLimits(max_traits=1),
            )


if __name__ == "__main__":
    unittest.main()
