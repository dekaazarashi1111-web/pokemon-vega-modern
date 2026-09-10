"""Original-byte and mutation checks; synthetic metadata is only a unit fixture."""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import record_modernization_p03_forgetting as record

class ForgettingEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=(ROOT/record.DIRECTORY/'original.zip').read_bytes()
        cls.original=record.members(cls.data)

    def test_original_native_outputs_revalidate(self):
        r=record.validate_files(self.original)
        self.assertEqual(len(r['cases']),12)
        self.assertEqual(r['rom']['sha256'],record.CHILD_SHA)
        self.assertFalse(r['release_ready'])

    def test_recursive_exact_types(self):
        self.assertFalse(record.same({'a':[1]},{'a':[True]}))
        self.assertFalse(record.same({'a':1},{'a':1.0}))
        self.assertFalse(record.same([1],[1,2]))
        self.assertTrue(record.same({'a':[None,False,1]},{'a':[None,False,1]}))

    def test_missing_member_or_extra_payload_rejected(self):
        f=dict(self.original);del f['tests.log']
        with self.assertRaises(ValueError):record.validate_files(f)
        f=dict(self.original);f['candidate.gba']=b'not a ROM'
        with self.assertRaises(ValueError):record.validate_files(f)

    def test_every_native_process_must_succeed(self):
        for c in record.suite.cases():
            f=dict(self.original);n=c['name']+'.process.json';p=record.load(f[n]);p['returncode']=1;f[n]=json.dumps(p).encode()
            with self.subTest(case=c['name']),self.assertRaises(ValueError):record.validate_files(f)

    def test_every_native_output_digest_is_bound(self):
        for c in record.suite.cases():
            f=dict(self.original);f[c['name']+'.stderr']+=b'changed\n'
            with self.subTest(case=c['name']),self.assertRaises(ValueError):record.validate_files(f)

    def test_no_lost_guards_or_defect_control(self):
        for n in ('parent-negative',*('guard-'+a for a in record.suite.GUARDS)):
            f=dict(self.original);f[n+'.stderr']=b''
            with self.subTest(prefix=n),self.assertRaises(ValueError):record.validate_files(f)

    def test_no_stage_or_phase_relabelling(self):
        for key,value in [('candidate_stage',83),('full_p03_acceptance',True),('full_p05_acceptance',True),('release_ready',True),('cache_reuse',1),('full_matrix',False),('core_instances',True)]:
            f=dict(self.original);r=record.load(f['result.json']);r[key]=value;f['result.json']=json.dumps(r).encode()
            with self.subTest(key=key),self.assertRaises(ValueError):record.validate_files(f)

    def test_recipe_and_matrix_bound_to_original(self):
        for name in ('candidate.json','matrix-outcomes.json'):
            f=dict(self.original);f[name]=b'{}'
            with self.subTest(name=name),self.assertRaises(ValueError):record.validate_files(f)

    def test_fixed_toolchain_and_unit_receipts_required(self):
        for name in ('fixed-toolchain.stdout','tests.log','job.stdout.log'):
            f=dict(self.original);f[name]=b'{}'
            with self.assertRaises(ValueError):record.validate_files(f)
        f=dict(self.original);f['compile.stderr']=b'warning\n'
        with self.assertRaises(ValueError):record.validate_files(f)

    def test_source_closure_cannot_drop_dependencies(self):
        with self.assertRaises(ValueError):record.bindings({'source_bindings':{}},ROOT)

    def test_unsafe_archive_layout(self):
        for bad in ('../outside.txt','/absolute.txt','dir/member.txt','back\\slash.txt'):
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:
                for i in range(77):z.writestr(str(i)+'.txt','')
                z.writestr(bad,'')
            with self.subTest(bad=bad),self.assertRaises(ValueError):record.members(out.getvalue())

    def test_metadata_contract_mutations(self):
        run=dict(id=record.RUN,head_sha=record.HEAD,head_branch=record.BRANCH,event='push',run_attempt=1,path=record.WORKFLOW,status='completed',conclusion='success',repository=dict(id=1358127462,full_name=record.REPO),head_repository=dict(id=1358127462,full_name=record.REPO))
        job=dict(run_id=record.RUN,head_sha=record.HEAD,name='remaining-routes',status='completed',conclusion='success',steps=[dict(name=n,status='completed',conclusion='success') for n in ('Fixed toolchain','Fail-closed result and input regressions','Reconstruct exact Stage83 without changing accepted baseline','New native forgetting routes, physical write guards and two-core saves','Run actions/upload-artifact@v4')])
        jobs=dict(total_count=1,jobs=[job])
        artifact=dict(id=record.ARTIFACT,name='p03-p05-remaining-routes',size_in_bytes=86028,digest='sha256:'+record.ZIP_SHA,workflow_run=dict(id=record.RUN,head_sha=record.HEAD,head_branch=record.BRANCH,repository_id=1358127462,head_repository_id=1358127462))
        record.metadata(run,jobs,artifact,self.data)
        for index,obj in enumerate((run,jobs,artifact)):
            for key in obj:
                values=copy.deepcopy([run,jobs,artifact]);values[index][key]=None
                with self.subTest(index=index,key=key),self.assertRaises((ValueError,TypeError,KeyError)):record.metadata(*values,self.data)
        with self.assertRaises(ValueError):record.metadata(run,jobs,artifact,self.data+b'changed')
        job['steps'][0]['conclusion']='skipped'
        with self.assertRaises(ValueError):record.metadata(run,jobs,artifact,self.data)

class RemainingWorkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acceptance=record.build()
        cls.current=record.remaining_work(ROOT,cls.acceptance)

    def test_completed_scopes_not_reopened(self):
        self.assertEqual([x['cases'] for x in self.current['accepted_scoped_reports']],[8,3,42,46,12])
        self.assertEqual(self.current['p06_adoption']['adopted_species_count'],2)
        self.assertEqual(self.current['p06_adoption']['field_change_count'],3)
        self.assertFalse(self.current['p07_adoption']['prior_instructions_absent_claimed'])
        ids={x['id'] for x in self.current['remaining_conditions']}
        self.assertNotIn('BREEDING_NOT_STARTED',ids)
        self.assertNotIn('MEGA_NOT_STARTED',ids)
        self.assertNotIn('P06_NOT_ADOPTED',ids)

    def test_different_candidates_are_not_final_acceptance(self):
        self.assertIsNone(self.current['final_candidate'])
        self.assertEqual(self.current['latest_scoped_candidate_stage'],84)
        self.assertFalse(self.current['historical_snapshot_is_current_backlog'])
        for key in ('full_p03_acceptance','full_p05_acceptance','full_p06_acceptance','full_p07_acceptance','release_ready','active_baseline_changed'):
            self.assertIs(self.current[key],False)

    def test_current_reconciliation_is_deterministic_and_read_only(self):
        names=set(self.current['source_bindings'])-{record.MANIFEST}
        before={n:(record.identity((ROOT/n).read_bytes()),(ROOT/n).stat().st_mtime_ns) for n in names}
        self.assertEqual(record.remaining_work(ROOT,self.acceptance),self.current)
        self.assertEqual(before,{n:(record.identity((ROOT/n).read_bytes()),(ROOT/n).stat().st_mtime_ns) for n in names})

    def test_every_closed_scope_has_source_binding(self):
        for row in self.current['accepted_scoped_reports']:
            self.assertIn(row['source_path'],self.current['source_bindings'])
        self.assertEqual(self.current['new_emulator_runs_during_reconciliation'],0)

if __name__=='__main__':unittest.main()
