"""prepareの設定後に別名importしても受入方策のヘッダーidentityを保持する。"""
from pathlib import Path
import importlib.util
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'scripts/pr16_circus_continuous.py'

def load(name):
    spec=importlib.util.spec_from_file_location(name,PATH)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ContinuousReentryTests(unittest.TestCase):
    def test_configured_dependency_reimport_preserves_exact_policy(self):
        first=load('continuous_reentry_first')
        self.assertEqual(len(first.HEADERS),7)
        self.assertEqual(len(set(first.HEADERS)),7)
        headers={path:(ROOT/path).read_text() for path in first.HEADERS}
        expected=first.policy_text('slot=wx_move_slot(c);',headers)
        # 実prepareと同じ共有設定変更。別名importを繰り返しても7件のまま。
        with patch.object(first.f,'HEADERS',first.HEADERS):
            for index in range(3):
                again=load('continuous_reentry_'+str(index))
                self.assertEqual(again.HEADERS,first.HEADERS)
                self.assertEqual(again.policy_text('slot=wx_move_slot(c);',headers),expected)
        self.assertEqual(expected.count('(read16(c,0x0203DB20U)%3U)'),4)

if __name__=='__main__':unittest.main()
