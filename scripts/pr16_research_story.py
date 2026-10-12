#!/usr/bin/env python3
"""通常進行の閉じた入力protocol。旧nativeケースは生成にも実行にも使わない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import struct
import pr16_research_new_game as old
import pr16_research_shop_ui as patch
ROOT=Path(__file__).resolve().parents[1]
C='tools/mgba_pr16_research_story.c'
CANDIDATE=patch.CANDIDATE
ERASED=old.ERASED
KEYS=(0,1,2,8,16,32,64,128)

def need(v,why):
    if not v:raise ValueError(why)

def identity(b):return {'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def unique(pairs):
    o={}
    for k,v in pairs:
        need(k not in o,'duplicate JSON key');o[k]=v
    return o

def integer(v,lo,hi):
    need(type(v) is int and lo<=v<=hi,'bounded integer');return v

def digest(v):need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v),'SHA-256')

def source_check(s):
    need(s.count('int main(int argc,char**argv){')==1,'one story main')
    stripped=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
    for token in ('write8','write16','write32','write_register','call_preserving','call_rom','si_call','si_restore','qol_stub_target','si_open','accepted_newgame_main','loadState','saveState','loadTemporarySave','putPixels','TestSet','ng_ledger','ng_position'):
        need(not re.search(r'\b'+token+r'\s*\(',stripped),'forbidden story call '+token)
    calls=set(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*\(',stripped))
    allowed=set('st_open st_keys st_press st_screen st_observe st_save main si_need si_digest ng_flash lc_read lc_w16 lc_w32 read8 read16 read32 run_key_frames sha256_file si_field si_flash si_guard si_guard_check qol_close qol_die mCoreFind mCoreLoadFile mCoreLoadSaveFile mCoreInitConfig mCoreConfigSetDefaultValue mCoreSetRTC mLogSetDefaultLogger init setVideoBuffer reset snprintf fopen fprintf fwrite fclose printf fflush strcmp strlen fgets sscanf if for while sizeof'.split())
    need(calls<=allowed,'closed source call graph: '+str(sorted(calls-allowed)))
    need(len(re.findall(r'\breset\s*\(',stripped))==1 and len(re.findall(r'\bfopen\s*\(',stripped))==1,'reset and screen-only file writer')
    need(stripped.count('core->reset(core);')==1 and stripped.count('core->setVideoBuffer(core,si_video,240);')==1,'one initial video reset')
    need(stripped.index('core->setVideoBuffer(core,si_video,240);')<stripped.index('core->reset(core);'),'video before reset')
    need('si_flash(c);si_guard(c);' in stripped,'barrier before frames')
    main=stripped.split('int main(int argc,char**argv){',1)[1]
    need(main.index('si_guard(c);')<main.index('st_keys(c,'),'barrier before first frame')
    need(stripped.count('run_key_frames(c,key,frames);')==1,'all frame execution logged')
    return identity(s.encode())

def generate():
    s=(ROOT/C).read_text();source_check(s)
    base=old.generate().decode();token='int main(int argc,char**argv){'
    need(base.count(token)==1,'one retained new-game declaration')
    base=base.replace(token,'int accepted_newgame_main(int argc,char**argv){')
    need(base.count(old.CANDIDATE['sha256'])==1,'one inherited candidate identity')
    base=base.replace(old.CANDIDATE['sha256'],CANDIDATE['sha256'])
    return (base+s).encode()

def commands(raw):
    need(type(raw) is str and 0<len(raw)<=40000 and raw.endswith('quit\n'),'bounded explicit command end')
    lines=raw.splitlines();need(lines.count('quit')==1,'one final quit')
    last=-1
    for line in lines:
        part=line.split(' ')
        if part[0]=='key':
            need(len(part)==3 and all(x.isdecimal() for x in part[1:]),'closed key syntax')
            need(int(part[1]) in KEYS,'ordinary single key');integer(int(part[2]),1,600)
        elif part[0]=='observe':
            need(len(part)==2 and part[1].isdecimal(),'observation syntax')
            n=int(part[1]);need(n>last,'unique ordered observations');last=n
        else:need(line in ('save','quit'),'closed command')
    return lines

def observations(raw,mode='new-game-story',screens=None):
    need(0<len(raw)<400000,'bounded raw observations')
    rows=[json.loads(x,object_pairs_hook=unique) for x in raw.decode().splitlines()]
    need(len(rows)>4,'complete trace');start,end=rows[0],rows[-1]
    need(set(start)=={'begin','candidate_sha256','initial_save_sha256','host_write_barriers'} and start['begin']==('NEW_GAME_STORY_DEVELOPMENT' if mode=='new-game-story' else 'INDEPENDENT_CONTINUE'),'begin schema')
    need(start['candidate_sha256']==CANDIDATE['sha256'] and start['host_write_barriers']==7,'fixed candidate/barrier')
    if mode=='new-game-story':need(start['initial_save_sha256']==ERASED['sha256'],'blank source not fixture')
    else:digest(start['initial_save_sha256'])
    need(end==dict(end='STORY_INPUT_CHECKPOINT',frames=end['frames'],inputs=end['inputs'],warnings_errors=0,host_write_barriers=7,guarded_host_writes=0,fixture_calls=0,natural_research_arrival_accepted=False),'scoped terminal')
    frame=0;inputs=[];obs=[];imgs=[];saves=[];expect_screen=None
    for row in rows[1:-1]:
        need(expect_screen is None or 'screen' in row,'immediate same-frame screen')
        if 'input' in row:
            need(set(row)=={'input','frame','key','frames'},'input schema')
            need(type(row['input']) is int and row['input']==len(inputs) and type(row['frame']) is int and row['frame']==frame,'input sequence/frame')
            integer(row['key'],0,128);need(row['key'] in KEYS,'ordinary key');integer(row['frames'],1,600)
            frame+=row['frames'];need(frame<=1800000,'total frame bound');inputs.append(row)
        elif 'observe' in row:
            need(set(row)=={'observe','frame','map','xy','live_xy','facing','field','lock','callback2','party_count','save_counter','rp','battle_flags','battle_outcome','party_sha256','flash_sha256','ledger_sha256'},'observation schema')
            for k in ('facing','lock','battle_outcome'):integer(row[k],0,255)
            for k in ('frame','callback2','battle_flags'):integer(row[k],0,2**32-1)
            need(row['frame']==frame and type(row['observe']) is int and (not obs or row['observe']>obs[-1]['observe']),'observation order/frame')
            for k in ('map','xy','live_xy'):
                need(type(row[k]) is list and len(row[k])==2,'coordinate schema')
                for x in row[k]:integer(x,0,65535)
            integer(row['party_count'],0,6);integer(row['rp'],0,9999);integer(row['save_counter'],0,2**32-1)
            for k in ('party_sha256','flash_sha256','ledger_sha256'):digest(row[k])
            need(type(row['field']) is bool,'boolean field');integer(row['lock'],0,255)
            obs.append(row);expect_screen=row['observe']
        elif 'screen' in row:
            need(set(row)=={'screen','frame','sha256'} and expect_screen==row['screen'] and row['frame']==frame,'screen paired at exact frame');digest(row['sha256'])
            if screens is not None:
                b=(screens/f"screen-{row['screen']:04}.ppm").read_bytes()
                need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n') and identity(b)['sha256']==row['sha256'],'real screen bytes')
                pixels=b[15:];need(any(pixels[i:i+3]!=pixels[:3] for i in range(3,len(pixels),3)),'nonblank renderer')
            imgs.append(row);expect_screen=None
        elif 'ordinary_save' in row:
            need(set(row)=={'ordinary_save','before','after','frame'} and row['ordinary_save'] is True and row['frame']==frame,'ordinary save schema')
            integer(row['before'],0,2**32-2);need(type(row['after']) is int and row['after']==row['before']+1,'one actual Save');saves.append(row)
        else:raise ValueError('unrecognized observation')
    need(expect_screen is None and len(obs)==len(imgs)>0 and type(end['frames']) is int and end['frames']==frame and type(end['inputs']) is int and end['inputs']==len(inputs),'complete terminal counts')
    if mode=='new-game-story':
        need(len(inputs)>=234,'complete prerequisite')
        prefix=b''.join(struct.pack('<IH',r['frames'],r['key']) for r in inputs[:233])
        need(identity(prefix)['sha256']==old.trace()['trace_sha256'] and inputs[233]['key']==0 and inputs[233]['frames']==600,'unchanged prerequisite keys')
        need(obs[0]['map']==[4,0] and obs[0]['party_count']==0 and obs[0]['save_counter']==0 and obs[0]['flash_sha256']==ERASED['sha256'],'natural starting point')
    return dict(inputs=inputs,observations=obs,screens=imgs,saves=saves,end=end,start=start)

def retained(first,second):
    """独立Continueの全party/Flash/位置/残高と自然starterを比較。"""
    a=first['observations'][-1];b=second['observations'][-1]
    need(len(first['saves'])==1 and first['saves'][0]['before']==0 and first['saves'][0]['after']==1 and not second['saves'],'one initial Save, no Continue Save')
    maps=[r['map'] for r in first['observations']]
    need([4,0] in maps and [3,0] in maps and [4,3] in maps and a['map']==[4,3],'actual home/outdoor/starter-lab route')
    need(all(r['rp']==0 and r['party_count'] in (0,1) and r['save_counter'] in (0,1) for r in first['observations']),'no earned RP or injected extra party')
    need(a['party_count']==1 and a['rp']==0 and a['field'] and a['lock']==0,'natural starter at idle field')
    need(a['save_counter']==1 and a['flash_sha256']!=ERASED['sha256'],'first natural progress Save')
    for k in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(a[k]==b[k],'Continue retains '+k)
    need(b['field'] and b['lock']==0,'Continue idle field')
    need(second['start']['initial_save_sha256']!=ERASED['sha256'],'retained real Save input')
    return dict(status='PASS_NATURAL_STARTER_STORY_SCOPED',candidate=CANDIDATE,natural_starter_accepted=True,natural_research_arrival_accepted=False,release_ready=False,active_baseline_changed=False,first_save=a,continued=b)
