"""保存済みprimary sourceのIS_MASTER定義と限定observer差分。"""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_battle_field as f

class NaturalField(unittest.TestCase):
    def setUp(self):
        self.minimal='c->setKeys(c,key);c->runFrame(c);++lb_frames;\na_require(lb_action(c) && read32(c,ADDR_BATTLE_TYPE_FLAGS)==0 && identity);'

    def test_primary_nonlink_master_definition(self):
        raw=(ROOT/'content/modernization/pr16_p08_ring_representative.json').read_text()
        self.assertIn('BATTLE_TYPE_IS_MASTER',raw)
        self.assertIn("0x0004 // In not-link battles, it's always set.",raw)

    def test_exact_nonlink_single_not_mask(self):
        out=f.render(self.minimal)
        self.assertIn('read32(c,ADDR_BATTLE_TYPE_FLAGS)==4U',out)
        self.assertNotIn('FLAGS)&',out)

    def test_identity_assertion_remains(self):
        self.assertIn('&& identity);',f.render(self.minimal))

    def test_readonly_added_observer(self):
        out=f.render(self.minimal)
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'create_mon('):self.assertNotIn(token,out)
        self.assertIn('LEARNED_ENCOUNTER',out)
        self.assertIn('lb_outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME)',out)

    def test_does_not_double_apply(self):
        with self.assertRaises(ValueError):f.render(f.render(self.minimal))
        with self.assertRaises(ValueError):f.render('')

    def test_pending_native_only(self):
        self.assertEqual(f.RUN,35833129256)
        self.assertEqual(f.ARTIFACT['id'],10737588489)
        self.assertNotIn('a_scene(',f.render(self.minimal))

if __name__=='__main__':unittest.main()
