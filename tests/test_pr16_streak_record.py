"""構築成功をnative受入へ昇格せず、既存の受入を保持する記録契約。"""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('streak_record',ROOT/'scripts/pr16_streak_record.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class RecordTests(unittest.TestCase):
    def fixture(self):
        state={'candidate':{'sha256':'unchanged'},'latest_native_run':34946969126,'release_ready':False,
            'bp':{'earning_accepted':True},'next_action':{},'source_bindings':{'accepted':{'sha256':'keep'}},'do_not_repeat':[]}
        backlog={'remaining_conditions':[{'id':'PHYSICAL_CIRCUS_ADMISSION','success_evidence':None},
            {'id':'OTHER','success_evidence':{'keep':True}}]}
        report=dict(classification=r.CLASS,run_scope='BUILD_ONLY_NO_EMULATOR',build=dict(source_bindings={}))
        for k in ('native_streak_verified','later_battle_rental_identity_verified','physical_admission_accepted','suppression_accepted','release_ready'):report[k]=False
        return state,backlog,report
    def test_projection_preserves_authority_and_inputs(self):
        args=self.fixture();before=copy.deepcopy(args);s,b=r.project(*args)
        self.assertEqual(args,before)
        for k in ('candidate','latest_native_run','release_ready'):self.assertEqual(s[k],args[0][k])
        self.assertTrue(s['bp']['earning_accepted']);self.assertEqual(b['remaining_conditions'][1],args[1]['remaining_conditions'][1])
        self.assertIsNone(b['remaining_conditions'][0]['success_evidence'])
        self.assertFalse(s['circus_streak_build']['native_streak_verified'])
    def test_all_unproved_promotions_rejected(self):
        for key in ('native_streak_verified','later_battle_rental_identity_verified','physical_admission_accepted','suppression_accepted','release_ready'):
            args=self.fixture();args[2][key]=True
            with self.assertRaises(ValueError):r.project(*args)
    def test_wrong_scope_or_already_accepted_is_rejected(self):
        for key,value in (('classification','NATIVE_ACCEPTED'),('run_scope','NATIVE')):
            args=self.fixture();args[2][key]=value
            with self.assertRaises(ValueError):r.project(*args)
        args=self.fixture();args[1]['remaining_conditions'][0]['success_evidence']={}
        with self.assertRaises(ValueError):r.project(*args)
    def test_build_original_bytes_are_immutable(self):
        with self.assertRaises(ValueError):r.verify_files({r.BUILD+'report.json':b'{}'})
    def test_record_driver_changes_only_metadata_labels(self):
        source=(ROOT/r.common.SELF).read_text();changed=r.recording_driver(source)
        self.assertNotIn('native_run_id=',changed);self.assertEqual(changed.count('build_run_id='),2)
        self.assertIn('ops.assert_remote(head)',changed);self.assertIn('guard.guard()',changed)
        with self.assertRaises(ValueError):r.recording_driver(source.replace('scoped_native=verified','gone'))
class ArchiveTests(unittest.TestCase):
    def archive(self,name='source/config/ram_layout.csv',data=b'address,size\n0,64\n',wrong=False):
        import io,json,zipfile
        from pr16_streak_archive import identity
        stream=io.BytesIO();bound=identity(data)
        if wrong:bound['size']+=1
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr(name,data);z.writestr('members.json',json.dumps({name:bound}))
        raw=stream.getvalue();return raw,identity(raw)
    def test_only_two_exact_csv_paths_allowed(self):
        for name in ('source/config/ram_layout.csv','source/config/save_layout.csv'):
            files,manifest=r.unpack_build(*self.archive(name));self.assertIn(name,files)
        with self.assertRaises(ValueError):r.unpack_build(*self.archive('source/config/unknown.csv'))
    def test_private_bytes_and_paths_rejected(self):
        for name,data in (('x.gba',b'text'),('../outside.txt',b'text'),('ok.txt',b'a\0b')):
            with self.assertRaises(ValueError):r.unpack_build(*self.archive(name,data))
    def test_zip_and_member_hashes_both_required(self):
        raw,bound=self.archive();bound['size']+=1
        with self.assertRaises(ValueError):r.unpack_build(raw,bound)
        with self.assertRaises(ValueError):r.unpack_build(*self.archive(wrong=True))
if __name__=='__main__':unittest.main()
