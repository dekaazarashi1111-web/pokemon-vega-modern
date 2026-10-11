"""新規native取消oracle20件。既受入host49/phase0/load/retryを呼ばない。"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_shop_cancel as m

def seed():
    body=bytearray(2048);body[:8]=b'VGS1\x02\0\0\x08';body[0x73f],body[0x740],body[0x745],body[0x763]=1,64,1,1
    raw=bytearray(131072);raw[m.prior.OFFSET:m.prior.OFFSET+2048]=m.prior.old.seal(body);return bytes(raw)

def sample():
    rows=[{'binding':'map98/3-background0','events':0x09390000,'backgrounds':0x09390020,'script':0x09390080,'x':2,'y':1},
          {'fixture':'stock-warp-only','map_group':98,'map_num':3,'x':2,'y':2,'shop_dispatch_injected':False,'guarded_host_writes':0}]
    owner=bytearray(64);owner[0],owner[1],owner[6],owner[36],owner[4]=1,64,1,1,100
    for i,stage in enumerate(m.STAGES):
        if i in (1,2):rows.append({'shop_open':'b' if i==1 else 'row','eligible_count':11,'window':4,'callback':0x093BF001,'native_tasks':1})
        rows.append({'event':stage,'counter':2+int(i>=3),'item_quantity':0,'inventory_sha256':'a'*64,'other_inventory_sha256':'b'*64,'party_sha256':'c'*64,'party_count':1,'owner':owner.hex()})
        rows.append({'ledger_event':stage,'version':2,'size':2048,'checksum_valid':True,'ledger_sha256':'d'*64,'unrelated_ledger_sha256':'e'*64,'migration_dirty':0,'recovery_blocked':0})
    rows.append(m.result(11,3,1100));return rows

def encode(rows):return ('\n'.join(json.dumps(x) for x in rows)+'\n').encode()

class ShopCancelTests(unittest.TestCase):
    def test_valid_native_schema(self):self.assertEqual(m.validate(encode(sample()))['fresh_cores'],3)
    def test_fixture_only_ledger(self):
        raw=seed()
        with patch.object(m.prior.old.old,'SEED',m.identity(raw)):out,receipt=m.fixture(raw)
        self.assertEqual(out[:m.prior.OFFSET],raw[:m.prior.OFFSET]);self.assertEqual(out[m.prior.OFFSET+2048:],raw[m.prior.OFFSET+2048:]);self.assertEqual(receipt['outside_ledger_changes'],0)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):m.fixture(seed())
    def test_bad_checksum_rejected(self):
        raw=bytearray(seed());raw[m.prior.OFFSET+8]^=1;raw=bytes(raw)
        with patch.object(m.prior.old.old,'SEED',m.identity(raw)),self.assertRaises(ValueError):m.fixture(raw)

MUTATIONS={
 'injected_dispatch':lambda r:r[1].update(shop_dispatch_injected=True),
 'wrong_map':lambda r:r[1].update(map_num=4),
 'unknown_setup_field':lambda r:r[1].update(ignored=True),
 'extra_output':lambda r:r.append(r[-1]),
 'truncated_output':lambda r:r.pop(2),
 'purchase_overclaim':lambda r:r[-1].update(purchase_accepted=True),
 'new_game_overclaim':lambda r:r[-1].update(normal_new_game_accepted=True),
 'natural_progress_overclaim':lambda r:r[-1].update(natural_progress_accepted=True),
 'wrong_candidate':lambda r:r[-1].update(candidate_sha256='f'*64),
 'extra_save':lambda r:r[-1].update(transaction_saves=1),
 'missing_guard':lambda r:r[-1].update(host_write_barriers=6),
 'wrong_core_count':lambda r:r[-1].update(fresh_cores=2),
 'bool_frames':lambda r:r[-1].update(frames_after_warp=True),
 'warnings':lambda r:r[-1].update(warnings_errors=1),
 'wrong_bag':lambda r:r[5].update(inventory_sha256='0'*64),
 'cancel_saved':lambda r:r[5].update(counter=3),
}
for name,mutate in MUTATIONS.items():
    def check(self,mutate=mutate):
        rows=sample();mutate(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):m.validate(encode(rows))
    setattr(ShopCancelTests,'test_reject_'+name,check)
if __name__=='__main__':unittest.main()
