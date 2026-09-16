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
    "modernization-p04-assets",
    "modernization-p04-capacity",
    "modernization-p03-stage65",
    "modernization-p03-stage66",
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
        # runnerがStage63からStage64をmemory生成するため、stale evidenceでも
        # clean bootstrapできる。builderは更新済みevidenceを結合する。
        [python, "scripts/run_modernization_p02_mgba.py", "run"],
        [python, "scripts/run_modernization_p02_mgba.py", "check"],
        [python, "scripts/build_modernization_p02_stage64.py", "build"],
        [python, "scripts/build_modernization_p02_stage64.py", "check"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p02_stage64_checkpoint.json",
            "content/modernization/p02_stage64_mgba_runtime_gate.json",
        ],
        ["make", "modernization-p02-focused-test"],
    ]
    modernization_contracts = [
        [python, "scripts/build_modernization_p03.py", "--check"],
        [python, "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"],
        [python, "scripts/build_modernization_p05.py", "--check"],
        [python, "scripts/build_modernization_p06.py", "--compact"],
        [python, "scripts/build_modernization_p07.py", "--check"],
        ["make", "modernization-contracts-focused-test"],
    ]
    modernization_p04_assets = [
        [python, "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"],
        [python, "scripts/build_modernization_p04_assets.py", "--write", "--compact"],
        ["git", "diff", "--exit-code", "--", "content/modernization/p04_asset_import_manifest.json"],
        [python, "scripts/build_modernization_p04_assets.py", "--check", "--compact"],
        ["make", "modernization-p04-assets-focused-test"],
    ]
    modernization_p04_capacity = [
        [python, "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"],
        [python, "scripts/build_modernization_p04_assets.py", "--write", "--compact"],
        ["git", "diff", "--exit-code", "--", "content/modernization/p04_asset_import_manifest.json"],
        [python, "scripts/build_modernization_p01.py", "build"],
        [python, "scripts/build_modernization_p02_stage64.py", "build"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p02_stage64_checkpoint.json",
        ],
        [python, "scripts/build_modernization_p03_stage65.py", "build"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage65_checkpoint.json",
        ],
        [python, "scripts/build_modernization_p05.py", "--check"],
        [python, "scripts/build_modernization_p04_capacity.py", "--check", "--compact"],
        ["make", "modernization-p04-capacity-focused-test"],
    ]
    modernization_p03_stage65 = [
        [python, "scripts/build_modernization_p03.py", "--check"],
        [python, "scripts/build_modernization_p01.py", "build"],
        [python, "scripts/build_modernization_p02_stage64.py", "build"],
        # mGBA runnerはStage65をmemory上で決定的生成して証跡を公開する。
        # 最終builderはその証跡を検証してcheckpointへ結合する。
        [python, "scripts/run_modernization_p03_stage65_mgba.py", "run"],
        [python, "scripts/build_modernization_p03_stage65.py", "build"],
        [python, "scripts/run_modernization_p03_stage65_mgba.py", "check"],
        [python, "scripts/build_modernization_p03_stage65.py", "check"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage65_checkpoint.json",
            "content/modernization/p03_stage65_mgba_runtime_gate.json",
        ],
        ["make", "modernization-p03-stage65-focused-test"],
    ]
    modernization_p03_stage66 = [
        [python, "scripts/build_modernization_p03.py", "--check"],
        [python, "scripts/build_modernization_p01.py", "build"],
        [python, "scripts/build_modernization_p02_stage64.py", "build"],
        [python, "scripts/build_modernization_p03_stage65.py", "build"],
        # Stage66 runnerは生成予定ROMをmemory上で検証し、builderが証跡と
        # ignored artifactを結合する。保存済みROMだけの検査にはしない。
        [python, "scripts/run_modernization_p03_stage66_mgba.py", "run"],
        [python, "scripts/build_modernization_p03_stage66.py", "build"],
        [python, "scripts/run_modernization_p03_stage66_mgba.py", "check"],
        [python, "scripts/build_modernization_p03_stage66.py", "check"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage66_bulk_route_audit.json",
            "content/modernization/p03_stage66_change_audit.json",
            "content/modernization/p03_stage66_checkpoint.json",
            "content/modernization/p03_stage66_mgba_runtime_gate.json",
        ],
        ["make", "modernization-p03-stage66-focused-test"],
        [python, "scripts/build_modernization_p08.py", "--check"],
        ["make", "modernization-p08-focused-test"],
    ]
    # 新しいunit群はignoredのexact ROM/artifactと外部固定checkoutも監査する。
    # clean private runnerでは先に全入力からそれらを再生成し、tracked manifestの
    # driftがないことを確認してからrepository全unitを走らせる。
    full_unit = [
        [python, "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"],
        [python, "scripts/build_modernization_p04_assets.py", "--write", "--compact"],
        ["git", "diff", "--exit-code", "--", "content/modernization/p04_asset_import_manifest.json"],
        [python, "scripts/build_modernization_p01.py", "build"],
        [python, "scripts/build_modernization_p02_stage64.py", "build"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p02_stage64_checkpoint.json",
        ],
        [python, "scripts/build_modernization_p03_stage65.py", "build"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage65_checkpoint.json",
        ],
        [python, "scripts/build_modernization_p03_stage66.py", "build"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage66_bulk_route_audit.json",
            "content/modernization/p03_stage66_change_audit.json",
            "content/modernization/p03_stage66_checkpoint.json",
        ],
        ["make", "test"],
    ]
    modernization_runtime = [
        [python, "scripts/build_modernization_p01.py", "build"],
        [python, "scripts/run_modernization_p01_mgba.py"],
        [python, "scripts/run_modernization_p02_mgba.py", "run"],
        [python, "scripts/run_modernization_p02_mgba.py", "check"],
        [python, "scripts/build_modernization_p02_stage64.py", "build"],
        [python, "scripts/build_modernization_p02_stage64.py", "check"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p02_stage64_checkpoint.json",
            "content/modernization/p02_stage64_mgba_runtime_gate.json",
        ],
        [python, "scripts/run_modernization_p03_stage65_mgba.py", "run"],
        [python, "scripts/build_modernization_p03_stage65.py", "build"],
        [python, "scripts/run_modernization_p03_stage65_mgba.py", "check"],
        [python, "scripts/build_modernization_p03_stage65.py", "check"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage65_checkpoint.json",
            "content/modernization/p03_stage65_mgba_runtime_gate.json",
        ],
        [python, "scripts/run_modernization_p03_stage66_mgba.py", "run"],
        [python, "scripts/build_modernization_p03_stage66.py", "build"],
        [python, "scripts/run_modernization_p03_stage66_mgba.py", "check"],
        [python, "scripts/build_modernization_p03_stage66.py", "check"],
        [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage66_bulk_route_audit.json",
            "content/modernization/p03_stage66_change_audit.json",
            "content/modernization/p03_stage66_checkpoint.json",
            "content/modernization/p03_stage66_mgba_runtime_gate.json",
        ],
        [python, "scripts/build_modernization_p08.py", "--check"],
    ]
    plans = {
        "battle-cli-offline": battle,
        "stage62-check": stage62_check,
        "stage62-mgba": stage62_mgba,
        "modernization-p01": modernization_p01,
        "modernization-p02": modernization_p02,
        "modernization-contracts": modernization_contracts,
        "modernization-p04-assets": modernization_p04_assets,
        "modernization-p04-capacity": modernization_p04_capacity,
        "modernization-p03-stage65": modernization_p03_stage65,
        "modernization-p03-stage66": modernization_p03_stage66,
        "full-unit": full_unit,
        # full-unitにbattle unitが含まれるため、allではmodernizationの実mGBAと
        # CLI実読取を追加する。保存済みevidenceの静的checkだけでは完了しない。
        # runtime chainがStage63～66を一度だけ生成する。続けて素材を復元し
        # 全unitを走らせ、full_unitとの重複buildを避ける。
        "all": (
            stage62_check
            + stage62_mgba
            + modernization_p04_assets[:-1]
            + modernization_runtime
            + [["make", "test"]]
            + battle[1:]
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
