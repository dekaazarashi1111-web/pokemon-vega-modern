#!/usr/bin/env python3
"""T04 Vega-exclusive move plans -> fixed CFRU-JP native effect adapters.

This module is deliberately pure: it accepts the frozen T04 ``move_port.json``
model and returns sources plus an integration manifest.  It never reads the
source Vega battle-script pointer and never emits a pointer into the old ROM.

The generated battle scripts use the current CFRU ``battle_script_macros.s``
ABI.  Semantics which CFRU implements by comparing a move id (rather than by
executing a battle script) are exposed as native queries and accompanied by
fail-closed, exact-count patch contracts.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, NoReturn


class MoveEffectLoweringError(ValueError):
    """The frozen T04 plan or the CFRU lowering contract changed."""


def _fail(message: str) -> NoReturn:
    raise MoveEffectLoweringError(message)


# This is an intentional second lock over T04.  Accepting a newly invented
# operation implicitly would turn an exclusive move into EFFECT_HIT, which is
# exactly the failure mode this lowering boundary exists to prevent.
EXPECTED_MOVE_PLANS: dict[int, tuple[str, ...]] = {
    292: ("DAMAGE", "THREE_STATUS_TOTAL_CHANCE_30"),
    355: ("DAMAGE", "TARGET_FLINCH_CHANCE_10"),
    356: ("DAMAGE", "TARGET_CONFUSION_CHANCE_20"),
    357: ("DAMAGE", "TARGET_ALL_FOES"),
    358: ("DAMAGE", "RECOIL_ONE_THIRD"),
    359: ("DAMAGE", "TARGET_CONFUSION_CHANCE_10"),
    360: ("DAMAGE", "TARGET_DEFENSE_DOWN_1_CHANCE_20"),
    361: ("DAMAGE",),
    418: ("DAMAGE", "USER_SPEED_UP_1_CHANCE_30"),
    425: ("DAMAGE", "RECOIL_ONE_THIRD"),
    426: ("DAMAGE", "USER_SPEED_UP_1_CHANCE_30"),
    427: ("DAMAGE", "HIT_EXACTLY_2", "USER_ATTACK_UP_1_CHANCE_10"),
    428: (
        "DAMAGE", "SOUND_MOVE", "TARGET_ALL_FOES",
        "TARGET_SP_DEFENSE_DOWN_1_CHANCE_20",
    ),
    429: ("USER_SPEED_EVASION_UP_1_ACCURACY_DOWN_1",),
    430: ("YAWN_EQUIVALENT", "ALWAYS_HIT"),
    431: ("DAMAGE", "USER_CONFUSION_CHANCE_20"),
    432: ("DAMAGE", "PRIORITY_MINUS_1", "TRAP_TURNS_4_TO_5"),
    433: ("DAMAGE", "TARGET_ALL_FOES", "NO_EVASION_BOOST"),
    434: ("DAMAGE", "USER_SP_ATTACK_DOWN_2"),
    435: ("DAMAGE", "TARGET_PARALYSIS_CHANCE_30"),
    436: ("DAMAGE", "USER_DEFENSE_DOWN_1_CHANCE_30"),
    437: ("DAMAGE", "TARGET_ALL_FOES", "TARGET_ACCURACY_DOWN_1_CHANCE_20"),
    438: ("DAMAGE", "TARGET_DEFENSE_DOWN_1_CHANCE_30"),
    439: ("DAMAGE", "PRIORITY_PLUS_1"),
    440: ("USER_ATTACK_SPATTACK_UP_1_RAIN_SPATTACK_UP_2",),
    441: ("DAMAGE", "TARGET_ALL_FOES", "TARGET_SPEED_DOWN_1_CHANCE_20"),
    442: ("DAMAGE", "USER_DEFENSE_UP_1_CHANCE_20"),
    443: ("DAMAGE", "TARGET_POISON_CHANCE_30"),
    444: ("DAMAGE", "TARGET_ALL_FOES", "USER_SP_ATTACK_UP_1_CHANCE_20"),
    445: ("ACCURACY_85", "TARGET_CONFUSION_ALWAYS"),
    446: ("DAMAGE", "TARGET_PARALYSIS_CHANCE_10"),
    447: ("DAMAGE", "TARGET_EVASION_DOWN_1_CHANCE_20"),
    448: ("DAMAGE", "TARGET_ALL_FOES", "USER_SP_ATTACK_UP_1_CHANCE_20"),
    449: ("DAMAGE", "TARGET_DEFENSE_DOWN_20_OR_FREEZE_10"),
    450: ("DAMAGE", "TARGET_DEFENSE_DOWN_1_CHANCE_20"),
    451: ("DAMAGE", "HIT_EXACTLY_2", "NO_SECONDARY_EFFECT"),
    452: ("DAMAGE", "TARGET_ALL_FOES", "TARGET_BAD_POISON_CHANCE_20"),
    453: ("DAMAGE", "TARGET_POISON_CHANCE_30"),
    454: ("DAMAGE", "TARGET_SPEED_DOWN_1_CHANCE_30"),
    455: ("DAMAGE", "SOUND_MOVE", "TARGET_SP_DEFENSE_DOWN_1_CHANCE_20"),
    456: ("DAMAGE", "TARGET_ALL_FOES", "TARGET_ACCURACY_DOWN_1_CHANCE_20"),
    457: ("DAMAGE", "USER_ACCURACY_UP_1_CHANCE_30"),
    458: ("DAMAGE", "USER_RANDOM_STAT_UP_1_CHANCE_30"),
    459: ("DAMAGE", "USER_SP_ATTACK_DOWN_1"),
    460: ("DAMAGE", "TARGET_CONFUSION_CHANCE_10"),
    461: ("DAMAGE", "USER_SP_DEFENSE_UP_1_CHANCE_20"),
    462: ("DAMAGE", "TARGET_EVASION_UP_1"),
    463: ("DAMAGE", "TARGET_SLEEP_CHANCE_20"),
    464: ("DYNAMIC_DAMAGE", "WEIGHT_BASED_SPECIAL_POWER"),
    465: ("DAMAGE", "SOUND_MOVE", "USER_SPEED_DOWN_1_CHANCE_20"),
    466: ("DAMAGE", "TARGET_ACCURACY_DOWN_1_CHANCE_20"),
    467: ("DAMAGE", "ROLLING_POWER"),
    468: ("DAMAGE", "USER_SP_DEFENSE_DOWN_1_CHANCE_20"),
    469: ("DAMAGE", "TARGET_ALL_FOES", "USER_SP_ATTACK_UP_1_CHANCE_20"),
    470: ("DAMAGE", "TARGET_CONFUSION_CHANCE_20", "TRAP_TURNS_3"),
    471: ("DYNAMIC_DAMAGE", "USER_HP_SCALED_POWER", "PROTECT_AFFECTED"),
    472: ("DAMAGE", "FALSE_SWIPE_DAMAGE_FLOOR", "PROTECT_AFFECTED"),
    473: ("DAMAGE", "TARGET_ATTACK_UP_1_CHANCE_30", "SOUND_MOVE"),
    474: ("DAMAGE", "PRIORITY_MINUS_4", "DOUBLE_POWER_IF_HIT"),
    475: ("DAMAGE", "USER_BAD_POISON"),
    476: ("DAMAGE", "TARGET_ALL_FOES", "CRITICAL_STAGE_UP_1"),
    477: ("DAMAGE", "PRIORITY_PLUS_1", "SOUND_MOVE"),
    478: ("USER_ACCURACY_UP_2",),
    479: ("DAMAGE", "PRIORITY_MINUS_1", "TRAP_TURNS_4_TO_5"),
    480: ("DAMAGE", "HIT_EXACTLY_3"),
    481: ("DAMAGE", "TARGET_SP_ATTACK_UP_2"),
    482: ("DAMAGE", "TARGET_HIGHER_ATTACK_DOWN_1_CHANCE_30"),
    486: ("DAMAGE", "USER_DEFENSE_SPDEF_SPEED_DOWN_1", "PROTECT_AFFECTED"),
    487: ("DAMAGE", "WEATHER_STATUS_CHANCE_20"),
    509: ("DAMAGE", "CRITICAL_STAGE_UP_2"),
}

EXPECTED_OPERATIONS = frozenset(op for plan in EXPECTED_MOVE_PLANS.values() for op in plan)


# Fixed CFRU-JP ``include/constants/battle_move_effects.h`` namespace.  Keep
# symbolic names beside the numeric row override so a later upstream-numbering
# drift cannot silently turn (for example) Vega's old 0xE6 into Syrup Bomb.
RUNTIME_EFFECT_SYMBOLS: dict[int, str] = {
    0: "EFFECT_HIT",
    2: "EFFECT_POISON_HIT",
    6: "EFFECT_PARALYZE_HIT",
    31: "EFFECT_FLINCH_HIT",
    36: "EFFECT_TRI_ATTACK",
    42: "EFFECT_TRAP",
    48: "EFFECT_RECOIL",
    49: "EFFECT_CONFUSE",
    55: "EFFECT_ACCURACY_UP_2",
    69: "EFFECT_DEFENSE_DOWN_HIT",
    70: "EFFECT_SPEED_DOWN_HIT",
    72: "EFFECT_SPECIAL_DEFENSE_DOWN_HIT",
    73: "EFFECT_ACCURACY_DOWN_HIT",
    74: "EFFECT_EVASION_DOWN_HIT",
    76: "EFFECT_CONFUSE_HIT",
    96: "EFFECT_SPEED_UP_1_HIT",
    110: "EFFECT_SPECIAL_ATTACK_UP_CHANCE",
    117: "EFFECT_ROLLOUT",
    138: "EFFECT_DEFENSE_UP_HIT",
    139: "EFFECT_ATTACK_UP_HIT",
    182: "EFFECT_SUPERPOWER",
    187: "EFFECT_YAWN",
    198: "EFFECT_ATK_SPATK_UP",
    204: "EFFECT_OVERHEAT",
    209: "EFFECT_BAD_POISON_HIT",
}


# Operations implemented by canonical move-table fields, not by the effect
# script.  The validator below verifies the relevant field rather than silently
# discarding these operations.
FIELD_OPERATIONS = frozenset({
    "DAMAGE", "DYNAMIC_DAMAGE", "TARGET_ALL_FOES", "PRIORITY_MINUS_1",
    "PRIORITY_MINUS_4", "PRIORITY_PLUS_1", "ALWAYS_HIT", "ACCURACY_85",
    "PROTECT_AFFECTED", "NO_SECONDARY_EFFECT",
})

# Operations whose mechanics live in CFRU C/table consumers.  A generated
# battle script alone cannot implement these, so each is backed by a native
# query and required patch contract.
QUERY_OPERATIONS = frozenset({
    "SOUND_MOVE", "RECOIL_ONE_THIRD", "HIT_EXACTLY_2", "HIT_EXACTLY_3",
    "NO_EVASION_BOOST", "WEIGHT_BASED_SPECIAL_POWER", "USER_HP_SCALED_POWER",
    "FALSE_SWIPE_DAMAGE_FLOOR", "DOUBLE_POWER_IF_HIT", "CRITICAL_STAGE_UP_1",
    "CRITICAL_STAGE_UP_2",
})


# operation -> (CFRU MOVE_EFFECT expression, dominant runtime EFFECT id).
# A zero runtime id means that CFRU has no exact single EFFECT classification;
# the generated descriptor remains the AI/query source of truth.
EFFECT_OPERATIONS: dict[str, tuple[str, int]] = {
    "THREE_STATUS_TOTAL_CHANCE_30": ("MOVE_EFFECT_TRI_ATTACK", 36),
    "TARGET_FLINCH_CHANCE_10": ("MOVE_EFFECT_FLINCH", 31),
    "TARGET_CONFUSION_CHANCE_20": ("MOVE_EFFECT_CONFUSION", 76),
    "TARGET_CONFUSION_CHANCE_10": ("MOVE_EFFECT_CONFUSION", 76),
    "TARGET_DEFENSE_DOWN_1_CHANCE_20": ("MOVE_EFFECT_DEF_MINUS_1", 69),
    "TARGET_DEFENSE_DOWN_1_CHANCE_30": ("MOVE_EFFECT_DEF_MINUS_1", 69),
    "USER_SPEED_UP_1_CHANCE_30": ("MOVE_EFFECT_SPD_PLUS_1 | MOVE_EFFECT_AFFECTS_USER", 96),
    "USER_ATTACK_UP_1_CHANCE_10": ("MOVE_EFFECT_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER", 139),
    "TARGET_SP_DEFENSE_DOWN_1_CHANCE_20": ("MOVE_EFFECT_SP_DEF_MINUS_1", 72),
    "USER_CONFUSION_CHANCE_20": ("MOVE_EFFECT_CONFUSION | MOVE_EFFECT_AFFECTS_USER", 0),
    "TRAP_TURNS_4_TO_5": ("MOVE_EFFECT_WRAP | MOVE_EFFECT_CERTAIN", 42),
    "USER_SP_ATTACK_DOWN_2": ("MOVE_EFFECT_SP_ATK_MINUS_2 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN", 204),
    "TARGET_PARALYSIS_CHANCE_30": ("MOVE_EFFECT_PARALYSIS", 6),
    "TARGET_PARALYSIS_CHANCE_10": ("MOVE_EFFECT_PARALYSIS", 6),
    "USER_DEFENSE_DOWN_1_CHANCE_30": ("MOVE_EFFECT_DEF_MINUS_1 | MOVE_EFFECT_AFFECTS_USER", 0),
    "TARGET_ACCURACY_DOWN_1_CHANCE_20": ("MOVE_EFFECT_ACC_MINUS_1", 73),
    "TARGET_SPEED_DOWN_1_CHANCE_20": ("MOVE_EFFECT_SPD_MINUS_1", 70),
    "TARGET_SPEED_DOWN_1_CHANCE_30": ("MOVE_EFFECT_SPD_MINUS_1", 70),
    "USER_DEFENSE_UP_1_CHANCE_20": ("MOVE_EFFECT_DEF_PLUS_1 | MOVE_EFFECT_AFFECTS_USER", 138),
    "TARGET_POISON_CHANCE_30": ("MOVE_EFFECT_POISON", 2),
    "USER_SP_ATTACK_UP_1_CHANCE_20": ("MOVE_EFFECT_SP_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER", 110),
    "TARGET_EVASION_DOWN_1_CHANCE_20": ("MOVE_EFFECT_EVS_MINUS_1", 74),
    "TARGET_BAD_POISON_CHANCE_20": ("MOVE_EFFECT_TOXIC", 209),
    "USER_ACCURACY_UP_1_CHANCE_30": ("MOVE_EFFECT_ACC_PLUS_1 | MOVE_EFFECT_AFFECTS_USER", 0),
    "USER_SP_ATTACK_DOWN_1": ("MOVE_EFFECT_SP_ATK_MINUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN", 0),
    "USER_SP_DEFENSE_UP_1_CHANCE_20": ("MOVE_EFFECT_SP_DEF_PLUS_1 | MOVE_EFFECT_AFFECTS_USER", 0),
    "TARGET_EVASION_UP_1": ("MOVE_EFFECT_EVS_PLUS_1 | MOVE_EFFECT_CERTAIN", 0),
    "TARGET_SLEEP_CHANCE_20": ("MOVE_EFFECT_SLEEP", 0),
    "USER_SPEED_DOWN_1_CHANCE_20": ("MOVE_EFFECT_SPD_MINUS_1 | MOVE_EFFECT_AFFECTS_USER", 0),
    "USER_SP_DEFENSE_DOWN_1_CHANCE_20": ("MOVE_EFFECT_SP_DEF_MINUS_1 | MOVE_EFFECT_AFFECTS_USER", 0),
    "TARGET_ATTACK_UP_1_CHANCE_30": ("MOVE_EFFECT_ATK_PLUS_1", 0),
    "USER_BAD_POISON": ("MOVE_EFFECT_TOXIC | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN", 0),
    "TARGET_SP_ATTACK_UP_2": ("MOVE_EFFECT_SP_ATK_PLUS_2 | MOVE_EFFECT_CERTAIN", 0),
}

DYNAMIC_PREPARE_OPERATIONS = frozenset({
    "USER_RANDOM_STAT_UP_1_CHANCE_30", "TARGET_HIGHER_ATTACK_DOWN_1_CHANCE_30",
    "WEATHER_STATUS_CHANCE_20",
})

SPECIAL_SCRIPT_OPERATIONS = frozenset({
    "YAWN_EQUIVALENT", "TARGET_CONFUSION_ALWAYS", "ROLLING_POWER",
    "USER_ACCURACY_UP_2", "USER_SPEED_EVASION_UP_1_ACCURACY_DOWN_1",
    "USER_ATTACK_SPATTACK_UP_1_RAIN_SPATTACK_UP_2",
    "TARGET_DEFENSE_DOWN_20_OR_FREEZE_10", "TRAP_TURNS_3",
    "USER_DEFENSE_SPDEF_SPEED_DOWN_1",
})

LOWERED_OPERATIONS = (
    FIELD_OPERATIONS | QUERY_OPERATIONS | frozenset(EFFECT_OPERATIONS)
    | DYNAMIC_PREPARE_OPERATIONS | SPECIAL_SCRIPT_OPERATIONS
)

if LOWERED_OPERATIONS != EXPECTED_OPERATIONS:
    missing = sorted(EXPECTED_OPERATIONS - LOWERED_OPERATIONS)
    extra = sorted(LOWERED_OPERATIONS - EXPECTED_OPERATIONS)
    raise AssertionError(f"lowering vocabulary mismatch: missing={missing}, extra={extra}")


_COMMAND_SIZE = {
    "attackcanceler": 1,
    "attackstring": 1,
    "ppreduce": 1,
    "accuracycheck": 7,
    "attackanimation": 1,
    "waitanimation": 1,
    "call": 5,
    "callasm": 5,
    "goto": 5,
    "jumpifweather": 12,
    "setmoveeffect": 6,
    "seteffectwithchancetarget": 1,
}
MAX_SCRIPT_BYTES = 96
MAX_SCRIPT_COMMANDS = 24


def _command_opcode(command: str) -> str:
    return command.strip().split(None, 1)[0]


def _script_size(commands: Sequence[str]) -> int:
    size = 0
    for command in commands:
        opcode = _command_opcode(command)
        try:
            size += _COMMAND_SIZE[opcode]
        except KeyError:
            _fail(f"unbounded generated battle-script command: {command}")
    return size


def _status_preamble() -> list[str]:
    return ["attackcanceler", "attackstring", "ppreduce", "attackanimation", "waitanimation"]


def _damage_preamble() -> list[str]:
    return ["attackcanceler", "accuracycheck BS_MOVE_MISSED 0x0", "call STANDARD_DAMAGE"]


def _apply_effect(expression: str) -> list[str]:
    return [f"setmoveeffect {expression}", "seteffectwithchancetarget"]


def _compile_commands(move_id: int, operations: tuple[str, ...]) -> tuple[list[str], int]:
    """Return native CFRU commands and the dominant runtime EFFECT id."""

    if move_id == 430:
        return ["goto BS_187_Yawn"], 187
    if move_id == 445:
        # This uses CFRU's u16-aware current command table.  The old Vega
        # script's u8 jumpifability encoding must never be copied here.
        return ["goto BS_049_SetConfusion"], 49
    if move_id == 467:
        return ["goto BS_117_Rollout"], 117
    if move_id == 478:
        return ["goto BS_055_RaiseUserAcc2"], 55
    if "RECOIL_ONE_THIRD" in operations:
        # The resolver still executes this adapter, not BS_048.  The native
        # effect byte is nevertheless required so CFRU's AI reaches its recoil
        # classification; the descriptor query supplies the exact 1/3 ratio.
        return ["goto BS_STANDARD_HIT"], 48
    if move_id == 429:
        commands = _status_preamble()
        commands += _apply_effect("MOVE_EFFECT_SPD_PLUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += _apply_effect("MOVE_EFFECT_EVS_PLUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += _apply_effect("MOVE_EFFECT_ACC_MINUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += ["goto BS_MOVE_END"]
        return commands, 0
    if move_id == 440:
        commands = _status_preamble()
        commands += ["jumpifweather WEATHER_RAIN_ANY VegaMoveEffectScript_440_Rain"]
        commands += _apply_effect("MOVE_EFFECT_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += _apply_effect("MOVE_EFFECT_SP_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += ["goto BS_MOVE_END", "VegaMoveEffectScript_440_Rain:"]
        commands += _apply_effect("MOVE_EFFECT_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += _apply_effect("MOVE_EFFECT_SP_ATK_PLUS_2 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += ["goto BS_MOVE_END"]
        return commands, 198
    if move_id == 449:
        commands = _damage_preamble()
        commands += _apply_effect("MOVE_EFFECT_DEF_MINUS_1")
        commands += _apply_effect("MOVE_EFFECT_FREEZE")
        commands += ["goto BS_MOVE_FAINT"]
        return commands, 69
    if move_id == 470:
        commands = _damage_preamble()
        commands += _apply_effect("MOVE_EFFECT_CONFUSION")
        commands += _apply_effect("MOVE_EFFECT_WRAP | MOVE_EFFECT_CERTAIN")
        commands += ["goto BS_MOVE_FAINT"]
        return commands, 76
    if move_id == 486:
        commands = _damage_preamble()
        for effect in ("MOVE_EFFECT_DEF_MINUS_1", "MOVE_EFFECT_SP_DEF_MINUS_1", "MOVE_EFFECT_SPD_MINUS_1"):
            commands += _apply_effect(effect + " | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN")
        commands += ["goto BS_MOVE_FAINT"]
        return commands, 182

    dynamic = [op for op in operations if op in DYNAMIC_PREPARE_OPERATIONS]
    effects = [op for op in operations if op in EFFECT_OPERATIONS]
    if len(dynamic) > 1 or (dynamic and effects):
        _fail(f"move {move_id}: ambiguous dynamic/effect lowering")
    if dynamic:
        return ["callasm VegaMoveEffectPrepare", "goto BS_STANDARD_HIT"], 0
    if len(effects) > 1:
        _fail(f"move {move_id}: multiple effects need an explicit native script")
    if effects:
        expression, runtime_effect = EFFECT_OPERATIONS[effects[0]]
        return [f"setmoveeffect {expression}", "goto BS_STANDARD_HIT"], runtime_effect
    return ["goto BS_STANDARD_HIT"], 0


def _validate_field_operations(move_id: int, row: Mapping[str, Any], operations: tuple[str, ...]) -> None:
    battle = row.get("battle")
    if not isinstance(battle, Mapping):
        _fail(f"move {move_id}: battle row missing")

    expected: dict[str, int] = {}
    if "TARGET_ALL_FOES" in operations:
        expected["target"] = 0x8
    if "PRIORITY_MINUS_1" in operations:
        expected["priority"] = -1
    if "PRIORITY_MINUS_4" in operations:
        expected["priority"] = -4
    if "PRIORITY_PLUS_1" in operations:
        expected["priority"] = 1
    if "ALWAYS_HIT" in operations:
        expected["accuracy"] = 0
    if "ACCURACY_85" in operations:
        expected["accuracy"] = 85
    if "NO_SECONDARY_EFFECT" in operations:
        expected["secondary"] = 0
    if "PROTECT_AFFECTED" in operations:
        flags = battle.get("flags")
        if not isinstance(flags, int) or isinstance(flags, bool) or not flags & 0x2:
            _fail(f"move {move_id}: PROTECT_AFFECTED flag missing")
    for field, value in expected.items():
        if battle.get(field) != value:
            _fail(f"move {move_id}: {field}={battle.get(field)!r}, expected {value}")


def _extract_rows(move_model: Mapping[str, Any]) -> list[tuple[int, Mapping[str, Any], tuple[str, ...]]]:
    raw_rows = move_model.get("moves")
    if not isinstance(raw_rows, list):
        _fail("T04 move model rows missing")

    rows: list[tuple[int, Mapping[str, Any], tuple[str, ...]]] = []
    for row in raw_rows:
        if not isinstance(row, Mapping):
            _fail("T04 move row must be an object")
        adapter = row.get("effect_adapter")
        if adapter is None:
            continue
        if not isinstance(adapter, Mapping):
            _fail("T04 effect_adapter must be an object")
        move_id = row.get("id")
        if not isinstance(move_id, int) or isinstance(move_id, bool):
            _fail("T04 adapter move id must be an integer")
        plan = adapter.get("effect_plan")
        if not isinstance(plan, Mapping):
            _fail(f"move {move_id}: effect_plan missing")
        raw_operations = plan.get("operations")
        if not isinstance(raw_operations, list) or not all(isinstance(op, str) for op in raw_operations):
            _fail(f"move {move_id}: operations must be a string list")
        operations = tuple(raw_operations)
        unknown = set(operations) - EXPECTED_OPERATIONS
        if unknown:
            _fail(f"move {move_id}: unknown operation(s): {sorted(unknown)}")
        expected = EXPECTED_MOVE_PLANS.get(move_id)
        if expected is None:
            _fail(f"unexpected T04 adapter move: {move_id}")
        if operations != expected:
            _fail(f"move {move_id}: plan changed: {operations!r} != {expected!r}")
        if (
            adapter.get("kind") != "GENERATED_ADAPTER"
            or adapter.get("binding_status") != "COMPILED_INTERFACE_T06_RUNTIME_BIND_PENDING"
            or plan.get("runtime_binding") != "T06_CFRU_EFFECT_DISPATCH"
        ):
            _fail(f"move {move_id}: T04 adapter lifecycle contract changed")
        _validate_field_operations(move_id, row, operations)
        rows.append((move_id, row, operations))

    rows.sort(key=lambda item: item[0])
    actual_ids = [item[0] for item in rows]
    if actual_ids != sorted(EXPECTED_MOVE_PLANS):
        missing = sorted(set(EXPECTED_MOVE_PLANS) - set(actual_ids))
        extra = sorted(set(actual_ids) - set(EXPECTED_MOVE_PLANS))
        _fail(f"T04 adapter set changed: count={len(rows)}, missing={missing}, extra={extra}")
    return rows


def _descriptor_flags(operations: tuple[str, ...]) -> int:
    flags = 0
    for operation, bit in (
        ("SOUND_MOVE", 0x0001),
        ("FALSE_SWIPE_DAMAGE_FLOOR", 0x0002),
        ("NO_EVASION_BOOST", 0x0004),
        ("WEIGHT_BASED_SPECIAL_POWER", 0x0008),
        ("USER_HP_SCALED_POWER", 0x0010),
        ("DOUBLE_POWER_IF_HIT", 0x0020),
        ("ROLLING_POWER", 0x0040),
    ):
        if operation in operations:
            flags |= bit
    return flags


def _render_asm(bindings: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        ".thumb", ".text", ".align 2", "",
        '.include "../asm_defines.s"',
        '.include "../battle_script_macros.s"', "",
        "@ Generated from the frozen T04 operation plans; no Vega script bytes are reused.",
    ]
    for binding in bindings:
        symbol = binding["script_symbol"]
        lines += ["", f".global {symbol}", f"{symbol}:"]
        for command in binding["script_commands"]:
            if command.endswith(":"):
                lines.append(command)
            else:
                lines.append(f"\t{command}")
    # The parent linker audit builds each half-open script range from one
    # public entry symbol to the next.  The final entry needs a public,
    # non-entry sentinel so its range never extends into an unrelated section.
    lines += ["", ".global VegaMoveEffectAdaptersEnd", "VegaMoveEffectAdaptersEnd:"]
    return "\n".join(lines) + "\n"


def _render_header() -> str:
    return """#pragma once

