"""Mystery Gift境界の新規診断専用test。import時に私有fileへ触れない。"""
import copy
import hashlib
import unittest
import pr16_dex_hof_boundary_mystery as v

FIXTURE=None


def reseal(obj,raw):
    if isinstance(obj,dict):
        if {'address','size','sha256'} <= obj.keys():
            a=obj['address']-0x08000000;obj['sha256']=hashlib.sha256(raw[a:a+obj['size']]).hexdigest()
        for x in obj.values():reseal(x,raw)
    elif isinstance(obj,list):
        for x in obj:reseal(x,raw)


class BoundaryMysteryTests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:raise RuntimeError('explicit in-memory FIXTURE required')
        self.raw,self.inherited,self.review,self.sources=FIXTURE

    def check(self,raw=None,inherited=None,review=None,sources=None):
        return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,
                          self.review if review is None else review,self.sources if sources is None else sources)

    def reject_review(self,edit):
        r=copy.deepcopy(self.review);edit(r)
        with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)

    def reject_evidence(self,edit):
        e=v.evidence_template();edit(e)
        with self.assertRaises((ValueError,KeyError,TypeError)):v.witness_geometry(e)

    def mutate(self,a,n,value):
        raw=bytearray(self.raw);pos=a-0x08000000;encoded=value.to_bytes(n,'little')
        self.assertNotEqual(raw[pos:pos+n],encoded);raw[pos:pos+n]=encoded
        r,i=copy.deepcopy(self.review),copy.deepcopy(self.inherited)
        reseal(r,raw);reseal(i,raw)
        with self.assertRaises((ValueError,KeyError,TypeError)):self.check(raw=raw,review=r,inherited=i)

    def contract(self,**updates):
        args=dict(active_before=[0]*16,task_id=0,state=11,text_state=0,placement=0,
                  setup_result=1,state0_calls_returned=True,selected_fields_preserved=True,
                  stack_nonalias=True,valid_window_resource=True)
        args.update(updates);return v.selected_task_contract(**args)

    def test_01_only_one_minimal_mixed_boundary(self):
        before=copy.deepcopy(self.inherited);rows,p=self.check()
        self.assertEqual([(r.start,r.end,r.kind) for r in rows],[(0x08142F5C,0x08142F62,v.KIND)])
        self.assertEqual(p['count'],1);self.assertEqual(before,self.inherited)
        self.assertEqual(p['protected_windows'],len(v.WINDOWS))

    def test_02_geometry_closed_partition(self):
        r=self.check()[0][0];self.assertEqual(v.witness_geometry(r.evidence),(r.start,6))
        self.assertEqual([x['size'] for x in r.evidence['elements']],[4,2])

    def test_03_current_identity_wrapper_rejects_diagnostic(self):
        if v.identity(self.raw)==v.CANDIDATE:self.assertEqual(v.regions(*FIXTURE)[1]['count'],1)
        else:
            with self.assertRaises(ValueError):v.regions(*FIXTURE)

    def test_04_current_target_binding(self):
        i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
        with self.assertRaises(ValueError):self.check(inherited=i)

    def test_05_unaccepted_original_required(self):
        i=copy.deepcopy(self.inherited);next(h for h in i['hits'] if h['address']==v.HIT)['accepted']=True
        with self.assertRaises(ValueError):self.check(inherited=i)

    def test_06_external_owner_required(self):
        i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review)
        next(h for h in i['hits'] if h['address']==v.HIT)['owner_candidates']=['x'];r['hit']['owner_candidates']=['x']
        with self.assertRaises(ValueError):self.check(inherited=i,review=r)

    def test_07_duplicate_original_rejected(self):
        i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(self.review['hit']))
        with self.assertRaises(ValueError):self.check(inherited=i)

    def test_08_geometry_missing_literal(self):self.reject_evidence(lambda e:e['elements'].pop(0))
    def test_09_geometry_missing_instruction(self):self.reject_evidence(lambda e:e['elements'].pop())
    def test_10_geometry_half_instruction(self):self.reject_evidence(lambda e:e['elements'][1].update(size=1))
    def test_11_geometry_only_hit_fragment(self):self.reject_evidence(lambda e:e['elements'][0].update(address=v.HIT,size=3))
    def test_12_geometry_nonadjacent(self):self.reject_evidence(lambda e:e['elements'][1].update(address=0x08142F62))
    def test_13_geometry_reverse_order(self):self.reject_evidence(lambda e:e['elements'].reverse())
    def test_14_geometry_duplicate_element(self):self.reject_evidence(lambda e:e['elements'].append(copy.deepcopy(e['elements'][0])))
    def test_15_no_pointer_interpretation(self):self.reject_evidence(lambda e:e.update(literal_is_pointer=True))
    def test_16_no_homogeneous_instruction_claim(self):self.reject_evidence(lambda e:e['elements'][0].update(role='complete_thumb_ldr_literal16'))
    def test_17_both_elements_have_root(self):self.reject_evidence(lambda e:e['elements'][0].pop('root'))
    def test_18_distinct_selector_roots(self):self.reject_evidence(lambda e:e['elements'][1]['root'].update(selector=11))
    def test_19_wrong_branch_target(self):self.reject_evidence(lambda e:e['elements'][1]['root'].update(selected_successor=0x08142F62))
    def test_20_wrong_consumer_width(self):self.reject_evidence(lambda e:e['elements'][0]['root'].update(load_width=1))
    def test_21_no_simultaneous_path_claim(self):self.reject_evidence(lambda e:e.update(single_path_covers_both_elements=True))
    def test_22_no_unrooted_geometry(self):self.reject_evidence(lambda e:e.update(root_verified=False))
    def test_23_no_integer_bool_alias(self):self.reject_evidence(lambda e:e['elements'][1]['root'].update(placement=True))
    def test_24_no_extra_evidence_fields(self):self.reject_evidence(lambda e:e.update(override=True))
    def test_25_no_extra_review_fields(self):self.reject_review(lambda r:r.update(override=True))
    def test_26_no_whole_function_range(self):self.reject_review(lambda r:r['claims'].update(whole_function_range_classified=True))
    def test_27_no_universal_epoch_claim(self):self.reject_review(lambda r:r['claims'].update(universal_callback_epoch_claimed=True))
    def test_28_no_client_heap_lifetime_claim(self):self.reject_review(lambda r:r['claims'].update(client_heap_lifetime_required=True))
    def test_29_no_runtime_claim(self):self.reject_review(lambda r:r['claims'].update(runtime_execution_observed=True))
    def test_30_no_donor_claim(self):self.reject_review(lambda r:r['claims'].update(donor_eligible=True))
    def test_31_root_not_symbol_name(self):self.reject_review(lambda r:r['root'].update(kind='symbol_only'))
    def test_32_missing_window(self):self.reject_review(lambda r:r['windows'].pop())
    def test_33_duplicated_window(self):self.reject_review(lambda r:r['windows'].append(copy.deepcopy(r['windows'][0])))
    def test_34_reordered_windows(self):self.reject_review(lambda r:r['windows'].reverse())
    def test_35_extra_window_field(self):self.reject_review(lambda r:r['windows'][0].update(trusted=True))
    def test_36_source_content_change(self):
        s=dict(self.sources);s['pret-mystery_gift_menu.c']+=b'\n'
        with self.assertRaises(ValueError):self.check(sources=s)
    def test_37_source_manifest_resealed(self):self.reject_review(lambda r:r['source_bindings']['pret-mystery_gift_menu.c'].update(sha256='0'*64))
    def test_38_source_role_missing(self):
        s=dict(self.sources);s.pop('pret-task.c')
        with self.assertRaises(ValueError):self.check(sources=s)
    def test_39_every_semantic_halfword_resealed(self):
        count=0
        for a,n in v.WINDOWS.values():
            for offset in range(0,n,2):
                z=min(2,n-offset);address=a+offset;old=int.from_bytes(v.chunk(self.raw,address,z),'little')
                with self.subTest(address=address,size=z):self.mutate(address,z,old^1)
                count+=1
        self.assertEqual(count,sum((n+1)//2 for a,n in v.WINDOWS.values()))
    def test_40_task_function_thumb_bit(self):self.mutate(0x081435A0,4,0x081435A8)
    def test_41_wrong_task_stride(self):
        old=int.from_bytes(v.chunk(self.raw,0x081435B4,2),'little');self.mutate(0x081435B4,2,old^64)
    def test_42_wrong_textstate_field(self):
        old=int.from_bytes(v.chunk(self.raw,0x0814357C,2),'little');self.mutate(0x0814357C,2,old^64)
    def test_43_wrong_main_field(self):
        old=int.from_bytes(v.chunk(self.raw,0x08000546,2),'little');self.mutate(0x08000546,2,old^64)
    def test_44_mask_pointer_substitution(self):self.mutate(0x08142F5C,4,0x08FFFFFF)
    def test_45_mask_in_other_branch_changed(self):self.mutate(0x08142F90,4,0xFFFFFF00)
    def test_46_state0_increment_removed(self):
        old=int.from_bytes(v.chunk(self.raw,0x08142F88,2),'little');self.mutate(0x08142F88,2,old^1)
    def test_47_both_separate_input_profiles(self):
        for state,place in ((11,0),(23,1)):
            p=self.contract(state=state,placement=place);self.assertEqual(p['next_text_state'],1);self.assertEqual(p['state_preserved'],state)
    def test_48_nonempty_admission_rejected(self):
        for index in range(16):
            active=[0]*16;active[index]=1
            with self.subTest(index=index),self.assertRaises(ValueError):self.contract(active_before=active)
    def test_49_invalid_taskid(self):
        for i in (-1,1,15,16,True):
            with self.subTest(task_id=i),self.assertRaises(ValueError):self.contract(task_id=i)
    def test_50_mismatched_state_placement(self):
        for state,place in ((11,1),(23,0),(37,1),(38,0),(11,True)):
            with self.subTest(state=state,place=place),self.assertRaises(ValueError):self.contract(state=state,placement=place)
    def test_51_state0_required(self):
        for state in (1,2,255,-1,False):
            with self.subTest(text_state=state),self.assertRaises(ValueError):self.contract(text_state=state)
    def test_52_setup_failure_rejected(self):
        for value in (0,-1,True,2**32):
            with self.subTest(value=value),self.assertRaises(ValueError):self.contract(setup_result=value)
    def test_53_finite_conditions_required(self):
        for name in ('state0_calls_returned','selected_fields_preserved','stack_nonalias','valid_window_resource'):
            for value in (False,1,None):
                with self.subTest(name=name,value=value),self.assertRaises(ValueError):self.contract(**{name:value})
    def test_54_contract_cannot_be_weakened(self):self.reject_review(lambda r:r['input_contract'].update(create_admission='any_task_or_failed_allocation'))
    def test_55_source_bytes_and_private_paths_not_published(self):
        def scan(obj):
            if isinstance(obj,dict):
                self.assertFalse(set(obj)&{'raw','rawhex','bytes','data','private_path','member_path'})
                for x in obj.values():scan(x)
            elif isinstance(obj,list):
                for x in obj:scan(x)
        scan(self.review);scan(self.check()[0][0].evidence)
    def test_56_no_invented_current_diagnostic_identity(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
    def test_57_scalar_mask_bitfield(self):
        mask=v.LITERALS[0x08142F5C]
        for top in (0,9,15,255):
            word=0x12345678;out=(word&mask)|(top<<16)
            self.assertEqual((out>>16)&255,top);self.assertEqual(out&mask,word&mask)
    def test_58_helper_stack_nonalias_keeps_two_fields_distinct(self):
        p=self.contract();self.assertEqual(p['text_state_address']-p['state_address'],1)
        self.assertNotEqual(p['text_state_address'],p['data_address'])
    def test_59_selector11_and23_tables_are_not_thumb_pointers(self):
        self.assertEqual(v.LITERALS[0x08143600],0x08143898);self.assertEqual(v.LITERALS[0x08143630],0x08143AA2)
        self.assertEqual(v.BLOCKS['task_entry_bounded_dispatch'][1][-1],('movhi',15,0))
    def test_60_input_check_is_not_runtime_observation(self):
        self.contract();self.assertFalse(self.check()[1]['runtime_execution_observed'])
