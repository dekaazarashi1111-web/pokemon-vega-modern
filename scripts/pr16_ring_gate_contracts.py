#!/usr/bin/env python3
"""保存2107命令で81要素展開と非null caller帰還を結合。ROM/native再実行なし。"""
from __future__ import annotations
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import pr16_ring_caller_contracts as caller

BASE='9768456890e460729630e1a47c856f682ccd40bf'
SLUG='pr16-ring-gate-contracts'
TASK='PR-P08-7-RING-GATE-CONTRACTS'
TITLE='81要素表と非null caller帰還・callback境界を保存検証'
SELF='scripts/pr16_ring_gate_contracts.py'
TEST='tests/test_pr16_ring_gate_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-gate-contracts.yml'
PRIOR='content/modernization/pr16_ring_gate_frontier.json'
REPORT='content/modernization/pr16_ring_gate_contracts.json'
KEY='latest_ring_diagnostic'
SOURCES=()
EXTRA_CODE=()
MIN_TESTS=35
EXPAND,DISPATCH,RESOURCE=0x08002e79,0x08002e4d,0x08003eed
COMBINATIONS,RECORDS,POOL,TABLE=0x03000a40,0x02020430,0x02020030,0x02028000
TRANSFERS={0x08002ed4:'02cd',0x08003f06:'54c9',0x08003f08:'54c0'}
INITIAL='0ee0588da2832d627bfaf4e8876aa5aa275fafc2'
NO_REPEAT=('保存2107命令による81要素展開・非null caller帰還/32byte保存・resource/callback停止契約を再利用する。'
    '11文字列/265caller/旧795/716/BP/nativeを単独再実行しない。'
    '非null限定帰還をdispatch callback帰還・全live slot境界やRing取得へ昇格しない。')
need=caller.need
vm=caller.vm


def identity(data):return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


class Machine(caller.Machine):
    def transfer_new(self,pc,error):
        n=self.nodes[pc]
        need(pc in TRANSFERS and n['hex']==TRANSFERS[pc] and n['size']==2 and n['kind']=='ordinary','新転送allowlist差分')
        need(error==f'未対応保存命令 {pc:08X}','新転送例外境界')
        h=int.from_bytes(bytes.fromhex(n['hex']),'little');base=(h>>8)&7;regs=[r for r in range(8)if h&(1<<r)]
        need(regs and base not in regs,'新転送base/writeback未対応')
        at=self.r[base];need(at%4==0 and at+4*len(regs)<=0x100000000,'新転送範囲')
        if h&0x800:
            for i,r in enumerate(regs):self.r[r]=self.read(at+i*4,4)
        else:
            for i,r in enumerate(regs):self.write(at+i*4,4,self.r[r])
        self.r[base]=at+len(regs)*4;return pc+2

    def run(self,entry,max_steps=100000):
        while True:
            try:return super().run(entry,max_steps)
            except ValueError as exc:
                pc=getattr(self,'last_pc',None)
                if pc not in TRANSFERS or str(exc)!=f'未対応保存命令 {pc:08X}':raise
                entry=self.transfer_new(pc,str(exc))|1


def expansion(args):
    need(type(args)in (tuple,list) and len(args)==3 and all(type(v)is int and 0<=v<0x100000000 for v in args),'3値引数')
    a,b,c=[v&255 for v in args];values=(b,a,c)
    table=[((values[l]<<12)|(values[k]<<8)|(values[j]<<4)|values[i])&65535
        for i,j,k,l in itertools.product(range(3),repeat=4)]
    image=b''.join(v.to_bytes(2,'little')for v in (*table,*values))
    writes=[(COMBINATIONS+162+i*2,2,v)for i,v in enumerate(values)]
    writes.extend((COMBINATIONS+i*2,2,v)for i,v in enumerate(table))
    return image,writes


def context_image(source,mode,pointer):
    need(type(source)is bytes and len(source)==16 and type(mode)is int and 0<=mode<0x100000000
        and type(pointer)is int and 0<=pointer<0x100000000,'context引数')
    value=mode&255;value=1 if value==127 else value
    return source+pointer.to_bytes(4,'little')+bytes(7)+bytes([1,0,value,0,0])


