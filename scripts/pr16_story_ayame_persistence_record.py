#!/usr/bin/env python3
"""Save18監査の追加記録。既存受入source/開始Saveを変更しない。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_ayame_persistence_audit as m
import pr16_research_story_route_actions as h
from pr16_learnset_compact_record import publish_resume
SELF='scripts/pr16_story_ayame_persistence_record.py'
WF='.github/workflows/pr16-story-ayame-persistence-audit.yml'
CORE='scripts/pr16_story_ayame_persistence_audit.py'
TEST='tests/test_pr16_story_ayame_persistence_audit.py'
CODE={SELF,WF,CORE,TEST}
CP='content/modernization/pr16_story_ayame_persistence_audit.json'
GUIDE='docs/PR16_STORY_AYAME_PERSISTENCE_AUDIT_JA.md'
EVIDENCE='content/modernization/pr16_story_ayame_persistence_evidence'
OUT=ROOT/'.local/pr16-ayame-persistence'
PUBLIC=OUT/'public'
PARENT='content/modernization/pr16_story_ayame_gate_checkpoint.json'
PARALLEL='content/modernization/pr16_story_ayame_gate_development/parallel_development.json'
LOCAL={CORE:dict(size=9874,sha256='6b9eb2f5dde59ce956825a4dcf634c69620dc3bc4971cf9902a2c81141ebc7df'),
       TEST:dict(size=7865,sha256='5ac0ae3594afcc1cda56e3cc2f9c43076a951fd5369d5ff878216df342d342b3')}


def record():
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/CP).exists(), '初回監査記録のみ')
    m.need(h.d.bindings(LOCAL)==LOCAL, 'ローカル42試験と同じsource bytes')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    parent=h.d.read(ROOT/PARENT)
    m.need(parent['run_id']==m.RUN and parent['source_head']==m.SOURCE and parent['actions_completion_confirmed'] is True,
           'Save18正式受入を保持して補強。並行Saveを開始点にしない')
    terminal=m.terminal(h.d.inputs.api(f'actions/runs/{m.RUN}'),
                        h.d.inputs.api(f'actions/runs/{m.RUN}/jobs?per_page=100'))
    record_id=parent['record_run_id']
    pr=h.d.inputs.api(f'actions/runs/{record_id}');pj=h.d.inputs.api(f'actions/runs/{record_id}/jobs?per_page=100')
    m.need(pr['id']==record_id and pr['head_sha']==parent['record_source_head'] and
           pr['path']=='.github/workflows/pr16-story-ayame-record.yml' and
           pr['status']=='completed' and pr['conclusion']=='success' and
           pj['total_count']==len(pj['jobs'])==1 and pj['jobs'][0]['status']=='completed' and
           pj['jobs'][0]['conclusion']=='success' and len(pj['jobs'][0]['steps'])>=7 and
           all(s['status']=='completed' and s['conclusion']=='success' for s in pj['jobs'][0]['steps']),
           '親記録runのpush/upload/postも完了済みであること')
    terminal['parent_record']=dict(run={k:pr[k] for k in ('id','head_sha','path','status','conclusion')},
                                   job={k:pj['jobs'][0][k] for k in ('id','status','conclusion','steps')})
    meta=h.d.inputs.api(f'actions/artifacts/{m.ARTIFACT}')
    m.need(meta['id']==m.ARTIFACT and meta['expired'] is False and meta['size_in_bytes']==m.ARCHIVE['size'] and
           meta['digest']=='sha256:'+m.ARCHIVE['sha256'] and meta['workflow_run']['id']==m.RUN and
           meta['workflow_run']['head_sha']==m.SOURCE, '原本artifact metadata')
    raw=h.d.inputs.api(f'actions/artifacts/{m.ARTIFACT}/zip',True)
    m.need(m.identity(raw)==m.ARCHIVE, '外側18101058bytes hash')
    with h.safe_zip(raw,100000000) as z:
        result=m.audit(z)
        measured=json.loads(z.read('measurement.json'))
        for path,binding in measured['source_bindings'].items():
            m.need(m.identity((ROOT/path).read_bytes())==binding and
                   m.identity(h.d.git('show',m.SOURCE+':'+path))==binding, '既存測定source不変: '+path)
    unit=(PUBLIC/'unit.stderr.txt').read_bytes()
    m.need(not (PUBLIC/'unit.stdout.txt').read_bytes() and unit.count(b' ... ok\n')==42 and
           b'\nOK\n' in unit and b'FAILED' not in unit and b'skipped' not in unit, '新42試験のみ成功')
    checks=h.d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=100')
    m.need(checks['total_count']==len(checks['workflow_runs']), '現在source Actions一覧の完全性')
    terminal.update(audit_source_head=os.environ['GITHUB_SHA'],audit_run_id=int(os.environ['GITHUB_RUN_ID']),
        original_artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','expires_at','workflow_run')},
        current_source_actions=[h.d.run_summary(r) for r in checks['workflow_runs']],
        current_audit_terminal_confirmed=False,general_ci_all_success_claimed=False)
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    h.d.write(evidence/'audit.json',result);h.d.write(evidence/'terminal.json',terminal)
    for name in ('unit.stdout.txt','unit.stderr.txt'):(evidence/name).write_bytes((PUBLIC/name).read_bytes())
    cp=dict(schema_version=1,task=m.TASK,status=result['status'],verification=result,terminal_evidence=EVIDENCE+'/terminal.json',
        audit_source_head=os.environ['GITHUB_SHA'],audit_run_id=int(os.environ['GITHUB_RUN_ID']),focused_tests=42,
        source_bindings=h.d.bindings(CODE|{PARALLEL}),evidence_bindings=h.d.bindings({EVIDENCE+'/'+n for n in
        ('audit.json','terminal.json','unit.stdout.txt','unit.stderr.txt')}),native_processes=0,accepted_test_reruns=0,
        release_ready=False,active_baseline_changed=False)
    h.d.write(ROOT/CP,cp)
    guide=f'''# アヤメSave18 保存領域の独立監査

`{result['status']}`。正式測定run{m.RUN}/job{m.JOB}の全7stepと、その記録run{record_id}のpush/upload/post終端を照合した。原本artifact{m.ARTIFACT}の外側SHA-256 `{m.ARCHIVE['sha256']}` と全170memberを検証。新しいnative実行・ROM生成・既存55試験の再実行は0。

実ROMの0x080DB224→0x083C4B28が示す14section配置からchecksum長を取得し、inputのcounter16/17とoutputの18/17の4bank・56件を検査した。同じ前世代bankをinput/outputで照合した件数を含み、56種類の独立Saveとは数えない。対象は宣言されたpayloadのみ。S61E拡張record、padding、RTCはstock checksumの対象と主張しない。S61Eの既受入CRC32判定を改変しない。

既受入map22/1 rootのtrainer ID1/1200/1203を、現ROMの372行remap表へ結合。external0x501/0x9B0/0x9B3→physical0x501/0x63D/0x63Fの3bitだけが0→1になった。section2相対bit1/317/319をtrainer IDと誤認しない。新規のnative call-path試験ではなく、完了原本の静的表・保存対応照合である。

legacy var全256件の差分は0x4021:93→5、0x4022:1→2、0x404D:0→8、0x4071:1→3。前3件のruntime owner同定は主張しない。連戦完了var0x4071は既受入map rootの完了値3と一致。NationalDex magic/flag0x840/var0x404Eと後続story var0x4072はいずれも0。注入による解禁・自然育成・進化・ジムリーダー勝利・全storyを受入しない。

唯一の次のstory-fast開始点は既存artifact{m.ARTIFACT}の `story-fast.srm`、SHA-256 `{m.OUTPUT_SHA}`、131088bytes、counter18、map5/4・7,4北、party4/RP0。同じartifactのcold.srmは全byte一致。前Save17 bank57344bytesも保持する。

新42試験は開発とActionsで同じ42件を確認したもので、84別件とは数えない。checksum/endian/overflow/対象外padding、sector重複/署名/部分世代、remap重複/誤physical、進行未完/全国図鑑注入、欠けたjob一覧/upload/post終端を拒否する。影響なしに再実行しない。

並行セッションの別Save948d9e58…（通常報酬取得済み）は `{PARALLEL}` に未採用開発履歴として分離した。非force拒否で同時更新を検知した後、正式nativeの重複起動0。正式Save dc1f690f…へ置換しない。並行開発native2は監査native0とは別計数。既存55試験・record工程・ROM/原本・全国図鑑owner・active baselineを維持した。

監査run自身 `{os.environ['GITHUB_RUN_ID']}` の最終push/uploadは自己予測しない。終了後のAPI照合とartifact内record-head.txt/record.zipを参照する。一般CIは全greenと主張しない。
'''
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    m.need(h.d.bindings(protected)==protected, '既受入binding/保護対象不変')
    state['story_ayame_persistence_audit']=dict(status=result['status'],checkpoint=CP,guide=GUIDE,
        audit_run_id=int(os.environ['GITHUB_RUN_ID']),parent_artifact_id=m.ARTIFACT,focused_tests=42,native_processes=0)
    for path in (GUIDE,CP):
        if path not in state['next_action']['read_paths']:state['next_action']['read_paths'].append(path)
    state['bp']['current_stop']+=' 正式Save18のROM宣言payload checksum56件と三兄弟physical flags/var4071の保存対応を別監査済み。'
    owned={CP,GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|{p.relative_to(ROOT).as_posix() for p in evidence.iterdir()}
    state['source_bindings'].update(h.d.bindings((owned|CODE|{PARALLEL})-{h.d.STATE,h.d.DOC,*h.d.LOGS}))
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK}
- Version: ayame-persistence-audit-v1
- Status: DONE（正式Save18原本の保存対応のみ。全story/自然育成/進化未完）
- Summary: 実ROM section tableから56件payload checksum、372行trainer remapと保存3bit、var4071の1→3、NationalDex3条件0を独立照合。S61E/padding/RTCはstock checksum対象外。4bankの重複前世代照合を別Saveと数えない。
- Files changed: 独立監査器/新42試験/記録workflow、監査JSON/text/guide、固定再開MD/JSON、両ログ。既存測定sourceと開始Saveを変更しない。
- Verify: run{m.RUN}/job{m.JOB}全7step、記録run{record_id}全終端、artifact{m.ARTIFACT}全170member。新42試験PASS。旧55試験再走0、監査native/compile/host書込0、全Save/RTC一致。resume/task graph/scoped index/private/diff後のみcommit。
- Commit: 監査source={os.environ['GITHUB_SHA']}、run={os.environ['GITHUB_RUN_ID']}。同branchへ非force pushし全text読戻し。自己終端は後続API照合。
- Network: 公式GitHub既完了原本を読取専用で再利用。並行Save948d9e58…は未採用履歴。正式dc1f690f…を維持。一般CI全成功とは主張しない。
- Next: 正式Save18から通常アヤメジムへ。旧連戦/55試験/この42試験を影響なしに再実行しない。NationalDex/progression停止条件とactive baselineを維持。
'''
    for path in h.d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as f:f.write(entry)
    h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',dict(status=result['status'],owned=sorted(owned),native_processes=0,focused_tests=42))


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in h.d.read(OUT/'owned.json'):
            raw=h.d.git('show','HEAD:'+path);m.need(raw==(ROOT/path).read_bytes(),'全text読戻し')
            z.writestr(path,raw)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    modes=dict(record=record,guard=guard,snapshot=snapshot)
    m.need(len(sys.argv)==2 and sys.argv[1] in modes,'record|guard|snapshot')
    modes[sys.argv[1]]()
