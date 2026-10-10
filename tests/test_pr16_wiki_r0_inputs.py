"""R0入力監査の独立合成試験。旧Wiki/ROM/受入試験を再実行しない。"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import pr16_wiki_r0_inputs as m


class InputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.small = {'species': 3, 'moves': 4, 'abilities': 2, 'items': 5}
        self.patcher = patch.dict(m.DOMAINS, self.small, clear=True)
        self.patcher.start(); self.addCleanup(self.patcher.stop)
        self.data = {}
        for folder, names in ((m.OLD, m.OLD_DATA), (m.NEW, m.NEW_DATA)):
            for name in names:
                raw = b'{}\n'
                if folder == m.OLD and name in {'data/' + d + '.jsonl' for d in self.small}:
                    domain = Path(name).stem
                    values = [{'id': i, 'key': domain + str(i), 'name': '名称' + str(i)} for i in range(self.small[domain])]
                    if domain == 'species':
                        for r in values:
                            r['base_stats'] = {'hp': 10, 'attack': 20, 'defense': 30, 'sp_attack': 40, 'sp_defense': 50, 'speed': 60, 'total': 210}
                    raw = b''.join(json.dumps(r, ensure_ascii=False).encode() + b'\n' for r in values)
                self.data[folder + '/' + name] = raw
        self.indexes = {}
        for folder in m.CANDIDATES:
            index = {'candidate': copy.deepcopy(m.CANDIDATES[folder]), 'files': {n[len(folder)+1:]: m.identity(raw) for n, raw in self.data.items() if n.startswith(folder + '/')}, 'counts': {'species': 3, 'moves': 4, 'active_side_change': 0, 'owner_overlay_rows': 0}}
            self.indexes[folder] = index
            self.put(folder + '/data/index.json', m.encode(index))
        for n, raw in self.data.items(): self.put(n, raw)
        for n in m.CHECKPOINTS: self.put(n, b'{"status":"ACCEPTED"}\n')
        self.put(m.STATE, m.encode({'decision_id': m.DECISION, 'owner_execution_plan': {'wiki': {'review_ready': False}}, 'recording': {'legacy_log_append': {}}, 'bindings': {}}))
        self.put(m.POLICY, b'# Fixed policy\n')
        for n in ('design/run_log.md', 'design/version_log.md'): self.put(n, b'# prior log\n')

    def put(self, name, raw):
        p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)

    def index(self, folder): self.put(folder + '/data/index.json', m.encode(self.indexes[folder]))

    def audit(self): return m.inspect(self.root, m.START)[0]

    def test_deterministic_pure_read(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        a = self.audit(); b = self.audit()
        self.assertEqual(m.encode(a), m.encode(b))
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})
        self.assertFalse(a['review_ready']); self.assertIsNone(a['selected_review_candidate'])
        self.assertEqual(a['accepted_tests_rerun'], 0)

    def test_invalid_head(self):
        with self.assertRaises(ValueError): m.inspect(self.root, 'main')

    def test_candidate_mismatch(self):
        self.indexes[m.NEW]['candidate']['sha256'] = '0' * 64; self.index(m.NEW)
        with self.assertRaisesRegex(ValueError, 'identity'): self.audit()

    def test_input_hash_mismatch(self):
        self.put(m.OLD + '/data/species.jsonl', b'{}\n')
        with self.assertRaisesRegex(ValueError, 'hash'): self.audit()

    def test_missing_input(self):
        (self.root / m.NEW / 'data/supply.jsonl').unlink()
        with self.assertRaisesRegex(ValueError, '欠落'): self.audit()

    def test_binary_input(self):
        self.put(m.OLD + '/data/species.jsonl', b'\0')
        with self.assertRaisesRegex(ValueError, 'binary'): self.audit()

    def test_symlink_leaf(self):
        p = self.root / m.OLD / 'data/species.jsonl'; p.unlink(); p.symlink_to(self.root / m.STATE)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.audit()

    def test_symlink_parent(self):
        (self.root / 'redirect').symlink_to(self.root / 'content', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'): m.read(self.root, 'redirect/modernization/pr16_wiki_first_execution_plan.json')

    def test_traversal(self):
        for name in ('../x', '/etc/passwd', 'a/../b', 'a\\b', './x'):
            with self.subTest(name=name), self.assertRaises(ValueError): m.read(self.root, name)

    def test_duplicate_json_key(self):
        with self.assertRaisesRegex(ValueError, '重複'): m.load(b'{"a":1,"a":2}')

    def test_duplicate_id(self):
        raw = b'{"id":0,"key":"a","name":"a"}\n{"id":0,"key":"b","name":"b"}\n'
        with self.assertRaisesRegex(ValueError, 'ID'): m.rows(raw, 2)

    def test_bool_id(self):
        with self.assertRaisesRegex(ValueError, 'ID'): m.rows(b'{"id":false,"key":"a","name":"a"}', 1)

    def test_duplicate_key(self):
        raw = b'{"id":0,"key":"a","name":"a"}\n{"id":1,"key":"a","name":"b"}\n'
        with self.assertRaisesRegex(ValueError, 'stable key'): m.rows(raw, 2)

    def test_count(self):
        with self.assertRaisesRegex(ValueError, '件数'): m.rows(b'{}\n', 2)

    def test_empty_name(self):
        with self.assertRaisesRegex(ValueError, '表示名'): m.rows(b'{"id":0,"key":"a","name":""}', 1)

    def test_bst(self):
        path = m.OLD + '/data/species.jsonl'
        raw = self.data[path].replace(b'"total": 210', b'"total": 211')
        self.put(path, raw); self.indexes[m.OLD]['files']['data/species.jsonl'] = m.identity(raw); self.index(m.OLD)
        with self.assertRaisesRegex(ValueError, 'BST'): self.audit()

    def test_unapproved_routes(self):
        for key in ('active_side_change', 'owner_overlay_rows'):
            with self.subTest(key=key):
                self.indexes[m.NEW]['counts'][key] = 1; self.index(m.NEW)
                with self.assertRaisesRegex(ValueError, '非承認'): self.audit()
                self.indexes[m.NEW]['counts'][key] = 0; self.index(m.NEW)

    def test_successor_count(self):
        self.indexes[m.NEW]['counts']['species'] = 1; self.index(m.NEW)
        with self.assertRaisesRegex(ValueError, '後継ID'): self.audit()

    def test_append_once(self):
        n = 'design/run_log.md'; prefix = (self.root/n).read_bytes()
        block = '\n- Task: SAMPLE / 一度だけ\n'
        self.assertTrue(m.append_once(self.root, n, 'SAMPLE', block))
        self.assertFalse(m.append_once(self.root, n, 'SAMPLE', block))
        self.assertEqual((self.root/n).read_bytes(), prefix + block.encode())

    def test_duplicate_log_rejected(self):
        self.put('design/run_log.md', b'- Task: X / a\n- Task: X / b\n')
        with self.assertRaisesRegex(ValueError, '重複'): m.append_once(self.root, 'design/run_log.md', 'X', 'x')

    def test_record_is_idempotent_and_not_ready(self):
        report = self.audit()
        m.record(self.root, report, 23)
        prior = {n: (self.root/n).read_bytes() for n in ('design/run_log.md', 'design/version_log.md')}
        m.record(self.root, report, 23)
        self.assertEqual(prior, {n: (self.root/n).read_bytes() for n in prior})
        state = m.load((self.root/m.STATE).read_bytes())
        self.assertFalse(state['owner_execution_plan']['wiki']['review_ready'])
        self.assertEqual(state['recording']['legacy_log_append']['status'], 'DONE')
        raw = (self.root/m.POLICY).read_bytes()
        self.assertEqual(state['bindings'][m.POLICY]['sha256'], m.identity(raw)['sha256'])
        self.assertEqual((self.root/m.MANIFEST).read_bytes(), m.encode(report))

    def test_ready_revision_not_modified(self):
        state = m.load((self.root/m.STATE).read_bytes()); state['owner_execution_plan']['wiki']['review_ready'] = True
        self.put(m.STATE, m.encode(state))
        with self.assertRaisesRegex(ValueError, '既公開R0'): m.record(self.root, self.audit(), 23)

    def test_manifest_tamper_does_not_write(self):
        before = (self.root/m.STATE).read_bytes()
        self.put(m.NEW + '/data/index.json', b'{"candidate": null, "files": {}}')
        with self.assertRaises(ValueError): self.audit()
        self.assertEqual((self.root/m.STATE).read_bytes(), before)


if __name__ == '__main__': unittest.main()
