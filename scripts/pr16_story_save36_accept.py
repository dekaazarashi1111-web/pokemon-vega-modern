#!/usr/bin/env python3
"""Save36の戻り転送・野生勝利・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save36_measure as m
from pr16_story_after_maori import need,identity
SOURCE='f4bc5af88aa4dec1e3fc2ccf34ff889d05df367f'
RUN,JOB,ARTIFACT=37125324369,111209348108,11274556304
ARCHIVE=dict(size=652970,sha256='807acebca23ef3ddfa4423b22ab015b30a1de81a4e50ded26416e42e003ad058')
OUTPUT=dict(size=131088,sha256='572b1816442da3ace4442b53167c59ae4e61aece80010a7bc17f291d8992f12c')
PARTY='ab2d5080e949385ad2880a3ab7f26222492b163f955fc30cbecebd0fd3b308c1'
FLASH='4d36caae13a47e8425d51ec58d69ed90525f28b639b8ebc8953d6a0ca725ee2a'
CP='content/modernization/pr16_story_save36_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE36_JA.md'
EVIDENCE='content/modernization/pr16_story_save36_evidence'
VISUAL='content/modernization/pr16_story_save36_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent

from pr16_story_save21_accept import load,integer,digest,commands,screen_bytes,BOOT,OBS_INTS,OBS_HASH,OBS_KEYS,END_KEYS
CANDIDATE=shared.plan.CANDIDATE
PARTIES=[m.a.PARTY,'c7e35884ddb35d63bc3f9c5230866816849ec270b436588b17cdd3dd74d57740','31594d29eb8d9b70d2e4cdfac6181d3f2b84bc107762af9cc41acec68411a0b0','2c53a2c0b809de119b7434a56cd01ccf045ff702ddd2493812a26e5b68b7a890',PARTY]
LEDGERS=[m.a.LEDGER,'431dae1aaabc03f63e392a39c87b6e6721836f6850ccf7ff48a81d78a529b82d','d4f0763809d464399028af05e90b70a143741c21948d3a3f48e5698ab6ded06a','6eff86924495aff9e8a3ab78f76a38244ae1d42a517ca6327166bf31aa620fda','f53f58f9f56b69943d14f92b8df3623be493d809276b0860da6d461fa3edc2f4']
def motion(n):
    start=[[16,5],[16,5],[16,4],[16,4],[15,4],[14,4],[13,4],[13,4],[13,5],[13,6],[13,6],[12,6],[11,6],[10,6],[9,6],[8,6],[8,6],[8,5],[8,5]]
    if n<19:xy=start[n];live=[v+7 for v in xy]
    elif n==19:xy,live=[7,10],[14,12]
    elif n<35:xy,live=[4,13],[14,12]
    elif n<42:xy,live=[4,13],[12,18]
    elif n==42:xy,live=[2,14],[13,20]
    elif n<82:xy,live=[6,14],[13,20]
    elif n==82:xy,live=[2,14],[13,20]
    elif n==83:xy,live=[4,14],[13,20]
    elif 89<=n<=91:xy,live=[6,16],[13,20]
    else:xy,live=[6,13],[13,20]
    face=2 if n in(1,2,16,17)else 1 if 7<=n<=9 or 35<=n<=83 or n>=89 else 3
    return xy,live,face

def coordinate_boundary(o,seed):
    if o['live_xy']==[v+7 for v in o['xy']]:return
    n=o['observe'];need(seed==m.a.OUTPUT and type(n)is int and(19<=n<=83 or 89<=n<=91),'Save35親の今回eventだけ')
    xy,live,face=motion(n)
    need(o['xy']==xy and o['live_xy']==live and o['facing']==face and o['map']==[1,73] and o['lock']==1 and o['field']is False and o['save_counter']==35 and o['party_count']==4 and o['rp']==0 and o['flash_sha256']==m.a.FLASH and o['callback2']==(m.m.BATTLE if 45<=n<=80 else m.m.FIELD),'event中の座標差を一般化せず、操作可能fieldへ昇格しない')
def trace_rows(raw, command, seed):
    """保存helperを使わず入力↔JSONLを一対一照合。旧field判定を書換えない。"""
    need(type(seed) is dict and set(seed) == {'size','sha256'} and type(seed['size']) is int and seed['size'] == 131088 and digest(seed['sha256']) and type(raw) is bytes and 0 < len(raw) < 400000 and raw.endswith(b'\n'), '原本/種別')
    lines = commands(command)
    rows = [load(x) for x in raw.splitlines()]
    need(all(type(r) is dict for r in rows) and len(rows) >= 16, '行object/schema')
    start = rows[0]
    expected_seed = seed
    need(set(start) == {'begin','candidate_sha256','initial_save_sha256','host_write_barriers'} and
         start['begin'] == 'INDEPENDENT_CONTINUE' and start['candidate_sha256'] == CANDIDATE['sha256'] and
         start['initial_save_sha256'] == expected_seed['sha256'] and
         type(start['host_write_barriers']) is int and start['host_write_barriers'] == 7, '開始境界')
    cursor, frame, input_count = 1, 0, 0
    observations, screens = [], []

    def take_key(key, frames):
        nonlocal cursor, frame, input_count
        need(cursor < len(rows), '入力行欠落')
        r = rows[cursor]
        need(set(r) == {'input','frame','key','frames'} and all(integer(v) for v in r.values()) and
             r == dict(input=input_count, frame=frame, key=key, frames=frames), '実入力/frame原本不一致')
        frame += frames; input_count += 1; cursor += 1
        need(frame <= 1800000, 'frame上限')

    def take_observe(n):
        nonlocal cursor
        need(cursor+1 < len(rows), '画面対欠落')
        r,screen = rows[cursor:cursor+2]
        need(set(r) == OBS_KEYS and all(integer(r[k], high=0xffffffff) for k in OBS_INTS) and
             all(digest(r[k]) for k in OBS_HASH) and type(r['field']) is bool, '観測schema')
        for k in ('map','xy','live_xy'):
            need(type(r[k]) is list and len(r[k]) == 2 and all(integer(v,high=65535) for v in r[k]), '座標schema')
        need(r['observe'] == n and r['frame'] == frame and r['lock'] in (0,1) and r['party_count'] <= 6,
             '観測frame/lock/party')
        coordinate_boundary(r,seed)
        need(set(screen) == {'screen','frame','sha256'} and type(screen['screen']) is int and
             type(screen['frame']) is int and screen['screen'] == n and screen['frame'] == frame and
             digest(screen['sha256']), '画面と観測の同frame')
        observations.append(r); screens.append(screen); cursor += 2

    for k,f in BOOT:
        take_key(k,f)
    take_observe(0)
    for line in lines[:-1]:
        p = line.split()
        if p[0] == 'key':
            take_key(int(p[1]),int(p[2]))
        else:
            take_observe(int(p[1]))
    need(cursor == len(rows)-1, '余剰行/隠し保存')
    end = rows[cursor]
    need(set(end) == END_KEYS and end['end'] == 'STORY_INPUT_CHECKPOINT' and
         all(integer(end[k]) for k in END_KEYS-{'end','natural_research_arrival_accepted'}) and
         end['frames'] == frame and end['inputs'] == input_count and end['host_write_barriers'] == 7 and
         end['warnings_errors'] == end['guarded_host_writes'] == end['fixture_calls'] == 0 and
         end['natural_research_arrival_accepted'] is False, '終端/書込禁止/過大受入')
    return dict(start=start, observations=observations, screens=screens, end=end)



def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=True)
    return parsed

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==112 and len(bo)==2,'全114画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(227,16653)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    for i,o in enumerate(ao):
        xy,live,face=motion(i);pi=0 if i<52 else 1 if i<60 else 2 if i<67 else 3 if i<76 else 4
        li=0 if i<27 else 1 if i<47 else 2 if i<68 else 3 if i<88 else 4
        field=i<19 or i in(92,111)
        need(o['xy']==xy and o['live_xy']==live and o['facing']==face and o['map']==[1,73],'全live移動/保存座標/camera区別')
        need(o['callback2']==(m.m.BATTLE if 45<=i<=80 else m.m.FIELD)and o['lock']==(0 if field else 1)and o['field']is field,'script/戦闘/field/保存の全境界')
        need(o['party_count']==4 and o['rp']==0 and o['party_sha256']==PARTIES[pi]and o['ledger_sha256']==LEDGERS[li],'全party/ledger推移・RP稼得0')
        need(o['battle_flags']==(0 if i<45 else 12)and o['battle_outcome']==(0 if i<78 else 1),'trainer1勝のみ')
        need(o['save_counter']==(35 if i<107 else 36),'Save36世代境界')
        if i<96:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<107:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'途中Flash11状態')
        else:need(o['flash_sha256']==FLASH,'Save36全Flash')
    need(len({ao[i]['flash_sha256']for i in range(96,107)})==11,'部分writeの別11状態')
    for o in bo:
        m.m.idle(o,36);need(o['xy']==[6,13]and o['facing']==1 and o['field']is True and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGERS[-1]and o['battle_flags']==o['battle_outcome']==0,'独立Continue全状態')
    return dict(status='PASS_CAVE_TRAINER360_EVENT_SAVE36_SCOPED',trainer_victories=1,trainer_id=360,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=36,map=[1,73],xy=[6,13],facing=1,party_count=4,rp=0,west_stair_accepted=True,dynamic8_5_native_arrival=True,trainer360_accepted=True,story_event_completed=True,move_selections=4,actual_pp_consumed=5,opponent_pressure_observation=73,save_success_text_observation=108,save_success_wording_observed=True,full_flash_observation=107,stable_field_observation=111,partial_write_observations=list(range(96,107)),progress_inputs=227,continue_inputs=13,screen_count=114,native_processes=2,prior_failed_native_processes=1,total_development_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,original_measurement_conclusion='failure',original_failure_is_post_save_trace_only=True,hm05_taught_or_used=False,trainer352_accepted=False,cave_crossing_complete=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'唯一のSave35親/Save36と全SaveRTC cold');need(identity(rom)==CANDIDATE,'同一候補')
    old,ra=s.bank(before,0xe000,35,s.LAYOUT);new,rb=s.bank(after,0,36,s.LAYOUT);_,rc=s.bank(after,0xe000,35,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧bank57344byte不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    need([(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v]==[(53,13,8)]and identity(y)['sha256']==PARTY,'party600byteははどうだんPP5だけ・HP320維持')
    for pp,expected in zip((12,11,10,8),PARTIES[1:]):
        modeled=bytearray(x);modeled[53]=pp;need(identity(bytes(modeled))['sha256']==expected,'中間party全byteモデル')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ba,ma=parent.shared.bag(before,old);bb,mb=parent.shared.bag(after,new);need(ba==bb and(ma,mb)==(13128,13576),'Bag/HM05不変・通常賞金448円')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全section不変')
    x13=before[old[13]:old[13]+0xff4];y13=after[new[13]:new[13]+0xff4]
    need(x13[:0x7d0]==y13[:0x7d0]and x13[0xde6:]==y13[0xde6:],'PC/tail不変')
    ea=parent.s61e_record(x13[0x7d0:0xde6]);eb=parent.s61e_record(y13[0x7d0:0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,0,3)],'正規eventの拡張flag4368/4369だけ・S61E CRC')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new)
    fd=[(i*8+bit,(u>>bit)&1,(v>>bit)&1)for i,(u,v)in enumerate(zip(fa,fb))for bit in range(8)if(u^v)&(1<<bit)];vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v]
    need(fd==[(1640,0,1)]and vd==[(0x4021,7,19),(0x4071,7,8)],'trainer360/正規story8/歩数補助varだけ')
    graph=json.loads((ROOT/m.TERRAIN).read_bytes())['coord7_5_graph']
    need(graph['visited_script_count']==6 and not graph['diagnostics']and[r['value']for r in graph['references']if r['category']=='trainer'and r['access']=='battle']==[360],'保存済6node event ownerだけ継承')
    need([r['operand']for r in graph['references']if r['category']=='var'and r['value']==0x4071 and r['access']=='write']==[8],'var4071=8 owner')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x72]==vb[0x72]==1,'全国図鑑まだ未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and ranges[-1][1]==i:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6990,1798),'全Save差分会計')
    return dict(party_changes=[[53,13,8]],pp=[1,8,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=ma,money_after=mb,reward=448,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={'4367':1,'4368':1,'4369':1},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':8,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),trainer_owner_saved_graph_reused=True)

def verify(folder,before,rom):
    folder=Path(folder);failure=json.loads((folder/'failure.json').read_bytes())
    need(failure==dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',type='ValueError',message='今回の7枚だけ',native_processes=2,source_head=SOURCE,run_id=RUN)and not(folder/'measurement.json').exists(),'保存後trace拒否の旧failureを保持')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両native原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    for i in(51,59,66,75):need(m.m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',1),'はどうだんslot1を4回だけ選択')
    for i in(56,63,70):need(m.m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('shift',None),'交代拒否3回')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=CANDIDATE);return result
