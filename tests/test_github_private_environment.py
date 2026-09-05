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
                            "source": "userfile",
                            "destination": "userfile",
                            "exclude": [],
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
        return temporary, root, config_path

    def test_build_is_deterministic_and_restore_verifies_every_file(self) -> None:
        temporary, root, config_path = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        config = private_env._load_config(config_path)
        first = root / "first/inputs.zip"
        second = root / "second/inputs.zip"
        result = private_env.build_archive(root, config["archives"][0], first)
        private_env.build_archive(root, config["archives"][0], second)
        self.assertEqual(sha256(first), sha256(second))

        config["archives"][0]["size"] = result["size"]
        config["archives"][0]["sha256"] = result["sha256"]
        (root.parent / "PRIVATE_INPUTS/roms/clean.gba").unlink()
        (root / "userfile/imports/design.txt").unlink()
        restored = private_env.restore_archive(
            root, first, config["archives"][0], force=False
        )
        self.assertEqual(restored["restored"], 2)
        self.assertEqual(
            private_env.restore_links(root, config, force=False), 1
        )
        self.assertEqual((root / "inputs/private/clean.gba").read_bytes(), b"owned-rom")
        self.assertEqual(
            (root / "userfile/imports/design.txt").read_text(encoding="utf-8"),
            "design",
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


if __name__ == "__main__":
    unittest.main()
