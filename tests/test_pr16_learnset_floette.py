"""Issue19 Eternal採用差分と非学習owner gateの新規範囲だけを検証する。"""
from __future__ import annotations
from collections import Counter
import copy
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from tools import pr16_learnset_floette as f
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_species_binding as b

ROOT = Path(__file__).resolve().parents[1]
CATALOG = s.BASE + 'pr16_learnset_payload_evidence/catalogs.json'
BINDINGS = s.BASE + 'pr16_learnset_payload_evidence/species-bindings.jsonl'


def source_dir():
    recorded = ROOT / f.SOURCE_EVIDENCE
    return recorded if recorded.exists() else ROOT / '.local/pr16-learnset-floette/source'


def fixture():
    source = source_dir()
    return {'reference': s.read_json(source/'reference.json'), 'target': s.read_json(source/'target.json'),
        'crosswalk': {int(k): v for k, v in s.read_json(source/'crosswalk.json').items()},
        'gift': s.read_json(ROOT/'config/modernization_floette_gift.json'),
        'decision': s.read_json(ROOT/f.DECISION),
        'moves': s.manifest(ROOT/'manifests/move_ids.csv', 'move_key'),
        'catalogs': s.read_json(ROOT/CATALOG)}


def rebind_reference(args):
    raw = s.encode(args['reference'])
    args['decision']['source_files']['reference.json'] = {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def synthetic_parent():
    """旧payloadを再生成しない。全owner query用の合成index fixture。"""
    bindings = {r['species_id']: r for r in s.rows(ROOT/BINDINGS)}
    result = []
    for family in b.CONSUMERS:
        for sid in range(1671):
            key = bindings[sid]['species_key'] if sid in bindings else 'SPECIES_KEY_TEST_'+str(sid)
            row = {'species_id':sid, 'species_key':key, 'consumer':family,
                   'status':'PAYLOAD_PREPARED_NOT_INSTALLED', 'routes':0,
                   'payload':None if family in ('form_change','pre_evolution_carry') else
                   {'file':family+'.bin', 'offset':0, 'size':0}}
            if sid == f.SID:
                row.update(status='BLOCKED_SOURCE_ADOPTION', policy='GIFT_LEARNSET_ADOPTION_REQUIRED', payload=None)
            elif sid in bindings and bindings[sid]['policy'] in b.NONPERMANENT:
                row.update(status='IDENTITY_ONLY_NO_REPLACEMENT', payload=None,
                    identity={'species_id':sid,'species_key':key,'policy':bindings[sid]['policy'],
                        'preserve_identity':True,'preserve_current_moves':True,'automatic_fallback':False})
            result.append(row)
    return result


class FloetteTests(unittest.TestCase):
    def setUp(self):
        self.args = fixture()

    def rows(self):
        return f.adopt(**self.args)

    def delta(self):
        return f.prepare_delta(self.rows(), self.args['catalogs'], self.args['moves'])

    def rejected(self):
        with self.assertRaises(ValueError): self.rows()

    def test_exact_37_routes(self):
        rows = self.rows()
        self.assertEqual(Counter(r['consumer'] for r in rows), f.EXPECTED)
        self.assertEqual(len({r['source_id'] for r in rows}), 37)

    def test_input_objects_unchanged(self):
        before = copy.deepcopy(self.args)
        self.rows()
        self.assertEqual(self.args, before)

    def test_full_provenance_preserved(self):
        rows = self.rows()
        self.assertEqual([r['provenance']['source_route'] for r in rows], self.args['reference']['routes'])
        self.assertTrue(all(r['provenance']['original_p01_apply'] is False for r in rows))

    def test_requires_explicit_decision(self):
        self.args['decision']['decision'] = 'AUTO_FALLBACK'; self.rejected()

    def test_normal_floette_is_not_donor(self):
        self.args['target']['canonical_id'] = 959; self.rejected()

    def test_wrong_form_key(self):
        self.args['target']['form_key'] = 'FORM_KEY_FLOETTE'; self.rejected()

    def test_wrong_reference_id(self):
        self.args['reference']['reference_id'] = 'legendsza:0670.00'; self.rejected()

    def test_reference_hash_tamper(self):
        self.args['reference']['routes'][0]['master_level'] = 11; self.rejected()

    def test_original_p01_not_rewritten(self):
        self.args['target']['normalized']['apply'] = True; self.rejected()

    def test_gift_flag_not_changed(self):
        self.args['gift']['gift']['claim_flag'] = '0x14CE'; self.rejected()

    def test_gift_location_not_changed(self):
        self.args['gift']['map']['x'] = 26; self.rejected()

    def test_saved_four_moves_protected(self):
        self.args['decision']['preserve_saved_four_moves'] = False; self.rejected()

    def test_owner_overlay_forbidden(self):
        self.args['decision']['owner_approved_overlay'] = [{'move_id':1}]; self.rejected()

    def test_runtime_acceptance_not_promoted(self):
        self.args['decision']['runtime_applied'] = True; self.rejected()

    def test_side_change_not_adopted(self):
        self.args['decision']['side_change_adopted'] = True; self.rejected()

    def test_level_zero_rejected_after_hash_check(self):
        self.args['reference']['routes'][0]['target_learning_level'] = 0
        rebind_reference(self.args); self.rejected()

    def test_boolean_level_rejected(self):
        self.args['reference']['routes'][0]['target_learning_level'] = True
        rebind_reference(self.args); self.rejected()

    def test_duplicate_route_rejected(self):
        self.args['reference']['routes'][1] = copy.deepcopy(self.args['reference']['routes'][0])
        rebind_reference(self.args); self.rejected()

    def test_catalog_duplicate_slot_rejected(self):
        self.args['catalogs']['machine']['slots'][1]['bit_index'] = 0; self.rejected()

    def test_catalog_one_based_confusion_rejected(self):
        self.args['catalogs']['machine']['slots'][0]['wiki_ordinal'] = 0; self.rejected()

    def test_tutor_out_of_range_rejected(self):
        self.args['catalogs']['tutor']['slots'][-1].update(bit_index=64, wiki_ordinal=65); self.rejected()

    def test_sparse_tutor_catalog_not_filled(self):
        maps = f.catalog_bits(self.args['catalogs'], self.args['moves'])
        self.assertEqual(sum(map(len, maps['tutor'].values())), 54)
        self.assertNotIn(2, [bit for bits in maps['tutor'].values() for bit in bits])

    def test_level_payload_exact_order(self):
        files, _ = self.delta(); raw = files['floette.level_up.bin']
        expected = [(r['project_move_id'],r['target_learning_level'])
                    for r in self.args['reference']['routes'] if r['method']=='level_up']
        self.assertEqual(len(raw),42); self.assertEqual(raw[-3:],b'\0\0\xff')
        self.assertEqual([struct.unpack_from('<HB',raw,n) for n in range(0,len(raw)-3,3)],expected)

    def test_evolution_not_level_zero_or_gift_initial(self):
        files, _ = self.delta()
        self.assertEqual(files['floette.evolution.bin'],struct.pack('<H',546))
        self.assertNotIn(546,[r['move_id'] for r in self.rows() if r['consumer']=='level_up'])
        self.assertTrue(all(r['rewrite_existing_moves'] is False for r in self.rows()))

    def test_egg_shared_reminder_not_invented(self):
        files, index = self.delta()
        self.assertEqual(files['floette.egg.bin'],struct.pack('<HH',21029,65535))
        self.assertEqual(files['floette.shared_egg.bin'],b'')
        self.assertEqual(files['floette.reminder.bin'],b'')
        self.assertTrue(all(r['payload'] is None for r in index if r['consumer'] in ('form_change','pre_evolution_carry')))

    def test_machine_bits_and_missing_archive_independent(self):
        files, _ = self.delta()
        mids = [r['project_move_id'] for r in self.args['reference']['routes'] if r['method']=='tm']
        slots = self.args['catalogs']['machine']['slots']
        expected = sum(1<<r['bit_index'] for r in slots if r['move_id'] in mids)
        self.assertEqual(int.from_bytes(files['floette.machine.bin'],'little'),expected)
        missing = [mid for mid in mids if mid not in {r['move_id'] for r in slots}]
        self.assertEqual(len(missing),12)
        self.assertEqual(files['floette.machine_archive.bin'],struct.pack('<'+'H'*len(missing),*missing))
        self.assertEqual(files['floette.tutor.bin'],bytes(16))

    def test_only_nine_index_entries_change(self):
        parent = synthetic_parent(); original=copy.deepcopy(parent)
        combined = f.compose_index(parent,self.delta()[1])
        self.assertEqual(len(combined),15039)
        self.assertEqual([(a['species_id'],a['consumer']) for a,c in zip(parent,combined) if a!=c],
                         [(1029,family) for family in b.CONSUMERS])
        self.assertEqual(parent,original)

    def test_already_adopted_parent_rejected(self):
        delta = self.delta()[1]; parent=f.compose_index(synthetic_parent(),delta)
        with self.assertRaises(ValueError): f.compose_index(parent,delta)

    def test_duplicate_index_rejected(self):
        parent=synthetic_parent(); parent[-1]=copy.deepcopy(parent[-2])
        with self.assertRaises(ValueError): f.compose_index(parent,self.delta()[1])

    def test_other_species_delta_rejected(self):
        delta=self.delta()[1]; delta[0]['species_id']=959
        with self.assertRaises(ValueError): f.compose_index(synthetic_parent(),delta)

    def test_owner_conditions_not_flattened(self):
        for row in self.delta()[1]:
            result=f.resolve_owner(row,1029,row['consumer'])
            expected='CONDITIONAL_CONSUMER_NOT_CONNECTED' if row['consumer'] in ('form_change','pre_evolution_carry') else 'EXPLICIT_OWNER_PAYLOAD_NOT_INSTALLED'
            self.assertEqual(result.action,expected)
            self.assertEqual(result.species_id,1029)
            self.assertTrue(result.preserve_existing_moves)

    def test_all_nonlearning_owner_policies_retained(self):
        combined=f.compose_index(synthetic_parent(),self.delta()[1])
        policies=f.owner_policies(combined)
        self.assertEqual(len(policies),1671)
        self.assertEqual(Counter(policies),{1:1483,2:21,3:7,4:3,5:6,6:102,7:49})
        self.assertEqual([policies[sid] for sid in (649,1029,1670)],[1,1,1])

    def test_invalid_owner_queries(self):
        row=self.delta()[1][0]
        for sid,consumer in ((True,'egg'),(-1,'egg'),(1671,'egg'),(1029,'unknown')):
            with self.subTest(sid=sid,consumer=consumer), self.assertRaises(ValueError):
                f.resolve_owner(row,sid,consumer)

    def test_blocked_owner_does_not_fallback(self):
        row=next(r for r in synthetic_parent() if r['species_id']==1029)
        with self.assertRaises(ValueError): f.resolve_owner(row,1029,row['consumer'])

    def test_nonlearning_cannot_return_empty_payload(self):
        row=copy.deepcopy(next(r for r in synthetic_parent() if r['status']=='IDENTITY_ONLY_NO_REPLACEMENT'))
        row['payload']={'file':'empty.bin','offset':0,'size':0}
        with self.assertRaises(ValueError): f.resolve_owner(row,row['species_id'],row['consumer'])

    def test_owner_payload_result_is_detached(self):
        row=next(r for r in self.delta()[1] if r['consumer']=='level_up')
        before=copy.deepcopy(row)
        result=f.resolve_owner(row,1029,'level_up');result.payload['size']=0
        self.assertEqual(row,before)


class OwnerCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        library=Path(cls.temp.name)/'owner.so'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
            str(ROOT/'src/modernization/pr16_learnset_owner.c'),'-o',str(library)],check=True)
        cls.library=ctypes.CDLL(str(library));cls.call=cls.library.Pr16ResolveLearnsetOwner
        cls.call.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_uint16,ctypes.c_uint16,ctypes.c_uint8,ctypes.POINTER(ctypes.c_uint16)]
        cls.call.restype=ctypes.c_uint8
        args=fixture();delta=f.prepare_delta(f.adopt(**args),args['catalogs'],args['moves'])[1]
        cls.index=f.compose_index(synthetic_parent(),delta)
        cls.raw=f.owner_policies(cls.index)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def invoke(self,sid,consumer,*,raw=None,count=1671):
        vector=(ctypes.c_uint8*1671).from_buffer_copy(self.raw if raw is None else raw)
        owner=ctypes.c_uint16(4242)
        result=self.call(vector,count,sid,consumer,ctypes.byref(owner))
        self.assertEqual(bytes(vector),self.raw if raw is None else raw)
        return result,owner.value

    def test_all_1671_by_nine_c_queries(self):
        for sid,policy in enumerate(self.raw):
            for consumer in range(9):
                expected=3 if policy>=5 else 2 if policy>=2 else 4 if consumer in (2,5) else 1
                self.assertEqual(self.invoke(sid,consumer),(expected,sid))

    def test_c_boundary_invalid_species(self):
        for sid in (1671,65535): self.assertEqual(self.invoke(sid,0),(0,65535))

    def test_c_invalid_consumer(self):
        for value in (9,255): self.assertEqual(self.invoke(1029,value),(0,65535))

    def test_c_short_policy_table(self):
        self.assertEqual(self.invoke(1029,0,count=1670),(0,65535))

    def test_c_invalid_policy(self):
        for value in (0,8,255):
            raw=bytearray(self.raw);raw[1029]=value
            self.assertEqual(self.invoke(1029,0,raw=bytes(raw)),(0,65535))

    def test_c_null_inputs(self):
        owner=ctypes.c_uint16(4242)
        self.assertEqual(self.call(None,1671,1029,0,ctypes.byref(owner)),0)
        self.assertEqual(owner.value,65535)
        self.assertEqual(self.call(None,1671,1029,0,None),0)

    def test_c_distinct_owner_no_donor_alias(self):
        for sid in (649,1029,1670): self.assertEqual(self.invoke(sid,3),(1,sid))

    def test_c_does_not_silently_flatten_condition(self):
        for consumer in (2,5):self.assertEqual(self.invoke(1029,consumer),(4,1029))


if __name__ == '__main__': unittest.main()
