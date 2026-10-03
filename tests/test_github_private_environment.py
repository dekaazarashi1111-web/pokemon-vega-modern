from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import github_private_environment as private_env  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GitHubPrivateEnvironmentTests(unittest.TestCase):
    def make_fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "workspace"
        root.mkdir()
        private_root = root.parent / "PRIVATE_INPUTS"
        (private_root / "roms").mkdir(parents=True)
        (private_root / "roms/clean.gba").write_bytes(b"owned-rom")
        integration_root = root.parent / "integration_inputs"
        (integration_root / "trainer-kit").mkdir(parents=True)
        (integration_root / "trainer-kit/KIT_MANIFEST.json").write_text(
            '{"source":"original"}\n', encoding="utf-8"
        )
        (root / "userfile/imports").mkdir(parents=True)
        (root / "userfile/imports/design.txt").write_text("design", encoding="utf-8")
        config = {
            "schema_version": 1,
            "release": {"tag": "private-environment-test", "title": "test"},
            "archives": [
                {
                    "name": "inputs.zip",
                    "size": 0,
                    "sha256": "-",
                    "sources": [
                        {
                            "source": "@workspace_parent/PRIVATE_INPUTS",
                            "destination": ".local/github-private-environment/PRIVATE_INPUTS",
                            "exclude": [],
                        },
                        {
                            "source": "@workspace_parent/integration_inputs",
                            "destination": "userfile/imports/integration_inputs",
                            "exclude": [],
                        },
                        {
                            "source": "userfile",
                            "destination": "userfile",
                            "exclude": ["imports/integration_inputs"],
                        },
                    ],
                }
            ],
            "input_links": [
                {
                    "path": "inputs/private/clean.gba",
                    "target": ".local/github-private-environment/PRIVATE_INPUTS/roms/clean.gba",
                }
            ],
        }
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        self.write_private_asset_manifest(root)
        return temporary, root, config_path

    @staticmethod
    def write_private_asset_manifest(root: Path) -> Path:
        manifest = root / "content/modernization/p04_asset_import_manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "output": {
                        "logical_root": "userfile/generated/modernization_p04_assets"
                    },
                    "rights": {"redistribution_allowed": False},
                }
            ),
            encoding="utf-8",
        )
        return manifest

    def test_build_is_deterministic_and_restore_verifies_every_file(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        restored_copy = root / "userfile/imports/integration_inputs/trainer-kit"
        restored_copy.mkdir(parents=True)
        (restored_copy / "KIT_MANIFEST.json").write_text(
            "stale restored copy\n", encoding="utf-8"
        )
        first = root / "first/inputs.zip"
        second = root / "second/inputs.zip"
        result = private_env.build_archive(root, config["archives"][0], first)
        private_env.build_archive(root, config["archives"][0], second)
        self.assertEqual(sha256(first), sha256(second))

        config["archives"][0]["size"] = result["size"]
        config["archives"][0]["sha256"] = result["sha256"]
        (restored_copy / "KIT_MANIFEST.json").unlink()
        restored_copy.rmdir()
        (root.parent / "PRIVATE_INPUTS/roms/clean.gba").unlink()
        (root / "userfile/imports/design.txt").unlink()
        restored = private_env.restore_archive(
            root, first, config["archives"][0], force=False
        )
        self.assertEqual(restored["restored"], 3)
        self.assertEqual(
            private_env.restore_links(root, config, force=False), 1
        )
        self.assertEqual((root / "inputs/private/clean.gba").read_bytes(), b"owned-rom")
        self.assertEqual(
            (root / "userfile/imports/design.txt").read_text(encoding="utf-8"),
            "design",
        )
        self.assertEqual(
            (root / "userfile/imports/integration_inputs/trainer-kit/KIT_MANIFEST.json")
            .read_text(encoding="utf-8"),
            '{"source":"original"}\n',
        )

    def test_secret_material_and_nested_private_key_are_rejected(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        key = root / "userfile/imports/id_ed25519"
        key.write_text("not-even-a-real-key", encoding="utf-8")
        with self.assertRaisesRegex(private_env.PrivateEnvironmentError, "秘密情報候補"):
            private_env.collect_archive_files(root, config["archives"][0])
        key.unlink()

        archive = root / "userfile/imports/toolkit.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr(
                "credentials/key",
                "-----BEGIN OPENSSH PRIVATE KEY-----\nsecret\n",
            )
        with self.assertRaisesRegex(private_env.PrivateEnvironmentError, "nested_private_key"):
            private_env.collect_archive_files(root, config["archives"][0])

    def test_restore_rejects_outer_hash_mismatch(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        output = root / "inputs.zip"
        result = private_env.build_archive(root, config["archives"][0], output)
        expected = dict(config["archives"][0])
        expected["size"] = result["size"]
        expected["sha256"] = "0" * 64
        with self.assertRaisesRegex(private_env.PrivateEnvironmentError, "外側hash"):
            private_env.restore_archive(root, output, expected, force=False)

    def test_non_redistributable_asset_root_is_rejected_fail_closed(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        self.write_private_asset_manifest(root)
        asset = root / "userfile/generated/modernization_p04_assets/species/front.png"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"private-upstream-png")

        with self.assertRaisesRegex(
            private_env.PrivateEnvironmentError, "再配布不可asset"
        ):
            private_env.collect_archive_files(root, config["archives"][0])

    def test_explicit_exclusion_keeps_non_redistributable_assets_out(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        self.write_private_asset_manifest(root)
        asset = root / "userfile/generated/modernization_p04_assets/species/front.png"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"private-upstream-png")
        userfile_source = config["archives"][0]["sources"][2]
        userfile_source["exclude"].append("generated/modernization_p04_assets")

        files = private_env.collect_archive_files(root, config["archives"][0])
        self.assertNotIn(
            "userfile/generated/modernization_p04_assets/species/front.png",
            {item.destination for item in files},
        )

    def test_repository_config_excludes_p04_private_use_assets(self) -> None:
        config = private_env._load_config(ROOT / "config/github_private_environment.json")
        inputs_archive = next(
            row for row in config["archives"]
            if row["name"] == "pokemon-vega-private-env-v1-inputs.zip"
        )
        userfile_source = next(
            row for row in inputs_archive["sources"] if row["source"] == "userfile"
        )
        self.assertIn(
            "generated/modernization_p04_assets", userfile_source["exclude"]
        )

    def test_bundle_source_root_and_file_symlinks_are_rejected(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        external = root.parent / "external"
        external.mkdir()
        (external / "plain.bin").write_bytes(b"outside-workspace")

        linked_root = root / "linked-root"
        linked_root.symlink_to(external, target_is_directory=True)
        config["archives"][0]["sources"].append(
            {"source": "linked-root", "destination": "linked", "exclude": []}
        )
        with self.assertRaisesRegex(
            private_env.PrivateEnvironmentError, "source pathのsymlink"
        ):
            private_env.collect_archive_files(root, config["archives"][0])

        config["archives"][0]["sources"].pop()
        linked_file = root / "userfile/imports/linked.bin"
        linked_file.symlink_to(external / "plain.bin")
        with self.assertRaisesRegex(
            private_env.PrivateEnvironmentError, "source内のsymlink"
        ):
            private_env.collect_archive_files(root, config["archives"][0])

    def test_missing_rights_manifest_fails_closed(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        (root / private_env.RIGHTS_MANIFESTS[0]).unlink()
        with self.assertRaisesRegex(
            private_env.PrivateEnvironmentError, "rights manifestがありません"
        ):
            private_env.collect_archive_files(root, config["archives"][0])

    def test_restore_links_rejects_parent_and_target_symlink_escape(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        target = root / ".local/github-private-environment/PRIVATE_INPUTS/roms/clean.gba"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"owned-rom")
        outside = root.parent / "outside"
        outside.mkdir()
        (root / "inputs").symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(
            private_env.PrivateEnvironmentError,
            "restore親pathがsymlink|workspace外",
        ):
            private_env.restore_links(root, config, force=True)
        self.assertFalse((outside / "private/clean.gba").exists())

        (root / "inputs").unlink()
        external_target = outside / "external.gba"
        external_target.write_bytes(b"outside")
        target.unlink()
        target.symlink_to(external_target)
        with self.assertRaisesRegex(
            private_env.PrivateEnvironmentError,
            "workspace外|targetがありません",
        ):
            private_env.restore_links(root, config, force=True)

    def test_restore_archive_rejects_manifest_parent_symlink(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        output = root / "inputs.zip"
        result = private_env.build_archive(root, config["archives"][0], output)
        expected = dict(config["archives"][0])
        expected["size"] = result["size"]
        expected["sha256"] = result["sha256"]
        outside = root.parent / "outside-manifests"
        outside.mkdir()
        manifest_link = root / ".local/github-private-environment/manifests"
        manifest_link.parent.mkdir(parents=True)
        manifest_link.symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(
            private_env.PrivateEnvironmentError, "restore親pathがsymlink"
        ):
            private_env.restore_archive(root, output, expected, force=True)
        self.assertFalse((outside / "inputs.zip.json").exists())


if __name__ == "__main__":
    unittest.main()