def record_args(raw):
    need(type(raw)is bytes and len(raw)==12,'record長')
    return [raw[0],int.from_bytes(raw[8:12],'little'),(raw[3]*raw[4]*32)&65535,int.from_bytes(raw[6:8],'little')]


def verify(nodes,analysis):
    need(len(nodes)==2107 and analysis['cached_node_count']==1935 and analysis['new_node_count']==172,'保存命令数')
    need(analysis['pending_direct_callees']==[0x080017d1,0x080020bd,0x081c7acd,0x09128221]
        and analysis['pending_continuations']==[],'pending差分')
    rows=[];stops=[]
    def returned(m,label,objects):
        need(not caller.outside_writes(m,objects),'所有object外write '+label)
        rows.append({'case':label,'steps':m.steps,'return_r0':m.r[0],'maximum_stack_bytes':vm.SP-m.low_sp,
            'writes':m.nonstack_writes(),'call_arguments':m.call_arguments,'return_sp_callee_saved_proven':True})
    def stop(m,entry,label,error,site,objects):
        try:m.run(entry)
        except ValueError as exc:need(str(exc)==error and m.last_pc==site,'停止境界 '+label)
        else:raise ValueError('未証明境界を通過 '+label)
        need(not caller.outside_writes(m,objects),'停止前object外write')
        stops.append({'case':label,'site':site,'error':error,'read_fault':m.read_fault,'return_proven':False,
            'maximum_stack_bytes':vm.SP-m.low_sp,'writes':m.nonstack_writes(),'call_arguments':m.call_arguments})
    values=sorted(set(itertools.product((0,1,7,15),repeat=3))|{tuple(v if j==i else 15 for j in range(3))for i in range(3)for v in range(16)}
        |{(255,256,511),(0xffffffff,0x12345678,0x12340001)})
    for args in values:
        expected,writes=expansion(args);m=Machine(nodes,[(COMBINATIONS,b'\xcc'*168,True)],args).run(EXPAND)
        need(m.data(COMBINATIONS,168)==expected and m.nonstack_writes()==writes,'81要素/metadata正確write')
        returned(m,'expand-'+str(args),[(COMBINATIONS,168)])
    expand_count=len(rows)
    for mode in (1,2,126,127,128,254,0x1fe):
        for n in (0,1,0x7f,0x80,255):
            for slot in (0,1,31,255):
                src=bytearray(range(16));src[4]=slot;src[12]=n;src[13]=255-n
                target=POOL+slot*32;pointer=0x08012345
                segs=[(caller.GATE_WORD,(1).to_bytes(4,'little'),False),(caller.GATE_CONTEXT,b'\xcc'*32,True),
                    (caller.SRC,bytes(src),False),(COMBINATIONS,b'\xcc'*168,True),(target,b'\xaa'*32,True)]
                m=Machine(nodes,segs,(caller.SRC,mode,pointer)).run(caller.GATE)
                ctx=bytearray(context_image(bytes(src),mode,pointer));ctx[29]-=1
                expected,write_expand=expansion((n>>4,(255-n)&15,(255-n)>>4))
                need(m.r[0]==1 and m.data(caller.GATE_CONTEXT,32)==bytes(ctx) and m.data(target,32)==bytes(ctx),'非null caller帰還/32byte保存')
                need(m.data(COMBINATIONS,168)==expected,'非null81要素結合')
                writes=m.nonstack_writes()
                need([w for w in writes if COMBINATIONS<=w[0]<COMBINATIONS+168]==write_expand,'非null展開write結合')
                need([w for w in writes if target<=w[0]<target+32]==[(target+i*4,4,int.from_bytes(ctx[i*4:i*4+4],'little'))for i in range(8)],'非null保存8word正確write')
                need(m.calls==[(0x08002d48,EXPAND)],'非null余分callなし')
                returned(m,f'nonnull-return-{mode}-{n}-{slot}',[(caller.GATE_CONTEXT,32),(COMBINATIONS,168),(target,32)])
    nonnull_count=len(rows)-expand_count
    # 自然callerのallocationは未観測。dispatchルートは明示12byte stride tableの1wordのみ。
    for mode in (0,255):
        for index in (0,1,254,255):
            src=bytearray(range(16));src[5]=index;target=TABLE+index*12;callback=0x08012345
            segs=[(caller.GATE_WORD,TABLE.to_bytes(4,'little'),False),(target,callback.to_bytes(4,'little'),False),
                (caller.GATE_CONTEXT,b'\xcc'*32,True),(caller.SRC,bytes(src),False),(COMBINATIONS,b'\xcc'*168,True)]
            m=Machine(nodes,segs,(caller.SRC,mode,0x08012345))
            stop(m,caller.GATE,f'dispatch-{mode}-{index}','保存node境界で停止',0x081c7acc,[(caller.GATE_CONTEXT,32),(COMBINATIONS,168)])
            need(m.call_arguments[-1]['args'][:2]==[caller.GATE_CONTEXT,callback],'callback table結合')
    for slot in (0,1,31,255):
        for dims in ((0,0),(1,1),(7,9),(255,255)):
            raw=bytes([5,0,0,*dims,0,0x34,0x12,0,0x70,0,2]);at=RECORDS+slot*12;args=record_args(raw)
            for mode in (0,1,2,3,4,255):
                m=Machine(nodes,[(at,raw,False)],(slot,mode))
                if mode in (1,2,3):
                    endpoint=0x080020bc if mode==1 else 0x080017d0
                    stop(m,RESOURCE,f'resource-{slot}-{dims}-{mode}','保存node境界で停止',endpoint,[])
                    need(m.call_arguments[-1]['args'][:(1 if mode==1 else 4)]==args[:(1 if mode==1 else 4)],'resource callee引数')
                else:
                    m.run(RESOURCE);need(not m.nonstack_writes()and not m.calls,'resource未選択は無書込')
                    returned(m,f'resource-noop-{slot}-{dims}-{mode}',[])
    for value in (0,1,0x3fff,0x4000,0x4010,0x410f,0x8000,0xffff,0x14010,0xffffffff):
        m=Machine(nodes,[],(value,));stop(m,caller.VARGET,'var-helper-'+str(value),'保存node境界で停止',0x09128220,[])
        need(m.r[0]==value&65535 and m.call_arguments[-1]['args'][0]==value&65535 and not m.nonstack_writes(),'VarGet helper引数')
    return {'classification':'SAVED_EXPANSION_NONNULL_RETURN_AND_CALLBACK_BOUNDARIES_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'synthetic_contract_cases':len(rows),'contracts':rows,'limited_stops':stops,
        'expansion_cases':expand_count,'nonnull_return_cases':nonnull_count,'nonrecursive_callback_stops':8,
        'specific_nonnull_return_proven':True,'nonnull_record_size':32,'combination_output_bytes':168,
        'slot_safety_requires_caller_allocation':True,'all_live_slot_bounds_proven':False,
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'all_dispatch_returns_proven':False,
        'pending_direct_callees':[0x080017d1,0x080020bd,0x081c7acd,0x09128221],
        'pending_effective_targets':[0x0806dc51,0x0806dc57],'pending_data_ranges':[],'pending_continuations':[],
        'unbound_runtime_data':[{'base':caller.GATE_WORD,'index_offset':5,'stride':12,'read_bytes':4,'kind':'callback table pointer'},
            {'base':RECORDS,'stride':12,'read_bytes':12,'kind':'resource record array'},
            {'base':POOL,'stride':32,'write_bytes':32,'kind':'nonnull output slots'}],
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'preconditions':['81要素表168byteは8bit切詰め3引数の合成。候補ROMのcallee命令を実行したモデル証拠でnativeではない。',
            '非null帰還はmode低8bitが0/255以外、127を1へ正規化する保存callerの限定経路。',
            'slot0/1/31/255は合成allocationを明示した境界試験。live配列長や全callerの制限を証明しない。',
            '未読callback・VarGet helper・resource calleeにstub/成功値を補わない。正規story到達・Ring取得は未証明。']}


