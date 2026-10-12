#!/usr/bin/env python3
"""保存first-stopのmemcpy/heap/GPU calleeとBG資源2表だけを採取する。"""
from __future__ import annotations
import functools
import json
import re
import sys
import pr16_ring_story_resources_frontier as prior
import pr16_ring_story_dispatch_frontier as front
import pr16_ring_story_caller_frontier as archive
import pr16_ring_owner_frontier as sample
import pr16_ring_transitive_owner as decoder
import pr16_ring_followup_v2 as s

BASE='5ace4113413471eff4736fa41fbed8ce7a7814e8'
SLUG='pr16-ring-story-resource-suppliers'
TASK='PR-P08-7-RING-STORY-RESOURCE-SUPPLIERS'
TITLE='BG実定数・属性分岐表とmemcpy/heap/GPUの未読供給を接続'
SELF='scripts/pr16_ring_story_resource_suppliers.py'
TEST='tests/test_pr16_ring_story_resource_suppliers.py'
WORKFLOW='.github/workflows/pr16-ring-story-resource-suppliers.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_resource_suppliers.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=(prior.SELF,front.SELF,archive.SELF,sample.SELF,decoder.SELF,
    'scripts/pr16_ring_zero_bytes.py','.github/workflows/pr16-ring-callee-bytes.yml',
    'scripts/pr16_ring_message_task_frontier.py')
ARTIFACT=10540273274
ZIP_SHA='05a88be36713c5054cc7e29b01487ab7ecfc1907e2b6ac8187b27cefcd9b7e5d'
ROOTS=(0x080009c1,0x08002949,0x08002ae9,0x0804b811,0x081c9d99)
SCOPES=((0x080009c0,0x08000a38),(0x0800292c,0x0800295c),(0x08002ae8,0x08002b80),
    (0x0804b810,0x0804b85c),(0x081c9d98,0x081c9df8),(0x080019e4,0x08001aa8))
BG_DEFAULT,ATTRIBUTE_TABLE=0x081cde84,0x08001a08
NETWORK='成功run35328554870のSHA固定exportを再利用。first-stop指定5calleeと実BG定数/属性7slotのみ、同candidate復元1。既読再解読/native0。'
NO_REPEAT='memcpy/heap/GPU供給とBG定数・属性7slotは本原本を再利用し、次はその保存命令によるreset→template→window連続RAMを検証。候補復元・旧870命令・旧540/1037/786条件・受入済BP/native単独再実行禁止。通常story/IO効果/未読save暗号化ownerは未証明。'
need=s.need


@functools.lru_cache(maxsize=3)
def payload(name):
    need(name in ('saved-context.json','jp-symbols.json','reference-sources.json'),'export allowlist')
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-suppliers-input.zip')as z:
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files'][name];parts=[]
        for index,part in enumerate(row['parts']):
            need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',part['path']),'chunk path')
            raw=z.read('export/'+part['path']);need(s.identity(raw)==part['identity'],'chunk identity')
            v=json.loads(raw);need(v['file']==name and v['index']==index and v['count']==len(row['parts']),'chunk sequence');parts.append(v['text'])
        raw=''.join(parts).encode();need(s.identity(raw)==row['identity'],'file identity');return json.loads(raw)


def plan(c):
    a=c['story_resources_frontier'];known=sample.cache_nodes([c])
    need(len(known)==10056 and a['candidate']==s.CANDIDATE and a['new_node_count']==870,'保存原本境界')
    need(not a['deferred_by_wave_limit']and not a['pending_continuations'],'前回採取未完')
    need(known[0x08001070]['literal_value']==BG_DEFAULT,'BG定数pointer')
    need(known[0x080019fc]['literal_value']==ATTRIBUTE_TABLE,'BG属性table pointer')
    for target in ROOTS:
        need(target in a['pending_direct_callees']and target&~1 not in known,'未読callee境界')
        need(any(n.get('kind')=='call'and n.get('target')==target&~1 for n in c['nodes']),'保存callerなし')
    need(a['ring_acquisition_accepted']is False and a['heap_io_window_font_supply_proven']is False,'受入境界')
    return known


