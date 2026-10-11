"""Synthetic screen/output preservation tests, NOT emulator or visual acceptance."""
from pathlib import Path
import os
import tempfile
import unittest

from scripts import pr16_purchased_gear_evidence as e


class PurchasedGearEvidenceTests(unittest.TestCase):
    def result(self, version=2, cold=False):
        return dict(schema_version=version, status='PASS',
                    case='eelektross-cold-policy-reset' if cold else 'eelektross-active',
                    fresh_cores=3 if version==1 or cold else 2,
                    cold_reload_before_encounter=cold,
                    witness={'reloaded':100 if version==1 or cold else 0})

    def screens(self, out, value):
        raw=e.PPM_HEADER+bytes(240*160*3)
        for suffix in e.required_screens(value):
            (out/(value['case']+'-'+suffix+'.ppm')).write_bytes(raw)
        return raw

    def test_reserves_new_nested_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=e.prepare_output(root,root/'.local/fresh/a')
            self.assertTrue(out.is_dir());self.assertFalse(list(out.iterdir()))

    def test_refuses_previous_original_without_deletion(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=e.prepare_output(root,root/'.local/run')
            originals={'result.json':b'OLD PASS','compile.stderr':b'ORIGINAL LOG','eelektross-active-native-turn.ppm':b'RAW'}
            for name,raw in originals.items():(out/name).write_bytes(raw)
            with self.assertRaises(ValueError):e.prepare_output(root,out)
            self.assertEqual({p.name:p.read_bytes() for p in out.iterdir()},originals)

    def test_refuses_even_existing_empty_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'.local/run';out.mkdir(parents=True)
            with self.assertRaises(ValueError):e.prepare_output(root,out)

    def test_refuses_outside_root_traversal_and_relative_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for path in (root,root/'.local',root/'elsewhere',root/'.local/../escape',Path('.local/run')):
                with self.subTest(path=path),self.assertRaises(ValueError):e.prepare_output(root,path)
            self.assertFalse((root/'escape').exists())

    def test_refuses_existing_file_symlink_and_symlink_ancestor(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);local=root/'.local';local.mkdir();target=root/'target';target.mkdir()
            (local/'file').write_bytes(b'OLD')
            (local/'link').symlink_to(target,target_is_directory=True)
            for path in (local/'file',local/'link',local/'link/new'):
                with self.subTest(path=path),self.assertRaises(ValueError):e.prepare_output(root,path)
            self.assertFalse((target/'new').exists());self.assertEqual((local/'file').read_bytes(),b'OLD')

    def test_refuses_dangling_output_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'.local').mkdir();out=root/'.local/run';out.symlink_to(root/'absent')
            with self.assertRaises(ValueError):e.prepare_output(root,out)

    def test_old_and_new_cold_versus_same_session_screen_counts(self):
        self.assertEqual(len(e.required_screens(self.result(version=1))),14)
        self.assertEqual(len(e.required_screens(self.result(cold=True))),14)
        self.assertEqual(len(e.required_screens(self.result())),13)

    def test_rejects_old_relabel_new_wrong_core_or_missing_witness(self):
        values=[]
        for key,bad in (('schema_version',True),('schema_version',3),('fresh_cores',True),('fresh_cores',3),
                        ('cold_reload_before_encounter',True),('cold_reload_before_encounter',0),
                        ('case','another'),('status','FAIL'),('witness',{'reloaded':True}),('witness',{})):
            value=self.result();value[key]=bad;values.append(value)
        value=self.result(version=1);value['fresh_cores']=2;values.append(value)
        value=self.result(version=1);value['witness']['reloaded']=0;values.append(value)
        value=self.result(cold=True);value['witness']['reloaded']=0;values.append(value)
        for value in values:
            with self.subTest(value=value),self.assertRaises(ValueError):e.required_screens(value)

    def test_binds_actual_fixed_size_bytes_without_visual_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);value=self.result();self.screens(out,value)
            bound=e.bind_screens(out,value['case'],value)
            self.assertEqual(bound['required_screens'],13)
            self.assertEqual(len(bound['files']),13)
            self.assertFalse(bound['visual_review_completed'])
            self.assertFalse(bound['presentation_accepted'])
            self.assertFalse(bound['release_ready'])
            self.assertTrue(all(v['size']==e.PPM_SIZE and len(v['sha256'])==64 for v in bound['files'].values()))

    def test_rejects_missing_screen_without_claiming_pass(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);value=self.result();self.screens(out,value)
            (out/(value['case']+'-native-turn.ppm')).unlink()
            with self.assertRaises(FileNotFoundError):e.bind_screens(out,value['case'],value)

    def test_rejects_truncated_overlong_and_wrong_header_screens(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);value=self.result();raw=self.screens(out,value)
            path=out/(value['case']+'-native-turn.ppm')
            for bad in (raw[:-1],raw+b'x',b'P5'+raw[2:]):
                with self.subTest(size=len(bad)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError):e.bind_screens(out,value['case'],value)

    def test_rejects_screen_symlink_directory_and_fifo(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);value=self.result();self.screens(out,value)
            path=out/(value['case']+'-native-turn.ppm');path.unlink()
            path.symlink_to(out/(value['case']+'-fixture.ppm'))
            with self.assertRaises(ValueError):e.bind_screens(out,value['case'],value)
            path.unlink();path.mkdir()
            with self.assertRaises((ValueError,OSError)):e.bind_screens(out,value['case'],value)
            path.rmdir();os.mkfifo(path)
            with self.assertRaises(ValueError):e.bind_screens(out,value['case'],value)

    def test_rejects_case_path_injection_and_case_mismatch(self):
        value=self.result()
        for name in ('../x','eelektross-cold-policy-reset','eelektross-active/../../x'):
            with self.subTest(name=name),self.assertRaises(ValueError):e.bind_screens(Path('/unused'),name,value)

    def test_requires_actual_intermediate_reload_screen_for_cold_control(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);value=self.result(cold=True);self.screens(out,value)
            self.assertEqual(e.bind_screens(out,value['case'],value)['required_screens'],14)
            (out/(value['case']+'-equipped-reloaded.ppm')).unlink()
            with self.assertRaises(FileNotFoundError):e.bind_screens(out,value['case'],value)


if __name__=='__main__':unittest.main()
