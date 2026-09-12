#!/usr/bin/env python3
"""Actual non-Rotom generic form carry acceptance on the frozen PR #16 parent.

The Shaymin representative reaches the authored FORM host, changes the same
individual through the native party picker, preserves four move/PP slots in
both directions, exercises party cancellation, and uses normal Save plus fresh
Continue.  Starting map, progress and individual are fixtures.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import pr16_breeding_delta as base
import pr16_p03_form_gap_inventory as form_inventory
from tools.trainer_final.kanto_events import _stage_map_state

repaired = base.repaired
need = repaired.need
common = base.load().common

SELF = "scripts/pr16_generic_form_carry.py"
SOURCE = "tools/mgba_pr16_generic_form_carry.c"
TEST = "tests/test_pr16_generic_form_carry.py"
WORKFLOW = ".github/workflows/pr16-generic-form-carry.yml"
MODEL = "content/collection_supply_v1/canonical_model.json"
MODEL_SHA = "fb8066c0a8140da079b1e947cdfb6c76e987cf0c2514456a86868ec554f061d0"
LEDGER = "content/modernization/pr16_p03_p07_route_coverage.json"
OUT = ROOT / ".local/pr16-generic-form-carry"
SCOPE = "PR16_P03_GENERIC_FORM_CARRY_PHYSICAL"
ENTRY_SCOPE = "PR16_P03_GENERIC_FORM_ENTRY_DIAGNOSTIC"
FIX_HOF_FLAG = 1 << 0
FIX_HOF_MIRROR = 1 << 1
FIX_LEDGER_20 = 1 << 2
FIX_LEAGUE_II = 1 << 3
FIX_HOST_PROGRESS = 1 << 4
FIX_FINALIZE = 1 << 5
PROBES = (
    {"name": "entry-host-only-untouched", "normalize": False, "pre_mask": 0,
     "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-host-only-normalized", "normalize": True, "pre_mask": 0,
     "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-flag-post-once", "normalize": True, "pre_mask": 0,
     "post_mask": FIX_HOF_FLAG | FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-mirror-post-once", "normalize": True, "pre_mask": 0,
     "post_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-legacy-post-once", "normalize": True, "pre_mask": 0,
     "post_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_LEDGER_20 | FIX_LEAGUE_II
     | FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-flag-pre-split", "normalize": True,
     "pre_mask": FIX_HOF_FLAG | FIX_FINALIZE,
     "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-mirror-pre-split", "normalize": True,
     "pre_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_FINALIZE,
     "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-ledger20-pre-split", "normalize": True,
     "pre_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_LEDGER_20 | FIX_FINALIZE,
     "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-league2-pre-split", "normalize": True,
     "pre_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_LEAGUE_II | FIX_FINALIZE,
     "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-legacy-ledgers-pre-split", "normalize": True,
     "pre_mask": FIX_HOF_MIRROR | FIX_LEDGER_20 | FIX_LEAGUE_II | FIX_FINALIZE,
     "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-legacy-pre-split", "normalize": True,
     "pre_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_LEDGER_20 | FIX_LEAGUE_II
     | FIX_FINALIZE, "post_mask": FIX_HOST_PROGRESS | FIX_FINALIZE},
    {"name": "entry-hof-mirror-host-pre-once", "normalize": True,
     "pre_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_HOST_PROGRESS | FIX_FINALIZE,
     "post_mask": 0},
    {"name": "entry-legacy-host-pre-once", "normalize": True,
     "pre_mask": FIX_HOF_MIRROR | FIX_LEDGER_20 | FIX_LEAGUE_II
     | FIX_HOST_PROGRESS | FIX_FINALIZE, "post_mask": 0},
    {"name": "entry-hof-legacy-host-pre-once", "normalize": True,
     "pre_mask": FIX_HOF_FLAG | FIX_HOF_MIRROR | FIX_LEDGER_20 | FIX_LEAGUE_II
     | FIX_HOST_PROGRESS | FIX_FINALIZE, "post_mask": 0},
)
PROBE_BY_NAME = {probe["name"]: probe for probe in PROBES}
CASES = ("shaymin-four-slot-roundtrip", "shaymin-party-cancel")
MOVES = [98, 235, 552, 33]
PP = [11, 3, 4, 7]
PP_BONUSES = 229
FORM_INDEX = 43
ELIGIBLE_ORDINAL = 6
MENU_PAGE = 1
MENU_CURSOR = 1
GENERIC_ROWS_SHA = "66cd203079d2a6d8ef1eb0fca6b5156c7bccbc1c720786df4953311491b5592e"
REPRESENTATIVE_ROUTE_IDS = [
    "bca6fe62e4b8925d73c8238a",
    "830d0124e9ca952d41d4a7f0",
    "57e91d3ffeb04c9795a8b6a1",
]
TRACE = (
    "interaction",
    "root",
    "service",
    "page",
    "party",
    "selection",
    "returned",
    "species_after",
    "saved",
    "reloaded",
)


def expected_probe(name):
    need(name in PROBE_BY_NAME, "unknown generic entry probe")
    probe = PROBE_BY_NAME[name]
    return {
        "schema_version": 1,
        "status": "OBSERVED",
        "scope": ENTRY_SCOPE,
        "case": name,
        "rom_sha256": repaired.ROM_SHA,
        "normalize": probe["normalize"],
        "pre_mask": probe["pre_mask"],
        "post_mask": probe["post_mask"],
        "finalize_count": int(bool(probe["pre_mask"] & FIX_FINALIZE))
        + int(bool(probe["post_mask"] & FIX_FINALIZE)),
        "fresh_core": True,
        "input_only_after_guard": True,
        "acceptance_claimed": False,
        "release_ready": False,
    }


def validate_probe(raw, name, code):
    need(type(code) is int and code == 0, "generic entry probe did not exit integer zero")
    row = common.strict_json(raw)
    want = expected_probe(name)
    dynamic = {
        "save_counter_before",
        "save_counter_after",
        "baseline_readback",
        "progress_readback",
        "host_readback",
        "interaction_frame",
        "root_menu_opened",
        "root_frame",
        "result",
        "host",
        "service",
        "mode",
        "page",
        "window",
        "field_lock",
        "main_callback2",
        "total_frames",
    }
    need(type(row) is dict and set(row) == set(want) | dynamic,
         "generic entry probe schema differs")
    for key, value in want.items():
        need(common.same_typed(row[key], value), "generic entry probe differs: " + key)
    for key in ("save_counter_before", "save_counter_after", "interaction_frame",
                "root_frame", "result", "host", "service", "mode", "page",
                "window", "field_lock", "main_callback2", "total_frames"):
        need(type(row[key]) is int and row[key] >= 0,
             "invalid generic entry integer: " + key)
    need(row["save_counter_after"] >= row["save_counter_before"],
         "generic entry save counter moved backwards")
    need(1 <= row["interaction_frame"] <= row["total_frames"] <= 600000,
         "generic entry frame range differs")
    need(row["result"] <= 0xFFFF and all(row[key] <= 0xFF for key in
         ("host", "service", "mode", "page", "window", "field_lock")),
         "generic entry state range differs")
    need(row["field_lock"] in (0, 1) and row["main_callback2"] <= 0xFFFFFFFF,
         "generic entry callback/lock range differs")
    need(type(row["root_menu_opened"]) is bool, "generic entry root flag is not bool")
    need((row["root_frame"] > 0) == row["root_menu_opened"],
         "generic entry root frame/flag differs")
    if row["root_menu_opened"]:
        need(row["interaction_frame"] <= row["root_frame"] <= row["total_frames"],
             "generic entry root frame range differs")
        need((row["result"], row["host"], row["service"], row["mode"], row["page"],
              row["field_lock"]) == (9, 3, 3, 0, 0, 1) and row["window"] < 32,
             "generic entry opened state is not the authored root menu")
    need(type(row["baseline_readback"]) is list and len(row["baseline_readback"]) == 6,
         "generic entry baseline readback differs")
    need(type(row["progress_readback"]) is list and len(row["progress_readback"]) == 4,
         "generic entry progress readback differs")
    need(type(row["host_readback"]) is list and len(row["host_readback"]) == 2,
         "generic entry host readback differs")
    for values in (row["baseline_readback"], row["progress_readback"], row["host_readback"]):
        need(all(type(value) is int and 0 <= value <= 0xFF for value in values),
             "generic entry readback value differs")
    need(row["baseline_readback"][0] in (0, 1) and row["progress_readback"][0] in (0, 1),
         "generic entry HOF flag readback differs")
    if want["normalize"]:
        need(row["baseline_readback"] == [0, 0, 0, 0, 0, 0],
             "generic entry normalized baseline is not empty")
    return row


def expected(name):
    need(name in CASES, "unknown generic form carry case")
    roundtrip = name == CASES[0]
    return {
        "schema_version": 1,
        "status": "PASS",
        "scope": SCOPE,
        "case": name,
        "rom_sha256": repaired.ROM_SHA,
        "form_index": FORM_INDEX,
        "eligible_ordinal": ELIGIBLE_ORDINAL,
        "menu_page": MENU_PAGE,
        "menu_cursor": MENU_CURSOR,
        "base_species": 749,
        "target_species": 900,
        "final_species": 749,
        "moves": MOVES,
        "pp": PP,
        "pp_bonuses": PP_BONUSES,
        "representative_route_ids": REPRESENTATIVE_ROUTE_IDS,
        "generic_owner_rows_sha256": GENERIC_ROWS_SHA,
        "result": 0 if roundtrip else 20,
        "rounds": 2 if roundtrip else 1,
        "fresh_cores": 3 if roundtrip else 2,
        "automatic_saves": 2 if roundtrip else 0,
        "manual_saves": 2 if roundtrip else 1,
        "physical_host": [1, 36, 6, 3],
        "host_index": 3,
        "selected_party_slot": 1 if roundtrip else 6,
        "host_write_barriers": 7,
        "rtc_flash_bytes_preserved": 131072,
        "test_mode": False,
        "party_byte_preserved_on_reload": True,
        "four_move_slots_preserved": True,
        "nonselected_preserved": True,
        "starting_progress_individual_map_are_fixtures": True,
        "native_acceptance_claimed_for_all_61_individual_rows": False,
        "generic_owner_representative_accepted": True,
        "release_ready": False,
        "warnings_errors": 0,
    }


def validate(raw, name, code):
    need(type(code) is int and code == 0, "generic form process did not exit integer zero")
    row = common.strict_json(raw)
    want = expected(name)
    need(type(row) is dict and set(row) == set(want) | {"traces", "total_frames"},
         "generic form result schema differs")
    for key, value in want.items():
        need(common.same_typed(row[key], value), "generic form result differs: " + key)
    need(type(row["total_frames"]) is int and 1 <= row["total_frames"] <= 600000,
         "invalid generic form frame count")
    traces = row["traces"]
    need(type(traces) is list and len(traces) == want["rounds"], "generic form round count differs")
    roundtrip = name == CASES[0]
    expected_species = [900, 749] if roundtrip else [749]
    last = 0
    for index, trace in enumerate(traces):
        need(type(trace) is dict and set(trace) == set(TRACE), "generic form witness schema differs")
        for key in TRACE:
            need(type(trace[key]) is int and 0 <= trace[key] <= row["total_frames"] + 2000,
                 "invalid generic form witness: " + key)
        active = ["interaction", "root", "service", "page", "party", "returned", "saved", "reloaded"]
        if roundtrip:
            active.insert(5, "selection")
        for key in TRACE:
            if key == "species_after":
                continue
            need((trace[key] > 0) == (key in active), "generic form cancellation/operation witness differs")
        ordered = [key for key in active if key not in ("species_after",)]
        need(last < trace["interaction"], "generic form rounds overlap")
        need(all(trace[a] < trace[b] for a, b in zip(ordered, ordered[1:])),
             "generic form physical sequence incomplete")
        need(trace["species_after"] == expected_species[index], "generic form species sequence differs")
        last = trace["reloaded"]
    return row


def _representative_rows(inventory):
    rows = [
        row for row in inventory["owners"]["generic_carry"]["rows"]
        if row["target_species_id"] in (749, 900)
    ]
    rows.sort(key=lambda row: row["source_route"]["route_id"])
    return rows


def oracle(raw):
    source = repaired.layer.source
    model = json.loads(source.checked(ROOT / MODEL, MODEL_SHA))
    need(model["service_form_indices"][:7] == [37, 38, 39, 40, 41, 42, 43],
         "physical form menu prefix differs")
    host = model["hosts"][3]
    need(host["service_id"] == 3 and host["physical"] == {
        "elevation": 3,
        "host_key": "RAID_HOST_TOHOKU_SKY",
        "map_group": 1,
        "map_num": 36,
        "service": "FORM",
        "x": 6,
        "y": 3,
    }, "authored form host differs")
    form = model["forms"][FORM_INDEX]
    need(
        form["base_species"] == 749
        and form["target_species"] == 900
        and form["method_id"] == 4
        and form["unlock_id"] == 15
        and form["distributable"] is True,
        "Shaymin form service row differs",
    )
    inventory = form_inventory.build_inventory(
        ROOT,
        ROOT / json.loads((ROOT / "config/modernization_p03_stage73_consumers.json").read_text())["inputs"]["learnsets_zip"]["path"],
    )
    generic = inventory["owners"]["generic_carry"]
    need(generic["route_count"] == 61 and generic["species_count"] == 10,
         "generic carry owner count differs")
    need(generic["rows_sha256"] == GENERIC_ROWS_SHA, "generic carry owner digest differs")
    representative = _representative_rows(inventory)
    need(
        sorted(row["source_route"]["route_id"] for row in representative)
        == sorted(REPRESENTATIVE_ROUTE_IDS),
        "Shaymin representative routes differ",
    )
    need(sorted(row["source_route"]["project_move_id"] for row in representative) == [98, 235, 552],
         "Shaymin representative moves differ")
    ledger = json.loads((ROOT / LEDGER).read_text())
    need(ledger["p03"]["form_inventory"] == {
        "routes": 70,
        "species": 19,
        "generic_carry_routes": 61,
        "fixed_transition_routes": 4,
        "rotom_routes": 5,
    }, "finite form ledger differs")
    state = _stage_map_state(raw, 1, 36)
    data = bytes.fromhex(state["bg_hex"])
    matches = []
    for offset in range(0, len(data), 12):
        x, y, elevation, kind = struct.unpack_from("<hhBB", data, offset)
        if (x, y, elevation) == (6, 3, 3):
            matches.append((kind, struct.unpack_from("<I", data, offset + 8)[0]))
    need(len(matches) == 1 and matches[0][0] == 0, "authored form BG event is not unique/type 0")
    address = matches[0][1]
    at = address - 0x08000000
    prefix = bytes.fromhex("6a160480030023115b4009")
    need(0 <= at <= len(raw) - len(prefix) and raw[at:at + len(prefix)] == prefix,
         "authored form BG does not call actual service")
    return {
        "candidate": repaired.identity(raw),
        "authored_host": host,
        "form_row": form,
        "form_index": FORM_INDEX,
        "eligible_ordinal": ELIGIBLE_ORDINAL,
        "menu_page": MENU_PAGE,
        "menu_cursor": MENU_CURSOR,
        "generic_owner_route_count": generic["route_count"],
        "generic_owner_species_count": generic["species_count"],
        "generic_owner_rows_sha256": generic["rows_sha256"],
        "representative_rows": representative,
        "bg_script_address": hex(address),
        "bg_script_prefix": prefix.hex(),
        "starting_progress_and_individual_fixture": True,
    }


def run():
    module = base.load()
    out = module.prepare_output(OUT)
    (out / "result.json").unlink(missing_ok=True)
    source = repaired.layer.source
    candidate = ROOT / repaired.ROM
    seed = ROOT / module.SEED
    raw = source.checked(candidate, repaired.ROM_SHA)
    source.checked(seed, module.SEED_SHA)
    audit = oracle(raw)
    (out / "oracle.json").write_bytes(repaired.stable(audit))
    helper = source.checked(ROOT / base.PARENT_C, base.PARENT_C_SHA).decode()
    dependencies = {
        SELF,
        SOURCE,
        TEST,
        WORKFLOW,
        MODEL,
        LEDGER,
        "scripts/pr16_p03_form_gap_inventory.py",
        "tools/modernization_learnsets.py",
        "tools/modernization_p03_stage73_consumers.py",
        base.SELF,
        base.PARENT,
        base.PARENT_C,
        "scripts/pr16_repaired_acceptance.py",
        "scripts/pr16_p07_preserved_layer.py",
        "scripts/pr16_integration_continuation.py",
        "scripts/run_modernization_p03_fullslots_e2e.py",
        "tools/trainer_final/kanto_events.py",
        "config/modernization_p03_stage73_consumers.json",
        "config/active_play_baseline.json",
        "design/active_play_baseline.md",
        *(path for path, _ in module.EMBEDDED),
    }
    config = json.loads((ROOT / "config/modernization_stage79_cumulative_mgba.json").read_bytes())
    p02 = next(domain for domain in config["domains"] if domain["id"] == "p02")
    for binding in (p02["runner"], *p02["dependencies"]):
        need(common.identity(ROOT / binding["path"]) == {key: binding[key] for key in ("size", "sha256")},
             "generic form embedded dependency differs")
        dependencies.add(binding["path"])
    bindings = {path: common.identity(ROOT / path) for path in sorted(dependencies)}
    protected = {str(path): common.identity(path) for path in (seed, candidate)}
    results = []
    failures = []
    diagnostic_results = []
    diagnostic_failures = []
    guards = []
    try:
        with tempfile.TemporaryDirectory(prefix="pr16-generic-form-", dir=ROOT / ".local") as temporary:
            work = Path(temporary)
            for index, (src, target) in enumerate(module.EMBEDDED):
                (work / target).write_text(module.embed((ROOT / src).read_text(), "generic_form_embedded_" + str(index)))
            (work / "pr16_form_breeding_helpers.c").write_text(module.embed(helper, "generic_form_breeding_helpers"))
            binary = work / "runner"
            _, _, process = common.capture(
                ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-Itools", "-I" + str(work),
                 str(ROOT / SOURCE), "-lmgba", "-o", str(binary)],
                out / "compile",
                120,
            )
            need(common.require_exited(process) == 0, "generic form C compile failed")
            for guard in module.GUARDS:
                stdout, stderr, process = common.capture([str(binary), "--guard-check", guard], out / ("guard-" + guard), 10)
                module.validate_guard(stdout, stderr, process)
                guards.append(guard)

            def probe_one(probe):
                name = probe["name"]
                private = work / (name + ".srm")
                shutil.copyfile(seed, private)
                stdout, stderr, process = common.capture(
                    [str(binary), str(candidate), str(private), repaired.ROM_SHA, module.SEED_SHA,
                     name, str(out / name)],
                    out / name,
                    300,
                )
                try:
                    row = validate_probe(stdout, name, common.require_exited(process))
                    need(b"mGBA[" not in stderr, "generic entry probe emulator warning")
                    return {"name": name, "result": row, "process": process}, None
                except (ValueError, RuntimeError, KeyError, TypeError) as exc:
                    return None, {"name": name, "error": str(exc), "process": process}

            with ThreadPoolExecutor(max_workers=4) as pool:
                for row, error in pool.map(probe_one, PROBES):
                    if row:
                        diagnostic_results.append(row)
                    if error:
                        diagnostic_failures.append(error)
            diagnostic_report = {
                "schema_version": 1,
                "status": "FAIL" if diagnostic_failures else "PASS_DIAGNOSTIC_ONLY",
                "scope": ENTRY_SCOPE,
                "candidate": repaired.identity(raw),
                "configuration": list(PROBES),
                "observations": diagnostic_results,
                "failures": diagnostic_failures,
                "actual_new_processes": len(PROBES),
                "successful_fresh_cores": len(diagnostic_results),
                "root_open_cases": [
                    row["name"] for row in diagnostic_results
                    if row["result"]["root_menu_opened"]
                ],
                "acceptance_claimed": False,
                "release_ready": False,
            }
            (out / "entry-diagnostic.json").write_bytes(repaired.stable(diagnostic_report))

            def one(name):
                private = work / (name + ".srm")
                shutil.copyfile(seed, private)
                stdout, stderr, process = common.capture(
                    [str(binary), str(candidate), str(private), repaired.ROM_SHA, module.SEED_SHA, name, str(out / name)],
                    out / name,
                    300,
                )
                try:
                    row = validate(stdout, name, common.require_exited(process))
                    need(b"mGBA[" not in stderr, "generic form emulator warning")
                    return {"name": name, "result": row, "process": process}, None
                except (ValueError, RuntimeError, KeyError, TypeError) as exc:
                    return None, {"name": name, "error": str(exc), "process": process}

            with ThreadPoolExecutor(max_workers=2) as pool:
                for row, error in pool.map(one, CASES):
                    if row:
                        results.append(row)
                    if error:
                        failures.append(error)
    finally:
        need(protected == {path: common.identity(Path(path)) for path in protected},
             "generic form original seed or candidate changed")
        need(bindings == {path: common.identity(ROOT / path) for path in bindings},
             "generic form protected source/baseline changed")
    report = {
        "schema_version": 1,
        "status": "FAIL" if failures or diagnostic_failures else "PASS",
        "scope": SCOPE,
        "candidate": repaired.identity(raw),
        "oracle": audit,
        "sources": bindings,
        "results": results,
        "failures": failures,
        "guard_checks": guards,
        "entry_diagnostic_status": "FAIL" if diagnostic_failures else "PASS_DIAGNOSTIC_ONLY",
        "entry_diagnostic_processes": len(PROBES),
        "entry_diagnostic_successful_fresh_cores": len(diagnostic_results),
        "entry_diagnostic_root_open_cases": [
            row["name"] for row in diagnostic_results
            if row["result"]["root_menu_opened"]
        ],
        "diagnostic_failures": diagnostic_failures,
        "actual_new_processes": len(CASES),
        "successful_fresh_cores": sum(row["result"]["fresh_cores"] for row in results),
        "generic_form_carry_physical_accepted": not failures,
        "fixed_form_transition_physical_accepted": False,
        "full_p03_acceptance": False,
        "release_ready": False,
        "old_runs_relabelled": 0,
    }
    (out / "result.json").write_bytes(repaired.stable(report))
    need(not diagnostic_failures, "generic entry diagnostic failed; inspect original stderr/screenshots")
    need(not failures, "generic form carry failed; inspect original stderr/screenshots")
    return report


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, struct.error) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
