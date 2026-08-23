from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal

from .domain import CostBreakdown, SettlementEvidence, TelemetryWindow


@dataclass(frozen=True)
class EconomicProof:
    externally_settled_usd: Decimal
    total_attributed_costs_usd: Decimal
    verified_net_cash_settled_usd: Decimal
    demonstrated: bool
    proof_sha256: str


def build_economic_proof(settlements: list[SettlementEvidence], telemetry: TelemetryWindow, costs: CostBreakdown) -> EconomicProof:
    if not settlements or not all(s.verified for s in settlements):
        raise ValueError("all external settlements must be independently verified")
    if telemetry.coverage_fraction < Decimal("0.95"):
        raise ValueError("telemetry coverage below 95%")
    if not telemetry.full_host_power_verified:
        raise ValueError("GPU-board-only power is insufficient")
    if not telemetry.costs_verified or telemetry.unresolved_cost_items:
        raise ValueError("all attributable costs must be verified and resolved")
    refs = [s.provider_reference for s in settlements]
    if len(refs) != len(set(refs)):
        raise ValueError("duplicate settlement reference")
    external = sum((s.amount_usd for s in settlements), Decimal("0"))
    net = external - costs.total
    payload = {
        "settlements": [asdict(s) for s in settlements],
        "telemetry": asdict(telemetry),
        "costs": asdict(costs),
        "net": str(net),
    }
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    return EconomicProof(external, costs.total, net, net > 0, digest)
