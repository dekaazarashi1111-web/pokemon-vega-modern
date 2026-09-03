from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.rebind_vega_codex_battle_protocol import (
    detect_stage,
    rebind_protocol,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "generated/runtime/windows_box14_vault_protocol.json"
INSTALLER = ROOT / "scripts/install_vega_codex_battle_cli.sh"


class VegaCodexBattleProtocolRebindTest(unittest.TestCase):
    def test_rebind_changes_only_top_level_stage_and_rom_identity(self) -> None:
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        rom = b"stage61-test-rom\x00\x01"
        rebound = rebind_protocol(
            protocol, rom, stage=61, rom_path="windows_box14_vault.gba",
        )
        self.assertEqual(rebound["stage"], 61)
        self.assertEqual(rebound["rom"], {
            "crc32": f"{zlib.crc32(rom) & 0xFFFFFFFF:08X}",
            "path": "windows_box14_vault.gba",
            "sha256": hashlib.sha256(rom).hexdigest(),
            "size": len(rom),
        })
        self.assertEqual(rebound["mailbox"], protocol["mailbox"])
        self.assertEqual(rebound["catalog_access"], protocol["catalog_access"])
        self.assertEqual(rebound["box14_vault"], protocol["box14_vault"])

    def test_stage_detection_accepts_current_candidate_name(self) -> None:
        self.assertEqual(
            detect_stage(Path("61_critical_release_candidate.gba"), 47), 61,
        )

    def test_installer_rebinds_an_override_rom(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            temporary = Path(raw)
            rom = temporary / "61_critical_release_candidate.gba"
            rom.write_bytes(b"stage61-installer-test")
            home = temporary / "home"
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_BIN_HOME": str(home / "bin"),
                "XDG_DATA_HOME": str(home / "share"),
                "VEGA_CODEX_BATTLE_ROM_SOURCE": str(rom),
                "VEGA_CODEX_BATTLE_STAGE": "61",
            })
            subprocess.run(
                ["bash", str(INSTALLER)], cwd=ROOT, env=env,
                check=True, capture_output=True, text=True,
            )
            libexec = home / "share/vega-codex-battle/libexec"
            installed_rom = libexec / "windows_box14_vault.gba"
            installed_protocol = json.loads(
                (libexec / "windows_box14_vault_protocol.json").read_text(
                    encoding="utf-8",
                )
            )
            raw_installed = installed_rom.read_bytes()
            self.assertEqual(installed_protocol["stage"], 61)
            self.assertEqual(
                installed_protocol["rom"]["sha256"],
                hashlib.sha256(raw_installed).hexdigest(),
            )
            self.assertEqual(
                installed_protocol["rom"]["crc32"],
                f"{zlib.crc32(raw_installed) & 0xFFFFFFFF:08X}",
            )
            self.assertEqual(
                stat.S_IMODE(installed_rom.stat().st_mode), 0o600,
            )


if __name__ == "__main__":
    unittest.main()
