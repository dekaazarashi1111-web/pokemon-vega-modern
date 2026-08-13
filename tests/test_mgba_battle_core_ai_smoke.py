#!/usr/bin/env python3
"""T06 CFRU-on-Vega 実ROM AI acceptance runner の限定検証。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_battle_core_ai_smoke.c"
INCLUDED_SOURCES = (
    SOURCE,
    ROOT / "tools/mgba_battle_core_smoke.c",
    ROOT / "tools/mgba_ai_fixture_runner.c",
)
STAGE_CANDIDATES = [
    ROOT / "build/stages/06_battle_core.gba",
    ROOT / "build/stages/06_battle.gba",
    *sorted((ROOT / "build/stages").glob("06*.gba")),
]
REQUIRED_SYMBOLS = (
    "AI_TrySwitchOrUseItem",
    "BattleAI_SetupAIData",
    "BattleAI_ChooseMoveOrAction",
    "ClearCachedAIData",
    "VegaConfigureNextBattlePolicy",
    "VegaBattlePolicyResolveAIProfileBits",
)
EXPECTED_PROFILES = {
    "AI_BASIC": 1,
    "AI_SEMI_SMART": 3,
    "AI_FULL_SMART": 5,
}
EXPECTED_SCENARIOS = {
    "ko_damage_choice": ("KO", "DIFFERENTIAL_DECISION", "SINGLE"),
    "two_hit_damage_choice": (
        "TWO_HIT_KO",
        "DIFFERENTIAL_DECISION",
        "SINGLE",
    ),
    "normal_immunity_avoidance": (
        "IMMUNITY",
        "DIFFERENTIAL_DECISION",
        "SINGLE",
    ),
    "hazard_install": ("HAZARD", "DIFFERENTIAL_DECISION", "SINGLE"),
    "hazard_remove": (
        "HAZARD_REMOVE",
        "DIFFERENTIAL_DECISION",
        "SINGLE",
    ),
    "setup_attack": ("SETUP", "DIFFERENTIAL_DECISION", "SINGLE"),
    "self_recovery": (
        "RECOVERY",
        "DIFFERENTIAL_DECISION",
        "SINGLE",
    ),
    "pivot_u_turn": ("PIVOT", "DIFFERENTIAL_DECISION", "SINGLE"),
    "weather_rain": ("WEATHER", "DIFFERENTIAL_DECISION", "SINGLE"),
    "field_electric": ("FIELD", "DIFFERENTIAL_DECISION", "SINGLE"),
    "double_target": (
        "DOUBLE_TARGET",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
    "double_ally_harm_avoidance": (
        "ALLY_HARM_AVOIDANCE",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
    "double_protect": (
        "PROTECT",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
    "double_wide_guard": (
        "WIDE_GUARD",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
    "double_tailwind": (
        "TAILWIND",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
    "double_trick_room": (
        "TRICK_ROOM",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
    "double_follow_me": (
        "FOLLOW_ME",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
    "double_helping_hand": (
        "HELPING_HAND",
        "DIFFERENTIAL_DECISION",
        "DOUBLE",
    ),
}

EXPECTED_MECHANICS = {
    "STANDARD": {
        "dynamax_candidate": 0xFF,
        "dynamax_potential": 0,
        "terastal_candidate": 0xFF,
        "terastal_potential": 0,
        "mega_present": False,
        "transformed_move_source": 0,
    },
    "MEGA": {
        "dynamax_candidate": 0xFF,
        "dynamax_potential": 0,
        "terastal_candidate": 0xFF,
        "terastal_potential": 0,
        "mega_present": True,
        "transformed_move_source": 0,
    },
    "Z_MOVE": {
        "dynamax_candidate": 0xFF,
        "dynamax_potential": 0,
        "terastal_candidate": 0xFF,
        "terastal_potential": 0,
        "mega_present": False,
        "transformed_move_source": 52,
    },
    "DYNAMAX": {
        "dynamax_candidate": 0,
        "dynamax_potential": 1,
        "terastal_candidate": 0,
        "terastal_potential": 0,
        "mega_present": False,
        "transformed_move_source": 52,
    },
    "TERASTAL": {
        "dynamax_candidate": 0xFF,
        "dynamax_potential": 0,
        "terastal_candidate": 0,
        "terastal_potential": 1,
        "mega_present": False,
        "transformed_move_source": 0,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_symbol_map(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict) or set(REQUIRED_SYMBOLS) - set(value):
        return None
    result: dict[str, int] = {}
    for name in REQUIRED_SYMBOLS:
        raw = value[name]
        if not isinstance(raw, int) or isinstance(raw, bool):
            return None
        if not 0x08000000 <= raw <= 0x09FFFFFF:
            return None
        result[name] = raw
    return result


def current_stage() -> tuple[Path, dict[str, int]] | None:
    """生成時のsource/ROM/symbol identityが揃ったstageだけを選ぶ。"""

    source_identities = {
        path.relative_to(ROOT).as_posix(): sha256(path) for path in INCLUDED_SOURCES
    }
    for path in dict.fromkeys(STAGE_CANDIDATES):
        metadata_path = path.with_suffix(".json")
        if not path.is_file() or not metadata_path.is_file():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            fingerprint_files = metadata["fingerprint_inputs"]["files"]
            recorded_sources = {
                logical: fingerprint_files[logical]["sha256"]
                for logical in source_identities
            }
            recorded_rom = metadata["output"]["sha256"]
            symbols = _parse_symbol_map(
                metadata["upstream_runs"][0]["integration_symbols"]
            )
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            continue
        if (
            recorded_sources == source_identities
            and recorded_rom == sha256(path)
            and symbols is not None
        ):
            return path, symbols
    return None


STAGE = current_stage()


def assert_hex_address(test: unittest.TestCase, value: object) -> int:
    test.assertIsInstance(value, str)
    assert isinstance(value, str)
    test.assertRegex(value, re.compile(r"^0x[0-9A-F]{8}$"))
    address = int(value, 16)
    test.assertGreaterEqual(address, 0x08000000)
    test.assertLessEqual(address, 0x09FFFFFF)
    return address


class BattleCoreAiSmokeSourceTests(unittest.TestCase):
    def test_reuses_real_battle_and_t01_ai_lifecycle(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('#include "mgba_battle_core_smoke.c"', source)
        self.assertIn("#define BATTLE_CORE_EMBEDDED", source)
        self.assertIn("run_trace_prefix(core)", source)
        self.assertIn("BATTLE_CORE_START_TRAINER", source)
        self.assertIn("VegaConfigureNextBattlePolicy", source)
        self.assertIn("trainer 328 identity", source)
        self.assertIn("make_max_party(core)", source)
        self.assertIn("configure_party_moves(core)", source)
        self.assertIn("sync_active_moves(core)", source)
        self.assertNotIn("mCoreLoadSaveFile", source)

    def test_profiles_use_same_linked_ai_entries_and_exact_bits(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for name, bits in EXPECTED_PROFILES.items():
            self.assertIn(f'"{name}"', source)
            self.assertIn(f"T06_AI_PROFILE_{name.removeprefix('AI_')} = {bits}", source)
        for symbol in REQUIRED_SYMBOLS:
            self.assertIn(symbol, source)
        self.assertIn("result.effective != profile", source)
        self.assertIn("result.resolved != profile", source)
        self.assertIn("authoritative high-bit AI mode", source)
        self.assertIn("T06_AI_TYPE_BLANK = 20", source)
        self.assertIn("T06_AI_PENDING_SHADOW = 0x0203E040", source)
        self.assertIn("T06_AI_PENDING_MAGIC = 0x54303650", source)
        self.assertIn("pre-battle shadow", source)
        self.assertNotIn("uint32_t pending_newbs", source)

    def test_all_named_decision_routes_are_fail_closed(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for name, (category, classification, battle) in EXPECTED_SCENARIOS.items():
            self.assertIn(f'"{name}"', source)
            self.assertIn(f'"{category}"', source)
            self.assertIn(classification, source)
            self.assertIn(battle, {"SINGLE", "DOUBLE"})
        self.assertIn("expected_slots", source)
        self.assertIn("expected_targets", source)
        self.assertIn("available_competitors", source)
        self.assertIn("differential AI scenario lacks a legal competing move", source)
        self.assertIn("table-driven AI scenarios differed from exact contracts", source)
        self.assertNotIn("FORCED_LEGAL_SCRIPT_ROUTE", source)
        self.assertNotIn("T06_AI_FORCED_LEGAL", source)
        self.assertIn(r'\"unreached_scenarios\":[]', source)
        self.assertNotIn('"status":"SKIP"', source)

    def test_switch_item_cache_and_performance_contracts_are_explicit(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("ACTION_SWITCH", source)
        self.assertIn("T06_AI_STATUS3_PERISH_SONG", source)
        self.assertIn("Perish Song optimal-switch fixture", source)
        self.assertIn("ACTION_USE_ITEM", source)
        self.assertIn("T06_AI_ITEM_FULL_RESTORE = 19", source)
        for mutation in (
            "switch",
            "faint",
            "form",
            "item",
            "weather",
            "terrain",
            "status",
            "stat_stages",
            "pp",
            "side_condition",
        ):
            self.assertIn(f'"{mutation}"', source)
        self.assertIn("T06_AI_POLICY_CACHE_SNAPSHOT_SIZE = 0x2D0", source)
        self.assertIn(
            "rom_lazy_snapshot_recalculation_without_runner_clear", source
        )
        self.assertIn("cache mutation did not create a live stale snapshot", source)
        self.assertIn("ROM lazy snapshot did not recalculate after mutation", source)
        lazy_body = source.split(
            "static void t06_ai_verify_lazy_cache_invalidation", 1
        )[1].split("static struct T06AiMechanicObservation", 1)[0]
        self.assertNotIn("t06_ai_clear_cold_cache", lazy_body)
        self.assertIn(
            "ClearCachedAIData left prediction-cache flag set", source
        )
        self.assertNotIn(
            "flags & ~NEWBS_CALCULATED_PREDICTIONS_BIT", source
        )
        self.assertIn("capture_prediction_cache(core)", source)
        self.assertIn("overlay_prediction_cache(core, cache)", source)
        self.assertIn("cold_setup.cycles + cold_move.cycles", source)
        self.assertIn("warm_setup.cycles + warm_move.cycles", source)
        self.assertIn("T06_AI_SINGLE_COLD_LIMIT = 3300000", source)
        self.assertIn("T06_AI_SINGLE_WARM_LIMIT = 450000", source)
        self.assertIn("T06_AI_DOUBLE_COLD_LIMIT = 8000000", source)
        self.assertIn("T06_AI_DOUBLE_WARM_LIMIT = 800000", source)

    def test_mechanic_and_secondary_chance_claims_are_bounded(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        config = json.loads(
            (ROOT / "config/battle_core.json").read_text(encoding="utf-8")
        )
        fixture_species = config["runtime_tables"]["evolutions"][
            "mega_fixture_species"
        ]
        self.assertEqual(fixture_species, 157)
        self.assertIn(
            f"T06_AI_MEGA_FIXTURE_SPECIES = {fixture_species}", source
        )
        self.assertIn("T06_AI_MEGA_SOURCE_ITEM = 534", source)
        self.assertIn("T06_AI_MEGA_METHOD = 0xFE", source)
        self.assertIn("read16(core, result.mega_candidate + 0U)", source)
        self.assertIn("read16(core, result.mega_candidate + 2U)", source)
        self.assertIn("read16(core, result.mega_candidate + 4U)", source)
        self.assertIn("read16(core, result.mega_candidate + 6U)", source)
        for mode in ("STANDARD", "MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"):
            self.assertIn(f'"{mode}"', source)
        self.assertIn("MODE_SPECIFIC_EXACT_CANDIDATE_ACTION", source)
        self.assertIn("mechanic mode candidate/action differs from exact contract", source)
        self.assertIn("T06_AI_NEWBS_TRANSFORMED_MOVE_SOURCE = 0x288", source)
        self.assertIn("NOT_INFERRED_FROM_TABLE_INVENTORY", source)
        self.assertIn("const uint8_t values[3] = {10, 20, 30}", source)

    def test_runner_is_read_only_and_requires_identity_arguments(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("ROM SHA-256 mismatch", source)
        self.assertIn("if (argc != 9)", source)
        self.assertIn(r'\"read_only\":true', source)
        self.assertIn(r'\"artifacts_written\":[]', source)
        self.assertIn("mCoreLoadFile", source)
        self.assertNotIn('fopen(argv[1], "wb")', source)

    def test_stale_stage_is_not_selected_for_live_acceptance(self) -> None:
        if STAGE is not None:
            stage_rom, symbols = STAGE
            metadata = json.loads(
                stage_rom.with_suffix(".json").read_text(encoding="utf-8")
            )
            for source in INCLUDED_SOURCES:
                logical = source.relative_to(ROOT).as_posix()
                self.assertEqual(
                    metadata["fingerprint_inputs"]["files"][logical]["sha256"],
                    sha256(source),
                )
            self.assertEqual(symbols, _parse_symbol_map(symbols))
            return
        existing = [
            path for path in dict.fromkeys(STAGE_CANDIDATES) if path.is_file()
        ]
        if not existing:
            self.skipTest("T06 stage has not been generated")
        self.assertTrue(existing)

    def test_runner_compiles_with_werror(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler is unavailable")
        with tempfile.TemporaryDirectory(prefix="t06-ai-source-") as raw:
            executable = Path(raw) / "mgba_battle_core_ai_smoke"
            completed = subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-O2",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    str(SOURCE),
                    "-o",
                    str(executable),
                    "-lmgba",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"runner compile failed:\n{completed.stdout}{completed.stderr}",
            )


@unittest.skipUnless(STAGE is not None, "fixed T06 AI stage ROM is unavailable")
class FixedStageBattleCoreAiSmokeTests(unittest.TestCase):
    _temporary: tempfile.TemporaryDirectory[str]
    _runner: Path
    _stage_rom: Path
    _rom_sha256: str
    _symbols: dict[str, int]

    @classmethod
    def setUpClass(cls) -> None:
        assert STAGE is not None
        cls._stage_rom, cls._symbols = STAGE
        cls._rom_sha256 = sha256(cls._stage_rom)
        compiler = shutil.which("cc")
        if compiler is None:
            raise unittest.SkipTest("C compiler is unavailable")
        cls._temporary = tempfile.TemporaryDirectory(prefix="t06-ai-live-")
        cls._runner = Path(cls._temporary.name) / "mgba_battle_core_ai_smoke"
        completed = subprocess.run(
            [
                compiler,
                "-std=c11",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(SOURCE),
                "-o",
                str(cls._runner),
                "-lmgba",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"runner compile failed:\n{completed.stdout}{completed.stderr}"
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @classmethod
    def run_once(cls) -> tuple[str, dict[str, Any]]:
        workdir = Path(cls._temporary.name)
        before = {
            path.relative_to(workdir)
            for path in workdir.rglob("*")
            if path.is_file()
        }
        environment = {
            "HOME": cls._temporary.name,
            "LC_ALL": "C",
            "LANG": "C",
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "TZ": "UTC",
        }
        argv = [
            str(cls._runner),
            str(cls._stage_rom),
            cls._rom_sha256,
            *(f"0x{cls._symbols[name]:08X}" for name in REQUIRED_SYMBOLS),
        ]
        completed = subprocess.run(
            argv,
            cwd=workdir,
            env=environment,
            text=True,
            capture_output=True,
            timeout=420,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"runner failed: rc={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        if completed.stderr:
            raise AssertionError(f"runner emitted stderr: {completed.stderr}")
        lines = completed.stdout.splitlines()
        if len(lines) != 1:
            raise AssertionError(
                f"runner output is not one JSON line: {completed.stdout!r}"
            )
        payload = json.loads(lines[0])
        after = {
            path.relative_to(workdir)
            for path in workdir.rglob("*")
            if path.is_file()
        }
        if after != before:
            raise AssertionError(f"runner retained artifacts: {sorted(after - before)}")
        return completed.stdout, payload

    def assert_payload(self, payload: dict[str, Any]) -> None:
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["fixture"], "t06_cfru_vega_ai_v1")
        self.assertEqual(payload["rom_sha256"], self._rom_sha256)
        self.assertEqual(payload["fixed_rtc_unix"], 946684800)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["warnings_errors"], 0)
        self.assertEqual(payload["artifacts_written"], [])
        self.assertEqual(payload["unreached_scenarios"], [])

        provenance = payload["provenance"]["symbols"]
        self.assertEqual(set(provenance), set(REQUIRED_SYMBOLS))
        for name in REQUIRED_SYMBOLS:
            self.assertEqual(
                assert_hex_address(self, provenance[name]), self._symbols[name]
            )

        self.assertEqual(set(payload["profiles"]), set(EXPECTED_PROFILES))
        for name, bits in EXPECTED_PROFILES.items():
            profile = payload["profiles"][name]
            self.assertEqual(profile["requested_bits"], bits)
            self.assertEqual(profile["resolved_bits"], bits)
            self.assertEqual(profile["effective_bits"], bits)
            self.assertEqual(profile["chosen_slot"], 0)
            self.assertEqual(profile["chosen_move"], 33)
            self.assertEqual(profile["target"], 0)

        scenarios = {row["name"]: row for row in payload["decision_scenarios"]}
        self.assertEqual(set(scenarios), set(EXPECTED_SCENARIOS))
        for name, expected in EXPECTED_SCENARIOS.items():
            row = scenarios[name]
            self.assertEqual(
                (row["category"], row["classification"], row["battle"]),
                expected,
            )
            self.assertEqual(row["effective_ai_flags"], 5)
            self.assertEqual(row["status"], "PASS")
            self.assertIn(row["chosen_slot"], range(4))
            self.assertGreater(row["chosen_move"], 0)
            self.assertGreaterEqual(row["legal_competing_moves"], 1)
            self.assertIn(row["target"], range(4))
            self.assertGreater(row["cycles"], 0)
            self.assertGreater(row["instructions"], 0)

        self.assertEqual(payload["action_scenarios"]["switch"]["action"], 2)
        self.assertIn(
            payload["action_scenarios"]["switch"]["parameter"], range(1, 6)
        )
        self.assertEqual(
            payload["action_scenarios"]["trainer_item"]["action"], 1
        )
        self.assertEqual(
            payload["action_scenarios"]["trainer_item"]["parameter"], 19
        )
        for row in payload["action_scenarios"].values():
            self.assertGreater(row["cycles"], 0)
            self.assertGreater(row["instructions"], 0)

        mechanics = payload["mechanic_policy_observations"]
        self.assertEqual(
            [row["mode"] for row in mechanics],
            ["STANDARD", "MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"],
        )
        for row in mechanics:
            self.assertEqual(row["effective_ai_flags"], 5)
            self.assertEqual(
                row["classification"],
                "MODE_SPECIFIC_EXACT_CANDIDATE_ACTION",
            )
            self.assertEqual(row["status"], "PASS")
            expected = EXPECTED_MECHANICS[row["mode"]]
            for field in (
                "dynamax_candidate",
                "dynamax_potential",
                "terastal_candidate",
                "terastal_potential",
                "transformed_move_source",
            ):
                self.assertEqual(row[field], expected[field])
            self.assertEqual(row["action"], 0)
            self.assertEqual(row["parameter"], 0)
            self.assertEqual(row["target"], 0)
            self.assertEqual(row["chosen_slot"], 0)
            self.assertEqual(row["chosen_move"], 52)
            mega_candidate = row["mega_candidate"]
            self.assertIsInstance(mega_candidate, str)
            assert isinstance(mega_candidate, str)
            self.assertRegex(mega_candidate, re.compile(r"^0x[0-9A-F]{8}$"))
            mega_address = int(mega_candidate, 16)
            if expected["mega_present"]:
                self.assertTrue(0x08000000 <= mega_address <= 0x09FFFFFF)
            else:
                self.assertEqual(mega_address, 0)

        cache = payload["cache_history"]
        self.assertEqual(cache["entry"], "CalculateAIPredictions")
        self.assertEqual(
            cache["mutations"],
            [
                "switch",
                "faint",
                "form",
                "item",
                "weather",
                "terrain",
                "status",
                "stat_stages",
                "pp",
                "side_condition",
            ],
        )
        self.assertEqual(cache["snapshot_size_bytes"], 720)
        self.assertFalse(cache["runner_clear_after_mutation"])
        self.assertTrue(cache["stale_snapshot_detected_before_each"])
        self.assertTrue(cache["lazy_recalculated_after_each"])
        self.assertEqual(
            cache["scope"],
            "rom_lazy_snapshot_recalculation_without_runner_clear",
        )
        self.assertEqual(cache["status"], "PASS")

        for name, cold_limit, warm_limit, battlers in (
            ("single_max_party", 3_300_000, 450_000, 2),
            ("double_four_battler", 8_000_000, 800_000, 4),
        ):
            row = payload["performance"][name]
            self.assertEqual(row["active_battlers"], battlers)
            self.assertEqual(row["party_size_per_side"], 6)
            self.assertEqual(row["action"], 0)
            self.assertRegex(row["state_fnv1a64"], re.compile(r"^[0-9a-f]{16}$"))
            self.assertEqual(row["cold"]["limit"], cold_limit)
            self.assertEqual(row["warm"]["limit"], warm_limit)
            self.assertLessEqual(row["cold"]["cycles"], cold_limit)
            self.assertLessEqual(row["warm"]["cycles"], warm_limit)
            self.assertGreater(row["cold"]["instructions"], 0)
            self.assertGreater(row["warm"]["instructions"], 0)
            self.assertEqual(row["threshold_status"], "PASS")

        inventory = payload["secondary_effect_chance_inventory"]
        for boundary in ("10", "20", "30"):
            self.assertGreater(inventory[boundary], 0)
        self.assertEqual(
            inventory["comparison_semantics"],
            "NOT_INFERRED_FROM_TABLE_INVENTORY",
        )
        self.assertEqual(
            payload["repeatability"],
            {
                "independent_process_runs_required": 2,
                "byte_identical_stdout_required": True,
            },
        )

    def test_two_independent_processes_are_byte_identical_and_pass(self) -> None:
        first_stdout, first_payload = self.run_once()
        second_stdout, second_payload = self.run_once()
        self.assertEqual(first_stdout, second_stdout)
        self.assertEqual(first_payload, second_payload)
        self.assert_payload(first_payload)


if __name__ == "__main__":
    unittest.main()
