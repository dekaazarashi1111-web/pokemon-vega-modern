#!/usr/bin/env python3
"""PR16未解決2地点のIPS書込区間とDPE配置envelopeをfail-closed照合。

書込record/予約envelope/一致pointerは実asset境界・実caller・容量を証明しない。
受入済みPLA1、旧探索、ROM再生成、nativeの再実行は行わない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = "content/modernization/pr16_selected_asset_provenance_evidence/provenance.json"
XREFS = "content/modernization/pr16_selected_asset_xrefs_evidence/inverse-references.json"
STATE = "content/modernization/pr16_wiki_first_execution_plan.json"
DPE_SOURCE = "scripts/build_upstream.py"
ORIGIN = 0x0880FA64
DPE_POINTER = 0x09673660
PLA1_POINTER = 0x095FE848
ROM_BASE = 0x08000000
CANDIDATE_SHA = "0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583"


def require(ok: bool, name: str) -> None:
    if not ok:
        raise ValueError(name)


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def bound(provenance: dict, xrefs: dict, source: str, state: dict) -> dict:
    """承認済み証拠を読むだけの有限境界証明。実readerを推定しない。"""
    lane = state["owner_execution_plan"]["technical_lanes"]["save_capacity"]
    require(state["next_action"]["id"] == "SAVE_CAPACITY_IPS_AND_DPE_ASSET_READERS", "固定next")
    require([lane[k] for k in ("classified", "unclassified", "selected_unknown_origins", "donor_safe_bytes")]
            == [789, 85, 6, 0], "正式数と安全容量")
    require(provenance["candidate"] == xrefs["candidate"]
            == {"size": 33554432, "sha256": CANDIDATE_SHA}, "現候補identity")
    require(provenance["ips_record_count"] == 20195 and provenance["ips_truncate"] is None, "IPS原本record")
    rows = {r["address"]: r for r in provenance["rows"]}
    require(len(rows) == 3 and set(rows) == {ORIGIN, DPE_POINTER, PLA1_POINTER}, "3対象限定")
    ips = rows[ORIGIN]["ips"]
    owners = rows[ORIGIN]["modernization"]
    require(ips["fully_resolved"] and ips["reference_matches"] and ips["width"] == 4
            and ips["last_writer_indices"] == [11873] * 4
            and len(ips["overlapping_records"]) == 1, "IPS全4byte最終writer")
    r = ips["overlapping_records"][0]
    require(r["index"] == 11873 and r["kind"] == "literal" and r["patch_offset"] == 2048219
            and r["start"] == 0x80B7B0 and r["end_exclusive"] == 0x80FAD0
            and r["payload_identity"]["size"] == r["end_exclusive"] - r["start"] == 17184,
            "IPS固定書込区間")
    start, end = ROM_BASE + r["start"], ROM_BASE + r["end_exclusive"]
    require(start <= ORIGIN and ORIGIN + 4 <= end and
            ips["offset"] == ORIGIN - ROM_BASE, "対象4byteの包含")
    require(owners["owners"] == [] and not owners["fully_owned"]
            and not owners["free_space_proven"], "Vega origin未所有はfreeでない")
    require(rows[ORIGIN]["current_target_equals_vega"] is True, "Vega最終byte一致")
    require(xrefs["origin"]["address"] == ORIGIN and
            xrefs["first_level_count"] == len(xrefs["first_level"]) == 11
            and xrefs["second_level_count"] == 1 and xrefs["literal_shape_count"] == 0,
            "保存済み逆参照のみ")
    refs = []
    for x in xrefs["first_level"]:
        require(start <= x["canonical_target"] < ORIGIN and
                x["canonical_target"] < end, "第1段pointerのIPS区間包含")
        require(x["target_offset_from_hit"] == x["canonical_target"] - ORIGIN
                and x["thumb_literal_shapes"] == [], "保存pointer identity")
        refs.append(dict(origin=x["address"], target=x["canonical_target"],
                         delta_to_unknown=x["target_offset_from_hit"],
                         offset_inside_ips_record=x["canonical_target"] - start,
                         mirror=x["mirror"], instruction_reader_proven=False))
    require(len({x["origin"] for x in refs}) == 11 and
            set(x["origin"] for x in refs) >= {DPE_POINTER, PLA1_POINTER},
            "参照起点集合")
    require(next(x["target"] for x in refs if x["origin"] == DPE_POINTER) == 0x0880EFD0,
            "DPE地点の保存指向値")
    require(next(x["target"] for x in refs if x["origin"] == PLA1_POINTER) == 0x0880F004,
            "受入済みPLA1地点の保存指向値")
    require(not rows[DPE_POINTER]["ips"]["fully_resolved"]
            and rows[DPE_POINTER]["modernization"]["owners"] == []
            and not rows[DPE_POINTER]["modernization"]["fully_owned"]
            and not rows[DPE_POINTER]["modernization"]["free_space_proven"],
            "DPE未所有は空き容量でない")
    require([x["name"] for x in rows[PLA1_POINTER]["modernization"]["owners"]]
            == ["pr16_supply_pla1"], "受入済みPLA1の現ownerを保持")
    size = re.search(r"(?m)^ROM_SIZE = (0x[0-9A-Fa-f]+)$", source)
    insert = re.search(r"(?m)^DPE_OFFSET = (0x[0-9A-Fa-f]+)$", source)
    require(size is not None and insert is not None
            and int(size.group(1), 16) == 0x2000000
            and int(insert.group(1), 16) == 0x1600000
            and 'insertion_offset = DPE_OFFSET' in source
            and 'output.bin is not present at insertion offset' in source,
            "固定DPE配置契約")
    dpe_start, dpe_end = ROM_BASE + int(insert.group(1), 16), ROM_BASE + int(size.group(1), 16)
    require(dpe_start <= DPE_POINTER < dpe_end and DPE_POINTER + 4 <= dpe_end,
            "DPE予約envelope包含")
    require(provenance["formal_classification_changes"] == 0
            and not provenance["actual_asset_reader_proven"]
            and not xrefs["actual_asset_reader_proven"], "受入外実readerを捏造しない")
    return {
        "schema_version": 1, "task": "USER-20261012-IPS-DPE-BOUNDARY",
        "candidate": provenance["candidate"],
        "ips": {
            "record_index": 11873, "patch_offset": r["patch_offset"],
            "write_start": start, "write_end_exclusive": end,
            "write_size": end - start, "target": ORIGIN,
            "target_offset": ORIGIN - start, "bytes_after_target": end - (ORIGIN + 4),
            "payload_identity": r["payload_identity"], "asset_start_proven": False,
            "asset_end_proven": False, "caller_proven": False,
        },
        "dpe": {
            "pointer_site": DPE_POINTER, "saved_pointer_value": 0x0880EFD0,
            "envelope_start": dpe_start, "envelope_end_exclusive": dpe_end,
            "offset_from_envelope_start": DPE_POINTER - dpe_start,
            "output_blob_extent_proven": False, "real_owner_proven": False,
            "asset_reader_proven": False, "free_space_proven": False,
        },
        "saved_first_level_refs_inside_ips_record": sorted(refs, key=lambda x: x["origin"]),
        "saved_first_level_count": len(refs), "new_rom_scans": 0,
        "candidate_reconstructions": 0, "accepted_test_reruns": 0,
        "formal_classification_changes": 0, "formal_classified": 789,
        "formal_unclassified": 85, "selected_unknown_origins": 6,
        "donor_safe_bytes": 0,
        "limitations_ja": [
            "IPS recordのwrite境界はasset境界でも実callerでもない。",
            "DPE envelopeは配置予約座標でありoutput.binの実包含/実owner証明ではない。",
            "旧11 pointer形を実命令によるreadや全起点網羅に昇格しない。",
            "PLA1の受入済みreader以外のreaderは未完。正式origin分類/容量/Saveは不変。",
        ],
    }


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    report = bound(read_json(PROVENANCE), read_json(XREFS),
                   (ROOT / DPE_SOURCE).read_text(encoding="utf-8"), read_json(STATE))
    output = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    require(not args.output.is_symlink(), "symlinkを拒否")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    require(args.output.read_bytes() == output, "保存後byte一致")
    print("IPS_RECORD_BOUND=0x%08X..0x%08X" %
          (report["ips"]["write_start"], report["ips"]["write_end_exclusive"]))
    print("DPE_ENVELOPE_OFFSET=0x%X" % report["dpe"]["offset_from_envelope_start"])
    print("RESULT=DONE TASK=USER-20261012-IPS-DPE-BOUNDARY VERIFY=PASS COMMIT=-")


if __name__ == "__main__":
    main()
