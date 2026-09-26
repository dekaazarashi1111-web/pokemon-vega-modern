"""方法別の原本比較。未知行の黙殺・相互流用・span破損を拒否する。"""
import unittest
from tools.pr16_vega_original_audit import grid, wiki_methods
from tools.pr16_vega_original_baseline import SourceError, parse_tables

class AuditTests(unittest.TestCase):
    def table(self, html):
        return parse_tables(html.encode())

    def names(self):
        return {'はたく': [{'move_id': 1, 'move_key': 'MOVE_KEY_POUND', 'name_ja': 'はたく'}]}

    def test_spans_keep_original_cell_identity(self):
        data = grid(self.table('<table><tr><td rowspan="2">a</td><td>b</td></tr><tr><td>c</td></tr></table>')[0])
        self.assertEqual(data[0][0], data[1][0])
        self.assertEqual(data[1][1]['origin'], [1, 0])

    def test_span_past_end_is_rejected(self):
        with self.assertRaises(SourceError):
            grid(self.table('<table><tr><td rowspan="2">a</td></tr></table>')[0])

    def test_irregular_grid_is_rejected(self):
        with self.assertRaises(SourceError):
            grid(self.table('<table><tr><td>a</td><td>b</td></tr><tr><td>a</td></tr></table>')[0])

    def test_duplicate_level_is_not_deduplicated(self):
        tables = self.table('<h4>レベルアップ</h4><table><tr><th>Lv</th><th>技</th></tr><tr><td>1</td><td>はたく</td></tr><tr><td>1</td><td>はたく</td></tr></table>')
        result, notes = wiki_methods(tables, self.names())
        self.assertEqual([r['order'] for r in result['level_up']], [0, 1])
        self.assertFalse(any(n['method'] == 'level_up' for n in notes))

    def test_missing_method_not_claimed_empty(self):
        _, notes = wiki_methods([], self.names())
        self.assertEqual(len(notes), 4)
        self.assertTrue(all(n['kind'] == 'MISSING_OR_MULTIPLE_METHOD_TABLE' for n in notes))

    def test_unknown_move_kept_in_ledger(self):
        result, notes = wiki_methods(self.table('<h4>教え技</h4><table><tr><th>技</th></tr><tr><td>未解決技</td></tr></table>'), self.names())
        self.assertEqual(result['tutor'], [])
        self.assertTrue(any(n['kind'] == 'UNKNOWN_OR_AMBIGUOUS_MOVE' and n['source_name'] == '未解決技' for n in notes))

    def test_tm_number_is_source_number_not_runtime_slot(self):
        result, _ = wiki_methods(self.table('<h4>技マシン</h4><table><tr><th>No</th><th>技</th></tr><tr><td>技01</td><td>はたく</td></tr><tr><td>秘01</td><td>はたく</td></tr></table>'), self.names())
        self.assertEqual([(r['machine_kind'], r['machine_number']) for r in result['machine']], [('TM', 1), ('HM', 1)])
        self.assertFalse(any('runtime_slot' in r for r in result['machine']))

    def test_egg_notes_are_not_direct_learning(self):
        result, _ = wiki_methods(self.table('<h4>タマゴ技</h4><table><tr><th>技</th><th>経路</th></tr><tr><td>はたく</td><td>親→子</td></tr></table>'), self.names())
        self.assertEqual(result['egg'][0]['breeding_notes'], ['親→子'])
        self.assertEqual(result['level_up'], [])

    def test_empty_is_explicit_not_unknown_move(self):
        result, notes = wiki_methods(self.table('<h4>教え技</h4><table><tr><th>技</th></tr><tr><td>なし</td></tr></table>'), self.names())
        self.assertEqual(result['tutor'], [])
        self.assertTrue(any(n['kind'] == 'EXPLICIT_EMPTY' for n in notes))

    def test_unknown_level_cannot_become_one(self):
        result, notes = wiki_methods(self.table('<h4>レベルアップ</h4><table><tr><th>Lv</th><th>技</th></tr><tr><td>進化</td><td>はたく</td></tr></table>'), self.names())
        self.assertEqual(result['level_up'], [])
        self.assertTrue(any(n['kind'] == 'UNRECOGNIZED_LEVEL' for n in notes))


