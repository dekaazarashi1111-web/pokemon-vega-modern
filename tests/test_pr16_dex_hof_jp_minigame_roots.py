"""ROM不要の意味operand疎fixtureで新minigame rootの生成・別hook・拒否条件を検査。"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_jp_minigame_roots as v


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


class MinigameRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SourceSparse()
        cls.results={lane:v.compose_selected(cls.raw,lane,True) for lane in v.PROFILES}

    def test_constructor_actual_arguments_and_same_task(self):
        for lane,(p,m) in self.results.items():
            with self.subTest(lane=lane):
                self.assertEqual(p['root']['constructor_register_arguments'],[11,0,13,0])
                self.assertEqual(p['root']['constructor_stack_arguments'],[1,0x08120319,0x080561A1])
                self.assertEqual(p['events'][0],dict(role='minigame_constructor_arguments',address=0x081281D8,menu_type=11,action=13))
                self.assertEqual(p['events'][4],dict(role='admitted_same_task',address=0x0811F5C4,task_id=0))
                self.assertEqual(m.read(v.TASKS,4),0x08120319)
                self.assertEqual(m.read(v.PARTY+8,1)&15,11)
                self.assertEqual(m.read(v.PARTY+11,1),13)

    def test_state6_is_real_body_not_opaque_return(self):
        for p,m in self.results.values():
            self.assertTrue(p['state6_body_executed'])
            self.assertEqual(p['events'][1],dict(role='state6_real_producer_call',address=0x0811F4CE,target=0x081210D4))
            self.assertNotIn((0x0811F4CE,0x081210D4),v.EXTERNAL)
            self.assertNotIn(0x0811F4CE,[r['site'] for r in p['conditional_calls']])

    def test_bitflag_two_real_stores_and_no_initial_seed(self):
        expected=[dict(role='bitflag_initial_store',address=0x081210E8,target=v.BITFLAG,value=0),
                  dict(role='bitflag_accumulating_store',address=0x0812114E,target=v.BITFLAG,value=0,slot=0)]
        for p,m in self.results.values():
            self.assertEqual(p['events'][2:4],expected)
            self.assertFalse(p['bitflag_host_seeded'])
            self.assertEqual(p['bitflag_value'],0)
            self.assertFalse({v.BITFLAG,v.BITFLAG+1}&{r['address'] for r in p['required_initial_memory']})
            self.assertEqual(m.read(v.BITFLAG,2),0)

    def test_mode_count_egg_species_are_explicit_conditions(self):
        for p,m in self.results.values():
            fields={r['address']:r['value'] for r in p['required_initial_memory']}
            self.assertEqual((fields[v.MODE],fields[v.MODE+1],fields[v.PARTY_COUNT]),(1,0,1))
            rows=[(r['site'],r['return_value']) for r in p['conditional_calls'] if r['target']==0x0803F354]
            expected=[(0x081211A2,0),(0x081211AE,1)]
            if p['lane']=='entry':expected.append((0x0812055A,0))
            self.assertEqual(rows,expected)

    def test_entry_real_action13_cell_and_callback_arguments(self):
        p,m=self.results['entry']
        self.assertEqual(p['events'][-1],dict(role='minigame_action_cell',address=0x081203E6,cell=0x0812041C,target=0x08120524))
        self.assertEqual((m.pc,m.reg[:2]),(0x081211E4,[0,0]))
        self.assertEqual(p['callback_arguments'],[0,0])
        self.assertEqual(p['instruction_steps'],3617)
        self.assertEqual(p['boundary_count'],128)

    def test_cancel_uses_separate_hook_and_stock_resume(self):
        p,m=self.results['cancel']
        self.assertEqual(p['events'][-2:],[
            dict(role='separate_cancel_hook',address=0x09097AB4,task_id=0,slot_pointer=v.PARTY+9),
            dict(role='cancel_stock_resume',address=0x08120580,action=13)])
        self.assertEqual(v.ALL_WORDS[0x0812057C],0x09097AB5)
        self.assertEqual(v.ALL_WORDS[0x09097AD0],0x08120581)
        self.assertEqual((m.pc,m.reg[0]),(0x08121248,0))
        self.assertEqual(p['callback_arguments'],[0])
        self.assertEqual(p['instruction_steps'],3593)
        self.assertEqual(p['boundary_count'],128)

    def test_callback_bodies_and_text_are_not_executed(self):
        for lane,(p,m) in self.results.items():
            with self.subTest(lane=lane):
                self.assertNotIn(m.pc,v.INS)
                self.assertFalse(p['callback_body_executed'])
                self.assertFalse(p['complete_text_reads_proven'])
                self.assertFalse(p['current_acceptance_claimed'])
                self.assertEqual(p['newly_classified'],0)
                self.assertEqual(len(p['frames']),26)
                self.assertEqual((p['frames'][0]['entry'],p['frames'][0]['stop']),(0x081281C0,0xFFFFFFF0))
                self.assertEqual(p['frames'][-1]['stop'],v.ENDPOINTS[lane])

    def test_old_positive_profile_is_not_called(self):
        with patch.object(v.take,'compose_selected',side_effect=AssertionError('旧正profile禁止')):
            for lane in v.PROFILES:self.assertFalse(v.compose_selected(self.raw,lane)['old_positive_profile_reexecuted'])

    def test_each_instruction_mutation_rejected(self):
        for a in sorted(v.INS):
            raw=copy.copy(self.raw);raw.cells=dict(self.raw.cells);raw.cells[a]^=1
            with self.subTest(address=hex(a)),self.assertRaises(ValueError):v.bind_semantics(raw)

    def test_each_literal_and_action_cell_mutation_rejected(self):
        for a in v.ALL_WORDS:
            raw=copy.copy(self.raw);raw.cells=dict(self.raw.cells);raw.cells[a]^=1
            with self.subTest(address=hex(a)),self.assertRaises(ValueError):v.bind_semantics(raw)

    def test_constructor_menu_type_action_not_host_substituted(self):
        for address,reg,value in ((0x081281D0,0,0),(0x081281D4,2,7)):
            raw=copy.copy(self.raw);raw.cells=dict(self.raw.cells)
            replacement=v.party.Ins(address,'imm',('mov',reg,value))
            for j,b in enumerate(v.party.encoded(replacement)):raw.cells[address+j]=b
            with self.subTest(address=hex(address)),self.assertRaises(ValueError):v.compose_selected(raw)

    def test_strict_closed_profile(self):
        for lane,profile in v.PROFILES.items():
            for key in profile:
                changed=copy.deepcopy(profile);changed[key]=True if type(profile[key])is int else 1
                with self.subTest(lane=lane,key=key),self.assertRaises(ValueError):v.selected_profile(lane,changed)
            with self.assertRaises(ValueError):v.selected_profile(lane,dict(profile,extra=0))
        for lane in ('exchange','mailbox','take','Flash','',0,None):
            with self.subTest(lane=lane),self.assertRaises(ValueError):v.selected_profile(lane)

    def test_profile_rejects_scalar_container_and_key_subclasses(self):
        class IntAlias(int):pass
        class StrAlias(str):pass
        class DictAlias(dict):pass
        class ListAlias(list):pass
        for lane,profile in v.PROFILES.items():
            for changed in (DictAlias(profile),dict(profile,mode=IntAlias(1))):
                with self.subTest(lane=lane,changed=changed),self.assertRaises(ValueError):
                    v.selected_profile(lane,changed)
            changed=dict(profile);del changed['mode'];changed[StrAlias('mode')]=1
            with self.assertRaises(ValueError):v.selected_profile(lane,changed)
        self.assertFalse(v.exact({'a':[IntAlias(1)]},{'a':[1]}))
        self.assertFalse(v.exact({'a':ListAlias([1])},{'a':[1]}))
        self.assertFalse(v.exact({'a':(1,)},{'a':[1]}))
        self.assertFalse(v.exact({'a':True},{'a':1}))
        self.assertTrue(v.exact({'a':[1,True,None,'x']},{'a':[1,True,None,'x']}))

    def test_changed_state6_branch_conditions_fail_closed(self):
        for lane in v.PROFILES:
            for key,value in (('mode',0),('party_count',0),('party_count',2),('species',85)):
                p=copy.deepcopy(v.PROFILES[lane]);p[key]=value
                with self.subTest(lane=lane,key=key),self.assertRaises(ValueError):v._compose(self.raw,lane,p)

    def test_changed_input_and_entry_egg_fail_closed(self):
        for lane,key,value in (('entry','choose_mon_input',0),('entry','choose_mon_input',2),
                               ('cancel','choose_mon_input',1),('entry','egg',1)):
            p=copy.deepcopy(v.PROFILES[lane]);p[key]=value
            with self.subTest(lane=lane,key=key),self.assertRaises(ValueError):v._compose(self.raw,lane,p)

    def test_every_boundary_has_explicit_abi_and_minimal_ram_contract(self):
        for p,m in self.results.values():
            for row in p['conditional_calls']:
                self.assertTrue(row['normal_abi_return_required'])
                self.assertFalse(row['effects_discharged'])
                self.assertTrue(row['required_fields'])
                self.assertEqual(row['discarded_registers'],['r0','r1','r2','r3','r12','lr'])
                self.assertTrue(row['flags_discarded'])
            self.assertTrue(p['nonlive_ram_erased_at_each_boundary'])
            self.assertIsInstance(m.reg[12],v.runtime.Unknown)
            self.assertLess(len(m.mem),128)

    def test_bitflag_live_at_all_boundaries_after_generation(self):
        for p,m in self.results.values():
            after_generation=False
            for row in p['conditional_calls']:
                if row['site']==0x0811F4D4:after_generation=True
                if after_generation:
                    self.assertTrue(any(f['address']<=v.BITFLAG and v.BITFLAG+2<=f['address']+f['size'] for f in row['required_fields']))
            self.assertTrue(after_generation)

    def test_bitflag_overwrite_rejected_at_last_boundary(self):
        for lane,(p,m) in self.results.items():
            site=p['conditional_calls'][-1]['site']
            with self.subTest(lane=lane),self.assertRaises(ValueError):
                v.compose_selected(self.raw,lane,opaque_writes={site:[(v.BITFLAG,2,1)]})

    def test_required_ram_counterexample_at_every_unique_boundary(self):
        for lane,(p,m) in self.results.items():
            seen=set()
            for row in p['conditional_calls']:
                if row['site'] in seen:continue
                seen.add(row['site']);field=row['required_fields'][0]
                with self.subTest(lane=lane,site=hex(row['site'])),self.assertRaises(ValueError):
                    v.compose_selected(self.raw,lane,opaque_writes={row['site']:[(field['address'],1,0)]})

    def test_nonlive_write_is_erased(self):
        for lane,(p,m) in self.results.items():
            site=p['conditional_calls'][-1]['site']
            result,state=v.compose_selected(self.raw,lane,True,opaque_writes={site:[(0x0203E000,4,7)]})
            self.assertEqual(result['events'],p['events']);self.assertNotIn(0x0203E000,state.mem)

    def test_object_and_task_epochs_preserved(self):
        for lane,(p,m) in self.results.items():
            site=p['conditional_calls'][-1]['site']
            for event in ({'heap_reinitialized':True},{'freed':[v.runtime.ROOT+v.runtime.HEADER]},{'task_invalidated':True}):
                with self.subTest(lane=lane,event=event),self.assertRaises(ValueError):
                    v.compose_selected(self.raw,lane,epoch_events={site:event})
            q=v.compose_selected(self.raw,lane,epoch_events={site:{'freed':[0x0203E000]}})
            self.assertEqual(q['lane'],lane)

    def test_constructor_object_zeroes_are_conditional_outputs(self):
        for p,m in self.results.values():
            pointer=v.runtime.ROOT+v.runtime.HEADER
            self.assertEqual(p['allocation_result_memory_conditions'],[dict(address=pointer+j,size=1,value=0) for j in (8,10,11,12,13,14)])
            alloc=next(r for r in p['conditional_calls'] if r['site']==0x0811F280)
            self.assertEqual(alloc['conditional_outputs'],p['allocation_result_memory_conditions'])
            self.assertFalse(alloc['effects_discharged'])

    def test_boundary_inputs_strict_and_not_silently_ignored(self):
        bad=[dict(opaque_writes={0:[(0,1,0)]}),dict(epoch_events={0:{}}),
             dict(epoch_events={0x0811F280:{'unknown':True}}),dict(epoch_events={0x0811F280:{'freed':[1]}}),
             dict(epoch_events={0x0811F280:{'task_invalidated':1}}),dict(return_machine=1)]
        for kwargs in bad:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.compose_selected(self.raw,**kwargs)
        for size in (0,4097,1<<32,1<<60):
            with self.subTest(size=size),self.assertRaises(ValueError):
                v.compose_selected(self.raw,opaque_writes={0x0811F280:[(0,size,0)]})

    def test_register_shift_semantics_and_poisoned_flags(self):
        ins=v.party.Ins(0x08121148,'alu_ext',('lsl',0,4))
        for value,amount,want in ((1,0,1),(1,31,1<<31),(1,32,0),(1,255,0),(1,256,1),(0,0,0)):
            m=v.Machine(self.raw,ins.address,{0:value,4:amount},instructions={ins.address:ins})
            m.step();self.assertEqual(m.reg[0],want);self.assertIsNone(m.flag_pc)
            self.assertTrue(all(isinstance(x,v.runtime.Unknown) for x in m.flags))
        m=v.Machine(self.raw,ins.address,{0:v.runtime.U,4:0},instructions={ins.address:ins})
        m.step();self.assertIsInstance(m.reg[0],v.runtime.Unknown)

    def test_sources_closed_and_manifest_independent(self):
        manifest=v.source_manifest();self.assertEqual(manifest,v.SOURCE_IDS)
        self.assertEqual(manifest['cfru-general_hooks.s']['git_blob_sha'],'6f05fd6603a31e05d2c5fc3ba3f7bea68a297f30')
        self.assertEqual(manifest['cfru-hooks']['path'],'hooks')
        manifest['cfru-hooks']['size']=0;self.assertNotEqual(manifest,v.SOURCE_IDS)
        for sources in ({},{key:b'' for key in v.take.SOURCE_IDS},{key:b'' for key in v.SOURCE_IDS}):
            with self.subTest(keys=list(sources)),self.assertRaises(ValueError):v.sources_bind(sources)

    def test_aliases_and_claim_limits(self):
        self.assertIs(v.raw_bind,v.bind_semantics)
        for lane,(p,m) in self.results.items():
            self.assertEqual(v.follow(self.raw,lane),p)
            self.assertTrue(p['conditional_finite_type_only']);self.assertTrue(p['synthetic_contract_execution'])
            for key in ('actual_runtime_execution_observed','full_story_reachability_claimed',
                        'universal_allocation_epoch_proven','all_opaque_effects_proven',
                        'irq_noninterference_proven','indirect_reference_completeness_claimed','donor_eligible'):
                self.assertIs(p[key],False)


if __name__=='__main__':unittest.main()
