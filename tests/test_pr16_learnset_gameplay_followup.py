"""Task公開/初期化競合を修復する生成C差分のみ。既受入20試験は呼ばない。"""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_gameplay_followup as f

class PageInputRepair(unittest.TestCase):
    def setUp(self):
        self.original=(ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()
        self.rendered=f.render(self.original)

    def test_adds_initialization_wait(self):
        self.assertIn('stamp-t.page_menu<60U',self.rendered)

    def test_input_deferred_before_count_increment(self):
        self.assertLess(self.rendered.index('stamp-t.page_menu<60U'),self.rendered.index('page_down++;'))

    def test_zero_keys_while_initializing(self):
        self.assertIn('if(stamp-t.page_menu<60U){key=0;}',self.rendered)

    def test_selected_mode_asserted(self):
        self.assertIn('read8(c,A_MODE)==3U+page',self.rendered)

    def test_expected_list_not_weakened(self):
        start='static void a_list(';end='/* action:'
        self.assertEqual(self.original.split(start)[1].split(end)[0],self.rendered.split(start)[1].split(end)[0])

    def test_save_and_continue_unchanged(self):
        self.assertEqual(self.original.split('static bool a_save')[1],self.rendered.split('static bool a_save')[1])
        self.assertEqual(self.original.split('static bool a_continue')[1].split('static void a_key_item')[0],self.rendered.split('static bool a_continue')[1].split('static void a_key_item')[0])

    def test_readonly_observer(self):
        for old in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'rawWrite', 'writeRegister'):
            self.assertEqual(self.original.count(old),self.rendered.count(old))

    def test_cancel_retained(self):
        self.assertIn('if(action==5){key=QOL_KEY_B;t.page_choice=stamp;}',self.rendered)

    def test_missing_anchor_fails_closed(self):
        with self.assertRaises(ValueError):f.render('')

    def test_duplicate_anchor_fails_closed(self):
        with self.assertRaises(ValueError):f.render(self.original+self.original)

    def test_double_patch_fails_closed(self):
        with self.assertRaises(ValueError):f.render(self.rendered)

    def test_no_original_rom_source_edit(self):
        self.assertTrue(all(p.startswith(('scripts/','tests/')) for p in f.EXTRA))
        self.assertEqual(f.RUN,35830398856)
        self.assertEqual(f.ARTIFACT['id'],10737350300)

if __name__=='__main__':unittest.main()
