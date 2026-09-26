"""新しい虫取りoracleだけ。既受入native/写真/mapviewは実行しない。"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_bug as b


def encoded(rows):
    return ('\n'.join(json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in rows)+'\n').encode()


class BugTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=b.load((ROOT/b.RAW).read_bytes())
    def rows(self,case=b.CASES[1]):
        return [b.load(line.encode()) for line in self.raw['cases'][case]['stdout'].splitlines()]
    def reject(self,change,case=b.CASES[1]):
        rows=self.rows(case);change(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            b.validate(encoded(rows),case)
    def test_earned_original(self):
        result=b.validate(self.raw['cases'][b.CASES[1]]['stdout'].encode(),b.CASES[1])
        self.assertEqual(result['earned_rp'],8);self.assertEqual(result['fresh_cores'],2)
    def test_missing_original(self):
        result=b.validate(self.raw['cases'][b.CASES[0]]['stdout'].encode(),b.CASES[0])
        self.assertEqual(result['earned_rp'],0);self.assertEqual(result['fresh_cores'],1)
    def test_initial_harness_failure_not_accepted(self):
        failure=self.raw['harness_failure'];self.assertEqual(failure['execution']['returncode'],1)
        with self.assertRaises(ValueError):b.validate(failure['stdout'].encode(),b.CASES[0])
    def test_duplicate_json_key(self):
        raw=self.raw['cases'][b.CASES[1]]['stdout'].replace('"status":"PASS"','"status":"FAIL","status":"PASS"').encode()
        with self.assertRaises(ValueError):b.validate(raw,b.CASES[1])
    def test_nonfinite_json(self):
        with self.assertRaises(ValueError):b.load(b'{"frame":NaN}')
    def test_unknown_case(self):
        with self.assertRaises(ValueError):b.closing('photo-zero-earn-duplicate-cold-continue')
    def test_truncation(self):self.reject(lambda r:r.pop())
    def test_extra_row(self):self.reject(lambda r:r.insert(2,copy.deepcopy(r[1])))
    def test_empty(self):
        with self.assertRaises(ValueError):b.validate(b'',b.CASES[1])
    def test_size_bound(self):
        with self.assertRaises(ValueError):b.validate(b' '*20000,b.CASES[1])
    def test_wrong_order(self):self.reject(lambda r:r.__setitem__(slice(1,3),list(reversed(r[1:3]))))
    def test_wrong_case_transcript(self):
        with self.assertRaises(ValueError):b.validate(self.raw['cases'][b.CASES[0]]['stdout'].encode(),b.CASES[1])
    def test_all_owner_bytes(self):
        for offset in range(64):
            with self.subTest(offset=offset):
                def change(rows):
                    row=next(r for r in rows if r.get('event')=='earned');value=bytearray.fromhex(row['owner']);value[offset]^=1;row['owner']=value.hex()
                self.reject(change)
    def test_all_visit_frames(self):
        for label in ('decline','earn','duplicate','cold_duplicate'):
            with self.subTest(label=label):
                self.reject(lambda r:next(v for v in r if v.get('visit')==label).__setitem__('frame',0))
    def test_sources_have_guarded_observation(self):
        text=(ROOT/b.C).read_text();setup=text.split('static struct mCore*rb_setup',1)[1].split('static void rb_screen',1)[0]
        after=setup.split('si_guard(c);',1)[1]
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'si_restore('):self.assertNotIn(bad,after)
        self.assertIn('si_guard(c);rb_stance(c)',text)
        self.assertNotIn('ResearchEconomy_Test',text)
        self.assertIn('species=bug?39:1',text)
    def test_no_rom_change_or_native_replay(self):
        self.assertEqual(self.raw['counts']['rom_changes'],0)
        self.assertEqual(self.raw['counts']['accepted_case_reruns'],0)
        self.assertEqual(self.raw['counts']['accepted_native_processes'],2)
        self.assertEqual(self.raw['counts']['failed_native_processes'],1)
    def test_independent_ledger_requires_full_fixture(self):
        with self.assertRaises(ValueError):b.validate(self.raw['cases'][b.CASES[1]]['stdout'].encode(),b.CASES[1],bytes(16))


MUTATIONS={
 'setup_id':('setup','species',10), 'setup_type':('setup','type1',0),
 'setup_root':('setup','script',0), 'setup_coords_record':('setup','record',0),
 'setup_rp_injected':('setup','rp_injected',True), 'setup_natural':('setup','progression_is_fixture',False),
 'counter':('event','counter',9), 'party_count':('event','party_count',2),
 'party_hash':('event','party_sha256','0'*64), 'bag_hash':('event','inventory_sha256','0'*64),
 'quantity':('event','item_quantity',1), 'ledger_version':('ledger_event','version',1),
 'checksum':('ledger_event','checksum_valid',False), 'unrelated':('ledger_event','unrelated_ledger_sha256','0'*64),
 'ledger_hash':('ledger_event','ledger_sha256','0'*64), 'migration':('ledger_event','migration_dirty',1),
 'recovery':('ledger_event','recovery_blocked',1), 'visit_result':('visit','result',3),
 'visit_rp':('visit','rp',8), 'visit_bool_frame':('visit','frame',True),
 'screen':('screen','sha256','0'*64), 'screen_name':('screen','screen','other.ppm'),
 'status':('status','status','FAIL'), 'candidate':('status','candidate_sha256','0'*64),
 'cores':('status','fresh_cores',1), 'earned':('status','earned_rp',0),
 'saves':('status','transaction_saves',0), 'manual_save':('status','manual_saves',1),
 'host_write':('status','guarded_host_writes',1), 'replay':('status','accepted_case_reruns',1),
 'natural_claim':('status','natural_arrival_accepted',True), 'all_claim':('status','all_activities_accepted',True),
 'warning':('status','warnings_errors',1), 'extra_field':('status','unbound',True)}
for name,(kind,key,value) in MUTATIONS.items():
    def method(self,kind=kind,key=key,value=value):
        self.reject(lambda rows:next(r for r in rows if kind in r).__setitem__(key,value))
    setattr(BugTests,'test_reject_'+name,method)

if __name__=='__main__':unittest.main()
