"""公開写像だけの契約試験。native/既受入68試験は実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_public_evidence as p


def sample():
    path='/'+ '/'.join(('home','synthetic-runner','workspace'))
    c={'command':['cc','-Werror','-I'+path+'/include','tools/probe.c','-L'+path+'/lib','-lmgba','-o',path+'/runner'],
       'compiler':'synthetic compiler','executable':{'size':10000,'sha256':'a'*64},'returncode':0,'source_bindings':{'tools/probe.c':{'size':1,'sha256':'b'*64}}}
    return {'compile.json':p.encode(c),'result.txt':b'unchanged\n'}


def private(raw):return ('/'+ 'home/').encode() in raw


class PublicProjection(unittest.TestCase):
    def test_original_unmodified(self):
        files=sample();original=copy.deepcopy(files);p.project(files,3,private);self.assertEqual(files,original)
    def test_only_absolute_arguments_change(self):
        f=sample();out=p.project(f,3,private);a=json.loads(f['compile.json']);b=json.loads(out['compile.public.json']);c=b['projection']
        self.assertEqual({k:v for k,v in a.items() if k!='command'},{k:v for k,v in c.items() if k!='command'})
        self.assertEqual([i for i,(x,y) in enumerate(zip(a['command'],c['command'])) if x!=y],[2,4,7])
        self.assertEqual(b['kind'],'PUBLIC_PROJECTION_NOT_ORIGINAL')
    def test_original_member_hash_retained(self):
        f=sample();out=p.project(f,3,private);v=json.loads(out['compile.public.json']);self.assertEqual(v['original_binding'],p.identity(f['compile.json']))
        for r in v['redactions']:self.assertEqual(r['original_utf8'],p.identity(json.loads(f['compile.json'])['command'][r['argument_index']].encode()))
    def test_unchanged_member_and_mapping(self):
        f=sample();out=p.project(f,3,private);self.assertEqual(out['result.txt'],f['result.txt']);self.assertNotIn('compile.json',out)
        for name,v in json.loads(out['publication.json'])['members'].items():
            self.assertEqual(v['original_binding'],p.identity(f[name]));self.assertEqual(v['published_binding'],p.identity(out[v['published_name']]))
    def test_four_absolute_arguments(self):
        f=sample();v=json.loads(f['compile.json']);v['command'][3]='/synthetic/generated.c';f['compile.json']=p.encode(v)
        self.assertEqual(len(json.loads(p.project(f,4,private)['compile.public.json'])['redactions']),4)
    def test_wrong_count_rejected(self):
        with self.assertRaises(ValueError):p.project(sample(),4,private)
    def test_boolean_count_rejected(self):
        with self.assertRaises(ValueError):p.project(sample(),True,private)
    def test_malformed_command_rejected(self):
        f=sample();v=json.loads(f['compile.json']);v['command'][0]=1;f['compile.json']=p.encode(v)
        with self.assertRaises(ValueError):p.project(f,3,private)
    def test_name_collision_rejected(self):
        f=sample();f['compile.public.json']=b'{}'
        with self.assertRaises(ValueError):p.project(f,3,private)
    def test_other_private_text_not_silently_redacted(self):
        f=sample();f['result.txt']=('/'+ '/'.join(('home','synthetic-runner','private'))).encode()
        with self.assertRaises(ValueError):p.project(f,3,private)
    def test_unknown_compile_field_rejected(self):
        f=sample();v=json.loads(f['compile.json']);v['unverified']=True;f['compile.json']=p.encode(v)
        with self.assertRaises(ValueError):p.project(f,3,private)
    def test_forged_reuse_artifact_rejected(self):
        with self.assertRaises(ValueError):p.reuse_unit(b'not the accepted artifact',lambda n:b'',{'x'})


if __name__=='__main__':unittest.main()
