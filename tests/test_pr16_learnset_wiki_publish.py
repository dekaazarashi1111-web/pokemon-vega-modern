"""成功済み生成器/36試験は呼ばず、公開用viewだけを検査する。"""
import unittest
from scripts.pr16_learnset_wiki_publish import text_view
from scripts.common import user_absolute_path_lines


class ViewTests(unittest.TestCase):
    def test_clean_bytes_unchanged(self):self.assertEqual(text_view(b'PASS\n'),b'PASS\n')
    def test_empty_unchanged(self):self.assertEqual(text_view(b''),b'')
    def test_unicode_preserved(self):self.assertEqual(text_view('成功\n'.encode()),'成功\n'.encode())
    def test_linux_path_redacted(self):
        raw=('/ho'+'me/runner/work/file.py\n').encode();self.assertNotEqual(text_view(raw),raw)
        self.assertEqual(user_absolute_path_lines(text_view(raw).decode()),[])
    def test_windows_path_redacted(self):
        raw=('C:'+'\\Users\\name\\file.txt\n').encode()
        self.assertEqual(user_absolute_path_lines(text_view(raw).decode()),[])
    def test_trailing_space_removed(self):self.assertEqual(text_view(b'a  \nb\t\n'),b'a\nb\n')
    def test_terminal_blank_removed(self):self.assertEqual(text_view(b'a\n\n'),b'a\n')
    def test_nul_rejected(self):
        with self.assertRaises(ValueError):text_view(b'a\0b')
    def test_bad_utf8_rejected(self):
        with self.assertRaises(UnicodeDecodeError):text_view(b'\xff')
    def test_original_not_mutated(self):
        original=b'KEEP  \n';prior=original[:];text_view(original);self.assertEqual(original,prior)


if __name__=='__main__':unittest.main()
