#!/usr/bin/env python3
"""固定CFRU-JPのBattle Factory battle-side資産をVega向けに描画する。

固定sourceの非 ``UNBOUND`` 分岐には、有効なrental spreadが1件もなく、
special/multi trainer配列も空のまま残る。このmoduleは次の境界だけを担当する。

* ``frontier.c`` の既知の配列外参照とbattle style上限をexact patchする。
* 非 ``UNBOUND`` fallbackを、既存Vega Species IDだけを使う決定的fixtureへ置換する。
* T04 move model、T05 item model、T02 Vega base-stat行契約をfail-closedに照合する。
* single/double/NPC multiとT06の8 ruleのdispatchをmanifestへ固定する。

APIはsourceを読み取って文字列を返すだけで、sandboxや正本へ書き込まない。
親builderは ``build_facility_runtime`` の ``render()`` をsource sandboxへ配置する。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


EXPECTED_CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"
EXPECTED_CFRU_TREE = "f4424af017abd01afe2d2deb833fb67275f03804"
VEGA_SPECIES_COUNT = 412
MOVE_COUNT = 1063
ITEM_COUNT = 999
ABILITY_COUNT = 312

FRONTIER_SOURCE = "src/frontier.c"
BUILD_SOURCE = "src/build_pokemon.c"
SPREAD_SOURCE = "src/Tables/battle_tower_spreads.h"
TRAINER_SOURCE = "src/Tables/battle_frontier_trainers.c"
RAID_PARTNER_SOURCE = "src/Tables/raid_partners.h"

EXPECTED_SOURCE_HASHES: Mapping[str, str] = {
    FRONTIER_SOURCE: "a33395bfaf81eec041a423d44d5620908e587a4f6e5614780b4bde393d7f4e06",
    BUILD_SOURCE: "ac81e3a9a8c7a58105573e6ee2abf62a4b22922e88c6c7d3a1ecdc6c9431e824",
    SPREAD_SOURCE: "c52eced597a03b3fc9afd794e95832467ba6a7df79ed98dea445ee28b35f0824",
    TRAINER_SOURCE: "39c3a7adac454fdaa1694b3bf273e79c0c97580e7bdad89f63b510132b29861c",
    RAID_PARTNER_SOURCE: "df77eba3cc6793bb34b638bffb989f6a3920fccca163ef1e82542a5005f579eb",
}

DEFAULT_SPECIES_IDS = (
    1, 2, 4, 7, 25, 39, 52, 63, 66, 74, 81, 92, 133,
    8, 14, 17, 75, 37, 38,
)
MONOTYPE_WITNESS_TYPE = 12
MONOTYPE_WITNESS_SPECIES = (1, 2, 37, 38, 66, 74)


class CFRUFacilityRuntimeError(ValueError):
    """固定source、canonical model、または施設data契約が一致しない。"""


def _fail(message: str) -> NoReturn:
    raise CFRUFacilityRuntimeError(message)


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


def _integer(value: object, label: str, lower: int, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
        _fail(f"{label} は {lower}..{upper} の整数である必要がある")
    return value


def _rows(value: object, label: str, count: int) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)) or len(value) != count:
        _fail(f"{label} は正確に {count} 行必要")
    output: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            _fail(f"{label}[{index}] はobjectである必要がある")
        output.append(row)
    return tuple(output)


@dataclass(frozen=True)
class FacilitySpreadSpec:
    """生成するBattleTowerSpreadのcanonical入力。"""

    key: str
    species_id: int
    move_ids: tuple[int, int, int, int]
    nature: int
    evs: tuple[int, int, int, int, int, int]
    item_id: int = 0
    ability_slot: int = 0
    for_singles: bool = True
    for_doubles: bool = True


@dataclass(frozen=True)
class FacilityRuntimeBundle:
    """filesystemへ書き込まない施設source bundle。"""

    _sources: tuple[tuple[str, str], ...]
    _manifest_json: str

    def render(self) -> dict[str, str]:
        return dict(self._sources)

    def manifest(self) -> dict[str, object]:
        value = json.loads(self._manifest_json)
        if not isinstance(value, dict):  # pragma: no cover - constructor内部契約
            raise AssertionError("facility manifest must be an object")
        return value


def make_vega_species_model(count: int = VEGA_SPECIES_COUNT) -> dict[str, object]:
    """T02で固定したVega base-stat行をcanonical Species ID modelへする。"""

    if isinstance(count, bool) or count != VEGA_SPECIES_COUNT:
        _fail(f"Vega Species行数は固定値 {VEGA_SPECIES_COUNT} である必要がある")
    return {
        "schema_version": 1,
        "source": "T02_VEGA_BASE_STATS",
        "count": count,
        "ids": list(range(count)),
    }


def default_facility_spreads() -> tuple[FacilitySpreadSpec, ...]:
    """Vega既存IDだけで構成した決定的なLv.50 rental入力を返す。"""

    # hp, atk, def, speed, sp.atk, sp.def。各rowは合計508以下。
    return (
        FacilitySpreadSpec("VEGA_RENTAL_001", 1, (202, 188, 73, 182), 5, (252, 0, 132, 4, 120, 0), ability_slot=1),
        FacilitySpreadSpec("VEGA_RENTAL_002", 2, (202, 188, 73, 182), 5, (252, 0, 132, 4, 120, 0), ability_slot=1),
        FacilitySpreadSpec("VEGA_RENTAL_004", 4, (53, 126, 332, 182), 10, (4, 0, 0, 252, 252, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_007", 7, (55, 58, 352, 182), 20, (252, 0, 128, 0, 0, 128)),
        FacilitySpreadSpec("VEGA_RENTAL_025", 25, (85, 98, 86, 182), 10, (4, 0, 0, 252, 252, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_039", 39, (129, 113, 156, 182), 5, (252, 0, 128, 0, 0, 128)),
        FacilitySpreadSpec("VEGA_RENTAL_052", 52, (1, 242, 269, 182), 13, (4, 252, 0, 252, 0, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_063", 63, (94, 347, 115, 182), 10, (4, 0, 0, 252, 252, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_066", 66, (280, 339, 89, 182), 3, (4, 252, 0, 252, 0, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_074", 74, (89, 317, 33, 182), 3, (252, 252, 0, 4, 0, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_081", 81, (85, 129, 113, 182), 15, (4, 0, 0, 252, 252, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_092", 92, (247, 92, 109, 182), 10, (4, 0, 0, 252, 252, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_133", 133, (98, 263, 213, 182), 13, (4, 252, 0, 252, 0, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_008", 8, (55, 58, 352, 182), 20, (252, 0, 128, 0, 0, 128)),
        FacilitySpreadSpec("VEGA_RENTAL_014", 14, (242, 53, 126, 182), 10, (4, 0, 0, 252, 252, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_017", 17, (210, 332, 98, 182), 13, (4, 252, 0, 252, 0, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_075", 75, (129, 113, 156, 182), 5, (252, 0, 128, 0, 0, 128)),
        FacilitySpreadSpec("VEGA_RENTAL_037", 37, (202, 188, 73, 182), 5, (252, 0, 132, 4, 120, 0)),
        FacilitySpreadSpec("VEGA_RENTAL_038", 38, (202, 188, 73, 182), 5, (252, 0, 132, 4, 120, 0)),
    )


FORMAT_DISPATCH: tuple[dict[str, object], ...] = (
    {
        "key": "SINGLE_3V3",
        "battle_type": 0,
        "battle_type_symbol": "BATTLE_FACILITY_SINGLE",
        "random_battle_type": 4,
        "random_battle_type_symbol": "BATTLE_FACILITY_SINGLE_RANDOM",
        "party_size": 3,
        "npc_partner": False,
    },
    {
        "key": "DOUBLE_4V4",
        "battle_type": 1,
        "battle_type_symbol": "BATTLE_FACILITY_DOUBLE",
        "random_battle_type": 5,
        "random_battle_type_symbol": "BATTLE_FACILITY_DOUBLE_RANDOM",
        "party_size": 4,
        "npc_partner": False,
    },
    {
        "key": "NPC_PARTNER_MULTI",
        "battle_type": 2,
        "battle_type_symbol": "BATTLE_FACILITY_MULTI",
        "random_battle_type": 6,
        "random_battle_type_symbol": "BATTLE_FACILITY_MULTI_RANDOM",
        "party_size": 4,
        "npc_partner": True,
    },
)

RULE_DISPATCH: tuple[dict[str, object], ...] = tuple(
    {
        "key": key,
        "tier": tier,
        "tier_symbol": symbol,
        "random_format": key == "RANDOM",
    }
    for key, tier, symbol in (
        ("RANDOM", 0, "BATTLE_FACILITY_STANDARD"),
        ("LITTLE", 4, "BATTLE_FACILITY_LITTLE_CUP"),
        ("MONOTYPE", 6, "BATTLE_FACILITY_MONOTYPE"),
        ("UNRESTRICTED", 1, "BATTLE_FACILITY_NO_RESTRICTIONS"),
        ("OU", 2, "BATTLE_FACILITY_OU"),
        ("UBER", 3, "BATTLE_FACILITY_UBER"),
        ("CAMOMONS", 7, "BATTLE_FACILITY_CAMOMONS"),
        ("GS", 5, "BATTLE_FACILITY_GS_CUP"),
    )
)


_ELIGIBILITY_OLD = (
    "\t\tfor (j = 0, tier = tiers[j]; j < numTiers; ++j, tier = tiers[j]) "
    "//Check every tier in requested format\n\t\t{"
)
_ELIGIBILITY_NEW = (
    "\t\tfor (j = 0; j < numTiers; ++j) //Check every tier in requested format\n"
    "\t\t{\n\t\t\ttier = tiers[j];"
)
_STYLE_CLAMP_OLD = "\t*battleStyle = MathMin(*battleStyle, NUM_TOWER_BATTLE_TYPES);"
_STYLE_CLAMP_NEW = "\t*battleStyle = MathMin(*battleStyle, NUM_TOWER_BATTLE_TYPES - 1);"
_RETRY_DECL_OLD = "\t\tbool8 loop = TRUE;\n\t\tu16 species, dexNum, item;"
_RETRY_DECL_NEW = (
    "\t\tbool8 loop = TRUE;\n"
    "\t\tu32 vegaFacilityAttempts = 0;\n"
    "\t\tu16 species, dexNum, item;"
)
_RETRY_LOOP_OLD = "\t\tdo\n\t\t{\n\t\t\tswitch (trainerId) {"
_RETRY_LOOP_NEW = (
    "\t\tdo\n\t\t{\n"
    "\t\t\tif (++vegaFacilityAttempts > 4096)\n"
    "\t\t\t{\n"
    "\t\t\t\tFree(builder);\n"
    "\t\t\t\treturn 0;\n"
    "\t\t\t}\n"
    "\t\t\tif (tier == BATTLE_FACILITY_MONOTYPE)\n"
    "\t\t\t{\n"
    "\t\t\t\tspread = &gVegaMonotypeSpreads[Random() % ARRAY_COUNT(gVegaMonotypeSpreads)];\n"
    "\t\t\t\tgoto VEGA_FACILITY_SPREAD_SELECTED;\n"
    "\t\t\t}\n"
    "\t\t\tswitch (trainerId) {"
)
_SPREAD_SELECTED_OLD = "\n\t\t\tspecies = spread->species;"
_SPREAD_SELECTED_NEW = (
    "\n\t\tVEGA_FACILITY_SPREAD_SELECTED:\n"
    "\t\t\tspecies = spread->species;"
)

_RENTAL_ACCEPT_OLD = """\t\t\tif (!IsPokemonBannedBasedOnStreak(species, item, builder->speciesArray, monsCount, trainerId, tier, forPlayer)
\t\t\t&& (!builder->speciesOnTeam[dexNum] || tier == BATTLE_FACILITY_NO_RESTRICTIONS)
\t\t\t&& (!ItemAlreadyOnTeam(item, monsCount, builder->itemArray) || tier == BATTLE_FACILITY_NO_RESTRICTIONS)
\t\t\t&& (tier == BATTLE_FACILITY_MEGA_BRAWL || itemEffect != ITEM_EFFECT_MEGA_STONE || item == ITEM_ULTRANECROZIUM_Z || !builder->itemEffectOnTeam[ITEM_EFFECT_MEGA_STONE])
\t\t\t&& ((itemEffect != ITEM_EFFECT_Z_CRYSTAL && item != ITEM_ULTRANECROZIUM_Z) || !builder->itemEffectOnTeam[ITEM_EFFECT_Z_CRYSTAL])
\t\t\t&& !PokemonTierBan(species, item, spread, NULL, tier, CHECK_BATTLE_TOWER_SPREADS)
\t\t\t&& !(tier == BATTLE_FACILITY_MONOTYPE && TeamNotAllSameType(species, item, monsCount, builder->speciesArray, builder->itemArray))
\t\t\t&& !(tier == BATTLE_FACILITY_GS_CUP && !IsFrontierSingles(battleType) && TooManyLegendariesOnGSCupTeam(species, monsCount, builder->speciesArray))
\t\t\t&& !((trainerId == BATTLE_TOWER_TID || forPlayer || (trainerId == BATTLE_FACILITY_MULTI_TRAINER_TID && IsRandomBattleTowerBattle())) && TeamDoesntHaveSynergy(spread, builder, forPlayer)))
\t\t\t{
\t\t\t\tloop = FALSE;
\t\t\t}"""
_RENTAL_ACCEPT_NEW = _RENTAL_ACCEPT_OLD.replace(
    "&& !PokemonTierBan(species, item, spread, NULL, tier, CHECK_BATTLE_TOWER_SPREADS)",
    "&& (VegaFacilitySpreadIsCurated(spread) || !PokemonTierBan(species, item, spread, NULL, tier, CHECK_BATTLE_TOWER_SPREADS))",
)

_SPREAD_FALLBACK_START = "\n#else\n\nconst struct BattleTowerSpread gFrontierSpreads[] ="
_SPREAD_FALLBACK_END = "\n#endif\n\nconst u16 gNumFrontierSpreads = ARRAY_COUNT(gFrontierSpreads);"
_TRAINER_FALLBACK_START = "\n#else\n\tconst struct BattleTowerTrainer gTowerTrainers[] ="
_TRAINER_FALLBACK_END = "\n#endif\n\nconst u16 gNumTowerTrainers = NELEMS(gTowerTrainers);"


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        _fail(f"{label} exact anchor数が1ではない: {count}")
    return text.replace(old, new, 1)


def patch_frontier_safety(source: str, *, verify_fixed_hash: bool = True) -> str:
    """frontier.cの2件の既知hazardをexact patchする。"""

    if not isinstance(source, str):
        _fail("frontier.c sourceは文字列である必要がある")
    actual = _sha256(source.encode("utf-8"))
    expected = EXPECTED_SOURCE_HASHES[FRONTIER_SOURCE]
    if verify_fixed_hash and actual != expected:
        _fail(f"{FRONTIER_SOURCE} SHA-256不一致: {actual} != {expected}")
    patched = _replace_once(source, _ELIGIBILITY_OLD, _ELIGIBILITY_NEW, "eligibility loop")
    return _replace_once(patched, _STYLE_CLAMP_OLD, _STYLE_CLAMP_NEW, "battleStyle clamp")


def patch_builder_safety(source: str, *, verify_fixed_hash: bool = True) -> str:
    """BuildFrontierPartyの再抽選を4096回でfail-closed終了させる。"""

    if not isinstance(source, str):
        _fail("build_pokemon.c sourceは文字列である必要がある")
    actual = _sha256(source.encode("utf-8"))
    expected = EXPECTED_SOURCE_HASHES[BUILD_SOURCE]
    if verify_fixed_hash and actual != expected:
        _fail(f"{BUILD_SOURCE} SHA-256不一致: {actual} != {expected}")
    patched = _replace_once(source, _RETRY_DECL_OLD, _RETRY_DECL_NEW, "rental retry counter")
    patched = _replace_once(patched, _RETRY_LOOP_OLD, _RETRY_LOOP_NEW, "rental retry guard")
    patched = _replace_once(
        patched,
        _SPREAD_SELECTED_OLD,
        _SPREAD_SELECTED_NEW,
        "dedicated monotype pool selection",
    )
    return _replace_once(
        patched, _RENTAL_ACCEPT_OLD, _RENTAL_ACCEPT_NEW, "rental rejection classifier"
    )


def _replace_fallback(
    source: str, start_marker: str, end_marker: str, replacement: str, label: str
) -> str:
    if source.count(start_marker) != 1 or source.count(end_marker) != 1:
        _fail(f"{label} fallback境界が固定sourceと一致しない")
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    if end <= start:
        _fail(f"{label} fallback境界順が不正")
    return source[:start] + "\n" + replacement.rstrip("\n") + source[end:]


def _validate_models(
    move_model: Mapping[str, Any],
    id_model: Mapping[str, Any],
    species_model: Mapping[str, Any],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    frozenset[int],
]:
    if move_model.get("schema_version") != 1 or move_model.get("task") != "T04":
        _fail("T04 move model schema/task不一致")
    moves = _rows(move_model.get("moves"), "T04.moves", MOVE_COUNT)
    if [row.get("id") for row in moves] != list(range(MOVE_COUNT)):
        _fail("T04 move IDは0..1062の連続canonical行である必要がある")
    if any(not isinstance(row.get("move_key"), str) or not row.get("move_key") for row in moves):
        _fail("T04 move_keyが欠落している")

    if id_model.get("schema_version") != 1 or id_model.get("task") != "T05":
        _fail("T05 ID model schema/task不一致")
    items = _rows(id_model.get("items"), "T05.items", ITEM_COUNT)
    if [row.get("id") for row in items] != list(range(ITEM_COUNT)):
        _fail("T05 item IDは0..998の連続canonical行である必要がある")
    abilities = _rows(id_model.get("abilities"), "T05.abilities", ABILITY_COUNT)
    if [row.get("id") for row in abilities] != list(range(ABILITY_COUNT)):
        _fail("T05 ability IDは0..311の連続canonical行である必要がある")
    if items[0].get("item_key") != "ITEM_KEY_NONE" or items[0].get("vega_id") != 0:
        _fail("T05 ITEM_NONE stable ABI不一致")

    if (
        species_model.get("schema_version") != 1
        or species_model.get("source") != "T02_VEGA_BASE_STATS"
        or species_model.get("count") != VEGA_SPECIES_COUNT
    ):
        _fail("T02 Vega Species model schema/source/count不一致")
    ids = species_model.get("ids")
    if not isinstance(ids, (list, tuple)) or list(ids) != list(range(VEGA_SPECIES_COUNT)):
        _fail("Vega Species stable IDは0..411の連続行である必要がある")
    return moves, items, frozenset(ids)


def _validate_spreads(
    spreads: Sequence[FacilitySpreadSpec],
    moves: Sequence[Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
    species_ids: frozenset[int],
) -> tuple[FacilitySpreadSpec, ...]:
    if not isinstance(spreads, (list, tuple)) or len(spreads) < 12:
        _fail("facility rental spreadはsingle/double/multi用に最低12件必要")
    output: list[FacilitySpreadSpec] = []
    keys: set[str] = set()
    for index, spread in enumerate(spreads):
        if not isinstance(spread, FacilitySpreadSpec):
            _fail(f"spreads[{index}] はFacilitySpreadSpecである必要がある")
        if not spread.key.startswith("VEGA_RENTAL_") or spread.key in keys:
            _fail(f"spreads[{index}].keyが未知または重複: {spread.key!r}")
        keys.add(spread.key)
        species_id = _integer(spread.species_id, f"{spread.key}.species_id", 1, 0xFFFF)
        if species_id not in species_ids:
            _fail(f"{spread.key}.species_id {species_id} はVega stable ID範囲外")
        if len(spread.move_ids) != 4:
            _fail(f"{spread.key}.move_idsは4件必要")
        for slot, move_id in enumerate(spread.move_ids):
            move_id = _integer(move_id, f"{spread.key}.move_ids[{slot}]", 1, 0xFFFF)
            if move_id >= len(moves) or moves[move_id].get("id") != move_id:
                _fail(f"{spread.key}.move_ids[{slot}] {move_id} はT04 canonical範囲外")
        item_id = _integer(spread.item_id, f"{spread.key}.item_id", 0, 0xFFFF)
        if item_id >= len(items) or items[item_id].get("id") != item_id:
            _fail(f"{spread.key}.item_id {item_id} はT05 canonical範囲外")
        _integer(spread.nature, f"{spread.key}.nature", 0, 24)
        _integer(spread.ability_slot, f"{spread.key}.ability_slot", 0, 2)
        if len(spread.evs) != 6:
            _fail(f"{spread.key}.evsは6件必要")
        ev_total = sum(
            _integer(value, f"{spread.key}.evs[{slot}]", 0, 252)
            for slot, value in enumerate(spread.evs)
        )
        if ev_total > 510:
            _fail(f"{spread.key}.EV合計 {ev_total} は510超過")
        if not isinstance(spread.for_singles, bool) or not isinstance(spread.for_doubles, bool):
            _fail(f"{spread.key}.format flagsはboolである必要がある")
        if not (spread.for_singles or spread.for_doubles):
            _fail(f"{spread.key} はsingle/doubleの少なくとも一方が必要")
        output.append(spread)
    species = {spread.species_id for spread in output}
    if not set(MONOTYPE_WITNESS_SPECIES) <= species:
        _fail(
            "MONOTYPE double/multiには同一typeのunique Species witness 4件が必要"
        )
    return tuple(output)


def _render_spread(spread: FacilitySpreadSpec) -> str:
    hp, atk, defense, speed, sp_atk, sp_def = spread.evs
    move_lines = ",\n".join(f"\t\t\t{move}" for move in spread.move_ids)
    return f"""\t{{
\t\t/* {spread.key}: Vega stable Species {spread.species_id}. */
\t\t.species = {spread.species_id},
\t\t.nature = {spread.nature},
\t\t.hpIv = 31,
\t\t.atkIv = 31,
\t\t.defIv = 31,
\t\t.spdIv = 31,
\t\t.spAtkIv = 31,
\t\t.spDefIv = 31,
\t\t.hpEv = {hp},
\t\t.atkEv = {atk},
\t\t.defEv = {defense},
\t\t.spdEv = {speed},
\t\t.spAtkEv = {sp_atk},
\t\t.spDefEv = {sp_def},
\t\t.ability = {spread.ability_slot},
\t\t.item = {spread.item_id},
\t\t.moves =
\t\t{{
{move_lines},
\t\t}},
\t\t.ball = BALL_TYPE_RANDOM,
\t\t.forSingles = {"TRUE" if spread.for_singles else "FALSE"},
\t\t.forDoubles = {"TRUE" if spread.for_doubles else "FALSE"},
\t\t.modifyMovesDoubles = FALSE,
\t}},"""


def _render_spread_array(name: str, spreads: Sequence[FacilitySpreadSpec]) -> str:
    body = "\n".join(_render_spread(spread) for spread in spreads)
    return f"const struct BattleTowerSpread {name}[] =\n{{\n{body}\n}};"


def _render_spread_fallback(spreads: Sequence[FacilitySpreadSpec]) -> tuple[str, dict[str, int]]:
    selections: tuple[tuple[str, tuple[int, ...]], ...] = (
        ("gFrontierSpreads", tuple(range(len(spreads)))),
        ("gVegaMonotypeSpreads", (0, 1, 17, 18, 8, 9)),
        ("gMiddleCupSpreads", (1, 13, 14, 15, 4, 16)),
        ("gLittleCupSpreads", (0, 2, 3, 7, 11, 12)),
        ("gFrontierLegendarySpreads", (3, 6, 8, 10, 11)),
        ("gArceusSpreads", (0,)),
        ("gPikachuSpreads", (3,)),
        ("gWormadamSpreads", (4,)),
        ("gRotomSpreads", (9,)),
        ("gOricorioSpreads", (10,)),
    )
    arrays = [
        _render_spread_array(name, tuple(spreads[index] for index in indices))
        for name, indices in selections
    ]
    rendered = "#else\n\n/* T06: deterministic Vega-safe non-UNBOUND rental pools. */\n\n"
    rendered += "\n\n".join(arrays)
    range_checks = "\n\t\t|| ".join(
        f"(value >= (u32){name} && value < (u32)({name} + ARRAY_COUNT({name})))"
        for name, _indices in selections
    )
    rendered += f"""

