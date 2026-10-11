#!/usr/bin/env python3
"""新規originだけを測定し、検証済みtextと固定再開点を同branchへ反映する。"""
from __future__ import annotations
import contextlib
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_selected_asset as m
import pr16_berry_origin_actions as old

ROOT, a, publication = old.ROOT, old.a, old.publication
read, load, write, snapshot = old.read, old.load, old.write, old.snapshot
STATE, GUIDE, BRANCH, LOGS = old.STATE, old.GUIDE, old.BRANCH, old.LOGS
TASK = 'USER-20261012-SELECTED-ASSET-0880FA64'
REPORT = 'content/modernization/pr16_selected_asset_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_selected_asset_evidence'
PARENT = 'content/modernization/pr16_berry_lz_type_checkpoint.json'
WINDOW = 'content/modernization/pr16_berry_lz_type_evidence/window-progress.json'
CODE = {'scripts/pr16_selected_asset.py','scripts/pr16_selected_asset_actions.py',
        'tests/test_pr16_selected_asset.py','.github/workflows/pr16-selected-asset.yml'}
WORK = ROOT/'.local/pr16-selected-asset'
PUBLIC = WORK/'public'
PHASE = 'preflight'
ATTEMPT = dict(rom_reconstructions=0,native_processes=0,accepted_test_reruns=0,full_rom_scans=0)
SOURCES = {
    'src/data/tilesets/headers.h':'676bd21050e753822a61aa127310c338938c3c00',
    'include/global.fieldmap.h':'e2828ec0cb1439718e830fbef4366770b3b77b1c',
    'data/multiboot_pokemon_colosseum.s':'a5f894908ad8d95031cfe017bde1ada72b70c2ac',
    'src/fieldmap.c':None,
}


