"""保存済みsource artifactに含まれる拡張子なしtextをexact pathで扱う。"""
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pr16_wiki_followup_sources import unpack

class ArchiveMakefileTests(unittest.TestCase):
    def fixture(self, name, text=b'all:\n\ttrue\n'):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr(name, text)
        return stream.getvalue()

    def test_exact_historical_makefile_allowed(self):
        with tempfile.TemporaryDirectory() as root:
            unpack(self.fixture('local/Makefile'), Path(root))
            self.assertEqual((Path(root) / 'local/Makefile').read_text(), 'all:\n\ttrue\n')

    def test_other_extensionless_paths_still_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ('other/Makefile', 'local/credentials', 'Makefile'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    unpack(self.fixture(name), Path(root))

    def test_exact_makefile_with_nul_still_rejected(self):
        with tempfile.TemporaryDirectory() as root, self.assertRaises(ValueError):
            unpack(self.fixture('local/Makefile', b'\0'), Path(root))

if __name__ == '__main__':
    unittest.main()
