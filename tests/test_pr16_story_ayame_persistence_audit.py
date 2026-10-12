"""新規の保存領域監査だけ。旧55試験/native/ROM生成は呼ばない。"""
import copy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_ayame_persistence_audit as m


def sample_save():
    raw=bytearray(131088)
    for i in range(14):
        sid=(i+3)%14
        struct.pack_into('<HHII',raw,i*0x1000+0xff4,sid,0,0x08012025,18)
    return bytes(raw)


def states():
    fa=bytes(0x120); fb=bytearray(fa); va=[0]*256; vb=va.copy()
    for flag in (0x501,0x63d,0x63f): fb[flag//8]|=1<<(flag%8)
    for var,a,b in ((0x4021,93,5),(0x4022,1,2),(0x404d,0,8),(0x4071,1,3)):
        va[var-0x4000]=a;vb[var-0x4000]=b
    return (fa,va),(bytes(fb),vb)


def run_jobs():
    run=dict(id=m.RUN,head_sha=m.SOURCE,head_branch='codex/modernization-followup-20260908',
        path='.github/workflows/pr16-story-ayame.yml',status='completed',conclusion='success',run_attempt=1)
    job=dict(id=m.JOB,run_id=m.RUN,name='continuation',status='completed',conclusion='success',
        steps=[dict(name=n,status='completed',conclusion='success') for n in m.STEPS])
    return run,dict(total_count=1,jobs=[job])


def remap():
    rows=[(n,0) for n in range(370)]+[(0x9b0,0x63d),(0x9b3,0x63f)]
    return b''.join(struct.pack('<HH',*r) for r in rows)


class PersistenceTests(unittest.TestCase):
    def bank_bad(self,offset,data):
        raw=bytearray(sample_save());raw[offset:offset+len(data)]=data
        with self.assertRaises(ValueError):m.bank(bytes(raw),0,18,m.LAYOUT)

    def test_checksum_little_endian_words(self):
        self.assertEqual(m.checksum(struct.pack('<II',0x00010002,0x00030004)),10)
    def test_checksum_unsigned_wrap(self):
        self.assertEqual(m.checksum(struct.pack('<II',0xffffffff,1)),0)
    def test_checksum_final_16bit_fold(self):
        self.assertEqual(m.checksum(struct.pack('<I',0xffffffff)),65534)
    def test_checksum_empty_rejected(self):
        with self.assertRaises(ValueError):m.checksum(b'')
    def test_checksum_unaligned_rejected(self):
        with self.assertRaises(ValueError):m.checksum(b'\0'*5)
    def test_checksum_mutable_input_rejected(self):
        with self.assertRaises(ValueError):m.checksum(bytearray(4))
    def test_checksum_oversized_rejected(self):
        with self.assertRaises(ValueError):m.checksum(bytes(0x1000))
    def test_layout_exact(self):
        raw=b''.join(struct.pack('<HH',*r) for r in m.LAYOUT)
        self.assertEqual(m.layout_table(raw),m.LAYOUT)
    def test_layout_truncated_rejected(self):
        with self.assertRaises(ValueError):m.layout_table(bytes(55))
    def test_layout_s61e_is_not_pc_payload(self):
        raw=bytearray(b''.join(struct.pack('<HH',*r) for r in m.LAYOUT))
        struct.pack_into('<H',raw,54,0xff0)
        with self.assertRaises(ValueError):m.layout_table(bytes(raw))
    def test_rotated_sector_ids_and_full_coverage(self):
        table,report=m.bank(sample_save(),0,18,m.LAYOUT)
        self.assertEqual(table[3],0);self.assertEqual(len(report),14)
        self.assertEqual(sorted(table),list(range(14)))
    def test_bank_duplicate_sid_rejected(self):self.bank_bad(0xff4,struct.pack('<H',4))
    def test_bank_outside_sid_rejected(self):self.bank_bad(0xff4,struct.pack('<H',14))
    def test_bank_signature_rejected(self):self.bank_bad(0xff8,bytes(4))
    def test_bank_partial_generation_rejected(self):self.bank_bad(0xffc,struct.pack('<I',17))
    def test_bank_payload_corruption_rejected(self):self.bank_bad(0,b'\1')
    def test_bank_stored_checksum_corruption_rejected(self):self.bank_bad(0xff6,b'\1')
    def test_bank_boolean_counter_rejected(self):
        with self.assertRaises(ValueError):m.bank(sample_save(),0,True,m.LAYOUT)
    def test_bank_boolean_offset_rejected(self):
        with self.assertRaises(ValueError):m.bank(sample_save(),False,18,m.LAYOUT)
    def test_bank_truncated_rtc_rejected(self):
        with self.assertRaises(ValueError):m.bank(sample_save()[:-1],0,18,m.LAYOUT)
    def test_checksum_does_not_claim_uncovered_padding(self):
        raw=bytearray(sample_save());raw[0xff0]=1
        self.assertEqual(len(m.bank(bytes(raw),0,18,m.LAYOUT)[1]),14)
    def test_mapping_high_ids_and_low_fallback(self):
        self.assertEqual(m.trainer_mapping(remap()),[(1,1281,1281),(1200,2480,1597),(1203,2483,1599)])
    def test_mapping_truncated_rejected(self):
        with self.assertRaises(ValueError):m.trainer_mapping(remap()[:-1])
    def test_mapping_duplicate_rejected(self):
        raw=bytearray(remap());raw[4:8]=raw[:4]
        with self.assertRaises(ValueError):m.trainer_mapping(bytes(raw))
    def test_mapping_unsorted_rejected(self):
        raw=remap();raw=raw[4:8]+raw[:4]+raw[8:]
        with self.assertRaises(ValueError):m.trainer_mapping(raw)
    def test_mapping_wrong_physical_rejected(self):
        raw=bytearray(remap());struct.pack_into('<H',raw,len(raw)-2,0x9b3)
        with self.assertRaises(ValueError):m.trainer_mapping(bytes(raw))
    def test_state_progress_and_exact_flag_deltas(self):
        d=m.state_delta(*states());self.assertEqual(d['gate_var4071'],[1,3])
        self.assertEqual(d['national_var404e'],0)
    def test_state_missing_third_flag_rejected(self):
        old,new=states();fb=bytearray(new[0]);fb[0x63f//8]&=~(1<<(0x63f%8))
        with self.assertRaises(ValueError):m.state_delta(old,(bytes(fb),new[1]))
    def test_state_unknown_flag_rejected(self):
        old,new=states();fb=bytearray(new[0]);fb[0]|=1
        with self.assertRaises(ValueError):m.state_delta(old,(bytes(fb),new[1]))
    def test_state_gate_incomplete_rejected(self):
        old,new=states();new[1][0x71]=2
        with self.assertRaises(ValueError):m.state_delta(old,new)
    def test_state_later_story_injected_rejected(self):
        old,new=states();new[1][0x72]=9
        with self.assertRaises(ValueError):m.state_delta(old,new)
    def test_state_dex_var_injected_rejected(self):
        old,new=states();new[1][0x4e]=0x6258
        with self.assertRaises(ValueError):m.state_delta(old,new)
    def test_state_dex_flag_injected_rejected(self):
        old,new=states();fb=bytearray(new[0]);fb[0x840//8]|=1
        with self.assertRaises(ValueError):m.state_delta(old,(bytes(fb),new[1]))
    def test_state_boolean_rejected(self):
        old,new=states();old[1][0x71]=True
        with self.assertRaises(ValueError):m.state_delta(old,new)
    def test_terminal_all_steps_success(self):self.assertEqual(m.terminal(*run_jobs())['run']['id'],m.RUN)
    def test_terminal_failed_upload_rejected(self):
        run,jobs=run_jobs();jobs['jobs'][0]['steps'][4]['conclusion']='failure'
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_terminal_pending_post_rejected(self):
        run,jobs=run_jobs();jobs['jobs'][0]['steps'][5]['status']='in_progress'
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_terminal_missing_complete_rejected(self):
        run,jobs=run_jobs();jobs['jobs'][0]['steps'].pop()
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_terminal_other_head_rejected(self):
        run,jobs=run_jobs();run['head_sha']='d75466777ae1ee5835b6df61fe6121733a09b5c2'
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_terminal_second_attempt_rejected(self):
        run,jobs=run_jobs();run['run_attempt']=2
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_terminal_boolean_attempt_rejected(self):
        run,jobs=run_jobs();run['run_attempt']=True
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_terminal_incomplete_job_page_rejected(self):
        run,jobs=run_jobs();jobs['total_count']=2
        with self.assertRaises(ValueError):m.terminal(run,jobs)


if __name__ == '__main__':unittest.main()
