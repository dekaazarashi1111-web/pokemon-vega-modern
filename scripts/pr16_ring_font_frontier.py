#!/usr/bin/env python3
"""実messageのfont2/4/5と初期化帰還を結合。callbackの直接1段だけ有限採取する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_font_bindings as prior
import pr16_ring_ui_frontier as graph

BASE='1065d278dff98bd44fae0797f93b9503faa1b923'
SLUG='pr16-ring-font-frontier'
TASK='PR-P08-7-RING-FONT-FRONTIER'
TITLE='実message font2/4/5のcallbackとdefault初期化帰還を結合'
SELF='scripts/pr16_ring_font_frontier.py'
TEST='tests/test_pr16_ring_font_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-font-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_font_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=28
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存messageのfont2/4/5だけで絞ったcallbackと直接1段、default initializer帰還を再利用。'
    '候補表の他offsetを有効fontとして採取しない。同じ復元/採取/初期化契約/旧140条件/BP/nativeを単独再実行しない。'
    'callbackの保存命令・分岐表境界をlive初期化/描画完了/Ring通常取得へ昇格しない。')
need=prior.need
ui=prior.prior.prior
INIT=0x080f8a29
TABLE=0x083e30e8
SELECTORS=(2,4,5)
SELECTOR_SITES=((0x080f7dfe,'0421',4),(0x080f7e2e,'0521',5),(0x080f7e56,'0221',2))
CALLS=((0x080f7e00,'fff792ff'),(0x080f7e30,'fff77aff'),(0x080f7e58,'fff766ff'))


def message_selectors(nodes):
    by={n['address']:n for n in nodes};need(len(by)==len(nodes),'保存node重複')
    for at,raw,font in SELECTOR_SITES:
        n=by.get(at,{});need(n.get('hex')==raw and n.get('size')==2 and n.get('kind')=='ordinary','message selector差分')
        need(int.from_bytes(bytes.fromhex(raw),'little')==0x2100|font,'selector r1即値')
    for at,raw in CALLS:
        n=by.get(at,{});need(n.get('hex')==raw and n.get('kind')=='call' and n.get('target')==0x080f7d28,'message call差分')
    for at,raw in ((0x080f7d4a,'6846'),(0x080f7d4c,'4171')):
        need(by.get(at,{}).get('hex')==raw,'template font保存差分')
    return {'selectors':list(SELECTORS),'sites':[r[0]for r in SELECTOR_SITES],
        'template_font_offset':5,'message_path_runtime_observed':False}


def selected_fonts(a,selectors):
    import pr16_ring_followup_v2 as s
    need(selectors==list(SELECTORS),'選択font集合')
    need(a.get('candidate_font_pointer_suppliers_bound')is True and a.get('candidate_font_descriptor_lookup_bound')is True,'保存table結合')
    need(a.get('actual_font_table_length_proven')is False and a.get('initializer_runtime_observed')is False,'実到達/全長の過大主張')
    tables=a.get('tables');need(type(tables)is list and len(tables)==1,'default table集合')
    table=tables[0];data=bytes.fromhex(table['hex'])
    need(table['address']==TABLE and len(data)==192 and s.identity(data)==table['identity'],'実table identity')
    need(table.get('actual_table_length_proven')is False and table.get('supplier_callsites')==[0x080f8a2c],'table出自')
    rows=[]
    for font in selectors:
        record=data[12*font:12*font+12];target=int.from_bytes(record[:4],'little')
        need(target&1 and 0x08000000<=target<0x0a000000 and not TABLE<=target<TABLE+192,'font callback形式')
        need(target in a['pending_font_callback_targets'],'保存callback集合差分')
        rows.append({'selector':font,'record_address':TABLE+font*12,'hex':record.hex(),'callback':target,
            'selected_by_saved_message':True,'runtime_selection_observed':False})
    return rows


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=ui.saved_inputs()
    for path in (prior.prior.REPORT,prior.REPORT):
        r=s.load(path);saved.bindings_fresh(s.ROOT,r['source_bindings']);windows.add_windows(memory,r['analysis']['new_windows'])
    a=s.load(prior.REPORT)['analysis']
    need(len(nodes)==3955 and a['saved_node_count']==3958 and len(a['caller_prefixes'])==1,'保存結合集合')
    nodes=[*nodes,*a['new_nodes'],*(n for row in a['caller_prefixes']for n in (row['supplier'],row['call']))]
    f.nodes_to_memory(memory,nodes);need(len(nodes)==len({n['address']for n in nodes})==3960,'保存3960node')
    return nodes,memory,context


def initializer_contracts(nodes):
    b=prior.b;c=b.Cases(nodes)
    for before in (0,TABLE,prior.GFONTS,0xffffffff):
        m=c.run('default-init-'+str(before),INIT,[(prior.GFONTS,b.word(before),True)],
            writes=[(prior.GFONTS,4,TABLE)],value=b.vm.RETURN)
        need(m.low_sp==b.vm.SP-4 and m.calls==[(0x080f8a2c,prior.SETTER)],'default init frame/call')
    for size in range(4):
        c.run('default-init-short-'+str(size),INIT,[(prior.GFONTS,bytes(size),True)],
            stop=('未許可 write',prior.SETTER+1))
    c.run('default-init-readonly',INIT,[(prior.GFONTS,bytes(4),False)],stop=('未許可 write',prior.SETTER+1))
    return c.rows


def follow_direct(result,known):
    need(result.get('direct_calls_recursively_expanded')==0,'既存waveの再帰禁止')
    roots=result['pending_direct_callees'];need(type(roots)is list and len(roots)==len(set(roots))<=16,'直接callee予算')
    need(all(type(p)is int and p&1 and 0x08000000<=p<0x0a000000 and p&~1 not in known for p in roots),'新規direct境界')
    need(not set(roots)&{ui.LOG|1,ui.FATAL|1},'assertの無関係採取禁止')
    return sorted(roots)


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_ui_leaf_bytes as leaf
    nodes,memory,context=saved_inputs();message=message_selectors(nodes);fonts=selected_fonts(previous['analysis'],message['selectors'])
    roots=sorted({INIT,0x080f8a31,*(r['callback']for r in fonts)})
    known=old.cache_nodes([{'nodes':nodes}]);need(not {p&~1 for p in roots}&known.keys(),'既読root採取禁止')
    ranges=leaf.data_ranges(context)+[(TABLE,192)]
    forbidden={at for start,length in ranges for at in range(start,start+length)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'roots':roots,'message':message,'selected_fonts':fonts,
        'max_direct_layers':1,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba';raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'既知data解読禁止')
        return decoder.thumb_instruction(data,at)
    first=walk.bounded_walk(raw,roots,known,decode,old.inspect_frontier,max_nodes=512,max_bytes=4096)
    (out/'first-frontier.json').write_bytes(s.stable(first))
    for n in first['new_nodes']:known[n['address']]=n
    children=follow_direct(first,known)
    more=walk.bounded_walk(raw,children,known,decode,old.inspect_frontier,max_nodes=1200,max_bytes=8192)if children else None
    all_rows=first['roots']+([]if more is None else more['roots'])
    new=first['new_nodes']+([]if more is None else more['new_nodes']);graph.validate_graph(new,nodes,ranges)
    points=set(first['points']);points.update([]if more is None else more['points'])
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*new]
    conditions=initializer_contracts(all_nodes)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={'classification':'SELECTED_MESSAGE_FONT_CALLBACK_FRONTIER_AND_DEFAULT_INIT_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'message_selector_binding':message,'selected_fonts':fonts,
        'initial_roots':roots,'direct_layer_roots':children,'direct_layers_expanded':int(bool(children)),
        'new_nodes':new,'new_node_count':len(new),'cached_node_count':len(nodes),'saved_node_count':len(all_nodes),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'roots':all_rows,**walk.classify_boundaries(all_rows,{n['address']for n in all_nodes}),
        'default_initializer_contracts':conditions,'contract_cases':len(conditions),
        'conditional_return_cases':sum(r['returned']for r in conditions),'default_initializer':{'entry':INIT,'pointer':TABLE,'global':prior.GFONTS,'stack_bytes':4,'runtime_observed':False},
        'tables':copy.deepcopy(previous['analysis']['tables']),'inherited_assert_callees':previous['analysis']['pending_direct_callees'],
        'inherited_decoder_rejections':copy.deepcopy(previous['analysis']['pending_decoder_rejections']),
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'actual_font_table_length_proven':False,
        'all_live_slot_bounds_proven':False,'all_callers_resolved':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':0,'saved_nodes_redecoded':0,
        'boundary_ja':'有効fontの全長は未証明。保存messageの2/4/5だけを選択しcallback直接1段まで。glyph/dataや未知jumpは補完しない。'}
    (out/'analysis.json').write_bytes(s.stable(result))
    prior.b.export_development(out)
    sources=s.load(str(out.relative_to(s.ROOT)/'development-source.json'))
    for p in (SELF,TEST):sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    (out/'development-source.json').write_bytes(s.stable(sources))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'実messageのfont2/4/5と直接{len(r["direct_layer_roots"])}calleeを新規{r["new_node_count"]}命令で結合。'
        f'default初期化の完全帰還/4byte frameと不足停止を{r["contract_cases"]}条件で検証。native0。',
        '次は今回保存font2/4/5と文字描画delegateのstate/終端/遅延・出力windowを結合する。'
        '未知jump表/未読calleeを保存pendingからだけ進め、他font offsetを実table長と断定しない。'
        '今回採取/default初期化・旧140契約/BP/nativeを単独再実行せず、live初期化・Ring通常取得・policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可')
    support.assert_remote(support.cmd('git','rev-parse','HEAD'),attempts=12)
    support.run(sys.modules[__name__])
