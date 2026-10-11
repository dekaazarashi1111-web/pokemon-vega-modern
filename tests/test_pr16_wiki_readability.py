"""表示境界・原本保護・資料ZIPの限定回帰。ゲーム/nativeは実行しない。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_wiki_readability as w


class ReadabilityTests(unittest.TestCase):
    def pokemon(self, hint='**回復候補**: すいとる、ねむる。'):
        return ('# リーテイル\n**固定レビュー版 R0**\n'+w.HINT+hint+'\n'+w.SUPPLY+'\n```json\n{"native":"DEFERRED_AUDIT"}\n```\n'+w.LEARN+'| 46 | こうごうせい | 直接 |\n| 4 | 技A | 持越し |\n| 条件C | 技B | 条件付き繁殖 |\n').encode()

    def fixture(self, root):
        files = {'README.md': b'# entry\n[detail](pokemon/3.md)\n', 'pokemon/3.md': b'<a id="learn"></a>\n[entry](../README.md)\n'}
        index = {'revision': 'R0.1', 'base_manifest': {'sha256': w.BASE_INDEX_SHA}, 'files': {n: w.identity(v) for n, v in sorted(files.items())}}
        index['tree_sha256'] = w.identity(w.compact(index['files']))['sha256']
        files['data/index.json'] = w.encode(index)
        w.write_files(root, files)
        return files

    def test_known_synthesis_not_hidden_by_hint(self):
        result = w.project_detail('pokemon/3.md', self.pokemon()).decode()
        self.assertNotIn('**回復候補**', result)
        self.assertIn('| 46 | こうごうせい |', result)
        self.assertIn('未分類・要全習得確認', result)

    def test_empty_hint_is_not_negative_evidence(self):
        result = w.project_detail('pokemon/3.md', self.pokemon('**回復候補**: 該当なし。')).decode()
        self.assertNotIn('該当なし', result)
        self.assertIn('#all-learning', result)

    def test_common_projection_not_species_three_special_case(self):
        for sid in (0, 3, 24, 1669, 1670):
            self.assertNotIn(w.HINT.encode(), w.project_detail(f'pokemon/{sid}.md', self.pokemon()))

    def test_learning_bytes_and_route_kinds_unchanged(self):
        raw = self.pokemon()
        projected = w.project_detail('pokemon/3.md', raw)
        self.assertEqual(raw.split(w.LEARN.encode())[1], projected.split(w.LEARN.encode())[1])

    def test_missing_boundary_rejected(self):
        with self.assertRaises(ValueError):
            w.project_detail('pokemon/3.md', self.pokemon().replace(w.HINT.encode(), b''))

    def test_duplicate_boundary_rejected(self):
        with self.assertRaises(ValueError):
            w.project_detail('pokemon/3.md', self.pokemon()+w.LEARN.encode())

    def test_move_inverse_bytes_unchanged(self):
        raw = ('```json\n{"effect":"unknown"}\n```\n'+w.INVERSE+'| direct | carry |\n').encode()
        result = w.project_detail('moves/235.md', raw)
        self.assertEqual(raw.split(w.INVERSE.encode())[1], result.split(w.INVERSE.encode())[1])
        self.assertIn(b'<details>', result)

    def test_json_content_unchanged(self):
        text = '```json\n{"handler": "未確認", "value": 0}\n```'
        result = w.collapse_json(text)
        self.assertIn(text, result)
        self.assertEqual(result.count('<details>'), 1)

    def test_conditions_unchanged(self):
        raw = '<a id="abc"></a>\n条件付き繁殖\n'.encode()
        self.assertEqual(w.project_detail('conditions/00.md', raw), raw)

    def test_raw_zero_accuracy_not_zero_percent(self):
        self.assertIn('0%とは断定しない', w.special_value(0, 'accuracy'))

    def test_special_power_not_normal_damage(self):
        for n in (0, 1):
            self.assertIn('原本'+str(n), w.special_value(n, 'power'))
        self.assertEqual(w.special_value(90, 'power'), '90')

    def test_zero_pp_not_usability_claim(self):
        self.assertIn('使用可否', w.special_value(0, 'pp'))

    def test_priority_preserved(self):
        self.assertEqual(w.special_value(-7, 'priority'), '-7')

    def test_escaping_preserves_table_structure(self):
        self.assertEqual(w.esc('a|b\nc[1]'), 'a&#124;b<br>c&#91;1&#93;')

    def test_internal_links_and_explicit_anchor(self):
        files = {'README.md': b'[go](p/3.md#learn)', 'p/3.md': b'<a id="learn"></a>\n[back](../README.md)'}
        self.assertEqual(w.validate_links(files), 2)

    def test_missing_link_rejected(self):
        with self.assertRaises(ValueError):
            w.validate_links({'README.md': b'[missing](missing.md)'})

    def test_missing_anchor_rejected(self):
        with self.assertRaises(ValueError):
            w.validate_links({'README.md': b'[missing](#none)'})

    def test_external_link_rejected(self):
        with self.assertRaises(ValueError):
            w.validate_links({'README.md': b'[external](https://example.invalid/x)'})

    def test_traversal_absolute_binary_rejected(self):
        for name in ('../x.md', '/x.md', 'a/../../x.json', 'a\\x.md', 'a//x.md', 'game.gba', '.git/config', 'save.sav'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                w.path_ok(name)

    def test_presentation_hints_not_game_semantics(self):
        files = {n: b'{}\n' for n in ('data/moves.jsonl', 'data/abilities.jsonl', 'data/mechanics.json', 'data/active_sources.json')}
        files['data/species.jsonl'] = w.compact({'id': 3, 'base_stats': {'hp': 76}, 'role_search_hints': {'healing': [71, 156]}})
        new = copy.deepcopy(files)
        new['data/species.jsonl'] = w.compact({'id': 3, 'base_stats': {'hp': 76}})
        self.assertEqual(w.game_projection(files), w.game_projection(new))
        new['data/species.jsonl'] = w.compact({'id': 3, 'base_stats': {'hp': 77}})
        self.assertNotEqual(w.game_projection(files), w.game_projection(new))

    def test_write_identical_bytes_keeps_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            files = self.fixture(root)
            before = {p: p.stat().st_mtime_ns for p in (root/w.OUT).rglob('*') if p.is_file()}
            w.write_files(root, files)
            self.assertEqual(before, {p: p.stat().st_mtime_ns for p in before})

    def test_stale_output_not_silently_deleted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            with self.assertRaises(ValueError):
                w.write_files(root, {'README.md': b'# entry'})

    def test_output_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'docs').symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                w.write_files(root, {'README.md': b'# entry'})

    def test_member_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            (root/w.OUT/'README.md').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                w.read_output(root)

    def test_extra_member_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            (root/w.OUT/'extra.md').write_bytes(b'extra')
            with self.assertRaises(ValueError):
                w.read_output(root)

    def test_package_roundtrip_determinism_and_allowlist(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            files = self.fixture(root)
            a = w.package(root, root/'a.zip')
            b = w.package(root, root/'b.zip')
            self.assertEqual(a['sha256'], b['sha256'])
            self.assertTrue(a['expanded_verified'])
            self.assertFalse(a['private_inputs_included'])
            with zipfile.ZipFile(root/'a.zip') as z:
                self.assertEqual(len(z.namelist()), len(files))
                self.assertTrue(all(n.startswith('r0.1-6e88a021/') for n in z.namelist()))

    def test_package_cannot_write_inside_fixed_wiki(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            with self.assertRaises(ValueError):
                w.package(root, root/w.OUT/'bad.zip')

    def test_base_manifest_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/w.BASE/'data').mkdir(parents=True)
            (root/w.BASE/'data/index.json').write_bytes(b'{}')
            with self.assertRaises(ValueError):
                w.load_base(root)


if __name__ == '__main__':
    unittest.main()