def data_tables(read):
    rows=[]
    for name,at,size in (('bg_default',BG_DEFAULT,4),('bg_attribute_slots',ATTRIBUTE_TABLE,28)):
        raw=read(at,size);need(type(raw)is bytes and len(raw)==size,'data幅')
        rows.append({'name':name,'address':at,'hex':raw.hex(),'identity':s.identity(raw)})
    raw=bytes.fromhex(rows[1]['hex']);slots=[]
    for i in range(7):
        target=int.from_bytes(raw[4*i:4*i+4],'little')
        need(target%2==0 and 0x08001a24<=target<0x08001a9e,'属性slot実行境界')
        slots.append({'selector':i+1,'address':ATTRIBUTE_TABLE+4*i,'target':target,'decode_root':target|1})
    return rows,slots


def collect(raw,roots,known,decode=decoder.thumb_instruction):
    def inspect(data,entries,cached,decode_fn):
        rows=[];nodes=[];points=set();cache=dict(cached)
        for entry in entries:
            end=next(hi for lo,hi in SCOPES if lo<=entry&~1<hi)
            r=sample.inspect_frontier(data,[entry],cache,decode_fn,window=min(128,end-(entry&~1)))
            rows+=r['roots'];nodes+=r['new_nodes'];points.update(r['points']);cache.update({n['address']:n for n in r['new_nodes']})
        return {'roots':rows,'new_nodes':nodes,'points':sorted(points)}
    return front.collect(raw,roots,known,inspect=inspect,decode=decode,scopes=SCOPES)


def preflight(known,read):
    return {'source_bindings':{p:s.identity(read(p))for p in dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES))},
        'roots':ROOTS,'scopes':SCOPES,'saved_nodes':len(known),'data_ranges':[(BG_DEFAULT,4),(ATTRIBUTE_TABLE,28)]}


def analyze(previous,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_message_task_frontier as exporter
    c=payload('saved-context.json');a=previous['analysis'];known=plan(c)
    need(c['story_resources_frontier']=={k:v for k,v in a.items()if k!='export_manifest'},'保存原本')
    memory={}
    for n in c['nodes']:
        for i,b in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=b
        if 'literal_address'in n:
            for i,b in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=b
    (out/'preflight.json').write_bytes(s.stable(preflight(known,lambda p:(s.ROOT/p).read_bytes())))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    data,slots=data_tables(lambda at,size:raw[at-0x08000000:at-0x08000000+size])
    roots=sorted(set(ROOTS)|{r['decode_root']for r in slots if r['target']not in known})
    r=collect(raw,roots,known);points=set(r.pop('points'))
    for row in data:points.update(range(row['address'],row['address']+row['identity']['size']))
    windows,reused=sample.new_windows(raw,sorted(points),memory);nodes=c['nodes']+r['new_nodes']
    need(len({n['address']for n in nodes})==len(nodes),'node合流重複')
    r.update({'classification':'CANDIDATE_RESOURCE_SUPPLIER_BYTES_NOT_NORMAL_STORY_EXECUTION','candidate':dict(s.CANDIDATE),
        'data_tables':data,'attribute_slots':slots,'new_node_count':len(r['new_nodes']),'saved_node_count':len(known),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'heap_io_window_font_supply_proven':False,'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,'normal_story_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'BG実定数と実属性dispatch7slotを供給。memcpy/heap/GPU静的callee帰還は実行証明ではない。未読save relocation/暗号化、HW転送、通常storyは未証明。'})
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    files=exporter.source_export((SELF,TEST,*SOURCES));files['saved-context.json']=s.stable(dict(c,nodes=nodes,story_resource_suppliers=r))
    for name in('jp-symbols.json','reference-sources.json'):files[name]=s.stable(payload(name))
    archive.export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'保存first-stopのmemcpy/heap/GPUとBG定数・属性7slotから新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteを固定。候補復元1、ROM変更/native0。',
        '保存命令でheap/reset・BG default→実template→属性→InitWindows/fontの連続RAM/部分write/不足条件を検証する。未読save relocation/暗号化とdefault callback/state2は別owner。今回byteと旧accepted条件は再採取/単独再実行しない。通常Ring取得/装備/保存、policy/Circus/P08未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_resource_suppliers']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
