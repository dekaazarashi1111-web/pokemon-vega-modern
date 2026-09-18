#!/usr/bin/env python3
"""保存memcpyの単一register LDM/STMとPOPだけを明示RAM上で補完する。"""
from __future__ import annotations
import pr16_ring_explicit_text_machine as prior
SELF='scripts/pr16_ring_story_resource_machine.py'
need=prior.need
LDM=frozenset((0x081c9db2,0x081c9db6,0x081c9dba,0x081c9dbe,0x081c9dcc))
STM=frozenset((0x081c9db4,0x081c9db8,0x081c9dbc,0x081c9dc0,0x081c9dce))
POP=0x081c9df4

class Machine(prior.Machine):
    def run(self,entry,max_steps=100000):
        while True:
            try:return super().run(entry,max_steps)
            except ValueError as exc:
                pc=getattr(self,'last_pc',None);n=self.nodes.get(pc,{})
                if pc in LDM and n.get('hex')=='01cb'and n.get('kind')=='ordinary'and str(exc)==f'未対応保存命令 {pc:08X}':
                    need(self.r[3]%4==0,'memcpy LDM alignment')
                    self.r[0]=self.read(self.r[3],4);self.r[3]=(self.r[3]+4)&0xffffffff;entry=(pc+2)|1
                elif pc in STM and n.get('hex')=='01c1'and n.get('kind')=='ordinary'and str(exc)==f'未対応保存命令 {pc:08X}':
                    need(self.r[1]%4==0,'memcpy STM alignment')
                    self.write(self.r[1],4,self.r[0]);self.r[1]=(self.r[1]+4)&0xffffffff;entry=(pc+2)|1
                elif pc==POP and n.get('hex')=='30bd'and n.get('kind')=='return'and str(exc)=='未対応間接命令':
                    at=self.r[13];values=[self.read(at+i*4,4)for i in range(3)]
                    self.r[4],self.r[5],self.r[15]=values;self.r[13]+=12;entry=values[2]|1
                else:raise


class Cases:
    def __init__(self,nodes):self.nodes=nodes;self.rows=[];self.sites=set()
    def run(self,label,entry,segments,args=(),writes=(),value=None,stop=None,fault=None):
        import hashlib,json
        need(label not in {r['case']for r in self.rows},'契約label重複')
        expected=prior.b.Expected(segments)
        for w in writes:expected.write(*w)
        m=Machine(self.nodes,segments,args)
        try:m.run(entry)
        except ValueError as exc:
            if stop is None:raise ValueError(f'{label}: {exc}; pc={getattr(m,"last_pc",0):08X}')from exc
            need((str(exc),m.last_pc)==stop,'停止境界 '+label+': '+str(exc)+' '+hex(m.last_pc))
        else:need(stop is None,'未証明境界を通過 '+label)
        if fault is not None:need(m.read_fault==fault,'read fault差分 '+label)
        need(m.nonstack_writes()==list(writes),'正確順序write差分 '+label)
        need(all(m.mem[p]==b for p,b in expected.mem.items()),'最終object差分 '+label)
        if stop is None and value is not None:need(m.r[0]==value,'戻値差分 '+label)
        self.sites.update(m.executed_sites)
        self.rows.append({'case':label,'returned':stop is None,'return_value':m.r[0]if stop is None else None,
            'stop':None if stop is None else list(stop),'read_fault':m.read_fault,'steps':m.steps,
            'maximum_stack_bytes':prior.b.vm.SP-m.low_sp,'nonstack_write_count':len(writes),
            'write_sha256':hashlib.sha256(json.dumps(list(writes),separators=(',',':')).encode()).hexdigest(),
            'final_object_sha256':expected.image(),'return_sp_r4_r11_proven':stop is None,'calls':m.call_arguments})
        return m
