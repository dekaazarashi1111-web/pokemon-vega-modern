#!/usr/bin/env python3
"""通常Stage72 Entryのr12退避→r3復元を命令境界で観測。ROM/入力は不変。"""
from __future__ import annotations
import copy
import os
from pathlib import Path
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_p08_ordinary_representative as m
import pr16_p08_checkpoint as cp
import pr16_p08_ring_recovery as e
need=e.need
TASK='USER-20260920-P08-ORDINARY-ABI'
SELF='scripts/pr16_p08_ordinary_abi.py'
HEADER='tools/mgba_pr16_p08_ordinary_abi.h'
TEST='tests/test_pr16_p08_ordinary_abi.py'
WORKFLOW='.github/workflows/pr16-p08-ordinary-abi.yml'
FILES=(SELF,HEADER,TEST,WORKFLOW)
BASE='3c71b1a276811b45fe0844bb6f05f14cfe9283b2'
REPORT='content/modernization/pr16_p08_ordinary_abi.json'
OLD_REPORT=m.REPORT
OUT=m.OUT
RUN=35512429611
JOB=106082548688
HEAD='304eb25919601ccd7534dfd6e1da1dd5be091019'
ARTIFACT=10605663618
ARCHIVE=dict(size=67051,sha256='afe36570cf4beefe7dd7db5b88dfc0d6fbdea1e82ab86300e7dec2866cd1fdd9')
ADAPT=m.adapt
PHYSICAL=m.physical
contract=m.contract
COMMON=m.COMMON
PRED=m.PRED
DISP=m.DISP|{'entry_r12','restored_pc'}
DYNAMIC=m.DYNAMIC
expected=m.expected


def once(text,before,after):
    need(text.count(before)==1,'ordinary ABI source anchor');return text.replace(before,after,1)


def adapt(files):
    result=ADAPT(files)
    text=(ROOT/m.HEADER).read_text()
    text=once(text,'#include "mgba_pr16_p08_ordinary_observer.h"','#include "mgba_pr16_p08_ordinary_abi.h"')
    text=once(text,'flags==0U && !read32(c,CF_FLAGS)','(flags & ~4U)==0U && !read32(c,CF_FLAGS)')
    result['controller.c']=once(result['controller.c'].decode(),'#include "mgba_pr16_p08_ordinary_main.h"',text).encode()
    return result


def physical(raw,generated):
    oracle,header=PHYSICAL(raw,generated)
    proof={}
    for row in oracle['routes']:
        if row['preserve_r3']:
            at=row['normal']-0x08000000
            need(raw[at:at+2]==b'\x63\x46','Stage72 Entry is not mov r3,r12')
            proof[row['name']]=dict(entry=row['normal'],restore_instruction='6346',restored_pc=row['normal']+2)
    need(len(proof)==7,'Stage72 r12 entry count');oracle['normal_entry_abi']=proof
    return oracle,header

def calls_proof(values,routes):
    lookup={r['name']:r for r in routes};pred=[];dispatch=[]
    need(len(lookup)==29,'route inventory')
    for row in values:
        is_pred=row.get('kind')=='predicate';need(row.get('kind') in ('predicate','dispatch'),'unknown call kind')
        need(set(row)==COMMON|(PRED if is_pred else DISP),'ordinary call schema')
        integers=COMMON-{'kind','pcs'}|(PRED if is_pred else DISP-{'name','preserve_r3'})
        need(all(type(row[k]) is int for k in integers),'ordinary call integer types')
        need(row['flags']==row['host_writes']==row['host_calls']==0 and row['types'] in (0,4),'suppression or injected ordinary call')
        pcs=row['pcs'];need(type(pcs) is list and 2<=len(pcs)<=128
            and all(type(pc) is int and 0x08000000<=pc<0x0a000000 for pc in pcs),'ordinary PC chain')
        if is_pred:
            need(pcs[0]==0x090D7BB0 and pcs[-1]==row['return_pc'] and row['bank'] in (0,1)
                 and 0<row['raw_ability']<=1024 and row['result']==0,'ordinary suppression predicate')
            pred.append(row)
        else:
            need(row['name'] in lookup,'unknown dispatcher');r=lookup[row['name']]
            need(type(row['preserve_r3']) is bool and row['preserve_r3']==bool(r['preserve_r3'])
                 and row['root']==pcs[0]==r['root'] and row['delegate']==row['expected_normal']==r['normal']
                 and row['restored_pc']==pcs[-1]==r['normal']+(2 if row['preserve_r3'] else 0),
                 'not the actual normal dispatcher')
            need(r['target'] in pcs and r['normal'] in pcs and (not row['preserve_r3'] or
                 (row['entry_r12']==row['r3_before']==row['r3_after'] and pcs[-2]==r['normal'])),'dispatcher/4th argument')
            dispatch.append(row)
    need(1<=len(pred)<=8 and 1<=len(dispatch)<=40,'missing or excessive ordinary calls')
    return dict(predicate_returns=len(pred),normal_dispatches=len(dispatch),
                hook_names=sorted({x['name'] for x in dispatch}),natural_normal_calls_verified=True)


