#!/usr/bin/env python3
"""T05 QOL item rows -> fixed CFRU-JP party-menu/runtime adapters.

T06 only owns the battle/stat boundary.  The save fields, quantity-selection
window and level-up/evolution presentation are connected by T08--T10.  This
module nevertheless replaces the two T05 callback placeholders with real,
ROM-callable code and makes that later UI boundary explicit:

* Exp Candy is applied to exactly one ``struct Pokemon`` and never enters the
  battle EXP distributor.  The result records every crossed level boundary.
* the effective level cap and the experience-table ceiling are enforced before
  mutation; unused items beyond the cap are not reported as consumed.
* each EV reset item zeros exactly one canonical stat, recalculates stats, and
  preserves fainted/current-HP semantics when maximum HP falls.
* the common x1/x5/x10/all selector is a small public resolver which clamps to
  the available stack.  The T10 window can call the same API without changing
  the effect core.

The fixed CFRU source is read only.  ``build_qol_runtime`` returns a source
bundle; the parent builder writes it into its disposable source sandbox and
removes the old assembly placeholder symbols.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn


EXPECTED_CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"
EXPECTED_CFRU_TREE = "f4424af017abd01afe2d2deb833fb67275f03804"

PARTY_MENU_SOURCE = "src/party_menu.c"
ITEM_TABLE_HEADER = "include/new/item_tables.h"
EXP_HEADER = "include/new/exp.h"
BUILD_POKEMON_SOURCE = "src/build_pokemon.c"

GENERATED_HEADER = "include/new/vega_qol_items.h"
GENERATED_SOURCE = "src/vega_qol_items.c"

EXPECTED_SOURCE_HASHES: Mapping[str, str] = {
    PARTY_MENU_SOURCE: "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
    ITEM_TABLE_HEADER: "05aa6e8cc119e56b479334a836236fb37c894726dbd704bd6ae7f34cecfd9f38",
    EXP_HEADER: "24fb9429ff217991c4d899c0e15a01e6b63fd42aad6c5f75bb44ccc22e51a48d",
    BUILD_POKEMON_SOURCE: "ac81e3a9a8c7a58105573e6ee2abf62a4b22922e88c6c7d3a1ecdc6c9431e824",
}

ITEM_COUNT = 999

EXP_CANDY_VALUES: Mapping[int, int] = {
    988: 100,
    989: 800,
    990: 3_000,
    991: 10_000,
    992: 30_000,
}

EV_RESET_STATS: Mapping[int, tuple[str, int]] = {
    993: ("STAT_HP", 0),
    994: ("STAT_ATK", 1),
    995: ("STAT_DEF", 2),
    996: ("STAT_SPEED", 3),
    997: ("STAT_SPATK", 4),
    998: ("STAT_SPDEF", 5),
}

_ITEM_HEADER_ANCHOR = (
    "void FieldUseFunc_ExpShare(u8 taskId);\n"
    "void FieldUseFunc_NatureMint(u8 taskId);"
)
_ITEM_HEADER_REPLACEMENT = _ITEM_HEADER_ANCHOR + '\n#include "vega_qol_items.h"'


class CFRUQolRuntimeError(ValueError):
    """固定source、T05 item model、またはQOL ABIが契約外である。"""


def _fail(message: str) -> NoReturn:
    raise CFRUQolRuntimeError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _public(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _public(child)
            for key, child in value.items()
            if not str(key).startswith("_")
        }
    if isinstance(value, (list, tuple)):
        return [_public(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    _fail(f"JSON化できないmodel値: {type(value).__name__}")


def _stable_bytes(value: object) -> bytes:
    return (
        json.dumps(
            _public(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _stable_digest(value: object) -> str:
    return _sha256(_stable_bytes(value))


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        _fail(f"{label} exact anchor数が1ではない: {count}")
    return source.replace(old, new, 1)


def _validate_fixed_sources(sources: Mapping[str, str], verify_hashes: bool) -> dict[str, str]:
    if not isinstance(sources, Mapping):
        _fail("sourcesはlogical path→UTF-8 text mappingである必要がある")
    expected = set(EXPECTED_SOURCE_HASHES)
    actual = set(sources)
    if actual != expected:
        _fail(
            "QOL source集合が不一致: "
            f"missing={sorted(expected - actual)} unknown={sorted(actual - expected)}"
        )
    hashes: dict[str, str] = {}
    for logical, expected_hash in EXPECTED_SOURCE_HASHES.items():
        source = sources[logical]
        if not isinstance(source, str):
            _fail(f"{logical}はUTF-8 textである必要がある")
        actual_hash = _sha256(source.encode("utf-8"))
        hashes[logical] = actual_hash
        if verify_hashes and actual_hash != expected_hash:
            _fail(f"{logical} SHA-256不一致: {actual_hash} != {expected_hash}")

    party = sources[PARTY_MENU_SOURCE]
    required_party_contracts = (
        "void FieldUseFunc_AbilityCapsule(u8 taskId)",
        "static void ItemUseCB_AbilityCapsule(u8 taskId, TaskFunc func)",
        "void FieldUseFunc_NatureMint(u8 taskId)",
        "static void ItemUseCB_NatureMint(u8 taskId, TaskFunc func)",
        "void ItemUseCB_RareCandy(u8 taskId, TaskFunc func)",
        "CalculateMonStats(mon);",
    )
    for anchor in required_party_contracts:
        if anchor not in party:
            _fail(f"固定party-menu APIが欠落: {anchor}")
    if "void FieldUseFunc_ExpCandy(u8 taskId)" in party or "void FieldUseFunc_EvResetZero(u8 taskId)" in party:
        _fail("固定sourceが既にT06 QOL callbackを定義している")

    if "u32 GetSpeciesExpToLevel(u16 species, u8 toLevel);" not in sources[EXP_HEADER]:
        _fail("固定CFRU experience-table APIが欠落")
    if "void CalculateMonStatsNew(struct Pokemon *mon)" not in sources[BUILD_POKEMON_SOURCE]:
        _fail("固定CFRU stat recalculation APIが欠落")
    if sources[ITEM_TABLE_HEADER].count(_ITEM_HEADER_ANCHOR) != 1:
        _fail("固定item_tables.h callback declaration境界が変化")
    return hashes


def _validate_row(row: Mapping[str, Any], item_id: int, expected: Mapping[str, object]) -> None:
    for key, value in expected.items():
        if row.get(key) != value:
            _fail(
                f"T05.items[{item_id}].{key}不一致: "
                f"{row.get(key)!r} != {value!r}"
            )


def _validate_id_model(id_model: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(id_model, Mapping):
        _fail("T05 ID modelはobjectである必要がある")
    if id_model.get("schema_version") != 1 or id_model.get("task") != "T05":
        _fail("T05 ID model schema/task不一致")
    raw_items = id_model.get("items")
    if not isinstance(raw_items, list) or len(raw_items) != ITEM_COUNT:
        _fail(f"T05 itemsは正確に{ITEM_COUNT}行必要")
    items: list[Mapping[str, Any]] = []
    for index, row in enumerate(raw_items):
        if not isinstance(row, Mapping) or row.get("id") != index:
            _fail("T05 item IDは0..998の連続canonical行である必要がある")
        items.append(row)

    exp_keys = ("XS", "S", "M", "L", "XL")
    for item_id, key in zip(EXP_CANDY_VALUES, exp_keys, strict=True):
        _validate_row(
            items[item_id],
            item_id,
            {
                "item_key": f"ITEM_KEY_EXP_CANDY_{key}",
                "classification": "QOL_APPEND",
                "field_effect_key": "EXP_ADD_FIXED",
                "field_effect_param": str(EXP_CANDY_VALUES[item_id]),
                "field_use_callback_key": "FieldUseFunc_ExpCandy",
                "consume_policy": "ON_EFFECT",
                "target_policy": "PARTY_ONE",
                "source_use_type": "ITEM_USE_PARTY_MENU",
                "runtime_binding": "T06_RUNTIME_BIND_PENDING",
            },
        )

    for item_id, (stat_symbol, _stat_id) in EV_RESET_STATS.items():
        _validate_row(
            items[item_id],
            item_id,
            {
                "item_key": f"ITEM_KEY_EV_RESET_{stat_symbol.removeprefix('STAT_')}",
                "classification": "QOL_APPEND",
                "field_effect_key": "EV_SET_ZERO",
                "field_effect_param": stat_symbol,
                "field_use_callback_key": "FieldUseFunc_EvResetZero",
                "consume_policy": "ON_EFFECT",
                "target_policy": "PARTY_ONE",
                "source_use_type": "ITEM_USE_PARTY_MENU",
                "runtime_binding": "T06_RUNTIME_BIND_PENDING",
            },
        )

    for item_id, hidden in ((942, False), (943, True)):
        _validate_row(
            items[item_id],
            item_id,
            {
                "field_use_callback_key": "FieldUseFunc_AbilityCapsule",
                "field_effect_key": "ABILITY_HIDDEN_SET" if hidden else "ABILITY_NORMAL_SWAP",
                "cfru_id": 729 if hidden else 728,
                "runtime_binding": "T06_RUNTIME_BIND_PENDING",
            },
        )
    for item_id in range(967, 988):
        _validate_row(
            items[item_id],
            item_id,
            {
                "field_use_callback_key": "FieldUseFunc_NatureMint",
                "field_effect_key": "NATURE_MODIFIER_SET_KEEP_PERSONALITY",
                "cfru_id": item_id - 214,
                "runtime_binding": "T06_RUNTIME_BIND_PENDING",
            },
        )

    _validate_row(
        items[853],
        853,
        {
            "item_key": "ITEM_KEY_BOTTLE_CAP",
            "field_effect_key": "HYPER_TRAIN_ONE",
            "field_use_callback_key": "SERVICE_CB_HYPER_TRAIN",
            "runtime_binding": "T06_SERVICE_ADAPTER_PENDING",
        },
    )
    _validate_row(
        items[854],
        854,
        {
            "item_key": "ITEM_KEY_GOLD_BOTTLE_CAP",
            "field_effect_key": "HYPER_TRAIN_ALL",
            "field_use_callback_key": "SERVICE_CB_HYPER_TRAIN",
            "runtime_binding": "T06_SERVICE_ADAPTER_PENDING",
        },
    )
    _validate_row(
        items[684],
        684,
        {
            "item_key": "ITEM_KEY_OVAL_CHARM",
            "field_effect_key": "BREEDING_CHECK_MULTIPLIER_X2_CAP100",
            "runtime_binding": "T08_QOL_ADAPTER_PENDING",
        },
    )
    return tuple(items)


def _render_header() -> str:
    return r'''#ifndef POKEMON_VEGA_T06_QOL_ITEMS_H
#define POKEMON_VEGA_T06_QOL_ITEMS_H

#ifndef VEGA_QOL_HOST_TEST
#include "../global.h"
#include "../pokemon.h"
#endif

enum VegaQolQuantityChoice
{
	VEGA_QOL_USE_X1 = 0,
	VEGA_QOL_USE_X5,
	VEGA_QOL_USE_X10,
	VEGA_QOL_USE_ALL,
	VEGA_QOL_USE_CHOICE_COUNT,
};

struct VegaQolExpResult
{
	u32 oldExp;
	u32 newExp;
	u32 appliedExp;
	u16 requestedItems;
	u16 consumedItems;
	u8 oldLevel;
	u8 newLevel;
	u8 levelsCrossed;
	bool8 stoppedAtCap;
};

struct VegaQolEvResult
{
	u8 changedStatMask;
	u8 oldEvs[6];
	u8 newEvs[6];
	u16 oldHp;
	u16 newHp;
	u16 oldMaxHp;
	u16 newMaxHp;
};

u16 VegaQolResolveUseCount(u8 choice, u16 available);
u32 VegaQolExpCandyValue(u16 item);
u8 VegaQolEvResetStat(u16 item);
u8 VegaQolEffectiveLevelCap(void);
bool8 VegaQolApplyExpCandy(
	struct Pokemon *mon,
	u16 item,
	u8 quantityChoice,
	u16 available,
	struct VegaQolExpResult *result);
bool8 VegaQolApplyEvResetItem(
	struct Pokemon *mon,
	u16 item,
	struct VegaQolEvResult *result);
bool8 VegaQolApplyEvResetAll(
	struct Pokemon *mon,
	struct VegaQolEvResult *result);

void FieldUseFunc_ExpCandy(u8 taskId);
void FieldUseFunc_EvResetZero(u8 taskId);

#endif
'''


def _render_source() -> str:
    return r'''#ifndef VEGA_QOL_HOST_TEST
#include "defines.h"
#include "../include/item_use.h"
#include "../include/party_menu.h"
#include "../include/sound.h"
#include "../include/constants/songs.h"
#include "../include/new/build_pokemon.h"
#include "../include/new/exp.h"
#include "../include/new/item.h"
#endif

#include "../include/new/vega_qol_items.h"

#define VEGA_QOL_STAT_COUNT 6
#define VEGA_QOL_INVALID_STAT 0xFF
#define VEGA_QOL_SPECIES_COUNT 1621u

#ifndef VEGA_QOL_HOST_TEST
extern u8 GetCurrentLevelCap(void);
#endif

static void VegaQolZeroBytes(void *destination, u32 size)
{
	volatile u8 *bytes = (volatile u8 *) destination;

	while (size != 0)
	{
		*bytes++ = 0;
		--size;
	}
}

static void VegaQolClearExpResult(struct VegaQolExpResult *result)
{
	if (result != 0)
		VegaQolZeroBytes(result, sizeof(*result));
}

static void VegaQolClearEvResult(struct VegaQolEvResult *result)
{
	if (result != 0)
		VegaQolZeroBytes(result, sizeof(*result));
}

u16 VegaQolResolveUseCount(u8 choice, u16 available)
{
	u16 requested;

	if (available == 0)
		return 0;

	switch (choice)
	{
		case VEGA_QOL_USE_X1:
			requested = 1;
			break;
		case VEGA_QOL_USE_X5:
			requested = 5;
			break;
		case VEGA_QOL_USE_X10:
			requested = 10;
			break;
		case VEGA_QOL_USE_ALL:
			requested = available;
			break;
		default:
			return 0;
	}

	return requested < available ? requested : available;
}

u32 VegaQolExpCandyValue(u16 item)
{
	switch (item)
	{
		case 988u: return 100u;
		case 989u: return 800u;
		case 990u: return 3000u;
		case 991u: return 10000u;
		case 992u: return 30000u;
		default: return 0;
	}
}

u8 VegaQolEvResetStat(u16 item)
{
	switch (item)
	{
		/* T05 canonical order: HP, Atk, Def, Speed, SpAtk, SpDef. */
		case 993u: return 0u;
		case 994u: return 1u;
		case 995u: return 2u;
		case 996u: return 3u;
		case 997u: return 4u;
		case 998u: return 5u;
		default: return VEGA_QOL_INVALID_STAT;
	}
}

u8 VegaQolEffectiveLevelCap(void)
{
	u8 cap = MAX_LEVEL;

#ifdef FLAG_HARD_LEVEL_CAP
	if (FlagGet(FLAG_HARD_LEVEL_CAP))
	{
		u8 hardCap = GetCurrentLevelCap();
		if (hardCap < cap)
			cap = hardCap;
	}
#endif

	if (cap < 1)
		cap = 1;
	return cap;
}

bool8 VegaQolApplyExpCandy(
	struct Pokemon *mon,
	u16 item,
	u8 quantityChoice,
	u16 available,
	struct VegaQolExpResult *result)
{
	u16 species;
	u16 requestedItems;
	u16 consumedItems;
	u16 level;
	u32 value;
	u32 oldExp;
	u32 capExp;
	u32 remaining;
	u32 requiredItems;
	u32 applied;
	u32 committedExp;
	u32 newExp;
	u32 nextLevelExp;
	u8 oldLevel;
	u8 cap;
	u8 plannedLevel;
	u8 levelsCrossed = 0;

	VegaQolClearExpResult(result);
	if (mon == 0 || result == 0)
		return FALSE;

	value = VegaQolExpCandyValue(item);
	requestedItems = VegaQolResolveUseCount(quantityChoice, available);
	species = GetMonData(mon, MON_DATA_SPECIES, 0);
	if (value == 0 || requestedItems == 0 || species == SPECIES_NONE
	 || species >= VEGA_QOL_SPECIES_COUNT
	 || GetMonData(mon, MON_DATA_IS_EGG, 0))
		return FALSE;

	oldLevel = GetLevelFromMonExp(mon);
	cap = VegaQolEffectiveLevelCap();
	oldExp = GetMonData(mon, MON_DATA_EXP, 0);
	capExp = GetSpeciesExpToLevel(species, cap);
	result->oldExp = oldExp;
	result->newExp = oldExp;
	result->oldLevel = oldLevel;
	result->newLevel = oldLevel;
	result->requestedItems = requestedItems;
	if (oldLevel < 1 || oldLevel >= cap || oldExp >= capExp)
	{
		result->stoppedAtCap = TRUE;
		return FALSE;
	}

	remaining = capExp - oldExp;
	requiredItems = ((remaining - 1u) / value) + 1u;
	consumedItems = requestedItems;
	if (requiredItems < consumedItems)
		consumedItems = (u16) requiredItems;
	applied = value * consumedItems;
	if (applied > remaining)
		applied = remaining;
	newExp = oldExp + applied;

	plannedLevel = oldLevel;
	committedExp = oldExp;
	for (level = (u16) oldLevel + 1u; level <= cap; ++level)
	{
		nextLevelExp = GetSpeciesExpToLevel(species, (u8) level);
		if (newExp < nextLevelExp)
			break;
		SetMonData(mon, MON_DATA_EXP, &nextLevelExp);
		CalculateMonStats(mon);
		committedExp = nextLevelExp;
		plannedLevel = (u8) level;
		++levelsCrossed;
	}

	if (committedExp != newExp)
	{
		SetMonData(mon, MON_DATA_EXP, &newExp);
		CalculateMonStats(mon);
	}
	result->newExp = newExp;
	result->appliedExp = applied;
	result->consumedItems = consumedItems;
	result->newLevel = plannedLevel;
	result->levelsCrossed = levelsCrossed;
	result->stoppedAtCap = newExp == capExp;
	return TRUE;
}

static void VegaQolReadEvState(
	struct Pokemon *mon,
	struct VegaQolEvResult *result)
{
	u8 stat;

	result->oldHp = GetMonData(mon, MON_DATA_HP, 0);
	result->oldMaxHp = GetMonData(mon, MON_DATA_MAX_HP, 0);
	for (stat = 0; stat < VEGA_QOL_STAT_COUNT; ++stat)
	{
		result->oldEvs[stat] = GetMonData(mon, MON_DATA_HP_EV + stat, 0);
		result->newEvs[stat] = result->oldEvs[stat];
	}
}

static void VegaQolRecalculatePreservingHp(
	struct Pokemon *mon,
	struct VegaQolEvResult *result)
{
	u16 hp;
	u16 maxHp;
	u16 difference;
	u32 adjustedHp;

	CalculateMonStats(mon);
	maxHp = GetMonData(mon, MON_DATA_MAX_HP, 0);
	if (result->oldHp == 0)
		hp = 0;
	else if (maxHp < result->oldMaxHp)
	{
		difference = result->oldMaxHp - maxHp;
		adjustedHp = result->oldHp > difference ? result->oldHp - difference : 1;
		hp = adjustedHp > maxHp ? maxHp : (u16) adjustedHp;
	}
	else
	{
		difference = maxHp - result->oldMaxHp;
		adjustedHp = (u32) result->oldHp + difference;
		hp = adjustedHp > maxHp ? maxHp : (u16) adjustedHp;
	}
	SetMonData(mon, MON_DATA_HP, &hp);
	result->newHp = hp;
	result->newMaxHp = maxHp;
}

bool8 VegaQolApplyEvResetItem(
	struct Pokemon *mon,
	u16 item,
	struct VegaQolEvResult *result)
{
	u8 stat;
	u8 zero = 0;
	u16 species;

	VegaQolClearEvResult(result);
	if (mon == 0 || result == 0)
		return FALSE;
	stat = VegaQolEvResetStat(item);
	species = GetMonData(mon, MON_DATA_SPECIES, 0);
	if (stat >= VEGA_QOL_STAT_COUNT || species == SPECIES_NONE
	 || species >= VEGA_QOL_SPECIES_COUNT
	 || GetMonData(mon, MON_DATA_IS_EGG, 0))
		return FALSE;

	VegaQolReadEvState(mon, result);
	if (result->oldEvs[stat] == 0)
		return FALSE;
	SetMonData(mon, MON_DATA_HP_EV + stat, &zero);
	result->newEvs[stat] = 0;
	result->changedStatMask = (u8) (1u << stat);
	VegaQolRecalculatePreservingHp(mon, result);
	return TRUE;
}

bool8 VegaQolApplyEvResetAll(
	struct Pokemon *mon,
	struct VegaQolEvResult *result)
{
	u8 stat;
	u8 zero = 0;
	u16 species;

	VegaQolClearEvResult(result);
	if (mon == 0 || result == 0)
		return FALSE;
	species = GetMonData(mon, MON_DATA_SPECIES, 0);
	if (species == SPECIES_NONE || species >= VEGA_QOL_SPECIES_COUNT
	 || GetMonData(mon, MON_DATA_IS_EGG, 0))
		return FALSE;

	VegaQolReadEvState(mon, result);
	for (stat = 0; stat < VEGA_QOL_STAT_COUNT; ++stat)
	{
		if (result->oldEvs[stat] != 0)
		{
			SetMonData(mon, MON_DATA_HP_EV + stat, &zero);
			result->newEvs[stat] = 0;
			result->changedStatMask |= (u8) (1u << stat);
		}
	}
	if (result->changedStatMask == 0)
		return FALSE;
	VegaQolRecalculatePreservingHp(mon, result);
	return TRUE;
}

#ifndef VEGA_QOL_HOST_TEST
#define gText_WontHaveEffect ((const u8*) 0x083DDE0B)

void __attribute__((long_call)) UpdateMonDisplayInfoAfterRareCandy(
	u8 slot,
	struct Pokemon *mon);
u8 __attribute__((long_call)) DisplayPartyMenuMessage(const u8 *text, u8 copyToVram);
void Task_ClosePartyMenuAfterText(u8 taskId);

static void VegaQolDisplayNoEffect(u8 taskId, TaskFunc returnTask)
{
	PlaySE(SE_SELECT);
	gPartyMenuUseExitCallback = FALSE;
	DisplayPartyMenuMessage(gText_WontHaveEffect, TRUE);
	ScheduleBgCopyTilemapToVram(2);
	gTasks[taskId].func = returnTask;
}

static void VegaQolDisplaySuccess(u8 taskId, u16 item)
{
	PlaySE(SE_USE_ITEM);
	DisplayPartyMenuMessage(ItemId_GetDescription(item), TRUE);
	ScheduleBgCopyTilemapToVram(2);
	gTasks[taskId].func = Task_ClosePartyMenuAfterText;
}

static void ItemUseCB_ExpCandy(u8 taskId, TaskFunc returnTask)
{
	struct Pokemon *mon = &gPlayerParty[gPartyMenu.slotId];
	struct VegaQolExpResult result;
	u16 item = Var800E;

	if (!CheckBagHasItem(item, 1)
	 || !VegaQolApplyExpCandy(mon, item, VEGA_QOL_USE_X1, 1, &result))
	{
		VegaQolDisplayNoEffect(taskId, returnTask);
		return;
	}

	RemoveBagItem(item, result.consumedItems);
	UpdateMonDisplayInfoAfterRareCandy(gPartyMenu.slotId, mon);
	VegaQolDisplaySuccess(taskId, item);
}

static void ItemUseCB_EvResetZero(u8 taskId, TaskFunc returnTask)
{
	struct Pokemon *mon = &gPlayerParty[gPartyMenu.slotId];
	struct VegaQolEvResult result;
	u16 item = Var800E;

	if (!CheckBagHasItem(item, 1)
	 || !VegaQolApplyEvResetItem(mon, item, &result))
	{
		VegaQolDisplayNoEffect(taskId, returnTask);
		return;
	}

	RemoveBagItem(item, 1);
	UpdateMonDisplayInfoAfterRareCandy(gPartyMenu.slotId, mon);
	VegaQolDisplaySuccess(taskId, item);
}

void FieldUseFunc_ExpCandy(u8 taskId)
{
	gItemUseCB = ItemUseCB_ExpCandy;
	SetUpItemUseCallback(taskId);
}

void FieldUseFunc_EvResetZero(u8 taskId)
{
	gItemUseCB = ItemUseCB_EvResetZero;
	SetUpItemUseCallback(taskId);
}
#endif
'''


@dataclass(frozen=True)
class QolRuntimeBundle:
    """filesystemへ書き込まないQOL source bundle。"""

    _sources: tuple[tuple[str, str], ...]
    _manifest_json: str

    def render(self) -> dict[str, str]:
        return dict(self._sources)

    def manifest(self) -> dict[str, object]:
        value = json.loads(self._manifest_json)
        if not isinstance(value, dict):  # pragma: no cover - constructor contract
            raise AssertionError("QOL manifest must be an object")
        return value


def apply_qol_runtime_patches(
    sources: Mapping[str, str],
    id_model: Mapping[str, Any],
    *,
    verify_fixed_hashes: bool = True,
) -> QolRuntimeBundle:
    """固定source/modelを検証し、sandboxへ置くsource bundleを返す。"""

    source_hashes = _validate_fixed_sources(sources, verify_fixed_hashes)
    items = _validate_id_model(id_model)

    rendered = {
        ITEM_TABLE_HEADER: _replace_once(
            sources[ITEM_TABLE_HEADER],
            _ITEM_HEADER_ANCHOR,
            _ITEM_HEADER_REPLACEMENT,
            "item_tables QOL API include",
        ),
        GENERATED_HEADER: _render_header(),
        GENERATED_SOURCE: _render_source(),
    }
    if "FieldUseFunc_ExpCandy:\n\tbx lr" in rendered[GENERATED_SOURCE] or "FieldUseFunc_EvResetZero:\n\tbx lr" in rendered[GENERATED_SOURCE]:
        _fail("generated QOL source contains a placeholder callback")

    manifest: dict[str, object] = {
        "schema_version": 1,
        "task": "T06",
        "source": {
            "commit": EXPECTED_CFRU_COMMIT,
            "tree": EXPECTED_CFRU_TREE,
            "inputs": dict(sorted(source_hashes.items())),
        },
        "model": {
            "task": id_model.get("task"),
            "schema_version": id_model.get("schema_version"),
            "item_count": len(items),
            "sha256": _stable_digest(id_model),
        },
        "callbacks": {
            "FieldUseFunc_ExpCandy": {
                "item_ids": list(EXP_CANDY_VALUES),
                "values": list(EXP_CANDY_VALUES.values()),
                "target": "CALLER_SELECTED_STRUCT_POKEMON_ONLY",
                "battle_exp_distributor_calls": 0,
                "level_boundary_result": "OLD_LEVEL_PLUS_ONE_THROUGH_NEW_LEVEL",
                "level_mutation_order": "ONE_EXPERIENCE_TABLE_THRESHOLD_AT_A_TIME",
                "cap": "MIN_MAX_LEVEL_AND_ACTIVE_HARD_CAP",
                "consume": "ONLY_ITEMS_WITH_NONZERO_EFFECT",
            },
            "FieldUseFunc_EvResetZero": {
                "item_ids": list(EV_RESET_STATS),
                "stat_ids": [value[1] for value in EV_RESET_STATS.values()],
                "target": "CALLER_SELECTED_STRUCT_POKEMON_ONLY",
                "recalculate": "CalculateMonStats",
                "consume": "ONLY_WHEN_SELECTED_EV_WAS_NONZERO",
            },
        },
        "quantity_ui_boundary": {
            "choices": ["x1", "x5", "x10", "all"],
            "resolver": "VegaQolResolveUseCount",
            "available_stack_clamp": True,
            "party_menu_window_owner": "T10",
        },
        "existing_cfru_adapters": {
            "ability_capsule_item_id": 942,
            "ability_patch_item_id": 943,
            "ability_callback": "FieldUseFunc_AbilityCapsule",
            "mint_item_ids": list(range(967, 988)),
            "mint_callback": "FieldUseFunc_NatureMint",
            "source_contract": PARTY_MENU_SOURCE,
        },
        "handoffs": {
            "level_move_and_evolution_presentation": "T10_PARTY_MENU_UI",
            "bottle_caps_853_854": "T06_STAT_ACCESSOR_AND_LATER_SERVICE_UI",
            "oval_charm_684": "T08_BREEDING_RUNTIME",
            "save_and_summary": "T10",
        },
        "outputs": {
            logical: {"size": len(text.encode("utf-8")), "sha256": _sha256(text.encode("utf-8"))}
            for logical, text in sorted(rendered.items())
        },
    }
    manifest["fingerprint"] = _stable_digest(manifest)
    return QolRuntimeBundle(tuple(sorted(rendered.items())), _stable_bytes(manifest).decode("utf-8"))


def build_qol_runtime(
    source_root: Path,
    id_model: Mapping[str, Any],
    *,
    verify_fixed_hashes: bool = True,
) -> QolRuntimeBundle:
    """固定CFRU rootを読み、QOL runtime bundleを構築する。"""

    root = Path(source_root)
    sources: dict[str, str] = {}
    for logical in EXPECTED_SOURCE_HASHES:
        path = root / logical
        if path.is_symlink() or not path.is_file():
            _fail(f"固定CFRU sourceが欠落またはsymlink: {logical}")
        try:
            sources[logical] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            _fail(f"固定CFRU sourceを読めない: {logical}: {error}")
    return apply_qol_runtime_patches(
        sources, id_model, verify_fixed_hashes=verify_fixed_hashes
    )


__all__ = [
    "BUILD_POKEMON_SOURCE",
    "CFRUQolRuntimeError",
    "EV_RESET_STATS",
    "EXPECTED_CFRU_COMMIT",
    "EXPECTED_CFRU_TREE",
    "EXPECTED_SOURCE_HASHES",
    "EXP_CANDY_VALUES",
    "EXP_HEADER",
    "GENERATED_HEADER",
    "GENERATED_SOURCE",
    "ITEM_COUNT",
    "ITEM_TABLE_HEADER",
    "PARTY_MENU_SOURCE",
    "QolRuntimeBundle",
    "apply_qol_runtime_patches",
    "build_qol_runtime",
]
