#!/usr/bin/env python3
"""Repair only Floette's one-frame-old cursor capture; preserve three good images."""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_gameplay as m
import pr16_learnset_visual as visual
from pr16_learnset_egg_gameplay import once,strict_pairs
BASE=m.BASE
WORK=ROOT/'.local/pr16-learnset-visual-list'
PROOF=WORK/'proof'
CP=BASE+'pr16_learnset_visual_list_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_VISUAL_LIST_JA.md'
EVIDENCE=BASE+'pr16_learnset_visual_list_evidence'
CODE={'scripts/pr16_learnset_visual_list.py','tests/test_pr16_learnset_visual_list.py','.github/workflows/pr16-learnset-visual-list.yml'}
PARENT={'run_id':35839299224,'source_head':'29f1d8ca2b4f8468471265418a6e42430a660616','reflected_head':'9fcdc3c68682a22d6e521169c7fe7c323c638cc7','artifact':{'id':10741160378,'name':'pr16-learnset-visual-proof','size_in_bytes':53866,'digest':'sha256:af74072b3e30a6462138e09d78dbbe63e6625638a177aae94256ec0359755a3b'}}
ARCHIVE={'size':21781,'sha256':'773e015190fdd0f0d3f296d90ebc69e84d5e3d5c8b58f6e1d1e29d23e6677017'}
DRIVER={'size':4200,'sha256':'d176cdb0d1a2798715b7d1fc78ce0beb5fcf6adb4ff16806fce59c8daa946009'}
SCOPE='ISSUE19_FLOETTE_LIST_CURSOR_SETTLE_ONLY'
SCREEN='screens/floette-replace-420-list.ppm'
need=m.need
identity=m.identity
load=m.load
write=m.write


def archive(raw):
    need(identity(raw)==ARCHIVE,'list archive preimage')
    text=once(raw.decode(),'static unsigned v_list_frame,v_summary_frame,v_summary_ready;','static unsigned v_list_frame,v_summary_frame,v_summary_ready,v_list_ready;')
    old='''        if((state==4 || state==6) && t.list && stamp-t.list>=90U
            && read8(c,p+0x9eb)==index && !v_list_shot)v_capture(c,"list");'''
    new='''        if((state==4 || state==6) && t.list && read8(c,p+0x9eb)==index) {
            if(++v_list_ready==90U) {
                v_capture(c,"list");c->setKeys(c,0);return t;
            }
        }else v_list_ready=0;'''
    return once(text,old,new)


def driver(raw):
    need(identity(raw)==DRIVER,'list driver preimage')
    text=once(raw.decode(),'if(id!=0U && id!=11U)return 2;','if(id!=11U)return 2;')
    text=once(text,'t.bag && t.mode_menu && t.mode_choice && t.party && t.list && t.summary\n        && !t.selection && !t.replaced && !t.learned && v_list_shot && v_summary_shot',
                    't.bag && t.mode_menu && t.mode_choice && t.party && t.list && !t.summary\n        && !t.selection && !t.replaced && !t.learned && v_list_shot && !v_summary_shot && v_list_ready==90U')
    start=text.index('    printf("{\\"status\\":\\"PASS_CAPTURE')
    text=text[:start]+'''    printf("{\\"status\\":\\"PASS_LIST_CAPTURE\\",\\"scope\\":\\"ISSUE19_FLOETTE_LIST_CURSOR_SETTLE_ONLY\\",\\"case\\":\\"floette-replace-420\\",\\"candidate_sha256\\":\\"%s\\",",rom_hash);
    printf("\\"species\\":1029,\\"page\\":0,\\"index\\":10,\\"candidate_count\\":12,\\"selected_move\\":420,\\"list_ready_frames\\":%u,\\"list_frame\\":%u,",v_list_ready,v_list_frame);
    printf("\\"cores\\":1,\\"host_write_barriers\\":1,\\"saves\\":0,\\"learned\\":false,\\"summary_entered\\":false,\\"initial_moves_pp_unchanged\\":true,\\"visual_reviewed\\":false,\\"issue19_complete\\":false,\\"release_ready\\":false,\\"warnings_errors\\":0}\\n");
    return 0;
}
'''
    return text


