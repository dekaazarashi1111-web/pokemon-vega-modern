#!/usr/bin/env python3
"""字形/cursor/音声の未読7calleeと実データの限定窓だけを追加する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_control_contracts as prior
import pr16_ring_followup_v2 as s

BASE='f61d2db02cadf65040312af1909588198da337fc'
SLUG='pr16-ring-output-frontier'
TASK='PR-P08-7-RING-OUTPUT-FRONTIER'
TITLE='字形・cursor・音声7calleeと限定実データを保存graphへ結合'
SELF='scripts/pr16_ring_output_frontier.py'
TEST='tests/test_pr16_ring_output_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-output-frontier.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_output_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存7calleeと字形4文字/font2・4・5、cursor画像/animation、symbolと音声表の限定窓を再利用。'
    '旧6534命令・636control/627text契約・font/BP/nativeを単独再実行しない。'
    '字形/cursor/scrollと音声/BIOSの実効果は保存命令と明示RAMから結合し、未読辺をstubにしない。')
need=s.need
FONTS={2:(0x081d6df4,0x081dedf4),4:(0x081def0c,0x081e6f0c),5:(0x081e7024,0x081ef024)}
CHARS=(1,7,8,247)
LITERALS=((0x0800639a,0x081d6df4),(0x080063d2,0x081dedf4),
    (0x080064fe,0x081def0c),(0x08006536,0x081e6f0c),
    (0x080065c2,0x081e7024),(0x080065fa,0x081ef024),
    (0x08005526,0x081ce048),(0x08005530,0x081ce148),(0x08005534,0x081ce548),
    (0x08006246,0x081ce5c0),(0x08006250,0x081ce5f4),
    (0x081c10b4,0x08467edc),(0x081c10b6,0x08467f0c))


def glyph_ranges(font,char):
    need(type(font)is int and font in FONTS and type(char)is int and char in CHARS,'限定font/文字')
    base,width=FONTS[font];at=base+(char//8)*512+(char%8)*32
    return [(f'font{font}-char{char}-left',at,32),(f'font{font}-char{char}-right',at+256,32),
        (f'font{font}-char{char}-width',width+char,1)]


def data_ranges():
    rows=[r for font in FONTS for char in CHARS for r in glyph_ranges(font,char)]
    rows += [('cursor-two-sources-window',0x081ce048,1280),('cursor-animation',0x081ce548,4),
        ('symbol-descriptor-window',0x081ce5c0,52),('symbol-pixels-window',0x081ce5f4,1024),
        ('audio-player-window',0x08467edc,48)]
    rows += [(f'audio-song-{sid}',0x08467f0c+sid*8,8)for sid in(0,5,0x123)]
    need(len({r[0]for r in rows})==len(rows) and sum(r[2]for r in rows)==3212,'data予算')
    points=[p for _,at,n in rows for p in range(at,at+n)]
    need(len(set(points))==len(points),'data窓重複')
    return rows


def plan(nodes,a):
    prior.validate_inputs(nodes,a)
    need(a.get('contract_cases')==636 and a.get('new_node_count')==0,'先行636契約/新規0')
    known={n['address']:n for n in nodes}
    for at,value in LITERALS:need(known.get(at,{}).get('literal_value')==value,'保存literal差分')
    for target in prior.PENDING:
        need(target&~1 not in known,'既読root再採取')
        need(any(n.get('kind')=='call' and n.get('target')==target&~1 for n in nodes),'実callsite欠落')
    return {'roots':list(prior.PENDING),'data_ranges':data_ranges(),'direct_recursive_layers':0}


def saved_inputs():return prior.saved_inputs()


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
        (0x08005ae4,24),(0x081ce54c,8),(prior.prior.TABLE,96)]+[(at,n)for _,at,n in p['data_ranges']]
    forbidden={v for at,n in ranges for v in range(at,at+n)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':p,'candidate':s.CANDIDATE,
        'source_bindings':{x:s.identity((s.ROOT/x).read_bytes())for x in paths}}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data命令化禁止')
        return decoder.thumb_instruction(data,at)
    wave=walk.bounded_walk(raw,p['roots'],old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,max_nodes=2048,max_bytes=16384)
    graph.validate_graph(wave['new_nodes'],nodes,ranges);points=set(wave.pop('points'));data=[]
    for name,at,n in p['data_ranges']:
        part=raw[at-0x08000000:at-0x08000000+n];need(len(part)==n,'data範囲')
        data.append({'name':name,'start':at,'length':n,'hex':part.hex(),'identity':s.identity(part)})
        points.update(range(at,at+n))
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*wave['new_nodes']]
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={k:copy.deepcopy(a[k])for k in('candidate','state_table','dispatch_tables','tables','selected_fonts','control_table','scroll_table')}
    result.update({**wave,'classification':'SAVED_OUTPUT_GLYPH_CURSOR_AUDIO_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(all_nodes),'cached_node_count':len(nodes),'new_node_count':len(wave['new_nodes']),
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'output_data':data,'data_window_bytes':3212,'selected_glyphs':list(CHARS),
        'font_data_bases':{str(k):list(v)for k,v in FONTS.items()},
        'inherited_pending_boundaries':copy.deepcopy(a['pending_boundaries']),
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'7calleeと選択4字形・cursor・symbol/音声の有限窓だけ。窓長を真のtable長や全文字対応/実caller/描画/Ring通常取得へ昇格しない。'})
    (out/'analysis.json').write_bytes(s.stable(result));prior.b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    t=prior.text
    for x in (t.prior.prior.prior.SELF,t.prior.prior.SELF,t.prior.SELF,prior.strict.SELF,t.SELF,prior.prior.SELF,prior.SELF,SELF,TEST):
        sources[x]=(s.ROOT/x).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));(out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'字形/cursor/音声7calleeを新規{r["new_node_count"]}命令と3212byteの限定実dataで結合。保存総数{r["saved_node_count"]}、旧node再解読/native0。',
        '次は保存字形4文字/font2・4・5・cursor/scrollと音声/BIOSの明示RAM契約を結合。'
        '同じ採取・636control/627text・font/BP/nativeを単独再実行しない。未読/間接辺はstubにせず残す。'
        '実画面/DMA・全live owner・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
