#!/usr/bin/env python3
"""元manifest1621+P04予約49+マイペースRockruff1の既存registryをWikiへ接続。"""
from __future__ import annotations
import copy
import io
import json
import os
from pathlib import Path
import re
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
sys.dont_write_bytecode=True
import pr16_learnset_wiki_actions as m
from pr16_candidate_wiki_inputs import Inputs, registries
SELF='scripts/pr16_learnset_wiki_registry_followup.py'
TEST='tests/test_pr16_learnset_wiki_registry_followup.py'
OLD_RUN=35756112654
OLD_HEAD='4893d8275a91080a5c3f930c3fe4bd7fe3c51c5f'
OLD_ARTIFACT={'id':10708915688,'name':'pr16-learnset-wiki-proof','size_in_bytes':5804,
              'digest':'sha256:5061fbdd919a5efc2a6dc4fab5d8146492ceddb94d6d8ee5924f67ca4ba748a2'}
original_read=m.w.read_registry
original_render=m.w.render
original_run=m.run


def normalize(rows,key,count):
    """正式registryの全identityを維持。欠落を補ったりaliasを勝手に生成しない。"""
    m.need(len(rows)==count and [r['id'] for r in rows]==list(range(count))
           and all(type(r['id']) is int for r in rows),'expanded registry ID/order')
    m.need(all(isinstance(r.get('key'),str) and r['key'] for r in rows)
           and len({r['key'] for r in rows})==count,'expanded registry stable key')
    m.need(all(isinstance(r.get('name'),str) and r['name'] for r in rows),'expanded registry display name')
    return {r['id']:dict(copy.deepcopy(r),**{key:r['key'],'display_name':r['name']}) for r in rows}


def read_registry(path,key,count):
    if key!='species_key':return original_read(path,key,count)
    m.need(path==ROOT/'manifests/species_ids.csv' and count==1671,'species registry source')
    inputs=Inputs(ROOT);rows=registries(inputs)['species']
    spec=m.load(m.INPUT/'spec.json')
    for name,binding in inputs.bindings.items():
        m.need(spec['source_bindings'].get(name)==binding,'registry input未結合: '+name)
    return normalize(rows,key,count)


def render(*args,**kwargs):
    files=original_render(*args,**kwargs)
    old=b'scripts/pr16_learnset_wiki_actions.py';new=SELF.encode()
    m.need(files['README.md'].count(old)==2,'Wiki実行入口の二重/欠落')
    files['README.md']=files['README.md'].replace(old,new)
    index=json.loads(files.pop('data/index.json'))
    index['files']={n:m.w.identity(raw) for n,raw in sorted(files.items())}
    index['payload_tree_sha256']=m.w.tree_hash(files)
    files['data/index.json']=m.w.encode(index)
    return files


def command(args,name,env=None):
    # build/checkの独立processにも同じregistry adapterを適用する。
    if len(args)>2 and args[1]=='-B' and args[2]==str(Path(m.__file__).resolve()):
        args=list(args);args[2]=str(ROOT/SELF)
    return original_run(args,name,env)


