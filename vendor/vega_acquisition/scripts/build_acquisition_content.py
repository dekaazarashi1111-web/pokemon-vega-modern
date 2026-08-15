#!/usr/bin/env python3
"""Generate deterministic acquisition C tables, host wrappers, and map patch manifest."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

MODE_ENUM = {
    "CAPTURE": "VEGA_ACQ_MODE_CAPTURE",
    "GIFT": "VEGA_ACQ_MODE_GIFT",
    "EGG": "VEGA_ACQ_MODE_EGG",
    "FOSSIL": "VEGA_ACQ_MODE_FOSSIL",
    "EVOLUTION_SUPPORT": "VEGA_ACQ_MODE_EVOLUTION_SUPPORT",
    "TRADE_EMULATOR": "VEGA_ACQ_MODE_TRADE_EMULATOR",
    "SERVICE": "VEGA_ACQ_MODE_SERVICE",
}
NO_INDEX = 0xFFFF


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value.upper()).strip("_") or "UNNAMED"


def c_string(value: object) -> str:
    text = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{text}"'


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def event_claim_key(event: dict[str, str]) -> str:
    if event["battle_or_gift"] in {"EVOLUTION_SUPPORT", "TRADE_EMULATOR", "SERVICE"}:
        return ""
    return event["shared_capture_key"] or event["flag_key"]


def generate(package: Path, output: Path) -> None:
    registry = rows(package / "content/collectible_species_registry.csv")
    events = rows(package / "content/acquisition_events.csv")
    hosts = rows(package / "content/acquisition_physical_hosts.csv")
    starters = rows(package / "content/starter_lab_catalog_24.csv")
    fossils = rows(package / "content/fossil_restoration_catalog_16.csv")

    species_by_key = {row["species_key"]: row for row in registry}
    source_item_by_event = {f"EVENT_{row['fossil_key']}": row["source_item_key"] for row in fossils}
    backup_starters = {
        row["slot_key"].replace("STARTER_LAB_", "EVENT_STARTER_LAB_")
        for row in starters if row["claim_policy"] == "BACKUP_REGISTERED_ONLY"
    }
    claim_keys = sorted({key for event in events if (key := event_claim_key(event))})
    claim_index = {key: index for index, key in enumerate(claim_keys)}
    collection_rows = [row for row in registry if row["completion_weight"] == "1"]
    collection_rows += [row for row in registry if row["target_status"] == "REQUIRED_ENABLING_FORM"]
    collection_index = {row["species_key"]: index for index, row in enumerate(collection_rows)}
    collection_bytes = (len(collection_index) + 7) // 8
    event_claim_bytes = (len(claim_index) + 7) // 8
    bounded_counter_bytes = 1
    alignment_padding_bytes = (-(12 + collection_bytes + event_claim_bytes + bounded_counter_bytes)) % 4
    evolution_counter_bytes = 32
    pending_bytes = 20
    save_block_bytes = (12 + collection_bytes + event_claim_bytes + bounded_counter_bytes
                        + alignment_padding_bytes + evolution_counter_bytes + pending_bytes)
    if save_block_bytes != 240:
        raise ValueError(f"unexpected save block size: {save_block_bytes}")

    event_records: list[dict[str, object]] = []
    for index, event in enumerate(events):
        targets = [value for value in event["target_species_keys"].split("|") if value]
        species_key = targets[0] if targets else ""
        species_id = int(species_by_key[species_key]["canonical_id"]) if species_key else 0
        levels = [int(value) for value in re.findall(r"\d+", event["capture_level"])]
        key = event_claim_key(event)
        event_key = event["event_key"]
        max_claims = 0 if not key else (2 if event_key == "EVENT_SPECIAL_NATIONAL_0789" else 1)
        flags = 0
        if event_key in backup_starters:
            flags |= 0x01
        elif species_id and max_claims == 1:
            flags |= 0x02
        if event["battle_or_gift"] == "EGG":
            flags |= 0x04
        if event_key == "EVENT_SPECIAL_NATIONAL_0789":
            flags |= 0x08
        if event["battle_or_gift"] in {"EVOLUTION_SUPPORT", "TRADE_EMULATOR", "SERVICE"}:
            flags |= 0x10
        event_records.append({
            "event_key": event_key,
            "species_key": species_key,
            "unlock_key": event["unlock_key"],
            "claim_key": key,
            "source_item_key": source_item_by_event.get(event_key, ""),
            "species_id": species_id,
            "claim_bit_index": claim_index.get(key, NO_INDEX),
            "bounded_counter_index": 0 if event_key == "EVENT_SPECIAL_NATIONAL_0789" else NO_INDEX,
            "mode": event["battle_or_gift"],
            "level": levels[0] if levels else 0,
            "max_claims": max_claims,
            "policy_flags": flags,
        })

    event_h = f"""#ifndef VEGA_ACQUISITION_EVENT_DEFS_H
