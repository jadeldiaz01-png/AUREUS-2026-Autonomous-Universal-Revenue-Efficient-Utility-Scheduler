from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class Decision(StrEnum):
    REJECT = "REJECT"
    SIMULATE = "SIMULATE"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    APPROVE = "APPROVE"


class IntentState(StrEnum):
    CREATED = "CREATED"
    POLICY_CHECK = "POLICY_CHECK"
    ECONOMICS_CHECK = "ECONOMICS_CHECK"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    READY = "READY"
    DISPATCHING = "DISPATCHING"
    DISPATCHED = "DISPATCHED"
    UNKNOWN = "UNKNOWN"
    RECONCILING = "RECONCILING"
    CONFIRMED = "CONFIRMED"
    FAILED_FINAL = "FAILED_FINAL"


@dataclass(frozen=True)
class CostBreakdown:
    energy: Decimal = Decimal("0")
    platform_fees: Decimal = Decimal("0")
    hosting: Decimal = Decimal("0")
    network: Decimal = Decimal("0")
    depreciation: Decimal = Decimal("0")
    ai_api: Decimal = Decimal("0")
    maintenance: Decimal = Decimal("0")
    other: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return sum((self.energy, self.platform_fees, self.hosting, self.network, self.depreciation, self.ai_api, self.maintenance, self.other), Decimal("0"))


@dataclass(frozen=True)
class Opportunity:
    provider: str
    resource_id: str
    gross_revenue_usd: Decimal
    expected_utilization: Decimal
    payment_probability: Decimal
    costs: CostBreakdown
    authorized_resource: bool = False
    tos_allowed: bool = False
    geo_allowed: bool = False
    risk_allowed: bool = False


@dataclass(frozen=True)
class SettlementEvidence:
    provider_reference: str
    destination_reference_hash: str
    amount_usd: Decimal
    received_at: datetime
    verified: bool
    source_sha256: str


@dataclass(frozen=True)
class TelemetryWindow:
    start_at: datetime
    end_at: datetime
    coverage_fraction: Decimal
    full_host_power_verified: bool
    costs_verified: bool
    unresolved_cost_items: tuple[str, ...] = field(default_factory=tuple)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)
