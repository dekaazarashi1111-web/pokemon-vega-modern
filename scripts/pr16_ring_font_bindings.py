#!/usr/bin/env python3
"""保存setterを検証し、新規caller限定探索からgFontsの実候補表と描画lookupを結合する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_font_bytes as prior
import pr16_ring_record_callers as refs

BASE='cad642b13f4099b0b4f17b35190f7af986d322f1'
SLUG='pr16-ring-font-bindings'
TASK='PR-P08-7-RING-FONT-BINDINGS'
TITLE='gFonts setter・実caller literal・描画descriptorを結合検証'
SELF='scripts/pr16_ring_font_bindings.py'
TEST='tests/test_pr16_ring_font_bindings.py'
WORKFLOW='.github/workflows/pr16-ring-font-bindings.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_font_bindings.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=32
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES,refs.SELF)))
NO_REPEAT=('gFonts setterの3保存命令と新規caller literal/table有限採取・描画lookup結合を再利用。'
    '同じsetter caller探索/候補復元/byte採取/旧3955命令契約/BP/nativeを単独再実行しない。'
    '候補表のoffset lookupを実table全長・live初期化・callback帰還・Ring通常取得へ昇格しない。')
need=prior.need
b=prior.prior.base
GFONTS=prior.prior.GFONTS
SETTER=0x08002c1d
ROM=prior.ROM
MAX_REFS,MAX_TABLES=64,8


def setter_nodes(a):
    """保存84byteから3命令だけを解釈。heap関数や既読nodeは再解読しない。"""
    import pr16_ring_followup_v2 as s
    w=a['window'];raw=bytes.fromhex(w['hex']);at=SETTER&~1
    need(w['start']==prior.LO and w['end']==prior.HI and s.identity(raw)==w['identity'],'初期化窓identity')
    get=lambda p,n:raw[p-w['start']:p-w['start']+n]
    need(get(at,6)==bytes.fromhex('014908607047'),'setter署名')
    pool=((at+4)&~3)+4;need(int.from_bytes(get(pool,4),'little')==GFONTS,'setter global literal')
    need(a['gfonts_literal_sites']==[at],'保存writer literal候補')
    return [{'address':at,'size':2,'hex':'0149','kind':'ordinary','literal_address':pool,'literal_value':GFONTS,'memory_write':False},
        {'address':at+2,'size':2,'hex':'0860','kind':'ordinary','memory_write':True},
        {'address':at+4,'size':2,'hex':'7047','kind':'return','register':14,'memory_write':False}]


def caller_literals(raw,references,setter=SETTER):
    """直前LDR r0+BL一致の条件付きdataflowのみ。実行可能境界/全callerは別問題。"""
    need(type(setter)is int and setter&1 and ROM<=setter<0x0a000000,'setter pointer')
    need(type(references)is list and len(references)<=MAX_REFS,'caller上限')
    complete=[];pending=[];points=set();tables={};seen=set()
    for row in references:
        site=row['site'];key=(site,row['kind']);need(key not in seen,'caller重複');seen.add(key)
        need(row['target']==setter&~1,'caller target差分')
        if row['kind']!='thumb_bl_candidate':pending.append(copy.deepcopy(row));continue
        encoded=prior.read(raw,site,4);hi=int.from_bytes(encoded[:2],'little');lo=int.from_bytes(encoded[2:],'little')
        need(refs.bl_target(site,hi,lo)==setter&~1 and row['encoded']==encoded.hex(),'BL byte/target差分')
        start=max(ROM,site-16);end=min(ROM+len(raw),site+8);points.update(range(start,end))
        if site<ROM+2:pending.append(copy.deepcopy(row));continue
        h=int.from_bytes(prior.read(raw,site-2,2),'little')
        if h&0xff00!=0x4800:pending.append(copy.deepcopy(row));continue
        pool=((site+2)&~3)+(h&255)*4
        data=prior.read(raw,pool,4);value=int.from_bytes(data,'little');points.update(range(pool,pool+4))
        node={'address':site-2,'size':2,'hex':prior.read(raw,site-2,2).hex(),'kind':'ordinary',
            'literal_address':pool,'literal_value':value,'memory_write':False}
        call={'address':site,'size':4,'hex':encoded.hex(),'kind':'call','target':setter&~1,'memory_write':False}
        complete.append({'site':site,'supplier':node,'call':call,'value':value,
            'binding':'IMMEDIATE_LDR_R0_BL_DATAFLOW_CONDITIONAL_ON_ENTRY','runtime_reachable':False})
        if value%4==0 and ROM<=value<value+192<=ROM+len(raw):tables.setdefault(value,[]).append(site)
    need(len(tables)<=MAX_TABLES,'font表候補上限')
    sampled=[]
    import pr16_ring_followup_v2 as s
    for address,sites in sorted(tables.items()):
        data=prior.read(raw,address,192);points.update(range(address,address+192))
        sampled.append({'address':address,'size':192,'hex':data.hex(),'identity':s.identity(data),
            'supplier_callsites':sites,'sampled_records':16,'record_stride':12,
            'actual_table_length_proven':False,'initializer_runtime_observed':False})
    return {'caller_prefixes':complete,'unresolved_callers':pending,'tables':sampled,'points':sorted(points)}


def setter_contracts(nodes):
    cases=b.Cases(nodes)
    values=sorted({0,1,GFONTS,0x02002000,0x08000000,0xffffffff,*[1<<i for i in range(32)],*[0xffffffff^(1<<i)for i in range(32)]})
    for value in values:
        m=cases.run('setter-'+str(value),SETTER,[(GFONTS,b'\xcc'*4,True)],(value,),[(GFONTS,4,value)],value)
        need(m.r[1]==GFONTS and m.low_sp==b.vm.SP,'setter register/SP')
    for count in range(4):
        cases.run('setter-short-'+str(count),SETTER,[(GFONTS,bytes(count),True)],(0x12345678,),stop=('未許可 write',SETTER+1))
    cases.run('setter-readonly',SETTER,[(GFONTS,bytes(4),False)],(0,),stop=('未許可 write',SETTER+1))
    return cases.rows


def prefix_contracts(setter,rows):
    result=[]
    for row in rows:
        nodes=[*setter,row['supplier'],row['call']];c=b.Cases(nodes)
        m=c.run('caller-'+str(row['site']),row['supplier']['address']|1,[(GFONTS,b'\xcc'*4,True)],
            writes=[(GFONTS,4,row['value'])],stop=('保存node境界で停止',row['site']+4))
        need(m.r[13]==b.vm.SP and m.r[4:12]==list(m.original[4:12]) and m.r[14]==row['site']+5,'prefix ABI')
        need(m.read(GFONTS,4)==row['value'] and m.calls==[(row['site'],SETTER)],'prefix pointer供給')
        result.append(dict(c.rows[0],scope_boundary_not_callee_failure=True,stored_pointer=m.read(GFONTS,4)))
    return result


def render_contracts(nodes,tables):
    rows=[];targets=set()
    for table in tables:
        data=bytes.fromhex(table['hex']);address=table['address']
        need(len(data)==192 and table['actual_table_length_proven']is False,'有限table境界')
        for selector in range(16):
            callback=int.from_bytes(data[12*selector:12*selector+4],'little')
            if callback&1 and ROM<=callback<0x0a000000:targets.add(callback)
            # callbackの実行は今回のscope外。削除は成功stubではなく明示境界。
            scoped=[n for n in nodes if n['address']!=(callback&~1)]
            for slot in (0,31):
                for fast in (0,1):
                    segments=prior.prior.render_segments(slot,selector,fast,pointer=address)+[(address,data,False)]
                    c=b.Cases(scoped)
                    stop=('保存node境界で停止',callback&~1)if callback&1 else ('ARM state未対応',0x081c7acc)
                    m=c.run(f'font-{address}-{selector}-{slot}-{fast}',b.RUN,segments,stop=stop)
                    need(m.r[0]==b.POOL+slot*32 and m.r[1]==callback and 0x08002e5e in m.executed_sites,'実lookup/callback引数')
                    rows.append(dict(c.rows[0],selector=selector,callback=callback,table=address,
                        valid_font_id_claimed=False,callback_execution_claimed=False,
                        boundary='CALLBACK_ENTRY_SCOPE'if callback&1 else 'ARM_STATE_REJECTED'))
        for selector in (16,255):
            c=b.Cases(nodes);segments=prior.prior.render_segments(31,selector,pointer=address)+[(address,data,False)]
            c.run(f'font-sample-end-{address}-{selector}',b.RUN,segments,
                stop=('未map read',0x08002e5e),fault={'address':address+12*selector,'size':4,'site':0x08002e5e})
            rows.append(dict(c.rows[0],selector=selector,table=address,boundary='SAMPLE_END_NOT_REAL_TABLE_LENGTH',valid_font_id_claimed=False))
    return rows,sorted(targets)


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_owner_frontier as old
    import pr16_ring_branch_frontier as windows
    nodes,memory,context=prior.prior.saved_inputs();setter=setter_nodes(previous['analysis'])
    windows.add_windows(memory,previous['analysis']['new_windows'])
    need(not {n['address']for n in setter}&{n['address']for n in nodes},'setter二重解読')
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'only_new_reference_target':SETTER,
        'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba';raw=candidate.read_bytes();saved.candidate_identity(raw)
    references=refs.references(raw,[SETTER&~1],max_refs=MAX_REFS)
    found=caller_literals(raw,references);points=found.pop('points');new_windows,reused=old.new_windows(raw,points,memory)
    groups={'setter':setter_contracts(setter),'caller_prefix':prefix_contracts(setter,found['caller_prefixes'])}
    groups['render_lookup'],targets=render_contracts(nodes,found['tables'])
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    rows=[r for rs in groups.values()for r in rs]
    result={'classification':'SAVED_FONT_SETTER_CALLER_TABLE_AND_RENDER_LOOKUP_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'setter_entry':SETTER,'setter_nodes':setter,
        'new_nodes':setter,'saved_node_count':len(nodes)+len(setter),'new_node_count':len(setter),
        'new_windows':new_windows,'new_window_bytes':sum(w['end']-w['start']for w in new_windows),
        'saved_bytes_reused':reused,'references':references,**found,'groups':groups,
        'contract_cases':len(rows),'conditional_return_cases':sum(r['returned']for r in rows),
        'candidate_font_pointer_suppliers_bound':bool(found['tables']),
        'candidate_font_descriptor_lookup_bound':bool(found['tables']),
        'pending_font_callback_targets':targets,'pending_direct_callees':previous['analysis']['pending_direct_callees'],
        'pending_decoder_rejections':copy.deepcopy(previous['analysis']['pending_decoder_rejections']),
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'actual_font_table_length_proven':False,
        'all_live_slot_bounds_proven':False,'all_callers_resolved':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':1,'reference_scan_scope':'NEW_TARGET_08002C1C_CANONICAL_THUMB_BL_AND_ALIGNED_POINTER_ONLY',
        'saved_nodes_redecoded':0,'new_instructions_decoded':3,
        'assumptions_ja':['初期化setterに入力pointer検査はない。全u32へ無条件storeする3命令の局所契約。',
            'canonical BL候補と直前LDR r0だけを結合。computed/ARM/mirrored callerと実到達は未証明。',
            '表の有限192byteを16個の有効fontとは同一視しない。各offsetでlookupされた値と失敗境界だけを保存。',
            '描画は合成slot入力から実hook/readerへの結合。callback本体は明示停止し、帰還/実描画を成功stubにしない。']}
    (out/'analysis.json').write_bytes(s.stable(result))
    b.export_development(out)
    sources=s.load(str(out.relative_to(s.ROOT)/'development-source.json'))
    for p in (SELF,TEST):sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    (out/'development-source.json').write_bytes(s.stable(sources))
    # exporterの3918命令の旧contextではなく、この工程の正確な保存集合で上書きする。
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*setter],'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'gFonts setter3命令とcaller候補{len(r["references"])}件・直前literal供給{len(r["caller_prefixes"])}件を結合。'
        f'表{len(r["tables"])}件の有限lookupとsetterを{r["contract_cases"]}条件で検証。ROM変更/native0。',
        '次は保存された実font表のcallback先を必要selectorから有限採取し、描画state/文字列/出力windowへの作用を結合する。'
        'setter/caller/table探索・今回lookup契約・旧3955命令/609条件/BP/nativeを単独再実行しない。'
        '実table全長・live初期化到達・assert残辺・Ring通常取得・policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可')
    support.assert_remote(support.cmd('git','rev-parse','HEAD'),attempts=12)
    support.run(sys.modules[__name__])