#include "../global.h"

struct DamageCalc;

enum VegaMoveEffectSemanticFlags
{
    VEGA_MOVE_EFFECT_SOUND = 1 << 0,
    VEGA_MOVE_EFFECT_FALSE_SWIPE = 1 << 1,
    VEGA_MOVE_EFFECT_IGNORE_POSITIVE_EVASION = 1 << 2,
    VEGA_MOVE_EFFECT_WEIGHT_POWER = 1 << 3,
    VEGA_MOVE_EFFECT_HP_POWER = 1 << 4,
    VEGA_MOVE_EFFECT_DOUBLE_IF_HIT = 1 << 5,
    VEGA_MOVE_EFFECT_ROLLING = 1 << 6,
};

enum VegaDamageCalculationFlags
{
    VEGA_DAMAGE_FLAG_CHECKING_FROM_MENU = 0x4,
    VEGA_DAMAGE_FLAG_AI_CALC = 0x8,
};

struct VegaMoveEffectDescriptor
{
    u16 move;
    u8 runtimeEffect;
    u8 fixedHitCount;
    u8 recoilDenominator;
    u8 criticalStage;
    u16 semanticFlags;
};

const struct VegaMoveEffectDescriptor *VegaMoveEffectDescriptorFor(u16 move);
bool8 VegaMoveEffectIsSound(u16 move);
bool8 VegaMoveEffectHasFalseSwipeFloor(u16 move);
bool8 VegaMoveEffectIgnoresPositiveEvasion(u16 move);
u8 VegaMoveEffectFixedHitCount(u16 move);
u8 VegaMoveEffectRecoilDenominator(u16 move);
u8 VegaMoveEffectCriticalStage(u16 move);
u8 VegaMoveEffectTrapTurns(u16 move, u8 fallbackTurns);
u32 VegaMoveEffectSecondaryChance(u16 move, u8 moveEffect, u32 fallbackChance);
bool8 VegaMoveEffectCanRollSecondaryOnce(u16 move, u8 moveEffect);
bool8 VegaMoveEffectIsRolling(u16 move);
u16 VegaMoveEffectAdjustBasePower(const struct DamageCalc *data, u16 power);
void VegaMoveEffectPrepare(void);
"""


def _render_c(bindings: Sequence[Mapping[str, Any]]) -> str:
    descriptors = []
    for binding in bindings:
        descriptors.append(
            "    {%du, %du, %du, %du, %du, 0x%04Xu},"
            % (
                binding["move_id"], binding["runtime_effect_id"],
                binding["fixed_hit_count"], binding["recoil_denominator"],
                binding["critical_stage"], binding["semantic_flags"],
            )
        )
    return """#include "defines.h"
