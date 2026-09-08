#!/usr/bin/env python3
"""P01: clean ROMと固定済み累積BPSから、2行だけを訂正する別候補を再生成。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.audit_p01_rom import collection_image, occurrences
from scripts.build_modernization_catalog import encoded
from scripts.build_p01_collection_table import generate, SOURCE
from tools.modernization_ids import IdentityError
from tools.release.bps import apply_bps, create_bps

CONFIG = "config/modernization_rom_repair.json"


def identity(raw: bytes) -> dict:
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "crc32": f"{zlib.crc32(raw) & 0xffffffff:08X}"}


def apply_table(parent: bytes, old: bytes, new: bytes, policy: dict) -> tuple[bytes, list[int]]:
    start = policy["table_offset"]
    if (len(parent) != 33554432 or len(old) != policy["table_size"] or len(new) != len(old)
            or hashlib.sha256(old).hexdigest() != policy["old_table_sha256"]
            or hashlib.sha256(new).hexdigest() != policy["new_table_sha256"]):
        raise IdentityError("P01_TABLE_SIZE_OR_HASH_MISMATCH")
    if occurrences(parent, old) != [start]:
        raise IdentityError("P01_PARENT_TABLE_LOCATION_MISMATCH")
    if policy["row_size"] != 8 or policy["changed_species_ids"] != [412, 649]:
        raise IdentityError("P01_ROW_PATCH_SCOPE_MISMATCH")
    if any(policy[name] for name in ("collection_bit_reindex", "save_abi_change", "new_allocation", "play_baseline_switch")):
        raise IdentityError("P01_PRESERVATION_POLICY_MISMATCH")
    allowed = {sid * 8 + byte for sid in policy["changed_species_ids"] for byte in range(8)}
    changed = [i for i, (left, right) in enumerate(zip(old, new)) if left != right]
    if not changed or not set(changed) <= allowed:
        raise IdentityError("P01_UNDECLARED_TABLE_CHANGE")
    # Row先頭のcanonical IDそのものは動かさない。非ID属性だけを正しいSpecies行へ結合する。
    if any(old[sid * 8:sid * 8 + 2] != new[sid * 8:sid * 8 + 2] for sid in range(1621)):
        raise IdentityError("P01_EXISTING_SPECIES_ID_CHANGED")
    result = parent[:start] + new + parent[start + len(old):]
    if result[:start] != parent[:start] or result[start + len(old):] != parent[start + len(old):]:
        raise IdentityError("P01_ROM_OUTSIDE_DECLARATION_CHANGED")
    return result, [start + offset for offset in changed]


def verified_patch(root: Path, relative: str) -> tuple[bytes, dict]:
    config = json.loads((root / "config/github_private_environment.json").read_text())
    pins = []
    for archive in config["archives"]:
        manifest = root / ".local/github-private-environment/manifests" / (archive["name"] + ".json")
        document = json.loads(manifest.read_text())
        if document.get("archive") != archive["name"]:
            raise IdentityError("P01_RESTORED_ARCHIVE_MANIFEST_MISMATCH")
        for row in document["files"]:
            if row["path"] == relative:
                pins.append({"size": row["size"], "sha256": row["sha256"]})
    if not pins or any(row != pins[0] for row in pins):
        raise IdentityError("P01_PARENT_PATCH_RECEIPT_MISSING_OR_CONFLICTING")
    path = root / relative
    if path.is_symlink():
        raise IdentityError("P01_PATCH_SYMLINK")
    raw = path.read_bytes()
    if len(raw) != pins[0]["size"] or hashlib.sha256(raw).hexdigest() != pins[0]["sha256"]:
        raise IdentityError("P01_PARENT_PATCH_HASH_MISMATCH")
    return raw, pins[0]


def build_payloads(root: Path) -> dict[str, bytes]:
    policy = json.loads((root / CONFIG).read_text())
    baseline = json.loads((root / "config/active_play_baseline.json").read_text())
    if baseline["stage"] != policy["parent_stage"] or baseline["rom"]["sha256"] != policy["parent_sha256"]:
        raise IdentityError("P01_PARENT_SELECTION_MISMATCH")
    clean = (root / policy["clean_rom"]).read_bytes()
    if len(clean) != policy["clean_size"] or hashlib.sha256(clean).hexdigest() != policy["clean_sha256"]:
        raise IdentityError("P01_CLEAN_ROM_IDENTITY_MISMATCH")
    patch, patch_pin = verified_patch(root, policy["parent_clean_patch"])
    parent = apply_bps(clean, patch)
    expected = {key: baseline["rom"][key] for key in ("size", "sha256", "crc32")}
    if identity(parent) != expected or (root / baseline["rom"]["path"]).read_bytes() != parent:
        raise IdentityError("P01_CLEAN_TO_PARENT_NOT_IDENTICAL")
    source = (root / SOURCE).read_text()
    old, _ = collection_image(source, 1621)
    first = generate(root)
    second = generate(root)
    if first != second:
        raise IdentityError("P01_TABLE_GENERATION_NOT_DETERMINISTIC")
    new = first["acquisition_collection_defs.bin"]
    candidate, changes = apply_table(parent, old, new, policy)
    repeated, repeated_changes = apply_table(apply_bps(clean, patch), old, second["acquisition_collection_defs.bin"], policy)
    if repeated != candidate or repeated_changes != changes:
        raise IdentityError("P01_CLEAN_REBUILD_NOT_DETERMINISTIC")
    incremental = create_bps(parent, candidate, metadata=b"USER-MODERNIZATION-P01 collection identity")
    reverse = create_bps(candidate, parent, metadata=b"USER-MODERNIZATION-P01 parent restore")
    direct = create_bps(clean, candidate, metadata=b"USER-MODERNIZATION-P01 clean rebuild")
    if (apply_bps(parent, incremental) != candidate or apply_bps(candidate, reverse) != parent
            or apply_bps(clean, direct) != candidate):
        raise IdentityError("P01_PATCH_ROUNDTRIP_MISMATCH")
    # 元ROM/clean/固定BPSを処理中にも変更していないことをbyte照合する。
    if ((root / baseline["rom"]["path"]).read_bytes() != parent
            or (root / policy["clean_rom"]).read_bytes() != clean
            or (root / policy["parent_clean_patch"]).read_bytes() != patch):
        raise IdentityError("P01_ORIGINAL_INPUT_CHANGED")
    files = {policy["output_rom"]: candidate,
             "build/modernization/stage62-to-p01.bps": incremental,
             "build/modernization/p01-to-stage62.bps": reverse,
             "build/modernization/clean-to-p01.bps": direct}
    report = {"schema_version": 1, "task": "USER-MODERNIZATION-P01", "candidate_key": policy["candidate_key"],
              "parent": expected, "clean": identity(clean), "candidate": identity(candidate),
              "parent_clean_patch": {"path": policy["parent_clean_patch"], **patch_pin},
              "changed_bytes": len(changes), "changed_offsets": changes,
              "declared_spans": [{"offset": policy["table_offset"] + sid * 8, "size": 8, "species_id": sid} for sid in (412, 649)],
              "undeclared_changes": 0, "table_sha256": hashlib.sha256(new).hexdigest(),
              "deterministic_clean_rebuilds": 2, "incremental_roundtrip": True, "reverse_roundtrip": True, "clean_roundtrip": True,
              "save_abi_change": False, "collection_bit_reindex": False, "new_allocation": False,
              "play_baseline_switch": False, "runtime_test": "SEPARATE_MGBA_GATE_REQUIRED",
              "outputs": {path: identity(raw) for path, raw in files.items()}}
    files["generated/modernization/candidate_build.json"] = encoded(report)
    return files


def execute(root: Path, command: str) -> dict:
    if command not in ("build", "check"):
        raise IdentityError("P01_INVALID_BUILD_COMMAND")
    files = build_payloads(root)
    for relative, raw in files.items():
        path = root / relative
        if path.is_symlink() or path.parent.resolve() != path.parent.absolute():
            raise IdentityError("P01_OUTPUT_SYMLINK")
        if command == "check":
            if not path.is_file() or path.read_bytes() != raw:
                raise IdentityError("P01_CANDIDATE_OUTPUT_DRIFT")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".p01-rom-", delete=False) as f:
                temp = Path(f.name)
                f.write(raw)
            try:
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
    return json.loads(files["generated/modernization/candidate_build.json"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    try:
        report = execute(ROOT, args.command)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except IdentityError as exc:
        print("P01_ROM_BUILD_FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
