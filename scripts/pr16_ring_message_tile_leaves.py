#!/usr/bin/env python3
"""矩形描画のindex計算・tile値書込2leafだけを追加保存する。BIOSは解釈しない。"""
from __future__ import annotations
import functools
import sys
import pr16_ring_followup_v2 as s
import pr16_ring_message_window_dependencies as prior
import pr16_ring_text_export_recovery as export

BASE='1bd73e76fecf82933ad1d967de515cc5dfa1bdd8'
SLUG='pr16-ring-message-tile-leaves'
TASK='PR-P08-7-RING-MESSAGE-TILE-LEAVES'
TITLE='矩形描画のindex計算・tile値書込2leafを保存'
SELF='scripts/pr16_ring_message_tile_leaves.py'
TEST='tests/test_pr16_ring_message_tile_leaves.py'
WORKFLOW='.github/workflows/pr16-ring-message-tile-leaves.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_message_tile_leaves.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.PRIOR,*prior.SOURCES)))
ROOTS=(0x08002805,0x0800283d)
ORIGINS=((0x08002652,ROOTS[0]),(0x08002668,ROOTS[1]))
TABLE=0x08004938
FALSE=prior.prior.FALSE
NO_REPEAT=('矩形index計算/値書込2leafは本原本とexportを再利用。'
    '次は状態0/1の明示RAM結合。BIOS SWI0B/0Cを成功stubにしない。今回/旧5callee/29命令/1231条件/BP/nativeは再実行しない。')
need=s.need


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    c=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    return dict(c,nodes=[*c['nodes'],*r['analysis']['new_nodes']],window_dependencies=r['analysis'])


def plan(c):
    a=c['window_dependencies'];by={n['address']:n for n in c['nodes']}
    need(len(by)==len(c['nodes'])==8560,'保存8560命令')
    need(a['candidate']==s.CANDIDATE and a['new_node_count']==280 and a['new_window_bytes']==614,'先行280命令614byte')
    need(a['pending_direct_callees']==list(ROOTS) and not a['pending_continuations'],'残存2leaf')
    bios=[r for r in a['pending_boundaries']if r['site']==0x081c7a88]
    need(len(bios)==1 and bios[0]['kind']=='decoder_rejection' and bios[0]['encoded']=='0bdf','保存SWI0B境界')
    for k in FALSE:need(a[k] is False,'未受入境界 '+k)
    for site,target in ORIGINS:
        need(by[site]['kind']=='call' and by[site]['target']==target&~1,'保存callsite '+hex(site))
    need(all(t&~1 not in by for t in ROOTS),'既読leaf再採取禁止')
    need(c['window_frontier']['selector0']['hex']=='58490008','属性0word保持')
    need(c['task_contracts']['contract_cases']==1231,'上流原本保持')
    return {'roots':list(ROOTS),'origin_calls':[list(p)for p in ORIGINS],
        'max_nodes':128,'max_bytes':512,'recursive_direct_calls':False,
        'accepted_contract_cases_replayed':0,'saved_nodes_redecoded':0,'bios_execution_claimed':False}


def validate_new(r,c):
    need(r['initial_roots']==list(ROOTS) and not r['saved_roots_reused'],'指定2根')
    need(r['saved_nodes_redecoded']==r['direct_calls_recursively_expanded']==0,'既読/再帰禁止')
    old={p for n in c['nodes'] for p in range(n['address'],n['address']+n['size'])}
    data=set(range(TABLE,TABLE+32));starts=[]
    for n in c['nodes']:
        if 'literal_address' in n:data.update(range(n['literal_address'],n['literal_address']+4))
    for n in r['new_nodes']:
        at,size=n['address'],n['size'];starts.append(at)
        need(type(at)is int and at%2==0 and size in (2,4) and 0x08000000<=at<at+size<=0x0a000000,'命令範囲')
        span=set(range(at,at+size));need(not span&(old|data),'既読/data再解読禁止')
        need(len(bytes.fromhex(n['hex']))==size,'命令byte長');old|=span
    need(0<len(starts)<=128 and starts==sorted(set(starts)),'新node予算/重複')


def analyze(previous,out):
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_message_owner_frontier as memory_source
    import pr16_ring_message_task_frontier as exporter
    c=saved_inputs();bound=plan(c);nodes=c['nodes']
    need(previous['analysis']['new_node_count']==280,'直前原本')
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':bound,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    forbidden=set(range(TABLE,TABLE+32))
    for n in nodes:
        if 'literal_address' in n:forbidden.update(range(n['literal_address'],n['literal_address']+4))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'保存dataを命令にしない')
        return decoder.thumb_instruction(data,at)
    r=walk.bounded_walk(raw,list(ROOTS),old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
        max_nodes=128,max_bytes=512,max_roots=16,max_rounds=8)
    validate_new(r,c)
    _,memory,_,_=memory_source.saved_inputs();memory=dict(memory)
    for n in nodes:
        for i,v in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=v
        if 'literal_address'in n:
            for i,v in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=v
    for i,v in enumerate(bytes.fromhex(c['window_frontier']['selector0']['hex'])):memory[TABLE+i]=v
    windows,reused=old.new_windows(raw,r.pop('points'),memory)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate変更禁止')
    r.update({k:False for k in FALSE})
    r.update({'classification':'WINDOW_TILE_LEAVES_NOT_NATIVE_ACCEPTANCE','candidate':dict(s.CANDIDATE),
        'plan':bound,'new_windows':windows,'new_node_count':len(r['new_nodes']),
        'saved_node_count':len(nodes)+len(r['new_nodes']),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,
        'successful_callee_stubs':0,'boundary_ja':'採取は実帰還やBIOS/DMAの実行証明ではない。新BL/間接辺を未解決のまま保持。'})
    files=exporter.source_export((SELF,TEST,*SOURCES,s.SELF,export.SELF))
    files['saved-context.json']=s.stable(dict(c,nodes=[*nodes,*r['new_nodes']],tile_leaves=r))
    manifest=export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    r['export_logical_files']=len(manifest['files']);(out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'矩形index計算とtile値書込の残存2leafを新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteで保存。旧8560命令再解読/1231条件再実行/native0。',
        '次は保存属性0・palette・r8 frame・矩形・queueの状態0/1結合を明示RAMで検証。'
        '帰還/次状態と描画成功を区別し、queue満杯等の部分成功とBIOS SWI停止を保持。'
        '今回2leaf/旧5callee/29命令/1231条件/BP/nativeは再実行しない。通常story/Ring/live初期化は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
