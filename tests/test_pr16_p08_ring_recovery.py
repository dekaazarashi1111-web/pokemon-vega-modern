"""原本byte保全と安全な回収の拒否検査。emulator/旧検証は実行しない。"""
import copy
import io
from pathlib import Path
import stat
import sys
import unittest
import warnings
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_p08_ring_recovery as m


def archive(names):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(stream, 'w') as z:
            for name in names:
                z.writestr(name, b'original\n\n')
    return stream.getvalue()


def fixture():
    return dict(source_head=m.HEAD, workflow_source_head=m.HEAD, recording_run=m.RUN, case='ring-active',
        native_verified=True, representative_accepted=False, visual_review_completed=False, failures=[],
        new_emulator_processes=1, fresh_cores=3, host_compiles=1, arm_compiles=0, arm_links=0,
        accepted_standalone_replays=0, prefix_wins_reexecuted=0, rom_changes=0, release_ready=False), \
        dict(returncode=0, timed_out=False, spawn_error=None)


class RecoveryTests(unittest.TestCase):
    def test_trailing_blank_line_is_preserved(self):
        raw = b'{\n  "size": 33554432\n}\n\n'
        encoded = m.stable(m.envelope(raw))
        self.assertFalse(encoded.endswith(b'\n\n'))
        self.assertEqual(m.unwrap(m.strict(encoded)), raw)
    def test_empty_output_preserved(self):
        self.assertEqual(m.unwrap(m.envelope(b'')), b'')
    def test_nonascii_crlf_preserved(self):
        raw = '原本 \r\n\r\n'.encode()
        self.assertEqual(m.unwrap(m.envelope(raw)), raw)
    def test_modified_identity_rejected(self):
        value = m.envelope(b'ok\n'); value['identity']['size'] += 1
        with self.assertRaises(ValueError): m.unwrap(value)
    def test_nul_rejected(self):
        with self.assertRaises(ValueError): m.envelope(b'\0')
    def test_nontext_rejected(self):
        with self.assertRaises(UnicodeDecodeError): m.envelope(b'\xff')
    def test_duplicate_json_rejected(self):
        with self.assertRaises(ValueError): m.strict(b'{"x":1,"x":2}')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError): m.strict(b'{"x":NaN}')
    def test_archive_roundtrip(self):
        raw = archive(['execution/materialize.stdout'])
        self.assertEqual(m.archive_members(raw, m.identity(raw))['execution/materialize.stdout'], b'original\n\n')
    def test_digest_rejected(self):
        raw = archive(['ok'])
        with self.assertRaises(ValueError): m.archive_members(raw, m.identity(raw + b'x'))
    def test_unsafe_members_rejected(self):
        for name in ('../bad', '/bad', 'a/../bad', 'a\\bad', 'directory/'):
            with self.subTest(name=name):
                raw = archive([name])
                with self.assertRaises(ValueError): m.archive_members(raw, m.identity(raw))
    def test_duplicate_members_rejected(self):
        raw = archive(['x', 'x'])
        with self.assertRaises(ValueError): m.archive_members(raw, m.identity(raw))
    def test_symlink_rejected(self):
        info = zipfile.ZipInfo('link'); info.create_system=3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        raw = archive([info])
        with self.assertRaises(ValueError): m.archive_members(raw, m.identity(raw))
    def test_verified_native(self):
        m.require_native(*fixture())
    def test_native_false_and_claims_rejected(self):
        for key, value in [('native_verified', False), ('representative_accepted', True), ('visual_review_completed', True),
                           ('arm_compiles', 1), ('release_ready', True), ('new_emulator_processes', True), ('recording_run', 0)]:
            with self.subTest(key=key):
                native, proc = fixture(); native[key] = value
                with self.assertRaises(ValueError): m.require_native(native, proc)
    def test_bad_process_rejected(self):
        for key, value in [('returncode', False), ('returncode', 1), ('timed_out', True), ('spawn_error', 'failed')]:
            with self.subTest(key=key):
                native, proc = fixture(); proc[key] = value
                with self.assertRaises(ValueError): m.require_native(native, proc)


if __name__ == '__main__': unittest.main()
