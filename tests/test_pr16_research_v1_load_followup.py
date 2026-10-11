"""先行call誤認の再発と偽成功を拒否。旧26件を再実行しない。"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).parent)]
import pr16_research_v1_load_followup as p
from test_pr16_research_v1_load import sample,encoded,BASE

class RootTests(unittest.TestCase):
    def fixture(self,case='v1-load-valid'):
        save,_,rows=sample(case)
        return save,p.root_expectations(case)+rows
    def bad(self,change,case='v1-load-valid'):
        save,rows=self.fixture(case);change(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            p.validate(encoded(rows),case,save,BASE)
    def test_valid_and_two_rejections(self):
        for case in p.prior.CASES:
            save,rows=self.fixture(case)
            self.assertEqual(p.validate(encoded(rows),case,save,BASE)['ordinary_root_calls'],2)
    def test_missing_first(self):self.bad(lambda r:r.pop(0))
    def test_duplicate_first(self):self.bad(lambda r:r.insert(0,r[0]))
    def test_reversed(self):self.bad(lambda r:r.__setitem__(slice(0,2),r[1::-1]))
    def test_first_result(self):self.bad(lambda r:r[0].update(result=1))
    def test_first_version(self):self.bad(lambda r:r[0].update(version=1))
    def test_first_counter(self):self.bad(lambda r:r[0].update(counter=2))
    def test_first_return(self):self.bad(lambda r:r[0].update(root_lr=p.LOAD_RETURN))
    def test_load_return(self):self.bad(lambda r:r[1].update(root_lr=p.FIRST_RETURN))
    def test_bool_counter(self):self.bad(lambda r:r[0].update(counter=False))
    def test_extra_key(self):self.bad(lambda r:r[0].update(ignored=True))
    def test_missing_key(self):self.bad(lambda r:r[0].pop('qol'))
    def test_bypassed_research(self):self.bad(lambda r:r[1].update(research=0))
    def test_duplicate_root_key(self):
        save,rows=self.fixture();raw=encoded(rows).replace(b'"diagnostic_root": true',b'"diagnostic_root": true,"diagnostic_root": true',1)
        with self.assertRaises(ValueError):p.validate(raw,p.prior.CASES[0],save,BASE)
    def test_checksum_false_success(self):self.bad(lambda r:r[1].update(result=1,version=2,last=0),p.prior.CASES[1])
    def test_tail_false_success(self):self.bad(lambda r:r[1].update(result=1,version=2,last=0),p.prior.CASES[2])
    def test_empty_output(self):
        with self.assertRaises(ValueError):p.validate(b'',p.prior.CASES[0],b'',BASE)
    def test_unknown_case(self):
        with self.assertRaises(ValueError):p.root_expectations('unreviewed')
    def test_unique_instrumentation(self):
        with self.assertRaises(ValueError):p.instrument(p.BEFORE+p.BEFORE)
        with self.assertRaises(ValueError):p.instrument('missing')
        self.assertEqual(p.instrument('before'+p.BEFORE+'after'),'before'+p.AFTER+'after')
    def test_wrong_rom(self):
        with self.assertRaises(ValueError):p.caller_bindings(b'wrong')

if __name__=='__main__':unittest.main()
