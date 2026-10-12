"""二origin受領の新境界試験。reader/ROM/旧試験は実行しない。"""
from __future__ import annotations
import copy
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_typed_origins_receipt as m


class Receipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp=m.regular(m.ROOT,m.CHECKPOINT); cls.raw=m.regular(m.ROOT,m.PROOF)
        cls.p=m.read(cls.raw)
        old=m.read(m.regular(m.ROOT,'content/modernization/pr16_forest_wallpaper_receipt_evidence/unknown-frontier.json'))
        # 旧874行の実再検査ではなく、差分器の明示的な合成fixture。
        accepted=[dict(address=0x08010000+8*i,accepted=True,classification='SYNTHETIC_ACCEPTED') for i in range(785)]
        cls.parent=m.encode(dict(classified=785,unclassified=89,hits=accepted+[r['hit'] for r in old['rows']],
            classifications=dict(SYNTHETIC_ACCEPTED=785,UNCLASSIFIED=89),legacy_namespace={'keep':[True,0,'原本']}))

    def build(self):
        return m.build(self.parent,self.cp,self.raw)

    def test_original_profiles_and_byte_offsets(self):
        result=m.profiles(self.p)
        self.assertEqual([(r['container_offset'],r['size']) for r in result[0]],[(3,1),(0,3)])
        self.assertEqual([(r['container_offset'],r['size']) for r in result[1]],[(1,3),(0,1)])

    def test_hit_order(self):
        p=copy.deepcopy(self.p);p['hits'].reverse()
        with self.assertRaises(ValueError):m.profiles(p)

    def test_original_checkpoint_identity(self):
        m.measurement(self.cp,self.raw)

    def test_checkpoint_tamper(self):
        with self.assertRaises(ValueError):m.measurement(self.cp+b' ',self.raw)

    def test_proof_tamper(self):
        with self.assertRaises(ValueError):m.measurement(self.cp,self.raw+b' ')

    def test_parent_requires_exact_formal_identity(self):
        with self.assertRaises(ValueError):self.build()

    def test_synthetic_two_changes_and_old_namespace(self):
        with patch.object(m,'PARENT_ID',m.identity(self.parent)):
            delta=self.build(); full=m.materialize(self.parent,delta,self.cp,self.raw)
        old=m.read(self.parent)
        self.assertEqual((full['classified'],full['unclassified']),(787,87))
        self.assertEqual(sum(a!=b for a,b in zip(old['hits'],full['hits'])),2)
        self.assertEqual(full['legacy_namespace'],old['legacy_namespace'])
        self.assertEqual(m.frontier(full)['total'],87)
        self.assertFalse(delta['claims']['donor_eligible'])
        self.assertEqual(delta['donor_safe_bytes'],0)

    def test_synthetic_deterministic(self):
        with patch.object(m,'PARENT_ID',m.identity(self.parent)):
            self.assertEqual(m.encode(self.build()),m.encode(self.build()))

    def test_reapplication_rejected(self):
        with patch.object(m,'PARENT_ID',m.identity(self.parent)):
            full=m.materialize(self.parent,self.build(),self.cp,self.raw)
            with self.assertRaises(ValueError):m.build(m.encode(full),self.cp,self.raw)

    def test_coverage_gap(self):
        with self.assertRaises(ValueError):m.coverage(m.HITS[0],[(m.HITS[0],3)])

    def test_coverage_overlap(self):
        with self.assertRaises(ValueError):m.coverage(m.HITS[0],[(m.HITS[0],4),(m.HITS[0],1)])

    def test_incomplete_bl_width(self):
        p=copy.deepcopy(self.p);p['profiles'][2]['instructions'][-2]['size']=2
        with self.assertRaises(ValueError):m.profiles(p)

    def test_integer_bool_distinction(self):
        self.assertFalse(m.exact(0,False));self.assertFalse(m.exact(1,True))
        p=copy.deepcopy(self.p);p['profiles'][0]['field_index']=False
        with self.assertRaises(ValueError):m.profiles(p)

    def test_json_duplicate_key(self):
        with self.assertRaises(ValueError):m.read(b'{"x":1,"x":2}')

    def test_json_float_nonfinite(self):
        for raw in (b'{"x":1.0}',b'{"x":NaN}',b'{"x":Infinity}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):m.read(raw)

    def test_regular_readonly_byte_mtime(self):
        p=m.ROOT/m.PROOF; before=(p.read_bytes(),p.stat().st_mtime_ns)
        m.measurement(self.cp,m.regular(m.ROOT,m.PROOF))
        self.assertEqual(before,(p.read_bytes(),p.stat().st_mtime_ns))

    def test_regular_path_escape(self):
        with self.assertRaises(ValueError):m.regular(m.ROOT,'../escape')

    def test_regular_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'a').write_text('a');(root/'b').symlink_to(root/'a')
            with self.assertRaises(ValueError):m.regular(root,'b')

    def test_zip_duplicate_and_foreign(self):
        for names in (['a','a'],['a','b']):
            raw=io.BytesIO()
            with zipfile.ZipFile(raw,'w') as z:
                for name in names:z.writestr(name,'text')
            with self.assertRaises(ValueError):m.zip_members(raw.getvalue(),{'a'})

    def test_zip_symlink(self):
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:
            info=zipfile.ZipInfo('a');info.create_system=3;info.external_attr=0o120777<<16;z.writestr(info,'target')
        with self.assertRaises(ValueError):m.zip_members(raw.getvalue(),{'a'})

    def test_zip_traversal(self):
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr('../a','text')
        with self.assertRaises(ValueError):m.zip_members(raw.getvalue(),{'../a'})

    def test_zip_wrong_identity(self):
        with self.assertRaises(ValueError):m.unpack(b'not-an-accepted-archive')


