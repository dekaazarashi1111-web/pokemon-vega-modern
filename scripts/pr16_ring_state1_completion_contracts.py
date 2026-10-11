#!/usr/bin/env python3
"""state1新suffixの独立write oracle。保存供給を使いROM/BIOS原本は再採取しない。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_bios_selector_continuation as prior
import pr16_ring_bios_memory_contracts as bios
import pr16_ring_followup_v2 as s

BASE='55e4e68a19300558972a12153a4df6f59a01d912'
SLUG='pr16-ring-state1-completion-contracts'
TASK='PR-P08-7-RING-STATE1-COMPLETION-CONTRACTS'
TITLE='state1のfill・内側tile・queue・state2帰還を独立write oracleで検証'
SELF='scripts/pr16_ring_state1_completion_contracts.py'
TEST='tests/test_pr16_ring_state1_completion_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-state1-completion-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_state1_completion_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=18
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.TEST,prior.PRIOR,bios.RECORDER,*prior.SOURCES)))
NETWORK=('GitHub connector/Actionsの出自照合のみ。保存12byte/2nodeとpalette20byteを再利用。'
    'candidate再構築0・ROM新byte採取0・外部資料再取得0・source-lock変更0。')
NO_REPEAT=('state1→2の今回独立write oracle/保存レジスタ/queue満杯対照/新suffix部分停止を保存原本から再利用。'
    'state2の旧poll/delete受入を再実行しない。state0の次の未供給32byteは0843FA24、'
    'コピー先0203730C/0203770C。palette20byte・2属性slot・8628旧node・BIOS/724/1231条件・BP/native再実行禁止。'
    'state1のRAM/queue条件付き完了をDMA描画・実BIOS・通常story/Ringへ昇格しない。')
need=s.need
w=bios.w
r=w.resource
DEFAULT={'task_id':0,'state':1,'bg':0,'shape':0,'display':0,'left':3,'top':5,
    'width':27,'height':4,'mode':0,'selector':0,'head':0,'occupied':(),
    'enabled':0,'bank':0,'context_base':0}


@functools.lru_cache(maxsize=1)
def inputs():
    import pr16_ring_flagset_continuation as saved
    c=bios.context();p=s.load(PRIOR);saved.bindings_fresh(s.ROOT,p['source_bindings'])
    a=p['analysis'];w.validate_inputs(c)
    need(a['candidate']==s.CANDIDATE and a['new_slot_bytes']==8 and a['new_node_count']==2
        and a['new_window_bytes']==12 and a['palette_resampled_bytes']==0,'selector出自')
    need(a['task_state1_to2_proven'] is False and a['bios_execution_observed'] is False
        and a['ring_acquisition_accepted'] is False and a['release_ready'] is False,'先行traceを受入扱いしない')
    need([(v['address'],v['hex'])for v in a['slots']]==[(0x081534e4,'f8341508'),(0x08001aec,'701b0008')],'保存slot')
    need([(v['address'],v['hex'])for v in a['new_nodes']]==[(0x081534f8,'0020'),(0x081534fa,'06e0')],'保存2node')
    return c,a


def parameters(options):
    need(type(options)is dict and set(options)<=set(DEFAULT),'未対応parameter')
    v=dict(DEFAULT,**options)
    need(v['state']==1 and 0<=v['task_id']<16 and 0<=v['bg']<4 and 0<=v['shape']<4
        and v['display']==0,'限定state/text background')
    need(0<=v['width']<=64 and 0<=v['height']<=8 and v['width']*v['height']<=256,'限定寸法')
    need(0<=v['left']<=255 and 0<=v['top']<=255 and 0<=v['mode']<=255
        and 0<=v['selector']<=255,'byte属性')
    need(v['bank'] in(0,1,128) and 0<=v['context_base']<=65535,'限定bank/base')
    return v


def segments(c,a,v):
    # state1はpalette表に依存しない。slot10以外をmapせずその事実も検査する。
    slot=a['slots'][1]
    return w.fixture(c,**v)+[(slot['address'],bytes.fromhex(slot['hex']),False)]


def expected(seg,v):
    """frame契約を合成し、新suffixは行列式とqueue仕様から期待値を作る。trace参照なし。"""
    e=w.b.Expected(seg)
    for at,size,value in w.frame_writes(seg,**{k:v[k]for k in('bg','shape','display','left','top','width','mode','selector')}):
        e.write(at,size,value)
    frame_end=len(e.writes)
    count=v['width']*v['height']
    for i in range(count*8):e.write(w.PIXELS+4*i,4,0x11111111)
    fill_end=len(e.writes)
    base=(v['context_base']&1023)+9
    for y in range(v['height']):
        for x in range(v['width']):
            at=w.TILEMAP+2*w.tile_index(v['left']+x,v['top']+y,v['shape'])
            e.write(at,2,0x7000|((base+y*v['width']+x)&0xfff))
    interior_end=len(e.writes)
    e.resource(0,3)
    resource_end=len(e.writes)
    e.write(w.task.tasks.TASKS+40*v['task_id']+8,2,2)
    return e,{'frame':frame_end,'fill':fill_end,'interior':interior_end,'resource':resource_end}


def check_effect(m,seg,writes,returned):
    e=w.b.Expected(seg)
    for at,size,value in writes:e.write(at,size,value)
    need(m.nonstack_writes()==writes,'正確順序write差分')
    need(all(m.mem.get(at)==value for at,value in e.mem.items()),'全明示object差分')
    need(all(all(at+i in m.writable for i in range(size))for at,size,_ in m.writes),'許可範囲外write')
    if returned:
        need(m.r[13]==w.b.vm.SP and m.r[4:12]==list(m.original[4:12]),'帰還SP/r4-r11')
        need(m.r[0]==w.b.vm.RETURN,'外側帰還値')
    return e.image()


def one(c,a,label,options,*,mutation=None,stop=None,prefix=None,fault=None):
    v=parameters(options);seg=segments(c,a,v);e,ends=expected(seg,v);writes=e.writes
    if mutation is not None:seg=mutation(seg)
    if prefix is not None:writes=writes[:prefix(ends)]
    m=prior.Machine(c,seg,(v['task_id'],),a['new_nodes']);error=None
    try:m.run(w.task.CALLBACK)
    except ValueError as exc:error=(str(exc),m.last_pc)
    need(error==stop,'新suffix停止差分 '+label+': '+str(error))
    need(m.read_fault==fault,'新suffixread fault差分 '+label+': '+str(m.read_fault))
    image=check_effect(m,seg,writes,error is None)
    need(not any(e['service']==11 for e in m.bios_events),'state1 palette呼出禁止')
    if error is None:
        need(len(m.bios_events)==1 and m.bios_events[0]['completed'],'fill完了')
        need(m.bios_events[0]['writes_completed']==v['width']*v['height']*8,'fill単位数')
        need(m.data(w.task.tasks.TASKS+40*v['task_id']+8,2)==b'\2\0','state2')
    else:need(m.data(w.task.tasks.TASKS+40*v['task_id']+8,2)==b'\1\0','停止時state1保持')
    return {'case':label,'parameters':v,'returned':error is None,'stop':list(error)if error else None,
        'read_fault':m.read_fault,'task_state_after':2 if error is None else 1,
        'write_count':len(writes),'write_identity':s.identity(s.stable(writes)),
        'final_object_sha256':image,'phase_ends':ends,'queue_reservations':e.reservations if error is None else [],
        'maximum_caller_stack_bytes':w.b.vm.SP-m.low_sp,'return_sp_r4_r11_proven':error is None,
        'fill_effect_conditional':True,'bios_execution_observed':False,'dma_execution_observed':False,
        'native_observation':False,'full_play_acceptance':False}


def trim(seg,at,size,writable=None):
    need(sum(p==at for p,_,_ in seg)==1,'trim対象')
    return [(p,data[:size],wr if writable is None else writable)if p==at else(p,data,wr)for p,data,wr in seg]


@functools.lru_cache(maxsize=1)
def verify():
    c,a=inputs();rows=[]
    # 同じprefix単独再検査ではなく、全task IDを新しいstate1→2へ延長する。
    for task_id in range(16):
        for label,kw in (('free',{}),('wrap',{'head':127,'occupied':(127,)}),
                        ('full',{'occupied':tuple(range(128))})):
            rows.append(one(c,a,f'task{task_id}-{label}',dict(task_id=task_id,bg=task_id%4,**kw)))
    for bg in range(4):
        for shape in range(4):
            rows.append(one(c,a,f'geometry-{bg}-{shape}',dict(bg=bg,shape=shape,left=31,top=31,width=2,height=2)))
    for mode,selector in ((0,1),(2,1),(255,255)):
        rows.append(one(c,a,f'frame-variant-{mode}-{selector}',dict(mode=mode,selector=selector)))
    for name,kw in (('zero-width',dict(width=0)),('zero-height',dict(height=0)),
                    ('one-cell',dict(width=1,height=1)),('max-fill',dict(width=32,height=8)),
                    ('base-wrap',dict(context_base=1023)),('bank1',dict(bank=1)),
                    ('color256',dict(bank=128)),('bitmap',dict(enabled=1))):
        rows.append(one(c,a,name,kw))
    # 新suffixの最初のtile storeで停止。先行frameはこの位置に書かない。
    at=w.TILEMAP+2*w.tile_index(3,5,0)
    def readonly_cell(seg):
        out=[]
        for p,data,wr in seg:
            if p!=w.TILEMAP:out.append((p,data,wr));continue
            cut=at-p;out +=[(p,data[:cut],wr),(at,data[cut:cut+2],False),(at+2,data[cut+2:],wr)]
        return out
    rows.append(one(c,a,'interior-readonly',{},mutation=readonly_cell,
        stop=('未許可 write',0x08002890),prefix=lambda e:e['fill']))
    rows.append(one(c,a,'queue-lock-readonly',{},mutation=lambda seg:trim(seg,r.LOCK,1,False),
        stop=('未許可 write',0x08000ec8),prefix=lambda e:e['interior']))
    rows.append(one(c,a,'queue-mask-short',{},mutation=lambda seg:trim(seg,r.MASK,3),
        stop=('未map read',0x08001854),prefix=lambda e:e['interior']+6,
        fault={'address':r.MASK,'size':4,'site':0x08001854}))
    # 必須state writeを禁じ、描画予約を成功したstate遷移へ読み替えない。
    def readonly_state(seg):
        out=[]
        for p,data,wr in seg:
            if p!=w.task.tasks.TASKS:out.append((p,data,wr));continue
            out +=[(p,data[:8],wr),(p+8,data[8:10],False),(p+10,data[10:],wr)]
        return out
    rows.append(one(c,a,'state-readonly',{},mutation=readonly_state,
        stop=('未許可 write',0x08068ca6),prefix=lambda e:e['resource']))
    need(len(rows)==79 and len({row['case']for row in rows})==79,'新規79条件')
    return rows


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    rows=copy.deepcopy(verify());need(verify.cache_info().misses==1,'結合二重実行禁止')
    c,a=inputs()
    result={'classification':'STATE1_TO2_CONDITIONAL_RAM_AND_QUEUE_CONTRACT_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'contract_cases':len(rows),'successful_returns':sum(r['returned']for r in rows),
        'cases':rows,'task_state1_to2_proven':True,'proof_scope':'EXPLICIT_RAM_FIXED_HLE_NO_IRQ_NO_DMA',
        'task_state01_complete_proven':False,'state0_remaining_read':copy.deepcopy(a['cases'][0]),
        'task_full_boundary':copy.deepcopy(a['task_full_boundary']),
        'queue_full_still_advances_state':True,'queue_reservation_is_not_render_success':True,
        'rom_changes':0,'candidate_reconstructions':0,'new_emulator_processes':0,
        'new_node_count':0,'new_window_bytes':0,'saved_node_count':8630,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,
        'bios_prefix_bytes_resampled':0,'palette_resampled_bytes':0,'saved_nodes_redecoded':0,
        'bios_execution_observed':False,'dma_execution_observed':False,'normal_story_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'state1の全write順・全明示object・SP/r4-r11帰還を独立期待値と照合。'
            'queue満杯でもstate2へ進むため、state進行を描画成功と同一視しない。'
            'BIOSは固定HLEメモリ契約、IRQ/BIOS stack/実機/通常storyは未観測。'
            'state0は0843FA24の次palette32byte供給前で停止した保存原本を継承。'}
    files=exporter.source_export((SELF,TEST,bios.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,bios_selector_continuation=a,state1_completion=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(a):
    return (f'state1→2を独立write oracleで新規{a["contract_cases"]}条件/{a["successful_returns"]}帰還・4部分停止まで条件付き検証。'
        '全task16枠、queue空/折返し/満杯、4背景4shape、bitmap/bank/寸法境界、SP/r4-r11を確認。'
        'ROM復元/新byte/emulator0。queue満杯もstate2へ進むが描画成功ではない。',
        '次は保存state0_remaining_readのBIOS0B source0843FA24、32byteの出自付き供給と'
        '0203730C/0203770C両コピーを未観測suffixへ延長する。state1→2/旧state2 poll/delete/BP/nativeは再実行しない。'
        'palette20byte・2属性slot・全保存nodeを再採取しない。通常story/live初期化・Ring取得・保存再開は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    sys.modules['pr16_ring_state1_completion_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
