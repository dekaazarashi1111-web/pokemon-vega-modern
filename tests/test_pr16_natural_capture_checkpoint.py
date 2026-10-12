import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts import pr16_natural_capture_checkpoint as m

class NaturalCaptureCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sets={label:m.display.archive((m.ROOT/m.DIRECTORY/str(rec[0])/'original.zip').read_bytes()) for label,rec in m.RECORDS.items()}
        cls.geometry=m.verify_geometry(cls.sets['geometry'])
    def verify(self,files=None,geometry=None):
        return m.verify_capture(self.sets['capture'] if files is None else files,self.geometry if geometry is None else geometry)
    def test_actual_raw_originals_and_review(self):
        value=self.verify();self.assertEqual(value['new_native_cores'],4);self.assertFalse(value['full_p05_acceptance']);self.assertEqual(len(value['reviewed_images']),12)
    def test_reject_product_or_gear_inflation(self):
        for key in ('release_ready','full_p05_acceptance','gear_acquisition_accepted','battle_connection_accepted'):
            files=dict(self.sets['capture']);keypath='pr16-natural-capture/result.json';row=m.load(files[keypath]);row[key]=True;files[keypath]=m.stable(row)
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify(files)
    def test_reject_raw_vs_report_difference(self):
        files=dict(self.sets['capture']);key='pr16-natural-capture/cave-113.stdout';row=m.load(files[key]);row['personality']+=1;files[key]=m.stable(row)
        with self.assertRaises(ValueError):self.verify(files)
    def test_reject_geometry_substitution(self):
        geometry=copy.deepcopy(self.geometry);geometry['maps'][0]['width']+=1
        with self.assertRaises(ValueError):self.verify(geometry=geometry)
    def test_reject_pixel_mutation(self):
        files=dict(self.sets['capture']);key='pr16-natural-capture/cave-118-natural-target.ppm';files[key]=files[key][:-1]+bytes([files[key][-1]^1])
        with self.assertRaises(ValueError):self.verify(files)
    def test_reject_missing_guard_record(self):
        files=dict(self.sets['capture']);files['pr16-natural-capture/guard-register.stdout']=b'PASS'
        with self.assertRaises(ValueError):self.verify(files)
    def test_reject_wrong_tested_head(self):
        files=dict(self.sets['capture']);files['pr16-natural-capture-evidence/tested-head.txt']=b'0'*40+b'\n'
        with self.assertRaises(ValueError):self.verify(files)
    def test_reject_incomplete_unit_log(self):
        files=dict(self.sets['capture']);files['pr16-natural-capture-evidence/unit.log']=b'Ran 34 tests\nFAIL\n'
        with self.assertRaises(ValueError):self.verify(files)
    def test_projection_preserves_remaining_gear_and_old_success(self):
        value={'capture':{'initial_fixtures':['map','lead','ball']}}
        old={'full_p06_acceptance':True,'full_p05_acceptance':False,'release_ready':False,'remaining_conditions':[{'id':'NATURAL_CAPTURE_GEAR'},{'id':'PHYSICAL_CIRCUS_ADMISSION'}]}
        with patch.object(m,'build',return_value=value),patch.object(m.prior,'read',return_value=m.stable(value)):
            new=m.project(old)
        self.assertTrue(new['natural_capture_checkpoint']['natural_capture_accepted']);self.assertFalse(new['full_p05_acceptance']);self.assertTrue(new['full_p06_acceptance']);self.assertEqual(len(new['remaining_conditions']),2);self.assertNotIn('natural_capture_checkpoint',old)

if __name__=='__main__':unittest.main()
