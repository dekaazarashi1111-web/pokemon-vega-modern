#!/usr/bin/env python3
"""保存済み73音声bankに限定した圧縮WaveData(type1)の静的read範囲照合。"""
from __future__ import annotations

import struct
from collections import Counter
import pr16_selected_sound_roots as sound

BASE = sound.BASE
TARGETS = sound.TARGETS
CANDIDATE = sound.CANDIDATE
need = sound.need
identity = sound.identity
encode = sound.encode
DPCM_SOURCE = {
    "repository": "pret/pokefirered",
    "commit": "c75f352304d529f6ba92d4f74b9cf8b5c3810788",
    "path": "src/m4a_1.s",
    "git_blob": "4cbbf08129ed6f85f3c730429f6b430627109117",
}
BLOCK_SAMPLES = 64
BLOCK_BYTES = 33


def verify_decoder_source(text: str) -> None:
    """固定公開ARM sourceのUnk2限定。PCM以外に拡張しない。"""
    a = text.index("arm_func_start SoundMainRAM_Unk2")
    b = text.index("arm_func_end SoundMainRAM_Unk2", a)
    block = text[a:b]
    fragments = ("mov r0, r3, lsr 6", "mov r1, 0x21", "mul r2, r1, r0",
                 "add r2, r2, 0x10", "mov r7, 0x40",
                 "ldrb lr, [r2], 1", "ldrb r1, [r2], 1",
                 "ldrb r1, [r2], 1", "subs r7, r7, 2")
    need(all(f in block for f in fragments), "固定DPCM decoder命令形")
    need(block.count("ldrb r1, [r2], 1") == 2, "33byte/blockの読み順")


def wave_type1(raw: bytes, address: int) -> dict:
    """64 samplesにつき先頭sample1byte+delta packed32byte。sample数をbyte数にしない。"""
    start = sound.x.canonical(address)
    need(start % 4 == 0, "WaveData 4byte整列")
    header = sound.read(raw, start, 16)
    kind, status, frequency, loop, sample_count = struct.unpack("<HHIII", header)
    need(kind == 1, "圧縮type1だけ")
    need(status in (0, 0x4000) and 0 < frequency <= 0x4000000, "status/frequency")
    need(0 < sample_count <= 0x200000 and 0 <= loop < sample_count, "sample_count/loop")
    blocks = (sample_count + BLOCK_SAMPLES - 1) // BLOCK_SAMPLES
    consumed_bytes = blocks * BLOCK_BYTES
    data_start = start + 16
    data = sound.read(raw, data_start, consumed_bytes)
    return {
        "address": start, "type": 1, "status": status,
        "frequency": frequency, "loop_start": loop,
        "sample_count": sample_count, "block_samples": BLOCK_SAMPLES,
        "block_bytes": BLOCK_BYTES, "blocks": blocks,
        "consumed_bytes": consumed_bytes, "data_start": data_start,
        "end_exclusive": data_start + consumed_bytes,
        "header_identity": identity(header), "data_identity": identity(data),
        "actual_reader_proven": False,
    }


def blocks_covering(wave: dict, address: int, width: int = 4) -> list[int]:
    """全byteが宣言された実DPCM read区間内。跨りも別blockとして返す。"""
    start, end = wave["data_start"], wave["end_exclusive"]
    need(type(address) is int and type(width) is int and 0 < width <= 256, "read幅")
    if address < start or address + width > end:
        return []
    first = (address - start) // BLOCK_BYTES
    last = (address + width - 1 - start) // BLOCK_BYTES
    return list(range(first, last + 1))


def owner_lineage(provenance: dict, placement: dict, supply: dict, alignment: dict) -> dict:
    """配置ownerに対応する保存済PLA1 archiveと2つの配置台帳の同値だけを検証。"""
    rows = provenance["rows"]
    need([r["address"] for r in rows] == list(TARGETS), "3地点順序")
    known = rows[1]["modernization"]["owners"]
    need(len(known) == 1 and known[0]["name"] == "pr16_supply_pla1"
         and known[0]["full_target_containment"], "PLA1現owner")
    entries = placement["placement"]["allocation"]["allocations"]
    a = [r for r in entries if r["name"] == "pr16_supply_pla1"]
    b = [r for r in alignment["link"]["allocation"]["allocations"] if r["name"] == "pr16_supply_pla1"]
    need(len(a) == len(b) == 1 and a[0] == b[0], "PLA1現在配置/保存台帳一致")
    name = "archive-image.bin"
    archived = supply["data_files"][name]
    archived_aligned = alignment["data_files"][name]
    need(archived == archived_aligned
         and archived == dict(sha256=a[0]["content_sha256"], size=a[0]["size"]),
         "PLA1 archive hash/size")
    need(a[0]["gba_start"] <= TARGETS[1] and TARGETS[1] + 4 <= a[0]["gba_end_exclusive"],
         "対象全4byteがPLA1内")
    need(known[0]["start"] == a[0]["gba_start"]
         and known[0]["end_exclusive"] == a[0]["gba_end_exclusive"]
         and known[0]["owner_offset"] == TARGETS[1] - a[0]["gba_start"]
         and known[0]["current_owner_sha256"] == archived["sha256"], "現owner区間・内容同値")
    need(not rows[0]["modernization"]["owners"]
         and not rows[2]["modernization"]["owners"], "他2点に所有者を創作しない")
    return {
        "address": TARGETS[1], "owner": a[0]["name"], "placement_start": a[0]["gba_start"],
        "placement_end_exclusive": a[0]["gba_end_exclusive"], "owner_offset": known[0]["owner_offset"],
        "source_task": a[0]["owner"], "source_image": name, "source_image_identity": archived,
        "source_checkpoint": "content/modernization/pr16_learnset_supply_checkpoint.json",
        "alignment_checkpoint": "content/modernization/pr16_learnset_supply_alignment_checkpoint.json",
        "placement_checkpoint": "content/modernization/pr16_dex_hof_generation_writer_checkpoint.json",
        "asset_reader_proven": False, "free_space_proven": False,
    }


