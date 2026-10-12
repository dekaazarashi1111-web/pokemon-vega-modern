#!/usr/bin/env python3
"""保存除算・音声再開・周波数の契約。VCOUNTは明示有限入力、BIOSは実行しない。"""
from __future__ import annotations
import copy
import functools
import hashlib
import json
import random
import sys
import pr16_ring_audio_tail_bytes as prior
import pr16_ring_followup_v2 as s

BASE='03a68a60e1227475947568880931cafae43e5ea3'
SLUG='pr16-ring-audio-tail-contracts'
TASK='PR-P08-7-RING-AUDIO-TAIL-CONTRACTS'
TITLE='保存除算・音声再開・周波数を有限VCOUNT入力と結合'
SELF='scripts/pr16_ring_audio_tail_contracts.py'
TEST='tests/test_pr16_ring_audio_tail_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-audio-tail-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_audio_tail_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=40
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存除算/音声再開/周波数と有限VCOUNT入力の契約は保存原本を再利用。BIOS11/12を実行済み・未読再採取へ読み替えない。'
    '15index参照窓は合法mode一覧ではない。ゼロ除算例外先0x081c7fcdは不足時停止として保持。'
    '同じ末端/音声342/164・renderer/cursor/glyph/BP/nativeを単独再実行しない。次は未結合text/live ownerの到達・allocation/callback。')
current=prior.prior
b=current.b
audio=current.audio
strict=current.strict
need=s.need
MASK=0xffffffff
DIV=0x081c7f39
ZERO=0x081c7fcc
ON=0x081c1761
VCOUNT=0x04000006
TIMER=0x04000100
TABLE=prior.TABLE
VALUES=(96,132,176,224,264,304,352,448,528,608,672,704,256,770,1284)
GROUPS=('division','division_zero','vsync_on','frequency','frequency_wait','frequency_missing','frequency_zero','bios_entry')
INHERIT=(*prior.INHERIT,'frequency_window','audio_bios_prefix','frequency_table_observed','pending_boundaries','pending_direct_callees')


def signed(word):
    audio.uint(word,32,'signed word');return word if word<0x80000000 else word-0x100000000


def quotient(left,right):
    left=signed(left);right=signed(right);need(right!=0,'ゼロ除算oracle禁止')
    value=abs(left)//abs(right)
    return (-value if(left<0)!=(right<0)else value)&MASK


def validate_inputs(nodes,a,context):
    need(len(nodes)==len({n['address']for n in nodes})==7291 and a['candidate']==s.CANDIDATE,'保存7291命令/candidate')
    for k in('dma_execution_observed','audio_hardware_observed','bios_execution_observed','actual_callback_table_observed',
             'all_live_slot_bounds_proven','ring_acquisition_accepted','release_ready'):
        need(a[k]is False,'未受入境界 '+k)
    need(a['pending_direct_callees']==[ZERO|1] and a['frequency_table_observed']is True,'末端未読境界')
    row=a['frequency_window'];segment=audio.prior.g.checked_data(row)
    need(segment[0]==TABLE and len(segment[1])==30 and row['values']==list(VALUES)
        and tuple(int.from_bytes(segment[1][i:i+2],'little')for i in range(0,30,2))==VALUES,'有限周波数窓')
    need(row['selected_indices']==list(range(1,16)) and row['index_zero_address']==TABLE-2,'周波数index根拠')
    for k in('actual_table_length_proven','all_selected_indices_valid_proven','index_zero_sampled','runtime_frequency_observed'):
        need(row[k]is False,'表長/実行昇格 '+k)
    for name,at,raw,num in(('bios_prefix',audio.BIOS,'0cdf7047',12),('audio_bios_prefix',prior.BIOS,'0bdf7047',11)):
        row=a[name]
        need(row['start']==at and row['length']==4 and row['hex']==raw and row['identity']==s.identity(bytes.fromhex(raw))
            and row['first_is_swi']is True and row['swi_number']==num and row['second_is_bx_lr']is True
            and row['executed']is False and row['return_proven']is False,'既知BIOS境界')
    by={n['address']:n for n in nodes}
    for at,encoded in((DIV&~1,'0029'),(ON&~1,'10b5'),(0x081c7fc2,'00f003f8')):
        need(by[at]['hex']==encoded,'末端入口/例外call')
    need(ZERO not in by and audio.BIOS not in by and prior.BIOS not in by,'未実行境界を命令化しない')
    return segment


