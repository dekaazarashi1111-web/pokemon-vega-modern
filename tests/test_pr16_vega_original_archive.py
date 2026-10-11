"""原作assetとROM identityの境界を合成fixtureで検証する。"""
import unittest
from tools.pr16_vega_original_baseline import SourceError

class ArchiveTests(unittest.TestCase):
    def build_archive(self, directory, *, extra=False, bad_manifest=False, bad_rom=False, unsafe=False):
        import hashlib, json, zipfile
        from pathlib import Path
        path = Path(directory) / 'test.zip'
        raw = b'fixture-original-only'
        ident = {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        manifest = {'schema_version': 1, 'archive': path.name, 'files': [dict(path='build/reference/vega.gba', **ident)]}
        if bad_manifest:
            manifest['archive'] = 'other.zip'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('PRIVATE_ENVIRONMENT_MANIFEST.json', json.dumps(manifest))
            z.writestr('build/reference/vega.gba', raw[:-1] + b'X' if bad_rom else raw)
            if extra:
                z.writestr('undeclared.txt', b'x')
            if unsafe:
                z.writestr('../escape', b'x')
        return path, {'size': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, {'rom_size': ident['size'], 'rom_sha256': ident['sha256']}, raw

    def test_only_declared_original_read(self):
        import tempfile
        from tools.pr16_vega_original_baseline import original_from_archive
        with tempfile.TemporaryDirectory() as directory:
            path, bound, rom, raw = self.build_archive(directory)
            self.assertEqual(original_from_archive(path, bound, rom), raw)

    def test_corrupt_outer_digest_rejected(self):
        import tempfile
        from tools.pr16_vega_original_baseline import original_from_archive
        with tempfile.TemporaryDirectory() as directory:
            path, bound, rom, _ = self.build_archive(directory)
            bound['sha256'] = '0' * 64
            with self.assertRaises(SourceError):
                original_from_archive(path, bound, rom)

    def test_undeclared_member_rejected(self):
        import tempfile
        from tools.pr16_vega_original_baseline import original_from_archive
        with tempfile.TemporaryDirectory() as directory:
            path, bound, rom, _ = self.build_archive(directory, extra=True)
            with self.assertRaises(SourceError):
                original_from_archive(path, bound, rom)

    def test_misnamed_manifest_rejected(self):
        import tempfile
        from tools.pr16_vega_original_baseline import original_from_archive
        with tempfile.TemporaryDirectory() as directory:
            path, bound, rom, _ = self.build_archive(directory, bad_manifest=True)
            with self.assertRaises(SourceError):
                original_from_archive(path, bound, rom)

    def test_wrong_original_bytes_rejected(self):
        import tempfile
        from tools.pr16_vega_original_baseline import original_from_archive
        with tempfile.TemporaryDirectory() as directory:
            path, bound, rom, _ = self.build_archive(directory, bad_rom=True)
            with self.assertRaises(SourceError):
                original_from_archive(path, bound, rom)

    def test_unsafe_zip_member_rejected(self):
        import tempfile
        from tools.pr16_vega_original_baseline import original_from_archive
        with tempfile.TemporaryDirectory() as directory:
            path, bound, rom, _ = self.build_archive(directory, unsafe=True)
            with self.assertRaises(SourceError):
                original_from_archive(path, bound, rom)

    def test_original_identity_conflict_rejected(self):
        import tempfile
        from tools.pr16_vega_original_baseline import original_from_archive
        with tempfile.TemporaryDirectory() as directory:
            path, bound, rom, _ = self.build_archive(directory)
            rom['rom_sha256'] = '0' * 64
            with self.assertRaises(SourceError):
                original_from_archive(path, bound, rom)


if __name__ == '__main__':
    unittest.main()
