#!/usr/bin/env python3
"""Apply the narrowly scoped Stage79 Factory map harness correction.

Historical Stage68 symbols and the default Stage68 runner remain unchanged in
meaning. Only the Stage79 caller follows the verified Stage69 map relocation.
No ROM, save, gameplay expectation, or executed evidence is rewritten.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR = "scripts/run_modernization_stage79_cumulative_mgba.py"
RUNNER = "tools/mgba_modernization_mega_shop_smoke.c"
WRAPPER = "tools/mgba_modernization_stage79_mega_shop_smoke.c"
CONFIG = "config/modernization_stage79_cumulative_mgba.json"

MAP_CHECK = '''    # Stage68 owns the shop ABI; Stage69 owns the cumulative map graph.
    # Do not edit historical symbols or accept arbitrary extra objects.
    map_source = _fixed_json(domain.get("map_contract_source"),
                             "Stage79 Factory map symbols")
    old_map = source["map"]
    current_map = map_source["map"]
    if (current_map.get("group_id") != 96
            or current_map.get("map_id") != 5
            or old_map.get("group_id") != 96
            or old_map.get("map_id") != 5
            or current_map.get("header_address") != old_map.get("header_address")
            or current_map.get("old_events_pointer") != old_map.get("events_after_address")
            or current_map.get("old_objects_pointer") != old_map.get("objects_after_address")
            or current_map.get("old_scripts_pointer") != old_map.get("old_scripts_pointer")
            or current_map.get("object_count_before") != 14
            or old_map.get("object_count_after") != 14
            or current_map.get("object_count_after") != 15
            or current_map.get("old_event_counts") != [14, 10, 0, 7]
            or current_map.get("existing_14_objects_preserved") is not True
            or current_map.get("stage68_shop_local14_preserved") is not True
            or current_map.get("map_scripts_preserved") is not True
            or current_map.get("gift_object", {}).get("local_id") != 15):
        _fail("Stage79 Factory map provenance/count contract mismatch")
'''


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"source preimage is not unique: {old[:100]!r}")
    return text.replace(old, new, 1)


def identity(name: str) -> dict:
    raw = (ROOT / name).read_bytes()
    return {"path": name, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main() -> None:
    config = json.loads((ROOT / CONFIG).read_text())
    rom = config["input_identity"]["rom"]
    assert identity(rom["path"])["sha256"] == rom["sha256"]
    gate = json.loads((ROOT / config["execution"]["runtime_gate"]).read_text())
    assert gate["status"] == "READY_NOT_RUN" and gate["not_yet_executed"] is True
    assert gate["execution"]["evidenced_domain_runs"] == 0
    script = (ROOT / ORCHESTRATOR).read_text()
    runner = (ROOT / RUNNER).read_text()
    # An already applied repair must be validated, not applied twice.
    if "Stage79 Factory map provenance/count contract mismatch" not in script:
        assert identity(ORCHESTRATOR)["sha256"] == config["orchestrator"]["sha256"]
        script = replace_once(script,
            '    source = _fixed_json(domain.get("contract_source"), "Mega shop symbols")\n',
            '    source = _fixed_json(domain.get("contract_source"), "Mega shop symbols")\n' + MAP_CHECK)
        script = replace_once(script,
            '        _member(source, ("map", "events_after_address"), "Mega shop symbols"),',
            '        _member(map_source, ("map", "events_after_address"), "Stage79 Factory map symbols"),')
        script = replace_once(script,
            '        _member(source, ("map", "old_scripts_pointer"), "Mega shop symbols"),',
            '        _member(map_source, ("map", "old_scripts_pointer"), "Stage79 Factory map symbols"),')
        script = replace_once(script,
            '        "contract_source": dict(mega["contract_source"]),',
            '        "contract_source": dict(mega["contract_source"]),\n'
            '        "map_contract_source": dict(mega["map_contract_source"]),\n'
            '        "factory_object_count": 15,')
        runner = replace_once(runner, '#include <time.h>\n',
            '#include <time.h>\n\n'
            '/* Stage68 keeps its exact 14-object graph. The cumulative caller\n'
            ' * opts into the exact Stage69 15-object graph, never a range. */\n'
            '#ifndef MEGA_EXPECTED_FACTORY_OBJECT_COUNT\n'
            '#define MEGA_EXPECTED_FACTORY_OBJECT_COUNT 14U\n'
            '#endif\n')
        runner = replace_once(runner, 'read8(core, events) != 14U',
                              'read8(core, events) != MEGA_EXPECTED_FACTORY_OBJECT_COUNT')
        runner = replace_once(runner, 'index < 14U; ++index',
                              'index < MEGA_EXPECTED_FACTORY_OBJECT_COUNT; ++index')
        (ROOT / ORCHESTRATOR).write_text(script)
        (ROOT / RUNNER).write_text(runner)
    (ROOT / WRAPPER).write_text(
        '/* Stage79 cumulative Factory graph: Stage69 adds gift NPC local 15. */\n'
        '#define MEGA_EXPECTED_FACTORY_OBJECT_COUNT 15U\n'
        '#include "mgba_modernization_mega_shop_smoke.c"\n')
    domains = {row["id"]: row for row in config["domains"]}
    mega = domains["mega_shop"]
    mega["runner"] = identity(WRAPPER)
    if not any(row["path"] == RUNNER for row in mega["dependencies"]):
        mega["dependencies"].append(identity(RUNNER))
    mega["map_contract_source"] = dict(domains["floette"]["contract_sources"]["symbols"])
    for domain in config["domains"]:
        for row in [domain["runner"], *domain.get("dependencies", [])]:
            if row["path"] in (RUNNER, WRAPPER):
                row.update(identity(row["path"]))
    config["orchestrator"].update(identity(ORCHESTRATOR))
    spec = importlib.util.spec_from_file_location("stage79_map_repaired", ROOT / ORCHESTRATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    arguments, _ = module._mega_shop_arguments(mega)
    mega["argument_count"] = len(arguments)
    mega["arguments_sha256"] = module._sha(module._stable(arguments))
    (ROOT / CONFIG).write_bytes(module._stable(config))
    module.prepare()
    assert identity(rom["path"])["sha256"] == rom["sha256"]
    print(json.dumps({"status": "SOURCE_REPAIR_APPLIED", "rom_unchanged": True,
                      "map_events": arguments[8], "object_count": 15,
                      "runtime_pass_claimed": False}))


if __name__ == "__main__":
    main()
