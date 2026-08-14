from __future__ import annotations

import io
import unittest
import zipfile

from scripts import build_release
from tools.release.bps import BpsError, apply_bps, create_bps


class BpsTests(unittest.TestCase):
    def test_round_trip_and_determinism(self) -> None:
        source = bytes((index * 37 + 11) & 0xFF for index in range(32768))
        target = bytearray(source)
        target[31:401] = b"Vega" * 92 + b"!!"
        target.extend(b"\xFF" * 131072)
        first = create_bps(source, bytes(target), metadata=b'{"version":"test"}\n')
        second = create_bps(source, bytes(target), metadata=b'{"version":"test"}\n')
        self.assertEqual(first, second)
        self.assertEqual(apply_bps(source, first), bytes(target))
        self.assertLess(len(first), 4096)

    def test_empty_and_literal_targets(self) -> None:
        for source, target in ((b"", b""), (b"abc", b"xyz"), (b"abc", b"abc")):
            with self.subTest(source=source, target=target):
                patch = create_bps(source, target)
                self.assertEqual(apply_bps(source, patch), target)

    def test_crc_and_source_identity_fail_closed(self) -> None:
        patch = create_bps(b"source", b"target")
        damaged = bytearray(patch)
        damaged[-1] ^= 1
        with self.assertRaisesRegex(BpsError, "patch CRC"):
            apply_bps(b"source", bytes(damaged))
        with self.assertRaisesRegex(BpsError, "source CRC"):
            apply_bps(b"sourcf", patch)


class ReleaseContractTests(unittest.TestCase):
    def test_final_stage_requires_complete_qol_chain(self) -> None:
        stage, metadata = build_release._validate_stage()
        self.assertEqual(len(stage), 32 * 1024 * 1024)
        self.assertEqual(metadata["task"], build_release.STAGE_TASK)
        self.assertTrue(all(metadata["acceptance"].values()))
        self.assertFalse(metadata["ram_audit"]["flash_serialized"])
        chain = build_release.build_qol_release.validate_stage_chain()
        fixture = build_release.build_qol_release.validate_published_fixture()
        self.assertEqual(chain["final_sha256"], metadata["output"]["sha256"])
        self.assertEqual(fixture["rom_sha256"], metadata["output"]["sha256"])
        self.assertTrue(all(fixture["continuous_save_contract"].values()))

    def test_factory_trial_remains_bound_below_final_stage(self) -> None:
        metadata = build_release._read_json(
            build_release.ROOT / build_release.FACILITY_STAGE_META
        )
        self.assertEqual(
            (
                metadata["contract"]["random_candidates"],
                metadata["contract"]["manual_selections"],
                metadata["contract"]["battle_count"],
                metadata["contract"]["exact_party_snapshot_bytes"],
            ),
            (6, 3, 3, 600),
        )

    def test_release_identity_is_v1_3(self) -> None:
        self.assertEqual(build_release.VERSION, "1.3.1")
        self.assertEqual(build_release.STAGE.name, "25_move_memory.gba")

    def test_release_docs_cover_feature_matrix(self) -> None:
        files = {
            name: (build_release.ROOT / path).read_bytes()
            for name, path in build_release.DOC_SOURCES.items()
        }
        rows = build_release._feature_rows()
        build_release._validate_release_docs(files, rows)
        self.assertEqual(len(rows), 23)

    def test_deterministic_archive_and_safety_scan(self) -> None:
        files = {"README_JA.md": b"release\n", "sample.bps": b"BPS1safe"}
        first = build_release._zip_bytes(files)
        second = build_release._zip_bytes(files)
        self.assertEqual(first, second)
        scan = build_release._scan_archive(first, files)
        self.assertEqual(scan["forbidden_members"], 0)

    def test_archive_rejects_rom_member(self) -> None:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr(f"{build_release.SLUG}/forbidden.gba", b"rom")
        with self.assertRaisesRegex(build_release.ReleaseError, "forbidden"):
            build_release._scan_archive(stream.getvalue(), {})


if __name__ == "__main__":
    unittest.main()