#include "defines_battle.h"
#include "../include/random.h"
#include "../include/constants/battle.h"
#include "../include/new/damage_calc.h"
#include "../include/new/vega_move_effect_adapters.h"

static const struct VegaMoveEffectDescriptor sVegaMoveEffects[] =
{
%s
};

const struct VegaMoveEffectDescriptor *VegaMoveEffectDescriptorFor(u16 move)
{
    u32 i;
    for (i = 0; i < NELEMS(sVegaMoveEffects); ++i)
        if (sVegaMoveEffects[i].move == move)
            return &sVegaMoveEffects[i];
    return NULL;
}

static bool8 HasFlag(u16 move, u16 flag)
{
    const struct VegaMoveEffectDescriptor *descriptor = VegaMoveEffectDescriptorFor(move);
    return descriptor != NULL && (descriptor->semanticFlags & flag) != 0;
}

bool8 VegaMoveEffectIsSound(u16 move)
{
    return HasFlag(move, VEGA_MOVE_EFFECT_SOUND);
}

bool8 VegaMoveEffectHasFalseSwipeFloor(u16 move)
{
    return HasFlag(move, VEGA_MOVE_EFFECT_FALSE_SWIPE);
}

bool8 VegaMoveEffectIgnoresPositiveEvasion(u16 move)
{
    return HasFlag(move, VEGA_MOVE_EFFECT_IGNORE_POSITIVE_EVASION);
}

