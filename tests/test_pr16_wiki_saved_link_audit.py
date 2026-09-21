"""今回の保存body/callee/511由来結合だけを試験。旧110試験・nativeは呼ばない。"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_candidate_wiki_saved_link as audit
import pr16_wiki_saved_link_snapshot as snapshot
from pr16_candidate_wiki_inputs import BASE, Inputs, ROOT, Rom, digest, stable
from pr16_candidate_wiki_link_graph import structural_graph


def symbol(name, raw, offset, size, status=audit.EXACT):
    sha = digest(raw[offset:offset+size])
    return {'symbol':name,'native_acceptance':audit.DEFERRED,'source_equivalence_proven':False,
        'status':status,'address':BASE+offset,'size':size,'saved_sha256':sha,'candidate_sha256':sha,
        'elf_symbol':{'symbol':name,'address':BASE+offset+1,'size':size,'type':2,'section':1}}


def miniature():
    raw = bytearray(32)
    raw[:6] = bytes.fromhex('00f002f87047')
    raw[8:10] = bytes.fromhex('7047')
    raw = bytes(raw)
    rows = {'Caller':symbol('Caller',raw,0,6),'Callee':symbol('Callee',raw,8,2)}
    graph = structural_graph(Rom(raw), BASE, BASE, BASE+6)
    graph.pop('nodes'); graph['saved_elf_full_extent_verified'] = True
    for call in graph['direct_calls']:
        call.update(saved_symbol_names=['Callee'],candidate_body_matched_names=['Callee'])
    return raw,rows,graph


class SavedLinkAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.symbols,self.graph = miniature()
    def invalid(self, row):
        with self.assertRaises((ValueError,KeyError,TypeError)):
            audit.verify_symbol(row,self.raw)
    def test_exact_full_body(self): audit.verify_symbol(self.symbols['Caller'],self.raw)
    def test_changed_current_body(self):
        with self.assertRaises(ValueError): audit.verify_symbol(self.symbols['Caller'],b'\0'*32)
    def test_misclassified_differs(self):
        row=copy.deepcopy(self.symbols['Caller']);row['status']=audit.DIFFERS;self.invalid(row)
    def test_preserved_differing_body(self):
        row=copy.deepcopy(self.symbols['Caller']);row['status']=audit.DIFFERS;row['saved_sha256']='0'*64
        audit.verify_symbol(row,self.raw)
    def test_native_promotion_rejected(self):
        row=copy.deepcopy(self.symbols['Caller']);row['native_acceptance']='PASS';self.invalid(row)
    def test_source_promotion_rejected(self):
        row=copy.deepcopy(self.symbols['Caller']);row['source_equivalence_proven']=True;self.invalid(row)
    def test_unknown_status(self):
        row=copy.deepcopy(self.symbols['Caller']);row['status']='PASS';self.invalid(row)
    def test_boolean_address(self):
        row=copy.deepcopy(self.symbols['Caller']);row['address']=True;self.invalid(row)
    def test_extent_mismatch(self):
        row=copy.deepcopy(self.symbols['Caller']);row['size']=4;self.invalid(row)
    def test_address_mismatch(self):
        row=copy.deepcopy(self.symbols['Caller']);row['address']+=2;self.invalid(row)
    def test_outside_body(self):
        row=copy.deepcopy(self.symbols['Caller']);row['address']=BASE+32;row['elf_symbol']['address']=BASE+33;self.invalid(row)
    def test_symbol_name_mismatch(self):
        row=copy.deepcopy(self.symbols['Caller']);row['symbol']='Other';self.invalid(row)
    def test_exact_named_call(self): audit.verify_calls(self.graph['direct_calls'],self.symbols)
    def test_differing_callee_not_promoted(self):
        self.symbols['Callee']['status']=audit.DIFFERS
        with self.assertRaises(ValueError): audit.verify_calls(self.graph['direct_calls'],self.symbols)
    def test_differing_callee_can_remain_unresolved(self):
        self.symbols['Callee']['status']=audit.DIFFERS
        self.graph['direct_calls'][0]['candidate_body_matched_names']=[]
        audit.verify_calls(self.graph['direct_calls'],self.symbols)
    def test_unknown_callee(self):
        with self.assertRaises(ValueError): audit.verify_calls(self.graph['direct_calls'],{})
    def test_wrong_callee_address(self):
        self.graph['direct_calls'][0]['target']+=2
        with self.assertRaises(ValueError): audit.verify_calls(self.graph['direct_calls'],self.symbols)
    def test_duplicate_names(self):
        self.graph['direct_calls'][0]['saved_symbol_names']*=2
        with self.assertRaises(ValueError): audit.verify_calls(self.graph['direct_calls'],self.symbols)
    def test_graph_matches_current(self):
        value=audit.verify_graph('Caller',self.graph,self.symbols['Caller'],self.raw,self.symbols)
        self.assertEqual(value['direct_calls'][0]['candidate_body_matched_names'],['Callee'])
        self.assertFalse(value['indirect_edges_resolved'])
    def test_graph_count_mutation(self):
        self.graph['node_count']+=1
        with self.assertRaises(ValueError): audit.verify_graph('Caller',self.graph,self.symbols['Caller'],self.raw,self.symbols)
    def test_graph_scope_promotion(self):
        self.graph['indirect_edges_resolved']=True
        with self.assertRaises(ValueError): audit.verify_graph('Caller',self.graph,self.symbols['Caller'],self.raw,self.symbols)
    def test_graph_for_differing_body_rejected(self):
        self.symbols['Caller']['status']=audit.DIFFERS
        with self.assertRaises(ValueError): audit.verify_graph('Caller',self.graph,self.symbols['Caller'],self.raw,self.symbols)
    def test_graph_inputs_unchanged(self):
        before=copy.deepcopy((self.graph,self.symbols))
        audit.verify_graph('Caller',self.graph,self.symbols['Caller'],self.raw,self.symbols)
        self.assertEqual(before,(self.graph,self.symbols))


class FrozenLineageTests(unittest.TestCase):
    def setUp(self):
        self.saved=snapshot.load(Inputs())
        self.rows=copy.deepcopy(self.saved['move_rows'])
        self.policy=Inputs().json('config/move_port.json')['mapping_policy']
        self.moves=[]
        for name in ('1','511'):
            row=self.rows[name]; current={'id':row['id'],'key':row['move_key']}
            current.update({b:row['battle'][a] for a,b in audit.BATTLE_FIELDS})
            current['row_sha256']=digest(bytes(row['battle'][a]&255 for a,b in audit.BATTLE_FIELDS))
            self.moves.append(current)
    def call(self): return audit.move511_lineage(self.rows,self.moves,self.policy)
    def rejected(self):
        with self.assertRaises((ValueError,KeyError,TypeError)): self.call()
    def test_canonical_origin(self): self.assertEqual(self.call()['status'],'FROZEN_VEGA_COMPAT_DUPLICATE_BOUND')
    def test_real_field_differences(self): self.assertEqual(self.call()['different_fields_from_canonical_pound'],['flags','z_move_power'])
    def test_alias_only_one(self): self.assertTrue(self.call()['canonical_pound_alias_does_not_target_511'])
    def test_no_native_or_handler_acceptance(self):
        r=self.call();self.assertEqual(r['native_acceptance'],audit.DEFERRED);self.assertEqual(r['full_handler_lineage'],audit.DEFERRED)
    def test_all_twelve_candidate_fields(self):
        for field in [b for a,b in audit.BATTLE_FIELDS]:
            with self.subTest(field=field):
                old=self.moves[1][field];self.moves[1][field]=old+1;self.rejected();self.moves[1][field]=old
    def test_row_hash_tampering(self): self.moves[1]['row_sha256']='0'*64;self.rejected()
    def test_stable_key_tampering(self): self.moves[1]['key']='MOVE_KEY_POUND';self.rejected()
    def test_alias_retarget(self): self.rows['aliases'][0]['canonical_id']=511;self.rejected()
    def test_duplicate_policy_change(self): self.policy['duplicate_name_resolution']['1']['canonical_vega_id']=511;self.rejected()
    def test_frozen_boundary_change(self): self.policy['frozen_vega_end']=512;self.rejected()
    def test_missing_candidate(self): self.moves.pop();self.rejected()
    def test_duplicate_candidate_id(self): self.moves.append(copy.deepcopy(self.moves[0]));self.rejected()
    def test_upstream_reclassification(self): self.rows['511']['cfru_symbol']='MOVE_POUND';self.rejected()
    def test_adapter_invention(self): self.rows['511']['effect_adapter']={};self.rejected()
    def test_origin_pointer_reclassification(self): self.rows['511']['effect_map']['mapping_kind']='EXTERNAL_ROM_POINTER';self.rejected()
    def test_candidate_boolean(self): self.moves[1]['effect_id']=False;self.rejected()
    def test_no_input_mutation(self):
        before=copy.deepcopy((self.rows,self.moves,self.policy));self.call();self.assertEqual(before,(self.rows,self.moves,self.policy))
    def test_source_proof_ranges_and_hashes(self):
        rows=audit.source_proof(Inputs(),'scripts/build_move_port.py',('build_move_model','_vega_battle','validate_move_model'))
        self.assertEqual(len(rows),3)
        self.assertTrue(all(r['start_line']<=r['end_line'] and len(r['unit_sha256'])==64 for r in rows))
    def test_missing_source_function(self):
        with self.assertRaises(ValueError): audit.source_proof(Inputs(),'scripts/build_move_port.py',('NotAFunction',))
    def test_snapshot_read_only(self):
        p=ROOT/snapshot.OUTPUT;before=(p.read_bytes(),p.stat().st_mtime_ns);snapshot.load(Inputs())
        self.assertEqual(before,(p.read_bytes(),p.stat().st_mtime_ns))
    def test_snapshot_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/snapshot.OUTPUT;p.parent.mkdir(parents=True);p.write_bytes((ROOT/snapshot.OUTPUT).read_bytes()+b' ')
            with self.assertRaises(ValueError): snapshot.load(Inputs(Path(tmp)))
    def test_wrong_report_hash(self):
        with self.assertRaises(ValueError): snapshot.compact(b'{}')

class WikiIntegrationTests(unittest.TestCase):
    def fixture(self):
        old='今回調べた保存先に実体なし。再コンパイルや近傍prologueからの命名はしていません。'
        names=('README.md','CODEX_INDEX.md','RUNTIME_LIMITATIONS.md','RUNTIME_Z_AUDIT.md','Z_MOVE_INDEX.md',
            'HIDDEN_PATCH_AUDIT.md','HIDDEN_ABILITY_INDEX.md','CREATION_MOVESET_AUDIT.md','EFFECT_ORIGIN_AUDIT.md',
            'moves/511.md')
        files={n:b'# fixture\n' for n in names}
        files['LINK_GRAPH_AUDIT.md']=('## 未保存link表\n'+old).encode()
        value={'summary':{},'symbols':{},'graphs':{},'scope_ja':'実行受入ではない',
            'capture_receipt':{},'move_511':{}}
        return files,{'saved_link_audit':value}
    def test_pages_and_historical_explanation(self):
        files,model=self.fixture();audit.append_pages(files,model)
        self.assertIn('SAVED_LINK_AUDIT.md',files)
        self.assertIn('MOVE_511_LINEAGE.md',files)
        self.assertIn('全body'.encode(),files['README.md'])
        self.assertIn('初回metadata監査時点'.encode(),files['LINK_GRAPH_AUDIT.md'])
        self.assertNotIn('今回調べた保存先に実体なし'.encode(),files['LINK_GRAPH_AUDIT.md'])
    def test_missing_historical_anchor_rejected(self):
        files,model=self.fixture();files['LINK_GRAPH_AUDIT.md']=b'changed'
        with self.assertRaises(ValueError): audit.append_pages(files,model)
    def test_final_guard_allows_only_named_snapshot(self):
        import pr16_wiki_checkpoint as checkpoint
        self.assertIn(snapshot.OUTPUT,checkpoint.ALLOWED)
        self.assertNotIn('content/modernization/arbitrary.json',checkpoint.ALLOWED)

if __name__=='__main__': unittest.main()
