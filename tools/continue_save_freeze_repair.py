"""Stage50のARMv5専用BLX wrapperをGBA ARMv4T tail-callへ修正する。"""

from __future__ import annotations

import hashlib
import struct
from typing import Any, Mapping


GBA_ROM_BASE = 0x08000000
WILD_HOOK_OFFSET = 0x0006CFE8
PLAYER_AVATAR = 0x02036FAC
TRY_STANDARD_WILD_ENCOUNTER = 0x08082F9D

LEGACY_WRAPPER = (
    bytes.fromhex("10b504498978022902d1034b984710bd002010bd")
    + struct.pack("<II", PLAYER_AVATAR, TRY_STANDARD_WILD_ENCOUNTER)
)

# ARM7TDMI (ARMv4T)にはThumb BLX(register)がない。移動中は元関数へ
# tail-callし、元のcaller LRをそのまま保持する。方向転換中だけ0を返す。
ARMV4T_WRAPPER = (
    bytes.fromhex("04498978022901d1034b184700207047c046c046")
    + struct.pack("<II", PLAYER_AVATAR, TRY_STANDARD_WILD_ENCOUNTER)
)


class ContinueSaveFreezeRepairError(ValueError):
    """Stage50のwrapper契約またはROM identityが一致しない。"""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def repair_stage50_rom(stage50: bytes, metadata: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
    payload = metadata.get("payload")
    plan = metadata.get("interaction_plan")
    if not isinstance(payload, Mapping) or not isinstance(plan, Mapping):
        raise ContinueSaveFreezeRepairError("Stage50 metadata rootが不正です")
    labels = plan.get("labels")
    if not isinstance(labels, Mapping) or "runtime_moving_wild_encounter" not in labels:
        raise ContinueSaveFreezeRepairError("Stage50 wild wrapper labelがありません")
    wrapper_offset = int(payload["offset"]) + int(labels["runtime_moving_wild_encounter"])
    if stage50[wrapper_offset:wrapper_offset + len(LEGACY_WRAPPER)] != LEGACY_WRAPPER:
        raise ContinueSaveFreezeRepairError("Stage50 legacy BLX wrapperが一致しません")
    hook_target = struct.unpack_from("<I", stage50, WILD_HOOK_OFFSET + 4)[0]
    expected_target = (GBA_ROM_BASE + wrapper_offset) | 1
    if hook_target != expected_target:
        raise ContinueSaveFreezeRepairError("wild hook targetがwrapperと一致しません")
    output = bytearray(stage50)
    output[wrapper_offset:wrapper_offset + len(ARMV4T_WRAPPER)] = ARMV4T_WRAPPER
    changed = [index for index, (before, after) in enumerate(zip(stage50, output))
               if before != after]
    if not changed or any(index < wrapper_offset
                          or index >= wrapper_offset + len(ARMV4T_WRAPPER)
                          for index in changed):
        raise ContinueSaveFreezeRepairError("wrapper外に変更があります")
    audit = {
        "status": "PASS",
        "input_sha256": _sha(stage50),
        "output_sha256": _sha(bytes(output)),
        "wrapper_offset": wrapper_offset,
        "wrapper_address": GBA_ROM_BASE + wrapper_offset,
        "wrapper_size": len(ARMV4T_WRAPPER),
        "changed_bytes": len(changed),
        "outside_wrapper_changes": 0,
        "hook_target": hook_target,
        "legacy_blx_register_removed": struct.pack("<H", 0x4798) not in ARMV4T_WRAPPER,
        "armv4t_tail_call": True,
        "turning_returns_false": True,
    }
    return bytes(output), audit
