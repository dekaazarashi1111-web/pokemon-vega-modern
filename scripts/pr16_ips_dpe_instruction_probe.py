#!/usr/bin/env python3
"""PR16: 保存11参照の実ROM上の命令形とDPE output.binの実長を新scope限定で検査。

形を実行済みreaderへ昇格しない。ROM/IPS/Saveの実byteを公開しない。
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
DPE = 0x09673660
DPE_INSERT = 0x09600000
CANDIDATE = {"size": 33554432, "sha256": "0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583"}
XREFS = "content/modernization/pr16_selected_asset_xrefs_evidence/inverse-references.json"
CHAIN = "content/modernization/pr16_selected_ips_dpe_frontier_evidence/dpe-source-chain.json"

def require(ok, what):
    if not ok:
        raise ValueError(what)

def identity(raw):
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def serialize(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()

def inside(raw, address, width, base=BASE):
    require(isinstance(address, int) and isinstance(width, int) and width > 0 and base <= address and address + width <= base + len(raw), "ROM読み取り範囲")
    return raw[address-base:address-base+width]

def instruction_shapes(raw, site, base=BASE):
    """有限実byteのARM/Thumb PC literal命令形。到達可能性/命令モードは別証明。"""
    inside(raw, site, 4, base)
    result = []
    if site % 4:
        return result
    low = max(base, site-4104)
    high = min(base+len(raw)-4, site+4104)
    for pc in range((low+3)&~3, high+1, 4):
        word = struct.unpack("<I", inside(raw, pc, 4, base))[0]
        # ARM LDR word, immediate/pre-index, Rn=PC, no writeback, both U directions.
        if word & 0x0F7F0000 == 0x051F0000 and word >> 28 != 0xF:
            displacement = word & 0xFFF
            address = pc + 8 + (displacement if word & (1<<23) else -displacement)
            if address == site:
                result.append({"pc": pc, "mode": "ARM_LDR_LITERAL_SHAPE", "reader_proven": False})
    low = max(base, site-1028)
    high = min(site-2, base+len(raw)-2)
    for pc in range((low+1)&~1, high+1, 2):
        half = struct.unpack("<H", inside(raw, pc, 2, base))[0]
        if half & 0xF800 == 0x4800 and (((pc+4)&~3) + (half&255)*4) == site:
            result.append({"pc": pc, "mode": "THUMB_LDR_LITERAL_SHAPE", "reader_proven": False})
    return sorted(result, key=lambda x: (x["pc"], x["mode"]))

def probe(raw, saved):
    require(identity(raw) == CANDIDATE, "固定ROM全SHA")
    require(saved["candidate"] == CANDIDATE and saved["first_level_count"] == len(saved["first_level"]) == 11, "保存参照11件")
    require(saved["literal_shape_count"] == 0, "旧限定Thumb形の記録")
    rows = []
    for x in saved["first_level"]:
        site = x["address"]
        bytes_ = inside(raw, site, 4)
        require(identity(bytes_) == {"size": 4, "sha256": x["sha256"]}, "保存参照原本4byte同一")
        stored = struct.unpack("<I", bytes_)[0]
        require(stored == x["target"] and (stored & ~1) >= BASE, "保存参照pointer全byte")
        require(BASE + (((stored & ~1) - BASE) % 0x02000000) == (x["canonical_target"] & ~1), "保存参照mirror正規化")
        shapes = instruction_shapes(raw, site)
        rows.append({"site": site, "canonical_target": x["canonical_target"], "mirror": x["mirror"],
                     "alignment_mod4": site % 4, "saved_word_sha256": x["sha256"],
                     "literal_shapes": shapes, "actual_instruction_fetch_proven": False,
                     "runtime_reader_proven": False,
                     "category": "PRIOR_ACCEPTED_PLA1_NOT_REPLAYED" if site == 0x095FE848 else "READER_PENDING"})
    require(len({r["site"] for r in rows}) == 11 and sum(r["alignment_mod4"] != 0 for r in rows) == 9, "参照originの重複/整列")
    require(any(r["site"] == DPE and r["canonical_target"] == 0x0880EFD0 for r in rows), "DPE保存pointer一致")
    return {"schema_version": 1, "task": "USER-20261012-IPS-DPE-INSTRUCTION-EXTENT",
            "candidate": CANDIDATE, "saved_first_level_references": 11, "unaligned_pointer_shapes": 9,
            "rows": rows, "instruction_shape_is_execution_proof": False,
            "classification_changes": 0, "formal_classified": 789, "formal_unclassified": 85,
            "selected_unknown_origins": 6, "donor_safe_bytes": 0,
            "private_raw_published": False}

def dpe_extent(raw, paths, chain):
    """出所付きファイルの実byteがある場合のみ測る。静的予約regionを実blobと混同しない。"""
    require(chain["upstream"]["commit"] == "10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e", "DPE固定pin")
    require(chain["build_contract"]["insert_address"] == DPE_INSERT and chain["build_contract"]["insert_copies_build_output_bin_contiguously"], "挿入契約")
    matches = []
    for p in paths:
        require(p.name == "output.bin" and "dpe" in (part.lower() for part in p.parts), "DPE候補以外のblob")
        size = p.stat().st_size
        if not 0 < size <= 0xA00000:
            continue
        with p.open("rb") as f:
            data = f.read()
        offset = DPE - DPE_INSERT
        containing = offset+4 <= len(data)
        same = containing and data[offset:offset+4] == inside(raw, DPE, 4)
        matches.append({"relative_cache_location": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else "OUTSIDE_ROOT",
                        "blob_identity": identity(data), "site_contained": containing,
                        "site_bytes_equal_current": same, "pinned_build_proven": False})
    return {"insertion_address": DPE_INSERT, "site": DPE, "offset": DPE-DPE_INSERT,
            "observed_candidates": matches, "source_pin": chain["upstream"]["commit"],
            "actual_output_bin_inclusion_proven": False,
            "linked_symbol_owner_proven": False, "asset_reader_proven": False,
            "donor_safe_bytes": 0, "note_ja": "cache内の候補output.binは出所/作成コマンドのpin照合が未了なら正式所有証明に使わない。候補なしもFAILとせず未証明を保持。"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path)
    args = parser.parse_args()
    require(not args.output.is_symlink() and not args.rom.is_symlink(), "symlink禁止")
    raw = args.rom.read_bytes()
    proof = probe(raw, json.loads((ROOT/XREFS).read_text()))
    chain = json.loads((ROOT/CHAIN).read_text())
    candidates = []
    if args.cache_root is not None and args.cache_root.is_dir() and not args.cache_root.is_symlink():
        candidates = sorted(p for p in args.cache_root.rglob("output.bin") if p.is_file() and "dpe" in (x.lower() for x in p.parts))
        require(len(candidates) <= 16, "未選定output.bin候補過多")
    proof["dpe_output_probe"] = dpe_extent(raw, candidates, chain)
    proof["accepted_test_reruns"] = 0
    proof["candidate_reconstructions_for_this_scope"] = 1
    proof["native_processes"] = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(serialize(proof))
    require(args.output.read_bytes() == serialize(proof), "保存後byte一致")
    print("IPS_DPE_INSTRUCTION_ROWS=11")
    print("IPS_DPE_UNALIGNED=9")
    print("IPS_DPE_OUTPUT_CANDIDATES=" + str(len(candidates)))
    print("RESULT=DONE TASK=USER-20261012-IPS-DPE-INSTRUCTION-EXTENT VERIFY=PASS COMMIT=-")

if __name__ == "__main__":
    main()
