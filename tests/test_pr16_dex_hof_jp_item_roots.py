"""ROM不要の意味operand疎fixtureで二つの新rootと拒否条件を検査する。"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_jp_item_roots as v


class SourceSparse:
    def __init__(self):
        self.cells={}
        for mod,rows in v.ALL_BLOCKS.values():
            for ins in rows:self.put(ins.address,mod.encoded(ins))
        for a,value in v.ALL_WORDS.items():self.put(a,value.to_bytes(4,'little'))

    def put(self,address,payload):
        for j,byte in enumerate(payload):
            a=address+j
            if a in self.cells and self.cells[a]!=byte:raise ValueError('意味fixtureの重複不一致')
            self.cells[a]=byte

    def __len__(self):return v.CANDIDATE['size']

    def __getitem__(self,part):
        if not isinstance(part,slice) or part.step not in(None,1):raise ValueError('有限連続sliceのみ')
        addresses=range(0x08000000+part.start,0x08000000+part.stop)
        if any(a not in self.cells for a in addresses):raise ValueError('未束縛byteを0で埋めない')
        return bytes(self.cells[a] for a in addresses)


class ItemRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SourceSparse()
        cls.results={lane:v.compose_selected(cls.raw,lane,True) for lane in ('exchange','mailbox')}

    def test_exchange_real_registration_and_dispatch(self):
        p,m=self.results['exchange']
        self.assertEqual(p['events'],[dict(role='same_task_input_registration',address=0x081240FA,
            task_id=0,registered_thumb=0x0812410D,task_cell=0x030050D0)])
        self.assertEqual([(f['entry'],f['stop']) for f in p['frames']],
                         [(0x081240D8,0xFFFFFFF0),(0x08076D10,0x08120D48)])
        self.assertEqual((m.pc,m.reg[:3]),(0x08120D48,[2,1,1]))
        self.assertEqual(m.read(v.TASKS,4),0x0812410D)

    def test_exchange_seven_exact_opaque_sites(self):
        p,_=self.results['exchange']
        self.assertEqual([(r['site'],r['target']) for r in p['conditional_calls']],
          [(0x081240DE,0x08120B60),(0x081240EA,0x081227D8),(0x08124112,0x08110BF8),
           (0x08124138,0x08099BE0),(0x08124142,0x08099A8C),(0x0812418A,0x08097AE8),
           (0x081241D8,0x08120DB8)])
        self.assertEqual(p['instruction_steps'],83)
        returns={r['site']:r['return_value'] for r in p['conditional_calls']}
        self.assertEqual({a:returns[a] for a in(0x081240DE,0x08124112,0x08124142,0x0812418A)},
                         {0x081240DE:0,0x08124112:0,0x08124142:1,0x0812418A:0})

    def test_mailbox_actual_constructor_and_table_cell(self):
        p,m=self.results['mailbox']
        self.assertEqual(p['root']['constructor_register_arguments'],[0,0,7,0])
        self.assertEqual(p['root']['constructor_stack_arguments'],[6,0x08120319,0x080ED451])
        self.assertEqual(p['events'],[
          dict(role='mailbox_constructor_arguments',address=0x08127D28,action=7),
          dict(role='admitted_same_task',address=0x0811F5C4,task_id=0),
          dict(role='mailbox_action_cell',address=0x081203E6,cell=0x08120404,target=0x08120496)])
        self.assertEqual((m.pc,m.reg[0]),(0x08127D3C,0))
        self.assertEqual(m.read(v.TASKS,4),0x08120319)
        self.assertEqual(p['instruction_steps'],3561)
        self.assertEqual(len(p['frames']),26)

    def test_mailbox_egg_checked_on_selected_mon(self):
        p,_=self.results['mailbox']
        rows=[r for r in p['conditional_calls'] if r['target']==0x0803F354]
        self.assertEqual([(r['site'],r['return_value']) for r in rows],[(0x0812055A,0)])
        self.assertFalse(rows[0]['effects_discharged'])

    def test_both_callback_bodies_are_unexecuted(self):
        for lane,(p,m) in self.results.items():
            with self.subTest(lane=lane):
                self.assertNotIn(m.pc,v.INS)
                self.assertFalse(p['callback_body_executed'])
                self.assertFalse(p['complete_text_reads_proven'])
                self.assertEqual(p['newly_classified'],0)
                self.assertEqual(m.read(v.PARTY+9,1),0)

    def test_old_positive_profiles_are_never_called(self):
        with patch.object(v.take,'compose_selected',side_effect=AssertionError('旧正profile禁止')):
            for lane in v.PROFILES:
                p=v.compose_selected(self.raw,lane)
                self.assertFalse(p['old_positive_profile_reexecuted'])

    def test_claims_are_conditional(self):
        for p,m in self.results.values():
            self.assertTrue(p['conditional_finite_type_only'])
            self.assertTrue(p['synthetic_contract_execution'])
            for key in ('actual_runtime_execution_observed','full_story_reachability_claimed',
                        'universal_allocation_epoch_proven','all_opaque_effects_proven',
                        'irq_noninterference_proven','indirect_reference_completeness_claimed','donor_eligible'):
                self.assertIs(p[key],False)

    def test_every_boundary_has_explicit_abi_and_ram_contract(self):
        for p,m in self.results.values():
            for r in p['conditional_calls']:
                self.assertTrue(r['normal_abi_return_required'])
                self.assertFalse(r['effects_discharged'])
                self.assertTrue(r['required_fields'])
                self.assertEqual(r['discarded_registers'],['r0','r1','r2','r3','r12','lr'])
                self.assertTrue(r['flags_discarded'])
            self.assertIsInstance(m.reg[12],v.runtime.Unknown)
            self.assertTrue(p['nonlive_ram_erased_at_each_boundary'])
            self.assertLess(len(m.mem),100)

    def test_profile_is_strict_and_closed(self):
        for lane,profile in v.PROFILES.items():
            for key in profile:
                changed=copy.deepcopy(profile)
                changed[key]=True if type(profile[key])is int else 1
                with self.subTest(lane=lane,key=key),self.assertRaises(ValueError):
                    v.selected_profile(lane,changed)
            changed=dict(profile,extra=0)
            with self.assertRaises(ValueError):v.selected_profile(lane,changed)
        for lane in ('take','Flash','',0,None):
            with self.subTest(lane=lane),self.assertRaises(ValueError):v.selected_profile(lane)

    def test_branch_counterexamples_fail_closed(self):
        for lane,key,value in [('exchange','text_active',1),('exchange','yes_input',1),
                ('exchange','yes_input',255),('exchange','bag_success',0),
                ('exchange','item_is_mail',1),('mailbox','egg',1),('mailbox','choose_mon_input',0)]:
            profile=copy.deepcopy(v.PROFILES[lane]);profile[key]=value
            with self.subTest(lane=lane,key=key,value=value),self.assertRaises(ValueError):
                v._compose(self.raw,lane,profile)

    def test_each_new_instruction_mutation_rejected(self):
        for rows in v.BLOCKS.values():
            for ins in rows:
                raw=copy.copy(self.raw);raw.cells=dict(self.raw.cells);raw.cells[ins.address]^=1
                with self.subTest(address=ins.address),self.assertRaises(ValueError):v.bind_semantics(raw)

    def test_every_common_instruction_mutation_rejected(self):
        for a in sorted(v.INS):
            raw=copy.copy(self.raw);raw.cells=dict(self.raw.cells);raw.cells[a]^=1
            with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)

    def test_every_literal_and_registration_mutation_rejected(self):
        for a in v.ALL_WORDS:
            raw=copy.copy(self.raw);raw.cells=dict(self.raw.cells);raw.cells[a]^=1
            with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)

    def test_mailbox_action_id_not_host_substituted(self):
        raw=copy.copy(self.raw);raw.cells=dict(self.raw.cells)
        replacement=v.party.Ins(0x08127D24,'imm',('mov',2,9))
        for j,b in enumerate(v.party.encoded(replacement)):raw.cells[replacement.address+j]=b
        with self.assertRaises(ValueError):v.compose_selected(raw,'mailbox')

    def test_required_ram_counterexample_at_every_unique_boundary(self):
        for lane,(p,m) in self.results.items():
            seen=set()
            for row in p['conditional_calls']:
                if row['site'] in seen:continue
                seen.add(row['site'])
                field=row['required_fields'][0]
                with self.subTest(lane=lane,site=row['site']),self.assertRaises(ValueError):
                    v.compose_selected(self.raw,lane,opaque_writes={row['site']:[(field['address'],1,0)]})

    def test_exchange_each_required_ram_range_rejected(self):
        p,_=self.results['exchange']
        for row in p['conditional_calls']:
            for field in row['required_fields']:
                with self.subTest(site=row['site'],address=field['address']),self.assertRaises(ValueError):
                    v.compose_selected(self.raw,'exchange',opaque_writes={row['site']:[(field['address'],1,0)]})

    def test_unrelated_ram_write_permitted_and_erased(self):
        for lane,(p,m) in self.results.items():
            site=p['conditional_calls'][-1]['site']
            result,state=v.compose_selected(self.raw,lane,True,opaque_writes={site:[(0x0203E000,4,7)]})
            self.assertEqual(result['events'],p['events'])
            self.assertNotIn(0x0203E000,state.mem)

    def test_same_task_epoch_is_required(self):
        for lane,(p,m) in self.results.items():
            site=next(r['site'] for r in p['conditional_calls'] if r['same_selected_task_required'])
            with self.subTest(lane=lane),self.assertRaises(ValueError):
                v.compose_selected(self.raw,lane,epoch_events={site:dict(task_invalidated=True)})

    def test_mailbox_object_epoch_required(self):
        p,_=self.results['mailbox']
        site=next(r['site'] for r in p['conditional_calls'] if r['object_epoch_required'])
        for event in ({'heap_reinitialized':True},{'freed':[v.runtime.ROOT+v.runtime.HEADER]}):
            with self.subTest(event=event),self.assertRaises(ValueError):
                v.compose_selected(self.raw,'mailbox',epoch_events={site:event})

    def test_unrelated_epoch_not_universal_freeze(self):
        for lane in v.PROFILES:
            site=self.results[lane][0]['conditional_calls'][-1]['site']
            self.assertEqual(v.compose_selected(self.raw,lane,epoch_events={site:{'freed':[0x0203E000]}})['lane'],lane)

    def test_enormous_write_extent_rejected_before_shift(self):
        for n in (4097,1<<32,1<<60):
            with self.subTest(n=n),self.assertRaises(ValueError):
                v.compose_selected(self.raw,'exchange',opaque_writes={0x081240DE:[(0,n,0)]})

    def test_constructor_object_initial_zero_bytes_are_explicit_conditions(self):
        p,_=self.results['mailbox']
        pointer=v.runtime.ROOT+v.runtime.HEADER
        self.assertEqual(p['allocation_result_memory_conditions'],
          [dict(address=pointer+j,size=1,value=0) for j in (8,10,11,12,13,14)])
        alloc=next(r for r in p['conditional_calls'] if r['site']==0x0811F280)
        self.assertEqual(alloc['conditional_outputs'],p['allocation_result_memory_conditions'])
        self.assertFalse(alloc['effects_discharged'])
        self.assertEqual(self.results['exchange'][0]['allocation_result_memory_conditions'],[])

    def test_initial_ram_values_and_unspecified_bytes_are_distinguished(self):
        for lane,(p,m) in self.results.items():
            fields={r['address']:r['value'] for r in p['required_initial_memory']}
            self.assertTrue(fields)
            if lane=='exchange':
                self.assertEqual(fields[v.NEW_ITEM_CELL],2)
                self.assertEqual(fields[v.OLD_ITEM_CELL],1)
                self.assertEqual(fields[v.PARTY+9],0)
            else:
                self.assertEqual(fields[v.MAIN],0)
                self.assertEqual(fields[0x020379F3],0)
                self.assertEqual(fields[0x020379F4],'unspecified')
                self.assertEqual(fields[0x03003E90],'unspecified')

    def test_unused_boundary_inputs_are_not_silently_ignored(self):
        for lane in v.PROFILES:
            for kw in ({'opaque_writes':{0x08120AD0:[]}}, {'epoch_events':{0x08120AD0:{}}}):
                with self.subTest(lane=lane,kw=kw),self.assertRaises(ValueError):v.compose_selected(self.raw,lane,**kw)

    def test_boundary_input_types_fail_closed(self):
        cases=[{'opaque_writes':[]},{'epoch_events':[]},
          {'opaque_writes':{True:[]}},{'opaque_writes':{0x081240DE:[(0,0,0)]}},
          {'opaque_writes':{0x081240DE:[(0,1,True)]}},
          {'epoch_events':{0x081240DE:{'all_safe':True}}},
          {'epoch_events':{0x081240DE:{'task_invalidated':1}}},
          {'epoch_events':{0x081240DE:{'freed':[True]}}}]
        for kw in cases:
            with self.subTest(kw=kw),self.assertRaises(ValueError):v.compose_selected(self.raw,**kw)

    def test_no_raw_payload_or_private_path_in_proof(self):
        def visit(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&{'raw','rawhex','bytes','private_path','member_path'})
                for child in value.values():visit(child)
            elif isinstance(value,list):
                for child in value:visit(child)
        for p,m in self.results.values():visit(p)

    def test_source_manifest_defensive_copy_and_fixed_whole_identities(self):
        manifest=v.source_manifest()
        self.assertEqual(manifest,v.take.SOURCE_IDS)
        manifest['pret-party_menu.c']['sha256']='0'*64
        self.assertNotEqual(manifest,v.source_manifest())
        with self.assertRaises(ValueError):v.sources_bind({})

    def test_source_hash_gate_rejects_altered_bytes(self):
        sources={key:b'changed source' for key in v.SOURCE_IDS}
        with self.assertRaises(ValueError):v.sources_bind(sources)

    def test_all_windows_finite_and_bound(self):
        for a,n in v.WINDOWS.values():self.assertEqual(len(v.chunk(self.raw,a,n)),n)
        with self.assertRaises(ValueError):v.chunk(self.raw,0x08000000,2)

    def test_public_function_flag_is_strict(self):
        for flag in (1,0,None,'yes'):
            with self.subTest(flag=flag),self.assertRaises(ValueError):v.compose_selected(self.raw,return_machine=flag)

    def test_profiles_not_mutated(self):
        before=copy.deepcopy(v.PROFILES)
        for lane in v.PROFILES:
            profile=v.selected_profile(lane);profile['task_id']=3
            self.assertEqual(self.results[lane][0]['profile'],before[lane])
        self.assertEqual(v.PROFILES,before)


if __name__=='__main__':unittest.main()
