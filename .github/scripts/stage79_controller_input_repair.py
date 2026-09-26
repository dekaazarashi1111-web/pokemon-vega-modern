#!/usr/bin/env python3
"""Guarded harness-only correction for a dropped physical menu input.

A recognized controller is not proof it consumed A: it can still be waiting on
its animation/text. Retry the same selection after 30 frames of released input.
The 20,000-frame limit, five shields, native damage, capture and cleanup
expectations stay unchanged. No game code, ROM, save or PASS record is written.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = "tools/mgba_battle_policy_smoke.c"
CONFIG = "config/modernization_stage79_cumulative_mgba.json"


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"nonunique source preimage: {old!r}")
    return text.replace(old, new, 1)


def identity(path: str) -> dict:
    raw = (ROOT / path).read_bytes()
    return {"path": path, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main() -> None:
    config = json.loads((ROOT / CONFIG).read_text())
    rom = config["input_identity"]["rom"]
    assert identity(rom["path"])["sha256"] == rom["sha256"]
    gate = json.loads((ROOT / config["execution"]["runtime_gate"]).read_text())
    assert gate["status"] == "READY_NOT_RUN" and gate["not_yet_executed"] is True
    assert gate["execution"]["evidenced_domain_runs"] == 0
    domain = next(row for row in config["domains"] if row["id"] == "battle_policy")
    text = (ROOT / RUNNER).read_text()
    if "POLICY_RAID_SELECTION_RETRY_INTERVAL" not in text:
        assert identity(RUNNER)["sha256"] == domain["runner"]["sha256"]
        text = once(text, "    POLICY_RAID_INTRO_PRESS_INTERVAL = 27,\n",
                    "    POLICY_RAID_INTRO_PRESS_INTERVAL = 27,\n"
                    "    POLICY_RAID_SELECTION_RETRY_INTERVAL = 30,\n")
        text = once(text, "    uint32_t next_message_press = evidence->frames;\n",
                    "    uint32_t next_message_press = evidence->frames;\n"
                    "    uint32_t next_selection_press = evidence->frames;\n")
        text = once(text,
            "        if (gate != 0 && (gate == 4 || gate == 5 || gate != latched_gate)) {",
            "        /* A callback may appear before it can consume physical A.\n"
            "         * A latched attempt must not suppress every later input. */\n"
            "        if (gate != 0 && (gate == 4 || gate == 5 || gate != latched_gate\n"
            "                          || evidence->frames >= next_selection_press)) {")
        text = once(text, "                latched_gate = gate;\n",
                    "                latched_gate = gate;\n"
                    "                next_selection_press = pulse_start\n"
                    "                    + POLICY_RAID_SELECTION_RETRY_INTERVAL;\n")
        (ROOT / RUNNER).write_text(text)
    for item in config["domains"]:
        for record in [item["runner"], *item.get("dependencies", [])]:
            if record["path"] == RUNNER:
                record.update(identity(RUNNER))
    spec = importlib.util.spec_from_file_location("stage79_input_repaired", ROOT / config["orchestrator"]["path"])
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (ROOT / CONFIG).write_bytes(module._stable(config))
    module.prepare()
    assert identity(rom["path"])["sha256"] == rom["sha256"]
    print(json.dumps({"status": "SOURCE_REPAIR_APPLIED", "rom_unchanged": True,
                      "selection_retry_frames": 30, "runtime_pass_claimed": False}))


if __name__ == "__main__":
    main()
