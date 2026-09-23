from __future__ import annotations

import unittest
from dataclasses import fields
from pathlib import Path
import re

from iris_asset_dna.anchors import DNAProjectionContract, IdentityAnchor, apply_anchor_operation, project_revision
from iris_asset_dna.analysis import (
    EquivalenceAxisResult,
    build_equivalence_witness,
    decide_equivalence,
)
from iris_asset_dna.compatibility import REQUIRED_COMPATIBILITY_AXES, CompatibilityAxisResult, DNACompatibilityProfile
from iris_asset_dna.context import build_dna_slice
from iris_asset_dna.cross_modal import (
    BrandDNALink,
    CrossModalDNAGraph,
    CrossModalEdge,
    CrossModalIdentityBinding,
    CrossModalIdentityObligation,
    IdentityRoleSlot,
    LinkedDomainDNARef,
    MotionDNALink,
    SceneIdentityDNA,
    SceneIdentityMember,
    VoiceDNALink,
    validate_crossmodal_binding,
    revision_node_ref,
    validate_scene_identity,
)
from iris_asset_dna.drift import (
    IdentityContinuityEnvelope,
    IdentityDriftEvidence,
    build_drift_report,
    validate_continuity_envelope,
)
from iris_asset_dna.enums import (
    AnchorAuthorityClass,
    AnchorLifecycleOperation,
    CompatibilityAxisState,
    CompatibilityOutcome,
    DependencyKind,
    DNAFamily,
    DNAIdentityLevel,
    DriftDimension,
    DriftEvidenceResult,
    DriftState,
    IdentityContinuity,
    ImportAdmissionState,
    ImportCollisionOutcome,
    LinkFreshness,
    LinkRequirement,
    LineageRelation,
    MutationDecisionKind,
    MigrationActionKind,
    ObligationExpectation,
    PackageLifecycle,
    RiskCode,
    RiskSeverity,
    TraitApplicability,
    TraitCriticality,
    TraitMutability,
)
from iris_asset_dna.errors import DNAAdmissionError, DNAIntegrityError, DNALimitError, DNAValidationError
from iris_asset_dna.families import (
    CharacterDNA,
    ComponentTransition,
    ContextualAppearanceState,
    CreatureDNA,
    DNAComponentIdentity,
    DNAFamilyProfile,
    DNATraitBundle,
    EnvironmentDNA,
    ObjectDNA,
    PersistentAppearanceTrait,
    ProductDNA,
    ProductIdentityRelation,
    validate_component_transition,
)
from iris_asset_dna.identity import (
    AssetDNAIdentity,
    DNARevisionRef,
    validate_envelope,
    validate_revision,
)
from iris_asset_dna.limits import DNARecordLimits
from iris_asset_dna.imports import (
    advance_import_admission,
    create_import_admission,
    find_import_collisions,
    resolve_import_collision,
)
from iris_asset_dna.invariants import M05_INVARIANTS, invariants_for_family, validate_invariant_catalog
from iris_asset_dna.lineage import (
    DNAIdentityLineageEdge,
    IdentityAlias,
    IdentityConsolidationProposal,
    IdentityEquivalenceClaim,
    IdentitySplitAllocation,
    build_split_plan,
    create_identity_break,
    record_consolidation,
)
from iris_asset_dna.migration import DNAMigrationPlan, MigrationAction, apply_migration, verify_migration_receipt
from iris_asset_dna.packages import (
    DNAMarketplaceContract,
    PackageDependency,
    conform_package,
    project_package_interface,
    resolve_dependency_closure,
    transition_package_lifecycle,
    verify_package_conformance_report,
)
from iris_asset_dna.risk import IDENTITY_RISK_CODES, IdentityRiskFinding, build_identity_risk_report
from iris_asset_dna.traits import (
    DEFAULT_TRAIT_SCHEMAS,
    IdentityEvidence,
    TraitSchemaRegistry,
)
from iris_asset_dna.transitions import (
    DNAMutationProposal,
    DNATraitChange,
    IdentityMutationDecision,
    admit_same_identity_revision,
    verify_mutation_receipt,
)
from m05_support import AUTHORITY, EVIDENCE, POLICY, PROVENANCE, envelope, package_manifest, ref, revision, trait