/* Generated pools are the reviewed Vega Species namespace authority. */
static bool8 VegaFacilitySpreadIsCurated(const struct BattleTowerSpread* spread)
{{
\tu32 value = (u32)spread;
\treturn {range_checks};
}}"""
    return rendered, {name: len(indices) for name, indices in selections}


def _trainer_row(text_index: int) -> str:
    return f"""\t{{
\t\t.owNum = EVENT_OBJ_GFX_YOUNGSTER,
\t\t.trainerClass = CLASS_YOUNGSTER,
\t\t.trainerSprite = TRAINER_PIC_YOUNGSTER,
\t\t.gender = BATTLE_FACILITY_MALE,
\t\t.preBattleText = sFrontierText_Youngster_PreBattle_{text_index},
\t\t.playerWinText = sFrontierText_Youngster_PlayerWin_{text_index},
\t\t.playerLoseText = sFrontierText_Youngster_PlayerLose_{text_index},
\t}},"""


def _special_trainer_array(
    name: str, text_index: int, spread_counts: Mapping[str, int]
) -> str:
    return f"""const struct SpecialBattleFrontierTrainer {name}[] =
{{
\t{{
\t\t.owNum = EVENT_OBJ_GFX_YOUNGSTER,
\t\t.trainerClass = CLASS_YOUNGSTER,
\t\t.trainerSprite = TRAINER_PIC_YOUNGSTER,
\t\t.gender = BATTLE_FACILITY_MALE,
\t\t.isMonotype = TRUE,
\t\t.name = sTrainerName_Red,
\t\t.preBattleText = sFrontierText_Youngster_PreBattle_{text_index},
\t\t.playerWinText = sFrontierText_Youngster_PlayerWin_{text_index},
\t\t.playerLoseText = sFrontierText_Youngster_PlayerLose_{text_index},
\t\t.regularSpreads = gFrontierSpreads,
\t\t.middleCupSpreads = gMiddleCupSpreads,
\t\t.littleCupSpreads = gLittleCupSpreads,
\t\t.legendarySpreads = gFrontierLegendarySpreads,
\t\t.regSpreadSize = {spread_counts["gFrontierSpreads"]},
\t\t.mcSpreadSize = {spread_counts["gMiddleCupSpreads"]},
\t\t.lcSpreadSize = {spread_counts["gLittleCupSpreads"]},
\t\t.legSpreadSize = {spread_counts["gFrontierLegendarySpreads"]},
\t\t.songId = 0,
\t}},
}};"""


def _multi_trainer_row(
    text_index: int, ot_id: int, spread_counts: Mapping[str, int]
) -> str:
    return f"""\t{{
\t\t.owNum = EVENT_OBJ_GFX_RIVAL,
\t\t.trainerClass = CLASS_RIVAL,
\t\t.backSpriteId = TRAINER_BACK_PIC_RED,
\t\t.gender = BATTLE_FACILITY_MALE,
\t\t.name = sTrainerName_Red,
\t\t.otId = 0x{ot_id:08X},
\t\t.regularSpreads = gFrontierSpreads,
\t\t.legendarySpreads = gFrontierLegendarySpreads,
\t\t.littleCupSpreads = gLittleCupSpreads,
\t\t.regSpreadSize = {spread_counts["gFrontierSpreads"]},
\t\t.legSpreadSize = {spread_counts["gFrontierLegendarySpreads"]},
\t\t.lcSpreadSize = {spread_counts["gLittleCupSpreads"]},
\t}},"""


def _render_trainer_fallback(
    spread_counts: Mapping[str, int]
) -> tuple[str, dict[str, int]]:
    # The pinned minimal profile deliberately leaves UNBOUND disabled.  Only
    # Youngster text set 1 is emitted outside that feature gate; sets 2 and 3
    # are declarations without linked string data in this profile.
    regular = "\n".join(_trainer_row(1) for _ in range(4))
    multi = "\n".join(
        (
            _multi_trainer_row(1, 0x56454741, spread_counts),
            _multi_trainer_row(1, 0x43465255, spread_counts),
        )
    )
    rendered = f"""#else

