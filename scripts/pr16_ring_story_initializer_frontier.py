#!/usr/bin/env python3
"""field0/2/3の未読calleeと初期化may-call接続をcandidate byteに限定。"""
from __future__ import annotations
from collections import deque
import sys
import pr16_ring_story_wait_lifecycle as prior
import pr16_ring_story_dispatch_frontier as front
import pr16_ring_story_caller_frontier as archive
import pr16_ring_owner_frontier as sample
import pr16_ring_transitive_owner as decoder
import pr16_ring_followup_v2 as s

BASE='94b3f04ab76ed1408beca47c24169e99b10a41c0'
SLUG='pr16-ring-story-initializer-frontier'
TASK='PR-P08-7-RING-STORY-INITIALIZER-FRONTIER'
TITLE='field初期化calleeとwindow/printerの条件付きcall接続を実byteに固定'
SELF='scripts/pr16_ring_story_initializer_frontier.py'
TEST='tests/test_pr16_ring_story_initializer_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-story-initializer-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_initializer_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=(prior.SELF,front.SELF,archive.SELF,sample.SELF,decoder.SELF,
    'scripts/pr16_ring_zero_bytes.py','.github/workflows/pr16-ring-callee-bytes.yml',
    'scripts/pr16_ring_message_task_frontier.py')
NETWORK='成功済み保存wait/field契約とhash固定exportを再利用。同hash candidateの復元1回。外部source追加/source-lock変更0。'
NO_REPEAT='field初期化3calleeとwindow/printer may-call接続の保存byteを再利用。call後のfallthroughはcallee帰還を仮定する静的到達で通常初期化実行ではない。旧wait786/script1037/text/bootstrap/BP/nativeを単独再実行しない。'
SCOPES=((0x080555f0,0x08055630),(0x08055b50,0x08055f80),(0x08056200,0x08057f00),
    (0x08068c70,0x08068cd0),(0x080f7c6c,0x080f7d14))
ROOTS=tuple(sorted(prior.UNREAD.values()))
TARGETS={'InitWindows':0x08003af1,'DeactivateAllTextPrinters':0x08002c29,'SetDefaultFontsPointer':0x080f8a29}
need=s.need


def pending_roots(previous,nodes):
    a=previous['analysis'];known=sample.cache_nodes([{'nodes':nodes}])
    need(a['field_unread_callees']=={str(k):v for k,v in prior.UNREAD.items()} and a['contract_cases']==786,'保存callee要求')
    need(a['host_memory_writes_between_ticks']==0 and a['actual_wait_callback']==prior.d.WAIT,'保存wait境界')
    rows={r['case']:r for r in a['cases']}
    for state,target in prior.UNREAD.items():
        need(rows['field-'+str(state)]['stop']==['保存node境界で停止',target&~1],'保存停止点')
        need(target&~1 not in known,'callee採取済み')
    return list(ROOTS),known


def in_scope(at):return any(lo<=at<hi for lo,hi in SCOPES)


def collect(raw,roots,known,decode=decoder.thumb_instruction):
    need(type(roots)is list and roots==list(ROOTS),'3callee固定root')
    return front.collect(raw,roots,known,decode=decode,scopes=SCOPES)


