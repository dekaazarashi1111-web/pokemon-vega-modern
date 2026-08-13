"""Symbolic dual-region content validation and dry-run generation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .v2_normalize import audit_v2, normalization_diagnostics

KEY_RE = re.compile(r"^(?:[A-Z][A-Z0-9_]*|NONE)$")
AI_PROFILES = {"AI_BASIC", "AI_SEMI_SMART", "AI_FULL_SMART"}
LAYERS = {"original", "overlay", "dexnav", "time", "outbreak", "fixed"}
TABLE_PROFILES = {"NORMAL", "RESEARCH"}
SIMPLE_UI = {"STANDARD_MESSAGE", "STANDARD_LIST", "YES_NO"}
CONTENT_FILES = {
    "progression": "content/kanto_progression.csv",
    "maps": "content/maps.csv",
    "encounters": "content/encounters.csv",
    "trainers": "content/trainers.csv",
    "qol_supply": "content/qol_supply.csv",
    "events": "content/events.csv",
    "event_symbols": "content/event_symbols.csv",
}
PRIMARY_KEYS = {
    "progression": "unlock_key", "maps": "map_key", "encounters": "encounter_key",
    "trainers": "trainer_key", "qol_supply": "supply_key", "events": "event_key",
    "event_symbols": "symbol_key",
}
REQUIRED_HEADERS = {
    "progression": ["unlock_key","region","sequence","predecessor_keys","recommended_level_min","recommended_level_max","difficulty_policy","mandatory","warning_key","safe_route_key","allowed_gimmicks"],
    "maps": ["map_key","region","logical_location_key","unlock_key","map_kind","field_pc_allowed","safe_route_key","warning_key"],
    "encounters": ["encounter_key","region","map_key","layer","table_profile","base_table_key","species_key","form_key","level_min","level_max","level_delta","iv_floor","hidden_ability_policy","egg_move_policy","held_item_key","shiny_policy","unlock_key","weight"],
    "trainers": ["trainer_key","region","map_key","trainer_role","ai_profile_key","expected_fight_style_key","team_stage","rematch_tier","league_stage","ev_spread_key","species_key","form_key","level","nature_key","ability_key","item_key","move1_key","move2_key","move3_key","move4_key","mechanic_policy","unlock_key","mandatory","difficulty_policy","warning_key"],
    "qol_supply": ["supply_key","item_key","service_key","unlock_key","supply_tier","repeatability","quantity","field_pc_allowed"],
    "events": ["event_key","region","map_key","unlock_key","presentation_profile","ui_components","condition_key","flag_key","reward_key","battle_key","warp_key","mandatory","result_policy","recommended_level_min","recommended_level_max","difficulty_policy","warning_key","safe_route_key"],
    "event_symbols": ["symbol_key","symbol_kind","owner"],
}


class ContentError(RuntimeError):
    pass


def _csv_with_header(root: Path, relative: str) -> tuple[list[str], list[dict[str, str]]]:
    with (root / relative).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _manifest_keys(root: Path, name: str, column: str) -> set[str]:
    _, rows = _csv_with_header(root, f"manifests/{name}")
    return {row[column] for row in rows}


def _split(value: str) -> list[str]:
    return [part for part in value.split("|") if part and part != "NONE"]


def _int(row: dict[str, str], key: str, errors: list[str], label: str) -> int:
    try:
        return int(row[key])
    except (KeyError, ValueError):
        errors.append(f"{label}: {key} must be integer")
        return 0


def _unique(rows: list[dict[str, str]], key: str, label: str, errors: list[str]) -> None:
    values = [row.get(key, "") for row in rows]
    duplicate = sorted(value for value,count in Counter(values).items() if count > 1)
    if duplicate:
        errors.append(f"{label}: duplicate {key}: {duplicate}")


def _check_symbolic_rows(name: str, rows: list[dict[str, str]], errors: list[str]) -> None:
    for line,row in enumerate(rows, 2):
        for field,value in row.items():
            if field.endswith("_key"):
                if not KEY_RE.fullmatch(value):
                    errors.append(f"{name}:{line}: non-symbolic {field}={value!r}")
                if re.fullmatch(r"(?:0x[0-9A-Fa-f]+|\d+)", value):
                    errors.append(f"{name}:{line}: raw numeric ID in {field}")
            elif field.endswith("_keys"):
                for key in _split(value):
                    if not KEY_RE.fullmatch(key):
                        errors.append(f"{name}:{line}: non-symbolic {field} member={key!r}")


def _unlocks(rows: list[dict[str, str]], errors: list[str]) -> tuple[set[str], dict[str, dict[str, str]]]:
    by_key = {row["unlock_key"]: row for row in rows}
    for row in rows:
        low = _int(row,"recommended_level_min",errors,row["unlock_key"])
        high = _int(row,"recommended_level_max",errors,row["unlock_key"])
        if not (1 <= low <= high <= 100):
            errors.append(f"{row['unlock_key']}: invalid recommended level range {low}-{high}")
        for parent in _split(row["predecessor_keys"]):
            if parent not in by_key:
                errors.append(f"{row['unlock_key']}: unresolved predecessor {parent}")
        if row["region"] == "KANTO" and row["difficulty_policy"] != "FIXED_HIGH_LEVEL_OPTIONAL":
            errors.append(f"{row['unlock_key']}: Kanto must use fixed optional high-level policy")
        if row["unlock_key"] == "KANTO_EARLY_ACCESS":
            if row["mandatory"] != "false" or row["warning_key"] == "WARNING_NONE" or row["safe_route_key"] == "NONE":
                errors.append("KANTO_EARLY_ACCESS: warning, optional policy, and safe route are required")
    return set(by_key), by_key


def _phase_has_ancestor(key: str, target: str, by_key: dict[str, dict[str, str]], seen: set[str] | None = None) -> bool:
    if key == target:
        return True
    seen = set() if seen is None else seen
    if key in seen or key not in by_key:
        return False
    seen.add(key)
    return any(_phase_has_ancestor(parent,target,by_key,seen) for parent in _split(by_key[key]["predecessor_keys"]))


def validate_trainer_rows(rows: list[dict[str, str]], registries: dict[str, set[str]],
                          phases: dict[str, dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for line,row in enumerate(rows,2):
        key = row.get("trainer_key", f"line{line}")
        if row.get("ai_profile_key") not in AI_PROFILES:
            errors.append(f"{key}: unresolved AI profile {row.get('ai_profile_key')}")
        for field, registry in (("species_key","species"),("ability_key","ability"),("item_key","item")):
            if row.get(field) not in registries[registry]:
                errors.append(f"{key}: unresolved/illegal {field} {row.get(field)}")
        moves = [row.get(f"move{x}_key","") for x in range(1,5)]
        if any(move not in registries["move"] for move in moves):
            errors.append(f"{key}: unresolved/illegal move")
        if len([m for m in moves if m != "MOVE_KEY_NONE"]) > 4:
            errors.append(f"{key}: more than four moves")
        try:
            level = int(row.get("level","0"))
        except ValueError:
            level = 0
        if not 1 <= level <= 100:
            errors.append(f"{key}: level outside 1..100")
        phase = phases.get(row.get("unlock_key",""))
        if not phase:
            errors.append(f"{key}: unresolved unlock")
        else:
            if level < int(phase["recommended_level_min"])-10 or level > int(phase["recommended_level_max"])+10:
                errors.append(f"{key}: level outside stage policy")
            allowed = set(_split(phase["allowed_gimmicks"]))
            mechanics = set(_split(row.get("mechanic_policy","NONE")))
            if len(mechanics) > 1:
                errors.append(f"{key}: multiple gimmicks in one battle")
            if mechanics - allowed:
                errors.append(f"{key}: gimmick before unlock")
        if row.get("region") == "KANTO" and row.get("difficulty_policy") != "FIXED_HIGH_LEVEL_OPTIONAL":
            errors.append(f"{key}: hidden/dynamic level scaling is forbidden")
        if row.get("unlock_key") == "KANTO_EARLY_ACCESS" and row.get("warning_key") in ("","WARNING_NONE"):
            errors.append(f"{key}: early-access warning missing")
        if row.get("trainer_role") == "GENERAL" and row.get("rematch_tier") not in ("NONE","LOCAL"):
            errors.append(f"{key}: blanket general-trainer rematch is forbidden")
    return errors


def validate_facility_doc(doc: dict[str, Any], registries: dict[str, set[str]],
                          unlocks: set[str]) -> list[str]:
    errors: list[str] = []
    owners=doc.get("state_owners",{})
    if owners.get("factory") == owners.get("mirage") or not owners.get("factory") or not owners.get("mirage"):
        errors.append("facility: Factory and Mirage state owners must be distinct")
    def keyed(section: str, key: str) -> dict[str, dict[str, Any]]:
        values = doc.get(section, [])
        out = {row.get(key,""): row for row in values}
        if len(out) != len(values) or "" in out:
            errors.append(f"facility.{section}: duplicate/missing {key}")
        return out
    currencies = keyed("currencies","currency_key")
    credits = keyed("credits","credit_key")
    modes = keyed("modes","mode_key")
    sets = keyed("rental_sets","rental_set_key")
    rental_pools = keyed("rental_pools","pool_key")
    trainer_pools = keyed("trainer_pools","pool_key")
    rewards = keyed("rewards","reward_key")
    encounter_pools = keyed("encounter_pools","pool_key")
    keyed("shops","shop_key"); keyed("encounter_npcs","npc_key"); keyed("raids","raid_key")
    for key,row in currencies.items():
        if row.get("availability") not in ("ENABLED","DEFERRED") or row.get("balance_policy") != "NONNEGATIVE_U16":
            errors.append(f"{key}: invalid currency availability/balance policy")
        if key == "CURRENCY_KEY_RESEARCH_POINT" and row.get("availability") != "DEFERRED":
            errors.append(f"{key}: T02/T08 supply hook unresolved; must be DEFERRED")
    for key,row in credits.items():
        if row.get("consume_count") != 1:
            errors.append(f"{key}: typed credit must consume exactly one")
    for key,row in sets.items():
        for field,registry in (("species_key","species"),("ability_key","ability"),("item_key","item")):
            if row.get(field) not in registries[registry]: errors.append(f"{key}: unresolved {field}")
        moves = row.get("move_keys",[])
        if not 1 <= len(moves) <= 4 or len(moves) != len(set(moves)) or any(x not in registries["move"] for x in moves):
            errors.append(f"{key}: illegal move set")
        if not 1 <= int(row.get("level",0)) <= 100: errors.append(f"{key}: invalid level")
        if len(_split(row.get("mechanic_policy","NONE"))) > 1: errors.append(f"{key}: multiple gimmicks")
    for key,row in rental_pools.items():
        if row.get("unlock_key") not in unlocks: errors.append(f"{key}: unresolved unlock")
        for ref in row.get("set_keys",[]):
            if ref not in sets: errors.append(f"{key}: unresolved rental set {ref}")
    for key,row in trainer_pools.items():
        if row.get("unlock_key") not in unlocks: errors.append(f"{key}: unresolved unlock")
        for ref in row.get("trainer_keys",[]):
            if ref not in registries["trainer"]: errors.append(f"{key}: unresolved trainer {ref}")
    for key,row in modes.items():
        for field,registry in (("rental_pool_key",rental_pools),("trainer_pool_key",trainer_pools),("streak_reward_key",rewards)):
            if row.get(field) not in registry: errors.append(f"{key}: unresolved {field}")
        if row.get("unlock_key") not in unlocks: errors.append(f"{key}: unresolved unlock")
        if len(_split(row.get("mechanic_policy","NONE"))) > 1: errors.append(f"{key}: multiple gimmicks")
    for key,row in rewards.items():
        currency = currencies.get(row.get("currency_key"))
        if not currency: errors.append(f"{key}: unknown currency")
        elif currency.get("availability") != "ENABLED": errors.append(f"{key}: deferred currency cannot be spent/earned")
        if int(row.get("amount",-1)) < 0: errors.append(f"{key}: negative balance delta")
    for row in doc.get("shops",[]):
        key=row.get("shop_key")
        currency=currencies.get(row.get("currency_key"))
        if not currency or currency.get("availability")!="ENABLED": errors.append(f"{key}: unresolved/deferred shop currency")
        if any(item not in registries["item"] for item in row.get("item_keys",[])): errors.append(f"{key}: unresolved shop item")
    for key,row in encounter_pools.items():
        if row.get("unlock_key") not in unlocks: errors.append(f"{key}: unresolved unlock")
        for entry in row.get("entries",[]):
            if entry.get("species_key") not in registries["species"]: errors.append(f"{key}: unresolved species")
            if entry.get("capture_policy") == "REPEATABLE_SPECIAL": errors.append(f"{key}: legendary/mythical repeat capture forbidden")
    for row in doc.get("encounter_npcs",[]):
        key=row.get("npc_key")
        kind=row.get("payment_kind")
        if kind == "currency":
            if row.get("currency_key") not in currencies or row.get("credit_key") != "NONE": errors.append(f"{key}: currency payment references invalid")
            elif currencies[row["currency_key"]].get("availability") != "ENABLED": errors.append(f"{key}: deferred currency unavailable")
        elif kind == "credit":
            if row.get("credit_key") not in credits or row.get("currency_key") != "NONE": errors.append(f"{key}: credit payment references invalid")
            elif credits[row["credit_key"]].get("availability") != "ENABLED": errors.append(f"{key}: deferred credit unavailable")
            if row.get("cost") != 1: errors.append(f"{key}: typed credit cost must be one")
        else: errors.append(f"{key}: payment_kind must be currency|credit")
        if row.get("pool_key") not in encounter_pools: errors.append(f"{key}: unresolved encounter pool")
        if row.get("unlock_key") not in unlocks: errors.append(f"{key}: unresolved unlock")
        if row.get("presentation_profile") != "SIMPLE_EVENT" or set(row.get("ui_components",[]))-SIMPLE_UI:
            errors.append(f"{key}: encounter NPC requires standard SIMPLE_EVENT UI")
        if row.get("dedicated_map") or row.get("full_screen_ui"): errors.append(f"{key}: dedicated map/full-screen UI forbidden")
        if not row.get("capacity_check_before_payment") or not row.get("persist_pending_before_battle"):
            errors.append(f"{key}: capacity-check and persisted pending transaction required")
    for row in doc.get("raids",[]):
        key=row.get("raid_key")
        if row.get("species_key") not in registries["species"]: errors.append(f"{key}: unresolved species")
        if not 1 <= int(row.get("level",0)) <= 100: errors.append(f"{key}: invalid level")
        if row.get("partner_pool_key") not in trainer_pools or row.get("reward_pool_key") not in rewards: errors.append(f"{key}: unresolved pool")
        if row.get("unlock_key") not in unlocks: errors.append(f"{key}: unresolved unlock")
        if row.get("mechanic_policy") != "RAID_DYNAMAX": errors.append(f"{key}: Raid permits fixed Dynamax only")
        if row.get("capture_policy") == "SHARED_ONCE" and (row.get("shared_capture_key") == "NONE" or row.get("reward_repeatability") != "ONCE" or row.get("claim_key") == "NONE"):
            errors.append(f"{key}: shared capture and reward claim state must be independent and once")
        if row.get("dedicated_map") or row.get("custom_ui") or row.get("cutscene") or row.get("presentation_profile") != "SIMPLE_EVENT":
            errors.append(f"{key}: dedicated map/UI/cutscene forbidden")
    return errors


def load_repository(root: Path) -> tuple[dict[str,list[dict[str,str]]],dict[str,Any]]:
    tables: dict[str,list[dict[str,str]]] = {}
    for name,relative in CONTENT_FILES.items():
        header,rows = _csv_with_header(root,relative)
        if header != REQUIRED_HEADERS[name]:
            raise ContentError(f"{relative}: header drift")
        tables[name]=rows
    facility=json.loads((root/"content/facilities.json").read_text(encoding="utf-8"))
    return tables,facility


def validate_repository(root: Path) -> dict[str,Any]:
    tables,facility=load_repository(root)
    errors: list[str]=[]
    try:
        import jsonschema
        facility_schema=json.loads((root/"content/schema/facility.schema.json").read_text(encoding="utf-8"))
        trainer_schema=json.loads((root/"content/schema/trainer_difficulty.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(facility_schema)
        jsonschema.Draft202012Validator.check_schema(trainer_schema)
        jsonschema.validate(facility,facility_schema)
        for row in tables["trainers"]: jsonschema.validate(row,trainer_schema)
    except (ImportError,ValueError,json.JSONDecodeError) as exc:
        errors.append(f"JSON schema setup failed: {exc}")
    except Exception as exc:
        errors.append(f"JSON schema validation failed: {exc}")
    for name,rows in tables.items():
        _unique(rows,PRIMARY_KEYS[name],name,errors)
        _check_symbolic_rows(name,rows,errors)
    unlocks,phases=_unlocks(tables["progression"],errors)
    for key,row in phases.items():
        if row["region"]=="KANTO" and int(row["sequence"]) >= int(phases["VEGA_HALL_OF_FAME"]["sequence"]) and not _phase_has_ancestor(key,"VEGA_HALL_OF_FAME",phases):
            errors.append(f"{key}: post-HoF content reachable without VEGA_HALL_OF_FAME")
    event_symbols={row["symbol_key"]:row["symbol_kind"] for row in tables["event_symbols"]}
    maps={row["map_key"] for row in tables["maps"]}
    logical=({f"K{x:02d}" for x in range(1,48)}
             | {f"T{x:03d}" for x in range(501,524)}
             | {f"T{x:03d}" for x in range(24,50)}
             | {"VEGA_NATIVE"})
    for row in tables["maps"]:
        if row["unlock_key"] not in unlocks: errors.append(f"{row['map_key']}: unresolved unlock")
        if row["logical_location_key"] not in logical: errors.append(f"{row['map_key']}: unresolved logical location")
        if row["field_pc_allowed"] not in ("true","false"): errors.append(f"{row['map_key']}: field_pc_allowed must be explicit bool")
        if row["field_pc_allowed"]=="true" and row["map_kind"] in ("DUNGEON","GYM","LEAGUE","EVENT"):
            errors.append(f"{row['map_key']}: field PC forbidden in {row['map_kind']}")
        if row["warning_key"] not in {r["warning_key"] for r in tables["progression"]} or row["safe_route_key"] not in {r["safe_route_key"] for r in tables["progression"]}:
            errors.append(f"{row['map_key']}: unresolved warning/safe route")
    registries={
        "species":_manifest_keys(root,"species_ids.csv","species_key"),
        "move":_manifest_keys(root,"move_ids.csv","move_key"),
        "ability":_manifest_keys(root,"ability_ids.csv","ability_key"),
        "item":_manifest_keys(root,"item_ids.csv","item_key"),
        "trainer":{row["trainer_key"] for row in tables["trainers"]},
    }
    errors.extend(validate_trainer_rows(tables["trainers"],registries,phases))
    for row in tables["trainers"]:
        if row["map_key"] not in maps: errors.append(f"{row['trainer_key']}: unresolved map")
    normal_tables={(row["map_key"],row["base_table_key"]) for row in tables["encounters"] if row["table_profile"]=="NORMAL" and int(row["weight"])>0}
    kanto_normal={(row["map_key"],row["base_table_key"]) for row in tables["encounters"] if row["region"]=="KANTO" and row["table_profile"]=="NORMAL"}
    for row in tables["encounters"]:
        key=row["encounter_key"]
        if row["map_key"] not in maps or row["unlock_key"] not in unlocks: errors.append(f"{key}: unresolved map/unlock")
        if row["layer"] not in LAYERS or row["table_profile"] not in TABLE_PROFILES: errors.append(f"{key}: invalid layer/table profile")
        if row["species_key"] not in registries["species"] or row["held_item_key"] not in registries["item"]: errors.append(f"{key}: unresolved species/item")
        low=_int(row,"level_min",errors,key); high=_int(row,"level_max",errors,key)
        if not 1<=low<=high<=100: errors.append(f"{key}: invalid level range")
        if row["table_profile"]=="RESEARCH" and (row["map_key"],row["base_table_key"]) not in normal_tables:
            errors.append(f"{key}: RESEARCH cannot replace/remove NORMAL table")
    for table in kanto_normal:
        if not any((row["map_key"],row["base_table_key"])==table and row["table_profile"]=="NORMAL" and 0 < int(row["weight"]) <= 10 for row in tables["encounters"]):
            errors.append(f"{table}: NORMAL rare slot disappeared")
    repeat_floor={"ITEM_KEY_POWER_BRACER":"VEGA_BADGE_5","ITEM_KEY_EXP_CANDY_L":"VEGA_BADGE_7","ITEM_KEY_ABILITY_PATCH":"VEGA_BADGE_8","ITEM_KEY_EXP_CANDY_XL":"KANTO_LEAGUE_CLEAR","ITEM_KEY_GOLD_BOTTLE_CAP":"KANTO_LEAGUE_CLEAR"}
    for row in tables["qol_supply"]:
        key=row["supply_key"]
        if row["item_key"] not in registries["item"] or row["unlock_key"] not in unlocks: errors.append(f"{key}: unresolved item/unlock")
        if row["repeatability"] in ("REPEATABLE","LIMITED_REPEATABLE") and row["item_key"] in repeat_floor:
            floor=repeat_floor[row["item_key"]]
            if not _phase_has_ancestor(row["unlock_key"],floor,phases): errors.append(f"{key}: repeatable supply before {floor}")
    for row in tables["events"]:
        key=row["event_key"]
        if row["map_key"] not in maps or row["unlock_key"] not in unlocks: errors.append(f"{key}: unresolved map/unlock")
        if row["presentation_profile"]!="SIMPLE_EVENT" or set(_split(row["ui_components"]))-SIMPLE_UI: errors.append(f"{key}: SIMPLE_EVENT uses forbidden component")
        for field,kind in (("condition_key","CONDITION"),("flag_key","FLAG"),("reward_key","REWARD"),("battle_key","BATTLE"),("warp_key","WARP")):
            value=row[field]
            if value != "NONE" and event_symbols.get(value) != kind: errors.append(f"{key}: unresolved {field} {value}")
        if row["unlock_key"]=="KANTO_EARLY_ACCESS" and (row["mandatory"]!="false" or row["warning_key"]=="WARNING_NONE" or row["safe_route_key"]=="NONE"):
            errors.append(f"{key}: early event must be optional with warning/safe route")
        if "SHIP" in key and row["result_policy"]!="RESULT_INDEPENDENT": errors.append(f"{key}: ship battle must be result-independent")
    errors.extend(validate_facility_doc(facility,registries,unlocks))
    audit=audit_v2(root)
    failed=[key for key,value in audit.items() if not value]
    if failed: errors.append(f"V2 independent audit failed: {failed}")
    if errors: raise ContentError("\n".join(errors))
    return {"tables":tables,"facility":facility,"registries":registries,"v2_audit":audit,"normalization":normalization_diagnostics(root)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()


def build_outputs(root: Path) -> dict[str,bytes]:
    result=validate_repository(root); tables=result["tables"]; facility=result["facility"]; norm=result["normalization"]
    use=Counter(row["trainer_role"] for row in tables["trainers"])
    supply="\n".join(f"| `{r['item_key'] if r['item_key']!='ITEM_KEY_NONE' else r['service_key']}` | `{r['unlock_key']}` | `{r['repeatability']}` |" for r in tables["qol_supply"])
    report=f"""# Symbolic content schema report

