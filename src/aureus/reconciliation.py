from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from .domain import SettlementEvidence
from .settlement import ExternalTransaction


class MatchStatus(StrEnum):
    VERIFIED = "VERIFIED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    NO_MATCH = "NO_MATCH"


@dataclass(frozen=True)
class ProviderPayout:
    reference: str
    amount_usd: Decimal
    paid_at: datetime


@dataclass(frozen=True)
class MatchResult:
    status: MatchStatus
    payout: ProviderPayout
    transaction: ExternalTransaction | None


def reconcile(payout: ProviderPayout, transactions: list[ExternalTransaction], lag: timedelta = timedelta(hours=6)) -> MatchResult:
    amount_time = [
        tx for tx in transactions
        if tx.verified
        and tx.amount_usd == payout.amount_usd
        and payout.paid_at - lag <= tx.observed_at <= payout.paid_at + lag
    ]
    explicit = [tx for tx in amount_time if tx.reference == payout.reference]
    if len(explicit) == 1:
        return MatchResult(MatchStatus.VERIFIED, payout, explicit[0])
    if amount_time:
        return MatchResult(MatchStatus.HUMAN_REVIEW, payout, amount_time[0] if len(amount_time) == 1 else None)
    return MatchResult(MatchStatus.NO_MATCH, payout, None)


def to_settlement_evidence(match: MatchResult, source_sha256: str) -> SettlementEvidence:
    if match.status is not MatchStatus.VERIFIED or match.transaction is None:
        raise ValueError("only explicit verified matches can become settlement evidence")
    import hashlib
    destination_hash = hashlib.sha256(match.transaction.transaction_id.encode()).hexdigest()
    return SettlementEvidence(match.payout.reference, destination_hash, match.transaction.amount_usd,
                              match.transaction.observed_at, True, source_sha256)
