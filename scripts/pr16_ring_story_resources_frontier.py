#!/usr/bin/env python3
"""field初期化のheap/save・BG・画面資源を未読byteだけで接続する。"""
from __future__ import annotations
import functools
import json
import re
import sys
import pr16_ring_story_initializer_contracts as prior
import pr16_ring_story_dispatch_frontier as front
import pr16_ring_story_caller_frontier as archive
import pr16_ring_owner_frontier as sample
import pr16_ring_transitive_owner as decoder
import pr16_ring_followup_v2 as s

BASE='9a0a433b4e7d8b1c37f4bd193250993ecddb251c'
SLUG='pr16-ring-story-resources-frontier'
TASK='PR-P08-7-RING-STORY-RESOURCES-FRONTIER'
TITLE='heap/save resetとBG・画面初期化の未読依存を重複なしで固定'
SELF='scripts/pr16_ring_story_resources_frontier.py'
TEST='tests/test_pr16_ring_story_resources_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-story-resources-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_resources_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=33
EXTRA_CODE=()
SOURCES=(prior.SELF,front.SELF,archive.SELF,sample.SELF,decoder.SELF,
    'scripts/pr16_ring_zero_bytes.py','.github/workflows/pr16-ring-callee-bytes.yml',
    'scripts/pr16_ring_message_task_frontier.py')
ARTIFACT=10537777182
ZIP_SHA='5d56e4c88e62e62ca4e99ed26c12a06f8b42a8959e87810cb188192e09275c7d'
ROOTS=tuple(sorted((0x0804b85d,0x08000a39,0x08087a49,0x08006e65,0x08006e9d,
    0x08001619,0x08001659,0x080019e5,0x08002bb1,0x08001b91,0x08001d09,0x081139f1)))
SCOPES=((0x08000a38,0x08000b40),(0x08001000,0x08002200),(0x08002b80,0x08002c1c),
    (0x08006e64,0x08006ee0),(0x0804b850,0x0804c000),(0x08087a48,0x08087b10),(0x081139f0,0x08113a80))
TABLES=(('bg_templates',0x08055b84,0x0822d6c8,16),('window_templates',0x080f7cc6,0x083e30d0,16))
SEPARATE_OWNERS=(0x0807d695,0x080f77e9,0x0807e7a5)
NETWORK='初回run35328047608は復元前manifestのsource_bindings不足でfailure、候補復元/native0。その原結論を保持して契約を修正。成功run35322265804のSHA固定exportを再利用。同一candidate復元1回、保存命令再解読0。外部source追加/source-lock変更0。'
NO_REPEAT='heap/save・BG・画面初期化12入口と保存caller指定template2表の限定byteを再利用。未読依存を成功stubにせず、次は保存命令の実write/return/不足条件。旧540/1037/786条件、採取済byte、BP/nativeは単独再実行しない。default callbackとfield2 ownerは別未完。'
need=s.need


@functools.lru_cache(maxsize=3)
def payload(name):
    need(name in ('saved-context.json','jp-symbols.json','reference-sources.json'),'export allowlist')
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-resources-input.zip') as z:
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files'][name];parts=[]
        for index,part in enumerate(row['parts']):
            need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',part['path']),'chunk path')
            raw=z.read('export/'+part['path']);need(s.identity(raw)==part['identity'],'chunk identity')
            v=json.loads(raw);need(v['file']==name and v['index']==index and v['count']==len(row['parts']),'chunk sequence');parts.append(v['text'])
        raw=''.join(parts).encode();need(s.identity(raw)==row['identity'],'file identity');return json.loads(raw)


def plan(c):
    a=c['story_initializer_contracts'];known=sample.cache_nodes([c])
    need(len(known)==9186 and a['candidate']==s.CANDIDATE and a['contract_cases']==540,'保存原本境界')
    need(a['first_initializer_unread_callee']==0x0804b85d,'heap停止点変更')
    need(a['first_window_resource']=={'address':0x030008d0,'size':1,'site':0x08001200},'BG停止点変更')
    need(a['default_field_callback_unread']==SEPARATE_OWNERS[0] and a['field2_unread_callees']==list(SEPARATE_OWNERS[1:]),'別owner境界')
    need(a['normal_field_callback_registration_proven']is False and a['heap_io_window_font_supply_proven']is False,'未証明境界')
    for target in ROOTS:
        need(target&~1 not in known,'採取済root再実行禁止')
        need(any(n.get('kind')=='call' and n.get('target')==target&~1 for n in c['nodes']),'保存callerなし')
        need(front.in_scope(target,SCOPES),'root scope')
    for name,site,at,size in TABLES:need(known[site].get('literal_value')==at and size==16,'template caller差分 '+name)
    return known


