"""New completion adapter boundaries; does not execute accepted native tests."""
import copy
import io
import json
import tempfile
from unittest.mock import patch
import zipfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_learnset_impact_close as m

class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.p={'run_id':41,'job_id':51,'source_head':'a'*40,'workflow':'.github/workflows/pr16-learnset-egg-gameplay.yml','artifact':{'id':61,'name':'proof','size_in_bytes':100,'digest':'sha256:'+'b'*64}}
        self.r={'id':41,'head_sha':'a'*40,'head_branch':m.m.BRANCH,'path':self.p['workflow'],'status':'completed','conclusion':'success'}
        self.j={'id':51,'run_id':41,'status':'completed','conclusion':'success','steps':[{'number':n,'status':'completed','conclusion':'success'} for n in (5,6,7,8)]}
        self.a=dict(self.p['artifact'],expired=False,workflow_run={'id':41,'head_sha':'a'*40})
    def check(self):m.metadata(self.p,self.r,self.j,self.a)
    def test_completed(self):self.check()
    def test_unfinished(self):
        self.r['status']='in_progress'
        with self.assertRaises(ValueError):self.check()
    def test_failed(self):
        self.r['conclusion']='failure'
        with self.assertRaises(ValueError):self.check()
    def test_wrong_head(self):
        self.r['head_sha']='c'*40
        with self.assertRaises(ValueError):self.check()
    def test_wrong_branch(self):
        self.r['head_branch']='main'
        with self.assertRaises(ValueError):self.check()
    def test_missing_push(self):
        self.j['steps'].pop(2)
        with self.assertRaises(ValueError):self.check()
    def test_upload_skipped(self):
        self.j['steps'][-1]['conclusion']='skipped'
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_step(self):
        self.j['steps'].append(copy.deepcopy(self.j['steps'][0]))
        with self.assertRaises(ValueError):self.check()
    def test_expired_artifact(self):
        self.a['expired']=True
        with self.assertRaises(ValueError):self.check()
    def test_wrong_artifact_source(self):
        self.a['workflow_run']['head_sha']='c'*40
        with self.assertRaises(ValueError):self.check()
    def test_wrong_zip_identity(self):
        with self.assertRaises(ValueError):m.unpack(b'not archive',self.p['artifact'])
    def test_path_traversal(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('../outside.txt','not allowed')
        raw=stream.getvalue();a={'size_in_bytes':len(raw),'digest':'sha256:'+m.identity(raw)['sha256']}
        with self.assertRaises(ValueError):m.unpack(raw,a)

class DependencyTests(unittest.TestCase):
    def validate_dependency(self,group,modified):
        with tempfile.TemporaryDirectory() as td,patch.object(m,'ROOT',Path(td)):
            expected=b'pinned compile input\n';Path(td,'input.c').write_bytes(expected if not modified else b'changed\n')
            v={'run_id':1,'source_head':'a'*40,'candidate':m.m.CANDIDATE,'proof_bindings':{},group:{'input.c':m.identity(expected)}}
            cp=dict(v,public_evidence_bindings={},public_evidence_path='public')
            data={'verification.json':json.dumps(v).encode(),'reflected-head.txt':b'b'*40+b'\n'}
            plan={'run_id':1,'source_head':'a'*40,'reflected_head':'b'*40}
            return m.bound(plan,data,cp)
    def test_egg_compiled_source_mutation(self):
        self.validate_dependency('compiled_sources',False)
        with self.assertRaises(ValueError):self.validate_dependency('compiled_sources',True)
    def test_visual_compiled_source_mutation(self):
        self.validate_dependency('compiled_source_bindings',False)
        with self.assertRaises(ValueError):self.validate_dependency('compiled_source_bindings',True)

class ImageReviewTests(unittest.TestCase):
    def setUp(self):
        self.images={n:{'size':1,'sha256':str(i)*64} for i,n in enumerate(('list','summary','floette-summary','repair/list'))}
        self.review={'reviewed':True,'images':{n:{'identity':b,'observation_ja':'実画像の対象行と文字および枠が正常に描画されていることを確認。'} for n,b in self.images.items()}}
    def test_exact_review(self):m.review_images(self.images,self.review)
    def test_wrong_image_digest(self):
        self.review['images']['repair/list']['identity']={'size':1,'sha256':'f'*64}
        with self.assertRaises(ValueError):m.review_images(self.images,self.review)
    def test_old_wrong_cursor_not_substituted(self):
        self.review['images']['old-list']=self.review['images'].pop('repair/list')
        with self.assertRaises(ValueError):m.review_images(self.images,self.review)

if __name__=='__main__':unittest.main()
