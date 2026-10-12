"""新候補1件のスキーマ・保存byte・観測だけの追加を検証。合成値はunit専用。"""
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_p08_memory_representative as m


def sample():
    row=m.validator(m.TARGET['sha256']).expected_result(m.case())
    row['witness']=dict(bag=138,mode_menu=566,mode_choice=566,party=671,list=797,ask=927,
        delete_ask=1021,summary=1147,selection=1226,replaced=1287,learned=1409,giveup=0,denied=0,field=1736)
    trace=b'original core destroyed; new core normal Continue\n'
    for label,counter in [('learned',2),('saved',3),('reloaded',3)]:
        trace+=f'P08_MEMORY_BYTES label={label} counter={counter} size=100 hex={"01"*100}\n'.encode()
    return row,trace,dict(returncode=0,timed_out=False,spawn_error=None)


class MemoryTests(unittest.TestCase):
    def test_representative_expected_semantics(self):
        row,trace,proc=sample();self.assertEqual(m.validate(m.e.stable(row),trace,proc),row)
    def test_distinct_candidate_required(self):
        row,trace,proc=sample();row['rom_sha256']=m.PARENT_SHA
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_complete_party_byte_proof(self):
        row,trace,proc=sample();trace=trace.replace(b'label=reloaded counter=3 size=100 hex=01',b'label=reloaded counter=3 size=100 hex=02')
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_three_stages_required(self):
        row,trace,proc=sample();trace=b'\n'.join(x for x in trace.split(b'\n') if b'label=saved ' not in x)
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_duplicate_stage_rejected(self):
        row,trace,proc=sample();trace+=trace.splitlines()[-1]+b'\n'
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_save_counter_does_not_jump(self):
        row,trace,proc=sample();trace=trace.replace(b'counter=3',b'counter=4')
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_fresh_core_trace_required(self):
        row,trace,proc=sample();trace=trace.replace(b'original core destroyed; new core normal Continue\n',b'')
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_bad_process(self):
        for key,value in [('returncode',1),('returncode',False),('timed_out',True),('spawn_error','failed')]:
            with self.subTest(key=key):
                row,trace,proc=sample();proc[key]=value
                with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_rejects_missing_or_unknown_result(self):
        for missing in (False,True):
            row,trace,proc=sample()
            if missing:del row['mode_reset']
            else:row['extra']=True
            with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_rejects_pp_barrier_release_changes(self):
        for key,value in [('pp_after',[7,20,10,10]),('host_write_barriers',2),('core_instances',1),('release_ready',True),('full_p03_acceptance',True)]:
            with self.subTest(key=key):
                row,trace,proc=sample();row[key]=value
                with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_memory_input_order_required(self):
        row,trace,proc=sample();row['witness']['replaced']=0
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_pinned_case_is_single_full_slot(self):
        case=m.case();self.assertEqual(case['name'],'taillow-memory-full');self.assertEqual(case['after'],[33,457,45,52])
        pool=[33,45,64,116,98,17,457]
        self.assertEqual(m.old.make_case((m.CASE,10,13,0,0,1,457),pool,20),case)
    def test_source_preserves_three_barriers_and_readbacks(self):
        raw=(m.ROOT/m.old.PARENT_C).read_bytes().replace(b'c->setVideoBuffer(c,video,240);',b'c->setVideoBuffer(c,video,240);c->reset(c);')
        result=m.adapt(raw,(m.ROOT/m.HEADER).read_bytes())
        self.assertEqual(raw.count(b'a_guard(c)'),result.count(b'a_guard(c)'))
        self.assertEqual(raw.count(b'r_slots(c,v,true)'),result.count(b'r_slots(c,v,true)'))
        self.assertEqual(raw.count(b'a_continue(c)'),result.count(b'a_continue(c)'))
        self.assertIn(b'if(argc!=7)return 2;',result)
    def test_added_observer_has_no_game_state_writes(self):
        raw=(m.ROOT/m.HEADER).read_bytes()
        for token in (b'write8(',b'write16(',b'write32(',b'call_preserving(',b'saveState',b'loadState',b'->setKeys(',b'->runFrame('):
            with self.subTest(token=token):self.assertNotIn(token,raw)
        self.assertEqual(raw.count(b'p08_memory_original_frame(c);'),1)
    def test_wrong_driver_anchor(self):
        with self.assertRaises(ValueError):m.adapt(b'fake',b'fake')
    def test_not_full_rom_or_unbound_identity(self):
        with self.assertRaises(ValueError):m.physical_case(b'not a ROM')


if __name__=='__main__':unittest.main()
