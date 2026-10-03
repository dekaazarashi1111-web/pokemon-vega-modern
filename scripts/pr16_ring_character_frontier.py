#!/usr/bin/env python3
"""保存stateから文字/選択font分岐と待機calleeの未読byteだけを取得する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_font_states as prior
import pr16_ring_followup_v2 as s

BASE='f9cb34283ae54b3423a4c58dfee399fa16c68121'
SLUG='pr16-ring-character-frontier'
TASK='PR-P08-7-RING-CHARACTER-FRONTIER'
TITLE='文字と選択font分岐・待機calleeの未読byteを有限結合'
SELF='scripts/pr16_ring_character_frontier.py'
TEST='tests/test_pr16_ring_character_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-character-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_character_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=22
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('文字8分岐・選択font2/4/5の字形分岐と待機5calleeの有限byteを再利用。'
    '次は明示RAM/狭いstackでstate/終端/遅延/queue結合を検証し、音声globalを暗黙stackゼロで代用しない。'
    '既読採取/受入済みfont・BP/nativeは再実行しない。')
need=s.need
CHAR=0x0800582c
GLYPH=0x08005ae4
SCROLL=0x081ce54c
CALLEES=(0x08004345,0x080054c5,0x080055d5,0x08071a71,0x081c7a85)
SPECS=(('character',CHAR,8,0x08005826,0x08005820,tuple(range(8))),
       ('selected_glyph',GLYPH,6,0x08005ade,0x08005ad8,(2,4,5)))
PREFIX={0x08005816:'f838',0x08005818:'0728',0x0800581a:'00d9',0x0800581c:'56e1',
    0x0800581e:'8000',0x08005820:'0149',0x08005822:'4018',0x08005824:'0068',0x08005826:'8746',
    0x08005acc:'2068',0x08005ace:'0007',0x08005ad0:'000f',0x08005ad2:'0528',0x08005ad4:'29d8',
    0x08005ad6:'8000',0x08005ad8:'0149',0x08005ada:'4018',0x08005adc:'0068',0x08005ade:'8746',
    0x08005bc2:'0b4c',0x08005bc4:'0b4d',0x08005bc6:'2868',0x08005bc8:'007d',
    0x08005bca:'4107',0x08005bcc:'480f',0x08005bce:'0019',0x08005bd0:'0078'}


def bind(nodes,a):
    by={n['address']:n for n in nodes};need(len(by)==len(nodes),'重複node')
    for at,raw in PREFIX.items():need(by.get(at,{}).get('hex')==raw,'保存prefix差分')
    need(by[0x0800581a].get('target')==0x0800581e and by[0x0800581c].get('target')==0x08005acc
        and by[0x08005ad4].get('target')==0x08005b2a,'範囲branch差分')
    for _,address,_,site,literal,_ in SPECS:
        need(by[literal].get('literal_value')==address and by[site].get('kind')=='indirect','literal/間接形式')
        need(any(r.get('site')==site and r.get('kind')=='indirect_boundary'for r in a['pending_boundaries']),'未読table境界欠落')
    need(by[0x08005bc2].get('literal_value')==SCROLL and by[0x08005bc4].get('literal_value')==0x0300504c,'scroll literal差分')
    need(a['pending_direct_callees']==list(CALLEES),'待機callee集合差分')
    need([r['selector']for r in a['selected_fonts']]==[2,4,5] and a['ring_acquisition_accepted']is False,'font/受入境界')
    return {'tables':[{'name':name,'address':at,'count':count,'selected_indices':list(selected),'site':site}
        for name,at,count,site,_,selected in SPECS],'scroll':{'address':SCROLL,'size':8,'mask':7},
        'initial_direct_callees':list(CALLEES),'recursive_direct_layers':0}


def targets(data,count,indices,forbidden):
    need(type(data)is bytes and len(data)==count*4,'table長')
    need(type(count)is int and count in (6,8),'table count')
    need(type(indices)in (list,tuple)and len(indices)==len(set(indices))and all(type(i)is int and 0<=i<count for i in indices),'選択index')
    values=[int.from_bytes(data[4*i:4*i+4],'little')for i in range(count)]
    need(all(0x08000000<=v<0x0a000000 and v%2==0 and v not in forbidden and v+1 not in forbidden for v in values),'target整列/範囲/data')
    return values,sorted({values[i]|1 for i in indices})


def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows']);nodes=[*nodes,*r['analysis']['new_nodes']]
    f.nodes_to_memory(memory,nodes);need(len(nodes)==len({n['address']for n in nodes})==5625,'保存5625node')
    return nodes,memory,context


def analyze(previous,out):
    import pr16_ring_ui_leaf_bytes as leaf
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=saved_inputs();a=previous['analysis'];plan=bind(nodes,a)
    ranges=leaf.data_ranges(context)+[(prior.prior.TABLE,192),(prior.TABLE,28),(CHAR,32),(GLYPH,24),(SCROLL,8)]
    forbidden={p for start,length in ranges for p in range(start,start+length)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':plan,'candidate':s.CANDIDATE,
        'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw);tables=[];roots=list(CALLEES);points=set()
    for row in plan['tables']:
        at=row['address'];data=raw[at-0x08000000:at-0x08000000+row['count']*4]
        values,selected=targets(data,row['count'],row['selected_indices'],forbidden);roots.extend(selected)
        tables.append({**row,'hex':data.hex(),'identity':s.identity(data),'targets':values,'roots':selected});points.update(range(at,at+len(data)))
    data=raw[SCROLL-0x08000000:SCROLL-0x08000000+8];scroll={**plan['scroll'],'hex':data.hex(),'identity':s.identity(data)}
    points.update(range(SCROLL,SCROLL+8));known=old.cache_nodes([{'nodes':nodes}])
    roots=sorted({r for r in roots if r&~1 not in known})
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data解読禁止')
        return decoder.thumb_instruction(data,at)
    wave=walk.bounded_walk(raw,roots,known,decode,old.inspect_frontier,max_nodes=1800,max_bytes=16384)
    prior.prior.graph.validate_graph(wave['new_nodes'],nodes,ranges);points.update(wave['points'])
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*wave['new_nodes']]
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={'classification':'SAVED_CHARACTER_SELECTED_GLYPH_WAIT_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'dispatch_tables':tables,'scroll_table':scroll,
        'state_table':copy.deepcopy(a['state_table']),'selected_fonts':copy.deepcopy(a['selected_fonts']),'tables':copy.deepcopy(a['tables']),
        'initial_roots':roots,'direct_calls_recursively_expanded':0,'roots':wave['roots'],
        'new_nodes':wave['new_nodes'],'new_node_count':len(wave['new_nodes']),'cached_node_count':len(nodes),'saved_node_count':len(all_nodes),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        **walk.classify_boundaries(wave['roots'],{n['address']for n in all_nodes}),
        'inherited_pending_boundaries':copy.deepcopy(a['pending_boundaries']),
        'inherited_assert_callees':a['inherited_assert_callees'],'inherited_decoder_rejections':copy.deepcopy(a['inherited_decoder_rejections']),
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'memory_model_followup_ja':'音声0x03007394/0x030073D4は旧合成stack範囲と重なる。未指定ゼロのprobe帰還は受入せず次工程でstack分離。'}
    (out/'analysis.json').write_bytes(s.stable(result));prior.prior.prior.b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in (prior.prior.SELF,prior.SELF,SELF,TEST):sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));(out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'文字8分岐/選択font2/4/5・待機5calleeを新規{r["new_node_count"]}命令で結合。scroll速度8byteを保存。既読/native再実行0。',
        '次は保存byteだけでstate/終端/遅延/入力待ち/出力queueの正確writeと帰還を結合。'
        '合成stackを狭め音声globalを明示RAMへ分離し、未mapをゼロ成功にしない。残る制御table/glyph/calleeだけをpendingとして保持。'
        '今回採取・受入済みfont/BP/nativeは再実行せずRing通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