class Machine(strict.Machine):
    def __init__(self,nodes,segments,args=(),*,sequence=(),bios=()):
        need(type(sequence)is tuple and len(sequence)<=64,'VCOUNT有限入力列')
        for v in sequence:audio.uint(v,8,'VCOUNT byte')
        need(type(bios)is tuple and len(bios)==len(set(bios)) and all(type(v)is int and v in(audio.BIOS,prior.BIOS)for v in bios),'BIOS分類allowlist')
        super().__init__(nodes,segments,args);self.sequence=sequence;self.vcount_reads=[];self.bios=bios
    def read(self,at,size):
        value=super().read(at,size)
        if at==VCOUNT:
            need(size==1,'VCOUNT read幅');index=len(self.vcount_reads)
            need(index<len(self.sequence),'VCOUNT入力列不足')
            value=self.sequence[index];self.vcount_reads.append((self.last_pc,value))
        return value
    def run(self,entry,max_steps=100000):
        try:return super().run(entry,max_steps)
        except ValueError as exc:
            if str(exc)=='保存node境界で停止' and self.last_pc in self.bios:
                raise ValueError('既知BIOS SWI未実行')from exc
            raise


class Cases:
    def __init__(self,nodes):self.nodes=nodes;self.rows=[];self.sites=set()
    def run(self,label,entry,segments,args=(),writes=(),value=None,stop=None,fault=None,sequence=(),events=()):
        need(label not in {r['case']for r in self.rows},'契約label重複')
        e=b.Expected(segments)
        for w in writes:e.write(*w)
        m=Machine(self.nodes,segments,args,sequence=sequence,bios=(audio.BIOS,prior.BIOS))
        try:m.run(entry)
        except ValueError as exc:
            if stop is None:raise ValueError(f'{label}: {exc}; pc={getattr(m,"last_pc",0):08X}')from exc
            need((str(exc),m.last_pc)==stop,'停止境界 '+label+': '+str(exc)+' '+hex(m.last_pc))
        else:need(stop is None,'未証明境界を通過 '+label)
        if fault is not None:need(m.read_fault==fault,'read fault差分 '+label)
        need(m.nonstack_writes()==list(writes),'正確順序write差分 '+label)
        need(all(m.mem[p]==v for p,v in e.mem.items()),'最終object差分 '+label)
        allowed=set(range(m.low_sp,b.vm.SP))
        for at,data,writable in segments:
            if writable:allowed.update(range(at,at+len(data)))
        need(all(all(at+i in allowed for i in range(size))for at,size,_ in m.writes),'object/live-frame外write '+label)
        need(m.vcount_reads==list(events),'VCOUNT read順序 '+label)
        if stop is None:
            need(len(m.vcount_reads)==len(sequence),'未消費VCOUNT入力 '+label)
            if value is not None:need(m.r[0]==value,'戻値差分 '+label)
        self.sites.update(m.executed_sites)
        self.rows.append({'case':label,'returned':stop is None,'return_value':m.r[0]if stop is None else None,
            'stop':None if stop is None else list(stop),'read_fault':m.read_fault,'steps':m.steps,
            'maximum_stack_bytes':b.vm.SP-m.low_sp,'nonstack_write_count':len(writes),
            'write_sha256':hashlib.sha256(json.dumps(list(writes),separators=(',',':')).encode()).hexdigest(),
            'final_object_sha256':e.image(),'return_sp_r4_r11_proven':stop is None,'calls':m.call_arguments,
            'vcount_input_is_fixture':bool(sequence),'vcount_reads':m.vcount_reads})
        return m


