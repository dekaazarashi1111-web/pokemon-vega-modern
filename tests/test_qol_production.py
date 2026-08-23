from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_qol_production  # noqa: E402


PROGRESSION = ROOT / "content/qol_progression.csv"
BINDINGS = ROOT / "config/qol_production_bindings.csv"
FEATURE_MATRIX = ROOT / "config/feature_matrix.csv"
QOL_B = ROOT / "config/qol_b.json"
SUPPLY = ROOT / "content/qol_supply.csv"
MAPS = ROOT / "content/maps.csv"
MAP_BINDINGS = ROOT / "content/map_bindings.csv"
RESEARCH = ROOT / "manifests/research_encounters.csv"
SPECIES = ROOT / "manifests/species_ids.csv"
SPECIAL = ROOT / "vendor/vega_acquisition/content/special_event_catalog_125.csv"
ITEM_IDS = ROOT / "manifests/item_ids.csv"
RUNTIME_C = ROOT / "overlays/qol_production/qol_production.c"
RUNTIME_H = ROOT / "overlays/qol_production/qol_production.h"
HOOKS_S = ROOT / "overlays/qol_production/qol_production_hooks.S"
HOOK_CONTRACT = ROOT / "overlays/qol_production/hook_contract_stage35.json"
RUNNER = ROOT / "tools/mgba_qol_production_smoke.c"
QOL_SLICE = ROOT / "tests/fixtures/qol_slice.json"
QOL_POLICY = ROOT / "docs/QOL_POLICY.md"
TEST_STRATEGY = ROOT / "docs/TEST_STRATEGY.md"
RELEASE_README = ROOT / "docs/RELEASE_README_JA.md"
DECISIONS = ROOT / "design/decisions.md"
OUTPUT_COVERAGE = ROOT / "reports/generated/qol_production_coverage.json"

STAGE35 = ROOT / "build/stages/35_trainer_changekit_final.gba"
STAGE35_META = ROOT / "build/stages/35_trainer_changekit_final.json"
STAGE35_ALLOC = ROOT / "build/stages/35_allocation.json"
STAGE36 = ROOT / "build/stages/36_qol_production.gba"
STAGE36_META = ROOT / "build/stages/36_qol_production.json"
MGBA_CASES = ROOT / "generated/runtime/qol_production_mgba_cases.csv"
MGBA_QUICK = ROOT / "build/stages/36_mgba_qol_production_quick.json"
MGBA_FULL = ROOT / "build/stages/36_mgba_qol_production_full.json"

STAGE35_SHA256 = "60b00504b7c90ee026c15ee285be69edc43c12c0eedcc64096fcadd1f290aa7b"
STAGE35_META_SHA256 = "51240a82f53eaa59eae3dd5dda1c802afac870a8ec2e36a2611876d09fc96c14"
STAGE35_ALLOC_SHA256 = "34412386b4e93b15b8c2214147f7aa444cb3e0f973ccae086b8998ceded75767"
RESEARCH_SHA256 = "da96838351dfa2f003f70378d40699d3d1208932781535d8cca6729463999b15"

LIVE_CLASSIFICATIONS = {"LIVE_ENGINE_UI", "LIVE_SERVICE", "LIVE_SUPPLY"}
QOL_B_FEATURES = {
    "AUTO_BATTLE",
    "EGG_BASKET",
    "FIELD_PC",
    "PC_BULK_MOVE_RELEASE",
    "PC_HELD_ITEM_BULK",
    "PC_MULTISELECT",
    "PC_RELEARN",
    "PC_SEARCH",
}
QUANTITY_CONSUMERS = {
    "EXP_CANDY": {988, 989, 990, 991, 992},
    "VITAMIN": {63, 64, 65, 66, 67, 70},
    "FEATHER": {386, 387, 388, 389, 390, 391},
    "RARE_CANDY": {68},
    "EV_RESET_ITEM": {993, 994, 995, 996, 997, 998},
}
QUANTITY_ITEM_KEYS = {
    "EXP_CANDY": {
        "ITEM_KEY_EXP_CANDY_XS", "ITEM_KEY_EXP_CANDY_S",
        "ITEM_KEY_EXP_CANDY_M", "ITEM_KEY_EXP_CANDY_L",
        "ITEM_KEY_EXP_CANDY_XL",
    },
    "VITAMIN": {
        "ITEM_KEY_HP_UP", "ITEM_KEY_PROTEIN", "ITEM_KEY_IRON",
        "ITEM_KEY_CARBOS", "ITEM_KEY_CALCIUM", "ITEM_KEY_ZINC",
    },
    "FEATHER": {
        "ITEM_KEY_HEALTH_WING", "ITEM_KEY_MUSCLE_WING",
        "ITEM_KEY_RESIST_WING", "ITEM_KEY_GENIUS_WING",
        "ITEM_KEY_CLEVER_WING", "ITEM_KEY_SWIFT_WING",
    },
    "RARE_CANDY": {"ITEM_KEY_RARE_CANDY"},
    "EV_RESET_ITEM": {
        "ITEM_KEY_EV_RESET_HP", "ITEM_KEY_EV_RESET_ATK",
        "ITEM_KEY_EV_RESET_DEF", "ITEM_KEY_EV_RESET_SPEED",
        "ITEM_KEY_EV_RESET_SPATK", "ITEM_KEY_EV_RESET_SPDEF",
    },
}
ACCEPTANCE_KEYS = {
    "35_UNIQUE_LIVE_OWNERS",
    "REAL_BOX_PSS_SAVE",
    "NORMAL_USER_ENTRY",
    "UNLOCK_SAVE_RELOAD",
    "ATOMIC_CANCEL_CAPACITY_FORBIDDEN",
    "PC_MULTI_BOX_EGG_SPECIAL_ADDED_SPECIES",
    "BASKET_255_256_QUEUE_SAVE",
    "AUTO_RANDOM_ONLY",
    "TEXT_CONTROL_AND_MOVEMENT_EVENTS",
    "TRAINING_STATS_DISPLAY_SAVE",
    "SUPPLY_UNLOCK_ONCE_REPEAT",
    "STAGE35_TRAINER_REGRESSION",
    "DETERMINISTIC_BPS_DECLARED_ONLY",
    "MGBA_TWO_PROCESS",
    "DOC_LEDGER_BUILD_ALIGNMENT",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row[key]
        if not value or value in result:
            raise AssertionError(f"{key} is missing or duplicated: {value!r}")
        result[value] = row
    return result


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON root must be an object: {path}")
    return value


def _function_body(source: str, declaration: str) -> str:
    """Return one C function, including its balanced outer braces."""
    start = source.index(declaration)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f"unterminated function: {declaration}")


