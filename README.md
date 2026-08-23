# AUREUS-2026

**Autonomous Universal Revenue & Efficient Utility Scheduler**

AUREUS is a governed revenue-optimization agent that discovers, evaluates, observes and reconciles legitimate compute-revenue opportunities while keeping financial and provider-write authority fail-closed by default.

## Core invariant

`VERIFIED_NET_CASH_SETTLED = EXTERNAL_CASH_RECEIVED - TOTAL_ATTRIBUTED_COSTS`

Provider earnings, internal balances and payout initiation are not settled cash.

## Production states

- `ENGINEERING_READY`: code, tests, migrations, supply-chain controls.
- `AGENT_RUNNING`: persistent runtime + PostgreSQL + workload identity + fresh telemetry + health/readiness.
- `ECONOMICALLY_DEMONSTRATED`: external settlement verified + complete costs + positive net cash.
- `PRODUCTION_GO`: all gates green on an exact SHA plus multiple independent positive settlement windows.

## Authority boundary

AUREUS does **not** autonomously perform KYC, accept contracts, purchase hardware, deposit funds, request payouts, transfer money, list/unlist provider machines or bypass platform controls. These actions require a separate explicit approval boundary.

See `docs/ARCHITECTURE.md`, `docs/PRODUCTION_GATES.md`, and `SECURITY.md`.
