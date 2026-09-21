"""Proofs that the M02 kernel stays domain-neutral, provider-free and M01-supervised.

Three separate claims live here, because each one fails in a different way.

*No provider in the core.* Real renderers, DCCs, clouds and databases reach M02 only through
the ports in :mod:`iris_project_os.ports`. The moment a kernel module imports one of them, the
kernel has chosen a provider for every downstream project.

*M01 stays the quality authority.* M02 may read the quality ladder and check a decision's
reference; it must never evaluate, judge, register an evaluator or define a dimension. Those
are M01's, and a kernel that re-decides quality is a second authority nobody audits.

*The five synthetic profiles are fixtures, not features.* Every domain word in this repository
belongs to :mod:`examples.m02_synthetic_profiles`. The assertions below are driven by that
module's own identifiers, so a profile renamed into the kernel is caught without anyone
maintaining a list of words to forbid.
"""

from __future__ import annotations

import ast
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from typing import Iterator

import iris_project_os
from iris_project_os.diffing import semantic_diff
from iris_project_os.serialization import dumps
from iris_project_os.snapshots import SnapshotClass, closure_obligations
from tests.m02_kernel_support import bound, closure, snapshot

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "iris_project_os"
FIXTURES = ROOT / "examples" / "m02_synthetic_profiles.py"

FORBIDDEN_ROOTS = (
    # DCC and media engines
    "blender",
    "bpy",
    "maya",
    "cmds",
    "houdini",
    "nuke",
    "substance",
    "unreal",
    "unity",
    "godot",
    # inference and rendering backends
    "comfyui",
    "comfy",
    "dreamsim",
    "flip",
    "pytorch_flip",
    "webgpu",
    "gpu",
    "vulkan",
    "cuda",
    "torch",
    "torchvision",
    "tensorflow",
    "jax",
    "onnx",
    "onnxruntime",
    "transformers",
    "huggingface_hub",
    "clip",
    "openai",
    "anthropic",
    "ollama",
    "replicate",
    # numeric and imaging libraries
    "numpy",
    "scipy",
    "PIL",
    "cv2",
    "trimesh",
    "shapely",
    "skimage",
    # transport, storage and cloud
    "requests",
    "httpx",
    "urllib3",
    "aiohttp",
    "websocket",
    "boto3",
    "botocore",
    "google",
    "azure",
    "cloudflare",
    "sqlalchemy",
    "psycopg",
    "psycopg2",
    "sqlite3",
    "mysql",
    "pymongo",
    "redis",
    "pymysql",
    "elasticsearch",
    "minio",
    "docker",
    "kubernetes",
    # governance and agent runtimes the kernel must not call into
    "hive",
    "mcp",
)

QUALITY_AUTHORITY = ("contracts", "decision", "errors", "versions")

NOT_QUALITY_AUTHORITY = (
    "dimensions",
    "evidence",
    "judging",
    "registry",
    "zones",
)

FORBIDDEN_QUALITY_VOCABULARY = (
    "DecisionEngine",
    "DomainProfile",
    "EvaluatorRegistry",
    "JudgeRequest",
    "JudgeResult",
    "DimensionRegistry",
    "SemanticZone",
)

NETWORK_TOUCHPOINTS = (
    ("socket", "socket"),
    ("socket", "create_connection"),
    ("subprocess", "run"),
    ("os", "system"),
)

EXTERNAL_ASIDE = ("blender", "comfyui", "dreamsim", "webgpu", "isometric", "prores")


def kernel_modules() -> Iterator[Path]:
    return sorted(KERNEL.glob("*.py"))


def kernel_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in kernel_modules())


