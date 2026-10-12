#!/usr/bin/env python3
"""Save23後の座標teleport ownerを限定照合。native・既受入入力は実行しない。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save23_accept as a
import pr16_story_save23_inspect as pathfinder
import pr16_research_story_route_actions as h
import pr16_story_after_maori_measure as transport
from pr16_story_after_maori import need,identity,unpack,write
from pr16_learnset_compact_record import publish_resume
BASE='46cbf4bc3e2d303c7178377e3882ecc874dba8ed'
TASK='USER-20261003-CAVE-COORD-ROUTE'
CP='content/modernization/pr16_story_cave_route_checkpoint.json'
GUIDE='docs/PR16_STORY_CAVE_ROUTE_JA.md'
CODE={'scripts/pr16_story_cave_route.py','tests/test_pr16_story_cave_route.py','.github/workflows/pr16-story-cave-route.yml'}
OUT=ROOT/'.local/pr16-story-cave-route'
PUBLIC=OUT/'public'


def teleport(raw,address):
    """この洞窟のlock/warpteleport/release/end直線scriptだけを受け付ける。"""
    op0,op1,bank,number,warp,x,y,release,end=unpack(raw,address,'BBBBBHHBB')
    need((op0,op1,release,end)==(0x69,0x3d,0x6d,0x02),'exact straight teleport script')
    need((bank,number,warp)==(1,73,0x99) and 0<=x<40 and 0<=y<23,'direct same-cave destination only')
    return dict(address=address,target_map=[bank,number],warp_id=warp,xy=[x,y],instruction_count=4,
                scope='STATIC_SCRIPT_OWNER_NOT_NATIVE_TELEPORT_ACCEPTANCE')


def coords(raw,header):
    events,=unpack(raw,header+4,'I')
    no,nw,nc,nb=unpack(raw,events,'BBBB')
    need((no,nw,nc,nb)==(10,4,11,4),'fixed cave event geometry')
    table,=unpack(raw,events+12,'I')
    rows=[]
    for i in range(nc):
        q=table+16*i;x,y=unpack(raw,q,'HH');elevation,=unpack(raw,q+4,'B')
        var,value=unpack(raw,q+6,'HH');script,=unpack(raw,q+12,'I')
        need(0<=x<40 and 0<=y<23 and elevation<=15,'bounded coordinate event')
        rows.append(dict(index=i,xy=[x,y],elevation=elevation,trigger_var=var,trigger_value=value,script=script))
    need(rows[10]==dict(index=10,xy=[4,1],elevation=0,trigger_var=0,trigger_value=0,script=0),'nullable reserved entry stays nullable')
    return rows


def inspect(rom,saved,view):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot
    need(identity(rom)==a.measured.plan.CANDIDATE and identity(saved)==a.OUTPUT,'canonical candidate and Save23 only')
    need(view['map']==[1,73] and (view['width'],view['height'])==(40,23),'reuse bounded original cave view')
    rows=coords(rom,view['header'])
    expected=[([19,14],4,0x4000,0,0x08214661),([27,7],4,0x4000,0,0x0821468a),([8,10],4,0x4000,0,0x0821467f)]
    need([(x['xy'],x['elevation'],x['trigger_var'],x['trigger_value'],x['script']) for x in rows[:3]]==expected,
         'three exact coordinate teleports')
    forward=teleport(rom,rows[1]['script']);back=teleport(rom,rows[2]['script'])
    need(forward['xy']==[19,14] and back['xy']==[27,7],'coordinate teleport destinations')
    route=pathfinder.static_path(view,[20,3],[27,7])
    need(route==[[x,3] for x in range(20,28)]+[[27,y] for y in range(4,8)],'11-step static candidate; no accepted prefix replay')
    need([x['index'] for x in rows if x['xy'] in route]==[1],'first route has only target coordinate trigger')
    r=RomImage('save23-cave-coords',rom);walker=ScriptWalker(r)
    for row in rows[:4]:walker.add_root(ScriptRoot(row['script'],'cave_coord_'+str(row['index']),'coord'))
    graph=walker.walk();need(not graph['diagnostics'] and len(graph['nodes'])==5,'complete bounded four-root graph')
    s=a.parent.sectors;table,_=s.bank(saved,0xe000,23,s.LAYOUT);flags,variables=s.legacy_state(saved,table)
    ext=a.parent.s61e_record(saved[table[13]+0x7d0:table[13]+0xde6])
    values={str(flag):(ext[(flag-2304)//8]>>((flag-2304)%8))&1 for flag in (4354,4366,4367,4368,4369)}
    need(values=={'4354':0,'4366':1,'4367':0,'4368':0,'4369':0} and variables[0]==0 and variables[0x71]==6,
         'observed Save23 backing state, no writes')
    return dict(status='PASS_CAVE_COORDINATE_ROUTE_OWNER_STATIC_ONLY',candidate=a.measured.plan.CANDIDATE,input_save=a.OUTPUT,
        coordinate_events=rows,next_trigger=rows[1],next_teleport=forward,reverse_teleport=back,
        static_route=route,static_route_steps=11,graph=graph,saved_var4000=0,saved_var4071=6,saved_expanded_flags=values,
        note_ja='衝突gridだけではwarp/script辺を表現しない。到達不能やROMバグとは判断しない。elevation4/VarGetによる実発火は未観測。',
        native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,save_changes=0,
        next_teleport_native_accepted=False,full_story_accepted=False,release_ready=False,active_baseline_changed=False)


def record():
    os.chdir(ROOT);h.d.current()
    need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/CP).exists(),'new route audit once only')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(state['story_save23']['story_fast_save']==a.OUTPUT and state['story_save23']['artifact_id']==a.ARTIFACT,'only accepted Save23 start')
    source_cp=h.d.read(ROOT/a.CP);need(source_cp['save23_accepted'] is True,'Save23 acceptance recorded')
    PUBLIC.mkdir(parents=True)
    meta,z=transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        rom=z.read('candidate.gba');saved=z.read('story-fast.srm')
        need(identity(rom)==manifest['candidate.gba'] and identity(saved)==manifest['story-fast.srm'],'exact readonly inputs')
    inspection=h.d.read(ROOT/a.EVIDENCE/'inspection.json');view=inspection['maps'][1]
    result=inspect(rom,saved,view)
    done=h.d.inputs.api('actions/runs/37091670533');jobs=h.d.inputs.api('actions/runs/37091670533/jobs?per_page=100')
    need(done['head_sha']=='f74ed8efe29f36952c3f9ec864ca6a8f37a47c82' and done['status']=='completed' and done['conclusion']=='success' and
         jobs['total_count']==len(jobs['jobs'])==1 and jobs['jobs'][0]['id']==111113139437 and len(jobs['jobs'][0]['steps'])==11 and
         all(x['status']=='completed' and x['conclusion']=='success' for x in jobs['jobs'][0]['steps']),'Save23 record push/upload/post terminal confirmed')
    h.d.git('merge-base','--is-ancestor',BASE,'HEAD')
    goal=('Save23 artifact11261539316のstory-fast.srm（SHA256 '+a.OUTPUT['sha256']+'、131088bytes）からだけ再開。'
        'map1/73・20,3東から通常入力で東7歩/南4歩の座標27,7へ進み、正規coord scriptの19,14へのteleportを新規実測する。'
        'elevation4/var4000=0のruntime発火は未受入。道中に野生戦が起きたら通常UIで対処し、host-writeやflag注入は使わない。'
        '到達後は通常Saveと独立Continueで区切る。座標trigger・静的11歩・4root/5nodeは保存済み監査を再利用。'
        'Save23までの45/cold13入力、24受入試験、旧Save1〜22/BP/P08は無影響に再走しない。'
        '27,7/19,14のteleport実到達、洞窟走破、HM05解決、全国図鑑、自然育成/進化、全storyは未完。')
    terminal=dict(run=h.d.run_summary(done),job=jobs['jobs'][0],reflected_head=BASE)
    cp=dict(schema_version=1,task=TASK,status=result['status'],source_head=os.environ['GITHUB_SHA'],
        run_id=int(os.environ['GITHUB_RUN_ID']),result=result,source_bindings=h.d.bindings(CODE),
        inherited_save23_record=terminal,next_goal_ja=goal,release_ready=False,active_baseline_changed=False)
    write(ROOT/CP,cp)
    guide=f'''# Save23後の洞窟座標teleport — 静的owner限定照合

`{result['status']}`。新しいnative入力は0。Save23受入記録run37091670533/job111113139437の全11step成功と反映HEAD `{BASE}` を外部APIで確認。

## 次の縦切り

既存のmap1/73衝突gridを再利用。Save23の20,3から東7歩/南4歩で27,7へ進む静的候補は11歩。通過するcoord eventは終点の1件だけ。実field通行・elevation4・VarGet条件の発火は未受入であり、衝突gridだけで出口への経路が見つからないことをバグとはしない。

map header→coord表の11件を限定読取。coord1=27,7/elevation4/var4000=0、root0x0821468Aのlock→warpteleport map1/73・19,14→release→endを確認。coord2=8,10は27,7へ戻る別root。coord0=19,14はflag4367の分岐を持つ。coord3〜8=11〜16,14・var4071=6にはflag4367/setvar4071=7があり、これは未実行の後続story owner。4root/5nodeにdecode診断0。reserved coord10のscript0はrootにしない。

固定Save23のbacking stateはvar4000=0/4071=6、拡張flag4354=0/4366=1/4367=0/4368=0/4369=0。ROM/Saveを変更せず、実runtimeのgate解禁や次teleport成功へ昇格しない。橋の見た目や全出口到達性の受入でもない。

## 再開と制限

{goal}

source `{os.environ['GITHUB_SHA']}`、run `{os.environ['GITHUB_RUN_ID']}`。本記録のpush/upload/postは外部APIで別途確認する。merge/release/active baseline変更なし。
'''
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    need(h.d.bindings(protected)==protected,'accepted sources unchanged')
    state['story_save23']['record_completion']=terminal
    state['story_cave_route']=dict(status=result['status'],checkpoint=CP,guide=GUIDE,run_id=int(os.environ['GITHUB_RUN_ID']),
        from_save=23,static_steps=11,target_coord=[27,7],expected_teleport_xy=[19,14],native_accepted=False)
    state['next_action'].update(id='STORY_CAVE_COORD27_FROM_SAVE23',goal_ja=goal,
        read_paths=[GUIDE,CP,a.GUIDE,a.CP,'scripts/pr16_story_cave_route.py','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],
        stop_rule_ja='Save23から先の未観測coord teleportだけ。静的監査/旧入力を再走しない。所持HM05を習得済みとしない。全国図鑑/bridge/story flagのhost注入は禁止。')
    state['bp']['next_step']=goal
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['do_not_repeat'].append('Save23後の座標teleport静的owner4root/5node・11歩候補はpr16_story_cave_route_checkpoint.jsonから再利用。native到達へ昇格しない。')
    owned={CP,GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}
    state['source_bindings'].update(h.d.bindings(CODE|{CP,GUIDE}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / Save23後の正規座標teleport ownerと次の11歩
- Version: story-cave-coordinate-route-v1
- Status: DONE（静的owner限定。次teleportのnative未実測）
- Summary: map1/73 coord表と27,7→19,14の正規warpteleportを4root/5node・診断0で照合。衝突gridだけの無経路をバグと誤認せず、Save23から11歩の候補を固定。reserved script0と後続flag4367/var4071 ownerを区別。
- Files changed: 限定採取/record器、新9拒否試験、専用workflow、checkpoint/guide、固定再開MD/JSON、両ログ。
- Verify: 固定candidate/Save23 hash、Save23記録run37091670533の全11step終端、原本backing flags/vars、静的graph/11歩。新9試験、scoped final index/resume/task graph/diff確認後commit。native0/旧case再走0/ROM・Save変更0/compile0。
- Commit: source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}、同branch非force push、全text読戻し。
- Network: GitHub connector/既存Actions原本のみ。一般CI全成功は主張せず、merge/release/active baseline変更なし。
- Next: {goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned));write(PUBLIC/'receipt.json',cp)


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            raw=h.d.git('show','HEAD:'+name);need(raw==(ROOT/name).read_bytes(),'all text readback');z.writestr(name,raw)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot)
    need(len(sys.argv)==2 and sys.argv[1] in actions,'record|guard|snapshot');actions[sys.argv[1]]()
