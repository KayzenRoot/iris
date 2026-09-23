"""The exact frozen M06 technology-family inventory and implementation map."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .errors import ProductionStateIntegrityError

__all__ = ["TechnologyFamily", "M06_FAMILIES", "M06_FAMILY_MAP", "validate_family_catalog"]


@dataclass(frozen=True)
class TechnologyFamily:
    code: str
    name: str
    implementation_module: str
    proof_method: str
    ownership: str = "M06_KERNEL"


M06_FAMILIES = (
    TechnologyFamily("RVF", "Revision Verification Fabric", "revisions", "test_family_rvf"),
    TechnologyFamily("IML", "Immutable Master Ledger", "revisions", "test_family_iml"),
    TechnologyFamily("DAS", "Digest Agility Shield", "revisions", "test_family_das"),
    TechnologyFamily("SEA", "Semantic Equivalence Airgap", "revisions", "test_family_sea"),
    TechnologyFamily("AVS", "Availability State Lattice", "revisions", "test_family_avs"),
    TechnologyFamily("CFM", "Causal Fingerprint Matrix", "dependencies", "test_family_cfm"),
    TechnologyFamily("MSI", "Minimum Sufficient Invalidation", "dependencies", "test_family_msi"),
    TechnologyFamily("HDS", "Hidden Dependency Sentinel", "dependencies", "test_family_hds"),
    TechnologyFamily("ICX", "Impact Cone Explainer", "dependencies", "test_family_icx"),
    TechnologyFamily("RDI", "Rebuildable Dependency Index", "dependencies", "test_family_rdi"),
    TechnologyFamily("SRE", "Selective Regeneration Engine", "regeneration", "test_family_sre"),
    TechnologyFamily("RAP", "Reuse Admission Passport", "regeneration", "test_family_rap"),
    TechnologyFamily("FEX", "Frontier Expansion Matrix", "regeneration", "test_family_fex"),
    TechnologyFamily("MXR", "Mixed Reconstruction Receipt", "regeneration", "test_family_mxr"),
    TechnologyFamily("SDS", "Stochastic Determinism Shield", "reconstruction", "test_family_sds"),
    TechnologyFamily("RCL", "Reproducibility Class Lattice", "reconstruction", "test_family_rcl"),
    TechnologyFamily("RXM", "Reconstruction eXactness Manifest", "reconstruction", "test_family_rxm"),
    TechnologyFamily("DRG", "Divergence Reason Graph", "reconstruction", "test_family_drg"),
    TechnologyFamily("ESB", "Equivalence Safety Bridge", "reconstruction", "test_family_esb", "M01_M05_EVALUATOR_PORT"),
    TechnologyFamily("HPR", "Historical Permission Firewall", "reconstruction", "test_family_hpr", "M53_M54_POLICY_PORT"),
    TechnologyFamily("LRG", "Lineage Reachability Guard", "lineage", "test_family_lrg"),
    TechnologyFamily("SGC", "Safe Garbage Collection Protocol", "lineage", "test_family_sgc", "M55_DELETION_PORT"),
    TechnologyFamily("RRB", "Rollback Reconstruction Bridge", "lineage", "test_family_rrb"),
    TechnologyFamily("RSC", "Release State Capsule", "release", "test_family_rsc"),
    TechnologyFamily("CRA", "Cleanup Race Armor", "lineage", "test_family_cra", "M55_TRANSACTION_PORT"),
)

M06_FAMILY_MAP = MappingProxyType({item.code: item for item in M06_FAMILIES})


def validate_family_catalog() -> None:
    expected = {
        "RVF", "IML", "DAS", "SEA", "AVS", "CFM", "MSI", "HDS", "ICX", "RDI",
        "SRE", "RAP", "FEX", "MXR", "SDS", "RCL", "RXM", "DRG", "ESB", "HPR",
        "LRG", "SGC", "RRB", "RSC", "CRA",
    }
    codes = [item.code for item in M06_FAMILIES]
    proofs = [item.proof_method for item in M06_FAMILIES]
    if len(codes) != 25 or set(codes) != expected or len(set(codes)) != 25:
        raise ProductionStateIntegrityError("M06 must register all 25 frozen technology families exactly once")
    if len(set(proofs)) != 25 or any(not item.implementation_module for item in M06_FAMILIES):
        raise ProductionStateIntegrityError("each M06 technology family requires one implementation and proof target")