#define VEGA_ACQUISITION_EVENT_DEFS_H
#include <stdint.h>
#define VEGA_ACQ_EVENT_COUNT {len(event_records)}u
#define VEGA_ACQ_NO_INDEX 0xFFFFu
typedef struct VegaAcqEventDef {{
    const char *event_key; const char *species_key; const char *unlock_key;
    const char *claim_key; const char *source_item_key;
    uint16_t species_id; uint16_t claim_bit_index; uint16_t bounded_counter_index;
    uint8_t mode; uint8_t level; uint8_t max_claims; uint8_t policy_flags;
}} VegaAcqEventDef;
extern const VegaAcqEventDef gVegaAcqEventDefs[VEGA_ACQ_EVENT_COUNT];
#endif
"""
    event_c = ['#include "acquisition_event_defs.h"', '#include "../overlays/acquisition_runtime/acquisition_runtime.h"', '', 'const VegaAcqEventDef gVegaAcqEventDefs[VEGA_ACQ_EVENT_COUNT] = {']
    for record in event_records:
        event_c.append('    {' + ', '.join([
            c_string(record["event_key"]), c_string(record["species_key"]),
            c_string(record["unlock_key"]), c_string(record["claim_key"]),
            c_string(record["source_item_key"]), f'{record["species_id"]}u',
            f'{record["claim_bit_index"]}u', f'{record["bounded_counter_index"]}u',
            MODE_ENUM[str(record["mode"])], f'{record["level"]}u',
            f'{record["max_claims"]}u', f'{record["policy_flags"]}u',
        ]) + '},')
    event_c += ['};', '']

    class_value = {"REQUIRED_BASE": 1, "REQUIRED_VEGA_ORIGINAL": 2, "REQUIRED_ENABLING_FORM": 3, "OPTIONAL_FORM": 4, "BATTLE_ONLY_EXCLUDED": 5, "BATTLE_ONLY_EXCLUDED_COPY": 5, "UNOBTAINABLE_EVENT_FORM_EXCLUDED": 6}
    collection_h = f"""#ifndef VEGA_ACQUISITION_COLLECTION_DEFS_H
