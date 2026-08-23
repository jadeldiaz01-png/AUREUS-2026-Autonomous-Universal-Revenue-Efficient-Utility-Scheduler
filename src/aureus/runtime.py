from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def read_secret(name: str) -> str:
    file_var = os.getenv(f"{name}_FILE")
    if not file_var:
        raise RuntimeError(f"{name}_FILE is required; static secret env vars are not accepted")
    value = Path(file_var).read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError(f"{name}_FILE is empty")
    return value


@dataclass(frozen=True)
class RuntimeReadiness:
    database_ready: bool
    workload_identity_ready: bool
    provider_fresh: bool
    telemetry_fresh: bool
    evidence_persisting: bool
    vast_observer_certified: bool

    @property
    def ready(self) -> bool:
        return all((self.database_ready, self.workload_identity_ready, self.provider_fresh, self.telemetry_fresh, self.evidence_persisting, self.vast_observer_certified))
