from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pr16_bp_party_retention_abi_cache",
    ROOT / "scripts/pr16_bp_party_retention_abi_cache.py",
)
assert SPEC and SPEC.loader
cache = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cache)


class CacheDiscoveryTests(unittest.TestCase):
    def test_two_complete_runs_are_selected(self) -> None:
        fingerprint = "a" * 64
        root = f"build/battle-core/{fingerprint}"
        names = [
            f"{root}/run-1/linked.o",
            f"{root}/run-1/outcome.json",
            f"{root}/run-2/linked.o",
            f"{root}/run-2/outcome.json",
            "ignored.txt",
        ]
        groups = cache.discover(names)
        self.assertEqual(set(groups), {fingerprint})
        self.assertEqual(groups[fingerprint][2]["linked.o"], names[2])

    def test_duplicate_member_is_rejected(self) -> None:
        fingerprint = "b" * 64
        member = f"build/battle-core/{fingerprint}/run-1/linked.o"
        with self.assertRaisesRegex(cache.CacheAuditError, "duplicate cache member"):
            cache.discover([member, member])


class TargetControlFlowTests(unittest.TestCase):
    @staticmethod
    def _thumb_bl(address: int, target: int) -> bytes:
        displacement = target - (address + 4)
        if displacement < 0:
            displacement += 1 << 23
        first = 0xF000 | ((displacement >> 12) & 0x07FF)
        second = 0xF800 | ((displacement >> 1) & 0x07FF)
        return struct.pack("<HH", first, second)

    @staticmethod
    def _thumb_b(address: int, target: int) -> bytes:
        displacement = target - (address + 4)
        if displacement < 0:
            displacement += 1 << 12
        return struct.pack("<H", 0xE000 | ((displacement >> 1) & 0x07FF))

    @staticmethod
    def _thumb_bne(address: int, target: int) -> bytes:
        displacement = target - (address + 4)
        if displacement < 0:
            displacement += 1 << 9
        return struct.pack("<H", 0xD100 | ((displacement >> 1) & 0x00FF))

    def _fixture(self, *, mismatched_join: bool = False) -> tuple[bytes, dict]:
        build = cache.base.ROM_BASE + 0x100
        predicate = cache.base.ROM_BASE + 0x600
        frontier = cache.base.ROM_BASE + 0x700
        rom = bytearray(0x1000)

        def put(address: int, raw: bytes) -> None:
            offset = address - cache.base.ROM_BASE
            rom[offset : offset + len(raw)] = raw

        true_block = build + 0x0C
        continuation = build + 0x40
        put(build, self._thumb_bl(build, predicate))
        put(build + 4, struct.pack("<H", 0x2800))  # cmp r0, #0
        put(build + 6, self._thumb_bne(build + 6, true_block))
        put(build + 8, self._thumb_b(build + 8, continuation))
        put(true_block, self._thumb_bl(true_block, frontier))
        exit_target = continuation + (2 if mismatched_join else 0)
        put(build + 0x10, self._thumb_b(build + 0x10, exit_target))

        # GCC may place unrelated basic blocks in linear address order between
        # the two predicate calls.  They must not be attributed to the target
        # source-level if block.
        for address in (build + 0x14, build + 0x18):
            put(address, self._thumb_bl(address, frontier))
        put(build + 0x20, self._thumb_bl(build + 0x20, predicate))
        for address in (build + 0x24, build + 0x28, build + 0x2C, build + 0x30):
            put(address, self._thumb_bl(address, frontier))

        symbols = {
            "BuildTrainerPartySetup": {
                "name": "BuildTrainerPartySetup",
                "address": build,
                "size": 0x80,
                "type": "T",
            },
            "IsRandomBattleTowerBattle": {
                "name": "IsRandomBattleTowerBattle",
                "address": predicate,
                "size": 0x18,
                "type": "T",
            },
            "BuildFrontierParty_variants": [
                {
                    "name": "BuildFrontierParty.isra.0",
                    "address": frontier,
                    "size": 0x100,
                    "type": "t",
                }
            ],
        }
        return bytes(rom), symbols

    def test_target_player_call_follows_true_cfg_edge(self) -> None:
        rom, symbols = self._fixture()
        report = cache.target_callsite_contract(rom, symbols)
        target = report["target_predicate_callsite"]
        next_target = report["next_predicate_callsite"]
        linear = [
            row
            for row in report["frontier_calls"]
            if target["address"] < row["address"] < next_target["address"]
        ]
        self.assertEqual(len(linear), 3)
        self.assertEqual(
            report["target_player_build_callsite"]["address"],
            symbols["BuildTrainerPartySetup"]["address"] + 0x0C,
        )
        self.assertTrue(report["target_predicate_guard"]["paths_rejoin"])
        self.assertTrue(report["candidate_control_flow_verified"])

    def test_target_true_and_false_paths_must_rejoin(self) -> None:
        rom, symbols = self._fixture(mismatched_join=True)
        with self.assertRaisesRegex(
            cache.CacheAuditError,
            "true/false paths do not rejoin",
        ):
            cache.target_callsite_contract(rom, symbols)


if __name__ == "__main__":
    unittest.main()