#define VEGA_ACQUISITION_COLLECTION_DEFS_H
#include <stdint.h>
#define VEGA_ACQ_CANONICAL_SPECIES_COUNT {len(registry)}u
#define VEGA_ACQ_COLLECTION_LEDGER_BIT_COUNT {len(collection_index)}u
#define VEGA_ACQ_COLLECTION_LEDGER_BYTES {collection_bytes}u
#define VEGA_ACQ_COMPLETION_TARGET_COUNT 1206u
typedef struct VegaAcqCollectionDef {{ uint16_t canonical_id; uint16_t ledger_bit_index; uint8_t completion_weight; uint8_t route_required; uint8_t target_class; uint8_t reserved; }} VegaAcqCollectionDef;
extern const VegaAcqCollectionDef gVegaAcqCollectionDefs[VEGA_ACQ_CANONICAL_SPECIES_COUNT];
#endif
"""
    collection_c = ['#include "acquisition_collection_defs.h"', '', 'const VegaAcqCollectionDef gVegaAcqCollectionDefs[VEGA_ACQ_CANONICAL_SPECIES_COUNT] = {']
    for row in registry:
        collection_c.append(f'    {{{int(row["canonical_id"])}u, {collection_index.get(row["species_key"], NO_INDEX)}u, {int(row["completion_weight"])}u, {1 if row["route_required"] == "yes" else 0}u, {class_value.get(row["target_status"], 0)}u, 0u}},')
    collection_c += ['};', '']

    release_hosts = sorted([row for row in hosts if row["status"] == "READY_TO_SERIALIZE"], key=lambda row: (int(row["group_id"]), int(row["map_id"]), int(row["local_id_or_bg_index"]), row["host_key"]))
    host_events: dict[str, list[int]] = defaultdict(list)
    for index, event in enumerate(events):
        if event["host_key"] in {row["host_key"] for row in release_hosts}:
            host_events[event["host_key"]].append(index)
    flat: list[int] = []
    ranges: list[tuple[int, int]] = []
    for host in release_hosts:
        start = len(flat); values = host_events[host["host_key"]]; flat.extend(values); ranges.append((start, len(values)))
    host_h = f"""#ifndef VEGA_ACQUISITION_HOST_DEFS_H
#define VEGA_ACQUISITION_HOST_DEFS_H
#include <stdint.h>
#define VEGA_ACQ_HOST_COUNT {len(release_hosts)}u
#define VEGA_ACQ_HOST_EVENT_INDEX_COUNT {len(flat)}u
typedef struct VegaAcqHostDef {{ const char *host_key; uint16_t first_event_index; uint16_t event_count; }} VegaAcqHostDef;
extern const VegaAcqHostDef gVegaAcqHostDefs[VEGA_ACQ_HOST_COUNT];
extern const uint16_t gVegaAcqHostEventIndices[VEGA_ACQ_HOST_EVENT_INDEX_COUNT];
#endif
"""
    host_c = ['#include "acquisition_host_defs.h"', '', 'const uint16_t gVegaAcqHostEventIndices[VEGA_ACQ_HOST_EVENT_INDEX_COUNT] = {']
    host_c += [f'    {value}u,' for value in flat]
    host_c += ['};', '', 'const VegaAcqHostDef gVegaAcqHostDefs[VEGA_ACQ_HOST_COUNT] = {']
    for host, (start, count) in zip(release_hosts, ranges):
        host_c.append(f'    {{{c_string(host["host_key"])}, {start}u, {count}u}},')
    host_c += ['};', '']

    wrapper_h = ['#ifndef VEGA_ACQUISITION_HOST_WRAPPERS_H', '#define VEGA_ACQUISITION_HOST_WRAPPERS_H', '']
    wrapper_c = ['#include "acquisition_host_wrappers.h"', '#include "../overlays/acquisition_runtime/acquisition_runtime.h"', '']
    patch_hosts = []
    for index, host in enumerate(release_hosts):
        symbol = f'VegaAcqHost_{slug(host["host_key"])}'
        wrapper_h.append(f'void {symbol}(void);')
        wrapper_c += [f'void {symbol}(void)', '{', f'    (void)VegaAcq_OpenHost({index}u);', '}', '']
        patch_hosts.append({
            "host_key": host["host_key"], "physical_map_key": host["physical_map_key"],
            "group_id": int(host["group_id"]), "map_id": int(host["map_id"]),
            "event_kind": host["event_kind"], "local_id": int(host["local_id_or_bg_index"]),
            "x": int(host["x"]), "y": int(host["y"]), "elevation": int(host["elevation"]),
            "object_count": int(host["object_count_before"]),
            "script_before_symbol": host["script_before"],
            "script_after_symbol": host["script_after"],
            "wrapper_symbol": symbol,
        })
        write(output / f'generated/map_scripts/{host["host_key"]}.inc', f"""@ Generated thin host script.  The Python serializer emits identical bytes.
