#!/usr/bin/env python3
"""保存契約の停止点3個だけを追加採取。旧3918命令と受入済み契約を再実行しない。"""
from __future__ import annotations
import copy
import sys
from pathlib import Path
import pr16_ring_ui_contracts as prior
import pr16_ring_ui_frontier as graph

BASE='614b4ab6f7df02f97de17e5b05a31d8b1bd24482'
SLUG='pr16-ring-ui-leaf-bytes'
TASK='PR-P08-7-RING-UI-LEAF-BYTES'
TITLE='heap split・assert・描画thunkの未読3入口を保存契約へ結合'
SELF='scripts/pr16_ring_ui_leaf_bytes.py'
TEST='tests/test_pr16_ring_ui_leaf_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-ui-leaf-bytes.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_ui_leaf_bytes.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
DIRECT=(0x0800292d,0x081c7a39,0x09378679)
CALLS=((0x080029ba,'fff7b7ff',DIRECT[0]),(0x080029f2,'c5f121f8',DIRECT[1]),
       (0x093785b2,'00f061f8',DIRECT[2]))
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('heap split/assert/render thunkの未読3入口採取は今回原本を再利用。'
    '旧3918命令・pool/heap契約・旧resource/BP/nativeを単独再実行しない。'
    '実gFonts callback table/実allocationは未観測のままで、未読辺を成功stubに置換しない。')
need=prior.need
identity=graph.identity


def plan(a,nodes):
    need(type(a)is dict and a.get('saved_node_count')==3918 and a.get('new_node_count')==0,'先行保存契約数')
    need(a.get('pending_direct_callees')==list(DIRECT) and a.get('pending_continuations')==[]
         and a.get('pending_effective_targets')==[],'未読3入口差分')
    need(type(nodes)is list and len(nodes)==3918,'保存3918命令')
    known={n['address']:n for n in nodes};need(len(known)==3918,'保存重複')
    for k in ('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):
        need(a.get(k)is False,'scope差分 '+k)
    for at,raw,target in CALLS:
        n=known.get(at,{})
        need(n.get('hex')==raw and n.get('kind')=='call' and n.get('target')==target&~1,'保存callsite差分')
    need(not {t&~1 for t in DIRECT}&known.keys(),'既読root再採取')
    return list(DIRECT)


def data_ranges(a):
    import pr16_ring_effective_frontier as f
    table=a['attribute_table']
    need(table['address']==0x08001ac8 and table['count']==10 and table['size']==40,'属性表範囲')
    need(a['dummy_template']['address']==0x081ce040 and a['dummy_template']['size']==8,'dummy範囲')
    ranges=[(t['start'],t['length'])for t in a['tables']]+[(f.TABLE,f.TABLE_COUNT*4),(0x081ce040,8),(0x08001ac8,40)]
    need(all(type(p)is int and type(n)is int and n>0 and 0x08000000<=p<p+n<=0x0a000000 for p,n in ranges),'data allocation範囲')
    return ranges


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    nodes,memory,a=prior.saved_inputs();roots=plan(previous['analysis'],nodes);ranges=data_ranges(a)
    forbidden={p for start,length in ranges for p in range(start,start+length)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'roots':roots,'prior_run':previous['run_id'],
        'data_ranges':ranges,'source_bindings':{p:identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'dataを命令として解読しない')
        return decoder.thumb_instruction(data,at)
    result=walk.bounded_walk(raw,roots,old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
        max_nodes=512,max_bytes=4096)
    new=result['new_nodes'];points=result.pop('points');graph.validate_graph(new,nodes,ranges)
    windows,reused=old.new_windows(raw,points,memory);all_nodes=[*nodes,*new]
    known={n['address']for n in all_nodes};tails=prior.previous.prior.literal_tails(new)
    need(identity(candidate.read_bytes())==identity(raw),'candidate変更')
    result.update({'classification':'SAVED_HEAP_SPLIT_ASSERT_AND_RENDER_THUNK_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'cached_node_count':len(nodes),'saved_node_count':len(all_nodes),
        'new_node_count':len(new),'new_windows':windows,'new_data_windows':[],
        'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'tables':copy.deepcopy(a['tables']),'attribute_table':copy.deepcopy(a['attribute_table']),
        'dummy_template':copy.deepcopy(a['dummy_template']),'literal_tails':tails,
        'pending_effective_targets':sorted({r['target']for r in tails if r['thumb_rom_target'] and r['target']&~1 not in known}),
        'literal_references':[n for n in new if 'literal_address'in n],
        'unbound_runtime_data':copy.deepcopy(a['unbound_runtime_data']),
        'actual_callback_table_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'all_callers_resolved':False,'all_live_frames_proven':False,
        'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':all_nodes,'analysis':result}))
    return result


def summaries(r):
    return (f'未読heap split/assert/render thunkの3入口を結合。新規{r["new_node_count"]}命令/'
        f'{r["new_window_bytes"]}byte、保存総数{r["saved_node_count"]}。旧node再解読/native0。',
        '次は今回保存3入口を使い、heap split完了/不足と実RunTextPrinters active継続を有界検証する。'
        '実gFonts callback tableと新たな未読辺はpendingを保持。旧3918命令・今回採取・'
        'pool/heap/resource/BP/nativeの単独再実行は禁止。Ring通常取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可')
    out=support.ROOT/'.local'/SLUG;out.mkdir(parents=True,exist_ok=True)
    prior.export_development(out)
    sources=support.load(str(out.relative_to(support.ROOT)/'development-source.json'))
    sources[TEST]=(support.ROOT/TEST).read_text(encoding='utf-8')
    (out/'development-source.json').write_bytes(support.stable(sources))
    support.assert_remote(support.cmd('git','rev-parse','HEAD'),attempts=12)
    support.run(sys.modules[__name__])