/* T06: non-empty deterministic trainers for Vega facility fixtures. */
extern const u8 sTrainerName_Red[];
extern const struct BattleTowerSpread gMiddleCupSpreads[];
extern const struct BattleTowerSpread gLittleCupSpreads[];

const struct BattleTowerTrainer gTowerTrainers[] =
{{
{regular}
}};

{_special_trainer_array("gSpecialTowerTrainers", 1, spread_counts)}

{_special_trainer_array("gFrontierBrains", 1, spread_counts)}

const struct MultiBattleTowerTrainer gFrontierMultiBattleTrainers[] =
{{
{multi}
}};

const u8 gNumFrontierMultiTrainers = NELEMS(gFrontierMultiBattleTrainers);"""
    return rendered, {
        "gTowerTrainers": 4,
        "gSpecialTowerTrainers": 1,
        "gFrontierBrains": 1,
        "gFrontierMultiBattleTrainers": 2,
    }


def _render_raid_partners(spreads: Sequence[FacilitySpreadSpec]) -> str:
    """Vega Speciesだけの1 trainer×3 mons raid partner tableを描画する。"""

    selected = tuple(spreads[index] for index in (0, 2, 3))
    partner_spreads = _render_spread_array("sVegaRaidPartnerSpreads", selected)
    return f'''#include "../config.h"

/* T06: Vega stable Species only; all six Raid ranks share one bounded pool. */
{partner_spreads}

extern const u8 sTrainerName_Red[];

const struct MultiRaidTrainer gRaidPartners[] =
{{
\t{{
\t\t.owNum = EVENT_OBJ_GFX_RED_NORMAL,
\t\t.trainerClass = CLASS_PKMN_TRAINER_2,
\t\t.backSpriteId = TRAINER_BACK_PIC_RED,
\t\t.gender = MALE,
\t\t.otId = 0x56454741,
\t\t.name = sTrainerName_Red,
\t\t.spreads =
\t\t{{
\t\t\t[ONE_STAR_RAID ... SIX_STAR_RAID] = sVegaRaidPartnerSpreads,
\t\t}},
\t\t.spreadSizes =
\t\t{{
\t\t\t[ONE_STAR_RAID ... SIX_STAR_RAID] = NELEMS(sVegaRaidPartnerSpreads),
\t\t}},
\t}},
}};

const u8 gNumRaidPartners = NELEMS(gRaidPartners);
'''


def apply_facility_runtime_patches(
    sources: Mapping[str, str],
    move_model: Mapping[str, Any],
    id_model: Mapping[str, Any],
    species_model: Mapping[str, Any],
    *,
    spreads: Sequence[FacilitySpreadSpec] | None = None,
    verify_fixed_hashes: bool = True,
) -> FacilityRuntimeBundle:
    """固定3 sourceのmappingを検証し、patched sourceとmanifestを返す。"""

    if not isinstance(sources, Mapping):
        _fail("sourcesはlogical path→textのmappingである必要がある")
    expected_keys = set(EXPECTED_SOURCE_HASHES)
    actual_keys = set(sources)
    if actual_keys != expected_keys:
        _fail(
            "facility source集合が不一致: "
            f"missing={sorted(expected_keys - actual_keys)} unknown={sorted(actual_keys - expected_keys)}"
        )
    source_hashes: dict[str, str] = {}
    for logical, expected_hash in EXPECTED_SOURCE_HASHES.items():
        source = sources[logical]
        if not isinstance(source, str):
            _fail(f"{logical} はUTF-8 textである必要がある")
        actual_hash = _sha256(source.encode("utf-8"))
        source_hashes[logical] = actual_hash
        if verify_fixed_hashes and actual_hash != expected_hash:
            _fail(f"{logical} SHA-256不一致: {actual_hash} != {expected_hash}")

    moves, items, species_ids = _validate_models(move_model, id_model, species_model)
    validated_spreads = _validate_spreads(
        default_facility_spreads() if spreads is None else spreads,
        moves,
        items,
        species_ids,
    )

    patched_frontier = patch_frontier_safety(
        sources[FRONTIER_SOURCE], verify_fixed_hash=verify_fixed_hashes
    )
    patched_builder = patch_builder_safety(
        sources[BUILD_SOURCE], verify_fixed_hash=verify_fixed_hashes
    )
    spread_fallback, spread_counts = _render_spread_fallback(validated_spreads)
    trainer_fallback, trainer_counts = _render_trainer_fallback(spread_counts)
    patched_spreads = _replace_fallback(
        sources[SPREAD_SOURCE],
        _SPREAD_FALLBACK_START,
        _SPREAD_FALLBACK_END,
        spread_fallback,
        "battle_tower_spreads",
    )
    patched_trainers = _replace_fallback(
        sources[TRAINER_SOURCE],
        _TRAINER_FALLBACK_START,
        _TRAINER_FALLBACK_END,
        trainer_fallback,
        "battle_frontier_trainers",
    )
    rendered = {
        FRONTIER_SOURCE: patched_frontier,
        BUILD_SOURCE: patched_builder,
        SPREAD_SOURCE: patched_spreads,
        TRAINER_SOURCE: patched_trainers,
        RAID_PARTNER_SOURCE: _render_raid_partners(validated_spreads),
    }

    manifest: dict[str, object] = {
        "schema_version": 1,
        "task": "T06",
        "source": {
            "commit": EXPECTED_CFRU_COMMIT,
            "tree": EXPECTED_CFRU_TREE,
            "inputs": dict(sorted(source_hashes.items())),
        },
        "models": {
            "moves": {
                "schema_version": move_model.get("schema_version"),
                "count": len(moves),
                "sha256": _stable_digest(move_model),
            },
            "ids": {
                "schema_version": id_model.get("schema_version"),
                "item_count": len(items),
                "ability_count": len(id_model["abilities"]),
                "sha256": _stable_digest(id_model),
            },
            "species": {
                "schema_version": species_model.get("schema_version"),
                "count": len(species_ids),
                "sha256": _stable_digest(species_model),
            },
        },
        "safety_patches": [
            {"key": "ELIGIBILITY_LOOP_BOUNDED_INDEX", "count": 1},
            {"key": "BATTLE_STYLE_MAX_INDEX", "count": 1},
            {"key": "RENTAL_RETRY_LIMIT_4096", "count": 1},
            {"key": "CURATED_VEGA_SPECIES_TIER_AUTHORITY", "count": 1},
        ],
        "rental": {
            "level": 50,
            "spread_count": len(validated_spreads),
            "species_ids": [spread.species_id for spread in validated_spreads],
            "move_ids": sorted(
                {move for spread in validated_spreads for move in spread.move_ids}
            ),
            "item_ids": sorted({spread.item_id for spread in validated_spreads}),
            "array_counts": spread_counts,
            "monotype_witness": {
                "type_id": MONOTYPE_WITNESS_TYPE,
                "species_ids": list(MONOTYPE_WITNESS_SPECIES),
                "party_size": 6,
            },
        },
        "trainer_counts": trainer_counts,
        "formats": list(FORMAT_DISPATCH),
        "rules": list(RULE_DISPATCH),
        "link_multi_release": False,
        "rendered_sha256": {
            logical: _sha256(text.encode("utf-8"))
            for logical, text in sorted(rendered.items())
        },
    }
    manifest["fingerprint"] = _stable_digest(manifest)
    return FacilityRuntimeBundle(
        tuple(sorted(rendered.items())),
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )


def build_facility_runtime(
    source_root: Path,
    move_model: Mapping[str, Any],
    id_model: Mapping[str, Any],
    species_model: Mapping[str, Any],
    *,
    spreads: Sequence[FacilitySpreadSpec] | None = None,
) -> FacilityRuntimeBundle:
    """固定CFRU rootを読み、書込みなしで施設runtime bundleを構築する。"""

    if not isinstance(source_root, Path) or not source_root.is_dir():
        _fail("source_rootは既存directoryのPathである必要がある")
    resolved_root = source_root.resolve()
    sources: dict[str, str] = {}
    for logical in EXPECTED_SOURCE_HASHES:
        path = (resolved_root / logical).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError:
            _fail(f"source pathがroot外へ逸脱: {logical}")
        if path.is_symlink() or not path.is_file():
            _fail(f"固定facility sourceが欠落または非regular: {logical}")
        try:
            sources[logical] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            _fail(f"{logical} がUTF-8ではない: {error}")
    return apply_facility_runtime_patches(
        sources,
        move_model,
        id_model,
        species_model,
        spreads=spreads,
        verify_fixed_hashes=True,
    )
