"""新規private差分検証の範囲・fail-closed条件のみ試験。既受入テストは呼ばない。"""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import pr16_ips_dpe_private_guard as g


class DeltaGuardTests(unittest.TestCase):
    def test_exact_scope_regular_text(self):
        self.assertTrue(g.safe("content/modernization/pr16_selected_ips_dpe_frontier_checkpoint.json"))
        self.assertTrue(g.safe("scripts/pr16_ips_dpe_private_guard.py"))

    def test_private_suffix_blocked(self):
        for name in ("content/rom.gba","x/y.sav","x/ips.ips","x.bin","data.zip"):
            self.assertFalse(g.safe(name))

    def test_private_area_blocked(self):
        for name in ("inputs/private/foo.json","inputs/source_archives/z.md","userfile/hi.json"):
            self.assertFalse(g.safe(name))

    def test_path_traversal_rejected(self):
        for name in ("../secret.md","/root/a.json","docs/../user.json","docs\\x.md"):
            self.assertFalse(g.safe(name))

    def test_only_existing_flags_do_not_add(self):
        old=b"some words\nSee /home/tester/secret/file.txt\n"
        new=old+b"Ordinary follow-up\n"
        self.assertEqual(g.added_absolute_paths(old,new),{})

    def test_new_absolute_user_path_detected(self):
        old=b"readme\n"
        new=old+b"See /home/tester/secret/file.txt\n"
        self.assertEqual(sum(g.added_absolute_paths(old,new).values()),1)

    def test_existing_unsafe_lines_not_disappeared_by_reordering(self):
        old=b"See /home/tester/secret/file.txt\nline\n"
        new=b"line\nSee /home/tester/secret/file.txt\n"
        self.assertEqual(g.added_absolute_paths(old,new),{})


if __name__=="__main__":
    unittest.main()
