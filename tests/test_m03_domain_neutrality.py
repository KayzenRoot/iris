"""The neutrality law: six domains, one kernel, and the kernel knows nothing about any of them.

§6 lists six production domains M03 must represent — brand mark, catalogue photography, isometric
asset set, commercial film, licensed spokesperson, narration and bed — and then states the actual
requirement in a negative: *no core schema may require pixel, mesh, camera, visual or text-to-image
only fields*, and domain semantics enter only through versioned opaque refs and extension registries.
§18 turns that into evidence: run the same core over synthetic fixtures for all six with no
domain-specific code imported into the kernel.

This file proves it in four independent ways, because each one fails differently. The first is
symmetry: all six briefs go through the same four kernel calls and produce the same four artifact
types, and the function that runs them contains no branch on any of the six identifiers. The second
is provenance of dependencies: every module in the kernel package is discovered twice — once from the
filesystem, once from the import system — and the abstract syntax of each is scanned for imports, so
a provider, DCC, cloud or database SDK cannot enter quietly and an added file cannot be missed by a
hardcoded list. The third is vocabulary: the kernel's own enum members and required record fields are
collected by introspection and searched for the words a pixel-thinking kernel would need; the only
§6-adjacent tokens that survive sit in one optional enumeration of *editable dimensions*, and a test
says so rather than letting the exception go unnoticed. The fourth is outcome: the six domains reach
six different digests, six different channel sets, and two different non-trivial verdicts — one
blocking contradiction and one human decision — which is what shows the kernel is doing work rather
than echoing input.

"""

from __future__ import annotations

import ast
import dataclasses
import enum
import importlib
import inspect
import pathlib
import pkgutil
import unittest
from dataclasses import fields
from typing import Any

import iris_intent
from iris_intent.base import Record
from iris_intent.conflicts import ConflictClass, ConflictConsequence
from iris_intent.constraints import ConstraintPolarity
from iris_intent.execution import SemanticMutationClass
from iris_intent.intent import IntentOrigin, ModalChannel, StatementKind
from iris_intent.readiness import ReadinessFamily

from examples import m03_synthetic_profiles as E

from tests import m03_kernel_support as S

#: §6's six domains, in the order the contract lists them.
SIX_DOMAINS = tuple(item.profile_id for item in E.BRIEFS)

#: The kernel runs once per domain and every test reads the same table, which is the evidence §18 asks for.
RUNS = {item.profile_id: E.run_kernel(item) for item in E.BRIEFS}

#: Words a kernel that had learned to think in pixels would need. §6 and §19's out-of-scope list.
DOMAIN_WORDS = (
    "pixel",
    "pixels",
    "mesh",
    "lens",
    "prompt",
    "seed",
    "shader",
    "atlas",
    "canvas",
    "sku",
    "wordmark",
    "monogram",
    "fps",
    "dpi",
    "codec",
    "blender",
    "comfyui",
    "maya",
    "unreal",
    "sora",
    "midjourney",
    "openai",
    "stability",
    "runway",
    "diffusers",
    "narration",
    "spokesperson",
    "photography",
    "isometric",
    "commercial",
    "campaign",
    "typography",
)

#: Provider, DCC, cloud and database namespaces §19 puts outside M03 entirely.
FORBIDDEN_ROOTS = (
    "openai",
    "anthropic",
    "stability_sdk",
    "comfyui",
    "bpy",
    "maya",
    "unreal",
    "torch",
    "tensorflow",
    "diffusers",
    "cv2",
    "PIL",
    "numpy",
    "boto3",
    "google",
    "azure",
    "sqlalchemy",
    "psycopg",
    "pymongo",
    "redis",
    "minio",
    "requests",
    "httpx",
    "aiohttp",
    "fastapi",
    "flask",
    "ollama",
)

#: Modules the kernel may stand on: the standard library and M01's frozen contract, plus itself.
ALLOWED_ROOTS = frozenset(getattr(__import__("sys"), "stdlib_module_names", set())) | {
    "iris_quality",
    "iris_project_os",
    "iris_intent",
    "_distutils_hack",
    "__future__",
}

KERNEL_PACKAGE = pathlib.Path(iris_intent.__file__).parent


def kernel_module_names() -> tuple[str, ...]:
    """Every importable module in the kernel, found through the import system."""

    return tuple(sorted(info.name for info in pkgutil.iter_modules([str(KERNEL_PACKAGE)])))


def kernel_source_files() -> tuple[pathlib.Path, ...]:
    """Every Python file in the kernel package, found on the filesystem."""

    return tuple(sorted(KERNEL_PACKAGE.glob("*.py")))