def inspect_saved_bank_wave_types(raw: bytes, saved_sound: dict, provenance: dict) -> dict:
    """保存bankの元indexだけを読む。旧PCMとnested-rootの再測定は禁止。"""
    need(identity(raw) == CANDIDATE and saved_sound["candidate"] == CANDIDATE
         and provenance["candidate"] == CANDIDATE, "候補SHA/size")
    prev = saved_sound["inspection"]
    need(prev["counts"]["banks"] == len(prev["banks"]) == 73
         and prev["counts"]["tone_records"] == 13194
         and prev["matches"] == [] and saved_sound["match_count"] == 0,
         "保存PCM原本の限定範囲")
    need(saved_sound["targets"] == [
         dict(address=r["address"], **r["current_target_identity"])
         for r in provenance["rows"]], "保存3地点のtype/SHA")
    for row in saved_sound["targets"]:
        need(identity(sound.read(raw, row["address"], 4)) ==
             {k: row[k] for k in ("sha256", "size")}, "選定4byteは現候補に一致")
    roots = prev["banks"]
    stats = Counter()
    waves = {}
    matches = []
    for root in roots:
        base = root["base"]
        indices = root["indices"]
        need(root["root"]["base"] == base
             and root["root"]["indices"] == indices, "保存bank系列一致")
        for index in indices:
            stats["saved_tone_records_checked"] += 1
            at = base + index * 12
            try:
                record = sound.read(raw, at, 12)
                kind = record[0]
                if kind not in (0, 8):
                    stats["not_direct_pcm_type"] += 1
                    continue
                address = struct.unpack_from("<I", record, 4)[0]
                if not sound.ptr(address):
                    stats["not_rom_pointer"] += 1
                    continue
                canonical = sound.x.canonical(address)
                if canonical not in waves:
                    header = sound.read(raw, canonical, 16)
                    if struct.unpack_from("<H", header)[0] != 1:
                        waves[canonical] = None
                    else:
                        try:
                            waves[canonical] = wave_type1(raw, canonical)
                        except ValueError:
                            waves[canonical] = None
                            stats["rejected_type1_header_or_extent"] += 1
                wave = waves[canonical]
                if wave is None:
                    continue
                stats["type1_tone_references"] += 1
                for target in TARGETS:
                    blocks = blocks_covering(wave, target)
                    if blocks:
                        matches.append({
                            "bank": base, "index": index, "tone_address": at,
                            "tone_identity": identity(record), "wave": wave,
                            "target": target, "decoder_blocks_required": blocks,
                            "same_block": len(blocks) == 1,
                            "conditional_reader_extent_only": True,
                            "actual_reader_proven": False,
                        })
            except ValueError:
                stats["rejected_record_or_pointer"] += 1
    need(stats["saved_tone_records_checked"] == 13194, "保存bank元record数不変")
    return {
        "schema_version": 1, "candidate": CANDIDATE,
        "input_sound_identity": identity(encode(saved_sound)),
        "input_provenance_identity": identity(encode(provenance)),
        "fixed_dpcm_source": DPCM_SOURCE,
        "scope": "SAVED_73_BANKS_TYPE1_ONLY_WITHOUT_PCM_REPLAY",
        "stats": dict(sorted(stats.items())),
        "unique_type1_waves": sum(w is not None for w in waves.values()),
        "matches": matches, "match_count": len(matches),
        "matched_targets": sorted(set(m["target"] for m in matches)),
        "actual_asset_reader_proven": False,
        "formal_classification_changes": 0,
        "formal_classified": 789, "formal_unclassified": 85,
        "selected_unknown_origins": 6, "donor_safe_bytes": 0,
        "limitations_ja": [
            "公開DPCM Unk2の64sample/33byteの静的消費範囲。実ROMからのdecoder呼出/再生経路を未証明。",
            "73群の保存済bank/indexだけ。有限root外と旧不採用PCMは再検査しない。",
            "宣言sample数は消費byte数ではなく、末尾の部分64sampleも33byteの読込み単位。",
            "type1が0件でも無い証明ではない。配置owner/IPSだけではasset型や退役を確定しない。",
        ],
    }
