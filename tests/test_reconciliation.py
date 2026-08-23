from datetime import datetime, timezone
from decimal import Decimal

from aureus.reconciliation import MatchStatus, ProviderPayout, reconcile
from aureus.settlement import ExternalTransaction


def test_exact_reference_can_verify() -> None:
    now = datetime.now(timezone.utc)
    payout = ProviderPayout("vast-123", Decimal("20"), now)
    tx = ExternalTransaction("paypal-tx", Decimal("20"), now, "vast-123", True)
    assert reconcile(payout, [tx]).status is MatchStatus.VERIFIED


def test_amount_and_time_only_requires_human_review() -> None:
    now = datetime.now(timezone.utc)
    payout = ProviderPayout("vast-123", Decimal("20"), now)
    tx = ExternalTransaction("paypal-tx", Decimal("20"), now, None, True)
    assert reconcile(payout, [tx]).status is MatchStatus.HUMAN_REVIEW
