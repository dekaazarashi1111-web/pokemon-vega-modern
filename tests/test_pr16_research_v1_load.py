"""V1 Flash fixture/oracleの限定負例。native旧ケースは実行しない。"""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_v1_load as p
BASE={'item_quantity':0,'party_count':6,'inventory_sha256':'1'*64,'other_inventory_sha256':'1'*64,'party_sha256':'2'*64}


def synthetic_seed():
    raw=bytearray(131072);ledger=bytearray(2048);ledger[:8]=b'VGS1\x02\0\0\x08';raw[p.OFFSET:p.OFFSET+2048]=p.seal(ledger);return bytes(raw)


def sample(case):
    seed=synthetic_seed()
    with patch.object(p.old,'SEED',p.identity(seed)):save,receipt=p.fixture(seed,case)
    valid=case==p.CASES[0];ledger=p.migrated(save[p.OFFSET:p.OFFSET+2048]) if valid else save[p.OFFSET:p.OFFSET+2048]
    state={'load_state':'adapter_return','counter':3 if valid else 2,'version':2 if valid else 1,
           'checksum_valid':p.checksum(ledger)==int.from_bytes(ledger[8:12],'little'),'migration_dirty':0,'recovery_blocked':0,
           'last_result':0 if valid else 7,'ledger_sha256':hashlib.sha256(ledger).hexdigest()}
    trace=dict(p.expected_trace(case),steps=1000,save_type=0);rows=[state,trace]
    if valid:
        prefix=bytearray(ledger);prefix[4:6]=bytes(2);prefix[8:12]=bytes(4);prefix[0x73f:0x77f]=bytes(64)
        for stage in ('continued','continued_again','continued_third'):
            rows.extend([dict(BASE,event=stage,counter=3,owner=ledger[0x73f:0x77f].hex()),
                {'ledger_event':stage,'version':2,'size':2048,'checksum_valid':True,'migration_dirty':0,'recovery_blocked':0,
                 'ledger_sha256':hashlib.sha256(ledger).hexdigest(),'unrelated_ledger_sha256':hashlib.sha256(prefix).hexdigest()}])
    rows.append({'status':'PASS','scope':p.SCOPE,'case':case,'candidate_sha256':p.CANDIDATE['sha256'],'fresh_cores':3 if valid else 1,
          'host_write_barriers':7,'ram_fixture_writes':0,'physical_flash_fault_accepted':False,
          'normal_new_game_accepted':False,'transaction_ui_accepted':False,'warnings_errors':0})
    return save,receipt,rows


def encoded(rows):return ('\n'.join(json.dumps(x) for x in rows)+'\n').encode()


class LoadTests(unittest.TestCase):
    def bad(self,change,case=p.CASES[0]):
        save,_,rows=sample(case);change(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):p.validate(encoded(rows),case,save,BASE)
    def test_three_shapes(self):
        for case in p.CASES:
            save,_,rows=sample(case);self.assertEqual(p.validate(encoded(rows),case,save,BASE)['case'],case)
    def test_fixture_scope(self):
        seed=synthetic_seed()
        with patch.object(p.old,'SEED',p.identity(seed)):
            for case in p.CASES:
                save,receipt=p.fixture(seed,case)
                self.assertEqual(seed[:p.OFFSET],save[:p.OFFSET]);self.assertEqual(seed[p.OFFSET+2048:],save[p.OFFSET+2048:])
                self.assertEqual(receipt['checksum_valid'],case!=p.CASES[1]);self.assertEqual(receipt['reserved_tail_valid'],case!=p.CASES[2])
    def test_wrong_seed(self):
        with self.assertRaises(ValueError):p.fixture(synthetic_seed(),p.CASES[0])
    def test_invalid_migration_input(self):
        for case in p.CASES[1:]:
            save,_,_=sample(case)
            with self.assertRaises(ValueError):p.migrated(save[p.OFFSET:p.OFFSET+2048])
    def test_missing_root(self):self.bad(lambda r:r[1].update(root_calls=0))
    def test_load_bypass(self):self.bad(lambda r:r[1].update(research_calls=0))
    def test_mirage_bypass(self):self.bad(lambda r:r[1].update(mirage_calls=0))
    def test_qol_bypass(self):self.bad(lambda r:r[1].update(qol_load_calls=0))
    def test_missing_save(self):self.bad(lambda r:r[1].update(save_calls=0))
    def test_wrong_native_return(self):self.bad(lambda r:r[1].update(native_result=255))
    def test_duplicate_save(self):self.bad(lambda r:r[1].update(save_calls=2))
    def test_wrong_counter(self):self.bad(lambda r:r[0].update(counter=2))
    def test_dirty(self):self.bad(lambda r:r[0].update(migration_dirty=1))
    def test_host_write(self):self.bad(lambda r:r[1].update(host_writes=1))
    def test_normalized_invalid(self):self.bad(lambda r:r[0].update(version=2),p.CASES[1])
    def test_invalid_result_hidden(self):self.bad(lambda r:r[1].update(root_result=1),p.CASES[2])
    def test_ledger_byte_change(self):self.bad(lambda r:r[0].update(ledger_sha256='0'*64))
    def test_party_change(self):self.bad(lambda r:r[2].update(party_sha256='3'*64))
    def test_bag_change(self):self.bad(lambda r:r[4].update(inventory_sha256='3'*64))
    def test_second_continue_change(self):self.bad(lambda r:r[7].update(ledger_sha256='4'*64))
    def test_bool_counter(self):self.bad(lambda r:r[0].update(counter=True))
    def test_case_missing(self):
        save,_,rows=sample(p.CASES[0])
        with self.assertRaises(ValueError):p.validate(encoded(rows[:-1]),p.CASES[0],save,BASE)
    def test_duplicate_json(self):
        save,_,rows=sample(p.CASES[0]);raw=encoded(rows).replace(b'"host_writes": 0',b'"host_writes": 0,"host_writes": 0')
        with self.assertRaises(ValueError):p.validate(raw,p.CASES[0],save,BASE)
    def test_ui_overclaim(self):self.bad(lambda r:r[-1].update(transaction_ui_accepted=True))
    def test_newgame_overclaim(self):self.bad(lambda r:r[-1].update(normal_new_game_accepted=True))
    def test_physical_fault_overclaim(self):self.bad(lambda r:r[-1].update(physical_flash_fault_accepted=True))

if __name__=='__main__':unittest.main()
