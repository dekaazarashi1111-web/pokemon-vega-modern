"""今回追加のhidden patch source/slot差分だけを検証する。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pr16_candidate_wiki_inputs import Inputs, digest
from pr16_candidate_wiki_consumers import Source
from pr16_candidate_wiki_hidden_patch import SNAPSHOT, PROFILE, audit, slot_rule, verify_contract, read_source

class ProfileInputs(Inputs):
    def __init__(self, text): super().__init__(); self.profile=text
    def raw(self, path):
        return self.profile.encode() if path==PROFILE else super().raw(path)

class HiddenPatchTests(unittest.TestCase):
    def source(self):return Source(Inputs().json(SNAPSHOT))
    def model(self):
        species=[];hidden=[]
        for sid,slots in enumerate(([0,0,0],[1,2,3],[20,20,20],[1,3,3],[0,0,3])):
            h={'species_id':sid,'species_key':f'SPECIES_KEY_{sid}','ability_id':slots[2],
               'first_supply':'SUPPLY_NOT_FOUND_IN_CURRENT_SOURCES','patch':'DEFERRED_AUDIT'}
            species.append({'id':sid,'key':h['species_key'],'ability_ids':list(slots),'hidden_ability':h,'evidence':'EXACT_CANDIDATE_ROM'})
            hidden.append(copy.deepcopy(h))
        return {'candidate':{'sha256':'a'*64},'species':species,'hidden_abilities':hidden,
                'consumer_audit':{'hidden_supply_rules':{}}}
    def run_audit(self,m=None):return audit(m or self.model(),self.source(),{'item_id':943})
    def test_locked_source_contract(self):verify_contract(self.source())
    def test_unassigned(self):self.assertEqual(slot_rule([1,2],0)['status'],'NO_HIDDEN_ABILITY_ASSIGNED')
    def test_distinct_slots(self):self.assertEqual(slot_rule([1,2],3)['eligible_nonzero_normal_ability_ids'],[1,2])
    def test_same_id_no_effect_even_normal_flag(self):self.assertEqual(slot_rule([20,20],20)['status'],'NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID')
    def test_one_slot_matches(self):
        r=slot_rule([3,2],3);self.assertEqual(r['status'],'DEPENDS_ON_CURRENT_NORMAL_ABILITY');self.assertEqual(r['eligible_nonzero_normal_ability_ids'],[2])
    def test_both_zero_need_engine(self):self.assertEqual(slot_rule([0,0],3)['status'],'NORMAL_ABILITY_RESOLUTION_REQUIRED')
    def test_zero_not_assumed_effective_normal(self):
        r=slot_rule([1,0],3);self.assertEqual(r['eligible_nonzero_normal_ability_ids'],[1]);self.assertTrue(r['zero_normal_slot_requires_engine_resolution'])
    def test_duplicate_normal_deduplicated(self):self.assertEqual(slot_rule([1,1],3)['eligible_nonzero_normal_ability_ids'],[1])
    def test_16bit_ability_supported(self):self.assertEqual(slot_rule([300,301],302)['hidden_ability_id'],302)
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):slot_rule([True,2],3)
    def test_negative_rejected(self):
        with self.assertRaises(ValueError):slot_rule([1,-1],3)
    def test_overflow_rejected(self):
        with self.assertRaises(ValueError):slot_rule([1,2],65536)
    def test_three_normals_rejected(self):
        with self.assertRaises(ValueError):slot_rule([1,2,3],4)
    def test_mirrors_synchronized(self):
        m=self.model();self.run_audit(m)
        for a,b in zip(m['species'],m['hidden_abilities']):self.assertEqual(a['hidden_ability']['patch'],b['patch'])
    def test_first_supply_not_promoted(self):
        m=self.model();v=self.run_audit(m)
        self.assertFalse(v['all_first_supply_routes_complete']);self.assertTrue(all(not r['first_supply_proven'] for r in v['records']))
        self.assertTrue(all(h['first_supply']=='SUPPLY_NOT_FOUND_IN_CURRENT_SOURCES' for h in m['hidden_abilities']))
    def test_mismatched_mirror_rejected(self):
        m=self.model();m['hidden_abilities'][1]['ability_id']=99
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_duplicate_mirror_rejected(self):
        m=self.model();m['hidden_abilities'][1]=copy.deepcopy(m['hidden_abilities'][0])
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_changed_source_rejected(self):
        data=Inputs().json(SNAPSHOT);u=data['sources']['src/party_menu.c']['units'][-1];u['text']=u['text'].replace('RemoveBagItem(item, 1);','RemoveBagItem(item, 2);');u['sha256']=digest(u['text'].encode())
        with self.assertRaises(ValueError):verify_contract(Source(data))
    def test_source_hash_tamper_rejected(self):
        data=Inputs().json(SNAPSHOT);data['sources']['src/party_menu.c']['units'][0]['text']+='x'
        with self.assertRaises(ValueError):Source(data)
    def test_cancel_mutation_rejected(self):
        data=Inputs().json(SNAPSHOT);u=next(u for u in data['sources']['src/party_menu.c']['units'] if u['symbol']=='Task_HandleAbilityChangeYesNoInput');u['text']=u['text'].replace('case 1:','case 1: RemoveBagItem(item, 1);');u['sha256']=digest(u['text'].encode())
        with self.assertRaises(ValueError):verify_contract(Source(data))
    def test_unbound_disabled(self):self.assertIsInstance(read_source(ProfileInputs('#undef UNBOUND\n')),Source)
    def test_unbound_enabled_after_undef_rejected(self):
        with self.assertRaises(ValueError):read_source(ProfileInputs('#undef UNBOUND\n#define UNBOUND\n'))
    def test_unbound_comment_not_a_directive(self):
        with self.assertRaises(ValueError):read_source(ProfileInputs('/* #undef UNBOUND */\n'))
    def test_counts_all_slots(self):self.assertEqual(self.run_audit()['summary']['hidden_patch_records'],5)
    def test_native_remains_deferred(self):self.assertTrue(all(r['candidate_native_acceptance']=='DEFERRED_AUDIT' for r in self.run_audit()['records']))
    def test_deterministic(self):self.assertEqual(self.run_audit(),self.run_audit())

if __name__=='__main__':unittest.main()
