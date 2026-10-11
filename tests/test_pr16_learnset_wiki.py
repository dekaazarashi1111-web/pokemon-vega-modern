"""新Wiki境界のみ。旧ROM/native/PLA1/PLC2試験は再実行しない。"""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from scripts import pr16_learnset_wiki as w


def row(**updates):
    r={'species_id':1,'species_key':'SPECIES_KEY_A','consumer':'level_up','move_id':33,
       'move_key':'MOVE_KEY_TACKLE','layer':'official_baseline','source_id':'official:r1',
       'source_order':0,'conditional_egg':False,'disposition':'BASELINE_SELECTED',
       'provenance':{'source_route':{'level':5,'source_game':'fixed','source_file':'raw.txt',
                     'source_line':3,'source_condition_ja':'条件を保持する','target_learning_level':5}}}
    r.update(updates);return r


class WikiTests(unittest.TestCase):
    def test_carry_is_not_direct_grant(self):
        self.assertEqual(w.meaning(row(consumer='form_change')),'CARRY_REFERENCE_NOT_DIRECT_GRANT')
        self.assertEqual(w.meaning(row(consumer='pre_evolution_carry')),'CARRY_REFERENCE_NOT_DIRECT_GRANT')
    def test_conditional_egg_is_not_flat(self):
        self.assertEqual(w.meaning(row(consumer='egg',conditional_egg=True)),'CONDITIONAL_BREEDING_NOT_FLAT_EGG')
    def test_direct_data_does_not_claim_supply(self):
        projected=w.project(row(),{})
        self.assertFalse(projected['physical_supply_verified'])
        self.assertEqual(projected['meaning'],'BASELINE_DATA_NOT_PHYSICAL_SUPPLY_ACCEPTANCE')
    def test_condition_dictionary_preserves_context(self):
        conditions={};p=w.project(row(),conditions)
        self.assertEqual(conditions[p['condition_id']]['source_condition_ja'],'条件を保持する')
        self.assertEqual(p['source']['source_line'],3)
    def test_source_is_not_mutated(self):
        original=row();before=copy.deepcopy(original);w.project(original,{})
        self.assertEqual(original,before)
    def test_source_hash_binds_full_original(self):
        original=row();p=w.project(original,{})
        self.assertEqual(p['source_row_sha256'],w.identity(w.encode(original))['sha256'])
        original['provenance']['source_route']['level']=6
        self.assertNotEqual(p['source_row_sha256'],w.source_hash(original))
    def test_conditional_identity_not_shared_after_change(self):
        a=row();b=copy.deepcopy(a);b['provenance']['source_route']['source_condition_ja']='別条件'
        self.assertNotEqual(w.project(a,{})['condition_id'],w.project(b,{})['condition_id'])
    def test_duplicate_route_identity_rejected(self):
        with self.assertRaises(ValueError):w.unique([row(),row()],w.route_key)
    def test_diff_excludes_carry_and_history(self):
        old=[{'old_route':'build_learnable_preservation','move_id':33}, {'old_route':'machine_archive','move_id':44}]
        d=w.diff_membership(old,[row(consumer='pre_evolution_carry'),row(consumer='machine',move_id=44)],1)
        self.assertEqual(d['common'],[{'consumer':'machine','move_id':44}]);self.assertEqual(d['new_only'],[])
        self.assertEqual(len(d['old_historical_or_conditional_rows']),1);self.assertFalse(d['stored_four_moves_deleted'])
    def test_diff_deduplicates_memberships_not_sources(self):
        d=w.diff_membership([], [row(),row()],1)
        self.assertEqual(d['new_direct_memberships'],1)
    def test_diff_conditional_egg_not_direct(self):
        d=w.diff_membership([], [row(consumer='egg',conditional_egg=True)],1)
        self.assertEqual(d['new_direct_memberships'],0)
    def test_word_decoder_rejects_side_change(self):
        with self.assertRaises(ValueError):w.words(struct.pack('<H',1063))
    def test_word_decoder_rejects_truncation(self):
        with self.assertRaises(ValueError):w.words(b'\x01')
    def test_word_decoder_retains_order(self):
        self.assertEqual(w.words(struct.pack('<3H',33,12,33)),[33,12,33])
    def test_span_rejects_traversal(self):
        with self.assertRaises(ValueError):w.span(Path('/unused'),{'file':'../bad','offset':0,'size':0})
    def test_span_rejects_outside(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'ok.bin').write_bytes(b'ab')
            with self.assertRaises(ValueError):w.span(p,{'file':'ok.bin','offset':1,'size':2})
    def test_check_is_readonly(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wiki';files={'README.md':b'wiki\n','data/a.json':b'{}\n'};w.write_new(p,files)
            before={f:(f.read_bytes(),f.stat().st_mtime_ns) for f in p.rglob('*') if f.is_file()}
            self.assertEqual(w.check_tree(p,files),w.tree_hash(files))
            self.assertEqual(before,{f:(f.read_bytes(),f.stat().st_mtime_ns) for f in before})
    def test_check_rejects_extra_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wiki';w.write_new(p,{'a.md':b'a'});(p/'extra').write_text('extra')
            with self.assertRaises(ValueError):w.check_tree(p,{'a.md':b'a'})
    def test_check_rejects_changed_byte(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wiki';w.write_new(p,{'a.md':b'a'})
            with self.assertRaises(ValueError):w.check_tree(p,{'a.md':b'b'})
    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):w.write_new(Path(d),{})
    def test_check_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wiki';w.write_new(p,{'a.md':b'a'});(p/'alias').symlink_to('a.md')
            with self.assertRaises(ValueError):w.check_tree(p,{'a.md':b'a'})
    def test_link_checker_rejects_external(self):
        with self.assertRaises(ValueError):w.check_links({'a.md':b'[x](https://example.com)'})
    def test_link_checker_rejects_missing_anchor(self):
        with self.assertRaises(ValueError):w.check_links({'a.md':b'[x](b.md#missing)','b.md':b'no'})
    def test_link_checker_accepts_bound_anchor(self):
        self.assertEqual(w.check_links({'a.md':b'[x](b.md#yes)','b.md':b'<a id="yes"></a>'}),1)
    def test_escape_untrusted_markdown(self):
        self.assertNotIn('[x]',w.escape('[x](bad)|`z`\n'))
        self.assertNotIn('|',w.escape('|'));self.assertIn('<br>',w.escape('\n'))
    def test_tree_is_order_independent(self):
        self.assertEqual(w.tree_hash({'a':b'a','b':b'b'}),w.tree_hash({'b':b'b','a':b'a'}))
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):w.encode({'bad':float('nan')})
    def test_projection_audit_rejects_implicit_nonlearning(self):
        with self.assertRaises(ValueError):w.audit_projection([row()],{1:{'learning_owner':False}})


if __name__=='__main__':unittest.main()
