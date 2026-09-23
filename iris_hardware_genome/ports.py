"""Provider-neutral ports; M07 does not load adapters or execute commands."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .discovery import DiscoveryBatch, DiscoverySessionRef, ProbeDescriptor
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError

__all__ = ["DiscoveryAdapterPort", "admit_adapter_batch"]


@runtime_checkable
class DiscoveryAdapterPort(Protocol):
    """An explicitly selected host adapter returns evidence; it is never auto-imported by M07."""

    adapter_id: str
    adapter_version: str

    def collect(self, session: DiscoverySessionRef, probe: ProbeDescriptor) -> DiscoveryBatch:
        """Return a bounded, provenance-bearing batch for a declared probe."""
        ...


def admit_adapter_batch(adapter: DiscoveryAdapterPort, session: DiscoverySessionRef, probe: ProbeDescriptor) -> DiscoveryBatch:
    if type(adapter).__module__.startswith("iris_hardware_genome"):
        raise HardwareGenomeAdmissionError("semantic core adapters must be explicitly supplied through an external port")
    if not isinstance(adapter, DiscoveryAdapterPort):
        raise HardwareGenomeAdmissionError("adapter does not implement the explicit discovery port")
    batch = adapter.collect(session, probe)
    if type(batch) is not DiscoveryBatch or batch.session != session or batch.probe != probe:
        raise HardwareGenomeAdmissionError("adapter returned a batch bound to a different exact request")
    if any(
        item.evidence is not None
        and (item.evidence.source_adapter_id != adapter.adapter_id or item.evidence.source_adapter_version != adapter.adapter_version)
        for item in batch.observations
    ):
        raise HardwareGenomeIntegrityError("adapter evidence provenance differs from the explicitly selected adapter identity/version")
    return batch
