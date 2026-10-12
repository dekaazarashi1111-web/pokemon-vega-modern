"""Only new terminal/archive boundaries; no old tests or emulator execution."""
import io
from pathlib import Path
import sys
import unittest
import warnings
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_research_hatch_proof as c


def sample(names=('proof.txt',)):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for name in names:
                z.writestr(name, b'original\n')
    raw = stream.getvalue()
    a = dict(id=123, expired=False, digest='sha256:'+c.identity(raw)['sha256'],
             size_in_bytes=len(raw), workflow_run=dict(id=456, head_sha='a'*40))
    return raw, a, {'proof.txt': c.identity(b'original\n')}


class TerminalTests(unittest.TestCase):
    def test_exact_zip_and_member(self):
        raw, a, expected = sample()
        self.assertEqual(c.archive(raw, a, expected, 456, 'a'*40), {'proof.txt': b'original\n'})
    def test_zip_digest(self):
        raw, a, expected = sample(); a['digest'] = 'sha256:'+'0'*64
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_member_digest(self):
        raw, a, expected = sample(); expected['proof.txt']['sha256'] = '0'*64
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_expired(self):
        raw, a, expected = sample(); a['expired'] = True
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_source_binding(self):
        raw, a, expected = sample(); a['workflow_run']['head_sha'] = 'b'*40
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_run_binding(self):
        raw, a, expected = sample(); a['workflow_run']['id'] = 457
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_boolean_id(self):
        raw, a, expected = sample(); a['id'] = True
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_duplicate(self):
        raw, a, expected = sample(('proof.txt', 'proof.txt'))
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_extra(self):
        raw, a, expected = sample(('proof.txt', 'extra.txt'))
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_missing(self):
        raw, a, expected = sample(())
        with self.assertRaises(ValueError): c.archive(raw, a, expected, 456, 'a'*40)
    def test_traversal(self):
        raw, a, _ = sample(('../proof.txt',))
        with self.assertRaises(ValueError): c.archive(raw, a, {'../proof.txt':None}, 456, 'a'*40)
    def test_nested_path(self):
        raw, a, _ = sample(('sub/proof.txt',))
        with self.assertRaises(ValueError): c.archive(raw, a, {'sub/proof.txt':None}, 456, 'a'*40)
    def test_blank_frame_is_not_visual_acceptance(self):
        raw = c.PPM_HEADER + bytes(240*160*3)
        self.assertFalse(c.frame(raw)['nonblank'])
    def test_nonblank_frame(self):
        raw = c.PPM_HEADER + b'\xff\0\0' + bytes(240*160*3-3)
        self.assertTrue(c.frame(raw)['nonblank'])
    def test_bad_frame_size(self):
        with self.assertRaises(ValueError): c.frame(c.PPM_HEADER + b'\0')
    def test_bad_frame_header(self):
        with self.assertRaises(ValueError): c.frame(b'P6\n160 240\n255\n'+bytes(240*160*3))
    def test_reflected_commit(self):
        commit = dict(sha='b'*40, parents=[dict(sha='a'*40)])
        self.assertEqual(c.reflected(('b'*40+'\n').encode(), 'a'*40, commit), 'b'*40)
    def test_wrong_parent(self):
        with self.assertRaises(ValueError): c.reflected(('b'*40+'\n').encode(), 'a'*40, dict(sha='b'*40, parents=[dict(sha='c'*40)]))
    def test_merge_parent_rejected(self):
        with self.assertRaises(ValueError): c.reflected(('b'*40+'\n').encode(), 'a'*40, dict(sha='b'*40, parents=[dict(sha='a'*40)]*2))
    def test_sha_injection(self):
        with self.assertRaises(ValueError): c.reflected(b'not-a-sha\n', 'a'*40, {})
    def test_terminal_source_never_executes_native(self):
        text = (c.ROOT/c.SELF).read_text()
        self.assertNotIn('r.execute(', text)
        self.assertNotIn("'cc'", text)
        self.assertNotIn('loadROM(', text)
        self.assertNotIn('def execute(', text)


if __name__ == '__main__': unittest.main()
