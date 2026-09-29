"""No retired provider identifiers remain in current public module interfaces."""
from __future__ import annotations

import unittest

from scripts.audit_retired_context import RETIRED_PATTERN, RETIRED_WORD
from iris_asset_dna import ports as dna_ports
from iris_production_state import ports as state_ports
from iris_intent.identity import SourceKind
from iris_project_os.identity import EntityKind


class StandalonePublicAbiTests(unittest.TestCase):
    def test_01_no_old_public_extension_port_names(self):
        for module in (dna_ports, state_ports):
            with self.subTest(module=module.__name__):
                self.assertEqual([name for name in dir(module)
                                  if RETIRED_PATTERN.search(name)], [])
        self.assertTrue(hasattr(dna_ports, "ProjectMemoryIdentitySlicePort"))
        self.assertTrue(hasattr(state_ports, "ProjectContextEvidencePort"))

    def test_02_only_neutral_current_memory_source_kind(self):
        self.assertEqual(SourceKind.PROJECT_MEMORY.value, "PROJECT_MEMORY")
        self.assertFalse(any(RETIRED_PATTERN.search(item.name)
                             or RETIRED_PATTERN.search(item.value)
                             for item in SourceKind))

    def test_03_only_neutral_current_context_entity_kind(self):
        self.assertEqual(EntityKind.PROJECT_CONTEXT.value, "PROJECT_CONTEXT")
        self.assertFalse(any(RETIRED_PATTERN.search(item.name)
                             or RETIRED_PATTERN.search(item.value)
                             for item in EntityKind))

    def test_04_old_serialized_category_is_not_silently_recognized(self):
        old_tag = RETIRED_WORD.upper() + "_MEMORY"
        self.assertNotIn(old_tag, {item.value for item in SourceKind})


if __name__ == "__main__":
    unittest.main()
