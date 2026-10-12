#!/usr/bin/env python3
"""Circus選択個体のread-only限定追跡。初戦ターンや受入済み取消は再実行しない。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_circus_identity.py'
TEST='tests/test_pr16_circus_identity.py'
WORKFLOW='.github/workflows/pr16-circus-identity.yml'
CASE='circus-rental-identity'
OUT=ROOT/'.local/pr16-circus-identity'
SHA='99cc09484a9c6bd787fb4b0631970396b4ae5ec2abc902ea8fdec932130b6c0b'
PREFIX=b'CIRCUS_IDENTITY '
C=r'''
/* Host reads only; no emulated function calls, bus writes or register writes. */
static unsigned ci_events;
static uint8_t ci_previous[300];
static uint32_t ci_script,ci_callback,ci_bs;
static void ci_snapshot(struct mCore *c,const char *label){
    uint32_t pc=0,lr=0;
    bp_require(c,ci_events++<128U,"identity trace exceeded bounded event budget");
    bp_require(c,c->readRegister(c,"pc",&pc) && c->readRegister(c,"lr",&lr),"identity register read failed");
    fprintf(stderr,"CIRCUS_IDENTITY {\"label\":\"%s\",\"frame\":%u,\"script\":%u,\"callback2\":%u,\"newbs\":%u,\"flags\":%u,\"pc\":%u,\"lr\":%u,\"count\":%u,\"marker\":%u,\"snapshot\":%u,\"pending\":%u,\"battle_species\":%u,\"battle_index\":%u,\"order\":[",
      label,b_frames,read32(c,SP_SCRIPT_PTR),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read32(c,CF_FLAGS),pc,lr,read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,BP_F(marker)),read8(c,BP_F(snapshot_valid)),read8(c,BP_F(reward_pending)),read16(c,ADDR_BATTLE_MONS),read16(c,ADDR_BATTLER_PARTY_INDEXES));
    for(unsigned i=0;i<3U;++i)fprintf(stderr,"%s%u",i?",":"",read8(c,SP_ORDER_CFRU+i));
    fprintf(stderr,"],\"party\":[");
    for(unsigned i=0;i<6U;++i){
      uint32_t at=QOL_PLAYER_PARTY+i*100U;
      fprintf(stderr,"%s{\"personality\":%u,\"species\":%u,\"bytes\":\"",i?",":"",read32(c,at),read16(c,at+BATTLE_CORE_PARTY_SPECIES_OFFSET));
      for(unsigned j=0;j<100U;++j)fprintf(stderr,"%02x",read8(c,at+j));
      fprintf(stderr,"\"}");
    }
    fprintf(stderr,"]}\n");
    b_copy(c,QOL_PLAYER_PARTY,ci_previous,300U);
    ci_script=read32(c,SP_SCRIPT_PTR);ci_callback=read32(c,BATTLE_CORE_MAIN_CALLBACK2);ci_bs=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);
}
static void ci_tick(struct mCore *c){
    uint8_t current[300];b_copy(c,QOL_PLAYER_PARTY,current,300U);
    if(memcmp(current,ci_previous,300U) || ci_script!=read32(c,SP_SCRIPT_PTR)
       || ci_callback!=read32(c,BATTLE_CORE_MAIN_CALLBACK2) || ci_bs!=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER))ci_snapshot(c,"transition");
}
'''

def need(ok,message):
    if not ok:raise ValueError(message)

def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def strict(raw):
    def pairs(items):
        out={}
        for key,value in items:
            need(key not in out,'duplicate key');out[key]=value
        return out
    def bad(value):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def replace_once(text,before,after):
    need(text.count(before)==1,'instrumentation anchor is not unique: '+before[:48])
    return text.replace(before,after,1)

def instrument(text):
    text=replace_once(text,'static struct CFTrace ct;','static struct CFTrace ct;\n'+C)
    text=replace_once(text,'    bp_state(c,label);','    ci_snapshot(c,label);bp_state(c,label);')
    text=replace_once(text,'ct.selected=b_frames;b_press(c,QOL_KEY_A,120U);','ct.selected=b_frames;ci_snapshot(c,"first-confirm");b_press(c,QOL_KEY_A,120U);')
    anchor='        b_frame(c,f%90U==0U?QOL_KEY_A:0U);'
    need(text.count(anchor)==2,'bounded selection/launch frame loops changed')
    text=text.replace(anchor,anchor+'ci_tick(c);')
    start=text.index('    struct BPProgress turn=bp_progress(c);')
    end=text.index('    return flags;',start)
    text=text[:start]+text[end:]
    text=replace_once(text,'"circus-first-battle"','"'+CASE+'"')
    start=text.index('    printf("{\\"schema_version\\":1')
    end=text.index('    return 0;',start)
    text=text[:start]+r'''    printf("{\"schema_version\":1,\"status\":\"PASS_CIRCUS_IDENTITY_OBSERVATION\",\"case\":\"circus-rental-identity\",\"candidate_sha256\":\"%s\",\"fresh_cores\":1,\"frames\":%u,\"first_turn_replayed\":false,\"physical_admission_accepted\":false,\"release_ready\":false}\n",hash,b_frames);
'''+text[end:]
    # Saved/snapshot lifecycle variables remain used in the preserved cancel code.
    text=text.replace('unsigned counter=read32(c,P03_SAVE_COUNTER),flags=0U;','unsigned counter=read32(c,P03_SAVE_COUNTER);')
    text=text.replace('if(battle)flags=cf_battle(c);','if(battle)(void)cf_battle(c);')
    text=text.replace('    unsigned final_counter=read32(c,P03_SAVE_COUNTER);\n','')
    return text

def parse_events(stderr):
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'native warnings')
    rows=[strict(line[len(PREFIX):]) for line in stderr.splitlines() if line.startswith(PREFIX)]
    need(4<=len(rows)<=128,'bounded identity trace missing')
    fields={'label','frame','script','callback2','newbs','flags','pc','lr','count','marker','snapshot','pending','battle_species','battle_index','order','party'}
    last=-1
    for row in rows:
        need(type(row) is dict and set(row)==fields,'identity event schema')
        need(type(row['label']) is str and re.fullmatch(r'[a-z0-9-]+',row['label']),'identity label')
        for key in fields-{'label','order','party'}:need(type(row[key]) is int and 0<=row[key]<=0xffffffff,'identity integer')
        need(last<=row['frame']<=120000 and row['count']<=6,'identity event order/range');last=row['frame']
        need(type(row['order']) is list and len(row['order'])==3 and all(type(v) is int and 0<=v<=6 for v in row['order']),'selection order')
        need(type(row['party']) is list and len(row['party'])==6,'six raw party slots required')
        for mon in row['party']:
            need(type(mon) is dict and set(mon)=={'personality','species','bytes'},'individual schema')
            need(type(mon['bytes']) is str and re.fullmatch('[0-9a-f]{200}',mon['bytes']),'100-byte raw individual')
            raw=bytes.fromhex(mon['bytes'])
            need(type(mon['personality']) is int and mon['personality']==int.from_bytes(raw[:4],'little'),'PID/raw disagreement')
            need(type(mon['species']) is int and mon['species']==int.from_bytes(raw[32:34],'little'),'species/raw disagreement')
    return rows

def analyze(rows):
    def only(label):
        found=[r for r in rows if r['label']==label];need(len(found)==1,'ambiguous stage: '+label);return found[0]
    first,second,action=(only(k) for k in ('first-confirm','circus-second-confirm','circus-action'))
    need(first['frame']<second['frame']<action['frame'],'selection/action order')
    need(first['count']==6 and second['count']==action['count']==3,'selection counts')
    order=first['order'];need(len(set(order))==3 and all(1<=x<=6 for x in order),'first selection slots')
    selected=[first['party'][i-1] for i in order]
    key=lambda mon:(mon['personality'],mon['species'])
    ids=lambda mons:[key(mon) for mon in mons]
    chosen_to_second=ids(selected)==ids(second['party'][:3])
    second_to_action=ids(second['party'][:3])==ids(action['party'][:3])
    transitions=[r for r in rows if second['frame']<r['frame']<=action['frame']]
    changed=next((r for r in transitions if ids(r['party'][:3])!=ids(second['party'][:3])),None)
    need(action['newbs']>=0x02000000 and 0<=action['battle_index']<3,'battle allocation/index')
    need(action['battle_species']==action['party'][action['battle_index']]['species'],'battle/party species disagreement')
    return dict(schema_version=1,classification=('CIRCUS_RENTALS_CHANGED_BEFORE_SECOND_CHOOSER' if not chosen_to_second else ('CIRCUS_RENTALS_REPLACED_AT_BATTLE_INIT' if not second_to_action else 'CIRCUS_RENTAL_IDENTITY_RETAINED')),
        selected_to_second_identity_equal=chosen_to_second,second_to_action_identity_equal=second_to_action,
        selected_to_second_all_300_bytes_equal=selected==second['party'][:3],second_to_action_all_300_bytes_equal=second['party'][:3]==action['party'][:3],
        first=first,second=second,action=action,first_changed_event=changed,event_count=len(rows),
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,first_turn_replayed=False)

def validate(stdout,stderr,code,case):
    need(type(code) is int and code==0 and case==CASE,'identity process failed')
    row=strict(stdout)
    expected=dict(schema_version=1,status='PASS_CIRCUS_IDENTITY_OBSERVATION',case=CASE,candidate_sha256=SHA,fresh_cores=1,
                  first_turn_replayed=False,physical_admission_accepted=False,release_ready=False)
    need(type(row) is dict and set(row)==set(expected)|{'frames'},'identity result schema')
    for k,v in expected.items():need(type(row[k]) is type(v) and row[k]==v,'identity result contract')
    events=parse_events(stderr);analysis=analyze(events)
    need(type(row['frames']) is int and row['frames']==analysis['action']['frame'],'observation stop differs')
    return row

def run():
    sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
    import pr16_circus_native as native
    base=(ROOT/native.SOURCE).read_text()
    # Exact original source is additionally bound by the accepted native checkpoint.
    checkpoint=strict((ROOT/'content/modernization/pr16_circus_first_battle_checkpoint.json').read_bytes())
    need(identity(base.encode())==checkpoint['original_sources'][native.SOURCE],'accepted native source changed')
    source=ROOT/'.local/pr16-circus-identity-input.c';source.parent.mkdir(exist_ok=True)
    source.write_text(instrument(base))
    native.SELF,native.SOURCE,native.TEST,native.WORKFLOW=SELF,source.relative_to(ROOT).as_posix(),TEST,WORKFLOW
    native.OUT=OUT;native.requested_cases=lambda:(CASE,);native.validate=validate
    result=native.run()
    need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE' and result['actual_new_processes']==1 and len(result['guard_checks'])==7,'limited native observation failed')
    raw=(OUT/(CASE+'.stderr')).read_bytes();events=parse_events(raw);analysis=analyze(events)
    analysis.update(candidate=result['candidate'],tested_head=result['source_head'],run_id=int(os.environ.get('GITHUB_RUN_ID','0')),
                    native_processes=1,fresh_cores=1,host_write_barriers=7,raw_stderr=identity(raw),
                    original_first_turn_run_reused=35367721416,accepted_native_cases_replayed=0)
    (OUT/'identity.json').write_bytes(stable(analysis));(OUT/'events.json').write_bytes(stable(events))
    print(json.dumps({k:analysis[k] for k in ('classification','selected_to_second_identity_equal','second_to_action_identity_equal','event_count')},ensure_ascii=False))
    return analysis

if __name__=='__main__':run()
