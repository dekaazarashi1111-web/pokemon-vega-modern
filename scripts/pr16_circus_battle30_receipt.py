#!/usr/bin/env python3
"""完了runの原本/表示を照合し、nativeを再実行せず固定引継ぎを確定する。"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
TASK='USER-20260920-CIRCUS-BATTLE30-RECEIPT'
REPORT='content/modernization/pr16_circus_battle30_pp.json'
RECEIPT='content/modernization/pr16_circus_battle30_receipt.json'
RUN=35479503528
JOB=105994620734
SOURCE='7ac90a66df9a31212fb09cedbd430d59d62649bf'
# 完了artifactのmetadata/byte/画像を照合してから固定する。
ARTIFACT=10596015821
ARCHIVE=dict(size=1074450,sha256='ac762db37f9402ea03db1d8f6a8f763e4ad48cde228297b9117ea23509246ecf')
BASE='b5f7d5d4966d8a32ea90200f0abee2131e030449'
VISUAL={'circus-continuous-30-save-streak-136-settled.ppm': '29戦目の勝利後、通常の交換確認（はい/いいえ）と日本語本文が表示されている。', 'circus-continuous-30-save-streak-138-action.ppm': '30戦目の先発対面。自軍HP182/182と相手・自軍の表示を確認。', 'circus-continuous-30-save-streak-139-outcome.ppm': '30戦目の終端で相手の場が空き、自軍HP93/163が表示されている。勝利判定は原本outcome=1と照合する。', 'circus-continuous-30-save-streak-140-settled.ppm': '10組目の3連勝報酬9BPの日本語表示。累計30勝/90BPは30件の原本と管理領域で照合し、この画面単体から推測しない。', 'circus-continuous-30-save-streak-142-saved.ppm': '通常Save後の元の受付前フィールド。黒画面や文字化けを認めない。', 'circus-continuous-30-save-streak-143-reloaded.ppm': 'fresh Continue後、保存時と同じ受付前フィールドを表示。保存値の一致は原本で別途検証する。'}
FILES=('scripts/pr16_circus_battle30_receipt.py','tests/test_pr16_circus_battle30_receipt.py',
       '.github/workflows/pr16-circus-battle30-receipt.yml')
PREFIX=f'evidence/pr16_circus_battle30_pp/{RUN}/execution/'
CASE='circus-continuous-30-save'
TARGET={'size':33554432,'sha256':'2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183'}


def need(value,message):
    if not value:raise ValueError(message)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def members(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist();need(len(names)==len(set(names)),'duplicate artifact member')
        result={}
        for item in z.infolist():
            path=PurePosixPath(item.filename)
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in item.filename,'unsafe artifact member')
            need((item.external_attr>>16)&0o170000!=0o120000,'symlink artifact member')
            need(item.file_size<=4_000_000,'oversized artifact member')
            if not item.is_dir():
                need(path.suffix in ('.json','.c','.h','.stdout','.stderr','.ppm'),'unexpected artifact type')
                result[item.filename]=z.read(item)
        return result


def validate(report,raw,run,job,artifact,visual):
    need(identity(raw)==ARCHIVE,'archive bytes differ')
    need(run['id']==RUN and run['head_sha']==SOURCE and run['status']=='completed','run scope')
    need(job['id']==JOB and job['run_id']==RUN and job['status']=='completed','job scope')
    need(artifact['id']==ARTIFACT and artifact['workflow_run']['id']==RUN
         and artifact['workflow_run']['head_sha']==SOURCE and not artifact['expired']
         and artifact['size_in_bytes']==ARCHIVE['size'] and artifact['digest']=='sha256:'+ARCHIVE['sha256'],'artifact scope')
    need(report['recording_run']==RUN and report['source_head']==SOURCE and report['candidate']==TARGET,'report scope')
    need(report['new_emulator_processes']==1 and report['arm_compiles']==report['arm_links']==report['rom_changes']==0
         and report['accepted_standalone_replays']==0,'execution accounting')
    files=members(raw);native=json.loads(files['native-result.json'])
    for key in ('source_head','workflow_source_head','candidate','process','result','prefix','matchup_prefix','generated',
                'screens','failures','lifecycle_verified','genuine_30_wins_verified','executable','native_source_head'):
        need(native[key]==report[key],'native/report projection: '+key)
    for suffix in ('.stdout','.stderr','.process.json'):
        name=CASE+suffix;need(identity(files['execution/'+name])==report['text_evidence'][PREFIX+name],'raw identity: '+name)
    need(report['process']==dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None),'process did not finish normally')
    need(json.loads(files['execution/'+CASE+'.process.json'])==report['process'],'process raw/report differ')
    result=report['result'];genuine=report['genuine_30_wins_verified'];lifecycle=report['lifecycle_verified']
    need(lifecycle and not report['failures'],'native lifecycle still incomplete')
    need(result['status']=='PASS_CIRCUS_CONTINUOUS_LIFECYCLE' and result['candidate_sha256']==TARGET['sha256']
         and result['host_write_barriers']==7 and result['input_only_after_guard'] is True
         and result['warnings_errors']==0 and result['owner_bytes_verified']==64 and result['party_bytes_verified']==600
         and result['manual_saves']==1 and result['fresh_cores']==2
         and result['save_counter_after']==result['save_counter_before']+1,'native lifecycle fields')
    need(type(genuine) is bool and genuine==(result['wins']==30 and result['losses']==0
         and result['battles']==30 and result['bp_earned']==90),'genuine goal projection')
    expected='success' if genuine else 'failure'
    need(run['conclusion']==job['conclusion']==expected,'original conclusion differs')
    for flag in ('physical_admission_accepted','suppression_accepted','release_ready'):
        need(report[flag] is False and result[flag] is False,'unearned acceptance: '+flag)
    need(report['matchup_prefix']['exact_event_count']==138
         and report['matchup_prefix']['continuation_prefix_wins']==29,'prefix scope')
    need(visual and len(visual)>=4,'visual review absent')
    reviewed={}
    for name,observation in visual.items():
        screen=files['screens/'+name]
        need(identity(screen)==report['screens'][name] and len(screen)==115215
             and screen.startswith(b'P6\n240 160\n255\n'),'screen identity')
        need(isinstance(observation,str) and observation,'visual observation absent')
        reviewed[name]=dict(identity=identity(screen),observation_ja=observation)
    return dict(schema_version=1,task=TASK,classification='CIRCUS_30_WINS_VISUAL_RECONCILED_SUPPRESSION_OPEN' if genuine else
                'CIRCUS_BATTLE30_SCOPED_LOSS_VISUAL_RECONCILED_30_OPEN',run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,
                tested_head=SOURCE,original_conclusion=expected,archive=ARCHIVE,candidate=TARGET,report_path=REPORT,
                native_source_head=report['native_source_head'],report_identity=identity((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()),
                native_result=result,matchup_prefix=report['matchup_prefix'],genuine_30_wins_verified=genuine,
                lifecycle_verified=True,visual_review=dict(completed=True,screens=reviewed),
                new_emulator_processes=0,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,rom_changes=0,
                physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
                previous_failure_preserved=report['previous_attempt'])


def compact_trace(raw,limit=64):
    """最終戦の実測のみ。状態bit/技/種族を名前や未観測の原因へ推測変換しない。"""
    need(type(limit) is int and 1<=limit<=64,'trace summary bound')
    text=raw.decode('utf-8');events=[];rows=[]
    for line in text.splitlines():
        if line.startswith('CIRCUS_CONTINUOUS '):events.append(json.loads(line.split(' ',1)[1]))
    actions=[e for e in events if e['label']=='action'];need(actions,'no observed battle action')
    start=actions[-1];first=start['frame'];last_frame=first-1
    pattern=re.compile(r'^CIRCUS_RELIABILITY frame=(\d+) streak=(\d+) selected=(\d+) actual=(\d+) blocked=(\d+) accuracy=(\d+) score=(\d+) own=([0-9a-f]+) foe=([0-9a-f]+)$')
    def mon(value):
        b=bytes.fromhex(value);need(len(b)==88,'battle-mon snapshot width')
        u16=lambda at:int.from_bytes(b[at:at+2],'little')
        u32=lambda at:int.from_bytes(b[at:at+4],'little')
        return dict(species_id=u16(0),types=list(b[33:35]),hp=u16(40),max_hp=u16(44),
                    status1_hex=f'{u32(76):08x}',status2_hex=f'{u32(80):08x}',
                    moves=[u16(12+2*i) for i in range(4)],pp=list(b[36:40]),
                    personality=u32(72),ot_id=u32(84))
    for line in text.splitlines():
        if not line.startswith('CIRCUS_RELIABILITY '):continue
        m=pattern.fullmatch(line);need(m,'malformed reliability observation')
        frame,streak,selected,actual,blocked,accuracy,score=map(int,m.groups()[:7])
        if frame<first:continue
        need(frame>last_frame and selected<4 and actual<4,'trace order or slot')
        last_frame=frame
        rows.append(dict(frame=frame,streak=streak,selected=selected,actual=actual,blocked=blocked,
                         accuracy=accuracy,score=score,own=mon(m[8]),foe=mon(m[9])))
    need(rows,'no final-battle observations')
    terminal=[{k:e[k] for k in ('label','frame','battle','outcome','bp','save_counter')}
              for e in events if e['frame']>=first and e['label'] in ('outcome','settled','saved','reloaded')]
    return dict(scope='OBSERVED_FINAL_BATTLE_ONLY_NOT_NEW_NATIVE_ACCEPTANCE',raw_identity=identity(raw),
                battle_number=start['battle']+1,first_action_frame=first,circus_flags_hex=f"{start['flags']:08x}",
                row_count=len(rows),truncated=len(rows)>limit,rows=rows[:limit],terminal=terminal,
                interpretation_ja='実snapshotのID・状態bit・PPを保存。表示名、乱数、freeze等の原因や未観測対面を推測しない。')


def source_inventory():
    """次の未完特性抑制に必要なtracked sourceを小さい抄録で渡す。実行しない。"""
    names=subprocess.check_output(['git','ls-files','scripts','tools','overlays'],cwd=ROOT,text=True).splitlines()
    selected=[n for n in names if any(word in n.lower() for word in ('circus','p05','mega'))
              and Path(n).suffix in ('.c','.h','.py') and 'test' not in Path(n).name]
    selected.sort(key=lambda n:(0 if n.startswith('tools/') else 1 if n.startswith('overlays/') else 2,n))
    inventory=[];budget=0
    pattern=re.compile(r'suppres|abilities|no.?abil|GetBattlerAbility|(?:streak|wins).{0,80}\b30[uU]?\b|LoadBattleCircus',re.I)
    for name in selected:
        raw=(ROOT/name).read_bytes();text=raw.decode();hits=[]
        for number,line in enumerate(text.splitlines(),1):
            if pattern.search(line) and len(line)<600:
                size=len(line.encode())
                if budget+size<=18000 and len(hits)<10:hits.append(dict(line=number,text=line));budget+=size
        if hits:inventory.append(dict(path=name,identity=identity(raw),excerpts=hits))
    findings=json.loads((ROOT/'content/modernization/pr16_p05_supply_owner_findings.json').read_bytes())
    sections={k:v for k,v in findings.items() if 'circus' in k.lower()}
    if len(json.dumps(sections).encode())>=20000:
        sections={k:dict(omitted=True,keys=list(v)[:40] if isinstance(v,dict) else [],reason='section exceeds bounded export') for k,v in sections.items()}
    return dict(scope='READ_ONLY_TRACKED_SOURCE_NOT_NATIVE_ACCEPTANCE',sources=inventory,owner_sections=sections)


def main():
    need(ARTIFACT>0 and re.fullmatch('[0-9a-f]{40}',BASE) and ARCHIVE and VISUAL,'unbound receipt inputs')
    import pr16_circus_battle25 as b
    import pr16_circus_battle30_pp_policy as p
    import pr16_ring_compiled_record as guard
    b.OUT=ROOT/'.local/pr16-circus-battle30-receipt';b.OUT.mkdir(parents=True,exist_ok=True)
    head=b.scope();state=b.resume.validate(ROOT);need(not (ROOT/RECEIPT).exists(),'already reconciled')
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,b.OUT,set(FILES);guard.guard()
    run,job,artifact=b.api('actions/runs/'+str(RUN)),b.api('actions/jobs/'+str(JOB)),b.api('actions/artifacts/'+str(ARTIFACT))
    archive=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    report=b.load(REPORT);value=validate(report,archive,run,job,artifact,VISUAL)
    need(value['report_identity']==identity((ROOT/REPORT).read_bytes()),'report canonical bytes')
    files=members(archive);out,err=files['execution/'+CASE+'.stdout'],files['execution/'+CASE+'.stderr']
    b.probe.SHA=TARGET['sha256'];need(b.probe.validate(out,err,0,CASE)==report['result'],'native raw projection')
    old=(ROOT/'evidence/pr16_circus_reserve_fallback/35478473681/execution'/ (CASE+'.stderr')).read_bytes()
    need(p.prefix_proof(old,err)==report['matchup_prefix'],'matchup raw projection')
    value['final_battle_trace']=compact_trace(err)
    value['next_contract_inventory']=source_inventory()
    config_path='config/modernization_p05_stage77_suppression.json'
    cfg=b.load(config_path)['suppression_contract']['battle_circus_global']
    need(cfg['battle_type_flags_address']=='0x02022AAC' and cfg['battle_type_mask']=='0x04000000'
         and cfg['circus_flags_address']=='0x0203DFBC' and cfg['ability_suppression_mask']=='0x80000000','suppression contract drift')
    native_events=[json.loads(line.split(b' ',1)[1]) for line in err.splitlines() if line.startswith(b'CIRCUS_CONTINUOUS ')]
    actions=[e for e in native_events if e['label']=='action']
    observed=sum(bool(e['types']&0x04000000 and e['flags']&0x80000000) for e in actions)
    need(len(actions)==30 and observed==0,'new suppression observation needs separate review')
    value['next_suppression_contract']=dict(path=config_path,identity=identity((ROOT/config_path).read_bytes()),
        predicate=cfg['predicate'],observed_action_count=30,observed_suppressed_actions=observed,
        status='NOT_YET_NATIVE_ACCEPTED',reason_ja='真正30勝は特性抑制の通し受入ではない。実受付/入場ownerから実際の抑制条件と戦闘挙動までを検証し、flag/streak/party/CPU直接注入で代用しない。')
    for label,args in [('receipt-tests',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_circus_battle30_receipt.py','-v'])]:
        stdout,stderr,proc=b.capture(args,label);need(b.exited(proc)==0 and b'Ran 20 tests' in stderr and b'\nOK\n' in stderr,label+' failed')
    value['receipt_tests']=dict(tests_run=20,success=True,skipped=0)
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['recording_source_head']=head
    checks=b.api('actions/runs?head_sha='+head+'&per_page=100')['workflow_runs']
    value['observed_head_runs']=[{k:r[k] for k in ('id','name','head_sha','status','conclusion')} for r in checks]
    value['session_new_execution_totals']=dict(native_processes=2,fresh_cores=4,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,rom_changes=0,
        run_ids=[35478473681,RUN],scope_ja='この会話で新規実行した29戦目控え補完と30戦目PP同点方策。会話開始時に既に進行中だった35477541574は含めない。')
    value['scope_note_ja']='native受入候補と正式BP親候補を区別。原本結論・旧失敗を保持。表示照合と完了状態の記録のみ、native/ARM再実行0。'
    backlog=b.load(b.resume.BACKLOG);row=next(r for r in backlog['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(row['success_evidence'] is None and not row.get('complete'),'physical gap already altered')
    genuine=value['genuine_30_wins_verified'];r=report['result']
    stop=(f"run{RUN}の原本・29勝/30戦目同点選択prefix・終端画面を照合。実{r['wins']}勝/{r['bp_earned']}BP、元party600/owner64、通常Save/fresh Continueをscoped確定。"
          '旧runの予測不一致failureは保持。完了runのpendingを解消し、記録でnative/ARM再実行なし。')
    nxt=('真正30勝の保存原本を保持し、正規実受付から特性抑制の未完経路を検証する。30勝単独・受入済みBP/Ring/P03/P06/P07・旧ARMは再実行しない。' if genuine else
         f'{REPORT}の最初の実敗北以降だけを修復する。受入prefixを独立再実行しない。')
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action']['id']='CIRCUS_SUPPRESSION_NATIVE' if genuine else 'CIRCUS_BATTLE30_FIRST_LOSS'
    state['next_action']['read_paths']=[RECEIPT,REPORT,'config/modernization_p05_stage77_suppression.json','content/modernization/pr16_saved_reconstruction.json',b.resume.BACKLOG]
    state['circus_battle30_receipt']=dict(path=RECEIPT,run_id=RUN,classification=value['classification'])
    state['pending_runs']=[x for x in state['pending_runs'] if x['run_id']!=RUN]
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='この照合前remote HEAD。native sourceはreceipt.tested_head/native_source_head。正式BP受入HEADは不変。'
    state['observed_head_checks']=dict(scope_head=head,runs=value['observed_head_runs'],
        reason_ja=f'run{RUN}/job{JOB} completed/{value["original_conclusion"]}をAPIと原本で確定。現在HEADの各CI結果はreceiptに分離。全CI greenとは主張しない。')
    state['session_execution_summary']=dict(new_emulator_processes=0,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,
        scope_ja=f'当照合runは実行0。前run{RUN}の1native/2fresh coresと歴史的ARM総数unknownを維持。')
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    row['battle30_receipt']=RECEIPT;row['resume']=nxt
    b.write(RECEIPT,b.stable(value));b.write(b.resume.BACKLOG,b.stable(backlog))
    for name in (*FILES,RECEIPT):state['source_bindings'][name]=identity((ROOT/name).read_bytes())
    if b.resume.BACKLOG in state['source_bindings']:state['source_bindings'][b.resume.BACKLOG]=identity((ROOT/b.resume.BACKLOG).read_bytes())
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    for label,args in [('resume',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v']),
                       ('task-graph',[sys.executable,'scripts/validate_task_graph.py'])]:
        stdout,stderr,proc=b.capture(args,label);need(b.exited(proc)==0,label+' failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Status: DONE（原本照合・scoped受入のみ。特性抑制/P08は未完）\n'
        '- Version: pr16-circus-battle30-receipt-v1\n- Summary: '+stop+'\n'
        '- Files changed: '+', '.join((*FILES,RECEIPT,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*b.LOGS))+'\n'
        '- Verify: 新規receipt契約・native原本validator（emulatorなし）・byte/event prefix・画面identity・固定引継ぎ・task graph・差分private guard/diff check PASS。\n'
        '- Commit: 同branch非force。検証入力HEAD='+head+'。自己SHAはremote/receipt。\n'
        '- Network: GitHub完了run/job/artifact取得のみ。private Release/旧builder/ARM/nativeなし。\n'
        '- Next: '+nxt+'\n')
    for name in b.LOGS:
        path=ROOT/name;need(f'— {TASK}\n' not in path.read_text(),'duplicate receipt log')
        with path.open('a') as stream:stream.write(entry)
    paths=[RECEIPT,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*b.LOGS]
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines());need(changed and changed<=set(paths),'staged scope')
    guard.BASE,guard.ALLOWED=head,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 完了Actions・原本・画面・固定引継ぎ・両ログを確定'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    commit=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty tracked files')
    (b.OUT/'commit-receipt.json').write_bytes(b.stable(dict(task=TASK,commit=commit,source_head=head,non_force_push=True,new_emulator_processes=0)))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


if __name__=='__main__':main()
