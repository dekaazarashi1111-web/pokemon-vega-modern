#!/usr/bin/env python3
"""残る実callee/validator正常継続を有限waveで採取。既読ABI/nativeは再実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys

BASE='5fc9c2f3c9a995b808b6e142e557a82a8a44bc89'
SLUG='pr16-ring-remaining-frontier'
TASK='PR-P08-7-RING-REMAINING-FRONTIER'
TITLE='残るcalleeとvalidator正常継続を有限waveで保存結合'
SELF='scripts/pr16_ring_remaining_frontier.py'
TEST='tests/test_pr16_ring_remaining_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-remaining-frontier.yml'
PRIOR='content/modernization/pr16_ring_effective_contracts.json'
REPORT='content/modernization/pr16_ring_remaining_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=32
EXTRA_CODE=()
DIRECT=(0x08008b49,0x08068ccd,0x080f7dbd,0x081c27dd)
EFFECTIVE=(0x093bde81,)
SUCCESS={1:0x093bdaa8,2:0x093bdb3e}
ROM_BASE,ROM_END=0x08000000,0x0a000000
MAX_ROUNDS,MAX_ROOTS,MAX_NODES,MAX_BYTES=32,256,4096,16384
CONTINUATIONS={'window_boundary','outside_branch','node_limit_boundary','truncated_instruction_boundary'}
NO_REPEAT=('残る4callee/中継先/validator正常継続の有限wave採取は保存原本を再利用。'
    '既存nodeと新規共有nodeを再解読せず、未知callee/間接辺/資源境界は未証明で保持。'
    '次は保存byteの契約結合だけを進め、BP/nativeや同じ採取を単独再実行しない。')
SOURCES=tuple('content/modernization/pr16_ring_'+name+'.json' for name in (
    'selector_owners','record_callers','branch_frontier','unread_frontier','patch_owner',
    'transitive_owner','flagset_continuation','callee_bytes','helper_bytes','nonzero_bytes',
    'zero_bytes','owner_frontier','owner_context','effective_frontier'))+tuple('scripts/'+name+'.py' for name in (
    'pr16_ring_effective_frontier','pr16_ring_owner_frontier','pr16_ring_record_callers',
    'pr16_ring_branch_frontier','pr16_ring_zero_bytes','pr16_ring_flagset_continuation',
    'pr16_ring_transitive_owner','pr16_ring_compiled_owner','pr16_ring_selector_followup',
    'pr16_ring_saved_contracts','pr16_ring_owner_context','pr16_ring_effective_contracts'))+(
    '.github/workflows/pr16-ring-callee-bytes.yml',)


def need(ok,text):
    if not ok:raise ValueError(text)


def pointer(value):
    need(type(value)is int and value&1 and ROM_BASE<=value<ROM_END,'Thumb pointer境界')
    return value


def requested_roots(analysis):
    need(analysis['pending_direct_callees']==list(DIRECT),'direct callee差分')
    need(analysis['pending_effective_targets']==list(EFFECTIVE),'effective target差分')
    stops=analysis['validator_success_stops']
    need(len(stops)==2 and {r['version']:r['stopped_at'] for r in stops}==SUCCESS
         and all(r['accepted'] is False for r in stops),'validator正常停止点差分')
    more=analysis['pending_continuations']
    need(type(more)is list and len(more)<=32,'継続予算')
    roots=sorted(set((*DIRECT,*EFFECTIVE,*(v|1 for v in SUCCESS.values()),*more)))
    for value in roots:pointer(value)
    return roots


def boundary_target(edge):
    value=edge.get('target')
    if value is None and edge['kind'] in ('node_limit_boundary','truncated_instruction_boundary'):
        value=edge['site']|1
    return value


def classify_boundaries(rows,known):
    resolved=[];pending=[];seen=set()
    for root in rows:
        for edge in root['boundaries']:
            kind=edge['kind'];target=boundary_target(edge)
            key=(root['entry'],edge['site'],kind,target)
            if key in seen:continue
            seen.add(key)
            row=dict(root=root['entry'],**edge)
            if target is not None:row['effective_target']=target
            if target is not None and target&~1 in known:
                row['binding']='SAVED_NODE_ONLY_NOT_RETURN_OR_LIVE_FRAME_PROOF';resolved.append(row)
            elif kind not in ('return_opcode_not_abi_proof','revisited_node_boundary'):
                pending.append(row)
    return {'saved_boundary_links':resolved,'pending_boundaries':pending,
        'pending_direct_callees':sorted({r['effective_target'] for r in pending if r['kind']=='unread_call'}),
        'pending_continuations':sorted({r['effective_target'] for r in pending
            if r['kind'] in CONTINUATIONS and 'effective_target' in r})}


def bounded_walk(raw,roots,cached,decode,inspect,*,max_rounds=MAX_ROUNDS,
                 max_roots=MAX_ROOTS,max_nodes=MAX_NODES,max_bytes=MAX_BYTES):
    """窓継続のみwave展開する。BL先の自動再帰・保存nodeの再解読は禁止。"""
    need(type(raw)is bytes and 0<len(raw)<=ROM_END-ROM_BASE,'ROM byte入力')
    need(type(roots)in (tuple,list) and roots and len(roots)==len(set(roots)),'root空/重複')
    for value in roots:
        pointer(value);need(value&~1<ROM_BASE+len(raw),'root ROM範囲')
    for value,maximum in ((max_rounds,MAX_ROUNDS),(max_roots,MAX_ROOTS),(max_nodes,MAX_NODES),(max_bytes,MAX_BYTES)):
        need(type(value)is int and 1<=value<=maximum,'wave予算')
    known=copy.deepcopy(cached);fresh={};points=set();rows=[];attempted=set();waves=[]
    queue=sorted(r for r in roots if r&~1 not in known)
    saved_roots=sorted(set(roots)-set(queue))
    for wave in range(max_rounds):
        if not queue:break
        need(len(attempted)+len(queue)<=max_roots,'root総上限')
        attempted.update(queue)
        result=inspect(raw,queue,known,decode)
        new=result['new_nodes']
        need(len({n['address'] for n in new})==len(new),'wave内node重複')
        need(not any(n['address'] in known for n in new),'保存node再解読')
        need(len(fresh)+len(new)<=max_nodes,'node総上限')
        points.update(result['points']);need(len(points)<=max_bytes,'採取byte総上限')
        for node in new:known[node['address']]=fresh[node['address']]=copy.deepcopy(node)
        need([r['entry'] for r in result['roots']]==queue,'wave root差分')
        rows.extend(result['roots'])
        following=set()
        for root in result['roots']:
            for edge in root['boundaries']:
                if edge['kind'] not in CONTINUATIONS:continue
                target=boundary_target(edge)
                if type(target)is int and target&1 and ROM_BASE<=target&~1<ROM_BASE+len(raw):
                    if target&~1 not in known and target not in attempted:following.add(target)
        waves.append({'index':wave,'entries':queue,'new_nodes':len(new),'next_continuations':sorted(following)})
        queue=sorted(following)
    return {'roots':rows,'new_nodes':[fresh[at] for at in sorted(fresh)],'points':sorted(points),
        'waves':waves,'initial_roots':sorted(roots),'saved_roots_reused':saved_roots,
        'deferred_by_wave_limit':queue,'wave_limit_reached':bool(queue),
        'direct_calls_recursively_expanded':0,'saved_nodes_redecoded':0,
        **classify_boundaries(rows,known)}


def preflight(roots,bindings,prior_run_id):
    required={SELF,TEST,WORKFLOW,PRIOR,*SOURCES}
    need(type(bindings)is dict and required<=bindings.keys(),'復元source binding欠落')
    for value in bindings.values():
        need(type(value)is dict and type(value.get('size'))is int and value['size']>=0
             and type(value.get('sha256'))is str and len(value['sha256'])==64,'source identity形式')
    return {'source_bindings':copy.deepcopy(bindings),'roots':list(roots),'max_rounds':MAX_ROUNDS,
        'max_roots':MAX_ROOTS,'max_nodes':MAX_NODES,'max_bytes':MAX_BYTES,'prior_run_id':prior_run_id}


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_effective_frontier as f
    import pr16_ring_owner_frontier as old
    import pr16_ring_record_callers as previous
    import pr16_ring_branch_frontier as windows
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_saved_contracts as vm
    import pr16_ring_effective_contracts as contracts
    reports={p:s.load(p) for p in (*f.REPORTS,f.REPORT)}
    for report in reports.values():saved.bindings_fresh(s.ROOT,report['source_bindings'])
    memory=previous.saved_memory(reports[f.OWNERS])
    for p in (f.CALLERS,f.FRONTIER,f.UNREAD,f.OLD,f.REPORT):
        windows.add_windows(memory,reports[p]['analysis']['new_windows'])
    windows.add_windows(memory,reports[f.REPORT]['analysis']['new_table_windows'])
    graphs=[*reports[f.PATCH]['frontier']['graphs'],*reports[f.TRANSITIVE]['native_owners'].values(),
        *(reports[p]['analysis']['graph'] for p in f.SAMPLES),
        *({'nodes':reports[p]['analysis']['new_nodes']} for p in (f.OLD,f.REPORT))]
    cached=old.cache_nodes(graphs);f.nodes_to_memory(memory,list(cached.values()))
    roots=requested_roots(prior['analysis'])
    bindings={p:s.identity((s.ROOT/p).read_bytes()) for p in (SELF,TEST,WORKFLOW,PRIOR,*SOURCES)}
    (out/'preflight.json').write_bytes(s.stable(preflight(roots,bindings,prior['run_id'])))
    # 次の保存契約実装用。Git管理済みtext/nodeだけ。ROM/save/秘密情報はexportしない。
    paths=(SELF,TEST,vm.SELF,vm.flow.SELF,f.SELF,contracts.SELF,old.SELF)
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8') for p in paths}))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':list(cached.values()),'prior_analysis':prior['analysis']}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(not f.TABLE<=at<f.TABLE+f.TABLE_COUNT*4,'既知jump表data境界')
        return decoder.thumb_instruction(data,at)
    result=bounded_walk(raw,roots,cached,decode,old.inspect_frontier)
    new,reused=old.new_windows(raw,result.pop('points'),memory)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    result.update({'classification':'BOUNDED_REMAINING_CALLEE_AND_VALIDATOR_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'new_windows':new,'saved_bytes_reused':reused,
        'new_node_count':len(result['new_nodes']),'new_window_bytes':sum(w['end']-w['start'] for w in new),
        'cached_node_count':len(cached),'memory_write_sites':[n['address'] for n in result['new_nodes'] if n['memory_write']],
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'validator_success_continuation_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':0,
        'development_failure_preserved':{'run_id':35114642802,
            'source_head':'fe3aadec4dbb154a618f6c2ac2e30b3d2588863f','original_conclusion':'failure',
            'cause':'復元preflightへのsource_bindings渡し漏れ。採取前に停止。',
            'candidate_reconstructions':0,'new_byte_samples':0}})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'pending.json').write_bytes(s.stable({k:result[k] for k in (
        'initial_roots','new_node_count','new_window_bytes','pending_direct_callees','pending_continuations',
        'pending_boundaries','wave_limit_reached','deferred_by_wave_limit')}))
    return result


def summaries(result):
    return (f'残るcallee/validatorの{len(result["initial_roots"])}入口を{len(result["waves"])}有限waveで結合。'
        f'新規{result["new_node_count"]}命令/{result["new_window_bytes"]}byteのみ保存。既存命令再解読0、native0。',
        '今回保存した4callee・0x093BDE81・validator version1/2正常継続のABI/効果を合成検証する。'
        '保存nodeとpending_boundariesを正とし、新規未読callee・間接辺・窓上限を未証明で保持する。'
        '同じ採取/既読ABI/BPを再実行せず、Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
