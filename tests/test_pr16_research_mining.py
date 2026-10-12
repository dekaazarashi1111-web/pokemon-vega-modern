"""採掘新規oracleの負例。raw原本だけを読取り、native/既受入検査は呼ばない。"""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_mining as b


def encoded(rows):
    return ('\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n').encode()


class MiningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=b.load(Path(os.environ.get('PR16_MINING_MEASUREMENT',ROOT/b.RAW)).read_bytes())
    def rows(self,case=b.CASES[2]):
        return [b.load(line.encode()) for line in self.raw['cases'][case]['stdout'].splitlines()]
    def reject(self,change,case=b.CASES[2]):
        rows=self.rows(case);change(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            b.validate(encoded(rows),case)
    def test_all_three_originals(self):
        for case in b.CASES:
            with self.subTest(case=case):
                out=b.validate(self.raw['cases'][case]['stdout'].encode(),case)
                self.assertEqual(out['earned_rp'],10 if case==b.CASES[2] else 0)
                self.assertIs(out['natural_reentry_accepted'],False)
    def test_all_owner_bytes(self):
        for i in range(64):
            with self.subTest(offset=i):
                def change(rows):
                    v=next(r for r in rows if r.get('event')=='earned');data=bytearray.fromhex(v['owner']);data[i]^=1;v['owner']=data.hex()
                self.reject(change)
    def test_every_row_required(self):
        for i in range(len(self.rows())):
            with self.subTest(row=i):self.reject(lambda r:r.pop(i))
    def test_every_row_closed(self):
        for i in range(len(self.rows())):
            with self.subTest(row=i):self.reject(lambda r:r[i].update(unexpected=1))
    def test_stage_order(self):
        self.reject(lambda r:r.reverse())
    def test_duplicate_rows(self):
        self.reject(lambda r:r.append(r[-1]))
    def test_duplicate_json_key(self):
        raw=encoded(self.rows()).replace(b'"status":"PASS"',b'"status":"PASS","status":"PASS"')
        with self.assertRaises(ValueError):b.validate(raw,b.CASES[2])
    def test_unbounded_and_malformed(self):
        for raw in (b'',b'x'*20001,b'{}',b'null',b'[]',b'not-json',b'\xff'):
            with self.subTest(raw=raw[:16]),self.assertRaises((ValueError,TypeError,KeyError)):
                b.validate(raw,b.CASES[2])
    def test_wrong_case(self):
        with self.assertRaises(ValueError):b.validate(encoded(self.rows()),'bug-earn-duplicate-cold')
    def test_wrong_fixture(self):
        for fixture in (b'',bytes(131072),bytearray(131072)):
            with self.subTest(kind=type(fixture).__name__),self.assertRaises(ValueError):
                b.validate(encoded(self.rows()),b.CASES[2],fixture)
    def test_missing_badge_cannot_credit(self):
        self.reject(lambda r:next(v for v in r if 'visit' in v).update(rp=10),b.CASES[0])
    def test_missing_move_cannot_credit(self):
        self.reject(lambda r:next(v for v in r if 'visit' in v).update(rp=10),b.CASES[1])


# 独立の拒否例をケース名で記録。型混同・過大主張・不変量破損を含む。
MUTATIONS = [
 ('badge','setup','mining','badge',0),('move','setup','mining','move',33),
 ('event_root','setup','mining','events',0),('record_root','setup','mining','record',0),
 ('script_root','setup','mining','script',0),('no_progress_fixture','setup','mining','progression_is_fixture',False),
 ('injected_credit','setup','mining','rp_injected',True),('bool_badge','setup','mining','badge',True),
 ('party','event','earned','party_sha256','0'*64),('bag','event','earned','inventory_sha256','0'*64),
 ('other_bag','event','earned','other_inventory_sha256','0'*64),('party_count','event','earned','party_count',2),
 ('bool_counter','event','earned','counter',True),('extra_save','event','cold_cap','counter',6),
 ('items','event','earned','item_quantity',1),('cold_owner','event','continued','owner','00'*64),
 ('ledger','ledger_event','earned','ledger_sha256','0'*64),('checksum','ledger_event','earned','checksum_valid',False),
 ('unrelated_owner','ledger_event','earned','unrelated_ledger_sha256','0'*64),('migration','ledger_event','earned','migration_dirty',1),
 ('recovery','ledger_event','earned','recovery_blocked',1),('ledger_size','ledger_event','earned','size',2047),
 ('ledger_version','ledger_event','earned','version',1),('cancel_rp','visit','decline','rp',10),
 ('cancel_save','visit','decline','counter',4),('cancel_removes_rock','visit','decline','rock_count',0),
 ('earn_result','visit','earn','result',4),('earn_credit','visit','earn','rp',8),
 ('earn_no_removal','visit','earn','rock_count',1),('earn_no_save','visit','earn','counter',2),
 ('cap_credit','visit','cold_cap','rp',20),('cap_result','visit','cold_cap','result',0),
 ('wild_tail','visit','earn','stopped_before_wild_tail',False),('not_eligible','visit','earn','eligible',False),
 ('frame_regression','visit','cold_cap','frame',1000),('frame_bool','visit','earn','frame',True),
 ('frame_bound','visit','earn','frame',10001),('frame_fraction','visit','earn','frame',2732.5),
 ('natural_reentry','reentry_fixture',True,'natural_reentry_accepted',True),('reentry_rp','reentry_fixture',True,'rp_injected',True),
 ('no_warp','reentry_fixture',True,'stock_warps',0),('screen','screen','mining-earn-outcome.ppm','sha256','0'*64),
 ('candidate','status','PASS','candidate_sha256','0'*64),('cores','status','PASS','fresh_cores',2),
 ('total_saves','status','PASS','transaction_saves',0),('manual_save','status','PASS','manual_saves',1),
 ('host_write','status','PASS','guarded_host_writes',1),('old_rerun','status','PASS','accepted_case_reruns',1),
 ('all_activities','status','PASS','all_activities_accepted',True),('natural_arrival','status','PASS','natural_arrival_accepted',True),
 ('warnings','status','PASS','warnings_errors',1),('bool_rp','status','PASS','earned_rp',True)]


def mutation_test(selector,value,key,replacement):
    def test(self):
        self.reject(lambda rows:next(r for r in rows if r.get(selector)==value).update({key:replacement}))
    return test

for name,selector,value,key,replacement in MUTATIONS:
    setattr(MiningTests,'test_reject_'+name,mutation_test(selector,value,key,replacement))

if __name__=='__main__':unittest.main()
