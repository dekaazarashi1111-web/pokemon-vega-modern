#!/usr/bin/env python3
"""保存font callbackからstate分岐表7項目と直接1段を結合する。nativeは起動しない。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_font_frontier as prior
import pr16_ring_followup_v2 as s

BASE='e58bfa4f3178bbc96962e3bf3f5e3e2823da8c7a'
SLUG='pr16-ring-font-states'
TASK='PR-P08-7-RING-FONT-STATES'
TITLE='font state7分岐と描画delegateを有限結合し境界を保存'
SELF='scripts/pr16_ring_font_states.py'
TEST='tests/test_pr16_ring_font_states.py'
WORKFLOW='.github/workflows/pr16-ring-font-states.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_font_states.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('font2/4/5のstate7分岐表と直接1段を保存。無効state帰還/未map表境界を再利用し、'
    '次は保存state/終端/遅延・window書込を契約結合する。既読命令/default初期化/旧font契約/BP/nativeを再実行しない。')
need=prior.need
TABLE=0x0800577c
COUNT=7
ENTRY=0x0800575d
PREFIX=((0x08005764,'307f'),(0x08005766,'0628'),(0x08005768,'00d9'),
    (0x0800576a,'73e2'),(0x0800576c,'8000'),(0x0800576e,'0249'),
    (0x08005770,'4018'),(0x08005772,'0068'),(0x08005774,'8746'))


def table_plan(nodes,analysis):
    by={n['address']:n for n in nodes};need(len(by)==len(nodes),'保存node重複')
    for at,raw in PREFIX:
        n=by.get(at,{});need(n.get('hex')==raw and n.get('size')==2,'state分岐prefix差分')
    need(by[0x08005768].get('target')==0x0800576c and by[0x0800576a].get('target')==0x08005c54,'state範囲分岐差分')
    n=by[0x0800576e];need(n.get('literal_address')==0x08005778 and n.get('literal_value')==TABLE,'state表literal差分')
    need(by[0x08005774].get('kind')=='indirect' and by[0x08005774].get('register')==0,'state間接形式')
    need(any(r.get('site')==0x08005774 and r.get('kind')=='indirect_boundary' for r in analysis['pending_boundaries']),'保存pending欠落')
    need([r['selector']for r in analysis['selected_fonts']]==[2,4,5],'実message font集合')
    need(analysis.get('ring_acquisition_accepted')is False and analysis.get('initializer_runtime_observed')is False,'native過大主張')
    return {'address':TABLE,'count':COUNT,'stride':4,'state_offset':28,'site':0x08005774,
        'binding':'SAVED_LDRB_CMP6_BLS_LSL2_LITERAL_LDR_MOV_PC','runtime_observed':False}


def table_values(raw,plan,occupied=()):
    need(plan['address']==TABLE and plan['count']==COUNT and plan['stride']==4,'table計画差分')
    need(type(raw)is bytes and len(raw)==COUNT*4,'state表28byte境界')
    forbidden=set(occupied)|set(range(TABLE,TABLE+COUNT*4));targets=[]
    for i in range(COUNT):
        value=int.from_bytes(raw[4*i:4*i+4],'little')
        # MOV PCによるThumb内分岐。偶数entryをそのまま保持し、外部callee帰還とは区別する。
        need(0x08000000<=value<0x0a000000 and value%2==0,'state target整列/範囲')
        need(value not in forbidden and value+1 not in forbidden,'state target/data重複')
        targets.append(value)
    return {**plan,'hex':raw.hex(),'identity':s.identity(raw),'targets':targets,
        'roots':sorted({v|1 for v in targets}),'actual_font_table_length_proven':False}


def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();report=s.load(PRIOR)
    saved.bindings_fresh(s.ROOT,report['source_bindings'])
    windows.add_windows(memory,report['analysis']['new_windows'])
    nodes=[*nodes,*report['analysis']['new_nodes']];f.nodes_to_memory(memory,nodes)
    need(len(nodes)==len({n['address']for n in nodes})==4058,'保存4058node')
    return nodes,memory,context


def boundary_contracts(nodes,fonts):
    b=prior.prior.b;c=b.Cases(nodes);slot=b.POOL
    for font in fonts:
        for flags in (0,0x7f,0x80,0xff):
            for state in (7,8,255):
                pool=bytearray(32);pool[20]=0xa9;pool[21]=flags;pool[28]=state
                writes=[]if flags&128 else [(slot+20,1,0xa0|font['selector']),(slot+21,1,flags|128)]
                m=c.run(f'invalid-state-{font["selector"]}-{flags}-{state}',font['callback'],
                    [(slot,bytes(pool),True)],(slot,),writes,1)
                need(m.low_sp==b.vm.SP-20,'font/delegate frame20')
        for state in range(COUNT):
            pool=bytearray(32);pool[21]=128;pool[28]=state
            m=c.run(f'state-table-unmapped-{font["selector"]}-{state}',font['callback'],
                [(slot,bytes(pool),True)],(slot,),stop=('未map read',0x08005772),
                fault={'address':TABLE+4*state,'size':4,'site':0x08005772})
            need(m.low_sp==b.vm.SP-20 and m.r[13]==b.vm.SP-20,'未map時live frame')
    return c.rows


def direct_roots(result,known):
    need(result.get('direct_calls_recursively_expanded')==0,'自動再帰禁止')
    values=result['pending_direct_callees']
    need(type(values)is list and len(values)==len(set(values))<=32,'直接callee予算')
    need(all(type(v)is int and v&1 and 0x08000000<=v<0x0a000000 and v&~1 not in known for v in values),'direct root形式')
    return sorted(set(values)-{prior.ui.LOG|1,prior.ui.FATAL|1})


def analyze(previous,out):
    import pr16_ring_ui_leaf_bytes as leaf
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=saved_inputs();plan=table_plan(nodes,previous['analysis'])
    ranges=leaf.data_ranges(context)+[(prior.TABLE,192),(TABLE,COUNT*4)]
    forbidden={p for start,length in ranges for p in range(start,start+length)}
    conditions=boundary_contracts(nodes,previous['analysis']['selected_fonts'])
    (out/'preflight.json').write_bytes(s.stable({'plan':plan,'saved_nodes':len(nodes),'contract_cases':len(conditions),
        'max_direct_layers':1,'candidate':s.CANDIDATE}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba';raw=candidate.read_bytes();saved.candidate_identity(raw)
    at=TABLE-0x08000000;table=table_values(raw[at:at+COUNT*4],plan,forbidden)
    known=old.cache_nodes([{'nodes':nodes}])
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'既知data解読禁止')
        return decoder.thumb_instruction(data,at)
    first=walk.bounded_walk(raw,table['roots'],known,decode,old.inspect_frontier,max_nodes=1000,max_bytes=8192)
    (out/'state-frontier.json').write_bytes(s.stable(first))
    for n in first['new_nodes']:known[n['address']]=n
    children=direct_roots(first,known)
    more=walk.bounded_walk(raw,children,known,decode,old.inspect_frontier,max_nodes=1600,max_bytes=12288)if children else None
    rows=first['roots']+([]if more is None else more['roots'])
    new=first['new_nodes']+([]if more is None else more['new_nodes'])
    prior.graph.validate_graph(new,nodes,ranges)
    points=set(range(TABLE,TABLE+COUNT*4))|set(first['points'])|set([]if more is None else more['points'])
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*new]
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={'classification':'SAVED_FONT_STATE_TABLE_FRONTIER_AND_BOUNDARIES_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'state_table':table,'selected_fonts':copy.deepcopy(previous['analysis']['selected_fonts']),
        'tables':copy.deepcopy(previous['analysis']['tables']),'initial_roots':table['roots'],'direct_layer_roots':children,
        'direct_layers_expanded':int(bool(children)),'new_nodes':new,'new_node_count':len(new),
        'cached_node_count':len(nodes),'saved_node_count':len(all_nodes),'new_windows':windows,
        'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'roots':rows,**walk.classify_boundaries(rows,{n['address']for n in all_nodes}),
        'boundary_contracts':conditions,'contract_cases':len(conditions),'conditional_return_cases':sum(r['returned']for r in conditions),
        'inherited_assert_callees':previous['analysis']['inherited_assert_callees'],
        'inherited_decoder_rejections':copy.deepcopy(previous['analysis']['inherited_decoder_rejections']),
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'actual_font_table_length_proven':False,
        'all_live_slot_bounds_proven':False,'all_callers_resolved':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':0,'saved_nodes_redecoded':0,'boundary_ja':'state byte<=6の7entryだけ。文字/control分岐、glyph、未読calleeを推測せずpendingで保持。'}
    (out/'analysis.json').write_bytes(s.stable(result))
    prior.prior.b.export_development(out)
    sources=s.load(str(out.relative_to(s.ROOT)/'development-source.json'))
    for p in (prior.SELF,SELF,TEST):sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    (out/'development-source.json').write_bytes(s.stable(sources))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'font2/4/5のstate7分岐と直接{len(r["direct_layer_roots"])}calleeを新規{r["new_node_count"]}命令で結合。'
        f'無効state帰還/未map表の{r["contract_cases"]}条件を検証。native0。',
        '次は今回保存state0..6の終端・遅延・入力待ちと出力windowの正確なwrite/帰還を結合する。'
        '残る文字/control分岐表と未読calleeは保存pendingからだけ進める。'
        '今回表/命令採取と無効state契約・default初期化・BP/nativeは単独再実行せず、Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12)
    s.run(sys.modules[__name__])
