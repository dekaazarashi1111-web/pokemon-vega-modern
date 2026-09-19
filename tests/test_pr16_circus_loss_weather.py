"""nativeフェード再開の狭い条件と初期frame0を、勝敗注入なしで検証。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('loss_weather',ROOT/'scripts/pr16_circus_loss_weather.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class WeatherGateTests(unittest.TestCase):
    def test_all_gate_combinations(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'gate'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/m.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            text=subprocess.check_output([str(exe)],text=True)
            self.assertEqual(text,'return_fade combinations=2624400 PASS\n')
    def test_patch_keeps_delegation_and_rejects_second_application(self):
        raw='#include "circus_streak_loss.h"\nEXPORT void CircusStreakRuntimeReadKeys(void)\n{\n    restore_cache_if_field();\n    ((void (*)(void))(uintptr_t)CIRCUS_PREVIOUS_READ_KEYS)();\n    restore_cache_if_field();\n}\n'
        patched=m.repair_runtime(raw)
        self.assertEqual(patched.count('CIRCUS_PREVIOUS_READ_KEYS)();'),1)
        self.assertEqual(patched.count('restore_cache_if_field();'),2)
        with self.assertRaises(ValueError):m.repair_runtime(patched)
    def test_runtime_only_calls_native_fade_and_does_not_set_result(self):
        self.assertIn('0x0807D361u',m.BODY)
        self.assertIn('0x0807951Du',m.BODY);self.assertIn('0x0807D465u',m.BODY)
        for bad in ('RESULT =','->current =','->best =','->phase =','set_result(','CircusRuntime_AfterBattle(', '0x080693F5'):
            self.assertNotIn(bad,m.BODY)
    def test_observer_is_read_only(self):
        text=(ROOT/m.WATCH).read_text()
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister('):self.assertNotIn(bad,text)
    def test_inherited_shell_steps_are_bounded(self):
        raw=(ROOT/m.SETUP_WORKFLOW).read_text()
        for label in m.SETUP_STEPS:
            shell=m.step_shell(raw,label)
            self.assertNotIn('git push',shell)
            subprocess.run(['bash','-n'],input=shell,text=True,check=True,capture_output=True)
        with self.assertRaises(ValueError):m.step_shell(raw+raw,m.SETUP_STEPS[0])
class FrameZeroTests(unittest.TestCase):
    # prepare installs the narrowly bound production parser before discovery.
    def sample(self):
        spec=importlib.util.spec_from_file_location('native_samples',ROOT/'tests/test_pr16_streak_native.py')
        t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
        return t
    def test_initial_fixture_zero_is_native_time(self):
        t=self.sample()
        for wins,losses in ((0,1),(3,0)):
            r,e=t.trace(wins,losses);e[0]['frame']=0
            self.assertEqual(t.check(r,e),r)
    def test_zero_is_only_first_fixture(self):
        t=self.sample()
        for at,label in ((0,'selected'),(1,'fixture')):
            r,e=t.trace();e[at].update(frame=0,label=label)
            with self.assertRaises(ValueError):t.check(r,e)
    def test_negative_bool_duplicate_frames_rejected(self):
        t=self.sample()
        for frame in (-1,False):
            r,e=t.trace();e[0]['frame']=frame
            with self.assertRaises(ValueError):t.check(r,e)
        r,e=t.trace();e[2]['frame']=e[1]['frame']
        with self.assertRaises(ValueError):t.check(r,e)
if __name__=='__main__':
    import pr16_streak_native as n
    m.install_probe(n.probe)
    unittest.main()
