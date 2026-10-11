#!/usr/bin/env python3
"""Build a finite, reviewable P05 inventory for native ring/BP/policy supply.

This checkpoint deliberately does not run the emulator and does not replace the
accepted purchased-stone -> equip -> native-battle route.  It only converts the
three fixture prerequisites that remain in NATURAL_CAPTURE_GEAR into explicit
physical acceptance sub-gaps and projects that inventory into the current
remaining-work view.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/pr16_p05_native_supply_reconciliation.py"
TEST = "tests/test_pr16_p05_native_supply_reconciliation.py"
WORKFLOW = ".github/workflows/pr16-p05-native-supply-reconciliation.yml"
OUTPUT = "content/modernization/pr16_p05_native_supply_reconciliation.json"
DOC = "docs/PR16_P05_NATIVE_SUPPLY_RECONCILIATION_CHECKPOINT_JA.md"
REMAINING = "content/modernization/p08_remaining_work.json"
PURCHASED = "content/modernization/pr16_purchased_gear_acceptance.json"
SCOPE = "PR16_P05_NATIVE_RING_BP_POLICY_FINITE_INVENTORY"

PURCHASED_ACCEPTANCE_KEYS = (
    "candidate",
    "purchased_gear_to_battle_accepted",
    "ring_bp_natural_acquisition_accepted",
    "ordinary_policy_selection_accepted",
)

GAP_IDS = (
    "P05_NATIVE_RING_ACQUISITION_PHYSICAL",
    "P05_NATIVE_BP_EARNING_PHYSICAL",
    "P05_ORDINARY_POLICY_SELECTION_PHYSICAL",
)

CATEGORY_PATTERNS = {
    "ring_supply": re.compile(
        r"(?ix)(?:initial_map_party_ring_bp_policy_are_fixtures|"
        r"mega[_ -]?ring|key[_ -]?stone|"
        r"ring[_ -]?(?:item|flag|grant|supply|acquisition|owned|required)|"
        r"メガリング|リング.{0,16}(?:入手|取得|所持|付与|フラグ))"
    ),
    "bp_earning": re.compile(
        r"(?ix)(?:battle[_ -]?points?|"
        r"bp[_ -]?(?:reward|award|grant|earn|balance|currency|counter|delta|amount)|"
        r"(?:reward|award|grant|earn|balance|currency|counter|delta|amount)[_ -]?bp|"
        r"バトルポイント|BP.{0,24}(?:reward|award|grant|earn|balance|報酬|獲得|付与)|"
        r"(?:報酬|獲得|付与).{0,24}BP)"
    ),
    "policy_selection": re.compile(
        r"(?ix)(?:battle[_ -]?(?:policy|permission|mode)|"
        r"mega[_ -]?(?:policy|permission|allowed|enable)|"
        r"next[_ -]?battle|ordinary[_ -]?policy|policy.{0,20}mega|"
        r"許可.{0,20}(?:戦闘|メガ)|(?:戦闘|メガ).{0,20}(?:許可|モード|選択))"
    ),
}

ACTION_PATTERN = re.compile(
    r"(?ix)(?:grant|give|award|reward|earn|add|setvar|set_flag|purchase|shop|"
    r"inventory|bag|受付|入手|取得|付与|報酬|獲得|選択|設定|mode|policy)"
)

ANCHOR_PREFIXES = {
    "ring_supply": (
        "scripts/pr16_purchased_gear.py",
        "scripts/pr16_gear_route_probe.py",
        "scripts/pr16_gear_originals.py",
        "scripts/build_modernization_p05.py",
    ),
    "bp_earning": (
        "scripts/build_bp_shop_runtime.py",
        "scripts/build_factory_reward_runtime.py",
        "scripts/build_factory_repeat_reward_runtime.py",
        "scripts/build_codex_battle_rewards.py",
        "scripts/pr16_purchased_gear.py",
    ),
    "policy_selection": (
        "scripts/pr16_apply_gear_policy_boundary.py",
        "scripts/pr16_purchased_gear.py",
        "scripts/run_modernization_p05_scheduler_e2e.py",
        "scripts/run_modernization_p05_controller_witness.py",
    ),
}

EXCLUDED_PATHS = {SELF, TEST, WORKFLOW, OUTPUT, DOC, REMAINING}
TEXT_SUFFIXES = {
    ".py", ".c", ".h", ".inc", ".json", ".yml", ".yaml", ".md",
    ".txt", ".toml", ".ini", ".cfg", ".sh", ".ps1",
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_purchased_receipt(path: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the purchased-gear receipt and validate its version-2 acceptance object."""
    source = path if path is not None else ROOT / PURCHASED
    data = json.loads(source.read_text())
    need(isinstance(data, dict), "purchased gear receipt root must be an object")
    acceptance = data.get("acceptance")
    need(isinstance(acceptance, dict), "purchased gear receipt missing object: acceptance")
    missing = [key for key in PURCHASED_ACCEPTANCE_KEYS if key not in acceptance]
    need(
        not missing,
        "purchased gear receipt acceptance missing keys: " + ", ".join(missing),
    )
    candidate = acceptance["candidate"]
    need(isinstance(candidate, dict), "purchased gear receipt acceptance.candidate must be an object")
    sha256 = candidate.get("sha256")
    size = candidate.get("size")
    need(
        isinstance(sha256, str) and re.fullmatch(r"[0-9a-f]{64}", sha256) is not None,
        "purchased gear receipt acceptance.candidate.sha256 must be 64 lowercase hex characters",
    )
    need(type(size) is int and size > 0, "purchased gear receipt acceptance.candidate.size must be positive")
    if "candidate" in data:
        need(
            data["candidate"] == candidate,
            "purchased gear receipt candidate aliases differ between root and acceptance",
        )
    return data, acceptance


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def identity(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def tracked_paths() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return sorted(p.decode("utf-8") for p in raw.split(b"\0") if p)


def role_for(path: str) -> str:
    if path.startswith(("scripts/", "tools/", "vendor/", "generated/", "config/")):
        return "implementation"
    if path.startswith("content/") and not path.startswith("content/modernization/"):
        return "implementation"
    if path.startswith(".github/workflows/"):
        return "automation"
    if path.startswith("tests/"):
        return "test"
    if path.startswith(("docs/", "content/modernization/")):
        return "evidence"
    return "other"


def excerpt(line: str) -> str:
    clean = " ".join(line.strip().split())
    return clean[:240]


def score_match(category: str, path: str, line: str, role: str) -> int:
    score = 0
    if role == "implementation":
        score += 5
    elif role == "automation":
        score += 2
    elif role in {"test", "evidence"}:
        score -= 2
    if path in ANCHOR_PREFIXES[category]:
        score += 6
    elif any(path.startswith(prefix.rsplit("/", 1)[0] + "/") for prefix in ANCHOR_PREFIXES[category]):
        score += 1
    if ACTION_PATTERN.search(line):
        score += 3
    if category == "bp_earning" and re.search(r"(?i)(reward|award|earn|報酬|獲得)", line):
        score += 3
    if category == "policy_selection" and re.search(r"(?i)(select|choice|menu|受付|選択)", line):
        score += 2
    return score


def scan_sources() -> tuple[dict[str, list[dict[str, Any]]], int, dict[str, dict[str, Any]]]:
    matches: dict[str, list[dict[str, Any]]] = {key: [] for key in CATEGORY_PATTERNS}
    scanned = 0
    identities: dict[str, dict[str, Any]] = {}
    for rel in tracked_paths():
        if rel in EXCLUDED_PATHS:
            continue
        path = ROOT / rel
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="ignore")
        scanned += 1
        file_has_match = False
        role = role_for(rel)
        for line_no, line in enumerate(text.splitlines(), 1):
            for category, pattern in CATEGORY_PATTERNS.items():
                if not pattern.search(line):
                    continue
                row = {
                    "path": rel,
                    "line": line_no,
                    "role": role,
                    "score": score_match(category, rel, line, role),
                    "excerpt": excerpt(line),
                }
                matches[category].append(row)
                file_has_match = True
        if file_has_match:
            identities[rel] = {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    for category, rows in matches.items():
        dedup: dict[tuple[str, int, str], dict[str, Any]] = {}
        for row in rows:
            dedup[(row["path"], row["line"], row["excerpt"])] = row
        ordered = sorted(
            dedup.values(),
            key=lambda row: (-row["score"], row["path"], row["line"], row["excerpt"]),
        )
        matches[category] = ordered[:120]
    return matches, scanned, identities


def _condition(remaining: dict[str, Any], condition_id: str) -> dict[str, Any]:
    rows = [row for row in remaining["remaining_conditions"] if row["id"] == condition_id]
    need(len(rows) == 1, f"remaining condition differs: {condition_id}")
    return rows[0]


def build_inventory() -> dict[str, Any]:
    remaining = json.loads((ROOT / REMAINING).read_text())
    _, purchased_acceptance = load_purchased_receipt()
    natural = _condition(remaining, "NATURAL_CAPTURE_GEAR")

    need(natural.get("natural_capture_required") is False, "natural capture success was reopened")
    need(natural.get("captured_to_battle_required") is False, "captured battle success was reopened")
    need(natural.get("gear_to_battle_required") is False, "purchased gear success was reopened")
    need(natural.get("ring_bp_natural_supply_required") is True, "ring/BP gap boundary changed")
    need(natural.get("ordinary_policy_selection_required") is True, "policy gap boundary changed")
    need(
        purchased_acceptance["purchased_gear_to_battle_accepted"] is True,
        "purchased gear receipt differs",
    )
    need(
        purchased_acceptance["ring_bp_natural_acquisition_accepted"] is False,
        "ring/BP already accepted elsewhere",
    )
    need(
        purchased_acceptance["ordinary_policy_selection_accepted"] is False,
        "policy already accepted elsewhere",
    )

    matches, scanned, identities = scan_sources()
    categories: dict[str, Any] = {}
    for category, rows in matches.items():
        implementation = [row for row in rows if row["role"] == "implementation"]
        anchor_hits = [row for row in implementation if row["path"] in ANCHOR_PREFIXES[category]]
        need(implementation, f"no implementation candidate for {category}")
        need(anchor_hits, f"no trusted anchor candidate for {category}")
        categories[category] = {
            "match_count_retained": len(rows),
            "implementation_match_count_retained": len(implementation),
            "anchor_match_count_retained": len(anchor_hits),
            "selected_roots": implementation[:12],
            "anchor_matches": anchor_hits[:12],
            "all_retained_matches": rows,
        }

    report = {
        "schema_version": 1,
        "status": "PASS_FINITE_STATIC_INVENTORY_NOT_NATIVE_ACCEPTANCE",
        "scope": SCOPE,
        "source_commit": git_text("rev-parse", "HEAD"),
        "candidate": purchased_acceptance["candidate"],
        "coverage_inventory_complete": True,
        "physical_acceptance_complete": False,
        "emulator_runs_by_this_checkpoint": 0,
        "purchased_gear_success_preserved": True,
        "natural_capture_success_preserved": True,
        "captured_to_battle_success_preserved": True,
        "remaining_physical_gap_ids": list(GAP_IDS),
        "categories": categories,
        "scanned_tracked_text_files": scanned,
        "matched_source_identities": identities,
        "source_receipts": {
            "remaining_work": {"path": REMAINING, **identity(ROOT / REMAINING)},
            "purchased_gear": {"path": PURCHASED, **identity(ROOT / PURCHASED)},
        },
        "separation": {
            "circus_admission_is_separate": True,
            "does_not_write_circus_flag": True,
            "does_not_enable_mega_globally": True,
            "does_not_inject_policy_after_cold_continue": True,
            "does_not_repeat_purchased_stone_route": True,
        },
        "release_ready": False,
    }
    return report


def project_remaining_work(remaining: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    natural = _condition(remaining, "NATURAL_CAPTURE_GEAR")
    natural.update(
        {
            "status": "PENDING_THREE_FINITE_NATIVE_SUPPLY_ACCEPTANCES",
            "supply_coverage_inventory_complete": True,
            "supply_physical_acceptance_complete": False,
            "remaining_supply_gap_ids": list(GAP_IDS),
            "supply_coverage_manifest": OUTPUT,
        }
    )
    need(natural["gear_to_battle_required"] is False, "projection reopened gear route")
    need(natural["ring_bp_natural_supply_required"] is True, "projection closed ring/BP without play")
    need(natural["ordinary_policy_selection_required"] is True, "projection closed policy without play")
    return remaining


def render_doc(report: dict[str, Any]) -> str:
    lines = [
        "# PR #16 P05 通常リング・BP・戦闘モード供給の有限化checkpoint",
        "",
        "このcheckpointは静的な入口候補台帳です。エミュレータ実行や通常プレイ受入の成功報告ではありません。",
        "既存のシビルドナイト購入→装備→自然戦闘→保存成功をやり直したり、取り消したりしません。",
        "",
        "## 残る実操作sub-gap",
        "",
    ]
    lines.extend(f"- `{gap}`" for gap in report["remaining_physical_gap_ids"])
    lines += ["", "## 候補根の機械抽出", ""]
    labels = {
        "ring_supply": "リング通常取得",
        "bp_earning": "BP通常獲得",
        "policy_selection": "戦闘許可モード通常選択",
    }
    for category, label in labels.items():
        data = report["categories"][category]
        lines += [
            f"### {label}",
            "",
            f"保持match: {data['match_count_retained']} / implementation: {data['implementation_match_count_retained']} / anchor: {data['anchor_match_count_retained']}",
            "",
        ]
        for row in data["selected_roots"][:8]:
            lines.append(f"- `{row['path']}:{row['line']}` score={row['score']} — `{row['excerpt']}`")
        lines.append("")
    lines += [
        "## 境界",
        "",
        "- `PHYSICAL_CIRCUS_ADMISSION` は別残件のままです。",
        "- Circusフラグの直接書込みで代替しません。",
        "- 冷Continue後に試験側から許可policyを再注入しません。",
        "- 通常戦闘を一律にメガ許可へ変更しません。",
        "- この台帳から実入口を選び、各sub-gapの通常操作・保存境界だけを次の受入で閉じます。",
        "",
        f"source commit: `{report['source_commit']}`",
        f"candidate SHA-256: `{report['candidate']['sha256']}`",
        "",
    ]
    return "\n".join(lines)


def write_outputs() -> dict[str, Any]:
    report = build_inventory()
    (ROOT / OUTPUT).write_bytes(stable_json(report))
    remaining = json.loads((ROOT / REMAINING).read_text())
    projected = project_remaining_work(remaining, report)
    (ROOT / REMAINING).write_bytes(stable_json(projected))
    (ROOT / DOC).write_text(render_doc(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print", action="store_true", dest="print_report")
    args = parser.parse_args()
    report = write_outputs() if args.write else build_inventory()
    if args.print_report or not args.write:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=__import__("sys").stderr)
        raise SystemExit(1)
