from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from aureus.domain import CostBreakdown, SettlementEvidence, TelemetryWindow
from aureus.evidence import build_economic_proof


def settlement(amount: str = "12") -> SettlementEvidence:
    return SettlementEvidence(
        provider_reference="payout-1",
        destination_reference_hash="a" * 64,
        amount_usd=Decimal(amount),
        received_at=datetime.now(timezone.utc),
        verified=True,
        source_sha256="b" * 64,
    )


def telemetry(*, coverage: str = "0.99", full_host: bool = True) -> TelemetryWindow:
    end = datetime.now(timezone.utc)
    return TelemetryWindow(end - timedelta(hours=24), end, Decimal(coverage), full_host, True)


def test_verified_positive_external_cash_can_demonstrate_economics() -> None:
    proof = build_economic_proof([settlement()], telemetry(), CostBreakdown(energy=Decimal("2"), depreciation=Decimal("1")))
    assert proof.verified_net_cash_settled_usd == Decimal("9")
    assert proof.demonstrated is True


def test_gpu_board_only_power_blocks_gate() -> None:
    with pytest.raises(ValueError, match="GPU-board-only"):
        build_economic_proof([settlement()], telemetry(full_host=False), CostBreakdown())


def test_low_telemetry_coverage_blocks_gate() -> None:
    with pytest.raises(ValueError, match="95%"):
        build_economic_proof([settlement()], telemetry(coverage="0.94"), CostBreakdown())


def test_unverified_external_cash_blocks_gate() -> None:
    bad = SettlementEvidence("payout-1", "a" * 64, Decimal("12"), datetime.now(timezone.utc), False, "b" * 64)
    with pytest.raises(ValueError, match="independently verified"):
        build_economic_proof([bad], telemetry(), CostBreakdown())
