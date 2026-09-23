"""Historical restoration cannot manufacture current hardware/runtime truth."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record, content_digest
from .discovery import DiscoverySnapshot
from .enums import ObservationState
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError
from .genome import HardwareGenome, validate_hardware_genome
from .versions import require_identifier, require_nonnegative_int

__all__ = ["HistoricalRestoration", "CurrentTruthEvidence", "restore_as_historical", "require_fresh_current_truth"]


@dataclass(frozen=True)
class HistoricalRestoration(M07Record):
    restoration_id: str
    genome_id: str
    restored_at_ms: int
    canonical_digest: str
    claim_status: str = "HISTORICAL_ONLY"

    def __post_init__(self) -> None:
        from .versions import require_digest

        for field in ("restoration_id", "genome_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "restored_at_ms", require_nonnegative_int(self.restored_at_ms, "restored_at_ms"))
        object.__setattr__(self, "canonical_digest", require_digest(self.canonical_digest, "canonical_digest"))
        if self.claim_status != "HISTORICAL_ONLY":
            raise HardwareGenomeIntegrityError("restored evidence must remain historical only")


@dataclass(frozen=True)
class CurrentTruthEvidence(M07Record):
    evidence_id: str
    restoration_id: str
    source_genome_id: str
    fresh_snapshot_id: str
    captured_at_ms: int
    subject_ids: tuple[str, ...]
    completeness: ObservationState

    def __post_init__(self) -> None:
        for field in ("evidence_id", "restoration_id", "source_genome_id", "fresh_snapshot_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "captured_at_ms", require_nonnegative_int(self.captured_at_ms, "captured_at_ms"))
        from .versions import require_unique

        object.__setattr__(self, "subject_ids", tuple(sorted(require_unique(self.subject_ids, "subject_ids", maximum=2_048))))
        if type(self.completeness) is not ObservationState or self.completeness is not ObservationState.OBSERVED:
            raise HardwareGenomeAdmissionError("current truth requires a complete fresh discovery snapshot")


def restore_as_historical(genome: HardwareGenome, *, restoration_id: str, restored_at_ms: int) -> HistoricalRestoration:
    genome = HardwareGenome.coerce(genome, "genome")
    validate_hardware_genome(genome)
    restored_at_ms = require_nonnegative_int(restored_at_ms, "restored_at_ms")
    return HistoricalRestoration(
        restoration_id, genome.genome_id, restored_at_ms,
        content_digest({"genome_id": genome.genome_id, "canonical_content": genome}),
    )


def require_fresh_current_truth(restoration: HistoricalRestoration, snapshot: DiscoverySnapshot) -> CurrentTruthEvidence:
    restoration = HistoricalRestoration.coerce(restoration, "restoration")
    snapshot = DiscoverySnapshot.coerce(snapshot, "snapshot")
    if snapshot.captured_at_ms <= restoration.restored_at_ms or snapshot.completeness is not ObservationState.OBSERVED:
        raise HardwareGenomeAdmissionError("historical restoration needs newer complete discovery before current claims")
    observed_subjects = {
        item.subject.subject_id for item in snapshot.observations
        if item.subject is not None and item.state is ObservationState.OBSERVED
    }
    if not observed_subjects:
        raise HardwareGenomeAdmissionError("fresh current-state evidence must bind exact observed hardware subjects")
    evidence_id = f"m07-recovery-current:{content_digest({'restoration': restoration, 'snapshot': snapshot})}"
    return CurrentTruthEvidence(
        evidence_id, restoration.restoration_id, restoration.genome_id, snapshot.snapshot_id,
        snapshot.captured_at_ms, tuple(sorted(observed_subjects)), snapshot.completeness,
    )
