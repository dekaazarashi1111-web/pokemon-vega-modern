"""陽性原本を毎回先に検証し、限定受入の過大主張/取り違えを拒否する。"""
import copy
import unittest
from scripts import pr16_research_standard_list_accept as a

class AcceptanceTests(unittest.TestCase):
    def inputs(self):
        root=a.ROOT/a.EVIDENCE
        return [a.read(root/(n+'.json')) for n in ('measurement','oracle','oracle-unit')]+[
            a.read(a.ROOT/a.REVIEW), a.terminal_fixture()]

    def test_saved_positive(self):
        result=a.validate(*self.inputs())
        self.assertTrue(result['standard_list_accepted'])
        self.assertEqual(result['new_native_processes'],0)
        self.assertFalse(result['naturally_earned_spending_accepted'])

    def reject(self,index,path,value):
        data=self.inputs()
        self.assertTrue(a.validate(*data)['standard_list_accepted'])
        data=copy.deepcopy(data);target=data[index]
        for key in path[:-1]:target=target[key]
        target[path[-1]]=value
        with self.assertRaises(ValueError):a.validate(*data)

CASES=[
 ('run_id',4,('run','id'),0),
 ('run_source',4,('run','head_sha'),'0'*40),
 ('run_pending',4,('run','status'),'in_progress'),
 ('run_failure',4,('run','conclusion'),'failure'),
 ('run_attempt',4,('run','run_attempt'),2),
 ('run_branch',4,('run','head_branch'),'main'),
 ('run_workflow',4,('run','path'),'.github/workflows/other.yml'),
 ('job_id',4,('job','id'),0),
 ('job_source',4,('job','head_sha'),'0'*40),
 ('job_failure',4,('job','conclusion'),'failure'),
 ('candidate',0,('candidate','sha256'),'0'*64),
 ('native_stderr',0,('stderr','size'),1),
 ('native_timeout',0,('timeout',),True),
 ('flash_changed',0,('flash_prefix_unchanged',),False),
 ('repeat_native',0,('counts','native_processes'),2),
 ('window_lifecycle',1,('single_task_and_window_lifecycle',),False),
 ('owner_changed',1,('all_owner_ledger_bag_party_flash_counter_unchanged',),False),
 ('raw_relabelled',1,('standard_list_accepted',),True),
 ('visits',1,('visits',),2),
 ('screens_incomplete',0,('screens',),{}),
 ('old_unit_count',2,('passed',),26),
 ('review_source',3,('source_head',),'0'*40),
 ('review_missing',3,('completed',),False),
 ('natural_overclaim',3,('naturally_earned_spending_accepted',),True),
]

def make_test(index,path,value):
    def test(self):self.reject(index,path,value)
    return test
for name,index,path,value in CASES:
    setattr(AcceptanceTests,'test_reject_'+name,make_test(index,path,value))

if __name__=='__main__':unittest.main()
