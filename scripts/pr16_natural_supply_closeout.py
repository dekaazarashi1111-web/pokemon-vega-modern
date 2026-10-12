#!/usr/bin/env python3
"""保存native/Actions/artifactの終端照合のみ。旧unit/native/compileは実行しない。"""
import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_natural_supply as s
import pr16_natural_gift_save as gift
need=s.need
SELF='scripts/pr16_natural_supply_closeout.py'
TEST='tests/test_pr16_natural_supply_closeout.py'


def unpack(raw,artifact,checkpoint):
    need(artifact['workflow_run']['id']==checkpoint['run_id'] and artifact['workflow_run']['head_sha']==checkpoint['source_head'] and artifact['workflow_run']['head_branch']==s.m.BRANCH,'artifact/run/source/branch')
    need(not artifact['expired'] and s.identity(raw)=={'size':artifact['size_in_bytes'],'sha256':artifact['digest'][7:]} and artifact['digest'].startswith('sha256:'),'artifact hash/期限')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist();need(len(entries)==len(set(z.namelist())) and sum(x.file_size for x in entries)<16*1024*1024,'proof ZIP重複/容量')
        data={}
        for x in entries:
            need(Path(x.filename).name==x.filename and not x.is_dir() and x.external_attr>>28!=0xA,'proof ZIP path/kind')
            b=z.read(x);b.decode('utf-8');need(b'\0' not in b,'proof binary');data[x.filename]=b
    v=json.loads(data['verification.json'],object_pairs_hook=s.egg.strict_pairs)
    need(v['run_id']==checkpoint['run_id'] and v['source_head']==checkpoint['source_head'] and v['candidate']==s.CANDIDATE,'proof identity')
    need(set(data)==set(v['proof_bindings'])|{'verification.json','reflected-head.txt'},'proof完全集合')
    for name,binding in v['proof_bindings'].items():need(s.identity(data[name])==binding,'proof member '+name)
    need(v['accepted']==checkpoint['accepted'] and v['status']==checkpoint['status'],'checkpoint/実測一致')
    reflected=data['reflected-head.txt'].decode().strip();need(re.fullmatch('[0-9a-f]{40}',reflected),'反映commit')
    return v,data,reflected


def validate_cases(v,data):
    oracle=json.loads(data['oracle.json']);pp={int(k):value for k,value in oracle['pp'].items()}
    cases=s.hatch_cases({int(k):row['egg_cycles'] for k,row in oracle['egg_stats'].items()})
    good=set(v['accepted']);need(good<=set(s.NAMES),'未知の受入case')
    expected_status='PASS_NATURAL_SUPPLY_SCOPED' if good==set(s.NAMES) else 'PARTIAL_NATURAL_SUPPLY'
    need(v['status']==expected_status,'未成功を昇格しない')
    names=[r['case'] for r in v['results']]
    need(len(names)==len(set(names)) and set(names)=={n for n,a in v['accepted'].items() if a['run_id']==v['run_id']},'全実測成功case集合')
    failed=set(v['failures']);need(not (failed&set(names)) and set(v['selected_cases'])==set(names)|failed and v['native_processes']==len(v['selected_cases']),'成功/失敗/選択/実行数一致')
    for name in failed:
        process=json.loads(data[name+'.process.json'])
        need(process['returncode']!=0 or process['timed_out'] is True,'失敗原本を成功にしない')
        need(data[name+'.stderr.txt'],'失敗理由原本')
    for k in ('arm_compiles','rom_changes','accepted_case_reruns','wiki_generations'):need(type(v[k])is int and v[k]==0,'不必要な再実行 '+k)
    for k in ('issue19_complete','release_ready','active_baseline_changed'):need(v[k]is False,'全体へ昇格しない '+k)
    for result in v['results']:
        name=result['case'];need(name in v['selected_cases'] and v['accepted'][name]['run_id']==v['run_id'],'選択case原本')
        need(json.loads(data[name+'.process.json'])=={'returncode':0,'timed_out':False},'native process成功')
        if name==s.GIFT:
            parsed=gift.validate(data[name+'.stdout.txt'],data[name+'.stderr.txt'],pp)
            need(parsed['npc_script']==oracle['gift_geometry']['script'],'実NPC pointer')
        else:
            with s.egg_contract(cases):parsed=s.egg.validate(data[name+'.stdout.txt'],data[name+'.stderr.txt'],name,pp)
            spec=next(c for c in cases if c[0]==name);expected=[(flag,i,move,move,pp[move],pp[move]) for flag in (1,1,0,0) for i,move in enumerate(spec[-1])]
            rows=re.findall(rb'^CHILD egg=(\d+) slot=(\d+) move=(\d+)/(\d+) pp=(\d+)/(\d+)$',data[name+'.stderr.txt'],re.M)
            need([tuple(map(int,row)) for row in rows]==expected,'16原本slot観測/原本技/PP')
        need(parsed==result==v['accepted'][name]['result'],'受入result再投影')
    return {'saved_results_checked':len(v['results']),'failed_results_retained':len(v['failures']),'native_reruns':0,'old_unit_reruns':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0}