def _asm_function(source: str, symbol: str) -> str:
    start = source.index(f"{symbol}:")
    end = source.index(f".size {symbol}", start)
    return source[start:end]


class QolProductionLedgerTests(unittest.TestCase):
    def test_release_35_have_unique_live_production_owners(self) -> None:
        progression_rows = _rows(PROGRESSION)
        binding_rows = _rows(BINDINGS)
        progression = _index(progression_rows, "feature_key")
        bindings = _index(binding_rows, "feature_key")

        self.assertEqual(len(progression_rows), 35)
        self.assertEqual(len(binding_rows), 35)
        self.assertEqual(set(bindings), set(progression))
        self.assertTrue(all(row["release_enabled"].lower() == "true"
                            for row in progression_rows))
        owners = [row["production_owner"] for row in binding_rows]
        self.assertEqual(len(set(owners)), 35)
        self.assertTrue(all(owners))
        self.assertTrue(all(row["classification"] in LIVE_CLASSIFICATIONS
                            for row in binding_rows))
        for row in binding_rows:
            for field in ("capability_keys", "entry_symbol", "ui_owner",
                          "unlock_source", "save_owner", "serializer_owner",
                          "supply_owner", "mgba_case"):
                self.assertTrue(row[field], msg=f"{row['feature_key']}:{field}")

    def test_capability_and_unlock_crosswalk_is_complete(self) -> None:
        progression = _index(_rows(PROGRESSION), "feature_key")
        bindings = _index(_rows(BINDINGS), "feature_key")
        matrix = _index(_rows(FEATURE_MATRIX), "feature_key")
        qol_b = _json(QOL_B)
        qol_b_rows = qol_b.get("features")
        self.assertIsInstance(qol_b_rows, list)
        qol_b_index = _index(qol_b_rows, "key")  # type: ignore[arg-type]
        self.assertEqual(set(qol_b_index), QOL_B_FEATURES)
        self.assertTrue(all(row["release_default"] == "ENABLED"
                            for row in qol_b_index.values()))

        known_capabilities = set(matrix) | set(qol_b_index)
        for feature, row in bindings.items():
            capabilities = set(row["capability_keys"].split("|"))
            self.assertNotIn("", capabilities, msg=feature)
            self.assertEqual(capabilities - known_capabilities, set(), msg=feature)

            # The binding records the physical boundary, rather than an
            # independently invented unlock label.  Only the two historical
            # aliases below are permitted.
            source_boundary = progression[feature]["source_boundary"]
            physical_boundary = {
                "GAME_START": "VEGA_PRE_ENTRY",
                "DAYCARE_FIRST_USE": "VEGA_DAYCARE_FIRST",
            }.get(source_boundary, source_boundary)
            self.assertEqual(row["unlock_source"], physical_boundary, msg=feature)

        canonical_feature = {
            "PC_SEARCH": "PC_SEARCH_MULTISELECT",
            "PC_MULTISELECT": "PC_SEARCH_MULTISELECT",
            "PC_BULK_MOVE_RELEASE": "PC_SEARCH_MULTISELECT",
            "FIELD_PC": "FIELD_PC",
            "PC_RELEARN": "PC_MOVE_EDIT",
            "PC_HELD_ITEM_BULK": "PC_HELD_ITEM_BULK",
            "EGG_BASKET": "EGG_BASKET",
            "AUTO_BATTLE": "AUTO_BATTLE",
        }
        for capability, qol_b_row in qol_b_index.items():
            owner = bindings[canonical_feature[capability]]
            self.assertIn(capability, owner["capability_keys"].split("|"))
            expected_unlock = {
                "UNLOCK_GAME_START": "VEGA_PRE_ENTRY",
            }.get(qol_b_row["unlock_key"], qol_b_row["unlock_key"])
            self.assertEqual(owner["unlock_source"], expected_unlock,
                             msg=capability)

        runtime = RUNTIME_C.read_text(encoding="utf-8")
        header = RUNTIME_H.read_text(encoding="utf-8")
        enum_block = header.split("typedef enum VegaQolFeature", 1)[1].split(
            "} VegaQolFeature;", 1
        )[0]
        enum_features = re.findall(r"\bVEGA_QOL_([A-Z][A-Z0-9_]+)\s*(?:=\s*\d+)?\s*,?", enum_block)
        self.assertEqual(enum_features, list(progression))
        for feature in progression:
            self.assertIn(f"case VEGA_QOL_{feature}:", runtime, msg=feature)

    def test_supply_unlocks_do_not_leak_before_authored_boundaries(self) -> None:
        supply = _index(_rows(SUPPLY), "supply_key")
        expected = {
            "SUPPLY_KEY_EVERSTONE": "VEGA_BADGE_1",
            "SUPPLY_KEY_EXP_CANDY_XS": "VEGA_DH_CLEAR",
            "SUPPLY_KEY_EXP_CANDY_S": "VEGA_DH_CLEAR",
            "SUPPLY_KEY_EXP_CANDY_M_ONCE": "VEGA_DH_CLEAR",
        }
        self.assertEqual(
            {key: supply[key]["unlock_key"] for key in expected}, expected
        )


class QolProductionRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = RUNTIME_C.read_text(encoding="utf-8")
        cls.header = RUNTIME_H.read_text(encoding="utf-8")
        cls.hooks = HOOKS_S.read_text(encoding="utf-8")

    def test_qol_b_uses_real_14_by_30_80_byte_storage_abi(self) -> None:
        self.assertIn("#define VEGA_QOL_BOX_COUNT 14u", self.header)
        self.assertIn("#define VEGA_QOL_BOX_CAPACITY 30u", self.header)
        self.assertIn("#define VEGA_QOL_BOX_MON_SIZE 80u", self.header)
        self.assertNotIn("QolBMon", self.runtime + self.header)
        for contract in (
            "#define FN_GET_BOX_MON_DATA_AT PTR(GetBoxMonDataAtFn, 0x0808B4B5u)",
            "#define FN_GET_BOXED_MON PTR(GetBoxedMonPtrFn, 0x0808B7CDu)",
            "#define FN_SET_BOX_MON_AT PTR(SetBoxMonAtFn, 0x0808B651u)",
            "#define FN_ZERO_BOX_MON_AT PTR(ZeroBoxMonAtFn, 0x0808B751u)",
            "#define FN_ORIGINAL_PSS_INPUT PTR(PssInputFn, 0x080942E9u)",
        ):
            self.assertIn(contract, self.runtime)
        for use in (
            "FN_GET_BOXED_MON(box, slot)",
            "FN_SET_BOX_MON_AT(destination_box",
            "FN_ZERO_BOX_MON_AT(box, slot)",
            "gVegaModernSaveData->egg_queue",
        ):
            self.assertIn(use, self.runtime)

    def test_oval_charm_call_uses_thumb_veneer(self) -> None:
        oval = _asm_function(self.hooks, "VegaQolProduction_OvalCharmHook")
        self.assertIn("bl VegaQolProduction_ModifyBreedingScore", oval)
        self.assertIn("bl .Lqol_call_r3", oval)
        self.assertIn(".Lqol_call_r3:\n    bx r3", oval)
        self.assertNotRegex(oval, r"\bmov\s+lr\s*,\s*pc\b")
        self.assertNotRegex(oval, r"\bmovs?\s+lr\s*,")
        prefix = self.hooks[:self.hooks.index("VegaQolProduction_OvalCharmHook:")]
        self.assertTrue(prefix.rstrip().endswith(".thumb_func"))

    def test_wild_battle_end_clears_only_qol_state(self) -> None:
        contract = _json(HOOK_CONTRACT)
        rows = {row["name"]: row for row in contract["hooks"]}  # type: ignore[index]
        wild_end = rows["wild_standard_end"]
        self.assertEqual(wild_end["address"], "0x0807F270")
        self.assertEqual(wild_end["expected"], "00b581b069460020")
        self.assertEqual(wild_end["target"], "VegaQolProduction_EndWildBattleHook")

        end_hook = _asm_function(self.hooks, "VegaQolProduction_EndWildBattleHook")
        self.assertLess(end_hook.index("bl VegaQolProduction_ClearBattleAutoState"),
                        end_hook.index("ldr r3, =0x0807f279"))
        clear = _function_body(
            self.runtime, "void VegaQolProduction_ClearBattleAutoState(void)"
        )
        for field in ("wild_token_armed", "battle_auto_eligible", "auto_active",
                      "wild_token_pid", "battle_token_pid"):
            self.assertRegex(clear, rf"G_QOL_STATE->{field}\s*=\s*0u;")

        production_sources = self.runtime + self.header + self.hooks
        self.assertNotRegex(production_sources, r"(?i)battle_?outcome")
        self.assertNotIn("0x02023DEA", production_sources.upper())

    def test_bulk_transactions_preflight_and_cancel_before_mutation(self) -> None:
        move = _function_body(self.runtime, "static VegaQolStatus move_selection")
        self.assertIn("u16 needed = 0u;", move)
        self.assertLess(move.index("if (cancelled)"),
                        move.index("FN_SET_BOX_MON_AT(destination_box"))
        self.assertLess(move.index("if (free_count < needed)"),
                        move.index("FN_SET_BOX_MON_AT(destination_box"))
        self.assertLess(move.index("FN_SET_BOX_MON_AT(destination_box"),
                        move.index("FN_ZERO_BOX_MON_AT(box, slot)"))

        items = _function_body(self.runtime, "static VegaQolStatus items_then_mutate")
        add = items.index("FN_ADD_BAG_ITEM")
        mutate = items.index("FN_ZERO_BOX_MON_AT")
        self.assertLess(items.index("if (cancelled)"), add)
        self.assertLess(items.index("mon_release_forbidden(mon)"), add)
        self.assertLess(items.index("item_forbidden(item)"), add)
        self.assertLess(items.index("FN_CHECK_BAG_SPACE"), add)
        self.assertLess(add, mutate)
        self.assertIn("rollback_bag:", items)
        self.assertIn("FN_REMOVE_BAG_ITEM(item, 1u)", items)

        relearn = _function_body(self.runtime, "static VegaQolStatus relearn_move")
        self.assertLess(relearn.index("if (cancelled)"),
                        relearn.index("FN_SET_MON_MOVE_SLOT"))
        claim = _function_body(self.runtime, "static VegaQolStatus claim_egg_queue")
        self.assertLess(claim.index("if (cancelled)"),
                        claim.index("FN_SET_BOX_MON_AT"))
        self.assertLess(claim.index("VEGA_QOL_CAPACITY"),
                        claim.index("FN_SET_BOX_MON_AT"))

    def test_pss_list_initial_index_is_split_into_scroll_and_row(self) -> None:
        menu = _function_body(
            self.runtime, "static VegaQolStatus open_pss_list_menu"
        )
        self.assertIn("menu.max_showed = total_items < 4u ? total_items : 4u;",
                      menu)
        self.assertIn("menu.window_id = 2u;", menu)
        self.assertIn("FN_FILL_WINDOW(2u, 0x11u);", menu)
        self.assertIn("initial_cursor >= total_items", menu)
        self.assertIn(
            "scroll_offset = (u16)(initial_cursor - menu.max_showed + 1u);",
            menu,
        )
        self.assertIn("selected_row = (u16)(initial_cursor - scroll_offset);", menu)
        self.assertIn(
            "FN_LIST_MENU_INIT(&menu, scroll_offset, selected_row)", menu
        )
        self.assertNotIn("FN_LIST_MENU_INIT(&menu, initial_cursor, 0u)", menu)

        naming = _function_body(self.runtime, "static void begin_search_name_input")
        self.assertIn("QOL_SEARCH_NAMING_PENDING", naming)
        self.assertIn("FN_SET_PSS_TASK(PTR(TaskFunc, 0x0808E4CDu));", naming)
        naming_adapter = _function_body(
            self.runtime, "void VegaQolProduction_DoNamingScreenAdapter"
        )
        self.assertIn("QOL_SEARCH_NAMING_PENDING", naming_adapter)
        self.assertIn("VegaQolProduction_OriginalDoNamingScreen(", naming_adapter)
        self.assertIn("return_from_search_naming", naming_adapter)

    def test_instant_text_unaligned_trampoline_preserves_stock_controls(self) -> None:
        contract = _json(HOOK_CONTRACT)
        rows = {row["name"]: row for row in contract["hooks"]}  # type: ignore[index]
        hook = rows["text_instant_printer_run"]
        self.assertEqual(hook["address"], "0x08002DD2")
        self.assertEqual(hook["mode"], "symbol_jump_unaligned")
        self.assertEqual(hook["target"], "VegaQolProduction_RunTextPrintersHook")
        self.assertEqual(len(bytes.fromhex(hook["expected"])), 10)

        trampoline = _asm_function(
            self.hooks, "VegaQolProduction_RunTextPrintersHook"
        )
        self.assertIn("ldr r3, =0x08002e35", trampoline)
        self.assertNotIn("ldr r3, =0x08002ddd", trampoline)

        accelerator = _function_body(
            self.runtime,
            "u8 VegaQolProduction_RunTextPrintersForInstantText(void)",
        )
        self.assertIn("if (!instant || printer->state != 0u)", accelerator)
        self.assertIn("result == 0u || result == 3u", accelerator)
        self.assertIn("printer->active = 0u;", accelerator)
        self.assertIn("FN_COPY_WINDOW_TO_VRAM(", accelerator)
        self.assertLess(accelerator.index("if (!instant"),
                        accelerator.index("for (j = 0u; j < 0x400u; ++j)"))

    def test_common_quantity_consumers_are_exact_real_item_abi(self) -> None:
        fixture = _json(QOL_SLICE)
        quantity = fixture["quantity_ui"]
        self.assertEqual(set(quantity["consumers"]), set(QUANTITY_CONSUMERS))
        self.assertEqual(quantity["choices"], [1, 5, 10, "ALL"])
        self.assertEqual(quantity["status"], "PASS")

        contract = _json(HOOK_CONTRACT)
        hooks = contract["hooks"]
        pointer_hooks = [row for row in hooks
                         if row["name"].startswith("quantity_item_")]
        expected_ids = set().union(*QUANTITY_CONSUMERS.values())
        actual_ids = {int(row["name"].removeprefix("quantity_item_"))
                      for row in pointer_hooks}
        self.assertEqual(len(pointer_hooks), 24)
        self.assertEqual(actual_ids, expected_ids)
        item_rows = {int(row["id"]): row for row in _rows(ITEM_IDS)}
        for consumer, ids in QUANTITY_CONSUMERS.items():
            self.assertEqual({item_rows[item_id]["item_key"] for item_id in ids},
                             QUANTITY_ITEM_KEYS[consumer], msg=consumer)
        self.assertTrue(all(row["mode"] == "symbol_pointer"
                            for row in pointer_hooks))
        self.assertTrue(all(
            row["target"] == "VegaQolProduction_FieldUseCommonQuantityAdapter"
            for row in pointer_hooks
        ))
        self.assertNotIn(589, actual_ids)  # only one reserved slot, not 18 shards
        self.assertNotIn(950, actual_ids)  # one-at-a-time evolution item

        evolution = [row for row in hooks
                     if row["name"] == "quantity_party_evolution"]
        self.assertEqual(len(evolution), 1)
        self.assertEqual(evolution[0]["address"], "0x08127048")
        self.assertEqual(evolution[0]["mode"], "symbol_jump")
        self.assertEqual(evolution[0]["target"],
                         "VegaQolProduction_PartyMenuTryEvolutionAdapter")

        exp_candy = _function_body(self.runtime, "static u8 is_exp_candy")
        reset = _function_body(self.runtime, "static u8 is_ev_reset_item")
        gain = _function_body(self.runtime, "static u8 is_ev_gain_item")
        quantity_task = _function_body(
            self.runtime, "static void common_quantity_task"
        )
        quantity_menu = _function_body(
            self.runtime, "static u8 open_common_quantity_menu"
        )
        quantity_close = _function_body(
            self.runtime, "static void close_common_quantity_menu"
        )
        self.assertIn("item >= 988u && item <= 992u", exp_candy)
        self.assertIn("item >= 993u && item <= 998u", reset)
        for token in ("item >= 63u && item <= 67u", "item == 70u",
                      "item >= 386u && item <= 391u"):
            self.assertIn(token, gain)
        self.assertIn("item == 68u", quantity_task)
        self.assertIn("gVegaQolQuantityItems", quantity_menu)
        self.assertIn("FN_LIST_MENU_INIT", quantity_menu)
        self.assertIn("FN_LIST_MENU_INPUT", quantity_task)
        self.assertIn("FN_LIST_MENU_DESTROY", quantity_close)
        self.assertNotIn("KEY_LEFT", quantity_task)
        self.assertNotIn("KEY_RIGHT", quantity_task)

        matrix = _index(_rows(FEATURE_MATRIX), "feature_key")
        quantity_notes = matrix["QUANTITY_UI"]["notes"]
        for term in ("アメ", "栄養", "ハネ", "ふしぎなアメ", "EV reset",
                     "Tera shard", "coin"):
            self.assertIn(term, quantity_notes)

        policy = QOL_POLICY.read_text(encoding="utf-8")
        strategy = TEST_STRATEGY.read_text(encoding="utf-8")
        readme = RELEASE_README.read_text(encoding="utf-8")
        decisions = DECISIONS.read_text(encoding="utf-8")
        for text in (policy, strategy, readme, decisions):
            for term in ("経験アメ", "栄養", "ハネ", "ふしぎなアメ", "EV reset"):
                if term == "経験アメ" and text == readme:
                    self.assertIn("アメ", text)
                else:
                    self.assertIn(term, text)
            self.assertIn("Tera shard", text)
            self.assertIn("コレクレーのコイン", text)
            self.assertIn("arcade coin", text)
        for text in (policy, strategy, decisions):
            self.assertIn("0..998", text)
        self.assertIn("D-024", decisions)

    def test_raid_and_late_gimmicks_use_real_battle_consumers(self) -> None:
        bindings = _index(_rows(BINDINGS), "feature_key")
        self.assertEqual(
            bindings["HIGH_DIFFICULTY_RAID"]["entry_symbol"],
            "VegaQolProduction_ConfigureHighRaid",
        )
        low_raid = _function_body(
            self.runtime, "u8 VegaQolProduction_ConfigureLowRaid",
        )
        self.assertIn("FN_CONFIGURE_HIGH_RAID(0u, 0u, 0u, 10u, 1u)", low_raid)
        self.assertIn("VEGA_QOL_LOW_RAID_COUNT", low_raid)
        self.assertEqual(
            bindings["TERA_DYNAMAX_STORY"]["entry_symbol"],
            "VegaQolProduction_ConfigureTrainerBattleAdapter",
        )
        contract = _json(HOOK_CONTRACT)
        hooks = {row["name"]: row for row in contract["hooks"]}
        trainer = hooks["trainer_battle_configure"]
        self.assertEqual(trainer["address"], "0x0807F948")
        self.assertEqual(trainer["mode"], "symbol_jump")
        self.assertEqual(
            trainer["target"],
            "VegaQolProduction_ConfigureTrainerBattleAdapter",
        )
        configure = _function_body(
            self.runtime,
            "const u8 *VegaQolProduction_ConfigureTrainerBattleAdapter",
        )
        self.assertIn("FN_STAGE35_CONFIGURE_TRAINER(data)", configure)
        self.assertIn("late_gimmick_trainer(G_TRAINER_OPPONENT_A)", configure)
        self.assertIn("FN_STAGE35_TRAINER_BATTLE_END(3u)", configure)
        raid = _function_body(
            self.runtime, "u8 VegaQolProduction_ConfigureHighRaid(void)"
        )
        self.assertIn("FN_CONFIGURE_HIGH_RAID(0u, 6u, 5u, 10u, 1u)", raid)
        self.assertIn("VEGA_QOL_HIGH_DIFFICULTY_RAID", raid)

    def test_mgba_uses_physical_auto_fallback_and_step_hatch_evidence(self) -> None:
        runner = RUNNER.read_text(encoding="utf-8")
        forbidden = _function_body(
            runner, "static bool qol_auto_live_forbidden_matrix"
        )
        for label in ("trainer", "static", "story", "legendary",
                      "shiny", "factory", "raid"):
            self.assertIn(f'"{label}"', forbidden)
        case = _function_body(
            runner, "static bool qol_auto_live_forbidden_case"
        )
        self.assertIn("setup_trainer(core, field)", case)
        self.assertIn("qol_setup_random_auto_battle(", case)
        self.assertIn("core->setKeys(core, QOL_KEY_SELECT);", case)
        self.assertIn("QOL_STATE_BATTLE_AUTO_ELIGIBLE", case)

        movement = _function_body(
            runner, "static bool qol_movement_user_path"
        )
        self.assertIn("run_key_frames(core, directions[index], 40U)", movement)
        self.assertIn("read16(core, QOL_BASKET_COUNTER) == tiles", movement)
        self.assertIn("moved_with_one_hatch_check_per_tile", movement)

        species = _index(_rows(SPECIES), "species_key")
        self.assertEqual(species["SPECIES_KEY_DITTO"]["id"], "183")
        self.assertIn("QOL_SPECIES_DITTO = 183U", runner)


