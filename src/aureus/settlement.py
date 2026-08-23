from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx


@dataclass(frozen=True)
class ExternalTransaction:
    transaction_id: str
    amount_usd: Decimal
    observed_at: datetime
    reference: str | None
    verified: bool


class PayPalTransactionSearch:
    """Read-only PayPal reporting adapter."""

    def __init__(self, access_token: str) -> None:
        self._client = httpx.Client(
            base_url="https://api-m.paypal.com/v1/reporting",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20.0,
        )

    def transactions(self, start_date: str, end_date: str) -> Any:
        return self._client.get("/transactions", params={"start_date": start_date, "end_date": end_date, "fields": "all"}).raise_for_status().json()
