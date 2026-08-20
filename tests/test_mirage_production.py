from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_mirage_production as mirage  # noqa: E402
from scripts import rebuild_mirage_production_from_clean as rebuild  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


MODES = ROOT / "manifests/facility_modes.csv"
TRAINERS = ROOT / "manifests/facility_trainers.csv"
RENTALS = ROOT / "manifests/facility_rentals.csv"
REWARDS = ROOT / "manifests/facility_rewards.csv"
TRAINER_IDS = ROOT / "manifests/trainer_ids.csv"
BINDINGS = ROOT / "config/mirage_production_bindings.csv"
RUNTIME_C = ROOT / "overlays/mirage_production/mirage_production.c"
RUNTIME_H = ROOT / "overlays/mirage_production/mirage_production.h"
RUNNER = ROOT / "tools/mgba_mirage_production_smoke.c"

STAGE37 = ROOT / "build/stages/37_event_design.gba"
STAGE37_META = ROOT / "build/stages/37_event_design.json"
STAGE37_ALLOC = ROOT / "build/stages/37_allocation.json"
STAGE38 = ROOT / "build/stages/38_mirage_production.gba"
STAGE38_META = ROOT / "build/stages/38_mirage_production.json"
STAGE38_ALLOC = ROOT / "build/stages/38_allocation.json"
SYMBOLS = ROOT / "generated/runtime/mirage_production_symbols.json"
CASES = ROOT / "generated/runtime/mirage_production_mgba_cases.csv"
AUDIT = ROOT / "reports/generated/mirage_production_audit.json"
COVERAGE = ROOT / "reports/generated/mirage_production_coverage.json"
QUICK = ROOT / "build/stages/38_mgba_mirage_production_quick.json"
FULL = ROOT / "build/stages/38_mgba_mirage_production_full.json"
CLEAN_EVIDENCE = ROOT / "build/stages/38_clean_rebuild.json"

STAGE37_SHA256 = "76d4f6a4005a815e6faf33f2ae24c18c2a7b4a1fe6f1f313e6f1837ecaf5cb7c"
STAGE37_META_SHA256 = "712ecdcd15b7fd7ac3003771eca45fd6ffd6e4dcb410436e3204e0862f1d9873"
STAGE37_ALLOC_SHA256 = "a7d2fc5dbcc4b31920fe05f45ccde49abf211db03ca0b459efa3512e9ac8660c"

REQUIRED_ENTRYPOINTS = {
    "MirageProduction_Probe",
    "MirageProduction_FieldEnter",
    "MirageProduction_CommitSelection",
    "MirageProduction_CommitRound4Mechanic",
    "MirageProduction_PrepareBattle",
    "MirageProduction_FinalizeBattleCopy",
    "MirageProduction_AfterBattle",
    "MirageProduction_Complete",
    "MirageProduction_Abort",
    "MirageProduction_Recover",
    "MirageProduction_MapTransitionRecover",
    "MirageProduction_SaveLoadAdapter",
    "MirageProduction_BuildTrainerPartyAdapter",
    "MirageProduction_LoadProperAbilityBattleDataAdapter",
    "MirageProduction_TestWarpToReception",
    "MirageProduction_TestInjectPersistenceFault",
}