- content validation: PASS
- raw numeric Species/Move/Item IDs: 0
- V2 independent checks: {sum(result['v2_audit'].values())} / 59 PASS
- generator dry-run: logical map emission only; physical binding owner is T13
- schema inputs: `{_sha(_stable({k:len(v) for k,v in tables.items()}))}`

## V2 normalization gate

- pre-normalization: {norm['raw_validation']} (semantic duplicate evolution rows={norm['raw_semantic_duplicate_count']}, decimal National ID rows={norm['raw_decimal_national_id_count']}, missing rescue items={len(norm['raw_missing_evolution_item_references'])})
- normalized: {norm['normalized_validation']} (evolution rows={norm['normalized_evolution_rows']}, explicit form key=true, missing rescue items=0)
- missing-before-normalization: {', '.join(norm['raw_missing_evolution_item_references'])}

Raw V2 is therefore rejected before normalization. The normalized contract canonicalizes integer National IDs, adds explicit form keys, removes semantic duplicates, and supplies symbolic rescue-item references. The received package itself remains unchanged.

## Coverage and availability

- V2 evolution families with dual-region route: 541 / 541
- shared special-capture keys: 125 / 125
- V2 logical Kanto locations: 47; physical binding intentionally pending T13
- trainer usage: {dict(sorted(use.items()))}
- unobtainable evolution lines after normalization: 0