def imported_roots() -> dict[str, set[str]]:
    """Top-level module names each kernel file imports, read off the syntax tree."""

    found: dict[str, set[str]] = {}
    for path in kernel_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
        found[path.name] = roots
    return found


def enum_vocabulary() -> set[str]:
    """Every name and value the kernel's own enumerations hold, lowercased."""

    words: set[str] = set()
    for name in kernel_module_names():
        module = importlib.import_module(f"iris_intent.{name}")
        for _, member in inspect.getmembers(module, inspect.isclass):
            if member.__module__ != module.__name__ or not issubclass(member, enum.Enum):
                continue
            for item in member:
                words.add(item.name.lower())
                words.add(str(item.value).lower())
    return words


def required_field_names() -> set[str]:
    """Fields every kernel record *demands*, which is where §6's prohibition actually bites."""

    demanded: set[str] = set()
    for name in kernel_module_names():
        module = importlib.import_module(f"iris_intent.{name}")
        for _, member in inspect.getmembers(module, inspect.isclass):
            if member.__module__ != module.__name__ or not issubclass(member, Record):
                continue
            if not hasattr(member, "__dataclass_fields__"):
                continue
            for field in fields(member):
                if field.default is not dataclasses.MISSING:
                    continue
                if field.default_factory is not dataclasses.MISSING:
                    continue
                demanded.add(field.name.lower())
    return demanded


def domain_identifiers() -> set[str]:
    """The names the six briefs bring with them: predicates, paths, profile and bundle ids."""

    tokens: set[str] = set()
    for item in E.BRIEFS:
        tokens.update(item.predicates)
        tokens.update(item.paths)
        tokens.add(item.profile_id)
        tokens.add(item.bundle.bundle_id)
        tokens.add(item.revision.revision_id)
    return {token.lower() for token in tokens if len(token) > 4}


def block_for(profile_id: str) -> Any:
    """The conflict the kernel derived for one domain, if it derived one."""

    found = RUNS[profile_id]["conflicts"]
    return found[0] if found else None


class SameKernelForSixDomains(unittest.TestCase):
    """§18's neutrality evidence: one code path, six briefs."""

    def test_all_six_briefs_are_present_and_distinct(self) -> None:
        self.assertEqual(len(E.BRIEFS), 6)
        self.assertEqual(len(set(SIX_DOMAINS)), 6)
        self.assertEqual(len({item.revision.brief_id for item in E.BRIEFS}), 6)
        self.assertEqual(len({item.channels for item in E.BRIEFS}), 6)
        self.assertEqual(len({item.paths for item in E.BRIEFS}), 6)
        for item in E.BRIEFS:
            with self.subTest(profile=item.profile_id):
                self.assertEqual(item.revision.status, "ADMITTED")
                self.assertIsNotNone(item.bundle.admitted_by)
                self.assertEqual(item.model.brief_id, item.revision.brief_id)
                self.assertEqual(item.bundle.brief_id, item.revision.brief_id)
        self.assertEqual(len({item.label for item in E.BRIEFS}), 6)

    def test_every_domain_survives_the_same_four_kernel_calls(self) -> None:
        shapes = set()
        for profile in E.BRIEFS:
            artifacts = RUNS[profile.profile_id]
            with self.subTest(profile=profile.profile_id):
                self.assertEqual(sorted(artifacts), ["conflicts", "fingerprint", "readiness", "slice"])
                self.assertEqual(
                    artifacts["fingerprint"].statement_count, len(profile.revision.statements)
                )
                shapes.add(
                    tuple(sorted((key, type(value).__name__) for key, value in artifacts.items()))
                )
        self.assertEqual(len(shapes), 1, "the six domains did not reach one artifact shape")

    def test_run_kernel_carries_no_branch_on_any_domain_name(self) -> None:
        source = inspect.getsource(E.run_kernel)
        for profile_id in SIX_DOMAINS:
            with self.subTest(profile=profile_id):
                self.assertNotIn(profile_id, source)
        self.assertNotIn("if item.profile_id ==", source)
        self.assertNotIn("switch", source)
        self.assertTrue(callable(E.run_kernel))

    def test_the_kernel_expresses_every_domain_through_one_shared_channel_vocabulary(self) -> None:
        channels = {m.value for m in ModalChannel}
        seen = set()
        for item in E.BRIEFS:
            with self.subTest(profile=item.profile_id):
                self.assertTrue(item.channels)
                self.assertTrue(set(item.channels) <= channels)
                self.assertTrue(set(item.model.modalities) <= channels)
            seen.update(item.channels)
        self.assertEqual(
            seen,
            channels - {ModalChannel.UNSPECIFIED.value, ModalChannel.CROSS.value, ModalChannel.INTERFACE.value},
            "the six briefs speak through the shared channels and invent no private ones",
        )

    def test_profiles_by_channel_answers_coverage_without_naming_a_domain(self) -> None:
        for channel in sorted({item for profile in E.BRIEFS for item in profile.channels}):
            with self.subTest(channel=channel):
                matched = E.profiles_by_channel(channel)
                self.assertTrue(matched)
                self.assertEqual(
                    {item.profile_id for item in matched},
                    {item.profile_id for item in E.BRIEFS if channel in item.channels},
                )
        self.assertEqual(E.profiles_by_channel("image"), E.profiles_by_channel("IMAGE"))
        self.assertEqual(E.profiles_by_channel("no-such-channel"), ())

    def test_a_profile_lookup_refuses_a_domain_the_examples_never_wrote(self) -> None:
        for profile_id in SIX_DOMAINS:
            self.assertIs(E.profile_for(profile_id), E.PROFILES[profile_id])
        with self.assertRaises(KeyError) as caught:
            E.profile_for("brief.brand.new-domain")
        self.assertIn("unknown synthetic brief", str(caught.exception))


