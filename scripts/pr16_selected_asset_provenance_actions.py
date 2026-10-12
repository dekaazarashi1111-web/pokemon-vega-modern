#!/usr/bin/env python3
"""3起点の入力系譜だけを採取。受入済み候補復元/探索/nativeは実行しない。"""
from __future__ import annotations
import datetime as dt
import io
import json
import os
from pathlib import PurePosixPath
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_selected_asset_provenance as m
import pr16_selected_sound_roots_recover as prior

ROOT,STATE,GUIDE,BRANCH,LOGS=prior.ROOT,prior.STATE,prior.GUIDE,prior.BRANCH,prior.LOGS
read,load,write,snapshot=prior.read,prior.load,prior.write,prior.snapshot
old,a,publication=prior.old,prior.a,prior.publication
TASK='USER-20261012-SELECTED-ASSET-PROVENANCE'
REPORT='content/modernization/pr16_selected_asset_provenance_checkpoint.json'
EVIDENCE='content/modernization/pr16_selected_asset_provenance_evidence'
WF='.github/workflows/pr16-selected-asset-provenance.yml'
CODE={WF,'scripts/pr16_selected_asset_provenance.py','scripts/pr16_selected_asset_provenance_actions.py','tests/test_pr16_selected_asset_provenance.py'}
CP='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
WORK=ROOT/'.local/pr16-selected-asset-provenance'
PUBLIC=WORK/'public'
PHASE='preflight'
COUNTS=dict(rom_reconstructions=0,native_processes=0,accepted_test_reruns=0,new_selected_provenance_measurements=0,
            accepted_sound_measurement_reruns=0,old_xref_or_base_search_reruns=0,old_lz_or_map_reruns=0)