u8 VegaMoveEffectFixedHitCount(u16 move)
{
    const struct VegaMoveEffectDescriptor *descriptor = VegaMoveEffectDescriptorFor(move);
    return descriptor == NULL ? 0 : descriptor->fixedHitCount;
}

u8 VegaMoveEffectRecoilDenominator(u16 move)
{
    const struct VegaMoveEffectDescriptor *descriptor = VegaMoveEffectDescriptorFor(move);
    return descriptor == NULL ? 0 : descriptor->recoilDenominator;
}

u8 VegaMoveEffectCriticalStage(u16 move)
{
    const struct VegaMoveEffectDescriptor *descriptor = VegaMoveEffectDescriptorFor(move);
    return descriptor == NULL ? 0 : descriptor->criticalStage;
}

u8 VegaMoveEffectTrapTurns(u16 move, u8 fallbackTurns)
{
    return move == 470u ? 3u : fallbackTurns;
}

u32 VegaMoveEffectSecondaryChance(u16 move, u8 moveEffect, u32 fallbackChance)
{
    if (move == 449u && (moveEffect & 0x3Fu) == MOVE_EFFECT_FREEZE)
        return 10u;
    return fallbackChance;
}

bool8 VegaMoveEffectCanRollSecondaryOnce(u16 move, u8 moveEffect)
{
    if (move == 427u
     && moveEffect == (MOVE_EFFECT_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER)
     && MOVE_HAD_EFFECT)
    {
        if (gNewBS->secondaryEffectApplied)
            return FALSE;
        /* CMD49 redispatches the move script for hit two.  Consume the single
         * 10%% roll before RNG so a failed first roll cannot roll again. */
        gNewBS->secondaryEffectApplied = TRUE;
    }
    return TRUE;
}

