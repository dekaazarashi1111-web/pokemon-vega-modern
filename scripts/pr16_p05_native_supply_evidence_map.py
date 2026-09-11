#!/usr/bin/env python3
"""Bind the finite P05 supply gaps to concrete source scopes and old evidence.

The prior inventory deliberately retained multiple textual roots.  This pass
turns those matches into a small source/evidence map suitable for authoring the
three missing native-play runners.  It does not mark any physical acceptance as
complete and never converts fixture-only P05 evidence into ordinary-play proof.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/pr16_p05_native_supply_evidence_map.py"
TEST = "tests/test_pr16_p05_native_supply_evidence_map.py"
WORKFLOW = ".github/workflows/pr16-p05-native-supply-evidence-map.yml"
INVENTORY = "content/modernization/pr16_p05_native_supply_reconciliation.json"
OUTPUT = "content/modernization/pr16_p05_native_supply_evidence_map.json"
DOC = "docs/PR16_P05_NATIVE_SUPPLY_EVIDENCE_MAP_CHECKPOINT_JA.md"
REMAINING = "content/modernization/p08_remaining_work.json"
PURCHASED = "content/modernization/pr16_purchased_gear_acceptance.json"
P05_ROUTE = "content/modernization/pr16_p05_route_acceptance.json"
SCOPE = "PR16_P05_NATIVE_SUPPLY_SOURCE_EVIDENCE_BINDING"

CATEGORY_TO_GAP = {
    "ring_supply": "P05_NATIVE_RING_ACQUISITION_PHYSICAL",
    "bp_earning": "P05_NATIVE_BP_EARNING_PHYSICAL",
    "policy_selection": "P05_ORDINARY_POLICY_SELECTION_PHYSICAL",
}

FIXTURE_ONLY_PATH_PARTS = (
    "pr16_purchased_gear",
    "run_modernization_p05_",
    "mgba_",
    "/tests/",
    "tests/",
)

RUNNER_CONTRACTS = {
    "ring_supply": {
        "start_boundary": "ordinary pre-ring save with no ring injected by the test",
        "required_operations": [
            "reach the authored ring supplier through normal map/event interaction",
            "accept the ring through the real give-item/flag transaction",
            "save normally, discard the emulator core, and Continue on a fresh core",
            "verify the same obtained ring state without writing inventory or flags",
        ],
        "forbidden_shortcuts": [
            "preinstall the ring before observation",
            "write the ownership flag or bag slot directly",
            "reuse purchased-stone success as proof of ring acquisition",
        ],
    },
    "bp_earning": {
        "start_boundary": "ordinary facility state with an observed BP balance and no post-observation BP injection",
        "required_operations": [
            "enter the authored BP-awarding activity through its real reception/menu",
            "finish the required battle or result path",
            "observe the real reward transaction increase BP",
            "save normally and verify the balance after cold Continue",
        ],
        "forbidden_shortcuts": [
            "seed the earned BP after observation",
            "prove only that a BP shop can spend a fixture balance",
            "call the reward helper without the ordinary facility/result path",
        ],
    },
    "policy_selection": {
        "start_boundary": "ordinary save with no next-battle policy injected after observation",
        "required_operations": [
            "reach the authored mode/policy selector through its real reception or menu",
            "choose an accepted battle mode through controller input",
            "enter the corresponding battle without a test-side policy write",
            "demonstrate the documented cold-Continue boundary and reselect normally when required",
        ],
        "forbidden_shortcuts": [
            "globally enable Mega in all battles",
            "restore the transient policy from the test after cold Continue",
            "claim controller/scheduler fixture coverage as ordinary policy selection",
        ],
    },
}

IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b")
NUMBER = re.compile(r"(?i)\b(?:0x[0-9a-f]+|\d{2,})\b")
ACTION = re.compile(
    r"(?ix)(?:give|grant|award|reward|earn|add|setvar|set_flag|shop|purchase|"
    r"menu|select|mode|policy|map|event|受付|取得|付与|報酬|獲得|選択|設定)"
)


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def identity(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def function_scope(path: Path, line_no: int) -> str:
    if path.suffix == ".py":
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            return "<module>"
        matches: list[tuple[int, int, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                end = getattr(node, "end_lineno", node.lineno)
                if node.lineno <= line_no <= end:
                    matches.append((node.lineno, end, node.name))
        if matches:
            matches.sort(key=lambda row: (row[1] - row[0], -row[0]))
            return matches[0][2]
        return "<module>"

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = max(0, line_no - 30)
    for index in range(line_no - 1, start - 1, -1):
        line = lines[index]
        match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{?\s*$", line)
        if match and match.group(1) not in {"if", "for", "while", "switch", "return"}:
            return match.group(1)
    return "<module>"


def source_context(row: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / row["path"]
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    line_no = row["line"]
    lo = max(1, line_no - 5)
    hi = min(len(lines), line_no + 5)
    block = "\n".join(lines[lo - 1 : hi])
    identifiers = sorted(set(IDENTIFIER.findall(block)))[:80]
    numbers = sorted(set(NUMBER.findall(block)), key=lambda value: (len(value), value))[:40]
    fixture_only = any(part in row["path"] for part in FIXTURE_ONLY_PATH_PARTS)
    score = row["score"]
    if row["role"] == "implementation":
        score += 5
    if ACTION.search(block):
        score += 4
    if function_scope(path, line_no) != "<module>":
        score += 3
    if fixture_only:
        score -= 7
    return {
        **row,
        "scope": function_scope(path, line_no),
        "context_start_line": lo,
        "context_end_line": hi,
        "context_sha256": hashlib.sha256(block.encode("utf-8")).hexdigest(),
        "identifiers": identifiers,
        "numeric_literals": numbers,
        "fixture_only": fixture_only,
        "binding_score": score,
    }


def flatten(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            rows.extend(flatten(child, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(flatten(child, f"{prefix}[{index}]"))
    elif isinstance(value, (str, int, bool)) or value is None:
        rows.append((prefix, value))
    return rows


def evidence_summary(path_name: str) -> dict[str, Any]:
    path = ROOT / path_name
    data = json.loads(path.read_text())
    selected = []
    for key, value in flatten(data):
        lower = key.lower()
        if any(token in lower for token in (
            "status", "accepted", "required", "fixture", "candidate", "sha256",
            "policy", "ring", "bp", "gear", "run_id", "process", "core", "release_ready",
        )):
            selected.append({"key": key, "value": value})
    return {
        "path": path_name,
        **identity(path),
        "selected_facts": selected[:160],
    }


def evidence_references(context: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    raw = (ROOT / evidence["path"]).read_text(encoding="utf-8", errors="ignore")
    tokens = [Path(context["path"]).name, context["scope"]]
    tokens.extend(identifier for identifier in context["identifiers"] if len(identifier) >= 8)
    return sorted({token for token in tokens if token != "<module>" and token in raw})[:30]


def _remaining_condition(data: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in data["remaining_conditions"] if row["id"] == "NATURAL_CAPTURE_GEAR"]
    need(len(rows) == 1, "NATURAL_CAPTURE_GEAR differs")
    return rows[0]


def build_map() -> dict[str, Any]:
    inventory = json.loads((ROOT / INVENTORY).read_text())
    need(inventory["status"] == "PASS_FINITE_STATIC_INVENTORY_NOT_NATIVE_ACCEPTANCE", "inventory status differs")
    need(inventory["coverage_inventory_complete"] is True, "inventory is not complete")
    need(inventory["physical_acceptance_complete"] is False, "inventory unexpectedly claims play acceptance")
    need(inventory["remaining_physical_gap_ids"] == list(CATEGORY_TO_GAP.values()), "inventory gap IDs differ")

    evidence = [evidence_summary(PURCHASED), evidence_summary(P05_ROUTE)]
    bindings: dict[str, Any] = {}
    for category, gap_id in CATEGORY_TO_GAP.items():
        source_rows = inventory["categories"][category]["selected_roots"]
        contexts = [source_context(row) for row in source_rows]
        contexts.sort(key=lambda row: (-row["binding_score"], row["path"], row["line"]))
        nonfixture = [row for row in contexts if not row["fixture_only"]]
        preferred = nonfixture[0] if nonfixture else contexts[0]
        linked = []
        for receipt in evidence:
            refs = evidence_references(preferred, receipt)
            linked.append({"path": receipt["path"], "references": refs})
        bindings[gap_id] = {
            "category": category,
            "evidence_disposition": "PARTIAL_FIXTURE_OR_ADJACENT_SUCCESS_NOT_ORDINARY_SUPPLY_ACCEPTANCE",
            "preferred_entry_candidate": preferred,
            "alternate_entry_candidates": [row for row in contexts if row is not preferred][:4],
            "nonfixture_candidate_count": len(nonfixture),
            "existing_receipt_links": linked,
            "runner_contract": RUNNER_CONTRACTS[category],
            "physical_acceptance_complete": False,
        }

    purchased = json.loads((ROOT / PURCHASED).read_text())
    need(purchased["purchased_gear_to_battle_accepted"] is True, "purchased route success changed")
    need(purchased["ring_bp_natural_acquisition_accepted"] is False, "ring/BP already accepted")
    need(purchased["ordinary_policy_selection_accepted"] is False, "policy already accepted")

    return {
        "schema_version": 1,
        "status": "PASS_SOURCE_EVIDENCE_BINDING_NOT_NATIVE_ACCEPTANCE",
        "scope": SCOPE,
        "source_commit": git_text("rev-parse", "HEAD"),
        "candidate": inventory["candidate"],
        "inventory": {"path": INVENTORY, **identity(ROOT / INVENTORY)},
        "evidence": evidence,
        "bindings": bindings,
        "coverage_inventory_complete": True,
        "source_evidence_binding_complete": True,
        "physical_acceptance_complete": False,
        "emulator_runs_by_this_checkpoint": 0,
        "purchased_gear_success_preserved": True,
        "remaining_physical_gap_ids": list(CATEGORY_TO_GAP.values()),
        "circus_admission_is_separate": True,
        "release_ready": False,
    }


def project_remaining_work(data: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    row = _remaining_condition(data)
    need(row["gear_to_battle_required"] is False, "gear success reopened")
    need(row["ring_bp_natural_supply_required"] is True, "ring/BP was prematurely closed")
    need(row["ordinary_policy_selection_required"] is True, "policy was prematurely closed")
    row.update(
        {
            "status": "PENDING_THREE_BOUND_NATIVE_SUPPLY_ACCEPTANCES",
            "supply_source_evidence_binding_complete": True,
            "supply_physical_acceptance_complete": False,
            "remaining_supply_gap_ids": list(CATEGORY_TO_GAP.values()),
            "supply_evidence_map": OUTPUT,
            "selected_supply_entrypoints": {
                gap: {
                    "path": value["preferred_entry_candidate"]["path"],
                    "line": value["preferred_entry_candidate"]["line"],
                    "scope": value["preferred_entry_candidate"]["scope"],
                    "fixture_only": value["preferred_entry_candidate"]["fixture_only"],
                }
                for gap, value in report["bindings"].items()
            },
        }
    )
    return data


def render_doc(report: dict[str, Any]) -> str:
    lines = [
        "# PR #16 P05 通常リング・BP・戦闘モード供給 source/evidence 対応checkpoint",
        "",
        "このcheckpointは、前段の静的matchを実装scope・既存receipt・次のrunner契約へ縮約したものです。",
        "通常プレイ受入の成功ではなく、エミュレータ実行数は0です。",
        "",
    ]
    labels = {
        "P05_NATIVE_RING_ACQUISITION_PHYSICAL": "リング通常取得",
        "P05_NATIVE_BP_EARNING_PHYSICAL": "BP通常獲得",
        "P05_ORDINARY_POLICY_SELECTION_PHYSICAL": "戦闘許可モード通常選択",
    }
    for gap, label in labels.items():
        binding = report["bindings"][gap]
        root = binding["preferred_entry_candidate"]
        lines += [
            f"## {label}",
            "",
            f"- gap: `{gap}`",
            f"- preferred source: `{root['path']}:{root['line']}`",
            f"- scope: `{root['scope']}`",
            f"- fixture-only source: `{str(root['fixture_only']).lower()}`",
            f"- nonfixture candidates: {binding['nonfixture_candidate_count']}",
            "- disposition: 既存receiptは隣接成功またはfixture境界であり、通常供給の代替にはしない。",
            "",
            "### 次runnerの必須操作",
            "",
        ]
        lines.extend(f"- {item}" for item in binding["runner_contract"]["required_operations"])
        lines += ["", "### 禁止する短絡", ""]
        lines.extend(f"- {item}" for item in binding["runner_contract"]["forbidden_shortcuts"])
        lines.append("")
    lines += [
        "## 保持する境界",
        "",
        "- 購入石→装備→自然戦闘→保存の成功は保持し、再実行対象に戻さない。",
        "- Circus実受付は別残件であり、この3経路の証拠へ混ぜない。",
        "- 後継最終候補への証拠移送はP08で行う。",
        "",
        f"source commit: `{report['source_commit']}`",
        f"candidate SHA-256: `{report['candidate']['sha256']}`",
        "",
    ]
    return "\n".join(lines)


def write_outputs() -> dict[str, Any]:
    report = build_map()
    (ROOT / OUTPUT).write_bytes(stable_json(report))
    remaining = json.loads((ROOT / REMAINING).read_text())
    (ROOT / REMAINING).write_bytes(stable_json(project_remaining_work(remaining, report)))
    (ROOT / DOC).write_text(render_doc(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print", action="store_true", dest="print_report")
    args = parser.parse_args()
    report = write_outputs() if args.write else build_map()
    if args.print_report or not args.write:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=__import__("sys").stderr)
        raise SystemExit(1)
