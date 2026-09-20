"""Proofs that the M01 kernel stays domain-neutral and self-contained.

The kernel is only useful if a future module can plug Blender, ComfyUI or a
perceptual model into it from the outside. These tests fail the moment the core
starts depending on any of that, or on the network.
"""

from __future__ import annotations

import ast
import socket
import subprocess
import sys
from pathlib import Path
from unittest import TestCase
from typing import Iterator

import iris_quality
from iris_quality.contracts import FidelityContract, PromotionRule, QualityClass
from iris_quality.decision import DecisionEngine
from iris_quality.dimensions import DimensionAssessment, GateState, UncertaintyState
from iris_quality.evidence import EvidenceRef
from iris_quality.judging import SubjectRef
from iris_quality.serialization import dumps
from iris_quality.versions import ComponentVersion
from tests.m01_kernel_support import promotion_authority

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "iris_quality"

FORBIDDEN_ROOTS = (
    "blender",
    "bpy",
    "comfyui",
    "comfy",
    "dreamsim",
    "flip",
    "pytorch_flip",
    "webgpu",
    "gpu",
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
    "numpy",
    "scipy",
    "PIL",
    "cv2",
    "trimesh",
    "shapely",
    "skimage",
    "requests",
    "httpx",
    "urllib3",
    "aiohttp",
)

FORBIDDEN_TEXT = (
    "profile.nerim",
    "isometric",
    "logo-vector",
    "generic-image",
    "blender",
    "comfyui",
    "dreamsim",
    "webgpu",
)

NETWORK_TOUCHPOINTS = (
    ("socket", "socket"),
    ("socket", "create_connection"),
    ("subprocess", "run"),
    ("os", "system"),
)


def kernel_modules() -> Iterator[Path]:
    return sorted(KERNEL.glob("*.py"))


def absolute_import_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".", 1)[0])
    return roots


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


class ImportBoundaryTests(TestCase):
    def test_the_kernel_directory_exists_and_is_populated(self) -> None:
        modules = list(kernel_modules())
        self.assertGreaterEqual(len(modules), 10)
        self.assertTrue((KERNEL / "__init__.py").is_file())

    def test_every_kernel_import_is_standard_library_or_the_kernel_itself(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                roots = absolute_import_roots(ast.parse(path.read_text(encoding="utf-8")))
                self.assertLessEqual(roots, set(sys.stdlib_module_names), f"{path.name} leaves stdlib")
                self.assertNotIn("examples", roots)

    def test_no_media_engine_or_model_provider_is_imported(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                roots = absolute_import_roots(ast.parse(path.read_text(encoding="utf-8")))
                self.assertEqual(roots & set(FORBIDDEN_ROOTS), set())

    def test_the_kernel_never_reaches_for_the_network_or_a_shell(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                calls = call_names(ast.parse(path.read_text(encoding="utf-8")))
                self.assertEqual(calls & {f"{a}.{b}" for a, b in NETWORK_TOUCHPOINTS}, set())

    def test_the_public_surface_is_the_kernel_alone(self) -> None:
        self.assertTrue(iris_quality.__all__)
        for name in iris_quality.__all__:
            with self.subTest(symbol=name):
                self.assertTrue(hasattr(iris_quality, name), f"{name} is exported but absent")


class VocabularyBoundaryTests(TestCase):
    def test_the_kernel_does_not_name_any_of_the_synthetic_domains(self) -> None:
        for path in kernel_modules():
            with self.subTest(module=path.name):
                text = path.read_text(encoding="utf-8").lower()
                for token in FORBIDDEN_TEXT:
                    self.assertNotIn(token, text, f"{path.name} hardcodes {token!r}")

    def test_the_documented_vocabulary_is_domain_neutral(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8") for path in kernel_modules()).lower()
        for word in ("polygon count", "texture resolution", "render time", "model size"):
            self.assertNotIn(word, text)

    def test_the_examples_package_is_the_only_side_that_knows_domains(self) -> None:
        fixtures = ROOT / "examples" / "m01_synthetic_profiles.py"
        text = fixtures.read_text(encoding="utf-8").lower()
        self.assertIn("isometric", text)
        self.assertNotIn("blender", text)
        self.assertNotIn("comfyui", text)


class NoNetworkExecutionTests(TestCase):
    def test_a_cold_import_of_the_whole_package_needs_no_network(self) -> None:
        script = (
            "import socket\n"
            "def _blocked(*args, **kwargs):\n"
            "    raise RuntimeError('network access during kernel import')\n"
            "socket.socket = _blocked\n"
            "socket.create_connection = _blocked\n"
            "import importlib, pkgutil, iris_quality\n"
            "for info in pkgutil.iter_modules(iris_quality.__path__):\n"
            "    importlib.import_module('iris_quality.' + info.name)\n"
            "print(len(iris_quality.__all__))\n"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), str(len(iris_quality.__all__)))

    def test_deciding_and_serialising_never_opens_a_socket(self) -> None:
        original = socket.socket

        def blocked(*args: object, **kwargs: object) -> None:
            raise RuntimeError("network access during a kernel decision")

        socket.socket = blocked
        try:
            evaluator = ComponentVersion("kernel.neutrality", "1.0.0")
            built = FidelityContract(
                contract_id="contract.neutral",
                intent="prove the kernel runs without the outside world",
                output_class=QualityClass.PREVIEW,
                dimension_ids=("technical-integrity",),
                major_defect_classes=("broken-structure",),
                evaluator_set=(evaluator,),
                promotion_rules=(PromotionRule(QualityClass.PREVIEW, ("technical-integrity",)),),
            )
            subject = SubjectRef(subject_id="asset.neutral", content_sha256="3" * 64)
            assessment = DimensionAssessment(
                dimension_id="technical-integrity",
                gate=GateState.PASS,
                uncertainty=UncertaintyState.KNOWN,
                evaluator=evaluator,
                value=0.97,
                confidence=0.97,
                evidence=(
                    EvidenceRef(
                        evidence_id="ev.neutral",
                        kind="METRIC",
                        locator="fixtures/neutral.json",
                        content_sha256="4" * 64,
                        produced_by=evaluator,
                        dimension_id="technical-integrity",
                    ),
                ),
            )
            decision = DecisionEngine().evaluate(
                built, subject, assessments=(assessment,),
                authority=promotion_authority(built)
            )
            self.assertEqual(decision.outcome.value, "PROMOTED")
            again = DecisionEngine().evaluate(built, subject, assessments=(assessment,), authority=promotion_authority(built))
            self.assertEqual(dumps(decision), dumps(again))
        finally:
            socket.socket = original