bool8 VegaMoveEffectIsRolling(u16 move)
{
    return HasFlag(move, VEGA_MOVE_EFFECT_ROLLING);
}

u16 VegaMoveEffectAdjustBasePower(const struct DamageCalc *data, u16 power)
{
    if (data == NULL)
        return power;
    switch (data->move)
    {
        case 464u:
        {
            u32 weight = GetActualSpeciesWeight(
                data->defSpecies, data->defAbility, data->defItemEffect,
                data->bankDef, data->monDef == NULL) / 10u;
            if (weight >= 200u) return 120u;
            if (weight >= 100u) return 100u;
            if (weight >= 50u) return 80u;
            if (weight >= 25u) return 60u;
            if (weight >= 10u) return 40u;
            return 20u;
        }
        case 471u:
            if (data->atkMaxHP != 0u)
            {
                u16 scaledPower = (150u * data->atkHP) / data->atkMaxHP;
                return scaledPower == 0u ? 1u : scaledPower;
            }
            return 1u;
        case 474u:
            if (!(data->specialFlags & (VEGA_DAMAGE_FLAG_CHECKING_FROM_MENU | VEGA_DAMAGE_FLAG_AI_CALC))
             && data->monAtk == NULL
             && ((gProtectStructs[data->bankAtk].physicalDmg
               && gProtectStructs[data->bankAtk].physicalBank == data->bankDef)
              || (gProtectStructs[data->bankAtk].specialDmg
               && gProtectStructs[data->bankAtk].specialBank == data->bankDef)))
                return power * 2u;
            return power;
        default:
            return power;
    }
}

