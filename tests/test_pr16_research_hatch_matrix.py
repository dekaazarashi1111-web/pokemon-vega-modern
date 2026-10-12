"""Only new matrix selection, inheritance and aggregation boundaries."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_hatch_matrix as m
NAMES=['research-egg-'+str(1200+i) for i in range(15)]
HEAD='a'*40
RUN=123
BIND={'size':1,'sha256':'b'*64}


def pair():
    base=dict(accepted={n:dict(old=n) for n in NAMES[:5]},candidate=copy.deepcopy(m.CANDIDATE),
              contracts={n:{'controller':'unchanged','fixture':n} for n in NAMES},
              protected_bindings={'protected':'same'},unit_binding={'unit':'same'},unit_origin=111)
    n=NAMES[5]
    w=copy.deepcopy(base)
    w.update(source_head=HEAD,run_id=RUN,matrix_case=n,matrix_input_checkpoint=BIND,
             status='PARTIAL_RESEARCH_HATCH',failures={},accepted_case_reruns=0,gift_reruns=0,
             rom_changes=0,arm_compiles=0,wiki_generations=0,new_unit_tests=0,native_processes=1,
             host_compiles=1,actions_completion_confirmed=False,issue19_complete=False,
             release_ready=False,active_baseline_changed=False,unit_passed=True)
    w['accepted'][n]=dict(run_id=RUN,source_head=HEAD,result={'status':'PASS'},contract=copy.deepcopy(base['contracts'][n]))
    return base,w,n


class MatrixTests(unittest.TestCase):
    def test_five_retained_ten_planned(self):
        b,_,_=pair();self.assertEqual(m.plan_cases(NAMES,b['accepted']),NAMES[5:])
    def test_completed_not_rerun(self):
        with self.assertRaises(ValueError):m.plan_cases(NAMES,dict.fromkeys(NAMES))
    def test_unknown_accepted(self):
        with self.assertRaises(ValueError):m.plan_cases(NAMES,{'unknown':{}})
    def test_duplicate_domain(self):
        with self.assertRaises(ValueError):m.plan_cases(NAMES[:-1]+[NAMES[0]],{})
    def test_malformed_domain(self):
        with self.assertRaises(ValueError):m.plan_cases(NAMES[:-1]+['../bad'],{})
    def test_one_pending_only(self):
        self.assertEqual(m.select_one(NAMES[5:],NAMES[9]),[NAMES[9]])
    def test_selection_rejects_accepted(self):
        with self.assertRaises(ValueError):m.select_one(NAMES[5:],NAMES[0])
    def test_duplicate_pending(self):
        with self.assertRaises(ValueError):m.select_one([NAMES[5]]*2,NAMES[5])
    def test_valid_merge_does_not_mutate_prefix(self):
        b,w,n=pair();before=copy.deepcopy(b);row=m.merge_one(b,w,n,HEAD,RUN,BIND)
        self.assertEqual(row,w['accepted'][n]);row.clear();self.assertEqual(b,before)
    def test_wrong_head(self):
        b,w,n=pair();w['source_head']='c'*40
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_wrong_run(self):
        b,w,n=pair();w['run_id']+=1
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_wrong_input(self):
        b,w,n=pair();w['matrix_input_checkpoint']={}
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_wrong_candidate(self):
        b,w,n=pair();w['candidate']={}
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_unit_rerun_is_rejected(self):
        b,w,n=pair();w['new_unit_tests']=32
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_inherited_unit_binding(self):
        b,w,n=pair();w['unit_binding']={}
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_controller_contract_change(self):
        b,w,n=pair();w['contracts'][n]['controller']='changed'
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_inherited_success_change(self):
        b,w,n=pair();w['accepted'][NAMES[0]]={}
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_extra_case_rejected(self):
        b,w,n=pair();w['accepted'][NAMES[6]]={}
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_missing_result_rejected(self):
        b,w,n=pair();del w['accepted'][n]
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_failure_not_success(self):
        b,w,n=pair();w['failures']={n:'failed'}
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_scope_is_not_promoted(self):
        b,w,n=pair();w['release_ready']=True
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_multiple_native_rejected(self):
        b,w,n=pair();w['native_processes']=2
        with self.assertRaises(ValueError):m.merge_one(b,w,n,HEAD,RUN,BIND)
    def test_case_proof_inventory(self):
        names=m.proof_names(NAMES[5]);self.assertEqual(len(names),10)
        self.assertIn(NAMES[5]+'.stdout.txt',names)
        self.assertNotIn(NAMES[0]+'.stdout.txt',names)


if __name__=='__main__':unittest.main()
