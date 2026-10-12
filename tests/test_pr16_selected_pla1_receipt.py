"""受領JSONに対する新しい14境界。ARM/36decoder試験は再走しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_pla1_closeout as r

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        import os
        directory = Path(os.environ.get('PR16_PLA1_RECEIPT_FIXTURE', str(Path(__file__).resolve().parents[1]/'.local/pr16-selected-pla1-closeout/received')))
        self.p = json.loads((directory/'pla1-reader.json').read_bytes())
        self.s = json.loads((directory/'result.json').read_bytes())
    def reject(self, change):
        change(self.p,self.s)
        with self.assertRaises(ValueError):r.validate(self.p,self.s)
    def test_valid_readonly(self):
        before=copy.deepcopy((self.p,self.s));r.validate(self.p,self.s);self.assertEqual((self.p,self.s),before)
    def test_wrong_candidate(self):self.reject(lambda p,s:p['candidate'].update(sha256='0'*64))
    def test_wrong_source(self):self.reject(lambda p,s:p.update(source_head='0'*40))
    def test_wrong_run(self):self.reject(lambda p,s:s.update(actions_run_id=0))
    def test_natural_entry_claim(self):self.reject(lambda p,s:p['profiles'][0].update(natural_entry_claimed=True))
    def test_native_claim(self):self.reject(lambda p,s:p.update(native_processes=1))
    def test_missing_byte(self):self.reject(lambda p,s:p['profiles'][0]['target_reads'].pop())
    def test_wrong_instruction(self):self.reject(lambda p,s:p['profiles'][0]['target_reads'][0].update(instruction=0x09FFF328))
    def test_wide_read(self):self.reject(lambda p,s:p['profiles'][0]['target_reads'][0].update(width=4))
    def test_failure_output_written(self):self.reject(lambda p,s:p['profiles'][1].update(output_write_on_failure=True))
    def test_false_success(self):self.reject(lambda p,s:p['profiles'][1].update(returned=1))
    def test_formal_promotion(self):self.reject(lambda p,s:p.update(formal_classified=790))
    def test_forged_completion(self):self.reject(lambda p,s:p.update(actions_completion_confirmed=True))
    def test_false_other_targets(self):self.reject(lambda p,s:s.update(other_two_targets_reader_proven=True))

if __name__=='__main__':unittest.main()
