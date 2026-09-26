#!/usr/bin/env python3
"""BG修復の試験証明を合成して再実行を避け、未受入nativeと終端照合を分離。"""
from __future__ import annotations
from copy import deepcopy
import ast
import base64
import io
import json
import os
from pathlib import Path
import re
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_collection_gift_native.py'
TEST='tests/test_pr16_collection_gift_native.py'
REPAIR='content/modernization/pr16_collection_gifts_evidence/36118048058/bg-repair.json'
SCOPE='scripts/pr16_collection_gift_scope.py'
SCOPE_TEST='tests/test_pr16_collection_gift_scope.py'


def need(ok, text):
    if not ok: raise ValueError(text)


def certificate(legacy, repair, current):
    """旧22のうち未変更17 + 修復時7 = 現行24。現在runでの実行件数は0。"""
    need(legacy['unit_passed'] is True and legacy['unit_origin']==36110983368,'旧unit受入原本')
    need(repair['run_id']==36118048058 and repair['status']=='PASS_HOST_BG_REPAIR_NATIVE_PENDING'
         and repair['unit_tests']==7 and repair['unit_skips']==0,'BG修復7試験')
    need(all(repair[k]==0 for k in ('new_native_processes','rom_changes','arm_compiles','host_compiles')),'host修復scope')
    for path, binding in legacy['unit_binding'].items():
        need(binding['sha256']==repair['source_before'][path], '変更前unit入力 '+path)
    need(set(current)==set(repair['source_after'])-{
        '.github/workflows/pr16-supply-followup-20260925.yml'},'現行source集合')
    need(all(current[p]==repair['source_after'][p] for p in current),'修復後入力の変化')
    return dict(schema_version=1, old_suite_run=36110983368, old_suite_tests=22,
                superseded_by_repair_tests=5, unchanged_old_tests=17,
                repair_run=36118048058, repair_tests=7, current_suite_unique_tests=24,
                current_run_unit_executions=0, source_bindings=deepcopy(current),
                meaning_ja='旧22の5件はBG修復時の7件で置換。現行24件を今回実行したという意味ではない。')


def load_runtime():
    import pr16_collection_gift_scope as scope
    c=scope.c;c.CODE|={SELF,TEST,scope.SELF,scope.TEST,'scripts/pr16_collection_gift_step.py','tests/test_pr16_collection_gift_step.py'}
    return scope,c


def evidence_file(c, cp, name):
    path=c.ROOT/c.EVIDENCE/str(cp['run_id'])/name
    raw=path.read_bytes()
    binding=cp.get('public_evidence_bindings',cp['proof_bindings'])[name]
    need(c.identity(raw)==binding, '保存証拠のhash '+name)
    return raw


