#!/usr/bin/env python3
"""保存setupの命令表とfield callerの未読接続だけをcandidateへ結び付ける。"""
from __future__ import annotations
import copy
import functools
import json
import re
import sys
import pr16_ring_story_caller_frontier as prior
import pr16_ring_followup_v2 as s
import pr16_ring_owner_frontier as sample
import pr16_ring_remaining_frontier as edges
import pr16_ring_transitive_owner as decoder

BASE='815874a137b4ff917383dfc010ca3f4dc91f8853'
SLUG='pr16-ring-story-dispatch-frontier'
TASK='PR-P08-7-RING-STORY-DISPATCH-FRONTIER'
TITLE='保存script setupの実命令表とfield callerの未読接続をcandidate byteに固定'
SELF='scripts/pr16_ring_story_dispatch_frontier.py'
TEST='tests/test_pr16_ring_story_dispatch_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-story-dispatch-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_dispatch_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=(prior.SELF,sample.SELF,edges.SELF,decoder.SELF,'scripts/pr16_ring_zero_bytes.py',
    '.github/workflows/pr16-ring-callee-bytes.yml','scripts/pr16_ring_message_task_frontier.py')
NETWORK='固定Actions exportと同hash candidateの既存復元だけ。外部source追加/source-lock変更なし。保存命令再解読0、未読辺とmessage表2slotだけ。'
NO_REPEAT='保存script setupのtable08162CC4/end08163010、message/waitmessage実slotと有限field/script caller採取を再利用。保存8K命令/bootstrap/text/BP/nativeの単独再実行禁止。間接dispatchとstory側state/window供給は到達証明ではない。'
ARTIFACT=10535062027
ZIP_SHA='e904c876eaa6878824d430133931b51a29a63cf92df81dce06d890c07a354bf3'
ENTRY_NAMES=('CB2_Overworld','CB2_LoadMap','CB2_ReturnToFieldLocal')
EXPECTED_ENTRIES=(0x08055e75,0x08055fdd,0x080560c9)
# fixed JP symbols bracket field setup/script runtime/text-box helpers; do not recurse elsewhere.
SCOPES=((0x08055b50,0x08057f00),(0x08069060,0x08069480),(0x080f7c6c,0x080f7d14))
MAX_WAVES,MAX_ROOTS,MAX_NODES,MAX_BYTES=16,96,2048,8192
TABLE,END,CONTEXT=0x08162cc4,0x08163010,0x03000eb0
need=s.need


@functools.lru_cache(maxsize=3)
def payload(name):
    need(name in ('saved-context.json','jp-symbols.json','reference-sources.json'),'export allowlist')
    with prior.artifact(ARTIFACT,ZIP_SHA,'story-caller.zip') as z:
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files'][name];parts=[]
        for index,part in enumerate(row['parts']):
            need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',part['path']),'chunk path')
            raw=z.read('export/'+part['path']);need(s.identity(raw)==part['identity'],'chunk identity')
            v=json.loads(raw);need(v['file']==name and v['index']==index and v['count']==len(row['parts']),'chunk sequence')
            parts.append(v['text'])
        raw=''.join(parts).encode();need(s.identity(raw)==row['identity'],'file identity');return json.loads(raw)


def setup_binding(nodes):
    by=sample.cache_nodes([{'nodes':nodes}])
    for at,value in ((0x080693b4,CONTEXT),(0x080693b6,TABLE),(0x080693b8,END)):
        need(by[at].get('literal_value')==value,'保存setup literal')
    for at,target in ((0x080693bc,0x0806906c),(0x080693c4,0x080690a8)):
        need(by[at]['kind']=='call' and by[at]['target']==target,'保存setup call')
    need(END>TABLE and (END-TABLE)%4==0,'table bound')
    return {'setup':0x080693a5,'context_initializer':0x0806906d,'bytecode_setup':0x080690a9,
        'context':CONTEXT,'table':TABLE,'end':END,'slot_count':(END-TABLE)//4,
        'saved_caller_reexecuted':False,'normal_story_observed':False}


def table_slots(read,table=TABLE,end=END):
    need(type(table)is int and type(end)is int and table==TABLE and end==END,'固定table境界')
    rows=[]
    for op in (0x66,0x67):
        at=table+4*op;need(at+4<=end,'slot越境');raw=read(at,4)
        need(type(raw)is bytes and len(raw)==4,'slot read幅')
        value=int.from_bytes(raw,'little')
        need(value&1 and 0x08000000<=value<0x0a000000,'handler Thumb範囲')
        if op==0x67:need(value==prior.TARGETS['ScrCmd_message'],'message handler差分')
        rows.append({'opcode':op,'address':at,'hex':raw.hex(),'target':value})
    return rows


def in_scope(pointer,scopes=SCOPES):
    need(type(pointer)is int and pointer&1,'Thumb pointer')
    return any(lo<=pointer&~1<hi for lo,hi in scopes)


def select_roots(symbols):
    roots=tuple(symbols[name]for name in ENTRY_NAMES)
    need(roots==EXPECTED_ENTRIES and all(in_scope(r)for r in roots),'固定JP entry')
    return list(roots)


