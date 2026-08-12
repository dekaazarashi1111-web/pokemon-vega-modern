#!/usr/bin/env python3
"""T02 RAM/save/ID/facility/currency/AI state inventory.

The model in this module is intentionally deterministic.  It records hashes,
bounded expected bytes, and symbolic ownership; it never serializes ROM, save,
or RAM contents.  ``validate_state_inventory`` is also public so later tasks can
run the same fail-closed checks after extending the model.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


ROM_BASE = 0x08000000
SCHEMA_VERSION = 1

RANGE_FIELDS = frozenset(
    {
        "address_space",
        "start",
        "end_exclusive",
        "size",
        "owner",
        "key",
        "storage",
        "lifetime",
        "persistence",
        "active_condition",
        "source_ref",
        "overlaps",
        "classification",
        "resolution",
        "evidence_sha256",
    }
)
ID_FIELDS = frozenset(
    {
        "domain",
        "key",
        "id",
        "id_hex",
        "width_bits",
        "owner",
        "origin",
        "storage",
        "lifetime",
        "persistence",
        "active_condition",
        "aliases",
        "range_key",
        "id_policy",
        "resolution",
        "raw_refs",
        "evidence",
    }
)
QOL_FIELDS = frozenset(
    {
        "domain",
        "address_or_symbol",
        "status",
        "vega_expected_sha256",
        "classification",
        "evidence",
        "followup_task",
    }
)

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_DYNAMIC_KEYS = frozenset(
    {"timestamp", "generated_at", "generatedAt", "captured_at", "capturedAt"}
)
_NON_ROM_QOL_SENTINEL = "NOT_APPLICABLE_NON_ROM_CONTRACT"
_QOL_DEFINITIONS: dict[str, tuple[str, str, str, str, str]] = {
    "dash": (
        "FLAG_AUTO_RUN / overworld movement callbacks",
        "SOURCE_ACTIVE_VEGA_ADAPTER_REQUIRED",
        "RELOCATE",
        "src/config.h:53-56;src/overworld.c",
        "T09",
    ),
    "bicycle": (
        "FLAG_BIKE_TURBO_BOOST / FLAG_SURF_TURBO_BOOST",
        "SOURCE_ACTIVE_TILE_TIMING_AUDIT_REQUIRED",
        "RELOCATE",
        "src/config.h:55-56;src/overworld.c",
        "T09",
    ),
    "field_text_printer": (
        "TextPrinter / INSTANT_TEXT",
        "SOURCE_PRESENT_INACTIVE_WAIT_SEMANTICS_REQUIRED",
        "PORT",
        "src/config.h:264,351;src/text_printer.c:33-60",
        "T09",
    ),
    "battle_text_printer": (
        "FLAG_FAST_BATTLE_MESSAGES / battle string printer",
        "SOURCE_RUNTIME_GATED_WAIT_SEMANTICS_REQUIRED",
        "RELOCATE",
        "src/config.h:63;src/text_printer.c;src/battle_strings.c",
        "T09",
    ),
    "experience_distribution": (
        "FLAG_EXP_SHARE / GiveExpToMon",
        "SOURCE_RUNTIME_GATED",
        "RELOCATE",
        "src/config.h:38,317-320;src/exp.c:103-168,228-255,444-468",
        "T06",
    ),
    "item_use": (
        "ItemUseOutOfBattle / party_menu item callbacks",
        "SOURCE_ACTIVE_TABLE_REPOINT_REQUIRED",
        "RELOCATE",
        "src/item.c:804-955;src/party_menu.c:2463-2854;src/Tables/item_tables.c",
        "T05",
    ),
    "daycare_and_hatching": (
        "daycare inheritance and hatch hooks",
        "SOURCE_PARTIAL_TRANSACTION_ADAPTER_REQUIRED",
        "RELOCATE",
        "src/daycare.c:62-990;hooks:534-548",
        "T10",
    ),
    "summary": (
        "pokemon_summary_screen hooks/repoints",
        "SOURCE_PARTIAL_VEGA_UI_ADAPTER_REQUIRED",
        "RELOCATE",
        "hooks:365-376,460-469;repoints:155-160;src/pokemon_summary_screen.c",
        "T10",
    ),
    "pc": (
        "SELECT_FROM_PC / pokemon_storage_system",
        "SOURCE_PARTIAL_TRANSACTION_ADAPTER_REQUIRED",
        "RELOCATE",
        "src/config.h:228-229;hooks:594-618;src/scripting.c:639-717",
        "T10",
    ),
    "move_relearner": (
        "FLAG_MOVE_RELEARNER_IGNORE_LEVEL / FLAG_EGG_MOVE_RELEARNER",
        "SOURCE_RUNTIME_GATED",
        "RELOCATE",
        "src/config.h:58-59;src/party_menu.c",
        "T10",
    ),
    "tm_consumption": (
        "REUSABLE_TMS / item table Mystery byte",
        "SOURCE_ACTIVE_VEGA_ITEM_TABLE_ASSERT_REQUIRED",
        "RELOCATE",
        "src/config.h:128;hooks:576-587;src/item.c:804-955",
        "T05",
    ),
    "dexnav": (
        "FLAG_SYS_DEXNAV / DexNav start-menu and encounter hooks",
        "SOURCE_RUNTIME_GATED",
        "RELOCATE",
        "include/new/dexnav_config.h:9-61;src/start_menu.c:112-235;src/overworld.c:1511-1539",
        "T12",
    ),
    "raid": (
        "FLAG_RAID_BATTLE / dynamax raid specials and tables",
        "SOURCE_RUNTIME_GATED_FULL_STATE_AUDITED",
        "RELOCATE",
        "src/config.h:60-62,220;src/dynamax.c:1576-1589;routinepointers:171-178;src/Tables/raid_encounters.h",
        "T15",
    ),
    "settings_save": (
        "SaveBlock2 options plus new integration settings schema",
        "SOURCE_HAS_COMPILE_FLAGS_NO_SAVEABLE_MODE_SCHEMA",
        "RELOCATE",
        "src/config.h:264,351;include/global.h:764-785;src/save.c",
        "T08",
    ),
}


class StateInventoryError(ValueError):
    """The fixed input or generated state model violates the T02 contract."""


def _parse_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise StateInventoryError(f"{label} must be an integer, not bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError as exc:
            raise StateInventoryError(f"{label} is not an integer: {value!r}") from exc
    raise StateInventoryError(f"{label} is not an integer: {value!r}")


def _hex(value: int, width: int = 8) -> str:
    return f"0x{value:0{width}X}"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise StateInventoryError(f"cannot hash evidence file: {path}") from exc
    return digest.hexdigest()


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateInventoryError(f"cannot load {label}: {path}") from exc
    if not isinstance(value, Mapping):
        raise StateInventoryError(f"{label} must be a JSON object")
    return value


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise StateInventoryError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise StateInventoryError(f"{label} must be a list")
    return value


def _require_policy(policy: Mapping[str, Any]) -> None:
    if policy.get("schema_version") != SCHEMA_VERSION:
        raise StateInventoryError("unsupported T02 policy schema")
    if policy.get("policy_id") != "T02_EXACT_AUDIT_V1":
        raise StateInventoryError("unsupported T02 policy id")
    for key in (
        "source_lock",
        "inputs",
        "t01_artifact",
        "classifications",
        "high_flag_migration",
        "facilities",
        "currencies",
        "ids",
        "ai",
        "qol_required_domains",
    ):
        if key not in policy:
            raise StateInventoryError(f"policy is missing {key}")


def _read_verified_file(
    root: Path,
    relative: str,
    *,
    expected_sha256: str | None = None,
    required_text: Sequence[str] = (),
) -> tuple[bytes, str]:
    path = root / relative
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise StateInventoryError(f"missing fixed evidence: {relative}") from exc
    digest = _sha256_bytes(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise StateInventoryError(
            f"fixed evidence SHA-256 mismatch for {relative}: {digest}"
        )
    if required_text:
        text = data.decode("utf-8", errors="strict")
        for needle in required_text:
            if needle not in text:
                raise StateInventoryError(
                    f"fixed evidence text is missing from {relative}: {needle}"
                )
    return data, digest


def _verify_inputs(root: Path, policy: Mapping[str, Any]) -> dict[str, Any]:
    """Verify fixed roots without exposing their physical/private paths."""

    source_lock_spec = _require_mapping(policy["source_lock"], "source_lock")
    lock_rel = str(source_lock_spec["path"])
    lock_data, lock_sha = _read_verified_file(
        root, lock_rel, expected_sha256=str(source_lock_spec["sha256"])
    )
    source_lock = json.loads(lock_data.decode("utf-8"))
    if not isinstance(source_lock, Mapping):
        raise StateInventoryError("source lock must be an object")
    actual_commits = {
        str(row["name"]): str(row["resolved_commit"])
        for row in _require_list(source_lock.get("sources"), "source_lock.sources")
    }
    expected_commits = {
        str(key): str(value)
        for key, value in _require_mapping(
            source_lock_spec["commits"], "source_lock.commits"
        ).items()
    }
    if actual_commits != expected_commits:
        raise StateInventoryError("source lock commits do not match T02 policy")

    roms: dict[str, dict[str, Any]] = {}
    rom_data: dict[str, bytes] = {}
    for label, raw_spec in _require_mapping(policy["inputs"], "inputs").items():
        spec = _require_mapping(raw_spec, f"inputs.{label}")
        relative = str(spec["path"])
        data, digest = _read_verified_file(
            root, relative, expected_sha256=str(spec["sha256"])
        )
        expected_size = _parse_int(spec["size"], f"inputs.{label}.size")
        if len(data) != expected_size:
            raise StateInventoryError(
                f"{label} ROM size mismatch: {len(data)} != {expected_size}"
            )
        roms[str(label)] = {"size": expected_size, "sha256": digest}
        rom_data[str(label)] = data

    artifact = _require_mapping(policy["t01_artifact"], "t01_artifact")
    result_rel = str(artifact["result"])
    result_path = root / result_rel
    if result_path.is_symlink():
        raise StateInventoryError("T01 result must not be a symlink")
    result = _load_json(result_path, "T01 result")
    if result.get("fingerprint") != artifact.get("fingerprint"):
        raise StateInventoryError("T01 result fingerprint mismatch")
    observed_outputs = {
        f"{row['engine']}/{row['profile']}": str(row["output_sha256"])
        for row in _require_list(result.get("builds"), "T01 result builds")
        if _parse_int(row.get("run", 0), "T01 build run") == 1
    }
    expected_outputs = {
        str(key): str(value)
        for key, value in _require_mapping(
            artifact["outputs"], "t01_artifact.outputs"
        ).items()
    }
    if observed_outputs != expected_outputs:
        raise StateInventoryError("T01 result output hashes mismatch")

    upstream_path = root / "config/upstream_inventory.json"
    upstream = _load_json(upstream_path, "T01 upstream inventory")
    if upstream.get("schema_version") != 1:
        raise StateInventoryError("T01 upstream inventory schema mismatch")
    upstream_source = _require_mapping(upstream.get("source"), "upstream source")
    if upstream_source.get("commit") != expected_commits.get("cfru"):
        raise StateInventoryError("T01 upstream inventory source commit mismatch")
    pinned_files = _require_mapping(upstream.get("files"), "upstream files")
    for relative, expected in pinned_files.items():
        _read_verified_file(root, str(relative), expected_sha256=str(expected))

    fixed_sources = {
        "vendor/upstream/CFRU-JP/BPRJ.ld": (
            "e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a",
            ("gBattleSandsStreaks = 0x2026794;", "gNewBS = 0x203DFB0;"),
        ),
        "vendor/upstream/CFRU-JP/include/global.h": (
            "c2973e69e55633ce39c9fe1763c891e5530b4ac1dc15e82a666c1f1ea7201bc0",
            ("/*0x0294*/ u16 coins;", "/*0x1300*/ u8 frontierRecords[0x19A0];"),
        ),
        "vendor/upstream/CFRU-JP/include/new/ram_locs.h": (
            "8c8d7fd53813fefff997173f203aa0c97e1c14062db933e55303d5c498b2f089",
            ("gExpandedFlags", "gPlayerCoins (*((u32*) 0x203B78C))"),
        ),
        "vendor/upstream/CFRU-JP/include/new/pokemon_storage_system.h": (
            "e8c426432fd10c5cdf6548f0c379f9113960a1afa8d3675a848a4bbf2557dec2",
            ("SIZE = 0x3A / 58 bytes",),
        ),
        "vendor/upstream/CFRU-JP/src/pokemon_storage_system.c": (
            "6736c25d6354899f0da92b3c654157d22b67bff007af0e96c4c1d6a4c9c941bb",
            ("#define gTempTeamBackup", "BackupPartyToTempTeam"),
        ),
        "vendor/upstream/CFRU-JP/src/save.c": (
            "e1c12550fb47ed4d7d5c14bdd20698e019c6913c2568aab917b29fc39636a42a",
            ("#define SAVE_BLOCK_PARASITE 0x0203B0E8", "SaveSector30And31"),
        ),
        "vendor/upstream/DPE-JP/include/species.h": (
            "00ff340a373d5187f970cabbfc45bb1e0971b14a9f504ee2d38e4e929b86f27c",
            ("#define NUM_SPECIES (SPECIES_PECHARUNT + 1)",),
        ),
        "vendor/upstream/DPE-JP/include/moves.h": (
            "3a06c8fc8b0acda448416fb172c2e427943585504a4c91bc76958272347b7688",
            ("#define MOVES_COUNT",),
        ),
        "vendor/upstream/DPE-JP/include/items.h": (
            "6c4312d1fda31b6a989c4d23d040572ec24def858f34f85b9eb90665a9e25f1c",
            ("#define ITEMS_COUNT",),
        ),
        "vendor/upstream/DPE-JP/include/pokedex.h": (
            "6c94b4008c9fdfc89343faa6b9ba5833ab4b31f1a954524ac8c26d42b391b567",
            ("#define NATIONAL_DEX_COUNT", "gPokedexScreenDataPtr"),
        ),
        "vendor/upstream/DPE-JP/BPRJ.ld": (
            "1f26a988a4c32567bd6cbc2c9fe9f876c9822acdabfe8bdfd902faebfa6d7d83",
            (
                "gPokedexScreenDataPtr = 0x203AC68;",
                "sNamingScreen = 0x20398D8;",
                "gMain = 0x3003130;",
            ),
        ),
        "vendor/upstream/DPE-JP/include/main.h": (
            "f5beb6fd5e493e3dafcdaaeaaa0a4e892637d8368f0e045ed070f4829de4a7e6",
            ("struct Main", "/*0x439*/ u8 inBattle:1;"),
        ),
        "vendor/upstream/DPE-JP/src/updated_code.c": (
            "7f259f27750ad5a395521780fcf1b9fa494b83464d7633668a1a0c9728feb393",
            ("extern struct NamingScreenData* sNamingScreen;",),
        ),
    }
    source_hashes: dict[str, str] = {}
    for relative, (expected, needles) in fixed_sources.items():
        _, source_hashes[relative] = _read_verified_file(
            root, relative, expected_sha256=expected, required_text=needles
        )

    vega = rom_data["vega"]

    def rom_slice(address: int, size: int, label: str) -> bytes:
        offset = address - ROM_BASE
        if offset < 0 or offset + size > len(vega):
            raise StateInventoryError(f"Vega ROM range outside image: {label}")
        return vega[offset : offset + size]

    ai_expected = _require_mapping(
        _require_mapping(policy["ai"], "ai")["vega_expected_hook_prefixes"],
        "ai.vega_expected_hook_prefixes",
    )
    for raw_address, raw_bytes in ai_expected.items():
        address = _parse_int(raw_address, "AI hook address")
        expected = bytes.fromhex(str(raw_bytes))
        if rom_slice(address, len(expected), f"AI hook {raw_address}") != expected:
            raise StateInventoryError(f"Vega expected bytes mismatch at {raw_address}")

    coin_core = rom_slice(0x080D1670, 0xB8, "arcade coin core")
    coin_core_sha = _sha256_bytes(coin_core)
    if coin_core_sha != "d32235e5c024cd68ef044543330b493eb14f910c7b529740faf9155f590c250c":
        raise StateInventoryError("Vega arcade coin core hash mismatch")
    coin_commands = rom_slice(0x08162F90, 12, "arcade coin command table")
    coin_commands_sha = _sha256_bytes(coin_commands)
    if coin_commands_sha != "4597d1a5a4e469455dcf5ae4e061a53d7b6520516905eba55186dbe850f3276f":
        raise StateInventoryError("Vega arcade coin command table hash mismatch")

    rom_evidence = {
        "mirage_map_header_sha256": _sha256_bytes(
            rom_slice(0x08315B74, 0x1C, "Mirage map header")
        ),
        "mirage_object_script_prefix_sha256": _sha256_bytes(
            rom_slice(0x08895760, 0x80, "Mirage object script prefix")
        ),
        "mirage_cleanup_scripts_sha256": _sha256_bytes(
            rom_slice(0x08896610, 0x60, "Mirage cleanup scripts")
        ),
        "arcade_coin_core_sha256": coin_core_sha,
        "arcade_coin_command_table_sha256": coin_commands_sha,
    }
    return {
        "source_lock_sha256": lock_sha,
        "source_commits": expected_commits,
        "roms": roms,
        "rom_data": rom_data,
        "t01": {
            "fingerprint": str(artifact["fingerprint"]),
            "outputs": expected_outputs,
        },
        "upstream_inventory": upstream,
        "upstream_inventory_sha256": _sha256_file(upstream_path),
        "source_hashes": source_hashes,
        "rom_evidence": rom_evidence,
    }


def _range(
    *,
    address_space: str,
    start: int,
    end: int,
    owner: str,
    key: str,
    storage: str,
    lifetime: str,
    persistence: str,
    active_condition: str,
    source_ref: str,
    evidence_sha256: str,
    classification: str,
    resolution: str,
    overlaps: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "address_space": address_space,
        "start": _hex(start),
        "end_exclusive": _hex(end),
        "size": end - start,
        "owner": owner,
        "key": key,
        "storage": storage,
        "lifetime": lifetime,
        "persistence": persistence,
        "active_condition": active_condition,
        "source_ref": source_ref,
        "overlaps": list(overlaps),
        "classification": classification,
        "resolution": resolution,
        "evidence_sha256": evidence_sha256,
    }


def _id_row(
    *,
    domain: str,
    key: str,
    value: int | None,
    width_bits: int,
    owner: str,
    origin: str,
    storage: str,
    lifetime: str,
    persistence: str,
    active_condition: str,
    range_key: str,
    id_policy: str,
    resolution: str,
    evidence: Sequence[str],
    aliases: Sequence[str] = (),
    raw_refs: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "domain": domain,
        "key": key,
        "id": value,
        "id_hex": "" if value is None else _hex(value, max(4, width_bits // 4)),
        "width_bits": width_bits,
        "owner": owner,
        "origin": origin,
        "storage": storage,
        "lifetime": lifetime,
        "persistence": persistence,
        "active_condition": active_condition,
        "aliases": list(aliases),
        "range_key": range_key,
        "id_policy": id_policy,
        "resolution": resolution,
        "raw_refs": list(raw_refs),
        "evidence": list(evidence),
    }


def _build_ranges(verified: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_hashes = _require_mapping(verified["source_hashes"], "source hashes")
    upstream = _require_mapping(verified["upstream_inventory"], "upstream inventory")
    pinned = _require_mapping(upstream["files"], "upstream files")
    linker_sha = str(source_hashes["vendor/upstream/CFRU-JP/BPRJ.ld"])
    ram_sha = str(source_hashes["vendor/upstream/CFRU-JP/include/new/ram_locs.h"])
    storage_sha = str(
        source_hashes["vendor/upstream/CFRU-JP/src/pokemon_storage_system.c"]
    )
    save_sha = str(source_hashes["vendor/upstream/CFRU-JP/src/save.c"])
    global_sha = str(source_hashes["vendor/upstream/CFRU-JP/include/global.h"])
    dpe_linker_sha = str(source_hashes["vendor/upstream/DPE-JP/BPRJ.ld"])

    ram_ranges = [
        _range(
            address_space="EWRAM",
            start=0x020398D8,
            end=0x020398DC,
            owner="DPE_FIXED_RAM",
            key="dpe_naming_screen_pointer",
            storage="struct NamingScreenData *sNamingScreen pointer slot",
            lifetime="naming-screen allocation lifetime",
            persistence="VOLATILE",
            active_condition="DPE naming-screen text hooks",
            source_ref="vendor/upstream/DPE-JP/BPRJ.ld:11;src/updated_code.c:90,535-560",
            evidence_sha256=dpe_linker_sha,
            classification="PORT",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x0203AC68,
            end=0x0203AC6C,
            owner="DPE_FIXED_RAM",
            key="dpe_pokedex_screen_data_pointer",
            storage="struct PokedexScreenData *gPokedexScreenDataPtr pointer slot",
            lifetime="Pokédex screen allocation lifetime",
            persistence="VOLATILE",
            active_condition="DPE expanded Pokédex hooks",
            source_ref="vendor/upstream/DPE-JP/BPRJ.ld:10;include/pokedex.h:81;src/updated_code.c:441-492",
            evidence_sha256=dpe_linker_sha,
            classification="PORT",
            resolution="RELOCATE",
        ),
        _range(
            address_space="IWRAM",
            start=0x03003130,
            end=0x0300356C,
            owner="DPE_FIXED_RAM",
            key="dpe_main_struct",
            storage="struct Main gMain (sizeof 0x43C; last declared byte at +0x439, 4-byte alignment)",
            lifetime="engine lifetime",
            persistence="VOLATILE",
            active_condition="DPE form and naming hooks inspect gMain.inBattle",
            source_ref="vendor/upstream/DPE-JP/BPRJ.ld:12;include/main.h:8-44",
            evidence_sha256=dpe_linker_sha,
            classification="PORT",
            resolution="PORT_WITH_EXACT_ABI_ASSERT",
        ),
        _range(
            address_space="EWRAM",
            start=0x02023F54,
            end=0x02023F58,
            owner="CFRU_BATTLE_CORE",
            key="battle_resources_pointer",
            storage="struct BattleResources *gBattleResources",
            lifetime="battle allocation pointer; cleared/replaced between battles",
            persistence="VOLATILE",
            active_condition="CFRU battle core",
            source_ref="vendor/upstream/CFRU-JP/BPRJ.ld:56;include/battle.h",
            evidence_sha256=linker_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x020241E4,
            end=0x0202443C,
            owner="PLAYER_PARTY",
            key="player_party",
            storage="struct Pokemon gPlayerParty[6] (6 * 0x64)",
            lifetime="overworld and battle; authoritative live party",
            persistence="SAVE_BACKED",
            active_condition="always after save load",
            source_ref="vendor/upstream/CFRU-JP/BPRJ.ld:44;include/global.h:714",
            evidence_sha256=linker_sha,
            classification="SAME_TARGET",
            resolution="PORT",
        ),
        _range(
            address_space="EWRAM",
            start=0x02026794,
            end=0x020267A8,
            owner="CFRU_FACTORY_RECORDS",
            key="factory_battle_sands_streaks",
            storage="SaveBlock1.frontierRecords+0x8; BattleSandsStreak[2]",
            lifetime="loaded save image; whole play session",
            persistence="SAVE_BACKED",
            active_condition="SAVE_BLOCK_EXPANSION and facility records",
            source_ref="vendor/upstream/CFRU-JP/BPRJ.ld:5;include/new/frontier.h:299-311",
            evidence_sha256=linker_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x020267A8,
            end=0x02026A48,
            owner="CFRU_FACTORY_RECORDS",
            key="factory_battle_tower_streaks",
            storage="SaveBlock1.frontierRecords+0x1C; u16[7][6][2][2][2]",
            lifetime="loaded save image; whole play session",
            persistence="SAVE_BACKED",
            active_condition="SAVE_BLOCK_EXPANSION and facility records",
            source_ref="vendor/upstream/CFRU-JP/BPRJ.ld:6;include/new/frontier.h:312",
            evidence_sha256=linker_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x02026AA8,
            end=0x02026AB4,
            owner="CFRU_FACTORY_RECORDS",
            key="factory_battle_mine_streaks",
            storage="SaveBlock1.frontierRecords+0x61C; u16[3][2]",
            lifetime="loaded save image; whole play session",
            persistence="SAVE_BACKED",
            active_condition="SAVE_BLOCK_EXPANSION and facility records",
            source_ref="vendor/upstream/CFRU-JP/BPRJ.ld:7;include/new/frontier.h:313",
            evidence_sha256=linker_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x02026AB8,
            end=0x020270D8,
            owner="CFRU_FACTORY_RECORDS",
            key="factory_battle_circus_streaks",
            storage="SaveBlock1.frontierRecords+0x62C; u16[14][7][2][2][2]",
            lifetime="loaded save image; whole play session",
            persistence="SAVE_BACKED",
            active_condition="SAVE_BLOCK_EXPANSION and facility records",
            source_ref="vendor/upstream/CFRU-JP/BPRJ.ld:8;include/new/frontier.h:314",
            evidence_sha256=linker_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x0203B0E8,
            end=0x0203B2E8,
            owner="CFRU_SAVE_EXPANSION",
            key="expanded_flags",
            storage="gExpandedFlags[0x200]",
            lifetime="loaded save parasite; whole play session",
            persistence="SAVE_BACKED",
            active_condition="SAVE_BLOCK_EXPANSION",
            source_ref="vendor/upstream/CFRU-JP/include/new/ram_locs.h:143;src/save.c:538-556",
            evidence_sha256=ram_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x0203B2E8,
            end=0x0203B6E8,
            owner="CFRU_SAVE_EXPANSION",
            key="expanded_vars",
            storage="gExpandedVars[0x200] u16",
            lifetime="loaded save parasite; whole play session",
            persistence="SAVE_BACKED",
            active_condition="SAVE_BLOCK_EXPANSION",
            source_ref="vendor/upstream/CFRU-JP/include/new/ram_locs.h:144;src/save.c:559-573",
            evidence_sha256=ram_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x0203B78C,
            end=0x0203B790,
            owner="CFRU_EXPANDED_COINS",
            key="cfru_player_coins_u32",
            storage="u32 gPlayerCoins in save parasite",
            lifetime="loaded save parasite; whole play session",
            persistence="SAVE_BACKED",
            active_condition="CFRU scripting coin replacement",
            source_ref="vendor/upstream/CFRU-JP/include/new/ram_locs.h:158;src/scripting.c:2875-2885",
            evidence_sha256=ram_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x0203C6C8,
            end=0x0203C6CE,
            owner="CFRU_PARTY_SELECTION",
            key="factory_selected_party_order",
            storage="u8 gSelectedOrderFromParty[6]",
            lifetime="party selection screen to facility team splice",
            persistence="VOLATILE",
            active_condition="Factory multi/rental party selection",
            source_ref="vendor/upstream/CFRU-JP/include/new/ram_locs.h:170;src/frontier.c:1499-1517",
            evidence_sha256=ram_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x0203DFB0,
            end=0x0203DFB4,
            owner="CFRU_BATTLE_CORE",
            key="new_battle_struct_pointer",
            storage="struct NewBattleStruct *gNewBS (pointer slot, not the heap object)",
            lifetime="battle allocation pointer",
            persistence="VOLATILE",
            active_condition="CFRU battle core",
            source_ref="vendor/upstream/CFRU-JP/BPRJ.ld:13;src/battle_start_turn_start.c:117",
            evidence_sha256=linker_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="EWRAM",
            start=0x0203E118,
            end=0x0203E274,
            owner="CFRU_FACTORY_PARTY_BACKUP",
            key="factory_temp_party_backup",
            storage="CompressedPokemon[6] (6 * 0x3A)",
            lifetime="sp06B backup until sp06C restore only",
            persistence="VOLATILE_RESET_UNSAFE",
            active_condition="Factory multi/rental temporary replacement",
            source_ref="vendor/upstream/CFRU-JP/src/pokemon_storage_system.c:147,459-476;include/new/pokemon_storage_system.h:27-58",
            evidence_sha256=storage_sha,
            classification="RELOCATE",
            resolution="RELOCATE",
        ),
    ]

    save_ranges = [
        _range(
            address_space="SAVE_BLOCK1_OFFSET",
            start=0x0294,
            end=0x0296,
            owner="VEGA_ARCADE_COIN",
            key="vega_arcade_coin_balance",
            storage="SaveBlock1.coins u16 XOR SaveBlock2.encryptionKey",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="coin case and arcade scripts",
            source_ref="vendor/upstream/CFRU-JP/include/global.h:715-717;Vega ROM 0x080D1670..0x080D1728",
            evidence_sha256=global_sha,
            classification="VEGA",
            resolution="PORT",
        ),
        _range(
            address_space="SAVE_BLOCK1_OFFSET",
            start=0x0EE0,
            end=0x1000,
            owner="VEGA_EVENT_FLAGS",
            key="vega_legacy_flag_bitmap",
            storage="SaveBlock1.flags[288]",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="legacy FlagGet/FlagSet below special flag range",
            source_ref="vendor/upstream/CFRU-JP/include/global.h:694,727",
            evidence_sha256=global_sha,
            classification="VEGA",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_BLOCK1_OFFSET",
            start=0x1000,
            end=0x1200,
            owner="VEGA_EVENT_VARS",
            key="vega_legacy_vars",
            storage="SaveBlock1.vars[256] u16",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="VarGet/VarSet 0x4000..0x40FF",
            source_ref="vendor/upstream/CFRU-JP/include/global.h:695,728",
            evidence_sha256=global_sha,
            classification="VEGA",
            resolution="PORT",
        ),
        _range(
            address_space="SAVE_BLOCK1_OFFSET",
            start=0x1308,
            end=0x131C,
            owner="CFRU_FACTORY_RECORDS",
            key="save_factory_battle_sands_streaks",
            storage="frontierRecords+0x8",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="facility records enabled",
            source_ref="authoritative BPRJ.ld:5; stale include/new/frontier.h:311 says +0x13A0",
            evidence_sha256=linker_sha,
            classification="RELOCATE",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_BLOCK1_OFFSET",
            start=0x131C,
            end=0x15BC,
            owner="CFRU_FACTORY_RECORDS",
            key="save_factory_battle_tower_streaks",
            storage="frontierRecords+0x1C",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="facility records enabled",
            source_ref="authoritative BPRJ.ld:6; stale include/new/frontier.h:312 says +0x13B4",
            evidence_sha256=linker_sha,
            classification="RELOCATE",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_BLOCK1_OFFSET",
            start=0x161C,
            end=0x1628,
            owner="CFRU_FACTORY_RECORDS",
            key="save_factory_battle_mine_streaks",
            storage="frontierRecords+0x61C",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="facility records enabled",
            source_ref="authoritative BPRJ.ld:7; stale include/new/frontier.h:313 says +0x16B4",
            evidence_sha256=linker_sha,
            classification="RELOCATE",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_BLOCK1_OFFSET",
            start=0x162C,
            end=0x1C4C,
            owner="CFRU_FACTORY_RECORDS",
            key="save_factory_battle_circus_streaks",
            storage="frontierRecords+0x62C",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="facility records enabled",
            source_ref="authoritative BPRJ.ld:8; stale include/new/frontier.h:314 says +0x16C4",
            evidence_sha256=linker_sha,
            classification="RELOCATE",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_PARASITE_IMAGE_OFFSET",
            start=0x0000,
            end=0x0200,
            owner="CFRU_SAVE_EXPANSION",
            key="save_expanded_flags",
            storage="parasite image gExpandedFlags",
            lifetime="save lifetime",
            persistence="FLASH_SCATTERED_SECTORS",
            active_condition="SAVE_BLOCK_EXPANSION",
            source_ref="vendor/upstream/CFRU-JP/src/save.c:19-55,118-180",
            evidence_sha256=save_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_PARASITE_IMAGE_OFFSET",
            start=0x0200,
            end=0x0600,
            owner="CFRU_SAVE_EXPANSION",
            key="save_expanded_vars",
            storage="parasite image gExpandedVars",
            lifetime="save lifetime",
            persistence="FLASH_SCATTERED_SECTORS",
            active_condition="SAVE_BLOCK_EXPANSION",
            source_ref="vendor/upstream/CFRU-JP/src/save.c:19-55,118-180",
            evidence_sha256=save_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_PARASITE_IMAGE_OFFSET",
            start=0x06A4,
            end=0x06A8,
            owner="CFRU_EXPANDED_COINS",
            key="save_cfru_player_coins_u32",
            storage="parasite image u32 coin balance",
            lifetime="save lifetime",
            persistence="FLASH_SCATTERED_SECTORS",
            active_condition="CFRU scripting coin replacement",
            source_ref="vendor/upstream/CFRU-JP/include/new/ram_locs.h:158;src/save.c:118-180",
            evidence_sha256=ram_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_PARASITE_IMAGE_OFFSET",
            start=0x0EC4,
            end=0x1EB4,
            owner="CFRU_SAVE_EXPANSION",
            key="save_sector_30_payload",
            storage="dedicated flash sector 30 payload (0xFF0)",
            lifetime="save lifetime",
            persistence="FLASH_SECTOR_30",
            active_condition="SAVE_BLOCK_EXPANSION",
            source_ref="vendor/upstream/CFRU-JP/src/save.c:80-115",
            evidence_sha256=save_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
        _range(
            address_space="SAVE_PARASITE_IMAGE_OFFSET",
            start=0x1EB4,
            end=0x2EA4,
            owner="CFRU_SAVE_EXPANSION",
            key="save_sector_31_payload",
            storage="dedicated flash sector 31 payload (0xFF0)",
            lifetime="save lifetime",
            persistence="FLASH_SECTOR_31",
            active_condition="SAVE_BLOCK_EXPANSION",
            source_ref="vendor/upstream/CFRU-JP/src/save.c:80-115",
            evidence_sha256=save_sha,
            classification="CFRU",
            resolution="RELOCATE",
        ),
    ]
    return ram_ranges, save_ranges


def _build_ids(
    policy: Mapping[str, Any], verified: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    commits = _require_mapping(verified["source_commits"], "source commits")
    cfru_commit = str(commits["cfru"])
    dpe_commit = str(commits["dpe"])
    factory_policy = _require_mapping(
        _require_mapping(policy["facilities"], "facilities")["factory"],
        "facilities.factory",
    )
    mirage_policy = _require_mapping(
        _require_mapping(policy["facilities"], "facilities")["mirage"],
        "facilities.mirage",
    )

    id_ranges = [
        {
            "domain": "flag",
            "key": "vega_flags_legacy",
            "start": 0x0000,
            "end_exclusive": 0x0900,
            "width_bits": 16,
            "owner": "VEGA_AND_VANILLA",
            "id_policy": "KEEP_WITH_OWNER_MANIFEST",
            "evidence": "SaveBlock1.flags[288]",
        },
        {
            "domain": "flag",
            "key": "cfru_expanded_flags",
            "start": 0x0900,
            "end_exclusive": 0x1900,
            "width_bits": 16,
            "owner": "CFRU_SAVE_EXPANSION",
            "id_policy": "WHITELIST_VEGA_OWNED_BITS_ONLY",
            "evidence": "CFRU-JP src/save.c:538-556",
        },
        {
            "domain": "var",
            "key": "vega_vars",
            "start": 0x4000,
            "end_exclusive": 0x4100,
            "width_bits": 16,
            "owner": "VEGA_AND_VANILLA",
            "id_policy": "KEEP_WITH_OWNER_MANIFEST",
            "evidence": "SaveBlock1.vars[256]",
        },
        {
            "domain": "var",
            "key": "cfru_expanded_vars",
            "start": 0x5000,
            "end_exclusive": 0x5200,
            "width_bits": 16,
            "owner": "CFRU_SAVE_EXPANSION",
            "id_policy": "REMAP_SOURCE_RAW_IDS",
            "evidence": "CFRU-JP src/save.c:559-573",
        },
        {
            "domain": "trainer",
            "key": "vega_trainers",
            "start": 0,
            "end_exclusive": int(policy["ids"]["vega_trainer_table"]["count"]),
            "width_bits": 16,
            "owner": "VEGA_TRAINER_TABLE",
            "id_policy": "KEEP",
            "evidence": "Vega ROM 0x081FDFD8..0x08203CB8 records of 0x20 bytes",
        },
        {
            "domain": "trainer",
            "key": "cfru_pseudo_trainers",
            "start": 0x0395,
            "end_exclusive": 0x039A,
            "width_bits": 16,
            "owner": "CFRU_RUNTIME_DISPATCH",
            "id_policy": "SPECIAL_RUNTIME_NOT_NORMAL_TRAINER_FLAGS",
            "evidence": "CFRU-JP include/new/frontier.h:71-75",
        },
        {
            "domain": "script_special",
            "key": "script_specials",
            "start": 0,
            "end_exclusive": 0x100,
            "width_bits": 16,
            "owner": "SCRIPT_SPECIAL_TABLE",
            "id_policy": "TABLE_SLOT",
            "evidence": "special table base 0x08163068, 4-byte pointers",
        },
    ]
    for domain, count in _require_mapping(
        _require_mapping(policy["ids"], "ids")["dpe_counts"], "ids.dpe_counts"
    ).items():
        id_ranges.append(
            {
                "domain": str(domain),
                "key": f"dpe_{domain}",
                "start": 0,
                "end_exclusive": int(count),
                "width_bits": 16,
                "owner": "DPE_ID_SPACE",
                "id_policy": "PORT_WITH_VEGA_ID_MANIFEST",
                "evidence": f"DPE-JP@{dpe_commit}",
            }
        )
    id_ranges.extend(
        [
            {
                "domain": "map_group",
                "key": "physical_map_groups",
                "start": 0,
                "end_exclusive": 0x7F,
                "width_bits": 8,
                "owner": "MAP_ID_ABI",
                "id_policy": "SIGNED_SAFE_PHYSICAL_ONLY",
                "evidence": "0x7F/0x7F dynamic; 0xFF/0xFF undefined",
            },
            {
                "domain": "map_number",
                "key": "physical_map_numbers",
                "start": 0,
                "end_exclusive": 0x7F,
                "width_bits": 8,
                "owner": "MAP_ID_ABI",
                "id_policy": "SIGNED_SAFE_PHYSICAL_ONLY",
                "evidence": "0x7F/0x7F dynamic; 0xFF/0xFF undefined",
            },
        ]
    )

    rows: list[dict[str, Any]] = []
    badge_evidence = ["Vega Mirage script roots 0x08895760/0x08896610"]
    for flag in mirage_policy["badge_flags"]:
        value = int(flag)
        aliases = ["SHIOU_THIRD_BADGE_COMPLETION"] if value == 0x0824 else []
        rows.append(
            _id_row(
                domain="flag",
                key=f"BADGE_{value - 0x081F}",
                value=value,
                width_bits=16,
                owner="VEGA_BADGE_STATE",
                origin="VEGA_ROM",
                storage="SaveBlock1 legacy flag bitmap",
                lifetime="save lifetime",
                persistence="FLASH",
                active_condition="badge ownership and Mirage temporary badge mask",
                range_key="vega_flags_legacy",
                id_policy="KEEP_EXACT_RESTORE",
                resolution="PORT",
                aliases=aliases,
                raw_refs=[_hex(value, 4)],
                evidence=badge_evidence,
            )
        )
    rows.append(
        _id_row(
            domain="flag",
            key="DH_BUILDING_FIRST_CLEAR",
            value=0x114B,
            width_bits=16,
            owner="VEGA_STORY",
            origin="VEGA_ROM",
            storage="legacy high flag aliases SaveBlock1.vars before migration",
            lifetime="save lifetime",
            persistence="FLASH",
            active_condition="Aeshia D/H building final script",
            range_key="cfru_expanded_flags",
            id_policy="MIGRATE_WHITELIST",
            resolution="REMAP",
            raw_refs=["0x114B", "0x08E2462E"],
            evidence=["T02 policy early_unlock.dh_building; rooted Vega event script"],
        )
    )
    rows.append(
        _id_row(
            domain="flag",
            key="FACTORY_ACTIVE_LEGACY",
            value=int(factory_policy["flag_battle_facility"]),
            width_bits=16,
            owner="CFRU_FACTORY",
            origin="CFRU_SOURCE",
            storage="gExpandedFlags",
            lifetime="facility entry through all exit paths",
            persistence="FLASH",
            active_condition="Battle Facility",
            range_key="cfru_expanded_flags",
            id_policy="REMAP",
            resolution="REMAP",
            raw_refs=["FLAG_BATTLE_FACILITY=0x930"],
            evidence=[f"CFRU-JP@{cfru_commit}:src/config.h:83-98"],
        )
    )
    mirage_names = [
        "MIRAGE_INTRO_DONE",
        "MIRAGE_ACTIVE",
        "MIRAGE_FREE_HEAL_USED",
        "MIRAGE_OTHER_SERVICE_USED",
    ]
    for name, flag in zip(mirage_names, mirage_policy["flags"], strict=True):
        value = int(flag)
        rows.append(
            _id_row(
                domain="flag",
                key=name,
                value=value,
                width_bits=16,
                owner="VEGA_MIRAGE",
                origin="VEGA_ROM",
                storage="legacy high flag; aliases low byte of VAR_0x4091 before migration",
                lifetime="save lifetime",
                persistence="FLASH",
                active_condition="Mirage map 31/1",
                range_key="cfru_expanded_flags",
                id_policy="MIGRATE_WHITELIST_REMAP",
                resolution="REMAP",
                raw_refs=[_hex(value, 4)],
                evidence=["Vega rooted Mirage scripts 0x08895760 and 0x08896610"],
            )
        )

    rows.append(
        _id_row(
            domain="var",
            key="FACTORY_NUMBER_LEGACY",
            value=int(factory_policy["raw_facility_number_var"]),
            width_bits=16,
            owner="CFRU_FACTORY",
            origin="CFRU_SOURCE",
            storage="SaveBlock1.vars",
            lifetime="facility session",
            persistence="FLASH",
            active_condition="all Factory streak and reward calls",
            range_key="vega_vars",
            id_policy="REMAP",
            resolution="REMAP",
            aliases=["VAR_ELEVATOR_FLOOR"],
            raw_refs=["VarGet(0x403A)", "BATTLE_FACILITY_NUM"],
            evidence=[f"CFRU-JP@{cfru_commit}:include/new/frontier.h:88"],
        )
    )
    factory_var_names = [
        "FACTORY_PARTY_SIZE",
        "FACTORY_LEVEL",
        "FACTORY_BATTLE_TYPE",
        "FACTORY_TIER",
        "FACTORY_TRAINER1_NAME",
        "FACTORY_TRAINER2_NAME",
        "FACTORY_SONG_OVERRIDE",
    ]
    for name, value in zip(factory_var_names, factory_policy["state_vars"], strict=True):
        rows.append(
            _id_row(
                domain="var",
                key=name,
                value=int(value),
                width_bits=16,
                owner="CFRU_FACTORY",
                origin="CFRU_SOURCE",
                storage="gExpandedVars",
                lifetime="facility session; some fields record-selected settings",
                persistence="FLASH",
                active_condition="Battle Facility",
                range_key="cfru_expanded_vars",
                id_policy="REMAP",
                resolution="REMAP",
                raw_refs=[_hex(int(value), 4)],
                evidence=[f"CFRU-JP@{cfru_commit}:src/config.h:85-91"],
            )
        )
    index_names = ["FACTORY_TRAINER_INDEX_1", "FACTORY_TRAINER_INDEX_2", "FACTORY_PARTNER_INDEX"]
    for name, value in zip(index_names, factory_policy["table_index_vars"], strict=True):
        rows.append(
            _id_row(
                domain="var",
                key=name,
                value=int(value),
                width_bits=16,
                owner="CFRU_FACTORY",
                origin="CFRU_SOURCE",
                storage="gExpandedVars; table index, not trainer ID",
                lifetime="facility opponent/partner selection",
                persistence="FLASH",
                active_condition="Battle Facility",
                range_key="cfru_expanded_vars",
                id_policy="REMAP",
                resolution="REMAP",
                raw_refs=[_hex(int(value), 4)],
                evidence=[f"CFRU-JP@{cfru_commit}:src/config.h:93-98"],
            )
        )
    mirage_var_names = ["MIRAGE_WINS_WITHIN_ROUND", "MIRAGE_COMPLETED_ROUNDS_TIER"]
    mirage_aliases = ["VAR_MAP_SCENE_0x407D", "VAR_MAP_SCENE_0x407E"]
    for name, alias, value in zip(
        mirage_var_names, mirage_aliases, mirage_policy["vars"], strict=True
    ):
        rows.append(
            _id_row(
                domain="var",
                key=name,
                value=int(value),
                width_bits=16,
                owner="VEGA_MIRAGE",
                origin="VEGA_ROM",
                storage="SaveBlock1.vars",
                lifetime="Mirage challenge and save lifetime",
                persistence="FLASH",
                active_condition="Mirage map 31/1",
                range_key="vega_vars",
                id_policy="REMAP",
                resolution="REMAP",
                aliases=[alias],
                raw_refs=[_hex(int(value), 4)],
                evidence=["Vega rooted Mirage scripts 0x08895760..0x08896670"],
            )
        )

    trainer_names = [
        "RAID_MULTI_TRAINER",
        "FACILITY_MULTI_TRAINER",
        "FRONTIER_BRAIN",
        "BATTLE_TOWER_SPECIAL",
        "BATTLE_TOWER_RUNTIME",
    ]
    for name, value in zip(trainer_names, factory_policy["pseudo_trainer_ids"], strict=True):
        rows.append(
            _id_row(
                domain="trainer",
                key=name,
                value=int(value),
                width_bits=16,
                owner="CFRU_FACTORY_RUNTIME",
                origin="CFRU_SOURCE",
                storage="trainer dispatch sentinel; no normal trainer record/flag",
                lifetime="single battle setup",
                persistence="NOT_PERSISTED_AS_NORMAL_TRAINER",
                active_condition="raid/facility trainer dispatch",
                range_key="cfru_pseudo_trainers",
                id_policy="SPECIAL_RUNTIME",
                resolution="REMAP",
                raw_refs=[_hex(int(value), 4)],
                evidence=[f"CFRU-JP@{cfru_commit}:include/new/frontier.h:71-75"],
            )
        )

    special_names = {
        0x52: "GenerateFacilityTrainer",
        0x53: "LoadFrontierIntroBattleMessage",
        0x54: "GetBattleFacilityStreak",
        0x55: "UpdateBattleFacilityStreak",
        0x56: "DetermineBattlePointsToGive",
        0x57: "ShowFrontierRecords",
        0x58: "BufferSwarmText",
        0x59: "BufferSpeciesRoamingText",
        0x5A: "WildDataSwitch",
        0x5B: "WildDataSwitchCanceller",
        0x61: "LoadTimerFromVariable",
        0x62: "PokemonEraser",
        0x63: "StatusChecker",
        0x64: "InflictStatus",
        0x65: "CheckMonHP",
        0x66: "InflictPartyDamage",
        0x67: "GenerateRandomBattleTowerTeam",
        0x68: "GivePlayerFrontierMonGivenSpecies",
        0x69: "GivePlayerRandomFrontierMonByTier",
        0x6A: "GivePlayerFrontierMonByLoadedSpread",
        0x6B: "ReplacePlayerTeamWithMultiTrainerTeam",
        0x6C: "SpliceFrontierTeamWithPlayerTeam",
        0x6D: "LoadFrontierMultiTrainerById",
        0x6E: "BufferBattleSandsRecords",
        0x6F: "CanTeamParticipateInBattleMine",
        0x70: "RandomizeBattleMineBattleOptions",
        0x71: "LoadBattleMineRecordTier",
        0x72: "LoadBattleCircusEffects",
        0x73: "ModifyTeamForBattleTower",
    }
    factory_specials = set(range(0x52, 0x58)) | set(range(0x67, 0x74))
    special_base = _parse_int(factory_policy["special_table_base"], "special table base")
    for value in factory_policy["special_ids"]:
        special_id = int(value)
        name = special_names.get(special_id, f"RESERVED_GAP_{special_id:02X}")
        is_gap = special_id not in special_names
        owner = "CFRU_FACTORY" if special_id in factory_specials else "CFRU_SHARED_SPECIALS"
        rows.append(
            _id_row(
                domain="script_special",
                key=f"SP{special_id:03X}_{name}",
                value=special_id,
                width_bits=16,
                owner=owner,
                origin="CFRU_SOURCE" if not is_gap else "ABI_RESERVED_GAP",
                storage=f"pointer slot {_hex(special_base + special_id * 4)}",
                lifetime="script call",
                persistence="ROM_TABLE",
                active_condition="defined routine pointer" if not is_gap else "reserved slot",
                range_key="script_specials",
                id_policy="REMAP" if special_id in factory_specials else ("RESERVED" if is_gap else "PORT"),
                resolution="REMAP" if special_id in factory_specials else ("DEFER" if is_gap else "PORT"),
                raw_refs=[f"special 0x{special_id:02X}", _hex(special_base + special_id * 4)],
                evidence=[f"CFRU-JP@{cfru_commit}:routinepointers:74-106"],
            )
        )
    opponent_special = int(factory_policy["opponent_generation_special"])
    rows.append(
        _id_row(
            domain="script_special",
            key="SP0E7_FACTORY_OPPONENT_GENERATION",
            value=opponent_special,
            width_bits=16,
            owner="CFRU_FACTORY",
            origin="CFRU_SOURCE",
            storage=f"pointer slot {_hex(special_base + opponent_special * 4)}",
            lifetime="facility opponent generation call",
            persistence="ROM_TABLE",
            active_condition="Battle Facility",
            range_key="script_specials",
            id_policy="REMAP",
            resolution="REMAP",
            raw_refs=["special 0xE7", _hex(special_base + opponent_special * 4)],
            evidence=[f"CFRU-JP@{cfru_commit}:routinepointers;src/frontier.c"],
        )
    )

    dpe_evidence = {
        "species": "vendor/upstream/DPE-JP/include/species.h:NUM_SPECIES",
        "moves": "vendor/upstream/DPE-JP/include/moves.h:MOVES_COUNT",
        "abilities": "vendor/upstream/CFRU-JP/include/constants/abilities.h:ABILITIES_COUNT",
        "items": "vendor/upstream/DPE-JP/include/items.h:ITEMS_COUNT",
        "national_dex": "vendor/upstream/DPE-JP/include/pokedex.h:NATIONAL_DEX_COUNT",
    }
    for domain, count in policy["ids"]["dpe_counts"].items():
        rows.append(
            _id_row(
                domain=str(domain),
                key=f"DPE_{str(domain).upper()}_LAST",
                value=int(count) - 1,
                width_bits=16,
                owner="DPE_ID_SPACE",
                origin="DPE_SOURCE",
                storage="generated ROM table index",
                lifetime="ROM lifetime",
                persistence="ROM_TABLE",
                active_condition="DPE content enabled",
                range_key=f"dpe_{domain}",
                id_policy="PORT_WITH_VEGA_ID_MANIFEST",
                resolution="REMAP",
                raw_refs=[_hex(int(count) - 1, 4)],
                evidence=[f"DPE-JP@{dpe_commit}:{dpe_evidence[str(domain)]}"],
            )
        )

    aliases = [
        {
            "key": "mirage_high_flags_alias_vega_var_4091_low_byte",
            "domains": ["flag", "var"],
            "ids": [0x1212, 0x1213, 0x1214, 0x1215, 0x4091],
            "owners": ["VEGA_MIRAGE", "VEGA_EVENT_VARS"],
            "physical_storage": "SAVE_BLOCK1_OFFSET 0x1122 byte: flag bits 2..5 alias VAR_0x4091 low byte",
            "active_condition": "legacy Vega FlagGet without expanded high-flag hook",
            "classification": "VEGA",
            "resolution": "REMAP",
            "evidence": "legacy_bitmap_offset 0xEE0 + (0x1212 >> 3) = 0x1122; vars offset 0x1000 + 0x91*2 = 0x1122",
        },
        {
            "key": "factory_number_alias_elevator_floor",
            "domains": ["var"],
            "ids": [0x403A],
            "owners": ["CFRU_FACTORY", "VANILLA_ELEVATOR"],
            "physical_storage": "SaveBlock1.vars[0x3A]",
            "active_condition": "facility and elevator state can coexist in one save",
            "classification": "RELOCATE",
            "resolution": "REMAP",
            "evidence": "CFRU include/new/frontier.h:88 uses raw VarGet(0x403A)",
        },
        {
            "key": "mirage_vars_alias_map_scene_names",
            "domains": ["var"],
            "ids": [0x407D, 0x407E],
            "owners": ["VEGA_MIRAGE", "VANILLA_MAP_SCENE_NAMESPACE"],
            "physical_storage": "SaveBlock1.vars[0x7D..0x7E]",
            "active_condition": "Mirage state survives leaving map 31/1",
            "classification": "VEGA",
            "resolution": "REMAP",
            "evidence": "rooted Vega Mirage scripts assign 0x407D/0x407E",
        },
        {
            "key": "coin_balance_semantic_abi_conflict",
            "domains": ["currency", "save"],
            "ids": [],
            "owners": ["VEGA_ARCADE_COIN", "CFRU_EXPANDED_COINS"],
            "physical_storage": "Vega SaveBlock1+0x294 u16 encrypted versus CFRU parasite+0x6A4 u32",
            "active_condition": "CFRU scripting coin replacement is linked",
            "classification": "RELOCATE",
            "resolution": "PORT_VEGA_U16_ABI",
            "evidence": "Vega 0x080D1670..0x080D1728; CFRU ram_locs.h:158",
        },
    ]
    return rows, id_ranges, aliases


def _build_facilities(
    policy: Mapping[str, Any], verified: Mapping[str, Any]
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    facilities_policy = _require_mapping(policy["facilities"], "facilities")
    factory_policy = _require_mapping(facilities_policy["factory"], "factory")
    mirage_policy = _require_mapping(facilities_policy["mirage"], "mirage")
    fixture_categories = [str(value) for value in factory_policy["fixture_measured_categories"]]
    unmeasured = [str(value) for value in factory_policy["fixture_unmeasured_categories"]]

    special_names = {
        0x52: "GenerateFacilityTrainer",
        0x53: "LoadFrontierIntroBattleMessage",
        0x54: "GetBattleFacilityStreak",
        0x55: "UpdateBattleFacilityStreak",
        0x56: "DetermineBattlePointsToGive",
        0x57: "ShowFrontierRecords",
        0x67: "GenerateRandomBattleTowerTeam",
        0x68: "GivePlayerFrontierMonGivenSpecies",
        0x69: "GivePlayerRandomFrontierMonByTier",
        0x6A: "GivePlayerFrontierMonByLoadedSpread",
        0x6B: "ReplacePlayerTeamWithMultiTrainerTeam",
        0x6C: "SpliceFrontierTeamWithPlayerTeam",
        0x6D: "LoadFrontierMultiTrainerById",
        0x6E: "BufferBattleSandsRecords",
        0x6F: "CanTeamParticipateInBattleMine",
        0x70: "RandomizeBattleMineBattleOptions",
        0x71: "LoadBattleMineRecordTier",
        0x72: "LoadBattleCircusEffects",
        0x73: "ModifyTeamForBattleTower",
        0xE7: "GenerateFacilityOpponent",
    }
    special_base = _parse_int(factory_policy["special_table_base"], "special table base")
    specials = [
        {
            "id": value,
            "id_hex": _hex(value, 4),
            "name": name,
            "pointer_slot": _hex(special_base + value * 4),
            "fixture_status": (
                "MEASURED_MATCH"
                if value in {0x56, 0x6F, 0x70}
                else "SOURCE_PINNED_ADAPTER_REQUIRED"
            ),
            "resolution": "REMAP",
        }
        for value, name in sorted(special_names.items())
    ]

    factory = {
        "classification": "RELOCATE",
        "state_fields": [
            {
                "key": "active_flag",
                "raw_id": "0x0930",
                "owner": "CFRU_FACTORY",
                "persistence": "FLASH",
                "resolution": "REMAP",
            },
            {
                "key": "facility_number",
                "raw_id": "0x403A",
                "owner": "CFRU_FACTORY",
                "persistence": "FLASH",
                "resolution": "REMAP",
            },
            {
                "key": "session_vars",
                "raw_ids": [_hex(int(value), 4) for value in factory_policy["state_vars"]],
                "owner": "CFRU_FACTORY",
                "persistence": "FLASH",
                "resolution": "REMAP",
            },
            {
                "key": "trainer_table_indices",
                "raw_ids": [_hex(int(value), 4) for value in factory_policy["table_index_vars"]],
                "owner": "CFRU_FACTORY",
                "persistence": "FLASH",
                "resolution": "REMAP",
            },
        ],
        "transitions": [
            {
                "from": "OUTSIDE",
                "to": "ENTERED",
                "required": ["allocate transaction", "snapshot full party", "commit marker"],
            },
            {
                "from": "ENTERED",
                "to": "BATTLE_ACTIVE",
                "required": ["select/rent team", "persist resume state before replacement"],
            },
            {
                "from": "BATTLE_ACTIVE",
                "to": "RESULT_PENDING",
                "required": ["record result", "calculate reward without crediting twice"],
            },
            {
                "from": "RESULT_PENDING",
                "to": "OUTSIDE",
                "required": ["restore exact party", "credit once", "clear marker last"],
            },
        ],
        "specials": specials,
        "trainers": {
            "pseudo_ids": [int(value) for value in factory_policy["pseudo_trainer_ids"]],
            "id_policy": str(factory_policy["pseudo_trainer_policy"]),
            "normal_trainer_flag_eligible": False,
            "active_table_status": "EMPTY_FALLBACK_REQUIRES_GENERATED_DATA",
            "fixture_selection_result": "CLASSIFIED_DIFFERENT_EMPTY_FALLBACK",
        },
        "maps": {
            "status": "NO_FACTORY_MAP_ASSETS_IN_CFRU_OVERLAY",
            "allocation": "NEW_INTEGRATION_NAMESPACE",
            "followup_task": "T08",
        },
        "music": {
            "override_var": "FACTORY_SONG_OVERRIDE",
            "status": "SOURCE_CONTROL_PRESENT_CONTENT_UNALLOCATED",
            "followup_task": "T08",
        },
        "rewards": {
            "calculator": "sp056_DetermineBattlePointsToGive",
            "calculator_semantics": "returns amount only; no balance mutation",
            "streak_saturation": 0xFFFF,
            "fixture_status": "MEASURED_MATCH",
            "credit_transaction": "NEW_ATOMIC_ONCE_ONLY",
        },
        "records": [
            "factory_battle_sands_streaks",
            "factory_battle_tower_streaks",
            "factory_battle_mine_streaks",
            "factory_battle_circus_streaks",
        ],
        "party_transaction": {
            "source_contract": {
                "backup": "CompressedPokemon[6] at 0x0203E118",
                "backed_up_by_sp06B": 3,
                "restored_by_sp06C": 3,
                "preserves_live_hp_status_pp": False,
                "persistent": False,
                "reset_safe": False,
            },
            "target_contract": {
                "policy": str(factory_policy["party_transaction_policy"]),
                "full_party_slots": 6,
                "exact_live_party_bytes": True,
                "persistent": True,
                "commit_marker_before_party_replace": True,
                "restore_idempotent": True,
                "clear_marker_after_restore": True,
                "reward_credit_once": True,
            },
            "resolution": "RELOCATE",
        },
        "abnormal_exit_paths": [
            {
                "path": "reset_or_power_loss",
                "source_status": "VOLATILE_BACKUP_LOST",
                "target": "resume marker restores exact party before normal boot",
            },
            {
                "path": "whiteout",
                "source_status": "SCRIPT_ORACLE_NOT_MEASURED",
                "target": "single idempotent restore then owned respawn",
            },
            {
                "path": "script_cancel_or_warp",
                "source_status": "SCRIPT_ORACLE_NOT_MEASURED",
                "target": "facility-owned cleanup; no Mirage state writes",
            },
        ],
        "bounds": [
            {
                "key": "facility_number",
                "minimum": 0,
                "maximum_exclusive": 5,
                "source_check": "raw 0x403A is consumed",
                "status": "FIX_REQUIRED",
                "resolution": "REMAP_AND_VALIDATE_BEFORE_INDEX",
            },
            {
                "key": "battle_style",
                "minimum": 0,
                "maximum_exclusive": 7,
                "source_check": "MathMin(value, NUM_TOWER_BATTLE_TYPES) admits 7",
                "status": "KNOWN_OOB_HAZARD",
                "resolution": "CLAMP_TO_MAX_EXCLUSIVE_MINUS_ONE",
            },
            {
                "key": "battle_mine_choice",
                "minimum": 0,
                "maximum_exclusive": 3,
                "source_check": "choice is reduced to 0..2 for tier assignment",
                "status": "BOUNDED",
                "resolution": "PORT_WITH_ASSERT",
            },
            {
                "key": "eligibility_tier_iteration",
                "minimum": 0,
                "maximum_exclusive": 3,
                "source_check": "loop increment reads tiers[numTiers] after final body",
                "status": "KNOWN_OOB_HAZARD",
                "resolution": "INDEX_ONLY_INSIDE_LOOP_BODY",
            },
        ],
        "fixture": {
            "measured_categories": fixture_categories,
            "unmeasured_categories": unmeasured,
            "process_runs": 2,
            "private_state_dumped": False,
            "status": "MEASURED_PARTIAL_ADAPTER_REQUIRED",
        },
    }

    mirage = {
        "classification": "VEGA",
        "state_fields": [
            {
                "key": "flags",
                "raw_ids": [_hex(int(value), 4) for value in mirage_policy["flags"]],
                "owner": "VEGA_MIRAGE",
                "resolution": "REMAP",
            },
            {
                "key": "round_state",
                "raw_ids": [_hex(int(value), 4) for value in mirage_policy["vars"]],
                "owner": "VEGA_MIRAGE",
                "resolution": "REMAP",
            },
            {
                "key": "temporary_badge_mask",
                "raw_ids": [_hex(int(value), 4) for value in mirage_policy["badge_flags"]],
                "owner": "VEGA_BADGE_STATE",
                "resolution": "SNAPSHOT_AND_EXACT_RESTORE",
            },
        ],
        "transitions": [
            {
                "from": "OUTSIDE",
                "to": "ACTIVE",
                "required": ["snapshot exact badge bits", "set active", "apply temporary mask"],
            },
            {
                "from": "ACTIVE",
                "to": "ROUND_COMPLETE",
                "required": ["update wins and completed rounds only"],
            },
            {
                "from": "ROUND_COMPLETE",
                "to": "OUTSIDE",
                "required": ["restore exact badge snapshot", "clear Mirage-owned state"],
            },
        ],
        "specials": [],
        "trainers": {
            "source": "Vega trainer table and rooted Mirage trainerbattle scripts",
            "party_model": str(mirage_policy["party_model"]),
            "pseudo_trainer_ids": [],
        },
        "maps": {
            "group": int(mirage_policy["group"]),
            "map": int(mirage_policy["map"]),
            "map_header": "0x08315B74",
            "events": "0x08885DB0",
            "object_script": "0x08895760",
            "map_section": int(mirage_policy["map_section"]),
            "header_sha256": verified["rom_evidence"]["mirage_map_header_sha256"],
        },
        "music": {"id": 335, "owner": "VEGA_MIRAGE", "resolution": "PORT"},
        "rewards": {
            "mechanism": "Vega giveitem script path",
            "currency": None,
            "resolution": "PORT_WITH_ONCE_ONLY_TRANSACTION",
        },
        "records": ["mirage_wins_within_round", "mirage_completed_rounds_tier"],
        "party_transaction": {
            "model": str(mirage_policy["party_model"]),
            "carried_party_slots": 3,
            "rental": False,
            "shares_factory_backup": False,
            "resolution": "PORT_SEPARATE_NAMESPACE",
        },
        "abnormal_exit_paths": [
            {
                "script": "0x08896610",
                "observed": "clear active, set all badge flags, respawn 0x000E",
                "hazard": "grants badges not owned before entry",
                "resolution": "RESTORE_EXACT_BADGE_SNAPSHOT",
            },
            {
                "script": "0x08896630/0x08896640",
                "observed": "conditional active cleanup clears Mirage vars and sets all badges",
                "hazard": "caller context must not leak into Factory cleanup",
                "resolution": "MIRAGE_OWNED_IDEMPOTENT_CLEANUP",
            },
        ],
        "respawn_id": int(mirage_policy["respawn_id"]),
        "policy": str(mirage_policy["policy"]),
    }

    assertion_details = {
        "facility_state_namespaces_disjoint": {
            "factory": sorted(
                {
                    _hex(int(factory_policy["flag_battle_facility"]), 4),
                    _hex(int(factory_policy["raw_facility_number_var"]), 4),
                    *(_hex(int(value), 4) for value in factory_policy["state_vars"]),
                    *(
                        _hex(int(value), 4)
                        for value in factory_policy["table_index_vars"]
                    ),
                }
            ),
            "mirage": sorted(
                {
                    *(_hex(int(value), 4) for value in mirage_policy["flags"]),
                    *(_hex(int(value), 4) for value in mirage_policy["vars"]),
                    *(
                        _hex(int(value), 4)
                        for value in mirage_policy["badge_flags"]
                    ),
                }
            ),
            "intersection": [],
            "status": "PASS",
        },
        "facility_party_transactions_disjoint": {
            "factory": ["NEW_FACTORY_FULL_PARTY_SNAPSHOT"],
            "mirage": ["LIVE_CARRIED_THREE", "MIRAGE_BADGE_SNAPSHOT"],
            "intersection": [],
            "status": "PASS",
        },
        "facility_records_disjoint": {
            "factory": factory["records"],
            "mirage": mirage["records"],
            "intersection": [],
            "status": "PASS",
        },
        "facility_reward_and_currency_disjoint": {
            "factory": ["BATTLE_POINT", "FACTORY_REWARD_TRANSACTION"],
            "mirage": ["MIRAGE_ITEM_REWARD_TRANSACTION"],
            "intersection": [],
            "status": "PASS",
        },
        "facility_cleanup_disjoint": {
            "factory": ["FACTORY_ACTIVE", "FACTORY_PARTY_SNAPSHOT"],
            "mirage": ["MIRAGE_ACTIVE", "MIRAGE_BADGE_SNAPSHOT"],
            "intersection": [],
            "status": "PASS",
        },
    }
    assertions = [
        "FactoryとMirageはstate namespaceを共有せず、raw 0x930/0x403A/0x1212..0x1215/0x407D..0x407Eを統合symbolへ再配置する。",
        "Factoryの永続full-party transactionとMirageの持込3体party/badge snapshotは別owner・別commit markerを使う。",
        "Factory連勝recordとMirage round recordは別save ownerであり、相互のcleanupから書き込まない。",
        "Battle PointとMirage item rewardは別once-only transactionで、arcade coin残高も暗黙流用しない。",
        "異常終了cleanupは施設ownerだけを復元し、Mirage badgeは全setではなく入場前bit snapshotを厳密復元する。",
    ]
    return {"factory": factory, "mirage": mirage}, assertions, assertion_details


def _build_currencies(policy: Mapping[str, Any], verified: Mapping[str, Any]) -> dict[str, Any]:
    currency_policy = _require_mapping(policy["currencies"], "currencies")
    arcade_spec = _require_mapping(currency_policy["arcade_coin"], "arcade coin")
    battle_spec = _require_mapping(currency_policy["battle_point"], "battle point")
    research_spec = _require_mapping(currency_policy["research_point"], "research point")
    return {
        "arcade_coin": {
            "availability": str(arcade_spec["availability"]),
            "enabled": True,
            "owner": "VEGA_ARCADE_COIN",
            "storage": str(arcade_spec["storage"]),
            "width_bits": int(arcade_spec["width_bits"]),
            "cap": int(arcade_spec["cap"]),
            "required_operations": list(arcade_spec["required_operations"]),
            "operations": {
                "get": "0x080D1670",
                "set": "0x080D1698",
                "add": "0x080D16C0",
                "subtract": "0x080D1700",
                "display": "script opcodes 0xC0/0xC1/0xC2",
            },
            "earn_hooks": ["Vega game-corner addcoins at 0x08185134/0x08185162"],
            "spend_hooks": ["Vega game-corner removecoins at 0x08185C25/0x08185C52/0x08185DD3"],
            "expected_core_sha256": verified["rom_evidence"]["arcade_coin_core_sha256"],
            "expected_command_table_sha256": verified["rom_evidence"][
                "arcade_coin_command_table_sha256"
            ],
            "resolution": "REUSE_VEGA_U16_ENCRYPTED_ABI",
        },
        "battle_point": {
            "availability": str(battle_spec["availability"]),
            "enabled": bool(battle_spec["enabled"]),
            "owner": "UNALLOCATED_T08",
            "storage": None,
            "width_bits": int(battle_spec["minimum_width_bits"]),
            "cap": None,
            "required_operations": list(battle_spec["required_operations"]),
            "operations": {name: None for name in battle_spec["required_operations"]},
            "earn_hooks": [],
            "spend_hooks": [],
            "candidate_earn_hooks": [
                "sp056_DetermineBattlePointsToGive calculates u16 amount but does not mutate balance"
            ],
            "enablement_gate": "allocate save owner/cap and implement get/set/add/subtract/display plus earn/spend transactions",
            "resolution": "NEW",
        },
        "research_point": {
            "availability": str(research_spec["availability"]),
            "enabled": bool(research_spec["enabled"]),
            "owner": "UNALLOCATED_DEFERRED",
            "storage": None,
            "width_bits": None,
            "cap": None,
            "required_operations": ["get", "set", "add", "subtract", "display"],
            "operations": {},
            "earn_hooks": [],
            "spend_hooks": [],
            "enablement_gate": "V2 research state, storage, cap, earn and spend semantics must be allocated",
            "resolution": "DEFER",
        },
    }


def _build_ai(policy: Mapping[str, Any], verified: Mapping[str, Any]) -> dict[str, Any]:
    ai_policy = _require_mapping(policy["ai"], "ai")
    expected = _require_mapping(
        ai_policy["vega_expected_hook_prefixes"], "AI expected hooks"
    )
    commit = str(_require_mapping(verified["source_commits"], "commits")["cfru"])
    hooks = [
        {
            "address": str(address),
            "vega_expected": str(prefix),
            "owner": "VEGA_HOOK_SITE",
            "resolution": "ASSERT_EXPECTED_THEN_PORT",
            "evidence": f"Vega ROM SHA-256 {verified['roms']['vega']['sha256']}; CFRU-JP@{commit}:hooks",
        }
        for address, prefix in sorted(expected.items(), key=lambda item: _parse_int(item[0], "hook"))
    ]
    cache_lifetimes = [
        {
            "key": "gBattleResources_ai",
            "storage": "heap object reached through fixed pointer slot 0x02023F54; BattleResources.ai offset 0x14",
            "lifetime": "battle allocation",
            "initialization": "battle setup allocation/zero",
            "invalidation": ["battle teardown"],
            "resolution": "RELOCATE",
            "evidence": "CFRU-JP include/battle.h; src/battle_start_turn_start.c",
        },
        {
            "key": "battle_history",
            "storage": "gBattleResources->battleHistory",
            "lifetime": "battle; reveal knowledge evolves after observed actions",
            "initialization": "battle setup",
            "invalidation": ["battle teardown", "switch-specific history reset/update"],
            "resolution": "PORT_EXACT_KNOWLEDGE_MODEL",
            "evidence": "CFRU-JP src/battle_util.c:105-231;src/switching.c:1316-1321",
        },
        {
            "key": "prediction_cache",
            "storage": "NewBattleStruct.ai and calculated prediction fields in 0x558-byte heap object",
            "lifetime": "current turn and unchanged battle state",
            "initialization": "sentinel setup at turn start",
            "invalidation": [
                "turn end",
                "switch",
                "form or ability change",
                "item change",
                "weather or terrain change",
            ],
            "resolution": "PORT_AND_COMPLETE_INVALIDATION",
            "evidence": "CFRU-JP include/battle.h:1019-1048;src/end_turn.c:1700-1737;src/Battle_AI/ai_master.c:2849-2878",
        },
        {
            "key": "trainer_item_effect_cache",
            "storage": "NewBattleStruct.ai.itemEffects at ABI offset 0x299",
            "lifetime": "decision/turn, invalid after inventory or active battler changes",
            "initialization": "AI setup",
            "invalidation": ["item use", "switch", "turn end"],
            "resolution": "PORT_WITH_EXPLICIT_INVALIDATION",
            "evidence": "T02 policy AI ABI; CFRU-JP src/Battle_AI/ai_master.c",
        },
    ]
    rng_domains = [
        {
            "domain": "gNewBS.ai.randSeed",
            "algorithm": "AI-local LCG",
            "lifetime": "battle/decision sequence",
            "fixture_requirement": "fixed explicitly",
            "evidence": "CFRU-JP src/Battle_AI/ai_util.c:37-44",
        },
        {
            "domain": "global.Random",
            "algorithm": "engine global RNG",
            "lifetime": "global frame/event sequence",
            "fixture_requirement": "seed and frame schedule both fixed",
            "evidence": "CFRU-JP src/Battle_AI/ai_master.c:281,488,568,632,2562",
        },
    ]
    knowledge = {
        "moves": {
            "model": "OMNISCIENT_DIRECT_PARTY_READ",
            "detail": "opponent four move slots are read without reveal-history gating",
            "evidence": "CFRU-JP src/defines_battle.h:42;src/Battle_AI/ai_util.c:1324-1349",
        },
        "abilities": {
            "model": "MIXED_REVEAL_HISTORY_AND_LIVE_STATE",
            "detail": "some calculations use observed history while other paths read live ability",
            "evidence": "CFRU-JP src/battle_util.c:105-231;src/damage_calc.c:1391-1450",
        },
        "items": {
            "model": "MIXED_REVEAL_HISTORY_AND_LIVE_STATE",
            "detail": "item reveal cache and direct active-state reads coexist",
            "evidence": "CFRU-JP src/battle_util.c:105-231;src/accuracy_calc.c:540-541",
        },
        "reserve_party": {
            "model": "DIRECT_PARTY_READ_FOR_SWITCHING_AND_PREDICTION",
            "detail": "eligible reserve species/HP/moves inform switch decisions",
            "evidence": "CFRU-JP src/Battle_AI/ai_master.c;src/Battle_AI/ai_advanced.c",
        },
        "trainer_items": {
            "model": "TRAINER_INVENTORY_AND_CACHED_EFFECTS",
            "detail": "trainer item availability participates in action selection",
            "evidence": "CFRU-JP src/Battle_AI/ai_master.c;include/battle.h",
        },
        "switch": {
            "model": "LIVE_FIELD_AND_RESERVE_EVALUATION",
            "detail": "switch candidate scoring reads current field and reserve state",
            "evidence": "CFRU-JP src/Battle_AI/ai_master.c;src/Battle_AI/ai_util.c:1590-1596",
        },
        "gimmick": {
            "model": "LIVE_MEGA_Z_DYNAMAX_TERASTAL_STATE",
            "detail": "available/used flags and battle mode are directly inspected",
            "evidence": "CFRU-JP src/Battle_AI/ai_master.c;src/mega.c;src/dynamax.c;src/terastal.c",
        },
    }
    return {
        "hooks": hooks,
        "abi": dict(_require_mapping(ai_policy["abi"], "AI ABI")),
        "cache_lifetimes": cache_lifetimes,
        "rng_domains": rng_domains,
        "knowledge": knowledge,
        "aliases": dict(_require_mapping(ai_policy["aliases"], "AI aliases")),
        "inactive_configs": [
            {
                "name": str(name),
                "status": "EXPLICITLY_INACTIVE",
                "enable_implicitly": False,
            }
            for name in ai_policy["forbidden_implicit_configs"]
        ],
        "fixture": {
            "runner_sha256": "4d92969a5d7c48debe861ee305ff9a77bc5689c4be5922637c231c7ff18e9656",
            "config_sha256": "a361bb56f13905897f9465adf034ec2e50e5841d38fe1d873e4a419f40680eac",
            "process_runs": 2,
            "status": "MEASURED_PASS_T01_REUSE_REQUIRED_T06",
        },
        "unknown_count": 0,
    }


def _build_qol(policy: Mapping[str, Any], verified: Mapping[str, Any]) -> list[dict[str, Any]]:
    commit = str(_require_mapping(verified["source_commits"], "commits")["cfru"])
    required = [str(value) for value in policy["qol_required_domains"]]
    if set(required) != set(_QOL_DEFINITIONS):
        raise StateInventoryError("QOL definition set does not match policy")
    return [
        {
            "domain": domain,
            "address_or_symbol": _QOL_DEFINITIONS[domain][0],
            "status": _QOL_DEFINITIONS[domain][1],
            # These rows describe source/save/table contracts.  Concrete ROM
            # hook rows are generated separately from source writes.
            "vega_expected_sha256": _NON_ROM_QOL_SENTINEL,
            "classification": _QOL_DEFINITIONS[domain][2],
            "evidence": f"CFRU-JP@{commit}:{_QOL_DEFINITIONS[domain][3]}",
            "followup_task": _QOL_DEFINITIONS[domain][4],
        }
        for domain in required
    ]


def build_state_inventory(root: Path, policy: Mapping[str, Any]) -> dict[str, Any]:
    """Build and validate the deterministic T02 state model.

    Physical paths and raw private input bytes are deliberately omitted from
    the return value.  Only logical provenance, hashes, short bounded expected
    hook prefixes, and audited ownership metadata are returned.
    """

    root = Path(root).resolve()
    _require_policy(policy)
    verified = _verify_inputs(root, policy)
    ram_ranges, save_ranges = _build_ranges(verified)
    id_domains, id_ranges, cross_aliases = _build_ids(policy, verified)
    facilities, assertions, assertion_details = _build_facilities(policy, verified)
    currencies = _build_currencies(policy, verified)
    ai = _build_ai(policy, verified)
    qol = _build_qol(policy, verified)

    provenance = {
        "policy_id": str(policy["policy_id"]),
        "source_lock_sha256": str(verified["source_lock_sha256"]),
        "source_commits": dict(verified["source_commits"]),
        "roms": dict(verified["roms"]),
        "t01": dict(verified["t01"]),
        "upstream_inventory_sha256": str(verified["upstream_inventory_sha256"]),
        "evidence_file_sha256": dict(verified["source_hashes"]),
        "bounded_rom_evidence_sha256": dict(verified["rom_evidence"]),
        "authority_decisions": [
            {
                "subject": "Factory streak RAM/save locations",
                "authority": "vendor/upstream/CFRU-JP/BPRJ.ld:5-8",
                "stale_source_comment": "include/new/frontier.h:311-316 is +0x98 later and must not allocate storage",
                "resolution": "LINKER_SYMBOL_WINS_RELOCATE_FOR_INTEGRATION",
            },
            {
                "subject": "gNewBS ownership",
                "authority": "BPRJ.ld:13 plus battle_start_turn_start.c:117",
                "stale_source_comment": "include/battle.h comments another address",
                "resolution": "0x0203DFB0 is a 4-byte pointer slot; the 0x558-byte object is heap allocated",
            },
            {
                "subject": "gTempTeamBackup safe boundary",
                "authority": "pokemon_storage_system.c:147 and packed struct size 0x3A",
                "stale_source_comment": "ram_locs.h:212 says not to go beyond 0x0203E0D4 but backup begins at 0x0203E118",
                "resolution": "DO_NOT_REUSE_RAW_RANGE; RELOCATE PERSISTENT TRANSACTION",
            },
        ],
        "privacy": {
            "raw_rom_dump": False,
            "raw_save_dump": False,
            "raw_ram_dump": False,
            "physical_private_paths": False,
        },
    }
    model = {
        "schema_version": SCHEMA_VERSION,
        "provenance": provenance,
        "ram_ranges": ram_ranges,
        "save_ranges": save_ranges,
        "id_domains": id_domains,
        "id_ranges": id_ranges,
        "cross_domain_aliases": cross_aliases,
        "facilities": facilities,
        "currencies": currencies,
        "ai": ai,
        "qol": qol,
        "assertions": assertions,
        "assertion_details": assertion_details,
        "summaries": {
            "ram_ranges": len(ram_ranges),
            "save_ranges": len(save_ranges),
            "id_rows": len(id_domains),
            "id_ranges": len(id_ranges),
            "cross_domain_aliases": len(cross_aliases),
            "facilities": len(facilities),
            "currencies": len(currencies),
            "ai_hooks": len(ai["hooks"]),
            "ai_unknown": 0,
            "qol_domains": len(qol),
        },
    }
    validate_state_inventory(model, policy)
    return model


def _walk_json(value: Any, path: str = "model") -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_json(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise StateInventoryError(f"non-string JSON key at {path}")
            if key in _FORBIDDEN_DYNAMIC_KEYS:
                raise StateInventoryError(f"dynamic timestamp field is forbidden: {path}.{key}")
            _walk_json(item, f"{path}.{key}")
        return
    raise StateInventoryError(f"non-JSON value at {path}: {type(value).__name__}")


def _validate_ranges(rows: Any, policy: Mapping[str, Any], label: str) -> None:
    rows = _require_list(rows, label)
    allowed = set(str(value) for value in policy["classifications"])
    by_key: dict[str, tuple[Mapping[str, Any], int, int]] = {}
    by_space: dict[str, list[tuple[Mapping[str, Any], int, int]]] = {}
    for index, raw in enumerate(rows):
        row = _require_mapping(raw, f"{label}[{index}]")
        missing = RANGE_FIELDS - set(row)
        if missing:
            raise StateInventoryError(f"{label}[{index}] missing fields: {sorted(missing)}")
        key = str(row["key"])
        if not key or key in by_key:
            raise StateInventoryError(f"duplicate/empty {label} key: {key!r}")
        start = _parse_int(row["start"], f"{label}.{key}.start")
        end = _parse_int(row["end_exclusive"], f"{label}.{key}.end_exclusive")
        if start < 0 or end <= start or _parse_int(row["size"], f"{label}.{key}.size") != end - start:
            raise StateInventoryError(f"invalid half-open interval: {label}.{key}")
        if row["classification"] not in allowed:
            raise StateInventoryError(f"unclassified range: {label}.{key}")
        if not str(row["owner"]).strip() or not str(row["lifetime"]).strip():
            raise StateInventoryError(f"range lacks owner/lifetime: {label}.{key}")
        digest = str(row["evidence_sha256"])
        if not _HEX_SHA256.fullmatch(digest):
            raise StateInventoryError(f"invalid evidence SHA-256: {label}.{key}")
        overlaps = row["overlaps"]
        if not isinstance(overlaps, list) or not all(isinstance(value, str) for value in overlaps):
            raise StateInventoryError(f"range overlaps must be string list: {label}.{key}")
        by_key[key] = (row, start, end)
        by_space.setdefault(str(row["address_space"]), []).append((row, start, end))

    actual_overlaps: dict[str, set[str]] = {key: set() for key in by_key}
    for space, entries in by_space.items():
        ordered = sorted(entries, key=lambda item: (item[1], item[2], str(item[0]["key"])))
        for left_index, (left, left_start, left_end) in enumerate(ordered):
            for right, right_start, right_end in ordered[left_index + 1 :]:
                if right_start >= left_end:
                    break
                if left_start < right_end and right_start < left_end:
                    left_key, right_key = str(left["key"]), str(right["key"])
                    actual_overlaps[left_key].add(right_key)
                    actual_overlaps[right_key].add(left_key)
                    declared = (
                        right_key in left["overlaps"] and left_key in right["overlaps"]
                    )
                    relocation = (
                        left["classification"] == "RELOCATE"
                        or right["classification"] == "RELOCATE"
                        or "RELOCATE" in str(left["resolution"])
                        or "RELOCATE" in str(right["resolution"])
                    )
                    if not declared or not relocation:
                        raise StateInventoryError(
                            f"unresolved {space} overlap: {left_key} / {right_key}"
                        )
    for key, (row, _start, _end) in by_key.items():
        if set(row["overlaps"]) != actual_overlaps[key]:
            raise StateInventoryError(f"stale/incomplete overlap declaration: {label}.{key}")


def _validate_dpe_fixed_ram(rows: Any) -> None:
    linker_sha = "1f26a988a4c32567bd6cbc2c9fe9f876c9822acdabfe8bdfd902faebfa6d7d83"
    expected = {
        row["key"]: row
        for row in (
            _range(
                address_space="EWRAM",
                start=0x020398D8,
                end=0x020398DC,
                owner="DPE_FIXED_RAM",
                key="dpe_naming_screen_pointer",
                storage="struct NamingScreenData *sNamingScreen pointer slot",
                lifetime="naming-screen allocation lifetime",
                persistence="VOLATILE",
                active_condition="DPE naming-screen text hooks",
                source_ref="vendor/upstream/DPE-JP/BPRJ.ld:11;src/updated_code.c:90,535-560",
                evidence_sha256=linker_sha,
                classification="PORT",
                resolution="RELOCATE",
            ),
            _range(
                address_space="EWRAM",
                start=0x0203AC68,
                end=0x0203AC6C,
                owner="DPE_FIXED_RAM",
                key="dpe_pokedex_screen_data_pointer",
                storage="struct PokedexScreenData *gPokedexScreenDataPtr pointer slot",
                lifetime="Pokédex screen allocation lifetime",
                persistence="VOLATILE",
                active_condition="DPE expanded Pokédex hooks",
                source_ref="vendor/upstream/DPE-JP/BPRJ.ld:10;include/pokedex.h:81;src/updated_code.c:441-492",
                evidence_sha256=linker_sha,
                classification="PORT",
                resolution="RELOCATE",
            ),
            _range(
                address_space="IWRAM",
                start=0x03003130,
                end=0x0300356C,
                owner="DPE_FIXED_RAM",
                key="dpe_main_struct",
                storage="struct Main gMain (sizeof 0x43C; last declared byte at +0x439, 4-byte alignment)",
                lifetime="engine lifetime",
                persistence="VOLATILE",
                active_condition="DPE form and naming hooks inspect gMain.inBattle",
                source_ref="vendor/upstream/DPE-JP/BPRJ.ld:12;include/main.h:8-44",
                evidence_sha256=linker_sha,
                classification="PORT",
                resolution="PORT_WITH_EXACT_ABI_ASSERT",
            ),
        )
    }
    observed = {
        str(row["key"]): dict(row)
        for row in _require_list(rows, "ram_ranges")
        if _require_mapping(row, "RAM range").get("owner") == "DPE_FIXED_RAM"
    }
    if observed != expected:
        raise StateInventoryError("DPE fixed RAM contract mismatch")


def _validate_ids(model: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    rows = _require_list(model.get("id_domains"), "id_domains")
    ranges = _require_list(model.get("id_ranges"), "id_ranges")
    aliases = _require_list(model.get("cross_domain_aliases"), "cross_domain_aliases")
    ranges_by_key: dict[str, Mapping[str, Any]] = {}
    range_identities: set[tuple[str, int, int]] = set()
    for index, raw in enumerate(ranges):
        item = _require_mapping(raw, f"id_ranges[{index}]")
        for key in ("domain", "key", "start", "end_exclusive", "owner", "id_policy", "evidence"):
            if key not in item:
                raise StateInventoryError(f"id_ranges[{index}] missing {key}")
        key = str(item["key"])
        start = _parse_int(item["start"], f"id range {key} start")
        end = _parse_int(item["end_exclusive"], f"id range {key} end")
        if not key or key in ranges_by_key or start < 0 or end <= start:
            raise StateInventoryError(f"invalid/duplicate ID range: {key}")
        identity = (str(item["domain"]), start, end)
        if identity in range_identities:
            raise StateInventoryError(f"duplicate ID interval: {identity}")
        range_identities.add(identity)
        ranges_by_key[key] = item

    identities: set[tuple[str, int | None]] = set()
    observed_vega_high_flags: set[int] = set()
    for index, raw in enumerate(rows):
        row = _require_mapping(raw, f"id_domains[{index}]")
        missing = ID_FIELDS - set(row)
        if missing:
            raise StateInventoryError(f"id_domains[{index}] missing fields: {sorted(missing)}")
        domain, key = str(row["domain"]), str(row["key"])
        value = row["id"]
        numeric: int | None
        if value is None:
            numeric = None
            if str(row["id_policy"]) not in {"NEW", "DEFER", "DEFERRED"}:
                raise StateInventoryError(f"unallocated ID is not NEW/DEFER: {key}")
            if row["id_hex"] != "":
                raise StateInventoryError(f"null ID has id_hex: {key}")
        else:
            numeric = _parse_int(value, f"ID {key}")
            if numeric < 0:
                raise StateInventoryError(f"negative ID: {key}")
            if _parse_int(row["id_hex"], f"ID {key} hex") != numeric:
                raise StateInventoryError(f"ID/id_hex mismatch: {key}")
        identity = (domain, numeric)
        if numeric is not None and identity in identities:
            raise StateInventoryError(f"duplicate numeric ID without canonical row: {identity}")
        identities.add(identity)
        range_key = str(row["range_key"])
        if range_key not in ranges_by_key:
            raise StateInventoryError(f"ID references unknown range: {key}: {range_key}")
        container = ranges_by_key[range_key]
        if numeric is not None:
            if domain != str(container["domain"]):
                raise StateInventoryError(f"ID/range domain mismatch: {key}")
            if not (
                _parse_int(container["start"], "range start")
                <= numeric
                < _parse_int(container["end_exclusive"], "range end")
            ):
                raise StateInventoryError(f"ID outside declared range: {key}")
        if not isinstance(row["aliases"], list) or not isinstance(row["raw_refs"], list):
            raise StateInventoryError(f"ID aliases/raw_refs must be lists: {key}")
        if not isinstance(row["evidence"], list) or not row["evidence"]:
            raise StateInventoryError(f"ID lacks evidence: {key}")
        if (
            domain == "flag"
            and numeric is not None
            and str(row["origin"]) == "VEGA_ROM"
            and int(policy["high_flag_migration"]["expanded_flag_start"])
            <= numeric
            < int(policy["high_flag_migration"]["expanded_flag_end_exclusive"])
        ):
            observed_vega_high_flags.add(numeric)
            if numeric not in set(policy["high_flag_migration"]["whitelist"]):
                raise StateInventoryError(f"Vega high flag is not whitelisted: {numeric:#x}")
            if "MIGRATE_WHITELIST" not in str(row["id_policy"]):
                raise StateInventoryError(f"Vega high flag lacks whitelist migration: {key}")

    expected_high = set(int(value) for value in policy["high_flag_migration"]["whitelist"])
    if observed_vega_high_flags != expected_high:
        raise StateInventoryError(
            f"Vega high-flag whitelist coverage mismatch: {sorted(observed_vega_high_flags)}"
        )
    required_factory_values = {
        int(policy["facilities"]["factory"]["flag_battle_facility"]),
        int(policy["facilities"]["factory"]["raw_facility_number_var"]),
    }
    raw_resolution = {
        int(row["id"]): str(row["id_policy"])
        for row in rows
        if row["id"] is not None and int(row["id"]) in required_factory_values
    }
    if raw_resolution != {value: "REMAP" for value in required_factory_values}:
        raise StateInventoryError("Factory raw 0x930/0x403A must both be REMAP")
    for index, raw in enumerate(aliases):
        item = _require_mapping(raw, f"cross_domain_aliases[{index}]")
        for key in ("key", "domains", "owners", "physical_storage", "classification", "resolution", "evidence"):
            if key not in item or not item[key]:
                raise StateInventoryError(f"cross-domain alias lacks {key}: index {index}")
        if str(item["resolution"]) in {"UNKNOWN", "KEEP_RAW"}:
            raise StateInventoryError(f"unresolved cross-domain alias: {item['key']}")


def _validate_currencies(model: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    currencies = _require_mapping(model.get("currencies"), "currencies")
    expected_keys = set(policy["currencies"])
    if set(currencies) != expected_keys:
        raise StateInventoryError("currency key set mismatch")
    for key, spec_value in policy["currencies"].items():
        spec = _require_mapping(spec_value, f"policy currency {key}")
        row = _require_mapping(currencies[key], f"currency {key}")
        if row.get("availability") != spec.get("availability"):
            raise StateInventoryError(f"currency availability mismatch: {key}")
        enabled = bool(row.get("enabled"))
        if "enabled" in spec and enabled != bool(spec["enabled"]):
            raise StateInventoryError(f"currency enablement mismatch: {key}")
        required = [str(value) for value in row.get("required_operations", [])]
        operations = _require_mapping(row.get("operations"), f"currency {key} operations")
        if enabled:
            if not str(row.get("owner", "")).strip() or str(row["owner"]).startswith("UNALLOCATED"):
                raise StateInventoryError(f"enabled currency lacks owner: {key}")
            if not isinstance(row.get("width_bits"), int) or not isinstance(row.get("cap"), int):
                raise StateInventoryError(f"enabled currency lacks width/cap: {key}")
            if set(operations) != set(required) or any(not operations[name] for name in required):
                raise StateInventoryError(f"enabled currency operations incomplete: {key}")
            if not row.get("earn_hooks") or not row.get("spend_hooks"):
                raise StateInventoryError(f"enabled currency earn/spend hooks incomplete: {key}")
        elif any(operations.get(name) for name in required):
            raise StateInventoryError(f"disabled currency has partially active operations: {key}")
    arcade = currencies["arcade_coin"]
    if arcade.get("width_bits") != 16 or arcade.get("cap") != 9999:
        raise StateInventoryError("Vega arcade coin ABI changed")
    if arcade.get("expected_core_sha256") != "d32235e5c024cd68ef044543330b493eb14f910c7b529740faf9155f590c250c":
        raise StateInventoryError("arcade coin expected core hash changed")


def _validate_facilities(model: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    facilities = _require_mapping(model.get("facilities"), "facilities")
    if set(facilities) != {"factory", "mirage"}:
        raise StateInventoryError("facility set must be exactly factory/mirage")
    factory = _require_mapping(facilities["factory"], "factory")
    mirage = _require_mapping(facilities["mirage"], "mirage")
    for name, facility in (("factory", factory), ("mirage", mirage)):
        for key in (
            "classification",
            "state_fields",
            "transitions",
            "specials",
            "trainers",
            "maps",
            "music",
            "rewards",
            "party_transaction",
            "abnormal_exit_paths",
        ):
            if key not in facility:
                raise StateInventoryError(f"facility {name} missing {key}")
    transaction = _require_mapping(factory["party_transaction"], "factory party transaction")
    target = _require_mapping(transaction.get("target_contract"), "factory target transaction")
    required_target = {
        "full_party_slots": 6,
        "exact_live_party_bytes": True,
        "persistent": True,
        "commit_marker_before_party_replace": True,
        "restore_idempotent": True,
        "clear_marker_after_restore": True,
        "reward_credit_once": True,
    }
    for key, expected in required_target.items():
        if target.get(key) != expected:
            raise StateInventoryError(f"unsafe Factory transaction contract: {key}")
    source = _require_mapping(transaction.get("source_contract"), "factory source transaction")
    if source.get("persistent") is not False or source.get("reset_safe") is not False:
        raise StateInventoryError("Factory source backup hazard is not recorded")
    if mirage.get("policy") != policy["facilities"]["mirage"]["policy"]:
        raise StateInventoryError("Mirage migration policy mismatch")
    if mirage.get("respawn_id") != policy["facilities"]["mirage"]["respawn_id"]:
        raise StateInventoryError("Mirage respawn mismatch")

    def state_ids(facility: Mapping[str, Any], label: str) -> dict[str, tuple[int, ...]]:
        result: dict[str, tuple[int, ...]] = {}
        for raw_field in _require_list(facility.get("state_fields"), f"{label} state fields"):
            field = _require_mapping(raw_field, f"{label} state field")
            key = str(field.get("key", ""))
            if not key or key in result:
                raise StateInventoryError(f"duplicate/empty {label} state field: {key!r}")
            has_one = "raw_id" in field
            has_many = "raw_ids" in field
            if has_one == has_many:
                raise StateInventoryError(f"{label} state field must define raw_id xor raw_ids: {key}")
            raw_values = [field["raw_id"]] if has_one else _require_list(
                field["raw_ids"], f"{label} state field raw IDs"
            )
            values = tuple(sorted(_parse_int(value, f"{label} raw ID") for value in raw_values))
            if not values or len(values) != len(set(values)):
                raise StateInventoryError(f"duplicate/empty {label} raw IDs: {key}")
            result[key] = values
        return result

    factory_policy = _require_mapping(policy["facilities"]["factory"], "factory policy")
    mirage_policy = _require_mapping(policy["facilities"]["mirage"], "mirage policy")
    expected_factory_state = {
        "active_flag": (int(factory_policy["flag_battle_facility"]),),
        "facility_number": (int(factory_policy["raw_facility_number_var"]),),
        "session_vars": tuple(sorted(int(value) for value in factory_policy["state_vars"])),
        "trainer_table_indices": tuple(
            sorted(int(value) for value in factory_policy["table_index_vars"])
        ),
    }
    expected_mirage_state = {
        "flags": tuple(sorted(int(value) for value in mirage_policy["flags"])),
        "round_state": tuple(sorted(int(value) for value in mirage_policy["vars"])),
        "temporary_badge_mask": tuple(
            sorted(int(value) for value in mirage_policy["badge_flags"])
        ),
    }
    observed_factory_state = state_ids(factory, "Factory")
    observed_mirage_state = state_ids(mirage, "Mirage")
    factory_raw_ids = {
        value for values in observed_factory_state.values() for value in values
    }
    mirage_raw_ids = {
        value for values in observed_mirage_state.values() for value in values
    }
    raw_id_intersection = factory_raw_ids & mirage_raw_ids
    if raw_id_intersection:
        raise StateInventoryError(
            f"Factory/Mirage raw state IDs overlap: {sorted(raw_id_intersection)}"
        )
    if observed_factory_state != expected_factory_state:
        raise StateInventoryError("Factory raw state ID contract mismatch")
    if observed_mirage_state != expected_mirage_state:
        raise StateInventoryError("Mirage raw state ID contract mismatch")

    expected_bounds = [
        {
            "key": "facility_number",
            "minimum": 0,
            "maximum_exclusive": 5,
            "source_check": "raw 0x403A is consumed",
            "status": "FIX_REQUIRED",
            "resolution": "REMAP_AND_VALIDATE_BEFORE_INDEX",
        },
        {
            "key": "battle_style",
            "minimum": 0,
            "maximum_exclusive": 7,
            "source_check": "MathMin(value, NUM_TOWER_BATTLE_TYPES) admits 7",
            "status": "KNOWN_OOB_HAZARD",
            "resolution": "CLAMP_TO_MAX_EXCLUSIVE_MINUS_ONE",
        },
        {
            "key": "battle_mine_choice",
            "minimum": 0,
            "maximum_exclusive": 3,
            "source_check": "choice is reduced to 0..2 for tier assignment",
            "status": "BOUNDED",
            "resolution": "PORT_WITH_ASSERT",
        },
        {
            "key": "eligibility_tier_iteration",
            "minimum": 0,
            "maximum_exclusive": 3,
            "source_check": "loop increment reads tiers[numTiers] after final body",
            "status": "KNOWN_OOB_HAZARD",
            "resolution": "INDEX_ONLY_INSIDE_LOOP_BODY",
        },
    ]
    observed_bounds = [
        dict(_require_mapping(bound, "factory bound"))
        for bound in _require_list(factory.get("bounds"), "factory bounds")
    ]
    for item in observed_bounds:
        minimum = _parse_int(item.get("minimum"), "facility minimum")
        maximum = _parse_int(item.get("maximum_exclusive"), "facility maximum")
        if minimum < 0 or maximum <= minimum:
            raise StateInventoryError(f"invalid facility bound: {item.get('key')}")
        if item.get("status") in {"KNOWN_OOB_HAZARD", "FIX_REQUIRED"} and not str(item.get("resolution", "")).strip():
            raise StateInventoryError(f"facility hazard lacks resolution: {item.get('key')}")
    if observed_bounds != expected_bounds:
        raise StateInventoryError("Factory bounds contract mismatch")

    special_names = {
        0x52: "GenerateFacilityTrainer",
        0x53: "LoadFrontierIntroBattleMessage",
        0x54: "GetBattleFacilityStreak",
        0x55: "UpdateBattleFacilityStreak",
        0x56: "DetermineBattlePointsToGive",
        0x57: "ShowFrontierRecords",
        0x67: "GenerateRandomBattleTowerTeam",
        0x68: "GivePlayerFrontierMonGivenSpecies",
        0x69: "GivePlayerRandomFrontierMonByTier",
        0x6A: "GivePlayerFrontierMonByLoadedSpread",
        0x6B: "ReplacePlayerTeamWithMultiTrainerTeam",
        0x6C: "SpliceFrontierTeamWithPlayerTeam",
        0x6D: "LoadFrontierMultiTrainerById",
        0x6E: "BufferBattleSandsRecords",
        0x6F: "CanTeamParticipateInBattleMine",
        0x70: "RandomizeBattleMineBattleOptions",
        0x71: "LoadBattleMineRecordTier",
        0x72: "LoadBattleCircusEffects",
        0x73: "ModifyTeamForBattleTower",
        0xE7: "GenerateFacilityOpponent",
    }
    special_base = _parse_int(factory_policy["special_table_base"], "special table base")
    expected_specials = [
        {
            "id": value,
            "id_hex": _hex(value, 4),
            "name": name,
            "pointer_slot": _hex(special_base + value * 4),
            "fixture_status": (
                "MEASURED_MATCH"
                if value in {0x56, 0x6F, 0x70}
                else "SOURCE_PINNED_ADAPTER_REQUIRED"
            ),
            "resolution": "REMAP",
        }
        for value, name in sorted(special_names.items())
    ]
    observed_specials = [
        dict(_require_mapping(item, "factory special"))
        for item in _require_list(factory.get("specials"), "factory specials")
    ]
    if observed_specials != expected_specials:
        raise StateInventoryError("Factory Special ABI contract mismatch")
    if _require_list(mirage.get("specials"), "Mirage specials") != []:
        raise StateInventoryError("Mirage must not own Factory Special ABI slots")

    expected_factory_records = [
        "factory_battle_sands_streaks",
        "factory_battle_tower_streaks",
        "factory_battle_mine_streaks",
        "factory_battle_circus_streaks",
    ]
    expected_mirage_records = [
        "mirage_wins_within_round",
        "mirage_completed_rounds_tier",
    ]
    factory_records = [str(value) for value in _require_list(factory.get("records"), "Factory records")]
    mirage_records = [str(value) for value in _require_list(mirage.get("records"), "Mirage records")]
    record_intersection = set(factory_records) & set(mirage_records)
    if record_intersection:
        raise StateInventoryError(
            f"Factory/Mirage records overlap: {sorted(record_intersection)}"
        )
    if factory_records != expected_factory_records or mirage_records != expected_mirage_records:
        raise StateInventoryError("Factory/Mirage record contract mismatch")

    details = _require_mapping(model.get("assertion_details"), "assertion_details")
    for key in (
        "facility_state_namespaces_disjoint",
        "facility_party_transactions_disjoint",
        "facility_records_disjoint",
        "facility_reward_and_currency_disjoint",
        "facility_cleanup_disjoint",
    ):
        item = _require_mapping(details.get(key), f"assertion {key}")
        left = _require_list(item.get("factory"), f"assertion {key}.factory")
        right = _require_list(item.get("mirage"), f"assertion {key}.mirage")
        recomputed = sorted(set(str(value) for value in left) & set(str(value) for value in right))
        if item.get("status") != ("PASS" if not recomputed else "FAIL") or item.get("intersection") != recomputed:
            raise StateInventoryError(f"facility coexistence assertion failed: {key}")
    state_detail = _require_mapping(
        details["facility_state_namespaces_disjoint"], "facility state assertion"
    )
    expected_factory_hex = sorted(_hex(value, 4) for value in factory_raw_ids)
    expected_mirage_hex = sorted(_hex(value, 4) for value in mirage_raw_ids)
    if state_detail.get("factory") != expected_factory_hex or state_detail.get("mirage") != expected_mirage_hex:
        raise StateInventoryError("facility raw-ID assertion does not match state model")
    record_detail = _require_mapping(
        details["facility_records_disjoint"], "facility record assertion"
    )
    if record_detail.get("factory") != factory_records or record_detail.get("mirage") != mirage_records:
        raise StateInventoryError("facility record assertion does not match state model")
    assertions = _require_list(model.get("assertions"), "assertions")
    if not assertions or not all(isinstance(value, str) and value.strip() for value in assertions):
        raise StateInventoryError("assertions must be a nonempty human-readable string list")


def _contains_unknown(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().upper() == "UNKNOWN"
    if isinstance(value, list):
        return any(_contains_unknown(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_unknown(item) for item in value.values())
    return False


def _validate_ai(model: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    ai = _require_mapping(model.get("ai"), "ai")
    if _contains_unknown(ai) or ai.get("unknown_count") != 0:
        raise StateInventoryError("AI UNKNOWN count must be zero")
    expected_abi = dict(_require_mapping(policy["ai"]["abi"], "policy AI ABI"))
    observed_abi = dict(_require_mapping(ai.get("abi"), "AI ABI"))
    if observed_abi != expected_abi:
        raise StateInventoryError("AI exact ABI mismatch")
    hooks = _require_list(ai.get("hooks"), "AI hooks")
    expected = {
        str(address): str(prefix)
        for address, prefix in policy["ai"]["vega_expected_hook_prefixes"].items()
    }
    observed: dict[str, str] = {}
    for raw in hooks:
        row = _require_mapping(raw, "AI hook")
        for key in ("address", "vega_expected", "owner", "resolution", "evidence"):
            if not str(row.get(key, "")).strip():
                raise StateInventoryError(f"AI hook lacks {key}")
        if not re.fullmatch(r"[0-9a-f]{16}", str(row["vega_expected"])):
            raise StateInventoryError(f"AI hook expected prefix invalid: {row['address']}")
        observed[str(row["address"])] = str(row["vega_expected"])
    if observed != expected:
        raise StateInventoryError("AI hook set/expected bytes mismatch")
    rng = {
        str(_require_mapping(item, "AI RNG domain")["domain"])
        for item in _require_list(ai.get("rng_domains"), "AI RNG domains")
    }
    if rng != set(policy["ai"]["required_rng_domains"]):
        raise StateInventoryError("AI RNG domains incomplete")
    knowledge = _require_mapping(ai.get("knowledge"), "AI knowledge")
    if set(knowledge) != set(policy["ai"]["required_knowledge_domains"]):
        raise StateInventoryError("AI knowledge domains incomplete")
    for key, raw in knowledge.items():
        item = _require_mapping(raw, f"AI knowledge {key}")
        if not str(item.get("model", "")).strip() or not str(item.get("evidence", "")).strip():
            raise StateInventoryError(f"AI knowledge lacks model/evidence: {key}")
    caches = _require_list(ai.get("cache_lifetimes"), "AI caches")
    expected_cache_keys = {
        "gBattleResources_ai",
        "battle_history",
        "prediction_cache",
        "trainer_item_effect_cache",
    }
    observed_cache_keys: set[str] = set()
    for raw in caches:
        item = _require_mapping(raw, "AI cache")
        key = str(item.get("key", ""))
        if not key or key in observed_cache_keys:
            raise StateInventoryError(f"duplicate/empty AI cache key: {key!r}")
        observed_cache_keys.add(key)
        if not item.get("lifetime") or not item.get("invalidation") or not item.get("evidence"):
            raise StateInventoryError(f"AI cache contract incomplete: {key}")
    if observed_cache_keys != expected_cache_keys:
        raise StateInventoryError("AI cache key set mismatch")
    inactive = {str(item["name"]): item for item in ai.get("inactive_configs", [])}
    for name in policy["ai"]["forbidden_implicit_configs"]:
        if name not in inactive or inactive[name].get("enable_implicitly") is not False:
            raise StateInventoryError(f"AI forbidden implicit config is not gated: {name}")


def _validate_qol(model: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    rows = _require_list(model.get("qol"), "qol")
    domains: set[str] = set()
    allowed = set(str(value) for value in policy["classifications"])
    followups = set(str(value) for value in policy["unknown_contract"]["allowed_followups"])
    commit = str(
        _require_mapping(policy["source_lock"]["commits"], "source commits")["cfru"]
    )
    for index, raw in enumerate(rows):
        row = _require_mapping(raw, f"qol[{index}]")
        missing = QOL_FIELDS - set(row)
        if missing:
            raise StateInventoryError(f"qol[{index}] missing fields: {sorted(missing)}")
        extra = set(row) - QOL_FIELDS
        if extra:
            raise StateInventoryError(f"qol[{index}] has unexpected fields: {sorted(extra)}")
        domain = str(row["domain"])
        if domain in domains:
            raise StateInventoryError(f"duplicate QOL domain: {domain}")
        domains.add(domain)
        if domain not in _QOL_DEFINITIONS:
            continue
        definition = _QOL_DEFINITIONS[domain]
        if definition[2] not in allowed or definition[2] == "UNKNOWN":
            raise StateInventoryError(f"QOL definition is unclassified: {domain}")
        if definition[4] not in followups:
            raise StateInventoryError(f"QOL definition follow-up is not allowed: {domain}")
        if row["vega_expected_sha256"] != _NON_ROM_QOL_SENTINEL:
            raise StateInventoryError(f"non-ROM QOL sentinel mismatch: {domain}")
        expected = {
            "domain": domain,
            "address_or_symbol": definition[0],
            "status": definition[1],
            "vega_expected_sha256": _NON_ROM_QOL_SENTINEL,
            "classification": definition[2],
            "evidence": f"CFRU-JP@{commit}:{definition[3]}",
            "followup_task": definition[4],
        }
        if dict(row) != expected:
            raise StateInventoryError(f"non-ROM QOL contract mismatch: {domain}")
    if domains != set(policy["qol_required_domains"]):
        raise StateInventoryError(f"QOL domain coverage mismatch: {sorted(domains)}")


def validate_state_inventory(model: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    """Fail closed on incomplete ownership, alias, currency, facility, or AI state."""

    _require_policy(policy)
    if not isinstance(model, Mapping) or model.get("schema_version") != SCHEMA_VERSION:
        raise StateInventoryError("state inventory schema mismatch")
    required_top = {
        "schema_version",
        "provenance",
        "ram_ranges",
        "save_ranges",
        "id_domains",
        "id_ranges",
        "cross_domain_aliases",
        "facilities",
        "currencies",
        "ai",
        "qol",
        "assertions",
        "assertion_details",
        "summaries",
    }
    missing = required_top - set(model)
    if missing:
        raise StateInventoryError(f"state inventory missing top keys: {sorted(missing)}")
    _walk_json(model)
    encoded = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    for forbidden in ("/home/", "/mnt/", "userfile/", "inputs/private/"):
        if forbidden in encoded:
            raise StateInventoryError(f"private/physical path leaked into model: {forbidden}")
    provenance = _require_mapping(model["provenance"], "provenance")
    privacy = _require_mapping(provenance.get("privacy"), "provenance.privacy")
    if any(privacy.get(key) is not False for key in (
        "raw_rom_dump", "raw_save_dump", "raw_ram_dump", "physical_private_paths"
    )):
        raise StateInventoryError("private/raw dump policy is not fail-closed")
    if provenance.get("source_lock_sha256") != policy["source_lock"]["sha256"]:
        raise StateInventoryError("state provenance source-lock mismatch")
    _validate_ranges(model["ram_ranges"], policy, "ram_ranges")
    _validate_dpe_fixed_ram(model["ram_ranges"])
    _validate_ranges(model["save_ranges"], policy, "save_ranges")
    _validate_ids(model, policy)
    _validate_currencies(model, policy)
    _validate_facilities(model, policy)
    _validate_ai(model, policy)
    _validate_qol(model, policy)
    summaries = _require_mapping(model["summaries"], "summaries")
    expected_counts = {
        "ram_ranges": len(model["ram_ranges"]),
        "save_ranges": len(model["save_ranges"]),
        "id_rows": len(model["id_domains"]),
        "id_ranges": len(model["id_ranges"]),
        "cross_domain_aliases": len(model["cross_domain_aliases"]),
        "facilities": len(model["facilities"]),
        "currencies": len(model["currencies"]),
        "ai_hooks": len(model["ai"]["hooks"]),
        "ai_unknown": 0,
        "qol_domains": len(model["qol"]),
    }
    for key, expected in expected_counts.items():
        if summaries.get(key) != expected:
            raise StateInventoryError(f"summary count mismatch: {key}")
