from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from scripts import pr16_captured_battle_checkpoint as m

class CapturedBattleCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files=m.display.archive((m.ROOT/m.DIRECTORY/str(m.RECORD[0])/'original.zip').read_bytes())
    def test_exact_controller_originals_and_review(self):
        value=m.verify(self.files);self.assertEqual(value['new_native_cores'],6);self.assertEqual(len(value['reviewed_images']),24);self.assertTrue(value['captured_to_native_battle_accepted']);self.assertFalse(value['gear_acquisition_accepted'])
    def test_reject_old_two_core_relabel(self):
        files=dict(self.files);key='pr16-captured-battle/result.json';row=m.load(files[key]);row['successful_fresh_cores']=4;files[key]=m.stable(row)
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_extra_success_counts(self):
        files=dict(self.files);key='pr16-captured-battle/result.json';row=m.load(files[key]);row['new_native_processes']=4;files[key]=m.stable(row)
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_gear_or_release_inflation(self):
        for name in ('gear_acquisition_accepted','full_p05_acceptance','release_ready'):
            files=dict(self.files);key='pr16-captured-battle/result.json';row=m.load(files[key]);row[name]=True;files[key]=m.stable(row)
            with self.subTest(name=name),self.assertRaises(ValueError):m.verify(files)
    def test_reject_controller_substitution(self):
        files=dict(self.files);files['pr16-captured-battle/controller.c']+=b'\n/* different */\n'
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_pixel_substitution(self):
        files=dict(self.files);key='pr16-captured-battle/cave-113-captured-sent-out.ppm';files[key]=files[key][:-1]+bytes([files[key][-1]^1])
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_missing_native_battle_proof(self):
        files=dict(self.files);key='pr16-captured-battle/cave-113.stderr';files[key]=b'\n'.join(line for line in files[key].splitlines() if not line.startswith(b'CAPTURED_BATTLE_PROOF '))
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_changed_captured_identity(self):
        files=dict(self.files);key='pr16-captured-battle/cave-113.stdout';row=m.load(files[key]);row['personality']+=1;files[key]=m.stable(row)
        with self.assertRaises(ValueError):m.verify(files)
    def test_projection_retains_gear_boundary_and_prior_receipt(self):
        old={'full_p06_acceptance':True,'full_p05_acceptance':False,'release_ready':False,'natural_capture_checkpoint':{'source_path':m.base.RECEIPT,'battle_connection_accepted':False},'remaining_conditions':[{'id':'NATURAL_CAPTURE_GEAR'}]}
        with patch.object(m,'build',return_value={}),patch.object(m.prior,'read',return_value=b'{}'):
            value=m.project(old)
        self.assertTrue(value['captured_battle_checkpoint']['captured_to_native_battle_accepted']);self.assertFalse(value['captured_battle_checkpoint']['gear_to_battle_accepted']);self.assertFalse(value['full_p05_acceptance']);self.assertTrue(value['full_p06_acceptance']);self.assertTrue(value['natural_capture_checkpoint']['historical_capture_only']);self.assertNotIn('captured_battle_checkpoint',old)

if __name__=='__main__':unittest.main()