void VegaMoveEffectPrepare(void)
{
    switch (gCurrentMove)
    {
        case 458u:
            gBattleCommunication[MOVE_EFFECT_BYTE] =
                (MOVE_EFFECT_ATK_PLUS_1 + (Random() %% 7u)) | MOVE_EFFECT_AFFECTS_USER;
            break;
        case 482u:
            gBattleCommunication[MOVE_EFFECT_BYTE] =
                gBattleMons[gBankTarget].attack >= gBattleMons[gBankTarget].spAttack
                ? MOVE_EFFECT_ATK_MINUS_1 : MOVE_EFFECT_SP_ATK_MINUS_1;
            break;
        case 487u:
            if (gBattleWeather & WEATHER_SUN_ANY)
                gBattleCommunication[MOVE_EFFECT_BYTE] = MOVE_EFFECT_BURN;
            else if (gBattleWeather & WEATHER_HAIL_ANY)
                gBattleCommunication[MOVE_EFFECT_BYTE] = MOVE_EFFECT_FREEZE;
            else if (gBattleWeather & WEATHER_RAIN_ANY)
                gBattleCommunication[MOVE_EFFECT_BYTE] = MOVE_EFFECT_PARALYSIS;
            else
                gBattleCommunication[MOVE_EFFECT_BYTE] = MOVE_EFFECT_POISON;
            break;
        default:
            gBattleCommunication[MOVE_EFFECT_BYTE] = 0;
            break;
    }
}
""" % "\n".join(descriptors)


def _required_patches() -> list[dict[str, Any]]:
    """Exact fixed-CFRU integration contracts for non-script consumers."""

    patches: list[dict[str, Any]] = []
    include_paths = {
        "src/accuracy_calc.c": ('#include "defines_battle.h"', "../include/new/vega_move_effect_adapters.h"),
        "src/attackcanceler.c": ('#include "defines_battle.h"', "../include/new/vega_move_effect_adapters.h"),
        "src/battle_util.c": ('#include "defines_battle.h"', "../include/new/vega_move_effect_adapters.h"),
        "src/cmd49.c": ('#include "defines_battle.h"', "../include/new/vega_move_effect_adapters.h"),
        "src/damage_calc.c": ('#include "defines_battle.h"', "../include/new/vega_move_effect_adapters.h"),
        "src/set_effect.c": ('#include "defines_battle.h"', "../include/new/vega_move_effect_adapters.h"),
        "src/Battle_AI/ai_negatives.c": ('#include "../defines_battle.h"', "../../include/new/vega_move_effect_adapters.h"),
    }
    for path, (anchor, header) in include_paths.items():
        patches.append({
            "id": "include-native-adapter-" + path.replace("/", "-").replace(".", "-"),
            "path": path,
            "needle": anchor,
            "replacement": anchor + '\n#include "' + header + '"',
            "expected_count": 1,
            "consumers": ["native adapter declaration"],
        })
    patches.extend([
        {
            "id": "damage-calculation-flag-namespace",
            "path": "src/damage_calc.c",
            "needle": "#define FLAG_CHECKING_FROM_MENU 0x4\n#define FLAG_AI_CALC 0x8",
            "replacement": (
                "#define FLAG_CHECKING_FROM_MENU 0x4\n"
                "#define FLAG_AI_CALC 0x8\n"
                "_Static_assert(FLAG_CHECKING_FROM_MENU == VEGA_DAMAGE_FLAG_CHECKING_FROM_MENU, \"menu damage flag ABI\");\n"
                "_Static_assert(FLAG_AI_CALC == VEGA_DAMAGE_FLAG_AI_CALC, \"AI damage flag ABI\");"
            ),
            "expected_count": 1,
            "consumers": ["runtime damage", "AI damage", "menu damage"],
        },
        {
            "id": "sound-central-query",
            "path": "src/battle_util.c",
            "needle": "return CheckTableForMove(move, gSoundMoves);",
            "replacement": "return CheckTableForMove(move, gSoundMoves) || VegaMoveEffectIsSound(move);",
            "expected_count": 1,
            "consumers": ["battle", "AI", "Soundproof", "Throat Spray", "move limitation"],
        },
        {
            "id": "recoil-runtime-query",
            "path": "src/cmd49.c",
            "needle": "CheckTableForMove(gCurrentMove, gPercent33RecoilMoves)",
            "replacement": "(CheckTableForMove(gCurrentMove, gPercent33RecoilMoves) || VegaMoveEffectRecoilDenominator(gCurrentMove) == 3)",
            "expected_count": 1,
            "consumers": ["battle move-end recoil"],
        },
        {
            "id": "recoil-ai-query",
            "path": "src/Battle_AI/ai_negatives.c",
            "needle": "CheckTableForMove(move, gPercent33RecoilMoves)",
            "replacement": "(CheckTableForMove(move, gPercent33RecoilMoves) || VegaMoveEffectRecoilDenominator(move) == 3)",
            "expected_count": 1,
            "consumers": ["AI recoil scoring"],
        },
        {
            "id": "fixed-hit-runtime-query",
            "path": "src/attackcanceler.c",
            "needle": "if (CheckTableForMove(gCurrentMove, gTwoToFiveStrikesMoves))\n\t\t\t{",
            "replacement": (
                "if (VegaMoveEffectFixedHitCount(gCurrentMove) != 0)\n\t\t\t{\n"
                "\t\t\t\tgMultiHitCounter = VegaMoveEffectFixedHitCount(gCurrentMove);\n"
                "\t\t\t\tPREPARE_BYTE_NUMBER_BUFFER(gBattleScripting.multihitString, 1, 0)\n"
                "\t\t\t}\n"
                "\t\t\telse if (CheckTableForMove(gCurrentMove, gTwoToFiveStrikesMoves))\n\t\t\t{"
            ),
            "expected_count": 1,
            "consumers": ["battle fixed-hit state"],
        },
        {
            "id": "fixed-hit-damage-query",
            "path": "src/damage_calc.c",
            "needle": "if (move == MOVE_SURGINGSTRIKES",
            "replacement": (
                "u8 vegaFixedHitCount = VegaMoveEffectFixedHitCount(move);\n"
                "\tif (vegaFixedHitCount != 0)\n"
                "\t\tnumHits = vegaFixedHitCount;\n"
                "\telse if (move == MOVE_SURGINGSTRIKES"
            ),
            "expected_count": 1,
            "consumers": ["battle damage", "AI damage"],
        },
        {
            "id": "fixed-hit-ai-party-query",
            "path": "src/damage_calc.c",
            "needle": "if (CheckTableForMove(move, gTwoToFiveStrikesMoves) && GetMonAbility(monAtk) == ABILITY_SKILLLINK)",
            "replacement": (
                "u8 vegaFixedHitCount = VegaMoveEffectFixedHitCount(move);\n\n"
                "\tif (vegaFixedHitCount != 0)\n"
                "\t{\n"
                "\t\tdamage *= vegaFixedHitCount;\n"
                "\t\treturn damage;\n"
                "\t}\n"
                "\telse if (CheckTableForMove(move, gTwoToFiveStrikesMoves) && GetMonAbility(monAtk) == ABILITY_SKILLLINK)"
            ),
            "expected_count": 1,
            "consumers": ["AI party damage fixed-hit multiplier"],
        },
        {
            "id": "fixed-hit-ai-active-query",
            "path": "src/damage_calc.c",
            "needle": "if (CheckTableForMove(move, gTwoToFiveStrikesMoves) && ABILITY(bankAtk) == ABILITY_SKILLLINK)",
            "replacement": (
                "u8 vegaFixedHitCount = VegaMoveEffectFixedHitCount(move);\n\n"
                "\tif (vegaFixedHitCount != 0)\n"
                "\t{\n"
                "\t\tdamage *= vegaFixedHitCount;\n"
                "\t\treturn damage;\n"
                "\t}\n"
                "\telse if (CheckTableForMove(move, gTwoToFiveStrikesMoves) && ABILITY(bankAtk) == ABILITY_SKILLLINK)"
            ),
            "expected_count": 1,
            "consumers": ["AI active-defender damage fixed-hit multiplier"],
        },
        {
            "id": "fixed-hit-parental-bond-query",
            "path": "src/battle_util.c",
            "needle": "&& gBattleMoves[move].effect != EFFECT_DOUBLE_HIT)",
            "replacement": (
                "&& gBattleMoves[move].effect != EFFECT_DOUBLE_HIT\n"
                "\t&& VegaMoveEffectFixedHitCount(move) == 0)"
            ),
            "expected_count": 1,
            "consumers": ["battle fixed-hit Parental Bond exclusion", "AI Parental Bond damage"],
        },
        {
            "id": "false-swipe-positive-query",
            "path": "src/damage_calc.c",
            "needle": "gBattleMoves[move].effect == EFFECT_FALSE_SWIPE",
            "replacement": "(gBattleMoves[move].effect == EFFECT_FALSE_SWIPE || VegaMoveEffectHasFalseSwipeFloor(move))",
            "expected_count": 3,
            "consumers": ["runtime damage", "AI party damage", "AI active damage"],
        },
        {
            "id": "false-swipe-negative-query",
            "path": "src/damage_calc.c",
            "needle": "gBattleMoves[gCurrentMove].effect != EFFECT_FALSE_SWIPE",
            "replacement": "(gBattleMoves[gCurrentMove].effect != EFFECT_FALSE_SWIPE && !VegaMoveEffectHasFalseSwipeFloor(gCurrentMove))",
            "expected_count": 1,
            "consumers": ["final damage floor"],
        },
        {
            "id": "ignore-positive-evasion-query",
            "path": "src/accuracy_calc.c",
            "needle": "else if (atkAbility == ABILITY_KEENEYE || atkAbility == ABILITY_MINDSEYE)",
            "replacement": (
                "else if (atkAbility == ABILITY_KEENEYE || atkAbility == ABILITY_MINDSEYE\n"
                "\t|| VegaMoveEffectIgnoresPositiveEvasion(move))"
            ),
            "expected_count": 1,
            "consumers": ["runtime positive-evasion-only accuracy", "AI positive-evasion-only accuracy"],
        },
        {
            "id": "critical-runtime-query",
            "path": "src/damage_calc.c",
            "needle": "+ (CheckTableForMove(gCurrentMove, gHighCriticalChanceMoves))",
            "replacement": "+ (CheckTableForMove(gCurrentMove, gHighCriticalChanceMoves))\n\t\t\t\t\t\t+ VegaMoveEffectCriticalStage(gCurrentMove)",
            "expected_count": 1,
            "consumers": ["runtime critical rank"],
        },
        {
            "id": "critical-ai-query",
            "path": "src/damage_calc.c",
            "needle": "+ (CheckTableForMove(move, gHighCriticalChanceMoves))",
            "replacement": "+ (CheckTableForMove(move, gHighCriticalChanceMoves))\n\t\t\t\t\t+ VegaMoveEffectCriticalStage(move)",
            "expected_count": 1,
            "consumers": ["AI critical rank"],
        },
        {
            "id": "dynamic-power-query",
            "path": "src/damage_calc.c",
            "needle": "gBattleMovePower = power;\n\treturn power;",
            "replacement": "power = VegaMoveEffectAdjustBasePower(data, power);\n\tgBattleMovePower = power;\n\treturn power;",
            "expected_count": 1,
            "consumers": ["runtime base power", "AI base power", "menu base power"],
        },
        {
            "id": "rolling-power-query",
            "path": "src/damage_calc.c",
            "needle": "\t\tcase MOVE_ROLLOUT:\n\t\tcase MOVE_ICEBALL:\n",
            "replacement": (
                "\t\tcase MOVE_ROLLOUT:\n"
                "\t\tcase MOVE_ICEBALL:\n"
                "\t\tcase 467u: /* Vega rolling-power adapter */\n"
            ),
            "expected_count": 1,
            "consumers": ["runtime Rollout timer", "Defense Curl power doubling"],
        },
        {
            "id": "per-effect-secondary-chance",
            "path": "src/set_effect.c",
            "needle": "u32 percentChance = gBattleMoves[gCurrentMove].secondaryEffectChance;",
            "replacement": "u32 percentChance = VegaMoveEffectSecondaryChance(gCurrentMove, gBattleCommunication[MOVE_EFFECT_BYTE], gBattleMoves[gCurrentMove].secondaryEffectChance);",
            "expected_count": 1,
            "consumers": ["compound secondary effects"],
        },
        {
            "id": "fixed-hit-user-secondary-once",
            "path": "src/set_effect.c",
            "needle": "else if (Random() % 100 <= percentChance && gBattleCommunication[MOVE_EFFECT_BYTE] != 0 && MOVE_HAD_EFFECT)",
            "replacement": (
                "else if (VegaMoveEffectCanRollSecondaryOnce(gCurrentMove, gBattleCommunication[MOVE_EFFECT_BYTE])\n"
                "\t\t&& Random() % 100 < percentChance && gBattleCommunication[MOVE_EFFECT_BYTE] != 0 && MOVE_HAD_EFFECT)"
            ),
            "expected_count": 1,
            "consumers": [
                "multi-hit resolver redispatch",
                "move 427 single user-boost roll",
                "exact 0..99 secondary-effect percentage boundary",
            ],
        },
        {
            "id": "fixed-trap-duration",
            "path": "src/set_effect.c",
            "needle": "gBattleMons[gEffectBank].status2 |= ((Random() & 1) + 4) << 0xD;",
            "replacement": "gBattleMons[gEffectBank].status2 |= VegaMoveEffectTrapTurns(gCurrentMove, (Random() & 1) + 4) << 0xD;",
            "expected_count": 1,
            "consumers": ["three-turn and four-to-five-turn trap"],
        },
    ])
    return patches


def apply_required_native_patches(
    source_files: Mapping[str, str],
    bundle: Mapping[str, Any],
) -> dict[str, str]:
    """Purely apply the bundle's exact-count patches to CFRU source strings."""

    raw_patches = bundle.get("required_patches")
    if not isinstance(raw_patches, list):
        _fail("lowering bundle required_patches missing")
    output = dict(source_files)
    for raw_patch in raw_patches:
        if not isinstance(raw_patch, Mapping):
            _fail("native patch entry must be an object")
        patch_id = raw_patch.get("id")
        path = raw_patch.get("path")
        needle = raw_patch.get("needle")
        replacement = raw_patch.get("replacement")
        expected = raw_patch.get("expected_count")
        if (
            not isinstance(patch_id, str) or not patch_id
            or not isinstance(path, str) or not path
            or not isinstance(needle, str) or not needle
            or not isinstance(replacement, str) or not replacement
            or not isinstance(expected, int) or isinstance(expected, bool) or expected <= 0
        ):
            _fail("malformed native patch contract")
        source = output.get(path)
        if not isinstance(source, str):
            _fail(f"native patch source missing: {path}")
        count = source.count(needle)
        if count != expected:
            _fail(f"native patch {patch_id} expected {expected} match(es), got {count}")
        output[path] = source.replace(needle, replacement)
    return output


