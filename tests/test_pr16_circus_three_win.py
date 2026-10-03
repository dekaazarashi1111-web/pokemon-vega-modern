"""読取専用の候補順位付けと、本当の3勝以外の受入拒否。"""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('three_win',ROOT/'scripts/pr16_circus_three_win.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ThreeWinTests(unittest.TestCase):
    def test_only_three_actual_wins(self):
        row=dict(wins=3,losses=0,battles=3);self.assertIs(m.three_wins(row),row)
    def test_loss_and_short_batches_rejected(self):
        for wins in range(3):
            with self.assertRaises(ValueError):m.three_wins(dict(wins=wins,losses=1,battles=wins+1))
    def test_bool_missing_and_extra_battle_rejected(self):
        for row in (dict(wins=3,losses=False,battles=3),dict(wins=3,battles=3),dict(wins=3,losses=0,battles=4)):
            with self.assertRaises(ValueError):m.three_wins(row)
    def test_policy_is_read_only_and_uses_ordinary_chooser(self):
        text=(ROOT/m.HEADER).read_text()
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', 'SC_OWNER', '0x03000EB8'):
            self.assertNotIn(bad,text)
        self.assertIn('wx_cursor(c,best);sp_entry(c,n,best);',text)
        self.assertIn('#define wx_team cw_team',text)
    def test_score_prioritizes_usable_attack_speed_without_overflow(self):
        source='#define CIRCUS_TEAM_HOST_TEST\n#include "'+str(ROOT/m.HEADER)+'"\n#include <assert.h>\nint main(void){\n'
        source+='assert(cw_move_score(90,100,1,49,152,145)>cw_move_score(60,100,0,72,105,60));\n'
        source+='assert(cw_move_score(0,100,1,100,100,100)==0);assert(cw_move_score(90,100,2,100,100,100)==0);\n'
        source+='assert(cw_move_score(90,0,1,100,100,100)==cw_move_score(90,100,1,100,100,100));\n'
        source+='assert(cw_move_score(255,100,1,65535,65535,65535)==(uint64_t)255*100*65535*(128+65535));return 0;}\n'
        with tempfile.TemporaryDirectory() as folder:
            c=Path(folder)/'score.c';exe=Path(folder)/'score';c.write_text(source)
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)
if __name__=='__main__':unittest.main()
