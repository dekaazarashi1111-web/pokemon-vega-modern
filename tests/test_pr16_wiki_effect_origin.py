"""今回追加のeffect由来分類だけを検証。ROM・native・旧受入suiteは呼ばない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from pr16_candidate_wiki_inputs import Inputs, digest
from pr16_candidate_wiki_effect_origin import audit, classify, load_lowering, python_proof, T04_KEY_ALIASES

class EffectOriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.lowering, cls.raw = load_lowering(Inputs())
    def model(self):
        rows = []
        for mid, ops in self.lowering.EXPECTED_MOVE_PLANS.items():
            _, eid = self.lowering._compile_commands(mid, ops)
            rows.append(dict(id=mid,key=T04_KEY_ALIASES.get(mid, f'MOVE_KEY_VEGA_{mid}'),effect_id=eid,evidence='EXACT_CANDIDATE_ROM',
                row_sha256='a'*64,effect_novelty='EXISTING_EFFECT_ID_REUSED',canonical_fields={}))
        for mid, key, fields in ((0,'NONE',{}),(1,'POUND',{'fields':{'effect':'EFFECT_HIT'},'source_symbol':'MOVE_POUND'}),(511,'VEGA_511',{})):
            rows.append(dict(id=mid,key='MOVE_KEY_'+key,effect_id=0,evidence='EXACT_CANDIDATE_ROM',row_sha256='b'*64,
                effect_novelty='EXISTING_EFFECT_ID_REUSED',canonical_fields=fields))
        return {'moves':rows,'candidate':{'sha256':'c'*64,'size':33554432,'crc32':'12345678'},
            'source_model':{'effect_ids':{'EFFECT_HIT':0},'source_repository':'locked/source','source_commit':'d'*40,'source_bindings':{}}}
    def run_audit(self,m=None): return audit(m or self.model(),self.lowering,self.raw)
    def test_seventy_adapters(self): self.assertEqual(self.run_audit()['summary']['t04_source_adapters'],70)
    def test_all_records_preserved(self): self.assertEqual(len(self.run_audit()['records']),73)
    def test_none_not_playable(self): self.assertEqual(next(r for r in self.run_audit()['records'] if r['move_id']==0)['status'],'MOVE_NONE_NOT_PLAYABLE')
    def test_unmatched_511_not_inferred(self): self.assertEqual(self.run_audit()['unresolved_move_ids'],[511])
    def test_upstream_declaration_not_handler_proof(self):
        row=next(r for r in self.run_audit()['records'] if r['move_id']==1)
        self.assertEqual(row['status'],'LOCKED_UPSTREAM_EFFECT_DECLARATION');self.assertEqual(row['full_handler_lineage'],'DEFERRED_AUDIT')
    def test_changed_effect_rejected(self):
        m=self.model();m['moves'][0]['effect_id']=65500
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_upstream_changed_effect_rejected(self):
        m=self.model();next(r for r in m['moves'] if r['id']==1)['effect_id']=3
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_duplicate_id_rejected(self):
        m=self.model();m['moves'].append(copy.deepcopy(m['moves'][0]))
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_missing_adapter_rejected(self):
        m=self.model();m['moves'].pop(0)
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_reassigned_key_rejected(self):
        m=self.model();m['moves'][0]['key']='MOVE_KEY_OTHER'
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_bool_id_rejected(self):
        m=self.model();m['moves'][-1]['id']=True
        with self.assertRaises(ValueError):self.run_audit(m)
    def test_no_native_promotion(self):
        v=self.run_audit();self.assertEqual(v['new_native_runs'],0);self.assertFalse(v['full_handler_history_complete'])
        self.assertTrue(all(r['native_acceptance']=='DEFERRED_AUDIT' for r in v['records']))
    def test_all_patch_contracts_remain_unaccepted(self):
        self.assertTrue(all(r['installed_on_candidate']=='DEFERRED_AUDIT' for r in self.run_audit()['source_patch_contracts']))
    def test_delegate(self):self.assertEqual(classify(['goto BS_187_Yawn'],[])['script_origin'],'UPSTREAM_SCRIPT_DELEGATE')
    def test_parameter_adapter(self):self.assertEqual(classify(['setmoveeffect MOVE_EFFECT_POISON','goto BS_STANDARD_HIT'],[])['script_origin'],'UPSTREAM_EFFECT_PARAMETER_ADAPTER')
    def test_dynamic_prepare(self):self.assertEqual(classify(['callasm VegaMoveEffectPrepare','goto BS_STANDARD_HIT'],[])['script_origin'],'PROJECT_DYNAMIC_PREPARE_ADAPTER')
    def test_composed_script(self):self.assertEqual(classify(['attackcanceler','goto BS_MOVE_END'],[])['script_origin'],'PROJECT_COMPOSED_SCRIPT')
    def test_delegate_still_has_local_query(self):
        row=classify(['goto BS_STANDARD_HIT'],['RECOIL_ONE_THIRD']);self.assertTrue(row['has_project_central_query']);self.assertFalse(row['new_engine_opcode_claimed'])
    def test_empty_script_rejected(self):
        with self.assertRaises(ValueError):classify([],[])
    def test_unknown_callasm_rejected(self):
        with self.assertRaises(ValueError):classify(['callasm InventedHandler'],[])
    def test_duplicate_query_rejected(self):
        with self.assertRaises(ValueError):classify(['goto BS_STANDARD_HIT'],['A','A'])
    def test_python_proof_line_hash(self):
        v=python_proof(self.raw,'_compile_commands');lines=self.raw.decode().splitlines(keepends=True)
        self.assertEqual(v['unit_sha256'],digest(''.join(lines[v['start_line']-1:v['end_line']]).encode()))
    def test_missing_python_symbol_rejected(self):
        with self.assertRaises(ValueError):python_proof(self.raw,'nonexistent')
    def test_memawashi_not_plain_hit(self):
        row=next(r for r in self.run_audit()['records'] if r['move_id']==429)
        self.assertEqual(row['candidate_effect_id'],0);self.assertEqual(row['origin']['script_origin'],'PROJECT_COMPOSED_SCRIPT')
    def test_named_t04_keys_preserved(self):
        rows={r['move_id']:r for r in self.run_audit()['records']}
        self.assertEqual(rows[470]['move_key'],'MOVE_KEY_SOUL_BITE');self.assertEqual(rows[509]['move_key'],'MOVE_KEY_DARK_SNIPE')
    def test_deterministic(self):self.assertEqual(self.run_audit(),self.run_audit())

if __name__=='__main__':unittest.main()
