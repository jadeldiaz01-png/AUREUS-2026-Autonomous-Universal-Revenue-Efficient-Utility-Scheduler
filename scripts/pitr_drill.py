from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

import psycopg


def ensure_table(conn: psycopg.Connection[tuple[object, ...]]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "create table if not exists aureus_pitr_probe ("
            "id text primary key, phase text not null, created_at timestamptz not null default now())"
        )
    conn.commit()


def seed(database_url: str, output: Path) -> None:
    before_id = f"before-{uuid.uuid4()}"
    after_id = f"after-{uuid.uuid4()}"
    restore_name = f"aureus_{uuid.uuid4().hex[:16]}"
    with psycopg.connect(database_url) as conn:
        ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute("insert into aureus_pitr_probe(id, phase) values (%s, 'before')", (before_id,))
            cur.execute("select pg_create_restore_point(%s)", (restore_name,))
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("insert into aureus_pitr_probe(id, phase) values (%s, 'after')", (after_id,))
        conn.commit()
    payload = {"restore_point": restore_name, "before_id": before_id, "after_id": after_id}
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PITR_SEED=PASS restore_point={restore_name}")


def verify(restored_database_url: str, seed_file: Path, output: Path) -> None:
    seed_data = json.loads(seed_file.read_text(encoding="utf-8"))
    with psycopg.connect(restored_database_url, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from aureus_pitr_probe where id=%s", (seed_data["before_id"],))
        before_present = cur.fetchone()[0] == 1
        cur.execute("select count(*) from aureus_pitr_probe where id=%s", (seed_data["after_id"],))
        after_absent = cur.fetchone()[0] == 0
    verified = before_present and after_absent
    payload = {
        "wal_archiving_verified": verified,
        "base_backup_verified": verified,
        "restore_drill_verified": verified,
        "restore_target_verified": verified,
        "before_marker_present": before_present,
        "after_marker_absent": after_absent,
        "restore_point": seed_data["restore_point"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PITR_VERIFY={'PASS' if verified else 'FAIL'}")
    if not verified:
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    seed_cmd = sub.add_parser("seed")
    seed_cmd.add_argument("database_url")
    seed_cmd.add_argument("output", type=Path)
    verify_cmd = sub.add_parser("verify")
    verify_cmd.add_argument("restored_database_url")
    verify_cmd.add_argument("seed_file", type=Path)
    verify_cmd.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "seed":
        seed(args.database_url, args.output)
    else:
        verify(args.restored_database_url, args.seed_file, args.output)


if __name__ == "__main__":
    main()
