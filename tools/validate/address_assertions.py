#!/usr/bin/env python3
"""T02生成監査を再計算し、tracked policyと既存reportの完全一致を検証する。"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
for candidate in (ROOT, ROOT / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from common import sha256_file  # noqa: E402
from generate_t02_audit import AuditError, generate  # noqa: E402


def validate_existing_reports(policy_path: Path) -> dict[str, object]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    expected_paths = [ROOT / str(value) for value in policy["outputs"]]
    for path in expected_paths:
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise AuditError(f"missing/non-regular T02 report: {path.relative_to(ROOT)}")
    with tempfile.TemporaryDirectory(prefix="t02-address-assertions-") as temporary:
        generated = Path(temporary) / "reports"
        result = generate(ROOT, policy_path, generated)
        mismatches: list[str] = []
        for expected in expected_paths:
            actual = generated / expected.name
            if expected.read_bytes() != actual.read_bytes():
                mismatches.append(expected.relative_to(ROOT).as_posix())
        if mismatches:
            raise AuditError(f"stale/non-deterministic T02 reports: {mismatches}")

    address_path = ROOT / "reports/generated/address_audit.csv"
    with address_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    allowed = set(policy["classifications"])
    counts: dict[str, int] = {value: 0 for value in policy["classifications"]}
    for number, row in enumerate(rows, 2):
        classification = row.get("classification", "")
        if classification not in allowed:
            raise AuditError(f"address_audit.csv:{number}: invalid classification")
        if not row.get("classification_evidence", "").strip():
            raise AuditError(f"address_audit.csv:{number}: missing classification evidence")
        counts[classification] += 1
        if classification == "UNKNOWN" and (
            not row.get("evidence", "").strip()
            or row.get("followup_task")
            not in set(policy["unknown_contract"]["allowed_followups"])
        ):
            raise AuditError(f"address_audit.csv:{number}: incomplete UNKNOWN")

    qol_path = ROOT / "reports/generated/qol_hook_inventory.csv"
    with qol_path.open(encoding="utf-8", newline="") as handle:
        qol_rows = list(csv.DictReader(handle))
    required_domains = {str(value) for value in policy["qol_required_domains"]}
    if {str(row.get("domain", "")) for row in qol_rows} != required_domains:
        raise AuditError("QOL report domain coverage mismatch")
    exact_domains: set[str] = set()
    contract_domains: set[str] = set()
    for number, row in enumerate(qol_rows, 2):
        domain = str(row["domain"])
        if row.get("classification") == "UNKNOWN":
            raise AuditError(f"qol_hook_inventory.csv:{number}: UNKNOWN classification")
        if row.get("status") == "FIXED_WRITE_EXACT_VEGA_BYTES":
            if not re.fullmatch(r"[0-9a-f]{64}", row.get("vega_expected_sha256", "")):
                raise AuditError(f"qol_hook_inventory.csv:{number}: invalid Vega hash")
            exact_domains.add(domain)
        elif row.get("vega_expected_sha256") == "NOT_APPLICABLE_NON_ROM_CONTRACT":
            contract_domains.add(domain)
        else:
            raise AuditError(f"qol_hook_inventory.csv:{number}: incomplete QOL evidence")
    if exact_domains != required_domains or contract_domains != required_domains:
        raise AuditError("every QOL domain needs exact writes and a non-ROM contract")

    inventory = json.loads(
        (ROOT / "reports/generated/id_inventory.json").read_text(encoding="utf-8")
    )
    maps = inventory.get("map_details", [])
    encounters = inventory.get("encounter_details", [])
    trainers = inventory.get("trainer_details", [])
    graph = inventory.get("script_graph", {})
    if len(maps) != policy["maps"]["expected_physical_map_count"]:
        raise AuditError("id_inventory map detail count mismatch")
    if len({int(row["group"]) for row in maps}) != policy["maps"]["expected_group_count"]:
        raise AuditError("id_inventory map group count mismatch")
    if len(encounters) != policy["encounters"]["expected_header_count"]:
        raise AuditError("id_inventory encounter detail count mismatch")
    expected_slots = {"land": 12, "water": 5, "rock": 5, "fishing": 10}
    for habitat in encounters:
        for name, table in habitat["tables"].items():
            if table is not None and len(table["slots"]) != expected_slots[name]:
                raise AuditError(f"encounter slot count mismatch: {name}")
    if len(trainers) != int(policy["ids"]["vega_trainer_table"]["count"]):
        raise AuditError("id_inventory trainer detail count mismatch")
    if int(graph.get("root_count", 0)) <= 0 or int(graph.get("visited_script_count", 0)) <= 0:
        raise AuditError("id_inventory rooted script graph is empty")
    if len(graph.get("nodes", [])) != int(graph["visited_script_count"]):
        raise AuditError("id_inventory visited script count mismatch")
    unlock = inventory.get("early_unlock", {})
    if (
        unlock.get("required_flags") != policy["early_unlock"]["required_flags"]
        or unlock.get("operator") != "AND"
        or unlock.get("validated") is not True
    ):
        raise AuditError("id_inventory early unlock contract mismatch")
    travel = inventory.get("map_contract", {}).get("travel_state", {})
    if travel.get("map_id_abi", {}).get("physical_max") != 126:
        raise AuditError("id_inventory travel ABI mismatch")
    return {
        "schema_version": 1,
        "status": "PASS",
        "policy_sha256": sha256_file(policy_path),
        "report_count": len(expected_paths),
        "address_rows": len(rows),
        "qol_rows": len(qol_rows),
        "map_details": len(maps),
        "encounter_details": len(encounters),
        "trainer_details": len(trainers),
        "script_graph_nodes": len(graph["nodes"]),
        "classification_counts": counts,
        "report_hashes": result["outputs"],
    }


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--policy",
        type=Path,
        default=ROOT / "config/t02_audit_policy.json",
    )
    return cli


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = validate_existing_reports(args.policy)
    except (AuditError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("ADDRESS_ASSERTIONS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
