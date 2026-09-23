from __future__ import annotations

import ast
import unittest
from pathlib import Path

import iris_asset_dna as m05
from iris_asset_dna.anchors import DNAProjectionContract
from iris_asset_dna.ports import PORT_BY_NAME, validate_port_catalog
from iris_asset_dna.readiness import DNAReadinessAssessment
from iris_asset_dna.enums import ReadinessState


class TestM05AuthorityPorts(unittest.TestCase):
    def test_frozen_authorities_map_to_versioned_non_executable_ports(self):
        validate_port_catalog()
        self.assertEqual(PORT_BY_NAME["QualityRepairProposalPort"].owner_modules, ("m01", "m48", "m49", "m50", "m51"))
        self.assertEqual(PORT_BY_NAME["ProductionStateRefPort"].owner_modules, ("m02", "m06"))
        self.assertEqual(PORT_BY_NAME["ConcreteWorkflowIdentityProjectionPort"].owner_modules, ("m16", "m17"))
        self.assertEqual(PORT_BY_NAME["MotionDNARefPort"].owner_modules, ("m30",))
        self.assertEqual(PORT_BY_NAME["TemporalContinuityEvidencePort"].owner_modules, ("m36", "m37", "m38"))
        self.assertEqual(PORT_BY_NAME["DigitalHumanPersonaBindingPort"].owner_modules, ("m39",))
        self.assertEqual(PORT_BY_NAME["VoiceMusicAudioDomainDNAPort"].owner_modules, ("m40", "m41", "m42"))
        self.assertEqual(PORT_BY_NAME["CanonContentCampaignBrandPort"].owner_modules, ("m43", "m44", "m45", "m46"))
        self.assertEqual(PORT_BY_NAME["HIVEMemoryIdentitySlicePort"].owner_modules, ("m52",))
        self.assertEqual(PORT_BY_NAME["RightsSecurityEvidencePort"].owner_modules, ("m53", "m54"))
        self.assertEqual(PORT_BY_NAME["StorageObservabilityAutomationPort"].owner_modules, ("m55", "m56", "m57"))
        self.assertEqual(PORT_BY_NAME["APIExportRecoveryIdentityPort"].owner_modules, ("m58", "m59", "m60"))
        self.assertTrue(all("does not execute" in port.authority_rule for port in m05.DEFAULT_PORTS))

    def test_quality_and_release_authority_are_not_m05_readiness(self):
        assessment = DNAReadinessAssessment(ReadinessState.READY, "a" * 64, ())
        self.assertFalse(assessment.quality_or_release_authority)
        self.assertEqual(assessment.authority_scope, "M05_SEMANTIC_CONFORMANCE_ONLY")
        self.assertFalse(any("promotion" in item.lower() for item in assessment.finding_codes))

    def test_m04_and_provider_refs_remain_external_pinned_inputs(self):
        projection = DNAProjectionContract("projection", m05.DNARevisionRef("dna-subject", "r1", "a" * 64), ("identity.signature",), preserved_trait_paths=("identity.signature",))
        self.assertEqual(projection.projection_owner, "m04")
        self.assertEqual(PORT_BY_NAME["ConcreteWorkflowIdentityProjectionPort"].authority_rule, m05.DEFAULT_PORTS[4].authority_rule)
        self.assertFalse(any(hasattr(port, method) for port in m05.DEFAULT_PORTS for method in ("execute", "compile_workflow", "invoke_provider")))

    def test_kernel_does_not_import_authority_neighbor_implementations(self):
        root = Path(m05.__file__).resolve().parent
        forbidden_roots = {"iris_quality", "iris_project_os", "iris_intent", "iris_multimodal_ir"}
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split(".", 1)[0], forbidden_roots, (path.name, alias.name))
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    root_name = (node.module or "").split(".", 1)[0]
                    self.assertNotIn(root_name, forbidden_roots, (path.name, node.module))
        self.assertIn("m16", PORT_BY_NAME["ConcreteWorkflowIdentityProjectionPort"].owner_modules)


if __name__ == "__main__":
    unittest.main()
