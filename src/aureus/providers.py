from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ProviderCapabilities:
    machine_read: bool
    billing_read: bool
    machine_write: bool = False
    billing_write: bool = False


class VastObserver:
    """Read-only Vast observer. No mutation methods are exposed."""

    capabilities = ProviderCapabilities(machine_read=True, billing_read=True)

    def __init__(self, api_key: str, base_url: str = "https://console.vast.ai/api/v0") -> None:
        self._client = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=20.0)

    def machines(self) -> Any:
        return self._client.get("/machines/", params={"owner": "me"}).raise_for_status().json()

    def earnings(self, machine_id: str) -> Any:
        return self._client.get(f"/machines/{machine_id}/earnings/").raise_for_status().json()


class RunPodObserver:
    """Observer-only RunPod integration for capability and cost discovery."""

    def __init__(self, api_key: str, base_url: str = "https://rest.runpod.io/v1") -> None:
        self._client = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=20.0)

    def gpu_types(self) -> Any:
        return self._client.get("/gpuTypes").raise_for_status().json()
