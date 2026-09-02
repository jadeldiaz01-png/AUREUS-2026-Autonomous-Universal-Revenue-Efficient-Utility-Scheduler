# AUREUS P0-R1 Real Infrastructure Activation

This runbook is the bridge from `IMPLEMENTED` to `RUNTIME_VERIFIED`. It must execute on the actual authorized VPS or Kubernetes runtime, not on a generic GitHub-hosted runner.

## Production runner

Register an isolated Linux GitHub Actions self-hosted runner with the label `aureus-production-runtime`. Prefer an ephemeral/JIT runner or a dedicated machine that is cleaned between jobs. The runner must have access only to the production namespace and evidence paths required by AUREUS. Do not place repository, OpenBao, provider or settlement secrets in the runner registration command or repository files.

The protected GitHub Environment `aureus-production-runtime` should require manual approval and should contain only non-secret configuration variables such as provider/revenue health URLs. Runtime credentials remain delivered by OpenBao or the host secret mechanism.

## Prerequisites on the authorized runtime

- Python 3.12+ with the AUREUS package dependencies installed.
- `kubectl` configured for the intended cluster and namespace `aureus`.
- PostgreSQL 18 reachable only from the authorized runtime network.
- WAL archiving already enabled and tested before the base backup.
- OpenBao 2.6.x reachable from the cluster and Kubernetes auth configured for ServiceAccount `aureus-runtime`.
- OpenTelemetry Collector deployed and reachable on cluster-private ports.
- Provider and revenue connector health endpoints authorized and read-only where required.
- `/run/secrets` memory-backed or equivalent protected secret storage.
- `/run/evidence` writable only by the activation identity.

## Evidence sequence

1. Deploy the exact signed AUREUS image digest associated with the SHA being certified.
2. Confirm PostgreSQL durable write/readback and WAL settings.
3. Run `scripts/pitr_drill.py seed` on the primary.
4. Restore an isolated disposable PostgreSQL clone from a real base backup and WAL archive to the named restore point.
5. Run `scripts/pitr_drill.py verify` against that clone to create `/run/evidence/pitr.json`.
6. Verify OpenBao workload identity through the local Auto-Auth proxy; this creates `/run/evidence/openbao.json` without exposing the token.
7. Send a uniquely identified synthetic trace through OTLP, verify it exists in the configured backend, and create `/run/evidence/otel-roundtrip.json`.
8. Run the approved provider observer and create `/run/evidence/provider.json` with authorization, read-only authority and freshness evidence.
9. Run the approved revenue-channel connector and create `/run/evidence/revenue-channel.json`.
10. For runtime-only certification, economic evidence remains fail-closed. For economic promotion, add externally reconciled settlement/cost evidence in `/run/evidence/economic.json`.
11. Execute `scripts/p0_r1_activate.sh`. It creates `production-evidence.json`, invokes the certifier and creates `production-certificate.json`.

## GitHub workflow

Dispatch `.github/workflows/p0-r1-real-infrastructure-activation.yml` with the exact deployed 40-character commit SHA. The job only schedules on `[self-hosted, linux, aureus-production-runtime]` and uses the protected `aureus-production-runtime` Environment.

Raw evidence is intentionally not uploaded as a public-repository Actions artifact. The workflow prints only a sanitized certificate summary containing gate results and SHA-256 hashes, then removes JSON evidence files from `/run/evidence` at job completion. Durable evidence should be retained in the approved private evidence store outside this repository before cleanup.

## Promotion semantics

`RUNTIME_VERIFIED` requires real target-environment evidence for PostgreSQL, PITR, OpenBao, OTLP, provider and revenue connector. Configuration files, screenshots, mocked probes and CI success do not qualify.

`ECONOMICALLY_VERIFIED` additionally requires external settlement and destination verification, complete attributable costs, telemetry coverage >= 0.95, no duplicate settlements and at least three independent windows with `VERIFIED_NET_CASH_SETTLED_USD > 0`.

`PRODUCTION_GO` additionally requires zero unauthorized financial actions, zero unauthorized provider writes and zero critical authorizations based solely on probabilistic AI output.

Any missing, stale, ambiguous or contradictory evidence produces `NO_GO`.
