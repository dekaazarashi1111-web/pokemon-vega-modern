#!/usr/bin/env python3
"""ChangeKit会話の原文から、現行1-byte font向けかな正本を作成・検証する。

``author`` は採用時だけ使うauthoring helperで、pykakasiを明示的に要求する。
ROM再構築では追跡済みの対応表を ``check`` し、外部packageへ依存しない。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "content/trainer_changekit_final/trainer_dialogue.csv"
OUTPUT = ROOT / "content/trainer_changekit_dialogue_readings.csv"
MAX_LINE_GLYPHS = 18
MAX_LINES_PER_PAGE = 2


class DialogueError(RuntimeError):
    """会話正本または現行charmap契約の違反。"""


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _charmap() -> tuple[dict[str, int], list[str]]:
    from tools.regression.rom_runtime import _charmap as load_charmap

    return load_charmap(ROOT)


def _encode(text: str) -> bytes:
    from tools.regression.rom_runtime import _encode_text

    mapping, tokens = _charmap()
    return _encode_text(text, mapping, tokens)


def _visible_lines(text: str) -> list[list[str]]:
    pages = text.split("\\p")
    return [page.split("\\n") for page in pages]


def _wrap(reading: str) -> str:
    """既存改行を尊重し、18 glyph x 2行ごとにpageを送る。"""

    logical_lines: list[str] = []
    for paragraph in reading.replace("\r", "").split("\\n"):
        value = paragraph.strip()
        if not value:
            logical_lines.append("")
            continue
        while len(value) > MAX_LINE_GLYPHS:
            split = value.rfind(" ", 0, MAX_LINE_GLYPHS + 1)
            if split < MAX_LINE_GLYPHS // 2:
                split = MAX_LINE_GLYPHS
            logical_lines.append(value[:split].rstrip())
            value = value[split:].lstrip()
        logical_lines.append(value)

    pages: list[str] = []
    for start in range(0, len(logical_lines), MAX_LINES_PER_PAGE):
        pages.append("\\n".join(logical_lines[start:start + MAX_LINES_PER_PAGE]))
    return "\\p".join(pages)


def _normalize_with_pykakasi(text: str) -> str:
    try:
        from pykakasi import kakasi
    except ImportError as error:
        raise DialogueError(
            "author modeにはpykakasi 2.3.0が必要です。通常のROM build/checkには不要です"
        ) from error

    marker = "XVEGALINEBREAKX"
    prepared = text.replace("\\n", marker).replace("\n", marker)
    reading = "".join(part["hira"] for part in kakasi().convert(prepared))
    reading = reading.replace(marker.lower(), "\\n").replace(marker, "\\n")
    for source, replacement in (
        ("ゔぁ", "ば"), ("ゔぃ", "び"), ("ゔぇ", "べ"),
        ("ゔぉ", "ぼ"), ("ゔゅ", "びゅ"), ("ゔ", "ぶ"),
    ):
        reading = reading.replace(source, replacement)
    translations = str.maketrans({
        "、": " ",
        "，": " ",
        "「": "『",
        "」": "』",
        "（": "(",
        "）": ")",
        "：": ":",
        "！": "！",
        "？": "？",
    })
    reading = reading.translate(translations)
    while "  " in reading:
        reading = reading.replace("  ", " ")
    return _wrap(reading)


def _source_unique() -> list[str]:
    if not SOURCE.is_file():
        raise DialogueError(f"正規化ChangeKit会話がありません: {SOURCE}")
    rows = _rows(SOURCE)
    if len(rows) != 4662:
        raise DialogueError(f"会話行数が4662ではありません: {len(rows)}")
    values = sorted({row["text"] for row in rows})
    if len(values) != 104:
        raise DialogueError(f"会話原文のunique数が104ではありません: {len(values)}")
    return values


def _audit_row(index: int, original: str, normalized: str) -> dict[str, object]:
    raw = _encode(normalized)
    pages = _visible_lines(normalized)
    widths = [len(line) for page in pages for line in page]
    if any(width > MAX_LINE_GLYPHS for width in widths):
        raise DialogueError(f"line width超過: {original!r} -> {normalized!r}")
    if any(len(page) > MAX_LINES_PER_PAGE for page in pages):
        raise DialogueError(f"page line数超過: {original!r} -> {normalized!r}")
    return {
        "reading_id": f"READING_{index:04d}",
        "original_sha256": _sha_text(original),
        "original_text": original,
        "normalized_text": normalized,
        "encoded_hex": raw.hex(),
        "encoded_size": len(raw),
        "page_count": len(pages),
        "max_line_glyphs": max(widths, default=0),
        "status": "ADOPTED_CURRENT_1BYTE_FONT",
    }


def author() -> list[dict[str, object]]:
    rows = [
        _audit_row(index, original, _normalize_with_pykakasi(original))
        for index, original in enumerate(_source_unique(), 1)
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def check() -> list[dict[str, object]]:
    if not OUTPUT.is_file():
        raise DialogueError(f"採用済みかな対応表がありません: {OUTPUT}")
    rows = _rows(OUTPUT)
    originals = _source_unique()
    if len(rows) != len(originals):
        raise DialogueError(f"かな対応表件数が不正です: {len(rows)}")
    by_original = {row["original_text"]: row for row in rows}
    if len(by_original) != len(rows) or set(by_original) != set(originals):
        raise DialogueError("かな対応表とChangeKit原文集合が一致しません")
    checked: list[dict[str, object]] = []
    for index, original in enumerate(originals, 1):
        row = by_original[original]
        expected = _audit_row(index, original, row["normalized_text"])
        actual = {key: row[key] for key in expected}
        comparable = {key: str(value) for key, value in expected.items()}
        if actual != comparable:
            raise DialogueError(f"かな対応表の派生値が不一致です: {row['reading_id']}")
        checked.append(expected)
    return checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("author", "check"))
    args = parser.parse_args()
    try:
        rows = author() if args.mode == "author" else check()
    except (OSError, KeyError, ValueError, DialogueError) as error:
        print(f"Trainer ChangeKit dialogue {args.mode}: FAIL: {error}", file=sys.stderr)
        return 1
    summary = {
        "status": "PASS",
        "mode": args.mode,
        "source_rows": 4662,
        "unique_readings": len(rows),
        "maximum_encoded_size": max(int(row["encoded_size"]) for row in rows),
        "maximum_line_glyphs": max(int(row["max_line_glyphs"]) for row in rows),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
