from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from aureus import api
from aureus.cli import main
from aureus.domain import CostBreakdown, Opportunity
from aureus.orchestrator import RevenueSupervisor
from aureus.policy import PolicyContext
from aureus.providers import RunPodObserver, VastObserver
from aureus.runtime import read_secret
from aureus.settlement import PayPalTransactionSearch


class _Response:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> _Response:
        return self

    def json(self) -> object:
        return self._payload


class _Client:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def get(self, path: str, params: object = None) -> _Response:
        self.calls.append((path, params))
        return _Response({"ok": True})


def test_health_endpoints_are_fail_closed() -> None:
    client = TestClient(api.app)
    assert client.get("/health/live").json() == {"live": True}
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"ready": False}


def test_cli_renders_policy(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    out = capsys.readouterr().out
    assert '"agent": "AUREUS-2026"' in out
    assert '"financial_execution_enabled": false' in out


def test_supervisor_ranks_by_expected_net() -> None:
    low = Opportunity(
        "test",
        "low",
        Decimal(5),
        Decimal(1),
        Decimal(1),
        CostBreakdown(energy=Decimal(4)),
        True,
        True,
        True,
        True,
    )
    high = Opportunity(
        "test",
        "high",
        Decimal(10),
        Decimal(1),
        Decimal(1),
        CostBreakdown(energy=Decimal(1)),
        True,
        True,
        True,
        True,
    )
    ranked = RevenueSupervisor().rank([low, high], PolicyContext())
    assert [item.opportunity.resource_id for item in ranked] == ["high", "low"]


def test_secret_file_is_required_and_read(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("TOKEN_FILE", raising=False)
    with pytest.raises(RuntimeError, match="TOKEN_FILE"):
        read_secret("TOKEN")
    path = tmp_path / "token"
    path.write_text("abc\n", encoding="utf-8")
    monkeypatch.setenv("TOKEN_FILE", str(path))
    assert read_secret("TOKEN") == "abc"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="empty"):
        read_secret("TOKEN")


def test_vast_observer_read_methods_only() -> None:
    observer = VastObserver("dummy")
    fake = _Client()
    observer._client = fake  # type: ignore[assignment]
    assert observer.machines() == {"ok": True}
    assert observer.earnings("m1") == {"ok": True}
    assert fake.calls[0][0] == "/machines/"
    assert fake.calls[1][0] == "/machines/m1/earnings/"


def test_runpod_observer_is_read_only() -> None:
    observer = RunPodObserver("dummy")
    fake = _Client()
    observer._client = fake  # type: ignore[assignment]
    assert observer.gpu_types() == {"ok": True}
    assert fake.calls == [("/gpuTypes", None)]


def test_paypal_transaction_search_uses_get() -> None:
    source = PayPalTransactionSearch("dummy")
    fake = _Client()
    source._client = fake  # type: ignore[assignment]
    assert source.transactions("2026-08-01T00:00:00Z", "2026-08-02T00:00:00Z") == {"ok": True}
    path, params = fake.calls[0]
    assert path == "/transactions"
    assert params == {
        "start_date": "2026-08-01T00:00:00Z",
        "end_date": "2026-08-02T00:00:00Z",
        "fields": "all",
    }
