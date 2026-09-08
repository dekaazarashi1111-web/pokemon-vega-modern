#!/usr/bin/env python3
"""復元済みGitHub Actions workspaceで固定private suiteを実行する。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SUITES = {
    "battle-cli-offline",
    "stage62-check",
    "stage62-mgba",
    "modernization-p01",
    "modernization-p02",
    "modernization-contracts",
    "full-unit",
    "all",
}


def command_plan(suite: str, python: str = sys.executable) -> list[list[str]]:
    battle = [
        [
            python, "-m", "unittest",
            "tests.test_codex_battle_runtime",
            "tests.test_codex_battle_rewards",
            "tests.test_windows_battle_catalog",
            "tests.test_windows_box14_vault",
            "tests.test_vega_codex_battle_protocol_rebind",
        ],
        [python, "tools/vega_codex_battle.py", "--version"],
        [
            python, "tools/vega_codex_battle.py", "catalog", "species",
            "search", "--query", "ピカチュウ", "--limit", "3", "--json",
        ],
    ]
    stage62_check = [[
        python, "scripts/build_stage62_npc_placement_integrity_repair.py",
        "check", "--runs", "2",
    ]]
    stage62_mgba = [[
        python, "scripts/build_stage62_npc_placement_integrity_repair.py",
        "mgba", "--runs", "2",
    ]]
    modernization_p01 = [
        ["make", "modernization-p01-focused-test"],
        [python, "scripts/audit_modernization_p01_rom.py", "--compact"],
        [python, "scripts/build_stage61_wiki.py", "check"],
        [python, "scripts/build_modernization_identity.py", "--check"],
        [python, "scripts/build_modernization_p01.py", "build"],
        [python, "scripts/build_modernization_p01.py", "check"],
        [python, "scripts/run_modernization_p01_mgba.py"],
    ]
    modernization_p02 = [
        [python, "scripts/build_modernization_p02.py", "--check"],
        # private復元bundleはStage62まで。固定入力から親Stage63も再生成し、
        # 保存済み生成物に依存せずStage64へ進む。
        [python, "scripts/build_modernization_p01.py", "build"],
        [python, "scripts/build_modernization_p02_stage64.py", "build"],
        [python, "scripts/run_modernization_p02_mgba.py", "run"],
        [python, "scripts/run_modernization_p02_mgba.py", "check"],
        [python, "scripts/build_modernization_p02_stage64.py", "check"],
        ["make", "modernization-p02-focused-test"],
    ]
    modernization_contracts = [
        [python, "scripts/build_modernization_p03.py", "--check"],
        [python, "scripts/build_modernization_p05.py", "--check"],
        [python, "scripts/build_modernization_p06.py", "--compact"],
        [python, "scripts/build_modernization_p07.py", "--check"],
        ["make", "modernization-contracts-focused-test"],
    ]
    full_unit = [["make", "test"]]
    plans = {
        "battle-cli-offline": battle,
        "stage62-check": stage62_check,
        "stage62-mgba": stage62_mgba,
        "modernization-p01": modernization_p01,
        "modernization-p02": modernization_p02,
        "modernization-contracts": modernization_contracts,
        "full-unit": full_unit,
        # full-unitにbattle unitが含まれるため、allではCLI実読取だけを追加する。
        "all": (
            stage62_check + stage62_mgba + full_unit + battle[1:]
        ),
    }
    try:
        return plans[suite]
    except KeyError as exc:
        raise ValueError(f"unknown private suite: {suite}") from exc


def run_suite(suite: str) -> None:
    for command in command_plan(suite):
        print("+", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=sorted(SUITES))
    args = parser.parse_args(argv)
    try:
        run_suite(args.suite)
    except subprocess.CalledProcessError as exc:
        print(
            f"GitHub private suite: FAIL suite={args.suite} exit={exc.returncode}",
            file=sys.stderr,
        )
        return exc.returncode or 1
    print(f"GitHub private suite: PASS suite={args.suite}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
