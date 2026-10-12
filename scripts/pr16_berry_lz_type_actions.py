#!/usr/bin/env python3
"""LZ測定を再走せず単一型差分を検証し、固定引継ぎと同branchへ記録する。"""
from __future__ import annotations
import datetime as dt
import io
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_berry_lz_type as m
import pr16_berry_child_lz_actions as old

ROOT = Path(__file__).resolve().parents[1]
a, publication = old.a, old.publication
read, load, write, snapshot = old.read, old.load, old.write, old.snapshot
STATE, GUIDE, BRANCH, LOGS = old.STATE, old.GUIDE, old.BRANCH, old.LOGS
BASE = 'b296b57b2fcf86b98d11e4b1389eeaa652d31958'
TASK = 'USER-20261011-BERRY-LZ-TYPE'
REPORT = 'content/modernization/pr16_berry_lz_type_checkpoint.json'
CODE = {'scripts/pr16_berry_lz_type.py','scripts/pr16_berry_lz_type_actions.py',
        'tests/test_pr16_berry_lz_type.py','.github/workflows/pr16-berry-lz-type.yml'}
WORK = ROOT/'.local/pr16-berry-lz-type'
PUBLIC = WORK/'public'
PHASE = 'preflight'


def public(name,value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def graph():
    p = subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,capture_output=True)
    m.need(p.returncode == 0 and not p.stderr,'task graph')


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/'+BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT') == '1','同branch初回だけ')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists(),'型差分の二重実行禁止')
    PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip()
    m.need(head==os.environ['GITHUB_SHA'],'event HEAD');a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip() and
           set(a.git('diff','--name-only',BASE,head).decode().splitlines())==CODE,'新4sourceだけ')
    m.need(not a.git('ls-files','--',*[n+'/AGENTS.md' for n in ('scripts','tests','docs','design','content',
        'content/modernization','.github','.github/workflows')]).strip(),'追加AGENTS読取が必要')
    state=load(STATE);lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_BERRY_LZ_TYPED_RECEIPT' and
        [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[788,86,7,0], '現在の単一型差分lane')
    owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected={old.REPORT,old.RECEIPT,old.REQUEST,'content/modernization/pr16_sound_origin_reader_receipt.json'}
    for path in sorted(protected.copy()-{old.REQUEST}):
        cp=load(path)
        for field in ('source_bindings','evidence_bindings','preserved_inputs'):
            for name,want in cp.get(field,{}).items():
                m.need(m.identity(read(name))==want,'継承入力hash: '+name);protected.add(name)
    for suffix in ('reference-chain.json','unknown-frontier.json','window-progress.json'):
        protected.add(m.PARENT+'/'+suffix)
    before=snapshot(protected)
    PHASE='receive-completed-receipt-run-without-replay'
    measurement,receipt=load(old.REPORT),load(old.RECEIPT)
    arts=a.fetch('actions/runs/'+str(receipt['actions_run_id'])+'/artifacts')['artifacts']
    arts=[x for x in arts if x['name']=='pr16-berry-child-lz-public-text' and not x['expired']]
    m.need(len(arts)==1,'受領workflowの単一公開artifact')
    art=arts[0]
    received=old.receive(receipt['actions_run_id'],receipt['source_head'],art['id'],art['digest'][7:],BASE,
        old.RECEIPT,'保存停止点から実LZ readerだけを検証して記録')
    accepted=load(old.EVIDENCE+'/actions-completion.json')
    proof=load(m.PROOF_PATH)
    PHASE='new-singleton-delta-tests'
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_berry_lz_type.py')
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    public('type-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==25 and not tests.skipped,'新しい型差分25試験')
    graph()
    PHASE='single-typed-origin-with-parent-preservation'
    parents=[load(m.PARENT+'/'+n) for n in ('reference-chain.json','unknown-frontier.json','window-progress.json')]
    outputs=m.promote(*parents,proof,measurement,receipt,accepted)
    m.need(outputs==m.promote(*parents,proof,measurement,receipt,accepted),'新型差分の決定性')
    chain,front,window=outputs
    names={m.OUTPUT+'/reference-chain.json':chain,m.OUTPUT+'/unknown-frontier.json':front,
        m.OUTPUT+'/window-progress.json':window,m.OUTPUT+'/receipt-actions-completion.json':received,
        m.OUTPUT+'/type-tests.txt':stream.getvalue().encode()}
    for name,value in names.items():write(name,value)
    stable=snapshot(names)
    m.need(all(load(n)==v for n,v in names.items() if isinstance(v,dict)) and stable==snapshot(names), '保存後read-only')
    m.need(front['rows']==[r for r in parents[1]['rows'] if r['hit']['address']!=m.HIT] and
           window['remaining_rows']==[r for r in parents[2]['remaining_rows'] if r['address']!=m.HIT], '他の未知85行/選定6行完全不変')
    m.need(before==snapshot(protected),'全受入済み原本byte/mtime不変')
    goal=(f'次の選定窓origin 0x{window["next_address"]:08X}を保存symbol近傍から固定asset/現候補の実consumerへ限定的に結ぶ。'
        '残る選定窓6行・正式789分類/85未知・安全容量0。Berryの親13profile/子機entry/LZ native/25 reader試験/25型差分試験は変更影響がない限り再走しない。'
        '全874scan/窓最適化は再走不要。旧owner退役・移管、窓外跨りread/間接参照、heap/controller、局所Save/fresh Continueは未完。')
    observed=a.live(head)
    report=dict(schema_version=1,task=TASK,status='BERRY_LZ_ORIGIN_FORMALLY_ACCEPTED_789_85',source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,
        classification_measurement_completion_confirmed=True,candidate=m.lz.CANDIDATE,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
        newly_classified_origins=[m.HIT],unchanged_other_unknown_rows=85,new_unit_tests=25,
        native_processes=0,rom_reconstructions=0,full_rom_scans=0,accepted_test_reruns=0,accepted_reader_replays=0,
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        preserved_inputs={n:v[0] for n,v in before.items()},evidence_bindings={n:m.identity(read(n)) for n in sorted(names)},
        completed_measurement_path=old.EVIDENCE+'/actions-completion.json',completed_receipt_path=m.OUTPUT+'/receipt-actions-completion.json',
        read_only_check_passed=True,task_graph_passed=True,observed_head_checks=observed,next_ja=goal)
    write(REPORT,report)
    lane.update(status=report['status'],checkpoint_path=REPORT,classified=789,unclassified=85,
        selected_unknown_origins=6,donor_safe_bytes=0,next_ja=goal,scheduling_status='READY_FROM_SAVED_SELECTED_ORIGINS',
        reference_chain_path=m.OUTPUT+'/reference-chain.json',unknown_frontier_path=m.OUTPUT+'/unknown-frontier.json',
        window_progress_path=m.OUTPUT+'/window-progress.json')
    state['next_action']=dict(id='SAVE_CAPACITY_NEXT_SELECTED_ORIGIN_BINDING',goal_ja=goal,
        read_paths=[GUIDE,REPORT,m.OUTPUT+'/reference-chain.json',m.OUTPUT+'/window-progress.json'],
        done_ja='次のoriginについて保存した証拠から実型/consumerを束縛し、完了した限定検証だけを追加する。安全容量を推測しない。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']={k:report[k] for k in ('task','source_head','actions_run_id','actions_completion_confirmed',
        'new_unit_tests','native_processes','rom_reconstructions','full_rom_scans','accepted_test_reruns','accepted_reader_replays',
        'read_only_check_passed','task_graph_passed','formal_classified','formal_unclassified','donor_safe_bytes')}
    state['recording'].update(task=TASK,source_head=head,status=report['status'],berry_lz_formal_checkpoint=REPORT,
        berry_lz_no_replay=True,received_berry_lz_type_inputs=m.OUTPUT+'/receipt-actions-completion.json')
    summary=('対象0x086C51BFの4byteを、実子機ARM callerからSWI11が消費する条件付きLZ77 tokenとして正式型登録。'
        '旧788/86のreference-chainを原本のまま継承し、1件だけ追加して789/85、選定窓の残り7→6。'
        '他の未知85行/選定6行は完全不変。新25型差分試験PASS。新native/候補復元/旧受入再走0、安全容量0。')
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1)
    _,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_NEXT_SELECTED_ORIGIN_BINDING。'+summary+' '+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode())
    state['bindings']['CHATGPT_RESUME.md']={'git_blob_sha':old.blob(text.encode()),**m.identity(text.encode())}
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),'Wiki/承認/安全方針不変')
    write(STATE,state)
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide+='\n## Berry子機LZ tokenの単一正式型登録\n\n'+summary+f'\n\n[正式型差分](../{m.OUTPUT}/reference-chain.json) / [残る選定窓](../{m.OUTPUT}/window-progress.json) / [checkpoint](../{REPORT})。\n\n'
    guide+='通信値は明示fixture、mGBA HLE readerの条件付き証拠です。自然リンク/元BIOS CPU/実cart/代替reader完全排除/領域退役の成功ではありません。\n\n## 次の未完作業\n\n'+goal+'\n'
    write(GUIDE,guide.encode())
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK} / Berry単一LZ token型差分\n'
        '- Version: berry-lz-type-v1\n- Status: DONE（1件型登録。保存容量/ゲーム統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 型差分専用source/新25試験/Actions、正式chain/frontier/window、固定引継ぎMD/JSON、両ログ。\n'
        '- Verify: 外部成功run/全artifact受領、25人工試験、型差分決定性、他85行/6行と全原本byte/mtime、task graph、限定最終index PASS。新native/復元/旧受入再走0。\n'
        '- Boundary: 正式789/85、選定残6、安全容量0。初回LZ JSON失敗は未受入履歴を保全し隠さない。全体CI greenは主張しない。\n'
        f'- Next: {goal}\n- Commit: この記録を含む同branch単親通常commit。実SHAはActions result/Git履歴で照合。\n'
        '- Network: 同repo PR/ref/Actions/artifact GETと同branchへの非force pushのみ。新たなROM/外部asset取得なし。私有原本と展開byteは公開しない。\n')
    for name in LOGS:
        previous=read(name);m.need(('- Task: '+TASK+' /').encode() not in previous,'同task二重追記禁止')
        write(name,previous+block.encode())
    PHASE='final-index-and-nonforce-push'
    allowed=CODE|set(names)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(BASE,allowed,REPORT)
    m.need(before==snapshot(protected),'push前受入済み原本保全')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push直前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 単一LZ originを789/85へ正式登録し次の6行を保存')
    a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob完全一致')
    for name in set(names)|{REPORT}:public(Path(name).name,read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=report['status'],source_head=head,commit=pushed,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),formal_classified=789,formal_unclassified=85,
        selected_unknown_origins=6,donor_safe_bytes=0,new_unit_tests=25,native_processes=0,rom_reconstructions=0,accepted_test_reruns=0))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,
            detail=str(exc).replace(str(ROOT),'.')[:300] if isinstance(exc,ValueError) else None,
            frames=[{'path':f.filename[len(str(ROOT))+1:],'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)
                    if f.filename.startswith(str(ROOT)+'/scripts/')],native_processes=0,rom_reconstructions=0))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__)
        sys.exit(1)
