#!/usr/bin/env python3
"""Read-only rooted grant-owner audit; not a National Dex or evolution fixture."""
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
import pr16_story_fast_maori as m
import pr16_story_fast_maori_record as parent
import pr16_research_story_route_actions as h
from pr16_learnset_compact_record import publish_resume
from tools.t02.rom_inventory import RomImage,ScriptRoot,ScriptWalker,MAP_GROUPS_POINTER_SITE,_decode_map_scripts
SELF='scripts/pr16_national_dex_owner.py'
TEST='tests/test_pr16_national_dex_owner.py'
WF='.github/workflows/pr16-national-dex-owner.yml'
TASK='USER-20260929-NATIONAL-DEX-OWNER'
CP='content/modernization/pr16_national_dex_owner_checkpoint.json'
GUIDE='docs/PR16_NATIONAL_DEX_OWNER_JA.md'
BASE='content/modernization/pr16_national_dex_owner_evidence'
OUT=ROOT/'.local/pr16-national-dex-owner'
PUBLIC=OUT/'public'
CODE={SELF,TEST,WF}
REGIONS=[(0x0806DA20,48,'e4d7ea64a05e5de20afdcd97b3b04afe39ed16c2d9c120d07d0d39492bdda108'),
 (0x0806DA50,56,'415dc6802fecdae1bcf381f7f6402a1dd5f481870662aed1e03aaabc36ca9c60'),
 (0x080CFA20,72,'ef6da906d96281af7aec11d3ffe2c0cd528c05e921086a4bcc7f994eeeefe1b8'),
 (0x080D067C,72,'74333eae1b5ceb97471a3aee31da3fb14d04b402c0ccdcbcae83b510f9dd1fed')]
GOAL='マオリSave16と全国図鑑grant ownerの限定照合は完了。story-fastはartifact11006311891のstory-fast.srm、map3/19(53,10)から通常storyを続ける。全国図鑑のVega側経路はmap3/0のvar0x4072=9→10→map4/3へwarp、同研究所のvar10イベント→special367→var11の保存状態。var9に至る通常進行と有効化後の自然進化は未受入。legacy var0x4055=7経路を序盤で到達済みと扱わず、flag/var注入やgate緩和はしない。元progression戦闘前Axewを保全し、正規解禁後の別境界で成長/進化/Lucky Egg対照/12ケース/Lv100soakへ進む。旧受入入力・44試験・このowner走査の無影響再実行は禁止。'


def check_routes(d):
    m.need(d['town_condition']==[0x4072,9,0x08853824] and
           d['lab_condition']==[0x4072,10,0x088538B0] and
           d['legacy_condition']==[0x4055,7,0x0817C61D],'native rooted conditions, not injected entry')
    m.need(d['special367']==0x0806DA21 and d['special403']==0x0806DA51,'special dispatch ownership')
    m.need(d['town_set']==[0x0885387C,0x4072,10] and d['town_warp']==[0x08853884,4,3] and
           d['town_set'][0]<d['town_warp'][0],'town9 changes10 before the lab warp')
    m.need(d['lab_set']==[0x08853A5D,0x4072,11] and d['lab_grant']==[0x08853A68,367] and
           d['lab_warp']==[0x08853A6B,30,0] and d['lab_set'][0]<d['lab_grant'][0]<d['lab_warp'][0],
           'lab10 advances11, grants Dex, then leaves; no repeat via old condition')
    m.need(d['legacy_grant']==[0x0817C740,367],'legacy grant is separately rooted; no early entitlement')
    m.need(d['graph_diagnostics']==0 and d['visited_nodes']==20,'complete three-root narrow graph only')
    return dict(status='PASS_NATIONAL_DEX_GRANT_OWNER_SCOPED',scope='STATIC_THREE_ROOTS_NOT_GAMEPLAY_UNLOCK',
        routes=d,early_unlock_reachable_accepted=False,var9_natural_arrival_accepted=False,
        dex_enabled_in_save=False,evolution_accepted=False,gate_modified=False,rom_changes=0,
        native_processes=0,fixture_writes=0,full_map_inventory_acceptance_claimed=False,release_ready=False)