class QolProductionInputAndHookTests(unittest.TestCase):
    def test_hook_expected_bytes_match_pinned_stage35(self) -> None:
        self.assertTrue(STAGE35.is_file(), "Stage35 ROM evidence is missing")
        raw = STAGE35.read_bytes()
        self.assertEqual(len(raw), 32 * 1024 * 1024)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), STAGE35_SHA256)
        contract = _json(HOOK_CONTRACT)
        self.assertEqual(contract["input_sha256"], STAGE35_SHA256)
        hooks = contract["hooks"]
        self.assertIsInstance(hooks, list)
        self.assertGreaterEqual(len(hooks), 30)
        occupied: set[int] = set()
        names: set[str] = set()
        for row in hooks:  # type: ignore[assignment]
            name = row["name"]
            address = int(row["address"], 0)
            expected = bytes.fromhex(row["expected"])
            self.assertNotIn(name, names)
            names.add(name)
            offset = address - 0x08000000
            self.assertEqual(raw[offset:offset + len(expected)], expected, msg=name)
            span = set(range(offset, offset + len(expected)))
            self.assertEqual(occupied & span, set(), msg=name)
            occupied |= span
            mode = row["mode"]
            if mode in {"symbol_jump", "cfru_symbol_jump", "absolute_jump"}:
                self.assertEqual(len(expected), 8, msg=name)
            elif mode == "symbol_jump_nop":
                self.assertGreaterEqual(len(expected), 8, msg=name)
                self.assertEqual(len(expected) % 2, 0, msg=name)
            elif mode == "symbol_jump_unaligned":
                self.assertEqual(address & 3, 2, msg=name)
                self.assertEqual(len(expected), 10, msg=name)
            elif mode == "symbol_bl":
                self.assertEqual(len(expected), 4, msg=name)
            elif mode == "symbol_pointer":
                self.assertEqual(len(expected), 4, msg=name)
            elif mode == "symbol_script_goto":
                self.assertEqual(len(expected), 5, msg=name)
            elif mode == "raw":
                self.assertEqual(len(expected), len(bytes.fromhex(row["replacement"])),
                                 msg=name)
            else:
                self.fail(f"unknown hook mode: {name}:{mode}")
        self.assertTrue({"wild_standard_end", "daycare_oval_charm",
                         "pss_input_callsite", "candy_quantity"} <= names)
        cfru_hooks = [row for row in hooks if row["mode"] == "cfru_symbol_jump"]
        self.assertEqual(len(cfru_hooks), 9)
        self.assertFalse(any(row["mode"] == "absolute_jump" for row in hooks))
        metadata = _json(ROOT / build_qol_production.BATTLE_CORE_META)
        symbols = metadata["downstream_symbols"]
        self.assertEqual({row["target"] for row in cfru_hooks}, set(symbols))

    def test_authored_research_special_and_field_map_counts(self) -> None:
        self.assertEqual(_sha(RESEARCH), RESEARCH_SHA256)
        research = [row for row in _rows(RESEARCH)
                    if row["status"] == "ACTIVE"
                    and row["shared_capture_key"] == "NONE"]
        self.assertEqual(len(research), 846)
        self.assertEqual(len({row["research_key"] for row in research}), 846)
        self.assertEqual({row["shiny_policy"] for row in research},
                         {"MINOR_BONUS_NO_CHAIN_LEAK"})

        builder = Path(build_qol_production.__file__).read_text(encoding="utf-8")
        runtime = RUNTIME_C.read_text(encoding="utf-8")
        self.assertIn('"shiny_rolls": 2', builder)
        self.assertIn("rule->shiny_rolls > 1u", runtime)
        self.assertIn("shiny_pid_matches(ot_id, candidate)", runtime)

        species = _index(_rows(SPECIES), "species_key")
        map_bindings = _index(_rows(MAP_BINDINGS), "map_key")
        for row in research:
            self.assertIn(row["species_key"], species, msg=row["research_key"])
            self.assertEqual(map_bindings[row["map_key"]]["status"], "ACTIVE",
                             msg=row["research_key"])

        special = _rows(SPECIAL)
        self.assertEqual(len(special), 125)
        self.assertEqual(len({int(row["canonical_id"]) for row in special}), 125)
        self.assertEqual(len({row["species_key"] for row in special}), 125)

        maps = _index(_rows(MAPS), "map_key")
        field = []
        for key, row in maps.items():
            if row["field_pc_allowed"].lower() != "true":
                continue
            binding = map_bindings[key]
            self.assertEqual(binding["status"], "ACTIVE", msg=key)
            field.append((int(binding["group_id"]), int(binding["map_id"])))
        self.assertEqual(len(field), 69)
        self.assertEqual(len(set(field)), 69)

    def test_stage35_trainer_invariants_are_physically_pinned(self) -> None:
        for path in (STAGE35, STAGE35_META, STAGE35_ALLOC):
            self.assertTrue(path.is_file(), f"baseline evidence is missing: {path}")
        self.assertEqual(_sha(STAGE35), STAGE35_SHA256)
        self.assertEqual(_sha(STAGE35_META), STAGE35_META_SHA256)
        self.assertEqual(_sha(STAGE35_ALLOC), STAGE35_ALLOC_SHA256)
        self.assertEqual(build_qol_production.EXPECTED_STAGE35_SHA256,
                         STAGE35_SHA256)
        self.assertEqual(build_qol_production.EXPECTED_STAGE35_META_SHA256,
                         STAGE35_META_SHA256)
        self.assertEqual(build_qol_production.EXPECTED_STAGE35_ALLOC_SHA256,
                         STAGE35_ALLOC_SHA256)

        metadata = _json(STAGE35_META)
        coverage = metadata["coverage"]
        self.assertEqual(coverage["encounter_count"], 1302)
        self.assertEqual(coverage["member_count"], 6490)
        self.assertEqual(coverage["battle_format_counts"],
                         {"DOUBLE": 74, "SINGLE": 1228})
        self.assertEqual(coverage["gimmick_type_counts"], {
            "DYNAMAX": 4, "MEGA": 86, "NONE": 1034,
            "TERASTAL": 67, "Z_MOVE": 111,
        })
        self.assertEqual(metadata["physical_bindings"]["count"], 1302)
        self.assertEqual(metadata["physical_bindings"]["unique_command_count"], 1302)
        self.assertEqual(metadata["physical_events"]["summary"]["task06_encounters"],
                         201)
        self.assertTrue(all(metadata["invariants"].values()))

        allocation = _json(STAGE35_ALLOC)
        self.assertEqual(allocation["summaries"]["overlap_count"], 0)
        payload = [row for row in allocation["allocations"]
                   if row["name"] == "trainer_changekit_final_stage35_payload"]
        self.assertEqual(len(payload), 1)
        self.assertEqual(
            int(payload[0]["start"]), int(metadata["runtime"]["payload"]["offset"]),
        )
        self.assertEqual(
            int(payload[0]["gba_start"]),
            int(metadata["runtime"]["payload"]["address"]),
        )

    def test_stage36_preserves_stage35_trainer_table_and_commands(self) -> None:
        self.assertTrue(STAGE36.is_file(), "Stage36 ROM evidence is missing")
        self.assertTrue(STAGE36_META.is_file(), "Stage36 metadata is missing")
        before = STAGE35.read_bytes()
        after = STAGE36.read_bytes()
        metadata35 = _json(STAGE35_META)
        metadata36 = _json(STAGE36_META)
        self.assertEqual(metadata36["input"]["sha256"], STAGE35_SHA256)

        table = metadata35["trainer_table"]
        start = int(table["new_address"]) - 0x08000000
        end = start + int(table["new_count"]) * int(table["record_size"])
        self.assertEqual(after[start:end], before[start:end])
        for row in metadata35["physical_bindings"]["rows"]:
            offset = int(row["command_address"]) - 0x08000000
            self.assertEqual(after[offset:offset + 8], before[offset:offset + 8],
                             msg=row["encounter_key"])


