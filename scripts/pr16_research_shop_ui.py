#!/usr/bin/env python3
"""59ac6688上のshop2参照だけを修復する。旧canonical/保存/価格は変更しない。"""
from __future__ import annotations
from array import array
import hashlib
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE='tools/pr16_research_shop_ui.S'
PARENT={'size':33554432,'sha256':'59ac6688576238f00dac88cccec1a42415f6f0e4f3f07d60411f6d3059bf61e6'}
CANDIDATE={'size':33554432,'sha256':'e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842'}
BASE=0x09F4B000
RESERVATION=128
CODE=bytes.fromhex('70b504000d0000200021094b00f00ff8084b00f00cf801002000f022064b00f006f820002900054b00f001f870bd1847b57f0f08cd890f08e13015087d7f0f08')
HOOKS=((0x093BF1E0,0x15000800,0x15010800),(0x093BF1F8,0x080F7F7D,BASE|1),(0x093BF61C,0x08110BF9,0x08110539))
ROOTS={
 0x080F7FFC:(64,'575753f4f9766817dbc64afb070a42ab4f373caa832ea067437582419d660f49'),
 0x093BEF60:(736,'909b7382e883ac048866a96a60c96408988801901d92a2757135835720050f3c'),
 0x093BF510:(320,'6128b97abea88222a98f38d689ed87035d27a75c3af45ca1716ecdc748ce143b'),
 0x080F89CC:(32,'19d9981b1aed03106357bf2d486368c433afa47e68fe05a7fe7a25446e329ce1'),
 0x080F7F7C:(64,'a401363c8b3e6280a42ea513458eaec9bebfd944f5eaddc9406eeabf615cbe51'),
 0x081530E0:(112,'ca65ef229f7226d4d61f1e5800a93736fada53933e2247bdfe9c0edd2aa1489f'),
 0x08110538:(144,'e64ed4de9f4b66a0d0f1e6970fa2bc4baae18099624f8f0bcfddb60862c8d0bc'),
 0x08110BF8:(56,'f403a8437aa88f6910432ea87fc3bc28e96cfe6decd7d6b2c1064b1a5e37b5ee'),
 0x093C0328:(116,'866d74853185fe10244f62630aad1c9681d63d63b2e4e02cd4b0accfb909adc0')}

def need(value,reason):
    if not value: raise ValueError(reason)

def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def patch_rows():
    return [dict(offset=a-0x08000000,before=struct.pack('<I',old).hex(),after=struct.pack('<I',new).hex()) for a,old,new in HOOKS]+[
        dict(offset=BASE-0x08000000,before=(b'\xff'*len(CODE)).hex(),after=CODE.hex())]

def edit(raw,rows):
    need(type(raw) is bytes and type(rows) is list and rows,'immutable ROM/nonempty rows')
    out=bytearray(raw);last=0
    for row in sorted(rows,key=lambda r:r['offset']):
        at=row['offset'];before=bytes.fromhex(row['before']);after=bytes.fromhex(row['after'])
        need(type(at) is int and last<=at<=len(raw)-len(before) and before!=after and len(before)==len(after)>0,'bounded nonoverlapping equal-size edits')
        need(raw[at:at+len(before)]==before,'exact preimage')
        out[at:at+len(after)]=after;last=at+len(after)
    return bytes(out)

def audit(raw):
    need(type(raw) is bytes and identity(raw)==PARENT,'exact accepted parent')
    need(raw[BASE-0x08000000:BASE-0x08000000+RESERVATION]==b'\xff'*RESERVATION,'all reserved bytes unused')
    words=array('I');words.frombytes(raw)
    if sys.byteorder!='little':words.byteswap()
    references=[i*4 for i,v in enumerate(words) if BASE<=v<BASE+RESERVATION]
    need(not references,'no aligned absolute references into reservation')
    for a,(size,digest) in ROOTS.items():
        need(identity(raw[a-0x08000000:a-0x08000000+size])==dict(size=size,sha256=digest),'source-proven root '+hex(a))
    for a,old,_ in HOOKS:
        need(struct.unpack_from('<I',raw,a-0x08000000)[0]==old,'two live API literals and top margin only')
    need(identity(CODE)==dict(size=64,sha256='912cccf40213defa338809c1fa1cc7820340e417a7f07b543ef1b924c621adea'),'fixed assembled Thumb code')
    need(raw[0x13bf05a:0x13bf05e]==bytes.fromhex('3820c046'),'actual preexisting pixel-base immediate, not dead canonical getter')
    return dict(base=BASE,reservation=RESERVATION,actual_code=64,new_ewram_bytes=0,
                aligned_absolute_reference_candidates=references,
                pixel_tiles=[0x38,0x188],dialogue_tiles=[0x198,0x200],frame_tiles=[0x214,0x21d],intervals_half_open=True,
                maximum_width=21,maximum_height=16,top=1,old_dialogue_hidden_without_free=True,
                standard_list_allocation_end=BASE,allocation_overlap=0)

def apply(raw):
    allocation=audit(raw);rows=patch_rows();out=edit(raw,rows)
    need(identity(out)==CANDIDATE,'expected successor identity')
    reverse=[dict(offset=r['offset'],before=r['after'],after=r['before']) for r in rows]
    need(edit(out,reverse)==raw,'whole-ROM rollback')
    count=sum(a!=b for a,b in zip(raw,out));need(count==71,'exact changed bytes')
    return out,dict(schema_version=1,parent=PARENT,candidate=CANDIDATE,patches=rows,allocation=allocation,
        changed_bytes=count,declared_bytes=76,outside_declared_changes=0,whole_rom_rollback_matches_parent=True,
        roots={hex(a):dict(size=n,sha256=h) for a,(n,h) in ROOTS.items()},
        code=identity(CODE),source=SOURCE,canonical_source_unchanged=True,
        numeric_and_standard_list_unchanged=True,shop_catalog_and_save_code_unchanged=True,
        natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,
        active_baseline_changed=False,release_ready=False)
