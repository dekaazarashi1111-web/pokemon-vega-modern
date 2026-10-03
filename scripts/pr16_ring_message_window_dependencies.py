#!/usr/bin/env python3
"""状態0/1の保存callsiteから残る5依存だけを採取する。既読根は再実行しない。"""
from __future__ import annotations
import functools
import sys
import pr16_ring_followup_v2 as s
import pr16_ring_message_window_frontier as prior
import pr16_ring_text_export_recovery as export

BASE='3f2fddf31ca50af69b3f824e959066a4459d9bfb'
SLUG='pr16-ring-message-window-dependencies'
TASK='PR-P08-7-RING-MESSAGE-WINDOW-DEPENDENCIES'
TITLE='状態0/1のtile矩形・window資源・paletteコピー中継5依存を保存'
SELF='scripts/pr16_ring_message_window_dependencies.py'
TEST='tests/test_pr16_ring_message_window_dependencies.py'
WORKFLOW='.github/workflows/pr16-ring-message-window-dependencies.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_message_window_dependencies.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.PRIOR,*prior.SOURCES)))
ROOTS=(0x08002555,0x08002591,0x08153089,0x081534cd,0x081c7a89)
ORIGINS=((0x080f81e0,ROOTS[0]),(0x08003fbc,ROOTS[1]),(0x081530fc,ROOTS[2]),
         (0x08152f9a,ROOTS[3]),(0x0806fba6,ROOTS[4]))
NO_REPEAT=('状態0/1の残存5callee採取は本原本とhash付きexportを再利用。'
    '次は属性0・palette・r8 frame・queueの明示RAM結合。今回/旧29命令78byte/旧1231条件/BP/nativeは再実行しない。')
need=s.need


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    c=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    return dict(c,nodes=[*c['nodes'],*r['analysis']['new_nodes']],window_frontier=r['analysis'])


def plan(c):
    a=c['window_frontier'];by={n['address']:n for n in c['nodes']}
    need(len(by)==len(c['nodes'])==8280,'保存8280命令')
    need(a['candidate']==s.CANDIDATE and a['new_node_count']==29 and a['new_window_bytes']==78,'先行29命令78byte')
    need(a['selector0']['hex']=='58490008' and a['selector0']['table']==prior.TABLE
         and a['selector0']['target']==0x08004958,'属性0保存word')
    need(a['pending_direct_callees']==[ROOTS[-1]] and not a['pending_continuations'],'palette残境界')
    for k in prior.FALSE:need(a[k] is False,'未受入境界 '+k)
    for site,target in ORIGINS:
        need(by[site]['kind']=='call' and by[site]['target']==target&~1,'依存の保存callsite '+hex(site))
    need(by[0x081c7ae8]['hex']=='4047' and by[0x081c7ae8]['register']==8,'frame r8中継')
    need(all(t&~1 not in by for t in ROOTS),'既読callee再採取禁止')
    need(c['task_contracts']['contract_cases']==1231 and c['task_contracts']['same_ram_state2_sequences']==96,'上流原本保持')
    return {'roots':list(ROOTS),'origin_calls':[list(p) for p in ORIGINS],
        'max_nodes':2048,'max_bytes':8192,'recursive_direct_calls':False,
        'accepted_contract_cases_replayed':0,'saved_nodes_redecoded':0}


def validate_new(r,c):
    need(r['initial_roots']==list(ROOTS) and not r['saved_roots_reused'],'指定5根')
    need(r['saved_nodes_redecoded']==r['direct_calls_recursively_expanded']==0,'既読/再帰禁止')
    old={p for n in c['nodes'] for p in range(n['address'],n['address']+n['size'])}
    data=set(range(prior.TABLE,prior.TABLE+32));starts=[]
    for n in c['nodes']:
        if 'literal_address' in n:data.update(range(n['literal_address'],n['literal_address']+4))
    for n in r['new_nodes']:
        at,size=n['address'],n['size'];starts.append(at)
        need(type(at)is int and at%2==0 and size in (2,4) and 0x08000000<=at<at+size<=0x0a000000,'命令範囲')
        span=set(range(at,at+size));need(not span&(old|data),'既読/data再解読禁止')
        need(len(bytes.fromhex(n['hex']))==size,'命令byte長');old|=span
    need(0<len(starts)<=2048 and starts==sorted(set(starts)),'新node予算/重複')


def analyze(previous,out):
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_message_owner_frontier as memory_source
    import pr16_ring_message_task_frontier as exporter
    c=saved_inputs();bound=plan(c);nodes=c['nodes']
    need(previous['analysis']['new_node_count']==29,'直前原本')
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':bound,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    forbidden=set(range(prior.TABLE,prior.TABLE+32))
    for n in nodes:
        if 'literal_address' in n:forbidden.update(range(n['literal_address'],n['literal_address']+4))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'保存dataを命令にしない')
        return decoder.thumb_instruction(data,at)
    r=walk.bounded_walk(raw,list(ROOTS),old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
        max_nodes=2048,max_bytes=8192,max_roots=64,max_rounds=8)
    validate_new(r,c)
    _,memory,_,_=memory_source.saved_inputs();memory=dict(memory)
    for n in nodes:
        for i,v in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=v
        if 'literal_address'in n:
            for i,v in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=v
    for i,v in enumerate(bytes.fromhex(c['window_frontier']['selector0']['hex'])):memory[prior.TABLE+i]=v
    windows,reused=old.new_windows(raw,r.pop('points'),memory)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate変更禁止')
    r.update({k:False for k in prior.FALSE})
    r.update({'classification':'WINDOW_REMAINING_FIVE_DEPENDENCIES_NOT_NATIVE_ACCEPTANCE','candidate':dict(s.CANDIDATE),
        'plan':bound,'new_windows':windows,'new_node_count':len(r['new_nodes']),
        'saved_node_count':len(nodes)+len(r['new_nodes']),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,
        'successful_callee_stubs':0,'boundary_ja':'採取は実帰還やBIOS/DMAの実行証明ではない。新BL/間接辺を未解決のまま保持。'})
    files=exporter.source_export((SELF,TEST,*SOURCES,s.SELF,export.SELF))
    files['saved-context.json']=s.stable(dict(c,nodes=[*nodes,*r['new_nodes']],window_dependencies=r))
    manifest=export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    r['export_logical_files']=len(manifest['files']);(out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'状態0/1の保存callsiteから残存5calleeを新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteで保存。旧8280命令再解読/1231条件再実行/native0。',
        '次は保存属性0・paletteコピー中継・r8 frame・tile矩形/window資源を明示RAMで結合し、'
        'state0/1の帰還・次状態・queue予約・不足時部分writeを検証。新BL/BIOS/DMAは成功stubにしない。'
        '今回5callee/旧29命令/旧1231条件/BP/nativeは単独再実行せず、通常story/Ring/live初期化は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