def public(name,value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def receive_parent():
    receipt=publication.accepted_run(38194268192,'6e000ae09ce0d92bca779f57e5b6c0e876a20c65',
        ['保存済み音声測定を再走せず検証して記録','Run actions/upload-artifact@v4'])
    art=a.fetch('actions/artifacts/11722342846')
    m.need(not art['expired'] and art['name']=='pr16-selected-sound-roots-public-text' and
           art['workflow_run']['id']==38194268192 and art['workflow_run']['head_sha']==receipt['source_head'] and
           art['size_in_bytes']==694858 and art['digest']=='sha256:12151a548bbf50fbc5fdaf869021233b251f458fe359012f2ea5ddd2655dca1a','完了音声受領artifact')
    raw=a.fetch('actions/artifacts/11722342846/zip',binary=True)
    m.need(m.identity(raw)==dict(size=694858,sha256=art['digest'][7:]),'完了音声ZIP全hash')
    members=old.zip_members(raw,4000000)
    m.need(set(members)=={'attempt.json','measurement-recovery.json','failure.json','parent-actions-completion.json',
        'pr16_selected_sound_roots_checkpoint.json','result.json','scoped-context.zip','serialization-tests.txt','sound-roots.json','sound-tests.txt','starting-head-checks.json'},'完了音声全11member')
    context=old.zip_members(members['scoped-context.zip'],3000000)
    m.need(len(context)==130 and sum(map(len,context.values()))==2678763 and json.loads(members['result.json'])['commit']==m.BASE_HEAD,'公開130text/commit')
    for name,data in context.items():
        data.decode();m.need(b'\0' not in data and a.git('show',m.BASE_HEAD+':'+name)==data,'公開音声text一致')
    m.need(members['pr16_selected_sound_roots_checkpoint.json']==read(prior.REPORT) and
           members['sound-roots.json']==read(prior.EVIDENCE+'/sound-roots.json'),'保存済み音声原本')
    receipt.update(published_commit=m.BASE_HEAD,artifact={k:art[k] for k in ('id','name','size_in_bytes','digest')},
        members={n:m.identity(v) for n,v in members.items()},public_context_count=130,
        original_measurement_run_conclusion='failure',successful_recovery_does_not_rewrite_failure=True)
    return receipt


def inputs():
    import github_private_environment as bundle
    m.need(old.m.blob(read('config/github_private_environment.json'))=='32913e02fdb71f007d3c65801a9bb5d3f5a6c210' and
           old.m.blob(read('scripts/github_private_environment.py'))=='be1e72a3784b3e17e5fffb43914edf80ed7bbee0','固定入力設定/検証器')
    config=load('config/github_private_environment.json')
    spec=next(r for r in config['archives'] if r['name']=='pokemon-vega-private-env-v1-inputs.zip')
    m.need(spec['size']==104736629 and spec['sha256']=='c7e982c7a6445f41e8926b17c548e64205df736ed83be13dd7676549543a23fe','固定入力archive')
    release=a.fetch('releases/tags/private-environment-v1')
    assets=[r for r in release['assets'] if r['name']==spec['name']]
    m.need(len(assets)==1 and assets[0]['size']==spec['size'],'既存releaseの単一入力asset')
    url=assets[0]['browser_download_url']
    m.need(url=='https://github.com/'+a.REPO+'/releases/download/private-environment-v1/'+spec['name'],'固定同repo download')
    raw=old.download(url+'?run='+os.environ['GITHUB_RUN_ID'],spec['size'])
    m.need(m.identity(raw)=={k:spec[k] for k in ('size','sha256')},'入力ZIP全hash')
    target=WORK/spec['name'];target.write_bytes(raw)
    manifest=bundle._read_and_verify_archive(target,spec)
    entries={r['path']:r for r in manifest['files']}
    names=dict(clean='roms/FireRed_JPN_Rev0_clean.gba',ips='patches/Pokemon_Vega_20180223.ips',vega='roms/Pokemon_Vega_20180223_clean-patched.gba')
    result={};bindings={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        m.need(len(entries)==len(manifest['files']),'manifest重複禁止')
        for item in z.infolist():
            p=PurePosixPath(item.filename)
            m.need(not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and not item.is_dir() and (item.external_attr>>16)&0o170000!=0o120000,'入力ZIP通常member')
        for label,suffix in names.items():
            name='.local/github-private-environment/PRIVATE_INPUTS/'+suffix
            m.need(name in entries,'固定入力member')
            data=z.read(name);want={k:entries[name][k] for k in ('size','sha256')}
            m.need(m.identity(data)==want,'入力member hash')
            result[label]=data;bindings[label]=want
    return result,dict(release_tag=release['tag_name'],asset_id=assets[0]['id'],archive={k:spec[k] for k in ('name','size','sha256')},
        verified_manifest_members=len(entries),selected_input_bindings=bindings,inputs_extracted_to_git=False)


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','same branch first attempt')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists(),'同scope二重実行禁止');PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip() and set(a.git('diff','--name-only',m.BASE_HEAD,head).decode().splitlines())==CODE,'新4sourceのみ')
    m.need(not a.git('ls-files','--',*[p+'/AGENTS.md' for p in ('scripts','tests','docs','design','content','content/modernization','.github','.github/workflows')]).strip(),'追加AGENTS確認')
    state,parent=load(STATE),load(prior.REPORT);lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_ASSET_OWNER_PROVENANCE' and [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0],'固定next/正式数')
    protected={prior.REPORT,CP,'config/github_private_environment.json','scripts/github_private_environment.py'}
    for field in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name,want in parent[field].items():m.need(m.identity(read(name))==want,'全親入力hash');protected.add(name)
    before=snapshot(protected);owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    PHASE='receive-completed-sound-recovery';completion=receive_parent();public('parent-actions-completion.json',completion)
    PHASE='new-provenance-tests';stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_asset_provenance.py'))
    public('provenance-tests.txt',stream.getvalue().encode());m.need(result.wasSuccessful() and result.testsRun==28 and not result.skipped,'新28境界試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,capture_output=True,check=True)
    PHASE='fixed-inputs-and-three-target-provenance';data,receipt=inputs()
    proof=m.measure(data['clean'],data['ips'],data['vega'],load(CP),load(prior.EVIDENCE+'/sound-roots.json'))
    COUNTS['new_selected_provenance_measurements']=1
    proof['input_receipt']=receipt;public('provenance.json',proof)
    PHASE='record-and-readback'
    evidence={EVIDENCE+'/provenance.json':m.encode(proof),EVIDENCE+'/provenance-tests.txt':stream.getvalue().encode(),EVIDENCE+'/parent-actions-completion.json':m.encode(completion)}
    for name,value in evidence.items():write(name,value)
    stable=snapshot(evidence)
    m.need(load(EVIDENCE+'/provenance.json')==proof and stable==snapshot(evidence) and before==snapshot(protected),'read-only保存/全旧原本不変')
    summary=' / '.join(f"0x{r['address']:08X}: current=Vega {r['current_target_equals_vega']}, current=clean {r['current_target_equals_clean']}, owner "+','.join(o['name'] for o in r['modernization']['owners']) for r in proof['rows'])
    goal=('入力系譜の3地点はprovenance.jsonに保存。'+summary+'。配置owner/IPS区間はasset型ではない。'
          '保存した具体的ownerを生成するsourceとasset台帳を読む。音声は既存73群の未対応圧縮WaveData(type1)だけを既存DPCM decoderの正確な消費範囲で照合し、PCM測定を再走しない。'
          '0件なら一致を創作しない。全4byteの実reader束縛後だけ正式型差分へ進む。'
          '今回28試験/入力系譜と旧音声32/保存6/record/base/逆参照/map/ARM/LZ/Wikiは無変更再走しない。正式789/85・選定残6・安全容量0。保存統合は未完。')
    status='SELECTED_ASSET_INPUT_PROVENANCE_BOUND_READER_PENDING'
    report=dict(schema_version=1,task=TASK,status=status,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,
        candidate=m.CANDIDATE,formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
        new_unit_tests=28,actual_asset_reader_proven=False,read_only_check_passed=True,task_graph_passed=True,
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},evidence_bindings={n:m.identity(read(n)) for n in sorted(evidence)},
        preserved_inputs={n:v[0] for n,v in before.items()},observed_head_checks=observed,next_ja=goal,**COUNTS)
    write(REPORT,report);lane.update(status=status,checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_COMPRESSED_ASSET_READER',goal_ja=goal,read_paths=[GUIDE,REPORT,EVIDENCE+'/provenance.json',prior.REPORT,prior.EVIDENCE+'/sound-roots.json'],done_ja='具体的な配置元/圧縮assetから全4byteの実readerを束縛する。型の形だけでは正式化しない。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,new_unit_tests=28,read_only_check_passed=True,task_graph_passed=True,**COUNTS)
    state['recording'].update(task=TASK,status=status,source_head=head,selected_asset_provenance_checkpoint=REPORT,received_sound_roots_completion=EVIDENCE+'/parent-actions-completion.json')
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1);_,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_SELECTED_COMPRESSED_ASSET_READER。'+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode());state['bindings']['CHATGPT_RESUME.md']=dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),'Wiki/所有者判断/安全方針不変');write(STATE,state)
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide+='\n## 選定3地点の入力系譜と現代化owner\n\n'+summary+'。\n\nIPS全recordの上書き順と現115owner境界を検証。値一致は中間の書込不存在証明ではなく、実asset/readerの型受入も未完。\n\n[checkpoint](../'+REPORT+') / [入力系譜](../'+EVIDENCE+'/provenance.json)。\n\n## 次の未完作業\n\n'+goal+'\n';write(GUIDE,guide.encode())
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 3地点の入力系譜とowner境界\n- Version: selected-asset-provenance-v1\n'
        '- Status: DONE（限定系譜検査。実asset reader/保存容量の完成ではない）\n'
        f'- Summary: {summary}。\n- Files changed: 新IPS最終write/owner照合器・28試験・専用Actions、checkpoint/text証拠、固定MD/JSON、両ログ。\n'
        '- Verify: 新28境界試験、入力ZIP全hash/全manifest member、完了音声run38194268192/694858byte ZIP/公開130blob、task graph、保存read-only、受入原本byte/mtime、最終index新規private違反0。全体guard/一般CIの既存失敗は保持。\n'
        '- Scope: 3地点の各4byteだけ。候補復元0/native0/旧音声・探索・受入試験再走0。拡張padding/未所有領域をfreeと推測しない。\n'
        f'- Next: {goal}\n- Commit: この記録を含む単親通常commit。実SHAはActions result/Git履歴。\n'
        '- Network: 同repo PR/ref/Actions/artifact、既存private-environment-v1入力assetのhash検証読取、同branch非force push。ROM/IPS/Saveの原本や生byteは公開せず、入力は変更しない。\n')
    for name in LOGS:
        original=read(name);m.need(('- Task: '+TASK+' /').encode() not in original,'二重追記禁止');write(name,original+block.encode())
    PHASE='final-index-and-nonforce-push';allowed=CODE|set(evidence)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(m.BASE_HEAD,allowed,REPORT);m.need(before==snapshot(protected),'旧原本byte/mtime')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 選定3地点の入力系譜と現owner境界を記録');a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip();m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob一致')
    for name in set(evidence)|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=status,source_head=head,commit=pushed,actions_run_id=int(os.environ['GITHUB_RUN_ID']),**COUNTS))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,**COUNTS))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
