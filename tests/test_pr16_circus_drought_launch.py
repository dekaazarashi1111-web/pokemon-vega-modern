"""outcome0の正規選出復帰を別guardで追加し、旧WIN/書込範囲を保持。"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_drought_launch as t
class DroughtLaunchTests(unittest.TestCase):
    def test_launch_fixture_8448_negative_and_positive_contexts(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'test'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/t.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('combinations=8448',result.stdout)
    def rows(self):return json.loads((ROOT/t.ROWS).read_bytes())
    def test_actual_new_cpu_diagnosis(self):
        value=t.diagnose(self.rows());self.assertEqual(value['current'],17);self.assertEqual(value['outcome'],0);self.assertGreaterEqual(value['native_loop_points'],16)
    def test_old_win_or_changed_cursor_not_launch_evidence(self):
        for key,value in [('current',16),('outcome',1),('script',0x09FF4D77),('weather','00'*64),('drought','00'*32),('tasks','00'*640)]:
            rows=self.rows();rows[-1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):t.diagnose(rows)
    def test_no_native_busy_loop_or_missing_endpoint_rejected(self):
        rows=self.rows()
        with self.assertRaises(ValueError):t.diagnose(rows[:-1])
        for r in rows:r['pc']=0
        with self.assertRaises(ValueError):t.diagnose(rows)
    def test_repair_is_exact_and_not_repeatable(self):
        src='#include "circus_drought.h"\nif(c.outcome == 1u && c.callback){}\nCircusDroughtInitialize(&c, w, a,b,c);\n'
        result=t.repair(src);self.assertIn('InitializeLaunch(',result);self.assertIn('c.outcome <= 1u',result)
        with self.assertRaises(ValueError):t.repair(result)
        with self.assertRaises(ValueError):t.repair(src.replace('== 1u','== 2u'))
    def test_original_predicate_and_native_state_ownership_not_replaced(self):
        header=(ROOT/t.HEADER).read_text()
        self.assertIn('CircusDroughtInitialize(c,w,original,init_vars,step);',header)
        self.assertIn('CircusDroughtEmptyLoader(w);',header)
        self.assertIn('c->outcome == 0u',header);self.assertIn('c->count == 3u',header)
        self.assertNotRegex(header,r'w\[[^\]]+\]\s*=(?!=)')
        self.assertNotRegex(header,r'c->(?:outcome|script|armed)\s*=(?!=)')
    def test_runtime_uses_real_wrappers_and_launch_initializer(self):
        source=(ROOT/'overlays/circus_streak/circus_drought.c').read_text()
        self.assertIn('CircusDroughtInitializeLaunch(&c, w, DroughtOriginal, DroughtInitVars, DroughtStep);',source)
        self.assertIn('VegaSaveValidate(',source);self.assertIn('CIRCUS_DROUGHT_ARMED',source)
        self.assertNotIn('NATIVE(0x0807AD09u),',source)
if __name__=='__main__':unittest.main()