def reconcile(cp,versions):
    need(cp['status']=='PASS_NATURAL_SUPPLY_SCOPED' and set(cp['accepted'])==set(s.NAMES),'3case完了前の終端昇格禁止')
    need(set(versions)==set(cp['prior_runs']+[cp['run_id']]),'全run集合')
    for name,accepted in cp['accepted'].items():
        origin=versions[accepted['run_id']]
        need(origin['accepted'][name]==accepted and [r for r in origin['results'] if r['case']==name]==[accepted['result']],'受入を発生run原本へ結合 '+name)
    executions=[name for v in versions.values() for name in v['selected_cases']]
    failed=sum(s.GIFT in v['failures'] for v in versions.values())
    need(all(executions.count(n)==1 for n in s.HATCH) and executions.count(s.GIFT)==failed+1,'成功済み孵化は各1回、配布は失敗原本+成功1')
    return {'accepted_cases':list(s.NAMES),'original_hatch_runs':1,'original_hatch_cases':2,'gift_failed_attempts':failed,'gift_successful_attempts':1,'total_native_processes':len(executions),'accepted_case_reruns':0}


def publish(v,completion=False):
    from pr16_learnset_compact_record import publish_resume
    need(completion and v['actions_completion_confirmed'],'終端専用publication')
    run=int(os.environ['GITHUB_RUN_ID']);dest=s.ROOT/s.EVIDENCE/str(run)
    need(not dest.exists(),'完了原本上書き禁止');dest.mkdir(parents=True)
    files=('closeout-unit.stdout.txt','closeout-unit.stderr.txt','closeout-unit.process.json','artifact-closeout.json')
    for name in files:(dest/name).write_bytes((s.PROOF/name).read_bytes())
    v['completion_record']={'run_id':run,'source_head':os.environ['GITHUB_SHA'],'evidence_path':dest.relative_to(s.ROOT).as_posix(),'files':{name:s.identity((dest/name).read_bytes()) for name in files},'new_unit_tests':CLOSEOUT_TESTS,'old_unit_reruns':0,'native_processes':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0,'case_results_revalidated_from_saved_bytes':3}
    s.write(s.ROOT/s.CP,v)
    first=gift.PRIOR;second=v['run_id'];audit=s.load(s.PROOF/'artifact-closeout.json');date=datetime.datetime.now(datetime.timezone.utc)
    (s.ROOT/s.GUIDE).write_text(f"""# PR16 Issue19: 通常配布・原本初期技孵化

状態 `PASS_NATURAL_SUPPLY_SCOPED`。3ケースを限定受入。native原本のActions終端 `True`。

候補 `{s.CANDIDATE['sha256']}` / {s.CANDIDATE['size']} bytes。ROM・runtime・ARMは変更せず、未受入経路の検証実装を追加した。全owner/全form/Issue19/releaseは未完、active baseline不変。

## 受入範囲

| case | 原本初期技（順序） | 通常操作の受入 | 実測run |
| --- | --- | --- | --- |
| caterpie-initial-hatch / Species649 | 33, 81, 0, 0 | 育て屋預け・歩行生成・受取・Save/fresh Continue・歩行孵化・Save/fresh Continue | {first} |
| leepun-initial-hatch / Species1 | 10, 39, 0, 0 | 同上。Vega採用原本から期待値を解決 | {first} |
| floette-eternal-npc-initial / Species1029 Lv50 | 204, 235, 382, 738（PP20,5,10,5） | map96/5 local15の実NPC配布・原本技/PP/HP・元party不変・通常Save/fresh Continue・再配布拒否 | {second} |

孵化の親2体・開始地点、配布の開始party/場所/Ring/未受領flagはfixture。親の通常捕獲、Ringの通常取得、ストーリー到達はこの受入に含めない。guarded操作区間では7host書込APIを拒否し、通常キー入力だけを与える。配布JSONのguarded_phases=3は配布・手動Save・fresh-core操作の3カテゴリを表し、Continueと再受取の間にもgetter用解除/再guardがある（a_guardは4回）。観測区間間のgetter用CPU呼出しは読み取り専用の補助で、配布処理や保存関数の直接呼出しへ読み替えない。

## 失敗と限定修復

run {first} は孵化2件成功・配布1件失敗、Actions全体 `failure` のまま保存した。配布は原本4技を生成済みだが、検証がSave counterを2→3と未検証で仮定し、実際の2→4で停止した。

中間run 36103989903で最初の遷移時はparty1体と判明し、原本のGetPending→ensure_save→旧内側Save移行を確認した。配布の最終run {second} では、移行保存（party1）と配布保存（party2）を各frame・lock・PCとともにraw観測。手動Save後5、fresh Continue後5、再受取拒否後5を一致させる。二遷移を二回のhost保存呼出しとは解釈しない。元party100byteと配布後200byteを独立rawで照合。candidateの保存設計や全Save経路の性能を評価したものではない。

## 再実行防止と証拠

孵化各1回、配布は失敗{audit["gift_failed_attempts"]}回+成功1回、計{audit["total_native_processes"]}native process。unitは初回20、中間12、配布phase変更影響13、host compile計4。成功済み孵化2件と初回20unitは修復で再実行しない。中間12試験はvalidator変更の影響があるため次の13試験に含めて再検証した。既存EXP/Bag/egg8/旧野生/ARM/Wikiは変更影響なし。

終端照合は新規{CLOSEOUT_TESTS}unitと保存ZIPのdigest/size/完全集合/全member hash/3caseのraw結果/反映commit親/Actions全stepを検査。native・旧unit・host/ARM compileの再実行0。失敗runは成功へ改ざんしない。正本 `{s.CP}`。完了記録source `{os.environ['GITHUB_SHA']}`、記録run `{run}`。

## 次

{s.NEXT}
""")
    state=s.load(s.ROOT/s.m.STATE)
    state['learnset_natural_supply']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')}
    state['learnset_natural_supply'].update(path=s.CP,accepted_cases=list(s.NAMES),pending_cases=[],completion_record=v['completion_record'])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_date_jst']=date.astimezone(ZoneInfo('Asia/Tokyo')).date().isoformat()
    state['observed_head_semantics']='限定3caseの実測3run（失敗2+成功1）とartifactを完了照合。observed HEADはnative再実行なしの記録source。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':v['terminal_actions'],'reason_ja':'初回failureと修復successを原本のまま区別。一般CI/action_requiredや全体完成へ昇格しない。'}
    state['bp']['current_stop']='Issue19: 通常配布・原本初期技孵化3case限定受入、Actions原本終端確認。全体未完。';state['bp']['next_step']=s.NEXT
    state['next_action']=dict(state['next_action'],id='NATURAL_SUPPLY_REMAINING',goal_ja=s.NEXT,read_paths=[s.GUIDE,s.CP,SELF,gift.SELF])
    for p in s.CODE|{s.CP,s.GUIDE}:state['source_bindings'][p]=s.identity((s.ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    note=f"""
## {date.isoformat()}
- Timestamp: {date.isoformat()}
- Task: USER-20260925-NATURAL-SUPPLY / 終端照合
- Version: issue19-natural-supply-v1-complete
- Status: DONE（3case限定受入。Issue19/P08/release全体は未完）
- Summary: 通常配布/固定form初期技1件と原本初期技孵化2件を保存原本で受入。fixture捕獲/進行/Ringの通常取得は対象外。
- Files changed: 保存artifact専用validatorと{CLOSEOUT_TESTS}新試験、記録専用Actions、checkpoint/guide/固定引継ぎMD/JSON・両ログ・text証拠。
- Verify: native原本run{first}は2成功1失敗のfailure、run{second}は配布1成功、旧孵化2件は不変。初回20unit/中間12unit/配布phase変更影響13unitの実行原本を継承。今回新{CLOSEOUT_TESTS}unit、native/旧unit/host/ARM/Wiki再実行0。
- Failure retained: 配布counter一増加の未検証前提を、guard下の二遷移raw観測に修正。ROM/ゲームruntimeを変更してテストへ合わせていない。既受入原本を上書きしない。
- Commit: 同branchへ非force push。source/単一親/祖先/reflected-head/remoteを照合。
- Network: 保存Actions artifact{len(audit["receipts"])}件だけをhash照合。merge/release/baseline切替なし。一般CI全緑を主張しない。
"""
    for path in ('design/run_log.md','design/version_log.md'):
        with (s.ROOT/path).open('a') as f:f.write(note)


CLOSEOUT_TESTS=15


def main():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();cp=s.load(s.ROOT/s.CP)
    unit=(s.PROOF/'closeout-unit.stderr.txt').read_bytes()
    need(s.load(s.PROOF/'closeout-unit.process.json')=={'returncode':0,'timed_out':False} and re.search(rb'Ran '+str(CLOSEOUT_TESTS).encode()+rb' tests in ',unit) and b'\nOK\n' in unit,'新規終端unitの実行原本')
    versions={};receipts=[]
    for rid in sorted(set(cp['prior_runs']+[cp['run_id']])):
        expected=cp if rid==cp['run_id'] else s.load(s.ROOT/s.EVIDENCE/str(rid)/'verification.json')
        listing=fetch('actions/runs/'+str(rid)+'/artifacts?per_page=100')
        need(listing['total_count']==len(listing['artifacts'])==1,'artifact全件')
        artifact=listing['artifacts'][0];need(artifact['name']=='pr16-natural-supply-proof','artifact名')
        raw=fetch('actions/artifacts/'+str(artifact['id'])+'/zip',binary=True)
        v,data,reflected=unpack(raw,artifact,expected);audit=validate_cases(v,data);versions[rid]=v
        if rid==cp['run_id']:need(json.loads(data['gift-save-impact.json'])['source_contract']==gift.source_contract(),'移行/配布source契約不変')
        parent=subprocess.check_output(['git','rev-list','--parents','-n','1',reflected],cwd=s.ROOT).decode().split()
        need(parent==[reflected,expected['source_head']],'sourceからの単一親記録commit')
        subprocess.run(['git','merge-base','--is-ancestor',reflected,'HEAD'],cwd=s.ROOT,check=True)
        receipts.append(dict(audit,artifact=artifact,reflected_head=reflected,source_head=expected['source_head'],run_id=rid))
    totals=reconcile(cp,versions)
    s.write(s.PROOF/'artifact-closeout.json',dict(status='PASS_SAVED_NATIVE_ACTIONS_ARTIFACT',receipts=receipts,**totals,new_unit_tests=CLOSEOUT_TESTS,new_native_processes=0))
    gift.configure();s.CODE.update((SELF,TEST));s.publish=publish;s.complete()
    s.write(s.PROOF/'completion.json',{'task':s.TASK,'status':'PASS_SCOPED_3_CASES','terminal_actions':s.load(s.ROOT/s.CP)['terminal_actions'],'new_unit_tests':CLOSEOUT_TESTS,'new_native_processes':0,'old_unit_reruns':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0})
    print(json.dumps(dict(status='PASS_SAVED_NATIVE_ACTIONS_ARTIFACT',**totals)))


if __name__=='__main__':
    if len(sys.argv)==1:main()
    elif sys.argv[1:]==['paths']:print('\n'.join(sorted(s.owned())))
    elif sys.argv[1:]==['guard']:s.guard()
    else:raise SystemExit('usage: pr16_natural_supply_closeout.py [paths|guard]')
