import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pr16_bp_loss_return_owner', HERE / 'scripts/pr16_bp_loss_return_owner.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
SAMPLE = '''#include "battle.h"
#define BATTLE_TYPE_FRONTIER 0x100
#define BATTLE_TYPE_BATTLE_TOWER 0x200
void EndBattleFlagClear(void) { gBattleOutcome = 0; }
void EndOfBattleThings(void) { (void)VegaBattlePolicyEnd(); EndBattleFlagClear(); }
void CB2_EndTrainerBattle(void) {
    if (gBattleOutcome == 2) SetMainCallback2(CB2_WhiteOut);
    else SetMainCallback2(CB2_ReturnToField);
}
'''


class OwnerAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'vendor/upstream/CFRU-JP/src/end_battle.c'
        self.source.parent.mkdir(parents=True)
        self.source.write_text(SAMPLE, encoding='utf-8')
        build = self.root / 'scripts/build_battle_core.py'
        build.parent.mkdir(parents=True)
        build.write_text('# VegaBattlePolicyEnd source patch\n', encoding='utf-8')

    def test_owner_audit_is_deterministic_and_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        one, text_one = M.audit(self.root)
        two, text_two = M.audit(self.root)
        self.assertEqual(M.stable(one), M.stable(two))
        self.assertEqual(text_one, text_two)
        self.assertTrue(one['summary']['owner_resolved'])
        self.assertFalse(one['summary']['candidate_rom_owner_verified'])
        self.assertEqual(one['summary']['new_emulator_processes'], 0)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_cli_writes_only_bounded_text_outputs(self):
        out = self.root / '.local/out'
        self.assertEqual(M.main(['--root', str(self.root), '--output-dir', str(out)]), 0)
        report = json.loads((out / 'owner-report.json').read_text())
        self.assertEqual(report['classification'], 'SOURCE_ONLY_OWNER_AUDIT_NOT_NATIVE_ACCEPTANCE')
        self.assertIn('CB2_WhiteOut', (out / 'owner-excerpts.txt').read_text())
        self.assertFalse(report['native_bp_earning_accepted'])

    def test_missing_required_owner_token_rejected(self):
        self.source.write_text('void nothing(void) {}\n')
        with self.assertRaises(M.OwnerAuditError): M.audit(self.root)

    def test_path_traversal_rejected(self):
        with self.assertRaises(M.OwnerAuditError): M.safe_path(self.root, Path('../outside'))

    def test_shared_header_declarations_do_not_resolve_owner(self):
        self.source.write_text(SAMPLE.split('void CB2_EndTrainerBattle')[0])
        header = self.source.parent / 'overworld.h'
        header.write_text('void CB2_WhiteOut(void);\nvoid CB2_ReturnToField(void);\n')
        report, _ = M.audit(self.root)
        self.assertTrue(report['summary']['source_scan_complete'])
        self.assertFalse(report['summary']['owner_resolved'])
        self.assertEqual(report['summary']['whiteout_owner_paths'], [])
        self.assertEqual(report['summary']['reference_only_overlap_paths'], ['vendor/upstream/CFRU-JP/src/overworld.h'])

    def test_comments_and_strings_do_not_supply_return_branch(self):
        self.source.write_text(SAMPLE.replace('else SetMainCallback2(CB2_ReturnToField);', '''// SetMainCallback2(CB2_ReturnToField);
    /* SetMainCallback2(CB2_ReturnToField); */
    const char *p = "SetMainCallback2(CB2_ReturnToField)";'''))
        report, _ = M.audit(self.root)
        self.assertFalse(report['summary']['owner_resolved'])

    def test_separate_functions_do_not_form_one_owner(self):
        self.source.write_text(SAMPLE.split('void CB2_EndTrainerBattle')[0] + '''
void loss(void) { SetMainCallback2(CB2_WhiteOut); }
void unrelated(void) { SetMainCallback2(CB2_ReturnToField); }
''')
        report, _ = M.audit(self.root)
        self.assertFalse(report['summary']['owner_resolved'])


if __name__ == '__main__':
    unittest.main()