def collect(raw,roots,cached,*,inspect=sample.inspect_frontier,decode=decoder.thumb_instruction,scopes=SCOPES):
    need(type(roots)is list and roots and len(set(roots))==len(roots),'root空/重複')
    need(all(in_scope(r,scopes)for r in roots),'採取root scope')
    known=copy.deepcopy(cached);new={};points=set();rows=[];waves=[];attempted=set();queue=sorted(roots)
    def limited_decode(data,at):
        need(any(lo<=at<hi for lo,hi in scopes),'decode scope境界')
        n=decode(data,at)
        need(any(lo<=at and at+n['size']<=hi for lo,hi in scopes),'命令scope越境')
        return n
    for wave in range(MAX_WAVES):
        queue=[r for r in queue if r&~1 not in known and r not in attempted]
        if not queue:break
        need(len(attempted)+len(queue)<=MAX_ROOTS,'root総予算');attempted.update(queue)
        part=inspect(raw,queue,known,limited_decode);fresh=part['new_nodes']
        need(len({n['address']for n in fresh})==len(fresh) and not any(n['address']in known for n in fresh),'新規node重複')
        need(len(new)+len(fresh)<=MAX_NODES,'node総予算');points.update(part['points']);need(len(points)<=MAX_BYTES,'byte総予算')
        for n in fresh:known[n['address']]=new[n['address']]=n
        rows+=part['roots'];following=set()
        for root in part['roots']:
            for edge in root['boundaries']:
                if edge['kind'] not in edges.CONTINUATIONS|{'unread_call'}:continue
                t=edges.boundary_target(edge)
                if t is not None and in_scope(t,scopes) and t&~1 not in known and t not in attempted:following.add(t)
        waves.append({'index':wave,'roots':queue,'new_nodes':len(fresh),'following':sorted(following)})
        queue=sorted(following)
    return {'initial_roots':roots,'new_nodes':[new[k]for k in sorted(new)],'points':sorted(points),'roots':rows,
        'waves':waves,'deferred_by_wave_limit':queue,'saved_nodes_redecoded':0,
        **edges.classify_boundaries(rows,known)}


def analyze(previous,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_message_task_frontier as exporter
    c=payload('saved-context.json');jp=payload('jp-symbols.json');a=previous['analysis']
    need(c['story_caller_frontier']=={k:v for k,v in a.items()if k!='export_manifest'},'caller export原本')
    need(a['saved_node_count']==len(c['nodes'])==8628 and a['ring_acquisition_accepted']is False,'保存境界')
    setup=setup_binding(c['nodes']);roots=select_roots(jp);known=sample.cache_nodes([c]);memory={}
    for n in c['nodes']:
        for i,b in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=b
        if 'literal_address'in n:
            for i,b in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=b
    paths=(SELF,TEST,WORKFLOW,PRIOR,*SOURCES)
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths},
        'roots':roots,'scopes':SCOPES,'budget':[MAX_WAVES,MAX_ROOTS,MAX_NODES,MAX_BYTES]}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    result=collect(raw,roots,known)
    slots=table_slots(lambda at,size:raw[at-0x08000000:at-0x08000000+size])
    points=set(result.pop('points'))
    for row in slots:points.update(range(row['address'],row['address']+4))
    windows,reused=sample.new_windows(raw,sorted(points),memory)
    all_nodes=c['nodes']+result['new_nodes'];need(len({n['address']for n in all_nodes})==len(all_nodes),'保存合流重複')
    result.update({'classification':'CANDIDATE_FIELD_CALLERS_AND_MESSAGE_TABLE_NOT_STORY_EXECUTION',
        'candidate':dict(s.CANDIDATE),'setup_binding':setup,'command_slots':slots,
        'candidate_message_slot_bound':True,'saved_node_count':len(c['nodes']),'new_node_count':len(result['new_nodes']),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'new_inbound':prior.saved_inbound(all_nodes),'jp_entry_names':dict(zip(ENTRY_NAMES,roots)),
        'call_target_names':{str(n['target']|1):[name for name,value in jp.items()if value==n['target']|1]
            for n in result['new_nodes']if n['kind']=='call'},
        'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,'full_rom_scans':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,'normal_story_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'保存setup供給表の66/67実slotと3 field entryから範囲限定のcall/分岐命令だけ。間接dispatch/stateと通常story到達・window資源は未証明。'})
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    files=exporter.source_export((SELF,TEST,*SOURCES));files['saved-context.json']=s.stable(dict(c,nodes=all_nodes,story_dispatch_frontier=result))
    files['jp-symbols.json']=s.stable(jp);files['reference-sources.json']=s.stable(payload('reference-sources.json'))
    prior.export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return (f'保存setupの実命令表08162CC4/end08163010からmessage67→0806B0CDをcandidate byteに結合。field3入口の未読{r["new_node_count"]}命令/{r["new_window_bytes"]}byteを有限採取。初期化/BP/native再実行0。',
        '保存field/script callerを条件付きstate/command dispatch契約に結合し、残る間接分岐のtableと通常story initializer到達を限定する。命令表接続はRing受入ではない。font/config/global/window初期供給、通常取得/保存、policy/Circus/P08は未受入。今回byteの再採取と旧bootstrap/text/BP/native再実行は禁止。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_dispatch_frontier']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