class QolProductionEvidenceTests(unittest.TestCase):
    def test_mgba_quick_and_full_are_current_independent_all_pass_evidence(self) -> None:
        for path in (STAGE36, MGBA_CASES, RUNNER, MGBA_QUICK, MGBA_FULL):
            self.assertTrue(path.is_file(), f"mGBA evidence input is missing: {path}")
        progression = _index(_rows(PROGRESSION), "feature_key")
        bindings = _index(_rows(BINDINGS), "feature_key")
        cases = _rows(MGBA_CASES)
        self.assertEqual(len(cases), 35)
        self.assertEqual([row["case_id"] for row in cases], list(progression))
        self.assertTrue(all(row["mode"] == "quick" for row in cases))
        for row in cases:
            self.assertEqual(row["path"],
                             bindings[row["case_id"]]["mgba_case"])
            self.assertTrue(row["path"], msg=row["case_id"])
        current = {
            "rom_sha256": _sha(STAGE36),
            "runner_sha256": _sha(RUNNER),
            "cases_sha256": _sha(MGBA_CASES),
        }
        expected_checks = {
            "field_boot", "case_fixture", "physical_hooks", "probe",
            "start_select_a_user_path", "text_control",
            "instant_text_battle_prompt", "movement_step_hatch_exact",
            "physical_pss_select_path", "real_box_cross_move",
            "auto_forbidden_matrix", "auto_physical_forbidden_contexts",
            "basket_255_256",
        }
        documents = {}
        for mode, path in (("quick", MGBA_QUICK), ("full", MGBA_FULL)):
            document = _json(path)
            documents[mode] = document
            self.assertEqual(document["status"], "PASS", msg=mode)
            self.assertEqual(document["mode"], mode)
            self.assertEqual(document["fixture"],
                             "qol_production_exact_rom_user_paths")
            self.assertEqual(document["process_runs"], 1)
            self.assertEqual(document["warnings_errors"], 0)
            self.assertEqual({key: document[key] for key in current}, current)
            checks = document["checks"]
            self.assertTrue(expected_checks <= set(checks), msg=mode)
            self.assertGreater(len(checks), len(expected_checks), msg=mode)
            self.assertTrue(all(value is True for value in checks.values()), msg=mode)
            feature_checks = document["feature_checks"]
            self.assertEqual(set(feature_checks), set(progression), msg=mode)
            self.assertTrue(all(value is True
                                for value in feature_checks.values()), msg=mode)
            self.assertEqual(document["coverage"]["features"], 35)
            self.assertEqual(document["coverage"]["boxes"], 14)
            self.assertEqual(document["coverage"]["case_rows"], 35)
            self.assertGreaterEqual(document["coverage"]["physical_input_paths"], 2)
        self.assertEqual(documents["quick"]["rom_sha256"],
                         documents["full"]["rom_sha256"])

    def test_coverage_has_15_evidence_backed_acceptance_results(self) -> None:
        self.assertTrue(OUTPUT_COVERAGE.is_file(),
                        "QOL production coverage evidence is missing")
        coverage = _json(OUTPUT_COVERAGE)
        self.assertEqual(coverage["status"], "PASS")
        self.assertEqual(coverage["mgba_case_count"], 35)
        bindings = _index(_rows(BINDINGS), "feature_key")
        feature_results = coverage["feature_checks"]
        self.assertEqual(set(feature_results), set(bindings))
        for feature, result in feature_results.items():
            self.assertEqual(result, {
                "status": "PASS",
                "case": bindings[feature]["mgba_case"],
                "quick": True,
                "full": True,
            }, msg=feature)
        acceptance = coverage["acceptance"]
        self.assertEqual(set(acceptance), ACCEPTANCE_KEYS)
        evidence_sources: list[str] = []
        for key, result in acceptance.items():
            self.assertIsInstance(result, dict, msg=key)
            self.assertEqual(result.get("status"), "PASS", msg=key)
            evidence = result.get("evidence")
            self.assertIsInstance(evidence, dict, msg=key)
            source = evidence.get("source")
            checks = evidence.get("checks")
            self.assertIsInstance(source, str, msg=key)
            self.assertTrue(source.strip(), msg=key)
            self.assertIsInstance(checks, dict, msg=key)
            self.assertTrue(checks, msg=key)
            self.assertTrue(all(value is True for value in checks.values()),
                            msg=key)
            evidence_sources.append(source)
        joined = "\n".join(evidence_sources).lower()
        self.assertIn("quick", joined)
        self.assertIn("full", joined)

        mgba = coverage["mgba"]
        self.assertEqual(set(mgba), {"quick", "full"})
        for mode, artifact in (("quick", MGBA_QUICK), ("full", MGBA_FULL)):
            document = _json(artifact)
            self.assertEqual(mgba[mode], {
                "artifact": artifact.relative_to(ROOT).as_posix(),
                "rom_sha256": document["rom_sha256"],
                "runner_sha256": document["runner_sha256"],
                "cases_sha256": document["cases_sha256"],
                "process_runs": 1,
                "warnings_errors": 0,
            })

    def test_builder_does_not_generate_unconditional_pass_coverage(self) -> None:
        source = Path(build_qol_production.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(
            source,
            r'"acceptance"\s*:\s*\{\s*key\s*:\s*"PASS"\s*'
            r'for\s+key\s+in\s+[A-Za-z_][A-Za-z0-9_]*\s*\}',
        )
        self.assertIn("feature_checks", source)
        self.assertIn("OUTPUT_MGBA_QUICK", source)
        self.assertIn("OUTPUT_MGBA_FULL", source)

    def test_builder_check_mode_never_calls_output_writer(self) -> None:
        fake_outputs = {
            build_qol_production.OUTPUT_META.as_posix(): json.dumps({
                "output": {"sha256": "test-only"},
                "hooks": {"count": 0},
            }).encode("utf-8")
        }
        with (
            mock.patch.object(build_qol_production, "build_outputs",
                              return_value=fake_outputs) as build,
            mock.patch.object(build_qol_production, "_check_outputs") as check,
            mock.patch.object(build_qol_production, "_mgba_outputs",
                              return_value={}) as mgba,
            mock.patch.object(build_qol_production, "_write_outputs") as write,
            mock.patch.object(sys, "argv", ["build_qol_production.py", "check"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = build_qol_production.main()
        self.assertEqual(result, 0)
        self.assertEqual(build.call_count, 2)
        self.assertEqual(check.call_count, 2)
        mgba.assert_called_once_with(fake_outputs)
        write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
