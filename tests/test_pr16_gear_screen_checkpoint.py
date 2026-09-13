"""Retained-original rejection checks; these tests do not execute an emulator."""
from pathlib import Path
import tempfile
import unittest
from scripts import pr16_gear_screen_checkpoint as c


class GearScreenCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files=c.display.archive((c.ROOT/c.DIRECTORY/'original.zip').read_bytes())

    def changed_json(self,path,key,value):
        files=dict(self.files);obj=c.load(files[path]);obj[key]=value;files[path]=c.stable(obj);return files

    def reject(self,files):
        with self.assertRaises((ValueError,KeyError,OSError)):
            c.verify(files)

    def test_accepts_only_four_processes_nine_cores_with_53_bound_58_reviewed_screens(self):
        value=c.verify(self.files)
        self.assertEqual((value['actual_native_processes'],value['actual_fresh_cores'],value['mandatory_bound_screens'],len(value['reviewed_images'])),(4,9,53,58))
        self.assertFalse(value['full_p05_acceptance']);self.assertFalse(value['release_ready'])
        self.assertTrue(all(not v['presentation_accepted'] for v in value['screen_bindings'].values()))

    def test_rejects_missing_mandatory_screen(self):
        files=dict(self.files);del files['pr16-purchased-gear/eelektross-active-native-turn.ppm'];self.reject(files)

    def test_rejects_changed_reviewed_extra_frame(self):
        files=dict(self.files);p='pr16-purchased-gear/eelektross-active-mega-active.ppm';raw=files[p];files[p]=raw[:-1]+bytes([raw[-1]^1]);self.reject(files)

    def test_rejects_screen_sidecar_promoted_to_visual_pass(self):
        self.reject(self.changed_json('pr16-purchased-gear/eelektross-active.screens.json','presentation_accepted',True))

    def test_rejects_inflated_phase_or_counts(self):
        for key,bad in (('full_p05_acceptance',True),('release_ready',True),('successful_fresh_cores',18),('actual_new_processes',8),('old_runs_relabelled',1)):
            with self.subTest(key=key):self.reject(self.changed_json('pr16-purchased-gear/result.json',key,bad))

    def test_rejects_false_process_exit_and_boolean_zero(self):
        for value in (1,False):
            with self.subTest(value=value):self.reject(self.changed_json('pr16-purchased-gear/eelektross-active.process.json','returncode',value))

    def test_rejects_different_head(self):
        files=dict(self.files);files[c.RECORD[7]+'tested-head.txt']=b'wrong\n';self.reject(files)

    def test_rejects_missing_tests(self):
        files=dict(self.files);files[c.RECORD[7]+'unit.log']=b'Ran 64 tests\nOK\n';self.reject(files)

    def test_rejects_corrupted_source_binding(self):
        files=dict(self.files);p=c.RECORD[7]+'source-bindings.json';value=c.load(files[p]);value[c.screens.SELF]['sha256']='0'*64;files[p]=c.stable(value);self.reject(files)

    def test_install_keeps_original_and_refuses_different_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=Path('evidence/original.zip');c.install(root,p,b'original');c.install(root,p,b'original')
            with self.assertRaises(ValueError):c.install(root,p,b'replacement')
            self.assertEqual((root/p).read_bytes(),b'original')

    def test_install_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'original.zip').symlink_to(root/'outside')
            with self.assertRaises(ValueError):c.install(root,Path('original.zip'),b'new')
            self.assertFalse((root/'outside').exists())


if __name__=='__main__':unittest.main()
