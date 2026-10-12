from __future__ import annotations

import copy
import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.modernization_p05_stage77_suppression import (
    DEFAULT_CONFIG,
    EXPECTED_HOOKS,
    EXPECTED_STAGE76_COMMIT,
    ModernizationP05Stage77SuppressionError,
    build_artifacts,
    circus_global_suppressed,
    compile_payload,
    preflight,
    read_config,
    require_pinned_parent,
    selected_delegate,
    sha256,
    stable_json,
    veneer,
)
from tools.release.bps import apply_bps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "overlays/modernization_p05_stage77_suppression"
EXPECTED_OUTPUT_PATHS = {
    "build/stages/77_modernization_p05_circus_suppression.gba",
    "build/stages/77_modernization_p05_circus_suppression.json",
    "build/stages/77_modernization_p05_circus_suppression_allocation.json",
    "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps",
    "generated/runtime/modernization_p05_stage77_suppression.bin",
    "generated/runtime/modernization_p05_stage77_suppression_symbols.json",
    "generated/runtime/modernization_p05_stage77_suppression_audit.json",
    "content/modernization/p05_stage77_suppression_contract.json",
    "content/modernization/p05_stage77_suppression_checkpoint.json",
}


class ModernizationP05Stage77SuppressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_config(ROOT, DEFAULT_CONFIG)
        cls.fixed = require_pinned_parent(ROOT, cls.config)
        cls.compiled = compile_payload(ROOT, 0x095E0000, EXPECTED_HOOKS)
        cls.artifacts = build_artifacts(ROOT)
        outputs = cls.config["outputs"]
        cls.result = cls.artifacts[outputs["rom"]]
        cls.metadata = json.loads(cls.artifacts[outputs["metadata"]])
        cls.allocation = json.loads(cls.artifacts[outputs["allocation"]])
        cls.audit = json.loads(cls.artifacts[outputs["audit"]])
        cls.contract = json.loads(cls.artifacts[outputs["contract"]])
        cls.checkpoint = json.loads(cls.artifacts[outputs["checkpoint"]])
        cls.asm_source = (
            SOURCE_DIR / "modernization_p05_stage77_suppression.S"
        ).read_text(encoding="utf-8")

    def _assert_config_rejects(self, mutated: dict) -> None:
        with tempfile.TemporaryDirectory(prefix="stage77-config-mutation-") as temporary:
            path = Path(temporary) / "mutated.json"
            path.write_text(json.dumps(mutated), encoding="utf-8")
            with self.assertRaises(ModernizationP05Stage77SuppressionError):
                read_config(ROOT, path)

    def test_exact_29_hook_33_surface_contract_and_abi(self) -> None:
        hooks = self.config["parent_abi"]["hooks"]
        self.assertEqual(hooks, EXPECTED_HOOKS)
        self.assertEqual(len(hooks), 29)
        self.assertEqual(len({row["address"] for row in hooks}), 29)
        self.assertEqual(len({row["target"] for row in hooks}), 29)
        self.assertEqual(sum(len(row["abilities"]) for row in hooks), 33)
        self.assertEqual(sum(row["width"] == 12 for row in hooks), 7)
        for row in hooks:
            self.assertEqual(
                int(row["continuation_thumb"], 0),
                (int(row["address"], 0) + row["width"]) | 1,
            )
            self.assertEqual(
                row["r3_contract"],
                "ORIGINAL_R3_IN_R12" if row["width"] == 12
                else "STAGE72_R3_CLOBBER_VENEER_COMPATIBLE",
            )

    def test_config_mutations_fail_closed(self) -> None:
        mutations: list[dict] = []
        mutated = copy.deepcopy(self.config)
        mutated["parent_identity"]["stage76_commit"] = "0" * 40
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["hooks"][0]["parent_hex"] = "00" * 12
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["hooks"][0]["normal_address"] = "0x0953417D"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["hooks"][0]["suppressed_address"] = "0x0953410D"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["hooks"][0]["r3_contract"] = "R3_LOST"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["suppression_contract"]["battle_circus_global"]["battle_type_mask"] = "0x08000000"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["suppression_contract"]["exclusions"]["full_p05_done"] = True
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["suppression_contract"]["exclusions"]["browt_pombon_gecqua_added"] = 1
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["preserved_stage76_patches"].pop()
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["outputs"]["rom"] = "build/stages/wrong.gba"
        mutations.append(mutated)
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                self._assert_config_rejects(mutation)

    def test_parent_commit_six_identities_and_stage72_symbols_are_exact(self) -> None:
        self.assertEqual(
            self.config["parent_identity"]["stage76_commit"],
            EXPECTED_STAGE76_COMMIT,
        )
        for key in (
            "rom", "metadata", "allocation", "checkpoint", "tracked_config",
            "contract",
        ):
            identity = self.config["parent_identity"][key]
            self.assertEqual(len(self.fixed[key]), identity["size"])
            self.assertEqual(sha256(self.fixed[key]), identity["sha256"])
        for key in ("checkpoint", "tracked_config", "contract"):
            path = self.config["parent_identity"][key]["path"]
            committed = subprocess.run(
                ["git", "show", f"{EXPECTED_STAGE76_COMMIT}:{path}"], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(committed.returncode, 0, committed.stderr.decode())
            self.assertEqual(committed.stdout, self.fixed[key])
        stage72_symbols = json.loads(self.fixed["stage72_symbols"])["symbols"]
        for row in EXPECTED_HOOKS:
            self.assertEqual(
                stage72_symbols[row["normal_delegate"]], row["normal_address"]
            )
            self.assertEqual(
                stage72_symbols[row["suppressed_delegate"]],
                row["suppressed_address"],
            )

    def test_global_gate_truth_table_selects_all_delegates(self) -> None:
        cases = (
            (0, 0, False),
            (0x04000000, 0, False),
            (0, 0x80000000, False),
            (0x04000000, 0x80000000, True),
            (0xFFFFFFFF, 0xFFFFFFFF, True),
        )
        for battle_flags, circus_flags, expected in cases:
            self.assertEqual(
                circus_global_suppressed(battle_flags, circus_flags), expected
            )
            for row in EXPECTED_HOOKS:
                chosen = selected_delegate(row, battle_flags, circus_flags)
                self.assertEqual(
                    chosen,
                    int(
                        row[
                            "suppressed_address" if expected else "normal_address"
                        ],
                        0,
                    ),
                )

    def test_assembly_dispatchers_pin_both_globals_and_both_targets(self) -> None:
        code = self.compiled.code
        for row in EXPECTED_HOOKS:
            name = row["target"]
            offset = self.compiled.symbols[name] - 0x095E0000
            size = self.compiled.sizes[name]
            self.assertEqual(size, 48 if row["width"] == 12 else 40)
            section = code[offset:offset + size]
            for value in (
                0x02022AAC,
                0x0203DFBC,
                int(row["normal_address"], 0),
                int(row["suppressed_address"], 0),
            ):
                self.assertIn(struct.pack("<I", value), section, row["name"])
        self.assertEqual(
            self.asm_source.count("\nSTAGE77_DISPATCH_R3_IN_R12 "), 7
        )
        self.assertEqual(
            self.asm_source.count("\nSTAGE77_DISPATCH_R3_CLOBBER "), 22
        )

    def test_five_argument_r3_and_stack_abi_tail_delegation_is_preserved(self) -> None:
        section = self.compiled.disassembly.split(
            "<Stage77_DispatchAbilityBattleEffects>:", 1
        )[1].split("\n\n", 1)[0]
        for instruction in (
            "mov\tr3, ip", "push\t{r2}", "mov\tip, r2", "pop\t{r2}",
            "bx\tip", "bx\tr3",
        ):
            self.assertIn(instruction, section)
        type_calc = next(row for row in EXPECTED_HOOKS if row["name"] == "TypeCalc")
        self.assertEqual(type_calc["abi"], "u8(u16,u8,u8,void*,u8)")
        self.assertEqual(type_calc["r3_contract"], "ORIGINAL_R3_IN_R12")
        # The dispatcher never changes SP permanently, so the fifth stack arg
        # reaches either Stage72 target at the same address.
        self.assertEqual(section.count("push\t{r2}"), section.count("pop\t{r2}"))

    def test_all_parent_preimages_and_output_veneers_match(self) -> None:
        parent = self.fixed["rom"]
        symbols = json.loads(
            self.artifacts[self.config["outputs"]["symbols"]]
        )["symbols"]
        for row in EXPECTED_HOOKS:
            offset = int(row["address"], 0) - 0x08000000
            before = bytes.fromhex(row["parent_hex"])
            self.assertEqual(parent[offset:offset + row["width"]], before)
            expected = veneer(
                row["width"], int(symbols[row["target"]], 0),
                int(row["address"], 0),
            )
            self.assertEqual(
                self.result[offset:offset + row["width"]], expected
            )

    def test_stage76_four_patches_and_eelevate_pending_sites_are_byte_unchanged(self) -> None:
        parent = self.fixed["rom"]
        rows = [
            self.config["parent_abi"]["is_ability_suppressed"],
            *self.config["parent_abi"]["preserved_stage76_patches"],
            *self.config["parent_abi"]["negative_preservation_sites"],
        ]
        for row in rows:
            offset = int(row["address"], 0) - 0x08000000
            expected = bytes.fromhex(row["parent_hex"])
            self.assertEqual(parent[offset:offset + row["width"]], expected)
            self.assertEqual(self.result[offset:offset + row["width"]], expected)

    def test_allocation_lineage_payload_and_allowlist_are_exact(self) -> None:
        parent_allocation = json.loads(self.fixed["allocation"])
        self.assertEqual(len(parent_allocation["allocations"]), 80)
        self.assertEqual(len(self.allocation["allocations"]), 81)
        self.assertEqual(
            self.allocation["allocations"][:80],
            parent_allocation["allocations"],
        )
        self.assertEqual(self.allocation["allocations"][-1]["sequence"], 80)
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)
        payload = self.metadata["payload"]
        self.assertEqual(payload["allocation_sequence"], 80)
        self.assertEqual(
            sha256(self.result[payload["start"]:payload["start"] + payload["size"]]),
            payload["sha256"],
        )
        self.assertTrue(self.metadata["allocation_lineage"]["first80_all_fields_equal"])
        self.assertEqual(
            self.checkpoint["rom_diff"]["changed_bytes_outside_allowlist"], 0
        )
        self.assertEqual(
            self.checkpoint["rom_diff"]["allowlist_interval_count"], 30
        )

    def test_bps_roundtrip_and_nine_artifact_checkpoint(self) -> None:
        outputs = self.config["outputs"]
        self.assertEqual(set(self.artifacts), EXPECTED_OUTPUT_PATHS)
        self.assertEqual(len(self.artifacts), 9)
        bps = self.artifacts[outputs["incremental_bps"]]
        self.assertEqual(apply_bps(self.fixed["rom"], bps), self.result)
        self.assertEqual(self.metadata["bps"]["source_sha256"], sha256(self.fixed["rom"]))
        self.assertEqual(self.metadata["bps"]["target_sha256"], sha256(self.result))
        manifest = self.checkpoint["artifact_manifest"]
        self.assertEqual(manifest["artifact_count"], 9)
        self.assertEqual(len(manifest["artifacts"]), 9)
        identities = {row["path"]: row for row in manifest["artifacts"]}
        for relative, raw in self.artifacts.items():
            identity = identities[relative]
            self.assertEqual(identity["size"], len(raw))
            if relative != outputs["checkpoint"]:
                self.assertEqual(identity["sha256"], sha256(raw))

    def test_completion_and_exclusion_claims_remain_fail_closed(self) -> None:
        for document in (self.metadata, self.audit, self.contract, self.checkpoint):
            self.assertFalse(document["release_ready"])
            self.assertFalse(document["full_p05_done"])
            self.assertFalse(document["done"])
        checks = self.checkpoint["checks"]
        self.assertEqual(checks["stage72_unique_hooks_repointed"], 29)
        self.assertEqual(checks["stage72_ability_surface_occurrences_guarded"], 33)
        self.assertEqual(checks["stage76_pointer_and_three_hooks_preserved"], "PASS")
        self.assertEqual(checks["eelevate_unsafe_switch_hooks_installed"], 0)
        self.assertEqual(checks["browt_pombon_gecqua_added"], 0)
        self.assertEqual(checks["side_change_added"], 0)
        self.assertEqual(checks["mgba_runtime"], "NOT_RUN")
        self.assertIn("Eelevate dedicated switch AI", " ".join(self.checkpoint["pending"]))

    def test_preflight_and_implementation_identity_are_deterministic(self) -> None:
        summary = preflight(ROOT)
        self.assertEqual(summary["hook_count"], 29)
        self.assertEqual(summary["r3_saved_hook_count"], 7)
        self.assertEqual(summary["payload_size"], 1220)
        expected_paths = {
            "config/modernization_p05_stage77_suppression.json",
            "tools/modernization_p05_stage77_suppression.py",
            "scripts/build_modernization_p05_stage77_suppression.sh",
            "tests/test_modernization_p05_stage77_suppression.py",
            "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S",
            "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.ld",
        }
        self.assertEqual(
            {row["path"] for row in self.metadata["implementation"]["files"]},
            expected_paths,
        )
        self.assertEqual(
            self.metadata["implementation"]["sha256"],
            self.checkpoint["implementation_sha256"],
        )
        self.assertEqual(
            self.metadata["allocation_lineage"]["parent_first80_sha256"],
            sha256(stable_json(json.loads(self.fixed["allocation"])["allocations"])),
        )


if __name__ == "__main__":
    unittest.main()
