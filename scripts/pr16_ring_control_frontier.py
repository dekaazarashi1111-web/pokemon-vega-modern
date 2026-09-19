#!/usr/bin/env python3
"""未読control24表・字形/出力/prompt/音声8calleeを保存graphへ有限結合。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_text_state_contracts as prior
import pr16_ring_followup_v2 as s

BASE='cf95b45fdfcd53ab3cf486f611ec12764a6574b4'
SLUG='pr16-ring-control-frontier'
TASK='PR-P08-7-RING-CONTROL-FRONTIER'
TITLE='control24表と字形・prompt・音声の未読8calleeを有限結合'
SELF='scripts/pr16_ring_control_frontier.py'
TEST='tests/test_pr16_ring_control_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-control-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_control_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('control24表と字形/出力/prompt/音声8calleeの有限採取は保存原本を再利用。'
    '旧5891命令・627text契約・受入済みfont/BP/nativeは単独再実行しない。'
    '次は保存命令のcontrol/prompt/字形を明示RAMで結合し、未読data/音声/BIOSを成功stubにしない。')
need=s.need
TABLE=0x08005894
COUNT=24
DIRECT=(0x080041bd,0x08004c51,0x08005495,0x08006235,0x08006355,0x080064b9,0x0800657d,0x081c10b1)
CALLS=((0x080043b0,'00f04efc',DIRECT[1]),(0x0800555c,'fef72efe',DIRECT[0]),
    (0x08005a8a,'fff703fd',DIRECT[2]),(0x08005ab4,'00f0befb',DIRECT[3]),
    (0x08005b0e,'00f021fc',DIRECT[4]),(0x08005b1e,'00f0cbfc',DIRECT[5]),
    (0x08005b26,'00f029fd',DIRECT[6]),(0x08071a88,'4ff112fb',DIRECT[7]))
PREFIX={0x08005874:'3068',0x08005876:'0378',0x08005878:'0130',0x0800587a:'3060',
    0x0800587c:'581e',0x0800587e:'1728',0x08005880:'00d9',0x08005882:'23e1',
    0x08005884:'8000',0x08005886:'0249',0x08005888:'4018',0x0800588a:'0068',0x0800588c:'8746'}


def bind(nodes,a):
    need(type(nodes)is list and len(nodes)==5891,'保存5891命令')
    by={n['address']:n for n in nodes};need(len(by)==len(nodes),'保存node重複')
    need(a.get('saved_node_count')==5891 and a.get('new_node_count')==0,'先行保存数')
    need(a.get('pending_direct_callees')==list(DIRECT),'未読8callee集合')
    for key in ('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):
        need(a.get(key)is False,'受入境界 '+key)
    for at,raw in PREFIX.items():need(by.get(at,{}).get('hex')==raw,'control prefix差分')
    need(by[0x08005880].get('target')==0x08005884 and by[0x08005882].get('target')==0x08005acc,'control範囲分岐')
    need(by[0x08005886].get('literal_value')==TABLE and by[0x0800588c].get('kind')=='indirect','control表参照')
    for at,raw,target in CALLS:
        n=by.get(at,{})
        need(n.get('hex')==raw and n.get('kind')=='call' and n.get('target')==target&~1,'保存callsite差分')
    need(not {v&~1 for v in DIRECT}&by.keys(),'既読callee再採取')
    return {'table':{'address':TABLE,'count':COUNT,'size':COUNT*4,'selector_min':1,'selector_max':24},
        'direct_callees':list(DIRECT),'saved_nodes':len(nodes),'recursive_direct_layers':0}


def targets(data,forbidden):
    need(type(data)is bytes and len(data)==COUNT*4,'control表96byte')
    values=[int.from_bytes(data[i:i+4],'little')for i in range(0,len(data),4)]
    need(all(0x08000000<=v<0x0a000000 and v%2==0 and v not in forbidden and v+1 not in forbidden for v in values),
        'control target整列/範囲/data')
    return values,sorted({v|1 for v in values})


def saved_inputs():return prior.saved_inputs()


def analyze(previous,out):
    import pr16_ring_ui_leaf_bytes as leaf
    import pr16_ring_ui_frontier as graph
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=saved_inputs();a=previous['analysis'];plan=bind(nodes,a)
    ranges=leaf.data_ranges(context)+[(0x083e30e8,192),(0x0800577c,28),(0x0800582c,32),
        (0x08005ae4,24),(0x081ce54c,8),(TABLE,COUNT*4)]
    forbidden={p for start,length in ranges for p in range(start,start+length)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':plan,'candidate':s.CANDIDATE,
        'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    data=raw[TABLE-0x08000000:TABLE-0x08000000+COUNT*4];values,selected=targets(data,forbidden)
    known=old.cache_nodes([{'nodes':nodes}]);requested=sorted(set((*DIRECT,*selected)))
    roots=[r for r in requested if r&~1 not in known]
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data解読禁止')
        return decoder.thumb_instruction(data,at)
    wave=walk.bounded_walk(raw,roots,known,decode,old.inspect_frontier,max_nodes=1800,max_bytes=16384)
    graph.validate_graph(wave['new_nodes'],nodes,ranges)
    points=set(wave.pop('points'))|set(range(TABLE,TABLE+COUNT*4))
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*wave['new_nodes']]
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    # scroll表は先行で採取済み。再採取せず既存receiptを参照する。
    scroll=s.load(prior.PRIOR)['analysis']['scroll_table'];prior.checked_table(scroll,8)
    result={**wave,'classification':'SAVED_CONTROL_GLYPH_PROMPT_AUDIO_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'control_table':{**plan['table'],'hex':data.hex(),'identity':s.identity(data),
            'targets':values,'roots':selected},'requested_roots':requested,
        'already_saved_roots_reused':[r for r in requested if r&~1 in known],
        'scroll_table':copy.deepcopy(scroll),'state_table':copy.deepcopy(a['state_table']),
        'dispatch_tables':copy.deepcopy(a['dispatch_tables']),'selected_fonts':copy.deepcopy(a['selected_fonts']),
        'tables':copy.deepcopy(a['tables']),'new_node_count':len(wave['new_nodes']),
        'cached_node_count':len(nodes),'saved_node_count':len(all_nodes),'new_windows':windows,
        'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'inherited_pending_boundaries':copy.deepcopy(a['pending_boundaries']),
        'older_pending_boundaries':copy.deepcopy(a['inherited_pending_boundaries']),
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'control表先と8calleeの保存命令結合だけ。字形data/音声/BIOSと実callerの帰還・Ring通常取得は未証明。'}
    (out/'analysis.json').write_bytes(s.stable(result));prior.b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in (prior.prior.prior.SELF,prior.prior.SELF,prior.strict.SELF,prior.SELF,SELF,TEST):
        sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'control24表と字形/出力/prompt/音声8calleeを新規{r["new_node_count"]}命令で有限結合。'
        f'保存総数{r["saved_node_count"]}、旧5891命令再解読/627契約再実行/native0。',
        '次は保存control24分岐・prompt初期化・字形/scroll/音声の明示RAM契約を結合。'
        '未読data/callee/BIOSはpendingを保持し、候補再採取や受入済みtext/font/BP/nativeを単独再実行しない。'
        '実描画/DMA・全live owner・gFonts実初期化・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
