#!/usr/bin/env python3
"""保存dispatchが要求した5slotとwait callbackの未読接続だけを採取。"""
from __future__ import annotations
import sys
import pr16_ring_story_dispatch_contracts as prior
import pr16_ring_story_dispatch_frontier as front
import pr16_ring_story_caller_frontier as archive
import pr16_ring_followup_v2 as s
import pr16_ring_owner_frontier as sample
import pr16_ring_transitive_owner as decoder

BASE='a4195f0e873ab4617ad6bbe422c210d9d08727af'
SLUG='pr16-ring-story-field-frontier'
TASK='PR-P08-7-RING-STORY-FIELD-FRONTIER'
TITLE='field状態5slotと実wait callbackの未読接続を限定採取'
SELF='scripts/pr16_ring_story_field_frontier.py'
TEST='tests/test_pr16_ring_story_field_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-story-field-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_field_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=(prior.SELF,front.SELF,archive.SELF,sample.SELF,decoder.SELF,
    'scripts/pr16_ring_zero_bytes.py','.github/workflows/pr16-ring-callee-bytes.yml',
    'scripts/pr16_ring_message_task_frontier.py')
NETWORK='成功run35319087228と保存exportを照合し同hash candidateを1回だけ復元。外部source追加/source-lock変更0。'
NO_REPEAT='080565B0の5slotと08068DDDの実callback、field未読接続は今回保存byteを再利用。全u8旧script契約、旧text/bootstrap/BP/nativeの単独再実行禁止。命令採取をfield初期化やRing通常取得のruntime受入へ昇格しない。'
TABLE,COUNT,WAIT=prior.FIELD_TABLE,5,prior.WAIT
TARGET_BOUNDS=(TABLE+COUNT*4,0x080565fc)
SCOPES=((0x08056200,0x08057f00),(0x08068dcc,0x08068e10),(0x080f7c6c,0x080f7d14))
need=s.need


def pending_binding(previous,nodes):
    a=previous['analysis'];known=sample.cache_nodes([{'nodes':nodes}])
    need(a['pending_field_table']=={'address':TABLE,'slots':COUNT,'dispatch_site':0x080565aa,'entry':0x08056599},'保存field要求')
    need(a['pending_wait_callback']==WAIT and a['contract_cases']==1037,'保存wait要求')
    need(known[0x080565a4].get('literal_value')==TABLE and known[0x080565a8]['hex']=='0068'
        and known[0x080565aa]['hex']=='8746','保存dispatch命令')
    need(known[0x0806b13a].get('literal_value')==WAIT,'保存wait literal')
    need(WAIT&~1 not in known,'wait採取済み')
    points=set()
    for n in nodes:
        points.update(range(n['address'],n['address']+n['size']))
        if 'literal_address'in n:points.update(range(n['literal_address'],n['literal_address']+4))
    need(not points.intersection(range(TABLE,TABLE+4*COUNT)),'table採取済み')
    return known


def field_slots(read,table=TABLE,count=COUNT):
    need(type(table)is int and type(count)is int and table==TABLE and count==COUNT,'5slot固定境界')
    raw=read(table,4*count);need(type(raw)is bytes and len(raw)==4*count,'5slot read幅')
    rows=[]
    for index in range(count):
        data=raw[index*4:index*4+4];target=int.from_bytes(data,'little')
        # MOV pcはBXではない。偶数Thumb命令addressを許し、ROM/関数内境界を検査する。
        need(TARGET_BOUNDS[0]<=target<TARGET_BOUNDS[1] and not target&1,'MOV-pc field target境界/整列')
        rows.append({'state':index,'address':table+4*index,'hex':data.hex(),'target':target,'decode_root':target|1})
    return rows


def requested_roots(rows,known):
    need(type(rows)is list and len(rows)==COUNT,'slot数')
    roots=[]
    for i,r in enumerate(rows):
        need(r['state']==i and r['address']==TABLE+i*4 and r['hex']==r['target'].to_bytes(4,'little').hex()
            and TARGET_BOUNDS[0]<=r['target']<TARGET_BOUNDS[1] and not r['target']&1
            and r['decode_root']==r['target']|1,'slot root結合')
        need(r['target']not in known,'field state採取済み')
        roots.append(r['decode_root'])
    need(WAIT&~1 not in known,'callback採取済み')
    return sorted(set(roots+[WAIT]))


def collect(raw,roots,known,decode=decoder.thumb_instruction):
    need(type(roots)is list and roots and WAIT in roots,'wait root必須')
    need(all(r==WAIT or TARGET_BOUNDS[0]<=r&~1<TARGET_BOUNDS[1]for r in roots),'最初のroot境界')
    def guarded(data,at):
        need(not TABLE<=at<TABLE+COUNT*4,'jump table data解読禁止')
        return decode(data,at)
    return front.collect(raw,roots,known,decode=guarded,scopes=SCOPES)


def analyze(previous,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_message_task_frontier as exporter
    c=prior.payload('saved-context.json');jp=prior.payload('jp-symbols.json')
    known=pending_binding(previous,c['nodes']);need(len(known)==8821,'保存8821命令境界')
    memory={}
    for n in c['nodes']:
        for i,b in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=b
        if 'literal_address'in n:
            for i,b in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=b
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in(SELF,TEST,WORKFLOW,PRIOR,*SOURCES)},
        'table':TABLE,'slots':COUNT,'wait':WAIT,'scopes':SCOPES,'saved_nodes':len(known)}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    slots=field_slots(lambda at,size:raw[at-0x08000000:at-0x08000000+size])
    roots=requested_roots(slots,known);r=collect(raw,roots,known)
    points=set(r.pop('points'));points.update(range(TABLE,TABLE+COUNT*4))
    windows,reused=sample.new_windows(raw,sorted(points),memory)
    nodes=c['nodes']+r['new_nodes'];need(len({n['address']for n in nodes})==len(nodes),'node合流重複')
    r.update({'classification':'CANDIDATE_FIELD_STATE_TABLE_AND_WAIT_CALLBACK_NOT_STORY_EXECUTION',
        'candidate':dict(s.CANDIDATE),'field_slots':slots,'wait_callback':WAIT,
        'new_node_count':len(r['new_nodes']),'saved_node_count':len(c['nodes']),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'new_inbound':archive.saved_inbound(nodes),
        'call_target_names':{str(n['target']|1):[name for name,value in jp.items()if value==n['target']|1]for n in r['new_nodes']if n['kind']=='call'},
        'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,'full_rom_scans':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,'normal_story_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'保存dispatchが要求した5slot/wait callbackと範囲内未読calleeだけ。保存nodeへ合流し既読契約を再実行しない。field資源供給と通常story取得は未受入。'})
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    files=exporter.source_export((SELF,TEST,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,nodes=nodes,story_dispatch_contracts={k:v for k,v in previous['analysis'].items()if k!='export_manifest'},story_field_frontier=r))
    files['jp-symbols.json']=s.stable(jp);files['reference-sources.json']=s.stable(prior.payload('reference-sources.json'))
    archive.export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'実field5slotとwait callback08068DDDを採取し未読{r["new_node_count"]}命令/{r["new_window_bytes"]}byteを結合。既読8821命令再解読0、BP/native0。',
        '保存field state本体と実wait callbackを条件付き実行へ結合し、初期化calleeのfont/window供給と未読境界を限定する。今回byte/旧script1037条件/BP/nativeの単独再実行は禁止。Ring通常取得/装備/保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_field_frontier']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
