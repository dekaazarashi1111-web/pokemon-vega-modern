#!/usr/bin/env python3
"""Issue19: 研究表に結合した特殊野生の観測→2 callsite限定修復。"""
from __future__ import annotations
import ast
import csv
import datetime
import io
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_special_wild as old
need,identity,load,write,encode=old.need,old.identity,old.load,old.write,old.encode
TASK=old.TASK
CP=old.BASE+'pr16_special_wild_repair_checkpoint.json'
GUIDE=old.GUIDE
SELF='scripts/pr16_special_wild_repair.py'
TEST='tests/test_pr16_special_wild_repair.py'
WF='.github/workflows/pr16-special-wild-repair-20260925.yml'
CODE={SELF,TEST,WF}
INPUTS={'manifests/research_encounters.csv','manifests/species_ids.csv','content/map_bindings.csv','scripts/build_qol_production.py'}
WORK=ROOT/'.local/pr16-special-wild-repair'
PROOF=WORK/'proof'
PARENT_RUN=36152934075
PARENT_SOURCE='23420259b94bcfff71078d91ccb7593a1c30c92b'
PARENT_HEAD='684fd787802a6df546b7953b8ab94bdbb95051cd'
PREIMAGES={0x1392722:bytes.fromhex('fff767ff'),0x139274A:bytes.fromhex('fff753ff')}
NOP=bytes.fromhex('c046c046')
STRIDE=0x9E3779B9
LIMIT=64


