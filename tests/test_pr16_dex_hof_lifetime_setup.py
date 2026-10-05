"""新setup欠落区間・effectモデルの負例。過去の旧suiteは再実行しない。"""
import copy,unittest
from unittest.mock import patch
import pr16_dex_hof_lifetime_setup as v
FIXTURE=None

def reseal(j,raw):
    if isinstance(j,dict):
        if {'address','size','sha256'}<=set(j):j['sha256']=v.identity(v.chunk(raw,j['address'],j['size']))['sha256']
        for x in j.values():reseal(x,raw)
    elif isinstance(j,list):
        for x in j:reseal(x,raw)

class PartySetupTests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:raise RuntimeError('explicit read-only fixture injection required')
        self.raw,self.review,self.parent,self.sources=FIXTURE
    def check(self,raw=None,review=None,parent=None,sources=None):
        return v.check_local(self.raw if raw is None else raw,self.review if review is None else review,self.parent if parent is None else parent,self.sources if sources is None else sources)
    def reject(self,edit):
        j=copy.deepcopy(self.review);edit(j)
        with self.assertRaises((ValueError,KeyError)):self.check(review=j)
    def mutation(self,a,n=2):
        r=bytearray(self.raw);r[a-0x08000000]^=1;j=copy.deepcopy(self.review);p=copy.deepcopy(self.parent);reseal(j,r);reseal(p,r)
        with self.assertRaises(ValueError):self.check(raw=r,review=j,parent=p)
    def test_01_whole_local_cfg_keeps_unknown(self):
        p=self.check();self.assertEqual(p['newly_classified'],0);self.assertFalse(p['root_to_hit_lifetime_proven']);self.assertFalse(p['donor_eligible']);self.assertEqual(p['cfg']['state_count'],23)
    def test_02_every_new_instruction_halfword_resealed(self):
        for a in sorted(v.NEW_BYTES):
            if a%2==0:
                with self.subTest(address=a):self.mutation(a)
    def test_03_every_new_literal_resealed(self):
        for a in v.NEW_WORDS:
            with self.subTest(address=a):self.mutation(a,4)
    def test_04_every_setup_state_dispatch_resealed(self):
        for a in v.TABLE:
            with self.subTest(address=a):self.mutation(a,4)
    def test_05_every_selected_getter_dispatch_resealed(self):
        for a in v.SELECTED_TABLE:
            with self.subTest(address=a):self.mutation(a,4)
    def test_06_padding_is_not_unwitnessed_gap(self):
        for a in v.PADDING:
            with self.subTest(address=a):self.mutation(a)
    def test_07_no_skipped_new_window(self):self.reject(lambda j:j['instruction_windows'].pop())
    def test_08_no_extra_new_window(self):self.reject(lambda j:j['instruction_windows'].append(j['instruction_windows'][0]))
    def test_09_no_window_relocation(self):self.reject(lambda j:j['instruction_windows'][0].update(address=j['instruction_windows'][0]['address']+2))
    def test_10_no_shortened_window(self):self.reject(lambda j:j['instruction_windows'][0].update(size=j['instruction_windows'][0]['size']-2))
    def test_11_no_missing_literal(self):self.reject(lambda j:j['literal_words'].pop(str(next(iter(v.NEW_WORDS)))))
    def test_12_no_claimed_lifetime(self):self.reject(lambda j:j.update(root_to_hit_lifetime_proven=True))
    def test_13_no_donor(self):self.reject(lambda j:j.update(donor_eligible=True))
    def test_14_no_new_classification(self):self.reject(lambda j:j.update(classifications_added=1))
    def test_15_no_deleted_opaque_obligation(self):self.reject(lambda j:j['unresolved_obligations'].pop())
    def test_16_no_claim_closed_opaque_call(self):self.reject(lambda j:j['call_obligations'][-1].update(status='closed'))
    def test_17_no_dropped_call(self):self.reject(lambda j:j['call_obligations'].pop())
    def test_18_no_current_sha_spoof(self):self.reject(lambda j:j['required_candidate'].update(sha256='0'*64))
    def test_19_no_omitted_inherited_reference(self):self.reject(lambda j:j['inherited_instruction_references'].pop())
    def test_20_parent_instruction_hash_checked(self):
        p=copy.deepcopy(self.parent);scope,name=v.OLD_REFS[0];sub=p if scope=='mail' else p['task_evidence'];sub['instruction_windows'][name]['sha256']='0'*64
        with self.assertRaises(ValueError):self.check(parent=p)
    def test_21_parent_literal_hash_checked(self):
        p=copy.deepcopy(self.parent);p['literal_words'][str(0x0811F294)]['sha256']='0'*64
        with self.assertRaises(ValueError):self.check(parent=p)
    def test_22_source_identity_cannot_be_resealed(self):
        for name in self.sources:
            with self.subTest(source=name):
                sources=dict(self.sources);sources[name]+=b'\n';p=copy.deepcopy(self.parent);p['source_bindings'][name].update(v.identity(sources[name]));p['source_bindings'][name]['git_blob_sha']=v.hashlib.sha1(b'blob '+str(len(sources[name])).encode()+b'\0'+sources[name]).hexdigest()
                with self.assertRaises(ValueError):self.check(parent=p,sources=sources)
    def test_23_current_identity_never_grants_acceptance(self):
        # new-only拒否APIを検証。過去独立reviewの操作は呼ばない。
        with self.assertRaisesRegex(ValueError,'lifetime remains unproven'):v.regions(self.raw,self.review,self.parent,self.sources)
    def test_24_record_disallows_raw_bytes_and_private_path(self):
        for key in ('raw','hex','path','value'):
            with self.subTest(field=key):self.reject(lambda j:j['instruction_windows'][0].update({key:'forbidden'}))
    def test_25_all_constructor_bytes_partitioned(self):self.assertEqual(v.cfg_proof()['whole_constructor_bytes'],348)
    def test_26_all_setup_bytes_partitioned(self):self.assertEqual(v.cfg_proof()['whole_setup_bytes'],570)
    def test_27_reset_tasks_is_actual_empty_slot_producer(self):
        m=v.Machine(self.raw,0x08076B54).run();self.assertEqual([m.read(v.TASKS+40*i+4,1) for i in range(16)],[0]*16)
    def test_28_task_capacity_failure_return_zero_is_ambiguous(self):
        p=v.effects(self.raw);trace=p['reset_then_uninterrupted_task_calls'];self.assertEqual(trace[0]['result'],0);self.assertTrue(trace[0]['new_task_registered']);self.assertEqual(trace[-1]['result'],0);self.assertFalse(trace[-1]['new_task_registered']);self.assertFalse(p['task_slot_guarantee_across_setup_helpers'])
    def test_29_unknown_dereference_is_not_silently_assumed_safe(self):
        with self.assertRaisesRegex(ValueError,'unknown memory address'):v.Machine(self.raw,0x08076BC8).step()
    def test_30_unbound_callee_is_not_silently_summarized(self):
        with self.assertRaisesRegex(ValueError,'outside closed model'):v.Machine(self.raw,0x08002B9C).run()
    def test_31_unknown_branch_requires_path_split(self):
        m=v.Machine(self.raw,0x0812B9FA)
        for _ in range(3):m.step()
        with self.assertRaisesRegex(ValueError,'symbolic split'):m.step()
    def test_32_species_count_is_bounded_with_unknown_input(self):
        p=v.effects(self.raw);effect=next(x for x in p['closed_effects'] if x['role']=='calculate_party_count_species11');self.assertEqual(effect['symbolic_paths'],127);self.assertEqual(effect['return_values'],list(range(7)))
    def test_33_ordinary_minigame_precondition_is_required(self):
        with self.assertRaisesRegex(ValueError,'outside closed model'):v.Machine(self.raw,0x081210D4,memory={0x0203B01C:11}).run()
    def test_34_local_word_write_sentinel_changes_get_rejected(self):
        # allocation field0 writerをfield4に変える負例。親窓もresealして意味検査で拒否。
        a=0x0811F2C4;r=bytearray(self.raw);r[a-0x08000000:a-0x08000000+2]=v.encoded(v.inherited.Ins(a,'mem',(False,'word',0,5,4)));j=copy.deepcopy(self.review);p=copy.deepcopy(self.parent);reseal(j,r);reseal(p,r)
        with self.assertRaises(ValueError):self.check(raw=r,review=j,parent=p)
    def test_35_full_task_table_has_no_external_write(self):
        mem={v.TASKS+40*i+4:1 for i in range(16)};m=v.Machine(self.raw,0x08076BB4,{0:0x08120319,1:0},mem).run();self.assertEqual(m.reg[0],0);self.assertEqual(m.external_writes(),[])
    def test_36_lifetime_claim_is_still_rejected_after_successful_callee_effects(self):
        p=self.check();self.assertEqual(p['effects']['status'],'PASS_BOUNDED_CALLEE_EFFECTS');self.assertFalse(p['allocation_same_lifetime_proven']);self.assertIn('remaining_setup_helper_return_and_memory_effects_not_closed',p['unresolved_obligations'])

    def test_37_flag_writer_between_cmp_and_branch_is_rejected(self):
        start=0x08FFF000
        for kind,args in [('imm',('add',0,1)),('imm',('mov',0,1)),('shift',('lsl',0,0,1)),('alu',('neg',0,0)),('addi',(0,0,1))]:
            with self.subTest(kind=kind,args=args):
                fake={start:v.inherited.Ins(start,'imm',('cmp',0,0)),start+2:v.inherited.Ins(start+2,kind,args),start+4:v.inherited.Ins(start+4,'branch',(0,start+8))}
                with patch.dict(v.INS,fake):
                    m=v.Machine(self.raw,start,{0:0});m.step();m.step()
                    with self.assertRaisesRegex(ValueError,'flag provenance'):m.step()
    def test_38_direct_branch_entry_without_cmp_is_rejected(self):
        m=v.Machine(self.raw,0x0812BA00);m.flags=(0,True,True,False)
        with self.assertRaisesRegex(ValueError,'flag provenance'):m.step()
    def test_39_species_and_egg_composition_contract(self):
        p=v.pokemon_data_effects(self.raw);self.assertEqual(len(p['contracts']),12);self.assertFalse(p['heap_cell_written']);self.assertFalse(p['task_array_written'])
        self.assertEqual({x['field'] for x in p['contracts']},{11,45});self.assertEqual({x['party_slot'] for x in p['contracts']},set(range(6)))
    def test_40_species_contract_checks_bytes_without_parent_wrapper(self):
        r=bytearray(self.raw);r[0x0803F7E8-0x08000000]^=1
        with self.assertRaises(ValueError):v.pokemon_data_effects(r)
    def test_41_cfg_rejects_edge_that_skips_cmp(self):
        a=0x0811F292;original=v.INS[a]
        with patch.dict(v.INS,{a:v.inherited.Ins(a,'jump',(0x0811F2D8,))}):
            with self.assertRaisesRegex(ValueError,'CMP producer'):v.cfg_proof()

    def test_42_setup_create_task_calls_require_uninterrupted_trace(self):
        calls={x['address']:x for x in v.obligations()}
        for site in (0x0811F5C4,0x0811F65A):
            self.assertEqual(calls[site]['status'],'reset_then_uninterrupted_priority0_only');self.assertFalse(calls[site]['actual_setup_context_discharged']);self.assertIn('no other task write or scheduler dispatch intervenes',calls[site]['required_context'])
    def test_43_omitting_callee_preconditions_is_rejected(self):
        self.reject(lambda j:next(x for x in j['call_obligations'] if x['address']==0x0811F5C4).update(required_context=[]))
    def test_44_pretending_setup_context_is_discharged_is_rejected(self):
        self.reject(lambda j:next(x for x in j['call_obligations'] if x['address']==0x0811F65A).update(actual_setup_context_discharged=True))
