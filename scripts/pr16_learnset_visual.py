#!/usr/bin/env python3
"""Retake only missing list/summary frames. Never learn, save or run Bag23."""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_gameplay as m
from pr16_learnset_egg_gameplay import once,strict_pairs
BASE=m.BASE
WORK=ROOT/'.local/pr16-learnset-visual'
PROOF=WORK/'proof'
CP=BASE+'pr16_learnset_visual_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_VISUAL_JA.md'
EVIDENCE=BASE+'pr16_learnset_visual_evidence'
CODE={'scripts/pr16_learnset_visual.py','tests/test_pr16_learnset_visual.py','.github/workflows/pr16-learnset-visual.yml'}
IDS=(0,11)
NAMES=('machine-page4-replace','floette-replace-420')
SOURCE='tools/mgba_pr16_learnset_gameplay.c'
SOURCE_ID={'size':6934,'sha256':'4d6050d21c6ab970b28c38643f1e0f5313c9a1f0aba03a91c9865411d08cca68'}
ARCHIVE_ID={'size':20788,'sha256':'8f7cdf0e3897c6d1dbf6b80eb7936687c4d080a35ab896bb8db871c623e6d383'}
SCOPE='ISSUE19_TWO_REPRESENTATIVE_LIST_SUMMARY_CAPTURES_ONLY'
need=m.need
identity=m.identity
write=m.write
load=m.load


def archive(raw):
    need(identity(raw)==ARCHIVE_ID,'accepted generated archive preimage')
    text=raw.decode()
    declaration='static bool v_list_shot,v_summary_shot;\nstatic unsigned v_list_frame,v_summary_frame,v_summary_ready;\nstatic void v_capture(struct mCore*,const char*);\n'
    text=once(text,'struct ATrace {',declaration+'struct ATrace {')
    anchor='        unsigned key=0;\n        if(f%30==0) {'
    capture='''        /* State 4 is an interactive list on this candidate, not state 6 only.
         * Read-only capture waits for rendering; no palette or VRAM writes. */
        if((state==4 || state==6) && t.list && stamp-t.list>=90U
            && read8(c,p+0x9eb)==index && !v_list_shot)v_capture(c,"list");
        if(cb==P03F_SUMMARY_CB) {
            unsigned q=read32(c,QOL_SUMMARY_DATA_SLOT);
            if(p02s_ewram_pointer(q) && q+P03F_SUMMARY_STATE<0x02040000
                && p03f_task(c,P03F_SUMMARY_TASK) && read8(c,q+P03F_SUMMARY_STATE)==2U) {
                if(++v_summary_ready==90U) {
                    a_require(v_list_shot,"summary without list evidence");
                    v_capture(c,"summary");c->setKeys(c,0);return t;
                }
            }else v_summary_ready=0;
        }
'''
    text=once(text,anchor,capture+anchor)
    text=once(text,'else{a_require(cursor==index,"wrong candidate selection");key=QOL_KEY_A;list_selected=true;}',
        'else if(v_list_shot){a_require(cursor==index,"wrong candidate selection");key=QOL_KEY_A;list_selected=true;}')
    text=once(text,'==2 && !summary_selected) {','==2 && !summary_selected && v_summary_shot) {')
    return text