def lower_t04_move_effects(move_model: Mapping[str, Any]) -> dict[str, Any]:
    """Lower all 70 frozen T04 adapters into native CFRU sources/contracts.

    Returned source paths are logical paths inside a prepared CFRU tree.  The
    caller owns filesystem writes and exact patch application.
    """

    rows = _extract_rows(move_model)
    bindings: list[dict[str, Any]] = []
    for move_id, _row, operations in rows:
        commands, runtime_effect = _compile_commands(move_id, operations)
        if runtime_effect not in RUNTIME_EFFECT_SYMBOLS:
            _fail(f"move {move_id}: runtime EFFECT id {runtime_effect} is outside fixed CFRU namespace")
        executable_commands = [command for command in commands if not command.endswith(":")]
        size = _script_size(executable_commands)
        if size > MAX_SCRIPT_BYTES or len(executable_commands) > MAX_SCRIPT_COMMANDS:
            _fail(
                f"move {move_id}: generated script exceeds bound: "
                f"bytes={size}, commands={len(executable_commands)}"
            )
        binding = {
            "move_id": move_id,
            "script_symbol": f"VegaMoveEffectScript_{move_id}",
            "operations": list(operations),
            "runtime_effect_id": runtime_effect,
            "runtime_effect_symbol": RUNTIME_EFFECT_SYMBOLS[runtime_effect],
            "fixed_hit_count": 2 if "HIT_EXACTLY_2" in operations else 3 if "HIT_EXACTLY_3" in operations else 0,
            "recoil_denominator": 3 if "RECOIL_ONE_THIRD" in operations else 0,
            "critical_stage": 2 if "CRITICAL_STAGE_UP_2" in operations else 1 if "CRITICAL_STAGE_UP_1" in operations else 0,
            "semantic_flags": _descriptor_flags(operations),
            "field_operations": [op for op in operations if op in FIELD_OPERATIONS],
            "query_operations": [op for op in operations if op in QUERY_OPERATIONS],
            "script_commands": commands,
            "disassembly_contract": {
                "opcodes": [_command_opcode(command) for command in executable_commands],
                "maximum_bytes": size,
                "maximum_commands": len(executable_commands),
            },
        }
        bindings.append(binding)

    asm_source = _render_asm(bindings)
    c_source = _render_c(bindings)
    header_source = _render_header()

    # Numeric ROM addresses in these sources would bypass the symbol/linker
    # contract.  0x0 is allowed for macro arguments; any 0x08/0x09 address is not.
    combined = asm_source + c_source + header_source
    if re.search(r"\b0x0[89][0-9A-Fa-f]{6}\b", combined):
        _fail("generated native adapters contain a numeric ROM pointer")
    if "jumpifability" in asm_source:
        _fail("generated adapter copied an ABI-sensitive jumpifability command")

    patches = _required_patches()
    table_memberships = {
        "gSoundMoves": [
            binding["move_id"] for binding in bindings
            if "SOUND_MOVE" in binding["operations"]
        ],
        "gPercent33RecoilMoves": [
            binding["move_id"] for binding in bindings
            if binding["recoil_denominator"] == 3
        ],
        "gTwoStrikesMoves": [
            binding["move_id"] for binding in bindings
            if binding["fixed_hit_count"] == 2
        ],
    }
    for binding in bindings:
        binding["table_memberships"] = [
            table for table, move_ids in table_memberships.items()
            if binding["move_id"] in move_ids
        ]
    return {
        "schema": "cfru-vega-move-effect-lowering/v1",
        "adapter_count": len(bindings),
        "operation_count": len(EXPECTED_OPERATIONS),
        "bindings": bindings,
        "runtime_effect_overrides": {
            binding["move_id"]: binding["runtime_effect_id"] for binding in bindings
        },
        "runtime_effect_symbols": dict(sorted(RUNTIME_EFFECT_SYMBOLS.items())),
        # These are semantic memberships materialized by the central-query
        # patches above.  Do not also append them to the fixed tables: keeping
        # one generated query boundary avoids duplicate/hand-maintained rows.
        "native_table_memberships": {
            table: {"move_ids": move_ids, "materialization": "central_query"}
            for table, move_ids in table_memberships.items()
        },
        "sources": {
            "assembly/battle_scripts/vega_move_effect_adapters.s": asm_source,
            "src/vega_move_effect_adapters.c": c_source,
            "include/new/vega_move_effect_adapters.h": header_source,
        },
        "required_header": "include/new/vega_move_effect_adapters.h",
        "required_patches": patches,
        "bounds": {
            "maximum_script_bytes": MAX_SCRIPT_BYTES,
            "maximum_script_commands": MAX_SCRIPT_COMMANDS,
            "maximum_adapter_count": 70,
            "patch_count": len(patches),
        },
    }