def on_writes(e):
    magic=e.read(audio.SOUND,4)
    if magic==audio.MAGIC:return
    for at in(current.IO_BASE+2,current.IO_BASE+14):e.write(at,2,0xb600)
    e.write(audio.SOUND+4,1,0);e.write(audio.SOUND,4,(magic-10)&MASK)


def wait_events(sequence):
    need(type(sequence)is tuple and len(sequence)<=64,'有限待機列')
    for v in sequence:audio.uint(v,8,'待機byte')
    first=True;events=[]
    for value in sequence:
        pc=0x081c15b8 if first else 0x081c15c0;events.append((pc,value))
        if first:
            if value!=159:first=False
        elif value==159:return None,events
    return ('VCOUNT入力列不足',0x081c15b8 if first else 0x081c15c0),events


def frequency_writes(e,mode,sequence):
    audio.uint(mode,32,'frequency mode');index=(mode>>16)&15;e.write(audio.SOUND+8,1,index)
    try:value=e.read(TABLE+2*(index-1),2)
    except ValueError:return ('未map read',0x081c1570),[]
    e.write(audio.SOUND+16,4,value)
    if value==0:return ('保存node境界で停止',ZERO),[]
    e.write(audio.SOUND+11,1,quotient(1584,value)&255)
    rate=quotient((value*0x91d1b+0x1388)&MASK,0x2710);e.write(audio.SOUND+20,4,rate)
    inverse=quotient(0x1000000,rate);e.write(audio.SOUND+24,4,(signed((inverse+1)&MASK)>>1)&MASK)
    e.write(TIMER+2,2,0);e.write(TIMER,2,(-quotient(0x44940,value))&65535);on_writes(e)
    stop,events=wait_events(sequence)
    if not stop:e.write(TIMER+2,2,128)
    return stop,events


def fixture(a,magic=audio.MAGIC):
    segment=audio.prior.g.checked_data(a['frequency_window'])
    return [*current.globals_fixture(magic),*current.io_fixture(),segment,(TIMER,b'\x5a'*4,True),(VCOUNT,b'\0',False)]


