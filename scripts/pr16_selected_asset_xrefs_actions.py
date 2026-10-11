#!/usr/bin/env python3
"""新しい逆参照scopeだけを検証・記録し、同branchへ非force反映する。"""
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
import pr16_selected_asset_xrefs as m
import pr16_selected_map_receipt_actions as prior

old, a, publication = prior.old, prior.a, prior.publication
ROOT, STATE, GUIDE, BRANCH, LOGS = prior.ROOT, prior.STATE, prior.GUIDE, prior.BRANCH, prior.LOGS
read, load, write, snapshot = prior.read, prior.load, prior.write, prior.snapshot
TASK = 'USER-20261012-SELECTED-ASSET-XREFS'
REPORT = 'content/modernization/pr16_selected_asset_xrefs_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_selected_asset_xrefs_evidence'
CODE = {'scripts/pr16_selected_asset_xrefs.py','scripts/pr16_selected_asset_xrefs_actions.py',
        'tests/test_pr16_selected_asset_xrefs.py','.github/workflows/pr16-selected-asset-xrefs.yml'}
WORK = ROOT/'.local/pr16-selected-asset-xrefs'
PUBLIC = WORK/'public'
PHASE = 'preflight'
COUNTS = dict(rom_reconstructions=0,native_processes=0,accepted_test_reruns=0,
    accepted_inventory_reruns=0,prior_lz_search_reruns=0,map_probe_reruns=0,arm_layout_recompiles=0,
    new_inverse_reference_passes=0)


