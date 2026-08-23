from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ReadinessDecision(StrEnum):
    NO_GO = "NO_GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    GO = "GO"


@dataclass(frozen=True)
class SettlementWindow:
    net_cash_usd: Decimal
    telemetry_coverage: Decimal
    unresolved_cost_items: int
    externally_verified: bool


@dataclass(frozen=True)
class ProductionEvidence:
    engineering_green: bool
    database_ready: bool
    pitr_restore_verified: bool
    workload_identity_verified: bool
    otlp_healthy: bool
    provider_observer_certified: bool
    runtime_ready: bool
    positive_windows: tuple[SettlementWindow, ...]


def evaluate(evidence: ProductionEvidence) -> ReadinessDecision:
    engineering = evidence.engineering_green
    runtime = all((evidence.database_ready, evidence.pitr_restore_verified, evidence.workload_identity_verified,
                   evidence.otlp_healthy, evidence.provider_observer_certified, evidence.runtime_ready))
    if not engineering:
        return ReadinessDecision.NO_GO
    if not runtime:
        return ReadinessDecision.CONDITIONAL_GO
    good = [w for w in evidence.positive_windows if w.externally_verified and w.net_cash_usd > 0
            and w.telemetry_coverage >= Decimal("0.95") and w.unresolved_cost_items == 0]
    return ReadinessDecision.GO if len(good) >= 3 else ReadinessDecision.CONDITIONAL_GO
