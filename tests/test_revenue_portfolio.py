from decimal import Decimal

from aureus.revenue_portfolio import CompoundingPolicy, RevenueChannel, RevenueStage, rank_channels


def test_compounding_uses_only_positive_verified_cash() -> None:
    policy = CompoundingPolicy()
    assert policy.allocation(Decimal("0"))["reinvest"] == Decimal("0")
    allocation = policy.allocation(Decimal("100"))
    assert allocation == {"reserve": Decimal("70.00"), "reinvest": Decimal("25.00"), "experimental": Decimal("5.00")}


def test_rank_channels_filters_unauthorized_or_unverifiable() -> None:
    good = RevenueChannel("ai_services", Decimal("20"), Decimal("0.8"), Decimal("0.1"), RevenueStage.AUTHORIZED, True, True)
    risky = RevenueChannel("compute", Decimal("30"), Decimal("0.5"), Decimal("0.5"), RevenueStage.ACTIVE, True, True)
    unauthorized = RevenueChannel("agentic_payments", Decimal("100"), Decimal("0.9"), Decimal("0.1"), RevenueStage.RESEARCH, False, True)
    unverifiable = RevenueChannel("unknown", Decimal("999"), Decimal("1"), Decimal("0"), RevenueStage.ACTIVE, True, False)
    ranked = rank_channels([risky, unauthorized, good, unverifiable])
    assert [channel.channel_id for channel in ranked] == ["ai_services", "compute"]


def test_invalid_probability_is_fail_closed() -> None:
    invalid = RevenueChannel("bad", Decimal("10"), Decimal("1.2"), Decimal("0.1"), RevenueStage.ACTIVE, True, True)
    assert rank_channels([invalid]) == []
