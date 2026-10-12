"""初戦原本の改変・guard弱化・限定結果の全体受入化を拒否する。"""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_circus_first_record as record
from test_pr16_circus_native import result,trace

class FirstRecordContracts(unittest.TestCase):
    def archive(self,files,manifest=None,extra=None):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:
            for name,data in files.items():z.writestr(name,data)
            z.writestr('members.json',record.stable(manifest if manifest is not None else {n:record.identity(d) for n,d in files.items()}))
            if extra is not None:z.writestr(*extra)
        return buf.getvalue()
    def check_zip(self,raw):return record.unpack(raw,record.identity(raw))
    def test_safe_text_and_fixed_ppm(self):
        files={'x.txt':b'hello','x.ppm':b'P6\n240 160\n255\n'+bytes(240*160*3)}
        unpacked,manifest=self.check_zip(self.archive(files));self.assertEqual(manifest,{n:record.identity(d) for n,d in files.items()})
    def test_outer_identity(self):
        with self.assertRaises(ValueError):record.unpack(self.archive({'x.txt':b'a'}),{})
    def test_member_identity(self):
        with self.assertRaises(ValueError):self.check_zip(self.archive({'x.txt':b'a'}, {'x.txt':record.identity(b'b')}))
    def test_manifest_coverage(self):
        for raw in (self.archive({'x.txt':b'a'},{}),self.archive({'x.txt':b'a'},extra=('y.txt',b'b'))):
            with self.assertRaises(ValueError):self.check_zip(raw)
    def test_unsafe_path(self):
        for name in ('../x.txt','/x.txt','a//b.txt','a\\b.txt'):
            with self.assertRaises(ValueError):self.check_zip(self.archive({name:b'a'}))
    def test_private_or_binary_member(self):
        for files in ({'x.gba':b'rom'},{'x.srm':b'save'},{'x.zip':b'zip'},{'x.txt':b'\0'}):
            with self.assertRaises(ValueError):self.check_zip(self.archive(files))
    def test_symlink_and_bad_ppm(self):
        info=zipfile.ZipInfo('x.txt');info.create_system=3;info.external_attr=0o120777<<16
        with self.assertRaises(ValueError):self.check_zip(self.archive({},extra=(info,b'elsewhere')))
        with self.assertRaises(ValueError):self.check_zip(self.archive({'x.ppm':b'P6\n240 160\n255\n'}))
    def fixture(self):
        row=result('circus-first-battle');stem='pr16-circus-native/circus-first-battle'
        process=dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None)
        files={stem+'.stdout':record.stable(row),stem+'.stderr':trace(row['case']),stem+'.process.json':record.stable(process)}
        screens={}
        for i in range(16):
            name=f'circus-first-battle-{i}.ppm';data=b'P6\n240 160\n255\n'+bytes(240*160*3)
            files['pr16-circus-native/'+name]=data;screens[name]=record.identity(data)
        for guard in record.GUARDS:
            prefix='pr16-circus-native/guard-'+guard
            files.update({prefix+'.stdout':b'',prefix+'.stderr':b'P03 archive: host write after observation barrier\n',
                prefix+'.process.json':record.stable(dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None))})
        r=dict(source_head=record.SPEC['tested_head'],candidate=dict(size=33554432,sha256=record.native.SHA),status='PASS_CIRCUS_SCOPED_NATIVE',
            scope='THUMB_REPAIRED_CIRCUS_FIRST_BATTLE_ONLY',requested_cases=['circus-first-battle'],failures=[],guard_checks=record.GUARDS.copy(),
            actual_new_processes=1,successful_fresh_cores=1,accepted_native_cases_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
            results=[dict(case='circus-first-battle',process=process,result=row,screens=screens,visual_review_completed=False)])
        return r,files
    def test_valid_original(self):
        r,f=self.fixture();self.assertEqual(record.validate_report(r,f),r['results'][0]['result'])
    def test_reject_head_scope_or_replayed_case(self):
        for key,value in (('source_head','0'*40),('scope','ALL_CASES'),('requested_cases',list(record.native.CASES)),('failures',[{}]),('guard_checks',record.GUARDS[:-1])):
            r,f=self.fixture();r[key]=value
            with self.assertRaises(ValueError):record.validate_report(r,f)
    def test_reject_native_misaccount_or_boolean(self):
        for key,value in (('actual_new_processes',True),('actual_new_processes',3),('successful_fresh_cores',2),('accepted_native_cases_replayed',1)):
            r,f=self.fixture();r[key]=value
            with self.assertRaises(ValueError):record.validate_report(r,f)
    def test_reject_full_acceptance(self):
        for key in ('physical_admission_accepted','suppression_accepted','release_ready'):
            r,f=self.fixture();r[key]=True
            with self.assertRaises(ValueError):record.validate_report(r,f)
    def test_reject_failed_process(self):
        r,f=self.fixture();key='pr16-circus-native/circus-first-battle.process.json'
        for field,value in (('returncode',1),('timed_out',True),('spawn_error','failed')):
            bad=f.copy();p=record.load(bad[key]);p[field]=value;bad[key]=record.stable(p)
            with self.assertRaises(ValueError):record.validate_report(r,bad)
    def test_reject_guard_or_screenshot_mutation(self):
        r,f=self.fixture()
        for name in ('pr16-circus-native/guard-register.stderr','pr16-circus-native/circus-first-battle-0.ppm'):
            bad=f.copy();bad[name]=b'changed'
            with self.assertRaises(ValueError):record.validate_report(r,bad)
    def test_reject_relabelled_result_or_visual(self):
        for key,value in (('visual_review_completed',True),('case','factory-fallback-cancel'),('result',{})):
            r,f=self.fixture();r['results'][0][key]=value
            with self.assertRaises(ValueError):record.validate_report(r,f)
    def state(self):
        from test_pr16_circus_thumb_record import RecordContracts
        s,b,_=RecordContracts().state()
        r=dict(physical_admission_accepted=False,release_ready=False,rental_identity_verified=False,
            classification='CIRCUS_FIRST_TURN_VERIFIED_RENTAL_IDENTITY_AND_STREAK_OPEN',candidate=dict(size=33554432,sha256=record.native.SHA))
        return s,b,r
    def test_projection_preserves_authorities_and_input(self):
        s,b,r=self.state();before=copy.deepcopy((s,b));new_s,new_b=record.project(s,b,r)
        self.assertEqual((s,b),before);self.assertEqual(s['candidate'],new_s['candidate']);self.assertEqual(b['remaining_conditions'][1],new_b['remaining_conditions'][1])
        self.assertEqual(new_s['bp']['next_step'],new_s['next_action']['goal_ja']);self.assertEqual(record.project(new_s,new_b,r),(new_s,new_b))
    def test_projection_rejects_closed_gate_or_claimed_identity(self):
        for key in ('physical_admission_accepted','release_ready','rental_identity_verified'):
            s,b,r=self.state();r[key]=True
            with self.assertRaises(ValueError):record.project(s,b,r)
        s,b,r=self.state();b['remaining_conditions'][0]['success_evidence']='accepted'
        with self.assertRaises(ValueError):record.project(s,b,r)

if __name__=='__main__':unittest.main()