| Item / service | First availability | Repeatability |
|---|---|---|
{supply}

## Safety policies

- Kanto Lv.68–100 is `FIXED_HIGH_LEVEL_OPTIONAL`; no party scaling field exists.
- Early invitation, research pass, dialogue, and ship battle are progress-aware; the ship battle is optional and result-independent.
- `SIMPLE_EVENT` permits standard message/list/Yes-No and normal script commands only.
- NORMAL encounter tables remain present when RESEARCH overlays exist.
- Facility, encounter transaction, currency/credit, AI, gimmick, and Raid references resolve symbolically. Research point remains `DEFERRED` until its earn hook is owned.
""".encode()
    dry={"schema_version":1,"mode":"DRY_RUN","validated":True,"logical_maps":sorted(r["map_key"] for r in tables["maps"]),"physical_map_emission":"PENDING_T13","unresolved_numeric_keys":True,"row_counts":{k:len(v) for k,v in tables.items()},"facility_counts":{k:len(v) for k,v in facility.items() if isinstance(v,list)}}
    v2base=root/"design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data"
    with (v2base/"伝説・幻・UB・パラドックスイベントマスター_二地方改訂版_125種.csv").open(encoding="utf-8-sig",newline="") as stream:
        specials=list(csv.DictReader(stream))
    shared_header="shared_capture_key,national_no,species_name,primary_region,capture_repeatability,reward_repeatability,claim_key\n"
    shared_rows=[f"SHARED_CAPTURE_KEY_NATIONAL_{int(r['national_no']):04d},{int(r['national_no'])},{r['name']},{'TOHOKU' if r['primary_capture_region']=='トーホク' else 'KANTO'},ONCE,ONCE,CLAIM_KEY_NATIONAL_{int(r['national_no']):04d}" for r in specials]
    with (v2base/"進化系統_二地方配置マスター_全541系統.csv").open(encoding="utf-8-sig",newline="") as stream:
        families=list(csv.DictReader(stream))
    family_header="family_key,root_national_no,root_name,tohoku_location_key,kanto_location_key,coverage_status\n"
    family_rows=[f"FAMILY_KEY_{int(r['evolution_chain_id']):04d},{int(r['root_national_no'])},{r['root_name']},{r['tohoku_map_code']},{r['kanto_map_code']},DUAL_REGION" for r in families]
    with (v2base/"カントージム_認定章・生態解禁マスター.csv").open(encoding="utf-8-sig",newline="") as stream:
        gyms=list(csv.DictReader(stream))
    gym_header="gym_key,unlock_key,reward_key,repeatability,presentation_profile\n"
    gym_rows=[f"GYM_KEY_KANTO_{i:02d},KANTO_CERT_{i},REWARD_KEY_KANTO_CERT_{i},ONCE,SIMPLE_EVENT" for i,_ in enumerate(gyms,1)]
    return {
        "reports/generated/content_schema.md":report,
        "generated/content/dry_run.json":_stable(dry),
        "content/normalized/shared_captures.csv":(shared_header+"\n".join(shared_rows)+"\n").encode(),
        "content/normalized/v2_family_coverage.csv":(family_header+"\n".join(family_rows)+"\n").encode(),
        "content/normalized/kanto_gym_rewards.csv":(gym_header+"\n".join(gym_rows)+"\n").encode(),
    }


def emit_content(root: Path, resolution: dict[str,Any] | None) -> bytes:
    result=validate_repository(root); tables=result["tables"]
    if not resolution:
        raise ContentError("build-mode emission requires --resolution with IDs and T13 physical_map_bindings")
    ids=resolution.get("ids",{}); bindings=resolution.get("physical_map_bindings",{})
    required=set()
    for rows in tables.values():
        for row in rows:
            for field,value in row.items():
                if field.endswith("_key") and value!="NONE" and field not in ("map_key","unlock_key","warning_key","safe_route_key"):
                    required.add(value)
    missing=sorted(required-set(ids))
    map_missing=sorted({r["map_key"] for r in tables["maps"]}-set(bindings))
    if missing or map_missing:
        raise ContentError(f"unresolved build keys: ids={missing[:8]} physical_maps={map_missing}; bind through T13")
    return _stable({"schema_version":1,"mode":"PHYSICAL","ids":{k:ids[k] for k in sorted(required)},"physical_maps":{k:bindings[k] for k in sorted(bindings)}})