def driver(raw):
    need(identity(raw)==SOURCE_ID,'accepted driver preimage')
    text=raw.decode();prefix='/* Capture-only projection: one host-write barrier, no teaching or Save. */\n'+text[text.index('#include'):text.index('static const char *g_prefix;')]
    shot=text[text.index('static void g_shot('):text.index('static void g_frame(')]
    main=text[text.index('int main(int argc,char **argv) {'):text.index('    g_shot("fixture");')]
    main=once(main,'if(id>=sizeof(G_CASES)/sizeof(*G_CASES))return 2;','if(id!=0U && id!=11U)return 2;')
    result='''
    unsigned before=read32(c,P03_SAVE_COUNTER);
    struct mCore saved=*c;a_guard(c);
    struct ATrace t=a_scene(c,v->family,v->page,v->index,(int)v->slot,v->action,v->count,v->candidates);
    a_require(t.bag && t.mode_menu && t.mode_choice && t.party && t.list && t.summary
        && !t.selection && !t.replaced && !t.learned && v_list_shot && v_summary_shot,
        "capture must stop before replacement/learning");
    a_require(read32(c,P03_SAVE_COUNTER)==before,"capture unexpectedly saved");
    a_restore(c,&saved);a_slots(c,v->species,v->level,v->known,v->pp);
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],hash);
    a_require(!strcmp(hash,rom_hash) && log_problem_count==0,"capture ROM/warnings");
    printf("{\\"status\\":\\"PASS_CAPTURE\\",\\"scope\\":\\"ISSUE19_TWO_REPRESENTATIVE_LIST_SUMMARY_CAPTURES_ONLY\\",\\"case\\":\\"%s\\",\\"candidate_sha256\\":\\"%s\\",",v->name,rom_hash);
    printf("\\"species\\":%u,\\"page\\":%u,\\"index\\":%u,\\"candidate_count\\":%u,\\"selected_move\\":%u,",v->species,v->page,v->index,v->count,v->expected);
    printf("\\"list_frame\\":%u,\\"summary_frame\\":%u,\\"summary_ready_frames\\":%u,",v_list_frame,v_summary_frame,v_summary_ready);
    printf("\\"host_write_barriers\\":1,\\"cores\\":1,\\"saves\\":0,\\"learned\\":false,\\"initial_moves_pp_unchanged\\":true,\\"visual_reviewed\\":false,\\"issue19_complete\\":false,\\"release_ready\\":false,\\"warnings_errors\\":0}\\n");
    return 0;
}
'''
    capture='''static void v_capture(struct mCore*c,const char *label) {
    g_shot(label);
    if(!strcmp(label,"list")){v_list_shot=true;v_list_frame=c->frameCounter(c);}
    else {v_summary_shot=true;v_summary_frame=c->frameCounter(c);}
}
'''
    return prefix+'static const char *g_prefix;\nstatic color_t *g_video;\n'+shot+capture+main+result


