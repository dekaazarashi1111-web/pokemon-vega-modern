import importlib.util
import io
import json
from pathlib import Path
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location('owner_closeout', Path(__file__).resolve().parents[1] / 'scripts/pr16_bp_owner_closeout.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class CloseoutTests(unittest.TestCase):
    def setUp(self):
        commit = 'e24a16fe39e27ae162faf5b78596d1f3df18489d'
        self.report = dict(schema_version=2, classification='SOURCE_ONLY_OWNER_AUDIT_NOT_NATIVE_ACCEPTANCE',
            fixed_source=dict(commit=commit), native_bp_earning_accepted=False, release_ready=False,
            summary=dict(new_emulator_processes=0, accepted_native_cases_replayed=0, candidate_rom_changed=False,
                source_scan_complete=True, owner_resolved=False, candidate_rom_owner_verified=False, callback_owner_candidates=[]),
            matches=dict(CB2_WhiteOut=[dict(path='vendor/upstream/CFRU-JP/include/overworld.h', line=97,
                text='void __attribute__((long_call)) CB2_WhiteOut(void);')]))
        self.data = {n: b'' for n in M.MEMBERS}
        self.data.update({'tested-head.txt': (M.TESTED + '\n').encode(), 'unit.stderr': b'Ran 19 tests in 0.1s\n\nOK\n',
            'source-restore.json': M.stable(dict(fsck_verified=True, clean_source_verified=True, locked_commit=commit,
                archived_worktree_used=False, archived_git_config_used=False))})

    def pack(self, *, extra=None, bad_manifest=False):
        self.data['owner-report.json'] = M.stable(self.report)
        manifest = {n: M.identity(b) for n, b in self.data.items() if n != 'members.json'}
        if bad_manifest:
            manifest['unit.stderr']['sha256'] = '0' * 64
        self.data['members.json'] = M.stable(manifest)
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as z:
            for n, b in self.data.items(): z.writestr(n, b)
            if extra: z.writestr(extra, b'not allowed')
        raw = out.getvalue()
        ident = M.identity(raw)
        pin = (1, 2, 3, M.TESTED, ident['size'], ident['sha256'], 2, 19)
        return raw, pin

    def test_exact_payloads_preserved_and_native_acceptance_false(self):
        raw, pin = self.pack()
        data, report, receipt = M.validate_artifact(raw, pin)
        self.assertEqual(data, self.data)
        self.assertFalse(report['summary']['owner_resolved'])
        self.assertTrue(receipt['fsck_verified'])

    def test_wrong_zip_digest_rejected(self):
        raw, pin = self.pack()
        with self.assertRaisesRegex(ValueError, 'ZIP identity'): M.validate_artifact(raw + b'x', pin)

    def test_wrong_member_digest_rejected_after_zip_rebound(self):
        raw, pin = self.pack(bad_manifest=True)
        with self.assertRaisesRegex(ValueError, 'member digest'): M.validate_artifact(raw, pin)

    def test_false_owner_claim_rejected(self):
        self.report['summary']['owner_resolved'] = True
        raw, pin = self.pack()
        with self.assertRaisesRegex(ValueError, 'promoted'): M.validate_artifact(raw, pin)

    def test_traversal_or_extra_member_rejected(self):
        raw, pin = self.pack(extra='../outside')
        with self.assertRaisesRegex(ValueError, 'members'): M.validate_artifact(raw, pin)


if __name__ == '__main__':
    unittest.main()
