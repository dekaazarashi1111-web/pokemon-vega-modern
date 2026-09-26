#!/usr/bin/env python3
"""gFontsの既知readerに隣接する未読初期化窓とliteral依存だけを有限採取する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_ui_leaf_contracts as prior

BASE='f8cf7d8836830527b3515c5affc1cd9360b8d06d'
SLUG='pr16-ring-font-bytes'
TASK='PR-P08-7-RING-FONT-BYTES'
TITLE='gFonts初期化の未読84byteと有限table候補を固定'
SELF='scripts/pr16_ring_font_bytes.py'
TEST='tests/test_pr16_ring_font_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-font-bytes.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_font_bytes.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('gFonts reader隣接の初期化窓と有限literal依存は保存結果を再利用する。'
    '同じcandidate復元/採取・旧3955命令/609条件・BP/nativeを単独再実行しない。'
    'literal表候補の有限窓を実table長・通常初期化到達・Ring取得へ昇格しない。')
need=prior.need
ROM=0x08000000
LO,HI=0x08002bd4,0x08002c28
MAX_WINDOW,MAX_TABLES,TABLE_BYTES=96,4,192


def read(raw,at,size):
    need(type(raw)is bytes and 0<len(raw)<=0x2000000,'ROM入力')
    need(type(at)is int and type(size)is int and 0<size<=192,'読取引数')
    need(ROM<=at<at+size<=ROM+len(raw),'読取範囲')
    return raw[at-ROM:at-ROM+size]


def probe(raw,lo=LO,hi=HI):
    """PC相対LDR解釈候補だけ。命令境界・table長・writer実到達は主張しない。"""
    need(type(lo)is int and type(hi)is int and lo%2==hi%2==0 and 0<hi-lo<=MAX_WINDOW,'初期化窓')
    window=read(raw,lo,hi-lo);points=set(range(lo,hi));loads=[];candidates={}
    for offset in range(0,len(window),2):
        h=int.from_bytes(window[offset:offset+2],'little')
        if h&0xf800!=0x4800:continue
        at=lo+offset;pool=((at+4)&~3)+(h&255)*4
        literal=read(raw,pool,4);value=int.from_bytes(literal,'little')
        points.update(range(pool,pool+4))
        loads.append({'site':at,'hex':window[offset:offset+2].hex(),'register':(h>>8)&7,
            'literal_address':pool,'literal_value':value,'code_boundary_proven':False})
        # GFONTSはRAMでありROM表として読まない。code窓とliteral自身も表にしない。
        if value%4==0 and ROM<=value and value+TABLE_BYTES<=ROM+len(raw) and not lo<=value<hi and value!=pool:
            candidates.setdefault(value,[]).append(at)
    need(len(candidates)<=MAX_TABLES,'表候補上限')
    tables=[]
    import pr16_ring_followup_v2 as s
    for at,sites in sorted(candidates.items()):
        data=read(raw,at,TABLE_BYTES);points.update(range(at,at+len(data)))
        tables.append({'address':at,'size':len(data),'hex':data.hex(),'identity':s.identity(data),
            'literal_sites':sites,'sampled_record_stride':12,'sampled_record_count':16,
            'actual_table_length_proven':False,'is_font_table_proven':False})
    return {'window':{'start':lo,'end':hi,'hex':window.hex(),'identity':s.identity(window)},
        'literal_candidates':loads,'table_candidates':tables,'points':sorted(points),
        'gfonts_literal_sites':[r['site']for r in loads if r['literal_value']==prior.GFONTS],
        'all_writers_resolved':False,'initializer_runtime_observed':False}


def plan(a,nodes):
    need(type(a)is dict and a.get('saved_node_count')==3955 and a.get('new_node_count')==0,'保存3955命令')
    need(type(nodes)is list and len(nodes)==len({n['address']for n in nodes})==3955,'保存node集合')
    need(a.get('actual_render_frontier',{}).get('global')==prior.GFONTS and
         a['actual_render_frontier'].get('record_stride')==12,'gFonts reader境界')
    for key in ('actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
        need(a.get(key)is False,'受入境界 '+key)
    need(a.get('pending_direct_callees')==[prior.LOG|1,prior.FATAL|1],'assert残辺')
    known={n['address']:n for n in nodes}
    need(known.get(HI,{}).get('hex')=='00b5','DeactivateAllTextPrinters隣接境界')
    need(not any(LO<=at<HI for at in known),'既読初期化窓の重複採取')
    return LO,HI


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_owner_frontier as old
    nodes,memory,a=prior.saved_inputs();lo,hi=plan(previous['analysis'],nodes)
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'window':[lo,hi],'prior_run':previous['run_id'],
        'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    result=probe(raw,lo,hi);points=result.pop('points');windows,reused=old.new_windows(raw,points,memory)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result.update({'classification':'FINITE_FONT_INITIALIZER_LITERAL_PROVENANCE_NOT_RUNTIME_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'new_windows':windows,'saved_bytes_reused':reused,
        'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_node_count':len(nodes),'new_node_count':0,'pending_direct_callees':previous['analysis']['pending_direct_callees'],
        'pending_decoder_rejections':copy.deepcopy(previous['analysis']['pending_decoder_rejections']),
        'actual_render_frontier':copy.deepcopy(previous['analysis']['actual_render_frontier']),
        'actual_callback_table_observed':False,'all_live_slot_bounds_proven':False,
        'all_callers_resolved':False,'all_dispatch_returns_proven':False,'all_live_frames_proven':False,
        'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':0,'saved_nodes_redecoded':0,'new_instructions_decoded':0,
        'boundary_ja':'84byteの限定窓だけを探索。表候補192byteは有限sampleであり16要素の実table長を意味しない。'})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':a}))
    prior.base.export_development(out)
    sources=s.load(str(out.relative_to(s.ROOT)/'development-source.json'))
    for p in (SELF,TEST):sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    (out/'development-source.json').write_bytes(s.stable(sources))
    return result


def summaries(r):
    return (f'gFonts初期化の隣接84byteを限定採取。literal候補{len(r["literal_candidates"])}件・'
        f'有限table候補{len(r["table_candidates"])}件、新規{r["new_window_bytes"]}byte。旧命令再解読/native0。',
        '次は今回保存初期化窓のwriter/callsiteと実12byte font descriptorを保存readerへ結合し、'
        '初期化store・selector・callback境界を検証する。表候補192byteを実table長と断定しない。'
        '同じ採取/候補復元/旧3955命令契約/BP/nativeを単独再実行しない。assert残辺・Ring通常取得・policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可')
    support.assert_remote(support.cmd('git','rev-parse','HEAD'),attempts=12)
    support.run(sys.modules[__name__])
