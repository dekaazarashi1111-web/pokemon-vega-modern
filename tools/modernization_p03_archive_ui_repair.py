#!/usr/bin/env python3
"""Stage82: preserve HOF gating and repair the native JP Move Memory list ABI.

Stage81 is reproduced by its existing exact-parent recipe. Historical source,
learnsets, Stage62 baseline and accepted evidence are never rewritten. This
recipe changes only six guarded byte spans in a new candidate, not user saves.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import modernization_p03_native_pp_repair as parent

ROOT = Path(__file__).resolve().parents[1]
PARENT_SHA = "521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579"
CANDIDATE_SHA = "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d"
ASM = "overlays/modernization_p03_archive_ui_repair/relearner_list.S"
ASM_SHA = "f01f83b0d583b2c8b3fd7961fa9911f80428d9c264c07a9f6b0de6ff83345082"
PAYLOAD_SHA = "26baa313b45d384a948a69f8067ca16f9db646700418e2fad81e36e62b520164"
PAYLOAD_SIZE = 220
ROM_SIZE = 33554432
LIST_SITE = 0x0E6088
LIST_SPAN = 0x134
LAYOUT = {"allocation": 0xDD0, "moves": 0xE8, "capacity": 40,
          "selected_party": 0x1E3, "selected_slot": 0x1E4,
          "items": 0x9F0, "item_stride": 8, "names": 0xB40, "name_stride": 16}
# name, ROM file offset, exact parent bytes, exact replacement bytes.
# The native name-span includes a 16-byte stride fix in the learned message.
SITES = (
    ('Stage75_MachineGateScript', 0x154B6EF,
     '210d800100',
     '0000000000'),
    ('Stage75_TutorGateScript', 0x154B70B,
     '210d800100',
     '0000000000'),
    ('native_allocation', 0xE5780,
     '9f20',
     'dd20'),
    ('native_list_builder', 0xE6088,
     'f0b5474680b483b0424f3968424c0819007864267043414d4019e8315df714f93968887639680c19207870434019e8315df70af90006000e804600253868807e854213da3e1c8d246400316808196a00e831891809880901314a891822f70cfc093401353068807e8542eedb294c2068294940180178642048432849401802216a4659f723f92748694622f7adfb2068817e90218d277f00c9194018224922f7ebfb2168887e013088760025012343449c4645450fda261c3c1c3068eb00011c2031c91802190a602430c0180560093401354545f1db0f4c2268eb00101c2030c018114901602432d218fe2010600f4a111c0f4868c868c168c868c12068203010606546958103b008bc9846f0bc01bc004700002caa0302e3010000e4410202c85304094c1c0202c45b3c08c05e00036c5c3c08',
     'f0b583b02b4804682b48205c642148432a49401800902100e831294b00f048f8282800d90020060001960130a0760025b4273f013f19b54219d26900e831615a0901204a8918380010220b78037001310130013af9d1ff23fb739f2000010019e90040180760456010370135e3e79f20000100190290e900401813490160fe21416000980221114a114b00f011f811481149062203680b6004300431013af9d10d490298086001980130888103b0f0bd1847c0462caa0302e3010000e4410202d1320408c8530409c45b3c084c1c020255f303086c5c3c08c05e0003c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046c046'),
    ('native_name_index', 0xE61F8,
     'd3009a188d235b00',
     '12011246b4231b01'),
    ('native_learned_name_stride', 0xE5DF4,
     'c900',
     '0901'),
 )


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_layout(layout: dict = LAYOUT) -> None:
    if any(type(value) is not int or value < 0 for value in layout.values()):
        raise ValueError("layout requires nonnegative exact integers")
    if layout != LAYOUT or layout["capacity"] != 40:
        raise ValueError("native scheduler ABI must not change")
    count = layout["capacity"] + 1
    ranges = [(layout["moves"], layout["moves"] + count * 2),
              (layout["selected_party"], layout["selected_slot"] + 1),
              (layout["items"], layout["items"] + count * layout["item_stride"]),
              (layout["names"], layout["names"] + count * layout["name_stride"])]
    for start, end in ranges:
        if not 0 <= start < end <= layout["allocation"]:
            raise ValueError("native list region exceeds allocation")
    for i, (start, end) in enumerate(ranges):
        for other_start, other_end in ranges[i + 1:]:
            if max(start, other_start) < min(end, other_end):
                raise ValueError("native list regions overlap")


def verify_assembly() -> dict:
    source = ROOT / ASM
    if source.is_symlink() or sha(source.read_bytes()) != ASM_SHA:
        raise ValueError("assembly source identity differs")
    tools = [shutil.which("arm-none-eabi-" + x) for x in ("as", "ld", "objcopy")]
    if not all(tools):
        raise ValueError("pinned ARM assembler/linker/objcopy are required")
    with tempfile.TemporaryDirectory(prefix="p03-archive-asm-") as temp:
        work = Path(temp)
        commands = [[tools[0], "-mcpu=arm7tdmi", "-mthumb", str(source), "-o", str(work / "list.o")],
                    [tools[1], "-Ttext=0x080e6088", "-e", "Stage82_RelearnerList", str(work / "list.o"), "-o", str(work / "list.elf")],
                    [tools[2], "-O", "binary", str(work / "list.elf"), str(work / "list.bin")]]
        for command in commands:
            subprocess.run(command, check=True, capture_output=True, timeout=60)
        payload = (work / "list.bin").read_bytes()
        if len(payload) != PAYLOAD_SIZE or sha(payload) != PAYLOAD_SHA:
            raise ValueError("assembled native function differs from reviewed payload")
        expected = next(bytes.fromhex(new) for name, _, _, new in SITES if name == "native_list_builder")
        if payload + bytes.fromhex("c046") * ((LIST_SPAN-len(payload))//2) != expected:
            raise ValueError("assembled function padding differs")
    return {"status": "PASS", "source_sha256": ASM_SHA, "payload_sha256": PAYLOAD_SHA, "payload_size": PAYLOAD_SIZE}


def build(data: bytes) -> tuple[bytes, dict]:
    if type(data) is not bytes or len(data) != ROM_SIZE or sha(data) != PARENT_SHA:
        raise ValueError("exact Stage81 parent identity required")
    if sha((ROOT / ASM).read_bytes()) != ASM_SHA:
        raise ValueError("assembly source identity differs")
    validate_layout()
    out = bytearray(data)
    spans = []
    for name, offset, old_hex, new_hex in sorted(SITES, key=lambda row: row[1]):
        old, new = bytes.fromhex(old_hex), bytes.fromhex(new_hex)
        if not old or len(old) != len(new) or offset < 0 or offset + len(old) > ROM_SIZE:
            raise ValueError("invalid repair span")
        if spans and offset < spans[-1][1]:
            raise ValueError("overlapping repair spans")
        if data[offset:offset+len(old)] != old:
            raise ValueError("parent instruction guard differs: " + name)
        if name.endswith("GateScript"):
            if data[offset-3:offset] != bytes.fromhex("2b2c08") or data[offset+5:offset+7] != bytes.fromhex("0601"):
                raise ValueError("Hall-of-Fame checkflag/branch guard differs")
        out[offset:offset+len(old)] = new
        spans.append((offset, offset+len(old)))
    candidate = bytes(out)
    position = 0
    for start, end in spans:
        if data[position:start] != candidate[position:start]:
            raise ValueError("unrelated ROM bytes changed")
        position = end
    if data[position:] != candidate[position:] or sha(candidate) != CANDIDATE_SHA:
        raise ValueError("candidate identity or protected ROM bytes differ")
    report = {"schema_version": 1, "stage": 82, "status": "BUILT_NOT_ACCEPTED",
              "parent_sha256": PARENT_SHA, "candidate_sha256": CANDIDATE_SHA, "size": ROM_SIZE,
              "repairs": [{"name": name, "offset": offset, "before_hex": old, "after_hex": new} for name,offset,old,new in SITES],
              "changed_byte_count": sum(a != b for a,b in zip(data,candidate)),
              "layout": dict(LAYOUT), "hall_of_fame_required": True,
              "unrelated_bytes_preserved": True, "learnsets_changed": False,
              "active_baseline_changed": False, "full_p03_acceptance": False,
              "breeding_e2e": False, "release_ready": False}
    return candidate, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=ROOT / ".local/p03-archive-ui-candidate")
    parser.add_argument("--verify-assembly", action="store_true")
    args = parser.parse_args()
    output = args.output_directory.absolute()
    output.resolve().relative_to((ROOT / ".local").resolve())
    if output.is_symlink():
        raise ValueError("symlink output forbidden")
    output.mkdir(parents=True, exist_ok=True)
    for name in ("candidate.gba", "candidate.json"):
        path = output / name
        if path.is_symlink():
            raise ValueError("symlink output forbidden")
        path.unlink(missing_ok=True)
    original = (ROOT / parent.PARENT_PATH).read_bytes()
    stage81, _ = parent.build(original)
    candidate, report = build(stage81)
    if args.verify_assembly:
        report["assembly_verification"] = verify_assembly()
    (output / "candidate.gba").write_bytes(candidate)
    (output / "candidate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
