#!/usr/bin/env python3
"""固定母親ownerへの2箇所の委譲だけを新候補へ適用し、境界を証明する。"""
from __future__ import annotations
import hashlib
import struct
from pathlib import Path
from tools.regression.home_recovery import MOTHER, ORIGINAL, REGIONS, original_mother_script, fallback

PARENT={'size':33554432,'sha256':'e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842'}
INPUT_SAVE={'size':131088,'sha256':'e3ff50a1d88d24db28b4996440cf11c0114fa75f228c238f9e2e87fb122ac48a'}
PARENT_RUNNER={'size':73792,'sha256':'67096f8c8a487c03957da071d0190f74542480fb051cf8e8934e1b05adee9a61'}
PORTAL=0x09220CD0
LOCKED=0x09220CF8
PROMPT=0x09220D04
TRAVEL=0x09220D1C
BUILDER='tools/regression/rom_runtime.py'


def need(ok,reason):
    if not ok:raise ValueError(reason)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def rows():
    return [dict(offset=LOCKED-0x08000000,before='0f00af0c220909046c02',after=fallback(MOTHER,reserved=5).hex()),
            dict(offset=PROMPT+19-0x08000000,before='6c02000000',after=fallback(MOTHER).hex())]


def edit(raw,patches):
    need(type(raw) is bytes and type(patches) is list and len(patches)==2,'固定2箇所')
    out=bytearray(raw);last=0
    for row in patches:
        need(type(row) is dict and set(row)=={'offset','before','after'},'patch schema')
        at=row['offset'];a=bytes.fromhex(row['before']);b=bytes.fromhex(row['after'])
        need(type(at) is int and last<=at<=len(raw)-len(a) and len(a)==len(b)>0 and a!=b,'固定幅・非重複')
        need(raw[at:at+len(a)]==a,'patch preimage')
        out[at:at+len(b)]=b;last=at+len(a)
    return bytes(out)


def audit(parent,original):
    need(type(parent) is bytes and identity(parent)==PARENT,'親候補の全SHA')
    need(type(original) is bytes and identity(original)==ORIGINAL,'固定Vega原本の全SHA')
    def objects(raw):
        def u(at):
            need(type(at) is int and 0<=at<=len(raw)-4,'ROM pointer範囲')
            return struct.unpack_from('<I',raw,at)[0]
        root=u(0x54B0C);group=u(root-0x8000000+16);header=u(group-0x8000000)
        events=u(header-0x8000000+4);obj=u(events-0x8000000+4)
        need(raw[events-0x8000000]==1,'母親object単一')
        at=obj-0x8000000;record=raw[at:at+24]
        need(len(record)==24 and record[0]==1 and struct.unpack_from('<hh',record,4)==(8,4),'母親local/座標')
        return dict(root=root,group=group,header=header,events=events,objects=obj,script=u(at+16)),record
    a,ar=objects(original);b,br=objects(parent)
    need(a['script']==MOTHER and b['script']==PORTAL,'原本とT17実owner')
    need(ar[:16]+ar[20:]==br[:16]+br[20:],'objectのscript以外不変')
    for raw in (parent,original):original_mother_script(raw,MOTHER)
    need(identity(parent[PORTAL-0x8000000:PORTAL-0x8000000+112])['sha256']=='bd7f5e2f12f322527b765949efb90efe68c5c9f51182f4fbcf2ee09513de5345','T17全入口/解禁条件/渡航/帰還')
    return dict(schema_version=1,original=ORIGINAL,parent=PARENT,original_object=a,current_object=b,
                original_regions=[dict(offset=x,size=n,sha256=h) for x,n,h in REGIONS],
                original_mother_goto=MOTHER,heal_call=0x081944F2,heal_special=0,
                npc_relocated=False,healing_injected=False,unlock_flags_changed=False)


def apply(parent,original):
    proof=audit(parent,original);patches=rows();out=edit(parent,patches)
    reverse=[dict(offset=r['offset'],before=r['after'],after=r['before']) for r in patches]
    need(edit(out,reverse)==parent,'全ROM rollback')
    proof.update(candidate=identity(out),patches=patches,declared_bytes=15,
        changed_bytes=sum(a!=b for r in patches for a,b in zip(bytes.fromhex(r['before']),bytes.fromhex(r['after']))),
        outside_declared_changes=0,whole_rom_rollback=True,arm_compiles=0,
        locked_route='ORIGINAL_MOTHER',unlocked_decline_route='ORIGINAL_MOTHER',unlocked_accept_route='UNCHANGED_T17_TRAVEL',
        native_recovery_accepted=False,travel_native_accepted=False,release_ready=False,active_baseline_changed=False)
    return out,proof


CANDIDATE={'size':33554432,'sha256':'06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'}


def generate():
    """既存closed入力driverの候補SHAだけをソースで固定し、通常compileに渡す。"""
    import pr16_research_story as story
    source=story.generate()
    old=PARENT['sha256'].encode();new=CANDIDATE['sha256'].encode()
    need(source.count(old)==1,'一意候補SHAのsource定義')
    result=source.replace(old,new)
    need(result.replace(new,old)==source,'候補SHA以外のdriver source不変')
    return result



def gate_destination(raw,flags,answer):
    """ROM命令を読む限定独立oracle。実渡航のnative受入とは区別する。"""
    need(type(flags) is dict and set(flags)=={0x082C,0x0824,0x114B} and all(type(v) is bool for v in flags.values()),'3flag型')
    need(type(answer) is bool,'yes/no型');pc=PORTAL;cmp=0
    for _ in range(30):
        if pc in (MOTHER,TRAVEL):return pc
        at=pc-0x8000000;op=raw[at]
        if op in (0x6A,0x5A):pc+=1
        elif op==0x23:pc+=5 # 既存RuntimeProbe、bodyはpatch外。
        elif op==0x2B:cmp=int(flags[struct.unpack_from('<H',raw,at+1)[0]]);pc+=3
        elif op==0x06:
            cond=raw[at+1];need(cond in (0,1),'既知分岐条件')
            target=struct.unpack_from('<I',raw,at+2)[0];pc=target if cmp==cond else pc+6
        elif op==0x05:pc=struct.unpack_from('<I',raw,at+1)[0]
        elif op==0x0F:need(raw[at+1]==0,'textbank');pc+=6
        elif op==0x09:need(raw[at+1]==5,'yes/no std');cmp=int(answer);pc+=2
        elif op==0x21:need(raw[at+1:at+5]==b'\x0d\x80\x01\0','yes answer比較');pc+=5
        else:raise ValueError('未対応のgate命令')
    raise ValueError('goto loop')
