# AUREUS-2026 Production Runtime Bring-Up

This runbook moves evidence from `IMPLEMENTED` to `RUNTIME_VERIFIED`. It does not authorize financial writes and it does not imply `PRODUCTION_GO`.

## Supported baseline

- PostgreSQL 18 with `wal_level=replica`, continuous WAL archiving, base backups and a destructive PITR restore drill.
- OpenBao 2.6.x using Kubernetes ServiceAccount Auto-Auth. Static `OPENBAO_TOKEN`/`VAULT_TOKEN` variables are forbidden.
- OpenTelemetry Collector deployed as a managed Kubernetes component with health check, memory limiter, persistent sending queue and retry.
- Provider and revenue connectors are read-only/authorized until separately promoted.
- Raw runtime/economic evidence stays outside the public repository.

## 1. PostgreSQL

1. Create separate roles for migrations, runtime application and backup/replication.
2. Apply `infra/postgres/postgresql.prod.conf` after substituting a durable WAL archive destination.
3. Require TLS and SCRAM authentication; do not expose PostgreSQL publicly.
4. Verify `show wal_level` is `replica` or `logical`, `show archive_mode` is `on`/`always`, and archived WAL segments are advancing.
5. Take a physical base backup after WAL archiving is confirmed.
6. Run `scripts/pitr_drill.py seed` against the primary. Record the named restore point.
7. Restore a disposable clone from the base backup plus archived WAL to that exact named restore point.
8. Run `scripts/pitr_drill.py verify` against the restored clone. The before-marker must exist and the after-marker must not exist. Only that output may set the PITR gate true.

A logical `pg_dump` is useful for other recovery scenarios but is not PITR evidence.

## 2. OpenBao workload identity

1. Run OpenBao 2.6.x in HA-capable storage for production. Do not use the deprecated file storage backend.
2. Enable Kubernetes auth and bind role `aureus-runtime-observer` only to ServiceAccount `aureus-runtime` in namespace `aureus`.
3. Install policy `infra/openbao/aureus-runtime-observer.hcl`.
4. Mount `infra/openbao/agent.hcl` into an OpenBao Agent sidecar.
5. Secret files live in a memory-backed volume and are mode `0400`.
6. Run `scripts/verify_openbao_identity.py` inside the pod. It queries the local Agent API proxy; the proxy forces the Auto-Auth token, so the application never handles a static token.
7. Persist only the sanitized `/run/evidence/openbao.json` artifact, never the token or secret values.

## 3. OpenTelemetry

1. Deploy the Collector using the official Helm chart or Operator, with the reviewed `infra/otel/collector.yaml` as the configuration baseline.
2. Pin the exact Collector container digest during promotion.
3. Keep OTLP ingress cluster-private and restrict it with NetworkPolicy.
4. Health must answer on `:13133`.
5. Send a synthetic AUREUS trace and query the configured observability backend for the exact trace identifier. Persist only a sanitized result `{verified:true,sensitive_data_policy_verified:true,...}` to `/run/evidence/otel-roundtrip.json`.
6. No credentials, settlement IDs or full request bodies may be exported as telemetry attributes.

## 4. Provider and revenue channel

Provider and revenue connectors must each produce a sanitized evidence file proving:

- authorization is current;
- connector is operating through an approved API/MCP path;
- provider authority is read-only where required;
- observation is fresh;
- health endpoint succeeds.

These assertions are not inferred from configuration files.

## 5. Runtime evidence collection

Set the exact deployed source commit in `AUREUS_SOURCE_SHA`, configure the runtime health URLs and evidence file paths, then run:

```bash
python scripts/verify_openbao_identity.py
python scripts/collect_runtime_evidence.py
```

`collect_runtime_evidence.py` performs a committed PostgreSQL write/readback, verifies WAL settings, consumes the independent PITR/OpenBao/OTLP/provider/channel artifacts and generates `/run/evidence/production-evidence.json`. It never writes database URLs or provider keys into the evidence bundle.

## 6. Certification

Copy the resulting raw bundle into the protected `aureus-production-readiness` GitHub Environment secret or an equivalent protected runner input and dispatch `production-gate` with the exact 40-character SHA.

The certifier returns `NO_GO` unless all runtime sections are verified. `PRODUCTION_GO` additionally requires externally settled cash, complete attributable costs, telemetry coverage >= 0.95, zero duplicate settlements, zero unauthorized actions and at least three independent positive economic windows.

## 7. Rollback / incident response

- Any identity, database, telemetry, provider or settlement uncertainty forces readiness to false.
- Revoke the OpenBao role/token lease and provider credential on suspected compromise.
- Stop revenue execution before diagnosis if evidence integrity is uncertain.
- Restore from a verified PITR chain, not from an untested backup.
- Re-run the full evidence collection after recovery; old certificates do not certify a new runtime state.
