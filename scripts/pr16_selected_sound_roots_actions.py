#!/usr/bin/env python3
"""保存した0件原本から有限音声rootの宣言境界へ進め、非force反映する。"""
from __future__ import annotations
import contextlib
import datetime as dt
import io
import json
import os
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_selected_sound_roots as m
import pr16_selected_asset_records_actions as prior

old, a, publication = prior.old, prior.a, prior.publication
ROOT, STATE, GUIDE, BRANCH, LOGS = prior.ROOT, prior.STATE, prior.GUIDE, prior.BRANCH, prior.LOGS
read, load, write, snapshot = prior.read, prior.load, prior.write, prior.snapshot
TASK = 'USER-20261012-SELECTED-SOUND-ROOTS'
REPORT = 'content/modernization/pr16_selected_sound_roots_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_selected_sound_roots_evidence'
CODE = {'scripts/pr16_selected_sound_roots.py','scripts/pr16_selected_sound_roots_actions.py',
        'tests/test_pr16_selected_sound_roots.py','.github/workflows/pr16-selected-sound-roots.yml'}
WORK = ROOT/'.local/pr16-selected-sound-roots'
PUBLIC = WORK/'public'
PHASE = 'preflight'
COUNTS = dict(rom_reconstructions=0,native_processes=0,accepted_test_reruns=0,
    accepted_inventory_reruns=0,prior_lz_search_reruns=0,map_probe_reruns=0,arm_layout_recompiles=0,
    new_sound_root_measurements=0,accepted_xref_passes_replayed=0)


