"""新規host境界だけを実行。既存load/phase0/retry試験をimport実行しない。"""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_research_ui_boundary as m

CASES = ('init-0','init-1','init-255','init-null','post-unset','purchase-unselected',
         'save-blocked','kanto-locked','empty','task-fail','window-fail','nothing',
         'b-cancel','negative','invalid-row','last-cancel','next-window-fail',
         'filtered','fallback-text','balance-zero','balance-9999') + tuple('select-'+str(i) for i in range(23))

class CanonicalUIBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.text = (ROOT / m.SOURCE).read_text()
        generated, cls.bindings = m.generate(cls.text)
        cls.generated_sha256 = hashlib.sha256(generated.encode()).hexdigest()
        source = Path(cls.tmp.name) / 'boundary.c'
        cls.exe = Path(cls.tmp.name) / 'boundary'
        source.write_text(generated)
        command = ['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(source),'-o',str(cls.exe)]
        p = subprocess.run(command, capture_output=True, timeout=90)
        if p.returncode or p.stderr:
            raise AssertionError('strict host compile: '+p.stderr.decode('utf-8'))
    def run_boundary(self, case):
        p = subprocess.run([str(self.exe),case], capture_output=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr.decode('utf-8'))
        self.assertEqual(p.stderr, b'')
        self.assertEqual(p.stdout, b'PASS_CANONICAL_HOST_BOUNDARY_NOT_NATIVE\n')
    def test_source_change_rejected(self):
        with self.assertRaises(ValueError): m.generate(self.text+'\n')
    def test_missing_function_rejected(self):
        with self.assertRaises(ValueError): m.function(self.text, 'NotAResearchFunction')
    def test_duplicate_function_rejected(self):
        body = m.function(self.text, 'ResearchEconomy_OpenShop')
        with self.assertRaises(ValueError): m.function(self.text+'\n'+body,'ResearchEconomy_OpenShop')
    def test_closed_function_set(self):
        self.assertEqual(set(self.bindings),set(m.FUNCTIONS))
        self.assertEqual(len(self.bindings),22)
    def test_unknown_runtime_case_rejected(self):
        p = subprocess.run([str(self.exe),'unknown'],capture_output=True,timeout=10)
        self.assertNotEqual(p.returncode,0)
        self.assertNotIn(b'PASS_',p.stdout)

for case in CASES:
    def check(self, case=case): self.run_boundary(case)
    setattr(CanonicalUIBoundaryTests,'test_boundary_'+case.replace('-','_'),check)

if __name__ == '__main__': unittest.main()
