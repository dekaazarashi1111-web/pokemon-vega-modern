from __future__ import annotations

import csv
import hashlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.engine.cfru_battle_patchset import (
    ALLOWED_AUDIT_CLASSIFICATIONS,
    CONTROL_FILE_HASHES,
    EXPECTED_AUDIT_SHA256,
    EXPECTED_DOMAIN_COUNTS,
    EXPECTED_PATCHSET_WRITE_COUNT,
    EXPECTED_PROFILE,
    EXPECTED_WRITE_IDS_SHA256,
    BattlePatchsetError,
    build_patchset,
    classify_control_sections,
    render_filtered_control_files,
    select_battle_audit_rows,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor/upstream/CFRU-JP"
AUDIT = ROOT / "reports/generated/address_audit.csv"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CfruBattlePatchsetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.patchset = build_patchset(SOURCE, AUDIT)

    def test_fixed_write_id_count_and_classification_contract(self) -> None:
        patchset = self.patchset
        manifest = patchset.manifest()
        self.assertEqual(len(patchset.writes), EXPECTED_PATCHSET_WRITE_COUNT)
        self.assertEqual(manifest["write_ids_sha256"], EXPECTED_WRITE_IDS_SHA256)
        self.assertEqual(patchset.domain_counts, dict(EXPECTED_DOMAIN_COUNTS))
        self.assertEqual(
            patchset.kind_counts,
            {
                "byte_replacement": 298,
                "hook": 217,
                "repoint": 78,
                "repointall": 251,
                "routine_pointer": 39,
                "special_insert": 72,
            },
        )
        self.assertEqual(patchset.classification_counts, {"CFRU": 774, "PORT": 181})
        self.assertTrue(
            set(patchset.classification_counts).issubset(ALLOWED_AUDIT_CLASSIFICATIONS)
        )
        self.assertEqual(len(patchset.omitted_write_ids), 955)
        self.assertEqual(len(patchset.writes) + len(patchset.omitted_write_ids), 1910)
        self.assertEqual(dict(patchset.input_hashes)["address_audit.csv"], EXPECTED_AUDIT_SHA256)
        self.assertEqual(
            {key: dict(patchset.input_hashes)[key] for key in CONTROL_FILE_HASHES},
            dict(CONTROL_FILE_HASHES),
        )
        selected_rows = select_battle_audit_rows(SOURCE, AUDIT)
        self.assertEqual(len(selected_rows), EXPECTED_PATCHSET_WRITE_COUNT)
        self.assertEqual(
            tuple(row["write_id"] for row in selected_rows), patchset.write_ids
        )
        self.assertTrue(all(row["vega_value"] for row in selected_rows))

    def test_every_source_section_is_explicitly_classified(self) -> None:
        sections = self.patchset.sections
        self.assertGreater(len(sections), 180)
        self.assertTrue(
            all(
                section.disposition in {"INCLUDE", "MIXED", "EXCLUDE"}
                for section in sections
            )
        )
        self.assertTrue(all(section.reason for section in sections))
        self.assertTrue(
            any(
                section.title == "Save Expansion Hooks"
                and section.disposition == "EXCLUDE"
                for section in sections
            )
        )
        self.assertTrue(
            any(
                section.title == "Other Battle Stuff"
                and section.disposition == "INCLUDE"
                for section in sections
            )
        )
        self.assertTrue(
            any(
                section.title == "Specials" and section.disposition == "MIXED"
                for section in sections
            )
        )

    def test_unknown_section_is_rejected_without_relying_on_hash_gate(self) -> None:
        texts = {name: (SOURCE / name).read_text(encoding="utf-8") for name in CONTROL_FILE_HASHES}
        texts["hooks"] += "\n##Future Story Hook\nFutureStoryHook 08000000 0\n"
        with self.assertRaisesRegex(BattlePatchsetError, "未知section"):
            classify_control_sections(texts)

    def test_render_is_deterministic_and_side_effect_free(self) -> None:
        inputs = [*(SOURCE / name for name in CONTROL_FILE_HASHES), AUDIT]
        before = {path: _digest(path) for path in inputs}
        first = render_filtered_control_files(SOURCE, AUDIT)
        second = render_filtered_control_files(SOURCE, AUDIT)
        after = {path: _digest(path) for path in inputs}
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(set(first), set(CONTROL_FILE_HASHES))
        # render()は内部tupleを公開せず、新しいdictを返す。
        first["hooks"] = "tampered"
        self.assertNotEqual(self.patchset.render()["hooks"], "tampered")

    def test_rendered_files_keep_battle_paths_and_drop_vega_owned_paths(self) -> None:
        rendered = self.patchset.render()
        hooks = rendered["hooks"]
        self.assertIn("BattleAI_DoAIProcessing", hooks)
        self.assertIn("BattleSetup_StartTrainerBattle", hooks)
        self.assertIn("ChooseFaintedMonHook", hooks)
        self.assertIn("RaidBossHPColourHook", hooks)
        for forbidden in (
            "SaveWriteToFlash", "SetUpStartMenu", "GiveEggFromDaycare",
            "FollowMe_SetStateHook", "StandardWildEncounter", "DynamicWhiteoutMap",
            "CreateSummaryScreenGigantamaxIconHook", "CreateBoxMonHook",
        ):
            self.assertNotIn(forbidden, hooks)

        replacements = rendered["bytereplacement"]
        self.assertIn("0801340C", replacements)
        self.assertIn("0800DDA0", replacements)
        self.assertIn("0802FFDA", replacements)
        for decryption_site in (
            "0803F0B8", "0803F096", "0803F09C", "0803F072", "0803F078",
            "0803F500", "0803FC12", "080401DA",
        ):
            self.assertIn(decryption_site, replacements)
        for save_key_site in ("0804B81A", "0804B81C", "0804B8F6"):
            self.assertNotIn(save_key_site, replacements)
        for experience_stride_site in (
            "0802F6B4", "0802F814", "0802F91C", "0803D364", "0803DF5E",
            "0803DFCA", "08040F50", "08043246", "080497B0", "080E8E38",
            "080E8F98", "080E90A0", "08136E92", "0813B1D2", "08159C70",
            "08159DD0", "08159ED8",
        ):
            self.assertIn(experience_stride_site, replacements)
        for max_level_ui_site in ("08042D94", "0811F1BE", "08136EA8"):
            self.assertNotIn(max_level_ui_site, replacements)
        for forbidden in ("080DB5C8", "08055E38", "0808EF08", "080458D4"):
            self.assertNotIn(forbidden, replacements)

        repoints = rendered["repoints"]
        self.assertIn("gBattleScriptingCommandsTable", repoints)
        self.assertIn("gExperienceTables", repoints)
        self.assertIn("gBattleAnims_Special", repoints)
        for forbidden in (
            "gSaveSectionOffsets", "SystemScript_ObtainItem", "EventScript_TrainerSpottedInitiate",
            "SurfPal", "TradeBallTiles", "sStartMenuActionTable",
        ):
            self.assertNotIn(forbidden, repoints)

        routine = rendered["routinepointers"]
        self.assertIn("sp052_GenerateFacilityTrainer", routine)
        self.assertIn("sp11C_GiveRaidBattleRewards", routine)
        self.assertIn("sp12F_SetHyperTraining", routine)
        self.assertIn("VBlankCB_Battle", routine)
        for forbidden in ("ScrCmd_message", "sp0AE_ClearFlag", "NpcSpawnWithTemplate", "scrB3_CheckCoins"):
            self.assertNotIn(forbidden, routine)

        special = rendered["special_inserts.asm"]
        self.assertEqual(
            sum(line.lstrip().startswith(".org ") for line in special.splitlines()),
            72,
        )
        rendered_orgs = [
            line.strip().split(",", 1)[0]
            for line in special.splitlines()
            if line.lstrip().startswith(".org ")
        ]
        self.assertEqual(len(rendered_orgs), len(set(rendered_orgs)))
        self.assertNotIn("/*", special)
        self.assertNotIn("*/", special)
        self.assertIn(".org 0x11DFA", special)
        self.assertIn(".org 0x39908", special)
        self.assertIn(".org 0x33B48", special)
        self.assertIn(".org 0x33D08", special)
        for forbidden in (
            ".org 0x890", ".org 0x7316", ".org 0x58186", ".org 0xDBE2A",
            ".org 0x1BC846", ".org 0x126C16",
        ):
            self.assertNotIn(forbidden, special)

    def test_rendered_record_lines_equal_selected_audit_records(self) -> None:
        rendered = self.patchset.render()
        for filename in ("hooks", "bytereplacement", "repoints", "repointall", "routinepointers"):
            source_lines = (SOURCE / filename).read_text(encoding="utf-8").splitlines()
            expected_lines = sorted(
                {row.source_line for row in self.patchset.writes if row.filename == filename}
            )
            expected = [source_lines[line - 1].strip() for line in expected_lines]
            observed = [
                raw.strip()
                for raw in rendered[filename].splitlines()
                if raw.strip()
                and not raw.lstrip().startswith("#")
            ]
            self.assertEqual(observed, expected, filename)

        expected_orgs = sorted(
            {row.source_line for row in self.patchset.writes if row.filename == "special_inserts.asm"}
        )
        source_lines = (SOURCE / "special_inserts.asm").read_text(encoding="utf-8").splitlines()
        expected_org_text = [source_lines[line - 1].strip() for line in expected_orgs]
        observed_org_text = [
            raw.strip()
            for raw in rendered["special_inserts.asm"].splitlines()
            if re_match_org(raw)
        ]
        self.assertEqual(observed_org_text, expected_org_text)

    def test_source_and_audit_hash_drift_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t06-patchset-test-") as temporary:
            temporary_path = Path(temporary)
            source = temporary_path / "CFRU-JP"
            source.mkdir()
            for name in CONTROL_FILE_HASHES:
                shutil.copyfile(SOURCE / name, source / name)
            audit = temporary_path / "address_audit.csv"
            shutil.copyfile(AUDIT, audit)

            (source / "hooks").write_text(
                (source / "hooks").read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(BattlePatchsetError, "control hash不一致"):
                build_patchset(source, audit)

            shutil.copyfile(SOURCE / "hooks", source / "hooks")
            audit.write_bytes(audit.read_bytes() + b"\n")
            with self.assertRaisesRegex(BattlePatchsetError, "address audit hash不一致"):
                build_patchset(source, audit)

    def test_unknown_or_unclassified_audit_write_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t06-patchset-audit-") as temporary:
            temporary_path = Path(temporary)
            source = temporary_path / "CFRU-JP"
            source.mkdir()
            for name in CONTROL_FILE_HASHES:
                shutil.copyfile(SOURCE / name, source / name)

            rows = list(csv.DictReader(io.StringIO(AUDIT.read_text(encoding="utf-8"))))
            fieldnames = list(rows[0])
            target = next(
                row
                for row in rows
                if row["engine"] == "cfru"
                and row["profile"] == EXPECTED_PROFILE
                and row["source_file"].endswith("/hooks")
                and row["symbol"] == "BattleAI_DoAIProcessing"
            )
            target["classification"] = "UNKNOWN"
            audit = temporary_path / "address_audit.csv"
            with audit.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(BattlePatchsetError, "分類を拒否"):
                build_patchset(
                    source, audit, verify_fixed_hashes=False, enforce_output_contract=False
                )

            target["classification"] = "CFRU"
            target["source_file"] = "vendor/upstream/CFRU-JP/storyhooks"
            with audit.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(BattlePatchsetError, "未知CFRU write source"):
                build_patchset(
                    source, audit, verify_fixed_hashes=False, enforce_output_contract=False
                )

    def test_unreviewed_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(BattlePatchsetError, "未監査profile"):
            build_patchset(SOURCE, AUDIT, profile="minimal")


def re_match_org(raw: str) -> bool:
    return raw.lstrip().startswith(".org ")


if __name__ == "__main__":
    unittest.main()