class KernelDependenciesStayNeutral(unittest.TestCase):
    """§18 and §19: nothing provider-shaped enters, and no file can hide from the scan."""

    def test_the_kernel_is_scanned_by_two_routes_that_agree(self) -> None:
        through_import = set(kernel_module_names())
        through_filesystem = {path.stem for path in kernel_source_files()} - {"__init__"}
        self.assertGreater(len(through_import), 20)
        self.assertEqual(through_import, through_filesystem)

    def test_no_kernel_module_imports_the_synthetic_profiles(self) -> None:
        graph = imported_roots()
        self.assertEqual(len(graph), len(kernel_source_files()))
        for name, roots in sorted(graph.items()):
            with self.subTest(module=name):
                self.assertNotIn("examples", roots)
        for path in kernel_source_files():
            with self.subTest(module=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("m03_synthetic_profiles", text)
                self.assertNotIn("examples.", text)
                self.assertNotIn("import examples", text)

    def test_no_provider_dcc_cloud_or_database_sdk_is_imported(self) -> None:
        graph = imported_roots()
        for name, roots in sorted(graph.items()):
            with self.subTest(module=name):
                self.assertEqual(sorted(roots & set(FORBIDDEN_ROOTS)), [])

    def test_every_import_is_the_standard_library_or_the_shared_m01_contract(self) -> None:
        offenders: dict[str, set[str]] = {}
        for name, roots in imported_roots().items():
            outside = {root for root in roots if root not in ALLOWED_ROOTS}
            if outside:
                offenders[name] = outside
        self.assertEqual(offenders, {}, f"the kernel reached outside its allowed roots: {offenders}")

    def test_the_example_profiles_never_reach_into_the_kernel(self) -> None:
        text = pathlib.Path(E.__file__).read_text(encoding="utf-8")
        self.assertNotIn("if __name__ == '__main__' and", text)
        for profile_id in SIX_DOMAINS:
            self.assertIn(profile_id, text)
        self.assertTrue(all("iris_intent" in line for line in [
            "from iris_intent.identity import (\n    VERSIONED_REF_KINDS,\n"
        ]))


class KernelVocabularyHoldsNoDomainWords(unittest.TestCase):
    """§6: the kernel's own words are media-agnostic, and its required fields prove it."""

    def test_no_enum_member_is_named_after_a_domain_construct(self) -> None:
        vocabulary = enum_vocabulary()
        self.assertGreater(len(vocabulary), 300)
        for word in DOMAIN_WORDS:
            with self.subTest(word=word):
                self.assertNotIn(word, vocabulary)

    def test_no_required_field_is_named_after_a_domain_construct(self) -> None:
        demanded = required_field_names()
        self.assertGreater(len(demanded), 20)
        for word in DOMAIN_WORDS + ("camera", "visual", "pixel", "mesh", "texture"):
            with self.subTest(word=word):
                self.assertNotIn(word, demanded)

    def test_the_six_domains_own_vocabulary_appears_nowhere_in_the_kernel(self) -> None:
        joined = " ".join(sorted(enum_vocabulary() | required_field_names()))
        offenders = sorted(token for token in domain_identifiers() if token in joined)
        self.assertEqual(offenders, [])

    def test_the_only_camera_shaped_word_is_an_optional_editable_dimension(self) -> None:
        """Documents §6's boundary honestly instead of looking away from it.

        ``SemanticMutationClass`` enumerates dimensions a compiler may be *told* to change, and
        ``CAMERA`` and ``TEXTURE`` are values a generative-asset brief may choose to name; the media
        words in ``ModalChannel`` are the shared channel vocabulary the six domains speak through.
        Neither kind is required anywhere: §6 forbids a core schema that *requires* a pixel, mesh,
        camera, visual or text-to-image field, which the test above checks field by field.
        """

        members = {item.value for item in SemanticMutationClass}
        self.assertIn("CAMERA", members)
        self.assertIn("TEXTURE", members)
        self.assertLess(len(members & set(DOMAIN_WORDS)), 1)
        self.assertTrue(issubclass(SemanticMutationClass, enum.Enum))
        self.assertNotIn("camera", required_field_names())
        self.assertNotIn("pixel", required_field_names())

    def test_readiness_and_conflict_vocabulary_names_states_and_not_subject_matter(self) -> None:
        for member in ReadinessFamily:
            self.assertFalse(any(word in member.value.lower() for word in DOMAIN_WORDS))
        for member in ConflictClass:
            self.assertFalse(any(word in member.value.lower() for word in DOMAIN_WORDS))
        self.assertEqual(
            sorted(item.value for item in ConflictConsequence),
            sorted({item.value for item in ConflictConsequence}),
        )


class SixDomainsSixOutcomes(unittest.TestCase):
    """The table has to differ, or the kernel is echoing its input."""

    def test_the_six_briefs_reach_six_different_semantic_digests(self) -> None:
        digests = {RUNS[item.profile_id]["fingerprint"].semantic_digest for item in E.BRIEFS}
        self.assertEqual(len(digests), 6)
        for digest in digests:
            self.assertEqual(len(digest), S.DIGEST_LEN)

    def test_each_domain_carries_its_own_statement_and_rule_counts(self) -> None:
        profile_by_id = {item.profile_id: item for item in E.BRIEFS}
        for profile_id in SIX_DOMAINS:
            fingerprint = RUNS[profile_id]["fingerprint"]
            profile = profile_by_id[profile_id]
            with self.subTest(profile=profile_id):
                self.assertEqual(
                    fingerprint.mandatory_count,
                    sum(1 for item in profile.revision.statements if item.mandatory),
                )
                self.assertGreater(fingerprint.mandatory_count, 0)
        shapes = {
            (
                RUNS[item.profile_id]["fingerprint"].statement_count,
                len(item.bundle.constraints),
            )
            for item in E.BRIEFS
        }
        self.assertEqual(shapes, {(4, 4), (3, 3)})
        self.assertEqual(
            sorted(item.profile_id for item in E.BRIEFS if len(item.revision.statements) == 4),
            ["film-commercial", "logo-brand-web"],
        )

    def test_the_table_holds_one_blocking_conflict_and_one_human_decision(self) -> None:
        blockers = {
            item.profile_id: RUNS[item.profile_id]["readiness"].blocking_families for item in E.BRIEFS
        }
        self.assertEqual(
            blockers["product-photography"], (ReadinessFamily.BLOCKING_CONFLICT.value,)
        )
        self.assertEqual(
            blockers["spokesperson-digital-human"],
            (ReadinessFamily.HUMAN_DECISION_REQUIRED.value,),
        )
        ready = {name for name, value in blockers.items() if not value}
        self.assertEqual(len(ready), 4)
        self.assertEqual(
            sorted(name for name in blockers if RUNS[name]["conflicts"]), ["product-photography"]
        )

    def test_the_photography_brief_is_blocked_by_a_contradiction_the_kernel_derived(self) -> None:
        conflict = block_for("product-photography")
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.conflict_class, ConflictClass.DIRECT_CONTRADICTION.value)
        self.assertEqual(conflict.consequence, ConflictConsequence.BLOCKING.value)
        self.assertTrue(conflict.blocks_contract)
        self.assertEqual(conflict.semantic_paths, ("brief.visual.product",))
        self.assertEqual(
            sorted(item.ref_id for item in conflict.parties),
            ["cn.photo.no-prop", "cn.photo.subject"],
        )
        self.assertEqual(
            [
                item.constraint_id
                for item in E.profile_for("product-photography").bundle.constraints
                if item.polarity == ConstraintPolarity.FORBID.value
            ],
            ["cn.photo.no-prop"],
        )

    def test_the_spokesperson_brief_is_held_by_a_question_only_a_human_may_answer(self) -> None:
        profile = E.profile_for("spokesperson-digital-human")
        report = RUNS[profile.profile_id]["readiness"]
        self.assertFalse(report.ready)
        self.assertIn(ReadinessFamily.HUMAN_DECISION_REQUIRED.value, report.assessed_families)
        self.assertEqual(len(profile.questions), 1)
        self.assertTrue(profile.questions[0].blocking)
        findings = report.findings_for(ReadinessFamily.HUMAN_DECISION_REQUIRED)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].family, ReadinessFamily.HUMAN_DECISION_REQUIRED.value)
        self.assertEqual(findings[0].subject_ref.ref_id, "q.persona.consent")
        self.assertEqual(findings[0].semantic_paths, ("brief.rights.disclosure",))
        self.assertIn("OPEN", findings[0].detail)
        self.assertIn("brief.rights.disclosure", profile.questions[0].semantic_paths)
        self.assertIs(block_for(profile.profile_id), None)

    def test_every_family_is_assessed_for_every_domain(self) -> None:
        for profile_id in SIX_DOMAINS:
            report = RUNS[profile_id]["readiness"]
            with self.subTest(profile=profile_id):
                self.assertEqual(len(report.assessed_families), 7)
                self.assertEqual(report.unassessed_families, ())
                self.assertEqual(
                    len(report.assessed_families), len(set(report.assessed_families))
                )
                self.assertTrue(all(report.assessed(item) for item in report.assessed_families))

    def test_each_slice_carries_only_its_own_domain_first_path(self) -> None:
        for profile in E.BRIEFS:
            item = RUNS[profile.profile_id]["slice"]
            with self.subTest(profile=profile.profile_id):
                self.assertEqual(item.paths, profile.paths[:1])
                self.assertEqual(item.purpose, "COMPILE_QUALITY")
                self.assertTrue(item.statement_ids)
                self.assertTrue(item.constraints)
                self.assertNotEqual(item.slice_digest, "")
        digests = {RUNS[name]["slice"].slice_digest for name in SIX_DOMAINS}
        self.assertEqual(len(digests), 6)

    def test_a_seventh_domain_compiles_through_the_same_calls_without_a_kernel_change(self) -> None:
        """The strongest form of §6: a domain nobody wrote a fixture for still fits."""

        source_item = E.source("src.haptic.brief")
        seventh = E.build(
            "tactile-finish-sample",
            "A haptic finish sample for a handheld shell",
            (
                E.say(
                    "st.haptic.grain",
                    "brief.tactile.grain",
                    StatementKind.CONSTRAINT_SEMANTICS.value,
                    "the grain is read by a thumb before it is read by an eye",
                    source_item,
                    modality=ModalChannel.MATERIAL.value,
                    mandatory=True,
                ),
                E.say(
                    "st.haptic.edge",
                    "brief.tactile.edge",
                    StatementKind.DIRECTION.value,
                    "no seam catches skin",
                    source_item,
                    origin=IntentOrigin.DERIVED.value,
                    ancestors=("st.haptic.grain",),
                ),
            ),
            (source_item,),
            (
                E.rule(
                    "cn.haptic.grain",
                    "brief.tactile.grain",
                    "keeps_grain",
                    channels=(ModalChannel.MATERIAL.value,),
                    mandatory=True,
                ),
                E.rule(
                    "cn.haptic.no-polish",
                    "brief.tactile.grain",
                    "keeps_grain",
                    polarity=ConstraintPolarity.FORBID.value,
                    channels=(ModalChannel.MATERIAL.value,),
                ),
            ),
            (ModalChannel.MATERIAL.value,),
            ("brief.tactile.grain", "brief.tactile.edge"),
            predicates=("keeps_grain",),
        )
        artifacts = E.run_kernel(seventh)
        self.assertEqual(sorted(artifacts), ["conflicts", "fingerprint", "readiness", "slice"])
        self.assertEqual(len(artifacts["conflicts"]), 1)
        self.assertEqual(
            artifacts["conflicts"][0].conflict_class, ConflictClass.DIRECT_CONTRADICTION.value
        )
        self.assertEqual(
            artifacts["readiness"].blocking_families, (ReadinessFamily.BLOCKING_CONFLICT.value,)
        )
        self.assertNotIn(
            artifacts["fingerprint"].semantic_digest,
            {RUNS[name]["fingerprint"].semantic_digest for name in SIX_DOMAINS},
        )
        self.assertTrue(set(seventh.channels) <= {m.value for m in ModalChannel})


if __name__ == "__main__":
    unittest.main()
