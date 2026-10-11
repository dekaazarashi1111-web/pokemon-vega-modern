#!/usr/bin/env python3
"""残る音声3入口と15indexの参照窓を採取。既知SWIは再採取せず未実行境界へ分類。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_audio_output_contracts as prior
import pr16_ring_followup_v2 as s

BASE='f2b17591d5211de4208f091f07e3e8d23512d8d5'
SLUG='pr16-ring-audio-tail-bytes'
TASK='PR-P08-7-RING-AUDIO-TAIL-BYTES'
TITLE='音声末端3入口と有限周波数参照窓を保存しBIOS境界を分類'
SELF='scripts/pr16_ring_audio_tail_bytes.py'
TEST='tests/test_pr16_ring_audio_tail_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-audio-tail-bytes.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_audio_tail_bytes.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=25
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('音声末端3入口/周波数15index参照窓の有限採取を保存原本で再利用。既知SWIは未実行BIOS境界であって未読再採取対象ではない。'
    '15要素を本来の表長/有効mode全域と断定せず、index0の表前参照を保持。'
    '同じ採取・audio342/164・renderer/cursor/glyph/BP/nativeは単独再実行しない。')
need=s.need
leaf=prior.prior
ROOTS=(0x081c1761,0x081c7a89,0x081c7f39)
CALLS={0x081c157a:(0x081c7f38,'06f0ddfc'),0x081c15b2:(0x081c1760,'00f0d5f8'),0x081c1738:(0x081c7a88,'06f0a6f9')}
TABLE=0x0844e72c
BIOS=0x081c7a88
INHERIT=(*leaf.INHERIT,'song_headers','bios_prefix')


def plan(nodes,a,context):
    prior.validate_inputs(nodes,a,context)
    need(a['contract_cases']==342 and a['conditional_return_cases']==250 and a['pending_stop_cases']==92,'先行契約件数')
    need(a['frequency_table_observed']is False,'同じfrequency窓を再採取禁止')
    by={n['address']:n for n in nodes}
    for at,(target,raw)in CALLS.items():
        n=by.get(at,{})
        need(n.get('kind')=='call'and n.get('target')==target and n.get('hex')==raw,'保存callsite')
    need(by[0x081c1568].get('literal_value')==TABLE,'周波数table根拠')
    need(all(p&~1 not in by for p in ROOTS),'既読入口再採取')
    return {'roots':list(ROOTS),'frequency_window':{'start':TABLE,'length':30,'selected_indices':list(range(1,16)),
        'actual_table_length_proven':False,'all_selected_indices_valid_proven':False,'index_zero_address':TABLE-2},
        'bios_prefix':{'start':BIOS,'length':4},'direct_recursive_layers':0}


def frequency_window(raw):
    data=leaf.span(raw,TABLE,30)
    return {'start':TABLE,'length':len(data),'hex':data.hex(),'identity':s.identity(data),
        'values':[int.from_bytes(data[i:i+2],'little')for i in range(0,30,2)],'selected_indices':list(range(1,16)),
        'actual_table_length_proven':False,'all_selected_indices_valid_proven':False,
        'index_zero_address':TABLE-2,'index_zero_sampled':False,'runtime_frequency_observed':False}


def bios_prefix(raw):
    data=leaf.span(raw,BIOS,4);first=int.from_bytes(data[:2],'little')
    return {'start':BIOS,'length':4,'hex':data.hex(),'identity':s.identity(data),'first_is_swi':first&0xff00==0xdf00,
        'swi_number':first&255 if first&0xff00==0xdf00 else None,'second_is_bx_lr':data[2:]==bytes.fromhex('7047'),
        'executed':False,'return_proven':False}


def classify_pending(old,new,known,bios):
    pending=leaf.pending_union(old,new,known)
    for row in pending:
        target=row.get('effective_target',row.get('target',row.get('site')))
        for prefix in bios:
            if type(target)is int and target&~1==prefix['start'] and prefix['first_is_swi']:
                need(prefix['executed']is False and prefix['return_proven']is False,'BIOS昇格禁止')
                row.update(original_kind=row['kind'],kind='bios_swi_boundary',bios_entry=prefix['start'],
                    swi_number=prefix['swi_number'],executed=False,return_proven=False)
    return pending


def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR)
    saved.bindings_fresh(s.ROOT,r['source_bindings']);plan(nodes,r['analysis'],context)
    return nodes,memory,context


def analyze(previous,out):
    import pr16_ring_ui_frontier as graph
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=saved_inputs();a=previous['analysis'];p=plan(nodes,a,context)
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':p,'candidate':s.CANDIDATE,
        'source_bindings':{x:s.identity((s.ROOT/x).read_bytes())for x in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    freq=frequency_window(raw);bios=bios_prefix(raw)
    ranges=leaf.data_ranges(a,context,a['song_headers'])+[(TABLE,30)]
    forbidden={v for at,n in ranges for v in range(at,at+n)}
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data命令化禁止')
        return decoder.thumb_instruction(data,at)
    wave=walk.bounded_walk(raw,p['roots'],old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
        max_nodes=1024,max_bytes=8192)
    graph.validate_graph(wave['new_nodes'],nodes,ranges)
    points=set(wave.pop('points'))|set(range(BIOS,BIOS+4))|set(range(TABLE,TABLE+30))
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*wave['new_nodes']]
    pending=classify_pending(a['pending_boundaries'],wave['pending_boundaries'],{n['address']for n in all_nodes},[a['bios_prefix'],bios])
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={k:copy.deepcopy(a[k])for k in INHERIT}
    result.update({**wave,'classification':'FINITE_AUDIO_TAIL_FREQUENCY_WINDOW_KNOWN_BIOS_BOUNDARIES_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(all_nodes),'cached_node_count':len(nodes),'new_node_count':len(wave['new_nodes']),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'frequency_window':freq,'audio_bios_prefix':bios,'frequency_table_observed':True,
        'inherited_pending_boundaries':copy.deepcopy(a['pending_boundaries']),'pending_boundaries':pending,
        'pending_direct_callees':sorted({r.get('effective_target',r.get('target'))for r in pending if r['kind']=='unread_call'}),
        'dma_execution_observed':False,'audio_hardware_observed':False,'bios_execution_observed':False,
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'15indexの参照窓は表長・全有効modeの証明ではない。既知SWIを未実行境界へ分類し、除算/音声復帰/実IOは別契約。'})
    (out/'analysis.json').write_bytes(s.stable(result));prior.b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for x in(*SOURCES,SELF,TEST):
        if x.endswith('.py')and(s.ROOT/x).is_file():sources[x]=(s.ROOT/x).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k!='new_nodes'}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'音声末端3入口/周波数15index参照窓を新規{r["new_node_count"]}命令・{r["new_window_bytes"]}byteで保存。'
        f'既知SWIは未実行BIOS境界へ分類。保存総数{r["saved_node_count"]}、既読再解読/native0。',
        '次は保存除算・音声復帰と有限周波数参照を契約結合。既知SWIを成功stubや再採取対象にしない。'
        '周波数表長/全mode有効性、実allocation/callback/実音声/未結合text/live callerは未証明。'
        '同じ採取・audio342/164・renderer/cursor/glyph・受入済みBP/nativeは単独再実行しない。Ring/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
