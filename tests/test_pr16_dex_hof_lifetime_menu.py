"""新scope限定の負例。全証跡SHAを再sealしても意味改変を拒否する。"""
import copy,unittest
from unittest.mock import patch
import pr16_dex_hof_lifetime_menu as v
FIXTURE=None

def reseal(j,raw):
    if isinstance(j,dict):
        if set(j)=={'address','size','sha256'}:j['sha256']=v.identity(v.chunk(raw,j['address'],j['size']))['sha256']
        for value in j.values():reseal(value,raw)
    elif isinstance(j,list):
        for value in j:reseal(value,raw)

class MenuRootTests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:raise RuntimeError('fixture must be injected explicitly')
        self.raw,self.review=FIXTURE
    def check(self,raw=None,j=None):return v.check_local(self.raw if raw is None else raw,self.review if j is None else j)
    def reject(self,change):
        j=copy.deepcopy(self.review);change(j)
        with self.assertRaises((ValueError,KeyError)):self.check(j=j)
    def mutate(self,address,size=2):
        raw=bytearray(self.raw);raw[address-0x08000000]^=1
        j=copy.deepcopy(self.review);reseal(j,raw)
        with self.assertRaises(ValueError):self.check(raw=raw,j=j)
    def test_01_positive_keeps_unknown(self):
        p=self.check();self.assertEqual(p['newly_classified'],0);self.assertFalse(p['full_root_to_hit_lifetime_proven']);self.assertFalse(p['task_full_lifetime_proven']);self.assertFalse(p['current_acceptance_claimed'])
    def test_02_every_instruction_halfword_resealed(self):
        addresses=sorted({a for rows in v.BLOCKS.values() for i in rows for a in range(i.address,i.address+i.size,2)})
        for a in addresses:
            with self.subTest(address=a):self.mutate(a)
    def test_03_every_literal_resealed(self):
        for a in v.LITERALS:
            with self.subTest(address=a):self.mutate(a,4)
    def test_04_fields_resealed(self):
        for a,n,_ in v.FIELDS.values():
            with self.subTest(address=a):self.mutate(a,n)
    def test_05_remove_opaque_call_obligation_rejected(self):self.reject(lambda j:j['unresolved_obligations'].pop(2))
    def test_06_acceptance_claim_rejected(self):self.reject(lambda j:j.update(newly_classified=1))
    def test_07_lifetime_claim_rejected(self):self.reject(lambda j:j.update(full_root_to_hit_lifetime_proven=True))
    def test_08_donor_claim_rejected(self):self.reject(lambda j:j.update(donor_eligible=True))
    def test_09_expanded_manifest_rejected(self):self.reject(lambda j:j.update(task_survives=True))
    def test_10_missing_window_rejected(self):self.reject(lambda j:j['instruction_windows'].pop('installed_tutor_compatibility_hook'))
    def test_11_changed_geometry_rejected(self):self.reject(lambda j:j['instruction_windows']['field_party_constructor_call'].update(size=2))
    def test_12_missing_actual_hook_rejected(self):self.reject(lambda j:j['literal_words'].pop(str(0x0911022C)))
    def test_13_old_input_not_current(self):
        with self.assertRaises(ValueError):v.regions(self.raw,self.review)
    def test_14_whole_identity_does_not_promote(self):
        real=v.identity
        with patch.object(v,'identity',side_effect=lambda raw:v.shared.CANDIDATE if raw is self.raw else real(raw)):
            with self.assertRaisesRegex(ValueError,'full allocation/task lifetime'):v.regions(self.raw,self.review)
    def test_15_unwitnessed_change_diagnostic_rejected(self):
        raw=bytearray(self.raw);raw[-1]^=1
        self.assertEqual(self.check(raw=raw)['newly_classified'],0)
        with self.assertRaises(ValueError):v.diagnose(raw,self.review)
    def test_16_mail_range_all_keys(self):
        for cursor in range(3):
            for keys in range(65536):self.assertIn(v.selector_return(cursor,3,keys),(-2,-1,0,1,2))
    def test_17_move_cursor_preserves_range_conditionally(self):
        for maximum in range(127):
            for cursor in range(maximum+1):
                for delta in (-1,0,1):
                    for wrap in (False,True):self.assertTrue(0<=v.cursor_transition(cursor,0,maximum,delta,wrap)<=maximum)
    def test_18_bad_cursor_preconditions_not_assumed(self):
        for cursor,count in ((-1,3),(3,3),(0,0),(0,128),(255,3)):
            with self.subTest(cursor=cursor,count=count):
                with self.assertRaises(ValueError):v.selector_return(cursor,count,1)
    def test_19_field0_is_not_task_lifetime(self):
        with self.assertRaisesRegex(ValueError,'field4'):v.task_contract(0,254,255,0x08126AB9,0)
        p=v.task_contract(1,254,255,0x08126AB9,0)
        self.assertFalse(p['lifetime_proven']);self.assertFalse(p['whole_list_membership_proven'])
    def test_20_bad_task_index_or_links(self):
        for args in ((1,254,255,0x08126AB9,16),(1,16,255,0x08126AB9,0),(1,254,16,0x08126AB9,0),(1,254,255,0x08126AB8,0)):
            with self.assertRaises(ValueError):v.task_contract(*args)
    def test_21_obsolete_tutor_body_not_reachable_without_hook(self):
        # 09110228のhookを旧命令に似た別命令へ置換しSHAを再計算しても拒否。
        self.mutate(0x09110228)
    def test_22_wrong_start_menu_callback_rejected(self):self.mutate(0x0836B380,4)

    def test_23_ordinary_adapter_local_frames(self):
        p=self.check()['ordinary_tutor_adapter_local_frames']
        self.assertEqual(p['unresolved_external_callees'],[0x0803F354])
        self.assertTrue(p['compact_reader_transitive_effects_bound'])
        self.assertFalse(p['transitive_noninterference_proven'])
        self.assertEqual(p['functions']['ordinary_adapter']['maximum_local_stack_bytes'],400)
        self.assertEqual(p['compact_reader_output_size'],8)
        self.assertEqual(p['compact_resolver_output_is_reader_stack_offset'],22)
    def test_24_compact_output_cannot_escape_eight_bytes(self):
        raw=bytearray(self.raw);a=0x095F9FFE
        raw[a-0x08000000:a-0x08000000+2]=v.encoded(v.shared.Ins(a,'mem',(False,'word',3,2,8)))
        j=copy.deepcopy(self.review);reseal(j,raw)
        with self.assertRaises(ValueError):self.check(raw=raw,j=j)
    def test_25_output_pointer_cannot_use_other_stack_slot(self):
        raw=bytearray(self.raw);a=0x095FA1B6
        raw[a-0x08000000:a-0x08000000+2]=v.encoded(v.shared.Ins(a,'spmem',(True,3,52)))
        j=copy.deepcopy(self.review);reseal(j,raw)
        with self.assertRaises(ValueError):self.check(raw=raw,j=j)
    def test_26_stack_cfg_rejects_unbalanced_return(self):
        blocks=dict(v.BLOCKS);name='compact_reader'
        blocks[name]=tuple(v.shared.Ins(i.address,'spadd',(32,)) if i.address==0x095FA0DA else i for i in blocks[name])
        with patch.object(v,'BLOCKS',blocks):
            with self.assertRaises(ValueError):v.adapter_frame_effects()
    def test_27_stack_cfg_rejects_unclosed_branch(self):
        blocks=dict(v.BLOCKS);name='supply_tutor_slot'
        blocks[name]=tuple(v.shared.Ins(i.address,'branch',(9,0x095F9464)) if i.address==0x09FFF57A else i for i in blocks[name])
        with patch.object(v,'BLOCKS',blocks):
            with self.assertRaises(ValueError):v.adapter_frame_effects()
    def getter_fixture(self):
        return dict(status='PASS_SPECIES11_EGG45_BOUNDED_PARTY_CALLEES',heap_cell_written=False,task_array_written=False,allocation_nonalias_precondition_proven=False,
          contracts=[dict(field=f,party_slot=s,argument_pointer=0x020241E4+s*100,write_region=dict(address=0x020241E4+s*100+32,size=48),symbolic_paths=1) for f in (11,45) for s in range(6)])
    def test_28_composition_cannot_promote_lifetime(self):
        p=v.compose_ordinary_adapter(self.raw,self.review,lambda raw:self.getter_fixture())
        self.assertFalse(p['full_root_to_hit_lifetime_proven']);self.assertFalse(p['allocation_nonalias_proven']);self.assertEqual(p['newly_classified'],0)
    def test_29_composition_missing_getter_branch_rejected(self):
        j=self.getter_fixture();j['contracts'].pop()
        with self.assertRaises(ValueError):v.compose_ordinary_adapter(self.raw,self.review,lambda raw:j)
    def test_30_composition_expanded_getter_write_rejected(self):
        j=self.getter_fixture();j['contracts'][0]['write_region']['size']=100
        with self.assertRaises(ValueError):v.compose_ordinary_adapter(self.raw,self.review,lambda raw:j)
    def test_31_composition_cannot_assume_allocation_nonalias(self):
        j=self.getter_fixture();j['allocation_nonalias_precondition_proven']=True
        with self.assertRaises(ValueError):v.compose_ordinary_adapter(self.raw,self.review,lambda raw:j)
