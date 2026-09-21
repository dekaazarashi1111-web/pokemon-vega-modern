"""新規runtime Z分岐だけを検証。既存native/受入CLIを呼ばない。"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pr16_candidate_wiki_inputs import BASE, identity
from pr16_candidate_wiki_consumers import Source, key_for
from pr16_candidate_wiki_runtime_z import physicality_symbols, aligned_matches, table_binding, split_rule, refine

TABLE = 'gMovesThatChangePhysicality:\n.hword MOVE_PHOTONGEYSER\n.hword MOVE_LIGHT_THAT_BURNS_THE_SKY\n.hword MOVE_TABLES_TERMIN\n'

class RuntimeZTests(unittest.TestCase):
    def test_table_symbols(self):
        self.assertEqual(physicality_symbols(TABLE),['MOVE_PHOTONGEYSER','MOVE_LIGHT_THAT_BURNS_THE_SKY'])
    def test_table_needs_label(self):
        with self.assertRaises(ValueError):physicality_symbols(TABLE.replace('gMovesThatChangePhysicality:','wrong:'))
    def test_table_needs_terminator(self):
        with self.assertRaises(ValueError):physicality_symbols(TABLE.replace('.hword MOVE_TABLES_TERMIN\n',''))
    def test_table_rejects_duplicate(self):
        with self.assertRaises(ValueError):physicality_symbols(TABLE.replace('MOVE_LIGHT_THAT_BURNS_THE_SKY','MOVE_PHOTONGEYSER'))
    def test_table_rejects_directive(self):
        with self.assertRaises(ValueError):physicality_symbols(TABLE.replace('.hword MOVE_PHOTONGEYSER','.byte 1'))
    def test_table_rejects_middle_terminator(self):
        with self.assertRaises(ValueError):physicality_symbols(TABLE.replace('.hword MOVE_PHOTONGEYSER','.hword MOVE_TABLES_TERMIN'))
    def test_wrong_ffff_terminator_is_not_a_match(self):
        self.assertEqual(table_binding(struct.pack('<HHH',3,4,65535),[3,4])['matches'],[])
    def test_terminator_provenance_is_explicit(self):
        row=table_binding(struct.pack('<HHH',3,4,0xFEFE),[3,4])
        self.assertEqual(row['terminator'],0xFEFE)
        self.assertEqual(row['terminator_source']['line'],11)
    def test_missing_signature_not_promoted(self):
        self.assertEqual(table_binding(bytes(32),[3,4])['status'],'NO_CANDIDATE_BYTE_MATCH')
    def test_six_byte_table_and_pointer(self):
        raw=bytearray(64);raw[8:14]=struct.pack('<HHH',3,4,0xFEFE);struct.pack_into('<I',raw,20,BASE+8)
        result=table_binding(bytes(raw),[3,4])
        self.assertEqual(result['matches'],[{'address':'0x08000008','aligned_pointer_value_sites':['0x08000014']}])
        self.assertEqual(result['signature_size'],6)
        self.assertEqual(result['compiled_consumer_entry_binding'],'DEFERRED_AUDIT')
    def test_unaligned_signature_ignored(self):
        self.assertEqual(aligned_matches(b'xabcdef',b'abcdef',2),[])
    def test_match_limit(self):
        with self.assertRaises(ValueError):aligned_matches(b'AB'*4,b'AB',2,3)
    def test_bad_id_rejected(self):
        for ids in ([0],[65535],[0xFEFE],[1,1],[True]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):table_binding(bytes(32),ids)
    def test_physical_remains_physical(self):
        self.assertEqual(split_rule('MOVE_KEY_POUND',0,set())['possible_categories'],[0])
    def test_special_remains_special(self):
        self.assertEqual(split_rule('MOVE_KEY_SURF',1,set())['possible_categories'],[1])
    def test_status_excluded_even_if_in_table(self):
        self.assertEqual(split_rule('MOVE_KEY_X',2,{'MOVE_KEY_X'})['possible_categories'],[])
    def test_stat_tie_is_special(self):
        self.assertEqual(split_rule('MOVE_KEY_X',0,{'MOVE_KEY_X'})['tie_category'],1)
    def test_tera_conditional(self):
        for key in ('MOVE_KEY_TERABLAST','MOVE_KEY_TERASTARSTORM'):
            rule=split_rule(key,1,set())
            self.assertEqual(rule['rule'],'TERA_CONDITIONAL_STAT_COMPARISON')
            self.assertEqual(rule['inactive_tera_fallback'],'CANDIDATE_BASE_SPLIT')
    def test_shell_same_bank_static(self):
        rule=split_rule('MOVE_KEY_SHELLSIDEARM',1,set())
        self.assertEqual(rule['rule'],'SHELL_SIDE_ARM_SELF_BANK_BASE_SPLIT')
        self.assertEqual(rule['possible_categories'],[1]);self.assertTrue(rule['same_bank_arguments'])
    def test_old_split_explicit(self):
        self.assertEqual(split_rule('MOVE_KEY_POUND',0,set(),True)['rule'],'OLD_TYPE_BASED_SPLIT')
    def test_bad_category(self):
        with self.assertRaises(ValueError):split_rule('MOVE_KEY_POUND',3,set())

class LockedSourceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source(json.loads((ROOT/'content/modernization/pr16_candidate_wiki_consumer_sources.json').read_bytes()))
        cls.inventory=json.loads((ROOT/'content/modernization/pr16_wiki_remaining_source_inventory.json').read_bytes())
    def example(self):
        raw=bytearray(64);raw[8:14]=struct.pack('<HHH',1,2,0xFEFE)
        moves=[]
        for mid,key in enumerate(['MOVE_KEY_PHOTONGEYSER','MOVE_KEY_LIGHT_THAT_BURNS_THE_SKY','MOVE_KEY_POUND','MOVE_KEY_SHELLSIDEARM'],1):
            category=0 if key=='MOVE_KEY_POUND' else 1
            moves.append({'id':mid,'key':key,'category_id':category,'generic_z':{'status':'DAMAGE_MOVE_SOURCE_RULE','targets':[{'category_id':0},{'category_id':1}]}})
        model={'candidate':identity(raw),'moves':moves,'consumer_audit':{'generic_z':{}},'followup_audit':{'summary':{},'remaining_work_ja':['汎用Zの静的対応は追加済み。','他の残件']}}
        inv=copy.deepcopy(self.inventory);inv['candidate']=model['candidate']
        return model,inv,bytes(raw)
    def test_refine_filters_static_and_preserves_dynamic(self):
        m,inv,raw=self.example();refine(m,self.source,inv,raw,'')
        self.assertEqual([len(x['generic_z']['targets']) for x in m['moves']],[2,2,1,1])
        self.assertEqual(m['runtime_z_audit']['records'],4)
        self.assertEqual(m['followup_audit']['remaining_work_ja'][1],'他の残件')
        self.assertIs(m['consumer_audit']['generic_z']['records'][0],m['moves'][0]['generic_z'])
    def test_refine_requires_candidate_bytes(self):
        m,inv,raw=self.example()
        with self.assertRaises(ValueError):refine(m,self.source,inv,raw+b'x','')
    def test_refine_requires_source_commit(self):
        m,inv,raw=self.example();inv['source_commit']='changed'
        with self.assertRaises(ValueError):refine(m,self.source,inv,raw,'')
    def test_refine_rejects_profile_old_split(self):
        m,inv,raw=self.example()
        with self.assertRaises(ValueError):refine(m,self.source,inv,raw,'#define OLD_MOVE_SPLIT\n')
    def test_refine_rejects_missing_stable_key(self):
        m,inv,raw=self.example();m['moves'].pop(0)
        with self.assertRaises(ValueError):refine(m,self.source,inv,raw,'')

if __name__=='__main__':unittest.main()
