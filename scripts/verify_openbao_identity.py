from __future__ import annotations

import json
import os
from pathlib import Path

import httpx


def main() -> None:
    if "OPENBAO_TOKEN" in os.environ or "VAULT_TOKEN" in os.environ:
        raise SystemExit("OPENBAO_IDENTITY=FAIL static token environment variable present")

    proxy = os.environ.get("AUREUS_OPENBAO_AGENT_URL", "http://127.0.0.1:8100")
    expected_policy = os.environ.get("AUREUS_OPENBAO_POLICY", "aureus-runtime-observer")
    output = Path(os.environ.get("AUREUS_OPENBAO_EVIDENCE_FILE", "/run/evidence/openbao.json"))

    response = httpx.get(f"{proxy}/v1/auth/token/lookup-self", timeout=10.0)
    response.raise_for_status()
    data = response.json().get("data") or {}
    policies = set(data.get("policies") or [])
    ttl = int(data.get("ttl") or 0)

    verified = expected_policy in policies and ttl > 0
    payload = {
        "workload_identity_verified": verified,
        "static_token_forbidden": True,
        "short_lived_credential_verified": ttl > 0,
        "expected_policy_present": expected_policy in policies,
        "ttl_seconds_observed": ttl,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OPENBAO_IDENTITY={'PASS' if verified else 'FAIL'}")
    if not verified:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
