#!/usr/bin/env python3
"""BIOS後の正確な未供給2slotと、その未読分岐先だけを継続する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_bios_memory_contracts as b
import pr16_ring_followup_v2 as s
import pr16_ring_owner_frontier as frontier

BASE='9406fcab6be820c9979069b9e73771eee0c7e674'
SLUG='pr16-ring-bios-selector-continuation'
TASK='PR-P08-7-RING-BIOS-SELECTOR-CONTINUATION'
TITLE='BIOS後の2属性slotと未読分岐先を供給して次の境界を固定'
SELF='scripts/pr16_ring_bios_selector_continuation.py'
TEST='tests/test_pr16_ring_bios_selector_continuation.py'
WORKFLOW='.github/workflows/pr16-ring-bios-selector-continuation.yml'
PRIOR=b.REPORT
REPORT='content/modernization/pr16_ring_bios_selector_continuation.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=18
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((b.SELF,b.TEST,b.RECORDER,frontier.SELF,*b.SOURCES,
    'scripts/pr16_ring_transitive_owner.py')))
NETWORK=('GitHub connector/Actions、同一hash candidateから新規属性2slotとその未読分岐先だけを取得。'
    '固定mGBA BIOS根拠は先行reportを継承。外部資料の再取得・source-lock変更なし。')
NO_REPEAT=('本工程の2属性slot/新規分岐先byte/結合traceは保存原本から再利用。'
    'BIOS契約32tests/26条件・palette20byte・724条件・1231条件・BP/nativeを単独再実行しない。'
    '次はcaseごとに保存した不足memory/未知nodeを対象にし、候補再構築を不要にできる保存byteを先に確認。')
need=s.need
SLOTS=((0x081534dc,0x081534e4,0x081534f8,0x08153540),
       (0x08001abe,0x08001aec,0x08001af0,0x08001b84))


def plan(previous,c):
    a=previous['analysis'];b.w.validate_inputs(c)
    need(a['candidate']==s.CANDIDATE and a['new_contract_cases']==26,'先行BIOS/candidate')
    need(a['palette_two_copies_conditional_proven'] and a['window_fill_effects_conditional_proven']
        and a['window_12byte_transfer_conditional_proven'],'先行効果')
    need(a['ring_acquisition_accepted'] is False and a['bios_execution_observed'] is False
        and a['task_state1_to2_proven'] is False and a['release_ready'] is False,'先行未受入')
    nodes={n['address']:n for n in c['nodes']};seen=set()
    for row in a['next_unmapped_reads']:
        site=row['stop'][1];fault=row['read_fault']
        need(row['stop'][0]=='未map read' and fault['site']==site and fault['size']==4,'先行read幅/停止')
        seen.add((site,fault['address']))
    need(seen=={(site,at)for site,at,_,_ in SLOTS},'正確な2slot')
    for site,at,_,_ in SLOTS:
        need(nodes[site]['hex']=='0068','slot load命令')
        need(all(not n['address']<=at<n['address']+n['size'] for n in c['nodes']),'slot/保存命令alias')
    p=a['source_palette'];data=bytes.fromhex(p['hex'])
    need(p['start']==b.SOURCE and p['length']==20 and p['identity']==s.identity(data)
        and p['candidate']==s.CANDIDATE,'保存palette identity')
    return [{'site':site,'address':at,'size':4,'target_window':[lo,hi]}for site,at,lo,hi in SLOTS]


def read_slots(raw,rows):
    need(type(raw)is bytes and len(raw)==s.CANDIDATE['size'],'候補幅')
    need(rows==[{'site':site,'address':at,'size':4,'target_window':[lo,hi]}for site,at,lo,hi in SLOTS],'採取計画差分')
    out=[]
    for row in rows:
        at=row['address'];data=raw[at-0x08000000:at-0x08000000+4]
        pointer=int.from_bytes(data,'little');target=pointer&~1;lo,hi=row['target_window']
        need(lo<=target<hi,'属性target所有範囲外')
        out.append(dict(row,hex=data.hex(),identity=s.identity(data),pointer=pointer,target=target))
    return out


def extend(raw,c,slots,decode):
    """未知targetだけを狭い所有範囲内で読む。保存node/calleeには再帰しない。"""
    cached=frontier.cache_nodes([{'nodes':c['nodes']}]);new=[];points=set();roots=[]
    for slot in slots:
        target=slot['target'];lo,hi=slot['target_window']
        need(lo<=target<hi and not target&1,'target整列/所有範囲')
        if target in cached:
            roots.append({'entry':target|1,'saved_target_reused':True,'boundaries':[]});continue
        def bounded(data,at):
            need(target<=at<hi,'decode所有範囲')
            n=decode(data,at);need(at+n['size']<=hi,'命令終端')
            if 'literal_address'in n:
                # literalは当該所有関数の直後まで。ROM全域は探索しない。
                need(lo<=n['literal_address']<=hi+64-4,'literal所有範囲')
            return n
        r=frontier.inspect_frontier(raw,[target|1],cached,bounded,window=min(128,hi-target),limit=32)
        need(len(r['new_nodes'])<=32,'新node予算')
        roots.extend(r['roots']);new.extend(r['new_nodes']);points.update(r['points'])
        cached.update({n['address']:n for n in r['new_nodes']})
    need(len(new)<=64 and len(points)<=256,'全体新規予算')
    return {'new_nodes':new,'roots':roots,'points':sorted(points)}


class Machine(b.Machine):
    def __init__(self,c,segments,args,new_nodes):
        super().__init__(c,segments,args)
        occupied={p for n in c['nodes']for p in range(n['address'],n['address']+n['size'])}
        for n in new_nodes:
            at=n['address'];size=n['size'];span=set(range(at,at+size))
            need(size in(2,4) and not at&1 and len(bytes.fromhex(n['hex']))==size,'新node形式')
            need(not span&occupied,'新node重複');occupied|=span;self.nodes[at]=n


def trace(c,palette,slots,new_nodes,state):
    need(state in(0,1),'限定task状態')
    seg=b.w.fixture(c,state=state,mode=0)
    if state==0:seg+=b.palette_segments(palette)
    seg +=[(r['address'],bytes.fromhex(r['hex']),False)for r in slots]
    m=Machine(c,seg,(0,),new_nodes);error=None
    try:m.run(b.w.task.CALLBACK)
    except ValueError as exc:
        error=str(exc)
        need(error in('未map read','未許可 write','保存node境界で停止')
            or error.startswith('未対応保存命令 '),'想定外trace停止 '+error)
    r=b.snapshot(m,'selector-state'+str(state),error)
    r['reached_new_slot']=any(at==SLOTS[state][1] and size==4 for at,size,_ in m.reads)
    need(r['reached_new_slot'],'新規slot未到達')
    r['registers_at_stop']=m.r[:4]
    r['trace_only_not_independent_transition_oracle']=True
    r['new_saved_sites_executed']=sorted(m.executed_sites&{n['address']for n in new_nodes})
    # 先行transferred_unitsは予定単位数。実完了数はwrites_completedで判定する。
    for e in r['bios_events']:
        e['planned_units']=e.pop('transferred_units')
        e['actually_written_units']=e['writes_completed']
        e['registers_after_semantics']='HOST_MODEL_STATE_NOT_HARDWARE_ABORT_REGISTERS'
    return r


def analyze(previous,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    c=b.context();rows=plan(previous,c)
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'slot_plan':rows,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    slots=read_slots(raw,rows);g=extend(raw,c,slots,decoder.thumb_instruction)
    palette=bytes.fromhex(previous['analysis']['source_palette']['hex'])
    cases=[trace(c,palette,slots,g['new_nodes'],state)for state in(0,1)]
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    memory={p:v for n in c['nodes']for p,v in enumerate(bytes.fromhex(n['hex']),n['address'])}
    for n in c['nodes']:
        if 'literal_address'in n:
            memory.update({n['literal_address']+i:v for i,v in enumerate(n['literal_value'].to_bytes(4,'little'))})
    windows,reused=frontier.new_windows(raw,g.pop('points'),memory)
    result={'classification':'BIOS_SELECTOR_SUPPLY_AND_BOUNDED_TRACE_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'slots':slots,'new_slot_bytes':8,'new_windows':windows,
        'new_window_bytes':8+sum(r['end']-r['start']for r in windows),
        'new_nodes':g['new_nodes'],'new_node_count':len(g['new_nodes']),'roots':g['roots'],
        'saved_node_count':8628+len(g['new_nodes']),'saved_literal_bytes_reused':reused,
        'palette_reused_from':PRIOR,'palette_resampled_bytes':0,'bios_prefix_bytes_resampled':0,
        'bios_contract_tests_replayed':0,'accepted_standalone_contracts_replayed':0,
        'accepted_native_cases_replayed':0,'cases':cases,'new_suffix_traces':2,
        'task_full_boundary':copy.deepcopy(previous['analysis']['task_full_boundary']),
        'rom_changes':0,'candidate_reconstructions':1,'new_emulator_processes':0,
        'saved_nodes_redecoded':0,'full_rom_scans':0,'successful_callee_stubs':0,
        'bios_execution_observed':False,'dma_execution_observed':False,'normal_story_observed':False,
        'task_state1_to2_proven':False,'task_state01_complete_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'先行BIOSの新suffixを2slotだけ供給し追跡。新byteの帰還/状態遷移は独立oracle未受入。'
            '旧BIOS eventのtransferred_unitsは予定数であり、本traceではplanned_unitsと実write数を分離。'
            '部分fault後のregisterはhost診断状態で、実機abort registerではない。'}
    files=exporter.source_export((SELF,TEST,b.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,bios_memory_contracts=previous['analysis'],bios_selector_continuation=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    stops=' / '.join(f'{c["case"]}: '+('条件付き帰還'if c['stop']is None else f'{c["stop"][0]} PC={c["stop"][1]:08X}')for c in r['cases'])
    return (f'BIOS後の2属性slot8byteと未読{r["new_node_count"]}命令を供給。保存palette/prefix再採取0、旧ABI/native再実行0。{stops}。',
        '本reportのcases/read_fault/registers_at_stopとnew_nodes/new_windowsを正本に、残るmemory/ABIを限定検証する。'
        'selector供給で得たtraceだけを全状態遷移・実BIOS・通常story/Ring受入へ昇格しない。'
        '候補の同一再構築・palette/BIOS prefix採取・32tests/26条件/724条件/BP/nativeの単独再実行は禁止。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    sys.modules['pr16_ring_bios_selector_continuation']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
