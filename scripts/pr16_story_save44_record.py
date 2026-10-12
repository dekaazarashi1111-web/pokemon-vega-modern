#!/usr/bin/env python3
"""504上段西進/trainer114のSave44原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save44_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-NORMAL-RECOVERY-SAVE44'
OUT=ROOT/'.local/pr16-story-save44-record'

CODE={'scripts/pr16_story_save44_accept.py','scripts/pr16_story_save44_record.py','tests/test_pr16_story_save44_accept.py',a.VISUAL,'.github/workflows/pr16-story-save44-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE44_JA.md' and a.CP=='content/modernization/pr16_story_save44_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save44_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37134410241,'19e979ba428a69fc5b3acbee8e004657bb350be8',111235875067,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save44_measure.',16)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==105 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save43全105member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save43/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==60 and len(z.namelist())==61 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save44member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==45 and visual['reviewed_screens']==dict(progress=list(range(43)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save44画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save44画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE44_ORIGINAL=str(original),PR16_SAVE43_INPUT=str(assets/'input.srm'),PR16_SAVE44_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save44_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==32 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 32 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'32成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save43-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save44 artifact11278342404のstory-fast.srm（c7a27be2dbcedecccc139899210415d391ee1946a70894836f80603d7cd86d1b、131088bytes）だけから再開。map3/44・39,12西/上段elevation4・party4/RP0・14264円・badge1・story4071=9/4072=1。バッグの道具/きのみは空。通常ならびかえで既存オノノクスを先頭へ移しHP294/294・PP[15,10,15,20]、ミュウツーは2番目HP314/354・PP[0,0,0,0]のまま。回復済みとは扱わない。費用/道具消費/移動/戦闘0、個体全byte不変。次はこの戦力で通常回復地点へ向かう。保存済み1440地形から39,12→38,12→37,12→37,13を経て西上段、26,10→26,11下り階段→26,12下段を有限候補にする。最初の新戦闘/event/未通過境界で通常Save。主力変更に合わせて既存PPと新実cursorを照合し通常技を選ぶ。未到達南map3/23から3/2へつながる静的候補を今回追加したが回復施設の位置/到達は未受入。Bagキー品わざメモリー/せいたいレーダーをPP回復品と誤認しない。host補充/ROM編集/故意の全滅なし。全45画面・78+cold13入力・16controller32受入試験を無影響再走しない。counter44は37だが部分write、38成功文言/安定Flash→42field。全SaveRTC/cold RAM ledger一致。並替選択13のRAM ledger変化ownerは未解明、全保存legacy flags/vars/PC/S61E不変。Save39旧差・Save40/41/42失敗回収履歴を保持。通常story/正規全国図鑑/自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達未完。全story/一般CI全成功/製品release未完、cleanROM二重生成/BPS固定/merge/release/baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save44_accepted=True,party_reorder_accepted=True,pp_recovery_accepted=False,healing_site_reached=False,normal_recovery_required=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=16,new_acceptance_tests=32,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 通常Bag確認・控え先頭交代・Save44 限定受入

`{result['status']}`。504番道路39,12西の同じ場所で、バッグの道具ポケットが空なのを確認し、既存オノノクスを通常「ならびかえ」で先頭へ。通常Save44と独立Continueを限定受入。PP回復と通常回復地点到達は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全60member/45画面/78+cold13入力。16controller成功原logを継承、新32原本受入/拒否試験だけ。native2/record0/旧受入再走0/ROM変更0。

4は道具が「とじる」だけ、5大切なものはタウンマップ/わざメモリー/せいたいレーダー/わざマシンケース、6はモンスターボール3個。9〜15通常手持ち/ならびかえでオノノクス先頭。全party600byteは100byte個体2体の順番交換だけ。オノノクスHP294/294・PP[15,10,15,20]、ミュウツーHP314/354・PP[0,0,0,0]を保持。費用0・道具消費0・戦闘0・移動0。控えの既存PPと主力のPP回復を混同しない。

16menu→17field、18〜21実menu cursor1→4。24〜37部分write14状態。37はcounter44だが書込み中で最終Flashではない。38〜41成功文言/安定全Flash、42field。cold0/1は39,12西。全45画面を目視。

全Bag/14264円/全legacy flags・vars/PC/S61E/story4071=9/4072=1/badge1不変。42sector checksum/旧Save43bank57344byte/6885byte1708範囲/cold全SaveRTC一致。RAM ledgerは13のならびかえ選択で変化し、保存最終/cold `{a.LEDGER}` 一致。変更ownerの断定はしない。Save39旧cold差owner未解明も保持。

保存済み504地形1440cellは再採取0。南側接続map3/23の静的headerだけを追加読取し、そこから3/2への接続候補を記録。いずれも通常到達/回復受入ではない。

## 次checkpoint送信前の確認

新counterのAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名を大小文字別に照合。新counter ORIGINAL/ROMと親counter INPUTのenv集合、親artifact/run/source/save SHA/counter/bank世代/全member数を原本と照合。送信treeとstaged一覧を明示し、旧正本と交差0を確認。専用宛先/private/source guardを維持。unittestはreturncode/全成功行/正確な終端で判定し、試験名内skipped等へのsubstring判定を禁止。成功試験は記録器だけの失敗で再走しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save43']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37134410176')
    need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='19e979ba428a69fc5b3acbee8e004657bb350be8','Save43記録source Stage79終端')
    state['story_save43']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save44']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,map=[3,44],xy=[39,12],facing=3,rp=0,money=14264,badge_count=1,story_vars={'4071':9,'4072':1},lead_species=850,lead_hp=[294,294],lead_pp=[15,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,party_reorder_accepted=True,cave_crossing_complete=True,west_descent_stairs_accepted=False,hm05_owned=True,hm05_taught_or_used=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='通常Bag確認/オノノクス先頭/Save44を限定受入。PP回復は未完。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504の39,12で通常ならびかえ/Save44測定source。ミュウツーPP0は未回復。オノノクス既存PPで通常回復地点へ進む。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_NORMAL_RECOVERY_TRAVEL_FROM_SAVE44',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save44_accept.py','content/modernization/pr16_story_save44_evidence/inspection.json','content/modernization/pr16_story_save40_preparation.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='道具/きのみ空のため、先頭へ通常交代した控えオノノクスで通常回復地点へ。既存PPを実画面/保存partyから照合し、最初の新戦闘/event/未通過境界で保存。PP補充/故意の全滅なし。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路39,12でBag空/オノノクス先頭交代・Save44独立Continue受入。主力ミュウツーのPP回復は未完。'
    state['do_not_repeat'].append('Save44の78/cold13入力45画面・16controller32受入を無影響再走しない。通常並替だけで費用/道具消費/移動/戦闘0。オノノクスPP[15,10,15,20]、ミュウツーPP0保持。37counter44は部分write、38成功文言/安定Flash→42field。全SaveRTC/最終cold ledger一致。13並替選択のRAM ledger owner未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 通常Bag確認・控え先頭交代・Save44
- Version: story-normal-recovery-preparation-save44-v1
- Status: DONE（通常並替/保存Continueの限定受入。PP回復は未完）
- Summary: 道具/きのみ空、既存オノノクスを通常ならびかえで先頭へ。HP294/294・PP[15,10,15,20]保持。ミュウツーHP314/354・PP0のまま、回復を偽装しない。費用/道具消費/移動/戦闘0。
- Files changed: Save44 controller/16試験/32原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、78/cold13入力/45画面/60member。controller16原log継承、新32受入、record native0。全600byteは100byte個体2体の交換だけ。全Bag/14264円/legacy flags・vars/PC/S61E不変、42checksum/旧bank57344byte/6885byte1708範囲/cold全SaveRTC一致。
- Evidence: 24〜37部分write、37counter44は未完、38成功文言/安定Flash→42field。13並替選択のRAM ledger変更owner未解明、保存最終/cold一致。Save43 record37134410241/Stage79run37134410176終端を反映。旧失敗履歴保持。保存済504地形1440再採取0、南map3/23は静的候補だけ。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知source不一致保持、merge/release/baseline変更0。
- Next: {goal}
'''
    for name in h.d.LOGS:
        with(ROOT/name).open('a',encoding='utf-8')as f:f.write(entry)
    write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')
def snapshot():
    for n in h.d.read(OUT/'owned.json'):need(h.d.git('show','HEAD:'+n)==(ROOT/n).read_bytes(),'全text読戻し '+n)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+h.d.git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1]in actions,'record|guard|snapshot');actions[sys.argv[1]]()

