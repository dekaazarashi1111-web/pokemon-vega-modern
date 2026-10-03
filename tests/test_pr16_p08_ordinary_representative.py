"""通常callee/真正退出stateの拒否契約。合成traceはunit専用。"""
from pathlib import Path
import copy
import json
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_p08_ordinary_representative as m


def routes():
    return [dict(name='route'+str(i),root=0x090B667C+128*i,target=0x095D5874+128*i,
        normal=0x0953410C+128*i,suppressed=0x0953417C+128*i,preserve_r3=True) for i in range(29)]


def call_rows():
    r=routes()[0];common=dict(frame=4900,flags=0,types=0,host_writes=0,host_calls=0)
    return [dict(common,kind='predicate',bank=0,raw_ability=66,result=0,return_pc=0x095D5890,
        pcs=[0x090D7BB0,0x090D7BB2,0x095D5890]),
        dict(common,kind='dispatch',name=r['name'],root=r['root'],delegate=r['normal'],expected_normal=r['normal'],
        preserve_r3=True,r3_before=3,r3_after=3,pcs=[r['root'],r['target'],r['normal']])]


def sample():
    original=json.loads((m.ROOT/m.PRIOR).read_bytes())['events'][0]
    events=[]
    for label,frame in [('p08-exit30',2602),('p08-town-boundary',3500),('p08-normal-action',5000),('p08-normal-return',5500)]:
        event=copy.deepcopy(original);event.update(label=label,frame=frame)
        if label=='p08-normal-action':event['newbs']=0x02030000
        if label=='p08-normal-return':event['outcome']=4
        events.append(event)
    row=m.expected();row.update(predicate_returns=1,normal_dispatches=1,trace_frames=40,trace_instructions=100000,
        walking_steps=50,continued_frame=2602,boundary_frame=3500,encounter_frame=5000,returned_frame=5500,
        total_frames=5500,species=4,ability=66,enemy_species=730,enemy_level=75,outcome=4)
    return row,events,original


def trace(events,calls=None):
    calls=call_rows() if calls is None else calls
    return b''.join(b'P08_ORDINARY_CALL '+m.e.stable(x) .replace(b'\n',b'')+b'\n' for x in calls)+\
        b''.join(b'CIRCUS_CONTINUOUS '+json.dumps(x).encode()+b'\n' for x in events)


def verify(row,events,original,stderr=None,proc=None):
    return m.validate(m.e.stable(row),trace(events) if stderr is None else stderr,
        dict(returncode=0,timed_out=False,spawn_error=None) if proc is None else proc,dict(routes=routes()),original)


class OrdinaryTests(unittest.TestCase):
    def test_exact_ordinary_normal_calls(self):
        row,events,original=sample();self.assertEqual(verify(row,events,original)[0],row)
    def test_nonzero_suppression_rejected(self):
        for key,value in [('flags',0x80000000),('types',0x04000000),('result',1),('host_writes',1),('host_calls',1)]:
            with self.subTest(key=key):
                rows=call_rows();rows[0][key]=value
                with self.assertRaises(ValueError):m.calls_proof(rows,routes())
    def test_wrong_normal_delegate(self):
        rows=call_rows();rows[1]['delegate']=routes()[0]['suppressed']
        with self.assertRaises(ValueError):m.calls_proof(rows,routes())
    def test_corrupted_fourth_argument(self):
        rows=call_rows();rows[1]['r3_after']=4
        with self.assertRaises(ValueError):m.calls_proof(rows,routes())
    def test_missing_physical_dispatcher_chain(self):
        rows=call_rows();rows[1]['pcs'].pop(1)
        with self.assertRaises(ValueError):m.calls_proof(rows,routes())
    def test_missing_predicate_or_dispatch(self):
        for rows in (call_rows()[:1],call_rows()[1:],[]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):m.calls_proof(rows,routes())
    def test_unknown_call_or_extra_field(self):
        for key,value in [('kind','fake'),('unknown',1),('frame',False),('bank',2)]:
            with self.subTest(key=key):
                rows=call_rows();rows[0][key]=value
                with self.assertRaises(ValueError):m.calls_proof(rows,routes())
    def test_wrong_counts_and_replayed_prefix(self):
        for key,value in [('prefix_wins_reexecuted',30),('predicate_returns',0),('normal_dispatches',0),('fresh_cores',2),
            ('new_emulator_processes',True),('manual_saves',1),('release_ready',True),('host_state_injection',True),('outcome',7)]:
            with self.subTest(key=key):
                row,events,original=sample();row[key]=value
                with self.assertRaises(ValueError):verify(row,events,original)
    def test_failed_process(self):
        for key,value in [('returncode',1),('returncode',False),('timed_out',True),('spawn_error','bad')]:
            with self.subTest(key=key):
                row,events,original=sample();p=dict(returncode=0,timed_out=False,spawn_error=None);p[key]=value
                with self.assertRaises(ValueError):verify(row,events,original,proc=p)
    def test_original_exit_not_relabelled(self):
        row,events,original=sample();events[0]['bp']=99
        with self.assertRaises(ValueError):verify(row,events,original)
    def test_owner_and_factory_cannot_change(self):
        for key in ('owner','factory'):
            row,events,original=sample();events[-1][key]=f'{int(events[-1][key][:2],16)^1:02x}'+events[-1][key][2:]
            with self.subTest(key=key),self.assertRaises(ValueError):verify(row,events,original)
    def test_no_new_facility_draw_or_getter(self):
        for prefix in (b'CIRCUS_SUPPRESSION_DRAW ',b'CIRCUS_GETTER_ABI '):
            row,events,original=sample()
            with self.assertRaises(ValueError):verify(row,events,original,stderr=trace(events)+prefix+b'{}\n')
    def test_unknown_result_field_and_frame_order(self):
        for key,value in [('unknown',0),('continued_frame',6000),('returned_frame',4999)]:
            row,events,original=sample();row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):verify(row,events,original)
    def test_no_host_injection_in_new_main_or_observer(self):
        for path in (m.HEADER,m.OBSERVER):
            raw=(m.ROOT/path).read_bytes()
            for token in (b'write8(',b'write16(',b'write32(',b'call_preserving(',b'loadState',b'saveState',b'cf_open(',b'cf_rentals(',b'create_mon('):
                with self.subTest(path=path,token=token):self.assertNotIn(token,raw)
        raw=(m.ROOT/m.HEADER).read_text();self.assertLess(raw.index('a_guard(c)'),raw.index('b_continue(c)'))
    def test_source_adaptation_only_renames_unused_main(self):
        files={'controller.c':b'original\n','getter_suppression.h':b'int main(int argc,char **argv){return 0;}','other.h':b'unmodified'}
        result=m.adapt(files);self.assertEqual(result['other.h'],files['other.h']);self.assertEqual(files['controller.c'],b'original\n')
        self.assertIn(b'p08_unused_circus_lifecycle_main',result['getter_suppression.h'])
        with self.assertRaises(ValueError):m.adapt({'controller.c':b'','getter_suppression.h':b'fake'})
    def test_archive_requires_true_cache_provenance(self):
        original=json.loads((m.ROOT/m.GETTER).read_bytes())['original_failure']['normal_save30']
        wrong=copy.deepcopy(original);wrong['run_id']=0
        with self.assertRaises(ValueError):m.cache.validate_cache(wrong,b'not the private save',original)


if __name__=='__main__':unittest.main()
