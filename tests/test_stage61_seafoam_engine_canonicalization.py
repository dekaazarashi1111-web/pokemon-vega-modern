#!/usr/bin/env python3
"""Stage61 Seafoam engine predicate の実ROM/ABI固定契約。"""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGE60 = ROOT / "build/stages/60_wild_species_root_repair.gba"
CLEAN = ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
RUNTIME = (
    ROOT
    / "overlays/stage61_display_npc_event_audit/"
      "stage61_display_npc_event_audit.c"
)

ROM_BASE = 0x08000000
STAGE60_SHA256 = (
    "3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1"
)
PREDICATE_ENTRY = 0x080553F8
PREDICATE_RAW = bytes.fromhex(
    "00b50006000e04f0aff80006000e012810d10548006881880448814202d00448"
    "814207d1012006e0485000030156000001570000002002bc0847"
)
PREDICATE_SHA256 = (
    "5f6b35fb819799c4e86f380fa8d10193891d54718d5db433d80a15064f8cd39b"
)
SURFABLE_ENTRY = 0x08059560
SURFABLE_RAW = bytes.fromhex(
    "00b50006000e04494018017801200840002803d1002002e000703108012002bc"
    "0847"
)
SURFABLE_SHA256 = (
    "b4034d0c39d6e9cbe4b8bad2fdca1b390c022f44016afaadd5e19ac108e471dc"
)

# Direct Thumb-1 BL callers of the predicate in the complete 32 MiB Stage60
# image.  The first owns initial-avatar state; the second owns fall-warp state.
CALLERS = {
    0x080553B6: bytes.fromhex("00f01ff8"),
    0x0808432C: bytes.fromhex("d1f764f8"),
}
# One extension-resident, currently unreferenced duplicate transition-policy
# function calls through a literal + shared ``bx r3`` veneer.  It is still a
# real machine-code xref and must not be hidden by a direct-BL-only audit.
POINTER_CALL_ROOTS = {0x0911FEB8: 0x080553F9}
EXTENSION_POINTER_CALL_OWNER = {
    "start": 0x0911FE44,
    "end": 0x0911FEC8,
    "sha256": (
        "c8cf20f72404bfca054d1b51927101cf4e3678a109ff6ad85c4a187df85eac1e"
    ),
    "veneer": 0x091202A8,
    "veneer_raw": bytes.fromhex("1847"),
}
CALLER_OWNERS = {
    "GetAdjustedInitialTransitionFlags": {
        "start": 0x0805538C,
        "end": 0x080553F8,
        "sha256": (
            "2d7f8e0a73c74ac8d95be472d012f3a610840adf411f35d49d8cbad711bfc153"
        ),
    },
    "FallWarpEffect_7": {
        "start": 0x080842F4,
        "end": 0x08084370,
        "sha256": (
            "f2f7c7733bd063150807cfb8a5376758125668932fb80a790d2723917ea47d20"
        ),
    },
}

SOURCE_HASHES = {
    "vendor/upstream/pokefirered/src/overworld.c": (
        "df352e738b56856765aec65adc6fdea0a4b25fe567bc760d4ce2d34afc6ff7e2"
    ),
    "vendor/upstream/pokefirered/src/field_effect.c": (
        "87a44c0a6411a2a51092928971346f24cb71183824f095533394357dfbc2344a"
    ),
    "vendor/upstream/pokefirered/src/metatile_behavior.c": (
        "a1491016f9b6ee56c38fd66bf890dfcb5d37c7dc0dfda9fe7c0a5282376b9042"
    ),
    "vendor/upstream/pokefirered/include/global.h": (
        "044325b90e7c79146cc0cf73d31b6be3e4840059e2e778b63d9b5448fe538429"
    ),
    "vendor/upstream/pokefirered/include/constants/map_groups.h": (
        "86f00ce61a8e88de0a73ef582476c7e03e804bbd70ee6a2877249894526683ad"
    ),
}

