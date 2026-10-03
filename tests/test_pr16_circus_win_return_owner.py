"""実原本のready1を保存し、失敗をnative受入へ昇格させない。"""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_win_return_owner as task

class OwnerTests(unittest.TestCase):
    def source(self):return (ROOT/task.RAW).read_bytes(),(ROOT/task.OLD).read_bytes()
    def test_actual_eighty_events_and_ready_one(self):
        value=task.witness(*self.source())
        self.assertEqual(value['original_events_identical'],80)
        self.assertEqual(value['task_order'],[3,4,5,0,1,2])
        for key in ('native_acceptance','save_continue_verified','genuine_30_wins_verified','persistent_180_frame_ready_zero_claimed'):self.assertFalse(value[key])
    def test_old_ready_zero_assumption_rejected(self):
        raw,old=self.source();lines=raw.splitlines()
        for i in range(len(lines)-1,-1,-1):
            if lines[i].startswith(b'CIRCUS_WIN_RETURN '):
                row=json.loads(lines[i][18:]);row['ready']=0;lines[i]=b'CIRCUS_WIN_RETURN '+json.dumps(row).encode();break
        with self.assertRaises(ValueError):task.witness(b'\n'.join(lines),old)
    def test_changed_original_events_rejected(self):
        raw,old=self.source();old=old.replace(b'"frame":0',b'"frame":1',1)
        with self.assertRaises(ValueError):task.witness(raw,old)
    def test_no_native_rerun_in_source_inspection(self):
        import inspect
        text=inspect.getsource(task.native)
        self.assertNotIn('n.run()',text)
        self.assertIn('arm-none-eabi-objdump',text)
        self.assertNotIn('write32',text)

if __name__=='__main__':unittest.main()
