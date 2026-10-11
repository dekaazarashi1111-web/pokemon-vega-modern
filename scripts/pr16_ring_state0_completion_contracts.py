#!/usr/bin/env python3
"""保存state0の未観測option/選択行を結合。通常story/実BIOS受入とは分離する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_state0_palette_supply as prior
import pr16_ring_followup_v2 as s

BASE='0e6bb070944df7439977426fcc31638c6c334801'
SLUG='pr16-ring-state0-completion-contracts'
TASK='PR-P08-7-RING-STATE0-COMPLETION-CONTRACTS'
TITLE='state0のoption境界・選択行供給・state1帰還を独立oracleで検証'
SELF='scripts/pr16_ring_state0_completion_contracts.py'
TEST='tests/test_pr16_ring_state0_completion_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-state0-completion-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_state0_completion_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.TEST,*prior.SOURCES)))
NETWORK='GitHub connector/Actions。固定candidateからdefault選択行8byteとそのpalette32byteだけを有限供給。保存20/32byte・slot/node再採取0、外部資料/source-lock変更0。'
NO_REPEAT='state0のoption全256値・default行/実palette・独立write oracleによるstate0→1を保存原本から再利用。state1→2は先行受入の継承のみ。次は通常story/live pointer初期化・task入場と保存callerの接続。option index0..31の算術は全32行有効証明ではない。BP/旧BIOS/native/同一候補再構築を単独再実行しない。'
need=s.need
b=prior.bios
w=prior.w
GLOBAL=0x0300504c
OBJECT=0x02010000
OPTION=OBJECT+0x14
ROW=0x0843fac4
WRAPPER=0x081530e1
DEST1,DEST2=b.DEST1,b.DEST2


@functools.lru_cache(maxsize=1)
def inputs():
    c=b.context();a=s.load(PRIOR)['analysis'];old=s.load(prior.selector.REPORT)['analysis']
    w.validate_inputs(c)
    need(a['candidate']==s.CANDIDATE and a['palette32_two_copies_conditional_proven'] is True,'先行供給')
    need(a['state0_to1_proven'] is False and a['ring_acquisition_accepted'] is False
        and a['bios_execution_observed'] is False and a['release_ready'] is False,'先行未受入')
    need(a['next_read']=={'address':GLOBAL,'size':4,'site':0x081530f4},'次のpointer')
    for key,at,n in(('saved_palette20',b.SOURCE,20),('source_palette32',prior.SOURCE,32)):
        row=a[key];raw=bytes.fromhex(row['hex'])
        need(row['start']==at and row['length']==n and row['identity']==s.identity(raw)
            and row['candidate']==s.CANDIDATE,'保存palette出自')
    nodes={n['address']:n for n in c['nodes']}
    for at,raw in((0x081530f4,'0968'),(0x081530f6,'097d'),(0x081530f8,'c908'),
                  (0x081530b4,'e400'),(0x081530b8,'0968'),(0x081530c8,'2068')):
        need(nodes[at]['hex']==raw,'option/row保存命令 '+hex(at))
    return c,a,old


class Machine(prior.selector.Machine):
    """旧4呼出モデルは変更せず、正確な6呼出列だけを許可する。履歴を消さない。"""
    def __init__(self,c,seg,args,nodes,plan=()):
        super().__init__(c,seg,args,nodes)
        need(type(plan)in(tuple,list)and len(plan)<=6,'BIOS有限列')
        self.bios_plan=tuple(tuple(v)for v in plan)

    def run(self,entry,max_steps=100000):
        while True:
            try:return w.strict.Machine.run(self,entry,max_steps)
            except ValueError as exc:
                pc=self.last_pc
                if str(exc)=='保存node境界で停止' and pc in(w.BIOS_COPY,w.BIOS_FILL):
                    index=len(self.bios_events)
                    need(index<len(self.bios_plan)and pc==w.BIOS_COPY
                        and tuple(self.r[:3])==self.bios_plan[index],'BIOS許可列/予算')
                    b.transfer(self,pc);entry=self.r[14]
                elif str(exc).startswith('未対応保存命令 '):
                    raw=bytes.fromhex(self.nodes[pc]['hex']);h=int.from_bytes(raw,'little')
                    if len(raw)!=2 or h&0xf000!=0xc000:raise
                    self.block_transfer(h);entry=pc+3
                else:raise


def selected_row(raw):
    need(type(raw)is bytes and len(raw)==8,'選択行は8byte限定')
    graphics=int.from_bytes(raw[:4],'little');palette=int.from_bytes(raw[4:],'little')
    for at,size in((graphics,288),(palette,32)):
        need(at%4==0 and 0x08000000<=at and at+size<=0x0a000000,'選択行pointer範囲/整列')
    return {'address':ROW,'length':8,'hex':raw.hex(),'identity':s.identity(raw),
        'graphics':graphics,'palette':palette,'index':0,'candidate':dict(s.CANDIDATE)}


def select_case(c,old,value,*,pointer=OBJECT,pointer_size=4,option_present=True):
    need(type(value)is int and 0<=value<256,'option byte')
    seg=[(w.TABLE,bytes.fromhex(c['window_frontier']['selector0']['hex']),False),
         (w.b.WINDOWS,w.b.template(bg=0),False),(GLOBAL,w.b.word(pointer)[:pointer_size],False)]
    if option_present:seg.append((OPTION,bytes([value]),False))
    if pointer_size<4:fault={'address':GLOBAL,'size':4,'site':0x081530f4}
    elif pointer!=OBJECT or not option_present:fault={'address':pointer+0x14,'size':1,'site':0x081530f6}
    else:fault={'address':ROW+(value>>3)*8,'size':4,'site':0x081530b8}
    m=Machine(c,seg,(0,532,224),old['new_nodes']);error=None
    try:m.run(WRAPPER)
    except ValueError as exc:error=(str(exc),m.last_pc)
    need(error==('未map read',fault['site'])and m.read_fault==fault,'option停止境界')
    image=prior.effect(m,seg,[])
    need(not m.bios_events,'option prefixでBIOS禁止')
    return {'option_byte':value,'raw_index':value>>3,'stop':list(error),'read_fault':fault,
        'object_sha256':image,'nonstack_writes':0,'valid_table_length_proven':False,'native_observation':False}


@functools.lru_cache(maxsize=1)
def option_contracts():
    c,_,old=inputs();rows=[select_case(c,old,v)for v in range(256)]
    rows +=[select_case(c,old,0,pointer_size=n)for n in range(4)]
    rows +=[select_case(c,old,0,pointer=v)for v in(0,OBJECT+0x100)]
    rows +=[select_case(c,old,0,option_present=False)]
    need(len(rows)==263,'option263契約');return rows


def segments(c,a,old,row,data,options):
    opt=dict(task_id=0,bg=0,mode=0,head=0,occupied=(),bank=0,enabled=0,flags=1,option=0,**{})
    need(type(options)is dict and set(options)<=set(opt),'未対応state0 parameter');opt.update(options)
    need(0<=opt['task_id']<16 and 0<=opt['bg']<4 and opt['mode']in(0,1,3,255)
        and 0<=opt['option']<8,'default行専用')
    need(type(data)is bytes and len(data)==32,'default palette幅')
    seg=w.fixture(c,state=0,**{k:v for k,v in opt.items()if k!='option'})
    seg +=[(b.SOURCE,bytes.fromhex(a['saved_palette20']['hex']),False),
        (prior.SOURCE,bytes.fromhex(a['source_palette32']['hex']),False),
        (DEST1,b'\xa5'*32,True),(DEST2,b'\x5a'*32,True),
        (prior.DEST1,b'\xa6'*32,True),(prior.DEST2,b'\x6a'*32,True),
        (GLOBAL,w.b.word(OBJECT),False),(OPTION,bytes([opt['option']]),False),
        (ROW,bytes.fromhex(row['hex']),False)]
    seg +=[(v['address'],bytes.fromhex(v['hex']),False)for v in old['slots']]
    # 保存paletteとのaliasは同一byteのときのみ既存segmentを再利用する。
    matched=[(at,raw)for at,raw,_ in seg if at==row['palette']]
    if matched:need(len(matched)==1 and matched[0][1]==data,'palette alias差分')
    else:seg.append((row['palette'],data,False))
    return seg,opt


def expected(seg,a,row,data,opt):
    e=w.b.Expected(seg)
    def palette(raw):
        for dest in(DEST1,DEST2):
            for i in range(0,len(raw),2):e.write(dest+i,2,int.from_bytes(raw[i:i+2],'little'))
    palette(bytes.fromhex(a['saved_palette20']['hex']))
    e.tiles(opt['bg'],0x083e2e6c,640,512)
    for item in prior.pair_writes(bytes.fromhex(a['source_palette32']['hex'])):e.write(*item)
    prefix=len(e.writes)
    e.tiles(opt['bg'],row['graphics'],288,532)
    queue_end=len(e.writes)
    palette(data);palette_end=len(e.writes)
    e.write(w.task.tasks.TASKS+40*opt['task_id']+8,2,1)
    return e,{'prefix':prefix,'queue':queue_end,'palette':palette_end}


def task_case(c,a,old,row,data,label,options,*,change=None,stop=None,cut=None,fault=None):
    seg,opt=segments(c,a,old,row,data,options);e,ends=expected(seg,a,row,data,opt)
    writes=e.writes if cut is None else e.writes[:cut(ends)]
    if change is not None:seg=change(seg)
    plan=[(b.SOURCE,DEST1,10),(b.SOURCE,DEST2,10),(prior.SOURCE,prior.DEST1,16),
        (prior.SOURCE,prior.DEST2,16),(row['palette'],DEST1,16),(row['palette'],DEST2,16)]
    m=Machine(c,seg,(opt['task_id'],),old['new_nodes'],plan);error=None
    try:m.run(w.task.CALLBACK)
    except ValueError as exc:error=(str(exc),m.last_pc)
    need(error==stop and m.read_fault==fault,'新state0 suffix '+label+': '+str((error,m.read_fault)))
    image=prior.effect(m,seg,writes,error is None)
    state=int.from_bytes(m.data(w.task.tasks.TASKS+40*opt['task_id']+8,2),'little')
    need(state==(1 if error is None else 0),'state0/1境界')
    if error is None:
        need(m.r[0]==w.b.vm.RETURN and len(m.bios_events)==6 and all(v['completed']for v in m.bios_events),'6copyと帰還')
        need(m.data(DEST1,32)==data==m.data(DEST2,32),'最終palette全32byte')
    return {'case':label,'parameters':opt,'returned':error is None,'stop':list(error)if error else None,
        'read_fault':fault,'state_after':state,'write_count':len(writes),
        'write_identity':s.identity(s.stable(writes)),'final_object_sha256':image,
        'queue_reservations':e.reservations if error is None else [],'phase_ends':ends,
        'completed_bios_copies':sum(v['completed']for v in m.bios_events),
        'bios_written_units':[v['writes_completed']for v in m.bios_events],
        'return_sp_r4_r11_proven':error is None,'maximum_caller_stack_bytes':w.b.vm.SP-m.low_sp,
        'bios_execution_observed':False,'dma_execution_observed':False,'native_observation':False}


def trim(seg,at,n):
    need(sum(p==at for p,_,_ in seg)==1,'trim対象');return [(p,raw[:n],wr)if p==at else(p,raw,wr)for p,raw,wr in seg]


@functools.lru_cache(maxsize=2)
def completion_contracts(row_hex,palette_hex):
    c,a,old=inputs();row=selected_row(bytes.fromhex(row_hex));data=bytes.fromhex(palette_hex);rows=[]
    for task_id in range(16):
        for name,kw in(('free',{}),('wrap',dict(head=127,occupied=(127,))),('full',dict(occupied=tuple(range(128))))):
            rows.append(task_case(c,a,old,row,data,f'task{task_id}-{name}',dict(task_id=task_id,bg=task_id%4,**kw)))
    for mode in(1,3,255):rows.append(task_case(c,a,old,row,data,f'mode-{mode}',dict(mode=mode)))
    for option in range(1,8):rows.append(task_case(c,a,old,row,data,f'lower-bits-{option}',dict(option=option)))
    for bg in range(4):
        for name,kw in(('bank1',dict(bank=1)),('bank128',dict(bank=128)),('bitmap',dict(enabled=1)),('disabled',dict(flags=0))):
            rows.append(task_case(c,a,old,row,data,f'bg{bg}-{name}',dict(bg=bg,**kw)))
    rows.append(task_case(c,a,old,row,data,'one-free-queue',dict(head=127,occupied=tuple(range(127)))))
    need(len(rows)==75,'新規75帰還')
    for n in range(8):
        site=0x081530b8 if n<4 else 0x081530c8;at=ROW if n<4 else ROW+4
        rows.append(task_case(c,a,old,row,data,f'row-short-{n}',{},change=lambda seg,n=n:trim(seg,ROW,n),
            stop=('未map read',site),cut=lambda e,n=n:e['prefix']if n<4 else e['queue'],
            fault={'address':at,'size':4,'site':site}))
    # palette alias時も元sourceを切ってprefixを再試験しない。新規palette専用。
    need(row['palette']not in(b.SOURCE,prior.SOURCE),'新suffix短供給は保存paletteと非alias')
    for n in range(32):
        rows.append(task_case(c,a,old,row,data,f'palette-short-{n}',{},
            change=lambda seg,n=n:trim(seg,row['palette'],n),stop=('未map read',w.BIOS_COPY),
            cut=lambda e,n=n:e['queue']+n//2,fault={'address':row['palette']+n//2*2,'size':2,'site':w.BIOS_COPY}))
    for dest in(DEST1,DEST2):
        def readonly_tail(seg,dest=dest):
            out=[]
            for p,raw,wr in seg:
                out.extend([(p,raw[:20],wr),(p+20,raw[20:],False)]if p==dest else[(p,raw,wr)])
            return out
        rows.append(task_case(c,a,old,row,data,f'palette-readonly-{dest:x}',{},change=readonly_tail,
            stop=('未許可 write',w.BIOS_COPY),cut=lambda e,dest=dest:e['queue']+10+(16 if dest==DEST2 else 0)))
    def readonly_state(seg):
        out=[]
        for p,raw,wr in seg:
            out.extend([(p,raw[:8],wr),(p+8,raw[8:10],False),(p+10,raw[10:],wr)]if p==w.task.tasks.TASKS else[(p,raw,wr)])
        return out
    rows.append(task_case(c,a,old,row,data,'state-readonly',{},change=readonly_state,
        stop=('未許可 write',0x08068ca6),cut=lambda e:e['palette']))
    need(len(rows)==118,'75帰還/43部分停止');return rows


def supply(raw,c,a):
    need(type(raw)is bytes and s.identity(raw)=={'size':s.CANDIDATE['size'],'sha256':s.CANDIDATE['sha256']},'固定candidate')
    saved={}
    for n in c['nodes']:
        saved.update({n['address']+i:v for i,v in enumerate(bytes.fromhex(n['hex']))})
        if 'literal_address'in n:saved.update({n['literal_address']+i:v for i,v in enumerate(n['literal_value'].to_bytes(4,'little'))})
    for key in('saved_palette20','source_palette32'):
        p=a[key];saved.update({p['start']+i:v for i,v in enumerate(bytes.fromhex(p['hex']))})
    reads=[]
    def get(at,size):
        reused=sum(at+i in saved for i in range(size));buf=bytearray()
        for i in range(size):buf.append(saved[at+i]if at+i in saved else raw[at+i-0x08000000])
        data=bytes(buf);reads.append({'start':at,'length':size,'hex':data.hex(),'identity':s.identity(data),
            'new_bytes':size-reused,'reused_bytes':reused,'candidate':dict(s.CANDIDATE)})
        return data
    row=selected_row(get(ROW,8));data=get(row['palette'],32)
    return row,data,reads


def analyze(previous,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    c,a,old=inputs();options=copy.deepcopy(option_contracts())
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'default_row':ROW,'row_bytes':8,'palette_bytes':32,
        'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore();candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw);row,data,reads=supply(raw,c,a)
    rows=copy.deepcopy(completion_contracts(row['hex'],data.hex()))
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    result={'classification':'DEFAULT_FRAME_STATE0_TO1_CONDITIONAL_RAM_CONTRACT_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'default_row':row,'source_windows':reads,
        'option_contract_cases':len(options),'option_cases':options,'raw_option_index_range':[0,31],
        'valid_table_length_proven':False,'default_option_bytes':list(range(8)),
        'contract_cases':len(rows),'successful_returns':sum(r['returned']for r in rows),'cases':rows,
        'state0_to1_default_proven':True,'state1_to2_inherited_not_replayed':True,
        'same_ram_state0_to2_executed':False,'task_state01_complete_proven':False,
        'queue_full_still_advances_state':True,'graphics_dma_execution_observed':False,
        'option_pointer_allocation':'EXPLICIT_SYNTHETIC_NOT_LIVE_SAVE_BLOCK',
        'new_window_bytes':sum(r['new_bytes']for r in reads),'new_node_count':0,'saved_nodes_redecoded':0,
        'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,
        'successful_callee_stubs':0,'bios_execution_observed':False,'dma_execution_observed':False,
        'normal_story_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'task_full_boundary':copy.deepcopy(a['task_full_boundary']),
        'boundary_ja':'default行の6回HLEコピー・queue予約・state1帰還。pointerは明示合成allocation、IRQ/DMA/実BIOSなし。全32行有効性、通常story/live初期化、Ring取得、同一RAM state0→2は未受入。'}
    files=exporter.source_export((SELF,TEST,b.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,bios_selector_continuation=old,state0_palette_supply=a,state0_completion=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return (f'state0 option全256値/不足pointer計263条件と、default行のstate0→1を{r["contract_cases"]}条件/{r["successful_returns"]}帰還で検証。'
        f'新規{r["new_window_bytes"]}byte、保存palette/node再採取0。全task16枠・queue満杯・SP/r4-r11・43部分停止を独立write oracleで確認。',
        '保存default行/実paletteとstate0→1・先行state1→2を再利用し、通常story側の0300504C初期化とtask作成/dispatchの保存callerを結合する。'
        '全32行の有効性は未証明。Ring正規取得・実装備戦闘・保存再開は未受入。旧BIOS/copy/state1/state2/BP/nativeを単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');sys.modules['pr16_ring_state0_completion_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