def audit(raw):
    m.need(m.identity(raw)==m.CANDIDATE,'exact unchanged story ROM')
    r=RomImage('story-fast',raw);groups=r.u32(MAP_GROUPS_POINTER_SITE)
    maps={}
    for g,n in ((3,0),(4,3)):
        header=r.u32(r.u32(groups+g*4)+n*4)
        roots,refs,rows=_decode_map_scripts(r,r.u32(header+8),f'map:{g}:{n}')
        conditions=[c for row in rows if row['type']==2 for c in row['conditions']]
        maps[g,n]=(header,conditions)
    def condition(g,n,var,value):
        found=[c for c in maps[g,n][1] if c['lhs_var']==var and c['rhs_var_or_value']==value]
        m.need(len(found)==1,'unique rooted condition')
        return [var,value,found[0]['script_address']]
    town=condition(3,0,0x4072,9);lab=condition(4,3,0x4072,10);legacy=condition(4,3,0x4055,7)
    walker=ScriptWalker(r)
    for label,c in [('vega-town9',town),('vega-lab10',lab),('legacy-lab7',legacy)]:walker.add_root(ScriptRoot(c[2],label,'map_script'))
    graph=walker.walk();refs=graph['references']
    def one(label,category,access,value):
        found=[x for x in refs if label in x['roots'] and x['category']==category and x['access']==access and x['value']==value]
        m.need(len(found)==1,'unique real '+label+' '+category)
        x=found[0]
        if category=='var':return [x['instruction_address'],x['value'],x['operand']]
        if category=='map':return [x['instruction_address'],*x['value']]
        return [x['instruction_address'],x['value']]
    d=dict(town_condition=town,lab_condition=lab,legacy_condition=legacy,
        special367=r.u32(0x08163068+367*4),special403=r.u32(0x08163068+403*4),
        town_set=one('vega-town9','var','write',0x4072),town_warp=one('vega-town9','map','warp',[4,3]),
        lab_set=one('vega-lab10','var','write',0x4072),lab_grant=one('vega-lab10','special','call',367),
        lab_warp=one('vega-lab10','map','warp',[30,0]),legacy_grant=one('legacy-lab7','special','call',367),
        graph_diagnostics=len(graph['diagnostics']),visited_nodes=len(graph['nodes']))
    result=check_routes(d);bound=[]
    for address,size,sha in REGIONS:
        binding=m.identity(r.raw(address,size));m.need(binding==dict(size=size,sha256=sha),'unchanged native grant/predicate/gates')
        bound.append(dict(address=address,binding=binding))
    result.update(candidate=m.CANDIDATE,rooted_graph=graph,native_regions=bound,
        owner_abi=dict(special_table=0x08163068,enable_function=0x0806DA21,predicate=0x0806DA51,
            save2_magic_offset=0x1B,national_magic=0xB9,national_var=0x404E,national_value=0x6258,national_flag=0x840))
    return result


