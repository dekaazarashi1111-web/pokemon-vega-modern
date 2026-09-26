"""新しい空判定修復/表示oracleだけ。私有ROM/seed・旧nativeは実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_map_view as m

class MapViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=m.load((ROOT/m.RECIPE).read_bytes())['candidate']
        old=m.photo.purchase.prior.prior.old
        cls.owner=bytearray(64);cls.owner[0],cls.owner[1],cls.owner[6],cls.owner[36]=1,64,1,1
        body=bytearray(2048);body[:8]=b'VGS1\x02\0\0\x08';body[0x73f:0x77f]=cls.owner;cls.body=old.seal(body)
        save=bytearray(131072);offset=m.photo.purchase.prior.prior.OFFSET;save[offset:offset+2048]=cls.body;cls.save=bytes(save)
        rows=[m.photo.BINDING.copy()]
        def stage(name,earned):
            owner=bytearray(cls.owner);owner[7]=1
            if earned:owner[4]=6;owner[10]=6;owner[24]=6;owner[27]=4;owner[36]=2
            ledger=bytearray(cls.body);ledger[0x73f:0x77f]=owner;ledger=old.seal(ledger)
            other=bytearray(ledger);other[4:6]=bytes(2);other[8:12]=bytes(4);other[0x73f:0x77f]=bytes(64)
            rows.append(dict(event=name,counter=2+2*earned,item_quantity=0,inventory_sha256='1'*64,
                other_inventory_sha256='2'*64,party_sha256='3'*64,party_count=6,owner=owner.hex()))
            rows.append(dict(ledger_event=name,version=2,size=2048,checksum_valid=True,
                ledger_sha256=m.identity(ledger)['sha256'],unrelated_ledger_sha256=m.identity(other)['sha256'],migration_dirty=0,recovery_blocked=0))
        def visual(name):
            return dict(visual=name,map=[96,37],position=[48,5],layout_id=497,layout=0x092A4498,
                        primary=0x0924BBDC,secondary=0x09237EC8,view_empty=True,screen=m.SCREENS['visual-'+name+'.ppm'])
        stage('fixture',False)
        rows += [dict(prompt='earn',entry_keys=64,screen_sha256=m.photo.SCREENS['photo-earn-prompt.ppm']),
                 dict(outcome='earn',screen_sha256=m.photo.SCREENS['photo-earn-outcome.ppm']),
                 dict(visit='earn',confirmed=True,activity_result=0,frame=2354)]
        stage('earned',True);rows.append(visual('earned'));stage('cold',True);rows += [visual('cold'),visual('cold_prompt'),
            dict(invariants='after-cold-prompt',full_flash_unchanged=True,full_ledger_unchanged=True,full_bag_party_unchanged=True,counter=4),m.closing('photo-cold-visual',cls.candidate)]
        cls.rows=rows
        cls.boundary=[dict(boundary='saved-map-view',view_bytes=512,neighbor_bytes=512,inside_one_hot_cases=256,
                          outside_one_hot_cases=256,zero_case=1,source_unchanged=True,clear_bytes=512,
                          clear_neighbor_unchanged=True,flash_unchanged=True),m.closing('predicate-boundary',cls.candidate)]
    def raw(self,rows):return b'\n'.join(json.dumps(r).encode() for r in rows)
    def validate(self,rows=None,case='photo-cold-visual',save=None,screens=None):
        return m.validate(self.raw(self.rows if rows is None else rows),case,self.candidate,self.save if save is None else save,m.SCREENS if screens is None else screens)
    def test_complete_photo(self):self.assertEqual(self.validate()['photo_earning_regressions'],1)
    def test_complete_boundary(self):self.assertEqual(self.validate(self.boundary,'predicate-boundary')['predicate_calls'],513)
    def test_actual_single_byte_recipe(self):
        recipe=m.load((ROOT/m.RECIPE).read_bytes());self.assertEqual(recipe['patches'],[dict(offset=0x58A48,before='ff010000',after='ff000000')]);self.assertEqual(recipe['changed_bytes'],1)
        self.assertEqual(recipe['saved_view_bytes'],512);self.assertEqual(recipe['roots']['0x81c7a88']['size'],4)
    def test_synthetic_apply_and_full_rollback(self):
        raw=bytearray(0x2000000);raw[m.OFFSET:m.OFFSET+4]=m.BEFORE;raw=bytes(raw)
        with mock.patch.object(m,'PARENT',m.identity(raw)):
            recipe=m.build_recipe(raw);out,receipt=m.apply(raw,recipe)
            self.assertEqual(out[:m.OFFSET]+m.BEFORE+out[m.OFFSET+4:],raw)
            self.assertTrue(receipt['whole_rom_rollback_matches_parent']);self.assertEqual(receipt['changed_bytes'],1)
            for key,value in [('after_last_index',511),('saved_view_bytes',1024),('changed_bytes',2),('release_ready',True)]:
                wrong=copy.deepcopy(recipe);wrong[key]=value
                with self.assertRaises(ValueError):m.apply(raw,wrong)
            with self.assertRaises(ValueError):m.apply(out,recipe)
    def test_wrong_parent_rejected(self):
        with self.assertRaises(ValueError):m.build_recipe(b'not a ROM')
    def test_nonbytes_parent_rejected(self):
        with self.assertRaises(ValueError):m.build_recipe(bytearray(32))
    def test_recipe_literal_preimage(self):
        raw=b'\0'*(m.OFFSET+4)
        with mock.patch.object(m,'PARENT',m.identity(raw)),self.assertRaises(ValueError):m.build_recipe(raw)
    def test_generated_candidate_and_no_accepted_main_call(self):
        base=('char*hash="'+m.PARENT['sha256']+'";int main(int argc,char**argv){return 0;}').encode()
        with mock.patch.object(m.photo,'generate',return_value=base):text=m.generate(b'unused',self.candidate).decode()
        self.assertEqual(text.count('int main(int argc,char**argv){'),1)
        self.assertEqual(text.count('accepted_photo_main('),1);self.assertIn(self.candidate['sha256'],text)
    def test_generator_rejects_double_main(self):
        with mock.patch.object(m.photo,'generate',return_value=b'int main(int argc,char**argv){'),self.assertRaises(ValueError):m.generate(b'unused',self.candidate)
    def test_photo_observation_has_no_host_write(self):
        source=(ROOT/m.C).read_text();body=source[source.index('static void mv_photo('):source.index('int main(')]
        for word in ('write8','write32','si_call','si_transaction','si_restore','si_normal_save','accepted_photo_main','ph_visit(c,"decline"','ph_visit(c,"duplicate"'):
            self.assertNotIn(word,body)
        self.assertEqual(body.count('ph_visit('),1);self.assertIn('si_guard(c)',body)
    def test_all_owner_bytes(self):
        for at in (1,6,9):
            for i in range(64):
                rows=copy.deepcopy(self.rows);body=bytearray.fromhex(rows[at]['owner']);body[i]^=128;rows[at]['owner']=body.hex()
                with self.assertRaises(ValueError):self.validate(rows)
    def test_complete_fixture_required(self):
        with self.assertRaises(ValueError):self.validate(save=self.save[:-1])
    def test_fixture_checksum(self):
        save=bytearray(self.save);save[m.photo.purchase.prior.prior.OFFSET+20]^=1
        with self.assertRaises(ValueError):self.validate(save=bytes(save))
    def test_fixture_zero_rp_required(self):
        at=m.photo.purchase.prior.prior.OFFSET;save=bytearray(self.save);body=bytearray(self.body);body[0x743]=6;save[at:at+2048]=m.photo.purchase.prior.prior.old.seal(body)
        with self.assertRaises(ValueError):self.validate(save=bytes(save))
    def test_missing_or_extra_row(self):
        for rows in (self.rows[:-1],self.rows+[{}]):
            with self.assertRaises(ValueError):self.validate(rows)
    def test_interleaving_order(self):
        rows=copy.deepcopy(self.rows);rows[1],rows[2]=rows[2],rows[1]
        with self.assertRaises(ValueError):self.validate(rows)
    def test_duplicate_key(self):
        raw=self.raw(self.rows).replace(b'"fresh_cores": 2',b'"fresh_cores": 2,"fresh_cores": 2')
        with self.assertRaises(ValueError):m.validate(raw,'photo-cold-visual',self.candidate,self.save,m.SCREENS)
    def test_nonfinite(self):
        with self.assertRaises(ValueError):m.load(b'{"x":NaN}')
    def test_changed_reviewed_image_set(self):
        screens=dict(m.SCREENS);screens['visual-cold.ppm']='0'*64
        with self.assertRaises(ValueError):self.validate(screens=screens)
    def test_boundary_mutations(self):
        for key,value in self.boundary[0].items():
            rows=copy.deepcopy(self.boundary);rows[0][key]=False if type(value) is bool else value+1 if type(value) is int else 'bad'
            with self.assertRaises(ValueError):self.validate(rows,'predicate-boundary')
    def test_boundary_result_mutations(self):
        for key,value in self.boundary[-1].items():
            rows=copy.deepcopy(self.boundary);rows[-1][key]=not value if type(value) is bool else value+1 if type(value) is int else 'bad'
            with self.assertRaises(ValueError):self.validate(rows,'predicate-boundary')

def mutation(at,key,value):
    def test(self):
        rows=copy.deepcopy(self.rows);rows[at][key]=value
        with self.assertRaises(ValueError):self.validate(rows)
    return test
MUTATIONS={
 'map':(11,'map',[96,36]),'layout':(11,'layout',0x092A449C),'tileset':(11,'primary',0),
 'empty_bool':(11,'view_empty',1),'position':(11,'position',[48,4]),'blue_image':(11,'screen','e5dc8b65607ab06b09f9989ec991abb26334555d6833065d412baedd37118098'),
 'cold_label':(11,'visual','earned'),'visual_extra':(11,'extra',True),
 'prompt_keys':(3,'entry_keys',1),'prompt_image':(3,'screen_sha256','0'*64),'reward_image':(4,'screen_sha256','0'*64),
 'credit':(5,'activity_result',4),'credit_bool':(5,'activity_result',False),'confirmation':(5,'confirmed',False),'frame':(5,'frame',True),
 'saved_counter':(6,'counter',3),'cold_counter':(9,'counter',5),'counter_bool':(1,'counter',True),
 'bag':(9,'inventory_sha256','4'*64),'party_count':(9,'party_count',5),'item':(9,'item_quantity',1),'hash_format':(9,'party_sha256','x'*64),
 'ledger':(10,'ledger_sha256','0'*64),'other_owner':(10,'unrelated_ledger_sha256','0'*64),'checksum_type':(10,'checksum_valid',1),'recovery':(10,'recovery_blocked',1),
 'flash':(13,'full_flash_unchanged',False),'tail_type':(13,'counter',True),'extra_save':(-1,'manual_saves',1),
 'hidden_repeat':(-1,'photo_earning_regressions',0),'host_write':(-1,'guarded_host_writes',1),'natural_claim':(-1,'natural_arrival_accepted',True),'release':(-1,'release_ready',True)
}
for name,args in MUTATIONS.items():setattr(MapViewTests,'test_reject_'+name,mutation(*args))
if __name__=='__main__':unittest.main()
