#!/usr/bin/env python3
"""Issue19: 特殊野生の候補内呼出順だけを新規観測し、既受入を再実行しない。"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
TASK='USER-20260925-SPECIAL-WILD'
BASE='content/modernization/'
CP=BASE+'pr16_special_wild_checkpoint.json'
GUIDE='docs/PR16_SPECIAL_WILD_JA.md'
STATE=BASE+'pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
SELF='scripts/pr16_special_wild.py'
C='tools/mgba_pr16_special_wild.c'
TEST='tests/test_pr16_special_wild.py'
WF='.github/workflows/pr16-special-wild-20260925.yml'
CODE={SELF,C,TEST,WF}
SOURCES={'tools/mgba_regression_smoke.c','src/modernization/pr16_learnset_wild_game.c',
 'overlays/move_distribution_v4/move_distribution_v4.c',
 'overlays/qol_production/qol_production.c',
 'overlays/research_economy_v1/research_economy_v1.c',
 'overlays/stage59_wild_identity_npc_regression_repair/stage59_wild_identity_npc_regression_repair.c',
 'config/research_economy_v1.json','config/stage59_wild_identity_npc_regression_repair.json'}
PROTECTED={BASE+n for n in ('pr16_research_hatch_checkpoint.json','pr16_collection_gifts_checkpoint.json','pr16_natural_supply_checkpoint.json','pr16_learnset_natural_checkpoint.json','pr16_bp_chooser_checkpoint.json','p08_remaining_work.json')}
PROTECTED|={'config/active_play_baseline.json','state/source-lock.json'}
CANDIDATE={'size':33554432,'sha256':'b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91'}
WORK=ROOT/'.local/pr16-special-wild';PROOF=WORK/'proof'
EVIDENCE=BASE+'pr16_special_wild_evidence'
METHODS=('fishing','hidden')


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def load(p):return json.loads(Path(p).read_bytes())
def write(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encode(v))

def unique(pairs):
    out={}
    for k,v in pairs:
        need(k not in out,'duplicate JSON key');out[k]=v
    return out


def decode_lines(raw):
    need(type(raw) is bytes and 0<len(raw)<=1000000,'native output bounds')
    return [json.loads(line,object_pairs_hook=unique) for line in raw.decode('utf-8').splitlines()]


def mon(raw):
    need(type(raw) is str and re.fullmatch('[0-9a-f]{200}',raw),'party100 byte encoding')
    raw=bytes.fromhex(raw);species=struct.unpack_from('<H',raw,32)[0]
    need(0<species<1671 and 1<=raw[84]<=100,'generated owner/level')
    return {'identity':identity(raw),'species':species,'pid':struct.unpack_from('<I',raw)[0],
            'level':raw[84],'moves':list(struct.unpack_from('<4H',raw,44)),
            'pp':list(raw[52:56]),'pp_bonus':raw[40]}


def validate(raw,method):
    need(method in METHODS,'known method')
    rows=decode_lines(raw);summary=rows[-1]
    need(summary==dict(event='summary',status='OBSERVED',method=method,calls=summary.get('calls'),host_write_violations=0,direct_call_fixture=True,gameplay_accepted=False,save_continue_accepted=False),'nonpromoted observation summary')
    count=summary['calls'];need(type(count)is int and 1<=count<=8,'bounded calls')
    calls=[x for x in rows if x['event']=='call'];need([x['attempt'] for x in calls]==list(range(1,count+1)),'unique complete native calls')
    fixture=[x for x in rows if x['event']=='fixture']
    need(len(fixture)==1 and fixture[0]['method']==method and fixture[0]['dispatch_status']==0 and fixture[0]['profile']==1 and fixture[0]['normal_unlock_claimed'] is False,'explicit research fixture')
    selected=[x for x in rows if x.get('attempt')==count]
    setters=[x for x in selected if x['event']=='special_setter'];applies=[x for x in selected if x['event']=='before_apply'];final=[x for x in selected if x['event']=='after_return'];result=[x for x in selected if x['event']=='result']
    need(len(setters)==len(applies)==len(final)==len(result)==1,'one special write and one post-generation reset')
    setter=setters[0];before=mon(applies[0]['party']);after=mon(final[0]['party'])
    need(setter['pc']==0x09114698 and setter['slot']==3 and 0<setter['move']<2000,'native special setter')
    need(setter['step']<applies[0]['step']<final[0]['step'],'generation/special/reset order')
    need(before['species']==after['species']==result[0]['species'] and before['pid']==after['pid'] and before['level']==after['level'],'same native individual')
    need(before['moves'][3]==setter['move'] and before['pp'][3]>0,'actual special slot before reset')
    need(result[0]['returned']!=0 and result[0]['special_setters']==result[0]['apply_calls']==1,'native success path')
    entries=[x['pc'] for x in selected if x['event']=='entry']
    expected=[0x08082750,0x093BEA68,0x09392714] if method=='fishing' else [0x09220198,0x093BEA98,0x0939273C]
    need(entries==expected,'candidate entry/research/V4 delegate order')
    classification='SPECIAL_SLOT_PRESERVED' if before['moves']==after['moves'] and before['pp']==after['pp'] and before['pp_bonus']==after['pp_bonus'] else 'SPECIAL_SLOT_OVERWRITTEN'
    return {'classification':classification,'before':before,'after':after,'special_move':setter['move'],'setter_lr':setter['lr'],'steps':final[0]['step'],'calls':count,'selected_seed':calls[-1]['seed'],'entries':entries,'runtime_accepted':False,'gameplay_accepted':False,'save_continue_accepted':False}


def anchors(rom):
    need(identity(rom)==CANDIDATE,'exact candidate before binary analysis')
    q=rom.find(b'VEGAQP36');need(q>=0 and rom.find(b'VEGAQP36',q+1)<0,'unique QOL header')
    fields=struct.unpack_from('<12I',rom,q+8);version,size,code=fields[:3]
    need(version==1 and 0<code<size and q+size<=len(rom) and fields[3]==35 and fields[5]==846,'QOL envelope')
    dispatch=fields[8];need(dispatch&1 and q+0x08000100<=dispatch<q+0x08000000+size,'QOL dispatcher inside envelope')
    hooks={}
    for name,off in [('fishing',0x82750),('hidden',0x1220198),('wild_initial',0x13925F4)]:
        need(rom[off:off+4]==bytes.fromhex('004b1847'),'candidate hook '+name)
        target=struct.unpack_from('<I',rom,off+4)[0];need(target&1 and 0x08000000<=target<0x0A000000,'candidate hook target')
        hooks[name]={'address':0x08000000+off,'target':target,'entry':identity(rom[off:off+8])}
    need(hooks['wild_initial']['target']==0x095FF881,'accepted initializer target')
    return {'qol_start':q+0x08000100,'qol_end':q+0x08000000+size,'dispatch':dispatch,'hooks':hooks}


def command(args,name,timeout=300):
    try:
        r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout)
        out,err,rc,timed=r.stdout,r.stderr,r.returncode,False
    except subprocess.TimeoutExpired as ex:out,err,rc,timed=ex.stdout or b'',ex.stderr or b'',-1,True
    (PROOF/(name+'.stdout.txt')).write_bytes(out);(PROOF/(name+'.stderr.txt')).write_bytes(err)
    write(PROOF/(name+'.process.json'),{'returncode':rc,'timed_out':timed})
    need(rc==0 and not timed,'command failed: '+name)
    return out,err


def execute():
    from pr16_learnset_wiki_actions import current
    import pr16_learnset_battle as b
    import pr16_learnset_entry_repair as entry
    import pr16_learnset_wild_repair as wild
    head=current();need(not WORK.exists() and not (ROOT/CP).exists(),'diagnostic already recorded; do not rerun')
    PROOF.mkdir(parents=True)
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':CANDIDATE,'status':'RUNNING','results':{},'failure':None,'new_unit_tests':0,'native_processes':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0,'accepted_case_reruns':0,'actions_completion_confirmed':False,'issue19_complete':False,'release_ready':False,'active_baseline_changed':False,'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|SOURCES},'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in PROTECTED}}
    try:
        _,err=command([sys.executable,'-B','-m','unittest','tests.test_pr16_special_wild','-v'],'unit')
        match=re.search(rb'Ran (\d+) tests? in ',err);need(match and b'\nOK\n'in err,'new unit completion');v['new_unit_tests']=int(match[1])
        cp=load(ROOT/BASE/'pr16_learnset_natural_checkpoint.json');need(cp['candidate']==CANDIDATE and cp['actions_completion_confirmed'],'accepted parent recipe')
        b.WORK=WORK/'restore-root';b.WORK.mkdir();parent=b.restore();rom,_=entry.apply(parent);rom=wild.replay(rom,cp['wild_repair'])
        a=anchors(rom);write(PROOF/'anchors.json',a);(WORK/'candidate.gba').write_bytes(rom)
        for label,start,end in [('v4',0x13925F4,0x1392764),('research',0x13BEA68,0x13BEAC0)]:
            p=WORK/(label+'.bin');p.write_bytes(rom[start:end]);command(['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb','--adjust-vma='+hex(0x08000000+start),str(p)],label+'-disassembly')
        v['host_compiles']+=1
        _,err=command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-MMD','-MF',str(WORK/'probe.d'),C,'-lmgba','-o',str(WORK/'probe')],'compile')
        need(not err,'new host compiler diagnostics')
        dependencies=shlex.split((WORK/'probe.d').read_text().replace('\\\n',' ').split(':',1)[1])
        v['compiled_sources']={Path(p).as_posix():identity((ROOT/p).read_bytes()) for p in dependencies}
        guards={}
        for api in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
            r=subprocess.run([str(WORK/'probe'),'--reject',api],capture_output=True)
            need(r.returncode==1 and b'host write inside native observation'in r.stderr,'guard rejects '+api)
            guards[api]={'returncode':r.returncode,'emulator_created':False}
        write(PROOF/'guard-rejections.json',guards)
        for method in METHODS:
            v['native_processes']+=1
            out,err=command([str(WORK/'probe'),str(WORK/'candidate.gba'),method,str(a['dispatch']),str(a['qol_start']),str(a['qol_end'])],method,600)
            need(not err,'native warning/error')
            v['results'][method]=validate(out,method)
        v['status']='OBSERVED_SPECIAL_WILD_ORDER'
    except Exception as ex:
        v['status']='STOPPED_SPECIAL_WILD_DIAGNOSTIC';v['failure']={'type':type(ex).__name__,'message':str(ex)};raise
    finally:
        for p,binding in v['protected_bindings'].items():need(identity((ROOT/p).read_bytes())==binding,'protected acceptance changed '+p)
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v)


def owned():
    dest=ROOT/EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return {CP,GUIDE,STATE,DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.rglob('*') if p.is_file()}


def publish(v):
    from pr16_learnset_compact_record import publish_resume
    conclusions={k:r['classification'] for k,r in v['results'].items()}
    nextstep='Issue19: 特殊野生checkpointの実ROM呼出順とbefore/afterを根拠に釣り/隠し専用の最小修復へ進む。診断済み同条件は再実行せず、変更後の必要な対照だけ追加。通常釣竿/スキャナー操作→捕獲→Save/fresh Continueは未受入。研究孵化15/研究配布17/旧野生/EXP/Bag/egg/旧ARM/Wikiは変更影響がなければ再実行しない。'
    if v['failure']:nextstep='Issue19: 特殊野生診断の保存失敗原本から未成功caseだけ縮小修復。成功したcase/既受入を再実行しない。'+nextstep
    (ROOT/GUIDE).write_text(f'''# PR16 Issue19: 釣り・隠し野生の特殊技順

状態 `{v['status']}`。run `{v['run_id']}` / source `{v['source_head']}`。
候補 `{CANDIDATE['sha256']}` / {CANDIDATE['size']} bytes。判定 `{conclusions}`。

## 今回の境界

新規のnative直接呼出診断であり、通常釣竿/スキャナーUI、通常解禁、捕獲、Save/Continueの受入ではない。
新規起動後のmap/進行flag/profile/RNGは開始fixture。呼出入口/復帰のレジスタ設定も観測区間外。
区間内は7種類のhost書込APIを拒否し、CPUをstepするだけで生成→QOL特殊技第4枠→実V4再初期化→復帰を記録。
保存原本の同一PID/species/level・技4枠/PP/PP Upsを比較する。getter補助は区間外。
候補のStage59入口、Research Economy delegate、V4 delegate、QOL special setterの実通過が必要。
新規unit {v['new_unit_tests']}、host compile {v['host_compiles']}、native process {v['native_processes']}。旧受入再実行/ARM/ROM変更0。
Actions終端 `{v['actions_completion_confirmed']}`。診断のActions成功を製品受入へ読み替えない。
原本 `{v['evidence_path']}`。1281 identity-only、Issue19全体未完、release_ready=false、PR未merge、baseline不変。

## 次

{nextstep}
''',encoding='utf-8')
    state=load(ROOT/STATE)
    state['learnset_special_wild']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')}
    state['learnset_special_wild'].update(path=CP,conclusions=conclusions,native_cases=0,diagnostic_processes=v['native_processes'])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='特殊野生の新規直接診断。通常取得受入・全体完成とは別。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'in_progress','conclusion':None}],'reason_ja':'記録時点ではpush/upload終端未確認。初期b3e45540のsource転送run36150780558は成功、実受入0。一般CIを成功へ昇格しない。'}
    state['bp']['current_stop']=f'Issue19: 特殊野生 {conclusions}。{v["status"]}。通常釣竿/スキャナー取得は未受入。';state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='SPECIAL_WILD_ORDER',goal_ja=nextstep,read_paths=[GUIDE,CP,SELF,TEST])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 特殊野生の実呼出順\n- Version: issue19-special-wild-diagnostic-v1\n- Status: '+('DONE（限定診断のみ、修復/通常供給は未完）' if not v['failure'] else 'STOPPED（保存原本から未完のみ継続）')+f'\n- Summary: {conclusions}。開始進行/map/profile/RNGと直接呼出はfixture、実観測区間7API書込拒否。\n- Files changed: 専用driver/C/tests/workflow、checkpoint/guide/text証拠、固定引継ぎMD/JSON、両ログ。\n- Verify: {v["status"]}; 新unit {v["new_unit_tests"]}, host {v["host_compiles"]}, native {v["native_processes"]}; 旧受入/ARM/ROM/Wiki再実行0。Actions終端は未確認。\n- Commit: 同branchへ非force push、reflected-head.txtでremote照合。source取得WIP b3e45540/36150780558は転送のみ。\n- Network: GitHub固定artifact/Actionsのみ。原本再採取/merge/release/active baseline変更なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(note)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record source')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'no overwrite of evidence');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_bytes().decode('utf-8');need('\0'not in text,'text evidence only')
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'private user path');(dest/p.name).write_text(safe,encoding='utf-8')
    v['public_evidence_bindings']={p.name:identity(p.read_bytes()) for p in dest.iterdir()};v['evidence_path']=dest.relative_to(ROOT).as_posix()
    write(ROOT/CP,v);publish(v)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths');actions[sys.argv[1]]()
