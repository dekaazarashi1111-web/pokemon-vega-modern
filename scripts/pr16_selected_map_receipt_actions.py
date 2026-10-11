#!/usr/bin/env python3
"""map測定の完了受領と0件停止点を記録。ROM/旧試験を再走しない。"""
from __future__ import annotations
import datetime as dt
import io
import json
import os
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_selected_map_receipt as r
import pr16_selected_map_asset_actions as measured

m = r.parent
old, a, publication = measured.old, measured.a, measured.publication
ROOT, STATE, GUIDE, BRANCH, LOGS = measured.ROOT, measured.STATE, measured.GUIDE, measured.BRANCH, measured.LOGS
read, load, write, snapshot = measured.read, measured.load, measured.write, measured.snapshot
TASK = 'USER-20261012-SELECTED-MAP-RECEIPT'
REPORT = 'content/modernization/pr16_selected_map_asset_receipt.json'
EVIDENCE = 'content/modernization/pr16_selected_map_receipt_evidence'
CODE = {'scripts/pr16_selected_map_receipt.py','scripts/pr16_selected_map_receipt_actions.py',
        'tests/test_pr16_selected_map_receipt.py','.github/workflows/pr16-selected-map-receipt.yml'}
WORK = ROOT/'.local/pr16-selected-map-receipt'
PUBLIC = WORK/'public'
PHASE = 'preflight'
COUNTS = dict(rom_reconstructions=0,native_processes=0,accepted_test_reruns=0,
              full_rom_scans=0,prior_lz_search_reruns=0,map_probe_reruns=0,arm_layout_recompiles=0)


