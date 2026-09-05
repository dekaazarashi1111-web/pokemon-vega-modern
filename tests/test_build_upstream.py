from __future__ import annotations

import copy
import re
import string
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_upstream as upstream  # noqa: E402


class SandboxPathTests(unittest.TestCase):
    def test_accepts_ascii_path_on_windows_mount(self) -> None:
        path = Path("/mnt/c/CodexT01/upstream")

        responses = [
            upstream.subprocess.CompletedProcess([], 0, "/mnt/c drvfs\n"),
            upstream.subprocess.CompletedProcess([], 0, "C:\\CodexT01\\upstream\n"),
        ]
        with mock.patch.object(upstream, "_run_text", side_effect=responses) as run:
            result = upstream.safe_sandbox_root(path)
        self.assertEqual(Path(result), path)
        self.assertEqual(run.call_args_list, [
            mock.call(["/usr/bin/findmnt", "-T", "/mnt/c", "-n", "-o", "TARGET,FSTYPE"], timeout=10),
            mock.call(["/usr/bin/wslpath", "-w", str(path)], timeout=10),
        ])

    def test_rejects_unc_non_ascii_spaces_and_ext4_paths(self) -> None:
        unsafe_paths = (
            r"\\server\share\upstream",
            "//wsl.localhost/Ubuntu/home/user/upstream",
            "/mnt/c/Codex T01/upstream",
            "/mnt/c/CodexT01/上流",
            "/home/user/CodexT01/upstream",
            "/tmp/CodexT01/upstream",
        )

        for path in unsafe_paths:
            with self.subTest(path=path), self.assertRaises(ValueError):
                upstream.safe_sandbox_root(path)

    def test_rejects_dot_dot_escape_from_windows_mount(self) -> None:
        with self.assertRaises(ValueError):
            upstream.safe_sandbox_root("/mnt/c/../../tmp/CodexT01/upstream")

    def test_rejects_existing_symlink_in_parent_chain(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t01-sandbox-") as temporary:
            root = Path(temporary)
            real_parent = root / "real"
            real_parent.mkdir()
            (root / "alias").symlink_to(real_parent, target_is_directory=True)
            virtual = Path("/mnt/c/CodexT01")
            exists, is_symlink = Path.exists, Path.is_symlink

            def mapped(path):
                return root / path.relative_to(virtual) if path.is_relative_to(virtual) else path

            with mock.patch.object(Path, "exists", lambda path: exists(mapped(path))), \
                    mock.patch.object(Path, "is_symlink", lambda path: is_symlink(mapped(path))), \
                    mock.patch.object(upstream, "_run_text") as run:
                with self.assertRaisesRegex(ValueError, "祖先にsymlink"):
                    upstream.safe_sandbox_root(virtual / "alias" / "upstream")
                run.assert_not_called()

    def test_rejects_drive_letter_that_is_not_mounted(self) -> None:
        response = upstream.subprocess.CompletedProcess([], 0, "/ ext4\n")
        with mock.patch.object(upstream, "_run_text", return_value=response) as run:
            with self.assertRaisesRegex(ValueError, "mountされていません"):
                upstream.safe_sandbox_root("/mnt/z/CodexT01/upstream")
        self.assertEqual(run.call_count, 1)

    def test_rejects_ext4_even_at_the_expected_drive_mount(self) -> None:
        response = upstream.subprocess.CompletedProcess([], 0, "/mnt/c ext4\n")
        with mock.patch.object(upstream, "_run_text", return_value=response) as run:
            with self.assertRaisesRegex(ValueError, "DrvFS/9p"):
                upstream.safe_sandbox_root("/mnt/c/CodexT01/upstream")
        self.assertEqual(run.call_count, 1)

    def test_rejects_path_longer_than_windows_safe_limit(self) -> None:
        overlong = Path("/mnt/c/CodexT01") / ("a" * 241)

        responses = [
            upstream.subprocess.CompletedProcess([], 0, "/mnt/c drvfs\n"),
            upstream.subprocess.CompletedProcess([], 0, "C:\\CodexT01\\" + "a" * 241),
        ]
        with mock.patch.object(upstream, "_run_text", side_effect=responses):
            with self.assertRaisesRegex(ValueError, "長すぎます"):
                upstream.safe_sandbox_root(overlong)

    def test_rejects_windows_shell_metacharacters_used_by_acl_command(self) -> None:
        unsafe_paths = (
            "/mnt/c/CodexT01/upstream&whoami",
            "/mnt/c/CodexT01/upstream|more",
            "/mnt/c/CodexT01/upstream%USERNAME%",
            '/mnt/c/CodexT01/upstream"quoted',
        )

        for path in unsafe_paths:
            with self.subTest(path=path), self.assertRaises(ValueError):
                upstream.safe_sandbox_root(path)


class WindowsAclTests(unittest.TestCase):
    @staticmethod
    def completed(stdout: str, returncode: int = 0):
        return upstream.subprocess.CompletedProcess([], returncode, stdout)

    def test_rejects_reparse_enumeration_before_acl_changes(self) -> None:
        translated = self.completed("C:\\CodexT01\\upstream\n")
        rejected_enumeration = self.completed("descendant reparse point\n", 1)

        with mock.patch.object(
            upstream,
            "_run_text",
            side_effect=(translated, rejected_enumeration),
        ), mock.patch.object(upstream.subprocess, "run") as acl_run:
            with self.assertRaises(RuntimeError):
                upstream._protect_windows_sandbox(Path("/mnt/c/CodexT01/upstream"))

        acl_run.assert_not_called()

    def test_applies_acl_to_each_enumerated_item_then_verifies(self) -> None:
        windows_root = "C:\\CodexT01\\upstream"
        translated = self.completed(windows_root + "\n")
        enumeration = self.completed(
            f"D\t{windows_root}\nF\t{windows_root}\\BPRJ0.gba\n"
        )
        identity = self.completed("HOST\\codex")
        success = upstream.subprocess.CompletedProcess([], 0, b"")

        with mock.patch.object(
            upstream,
            "_run_text",
            side_effect=(translated, enumeration, identity),
        ), mock.patch.object(
            upstream.subprocess,
            "run",
            side_effect=(success, success, success),
        ) as acl_run:
            upstream._protect_windows_sandbox(Path("/mnt/c/CodexT01/upstream"))

        self.assertEqual(acl_run.call_count, 3)
        directory_argv = acl_run.call_args_list[0].args[0]
        file_argv = acl_run.call_args_list[1].args[0]
        verify_argv = acl_run.call_args_list[2].args[0]
        self.assertEqual(directory_argv[1], windows_root)
        self.assertIn("HOST\\codex:(OI)(CI)F", directory_argv)
        self.assertEqual(file_argv[1], windows_root + "\\BPRJ0.gba")
        self.assertIn("HOST\\codex:F", file_argv)
        self.assertIn("-EncodedCommand", verify_argv)


class CacheSafetyTests(unittest.TestCase):
    FINGERPRINT = "a" * 64

    def test_accepts_regular_cache_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            artifact = upstream._safe_cache_artifact_root(root, self.FINGERPRINT)

            self.assertEqual(
                artifact,
                root / "build" / "upstream-cache" / self.FINGERPRINT,
            )
            self.assertTrue((root / "build" / "upstream-cache").is_dir())

    def test_rejects_symlinked_cache_ancestors_artifact_and_descendants(self) -> None:
        for target_kind in ("build", "cache", "artifact", "descendant"):
            with self.subTest(target_kind=target_kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                outside = root / "outside"
                outside.mkdir()
                cache = root / "build" / "upstream-cache"
                if target_kind == "build":
                    (root / "build").symlink_to(outside, target_is_directory=True)
                elif target_kind == "cache":
                    (root / "build").mkdir()
                    cache.symlink_to(outside, target_is_directory=True)
                else:
                    cache.mkdir(parents=True)
                    artifact = cache / self.FINGERPRINT
                    if target_kind == "artifact":
                        artifact.symlink_to(outside, target_is_directory=True)
                    else:
                        artifact.mkdir()
                        (artifact / "escaped").symlink_to(outside, target_is_directory=True)

                with self.assertRaises(RuntimeError):
                    upstream._safe_cache_artifact_root(root, self.FINGERPRINT)

    def test_rejects_symlinked_lock_root_before_opening_lock_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "build" / "upstream-cache"
            cache.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir()
            (cache / ".locks").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(RuntimeError):
                upstream._fingerprint_lock(root, self.FINGERPRINT)

            self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_symlinked_individual_lock_files(self) -> None:
        cases = (
            (
                f"{self.FINGERPRINT}.lock",
                lambda root: upstream._fingerprint_lock(root, self.FINGERPRINT),
            ),
            ("publish.lock", upstream._publish_lock),
        )
        for lock_name, acquire in cases:
            with self.subTest(lock_name=lock_name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                locks = root / "build" / "upstream-cache" / ".locks"
                locks.mkdir(parents=True)
                outside = root / "outside.lock"
                (locks / lock_name).symlink_to(outside)
                handle = None
                try:
                    with self.assertRaises(RuntimeError):
                        handle = acquire(root)
                finally:
                    if handle is not None:
                        handle.close()

                self.assertFalse(outside.exists())

class RomExtensionTests(unittest.TestCase):
    def test_ff_extends_copy_without_modifying_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "clean.gba"
            destination = root / "expanded.gba"
            original = bytes((0x00, 0x12, 0xFE, 0xFF))
            source.write_bytes(original)

            upstream.extend_rom_ff(source, destination, 12)

            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(destination.read_bytes(), original + (b"\xFF" * 8))

    def test_rejects_truncation_and_in_place_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "clean.gba"
            source.write_bytes(b"original")

            with self.assertRaises(ValueError):
                upstream.extend_rom_ff(source, root / "too-small.gba", 4)
            self.assertFalse((root / "too-small.gba").exists())

            with self.assertRaises(ValueError):
                upstream.extend_rom_ff(source, source, 16)
            self.assertEqual(source.read_bytes(), b"original")


class RomLayoutTests(unittest.TestCase):
    @staticmethod
    def write_fixture(root: Path, engine: str) -> tuple[Path, Path, Path]:
        source = root / "input.gba"
        output = root / "test.gba"
        blob = root / "output.bin"
        source_data = bytearray(b"I" * 32)
        output_data = bytearray(source_data)
        blob_data = b"BLOB"
        offset = 20 if engine == "dpe" else 8
        output_data[offset : offset + len(blob_data)] = blob_data
        source.write_bytes(source_data)
        output.write_bytes(output_data)
        blob.write_bytes(blob_data)
        return source, output, blob

    def validate(self, source: Path, output: Path, blob: Path, engine: str):
        with mock.patch.multiple(
            upstream,
            ROM_SIZE=32,
            CFRU_OFFSET=8,
            DPE_OFFSET=20,
        ):
            return upstream._validate_rom_layout(source, output, blob, engine)

    def test_accepts_blob_at_fixed_offset_and_preserved_reserved_region(self) -> None:
        for engine in ("dpe", "cfru"):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as temporary:
                source, output, blob = self.write_fixture(Path(temporary), engine)

                evidence = self.validate(source, output, blob, engine)

                self.assertEqual(
                    evidence["blob_at_offset_sha256"],
                    upstream.sha256_file(blob),
                )
                self.assertEqual(
                    evidence["reserved_input_sha256"],
                    evidence["reserved_output_sha256"],
                )

    def test_rejects_output_bin_not_present_at_fixed_offset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, output, blob = self.write_fixture(Path(temporary), "cfru")
            changed = bytearray(output.read_bytes())
            changed[8] ^= 0xFF
            output.write_bytes(changed)

            with self.assertRaises(RuntimeError):
                self.validate(source, output, blob, "cfru")

    def test_rejects_modification_of_reserved_downstream_region(self) -> None:
        for engine, reserved_offset in (("dpe", 8), ("cfru", 20)):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as temporary:
                source, output, blob = self.write_fixture(Path(temporary), engine)
                changed = bytearray(output.read_bytes())
                changed[reserved_offset] ^= 0xFF
                output.write_bytes(changed)

                with self.assertRaises(RuntimeError):
                    self.validate(source, output, blob, engine)


class LiteralPatchTests(unittest.TestCase):
    def test_replaces_exactly_one_literal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.py"
            path.write_text("before\nOFFSET = 0x1800000\nafter\n", encoding="utf-8")

            upstream.apply_literal_patch(
                path,
                "OFFSET = 0x1800000",
                "OFFSET = 0x1600000",
                "DPE insertion offset",
            )

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "before\nOFFSET = 0x1600000\nafter\n",
            )

    def test_rejects_missing_or_ambiguous_literal_without_writing(self) -> None:
        cases = {
            "missing": "VALUE = 1\n",
            "ambiguous": "TOKEN\nTOKEN\n",
        }
        for label, content in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "source.txt"
                path.write_text(content, encoding="utf-8")

                with self.assertRaises((ValueError, RuntimeError)) as raised:
                    upstream.apply_literal_patch(path, "TOKEN", "REPLACED", label)

                self.assertIn(label, str(raised.exception))
                self.assertEqual(path.read_text(encoding="utf-8"), content)


class ChangedAddressMetricTests(unittest.TestCase):
    def test_counts_only_candidate_changes_and_reference_agreement(self) -> None:
        base = bytes((0, 1, 2, 3, 4, 5))
        candidate = bytes((0, 9, 2, 8, 4, 7))
        reference = bytes((0, 9, 2, 6, 4, 7))

        result = upstream.changed_address_metrics(base, candidate, reference)

        self.assertEqual(result["changed_count"], 3)
        self.assertEqual(result["reference_match_count"], 2)
        self.assertEqual(result["reference_mismatch_count"], 1)
        self.assertAlmostEqual(result["reference_match_ratio"], 2 / 3)

    def test_rejects_length_mismatch_instead_of_silently_truncating(self) -> None:
        with self.assertRaises(ValueError):
            upstream.changed_address_metrics(b"abc", b"ab", b"abc")
        with self.assertRaises(ValueError):
            upstream.changed_address_metrics(b"abc", b"abc", b"abcd")


class FactoryBehaviorObservationTests(unittest.TestCase):
    FIXTURE_ID = "t01-factory-special-abi-v1"
    FACTORY_SHA256 = "a" * 64
    CANDIDATE_SHA256 = "b" * 64
    RUNS = 2
    COMPARISONS = {
        "selection": "different",
        "bp_reward": "match",
        "eligibility": "match",
        "battle_mine_options": "match",
    }
    CASE_COUNTS = {
        "selection": 4,
        "bp_reward": 3,
        "battle_mine_options": 6,
    }

    @classmethod
    def valid_observation(cls) -> dict[str, object]:
        categories = {
            name: {
                "comparison": comparison,
                "factory": [{} for _ in range(cls.CASE_COUNTS[name])],
                "candidate": [{} for _ in range(cls.CASE_COUNTS[name])],
            }
            for name, comparison in cls.COMPARISONS.items()
            if name != "eligibility"
        }
        categories["eligibility"] = {
            "comparison": cls.COMPARISONS["eligibility"],
            "factory": {"empty_party": 0, "valid_six": 1, "egg_in_party": 0},
            "candidate": {"empty_party": 0, "valid_six": 1, "egg_in_party": 0},
        }
        matching = sum(value == "match" for value in cls.COMPARISONS.values())
        return {
            "schema_version": 1,
            "fixture_id": cls.FIXTURE_ID,
            "status": "PASS",
            "comparison_policy": "different_is_classification_not_failure",
            "artifacts_written": [],
            "repeatability": {"factory": "PASS", "candidate": "PASS", "runs": cls.RUNS},
            "roms": {
                "factory_sha256": cls.FACTORY_SHA256,
                "candidate_sha256": cls.CANDIDATE_SHA256,
            },
            **categories,
            "summary": {
                "matching_categories": matching,
                "different_categories": len(cls.COMPARISONS) - matching,
            },
        }

    def validate(self, observation: dict[str, object]) -> None:
        upstream.validate_factory_behavior_observation(
            observation,
            expected_fixture_id=self.FIXTURE_ID,
            expected_factory_sha256=self.FACTORY_SHA256,
            expected_candidate_sha256=self.CANDIDATE_SHA256,
            expected_runs=self.RUNS,
            expected_comparisons=self.COMPARISONS,
            expected_case_counts=self.CASE_COUNTS,
        )

    def test_accepts_complete_factory_behavior_contract(self) -> None:
        self.validate(self.valid_observation())

    def test_rejects_missing_battle_mine_category(self) -> None:
        observation = self.valid_observation()
        del observation["battle_mine_options"]

        with self.assertRaises(RuntimeError):
            self.validate(observation)

    def test_rejects_shortened_case_coverage(self) -> None:
        observation = self.valid_observation()
        observation["battle_mine_options"]["candidate"].pop()  # type: ignore[index,union-attr]

        with self.assertRaises(RuntimeError):
            self.validate(observation)

    def test_rejects_forged_expected_classification(self) -> None:
        observation = self.valid_observation()
        observation["selection"]["comparison"] = "match"  # type: ignore[index]

        with self.assertRaises(RuntimeError):
            self.validate(observation)

    def test_rejects_rom_hash_or_repeatability_mismatch(self) -> None:
        wrong_factory = self.valid_observation()
        wrong_factory["roms"]["factory_sha256"] = "c" * 64  # type: ignore[index]
        wrong_candidate = self.valid_observation()
        wrong_candidate["roms"]["candidate_sha256"] = "d" * 64  # type: ignore[index]
        wrong_runs = self.valid_observation()
        wrong_runs["repeatability"]["runs"] = 1  # type: ignore[index]

        for observation in (wrong_factory, wrong_candidate, wrong_runs):
            with self.subTest(observation=observation), self.assertRaises(RuntimeError):
                self.validate(observation)


class AiCycleObservationTests(unittest.TestCase):
    ROM_SHA256 = "a" * 64
    SYMBOLS = {
        "AI_TrySwitchOrUseItem": 0x09049FB0,
        "BattleAI_SetupAIData": 0x09049C50,
        "BattleAI_ChooseMoveOrAction": 0x0904C290,
        "ClearCachedAIData": 0x0904C738,
    }

    @classmethod
    def valid_observation(cls) -> dict[str, object]:
        def measurement(cycles: int, *, effective_ai_flags: int | None = None):
            result = {
                "cycles": cycles,
                "instructions": cycles // 3,
                "action": 0,
                "parameter": 0,
                "target": 0,
                "return_value": 0,
            }
            if effective_ai_flags is not None:
                result["effective_ai_flags"] = effective_ai_flags
            return result

        fixtures = {}
        thresholds = {}
        for name, battlers in (
            ("single_max_party", 2),
            ("double_four_battler", 4),
        ):
            action_cold = measurement(1_000)
            action_warm = measurement(100)
            move_cold = measurement(500, effective_ai_flags=7)
            move_warm = measurement(50, effective_ai_flags=7)
            fixtures[name] = {
                "active_battlers": battlers,
                "party_size_per_side": 6,
                "move_slots_per_active_battler": 4,
                "move_slots_per_party_member": 4,
                "moves_and_pp_nonzero": True,
                "fixture_state_fnv1a64": "0123456789abcdef",
                "threshold_status": "PASS",
                "action_stage": {"cold": action_cold, "warm": action_warm},
                "move_stage": {"cold": move_cold, "warm": move_warm},
                "total_cycles": {"cold": 1_500, "warm": 150},
            }
            thresholds[name] = {"cold_max_cycles": 2_000, "warm_max_cycles": 200}
        return {
            "status": "PASS",
            "measurement_kind": "mGBA_0.10.2_ARM7TDMI_cycles",
            "repeatability": {"runs": 2, "status": "PASS"},
            "provenance": {
                "rom_sha256": cls.ROM_SHA256,
                "symbols": {
                    name: f"0x{address:08X}" for name, address in cls.SYMBOLS.items()
                },
            },
            "thresholds": thresholds,
            "fixtures": fixtures,
        }

    def validate(self, observation: dict[str, object]) -> None:
        upstream.validate_ai_cycle_observation(
            observation,
            expected_rom_sha256=self.ROM_SHA256,
            expected_symbols=self.SYMBOLS,
            expected_runs=2,
        )

    def test_accepts_real_arm_cycle_fixture_contract(self) -> None:
        self.validate(self.valid_observation())

    def test_rejects_stale_provenance_or_repeat_contract(self) -> None:
        cases = []
        wrong_rom = self.valid_observation()
        wrong_rom["provenance"]["rom_sha256"] = "b" * 64  # type: ignore[index]
        cases.append(wrong_rom)
        wrong_symbols = self.valid_observation()
        wrong_symbols["provenance"]["symbols"]["ClearCachedAIData"] = "0x09000000"  # type: ignore[index]
        cases.append(wrong_symbols)
        wrong_runs = self.valid_observation()
        wrong_runs["repeatability"] = {"runs": 1, "status": "PASS"}
        cases.append(wrong_runs)

        for observation in cases:
            with self.subTest(observation=observation), self.assertRaises(RuntimeError):
                self.validate(observation)

    def test_rejects_non_move_non_full_smart_or_false_threshold_pass(self) -> None:
        cases = []
        switched = self.valid_observation()
        switched["fixtures"]["single_max_party"]["action_stage"]["cold"]["action"] = 2  # type: ignore[index]
        cases.append(switched)
        basic_only = self.valid_observation()
        basic_only["fixtures"]["double_four_battler"]["move_stage"]["warm"]["effective_ai_flags"] = 1  # type: ignore[index]
        cases.append(basic_only)
        over_limit = self.valid_observation()
        over_limit["thresholds"]["single_max_party"]["cold_max_cycles"] = 1_499  # type: ignore[index]
        cases.append(over_limit)
        forged_total = self.valid_observation()
        forged_total["fixtures"]["double_four_battler"]["total_cycles"]["warm"] = 149  # type: ignore[index]
        cases.append(forged_total)
        no_warm_gain = self.valid_observation()
        no_warm_gain["fixtures"]["single_max_party"]["total_cycles"]["warm"] = 1_500  # type: ignore[index]
        no_warm_gain["fixtures"]["single_max_party"]["action_stage"]["warm"]["cycles"] = 1_000  # type: ignore[index]
        no_warm_gain["fixtures"]["single_max_party"]["move_stage"]["warm"]["cycles"] = 500  # type: ignore[index]
        no_warm_gain["thresholds"]["single_max_party"]["warm_max_cycles"] = 2_000  # type: ignore[index]
        cases.append(no_warm_gain)

        for observation in cases:
            with self.subTest(observation=observation), self.assertRaises(RuntimeError):
                self.validate(copy.deepcopy(observation))

    def test_rejects_fixture_without_four_nonzero_move_slots(self) -> None:
        cases = []
        active_slots = self.valid_observation()
        active_slots["fixtures"]["single_max_party"]["move_slots_per_active_battler"] = 3  # type: ignore[index]
        cases.append(active_slots)
        party_slots = self.valid_observation()
        party_slots["fixtures"]["double_four_battler"]["move_slots_per_party_member"] = 3  # type: ignore[index]
        cases.append(party_slots)
        zero_move_or_pp = self.valid_observation()
        zero_move_or_pp["fixtures"]["single_max_party"]["moves_and_pp_nonzero"] = False  # type: ignore[index]
        cases.append(zero_move_or_pp)

        for observation in cases:
            with self.subTest(observation=observation), self.assertRaises(RuntimeError):
                self.validate(copy.deepcopy(observation))


class StableFingerprintTests(unittest.TestCase):
    def test_mapping_order_does_not_change_fingerprint(self) -> None:
        first = {
            "source": {"commit": "a" * 40, "name": "dpe"},
            "tools": {"python": "3.12.3", "gcc": "13.2.1"},
            "flags": ["-mthumb", "-Os"],
        }
        reordered = {
            "flags": ["-mthumb", "-Os"],
            "tools": {"gcc": "13.2.1", "python": "3.12.3"},
            "source": {"name": "dpe", "commit": "a" * 40},
        }

        first_digest = upstream.stable_fingerprint(first)
        reordered_digest = upstream.stable_fingerprint(reordered)

        self.assertEqual(first_digest, reordered_digest)
        self.assertRegex(first_digest, r"^[0-9a-f]{64}$")

    def test_material_value_or_list_order_change_changes_fingerprint(self) -> None:
        baseline = {"source": "dpe", "flags": ["-mthumb", "-Os"]}

        self.assertNotEqual(
            upstream.stable_fingerprint(baseline),
            upstream.stable_fingerprint({"source": "cfru", "flags": ["-mthumb", "-Os"]}),
        )
        self.assertNotEqual(
            upstream.stable_fingerprint(baseline),
            upstream.stable_fingerprint({"source": "dpe", "flags": ["-Os", "-mthumb"]}),
        )


class ReproductionIdentityTests(unittest.TestCase):
    def test_ai_iterations_are_part_of_reproduction_fingerprint(self) -> None:
        base_inputs = {
            "clean_rom_sha256": "a" * 64,
            "sources": {"dpe": "b" * 40, "cfru": "c" * 40},
            "toolchain_manifest_sha256": "d" * 64,
        }

        default = upstream.reproduction_fingerprint(base_inputs, ai_iterations=21)
        repeated = upstream.reproduction_fingerprint(base_inputs, ai_iterations=21)
        different_iterations = upstream.reproduction_fingerprint(base_inputs, ai_iterations=31)

        self.assertRegex(default, r"^[0-9a-f]{64}$")
        self.assertEqual(default, repeated)
        self.assertNotEqual(default, different_iterations)

    def test_report_identity_rejects_stale_or_cross_linked_results(self) -> None:
        current = "a" * 64
        valid_latest = {
            "fingerprint": current,
            "result": f"build/upstream-cache/{current}/result.json",
        }
        valid_result = {"fingerprint": current}

        upstream.validate_report_identity(valid_latest, valid_result, current)

        cases = (
            ({**valid_latest, "fingerprint": "b" * 64}, valid_result, current),
            (valid_latest, {"fingerprint": "b" * 64}, current),
            (valid_latest, valid_result, "b" * 64),
            (
                {
                    **valid_latest,
                    "result": f"build/upstream-cache/{'b' * 64}/result.json",
                },
                valid_result,
                current,
            ),
        )
        for latest, result, current_fingerprint in cases:
            with self.subTest(
                latest=latest["fingerprint"],
                result=result["fingerprint"],
                current=current_fingerprint,
            ), self.assertRaises(ValueError):
                upstream.validate_report_identity(latest, result, current_fingerprint)

    def test_report_rejects_build_artifact_or_source_cross_link_before_recovery(self) -> None:
        fingerprint = "a" * 64
        sources = {
            "dpe": {"commit": "d" * 40, "tree": "1" * 40, "status": "clean"},
            "cfru": {"commit": "c" * 40, "tree": "2" * 40, "status": "clean"},
        }
        current_inputs = {"repeat": 2}
        clean_hashes = {"sha256": "3" * 64}
        toolcheck = {
            "status": "PASS",
            "fixtures_status": "PASS",
            "sandbox_acl": "PASS_current_windows_user_only",
            "full_check_log_sha256": "toolcheck",
            "tools": {"pinned": True},
            "converter_fixtures": {"pinned": True},
        }
        valid_build = {
            "engine": "dpe",
            "profile": "base",
            "run": 1,
            "source_commit": sources["dpe"]["commit"],
            "source_tree": sources["dpe"]["tree"],
            "artifact_dir": (
                f"build/upstream-cache/{fingerprint}/dpe/base/run-1"
            ),
        }
        cases = {
            "different fingerprint artifact": {
                **valid_build,
                "artifact_dir": (
                    f"build/upstream-cache/{'b' * 64}/dpe/base/run-1"
                ),
            },
            "different source commit": {
                **valid_build,
                "source_commit": "e" * 40,
            },
            "different source tree": {
                **valid_build,
                "source_tree": "4" * 40,
            },
        }

        for label, crossed_build in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                result_path = (
                    root / "build" / "upstream-cache" / fingerprint / "result.json"
                )
                result_path.parent.mkdir(parents=True)
                (root / "infra").mkdir()
                (root / "infra" / "toolchain_manifest.json").write_text(
                    "{}\n", encoding="utf-8"
                )
                (root / "state").mkdir()
                (root / "state" / "source-lock.json").write_text(
                    '{"sources": []}\n', encoding="utf-8"
                )
                result = {
                    "schema_version": 1,
                    "fingerprint": fingerprint,
                    "fingerprint_inputs": current_inputs,
                    "observation_parameters": {"ai_process_runs": 2},
                    "input": clean_hashes,
                    "sources": sources,
                    "toolcheck": toolcheck,
                    "repeatability": {
                        "status": "PASS",
                        "independent_builds_per_variant": 2,
                    },
                    "ai_benchmark": {
                        "process_repeatability": {"runs": 2},
                    },
                    "builds": [crossed_build],
                }
                result_path.write_text(
                    upstream.json.dumps(result), encoding="utf-8"
                )
                latest = {
                    "fingerprint": fingerprint,
                    "result": result_path.relative_to(root).as_posix(),
                }
                args = mock.Mock(
                    config="config/project.toml",
                    sandbox_root=root / "sandbox",
                )

                def source_state(path: Path, _commit: str):
                    return sources["dpe" if path.name == "DPE-JP" else "cfru"]

                with mock.patch.multiple(
                    upstream,
                    _project_inputs=mock.Mock(
                        return_value=(root / "clean.gba", clean_hashes)
                    ),
                    _factory_reference_input=mock.Mock(
                        return_value=(root / "factory.gba", {"sha256": "5" * 64})
                    ),
                    _source_entries=mock.Mock(
                        return_value={
                            "dpe": {
                                "path": "vendor/upstream/DPE-JP",
                                "resolved_commit": sources["dpe"]["commit"],
                            },
                            "cfru": {
                                "path": "vendor/upstream/CFRU-JP",
                                "resolved_commit": sources["cfru"]["commit"],
                            },
                        }
                    ),
                    _source_state=mock.Mock(side_effect=source_state),
                    safe_sandbox_root=mock.Mock(return_value=root / "sandbox"),
                    _full_toolchain_check=mock.Mock(return_value="toolcheck"),
                    _protect_windows_sandbox=mock.Mock(),
                    _validate_manifest=mock.Mock(return_value={"pinned": True}),
                    _converter_fixtures=mock.Mock(return_value={"pinned": True}),
                    _fingerprint_inputs=mock.Mock(return_value=current_inputs),
                    reproduction_fingerprint=mock.Mock(return_value=fingerprint),
                    _recover_artifact=mock.Mock(),
                ):
                    with self.assertRaises(RuntimeError):
                        upstream._report_locked(args, root, latest)
                    upstream._recover_artifact.assert_not_called()


class JsonFixtureProcessTests(unittest.TestCase):
    def run_fixture(self, program: str, *, maximum_output_bytes: int = 4096):
        with tempfile.TemporaryDirectory() as temporary:
            return upstream._run_json_fixture(
                [sys.executable, "-c", program],
                cwd=Path(temporary),
                env={},
                timeout=5,
                label="test fixture",
                maximum_output_bytes=maximum_output_bytes,
            )

    def test_accepts_exactly_one_json_object_on_stdout(self) -> None:
        result = self.run_fixture('print("{\\\"status\\\":\\\"PASS\\\"}")')

        self.assertEqual(result, {"status": "PASS"})

    def test_rejects_non_json_diagnostics_on_stdout(self) -> None:
        with self.assertRaises(RuntimeError):
            self.run_fixture('print("diagnostic")\nprint("{}")')

    def test_rejects_any_stderr_even_with_valid_json(self) -> None:
        with self.assertRaises(RuntimeError):
            self.run_fixture(
                'import sys\nprint("{}")\nprint("warning", file=sys.stderr)'
            )

    def test_rejects_output_beyond_hard_limit(self) -> None:
        with self.assertRaises(RuntimeError):
            self.run_fixture('print("x" * 10000)', maximum_output_bytes=64)


class FinalConfigAndBuildLogTests(unittest.TestCase):
    def test_effective_preprocessor_defines_apply_late_undefs(self) -> None:
        include_expanded_final_config = """
#define UNBOUND 1
#define VAR_GAME_DIFFICULTY 0x40
#define SAVE_BLOCK_EXPANSION 1
#define AI_FULL_SMART 5
/* config_t01_profile.h is expanded here, after the pinned config. */
#undef UNBOUND
#undef VAR_GAME_DIFFICULTY
"""

        defines = upstream.effective_preprocessor_defines(include_expanded_final_config)

        self.assertNotIn("UNBOUND", defines)
        self.assertNotIn("VAR_GAME_DIFFICULTY", defines)
        self.assertEqual(defines["SAVE_BLOCK_EXPANSION"], "1")
        self.assertEqual(defines["AI_FULL_SMART"], "5")

    def test_build_log_rejects_errors_hidden_behind_zero_exit(self) -> None:
        upstream.validate_build_log("Compiling...\nBuild successful.\n")

        invalid_logs = (
            "Symbol MISSING_ROUTINE missing\nBuild completed\n",
            "Error compiling. Please inspect the command above.\n",
            "There was an error inserting the event script on line 12\n",
            "Devkit not found.\n",
            'Traceback (most recent call last):\n  File "scripts/build.py", line 1\n',
        )
        for log in invalid_logs:
            with self.subTest(log=log.splitlines()[0]), self.assertRaises(
                (ValueError, RuntimeError)
            ):
                upstream.validate_build_log(log)


class GritCanonicalizerTests(unittest.TestCase):
    @staticmethod
    def canonicalizer():
        namespace = {"re": re}
        exec(upstream.GRIT_CANONICALIZER_SOURCE, namespace)
        return namespace["CanonicalizeGritLz77Padding"]

    def test_zeros_only_bytes_after_logical_lz77_stream(self) -> None:
        assembly = """@ + 8 tiles lz77 compressed
assetTiles:
    .byte 0x10,0x01,0x00,0x00,0x00,0x00,0xAB,0xCD
    .size assetTiles, .-assetTiles
"""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "asset.s"
            path.write_text(assembly, encoding="utf-8")

            self.canonicalizer()(str(path))

            self.assertIn("0x10,0x01,0x00,0x00,0x00,0x00,0x00,0x00", path.read_text())

    def test_does_not_reinterpret_uncompressed_data_starting_with_0x10(self) -> None:
        assembly = """@ + 8 tiles not compressed
assetTiles:
    .byte 0x10,0x11,0x22,0x33,0x44
    .size assetTiles, .-assetTiles
"""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "asset.s"
            path.write_text(assembly, encoding="utf-8")

            self.canonicalizer()(str(path))

            self.assertEqual(path.read_text(encoding="utf-8"), assembly)

    def test_canonicalizes_real_palette_and_map_comment_forms(self) -> None:
        cases = (
            (
                "palette",
                "assetPal",
                "@\t+ palette 18 entries, lz77 compressed",
            ),
            (
                "map",
                "assetMap",
                "@\t+ regular map (flat), lz77 compressed, 8x8 ",
            ),
        )
        for kind, label, comment in cases:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / f"{kind}.s"
                path.write_text(
                    f"{comment}\n"
                    f"{label}:\n"
                    "    .byte 0x10,0x01,0x00,0x00,0x00,0x00,0xAB,0xCD\n"
                    f"    .size {label}, .-{label}\n",
                    encoding="utf-8",
                )

                self.canonicalizer()(str(path))

                self.assertIn(
                    "0x10,0x01,0x00,0x00,0x00,0x00,0x00,0x00",
                    path.read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
