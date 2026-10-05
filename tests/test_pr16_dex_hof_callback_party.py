"""新ReadMail局所証拠の反証だけ。fixtureは明示注入し原本を変更しない。"""
import copy, unittest
from unittest.mock import patch
import pr16_dex_hof_callback_party as v
FIXTURE=None

def reseal(obj,raw):
    if isinstance(obj,dict):
        if {'address','size','sha256'}<=obj.keys():obj['sha256']=v.identity(v.chunk(raw,obj['address'],obj['size']))['sha256']
        for value in obj.values():reseal(value,raw)
    elif isinstance(obj,list):
        for value in obj:reseal(value,raw)

class PartyCallbacksTests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:raise RuntimeError('explicit fixture injection required')
        self.raw,self.review,self.sources=FIXTURE
    def check(self,raw=None,review=None,sources=None):
        return v.check_local(self.raw if raw is None else raw,self.review if review is None else review,self.sources if sources is None else sources)
    def reject(self,edit):
        j=copy.deepcopy(self.review);edit(j)
        with self.assertRaises((ValueError,KeyError)):self.check(review=j)
    def mutate(self,a,n):
        self.assertIn(n,(1,2,4));self.assertEqual(len(v.chunk(self.raw,a,n)),n)
        raw=bytearray(self.raw);raw[a-0x08000000]^=1
        j=copy.deepcopy(self.review);reseal(j,raw)
        with self.assertRaises(ValueError):self.check(raw=raw,review=j)
    def test_01_only_local_consumers_pass(self):
        p=self.check();self.assertEqual(p['newly_classified'],0);self.assertEqual(p['semantic_instruction_count'],401)
        self.assertFalse(p['actual_root_proven']);self.assertFalse(p['same_allocation_full_lifetime_proven'])
    def test_02_wrong_candidate_rejected(self):self.reject(lambda j:j['required_candidate'].update(sha256='0'*64))
    def test_03_actual_mail_role_not_summary(self):self.reject(lambda j:j.update(role='party_summary'))
    def test_04_cannot_remove_root_blocker(self):self.reject(lambda j:j['unresolved_obligations'].pop(0))
    def test_05_cannot_remove_lifetime_blocker(self):self.reject(lambda j:j['unresolved_obligations'].pop(2))
    def test_06_no_classification_even_current(self):self.reject(lambda j:j.update(classifications_added=1))
    def test_07_no_donor_lease(self):self.reject(lambda j:j.update(donor_eligible=True))
    def test_08_no_count_drift(self):self.reject(lambda j:j['baseline_counts'].update(unknown=145))
    def test_09_no_missing_block(self):self.reject(lambda j:j['instruction_windows'].pop('constructor_entry'))
    def test_10_no_widened_hit_window(self):self.reject(lambda j:j['minimal_instruction_window'].update(size=8))
    def test_11_no_half_BL(self):self.reject(lambda j:j['minimal_instruction_window'].update(size=4))
    def test_12_no_missing_word(self):self.reject(lambda j:j['literal_words'].pop(str(0x0812455C)))
    def test_13_no_missing_actions_field(self):self.reject(lambda j:j['data_fields'].pop('read_action_id'))
    def test_14_each_new_instruction_halfword_resealed(self):
        addresses=sorted({a for rows in v.BLOCKS.values() for i in rows for a in range(i.address,i.address+i.size,2)})
        for a in addresses:
            with self.subTest(address=a):self.mutate(a,2)
        self.assertEqual(len(addresses),445)
    def test_15_all_pointer_roles_resealed(self):
        for a in v.LITERALS:
            with self.subTest(address=a):self.mutate(a,4)
    def test_16_all_typed_fields_resealed(self):
        for a,n,_ in v.DATA_FIELDS.values():
            with self.subTest(address=a):self.mutate(a,n)
    def test_17_source_mutation_rejected(self):
        for name in v.SOURCE_IDS:
            with self.subTest(source=name):
                src=dict(self.sources);src[name]+=b'\n'
                with self.assertRaises(ValueError):self.check(sources=src)
    def test_18_source_resealed_still_rejected(self):
        src=dict(self.sources);name='pret-party_menu.c';src[name]+=b'\n';j=copy.deepcopy(self.review)
        j['source_bindings'][name].update(v.identity(src[name]),git_blob_sha=v.hashlib.sha1(b'blob '+str(len(src[name])).encode()+b'\0'+src[name]).hexdigest())
        with self.assertRaises(ValueError):self.check(review=j,sources=src)
    def test_19_old_diagnostic_not_current_wrapper(self):
        with self.assertRaises(ValueError):v.regions(self.raw,{'candidate':v.identity(self.raw)},self.review,self.sources)
    def test_20_current_identity_alone_never_accepts(self):
        real=v.identity
        with patch.object(v,'identity',side_effect=lambda raw:v.CANDIDATE if raw is self.raw else real(raw)):
            with self.assertRaisesRegex(ValueError,'lifetime remain unproven'):v.regions(self.raw,{'candidate':v.CANDIDATE},self.review,self.sources)
    def test_21_regions_keep_unknown(self):
        hit=dict(self.review['hit'],accepted=False,owner_candidates=[])
        other=dict(self.review['task_evidence']['hit'],accepted=False,owner_candidates=[])
        r,p=v._regions(self.raw,{'classified':728,'unclassified':146,'hits':[hit,other]},self.review,self.sources)
        self.assertEqual(r,[]);self.assertEqual(p['newly_classified'],0)
    def test_22_regions_reject_already_accepted(self):
        hit=dict(self.review['hit'],accepted=True,owner_candidates=[])
        with self.assertRaises(ValueError):v._regions(self.raw,{'classified':728,'unclassified':146,'hits':[hit]},self.review,self.sources)
    def test_23_unrelated_owner_rejected(self):
        hit=dict(self.review['hit'],accepted=False,owner_candidates=['other'])
        with self.assertRaises(ValueError):v._regions(self.raw,{'classified':728,'unclassified':146,'hits':[hit]},self.review,self.sources)
    def test_24_no_extra_semantic_block(self):self.reject(lambda j:j['instruction_windows'].update(extra=j['minimal_instruction_window']))
    def test_25_geometry_is_not_mutable_review_control(self):self.reject(lambda j:j['instruction_windows']['state20_task_consumer'].update(address=0x0811F5BE))
    def test_26_source_role_cannot_be_dropped(self):self.reject(lambda j:j['source_bindings'].pop('BPRJ.ld'))
    def test_27_diagnose_binds_executed_whole_input(self):
        if v.identity(self.raw)==self.review['diagnostic_input']:
            self.assertEqual(v.diagnose(self.raw,self.review,self.sources)['newly_classified'],0)
        else:
            with self.assertRaisesRegex(ValueError,'metadata matches whole executed input'):v.diagnose(self.raw,self.review,self.sources)
            self.assertEqual(self.check()['newly_classified'],0)
    def test_28_diagnose_rejects_wrong_input_metadata(self):
        j=copy.deepcopy(self.review);j['diagnostic_input']=v.CANDIDATE if v.identity(self.raw)==v.DIAGNOSTIC else v.DIAGNOSTIC
        with self.assertRaises(ValueError):v.diagnose(self.raw,j,self.sources)
    def test_29_diagnose_rejects_unwitnessed_whole_rom_change(self):
        raw=bytearray(self.raw);raw[-1]^=1
        with self.assertRaises(ValueError):v.diagnose(raw,self.review,self.sources)
    def test_30_source_attribution_is_fixed(self):
        for field,value in [('commit','0'*40),('repository','other/project'),('source','src/other.c'),('url','https://example.com/wrong')]:
            with self.subTest(field=field):
                j=copy.deepcopy(self.review);j['source_bindings']['pret-party_menu.c'][field]=value
                with self.assertRaises(ValueError):self.check(review=j)
    def test_31_task_evidence_required(self):self.reject(lambda j:j.pop('task_evidence'))
    def test_32_task_evidence_cannot_claim_acceptance(self):self.reject(lambda j:j['task_evidence'].update(newly_classified=1))