class AliasTests(unittest.TestCase):
    def fixture(self):
        import csv, io
        stream = io.StringIO()
        writer = csv.DictWriter(stream, ['id', 'vega_id', 'status', 'move_key', 'display_name'])
        writer.writeheader()
        for mid in range(1, 512):
            writer.writerow({'id': mid, 'vega_id': mid, 'status': 'FROZEN', 'move_key': f'KEY_{mid}', 'display_name': f'技{mid if mid != 511 else 1}'})
        policy = {'vega_name_overrides': {'470': {'source_name': '旧名', 'display_name': '技470', 'move_key': 'KEY_470'}},
                  'duplicate_name_resolution': {'1': {'canonical_vega_id': 1, 'duplicate_vega_ids': [1, 511]}}}
        return stream.getvalue().encode(), policy

    def test_fixed_alias_not_modern_same_name(self):
        from tools.pr16_vega_original_audit import move_lookup
        ids, names = move_lookup(*self.fixture())
        self.assertEqual(names['旧名'][0]['move_id'], 470)
        self.assertEqual(len(ids), 511)
        self.assertEqual(names['技1'][0]['move_id'], 1)
        self.assertIn(511, ids)

    def test_wrong_alias_identity_is_rejected(self):
        from tools.pr16_vega_original_audit import move_lookup
        raw, policy = self.fixture(); policy['vega_name_overrides']['470']['move_key'] = 'WRONG'
        with self.assertRaises(SourceError):
            move_lookup(raw, policy)

    def test_unapproved_duplicate_is_not_resolved(self):
        from tools.pr16_vega_original_audit import move_lookup
        raw, policy = self.fixture(); policy['duplicate_name_resolution']['1']['duplicate_vega_ids'] = [1]
        with self.assertRaises(SourceError):
            move_lookup(raw, policy)

class ReplayTests(unittest.TestCase):
    def test_check_preserves_bytes_and_mtime(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from tools.pr16_vega_original_audit import prepare, check
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'tools').mkdir()
            for n in ('pr16_vega_original_audit.py', 'pr16_vega_original_baseline.py'):
                (root/'tools'/n).write_text('fixture')
            out = root/'.local/out'
            with patch('tools.pr16_vega_original_audit.compile_evidence', return_value={'summary.json': b'{"ok":true}\n'}):
                prepare(root, root, out)
                before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir()}
                self.assertEqual(check(root, root, out), {'ok': True})
                self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir()})

    def test_check_does_not_repair_tampering(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from tools.pr16_vega_original_audit import prepare, check
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'tools').mkdir()
            for n in ('pr16_vega_original_audit.py', 'pr16_vega_original_baseline.py'):
                (root/'tools'/n).write_text('fixture')
            out = root/'.local/out'
            with patch('tools.pr16_vega_original_audit.compile_evidence', return_value={'summary.json': b'{"ok":true}\n'}):
                prepare(root, root, out)
                (out/'summary.json').write_bytes(b'corrupt')
                with self.assertRaises(SourceError):
                    check(root, root, out)
                self.assertEqual((out/'summary.json').read_bytes(), b'corrupt')

    def test_existing_output_not_overwritten(self):
        import tempfile
        from pathlib import Path
        from tools.pr16_vega_original_audit import prepare
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); out = root/'.local/out'; out.mkdir(parents=True)
            with self.assertRaises(SourceError):
                prepare(root, root, out)

    def test_symlink_output_is_rejected(self):
        import tempfile
        from pathlib import Path
        from tools.pr16_vega_original_audit import prepare
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'.local').mkdir(); out = root/'.local/out'; out.symlink_to(root)
            with self.assertRaises(SourceError):
                prepare(root, root, out)

if __name__ == '__main__':
    unittest.main()
