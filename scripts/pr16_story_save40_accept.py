#!/usr/bin/env python3
"""Save40の504正規event・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save40_measure as m
from pr16_story_after_maori import need,identity
SOURCE='c51b505a4541b91951d660aea6cf1d931a06b490'
RUN,JOB,ARTIFACT=37129549744,111221756160,11276815366
ARCHIVE=dict(size=591258,sha256='5f7bb21e21652641f23df582c33731c98f7d66557add3c99e5078a55e46257ee')
OUTPUT=dict(size=131088,sha256='cf8fc894e9542afbfa411db72f26411bec5dae3220bc8f8104cf71bfc109add1')
PARTY=m.a.PARTY
FLASH='132c15c9a539381beaece52667a5201737ffe1dd84e2c13463a806622d1afa7f'
CP='content/modernization/pr16_story_save40_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE40_JA.md'
EVIDENCE='content/modernization/pr16_story_save40_evidence'
VISUAL='content/modernization/pr16_story_save40_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
from pr16_story_save21_accept import load,integer,digest,commands,screen_bytes,BOOT,OBS_INTS,OBS_HASH,OBS_KEYS,END_KEYS
CANDIDATE=shared.plan.CANDIDATE
LEDGERS=['95d109f9df4c120c3343661ca2c130f17047761f4ef8a01bc4b9e05456073a26','8d9929bc88d9ea0adcd06aff00a88aafbe57a707af12fb94fd4cc065c521f41d']
LEDGER=LEDGERS[-1]
def motion(n):
    points=[[71,9],[71,9],[71,10],[71,10]]+[[x,10]for x in range(70,62,-1)]+[[63,10]]+[[63,y]for y in range(9,3,-1)]+[[63,4],[62,4],[61,4],[61,4]]+[[61,y]for y in range(5,11)]+[[61,10]]
    if n<30:xy=points[n];live=[v+7 for v in xy]
    elif n==30:xy,live=[57,8],[67,17]
    elif n in(31,32,45):xy,live=[48,8],[67,17]
    elif 33<=n<=44:xy,live=[48,10],[67,17]
    elif 46<=n<=51:xy,live=[48,6],[67,17]
    elif n in(52,53,54,55):xy,live={52:[50,16],53:[50,13],54:[44,12],55:[45,10]}[n],[67,17]
    else:xy,live=[60,10],[67,17]
    face=1 if n in(1,2)or 22<=n<=28 else 2 if 12<=n<=18 else 3
    return xy,live,face

def coordinate_boundary(o,seed):
    if o['live_xy']==[v+7 for v in o['xy']]:return
    n=o['observe'];need(seed==m.a.OUTPUT and type(n)is int and 30<=n<=55,'Save39親の504eventカメラだけ')
    xy,live,face=motion(n)
    need(o['xy']==xy and o['live_xy']==live and o['facing']==face and o['map']==[3,44]and o['lock']==1 and o['field']is False and o['save_counter']==39 and o['party_count']==4 and o['rp']==0 and o['flash_sha256']==m.a.FLASH and o['callback2']==m.m.FIELD,'event中のカメラ座標差だけを限定許容・field移動へ昇格しない')
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
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==81 and len(bo)==2,'全83画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(156,8738)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    for i,o in enumerate(ao):
        xy,live,face=motion(i);field=i<30 or i in(56,80)
        need(o['map']==[3,44]and o['xy']==xy and o['live_xy']==live and o['facing']==face,'全通常移動/カメラ座標/復帰を区別')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if field else 1)and o['field']is field,'event/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGERS[0 if i<41 else 1],'全party不変/戦闘0/ledger推移')
        need(o['save_counter']==(39 if i<75 else 40),'counter40だけ')
        if i<64:need(o['flash_sha256']==m.a.FLASH,'Save前Flash全byte不変')
        elif i<76:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'64〜75は未完の部分write')
        else:need(o['flash_sha256']==FLASH,'76成功文言以降だけ安定Flash')
    need(len({o['flash_sha256']for o in ao[64:76]})==12,'12部分writeを分離')
    for o in bo:
        m.idle(o,40);need(o['xy']==[60,10]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_ROUTE504_MOSGIS_EVENT_SAVE40_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=40,map=[3,44],xy=[60,10],facing=3,party_count=4,rp=0,route504_story_event_accepted=True,story4071_before=8,story4071_after=9,expanded_flag4370_accepted=True,cave_crossing_complete=True,
        save_success_text_observation=76,save_success_wording_observed=True,stable_full_flash_observation=76,save_counter_changed_observation=75,stable_field_observation=80,partial_write_observations=list(range(64,76)),event_camera_observations=list(range(30,56)),event_field_return_observation=56,
        progress_inputs=156,continue_inputs=13,screen_count=83,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,original_measurement_conclusion='failure',original_failure_is_post_save_trace_only=True,
        hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120 and fa==fb,'全legacy flag不変');return []
def event_delta(ed,vd):
    need(ed==[(258,3,7)],'拡張flag4370だけ・旧4368/4369保持')
    need(vd==[(0x4021,40,63),(0x4022,0,3),(0x4071,8,9)],'正規story4071=9と補助var2件だけ')

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save39/40とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,39,s.LAYOUT);new,rb=s.bank(after,0,40,s.LAYOUT);_,rc=s.bank(after,0xe000,39,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save39bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13796,'全Bag/HM05/所持金')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全section保持')
    x13=before[old[13]:old[13]+0xff4];y13=after[new[13]:new[13]+0xff4]
    need(x13[:0x7d0]==y13[:0x7d0]and x13[0xde6:]==y13[0xde6:],'PC/tail保持')
    ea=parent.s61e_record(x13[0x7d0:0xde6]);eb=parent.s61e_record(y13[0x7d0:0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];event_delta(ed,vd)
    prep=json.loads((ROOT/m.PREP).read_bytes());refs=prep['graph']['references']
    need(prep['coords'][0]['trigger_var']==0x4071 and prep['coords'][0]['trigger_value']==8 and any(q['category']=='var'and q['value']==0x4071 and q['access']=='write'and q['operand']==9 for q in refs)and any(q['category']=='flag'and q['value']==4370 and q['access']=='set'for q in refs),'固定ROM座標owner→正規var/flagの照合')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and (va[0x71],vb[0x71])==(8,9) and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6931,1698),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,5,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);failure=json.loads((folder/'failure.json').read_bytes())
    need(failure==dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',type='ValueError',message='Save35親の今回eventだけ',native_processes=2,source_head=SOURCE,run_id=RUN)and not(folder/'measurement.json').exists(),'保存後の旧洞窟専用parser failureを保持')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全原本native正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+57:04d}.ppm').read_bytes())==i,'menu実cursor0→4の各行')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection['route']==m.ROUTE and inspection['native_event_accepted']is False and inspection['coordinate']==dict(index=0,xy=[60,10],elevation=3,trigger_var=0x4071,trigger_value=8,script=136399338),'静的候補を原本nativeで初受入')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=CANDIDATE);return result
