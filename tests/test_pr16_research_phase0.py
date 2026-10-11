"""新規phase0 oracleのみ。受入済みnative/unitは実行しない。"""
import hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_phase0 as p


def sample(case):
    h=hashlib.sha256(b'synthetic').hexdigest();owner=bytearray(64)
    owner[0]=1;owner[1]=64;owner[6]=1;owner[36]=1
    rows=[]
    for i,stage in enumerate(p.STAGES):
        v1=case==p.CASES[2] and i in (1,2)
        rows.append({'event':stage,'counter':2,'item_quantity':0,'party_count':1,'owner':owner.hex(),
                     'inventory_sha256':h,'other_inventory_sha256':h,'party_sha256':h})
        rows.append({'ledger_event':stage,'version':1 if v1 else 2,'size':2048,'checksum_valid':True,
                     'ledger_sha256':h,'unrelated_ledger_sha256':h,'migration_dirty':0,'recovery_blocked':int(i==2)})
    rows.append(p.expected_result(case));return rows


def raw(rows):return ('\n'.join(json.dumps(x) for x in rows)+'\n').encode()


class Phase0Tests(unittest.TestCase):
    def bad(self,fn,case=p.CASES[0]):
        r=sample(case);fn(r)
        with self.assertRaises((ValueError,KeyError,TypeError)):p.validate(raw(r),case)
    def test_three_declared_cases(self):
        for case in p.CASES:self.assertEqual(p.validate(raw(sample(case)),case)['native_result'],255)
    def test_native_false_success(self):self.bad(lambda r:r[-1].update(native_result=1))
    def test_native_return_not_observed(self):self.bad(lambda r:r[-1].update(native_returns=0))
    def test_extra_native_save(self):self.bad(lambda r:r[-1].update(delegate_saves=2))
    def test_native_save_counter_changed(self):self.bad(lambda r:r[4].update(counter=3))
    def test_v1_rollback_corruption(self):self.bad(lambda r:r[5].update(ledger_sha256='1'*64),p.CASES[2])
    def test_recovery_not_blocked(self):self.bad(lambda r:r[5].update(recovery_blocked=0))
    def test_persisted_corruption(self):self.bad(lambda r:r[7].update(ledger_sha256='2'*64))
    def test_second_continue_changed(self):self.bad(lambda r:r[9].update(ledger_sha256='2'*64))
    def test_bag_changed(self):self.bad(lambda r:r[4].update(inventory_sha256='3'*64))
    def test_party_changed(self):self.bad(lambda r:r[4].update(party_sha256='3'*64))
    def test_bool_counter(self):self.bad(lambda r:r[4].update(counter=True))
    def test_physical_fault_overclaim(self):self.bad(lambda r:r[-1].update(physical_flash_fault_accepted=True))
    def test_retry_overclaim(self):self.bad(lambda r:r[-1].update(same_core_retry_accepted=True))
    def test_missing_observation(self):
        with self.assertRaises(ValueError):p.validate(raw(sample(p.CASES[0])[1:]),p.CASES[0])
    def test_duplicate_field(self):
        b=raw(sample(p.CASES[0])).replace(b'"native_result": 255',b'"native_result": 255, "native_result": 255')
        with self.assertRaises(ValueError):p.validate(b,p.CASES[0])
    def test_generation_readonly_observer(self):
        text=p.generate('int main(int argc,char**argv){'+p.OBSERVE+'}', 'int main(int argc,char**argv){return 0;}')
        self.assertEqual(text.count('int main('),1)
        self.assertIn('ph_native_last=(unsigned)read_register(c,"r0")',text)
        self.assertNotIn('write_register',text)
    def test_generation_rejects_drift(self):
        with self.assertRaises(ValueError):p.generate('int main(int argc,char**argv){}','int main(int argc,char**argv){}')

if __name__=='__main__':unittest.main()
