#!/usr/bin/env python3
"""実RunTextPrinters中継と未読6callee・dummy templateだけを追加採取。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_ui_frontier as prior

BASE='c063e17cc56aa00b17edef88c33a4542912e589a'
SLUG='pr16-ring-ui-delegates'
TASK='PR-P08-7-RING-UI-DELEGATES'
TITLE='実text中継とwindow allocationの6calleeを保存命令へ結合'
SELF='scripts/pr16_ring_ui_delegates.py'
TEST='tests/test_pr16_ring_ui_delegates.py'
WORKFLOW='.github/workflows/pr16-ring-ui-delegates.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_ui_delegates.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
CALLEES=(0x08001aa9,0x08001fa1,0x08002009,0x08002b9d,0x08002bc5,0x08004a01)
HOOK=0x09378a43
DUMMY=0x081ce040
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('実RunTextPrinters転送先0x09378A43とwindow6callee・dummy template採取は保存原本を再利用。'
    '旧3496命令/7入口/旧resource契約/BP/nativeを単独再実行しない。allocatorや間接辺を成功stubへ置換しない。')
need=prior.need
identity=prior.identity


def hook_target(nodes):
    known={n['address']:n for n in nodes}
    for at,raw in ((0x08002dd0,'f0b5'),(0x08002dd2,'014b'),(0x08002dd4,'1847')):
        need(known.get(at,{}).get('hex')==raw,'実hook命令差分')
    n=known[0x08002dd2]
    need(n.get('literal_address')==0x08002dd8 and n.get('literal_value')==HOOK,'実hook literal差分')
    need(known[0x08002dd4].get('register')==3,'実hook register差分')
    return HOOK


def plan(a,nodes):
    need(type(a)is dict and a.get('saved_node_count')==3496,'保存3496命令')
    need(a.get('pending_direct_callees')==list(CALLEES) and a.get('pending_continuations')==[], '未読6callee差分')
    need(len(nodes)==3496 and len({n['address']for n in nodes})==3496,'保存node集合')
    for k in ('all_live_slot_bounds_proven','actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
        need(a.get(k)is False,'scope差分 '+k)
    roots=sorted((*CALLEES,hook_target(nodes)))
    need(not {r&~1 for r in roots}&{n['address']for n in nodes},'root再採取')
    return roots


def literal_tails(nodes):
    known={n['address']:n for n in nodes};rows=[]
    for at,n in sorted(known.items()):
        if n['kind']!='indirect' or n['size']!=2:continue
        h=int.from_bytes(bytes.fromhex(n['hex']),'little')
        if h&0xff87!=0x4700:continue
        previous=known.get(at-2)
        if not previous or previous['size']!=2 or 'literal_value'not in previous:continue
        ph=int.from_bytes(bytes.fromhex(previous['hex']),'little')
        if ph&0xf800!=0x4800 or (ph>>8)&7!=(h>>3)&15:continue
        target=previous['literal_value']
        need(type(target)is int and 0<=target<=0xffffffff,'literal u32')
        rows.append({'load_site':at-2,'site':at,'target':target,
            'thumb_rom_target':bool(target&1 and 0x08000000<=target<0x0a000000),
            'binding':'FALLTHROUGH_LITERAL_BX_NOT_ALL_ENTRY_PATHS_OR_RETURN_PROOF'})
    return rows


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,_=prior.saved_inputs();r=s.load(prior.REPORT)
    saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows'])
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
    ranges=[(t['start'],t['length'])for t in tables]+[(f.TABLE,f.TABLE_COUNT*4),(DUMMY,8)]
    forbidden={p for start,length in ranges for p in range(start,start+length)}
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'roots':roots,'data_ranges':[(DUMMY,8)],
        'prior_run':previous['run_id'],'source_bindings':{p:identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data decode禁止')
        return decoder.thumb_instruction(data,at)
    result=walk.bounded_walk(raw,roots,old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
                             max_nodes=1800,max_bytes=8192)
    new=result['new_nodes'];points=result.pop('points');prior.validate_graph(new,nodes,ranges)
    windows,reused=old.new_windows(raw,points,memory)
    data,reused_data=old.new_windows(raw,list(range(DUMMY,DUMMY+8)),memory)
    template=raw[DUMMY-0x08000000:DUMMY-0x08000000+8]
    need(len(template)==8,'dummy template範囲')
    all_nodes=[*nodes,*new];known={n['address']for n in all_nodes};tails=literal_tails(new)
    pending=sorted({r['target']for r in tails if r['thumb_rom_target'] and r['target']&~1 not in known})
    need(identity(candidate.read_bytes())==identity(raw),'candidate変更')
    result.update({'classification':'SAVED_ACTUAL_UI_DELEGATES_NOT_LIVE_ALLOCATION_OR_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'new_windows':windows,'new_data_windows':data,'tables':tables,
        'dummy_template':{'address':DUMMY,'hex':template.hex(),**identity(template)},
        'saved_bytes_reused':reused+reused_data,'new_node_count':len(new),
        'new_window_bytes':sum(w['end']-w['start']for w in [*windows,*data]),
        'cached_node_count':len(nodes),'saved_node_count':len(all_nodes),'literal_tails':tails,
        'pending_effective_targets':pending,'actual_run_text_printers_target':HOOK,
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
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in (SELF,TEST)}))
    return result


def summaries(r):
    return (f'実RunTextPrinters中継0x09378A43とwindow6calleeを結合。新規{r["new_node_count"]}命令/'
        f'{r["new_window_bytes"]}byte、dummy template8byte。純正symbol名だけで実本体を扱わない。',
        '次は保存text/window初期化・満杯拒否・null解放・実RunTextPrinters中継の契約を結合。'
        '未読heap/callback/実gFonts tableはpendingを正とし、stubで通過させない。'
        '今回delegate採取・旧7入口/3496命令・resource契約・BP/nativeを単独再実行しない。'
        'Ring通常取得・装備実戦・保存とpolicy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
