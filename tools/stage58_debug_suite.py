#!/usr/bin/env python3
"""Stage58の全map/event/wild/Codex拠点をexact ROMから横断監査する。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import struct
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_interaction_ownership_repair import _wild_audit  # noqa: E402
from tools.stage57_debug_suite import (  # noqa: E402
    _collect_contactable_roots,
    quick_audit as stage57_quick_audit,
)
from tools.stage58_world_balance import (  # noqa: E402
    FIRERED_SLOT_PROBABILITIES,
    WILD_SLOT_COUNTS,
    WorldBalanceError,
    audit_world_balance_plan,
)
from tools.t02.rom_inventory import RomImage, ScriptWalker  # noqa: E402
from tools.trainer_final.kanto_events import (  # noqa: E402
    _object_fields,
    _stage_map_state,
)


TASK = "USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG"
STAGE = 58
ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
STAGE57_ROM = Path("build/stages/57_comprehensive_debug_repair.gba")
STAGE57_METADATA = Path("build/stages/57_comprehensive_debug_repair.json")
STAGE50_ROM = Path("build/stages/50_interaction_ownership_repair.gba")
STAGE50_ITEM_REPORT = Path("reports/generated/interaction_ownership_repair.json")
DEFAULT_ROM = Path("build/stages/58_qol_world_convenience_debug.gba")
DEFAULT_METADATA = Path("build/stages/58_qol_world_convenience_debug.json")
DEFAULT_CASES = Path("generated/runtime/stage58_qol_world_convenience_debug_cases.json")
EXPECTED_ROOT_COUNTS = {
    "object": 3098,
    "coord": 743,
    "bg": 1031,
    "map_script": 569,
}
EXPECTED_MODE_TABLES = {
    "land": 164,
    "water": 44,
    "rock": 17,
    "fishing": 46,
}
GET_POCKET_BY_ITEM_ID_OFFSET = 0x0009A3E8
BUY_MENU_TRY_MAKE_PURCHASE_OFFSET = 0x0009B894
GET_POCKET_BY_ITEM_ID_EXPECTED = bytes.fromhex(
    "10b50004000c064cfff75cff0004000c81000918c9000919887d10bc02bc0847"
)
BUY_MENU_TRY_MAKE_PURCHASE_EXPECTED = bytes.fromhex(
    "30b50006050ea8004019c0000d494418042068f761fb60896188fef7edf80006"
    "000e012814d10849084a281ca4f0defa281c00f0ddf860896188012200f0dcf8"
    "0be00000d850000375dc3d08fdb809080349044a281ca4f0c9fa30bc01bc0047"
)
SAVEBLOCK_KEY_ROTATION_CALL_SITE = 0x0804B8FA
SAVEBLOCK_KEY_ROTATION_ORIGINAL_CALL = bytes.fromhex("00f02ffa")
SAVEBLOCK_KEY_ROTATION_STOCK_BAG_SITE = 0x0804BD76
SAVEBLOCK_KEY_ROTATION_STOCK_BAG_CALL = bytes.fromhex("4df063fd")
SAVEBLOCK_KEY_ROTATION_VENEER = 0x0837BEAC
SAVEBLOCK_CALLBACK_RESTORE_SITE = 0x0804B8DE
SAVEBLOCK_CALLBACK_RESTORE_EXPECTED = bytes.fromhex("019820610099e160")
CODEX_SAVE_LAYOUT_FUNCTION_CONTRACT = {
    "Stage58QolItemAdapter_CodexSnapshotSeenMirrors": (
        0x0941710C, 168,
        "07a361604ee0e8b2a18f7e1ed837bc6bffbbe76a4adf6fc3c3d31dc3cb992275",
    ),
    "Stage58QolItemAdapter_CodexRestoreSeenMirrors": (
        0x094171B4, 168,
        "c825f95f54307b62e2280ecd1d28daccf900e843dbdfa04ffeb43992cb78261a",
    ),
    "Stage58QolItemAdapter_CodexContinueSeenHash": (
        0x0941725C, 124,
        "7423f54db7757a1ad30af45e7d78070ba9113894011c38ae6992fc9fa6a87b47",
    ),
}
CODEX_SAVE_LAYOUT_PATCH_CONTRACT = (
    ("snapshot_save1", 0x093CB45A,
     "903be1189622314800f0acfa", "snapshot"),
    ("snapshot_save2_legacy", 0x093CB48A,
     "290010222848183100f094fa", None),
    ("restore_save1", 0x093CD66A,
     "c423fe3a9b004e490700ff3ae818fef7a1f9", "restore"),
    ("restore_save2_legacy", 0x093CD6B0,
     "300010223f491830fef781f9", None),
    ("hash_save1", 0x093CCEAC,
     "c423224a9b00eb18a9181a78013354407c438b42f9d1", "hash"),
    ("hash_save2_legacy", 0x093CCF0A,
     "3300283618331a78013354407c43b342f9d1", "skip"),
)
THIN_FLAG_GET_EXPECTED = struct.pack(
    "<22HIII",
    0x480A, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A09,
    0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7812,
    0x2301, 0x4083, 0x401A, 0x2A00, 0xD000, 0x2201,
    0x4803, 0x8002, 0x4770, 0x46C0,
    0x02036FEC, 0x03005048, 0x02037004,
)
THIN_FLAG_SET_EXPECTED = struct.pack(
    "<18HII",
    0x4808, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A07,
    0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7811,
    0x2301, 0x4083, 0x4319, 0x7011, 0x4770, 0x46C0,
    0x02036FEC, 0x03005048,
)
CODEX_RESULT_CONTRACT = {
    "table": 0x0820CAE8,
    "win_site": 0x0820CAEC,
    "loss_site": 0x0820CAF0,
    "draw_site": 0x0820CAF4,
    "win_inherited": 0x093D203D,
    "loss_inherited": 0x093D2059,
    "draw_inherited": 0x093D2059,
    "return_to_field": 0x093D1E01,
    "result_script": 0x081BC8BB,
}
CODEX_RESULT_REQUIRED_LITERALS = (
    0x0203FA00,  # Stage47 runtime state owner
    0x32524243,  # Stage47 runtime magic
    0xCDADBDBC,  # magic inverse
    0x02022AAC,  # gBattleTypeFlags
    0xFFF7FFFF,  # ~BATTLE_TYPE_TRAINER_TOWER
    0x020385E2,  # gTrainerBattleOpponent_A
    0x03003138,  # gMain.savedCallback
    0x08000545,  # SetMainCallback2
    0x080561A1,  # continue suspended trainerbattle script
    0x093D1E01,  # final Stage47 reward return adapter
    0x02023CD4,  # gBattlescriptCurrInstr
    0x081BC8BB,  # stock Pickup+end2 tail
    0x08014E91,  # stock won handler
    0x08014FA5,  # stock lost handler
    0x093D203D,  # inherited non-Codex won adapter
    0x093D2059,  # inherited non-Codex lost adapter
)
# arm-none-eabi-gcc/ARM7TDMIで生成したCodex結果ownerの独立exact契約。
# metadata内の自己申告SHAだけでは、codeとSHAを同時に壊したmutationを検出
# できないため、各公開ownerの配置・size・命令/literal poolをここで固定する。
CODEX_RESULT_FUNCTION_CONTRACT = {
    "Stage58QolItemAdapter_CodexTransactionIdentityValid": (
        56, 52, "890f0fcedad7e43f39f5c640a9e440ef8f3681747d2f1a3e29ecb4238555e3b3",
    ),
    "Stage58QolItemAdapter_CodexReturnToFieldAdapter": (
        108, 46, "a0a7d900485dd7a0835139456d8bf5e1aeb16ad45a108227a21a56639755fb3d",
    ),
    "Stage58QolItemAdapter_CodexResultStateValid": (
        156, 60, "4cc14c7dcead7010ad53f408adec9b8f9a3c02b7a30e739d46e8f18db99cb285",
    ),
    "Stage58QolItemAdapter_CodexBattleResultOwned": (
        216, 52, "cef2401a0ce83ce53e61ec94c2b35b4d2e32526485d7d5463fc164f621e4de17",
    ),
    "Stage58QolItemAdapter_CodexLegacyResultHazard": (
        268, 44, "727f4a04e5c07f12f8cc68dcf026a72e452e9b0192ea907f49eb2470b3f0861e",
    ),
    "Stage58QolItemAdapter_CodexRewardResultKind": (
        312, 48, "a0c340451f1682e861cfd737c4fc79901eb5e98e722d3805d74b4f476ad0fd99",
    ),
    "Stage58QolItemAdapter_FinishNonpunitiveCodexResult": (
        360, 66, "eebdb4a99d597ae77dfc64b56c2718d8bc37295a7bff977d543868e392945c4b",
    ),
    "Stage58QolItemAdapter_CodexBattleWonAdapter": (
        428, 54, "0332e89ad67bec9ffad433d9862c9f9799fdbbcae6129cd56cbf73935df21a7e",
    ),
    "Stage58QolItemAdapter_CodexBattleLostAdapter": (
        484, 54, "5c5dbe44b66d7b06f4bb50453c5643447517e44a8707c35feeabe453f25d2494",
    ),
}
CODEX_RESULT_INHERITED_EXACT = (
    (0x081BC8BB, bytes.fromhex("e53e")),
    (0x093CDAFB, struct.pack("<I", 0x093D2075)),
    (0x093CDB08, struct.pack("<I", 0x093D2115)),
    (0x093CDB2A, struct.pack("<I", 0x093D2115)),
    (
        0x080561A0,
        bytes.fromhex(
            "00b500f06bf8034903480860fff776ff01bc00476050000385d40708"
        ),
    ),
    (
        0x093D1E00,
        bytes.fromhex(
            "10b500f00dfb002811d00b4b1a7d002a0dd0db7e002b0ad0084b1b78002b06d0"
            "0748084b00f012f810bc01bc0047064b00f00cf8f8e7c04600fa03022ffa0302"
            "a161050845050008cdfb07081847c046"
        ),
    ),
)
CODEX_RESULT_LEGACY_FUNCTION_CONTRACT = {
    "reward_win": (
        0x093D203C, 26,
        "8dcbe1971d57f5e1c291256c33ad4fcc37bbdf67a33d702441240837f36d1925",
        "8dcbe1971d57f5e1c291256c33ad4fcc37bbdf67a33d702441240837f36d1925",
    ),
    "reward_loss": (
        0x093D2058, 26,
        "64879a4bd991d5c0a4046bc69350de4c93101b0a776c4239714b67f5cb29b97e",
        "64879a4bd991d5c0a4046bc69350de4c93101b0a776c4239714b67f5cb29b97e",
    ),
    "reward_arm_nonpunitive": (
        0x093D2BA8, 88,
        "f1dc228efb072320dafa5d333f0633a1dc6ec1a8c3c37f7b38871cbac76c96b8",
        "f1dc228efb072320dafa5d333f0633a1dc6ec1a8c3c37f7b38871cbac76c96b8",
    ),
    "reward_after_battle": (
        0x093D2074, 158,
        "3dac1e39398f098703abc12e25c6f278950d6603b9861cb6f59e6605f954f74c",
        "bb539984523c99a0eadbf909d926d29207be8bd766631bcc3a1290f64c317b39",
    ),
    "reward_field_finish": (
        0x093D2114, 46,
        "fcd89ecac7b0d3895714d529bd9e9ddffe07b48e19c4233e1bb9641bac076af1",
        "fcd89ecac7b0d3895714d529bd9e9ddffe07b48e19c4233e1bb9641bac076af1",
    ),
    "runtime_after_battle": (
        0x093CB820, 56,
        "dcef65d884e78b5db6b6a7ca2c48bde1ff05f5a24c4d51cc4a95fbabcd846a3e",
        "dcef65d884e78b5db6b6a7ca2c48bde1ff05f5a24c4d51cc4a95fbabcd846a3e",
    ),
    "runtime_field_finish": (
        0x093CB858, 64,
        "171aa817eaca74795c7d10b54f1708dbdd2e662748182279a178b268f4db5304",
        "171aa817eaca74795c7d10b54f1708dbdd2e662748182279a178b268f4db5304",
    ),
}


class Stage58DebugError(RuntimeError):
    """Stage58のidentity、map graph、scriptまたはwild契約違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage58DebugError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _read_document(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _identity(raw: bytes, metadata: Mapping[str, Any],
              cases: Mapping[str, Any]) -> str:
    digest = _sha(raw)
    if len(raw) != ROM_SIZE:
        _fail(f"Stage58 ROM size不一致: {len(raw)}")
    if (metadata.get("task"), metadata.get("stage")) != (TASK, STAGE):
        _fail("Stage58 metadata task/stage不一致")
    if (cases.get("task"), cases.get("stage")) != (TASK, STAGE):
        _fail("Stage58 cases task/stage不一致")
    if metadata.get("output", {}).get("sha256") != digest \
            or cases.get("rom_sha256") != digest:
        _fail("Stage58 ROM/metadata/cases SHA-256不一致")
    return digest


def _root_key(root: Any) -> tuple[str, str, int]:
    return str(root.label), str(root.kind), int(root.address)


def _root_inventory(raw: bytes) -> tuple[list[Any], Counter[str]]:
    return _collect_contactable_roots(RomImage("Stage58", raw))


def _expected_added_roots(output: bytes,
                          cases: Mapping[str, Any]) -> set[tuple[str, str, int]]:
    hub = cases["codex_hub"]
    values = {
        (f"map:{hub['group']}:{hub['map']}:object:10", "object",
         int(hub["pc"]["script"])),
        (f"map:{hub['group']}:{hub['map']}:object:11", "object",
         int(hub["healer"]["script"])),
        (f"map:{hub['group']}:{hub['map']}:object:12", "object",
         int(hub["mart"]["script"])),
    }
    for row in cases["thin_events"]:
        state = _stage_map_state(
            output, int(row["group"]), int(row["map"]),
        )
        fields = _object_fields(state["objects"][-1])
        values.add((
            f"map:{row['group']}:{row['map']}:object:{row['object_count_before']}",
            "object", int(fields["script_pointer"]),
        ))
    return values


def _preserved_and_added_root_audit(
    baseline: bytes,
    output: bytes,
    cases: Mapping[str, Any],
) -> dict[str, Any]:
    before, before_counts = _root_inventory(baseline)
    after, after_counts = _root_inventory(output)
    if dict(after_counts) != EXPECTED_ROOT_COUNTS:
        _fail(f"Stage58 contactable root inventory drift: {dict(after_counts)}")
    before_set = {_root_key(root) for root in before}
    after_set = {_root_key(root) for root in after}
    removed = sorted(before_set - after_set)
    added = after_set - before_set
    expected = _expected_added_roots(output, cases)
    if removed or added != expected:
        _fail(
            "既存root保持/追加root集合不一致: "
            f"removed={removed[:4]} added={sorted(added)[:12]} "
            f"expected={sorted(expected)}"
        )
    walker = ScriptWalker(RomImage("Stage58", output))
    for root in after:
        walker.add_root(root)
    graph = walker.walk()
    if graph["diagnostics"]:
        _fail(
            "Stage58 event CFG diagnostics残存: "
            + json.dumps(graph["diagnostics"][:8], ensure_ascii=False,
                         sort_keys=True)
        )
    return {
        "status": "PASS",
        "physical_maps": 678,
        "root_count_before": len(before),
        "root_count_after": len(after),
        "root_counts_before": dict(before_counts),
        "root_counts_after": dict(after_counts),
        "preserved_root_count": len(before_set),
        "added_root_count": len(added),
        "removed_root_count": 0,
        "unique_root_address_count": graph["unique_root_address_count"],
        "visited_script_count": graph["visited_script_count"],
        "diagnostic_count": 0,
    }


def _match_object(state: Mapping[str, Any], expected: Mapping[str, Any],
                  label: str) -> dict[str, Any]:
    matches = [
        _object_fields(raw) for raw in state["objects"]
        if _object_fields(raw)["local_id"] == int(expected["local_id"])
    ]
    if len(matches) != 1:
        _fail(f"{label} local IDが一意ではありません")
    actual = matches[0]
    required = {
        "local_id": int(expected["local_id"]),
        "graphics_id": int(expected["graphics_id"]),
        "x": int(expected["x"]),
        "y": int(expected["y"]),
        "script_pointer": int(expected["script"]),
    }
    if any(int(actual[key]) != value for key, value in required.items()):
        _fail(f"{label} object不一致: actual={actual} expected={required}")
    return actual


def _map_event_audit(baseline: bytes, output: bytes,
                     cases: Mapping[str, Any]) -> dict[str, Any]:
    hub_case = cases["codex_hub"]
    group, number = int(hub_case["group"]), int(hub_case["map"])
    before = _stage_map_state(baseline, group, number)
    after = _stage_map_state(output, group, number)
    if (int(before["counts"]["objects"]), int(after["counts"]["objects"])) \
            != (10, int(hub_case["object_count"])):
        _fail("Codex hub object count不一致")
    if after["objects"][:10] != before["objects"] \
            or any(after[key] != before[key]
                   for key in ("warps_hex", "coords_hex", "bg_hex")):
        _fail("Codex hubの既存object/warp/coord/bgが変化しています")
    hub_objects = {
        name: _match_object(after, hub_case[name], f"Codex {name}")
        for name in ("npc", "pc", "healer", "mart")
    }
    pc = int(hub_case["pc"]["script"]) - ROM_BASE
    pc_signature = bytes.fromhex("258701210d80020006018a50190869")
    storage = int(hub_case["pc"]["storage_script"]) - ROM_BASE
    storage_body = output[storage:storage + 48]
    storage_pattern = bytes((0x25, int(hub_case["pc"]["special"]), 0, 0x27))
    if output[pc:pc + len(pc_signature)] != pc_signature \
            or int(hub_case["pc"]["entry_special"]) != 0x187 \
            or storage_pattern not in storage_body:
        _fail("Codex PCがstock menu→Storage→waitstate導線ではありません")
    healer = int(hub_case["healer"]["script"]) - ROM_BASE
    expected_heal_prefix = bytes((0x6A, 0x5A, 0x25)) \
        + struct.pack("<H", int(hub_case["healer"]["special"]))
    if output[healer:healer + len(expected_heal_prefix)] != expected_heal_prefix:
        _fail("Codex healerが標準HealPlayerParty specialではありません")
    mart = int(hub_case["mart"]["script"]) - ROM_BASE
    if output[mart:mart + 4] != bytes((0x6A, 0x5A, 0x0F, 0x00)) \
            or output[mart + 10] != 0x86 \
            or output[mart + 15:mart + 17] != bytes((0x6C, 0x02)):
        _fail("Codex money mart lifecycle不一致")
    mart_items_pointer = struct.unpack_from("<I", output, mart + 11)[0]
    item_offset = mart_items_pointer - ROM_BASE
    item_count = len(hub_case["mart"]["items"])
    actual_items = list(struct.unpack_from(
        f"<{item_count + 1}H", output, item_offset,
    ))
    if actual_items != [int(value) for value in hub_case["mart"]["items"]] + [0]:
        _fail("Codex money mart item list不一致")
    if output[
        GET_POCKET_BY_ITEM_ID_OFFSET:
        GET_POCKET_BY_ITEM_ID_OFFSET + len(GET_POCKET_BY_ITEM_ID_EXPECTED)
    ] != GET_POCKET_BY_ITEM_ID_EXPECTED:
        _fail("stock GetPocketByItemId ABI drift（item row +22）")
    if output[
        BUY_MENU_TRY_MAKE_PURCHASE_OFFSET:
        BUY_MENU_TRY_MAKE_PURCHASE_OFFSET + len(BUY_MENU_TRY_MAKE_PURCHASE_EXPECTED)
    ] != BUY_MENU_TRY_MAKE_PURCHASE_EXPECTED:
        _fail("stock Mart購入transaction owner drift")

    thin_rows: list[dict[str, Any]] = []
    thin_get_targets: set[int] = set()
    thin_set_targets: set[int] = set()
    for row in cases["thin_events"]:
        coordinate = (int(row["group"]), int(row["map"]))
        old = _stage_map_state(baseline, *coordinate)
        new = _stage_map_state(output, *coordinate)
        before_count = int(row["object_count_before"])
        after_count = int(row["object_count_after"])
        if (len(old["objects"]), len(new["objects"])) != (before_count, after_count) \
                or new["objects"][:before_count] != old["objects"] \
                or any(new[key] != old[key]
                       for key in ("warps_hex", "coords_hex", "bg_hex")):
            _fail(f"thin event既存event保持不一致: {row['key']}")
        fields = _match_object(new, {
            "local_id": row["local_id"], "graphics_id": 55,
            "x": row["x"], "y": row["y"],
            "script": _object_fields(new["objects"][-1])["script_pointer"],
        }, f"thin event {row['key']}")
        script = int(fields["script_pointer"]) - ROM_BASE
        flag = int(row["flag"])
        item = int(row["item_id"])
        quantity = int(row["quantity"])
        prefix = bytes((0x6A, 0x5A, 0x1A, 0x00, 0x80)) + struct.pack("<H", flag)
        add_pattern = bytes((0x44,)) + struct.pack("<HH", item, quantity) \
            + bytes((0x21,)) + struct.pack("<HH", 0x800D, 0)
        set_pattern = bytes((0x1A, 0x00, 0x80)) + struct.pack("<H", flag)
        body = output[script:script + 70]
        get_target = struct.unpack_from("<I", body, 8)[0]
        already_target = struct.unpack_from("<I", body, 19)[0]
        full_target = struct.unpack_from("<I", body, 43)[0]
        set_target = struct.unpack_from("<I", body, 53)[0]
        end_target = struct.unpack_from("<I", body, 66)[0]
        branch_targets = (already_target, full_target, end_target)
        if not body.startswith(prefix) \
                or body[7] != 0x23 \
                or body[12:19] != bytes((0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01)) \
                or body[23:31] != bytes((0x0F, 0x00)) + body[25:29] + bytes((0x09, 0x04)) \
                or body[31:41] != add_pattern \
                or body[41:43] != bytes((0x06, 0x01)) \
                or body[47:52] != set_pattern \
                or body[52] != 0x23 \
                or body[57:65] != bytes((0x0F, 0x00)) + body[59:63] + bytes((0x09, 0x04)) \
                or body[65] != 0x05 \
                or get_target & 1 != 1 or set_target & 1 != 1 \
                or not ROM_BASE <= (get_target & ~1) < ROM_BASE + ROM_SIZE \
                or not ROM_BASE <= (set_target & ~1) < ROM_BASE + ROM_SIZE \
                or len(set(branch_targets)) != 3 \
                or any(not ROM_BASE <= target < ROM_BASE + ROM_SIZE
                       for target in branch_targets) \
                or output[end_target - ROM_BASE:end_target - ROM_BASE + 2] \
                    != bytes((0x6C, 0x02)):
            _fail(f"thin event transaction順序不一致: {row['key']}")
        thin_get_targets.add(get_target & ~1)
        thin_set_targets.add(set_target & ~1)
        thin_rows.append({
            "key": row["key"], "group": coordinate[0], "map": coordinate[1],
            "local_id": int(row["local_id"]), "script": int(fields["script_pointer"]),
            "native_flag_get_before_additem": True,
            "native_flag_set_after_additem_success": True,
            "quest_log_safe_expanded_flag_owner": True,
            "conditional_branch_targets_exact": True,
            "bag_full_preserves_flag": True,
        })
    if len(thin_get_targets) != 1 or len(thin_set_targets) != 1:
        _fail("thin event native flag ownerが単一ではありません")
    thin_runtime_rows = []
    for kind, targets, expected in (
        ("get", thin_get_targets, THIN_FLAG_GET_EXPECTED),
        ("set", thin_set_targets, THIN_FLAG_SET_EXPECTED),
    ):
        address = next(iter(targets))
        offset = address - ROM_BASE
        if address & 3 or offset < 0 or offset + len(expected) > len(output):
            _fail(f"thin event native {kind} runtime配置不一致")
        if output[offset:offset + len(expected)] != expected:
            _fail(f"thin event native {kind} runtime exact byte不一致")
        thin_runtime_rows.append({
            "kind": kind,
            "address": address,
            "size": len(expected),
            "sha256": _sha(expected),
            "exact_bytes": True,
        })
    return {
        "status": "PASS",
        "codex_hub": {
            "group": group, "map": number,
            "object_count_before": 10,
            "object_count_after": int(after["counts"]["objects"]),
            "objects": hub_objects,
            "existing_objects_preserved": True,
            "warps_coords_bg_preserved": True,
            "pc_waitstate_declared": True,
            "pc_field_return_requires_mgba": True,
            "pc_stock_menu_lifecycle": True,
            "healer_standard_special": True,
            "normal_money_mart": True,
            "mart_item_count": item_count,
            "mart_item_pocket_field_offset": 22,
            "mart_add_before_money_debit": True,
            "mart_bag_full_no_debit_requires_mgba": True,
        },
        "thin_events": thin_rows,
        "thin_event_count": len(thin_rows),
        "thin_flag_owner": {
            "status": "PASS",
            "single_native_get_owner": True,
            "single_native_set_owner": True,
            "native_runtime_exact": True,
            "getter_result_address": 0x02037004,
            "setter_read_modify_write": True,
            "runtime_rows": thin_runtime_rows,
        },
    }


def _codex_result_surface(
    raw: bytes,
    baseline: bytes,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Codex勝敗終了hookを生成器と独立にROM実体から監査する。"""
    evidence = metadata.get("codex_result_compat")
    if not isinstance(evidence, Mapping):
        _fail("Codex result compatibility evidence不足")
    if (
        evidence.get("status") != "PASS"
        or int(evidence.get("end_turn_function_table", -1))
            != CODEX_RESULT_CONTRACT["table"]
        or int(evidence.get("inherited_return_to_field_adapter", -1))
            != CODEX_RESULT_CONTRACT["return_to_field"]
        or int(evidence.get("nonpunitive_result_script", -1))
            != CODEX_RESULT_CONTRACT["result_script"]
        or evidence.get("strategy")
            != ("CODEX_TRANSACTION_WIN_LOSS_DRAW_CLEAR_TOWER_"
                "OVERRIDE_PICKUP_END2_CONTROLLER_INDEPENDENT_"
                "PARTIAL_FAIL_CLOSED")
        or evidence.get("non_codex_delegates_preserved") is not True
        or evidence.get("controller_disconnect_safe") is not True
        or evidence.get("owned_result_kinds") != ["win", "loss", "draw"]
        or evidence.get("reward_result_taxonomy")
            != {"win": 1, "loss": 2, "draw": 3, "forfeit": 4}
        or evidence.get("result_guard")
            != ("MAGIC_INVERSE_ACTIVE_BOTH_SELECTIONS_"
                "FIELD_COMPLETION_PENDING_TRAINER_OPPONENT_745")
        or evidence.get("return_guard") != "MAGIC_INVERSE_ACTIVE"
        or evidence.get("partial_legacy_hazard_fail_closed") is not True
        or evidence.get("partial_legacy_hazard_action")
            != "STOCK_RESULT_WITHOUT_STAGE47_DELEGATE"
        or int(evidence.get("new_ram_or_save_owner_count", -1)) != 0
    ):
        _fail("Codex result compatibility contract不一致")

    runtime = metadata.get("runtime")
    if not isinstance(runtime, Mapping):
        _fail("Codex result runtime evidence不足")
    adapter = runtime.get("qol_item_adapter")
    if not isinstance(adapter, Mapping):
        _fail("Codex result adapter runtime evidence不足")
    load = int(adapter.get("load_address", -1))
    size = int(adapter.get("size", -1))
    offset = load - ROM_BASE
    if load & 3 or size <= 0 or offset < 0 or offset + size > len(raw):
        _fail("Codex result adapter runtime span不正")
    adapter_raw = raw[offset:offset + size]
    if _sha(adapter_raw) != str(adapter.get("sha256", "")):
        _fail("Codex result adapter runtime SHA-256不一致")

    symbols = adapter.get("symbols")
    symbol_sizes = adapter.get("symbol_sizes")
    if not isinstance(symbols, Mapping) or not isinstance(symbol_sizes, Mapping):
        _fail("Codex result adapter symbol evidence不足")
    expected_rows = {
        "win": (
            CODEX_RESULT_CONTRACT["win_site"],
            CODEX_RESULT_CONTRACT["win_inherited"],
            "Stage58QolItemAdapter_CodexBattleWonAdapter",
        ),
        "loss": (
            CODEX_RESULT_CONTRACT["loss_site"],
            CODEX_RESULT_CONTRACT["loss_inherited"],
            "Stage58QolItemAdapter_CodexBattleLostAdapter",
        ),
        "draw": (
            CODEX_RESULT_CONTRACT["draw_site"],
            CODEX_RESULT_CONTRACT["draw_inherited"],
            "Stage58QolItemAdapter_CodexBattleLostAdapter",
        ),
    }
    rows = evidence.get("rows")
    if not isinstance(rows, list) or len(rows) != len(expected_rows):
        _fail("Codex result adapter row数不一致")
    evidence_sizes = evidence.get("adapter_symbol_sizes")
    if not isinstance(evidence_sizes, Mapping):
        _fail("Codex result adapter symbol size evidence不足")
    checked_rows = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            _fail("Codex result adapter row形式不一致")
        kind = str(row.get("kind", ""))
        if kind in seen or kind not in expected_rows:
            _fail("Codex result adapter kind集合不一致")
        seen.add(kind)
        site, inherited, symbol = expected_rows[kind]
        replacement = int(row.get("replacement", -1))
        target = int(symbols.get(symbol, -1))
        target_size = int(symbol_sizes.get(symbol, -1))
        site_offset = site - ROM_BASE
        if (
            int(row.get("site", -1)) != site
            or int(row.get("expected", -1)) != inherited
            or struct.unpack_from("<I", baseline, site_offset)[0] != inherited
            or struct.unpack_from("<I", raw, site_offset)[0] != replacement
            or replacement != (target | 1)
            or replacement & 1 != 1
            or target_size <= 0
            or not load <= target < target + target_size <= load + size
            or int(evidence_sizes.get(symbol, -1)) != target_size
        ):
            _fail(f"Codex result {kind} adapter配線不一致")
        checked_rows.append({
            "kind": kind,
            "site": site,
            "inherited": inherited,
            "replacement": replacement,
            "symbol": symbol,
            "symbol_size": target_size,
            "thumb": True,
        })
    if seen != set(expected_rows):
        _fail("Codex result adapter kind不足")
    return_symbol = "Stage58QolItemAdapter_CodexReturnToFieldAdapter"
    return_target = int(symbols.get(return_symbol, -1))
    return_size = int(symbol_sizes.get(return_symbol, -1))
    if (
        int(evidence.get("return_to_field_adapter", -1))
            != (return_target | 1)
        or return_size <= 0
        or not load <= return_target < return_target + return_size <= load + size
        or int(evidence_sizes.get(return_symbol, -1)) != return_size
        or struct.pack("<I", return_target | 1) not in adapter_raw
    ):
        _fail("Codex result return-to-field adapter配線不一致")
    missing_literals = [
        value for value in CODEX_RESULT_REQUIRED_LITERALS
        if struct.pack("<I", value) not in adapter_raw
    ]
    if missing_literals:
        _fail(
            "Codex result adapter必須literal不足: "
            + ",".join(f"0x{value:08X}" for value in missing_literals)
        )
    checked_functions = []
    for symbol, (relative, expected_size, expected_sha) in \
            CODEX_RESULT_FUNCTION_CONTRACT.items():
        address = int(symbols.get(symbol, -1))
        symbol_size = int(symbol_sizes.get(symbol, -1))
        start = address - ROM_BASE
        body = raw[start:start + symbol_size]
        if (
            address != load + relative
            or symbol_size != expected_size
            or start < 0
            or start + symbol_size > len(raw)
            or _sha(body) != expected_sha
        ):
            _fail(f"Codex result {symbol} 命令契約不一致")
        checked_functions.append({
            "symbol": symbol,
            "address": address,
            "size": symbol_size,
            "sha256": expected_sha,
        })
    controller_literal = struct.pack("<I", 0x0203FA2F)
    if any(
        controller_literal in raw[
            int(symbols[symbol]) - ROM_BASE:
            int(symbols[symbol]) - ROM_BASE + int(symbol_sizes[symbol])
        ]
        for symbol in CODEX_RESULT_FUNCTION_CONTRACT
    ):
        _fail("Codex result ownerにvolatile controller guardが再混入")
    for address, expected in CODEX_RESULT_INHERITED_EXACT:
        start = address - ROM_BASE
        if (
            raw[start:start + len(expected)] != expected
            or baseline[start:start + len(expected)] != expected
        ):
            _fail(f"Codex inherited field/result surface不一致: 0x{address:08X}")
    checked_legacy_functions = []
    for name, (address, function_size, baseline_sha, stage58_sha) in \
            CODEX_RESULT_LEGACY_FUNCTION_CONTRACT.items():
        start = address - ROM_BASE
        baseline_body = baseline[start:start + function_size]
        stage58_body = raw[start:start + function_size]
        if (
            len(baseline_body) != function_size
            or len(stage58_body) != function_size
            or _sha(baseline_body) != baseline_sha
            or _sha(stage58_body) != stage58_sha
        ):
            _fail(f"Codex legacy {name} whole-function契約不一致")
        checked_legacy_functions.append({
            "name": name, "address": address, "size": function_size,
            "baseline_sha256": baseline_sha, "stage58_sha256": stage58_sha,
        })
    reward = metadata.get("codex_reward_result_kind")
    reward_symbol = "Stage58QolItemAdapter_CodexRewardResultKind"
    reward_target = int(symbols.get(reward_symbol, -1))
    reward_site = 0x093D20B8
    reward_offset = reward_site - ROM_BASE
    reward_size = 24
    inherited_mapping = bytes.fromhex(
        "124b1a787f231a407b3b052a03d0104b1b881b061b0eab75"
    )
    replacement = raw[reward_offset:reward_offset + reward_size]
    first, second = struct.unpack_from("<HH", replacement)
    delta = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
    if delta & (1 << 22):
        delta -= 1 << 23
    decoded_target = reward_site + 4 + delta
    if (
        not isinstance(reward, Mapping)
        or reward.get("status") != "PASS"
        or int(reward.get("inherited_after_battle_adapter", -1))
            != 0x093D2075
        or int(reward.get("mapping_patch_site", -1)) != reward_site
        or int(reward.get("mapping_patch_size", -1)) != reward_size
        or int(reward.get("mapping_function", -1)) != (reward_target | 1)
        or int(reward.get("mapping_function_size", -1))
            != int(symbol_sizes.get(reward_symbol, -1))
        or reward.get("taxonomy")
            != {"win": 1, "loss": 2, "draw": 3, "forfeit": 4}
        or reward.get("finalized_and_persisted_by_inherited_owner_after_mapping")
            is not True
        or int(reward.get("new_ram_or_save_owner_count", -1)) != 0
        or baseline[reward_offset:reward_offset + reward_size]
            != inherited_mapping
        or (first & 0xF800) != 0xF000
        or (second & 0xF800) != 0xF800
        or decoded_target != reward_target
        or replacement[4:] != struct.pack("<H", 0x75A8) + b"\xC0\x46" * 9
        or _sha(inherited_mapping) != str(reward.get("expected_sha256", ""))
        or _sha(replacement) != str(reward.get("replacement_sha256", ""))
        or raw[reward_offset + reward_size:reward_offset + reward_size + 38]
            != baseline[
                reward_offset + reward_size:reward_offset + reward_size + 38
            ]
    ):
        _fail("Codex reward result-kind mapping/finalize/persist契約不一致")
    return {
        "status": "PASS",
        "table": CODEX_RESULT_CONTRACT["table"],
        "rows": checked_rows,
        "adapter_span": {"address": load, "size": size},
        "adapter_sha256": _sha(adapter_raw),
        "required_literal_count": len(CODEX_RESULT_REQUIRED_LITERALS),
        "exact_function_count": len(checked_functions),
        "exact_functions": checked_functions,
        "inherited_exact_surface_count": len(CODEX_RESULT_INHERITED_EXACT),
        "legacy_exact_function_count": len(checked_legacy_functions),
        "legacy_exact_functions": checked_legacy_functions,
        "reward_result_taxonomy": reward["taxonomy"],
        "reward_mapping_before_finalize_persist": True,
        "runtime_state_guarded": True,
        "controller_disconnect_safe": True,
        "win_loss_draw_owned": True,
        "tower_text_owner_bypassed_for_codex_only": True,
        "non_codex_delegates_preserved": True,
        "new_ram_or_save_owner_count": 0,
    }


def _saveblock_key_rotation_stock_surface(
    raw: bytes,
    baseline: bytes,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = metadata.get("saveblock_key_rotation_stock_contract")
    site_offset = SAVEBLOCK_KEY_ROTATION_CALL_SITE - ROM_BASE
    bag_offset = SAVEBLOCK_KEY_ROTATION_STOCK_BAG_SITE - ROM_BASE
    veneer_offset = SAVEBLOCK_KEY_ROTATION_VENEER - ROM_BASE
    callback_offset = SAVEBLOCK_CALLBACK_RESTORE_SITE - ROM_BASE
    if (
        not isinstance(evidence, Mapping)
        or evidence.get("status") != "PASS"
        or evidence.get("policy") != "preserve_stock_no_runtime_rebind"
        or baseline[site_offset:site_offset + 4]
            != SAVEBLOCK_KEY_ROTATION_ORIGINAL_CALL
        or raw[site_offset:site_offset + 4]
            != SAVEBLOCK_KEY_ROTATION_ORIGINAL_CALL
        or baseline[bag_offset:bag_offset + 4]
            != SAVEBLOCK_KEY_ROTATION_STOCK_BAG_CALL
        or raw[bag_offset:bag_offset + 4]
            != SAVEBLOCK_KEY_ROTATION_STOCK_BAG_CALL
        or baseline[callback_offset:callback_offset + 8]
            != SAVEBLOCK_CALLBACK_RESTORE_EXPECTED
        or raw[callback_offset:callback_offset + 8]
            != SAVEBLOCK_CALLBACK_RESTORE_EXPECTED
        or baseline[veneer_offset:veneer_offset + 8] != b"\xFF" * 8
        or raw[veneer_offset:veneer_offset + 8] != b"\xFF" * 8
        or int(evidence.get("apply_all_call_site", -1))
            != SAVEBLOCK_KEY_ROTATION_CALL_SITE
        or int(evidence.get("bag_encryption_call_site", -1))
            != SAVEBLOCK_KEY_ROTATION_STOCK_BAG_SITE
        or int(evidence.get("callback_restore_site", -1))
            != SAVEBLOCK_CALLBACK_RESTORE_SITE
        or evidence.get("stock_callback_restore_preserved") is not True
        or evidence.get("stock_apply_all_preserved") is not True
        or evidence.get("stock_bag_child_preserved") is not True
        or int(evidence.get("set_bag_pockets_pointers", -1)) != 0x0809984D
        or int(evidence.get("original_apply_new_encryption", -1))
            != 0x0804BD5D
        or int(evidence.get("original_bag_encryption", -1)) != 0x08099841
        or int(evidence.get("save_block1_pointer", -1)) != 0x03005048
        or int(evidence.get("save_block2_pointer", -1)) != 0x0300504C
        or int(evidence.get("bag_pockets", -1)) != 0x020397D8
        or int(evidence.get("descriptor_stride", -1)) != 8
        or int(evidence.get("descriptor_count", -1)) != 5
        or evidence.get("bag_pocket_descriptors") != [
            {"name": "items", "save1_offset": 0x0310, "capacity": 42},
            {"name": "key_items", "save1_offset": 0x03B8,
             "capacity": 30},
            {"name": "poke_balls", "save1_offset": 0x0430,
             "capacity": 13},
            {"name": "tm_case", "save1_offset": 0x0464,
             "capacity": 58},
            {"name": "berry_pouch", "save1_offset": 0x054C,
             "capacity": 43},
        ]
        or evidence.get("call_order")
            != ["SetSaveBlocksPointersOwnsBagRebind",
                "RestoreSaveBlockCopies",
                "ApplyNewEncryptionKeyToAllEncryptedData",
                "StoreNewEncryptionKey"]
        or int(evidence.get("additional_runtime_rebind_count", -1)) != 0
        or evidence.get("host_rebind_after_field_return_forbidden") is not True
        or evidence.get("all_stock_encrypted_fields_preserved") is not True
        or int(evidence.get("new_ram_or_save_owner_count", -1)) != 0
    ):
        _fail("SaveBlock key rotation stock exact契約不一致")
    veneer_evidence = evidence.get("veneer", {})
    if (
        int(veneer_evidence.get("address", -1))
            != SAVEBLOCK_KEY_ROTATION_VENEER
        or int(veneer_evidence.get("size", -1)) != 8
        or int(veneer_evidence.get(
            "preexisting_pointer_reference_count", -1)) != 0
        or int(veneer_evidence.get("prior_allocation_overlap_count", -1)) != 0
        or veneer_evidence.get("remains_unallocated") is not True
    ):
        _fail("SaveBlock key rotation unused veneer exact契約不一致")
    return {
        "status": "PASS",
        "call_site": SAVEBLOCK_KEY_ROTATION_CALL_SITE,
        "stock_apply_all_call_sha256": _sha(SAVEBLOCK_KEY_ROTATION_ORIGINAL_CALL),
        "stock_bag_call_site": SAVEBLOCK_KEY_ROTATION_STOCK_BAG_SITE,
        "stock_bag_call_sha256": _sha(SAVEBLOCK_KEY_ROTATION_STOCK_BAG_CALL),
        "callback_restore_site": SAVEBLOCK_CALLBACK_RESTORE_SITE,
        "callback_restore_sha256": _sha(SAVEBLOCK_CALLBACK_RESTORE_EXPECTED),
        "stock_bag_child_preserved": True,
        "veneer_address": SAVEBLOCK_KEY_ROTATION_VENEER,
        "veneer_sha256": _sha(b"\xFF" * 8),
        "additional_runtime_rebind_count": 0,
        "call_order": list(evidence["call_order"]),
        "new_ram_or_save_owner_count": 0,
    }


def _thumb_bl(source: int, target: int) -> bytes:
    delta = target - (source + 4)
    if delta & 1 or not -(1 << 22) <= delta < (1 << 22):
        _fail("Stage58 exact Thumb BL range/alignment不一致")
    return struct.pack(
        "<HH", 0xF000 | ((delta >> 12) & 0x07FF),
        0xF800 | ((delta >> 1) & 0x07FF),
    )


def _codex_save_layout_surface(
    raw: bytes,
    baseline: bytes,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = metadata.get("codex_save_layout_repair", {})
    runtime = metadata.get("runtime", {}).get("qol_item_adapter", {})
    symbols = runtime.get("symbols", {})
    sizes = runtime.get("symbol_sizes", {})
    if (
        evidence.get("status") != "PASS"
        or evidence.get("strategy")
            != "PATCH_SIX_STAGE44_SITES_TO_VEGA_MIRROR_ADAPTERS"
        or int(evidence.get("bitmap_size", -1)) != 52
        or int(evidence.get("patch_count", -1)) != 6
        or int(evidence.get("adapter_callsite_count", -1)) != 3
        or int(evidence.get("new_ram_or_save_owner_count", -1)) != 0
        or evidence.get("bag_snapshot_restore_removed") is not True
        or evidence.get("existing_public_state_offset_preserved") is not True
        or evidence.get("snapshot_restore_mirrors") != [
            "save1_seen_primary", "save1_seen_secondary", "save2_seen",
            "save2_unown_spinda_personalities",
        ]
        or evidence.get("hash_mirrors") != [
            "save1_seen_primary", "save1_seen_secondary", "save2_owned",
            "save2_seen", "save2_pokedex_header",
        ]
    ):
        _fail("Codex Vega save layout metadata契約不一致")
    buffers = evidence.get("snapshot_buffers", {})
    if (
        int(str(buffers.get("primary_address")), 0) != 0x0203FDA6
        or int(buffers.get("primary_size", -1)) != 150
        or int(str(buffers.get("spill_address")), 0) != 0x0203FF3C
        or int(buffers.get("spill_size", -1)) != 16
        or (int(buffers.get("used", -1)),
            int(buffers.get("capacity", -1)),
            int(buffers.get("unused", -1))) != (164, 166, 2)
    ):
        _fail("Codex Vega split snapshot buffer契約不一致")

    checked_functions: list[dict[str, Any]] = []
    targets: dict[str, int] = {}
    key_by_symbol = {
        "Stage58QolItemAdapter_CodexSnapshotSeenMirrors": "snapshot",
        "Stage58QolItemAdapter_CodexRestoreSeenMirrors": "restore",
        "Stage58QolItemAdapter_CodexContinueSeenHash": "hash",
    }
    for symbol, (address, size, digest) in \
            CODEX_SAVE_LAYOUT_FUNCTION_CONTRACT.items():
        actual_address = int(symbols.get(symbol, -1))
        actual_size = int(sizes.get(symbol, -1))
        body = raw[address - ROM_BASE:address - ROM_BASE + size]
        if (actual_address != address or actual_size != size
                or len(body) != size or _sha(body) != digest):
            _fail(f"Codex Vega save layout function exact不一致: {symbol}")
        targets[key_by_symbol[symbol]] = address
        checked_functions.append({
            "symbol": symbol, "address": address, "size": size,
            "sha256": digest,
        })

    evidence_rows = {
        str(row.get("key")): row for row in evidence.get("patches", [])
    }
    checked_patches: list[dict[str, Any]] = []
    for key, site, expected_hex, target_kind in CODEX_SAVE_LAYOUT_PATCH_CONTRACT:
        expected = bytes.fromhex(expected_hex)
        size = len(expected)
        if key == "snapshot_save1":
            replacement = (struct.pack("<H", 0x0020)
                           + _thumb_bl(site + 2, targets["snapshot"])
                           + struct.pack("<3H", 0x46C0, 0x46C0, 0x46C0))
        elif key == "restore_save1":
            replacement = (struct.pack("<HH", 0x0007, 0x0028)
                           + _thumb_bl(site + 4, targets["restore"])
                           + struct.pack("<5H", *([0x46C0] * 5)))
        elif key == "hash_save1":
            replacement = (struct.pack("<H", 0x0020)
                           + _thumb_bl(site + 2, targets["hash"])
                           + struct.pack("<H", 0x0004)
                           + struct.pack("<7H", *([0x46C0] * 7)))
        elif key == "hash_save2_legacy":
            replacement = struct.pack("<H", 0xE007) \
                + struct.pack("<8H", *([0x46C0] * 8))
        else:
            replacement = struct.pack(
                f"<{size // 2}H", *([0x46C0] * (size // 2))
            )
        offset = site - ROM_BASE
        row = evidence_rows.get(key, {})
        expected_target = None if target_kind in (None, "skip") \
            else targets[str(target_kind)] | 1
        if (
            baseline[offset:offset + size] != expected
            or raw[offset:offset + size] != replacement
            or int(row.get("site", -1)) != site
            or int(row.get("size", -1)) != size
            or row.get("expected") != expected.hex()
            or row.get("replacement") != replacement.hex()
            or row.get("target") != expected_target
        ):
            _fail(f"Codex Vega save layout patch exact不一致: {key}")
        checked_patches.append({
            "key": key, "site": site, "size": size,
            "replacement_sha256": _sha(replacement),
        })
    return {
        "status": "PASS",
        "function_count": len(checked_functions),
        "functions": checked_functions,
        "patch_count": len(checked_patches),
        "patches": checked_patches,
        "snapshot_used_bytes": 164,
        "snapshot_capacity_bytes": 166,
        "bag_snapshot_restore_removed": True,
        "seen_and_personality_restore": True,
        "owned_and_header_hash_guarded": True,
        "new_ram_or_save_owner_count": 0,
    }


def _field_item_surface(raw: bytes, maps: Mapping[str, Any]) -> dict[str, Any]:
    """Stage50で確定した全field item scriptをexact byteで継承確認する。"""
    report = _read_document(ROOT / STAGE50_ITEM_REPORT, "Stage50 item report")
    stage50 = (ROOT / STAGE50_ROM).read_bytes()
    expected_hash = str(report.get("output", {}).get("sha256", ""))
    if len(stage50) != ROM_SIZE or _sha(stage50) != expected_hash:
        _fail("Stage50 field item正本identity不一致")
    payload = report.get("payload", {})
    base = int(payload.get("offset", -1))
    scripts = report.get("interaction_plan", {}).get("scripts", {})
    if base < 0 or not isinstance(scripts, dict):
        _fail("Stage50 field item script inventory不足")
    rows = {
        str(label): value for label, value in scripts.items()
        if str(label).startswith(("script_item::", "script_hidden::"))
    }
    main_rows = {
        label: value for label, value in rows.items()
        if not label.endswith(("::already", "::full", "::end"))
    }
    item_audit = report.get("item_audit", {})
    expected_main = int(item_audit.get("object_transactions", -1)) \
        + int(item_audit.get("hidden_transactions", -1))
    if len(rows) != 1000 or len(main_rows) != expected_main \
            or expected_main != 250:
        _fail(
            "Stage50 field item inventory件数不一致: "
            f"scripts={len(rows)} transactions={len(main_rows)}"
        )
    checked_bytes = 0
    for label, row in rows.items():
        offset = base + int(row["offset"])
        size = int(row["size"])
        if size <= 0 or offset < 0 or offset + size > ROM_SIZE:
            _fail(f"field item script span不正: {label}")
        expected = stage50[offset:offset + size]
        if raw[offset:offset + size] != expected:
            _fail(f"field item script byte drift: {label}")
        checked_bytes += size
    return {
        "status": "PASS",
        "inherited_transaction_count": expected_main,
        "inherited_script_segment_count": len(rows),
        "inherited_script_bytes_checked": checked_bytes,
        "new_atomic_reward_transactions": int(maps["thin_event_count"]),
        "total_transaction_count": expected_main
            + int(maps["thin_event_count"]),
        "inherited_checkflag_additem_setflag_order": True,
        "new_native_get_additem_native_set_order": True,
        "bag_full_preserves_flag": True,
        "already_collected_path": True,
        "inherited_object_removed_after_success": True,
        "new_objects_remain_with_collected_flag_path": True,
    }


def _wild_surface(raw: bytes, metadata: Mapping[str, Any]) -> dict[str, Any]:
    inventory = _read_document(
        ROOT / "reports/generated/id_inventory.json", "map inventory",
    )
    wild = _wild_audit(raw, inventory["map_contract"]["group_sizes"])
    if wild["mode_tables"] != EXPECTED_MODE_TABLES:
        _fail(f"Stage58 wild mode table数不一致: {wild['mode_tables']}")
    balance = metadata["world_balance"]
    plan_audit = audit_world_balance_plan(balance)
    audit = balance["audit"]
    zero_keys = (
        "duplicate_physical_header_count",
        "method_misplacement_count",
        "zero_weight_native_inclusion_count",
        "event_native_inclusion_count",
        "egg_native_inclusion_count",
        "fossil_native_inclusion_count",
        "thin_candidate_collision_or_event_conflict_count",
    )
    if any(int(audit[key]) for key in zero_keys):
        _fail("Stage58 world balance forbidden inclusionが残っています")
    native_slots = sum(
        int(wild["mode_tables"].get(mode, 0)) * WILD_SLOT_COUNTS[mode]
        for mode in WILD_SLOT_COUNTS
    )
    if native_slots != 2733:
        _fail(f"Stage58全wild slot数不一致: {native_slots}")
    for mode, probabilities in FIRERED_SLOT_PROBABILITIES.items():
        groups = balance["slot_probabilities"][mode]
        if groups != probabilities:
            _fail(f"Stage58 {mode} standard probability drift")
    return {
        "status": "PASS",
        "native_headers": int(wild["native_headers"]),
        "unique_coordinate_headers": int(wild["unique_coordinate_headers"]),
        "legacy_orphan_headers_classified": len(wild["legacy_orphan_headers"]),
        "mode_tables": wild["mode_tables"],
        "native_slots_checked": native_slots,
        "kanto_plan": plan_audit,
        "kanto_enabled_headers": int(audit["enabled_physical_header_count"]),
        "kanto_disabled_headers": int(audit["disabled_non_native_physical_header_count"]),
        "forbidden_native_inclusion_count": 0,
    }


def full_audit(raw: bytes, metadata: Mapping[str, Any],
               cases: Mapping[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    digest = _identity(raw, metadata, cases)
    baseline = (ROOT / STAGE57_ROM).read_bytes()
    stage57_metadata = _read_document(ROOT / STAGE57_METADATA, "Stage57 metadata")
    inherited_metadata = copy.deepcopy(stage57_metadata)
    inherited_metadata.setdefault("output", {})["sha256"] = digest
    inherited = stage57_quick_audit(raw, metadata=inherited_metadata)
    inherited.pop("elapsed_seconds", None)
    roots = _preserved_and_added_root_audit(baseline, raw, cases)
    maps = _map_event_audit(baseline, raw, cases)
    wild = _wild_surface(raw, metadata)
    codex_result = _codex_result_surface(raw, baseline, metadata)
    key_rotation = _saveblock_key_rotation_stock_surface(
        raw, baseline, metadata,
    )
    codex_save_layout = _codex_save_layout_surface(
        raw, baseline, metadata,
    )
    return {
        "status": "PASS",
        "rom_sha256": digest,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "inherited_stage57": inherited,
        "script_cfg": roots,
        "map_events": maps,
        "wild_surface": wild,
        "codex_result_surface": codex_result,
        "saveblock_key_rotation_stock_surface": key_rotation,
        "codex_save_layout_surface": codex_save_layout,
        "field_item_surface": _field_item_surface(raw, maps),
        "story_trainer_surface": inherited["checks"]["story_trainers"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, nargs="?", default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = (ROOT / args.rom).read_bytes() if not args.rom.is_absolute() \
            else args.rom.read_bytes()
        metadata_path = ROOT / args.metadata if not args.metadata.is_absolute() \
            else args.metadata
        cases_path = ROOT / args.cases if not args.cases.is_absolute() else args.cases
        result = {
            "schema_version": 1,
            "tool": "stage58_debug_suite",
            "task": TASK,
            "stage": STAGE,
            **full_audit(
                raw,
                _read_document(metadata_path, "Stage58 metadata"),
                _read_document(cases_path, "Stage58 cases"),
            ),
        }
        rendered = _stable(result)
        if args.output:
            output = ROOT / args.output if not args.output.is_absolute() else args.output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error,
            json.JSONDecodeError, Stage58DebugError,
            WorldBalanceError) as error:
        print(f"Stage58 debug full failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