def may_paths(nodes,entry=0x080565c5,targets=TARGETS,limit=1024):
    """保存CFGの有限may-call。callee後の継続は帰還仮定と明記し、間接先を創作しない。"""
    need(type(limit)is int and 1<=limit<=1024,'CFG予算')
    known=sample.cache_nodes([{'nodes':nodes}]);need(type(entry)is int and entry&1 and in_scope(entry&~1),'CFG entry')
    need(type(targets)is dict and targets and all(type(v)is int and v&1 and 0x08000000<=v<0x0a000000 for v in targets.values()),'CFG target')
    queue=deque([(entry&~1,[])]);seen=set();found={};deferred=[]
    while queue:
        at,path=queue.popleft()
        if at in seen:continue
        if len(seen)>=limit:deferred=[at]+[p for p,_ in queue];break
        seen.add(at)
        if at not in known or not in_scope(at):continue
        n=known[at];successors=[]
        if n['kind']=='call':
            call={'site':at,'kind':'direct_call','target':n['target']|1}
            for name,target in targets.items():
                if target==n['target']|1 and name not in found:found[name]=path+[call]
            successors=[(n['target'],call),(at+n['size'],{'site':at,'kind':'after_call_assumes_return','target':at+n['size']})]
        elif n['kind'] in ('jump','conditional'):
            successors=[(n['target'],{'site':at,'kind':'possible_branch','target':n['target']})]
            if n['kind']=='conditional':successors.append((at+n['size'],{'site':at,'kind':'possible_fallthrough','target':at+n['size']}))
        elif n['kind']=='ordinary' and int.from_bytes(bytes.fromhex(n['hex']),'little')&0xff00!=0xbd00:
            successors=[(at+n['size'],{'site':at,'kind':'instruction_fallthrough','target':at+n['size']})]
        # 間接jump・returnはここで止める。引数、stack、side effectを証明しない。
        for target,edge in successors:
            if target not in seen and in_scope(target):queue.append((target,path+[edge]))
    return {'entry':entry,'targets':dict(targets),'paths':found,'not_found_in_bounded_graph':[k for k in targets if k not in found],
        'visited_nodes':len(seen),'deferred_by_node_limit':deferred,
        'assumes_return_at_after_call_edges':True,'argument_or_return_abi_proven':False,'runtime_reachability_proven':False}


def analyze(previous,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_message_task_frontier as exporter
    c=prior.payload('saved-context.json');roots,known=pending_roots(previous,c['nodes']);jp=prior.payload('jp-symbols.json')
    need(len(known)==9012,'保存9012命令境界');memory={}
    for n in c['nodes']:
        for i,b in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=b
        if 'literal_address'in n:
            for i,b in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=b
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in(SELF,TEST,WORKFLOW,PRIOR,*SOURCES)},'roots':roots,'scopes':SCOPES,'saved_nodes':len(known)}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw);r=collect(raw,roots,known)
    windows,reused=sample.new_windows(raw,r.pop('points'),memory);nodes=c['nodes']+r['new_nodes']
    need(len({n['address']for n in nodes})==len(nodes),'node合流重複')
    r.update({'classification':'CANDIDATE_FIELD_INITIALIZER_MAY_CALL_NOT_NORMAL_STORY_EXECUTION',
        'candidate':dict(s.CANDIDATE),'field0_initializer_may_paths':may_paths(nodes),
        'new_node_count':len(r['new_nodes']),'saved_node_count':len(known),'new_windows':windows,
        'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'new_inbound':archive.saved_inbound(nodes),
        'call_target_names':{str(n['target']|1):[name for name,value in jp.items()if value==n['target']|1]for n in r['new_nodes']if n['kind']=='call'},
        'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,'full_rom_scans':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,
        'normal_story_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'未読field3calleeと範囲内直呼出しだけ。may-callのcall後継続は帰還仮定。初期化のheap/IO/window資源・通常story到達は未証明。'})
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    files=exporter.source_export((SELF,TEST,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,nodes=nodes,story_wait_lifecycle={k:v for k,v in previous['analysis'].items()if k!='export_manifest'},story_initializer_frontier=r))
    files['jp-symbols.json']=s.stable(jp);files['reference-sources.json']=s.stable(prior.payload('reference-sources.json'))
    archive.export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    names='/'.join(r['field0_initializer_may_paths']['paths'])or'未到達'
    return (f'field初期化3calleeの未読{r["new_node_count"]}命令/{r["new_window_bytes"]}byteを保存。field0から{names}への有限may-callを固定。通常実行/帰還は未証明、native0。',
        '保存field初期化/RunFieldCallback/flash getterの条件付き契約を結合し、window/font供給の残るheap/IO/callback停止点を絞る。今回byteと旧wait/script/text/BP/nativeの単独再実行は禁止。Ring通常取得/保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_initializer_frontier']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
