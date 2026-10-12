#!/usr/bin/env python3
"""保存viewの空判定だけを512byteに修復。原本/周辺ownerを変更しない。"""
from __future__ import annotations
from pathlib import Path
import pr16_research_photo as photo
import pr16_saved_recipe as recipe_core
ROOT = Path(__file__).resolve().parents[1]
need, identity, load = photo.need, photo.identity, photo.load
PARENT = photo.CANDIDATE
C = 'tools/mgba_pr16_research_map_view.c'
RECIPE = 'content/modernization/pr16_research_map_view_recipe.json'
OFFSET = 0x58A48
BEFORE, AFTER = bytes.fromhex('ff010000'), bytes.fromhex('ff000000')
# Bound writer, emptiness predicate, clearer, restore and the actual CpuSet SWI.
ROOTS = ((0x08058994,128),(0x08058A14,64),(0x08058A54,44),(0x08058A80,140),(0x081C7A88,4),(0x0806EE14,56))
SCREENS = {'visual-earned.ppm':'e6aa09ed93ed4fd42593a0584509e2cc08ec309cf387c8cf836aad724dc4e1bc',
           'visual-cold.ppm':'e6aa09ed93ed4fd42593a0584509e2cc08ec309cf387c8cf836aad724dc4e1bc',
           'visual-cold_prompt.ppm':'b7bed16f0c7216dea297a2c408332b193f26272bd90ded4efc38259516784895'}


def build_recipe(parent: bytes) -> dict:
    need(type(parent) is bytes and identity(parent)==PARENT, 'exact accepted parent')
    need(parent[OFFSET:OFFSET+4]==BEFORE, 'predicate literal preimage')
    output=parent[:OFFSET]+AFTER+parent[OFFSET+4:]
    return dict(schema_version=1,parent=PARENT,candidate=identity(output),
        patches=[dict(offset=OFFSET,before=BEFORE.hex(),after=AFTER.hex())],
        roots={hex(a):identity(parent[a-0x08000000:a-0x08000000+n]) for a,n in ROOTS},
        purpose='SAVED_MAP_VIEW_EMPTY_SCAN_256_HALFWORDS_NOT_512',
        saved_view_offset=0x898,saved_view_bytes=512,visible_halfwords=210,
        before_last_index=511,after_last_index=255,changed_bytes=1,
        arm_compiles=0,arm_links=0,new_allocations=0,active_baseline_changed=False,release_ready=False)


def apply(parent: bytes, recipe: dict | None = None):
    expected=build_recipe(parent)
    if recipe is None:recipe=load((ROOT/RECIPE).read_bytes())
    need(photo.exact(recipe,expected), 'closed recipe / roots / one-byte repair')
    output,receipt=recipe_core.apply_recipe(parent,recipe)
    need(output[:OFFSET]==parent[:OFFSET] and output[OFFSET+4:]==parent[OFFSET+4:], 'outside literal invariant')
    need(sum(a!=b for a,b in zip(parent,output))==1,'exactly one changed byte')
    return output,dict(receipt,changed_bytes=1,arm_compiles=0,arm_links=0,new_allocations=0)


def generate(seed: bytes, candidate: dict) -> bytes:
    need(photo.exact(candidate,load((ROOT/RECIPE).read_bytes())['candidate']),'exact successor')
    text=photo.generate(seed).decode()
    token='int main(int argc,char**argv){'
    need(text.count(token)==1 and text.count(PARENT['sha256'])==1,'one inherited main/candidate')
    text=text.replace(token,'int accepted_photo_main(int argc,char**argv){').replace(PARENT['sha256'],candidate['sha256'])
    return (text+'\n'+(ROOT/C).read_text()).encode()


def closing(case: str, candidate: dict) -> dict:
    need(case in ('predicate-boundary','photo-cold-visual'),'closed new cases')
    return dict(status='PASS',case=case,candidate_sha256=candidate['sha256'],fresh_cores=1 if case=='predicate-boundary' else 2,
                predicate_calls=513 if case=='predicate-boundary' else 0,clear_calls=1 if case=='predicate-boundary' else 0,
                transaction_saves=0 if case=='predicate-boundary' else 2,manual_saves=0,
                guarded_host_writes=0,photo_earning_regressions=0 if case=='predicate-boundary' else 1,
                natural_arrival_accepted=False,release_ready=False,warnings_errors=0)


