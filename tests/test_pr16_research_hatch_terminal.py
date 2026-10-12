"""New terminal cohort/critical-job gates; never run old suites or emulator."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_hatch_terminal as t
NAMES = ['research-egg-'+str(1200+i) for i in range(15)]
HEAD = 'a'*40
RUN = 123


def cohort():
    contracts = {n: {'controller': 'same', 'fixture': n} for n in NAMES}
    rows = {n: dict(result={'status': 'PASS'}, contract=contracts[n], source_head=HEAD, run_id=RUN) for n in NAMES}
    return dict(status='PASS_RESEARCH_HATCH_SCOPED', accepted=rows, contracts=contracts,
        failures={}, pending_cases=[], unresolved_worker_attempts=[],
        actions_completion_confirmed=False, issue19_complete=False, release_ready=False,
        active_baseline_changed=False, accepted_case_reruns=0, gift_reruns=0, arm_compiles=0,
        rom_changes=0, wiki_generations=0, native_processes=10, host_compiles=10,
        new_unit_tests=23, matrix={'worker_artifacts': dict.fromkeys(NAMES[5:])},
        source_head=HEAD, run_id=RUN)


def jobs():
    names = ['plan', 'collect']+['hatch / '+n for n in NAMES[5:]]
    result = []
    for i, name in enumerate(names):
        steps = [dict(number=j+1, name=s, status='completed', conclusion='success')
                 for j, s in enumerate(t.CRITICAL.get(name, (t.NATIVE_STEP,)))]
        result.append(dict(id=100+i, name=name, run_id=RUN, head_sha=HEAD,
                           status='completed', conclusion='success', steps=steps))
    return dict(total_count=12, jobs=result), names


class TerminalTests(unittest.TestCase):
    def test_complete_cohort(self):
        v=cohort();before=copy.deepcopy(v)
        self.assertEqual(t.cohort(v,NAMES,NAMES[:5]),NAMES[5:]);self.assertEqual(v,before)
    def test_incomplete_cohort(self):
        v=cohort();v['accepted'].pop(NAMES[-1])
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_duplicate_domain(self):
        with self.assertRaises(ValueError):t.cohort(cohort(),NAMES[:-1]+[NAMES[0]],NAMES[:5])
    def test_wrong_partition(self):
        v=cohort();v['matrix']['worker_artifacts'].pop(NAMES[-1])
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_unresolved_case_not_promoted(self):
        v=cohort();v['unresolved_worker_attempts']=[NAMES[-1]]
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_failure_not_promoted(self):
        v=cohort();v['failures']={NAMES[-1]:'failure'}
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_release_not_promoted(self):
        v=cohort();v['release_ready']=True
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_already_complete_no_repeat(self):
        v=cohort();v['actions_completion_confirmed']=True
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_rerun_rejected(self):
        v=cohort();v['accepted_case_reruns']=1
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_worker_wrong_origin(self):
        v=cohort();v['accepted'][NAMES[5]]['run_id']=99
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_case_contract(self):
        v=cohort();v['accepted'][NAMES[5]]['contract']={}
        with self.assertRaises(ValueError):t.cohort(v,NAMES,NAMES[:5])
    def test_complete_twelve_jobs(self):
        v,n=jobs();self.assertEqual(len(t.terminal_jobs(v,n,HEAD,RUN)),12)
    def test_paginated_jobs(self):
        v,n=jobs();v['total_count']=13
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_duplicate_job(self):
        v,n=jobs();v['jobs'][-1]['name']=v['jobs'][-2]['name']
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_in_progress_job(self):
        v,n=jobs();v['jobs'][2]['status']='in_progress'
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_failed_job(self):
        v,n=jobs();v['jobs'][2]['conclusion']='failure'
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_wrong_job_head(self):
        v,n=jobs();v['jobs'][2]['head_sha']='b'*40
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_critical_save_skipped(self):
        v,n=jobs();v['jobs'][1]['steps'][-1]['conclusion']='skipped'
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_native_skipped(self):
        v,n=jobs();v['jobs'][2]['steps'][0]['conclusion']='skipped'
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_missing_native_step(self):
        v,n=jobs();v['jobs'][2]['steps'][0]['name']='different action'
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_duplicate_step_numbers(self):
        v,n=jobs();v['jobs'][1]['steps'][1]['number']=1
        with self.assertRaises(ValueError):t.terminal_jobs(v,n,HEAD,RUN)
    def test_no_old_complete_or_native_execution(self):
        text=(t.ROOT/t.SELF).read_text()
        for call in ('r.execute(', 'r.complete(', 'm.worker(', 'm.collect(', "'cc'", 'loadROM('):
            self.assertNotIn(call,text)


if __name__ == '__main__':unittest.main()
