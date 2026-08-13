#!/usr/bin/env python3
"""T06 battle core builderの固定入力・fail-closed契約。"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts.build_battle_core import (  # noqa: E402
    BattleCoreError,
    ROM_BASE,
    _archive_source,
    _audit_rows,
    _battle_patchset,
    _diagnostic_excerpt,
    _fingerprint_inputs,
    _load_config,
    _load_models,
    _pending_shadow_contract,
    _pending_shadow_input_contract,
    _stock_ram_contract,
    _trainer_copy_contract,
    build_vega_base_stats,
    build_vega_evolutions,
    check,
    install_canonical_runtime_roots,
    install_runtime_abi_bridges,
    parse_alias_values,
    prepare_source_tree,
    render_vega_effect_dispatch,
    rewrite_equ_constants,
    _validate_battle_smoke_payload,
    validate_applied_hook_outputs,
    validate_facility_monotype_witness,
    validate_changed_byte_coverage,
    validate_canonical_runtime_roots,
    validate_fixed_inputs,
    validate_hook_expected_bytes,
    validate_linked_evolution_references,
    validate_runtime_abi_bridges,
)
from scripts.build_upstream import _patch_source  # noqa: E402
from tools.engine.cfru_move_effect_lowering import lower_t04_move_effects  # noqa: E402
from tools.engine.cfru_script_table_gate import validate_script_command_tables  # noqa: E402


class BattleCoreBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = _load_config(ROOT)

    def test_fixed_inputs_and_models_are_exact(self) -> None:
        fixed = validate_fixed_inputs(ROOT, self.config)
        self.assertEqual(
            fixed["source"]["commit"],
            "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        )
        self.assertEqual(
            fixed["pending_shadow"],
            {
                "start": 0x0203E040,
                "end_exclusive": 0x0203E074,
                "size": 52,
                "magic": 0x54303650,
                "stage04_aligned_literal_count": 0,
            },
        )
        moves, ids = _load_models(ROOT, self.config)
        self.assertEqual(len(moves["moves"]), 1063)
        self.assertEqual(len(ids["types"]), 25)
        self.assertEqual(len(ids["abilities"]), 312)
        self.assertEqual(len(ids["items"]), 999)
        fingerprint = _fingerprint_inputs(ROOT, self.config, fixed)
        self.assertIn(
            "tools/engine/t06_publish_gate.py", fingerprint["files"]
        )

    def test_failure_diagnostics_are_bounded_without_losing_edges(self) -> None:
        short = "short diagnostic"
        self.assertEqual(_diagnostic_excerpt(short), short)
        noisy = "BEGIN" + "x" * 20_000 + "END"
        excerpt = _diagnostic_excerpt(noisy, limit=1024)
        self.assertLessEqual(len(excerpt), 1024)
        self.assertTrue(excerpt.startswith("BEGIN"))
        self.assertTrue(excerpt.endswith("END"))
        self.assertIn("characters omitted", excerpt)
        with self.assertRaises(ValueError):
            _diagnostic_excerpt(noisy, limit=128)

    def test_stock_rng_absolute_symbol_is_checked_outside_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            source = work / "fixture.s"
            object_path = work / "fixture.o"
            linked = work / "linked.o"
            source.write_text(
                ".thumb\n.text\n.global fixture\nfixture:\n bx lr\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["/usr/bin/arm-none-eabi-as", "-o", str(object_path), str(source)],
                check=True,
            )
            subprocess.run(
                [
                    "/usr/bin/arm-none-eabi-ld", "-r",
                    "--defsym=gCfruPendingBattleShadow=0x0203E040",
                    "--defsym=gRngValue=0x03005040",
                    "-o", str(linked), str(object_path),
                ],
                check=True,
            )
            self.assertEqual(
                _stock_ram_contract(linked),
                {
                    "gCfruPendingBattleShadow": 0x0203E040,
                    "gRngValue": 0x03005040,
                },
            )
            subprocess.run(
                [
                    "/usr/bin/arm-none-eabi-ld", "-r",
                    "--defsym=gCfruPendingBattleShadow=0x0203E040",
                    "--defsym=gRngValue=0x03005044",
                    "-o", str(linked), str(object_path),
                ],
                check=True,
            )
            with self.assertRaisesRegex(BattleCoreError, "stock RAM symbol"):
                _stock_ram_contract(linked)

    def test_pending_shadow_rejects_input_references_and_helper_calls(self) -> None:
        fixture_config = {
            "rom": {
                "pending_shadow_start": 0x0203E040,
                "pending_shadow_end_exclusive": 0x0203E074,
                "pending_shadow_magic": 0x54303650,
            }
        }
        self.assertEqual(
            _pending_shadow_input_contract(bytes(64), fixture_config)["size"], 52
        )
        with self.assertRaisesRegex(BattleCoreError, "references the reserved"):
            _pending_shadow_input_contract(
                bytes(8) + (0x0203E052).to_bytes(4, "little") + bytes(8),
                fixture_config,
            )

        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            source = work / "fixture.s"
            linked = work / "linked.o"
            source.write_text(
                ".thumb\n.text\n"
                ".global cfru_pending_command_reset\n"
                ".type cfru_pending_command_reset, %function\n"
                "cfru_pending_command_reset:\n strb r1, [r0]\n bx lr\n"
                ".size cfru_pending_command_reset, .-cfru_pending_command_reset\n"
                ".global cfru_pending_command_copy\n"
                ".type cfru_pending_command_copy, %function\n"
                "cfru_pending_command_copy:\n ldrb r2, [r1]\n strb r2, [r0]\n bx lr\n"
                ".size cfru_pending_command_copy, .-cfru_pending_command_copy\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["/usr/bin/arm-none-eabi-as", "-o", str(linked), str(source)],
                check=True,
            )
            self.assertEqual(_pending_shadow_contract(linked)["size"], 52)

    def test_trainer_copy_rejects_compiler_introduced_calls(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            source = work / "fixture.s"
            object_path = work / "linked.o"
            source.write_text(
                ".thumb\n"
                ".text\n"
                ".global cfru_trainer_mon_copy\n"
                ".type cfru_trainer_mon_copy, %function\n"
                "cfru_trainer_mon_copy:\n"
                " ldrb r2, [r1]\n"
                " strb r2, [r0]\n"
                " bx lr\n"
                ".size cfru_trainer_mon_copy, .-cfru_trainer_mon_copy\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["/usr/bin/arm-none-eabi-as", "-o", str(object_path), str(source)],
                check=True,
            )
            self.assertEqual(_trainer_copy_contract(object_path)["call_count"], 0)

            source.write_text(
                ".thumb\n"
                ".text\n"
                ".global cfru_trainer_mon_copy\n"
                ".type cfru_trainer_mon_copy, %function\n"
                "cfru_trainer_mon_copy:\n"
                " bl helper\n"
                " bx lr\n"
                ".size cfru_trainer_mon_copy, .-cfru_trainer_mon_copy\n"
                ".type helper, %function\n"
                "helper:\n"
                " bx lr\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["/usr/bin/arm-none-eabi-as", "-o", str(object_path), str(source)],
                check=True,
            )
            with self.assertRaisesRegex(BattleCoreError, "compiler-introduced calls"):
                _trainer_copy_contract(object_path)

    def test_battle_only_audit_is_complete_and_classified(self) -> None:
        rows = _audit_rows(ROOT, self.config)
        self.assertEqual(len(rows), 955)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["classification"]] = counts.get(row["classification"], 0) + 1
        self.assertEqual(
            counts,
            {"CFRU": 774, "PORT": 181},
        )
        self.assertNotIn("UNKNOWN", counts)
        self.assertNotIn("VEGA", counts)

    def test_generated_alias_universe_covers_c_and_assembly(self) -> None:
        move_path = ROOT / self.config["inputs"]["move_aliases"]["path"]
        ids_path = ROOT / self.config["inputs"]["id_aliases"]["path"]
        aliases = parse_alias_values(
            move_path.read_text(encoding="utf-8"),
            ids_path.read_text(encoding="utf-8"),
        )
        self.assertEqual(sum(name.startswith("MOVE_") for name in aliases), 992)
        self.assertEqual(sum(name.startswith("ITEM_") for name in aliases), 827)
        self.assertEqual(aliases["MOVE_PSYCHICNOISE"], 1062)
        self.assertEqual(aliases["ABILITY_AIRLOCK"], 77)
        self.assertEqual(aliases["ITEM_SERIOUS_MINT"], 987)
        for logical, minimum in (("asm_defines.s", 2000), ("xse_defines.s", 20)):
            original = (ROOT / self.config["source"]["path"] / logical).read_text(encoding="utf-8")
            rewritten, count = rewrite_equ_constants(original, aliases)
            self.assertGreaterEqual(count, minimum)
            if logical == "asm_defines.s":
                self.assertNotEqual(rewritten, original)

    def test_every_hook_matches_stage04_or_known_t04_repoint(self) -> None:
        rows = _audit_rows(ROOT, self.config)
        stage04 = (ROOT / self.config["inputs"]["stage04"]["path"]).read_bytes()
        t04 = json.loads((ROOT / "build/stages/04_moves.json").read_text(encoding="utf-8"))
        result = validate_hook_expected_bytes(stage04, rows, t04["repoints"]["rows"])
        self.assertEqual(result["total"], 955)
        self.assertEqual(result["t04_repoint_matches"], 178)
        self.assertEqual(result["vega_matches"], 777)

    def test_prepared_source_binds_runtime_policy_effects_and_cacophony(self) -> None:
        patchset = _battle_patchset(ROOT, self.config)
        with tempfile.TemporaryDirectory(prefix=".t06-source-", dir=ROOT / "build") as raw:
            tree = Path(raw) / "source"
            _archive_source(
                ROOT / self.config["source"]["path"],
                self.config["source"]["commit"],
                tree,
            )
            _patch_source(tree, "cfru", None)
            result = prepare_source_tree(ROOT, tree, self.config, patchset)
            prepared_catching = (tree / "src/catching.c").read_text(
                encoding="utf-8"
            )
            prepared_end = (tree / "src/end_battle.c").read_text(
                encoding="utf-8"
            )
            prepared_integration = (tree / "src/integration.c").read_text(
                encoding="utf-8"
            )
            prepared_mega = (tree / "src/mega.c").read_text(encoding="utf-8")
            prepared_builder = (tree / "src/build_pokemon.c").read_text(
                encoding="utf-8"
            )
            prepared_multi = (tree / "src/multi.c").read_text(encoding="utf-8")
            prepared_linker = (tree / "BPRJ.ld").read_text(encoding="utf-8")
        self.assertEqual(result["battle_patchset"]["write_count"], 955)
        self.assertEqual(result["battle_patchset"]["omitted_write_count"], 955)
        self.assertEqual(result["facility_runtime"]["rental"]["spread_count"], 19)
        self.assertEqual(
            result["facility_runtime"]["trainer_counts"],
            {
                "gTowerTrainers": 4,
                "gSpecialTowerTrainers": 1,
                "gFrontierBrains": 1,
                "gFrontierMultiBattleTrainers": 2,
            },
        )
        self.assertEqual(len(result["facility_runtime"]["formats"]), 3)
        self.assertEqual(len(result["facility_runtime"]["rules"]), 8)
        self.assertEqual(
            result["facility_runtime"]["monotype_runtime_gate"]["status"], "PASS"
        )
        self.assertEqual(result["effect_dispatch"]["binding_count"], 70)
        self.assertEqual(result["effect_dispatch"]["callsite_count"], 11)
        self.assertEqual(result["effect_dispatch"]["operation_count"], 66)
        self.assertGreaterEqual(result["effect_dispatch"]["native_patch_count"], 20)
        self.assertEqual(
            result["cacophony"],
            {
                "canonical_id": 76,
                "comparison_calls": 11,
                "switch_cases": 3,
                "table_rows": 2,
                "battle_script_jumps": 2,
                "special_insert_blocks": 1,
                "asm_equ_definitions": 1,
            },
        )
        self.assertEqual(result["rom_integration"]["mechanic_eligibility_gates"], 8)
        self.assertEqual(result["rom_integration"]["mechanic_activation_marks"], 7)
        self.assertEqual(
            result["mega_item_aliases"],
            {
                "source_item_count": 774,
                "remapped_item_count": 614,
                "comparison_count": 3,
                "mapping_sha256": "4ab9f5b959aa29c5b7c911c5e019dad59bd7d145a2fa0298030661011854c15c",
                "charizardite_x": {"source_id": 534, "canonical_id": 748},
            },
        )
        self.assertEqual(
            prepared_mega.count("VegaCanonicalItemFromCfruSource("), 4
        )
        self.assertNotIn("evolutions[i].param == mon->item", prepared_mega)
        self.assertNotRegex(prepared_mega, r"evolutions\[i\]\.param == item")
        self.assertEqual(
            result["rom_integration"]["raid_runtime_hooks"],
            {
                "initial_shield_predicate": 1,
                "shield_count": 1,
                "shield_break": 1,
                "boss_hp": 1,
                "turn_limit": 1,
                "capture_success": 1,
            },
        )
        self.assertEqual(
            result["rom_integration"]["raid_partner_moves"],
            {
                "source": "AUDITED_SPREAD",
                "randomizer_fallback": "DISABLED_UNTIL_VEGA_PACKED_U16_ADAPTER",
            },
        )
        prepared_raid_party = prepared_builder.split(
            "static void BuildRaidMultiParty(void)\n{", 1
        )[1].split("static void CreateFrontierMon", 1)[0]
        self.assertIn("retain audited spread moves", prepared_raid_party)
        self.assertIn("CreateFrontierMon", prepared_raid_party)
        self.assertIn("MON_DATA_MET_LOCATION", prepared_raid_party)
        self.assertNotIn("GiveBoxMonInitialMoveset", prepared_raid_party)
        self.assertNotIn(".moves, 0", prepared_raid_party)
        self.assertEqual(
            result["rom_integration"]["partner_controller_dispatch"],
            {"table_entries": 57, "guard": "buffer >= COMMAND_MAX"},
        )
        self.assertIn("if (buffer >= COMMAND_MAX)", prepared_multi)
        self.assertNotIn("if (buffer > COMMAND_MAX)", prepared_multi)
        self.assertEqual(
            prepared_catching.count("VegaGiveCaughtMonToPlayer(mon)"), 1
        )
        self.assertEqual(
            prepared_end.count("VegaBattlePolicyRestoreTeraTypes()"), 1
        )
        self.assertLess(
            prepared_end.index("(void)VegaBattlePolicyEnd()"),
            prepared_end.index("EndBattleFlagClear()"),
        )
        self.assertLess(
            prepared_end.index("BringBackTheDead()"),
            prepared_end.index("(void)VegaBattlePolicyEnd()"),
        )
        self.assertEqual(
            result["stock_rng_binding"],
            {"symbol": "gRngValue", "address": 0x03005040},
        )
        self.assertEqual(
            result["prebattle_shadow_binding"],
            {
                "symbol": "gCfruPendingBattleShadow",
                "address": 0x0203E040,
                "size": 52,
                "magic": 0x54303650,
            },
        )
        self.assertEqual(
            prepared_linker.count(
                "gCfruPendingBattleShadow = 0x0203E040;"
            ),
            1,
        )
        self.assertNotIn(
            "CfruPendingBattleShadow gCfruPendingBattleShadow;",
            prepared_integration,
        )
        self.assertEqual(prepared_linker.count("gRngValue = 0x03005040;"), 1)
        self.assertEqual(prepared_linker.count("Random = 0x804448C | 1;"), 1)
        self.assertEqual(
            result["runtime_abi_redirects"],
            ["gBaseStats", "gItems", "gEvolutionTable"],
        )
        self.assertEqual(
            result["rom_integration"]["facility_state"]["save_or_event_var_writes"], 0
        )

    def test_changed_byte_coverage_rejects_unclassified_write(self) -> None:
        before = bytes(64)
        after = bytearray(before)
        after[17] = 1
        with self.assertRaisesRegex(BattleCoreError, "unclassified ROM overwrite"):
            validate_changed_byte_coverage(before, bytes(after), [], 32, 16)
        after = bytearray(before)
        after[33] = 1
        result = validate_changed_byte_coverage(before, bytes(after), [], 32, 16)
        self.assertEqual(result["unclassified_changed_bytes"], 0)

    def test_linked_evolution_abi_preserves_vega_rows_and_bounds_mega_fixture(self) -> None:
        stage04 = (ROOT / self.config["inputs"]["stage04"]["path"]).read_bytes()
        record = self.config["runtime_tables"]["evolutions"]
        generated = build_vega_evolutions(stage04, record)
        self.assertEqual(len(generated), 1440 * 16 * 8)
        source = record["vega_pointer"] - ROM_BASE
        for species in range(412):
            legacy = stage04[source + species * 40:source + (species + 1) * 40]
            widened = generated[species * 128:(species + 1) * 128]
            if species == 157:
                self.assertEqual(legacy, bytes(40))
                self.assertEqual(
                    widened[:8],
                    bytes.fromhex("fe0016029d000000"),
                )
                self.assertEqual(widened[8:40], legacy[8:40])
            else:
                self.assertEqual(widened[:40], legacy)
            self.assertEqual(widened[40:], bytes(88))
        self.assertEqual(generated[412 * 128:], bytes((1440 - 412) * 128))
        predecessor = generated[156 * 128:156 * 128 + 8]
        self.assertEqual(int.from_bytes(predecessor[4:6], "little"), 157)
        self.assertEqual(
            int.from_bytes(
                stage04[
                    record["vega_pointer_site"]:
                    record["vega_pointer_site"] + 4
                ],
                "little",
            ),
            record["vega_pointer"],
        )
        self.assertEqual(record["linked_canonical_literal_count"], 38)
        self.assertEqual(record["linked_legacy_root_literal_count"], 0)
        self.assertEqual(
            record["legacy_pointer_sites"],
            [0x4265C, 0x426AC, 0x42828, 0x44F60, 0xCF9E8],
        )

    def test_linked_evolution_references_reject_legacy_root_reads(self) -> None:
        record = dict(self.config["runtime_tables"]["evolutions"])
        record["vega_pointer"] = 0x08123456
        size = 0xD1000
        stage04 = bytearray(size)
        final_stage = bytearray(size)
        legacy = record["vega_pointer"].to_bytes(4, "little")
        for site in record["legacy_pointer_sites"]:
            stage04[site:site + 4] = legacy
            final_stage[site:site + 4] = legacy
        canonical_address = ROM_BASE + 0x90000
        for index in range(38):
            start = 0x100 + index * 4
            final_stage[start:start + 4] = canonical_address.to_bytes(4, "little")
        fixture = canonical_address - ROM_BASE + 157 * 128
        final_stage[fixture:fixture + 8] = bytes.fromhex("fe0016029d000000")
        runtime = {
            "address": canonical_address,
            "size": 1440 * 128,
            "symbol": "gCfruVegaEvolutionTable",
            "sha256": "00" * 32,
        }
        result = validate_linked_evolution_references(
            bytes(stage04), bytes(final_stage), record, runtime, 0, 0xA0000
        )
        self.assertEqual(result["canonical_literal_count"], 38)
        self.assertEqual(result["legacy_root_literal_count"], 0)
        final_stage[0x800:0x804] = (ROM_BASE + 0x4265C).to_bytes(4, "little")
        with self.assertRaisesRegex(BattleCoreError, "reference count differs"):
            validate_linked_evolution_references(
                bytes(stage04), bytes(final_stage), record, runtime, 0, 0xA0000
            )

    def test_canonical_runtime_root_is_installed_and_revalidated(self) -> None:
        stage04 = bytearray(128)
        final_stage = bytearray(stage04)
        old_pointer = ROM_BASE + 32
        canonical_pointer = ROM_BASE + 64
        table = b"abcd"
        stage04[4:8] = old_pointer.to_bytes(4, "little")
        final_stage[4:8] = old_pointer.to_bytes(4, "little")
        final_stage[64:68] = table
        runtime_config = {
            "base_stats": {
                "symbol": "gCfruVegaBaseStats",
                "count": 1,
                "stride": 4,
                "vega_pointer_site": 4,
                "vega_pointer": old_pointer,
                "vega_pointer_occurrences": 1,
                "canonical_pointer_sites": [4],
                "legacy_pointer_sites": [],
            }
        }
        runtime_records = {
            "base_stats": {
                "symbol": "gCfruVegaBaseStats",
                "address": canonical_pointer,
                "size": len(table),
                "sha256": hashlib.sha256(table).hexdigest(),
            }
        }
        offsets = {"gCfruVegaBaseStats": canonical_pointer}
        installed = install_canonical_runtime_roots(
            bytes(stage04), final_stage, runtime_config, runtime_records, offsets
        )
        self.assertEqual(installed["count"], 1)
        self.assertEqual(
            int.from_bytes(final_stage[4:8], "little"), canonical_pointer
        )
        self.assertEqual(
            validate_canonical_runtime_roots(
                bytes(stage04), bytes(final_stage), runtime_config,
                runtime_records, offsets,
            ),
            installed,
        )

        coverage = validate_changed_byte_coverage(
            bytes(stage04), bytes(final_stage), [], 64, len(table), installed["rows"]
        )
        self.assertGreater(coverage["canonical_runtime_root_changed_bytes"], 0)
        self.assertEqual(coverage["canonical_runtime_root_intervals"], 1)

        broken = bytearray(final_stage)
        broken[4] ^= 1
        with self.assertRaisesRegex(BattleCoreError, "root target differs"):
            validate_canonical_runtime_roots(
                bytes(stage04), bytes(broken), runtime_config,
                runtime_records, offsets,
            )

    def test_selected_party_order_abi_bridge_is_exact_and_revalidated(self) -> None:
        bridge = self.config["abi_bridges"]
        self.assertEqual(
            bridge,
            {
                "selected_party_order": {
                    "rom_offset": 0x0A1730,
                    "before_pointer": 0x0203B048,
                    "after_pointer": 0x0203C6C8,
                    "consumer_address": 0x080A16B0,
                    "symbol": "gSelectedOrderFromParty",
                }
            },
        )
        stage04 = bytearray(0x0A1734)
        stage04[0x0A1730:0x0A1734] = (0x0203B048).to_bytes(4, "little")
        final_stage = bytearray(stage04)
        installed = install_runtime_abi_bridges(
            bytes(stage04), final_stage, bridge
        )
        self.assertEqual(installed["count"], 1)
        self.assertEqual(
            int.from_bytes(final_stage[0x0A1730:0x0A1734], "little"),
            0x0203C6C8,
        )
        self.assertEqual(
            validate_runtime_abi_bridges(bytes(stage04), bytes(final_stage), bridge),
            installed,
        )
        broken = bytearray(final_stage)
        broken[0x0A1730] ^= 1
        with self.assertRaisesRegex(BattleCoreError, "CFRU literal differs"):
            validate_runtime_abi_bridges(bytes(stage04), bytes(broken), bridge)

    def test_applied_hook_gate_rejects_wrong_final_target(self) -> None:
        # Production cardinality is independently fixed at 955; this fixture
        # exercises the fail-closed byte/target logic with repeated unique rows.
        stage = bytearray(4096)
        linked = bytearray(stage)
        output = bytearray(stage)
        rows = []
        offsets = {}
        for index in range(955):
            start = index * 4
            symbol = f"Symbol{index}"
            address = 0x09000000 + index * 4
            kind = "repoint"
            linked[start:start + 4] = address.to_bytes(4, "little")
            output[start:start + 4] = address.to_bytes(4, "little")
            offsets[symbol] = address
            rows.append({
                "write_id": f"fixture/{index:04d}",
                "start": hex(ROM_BASE + start),
                "end_exclusive": hex(ROM_BASE + start + 4),
                "size": "4",
                "kind": kind,
                "symbol": symbol,
                "classification": "CFRU",
            })
        # Production pointer count includes 584 rows. Mark the remainder as
        # static writes so the exact cardinality guard remains meaningful.
        for row in rows[584:]:
            row["kind"] = "byte_replacement"
        result = validate_applied_hook_outputs(
            bytes(stage), bytes(linked), bytes(output), rows, offsets, [], []
        )
        self.assertEqual(result["actual_match_count"], 955)
        self.assertEqual(result["decoded_pointer_count"], 584)
        broken = bytearray(output)
        broken[12] ^= 1
        with self.assertRaisesRegex(BattleCoreError, "final bytes differ"):
            validate_applied_hook_outputs(
                bytes(stage), bytes(linked), bytes(broken), rows, offsets, [], []
            )

    def test_battle_smoke_validator_rejects_unreached_route(self) -> None:
        runner = ROOT / "tools/mgba_battle_core_smoke.c"
        source = runner.read_text(encoding="utf-8")
        self.assertEqual(source.count('"SCHEDULER_E2E"'), 7)
        for route in (
            "status", "priority", "multi_target", "switch", "faint",
            "experience", "capture",
        ):
            self.assertNotIn(f'{{"{route}", "DIRECT_CALL_BOUNDED"', source)
        self.assertIn(r'\"unreached_routes\":[]', source)
        self.assertIn(r'\"non_e2e_routes\":[]', source)
        self.assertIn("priority_scheduler_order_e2e", source)
        self.assertIn("status_cleared_on_faint", source)

    def test_release_profile_disables_global_scaling(self) -> None:
        profile = (ROOT / "config/cfru_vega_minimal.h").read_text(encoding="utf-8")
        for name in (
            "VAR_GAME_DIFFICULTY",
            "SCALED_TRAINERS",
            "TRAINERS_WITH_EVS",
            "WILD_ALWAYS_SMART",
        ):
            self.assertIn(f"#undef {name}", profile)
        for name in ("MEGA_EVOLUTION_FEATURE", "DYNAMAX_FEATURE", "TERASTAL_FEATURE"):
            self.assertIn(f"#define {name}", profile)

    def test_vega_base_stats_are_widened_for_canonical_runtime_root(self) -> None:
        stage04 = (ROOT / self.config["inputs"]["stage04"]["path"]).read_bytes()
        record = self.config["runtime_tables"]["base_stats"]
        source_root = int.from_bytes(stage04[0x1BC:0x1C0], "little")
        self.assertEqual(source_root, 0x0821118C)
        self.assertEqual(record["vega_pointer_occurrences"], 55)
        self.assertEqual(
            record["canonical_pointer_sites"],
            [
                444, 73636, 75768, 76400, 90736, 124952, 136248, 145588,
                176788, 181864, 183572, 194364, 194664, 194936, 232644,
                233768, 233940, 235348, 250928, 251136, 253848, 257772,
                257844, 264872, 276560, 277152, 301096, 324696, 825020,
                954048, 954348, 954620, 1067136, 1077796, 1160848,
                1272340, 1273724, 1290944, 1416440, 1416740, 1417012,
            ],
        )
        self.assertEqual(
            record["legacy_pointer_sites"],
            [
                253600, 253956, 263244, 263276, 266384, 274384, 274404,
                274424, 274444, 274464, 274528, 275040, 285588, 834076,
            ],
        )
        self.assertEqual(
            set(record["canonical_pointer_sites"]) | set(record["legacy_pointer_sites"]),
            {
                offset for offset in range(len(stage04) - 3)
                if stage04[offset:offset + 4] == source_root.to_bytes(4, "little")
            },
        )
        generated = build_vega_base_stats(stage04, record)
        self.assertEqual(len(generated), 412 * 32)
        source_offset = source_root - 0x08000000
        for species in (0, 1, 4, 10, 411):
            old = stage04[source_offset + species * 28:source_offset + (species + 1) * 28]
            new = generated[species * 32:(species + 1) * 32]
            self.assertEqual(new[:22], old[:22])
            self.assertEqual(int.from_bytes(new[22:24], "little"), old[22])
            self.assertEqual(new[24:26], old[24:26])
            self.assertEqual(int.from_bytes(new[26:28], "little"), old[23])
            self.assertEqual(new[28:30], b"\0\0")
            self.assertEqual(int.from_bytes(new[30:32], "little"), old[9])

    def test_all_t04_pending_effect_adapters_have_explicit_dispatch(self) -> None:
        model = json.loads(
            (ROOT / self.config["inputs"]["move_model"]["path"]).read_text(encoding="utf-8")
        )
        source, bindings = render_vega_effect_dispatch(model)
        lowering = lower_t04_move_effects(model)
        self.assertEqual(len(bindings), 70)
        self.assertEqual(bindings[0]["move_id"], 292)
        self.assertEqual(bindings[-1]["move_id"], 509)
        self.assertEqual(source.count("case "), 70)
        self.assertIn("VegaResolveMoveEffectScript", source)
        self.assertIn("gBattleScriptsForMoveEffects[gBattleMoves[move].effect]", source)
        self.assertNotRegex(source, r"\b0x0[89][0-9A-Fa-f]{6}\b")
        self.assertEqual(lowering["operation_count"], 66)
        self.assertEqual(len(lowering["runtime_effect_overrides"]), 70)
        self.assertTrue(all("script_symbol" in row for row in bindings))

    def test_linked_script_command_tables_are_exact(self) -> None:
        candidates = sorted((ROOT / "build/battle-core").glob("*/run-1/test.gba"))
        offsets_candidates = sorted((ROOT / "build/battle-core").glob("*/run-1/offsets.ini"))
        if not candidates or not offsets_candidates:
            self.skipTest("no linked T06 prototype is available")
        from scripts.build_battle_core import parse_offsets
        snapshot = validate_script_command_tables(
            candidates[-1].read_bytes(),
            parse_offsets(offsets_candidates[-1].read_text(encoding="utf-8")),
        )
        self.assertEqual(snapshot["tables"]["main"]["entry_count"], 256)
        self.assertEqual(snapshot["tables"]["secondary"]["entry_count"], 57)
        self.assertEqual(snapshot["roots"]["count"], 5)


@unittest.skipUnless((ROOT / "build/stages/06_battle_core.json").is_file(), "T06 stage is not published")
class PublishedBattleCoreTests(unittest.TestCase):
    def test_check_is_read_only_and_passes(self) -> None:
        tracked = [
            ROOT / "build/stages/06_battle_core.gba",
            ROOT / "build/stages/06_battle_core.json",
            ROOT / "generated/engine/battle_core/cfru_payload.bin",
            ROOT / "generated/engine/battle_core/runtime_tables.json",
            ROOT / "reports/generated/battle_hook_matrix.csv",
            ROOT / "reports/generated/battle_core_smoke.md",
            ROOT / "reports/generated/facility_core_smoke.md",
            ROOT / "reports/generated/trainer_ai_smoke.md",
        ]
        before = {path: path.read_bytes() for path in tracked}
        result = check(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["hooks"], 955)
        self.assertEqual(before, {path: path.read_bytes() for path in tracked})


if __name__ == "__main__":
    unittest.main()
