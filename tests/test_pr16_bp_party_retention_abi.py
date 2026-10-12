from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pr16_bp_party_retention_abi",
    ROOT / "scripts/pr16_bp_party_retention_abi.py",
)
assert SPEC and SPEC.loader
abi = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(abi)


def encode_bl(address: int, target: int) -> bytes:
    displacement = target - (address + 4)
    if not -(1 << 22) <= displacement < (1 << 22) or displacement & 1:
        raise ValueError("target outside Thumb BL range")
    encoded = displacement & ((1 << 23) - 1)
    first = 0xF000 | ((encoded >> 12) & 0x07FF)
    second = 0xF800 | ((encoded >> 1) & 0x07FF)
    return struct.pack("<HH", first, second)


def sources() -> dict[str, str]:
    builder = """
void BuildTrainerPartySetup(void)
{
    BuildFrontierParty(&gEnemyParty[0], 1, towerTier, TRUE, FALSE, B_SIDE_OPPONENT);
    BuildFrontierParty(&gEnemyParty[3], 2, towerTier, FALSE, FALSE, B_SIDE_OPPONENT);
    BuildFrontierParty(&gEnemyParty[0], 3, towerTier, TRUE, FALSE, B_SIDE_OPPONENT);
    BuildFrontierParty(&gEnemyParty[0], 4, towerTier, TRUE, FALSE, B_SIDE_OPPONENT);
    BuildFrontierParty(&gEnemyParty[3], 5, towerTier, FALSE, FALSE, B_SIDE_OPPONENT);
    if (IsRandomBattleTowerBattle())
        BuildFrontierParty(gPlayerParty, 0, towerTier, TRUE, TRUE + 1, B_SIDE_PLAYER);
    if (IsRandomBattleTowerBattle()
        || GetMonData(&gPlayerParty[3], MON_DATA_SPECIES, 0) == SPECIES_NONE)
        BuildFrontierParty(&gPlayerParty[3], 6, towerTier, 3, FALSE, B_SIDE_PLAYER);
}
"""
    return {
        abi.SOURCE_PATHS["builder"]: builder,
        abi.SOURCE_PATHS["predicate"]: "bool8 IsRandomBattleTowerBattle()\n{\n    return TRUE;\n}\n",
        abi.SOURCE_PATHS["header"]: "bool8 IsRandomBattleTowerBattle();\n",
    }


class SourceContractTests(unittest.TestCase):
    def test_source_contract_fixes_player_target_ordinal(self) -> None:
        report = abi.source_contract(sources())
        self.assertEqual(report["predicate_call_count"], 2)
        self.assertEqual(report["frontier_call_count"], 7)
        self.assertEqual(report["target_predicate_ordinal_zero_based"], 0)

    def test_source_contract_rejects_changed_player_arguments(self) -> None:
        changed = sources()
        path = abi.SOURCE_PATHS["builder"]
        changed[path] = changed[path].replace("TRUE + 1", "TRUE")
        with self.assertRaisesRegex(abi.AbiAuditError, "player random-rebuild"):
            abi.source_contract(changed)

    def test_source_contract_rejects_predicate_abi_drift(self) -> None:
        changed = sources()
        changed[abi.SOURCE_PATHS["predicate"]] = (
            "u16 IsRandomBattleTowerBattle(void)\n{\n    return 1;\n}\n"
        )
        with self.assertRaisesRegex(abi.AbiAuditError, "definition ABI"):
            abi.source_contract(changed)


class ThumbContractTests(unittest.TestCase):
    def test_decode_thumb_bl_forward(self) -> None:
        address = 0x092CE716
        raw = bytes.fromhex("00f087fa")
        self.assertEqual(abi.decode_thumb_bl(address, raw), 0x092CEC28)

    def test_decode_thumb_bl_backward(self) -> None:
        address = 0x09101000
        target = 0x090FF000
        raw = encode_bl(address, target)
        self.assertEqual(abi.decode_thumb_bl(address, raw), target)


class SymbolContractTests(unittest.TestCase):
    def test_parse_nm_symbols_accepts_unique_bounded_text(self) -> None:
        text = "\n".join(
            [
                "090DD2A4 00000600 T BuildTrainerPartySetup",
                "090F0000 00000024 T IsRandomBattleTowerBattle",
                "09100000 00000100 T BuildFrontierParty",
            ]
        )
        symbols = abi.parse_nm_symbols(text)
        self.assertEqual(symbols["BuildTrainerPartySetup"]["address"], 0x090DD2A4)

    def test_parse_nm_symbols_rejects_duplicate_target(self) -> None:
        text = "\n".join(
            [
                "090DD2A4 00000600 T BuildTrainerPartySetup",
                "090F0000 00000024 T IsRandomBattleTowerBattle",
                "090F0100 00000024 t IsRandomBattleTowerBattle",
                "09100000 00000100 T BuildFrontierParty",
            ]
        )
        with self.assertRaisesRegex(abi.AbiAuditError, "missing/ambiguous"):
            abi.parse_nm_symbols(text)


class CandidateTargetTests(unittest.TestCase):
    def test_candidate_target_binds_first_predicate_to_one_player_build(self) -> None:
        build = abi.EXPECTED_BUILD_SETUP_ADDRESS
        predicate = 0x090F0000
        frontier = 0x09100000
        size = 0xC0
        rom = bytearray(build - abi.ROM_BASE + size)
        predicate_sites = [build + 0x30, build + 0x78]
        frontier_sites = [
            build + 0x08,
            build + 0x10,
            build + 0x18,
            build + 0x40,
            build + 0x88,
            build + 0x90,
            build + 0x98,
        ]
        for site in predicate_sites:
            offset = site - abi.ROM_BASE
            rom[offset : offset + 4] = encode_bl(site, predicate)
        for site in frontier_sites:
            offset = site - abi.ROM_BASE
            rom[offset : offset + 4] = encode_bl(site, frontier)
        symbols = {
            "BuildTrainerPartySetup": {"address": build, "size": size, "type": "T"},
            "IsRandomBattleTowerBattle": {
                "address": predicate,
                "size": 0x24,
                "type": "T",
            },
            "BuildFrontierParty": {"address": frontier, "size": 0x100, "type": "T"},
        }
        report = abi.target_callsite_contract(bytes(rom), symbols)
        self.assertEqual(report["target_predicate_callsite"]["address"], predicate_sites[0])
        self.assertEqual(report["target_player_build_callsite"]["address"], build + 0x40)
        self.assertTrue(report["candidate_branch_targets_verified"])


if __name__ == "__main__":
    unittest.main()
