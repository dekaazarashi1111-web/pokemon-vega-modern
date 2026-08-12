#!/usr/bin/env python3
"""Focused acceptance for the T04 libmGBA early-game move smoke."""

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


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_move_smoke.c"
VEGA_ROM = ROOT / "build/reference/vega.gba"
VEGA_SHA256 = "f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5"
ROOTED_EARLY_MOVES = {1, 10, 33, 39, 43, 45, 64, 116, 120, 182, 204}
BATTLE_TYPE_TRAINER = 0x0008


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def executable_pc(value: int) -> bool:
    return (
        0x02000000 <= value < 0x02040000
        or 0x03000000 <= value < 0x03008000
        or 0x08000000 <= value < 0x0A000000
    )


class MoveSmokeSourceTests(unittest.TestCase):
    def test_contract_names_synthetic_wild_direct_calls_without_trainer_claim(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("synthetic_rooted_early_wild_battle", source)
        self.assertIn("battle_kind", source)
        self.assertIn("CreateMon", source)
        self.assertIn("BattleSetup_StartWildBattle", source)
        self.assertNotIn("natural_early_trainer_battle", source)
        self.assertNotIn("trainer_battle_active", source)


@unittest.skipUnless(VEGA_ROM.is_file(), "fixed Vega ROM is unavailable")
class FixedRomMoveSmokeTests(unittest.TestCase):
    _temporary: tempfile.TemporaryDirectory[str]
    _runner: Path
    _reference_runs: list[tuple[str, dict[str, object]]] | None = None

    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("cc") is None:
            raise unittest.SkipTest("C compiler is unavailable")
        cls._temporary = tempfile.TemporaryDirectory(prefix="t04-move-smoke-")
        cls._runner = Path(cls._temporary.name) / "mgba_move_smoke"
        compiled = subprocess.run(
            [
                "cc",
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
        if compiled.returncode != 0:
            raise AssertionError(f"runner compile failed:\n{compiled.stdout}{compiled.stderr}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @classmethod
    def _run(cls, rom: Path, expected_sha256: str) -> tuple[str, dict[str, object]]:
        workdir = Path(cls._temporary.name)
        files_before = {path.relative_to(workdir) for path in workdir.rglob("*") if path.is_file()}
        environment = {
            "HOME": cls._temporary.name,
            "LC_ALL": "C",
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "TZ": "UTC",
        }
        completed = subprocess.run(
            [str(cls._runner), str(rom), expected_sha256, "300"],
            cwd=workdir,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"runner failed for {rom.name}: rc={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        if completed.stderr:
            raise AssertionError(f"runner emitted stderr: {completed.stderr}")
        lines = completed.stdout.splitlines()
        if len(lines) != 1:
            raise AssertionError(f"runner output is not one JSON line: {completed.stdout!r}")
        payload = json.loads(lines[0])
        files_after = {path.relative_to(workdir) for path in workdir.rglob("*") if path.is_file()}
        if files_after != files_before:
            raise AssertionError(f"runner retained artifacts: {sorted(files_after - files_before)}")
        return completed.stdout, payload

    @classmethod
    def _vega_twice(cls) -> list[tuple[str, dict[str, object]]]:
        if cls._reference_runs is None:
            cls._reference_runs = [cls._run(VEGA_ROM, VEGA_SHA256) for _ in range(2)]
        return cls._reference_runs

    def assert_valid_observation(self, payload: dict[str, object], expected_sha256: str) -> None:
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["fixture"], "synthetic_rooted_early_wild_battle")
        self.assertEqual(payload["battle_kind"], "WILD")
        self.assertEqual(payload["rom_sha256"], expected_sha256)
        self.assertEqual(payload["fixed_rtc_unix"], 946684800)
        self.assertEqual(payload["boot_trace_segments"], 233)
        self.assertEqual(payload["progress_frames"], 300)
        self.assertEqual(payload["warnings_errors"], 0)
        self.assertEqual(payload["artifacts_written"], [])
        self.assertTrue(payload["core_alive_after_progression"])
        self.assertTrue(payload["active_move_ids_stable"])
        self.assertEqual(
            payload["move_execution"],
            {"input": "A_x6_slot0", "player_pp_spent": True, "hp_changed": True},
        )
        self.assertEqual(
            payload["provenance"],
            {
                "field_base": "natural_T03_233_segment_trace",
                "rooted_species": {"player": 4, "enemy": 10, "level": 5},
                "direct_rom_calls": {
                    "CreateMon": "0x0803D1C1",
                    "BattleSetup_StartWildBattle": "0x0807EE2D",
                },
            },
        )
        self.assertEqual(
            payload["move_id_contract"],
            {"zero_slot_allowed": True, "nonzero_min": 1, "nonzero_max": 511},
        )

        observed_nonzero: set[int] = set()
        for phase in ("before", "after"):
            snapshot = payload[phase]
            self.assertTrue(snapshot["wild_battle_active"])
            self.assertEqual(snapshot["battle_type_flags"] & BATTLE_TYPE_TRAINER, 0)
            self.assertEqual(snapshot["active_battlers"], 2)
            self.assertEqual(snapshot["absent_flags"], 0)
            self.assertTrue(executable_pc(snapshot["pc"]))
            self.assertRegex(snapshot["ewram_iwram_fnv1a64"], re.compile(r"^[0-9a-f]{16}$"))
            self.assertEqual([row["species"] for row in snapshot["battlers"]], [4, 10])
            for battler in snapshot["battlers"]:
                self.assertGreater(battler["hp"], 0)
                self.assertEqual(len(battler["moves"]), 4)
                self.assertEqual(len(battler["pp"]), 4)
                populated = 0
                for move, pp in zip(battler["moves"], battler["pp"], strict=True):
                    if move == 0:
                        continue
                    populated += 1
                    observed_nonzero.add(move)
                    self.assertIn(move, ROOTED_EARLY_MOVES)
                    self.assertLessEqual(move, 511)
                    self.assertGreater(pp, 0)
                self.assertGreater(populated, 0)
        self.assertEqual(observed_nonzero, {33, 43, 45, 64, 116})
        self.assertNotEqual(payload["before"]["battlers"], payload["after"]["battlers"])
        self.assertTrue(
            any(
                after_pp < before_pp
                for before_pp, after_pp in zip(
                    payload["before"]["battlers"][0]["pp"],
                    payload["after"]["battlers"][0]["pp"],
                    strict=True,
                )
            )
        )
        self.assertTrue(
            any(
                before["hp"] != after["hp"]
                for before, after in zip(
                    payload["before"]["battlers"],
                    payload["after"]["battlers"],
                    strict=True,
                )
            )
        )
        self.assertNotEqual(
            payload["before"]["ewram_iwram_fnv1a64"],
            payload["after"]["ewram_iwram_fnv1a64"],
        )

    def test_fixed_vega_is_json_only_and_two_process_deterministic(self) -> None:
        first, second = self._vega_twice()
        self.assertEqual(first[0], second[0])
        self.assert_valid_observation(first[1], VEGA_SHA256)

    def test_candidate_stage_matches_reference_runtime_observation(self) -> None:
        candidates = [ROOT / "build/stages/04_moves.gba", ROOT / "build/stages/03_harness.gba"]
        candidate = next((path for path in candidates if path.is_file()), None)
        if candidate is None:
            self.skipTest("candidate stage ROM is unavailable")
        candidate_sha256 = sha256(candidate)
        _, candidate_payload = self._run(candidate, candidate_sha256)
        self.assert_valid_observation(candidate_payload, candidate_sha256)
        reference_payload = self._vega_twice()[0][1]
        for payload in (reference_payload, candidate_payload):
            self.assertEqual(
                payload["after"]["battlers"][0]["pp"][0],
                payload["before"]["battlers"][0]["pp"][0] - 1,
            )
            self.assertLess(
                payload["after"]["battlers"][1]["hp"],
                payload["before"]["battlers"][1]["hp"],
            )
        self.assertEqual(
            [row["moves"] for row in candidate_payload["after"]["battlers"]],
            [row["moves"] for row in reference_payload["after"]["battlers"]],
        )
        self.assertEqual(
            [row["pp"] for row in candidate_payload["after"]["battlers"]],
            [row["pp"] for row in reference_payload["after"]["battlers"]],
        )

    def test_wrong_rom_hash_fails_before_emulation(self) -> None:
        completed = subprocess.run(
            [str(self._runner), str(VEGA_ROM), "0" * 64, "300"],
            cwd=self._temporary.name,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("ROM SHA-256 mismatch", completed.stderr)


if __name__ == "__main__":
    unittest.main()