ACCEPTANCE_KEYS = {
    "STAGE37_IDENTITY_PRIVATE_IMMUTABLE",
    "MIRAGE_MANIFEST_CROSSWALK_EXACT",
    "NORMAL_FIELD_ENTRY_4_ROUNDS_28_BATTLES",
    "ROUND_UNLOCK_NO_SKIP",
    "LEVEL100_SINGLE_3V3_AI_GIMMICKS",
    "ROUND4_LOCK_ONE_GIMMICK_NO_LEAK",
    "DETERMINISTIC_POOL_NO_REBALANCE",
    "VIRTUAL_ITEM_TIERS_ISOLATED",
    "ATOMIC_RECORD_CLAIM_SAVE_RELOAD",
    "BADGE_EXACT_RESTORE_ALL_EXITS",
    "BATTLE_LOCAL_CLEANUP_ALL_EXITS",
    "UPSTREAM_RUNTIME_CONTENT_REGRESSION",
    "PRO_WAITING_AREAS_UNCHANGED",
    "CLEAN_REBUILD_BPS_EXACT",
    "DECLARED_SPAN_OVERLAP_MGBA_TWO_PROCESS",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON root must be an object: {path}")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MirageProductionSourceTests(unittest.TestCase):
    def test_four_modes_four_pools_five_rewards_and_four_ids_are_exact(self) -> None:
        modes = [row for row in _rows(MODES) if row["party_owner"] == "MIRAGE"]
        self.assertEqual(len(modes), 4)
        self.assertEqual(
            [row["mode_key"] for row in modes],
            [f"FACILITY_MODE_MIRAGE_ROUND_{round_}" for round_ in range(1, 5)],
        )
        self.assertEqual([row["battle_count"] for row in modes], ["7"] * 4)
        self.assertEqual([row["selection_count"] for row in modes], ["3"] * 4)
        self.assertEqual([row["format"] for row in modes], ["SINGLE"] * 4)
        self.assertEqual([row["level_policy"] for row in modes], ["LEVEL_100_FIXED"] * 4)
        self.assertEqual([row["ai_profile_key"] for row in modes], ["AI_FULL_SMART"] * 4)
        self.assertEqual([row["state_owner"] for row in modes], ["OWNER_KEY_MIRAGE_STATE"] * 4)
        self.assertEqual(
            [row["mechanic_policy"] for row in modes],
            ["NONE", "MEGA", "Z", "ONE_OF_MEGA_Z_TERA"],
        )

        trainers = [row for row in _rows(TRAINERS)
                    if row["facility_trainer_key"].startswith("FACILITY_TRAINER_KEY_MIRAGE_")]
        self.assertEqual(len(trainers), 4)
        self.assertEqual(
            [row["pool_key"] for row in trainers],
            [f"TRAINER_POOL_KEY_MIRAGE_{round_}" for round_ in range(1, 5)],
        )
        rental_keys = {f"RENTAL_KEY_SPECIAL_{index:02d}" for index in range(1, 7)}
        for row in trainers:
            self.assertEqual({row[f"rental_key{index}"] for index in range(1, 7)}, rental_keys)
            self.assertEqual(row["format"], "SINGLE")
            self.assertEqual(row["ai_profile_key"], "AI_FULL_SMART")

        special = [row for row in _rows(RENTALS)
                   if row["pool_key"] == "RENTAL_POOL_KEY_SPECIAL"]
        self.assertEqual(len(special), 6)
        self.assertEqual({row["rental_key"] for row in special}, rental_keys)
        self.assertTrue(all(row["status"] == "ACTIVE" for row in special))

        rewards = [row for row in _rows(REWARDS)
                   if row["trigger_kind"] == "MIRAGE_VIRTUAL_ITEM"]
        self.assertEqual(len(rewards), 5)
        self.assertEqual([int(row["streak"]) for row in rewards], [7, 14, 21, 28, 35])
        self.assertEqual([int(row["amount"]) for row in rewards], [-1, -2, -3, -4, -5])
        self.assertEqual([row["currency_key"] for row in rewards], ["CURRENCY_KEY_MIRAGE"] * 5)
        self.assertEqual([row["repeatability"] for row in rewards],
                         ["REPEATABLE", "REPEATABLE", "REPEATABLE", "ONCE", "ONCE"])
        self.assertEqual([row["claim_key"] for row in rewards[-2:]],
                         ["CLAIM_KEY_MIRAGE_ONCE", "CLAIM_KEY_MIRAGE_TOP"])

        trainer_ids = [row for row in _rows(TRAINER_IDS)
                       if row["trainer_key"].startswith("FACILITY_TRAINER_KEY_MIRAGE_")]
        self.assertEqual(len(trainer_ids), 4)
        self.assertEqual([int(row["id"]) for row in trainer_ids], [745, 746, 747, 748])

        model = mirage._load_model(mirage._input_contract())
        self.assertEqual(
            [
                (row["species_id"], row["item_id"], row["move_ids"],
                 row["ability_id"], row["nature_id"], row["iv"],
                 row["ev_values"], row["battle_level"])
                for row in model["rentals"]
            ],
            [
                (428, 891, [650, 59, 546, 227], 118, 12, 31, [85] * 6, 100),
                (1346, 939, [497, 58, 375, 202], 247, 12, 31, [85] * 6, 100),
                (42, 187, [490, 333, 350, 390], 93, 12, 31, [85] * 6, 100),
                (1550, 892, [499, 667, 89, 390], 126, 12, 31, [85] * 6, 100),
                (532, 903, [1001, 188, 94, 303], 145, 12, 31, [85] * 6, 100),
                (324, 924, [578, 56, 85, 195], 11, 12, 31, [85] * 6, 100),
            ],
        )
        self.assertEqual(
            [(row["streak"], row["tier"], row["claim_mask"])
             for row in model["rewards"]],
            [(7, 1, 0), (14, 2, 0), (21, 3, 0), (28, 4, 1), (35, 5, 2)],
        )

    def test_runtime_exports_atomic_production_and_test_contracts(self) -> None:
        header = RUNTIME_H.read_text(encoding="utf-8")
        runtime = RUNTIME_C.read_text(encoding="utf-8")
        for symbol in REQUIRED_ENTRYPOINTS:
            self.assertIn(symbol, header, msg=symbol)
            self.assertIn(symbol, runtime, msg=symbol)
        self.assertIn("0x0203EE00", header + runtime)
        self.assertIn("PERSIST_FAILED", header + runtime)
        self.assertIn("TestInjectPersistenceFault", runtime)
        self.assertIn("MIRAGE_PRODUCTION_JOURNAL_FIRST_RECORD", runtime)
        self.assertIn("MIRAGE_BATTLE_MON_ABILITY_OFFSET", runtime)
        self.assertEqual(runtime.count("FN_CHANGEKIT_LOAD_PROPER_ABILITY();"), 1)
        self.assertEqual(runtime.count("FN_HEAL_PLAYER_PARTY();"), 1)
        self.assertNotIn("OWNER_KEY_FACTORY_STATE", runtime)

    def test_save_journal_and_volatile_ram_keep_the_existing_abi(self) -> None:
        save_rows = _rows(ROOT / "config/save_layout.csv")
        mirage_rows = [row for row in save_rows
                       if row["symbol"] == "mirage_records_and_item_reward"]
        self.assertEqual(len(mirage_rows), 1)
        save = mirage_rows[0]
        self.assertEqual(
            (int(save["start"], 0), int(save["end_exclusive"], 0), int(save["size"])),
            (0x2574, 0x259C, 40),
        )
        self.assertIn("current_record[4..7]", save["notes"])

        ram_rows = _rows(ROOT / "config/ram_layout.csv")
        runtime_rows = [row for row in ram_rows
                        if row["owner"] == "T21_MIRAGE_PRODUCTION"]
        self.assertEqual(len(runtime_rows), 1)
        ram = runtime_rows[0]
        self.assertEqual(
            (int(ram["start"], 0), int(ram["end_exclusive"], 0), int(ram["size"])),
            (0x0203EE00, 0x0203F098, 664),
        )
        self.assertLessEqual(int(ram["end_exclusive"], 0), 0x0203F101)

        source = r"""
#include <stddef.h>
#include "overlays/save_migration/save_migration.h"
#include "overlays/mirage_production/mirage_production.h"
_Static_assert(sizeof(VegaMirageState) == 40u, "Mirage ABI size");
_Static_assert(offsetof(VegaModernSaveData, mirage) == 0x65cu,
               "Mirage ledger offset");
_Static_assert(offsetof(VegaMirageState, current_record)
               + 4u * sizeof(uint16_t) == 8u, "journal start");
_Static_assert(offsetof(VegaMirageState, current_record)
               + 8u * sizeof(uint16_t) == 16u, "journal end");
_Static_assert(offsetof(VegaMirageState, best_record) == 16u,
               "best record offset");
_Static_assert(offsetof(VegaMirageState, reward_claim_bits) == 32u,
               "reward claim offset");
_Static_assert(offsetof(VegaMirageState, item_reward_transaction_id) == 36u,
               "reward transaction offset");
_Static_assert(sizeof(MirageProductionState) == 664u,
               "volatile runtime size");
_Static_assert(MIRAGE_PRODUCTION_STATE_ADDRESS
               + sizeof(MirageProductionState) <= 0x0203F101u,
               "existing battle UI help-video state overlap");
_Static_assert(offsetof(MirageProductionState, party_snapshot) == 0x40u,
               "party snapshot offset");
_Static_assert(sizeof(((MirageProductionState *)0)->party_snapshot) == 600u,
               "party snapshot size");
int main(void) { return 0; }
"""
        with tempfile.TemporaryDirectory(prefix="mirage-save-abi-") as raw:
            output = Path(raw) / "save-abi"
            completed = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 f"-I{ROOT}", "-x", "c", "-", "-o", str(output)],
                input=source, text=True, capture_output=True, check=False,
                cwd=ROOT,
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)

    def test_mgba_runner_compiles_with_werror(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mirage-mgba-runner-") as raw:
            output = Path(raw) / "mgba-mirage-production"
            completed = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 f"-I{ROOT / 'tools'}", str(RUNNER), "-lmgba", "-o", str(output)],
                text=True, capture_output=True, check=False, cwd=ROOT,
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)


class MirageProductionPhysicalBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage37 = STAGE37.read_bytes()
        cls.rom = STAGE38.read_bytes()
        cls.metadata = _json(STAGE38_META)
        cls.allocation = _json(STAGE38_ALLOC)
        cls.symbols = _json(SYMBOLS)
        cls.bindings = _rows(BINDINGS)

    def test_pinned_stage37_and_stage38_identity_are_exact(self) -> None:
        self.assertEqual(len(self.stage37), 32 * 1024 * 1024)
        self.assertEqual(_sha(STAGE37), STAGE37_SHA256)
        self.assertEqual(_sha(STAGE37_META), STAGE37_META_SHA256)
        self.assertEqual(_sha(STAGE37_ALLOC), STAGE37_ALLOC_SHA256)
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(_sha(STAGE38), self.metadata["output"]["sha256"])
        self.assertEqual(self.metadata["input"]["sha256"], STAGE37_SHA256)
        self.assertEqual(self.metadata["status"], "PASS")
        self.assertEqual(self.metadata["change_audit"]["outside_declared_span_count"], 0)
        self.assertEqual(self.metadata["change_audit"]["declared_span_overlap_count"], 0)
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)

    def test_runtime_symbols_and_seven_rooted_physical_patches_are_live(self) -> None:
        entrypoints = self.symbols["entrypoints"]
        self.assertTrue(REQUIRED_ENTRYPOINTS <= set(entrypoints))
        payload = self.metadata["runtime"]["payload"]
        start = int(payload["address"])
        end = start + int(payload["size"])
        for symbol in REQUIRED_ENTRYPOINTS:
            address = int(entrypoints[symbol])
            self.assertEqual(address & 1, 1, msg=symbol)
            self.assertTrue(start <= (address & ~1) < end, msg=symbol)

        self.assertEqual(len(self.bindings), 7)
        patches = {row["name"]: row for row in self.metadata["physical_bindings"]["root_patches"]}
        self.assertEqual(set(patches), {row["binding_key"] for row in self.bindings})
        ability = patches["MIRAGE_ABILITY_LOAD_CHAIN"]
        self.assertEqual(ability["address"], 0x090973FC)
        self.assertEqual(ability["expected_hex"], "6bf298fd")
        self.assertEqual(
            ability["target_symbol"],
            "native::MirageProduction_LoadProperAbilityBattleDataAdapter",
        )
        for binding in self.bindings:
            patch = patches[binding["binding_key"]]
            address = int(binding["address"], 0)
            replacement = bytes.fromhex(patch["replacement_hex"])
            offset = address - 0x08000000
            self.assertEqual(self.stage37[offset:offset + len(bytes.fromhex(binding["expected_hex"]))],
                             bytes.fromhex(binding["expected_hex"]), msg=binding["binding_key"])
            self.assertEqual(self.rom[offset:offset + len(replacement)], replacement,
                             msg=binding["binding_key"])
            if binding["patch_mode"] in {"THUMB_BL", "THUMB_JUMP"}:
                symbol = binding["target_symbol"].removeprefix("native::")
                self.assertEqual(int(patch["target"]), int(entrypoints[symbol]))

        # A fresh mGBA core must reproduce the stock title initialization
        # order before invoking the rooted load adapter.  Pin the exact stock
        # SetSaveBlocksPointers owner used by the runner so a zero
        # gPokemonStoragePtr can never turn reset recovery into a false ROM
        # failure (or corrupt storage sections 5..13 in the fixture save).
        pointer_setup = 0x0804B810 - 0x08000000
        self.assertEqual(
            self.rom[pointer_setup:pointer_setup + 12],
            bytes.fromhex("30b50c4c2568f8f739fe7c21"),
        )

    def test_field_graph_sets_respawn_14_once_after_commit(self) -> None:
        field = self.symbols["scripts"]
        self.assertEqual(field["party_selection_special"], 0x29)
        self.assertTrue(field["party_selection_waitstate"])
        self.assertIsNone(field["pre_battle_special"])
        self.assertFalse(field["pre_battle_waitstate"])
        self.assertEqual(
            field["pre_battle_heal_owner"], "RUNTIME_FINALIZE_BATTLE_COPY"
        )
        self.assertEqual(field["special_operation_count"], 1)
        self.assertEqual(field["waitstate_operation_count"], 1)
        self.assertEqual(field["trainerbattle_command"], 0x5C)
        self.assertEqual(field["trainerbattle_mode"], 3)
        self.assertEqual(field["trainerbattle_mode_name"], "SINGLE_NO_INTRO")
        self.assertEqual(field["trainerbattle_local_id"], 1)
        self.assertEqual(field["trainerbattle_live_flags"], 0x0C)
        self.assertEqual(
            field["trainerbattle_required_flags"],
            {"IS_MASTER": 0x04, "TRAINER": 0x08},
        )
        self.assertEqual(field["trainerbattle_authored_flags"], ["TRAINER"])
        self.assertEqual(
            field["trainerbattle_engine_owned_flags"], ["IS_MASTER"]
        )
        self.assertEqual(
            field["trainerbattle_forbidden_flags"],
            ["DOUBLE", "LINK", "MULTI", "FRONTIER"],
        )
        self.assertTrue(field["trainerbattle_forbidden_flags_zero"])
        self.assertEqual(field["trainerbattle_launch_count"], 28)
        self.assertEqual(field["direct_bare_battlebegin_count"], 0)
        self.assertTrue(field["map_script_installed"])
        self.assertEqual(field["map_script_type"], 3)
        transition_contract = field["map_transition_recovery"]
        self.assertEqual(
            {
                key: transition_contract[key]
                for key in (
                    "script", "entrypoint", "direct_recover_call",
                    "active_challenge", "inactive_challenge",
                )
            },
            {
                "script": "script::mirage_transition_recover",
                "entrypoint": "MirageProduction_MapTransitionRecover",
                "direct_recover_call": False,
                "active_challenge": "SKIP_KEEP_JOURNAL_STATUS_OK",
                "inactive_challenge": "RECOVER_STALE_STATE",
            },
        )
        transition_physical = field["map_transition_recovery_physical"]
        transition_offset = int(transition_physical["script_address"]) - 0x08000000
        transition_raw = bytes.fromhex(transition_physical["script_hex"])
        self.assertEqual(
            self.rom[transition_offset:transition_offset + len(transition_raw)],
            transition_raw,
        )
        table_offset = int(transition_physical["table_address"]) - 0x08000000
        table_raw = bytes.fromhex(transition_physical["table_hex"])
        self.assertEqual(
            self.rom[table_offset:table_offset + len(table_raw)], table_raw
        )
        transition = next(
            row for row in field["scripts"]
            if row["label"] == "script::mirage_transition_recover"
        )
        self.assertEqual(
            transition["operations"],
            ["callnative:MirageProduction_MapTransitionRecover", "end"],
        )
        self.assertEqual(
            field["first_trainerbattle_script"],
            "script::mirage_battle_01_after",
        )
        self.assertEqual(
            field["first_trainerbattle_address"],
            field["labels"]["script::mirage_battle_01_after"],
        )
        choose = next(
            row for row in field["scripts"]
            if row["label"] == "script::mirage_choose"
        )
        self.assertIn("special:0x0029", choose["operations"])
        launch_scripts = [
            row for row in field["scripts"]
            if row["label"].endswith("_launch")
        ]
        self.assertEqual(len(launch_scripts), 28)
        self.assertTrue(all(
            not any(operation.startswith(("special:", "waitstate"))
                    for operation in row["operations"])
            for row in launch_scripts
        ))
        trainerbattle_rows = field["trainerbattle_rows"]
        self.assertEqual(len(trainerbattle_rows), 28)
        self.assertEqual(
            [row["trainer_id"] for row in trainerbattle_rows],
            [745] * 7 + [746] * 7 + [747] * 7 + [748] * 7,
        )
        for battle, row in enumerate(trainerbattle_rows, 1):
            self.assertEqual(row["battle"], battle)
            self.assertEqual(row["opcode"], 0x5C)
            self.assertEqual(row["mode"], 3)
            self.assertEqual(row["local_id"], 1)
            self.assertEqual(row["defeat_text"], "text::defeat")
            self.assertEqual(row["continuation"], "MirageProduction_AfterBattle")
            self.assertFalse(row["trainer_flag_precheck"])
            command = (
                bytes((0x5C, 3))
                + int(row["trainer_id"]).to_bytes(2, "little")
                + (1).to_bytes(2, "little")
                + int(row["defeat_text_address"]).to_bytes(4, "little")
            )
            self.assertEqual(row["command_hex"], command.hex())
            offset = int(row["address"]) - 0x08000000
            self.assertEqual(self.rom[offset:offset + len(command)], command)
            self.assertEqual(self.rom[offset + len(command)], 0x23)
        self.assertEqual(
            field["respawn"],
            {
                "id": 14,
                "opcode": 0x9F,
                "operation": "setrespawn:14",
                "operation_count": 1,
                "after_commit_selection": True,
                "before_first_battle": True,
                "selection_cancel_preserves_previous_respawn": True,
            },
        )
        matches = [
            row for row in field["scripts"]
            if "setrespawn:14" in row["operations"]
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["label"], "script::mirage_commit_success")
        self.assertEqual(
            matches[0]["operations"],
            ["setrespawn:14", "goto:script::mirage_battle_01"],
        )
        address = int(field["labels"]["script::mirage_commit_success"])
        offset = address - 0x08000000
        self.assertEqual(self.rom[offset:offset + 3], bytes.fromhex("9f0e00"))

    def test_upstream_and_private_waiting_owners_are_unchanged(self) -> None:
        regression = self.metadata["regression"]
        self.assertEqual(regression["trainer_encounters"], 1302)
        self.assertEqual(regression["trainer_members"], 6490)
        self.assertEqual(regression["trainer_double"], 74)
        self.assertEqual(regression["kanto_trainers"], 201)
        self.assertEqual(regression["acquisition_events"], 201)
        self.assertEqual(regression["qol_features"], 35)
        self.assertTrue(regression["factory_raid_event_owners_unchanged"])
        audit = _json(AUDIT)
        self.assertTrue(all(audit["upstream"].values()))
        self.assertTrue(all(audit["private_waiting_areas"].values()))

    def test_incremental_and_clean_direct_bps_are_exact(self) -> None:
        clean = (ROOT / rebuild.CLEAN).read_bytes()
        incremental = (ROOT / rebuild.INCREMENTAL).read_bytes()
        direct = (ROOT / rebuild.DIRECT).read_bytes()
        self.assertEqual(apply_bps(self.stage37, incremental), self.rom)
        self.assertEqual(apply_bps(clean, direct), self.rom)


