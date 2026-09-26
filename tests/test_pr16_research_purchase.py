"""新規購入境界oracle。旧取消/host49/load/retryの試験は起動しない。"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_purchase as m
old=m.prior.prior.old

def seed():
    b=bytearray(2048);b[:8]=b'VGS1\x02\0\0\x08';b[0x73f],b[0x740],b[0x745],b[0x763]=1,64,1,1
    raw=bytearray(131072);raw[old.OFFSET:old.OFFSET+2048]=old.seal(b);return bytes(raw)

def fixture():
    raw=seed()
    with patch.object(old.old,'SEED',m.identity(raw)):return m.fixture(raw)[0]

def sample():
    save=fixture();source=save[old.OFFSET:old.OFFSET+2048]
    rows=[{'binding':'map98/3-background0','events':0x09413C50,'backgrounds':0x09413C14,'script':0x093C0328,'catalog':0,'item':4,'price':10,'quantity':5}]
    for i,stage in enumerate(m.STAGES):
        if i in (1,3,6):rows.append({'shop_open':{1:'decline',3:'buy',6:'insufficient'}[i],'eligible_count':11,'window':4,'callback':0x093BF001,'native_tasks':1})
        ledger=bytearray(source)
        if i>=4:ledger[0x743]=0;ledger[0x763]=2
        ledger=old.seal(ledger)
        other=bytearray(ledger);other[4:6]=bytes(2);other[8:12]=bytes(4);other[0x73f:0x77f]=bytes(64)
        rows.append({'event':stage,'counter':2+2*int(i>=4)+int(i>=8),'item_quantity':5*int(i>=4),'inventory_sha256':('f' if i>=4 else 'a')*64,'other_inventory_sha256':'b'*64,'party_sha256':'c'*64,'party_count':1,'owner':ledger[0x73f:0x77f].hex()})
        rows.append({'ledger_event':stage,'version':2,'size':2048,'checksum_valid':True,'ledger_sha256':m.identity(ledger)['sha256'],'unrelated_ledger_sha256':m.identity(other)['sha256'],'migration_dirty':0,'recovery_blocked':0})
    rows.append(m.result(2000));return rows,save

def encode(rows):return ('\n'.join(json.dumps(x) for x in rows)+'\n').encode()
def event(rows,stage):return next(r for r in rows if r.get('event')==stage)
def ledger(rows,stage):return next(r for r in rows if r.get('ledger_event')==stage)

class PurchaseTests(unittest.TestCase):
    def test_complete_closed_trace(self):
        rows,save=sample();self.assertEqual(m.validate(encode(rows),save)['fresh_cores'],4)
    def test_fixture_only_ledger(self):
        raw=seed()
        with patch.object(old.old,'SEED',m.identity(raw)):out,receipt=m.fixture(raw)
        self.assertEqual(out[:old.OFFSET],raw[:old.OFFSET]);self.assertEqual(out[old.OFFSET+2048:],raw[old.OFFSET+2048:]);self.assertEqual(receipt['outside_ledger_changes'],0);self.assertEqual(int.from_bytes(out[old.OFFSET+0x743:old.OFFSET+0x745],'little'),10)
    def test_wrong_seed(self):
        with self.assertRaises(ValueError):m.fixture(seed())
    def test_bad_seed_checksum(self):
        raw=bytearray(seed());raw[old.OFFSET+8]^=1;raw=bytes(raw)
        with patch.object(old.old,'SEED',m.identity(raw)),self.assertRaises(ValueError):m.fixture(raw)
    def test_generated_fixture_binding_and_single_main(self):
        raw=seed()
        with patch.object(old.old,'SEED',m.identity(raw)):
            before,_=m.prior.fixture(raw);after,_=m.fixture(raw)
            template='#define UC_FIXTURE "'+m.identity(before)['sha256']+'"\nint main(int argc,char**argv){return 0;}'
            with patch.object(m.prior,'generate',return_value=template.encode()):code=m.generate(raw).decode()
        self.assertEqual(code.count('int main(int argc,char**argv){'),1);self.assertIn('int accepted_shop_cancel_main',code);self.assertIn(m.identity(after)['sha256'],code);self.assertNotIn(m.identity(before)['sha256'],code)
    def test_raw_duplicate_json_key_rejected(self):
        rows,save=sample();raw=encode(rows).replace(b'"catalog": 0',b'"catalog": 0, "catalog": 0',1)
        with self.assertRaises(ValueError):m.validate(raw,save)
    def test_corrupt_input_ledger_rejected(self):
        rows,save=sample();b=bytearray(save);b[old.OFFSET+8]^=1
        with self.assertRaises(ValueError):m.validate(encode(rows),bytes(b))

MUTATIONS={
 'wrong_root':lambda r:r[0].update(script=0x093C0330),
 'bool_catalog':lambda r:r[0].update(catalog=False),
 'wrong_price':lambda r:r[0].update(price=100),
 'extra_binding_field':lambda r:r[0].update(injected=True),
 'extra_row':lambda r:r.append(r[-1]),
 'missing_row':lambda r:r.pop(3),
 'reordered_stages':lambda r:r.reverse(),
 'wrong_candidate':lambda r:r[-1].update(candidate_sha256='d'*64),
 'new_game_overclaim':lambda r:r[-1].update(normal_new_game_accepted=True),
 'natural_progress_overclaim':lambda r:r[-1].update(natural_progress_accepted=True),
 'missing_guard':lambda r:r[-1].update(host_write_barriers=6),
 'host_write':lambda r:r[-1].update(guarded_host_writes=1),
 'wrong_cores':lambda r:r[-1].update(fresh_cores=3),
 'bool_frames':lambda r:r[-1].update(frames_after_warp=True),
 'warnings':lambda r:r[-1].update(warnings_errors=1),
 'extra_transaction_save':lambda r:r[-1].update(transaction_saves=3),
 'decline_persisted':lambda r:event(r,'declined').update(counter=3),
 'selection_spent':lambda r:event(r,'selected_buy').update(item_quantity=5),
 'purchase_quantity':lambda r:event(r,'purchased').update(item_quantity=4),
 'purchase_not_saved':lambda r:event(r,'transaction_continue').update(counter=2),
 'repeat_purchase':lambda r:event(r,'insufficient').update(item_quantity=10),
 'insufficient_saved':lambda r:event(r,'insufficient').update(counter=5),
 'unrelated_bag_changed':lambda r:event(r,'purchased').update(other_inventory_sha256='0'*64),
 'party_changed':lambda r:event(r,'continued').update(party_sha256='0'*64),
 'bad_party_count':lambda r:event(r,'continued').update(party_count=True),
 'bag_disappeared':lambda r:event(r,'continued').update(inventory_sha256='a'*64),
 'nonhex_digest':lambda r:event(r,'continued').update(inventory_sha256='z'*64),
 'missing_owner_byte':lambda r:event(r,'continued').update(owner='00'*63),
 'wrong_owner':lambda r:event(r,'continued').update(owner='00'*64),
 'forged_full_ledger':lambda r:ledger(r,'continued').update(ledger_sha256='0'*64),
 'unrelated_ledger_changed':lambda r:ledger(r,'continued').update(unrelated_ledger_sha256='0'*64),
 'migration_dirty':lambda r:ledger(r,'continued').update(migration_dirty=1),
 'wrong_checksum':lambda r:ledger(r,'purchased').update(checksum_valid=False),
 'extra_event_field':lambda r:event(r,'fixture').update(ignored=True),
 'missing_menu_task':lambda r:next(x for x in r if 'shop_open' in x).update(native_tasks=0),
}
for name,mutate in MUTATIONS.items():
    def check(self,mutate=mutate):
        rows,save=sample();mutate(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):m.validate(encode(rows),save)
    setattr(PurchaseTests,'test_reject_'+name,check)
if __name__=='__main__':unittest.main()
