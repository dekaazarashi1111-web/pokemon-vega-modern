"""tracked sourceのみを消失原本へ関連付ける。ROM/saveを輸出しない。"""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('load_order',ROOT/'scripts/pr16_circus_load_order.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LoadOrderTests(unittest.TestCase):
    def test_consumers_selected(self):
        for token in ('SaveLoad','SaveWrite','FactoryRuntime_Recover','FactoryOnRecover','save_adapter','0x09405D81','0x9405d81'):
            self.assertTrue(m.selected('scripts/source.py',token.encode()))
    def test_circus_and_save_owner_files_included(self):
        for name in ('overlays/circus_streak/a.c','overlays/save_migration/a.h'):
            self.assertTrue(m.selected(name,b'/* plain tracked source */'))
        self.assertFalse(m.selected('tools/unrelated.py',b'print(1)'))
    def test_binary_or_untracked_scopes_never_exported(self):
        for name in ('../tools/x.c','/tools/x.c','tools/../../x.c','build/x.c','private/x.c','vendor/x.c',
                     'tools/private/x.c','tools/vendor/x.c','tools/.local/x.c','evidence/x.c','assets/x.c',
                     'scripts/x.gba','scripts/x.sav','scripts/x.zip','scripts/x.bin'):
            self.assertFalse(m.allowed(name));self.assertFalse(m.selected(name,b'SaveLoad'))
    def test_invalid_source_fails_closed(self):
        for raw in (b'\xff',b'a\0SaveLoad',b'x'*(1024*1024+1)):
            with self.assertRaises((ValueError,UnicodeDecodeError)):m.selected('tools/x.c',raw)
if __name__=='__main__':unittest.main()