def replace(value,path,new):
    for key in path[:-1]:value=value[key]
    value[path[-1]]=new


def profile_rejection(path,new):
    def test(self):
        value=copy.deepcopy(self.p);replace(value,path,new)
        with self.assertRaises(ValueError):m.profiles(value)
    return test


for name,path,new in [
    ('candidate',['candidate','sha256'],'0'*64),
    ('native_claim',['claims','actual_runtime_execution_observed'],True),
    ('donor_claim',['claims','donor_safe_bytes'],6528),
    ('alias_claim',['profiles',0,'claims','all_alternative_readers_excluded'],True),
    ('profile_count',['profiles'],[]),
    ('field_value',['literal_fields',0,'value'],0),
    ('field_address',['literal_fields',1,'address'],0x080A0074),
    ('gpu_store_width',['profiles',0,'store','size'],4),
    ('gpu_arguments',['profiles',0,'arguments'],[72,0]),
    ('gpu_load_register',['profiles',0,'load','register'],0),
    ('gpu_stop',['profiles',0,'stop'],'gpu_flushed'),
    ('callback_field',['profiles',1,'store','address'],0x03003140),
    ('callback_target',['profiles',1,'call','target'],0x080006F6),
    ('callback_return',['profiles',1,'stop'],'before_return'),
    ('literal_reads',['profiles',0,'reads'],[]),
    ('thumb_entry',['profiles',2,'entry'],0x081C96DE),
    ('callee_target',['profiles',2,'opaque_call','target'],0x081C94BA),
    ('callee_sp',['profiles',2,'opaque_call','sp'],0x03007EC4),
    ('callee_return',['profiles',2,'opaque_call','return_pc'],0x081C96EA),
    ('thumb_stop',['profiles',2,'stop'],0x081C96F0),
    ('thumb_reads',['profiles',2,'reads'],[]),
    ('caller_condition',['profiles',0,'caller_condition'],''),
    ('float_condition',['profiles',2,'conditions_ja'],''),
]:
    setattr(Receipt,'test_reject_'+name,profile_rejection(path,new))


def delta_rejection(key,new):
    def test(self):
        with patch.object(m,'PARENT_ID',m.identity(self.parent)):
            delta=self.build();delta[key]=new
            with self.assertRaises(ValueError):m.materialize(self.parent,delta,self.cp,self.raw)
    return test


for key,new in [('classified',788),('unclassified',86),('donor_safe_bytes',6528),('changes',[]),('witnesses',[])]:
    setattr(Receipt,'test_delta_'+key,delta_rejection(key,new))


class Metadata(unittest.TestCase):
    def setUp(self):
        self.run=dict(id=m.RUN,head_sha=m.SOURCE,head_branch=m.BRANCH,path=m.WORKFLOW,event='push',
            run_attempt=1,status='completed',conclusion='success',repository={'full_name':m.REPO},head_repository={'full_name':m.REPO})
        self.jobs=dict(total_count=1,jobs=[dict(id=m.JOB,run_id=m.RUN,head_sha=m.SOURCE,name='typed-origins',
            status='completed',conclusion='success',steps=[dict(number=n,name=s,status='completed',conclusion='success') for n,s in m.STEP_NAMES])])
        self.artifact=dict(id=m.ARTIFACT,name='pr16-typed-origins-public-text',size_in_bytes=m.ZIP_ID['size'],expired=False,
            digest='sha256:'+m.ZIP_ID['sha256'],workflow_run=dict(id=m.RUN,repository_id=1358127462,head_repository_id=1358127462,
            head_branch=m.BRANCH,head_sha=m.SOURCE))

    def test_complete_metadata(self):
        self.assertEqual(m.metadata(self.run,self.jobs,self.artifact)['run_id'],m.RUN)


def metadata_rejection(group,path,new):
    def test(self):
        replace(getattr(self,group),path,new)
        with self.assertRaises(ValueError):m.metadata(self.run,self.jobs,self.artifact)
    return test


for name,group,path,new in [
    ('pending','run',['status'],'in_progress'),('failed','run',['conclusion'],'failure'),
    ('source','run',['head_sha'],'0'*40),('branch','run',['head_branch'],'main'),
    ('attempt','run',['run_attempt'],2),('fork','run',['head_repository','full_name'],'other/repo'),
    ('job_missing','jobs',['total_count'],2),('step_skip','jobs',['jobs',0,'steps',5,'conclusion'],'skipped'),
    ('step_order','jobs',['jobs',0,'steps',0,'number'],2),('expired','artifact',['expired'],True),
    ('zip_digest','artifact',['digest'],'sha256:'+'0'*64),('artifact_run','artifact',['workflow_run','id'],1),
]:
    setattr(Metadata,'test_reject_'+name,metadata_rejection(group,path,new))


if __name__=='__main__':unittest.main()
