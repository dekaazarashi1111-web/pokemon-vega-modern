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
    full_unit = [["make", "test"]]
    plans = {
        "battle-cli-offline": battle,
        "stage62-check": stage62_check,
        "stage62-mgba": stage62_mgba,
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
