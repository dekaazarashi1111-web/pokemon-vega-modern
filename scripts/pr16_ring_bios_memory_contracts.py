#!/usr/bin/env python3
"""保存Thumb callerと固定mGBA BIOSの有界メモリ契約。native/実BIOS受入ではない。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_message_window_contracts as w
import pr16_ring_followup_v2 as s

BASE='c84dd781f100c52038f32ad97d1555668b0f0ac9'
SLUG='pr16-ring-bios-memory-contracts'
TASK='PR-P08-7-RING-BIOS-MEMORY-CONTRACTS'
TITLE='BIOSコピー・fillの供給元と部分書込を検証し未読属性表まで継続'
SELF='scripts/pr16_ring_bios_memory_contracts.py'
TEST='tests/test_pr16_ring_bios_memory_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-bios-memory-contracts.yml'
RECORDER='scripts/pr16_ring_bios_record.py'
PRIOR='content/modernization/pr16_ring_message_window_checkpoint.json'
REPORT='content/modernization/pr16_ring_bios_memory_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=(RECORDER,)
SOURCES=tuple(dict.fromkeys((RECORDER,w.SELF,w.REPORT,*w.SOURCES,
    'scripts/pr16_ring_zero_bytes.py','.github/workflows/pr16-ring-callee-bytes.yml',
    'infra/toolchain_manifest.json')))
NETWORK=('GitHub connector/Actions、既存hash固定candidateから新規palette20byteのみ取得。'
    '一次資料: https://github.com/mgba-emu/mgba/blob/0.10.2/src/gba/hle-bios.s '
    '(blob c891479a5ee8efb37eba00365c765d2fa90b12b1) のCpuSet/CpuFastSet/swiBase。'
    '検索語: mGBA 0.10.2 CpuSet CpuFastSet。低20bit count、8word転送、r2/flags復元を採用。'
    'full BIOS/IRQ/実機/サイクル同値性は未証明。source-lock/toolchain変更なし。')
NO_REPEAT=('BIOS0B/0Cの今回メモリ効果・短い供給/readonly部分書込・palette20byte・'
    'state1 fill後の12byte window転送を保存原本から再利用。prefix/724条件/旧1231条件/'
    '候補再構築/BP/nativeを単独再実行しない。次は保存した属性表不足の正確なread境界。'
    '条件付きHLE契約を実BIOS実行/通常story/Ring受入に昇格しない。')
need=s.need
SOURCE=0x083e30ac
DEST1,DEST2=0x020372ec,0x020376ec
LIMIT=2048
PROVENANCE={'repository':'mgba-emu/mgba','ref':'0.10.2','path':'src/gba/hle-bios.s',
    'git_blob':'c891479a5ee8efb37eba00365c765d2fa90b12b1',
    'dispatcher_path':'src/gba/bios.c','dispatcher_git_blob':'1d0c0dd10ad02d26ee18f7fada6bc7377d34e346',
    'mode':'CONDITIONAL_MGBA_0_10_2_HLE_MEMORY_CONTRACT_NOT_BIOS_EXECUTION',
    'preconditions_ja':['割込・DMA介入なし。source/destinationは列挙した非aliasの明示領域。',
        '呼出し中のBIOS固有stack領域はcaller objectと非aliasで使用可能という仮定。',
        'SPSR/例外mode復元は固定swiBaseの契約。実BIOS/IRQ/サイクル/BIOS stack byteは未観測。',
        '不正alignment、予約control bit、2048word超、領域跨ぎは未モデルとして拒否。']}


def region(at,size,write=False):
    need(type(at)is int and type(size)is int and 0<=size<=LIMIT*4 and 0<=at<2**32,'領域引数')
    ranges=[(0x02000000,0x02040000),(0x03000000,0x03008000)]
    if not write:ranges.append((0x08000000,0x0a000000))
    need(any(lo<=at and at+size<=hi for lo,hi in ranges),'BIOS領域外/跨ぎ')
    if write:need(not(at<w.strict.STACK_END and at+size>w.strict.STACK_START),'BIOS destination/予約stack alias')


def transfer(m,site):
    """各要素/8word blockを順に扱う。供給不足後の既完了writeは戻さない。"""
    need(site in (w.BIOS_COPY,w.BIOS_FILL),'未知BIOS service')
    src,dst,ctl=m.r[:3]
    need(all(type(x)is int and 0<=x<2**32 for x in (src,dst,ctl)),'BIOS unsigned引数')
    need(ctl & ~0x050fffff == 0,'BIOS予約control bit')
    fast=site==w.BIOS_FILL;fill=bool(ctl&0x01000000)
    unit=4 if fast or ctl&0x04000000 else 2
    requested=ctl&0xfffff
    count=((requested+7)//8)*8 if fast else requested
    need(count<=LIMIT,'BIOS count予算')
    need(not(src%unit or dst%unit),'BIOS alignment')
    source_bytes=unit if fill else count*unit
    region(src,source_bytes);region(dst,count*unit,True)
    need(not(source_bytes and count and src<dst+count*unit and dst<src+source_bytes),'BIOS source/destination alias')
    before=m.r.copy();flags=copy.deepcopy(m.flags);start=len(m.writes)
    event={'site':site,'service':12 if fast else 11,'args':[src,dst,ctl],
        'source_bytes':source_bytes,'requested_units':requested,'transferred_units':count,
        'unit':unit,'fill':fill,'completed':False,'writes_completed':0,
        'bios_execution_observed':False,'return_is_conditional':True}
    m.bios_events.append(event)
    try:
        fixed=m.read(src,unit) if fill else None
        if fast:
            if fill:m.r[3]=fixed
            for base in range(0,count,8):
                # LDMIAが8wordを読み終える前にSTMIAを始めない。
                values=[fixed]*8 if fill else [m.read(src+(base+i)*4,4) for i in range(8)]
                if not fill:m.r[0]=src+(base+8)*4;m.r[3]=values[0]
                for i,value in enumerate(values):m.write(dst+(base+i)*4,4,value)
                m.r[1]=dst+(base+8)*4
        else:
            for i in range(count):
                value=fixed if fill else m.read(src+i*unit,unit)
                m.write(dst+i*unit,unit,value)
            m.r[3]=0x170
        need(m.r[2]==before[2] and m.r[4:]==before[4:] and m.flags==flags,'BIOS保存契約')
        event['completed']=True
    finally:
        event['writes_completed']=len(m.writes)-start
        event['write_identity']=s.identity(s.stable(m.writes[start:]))
        event['registers_after']=m.r[:4]


class Machine(w.strict.Machine):
    """旧モデルを変更せず、保存LDM/STMと明示BIOS効果だけを接続する。"""
    def __init__(self,c,segments,args=()):
        w.validate_inputs(c)
        super().__init__(c['nodes'],segments,args)
        self.bios_events=[];self.block_events=[]

    def block_transfer(self,h):
        need(h&0xf000==0xc000,'Thumb block形式')
        rb=(h>>8)&7;regs=[i for i in range(8) if h&(1<<i)];load=bool(h&0x0800)
        need(regs and rb not in regs,'Thumb空list/base alias未モデル')
        at=self.r[rb];need(at%4==0,'Thumb block alignment')
        values=[]
        for index in regs:
            if load:self.r[index]=self.read(at,4)
            else:self.write(at,4,self.r[index])
            values.append(self.r[index]);at+=4
        self.r[rb]=at
        self.block_events.append({'site':self.last_pc,'load':load,'base':rb,'registers':regs,'values':values})

    def run(self,entry,max_steps=100000):
        while True:
            try:return super().run(entry,max_steps)
            except ValueError as exc:
                pc=self.last_pc
                if str(exc)=='保存node境界で停止' and pc in (w.BIOS_COPY,w.BIOS_FILL):
                    need(len(self.bios_events)<4,'BIOS呼出予算')
                    transfer(self,pc);entry=self.r[14]
                elif str(exc).startswith('未対応保存命令 '):
                    node=self.nodes[pc];raw=bytes.fromhex(node['hex'])
                    need(len(raw)==2,'Thumb block幅')
                    h=int.from_bytes(raw,'little')
                    if h&0xf000!=0xc000:raise
                    self.block_transfer(h);entry=pc+3
                else:raise


def palette_segments(data,first=20,second=20,readonly=False):
    need(type(data)is bytes and 0<=len(data)<=20,'palette供給幅')
    return [(SOURCE,data,False),(DEST1,bytes(first),not readonly),(DEST2,bytes(second),True)]


def snapshot(m,label,error):
    return {'case':label,'returned':error is None,'stop':None if error is None else [error,m.last_pc],
        'read_fault':m.read_fault,'bios_events':m.bios_events,'block_events':m.block_events,
        'nonstack_write_count':len(m.nonstack_writes()),'write_identity':s.identity(s.stable(m.nonstack_writes())),
        'caller_maximum_stack_bytes':w.strict.STACK_END-m.low_sp,
        'bios_stack_bytes_included':False,'task_state_after':int.from_bytes(m.data(w.task.tasks.TASKS+8,2),'little')
            if w.task.tasks.TASKS+8 in m.mem else None}


def execute(c,label,segments,entry,args):
    m=Machine(c,segments,args);error=None
    try:m.run(entry)
    except ValueError as exc:error=str(exc)
    return m,snapshot(m,label,error)


@functools.lru_cache(maxsize=1)
def context():
    return w.saved_inputs()


@functools.lru_cache(maxsize=1)
def integration():
    """旧724試験は起動せず、以前のBIOS停止を新しいsuffixへ延長する。"""
    c=context();rows=[];data=bytes(range(20))
    for mode in (0,1,3):
        seg=w.fixture(c,state=0,mode=mode)+palette_segments(data)
        m,r=execute(c,f'state0-palette-mode{mode}',seg,w.task.CALLBACK,(0,))
        need(r['stop']==['未map read',0x081534dc] and r['task_state_after']==0,'state0次境界')
        need(len(m.bios_events)==2 and all(e['completed'] for e in m.bios_events),'二重palette')
        need(m.data(DEST1,20)==data==m.data(DEST2,20),'palette二重RAM効果')
        r['synthetic_palette']=True;rows.append(r)
    for mode in (0,2):
        seg=w.fixture(c,state=1,mode=mode)
        m,r=execute(c,f'state1-fill-mode{mode}',seg,w.task.CALLBACK,(0,))
        need(r['stop']==['未map read',0x08001abe] and r['task_state_after']==1,'state1次境界')
        need(len(m.bios_events)==1 and m.bios_events[0]['completed'],'fill完了')
        need(m.bios_events[0]['args'][1:]==[w.PIXELS,0x01000360],'fill引数')
        need(m.data(w.PIXELS,3456)==b'\x11'*3456,'fill画素RAM')
        need(len(m.nonstack_writes())==942,'frame78+fill864')
        need([(e['site'],e['load'])for e in m.block_events]==[(0x08003f80,True),(0x08003f82,False)],'window12byte転送')
        rows.append(r)
    for n in (0,1,2,9,18,19):
        seg=palette_segments(data[:n])
        m,r=execute(c,f'palette-short-source-{n}',seg,w.PALETTE,(SOURCE,224,20))
        need(r['stop']==['未map read',w.BIOS_COPY] and len(m.nonstack_writes())==n//2,'短供給部分書込')
        rows.append(r)
    for n in (0,1,2,9,18,19):
        seg=palette_segments(data,first=n)
        m,r=execute(c,f'palette-short-destination-{n}',seg,w.PALETTE,(SOURCE,224,20))
        need(r['stop']==['未許可 write',w.BIOS_COPY] and len(m.nonstack_writes())==n//2,'短destination部分書込')
        rows.append(r)
    m,r=execute(c,'palette-readonly',palette_segments(data,readonly=True),w.PALETTE,(SOURCE,224,20))
    need(r['stop']==['未許可 write',w.BIOS_COPY] and not m.nonstack_writes(),'readonly')
    rows.append(r)
    for n in (0,1,4,31,32,3452,3455):
        seg=[(at,raw[:n] if at==w.PIXELS else raw,wr)for at,raw,wr in w.fixture(c,state=1)]
        m,r=execute(c,f'fill-short-destination-{n}',seg,w.task.CALLBACK,(0,))
        need(r['stop']==['未許可 write',w.BIOS_FILL] and len(m.nonstack_writes())==78+n//4,'fill部分書込')
        rows.append(r)
    return rows


def supplied_palette(previous,out):
    """候補identityを確認し、新規20byteだけを供給。ROM/prefix/graphはexportしない。"""
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    data=raw[SOURCE-0x08000000:SOURCE-0x08000000+20];need(len(data)==20,'palette窓')
    c=context();seg=w.fixture(c,state=0,mode=0)+palette_segments(data)
    m,row=execute(c,'candidate-palette-state0-mode0',seg,w.task.CALLBACK,(0,))
    need(row['stop']==['未map read',0x081534dc] and len(m.bios_events)==2,'実candidate二重palette継続')
    need(m.data(DEST1,20)==data==m.data(DEST2,20),'実palette二重効果')
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    row['synthetic_palette']=False
    return {'start':SOURCE,'length':20,'hex':data.hex(),'identity':s.identity(data),
        'candidate':dict(s.CANDIDATE),'supplier':'HASH_VERIFIED_CANDIDATE_READ_ONLY_EXACT_20_BYTES'},row


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    rows=copy.deepcopy(integration());need(integration.cache_info().misses==1,'結合二重実行禁止')
    palette,row=supplied_palette(previous,out);rows.append(row)
    result={'classification':'CONDITIONAL_BIOS_MEMORY_AND_CALLER_SUFFIX_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'provenance':PROVENANCE,'cases':rows,'new_contract_cases':len(rows),
        'source_palette':palette,'saved_node_count':8628,'new_node_count':0,'new_window_bytes':20,
        'bios_prefix_bytes_resampled':0,'saved_nodes_redecoded':0,'candidate_reconstructions':1,
        'rom_changes':0,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,'successful_callee_stubs':0,
        'palette_two_copies_conditional_proven':True,'window_fill_effects_conditional_proven':True,
        'window_12byte_transfer_conditional_proven':True,'palette_supplier_identity_verified':True,
        'task_state1_to2_proven':False,'task_state01_complete_proven':False,
        'normal_story_observed':False,'initializer_runtime_observed':False,'task_scheduler_execution_observed':False,
        'bios_execution_observed':False,'dma_execution_observed':False,'ring_acquisition_accepted':False,
        'release_ready':False,'actual_callback_table_observed':False,
        'task_full_boundary':copy.deepcopy(previous['analysis']['task_full_boundary']),
        'next_unmapped_reads':[{'case':r['case'],'stop':r['stop'],'read_fault':r['read_fault']}
            for r in rows if r['stop'] and r['stop'][1]in(0x081534dc,0x08001abe)],
        'boundary_ja':'固定HLEの明示メモリ契約。live BIOS stack/IRQ/実BIOSの観測ではない。'
            'palette二重RAMコピー後は選択表、state1 frame/fill/window転送後は属性10の表で停止。'
            'state0/1完了・queue転送・通常story/Ringは未受入。'}
    files=exporter.source_export((SELF,TEST,RECORDER,w.SELF,*SOURCES))
    files['saved-context.json']=s.stable(dict(context(),bios_memory_contracts={k:v for k,v in result.items()if k!='cases'}))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return (f'BIOS0B/0Cの有界メモリ契約を{r["new_contract_cases"]}新規結合条件で検証。'
        '同一候補palette20byteを新規供給し020372EC/020376ECへの両コピーを確認。'
        'state1は78frame+864fill書込とwindow12byte転送後、属性10の表読出で停止。native/ROM変更0。',
        '次は本reportのnext_unmapped_readsにある081534DC/08001ABEの正確な属性表slotを根拠付きで供給する。'
        '保存済palette20byte/BIOS prefix/今回契約/724条件/旧1231条件/BP/nativeを単独再実行しない。'
        'state1→2、BIOS stack/IRQ、通常story/Ring/live初期化、task満杯busy2のlivenessは未受入を保持。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    sys.modules['pr16_ring_bios_memory_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
