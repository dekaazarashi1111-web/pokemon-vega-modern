#!/usr/bin/env python3
"""完了済み503新5勝/Save22原本のみを記録。nativeと受入68試験を再走しない。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save22_accept as m
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
import pr16_story_gym_record as log_gate
SOURCE='8c6f51827d3d51a1f2f25b4444f6103496d2ecba'
RUN=36668710078
JOB=109738877587
CONFIG=m.DEV+'/record-input.json'
SELF='scripts/pr16_story_save22_record.py'
TEST='tests/test_pr16_story_save22_record.py'
WF='.github/workflows/pr16-story-save22-record.yml'
CODE={SELF,TEST,WF,CONFIG}
EVIDENCE='content/modernization/pr16_story_save22_evidence'
OUT=ROOT/'.local/pr16-story-save22-record'
PUBLIC=OUT/'public'
STEPS=['Set up job','Run actions/checkout@v4','Scoped source guard before native',
       'New five trainers cave entrance Save22 and independent Continue only','Lightweight task graph',
       'Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
MEASURE_WF='.github/workflows/pr16-story-save22.yml'
MEASURE_CODE={MEASURE_WF,m.DEV+'/spec.json','scripts/pr16_story_save22_accept.py',
    'scripts/pr16_story_save22_measure.py','tests/test_pr16_story_save22_accept.py',
    'tests/test_pr16_story_save22_transport.py'}
EXPECTED=dict(size=27997,sha256='9104b9aa1b3fc654193932c48cbbf2863ff8610c6bfd466675a42cb79f66b4b7')
COUNTS=dict(source_head=SOURCE,run_id=RUN,new_tests=68,new_acceptance_tests=58,new_transport_tests=10,
    development_native_processes=2,development_native_failures=0,formal_native_processes=2,
    accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,development_cold_card_end_accepted=False,
    development_text_recovered_only_after_exact_predetermined_hash_match=True)
RECORD_TESTS=22
TEXT=('verification.json','measurement.json','manifest.json','parent.json','unit.stdout.txt','unit.stderr.txt',
      'transport-unit.stdout.txt','transport-unit.stderr.txt',
      'progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json',
      'continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json',
      'progress-development.stdout.txt','progress-development.commands.txt',
      'continue-development.stdout.txt','continue-development.commands.txt')


def terminal(run,jobs):
    required=dict(id=RUN,head_sha=SOURCE,head_branch=m.source.BRANCH,path=MEASURE_WF,
                  status='completed',conclusion='success',run_attempt=1)
    m.need(all(type(run.get(k)) is type(v) and run[k]==v for k,v in required.items()),'完了済み正式run初回だけ')
    m.need(type(jobs.get('total_count')) is int and jobs['total_count']==1 and len(jobs.get('jobs',[]))==1,'全jobページ')
    job=jobs['jobs'][0];required=dict(id=JOB,run_id=RUN,name='continuation',status='completed',conclusion='success')
    m.need(all(type(job.get(k)) is type(v) and job[k]==v for k,v in required.items()),'正式job identity/終端')
    m.need([x.get('name') for x in job.get('steps',[])]==STEPS and
           all(x.get('status')=='completed' and x.get('conclusion')=='success' for x in job['steps']),
           'upload/postを含む全8step成功')
    return dict(run=h.d.run_summary(run),job=job)


def counts(data):
    m.need(all(type(data.get(k)) is type(v) and data[k]==v for k,v in COUNTS.items()),'実行会計を再解釈しない')


def members(folder,expected):
    manifest=m.load((folder/'manifest.json').read_bytes())
    m.need(type(manifest) is dict and type(expected) is int and len(manifest)==expected,'manifest件数/type')
    for name in manifest:
        p=Path(name)
        m.need(type(name) is str and name and not p.is_absolute() and '..' not in p.parts and
               '\\' not in name and p.as_posix()==name and name!='manifest.json','安全な原本member名')
    m.need(not any(p.is_symlink() for p in folder.rglob('*')),'symlink禁止')
    names={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    m.need(names==set(manifest)|{'manifest.json'},'欠落/未宣言member禁止')
    for name,binding in manifest.items():m.need(m.identity((folder/name).read_bytes())==binding,'全member byte '+name)
    return manifest


def recover_expected(folder,dest,binding):
    """事前hashに固定された開発textだけを回収。未知出力から期待値を作らない。"""
    raw=(folder/'expected.json').read_bytes()
    m.need(binding==EXPECTED and m.identity(raw)==EXPECTED,'測定前に固定されたexpected全27997bytes')
    m.decode_plan(m.load(raw))
    m.need(not dest.exists(),'受入原本を上書きしない')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)



def goal(artifact):
    return (f'story-fastの唯一の開始点はartifact{artifact}のstory-fast.srm（Save22、131088bytes、'
        f'SHA256 {m.OUTPUT_SAVE["sha256"]}）。ちえのどうくつ北入口map1/36・4,6北・party4/RP0、'
        '12296円・badge1・var4071=6/4072=1。ミュウツーHP324/354・PP[1,14,5,5]、他3体HP満タン。'
        '503新5勝/6040円・北入口warp・通常Save22/独立Continueは完了。洞窟内部/階段/走破は未到達。'
        '現在地から通常storyの未完区間だけをSave/cold境界で進める。397/cold35入力・68試験・'
        'Save1〜21/旧BP/P08は無影響に再走しない。HM05は所持だけで未習得/未使用・原因未解決。'
        'Save21の同一拒否入力は繰り返さず、必要時は固定ROMの互換性判定ownerを限定照合し、'
        '承認済みfield-utility分離fixtureの自然取得条件を確認する。基準外習得を盲追加しない。'
        '分離progression原本Axew Lv37/EXP68589とNationalDex magic0・grant ownerを保全し、'
        'flag/var注入で解禁しない。正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・'
        'Lv100soak・研究施設自然到達・全storyは未完。')



def record():
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists() and not (ROOT/EVIDENCE).exists(),'未記録の初回だけ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    c=h.d.read(ROOT/CONFIG)
    m.need(set(c['record_source_bindings'])=={SELF,TEST} and h.d.bindings(c['record_source_bindings'])==c['record_source_bindings'],'ローカル検証済み記録source全byte')
    m.need(c['task']==m.TASK and c['source_head']==SOURCE and c['run_id']==RUN and c['job_id']==JOB,'固定測定identity')
    done=terminal(h.d.inputs.api(f'actions/runs/{RUN}'),h.d.inputs.api(f'actions/runs/{RUN}/jobs?per_page=100'))
    meta,z=transport.archive(c['artifact_id'],RUN,c['archive'],SOURCE)
    m.need(meta['name']=='pr16-story-save22-checkpoint','正式artifact名')
    folder=OUT/'original';folder.mkdir(parents=True)
    with z:z.extractall(folder)
    members(folder,c['manifest_members'])
    recover_expected(folder,ROOT/m.DEV/'expected.json',c['expected_json'])
    measured=h.d.read(folder/'measurement.json');counts(measured)
    m.need(set(measured['source_bindings'])==MEASURE_CODE,'全測定source集合')
    for path,binding in measured['source_bindings'].items():
        m.need(m.identity((ROOT/path).read_bytes())==binding and m.identity(h.d.git('show',SOURCE+':'+path))==binding,
               '測定source変更を自動追認しない '+path)
    m.need(measured['expected_json']==EXPECTED,'測定expected binding')
    for name,count in (('unit',58),('transport-unit',10)):
        log_gate.unit_original((folder/(name+'.stdout.txt')).read_bytes(),(folder/(name+'.stderr.txt')).read_bytes(),count)
    result,ledger=m.verify(folder);result=json.loads(json.dumps(result))
    m.need(result==measured['result']==h.d.read(folder/'verification.json') and
           m.identity((folder/'verification.json').read_bytes())==c['verification'],'全oracle値と原本')
    m.need(ledger==h.d.read(folder/'save-byte-ledger.json') and ledger['changed_bytes']==6895 and len(ledger['ranges'])==1836 and
           m.identity((folder/'save-byte-ledger.json').read_bytes())==c['save_byte_ledger'],'全差分ledger')
    m.need(set(c['additional_cold_screens'])=={'4','5'},'未受入coldの追加menu/fieldを両方照合')
    for index,binding in c['additional_cold_screens'].items():
        screen=(folder/f'continue/screen-{int(index):04d}.ppm').read_bytes()
        m.need(m.identity(screen)==binding,'追加cold目視原本全byte')
        m.screen_bytes(screen,dict(sha256=binding['sha256']))
    log_gate.unit_original((OUT/'preflight/unit.stdout.txt').read_bytes(),(OUT/'preflight/unit.stderr.txt').read_bytes(),RECORD_TESTS)
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    for name in TEXT:
        raw=(folder/name).read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'tracked textだけ')
        path=evidence/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    for suffix in ('stdout','stderr'):
        (evidence/f'record-unit.{suffix}.txt').write_bytes((OUT/f'preflight/unit.{suffix}.txt').read_bytes())
    checks=h.d.inputs.api('actions/runs?head_sha='+SOURCE+'&per_page=100')
    m.need(checks['total_count']==len(checks['workflow_runs']),'測定HEAD Actions全ページ')
    observed=[h.d.run_summary(r) for r in checks['workflow_runs']]
    done.update(artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        measured_head_checks=observed,general_ci_all_success_claimed=False,
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        record_native_processes=0,record_accepted_test_reruns=0,record_new_tests=RECORD_TESTS,record_compiles=0)
    prior_run=h.d.inputs.api('actions/runs/36663051577')
    prior_jobs=h.d.inputs.api('actions/runs/36663051577/jobs?per_page=100')
    m.need(prior_run['head_sha']=='dd00a9d0a585849c4395645ee0384944526d2272' and
        prior_run['path']=='.github/workflows/pr16-story-save21-record.yml' and
        prior_run['status']=='completed' and prior_run['conclusion']=='success' and prior_run['run_attempt']==1 and
        prior_jobs['total_count']==len(prior_jobs['jobs'])==1 and prior_jobs['jobs'][0]['id']==109721759017 and
        len(prior_jobs['jobs'][0]['steps'])==11 and all(s['status']=='completed' and s['conclusion']=='success'
        for s in prior_jobs['jobs'][0]['steps']),'旧Save21記録のpush/upload/post完了を別APIで照合')
    h.d.git('merge-base','--is-ancestor','98052e7f7671e401124628591e98ea10e91c722e',SOURCE)
    done['inherited_save21_record_completion']=dict(run=h.d.run_summary(prior_run),
        job=prior_jobs['jobs'][0],reflected_head='98052e7f7671e401124628591e98ea10e91c722e',new_native_processes=0)
    h.d.write(evidence/'terminal.json',done)
    h.d.write(evidence/'visual-review.json',dict(source_head=SOURCE,run_id=RUN,
        anchors=h.d.read(ROOT/m.DEV/'expected.json')['visual_review'],additional_cold_screens=c['additional_cold_screens'],
        total_reviewed_anchors=59,notes_ja='開発57anchorと追加cold4/5を目視。5戦の開始/勝利/各賞金、交代UI取消、観測37の接近中field、北入口warp、書込途中、party HP324/354・12296円/badge1、card/menuから操作可能fieldを照合。洞窟内部/走破、保存成功文言frame、HM05習得/使用は主張しない。'))
    paths={p.relative_to(ROOT).as_posix() for p in evidence.rglob('*') if p.is_file()};next_goal=goal(meta['id'])
    checkpoint=dict(schema_version=1,task=m.TASK,status=result['status'],source_head=SOURCE,run_id=RUN,job_id=JOB,
        actions_completion_confirmed=True,actions_conclusion='success',artifact=done['artifact'],verification=result,
        save22_accepted=True,source_bindings=measured['source_bindings'],evidence_bindings=h.d.bindings(paths),
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        save_byte_ledger=dict(binding=c['save_byte_ledger'],changed_bytes=6895,ranges=1836,artifact_only=True),
        next_goal_ja=next_goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    h.d.write(ROOT/m.CP,checkpoint)
    guide=f'''# 503新5勝・ちえのどうくつ北入口・Save22 限定受入

`{result['status']}`。Save21後の新しい通常trainer5戦と北入口へのwarp、通常Save22・独立Continueだけを受入。洞窟内部/階段/走破、HM05習得/使用、自然育成/進化、全国図鑑、研究施設自然到達、全storyは未受入。

## 原本と実行会計

測定source `{SOURCE}`、run `{RUN}`、job `{JOB}`、upload/postを含む全8step成功。artifact `{meta['id']}`、{c['archive']['size']}bytes、SHA256 `{c['archive']['sha256']}`、期限 `{meta['expires_at']}`。全{c['manifest_members']}member/93画面を全byte検証し、開発57anchorと追加cold4/5の計59anchorを目視。

397/cold35入力、41557/cold3464frames。開発2・正式2native成功、compile/ROM変更/旧受入case再走0。新58受入試験+10転送試験=68を開発/正式で二重計上しない。今回の記録は原本読取のみでnative/受入試験再走0、別の記録拒否22試験。開発cold30入力はcard終端で未受入。正式は固定prefixの後だけ退出入力を追加し、cold4のmenu/lock1とcold5のfield/lock0を区別した。

測定jobが再構成したexpected.json全27997bytesを、事前宣言SHA256 `{EXPECTED['sha256']}` と一致する場合だけ追跡へ回収する。未知出力から期待値を再生成しない。

## 新5戦と到達範囲

アミカtrainer102/240円、コウガ108/132円、アイク94/2600円、ルチア1362/2600円、ヘイスケ97/468円。賞金計6040円、6256→12296円。5戦の連続性と個別の勝利/賞金画面、保存physical bitを結合。観測8は同一戦闘の交代UI取消、観測37は次trainer接近中のlock1で、全5回のidle復帰を主張しない。残留battle_flags12/outcome1を追加勝利と数えず、野生勝利/逃走/捕獲/敗北/通常回復は0。

map3/21のwarp15,56から、観測80でmap1/36・4,6北へ通常移動。固定ROMの相互warp表と洞窟onloadの世界地図flag2217直接ownerを照合。新trainer5roots/30nodes・洞窟1node、diagnostics0。洞窟奥、帰りwarp実行、rematchは未受入。

## Saveと保全境界

Save22 `{m.OUTPUT_SAVE['sha256']}`、131088bytesは独立Continue後も全Save/RTC不変。party4/RP0・12296円・badge1、var4071=6/4072=1。ミュウツーHP324/354、技PP[1,14,5,5]、他3体HP満タン。全員Lv100でEXP/種族/技/装備は保持。600partybytesの差分はPP4bytes、HP1byte、slot1/3のoffset41各1byteのみ。offset41の因果owner/全なつき度の受入にしない。Mew/Bibarelの4技/PPは空のまま、全Bag slot/HM05保持。

全Save差分6895bytes/1836範囲。旧Save21 bank57344bytes、PC、未使用party200bytesを保持。sector checksum42件とS61E全payload/CRC/反転値を検証。legacy差分はtrainer5bitと2056/2217、vars4021:92→23/4022:2→3/404d:8→20だけ。flag2056と補助varのruntime ownerは未解決のまま、推測で受入範囲を広げない。NationalDex magic0/var404e0/flag840=0、分離progression/grant ownerを保持。

観測84/85は書込途中、86でSave22/Flash/field安定。保存成功文言frameは未採取。ROM/Save/全差分hex/画像はartifactだけ、tracked text原本は `{EVIDENCE}`。

## CI・旧受入との分離

前回Save21記録run36663051577/job109721759017のpush/upload/postを含む全11step成功を別APIで照合、反映HEAD98052e7fの祖先関係を確認。Save1〜21/旧BP/P08は再走しない。一般CIのP03 capacity段階failureと後続skip/artifact failureは専用成功と別scopeで保持し、全CI成功を主張しない。PR merge/release/active baseline切替なし。

## 次の唯一の開始点

{next_goal}

記録source `{os.environ['GITHUB_SHA']}`、run `{os.environ['GITHUB_RUN_ID']}`。記録自身のpush/upload/postは自己予測せず、別API・record-head.txt・record.zipで読戻し確認する。
'''
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    m.need(h.d.bindings(protected)==protected,'旧受入source/evidence不変')
    state.setdefault('observed_head_history',[]).append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],
        checks=state['observed_head_checks'],reason_ja='既に完了したSave22測定を原本から記録。Save21以前も今回の入力も再走しない。'))
    state['observed_head']=SOURCE
    state['observed_head_semantics']='503新5勝/6040円・ちえのどうくつ北入口・Save22測定source。洞窟内部/全story/自然育成/全国図鑑/HM05解決/記録commit/active baselineではない。'
    state['observed_head_checks']=dict(scope_head=SOURCE,runs=observed,reason_ja='専用runの全8step完了と全Save/画面を照合。一般CIは別scopeで全成功を主張しない。')
    now=datetime.datetime.now(datetime.timezone.utc);state['observed_date_jst']=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['story_save22']=dict(status=result['status'],checkpoint=m.CP,guide=m.GUIDE,run_id=RUN,artifact_id=meta['id'],
        story_fast_save=m.OUTPUT_SAVE,map=[1,36],xy=[4,6],facing=2,badge_count=1,money=12296,rp=0,
        story_vars={'4071':6,'4072':1},hm05_owned=True,hm05_taught_or_used=False,
        hm05_root_cause_resolved=False,inner_cave_reached=False,record_run_id=int(os.environ['GITHUB_RUN_ID']),
        next_goal_ja=next_goal,release_ready=False)
    state['story_save21']['record_completion']=done['inherited_save21_record_completion']
    state['next_action'].update(id='STORY_AFTER_CHIE_NORTH_ENTRANCE_SAVE22',goal_ja=next_goal,
        read_paths=[m.GUIDE,m.CP,'docs/PR16_NATIONAL_DEX_OWNER_JA.md','content/modernization/pr16_national_dex_owner_checkpoint.json',
                    'content/modernization/pr16_story_acceleration_checkpoint.json',m.DEV+'/expected.json',SELF],
        stop_rule_ja='Save22北入口より先だけを通常story/Save/cold境界で区切る。397/cold35入力・68試験・Save1〜21/旧BP/P08の無影響再走、HM05拒否の重複、互換性の盲修正、全国図鑑flag/var注入解禁は禁止。')
    state['bp']['next_step']=next_goal
    state['bp']['current_stop']='支援story-fastの503新5勝/6040円・洞窟北入口・Save22/独立Continueを限定受入。map1/36・4,6北・party4/RP0・12296円・badge1。HM05未習得/未使用・原因未解決。NationalDex magic0保全、洞窟内部/全story未完。'
    state['do_not_repeat'].append(f'Save22 run{RUN}の397/cold35入力・58+10試験・503新5勝/6040円/洞窟北入口/保存Continueは記録済み。無影響の再走禁止。Save21以前も不変。')
    owned={m.CP,m.GUIDE,m.DEV+'/expected.json',h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|MEASURE_CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}))
    publish_resume(state);stamp=now.isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK} / 503新5勝・洞窟北入口・Save22原本記録
- Version: story-route503-save22-v1
- Status: DONE（支援story新区間限定。洞窟内部/走破・HM05解決・自然育成/全国図鑑/全story未完）
- Summary: 既に完了したSave22の503新5勝/6040円・北入口warp・保存coldを受入。全121member/93画面/59目視anchor、全差分6895bytes・1836範囲。観測37接近中lock1、書込途中、開発card終端を過大受入しない。事前固定hashのexpected.jsonだけ回収。
- Files changed: 記録器/22拒否試験・専用workflow/設定・checkpoint/guide/text証跡・開発expected、固定再開MD/JSON、両ログ。ROM/save/全差分hexはartifactのみ。
- Verify: run{RUN}/job{JOB}全8step成功、artifact{meta['id']}。397/cold35入力、全Save/RTC131088bytes・checksum42件/S61E/旧bank/PC/Bag保持。元の新試験58+10を二重計上せず、記録native0・受入試験再走0・compile0。新記録22試験/scoped final-index/private/resume/task graph/diff通過後のみcommit。一般CI全成功は主張しない。
- Commit: 測定{SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。小分けWIP後、同branchへ非force pushと全text読戻し。
- Network: GitHub connector/固定Actions artifactのみ。開始HEAD8c6f5182と旧Save21記録run36663051577全11step成功を照合。旧BP/P08/Save1〜21/progression/grant owner/active baseline/source-lock不変、PR16未merge/releaseなし。P03 capacity段階の一般CI failureは別scope。
- Next: {next_goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write(entry)
    PUBLIC.mkdir(parents=True,exist_ok=True);h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',dict(status='RECORD_PREPARED_FROM_COMPLETED_SAVE22',terminal=done,owned=sorted(owned),
        manifest_members=c['manifest_members'],record_native_processes=0,record_accepted_test_reruns=0))


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard()
    h.d.git('diff','--cached','--check')


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            raw=h.d.git('show','HEAD:'+name);m.need(raw==(ROOT/name).read_bytes(),'commit済み全text読戻し '+name);z.writestr(name,raw)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot)
    m.need(len(sys.argv)==2 and sys.argv[1] in actions,'record|guard|snapshot');actions[sys.argv[1]]()
