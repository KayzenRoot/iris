from __future__ import annotations

import unittest

from iris_hardware_genome import (
    BackendFamily,
    CapabilityDimension,
    EvidenceStrength,
    FreshnessClass,
    HardwareSubjectRef,
    HardwareGenomeIntegrityError,
    HardwareGenomeLimitError,
    HardwareGenomeLimits,
    MediaDirection,
    MediaEngineCapability,
    MediaInteropEvidence,
    ObservationState,
    PeerPathProof,
    PrecisionFamily,
    PrecisionFeature,
    RuntimeScope,
    RuntimeSubjectRef,
    SubjectKind,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
    TopologyNodeKind,
    TopologyLinkEvidence,
    TopologyRelation,
    validate_topology_graph,
)
from m07_support import RUNTIME, SUBJECT, SUBJECT_1, evidence, observation


class TestPrecisionMediaTopology(unittest.TestCase):
    def test_precision_dimensions_do_not_collapse_to_boolean(self):
        observed = observation("precision.fp8.e4m3", observation_id="precision-e4m3")
        feature = PrecisionFeature(
            "precision-feature", SUBJECT.subject_id, RUNTIME.runtime_id, BackendFamily.CUDA,
            PrecisionFamily.FP8_E4M3,
            tuple((dimension, ObservationState.OBSERVED if dimension in {CapabilityDimension.REPRESENTATION, CapabilityDimension.ARITHMETIC} else ObservationState.UNKNOWN) for dimension in CapabilityDimension),
            (observed.observation_id,),
        )
        feature.validate_observations((observed,))
        self.assertIs(feature.state_for(CapabilityDimension.REPRESENTATION), ObservationState.OBSERVED)
        self.assertIs(feature.state_for(CapabilityDimension.CONFORMANCE), ObservationState.UNKNOWN)

    def test_media_codec_direction_engine_and_feature_limits_are_exact(self):
        value = {
            "engine_id": "video-engine-0", "codec": "h264", "direction": "ENCODE",
            "profile": "high", "level": "5.1", "bit_depth": 8, "chroma_format": "420",
            "max_width": 7680, "max_height": 4320, "input_format": "nv12", "output_format": "h264",
        }
        observed = observation("media.h264.encode", observation_id="media-h264", value=value)
        capability = MediaEngineCapability(
            "media-cap", SUBJECT.subject_id, RUNTIME.runtime_id, "video-engine-0", "os-media",
            "h264", MediaDirection.ENCODE, "high", "5.1", 8, "420", 7680, 4320,
            "nv12", "h264", EvidenceStrength.FEATURE_REPORTED, ObservationState.OBSERVED, observed,
        )
        self.assertEqual(capability.max_width, 7680)
        self.assertEqual(capability.direction, MediaDirection.ENCODE)
        with self.assertRaises(HardwareGenomeIntegrityError):
            MediaEngineCapability(
                "media-wrong", SUBJECT.subject_id, RUNTIME.runtime_id, "different-engine", "os-media",
                "h264", MediaDirection.ENCODE, "high", "5.1", 8, "420", 7680, 4320,
                "nv12", "h264", EvidenceStrength.FEATURE_REPORTED, ObservationState.OBSERVED, observed,
            )
        wrong_direction = observation("media.h264.decode", observation_id="media-decode", value=value)
        with self.assertRaises(HardwareGenomeIntegrityError):
            MediaEngineCapability(
                "media-direction", SUBJECT.subject_id, RUNTIME.runtime_id, "video-engine-0", "os-media",
                "h264", MediaDirection.ENCODE, "high", "5.1", 8, "420", 7680, 4320,
                "nv12", "h264", EvidenceStrength.FEATURE_REPORTED, ObservationState.OBSERVED, wrong_direction,
            )

    def test_media_interop_requires_exact_two_api_paths_and_scope(self):
        interop_observation = observation(
            "media.interop.vulkan.directml", observation_id="interop-vulkan-directml",
            value={"source_engine_id": "decode-0", "source_api": "vulkan", "target_engine_id": "compute-0", "target_api": "directml"},
        )
        interop = MediaInteropEvidence(
            "interop-proof", SUBJECT.subject_id, RUNTIME.runtime_id, "decode-0", "vulkan",
            "compute-0", "directml", ObservationState.OBSERVED, interop_observation,
        )
        value = {
            "engine_id": "decode-0", "codec": "h264", "direction": "DECODE",
        }
        media_observation = observation("media.h264.decode", observation_id="media-decode", value=value)
        capability = MediaEngineCapability(
            "decode-cap", SUBJECT.subject_id, RUNTIME.runtime_id, "decode-0", "vulkan", "h264",
            MediaDirection.DECODE, None, None, None, None, None, None, None, None,
            EvidenceStrength.FEATURE_REPORTED, ObservationState.OBSERVED, media_observation,
            (interop.interop_id,), (interop,),
        )
        self.assertEqual(capability.interop_keys, (interop.interop_id,))
        unrelated_observation = observation(
            "media.interop.opengl.directml", observation_id="interop-opengl-directml",
            value={"source_engine_id": "other-engine", "source_api": "opengl", "target_engine_id": "compute-0", "target_api": "directml"},
        )
        other = MediaInteropEvidence(
            "interop-other", SUBJECT.subject_id, RUNTIME.runtime_id, "other-engine", "opengl",
            "compute-0", "directml", ObservationState.OBSERVED, unrelated_observation,
        )
        with self.assertRaises(HardwareGenomeIntegrityError):
            MediaEngineCapability(
                "decode-other", SUBJECT.subject_id, RUNTIME.runtime_id, "decode-0", "vulkan", "h264",
                MediaDirection.DECODE, None, None, None, None, None, None, None, None,
                EvidenceStrength.FEATURE_REPORTED, ObservationState.OBSERVED, media_observation,
                (other.interop_id,), (other,),
            )

    def test_pairwise_access_proof_binds_ordered_endpoints_and_runtime(self):
        pair_evidence = evidence("peer-proof", related_subject=SUBJECT_1)
        proof = PeerPathProof(
            "peer-a-b", SUBJECT.subject_id, SUBJECT_1.subject_id, RUNTIME.runtime_id,
            "SOURCE_TO_TARGET", "cuda", ObservationState.OBSERVED, pair_evidence,
        )
        self.assertIs(proof.state, ObservationState.OBSERVED)
        reverse = evidence("peer-proof-reverse", subject=SUBJECT_1, related_subject=SUBJECT)
        with self.assertRaises(HardwareGenomeIntegrityError):
            PeerPathProof(
                "peer-a-b-bad", SUBJECT.subject_id, SUBJECT_1.subject_id, RUNTIME.runtime_id,
                "SOURCE_TO_TARGET", "cuda", ObservationState.OBSERVED, reverse,
            )

    def test_topology_edges_are_evidence_bound_acyclic_and_bounded(self):
        host = TopologyNode("host-node", TopologyNodeKind.HOST, runtime=RUNTIME)
        gpu = TopologyNode("gpu-node", TopologyNodeKind.ACCELERATOR, subject=SUBJECT, runtime=RUNTIME)
        edge = TopologyEdge(
            "attach", host.node_id, gpu.node_id, TopologyRelation.ATTACHED_TO,
            ObservationState.OBSERVED, evidence("topology-edge"), FreshnessClass.TOPOLOGY_STABLE,
        )
        graph = TopologyGraph("topology", (host, gpu), (edge,))
        validate_topology_graph(graph)
        invalid = TopologyEdge(
            "parent", host.node_id, gpu.node_id, TopologyRelation.PARENT_OF,
            ObservationState.OBSERVED, evidence("topology-parent"), FreshnessClass.TOPOLOGY_STABLE,
        )
        cycle = TopologyEdge(
            "parent-back", gpu.node_id, host.node_id, TopologyRelation.PARENT_OF,
            ObservationState.OBSERVED, evidence("topology-parent-back"), FreshnessClass.TOPOLOGY_STABLE,
        )
        with self.assertRaises(HardwareGenomeIntegrityError):
            validate_topology_graph(TopologyGraph("cycle", (host, gpu), (invalid, cycle)))
        with self.assertRaises(HardwareGenomeLimitError):
            validate_topology_graph(graph, limits=HardwareGenomeLimits(max_topology_nodes=1))

    def test_partitioned_virtual_and_physical_nodes_remain_distinct(self):
        vm = RuntimeSubjectRef("vm-runtime", RuntimeScope.VM, "1.0")
        physical = TopologyNode("physical", TopologyNodeKind.ACCELERATOR, subject=SUBJECT, runtime=RUNTIME)
        partition_subject = HardwareSubjectRef("gpu-partition", SubjectKind.PARTITION)
        partition = TopologyNode("partition", TopologyNodeKind.PARTITION, subject=partition_subject, runtime=vm)
        relation = TopologyEdge(
            "exposed", "physical", "partition", TopologyRelation.EXPOSED_AS,
            ObservationState.OBSERVED, evidence("partition-exposed", subject=SUBJECT, runtime=RUNTIME), FreshnessClass.TOPOLOGY_STABLE,
        )
        validate_topology_graph(TopologyGraph("virtualized", (physical, partition), (relation,)))
        self.assertIsNot(physical.subject.kind, partition.subject.kind)

    def test_topology_never_claims_unobserved_parent_or_peer_semantics(self):
        a = TopologyNode("a", TopologyNodeKind.ACCELERATOR, subject=SUBJECT)
        b = TopologyNode("b", TopologyNodeKind.ACCELERATOR, subject=SUBJECT_1)
        pair = TopologyEdge(
            "peer-unknown", "a", "b", TopologyRelation.PEER_ACCESS_TO, ObservationState.UNKNOWN,
            evidence("peer-unknown", related_subject=SUBJECT_1, runtime=None), FreshnessClass.UNKNOWN_VOLATILITY,
        )
        validate_topology_graph(TopologyGraph("unknown-peer", (a, b), (pair,)))
        self.assertIs(pair.state, ObservationState.UNKNOWN)

    def test_pcie_capability_and_negotiated_state_do_not_claim_measured_bandwidth(self):
        maximum = observation(
            "topology.pcie.link-0.maximum", observation_id="pcie-max",
            value={"generation": 5, "lane_width": 16},
        )
        negotiated = observation(
            "topology.pcie.link-0.negotiated", observation_id="pcie-negotiated",
            value={"generation": 4, "lane_width": 8},
        )
        link = TopologyLinkEvidence(
            "link-0", SUBJECT.subject_id, RUNTIME.runtime_id, 5, 16, maximum, 4, 8, negotiated,
        )
        self.assertEqual(link.maximum_generation, 5)
        self.assertEqual(link.negotiated_generation, 4)
        self.assertFalse(hasattr(link, "measured_bandwidth_bytes_per_second"))
        self.assertFalse(hasattr(link, "bandwidth_observation"))


if __name__ == "__main__":
    unittest.main()
