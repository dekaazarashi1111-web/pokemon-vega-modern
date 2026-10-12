"""定数1件と再開gateの限定差分。成功16試験・Bag23の再実行なし。"""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_battle_retry as r

class CompilerRepair(unittest.TestCase):
    def test_keypad_constant(self):
        self.assertEqual(0x0020,1<<5)
        source=(ROOT/'tools/mgba_continue_field_smoke.c').read_text()
        self.assertIn('CONTINUE_KEY_LEFT = 0x20U',source)
        self.assertIn('#define QOL_KEY_LEFT 0x0020U',r.repair_c('#include "pr16_learnset_battle_fixture.h"'))

    def test_only_constant_added(self):
        old='#include "pr16_learnset_battle_fixture.h"\nint main() { return 7; }\n'
        out=r.repair_c(old)
        self.assertEqual(out.splitlines()[-1],old.splitlines()[-1])
        self.assertEqual(len(out.splitlines()),len(old.splitlines())+2)

    def test_missing_anchor_rejected(self):
        with self.assertRaises(ValueError):r.repair_c('')
        with self.assertRaises(ValueError):r.repair_runner('')

    def test_duplicate_anchor_rejected(self):
        with self.assertRaises(ValueError):r.repair_c('#include "pr16_learnset_battle_fixture.h"\n'*2)

    def test_accepted_checkpoint_never_rerun(self):
        old="m.need(not (ROOT/CP).exists(),'battle checkpoint already exists: inspect before retry')"
        self.assertIn("m.load(ROOT/CP)['status']=='FAIL'",r.repair_runner(old))
        self.assertIn('accepted battle rerun refused',r.repair_runner(old))

    def test_prior_native_was_not_run(self):
        self.assertEqual(r.RUN,35832603358)
        self.assertEqual(r.ARTIFACT['id'],10737707124)
        self.assertEqual(r.HEAD,'ea7cf90458ee011719c7aafd137c740a97320c05')

if __name__=='__main__':unittest.main()
