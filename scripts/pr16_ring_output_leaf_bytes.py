#!/usr/bin/env python3
"""保存glyph展開から判明した256byte変換表と音声3calleeの不足分だけを採取。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_output_frontier as prior
import pr16_ring_followup_v2 as s

BASE='a7387e19b2c4bd3bbebc2392d7b277437d948d35'
SLUG='pr16-ring-output-leaf-bytes'
TASK='PR-P08-7-RING-OUTPUT-LEAF-BYTES'
TITLE='字形の256byte変換表と音声3calleeを保存graphへ限定結合'
SELF='scripts/pr16_ring_output_leaf_bytes.py'
TEST='tests/test_pr16_ring_output_leaf_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-output-leaf-bytes.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_output_leaf_bytes.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('字形256byte変換表と音声3calleeの不足採取は保存原本を再利用する。'
    '旧6983命令/3212byte・636control/627text・受入済みfont/BP/nativeを単独再実行しない。'
    '次は保存字形/cursor/scrollの明示RAM効果を検証し、未読音声/BIOSを成功stubにしない。')
need=s.need
TABLE=0x081cdf40
LENGTH=256
ROOTS=(0x081c0c45,0x081c0fb5,0x081c15f9)
PREFIX={0x08002f64:'044c',0x08002f6c:'1078',0x08002f7c:'1088',0x08002f7e:'000a',
        0x08002f80:'0019',0x08002f82:'0078',0x08002f84:'4000',0x08002f86:'4019',0x08002f88:'0088'}


def plan(nodes,a):
    need(type(nodes)is list and len(nodes)==6983,'保存6983命令')
    by={n['address']:n for n in nodes};need(len(by)==len(nodes),'保存重複')
    need(a.get('saved_node_count')==6983 and a.get('data_window_bytes')==3212,'先行保存数')
    need(a.get('pending_direct_callees')==list(ROOTS),'未読3callee集合')
    for key in('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):
        need(a.get(key)is False,'受入境界 '+key)
    for at,raw in PREFIX.items():need(by.get(at,{}).get('hex')==raw,'保存decoder prefix差分')
    need(by[0x08002f64].get('literal_value')==TABLE,'実変換表pointer')
    need(len(a.get('output_data',[]))==44,'先行44窓')
    for row in a['output_data']:
        need(not(row['start']<TABLE+LENGTH and row['start']+row['length']>TABLE),'既読表再採取')
    for root in ROOTS:
        need(root&~1 not in by,'既読callee再採取')
        need(any(n.get('kind')=='call' and n.get('target')==root&~1 for n in nodes),'保存callsite欠落')
    return {'roots':list(ROOTS),'translation_table':{'start':TABLE,'length':LENGTH},'direct_recursive_layers':0}


def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows']);nodes=[*nodes,*r['analysis']['new_nodes']]
    f.nodes_to_memory(memory,nodes);plan(nodes,r['analysis']);return nodes,memory,context


def analyze(previous,out):
    import pr16_ring_ui_leaf_bytes as leaf
    import pr16_ring_ui_frontier as graph
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=saved_inputs();a=previous['analysis'];p=plan(nodes,a)
    ranges=leaf.data_ranges(context)+[(0x083e30e8,192),(0x0800577c,28),(0x0800582c,32),
        (0x08005ae4,24),(0x081ce54c,8),(prior.prior.prior.TABLE,96),(TABLE,LENGTH)]
    ranges +=[(r['start'],r['length'])for r in a['output_data']]
    forbidden={v for at,n in ranges for v in range(at,at+n)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':p,'candidate':s.CANDIDATE,
        'source_bindings':{x:s.identity((s.ROOT/x).read_bytes())for x in paths}}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data命令化禁止')
        return decoder.thumb_instruction(data,at)
    wave=walk.bounded_walk(raw,p['roots'],old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,max_nodes=1024,max_bytes=8192)
    graph.validate_graph(wave['new_nodes'],nodes,ranges);points=set(wave.pop('points'))|set(range(TABLE,TABLE+LENGTH))
    data=raw[TABLE-0x08000000:TABLE-0x08000000+LENGTH]
    need(len(data)==LENGTH,'変換表長')
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*wave['new_nodes']]
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={k:copy.deepcopy(a[k])for k in('candidate','state_table','dispatch_tables','tables','selected_fonts',
        'control_table','scroll_table','output_data','selected_glyphs','font_data_bases')}
    result.update({**wave,'classification':'SAVED_GLYPH_TRANSLATION_AND_AUDIO_LEAF_BYTES_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(all_nodes),'cached_node_count':len(nodes),'new_node_count':len(wave['new_nodes']),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'glyph_translation':{'start':TABLE,'length':LENGTH,'hex':data.hex(),'identity':s.identity(data)},
        'inherited_pending_boundaries':copy.deepcopy(a['pending_boundaries']),
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'実変換表と音声calleeの有限継続だけ。字形/pixel効果・音声/BIOS・live callerとRing通常取得は未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));prior.prior.b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)));t=prior.prior.text
    for x in(t.prior.prior.prior.SELF,t.prior.prior.SELF,t.prior.SELF,prior.prior.strict.SELF,t.SELF,
        prior.prior.prior.SELF,prior.prior.SELF,prior.SELF,SELF,TEST):
        sources[x]=(s.ROOT/x).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));(out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return(f'字形256byte変換表と音声3calleeを新規{r["new_node_count"]}命令で限定結合。保存総数{r["saved_node_count"]}、既読再解読/native0。',
        '次は保存字形4文字/font2・4・5とspace・cursor/scrollの明示RAM/pixel効果を結合。'
        '音声/BIOS・未読辺はstubにせず、同じ採取・636control/627text・受入済みfont/BP/nativeは再実行しない。'
        '実画面/DMA・全live owner・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
