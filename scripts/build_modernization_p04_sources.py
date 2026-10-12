#!/usr/bin/env python3
"""工程4のcommit固定sourceを取得し、候補とGBA素材coverageを監査する。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_sources import P04SourceError, audit_p04_sources


def _run(*args: str) -> None:
    subprocess.run(args, check=True)


def _fetch_source(root: Path, destination: Path) -> None:
    """manifestで固定したcommitだけを明示的な書込操作として取得する。"""
    asset_manifest = json.loads(
        (root / "content/modernization/p04_asset_sources.json").read_text(encoding="utf-8")
    )
    selected = next(
        item
        for item in asset_manifest["sources"]
        if item["source_key"] == asset_manifest["selected_source_key"]
    )
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not (destination / ".git").is_dir():
            raise P04SourceError(f"取得先が既存の非git directoryです: {destination}")
        dirty = subprocess.run(
            ["git", "-C", str(destination), "status", "--porcelain", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if dirty:
            raise P04SourceError(f"既存checkoutに変更があるため取得を中止します: {destination}")
        origin = subprocess.run(
            ["git", "-C", str(destination), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        accepted = {selected["clone_url"], selected["repository_url"], selected["repository_url"] + ".git"}
        if origin not in accepted:
            raise P04SourceError(f"既存checkoutのoriginが違います: {origin}")
    else:
        _run("git", "clone", "--no-checkout", selected["clone_url"], str(destination))
    _run("git", "-C", str(destination), "fetch", "--depth", "1", "origin", selected["commit"])
    _run("git", "-C", str(destination), "checkout", "--detach", selected["commit"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="ワークスペースroot")
    parser.add_argument("--source-root", type=Path, help="固定source checkout")
    parser.add_argument("--fetch", action="store_true", help="固定commitを取得してから監査する（書込あり）")
    parser.add_argument("--compact", action="store_true", help="JSONを1行で出力する")
    args = parser.parse_args()
    root = args.root.resolve()
    source_root = args.source_root
    if source_root is None:
        source_root = root / ".local/modernization_sources/pokeemerald-expansion"
    if args.fetch:
        _fetch_source(root, source_root)
    try:
        result = audit_p04_sources(root, source_root=source_root, require_checkout=True)
    except (P04SourceError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    if args.compact:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