def rows(path):
    with (ROOT/path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def research_rows():
    """既存builderを実行せず、現在sourceの宣言と846行を厳格に解決する。"""
    tree=ast.parse((ROOT/'scripts/build_qol_production.py').read_text())
    values=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UNLOCK_CODES' for t in n.targets)]
    need(len(values)==1,'one declared unlock mapping');unlocks=values[0]
    maps={r['map_key']:r for r in rows('content/map_bindings.csv')}
    species={r['species_key']:r for r in rows('manifests/species_ids.csv')}
    result=[]
    for r in rows('manifests/research_encounters.csv'):
        if r['status']!='ACTIVE' or r['shared_capture_key']!='NONE':continue
        m=maps[r['map_key']];sp=species[r['species_key']]
        need(m['status']=='ACTIVE' and r['unlock_key'] in unlocks,'active research binding')
        need(r['shiny_policy']=='MINOR_BONUS_NO_CHAIN_LEAK' and r['egg_move_policy']=='ONE_LEGAL_MOVE','authored research contract')
        fields=[int(m['group_id']),int(m['map_id']),int(sp['id']),int(r['level_min']),int(r['level_max']),int(r['iv_floor']),int(r['hidden_ability_rate']),5 if r['held_item_policy']=='MODERN_LEGAL_LOW_RATE' else 0,2,unlocks[r['unlock_key']],int(r['normal_preserved'].lower()=='true')]
        result.append({'research_key':r['research_key'],'region':r['region'],'fields':fields})
    result.sort(key=lambda r:(*r['fields'][:2],r['research_key']))
    need(len(result)==846 and len({r['research_key'] for r in result})==846,'exact unique 846 research rows')
    return result


def select_fixture(rom,a,declared):
    packed=b''.join(struct.pack('<BBH8B',*r['fields']) for r in declared)
    qstart,qend=a['qol_start']-0x08000000,a['qol_end']-0x08000000
    first=rom.find(packed,qstart,qend)
    need(first>=0 and rom.find(packed,first+1,qend)<0,'exact authored846/QOL binary table')
    bymap={}
    for r in declared:
        if r['region']=='TOHOKU' and r['fields'][9]<=8:
            bymap.setdefault(tuple(r['fields'][:2]),[]).append(r)
    root=struct.unpack_from('<I',rom,0x8257C)[0]-0x08000000
    need(0<=root<len(rom)-20,'bounded wild header root')
    candidates=[];ended=False;seen=set()
    for i in range(1024):
        off=root+20*i;need(off+20<=len(rom),'bounded wild table scan')
        g,m=rom[off:off+2]
        if (g,m)==(255,255):ended=True;break
        pair=(g,m);need(pair not in seen,'unique wild map header');seen.add(pair)
        info=struct.unpack_from('<I',rom,off+16)[0]
        if pair not in bymap or not 0x08000000<=info<0x0A000000-8:continue
        ptr=struct.unpack_from('<I',rom,info-0x08000000+4)[0]
        if not 0x08000000<=ptr<0x0A000000-40:continue
        candidates.append({'map':list(pair),'info':info,'header_offset':off,'header':identity(rom[off:off+20]),'rows':bymap[pair]})
    need(ended and candidates,'terminated header inventory with research fishing intersection')
    candidates.sort(key=lambda c:(len(c['rows']),c['map']))
    selected=candidates[0]
    need(tuple(selected['map'])!=(11,3),'do not repeat original unbound fixture')
    need((3,63) in bymap,'hidden existing ecology fixture has authored research rows')
    return {'fishing':selected,'hidden':{'map':[3,63],'rows':bymap[(3,63)]},'candidates':[{k:c[k] for k in ('map','info')} for c in candidates],'research_table':{'offset':first,**identity(packed)},'root':root,'header_count':i,'old_unbound_map':[11,3]}


def patch_candidate(rom):
    """Late V4 reset callsだけNOP。共通initializer/land/return flowは不変。"""
    need(identity(rom)==old.CANDIDATE,'exact accepted parent; no patch chaining')
    candidate=bytearray(rom);changes=[]
    for off,before in PREIMAGES.items():
        need(rom[off:off+4]==before,'late call preimage')
        first,second=struct.unpack('<HH',before)
        relative=((first&0x7FF)<<12)|((second&0x7FF)<<1)
        if relative&(1<<22):relative-=1<<23
        need(0x08000000+off+4+relative==0x093925F4,'BL target is shared initializer')
        need(rom[off+4:off+12]==bytes.fromhex('200010bc02bc0847'),'unchanged saved r4 return ABI')
        candidate[off:off+4]=NOP
        changes.append({'offset':off,'before':before.hex(),'after':NOP.hex(),'surrounding':identity(rom[off-14:off+18])})
    candidate=bytes(candidate)
    actual={i for i,(a,b) in enumerate(zip(rom,candidate)) if a!=b}
    expected={off+i for off in PREIMAGES for i in range(4)}
    need(actual==expected and len(candidate)==len(rom),'exact 8 changed bytes only')
    reverted=bytearray(candidate)
    for row in changes:reverted[row['offset']:row['offset']+4]=bytes.fromhex(row['before'])
    need(bytes(reverted)==rom,'full ROM rollback')
    return candidate,{'parent':identity(rom),'candidate':identity(candidate),'patches':changes,'changed_bytes':8,'outside_declared_changes':0,'rollback_verified':True,'arm_compiles':0,'shared_initializer_changed':False,'land_adapter_changed':False}


NEW_MAIN=r'''
int main(int argc,char**argv){
    if(argc==3&&!strcmp(argv[1],"--reject"))reject_test(argv[2]);
    if(argc!=12){fprintf(stderr,"usage: probe ROM METHOD DISPATCH QSTART QEND GROUP MAP SEED LIMIT PROFILE MODE\n");return 2;}
    bool fishing=!strcmp(argv[2],"fishing");if(!fishing&&strcmp(argv[2],"hidden"))return 2;
    uint32_t dispatch=parse_u32(argv[3],"dispatch"),qb=parse_u32(argv[4],"QOL start"),qe=parse_u32(argv[5],"QOL end");
    unsigned group=parse_u32(argv[6],"group"),map=parse_u32(argv[7],"map"),limit=parse_u32(argv[9],"limit"),profile=parse_u32(argv[10],"profile"),mode=parse_u32(argv[11],"mode");
    uint32_t seed0=parse_u32(argv[8],"seed");
    if(group>255U||map>255U||limit<1U||limit>64U||profile>1U||mode>2U||!rom_code_pointer(dispatch)||qb<ROM_BASE||qe>ROM_END||qb>=qe)die("explicit fixture bounds");
    struct mLogger logger={.log=silent_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    struct mCore*c=mCoreFind(argv[1]);if(!c||!c->init(c)||!mCoreLoadFile(c,argv[1]))die("core init");
    mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");
    color_t*video=calloc(GBA_WIDTH*GBA_HEIGHT,sizeof(*video));if(!video)die("video");c->setVideoBuffer(c,video,GBA_WIDTH);c->reset(c);
    uint32_t transitions=run_natural_new_game(c,video),save=read32(c,G_SAVE_BLOCK1);
    if(save<0x02000000U||save+6U>=0x02040000U)die("save pointer");
    for(unsigned f=0x0820U;f<=0x082CU;++f)(void)call_thumb(c,0x0806DE75U,f,0,0,0);
    (void)call_thumb(c,0x0806DE75U,0x114BU,0,0,0);
    uint32_t status=call_thumb(c,dispatch,15U,profile,0,0);
    printf("{\"event\":\"fixture\",\"method\":\"%s\",\"dispatch_status\":%u,\"profile\":%u,\"transitions\":%u,\"normal_unlock_claimed\":false,\"map\":[%u,%u],\"seed_start\":%u,\"limit\":%u,\"mode\":%u}\n",argv[2],status,read8(c,0x0203D01FU),transitions,group,map,seed0,limit,mode);
    if(status!=0U||read8(c,0x0203D01FU)!=profile)die("native profile fixture mismatch");
    uint32_t info=0,root=read32(c,0x0808257CU);if(!rom_pointer(root))die("wild root");
    for(unsigned i=0;i<1024U;++i){uint32_t h=root+20U*i;unsigned g=read8(c,h),m=read8(c,h+1U);if(g==255U&&m==255U)break;if(g==group&&m==map)info=read32(c,h+16U);}
    if(fishing&&!rom_pointer(info))die("fishing fixture table absent");
    write8(c,save+4U,group);write8(c,save+5U,map);
    unsigned specials=0,applies=0,attempt=0;bool witnessed=false;
    for(attempt=1U;attempt<=limit;++attempt){
        for(unsigned i=0;i<PARTY_BYTES;++i)write8(c,ENEMY_PARTY+i,0);
        write8(c,ENEMY_PARTY_COUNT,0);uint32_t seed=seed0+(attempt-1U)*0x9E3779B9U;write32(c,GLOBAL_RNG,seed);
        printf("{\"event\":\"call\",\"attempt\":%u,\"seed\":%u,\"entry\":%u,\"map\":[%u,%u]}\n",attempt,seed,fishing?0x08082751U:0x09220199U,group,map);
        uint32_t result=observed(c,fishing?0x08082751U:0x09220199U,fishing?info:0,fishing?2U:0,attempt,qb,qe,&specials,&applies);
        printf("{\"event\":\"result\",\"attempt\":%u,\"returned\":%u,\"species\":%u,\"special_setters\":%u,\"apply_calls\":%u,\"post_calls\":%u}\n",attempt,result,(unsigned)call_thumb(c,GET_MON_DATA,ENEMY_PARTY,11U,0,0),specials,applies,sw_post_calls);fflush(stdout);
        witnessed=result!=0U&&sw_post_calls==1U&&(mode==0U?specials==0U:(specials==1U&&(mode!=2U||sw_special_move!=read16(c,ENEMY_PARTY+50U))));
        if(witnessed)break;
    }
    printf("{\"event\":\"summary\",\"status\":\"%s\",\"method\":\"%s\",\"calls\":%u,\"host_write_violations\":%u,\"direct_call_fixture\":true,\"gameplay_accepted\":false,\"save_continue_accepted\":false}\n",witnessed?"OBSERVED":"NO_SPECIAL_WITNESS",argv[2],attempt<=limit?attempt:limit,violations);
    free(video);mCoreConfigDeinit(&c->config);c->deinit(c);return witnessed?0:1;
}
'''


def generated_source():
    text=(ROOT/old.C).read_text()
    edits={
        'static unsigned violations;':'static unsigned violations;\nstatic unsigned sw_post_calls;\nstatic uint16_t sw_special_move;',
        'uint64_t steps=0;guard(c);*special=0;*apply=0;':'uint64_t steps=0;sw_post_calls=0;sw_special_move=0;guard(c);*special=0;*apply=0;',
        '++*special;printf':'sw_special_move=(uint16_t)read_register(c,"r1");++*special;printf',
        'if(at==0x093925F4U){':'if(at==0x09392722U||at==0x0939274AU){++sw_post_calls;dump_mon(c,"before_post",attempt,steps);}\n        if(at==0x093925F4U){',
        'int main(int argc,char**argv){':'int saved_probe_main(int argc,char**argv){',
    }
    for before,after in edits.items():need(text.count(before)==1,'exact probe source anchor');text=text.replace(before,after)
    return text+NEW_MAIN


def native_result(raw,method,a,fixture,patched,special):
    data=old.decode_lines(raw);summary=data[-1];count=summary.get('calls')
    need(summary==dict(event='summary',status='OBSERVED',method=method,calls=count,host_write_violations=0,direct_call_fixture=True,gameplay_accepted=False,save_continue_accepted=False),'unpromoted guarded native completion')
    need(type(count)is int and 1<=count<=fixture['limit']<=LIMIT,'bounded native calls')
    setup=[r for r in data if r['event']=='fixture']
    need(len(setup)==1 and all(setup[0][k]==fixture[k] for k in ('map','seed_start','limit','mode','profile')) and setup[0]['dispatch_status']==0 and setup[0]['normal_unlock_claimed'] is False,'fixed fixture echoed')
    calls=[r for r in data if r['event']=='call']
    need(len(calls)==count and [r['attempt'] for r in calls]==list(range(1,count+1)),'complete unique call indices')
    for i,c in enumerate(calls):need(c['map']==fixture['map'] and c['seed']==(fixture['seed_start']+i*STRIDE)&0xFFFFFFFF,'declared distinct seed sequence')
    last=[r for r in data if r.get('attempt')==count]
    def one(event):
        found=[r for r in last if r['event']==event];need(len(found)==1,'one '+event);return found[0]
    pre=one('before_post');final=one('after_return');result=one('result')
    before,after=old.mon(pre['party']),old.mon(final['party'])
    need(pre['step']<final['step'],'post-generation call order')
    need(before['species']==after['species']==result['species'] and before['pid']==after['pid'] and before['level']==after['level'],'same individual through late adapter')
    need(result['returned']!=0 and result['post_calls']==1 and result['apply_calls']==(0 if patched else 1),'preserved return and exact reset count')
    applies=[r for r in last if r['event']=='before_apply'];need(len(applies)==(0 if patched else 1),'exact observed reset entries')
    if applies:need(pre['step']<applies[0]['step']<final['step'] and pre['party']==applies[0]['party'],'old callsite/same mon at initializer')
    entries=[r['pc'] for r in last if r['event']=='entry']
    expected=[0x08082750,0x093BEA68,0x09392714] if method=='fishing' else [0x09220198,0x093BEA98,0x0939273C]
    need(entries==expected,'actual original-entry/research/V4 chain; not Stage59')
    setters=[r for r in last if r['event']=='special_setter'];need(len(setters)==result['special_setters']==int(special),'exact special setter count')
    special_move=None
    if special:
        setter=setters[0];special_move=setter['move']
        need(setter['pc']==0x09114698 and setter['slot']==3 and a['qol_start']<=setter['lr']<a['qol_end'] and setter['step']<pre['step'],'actual QOL special setter origin/order')
        need(0<special_move<2000 and before['moves'][3]==special_move and before['pp'][3]>0,'written special before late reset')
    equal=all(before[k]==after[k] for k in ('moves','pp','pp_bonus'))
    if patched:need(equal and pre['party']==final['party'],'patched full individual/moves/PP/PP Ups preserved')
    elif special:need(not equal and special_move!=after['moves'][3],'actual overwritten special before repair')
    else:need(equal and pre['party']==final['party'],'unchanged no-special control')
    return {'method':method,'classification':'SPECIAL_SLOT_PRESERVED' if special and patched else 'SPECIAL_SLOT_OVERWRITTEN' if special else 'NO_SPECIAL_UNCHANGED','before':before,'after':after,'special_move':special_move,'calls':count,'selected_seed':calls[-1]['seed'],'returned':result['returned'],'entries':entries,'fixture':fixture,'patched':patched,'source_scope':'DIRECT_ENTRY_FIXTURE_NOT_GAMEPLAY','gameplay_accepted':False,'save_continue_accepted':False}


def initial_control(v):
    need(v['run_id']==PARENT_RUN and v['source_head']==PARENT_SOURCE and v['candidate']==old.CANDIDATE and v['status']=='STOPPED_SPECIAL_WILD_DIAGNOSTIC' and not v['results'],'original failed experiment retained')
    folder=ROOT/v['evidence_path']
    for n,b in v['public_evidence_bindings'].items():need(identity((folder/n).read_bytes())==b,'unchanged original evidence '+n)
    raw=(folder/'fishing.stdout.txt').read_bytes();data=old.decode_lines(raw)
    need(data[-1]['status']=='NO_SPECIAL_WITNESS' and data[-1]['calls']==8 and data[-1]['host_write_violations']==0,'original eight normal calls, not success')
    for attempt in range(1,9):
        rs=[r for r in data if r.get('attempt')==attempt]
        pre=[r for r in rs if r['event']=='before_apply'];post=[r for r in rs if r['event']=='after_return'];ret=[r for r in rs if r['event']=='result']
        need(len(pre)==len(post)==len(ret)==1 and pre[0]['party']==post[0]['party'] and ret[0]['special_setters']==0 and ret[0]['apply_calls']==1,'saved normal/no-rule retention')
    return {'source_run':PARENT_RUN,'raw_binding':identity(raw),'selected_seed':0x24681357,'mon':old.mon(next(r['party'] for r in data if r.get('attempt')==1 and r['event']=='after_return')),'cases_reexecuted':0}


def invoke(rom,method,a,fixture,patched,special,label):
    cmd=[str(WORK/'probe'),str(rom),method,str(a['dispatch']),str(a['qol_start']),str(a['qol_end']),*[str(x) for x in fixture['map']],*[str(fixture[k]) for k in ('seed_start','limit','profile','mode')]]
    out,err=old.command(cmd,label,600);need(not err,'native diagnostics absent '+label)
    result=native_result(out,method,a,fixture,patched,special);write(PROOF/(label+'.result.json'),result);return result


def execute():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    import pr16_learnset_battle as b
    import pr16_learnset_entry_repair as entry
    import pr16_learnset_wild_repair as wild
    head=current();need(not WORK.exists() and not (ROOT/CP).exists(),'new repair only; do not rerun saved repair')
    PROOF.mkdir(parents=True);old.PROOF=PROOF
    predecessor=load(ROOT/old.CP)
    protected=old.PROTECTED|{old.CP}|set(predecessor['source_bindings'])
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'parent_candidate':old.CANDIDATE,'candidate':old.CANDIDATE,'status':'RUNNING','results':{},'controls':{},'failures':{},'failure':None,'new_unit_tests':0,'native_processes':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0,'accepted_case_reruns':0,'actions_completion_confirmed':False,'issue19_complete':False,'release_ready':False,'active_baseline_changed':False,'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|INPUTS|set(predecessor['source_bindings'])},'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in protected}}
    try:
        run=fetch('actions/runs/'+str(PARENT_RUN));need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==PARENT_SOURCE,'original failed Actions terminal')
        v['predecessor']={'run_id':PARENT_RUN,'head':PARENT_SOURCE,'conclusion':'failure','reflected_head':PARENT_HEAD,'control':initial_control(predecessor)}
        subprocess.run(['git','merge-base','--is-ancestor',PARENT_HEAD,head],check=True)
        _,err=old.command([sys.executable,'-B','-m','unittest','tests.test_pr16_special_wild_repair','-v'],'new-unit')
        match=re.search(rb'Ran (\d+) tests? in ',err);need(match and b'\nOK\n'in err,'new repair unit completion');v['new_unit_tests']=int(match[1])
        cp=load(ROOT/old.BASE/'pr16_learnset_natural_checkpoint.json');b.WORK=WORK/'restore-root';b.WORK.mkdir()
        parent=b.restore();rom,_=entry.apply(parent);rom=wild.replay(rom,cp['wild_repair']);a=old.anchors(rom)
        fixtures=select_fixture(rom,a,research_rows());v['fixtures']=fixtures;write(PROOF/'fixtures.json',fixtures);write(PROOF/'anchors.json',a)
        parentpath=WORK/'parent.gba';parentpath.write_bytes(rom)
        source=generated_source();cfile=PROOF/'probe.c';cfile.write_text(source)
        v['host_compiles']=1;_,err=old.command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools',str(cfile),'-lmgba','-o',str(WORK/'probe')],'compile');need(not err,'warning-free probe compile')
        v['compiled_source']=identity(cfile.read_bytes())
        for api in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
            r=subprocess.run([str(WORK/'probe'),'--reject',api],capture_output=True)
            need(r.returncode==1 and b'host write inside native observation'in r.stderr,'same seven write barriers '+api)
        write(PROOF/'guard-rejections.json',{'apis':7,'emulator_created':False,'rejected':True})
        for method in ('hidden','fishing'):
            f={'map':fixtures[method]['map'],'seed_start':0x13572468 if method=='hidden' else 0xABCD1234,'limit':LIMIT,'profile':1,'mode':2}
            v['native_processes']+=1
            try:v['results']['parent-'+method]=invoke(parentpath,method,a,f,False,True,'parent-'+method)
            except Exception as ex:v['failures']['parent-'+method]={'type':type(ex).__name__,'message':str(ex)}
        need(not v['failures'] and len(v['results'])==2,'both original special losses required before repair')
        candidate,recipe=patch_candidate(rom);candidate2,recipe2=patch_candidate(rom)
        need(candidate==candidate2 and recipe==recipe2,'independent replay identity')
        successor=WORK/'candidate.gba';successor.write_bytes(candidate);v['candidate']=identity(candidate);v['repair']=recipe;v['rom_changes']=1;write(PROOF/'repair.json',recipe)
        for method in ('hidden','fishing'):
            base=v['results']['parent-'+method];f=dict(base['fixture'],seed_start=base['selected_seed'],limit=1,mode=1)
            v['native_processes']+=1
            try:
                measured=invoke(successor,method,a,f,True,True,'repaired-'+method)
                need(measured['before']==base['before'] and measured['returned']==base['returned'],'same seeded individual and original return '+method)
                v['results']['repaired-'+method]=measured
            except Exception as ex:v['failures']['repaired-'+method]={'type':type(ex).__name__,'message':str(ex)}
        # 旧失敗runの正常/no-rule対照は再実行しない。変更後だけ同じseedを照合。
        f={'map':[11,3],'seed_start':v['predecessor']['control']['selected_seed'],'limit':1,'profile':1,'mode':0}
        v['native_processes']+=1
        try:
            control=invoke(successor,'fishing',a,f,True,False,'control-fishing-no-rule')
            need(control['after']==v['predecessor']['control']['mon'],'saved original normal control identity');v['controls']['fishing-no-rule']=control
        except Exception as ex:v['failures']['control-fishing-no-rule']={'type':type(ex).__name__,'message':str(ex)}
        # 隠しのNORMAL側は未観測だったため、この変更で影響する対照だけ新規に比較。
        f={'map':fixtures['hidden']['map'],'seed_start':0xABCDEF01,'limit':LIMIT,'profile':0,'mode':0}
        v['native_processes']+=1
        try:
            normal=invoke(parentpath,'hidden',a,f,False,False,'control-hidden-parent');v['controls']['hidden-parent']=normal
            f=dict(f,seed_start=normal['selected_seed'],limit=1);v['native_processes']+=1
            changed=invoke(successor,'hidden',a,f,True,False,'control-hidden-repaired')
            need(changed['after']==normal['after'] and changed['returned']==normal['returned'],'normal hidden control unchanged');v['controls']['hidden-repaired']=changed
        except Exception as ex:v['failures']['control-hidden']={'type':type(ex).__name__,'message':str(ex)}
        need(not v['failures'] and len(v['results'])==4 and len(v['controls'])==3,'two repaired special paths and necessary negative controls')
        v['status']='PASS_SPECIAL_WILD_REPAIR_DIRECT_SCOPED'
    except Exception as ex:
        v['status']='STOPPED_SPECIAL_WILD_REPAIR';v['failure']={'type':type(ex).__name__,'message':str(ex)};raise
    finally:
        for p,binding in v['protected_bindings'].items():need(identity((ROOT/p).read_bytes())==binding,'protected source/acceptance changed '+p)
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v)