class TestFrozenInvariantFamilies(unittest.TestCase):
    def test_catalog_proofs_are_bound_to_existing_family_tests(self):
        validate_invariant_catalog()
        self.assertEqual([item.number for item in M05_INVARIANTS], list(range(1, 151)))
        self.assertEqual({item.family for item in M05_INVARIANTS}, {f"F-M05-{i:02d}" for i in range(1, 26)})
        self.assertEqual(sum(len(invariants_for_family(f"F-M05-{i:02d}")) for i in range(1, 26)), 150)
        for item in M05_INVARIANTS:
            self.assertTrue(callable(getattr(self, item.proof_method)), item.proof_method)
        contract_path = Path(__file__).resolve().parents[1] / "planning" / "contracts" / "M05-MODULE-CONTRACT-FREEZE-CANDIDATE.md"
        contract = contract_path.read_text(encoding="utf-8")
        invariant_section = contract.split("## 5. Hard invariants", 1)[1].split("## 6. Identity substrate contract", 1)[0]
        frozen_statements = {
            int(number): statement.strip()
            for number, statement in re.findall(r"^\s*(\d{1,3})\.\s+(.+?)\s*$", invariant_section, re.MULTILINE)
        }
        self.assertEqual(frozen_statements, {item.number: item.statement for item in M05_INVARIANTS})

    def test_family_01_behavior(self):
        first = revision("dna-stable", "r1", 1, display_metadata={"path": "assets/a.png"})
        second = revision("dna-stable", "r2", 2, parent_revision_refs=(first.ref,), display_metadata={"path": "cache/b.png"}, evidence_refs=(EVIDENCE,))
        other_id = revision("dna-other", "r1", 1)
        self.assertEqual(first.semantic_digest, second.semantic_digest)
        self.assertEqual(first.semantic_digest, other_id.semantic_digest)
        validate_envelope(envelope(first, second))
        with self.assertRaises(DNAIntegrityError):
            validate_envelope(envelope(first, second, head_revision_id="r1"))
        self.assertNotEqual(first.ref, second.ref)

    def test_family_02_behavior(self):
        states = tuple(trait(f"identity.state{i}", applicability=state) for i, state in enumerate(TraitApplicability))
        self.assertEqual({item.applicability for item in states}, set(TraitApplicability))
        unknown_schema = trait("identity.future", schema_family="future.required", mandatory_schema=True)
        with self.assertRaises(DNAAdmissionError):
            validate_revision(revision(traits=(unknown_schema,)))
        opaque = trait(
            "identity.opaque", schema_family="future.optional", mandatory_schema=False,
            opaque_policy=ref("m05", "trait.preservation", "opaque-policy"),
        )
        TraitSchemaRegistry(DEFAULT_TRAIT_SCHEMAS.registered).validate(opaque)
        with self.assertRaises(DNAAdmissionError):
            TraitSchemaRegistry(DEFAULT_TRAIT_SCHEMAS.registered).validate(
                trait("identity.opaque", schema_family="future.optional", mandatory_schema=False)
            )
        self.assertEqual(states[0].criticality, TraitCriticality.IDENTITY_DEFINING)

    def test_family_03_behavior(self):
        evidence = IdentityEvidence("obs-1", "provider-observation", EVIDENCE, observed_path="identity.signature")
        self.assertFalse(isinstance(evidence, type(trait())))
        derived = trait("identity.derived", criticality=TraitCriticality.DERIVED_EVIDENCE_ONLY)
        with self.assertRaises(DNAAdmissionError):
            validate_revision(revision(traits=(derived,)))
        restricted_policy = ref("m54", "privacy.policy", "restricted-policy")
        restricted = IdentityEvidence("obs-private", "restricted-observation", EVIDENCE, restricted=True, policy_refs=(restricted_policy,))
        self.assertTrue(restricted.restricted)

    def test_family_04_behavior(self):
        source = revision()
        observed = IdentityAnchor("anchor-observed", source.dna_id, AnchorAuthorityClass.OBSERVATION, ref("m04", "scene.snapshot", "snapshot"))
        with self.assertRaises(DNAAdmissionError):
            apply_anchor_operation(observed, AnchorLifecycleOperation.REBIND, event_id="event-observed", source_revision_ref=source.ref, reason="observed only", authority_ref=AUTHORITY, policy_ref=POLICY, new_target_ref=ref("m04", "scene.snapshot", "snapshot-2"))
        canonical = IdentityAnchor("anchor-canonical", source.dna_id, AnchorAuthorityClass.CANONICAL, ref("m04", "scene.snapshot", "snapshot"))
        with self.assertRaises(DNAAdmissionError):
            apply_anchor_operation(canonical, AnchorLifecycleOperation.REBIND, event_id="event-no-auth", source_revision_ref=source.ref, reason="rebind", new_target_ref=ref("m04", "scene.snapshot", "snapshot-2"))
        result = apply_anchor_operation(canonical, AnchorLifecycleOperation.REBIND, event_id="event-authorized", source_revision_ref=source.ref, reason="approved rebind", authority_ref=AUTHORITY, policy_ref=POLICY, new_target_ref=ref("m04", "scene.snapshot", "snapshot-2"))
        contract = DNAProjectionContract("projection-v1", source.ref, ("identity.signature",), preserved_trait_paths=("identity.signature",))
        self.assertEqual(project_revision(source, contract).projected_traits, source.traits)
        self.assertEqual(result.result_anchor.target_ref.ref_id, "snapshot-2")

    def test_family_05_behavior(self):
        left = revision("dna-left")
        right = revision("dna-right")
        axes = tuple(EquivalenceAxisResult(axis, "MATCH", (EVIDENCE,)) for axis in ("family", "identity_level", "schema", "traits", "components", "anchors", "domain_links"))
        witness = build_equivalence_witness(left, right, axes, (EVIDENCE,))
        decision = decide_equivalence(witness, authority_ref=AUTHORITY, policy_ref=POLICY, decision_evidence_refs=(EVIDENCE,))
        self.assertEqual(decision.outcome, "EQUIVALENT")
        self.assertNotEqual(left.dna_id, right.dna_id)
        claim = IdentityEquivalenceClaim("claim-1", left.ref, right.ref, (EVIDENCE,))
        alias = IdentityAlias("alias-1", left.dna_id, ref("m47", "external.identity", "legacy-id"), AUTHORITY, POLICY, left.ref)
        proposal = IdentityConsolidationProposal("consolidate-1", (left.ref, right.ref), (EVIDENCE,), "retain both source histories")
        receipt = record_consolidation(proposal, left.ref, authority_ref=AUTHORITY, policy_ref=POLICY)
        self.assertEqual(receipt.source_refs, proposal.source_refs)
        self.assertEqual(alias.dna_id, left.dna_id)
        self.assertEqual(claim.right_ref, right.ref)

    def test_family_06_behavior(self):
        source = revision(traits=(trait("identity.signature"), trait("identity.name", "Rin", schema_family="identity.core")))
        result = build_dna_slice(source, ("identity.signature",), dependency_map={"identity.signature": ("identity.name",)})
        self.assertEqual(result.included_paths, ("identity.name", "identity.signature"))
        self.assertEqual(result.dependency_paths, ("identity.name",))
        self.assertLessEqual(result.trait_count, len(source.traits))
        from collections.abc import Mapping

        class HostileDependencies(Mapping):
            def __getitem__(self, key):
                raise AssertionError("custom dependency map executed")

            def __iter__(self):
                raise AssertionError("custom dependency map executed")

            def __len__(self):
                raise AssertionError("custom dependency map executed")

        with self.assertRaises(DNAValidationError):
            build_dna_slice(source, ("identity.signature",), dependency_map=HostileDependencies())
        with self.assertRaises(DNALimitError):
            build_dna_slice(
                source,
                ("identity.signature",),
                dependency_map={"identity.signature": ("identity.name",)},
                limits=DNARecordLimits(max_graph_depth=1),
            )

    def test_family_07_behavior(self):
        profile = DNAFamilyProfile("character-v1", DNAFamily.CHARACTER, "1", (DNAIdentityLevel.INDIVIDUAL,), required_namespaces=("character.identity",), extension_namespaces=("character.custom",))
        source = revision("dna-char", family=DNAFamily.CHARACTER, traits=(trait("character.identity.name", "Mara", schema_family="character.identity"),))
        bundle = DNATraitBundle("character-bundle", source.dna_id, profile.reference, source.traits, ("character.identity.name",))
        self.assertEqual(bundle.dna_id, source.dna_id)
        self.assertEqual(profile.family, DNAFamily.CHARACTER)
        self.assertEqual(len(DEFAULT_TRAIT_SCHEMAS.registered), len({(item.family, item.version) for item in DEFAULT_TRAIT_SCHEMAS.registered}))

    def test_family_08_behavior(self):
        source_ref = ref("m05", "component.identity", "component-source")
        target_ref = ref("m05", "component.identity", "component-replacement")
        component = DNAComponentIdentity("component-1", "dna-object", "handle", DNAFamily.OBJECT, "1", ("object.part.handle",), source_component_refs=(source_ref,), provenance_refs=(PROVENANCE,))
        transition = ComponentTransition("transition-1", "REPLACE", (source_ref,), (target_ref,), AUTHORITY, POLICY, "replace broken handle")
        validate_component_transition(transition)
        self.assertEqual(component.reference.family, "component.identity")
        with self.assertRaises(DNAAdmissionError):
            validate_component_transition(ComponentTransition("split-invalid", "SPLIT", (source_ref,), (target_ref,), AUTHORITY, POLICY, "split needs more than one target"))

    def test_family_09_behavior(self):
        character_profile = DNAFamilyProfile("character-profile", DNAFamily.CHARACTER, "1", (DNAIdentityLevel.INDIVIDUAL,), required_namespaces=("character.identity",))
        character = revision("dna-character", family=DNAFamily.CHARACTER, traits=(trait("character.identity.name", "Ari", schema_family="character.identity"),))
        CharacterDNA(AssetDNAIdentity(character.dna_id, "character", DNAFamily.CHARACTER, provenance_refs=(PROVENANCE,)), character, character_profile)
        creature_profile = DNAFamilyProfile("creature-profile", DNAFamily.CREATURE, "1", (DNAIdentityLevel.ARCHETYPE, DNAIdentityLevel.INDIVIDUAL), required_namespaces=("creature.taxonomy",), allowed_component_roles=("left-wing", "tail", "sensory-fin"))
        creature = revision("dna-creature", family=DNAFamily.CREATURE, identity_level=DNAIdentityLevel.ARCHETYPE, traits=(trait("creature.taxonomy.species", "asymmetric-glider", schema_family="creature.taxonomy"),))
        CreatureDNA(AssetDNAIdentity(creature.dna_id, "creature", DNAFamily.CREATURE, provenance_refs=(PROVENANCE,)), creature, creature_profile)
        self.assertIn("left-wing", creature_profile.allowed_component_roles)

    def test_family_10_behavior(self):
        object_profile = DNAFamilyProfile("object-profile", DNAFamily.OBJECT, "1", (DNAIdentityLevel.INDIVIDUAL,))
        object_revision = revision("dna-tool", family=DNAFamily.OBJECT)
        ObjectDNA(AssetDNAIdentity(object_revision.dna_id, "object", DNAFamily.OBJECT, provenance_refs=(PROVENANCE,)), object_revision, object_profile)
        product_profile = DNAFamilyProfile("product-profile", DNAFamily.PRODUCT, "1", (DNAIdentityLevel.PRODUCT_FAMILY, DNAIdentityLevel.MODEL, DNAIdentityLevel.VARIANT_SKU))
        product_revision = revision("dna-product", family=DNAFamily.PRODUCT, identity_level=DNAIdentityLevel.PRODUCT_FAMILY)
        ProductDNA(AssetDNAIdentity(product_revision.dna_id, "product", DNAFamily.PRODUCT, provenance_refs=(PROVENANCE,)), product_revision, product_profile)
        relation = ProductIdentityRelation(ref("m05", "product.identity", "family", revision_id="r1"), DNAIdentityLevel.PRODUCT_FAMILY, ref("m05", "product.identity", "model", revision_id="r1"), DNAIdentityLevel.MODEL, ("product.geometry.form",), ("product.variant.finish",))
        self.assertEqual(relation.parent_level, DNAIdentityLevel.PRODUCT_FAMILY)
        with self.assertRaises(DNAAdmissionError):
            ProductIdentityRelation(relation.parent_ref, DNAIdentityLevel.MODEL, relation.child_ref, DNAIdentityLevel.PRODUCT_FAMILY, (), ())

    def test_family_11_behavior(self):
        profile = DNAFamilyProfile("environment-profile", DNAFamily.ENVIRONMENT, "1", (DNAIdentityLevel.INDIVIDUAL,), required_namespaces=("environment.landmark",))
        source = revision("dna-set", family=DNAFamily.ENVIRONMENT, traits=(trait("environment.landmark.tower", "east-ridge", schema_family="environment.landmark"),))
        EnvironmentDNA(AssetDNAIdentity(source.dna_id, "environment", DNAFamily.ENVIRONMENT, provenance_refs=(PROVENANCE,)), source, profile)
        contextual = ContextualAppearanceState("fog-state", ref("m04", "scene.context", "shot-12"), (("environment.weather.fog", "dense"),))
        persistent = PersistentAppearanceTrait(trait("identity.appearance.silhouette", "ridge-line", schema_family="identity.appearance", criticality=TraitCriticality.IDENTITY_SIGNIFICANT, mutability=TraitMutability.MUTABLE_WITH_EXPLICIT_POLICY))
        self.assertEqual(contextual.context_ref.owner_module, "m04")
        self.assertEqual(persistent.trait.path, "identity.appearance.silhouette")

    def test_family_12_behavior(self):
        motion = LinkedDomainDNARef("motion-link", "m30", "motion.dna", "motion-id", "rev-4", "4", LinkRequirement.REQUIRED, ("character.body",), ("motion.identity",))
        with self.assertRaises(DNAAdmissionError):
            LinkedDomainDNARef("latest-link", "m30", "motion.dna", "motion-id", "latest", "4", LinkRequirement.REQUIRED, (), ())
        stale = LinkedDomainDNARef("stale-motion", "m30", "motion.dna", "motion-id", "rev-3", "3", LinkRequirement.REQUIRED, (), (), freshness=LinkFreshness.STALE)
        with self.assertRaises(DNAAdmissionError):
            stale.validate_required_freshness()
        self.assertEqual(motion.pinned_ref.revision_id, "rev-4")

    def test_family_13_behavior(self):
        member_revision = revision("dna-performer", family=DNAFamily.CHARACTER, traits=(trait("character.identity.name", "Tala", schema_family="character.identity"),))
        slot = IdentityRoleSlot("lead", (DNAFamily.CHARACTER,), ("character.identity.name",), minimum_members=1, maximum_members=1)
        scene_revision = revision("dna-scene", "scene-r1", 1, family=DNAFamily.SCENE)
        scene = SceneIdentityDNA(scene_revision.ref, (slot,), (SceneIdentityMember("lead", member_revision.ref, DNAFamily.CHARACTER),), scene_ir_projection_ref=ref("m04", "scene.ir.snapshot", "shot-1"))
        validate_scene_identity(scene, (scene_revision, member_revision))
        with self.assertRaises(DNAAdmissionError):
            IdentityRoleSlot("lead", (DNAFamily.CHARACTER,), allowed_substitute_role_ids=("understudy",))
        self.assertEqual(scene.scene_ir_projection_ref.owner_module, "m04")

    def test_family_14_behavior(self):
        motion_ref = LinkedDomainDNARef("motion", "m30", "motion.dna", "motion-a", "rev-1", "1", LinkRequirement.OPTIONAL, (), ())
        voice_ref = LinkedDomainDNARef("voice", "m40", "voice.dna", "voice-a", "rev-1", "1", LinkRequirement.OPTIONAL, (), ())
        brand_ref = LinkedDomainDNARef("brand", "m46", "brand.dna", "brand-a", "rev-1", "1", LinkRequirement.OPTIONAL, (), ())
        self.assertEqual(MotionDNALink(motion_ref, "walk-cycle").reference.owner_module, "m30")
        self.assertEqual(VoiceDNALink(voice_ref, "narrator").reference.owner_module, "m40")
        self.assertEqual(BrandDNALink(brand_ref, "sponsor").reference.owner_module, "m46")
        with self.assertRaises(DNAAdmissionError):
            MotionDNALink(voice_ref, "walk-cycle")

    def test_family_15_behavior(self):
        revision_ref = revision().ref
        link = LinkedDomainDNARef("voice-link", "m40", "voice.dna", "voice-a", "rev-1", "1", LinkRequirement.REQUIRED, (), ())
        obligation = CrossModalIdentityObligation("sync-voice", ("voice-link",), ObligationExpectation.EXACT, True, ref("m01", "evaluator.authority", "crossmodal"))
        binding = CrossModalIdentityBinding("binding-1", revision_ref, (link,), (), (obligation,))
        validate_crossmodal_binding(binding)
        missing = CrossModalIdentityBinding("binding-missing", revision_ref, (), (), (obligation,))
        with self.assertRaises(DNAAdmissionError):
            validate_crossmodal_binding(missing)
        subject = revision()
        motion = LinkedDomainDNARef("graph-motion", "m30", "motion.dna", "motion-a", "rev-1", "1", LinkRequirement.REQUIRED, (), ())
        edge = CrossModalEdge("edge-motion", "HAS_MOTION_IDENTITY", revision_node_ref(subject.ref), motion.pinned_ref)
        graph = CrossModalDNAGraph("crossmodal-graph", (subject.ref,), (edge,), external_refs=(motion.pinned_ref,))
        self.assertEqual(graph.edges, (edge,))
        with self.assertRaises(DNAAdmissionError):
            CrossModalDNAGraph("undeclared-endpoint", (subject.ref,), (edge,))

    def test_family_16_behavior(self):
        source = revision()
        continuity = IdentityContinuityEnvelope("continuity-1", source.ref, ("identity.signature",), evaluator_owner_refs=(ref("m01", "evaluator.authority", "identity-drift"),))
        validate_continuity_envelope(continuity, source)
        unknown = IdentityDriftEvidence("unknown-signature", source.ref, "identity.signature", DriftDimension.CATEGORICAL, DriftEvidenceResult.UNKNOWN, TraitCriticality.IDENTITY_DEFINING, ref("m01", "evaluator.authority", "identity-drift"))
        report = build_drift_report("drift-1", continuity, (unknown,))
        self.assertEqual(report.state, DriftState.INDETERMINATE)
        self.assertFalse(report.admits_mutation)
        self.assertNotIn("score", {item.name for item in fields(report)})

    def test_family_17_behavior(self):
        source_trait = trait("character.signature.mark", "scar-A", schema_family="character.signature", criticality=TraitCriticality.IDENTITY_SIGNIFICANT, mutability=TraitMutability.MUTABLE_WITH_EXPLICIT_POLICY)
        source = revision("dna-mutation", traits=(source_trait,))
        new_trait = trait("character.signature.mark", "scar-B", schema_family="character.signature", criticality=TraitCriticality.IDENTITY_SIGNIFICANT, mutability=TraitMutability.MUTABLE_WITH_EXPLICIT_POLICY)
        proposal = DNAMutationProposal("proposal-1", source.dna_id, source.ref, (DNATraitChange(source_trait.path, new_trait),), "approved semantic update", "PRESERVE", (EVIDENCE,))
        decision = IdentityMutationDecision("decision-1", proposal.proposal_id, source.ref, MutationDecisionKind.ADMIT_SAME_IDENTITY_REVISION, AUTHORITY, POLICY, "authorized same identity revision")
        result, receipt = admit_same_identity_revision(source, proposal, decision, new_revision_id="r2", new_revision_number=2)
        self.assertEqual(result.dna_id, source.dna_id)
        self.assertEqual(result.parent_revision_refs, (source.ref,))
        self.assertTrue(verify_mutation_receipt(receipt))
        self.assertEqual(source.traits, (source_trait,))

    def test_family_18_behavior(self):
        source = revision(traits=(trait("identity.signature"), trait("identity.name", "M", schema_family="identity.core")))
        new_identity, child, lineage = create_identity_break(source, new_dna_id="dna-child", new_revision_id="r1", revision_number=1, inherited_paths=("identity.signature",), retired_paths=("identity.name",), reason="identity discontinuity", authority_ref=AUTHORITY, policy_ref=POLICY)
        self.assertNotEqual(new_identity.dna_id, source.dna_id)
        self.assertEqual(lineage.source_revision_ref, source.ref)
        child_ref = DNARevisionRef("dna-split-child", "r1", "a" * 64)
        allocation = IdentitySplitAllocation(child_ref, ("identity.signature",), (), ())
        plan = build_split_plan(source, split_id="split-1", allocations=(allocation,), retained_source_paths=("identity.name",), retired_source_paths=(), authority_ref=AUTHORITY, policy_ref=POLICY)
        self.assertEqual(plan.source_revision_ref, source.ref)
        self.assertEqual(child.revision_number, 1)

    def test_family_19_behavior(self):
        restricted_ref = ref("m54", "restricted.evidence", "private-ref")
        restricted = IdentityEvidence("private-evidence", "biometric-observation", restricted_ref, restricted=True, policy_refs=(ref("m54", "privacy.policy", "privacy"),))
        self.assertFalse(hasattr(restricted, "payload"))
        with self.assertRaises(DNAAdmissionError):
            IdentityEvidence("unprotected-private", "biometric-observation", restricted_ref, restricted=True, policy_refs=(POLICY,))
        self.assertEqual(restricted.source_ref.owner_module, "m54")

    def test_family_20_behavior(self):
        first = revision("dna-lineage", "r1", 1)
        second = revision("dna-lineage", "r2", 2, parent_revision_refs=(first.ref,))
        edge = DNAIdentityLineageEdge("lineage-edge", first.ref, second.ref, LineageRelation.SAME_IDENTITY_REVISION, authority_ref=AUTHORITY, policy_ref=POLICY)
        self.assertEqual(edge.source_ref.dna_id, edge.target_ref.dna_id)
        self.assertNotIn("branch_id", {item.name for item in fields(edge)})
        self.assertIsInstance(second.ref, DNARevisionRef)

    def test_family_21_behavior(self):
        source = revision("dna-migrate")
        axes = tuple(CompatibilityAxisResult(axis, CompatibilityAxisState.COMPATIBLE, "axis checked") for axis in REQUIRED_COMPATIBILITY_AXES)
        profile = DNACompatibilityProfile("compat-v1", source.ref, ref("m34", "consumer.capability", "portable"), axes)
        self.assertEqual(profile.outcome, CompatibilityOutcome.COMPATIBLE)
        self.assertEqual(DNACompatibilityProfile("partial", source.ref, ref("m34", "consumer.capability", "partial"), axes[:2]).outcome, CompatibilityOutcome.INDETERMINATE)
        plan = DNAMigrationPlan("migration-v1", source.ref, "iris-m05-core", source.schema_version, source.family, "iris-m05-core", "iris-m05-core-v2", (MigrationAction(MigrationActionKind.PRESERVE, "identity.signature", "identity.signature"),), IdentityContinuity.PRESERVE, AUTHORITY, POLICY)
        migrated = apply_migration(source, plan, new_revision_id="r2", new_revision_number=2)
        self.assertEqual(migrated.identity.dna_id, source.dna_id)
        self.assertTrue(verify_migration_receipt(migrated.receipt))

    def test_family_22_behavior(self):
        required = PackageDependency("required-motion", DependencyKind.REQUIRED_EXTERNAL_DNA, ref("m30", "motion.dna", "motion-a", revision_id="rev-5"))
        optional = PackageDependency("optional-brand", DependencyKind.OPTIONAL_EXTERNAL_DNA, ref("m46", "brand.dna", "brand-a"))
        manifest = package_manifest(revision(), dependencies=(required, optional))
        closure = resolve_dependency_closure(manifest, ())
        self.assertEqual(closure.missing_required_ids, ("required-motion",))
        self.assertEqual(closure.missing_optional_ids, ("optional-brand",))
        report = conform_package(manifest, (revision(),), ())
        self.assertFalse(report.valid)
        self.assertTrue(verify_package_conformance_report(report))

    def test_family_23_behavior(self):
        subject = revision()
        manifest = package_manifest(subject)
        projection = project_package_interface(manifest)
        contract = DNAMarketplaceContract(
            ref("m05", "reusable.package", manifest.package_id, version=manifest.version),
            subject.family,
            (),
            (),
            (ref("m53", "rights.clearance", "license"),),
            (PROVENANCE,),
            (ref("m54", "security.classification", "restricted"),),
        )
        self.assertEqual(projection.subject_ids, (subject.dna_id,))
        self.assertEqual(contract.rights_refs[0].owner_module, "m53")
        with self.assertRaises(DNAAdmissionError):
            DNAMarketplaceContract(contract.package_ref, subject.family, (), (), (POLICY,), (PROVENANCE,), contract.security_refs)

    def test_family_24_behavior(self):
        first = revision("dna-import", "r1", 1, traits=(trait("identity.signature", "A"),))
        incoming = revision("dna-import", "r2", 2, traits=(trait("identity.signature", "B"),), parent_revision_refs=(first.ref,))
        manifest = package_manifest(incoming, package_id="import-package")
        collisions = find_import_collisions(manifest, (envelope(first),))
        self.assertEqual(len(collisions), 1)
        conformance = conform_package(manifest, (incoming,), ())
        axes = tuple(CompatibilityAxisResult(axis, CompatibilityAxisState.EXACT, "pinned") for axis in REQUIRED_COMPATIBILITY_AXES)
        compatibility = DNACompatibilityProfile("import-compat", incoming.ref, ref("m34", "consumer.capability", "test"), axes)
        admission = create_import_admission(manifest, admission_id="import-1")
        admission = advance_import_admission(admission, ImportAdmissionState.VALIDATED, conformance=conformance, collision_findings=collisions, reason="format and schema passed")
        admission = advance_import_admission(admission, ImportAdmissionState.COMPATIBILITY_CHECKED, compatibility=compatibility, reason="compatibility axes passed")
        decisions = (ref("m53", "rights.decision", "allowed"), ref("m54", "security.decision", "allowed"))
        admission = advance_import_admission(admission, ImportAdmissionState.POLICY_CHECKED, external_policy_decision_refs=decisions, reason="external policies checked")
        admission = advance_import_admission(admission, ImportAdmissionState.ADMISSION_PROPOSED, authority_ref=AUTHORITY, admission_policy_ref=POLICY, reason="admission proposed")
        resolution = resolve_import_collision(collisions[0], outcome=ImportCollisionOutcome.SAME_IDENTITY_CONTINUATION, decision_ref=ref("m05", "import.collision.decision", "decision"), authority_ref=AUTHORITY, policy_ref=POLICY, evidence_refs=(EVIDENCE,))
        admission = advance_import_admission(admission, ImportAdmissionState.ADMITTED, collision_resolutions=(resolution,), authority_ref=AUTHORITY, admission_policy_ref=POLICY, reason="governed collision resolved")
        self.assertEqual(admission.state, ImportAdmissionState.ADMITTED)
        exact = find_import_collisions(package_manifest(first), (envelope(first),))[0]
        noop = resolve_import_collision(exact, outcome=ImportCollisionOutcome.EXACT_DUPLICATE_NOOP, decision_ref=ref("m05", "import.collision.decision", "noop"), authority_ref=AUTHORITY, policy_ref=POLICY, evidence_refs=(EVIDENCE,))
        self.assertEqual(noop.outcome, ImportCollisionOutcome.EXACT_DUPLICATE_NOOP)
        event = transition_package_lifecycle(PackageLifecycle.ACTIVE, PackageLifecycle.DEPRECATED, package_ref=manifest_ref(manifest), authority_ref=AUTHORITY, policy_ref=POLICY, reason="replacement available", replacement_refs=(ref("m05", "reusable.package", "replacement"),))
        self.assertEqual(event.next, PackageLifecycle.DEPRECATED)

    def test_family_25_behavior(self):
        target = ref("m05", "identity.subject", "dna-risk")
        findings = tuple(IdentityRiskFinding(f"risk-{index}", code, RiskSeverity.HIGH if index == 0 else RiskSeverity.LOW, target, (EVIDENCE,), f"boundary: {code.value}") for index, code in enumerate(IDENTITY_RISK_CODES))
        report = build_identity_risk_report(findings)
        self.assertTrue(report.has_high_or_critical)
        self.assertEqual({item.code for item in report.findings}, set(RiskCode))


def manifest_ref(manifest):
    return ref("m05", "reusable.package", manifest.package_id, version=manifest.version)


if __name__ == "__main__":
    unittest.main()