def validate(raw: bytes, case: str, candidate: dict, fixture: bytes, screens: dict) -> dict:
    need(type(raw) is bytes and 0<len(raw)<32000 and len(fixture)==131072,'bounded stdout / complete fixture')
    need(photo.exact(candidate,load((ROOT/RECIPE).read_bytes())['candidate']),'fixed successor result')
    need(photo.exact(screens,SCREENS),'fixed reviewed screen set')
    rows=[load(line) for line in raw.splitlines()]
    need(photo.exact(rows[-1],closing(case,candidate)),'exact native scope/result')
    if case=='predicate-boundary':
        need(len(rows)==2 and photo.exact(rows[0],dict(boundary='saved-map-view',view_bytes=512,neighbor_bytes=512,
             inside_one_hot_cases=256,outside_one_hot_cases=256,zero_case=1,source_unchanged=True,
             clear_bytes=512,clear_neighbor_unchanged=True,flash_unchanged=True)),'all 513 predicate and clear boundaries')
    else:
        order=['binding','event','ledger_event','prompt','outcome','visit','event','ledger_event','visual',
               'event','ledger_event','visual','visual','invariants','status']
        need(len(rows)==len(order) and all(type(r) is dict and k in r for k,r in zip(order,rows)),'photo visual row count/order')
        need(photo.exact(rows[0],photo.BINDING),'native background owner')
        stage_rows=[r for r in rows if 'visual' in r]
        need([r['visual'] for r in stage_rows]==['earned','cold','cold_prompt'],'ordered visual stages')
        for r in stage_rows:
            need(set(r)=={'visual','map','position','layout_id','layout','primary','secondary','view_empty','screen'},'closed visual schema')
            need(photo.exact({k:v for k,v in r.items() if k not in ('visual','screen','view_empty')},
                 dict(map=[96,37],position=[48,5],layout_id=497,layout=0x092A4498,primary=0x0924BBDC,secondary=0x09237EC8)), 'same exact map/layout/tilesets')
            need(type(r['view_empty']) is bool and r['view_empty'],'cleared saved view stays empty')
            need(r['screen']==screens['visual-'+r['visual']+'.ppm'],'reviewed terrain screenshot')
        # All 2048 ledger bytes plus full Bag/party are asserted in C, not a credit-only check.
        events=[r for r in rows if 'event' in r];ledgers=[r for r in rows if 'ledger_event' in r]
        need([r['event'] for r in events]==['fixture','earned','cold'] and [r['ledger_event'] for r in ledgers]==['fixture','earned','cold'],'full economic snapshots')
        first=events[0];source=fixture[photo.purchase.prior.prior.OFFSET:photo.purchase.prior.prior.OFFSET+2048]
        old=photo.purchase.prior.prior.old
        baseline=bytearray(64);baseline[0],baseline[1],baseline[6],baseline[36]=1,64,1,1
        need(source[:8]==b'VGS1\x02\0\0\x08' and old.checksum(source)==int.from_bytes(source[8:12],'little'),'fixture checksum')
        need(source[0x73f:0x77f]==baseline and type(first['counter']) is int and first['counter']==2,'zero RP / counter precondition')
        for i,(ev,led) in enumerate(zip(events,ledgers)):
            need(set(ev)==old.lc.EVENT_FIELDS and set(led)==old.lc.LEDGER_FIELDS,'full owner/ledger schema')
            need(type(ev['counter']) is int and ev['counter']==first['counter']+2*(i>0),'only two transaction saves')
            photo.catalog.integer(ev['party_count'],1,6);photo.catalog.integer(ev['item_quantity'],0,999)
            for k in ('inventory_sha256','other_inventory_sha256','party_sha256'):old.old.digest(ev[k])
            for k in ('inventory_sha256','other_inventory_sha256','party_sha256','item_quantity','party_count'):
                need(type(ev[k]) is type(first[k]) and ev[k]==first[k],'whole Bag/party invariant '+k)
            need(type(ev['owner']) is str and len(ev['owner'])==128 and all(c in '0123456789abcdef' for c in ev['owner']),'canonical full owner')
            owner=bytes.fromhex(ev['owner']);want=bytearray(source[0x73f:0x77f]);need(len(owner)==64 and owner[7]<=2,'complete bounded owner')
            want[7]=owner[7]
            if i:want[4]=6;want[10]=6;want[24]=6;want[27]=4;want[36]=2
            need(owner==want,'all RP/lifetime/daily/claim/reservation bytes')
            modeled=bytearray(source);modeled[0x73f:0x77f]=owner;modeled=old.seal(modeled)
            unrelated=bytearray(modeled);unrelated[4:6]=bytes(2);unrelated[8:12]=bytes(4);unrelated[0x73f:0x77f]=bytes(64)
            need(photo.exact(led,dict(ledger_event=ev['event'],version=2,size=2048,checksum_valid=True,
                 ledger_sha256=identity(modeled)['sha256'],unrelated_ledger_sha256=identity(unrelated)['sha256'],migration_dirty=0,recovery_blocked=0)),'independent ledger checksum')
        need(photo.exact(rows[-2],dict(invariants='after-cold-prompt',full_flash_unchanged=True,full_ledger_unchanged=True,full_bag_party_unchanged=True,counter=4)), 'cold prompt readonly')
        prompt=[r for r in rows if 'prompt' in r];outcome=[r for r in rows if 'outcome' in r];visits=[r for r in rows if 'visit' in r]
        need(len(prompt)==len(outcome)==len(visits)==1,'one affected earning prerequisite, no cancel/duplicate reruns')
        need(photo.exact(prompt[0],dict(prompt='earn',entry_keys=64,screen_sha256=photo.SCREENS['photo-earn-prompt.ppm'])),'same warm prompt')
        need(photo.exact(outcome[0],dict(outcome='earn',screen_sha256=photo.SCREENS['photo-earn-outcome.ppm'])),'same warm outcome')
        v=visits[0];photo.catalog.integer(v.get('frame'),901,10000)
        need(photo.exact(v,dict(visit='earn',confirmed=True,activity_result=0,frame=v['frame'])),'physical earning visit')
    return dict(closing(case,candidate),stdout=identity(raw),rows=rows)