def owned():
    dest=ROOT/old.EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return {CP,GUIDE,old.STATE,old.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.rglob('*') if p.is_file()}


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record exact source')
    dest=ROOT/old.EVIDENCE/str(v['run_id']);need(not dest.exists(),'immutable evidence path');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_text();need('\0'not in text,'text evidence only')
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'no private paths');(dest/p.name).write_text(safe)
    v['public_evidence_bindings']={p.name:identity(p.read_bytes()) for p in dest.iterdir()};v['evidence_path']=dest.relative_to(ROOT).as_posix();write(ROOT/CP,v)
    nextstep='Issue19: 特殊野生の2 callsite限定修復と直接native対照を保存。次は変更後候補で通常釣竿/スキャナーUI→捕獲→通常Save/fresh Continue。直接call fixtureを通常取得へ読み替えない。元親/同じ特殊技診断/受入済み研究孵化15・配布17・旧野生・EXP・Bag・egg・旧ARM・Wikiは変更影響がない限り再実行しない。'
    if v['failure']:nextstep='Issue19: 特殊野生修復checkpointの失敗原本を先に読み、未成功caseのみ修正する。保存成功の親診断や対照を再実行しない。'+nextstep
    lines=['# PR16 Issue19: 釣り・隠し野生の特殊技順',f"\n状態 `{v['status']}`。run `{v['run_id']}` / source `{v['source_head']}`。",f"\n親候補 `{v['parent_candidate']['sha256']}`。後継 `{v['candidate']['sha256']}`。",'\n## 保存原本と修復境界','\n初回36152934075は研究表のないmap11/3で特殊技を観測できずfailure。通常個体8callは変更前後一致。原失敗CP/証拠は不変。13旧unitや同じ8callを再実行しない。','\n現候補の実入口はResearch Economyへ直接接続し、V4→QOLへ委譲する。旧Stage59ソースを現在の実到達経路へ読み替えない。846研究行と候補QOL blobの全table byte一致を要求し、実釣りheaderとの交差からfixtureを選ぶ。','\n修復は釣り0x09392722・隠し0x0939274Aの共通再初期化へのBLだけをNOP化。原候補2経路で実QOL特殊技第4枠が消えることを観測した後だけ生成する。共通initializer・land・戻り値・owner方針は変更しない。8byte限定差分、全ROM rollback、2独立replayを検査。','\n新開始map/進行flag/profile/RNGと入口レジスタはfixture。観測区間は7host書込み拒否下のCPU実行と読取のみ。通常釣竿/スキャナーUI、捕獲、Save/Continue、ストーリー到達は未受入。']
    for name,r in v['results'].items():lines.append(f"\n- {name}: {r['classification']}; species {r['before']['species']}; {r['before']['moves']} → {r['after']['moves']}; PP {r['before']['pp']} → {r['after']['pp']}; calls {r['calls']}。");
    lines.extend([f"\n新unit {v['new_unit_tests']}、host compile {v['host_compiles']}、native process {v['native_processes']}、ARM0。受入済み再実行0。後継作成 {v['rom_changes']}。Actions終端未確認。原本 `{v['evidence_path']}`。",f"\n失敗記録 `{v['failure']}` / case別 `{v['failures']}`。",'\n1281 identity-only/自動fallback禁止、Issue19全体未完、release_ready=false、PR未merge、active baseline不変。','\n## 次',nextstep])
    (ROOT/GUIDE).write_text('\n'.join(lines)+'\n')
    state=load(ROOT/old.STATE)
    state['learnset_special_wild_repair']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')}
    state['learnset_special_wild_repair'].update(path=CP,diagnostic_processes=v['native_processes'],gameplay_accepted=False)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='特殊野生2callsite後継の限定直接診断。通常取得/保存継続の受入ではない。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'in_progress','conclusion':None}],'predecessor':{'id':PARENT_RUN,'conclusion':'failure'},'reason_ja':'記録時点で現runのpush/upload終端は未確認。旧失敗原本は維持。'}
    state['bp']['current_stop']='Issue19: '+v['status']+'。特殊野生の通常取得/保存継続は未受入。';state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='SPECIAL_WILD_REPAIR_GAMEPLAY',goal_ja=nextstep,read_paths=[GUIDE,CP,SELF,TEST])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 特殊野生の実特殊技順と2callsite限定修復\n- Version: issue19-special-wild-repair-v1\n- Status: '+('DONE（限定直接nativeのみ）' if not v['failure'] else 'STOPPED（保存成功は保持、未成功だけ継続）')+f'\n- Summary: {v["status"]}。8byte限定修復、共通/land/旧原本は不変。元map11/3の8callは再実行せず保存正常対照を使用。Stage59は現候補経由でないと訂正。\n- Files changed: 専用repair driver/test/workflow/CP、guide、run別text証拠、固定引継ぎMD/JSON、両ログ。\n- Verify: 新unit {v["new_unit_tests"]}, host {v["host_compiles"]}, native {v["native_processes"]}, ARM0; 旧受入/旧13unit/旧ROM再build/Wiki再実行0。Actions終端未確認。通常操作/capture/Save未受入。\n- Commit: 同branchへの非force pushとreflected-head.txtにremote照合を保存。source {v["source_head"]}, run {v["run_id"]}。\n- Network: GitHub pinned artifact/Actionsのみ。merge/release/active baseline変更なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(note)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard();subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths');actions[sys.argv[1]]()
