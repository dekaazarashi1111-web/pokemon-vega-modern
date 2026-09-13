#!/usr/bin/env python3
"""Repair one proven null-special/waitstate edge above the immutable df8 ROM.

Historical Stage18/Trial recipes and the global special table remain unchanged.
The recipe is fully identified by the fixed input SHA plus this two-byte operand;
its output identity is calculated from the actual bytes, not supplied by a caller.
This is an engineering candidate, NOT BP/release acceptance.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import struct
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_trial_successor as parent_layer
need,identity,stable=parent_layer.need,parent_layer.identity,parent_layer.stable
SELF='scripts/pr16_bp_chooser_successor.py'
OUT=ROOT/'.local/pr16-bp-chooser-successor'
PARENT_SHA=parent_layer.SHA
OFFSET=0x012CF629
BEFORE=bytes.fromhex('2f00')
AFTER=bytes.fromhex('2900')
BASE=0x08000000
BINDING_RUN=34733046485
BINDING_ARTIFACT=10309958311
BINDING_SHA='612b0740fcf4472ba885e39228e685ea716da3037cac3694829850d9536bb742'


def replace_operand(raw:bytes,start:int,before:bytes,after:bytes)->bytes:
    need(type(raw) is bytes and type(start) is int,'immutable ROM and integer offset required')
    need(type(before) is bytes and type(after) is bytes and len(before)==len(after)==2,'exactly one U16 special operand required')
    need(0<=start<=len(raw)-2 and raw[start:start+2]==before,'chooser operand preimage differs')
    need(before!=after,'empty repair rejected')
    changed=raw[:start]+after+raw[start+2:]
    need(len(changed)==len(raw) and changed[:start]==raw[:start] and changed[start+2:]==raw[start+2:],'undeclared change')
    return changed


def binding(raw:bytes)->dict:
    need(identity(raw)==dict(size=33554432,sha256=PARENT_SHA),'exact df8 successor required')
    def word(address):return struct.unpack_from('<I',raw,address-BASE)[0]
    need(word(0x08162CC4+0x25*4)==0x080697BD,'special command handler differs')
    need(raw[0x697BC:0x697DE]==bytes.fromhex('00b5fff7fbfc0004800b044941180448814207d208685ef179f909e0683016085837'),'special table dispatch differs')
    need(word(0x08163068+0x2F*4)==0x080CBF8D,'null special binding differs')
    need(raw[0xCBF8C:0xCBF8E]==bytes.fromhex('7047'),'old special is not immediate return')
    need(word(0x08163068+0x29*4)==0x080A160D,'party selection special binding differs')
    need(raw[0xA160C:0xA1628]==bytes.fromhex('00b5044904488860002086f0e3fb01bc004700003031000329160a08'),'chooser wrapper/InitChooseHalfParty call differs')
    need(word(0x08162CC4+0x27*4)==0x08069865,'waitstate handler differs')
    need(raw[0x69864:0x69870]==bytes.fromhex('00b5fff7bffd012002bc0847'),'waitstate stop dispatch differs')
    need(raw[OFFSET-1:OFFSET+3]==bytes.fromhex('252f0027'),'special/waitstate script boundary differs')
    return dict(command_table=0x08162CC4,special_table=0x08163068,
        old_special=0x2F,old_target=0x080CBF8D,old_target_is_immediate_return=True,
        replacement_special=0x29,replacement_target=0x080A160D,chooser_initializer=0x08127DE0,
        waitstate_handler=0x08069865,script_context_stop=0x080693E8,
        cause='NULL_SPECIAL_FOLLOWED_BY_UNRESUMED_WAITSTATE',
        original_run=BINDING_RUN,original_artifact=BINDING_ARTIFACT,original_zip_sha256=BINDING_SHA)


def allocations(parent:bytes,candidate:bytes,original:dict)->dict:
    plan=copy.deepcopy(original);need(plan['summaries']['overlap_count']==0,'parent overlaps')
    owners=0
    for i,row in enumerate(plan['allocations']):
        a,b=row['start'],row['end_exclusive']
        need(type(a) is int and type(b) is int and 0<=a<b<=len(parent),'allocation bounds')
        need(row['sequence']==i and b-a==row['size'],'allocation layout')
        need(identity(parent[a:b])['sha256']==row['content_sha256'],'allocation input hash differs')
        if a<=OFFSET and OFFSET+2<=b:
            owners+=1;row['content_sha256']=identity(candidate[a:b])['sha256']
        else:need(parent[a:b]==candidate[a:b],'non-owner allocation changed')
    need(owners==1,'exactly one allocation owner required')
    for row in plan['allocations']:
        need(identity(candidate[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'output allocation hash differs')
    return plan


def build(parent:bytes,allocation:dict):
    observed=binding(parent)
    raw=replace_operand(parent,OFFSET,BEFORE,AFTER)
    need(raw[OFFSET-1:OFFSET+3]==bytes.fromhex('25290027'),'output chooser boundary differs')
    report=dict(schema_version=1,status='CHOOSER_SPECIAL_REPAIRED_NOT_NATIVE_ACCEPTED',
        parent=identity(parent),candidate=identity(raw),crc32=f'{zlib.crc32(raw)&0xffffffff:08X}',
        allocation=allocations(parent,raw,allocation),binding=observed,
        change=dict(offset=OFFSET,address=BASE+OFFSET,size=2,before=BEFORE.hex(),after=AFTER.hex(),changed_bytes=1),
        undeclared_changed_bytes=0,new_allocations=0,global_special_table_changes=0,save_layout_changes=0,
        scope='Initial Factory Trial rental chooser only; battle and exchange launchers are not accepted',
        native_rental_accepted=False,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,
        full_candidate_regression_complete=False,clean_rom_dual_build_verified=False,release_ready=False)
    return raw,report


def run():
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe output')
    OUT.mkdir(parents=True,exist_ok=True)
    parent_report=parent_layer.run();parent=(parent_layer.OUT/'candidate.gba').read_bytes()
    left,report=build(parent,parent_report['allocation']);right,again=build(parent,parent_report['allocation'])
    need(left==right and report==again,'independent bounded repair differs')
    (OUT/'candidate.gba').write_bytes(left)
    import pr16_shop_display_repair as shop
    patches={}
    for name,old,new in (('parent-to-chooser.bps',parent,left),('chooser-to-parent.bps',left,parent)):
        patch=shop.r.layer.create_bps(old,new);need(shop.r.layer.apply_bps(old,patch)==new,'patch roundtrip differs')
        (OUT/name).write_bytes(patch);patches[name]=identity(patch)
    report.update(patches=patches,independent_bounded_repairs=2,
        sources={p:identity((ROOT/p).read_bytes()) for p in (SELF,parent_layer.SELF,parent_layer.route.SELF)})
    (OUT/'candidate.json').write_bytes(stable(report))
    need(identity(parent)==identity((parent_layer.OUT/'candidate.gba').read_bytes()),'parent mutated')
    return report

if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False))
