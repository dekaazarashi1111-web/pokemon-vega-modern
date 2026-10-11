"""中断のhost契約。合成した復旧行をnativeの観測として扱わない。"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/('pr16_circus_'+name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=module('interruption_probe');m=module('interruption')
EVIDENCE='evidence/pr16_circus_three_win/35418424222/circus-streak-batch-save.stderr'

def crc_owner(raw,**changes):
    data=bytearray.fromhex(raw)
    widths=dict(generation=(16,'I'),session=(20,'I'),prepared=(24,'I'),settled=(28,'I'),
        current=(32,'H'),best=(34,'H'),phase=(36,'B'),outcome=(38,'B'))
    for key,value in changes.items():offset,fmt=widths[key];struct.pack_into('<'+fmt,data,offset,value)
    data[12:16]=bytes(4);struct.pack_into('<I',data,12,zlib.crc32(data)&0xffffffff)
    return data.hex()

def fixture():
    # 最初8行は実観測済み。3つの復旧行はこのhost test専用の合成。
    rows=[json.loads(line[14:]) for line in (ROOT/EVIDENCE).read_text().splitlines() if line.startswith('CIRCUS_STREAK ')][:8]
    expected=crc_owner(rows[-1]['owner'],phase=0,current=0,settled=2,outcome=3,generation=6)
    for name,frame,counter in [('recovered',27000,2),('saved',29000,3),('reloaded',32000,3)]:
        rows.append(dict(rows[0],label=name,frame=frame,battle=2,save_counter=counter,owner=expected))
    result=dict(schema_version=1,status='PASS_CIRCUS_INTERRUPTION_NATIVE',case=p.CASE,candidate_sha256=p.SHA,
        wins=1,losses=0,battles_started=2,battles_finished=1,interruptions=1,
        save_counter_before=2,save_counter_after=3,manual_saves=1,fresh_cores=3,
        owner_bytes_verified=64,party_bytes_verified=600,host_write_barriers=7,events=11,
        input_only_after_guard=True,physical_admission_accepted=False,suppression_accepted=False,
        release_ready=False,warnings_errors=0,turns=17,switches=1,forced_identity_checks=1,total_frames=32000)
    return rows,result

def stderr(rows):return ''.join('CIRCUS_STREAK '+json.dumps(row)+'\n' for row in rows).encode()
def validate(rows,result):return p.validate(json.dumps(result).encode(),stderr(rows),0,p.CASE)

class InterruptionTests(unittest.TestCase):
    def test_synthetic_host_contract_only(self):
        rows,result=fixture();self.assertEqual(validate(rows,result),result)
        s=p.analyze(p.parse(stderr(rows)),result)
        self.assertEqual((s['real_wins_before_interruption'],s['current_after'],s['best_after'],s['fresh_cores']),(1,0,1,3))
        self.assertFalse(s['physical_admission_accepted'])
    def test_crc_rejected(self):
        rows,result=fixture();raw=bytearray.fromhex(rows[8]['owner']);raw[32]=1;rows[8]['owner']=raw.hex()
        with self.assertRaises(ValueError):validate(rows,result)
    def test_crc_valid_wrong_abort_semantics_rejected(self):
        for key,value in [('current',1),('best',2),('outcome',1),('settled',1),('prepared',3),('phase',1),('generation',7),('session',2)]:
            with self.subTest(key=key):
                rows,result=fixture()
                for row in rows[8:]:row['owner']=crc_owner(row['owner'],**{key:value})
                with self.assertRaises(ValueError):validate(rows,result)
    def test_double_recovery_rejected(self):
        rows,result=fixture();rows[-1]['owner']=crc_owner(rows[-1]['owner'],generation=7)
        with self.assertRaises(ValueError):validate(rows,result)
    def test_exact_result_scope_and_types(self):
        for key,value in [('wins',2),('losses',1),('fresh_cores',2),('battles_finished',2),('interruptions',True),
                          ('physical_admission_accepted',True),('suppression_accepted',True),('release_ready',True),
                          ('warnings_errors',1),('host_write_barriers',6),('extra',0)]:
            with self.subTest(key=key):
                rows,result=fixture();result[key]=value
                with self.assertRaises(ValueError):validate(rows,result)
    def test_counters_and_order(self):
        for i,key,value in [(8,'bp',9),(8,'save_counter',3),(7,'save_counter',3),(9,'save_counter',2),
                            (10,'frame',31999),(6,'battle',0),(8,'snapshot',1),(8,'pending',1),(8,'marker',2),
                            (7,'script',0),(0,'frame',True),(8,'extra',0)]:
            with self.subTest(i=i,key=key):
                rows,result=fixture();rows[i][key]=value
                with self.assertRaises(ValueError):validate(rows,result)
    def test_party_and_factory_restore(self):
        for i,key in [(8,'party'),(10,'party'),(5,'factory'),(9,'factory')]:
            rows,result=fixture();raw=bytearray.fromhex(rows[i][key]);raw[-1]^=1;rows[i][key]=raw.hex()
            with self.assertRaises(ValueError):validate(rows,result)
    def test_second_launch_individual_replacement(self):
        rows,result=fixture()
        for i in (6,7):
            raw=bytearray.fromhex(rows[i]['party']);raw[0]^=1;rows[i]['party']=raw.hex()
        with self.assertRaises(ValueError):validate(rows,result)
    def test_real_win_required(self):
        rows,result=fixture();rows[4]['outcome']=2
        with self.assertRaises(ValueError):validate(rows,result)
    def test_event_count_and_monotonic_frames(self):
        rows,result=fixture()
        for value in (rows[:-1],rows+rows[-1:],rows[:8]+list(reversed(rows[8:]))):
            with self.assertRaises(ValueError):validate(value,result)
    def test_duplicate_json_and_diagnostics(self):
        with self.assertRaises(ValueError):p.strict('{"wins":1,"wins":2}')
        with self.assertRaises(ValueError):p.strict('{"x":NaN}')
        rows,_=fixture()
        with self.assertRaises(ValueError):p.parse(b'mGBA[error]\n'+stderr(rows))
    def test_process_code_and_identity(self):
        rows,result=fixture()
        for code,case in ((1,p.CASE),(False,p.CASE),(0,'circus-streak-batch-save')):
            with self.assertRaises(ValueError):p.validate(json.dumps(result).encode(),stderr(rows),code,case)
    def test_bounded_runner_adaptation(self):
        source="scope='CIRCUS_DEDICATED_STREAK_BATCH_SAVE_NATIVE'\n            generated['controller.c']=(ROOT/SOURCE).read_text()"
        changed=m.adapt_runner(source)
        self.assertIn("scope='CIRCUS_SECOND_BATTLE_INTERRUPTION_NATIVE'",changed)
        self.assertIn("m.embed((ROOT/BASE_SOURCE).read_text(),'interrupt_unexecuted_batch')",changed)
        for bad in ('',source+source,changed):
            with self.assertRaises(ValueError):m.adapt_runner(bad)
        text='native_processes=1,fresh_cores=2,accepted_native_cases_replayed=0,'
        self.assertIn('fresh_cores=3',m.adapt_summary(text))
        for bad in ('',text+text,m.adapt_summary(text)):
            with self.assertRaises(ValueError):m.adapt_summary(bad)
    def test_read_only_after_first_guard(self):
        source=(ROOT/m.SOURCE).read_text()
        active=source.split('a_guard(c);',1)[1]
        for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'create_mon(', 'loadState(', 'saveState('):
            self.assertNotIn(forbidden,active)
        self.assertEqual(source.count('b_restart(c,argv[1],argv[2])'),2)
        self.assertEqual(source.count('b_save(c)'),1)
        self.assertIn('sc_finish_battle(c,0U)==1U',source)
        self.assertNotIn('#define main',source)
if __name__=='__main__':unittest.main()
