#!/usr/bin/env python3
"""工程4の固定外部素材を私用領域へ決定的に抽出し、追跡可能な台帳を作る。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from tools.modernization_p04_sources import P04SourceError, audit_p04_sources


SCHEMA_VERSION = 1
DEFAULT_MANIFEST_RELATIVE = "content/modernization/p04_asset_import_manifest.json"
DEFAULT_OUTPUT_RELATIVE = "userfile/generated/modernization_p04_assets"
EXPECTED_SOURCE_COMMIT = "cafe0221cefb2a991cc0ece429174ade877d037d"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
KEY_RE = re.compile(r"[A-Z][A-Z0-9_]*")
SOURCE_COMPONENT_RE = re.compile(r"[A-Za-z0-9_.-]+")
STONE_STEM_RE = re.compile(r"[a-z0-9_]+")
ROOT_LICENSE_RE = re.compile(r"(?:LICENSE|LICENCE|COPYING|NOTICE)(?:\..*)?", re.IGNORECASE)


class P04AssetImportError(RuntimeError):
    """素材取込契約を安全に満たせない場合の例外。"""


@dataclass(frozen=True)
class P04AssetBuild:
    """書込み前にメモリ上で確定したmanifestと出力payload。"""

    manifest: dict[str, Any]
    payload: dict[str, bytes]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise P04AssetImportError(message)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise P04AssetImportError(f"JSONを読めません: {path}: {exc}") from exc
    _require(isinstance(value, dict), f"JSON rootはobject必須です: {path}")
    return value


def _canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise P04AssetImportError(f"hash対象を読めません: {path}: {exc}") from exc
    return digest.hexdigest()


def _validate_relative_path(value: str, *, context: str) -> PurePosixPath:
    """外部契約由来のpathをPOSIX相対pathへ限定する。"""
    _require(isinstance(value, str) and bool(value), f"{context}: 空pathは禁止です")
    _require("\\" not in value and "\x00" not in value, f"{context}: path表現が不正です: {value!r}")
    path = PurePosixPath(value)
    _require(not path.is_absolute(), f"{context}: 絶対pathは禁止です: {value}")
    _require(str(path) == value, f"{context}: 正規化前後が違うpathは禁止です: {value}")
    _require(all(part not in {"", ".", ".."} for part in path.parts), f"{context}: path traversalを検出しました: {value}")
    _require(all(SOURCE_COMPONENT_RE.fullmatch(part) is not None for part in path.parts), f"{context}: path文字が不正です: {value}")
    return path


def _source_file(checkout: Path, relative: str, *, context: str) -> Path:
    rel = _validate_relative_path(relative, context=context)
    checkout = checkout.resolve()
    candidate = checkout.joinpath(*rel.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise P04AssetImportError(f"{context}: source fileがありません: {relative}: {exc}") from exc
    _require(resolved == checkout or checkout in resolved.parents, f"{context}: checkout外を参照しています: {relative}")
    _require(candidate.is_file() and not candidate.is_symlink(), f"{context}: 通常file必須です: {relative}")
    return candidate


def _run_git(checkout: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(checkout), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise P04AssetImportError(f"git監査に失敗しました: {checkout}: {detail.strip()}") from exc
    return completed.stdout.strip()


def _assert_checkout_state(checkout: Path, expected_commit: str) -> None:
    """取込直前・直後のHEADとclean状態をfail closedで確認する。"""
    _require(checkout.is_dir(), f"固定source checkoutがありません: {checkout}")
    actual_commit = _run_git(checkout, "rev-parse", "HEAD")
    _require(actual_commit == expected_commit, f"source HEAD不一致: expected={expected_commit}, actual={actual_commit}")
    dirty = _run_git(checkout, "status", "--porcelain", "--untracked-files=all")
    _require(not dirty, f"source checkoutに変更があります: {dirty[:300]}")


def _paeth(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    left_distance = abs(estimate - left)
    above_distance = abs(estimate - above)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def _parse_indexed_png(data: bytes, *, context: str) -> tuple[dict[str, Any], list[int]]:
    """標準libraryだけでindexed PNGを検証し、palette index列を復元する。"""
    _require(data.startswith(PNG_SIGNATURE), f"{context}: PNG signature不正")
    offset = len(PNG_SIGNATURE)
    ihdr: tuple[int, int, int, int, int, int, int] | None = None
    palette_entries: int | None = None
    idat_parts: list[bytes] = []
    saw_iend = False
    while offset < len(data):
        _require(offset + 12 <= len(data), f"{context}: PNG chunk headerが途中で切れています")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        _require(chunk_end <= len(data), f"{context}: PNG chunkが途中で切れています")
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : chunk_end])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        _require(actual_crc == expected_crc, f"{context}: PNG CRC不一致: {chunk_type!r}")
        if chunk_type == b"IHDR":
            _require(ihdr is None and length == 13, f"{context}: PNG IHDR不正")
            ihdr = struct.unpack(">IIBBBBB", payload)
        elif chunk_type == b"PLTE":
            _require(length % 3 == 0 and 1 <= length // 3 <= 256, f"{context}: PNG PLTE不正")
            palette_entries = length // 3
        elif chunk_type == b"IDAT":
            idat_parts.append(payload)
        elif chunk_type == b"IEND":
            _require(length == 0, f"{context}: PNG IEND不正")
            saw_iend = True
            offset = chunk_end
            break
        offset = chunk_end
    _require(saw_iend and offset == len(data), f"{context}: PNG IENDまたは末尾が不正")
    _require(ihdr is not None, f"{context}: PNG IHDRがありません")
    width, height, bit_depth, color_type, compression, filtering, interlace = ihdr
    _require(width > 0 and height > 0, f"{context}: PNG寸法が不正")
    _require(color_type == 3, f"{context}: indexed PNGではありません")
    _require(bit_depth in {1, 2, 4, 8}, f"{context}: indexed PNG bit depthが不正: {bit_depth}")
    _require(compression == 0 and filtering == 0 and interlace == 0, f"{context}: 非対応PNG方式です")
    _require(palette_entries is not None, f"{context}: PNG PLTEがありません")
    _require(bool(idat_parts), f"{context}: PNG IDATがありません")

    decompressor = zlib.decompressobj()
    try:
        raw = decompressor.decompress(b"".join(idat_parts)) + decompressor.flush()
    except zlib.error as exc:
        raise P04AssetImportError(f"{context}: PNG IDAT展開失敗: {exc}") from exc
    _require(decompressor.eof and not decompressor.unused_data and not decompressor.unconsumed_tail, f"{context}: PNG zlib stream不正")
    row_bytes = (width * bit_depth + 7) // 8
    _require(len(raw) == height * (row_bytes + 1), f"{context}: PNG scanline長不一致")

    rows: list[bytes] = []
    previous = bytes(row_bytes)
    for row_number in range(height):
        start = row_number * (row_bytes + 1)
        filter_type = raw[start]
        encoded = raw[start + 1 : start + 1 + row_bytes]
        _require(filter_type <= 4, f"{context}: PNG filter不正: {filter_type}")
        decoded = bytearray(row_bytes)
        for index, current in enumerate(encoded):
            left = decoded[index - 1] if index else 0
            above = previous[index]
            upper_left = previous[index - 1] if index else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            else:
                predictor = _paeth(left, above, upper_left)
            decoded[index] = (current + predictor) & 0xFF
        previous = bytes(decoded)
        rows.append(previous)

    mask = (1 << bit_depth) - 1
    pixels: list[int] = []
    for row in rows:
        for x in range(width):
            bit_offset = x * bit_depth
            byte_index = bit_offset // 8
            shift = 8 - bit_depth - (bit_offset % 8)
            pixels.append((row[byte_index] >> shift) & mask)
    maximum_index = max(pixels)
    _require(maximum_index < palette_entries, f"{context}: PNG indexがPLTE範囲外です")
    _require(maximum_index < 16, f"{context}: GBA 4bppへ変換できないpalette indexです: {maximum_index}")
    _require(width % 8 == 0 and height % 8 == 0, f"{context}: GBA 8x8 tile境界に揃っていません")
    metadata = {
        "format": "PNG",
        "indexed": True,
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "png_palette_entries": palette_entries,
        "maximum_used_palette_index": maximum_index,
        "tiles_wide": width // 8,
        "tiles_high": height // 8,
        "tile_count": (width // 8) * (height // 8),
    }
    return metadata, pixels


def _encode_gba_4bpp(pixels: list[int], width: int, height: int) -> bytes:
    """8x8 tileを横優先に並べ、左pixelを下位nibbleへ格納する。"""
    _require(len(pixels) == width * height, "4bpp変換のpixel数が寸法と一致しません")
    _require(width % 8 == 0 and height % 8 == 0, "4bpp変換寸法がtile境界に揃っていません")
    _require(all(0 <= pixel < 16 for pixel in pixels), "4bpp範囲外のpixelがあります")
    output = bytearray()
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            for row in range(8):
                base = (tile_y + row) * width + tile_x
                for column in range(0, 8, 2):
                    output.append(pixels[base + column] | (pixels[base + column + 1] << 4))
    return bytes(output)


def _parse_jasc_palette(data: bytes, *, context: str) -> tuple[dict[str, Any], list[tuple[int, int, int]], bytes, bytes]:
    """JASC-PALを厳密に読み、LF表現とGBA BGR555表現へ正規化する。"""
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise P04AssetImportError(f"{context}: paletteはASCII必須です") from exc
    _require(len(lines) >= 4 and lines[0] == "JASC-PAL" and lines[1] == "0100", f"{context}: JASC-PAL header不正")
    try:
        declared = int(lines[2])
    except ValueError as exc:
        raise P04AssetImportError(f"{context}: palette色数が整数ではありません") from exc
    _require(1 <= declared <= 16, f"{context}: GBA 4bpp範囲のpaletteではありません: {declared}")
    _require(len(lines) == 3 + declared, f"{context}: palette宣言色数と行数が一致しません")
    colors: list[tuple[int, int, int]] = []
    for line_number, line in enumerate(lines[3:], start=4):
        try:
            rgb = tuple(int(part) for part in line.split())
        except ValueError as exc:
            raise P04AssetImportError(f"{context}:{line_number}: RGB値が整数ではありません") from exc
        _require(len(rgb) == 3 and all(0 <= value <= 255 for value in rgb), f"{context}:{line_number}: RGB値不正")
        colors.append((rgb[0], rgb[1], rgb[2]))
    canonical_lines = ["JASC-PAL", "0100", str(declared), *(f"{r} {g} {b}" for r, g, b in colors)]
    canonical = ("\n".join(canonical_lines) + "\n").encode("ascii")
    gba = b"".join(
        struct.pack("<H", ((blue // 8) << 10) | ((green // 8) << 5) | (red // 8))
        for red, green, blue in colors
    )
    metadata = {
        "format": "JASC-PAL",
        "version": "0100",
        "declared_colors": declared,
        "actual_colors": len(colors),
        "gba_palette_bytes": len(gba),
    }
    return metadata, colors, canonical, gba


def _aggregate_hash(entries: Iterable[tuple[str, str]]) -> str:
    """relative pathと各file SHA-256から集合hashを作る。"""
    digest = hashlib.sha256()
    for relative, file_hash in sorted(set(entries)):
        _validate_relative_path(relative, context="aggregate path")
        _require(SHA256_RE.fullmatch(file_hash) is not None, f"aggregate file hash不正: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _add_payload(payload: dict[str, bytes], relative: str, data: bytes) -> None:
    _validate_relative_path(relative, context="output path")
    _require(relative not in payload, f"出力pathが重複しています: {relative}")
    payload[relative] = data


def _source_descriptor(relative: str, data: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "relative_path": relative,
        "size": len(data),
        "sha256": _sha256_bytes(data),
        "metadata": metadata,
    }


def _output_descriptor(relative: str, data: bytes, *, format_name: str, normalization: str) -> dict[str, Any]:
    return {
        "relative_path": relative,
        "size": len(data),
        "sha256": _sha256_bytes(data),
        "format": format_name,
        "normalization": normalization,
    }


def _make_png_asset(
    checkout: Path,
    source_relative: str,
    output_base: str,
    filename: str,
    expected_dimensions: tuple[int, int],
    payload: dict[str, bytes],
    source_files: dict[str, tuple[int, str]],
) -> tuple[dict[str, Any], int]:
    source_path = _source_file(checkout, source_relative, context=source_relative)
    data = source_path.read_bytes()
    metadata, pixels = _parse_indexed_png(data, context=source_relative)
    actual_dimensions = (metadata["width"], metadata["height"])
    _require(actual_dimensions == expected_dimensions, f"{source_relative}: 寸法不一致: {actual_dimensions}")
    converted = _encode_gba_4bpp(pixels, metadata["width"], metadata["height"])
    expected_size = metadata["width"] * metadata["height"] // 2
    _require(len(converted) == expected_size, f"{source_relative}: 4bpp出力size不一致")
    mirror_relative = f"{output_base}/{filename}"
    converted_relative = f"{output_base}/{Path(filename).stem}.4bpp"
    _add_payload(payload, mirror_relative, data)
    _add_payload(payload, converted_relative, converted)
    source_hash = _sha256_bytes(data)
    source_files[source_relative] = (len(data), source_hash)
    return {
        "role": Path(filename).stem.upper(),
        "source": _source_descriptor(source_relative, data, metadata),
        "normalized": _output_descriptor(
            mirror_relative,
            data,
            format_name="INDEXED_PNG",
            normalization="BYTE_EXACT_SOURCE_MIRROR",
        ),
        "gba_conversion": _output_descriptor(
            converted_relative,
            converted,
            format_name="GBA_4BPP_TILES_8X8_ROW_MAJOR",
            normalization="LEFT_PIXEL_LOW_NIBBLE",
        ) | {"status": "CONVERTED"},
    }, metadata["maximum_used_palette_index"]


def _make_palette_asset(
    checkout: Path,
    source_relative: str,
    output_base: str,
    filename: str,
    payload: dict[str, bytes],
    source_files: dict[str, tuple[int, str]],
) -> tuple[dict[str, Any], int]:
    source_path = _source_file(checkout, source_relative, context=source_relative)
    data = source_path.read_bytes()
    metadata, _colors, canonical, converted = _parse_jasc_palette(data, context=source_relative)
    mirror_relative = f"{output_base}/{filename}"
    converted_relative = f"{output_base}/{Path(filename).stem}.gbapal"
    _add_payload(payload, mirror_relative, canonical)
    _add_payload(payload, converted_relative, converted)
    source_hash = _sha256_bytes(data)
    source_files[source_relative] = (len(data), source_hash)
    return {
        "role": Path(filename).stem.upper() + "_PALETTE",
        "source": _source_descriptor(source_relative, data, metadata),
        "normalized": _output_descriptor(
            mirror_relative,
            canonical,
            format_name="JASC_PAL",
            normalization="LF_LINE_ENDINGS_PRESERVE_DECLARED_COLORS",
        ),
        "gba_conversion": _output_descriptor(
            converted_relative,
            converted,
            format_name="GBA_BGR555_LITTLE_ENDIAN",
            normalization="RGB8_FLOOR_DIVIDE_BY_8_PRESERVE_DECLARED_COLORS",
        ) | {"status": "CONVERTED"},
    }, metadata["declared_colors"]


def _selected_source(asset_contract: dict[str, Any]) -> dict[str, Any]:
    selected_key = asset_contract.get("selected_source_key")
    matches = [item for item in asset_contract.get("sources", []) if item.get("source_key") == selected_key]
    _require(len(matches) == 1, "selected asset sourceを一意に解決できません")
    return matches[0]


def _record_key(value: Any, *, context: str) -> str:
    _require(isinstance(value, str) and KEY_RE.fullmatch(value) is not None, f"{context}: key不正: {value!r}")
    return value


def build_p04_asset_import(root: Path, *, source_root: Path | None = None) -> P04AssetBuild:
    """sourceと契約を監査し、書込みなしで全出力とmanifestを確定する。"""
    root = root.resolve()
    candidate_path = root / "content/modernization/p04_candidate_manifest.json"
    source_contract_path = root / "content/modernization/p04_asset_sources.json"
    candidate_contract = _load_json_object(candidate_path)
    asset_contract = _load_json_object(source_contract_path)
    selected = _selected_source(asset_contract)
    expected_commit = selected.get("commit")
    _require(expected_commit == EXPECTED_SOURCE_COMMIT, f"許可されていないsource commitです: {expected_commit}")
    if source_root is None:
        local_checkout = _validate_relative_path(selected.get("local_checkout", ""), context="local_checkout")
        source_root = root.joinpath(*local_checkout.parts)
    checkout = source_root.resolve()

    try:
        source_audit = audit_p04_sources(root, source_root=checkout, require_checkout=True)
    except P04SourceError as exc:
        raise P04AssetImportError(str(exc)) from exc
    _assert_checkout_state(checkout, expected_commit)
    source_checkout_audit = source_audit.get("source_checkout") or {}
    _require(source_checkout_audit.get("asset_set_sha256") is not None, "上流素材集合hashを取得できません")

    root_license_files = sorted(
        item.name for item in checkout.iterdir() if item.is_file() and ROOT_LICENSE_RE.fullmatch(item.name)
    )
    _require(selected.get("license_file") is None, "選定source契約がroot LICENSE不在を示していません")
    _require(not root_license_files, f"source契約と異なるroot license fileを検出しました: {root_license_files}")
    _require(selected.get("redistribution_allowed") is False, "権利確認前の再配布許可は禁止です")

    layout = selected.get("asset_layout")
    _require(isinstance(layout, dict), "選定sourceのasset_layoutがありません")
    species_root = str(_validate_relative_path(layout.get("species_root", ""), context="species_root"))
    item_icon_root = str(_validate_relative_path(layout.get("item_icon_root", ""), context="item_icon_root"))
    item_palette_root = str(_validate_relative_path(layout.get("item_palette_root", ""), context="item_palette_root"))
    palette_overrides = layout.get("palette_overrides", {})
    _require(isinstance(palette_overrides, dict), "palette_overridesがobjectではありません")
    for key, value in palette_overrides.items():
        _validate_relative_path(key, context="palette override key")
        _validate_relative_path(value, context="palette override value")

    records = candidate_contract.get("records")
    _require(isinstance(records, list), "候補recordsが配列ではありません")
    mega_records = sorted(
        (
            record for record in records
            if record.get("classification") == "BATTLE_ONLY_MEGA"
            and record.get("implementation_scope") == "ADOPT_CANDIDATE"
        ),
        key=lambda record: record.get("record_key", ""),
    )
    new_species_records = sorted(
        (
            record for record in records
            if record.get("classification") == "NEW_SPECIES"
            and record.get("implementation_scope") == "ADOPT_CANDIDATE"
        ),
        key=lambda record: record.get("record_key", ""),
    )
    non_adopted_records = sorted(
        (
            record for record in records
            if record.get("classification") == "NEW_SPECIES"
            and record.get("implementation_scope") == "NON_ADOPTED_USER_SCOPE"
        ),
        key=lambda record: record.get("record_key", ""),
    )
    hold_records = sorted(
        (record for record in records if record.get("classification") == "APPEARANCE_CLASSIFICATION_PENDING"),
        key=lambda record: record.get("record_key", ""),
    )
    _require(len(mega_records) == 49, f"Mega candidate件数不一致: {len(mega_records)}")
    _require(len(new_species_records) == 0, f"現行採用Winds/Waves新種件数不一致: {len(new_species_records)}")
    _require(len(non_adopted_records) == 3, f"現行非採用Winds/Waves新種件数不一致: {len(non_adopted_records)}")
    _require(len(hold_records) == 2, f"分類保留件数不一致: {len(hold_records)}")

    payload: dict[str, bytes] = {}
    source_files: dict[str, tuple[int, str]] = {}
    species_assets: list[dict[str, Any]] = []
    palette_coverage_issues: list[dict[str, Any]] = []
    for record in mega_records:
        record_key = _record_key(record.get("record_key"), context="Mega record_key")
        species_key = _record_key(record.get("proposed_species_key"), context=record_key)
        identity_species_key = _record_key(record.get("identity_species_key"), context=record_key)
        identity_form_key = _record_key(record.get("identity_form_key"), context=record_key)
        asset_dir = record.get("asset_dir")
        _validate_relative_path(asset_dir, context=f"{record_key}.asset_dir")
        output_base = f"species/{record_key}"
        source_base = f"{species_root}/{asset_dir}"
        png_assets: list[dict[str, Any]] = []
        maximum_indices: dict[str, int] = {}
        for filename, dimensions in (
            ("front.png", (64, 64)),
            ("back.png", (64, 64)),
            ("icon.png", (32, 64)),
        ):
            entry, maximum = _make_png_asset(
                checkout,
                f"{source_base}/{filename}",
                output_base,
                filename,
                dimensions,
                payload,
                source_files,
            )
            png_assets.append(entry)
            maximum_indices[entry["role"]] = maximum

        palette_base = palette_overrides.get(asset_dir, source_base)
        _validate_relative_path(palette_base, context=f"{record_key}.palette_base")
        palette_assets: list[dict[str, Any]] = []
        declared_palette_colors: dict[str, int] = {}
        for filename in ("normal.pal", "shiny.pal"):
            entry, declared = _make_palette_asset(
                checkout,
                f"{palette_base}/{filename}",
                output_base,
                filename,
                payload,
                source_files,
            )
            palette_assets.append(entry)
            declared_palette_colors[entry["role"]] = declared

        front_back_required = max(maximum_indices["FRONT"], maximum_indices["BACK"]) + 1
        record_issues: list[dict[str, Any]] = []
        for palette_role in ("NORMAL_PALETTE", "SHINY_PALETTE"):
            available = declared_palette_colors[palette_role]
            if available < front_back_required:
                issue = {
                    "record_key": record_key,
                    "issue": "CONTRACT_PALETTE_INDEX_GAP",
                    "palette_role": palette_role,
                    "required_entries_from_front_back_indices": front_back_required,
                    "contract_palette_entries": available,
                    "fake_or_inferred_colors_added": False,
                }
                record_issues.append(issue)
                palette_coverage_issues.append(issue)
        consumer_status = "READY_FOR_GBA_TILE_AND_PALETTE_STAGING" if not record_issues else "BLOCKED_CONTRACT_PALETTE_INDEX_GAP"
        species_assets.append(
            {
                "record_key": record_key,
                "candidate_keys": {
                    "proposed_species_key": species_key,
                    "identity_species_key": identity_species_key,
                    "identity_form_key": identity_form_key,
                    "mega_stone_key": _record_key(record.get("mega_stone_key"), context=record_key),
                },
                "source_asset_directory": source_base,
                "source_palette_directory": palette_base,
                "output_directory": output_base,
                "png_assets": png_assets,
                "palette_assets": palette_assets,
                "gba_consumer_measurement": {
                    "consumer_ready": not record_issues,
                    "status": consumer_status,
                    "front_back_required_palette_entries": front_back_required,
                    "icon_tile_conversion": "CONVERTED_ICON_PALETTE_ASSIGNMENT_DEFERRED_TO_CONSUMER",
                    "issues": record_issues,
                },
            }
        )

    stone_groups: dict[str, dict[str, Any]] = {}
    for record in mega_records:
        record_key = _record_key(record.get("record_key"), context="stone record")
        stone_key = _record_key(record.get("mega_stone_key"), context=record_key)
        stem = record.get("stone_asset_stem")
        _require(isinstance(stem, str) and STONE_STEM_RE.fullmatch(stem) is not None, f"{record_key}: stone asset stem不正")
        group = stone_groups.setdefault(stone_key, {"stem": stem, "record_keys": []})
        _require(group["stem"] == stem, f"{stone_key}: candidate間でstone stem不一致")
        group["record_keys"].append(record_key)
    _require(len(stone_groups) == 45, f"Mega Stone件数不一致: {len(stone_groups)}")

    stone_assets: list[dict[str, Any]] = []
    for stone_key in sorted(stone_groups):
        group = stone_groups[stone_key]
        stem = group["stem"]
        output_base = f"stones/{stone_key}"
        png_entry, maximum_index = _make_png_asset(
            checkout,
            f"{item_icon_root}/{stem}.png",
            output_base,
            "icon.png",
            (24, 24),
            payload,
            source_files,
        )
        palette_entry, declared = _make_palette_asset(
            checkout,
            f"{item_palette_root}/{stem}.pal",
            output_base,
            "palette.pal",
            payload,
            source_files,
        )
        required_entries = maximum_index + 1
        _require(declared >= required_entries, f"{stone_key}: icon indexをstone paletteが覆っていません")
        stone_assets.append(
            {
                "mega_stone_key": stone_key,
                "candidate_record_keys": sorted(group["record_keys"]),
                "stone_asset_stem": stem,
                "output_directory": output_base,
                "png_asset": png_entry,
                "palette_asset": palette_entry,
                "gba_consumer_measurement": {
                    "consumer_ready": True,
                    "status": "READY_FOR_GBA_TILE_AND_PALETTE_STAGING",
                    "required_palette_entries": required_entries,
                    "contract_palette_entries": declared,
                },
            }
        )

    missing_assets: list[dict[str, Any]] = []
    for record in new_species_records:
        record_key = _record_key(record.get("record_key"), context="Winds/Waves record_key")
        missing_assets.append(
            {
                "record_key": record_key,
                "proposed_species_key": _record_key(record.get("proposed_species_key"), context=record_key),
                "identity_species_key": _record_key(record.get("identity_species_key"), context=record_key),
                "identity_form_key": _record_key(record.get("identity_form_key"), context=record_key),
                "name_en": record.get("name_en"),
                "status": "MISSING_FROM_PINNED_SOURCE",
                "required_roles": ["FRONT", "BACK", "ICON", "NORMAL_PALETTE", "SHINY_PALETTE"],
                "fake_or_placeholder_generated": False,
            }
        )

    output_entries = [(relative, _sha256_bytes(data)) for relative, data in payload.items()]
    output_set_hash = _aggregate_hash(output_entries)
    source_entries = [(relative, file_hash) for relative, (_size, file_hash) in source_files.items()]
    source_set_hash = _aggregate_hash(source_entries)
    _require(
        source_set_hash == source_checkout_audit["asset_set_sha256"],
        f"既存P04 source auditと素材集合hashが一致しません: {source_set_hash}",
    )
    # Tatsugiriの3種のMegaフォームは上流でも共通normal/shiny paletteを参照する。
    # front/back/iconはフォーム別だが、2 palette x 残り2フォームの重複を除くため
    # source上の固有file数は330ではなく326になる。
    _require(len(source_files) == 326, f"source固有file件数不一致: {len(source_files)}")
    _require(len(payload) == 670, f"出力file件数不一致: {len(payload)}")
    _require(not palette_coverage_issues, f"palette coverage issueが残っています: {len(palette_coverage_issues)}")
    ready_species = sum(
        item["gba_consumer_measurement"]["status"] == "READY_FOR_GBA_TILE_AND_PALETTE_STAGING"
        for item in species_assets
    )
    _require(ready_species == 49, f"GBA consumer-ready Mega件数不一致: {ready_species}")

    _assert_checkout_state(checkout, expected_commit)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task": "USER-MODERNIZATION-P04-ASSET-IMPORT",
        "status": "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS",
        "research_cutoff_date": "2026-09-08",
        "inputs": {
            "candidate_manifest": {
                "relative_path": "content/modernization/p04_candidate_manifest.json",
                "sha256": _sha256_file(candidate_path),
            },
            "asset_source_contract": {
                "relative_path": "content/modernization/p04_asset_sources.json",
                "sha256": _sha256_file(source_contract_path),
            },
        },
        "source": {
            "source_key": asset_contract["selected_source_key"],
            "repository_url": selected["repository_url"],
            "commit": expected_commit,
            "local_checkout": selected["local_checkout"],
            "checkout_clean_required": True,
            "checkout_clean_observed": True,
            "source_unique_file_count": len(source_files),
            "source_reference_count": len(mega_records) * 5 + len(stone_groups) * 2,
            "source_asset_set_sha256": source_set_hash,
            "source_asset_set_hash_algorithm": "SHA256_EACH_FILE_THEN_SHA256_SORTED_RELATIVE_PATH_NUL_FILE_SHA256_LF",
        },
        "rights": {
            "root_license_file": None,
            "detected_root_license_files": root_license_files,
            "source_contract_license_status": selected["license_status"],
            "redistribution_allowed": False,
            "staging_scope": "PERSONAL_PRIVATE_USE_ONLY",
            "tracked_binary_assets": False,
            "release_gate": "MANUAL_RIGHTS_AND_CREDITS_REVIEW_REQUIRED",
        },
        "output": {
            "logical_root": DEFAULT_OUTPUT_RELATIVE,
            "git_tracking": "IGNORED",
            "write_policy": "CREATE_IF_ABSENT_OR_REUSE_ONLY_IF_EXACT;FAIL_ON_ANY_CONTAMINATION",
            "payload_file_count": len(payload),
            "payload_total_size": sum(len(data) for data in payload.values()),
            "source_mirror_file_count": 335,
            "gba_binary_file_count": 335,
            "asset_set_sha256": output_set_hash,
            "asset_set_hash_algorithm": "SHA256_EACH_FILE_THEN_SHA256_SORTED_RELATIVE_PATH_NUL_FILE_SHA256_LF",
            "normalization": {
                "png": "BYTE_EXACT_SOURCE_MIRROR_PLUS_GBA_4BPP_TILES",
                "jasc_palette": "LF_CANONICAL_TEXT_PLUS_GBA_BGR555_LITTLE_ENDIAN",
                "palette_padding_or_inferred_colors": "NONE",
            },
        },
        "coverage": {
            "mega_candidate_records": {"covered": len(species_assets), "required": 49},
            "unique_mega_source_directories": {"covered": len({item["source_asset_directory"] for item in species_assets}), "required": 48},
            "mega_stones": {"covered": len(stone_assets), "required": 45},
            "winds_waves_new_species": {"covered": 0, "required": 0},
            "gba_tile_conversion_records": {"converted": 49, "required": 49},
            "gba_full_species_palette_compatibility": {"ready": ready_species, "required": 49},
            "gba_stone_compatibility": {"ready": 45, "required": 45},
        },
        "consumer_scope": {
            "rom_modified": False,
            "id_assignments_created": False,
            "compression_applied": False,
            "tile_format": "UNCOMPRESSED_GBA_4BPP_8X8_ROW_MAJOR",
            "palette_format": "UNCOMPRESSED_GBA_BGR555_LITTLE_ENDIAN",
            "integration_status": "STAGING_ONLY_NOT_ROM_READY",
        },
        "species_assets": species_assets,
        "stone_assets": stone_assets,
        "missing_assets": missing_assets,
        "palette_coverage_issues": palette_coverage_issues,
        "excluded_non_adopted_records": [
            {
                "record_key": _record_key(record.get("record_key"), context="non-adopted record"),
                "proposed_species_key": _record_key(record.get("proposed_species_key"), context="non-adopted record"),
                "identity_species_key": _record_key(record.get("identity_species_key"), context="non-adopted record"),
                "identity_form_key": _record_key(record.get("identity_form_key"), context="non-adopted record"),
                "name_en": record.get("name_en"),
                "status": "NON_ADOPTED_USER_SCOPE",
                "id_assignment": "NOT_APPLICABLE_NON_ADOPTED",
                "asset_requirement": "NOT_REQUIRED",
                "future_readoption": "EXPLICIT_USER_DECISION_AND_FULL_CAPACITY_ASSET_REVALIDATION_REQUIRED",
            }
            for record in non_adopted_records
        ],
        "excluded_classification_hold_records": [
            {
                "record_key": _record_key(record.get("record_key"), context="hold record"),
                "identity_species_key": _record_key(record.get("identity_species_key"), context="hold record"),
                "identity_form_key": _record_key(record.get("identity_form_key"), context="hold record"),
                "status": "EXCLUDED_CLASSIFICATION_HOLD",
            }
            for record in hold_records
        ],
    }
    return P04AssetBuild(manifest=manifest, payload=payload)


def _expected_directories(payload: dict[str, bytes]) -> set[str]:
    directories: set[str] = set()
    for relative in payload:
        parent = PurePosixPath(relative).parent
        while str(parent) != ".":
            directories.add(str(parent))
            parent = parent.parent
    return directories


def verify_output_directory(output_root: Path, payload: dict[str, bytes]) -> None:
    """既存出力が期待集合・byteと完全一致することだけを許可する。"""
    _require(output_root.exists(), f"素材出力directoryがありません: {output_root}")
    _require(output_root.is_dir() and not output_root.is_symlink(), f"素材出力rootは通常directory必須です: {output_root}")
    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for item in output_root.rglob("*"):
        relative = item.relative_to(output_root).as_posix()
        _validate_relative_path(relative, context="existing output")
        _require(not item.is_symlink(), f"既存出力にsymlinkがあります: {relative}")
        if item.is_file():
            actual_files.add(relative)
        elif item.is_dir():
            actual_directories.add(relative)
        else:
            raise P04AssetImportError(f"既存出力に通常file/directory以外があります: {relative}")
    expected_files = set(payload)
    expected_directories = _expected_directories(payload)
    extra_files = sorted(actual_files - expected_files)
    missing_files = sorted(expected_files - actual_files)
    extra_directories = sorted(actual_directories - expected_directories)
    missing_directories = sorted(expected_directories - actual_directories)
    _require(
        not (extra_files or missing_files or extra_directories or missing_directories),
        "既存出力混入または欠落を検出しました: "
        f"extra_files={extra_files[:5]}, missing_files={missing_files[:5]}, "
        f"extra_dirs={extra_directories[:5]}, missing_dirs={missing_directories[:5]}",
    )
    for relative in sorted(expected_files):
        actual = (output_root / relative).read_bytes()
        _require(actual == payload[relative], f"既存出力byte不一致: {relative}")


def install_asset_payload(output_root: Path, payload: dict[str, bytes]) -> str:
    """出力なしなら原子的に作成し、既存なら完全一致時だけ再利用する。"""
    _require(bool(payload), "空payloadはinstallできません")
    if output_root.exists() or output_root.is_symlink():
        verify_output_directory(output_root, payload)
        return "REUSED_EXACT"
    parent = output_root.parent
    parent.mkdir(parents=True, exist_ok=True)
    _require(parent.is_dir() and not output_root.exists(), f"素材出力親directoryを準備できません: {parent}")
    staging = Path(tempfile.mkdtemp(prefix=".p04-assets-", dir=parent))
    try:
        for relative, data in sorted(payload.items()):
            target = staging.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(data)
        verify_output_directory(staging, payload)
        try:
            os.rename(staging, output_root)
        except OSError as exc:
            raise P04AssetImportError(f"素材出力の原子的確定に失敗しました: {exc}") from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    verify_output_directory(output_root, payload)
    return "CREATED"


def write_manifest(path: Path, manifest: dict[str, Any]) -> str:
    """明示的な生成操作でmanifestを原子的に作成・更新する。"""
    data = _canonical_json_bytes(manifest)
    if path.is_file() and path.read_bytes() == data:
        return "REUSED_EXACT"
    _require(not path.exists() or path.is_file(), f"manifest pathが通常fileではありません: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    _require(not temporary.exists(), f"manifest一時fileが既にあります: {temporary}")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return "WRITTEN"


def _report(build: P04AssetBuild, *, mode: str, output_state: str, manifest_state: str) -> dict[str, Any]:
    manifest_bytes = _canonical_json_bytes(build.manifest)
    return {
        "schema_version": SCHEMA_VERSION,
        "task": "USER-MODERNIZATION-P04-ASSET-IMPORT",
        "status": "PASS",
        "mode": mode,
        "source_commit": build.manifest["source"]["commit"],
        "source_unique_file_count": build.manifest["source"]["source_unique_file_count"],
        "source_asset_set_sha256": build.manifest["source"]["source_asset_set_sha256"],
        "mega_candidate_assets": build.manifest["coverage"]["mega_candidate_records"],
        "mega_stone_assets": build.manifest["coverage"]["mega_stones"],
        "winds_waves_assets": build.manifest["coverage"]["winds_waves_new_species"],
        "gba_full_species_palette_compatibility": build.manifest["coverage"]["gba_full_species_palette_compatibility"],
        "palette_coverage_issue_count": len(build.manifest["palette_coverage_issues"]),
        "payload_file_count": build.manifest["output"]["payload_file_count"],
        "payload_total_size": build.manifest["output"]["payload_total_size"],
        "asset_set_sha256": build.manifest["output"]["asset_set_sha256"],
        "manifest_sha256": _sha256_bytes(manifest_bytes),
        "license_status": build.manifest["rights"]["source_contract_license_status"],
        "staging_scope": build.manifest["rights"]["staging_scope"],
        "output_logical_root": build.manifest["output"]["logical_root"],
        "output_git_ignore_verified": True,
        "output_state": output_state,
        "manifest_state": manifest_state,
        "rom_modified": False,
        "id_assignments_created": False,
    }


def _resolve_fixed_workspace_path(
    root: Path,
    requested: Path | None,
    relative: str,
    *,
    label: str,
) -> Path:
    """固定workspace pathだけを許可し、途中のsymlinkによるroot外逸脱を拒否する。"""

    root = root.resolve()
    expected = root.joinpath(*PurePosixPath(relative).parts)
    candidate = requested if requested is not None else expected
    if not candidate.is_absolute():
        candidate = root / candidate
    actual = Path(os.path.abspath(candidate))
    _require(
        actual == expected,
        f"{label}は固定pathのみ許可します: "
        f"expected={expected} actual={actual}",
    )
    current = root
    for component in PurePosixPath(relative).parts:
        current = current / component
        _require(not current.is_symlink(), f"{label}のpathにsymlinkがあります: {current}")
    return expected


def _resolve_private_output_root(root: Path, requested: Path | None) -> Path:
    """manifestが宣言するGit外private root以外への書込・監査を拒否する。"""

    root = root.resolve()
    actual = _resolve_fixed_workspace_path(
        root,
        requested,
        DEFAULT_OUTPUT_RELATIVE,
        label="素材出力root",
    )
    try:
        ignored = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", DEFAULT_OUTPUT_RELATIVE],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        raise P04AssetImportError(f"Git ignore状態を確認できません: {exc}") from exc
    _require(
        ignored.returncode == 0,
        f"素材出力rootがGit ignore対象ではありません: {DEFAULT_OUTPUT_RELATIVE}",
    )
    return actual


def _resolve_manifest_path(root: Path, requested: Path | None) -> Path:
    """tracked manifestを固定path以外へ書き出さない。"""

    return _resolve_fixed_workspace_path(
        root,
        requested,
        DEFAULT_MANIFEST_RELATIVE,
        label="asset import manifest",
    )


def generate_p04_asset_import(
    root: Path,
    *,
    source_root: Path | None = None,
    output_root: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """私用出力とtracked manifestを明示的に生成する。"""
    root = root.resolve()
    output_root = _resolve_private_output_root(root, output_root)
    manifest_path = _resolve_manifest_path(root, manifest_path)
    build = build_p04_asset_import(root, source_root=source_root)
    output_state = install_asset_payload(output_root, build.payload)
    manifest_state = write_manifest(manifest_path, build.manifest)
    return _report(build, mode="WRITE", output_state=output_state, manifest_state=manifest_state)


def audit_p04_asset_import(
    root: Path,
    *,
    source_root: Path | None = None,
    output_root: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """source・manifest・私用出力を一切更新せず再計算して照合する。"""
    root = root.resolve()
    output_root = _resolve_private_output_root(root, output_root)
    manifest_path = _resolve_manifest_path(root, manifest_path)
    build = build_p04_asset_import(root, source_root=source_root)
    actual_manifest = _load_json_object(manifest_path)
    _require(actual_manifest == build.manifest, f"asset import manifestが再計算結果と一致しません: {manifest_path}")
    verify_output_directory(output_root, build.payload)
    return _report(build, mode="CHECK", output_state="VERIFIED_EXACT", manifest_state="VERIFIED_EXACT")


__all__ = [
    "DEFAULT_MANIFEST_RELATIVE",
    "DEFAULT_OUTPUT_RELATIVE",
    "EXPECTED_SOURCE_COMMIT",
    "P04AssetBuild",
    "P04AssetImportError",
    "_assert_checkout_state",
    "_canonical_json_bytes",
    "_encode_gba_4bpp",
    "_parse_indexed_png",
    "_validate_relative_path",
    "audit_p04_asset_import",
    "build_p04_asset_import",
    "generate_p04_asset_import",
    "install_asset_payload",
    "verify_output_directory",
    "write_manifest",
]