def public(name, value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def receive_parent():
    result=publication.accepted_run(38178464746,'08a72f359efc98bfe1191641f10d8db0997bca82',
        ['完了map証拠だけを受領して停止点を記録','Run actions/upload-artifact@v4'])
    art=a.fetch('actions/artifacts/11716387524')
    m.need(art['name']=='pr16-selected-map-receipt-public-text' and not art['expired'] and
        art['workflow_run']['id']==38178464746 and art['workflow_run']['head_sha']==result['source_head'] and
        art['size_in_bytes']==417677 and art['digest']=='sha256:dea9248ddda1b573ca7972f65bde1a24d2f61674dbae44aabbe6e5c9b5da6352','前回artifact identity')
    raw=a.fetch('actions/artifacts/11716387524/zip',binary=True)
    m.need(m.identity(raw)==dict(size=417677,sha256=art['digest'][7:]),'前回ZIP全hash')
    members=old.zip_members(raw)
    m.need(set(members)=={'actions-completion.json','pr16_selected_map_asset_receipt.json','observed-source-checks.json',
        'receipt-tests.txt','result.json','scope-summary.json','scoped-context.zip','starting-head-checks.json'},'前回全8member')
    context=old.zip_members(members['scoped-context.zip'])
    m.need(len(context)==97 and json.loads(members['result.json'])['commit']==m.BASE_HEAD,'前回97text/公開commit')
    for name,data in context.items():
        data.decode('utf-8');m.need(b'\0' not in data and a.git('show',m.BASE_HEAD+':'+name)==data,'前回公開blob')
    m.need(members['pr16_selected_map_asset_receipt.json']==read(prior.REPORT),'前回checkpoint原本')
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
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_ASSET_OWNER_AFTER_MAP_PROBE' and
        [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0],'現行next/789/85/6/0')
    owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected={prior.REPORT}
    for key in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name,want in parent[key].items():
            m.need(m.identity(read(name))==want,'継承原本hash: '+name);protected.add(name)
    before=snapshot(protected)
    PHASE='receive-completed-parent-without-replay'
    completion=receive_parent();starting=prior.measured.previous.runs(m.BASE_HEAD)
    public('parent-actions-completion.json',completion)
    PHASE='new-inverse-reference-tests'
    stream=io.StringIO()
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_asset_xrefs.py'))
    public('xref-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==30 and not tests.skipped,'新30試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='fixed-symbol-input'
    spec=old.m.SYMBOL_SOURCE
    symbols=old.download('https://raw.githubusercontent.com/'+spec['repository']+'/'+spec['commit']+'/'+spec['path'],5000000)
    m.need(m.identity(symbols)=={k:spec[k] for k in ('size','sha256')} and old.m.blob(symbols)==spec['git_blob'],'固定JP symbol全hash')
    PHASE='one-new-scope-candidate-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    COUNTS['rom_reconstructions']=1;public('attempt.json',COUNTS)
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        raw,cp=reconstruction.reconstruct()
    m.need(cp['candidate']==m.CANDIDATE and m.identity(raw)==m.CANDIDATE,'全候補/既存owner配置')
    PHASE='bounded-target-inverse-references'
    proof=m.measure(raw,symbols)
    COUNTS['new_inverse_reference_passes']=proof['new_inverse_reference_passes']
    proof.update(public_symbol_source=spec,placement_identity=m.identity(m.encode(cp['placement'])))
    public('inverse-references.json',proof)
    evidence={EVIDENCE+'/inverse-references.json':proof,EVIDENCE+'/parent-actions-completion.json':completion,
        EVIDENCE+'/xref-tests.txt':stream.getvalue().encode(),EVIDENCE+'/starting-head-checks.json':starting}
    for name,value in evidence.items():write(name,value)
    stable=snapshot(evidence)
    m.need(load(EVIDENCE+'/inverse-references.json')==proof and stable==snapshot(evidence),'保存後read-only')
    m.need(before==snapshot(protected),'全受入原本byte/mtime不変')
    count,second,shapes=(proof[k] for k in ('first_level_count','second_level_count','literal_shape_count'))
    goal=(f'0x0880FA64の前4096byteから全4byteまでへの逆参照{count}件、第2段{second}件、Thumb literal形{shapes}件を保存。'
        'inverse-references.jsonの具体的なorigin/targetから実table・caller・asset境界を特定し、全4byteのreaderへ結ぶ。'
        'pointer形と旧symbol近傍だけではowner/型を確定しない。前4096byte外のasset開始・計算参照は未網羅。'
        '今回の逆参照/30試験と受入済みmap/ARM/LZ/Wikiは無変更再走しない。正式789/85・選定残6・安全容量0。'
        '窓外跨り/間接参照/退役移管/heap/controller/局所Saveは未完。')
    status='SELECTED_ASSET_INVERSE_REFERENCES_BOUND_READER_PENDING'
    report=dict(schema_version=1,task=TASK,status=status,source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,candidate=m.CANDIDATE,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,new_unit_tests=30,
        first_level_count=count,second_level_count=second,literal_shape_count=shapes,
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        evidence_bindings={n:m.identity(read(n)) for n in sorted(evidence)},preserved_inputs={n:v[0] for n,v in before.items()},
        actual_asset_reader_proven=False,read_only_check_passed=True,task_graph_passed=True,
        observed_head_checks=observed,starting_head_checks=starting,next_ja=goal,**COUNTS)
    write(REPORT,report)
    lane.update(status=status,checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id=m.NEXT,goal_ja=goal,read_paths=[GUIDE,REPORT,EVIDENCE+'/inverse-references.json',prior.REPORT],
        done_ja='保存した具体的参照元から全4byteの実readerを束縛し、完了run受領後に正式型差分だけ追加する。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=30,read_only_check_passed=True,task_graph_passed=True,**COUNTS)
    state['recording'].update(task=TASK,status=status,source_head=head,selected_asset_xrefs_checkpoint=REPORT,
        received_selected_map_receipt_completion=EVIDENCE+'/parent-actions-completion.json')
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1);_,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は '+m.NEXT+'。'+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode())
    state['bindings']['CHATGPT_RESUME.md']=dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),'Wiki/承認/安全方針不変')
    write(STATE,state)
    summary=(f'対象近傍へ全byte開始/3mirrorの逆参照{count}件、第2段{second}件、Thumb literal形{shapes}件。'
        '全候補SHA/115owner配置、各参照wordのhash、固定JP symbol近傍を束縛。新30境界試験・task graph PASS。'
        '新scope復元1回、native/旧inventory/map/LZ/Wiki再走0。pointer形は実reader受入ではない。')
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide+='\n## 選定assetの対象限定逆参照\n\n'+summary+'\n\n[checkpoint](../'+REPORT+') / [逆参照](../'+EVIDENCE+'/inverse-references.json)。\n\n## 次の未完作業\n\n'+goal+'\n'
    write(GUIDE,guide.encode())
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 選定assetの具体的逆参照\n'
        '- Version: selected-asset-xrefs-v1\n- Status: DONE（新しい逆参照検査を実装・検証。実reader/保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 新検査器/30試験/専用Actions、checkpoint/text証拠、固定MD/JSON、両ログ。\n'
        '- Verify: 新30人工境界試験、前回完了run/ZIP全hash/公開97blob、受入原本byte/mtime、task graph、最終index新規private違反0。\n'
        '- Boundary: 新しい対象限定逆参照は全32MiBを読む。旧874参照inventory再走ではない。件数上限では部分成功にせず拒否。全体guard/一般CIの既存失敗は未解消。\n'
        f'- Next: {goal}\n- Commit: この記録を含む単親通常commit。実SHAはActions result/Git履歴。\n'
        '- Network: 同repo PR/ref/Actions/artifact、固定ComplexRobot/frlg-sym c04a315のJP symbol、既存private入力復元、同branch非force push。'
        '会話でgMultiBootProgram_PokemonColosseum_StartをWeb検索したが一次資料を確認できず根拠不採用。'
        '固定pret/pokefirered c75f352のsrc/text.cを読んだがglyph所有元証拠には未採用。ROM/save/生byte列を追加公開しない。\n')
    for name in LOGS:
        original=read(name);m.need(('- Task: '+TASK+' /').encode() not in original,'同task二重追記禁止')
        write(name,original+block.encode())
    PHASE='final-index-and-nonforce-push'
    allowed=CODE|set(evidence)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(m.BASE_HEAD,allowed,REPORT)
    m.need(before==snapshot(protected),'全受入原本byte/mtime不変')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 具体的逆参照とreader未完境界を記録');a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob一致')
    for name in set(evidence)|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=status,source_head=head,commit=pushed,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        first_level_count=count,second_level_count=second,literal_shape_count=shapes,**COUNTS))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,**COUNTS))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