def image(raw):
    header=b'P6\n240 160\n255\n';need(raw.startswith(header) and len(raw)==len(header)+240*160*3,'PPM shape')
    pixels=raw[len(header):];colors=set(zip(pixels[::3],pixels[1::3],pixels[2::3]))
    need(16<=len(colors)<=32768,'blank/invalid capture palette')
    bright=sum(max(pixels[i:i+3])>=64 for i in range(0,len(pixels),3))
    need(bright>=240*160//10,'black transition capture')
    return dict(identity(raw),width=240,height=160,distinct_colors=len(colors),bright_pixels=bright)


def validate(raw,case):
    r=json.loads(raw,object_pairs_hook=strict_pairs)
    expected={'status':'PASS_CAPTURE','scope':SCOPE,'case':case['name'],'candidate_sha256':m.CANDIDATE['sha256'],
      'species':case['species'],'page':case['page'],'index':case['index'],'candidate_count':case['count'],
      'selected_move':case['expected'],'summary_ready_frames':90,'host_write_barriers':1,'cores':1,'saves':0,
      'learned':False,'initial_moves_pp_unchanged':True,'visual_reviewed':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0}
    need(set(r)==set(expected)|{'list_frame','summary_frame'},'capture result schema')
    for k,v in expected.items():need(type(r[k]) is type(v) and r[k]==v,'capture scope '+k)
    need(type(r['list_frame']) is int and type(r['summary_frame']) is int and 1<=r['list_frame']<r['summary_frame']<200000,'capture chronology')
    return r


def execute():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    import pr16_learnset_battle as b
    head=current();need(not WORK.exists() and not (ROOT/CP).exists(),'no capture wholesale replay')
    PROOF.mkdir(parents=True);(PROOF/'screens').mkdir();old=m.PROOF;m.PROOF=PROOF
    protected=(*m.PROTECTED,m.CP,b.CP,BASE+'pr16_learnset_egg_gameplay_checkpoint.json')
    v={'schema_version':1,'status':'RUNNING','run_id':int(os.environ['GITHUB_RUN_ID']),'source_head':head,'scope':SCOPE,
       'candidate':m.CANDIDATE,'captures':[],'native_processes':0,'new_unit_tests':0,'arm_compiles':0,'rom_changes':0,
       'full_bag_reruns':0,'battle_reruns':0,'egg_reruns':0,'wiki_generations':0,'issue19_complete':False,'release_ready':False,'visual_reviewed':False,
       'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|{SOURCE}},
       'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in protected}}
    try:
        m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_visual','-v'],'unit');v['new_unit_tests']=10
        cp=load(ROOT/m.CP);need(cp['actions_completion_confirmed'] is True,'Bag completion missing');a=cp['artifact']
        meta=fetch('actions/artifacts/'+str(a['id']));need(all(meta[k]==val for k,val in a.items()) and not meta['expired'] and meta['workflow_run']['head_sha']==cp['source_head'],'Bag artifact')
        raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True)
        need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'Bag ZIP identity')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            need(len(z.namelist())==len(set(z.namelist()))<250 and sum(x.file_size for x in z.infolist())<32000000,'Bag ZIP bounds')
            for name,ident in cp['proof_bindings'].items():need(identity(z.read(name))==ident,'Bag member '+name)
            vectors=json.loads(z.read('vectors.json'))['cases']
            for name,ident in cp['generated_sources'].items():
                raw=z.read('executed-'+name);need(identity(raw)==ident,'accepted generated source')
                if name=='pr16_gameplay_archive.c':raw=archive(raw).encode()
                (WORK/name).write_bytes(raw);(PROOF/('executed-'+name)).write_bytes(raw)
        need([vectors[i]['name'] for i in IDS]==list(NAMES),'representative identity')
        (WORK/'capture.c').write_text(driver((ROOT/SOURCE).read_bytes()));(PROOF/'executed-capture.c').write_bytes((WORK/'capture.c').read_bytes())
        b.WORK=WORK/'restore-root';b.WORK.mkdir();rom=b.restore();need(identity(rom)==m.CANDIDATE,'candidate restoration')
        v['compiled_source_bindings']=cp['compiled_sources']
        need(all(identity((ROOT/p).read_bytes())==binding for p,binding in v['compiled_source_bindings'].items()),'accepted include/header changed')
        exe=WORK/'runner'
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),str(WORK/'capture.c'),'-lmgba','-o',str(exe)],'compile');need(not err,'capture compiler warnings')
        seed=(ROOT/m.SEED).read_bytes();need(identity(seed)==m.SEED_ID,'capture seed')
        for i in IDS:
            case=vectors[i];name=case['name'];fixture=WORK/(name+'.srm');fixture.write_bytes(seed);v['native_processes']+=1
            raw,err=m.run([str(exe),str(b.WORK/'candidate.gba'),str(fixture),m.CANDIDATE['sha256'],m.SEED_ID['sha256'],str(i),str(PROOF/'screens'/name)],name,240)
            need(b'mGBA[' not in err,'capture warning')
            result=validate(raw,case);result['screens']={kind:image((PROOF/'screens'/(name+'-'+kind+'.ppm')).read_bytes()) for kind in ('list','summary')}
            v['captures'].append(result);write(PROOF/'verification.json',v)
        need(v['protected_bindings']=={p:identity((ROOT/p).read_bytes()) for p in protected} and identity((b.WORK/'candidate.gba').read_bytes())==m.CANDIDATE and (ROOT/m.SEED).read_bytes()==seed,'accepted/ROM/seed mutation')
        v['status']='PASS_CAPTURE_PENDING_VISUAL_REVIEW'
    except Exception as e:v.update(status='FAIL',error_type=type(e).__name__,error=str(e).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={p.relative_to(PROOF).as_posix():identity(p.read_bytes()) for p in PROOF.rglob('*') if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=old


def owned():return CODE|{CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in (ROOT/EVIDENCE).rglob('*') if p.is_file()}


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'capture source head')
    dst=ROOT/EVIDENCE/str(v['run_id']);need(not dst.exists(),'duplicate capture text');dst.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_bytes().decode();need('\0' not in text,'no tracked binary');text=redact_user_paths(text)
        text='\n'.join(s.rstrip() for s in text.splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(text),'no private path');(dst/p.name).write_text(text)
    v.update(public_evidence_path=dst.relative_to(ROOT).as_posix(),public_evidence_bindings={p.name:identity(p.read_bytes()) for p in dst.iterdir()},actions_completion_confirmed=False)
    write(ROOT/CP,v)
    (ROOT/GUIDE).write_text(f'# Issue19: 一覧・summary撮影の限定修復\n\n候補6e88a021、run{v["run_id"]}、source `{v["source_head"]}`、`{v["status"]}`。\n\n既受入23ケース全体は再実行しない。Mew raw40-page4とFloette420の2対象のみ、通常Bag入口から一覧/summaryを表示し、習得選択・Save前に停止する。1対象1core/観測guard1。既存技/PP・Save counter不変。\n\n一覧state4/6を両方認識し、表示開始から90frame待機後に選択行を撮影。summaryはTask/状態2の連続90frame後に撮影する。palette/VRAMを直接書き換えない。画像はartifact内のみ、trackedはhash・240x160・色数・明度・実行source/stdout/stderr。\n\n新規unit {v["new_unit_tests"]}、native {v["native_processes"]}。pixel検査と目視受入を区別する。`visual_reviewed=false` の間は実画像4枚の目視とActions終端を後続で照合する。正本 `{CP}`。Issue19/releaseは未完。\n')
    state=load(ROOT/m.STATE);state['learnset_visual']={k:v[k] for k in ('status','run_id','source_head','native_processes','visual_reviewed','actions_completion_confirmed')};state['learnset_visual']['path']=CP
    state['observed_head']=v['source_head'];state['observed_head_semantics']='代表2対象の撮影限定source。全Bagの再実行/習得/Saveは行わない。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'in_progress','conclusion':None}],'reason_ja':'artifact画像とActions終端の後続確認が必要。'}
    state['bp']['current_stop']='Issue19: Bag23/通常戦闘/タマゴの原本を保持。代表画像は'+v['status']+'。'
    goal='画像checkpointの実画像4枚を目視し、撮影・タマゴの最新Actions終端を記録限定で照合。成功したnativeを再実行しない。'
    state['bp']['next_step']=goal;state['next_action']=dict(state['next_action'],id='LEARNSET_VISUAL_REVIEW',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_LEARNSET_EGG_GAMEPLAY_JA.md'])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20260923-LEARNSET-VISUAL\n- Version: issue19-visual-capture-v1\n- Status: {v["status"]}\n- Summary: 一覧state4/6とsummary描画待ちを限定修復。Mew/Floetteの2対象は習得・Save前に停止し4枚をartifact保存。\n- Files changed: 専用source投影/validator/10境界試験/Actions、checkpoint/text原本・固定引継ぎMD/JSON・guide・両ログ。\n- Verify: run{v["run_id"]} native {v["native_processes"]}・unit {v["new_unit_tests"]}。受入全Bag/戦闘/タマゴ/ARM/Wiki再実行0、ROM変更0。目視は別途未完として保持。\n- Commit: 同branchへ非force pushしreflected-headをremote照合。\n- Network: 保存候補/固定Bag artifactのみ。binaryは新規追跡しない。全履歴guard/release成功を主張しない。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(log)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned()-CODE;g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths');actions[sys.argv[1]]()