def validate(stdout,stderr,proc,oracle,original_event):
    need(type(proc['returncode']) is int and proc['returncode']==0 and proc['timed_out'] is False
         and proc['spawn_error'] is None and b'mGBA[' not in stderr,'ordinary native process')
    row=e.strict(stdout);fixed=expected();need(set(row)==set(fixed)|DYNAMIC,'ordinary result schema')
    for key,want in fixed.items():need(type(row[key]) is type(want) and row[key]==want,'ordinary result: '+key)
    need(all(type(row[k]) is int for k in DYNAMIC),'ordinary integer schema')
    need(0<row['continued_frame']<row['boundary_frame']<row['encounter_frame']<row['returned_frame']==row['total_frames']<=100000,'ordinary frame order')
    need(1<=row['trace_frames']<=600 and 0<row['trace_instructions']<1200000000
         and 1<=row['walking_steps']<=400 and row['species']==4 and 0<row['ability']<=1024
         and 1<=row['enemy_species']<=2048 and 1<=row['enemy_level']<=100 and row['outcome'] in (1,2,4),'ordinary battle bounds')
    calls=contract.rows(stderr,b'P08_ORDINARY_CALL ');proof=calls_proof(calls,oracle['routes'])
    need(proof['predicate_returns']==row['predicate_returns'] and proof['normal_dispatches']==row['normal_dispatches']
         and all(row['boundary_frame']<x['frame']<=row['returned_frame'] for x in calls),'ordinary call projection')
    need(not contract.rows(stderr,b'CIRCUS_SUPPRESSION_DRAW ') and not contract.rows(stderr,b'CIRCUS_GETTER_ABI '),'old facility work repeated')
    events=contract.rows(stderr,b'CIRCUS_CONTINUOUS ')
    need([x['label'] for x in events]==['p08-exit30','p08-town-boundary','p08-normal-action','p08-normal-return'],'ordinary event sequence')
    before=events[0]
    for key in ('party','owner','factory','bp','count','save_counter','pending','snapshot','marker','flags','newbs','types'):
        need(type(before[key]) is type(original_event[key]) and before[key]==original_event[key],'genuine exit state: '+key)
    for event,frame in zip(events,(row['continued_frame'],row['boundary_frame'],row['encounter_frame'],row['returned_frame'])):
        need(event['frame']==frame and event['owner']==before['owner'] and event['factory']==before['factory']
             and event['bp']==90 and event['save_counter']==3 and event['count']==1 and event['battle']==30
             and not any(event[k] for k in ('flags','pending','snapshot','marker')) and not event['types']&0x04000000,'ordinary leaked owner/ledger')
        need(bytes.fromhex(event['party'])[:8]==bytes.fromhex(before['party'])[:8],'original individual lost')
    need(events[2]['types'] in (0,4) and events[2]['newbs'] and events[-1]['newbs']==0,'ordinary allocation/return')
    need(events[-1]['outcome']==row['outcome'],'ordinary outcome projection')
    return row,dict(calls=proof,events=events,normal_entry_abi=oracle['normal_entry_abi'])



