from __future__ import annotations

import json
from pathlib import Path


def test_p0_r1_contract_is_fail_closed() -> None:
    contract = json.loads(Path("config/p0-r1-runtime-contract.json").read_text(encoding="utf-8"))
    assert contract["default_decision"] == "NO_GO"
    assert contract["execution_location"] == "AUTHORIZED_SELF_HOSTED_RUNTIME"
    assert contract["artifact_policy"]["raw_artifacts_must_not_be_committed"] is True
    assert contract["artifact_policy"]["raw_artifacts_must_not_be_uploaded_from_public_repository"] is True
    assert contract["runtime_gates"]["pitr_named_restore_point_drill"] is True
    assert contract["runtime_gates"]["openbao_kubernetes_workload_identity"] is True
    assert contract["runtime_gates"]["otlp_trace_roundtrip"] is True
    assert contract["economic_gates"]["minimum_independent_positive_windows"] == 3
    assert contract["authority_gates"]["unauthorized_financial_actions"] == 0
    assert contract["authority_gates"]["unauthorized_provider_writes"] == 0


def test_activation_workflow_stays_on_protected_self_hosted_runtime() -> None:
    workflow = Path(".github/workflows/p0-r1-real-infrastructure-activation.yml").read_text(encoding="utf-8")
    assert "runs-on: [self-hosted, linux, aureus-production-runtime]" in workflow
    assert "environment: aureus-production-runtime" in workflow
    assert "persist-credentials: false" in workflow
    assert "ref: ${{ inputs.expected_sha }}" in workflow
    assert "actions/upload-artifact" not in workflow
    assert "AUREUS_PRODUCTION_EVIDENCE_JSON" not in workflow
    assert "OPENBAO_TOKEN" in workflow
    assert "VAULT_TOKEN" in workflow


def test_activation_script_requires_real_artifacts() -> None:
    script = Path("scripts/p0_r1_activate.sh").read_text(encoding="utf-8")
    for artifact in (
        "openbao.json",
        "pitr.json",
        "otel-roundtrip.json",
        "provider.json",
        "production-evidence.json",
    ):
        assert artifact in script
    assert "scripts/verify_openbao_identity.py" in script
    assert "scripts/collect_runtime_evidence.py" in script
    assert "scripts/certify_production_evidence.py" in script
