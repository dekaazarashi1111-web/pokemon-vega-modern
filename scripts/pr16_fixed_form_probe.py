#!/usr/bin/env python3
"""Run a diagnostic-only native probe for the four finite fixed FORM targets.

The probe uses the authored FORM host and ordinary menu/party input on four
fresh cores.  It records what the runtime does at each canonical service row,
but deliberately does not claim physical acceptance or close P03.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import pr16_breeding_delta as base
import pr16_fixed_form_contract as contract
import pr16_generic_form_carry as generic

repaired = base.repaired
need = repaired.need
common = base.load().common

SELF = "scripts/pr16_fixed_form_probe.py"
SOURCE = "tools/mgba_pr16_fixed_form_probe.c"
TEST = "tests/test_pr16_fixed_form_probe.py"
WORKFLOW = ".github/workflows/pr16-fixed-form-probe.yml"
CONTRACT_SCRIPT = "scripts/pr16_fixed_form_contract.py"
CONTRACT_JSON = "content/modernization/pr16_fixed_form_contract.json"
MODEL = "content/collection_supply_v1/canonical_model.json"
OUT = ROOT / ".local/pr16-fixed-form-probe"
SCOPE = "PR16_P03_FIXED_FORM_TRANSITION_NATIVE_PROBE"
MENU_NAVIGATION = "canonical-ordinal-native-input"
ROWS_PER_PAGE = 5
MAX_PAGES = 80

CASES = {
    "necrozma-dusk-mane-native-probe": {
        "family": "necrozma_fixed_transition",
        "route_id": "667255b406678096a7fa9344",
        "form_index": 245,
        "base_species": 1198,
        "target_species": 1260,
        "project_move": 690,
    },
    "necrozma-dawn-wings-native-probe": {
        "family": "necrozma_fixed_transition",
        "route_id": "a79bbbec71c9a6be03a7d1e4",
        "form_index": 246,
        "base_species": 1198,
        "target_species": 1261,
        "project_move": 669,
    },
    "zacian-crowned-native-probe": {
        "family": "crowned_battle_transition",
        "route_id": "371ffcca84ed4eb8fbb6d56b",
        "form_index": 280,
        "base_species": 1361,
        "target_species": 1386,
        "project_move": 768,
    },
    "zamazenta-crowned-native-probe": {
        "family": "crowned_battle_transition",
        "route_id": "2a8a2a856af40ec96087c9a7",
        "form_index": 281,
        "base_species": 1362,
        "target_species": 1387,
        "project_move": 769,
    },
}

BOOL_KEYS = (
    "menu_opened",
    "party_opened",
    "target_match",
    "selection_sent",
    "field_returned",
    "identity_preserved",
    "nonselected_preserved",
    "starting_progress_individual_map_are_fixtures",
    "fresh_core",
    "input_only_after_guard",
    "acceptance_claimed",
    "p03_fixed_form_gap_closed",
    "full_p03_acceptance",
    "release_ready",
)


def _learnsets_zip() -> Path:
    config = json.loads(
        (ROOT / "config/modernization_p03_stage73_consumers.json").read_text(
            encoding="utf-8"
        )
    )
    return ROOT / config["inputs"]["learnsets_zip"]["path"]


def _contract_and_ordinals() -> tuple[dict, dict[str, int]]:
    built = contract.build_contract(ROOT, _learnsets_zip())
    tracked = json.loads((ROOT / CONTRACT_JSON).read_text(encoding="utf-8"))
    need(built == tracked, "tracked fixed FORM contract differs from regeneration")
    model = json.loads((ROOT / MODEL).read_text(encoding="utf-8"))
    service = model["service_form_indices"]
    need(type(service) is list and len(service) == 95, "FORM service index inventory differs")
    targets = {row["target_species"]: row for row in built["targets"]}
    need(set(targets) == {1260, 1261, 1386, 1387}, "fixed FORM target set differs")
    ordinals: dict[str, int] = {}
    for name, expected in CASES.items():
        row = targets[expected["target_species"]]
        for key in ("family", "route_id", "service_index", "base_species", "project_move_id"):
            want_key = {
                "service_index": "form_index",
                "project_move_id": "project_move",
            }.get(key, key)
            need(row[key] == expected[want_key], f"fixed FORM case contract differs: {name} {key}")
        need(row["native_acceptance_required"] is True,
             "fixed FORM native requirement disappeared")
        ordinal = service.index(expected["form_index"])
        need(0 <= ordinal < MAX_PAGES * ROWS_PER_PAGE,
             "fixed FORM canonical ordinal is outside bounded menu")
        ordinals[name] = ordinal
    return built, ordinals


def expected(name: str, ordinal: int) -> dict:
    need(name in CASES, "unknown fixed FORM probe case")
    case = CASES[name]
    return {
        "schema_version": 1,
        "status": "OBSERVED",
        "scope": SCOPE,
        "case": name,
        "family": case["family"],
        "route_id": case["route_id"],
        "rom_sha256": repaired.ROM_SHA,
        "form_index": case["form_index"],
        "canonical_ordinal": ordinal,
        "menu_page": ordinal // ROWS_PER_PAGE,
        "menu_cursor": ordinal % ROWS_PER_PAGE,
        "menu_navigation": MENU_NAVIGATION,
        "base_species": case["base_species"],
        "target_species": case["target_species"],
        "project_move": case["project_move"],
        "starting_progress_individual_map_are_fixtures": True,
        "fresh_core": True,
        "input_only_after_guard": True,
        "warnings_errors": 0,
        "acceptance_claimed": False,
        "p03_fixed_form_gap_closed": False,
        "full_p03_acceptance": False,
        "release_ready": False,
    }


def validate(raw: bytes, name: str, ordinal: int, code: int) -> dict:
    need(type(code) is int and code == 0,
         "fixed FORM probe did not exit integer zero")
    row = common.strict_json(raw)
    want = expected(name, ordinal)
    dynamic = {
        "menu_opened",
        "party_opened",
        "target_match",
        "selection_sent",
        "field_returned",
        "probe_outcome",
        "wait_kind",
        "pending_form",
        "result",
        "main_callback2",
        "window",
        "species_after",
        "held_item_after",
        "moves_after",
        "pp_after",
        "pp_bonuses_after",
        "identity_preserved",
        "nonselected_preserved",
        "save_counter_before",
        "save_counter_after",
        "total_frames",
    }
    need(type(row) is dict and set(row) == set(want) | dynamic,
         "fixed FORM probe result schema differs")
    for key, value in want.items():
        need(common.same_typed(row[key], value),
             "fixed FORM probe result differs: " + key)
    for key in BOOL_KEYS:
        need(type(row[key]) is bool, "fixed FORM probe bool differs: " + key)
    need(row["identity_preserved"] and row["nonselected_preserved"],
         "fixed FORM probe changed party identity/nonselected individual")
    need(not row["acceptance_claimed"]
         and not row["p03_fixed_form_gap_closed"]
         and not row["full_p03_acceptance"]
         and not row["release_ready"],
         "diagnostic probe overclaimed acceptance")
    for key in (
        "wait_kind", "pending_form", "result", "main_callback2", "window",
        "species_after", "held_item_after", "pp_bonuses_after",
        "save_counter_before", "save_counter_after", "total_frames",
    ):
        need(type(row[key]) is int and row[key] >= 0,
             "fixed FORM probe integer differs: " + key)
    need(row["wait_kind"] in (0, 1, 2), "fixed FORM wait kind differs")
    need(row["pending_form"] <= 0xFFFF and row["result"] <= 0xFFFF,
         "fixed FORM state range differs")
    need(row["main_callback2"] <= 0xFFFFFFFF and row["window"] <= 0xFF,
         "fixed FORM callback/window range differs")
    need(1 <= row["total_frames"] <= 600000,
         "fixed FORM total frame range differs")
    need(row["save_counter_after"] >= row["save_counter_before"],
         "fixed FORM save counter moved backwards")
    need(type(row["moves_after"]) is list and len(row["moves_after"]) == 4,
         "fixed FORM move vector differs")
    need(type(row["pp_after"]) is list and len(row["pp_after"]) == 4,
         "fixed FORM PP vector differs")
    need(all(type(value) is int and 0 <= value <= 1062
             for value in row["moves_after"]),
         "fixed FORM move value differs")
    need(all(type(value) is int and 0 <= value <= 63
             for value in row["pp_after"]),
         "fixed FORM PP value differs")
    need(0 <= row["pp_bonuses_after"] <= 0xFF,
         "fixed FORM PP bonus value differs")
    need(row["probe_outcome"] in {
        "menu-navigation-failed",
        "native-terminal",
        "party-not-opened",
        "pending-mismatch",
        "selected-target",
        "party-slot-not-selected",
    }, "fixed FORM probe outcome differs")
    need(row["party_opened"] == (row["wait_kind"] == 1),
         "fixed FORM party/wait witness differs")
    need(not row["target_match"] or (
        row["party_opened"] and row["pending_form"] == row["form_index"]
    ), "fixed FORM target match witness differs")
    need(not row["selection_sent"] or row["target_match"],
         "fixed FORM selection was sent to a mismatched row")
    if row["probe_outcome"] == "selected-target":
        need(row["selection_sent"], "selected target lacks native selection witness")
    return row


def run() -> dict:
    module = base.load()
    out = module.prepare_output(OUT)
    (out / "result.json").unlink(missing_ok=True)
    source = repaired.layer.source
    candidate = ROOT / repaired.ROM
    seed = ROOT / module.SEED
    raw = source.checked(candidate, repaired.ROM_SHA)
    source.checked(seed, module.SEED_SHA)
    fixed_contract, ordinals = _contract_and_ordinals()
    helper = source.checked(ROOT / base.PARENT_C, base.PARENT_C_SHA).decode()

    dependencies = {
        SELF,
        SOURCE,
        TEST,
        WORKFLOW,
        CONTRACT_SCRIPT,
        CONTRACT_JSON,
        MODEL,
        "scripts/pr16_generic_form_carry.py",
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
    config = json.loads(
        (ROOT / "config/modernization_stage79_cumulative_mgba.json").read_bytes()
    )
    p02 = next(domain for domain in config["domains"] if domain["id"] == "p02")
    for binding in (p02["runner"], *p02["dependencies"]):
        need(common.identity(ROOT / binding["path"]) == {
            key: binding[key] for key in ("size", "sha256")
        }, "fixed FORM embedded dependency differs")
        dependencies.add(binding["path"])
    bindings = {path: common.identity(ROOT / path) for path in sorted(dependencies)}
    protected = {str(path): common.identity(path) for path in (seed, candidate)}
    observations = []
    failures = []
    guards = []
    try:
        with tempfile.TemporaryDirectory(
            prefix="pr16-fixed-form-probe-", dir=ROOT / ".local"
        ) as temporary:
            work = Path(temporary)
            for index, (src, target) in enumerate(module.EMBEDDED):
                (work / target).write_text(
                    module.embed(
                        (ROOT / src).read_text(),
                        "fixed_form_probe_embedded_" + str(index),
                    )
                )
            (work / "pr16_form_breeding_helpers.c").write_text(
                module.embed(helper, "fixed_form_probe_helpers")
            )
            binary = work / "runner"
            _, _, process = common.capture(
                [
                    "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-Itools", "-I" + str(work), str(ROOT / SOURCE),
                    "-lmgba", "-o", str(binary),
                ],
                out / "compile",
                120,
            )
            need(common.require_exited(process) == 0,
                 "fixed FORM probe C compile failed")
            for guard in module.GUARDS:
                stdout, stderr, process = common.capture(
                    [str(binary), "--guard-check", guard],
                    out / ("guard-" + guard),
                    10,
                )
                module.validate_guard(stdout, stderr, process)
                guards.append(guard)

            def one(name: str):
                private = work / (name + ".srm")
                shutil.copyfile(seed, private)
                stdout, stderr, process = common.capture(
                    [
                        str(binary), str(candidate), str(private), repaired.ROM_SHA,
                        module.SEED_SHA, name, str(ordinals[name]),
                        str(out / name),
                    ],
                    out / name,
                    300,
                )
                try:
                    row = validate(
                        stdout, name, ordinals[name], common.require_exited(process)
                    )
                    need(b"mGBA[" not in stderr,
                         "fixed FORM probe emulator warning")
                    return {"name": name, "result": row, "process": process}, None
                except (ValueError, RuntimeError, KeyError, TypeError) as exc:
                    return None, {
                        "name": name,
                        "error": str(exc),
                        "process": process,
                    }

            with ThreadPoolExecutor(max_workers=4) as pool:
                for row, error in pool.map(one, CASES):
                    if row:
                        observations.append(row)
                    if error:
                        failures.append(error)
    finally:
        need(protected == {
            path: common.identity(Path(path)) for path in protected
        }, "fixed FORM probe changed original seed or candidate")
        need(bindings == {
            path: common.identity(ROOT / path) for path in bindings
        }, "fixed FORM protected source/baseline changed")

    matched = [
        row["name"] for row in observations if row["result"]["target_match"]
    ]
    selected = [
        row["name"] for row in observations if row["result"]["selection_sent"]
    ]
    report = {
        "schema_version": 1,
        "status": "FAIL" if failures else "PASS_DIAGNOSTIC_ONLY",
        "scope": SCOPE,
        "candidate": repaired.identity(raw),
        "contract": fixed_contract,
        "canonical_ordinals": ordinals,
        "sources": bindings,
        "observations": observations,
        "failures": failures,
        "guard_checks": guards,
        "actual_new_processes": len(CASES),
        "successful_fresh_cores": len(observations),
        "native_rows_matched": matched,
        "native_selections_sent": selected,
        "native_acceptance_claimed": False,
        "p03_fixed_form_gap_closed": False,
        "full_p03_acceptance": False,
        "release_ready": False,
        "old_runs_relabelled": 0,
    }
    (out / "result.json").write_bytes(repaired.stable(report))
    need(not failures, "fixed FORM diagnostic failed; inspect raw evidence")
    return report


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
