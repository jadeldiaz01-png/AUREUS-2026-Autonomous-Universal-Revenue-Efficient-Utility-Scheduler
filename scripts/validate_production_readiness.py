import json
from pathlib import Path

p = Path("config/production-readiness.json")
data = json.loads(p.read_text(encoding="utf-8"))
gates = data.get("gates") or {}
blockers = data.get("blockers") or []
decision = data.get("decision")

if data.get("schema_version") != "1.0.0":
    raise SystemExit("AUREUS_READINESS=FAIL unsupported schema")
if decision not in {"BLOCKED", "CONDITIONAL", "PRODUCTION_GO"}:
    raise SystemExit("AUREUS_READINESS=FAIL invalid decision")
if not gates or any(type(v) is not bool for v in gates.values()):
    raise SystemExit("AUREUS_READINESS=FAIL gates must be booleans")
if decision == "PRODUCTION_GO":
    if blockers or not all(gates.values()):
        raise SystemExit("AUREUS_READINESS=FAIL unsafe production promotion")
else:
    if not blockers:
        raise SystemExit("AUREUS_READINESS=FAIL non-production state requires blockers")

print(f"AUREUS_READINESS=PASS decision={decision} gates={sum(gates.values())}/{len(gates)}")