def prefix_proof(previous,current):
    prefix,found,_=previous.partition(b'P08_ORDINARY_CALL ')
    need(found and current.startswith(prefix),'ordinary input/state prefix changed')
    old=contract.rows(previous,b'P08_ORDINARY_CALL ')
    new=contract.rows(current,b'P08_ORDINARY_CALL ')
    need(len(old)==1 and new and old[0]['name']==new[0]['name']=='AbilityBattleEffects'
         and old[0]['frame']==new[0]['frame']==4989 and old[0]['r3_before']==new[0]['r3_before']==65535,
         'first normal call boundary differs')
    return dict(exact_prefix=e.identity(prefix),frame=4989,original_failed_before_restore=True,
        corrected_observation_after_native_restore=True,input_changes=0,rom_changes=0,accepted_standalone_replays=0)


def validate_with_prefix(stdout,stderr,proc,oracle,original):
    row,proof=validate(stdout,stderr,proc,oracle,original)
    proof['previous_prefix']=prefix_proof((OUT/'previous.stderr').read_bytes(),stderr)
    return row,proof


def configure():
    m.REPORT=REPORT;m.FILES=(*FILES,*m.FILES);m.TASK=TASK;m.OBSERVER=HEADER
    m.adapt=adapt;m.physical=physical;m.validate=validate_with_prefix


def prepare():
    b=cp.b;b.OUT=OUT;head=b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted')
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'unreviewed source delta')
    run=b.api('actions/runs/'+str(RUN));job=b.api('actions/jobs/'+str(JOB));art=b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure','previous run')
    need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='failure','previous job')
    need(not art['expired'] and art['workflow_run']['id']==RUN and art['digest']=='sha256:'+ARCHIVE['sha256'],'previous artifact')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    members=e.archive_members(raw,ARCHIVE);old=e.strict(members['native-result.json'])
    need(old['candidate']==m.TARGET and old['new_emulator_processes']==1 and old['native_verified'] is False
         and old['failures']==[dict(type='ValueError',message='ordinary native process')],'previous failure scope')
    previous=members['execution/'+m.CASE+'.stderr']
    need(previous.endswith(b'P03 archive: natural Stage77 delegate or r3 differs\n')
         and members['execution/'+m.CASE+'.stdout']==b'','previous failure boundary')
    (OUT/'previous.stderr').write_bytes(previous)
    for path,meta in {**old['source_bindings'],**old['protected_originals']}.items():
        need(e.identity((ROOT/path).read_bytes())==meta,'protected previous source')
    original=m.sources(b)
    _,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'ordinary-abi-tests')
    need(b.exited(proc)==0 and b'\nOK\n' in err,'new ABI contracts')
    value=copy.deepcopy(old)
    for key in ('process','generated','transitive_compiled_sources','oracle','cache'):value.pop(key,None)
    value.update(task=TASK,source_head=head,workflow_source_head=os.environ['GITHUB_SHA'],original=original,
        previous_trial=dict(run_id=RUN,job_id=JOB,head_sha=HEAD,artifact_id=ARTIFACT,archive=ARCHIVE,
            conclusion='failure',classification='OBSERVER_COMPARED_BEFORE_STAGE72_RESTORE',new_processes=1,
            observed_fresh_cores=1,accepted=False,report=OLD_REPORT),
        source_bindings={p:e.identity((ROOT/p).read_bytes()) for p in m.FILES},
        new_emulator_processes=0,host_compiles=0,fresh_cores=0,failures=[],screens={})
    value['protected_originals'][OLD_REPORT]=e.identity((ROOT/OLD_REPORT).read_bytes())
    (OUT/'native-result.json').write_bytes(e.stable(value));m.checkpoint(value,'START')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');configure()
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='native':m.native()
    elif sys.argv[1]=='finish':m.checkpoint(e.strict((OUT/'native-result.json').read_bytes()),'FINISH')
    elif sys.argv[1]=='pack':cp.pack(OUT,m.FILES)
    elif sys.argv[1]=='result':sys.exit(0 if e.strict((OUT/'native-result.json').read_bytes())['native_verified'] else 1)
    else:raise ValueError('unknown command')
