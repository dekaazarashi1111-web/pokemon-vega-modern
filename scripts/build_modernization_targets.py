#!/usr/bin/env python3
"""P01現行対象表とWiki用索引のconsumer。歴史的Wiki・ROMへは書き込まない。"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.build_modernization_catalog import catalog, encoded
from tools.modernization_ids import IdentityError
from tools.modernization_targets import load_targets

OUT = Path("generated/modernization")


def render(targets: dict) -> dict[str, bytes]:
    fields = ("species_key", "id", "national_no", "form_key", "name", "target_status", "collection_key", "apply")
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in targets["species"]:
        writer.writerow(row)
    md = ["# P01 現行ID・原作習得対象索引", "",
          "この索引は現行sourceの対象identityであり、ROMへの技反映・進化仕様の採用・プレイ基準切替を示しません。",
          "固定Stage61 Wikiは変更しません。原作習得の全反映はP03です。", "",
          "| species_key | 現行ID | 名前 | フォーム | 対象区分 | 原作習得対象 |", "|---|---:|---|---|---|---|"]
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    for row in targets["species"]:
        md.append("| " + " | ".join(cell(value) for value in (row["species_key"], row["id"], row["name"], row["form_key"], row["target_status"], "採用対象" if row["apply"] else "除外・維持")) + " |")
    return {"current_targets.json": encoded(targets), "current_targets.csv": text.getvalue().encode("utf-8"),
            "current_species_index.md": ("\n".join(md) + "\n").encode("utf-8")}


def payloads(root: Path) -> dict[str, bytes]:
    # 既存generator出力を実際に消費し、別HEAD・手編集・stale出力を拒否する。
    current = catalog(root)
    path = root / OUT / "current_catalog.json"
    if path.is_symlink() or not path.is_file() or path.read_bytes() != encoded(current):
        raise IdentityError("CURRENT_CATALOG_MISSING_OR_STALE")
    return render(load_targets(root, current))


def execute(root: Path, command: str) -> dict[str, dict]:
    if command not in ("build", "check"):
        raise IdentityError("INVALID_TARGET_COMMAND")
    output = root / OUT
    if output.resolve() != output.absolute():
        raise IdentityError("OUTPUT_SYMLINK_FORBIDDEN")
    files = payloads(root)
    if command == "build":
        output.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        target = output / name
        if target.is_symlink():
            raise IdentityError("OUTPUT_SYMLINK_FORBIDDEN")
        if command == "check":
            if not target.is_file() or target.read_bytes() != raw:
                raise IdentityError("GENERATED_TARGET_MISMATCH")
        else:
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=output, prefix=".p01-target-", delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(raw)
                os.replace(temporary, target)
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
    return {name: {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} for name, raw in files.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    print(json.dumps({"command": args.command, "source_only": True, "outputs": execute(ROOT, args.command)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IdentityError as exc:
        print("P01_TARGET_GATE_FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
