"""保存済み測定を再走せず、Forest受領器の拒否境界だけを検査する。"""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_forest_wallpaper_receipt as r


class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = r.regular(r.ROOT, r.MEASUREMENT)
        cls.cp = r.measurement(cls.raw)

    def reject(self, change):
        value = copy.deepcopy(self.cp)
        change(value)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            r.profiles(value)

    def test_original_four_profiles(self):
        self.assertEqual(len(r.measurement(self.raw)['profiles']), 4)

    def test_measurement_mutation(self):
        with self.assertRaises(ValueError):
            r.measurement(self.raw + b' ')

    def test_boolean_is_not_integer(self):
        self.assertFalse(r.exact(True, 1))
        self.assertFalse(r.exact([0], [False]))

    def test_duplicate_json(self):
        with self.assertRaises(ValueError):
            r.read(b'{"a":1,"a":2}')

    def test_float_json(self):
        with self.assertRaises(ValueError):
            r.read(b'{"a":1.0}')

    def test_nan_json(self):
        with self.assertRaises(ValueError):
            r.read(b'{"a":NaN}')

    def test_nul_json(self):
        with self.assertRaises(ValueError):
            r.read(b'{}\0')

    def test_parent_counter(self):
        self.reject(lambda c: c.update(classified=785))

    def test_donor_claim(self):
        self.reject(lambda c: c['claims'].update(donor_eligible=True))

    def test_native_claim(self):
        self.reject(lambda c: c['claims'].update(actual_runtime_execution_observed=True))

    def test_formal_premature(self):
        self.reject(lambda c: c.update(formal_receipt_created=True))

    def test_actions_premature(self):
        self.reject(lambda c: c.update(actions_completion_confirmed=True))

    def test_wrong_source(self):
        self.reject(lambda c: c.update(source_head='0'*40))

    def test_missing_profile(self):
        self.reject(lambda c: c['profiles'].pop())

    def test_duplicate_profile(self):
        self.reject(lambda c: c['profiles'].__setitem__(1, c['profiles'][0]))

    def test_boolean_offset(self):
        self.reject(lambda c: c['profiles'][0].update(wallpaper_offset=False))

    def test_incomplete_target(self):
        self.reject(lambda c: c['profiles'][0].update(target_bytes_consumed=3))

    def test_padding_consumption(self):
        self.reject(lambda c: c['profiles'][0].update(asset_lz_consumed=976))

    def test_wrong_decoded(self):
        self.reject(lambda c: c['profiles'][0]['decoded'].update(sha256='0'*64))

    def test_null_writes(self):
        self.reject(lambda c: c['profiles'][1].update(heap_bytes_written=1))

    def test_null_decode(self):
        self.reject(lambda c: c['profiles'][1].update(decoded=r.DECODED))

    def test_stack_unproven(self):
        self.reject(lambda c: c['profiles'][0].update(malloc_return_frame_proven=False))

    def test_wrong_stack_pointer(self):
        self.reject(lambda c: c['profiles'][0]['events'][-2].update(sp=50364096))

    def test_missing_table_field(self):
        self.reject(lambda c: c['profiles'][0]['table_reads'].pop())

    def test_wrong_call(self):
        self.reject(lambda c: c['profiles'][0]['calls'][0].update(target=0))

    def test_null_wrong_boundary(self):
        self.reject(lambda c: c['profiles'][1]['events'][-1].update(kind='CreateTask_boundary'))

    def test_path_traversal(self):
        with self.assertRaises(ValueError):
            r.regular(r.ROOT, '../escape')

    def test_path_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d);(p/'real').write_bytes(b'{}');(p/'alias').symlink_to(p/'real')
            with self.assertRaises(ValueError):
                r.regular(p, 'alias')

    def test_zip_not_original(self):
        with self.assertRaises(ValueError):
            r.unpack(b'not an original artifact')


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.run = dict(id=r.RUN,head_sha=r.SOURCE,head_branch=r.BRANCH,run_attempt=1,
            status='completed',conclusion='success',path=r.WORKFLOW,event='push',
            repository=dict(full_name=r.REPO),head_repository=dict(full_name=r.REPO))
        self.jobs = dict(total_count=1,jobs=[dict(id=r.JOB,run_id=r.RUN,head_sha=r.SOURCE,
            name='forest-reader',status='completed',conclusion='success',
            steps=[dict(number=n,name=s,status='completed',conclusion='success') for n,s in r.STEP_NAMES])])
        self.artifact = dict(id=r.ARTIFACT,name='pr16-forest-reader-public-text',size_in_bytes=r.ZIP_ID['size'],
            expired=False,digest='sha256:'+r.ZIP_ID['sha256'],workflow_run=dict(id=r.RUN,repository_id=1358127462,
            head_repository_id=1358127462,head_branch=r.BRANCH,head_sha=r.SOURCE))

    def check(self):
        return r.metadata(self.run, self.jobs, self.artifact)

    def test_exact_metadata(self):
        self.assertEqual(self.check()['run_id'], r.RUN)

    def test_incomplete_run(self):
        self.run.update(status='in_progress',conclusion=None)
        with self.assertRaises(ValueError): self.check()

    def test_rerun_attempt(self):
        self.run['run_attempt'] = 2
        with self.assertRaises(ValueError): self.check()

    def test_fork(self):
        self.run['head_repository']['full_name'] = 'other/repo'
        with self.assertRaises(ValueError): self.check()

    def test_missing_job_page(self):
        self.jobs['total_count'] = 2
        with self.assertRaises(ValueError): self.check()

    def test_skipped_step(self):
        self.jobs['jobs'][0]['steps'][4]['conclusion'] = 'skipped'
        with self.assertRaises(ValueError): self.check()

    def test_step_order(self):
        self.jobs['jobs'][0]['steps'].reverse()
        with self.assertRaises(ValueError): self.check()

    def test_wrong_artifact_digest(self):
        self.artifact['digest'] = 'sha256:'+'0'*64
        with self.assertRaises(ValueError): self.check()

    def test_wrong_artifact_head(self):
        self.artifact['workflow_run']['head_sha'] = '0'*40
        with self.assertRaises(ValueError): self.check()

    def test_expired_artifact(self):
        self.artifact['expired'] = True
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__':
    unittest.main()
