"""写真稼得だけの独立検査。合成ledgerを使い私用seed/旧nativeを呼ばない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_photo as m

class PhotoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old=m.purchase.prior.prior.old
        cls.owner=bytearray(64);cls.owner[0],cls.owner[1],cls.owner[6],cls.owner[36]=1,64,1,1
        body=bytearray(2048);body[:8]=b'VGS1\x02\0\0\x08';body[0x73f:0x77f]=cls.owner;body=old.seal(body)
        save=bytearray(131072);offset=m.purchase.prior.prior.OFFSET;save[offset:offset+2048]=body;cls.save=bytes(save)
        rows=[m.BINDING.copy()]
        def stage(index):
            owner=bytearray(cls.owner);owner[7]=1
            if index>=2:owner[4]=6;owner[10]=6;owner[24]=6;owner[27]=4;owner[36]=2
            ledger=bytearray(body);ledger[0x73f:0x77f]=owner;ledger=old.seal(ledger)
            other=bytearray(ledger);other[4:6]=bytes(2);other[8:12]=bytes(4);other[0x73f:0x77f]=bytes(64)
            rows.append(dict(event=m.STAGES[index],counter=2+2*(index>=2),item_quantity=0,
                inventory_sha256='1'*64,other_inventory_sha256='2'*64,party_sha256='3'*64,
                party_count=6,owner=owner.hex()))
            rows.append(dict(ledger_event=m.STAGES[index],version=2,size=2048,checksum_valid=True,
                ledger_sha256=m.identity(ledger)['sha256'],unrelated_ledger_sha256=m.identity(other)['sha256'],
                migration_dirty=0,recovery_blocked=0))
        def visit(index,name):
            rows.append(dict(prompt=name,entry_keys=64 if index==0 else 1,screen_sha256=m.SCREENS[f'photo-{name}-prompt.ppm']))
            if index:rows.append(dict(outcome=name,screen_sha256=m.SCREENS[f'photo-{name}-outcome.ppm']))
            rows.append(dict(visit=name,confirmed=index!=0,activity_result=0 if index<2 else 4,frame=1100+500*index))
        stage(0);visit(0,'decline');stage(1);visit(1,'earn');stage(2);visit(2,'duplicate');stage(3)
        stage(4);visit(3,'duplicate_after_continue');stage(5);rows.append(m.closing());cls.rows=rows

    def raw(self, rows=None):return b'\n'.join(json.dumps(r).encode() for r in (self.rows if rows is None else rows))
    def test_complete(self):
        out=m.validate(self.raw(),self.save)
        self.assertEqual(out['earned_rp'],6);self.assertEqual(out['manual_saves'],0)
        self.assertEqual(len(out['screens']),7);self.assertFalse(out['natural_arrival_accepted'])
    def test_every_owner_byte(self):
        for index in (1,5,10,15,17,22):
            for byte in range(64):
                rows=copy.deepcopy(self.rows);owner=bytearray.fromhex(rows[index]['owner']);owner[byte]^=128;rows[index]['owner']=owner.hex()
                with self.assertRaises(ValueError):m.validate(self.raw(rows),self.save)
    def test_seed_requires_zero_balance(self):
        save=bytearray(self.save);at=m.purchase.prior.prior.OFFSET
        body=bytearray(save[at:at+2048]);body[0x743]=6;save[at:at+2048]=m.purchase.prior.prior.old.seal(body)
        with self.assertRaises(ValueError):m.validate(self.raw(),bytes(save))
    def test_bad_seed_checksum(self):
        save=bytearray(self.save);save[m.purchase.prior.prior.OFFSET+12]^=1
        with self.assertRaises(ValueError):m.validate(self.raw(),bytes(save))
    def test_missing_row(self):
        with self.assertRaises(ValueError):m.validate(self.raw(self.rows[:-1]),self.save)
    def test_extra_row(self):
        with self.assertRaises(ValueError):m.validate(self.raw(self.rows+[{}]),self.save)
    def test_reordered_row(self):
        rows=copy.deepcopy(self.rows);rows[17],rows[22]=rows[22],rows[17]
        with self.assertRaises(ValueError):m.validate(self.raw(rows),self.save)
    def test_duplicate_key(self):
        with self.assertRaises(ValueError):m.validate(self.raw().replace(b'"fresh_cores": 2',b'"fresh_cores": 2,"fresh_cores": 2'),self.save)
    def test_nonfinite(self):
        with self.assertRaises(ValueError):m.load(b'{"x":NaN}')
    def test_generated_barrier(self):
        source=(ROOT/'tools/mgba_pr16_research_photo.c').read_text()
        setup=source[source.index('static struct mCore*ph_setup'):source.index('static void ph_invariants')]
        self.assertEqual(setup.count('si_guard(c)'),1)
        self.assertLess(setup.index('QOL_SET_WARP_DESTINATION'),setup.index('si_guard(c)'))
        for term in ('SI_OWNER,','SI_OWNER+4,','lc_fixture','FieldPhoto','CreditActivity','si_transaction'):
            self.assertNotIn(term,setup)
        main=source[source.index('int main(int argc'):]
        for term in ('si_normal_save','up_select','up_finish','ct_setup','call_preserving','write8','write32','setRegister','fixture(c'):
            self.assertNotIn(term,main)
        self.assertIn('read32(c,SI_COUNTER)==target',source)
        self.assertIn('ph_screen(stage,"outcome",hash)',source)
    def test_generate_does_not_call_accepted_mains(self):
        seed=b'seed';old=b'old';new=b'new'
        with mock.patch.object(m.catalog,'generate',return_value=('static char*s="'+m.identity(old)['sha256']+'";int main(int argc,char**argv){return 0;}').encode()),mock.patch.object(m.purchase,'fixture',return_value=(old,{})),mock.patch.object(m,'fixture',return_value=(new,{})):
            source=m.generate(seed).decode()
        self.assertEqual(source.count('int main(int argc,char**argv){'),1)
        self.assertEqual(source.count('accepted_catalog_main('),1)
        self.assertIn(m.identity(new)['sha256'],source)
    def test_physical_rejects_other_rom(self):
        with self.assertRaises(ValueError):m.physical(b'not a ROM')

def mutate(index,key,value):
    def test(self):
        rows=copy.deepcopy(self.rows);rows[index][key]=value
        with self.assertRaises(ValueError):m.validate(self.raw(rows),self.save)
    return test
CASES={
 'root_bool':(0,'activity',True),'root_wrong':(0,'script',0x093C0328),
 'prompt_unknown':(3,'prompt','another'),'prompt_keys':(3,'entry_keys',1),
 'prompt_image':(3,'screen_sha256','0'*64),'prompt_extra':(3,'extra',1),
 'confirmation':(4,'confirmed',True),'boolean_result':(4,'activity_result',False),
 'result_earn':(9,'activity_result',4),'result_duplicate':(14,'activity_result',0),
 'frame_backwards':(14,'frame',999),'frame_bool':(14,'frame',True),
 'image_during_save':(8,'screen_sha256',m.SCREENS['photo-earn-prompt.ppm']),
 'new_saves_on_duplicate':(15,'counter',5),'lost_continue':(17,'counter',2),
 'changed_item':(22,'item_quantity',1),'changed_party':(22,'party_count',5),
 'changed_inventory':(22,'inventory_sha256','4'*64),'bad_inventory_hash':(22,'party_sha256','x'*64),
 'checksum_bool':(23,'checksum_valid',1),'changed_ledger':(23,'ledger_sha256','0'*64),
 'unrelated_ledger':(23,'unrelated_ledger_sha256','0'*64),'blocked':(23,'recovery_blocked',1),
 'schema_version':(23,'version',1),'closing_extra':(-1,'extra',1),
 'accepted_all':(-1,'all_activities_accepted',True),'accepted_arrival':(-1,'natural_arrival_accepted',True),
 'accepted_connection':(-1,'shop_connection_accepted',True),'manual_save':(-1,'manual_saves',1),
 'bool_counter':(-1,'guarded_host_writes',False),'wrong_rp':(-1,'earned_rp',10),
}
for name,args in CASES.items():setattr(PhotoTests,'test_reject_'+name,mutate(*args))
if __name__=='__main__':unittest.main()
