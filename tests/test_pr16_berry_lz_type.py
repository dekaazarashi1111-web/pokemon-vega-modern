"""新しい単一LZ型差分の人工試験。既存native/reader試験は実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_berry_lz_type as m


def fixture():
    rows = []
    for i in range(86):
        hit = dict(address=m.HIT+i*16, target=0x09FED200+i, size=4,
            sha256=m.HIT_ID['sha256'] if i==0 else '0'*64,
            classification='UNCLASSIFIED', accepted=False, kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS')
        rows.append(dict(hit=hit,owners=['example'] if i%2 else [],context=dict(index=i)))
    chain = dict(candidate=m.lz.CANDIDATE, classified=788, unclassified=86, donor_safe_bytes=0)
    front = dict(candidate=m.lz.CANDIDATE,total=86,rows=rows,owner_unknown=43,unowned_unknown=43)
    window = dict(remaining_count=7,remaining_rows=[copy.deepcopy(r['hit']) for r in rows[:7]],
        formal_classified=788,formal_unclassified=86,selected_range=m.RANGE,donor_safe_bytes=0,
        newly_classified_addresses=[123],retirement_or_transfer_complete=False)
    roles = [dict(source_address=m.lz.TARGET+i,size=2,kind='backreference',
        rom_address=m.HIT+i,target_byte_indexes=[i,i+1],sha256='a'*64) for i in (0,2)]
    parsed = dict(source_start=m.lz.STREAM,source_end_exclusive=m.lz.STREAM+2000,
        consumed_bytes=2000,output={'size':5000},target_byte_indexes=[0,1,2,3],target_roles=roles)
    native = dict(schema_version=1,native_processes=1,child_header_boots=0,
        entry=m.lz.CHILD+0x120,stop_pc=m.lz.CHILD+0x1D8,swi11_count=1,
        sio_fixture_transactions=8,sio_fixture_reads=32,host_write_guards=7,
        host_writes_after_entry=0,target_read_mask=15,mapped_bytes=m.lz.SIZE,
        payload_read_first=m.lz.STREAM,payload_read_end_exclusive=m.lz.STREAM+2000,
        payload_read_bytes=2000,payload_read_unique=2000,payload_read_max_count=1,
        output_write_bytes=5000,output_size=5000,steps=200,
        status='CONDITIONAL_LZ_READER_OBSERVED',stop_reason='RETURNED_FROM_SWI11',
        natural_link_transfer_proven=False,original_bios_cpu_execution_claimed=False,
        formal_rom_changed=False,formal_save_changed=False,full_emulator_checkpoint_restored=False,
        sio_reads_are_fixture=True,all_issued_code_equal_source=True,
        all_payload_reads_equal_source=True,output_writes_sequential=True,
        issued_spans=[{'address':m.lz.CHILD+x,'visits':1} for x in (0x120,0x144,0x1CC,0x1D0,0x1D4)],
        native_diagnostics=dict(fatal=0,error=0,warn=0,info=0,debug=2,stub=0,game_error=0))
    proof = dict(status='CONDITIONAL_LZ_READER_OBSERVED',classification_candidate='CONDITIONAL_LZ77_SOURCE_TOKEN',
        candidate=m.lz.CANDIDATE,mapped_image=m.lz.IMAGE,formal_classification_changes=0,donor_safe_bytes=0,
        reader=parsed,native=native)
    measurement = dict(actions_run_id=44,source_head='a'*40,candidate=m.lz.CANDIDATE)
    receipt = dict(measurement_run_id=44,measurement_source_head='a'*40,measurement_completion_confirmed=True,
        status='LZ_READER_COMPLETION_BOUND_FORMAL_DELTA_PENDING')
    accepted = dict(id=44,source_head='a'*40,status='completed',conclusion='success')
    return copy.deepcopy([chain,front,window,proof,measurement,receipt,accepted])


class TypeDeltaTests(unittest.TestCase):
    def setUp(self): self.args=fixture()
    def apply(self): return m.promote(*self.args)
    def reject(self):
        with self.assertRaises(ValueError): self.apply()
    def test_counts(self):
        c,f,w=self.apply()
        self.assertEqual((c['classified'],c['unclassified'],f['total'],w['remaining_count']),(789,85,85,6))
        self.assertEqual(c['changes'][0]['classification'],m.CLASSIFICATION)
    def test_read_only(self):
        before=m.encode(self.args);self.apply();self.assertEqual(before,m.encode(self.args))
    def test_deterministic(self): self.assertEqual(self.apply(),self.apply())
    def test_other_rows_identical(self):
        _,f,w=self.apply()
        self.assertEqual(f['rows'],self.args[1]['rows'][1:]);self.assertEqual(w['remaining_rows'],self.args[2]['remaining_rows'][1:])
    def test_no_capacity_promotion(self):
        c,f,w=self.apply()
        self.assertEqual(c['classified']+c['unclassified'],874)
        self.assertEqual(w['donor_safe_bytes'],0);self.assertFalse(c['claims']['donor_eligible'])
        self.assertFalse(c['claims']['natural_link_transfer_proven'])
    def test_wrong_candidate(self): self.args[0]['candidate']['sha256']='b'*64;self.reject()
    def test_old_counts_required(self): self.args[0]['classified']=789;self.reject()
    def test_duplicate_unknown(self): self.args[1]['rows'][1]=self.args[1]['rows'][0];self.reject()
    def test_missing_hit(self): self.args[1]['rows'][0]['hit']['address']-=1;self.reject()
    def test_wrong_hit_identity(self):
        self.args[1]['rows'][0]['hit']['sha256']='b'*64;self.args[2]['remaining_rows'][0]['sha256']='b'*64;self.reject()
    def test_already_accepted(self):
        self.args[1]['rows'][0]['hit']['accepted']=True;self.args[2]['remaining_rows'][0]['accepted']=True;self.reject()
    def test_disagreeing_selected_hit(self): self.args[2]['remaining_rows'][0]['target']+=1;self.reject()
    def test_wrong_window(self): self.args[2]['selected_range']['size']-=4;self.reject()
    def test_unfinished_run(self): self.args[6]['status']='in_progress';self.reject()
    def test_wrong_run(self): self.args[6]['id']+=1;self.reject()
    def test_wrong_source(self): self.args[6]['source_head']='b'*40;self.reject()
    def test_unreceived(self): self.args[5]['measurement_completion_confirmed']=False;self.reject()
    def test_partial_token(self): self.args[3]['reader']['target_roles'].pop();self.reject()
    def test_duplicate_token(self): self.args[3]['reader']['target_roles'].append(self.args[3]['reader']['target_roles'][0]);self.reject()
    def test_wrong_token_width(self): self.args[3]['reader']['target_roles'][0]['size']=3;self.reject()
    def test_wrong_rom_mapping(self): self.args[3]['reader']['target_roles'][0]['rom_address']+=1;self.reject()
    def test_wrong_native_count(self): self.args[3]['native']['payload_read_unique']-=1;self.reject()
    def test_native_warning(self): self.args[3]['native']['native_diagnostics']['warn']=1;self.reject()
    def test_natural_transfer_claim(self): self.args[3]['native']['natural_link_transfer_proven']=True;self.reject()
    def test_scope_broadened(self): self.args[3]['donor_safe_bytes']=4;self.reject()


if __name__=='__main__': unittest.main()
