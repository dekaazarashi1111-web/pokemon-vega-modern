"""Deterministic Kanto trainer map-event planning for the final ChangeKit merge.

This module deliberately does not allocate or patch ROM space.  It emits byte
images plus symbolic fixups so the final builder remains the sole ROM owner.
The inputs are immutable Stage 34/clean ROM bytes, the checked-in Kanto map
catalogue and Task 06 CSVs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import struct
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

GBA_ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x54B0C
OBJECT_SIZE = 0x18
EVENT_HEADER_SIZE = 0x14
OBJECT_LIMIT = 15
FLAG_SYS_GAME_CLEAR = 0x082C
FLAG_BADGE01_GET = 0x0824
FLAG_KANTO_PORTAL_READY = 0x114B
CERT_FLAG_BASE = 0x1400

_SCRIPT_OP = {
    "end": 0x02,
    "goto": 0x05,
    "goto_if": 0x06,
    "callstd": 0x09,
    "loadword": 0x0F,
    "setflag": 0x29,
    "checkflag": 0x2B,
    "trainerbattle": 0x5C,
    "faceplayer": 0x5A,
    "lock": 0x6B,
    "release": 0x6C,
}


class KantoPlanError(RuntimeError):
    """The requested physical plan cannot be represented without guessing."""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _rom_offset(pointer: int, size: int, what: str, rom_size: int) -> int:
    offset = pointer - GBA_ROM_BASE
    if pointer < GBA_ROM_BASE or offset < 0 or offset + size > rom_size:
        raise KantoPlanError(f"{what}: ROM pointer outside image: {pointer:#010x}")
    return offset


def _u32(raw: bytes, offset: int, what: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        raise KantoPlanError(f"{what}: truncated u32")
    return struct.unpack_from("<I", raw, offset)[0]


def _csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise KantoPlanError(f"missing ChangeKit CSV: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _split_ints(value: str) -> list[int]:
    return [int(part) for part in value.split("+")]


def _read_map_catalog(repo_root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((repo_root / "generated/maps/kanto").glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        header = row.get("map_header")
        if not header or header.get("scope_decision") not in {"INCLUDE", "REBUILD"}:
            continue
        key = str(header["map_key"])
        if key in result:
            raise KantoPlanError(f"duplicate Kanto map key: {key}")
        result[key] = row
    if len(result) != 253:
        raise KantoPlanError(f"Kanto map catalogue drift: {len(result)} != 253")
    return result


def _map_header_offset(rom: bytes, group: int, number: int) -> tuple[int, int]:
    root_pointer = _u32(rom, MAP_GROUPS_POINTER_SITE, "gMapGroups site")
    root = _rom_offset(root_pointer, (group + 1) * 4, "gMapGroups", len(rom))
    group_pointer = _u32(rom, root + group * 4, f"map group {group}")
    group_offset = _rom_offset(group_pointer, (number + 1) * 4, f"map group {group}", len(rom))
    header_pointer = _u32(rom, group_offset + number * 4, f"map {group}/{number}")
    return header_pointer, _rom_offset(header_pointer, 0x1C, f"map header {group}/{number}", len(rom))


def _stage_map_state(rom: bytes, group: int, number: int) -> dict[str, Any]:
    header_pointer, header = _map_header_offset(rom, group, number)
    events_pointer = _u32(rom, header + 4, f"events {group}/{number}")
    events = _rom_offset(events_pointer, EVENT_HEADER_SIZE, f"events {group}/{number}", len(rom))
    object_count, warp_count, coord_count, bg_count = rom[events:events + 4]
    pointers = struct.unpack_from("<IIII", rom, events + 4)
    sizes = (object_count * OBJECT_SIZE, warp_count * 8, coord_count * 16, bg_count * 12)
    arrays: list[bytes] = []
    for name, pointer, size in zip(("objects", "warps", "coords", "bg"), pointers, sizes):
        if not size:
            arrays.append(b"")
        else:
            at = _rom_offset(pointer, size, f"{name} {group}/{number}", len(rom))
            arrays.append(rom[at:at + size])
    objects = [arrays[0][i:i + OBJECT_SIZE] for i in range(0, len(arrays[0]), OBJECT_SIZE)]
    return {
        "map_header_address": header_pointer,
        "event_header_address": events_pointer,
        "event_header_hex": rom[events:events + EVENT_HEADER_SIZE].hex(),
        "counts": {"objects": object_count, "warps": warp_count,
                   "coords": coord_count, "bg": bg_count},
        "pointers": {"objects": pointers[0], "warps": pointers[1],
                     "coords": pointers[2], "bg": pointers[3]},
        "objects": objects,
        "warps_hex": arrays[1].hex(),
        "coords_hex": arrays[2].hex(),
        "bg_hex": arrays[3].hex(),
    }


def _clean_source_objects(repo_root: Path, clean_rom: bytes,
                          source_map: str) -> list[bytes]:
    groups = json.loads((repo_root /
        "vendor/upstream/pokefirered/data/maps/map_groups.json").read_text(encoding="utf-8"))
    location: tuple[int, int] | None = None
    for group_index, group_name in enumerate(groups["group_order"]):
        try:
            location = (group_index, groups[group_name].index(source_map))
            break
        except ValueError:
            pass
    if location is None:
        raise KantoPlanError(f"source map missing from clean map groups: {source_map}")
    _, header = _map_header_offset(clean_rom, *location)
    events_pointer = _u32(clean_rom, header + 4, f"clean events {source_map}")
    events = _rom_offset(events_pointer, EVENT_HEADER_SIZE, f"clean events {source_map}", len(clean_rom))
    count = clean_rom[events]
    if not count:
        return []
    objects_pointer = _u32(clean_rom, events + 4, f"clean objects {source_map}")
    objects = _rom_offset(objects_pointer, count * OBJECT_SIZE,
                          f"clean objects {source_map}", len(clean_rom))
    return [clean_rom[objects + i * OBJECT_SIZE:objects + (i + 1) * OBJECT_SIZE]
            for i in range(count)]


def _object_fields(raw: bytes) -> dict[str, int]:
    if len(raw) != OBJECT_SIZE:
        raise KantoPlanError("object event record must be 24 bytes")
    return {
        "local_id": raw[0], "graphics_id": raw[1], "kind": raw[2],
        "movement_type": raw[3], "x": struct.unpack_from("<H", raw, 4)[0],
        "y": struct.unpack_from("<H", raw, 6)[0], "elevation": raw[8],
        "trainer_type": struct.unpack_from("<H", raw, 12)[0],
        "sight_range": struct.unpack_from("<H", raw, 14)[0],
        "script_pointer": struct.unpack_from("<I", raw, 16)[0],
        "flag": struct.unpack_from("<H", raw, 20)[0],
    }


def _source_template_trainer_id(clean_rom: bytes, source_object: bytes,
                                *, source_map: str, root_index: int,
                                identity_evidence: str = "") -> tuple[int, dict[str, Any]]:
    """Resolve a clean object root to its unique rooted FireRed trainer battle."""
    # Reuse the project's strict event-bytecode walker: it follows only command
    # boundaries and explicit call/goto edges, never byte-pattern searches.
    from tools.t02.rom_inventory import RomImage, ScriptRoot, ScriptWalker

    script_pointer = _object_fields(source_object)["script_pointer"]
    # The champion object is a movement actor whose battle is launched by the
    # room's coordinate script, so its object script pointer is intentionally
    # null in clean FireRed.  Task06 names both the BLUE graphics and Champion
    # role, which uniquely identifies the initial Champion table template.
    if script_pointer == 0 and source_map == "PokemonLeague_ChampionsRoom" \
            and "BLUE" in identity_evidence.upper():
        return 409, {
            "method": "GRAPHICS_AND_ARCHETYPE_FALLBACK",
            "source_script_pointer": 0,
            "candidate_trainer_ids": [409],
            "fallback_used": True,
            "fallback_basis": "OBJ_EVENT_GFX_BLUE + Pokemon League Champion initial identity",
            "identity_basis": identity_evidence,
        }
    walker = ScriptWalker(RomImage(label="clean", data=clean_rom,
                                   logical_path="inputs/private/FireRed_JPN_Rev0_clean.gba"))
    label = f"{source_map}:object:{root_index}"
    walker.add_root(ScriptRoot(script_pointer, label, "object"))
    result = walker.walk()
    command_rows = [{"address": int(reference["instruction_address"]),
                     "trainer_id": int(reference["value"]),
                     "kind": int(reference["battle_type"])}
                    for reference in result["references"]
                    if reference["category"] == "trainer"
                    and reference["access"] == "battle"
                    and label in reference["roots"]
                    and 0 <= int(reference["value"]) <= 742]
    candidates = sorted({
        int(reference["value"])
        for reference in result["references"]
        if reference["category"] == "trainer"
        and reference["access"] == "battle"
        and label in reference["roots"]
        and 0 <= int(reference["value"]) <= 742
    })
    audit = {"method": "ROOTED_EVENT_SCRIPT_WALK", "source_script_pointer": script_pointer,
             "candidate_trainer_ids": candidates, "fallback_used": False,
             "commands": command_rows,
             "identity_basis": f"{source_map} object root_index={root_index}"}
    if len(candidates) > 1 and source_map.startswith("PokemonLeague_"):
        # The same elite-four object branches between initial and postgame
        # variants. Task06 is an INITIAL encounter, so the lower initial table
        # id is the identity-preserving class/name/reward template.
        chosen = min(candidates)
        audit.update({"method": "ROOTED_IDENTITY_INITIAL_VARIANT",
                      "selected_trainer_id": chosen,
                      "selection_basis": "same rooted Elite Four identity; INITIAL variant"})
        return chosen, audit
    if len(candidates) != 1:
        audit.update({"fallback_used": True,
                      "fallback_basis": "NONE_FAIL_CLOSED; graphics/archetype evidence not unique"})
        raise KantoPlanError(
            f"{label}: expected one rooted source trainer, found {candidates}; "
            "graphics-only fallback is unsafe"
        )
    audit["selected_trainer_id"] = candidates[0]
    return candidates[0], audit


def _rooted_trainer_command(rom: bytes, script_pointer: int, trainer_id: int,
                            label: str) -> dict[str, int]:
    from tools.t02.rom_inventory import RomImage, ScriptRoot, ScriptWalker

    walker = ScriptWalker(RomImage(label="stage34", data=rom, logical_path="stage34"))
    walker.add_root(ScriptRoot(script_pointer, label, "object"))
    result = walker.walk()
    commands = [{"address": int(ref["instruction_address"]),
                 "trainer_id": int(ref["value"]), "kind": int(ref["battle_type"])}
                for ref in result["references"]
                if ref["category"] == "trainer" and ref["access"] == "battle"
                and label in ref["roots"] and int(ref["value"]) == trainer_id]
    unique = {(row["address"], row["kind"]): row for row in commands}
    if len(unique) != 1:
        raise KantoPlanError(f"{label}: existing trainer {trainer_id} command is not unique: {commands}")
    return next(iter(unique.values()))


def build_object_record(template: bytes, *, local_id: int, x: int, y: int,
                        elevation: int, sight_range: int, talk_start: bool = False) -> dict[str, Any]:
    """Return a relocatable 24-byte object record and its script fixup."""
    if len(template) != OBJECT_SIZE or not 1 <= local_id <= 0xFF:
        raise KantoPlanError("invalid object template/local id")
    if min(x, y, elevation, sight_range) < 0 or max(x, y) > 0xFFFF:
        raise KantoPlanError("object coordinate/range outside ABI")
    raw = bytearray(template)
    raw[0] = local_id
    struct.pack_into("<HH", raw, 4, x, y)
    raw[8] = elevation & 0xFF
    struct.pack_into("<HH", raw, 12, 0 if talk_start else 1, 0 if talk_start else sight_range)
    struct.pack_into("<I", raw, 16, 0)
    struct.pack_into("<H", raw, 20, 0)
    return {"data_hex": raw.hex(), "fixups": [{"offset": 16, "target": "SCRIPT_KEY"}]}


def build_event_header(object_count: int, old_counts: Mapping[str, int]) -> dict[str, Any]:
    """Build a relocatable event header retaining the three non-object arrays."""
    if not 0 <= object_count <= OBJECT_LIMIT:
        raise KantoPlanError(f"map object cap exceeded: {object_count}")
    raw = bytearray(struct.pack("<BBBBIIII", object_count, int(old_counts["warps"]),
                                int(old_counts["coords"]), int(old_counts["bg"]), 0, 0, 0, 0))
    fixups = []
    if object_count:
        fixups.append({"offset": 4, "target": "OBJECT_TABLE"})
    for offset, key in ((8, "WARPS"), (12, "COORDS"), (16, "BG")):
        if int(old_counts[key.lower()]):
            fixups.append({"offset": offset, "target": f"PRESERVED_{key}"})
    return {"data_hex": raw.hex(), "fixups": fixups}


def _msgbox_script(text_key: str, *, release: bool = True) -> dict[str, Any]:
    raw = bytearray([_SCRIPT_OP["loadword"], 0, 0, 0, 0, 0,
                     _SCRIPT_OP["callstd"], 4])
    if release:
        raw.append(_SCRIPT_OP["release"])
    raw.append(_SCRIPT_OP["end"])
    return {"data_hex": raw.hex(), "fixups": [{"offset": 2, "target": text_key}]}


def build_trainer_scripts(script_key: str, trainer_id: int, local_id: int,
                          battle_format: str, unlock_expression: str,
                          defeat_flag: int, text_keys: Mapping[str, str]) -> list[dict[str, Any]]:
    """Emit gate/battle/locked script fragments with symbolic pointer fixups."""
    if not 0 <= trainer_id <= 0xFFFF or not 0 <= defeat_flag <= 0xFFFF:
        raise KantoPlanError("trainer id/defeat flag outside event ABI")
    if battle_format not in {"SINGLE", "DOUBLE"}:
        raise KantoPlanError(f"unsupported battle format: {battle_format}")
    gate = bytearray([_SCRIPT_OP["lock"], _SCRIPT_OP["faceplayer"]])
    gate_fixups: list[dict[str, Any]] = []

    def check(flag: int, condition: int, target: str) -> None:
        gate.extend([_SCRIPT_OP["checkflag"]])
        gate.extend(struct.pack("<H", flag))
        gate.extend([_SCRIPT_OP["goto_if"], condition])
        at = len(gate)
        gate.extend(b"\0\0\0\0")
        gate_fixups.append({"offset": at, "target": target})

    locked_key = f"{script_key}::locked"
    # All normal Kanto gates accept Hall of Fame.  The portal fallback is the
    # conjunction used by the existing Kanto entry script.
    if unlock_expression == "KANTO_REGION_ACTIVE":
        check(FLAG_SYS_GAME_CLEAR, 1, f"{script_key}::battle")
        check(FLAG_BADGE01_GET, 0, locked_key)
        check(FLAG_KANTO_PORTAL_READY, 0, locked_key)
    elif unlock_expression.startswith("KANTO_CERT_COUNT>="):
        required = int(unlock_expression.rsplit(">=", 1)[1])
        if not 1 <= required <= 8:
            raise KantoPlanError(f"invalid certification gate: {unlock_expression}")
        check(CERT_FLAG_BASE + required - 1, 0, locked_key)
    elif unlock_expression in {"POSTGAME", "HALL_OF_FAME", "FLAG_SYS_GAME_CLEAR"}:
        check(FLAG_SYS_GAME_CLEAR, 0, locked_key)
    elif unlock_expression not in {"TRUE", "NONE"}:
        raise KantoPlanError(f"unsupported unlock expression: {unlock_expression}")
    gate.append(_SCRIPT_OP["goto"])
    gate_at = len(gate)
    gate.extend(b"\0\0\0\0")
    gate_fixups.append({"offset": gate_at, "target": f"{script_key}::battle"})

    kind = 4 if battle_format == "DOUBLE" else 0
    battle = bytearray([_SCRIPT_OP["trainerbattle"], kind])
    # FireRed's trainerbattle_single/double macros always encode command-local
    # id 0. The physical ObjectEvent local id is separate plan metadata.
    battle.extend(struct.pack("<HH", trainer_id, 0))
    battle_fixups = []
    for target in (text_keys["intro"], text_keys["defeat"]):
        at = len(battle)
        battle.extend(b"\0\0\0\0")
        battle_fixups.append({"offset": at, "target": target})
    if kind == 4:
        at = len(battle)
        battle.extend(b"\0\0\0\0")
        battle_fixups.append({"offset": at, "target": text_keys["not_enough"]})
    battle.extend([_SCRIPT_OP["setflag"]])
    battle.extend(struct.pack("<H", defeat_flag))
    battle.extend([_SCRIPT_OP["loadword"], 0])
    post_at = len(battle)
    battle.extend(b"\0\0\0\0")
    battle_fixups.append({"offset": post_at, "target": text_keys["post"]})
    battle.extend([_SCRIPT_OP["callstd"], 4, _SCRIPT_OP["release"], _SCRIPT_OP["end"]])

    return [
        {"script_key": script_key, "role": "gate", "data_hex": gate.hex(), "fixups": gate_fixups},
        {"script_key": f"{script_key}::battle", "role": "trainerbattle", "kind": kind,
         "trainer_id": trainer_id, "object_local_id": local_id,
         "command_local_id": 0, "command_offset": 0,
         "data_hex": battle.hex(),
         "fixups": battle_fixups},
        {"script_key": locked_key, "role": "locked", **_msgbox_script(text_keys["locked"])},
    ]


# Each author-written Kanto line is replaced as a complete sentence, not by a
# lossy per-character transliteration.  This keeps the current 1-byte font ABI.
_DIALOGUE_NORMALIZATION = {
    "固めた守りを、丁寧に崩されたな。": "かためた まもりを\nていねいに くずされたな。",
    "足場が悪くても、こちらの守りは崩れん\\nぞ。": "あしばが わるくても\nこちらの まもりは くずれんぞ。",
    "今はまだこの先の認定戦を受けられない\\n。先に条件を整えよう。": "いまは まだ すすめない。\nさきに じゅんびを ととのえよう。",
    "カントーでは一本道ほど危ない。回復と\\n帰路を先に確かめな。": "カントーの いっぽんみちは\nきけんだ。かえりみちも みておけ。",
    "波を乗り継ぐ前に、止められちゃった。": "なみに のるまえに\nとめられちゃった。",
    "波を止めても、次の流れはすぐに来るよ\\n。": "なみを とめても\nつぎの なみは すぐに くるよ。",
    "仮説より、君の対応が一枚上だった。": "よみより きみの うごきが\nいちまい うえだった。",
    "理論どおりに動くか、実戦で確かめよう\\n。": "よみどおりに うごくか\nしょうぶで たしかめよう。",
    "対応が速い。こちらの変化についてきた\\nね。": "たいおうが はやい。\nこちらの へんかに ついてきたね。",
    "育て方の違いを、動きで見せてあげる。": "そだてかたの ちがいを\nうごきで みせてあげる。",
    "最後まで迷わなかったね。強い意志だよ\\n。": "さいごまで まよわなかったね。\nつよい こころだよ。",
    "見えないものほど、戦いを長く支配する\\nの。": "みえない ちからほど\nしょうぶを ながく うごかすの。",
    "先を読んだ上で、さらに先を選んだのか\\n。": "さきを よんで\nさらに さきを えらんだのか。",
    "次の一手は読めても、受け切れるとは限\\nらない。": "つぎの てが よめても\nうけきれるとは かぎらない。",
    "役割を見抜いて、順に崩したんだね。": "やくわりを みぬいて\nじゅんに くずしたんだね。",
    "手持ちの役割は全部違う。崩せるかな？": "てもちの やくわりは\nみんな ちがう。くずせるかな？",
    "急所ではなく、組み立てで負けたか。": "きゅうしょでなく\nくみたてで まけたか。",
    "一撃だけを狙わない。崩してから決める\\n！": "いちげきに たよらない。\nくずしてから きめる！",
    "竜の圧を受けても、隊列を崩さないとは\\n。": "りゅうの ちからを うけても\nならびを くずさないとは。",
    "力だけでは竜を扱えない。順番が大事だ\\n。": "ちからだけでは だめだ。\nじゅんばんが だいじだ。",
    "こちらの二つ目の勝ち筋まで消されたか\\n。": "こちらの ふたつめの みちまで\nけされたか。",
    "勝ち筋は一つじゃない。全部ふさいでみ\\nな。": "かつ みちは ひとつじゃない。\nぜんぶ ふさいでみな。",
    "かわいいだけで選んでないよ。動きまで\\n見てね。": "かわいいだけじゃ ないよ。\nうごきまで みてね。",
    "糸を張る前に、流れを切られたか……。": "いとを はるまえに\nながれを きられたか…。",
    "この辺の虫たちは、ただ素早いだけじゃ\\nないよ。": "ここの むしたちは\nすばやいだけじゃ ないよ。",
    "数値外の判断……再計算が必要だ。": "よそうがいの うごき…。\nもういちど かんがえよう。",
    "計画の邪魔はさせない。実験部隊、戦闘\\n開始！": "けいかくの じゃまは させない。\nじっけんたい しょうぶ かいし！",
    "最初から全力だ！一手もむだにしないぞ\\n！": "さいしょから ぜんりょくだ！\nひとて たりとも むだにしないぞ！",
    "休憩の前に一勝負。景色ごと楽しもうよ\\n。": "ひとやすみの まえに しょうぶ。\nけしきも たのしもうよ。",
    "流れを読まれた。見事な合わせ方だ。": "ながれを よまれた。\nみごとな あわせかただ。",
    "待つだけが釣りじゃない。流れを読むん\\nだ。": "まつだけが つりじゃない。\nながれを よむんだ。",
    "同じ型には頼らない。こちらの流れで行\\nくよ。": "おなじ かたには たよらない。\nこちらの ながれで いくよ。",
    "道具と交代を使えば、長い道でも戦い抜\\nけるさ。": "どうぐと こうたいが あれば\nながい みちでも たたかえるさ。",
    "二人分の手数を一つにする。先発から連\\n携するよ！": "ふたりの うごきを ひとつに。\nさいしょから れんけいするよ！",
    "ダブルバトルには、戦えるポケモンが二\\n匹必要だよ。": "ダブルバトルには\nポケモンが 2ひき ひつようだよ。",
}


def normalize_dialogue_text(text: str) -> str:
    """Normalize one of the 35 Task 06 prose bodies to the fixed charmap."""
    key = text.replace("\r\n", "\n")
    if key in _DIALOGUE_NORMALIZATION:
        return _DIALOGUE_NORMALIZATION[key]
    # csv preserves authored control sequences, while some callers decode them.
    escaped = key.replace("\n", "\\n")
    if escaped in _DIALOGUE_NORMALIZATION:
        return _DIALOGUE_NORMALIZATION[escaped]
    raise KantoPlanError(f"dialogue normalization is not authored for: {text!r}")


def _charmap(repo_root: Path) -> tuple[dict[str, int], list[str]]:
    mapping: dict[str, int] = {}
    for line in (repo_root / "vendor/upstream/CFRU-JP/charmap.tbl").read_text(
            encoding="utf-8-sig").splitlines():
        if len(line) < 3 or line[2] != "=":
            continue
        try:
            mapping.setdefault(line[3:], int(line[:2], 16))
        except ValueError:
            pass
    tokens = sorted((token for token in mapping if token and token != "$"),
                    key=lambda token: (-len(token), token))
    return mapping, tokens


def encode_dialogue_text(repo_root: Path, text: str, *, width: int = 18) -> bytes:
    """Encode normalized text and fail if a rendered line exceeds the ABI width."""
    mapping, tokens = _charmap(repo_root)
    source = text.replace("\r\n", "\n").replace("\n", "\\n")
    raw = bytearray()
    line_width = 0
    cursor = 0
    while cursor < len(source):
        for token in tokens:
            if source.startswith(token, cursor):
                if token in {"\\n", "\\p"}:
                    line_width = 0
                else:
                    line_width += 1
                    if line_width > width:
                        raise KantoPlanError(f"dialogue line exceeds width {width}: {text!r}")
                raw.append(mapping[token])
                cursor += len(token)
                break
        else:
            raise KantoPlanError(f"unencodable normalized dialogue at {source[cursor:]!r}")
    raw.append(0xFF)
    return bytes(raw)


def _layout_blockdata(repo_root: Path, row: Mapping[str, Any]) -> tuple[int, int, list[int]]:
    layout_id = str(row["map_header"]["layout"])
    catalog = json.loads((repo_root /
        "vendor/upstream/pokefirered/data/layouts/layouts.json").read_text(encoding="utf-8"))
    item = next((value for value in catalog["layouts"] if value.get("id") == layout_id), None)
    if item is None:
        raise KantoPlanError(f"layout missing from catalogue: {layout_id}")
    raw = (repo_root / "vendor/upstream/pokefirered" / item["blockdata_filepath"]).read_bytes()
    width, height = int(item["width"]), int(item["height"])
    if len(raw) != width * height * 2:
        raise KantoPlanError(f"layout blockdata size drift: {layout_id}")
    return width, height, list(struct.unpack(f"<{width * height}H", raw))


def _walkable(blocks: Sequence[int], width: int, height: int,
              x: int, y: int, elevation: int) -> bool:
    if not (0 <= x < width and 0 <= y < height):
        return False
    value = blocks[y * width + x]
    collision = (value >> 10) & 3
    tile_elevation = (value >> 12) & 0xF
    return collision == 0 and tile_elevation in {0, elevation}


def _neighbors(x: int, y: int) -> Iterable[tuple[int, int]]:
    yield x, y - 1
    yield x - 1, y
    yield x + 1, y
    yield x, y + 1


def _movement_direction(value: str) -> tuple[int, int] | None:
    if value.endswith("FACE_UP"):
        return 0, -1
    if value.endswith("FACE_DOWN"):
        return 0, 1
    if value.endswith("FACE_LEFT"):
        return -1, 0
    if value.endswith("FACE_RIGHT"):
        return 1, 0
    return None


def _placement_audit(blocks: Sequence[int], width: int, height: int, x: int, y: int,
                     elevation: int, sight: int, movement: str,
                     reserved: set[tuple[int, int]]) -> dict[str, Any]:
    adjacent = [(nx, ny) for nx, ny in _neighbors(x, y)
                if _walkable(blocks, width, height, nx, ny, elevation)
                and (nx, ny) not in reserved]
    direction = _movement_direction(movement)
    sightline: list[list[int]] = []
    if direction and sight:
        dx, dy = direction
        for distance in range(1, sight + 1):
            point = (x + dx * distance, y + dy * distance)
            if not _walkable(blocks, width, height, *point, elevation):
                break
            sightline.append([point[0], point[1]])
    sight_set = {tuple(point) for point in sightline}
    avoidable = sight == 0 or direction is None or any(point not in sight_set for point in adjacent)
    return {"walkable": _walkable(blocks, width, height, x, y, elevation),
            "adjacent_walkable": len(adjacent), "sightline": sightline,
            "avoidable_path": avoidable}


def _nearest_safe_tile(blocks: Sequence[int], width: int, height: int,
                       origin: tuple[int, int], elevation: int,
                       reserved: set[tuple[int, int]], *,
                       allowed: set[tuple[int, int]] | None = None) -> tuple[int, int]:
    ox, oy = origin
    candidates = []
    for y in range(height):
        for x in range(width):
            if ((x, y) in reserved or (allowed is not None and (x, y) not in allowed)
                    or not _walkable(blocks, width, height, x, y, elevation)):
                continue
            if not any(_walkable(blocks, width, height, nx, ny, elevation)
                       and (nx, ny) not in reserved for nx, ny in _neighbors(x, y)):
                continue
            candidates.append((abs(x - ox) + abs(y - oy), y, x))
    if not candidates:
        raise KantoPlanError(f"no safe relocation tile near {origin}")
    _, y, x = min(candidates)
    return x, y


def _reachable_tiles(map_row: Mapping[str, Any], blocks: Sequence[int], width: int,
                     height: int, elevation: int = 3) -> set[tuple[int, int]]:
    """Return walkable tiles connected to a physical warp/edge entrance."""
    seeds: set[tuple[int, int]] = set()
    for warp in map_row.get("warps", []):
        x, y = int(warp["x"]), int(warp["y"])
        if _walkable(blocks, width, height, x, y, elevation):
            seeds.add((x, y))
        seeds.update((nx, ny) for nx, ny in _neighbors(x, y)
                     if _walkable(blocks, width, height, nx, ny, elevation))
    if map_row.get("connections"):
        for x in range(width):
            for y in (0, height - 1):
                if _walkable(blocks, width, height, x, y, elevation):
                    seeds.add((x, y))
        for y in range(height):
            for x in (0, width - 1):
                if _walkable(blocks, width, height, x, y, elevation):
                    seeds.add((x, y))
    reached = set(seeds)
    pending = deque(seeds)
    while pending:
        x, y = pending.popleft()
        for point in _neighbors(x, y):
            if point not in reached and _walkable(blocks, width, height, *point, elevation):
                reached.add(point)
                pending.append(point)
    return reached


def _text_plan(repo_root: Path, dialogues: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], str]]:
    output: list[dict[str, Any]] = []
    keys: dict[tuple[str, str], str] = {}
    seen: dict[str, str] = {}
    for row in dialogues:
        normalized = normalize_dialogue_text(row["text"])
        digest = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        text_key = seen.setdefault(normalized, f"text::kanto::{digest}")
        keys[(row["encounter_key"], row["state_key"])] = text_key
        if not any(item["text_key"] == text_key for item in output):
            encoded = encode_dialogue_text(repo_root, normalized)
            output.append({"text_key": text_key, "normalized_text": normalized,
                           "data_hex": encoded.hex(), "sha256": _sha(encoded)})
    return output, keys


def _generic_text(repo_root: Path, key: str, text: str) -> dict[str, Any]:
    encoded = encode_dialogue_text(repo_root, text)
    return {"text_key": key, "normalized_text": text, "data_hex": encoded.hex(),
            "sha256": _sha(encoded)}


def _archive_identity(row: Mapping[str, object], index: int) -> tuple[str, int, str]:
    key = str(row.get("encounter_key") or row.get("command_key") or
              row.get("trainer_key") or f"ARCHIVE_{index + 1:03d}")
    try:
        trainer_id = int(row["trainer_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise KantoPlanError(f"Archive {key}: trainer_id is required") from exc
    battle = str(row.get("battle_format") or row.get("battle_type") or "SINGLE")
    battle = "DOUBLE" if "DOUBLE" in battle else "SINGLE" if "SINGLE" in battle else battle
    if battle not in {"SINGLE", "DOUBLE"}:
        raise KantoPlanError(f"Archive {key}: unsupported battle format {battle}")
    return key, trainer_id, battle


def build_kanto_event_plan(stage_rom: bytes, clean_rom: bytes, repo_root: Path,
                           task06_dir: Path, *,
                           archive_rows: Sequence[Mapping[str, object]] = (),
                           archive_dialogue_rows: Sequence[Mapping[str, object]] = (),
                           acquisition_metadata: Mapping[str, object] | None = None) -> dict[str, Any]:
    """Build the complete JSON-safe Kanto/Trainer Archive physical event plan."""
    repo_root, task06_dir = Path(repo_root), Path(task06_dir)
    encounters = _csv(task06_dir / "data/trainer_encounters.csv")
    dialogues = _csv(task06_dir / "data/trainer_dialogue.csv")
    rewards = {row["encounter_key"]: row for row in
               _csv(task06_dir / "data/trainer_rewards.csv")}
    if len(encounters) != 201 or len(dialogues) != 814:
        raise KantoPlanError(f"Task06 cardinality drift: {len(encounters)} encounters, {len(dialogues)} dialogue rows")
    if len({row["encounter_key"] for row in encounters}) != 201:
        raise KantoPlanError("Task06 encounter keys are not unique")
    if any(rewards[row["encounter_key"]]["reward_kind"] != "AUTO_PRIZE_MONEY"
           for row in encounters if row["status"] != "EXISTING_ROM_VERIFIED"):
        raise KantoPlanError("new Kanto encounter has a non-automatic reward")

    catalog = _read_map_catalog(repo_root)
    text_rows, dialogue_keys = _text_plan(repo_root, dialogues)
    archive_dialogue_keys: dict[tuple[str, str], str] = {}
    for row in archive_dialogue_rows:
        encounter_key = str(row.get("encounter_key") or row.get("command_key") or "")
        state_key = str(row.get("state_key") or "")
        if not encounter_key or not state_key:
            raise KantoPlanError("Archive dialogue requires encounter_key and state_key")
        text_key = str(row.get("text_key") or
                       f"text::archive::{hashlib.sha256((encounter_key + ':' + state_key).encode()).hexdigest()[:16]}")
        encoded_hex = str(row.get("encoded_hex") or "")
        normalized = str(row.get("normalized_text") or row.get("text") or "")
        if encoded_hex:
            try:
                encoded = bytes.fromhex(encoded_hex)
            except ValueError as exc:
                raise KantoPlanError(f"{text_key}: invalid encoded_hex") from exc
            if not encoded or encoded[-1] != 0xFF:
                raise KantoPlanError(f"{text_key}: encoded dialogue lacks 0xFF terminator")
        elif normalized:
            encoded = encode_dialogue_text(repo_root, normalized)
            encoded_hex = encoded.hex()
        else:
            raise KantoPlanError(f"{text_key}: encoded_hex or normalized text is required")
        archive_dialogue_keys[(encounter_key, state_key)] = text_key
        if not any(item["text_key"] == text_key for item in text_rows):
            text_rows.append({"text_key": text_key, "normalized_text": normalized,
                              "data_hex": encoded_hex, "sha256": _sha(encoded)})
    generic = {
        "post": "text::kanto::post",
        "locked": "text::kanto::locked",
        "not_enough": "text::kanto::not_enough",
        "archive_intro": "text::archive::intro",
        "archive_defeat": "text::archive::defeat",
        "archive_post": "text::archive::post",
        "archive_locked": "text::archive::locked",
    }
    text_rows += [
        _generic_text(repo_root, generic["post"], "みごとな しょうりだ。\nまた しょうぶしよう。"),
        _generic_text(repo_root, generic["locked"], "まだ ちょうせん できない。\nさきに すすもう。"),
        _generic_text(repo_root, generic["not_enough"], "ダブルバトルには\nポケモンが 2ひき ひつようだ。"),
        _generic_text(repo_root, generic["archive_intro"], "きろくの しょうぶを\nはじめよう。"),
        _generic_text(repo_root, generic["archive_defeat"], "きみの しょうりだ。"),
        _generic_text(repo_root, generic["archive_post"], "きろくは のこった。\nまた いどんしてくれ。"),
        _generic_text(repo_root, generic["archive_locked"], "でんどういりの あとに\nまた きてくれ。"),
    ]

    map_states: dict[str, dict[str, Any]] = {}
    map_grids: dict[str, tuple[int, int, list[int]]] = {}
    for key, row in catalog.items():
        group, number = int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"])
        map_states[key] = _stage_map_state(stage_rom, group, number)
        map_grids[key] = _layout_blockdata(repo_root, row)

    acquisition_hosts: set[tuple[int, int, int, int]] = set()
    if acquisition_metadata:
        scripts = acquisition_metadata.get("map_scripts", acquisition_metadata)
        values = scripts.values() if isinstance(scripts, Mapping) else scripts
        for value in values if isinstance(values, Iterable) else ():
            if not isinstance(value, Mapping):
                continue
            try:
                acquisition_hosts.add((int(value["group_id"]), int(value["map_id"]),
                                       int(value["x"]), int(value["y"])))
            except (KeyError, TypeError, ValueError):
                continue

    new_by_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bindings: list[dict[str, Any]] = []
    scripts: list[dict[str, Any]] = []
    relocations: list[dict[str, Any]] = []
    occupied_by_map: dict[str, set[tuple[int, int]]] = {}
    ids_by_map: dict[str, set[int]] = {}
    for key, state in map_states.items():
        occupied_by_map[key] = {(_object_fields(raw)["x"], _object_fields(raw)["y"])
                                for raw in state["objects"]}
        ids_by_map[key] = {_object_fields(raw)["local_id"] for raw in state["objects"]}
        row = catalog[key]
        occupied_by_map[key].update((int(w["x"]), int(w["y"])) for w in row.get("warps", []))
        occupied_by_map[key].update((int(e["x"]), int(e["y"]))
                                    for kind in ("coord_events", "bg_events")
                                    for e in row.get(kind, []))

    def allocate_id(map_key: str) -> int:
        for value in range(1, 0x100):
            if value not in ids_by_map[map_key]:
                ids_by_map[map_key].add(value)
                return value
        raise KantoPlanError(f"{map_key}: local object ids exhausted")

    for encounter in encounters:
        key = encounter["encounter_key"]
        map_key = encounter["physical_map_key"]
        if map_key not in catalog:
            raise KantoPlanError(f"{key}: unknown physical map {map_key}")
        if encounter["status"] == "EXISTING_ROM_VERIFIED":
            source_name = str(catalog[map_key]["map_header"]["source_map"])
            source_objects = _clean_source_objects(repo_root, clean_rom, source_name)
            existing_template_ids = []
            for root_index in _split_ints(encounter["root_index"]):
                template_id, _ = _source_template_trainer_id(
                    clean_rom, source_objects[root_index], source_map=source_name,
                    root_index=root_index,
                    identity_evidence=(encounter["graphics_id"] + " " +
                                       encounter.get("notes", ""))
                )
                existing_template_ids.append(template_id)
            desired_local = _split_ints(encounter["local_id"])[0]
            live_objects = [raw for raw in map_states[map_key]["objects"]
                            if _object_fields(raw)["local_id"] == desired_local]
            if len(live_objects) != 1:
                raise KantoPlanError(f"{key}: existing local object {desired_local} is not unique")
            live_script = _object_fields(live_objects[0])["script_pointer"]
            live_command = _rooted_trainer_command(stage_rom, live_script,
                                                   int(encounter["trainer_id"]),
                                                   f"existing::{key}")
            locked_text_key = dialogue_keys.get((key, "LOCKED"), generic["locked"])
            existing_text_keys = {
                "intro": dialogue_keys[(key, "INTRO")],
                "defeat": dialogue_keys[(key, "DEFEAT")],
                "post": dialogue_keys.get((key, "POST_BATTLE"), generic["post"]),
                "locked": locked_text_key,
                "not_enough": dialogue_keys.get((key, "NOT_ENOUGH_POKEMON"),
                                                   generic["not_enough"]),
            }
            bindings.append({"encounter_key": key, "owner_kind": "EXISTING",
                             "map_key": map_key, "group_id": int(encounter["group_id"]),
                             "map_id": int(encounter["map_id"]),
                             "local_ids": _split_ints(encounter["local_id"]),
                             "script_key": encounter["script_key"],
                             "trainer_id": int(encounter["trainer_id"]),
                             "source_template_trainer_id": existing_template_ids[0],
                             "source_template_trainer_ids": existing_template_ids,
                             "battle_format": "DOUBLE" if "DOUBLE" in encounter["battle_type"] else "SINGLE",
                             "trainerbattle_kind": live_command["kind"],
                             "unlock_expression": encounter["unlock_expression"],
                             "locked_text_key": locked_text_key,
                             "text_keys": existing_text_keys,
                             "existing_object_script_address": live_script,
                             "existing_command_address": live_command["address"],
                             "existing_command_kind": live_command["kind"],
                             "proxy_plan": {"preserve_progression_owner": True,
                                            "preserve_reward_owner": True,
                                            "locked_text_key": locked_text_key,
                                            "task06_text_keys": existing_text_keys,
                                            "delegate_command_address": live_command["address"]}})
            continue
        source_name = str(catalog[map_key]["map_header"]["source_map"])
        source_objects = _clean_source_objects(repo_root, clean_rom, source_name)
        roots, xs, ys = (_split_ints(encounter[name]) for name in ("root_index", "x", "y"))
        movements = encounter["movement_type"].split("+")
        if not (len(roots) == len(xs) == len(ys) == len(movements)):
            raise KantoPlanError(f"{key}: object-pair fields disagree")
        width, height, blocks = map_grids[map_key]
        component_ids: list[int] = []
        component_positions: list[list[int]] = []
        component_template_ids: list[int] = []
        owner_kind = "NORMAL"
        for component, (root, authored_x, authored_y, movement) in enumerate(
                zip(roots, xs, ys, movements)):
            if root >= len(source_objects):
                raise KantoPlanError(f"{key}: source object index {root} outside {source_name}")
            source = source_objects[root]
            fields = _object_fields(source)
            template_trainer_id, template_audit = _source_template_trainer_id(
                clean_rom, source, source_map=source_name, root_index=root
            )
            if (fields["x"], fields["y"], fields["elevation"]) != (
                    authored_x, authored_y, int(encounter["elevation"])):
                raise KantoPlanError(f"{key}: authored coordinate differs from clean source object")
            x, y = authored_x, authored_y
            group, number = int(encounter["group_id"]), int(encounter["map_id"])
            ownership_conflict = (x, y) in occupied_by_map[map_key] or (group, number, x, y) in acquisition_hosts
            if ownership_conflict:
                origin = (x, y)
                x, y = _nearest_safe_tile(blocks, width, height, origin,
                                          fields["elevation"], occupied_by_map[map_key])
                owner_kind = "RELOCATED"
                relocations.append({"encounter_key": key, "component": component,
                                    "map_key": map_key, "from": list(origin), "to": [x, y],
                                    "reason": "BASELINE_OBJECT_OR_ACQUISITION_HOST_CONFLICT"})
            local_id = allocate_id(map_key)
            authored_sight = int(encounter["sight_range"])
            audit = _placement_audit(blocks, width, height, x, y, fields["elevation"],
                                     authored_sight, movement,
                                     occupied_by_map[map_key] - {(x, y)})
            effective_sight = authored_sight
            if audit["walkable"] and not audit["avoidable_path"]:
                # Optional encounters must not seal a one-tile corridor.  The
                # safest mechanical repair is talk-to-start at the authored
                # source coordinate; graphics/movement/party remain intact.
                effective_sight = 0
                audit = _placement_audit(blocks, width, height, x, y, fields["elevation"],
                                         0, movement, occupied_by_map[map_key] - {(x, y)})
                audit["auto_fix"] = {"kind": "SIGHT_RANGE_TO_TALK_START",
                                     "authored": authored_sight, "effective": 0}
            if not audit["walkable"] or not audit["avoidable_path"]:
                raise KantoPlanError(f"{key}: placement lacks walkability/avoidable path")
            record = build_object_record(source, local_id=local_id, x=x, y=y,
                                         elevation=fields["elevation"],
                                         sight_range=effective_sight,
                                         talk_start=effective_sight == 0)
            record["fixups"][0]["target"] = encounter["script_key"]
            occupied_by_map[map_key].add((x, y))
            new_by_map[map_key].append({"owner_kind": owner_kind, "encounter_key": key,
                                        "component": component, "local_id": local_id,
                                        "x": x, "y": y, "elevation": fields["elevation"],
                                        "graphics_id": fields["graphics_id"],
                                        "movement_type": movement,
                                        "sight_range": effective_sight,
                                        "authored_sight_range": authored_sight,
                                        "source_template_trainer_id": template_trainer_id,
                                        "record": record,
                                        "audit": {**audit, "source_template": template_audit}})
            component_ids.append(local_id)
            component_positions.append([x, y])
            component_template_ids.append(template_trainer_id)
        battle_format = "DOUBLE" if "DOUBLE" in encounter["battle_type"] else "SINGLE"
        states = {state: dialogue_keys.get((key, state)) for state in
                  ("INTRO", "DEFEAT", "POST_BATTLE", "NOT_ENOUGH_POKEMON")}
        text_keys = {"intro": states["INTRO"], "defeat": states["DEFEAT"],
                     "post": states["POST_BATTLE"] or generic["post"],
                     "locked": dialogue_keys.get((key, "LOCKED"), generic["locked"]),
                     "not_enough": states["NOT_ENOUGH_POKEMON"] or generic["not_enough"]}
        if not text_keys["intro"] or not text_keys["defeat"]:
            raise KantoPlanError(f"{key}: intro/defeat dialogue missing")
        defeat_flag = 0x0500 + int(encounter["trainer_id"])
        scripts.extend(build_trainer_scripts(encounter["script_key"],
                                             int(encounter["trainer_id"]), component_ids[0],
                                             battle_format, encounter["unlock_expression"],
                                             defeat_flag, text_keys))
        bindings.append({"encounter_key": key, "owner_kind": owner_kind,
                         "map_key": map_key, "group_id": int(encounter["group_id"]),
                         "map_id": int(encounter["map_id"]), "local_ids": component_ids,
                         "positions": component_positions, "script_key": encounter["script_key"],
                         "trainer_id": int(encounter["trainer_id"]),
                         "source_template_trainer_id": component_template_ids[0],
                         "source_template_trainer_ids": component_template_ids,
                         "battle_format": battle_format, "defeat_flag": defeat_flag,
                         "trainerbattle_kind": 4 if battle_format == "DOUBLE" else 0,
                         "text_keys": text_keys,
                         "unlock_expression": encounter["unlock_expression"],
                         "reward_kind": "AUTO_PRIZE_MONEY"})

    # Archive uses a stable safe trainer template. Identity graphics may be supplied
    # by a future row, but absence never blocks physical command preservation.
    archive_template = _clean_source_objects(repo_root, clean_rom, "MtMoon_1F")[0]
    archive_template_id, archive_template_audit = _source_template_trainer_id(
        clean_rom, archive_template, source_map="MtMoon_1F", root_index=0
    )
    archive_candidates = sorted(
        (key for key, row in catalog.items()
         if row["map_header"]["classification"] in {"OUTDOOR", "DUNGEON"}),
        key=lambda key: (-int(catalog[key]["layout"]["width"]) * int(catalog[key]["layout"]["height"]),
                         int(catalog[key]["map_header"]["group_id"]),
                         int(catalog[key]["map_header"]["map_id"]), key))
    archive_map_counts: dict[str, int] = defaultdict(int)
    archive_flags: set[int] = set()
    archive_keys: set[str] = set()
    for index, archive in enumerate(archive_rows):
        archive_key, trainer_id, battle_format = _archive_identity(archive, index)
        if archive_key in archive_keys:
            raise KantoPlanError(f"duplicate Archive command key: {archive_key}")
        archive_keys.add(archive_key)
        selected: tuple[str, int, int, dict[str, Any]] | None = None
        for map_key in archive_candidates:
            current = len(map_states[map_key]["objects"]) + len(new_by_map[map_key])
            if archive_map_counts[map_key] >= 5 or current >= OBJECT_LIMIT:
                continue
            width, height, blocks = map_grids[map_key]
            center = (width // 2, height // 2)
            reachable = _reachable_tiles(catalog[map_key], blocks, width, height)
            if not reachable:
                continue
            try:
                x, y = _nearest_safe_tile(blocks, width, height, center, 3,
                                          occupied_by_map[map_key], allowed=reachable)
            except KantoPlanError:
                continue
            audit = _placement_audit(blocks, width, height, x, y, 3, 0,
                                     "MOVEMENT_TYPE_FACE_DOWN", occupied_by_map[map_key])
            if audit["walkable"] and audit["avoidable_path"] and audit["adjacent_walkable"]:
                audit["reachable_from_entry"] = True
                audit["reachable_component_size"] = len(reachable)
                selected = map_key, x, y, audit
                break
        if selected is None:
            raise KantoPlanError(f"Archive {archive_key}: no map has safe object budget")
        map_key, x, y, audit = selected
        local_id = allocate_id(map_key)
        script_key = f"SCRIPT_TRAINER_ARCHIVE_{index + 1:03d}"
        record = build_object_record(archive_template, local_id=local_id, x=x, y=y,
                                     elevation=3, sight_range=0, talk_start=True)
        record["fixups"][0]["target"] = script_key
        occupied_by_map[map_key].add((x, y))
        archive_map_counts[map_key] += 1
        defeat_flag = 0x1800 + index
        if defeat_flag in archive_flags:
            raise KantoPlanError("Archive defeat flag collision")
        archive_flags.add(defeat_flag)
        new_by_map[map_key].append({"owner_kind": "ARCHIVE", "encounter_key": archive_key,
                                    "component": 0, "local_id": local_id, "x": x, "y": y,
                                    "elevation": 3, "graphics_id": _object_fields(archive_template)["graphics_id"],
                                    "movement_type": "MOVEMENT_TYPE_FACE_DOWN", "sight_range": 0,
                                    "source_template_trainer_id": archive_template_id,
                                    "record": record,
                                    "audit": {**audit, "source_template": archive_template_audit,
                                              "archive_identity_fallback":
                                              "SAFE_TRAINER_GFX_FROM_MT_MOON_1F_OBJECT_0"}})
        supplied = archive.get("text_keys", {})
        if isinstance(supplied, str):
            try:
                supplied = json.loads(supplied)
            except json.JSONDecodeError as exc:
                raise KantoPlanError(f"Archive {archive_key}: text_keys is not JSON") from exc
        if not isinstance(supplied, Mapping):
            raise KantoPlanError(f"Archive {archive_key}: text_keys must be a mapping")
        def archive_text(state: str, generic_key: str) -> str:
            return str(supplied.get(state) or supplied.get(state.lower()) or
                       archive_dialogue_keys.get((archive_key, state), generic_key))
        text_keys = {"intro": archive_text("INTRO", generic["archive_intro"]),
                     "defeat": archive_text("DEFEAT", generic["archive_defeat"]),
                     "post": archive_text("POST_BATTLE", generic["archive_post"]),
                     "locked": archive_text("LOCKED", generic["archive_locked"]),
                     "not_enough": archive_text("NOT_ENOUGH_POKEMON", generic["not_enough"])}
        scripts.extend(build_trainer_scripts(script_key, trainer_id, local_id, battle_format,
                                             "POSTGAME", defeat_flag, text_keys))
        header = catalog[map_key]["map_header"]
        bindings.append({"encounter_key": archive_key, "owner_kind": "ARCHIVE",
                         "archive_index": index, "map_key": map_key,
                         "group_id": int(header["group_id"]), "map_id": int(header["map_id"]),
                         "local_ids": [local_id], "positions": [[x, y]], "script_key": script_key,
                         "trainer_id": trainer_id, "battle_format": battle_format,
                         "trainerbattle_kind": 4 if battle_format == "DOUBLE" else 0,
                         "source_template_trainer_id": archive_template_id,
                         "source_template_trainer_ids": [archive_template_id],
                         "defeat_flag": defeat_flag, "unlock_expression": "POSTGAME",
                         "text_keys": text_keys,
                         "reward_kind": "AUTO_PRIZE_MONEY"})

    maps: list[dict[str, Any]] = []
    for map_key in sorted(new_by_map, key=lambda key: (
            int(catalog[key]["map_header"]["group_id"]),
            int(catalog[key]["map_header"]["map_id"]), key)):
        state = map_states[map_key]
        preserved = state["objects"]
        additions = new_by_map[map_key]
        if len(preserved) + len(additions) > OBJECT_LIMIT:
            raise KantoPlanError(f"{map_key}: object count exceeds {OBJECT_LIMIT}")
        object_table = bytearray(b"".join(preserved))
        fixups = []
        for item in additions:
            relative = len(object_table)
            record = bytes.fromhex(item["record"]["data_hex"])
            object_table.extend(record)
            fixups.append({"offset": relative + 16, "target": item["record"]["fixups"][0]["target"]})
        event = build_event_header(len(preserved) + len(additions), state["counts"])
        header = catalog[map_key]["map_header"]
        maps.append({"map_key": map_key, "group_id": int(header["group_id"]),
                     "map_id": int(header["map_id"]),
                     "map_header_address": state["map_header_address"],
                     "old_event_header_address": state["event_header_address"],
                     "old_event_header_hex": state["event_header_hex"],
                     "preserved_objects": [{"index": i, "record_hex": raw.hex(),
                                            **_object_fields(raw)}
                                           for i, raw in enumerate(preserved)],
                     "new_objects": additions, "object_table_hex": object_table.hex(),
                     "object_table_fixups": fixups, "new_event_header": event,
                     "preserved_arrays": {"warps_hex": state["warps_hex"],
                                          "coords_hex": state["coords_hex"],
                                          "bg_hex": state["bg_hex"]},
                     "patch": {"map_header_pointer_field_address":
                               state["map_header_address"] + 4,
                               "target": f"map::{map_key}::event_header"}})

    counts = defaultdict(int)
    for binding in bindings:
        counts[binding["owner_kind"]] += 1
    return {
        "schema_version": 1,
        "input_sha256": {"stage34_rom": _sha(stage_rom), "clean_rom": _sha(clean_rom)},
        "maps": maps, "scripts": scripts, "texts": text_rows,
        "bindings": bindings, "relocations": relocations,
        "summary": {"task06_encounters": len(encounters), "dialogue_rows": len(dialogues),
                    "existing_bindings": counts["EXISTING"], "normal_bindings": counts["NORMAL"],
                    "relocated_bindings": counts["RELOCATED"],
                    "archive_bindings": counts["ARCHIVE"],
                    "new_object_records": sum(len(row["new_objects"]) for row in maps),
                    "double_bindings": sum(b["battle_format"] == "DOUBLE" for b in bindings),
                    "max_objects_per_map": max((len(row["preserved_objects"]) +
                                                len(row["new_objects"]) for row in maps), default=0),
                    "max_archive_per_map": max(archive_map_counts.values(), default=0)},
    }


def write_plan_json(plan: Mapping[str, object], path: Path) -> None:
    """Convenience serializer; callers still own destination lifecycle."""
    Path(path).write_text(json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")
