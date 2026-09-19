#!/usr/bin/env python3
"""text状態専用: 明示RAMと512byte live stackを分離する。旧受入モデルは不変。"""
from __future__ import annotations
import hashlib
import json
import pr16_ring_ui_contracts as b

SELF='scripts/pr16_ring_explicit_text_machine.py'
need=b.need
STACK_START=b.vm.SP-512
STACK_END=b.vm.SP
AUDIO=(0x03007394,0x030073d4)


class Machine(b.Machine):
    def __init__(self,nodes,segments,args=()):
        need(type(args)in (tuple,list)and len(args)<=4,'明示引数4個以下')
        super().__init__(nodes,[],args)
        # 旧helperが用意する0x03007000..8000のゼロ領域は採用しない。
        self.mem.clear();self.writable=set(range(STACK_START,STACK_END))
        need(type(segments)in (tuple,list),'明示segment列')
        for at,data,writable in segments:
            need(type(at)is int and type(data)is bytes and type(writable)is bool
                and 0<=at<=at+len(data)<=0x100000000,'明示segment形式')
            need(not (at<STACK_END and at+len(data)>STACK_START),'明示object/予約stack重複')
            for i,value in enumerate(data):
                p=at+i;need(p not in self.mem,'明示segment重複');self.mem[p]=value
                if writable:self.writable.add(p)

    def read(self,at,size):
        if STACK_START<=at<STACK_END:
            need(self.r[13]<=at and at+size<=STACK_END,'非live stack read')
        return super().read(at,size)

    def write(self,at,size,value):
        if STACK_START<=at<STACK_END:
            need(self.r[13]<=at and at+size<=STACK_END,'非live stack write')
        return super().write(at,size,value)

    def nonstack_writes(self):
        return [w for w in self.writes if not STACK_START<=w[0]<STACK_END]


class Cases:
    def __init__(self,nodes):self.nodes=nodes;self.rows=[];self.sites=set()
    def run(self,label,entry,segments,args=(),writes=(),value=None,stop=None,fault=None):
        need(label not in {r['case']for r in self.rows},'契約label重複')
        e=b.Expected(segments)
        for w in writes:e.write(*w)
        m=Machine(self.nodes,segments,args)
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
        if stop is None and value is not None:need(m.r[0]==value,'戻値差分 '+label)
        self.sites.update(m.executed_sites)
        self.rows.append({'case':label,'returned':stop is None,'return_value':m.r[0]if stop is None else None,
            'stop':None if stop is None else list(stop),'read_fault':m.read_fault,'steps':m.steps,
            'maximum_stack_bytes':b.vm.SP-m.low_sp,'nonstack_write_count':len(writes),
            'write_sha256':hashlib.sha256(json.dumps(list(writes),separators=(',',':')).encode()).hexdigest(),
            'final_object_sha256':e.image(),'return_sp_r4_r11_proven':stop is None,'calls':m.call_arguments})
        return m
