#!/usr/bin/env python3
"""Stage81: classified native move-PP references, without changing Stage80/baseline.

Five instruction-guarded literal sites are PP lookup consumers (stride 12).
The existing canonical table is ROM[0x1cc] == 0x090421f4; PP is byte 4.
No global replace or new move balancing is performed.  Only the empty-slot
and replacement consumers have learning UI E2E coverage in the companion suite.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
PARENT_PATH = "build/stages/80_modernization_runtime_boundary_repair.gba"
PARENT_SHA = "6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3"
CANDIDATE_SHA = "521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579"
ROM_SIZE = 33554432
OLD_PP = 0x08E0CBB4
CANONICAL_MOVES = 0x090421F4
CANONICAL_PP = CANONICAL_MOVES + 4
# (ROM file offset, guarded instruction offset, instruction bytes, consumer role)
SITES = ((69060, 69022, '311c1131208842001218920006481218281c2ef05efe02340136', 'trainer_custom_moves'), (69480, 69388, '2ef0b0fd311c1131208842001218920012481218281c2ef0a5fd02340136', 'trainer_custom_moves_with_item'), (254052, 254028, '1131308842001218920003481218381c01f0b2fd', 'give_move_to_box_mon_empty_slot'), (254220, 254190, '6846008842001218920004481218281c211c01f0', 'set_mon_move_slot_replacement'), (263636, 263552, '00684c300019008842001218920011481218381cfff76cfa023602340135', 'native_party_move_pp_initialization'))


def identity(data: bytes) -> dict:
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def patch_sites(data: bytes) -> bytes:
    """Instruction/preimage checked primitive; production entry also pins full ROM."""
    if len(data) != ROM_SIZE:
        raise ValueError("ROM size mismatch")
    if struct.unpack_from("<I", data, 0x1CC)[0] != CANONICAL_MOVES:
        raise ValueError("canonical move root mismatch")
    out = bytearray(data)
    for offset, code_offset, code_hex, role in SITES:
        code = bytes.fromhex(code_hex)
        if data[code_offset:code_offset + len(code)] != code:
            raise ValueError(f"instruction guard mismatch: {role}")
        if struct.unpack_from("<I", data, offset)[0] != OLD_PP:
            raise ValueError(f"PP literal preimage mismatch: {role}")
        struct.pack_into("<I", out, offset, CANONICAL_PP)
    return bytes(out)


def build(data: bytes) -> tuple[bytes, dict]:
    parent = identity(data)
    if parent != {"size": ROM_SIZE, "sha256": PARENT_SHA}:
        raise ValueError("fixed Stage80 parent identity mismatch")
    out = patch_sites(data)
    if identity(out) != {"size": ROM_SIZE, "sha256": CANDIDATE_SHA}:
        raise ValueError("deterministic Stage81 identity mismatch")
    allowed = {i for offset, *_ in SITES for i in range(offset, offset + 4)}
    # Compare contiguous unchanged ranges too; this is not a search-and-replace.
    last = 0
    for offset, *_ in sorted(SITES):
        if data[last:offset] != out[last:offset]:
            raise ValueError("change outside classified sites")
        last = offset + 4
    if data[last:] != out[last:]:
        raise ValueError("change outside classified sites")
    pp = out[CANONICAL_PP - 0x08000000 + 535 * 12]
    if pp != 20:
        raise ValueError("adopted Bug Bite PP is not 20")
    report = {
        "schema_version": 1, "stage": 81, "status": "CANDIDATE_BUILT",
        "parent": {"path": PARENT_PATH, **parent}, "candidate": identity(out),
        "canonical_move_table": f"0x{CANONICAL_MOVES:08X}",
        "canonical_pp": f"0x{CANONICAL_PP:08X}", "bug_bite_pp": pp,
        "patches": [{"rom_offset": f"0x{o:08X}", "consumer": role,
                     "before": f"0x{OLD_PP:08X}", "after": f"0x{CANONICAL_PP:08X}",
                     "instruction_offset": f"0x{c:08X}", "instruction_hex": h}
                    for o, c, h, role in SITES],
        "modified_bytes": sum(data[i] != out[i] for i in allowed),
        "active_baseline_changed": False, "current_stage79_candidate_changed": False,
        "full_p03_acceptance": False, "release_ready": False,
    }
    return out, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=ROOT / ".local/p03-native-pp-candidate")
    args = parser.parse_args()
    output = args.output_directory.absolute()
    output.resolve().relative_to((ROOT / ".local").resolve())
    if output.is_symlink():
        raise ValueError("symlink output forbidden")
    output.mkdir(parents=True, exist_ok=True)
    for name in ("candidate.gba", "candidate.json"):
        (output / name).unlink(missing_ok=True)
    parent = ROOT / PARENT_PATH
    if parent.is_symlink():
        raise ValueError("symlink parent forbidden")
    data = parent.read_bytes()
    candidate, report = build(data)
    (output / "candidate.gba").write_bytes(candidate)
    (output / "candidate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