SOURCE_FUNCTION_HASHES = {
    (
        "vendor/upstream/pokefirered/src/overworld.c",
        "static u8 GetAdjustedInitialTransitionFlags(struct "
        "InitialPlayerAvatarState *playerStruct, u16 metatileBehavior, "
        "u8 mapType)",
    ): "5cbd567d7a8362d879c3b0f17ce7b114cd620c479d4e0ede0a60add2f2d6dbda",
    (
        "vendor/upstream/pokefirered/src/overworld.c",
        "bool8 MetatileBehavior_IsSurfableInSeafoamIslands("
        "u16 metatileBehavior)",
    ): "3155abe53e1571c8df20617116176e13d1af884d2b7a18551ecf1c5d49e9d9d3",
    (
        "vendor/upstream/pokefirered/src/field_effect.c",
        "static bool8 FallWarpEffect_7(struct Task *task)",
    ): "21bc21df0ac0154f3f2b7d4764b02bfe4894952ac3cc401748d697ce1e083d45",
    (
        "vendor/upstream/pokefirered/src/metatile_behavior.c",
        "bool8 MetatileBehavior_IsSurfable(u8 metatileBehavior)",
    ): "75d1e464d398bb6873e6c56a8b6a3cb694ccb24c77ee39da1f0f2175c03034f5",
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _rom_slice(rom: bytes, start: int, end: int) -> bytes:
    return rom[start - ROM_BASE:end - ROM_BASE]


def _thumb1_bl_target(site: int, raw: bytes) -> int | None:
    if len(raw) != 4:
        return None
    first, second = struct.unpack("<HH", raw)
    if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
        return None
    displacement = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
    if displacement & (1 << 22):
        displacement -= 1 << 23
    return site + 4 + displacement


def _all_direct_thumb1_bl_callers(rom: bytes, target: int) -> list[int]:
    callers: list[int] = []
    for offset in range(0, len(rom) - 3, 2):
        site = ROM_BASE + offset
        if _thumb1_bl_target(site, rom[offset:offset + 4]) == target:
            callers.append(site)
    return callers


def _all_pointer_roots(rom: bytes, pointer: int) -> list[int]:
    needle = struct.pack("<I", pointer)
    roots: list[int] = []
    cursor = 0
    while True:
        offset = rom.find(needle, cursor)
        if offset < 0:
            return roots
        roots.append(ROM_BASE + offset)
        cursor = offset + 1


def _extract_c_function(source: str, signature: str) -> str:
    start = source.index(signature + "\n{")
    brace = start + len(signature) + 1
    depth = 0
    for cursor in range(brace, len(source)):
        if source[cursor] == "{":
            depth += 1
        elif source[cursor] == "}":
            depth -= 1
            if depth == 0:
                return source[start:cursor + 1]
    raise AssertionError(f"関数終端を検出できません: {signature}")


def _entry_trampoline(target: int) -> bytes:
    if target & 1:
        raise ValueError("symbol address must be halfword-aligned")
    # ldr r3, [pc, #0]; bx r3; .word target|1
    return bytes.fromhex("004b1847") + struct.pack("<I", target | 1)


class Stage61SeafoamEngineCanonicalizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage60 = STAGE60.read_bytes()
        cls.clean = CLEAN.read_bytes()
        cls.runtime_source = RUNTIME.read_text(encoding="utf-8")

    def test_stage60_predicate_and_stock_surfable_preimages_are_exact(self) -> None:
        self.assertEqual(_sha(self.stage60), STAGE60_SHA256)
        self.assertEqual(
            _rom_slice(
                self.stage60,
                PREDICATE_ENTRY,
                PREDICATE_ENTRY + len(PREDICATE_RAW),
            ),
            PREDICATE_RAW,
        )
        self.assertEqual(_sha(PREDICATE_RAW), PREDICATE_SHA256)
        self.assertEqual(
            _thumb1_bl_target(
                PREDICATE_ENTRY + 6,
                PREDICATE_RAW[6:10],
            ),
            SURFABLE_ENTRY,
        )
        self.assertEqual(
            _rom_slice(
                self.stage60,
                SURFABLE_ENTRY,
                SURFABLE_ENTRY + len(SURFABLE_RAW),
            ),
            SURFABLE_RAW,
        )
        self.assertEqual(_sha(SURFABLE_RAW), SURFABLE_SHA256)
        # Both owners are unchanged Japanese FireRed Rev.0 engine code.
        for address, raw in (
            (PREDICATE_ENTRY, PREDICATE_RAW),
            (SURFABLE_ENTRY, SURFABLE_RAW),
        ):
            self.assertEqual(
                _rom_slice(self.clean, address, address + len(raw)), raw
            )
        self.assertIn(struct.pack("<I", 0x03005048), PREDICATE_RAW)
        self.assertIn(struct.pack("<I", 0x00005601), PREDICATE_RAW)
        self.assertIn(struct.pack("<I", 0x00005701), PREDICATE_RAW)

    def test_all_direct_callers_and_owner_extents_are_pinned(self) -> None:
        self.assertEqual(
            _all_direct_thumb1_bl_callers(self.stage60, PREDICATE_ENTRY),
            sorted(CALLERS),
        )
        for site, raw in CALLERS.items():
            self.assertEqual(_rom_slice(self.stage60, site, site + 4), raw)
            self.assertEqual(_thumb1_bl_target(site, raw), PREDICATE_ENTRY)
            self.assertEqual(_rom_slice(self.clean, site, site + 4), raw)
        for owner in CALLER_OWNERS.values():
            raw = _rom_slice(self.stage60, owner["start"], owner["end"])
            self.assertEqual(_sha(raw), owner["sha256"])
            self.assertEqual(
                raw, _rom_slice(self.clean, owner["start"], owner["end"])
            )

    def test_all_indirect_pointer_call_roots_are_pinned(self) -> None:
        self.assertEqual(
            _all_pointer_roots(self.stage60, PREDICATE_ENTRY | 1),
            sorted(POINTER_CALL_ROOTS),
        )
        for root, pointer in POINTER_CALL_ROOTS.items():
            self.assertEqual(
                _rom_slice(self.stage60, root, root + 4),
                struct.pack("<I", pointer),
            )
        owner = EXTENSION_POINTER_CALL_OWNER
        raw = _rom_slice(self.stage60, owner["start"], owner["end"])
        self.assertEqual(_sha(raw), owner["sha256"])
        self.assertEqual(
            _rom_slice(
                self.stage60,
                owner["veneer"],
                owner["veneer"] + len(owner["veneer_raw"]),
            ),
            owner["veneer_raw"],
        )
        # The duplicate owner has no direct caller or function-pointer root in
        # Stage60; recording that dormancy avoids treating it as the active
        # initial-avatar path while retaining its predicate xref evidence.
        self.assertEqual(
            _all_direct_thumb1_bl_callers(self.stage60, owner["start"]), []
        )
        self.assertEqual(
            _all_pointer_roots(self.stage60, owner["start"] | 1), []
        )

    def test_fixed_source_correspondence_and_saveblock_abi(self) -> None:
        for relative, expected in SOURCE_HASHES.items():
            self.assertEqual(_sha((ROOT / relative).read_bytes()), expected)
        for (relative, signature), expected in SOURCE_FUNCTION_HASHES.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            function = _extract_c_function(source, signature)
            self.assertEqual(_sha(function.encode("utf-8")), expected)

        global_h = (ROOT / "vendor/upstream/pokefirered/include/global.h").read_text(
            encoding="utf-8"
        )
        map_groups = (
            ROOT / "vendor/upstream/pokefirered/include/constants/map_groups.h"
        ).read_text(encoding="utf-8")
        self.assertIn("/*0x0004*/ struct WarpData location;", global_h)
        self.assertIn("s8 mapGroup;\n    s8 mapNum;\n    s8 warpId;", global_h)
        self.assertIn(
            "#define MAP_SEAFOAM_ISLANDS_B3F                  "
            "(86 | (1 << 8))",
            map_groups,
        )
        self.assertIn(
            "#define MAP_SEAFOAM_ISLANDS_B4F                  "
            "(87 | (1 << 8))",
            map_groups,
        )

    def test_project_wrapper_is_same_abi_and_exactly_bounded(self) -> None:
        source = self.runtime_source
        self.assertIn("typedef u8 (*MetatileBehaviorFn)(u8);", source)
        self.assertIn(
            "PTR(MetatileBehaviorFn, 0x08059561u)", source
        )
        self.assertIn("STAGE61_SOURCE_SEAFOAM_GROUP = 1u", source)
        self.assertIn("STAGE61_PROJECT_SEAFOAM_GROUP = 97u", source)
        self.assertIn("STAGE61_SEAFOAM_B3F_MAP = 86u", source)
        self.assertIn("STAGE61_SEAFOAM_B4F_MAP = 87u", source)
        signature = (
            "u8 Stage61DisplayNpcEvent_IsSurfableInSeafoamIslands("
            "u16 metatile_behavior)"
        )
        function = _extract_c_function(source, signature)
        self.assertIn(
            "FN_METATILE_BEHAVIOR_IS_SURFABLE((u8)metatile_behavior) != 1u",
            function,
        )
        self.assertIn("save = G_SAVE_BLOCK1_PTR;", function)
        self.assertIn("save[4], save[5]", function)

        def expected(surfable: bool, group: int, map_number: int) -> bool:
            return (
                surfable
                and group in {1, 97}
                and map_number in {86, 87}
            )

        accepted = {
            (group, map_number)
            for group in range(256)
            for map_number in range(256)
            if expected(True, group, map_number)
        }
        self.assertEqual(accepted, {(1, 86), (1, 87), (97, 86), (97, 87)})
        self.assertFalse(expected(False, 1, 86))
        self.assertFalse(expected(False, 97, 87))

    def test_entry_hook_is_an_exact_full_predicate_redirect(self) -> None:
        self.assertEqual(
            _rom_slice(self.stage60, PREDICATE_ENTRY, PREDICATE_ENTRY + 8),
            bytes.fromhex("00b50006000e04f0"),
        )
        replacement = _entry_trampoline(0x09ABC000)
        self.assertEqual(replacement.hex(), "004b184701c0ab09")
        self.assertEqual(len(replacement), 8)
        with self.assertRaises(ValueError):
            _entry_trampoline(0x09ABC001)

    def test_arm7tdmi_wrapper_compile_and_object_code(self) -> None:
        gcc = shutil.which("arm-none-eabi-gcc")
        nm = shutil.which("arm-none-eabi-nm")
        objcopy = shutil.which("arm-none-eabi-objcopy")
        if gcc is None or nm is None or objcopy is None:
            self.skipTest("ARM GNU toolchain is not installed")
        with tempfile.TemporaryDirectory(prefix="stage61-seafoam-") as temp:
            obj = Path(temp) / "runtime.o"
            wrapper = Path(temp) / "wrapper.bin"
            subprocess.run(
                [
                    gcc,
                    "-mthumb",
                    "-mcpu=arm7tdmi",
                    "-mthumb-interwork",
                    "-Os",
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-ffreestanding",
                    "-fno-builtin",
                    "-fno-unwind-tables",
                    "-fno-asynchronous-unwind-tables",
                    "-fdata-sections",
                    "-ffunction-sections",
                    "-fno-common",
                    "-c",
                    str(RUNTIME),
                    "-o",
                    str(obj),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            symbols = subprocess.run(
                [nm, "-n", "-S", "--defined-only", str(obj)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertIn(
                " T Stage61DisplayNpcEvent_IsSurfableInSeafoamIslands",
                symbols,
            )
            subprocess.run(
                [
                    objcopy,
                    "-O",
                    "binary",
                    "--only-section=.text."
                    "Stage61DisplayNpcEvent_IsSurfableInSeafoamIslands",
                    str(obj),
                    str(wrapper),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            wrapper_raw = wrapper.read_bytes()
            self.assertEqual(len(wrapper_raw), 0x44)
            self.assertEqual(
                _sha(wrapper_raw),
                "266de8d4ffdfaeca7e0b774a4146d0d6952a99700f5be474871828e174cab10f",
            )
            self.assertIn(struct.pack("<I", 0x08059561), wrapper_raw)
            self.assertIn(struct.pack("<I", 0x03005048), wrapper_raw)


if __name__ == "__main__":
    unittest.main()
