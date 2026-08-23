from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import Any

import psycopg

from .domain import SettlementEvidence
from .evidence import EconomicProof
from .intents import ComputeIntent


class PostgresStore:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def persist_intent(self, intent: ComputeIntent) -> None:
        with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO compute_intents(id,idempotency_key,provider,resource_id,state)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (idempotency_key) DO UPDATE SET state=EXCLUDED.state, updated_at=now()""",
                (intent.intent_id, intent.idempotency_key, intent.provider, intent.resource_id, intent.state.value),
            )

    def persist_external_settlement(self, evidence: SettlementEvidence) -> None:
        with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO external_settlement_evidence
                (provider_reference,destination_reference_hash,amount_usd,received_at,verified,source_sha256)
                VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (provider_reference) DO NOTHING""",
                (evidence.provider_reference, evidence.destination_reference_hash, evidence.amount_usd,
                 evidence.received_at, evidence.verified, evidence.source_sha256),
            )

    def persist_economic_proof(self, period_start: datetime, period_end: datetime, proof: EconomicProof) -> None:
        with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO economic_proofs
                (period_start,period_end,externally_settled_usd,total_attributed_costs_usd,
                 verified_net_cash_settled_usd,proof_sha256,demonstrated)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (proof_sha256) DO NOTHING""",
                (period_start, period_end, proof.externally_settled_usd, proof.total_attributed_costs_usd,
                 proof.verified_net_cash_settled_usd, proof.proof_sha256, proof.demonstrated),
            )


def evidence_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()
