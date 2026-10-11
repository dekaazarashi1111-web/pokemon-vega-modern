#!/usr/bin/env python3
"""後継ABIと実map lookupの新scopeを検証・記録し、許可branchへ非force反映する。"""
from __future__ import annotations
import contextlib
import datetime as dt
import io
import json
import os
import re
import struct
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_selected_map_asset as m
import pr16_selected_asset_actions as previous

old = previous.old
ROOT, a, publication = old.ROOT, old.a, old.publication
read, load, write, snapshot = old.read, old.load, old.write, old.snapshot
STATE, GUIDE, BRANCH, LOGS = old.STATE, old.GUIDE, old.BRANCH, old.LOGS
TASK = 'USER-20261012-SELECTED-MAP-ASSET-ABI'
REPORT = 'content/modernization/pr16_selected_map_asset_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_selected_map_asset_evidence'
CODE = {'scripts/pr16_selected_map_asset.py','scripts/pr16_selected_map_asset_actions.py',
        'tests/test_pr16_selected_map_asset.py','.github/workflows/pr16-selected-map-asset.yml'}
WORK = ROOT/'.local/pr16-selected-map-asset'
PUBLIC = WORK/'public'
PHASE = 'preflight'
ATTEMPT = dict(rom_reconstructions=0,native_processes=0,accepted_test_reruns=0,
               full_rom_scans=0,prior_lz_search_reruns=0)


