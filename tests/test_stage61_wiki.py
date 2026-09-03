import importlib.util
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_stage61_wiki.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("stage61_wiki_builder", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Stage61 Wiki builderを読み込めません")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage61WikiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = _load_builder()
        cls.files, cls.index = cls.builder._build()
        cls.species = [json.loads(line) for line in cls.files["data/species.jsonl"].decode().splitlines()]

    def test_active_rom_and_complete_entity_counts(self):
        self.assertEqual(
            self.index["active_rom"]["sha256"],
            "44e951e20e7985b6f4480a04ff997cc77e6305dd0945eb90cfed7e3c6d85ae4e",
        )
        self.assertEqual(self.index["counts"]["species"], 1621)
        self.assertEqual(self.index["counts"]["moves"], 1063)
        self.assertEqual(self.index["counts"]["abilities"], 312)
        self.assertEqual(self.index["counts"]["items"], 999)
        self.assertEqual(self.index["counts"]["level_move_records_raw"], 28874)
        self.assertEqual(self.index["counts"]["level_moves"], 28859)
        self.assertEqual(self.index["counts"]["egg_moves"], 8831)
        self.assertEqual(self.index["counts"]["evolutions"], 856)

    def test_runtime_consumer_slots_match_the_connected_v4_tables(self):
        self.assertEqual(self.index["counts"]["machine_runtime_slots"], 128)
        self.assertEqual(self.index["counts"]["machine_runtime_compatibilities"], 60214)
        self.assertEqual(self.index["counts"]["tutor_runtime_slots"], 64)
        self.assertEqual(self.index["counts"]["tutor_runtime_compatibilities"], 21883)
        self.assertEqual(len(self.index["runtime_move_slots"]["machine"]), 128)
        self.assertEqual(len(self.index["runtime_move_slots"]["tutor"]), 64)
        limitations = self.files["RUNTIME_LIMITATIONS.md"].decode()
        self.assertIn("128件（TM01–120＋HM01–08）", limitations)
        self.assertIn("V4の64件を全件接続", limitations)
        self.assertNotIn("実際の `gTMHMMoves` は58件", limitations)

    def test_every_species_has_page_stats_abilities_route_and_learnsets(self):
        self.assertEqual([row["id"] for row in self.species], list(range(1621)))
        for record in self.species:
            self.assertIn(record["page"], self.files)
            self.assertEqual(len(record["abilities"]), 3)
            self.assertEqual(len(record["types"]), 2)
            self.assertEqual(
                record["base_stats"]["total"],
                sum(record["base_stats"][key] for key in ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")),
            )
            self.assertTrue(record["acquisition"]["catalog_route"]["method"])
            self.assertEqual(
                set(record["learnsets"]),
                {"level_up", "egg", "machine_runtime", "tutor_runtime"},
            )

    def test_search_index_and_species_links_are_resolvable(self):
        search = [json.loads(line) for line in self.files["data/search_index.jsonl"].decode().splitlines()]
        self.assertEqual(len(search), 1621 + 1063 + 312 + 999)
        species_search = [row for row in search if row["kind"] == "species"]
        self.assertEqual(len(species_search), 1621)
        for row in search:
            self.assertIn(row["page"], self.files)
            self.assertIn(f'<a id="{row["anchor"]}"></a>', self.files[row["page"]].decode())

    def test_published_outputs_match_deterministic_build(self):
        output = ROOT / "docs/wiki/stage61"
        actual = {path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob("*") if path.is_file()}
        self.assertEqual(actual, self.files)
        report = json.loads((ROOT / "reports/generated/stage61_wiki.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["file_count"], len(self.files))

    def test_no_broken_relative_markdown_links(self):
        pattern = re.compile(r"\[[^]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")
        for relative, data in self.files.items():
            if not relative.endswith(".md"):
                continue
            parent = Path(relative).parent
            for target in pattern.findall(data.decode()):
                resolved = (ROOT / "docs/wiki/stage61" / parent / target).resolve()
                self.assertTrue(resolved.is_file(), f"壊れたlink: {relative} -> {target}")


if __name__ == "__main__":
    unittest.main()
