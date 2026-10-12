#!/usr/bin/env python3
"""二つのoriginを実Thumb readerへ束縛。未確認のalias/IRQ/退役権限は発行しない。"""
from __future__ import annotations
import hashlib
import json
import struct

BASE=0x08000000
CANDIDATE=dict(size=33554432,sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
FIRST,SECOND=0x080A006F,0x081C96E9
POOL=(0x080A006C,0x080A0070)
VALUES=(0x1111,0x0809FED5)
INIT=(0x0809FF00,0x080A006C)
STACK=(0x03007800,0x03007F00)
NAMES={'SetGpuReg','SetVBlankCallback','SetMainCallback2','gMain','sGpuRegBuffer','__subsf3'}
CLAIMS=dict(conditional_finite_reader_only=True,actual_runtime_execution_observed=False,
    formal_classification_accepted=False,donor_eligible=False,donor_leased=False,donor_safe_bytes=0,
    indirect_reference_completeness_claimed=False,natural_entry_reachability_proven=False,
    actual_gpu_flush_or_irq_executed=False,all_alternative_readers_excluded=False,
    floating_point_callee_body_executed=False,formal_rom_changed=False,formal_save_changed=False,
    native_processes=0,accepted_measurement_replays=0,accepted_test_reruns=0)


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):
    need(type(raw) is bytes,'bytesのみ')
    return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def encode(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def take(raw,address,size):
    need(type(raw) is bytes and type(address) is int and type(size) is int and size>0,'有限整数read')
    offset=address-BASE;need(0<=offset and offset+size<=len(raw),'ROM有限範囲')
    return raw[offset:offset+size]


def half(raw,address):return int.from_bytes(take(raw,address,2),'little')


def literal(op,pc):
    need(type(op) is int and 0<=op<=65535 and type(pc) is int and pc%2==0 and BASE<=pc<BASE+CANDIDATE['size'],'命令型/整列')
    need(op&0xF800==0x4800,'実Thumb PC-relative LDRのみ')
    return (op>>8)&7,((pc+4)&~3)+(op&255)*4


def simple(op):
    # 基本block開始を決めるだけ。実行・operand意味は既存CPU解釈器が現byteから決定する。
    return op&0xF800 in (0x4800,0x2000) or op&0xFC00 in (0x1800,0x1C00)


def locate_load(raw,pool,scope=INIT):
    lo,hi=scope
    need(type(lo) is int and type(hi) is int and lo%2==hi%2==0 and 0<hi-lo<=512,'有限命令scope')
    found=[]
    for pc in range(lo,hi,2):
        op=half(raw,pc)
        if op&0xF800==0x4800 and literal(op,pc)[1]==pool:found.append(pc)
    need(len(found)==1,'literalへの実LDRが一意ではない')
    pc=found[0];entry=pc
    for _ in range(6):
        if entry-2<lo or not simple(half(raw,entry-2)):break
        entry-=2
    return dict(load=pc,entry=entry,register=literal(half(raw,pc),pc)[0],pool=pool,
                opcode_identity=identity(take(raw,pc,2)))


def validate_fields(raw):
    fields=[dict(address=a,value=v,**identity(take(raw,a,4))) for a,v in zip(POOL,VALUES)]
    need(all(int.from_bytes(take(raw,r['address'],4),'little')==r['value'] for r in fields),'固定二fieldの実値')
    crossed=take(raw,POOL[0],4)[3:]+take(raw,POOL[1],4)[:3]
    need(crossed==take(raw,FIRST,4),'1byte+3byte交差の全4byte')
    need(int.from_bytes(crossed,'little')==0x09FED500,'保存targetに一致')
    return fields


def symbolic_name(raw,source):
    need(identity(raw)=={k:source[k] for k in ('size','sha256')},'固定JP table全identity')
    values={};records={}
    for n,line in enumerate(raw.decode().splitlines(),1):
        row=line.split('\t')
        if len(row)==8 and row[4] in NAMES:
            name=row[4];need(name not in values,'symbol重複')
            values[name]=int(row[1],16);records[name]=dict(address=values[name],line=n,row_sha256=identity(line.encode())['sha256'])
    need(set(values)==NAMES,'必要symbol不足')
    need(all(BASE<=values[n]<BASE+CANDIDATE['size'] and values[n]%2==0 for n in NAMES-{'gMain','sGpuRegBuffer'}),'code symbol範囲')
    need(all(0x02000000<=values[n]<0x03008000 and values[n]%4==0 for n in ('gMain','sGpuRegBuffer')),'RAM symbol範囲')
    need(values['__subsf3']==0x081C96DC,'固定float入口')
    return values,records


class Boundary(Exception):pass


def machine(raw,code,writes,extra_reads=()):
    import pr16_dex_hof_runtime_sprite as cpu
    class Closed(cpu.Machine):
        def read(self,address,size):
            if BASE<=address<BASE+len(self.raw):
                need(any(lo<=address and address+size<=hi for lo,hi in (*code,*extra_reads)),'scope外ROM read')
            return super().read(address,size)
    value=Closed(raw,code,writes)
    value.r[:4]=[cpu.UndefinedCallerRegister('entry r'+str(i)) for i in range(4)]
    value.r[12]=cpu.UndefinedCallerRegister('entry r12')
    value.flags=[cpu.UndefinedCallerRegister('entry NZCV')]*4
    return value,cpu


def literal_profile(raw,sym,index,load):
    pool,value=POOL[index],VALUES[index]
    api=sym['SetGpuReg' if index==0 else 'SetVBlankCallback']
    extent=192 if index==0 else 32
    code=((load['entry'],INIT[1]),(api,api+extent))
    expected=(sym['sGpuRegBuffer'],sym['sGpuRegBuffer']+96) if index==0 else (sym['gMain']+12,sym['gMain']+16)
    m,cpu=machine(raw,code,(STACK,expected),((POOL[0],0x080A0088),))
    captured={}
    # 実call到達時に停止しABI引数を記録。その後hookを外し、実callee byteを解釈する。
    def at_api(state,pc):
        captured.update(arguments=[state.r[0],state.r[1]],return_pc=state.r[14]&~1,
                        sp=state.r[13],target=pc)
        raise Boundary()
    m.hooks={api:at_api}
    try:m.run(load['entry'],0x01000000,limit=80)
    except Boundary:pass
    need(captured and len(m.calls)==1 and m.calls[0]['target']==api,'literalから指定APIへの唯一の実call')
    need((pool,4) in m.reads and m.reads[pool,4]['sha256']==identity(take(raw,pool,4))['sha256'],'実LDR全word消費')
    args=captured['arguments']
    if index==0:
        need(type(args[0]) is int and args[0]%2==0 and 0<=args[0]<96 and args[1]==value,'GPU regOffset/value実引数')
        destination=sym['sGpuRegBuffer']+args[0];size=2
    else:
        need(args[0]==value,'vblank実callback引数')
        destination=sym['gMain']+12;size=4
    m.hooks={};old_write=m.write
    def write(address,n,v):
        old_write(address,n,v)
        if address==destination and n==size:
            captured['store_pc']=m.trace[-1]['address']
            if index==0:raise Boundary()
    m.write=write
    try:m.run(api,captured['return_pc'],limit=80)
    except Boundary:
        need(index==0,'GPU store境界以外は拒否')
    rows=[r for r in m.writes if not STACK[0]<=r['address']<STACK[1]]
    need(rows==[dict(address=destination,size=size,value=value)],'実typed store以外のwrite禁止')
    need('store_pc' in captured,'実consumer storeが必要')
    if index==1:need(m.r[13]==captured['sp'],'callback setter実SP帰還')
    need(not any(FIRST<=r['address']<FIRST+4 for r in m.trace),'literalをinstructionとして実行していない')
    need(not any(0x09FED0C4<=a<0x09FEEA44 for a,n in m.reads),'選定donorへのreadなし')
    return dict(status='PASS_CONDITIONAL_ACTUAL_LITERAL_READER',field_index=index,
        literal=fields_record(raw,index),load=load,call=m.calls[0],arguments=[args[0],args[1] if type(args[1]) is int else None],
        store=rows[0],store_pc=captured['store_pc'],instructions=m.trace,reads=list(m.reads.values()),
        stop='first_actual_u16_buffer_store' if index==0 else 'actual_callback_setter_return',
        caller_condition='実argument blockへの直接entry。入口のcaller-saved/NZCVは未定義。自然entryや全初期化処理の証明ではない。',
        consumer_condition='固定JP symbolの実API本体を解釈。GPUは最初のu16 buffer storeで打切り、vblankは実帰還まで。IRQ/GPU flushは非実行。',
        claims=dict(CLAIMS))


def fields_record(raw,index):return dict(address=POOL[index],value=VALUES[index],**identity(take(raw,POOL[index],4)))


def float_profile(raw,sym):
    entry,stop=0x081C96DC,0x081C96EE
    need(sym['__subsf3']==entry,'公開float入口')
    m,cpu=machine(raw,((entry,stop),),(STACK,))
    m.r[0]=0;m.r[1]=0
    target=0x081C94B8;captured={}
    def opaque(state,pc):
        captured.update(target=pc,arguments=state.r[:2],sp=state.r[13],return_pc=state.r[14]&~1)
        # 出力は停止点まで一切readされない。呼出し後RAMの値/浮動小数点結果は証明しない。
        for i in (0,1,2,3,12):state.r[i]=cpu.UndefinedCallerRegister('opaque return')
        state.flags=[cpu.UndefinedCallerRegister('opaque NZCV')]*4
    m.hooks={target:opaque};m.run(entry,stop,limit=32)
    need(captured and captured['return_pc']==0x081C96EC and len(m.calls)==1,'正確なBL復帰')
    need(m.calls==[dict(address=0x081C96E8,target=target)],'対象call原本')
    need(m.r[0]==m.r[13]+52 and m.trace[-1]['address']==0x081C96EC,'直後ADDを実解釈')
    cover={a for r in m.trace for a in range(r['address'],r['address']+r['size'])}
    need(set(range(SECOND,SECOND+4))<=cover,'対象全4byteの実命令fetch')
    need(m.reads and all(n==2 for a,n in m.reads),'浮動call後data readなし/Thumb fetchのみ')
    return dict(status='PASS_CONDITIONAL_ACTUAL_THUMB_READER',entry=entry,stop=stop,
        input_bits=[0,0],call=m.calls[0],opaque_call=captured,instructions=m.trace,reads=list(m.reads.values()),
        conditions_ja='公開__subsf3の直接entry。最初のunpack callは同期AAPCS正常帰還条件。callee body/出力は実行せず、復帰後はADD SP,#52直後で停止してRAMも出力も読まない。自然呼出/浮動小数点演算結果を主張しない。',claims=dict(CLAIMS))


def prove(raw,sym):
    need(identity(raw)==CANDIDATE,'現候補全byte')
    fields=validate_fields(raw)
    loads=[locate_load(raw,a) for a in POOL]
    profiles=[literal_profile(raw,sym,i,load) for i,load in enumerate(loads)]
    profiles.append(float_profile(raw,sym))
    return dict(schema_version=1,status='TWO_ORIGINS_CONDITIONAL_TYPED_READERS_MEASURED',candidate=dict(CANDIDATE),
        literal_fields=fields,profiles=profiles,claims=dict(CLAIMS),
        hits=[dict(address=a,size=4,sha256=identity(take(raw,a,4))['sha256']) for a in (FIRST,SECOND)],
        interpretation_ja=['先頭はu32 literal上位1byteと別のThumb callback field下位3byteの跨り。両aligned fieldの実LDRとtyped storeを検証。',
                           '次の1件は公開__subsf3入口から実BLと復帰直後ADDのinstruction fetch。callee内部の実行証明ではない。'],
        remaining_ja='両起点の正式受領は成功Actionsと保存原本を照合後。窓外跨りread/owner内origin/間接参照・退役/移管/保存統合は未証明。')
