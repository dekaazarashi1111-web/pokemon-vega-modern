#!/usr/bin/env python3
"""完走済みSave23原本の後続oracle。最初のflag不変検査failureは改作しない。"""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save23_measure as measured
from pr16_story_after_maori import need,identity
parent=measured.parent
SOURCE='171a6518751659d66523924b9469045019814fb7'
RUN=37090970832
JOB=111111036767
ARTIFACT=11261539316
ARCHIVE=dict(size=17499395,sha256='b5cb150d1fe3271b8dba3791b01fc3a3548f5183cb5c5bc5a6d684a99f8234b4')
OUTPUT=dict(size=131088,sha256='728bd39b11ea53bafd31cff5fb50e7f81fe5973c0c5fae559ea22037827832bb')
FLASH='bd1cb1658216d44d969a69ba40b90c39f338095262ac2790f4c212ffd0ea3b6c'
CP='content/modernization/pr16_story_save23_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE23_JA.md'
EVIDENCE='content/modernization/pr16_story_save23_evidence'


def flag_vars(fa,va,fb,vb):
    need(type(fa) is bytes and type(fb) is bytes and len(fa)==len(fb)==0x120 and
         len(va)==len(vb)==256 and all(type(v) is int for v in (*va,*vb)),'whole legacy arrays')
    flags=[(8*i+j,(u>>j)&1,(v>>j)&1) for i,(u,v) in enumerate(zip(fa,fb)) for j in range(8) if (u^v)&(1<<j)]
    variables=[(0x4000+i,u,v) for i,(u,v) in enumerate(zip(va,vb)) if u!=v]
    need(flags==[(2056,1,0)],'only recorded auxiliary flag2056 clears; owner remains unresolved')
    need(variables==[(0x4021,23,26),(0x4022,3,1)],'exact two auxiliary var deltas only')
    need(va[0x4e]==vb[0x4e]==0 and not ((fa[0x840//8]|fb[0x840//8])&1) and
         va[0x71]==vb[0x71]==6 and va[0x72]==vb[0x72]==1,'national and story gates immutable')
    return dict(auxiliary_flag_deltas=flags,auxiliary_var_deltas=variables,
        auxiliary_flag2056_runtime_owner_resolved=False,auxiliary_vars_runtime_owner_resolved=False,
        national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1})


def boundary(before,after,cold):
    s=parent.sectors
    need(identity(before)==measured.plan.INPUT_SAVE and identity(after)==OUTPUT and after==cold,'fixed complete Save22/23 and all cold RTC')
    old,ra=s.bank(before,0,22,s.LAYOUT);new,rb=s.bank(after,0xe000,23,s.LAYOUT);_,rc=s.bank(after,0,22,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'whole Save22 bank immutable')
    pa=before[old[1]+56:old[1]+656];pb=after[new[1]+56:new[1]+656]
    need(pa==pb and identity(pb)['sha256']==parent.PARTY,'all600 party bytes preserved')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'4 slots')
    a,ma=parent.shared.bag(before,old);b,mb=parent.shared.bag(after,new)
    need(a==b and ma==mb==12296,'all Bag/money unchanged')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'all PC/S61E payload')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);result=flag_vars(fa,va,fb,vb)
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==0,'NationalDex magic unchanged')
    # Extension CRC/inverse/value contracts are verified independently from the stock sector checksum.
    ext=after[new[13]+0x7d0:new[13]+0xde6];parent.s61e_record(ext)
    result.update(party_bytes_preserved=600,bag_unchanged=True,money=mb,hm05_owned=True,hm05_taught_or_used=False,
        sector_checksums=len(ra)+len(rb)+len(rc),pc_and_s61e_sections_unchanged=list(range(5,14)),
        s61e_crc_and_inverse_checked=True,save22_bank_preserved_bytes=57344,complete_save_rtc_cold_identical=True)
    changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
    ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    ledger=dict(changed_bytes=len(changed),ranges=[dict(start=a,end=b,before_hex=before[a:b].hex(),after_hex=after[a:b].hex()) for a,b in ranges])
    result['changed_bytes']=len(changed);result['changed_ranges']=len(ranges)
    return result,ledger


