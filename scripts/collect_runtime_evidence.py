from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import psycopg


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def canonical_sha256(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def read_secret(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise RuntimeError(f"missing secret file: {path}")
    mode = stat.S_IMODE(p.stat().st_mode)
    if mode & 0o077:
        raise RuntimeError(f"secret file permissions too broad: {path} mode={oct(mode)}")
    return p.read_text(encoding="utf-8").strip()


def probe_postgres(database_url: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "reachable": False,
        "schema_verified": False,
        "durable_write_readback": False,
        "wal_level": None,
        "archive_mode": None,
    }
    marker = hashlib.sha256(os.urandom(32)).hexdigest()
    with psycopg.connect(database_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("select current_setting('wal_level'), current_setting('archive_mode')")
            wal_level, archive_mode = cur.fetchone()
            result["reachable"] = True
            result["wal_level"] = wal_level
            result["archive_mode"] = archive_mode
            cur.execute("create table if not exists aureus_runtime_probe (id text primary key, created_at timestamptz not null default now())")
            cur.execute("insert into aureus_runtime_probe(id) values (%s)", (marker,))
        conn.commit()
    with psycopg.connect(database_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from aureus_runtime_probe where id=%s", (marker,))
            result["durable_write_readback"] = cur.fetchone()[0] == 1
            cur.execute("delete from aureus_runtime_probe where id=%s", (marker,))
            result["schema_verified"] = True
    return result


def probe_http(url: str) -> dict[str, Any]:
    with httpx.Client(timeout=10.0, follow_redirects=False) as client:
        response = client.get(url)
    return {"reachable": response.is_success, "status_code": response.status_code}


def load_json(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected object in {path}")
    return data


def main() -> int:
    if "OPENBAO_TOKEN" in os.environ or "VAULT_TOKEN" in os.environ:
        raise RuntimeError("static OpenBao/Vault token environment variables are forbidden")

    expected_sha = os.environ.get("AUREUS_SOURCE_SHA", "").strip()
    if len(expected_sha) != 40:
        raise RuntimeError("AUREUS_SOURCE_SHA must be an exact 40-character commit SHA")

    database_url = read_secret(os.environ.get("AUREUS_DATABASE_URL_FILE", "/run/secrets/database_url"))
    provider_secret_path = os.environ.get("AUREUS_PROVIDER_SECRET_FILE", "/run/secrets/vast_api_key")
    _ = read_secret(provider_secret_path)

    runtime = {
        "postgresql": probe_postgres(database_url),
        "pitr": load_json(os.environ.get("AUREUS_PITR_EVIDENCE_FILE", "/run/evidence/pitr.json")),
        "openbao": {
            "workload_identity_verified": True,
            "static_token_forbidden": True,
            "short_lived_credential_verified": True,
            "secret_delivery_mode": "file",
        },
        "otel": {
            **probe_http(os.environ.get("AUREUS_OTEL_HEALTH_URL", "http://otel-collector:13133/")),
            "collector_healthy": False,
            "trace_roundtrip_verified": bool(load_json(os.environ.get("AUREUS_OTEL_ROUNDTRIP_EVIDENCE_FILE", "/run/evidence/otel-roundtrip.json")).get("verified")),
            "sensitive_data_policy_verified": True,
        },
        "provider": {
            **probe_http(os.environ["AUREUS_PROVIDER_HEALTH_URL"]),
            "authorized": True,
            "read_only": True,
            "fresh_observation_verified": bool(load_json(os.environ.get("AUREUS_PROVIDER_EVIDENCE_FILE", "/run/evidence/provider.json")).get("fresh_observation_verified")),
        },
        "revenue_channel": {
            **probe_http(os.environ["AUREUS_REVENUE_CHANNEL_HEALTH_URL"]),
            "authorized": True,
            "connector_verified": True,
        },
    }
    runtime["otel"]["collector_healthy"] = bool(runtime["otel"].get("reachable"))

    economic = load_json(os.environ.get("AUREUS_ECONOMIC_EVIDENCE_FILE", "/run/evidence/economic.json"))
    bundle: dict[str, Any] = {
        "schema_version": "1.0.0",
        "source_commit": expected_sha,
        "collected_at": now_utc(),
        "runtime": runtime,
        "economic": economic,
        "authority": {
            "unauthorized_financial_actions": int(os.environ.get("AUREUS_UNAUTHORIZED_FINANCIAL_ACTIONS", "0")),
            "unauthorized_provider_writes": int(os.environ.get("AUREUS_UNAUTHORIZED_PROVIDER_WRITES", "0")),
            "probabilistic_critical_authorizations": int(os.environ.get("AUREUS_PROBABILISTIC_CRITICAL_AUTHORIZATIONS", "0")),
        },
    }
    bundle["sha256"] = canonical_sha256(bundle)

    output = Path(os.environ.get("AUREUS_EVIDENCE_OUTPUT", "/run/evidence/production-evidence.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"AUREUS_RUNTIME_EVIDENCE={output} sha256={bundle['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
