# AUREUS-2026 architecture

AUREUS uses a deterministic control plane around probabilistic research/forecasting agents.

## Planes

1. **Research plane** — discovery, due diligence, fraud/TOS/geo review, market intelligence.
2. **Economic plane** — utilization/payment forecasting, full attributable-cost accounting, ranking.
3. **Policy/Risk plane** — deterministic authorization, kill switches, human approvals.
4. **Execution plane** — durable intents, idempotency, UNKNOWN -> RECONCILING, bounded adapters.
5. **Evidence plane** — telemetry, revenue ledger, external settlement, canonical hashes.
6. **Operations plane** — PostgreSQL, OpenBao workload identity, OpenTelemetry, SLOs, DR.

Probabilistic AI may propose actions but cannot authorize critical financial, identity, contractual or provider-mutation actions.
