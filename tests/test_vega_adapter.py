#!/usr/bin/env python3
"""Focused acceptance tests for the deterministic T03 Vega adapter module."""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "overlays/vega_adapter"
MANIFEST = ROOT / "infra/toolchain_manifest.json"
ORIGIN = 0x09200000
MARKER = b"PVADAPTER_V1\0\0\0\0"
OUTPUTS = (
    "vega_adapter.bin",
    "vega_adapter.elf",
    "vega_adapter.map",
    "metadata.json",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_build(
    out_dir: Path,
    origin: int = ORIGIN,
    manifest: Path = MANIFEST,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    # The Makefile and builder must not resolve ARM tools from caller PATH.
    environment["PATH"] = "/path/pollution/that/does/not/exist"
    return subprocess.run(
        [
            "/usr/bin/make",
            "-C",
            str(MODULE),
            f"OUT_DIR={out_dir}",
            f"ROM_ORIGIN={origin:#010x}",
            f"TOOLCHAIN_MANIFEST={manifest}",
        ],
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
        check=False,
    )


class VegaAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="t03-vega-adapter-test-")
        base = Path(cls.temporary.name)
        cls.first = base / "first"
        cls.second = base / "second"
        for output in (cls.first, cls.second):
            result = run_build(output)
            if result.returncode:
                raise AssertionError(result.stdout)
        cls.metadata = json.loads(
            (cls.first / "metadata.json").read_text(encoding="utf-8")
        )
        cls.binary = (cls.first / "vega_adapter.bin").read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_two_builds_are_byte_identical_and_path_independent(self) -> None:
        for name in OUTPUTS:
            self.assertEqual(
                (self.first / name).read_bytes(),
                (self.second / name).read_bytes(),
                name,
            )
        serialized = (self.first / "metadata.json").read_text(encoding="utf-8")
        map_text = (self.first / "vega_adapter.map").read_text(encoding="utf-8")
        self.assertNotIn(self.temporary.name, serialized)
        self.assertNotIn(self.temporary.name, map_text)
        self.assertNotRegex(serialized.lower(), r"timestamp|generated_at|captured_at")

    def test_marker_header_thumb_entry_and_noop_instruction(self) -> None:
        module = self.metadata["module"]
        allocation = self.metadata["allocation"]
        self.assertEqual(self.binary[:16], MARKER)
        abi, size, entry, hooks = struct.unpack_from("<IIII", self.binary, 16)
        self.assertEqual(abi, 1)
        self.assertEqual(size, len(self.binary))
        self.assertEqual(size, 34)
        self.assertEqual(hooks, 0)
        self.assertEqual(entry, int(module["entry_address"], 0))
        self.assertEqual(entry & 1, 1)
        self.assertEqual(entry & ~1, int(module["entry_code_address"], 0))
        self.assertEqual(self.binary[32:], b"\x70\x47")  # Thumb: bx lr
        self.assertEqual(module["entry_symbol"], "vega_adapter_entry")
        self.assertEqual(module["entry_isa"], "Thumb")
        self.assertEqual(module["hook_count"], 0)
        self.assertEqual(module["hooks"], [])
        self.assertEqual(module["vega_owned_writes"], [])
        self.assertEqual(module["side_effects"], "NONE_UNREFERENCED_BX_LR")
        self.assertEqual(int(allocation["rom_origin"], 0), ORIGIN)
        self.assertEqual(int(allocation["rom_offset"], 0), ORIGIN - 0x08000000)
        self.assertEqual(allocation["section"], "vega_adapter_module")
        self.assertEqual(
            self.metadata["allocator_request"],
            {
                "name": "vega_adapter_module",
                "region": "integration_modules",
                "size": 34,
                "alignment": 4,
                "start": "0x01200000",
                "owner": "vega_adapter",
                "purpose": "T03 deterministic no-op harness module",
                "content_sha256": "16ab88fb53956eccba0cb99a9621c14e9f04282535f8c7cc74ee4b5dd010e350",
            },
        )
        self.assertEqual(
            sha256(self.binary),
            "16ab88fb53956eccba0cb99a9621c14e9f04282535f8c7cc74ee4b5dd010e350",
        )

    def test_sections_sizes_and_all_artifact_hashes_are_exact(self) -> None:
        sections = {row["name"]: row for row in self.metadata["sections"]}
        self.assertEqual(set(sections), {".vega_adapter.header", ".vega_adapter.text"})
        self.assertEqual(sections[".vega_adapter.header"]["size"], 32)
        self.assertEqual(sections[".vega_adapter.text"]["size"], 2)
        self.assertEqual(
            sections[".vega_adapter.header"]["sha256"], sha256(self.binary[:32])
        )
        self.assertEqual(
            sections[".vega_adapter.text"]["sha256"], sha256(self.binary[32:])
        )
        self.assertEqual(
            int(sections[".vega_adapter.header"]["end_exclusive"], 0),
            int(sections[".vega_adapter.text"]["start"], 0),
        )
        for name in OUTPUTS[:3]:
            artifact = self.metadata["artifacts"][name]
            data = (self.first / name).read_bytes()
            self.assertGreater(len(data), 0)
            self.assertEqual(artifact["path"], name)
            self.assertEqual(artifact["size"], len(data))
            self.assertEqual(artifact["sha256"], sha256(data))
            self.assertRegex(artifact["sha256"], r"^[0-9a-f]{64}$")
        self.assertLessEqual(len(self.binary), 64)

    def test_map_and_metadata_pin_symbols_sources_and_toolchain(self) -> None:
        map_text = (self.first / "vega_adapter.map").read_text(encoding="utf-8")
        for symbol in (
            "gVegaAdapterModuleHeader",
            "vega_adapter_entry",
            "__vega_adapter_start",
            "__vega_adapter_end",
            "__vega_adapter_hook_count",
        ):
            self.assertIn(symbol, map_text)
        for logical, digest in self.metadata["inputs"].items():
            self.assertTrue(logical.startswith("overlays/vega_adapter/"))
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertEqual(digest, sha256((ROOT / logical).read_bytes()))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        expected_tools = {
            "python",
            "arm_none_eabi_as",
            "arm_none_eabi_ld",
            "arm_none_eabi_objcopy",
            "arm_none_eabi_nm",
        }
        self.assertEqual(set(self.metadata["toolchain"]), expected_tools)
        for key in expected_tools:
            identity = self.metadata["toolchain"][key]
            if key == "python":
                self.assertEqual(identity["sha256"], sha256(Path("/usr/bin/python3").read_bytes()))
                self.assertEqual(identity["reference_sha256"], manifest["tools"][key]["sha256"])
                self.assertEqual(identity["identity_policy"], "UBUNTU_CPYTHON_PACKAGE_ABI_V1")
                self.assertEqual(identity["package"], "python3.12-minimal")
                self.assertRegex(identity["package_version"], r"^3\.12\.3-1ubuntu0\.[0-9]+$")
                self.assertEqual(identity["package_architecture"], "amd64")
                self.assertEqual(identity["soabi"], "cpython-312-x86_64-linux-gnu")
                self.assertEqual(identity["function_probe"], "PASS")
                if identity["sha256"] != identity["reference_sha256"]:
                    self.assertEqual(identity["verification"], "APT_PACKAGE_SHA256_MEMBER_SHA256_ABI")
                    self.assertRegex(identity["package_sha256"], r"^[0-9a-f]{64}$")
            else:
                self.assertEqual(identity["sha256"], manifest["tools"][key]["sha256"])

    def test_old_dpe_overlapping_and_unaligned_origins_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t03-vega-adapter-negative-") as raw:
            output = Path(raw) / "artifact"
            for origin, pattern in (
                (0x09F00000, r"integration_modules"),
                (ORIGIN + 2, r"4-byte aligned"),
            ):
                result = run_build(output, origin)
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(result.stdout, pattern)
                self.assertFalse((output / "metadata.json").exists())

    def test_tampered_tool_identity_is_rejected_before_publication(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t03-vega-adapter-tool-negative-") as raw:
            directory = Path(raw)
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            manifest["tools"]["arm_none_eabi_as"]["sha256"] = "0" * 64
            manifest_path = directory / "toolchain.json"
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True), encoding="utf-8"
            )
            output = directory / "artifact"
            result = run_build(output, manifest=manifest_path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pinned tool SHA-256 mismatch", result.stdout)
            self.assertFalse((output / "metadata.json").exists())


if __name__ == "__main__":
    unittest.main()
