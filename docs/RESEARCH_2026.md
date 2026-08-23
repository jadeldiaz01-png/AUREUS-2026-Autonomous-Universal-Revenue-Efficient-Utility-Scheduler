# 2026 implementation research decisions

AUREUS uses current official interfaces and conservative evidence semantics:

- OpenBao Kubernetes auth uses pod ServiceAccount tokens and OpenBao Agent templates render short-lived/runtime secrets to files.
- PayPal Transaction Search is read-only and uses the reporting search scope; reporting can lag executed transactions, so reconciliation is asynchronous.
- PostgreSQL production recovery requires continuous WAL archiving plus a base backup for PITR.
- OpenTelemetry Collector is treated as security-sensitive infrastructure and receives bounded resources and least-privilege configuration.

Provider earnings, payout initiation and internal balances are observations, not independently settled cash.