def validate(raw):
    value=json.loads(raw,object_pairs_hook=strict_pairs)
    expected={'status':'PASS_LIST_CAPTURE','scope':SCOPE,'case':'floette-replace-420','candidate_sha256':m.CANDIDATE['sha256'],
              'species':1029,'page':0,'index':10,'candidate_count':12,'selected_move':420,'list_ready_frames':90,
              'cores':1,'host_write_barriers':1,'saves':0,'learned':False,'summary_entered':False,'initial_moves_pp_unchanged':True,
              'visual_reviewed':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0}
    need(set(value)==set(expected)|{'list_frame'},'list schema')
    for k,v in expected.items():need(type(value[k]) is type(v) and value[k]==v,'list scope '+k)
    need(type(value['list_frame']) is int and 1<=value['list_frame']<200000,'list frame')
    return value


def execute():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    import pr16_learnset_battle as b
    head=current();need(not WORK.exists() and not (ROOT/CP).exists(),'no replay of accepted capture')
    PROOF.mkdir(parents=True);(PROOF/'screens').mkdir();old=m.PROOF;m.PROOF=PROOF
    protected=(*m.PROTECTED,m.CP,b.CP,BASE+'pr16_learnset_egg_gameplay_checkpoint.json',visual.CP)
    v={'schema_version':1,'status':'RUNNING','run_id':int(os.environ['GITHUB_RUN_ID']),'source_head':head,'candidate':m.CANDIDATE,'scope':SCOPE,
       'parent':PARENT,'native_processes':0,'new_unit_tests':0,'other_image_reruns':0,'accepted_unit_reruns':0,'arm_compiles':0,'rom_changes':0,
       'bag_suite_reruns':0,'battle_reruns':0,'egg_reruns':0,'wiki_generations':0,'issue19_complete':False,'release_ready':False,'visual_reviewed':False,
       'rejected_original_screen':{'path':SCREEN,'sha256':'c17e2cca6a19c9db1121477ba30c474dfa4ed615b94bbdf90220026c235254fd','reason_ja':'internal index10到達直後の旧画像は、描画カーソルが前行のめいそうに残る。summaryのあやしいかぜは正常。原本を保持し一覧1枚だけ再撮影。'},
       'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|{'scripts/pr16_learnset_visual.py',visual.SOURCE}},
       'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in protected}}
    try:
        m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_visual_list','-v'],'unit');v['new_unit_tests']=8
        a=PARENT['artifact'];run=fetch('actions/runs/'+str(PARENT['run_id']));meta=fetch('actions/artifacts/'+str(a['id']))
        need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==PARENT['source_head'],'original capture unfinished')
        need(all(meta[k]==val for k,val in a.items()) and not meta['expired'] and meta['workflow_run']['id']==PARENT['run_id'],'original artifact metadata')
        raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True);need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'original ZIP identity')
        data=b.zip_members(raw);oldcp=load(ROOT/visual.CP)
        need(data['reflected-head.txt'].decode().strip()==PARENT['reflected_head'] and oldcp['source_head']==PARENT['source_head'],'original capture ref')
        for n,binding in oldcp['proof_bindings'].items():need(identity(data[n])==binding,'original capture member '+n)
        need(identity(data[SCREEN])['sha256']==v['rejected_original_screen']['sha256'],'rejected original screenshot binding')
        for n,raw in data.items():
            if n.startswith('executed-') and n.endswith(('.c','.h')) and n!='executed-capture.c':
                name=n.removeprefix('executed-');need(Path(name).name==name,'generated source path')
                if name=='pr16_gameplay_archive.c':raw=archive(raw).encode()
                (WORK/name).write_bytes(raw)
        source=driver(data['executed-capture.c']);(WORK/'capture.c').write_text(source)
        (PROOF/'executed-capture.c').write_text(source);(PROOF/'executed-pr16_gameplay_archive.c').write_bytes((WORK/'pr16_gameplay_archive.c').read_bytes())
        v['compiled_source_bindings']=oldcp['compiled_source_bindings']
        need(all(identity((ROOT/p).read_bytes())==binding for p,binding in v['compiled_source_bindings'].items()),'inherited compile input')
        b.WORK=WORK/'restore-root';b.WORK.mkdir();b.restore()
        exe=WORK/'runner';_,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),str(WORK/'capture.c'),'-lmgba','-o',str(exe)],'compile');need(not err,'list compiler warning')
        seed=(ROOT/m.SEED).read_bytes();need(identity(seed)==m.SEED_ID,'list seed');fixture=WORK/'list.srm';fixture.write_bytes(seed)
        v['native_processes']=1
        raw,err=m.run([str(exe),str(b.WORK/'candidate.gba'),str(fixture),m.CANDIDATE['sha256'],m.SEED_ID['sha256'],'11',str(PROOF/'screens'/'floette-replace-420')],'list',240)
        need(b'mGBA[' not in err,'list emulator warning');v['result']=validate(raw);v['screen']=visual.image((PROOF/SCREEN).read_bytes())
        need(v['protected_bindings']=={p:identity((ROOT/p).read_bytes()) for p in protected} and identity((b.WORK/'candidate.gba').read_bytes())==m.CANDIDATE and (ROOT/m.SEED).read_bytes()==seed,'accepted input changed')
        v['status']='PASS_CAPTURE_PENDING_VISUAL_REVIEW'
    except Exception as exc:v.update(status='FAIL',error_type=type(exc).__name__,error=str(exc).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={p.relative_to(PROOF).as_posix():identity(p.read_bytes()) for p in PROOF.rglob('*') if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=old


def owned():return CODE|{CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in (ROOT/EVIDENCE).rglob('*') if p.is_file()}


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'list source head')
    dst=ROOT/EVIDENCE/str(v['run_id']);need(not dst.exists(),'duplicate list text');dst.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_bytes().decode();need('\0' not in text,'binary tracked');text=redact_user_paths(text)
        text='\n'.join(x.rstrip() for x in text.splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(text),'private path');(dst/p.name).write_text(text)
    v.update(public_evidence_path=dst.relative_to(ROOT).as_posix(),public_evidence_bindings={p.name:identity(p.read_bytes()) for p in dst.iterdir()},actions_completion_confirmed=False);write(ROOT/CP,v)
    (ROOT/GUIDE).write_text(f'# フラエッテ一覧1枚の限定修復\n\nrun{v["run_id"]} / source `{v["source_head"]}` / `{v["status"]}`。\n\n旧run35839299224はcapture/記録/push成功だが、フラエッテ一覧の実描画カーソルだけ前行の「めいそう」に残っていた。正常なミュウ一覧・summaryとフラエッテsummaryの3枚は保持する。旧画像も証拠として改作しない。\n\n一覧開始からの待機ではなく、内部index10が連続90frame安定した後に撮影する。通常キー入力だけ、一覧撮影で停止し、summary/習得/Saveは実行しない。1process/1core、8追加境界試験。画像はartifact、trackedはtext/hashのみ。\n\n正本 `{CP}`。目視とActions終端は後続の記録限定照合で確定。\n')
    state=load(ROOT/m.STATE);state['learnset_visual_list']={k:v[k] for k in ('status','run_id','source_head','native_processes','visual_reviewed','actions_completion_confirmed')};state['learnset_visual_list']['path']=CP
    state['observed_head']=v['source_head'];state['observed_head_semantics']='フラエッテ一覧1枚のcursor描画待ち限定修復source。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'in_progress','conclusion':None}],'reason_ja':'旧capture successと1枚の目視不合格を区別。修復画像の目視/終端は後続で確認。'}
    state['bp']['current_stop']='タマゴ8ケースPASS。代表4枚中3枚は目視正常、フラエッテ一覧1枚を限定再撮影: '+v['status']+'。'
    goal='修復一覧1枚を目視し、正常な旧3枚と合わせて4枚を受入。タマゴ/撮影/修復のActions終端を記録限定で照合。成功したnative/画像/受入unitは再実行しない。'
    state['bp']['next_step']=goal;state['next_action']=dict(state['next_action'],id='LEARNSET_VISUAL_LIST_REVIEW',goal_ja=goal,read_paths=[GUIDE,CP,visual.GUIDE,visual.CP])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20260923-LEARNSET-VISUAL-LIST\n- Version: issue19-list-settle-v1\n- Status: {v["status"]}\n- Summary: 目視で発見した一覧cursorの1frame遅延を修復。index10連続90frameで1枚だけ再撮影しsummary前に停止。正常3枚/旧不合格画像の原本は保持。\n- Files changed: 限定controller/8境界試験/Actions、checkpoint/text原本・guide・固定引継ぎMD/JSON・両ログ。\n- Verify: run{v["run_id"]}、新規native {v["native_processes"]}、unit {v["new_unit_tests"]}。習得/Save/受入Bag全体/戦闘/タマゴ/ARM/Wiki再実行0。\n- Commit: 同branchへ非force push、reflected-headをremote照合。\n- Network: 固定capture artifactと保存候補のみ。全履歴guard/release成功は主張しない。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(log)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned()-CODE;g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths');actions[sys.argv[1]]()