def public(name, value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def runs(head):
    value=a.fetch('actions/runs?head_sha='+head+'&per_page=100')
    m.need(value['total_count']==len(value['workflow_runs']), 'Actions未取得ページ')
    return dict(source_head=head,all_ci_green_claimed=False,
        runs=[{k:r[k] for k in ('id','name','head_sha','path','event','status','conclusion')} for r in value['workflow_runs']])


def receive_parent():
    receipt=publication.accepted_run(38130698828,'0cacf5317bd1ce1209d258129ddff1f24b3b3b03',
        ['完了LZ原本から単一型差分だけを検証して記録','Run actions/upload-artifact@v4'])
    art=a.fetch('actions/artifacts/11698989329')
    m.need(art['name']=='pr16-berry-lz-type-public-text' and not art['expired'] and
        art['workflow_run']['head_sha']==receipt['source_head'] and art['workflow_run']['id']==receipt['id'] and
        art['digest']=='sha256:339c4e5391fcc12e8208586847595c69726c60f798791d818b9f2d1770a6eee4' and
        art['size_in_bytes']==287148, '前回成果物identity')
    raw=a.fetch('actions/artifacts/11698989329/zip',binary=True)
    m.need(m.identity(raw)==dict(size=art['size_in_bytes'],sha256=art['digest'][7:]), '前回ZIP全hash')
    members=old.zip_members(raw)
    m.need(set(members)=={'pr16_berry_lz_type_checkpoint.json','reference-chain.json',
        'receipt-actions-completion.json','result.json','scoped-context.zip','type-tests.txt',
        'unknown-frontier.json','window-progress.json'}, '前回全8member')
    context=old.zip_members(members['scoped-context.zip'])
    m.need(len(context)==68 and json.loads(members['result.json'])['commit']==m.BASE, '前回68text/公開commit')
    for name,data in context.items():
        data.decode('utf-8');m.need(b'\0' not in data and a.git('show',m.BASE+':'+name)==data,'前回公開blob')
    m.need(members['pr16_berry_lz_type_checkpoint.json']==read(PARENT),'前回checkpoint原本')
    receipt.update(artifact={k:art[k] for k in ('id','name','digest','size_in_bytes')},
        members={n:m.identity(v) for n,v in members.items()},published_commit=m.BASE,
        context_bindings={n:m.identity(v) for n,v in context.items()},accepted_test_reruns=0)
    return receipt


def sources():
    data, bindings = {}, {}
    commit=old.m.SOURCE
    for name,fixed in SOURCES.items():
        if fixed is None:
            meta=json.loads(old.download('https://api.github.com/repos/pret/pokefirered/contents/'+name+'?ref='+commit,200000))
            m.need(meta['type']=='file' and meta['path']==name, '固定source metadata')
            fixed=meta['sha']
        raw=old.download('https://raw.githubusercontent.com/pret/pokefirered/'+commit+'/'+name,1000000)
        m.need(old.m.blob(raw)==fixed,'固定source全blob: '+name)
        data[name]=raw
        bindings[name]=dict(repository='pret/pokefirered',commit=commit,path=name,git_blob=fixed,**m.identity(raw))
    spec=old.m.SYMBOL_SOURCE
    raw=old.download('https://raw.githubusercontent.com/'+spec['repository']+'/'+spec['commit']+'/'+spec['path'],5000000)
    m.need(m.identity(raw)=={k:spec[k] for k in ('size','sha256')} and old.m.blob(raw)==spec['git_blob'],'全JPsymbol identity')
    names=set(re.findall(r'const struct Tileset (gTileset_\w+)',data['src/data/tilesets/headers.h'].decode()))
    names.update(re.findall(r'\b(?:Load|Copy|Draw|Decompress)\w*Tileset\w*',data['src/fieldmap.c'].decode()))
    names.update({'LZ77UnCompVram','LZ77UnCompWram','gMultiBootProgram_PokemonColosseum_Start'})
    return data,bindings,old.m.parse_symbols(raw,names)


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and
        os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回限定')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists(),'同scope二重測定禁止')
    PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip() and
        set(a.git('diff','--name-only',m.BASE,head).decode().splitlines())==CODE,'新4sourceのみ')
    m.need(not a.git('ls-files','--',*[p+'/AGENTS.md' for p in ('scripts','tests','docs','design','content','content/modernization','.github','.github/workflows')]).strip(),'追加AGENTS読取が必要')
    state,parent,window=load(STATE),load(PARENT),load(WINDOW)
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_NEXT_SELECTED_ORIGIN_BINDING' and
        [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0] and
        window['next_address']==m.HIT,'現行next/789/85/6/0')
    owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected={PARENT,WINDOW,old.SYMBOLS}
    for field in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name,want in parent[field].items():
            m.need(m.identity(read(name))==want,'継承入力hash: '+name);protected.add(name)
    before=snapshot(protected)
    PHASE='receive-completed-parent-without-replay'
    prior=receive_parent();baseline_checks=runs(m.BASE)
    PHASE='new-boundary-tests'
    stream=io.StringIO()
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_asset.py'))
    public('asset-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==30 and not tests.skipped,'新30試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='fixed-public-source-bindings'
    data,bindings,symbols=sources()
    PHASE='one-new-scope-candidate-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions']=1;public('attempt.json',ATTEMPT)
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        raw,cp=reconstruction.reconstruct()
    m.need(cp['candidate']==m.CANDIDATE and m.identity(raw)==m.CANDIDATE,'全候補/既存owner配置')
    m.need(m.identity(m.section(raw,0x08000000,m.HIT,4))==m.HIT_ID,'対象4byte')
    PHASE='bounded-asset-and-descriptor-measurement'
    start=m.HIT-m.RADIUS
    region=m.section(raw,0x08000000,start,2*m.RADIUS+4)
    parsed=m.candidates(region,start,m.HIT)
    descriptors=m.bind_descriptors(raw,symbols['found'],parsed['matches'])
    values={str(r['start']):r['start'] for r in parsed['matches']}
    values.update({r['symbol']:r['address'] for r in descriptors['matching_descriptors']})
    consumers={}
    for name,s in symbols['found'].items():
        if name.startswith('g'):continue
        lo=s['address']&~1;hi=s['following_distinct_address']
        if hi is None or not 0<hi-lo<=16384:continue
        code=m.section(raw,0x08000000,lo,hi-lo)
        consumers[name]=dict(symbol=s,code_identity=m.identity(code),
            literal_shapes=old.m.literal_occurrences(code,lo,values),actual_consumer_proven=False)
    selected=next(r for r in load(old.SYMBOLS)['origins'] if r['hit']['address']==m.HIT)
    proof=dict(schema_version=1,candidate=m.CANDIDATE,origin=dict(address=m.HIT,**m.HIT_ID),
        saved_symbol_neighborhood=selected,public_sources=bindings,public_symbol_source=old.m.SYMBOL_SOURCE,
        selected_symbols=symbols,lz_candidates=parsed,tileset_descriptors=descriptors,consumer_frontier=consumers,
        placement_identity=m.identity(m.encode(cp['placement'])),
        classification_changes=0,actual_consumer_proven=False,donor_safe_bytes=0,
        limitations_ja=['近傍labelをasset境界としない。構文候補とdescriptor一致は実caller/reader受入ではない。',
          '整列headerを前64KiBから探した有限結果。未発見をowner不在/全ROM完全性へ昇格しない。'])
    names={EVIDENCE+'/bounded-asset.json':proof,EVIDENCE+'/parent-actions-completion.json':prior,
        EVIDENCE+'/asset-tests.txt':stream.getvalue().encode(),EVIDENCE+'/starting-head-checks.json':baseline_checks}
    for name,value in names.items():write(name,value)
    stable=snapshot(names)
    m.need(load(EVIDENCE+'/bounded-asset.json')==proof and stable==snapshot(names),'保存後read-only')
    m.need(before==snapshot(protected),'全受入原本byte/mtime不変')
    count=len(parsed['matches']);bound=len(descriptors['matching_descriptors'])
    goal=(f'0x0880FA64の保存済みLZ構文候補{count}件/一致Tileset descriptor{bound}件とconsumer frontierから、'
        '実asset owner/実caller/readerへ有限に結ぶ。今回の前後64KiB探索/30試験は再走せず保存hashを継承する。'
        '正式789/85・選定残6・安全容量0。窓外跨りread/間接参照/旧owner退役・移管/heap/controller/局所Saveは未完。')
    report=dict(schema_version=1,task=TASK,status='SELECTED_ASSET_BOUNDED_READER_PENDING',source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,candidate=m.CANDIDATE,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
        new_unit_tests=30,source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        evidence_bindings={n:m.identity(read(n)) for n in sorted(names)},preserved_inputs={n:v[0] for n,v in before.items()},
        lz_candidates=count,matching_tileset_descriptors=bound,read_only_check_passed=True,task_graph_passed=True,
        observed_head_checks=observed,starting_head_checks=baseline_checks,next_ja=goal,**ATTEMPT)
    write(REPORT,report)
    lane.update(status=report['status'],checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_ASSET_ACTUAL_READER',goal_ja=goal,
        read_paths=[GUIDE,REPORT,EVIDENCE+'/bounded-asset.json',WINDOW],done_ja='実consumerと完了Actionsを束縛した範囲だけ正式差分へ受領する。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']={k:report[k] for k in ('task','source_head','actions_run_id','actions_completion_confirmed',
        'new_unit_tests','read_only_check_passed','task_graph_passed','formal_classified','formal_unclassified','donor_safe_bytes',*ATTEMPT)}
    state['recording'].update(task=TASK,status=report['status'],source_head=head,selected_asset_checkpoint=REPORT)
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1);_,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_SELECTED_ASSET_ACTUAL_READER。'+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode())
    state['bindings']['CHATGPT_RESUME.md']=dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),'Wiki/承認/安全方針不変')
    write(STATE,state)
    summary=f'対象0880FA64の全候補SHA/4byteを束縛し、前後64KiBの有限探索でLZ構文候補{count}件、一致Tileset descriptor{bound}件を保存。実reader受入や型分類増加は未主張。新30試験、候補復元1、native/旧受入再走0。'
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide+='\n## 0880FA64の有限asset候補とdescriptor\n\n'+summary+f'\n\n[限定証拠](../{EVIDENCE}/bounded-asset.json) / [checkpoint](../{REPORT})。前回Berry型登録Actionsの全8member/68text/公開commitを受領。\n\n## 次の未完作業\n\n'+goal+'\n'
    write(GUIDE,guide.encode())
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 次の選定originのasset境界\n'
        '- Version: selected-asset-v1\n- Status: DONE（有限測定。実reader/保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 専用検証器/30試験/Actions、限定証拠、固定引継ぎMD/JSON、両ログ。\n'
        '- Verify: 新30境界試験、全候補/配置/対象hash、固定公開source全blob、前回Actions/全artifact、保存後read-only、task graph、限定最終index。\n'
        '- Boundary: 正式789/85・残6・安全容量0。全体CI green/全story/ROM配布受入は非主張。\n'
        f'- Next: {goal}\n- Commit: この記録を含む単親通常commit。実SHAはActions result/Git履歴。\n'
        '- Network: 同repo PR/ref/Actions/artifact/既存private入力と同branch非force push。固定pret/pokefirered '+old.m.SOURCE+
        ' のfieldmap/Tileset/Colosseum sourceと固定JPsymbolを参照。検索語 gTileset_General。ROM/save/生byte列の公開なし。\n')
    for name in LOGS:
        previous=read(name);m.need(('- Task: '+TASK+' /').encode() not in previous,'同task二重追記禁止');write(name,previous+block.encode())
    PHASE='final-index-and-nonforce-push'
    allowed=CODE|set(names)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(m.BASE,allowed,REPORT)
    m.need(before==snapshot(protected),'push前原本保全')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 限定asset境界と次のreaderを記録');a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob一致')
    for name in set(names)|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=report['status'],source_head=head,commit=pushed,lz_candidates=count,
        matching_tileset_descriptors=bound,actions_run_id=int(os.environ['GITHUB_RUN_ID']),**ATTEMPT))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,attempt=ATTEMPT))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
