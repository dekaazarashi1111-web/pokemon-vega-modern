"""Final candidate identity and original-evidence regressions, not fresh ROM results."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
import modernization_final_integration as final
import run_modernization_p06_decided_e2e as native


class FinalIdentityTests(unittest.TestCase):
    def setUp(self):
        self.row = json.loads((ROOT/'tests/fixtures/p06_decided_native_template.json').read_bytes())

    def test_parent_success_does_not_accept_final(self):
        with self.assertRaises(ValueError):
            native.validate(json.dumps(self.row).encode(), (373,0,0), 0, final.SHA)

    def test_final_parser_template_needs_exact_candidate(self):
        # Parser fixture only; this is explicitly NOT a native Stage84 execution.
        self.row['candidate_sha256'] = final.SHA
        result = native.validate(json.dumps(self.row).encode(), (373,0,0), 0, final.SHA)
        self.assertFalse(result['full_p06_acceptance'])
        with self.assertRaises(ValueError):
            native.validate(json.dumps(self.row).encode(), (373,0,0), 0)

    def test_arbitrary_candidate_cannot_be_authorized(self):
        with self.assertRaises(ValueError):
            native.validate(json.dumps(self.row).encode(), (373,0,0), 0, '0'*64)

    def test_final_still_checks_stats(self):
        self.row['candidate_sha256'] = final.SHA
        self.row['final_stats'][1] = 70
        with self.assertRaises(ValueError):
            native.validate(json.dumps(self.row).encode(), (373,0,0), 0, final.SHA)

    def test_final_still_checks_exit_and_cold_save(self):
        self.row['candidate_sha256'] = final.SHA
        for code in (False, 1, -9):
            with self.subTest(code=code), self.assertRaises(ValueError):
                native.validate(json.dumps(self.row).encode(), (373,0,0), code, final.SHA)
        self.row['candidate_cold_100_bytes_equal'] = False
        with self.assertRaises(ValueError):
            native.validate(json.dumps(self.row).encode(), (373,0,0), 0, final.SHA)

    def test_safe_path(self):
        for path in ('../x', '/tmp/x'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                final.safe(path)


class OriginalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ.get('P06_ORIGINAL_ZIP', str(ROOT/'content/modernization/p08_p06_evidence/34444010444/original.zip')))
        with zipfile.ZipFile(cls.path) as archive:
            cls.members = {name: archive.read(name) for name in archive.namelist()}

    def test_exact_original(self):
        receipt = final.evidence(self.path)
        self.assertEqual(receipt['observations'], 8)
        self.assertEqual(receipt['adopted_fields'], 3)
        self.assertEqual(receipt['new_mgba_executions_for_evidence_check'], 0)
        self.assertFalse(receipt['full_p06_acceptance'])

    def test_summary_mutations(self):
        for key, value in [('full_p06_acceptance', True), ('candidate_stage',84), ('core_instances',25),
                           ('cache_reuse',1), ('observations',8), ('fresh_process_runs',True)]:
            members = self.members.copy()
            row = json.loads(members['result.json']); row[key] = value
            members['result.json'] = json.dumps(row).encode()
            with self.subTest(key=key), self.assertRaises(ValueError):
                final.validate_original_members(members)

    def test_original_observation_mutations(self):
        for key, value in [('candidate_sha256',final.SHA), ('final_stats',[0]*6), ('normal_save_menu',False),
                           ('host_write_barriers',0), ('slot_preserved',False)]:
            members = self.members.copy(); row = json.loads(members['220-0-0.stdout']); row[key] = value
            members['220-0-0.stdout'] = json.dumps(row).encode()
            with self.subTest(key=key), self.assertRaises(ValueError):
                final.validate_original_members(members)

    def test_guards_and_exits(self):
        for guard in native.GUARDS:
            members = self.members.copy()
            name = 'guard-'+guard+'.process.json'
            row = json.loads(members[name]); row['returncode'] = 0; members[name] = json.dumps(row).encode()
            with self.subTest(guard=guard), self.assertRaises(ValueError):
                final.validate_original_members(members)
        members = self.members.copy()
        row = json.loads(members['220-0-0.process.json']); row['timed_out'] = True
        members['220-0-0.process.json'] = json.dumps(row).encode()
        with self.assertRaises((ValueError,RuntimeError)):
            final.validate_original_members(members)

    def test_sources_toolchain_and_head(self):
        for name in ('tested-head.txt','sources/tools/modernization_p06_decided_adjustments.py',
                     'cc-version.stdout', 'mgba-version.stdout'):
            members = self.members.copy(); members[name] = b'changed'
            with self.subTest(name=name), self.assertRaises(ValueError):
                final.validate_original_members(members)

    def test_missing_case(self):
        members = self.members.copy(); row=json.loads(members['result.json']); row['cases'].pop()
        members['result.json'] = json.dumps(row).encode()
        with self.assertRaises(ValueError):
            final.validate_original_members(members)


if __name__ == '__main__':
    unittest.main()