def contracts(nodes,a,context):
    validate_inputs(nodes,a,context);cases=Cases(nodes);groups={}
    def run(*args,**kwargs):return cases.run(*args,**kwargs)
    for group in GROUPS:
        before=len(cases.rows)
        if group=='division':
            values=(0,1,2,3,7,15,31,0x7fff,0xffff,0x10000,0x7ffffffe,0x7fffffff,0x80000000,0x80000001,0xfffffffe,0xffffffff)
            pairs=[(left,right)for left in values for right in values if right]
            rng=random.Random(20260917);pairs.extend((rng.getrandbits(32),rng.randrange(1,1<<32))for _ in range(64))
            for index,(left,right)in enumerate(pairs):
                run(f'{group}-{index}',DIV,[],(left,right),value=quotient(left,right))
                cases.rows[-1]['operands']=[left,right]
        elif group=='division_zero':
            for left in(0,1,1584,0x7fffffff,0x80000000,0xffffffff):
                m=run(f'{group}-{left}',DIV,[],(left,0),stop=('保存node境界で停止',ZERO))
                need(m.r[:2]==[left,0],'例外入力不変')
        elif group=='vsync_on':
            for magic in(0,1,audio.MAGIC-1,audio.MAGIC,audio.MAGIC+1,audio.MAGIC+10,audio.MAGIC+11,MASK):
                for marker in(0,1,255):
                    segs=fixture(a,magic);at,data,w=segs[1];data=bytearray(data);data[4]=marker;segs[1]=(at,bytes(data),w)
                    e=b.Expected(segs);on_writes(e)
                    run(f'{group}-{magic}-{marker}',ON,segs,writes=e.writes)
        elif group in('frequency','frequency_wait'):
            indices=range(1,16)if group=='frequency'else(1,12,13,15)
            for index in indices:
                for magic in((audio.MAGIC,audio.MAGIC+10,audio.MAGIC+11)if group=='frequency'else(audio.MAGIC+10,)):
                    sequences=((158,159),(159,0,0,159))if group=='frequency'else((159,159),(0,0))
                    for sequence in sequences:
                        segs=fixture(a,magic);e=b.Expected(segs);stop,events=frequency_writes(e,index<<16,sequence)
                        run(f'{group}-{index}-{magic}-{sequence}',current.FREQ,segs,(index<<16,),e.writes,stop=stop,sequence=sequence,events=events)
                        cases.rows[-1]['selected_window_index']=index;cases.rows[-1]['legal_mode_claimed']=False
        elif group=='frequency_missing':
            for index in(0,15):
                segs=fixture(a)
                if index==15:segs=[(at,data[:-1]if at==TABLE else data,w)for at,data,w in segs]
                e=b.Expected(segs);stop,events=frequency_writes(e,index<<16,())
                run(f'{group}-{index}',current.FREQ,segs,(index<<16,),e.writes,stop=stop,
                    fault={'address':TABLE+2*(index-1),'size':2,'site':0x081c1570})
        elif group=='frequency_zero':
            for index in(1,12,15):
                segs=fixture(a);segs=[(at,bytes(30)if at==TABLE else data,w)for at,data,w in segs]
                e=b.Expected(segs);stop,events=frequency_writes(e,index<<16,())
                run(f'{group}-{index}',current.FREQ,segs,(index<<16,),e.writes,stop=stop)
                cases.rows[-1]['zero_table_is_fault_fixture']=True
        elif group=='bios_entry':
            for at in(audio.BIOS,prior.BIOS):run(f'{group}-{at}',at|1,[],stop=('既知BIOS SWI未実行',at))
        groups[group]=len(cases.rows)-before
    return cases,groups


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows']);nodes=[*nodes,*r['analysis']['new_nodes']]
    f.nodes_to_memory(memory,nodes);validate_inputs(nodes,r['analysis'],context);return nodes,memory,context


@functools.lru_cache(maxsize=1)
def evaluated():
    nodes,_,context=saved_inputs();return contracts(nodes,s.load(PRIOR)['analysis'],context)


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups=evaluated()
    result={k:copy.deepcopy(a[k])for k in INHERIT}
    result.update({'classification':'SAVED_SIGNED_DIVISION_AUDIO_RESTART_FREQUENCY_FINITE_VCOUNT_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,
        'contract_cases':len(cases.rows),'conditional_return_cases':sum(r['returned']for r in cases.rows),
        'pending_stop_cases':sum(not r['returned']for r in cases.rows),'groups':groups,'cases':cases.rows,
        'executed_saved_sites':sorted(cases.sites),'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),
        'vcount_input_is_fixture':True,'legal_frequency_modes_proven':False,'division_zero_exception_accepted':False,
        'dma_execution_observed':False,'audio_hardware_observed':False,'bios_execution_observed':False,
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'保存除算と音声再開・周波数だけ。VCOUNT有限列は実機観測ではなく、BIOS11/12を実行しない。例外先0x081c7fcd/合法mode/live ownerは未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in(*SOURCES,SELF,TEST):
        if p.endswith('.py')and(s.ROOT/p).is_file():sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'保存符号付き除算/音声再開/周波数と有限VCOUNT入力を{r["contract_cases"]}条件で結合。'
        f'帰還{r["conditional_return_cases"]}/不足停止{r["pending_stop_cases"]}。BIOS11/12・実音声/nativeは未実行。',
        '次は未結合text/live ownerの到達・実allocation・callback選択を保存callerから絞る。'
        '音声の既知BIOS11/12は未実行境界として引き継ぎ、ゼロ除算例外先0x081c7fcdは実callerに必要な場合だけ続ける。'
        '15index参照窓を合法mode一覧にせず、同じ音声末端/342/164・renderer/cursor/glyph・受入済みBP/nativeを単独再実行しない。Ring/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
