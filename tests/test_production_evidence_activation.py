from __future__ import annotations

import importlib.util
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "certify_production_evidence", Path("scripts/certify_production_evidence.py")
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
certify = MODULE.certify


def bundle() -> dict[str, object]:
    runtime = {
        key: {"verified": True, "evidence_ref": f"evidence://{key}/sha256:abc"}
        for key in ("postgresql", "pitr", "openbao", "otel", "provider", "revenue_channel")
    }
    windows = [
        {
            "settlement_verified": True,
            "costs_complete": True,
            "verified_net_cash_settled_usd": "1.00",
            "evidence_ref": f"evidence://window/{i}/sha256:def",
        }
        for i in range(3)
    ]
    return {
        "schema_version": "1.0.0",
        "source_commit_sha": "a" * 40,
        "runtime": runtime,
        "economics": {
            "external_settlement_verified": True,
            "external_destination_verified": True,
            "cost_attribution_complete": True,
            "unresolved_attributable_costs": 0,
            "telemetry_coverage": 0.99,
            "duplicate_settlements": 0,
            "windows": windows,
        },
        "authority": {
            "unauthorized_financial_actions": 0,
            "unauthorized_provider_writes": 0,
            "probabilistic_critical_authorizations": 0,
        },
    }


def test_go_requires_all_real_evidence_contracts() -> None:
    data = bundle()
    result = certify(data, "a" * 40)
    assert result["decision"] == "PRODUCTION_GO"
    assert result["runtime_verified"] is True
    assert result["economically_verified"] is True
    assert len(result["certificate_sha256"]) == 64


def test_missing_pitr_fails_closed() -> None:
    data = bundle()
    data["runtime"]["pitr"]["verified"] = False  # type: ignore[index]
    result = certify(data, "a" * 40)
    assert result["decision"] == "NO_GO"
    assert "runtime_pitr_not_verified" in result["blockers"]


def test_two_windows_are_insufficient() -> None:
    data = bundle()
    data["economics"]["windows"] = data["economics"]["windows"][:2]  # type: ignore[index]
    result = certify(data, "a" * 40)
    assert result["decision"] == "NO_GO"
    assert "fewer_than_three_windows" in result["blockers"]


def test_commit_mismatch_fails_closed() -> None:
    result = certify(bundle(), "b" * 40)
    assert result["decision"] == "NO_GO"
    assert "source_commit_mismatch" in result["blockers"]


def test_unresolved_cost_or_unauthorized_action_blocks_go() -> None:
    data = bundle()
    data["economics"]["unresolved_attributable_costs"] = 1  # type: ignore[index]
    data["authority"]["unauthorized_financial_actions"] = 1  # type: ignore[index]
    result = certify(data, "a" * 40)
    assert result["decision"] == "NO_GO"
    assert "unresolved_costs" in result["blockers"]
    assert "unauthorized_financial_actions" in result["blockers"]
