"""初回計測guardと公開workflowの新scope検証。private入力には触れない。"""
import copy
import os
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_blastoise_actions as a

class BlastoiseActionsTests(unittest.TestCase):
    def history(self):return dict(total_count=1,workflow_runs=[dict(id=71,head_sha='a'*40,head_branch=a.BRANCH,run_attempt=1)])
    def test_one_scope_first_attempt(self):a.validate_history(self.history(),71,'a'*40)
    def test_second_run_rejected(self):
        h=self.history();h['total_count']=2
        with self.assertRaises(ValueError):a.validate_history(h,71,'a'*40)
    def test_hidden_other_branch_rejected(self):
        h=self.history();h['workflow_runs'].append(dict(h['workflow_runs'][0],id=72,head_branch='other'))
        with self.assertRaises(ValueError):a.validate_history(h,71,'a'*40)
    def test_attempt2_rejected(self):
        h=self.history();h['workflow_runs'][0]['run_attempt']=2
        with self.assertRaises(ValueError):a.validate_history(h,71,'a'*40)
    def test_head_mismatch_rejected(self):
        with self.assertRaises(ValueError):a.validate_history(self.history(),71,'b'*40)
    def test_branch_mismatch_rejected(self):
        h=self.history();h['workflow_runs'][0]['head_branch']='main'
        with self.assertRaises(ValueError):a.validate_history(h,71,'a'*40)
    def test_run_mismatch_rejected(self):
        with self.assertRaises(ValueError):a.validate_history(self.history(),72,'a'*40)
    def test_run_boolean_rejected(self):
        h=self.history();h['workflow_runs'][0]['id']=True
        with self.assertRaises(ValueError):a.validate_history(h,1,'a'*40)
    def test_total_boolean_rejected(self):
        h=self.history();h['total_count']=True
        with self.assertRaises(ValueError):a.validate_history(h,71,'a'*40)
    def test_attempt_boolean_rejected(self):
        h=self.history();h['workflow_runs'][0]['run_attempt']=True
        with self.assertRaises(ValueError):a.validate_history(h,71,'a'*40)
    def test_closed_new_suite_names(self):self.assertEqual(a.SUITES,('sources','asset','chain','validation','actions'))
    def test_publication_path_matches_workflow(self):
        p=a.publication.contract(ROOT,a.WF,a.PUBLIC,a.ARTIFACT,a.SELF)
        self.assertEqual(p['directory'],'public-blastoise-asset')
    def test_export_rejects_non_success_before_read(self):
        for value in ('failure','cancelled','skipped',''):
            with self.subTest(value=value),mock.patch.dict(os.environ,BLASTOISE_MEASUREMENT_OUTCOME=value):
                with self.assertRaises(ValueError):a.export()
    def test_export_graph_failure_prevents_publication(self):
        def run(args,**kw):
            if '--check' in args:raise subprocess.CalledProcessError(1,args)
            return subprocess.CompletedProcess(args,0)
        with mock.patch.dict(os.environ,BLASTOISE_MEASUREMENT_OUTCOME='success',GITHUB_SHA='a'*40), \
             mock.patch.object(a,'validate_guard'), \
             mock.patch.object(a.subprocess,'check_output',return_value='a'*40), \
             mock.patch.object(a.subprocess,'run',side_effect=run), \
             mock.patch.object(a.validation,'validate_output') as publish:
            with self.assertRaises(subprocess.CalledProcessError):a.export()
            publish.assert_not_called()
    def test_source_missing_never_network_without_flag(self):
        with tempfile.TemporaryDirectory()as tmp:
            with self.assertRaises(ValueError):a.source_preflight(tmp)
    def test_source_symlink_directory_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);(root/'real').mkdir();(root/'link').symlink_to(root/'real',target_is_directory=True)
            with self.assertRaises(ValueError):a.source_preflight(root/'link')
    def test_workflow_has_no_secret_or_write_permission(self):
        text=(ROOT/a.WF).read_text()
        self.assertNotIn('secrets.',text);self.assertNotIn(': write',text)
        self.assertIn('persist-credentials: false',text);self.assertIn('github.run_attempt == 1',text)
    def test_workflow_success_only_publication(self):
        text=(ROOT/a.WF).read_text()
        self.assertIn("if: ${{ always() && steps.publication_guard.outcome == 'success' }}",text)
        self.assertIn('if-no-files-found: error',text);self.assertIn('path: public-blastoise-asset',text)

if __name__=='__main__':unittest.main()
