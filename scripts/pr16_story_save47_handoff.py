#!/usr/bin/env python3
"""Save47終端とcold画面で残ったNPCを固定再開先へ同期。native/成功試験の再走なし。"""
from __future__ import annotations
import datetime,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save47_record as rec
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=rec.h;a=rec.a
BASE='f72ff781aeca4a4b86237025080baaa943f0998d'
RECORD_SOURCE='cd72e53291d03339df72007ada3c7463b962d10d'
TASK='USER-20261003-SAVE47-COLD-NPC-HANDOFF'
OUT=ROOT/'.local/pr16-story-save47-handoff'
NEXT='content/modernization/pr16_story_save47_next_route.json'
CODE={'scripts/pr16_story_save47_handoff.py','.github/workflows/pr16-story-save47-handoff.yml',NEXT}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'同期1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(state['story_save47']['story_fast_save']==a.OUTPUT,'受入済Save47だけ')
    terminal=rec.inherited.terminal(37138998824,RECORD_SOURCE,111249329799,['success']*11)
    stage=h.d.inputs.api('actions/runs/37138998686');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']==RECORD_SOURCE,'record47source Stage79終端')
    route=h.d.read(ROOT/NEXT);vertices=route['route'];need(len(vertices)==69 and vertices[:4]==[[11,5],[11,4],[12,4],[13,4]]and vertices[-1]==[17,19]and [12,5]not in vertices,'右隣NPC回避の有限候補')
    need(len(set(map(tuple,vertices)))==69 and all(abs(x[0]-y[0])+abs(x[1]-y[1])==1 for x,y in zip(vertices,vertices[1:])),'隣接1tile/重複0')
    prep=h.d.read(ROOT/a.m.PREP);cells={tuple(x['xy']):x for x in prep['allcells']};need(a.m.elevation_path(cells,vertices,3)==[3]*69,'保存地形/衝突0/下段3')
    visual=h.d.read(ROOT/a.VISUAL);need(route['cold_screen_anchor']==visual['screen_anchors']['continue/screen-0001.ppm']and route['input_save']==a.OUTPUT,'cold原画と正式入力の結合')
    state['story_save47']['record_completion']=terminal
    state['story_save47']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    old=state['next_action']['goal_ja'];needle='11,5→12,5→13,5→13,4';need(needle in old,'旧静的候補を明示訂正')
    goal=old.replace(needle,'11,5→11,4→12,4→13,4')+' Save47独立Continue原画でもジュネが右隣12,5に残るため直進しない。新候補69vertexは'+NEXT+'を使用。旧測定と旧GUIDEの提案経路は履歴のまま保持。記録run37138998824/job111249329799全11step成功、新44試験成功済みで再走しない。'
    state['story_save47']['next_goal_ja']=goal;state['story_save47']['next_route']=NEXT
    state['story_save47']['cold_npc_route_correction']=dict(avoid=[12,5],first_steps=vertices[:4],native_processes=0,accepted_test_reruns=0,cold_screen_anchor=route['cold_screen_anchor'])
    state['next_action']['goal_ja']=goal;state['next_action']['read_paths'].insert(0,NEXT);state['bp']['next_step']=goal
    state['do_not_repeat'].append('Save47 cold原画の右隣NPC12,5へ直進しない。次は11,5→11,4→12,4→13,4で北迂回へ合流。69vertexの静的候補であり到達未証明。47測定170/cold13と12+44成功試験は再走0。')
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress',scope='handoff_text_only_no_native')]
    need(h.d.bindings(protected)==protected,'旧受入全sourceと測定原本を保持')
    state['source_bindings'].update(h.d.bindings(CODE));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / Save47終端とcold NPC回避候補の同期
- Version: story-save47-handoff-v1
- Status: DONE（再開候補だけの訂正。到達は未受入）
- Summary: Save47独立Continue原画ではジュネが右隣12,5に残る。旧静的候補の直進を11,4→12,4→13,4へ訂正、69vertexの保存地形/隣接/衝突0/高度3を照合。旧測定/原used0/旧GUIDEは歴史として不変。
- Files changed: 専用同期script/workflow/69vertex候補JSON、固定再開MD/JSON、両ログ。
- Verify: record37138998824/job111249329799全11step成功、Stage79run37138998686成功。新44受入試験/既存12controller/native2の再走0。新native0/ROM0/fixture0。
- Commit: source={os.environ['GITHUB_SHA']}、run={os.environ['GITHUB_RUN_ID']}。scoped guard/全text読戻し後に同branch非force push。
- Network: 同repo Actions終端GETだけ。既存ROM/runtime/input再取得0。一般CI既知不一致/action_requiredを全成功にしない。
- Next: Save47/11,5から訂正候補と新パネル+実cursor判定/親PP[11,10,15,20]だけ。回復未完、merge/release/baseline変更0。
'''
    for path in h.d.LOGS:
        with(ROOT/path).open('a',encoding='utf-8')as f:f.write(entry)
    owned={h.d.STATE,h.d.DOC,*h.d.LOGS};OUT.mkdir();write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')
def snapshot():
    for p in h.d.read(OUT/'owned.json'):need(h.d.git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'全文readback '+p)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+h.d.git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    commands=dict(record=record,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1]in commands,'record|guard|snapshot');commands[sys.argv[1]]()
