"""新しい限定validatorだけを検査する。既受入native/旧unitは再実行しない。"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_lifecycle as m


def sample(case='v1-valid'):
    reject=case in m.CASES[3:];saves=0 if reject else 1
    h=hashlib.sha256(b'synthetic').hexdigest()
    owner=bytearray(64);owner[0]=1;owner[1]=64;owner[6]=1;owner[36]=1
    rows=[]
    for n,stage in enumerate(m.STAGES):
        rows.append({'event':stage,'counter':2+(saves if n else 0),'item_quantity':0,
                     'inventory_sha256':h,'other_inventory_sha256':h,'party_sha256':h,'party_count':1,
                     'owner':(bytes(64) if n==0 or (reject and n==1) else owner).hex()})
        rows.append({'ledger_event':stage,'version':1 if n==0 or (reject and n==1) else 2,'size':2048,
                     'checksum_valid':not(case=='v1-bad-checksum' and n<2),
                     'ledger_sha256':h,'unrelated_ledger_sha256':h,'migration_dirty':0,'recovery_blocked':0})
    rows.append({'status':'PASS','scope':m.SCOPE,'case':case,'candidate_sha256':m.CANDIDATE['sha256'],
                 'result':7 if reject else 5,'delegate_saves':saves,'delegate_loads':0,'phase0':saves,
                 'fresh_cores':3,'host_write_barriers':7,'normal_new_game_or_transaction_ui_accepted':False,
                 'v1_load_adapter_accepted':False,'phase0_failure_accepted':False,'warnings_errors':0})
    return rows


def raw(rows):return ('\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n').encode()


class LifecycleTests(unittest.TestCase):
    def changed(self,change,case='v1-valid'):
        rows=sample(case);change(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):m.validate(raw(rows),case)
    def test_all_five_scopes(self):
        for case in m.CASES:
            with self.subTest(case=case):self.assertEqual(m.validate(raw(sample(case)),case)['case'],case)
    def test_boolean_save_count(self):self.changed(lambda r:r[-1].update(delegate_saves=True))
    def test_candidate_identity(self):self.changed(lambda r:r[-1].update(candidate_sha256='0'*64))
    def test_extra_native_save(self):self.changed(lambda r:r[4].update(counter=4))
    def test_owner_balance(self):
        def f(r):b=bytearray.fromhex(r[2]['owner']);b[4]=1;r[2]['owner']=b.hex()
        self.changed(f)
    def test_owner_pending(self):
        def f(r):b=bytearray.fromhex(r[2]['owner']);b[48]=1;r[2]['owner']=b.hex()
        self.changed(f)
    def test_full_bag_digest(self):self.changed(lambda r:r[2].update(inventory_sha256='1'*64))
    def test_unrelated_items(self):self.changed(lambda r:r[2].update(other_inventory_sha256='1'*64))
    def test_complete_party(self):self.changed(lambda r:r[4].update(party_sha256='1'*64))
    def test_migration_prefix(self):self.changed(lambda r:r[3].update(unrelated_ledger_sha256='1'*64))
    def test_v2_checksum(self):self.changed(lambda r:r[3].update(checksum_valid=False))
    def test_second_continue(self):self.changed(lambda r:r[7].update(ledger_sha256='2'*64))
    def test_missing_observation(self):
        with self.assertRaises(ValueError):m.validate(raw(sample()[:-1]),'v1-valid')
    def test_extra_observation(self):
        with self.assertRaises(ValueError):m.validate(raw(sample()+[{}]),'v1-valid')
    def test_duplicate_json_key(self):
        b=raw(sample()).replace(b'"phase0":1',b'"phase0":1,"phase0":1')
        with self.assertRaises(ValueError):m.validate(b,'v1-valid')
    def test_no_new_game_claim(self):self.changed(lambda r:r[-1].update(normal_new_game_or_transaction_ui_accepted=True))
    def test_no_load_adapter_claim(self):self.changed(lambda r:r[-1].update(v1_load_adapter_accepted=True))
    def test_no_phase0_failure_claim(self):self.changed(lambda r:r[-1].update(phase0_failure_accepted=True))
    def test_rejected_v1_not_normalized(self):self.changed(lambda r:r[3].update(ledger_sha256='3'*64),'v1-bad-checksum')
    def test_extra_result_field(self):self.changed(lambda r:r[-1].update(release_ready=True))
    def test_volatile_type(self):self.changed(lambda r:r[3].update(migration_dirty=False))
    def test_bound_volatile_offsets(self):
        text=(ROOT/'tools/mgba_pr16_research_lifecycle.c').read_text()
        self.assertIn('read8(c,SI_VOL+26),read8(c,SI_VOL+27)',text)
        self.assertNotIn('read8(c,SI_VOL+30),read8(c,SI_VOL+31)',text)


if __name__=='__main__':unittest.main()
