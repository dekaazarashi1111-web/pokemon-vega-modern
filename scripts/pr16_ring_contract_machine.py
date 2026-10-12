#!/usr/bin/env python3
"""新規validator継続用の保存Thumbモデル。SP相対とNZCVを具体化する。

旧受入済みモデル/検証は変更しない。ARMv4 Thumb MULのC/Vは不定として扱う。
命令・data・間接先は明示mapのみ。CPU/周辺機器の実行・native到達証明ではない。
"""
from __future__ import annotations
import pr16_ring_saved_contracts as base

SELF='scripts/pr16_ring_contract_machine.py'
need=base.need
MASK=base.MASK


class Machine(base.Machine):
    def __init__(self,nodes,segments,args=()):
        super().__init__(nodes,segments,args)
        self.executed_sites=set();self.read_fault=None

    def read(self,at,size):
        if not all(at+i in self.mem for i in range(size)):
            self.read_fault={'address':at,'size':size,'site':getattr(self,'last_pc',None)}
        return super().read(at,size)

    def nz(self,value,carry=Ellipsis):
        self.flags=(bool(value&0x80000000),value==0,
                    self.flags[2] if carry is Ellipsis else carry,self.flags[3])
        return value

    def add_carry(self,a,b,carry):
        need(type(carry)in (int,bool) and carry in (0,1),'未定義carry依存')
        total=a+b+int(carry);value=total&MASK
        signed=lambda x:x if x<0x80000000 else x-0x100000000
        st=signed(a)+signed(b)+int(carry)
        self.flags=(bool(value&0x80000000),value==0,total>MASK,not -0x80000000<=st<0x80000000)
        return value

    def arithmetic(self,a,b,sub=False,carry=0):
        return self.add_carry(a,(~b)&MASK,1) if sub else self.add_carry(a,b,carry)

    def branch(self,condition):
        need(type(condition)is int and 0<=condition<14,'条件形式')
        needed=((1,),(1,),(2,),(2,),(0,),(0,),(3,),(3,),(1,2),(1,2),(0,3),(0,3),(0,1,3),(0,1,3))[condition]
        need(all(type(self.flags[i])is bool for i in needed),'未定義flag依存')
        return super().branch(condition)

    def shift(self,value,amount,op):
        need(type(amount)is int and 0<=amount<=255 and op in (0,1,2,3),'shift範囲')
        if amount==0:return self.nz(value)
        if op==0:
            carry=bool((value>>(32-amount))&1) if amount<=32 else False
            result=(value<<amount)&MASK if amount<32 else 0
        elif op==1:
            carry=bool((value>>(amount-1))&1) if amount<=32 else False
            result=value>>amount if amount<32 else 0
        elif op==2:
            carry=bool((value>>(min(amount,32)-1))&1)
            result=((value if value<0x80000000 else value-0x100000000)>>min(amount,32))&MASK
        else:
            count=amount%32
            result=((value>>count)|(value<<(32-count)))&MASK if count else value
            carry=bool(result&0x80000000)
        return self.nz(result,carry)

    def run(self,entry,max_steps=100000):
        need(type(entry)is int and entry&1,'Thumb entry')
        need(type(max_steps)is int and 1<=max_steps<=100000,'step上限')
        pc=entry&~1
        while pc!=(base.RETURN&~1):
            need(self.steps<max_steps,'step上限到達');self.steps+=1
            self.last_pc=pc;need(pc in self.nodes,'保存node境界で停止');self.executed_sites.add(pc)
            n=self.nodes[pc];raw=bytes.fromhex(n['hex']);h=int.from_bytes(raw[:2],'little');nextpc=pc+len(raw)
            rd=h&7;rs=(h>>3)&7
            if n['kind']=='call':
                need(len(raw)==4 and h&0xf800==0xf000,'call上位')
                lo=int.from_bytes(raw[2:],'little');need(lo&0xf800==0xf800,'call下位')
                hi=h&0x7ff;hi=hi-0x800 if hi&0x400 else hi
                target=pc+4+(hi<<12)+((lo&0x7ff)<<1);need(target==n['target'],'call結合')
                self.r[14]=pc+5;self.calls.append((pc,target|1));nextpc=target
            elif n['kind'] in ('indirect','return'):
                if h&0xff87==0x4700:
                    target=self.r[(h>>3)&15];need(target&1,'ARM state未対応');nextpc=target&~1
                elif h&0xff87==0x4687:
                    nextpc=self.r[(h>>3)&15]&~1
                else:raise ValueError('未対応間接命令')
            elif n['kind'] in ('jump','conditional'):
                if n['kind']=='jump':
                    need(h&0xf800==0xe000,'jump形式');d=h&0x7ff;d=d-0x800 if d&0x400 else d;take=True
                else:
                    condition=(h>>8)&15;need(h&0xf000==0xd000 and condition<14,'条件形式')
                    d=h&255;d=d-256 if d&128 else d;take=self.branch(condition)
                target=pc+4+2*d;need(target==n['target'],'branch結合')
                if take:nextpc=target
            elif h&0xf600==0xb400:
                indices=[i for i in range(8) if h&(1<<i)]
                if h&0x100:indices.append(15 if h&0x800 else 14)
                need(indices,'空stack register列')
                if h&0x800:
                    for i in indices:self.r[i]=self.read(self.r[13],4);self.r[13]+=4
                    if 15 in indices:need(self.r[15]&1,'POP PC state');nextpc=self.r[15]&~1
                else:
                    self.r[13]-=len(indices)*4;need(base.STACK_LO<=self.r[13]<=base.SP,'stack下限')
                    for j,i in enumerate(indices):self.write(self.r[13]+j*4,4,self.r[i])
                self.low_sp=min(self.low_sp,self.r[13])
            elif h&0xff00==0xb000:
                delta=(h&127)*4;self.r[13]+= -delta if h&128 else delta
                need(base.STACK_LO<=self.r[13]<=base.SP,'SP境界');self.low_sp=min(self.low_sp,self.r[13])
            elif h&0xf000==0x9000:
                at=self.r[13]+(h&255)*4;reg=(h>>8)&7
                if h&0x800:self.r[reg]=self.read(at,4)
                else:self.write(at,4,self.r[reg])
            elif h&0xf000==0xa000:
                self.r[(h>>8)&7]=((self.r[13] if h&0x800 else (pc+4)&~3)+(h&255)*4)&MASK
            elif h&0xf000==0x5000:
                op=(h>>9)&7;at=(self.r[rs]+self.r[(h>>6)&7])&MASK
                if op<3:self.write(at,(4,2,1)[op],self.r[rd])
                else:
                    width=(1,4,2,1,2)[op-3];value=self.read(at,width)
                    if op in (3,7) and value&(1<<(width*8-1)):value-=1<<(width*8)
                    self.r[rd]=value&MASK
            elif h&0xe000==0x6000 or h&0xf000==0x8000:
                width=2 if h&0xf000==0x8000 else (1 if h&0x1000 else 4)
                at=(self.r[rs]+((h>>6)&31)*width)&MASK
                if h&0x800:self.r[rd]=self.read(at,width)
                else:self.write(at,width,self.r[rd])
            elif h&0xf800==0x1800:
                x=(h>>6)&7;b=x if h&0x400 else self.r[x]
                self.r[rd]=self.arithmetic(self.r[rs],b,bool(h&0x200))
            elif h&0xe000==0:
                op=(h>>11)&3;need(op<3,'shift opcode')
                amount=(h>>6)&31;self.r[rd]=self.shift(self.r[rs],amount or (0 if op==0 else 32),op)
            elif h&0xe000==0x2000:
                reg=(h>>8)&7;op=(h>>11)&3;imm=h&255
                if op==0:self.r[reg]=self.nz(imm)
                elif op==1:self.arithmetic(self.r[reg],imm,True)
                else:self.r[reg]=self.arithmetic(self.r[reg],imm,op==3)
            elif h&0xfc00==0x4000:
                op=(h>>6)&15;a,b=self.r[rd],self.r[rs]
                if op in (0,1,12,14,15):
                    value={0:lambda:a&b,1:lambda:a^b,12:lambda:a|b,14:lambda:a&~b,15:lambda:~b}[op]()&MASK
                    self.r[rd]=self.nz(value)
                elif op in (2,3,4,7):self.r[rd]=self.shift(a,b&255,{2:0,3:1,4:2,7:3}[op])
                elif op in (5,6):self.r[rd]=self.add_carry(a,(~b)&MASK if op==6 else b,self.flags[2])
                elif op==8:self.nz(a&b)
                elif op==9:self.r[rd]=self.arithmetic(0,b,True)
                elif op==10:self.arithmetic(a,b,True)
                elif op==11:self.arithmetic(a,b)
                elif op==13:
                    self.r[rd]=(a*b)&MASK;self.nz(self.r[rd]);self.flags=(*self.flags[:2],None,None)
            elif h&0xfc00==0x4400:
                dst=rd|((h>>4)&8);src=(h>>3)&15;op=(h>>8)&3
                need(op!=3 and dst!=15 and src!=15,'未対応PC register依存')
                if op==0:self.r[dst]=(self.r[dst]+self.r[src])&MASK
                elif op==1:self.arithmetic(self.r[dst],self.r[src],True)
                else:self.r[dst]=self.r[src]
            elif h&0xf800==0x4800:
                pool=((pc+4)&~3)+(h&255)*4
                need(n.get('literal_address')==pool and type(n.get('literal_value'))is int,'literal結合')
                self.r[(h>>8)&7]=n['literal_value']
            else:raise ValueError(f'未対応保存命令 {pc:08X}')
            pc=nextpc
        need(self.r[13]==base.SP and self.r[4:12]==list(self.original[4:12]),'return/SP/callee-saved差分')
        return self