class MirageProductionMgbaAndCleanRebuildTests(unittest.TestCase):
    def test_quick_full_are_independent_all_pass_and_identity_equal(self) -> None:
        documents = {"quick": _json(QUICK), "full": _json(FULL)}
        for mode, document in documents.items():
            self.assertEqual(document["status"], "PASS", msg=mode)
            self.assertEqual(document["mode"], mode)
            self.assertEqual(document["process_runs"], 1)
            self.assertEqual(document["warnings_errors"], 0)
            self.assertEqual(set(document["acceptance_checks"]), ACCEPTANCE_KEYS)
            self.assertTrue(all(document["acceptance_checks"].values()), msg=mode)
            self.assertTrue(document["checks"])
            self.assertTrue(all(document["checks"].values()), msg=mode)
            self.assertEqual(document["coverage"]["rounds"], 4)
            self.assertEqual(document["coverage"]["battles"], 28)
            self.assertEqual(document["coverage"]["exit_paths"], 8)
            self.assertEqual(document["rom_sha256"], _sha(STAGE38))
            self.assertEqual(document["runner_sha256"], _sha(RUNNER))
            self.assertEqual(document["symbols_sha256"], _sha(SYMBOLS))
            self.assertEqual(document["cases_sha256"], _sha(CASES))
        self.assertEqual(documents["full"]["coverage"]["badge_masks"], 256)
        self.assertGreaterEqual(documents["quick"]["coverage"]["badge_masks"], 4)
        for key in ("result_identity", "rom_sha256", "runner_sha256",
                    "symbols_sha256", "cases_sha256"):
            self.assertEqual(documents["quick"][key], documents["full"][key], msg=key)

    def test_coverage_has_fifteen_evidence_backed_acceptance_results(self) -> None:
        coverage = _json(COVERAGE)
        self.assertEqual(coverage["status"], "PASS")
        self.assertEqual(set(coverage["acceptance"]), ACCEPTANCE_KEYS)
        for key, result in coverage["acceptance"].items():
            self.assertEqual(result["status"], "PASS", msg=key)
            self.assertTrue(result["evidence"]["source"], msg=key)
            self.assertTrue(result["evidence"]["checks"], msg=key)
            self.assertTrue(all(result["evidence"]["checks"].values()), msg=key)
        self.assertEqual(coverage["mgba"]["quick"]["process_runs"], 1)
        self.assertEqual(coverage["mgba"]["full"]["process_runs"], 1)

    def test_clean_rebuild_chain_and_direct_identity_are_published(self) -> None:
        evidence = _json(CLEAN_EVIDENCE)
        self.assertEqual(evidence["status"], "PASS")
        self.assertTrue(evidence["bps"]["chain_direct_identity_equal"])
        self.assertTrue(evidence["bps"]["stage37_incremental"]["round_trip_exact"])
        self.assertTrue(evidence["bps"]["clean_direct"]["round_trip_exact"])
        self.assertEqual(evidence["declared_span"]["outside_declared_span_count"], 0)
        self.assertEqual(evidence["declared_span"]["declared_span_overlap_count"], 0)
        self.assertEqual(evidence["allocator_overlap_count"], 0)
        self.assertEqual(evidence["mgba"]["process_count"], 2)
        self.assertEqual(
            evidence["runtime_contract"],
            {
                "required_export_count": 16,
                "root_patch_count": 7,
                "ability_root_address": "0x090973FC",
                "ability_root_expected_hex": "6bf298fd",
                "ability_adapter":
                    "MirageProduction_LoadProperAbilityBattleDataAdapter",
                "trainerbattle_command": 0x5C,
                "trainerbattle_mode": 3,
                "trainerbattle_launch_count": 28,
                "direct_bare_battlebegin_count": 0,
                "runtime_state_address": "0x0203EE00",
                "runtime_state_end_exclusive": "0x0203F098",
                "runtime_state_size": 664,
                "ui_help_video_state_address": "0x0203F101",
            },
        )

    def test_rebuild_check_mode_never_calls_output_writer(self) -> None:
        evidence = {"input_output": {"stage38_sha256": "test"},
                    "mgba": {"result_identity": "test"}}
        report = b"report\n"
        expected = rebuild._stable(evidence)

        def fake_read(path: Path) -> bytes:
            if path == rebuild.EVIDENCE:
                return expected
            if path == rebuild.REPORT:
                return report
            raise AssertionError(path)

        with (
            mock.patch.object(rebuild, "_run") as run,
            mock.patch.object(rebuild, "_validate", return_value=(evidence, report)),
            mock.patch.object(rebuild, "_read", side_effect=fake_read),
            mock.patch.object(rebuild, "_atomic_write") as write,
        ):
            self.assertEqual(rebuild._execute("check"), evidence)
        run.assert_called_once()
        write.assert_not_called()

    def test_builder_check_mode_never_calls_output_writer(self) -> None:
        fake_outputs = {
            mirage.OUTPUT_META.as_posix(): json.dumps({
                "output": {"sha256": "test-only"},
            }).encode("utf-8")
        }
        with (
            mock.patch.object(mirage, "build_outputs", return_value=fake_outputs) as build,
            mock.patch.object(mirage, "_check_outputs") as check,
            mock.patch.object(mirage, "_mgba_outputs", return_value={}) as mgba,
            mock.patch.object(mirage, "_write_outputs") as write,
            mock.patch.object(sys, "argv", ["build_mirage_production.py", "check"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = mirage.main()
        self.assertEqual(result, 0)
        self.assertGreaterEqual(build.call_count, 1)
        self.assertGreaterEqual(check.call_count, 1)
        self.assertEqual(mgba.call_count, 1)
        write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
