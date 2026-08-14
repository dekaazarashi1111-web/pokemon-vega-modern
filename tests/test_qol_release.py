from __future__ import annotations

import hashlib
import json
import unittest

from scripts import build_qol_release


class QolReleaseIntegrationTest(unittest.TestCase):
    def test_stage_chain_is_exact_and_save_layout_is_not_extended(self) -> None:
        chain = build_qol_release.validate_stage_chain()
        self.assertEqual([row["stage"] for row in chain["rows"]], list(range(20, 26)))
        self.assertEqual(chain["final_sha256"], hashlib.sha256(
            (build_qol_release.ROOT / build_qol_release.STAGE).read_bytes()
        ).hexdigest())
        self.assertEqual(
            chain["save_contract"]["new_serialized_fields_after_stage20"], 0
        )

    def test_published_fixture_uses_one_final_rom_for_every_component(self) -> None:
        fixture = build_qol_release.validate_published_fixture()
        self.assertEqual(len(fixture["components"]), 8)
        self.assertTrue(all(
            component["rom_sha256"] == fixture["rom_sha256"]
            for component in fixture["components"].values()
        ))
        self.assertTrue(all(fixture["continuous_save_contract"].values()))

    def test_check_mode_has_no_artifact_drift(self) -> None:
        outputs = build_qol_release.collect_outputs()
        for relative, raw in outputs.items():
            self.assertEqual((build_qol_release.ROOT / relative).read_bytes(), raw)
        fixture = json.loads(outputs[build_qol_release.FIXTURE.as_posix()])
        self.assertEqual(fixture["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
