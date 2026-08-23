from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    policy = json.loads(Path("config/aureus-policy.json").read_text(encoding="utf-8"))
    print(json.dumps({"agent": "AUREUS-2026", "policy": policy}, indent=2))
