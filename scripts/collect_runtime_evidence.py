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
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def evidence_ref(payload: dict[str, Any]) -> str:
    return f"sha256:{canonical_sha256(payload)}"


def read_secret(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise RuntimeError(f"missing secret file: {path}")
    mode = stat.S_IMODE(p.stat().st_mode)
    if mode & 0o077:
        raise RuntimeError(f"secret file permissions too broad: {path} mode={oct(mode)}")
    return p.read_text(encoding="utf-8").strip()


def load_json(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected object in {path}")
    return data


def probe_http(url: str) -> dict[str, Any]:
    with httpx.Client(timeout=10.0, follow_redirects=False) as client:
        response = client.get(url)
    return {"reachable": response.is_success, "status_code": response.status_code}


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
            cur.execute(
                "create table if not exists aureus_runtime_probe "
                "(id text primary key, created_at timestamptz not null default now())"
            )
            cur.execute("insert into aureus_runtime_probe(id) values (%s)", (marker,))
        conn.commit()
    with psycopg.connect(database_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from aureus_runtime_probe where id=%s", (marker,))
            result["durable_write_readback"] = cur.fetchone()[0] == 1
            cur.execute("delete from aureus_runtime_probe where id=%s", (marker,))
            result["schema_verified"] = True
    result["verified"] = bool(
        result["reachable"]
        and result["schema_verified"]
        and result["durable_write_readback"]
        and result["wal_level"] in {"replica", "logical"}
        and result["archive_mode"] in {"on", "always"}
    )
    result["evidence_ref"] = evidence_ref(result)
    return result


def verified_section(payload: dict[str, Any], required_true: tuple[str, ...]) -> dict[str, Any]:
    section = dict(payload)
    section["verified"] = all(section.get(key) is True for key in required_true)
    section["evidence_ref"] = evidence_ref(section)
    return section


def main() -> int:
    if "OPENBAO_TOKEN" in os.environ or "VAULT_TOKEN" in os.environ:
        raise RuntimeError("static OpenBao/Vault token environment variables are forbidden")

    expected_sha = os.environ.get("AUREUS_SOURCE_SHA", "").strip()
    if len(expected_sha) != 40:
        raise RuntimeError("AUREUS_SOURCE_SHA must be an exact 40-character commit SHA")

    database_url = read_secret(os.environ.get("AUREUS_DATABASE_URL_FILE", "/run/secrets/database_url"))
    _ = read_secret(os.environ.get("AUREUS_PROVIDER_SECRET_FILE", "/run/secrets/vast_api_key"))

    pitr = verified_section(
        load_json(os.environ.get("AUREUS_PITR_EVIDENCE_FILE", "/run/evidence/pitr.json")),
        ("wal_archiving_verified", "base_backup_verified", "restore_drill_verified", "restore_target_verified"),
    )
    openbao = verified_section(
        load_json(os.environ.get("AUREUS_OPENBAO_EVIDENCE_FILE", "/run/evidence/openbao.json")),
        ("workload_identity_verified", "static_token_forbidden", "short_lived_credential_verified"),
    )
    otel_proof = load_json(os.environ.get("AUREUS_OTEL_ROUNDTRIP_EVIDENCE_FILE", "/run/evidence/otel-roundtrip.json"))
    otel = {
        **probe_http(os.environ.get("AUREUS_OTEL_HEALTH_URL", "http://otel-collector:13133/")),
        "collector_healthy": False,
        "trace_roundtrip_verified": otel_proof.get("verified") is True,
        "sensitive_data_policy_verified": otel_proof.get("sensitive_data_policy_verified") is True,
    }
    otel["collector_healthy"] = otel["reachable"] is True
    otel = verified_section(otel, ("collector_healthy", "trace_roundtrip_verified", "sensitive_data_policy_verified"))

    provider_proof = load_json(os.environ.get("AUREUS_PROVIDER_EVIDENCE_FILE", "/run/evidence/provider.json"))
    provider = {
        **probe_http(os.environ["AUREUS_PROVIDER_HEALTH_URL"]),
        "authorized": provider_proof.get("authorized") is True,
        "read_only": provider_proof.get("read_only") is True,
        "fresh_observation_verified": provider_proof.get("fresh_observation_verified") is True,
    }
    provider = verified_section(provider, ("reachable", "authorized", "read_only", "fresh_observation_verified"))

    revenue_proof = load_json(os.environ.get("AUREUS_REVENUE_CHANNEL_EVIDENCE_FILE", "/run/evidence/revenue-channel.json"))
    revenue_channel = {
        **probe_http(os.environ["AUREUS_REVENUE_CHANNEL_HEALTH_URL"]),
        "authorized": revenue_proof.get("authorized") is True,
        "connector_verified": revenue_proof.get("connector_verified") is True,
    }
    revenue_channel = verified_section(revenue_channel, ("reachable", "authorized", "connector_verified"))

    economics = load_json(os.environ.get("AUREUS_ECONOMIC_EVIDENCE_FILE", "/run/evidence/economic.json"))
    bundle: dict[str, Any] = {
        "schema_version": "1.0.0",
        "source_commit_sha": expected_sha,
        "collected_at": now_utc(),
        "runtime": {
            "postgresql": probe_postgres(database_url),
            "pitr": pitr,
            "openbao": openbao,
            "otel": otel,
            "provider": provider,
            "revenue_channel": revenue_channel,
        },
        "economics": economics,
        "authority": {
            "unauthorized_financial_actions": int(os.environ.get("AUREUS_UNAUTHORIZED_FINANCIAL_ACTIONS", "0")),
            "unauthorized_provider_writes": int(os.environ.get("AUREUS_UNAUTHORIZED_PROVIDER_WRITES", "0")),
            "probabilistic_critical_authorizations": int(os.environ.get("AUREUS_PROBABILISTIC_CRITICAL_AUTHORIZATIONS", "0")),
        },
    }
    bundle["bundle_sha256"] = canonical_sha256(bundle)

    output = Path(os.environ.get("AUREUS_EVIDENCE_OUTPUT", "/run/evidence/production-evidence.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"AUREUS_RUNTIME_EVIDENCE={output} sha256={bundle['bundle_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
