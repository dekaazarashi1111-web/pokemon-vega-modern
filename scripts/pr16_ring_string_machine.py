#!/usr/bin/env python3
"""保存memsetのSTMIA r1!,{r3}/POP {r4,r5,pc}だけを追加する。旧モデルは不変。"""
from __future__ import annotations
import pr16_ring_contract_machine as prior
SELF='scripts/pr16_ring_string_machine.py'
STM_SITES=frozenset((0x081c9e1e,0x081c9e20,0x081c9e22,0x081c9e24,0x081c9e2e))
POP_SITE=0x081c9e48
need=prior.need


class Machine(prior.Machine):
    def extension(self,pc,error):
        node=self.nodes[pc]
        need(node['size']==2,'拡張命令長')
        if pc in STM_SITES and node['hex']=='08c1' and node['kind']=='ordinary':
            need(error==f'未対応保存命令 {pc:08X}','STM例外境界')
            self.write(self.r[1],4,self.r[3]);self.r[1]=(self.r[1]+4)&prior.MASK
            return pc+2
        if pc==POP_SITE and node['hex']=='30bd' and node['kind']=='return':
            need(error=='未対応間接命令','POP例外境界')
            at=self.r[13]
            need(prior.base.STACK_LO<=at<=prior.base.STACK_HI-12,'POP stack境界')
            values=[self.read(at+i*4,4) for i in range(3)]
            self.r[4],self.r[5],self.r[15]=values;self.r[13]+=12
            # ARM7TDMI: POP PCはbit0を無視してThumbを維持。BXのmode交換とは別。
            return values[2]&~1
        raise ValueError('拡張allowlist外')

    def run(self,entry,max_steps=100000):
        while True:
            try:return super().run(entry,max_steps)
            except ValueError as exc:
                pc=getattr(self,'last_pc',None)
                if pc not in self.nodes:raise
                node=self.nodes[pc]
                eligible=(pc in STM_SITES and node['hex']=='08c1' and node['kind']=='ordinary'
                    and str(exc)==f'未対応保存命令 {pc:08X}') or (
                    pc==POP_SITE and node['hex']=='30bd' and node['kind']=='return'
                    and str(exc)=='未対応間接命令')
                if not eligible:raise
                entry=self.extension(pc,str(exc))|1
