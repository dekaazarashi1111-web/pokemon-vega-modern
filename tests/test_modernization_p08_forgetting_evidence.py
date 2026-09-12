"""Original-byte and mutation checks; synthetic metadata is only a unit fixture."""
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
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


class CurrentRemainingWorkOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acceptance = record.build()
        cls.tracked = record.load((ROOT/record.OVERVIEW).read_bytes())

    def test_current_snapshot_preserves_later_checkpoint_fields(self):
        current = record.current_remaining_work(ROOT, self.acceptance)
        self.assertTrue(record.same(current, self.tracked))
        conditions = {row['id']: row for row in current['remaining_conditions']}

        p03 = conditions['EVOLUTION_FORM_OTHER_EGG']
        self.assertEqual(
            p03['status'], 'PENDING_FIXED_FORM_ROUTE_ACCEPTANCE')
        self.assertEqual(p03['remaining_physical_gap_ids'], [
            'P03_FIXED_FORM_TRANSITION_PHYSICAL',
        ])
        self.assertEqual(
            p03['coverage_manifest'],
            'content/modernization/pr16_p03_p07_route_coverage.json')

        p05 = conditions['NATURAL_CAPTURE_GEAR']
        self.assertEqual(
            p05['status'], 'PENDING_THREE_BOUND_NATIVE_SUPPLY_ACCEPTANCES')
        self.assertEqual(p05['remaining_supply_gap_ids'], [
            'P05_NATIVE_RING_ACQUISITION_PHYSICAL',
            'P05_NATIVE_BP_EARNING_PHYSICAL',
            'P05_ORDINARY_POLICY_SELECTION_PHYSICAL',
        ])
        self.assertEqual(
            p05['supply_coverage_manifest'],
            'content/modernization/pr16_p05_native_supply_reconciliation.json')
        self.assertEqual(
            p05['supply_evidence_map'],
            'content/modernization/pr16_p05_native_supply_evidence_map.json')

        p07 = conditions['P07_REMAINING_ROUTE_ACCEPTANCE']
        self.assertTrue(p07['complete'])
        self.assertEqual(p07['remaining_physical_gap_ids'], [])
        self.assertEqual(
            p07['status'], 'PASS_PARENT_CANDIDATE_PENDING_P08_TRANSFER')

    def test_unknown_future_fields_survive_unchanged(self):
        future = copy.deepcopy(self.tracked)
        future['future_owner_projection'] = {'sentinel': True}
        future['remaining_conditions'][0]['future_owner_field'] = 'kept'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root/record.OVERVIEW
            target.parent.mkdir(parents=True)
            target.write_bytes((json.dumps(future, ensure_ascii=False,
                                           sort_keys=True, indent=2) + '\n').encode())
            actual = record.current_remaining_work(root, self.acceptance)
        self.assertTrue(record.same(actual, future))

    def test_missing_owned_report_is_rejected(self):
        broken = copy.deepcopy(self.tracked)
        broken['accepted_scoped_reports'] = [
            row for row in broken['accepted_scoped_reports']
            if row.get('source_path') != record.MANIFEST
        ]
        with self.assertRaisesRegex(
                ValueError, 'forgetting accepted report link differs'):
            record.validate_current_remaining_work(broken, self.acceptance)

    def test_changed_owned_binding_is_rejected(self):
        broken = copy.deepcopy(self.tracked)
        broken['source_bindings'][record.MANIFEST]['sha256'] = '0' * 64
        with self.assertRaisesRegex(
                ValueError, 'forgetting manifest binding differs'):
            record.validate_current_remaining_work(broken, self.acceptance)

if __name__=='__main__':unittest.main()
