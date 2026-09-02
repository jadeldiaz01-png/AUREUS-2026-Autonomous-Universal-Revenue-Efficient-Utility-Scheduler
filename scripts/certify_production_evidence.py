from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def require(value: bool, reason: str, blockers: list[str]) -> None:
    if not value:
        blockers.append(reason)


def certify(bundle: dict[str, Any], expected_sha: str) -> dict[str, Any]:
    blockers: list[str] = []
    require(bundle.get("schema_version") == "1.0.0", "unsupported_schema", blockers)
    require(bundle.get("source_commit_sha") == expected_sha, "source_commit_mismatch", blockers)

    runtime = bundle.get("runtime") or {}
    for key in ("postgresql", "pitr", "openbao", "otel", "provider", "revenue_channel"):
        section = runtime.get(key) or {}
        require(section.get("verified") is True, f"runtime_{key}_not_verified", blockers)
        require(bool(section.get("evidence_ref")), f"runtime_{key}_evidence_missing", blockers)

    economics = bundle.get("economics") or {}
    require(economics.get("external_settlement_verified") is True, "external_settlement_not_verified", blockers)
    require(economics.get("external_destination_verified") is True, "external_destination_not_verified", blockers)
    require(economics.get("cost_attribution_complete") is True, "cost_attribution_incomplete", blockers)
    require(int(economics.get("unresolved_attributable_costs", -1)) == 0, "unresolved_costs", blockers)
    require(Decimal(str(economics.get("telemetry_coverage", 0))) >= Decimal("0.95"), "telemetry_coverage_below_0_95", blockers)
    require(int(economics.get("duplicate_settlements", -1)) == 0, "duplicate_settlements", blockers)

    windows = economics.get("windows") or []
    require(len(windows) >= 3, "fewer_than_three_windows", blockers)
    for i, window in enumerate(windows):
        require(window.get("settlement_verified") is True, f"window_{i}_settlement_not_verified", blockers)
        require(window.get("costs_complete") is True, f"window_{i}_costs_incomplete", blockers)
        net = Decimal(str(window.get("verified_net_cash_settled_usd", "0")))
        require(net > 0, f"window_{i}_net_not_positive", blockers)
        require(bool(window.get("evidence_ref")), f"window_{i}_evidence_missing", blockers)

    authority = bundle.get("authority") or {}
    require(int(authority.get("unauthorized_financial_actions", -1)) == 0, "unauthorized_financial_actions", blockers)
    require(int(authority.get("unauthorized_provider_writes", -1)) == 0, "unauthorized_provider_writes", blockers)
    require(int(authority.get("probabilistic_critical_authorizations", -1)) == 0, "probabilistic_critical_authorizations", blockers)

    decision = "PRODUCTION_GO" if not blockers else "NO_GO"
    result = {
        "schema_version": "1.0.0",
        "source_commit_sha": expected_sha,
        "decision": decision,
        "runtime_verified": not any(b.startswith("runtime_") for b in blockers),
        "economically_verified": not any(b.startswith(("external_", "cost_", "unresolved_", "telemetry_", "duplicate_", "fewer_", "window_")) for b in blockers),
        "blockers": blockers,
        "input_sha256": canonical_sha256(bundle),
    }
    result["certificate_sha256"] = canonical_sha256(result)
    return result


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: certify_production_evidence.py BUNDLE EXPECTED_SHA OUTPUT")
    bundle_path, expected_sha, output_path = sys.argv[1:]
    bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
    result = certify(bundle, expected_sha)
    Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"AUREUS_PRODUCTION_EVIDENCE={result['decision']} sha256={result['certificate_sha256']}")
    if result["decision"] != "PRODUCTION_GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
