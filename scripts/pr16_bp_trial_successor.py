#!/usr/bin/env python3
"""One explicit Trial delegate fix above e630; never mutate historical recipes."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_trial_route as route
need,identity,stable=route.need,route.identity,route.stable
SELF='scripts/pr16_bp_trial_successor.py'
OUT=ROOT/'.local/pr16-bp-trial-successor'
SHA='df8a15c3b464854ca84a5c0533177cfa3187b5eef252d20248f7654edb72887c'
OFFSET=0x013C93C1
BEFORE=bytes.fromhex('90f72c09')
AFTER=bytes.fromhex('a4d43809')


def replace_edge(raw:bytes,start:int,before:bytes,after:bytes)->bytes:
    need(type(raw) is bytes and type(start) is int,'immutable bytes and integer offset required')
    need(type(before) is bytes and type(after) is bytes and len(before)==len(after)==4,'one four-byte pointer required')
    need(0<=start<=len(raw)-4 and raw[start:start+4]==before,'Trial operand preimage differs')
    need(before!=after,'empty repair is not a successor')
    changed=raw[:start]+after+raw[start+4:]
    need(len(changed)==len(raw) and changed[:start]==raw[:start] and changed[start+4:]==raw[start+4:],'undeclared ROM change')
    return changed


def allocations(parent:bytes,candidate:bytes,original:dict)->dict:
    plan=copy.deepcopy(original);need(plan['summaries']['overlap_count']==0,'parent overlap')
    owners=0
    for i,row in enumerate(plan['allocations']):
        start,end=row['start'],row['end_exclusive']
        need(type(start) is int and type(end) is int and 0<=start<end<=len(parent),'allocation bounds differ')
        need(row['sequence']==i and end==start+row['size'],'allocation sequence/size differs')
        need(identity(parent[start:end])['sha256']==row['content_sha256'],'allocation preimage changed')
        if start<=OFFSET and OFFSET+4<=end:
            owners+=1;row['content_sha256']=identity(candidate[start:end])['sha256']
        else:need(parent[start:end]==candidate[start:end],'non-owner allocation changed')
    need(owners==1,'exactly one prior allocation must own the Trial operand')
    for row in plan['allocations']:
        need(identity(candidate[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'successor allocation mismatch')
    return plan


def build(parent:bytes,allocation:dict):
    audit=route.inspect(parent)
    need(audit['status']=='PASS_ROOTED_STATIC_NOT_NATIVE_ACCEPTANCE','rooted Trial predecessor not proved')
    need(audit['trial_operand']['operand_address']==route.BASE+OFFSET and audit['replacement_candidate']==0x0938D4A4,'rooted operand/target differs')
    candidate=replace_edge(parent,OFFSET,BEFORE,AFTER)
    need(identity(candidate)==dict(size=33554432,sha256=SHA),'fixed successor identity differs')
    need(audit['proposed_successor']['sha256']==SHA,'static successor projection differs')
    graph=route.graph(candidate,[0x093C9390])
    need(any(node['address']==0x0938D4A4 for node in graph),'previous physical reception wrapper was bypassed')
    need(any(row.get('special')==0x2f for node in graph for row in node['instructions']),'rental selection no longer reachable')
    changed=allocations(parent,candidate,allocation)
    report=dict(schema_version=1,status='BUILT_NOT_NATIVE_ACCEPTED',parent=identity(parent),candidate=identity(candidate),
        crc32=f'{zlib.crc32(candidate)&0xffffffff:08X}',allocation=changed,
        change=dict(offset=OFFSET,size=4,before=BEFORE.hex(),after=AFTER.hex(),changed_bytes=sum(a!=b for a,b in zip(BEFORE,AFTER))),
        scope='Trial status-10 goto only; preserve research/credit wrapper and completion adapters',
        predecessor_script=0x0938D4A4,legacy_rental_root=0x092CF5F0,legacy_completion_root=0x092CF790,
        undeclared_changed_bytes=0,new_allocations=0,save_layout_changes=0,table_changes=0,native_accepted=False,
        native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,full_clean_rebuild_claimed=False,
        active_baseline_changed=False,release_ready=False)
    return candidate,report


def run():
    import pr16_shop_display_repair as parent_layer
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe output');OUT.mkdir(parents=True,exist_ok=True)
    parent_report=parent_layer.run();parent=(parent_layer.OUTPUT/'candidate.gba').read_bytes()
    left,report=build(parent,parent_report['allocation']);right,again=build(parent,parent_report['allocation'])
    need(left==right and report==again,'independent pointer repair differs')
    (OUT/'candidate.gba').write_bytes(left)
    patches={}
    for name,old,new in (('parent-to-trial-successor.bps',parent,left),('trial-successor-to-parent.bps',left,parent)):
        patch=parent_layer.r.layer.create_bps(old,new)
        need(parent_layer.r.layer.apply_bps(old,patch)==new,'engineering patch roundtrip differs')
        (OUT/name).write_bytes(patch);patches[name]=identity(patch)
    report.update(independent_pointer_repair_builds=2,patches=patches,
        sources={name:identity((ROOT/name).read_bytes()) for name in (SELF,route.SELF,parent_layer.SELF,'config/factory_high_modes_v2.json','scripts/build_factory_high_modes_v2.py')})
    (OUT/'candidate.json').write_bytes(stable(report))
    need(identity(parent)==identity((parent_layer.OUTPUT/'candidate.gba').read_bytes()),'parent ROM was mutated')
    return report

if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False))
