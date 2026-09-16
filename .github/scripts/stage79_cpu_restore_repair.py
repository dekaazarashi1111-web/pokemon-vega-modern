#!/usr/bin/env python3
"""Repair host CPU restoration, with exact source identities and no ROM edits."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/modernization_stage79_cumulative_mgba.json"
OUT = ROOT / ".local/stage79-cpu-repair"
REPAIRS = {
    "tools/mgba_battle_core_smoke.c": (
        "6a4c72232388e4fdf5f4c48a0f5f825193b6977ad8a117d70477b7d595982e23",
        '    write_register(core, "pc", (uint32_t)state->registers[15]);',
        '    /* writeRegister(pc) refills the pipeline and adds one instruction. */\n'
        '    uint32_t width = ((uint32_t)state->registers[16] & 0x20U) ? 2U : 4U;\n'
        '    write_register(core, "pc", (uint32_t)state->registers[15] - width);',
    ),
    "tools/mgba_regression_smoke.c": (
        "f2e63f6bbf3c2c860664fa6bb178304b834352917b75d3605fb0aa20dd11c5b0",
        '    write_register(core, "pc", context->registers[15]);',
        '    /* writeRegister(pc) refills the pipeline and adds one instruction. */\n'
        '    uint32_t width = ((uint32_t)context->registers[16] & 0x20U) ? 2U : 4U;\n'
        '    write_register(core, "pc", (int32_t)((uint32_t)context->registers[15] - width));',
    ),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def snapshot(document) -> None:
    paths = set(REPAIRS) | {
        "config/modernization_stage79_cumulative_mgba.json",
        "scripts/run_modernization_stage79_cumulative_mgba.py",
        "scripts/run_modernization_stage79_github_domain.py",
        "tests/test_modernization_stage79_cumulative_mgba.py",
        "tests/mgba_cpu_restore_regression.c",
    }
    for node in walk(document):
        path = node.get("path")
        if isinstance(path, str) and Path(path).suffix in {".c", ".h", ".py", ".json", ".s", ".ld"}:
            paths.add(path)
    with tarfile.open(OUT / "source-before.tar.gz", "w:gz") as archive:
        for path in sorted(paths):
            source = ROOT / path
            source.resolve(strict=True).relative_to(ROOT)
            if source.is_symlink():
                raise RuntimeError(f"symlink source: {path}")
            archive.add(source, arcname=path, recursive=False)
    identity = document["input_identity"]["rom"]
    rom = (ROOT / identity["path"]).read_bytes()
    assert sha(rom) == identity["sha256"]
    def u32(address):
        return struct.unpack_from("<I", rom, address - 0x08000000)[0]
    map_root = u32(0x08054B0C)
    group = u32(map_root + 96 * 4)
    header = u32(group + 5 * 4)
    events = u32(header + 4)
    objects = u32(events + 4)
    count = rom[events - 0x08000000]
    graph = {
        "rom_sha256": sha(rom), "map_root": hex(map_root),
        "group96": hex(group), "header96_5": hex(header),
        "events": hex(events), "scripts": hex(u32(header + 8)),
        "event_counts": list(rom[events - 0x08000000:events - 0x08000000 + 4]),
        "objects": [
            {"local_id": rom[objects - 0x08000000 + i * 24],
             "script": hex(u32(objects + i * 24 + 16))}
            for i in range(count)
        ],
    }
    (OUT / "factory-graph.json").write_text(json.dumps(graph, indent=2) + "\n")
    snippet = ROOT / ".local/stage79-cpu-disassembly.bin"
    snippet.write_bytes(rom[0x012D1B80:0x012D1D80])
    with (OUT / "acquisition-disassembly.txt").open("w") as stream:
        subprocess.run([
            "arm-none-eabi-objdump", "-D", "-b", "binary", "-marm",
            "-Mforce-thumb", "--adjust-vma=0x092D1B80", str(snippet),
        ], stdout=stream, check=True)
    snippet.unlink()


def apply(document) -> None:
    changed = {}
    for path, (expected, before, after) in REPAIRS.items():
        source = ROOT / path
        raw = source.read_bytes()
        if sha(raw) != expected:
            raise RuntimeError(f"unexpected source identity: {path}")
        text = raw.decode("utf-8")
        if text.count(before) != 1:
            raise RuntimeError(f"repair anchor is not unique: {path}")
        source.write_text(text.replace(before, after), encoding="utf-8")
        updated = source.read_bytes()
        changed[path] = {"size": len(updated), "sha256": sha(updated)}
    refreshed = 0
    for node in walk(document):
        path = node.get("path")
        if isinstance(path, str) and path in changed and "sha256" in node:
            if node["sha256"] != REPAIRS[path][0]:
                raise RuntimeError(f"unexpected pinned source identity: {path}")
            node.update(changed[path])
            refreshed += 1
    if refreshed != 7:
        raise RuntimeError(f"expected seven dependency pins, found {refreshed}")
    CONFIG.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "repair.json").write_text(json.dumps({
        "changed_sources": changed, "refreshed_dependency_pins": refreshed,
        "rom_sha256": document["input_identity"]["rom"]["sha256"],
        "acceptance_predicates_changed": False,
    }, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    if sys.argv[1:] == ["snapshot"]:
        snapshot(document)
    elif sys.argv[1:] == ["apply"]:
        apply(document)
    else:
        raise SystemExit("usage: stage79_cpu_restore_repair.py snapshot|apply")


if __name__ == "__main__":
    main()
