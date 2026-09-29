#!/usr/bin/env python3
"""完了済みSave17原本だけを記録。core/compile/受入試験の再実行0。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'),str(ROOT)]
import pr16_story_after_maori_accept as m
SELF = 'scripts/pr16_story_after_maori_record.py'
WF = '.github/workflows/pr16-story-after-maori-record.yml'
TEST = 'tests/test_pr16_story_after_maori_record.py'
RUN = 36510782954
JOB = 109222190727
SOURCE = '0c5a118c855ee52eecbadaa7c4114d32a59e500f'
ARTIFACT = 11008723945
ARCHIVE = dict(size=18112423,sha256='e78ed5327d55427cca992406d43fa488f92065d11fe0bc0636493a83c97fb4db')
OUT = ROOT/'.local/pr16-story-after-maori-record'
PUBLIC = OUT/'public'
EVIDENCE = 'content/modernization/pr16_story_after_maori_evidence'
STEP_NAMES = ['Set up job','Run actions/checkout@v4','New Save17 interval and independent Continue only',
              'Lightweight task graph','Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
TEXT = ('verification.json','measurement.json','manifest.json','unit.stdout.txt','unit.stderr.txt',
        'progress/stdout.txt','progress/stderr.txt','continue/stdout.txt','continue/stderr.txt',
        'inspection.json','prior-19-unit.stderr.txt','prior-19-receipt.json','development-failure-receipt.json')
GOAL = ('story-fastはアヤメシティ通常回復Save17を唯一の開始点とする。artifact11008723945のstory-fast.srmを'
        '復元し、map5/4・7,4・北向きのポケモンセンターから通常の出口・町イベントを進める。'
        '今回の317/cold22入力・34試験・受入済み19試験・マオリ・旧BP/P08/Save1〜16は影響なしに再走しない。'
        '全国図鑑正規解禁へ向けて通常storyを継続し、次の自然保存境界で区切る。'
        'progression原本は戦闘前Axew Lv37/EXP68589のまま保持し、NationalDex magic0を注入で解除しない。'
        '自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。')


def completed(run,jobs):
    m.need(run.get('id') == RUN and run.get('head_sha') == SOURCE and
           run.get('head_branch') == m.source.BRANCH and run.get('path') == '.github/workflows/pr16-story-after-maori.yml' and
           run.get('status') == 'completed' and run.get('conclusion') == 'success' and
           type(run.get('run_attempt')) is int and run['run_attempt'] == 1, 'exact successful measurement terminal')
    m.need(jobs.get('total_count') == 1 and len(jobs.get('jobs',[])) == 1, 'complete job page')
    job = jobs['jobs'][0]
    m.need(job.get('id') == JOB and job.get('run_id') == RUN and job.get('name') == 'continuation' and
           job.get('status') == 'completed' and job.get('conclusion') == 'success', 'exact native job')
    m.need([x.get('name') for x in job.get('steps',[])] == STEP_NAMES and
           all(x.get('status') == 'completed' and x.get('conclusion') == 'success' for x in job['steps']),
           'all seven steps including upload/post must be completed/success')
    return dict(run={k:run[k] for k in ('id','head_sha','head_branch','path','status','conclusion','run_attempt')},
                job={k:job[k] for k in ('id','run_id','name','status','conclusion','steps')})


def artifact_meta(meta):
    m.need(meta.get('id') == ARTIFACT and meta.get('size_in_bytes') == ARCHIVE['size'] and
           meta.get('digest') == 'sha256:'+ARCHIVE['sha256'] and meta.get('expired') is False and
           meta.get('name') == 'pr16-story-after-maori-checkpoint' and
           meta.get('workflow_run',{}).get('id') == RUN and meta['workflow_run'].get('head_sha') == SOURCE,
           'immutable complete artifact, not a convenient replacement')


def record():
    import pr16_research_story_route_actions as h
    import pr16_story_after_maori_measure as measure
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT)
    h.d.current()
    state = h.source_check()
    m.need(not (ROOT/m.CP).exists() and not (ROOT/EVIDENCE).exists(), 'no duplicate accepted record')
    before = h.d.bindings(set(state['source_bindings']) | h.d.PROTECTED)
    terminal = completed(h.d.inputs.api(f'actions/runs/{RUN}'),h.d.inputs.api(f'actions/runs/{RUN}/jobs?per_page=100'))
    meta = h.d.inputs.api(f'actions/artifacts/{ARTIFACT}')
    artifact_meta(meta)
    raw = h.d.inputs.api(f'actions/artifacts/{ARTIFACT}/zip',True)
    m.need(m.identity(raw) == ARCHIVE, 'complete 18112423-byte archive')
    folder = OUT/'original'
    folder.mkdir(parents=True)
    with h.safe_zip(raw,80000000) as z:
        manifest = json.loads(z.read('manifest.json'))
        m.need(len(manifest) == 144 and set(z.namelist()) == set(manifest) | {'manifest.json'}, 'all 144 members')
        for name,binding in manifest.items():
            m.need(m.identity(z.read(name)) == binding, 'original member '+name)
        z.extractall(folder)
    measured = json.loads((folder/'measurement.json').read_bytes())
    m.need(measured['run_id'] == RUN and measured['source_head'] == SOURCE and measured['focused_tests'] == 34 and
           measured['formal_native_processes'] == 2 and measured['development_native_processes'] == 3 and
           measured['development_failed_native'] == 1 and measured['accepted_case_reruns'] == 0 and
           measured['reused_prior_tests'] == 19 and measured['prior_test_reruns'] == 0, 'original execution accounting')
    for path,binding in measured['source_bindings'].items():
        m.need(m.identity((ROOT/path).read_bytes()) == binding and m.identity(h.d.git('show',SOURCE+':'+path)) == binding,
               'unchanged measured source '+path)
    v,ledger = m.verify(folder)
    v = json.loads(json.dumps(v))  # JSON array normalization only; no result/field rewriting.
    m.need(v == measured['result'] == json.loads((folder/'verification.json').read_bytes()), 'read-only oracle equality')
    m.need(ledger == json.loads((folder/'save-byte-ledger.json').read_bytes()) and
           m.identity((folder/'save-byte-ledger.json').read_bytes()) == measured['save_byte_ledger'], 'complete original byte ledger')
    unit = (folder/'unit.stderr.txt').read_bytes()
    m.need(not (folder/'unit.stdout.txt').read_bytes() and unit.count(b' ... ok\n') == 34 and b'\nOK\n' in unit and
           b'skipped' not in unit and b'FAILED' not in unit, 'reuse original34; never rerun acceptance')
    evidence = ROOT/EVIDENCE
    evidence.mkdir()
    for name in TEXT:
        data = (folder/name).read_bytes()
        data.decode('utf-8')
        m.need(b'\0' not in data, 'tracked text only')
        target = evidence/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    checks = h.d.inputs.api('actions/runs?head_sha='+SOURCE+'&per_page=100')
    m.need(checks['total_count'] == len(checks['workflow_runs']), 'complete measured-head Actions page')
    latest = [h.d.run_summary(r) for r in checks['workflow_runs']]
    terminal.update(record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        record_native_processes=0,record_accepted_test_reruns=0,record_compiles=0,record_new_gate_tests=16,
        formal_artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','expires_at','workflow_run')},
        measured_head_actions=latest,general_ci_all_success_claimed=False)
    h.d.write(evidence/'terminal.json',terminal)
    review = json.loads((ROOT/m.DEV/'expected.json').read_text())['visual_review']
    checkpoint = dict(schema_version=1,task=m.TASK,status='PASS_STORY_AFTER_MAORI_AYAME_SAVE17_SCOPED',
        source_head=SOURCE,run_id=RUN,job_id=JOB,actions_completion_confirmed=True,actions_conclusion='success',
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        terminal_evidence=EVIDENCE+'/terminal.json',artifact=terminal['formal_artifact'],verification=v,
        save_byte_ledger=dict(binding=measured['save_byte_ledger'],changed_bytes=ledger['changed_bytes'],
            ranges=len(ledger['ranges']),artifact_only=True),visual_review=review,
        source_bindings=measured['source_bindings'],evidence_bindings=h.d.bindings({EVIDENCE+'/'+n for n in TEXT+('terminal.json',)}),
        next_goal_ja=GOAL,record_native_processes=0,record_accepted_case_reruns=0,
        general_ci_all_success_claimed=False,release_ready=False,active_baseline_changed=False)
    h.d.write(ROOT/m.CP,checkpoint)
    guide = f'''# マオリ後の通常進行・アヤメSave17 限定受入

## 完了範囲

`PASS_STORY_AFTER_MAORI_AYAME_SAVE17_SCOPED`。固定Save16から502番道路を通常移動し、ミキとスイの双子戦、ムギヒコ、ブンタの計3戦に勝利。通常ゲートを通過し、アヤメシティのポケモンセンターで通常回復・Save17・独立Continue・手持ちUI確認まで完了した。

自己OT Lv100支援partyのstory-fast限定。自然入手、自然育成、自然難易度、進化、研究施設自然到達、全storyを受入したものではない。NationalDex magic0を保持。flag注入・host書込・ROM変更・compile・旧受入の明示再走0。

## 原本・実測

測定source `{SOURCE}`、run `{RUN}`、job `{JOB}` の全7stepが completed/success。artifact `{ARTIFACT}` は {ARCHIVE['size']}bytes、SHA-256 `{ARCHIVE['sha256']}`、期限 `{meta['expires_at']}`。manifestと全144memberを照合。ROM/Save/119画像/全Save byte差分はartifactのみ、追跡textは `{EVIDENCE}`。

progress317入力・28007frames・116画面、cold22入力・1746frames・3画面。全119画像の形式/全byte SHA/非空を検証し、開発時の直接pixelレビュー31anchorを同一hashの正式画像に結び付けた。双子戦の味方誤攻撃も通常入力のまま保持した。賞金168+108+160=436、所持金2936→3372。新規34試験は開発とActionsで同じ34件を実行した数であり、68別件とは数えない。先行19試験は同一sourceの完了原本を再利用し、再実行0。

3戦はBATTLE開始14/47/69、勝利35/59/80、field解錠39/61/82で判定。ひんしやfieldに残るoutcome1を追加勝利に数えない。map列は3/19→3/20→3/11→3/20→3/1→5/4。保存中113の部分Flash変更を保存完了と混同せず、114/115のcounter17・解錠とcoldで確定した。保存成功文言そのもののframeは未取得。

全Save/RTC131088bytesがcold後も一致。前回bank57344bytes、PC section5〜13、未使用party200bytes、全5Bag pocketを保持。party600bytesの差分は8bytes（友情/PP/通常戦闘EV）。species/EXP/Lv100/状態保持、4体全回復。3trainer flag175/190/702を新ROM ownerと照合し、別flag913は4戦目と数えない。全Save差分{ledger['changed_bytes']}bytes/{len(ledger['ranges'])}範囲を再構成一致。一般sector checksum全体の受入は主張しない。

## 失敗も含む実行数

開発native3（保存前の900frame上限違反1、修正後progress1、cold1）。失敗SaveはSave16のまま。修正は600frame上限と起動前の全操作列検査。失敗stdout全73502bytesが正式成功stdoutのprefixと一致し、失敗の再実行はしていない。初期Actionsのfixture転記失敗36507857717と出力directory事前作成衝突36508880929はいずれもnative0で停止し、今回修正済み。正式native2、記録native/compile/受入試験再実行0。既存push CIは専用測定の実行数と分け、全成功とは主張しない。

## 次の唯一のstory-fast開始点

同artifactの `story-fast.srm`（`cold.srm`も全byte同一）。131088bytes、SHA-256 `{m.OUTPUT_SAVE['sha256']}`、counter17、map5/4（アヤメシティ・ポケモンセンター）、座標7,4、北向き。party4/RP0。ROMは既存33554432bytes、SHA-256 `{m.source.CANDIDATE['sha256']}` のまま。

{GOAL}

非支援Save14・分離progression原本・全国図鑑owner・正式BP/P08受入を変更しない。旧候補や別baselineへ混ぜない。PR16 open/draft/未merge、release=false、active baseline/source-lock不変。source-validationの旧P03 capacity原本段階failureやaction_requiredを本scopeの成功に合算しない。

記録workflow自身のpush/upload終端は自己予測しない。record run `{os.environ['GITHUB_RUN_ID']}` をAPIで別照合する。記録commitと全textの読戻し結果はそのartifactの `record-head.txt` / `record.zip` が正本。
'''
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    m.need(h.d.bindings(before) == before, 'previous accepted sources unchanged before publish')
    state.setdefault('observed_head_history',[]).append(dict(head=state['observed_head'],
        semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],
        reason_ja='旧受入/全国図鑑ownerを保持し、通常3戦・アヤメSave17の別scopeを追加。'))
    state['observed_head'] = SOURCE
    state['observed_head_semantics'] = '支援story-fastの通常3戦・アヤメ回復Save17測定source。進化/自然育成/全story、記録commit、active baselineではない。'
    state['observed_head_checks'] = dict(scope_head=SOURCE,runs=latest,
        reason_ja='専用run36510782954/job109222190727全7stepと144memberを照合。既存push CIのfailure/action_requiredは別scope。記録workflow自身の終端は別API照合。')
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    state['observed_date_jst'] = now.date().isoformat()
    state['story_after_maori'] = dict(status=checkpoint['status'],checkpoint=m.CP,guide=m.GUIDE,
        run_id=RUN,artifact_id=ARTIFACT,story_fast_save=m.OUTPUT_SAVE,record_run_id=int(os.environ['GITHUB_RUN_ID']),
        map=[5,4],xy=[7,4],facing=2,next_goal_ja=GOAL,release_ready=False)
    state['next_action'].update(id='STORY_AFTER_AYAME_SAVE17',goal_ja=GOAL,
        read_paths=[m.GUIDE,m.CP,'docs/PR16_NATIONAL_DEX_OWNER_JA.md',
            'content/modernization/pr16_national_dex_owner_checkpoint.json',
            'content/modernization/pr16_story_acceleration_checkpoint.json',m.DEV+'/expected.json',SELF],
        stop_rule_ja='新しい通常story区間を自然Save/cold境界で区切る。受入済み317/cold22、34/19試験、旧BP/P08/マオリを再走しない。異常時は原本と失敗証跡を保全し、成功へ読み替えない。')
    state['bp']['next_step'] = GOAL
    state['bp']['current_stop'] = '支援story-fastで502番道路の通常3戦・ゲート通過・アヤメPC通常回復Save17・独立Continueを限定受入。全Save/RTC131088bytes保持、map5/4・7,4北、party4/RP0。全国図鑑magic0・progression進化blockedは維持。次はartifact11008723945から先の通常story。'
    owned = {m.CP,m.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS} | {EVIDENCE+'/'+n for n in TEXT+('terminal.json',)}
    bound = (owned | measure.CODE | {SELF,WF,TEST}) - {h.d.STATE,h.d.DOC,*h.d.LOGS}
    state['source_bindings'].update(h.d.bindings(bound))
    publish_resume(state)
    stamp = now.isoformat(timespec='seconds')
    entry = f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK} / マオリ後3戦・アヤメ通常回復Save17
- Version: story-after-maori-v1
- Status: DONE（支援storyの新規区間限定。自然育成/進化/全story未完）
- Summary: 固定Save16→双子/ムギヒコ/ブンタ3勝・通常gate・アヤメPC全回復・Save17・独立Continue。賞金436。317/cold22入力、119画面。保存中113と完了114を分離。味方誤攻撃と失敗実行を隠さず保持。
- Files changed: 新区間入力、600frame境界/検証器/34試験、正式測定/記録、text証跡/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/Save/画像/全差分hexはartifactのみ。
- Verify: run{RUN}/job{JOB}全7step成功、artifact{ARTIFACT}全144member hash、全Save差分6620bytes/1732範囲再構成一致、cold全131088bytes、前bank57344bytes/PC/Bag保持。開発34/正式34は同じ新34件。先行19原本再利用。新規記録gate16試験。開発native3（失敗1）/正式2、記録native0/受入再走0/compile0。scoped index/private path/resume/task graph/diff後のみcommit。既存push CIは別scopeで全成功としない。
- Commit: WIPf37b7c8/9bb7577、測定source{SOURCE}。記録source={os.environ['GITHUB_SHA']}、run={os.environ['GITHUB_RUN_ID']}。同branch非force push・全text読戻し。
- Network: 固定GitHub HEAD/run/artifact。旧受入/BP/P08/非支援Save14/progression/全国図鑑owner/active baseline/source-lock不変。PR16未merge、releaseなし。
- Next: {GOAL}
'''
    for path in h.d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as stream: stream.write(entry)
    PUBLIC.mkdir(parents=True)
    h.d.write(OUT/'owned.json',sorted(owned))
    h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',dict(status='RECORD_PREPARED_FROM_COMPLETED_ORIGINAL',terminal=terminal,
        owned=sorted(owned),verified_members=144,record_native_processes=0,record_accepted_test_reruns=0))


def guard():
    import pr16_research_story_route_actions as h
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current()
    pr16_resume.validate(ROOT)
    g.START = os.environ['GITHUB_SHA']
    g.CODE = set()
    g.OWNED = set(h.d.read(OUT/'owned.json'))
    g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


def snapshot():
    import pr16_research_story_route_actions as h
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            data = h.d.git('show','HEAD:'+name)
            m.need(data == (ROOT/name).read_bytes(), 'committed text readback '+name)
            z.writestr(name,data)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__ == '__main__':
    commands = dict(record=record,guard=guard,snapshot=snapshot)
    m.need(len(sys.argv) == 2 and sys.argv[1] in commands, 'record|guard|snapshot')
    commands[sys.argv[1]]()
