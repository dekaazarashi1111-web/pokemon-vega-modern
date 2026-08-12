#!/usr/bin/env python3
"""Audit DPE-JP/CFRU-JP fixed ROM addresses against Vega IPS touched ranges.

Run after cloning the public source repositories locally. The script does not
need or read a ROM. It recognizes the insertion-control files used by these
projects and reports which write/repoint/hook sites Vega already modifies.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

ROM_BASE = 0x08000000
ROM_LIMIT = 0x0A000000
CONTROL_FILES = {
    "bytereplacement",
    "hooks",
    "repoints",
    "repointall",
    "routinepointers",
    "functionrewrites",
    "special_inserts.asm",
}


def load_analyzer():
    path = Path(__file__).resolve().parent / "analyze_patches.py"
    spec = importlib.util.spec_from_file_location("vega_patch_analyzer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


analyzer = load_analyzer()


@dataclass(frozen=True)
class Site:
    project: str
    file: str
    line: int
    kind: str
    symbol: str
    address: int
    write_length: int
    source: str

    @property
    def offset(self) -> int:
        return self.address - ROM_BASE if self.address >= ROM_BASE else self.address


HEX_TOKEN = re.compile(r"^(?:0x)?([0-9A-Fa-f]{6,8})$")
ORG_RE = re.compile(r"^\s*\.org\s+(0x[0-9A-Fa-f]+)")


def normalise_address(token: str) -> int | None:
    match = HEX_TOKEN.match(token.strip().rstrip(","))
    if not match:
        return None
    value = int(match.group(1), 16)
    if 0x800000 <= value < 0x2000000:  # common files omit the leading zero
        value += 0x08000000 if value < ROM_BASE else 0
    if ROM_BASE <= value < ROM_LIMIT:
        return value
    if 0 <= value < 0x02000000:
        return ROM_BASE + value
    return None


def literal_byte_count(tokens: list[str]) -> int:
    count = 0
    for token in tokens:
        token = token.strip()
        if re.fullmatch(r"[0-9A-Fa-f]{2}", token):
            count += 1
        else:
            # A symbolic define still writes at least one byte in these files.
            count += 1
    return max(count, 1)


def iter_control_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.name in CONTROL_FILES:
            yield path


def parse_file(project: str, root: Path, path: Path) -> list[Site]:
    sites: list[Site] = []
    relative = str(path.relative_to(root))
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return sites

    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("@"):
            continue

        if path.name == "special_inserts.asm":
            match = ORG_RE.match(raw)
            if match:
                value = int(match.group(1), 16)
                address = value if value >= ROM_BASE else ROM_BASE + value
                sites.append(
                    Site(project, relative, number, "special_insert", ".org", address, 1, stripped)
                )
            continue

        parts = stripped.split()
        if path.name == "bytereplacement":
            address = normalise_address(parts[0])
            if address is not None and len(parts) >= 2:
                sites.append(
                    Site(
                        project,
                        relative,
                        number,
                        "byte_replacement",
                        "",
                        address,
                        literal_byte_count(parts[1:]),
                        stripped,
                    )
                )
            continue

        if len(parts) < 2:
            continue
        address = normalise_address(parts[1])
        if address is None:
            continue
        symbol = parts[0]
        if path.name == "hooks":
            # CFRU/DPE Hook writes 8 bytes on aligned sites and 10 on halfword-only sites.
            length = 10 if ((address - ROM_BASE) % 4) else 8
            kind = "hook"
        elif path.name in {"repoints", "repointall", "routinepointers"}:
            length = 4
            kind = path.name
        elif path.name == "functionrewrites":
            length = 16
            kind = "function_rewrite"
        else:
            length = 1
            kind = path.name
        sites.append(Site(project, relative, number, kind, symbol, address, length, stripped))
    return sites


def overlap_bytes(start: int, end: int, ranges) -> int:
    total = 0
    for item in ranges:
        if item.end <= start:
            continue
        if item.start >= end:
            break
        total += max(0, min(end, item.end) - max(start, item.start))
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vega_ips", type=Path)
    parser.add_argument("--cfru", type=Path, required=True, help="local CFRU-JP source directory")
    parser.add_argument("--dpe", type=Path, required=True, help="local DPE-JP source directory")
    parser.add_argument("--out-dir", type=Path, default=Path("source_audit"))
    args = parser.parse_args()

    for root in (args.cfru, args.dpe):
        if not root.is_dir():
            raise SystemExit(f"Source directory not found: {root}")

    vega = analyzer.parse_ips(args.vega_ips)
    vega_ranges = vega["ranges"]
    sites: list[Site] = []
    for project, root in (("CFRU-JP", args.cfru), ("DPE-JP", args.dpe)):
        for path in iter_control_files(root):
            sites.extend(parse_file(project, root, path))

    rows = []
    for site in sites:
        start = site.offset
        end = start + site.write_length
        direct = overlap_bytes(start, end, vega_ranges)
        nearby = overlap_bytes(max(0, start - 8), end + 8, vega_ranges)
        status = "DIRECT" if direct else ("NEARBY" if nearby else "CLEAR_BY_IPS_RANGE")
        rows.append(
            {
                "project": site.project,
                "control_file": site.file,
                "line": site.line,
                "kind": site.kind,
                "symbol": site.symbol,
                "gba_address": f"0x{site.address:08X}",
                "estimated_write_length": site.write_length,
                "status": status,
                "direct_overlap_bytes": direct,
                "nearby_overlap_bytes_with_8byte_margin": nearby,
                "source_line": site.source,
            }
        )

    order = {"DIRECT": 0, "NEARBY": 1, "CLEAR_BY_IPS_RANGE": 2}
    rows.sort(key=lambda row: (order[row["status"]], row["project"], row["gba_address"]))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = args.out_dir / "fixed_address_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for status in order:
        counts[status] = sum(1 for row in rows if row["status"] == status)
    summary = {
        "sites_total": len(rows),
        "status_counts": counts,
        "important_note": (
            "CLEAR_BY_IPS_RANGE only means Vega IPS did not directly write the estimated site. "
            "It does not prove semantic compatibility or unchanged target functions."
        ),
    }
    json_path = args.out_dir / "fixed_address_audit_summary.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = args.out_dir / "fixed_address_audit.md"
    direct_rows = [row for row in rows if row["status"] == "DIRECT"]
    lines = [
        "# DPE-JP/CFRU-JP 固定アドレス監査",
        "",
        f"- 抽出site数: {len(rows):,}",
        f"- Vega IPSと直接重複: {counts['DIRECT']:,}",
        f"- 8 bytes以内にVega変更あり: {counts['NEARBY']:,}",
        f"- IPS範囲上は直接重複なし: {counts['CLEAR_BY_IPS_RANGE']:,}",
        "",
        "`CLEAR_BY_IPS_RANGE`は互換性を保証しません。repointall、RAM、save-block、ID体系は別監査が必要です。",
        "",
        "## 直接重複site（先頭100件）",
        "",
        "|project|kind|symbol|address|overlap|source|",
        "|---|---|---|---|---:|---|",
    ]
    for row in direct_rows[:100]:
        source = str(row["source_line"]).replace("|", "\\|")
        lines.append(
            f"|{row['project']}|{row['kind']}|{row['symbol']}|{row['gba_address']}|"
            f"{row['direct_overlap_bytes']}|`{source}`|"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
