# Production gates

## Engineering gate

Ruff, mypy, tests, migrations, policy invariants, SBOM/provenance and restore drill must be green on one exact SHA.

## Runtime gate — `AGENT_RUNNING`

Requires persistent PostgreSQL, verified backup/restore, OpenBao workload identity, healthy OTLP pipeline, provider observer certification, fresh provider telemetry, fresh hardware telemetry, durable evidence persistence and `/health/ready = 200`.

## Economic gate — `P4E_ECONOMICALLY_DEMONSTRATED`

Requires independently verified destination settlement, >=95% telemetry coverage, full-host/conservative verified power scope, all attributable costs resolved, unique settlement references and `VERIFIED_NET_CASH_SETTLED > 0`.

## Production GO

Internal conservative policy requires at least three independent positive settlement windows before declaring sustainable production readiness. This is an AUREUS governance rule, not a provider requirement.