def parsed(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def absolute_imports(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def import_roots(tree: ast.AST) -> set[str]:
    return {name.split(".", 1)[0] for name in absolute_imports(tree)}


def call_names(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                found.add(f"{target.value.id}.{target.attr}")
            elif isinstance(target, ast.Name):
                found.add(target.id)
    return found


IMMUTABLE_ANNOTATIONS = ("Mapping", "Sequence", "Tuple", "FrozenSet", "frozenset", "tuple", "AbstractSet")
MUTABLE_ANNOTATIONS = ("dict", "list", "set", "Dict", "List", "Set", "MutableMapping", "MutableSequence", "DefaultDict")


def _annotation_root(node_value: ast.AST | None) -> str:
    if isinstance(node_value, ast.Subscript):
        return _annotation_root(node_value.value)
    if isinstance(node_value, ast.Name):
        return node_value.id
    if isinstance(node_value, ast.Attribute):
        return node_value.attr
    return ""


class ImportBoundaryTests(TestCase):
    """The kernel is stdlib plus the M01 package it borrows vocabulary from, and nothing else."""

    def test_the_kernel_directory_exists_and_is_populated(self) -> None:
        modules = list(kernel_modules())
        self.assertGreaterEqual(len(modules), 20)
        self.assertTrue((KERNEL / "__init__.py").is_file())

    def test_every_kernel_import_is_standard_library_or_m01(self) -> None:
        allowed = set(sys.stdlib_module_names) | {"iris_project_os", "iris_quality"}
        for path in kernel_modules():
            with self.subTest(module=path.name):
                roots = import_roots(parsed(path))
                self.assertLessEqual(roots, allowed, f"{path.name} leaves the kernel's two legal roots")

    def test_the_kernel_never_imports_a_fixture_or_a_test(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                roots = import_roots(parsed(path))
                self.assertEqual(roots & {"examples", "tests", "docs", "scripts"}, set())

    def test_no_provider_dcc_cloud_or_database_sdk_is_imported(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                roots = import_roots(parsed(path))
                self.assertEqual(roots & set(FORBIDDEN_ROOTS), set(), f"{path.name} chose a provider")

    def test_the_kernel_never_reaches_for_the_network_or_a_shell(self) -> None:
        blocked = {f"{owner}.{name}" for owner, name in NETWORK_TOUCHPOINTS}
        for path in kernel_modules():
            with self.subTest(module=path.name):
                calls = call_names(parsed(path))
                self.assertEqual(calls & blocked, set())

    def test_the_kernel_declares_no_module_level_mutable_authority(self) -> None:
        """§12's "no global mutable semantic authority registries": a shared dict is a hidden database.

        A bare ``={}``/``=[]``/``=set()`` at module scope — or the same thing wearing a mutable
        annotation — is the one shape that lets two callers mutate the same state without either
        asking for it, so the surface is checked rather than trusted. A lookup table the kernel
        genuinely freezes is written ``X: Mapping[...] = {...}`` and is allowed; nothing the kernel
        hands out is a mutable singleton.
        """

        for path in kernel_modules():
            with self.subTest(module=path.name):
                tree = parsed(path)
                if not isinstance(tree, ast.Module):
                    continue
                for statement in tree.body:
                    if isinstance(statement, ast.Assign):
                        targets, value, annotation = statement.targets, statement.value, None
                    elif isinstance(statement, ast.AnnAssign):
                        targets, value, annotation = [statement.target], statement.value, statement.annotation
                    else:
                        continue
                    if value is None or not isinstance(value, (ast.Dict, ast.List, ast.Set)):
                        continue
                    if annotation is not None and _annotation_root(annotation) in IMMUTABLE_ANNOTATIONS:
                        continue
                    for target in targets:
                        if not isinstance(target, ast.Name) or target.id.startswith("_"):
                            continue
                        self.fail(f"{path.name} binds a mutable module-level {target.id}")

    def test_the_public_surface_is_the_kernel_alone(self) -> None:
        self.assertGreaterEqual(len(iris_project_os.__all__), 200)
        for name in iris_project_os.__all__:
            with self.subTest(symbol=name):
                self.assertTrue(hasattr(iris_project_os, name), f"{name} is exported but absent")


class QualityAuthorityTests(TestCase):
    """M01 decides quality. M02 may name a decision, never make one."""

    def test_the_kernel_imports_only_m01s_borrowed_vocabulary(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                foreign = {
                    name.split(".", 1)[1]
                    for name in absolute_imports(parsed(path))
                    if name.startswith("iris_quality.")
                }
                self.assertLessEqual(foreign, set(QUALITY_AUTHORITY))

    def test_the_kernel_never_imports_the_judging_machinery(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                foreign = {
                    name.split(".", 1)[1]
                    for name in absolute_imports(parsed(path))
                    if name.startswith("iris_quality.")
                }
                self.assertEqual(foreign & set(NOT_QUALITY_AUTHORITY), set())

    def test_the_kernel_never_names_a_quality_authority_symbol(self) -> None:
        text = kernel_text()
        for name in FORBIDDEN_QUALITY_VOCABULARY:
            self.assertNotIn(name, text, f"the kernel reaches for M01's {name}")

    def test_the_kernel_takes_the_quality_ladder_from_m01(self) -> None:
        """A ladder defined twice is two ladders. M02 must borrow the one object M01 owns."""

        from iris_quality.contracts import QualityClass as Foreign
        from iris_project_os.versions import QualityClass as Borrowed

        self.assertIs(Foreign, Borrowed)

    def test_a_m02_claim_of_quality_names_an_m01_decision_it_does_not_author(self) -> None:
        """A MATERIALIZED closure may be unjudged; a VALIDATED one has to point at decisions.

        The kernel's side of the bargain is a reference it can check, never a score it computed,
        so this asserts the gate exists without pretending M02 judged anything.
        """

        first = snapshot(production_id="p.judged", klass=SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertTrue(first.closure.quality_decisions)

        unjudged = closure(production_id="p.unjudged", graph=bound())
        obligations = closure_obligations(unjudged, SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertTrue(
            any("decision" in item.lower() for item in obligations),
            obligations,
        )


class DomainVocabularyTests(TestCase):
    """Nothing in the core knows the five synthetic domains."""

    def test_the_kernel_never_names_a_synthetic_profile(self) -> None:
        from examples import m02_synthetic_profiles as profiles

        text = kernel_text()
        for fixture in profiles.PROFILES.values():
            with self.subTest(profile=fixture.profile_id):
                for token in (
                    fixture.profile_id,
                    fixture.graph_id,
                    fixture.project_id,
                    fixture.production_id,
                    fixture.branch_id,
                    *fixture.node_ids,
                    *(item.variant_set_id for item in fixture.variant_sets),
                    *(item.constraint_id for item in fixture.variant_constraints),
                    *(item.anchor_id for item in fixture.identity_anchors),
                ):
                    self.assertNotIn(token, text, f"the kernel hardcodes {token!r}")

    def test_the_kernel_never_names_an_external_engine(self) -> None:
        text = kernel_text().lower()
        for token in EXTERNAL_ASIDE:
            self.assertNotIn(token, text, f"the kernel speaks {token!r}")

    def test_the_kernel_states_no_domain_specific_measurement(self) -> None:
        """Domain-neutral means the core has no unit: the moment it names one, it has chosen a field."""

        text = kernel_text().lower()
        for word in ("polygon count", "texel", "loudness", "frame rate", "sample rate", "pixel"):
            self.assertNotIn(word, text)

    def test_the_fixtures_are_the_only_side_that_knows_the_domains(self) -> None:
        text = FIXTURES.read_text(encoding="utf-8")
        self.assertIn("isometric", text)
        self.assertNotIn("blender", text.lower())
        self.assertNotIn("comfyui", text.lower())

    def test_the_kernel_is_importable_with_the_examples_directory_gone(self) -> None:
        """Proof by isolation: run from a directory where ``examples`` cannot be resolved."""

        script = (
            "import importlib, pkgutil, sys, iris_project_os\n"
            "for info in pkgutil.iter_modules(iris_project_os.__path__):\n"
            "    importlib.import_module('iris_project_os.' + info.name)\n"
            "assert 'examples' not in sys.modules, sys.modules.keys()\n"
            "print(len(iris_project_os.__all__))\n"
        )
        with tempfile.TemporaryDirectory() as scratch:
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=scratch,
                capture_output=True,
                text=True,
                check=False,
                env={"PYTHONPATH": str(ROOT), "SYSTEMROOT": str(Path(sys.executable).parents[2])},
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), str(len(iris_project_os.__all__)))


class NoNetworkExecutionTests(TestCase):
    """The kernel must be able to state, freeze and compare a closure with no outside world."""

    def test_a_cold_import_of_the_whole_package_needs_no_network(self) -> None:
        script = (
            "import socket\n"
            "def _blocked(*args, **kwargs):\n"
            "    raise RuntimeError('network access during kernel import')\n"
            "socket.socket = _blocked\n"
            "socket.create_connection = _blocked\n"
            "import importlib, pkgutil, iris_project_os\n"
            "for info in pkgutil.iter_modules(iris_project_os.__path__):\n"
            "    importlib.import_module('iris_project_os.' + info.name)\n"
            "print(len(iris_project_os.__all__))\n"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), str(len(iris_project_os.__all__)))

    def test_freezing_diffing_and_serialising_never_opens_a_socket(self) -> None:
        original = socket.socket

        def blocked(*args: object, **kwargs: object) -> None:
            raise RuntimeError("network access during a kernel operation")

        socket.socket = blocked
        try:
            frozen = snapshot(production_id="p.offline", klass=SnapshotClass.VALIDATED_SNAPSHOT)
            diff = semantic_diff(frozen.closure, frozen.closure)
            self.assertTrue(diff.is_empty)
            payload = dumps(frozen)
            self.assertTrue(payload)
            self.assertEqual(payload, dumps(frozen))
        finally:
            socket.socket = original
