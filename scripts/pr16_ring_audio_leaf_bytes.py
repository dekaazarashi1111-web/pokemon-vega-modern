#!/usr/bin/env python3
"""音声の未読3callee、BIOS入口、選択3曲headerだけを有限採取。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_audio_boundary_contracts as prior
import pr16_ring_followup_v2 as s

BASE='fe034fdb0220df0d5e20890427dc3ba6eb90136c'
SLUG='pr16-ring-audio-leaf-bytes'
TASK='PR-P08-7-RING-AUDIO-LEAF-BYTES'
TITLE='音声の未読3callee・BIOS入口と選択3曲headerを有限保存'
SELF='scripts/pr16_ring_audio_leaf_bytes.py'
TEST='tests/test_pr16_ring_audio_leaf_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-audio-leaf-bytes.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_audio_leaf_bytes.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=25
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('音声未読3callee・BIOS入口・song0/5/291 headerの有限採取は保存原本を再利用。'
    '既読7091命令・audio164/renderer/cursor/glyph/BP/nativeは単独再実行しない。'
    'SWIを成功stubにせず、track pointerを再生完了やlive音声の受入へ昇格しない。')
need=s.need
ROOTS=(*prior.PENDING,prior.BIOS|1)
CALLS={0x08004462:(prior.BIOS,'c3f10ffb'),0x081c0c6c:(0x081c0c34,'fff7e2ff'),
       0x081c1670:(0x081c16e4,'00f038f8'),0x081c1676:(0x081c1554,'fff76dff')}
SONGS={0:0x0867a280,5:0x0867a360,291:0x08696a14}
ROM_BASE,ROM_END=0x08000000,0x0a000000
MAX_TRACKS=16
INHERIT=('candidate','state_table','dispatch_tables','tables','selected_fonts','control_table',
    'scroll_table','output_data','selected_glyphs','font_data_bases','glyph_translation',
    'stack_residue_contract','fill_neighbor_nibble_effect_preserved','zero_step_scroll_indices')


def span(raw,at,size):
    need(type(raw)is bytes and 0<len(raw)<=ROM_END-ROM_BASE,'ROM byte入力')
    need(type(at)is int and type(size)is int and size>0 and ROM_BASE<=at<at+size<=ROM_BASE+len(raw),'採取範囲')
    return raw[at-ROM_BASE:at-ROM_BASE+size]


def plan(nodes,a,context):
    prior.validate_inputs(nodes,a,context)
    need(a['contract_cases']==164 and a['conditional_return_cases']==138 and a['pending_stop_cases']==26,'先行限定契約')
    need(a['audio_hardware_observed']is False and a['bios_execution_observed']is False,'未受入境界')
    by={n['address']:n for n in nodes}
    need(len(by)==len(nodes),'保存重複')
    for at,(target,encoded)in CALLS.items():
        n=by.get(at,{})
        need(n.get('kind')=='call'and n.get('target')==target and n.get('hex')==encoded,'保存callsite差分')
    need(all(r&~1 not in by for r in ROOTS),'既読入口再採取')
    data=prior.saved_audio_data(a)
    for song,header in SONGS.items():
        table=next(r for r in data if r[0]==0x08467f0c+song*8)
        need(int.from_bytes(table[1][:4],'little')==header,'曲header根拠')
    return {'roots':list(ROOTS),'song_headers':[{'song':k,'start':v}for k,v in SONGS.items()],
        'max_tracks':MAX_TRACKS,'bios_prefix':{'start':prior.BIOS,'length':4},'direct_recursive_layers':0}


def headers(raw):
    result=[]
    for song,at in SONGS.items():
        prefix=span(raw,at,8);count=prefix[0]
        need(count<=MAX_TRACKS,'選択曲の有限track上限')
        data=span(raw,at,8+4*count)
        pointers=[int.from_bytes(data[8+4*i:12+4*i],'little')for i in range(count)]
        need(all(ROM_BASE<=p<ROM_BASE+len(raw)for p in pointers),'track pointer ROM範囲')
        result.append({'song':song,'start':at,'length':len(data),'hex':data.hex(),'identity':s.identity(data),
            'track_count':count,'track_pointers':pointers,'priority_byte':prefix[2],
            'bank_pointer':int.from_bytes(prefix[4:8],'little'),'track_streams_sampled':False,'playback_accepted':False})
    return result


def bios_prefix(raw):
    data=span(raw,prior.BIOS,4);first=int.from_bytes(data[:2],'little')
    return {'start':prior.BIOS,'length':4,'hex':data.hex(),'identity':s.identity(data),
        'first_is_swi':first&0xff00==0xdf00,'swi_number':first&255 if first&0xff00==0xdf00 else None,
        'second_is_bx_lr':data[2:]==bytes.fromhex('7047'),'executed':False,'return_proven':False}


def data_ranges(a,context,selected):
    import pr16_ring_ui_leaf_bytes as leaf
    ranges=leaf.data_ranges(context)
    for t in(a['state_table'],a['control_table'],a['scroll_table'],*a['dispatch_tables'],*a['tables']):
        ranges.append((t['address'],t.get('size',len(bytes.fromhex(t['hex'])))))
    ranges +=[(r['start'],r['length'])for r in(*a['output_data'],a['glyph_translation'],*selected)]
    return sorted(set(ranges))


def pending_union(old,new,known):
    rows=[];seen=set()
    for row in(*old,*new):
        target=row.get('effective_target',row.get('target'))
        if row['kind']=='unread_call'and type(target)is int and target&~1 in known:continue
        key=s.stable(row)
        if key not in seen:rows.append(copy.deepcopy(row));seen.add(key)
    return rows


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
    selected=headers(raw);bios=bios_prefix(raw);ranges=data_ranges(a,context,selected)
    forbidden={v for at,n in ranges for v in range(at,at+n)}
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data命令化禁止')
        # 既存decoderはSWI/undefinedを停止境界として保存する。BIOS成功stubは追加しない。
        return decoder.thumb_instruction(data,at)
    wave=walk.bounded_walk(raw,p['roots'],old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
        max_nodes=1024,max_bytes=8192)
    graph.validate_graph(wave['new_nodes'],nodes,ranges)
    points=set(wave.pop('points'))|set(range(prior.BIOS,prior.BIOS+4))
    for row in selected:points.update(range(row['start'],row['start']+row['length']))
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*wave['new_nodes']]
    pending=pending_union(a['pending_boundaries'],wave['pending_boundaries'],{n['address']for n in all_nodes})
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={k:copy.deepcopy(a[k])for k in INHERIT}
    result.update({**wave,'classification':'FINITE_AUDIO_LEAVES_BIOS_PREFIX_SONG_HEADERS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(all_nodes),'cached_node_count':len(nodes),'new_node_count':len(wave['new_nodes']),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'song_headers':selected,'bios_prefix':bios,'inherited_pending_boundaries':copy.deepcopy(a['pending_boundaries']),
        'pending_boundaries':pending,'pending_direct_callees':sorted({r.get('effective_target',r.get('target'))for r in pending if r['kind']=='unread_call'}),
        'dma_execution_observed':False,'audio_hardware_observed':False,'bios_execution_observed':False,
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'未読音声3calleeとBIOS4byte入口・選択3曲headerだけ。SWI/間接辺/track streamは未結合、実音声やnative Ring受入ではない。'})
    (out/'analysis.json').write_bytes(s.stable(result));prior.b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for x in(*SOURCES,SELF,TEST):
        if x.endswith('.py')and(s.ROOT/x).is_file():sources[x]=(s.ROOT/x).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources))
    compact={k:v for k,v in result.items()if k!='new_nodes'}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':compact,'inherited_analysis':context}))
    return result


def summaries(r):
    return(f'音声未読3callee/BIOS入口/選択3曲headerを新規{r["new_node_count"]}命令・{r["new_window_bytes"]}byteで保存。'
        f'保存総数{r["saved_node_count"]}。既読再解読/native0。',
        '次は保存した音声末端・選択曲headerとBIOS SWI停止の契約結合。BIOSを実行済みにせず、間接callback/実allocationを明示する。'
        '同じ採取・audio164/renderer/cursor/glyph/control/font・受入済みBP/nativeを単独再実行しない。'
        '実音声/全live owner/Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