def execute():
    from pr16_wiki_reconcile import fetch
    scope,c=load_runtime();old=c.load(c.ROOT/c.CP);repair=c.load(c.ROOT/REPAIR)
    legacy=c.load(c.ROOT/c.EVIDENCE/'36110983368/verification.json')
    current={p:c.identity((c.ROOT/p).read_bytes()) for p in repair['source_after'] if p!=c.WF}
    from pr16_collection_gift_step import normalized_controller
    actual_controller=current[c.C]
    current[c.C]=c.identity(normalized_controller((c.ROOT/c.C).read_bytes()))
    cert=certificate(legacy,repair,current)
    cert['pre_barrier_step_fix']=dict(actual_source=actual_controller,guarded_controller_bytes_unchanged=True,reverse_patch_sha256=current[c.C]['sha256'])
    for cp, name, count in ((legacy,'unit.stderr.txt',22),(c.load(c.ROOT/c.EVIDENCE/'36111746469/verification.json'),'scope-unit.stderr.txt',9)):
        raw=evidence_file(c,cp,name)
        need(re.findall(rb'^Ran (\d+) tests? in ',raw,re.M)==[str(count).encode()] and b'\nOK\n' in raw,'保存unit結果')
    prior=c.load(c.ROOT/c.EVIDENCE/'36111746469/verification.json')
    need(c.identity((c.ROOT/SCOPE_TEST).read_bytes())==prior['source_bindings'][SCOPE_TEST], 'scope試験不変')
    original=fetch('contents/'+SCOPE+'?ref='+prior['source_head'])
    raw=base64.b64decode(original['content'])
    need(c.identity(raw)==prior['source_bindings'][SCOPE], 'scope原本hash')
    def body(text,name):
        nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name]
        need(len(nodes)==1,'scope関数一意');return ast.dump(nodes[0],include_attributes=False)
    need(body(raw,'split_cases')==body((c.ROOT/SCOPE).read_text(),'split_cases'),'scope採用判断不変')
    cert['scope_tests']=dict(origin_run=36111746469,inherited_tests=9,new_tests=0,
                             split_cases_ast_unchanged=True,test_binding=prior['source_bindings'][SCOPE_TEST])
    run=fetch('actions/runs/36118048058')
    need(run['head_sha']==repair['input_head'] and run['status']=='completed' and run['conclusion']=='success','修復Actions終端')
    cert['repair_terminal']={k:run[k] for k in ('id','head_sha','status','conclusion')}
    # 正本checkpointを書換えず、検証済み合成cacheを実行への読取りviewに渡す。
    # unit_originは単一実行を偽装せず、二原本の明示的なdictとして保持。
    view=deepcopy(old)
    view.update(unit_binding={p:c.identity((c.ROOT/p).read_bytes()) for p in (
        c.TEST,c.SELF,c.C,'scripts/pr16_collection_gift_bg.py','tests/test_pr16_collection_gift_bg.py')},
        unit_passed=True,unit_origin=dict(old_suite_run=36110983368,repair_run=36118048058,composite=True))
    original_load=c.load
    def cached_load(path):
        return deepcopy(view) if Path(path)==c.ROOT/c.CP else original_load(path)
    def cached_vectors(model,rows,pp):
        index=[json.loads(x,object_pairs_hook=c.egg.strict_pairs) for x in (c.WORK/'payload/consumer-index.jsonl').read_bytes().splitlines()]
        cases,excluded=scope.split_cases(model,rows,pp,index)
        c.write(c.PROOF/'unit-reuse.json',cert)
        c.write(c.PROOF/'scope.json',dict(schema_version=1,new_scope_unit_tests=0,inherited_scope_unit_tests=9,
            candidate=c.CANDIDATE,learning_cases=17,defined_routes=18,excluded=excluded,old_unit_reruns=0,
            policy_changes=0,automatic_fallback=False,all_owners_accepted=False))
        return cases
    c.load=cached_load;scope.scoped_vectors=cached_vectors
    try:scope.execute()
    finally:
        c.load=original_load
        path=c.PROOF/'verification.json'
        if path.exists():
            v=c.load(path);v['unit_reuse']=cert;v['new_cache_validator_tests']=0;v['inherited_cache_validator_tests']=dict(run_id=36118704240,tests=5)
            v['proof_bindings']={p.name:c.identity(p.read_bytes()) for p in c.PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
            c.write(path,v)


def complete():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    scope,c=load_runtime();current();v=c.load(c.ROOT/c.CP)
    need(len(v['accepted'])==17 and not v['failures'] and not v['actions_completion_confirmed'],'17成功の未確定終端のみ')
    need(v['scope']['learning_cases']==17 and v['scope']['defined_routes']==18 and
         [x['species'] for x in v['scope']['excluded']]==[1281] and not v['scope']['all_owners_accepted'],'1281保留')
    runs=[]
    for rid in sorted(set(v['prior_runs']+[v['run_id']])):
        run=fetch('actions/runs/'+str(rid));need(run['status']=='completed' and run['head_branch']==c.m.BRANCH and run['path']==c.WF,'終端run')
        jobs=fetch('actions/runs/'+str(rid)+'/jobs?per_page=100');need(jobs['total_count']==len(jobs['jobs'])==1,'jobページ完全性')
        if rid==v['run_id']:
            need(run['head_sha']==v['source_head'] and run['conclusion']=='success' and
                 all(x['conclusion'] in ('success','skipped') for x in jobs['jobs'][0]['steps']),'最新run成功')
        runs.append(dict({k:run[k] for k in ('id','head_sha','status','conclusion','path')},job_id=jobs['jobs'][0]['id']))
    for p,b in v['public_evidence_bindings'].items():need(c.identity((c.ROOT/v['evidence_path']/p).read_bytes())==b,'保存公開原本')
    for table in ('source_bindings','protected_bindings','compiled_sources'):
        for p,b in v.get(table,{}).items():
            if p!=c.WF:need(c.identity((c.ROOT/p).read_bytes())==b,'入力不変 '+p)
    artifacts=fetch('actions/runs/'+str(v['run_id'])+'/artifacts?per_page=100')
    need(artifacts['total_count']==len(artifacts['artifacts']),'artifactページ完全性')
    matched=[a for a in artifacts['artifacts'] if a['name']=='pr16-collection-gifts-proof']
    need(len(matched)==1 and not matched[0]['expired'],'proof artifact一意/有効')
    artifact=matched[0]
    need(artifact['workflow_run']['head_sha']==v['source_head'],'artifact source')
    raw=fetch('actions/artifacts/'+str(artifact['id'])+'/zip',binary=True)
    need(c.identity(raw)==dict(size=artifact['size_in_bytes'],sha256=artifact['digest'][7:]),'artifact ZIP hash')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist();need(len(names)==len(set(names))<=256,'proof ZIP集合')
        need(all(Path(n).name==n and not n.startswith('.') for n in names),'proof ZIP path')
        for p,b in v['proof_bindings'].items():need(c.identity(z.read(p))==b,'raw artifact member '+p)
        original=json.loads(z.read('verification.json'));need(original['accepted']==v['accepted'] and original['source_head']==v['source_head'],'raw結果不変')
        reflected=z.read('reflected-head.txt').decode().strip()
    child=fetch('git/commits/'+reflected)
    need([p['sha'] for p in child['parents']]==[v['source_head']] and child['message'].startswith(c.TASK+':'),'成果commit親/Task')
    v.update(actions_completion_confirmed=True,terminal_actions=runs,completed_by_source=os.environ['GITHUB_SHA'],
             proof_artifact={k:artifact[k] for k in ('id','name','digest','size_in_bytes')},reflected_head=reflected)
    c.write(c.ROOT/c.CP,v);scope.publish(v,True)
    c.PROOF.mkdir(parents=True,exist_ok=True)
    receipt=dict(task=c.TASK,status='PASS_COLLECTION_BG_TERMINAL',terminal_actions=runs,accepted_cases=17,
        excluded_identity_only=[1281],new_native_processes=0,new_unit_tests=0,host_compiles=0,arm_compiles=0,rom_changes=0,
        reflected_head=reflected,proof_artifact=v['proof_artifact'],issue19_complete=False,release_ready=False)
    c.write(c.PROOF/'completion.json',receipt)
    dest=c.ROOT/c.EVIDENCE/os.environ['GITHUB_RUN_ID'];dest.mkdir(parents=True)
    c.write(dest/'completion.json',receipt)


def main():
    need(len(sys.argv)==2,'execute|record|complete|guard|paths')
    action=sys.argv[1]
    if action=='execute':execute();return
    if action=='complete':complete();return
    scope,c=load_runtime()
    if action=='record':scope.record()
    elif action=='guard':c.guard()
    elif action=='paths':print('\n'.join(sorted(c.owned())))
    else:raise ValueError('未知command')

if __name__=='__main__':main()
