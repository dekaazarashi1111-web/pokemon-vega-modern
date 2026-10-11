"""Fail closed on false termination, missing restoration and inherited guard failures."""
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile
sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_bp_loss_return_evidence as e
from tests.test_pr16_bp_battle_return import ReturnTests

class LossEvidenceTests(unittest.TestCase):
    def sample(self):
        row = ReturnTests().sample(2)
        row.update(status=e.native.STATUS,scope=e.native.SCOPE,case=e.native.CASE,
            candidate_sha256=e.CANDIDATE['sha256'],final_script_pointer=0,final_callback2=0x08055E75)
        prefix = (b'BP_CTRL label=fixture \nBP_READ name=cfru_selected_order \nBP_LAUNCH label=before-confirm \n'
            b'BP_LAUNCH label=launch-stop \nBP_READ name=enemy_party_generated \nBP_PROGRESS move=\n'
            b'BP_CTRL label=first-turn-return \n')
        def line(label, frame, cb, script, marker, snapshot, count):
            return f'BP_RETURN label={label} frame={frame} cb2={cb:08x} script={script:08x} outcome=2 marker={marker} snapshot={snapshot} count={count} bp=0 save=2\n'.encode()
        trace = prefix + line('extension-start',4200,0x080109C1,0x092CF669,2,1,3)
        trace += line('transition',8400,e.successor.ENTRY,0x092CF669,2,1,3)
        trace += line('transition',8600,0x08055E75,0x092CF66E,2,1,3)
        trace += line('transition',8700,0x08055E75,0x08192DAA,0,0,1)
        trace += line('facility-stop',9000,0x08055E75,0,0,0,1)
        return row, trace

    def test_completed_loss_script_and_full_chain(self):
        row,trace=self.sample()
        self.assertEqual(e.validate_native(json.dumps(row).encode(),trace,0),row)
        self.assertEqual(e.terminal_loss(row,trace)['restored_frame'],8700)

    def test_null_script_alone_is_not_success(self):
        row,trace=self.sample()
        with self.assertRaises(ValueError):e.terminal_loss(row,trace.split(b'BP_RETURN label=transition')[0])

    def test_other_callback_and_nonterminated_script_rejected(self):
        for k,v in [('final_callback2',0x08055F65),('final_callback2',0),('final_script_pointer',0x092CF66E)]:
            row,trace=self.sample();row[k]=v
            with self.assertRaises(ValueError):e.validate_native(json.dumps(row).encode(),trace,0)

    def test_missing_each_required_transition_rejected(self):
        row,trace=self.sample()
        for frame in (8400,8600,8700,9000):
            cut=b'\n'.join(l for l in trace.splitlines() if f'frame={frame}'.encode() not in l)+b'\n'
            with self.assertRaises(ValueError):e.terminal_loss(row,cut)

    def test_old_numeric_and_native_write_guards_still_enforced(self):
        for k,v in [('original_party_or_snapshot_bytes_verified',599),('host_write_barriers',6),
                    ('input_only_after_guard',False),('bp_earned',9),('save_counter',3),
                    ('native_bp_earning_accepted',True),('final_party_count',3),
                    ('total_frames',100000),('warnings_errors',1),('fresh_cores',0),
                    ('battle_outcome',1),('candidate_sha256',e.successor.PARENT_SHA)]:
            row,trace=self.sample();row[k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):e.validate_native(json.dumps(row).encode(),trace,0)

    def test_process_failure_cannot_be_reclassified(self):
        row,trace=self.sample()
        with self.assertRaises(ValueError):e.validate_native(json.dumps(row).encode(),trace,1)

    def test_duplicate_stop_and_wrong_terminal_trace_rejected(self):
        row,trace=self.sample()
        for changed in (trace+trace.splitlines()[-1]+b'\n',trace.replace(b'count=1 bp=0 save=2',b'count=3 bp=0 save=2')):
            with self.assertRaises(ValueError):e.terminal_loss(row,changed)

    def test_whiteout_even_after_shim_is_rejected(self):
        row,trace=self.sample()
        with self.assertRaises(ValueError):e.terminal_loss(row,trace+b'BP_RETURN cb2=08055f65\n')

    def test_unordered_or_changed_post_loss_save_is_rejected(self):
        row,trace=self.sample()
        for changed in (trace.replace(b'frame=8700',b'frame=8500'),trace.replace(b'count=1 bp=0 save=2',b'count=1 bp=0 save=3')):
            with self.assertRaises(ValueError):e.terminal_loss(row,changed)

    def test_wrong_archive_rejected_before_reading(self):
        with self.assertRaises(ValueError):e.verify_archive(b'fake result')

    def test_archive_traversal_rejected(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('../escape','x')
        with self.assertRaises(ValueError):e.zip_members(out.getvalue())

    def test_history_and_controller_are_not_rewritten(self):
        before=(e.ROOT/e.native.OLD).read_bytes()
        row,trace=self.sample();e.validate_native(json.dumps(row).encode(),trace,0)
        self.assertEqual((e.ROOT/e.native.OLD).read_bytes(),before)
        self.assertEqual(e.identity(before)['sha256'],e.native.OLD_SHA)
        self.assertEqual(e.native.derived_driver().assemble_controller().count('while(b_frames-w.start<90000U)'),1)

if __name__=='__main__':unittest.main()
