"""Record uses immutable artifact and prohibits unobserved full acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_ring_npc_gift_record as m


class RecordContracts(unittest.TestCase):
    def test_archive_digest_is_pinned(self):
        with self.assertRaises(ValueError):m.unpack(b'not the original native artifact')

    def test_receipt_has_three_exact_unmodified_cases(self):
        report=json.loads((ROOT/m.REPORT).read_bytes())
        self.assertEqual(report['native']['actual_new_processes'],3)
        self.assertEqual(report['native']['successful_fresh_cores'],6)
        self.assertEqual(set(report['originals']),{'gift-save-revisit','locked-save-revisit','full-save-revisit'})
        for name,original in report['originals'].items():
            for data in original.values():
                self.assertEqual(m.identity(data['utf8'].encode('utf-8')),data['identity'])

    def test_record_never_promotes_battle_release(self):
        r=json.loads((ROOT/m.REPORT).read_bytes())
        self.assertEqual(r['classification'],'SCOPED_NPC_GIFT_SAVE_ONLY')
        self.assertTrue(r['npc_gift_save_scoped_accepted'])
        for key in ('ring_full_acceptance','ordinary_battle_accepted','release_ready'):
            self.assertIs(r[key],False)
        self.assertEqual(r['record_new_emulator_processes'],0)

    def test_source_and_candidate_are_not_bp_candidate(self):
        r=json.loads((ROOT/m.REPORT).read_bytes())
        self.assertEqual(r['tested_head'],m.TESTED)
        self.assertEqual(r['candidate']['sha256'],m.CANDIDATE)
        self.assertEqual(r['crc32'],'62F3C583')
        s=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
        self.assertEqual(s['candidate']['sha256'],'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b')
        self.assertIn('P05_NATIVE_RING_ACQUISITION_PHYSICAL',s['remaining_physical_gap_ids'])
        self.assertIn('P05_ORDINARY_POLICY_SELECTION_PHYSICAL',s['remaining_physical_gap_ids'])

    def test_visual_digests_refer_to_seven_reviewed_members(self):
        r=json.loads((ROOT/m.REPORT).read_bytes())
        self.assertEqual(len(r['visual_review']['reviewed_sha256']),7)
        for name,sha in m.VISUAL.items():
            self.assertEqual(r['member_manifest']['pr16-ring-npc-native/'+name+'.png']['sha256'],sha)

    def test_initial_failure_not_rewritten(self):
        r=json.loads((ROOT/m.REPORT).read_bytes())
        self.assertEqual(r['previous_rejected_build']['conclusion'],'failure')
        self.assertEqual(r['previous_rejected_build']['native_processes'],0)


if __name__=='__main__':unittest.main()
