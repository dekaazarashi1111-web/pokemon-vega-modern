#!/usr/bin/env python3
"""工程4の外部素材取込・決定性・fail-closed条件に対するfocused test。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_asset_importer import (
    DEFAULT_MANIFEST_RELATIVE,
    DEFAULT_OUTPUT_RELATIVE,
    EXPECTED_SOURCE_COMMIT,
    P04AssetImportError,
    _assert_checkout_state,
    _canonical_json_bytes,
    _encode_gba_4bpp,
    _parse_indexed_png,
    _resolve_manifest_path,
    _resolve_private_output_root,
    _validate_relative_path,
    audit_p04_asset_import,
    build_p04_asset_import,
    install_asset_payload,
)


class ModernizationP04AssetImporterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = ROOT / ".local/modernization_sources/pokeemerald-expansion"
        if not cls.source_root.is_dir():
            raise unittest.SkipTest("commit固定済みsource checkoutがないため実素材testを省略")
        cls.build = build_p04_asset_import(ROOT, source_root=cls.source_root)

    def test_manifest_has_complete_candidate_mapping_and_private_rights_gate(self) -> None:
        manifest = self.build.manifest
        self.assertEqual("PRIVATE_USE_STAGING_WITH_DECLARED_GAPS", manifest["status"])
        self.assertEqual(EXPECTED_SOURCE_COMMIT, manifest["source"]["commit"])
        self.assertEqual(49, len(manifest["species_assets"]))
        self.assertEqual(45, len(manifest["stone_assets"]))
        self.assertEqual(49, len({item["record_key"] for item in manifest["species_assets"]}))
        self.assertEqual(49, len({item["candidate_keys"]["proposed_species_key"] for item in manifest["species_assets"]}))
        self.assertEqual(45, len({item["mega_stone_key"] for item in manifest["stone_assets"]}))
        self.assertIsNone(manifest["rights"]["root_license_file"])
        self.assertEqual([], manifest["rights"]["detected_root_license_files"])
        self.assertFalse(manifest["rights"]["redistribution_allowed"])
        self.assertFalse(manifest["rights"]["tracked_binary_assets"])
        self.assertEqual("PERSONAL_PRIVATE_USE_ONLY", manifest["rights"]["staging_scope"])

    def test_counts_source_hash_and_output_hash_are_fixed(self) -> None:
        manifest = self.build.manifest
        self.assertEqual(326, manifest["source"]["source_unique_file_count"])
        self.assertEqual(335, manifest["source"]["source_reference_count"])
        self.assertEqual(
            "d42d9d6570caf34c3dfeb39b1d524ed7ac53176aa7cf4ececb9157f139dd00f6",
            manifest["source"]["source_asset_set_sha256"],
        )
        self.assertEqual(670, manifest["output"]["payload_file_count"])
        self.assertEqual(426648, manifest["output"]["payload_total_size"])
        self.assertEqual(
            "462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c",
            manifest["output"]["asset_set_sha256"],
        )
        self.assertEqual(335, manifest["output"]["source_mirror_file_count"])
        self.assertEqual(335, manifest["output"]["gba_binary_file_count"])

    def test_gba_conversion_has_expected_dimensions_and_tile_layout(self) -> None:
        clefable = next(item for item in self.build.manifest["species_assets"] if item["record_key"] == "P04_MEGA_CLEFABLE")
        front = next(item for item in clefable["png_assets"] if item["role"] == "FRONT")
        icon = next(item for item in clefable["png_assets"] if item["role"] == "ICON")
        self.assertEqual((64, 64), (front["source"]["metadata"]["width"], front["source"]["metadata"]["height"]))
        self.assertEqual(2048, front["gba_conversion"]["size"])
        self.assertEqual(1024, icon["gba_conversion"]["size"])
        self.assertEqual("GBA_4BPP_TILES_8X8_ROW_MAJOR", front["gba_conversion"]["format"])
        source_png = self.source_root / front["source"]["relative_path"]
        metadata, pixels = _parse_indexed_png(source_png.read_bytes(), context="test front")
        converted = _encode_gba_4bpp(pixels, metadata["width"], metadata["height"])
        self.assertEqual(self.build.payload[front["gba_conversion"]["relative_path"]], converted)
        self.assertEqual(pixels[0], converted[0] & 0x0F)
        self.assertEqual(pixels[1], converted[0] >> 4)

        stone = next(item for item in self.build.manifest["stone_assets"] if item["mega_stone_key"] == "ITEM_KEY_CLEFABLITE")
        self.assertEqual(288, stone["png_asset"]["gba_conversion"]["size"])
        self.assertEqual(32, stone["palette_asset"]["gba_conversion"]["size"])

    def test_all_mega_palettes_are_consumer_ready_without_fake_colors(self) -> None:
        manifest = self.build.manifest
        self.assertEqual({"ready": 49, "required": 49}, manifest["coverage"]["gba_full_species_palette_compatibility"])
        issues = manifest["palette_coverage_issues"]
        self.assertEqual([], issues)
        self.assertEqual("NONE", manifest["output"]["normalization"]["palette_padding_or_inferred_colors"])
        readiness = {
            item["record_key"]: item["gba_consumer_measurement"]["consumer_ready"]
            for item in manifest["species_assets"]
        }
        self.assertTrue(readiness["P04_MEGA_TATSUGIRI_DROOPY"])
        self.assertTrue(readiness["P04_MEGA_TATSUGIRI_STRETCHY"])
        self.assertTrue(readiness["P04_MEGA_TATSUGIRI_CURLY"])
        tatsugiri = [
            item for item in manifest["species_assets"]
            if item["record_key"].startswith("P04_MEGA_TATSUGIRI_")
        ]
        self.assertEqual(3, len(tatsugiri))
        self.assertEqual(
            {
                (
                    "graphics/pokemon/tatsugiri/mega/normal.pal",
                    "1b16577853e69ac12363fe18e9e856ce4821f76a67d0e63b6a8d4ac85bf5965f",
                ),
            },
            {
                (
                    next(asset for asset in item["palette_assets"] if asset["role"] == "NORMAL_PALETTE")["source"]["relative_path"],
                    next(asset for asset in item["palette_assets"] if asset["role"] == "NORMAL_PALETTE")["source"]["sha256"],
                )
                for item in tatsugiri
            },
        )

    def test_winds_waves_assets_are_not_required_for_non_adopted_scope(self) -> None:
        missing = self.build.manifest["missing_assets"]
        self.assertEqual([], missing)
        excluded = self.build.manifest["excluded_non_adopted_records"]
        self.assertEqual(3, len(excluded))
        self.assertEqual(
            {"P04_SPECIES_BROWT", "P04_SPECIES_POMBON", "P04_SPECIES_GECQUA"},
            {item["record_key"] for item in excluded},
        )
        self.assertTrue(all(item["status"] == "NON_ADOPTED_USER_SCOPE" for item in excluded))
        self.assertTrue(all(item["id_assignment"] == "NOT_APPLICABLE_NON_ADOPTED" for item in excluded))
        self.assertTrue(all(item["asset_requirement"] == "NOT_REQUIRED" for item in excluded))
        self.assertEqual(
            {"covered": 0, "required": 0},
            self.build.manifest["coverage"]["winds_waves_new_species"],
        )

    def test_build_is_byte_deterministic(self) -> None:
        rebuilt = build_p04_asset_import(ROOT, source_root=self.source_root)
        self.assertEqual(_canonical_json_bytes(self.build.manifest), _canonical_json_bytes(rebuilt.manifest))
        self.assertEqual(self.build.payload, rebuilt.payload)

    def test_install_reuses_exact_output_and_rejects_contamination(self) -> None:
        sample_payload = {
            "species/P04_SAMPLE/front.png": b"sample-png",
            "species/P04_SAMPLE/front.4bpp": b"sample-tiles",
        }
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "assets"
            self.assertEqual("CREATED", install_asset_payload(output_root, sample_payload))
            self.assertEqual("REUSED_EXACT", install_asset_payload(output_root, sample_payload))
            (output_root / "foreign.bin").write_bytes(b"not-owned")
            with self.assertRaisesRegex(P04AssetImportError, "既存出力混入または欠落"):
                install_asset_payload(output_root, sample_payload)

    def test_path_traversal_and_noncanonical_paths_fail_closed(self) -> None:
        for value in ("../escape.png", "/absolute.png", "a//b.png", "a\\b.png", "./asset.png"):
            with self.subTest(value=value), self.assertRaises(P04AssetImportError):
                _validate_relative_path(value, context="test")

    def test_dirty_or_wrong_commit_checkout_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "source"
            checkout.mkdir()
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            tracked = checkout / "tracked.txt"
            tracked.write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(checkout), "add", "tracked.txt"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(checkout),
                    "-c", "user.name=P04 Test", "-c", "user.email=p04@example.invalid",
                    "commit", "-q", "-m", "fixture",
                ],
                check=True,
            )
            commit = subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            _assert_checkout_state(checkout, commit)
            with self.assertRaisesRegex(P04AssetImportError, "source HEAD不一致"):
                _assert_checkout_state(checkout, "0" * 40)
            tracked.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(P04AssetImportError, "source checkoutに変更"):
                _assert_checkout_state(checkout, commit)

    def test_default_check_is_side_effect_free(self) -> None:
        manifest_path = ROOT / DEFAULT_MANIFEST_RELATIVE
        output_root = ROOT / DEFAULT_OUTPUT_RELATIVE
        observed = [
            manifest_path,
            output_root / "species/P04_MEGA_CLEFABLE/front.png",
            output_root / "species/P04_MEGA_CLEFABLE/front.4bpp",
            output_root / "stones/ITEM_KEY_CLEFABLITE/palette.gbapal",
        ]
        before = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in observed}
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_modernization_p04_assets.py"), "--check", "--compact"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        self.assertEqual("PASS", report["status"])
        self.assertEqual("CHECK", report["mode"])
        self.assertEqual(DEFAULT_OUTPUT_RELATIVE, report["output_logical_root"])
        self.assertTrue(report["output_git_ignore_verified"])
        after = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in observed}
        self.assertEqual(before, after)

    def test_checked_manifest_and_ignored_output_match_recomputation(self) -> None:
        report = audit_p04_asset_import(ROOT, source_root=self.source_root)
        self.assertEqual("PASS", report["status"])
        self.assertEqual("VERIFIED_EXACT", report["output_state"])
        tracked = json.loads((ROOT / DEFAULT_MANIFEST_RELATIVE).read_text(encoding="utf-8"))
        self.assertEqual(self.build.manifest, tracked)


class ModernizationP04AssetImporterPureSafetyTest(unittest.TestCase):
    """外部checkoutが無くても必ず走るfail-closed test。"""

    def test_path_traversal_is_rejected_without_external_checkout(self) -> None:
        for value in ("../escape.png", "/absolute.png", "a//b.png", "a\\b.png"):
            with self.subTest(value=value), self.assertRaises(P04AssetImportError):
                _validate_relative_path(value, context="pure safety test")

    def test_output_override_cannot_claim_the_fixed_ignored_root(self) -> None:
        self.assertEqual(
            (ROOT / DEFAULT_OUTPUT_RELATIVE).resolve(),
            _resolve_private_output_root(ROOT, None),
        )
        with self.assertRaisesRegex(P04AssetImportError, "固定path"):
            _resolve_private_output_root(ROOT, ROOT / "content/modernization/assets")

    def test_output_symlink_escape_and_manifest_override_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary) / "workspace"
            external = Path(temporary) / "external"
            temporary_root.mkdir()
            external.mkdir()
            (temporary_root / "userfile").symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(P04AssetImportError, "symlink"):
                _resolve_private_output_root(temporary_root, None)

        self.assertEqual(
            ROOT / DEFAULT_MANIFEST_RELATIVE,
            _resolve_manifest_path(ROOT, None),
        )
        with self.assertRaisesRegex(P04AssetImportError, "固定path"):
            _resolve_manifest_path(ROOT, ROOT / "userfile/untracked-manifest.json")

    def test_dirty_checkout_guard_runs_without_real_upstream_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "source"
            checkout.mkdir()
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            tracked = checkout / "tracked.txt"
            tracked.write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(checkout), "add", "tracked.txt"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(checkout),
                    "-c", "user.name=P04 Test", "-c", "user.email=p04@example.invalid",
                    "commit", "-q", "-m", "fixture",
                ],
                check=True,
            )
            commit = subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            _assert_checkout_state(checkout, commit)
            tracked.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(P04AssetImportError, "source checkoutに変更"):
                _assert_checkout_state(checkout, commit)


if __name__ == "__main__":
    unittest.main()