def public(name, value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def receive_parent():
    result=publication.accepted_run(38182076122,'f8a4ee07c9589d992a57842f935f7816d5ea6b54',
        ['整列2起点のrecord候補を検証して記録','Run actions/upload-artifact@v4'])
    art=a.fetch('actions/artifacts/11717778719')
    m.need(art['name']=='pr16-selected-asset-records-public-text' and not art['expired'] and
        art['workflow_run']['id']==38182076122 and art['workflow_run']['head_sha']==result['source_head'] and
        art['size_in_bytes']==480414 and art['digest']=='sha256:ace55a53580609aaedaf9e76957767bd69569264f3e6b406147776b4d24875a0','前回artifact identity')
    raw=a.fetch('actions/artifacts/11717778719/zip',binary=True)
    m.need(m.identity(raw)==dict(size=480414,sha256=art['digest'][7:]),'前回ZIP全hash')
    members=old.zip_members(raw)
    m.need(set(members)=={'attempt.json','record-candidates.json','parent-actions-completion.json',
        'pr16_selected_asset_records_checkpoint.json','result.json','starting-head-checks.json','scoped-context.zip','record-tests.txt'},'前回全8member')
    context=old.zip_members(members['scoped-context.zip'])
    m.need(len(context)==115 and json.loads(members['result.json'])['commit']==m.BASE_HEAD,'前回115text/公開commit')
    for name,data in context.items():
        data.decode('utf-8');m.need(b'\0' not in data and a.git('show',m.BASE_HEAD+':'+name)==data,'前回公開blob')
    for name,path in [('pr16_selected_asset_records_checkpoint.json',prior.REPORT),
                      ('record-candidates.json',prior.EVIDENCE+'/record-candidates.json')]:
        m.need(members[name]==read(path),'前回原本一致')
    result.update(artifact={k:art[k] for k in ('id','name','digest','size_in_bytes')},
        members={n:m.identity(v) for n,v in members.items()},published_commit=m.BASE_HEAD,
        context_bindings={n:m.identity(v) for n,v in context.items()},accepted_test_reruns=0)
    return result


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and
        os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回限定')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists(),'同scope二重測定禁止')
    PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip() and
        set(a.git('diff','--name-only',m.BASE_HEAD,head).decode().splitlines())==CODE,'新4sourceのみ')
    m.need(not a.git('ls-files','--',*[p+'/AGENTS.md' for p in
        ('scripts','tests','docs','design','content','content/modernization','.github','.github/workflows')]).strip(),'追加AGENTS確認')
    state,parent=load(STATE),load(prior.REPORT)
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_ASSET_RECORD_READER' and
        [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0],'現行next/789/85/6/0')
    owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected={prior.REPORT}
    for key in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name,want in parent[key].items():
            m.need(m.identity(read(name))==want,'継承原本hash: '+name);protected.add(name)
    before=snapshot(protected)
    PHASE='receive-completed-parent-without-replay'
    completion=receive_parent();starting=prior.prior.prior.measured.previous.runs(m.BASE_HEAD)
    public('parent-actions-completion.json',completion)
    PHASE='new-sound-root-tests'
    stream=io.StringIO()
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_sound_roots.py'))
    public('sound-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==32 and not tests.skipped,'新32試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='fixed-symbol-input'
    spec=old.m.SYMBOL_SOURCE
    symbols=old.download('https://raw.githubusercontent.com/'+spec['repository']+'/'+spec['commit']+'/'+spec['path'],5000000)
    m.need(m.identity(symbols)=={k:spec[k] for k in ('size','sha256')} and old.m.blob(symbols)==spec['git_blob'],'固定JP symbol全hash')
    sources={}
    for name,blob in {'include/gba/m4a_internal.h':'609259b032a32c932fc1a9f54d0e3afda70c02dc',
                      'src/sound.c':'9060aa513d2946d5a59c34f24658da96e0ab6a8e'}.items():
        source=old.download('https://raw.githubusercontent.com/pret/pokefirered/'+old.m.SOURCE+'/'+name,300000)
        m.need(old.m.blob(source)==blob,'固定公開音声source全blob')
        sources[name]=dict(repository='pret/pokefirered',commit=old.m.SOURCE,path=name,git_blob=blob,**m.identity(source))
    PHASE='one-new-scope-candidate-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    COUNTS['rom_reconstructions']=1;public('attempt.json',COUNTS)
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        raw,cp=reconstruction.reconstruct()
    m.need(cp['candidate']==m.CANDIDATE and m.identity(raw)==m.CANDIDATE,'全候補/既存owner配置')
    PHASE='bounded-sound-root-declared-extents'
    proof=m.measure(raw,symbols,load(prior.EVIDENCE+'/record-candidates.json'))
    COUNTS['new_sound_root_measurements']=1
    proof.update(public_sources=sources,public_symbol_source=spec,placement_identity=m.identity(m.encode(cp['placement'])))
    public('sound-roots.json',proof)
    evidence={EVIDENCE+'/sound-roots.json':proof,EVIDENCE+'/parent-actions-completion.json':completion,
        EVIDENCE+'/sound-tests.txt':stream.getvalue().encode(),EVIDENCE+'/starting-head-checks.json':starting}
    for name,value in evidence.items():write(name,value)
    stable=snapshot(evidence)
    m.need(load(EVIDENCE+'/sound-roots.json')==proof and stable==snapshot(evidence),'保存後read-only')
    m.need(before==snapshot(protected),'全受入原本byte/mtime不変')
    count=proof['match_count']
    covered=sorted({t for row in proof['inspection']['matches'] for t in row['covered_targets']})
    goal=(f'有限音声rootから非圧縮PCM宣言範囲への一致{count}件、対象'+','.join(f'0x{t:08X}' for t in covered)+'。'
        'sound-roots.jsonの実bank/record/WaveDataとconsumer_frontierから、現命令のtable選択と全4byteの実readerを束縛する。'
        '一致0件なら一致候補を創作せず、保存済み0件を踏まえ他の実asset起点へ進む。'
        '宣言範囲/literal形だけでは正式型にしない。今回32試験/音声root測定と旧record/base/逆参照/map/ARM/LZ/Wikiを無変更再走しない。'
        '正式789/85・選定残6・安全容量0。窓外跨り/間接参照/退役移管/heap/controller/局所Saveは未完。')
    status='SELECTED_SOUND_ROOT_EXTENTS_BOUND_READER_PENDING'
    report=dict(schema_version=1,task=TASK,status=status,source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,candidate=m.CANDIDATE,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,new_unit_tests=32,
        match_count=count,covered_targets=covered,
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        evidence_bindings={n:m.identity(read(n)) for n in sorted(evidence)},preserved_inputs={n:v[0] for n,v in before.items()},
        actual_asset_reader_proven=False,read_only_check_passed=True,task_graph_passed=True,
        observed_head_checks=observed,starting_head_checks=starting,next_ja=goal,**COUNTS)
    write(REPORT,report)
    lane.update(status=status,checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_SOUND_ROOT_READER',goal_ja=goal,read_paths=[GUIDE,REPORT,EVIDENCE+'/sound-roots.json',prior.REPORT],
        done_ja='保存した具体的参照元から全4byteの実readerを束縛し、完了run受領後に正式型差分だけ追加する。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=32,read_only_check_passed=True,task_graph_passed=True,**COUNTS)
    state['recording'].update(task=TASK,status=status,source_head=head,selected_sound_roots_checkpoint=REPORT,
        received_selected_asset_records_completion=EVIDENCE+'/parent-actions-completion.json')
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1);_,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は '+'SAVE_CAPACITY_SELECTED_SOUND_ROOT_READER'+'。'+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode())
    state['bindings']['CHATGPT_RESUME.md']=dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),'Wiki/承認/安全方針不変')
    write(STATE,state)
    summary=(f'保存record/base原本は構造体候補0件と確認。別の有限音声root→ToneData→非圧縮WaveDataを実装し、一致{count}件。'
        '宣言sample範囲・bank/record/全hashと現命令literal形を保存。実reader/自然入口の受入ではない。'
        '新32境界試験・task graph PASS、新scope候補復元1。native/旧受入/旧逆参照/base/map/LZ/Wiki再走0。')
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide+='\n## 有限音声rootとPCM宣言境界\n\n'+summary+'\n\n[checkpoint](../'+REPORT+') / [音声root](../'+EVIDENCE+'/sound-roots.json)。\n\n## 次の未完作業\n\n'+goal+'\n'
    write(GUIDE,guide.encode())
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 有限音声rootとPCM宣言境界\n'
        '- Version: selected-sound-roots-v1\n- Status: DONE（新しい音声root検査を実装・検証。実reader/保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 新検査器/32試験/専用Actions、checkpoint/text証拠、固定MD/JSON、両ログ。\n'
        '- Verify: 新32人工境界試験、前回完了run/ZIP全hash/公開115blob、受入原本byte/mtime、task graph、最終index新規private違反0。\n'
        '- Boundary: 音声root候補から有限song512/cry512/bank128key。公開symbol/命令形と宣言範囲は実reader受入でない。圧縮/PSG/未知flagは対象外。全体guard/一般CIの既存失敗は未解消。\n'
        f'- Next: {goal}\n- Commit: この記録を含む単親通常commit。実SHAはActions result/Git履歴。\n'
        '- Network: 同repo PR/ref/Actions/artifact、固定ComplexRobot/frlg-sym c04a315のJP symbol、固定pret/pokefirered c75f352のm4a_internal.h/sound.c、既存private入力復元、同branch非force push。ROM/save/生byte列を追加公開しない。\n')
    for name in LOGS:
        original=read(name);m.need(('- Task: '+TASK+' /').encode() not in original,'同task二重追記禁止')
        write(name,original+block.encode())
    PHASE='final-index-and-nonforce-push'
    allowed=CODE|set(evidence)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(m.BASE_HEAD,allowed,REPORT)
    m.need(before==snapshot(protected),'全受入原本byte/mtime不変')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 有限音声rootのPCM宣言境界と実reader未完を記録');a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob一致')
    for name in set(evidence)|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=status,source_head=head,commit=pushed,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        match_count=count,covered_targets=covered,**COUNTS))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,**COUNTS))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
