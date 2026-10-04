#!/usr/bin/env python3
"""固定ROMのplay-time/research-minute owner。全SaveBlock2免除はしない。"""
from __future__ import annotations
import struct
from pr16_story_live_observer import u16, u32, story_effects
from pr16_story_milestones import require, DiagnosticStop
CLOCK_START, CLOCK_END, CLOCK_MAX = 0xE, 0x13, 999 * 216000 + 59 * 3600 + 59 * 60 + 59
OWNER = 0x73F

def clock_value(raw):
    require(type(raw) is bytes and len(raw)==0xF24, 'clock_save2_geometry')
    h=u16(raw,14); m,s,v=raw[16:19]
    require(h<=999 and m<60 and s<60 and v<60, 'clock_fields_range')
    return h*216000+m*3600+s*60+v

def clock_delta(before, after, frames, *, extra_save2=None):
    require(type(frames) is int and 0<frames<=120000, 'clock_frame_budget')
    first,last=clock_value(before),clock_value(after)
    require(first<CLOCK_MAX and last<CLOCK_MAX, 'clock_saturation_needs_separate_owner')
    # One main loop per VBlank; a sample can straddle its update by one frame.
    require(0<=last-first<=frames+1, 'clock_nonmonotone_or_excessive')
    expected=bytearray(before); expected[14:19]=after[14:19]
    for at,value in (extra_save2 or {}).items():
        require(type(at) is int and 0<=at<len(before) and not 14<=at<19 and type(value) is int and 0<=value<256,'clock_extra_byte_geometry')
        expected[at]=value
    require(bytes(expected)==after, 'unowned_save2_change')
    return dict(ticks=last-first,minute_rollovers=last//3600-first//3600,frame_budget=frames)

def ledger_checksum(raw):
    require(len(raw)==2048,'ledger_geometry');h=2166136261
    for i,v in enumerate(raw):h=((h^(0 if 8<=i<12 else v))*16777619)&0xffffffff
    return h

def ledger_valid(raw):
    require(type(raw) is bytes and len(raw)==2048,'ledger_geometry')
    require(raw[:8]==bytes.fromhex('5647533102000008') and u32(raw,8)==ledger_checksum(raw),'ledger_header_checksum')
    require(raw[OWNER:OWNER+4]==b'\x01\x40\x00\x00' and raw[OWNER+7]<60 and raw[OWNER+44:OWNER+64]==bytes(20),'ledger_idle_owner')

def ledger_after_minutes(raw, minutes):
    ledger_valid(raw);require(type(minutes) is int and 0<=minutes<=34,'minute_budget')
    out=bytearray(raw)
    for _ in range(minutes):
        n=out[OWNER+7]+1
        if n==60:
            out[OWNER+7]=0;struct.pack_into('<H',out,OWNER+8,(u16(out,OWNER+8)+1)&65535)
            out[OWNER+14:OWNER+26]=bytes(12)
            out[OWNER+27:OWNER+32]=bytes(5)
        else:out[OWNER+7]=n
        struct.pack_into('<I',out,8,ledger_checksum(out))
    return bytes(out)

def time_evidence(before, after, *, extra_save2=None):
    b,a=before['observation'],after['observation']
    require(a['observe']>b['observe'],'time_observation_order')
    clock=clock_delta(before['save2'],after['save2'],a['frame']-b['frame'],extra_save2=extra_save2)
    require(ledger_after_minutes(before['ledger'],clock['minute_rollovers'])==after['ledger'],'unowned_research_ledger_change')
    return clock

def no_save(before,after):
    b,a=before['observation'],after['observation']
    require(a['save_counter']==b['save_counter']==101 and a['flash_sha256']==b['flash_sha256'] and a['rp']==b['rp']==0 and a['party_count']==b['party_count']==4,'unexpected_save_or_scope')
    require(all(before[k]==after[k]for k in('last_ball','coins','expanded_flags','expanded_vars')),'unowned_expansion_change')

def byte_deltas(before,after):
    require(type(before)in(bytes,bytearray) and type(after)in(bytes,bytearray) and len(before)==len(after),'delta_geometry')
    return [[i,x,y]for i,(x,y)in enumerate(zip(before,after))if x!=y]

def walking_evidence(before,after,target):
    """Same-map one-tile or rotation. Map transitions use a separate owner."""
    no_save(before,after);b,a=before['observation'],after['observation']
    require(b['callback2']==a['callback2']==0x08055E75 and b['lock']==a['lock']==0 and b['map']==a['map'],'walking_field_scope')
    require(type(target)is list and len(target)==2 and sum(abs(x-y)for x,y in zip(b['xy'],target))==1,'one_tile_target')
    require(a['xy']in(b['xy'],target),'walking_position')
    count=int(a['xy']==target);expected=bytearray(before['save1'])
    struct.pack_into('<HH',expected,0,*a['xy'])
    for var,mod in [(0x21,128),(0x22,5)]:
        value=(before['variables'][var]+count)%mod
        require(after['variables'][var]==value,'step_counter')
        struct.pack_into('<H',expected,0x1000+var*2,value)
    key=u32(before['save2'],0xF20)
    steps=u32(before['save1'],0x1214)^key
    struct.pack_into('<I',expected,0x1214,min(0xFFFFFF,steps+count)^key)
    if bytes(expected)!=after['save1']:
        raise DiagnosticStop('unowned_walking_save1',dict(deltas=byte_deltas(expected,after['save1'])[:80]))
    wrap=count and before['variables'][0x21]==127
    p=bytearray(before['party']);changed=[]
    for slot in range(4):
        first,last=before['party_mons'][slot],after['party_mons'][slot]
        require(first['status']==last['status']==0,'walking_status_owner')
        at=slot*100+41
        allowed=(p[at],min(255,p[at]+1))if wrap else(p[at],)
        require(after['party'][at]in allowed,'friendship_event5_bounded')
        if p[at]!=after['party'][at]:changed.append([slot,p[at],after['party'][at]])
        p[at]=after['party'][at]
    require(bytes(p)==after['party'],'unowned_walking_party')
    t=time_evidence(before,after)
    return dict(walking_steps=count,friendship_wrap=bool(wrap),friendship=changed,clock=t,save_requested=False,milestone_reached=False)
