from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.engine.cfru_qol_runtime import (
    BUILD_POKEMON_SOURCE,
    CFRUQolRuntimeError,
    EV_RESET_STATS,
    EXPECTED_CFRU_COMMIT,
    EXPECTED_SOURCE_HASHES,
    EXP_CANDY_VALUES,
    EXP_HEADER,
    GENERATED_HEADER,
    GENERATED_SOURCE,
    ITEM_COUNT,
    ITEM_TABLE_HEADER,
    PARTY_MENU_SOURCE,
    apply_qol_runtime_patches,
    build_qol_runtime,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "vendor/upstream/CFRU-JP"
MODEL_PATH = ROOT / "generated/engine/ids/id_spaces.json"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources() -> dict[str, str]:
    return {
        logical: (SOURCE_ROOT / logical).read_text(encoding="utf-8")
        for logical in EXPECTED_SOURCE_HASHES
    }


HOST_STUB = r'''#ifndef VEGA_QOL_HOST_STUB_H
#define VEGA_QOL_HOST_STUB_H

#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint8_t bool8;

#define FALSE 0
#define TRUE 1
#define MAX_LEVEL 100
#define FLAG_HARD_LEVEL_CAP 1
#define SPECIES_NONE 0

#define STAT_HP 0
#define STAT_ATK 1
#define STAT_DEF 2
#define STAT_SPEED 3
#define STAT_SPATK 4
#define STAT_SPDEF 5

#define MON_DATA_SPECIES 0
#define MON_DATA_IS_EGG 1
#define MON_DATA_EXP 2
#define MON_DATA_LEVEL 3
#define MON_DATA_HP 4
#define MON_DATA_MAX_HP 5
#define MON_DATA_HP_EV 10

struct Pokemon
{
	u16 species;
	bool8 isEgg;
	u32 exp;
	u8 level;
	u16 hp;
	u16 maxHp;
	u8 evs[6];
};

u32 GetMonData(struct Pokemon *mon, int field, const void *data);
void SetMonData(struct Pokemon *mon, int field, const void *data);
u8 GetLevelFromMonExp(struct Pokemon *mon);
u32 GetSpeciesExpToLevel(u16 species, u8 level);
void CalculateMonStats(struct Pokemon *mon);
bool8 FlagGet(u16 flag);
u8 GetCurrentLevelCap(void);

#endif
'''


HOST_HARNESS = r'''#include <stdio.h>
#include <string.h>
#include "include/new/vega_qol_items.h"

static bool8 sHardCapEnabled;
static u8 sHardCap = 100;
static u32 sCalculateCount;

u32 GetSpeciesExpToLevel(u16 species, u8 level)
{
	(void) species;
	return (u32) level * level * level;
}

u8 GetLevelFromMonExp(struct Pokemon *mon)
{
	u16 level;
	u8 result = 1;
	for (level = 2; level <= MAX_LEVEL; ++level)
	{
		if (mon->exp < GetSpeciesExpToLevel(mon->species, (u8) level))
			break;
		result = (u8) level;
	}
	return result;
}

u32 GetMonData(struct Pokemon *mon, int field, const void *data)
{
	(void) data;
	switch (field)
	{
		case MON_DATA_SPECIES: return mon->species;
		case MON_DATA_IS_EGG: return mon->isEgg;
		case MON_DATA_EXP: return mon->exp;
		case MON_DATA_LEVEL: return mon->level;
		case MON_DATA_HP: return mon->hp;
		case MON_DATA_MAX_HP: return mon->maxHp;
		default:
			if (field >= MON_DATA_HP_EV && field < MON_DATA_HP_EV + 6)
				return mon->evs[field - MON_DATA_HP_EV];
			return 0;
	}
}

void SetMonData(struct Pokemon *mon, int field, const void *data)
{
	if (field == MON_DATA_EXP)
		mon->exp = *(const u32 *) data;
	else if (field == MON_DATA_LEVEL)
		mon->level = *(const u8 *) data;
	else if (field == MON_DATA_HP)
		mon->hp = *(const u16 *) data;
	else if (field == MON_DATA_MAX_HP)
		mon->maxHp = *(const u16 *) data;
	else if (field >= MON_DATA_HP_EV && field < MON_DATA_HP_EV + 6)
		mon->evs[field - MON_DATA_HP_EV] = *(const u8 *) data;
}

void CalculateMonStats(struct Pokemon *mon)
{
	u16 oldMax = mon->maxHp;
	u16 newMax;
	++sCalculateCount;
	mon->level = GetLevelFromMonExp(mon);
	newMax = (u16) (20 + mon->level + mon->evs[STAT_HP] / 4);
	mon->maxHp = newMax;
	if (oldMax == 0)
		mon->hp = newMax;
	else if (mon->hp != 0 && newMax >= oldMax)
		mon->hp = (u16) (mon->hp + newMax - oldMax);
}

bool8 FlagGet(u16 flag)
{
	(void) flag;
	return sHardCapEnabled;
}

u8 GetCurrentLevelCap(void)
{
	return sHardCap;
}

#define CHECK(expr) do { if (!(expr)) { printf("FAIL:%d:%s\n", __LINE__, #expr); return 1; } } while (0)

int main(void)
{
	struct VegaQolExpResult expResult;
	struct VegaQolEvResult evResult;
	struct Pokemon first = {1, FALSE, 1, 1, 21, 21, {0, 0, 0, 0, 0, 0}};
	struct Pokemon second = {2, FALSE, 64, 4, 24, 24, {0, 0, 0, 0, 0, 0}};
	struct Pokemon beforeSecond;

	CHECK(VegaQolResolveUseCount(VEGA_QOL_USE_X1, 20) == 1);
	CHECK(VegaQolResolveUseCount(VEGA_QOL_USE_X5, 3) == 3);
	CHECK(VegaQolResolveUseCount(VEGA_QOL_USE_X10, 20) == 10);
	CHECK(VegaQolResolveUseCount(VEGA_QOL_USE_ALL, 17) == 17);
	CHECK(VegaQolResolveUseCount(VEGA_QOL_USE_ALL, 0) == 0);
	CHECK(VegaQolResolveUseCount(99, 17) == 0);

	CHECK(VegaQolExpCandyValue(988) == 100);
	CHECK(VegaQolExpCandyValue(992) == 30000);
	CHECK(VegaQolExpCandyValue(987) == 0);
	CHECK(VegaQolEvResetStat(993) == STAT_HP);
	CHECK(VegaQolEvResetStat(998) == STAT_SPDEF);
	CHECK(VegaQolEvResetStat(992) == 0xFF);

	memcpy(&beforeSecond, &second, sizeof(second));
	sHardCapEnabled = FALSE;
	sCalculateCount = 0;
	CHECK(VegaQolApplyExpCandy(&first, 988, VEGA_QOL_USE_X1, 1, &expResult));
	CHECK(first.exp == 101);
	CHECK(first.level == 4);
	CHECK(expResult.oldLevel == 1 && expResult.newLevel == 4);
	CHECK(expResult.levelsCrossed == 3);
	CHECK(expResult.appliedExp == 100 && expResult.consumedItems == 1);
	CHECK(sCalculateCount == 4); /* Lv2, Lv3, Lv4, then remaining EXP. */
	CHECK(memcmp(&second, &beforeSecond, sizeof(second)) == 0);

	first.exp = 700;
	first.level = 8;
	first.maxHp = 28;
	first.hp = 28;
	sHardCapEnabled = TRUE;
	sHardCap = 10;
	CHECK(VegaQolApplyExpCandy(&first, 988, VEGA_QOL_USE_X10, 10, &expResult));
	CHECK(first.exp == 1000 && first.level == 10);
	CHECK(expResult.requestedItems == 10 && expResult.consumedItems == 3);
	CHECK(expResult.appliedExp == 300 && expResult.stoppedAtCap);
	CHECK(!VegaQolApplyExpCandy(&first, 988, VEGA_QOL_USE_ALL, 99, &expResult));
	CHECK(first.exp == 1000 && expResult.consumedItems == 0);

	first.exp = 1;
	first.level = 1;
	first.maxHp = 21;
	first.hp = 21;
	CHECK(VegaQolApplyExpCandy(&first, 992, VEGA_QOL_USE_ALL, 65535, &expResult));
	CHECK(first.exp == 1000 && expResult.consumedItems == 1);
	CHECK(expResult.appliedExp == 999 && expResult.stoppedAtCap);

	first.isEgg = TRUE;
	first.exp = 1;
	CHECK(!VegaQolApplyExpCandy(&first, 988, VEGA_QOL_USE_X1, 1, &expResult));
	CHECK(first.exp == 1 && expResult.consumedItems == 0);
	first.isEgg = FALSE;
	first.species = 412;
	CHECK(!VegaQolApplyExpCandy(&first, 988, VEGA_QOL_USE_X1, 1, &expResult));
	CHECK(!VegaQolApplyEvResetItem(&first, 994, &evResult));
	first.species = 1;

	first.exp = 1000;
	first.level = 10;
	first.evs[STAT_HP] = 252;
	first.maxHp = 93;
	first.hp = 80;
	CHECK(VegaQolApplyEvResetItem(&first, 993, &evResult));
	CHECK(first.evs[STAT_HP] == 0);
	CHECK(first.maxHp == 30 && first.hp == 17);
	CHECK(evResult.changedStatMask == 1);
	CHECK(evResult.oldEvs[STAT_HP] == 252 && evResult.newEvs[STAT_HP] == 0);
	CHECK(!VegaQolApplyEvResetItem(&first, 993, &evResult));
	CHECK(first.maxHp == 30 && first.hp == 17);

	first.evs[STAT_HP] = 252;
	first.maxHp = 93;
	first.hp = 0;
	CHECK(VegaQolApplyEvResetItem(&first, 993, &evResult));
	CHECK(first.hp == 0 && first.maxHp == 30);

	first.evs[STAT_ATK] = 42;
	first.hp = 30;
	first.maxHp = 30;
	CHECK(VegaQolApplyEvResetItem(&first, 994, &evResult));
	CHECK(first.evs[STAT_ATK] == 0 && first.hp == 30 && first.maxHp == 30);
	CHECK(evResult.changedStatMask == (1u << STAT_ATK));

	first.evs[STAT_ATK] = 1;
	first.evs[STAT_DEF] = 2;
	first.evs[STAT_SPEED] = 3;
	first.evs[STAT_SPATK] = 4;
	first.evs[STAT_SPDEF] = 5;
	CHECK(VegaQolApplyEvResetAll(&first, &evResult));
	CHECK(evResult.changedStatMask == 0x3E);
	CHECK(first.evs[1] == 0 && first.evs[2] == 0 && first.evs[3] == 0);
	CHECK(first.evs[4] == 0 && first.evs[5] == 0);
	CHECK(!VegaQolApplyEvResetAll(&first, &evResult));

	printf("PASS\n");
	return 0;
}
'''


class CFRUQolRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.id_model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
        cls.bundle = build_qol_runtime(SOURCE_ROOT, cls.id_model)

    def test_t05_qol_rows_and_existing_cfru_adapters_are_fixed(self) -> None:
        manifest = self.bundle.manifest()
        self.assertEqual(manifest["model"]["item_count"], ITEM_COUNT)
        self.assertEqual(
            manifest["callbacks"]["FieldUseFunc_ExpCandy"]["item_ids"],
            list(EXP_CANDY_VALUES),
        )
        self.assertEqual(
            manifest["callbacks"]["FieldUseFunc_EvResetZero"]["stat_ids"],
            [value[1] for value in EV_RESET_STATS.values()],
        )
        adapters = manifest["existing_cfru_adapters"]
        self.assertEqual(adapters["ability_capsule_item_id"], 942)
        self.assertEqual(adapters["ability_patch_item_id"], 943)
        self.assertEqual(adapters["mint_item_ids"], list(range(967, 988)))
        self.assertEqual(manifest["handoffs"]["oval_charm_684"], "T08_BREEDING_RUNTIME")
        self.assertIn("STAT_ACCESSOR", manifest["handoffs"]["bottle_caps_853_854"])

    def test_generated_callbacks_are_real_and_party_selected(self) -> None:
        rendered = self.bundle.render()
        source = rendered[GENERATED_SOURCE]
        self.assertIn("void FieldUseFunc_ExpCandy(u8 taskId)", source)
        self.assertIn("void FieldUseFunc_EvResetZero(u8 taskId)", source)
        self.assertIn("gItemUseCB = ItemUseCB_ExpCandy;", source)
        self.assertIn("gItemUseCB = ItemUseCB_EvResetZero;", source)
        self.assertIn("&gPlayerParty[gPartyMenu.slotId]", source)
        self.assertNotIn("FieldUseFunc_ExpCandy:\n\tbx lr", source)
        self.assertNotIn("FieldUseFunc_EvResetZero:\n\tbx lr", source)
        self.assertIn("volatile u8 *bytes", source)
        self.assertNotIn("memset(", source)
        core = source[: source.index("#ifndef VEGA_QOL_HOST_TEST", source.index("bool8 VegaQolApplyEvResetAll"))]
        self.assertNotIn("gPlayerParty", core)
        self.assertNotIn("atk23_getexp", source)
        self.assertNotIn("FLAG_EXP_SHARE", source)

    def test_quantity_cap_and_nonconsume_contract_is_explicit(self) -> None:
        source = self.bundle.render()[GENERATED_SOURCE]
        self.assertIn("case VEGA_QOL_USE_X1:", source)
        self.assertIn("case VEGA_QOL_USE_X5:", source)
        self.assertIn("case VEGA_QOL_USE_X10:", source)
        self.assertIn("case VEGA_QOL_USE_ALL:", source)
        self.assertIn("requiredItems = ((remaining - 1u) / value) + 1u;", source)
        self.assertIn("if (requiredItems < consumedItems)", source)
        self.assertIn("if (oldLevel < 1 || oldLevel >= cap || oldExp >= capExp)", source)
        self.assertIn("species >= VEGA_QOL_SPECIES_COUNT", source)
        self.assertIn("SetMonData(mon, MON_DATA_EXP, &nextLevelExp);", source)
        self.assertIn("ONE_EXPERIENCE_TABLE_THRESHOLD_AT_A_TIME", json.dumps(self.bundle.manifest()))
        self.assertIn("if (result->oldEvs[stat] == 0)", source)
        self.assertEqual(
            self.bundle.manifest()["quantity_ui_boundary"]["choices"],
            ["x1", "x5", "x10", "all"],
        )

    def test_host_core_exercises_exp_ev_cap_overflow_and_selected_only(self) -> None:
        compiler = shutil.which("cc")
        self.assertIsNotNone(compiler, "host C compiler is required for the QOL ABI gate")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for logical, text in self.bundle.render().items():
                target = root / logical
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8", newline="\n")
            (root / "host_stub.h").write_text(HOST_STUB, encoding="utf-8", newline="\n")
            (root / "harness.c").write_text(HOST_HARNESS, encoding="utf-8", newline="\n")
            result = subprocess.run(
                [
                    str(compiler),
                    "-std=c99",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-DVEGA_QOL_HOST_TEST",
                    "-include",
                    str(root / "host_stub.h"),
                    str(root / GENERATED_SOURCE),
                    str(root / "harness.c"),
                    "-I",
                    str(root),
                    "-o",
                    str(root / "qol_host"),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            executed = subprocess.run(
                [str(root / "qol_host")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            self.assertEqual(executed.stdout, "PASS\n")

    def test_header_patch_is_exact_and_bundle_is_deterministic(self) -> None:
        rendered = self.bundle.render()
        self.assertIn('#include "vega_qol_items.h"', rendered[ITEM_TABLE_HEADER])
        self.assertEqual(rendered[ITEM_TABLE_HEADER].count('#include "vega_qol_items.h"'), 1)
        self.assertIn("struct VegaQolExpResult", rendered[GENERATED_HEADER])
        second = build_qol_runtime(SOURCE_ROOT, self.id_model)
        self.assertEqual(rendered, second.render())
        self.assertEqual(self.bundle.manifest(), second.manifest())
        self.assertEqual(self.bundle.manifest()["source"]["commit"], EXPECTED_CFRU_COMMIT)
        self.assertRegex(self.bundle.manifest()["fingerprint"], r"^[0-9a-f]{64}$")

    def test_build_is_side_effect_free(self) -> None:
        inputs = [SOURCE_ROOT / logical for logical in EXPECTED_SOURCE_HASHES]
        before = {path: _digest(path) for path in inputs}
        rendered = self.bundle.render()
        rendered[GENERATED_SOURCE] = "tampered"
        after = {path: _digest(path) for path in inputs}
        self.assertEqual(before, after)
        self.assertNotEqual(self.bundle.render()[GENERATED_SOURCE], "tampered")

    def test_source_set_and_hash_drift_fail_closed(self) -> None:
        sources = _sources()
        missing = dict(sources)
        missing.pop(EXP_HEADER)
        with self.assertRaisesRegex(CFRUQolRuntimeError, "missing"):
            apply_qol_runtime_patches(missing, self.id_model)
        unknown = dict(sources)
        unknown["src/future_qol.c"] = ""
        with self.assertRaisesRegex(CFRUQolRuntimeError, "unknown"):
            apply_qol_runtime_patches(unknown, self.id_model)
        drifted = dict(sources)
        drifted[PARTY_MENU_SOURCE] += "\n/* drift */\n"
        with self.assertRaisesRegex(CFRUQolRuntimeError, "SHA-256不一致"):
            apply_qol_runtime_patches(drifted, self.id_model)

    def test_t05_model_drift_fails_closed(self) -> None:
        drifted = copy.deepcopy(self.id_model)
        drifted["items"][988]["field_effect_param"] = "101"
        with self.assertRaisesRegex(CFRUQolRuntimeError, "field_effect_param不一致"):
            build_qol_runtime(SOURCE_ROOT, drifted)
        drifted = copy.deepcopy(self.id_model)
        drifted["items"][997]["id"] = 998
        with self.assertRaisesRegex(CFRUQolRuntimeError, "連続canonical"):
            build_qol_runtime(SOURCE_ROOT, drifted)
        drifted = copy.deepcopy(self.id_model)
        drifted["items"][943]["field_use_callback_key"] = "NONE"
        with self.assertRaisesRegex(CFRUQolRuntimeError, "field_use_callback_key不一致"):
            build_qol_runtime(SOURCE_ROOT, drifted)

    def test_expected_fixed_source_hashes_cover_all_apis(self) -> None:
        self.assertEqual(
            set(EXPECTED_SOURCE_HASHES),
            {PARTY_MENU_SOURCE, ITEM_TABLE_HEADER, EXP_HEADER, BUILD_POKEMON_SOURCE},
        )
        for logical, expected in EXPECTED_SOURCE_HASHES.items():
            self.assertEqual(_digest(SOURCE_ROOT / logical), expected)


if __name__ == "__main__":
    unittest.main()
