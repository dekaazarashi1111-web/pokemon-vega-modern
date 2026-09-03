#!/usr/bin/env python3
"""Codex Battle protocolのROM identityだけを派生ROMへ安全に再固定する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zlib
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


def detect_stage(path: Path, fallback: int) -> int:
    match = re.search(r"(?:^|[^0-9])(?:stage)?(\d{2})(?:_|[^0-9])", path.stem,
                      flags=re.IGNORECASE)
    return int(match.group(1)) if match else fallback


def rebind_protocol(
    protocol: Mapping[str, Any], rom: bytes, *, stage: int, rom_path: str,
) -> dict[str, Any]:
    if type(stage) is not int or stage < 47:
        raise ValueError("Codex Battle/送付CLIにはStage47以降が必要です")
    if not rom or not isinstance(protocol.get("rom"), Mapping):
        raise ValueError("protocol/ROM identity入力が不正です")
    rebound = deepcopy(dict(protocol))
    rebound["stage"] = stage
    rebound["rom"] = {
        "crc32": f"{zlib.crc32(rom) & 0xFFFFFFFF:08X}",
        "path": rom_path,
        "sha256": hashlib.sha256(rom).hexdigest(),
        "size": len(rom),
    }
    return rebound


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rom-path", default="windows_box14_vault.gba")
    parser.add_argument("--stage", type=int)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    fallback = int(protocol.get("stage", 0))
    stage = args.stage if args.stage is not None else detect_stage(
        args.rom, fallback,
    )
    rebound = rebind_protocol(
        protocol, args.rom.read_bytes(), stage=stage, rom_path=args.rom_path,
    )
    args.output.write_text(
        json.dumps(rebound, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
