"""保存証拠の拒否試験だけを実行。native/ARM/codec試験は呼ばない。"""
from __future__ import annotations
import copy
import json
import unittest
from scripts import pr16_learnset_compact_record as r


class RecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=r.inputs()
        cls.files={name:(r.ROOT/r.EVIDENCE/name).read_bytes() for name in cls.config['proof_files']}

    def altered(self,name,change):
        files=dict(self.files);config=copy.deepcopy(self.config)
        value=json.loads(files[name]);change(value);files[name]=r.encode(value)
        if name!='verification.json':
            outer=json.loads(files['verification.json'])
            outer['proof_files'][name]=r.identity(files[name])
            files['verification.json']=r.encode(outer)
        config['proof_files']={p:r.identity(b) for p,b in files.items()}
        return files,config

    def reject(self,name,change):
        with self.assertRaises(ValueError):r.validate(*self.altered(name,change))

    def test_exact_proof(self):
        self.assertEqual(r.validate(self.files,self.config)['candidate'],self.config['candidate'])
    def test_missing_member(self):
        files=dict(self.files);files.pop('link.json')
        with self.assertRaises(ValueError):r.validate(files,self.config)
    def test_extra_member(self):
        with self.assertRaises(ValueError):r.validate(dict(self.files,unexpected=b'{}'),self.config)
    def test_hash_tamper(self):
        files=dict(self.files);files['link.json']+=b' '
        with self.assertRaises(ValueError):r.validate(files,self.config)
    def test_no_gameplay_promotion(self):
        self.reject('verification.json',lambda x:x.update(gameplay_e2e_accepted=True))
    def test_no_archive_promotion(self):
        self.reject('verification.json',lambda x:x.update(archive_rebound=True))
    def test_no_tutor_promotion(self):
        self.reject('verification.json',lambda x:x.update(game_tutor_connected=True))
    def test_no_accepted_native_repeat(self):
        self.reject('verification.json',lambda x:x.update(accepted_native_reruns=1))
    def test_no_accepted_host_repeat(self):
        self.reject('verification.json',lambda x:x.update(accepted_tests_rerun=1))
    def test_native_process_count(self):
        self.reject('verification.json',lambda x:x.update(native_processes=1))
    def test_source_binding(self):
        self.reject('verification.json',lambda x:x.update(source_head='0'*40))
    def test_wrong_hook(self):
        self.reject('link.json',lambda x:x['hooks'][0].update(offset=0))
    def test_wrong_p07_delegate(self):
        self.reject('link.json',lambda x:x.update(p07_archive_delegate=0x0954B281))
    def test_extra_segment(self):
        self.reject('link.json',lambda x:x['segments'].append(x['segments'][0]))
    def test_allocation_overlap(self):
        def change(x):
            x['allocation']['allocations'][1]['start']=x['allocation']['allocations'][0]['start']
        self.reject('link.json',change)
    def test_native_pp_evidence(self):
        self.reject('native11.json',lambda x:x.update(stored_four_moves_and_pp_preserved=False))
    def test_false_semantic_equivalence(self):
        self.reject('compact-audit.json',lambda x:x.update(owner_order_count_payload_actions_equal=False))
    def test_failure_history_preserved(self):
        self.reject('inherited-compact.json',lambda x:x.update(run_conclusion='success'))


class ResumePublicationTests(unittest.TestCase):
    """受入済み18試験を再実行せず、今回の固定入口退行だけを検証。"""
    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.addCleanup(patch.stopall)
        patch.object(r, 'ROOT', self.root).start()
        self.entry = self.root/r.ENTRY
        self.entry.write_text('固定入口。進捗を複製しない。\n', encoding='utf-8')
        for name in (r.STATE, r.DOC):
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'old-output')
        self.state = {'source_bindings': {r.ENTRY:r.identity(self.entry.read_bytes())},
                      'next_action': {'goal_ja':'tutor/archiveの次工程'}}
        self.render = patch('pr16_resume.render', return_value='生成された固定再開メモ\n').start()

    def test_entry_bytes_and_mtime_unchanged(self):
        before = (self.entry.read_bytes(), self.entry.stat().st_mtime_ns)
        r.publish_resume(self.state)
        self.assertEqual(before, (self.entry.read_bytes(), self.entry.stat().st_mtime_ns))

    def test_json_and_markdown_are_one_state(self):
        r.publish_resume(self.state)
        self.assertEqual(json.loads((self.root/r.STATE).read_bytes()), self.state)
        self.assertEqual((self.root/r.DOC).read_text(), self.render.return_value)
        self.render.assert_called_once_with(self.state)

    def test_stale_binding_is_rejected_without_writes(self):
        self.entry.write_text('不一致の入力', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '自動追認しない'):
            r.publish_resume(self.state)
        self.assertEqual((self.root/r.STATE).read_bytes(), b'old-output')
        self.assertEqual((self.root/r.DOC).read_bytes(), b'old-output')
        self.render.assert_not_called()

    def test_render_failure_leaves_both_outputs(self):
        self.render.side_effect = ValueError('render拒否')
        with self.assertRaises(ValueError):r.publish_resume(self.state)
        for name in (r.STATE,r.DOC):
            self.assertEqual((self.root/name).read_bytes(), b'old-output')

    def test_binding_and_input_state_not_rewritten(self):
        before = copy.deepcopy(self.state)
        r.publish_resume(self.state)
        self.assertEqual(self.state, before)

    def test_entry_is_not_a_publication_output(self):
        from unittest.mock import patch
        with patch.object(r, 'inputs', return_value={'proof_files':{}}):
            self.assertNotIn(r.ENTRY, r.owned())
            self.assertTrue({r.STATE,r.DOC,r.CP}.issubset(r.owned()))


if __name__=='__main__':unittest.main()