def public(name, value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def receive():
    result=publication.accepted_run(r.RUN,r.SOURCE_HEAD,
        ['後継ABIと実map lookupだけを限定測定して記録','Run actions/upload-artifact@v4'])
    spec=r.ARTIFACT;art=a.fetch('actions/artifacts/'+str(spec['id']))
    m.need(art['name']==spec['name'] and art['size_in_bytes']==spec['size'] and
        art['digest']=='sha256:'+spec['sha256'] and not art['expired'] and
        art['workflow_run']['id']==r.RUN and art['workflow_run']['head_sha']==r.SOURCE_HEAD,'原本artifact metadata')
    raw=a.fetch('actions/artifacts/'+str(spec['id'])+'/zip',binary=True)
    m.need(m.identity(raw)=={k:spec[k] for k in ('size','sha256')},'全ZIP identity')
    members=old.zip_members(raw)
    m.need(set(members)=={'arm-layout.json','attempt.json','map-asset.json','map-tests.txt',
        'parent-actions-completion.json','pr16_selected_map_asset_checkpoint.json','result.json',
        'scoped-context.zip','starting-head-checks.json'},'閉じた9member')
    context=old.zip_members(members['scoped-context.zip'])
    m.need(len(context)==87 and sum(map(len,context.values()))==1483776,'全87text extent')
    for name,data in context.items():
        data.decode('utf-8')
        m.need(b'\0' not in data and a.git('show',r.BASE_HEAD+':'+name)==data,'公開commit全87blob')
    value=json.loads(members['result.json'])
    m.need(value['commit']==r.BASE_HEAD and value['source_head']==r.SOURCE_HEAD and
        value['corrected_descriptor_candidates']==68 and value['selected_map_candidates']==0 and
        value['rom_reconstructions']==1 and value['native_processes']==value['accepted_test_reruns']==0,'原本完了結果')
    m.need(members['pr16_selected_map_asset_checkpoint.json']==read(measured.REPORT),'checkpoint原本')
    for name in ('arm-layout.json','map-asset.json','map-tests.txt','parent-actions-completion.json','starting-head-checks.json'):
        m.need(members[name]==read(measured.EVIDENCE+'/'+name),'保存済み証拠member全byte')
    result.update(artifact={k:art[k] for k in ('id','name','size_in_bytes','digest')},
        members={n:m.identity(v) for n,v in members.items()},
        published_commit=r.BASE_HEAD,context_bindings={n:m.identity(v) for n,v in context.items()},
        accepted_measurement_tests=32,**COUNTS)
    return result


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and
        os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回受領')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists(),'同受領の二重追記禁止')
    PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip() and
        set(a.git('diff','--name-only',r.BASE_HEAD,head).decode().splitlines())==CODE,'新受領4sourceのみ')
    m.need(not a.git('ls-files','--',*[p+'/AGENTS.md' for p in
        ('scripts','tests','docs','design','content','content/modernization','.github','.github/workflows')]).strip(),'追加AGENTS確認')
    state,parent=load(STATE),load(measured.REPORT)
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_MAP_ASSET_READER' and
        parent['actions_run_id']==r.RUN and parent['source_head']==r.SOURCE_HEAD and
        parent['new_unit_tests']==32 and parent['read_only_check_passed'] and parent['task_graph_passed'] and
        [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0],
        '測定原本と現行停止点')
    owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected={measured.REPORT}
    for key in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name,want in parent[key].items():
            m.need(m.identity(read(name))==want,'継承原本hash: '+name);protected.add(name)
    before=snapshot(protected)
    PHASE='completed-actions-and-artifact-receipt'
    completion=receive();public('actions-completion.json',completion)
    source_checks=measured.previous.runs(r.SOURCE_HEAD)
    starting_checks=measured.previous.runs(r.BASE_HEAD)
    PHASE='new-receipt-regressions-no-measurement-replay'
    stream=io.StringIO()
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_map_receipt.py'))
    public('receipt-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==24 and not tests.skipped,'新受領24試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    proof=load(measured.EVIDENCE+'/map-asset.json');summary=r.summarize(proof)
    m.need(summary==r.summarize(load(measured.EVIDENCE+'/map-asset.json')) and before==snapshot(protected),
        '保存証拠だけのread-only要約')
    evidence={EVIDENCE+'/actions-completion.json':completion,EVIDENCE+'/scope-summary.json':summary,
        EVIDENCE+'/receipt-tests.txt':stream.getvalue().encode(),
        EVIDENCE+'/observed-source-checks.json':source_checks,EVIDENCE+'/starting-head-checks.json':starting_checks}
    for name,value in evidence.items():write(name,value)
    status='SELECTED_MAP_ABI_AND_LOOKUP_ACCEPTED_OWNER_UNRESOLVED'
    report=dict(schema_version=1,task=TASK,status=status,source_head=head,
        accepted_measurement_head=r.SOURCE_HEAD,accepted_measurement_run=r.RUN,
        accepted_measurement_published_commit=r.BASE_HEAD,actions_completion_confirmed=True,
        receipt_actions_run_id=int(os.environ['GITHUB_RUN_ID']),receipt_actions_completion_confirmed=False,
        candidate=m.CANDIDATE,summary=summary,new_unit_tests=24,accepted_measurement_tests=32,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        evidence_bindings={n:m.identity(read(n)) for n in sorted(evidence)},
        preserved_inputs={n:v[0] for n,v in before.items()},read_only_check_passed=True,task_graph_passed=True,
        observed_head_checks=observed,starting_head_checks=starting_checks,next_ja=r.GOAL,**COUNTS)
    write(REPORT,report)
    lane.update(status=status,checkpoint_path=REPORT,next_ja=r.GOAL)
    state['next_action']=dict(id=r.NEXT,goal_ja=r.GOAL,
        read_paths=[GUIDE,REPORT,EVIDENCE+'/scope-summary.json',measured.EVIDENCE+'/map-asset.json',measured.previous.WINDOW],
        done_ja='具体的な実参照元から対象assetと全4byteのreaderを束縛し、完了run受領後に正式型差分だけ追加する。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,received_measurement_run=r.RUN,received_measurement_completion_confirmed=True,
        new_unit_tests=24,read_only_check_passed=True,task_graph_passed=True,**COUNTS)
    state['recording'].update(task=TASK,status=status,source_head=head,selected_map_asset_receipt=REPORT,
        received_selected_map_completion=EVIDENCE+'/actions-completion.json')
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1);_,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は '+r.NEXT+'。'+r.GOAL+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode())
    state['bindings']['CHATGPT_RESUME.md']=dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),
        'Wiki/承認/既存scope不変')
    write(STATE,state)
    summary_ja=(f'run {r.RUN}の全job/必須step成功、artifact9member/87textと公開commit {r.BASE_HEAD}を受領。'
        '訂正後68 descriptor妥当。実lookup由来の128×128有限入力で678 header/486 layout/110 descriptor、対象一致0。'
        '旧decoderの逆offsetは後継で修正済み、原本は不変。一致したmap候補があるかのような停止点を修正。'
        '新受領24試験のみ実行し、受入32試験・lookup/probe・ARM compile・ROM再構成・native・旧LZ再走0。')
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide+='\n## map後継測定の完了受領と0件の継続点\n\n'+summary_ja+'\n\n[受領JSON](../'+REPORT+') / [範囲要約](../'+EVIDENCE+'/scope-summary.json)。'
    guide+='原本checkpointのin-progress記録は測定時点の履歴として保持し、完了は受領JSONを参照する。一般CIや全index既存違反をgreenへ読み替えない。\n\n## 次の未完作業\n\n'+r.GOAL+'\n'
    write(GUIDE,guide.encode())
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / map測定の完了受領と0件停止点\n'
        '- Version: selected-map-receipt-v1\n- Status: DONE（限定測定を受領。対象asset/保存統合は未完）\n'
        f'- Summary: {summary_ja}\n- Files changed: 受領検査/24試験/専用Actions、受領JSON/text、固定MD/JSON、両ログ。\n'
        '- Verify: 新24人工境界試験、成功run/artifact全hash/公開全blob、入力保全/read-only、task graph、最終index新規private違反0。\n'
        '- Boundary: 正式789/85・選定残6・安全容量0。0件を全map不存在/asset消費へ昇格しない。一般CIの失敗/全indexの既存違反は未修正のまま記録。\n'
        f'- Next: {r.GOAL}\n- Commit: この記録を含む単親通常commit。実SHAはActions result/Git履歴。\n'
        '- Network: 同repo PR/ref/Actions/artifact GETと同branch非force push。受領scopeで公開source再取得なし。'
        '会話でpret/pokefireredの固定src/text.cとColosseum公開symbolを補助参照したがowner証拠には採用せず、候補復元/測定追試なし。\n')
    for name in LOGS:
        original=read(name);m.need(('- Task: '+TASK+' /').encode() not in original,'同task二重追記禁止')
        write(name,original+block.encode())
    PHASE='final-index-and-nonforce-push'
    allowed=CODE|set(evidence)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(r.BASE_HEAD,allowed,REPORT)
    m.need(before==snapshot(protected),'全受入原本byte/mtime不変')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': map完了受領とasset所有元未特定の継続点を記録')
    a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob一致')
    for name in set(evidence)|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=status,source_head=head,commit=pushed,new_unit_tests=24,
        accepted_measurement_run=r.RUN,receipt_run=int(os.environ['GITHUB_RUN_ID']),summary=summary,**COUNTS))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__)
                if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,**COUNTS))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
