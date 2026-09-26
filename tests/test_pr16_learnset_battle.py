"""新しい自然戦闘の受入境界だけを検証。旧Bag/nativeを実行しない。"""
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_battle as b

class LearnedBattle(unittest.TestCase):
    def setUp(self):
        self.row={'status':'PASS','scope':b.SCOPE,'candidate_sha256':b.m.CANDIDATE['sha256'],'species':1029,'move':420,'slot':1,
            'initial_party_fixture':True,'bag_reruns':0,'host_write_barriers':3,'fresh_cores':2,'manual_saves':1,
            'party_preserved_bytes':100,'warnings_errors':0,'story_acquisition_verified':False,'issue19_complete':False,'release_ready':False,
            'enemy_species':19,'walking_steps':45,'boundary':10,'encounter':20,'selection':30,'chosen':31,'pp_spent':40,'damage':50,
            'returned':90,'pp_before':30,'pp_after':29,'enemy_hp_before':18,'enemy_hp_min':0,'outcome':1}
        a=b'\x01'*100;c=a[:30]+b'\x02'+a[31:]
        self.err=b''.join(b'GAMEPLAY_PARTY label='+label+b' counter='+str(counter).encode()+b' hex='+raw.hex().encode()+b'\n'
            for label,counter,raw in ((b'battle_fixture',2,a),(b'battle_returned',2,c),(b'battle_saved',3,c),(b'battle_continued',3,c)))

    def validate(self):return b.validate(json.dumps(self.row).encode(),self.err)

    def test_complete_physical_result(self):
        self.assertEqual(self.validate()['persisted_party']['size'],100)

    def test_no_damage_rejected(self):
        self.row['enemy_hp_min']=18
        with self.assertRaises(ValueError):self.validate()

    def test_no_pp_rejected(self):
        self.row['pp_after']=30
        with self.assertRaises(ValueError):self.validate()

    def test_wrong_move_rejected(self):
        self.row['move']=1063
        with self.assertRaises(ValueError):self.validate()

    def test_wrong_rom_rejected(self):
        self.row['candidate_sha256']='0'*64
        with self.assertRaises(ValueError):self.validate()

    def test_skipped_natural_encounter_rejected(self):
        self.row['encounter']=0
        with self.assertRaises(ValueError):self.validate()

    def test_party_corruption_rejected(self):
        self.err=self.err.replace(b'label=battle_continued counter=3 hex=01',b'label=battle_continued counter=3 hex=03')
        with self.assertRaises(ValueError):self.validate()

    def test_missing_fresh_continue_rejected(self):
        self.err=self.err.split(b'GAMEPLAY_PARTY label=battle_continued')[0]
        with self.assertRaises(ValueError):self.validate()

    def test_story_promotion_rejected(self):
        self.row['initial_party_fixture']=False
        with self.assertRaises(ValueError):self.validate()

    def test_release_promotion_rejected(self):
        self.row['release_ready']=True
        with self.assertRaises(ValueError):self.validate()

    def test_unknown_fields_rejected(self):
        self.row['unproven_owner']=999
        with self.assertRaises(ValueError):self.validate()

    def test_fixture_explicit_boundaries(self):
        audit={'paths':{'town':[[21,20]],'grass':[[12,39]]}}
        self.assertIn(b'LB_SOURCE_CASE 11',b.fixture_header(b'\1'*100,11,audit))
        for raw,idx,paths in ((b'',11,audit),(b'\1'*100,0,audit),(b'\1'*100,11,{'paths':{'town':[[1,2]]}})):
            with self.assertRaises(ValueError):b.fixture_header(raw,idx,paths)

    def test_zip_path_escape_rejected(self):
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr('../escape','x')
        with self.assertRaises(ValueError):b.zip_members(raw.getvalue())

    def test_zip_duplicate_rejected(self):
        import warnings
        raw=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(raw,'w') as z:z.writestr('one','x');z.writestr('one','y')
        with self.assertRaises(ValueError):b.zip_members(raw.getvalue())

    def test_native_barriers_no_target_call(self):
        s=(ROOT/b.C).read_text()
        self.assertEqual(s.count('a_guard(c);'),3)
        for part in s.split('a_guard(c);')[1:]:
            segment=part.split('a_restore(c,&saved);')[0]
            for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'create_mon('):self.assertNotIn(forbidden,segment)
        self.assertNotIn('BATTLE_CORE_START_WILD',s)
        self.assertNotIn('BATTLE_CORE_GLOBAL_RNG',s)
        self.assertNotIn('a_scene(',s)

    def test_save_and_continue_only_generalize_position(self):
        old=(ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text();new=(ROOT/b.C).read_text()
        save=old[old.index('static bool a_save('):old.index('static void a_array(')].replace('a_save(','lb_normal_save(').replace('a_field(c)','lb_field(c)')
        cont=old[old.index('static bool a_continue('):old.index('static void a_key_item(')].replace('a_continue(','lb_normal_continue(').replace('p02s_continue_position(c)','lb_resume_position(c)').replace('a_field(c)','lb_field(c)')
        self.assertIn(save,new);self.assertIn(cont,new)

if __name__=='__main__':unittest.main()
