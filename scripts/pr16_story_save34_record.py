#!/usr/bin/env python3
"""西側北辺未通過のSave34原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save34_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-CAVE-WEST-FRONTIER-SAVE34'
OUT=ROOT/'.local/pr16-story-save34-record'
PREPARATION_CODE={'scripts/pr16_story_save34_inspect.py','.github/workflows/pr16-story-save34-inspect.yml'}
CODE={'scripts/pr16_story_save34_accept.py','scripts/pr16_story_save34_record.py','tests/test_pr16_story_save34_accept.py',a.VISUAL,'.github/workflows/pr16-story-save34-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE34_JA.md' and a.CP=='content/modernization/pr16_story_save34_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save34_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37123210891,'6910abb080a36796bd570455eb7858828a5d3b51',111203247521,['success']*11)
    preparation_done=inherited.terminal(37123370663,'9b4354510b2f511043075548967ad36e4a506b06',111203707030,['success']*8)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save34_measure.' in v]
    need(len(tests)==14 and any('Ran 14 tests in 'in v for v in log) and any(v.endswith(' OK')for v in log),'変更14controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==46 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save33全46member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save33/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==35 and len(z.namelist())==36 and set(z.namelist())==set(manifest)|{'manifest.json'},'全35member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==20 and visual['reviewed_screens']==dict(progress=list(range(18)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is False,'全20画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全20画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE34_ORIGINAL=str(original),PR16_SAVE33_INPUT=str(assets/'input.srm'),PR16_SAVE34_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save34_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==24 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新24受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save33-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'preparation-terminal.json',preparation_done)
    write(evidence/'controller-test-receipt.json',dict(job=a.JOB,passed_tests=14,test_lines=tests,replayed_tests=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save34 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map1/73・9,7北・party4/RP0・13128円・badge1・story4071=7/4072=1。北辺9,7→9,6は3回通常入力で通過せず、この失敗辺を反復しない。Save34/独立Continueだけ限定受入。'
      'ミュウツーHP322/354・PP[1,14,0,0]、party/Bag/PC/S61E/所持金は不変。れいとうビーム/火炎放射は選ばない。host回復/PP/flag/var注入は禁止。'
      '新map-load原本3node/14命令より、flag4367=1が8,5にmetatile0281/collision0を設定する。実到達は未受入。'
      '次は9,7→9,8→9,9→9,10→8,10の通常戻り転送で27,7へ。そこから26,7→25,7→24,7→23,7→22,7→21,7→20,7→19,7→18,7→18,6→18,5→17,5→16,5→16,4→15,4→14,4→13,4→13,5岩階段→13,6→12,6→11,6→10,6→9,6→8,6→8,5→7,5の候補。'
      'これは最新Save34から新しく開いた8,5/次eventへ向かう必要な通常迂回であり、旧Save再ロードや受入単体の再試験ではない。7,5 coordはvar4071=7でtrainer360を含む6node/var4071=8の保存済原本。'
      '50/cold13入力・20画面・新14controller/24受入試験、既受入Save1〜33を無影響再走しない。保存成功文言の瞬間は未採取。Save34受入は全Flash/sector checksum/field復帰/独立Continueによる。'
      '補助var4021=119/4022=1のruntime ownerは未解決。trainer352/360、洞窟出口4,19→map1/38、全国図鑑、自然成長進化、全storyは未完。既存ROM/runtimeはActions入力だけ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save34_accepted=True,north_edge_traversed=False,dynamic8_5_native_arrival=False,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|PREPARATION_CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=14,new_acceptance_tests=24,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 西側北辺の未通過・Save34 限定受入

`{result['status']}`。Save33の8,10から9,7へ進み、北辺9,7→9,6を3回通常入力したが通過しなかった。そこで通常Save34/独立Continueへ区切った。未通過を保持し、8,5/7,5 eventへ到達したとは主張しない。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全35member、50/cold13入力、20画面。9,7到達6、北向き試行7/8/9は同じ座標。13〜16は部分write4状態、counter34先行16、17で全Flash完成/field復帰。保存成功文言の瞬間は120frame採取間隔の間にあり未採取、表示済みと主張しない。受入根拠は全Flash/sector checksum/通常field復帰と独立Continueの全SaveRTC一致。

戦闘0、party全600byte/HP322/PP[1,14,0,0]、Bag/HM05/13128円/PC/S61E payload不変。legacy flags/story4071=7/4072=1・flag4367=1・badge1保持。補助var4021=115→119/4022=2→1のruntime ownerは未解決。warm ledger hashは観測4で変わるが保存S61E payload/RP0不変、稼得やstory進行に昇格しない。42sector checksum・旧Save33bank57344byte・全SaveRTC cold同一、6996byte/1788範囲差分。

新map-load採取run37123370663/job111203707030全8step成功/native0。保存済920マスは再採取0。type1 root0x08214639のflag4367→call0x0821464Cが8,5へmetatile0281/collision0を設定する3node/14命令の原本を保持。別flag4354の6tileは東側32〜34,16〜17。動的8,5はこのrunで未踏破。新14controllerは原log継承、24新受入だけ実行。旧native/受入試験/ROM変更/compile/fixture0。

上流pret/pokefireredのmetatile_behaviors.hとevent_object_movement.cを比較参照し、behavior0x32はnorth-block、通常elevation不一致は別境界と確認した。ただし現候補実ROMの関数同値性を証明したとはしない。参照URLは両ログに保持。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save33']['record_completion']=prior_done
    state['story_save34_preparation']=dict(run_id=37123370663,job_id=111203707030,artifact_id=11273568224,status='completed',conclusion='success',native_processes=0,new_terrain_cells=0,graph_nodes=3,instructions=14,source_head='9b4354510b2f511043075548967ad36e4a506b06',checkpoint=a.m.PREP)
    state['story_save34']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[1,73],xy=[9,7],facing=2,rp=0,money=13128,badge_count=1,story_vars={'4071':7,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,north_edge_traversed=False,dynamic8_5_native_arrival=False,story_flag4367_accepted=True,cave_crossing_complete=False,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='北辺未通過を保持し、Save34保存と独立Continueを限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='西側9,7/北辺9,6未通過/Save34測定source。8,5/7,5 event/洞窟出口/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_DYNAMIC_WEST_DETOUR_FROM_SAVE34',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save34_measure.py',a.m.PREP,a.m.TERRAIN,'content/modernization/pr16_story_cave_route_checkpoint.json'],stop_rule_ja='Save34の9,7北から通常迂回。9,7→9,6の失敗辺は反復しない。PP[1,14,0,0]、正規UIだけで動的8,5/7,5eventへ。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='西側9,7北で9,6への3試行は未通過。Save34/独立Continue受入。戦闘0/13128円/HP322/PP[1,14,0,0]。戻り転送→西岩階段→動的8,5の迂回候補。'
    state['do_not_repeat'].append('Save34の50/cold13入力・20画面・新14controller/24受入試験を無影響再走しない。北辺9,7→9,6の3回未通過を保持し反復しない。保存文言は未採取。全35member/独立Continueを保持。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|PREPARATION_CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 西側北辺の未通過とSave34
- Version: story-cave-west-frontier-save34-v1
- Status: DONE（北辺未通過を保持。通常保存/Continue限定受入）
- Summary: Save33から9,7へ進み北辺9,6への3試行は未通過。その場で通常Save34/独立Continueへ区切る。戦闘0・party600byte/HP322/PP[1,14,0,0]・Bag/13128円/PC/S61E不変。8,5/7,5 event/洞窟出口は未到達。
- Files changed: 未読map-load採取器、Save34 controller/14変更試験/24受入試験/record workflow、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}全8step成功、50/cold13入力・20画面・全35member。北向き7/8/9は同じ9,7。部分write13〜16/counter34先行16、全Flash完成とfield復帰17。保存成功文言の瞬間は未採取と明記。42checksum/6996byte差分/全SaveRTC不変。補助var4021=115→119/4022=2→1のowner未解決。warm ledger変化4はRP稼得ではない。14controller原本再利用、新24受入/拒否試験だけ実行しstderr保存。record native0/ROM変更0/旧ゲーム再走0。
- Preparation: run37123370663/job111203707030全8step成功/native0。新3node14命令だけ採取、既存920地形再採取0。flag4367のmap-loadが8,5を開く。次は戻り転送で27,7から西岩階段13,5を経由する通常迂回候補。
- History: Save33記録run37123210891全11step終端を反映。旧失敗原本を保持。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushし全text読戻し。
- Network: 同repo GitHub/Actions原本。比較参照 https://raw.githubusercontent.com/pret/pokefirered/master/include/constants/metatile_behaviors.h と https://raw.githubusercontent.com/pret/pokefirered/master/src/event_object_movement.c を読取。behavior0x32とelevation不一致の上流定義を参考とし、候補実ROM同値証明へ昇格しない。既存ROM/runtime/input Save33再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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
