"""後継consumer分割の境界試験。受入済み原本採取/旧回帰を実行しない。"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import pr16_learnset_successor as s

MOVES = {10: {'move_key': 'MOVE_KEY_SCRATCH'}, 45: {'move_key': 'MOVE_KEY_GROWL'}}


def official(method='level_up', kind='direct', mid=10, key='MOVE_KEY_SCRATCH'):
    route = {'method': method, 'route_kind': kind, 'project_move_id': mid,
             'route_id': 'a' * 24, 'level': 5, 'target_learning_level': 5,
             'source_condition_ja': '保持する条件', 'machine_item': 'TM99',
             'acquisition_condition_ja': '保持する手順', 'form_change_condition_ja': '保持する姿条件'}
    if kind == 'pre_evolution':
        route['target_learning_level'] = None
    return {'target_species_id': 1, 'target_species_key': 'SPECIES_KEY_TEST', 'target_form_key': 'FORM_A',
            'source_route': route, 'consumer': s.consumer(route), 'layer': 'official_baseline',
            'runtime_move_ready': mid != 1063, 'move_key': key, 'reference_id': 'fixture:01',
            'runtime_supply': {'runtime_slot_zero_based': 98, 'source_machine_item': 'TM99'}}


def legacy(*routes):
    return {'species_id': 1, 'species_key': 'SPECIES_KEY_TEST', 'routes': list(routes)}


def oldrow(route='level_up', mid=10, level=5, slot=2):
    return {'route': route, 'move_id': mid, 'move_key': MOVES[mid]['move_key'], 'level': level, 'slot': slot}


class ProjectionTests(unittest.TestCase):
    def test_all_nine_consumers(self):
        routes = [('level_up', 'direct'), ('evolution', 'direct'), ('reminder', 'direct'),
                  ('tm', 'direct'), ('tutor', 'direct'), ('egg', 'direct'),
                  ('level_up', 'pre_evolution'), ('shared_egg', 'shared_egg'), ('form_move', 'direct')]
        self.assertEqual({s.consumer(official(m, k)['source_route']) for m, k in routes}, set(s.CONSUMERS))

    def test_projection_is_lossless_and_does_not_mutate(self):
        row = official(); before = copy.deepcopy(row)
        p = s.official_row(row, 9, MOVES, {})
        self.assertEqual(p['provenance'], before)
        self.assertEqual(row, before)
        self.assertEqual(p['source_order'], 9)
        self.assertEqual(p['form_key'], 'FORM_A')

    def test_side_change_excluded_in_every_legal_route_kind(self):
        for method, kind in [('level_up','direct'), ('tm','direct'), ('egg','direct'),
                             ('tutor','direct'), ('reminder','direct'), ('egg','pre_evolution'),
                             ('shared_egg','shared_egg')]:
            with self.subTest(method=method, kind=kind):
                row = official(method, kind, 1063, 'MOVE_KEY_ALLYSWITCH')
                p = s.official_row(row, 0, MOVES, {})
                self.assertEqual(p['disposition'], s.DECLINED)
                self.assertEqual(p['provenance'], row)
                self.assertEqual(p['move_id'], 1063)

    def test_level_order_gap_needs_no_placeholder(self):
        rows = [official(), official(mid=1063, key='MOVE_KEY_ALLYSWITCH'), official(mid=45,key='MOVE_KEY_GROWL')]
        projected = [s.official_row(r, i, MOVES, {}) for i, r in enumerate(rows)]
        active = [r for r in projected if r['disposition'] != s.DECLINED]
        self.assertEqual([r['source_order'] for r in active], [0, 2])
        self.assertEqual([r['move_id'] for r in active], [10, 45])

    def test_unknown_move_fails(self):
        with self.assertRaises(ValueError): s.official_row(official(mid=9999), 0, MOVES, {})

    def test_move_key_mismatch_fails(self):
        with self.assertRaises(ValueError): s.official_row(official(key='MOVE_KEY_GROWL'), 0, MOVES, {})

    def test_side_change_cannot_be_declared_implemented(self):
        moves = dict(MOVES, **{})
        moves[1063] = {'move_key': 'MOVE_KEY_ALLYSWITCH'}
        with self.assertRaises(ValueError):
            s.official_row(official(mid=1063,key='MOVE_KEY_ALLYSWITCH'),0,moves,{})

    def test_move_zero_is_not_playable(self):
        with self.assertRaises(ValueError): s.move_guard(0, 'MOVE_KEY_NONE', {0:{'move_key':'MOVE_KEY_NONE'}})

    def test_bool_move_id_is_not_integer(self):
        with self.assertRaises(ValueError): s.move_guard(True, 'X', {1:{'move_key':'X'}})

    def test_consumer_and_layer_mismatch(self):
        for key, value in [('consumer','egg'), ('layer','CURRENT_PRESERVED')]:
            row = official(); row[key] = value
            with self.assertRaises(ValueError): s.official_row(row,0,MOVES,{})

    def test_unknown_method_fails(self):
        with self.assertRaises(ValueError): s.consumer({'method':'future','route_kind':'direct'})

    def test_carry_cannot_be_target_level(self):
        row = official('level_up','pre_evolution');row['source_route']['target_learning_level']=5
        with self.assertRaises(ValueError): s.official_row(row,0,MOVES,{})

    def test_shared_egg_requires_explicit_condition(self):
        row = official('shared_egg','shared_egg');row['source_route']['acquisition_condition_ja']=''
        with self.assertRaises(ValueError): s.official_row(row,0,MOVES,{})

    def test_form_change_requires_explicit_condition(self):
        row = official('level_up','form_change');row['source_route']['form_change_condition_ja']=''
        with self.assertRaises(ValueError): s.official_row(row,0,MOVES,{})

    def test_special_breeding_not_flattened(self):
        p = s.official_row(official('special_breeding'),0,MOVES,{})
        self.assertTrue(p['conditional_egg'])
        self.assertIsNone(s.signature(p))

    def test_level_range_checked(self):
        for level in (0,101,None,True):
            row=official();row['source_route']['target_learning_level']=level
            with self.assertRaises(ValueError): s.official_row(row,0,MOVES,{})

    def test_source_machine_number_is_not_runtime_slot(self):
        p = s.official_row(official('tm'),0,MOVES,{('machine',10):[2,7]})
        self.assertEqual(p['runtime_binding']['candidate_slots_zero_based'],[2,7])
        self.assertEqual(p['provenance']['source_route']['machine_item'],'TM99')
        self.assertFalse(p['runtime_binding']['compatibility_granted'])

    def test_missing_supply_is_explicit(self):
        p = s.official_row(official('tr'),0,MOVES,{})
        self.assertEqual(p['runtime_binding']['status'],'ARCHIVE_ADAPTER_REQUIRED')
        self.assertFalse(p['runtime_binding']['physical_supply_verified'])

    def test_catalog_conflict_fails(self):
        old={1:legacy(oldrow('machine',10,slot=2)),2:legacy(oldrow('machine',45,slot=2))}
        with self.assertRaises(ValueError): s.candidate_catalog(old)

    def test_catalog_keeps_duplicate_move_slots(self):
        old={1:legacy(oldrow('machine',10,slot=2),oldrow('machine',10,slot=7))}
        self.assertEqual(s.candidate_catalog(old),{('machine',10):[2,7]})

    def test_vega_keeps_original_offsets_and_order(self):
        species={'species_id':1,'species_key':'SPECIES_KEY_TEST','source_decision':'fixture',
                 'source_kind':'original','dex_no':1,'vega_id':1}
        row={'move_id':10,'move_key':'MOVE_KEY_SCRATCH','order':7,'source_offset':200,'level':12}
        p=s.vega_row(species,'level_up',row,MOVES,{})
        self.assertEqual(p['provenance']['source_route'],row)
        self.assertEqual(p['source_id'],'vega:1:level_up:7')


class DifferenceTests(unittest.TestCase):
    def test_level_sequence_change_is_not_equal_membership(self):
        first=s.official_row(official(),0,MOVES,{})
        second=s.official_row(official(mid=45,key='MOVE_KEY_GROWL'),1,MOVES,{})
        diff=s.compare_species(legacy(oldrow(mid=45),oldrow()),[first,second],True)
        self.assertEqual(diff['common_direct_membership'],2)
        self.assertFalse(diff['level_up_sequence_equal'])

    def test_duplicate_multiplicity_is_preserved(self):
        p=s.official_row(official(),0,MOVES,{})
        diff=s.compare_species(legacy(oldrow(),oldrow()),[p],True)
        self.assertEqual(diff['common_direct_membership'],1)
        self.assertEqual(diff['old_direct_not_selected'],1)

    def test_unselected_species_is_not_automatically_erased(self):
        diff=s.compare_species(legacy(oldrow()),[],False)
        self.assertIsNone(diff['old_direct_not_selected'])
        self.assertIn('NO_AUTOMATIC_FALLBACK_OR_DELETION',diff['old_entries'][0]['disposition'])

    def test_preserved_history_is_not_a_direct_grant(self):
        diff=s.compare_species(legacy(oldrow('build_learnable_preservation')),[],True)
        self.assertIn('REQUIRES_ADAPTER_REVIEW',diff['old_entries'][0]['disposition'])
        self.assertEqual(diff['old_direct_not_selected'],0)

    def test_machine_archive_membership_not_supply_acceptance(self):
        p=s.official_row(official('tm'),0,MOVES,{})
        diff=s.compare_species(legacy(oldrow('machine_archive')),[p],True)
        self.assertEqual(diff['common_direct_membership'],1)
        self.assertIn('CONDITION_ORDER_UNPROVEN',diff['old_entries'][0]['disposition'])


class HatchTests(unittest.TestCase):
    def setUp(self):
        self.row={'classification':'PRE_EVOLUTION_EGG','species_id':27,'source_group_index':8,
                  'hatch_species_id':24,'move_id':10,'move_key':'MOVE_KEY_SCRATCH',
                  'adopt_as_receiver_direct_egg':False,'add_as_shared_egg':False,
                  'original_direct_egg_rows':[{'move_id':10,'order':0,'source_offset':200}]}
        self.families={(27,8):{'hatch_species_id':24,'direct_egg_rows':self.row['original_direct_egg_rows']}}

    def test_official_hatch_species_can_be_joined(self):
        p=s.hatch_link(self.row,self.families,{24:{10}},MOVES)
        self.assertTrue(p['hatch_selected_direct_egg_membership'])
        self.assertFalse(p['direct_grant'])
        self.assertFalse(p['shared_grant'])

    def test_cross_source_gap_does_not_invent_egg_grant(self):
        p=s.hatch_link(self.row,self.families,{24:{45}},MOVES)
        self.assertFalse(p['hatch_selected_direct_egg_membership'])
        self.assertIn('DIFFERENCE',p['cross_source_status'])
        self.assertEqual(p['provenance'],self.row)

    def test_wrong_hatch_source_fails(self):
        self.row['hatch_species_id']=25
        with self.assertRaises(ValueError):s.hatch_link(self.row,self.families,{},MOVES)

    def test_empty_original_evidence_fails(self):
        self.row['original_direct_egg_rows']=[]
        with self.assertRaises(ValueError):s.hatch_link(self.row,self.families,{},MOVES)

    def test_direct_and_shared_promotions_fail(self):
        for key in ('adopt_as_receiver_direct_egg','add_as_shared_egg'):
            row=copy.deepcopy(self.row);row[key]=True
            with self.assertRaises(ValueError):s.hatch_link(row,self.families,{},MOVES)


class FilesystemTests(unittest.TestCase):
    def test_sink_check_produces_same_bytes_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);disk=s.Sink(out);memory=s.Sink(None)
            for row in ({'a':'日本語'}, {'a':2}):
                disk.emit('test.jsonl',row);memory.emit('test.jsonl',row)
            self.assertEqual(disk.close(),memory.close())
            self.assertEqual(s.identity(out/'test.jsonl')['sha256'],hashlib.sha256((out/'test.jsonl').read_bytes()).hexdigest())

    def test_existing_generate_target_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'.local/result';out.mkdir(parents=True)
            with self.assertRaises(ValueError):s.output_path(root,out,create=True)

    def test_output_outside_local_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):s.output_path(Path(temp),Path(temp)/'content/result',create=True)

    def test_symlink_input_and_output_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'real').write_text('x');(root/'link').symlink_to(root/'real')
            with self.assertRaises(ValueError):s.identity(root/'link')
            (root/'.local').symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):s.output_path(root,root/'.local/result',create=True)

    def test_hash_drift_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'f';p.write_text('a');expected=s.identity(p);p.write_text('b')
            with self.assertRaises(ValueError):s.bound(p,expected)

    def test_check_does_not_repair_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'.local/result';out.mkdir(parents=True)
            (out/'x.jsonl').write_text('good\n');ident=s.identity(out/'x.jsonl')
            receipt={'files':{'x.jsonl':ident}}
            (out/'receipt.json').write_bytes(s.encode(receipt));(out/'x.jsonl').write_text('bad\n')
            before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir()}
            with mock.patch.object(s,'compile_tables',return_value=receipt):
                with self.assertRaises(ValueError):s.check(root,root,out)
            self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir()})

    def test_check_rejects_extra_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'.local/result';out.mkdir(parents=True)
            receipt={'files':{}};(out/'receipt.json').write_bytes(s.encode(receipt));(out/'extra').write_text('x')
            with mock.patch.object(s,'compile_tables',return_value=receipt):
                with self.assertRaises(ValueError):s.check(root,root,out)

    def test_manifest_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'m.csv';p.write_text('id,move_key\n1,A\n1,B\n')
            with self.assertRaises(ValueError):s.manifest(p,'move_key')


if __name__ == '__main__':
    unittest.main()