def prepare():
    m.prepare()
    inputs=Inputs(ROOT);ids=registries(inputs)
    normalize(ids['species'],'species_key',1671)
    spec=m.load(m.INPUT/'spec.json')
    spec['source_bindings'].update(inputs.bindings)
    spec['source_bindings']['scripts/pr16_candidate_wiki_inputs.py']=m.w.identity((ROOT/'scripts/pr16_candidate_wiki_inputs.py').read_bytes())
    m.write(m.INPUT/'spec.json',spec)
    # 最初のrunをfailureのまま保持。候補復元PASSはWiki受入へ昇格しない。
    prior=m.fetch('actions/runs/'+str(OLD_RUN))
    m.need(prior['status']=='completed' and prior['conclusion']=='failure' and prior['head_sha']==OLD_HEAD,'registry failure run')
    meta=m.fetch('actions/artifacts/'+str(OLD_ARTIFACT['id']))
    m.need(all(meta[k]==v for k,v in OLD_ARTIFACT.items()) and not meta['expired']
           and meta['workflow_run']['head_sha']==OLD_HEAD,'registry failure artifact')
    raw=m.fetch('actions/artifacts/'+str(OLD_ARTIFACT['id'])+'/zip',binary=True)
    m.need(m.w.identity(raw)=={'size':OLD_ARTIFACT['size_in_bytes'],'sha256':OLD_ARTIFACT['digest'][7:]},'registry failure ZIP')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        m.need(len(names)==len(set(names))==4 and set(names)=={'build-a.stdout.txt','build-a.stderr.txt','failure.json','restoration.json'},'registry failure ZIP集合')
        for info in z.infolist():
            m.need(not info.is_dir() and info.external_attr>>28!=0xA and info.file_size<200000,'registry failure member')
            data=z.read(info);data.decode('utf-8');(m.PROOF/('prior-'+info.filename)).write_bytes(data)
    failure=m.load(m.PROOF/'prior-failure.json')
    m.need(failure['source_head']==OLD_HEAD and failure['run_id']==str(OLD_RUN)
           and 'manifest ID/key集合不一致' in failure['error'],'registry failure boundary')
    restoration=m.load(m.PROOF/'restoration.json')
    restoration['source_bindings']=spec['source_bindings']
    restoration['prior_failure']={'run_id':OLD_RUN,'source_head':OLD_HEAD,'artifact':OLD_ARTIFACT,
        'conclusion':'failure','wiki_generation_completed':False,'native_runs':0,
        'scope':'保存候補の復元のみ成功。manifest1621を全1671と誤仮定した新Wiki読取を修正。'}
    restoration['registry']={'manifest_species':1621,'p04_form_reservations':49,'rockruff_identity':1,
        'total_species':1671,'existing_registry_implementation_unchanged':True,'inputs':inputs.bindings}
    m.write(m.PROOF/'restoration.json',restoration)


def verify():
    m.verify()
    m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_wiki_registry_followup','-v'],'registry-unit')
    unit=(m.PROOF/'registry-unit.stderr.txt').read_text()
    m.need(re.findall(r'Ran (\d+) tests?',unit)==['8'] and unit.rstrip().endswith('OK'),'registry追加8試験')
    v=m.load(m.PROOF/'verification.json')
    v.update(focused_tests=36,generator_tests=28,registry_tests=8,
             registry=m.load(m.PROOF/'restoration.json')['registry'],prior_failed_run=OLD_RUN)
    m.write(m.PROOF/'verification.json',v)


def record():
    m.record()
    for name in ('design/run_log.md','design/version_log.md'):
        p=ROOT/name;text=p.read_text();old='run'+os.environ['GITHUB_RUN_ID']+'、新28試験PASS'
        m.need(text.count(old)==1,'当回log segment')
        p.write_text(text.replace(old,'run'+os.environ['GITHUB_RUN_ID']+'、新28+registry8=36試験PASS'),encoding='utf-8')
    p=ROOT/m.GUIDE;text=p.read_text();m.need(text.count('新28試験')==1,'guide count')
    p.write_text(text.replace('新28試験','新28+registry8=36試験')+'\n初回run35756112654は候補復元後、manifest1621を全1671と誤仮定してWiki生成前に失敗。原本はfailureのまま保存。既存P04予約49/マイペースRockruff1を含む正式registry読取へ接続し、ID/原本採用/ROMは変更していない。\n',encoding='utf-8')
    state=m.load(ROOT/m.STATE)
    state['source_bindings'][m.GUIDE]=m.w.identity(p.read_bytes())
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':[],
        'reason_ja':'当回Wiki36試験と独立2生成は成功。run全体の完了は後続の記録限定照合で固定する。旧Checksの成功を当回HEADへ流用しない。'}
    state['do_not_repeat'][-1]=state['do_not_repeat'][-1].replace('新28試験','新28+registry8=36試験')
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)


if __name__=='__main__':
    m.CODE|={SELF,TEST}
    m.w.read_registry=read_registry;m.w.render=render;m.run=command
    try:
        args=sys.argv[1:]
        if args and args[0] in ('build','check'):
            m.need(len(args)<=2,'usage build|check [output]');m.cli(args[0],args[1] if len(args)==2 else m.OUTPUT)
        else:
            m.need(len(args)==1,'one action required')
            {'prepare':prepare,'verify':verify,'record':record,'guard':m.guard,
             'paths':lambda:print('\n'.join(sorted(m.owned()|m.CODE)))}[args[0]]()
    except Exception as exc:
        if sys.argv[1:2]!=['check']:
            m.PROOF.mkdir(parents=True,exist_ok=True)
            m.write(m.PROOF/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
                     'run_id':os.environ.get('GITHUB_RUN_ID'),'error':str(exc).replace(str(ROOT),'$REPO')})
        raise
