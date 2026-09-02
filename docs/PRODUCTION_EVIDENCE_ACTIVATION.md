# AUREUS Production Evidence Activation

This runbook promotes AUREUS only from observed target-environment evidence. Repository code, mocks, screenshots, projected revenue, provider balances and pending withdrawals are insufficient.

## Runtime evidence sequence

1. PostgreSQL: prove authenticated reachability, schema identity and durable write/readback using the production runtime role.
2. PITR: enable continuous WAL archiving, take a base backup, create a named restore point, restore into an isolated target and verify the expected record state. PostgreSQL 18 documents that PITR depends on a continuous archived WAL sequence; logical pg_dump output is not a PITR substitute.
3. OpenBao: authenticate the workload with Kubernetes service-account identity. Do not inject a static long-lived OpenBao token. Record role, auth mount, token TTL class and a hash/reference to the successful identity proof; never commit the token.
4. OpenTelemetry: prove collector health and an end-to-end trace/metric roundtrip. Apply least privilege, protect collector endpoints, limit resources and verify that sensitive settlement/credential values are not exported.
5. Revenue provider/channel: prove the channel is authorized and the runtime credential is read-only unless a separately approved write capability is required.
6. Settlement: reconcile provider/work reference to an independently observed external settlement destination. For PayPal Transaction Search, use the reporting/search/read scope; transaction visibility can lag execution, so observation timestamps must be retained.

## Economic evidence

A production certificate requires at least three independent windows. Every window must contain independently verified settlement, complete attributable costs and VERIFIED_NET_CASH_SETTLED_USD > 0. Aggregate platform balances, invoices, advertised rewards, credits, token marks or pending payouts do not count.

Required cost classes include platform/payment fees, model/API use, compute, electricity where applicable, network, depreciation/maintenance where applicable, taxes/withholding when attributable and any other known direct cost. Any unresolved attributable cost blocks promotion.

## Evidence handling

Raw production evidence stays outside the public repository. The protected GitHub Environment `aureus-production-readiness` supplies `AUREUS_PRODUCTION_EVIDENCE_JSON` to the production gate. The gate checks out the exact requested SHA, writes the raw bundle to a mode-600 temporary file, certifies it, prints only a hash-based certificate and removes the raw file.

Every runtime section must provide an `evidence_ref` pointing to an immutable external object or evidence-ledger record. References should include or resolve to a SHA-256 digest. Timestamps must be UTC and evidence retention must exceed the audit window.

## Production GO

`PRODUCTION_GO` is permitted only when PostgreSQL, PITR, OpenBao, OTLP, provider and revenue-channel runtime evidence are verified; external settlement and destination are verified; cost attribution is complete; telemetry coverage is at least 0.95; duplicate settlements are zero; at least three independent windows are net-positive; and unauthorized financial actions, provider writes and probabilistic critical authorizations are all zero.

The certification command is:

```bash
python scripts/certify_production_evidence.py /path/to/evidence.json "$EXPECTED_SHA" /tmp/certificate.json
```

A nonzero exit is intentional when evidence is incomplete.

## 2026 source baseline

- PostgreSQL 18 continuous archiving and PITR: https://www.postgresql.org/docs/18/continuous-archiving.html
- OpenBao Kubernetes auth: https://openbao.org/docs/auth/kubernetes/
- OpenBao Agent Kubernetes auto-auth: https://openbao.org/docs/agent-and-proxy/autoauth/methods/kubernetes/
- OpenTelemetry Collector security: https://opentelemetry.io/docs/security/
- PayPal Transaction Search: https://developer.paypal.com/api/transaction-search/v1/search-get/