def public(name, value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def receive_parent():
    receipt=publication.accepted_run(38173141350,'1fafda9f6f4c10d5a597287fc001333d4f5f67dd',
        ['選定originだけを限定測定して記録','Run actions/upload-artifact@v4'])
    art=a.fetch('actions/artifacts/11715195931')
    m.need(art['name']=='pr16-selected-asset-public-text' and not art['expired'] and
        art['workflow_run']['head_sha']==receipt['source_head'] and art['workflow_run']['id']==receipt['id'] and
        art['digest']=='sha256:85bb6ce9fecd9d9252dd390de9caf155ed4ba774b93f40a0832546d7022fd48b' and
        art['size_in_bytes']==317432,'前回artifact identity')
    raw=a.fetch('actions/artifacts/11715195931/zip',binary=True)
    m.need(m.identity(raw)==dict(size=art['size_in_bytes'],sha256=art['digest'][7:]),'前回ZIP全hash')
    members=old.zip_members(raw)
    m.need(set(members)=={'asset-tests.txt','attempt.json','bounded-asset.json','parent-actions-completion.json',
        'pr16_selected_asset_checkpoint.json','result.json','scoped-context.zip','starting-head-checks.json'},'前回全8member')
    context=old.zip_members(members['scoped-context.zip'])
    m.need(len(context)==77 and json.loads(members['result.json'])['commit']==m.BASE_HEAD,'前回77text/公開commit')
    for name,data in context.items():
        data.decode('utf-8');m.need(b'\0' not in data and a.git('show',m.BASE_HEAD+':'+name)==data,'前回公開blob')
    m.need(members['pr16_selected_asset_checkpoint.json']==read(previous.REPORT),'前回checkpoint原本')
    receipt.update(artifact={k:art[k] for k in ('id','name','digest','size_in_bytes')},
        members={n:m.identity(v) for n,v in members.items()},published_commit=m.BASE_HEAD,
        context_bindings={n:m.identity(v) for n,v in context.items()},accepted_test_reruns=0,
        limitations_ja='旧run完了を受領。旧descriptor decoderのABI誤りや実reader不成立を成功へ読み替えない。')
    return receipt


def sources_and_layout(saved):
    data,bindings={},{}
    for name in ('include/global.fieldmap.h','src/fieldmap.c','src/overworld.c'):
        fixed=(saved['public_sources'][name]['git_blob'] if name in saved['public_sources'] else
               '339014da46ae8543143edc99ab72bf7496203a0d')
        raw=old.download('https://raw.githubusercontent.com/pret/pokefirered/'+old.m.SOURCE+'/'+name,300000)
        m.need(old.m.blob(raw)==fixed,'固定公開source全blob: '+name)
        data[name]=raw
        bindings[name]=dict(repository='pret/pokefirered',commit=old.m.SOURCE,path=name,git_blob=fixed,**m.identity(raw))
    spec=old.m.SYMBOL_SOURCE
    raw=old.download('https://raw.githubusercontent.com/'+spec['repository']+'/'+spec['commit']+'/'+spec['path'],5000000)
    m.need(m.identity(raw)=={k:spec[k] for k in ('size','sha256')} and old.m.blob(raw)==spec['git_blob'],'固定JP symbol全hash')
    symbols=old.m.parse_symbols(raw,m.NAMES)
    m.need(m.LOOKUP in symbols['found'],'必要な実lookup symbol')
    header=data['include/global.fieldmap.h'].decode()
    blocks=[]
    for name in ('Tileset','MapLayout'):
        found=re.findall(r'struct '+name+r'\n\{.*?\n\};',header,re.S)
        m.need(len(found)==1,'一意の固定公開構造体抽出');blocks.append(found[0])
    fields={
        'tileset_size':'sizeof(struct Tileset)', 'compressed':'__builtin_offsetof(struct Tileset,isCompressed)',
        'secondary':'__builtin_offsetof(struct Tileset,isSecondary)',
        **{n:'__builtin_offsetof(struct Tileset,'+f+')' for n,f in
           dict(tiles='tiles',palettes='palettes',metatiles='metatiles',callback='callback',attributes='metatileAttributes').items()},
        'map_layout_size':'sizeof(struct MapLayout)',
        **{n:'__builtin_offsetof(struct MapLayout,'+f+')' for n,f in
           dict(width='width',height='height',border='border',map='map',primary='primaryTileset',
                secondary_tileset='secondaryTileset',border_width='borderWidth',border_height='borderHeight').items()}}
    shim='typedef unsigned char u8, bool8; typedef unsigned short u16; typedef unsigned int u32; typedef int s32; typedef void (*TilesetCB)(void);\n'
    source=(shim+'\n'.join(blocks)+'\nconst unsigned int layout[] = {'+','.join(fields[k] for k in m.LAYOUT)+'};\n').encode()
    work=WORK/'abi';work.mkdir();(work/'layout.c').write_bytes(source)
    subprocess.run(['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-std=c11','-Wall','-Wextra','-Werror',
                    '-c',str(work/'layout.c'),'-o',str(work/'layout.o')],check=True,capture_output=True)
    subprocess.run(['arm-none-eabi-objcopy','-O','binary','--only-section=.rodata',str(work/'layout.o'),str(work/'layout.bin')],check=True,capture_output=True)
    binary=(work/'layout.bin').read_bytes()
    m.need(len(binary)==len(m.LAYOUT)*4,'ARM layout閉extent')
    layout=m.checked_layout(dict(zip(m.LAYOUT,struct.unpack('<'+'I'*len(m.LAYOUT),binary))))
    return symbols,layout,dict(public_sources=bindings,public_symbol_source=spec,symbols=symbols,
        compile_source_identity=m.identity(source),compiled_rodata_identity=m.identity(binary),
        compiler_version=subprocess.check_output(['arm-none-eabi-gcc','-dumpfullversion'],text=True).strip(),
        layout=layout,shim_semantics_ja='固定公開構造体本文を無変更で抽出しARMv4Tで配置。ゲーム本体の再コンパイルではない。')


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
    m.need(not a.git('ls-files','--',*[p+'/AGENTS.md' for p in ('scripts','tests','docs','design','content','content/modernization','.github','.github/workflows')]).strip(),'追加AGENTS読取が必要')
    state,parent,saved=load(STATE),load(previous.REPORT),load(previous.EVIDENCE+'/bounded-asset.json')
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_ASSET_ACTUAL_READER' and
        [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0],'現行next/789/85/6/0')
    owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected={previous.REPORT,previous.WINDOW,'scripts/pr16_dex_hof_runtime_sprite.py','scripts/pr16_dex_hof_lifetime_root.py'}
    for field in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name,want in parent[field].items():
            m.need(m.identity(read(name))==want,'継承入力hash: '+name);protected.add(name)
    before=snapshot(protected)
    PHASE='receive-completed-parent-without-replay'
    prior=receive_parent();baseline_checks=previous.runs(m.BASE_HEAD)
    public('parent-actions-completion.json',prior)
    PHASE='new-abi-and-lookup-tests'
    stream=io.StringIO()
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_map_asset.py'))
    public('map-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==32 and not tests.skipped,'新32試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='fixed-public-arm-layout'
    symbols,layout,sources=sources_and_layout(saved);public('arm-layout.json',sources)
    PHASE='one-new-scope-candidate-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions']=1;public('attempt.json',ATTEMPT)
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        raw,cp=reconstruction.reconstruct()
    m.need(cp['candidate']==m.CANDIDATE and m.identity(raw)==m.CANDIDATE,'全候補/既存owner配置')
    PHASE='corrected-descriptors-and-actual-map-lookup'
    proof=m.measure(raw,saved,symbols,layout)
    proof['placement_identity']=m.identity(m.encode(cp['placement']))
    public('map-asset.json',proof)
    names={EVIDENCE+'/map-asset.json':proof,EVIDENCE+'/arm-layout.json':sources,
        EVIDENCE+'/parent-actions-completion.json':prior,EVIDENCE+'/map-tests.txt':stream.getvalue().encode(),
        EVIDENCE+'/starting-head-checks.json':baseline_checks}
    for name,value in names.items():write(name,value)
    stable=snapshot(names)
    m.need(load(EVIDENCE+'/map-asset.json')==proof and stable==snapshot(names),'保存後read-only')
    m.need(before==snapshot(protected),'全受入原本byte/mtime不変')
    valid=proof['valid_descriptor_candidates'];probe=proof['map_probe'];matches=len(probe['matches'])
    goal=('正しいARM Tileset ABI（callback+0x10/属性+0x14）と保存した実map lookup/descriptor候補から、'
        '0x0880FA64の実asset extentとcaller/read全4byteを限定して閉じる。旧0件原本はABI不整合の履歴であり不存在証明ではない。'
        '今回のlookup/probe/32試験、旧LZ探索/30試験を無変更再走しない。正式789/85・選定残6・安全容量0。'
        '窓外跨り/間接参照/退役移管/heap/controller/局所Saveは未完。')
    status='SELECTED_MAP_LOOKUP_BOUND_ASSET_READER_PENDING'
    report=dict(schema_version=1,task=TASK,status=status,source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,candidate=m.CANDIDATE,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
        new_unit_tests=32,source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        evidence_bindings={n:m.identity(read(n)) for n in sorted(names)},preserved_inputs={n:v[0] for n,v in before.items()},
        corrected_descriptor_candidates=valid,selected_map_candidates=matches,
        actual_asset_reader_proven=False,read_only_check_passed=True,task_graph_passed=True,
        observed_head_checks=observed,starting_head_checks=baseline_checks,next_ja=goal,**ATTEMPT)
    write(REPORT,report)
    lane.update(status=status,checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_MAP_ASSET_READER',goal_ja=goal,
        read_paths=[GUIDE,REPORT,EVIDENCE+'/map-asset.json',EVIDENCE+'/arm-layout.json',previous.WINDOW],
        done_ja='実lookupで選定したassetと実readerの全4byte消費を束縛し、完了run受領後にだけ正式型差分を追加する。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']={k:report[k] for k in ('task','source_head','actions_run_id','actions_completion_confirmed',
        'new_unit_tests','read_only_check_passed','task_graph_passed','formal_classified','formal_unclassified','donor_safe_bytes',*ATTEMPT)}
    state['recording'].update(task=TASK,status=status,source_head=head,selected_map_asset_checkpoint=REPORT,
        received_selected_asset_completion=EVIDENCE+'/parent-actions-completion.json')
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1);_,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_SELECTED_MAP_ASSET_READER。'+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode())
    state['bindings']['CHATGPT_RESUME.md']=dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),'Wiki/承認/安全方針不変')
    write(STATE,state)
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    summary=(f'旧Tileset decoderのcallback/属性offset逆転を固定公開headerのARM compileで確認し、後継だけを修正。'
        f'68 descriptor候補中data field妥当{valid}件。現lookupの実命令とroot、有限入力矩形から{matches}選定候補を保存。'
        '実asset readや分類増加は未主張。新32試験、候補復元1、native/旧受入/旧LZ探索再走0。')
    guide+='\n## Tileset ABI訂正と現map lookup\n\n'+summary+f'\n\n[後継証拠](../{EVIDENCE}/map-asset.json) / [checkpoint](../{REPORT})。前回run全8member/77text/公開commitを受領。旧測定原本は不変。\n\n## 次の未完作業\n\n'+goal+'\n'
    write(GUIDE,guide.encode())
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 正しいTileset ABIと実map lookup\n'
        '- Version: selected-map-asset-v1\n- Status: DONE（後継ABI/限定lookup。実asset readerと保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 後継検証器/32試験/Actions、限定証拠、固定引継ぎMD/JSON、両ログ。\n'
        '- Verify: 新32人工境界試験、固定構造体ARM layout、実lookup/全候補SHA/115owner、前回完了Actions/全artifact、保存後read-only、task graph、限定最終index。\n'
        '- Boundary: 正式789/85・残6・安全容量0。全体CI green/全story/退役・移管/ROM配布受入は非主張。\n'
        f'- Next: {goal}\n- Commit: この記録を含む単親通常commit。実SHAはActions result/Git履歴。\n'
        '- Network: 同repo PR/ref/Actions/artifact/既存private入力と同branch非force push。固定pret/pokefirered '+old.m.SOURCE+
        ' のglobal.fieldmap.h/fieldmap.c/overworld.cと固定JPsymbol。参照語 struct Tileset / Overworld_GetMapHeaderByGroupAndId。ROM/save/生byte列の公開なし。\n')
    for name in LOGS:
        original=read(name);m.need(('- Task: '+TASK+' /').encode() not in original,'同task二重追記禁止');write(name,original+block.encode())
    PHASE='final-index-and-nonforce-push'
    allowed=CODE|set(names)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(m.BASE_HEAD,allowed,REPORT)
    m.need(before==snapshot(protected),'push前原本保全')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': Tileset ABI訂正と実map lookupを記録');a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob一致')
    for name in set(names)|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=status,source_head=head,commit=pushed,
        corrected_descriptor_candidates=valid,selected_map_candidates=matches,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),**ATTEMPT))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,attempt=ATTEMPT))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