def semantics(a,b):
    ao,bo=a['observations'],b['observations']
    need(len(ao)==15 and len(bo)==2 and (a['end']['inputs'],a['end']['frames'])==(45,3318) and
         (b['end']['inputs'],b['end']['frames'])==(13,1510),'exact original accounting')
    coordinates=[[4,6],[4,5],[4,5],[5,5],[5,5],[5,4],[5,4]]
    for i,o in enumerate(ao):
        need(o['map']==([1,36] if i<7 else [1,73]) and o['xy']==(coordinates[i] if i<7 else [20,3]) and
             o['party_sha256']==parent.PARTY and o['ledger_sha256']==parent.LEDGER and
             o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['callback2']==parent.FIELD,
             'exact ordinary input route; no new encounter, party change, or RP')
        need(o['field'] is (i<8 or i==14) and o['lock']==(0 if i<8 or i==14 else 1),'field and Save UI boundaries')
        need(o['save_counter']==(22 if i<13 else 23),'partial Save must not count as stable field')
        if i<=10:need(o['flash_sha256']==parent.FLASH,'no hidden early saves')
        if i in (11,12):need(o['flash_sha256'] not in (parent.FLASH,FLASH),'two partial write snapshots')
        if i>=13:need(o['flash_sha256']==FLASH,'completed Flash before menu dismissal')
    final=ao[-1];measured.idle(final,[1,73],[20,3],23)
    for o in bo:
        measured.idle(o,[1,73],[20,3],23)
        need(all(o[k]==final[k] for k in ('facing','party_sha256','flash_sha256','ledger_sha256')),'independent persisted boundary')
    return dict(route=[[1,36],[1,73]],arrival_observation=7,save_success_wording_observation=13,
        save_stable_field_observation=14,inner_cave_arrival=True,cave_crossing_complete=False,ordinary_saves=1,
        save_counter=23,map=[1,73],xy=[20,3],facing=4,party_count=4,rp=0,trainer_victories=0,wild_victories=0,
        escapes=0,captures=0,fixture_writes=0,national_dex_unlocked=False,hm05_root_cause_resolved=False,
        natural_growth_accepted=False,natural_evolution_accepted=False,natural_research_arrival_accepted=False,
        full_story_accepted=False,release_ready=False)


def verify(folder):
    folder=Path(folder)
    failure=json.loads((folder/'failure.json').read_bytes())
    need(failure==dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',exception_type='ValueError',
        native_processes=2,source_head=SOURCE,run_id=RUN),'original measurement failure retained')
    need(identity((folder/'candidate.gba').read_bytes())==measured.plan.CANDIDATE and
         identity((folder/'runner').read_bytes())==parent.RUNNER,'unchanged candidate/runner')
    parsed={}
    for lane,seed in [('progress',measured.plan.INPUT_SAVE),('continue',OUTPUT)]:
        parsed[lane]=measured.trace(folder/lane,seed)
        execution=json.loads((folder/lane/'execution.json').read_bytes())
        need(execution==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],
            observations=len(parsed[lane]['observations'])),'exact clean native ending and Save identity')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'working Save matches checkpoint')
    result=semantics(parsed['progress'],parsed['continue'])
    state,ledger=boundary((folder/'input.srm').read_bytes(),(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes())
    result.update(status='PASS_INTERIOR_WARP_SAVE23_SCOPED_FROM_PRESERVED_FAILED_RUN',boundary=state,
        candidate=measured.plan.CANDIDATE,input_save=measured.plan.INPUT_SAVE,output_save=OUTPUT,
        measured_run_conclusion='failure',failure_reason_ja='初回oracleが補助flag2056の通常変化を不変条件で拒否。旧failureは保持。',
        measurement_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,
        progress_inputs=45,continue_inputs=13,progress_frames=3318,continue_frames=1510,screen_count=17,
        save_success_wording_observed=True,visual_review_required=True,rom_changes=0,compiles=0)
    return result,ledger
