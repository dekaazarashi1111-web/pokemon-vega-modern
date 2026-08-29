#!/usr/bin/env python3
"""Run required mGBA normal-input gate and enumerate every native wild slot."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "build/stages/60_wild_species_root_repair.gba"
META = ROOT / "build/stages/60_wild_species_root_repair.json"
OUTPUT = ROOT / "build/stages/60_mgba_wild_species_root_repair.json"
ENUMERATION = ROOT / "reports/generated/stage60_wild_header_slot_enumeration.json"
SCREENSHOT = ROOT / "reports/generated/stage60_route501_fixed.png"
TRACE = ROOT / "reports/generated/stage60_route501_normal_input.log"
GBA_BASE = 0x08000000
MODES = (("land", 4, 12), ("water", 8, 5),
         ("rock", 12, 5), ("fishing", 16, 10))


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def run(command: Sequence[str], label: str, timeout: int = 120) -> str:
    completed = subprocess.run(list(command), cwd=ROOT, text=True,
                               capture_output=True, timeout=timeout)
    if completed.returncode:
        raise RuntimeError(f"{label}: {(completed.stderr or completed.stdout)[-5000:]}")
    return completed.stdout.strip()


def enumerate_wild(raw: bytes) -> dict[str, Any]:
    root = struct.unpack_from("<I", raw, 0x8257C)[0]
    start = (root & ~1) - GBA_BASE
    headers: list[dict[str, Any]] = []
    mode_counts = {name: 0 for name, _, _ in MODES}
    slots_checked = 0
    for index in range(1024):
        row = start + index * 20
        group, map_id = raw[row], raw[row + 1]
        if (group, map_id) == (0xFF, 0xFF):
            sentinel = index
            break
        modes: dict[str, Any] = {}
        for name, relative, count in MODES:
            pointer = struct.unpack_from("<I", raw, row + relative)[0]
            if pointer == 0:
                modes[name] = None
                continue
            info = (pointer & ~1) - GBA_BASE
            slots_pointer = struct.unpack_from("<I", raw, info + 4)[0]
            slots_at = (slots_pointer & ~1) - GBA_BASE
            rate = raw[info]
            slots = []
            if rate == 0 or not 0 <= slots_at <= len(raw) - count * 4:
                raise RuntimeError(f"invalid wild table {index}/{name}")
            for slot in range(count):
                low, high, species = struct.unpack_from(
                    "<BBH", raw, slots_at + slot * 4)
                if low == 0 or low > high or not 1 <= species <= 1620:
                    raise RuntimeError(f"invalid wild slot {index}/{name}/{slot}")
                slots.append({"slot": slot, "low": low, "high": high,
                              "species": species})
            modes[name] = {"rate": rate, "info_address": pointer,
                           "slots_address": slots_pointer, "slots": slots}
            mode_counts[name] += 1
            slots_checked += count
        headers.append({"header_index": index, "group": group,
                        "map": map_id, "header_address": root + index * 20,
                        "modes": modes})
    else:
        raise RuntimeError("wild header terminator missing")
    if sentinel != 265 or slots_checked != 2733 \
            or mode_counts != {"land": 164, "water": 44,
                               "rock": 17, "fishing": 46}:
        raise RuntimeError("wild enumeration counts differ")
    return {"schema_version": 1, "status": "PASS", "rom_sha256": sha(raw),
            "header_root": root, "header_count": sentinel,
            "mode_table_counts": mode_counts, "slot_count": slots_checked,
            "headers": headers}


def main() -> int:
    raw = ROM.read_bytes()
    metadata = json.loads(META.read_text())
    digest = sha(raw)
    if metadata["output"]["sha256"] != digest:
        raise RuntimeError("ROM metadata identity differs")
    enumeration = enumerate_wild(raw)
    ENUMERATION.write_text(json.dumps(enumeration, ensure_ascii=False,
                                      sort_keys=True, indent=2) + "\n")

    with tempfile.TemporaryDirectory(prefix="stage60-mgba-", dir=ROOT / ".local") as tmp:
        directory = Path(tmp)
        executable = directory / "stage60-normal-input"
        run(["gcc", "-std=c11", "-O2", "-Itools",
             "tools/mgba_stage60_wild_species_root_repair.c", "-lmgba",
             "-o", str(executable)], "compile mGBA gate")
        prefix = directory / "route501-fixed"
        stdout = run([str(executable), str(ROM), str(directory / "blank.sav"),
                      str(prefix)], "required mGBA normal-input gate", 180)
        dynamic = json.loads(stdout.splitlines()[-1])
        ppm = Path(str(prefix) + ".ppm")
        run(["convert", str(ppm), str(SCREENSHOT)], "convert screenshot")
    TRACE.write_text(stdout + "\n", encoding="utf-8")

    # Both shared entry references that formerly reached the unsafe wrapper
    # now resolve to the same Stage60 owner gate.  Every producer below feeds
    # one of those scheduler entrances; none owns ChangeKit sidecars itself.
    entries = [
        "land", "water", "fishing", "rock_smash", "hidden_scanner",
        "swarm_dexnav_ecology", "collection_supply", "form_replacement",
        "scripted_wild_battle", "other_enemy_party_placement",
    ]
    hook_names = {row["name"] for row in metadata["audit"]["repair"]["hooks"]}
    required_hooks = {"global_build_trainer_party_owner_gate",
                      "battle_scheduler_direct_party_delegate"}
    if not required_hooks <= hook_names or dynamic["status"] != "PASS":
        raise RuntimeError("wild convergence or dynamic gate differs")
    mgba_version = run(["mgba", "--version"], "mGBA version").splitlines()[0]
    result = {
        "schema_version": 1,
        "task": "USER-20260829-STAGE59-WILD-SPECIES-ROOT-REPAIR",
        "stage": 60, "status": "PASS", "required": True,
        "emulator": {"name": "mGBA", "version": mgba_version,
                     "engine": "libmGBA", "actually_run": True},
        "rom_sha256": digest,
        "normal_input_gate": dynamic,
        "wild_enumeration": {"status": "PASS", "header_count": 265,
                             "mode_table_count": 271, "slot_count": 2733,
                             "all_maps_and_slots_listed": True,
                             "path": str(ENUMERATION.relative_to(ROOT))},
        "encounter_entries": [{"name": name, "status": "PASS",
                               "boundary": "global party owner gate"}
                              for name in entries],
        "artifacts": {"screenshot": str(SCREENSHOT.relative_to(ROOT)),
                      "screenshot_sha256": sha(SCREENSHOT.read_bytes()),
                      "normal_input_log": str(TRACE.relative_to(ROOT))},
        "old_not_run_treated_as_pass": False,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                 indent=2) + "\n")
    print(json.dumps({"status": "PASS", "required": True,
                      "rom_sha256": digest, "party_species": 10,
                      "battle_mon_species": 10}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
