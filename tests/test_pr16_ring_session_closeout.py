"""今回集計の不整合とnative受入誤昇格を拒否する。既読ABIは実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_session_closeout as m


def fixture():
    common={'candidate':copy.deepcopy(m.s.CANDIDATE),'old_unread_targets':list(range(18)),
            **{k:0 for k in m.ZERO_KEYS},**{k:False for k in m.FALSE_KEYS}}
    a={**copy.deepcopy(common),'target':0x08113984,'references':[],'candidate_reconstructions':1,
       'new_window_bytes':3326,'saved_bytes_reused':622}
    b={**copy.deepcopy(common),'candidate_reconstructions':0,
       'unread_external_targets':[0x0912C4A9,0x0912C555,0x09099E05],
       'counts':dict(zip(m.VECTOR_KEYS,(2584,256,256,256,3072,1767))),
       'readers':{'physical_hardware_behavior_proven':False,'supplied_io_stream_only':True},
       'date_validator':{'all_months_or_leap_years_proven':False}}
    return a,b


def jobs():
    return {'total_count':7,'jobs':[{'id':i,'name':f'domain ({i})','status':'completed','conclusion':'success',
            'steps':[{'name':'domainをmGBAで実行','conclusion':'skipped'}]} for i in range(7)]}


class Closeout(unittest.TestCase):
    def test_expected_totals(self):
        t=m.totals(*fixture());self.assertEqual(t['bounded_delegate_vectors'],8191)
        self.assertEqual(t['new_implementation_tests'],66);self.assertEqual(t['candidate_reconstructions'],1)
    def test_pure_inputs(self):
        pair=fixture();before=copy.deepcopy(pair);m.totals(*pair);self.assertEqual(pair,before)
    def test_candidate_mismatch(self):
        for i in range(2):
            pair=fixture();pair[i]['candidate']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'candidate'):m.totals(*pair)
    def test_replay_or_changes_rejected(self):
        for key in m.ZERO_KEYS:
            for i in range(2):
                pair=fixture();pair[i][key]=1
                with self.assertRaises(ValueError):m.totals(*pair)
    def test_boolean_zero_rejected(self):
        pair=fixture();pair[0]['rom_changes']=False
        with self.assertRaises(ValueError):m.totals(*pair)
    def test_acceptance_absence_rejected(self):
        for key in m.FALSE_KEYS:
            pair=fixture();pair[1][key]=True
            with self.assertRaisesRegex(ValueError,'overclaim'):m.totals(*pair)
    def test_reconstruction_mismatch(self):
        for i,v in ((0,0),(1,1)):
            pair=fixture();pair[i]['candidate_reconstructions']=v
            with self.assertRaises(ValueError):m.totals(*pair)
    def test_frontier_not_dropped(self):
        pair=fixture();pair[1]['old_unread_targets'].pop()
        with self.assertRaisesRegex(ValueError,'frontier'):m.totals(*pair)
    def test_duplicate_old_targets(self):
        pair=fixture()
        for obj in pair:obj['old_unread_targets']=[1]*18
        with self.assertRaisesRegex(ValueError,'frontier'):m.totals(*pair)
    def test_unread_delegate_mismatch(self):
        pair=fixture();pair[1]['unread_external_targets'].pop()
        with self.assertRaisesRegex(ValueError,'delegates'):m.totals(*pair)
    def test_reference_boundary_mismatch(self):
        for key,value in (('target',0x08113988),('references',[1])):
            pair=fixture();pair[0][key]=value
            with self.assertRaises(ValueError):m.totals(*pair)
    def test_sample_counts_mismatch(self):
        for key in ('new_window_bytes','saved_bytes_reused'):
            pair=fixture();pair[0][key]+=1
            with self.assertRaises(ValueError):m.totals(*pair)
    def test_vector_counts_mismatch(self):
        for key in m.VECTOR_KEYS:
            pair=fixture();pair[1]['counts'][key]+=1
            with self.assertRaises(ValueError):m.totals(*pair)
    def test_model_not_hardware(self):
        pair=fixture();pair[1]['readers']['physical_hardware_behavior_proven']=True
        with self.assertRaisesRegex(ValueError,'model'):m.totals(*pair)
    def test_seven_cached_domains(self):
        j=jobs();self.assertEqual(len(m.verify_cached_jobs(j)),7)
        j['jobs'].append({'name':'plan'});j['total_count']+=1
        self.assertEqual(len(m.verify_cached_jobs(j)),7)
    def test_native_replay_rejected(self):
        j=jobs();j['jobs'][0]['steps'][0]['conclusion']='success'
        with self.assertRaisesRegex(ValueError,'native replay'):m.verify_cached_jobs(j)
    def test_domain_failure_or_missing(self):
        for mutate in (lambda j:j['jobs'][0].update(conclusion='failure'),
                       lambda j:j['jobs'][0]['steps'].clear(),
                       lambda j:j['jobs'][0].update(name='plan')):
            j=jobs();mutate(j)
            with self.assertRaises(ValueError):m.verify_cached_jobs(j)
    def test_pagination_rejected(self):
        j=jobs();j['total_count']=101
        with self.assertRaisesRegex(ValueError,'pagination'):m.verify_cached_jobs(j)


if __name__=='__main__':unittest.main()
