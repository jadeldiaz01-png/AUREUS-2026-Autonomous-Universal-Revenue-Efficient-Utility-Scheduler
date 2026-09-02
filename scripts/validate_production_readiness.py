import json
from pathlib import Path

LEVELS = {"IMPLEMENTED": 0, "CI_VERIFIED": 1, "RUNTIME_VERIFIED": 2, "ECONOMICALLY_VERIFIED": 3}

p = Path("config/production-readiness.json")
data = json.loads(p.read_text(encoding="utf-8"))
blockers = data.get("blockers") or []
decision = data.get("decision")
schema = data.get("schema_version")

if schema == "1.0.0":
    gates = data.get("gates") or {}
    if decision not in {"BLOCKED", "CONDITIONAL", "PRODUCTION_GO"}:
        raise SystemExit("AUREUS_READINESS=FAIL invalid decision")
    if not gates or any(type(v) is not bool for v in gates.values()):
        raise SystemExit("AUREUS_READINESS=FAIL gates must be booleans")
    if decision == "PRODUCTION_GO" and (blockers or not all(gates.values())):
        raise SystemExit("AUREUS_READINESS=FAIL unsafe production promotion")
    if decision != "PRODUCTION_GO" and not blockers:
        raise SystemExit("AUREUS_READINESS=FAIL non-production state requires blockers")
    print(f"AUREUS_READINESS=PASS schema=1 decision={decision}")
    raise SystemExit(0)

if schema != "2.0.0":
    raise SystemExit("AUREUS_READINESS=FAIL unsupported schema")
if decision not in {"NO_GO", "CONDITIONAL_GO", "PRODUCTION_GO"}:
    raise SystemExit("AUREUS_READINESS=FAIL invalid decision")

sections = {name: data.get(name) or {} for name in ("engineering", "runtime", "economics")}
for name, section in sections.items():
    if not section:
        raise SystemExit(f"AUREUS_READINESS=FAIL missing {name}")
    for gate, level in section.items():
        if level not in LEVELS:
            raise SystemExit(f"AUREUS_READINESS=FAIL invalid level {name}.{gate}={level}")

requirements = data.get("production_go_requires") or {}
if int(requirements.get("minimum_positive_windows", 0)) < 3:
    raise SystemExit("AUREUS_READINESS=FAIL positive-window floor")
if float(requirements.get("telemetry_coverage_min", 0)) < 0.95:
    raise SystemExit("AUREUS_READINESS=FAIL telemetry coverage floor")
if int(requirements.get("unauthorized_financial_actions", 1)) != 0:
    raise SystemExit("AUREUS_READINESS=FAIL financial authority invariant")
if int(requirements.get("unauthorized_provider_writes", 1)) != 0:
    raise SystemExit("AUREUS_READINESS=FAIL provider authority invariant")

if decision == "PRODUCTION_GO":
    if blockers:
        raise SystemExit("AUREUS_READINESS=FAIL production cannot have blockers")
    if any(LEVELS[level] < LEVELS["CI_VERIFIED"] for level in sections["engineering"].values()):
        raise SystemExit("AUREUS_READINESS=FAIL engineering evidence too weak")
    if any(LEVELS[level] < LEVELS["RUNTIME_VERIFIED"] for level in sections["runtime"].values()):
        raise SystemExit("AUREUS_READINESS=FAIL runtime evidence too weak")
    if any(LEVELS[level] < LEVELS["ECONOMICALLY_VERIFIED"] for level in sections["economics"].values()):
        raise SystemExit("AUREUS_READINESS=FAIL economic evidence too weak")
else:
    if not blockers:
        raise SystemExit("AUREUS_READINESS=FAIL non-production state requires blockers")

print(
    "AUREUS_READINESS=PASS "
    f"schema=2 decision={decision} "
    f"engineering={len(sections['engineering'])} runtime={len(sections['runtime'])} economics={len(sections['economics'])}"
)
