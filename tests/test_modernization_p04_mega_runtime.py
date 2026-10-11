from __future__ import annotations

import copy
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import build_modernization_p04_mega_runtime as builder  # noqa: E402
from tools import modernization_p04_mega_runtime as core  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


class ModernizationP04MegaRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / core.DEFAULT_CONFIG).read_text(encoding="utf-8")
        )
        cls.contract = core.build_mapping_contract(ROOT)
        cls.mappings = cls.contract["mappings"]
        cls.full_outputs = None
        if cls.config["status"] == "STAGE70_IDENTITY_PINNED":
            cls.full_outputs = builder.build_outputs()

    def test_all_49_stable_mappings_and_capacity_are_exact(self) -> None:
        counts = self.contract["counts"]
        self.assertEqual(
            counts,
            {
                "mappings": 49,
                "unique_base_species": 48,
                "unique_stones": 45,
                "forward_entries": 49,
                "reverse_entries": 49,
                "new_ability_effects_pending_stage72": 6,
            },
        )
        self.assertEqual(
            [row["target_species_id"] for row in self.mappings],
            list(range(1621, 1670)),
        )
        self.assertEqual(
            sorted({row["mega_stone_id"] for row in self.mappings}),
            list(range(999, 1044)),
        )
        self.assertEqual(self.contract["capacity_audit"]["existing_mega_entry_count"], 80)
        self.assertEqual(self.contract["capacity_audit"]["minimum_free_slots_before"], 15)
        self.assertEqual(self.contract["capacity_audit"]["minimum_free_slots_after"], 14)
        self.assertEqual(self.config["runtime_policy"]["required_keystone_item_id"], 580)

    def test_special_forms_never_collapse_to_shared_base(self) -> None:
        rows = {row["record_key"]: row for row in self.mappings}
        actual = {
            key: (
                rows[key]["source_species_id"],
                rows[key]["mega_stone_id"],
                rows[key]["target_species_id"],
            )
            for key in (
                "P04_MEGA_RAICHU_X",
                "P04_MEGA_RAICHU_Y",
                "P04_MEGA_MEOWSTIC_M",
                "P04_MEGA_MEOWSTIC_F",
                "P04_MEGA_MAGEARNA",
                "P04_MEGA_MAGEARNA_ORIGINAL",
                "P04_MEGA_TATSUGIRI_CURLY",
                "P04_MEGA_TATSUGIRI_DROOPY",
                "P04_MEGA_TATSUGIRI_STRETCHY",
                "P04_MEGA_FLOETTE_ETERNAL",
            )
        }
        self.assertEqual(
            actual,
            {
                "P04_MEGA_RAICHU_X": (26, 1032, 1656),
                "P04_MEGA_RAICHU_Y": (26, 1033, 1657),
                "P04_MEGA_MEOWSTIC_M": (967, 1030, 1654),
                "P04_MEGA_MEOWSTIC_F": (1013, 1030, 1653),
                "P04_MEGA_MAGEARNA": (1199, 1027, 1649),
                "P04_MEGA_MAGEARNA_ORIGINAL": (1254, 1027, 1650),
                "P04_MEGA_TATSUGIRI_CURLY": (1553, 1040, 1664),
                "P04_MEGA_TATSUGIRI_DROOPY": (1554, 1040, 1665),
                "P04_MEGA_TATSUGIRI_STRETCHY": (1555, 1040, 1666),
                "P04_MEGA_FLOETTE_ETERNAL": (1029, 1017, 1639),
            },
        )

    def test_host_model_applies_policy_ring_usage_and_exact_stone_gates(self) -> None:
        groups: dict[int, list[dict]] = defaultdict(list)
        for row in self.mappings:
            groups[row["source_species_id"]].append(row)
        all_stones = {row["mega_stone_id"] for row in self.mappings}
        for source, rows in groups.items():
            entries = [tuple(row["forward_entry"]) for row in rows] + [(0, 30, 0, 0)]
            valid = {row["mega_stone_id"] for row in rows}
            for row in rows:
                held = row["mega_stone_id"]
                self.assertEqual(
                    core.resolve_standard_mega(
                        entries,
                        held,
                        policy_allowed=True,
                        has_keystone=True,
                        already_used=False,
                    ),
                    row["target_species_id"],
                )
                self.assertEqual(
                    core.resolve_standard_mega(
                        entries,
                        held,
                        policy_allowed=True,
                        has_keystone=False,
                        already_used=False,
                    ),
                    0,
                )
                self.assertEqual(
                    core.resolve_standard_mega(
                        entries,
                        held,
                        policy_allowed=True,
                        has_keystone=True,
                        already_used=True,
                    ),
                    0,
                )
                self.assertEqual(
                    core.resolve_standard_mega(
                        entries,
                        held,
                        policy_allowed=False,
                        has_keystone=True,
                        already_used=False,
                    ),
                    0,
                )
            for wrong in all_stones - valid:
                self.assertEqual(
                    core.resolve_standard_mega(
                        entries,
                        wrong,
                        policy_allowed=True,
                        has_keystone=True,
                        already_used=False,
                    ),
                    0,
                    f"source={source}, wrong stone={wrong}",
                )

    def test_mode_specific_keystone_and_usage_contract(self) -> None:
        policy = self.config["runtime_policy"]
        self.assertEqual(
            policy["gate_order"],
            [
                "PROJECT_VEGA_BATTLE_POLICY_CAN_MEGA",
                "UPSTREAM_MODE_KEYSTONE_GATE",
                "EVOLUTION_ROW_EXACT_STONE",
                "PROJECT_AND_UPSTREAM_USAGE_MARKS",
            ],
        )
        self.assertFalse(
            core.project_policy_allows_mega(
                configured_mega_mode=False, side_used=False
            )
        )
        self.assertTrue(
            core.project_policy_allows_mega(
                configured_mega_mode=True, side_used=False
            )
        )
        self.assertFalse(
            core.project_policy_allows_mega(
                configured_mega_mode=True, side_used=True
            )
        )
        self.assertTrue(core.upstream_keystone_enabled("normal", True))
        self.assertFalse(core.upstream_keystone_enabled("normal", False))
        self.assertTrue(core.upstream_keystone_enabled("frontier", False))
        self.assertTrue(core.upstream_keystone_enabled("link", False))
        self.assertFalse(core.upstream_keystone_enabled("mega_brawl", False))
        sample = self.mappings[0]
        entries = [tuple(sample["forward_entry"]), (0, 0, 0, 0)]
        for mode, owns_ring, expected in (
            ("normal", True, sample["target_species_id"]),
            ("normal", False, 0),
            ("frontier", False, sample["target_species_id"]),
            ("link", False, sample["target_species_id"]),
        ):
            self.assertEqual(
                core.resolve_standard_mega(
                    entries,
                    sample["mega_stone_id"],
                    policy_allowed=True,
                    has_keystone=core.upstream_keystone_enabled(mode, owns_ring),
                    already_used=False,
                ),
                expected,
            )

        # 通常doubleは同ownerのbank/partnerを同時にmarkする。
        bank_done, partner_done = core.upstream_mark_mega(
            "normal", bank_done=False, partner_done=False, separate_owner=False
        )
        self.assertEqual((bank_done, partner_done), (True, True))
        self.assertTrue(
            core.upstream_owner_already_used(
                bank_done=bank_done,
                partner_done=partner_done,
                separate_owner=False,
            )
        )
        # in-game partner/two opponentsは相手owner側のmarkを共有しない。
        bank_done, partner_done = core.upstream_mark_mega(
            "normal", bank_done=False, partner_done=False, separate_owner=True
        )
        self.assertEqual((bank_done, partner_done), (True, False))
        self.assertFalse(
            core.upstream_owner_already_used(
                bank_done=False, partner_done=True, separate_owner=True
            )
        )
        # 上流Brawlはdoneを立てない一方、compiled project side-usedの実挙動は保留。
        self.assertEqual(
            core.upstream_mark_mega(
                "mega_brawl",
                bank_done=False,
                partner_done=False,
                separate_owner=False,
            ),
            (False, False),
        )
        self.assertEqual(
            policy["compiled_project_usage"]["mega_brawl"],
            "PROJECT_SIDE_USED_GATE_PRECEDES_UPSTREAM_EXCEPTION_EXACT_RUNTIME_PENDING_MGBA",
        )

    def test_reverse_rows_and_lifecycle_contract(self) -> None:
        for row in self.mappings:
            entries = [tuple(row["reverse_entry"]), (0, 0, 0, 0)]
            self.assertEqual(core.resolve_revert(entries), row["source_species_id"])
        lifecycle = self.contract["lifecycle"]
        self.assertEqual(lifecycle["switch"], "RETAIN_MEGA")
        self.assertEqual(
            lifecycle["faint"],
            "REVERT_BASE_VIA_TRY_FORM_REVERT_KEEP_MEGA_DATA_DONE",
        )
        self.assertEqual(
            lifecycle["revive"],
            "BASE_FORM_AND_REMEGA_REJECTED_BY_BANK_MEGA_EVOLVED",
        )
        self.assertEqual(
            lifecycle["battle_end"], "REVERSE_ROW_VIA_EXISTING_MEGA_REVERT"
        )
        self.assertEqual(
            lifecycle["interrupt"], "PRE_BATTLE_SNAPSHOT_RESTORE_BY_EXISTING_OWNER"
        )

    def test_capacity_audit_fails_closed_on_full_or_hidden_source_row(self) -> None:
        baseline = bytearray(
            (ROOT / self.config["inputs"]["capacity_baseline_rom"]["path"]).read_bytes()
        )
        table = int(
            self.config["fixed_cfru_jp"]["evolution_abi"]["capacity_baseline_address"],
            0,
        ) - core.ROM_BASE
        # Raichuは2 slot必要。全16 slotを占有するとstride拡張せずfailする。
        for slot in range(core.EVOS_PER_MON):
            struct.pack_into("<HHHH", baseline, table + 26 * core.ROW_STRIDE + slot * 8,
                             1, 1, 1, 0)
        with self.assertRaisesRegex(core.ModernizationP04MegaRuntimeError, "slot不足"):
            core.audit_capacity(bytes(baseline), table + core.ROM_BASE, 1621, self.mappings)

        hidden = bytearray(
            (ROOT / self.config["inputs"]["capacity_baseline_rom"]["path"]).read_bytes()
        )
        struct.pack_into("<HHHH", hidden, table + 26 * core.ROW_STRIDE + 1 * 8,
                         core.EVO_MEGA, 1032, 1656, 0)
        with self.assertRaisesRegex(core.ModernizationP04MegaRuntimeError, "探索から隠れ"):
            core.audit_capacity(bytes(hidden), table + core.ROM_BASE, 1621, self.mappings)

    def test_fixed_cfru_sources_symbols_and_snapshot_owners_are_pinned(self) -> None:
        audit = self.contract["fixed_cfru_jp_audit"]
        self.assertEqual(audit["status"], "PASS")
        self.assertTrue(audit["offsets"]["independent_runs_equal"])
        self.assertEqual(audit["offsets"]["symbols"]["CanMegaEvolve"], "0x09114BE4")
        self.assertEqual(audit["offsets"]["symbols"]["MegaRevert"], "0x09114FB8")
        self.assertEqual(audit["offsets"]["symbols"]["EndOfBattleThings.part.0"],
                         "0x090F6E84")
        self.assertEqual(
            audit["offsets"]["symbols"]["VegaBattlePolicyCanMega"],
            "0x09126B60",
        )
        self.assertEqual(
            audit["semantics"]["mega_brawl_compiled_project_gate"],
            "SIDE_USED_GATE_PRESENT_EXACT_MGBA_PENDING",
        )
        owners = {row.get("owner") for row in audit["sources"] if row.get("owner")}
        self.assertEqual(
            owners,
            {"CODEX_BATTLE_RUNTIME", "MIRAGE_PRODUCTION", "FACTORY_HIGH_MODES_V2"},
        )

    def test_c_oracle_matches_fixed_cfru_stop_and_cleanup_semantics(self) -> None:
        compiler = shutil.which("cc")
        self.assertIsNotNone(compiler)
        overlay = ROOT / "overlays/modernization_p04_mega_runtime"
        with tempfile.TemporaryDirectory() as raw:
            executable = Path(raw) / "p04_mega_oracle"
            compile_result = subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    str(overlay / "modernization_p04_mega_runtime_oracle.c"),
                    str(overlay / "modernization_p04_mega_runtime_oracle_host.c"),
                    "-o",
                    str(executable),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            run = subprocess.run(
                [str(executable)], text=True, capture_output=True, check=False
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result, {"status": "PASS", "assertions": 34, "failures": 0})

    def test_stage70_identity_and_ability_tables_fail_closed_until_pinned(self) -> None:
        if self.config["status"] == "WAITING_STAGE70_IDENTITY":
            with self.assertRaisesRegex(
                core.ModernizationP04MegaRuntimeError, "Stage70 identity未確定"
            ):
                core.build_stage71_image(ROOT)
        with self.assertRaisesRegex(
            core.ModernizationP04MegaRuntimeError, "Ability安全表metadata欠落"
        ):
            core._validate_ability_safety(  # pylint: disable=protected-access
                {
                    "ability_runtime": {
                        "localization_status":
                            "PROVISIONAL_LOCALIZATION_REPLACEABLE_P05_HAS_NO_JAPANESE_SUBMISSION",
                        "effect_runtime_status": "EFFECT_RUNTIME_PENDING_STAGE72",
                    }
                },
                bytes(core.ROM_SIZE),
                {},
            )

    def test_materialized_artifacts_are_exact_when_stage70_is_pinned(self) -> None:
        if self.full_outputs is None:
            self.skipTest("Stage70 identity待ち: preflight範囲のみ")
        assert self.full_outputs is not None
        for relative, expected in self.full_outputs.items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(path.read_bytes(), expected, relative)
        metadata = json.loads(
            self.full_outputs[self.config["outputs"]["metadata"]]
        )
        self.assertFalse(metadata["release_candidate"])
        self.assertEqual(metadata["evolution_table"]["forward_entries_added"], 49)
        self.assertEqual(metadata["evolution_table"]["reverse_entries_added"], 49)
        self.assertEqual(metadata["change_allowlist"]["outside_allowlist_count"], 0)
        self.assertEqual(
            metadata["allocation"]["policy"],
            "UPDATE_MUTATED_OWNER_CONTENT_HASH_PRESERVE_LAYOUT",
        )
        self.assertEqual(
            metadata["allocation"]["output_sha256"],
            hashlib.sha256(
                self.full_outputs[self.config["outputs"]["allocation"]]
            ).hexdigest(),
        )
        self.assertEqual(
            metadata["validation"]["usage_by_mode"][
                "mega_brawl_compiled_project_side_used"
            ],
            "EXACT_RUNTIME_PENDING_SINGLE_FINAL_MGBA",
        )
        patch = self.full_outputs[self.config["outputs"]["incremental_bps"]]
        parent = (ROOT / self.config["inputs"]["stage70_rom"]["path"]).read_bytes()
        self.assertEqual(
            apply_bps(parent, patch),
            self.full_outputs[self.config["outputs"]["rom"]],
        )

    def test_stage71_allocation_updates_only_owner_hash_and_all_slices_match(self) -> None:
        if self.full_outputs is None:
            self.skipTest("Stage70 identity待ち: allocation検証なし")
        assert self.full_outputs is not None
        parent_rom = (ROOT / self.config["inputs"]["stage70_rom"]["path"]).read_bytes()
        output_rom = self.full_outputs[self.config["outputs"]["rom"]]
        parent_raw = (
            ROOT / self.config["inputs"]["stage70_allocation"]["path"]
        ).read_bytes()
        output_raw = self.full_outputs[self.config["outputs"]["allocation"]]
        self.assertNotEqual(parent_raw, output_raw)
        audit = core.validate_stage71_allocation(
            parent_rom, output_rom, parent_raw, output_raw
        )
        self.assertEqual(audit["status"], "PASS")
        self.assertTrue(audit["content_hash_updated"])
        self.assertEqual(audit["all_allocation_rom_slices_compared"], 74)
        self.assertEqual(audit["non_target_allocation_count"], 73)
        self.assertEqual(audit["overlap_count"], 0)
        self.assertTrue(audit["non_target_ledger_rows_unchanged"])
        self.assertTrue(audit["non_target_rom_slices_unchanged"])

        parent_ledger = json.loads(parent_raw)
        output_ledger = json.loads(output_raw)
        target = next(
            row for row in output_ledger["allocations"] if row["sequence"] == 73
        )
        self.assertEqual(
            target["content_sha256"],
            hashlib.sha256(output_rom[target["start"]:target["end_exclusive"]]).hexdigest(),
        )
        self.assertEqual(
            hashlib.sha256(parent_raw).hexdigest(),
            self.config["inputs"]["stage70_allocation"]["sha256"],
        )
        for before, after in zip(
            parent_ledger["allocations"], output_ledger["allocations"], strict=True
        ):
            if before["sequence"] == 73:
                self.assertEqual(
                    {key: value for key, value in before.items()
                     if key != "content_sha256"},
                    {key: value for key, value in after.items()
                     if key != "content_sha256"},
                )
            else:
                self.assertEqual(before, after)
                self.assertEqual(
                    parent_rom[before["start"]:before["end_exclusive"]],
                    output_rom[after["start"]:after["end_exclusive"]],
                )

    def test_stage71_allocation_validation_is_fail_closed(self) -> None:
        if self.full_outputs is None:
            self.skipTest("Stage70 identity待ち: allocation検証なし")
        assert self.full_outputs is not None
        parent_rom = (ROOT / self.config["inputs"]["stage70_rom"]["path"]).read_bytes()
        output_rom = self.full_outputs[self.config["outputs"]["rom"]]
        parent_raw = (
            ROOT / self.config["inputs"]["stage70_allocation"]["path"]
        ).read_bytes()
        output_raw = self.full_outputs[self.config["outputs"]["allocation"]]
        ledger = json.loads(output_raw)

        wrong_target_hash = copy.deepcopy(ledger)
        next(row for row in wrong_target_hash["allocations"]
             if row["sequence"] == 73)["content_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            core.ModernizationP04MegaRuntimeError, "出力ROM全spanと不一致"
        ):
            core.validate_stage71_allocation(
                parent_rom,
                output_rom,
                parent_raw,
                core.stable_json(wrong_target_hash),
            )

        changed_non_target = copy.deepcopy(ledger)
        changed_row = next(
            row for row in changed_non_target["allocations"]
            if row["sequence"] != 73
        )
        changed_row["purpose"] = str(changed_row.get("purpose", "")) + " TAMPER"
        with self.assertRaisesRegex(
            core.ModernizationP04MegaRuntimeError, "非対象allocation ledger row"
        ):
            core.validate_stage71_allocation(
                parent_rom,
                output_rom,
                parent_raw,
                core.stable_json(changed_non_target),
            )

        changed_non_target_rom = bytearray(output_rom)
        non_target = next(
            row for row in ledger["allocations"] if row["sequence"] != 73
        )
        changed_non_target_rom[non_target["start"]] ^= 0xFF
        with self.assertRaisesRegex(
            core.ModernizationP04MegaRuntimeError, "非対象allocation ROM slice"
        ):
            core.validate_stage71_allocation(
                parent_rom,
                bytes(changed_non_target_rom),
                parent_raw,
                output_raw,
            )

        overlap = copy.deepcopy(ledger)
        ordered = sorted(overlap["allocations"], key=lambda row: row["start"])
        left, right = next(
            (left, right)
            for left, right in zip(ordered, ordered[1:])
            if left["region"] == right["region"]
        )
        left["end_exclusive"] = right["start"] + 1
        left["gba_end_exclusive"] = core.ROM_BASE + left["end_exclusive"]
        left["size"] = left["end_exclusive"] - left["start"]
        with self.assertRaisesRegex(
            core.ModernizationP04MegaRuntimeError, "allocation overlap検出"
        ):
            core._allocation_layout(overlap, core.ROM_SIZE)  # pylint: disable=protected-access


if __name__ == "__main__":
    unittest.main()