def archive_effects(value):
    """詳細write列はartifactに固定し、tracked正本は件数/hashで結合する。"""
    stable=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    result=copy.deepcopy(value)
    raw=stable({k:result[k]for k in ('contracts','limited_stops')})
    result['raw_effects_identity']=identity(raw)
    for key in ('contracts','limited_stops'):
        for row in result[key]:
            writes=row.pop('writes');row['nonstack_write_count']=len(writes)
            row['nonstack_write_identity']=identity(stable(writes))
    return result,raw


def analyze(prior_report,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_gate_frontier as frontier
    import io
    import unittest
    import subprocess
    nodes,_,_=frontier.saved_inputs();nodes=[*nodes,*prior_report['analysis']['new_nodes']]
    result=verify(nodes,prior_report['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    # 引継ぎMD/JSONに変更影響があるため、生成/検査器の単体回帰も実施する。nativeは起動しない。
    stream=io.StringIO();suite=unittest.TestLoader().discover(str(s.ROOT/'tests'),pattern='test_pr16_resume.py')
    tested=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    need(tested.wasSuccessful()and not tested.skipped and tested.testsRun>0,'固定再開文書の回帰')
    text=stream.getvalue().encode('utf-8');(out/'resume-tests.txt').write_bytes(text)
    result['resume_generator_regression']={'tests_run':tested.testsRun,'failures':len(tested.failures),
        'errors':len(tested.errors),'skips':len(tested.skipped),'successful':tested.wasSuccessful(),'log_identity':identity(text)}
    checkpoint=s.ROOT/s.CHECKPOINT
    need(checkpoint.read_bytes()==subprocess.check_output(['git','show',INITIAL+':'+s.CHECKPOINT],cwd=s.ROOT),'正式BP checkpoint変更')
    stages=[]
    for path in ('content/modernization/pr16_ring_text_frontier.json','content/modernization/pr16_ring_caller_contracts.json',PRIOR):
        r=s.load(path);live=s.api(f'actions/runs/{r["run_id"]}')
        need(live['status']=='completed'and live['conclusion']=='success'and live['head_sha']==r['source_head'],'工程Actions不一致')
        stages.append({'path':path,'identity':identity((s.ROOT/path).read_bytes()),'run_id':r['run_id'],
            'source_head':r['source_head'],'conclusion':'success','tests_run':r['focused_tests']['tests_run']})
    result['prior_session_stages_verified_without_replay']=stages
    result['formal_bp_checkpoint_unchanged_from']=INITIAL
    result,raw=archive_effects(result);(out/'raw-effects.json').write_bytes(raw)
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return (f'保存2107命令で81要素展開{result["expansion_cases"]}件・非null帰還{result["nonnull_return_cases"]}件を結合。'
        '32byte出力保存・168byte表・owned frameとcallee-savedを検証。dispatch/VarGet未読先は未証明のまま。',
        '次は未読callee0x080017D1/0x080020BD/0x081C7ACD/0x09128221とVarGetの実継続0x0806DC51/0x0806DC57を既読2107命令へ有限結合する。'
        'callback table/12byte resource records/32byte出力slotは実caller allocation証拠と分離する。'
        '保存81要素展開・非null帰還・265caller・11文字列・旧795/716/BP/nativeの単独再実行は禁止。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_gate_frontier as frontier
    import pr16_ring_text_frontier as text
    import pr16_ring_reference_contracts as older
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((frontier.SELF,caller.SELF,text.SELF,older.SELF,caller.prior.SELF,
        caller.prior.prior.SELF,vm.SELF,vm.flow.SELF,'tests/test_pr16_resume.py',
        'content/modernization/pr16_ring_text_frontier.json','content/modernization/pr16_ring_caller_contracts.json',
        *older.SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
