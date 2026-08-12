#!/usr/bin/env python3
"""Analyze direct byte-range conflicts between one IPS patch and one UPS patch.

No ROM is required. The script validates both patch containers, decodes all
modified ranges, and emits JSON/CSV/Markdown reports.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

ROM_BASE = 0x08000000
MIB = 0x100000


@dataclass(frozen=True)
class Range:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def union_ranges(ranges: Iterable[Range]) -> list[Range]:
    ordered = sorted((r for r in ranges if r.end > r.start), key=lambda r: (r.start, r.end))
    result: list[Range] = []
    for current in ordered:
        if not result or current.start > result[-1].end:
            result.append(current)
        elif current.end > result[-1].end:
            result[-1] = Range(result[-1].start, current.end)
    return result


def intersect_ranges(left: Sequence[Range], right: Sequence[Range]) -> list[Range]:
    i = j = 0
    result: list[Range] = []
    while i < len(left) and j < len(right):
        start = max(left[i].start, right[j].start)
        end = min(left[i].end, right[j].end)
        if start < end:
            result.append(Range(start, end))
        if left[i].end < right[j].end:
            i += 1
        else:
            j += 1
    return result


def subtract_ranges(left: Sequence[Range], right: Sequence[Range]) -> list[Range]:
    result: list[Range] = []
    j = 0
    for item in left:
        cursor = item.start
        while j < len(right) and right[j].end <= cursor:
            j += 1
        k = j
        while k < len(right) and right[k].start < item.end:
            if right[k].start > cursor:
                result.append(Range(cursor, min(item.end, right[k].start)))
            cursor = max(cursor, right[k].end)
            if cursor >= item.end:
                break
            k += 1
        if cursor < item.end:
            result.append(Range(cursor, item.end))
    return result


def clip_ranges(ranges: Sequence[Range], low: int, high: int) -> list[Range]:
    return [
        Range(max(r.start, low), min(r.end, high))
        for r in ranges
        if r.start < high and r.end > low
    ]


def total_bytes(ranges: Sequence[Range]) -> int:
    return sum(r.length for r in ranges)


def parse_ips(path: Path) -> dict:
    data = path.read_bytes()
    if not data.startswith(b"PATCH"):
        raise ValueError(f"{path}: invalid IPS header")

    pos = 5
    records: list[Range] = []
    values: dict[int, int] = {}
    raw_bytes = 0
    rle_bytes = 0

    while True:
        if pos + 3 > len(data):
            raise ValueError(f"{path}: truncated IPS before EOF")
        if data[pos : pos + 3] == b"EOF":
            pos += 3
            break

        offset = int.from_bytes(data[pos : pos + 3], "big")
        pos += 3
        if pos + 2 > len(data):
            raise ValueError(f"{path}: truncated IPS record header")
        length = int.from_bytes(data[pos : pos + 2], "big")
        pos += 2

        if length:
            if pos + length > len(data):
                raise ValueError(f"{path}: truncated IPS raw record")
            payload = data[pos : pos + length]
            pos += length
            raw_bytes += length
        else:
            if pos + 3 > len(data):
                raise ValueError(f"{path}: truncated IPS RLE record")
            length = int.from_bytes(data[pos : pos + 2], "big")
            pos += 2
            payload = bytes([data[pos]]) * length
            pos += 1
            rle_bytes += length

        records.append(Range(offset, offset + length))
        for index, byte in enumerate(payload):
            values[offset + index] = byte

    truncate_size = None
    remaining = len(data) - pos
    if remaining == 3:
        truncate_size = int.from_bytes(data[pos : pos + 3], "big")
        pos += 3
    elif remaining != 0:
        raise ValueError(f"{path}: unsupported trailing IPS data ({remaining} bytes)")

    merged = union_ranges(records)
    return {
        "data": data,
        "records": records,
        "ranges": merged,
        "values": values,
        "raw_bytes": raw_bytes,
        "rle_bytes": rle_bytes,
        "truncate_size": truncate_size,
    }


def read_ups_vli(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 1
    while True:
        if pos >= len(data):
            raise ValueError("truncated UPS variable-length integer")
        byte = data[pos]
        pos += 1
        value += (byte & 0x7F) * shift
        if byte & 0x80:
            return value, pos
        shift <<= 7
        value += shift


def parse_ups(path: Path) -> dict:
    data = path.read_bytes()
    if not data.startswith(b"UPS1"):
        raise ValueError(f"{path}: invalid UPS header")
    if len(data) < 16:
        raise ValueError(f"{path}: truncated UPS file")

    pos = 4
    input_size, pos = read_ups_vli(data, pos)
    output_size, pos = read_ups_vli(data, pos)
    footer = len(data) - 12

    offset = 0
    records: list[Range] = []
    xor_values: dict[int, int] = {}

    while pos < footer:
        relative, pos = read_ups_vli(data, pos)
        offset += relative
        start = offset
        while True:
            if pos >= footer:
                raise ValueError(f"{path}: truncated UPS XOR block")
            byte = data[pos]
            pos += 1
            if byte == 0:
                break
            xor_values[offset] = byte
            offset += 1
        records.append(Range(start, offset))
        # UPS offsets include the zero terminator position when advancing.
        offset += 1

    if pos != footer:
        raise ValueError(f"{path}: malformed UPS footer alignment")

    source_crc, target_crc, patch_crc = struct.unpack("<III", data[-12:])
    calculated_patch_crc = zlib.crc32(data[:-4]) & 0xFFFFFFFF
    merged = union_ranges(records)

    return {
        "data": data,
        "records": records,
        "ranges": merged,
        "xor_values": xor_values,
        "input_size": input_size,
        "output_size": output_size,
        "source_crc": source_crc,
        "target_crc": target_crc,
        "patch_crc": patch_crc,
        "calculated_patch_crc": calculated_patch_crc,
    }


def classify(offset: int) -> tuple[str, str]:
    if offset < 0x400:
        return "header/pointer-vector", "critical"
    if offset < 0x200000:
        return "core-engine/hook-area", "critical"
    if offset < 0x500000:
        return "shared-table/data-area", "high"
    if offset < 0x1000000:
        return "occupied-storage/free-space-area", "high"
    return "UPS-extension-area", "low"


def cluster_ranges(ranges: Sequence[Range], maximum_gap: int = 0x100) -> list[dict]:
    clusters: list[dict] = []
    for item in ranges:
        if not clusters or item.start - clusters[-1]["end"] > maximum_gap:
            clusters.append(
                {
                    "start": item.start,
                    "end": item.end,
                    "subranges": 1,
                    "overlap_bytes": item.length,
                }
            )
        else:
            clusters[-1]["end"] = max(clusters[-1]["end"], item.end)
            clusters[-1]["subranges"] += 1
            clusters[-1]["overlap_bytes"] += item.length
    for item in clusters:
        item["span"] = item["end"] - item["start"]
    return clusters


def hex_slice(mapping: dict[int, int], start: int, end: int) -> str:
    return bytes(mapping[index] for index in range(start, end)).hex().upper()


POINTER_PATTERNS = {
    "B0CBE0": {
        "target": "0x08E0CBB0",
        "meaning": "Vega move data table; 0x1800 bytes to 0x08E0E3B0 = 512 entries x 12 bytes",
    },
    "B0BBE0": {
        "target": "0x08E0BBB0",
        "meaning": "Vega move-name table; 0x1000 bytes to 0x08E0CBB0 = 512 entries x 8 bytes",
    },
    "30668B": {
        "target": "0x088B6630",
        "meaning": "Vega egg-move table target; seen at DPE-JP gEggMoves repoint site 0x08045214",
    },
    "B0E3E0": {
        "target": "0x08E0E3B0",
        "meaning": "Vega table immediately following the 512-entry move data table",
    },
    "906869": {
        "target": "0x08696890",
        "meaning": "Vega custom script/data target; exact subsystem unresolved",
    },
}


def infer_pointer_notes(vega_hex: str) -> list[str]:
    notes = []
    for pattern, metadata in POINTER_PATTERNS.items():
        if pattern in vega_hex:
            notes.append(f"{metadata['target']}: {metadata['meaning']}")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ips", type=Path)
    parser.add_argument("ups", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("patch_audit"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ips = parse_ips(args.ips)
    ups = parse_ups(args.ups)

    ips_ranges = ips["ranges"]
    ups_ranges = ups["ranges"]
    overlaps = intersect_ranges(ips_ranges, ups_ranges)
    ips_only = subtract_ranges(ips_ranges, ups_ranges)
    ups_only = subtract_ranges(ups_ranges, ips_ranges)

    input_size = ups["input_size"]
    output_size = ups["output_size"]
    ups_base = clip_ranges(ups_ranges, 0, input_size)
    ups_extension = clip_ranges(ups_ranges, input_size, output_size)

    conflict_rows: list[dict] = []
    for number, item in enumerate(overlaps, start=1):
        area, severity = classify(item.start)
        vega_hex = hex_slice(ips["values"], item.start, item.end)
        pointer_notes = infer_pointer_notes(vega_hex)
        if item.start <= 0x45214 < item.end:
            pointer_notes.append("Exact DPE-JP gEggMoves repoint site: 0x08045214")
        note = "; ".join(pointer_notes)
        conflict_rows.append(
            {
                "id": number,
                "file_offset_start": f"0x{item.start:08X}",
                "file_offset_end_inclusive": f"0x{item.end - 1:08X}",
                "gba_address_start": f"0x{ROM_BASE + item.start:08X}",
                "gba_address_end_inclusive": f"0x{ROM_BASE + item.end - 1:08X}",
                "length": item.length,
                "area": area,
                "severity": severity,
                "vega_ips_output_hex": vega_hex,
                "factory_ups_xor_hex": hex_slice(ups["xor_values"], item.start, item.end),
                "resolution": "PORT" if item.start < 0x500000 else "RELOCATE",
                "note": note,
            }
        )

    length_distribution = Counter(item.length for item in overlaps)
    clusters = cluster_ranges(overlaps)
    clusters_by_overlap = sorted(
        clusters,
        key=lambda item: (item["overlap_bytes"], item["span"]),
        reverse=True,
    )

    per_mib = []
    for low in range(0, output_size, MIB):
        high = min(low + MIB, output_size)
        per_mib.append(
            {
                "start": f"0x{low:08X}",
                "end_inclusive": f"0x{high - 1:08X}",
                "ips_bytes": total_bytes(clip_ranges(ips_ranges, low, high)),
                "ups_bytes": total_bytes(clip_ranges(ups_ranges, low, high)),
                "overlap_bytes": total_bytes(clip_ranges(overlaps, low, high)),
            }
        )

    band_definitions = [
        ("header/pointer-vector", 0, 0x400),
        ("core-engine/hook-area", 0x400, 0x200000),
        ("shared-table/data-area", 0x200000, 0x500000),
        ("occupied-storage/free-space-area", 0x500000, 0x1000000),
        ("UPS-extension-area", 0x1000000, output_size),
    ]
    bands = []
    for name, low, high in band_definitions:
        selected = clip_ranges(overlaps, low, high)
        bands.append(
            {
                "name": name,
                "start": f"0x{low:08X}",
                "end_inclusive": f"0x{high - 1:08X}",
                "range_count": len(selected),
                "overlap_bytes": total_bytes(selected),
            }
        )

    pointer_summary = []
    for pattern, metadata in POINTER_PATTERNS.items():
        matching = [row for row in conflict_rows if pattern in row["vega_ips_output_hex"]]
        pointer_summary.append(
            {
                "vega_pointer_bytes_le": pattern,
                "target": metadata["target"],
                "meaning": metadata["meaning"],
                "conflict_ranges": len(matching),
                "conflict_bytes_in_matching_ranges": sum(row["length"] for row in matching),
            }
        )

    dominant_move_ranges = {
        row["id"]
        for row in conflict_rows
        if "B0CBE0" in row["vega_ips_output_hex"] or "B0BBE0" in row["vega_ips_output_hex"]
    }
    dominant_move_bytes = sum(
        row["length"] for row in conflict_rows if row["id"] in dominant_move_ranges
    )

    report = {
        "inputs": {
            "ips_name": args.ips.name,
            "ips_sha256": sha256(args.ips),
            "ups_name": args.ups.name,
            "ups_sha256": sha256(args.ups),
        },
        "ips": {
            "container_valid": True,
            "patch_file_size": len(ips["data"]),
            "record_count": len(ips["records"]),
            "unique_range_count": len(ips_ranges),
            "raw_declared_bytes": ips["raw_bytes"],
            "rle_declared_bytes": ips["rle_bytes"],
            "unique_modified_bytes": total_bytes(ips_ranges),
            "maximum_modified_offset_inclusive": f"0x{max(r.end for r in ips_ranges) - 1:08X}",
            "truncate_size": ips["truncate_size"],
        },
        "ups": {
            "container_valid": True,
            "patch_crc_valid": ups["patch_crc"] == ups["calculated_patch_crc"],
            "patch_file_size": len(ups["data"]),
            "input_size": input_size,
            "output_size": output_size,
            "source_crc32": f"{ups['source_crc']:08X}",
            "target_crc32": f"{ups['target_crc']:08X}",
            "patch_crc32": f"{ups['patch_crc']:08X}",
            "record_count": len(ups["records"]),
            "unique_range_count": len(ups_ranges),
            "modified_bytes_total": total_bytes(ups_ranges),
            "modified_bytes_in_original_16mib": total_bytes(ups_base),
            "modified_bytes_in_16_to_32mib_extension": total_bytes(ups_extension),
            "maximum_modified_offset_inclusive": f"0x{max(r.end for r in ups_ranges) - 1:08X}",
        },
        "comparison": {
            "direct_overlap_range_count": len(overlaps),
            "direct_overlap_bytes": total_bytes(overlaps),
            "overlap_as_percent_of_vega_changes": round(
                100 * total_bytes(overlaps) / total_bytes(ips_ranges), 8
            ),
            "overlap_as_percent_of_factory_base_changes": round(
                100 * total_bytes(overlaps) / total_bytes(ups_base), 8
            ),
            "vega_only_bytes": total_bytes(ips_only),
            "factory_only_bytes_total": total_bytes(ups_only),
            "factory_only_bytes_in_original_16mib": total_bytes(
                clip_ranges(ups_only, 0, input_size)
            ),
            "factory_only_bytes_in_extension": total_bytes(
                clip_ranges(ups_only, input_size, output_size)
            ),
            "overlap_length_distribution": {
                str(length): count for length, count in sorted(length_distribution.items())
            },
            "cluster_count_with_gap_le_0x100": len(clusters),
            "move_name_or_move_data_pointer_conflict_ranges": len(dominant_move_ranges),
            "move_name_or_move_data_pointer_conflict_bytes": dominant_move_bytes,
            "move_name_or_move_data_share_of_all_overlap_percent": round(
                100 * dominant_move_bytes / total_bytes(overlaps), 8
            ),
        },
        "pointer_target_summary": pointer_summary,
        "bands": bands,
        "per_mib": per_mib,
        "largest_overlap_clusters": [
            {
                "file_offset_start": f"0x{item['start']:08X}",
                "file_offset_end_inclusive": f"0x{item['end'] - 1:08X}",
                "gba_address_start": f"0x{ROM_BASE + item['start']:08X}",
                "gba_address_end_inclusive": f"0x{ROM_BASE + item['end'] - 1:08X}",
                "span": item["span"],
                "subranges": item["subranges"],
                "overlap_bytes": item["overlap_bytes"],
            }
            for item in clusters_by_overlap[:100]
        ],
        "conflicts": conflict_rows,
    }

    json_path = args.out_dir / "conflict_report.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = args.out_dir / "conflicts.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(conflict_rows[0].keys()))
        writer.writeheader()
        writer.writerows(conflict_rows)

    md_path = args.out_dir / "conflict_report.md"
    c = report["comparison"]
    u = report["ups"]
    i = report["ips"]
    lines = [
        "# Vega IPS × Factory UPS 競合監査",
        "",
        "## 判定",
        "",
        "**単純な重ね当てや、重複部分だけ片方を優先する方式では統合できません。**",
        "直接重複は少量ですが、3バイト単位のポインタ／フック候補が多数含まれ、",
        "Vegaのストーリー基盤とDPE/CFRUの拡張テーブルをソース側で接続し直す必要があります。",
        "",
        "## 入力検証",
        "",
        f"- IPS: `{args.ips.name}` / SHA-256 `{report['inputs']['ips_sha256']}`",
        f"- UPS: `{args.ups.name}` / SHA-256 `{report['inputs']['ups_sha256']}`",
        f"- UPS source CRC32: `{u['source_crc32']}`",
        f"- UPS target CRC32: `{u['target_crc32']}`",
        f"- UPS patch CRC32: `{u['patch_crc32']}` / valid: `{u['patch_crc_valid']}`",
        f"- UPS size: {u['input_size']:,} → {u['output_size']:,} bytes",
        "",
        "## 数値結果",
        "",
        "|項目|結果|",
        "|---|---:|",
        f"|Vega IPSの変更量|{i['unique_modified_bytes']:,} bytes|",
        f"|Factory UPSの変更量|{u['modified_bytes_total']:,} bytes|",
        f"|Factoryが元16 MiB内で変更|{u['modified_bytes_in_original_16mib']:,} bytes|",
        f"|Factoryが拡張16–32 MiBへ格納|{u['modified_bytes_in_16_to_32mib_extension']:,} bytes|",
        f"|直接重複|**{c['direct_overlap_bytes']:,} bytes / {c['direct_overlap_range_count']:,} ranges**|",
        f"|Vega変更量に対する重複率|{c['overlap_as_percent_of_vega_changes']:.6f}%|",
        f"|Factoryの元ROM領域変更に対する重複率|{c['overlap_as_percent_of_factory_base_changes']:.6f}%|",
        "",
        "## 重複の性質",
        "",
        f"- 3バイト長: {c['overlap_length_distribution'].get('3', 0)} ranges",
        f"- 1バイト長: {c['overlap_length_distribution'].get('1', 0)} ranges",
        "- GBA ROMポインタは上位バイトが共通のため、IPSが下位3バイトだけ変更する例が多く、",
        "  3バイト競合の多さは単なるデータ衝突ではなく、ポインタ／フック衝突の強い兆候です。",
        "- `0x08045214` は公開DPE-JPの `gEggMoves` repoint siteと一致します。",
        f"- move-name / move-data pointerを含む競合は {c['move_name_or_move_data_pointer_conflict_ranges']} ranges / {c['move_name_or_move_data_pointer_conflict_bytes']} bytes、全重複の {c['move_name_or_move_data_share_of_all_overlap_percent']:.3f}% です。",
        "- Vegaの `0x08E0BBB0` → `0x08E0CBB0` は0x1000 bytesで、512件×8 bytesの技名表と整合します。",
        "- Vegaの `0x08E0CBB0` → `0x08E0E3B0` は0x1800 bytesで、512件×12 bytesの戦闘技データ表と整合します。",
        "- したがって最初の大仕事はSpecies追加ではなく、Vega固有技をCFRUの拡張Move ID空間へ移植することです。",
        "",
        "## ポインタ競合の主要ターゲット",
        "",
        "|Vega pointer|推定対象|競合ranges|該当range bytes|",
        "|---|---|---:|---:|",
    ]
    for item in report["pointer_target_summary"]:
        lines.append(
            f"|{item['target']}|{item['meaning']}|{item['conflict_ranges']}|{item['conflict_bytes_in_matching_ranges']}|"
        )
    lines += [
        "",
        "## 領域別",
        "",
        "|領域|重複ranges|重複bytes|",
        "|---|---:|---:|",
    ]
    for band in bands:
        lines.append(
            f"|{band['name']}|{band['range_count']:,}|{band['overlap_bytes']:,}|"
        )
    lines += [
        "",
        "## 最大の競合クラスター",
        "",
        "|file offset|GBA address|span|subranges|overlap bytes|",
        "|---|---|---:|---:|---:|",
    ]
    for item in report["largest_overlap_clusters"][:20]:
        lines.append(
            f"|{item['file_offset_start']}–{item['file_offset_end_inclusive']}|"
            f"{item['gba_address_start']}–{item['gba_address_end_inclusive']}|"
            f"{item['span']:,}|{item['subranges']:,}|{item['overlap_bytes']:,}|"
        )
    lines += [
        "",
        "## 推奨統合方式",
        "",
        "1. Vegaをストーリー／マップ／イベントの基準ROMにする。",
        "2. Factory UPSを重ねず、DPE-JP/CFRU-JPの公開ソースから機能を移植する。",
        "3. 32 MiB拡張領域へ新コード・新データを再配置する。",
        "4. `conflicts.csv` の `PORT` はVega側ルーチンへ手動接続し直す。",
        "5. `RELOCATE` はVegaが使用中の格納領域を避けて再配置する。",
        "6. Vegaの既存Species IDを固定し、追加ポケモンは後続IDへ割り当てる。",
        "7. 種族名、種族値、画像、アイコン、鳴き声、技、進化、図鑑の全テーブルを同じID対応表から生成する。",
        "8. 野生・トレーナー・進化条件はエンジン安定後に設定する。",
        "",
        "## 制約",
        "",
        "この監査はパッチだけで算出した直接バイト競合です。",
        "真の関数依存、RAM/save-block競合、Species ID意味衝突、スクリプトspecial番号競合は、",
        "クリーンROMから両参照ROMを生成して逆アセンブル／実行テストしないと確定できません。",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report["comparison"], ensure_ascii=False, indent=2))
    print(f"Wrote: {json_path}")
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