def validate_linked_adapter_disassembly(
    image: bytes,
    symbol_ranges: Mapping[str, tuple[int, int]],
    forbidden_vega_pointers: Sequence[int] = (),
    expected_commands: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, int]:
    """Validate bounded linked script spans without trusting a text report.

    ``symbol_ranges`` uses half-open file offsets.  The function is intentionally
    decoder-independent; the generator's opcode sequence is the disassembly
    contract, while this gate proves symbol cardinality/bounds and absence of
    every frozen legacy script pointer in the actual linked bytes.
    """

    expected_symbols = {f"VegaMoveEffectScript_{move}" for move in EXPECTED_MOVE_PLANS}
    if set(symbol_ranges) != expected_symbols:
        _fail("linked adapter symbol set does not match the 70-plan contract")
    total = 0
    if expected_commands is not None and set(expected_commands) != expected_symbols:
        _fail("linked adapter command contract does not match the 70-plan symbols")

    pointer_commands = {"accuracycheck", "call", "callasm", "goto", "jumpifweather"}
    opcode_bytes = {
        "attackcanceler": 0x00,
        "accuracycheck": 0x01,
        "attackstring": 0x02,
        "ppreduce": 0x03,
        "attackanimation": 0x09,
        "waitanimation": 0x0A,
        "seteffectwithchancetarget": 0x15,
        "setmoveeffect": 0x2E,
        "goto": 0x28,
        "jumpifweather": 0x2A,
        "call": 0x41,
        "callasm": 0xF8,
    }
    decoded_command_count = 0
    for symbol, bounds in symbol_ranges.items():
        if (
            not isinstance(bounds, tuple) or len(bounds) != 2
            or not all(isinstance(value, int) and not isinstance(value, bool) for value in bounds)
        ):
            _fail(f"{symbol}: invalid linked range")
        start, end = bounds
        if start < 0 or end <= start or end > len(image):
            _fail(f"{symbol}: linked range outside image")
        size = end - start
        if size > MAX_SCRIPT_BYTES:
            _fail(f"{symbol}: linked script exceeds {MAX_SCRIPT_BYTES} bytes")
        span = image[start:end]
        if expected_commands is not None:
            commands = [command for command in expected_commands[symbol] if not command.endswith(":")]
            cursor = 0
            for command in commands:
                opcode = _command_opcode(command)
                if opcode not in opcode_bytes or opcode not in _COMMAND_SIZE:
                    _fail(f"{symbol}: unsupported linked opcode contract: {opcode}")
                width = _COMMAND_SIZE[opcode]
                if cursor + width > len(span) or span[cursor] != opcode_bytes[opcode]:
                    actual = span[cursor] if cursor < len(span) else None
                    _fail(
                        f"{symbol}: linked opcode/width mismatch at {cursor}: "
                        f"{actual!r} != {opcode_bytes[opcode]:#x}"
                    )
                if opcode in pointer_commands:
                    # jumpifweather is opcode,u8 predicate,u32 flags,u16 mask,
                    # u32 target.  Its linked control pointer starts at +8.
                    pointer_offset = cursor + (8 if opcode == "jumpifweather" else 1)
                    target = int.from_bytes(span[pointer_offset:pointer_offset + 4], "little")
                    if not 0x08000000 <= target < 0x0A000000:
                        _fail(f"{symbol}: linked control target outside ROM: {target:#x}")
                cursor += width
                decoded_command_count += 1
            if cursor != len(span):
                _fail(f"{symbol}: linked script has {len(span) - cursor} unclassified byte(s)")
        for pointer in forbidden_vega_pointers:
            if not isinstance(pointer, int) or isinstance(pointer, bool) or pointer < 0 or pointer > 0xFFFFFFFF:
                _fail("forbidden Vega pointer must be a u32")
            if pointer.to_bytes(4, "little") in span:
                _fail(f"{symbol}: legacy Vega script pointer survived linking")
        total += size
    return {
        "symbol_count": len(symbol_ranges),
        "total_bytes": total,
        "maximum_bytes": MAX_SCRIPT_BYTES,
        "decoded_command_count": decoded_command_count,
    }


__all__ = [
    "EXPECTED_MOVE_PLANS",
    "EXPECTED_OPERATIONS",
    "MAX_SCRIPT_BYTES",
    "MAX_SCRIPT_COMMANDS",
    "RUNTIME_EFFECT_SYMBOLS",
    "MoveEffectLoweringError",
    "apply_required_native_patches",
    "lower_t04_move_effects",
    "validate_linked_adapter_disassembly",
]