lock
faceplayer
callnative {symbol}
waitstate
release
end
""")
    wrapper_h += ['', '#endif', '']

    save_h = f"""#ifndef VEGA_ACQUISITION_SAVE_LAYOUT_H
#define VEGA_ACQUISITION_SAVE_LAYOUT_H
#include <stdint.h>
#include "../overlays/acquisition_runtime/acquisition_runtime.h"
#define VEGA_ACQ_SAVE_MAGIC 0x51434156u
#define VEGA_ACQ_SAVE_VERSION 1u
#define VEGA_ACQ_COLLECTION_BYTES {collection_bytes}u
#define VEGA_ACQ_EVENT_CLAIM_BITS {len(claim_index)}u
#define VEGA_ACQ_EVENT_CLAIM_BYTES {event_claim_bytes}u
#define VEGA_ACQ_BOUNDED_COUNTER_COUNT {bounded_counter_bytes}u
#define VEGA_ACQ_ALIGNMENT_PADDING_BYTES {alignment_padding_bytes}u
#define VEGA_ACQ_EVOLUTION_COUNTER_BYTES {evolution_counter_bytes}u
#define VEGA_ACQ_SAVE_BLOCK_BYTES {save_block_bytes}u
typedef struct VegaAcqSaveBlock {{
    uint32_t magic; uint16_t version; uint16_t size; uint32_t crc32;
    uint8_t collection_bits[VEGA_ACQ_COLLECTION_BYTES];
    uint8_t event_claim_bits[VEGA_ACQ_EVENT_CLAIM_BYTES];
    uint8_t bounded_claim_counters[VEGA_ACQ_BOUNDED_COUNTER_COUNT];
    uint8_t alignment_padding[VEGA_ACQ_ALIGNMENT_PADDING_BYTES];
    uint8_t evolution_counters[VEGA_ACQ_EVOLUTION_COUNTER_BYTES];
    VegaAcqPendingTransaction pending;
}} VegaAcqSaveBlock;
_Static_assert(sizeof(VegaAcqSaveBlock) == VEGA_ACQ_SAVE_BLOCK_BYTES,
               "acquisition save ABI changed");
#endif
"""

    write(output / "generated/acquisition_event_defs.h", event_h)
    write(output / "generated/acquisition_event_defs.c", "\n".join(event_c))
    write(output / "generated/acquisition_collection_defs.h", collection_h)
    write(output / "generated/acquisition_collection_defs.c", "\n".join(collection_c))
    write(output / "generated/acquisition_host_defs.h", host_h)
    write(output / "generated/acquisition_host_defs.c", "\n".join(host_c))
    write(output / "generated/acquisition_host_wrappers.h", "\n".join(wrapper_h))
    write(output / "generated/acquisition_host_wrappers.c", "\n".join(wrapper_c))
    write(output / "generated/acquisition_save_layout.h", save_h)
    patch_manifest = {
        "schema_version": 1,
        "allocation_name": "acquisition_map_scripts",
        "release_policy": "READY_TO_SERIALIZE_OBJECT_REUSE_ONLY",
        "script_template": {"opcodes": ["lock:0x6A", "faceplayer:0x5A", "callnative:0x23 + thumb pointer", "waitstate:0x27", "release:0x6C", "end:0x02"]},
        "hosts": patch_hosts,
    }
    write(output / "generated/map_script_patch_manifest.json", json.dumps(patch_manifest, ensure_ascii=False, sort_keys=True, indent=2))


def compare_tree(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []
    for path in sorted(actual.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(actual)
        expected_path = expected / relative
        if not expected_path.is_file() or expected_path.read_bytes() != path.read_bytes():
            differences.append(str(relative))
    return differences


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    package = args.package.resolve()
    if args.check:
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp)
            generate(package, generated)
            differences = compare_tree(package, generated)
        if differences:
            print("generated files differ: " + ", ".join(differences), file=sys.stderr)
            return 1
        print("generated acquisition sources are reproducible")
        return 0
    output = (args.output or package).resolve()
    generate(package, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
