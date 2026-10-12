#!/usr/bin/env python3
"""保存UIから特定済みのheap2入口・描画本体・epilogue・10要素表だけを追加する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_ui_delegates as prior

BASE='f15865ba59eb0559d85f1ad890a8010f6fae687f'
SLUG='pr16-ring-ui-runtime-bytes'
TASK='PR-P08-7-RING-UI-RUNTIME-BYTES'
TITLE='特定済みheapと実描画本体・復帰・属性10要素表を未読byteだけで結合'
SELF='scripts/pr16_ring_ui_runtime_bytes.py'
TEST='tests/test_pr16_ring_ui_runtime_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-ui-runtime-bytes.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_ui_runtime_bytes.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
DIRECT=(0x0800295d,0x08002a09,0x09378589)
EFFECTIVE=(0x08002e35,)
TABLE,COUNT=0x08001ac8,10
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('heap2入口・実描画本体・復帰と属性10要素表の採取は保存原本を再利用。'
    '旧3595命令や既読UI/属性/resource/nativeを単独再実行せず、保存pool/heap/callbackの契約へ進む。')
need=prior.need
identity=prior.identity


def plan(a,nodes):
    need(type(a)is dict and a.get('saved_node_count')==3595,'保存3595命令')
    need(a.get('pending_direct_callees')==list(DIRECT),'direct3入口差分')
    need(a.get('pending_effective_targets')==list(EFFECTIVE) and a.get('pending_continuations')==[], '復帰/継続差分')
    need(len(nodes)==3595 and len({n['address']for n in nodes})==3595,'保存node集合')
    for k in ('all_live_slot_bounds_proven','actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
        need(a.get(k)is False,'scope差分 '+k)
    known={n['address']:n for n in nodes}
    for at,raw in ((0x08001ab2,'481e'),(0x08001ab4,'0928'),(0x08001ab6,'65d8'),
                   (0x08001ab8,'8000'),(0x08001aba,'0249'),(0x08001abc,'4018'),
                   (0x08001abe,'0068'),(0x08001ac0,'8746')):
        need(known.get(at,{}).get('hex')==raw,'属性selector/table命令差分')
    need(known[0x08001aba].get('literal_value')==TABLE,'属性table位置差分')
    roots=sorted((*DIRECT,*EFFECTIVE));need(not {r&~1 for r in roots}&known.keys(),'root再採取')
    return roots


def table_targets(raw):
    need(type(raw)is bytes and len(raw)==COUNT*4,'属性表40byte')
    values=[int.from_bytes(raw[i:i+4],'little')for i in range(0,len(raw),4)]
    need(all(0x08000000<=v<0x0a000000 and not v&1 and not TABLE<=v<TABLE+COUNT*4 for v in values),
         '属性表のThumb MOV-PC境界')
    return values


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,_=prior.saved_inputs();r=s.load(prior.REPORT)
    saved.bindings_fresh(s.ROOT,r['source_bindings'])
    for key in ('new_windows','new_data_windows'):windows.add_windows(memory,r['analysis'][key])
    nodes=[*nodes,*r['analysis']['new_nodes']];f.nodes_to_memory(memory,nodes)
    return nodes,memory,copy.deepcopy(r['analysis']['tables'])


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_effective_frontier as f
    nodes,memory,tables=saved_inputs();roots=plan(previous['analysis'],nodes)
    ranges=[(t['start'],t['length'])for t in tables]+[(f.TABLE,f.TABLE_COUNT*4),(prior.DUMMY,8),(TABLE,COUNT*4)]
    forbidden={p for start,length in ranges for p in range(start,start+length)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'roots':roots,'data_ranges':[(TABLE,COUNT*4)],
        'prior_run':previous['run_id'],'source_bindings':{p:identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    table=raw[TABLE-0x08000000:TABLE-0x08000000+COUNT*4];targets=table_targets(table)
    roots=sorted(set((*roots,*(v|1 for v in targets))))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data decode禁止')
        return decoder.thumb_instruction(data,at)
    result=walk.bounded_walk(raw,roots,old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
                             max_nodes=1800,max_bytes=8192)
    new=result['new_nodes'];points=result.pop('points');prior.prior.validate_graph(new,nodes,ranges)
    windows,reused=old.new_windows(raw,points,memory)
    data,reused_data=old.new_windows(raw,list(range(TABLE,TABLE+COUNT*4)),memory)
    all_nodes=[*nodes,*new];known={n['address']for n in all_nodes};tails=prior.literal_tails(new)
    need(identity(candidate.read_bytes())==identity(raw),'candidate変更')
    result.update({'classification':'SAVED_UI_HEAP_RENDER_AND_ATTRIBUTE_TABLE_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'new_windows':windows,'new_data_windows':data,'tables':tables,
        'attribute_table':{'address':TABLE,'count':COUNT,'hex':table.hex(),'targets':targets,**identity(table)},
        'dummy_template':copy.deepcopy(previous['analysis']['dummy_template']),
        'saved_bytes_reused':reused+reused_data,'new_node_count':len(new),
        'new_window_bytes':sum(w['end']-w['start']for w in [*windows,*data]),
        'cached_node_count':len(nodes),'saved_node_count':len(all_nodes),'literal_tails':tails,
        'pending_effective_targets':sorted({r['target']for r in tails if r['thumb_rom_target'] and r['target']&~1 not in known}),
        'literal_references':[n for n in new if 'literal_address'in n],
        'unbound_runtime_data':copy.deepcopy(previous['analysis']['unbound_runtime_data']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'caller_pointer_size_limit_proven':False,'actual_callback_table_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result}))
    return result


def summaries(r):
    return (f'heap2入口・実描画本体と復帰・属性10要素表を結合。新規{r["new_node_count"]}命令/'
        f'{r["new_window_bytes"]}byte、保存総数{r["saved_node_count"]}。既読再解読/native0。',
        '次は保存pool/heap/実RunTextPrintersの条件付き帰還・書込範囲・不足時部分書込を検証する。'
        '実gFonts callback tableと未読calleeはpendingで保持し、仮成功stubを入れない。'
        '今回採取/旧3595命令/旧UI・resource契約/BP/nativeを単独再実行しない。'
        'Ring通常取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