def record():
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(not (ROOT/CP).exists(),'accepted owner audit is not replayed')
    old=h.d.read(ROOT/m.CP)
    m.need(old['actions_completion_confirmed'] and old['run_id']==parent.RUN,'completed Maori checkpoint')
    run=h.d.inputs.api('actions/runs/36504857429');jobs=h.d.inputs.api('actions/runs/36504857429/jobs?per_page=100')
    m.need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']=='598c5a7b0fd5202fdee4a8fde519aab268ac3114' and
           jobs['total_count']==len(jobs['jobs'])==1 and jobs['jobs'][0]['conclusion']=='success' and
           all(s['conclusion']=='success' and s['status']=='completed' for s in jobs['jobs'][0]['steps']),'Maori record push/upload/post terminal')
    frozen=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    meta=h.d.inputs.api(f'actions/artifacts/{parent.ARTIFACT}');parent.artifact_meta(meta)
    archive=h.d.inputs.api(f'actions/artifacts/{parent.ARTIFACT}/zip',True)
    m.need(m.identity(archive)==parent.ARCHIVE,'pinned previously accepted artifact')
    with h.safe_zip(archive,60000000) as z:
        raw=z.read('candidate.gba');saved=z.read('story-fast.srm')
    v=audit(raw)
    m.need(m.identity(saved)==m.OUTPUT_SAVE,'unchanged Save16')
    sec=m.sections(saved,0,16);m.need(saved[sec[0]+0x1B]==0,'National Dex remains ungranted in current Save16')
    v['current_save']=dict(identity=m.OUTPUT_SAVE,national_magic=0,bytes_changed=0)
    PUBLIC.mkdir(parents=True)
    tests=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_national_dex_owner.py','-v'],capture_output=True,timeout=60)
    m.need(tests.returncode==0 and not tests.stdout and tests.stderr.count(b' ... ok\n')==14 and b'\nOK\n' in tests.stderr,'14 new owner tests only')
    evidence=ROOT/BASE;evidence.mkdir()
    (evidence/'unit.txt').write_bytes(tests.stderr)
    h.d.write(evidence/'audit.json',v)
    m.need(h.d.bindings(frozen)==frozen,'no accepted source changed')
    checkpoint=dict(schema_version=1,task=TASK,status=v['status'],source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        measurement_complete=True,actions_completion_confirmed=False,source_bindings=h.d.bindings(CODE),
        candidate=m.CANDIDATE,current_save=v['current_save'],native_processes=0,compiles=0,rom_changes=0,
        accepted_case_reruns=0,new_tests=14,maori_record_completed_run=h.d.run_summary(run),
        maori_record_completed_head='3af810957b9d86578c595b11b0a8a67a0276a289',evidence=BASE+'/audit.json',
        national_dex_gameplay_unlock_accepted=False,evolution_accepted=False,release_ready=False,next_goal_ja=GOAL)
    h.d.write(ROOT/CP,checkpoint)
    guide='''# 全国図鑑の正規grant owner — 静的な限定照合

`PASS_NATIONAL_DEX_GRANT_OWNER_SCOPED`。実ROMのmap header→条件table→script CFG→special tableを読み、3本のroot/20nodesにdecode診断0。ROMやSaveを変更せず、ゲームによる全国図鑑解禁や進化成功を受入してはいない。

## Vega側の具体的な経路

map3/0のtype2条件 `var0x4072=9` がroot `0x08853824` を選ぶ。`0x0885387C`で同varを10へ更新し、`0x08853884`からmap4/3へwarp。研究所map4/3のtype2条件 `var0x4072=10` はroot `0x088538B0` を選び、`0x08853A5D`でvar11、`0x08853A68`でspecial367、`0x08853A6B`からmap30/0へ出る。9に至る通常進行はこの照合の外側であり、序盤ですぐ入れるとは推測しない。

special table `0x08163068` の367番は `0x0806DA21`、403番は判定関数 `0x0806DA51`。native有効化ownerはSaveBlock2+0x1Bのmagic0xB9、var0x404E=0x6258、flag0x840を扱う。既存進化guard `0x080CFA20` / `0x080D067C` とgrant/predicateの4範囲を候補hashとともに固定した。閾値やflagのhost書換えは行っていない。

## legacy経路との区別

同じ研究所には `var0x4055=7` → root `0x0817C61D` → special367（`0x0817C740`）の別経路も残る。この条件が早期通常進行で成立する証拠は得ておらず、rootがあることを現在の到達可能性へ昇格しない。VarGetにはCFRU側hookがあるため、単純なSave内offset読取からvar値を断定しない。

探索時にVega425mapの旧root走査でinvalid roots6とdecode診断1が出た。これは今回の3root限定証明とは別の探索結果で、全678map監査や全経路到達証明をPASSとしない。根拠は限定audit.jsonのroot/CFG/参照元であり、ROM全体の生byte検索だけではない。

## 保存原本と次工程

Maori Save16 artifact11006311891のROM06c5e85c…とSave5c4a03b9…を読取専用で再利用し、全国図鑑magic0を確認した。元progression/Save14は不変。追加native/compile/ROM・Save書換え/既受入case再実行0、新規のowner検査14件を実行した。マオリ完了記録run36504857429はpush/upload/postを含めcompleted/success、commit3af810957b9d86578c595b11b0a8a67a0276a289を継承する。

'''+GOAL+'\n\n本workflow自身の終端成功は自己予測せず、push/upload後の外部API照合で確認する。\n'
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    state['national_dex_owner']={k:checkpoint[k] for k in ('status','source_head','run_id','native_processes','new_tests','evolution_accepted')}
    state['national_dex_owner'].update(path=CP,guide=GUIDE)
    state['story_fast_maori'].update(record_actions_completion_confirmed=True,record_completed_head='3af810957b9d86578c595b11b0a8a67a0276a289')
    state['next_action'].update(id='STORY_FAST_TO_NATURAL_DEX_BOUNDARY',goal_ja=GOAL,
        read_paths=[GUIDE,CP,m.GUIDE,m.CP,'docs/PR16_STORY_ACCELERATION_CHECKPOINT_JA.md',
                    'content/modernization/pr16_story_acceleration_checkpoint.json',
                    'docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md'])
    state['bp']['next_step']=GOAL
    owned={CP,GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS,BASE+'/audit.json',BASE+'/unit.txt'}
    for p in (owned|CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}:state['source_bindings'][p]=m.identity((ROOT/p).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    log=f'\n## {stamp}\n- Task: {TASK} / 全国図鑑grant owner固定\n- Version: national-dex-owner-v1\n- Status: DONE（静的3root限定、自然解禁/進化は未受入）\n- Summary: Vega var4072の9→10→研究所→11/special367をheaderから追跡。legacy4055=7と区別。CFRU VarGet hookを無視したsave-offset断定を避け、探索の6invalid/1diagnosticは全体PASSへ改作しない。\n- Files changed: owner検証器/14試験/限定Actions、audit/checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 新14試験PASS、3root20nodes/decode0、特殊処理table/4native範囲/固定ROM/Save16 magic0。追加native/compile/既受入再実行0。Maori record36504857429全step終端成功を別API照合。最終resume/task graph/scoped index後のみcommit。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push/readback。\n- Next: {GOAL}\n'
    for p in h.d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(log)
    h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',checkpoint)


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            data=h.d.git('show','HEAD:'+name);m.need(data==(ROOT/name).read_bytes(),'record text readback');z.writestr(name,data)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))

if __name__=='__main__':
    operations=dict(record=record,guard=guard,snapshot=snapshot)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('record|guard|snapshot')
    operations[sys.argv[1]]()