def collect(raw,roots,known,decode=decoder.thumb_instruction):
    need(type(roots)is list and roots==list(ROOTS),'12入口固定')
    def inspect(data,entries,cached,decode_fn):
        rows=[];nodes=[];points=set();cache=dict(cached)
        for entry in entries:
            end=next(hi for lo,hi in SCOPES if lo<=entry&~1<hi)
            r=sample.inspect_frontier(data,[entry],cache,decode_fn,window=min(128,end-(entry&~1)))
            rows+=r['roots'];nodes+=r['new_nodes'];points.update(r['points']);cache.update({n['address']:n for n in r['new_nodes']})
        return {'roots':rows,'new_nodes':nodes,'points':sorted(points)}
    return front.collect(raw,roots,known,inspect=inspect,decode=decode,scopes=SCOPES)


def tables(read):
    rows=[]
    for name,site,at,size in TABLES:
        raw=read(at,size);need(type(raw)is bytes and len(raw)==size,'template read幅')
        rows.append({'name':name,'caller_literal_site':site,'address':at,'hex':raw.hex(),'identity':s.identity(raw)})
    return rows


def preflight(known,read):
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    bindings={}
    for path in paths:
        raw=read(path);need(type(raw)is bytes and bool(raw),'source byte入力')
        bindings[path]=s.identity(raw)
    return {'roots':ROOTS,'scopes':SCOPES,'tables':TABLES,'saved_nodes':len(known),'source_bindings':bindings}


def analyze(previous,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_message_task_frontier as exporter
    c=payload('saved-context.json');a=previous['analysis'];known=plan(c)
    need(c['story_initializer_contracts']=={k:v for k,v in a.items()if k!='export_manifest'},'保存契約原本')
    memory={}
    for n in c['nodes']:
        for i,b in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=b
        if 'literal_address'in n:
            for i,b in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=b
    (out/'preflight.json').write_bytes(s.stable(preflight(known,lambda p:(s.ROOT/p).read_bytes())))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw);r=collect(raw,list(ROOTS),known)
    data=tables(lambda at,size:raw[at-0x08000000:at-0x08000000+size]);points=set(r.pop('points'))
    for row in data:points.update(range(row['address'],row['address']+row['identity']['size']))
    windows,reused=sample.new_windows(raw,sorted(points),memory);nodes=c['nodes']+r['new_nodes']
    need(len({n['address']for n in nodes})==len(nodes),'node合流重複');jp=payload('jp-symbols.json')
    r.update({'classification':'CANDIDATE_HEAP_BG_SCREEN_DEPENDENCIES_NOT_NORMAL_STORY_EXECUTION',
        'candidate':dict(s.CANDIDATE),'templates':data,'scopes':SCOPES,
        'failed_attempts':[{'run_id':35328047608,'job_id':105545659303,'source_head':'0f006d3dea36feb618dfbe9673618f9e17b2b02d',
            'original_conclusion':'failure','reason':'preflight source_bindings欠落・復元前停止','candidate_reconstructions':0,'new_emulator_processes':0}],
        'new_node_count':len(r['new_nodes']),'saved_node_count':len(known),'new_windows':windows,
        'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'call_target_names':{str(n['target']|1):[name for name,value in jp.items()if value==n['target']|1]for n in r['new_nodes']if n['kind']=='call'},
        'separate_unresolved_owners':list(SEPARATE_OWNERS),'heap_io_window_font_supply_proven':False,
        'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,'full_rom_scans':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,'normal_story_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'保存caller指定12入口と2表だけ。静的call後継続はcallee帰還仮定、実RAM/IO/heap供給や通常story到達ではない。'})
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    files=exporter.source_export((SELF,TEST,*SOURCES));files['saved-context.json']=s.stable(dict(c,nodes=nodes,story_resources_frontier=r))
    for name in('jp-symbols.json','reference-sources.json'):files[name]=s.stable(payload(name))
    archive.export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'heap/save reset・BG・画面資源の12入口から未読{r["new_node_count"]}命令/{r["new_window_bytes"]}byteと実template2表を保存。既読再解読0、同candidate復元1/native0。',
        '保存heap/save resetとBG/画面資源を条件付きwrite/return契約へ結合し、030008D0供給→InitWindows/font登録の最初の未証明依存を進める。default0807D695とfield2の080F77E9/0807E7A5は別owner。今回byte、旧540/1037/786条件、BP/nativeを単独再実行しない。Ring通常取得/装備/保存、policy/Circus/P08未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_resources_frontier']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
