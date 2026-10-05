"""allocator境界・epoch反証・setup最小射影。条件を実runtime保証へ昇格しない。"""
import copy,hashlib,json
import pr16_dex_hof_callback_party as shared
import pr16_dex_hof_lifetime_setup as setup
need,identity,chunk=shared.need,shared.identity,shared.chunk
CANDIDATE,DIAGNOSTIC=shared.CANDIDATE,shared.DIAGNOSTIC
"""実allocatorの固定命令意味。rawbyteは含めない。"""
block=shared.block
BLOCKS={}
BLOCKS['heap_init_call']=tuple(block(0x080003ee, [
 ('literal', 0, 134218852), # 0x080003ee
 ('imm', 'mov', 1, 224), # 0x080003f0
 ('shift', 'lsl', 1, 1, 9), # 0x080003f2
 ('call', 134228864), # 0x080003f4
]))
BLOCKS['put_header']=tuple(block(0x0800292c, [
 ('push', 16, True), # 0x0800292c
 ('imm', 'mov', 4, 0), # 0x0800292e
 ('mem', False, 'half', 4, 0, 0), # 0x08002930
 ('literal', 4, 134228292), # 0x08002932
 ('mem', False, 'half', 4, 0, 2), # 0x08002934
 ('mem', False, 'word', 3, 0, 4), # 0x08002936
 ('mem', False, 'word', 1, 0, 8), # 0x08002938
 ('mem', False, 'word', 2, 0, 12), # 0x0800293a
 ('pop', 16, False), # 0x0800293c
 ('pop', 1, False), # 0x0800293e
 ('bx', 0), # 0x08002940
]))
BLOCKS['put_first']=tuple(block(0x08002948, [
 ('push', 0, True), # 0x08002948
 ('addi', 2, 0, 0), # 0x0800294a
 ('addi', 3, 1, 0), # 0x0800294c
 ('imm', 'sub', 3, 16), # 0x0800294e
 ('addi', 1, 2, 0), # 0x08002950
 ('call', 134228268), # 0x08002952
 ('pop', 1, False), # 0x08002956
 ('bx', 0), # 0x08002958
]))
BLOCKS['alloc_scan_fit']=tuple(block(0x0800295c, [
 ('push', 240, True), # 0x0800295c
 ('addi', 5, 1, 0), # 0x0800295e
 ('literal', 2, 134228376), # 0x08002960
 ('mem', False, 'word', 0, 2, 0), # 0x08002962
 ('literal', 1, 134228380), # 0x08002964
 ('mem', False, 'word', 0, 1, 0), # 0x08002966
 ('imm', 'mov', 0, 3), # 0x08002968
 ('alu', 'and', 0, 5), # 0x0800296a
 ('imm', 'cmp', 0, 0), # 0x0800296c
 ('branch', 0, 134228342), # 0x0800296e
 ('shift', 'lsr', 0, 5, 2), # 0x08002970
 ('imm', 'add', 0, 1), # 0x08002972
 ('shift', 'lsl', 5, 0, 2), # 0x08002974
 ('addi', 6, 1, 0), # 0x08002976
 ('literal', 7, 134228384), # 0x08002978
 ('mem', True, 'word', 4, 6, 0), # 0x0800297a
 ('mem', True, 'half', 0, 4, 0), # 0x0800297c
 ('imm', 'cmp', 0, 0), # 0x0800297e
 ('branch', 1, 134228444), # 0x08002980
 ('mem', True, 'word', 3, 4, 4), # 0x08002982
 ('compare', 3, 5), # 0x08002984
 ('branch', 3, 134228444), # 0x08002986
 ('sub', 0, 3, 5), # 0x08002988
 ('imm', 'cmp', 0, 31), # 0x0800298a
 ('branch', 8, 134228388), # 0x0800298c
 ('imm', 'mov', 0, 1), # 0x0800298e
 ('mem', False, 'half', 0, 4, 0), # 0x08002990
 ('addi', 0, 4, 0), # 0x08002992
 ('imm', 'add', 0, 16), # 0x08002994
 ('jump', 134228472), # 0x08002996
]))
BLOCKS['alloc_split']=tuple(block(0x080029a4, [
 ('imm', 'sub', 3, 16), # 0x080029a4
 ('sub', 3, 3, 5), # 0x080029a6
 ('addi', 0, 5, 0), # 0x080029a8
 ('imm', 'add', 0, 16), # 0x080029aa
 ('add', 0, 4, 0), # 0x080029ac
 ('mem', False, 'word', 0, 7, 0), # 0x080029ae
 ('imm', 'mov', 1, 1), # 0x080029b0
 ('mem', False, 'half', 1, 4, 0), # 0x080029b2
 ('mem', False, 'word', 5, 4, 4), # 0x080029b4
 ('mem', True, 'word', 2, 4, 12), # 0x080029b6
 ('addi', 1, 4, 0), # 0x080029b8
 ('call', 134228268), # 0x080029ba
 ('mem', True, 'word', 0, 6, 0), # 0x080029be
 ('mem', True, 'word', 1, 7, 0), # 0x080029c0
 ('mem', False, 'word', 1, 0, 12), # 0x080029c2
 ('literal', 0, 134228440), # 0x080029c4
 ('mem', True, 'word', 2, 1, 12), # 0x080029c6
 ('mem', True, 'word', 0, 0, 0), # 0x080029c8
 ('compare', 2, 0), # 0x080029ca
 ('branch', 0, 134228432), # 0x080029cc
 ('mem', False, 'word', 1, 2, 8), # 0x080029ce
 ('mem', True, 'word', 0, 6, 0), # 0x080029d0
 ('imm', 'add', 0, 16), # 0x080029d2
 ('jump', 134228472), # 0x080029d4
]))
BLOCKS['alloc_scan_tail']=tuple(block(0x080029dc, [
 ('mem', True, 'word', 0, 1, 0), # 0x080029dc
 ('mem', True, 'word', 3, 0, 12), # 0x080029de
 ('mem', True, 'word', 0, 2, 0), # 0x080029e0
 ('compare', 3, 0), # 0x080029e2
 ('branch', 0, 134228458), # 0x080029e4
 ('mem', False, 'word', 3, 1, 0), # 0x080029e6
 ('jump', 134228346), # 0x080029e8
 ('literal', 0, 134228480), # 0x080029ea
 ('imm', 'mov', 1, 174), # 0x080029ec
 ('literal', 2, 134228484), # 0x080029ee
 ('imm', 'mov', 3, 1), # 0x080029f0
 ('call', 136084024), # 0x080029f2
 ('imm', 'mov', 0, 0), # 0x080029f6
 ('pop', 240, False), # 0x080029f8
 ('pop', 2, False), # 0x080029fa
 ('bx', 1), # 0x080029fc
]))
BLOCKS['free_prefix']=tuple(block(0x08002a08, [
 ('push', 240, True), # 0x08002a08
 ('imm', 'cmp', 1, 0), # 0x08002a0a
 ('branch', 1, 134228516), # 0x08002a0c
 ('literal', 0, 134228508), # 0x08002a0e
 ('literal', 2, 134228512), # 0x08002a10
 ('imm', 'mov', 1, 195), # 0x08002a12
 ('imm', 'mov', 3, 1), # 0x08002a14
 ('call', 136084024), # 0x08002a16
 ('jump', 134228682), # 0x08002a1a
]))
BLOCKS['free_body']=tuple(block(0x08002a24, [
 ('addi', 6, 0, 0), # 0x08002a24
 ('addi', 4, 1, 0), # 0x08002a26
 ('imm', 'sub', 4, 16), # 0x08002a28
 ('mem', True, 'half', 0, 4, 2), # 0x08002a2a
 ('literal', 7, 134228688), # 0x08002a2c
 ('compare', 0, 7), # 0x08002a2e
 ('branch', 0, 134228542), # 0x08002a30
 ('literal', 0, 134228692), # 0x08002a32
 ('literal', 2, 134228696), # 0x08002a34
 ('imm', 'mov', 1, 204), # 0x08002a36
 ('imm', 'mov', 3, 1), # 0x08002a38
 ('call', 136084024), # 0x08002a3a
 ('mem', True, 'half', 0, 4, 0), # 0x08002a3e
 ('imm', 'cmp', 0, 1), # 0x08002a40
 ('branch', 0, 134228560), # 0x08002a42
 ('literal', 0, 134228692), # 0x08002a44
 ('literal', 2, 134228700), # 0x08002a46
 ('imm', 'mov', 1, 205), # 0x08002a48
 ('imm', 'mov', 3, 1), # 0x08002a4a
 ('call', 136084024), # 0x08002a4c
 ('imm', 'mov', 0, 0), # 0x08002a50
 ('mem', False, 'half', 0, 4, 0), # 0x08002a52
 ('mem', True, 'word', 0, 4, 12), # 0x08002a54
 ('compare', 0, 6), # 0x08002a56
 ('branch', 0, 134228620), # 0x08002a58
 ('mem', True, 'half', 5, 0, 0), # 0x08002a5a
 ('imm', 'cmp', 5, 0), # 0x08002a5c
 ('branch', 1, 134228620), # 0x08002a5e
 ('mem', True, 'half', 0, 0, 2), # 0x08002a60
 ('compare', 0, 7), # 0x08002a62
 ('branch', 0, 134228594), # 0x08002a64
 ('literal', 0, 134228692), # 0x08002a66
 ('literal', 2, 134228704), # 0x08002a68
 ('imm', 'mov', 1, 211), # 0x08002a6a
 ('imm', 'mov', 3, 1), # 0x08002a6c
 ('call', 136084024), # 0x08002a6e
 ('mem', True, 'word', 0, 4, 4), # 0x08002a72
 ('imm', 'add', 0, 16), # 0x08002a74
 ('mem', True, 'word', 2, 4, 12), # 0x08002a76
 ('mem', True, 'word', 1, 2, 4), # 0x08002a78
 ('add', 0, 0, 1), # 0x08002a7a
 ('mem', False, 'word', 0, 4, 4), # 0x08002a7c
 ('mem', False, 'half', 5, 2, 2), # 0x08002a7e
 ('mem', True, 'word', 0, 4, 12), # 0x08002a80
 ('mem', True, 'word', 0, 0, 12), # 0x08002a82
 ('mem', False, 'word', 0, 4, 12), # 0x08002a84
 ('compare', 0, 6), # 0x08002a86
 ('branch', 0, 134228620), # 0x08002a88
 ('mem', False, 'word', 4, 0, 8), # 0x08002a8a
 ('compare', 4, 6), # 0x08002a8c
 ('branch', 0, 134228682), # 0x08002a8e
 ('mem', True, 'word', 0, 4, 8), # 0x08002a90
 ('mem', True, 'half', 5, 0, 0), # 0x08002a92
 ('imm', 'cmp', 5, 0), # 0x08002a94
 ('branch', 1, 134228682), # 0x08002a96
 ('mem', True, 'half', 1, 0, 2), # 0x08002a98
 ('literal', 0, 134228688), # 0x08002a9a
 ('compare', 1, 0), # 0x08002a9c
 ('branch', 0, 134228652), # 0x08002a9e
 ('literal', 0, 134228692), # 0x08002aa0
 ('literal', 2, 134228708), # 0x08002aa2
 ('imm', 'mov', 1, 228), # 0x08002aa4
 ('imm', 'mov', 3, 1), # 0x08002aa6
 ('call', 136084024), # 0x08002aa8
 ('mem', True, 'word', 1, 4, 8), # 0x08002aac
 ('mem', True, 'word', 0, 4, 12), # 0x08002aae
 ('mem', False, 'word', 0, 1, 12), # 0x08002ab0
 ('mem', True, 'word', 1, 4, 12), # 0x08002ab2
 ('compare', 1, 6), # 0x08002ab4
 ('branch', 0, 134228668), # 0x08002ab6
 ('mem', True, 'word', 0, 4, 8), # 0x08002ab8
 ('mem', False, 'word', 0, 1, 8), # 0x08002aba
 ('mem', False, 'half', 5, 4, 2), # 0x08002abc
 ('mem', True, 'word', 0, 4, 8), # 0x08002abe
 ('mem', True, 'word', 1, 0, 4), # 0x08002ac0
 ('imm', 'add', 1, 16), # 0x08002ac2
 ('mem', True, 'word', 2, 4, 4), # 0x08002ac4
 ('add', 1, 1, 2), # 0x08002ac6
 ('mem', False, 'word', 1, 0, 4), # 0x08002ac8
 ('pop', 240, False), # 0x08002aca
 ('pop', 1, False), # 0x08002acc
 ('bx', 0), # 0x08002ace
]))
BLOCKS['init_heap']=tuple(block(0x08002b80, [
 ('push', 0, True), # 0x08002b80
 ('literal', 2, 134228884), # 0x08002b82
 ('mem', False, 'word', 0, 2, 0), # 0x08002b84
 ('literal', 2, 134228888), # 0x08002b86
 ('mem', False, 'word', 1, 2, 0), # 0x08002b88
 ('call', 134228296), # 0x08002b8a
 ('pop', 1, False), # 0x08002b8e
 ('bx', 0), # 0x08002b90
]))
BLOCKS['alloc_wrapper']=tuple(block(0x08002b9c, [
 ('push', 0, True), # 0x08002b9c
 ('addi', 1, 0, 0), # 0x08002b9e
 ('literal', 0, 134228908), # 0x08002ba0
 ('mem', True, 'word', 0, 0, 0), # 0x08002ba2
 ('call', 134228316), # 0x08002ba4
 ('pop', 2, False), # 0x08002ba8
 ('bx', 1), # 0x08002baa
]))
BLOCKS['free_wrapper']=tuple(block(0x08002bc4, [
 ('push', 0, True), # 0x08002bc4
 ('addi', 1, 0, 0), # 0x08002bc6
 ('literal', 0, 134228948), # 0x08002bc8
 ('mem', True, 'word', 0, 0, 0), # 0x08002bca
 ('call', 134228488), # 0x08002bcc
 ('pop', 1, False), # 0x08002bd0
 ('bx', 0), # 0x08002bd2
]))
LITERALS={134218852: 33554432, 134228292: 41891, 134228376: 33685508, 134228380: 33685512, 134228384: 33685516, 134228440: 33685508, 134228480: 136109704, 134228484: 136109724, 134228508: 136109704, 134228512: 136109728, 134228688: 41891, 134228692: 136109704, 134228696: 136109740, 134228700: 136109780, 134228704: 136109800, 134228708: 136109844, 134228884: 50334264, 134228888: 50334268, 134228908: 50334264, 134228948: 50334264}


# 新しい合成境界。既存main dispatcherと同じ実体、命令全体を束縛する。
BLOCKS['main_callback_consumer']=tuple(block(0x08000510,[
 ('push',16,True),('call',0x080F6168),('imm','cmp',0,0),('branch',1,0x0800053A),
 ('call',0x0813C034),('shift','lsl',0,0,24),('imm','cmp',0,0),('branch',1,0x0800053A),
 ('literal',4,0x08000540),('mem',True,'word',0,4,0),('imm','cmp',0,0),('branch',0,0x08000530),
 ('call',0x081C7AC8),('mem',True,'word',0,4,4),('imm','cmp',0,0),('branch',0,0x0800053A),
 ('call',0x081C7AC8),('pop',16,False),('pop',1,False),('bx',0)]))
BLOCKS['main_interwork']=tuple(block(0x081C7AC8,[('bx',0)]))
LITERALS[0x08000540]=0x03003130

INS={i.address:i for rows in BLOCKS.values() for i in rows}
ROOT,LIMIT,HEADER,REQUEST=0x02000000,0x1C000,16,0x238
HEAP_CELL,TASKS=shared.HEAP_CELL,shared.TASKS
ROOT_CELL,SIZE_CELL=0x03000A38,0x03000A3C
SCRATCH=(0x02020004,12)
ASSERT=0x081C7A38

def encoded(ins):
 if ins.kind in ('sub','subi'):
  rd,rs,rt=ins.args;return ((0x1E00 if ins.kind=='subi' else 0x1A00)|(rt<<6)|(rs<<3)|rd).to_bytes(2,'little')
 return setup.encoded(ins)

def window(raw,a,n):return dict(address=a,**identity(chunk(raw,a,n)))
def make_review(raw):
 return dict(schema_version=1,required_candidate=CANDIDATE,
  instruction_windows={k:window(raw,v[0].address,sum(i.size for i in v)) for k,v in BLOCKS.items()},
  literal_words={str(a):window(raw,a,4) for a in LITERALS},
  inherited_reviews=PRIOR_REFS,read_mail_type=dict(hit=window(raw,0x08124573,4),instruction_window=window(raw,0x08124572,6),root_table=window(raw,0x0836B380,4),action_table=window(raw,0x08419DEC,4),kind='rooted_thumb_instruction_stream',condition='registered-successful-mail-continuation',universal_epoch_proven=False,maximum_target_access_width_proven=False,donor_eligible=False),classifications_added=0,donor_eligible=False,whole_runtime_lifetime_proven=False)

def binding(raw,review):
 need(set(review)==set(make_review(raw)),'closed runtime review schema')
 need(review['inherited_reviews']==PRIOR_REFS,'fixed full identities of inherited reviews')
 need(review['read_mail_type']==make_review(raw)['read_mail_type'],'fixed conditional read-mail type envelope')
 need(review['schema_version']==1 and review['required_candidate']==CANDIDATE,'fixed candidate')
 need(review['classifications_added']==0 and review['donor_eligible'] is False and review['whole_runtime_lifetime_proven'] is False,'conditional scope cannot promote classifications')
 need(set(review['instruction_windows'])==set(BLOCKS),'exact code roles')
 for k,rows in BLOCKS.items():
  setup.exact_window(raw,review['instruction_windows'][k],rows[0].address,sum(i.size for i in rows))
  for i in rows:need(chunk(raw,i.address,i.size)==encoded(i),'independent allocator instruction semantics')
 need(set(review['literal_words'])=={str(a) for a in LITERALS},'exact allocator literal roles')
 for a,value in LITERALS.items():
  setup.exact_window(raw,review['literal_words'][str(a)],a,4);need(int.from_bytes(chunk(raw,a,4),'little')==value,'allocator literal semantics')
 cfg=[]
 for i in INS.values():
  if i.kind=='branch':
   p=INS.get(i.address-2);need(p and (p.kind=='compare' or p.kind=='imm' and p.args[0]=='cmp'),'allocator CMP flag provenance')
  if i.kind in ('branch','jump'):need(i.args[-1] in INS,'allocator closed direct branch');cfg.append(i.args[-1])
  if i.kind=='call':need(i.args[0] in INS or i.args[0] in (ASSERT,0x080F6168,0x0813C034),'only allocator calls or explicitly unreachable assertion')
  if i.kind not in ('jump','bx') and i.address!=0x080003F4:need(i.address+i.size in INS,'allocator fallthrough does not enter literal pool')
 need(all(INS[t].kind!='branch' for t in cfg),'no direct entry skips CMP')
 return dict(instructions=len(INS),windows=len(BLOCKS),literals=len(LITERALS),closed_direct_branches=len(cfg),assertion_calls_excluded_from_success_contract=True)

class Unknown:pass
U=Unknown()
def concrete(x):return type(x) is int
MASK=(1<<32)-1
class Machine:
    # Thumb全体の汎用emulatorではない。分岐根拠は直前CMPだけに限定し、
    # 他のflagwriterを挟む経路はcfg_proof/runtime gateで拒否する。
    def __init__(self,raw,entry,registers=None,memory=None,instructions=None):
        self.instructions=INS if instructions is None else instructions
        self.raw=raw;self.pc=entry;self.reg=[U]*16;self.reg[13]=0x03007000;self.reg[14]=0xFFFFFFF1
        if registers:
            for k,v in registers.items():self.reg[k]=v
        self.mem={} if memory is None else dict(memory);self.writes=[];self.calls=[];self.steps=0;self.flags=(U,U,U,U);self.flag_pc=None
    def read(self,a,n):
        need(concrete(a),'unknown memory address is not an effect proof');need(n in (1,2,4) and a%n==0 and 0<=a<a+n<=1<<32,'aligned bounded memory read')
        if 0x08000000<=a<0x0A000000:return int.from_bytes(chunk(self.raw,a,n),'little')
        b=[self.mem.get(a+j,U) for j in range(n)]
        return sum(v<<(8*j) for j,v in enumerate(b)) if all(concrete(v) for v in b) else U
    def write(self,a,n,value):
        need(concrete(a),'unknown write target is not an effect proof');need(n in (1,2,4) and a%n==0 and 0<=a<a+n<=1<<32,'aligned bounded memory write');self.writes.append((self.pc,a,n))
        for j in range(n):self.mem[a+j]=(value>>(j*8))&255 if concrete(value) else U
    def cmp(self,a,b):
        self.flag_pc=self.pc
        if not concrete(a) or not concrete(b):self.flags=(U,U,U,U);return
        val=(a-b)&MASK;self.flags=(val>>31,val==0,a>=b, bool(((a^b)&(a^val))>>31))
    def condition(self,c):
        need(self.flag_pc==self.pc-2,'branch flag provenance must be immediately preceding CMP')
        n,z,carry,v=self.flags
        need(all(concrete(x) or type(x) is bool for x in self.flags),'branch needs symbolic split')
        return {0:z,1:not z,2:carry,3:not carry,4:bool(n),5:not n,8:carry and not z,9:not carry or z,10:n==v,11:n!=v,12:not z and n==v,13:z or n!=v}[c]
    def step(self,branch_choice=None):
        need(self.pc in self.instructions,'callee or control-flow effect outside closed model');i=self.instructions[self.pc];k,x=i.kind,i.args;r=self.reg;nxt=self.pc+i.size
        def binary(op,a,b):return op(a,b)&MASK if concrete(a) and concrete(b) else U
        if k=='literal':r[x[0]]=self.read(x[1],4)
        elif k=='movhi':
            r[x[0]]=r[x[1]]
            if x[0]==15:need(concrete(r[15]),'bounded table dispatch');nxt=r[15]&~1
        elif k=='imm':
            op,rd,v=x
            if op=='cmp':self.cmp(r[rd],v)
            elif op=='mov':r[rd]=v
            else:r[rd]=binary((lambda a,b:a+b) if op=='add' else (lambda a,b:a-b),r[rd],v)
        elif k in ('sub','subi'):
            rd,rs,rt=x;r[rd]=binary(lambda a,b:a-b,r[rs],rt if k=='subi' else r[rt])
        elif k in ('add','addi','addhi'):
            rd=x[0];a=r[x[1]] if k!='addhi' else r[rd];b=x[2] if k=='addi' else r[x[2]] if k=='add' else r[x[1]];r[rd]=binary(lambda a,b:a+b,a,b)
        elif k=='compare':self.cmp(r[x[0]],r[x[1]])
        elif k=='shift':
            op,rd,rs,amt=x;v=r[rs]
            r[rd]=U if not concrete(v) else ((v<<amt)&MASK if op=='lsl' else v>>(amt or 32) if op=='lsr' else ((v if v<1<<31 else v-(1<<32))>>(amt or 32))&MASK)
        elif k=='alu':
            op,rd,rs=x
            r[rd]=binary({'and':lambda a,b:a&b,'orr':lambda a,b:a|b,'mul':lambda a,b:a*b,'neg':lambda a,b:-b}[op],r[rd] if op!='neg' else 0,r[rs])
        elif k=='signed_load':
            width,rd,rb,ro=x;n={'byte':1,'half':2}[width];a=binary(lambda a,b:a+b,r[rb],r[ro]);value=self.read(a,n)
            need(concrete(value),'signed load requires explicit bytes');r[rd]=(value-(1<<(n*8)) if value&(1<<(n*8-1)) else value)&MASK
        elif k=='mem':
            load,width,rd,rb,off=x;a=binary(lambda a,b:a+b,r[rb],off);size={'word':4,'half':2,'byte':1}[width]
            if load:r[rd]=self.read(a,size)
            else:self.write(a,size,r[rd])
        elif k=='multiple':
            load,rb,mask=x;need(not load,'store multiple only')
            for rd in range(8):
                if mask&(1<<rd):self.write(r[rb],4,r[rd]);r[rb]+=4
        elif k=='spadd':r[13]+=x[0]
        elif k=='spmem':
            load,rd,off=x
            if load:r[rd]=self.read(r[13]+off,4)
            else:self.write(r[13]+off,4,r[rd])
        elif k in ('push','pop'):
            mask,extra=x;registers=[j for j in range(8) if mask&(1<<j)]+([14 if k=='push' else 15] if extra else [])
            if k=='push':
                r[13]-=4*len(registers)
                for j,rd in enumerate(registers):self.write(r[13]+4*j,4,r[rd])
            else:
                for rd in registers:r[rd]=self.read(r[13],4);r[13]+=4
                if extra:nxt=r[15]&~1
        elif k=='call':self.calls.append((self.pc,x[0]));r[14]=nxt|1;nxt=x[0]
        elif k=='branch':
            need(self.flag_pc==self.pc-2,'branch flag provenance must be immediately preceding CMP')
            nxt=x[1] if (self.condition(x[0]) if branch_choice is None else branch_choice) else nxt
        elif k=='jump':nxt=x[0]
        elif k=='bx':need(concrete(r[x[0]]),'return/indirect unknown');need(r[x[0]]&1==1,'Thumb return/indirect state required');nxt=r[x[0]]&~1
        else:raise ValueError('unsupported effect instruction '+k)
        self.pc=nxt;self.steps+=1;need(self.steps<30000,'finite local effect execution')
    def run(self):
        while self.pc!=0xFFFFFFF0:self.step()
        need(self.reg[13]==0x03007000,'balanced caller stack');return self
    def paths(self):
        pending=[self];finished=[]
        while pending:
            m=pending.pop()
            while m.pc!=0xFFFFFFF0:
                need(m.pc in INS,'selected effect path escaped bound code')
                if INS[m.pc].kind=='branch' and any(isinstance(x,Unknown) for x in m.flags):
                    other=copy.deepcopy(m);other.raw=m.raw;other.step(branch_choice=False);pending.append(other);m.step(branch_choice=True)
                else:m.step()
            need(m.reg[13]==0x03007000,'balanced caller stack on every symbolic path');finished.append(m)
            need(len(finished)+len(pending)<10000,'bounded symbolic path set')
        return finished
    def external_writes(self):return [(a,n) for _,a,n in self.writes if not 0x03006F00<=a<0x03007000]


def setmem(mem,a,n,v):
 need(type(a)is int and type(v)is int,'concrete fixture fields')
 for j in range(n):mem[a+j]=(v>>(8*j))&255

def getmem(mem,a,n):
 need(all(type(mem.get(a+j))is int for j in range(n)),'no fabricated unread field')
 return sum(mem[a+j]<<(8*j) for j in range(n))

def heap_fixture(layout,root=ROOT):
 """layoutは(used,payload)の連続block列。payload byteは作らない。"""
 need(layout and all(type(u)is int and u in (0,1) and type(n)is int and n>=0 and n%4==0 for u,n in layout),'valid layout fields')
 size=sum(HEADER+n for _,n in layout);need(root==ROOT and size<=LIMIT,'bounded ordinary arena fixture')
 mem={};setmem(mem,ROOT_CELL,4,root);setmem(mem,SIZE_CELL,4,size)
 pos=root;previous=root
 for j,(used,n) in enumerate(layout):
  nxt=pos+HEADER+n if j+1<len(layout) else root
  for off,width,val in [(0,2,used),(2,2,0xA3A3),(4,4,n),(8,4,previous),(12,4,nxt)]:setmem(mem,pos+off,width,val)
  previous=pos;pos+=HEADER+n
 return mem,size

def well_formed(mem,size,root=ROOT):
 need(root==ROOT and HEADER<=size<=LIMIT and size%4==0,'ordinary initialized arena geometry')
 need(getmem(mem,ROOT_CELL,4)==root and getmem(mem,SIZE_CELL,4)==size,'current allocator root/size must match admitted arena')
 pos=root;previous=root;rows=[]
 while pos<root+size:
  need(pos+HEADER<=root+size,'full header present')
  used,magic,n,prev,nxt=(getmem(mem,pos+o,w) for o,w in [(0,2),(2,2),(4,4),(8,4),(12,4)])
  need(used in (0,1) and magic==0xA3A3 and n%4==0 and n<=root+size-pos-HEADER,'well formed live/free header')
  end=pos+HEADER+n;need(prev==previous and nxt==(root if end==root+size else end),'noncyclic contiguous bounded chain')
  rows.append((pos,used,n));previous=pos;pos=end
 need(pos==root+size,'whole arena partition');return rows

def execute(raw,entry,regs,mem):
 m=Machine(raw,entry,regs,mem);m.run();return m

def allocate_case(raw,layout,request=REQUEST):
 mem,size=heap_fixture(layout);before=well_formed(mem,size)
 wanted=(request+3)&~3;need(0<request<=LIMIT and wanted<=LIMIT,'bounded nonzero allocator request')
 fits=[row for row in before if row[1]==0 and row[2]>=wanted];need(bool(fits),'success-only contract needs a real free fit; OOM assertion not assumed returning')
 b,_,n=fits[0];m=execute(raw,0x08002B9C,{0:request},mem);after=well_formed(m.mem,size)
 need(m.reg[0]==b+HEADER,'actual first-fit return')
 allocation=next(row for row in after if row[0]==b);need(allocation==(b,1,wanted if n-wanted>31 else n),'actual split/whole metadata')
 need(ROOT+HEADER<=m.reg[0] and m.reg[0]+wanted<=ROOT+size,'returned requested extent bounded and aligned')
 # 全writeをheader/scratchへ限定。pre-existing live payloadへ書くcalleeはない。
 headers=[(a,HEADER) for a,_,_ in before]+[(a,HEADER) for a,_,_ in after]
 need(all(any(lo<=a and a+width<=lo+length for lo,length in headers+[SCRATCH]) for a,width in m.external_writes()),'allocator stores only metadata and explicit scratch')
 for a,u,payload in before:
  if u:need((a,u,payload) in after,'previous live allocation metadata preserved')
 return m,size,dict(block=b,return_pointer=m.reg[0],requested=wanted,allocated=allocation[2],split=n-wanted>31,steps=m.steps)

def geometry_theorem():
 """全aligned payload長を列挙。base移動は下の加減算恒等式で消去する。"""
 checked=0
 for n in range(REQUEST,LIMIT-HEADER+1,4):
  p=HEADER;size=HEADER+n
  if n-REQUEST>31:
   split=p+REQUEST;remain=n-REQUEST-HEADER
   need(remain>=HEADER and split+HEADER+remain==size,'split conserves whole selected block')
   need(p+REQUEST==split,'requested payload disjoint from new header')
  else:need(REQUEST<=n<=REQUEST+28,'whole block only absorbs at most28 aligned bytes')
  need(HEADER+REQUEST<=size<=LIMIT,'allocation and all derived addresses stay in admitted extent')
  checked+=1
 return dict(payload_sizes_checked=checked,requested_size=REQUEST,header_size=HEADER,arena_base=ROOT,arena_size=LIMIT,
  return_alignment=4,return_min=ROOT+HEADER,return_max=ROOT+LIMIT-REQUEST,
  proof_ja='任意block base BについてBを両辺から除いた同一の加減算を検査。well-formed chain内ならB+16+N<=heapEndでwrapなし。scanは有限なnext列を進め、最初のflag0かつN>=568のみ成功。',
  preconditions=['root cell equals ordinary arena base','entire header chain is well formed at call entry','one fitting free block exists','stack valid and nonalias','no concurrent allocator reentry or header/scratch mutation during the call'],
  actual_constructor_entry_preconditions_proven=False)

def allocator_effects(raw,exhaustive=False):
 cases=[]
 sizes=range(REQUEST,LIMIT-HEADER+1,4) if exhaustive else [REQUEST,REQUEST+4,REQUEST+28,REQUEST+32,REQUEST+36,2048,4096,LIMIT-HEADER]
 for n in sizes:
  m,size,record=allocate_case(raw,[(0,n)]);cases.append(record)
 # 同じpathがhead以外、skip-in-use、skip-too-small、非末尾next修復で正しく働くこと。
 for layout in [[(1,16),(0,REQUEST)],[(0,4),(1,4),(0,REQUEST+32)],[(1,0),(0,REQUEST+32),(1,4)],[(0,REQUEST+28),(1,4)],[(1,REQUEST),(0,2048)]]:
  m,size,record=allocate_case(raw,layout);cases.append(record)
 # 起動時の実InitHeap登録producer。関数入口を自然起動全体の証明にはしない。
 init=execute(raw,0x08002B80,{0:ROOT,1:LIMIT},{})
 need(well_formed(init.mem,LIMIT)==[(ROOT,0,LIMIT-HEADER)],'actual InitHeap creates the admitted geometry')
 need(LITERALS[0x08000464]==ROOT,'actual boot literal points to ordinary arena')
 return dict(status='PASS_CONDITIONAL_ALLOCATOR_568',actual_machine_cases=len(cases),exhaustive_selected_payloads=exhaustive,
  writes_ja='選択/分割/nextのheader、02020004..02020010 scratch、callee自身stackのみ。既存live payload・party/task globalには書かない。',
  geometry=geometry_theorem(),natural_boot_reachability=False,current_heap_validity_proven=False,whole_runtime_epoch_proven=False)

def epoch_counterexample(raw):
 """実Free→Allocで同address/metadataが復元される反例。ghost epoch以外に世代はない。"""
 first,size,record=allocate_case(raw,[(0,REQUEST+32)]);p=first.reg[0]
 # Freeはpointer cellをNULL化しない。payload先頭もFree/Allocが書かない。
 setmem(first.mem,HEAP_CELL,4,p);setmem(first.mem,p,4,0x08120319);setmem(first.mem,p+4,4,0x08124561)
 freed=execute(raw,0x08002BC4,{0:p},first.mem);well_formed(freed.mem,size)
 second=execute(raw,0x08002B9C,{0:REQUEST},freed.mem);well_formed(second.mem,size)
 need(second.reg[0]==p and getmem(second.mem,HEAP_CELL,4)==p,'same pointer cell can survive free/reuse')
 need(getmem(second.mem,p,4)==0x08120319 and getmem(second.mem,p+4,4)==0x08124561,'stale callback contents can survive allocation epoch change')
 need(all(first.mem.get(p-HEADER+j)==second.mem.get(p-HEADER+j) for j in range(HEADER)),'same final header bytes cannot prove epoch')
 return dict(status='PASS_ACTUAL_MACHINE_ABA_COUNTEREXAMPLE',same_pointer=True,same_header=True,same_callback_fields=True,same_epoch=False,
  minimal_temporal_condition_ja='constructor成功から最後のobject readまで、このallocationへのFree・heap再初期化/保存退避・header破壊を禁止する。任意の他allocationや非干渉IRQを禁止する必要はない。')

def disjoint(a,n,b,m):return a+n<=b or b+m<=a

def protected_projection(pointer,phase,task_id=0):
 need(type(pointer)is int and pointer%4==0 and ROOT+HEADER<=pointer<=ROOT+LIMIT-REQUEST,'allocator-derived object geometry')
 need(phase in ('before_task','menu','mail_exit','after_mail_copy'),'fixed proof phase')
 need(type(task_id)is int and 0<=task_id<16,'task index domain')
 # task head/list is a separate admissibility predicate; other task data is not frozen.
 out=[dict(address=HEAP_CELL,size=4,role='object pointer')]
 if phase!='after_mail_copy':out += [dict(address=pointer-HEADER,size=8,role='allocation used/magic/extent'),dict(address=pointer,size=8,role='task/exit callback fields')]
 if phase in ('menu','mail_exit'):out.append(dict(address=TASKS+40*task_id,size=5,role='selected task callback and active; membership separate'))
 if phase=='after_mail_copy':out=[dict(address=0x03003134,size=4,role='copied main callback')]
 return out

def projection_preserved(pointer,phase,writes,task_id=0,freed=(),heap_reinitialized=False):
 if phase!='after_mail_copy':
  need(not heap_reinitialized,'heap reset invalidates epoch even if fields restored')
  need(pointer not in freed,'explicit Free ends epoch even if pointer/header restored')
 protect=protected_projection(pointer,phase,task_id)
 for a,n in writes:
  need(type(a)is int and type(n)is int and n>0 and 0<=a<a+n<=1<<32,'known bounded writes only')
  need(all(disjoint(a,n,r['address'],r['size']) for r in protect),'write intersects protected role')
 return True

def minimal_frontier():
 """callsiteごとに返り値と保護射影を分離する。未検証calleeの無害性は付与しない。"""
 rows=[]
 for state,entry in enumerate(setup.STATES):
  upper=setup.STATES[state+1] if state<22 else 0x0811F604
  for pc in sorted(setup.INS):
   i=setup.INS[pc]
   if entry<=pc<upper and i.kind=='call':
    target=i.args[0]
    if state==7 and target==0x0811F640:continue # 失敗exitは成功continuationの前提と両立しない。
    rows.append(dict(state=state,address=pc,target=target,
      return_condition=('link inactive / r0 low byte zero' if state==5 and pc==0x0811F4BC else
                        'low byte nonzero on eventual success; zero may wait' if state in (7,8,15,16) else 'normal return only'),
      effect_condition='preserve allocation epoch, object pointer and currently live callback/control fields; task admission at state20 separately',
      status='bounded_existing_contract' if target in setup.SAFE_ENTRIES or target in setup.CONDITIONAL_ENTRIES else 'conditional_callee_frontier',
      actual_effect_discharged=False))
 return dict(setup_success_calls=rows,
  task_admission_ja='state20の直前に有効なlinked task listと1個以上のfree slotがあれば十分。ResetTasksから全task bytes不変や全16空slotは不要。満杯戻り0を成功扱いしない。',
  task_lifetime_ja='選択taskのactive=1、正しいfunction、RunTasksからのlist所属だけを保持。他task全体やそのdataを凍結しない。',
  irq_condition_ja='IRQ禁止ではなく、必要field・allocator scratch実行区間・現在のtask/cursor制約への非干渉が必要。実IRQ handlerの全保証は本scopeでは未証明。',
  return_condition_ja='成功する有限continuationのみに制限し、待機helperの一般的なeventual returnや全入力での終了を要求しない。',
  mail_release_boundary_ja='SetMainCallback2がobject+4をgMain.callback2へコピーした後にFreePartyPointersが呼ばれる。ReadMail本体の最初の旧hitまでobjectをliveと仮定し続ける必要はない。コピー後はmain callback/cursor/選択monだけを守る。',
  branch_input_ja='普通party menuType0/keepCursor0/有効party slot/適切なmailまたはtutor選択は有限success条件。全入力domainの到達証明へ拡張しない。',
  classification_boundary_ja='既受入assetのallocation-success条件は自然battle到達を不要とする。一方、未知calleeを全て非干渉と置くだけでは実caller間の型継承根拠にならない。親は他workerの実menu/consumer閉鎖と合成して判断する。',
  whole_runtime_lifetime_proven=False,classification_ready_here=False)

def check_local(raw,review,exhaustive=False):
 cfg=binding(raw,review)
 return dict(status='PASS_ALLOCATOR_CONDITIONAL_PROJECTION_NOT_ACCEPTED',cfg=cfg,allocator=allocator_effects(raw,exhaustive),
  epoch=epoch_counterexample(raw),mail_phase=mail_copy_and_consumer(raw),task_admission=task_admission_effects(raw),frontier=minimal_frontier(),whole_input_identity=identity(raw),newly_classified=0,
  donor_eligible=False,whole_runtime_lifetime_proven=False,current_acceptance_claimed=False)

TASK_BLOCKS=('create_task_1','create_task_2','insert_task_1','insert_task_2','insert_task_3','find_first_task','memset')
def bind_task_contract(raw):
 for name in TASK_BLOCKS:
  for i in setup.BLOCKS[name]:
   need(chunk(raw,i.address,i.size)==setup.encoded(i),'task admission exact inherited semantics')
   if i.kind=='literal':
    a=i.args[1];need(int.from_bytes(chunk(raw,a,4),'little')==setup.LITERALS[a],'task admission exact inherited literal')

def task_chain(mem):
 active=[i for i in range(16) if getmem(mem,TASKS+40*i+4,1)==1]
 need(all(getmem(mem,TASKS+40*i+4,1) in (0,1) for i in range(16)),'boolean task active flags')
 if not active:return []
 heads=[i for i in active if getmem(mem,TASKS+40*i+5,1)==254];need(len(heads)==1,'unique active head')
 out=[];i=heads[0];prev=254;priority=-1
 while i!=255:
  need(i in active and i not in out,'finite active reachable chain')
  need(getmem(mem,TASKS+40*i+5,1)==prev,'consistent previous task link')
  pri=getmem(mem,TASKS+40*i+7,1);need(pri>=priority,'ordered priority task list')
  out.append(i);prev=i;priority=pri;i=getmem(mem,TASKS+40*i+6,1)
 need(set(out)==set(active),'every active task is connected')
 return out

def task_fixture(active):
 """一般のvalid task listを生成。各tuple=(slot,priority)。"""
 mem={};need(len({i for i,_ in active})==len(active),'no duplicate active slots')
 for i in range(16):
  for off in range(40):mem[TASKS+40*i+off]=0
 ordered=sorted(active,key=lambda x:x[1])
 for j,(i,pri) in enumerate(ordered):
  need(0<=i<16 and 0<=pri<256,'task fixture domains')
  for off,w,val in [(0,4,0x08120319+4*i),(4,1,1),(5,1,254 if not j else ordered[j-1][0]),(6,1,255 if j+1==len(ordered) else ordered[j+1][0]),(7,1,pri)]:setmem(mem,TASKS+40*i+off,w,val)
 task_chain(mem);return mem

def admit_party_task(raw,mem,function=0x08120319):
 """現在snapshotがvalid+freeという最小述語の下で実CreateTaskを実行。"""
 bind_task_contract(raw);before=task_chain(mem);free=[i for i in range(16) if getmem(mem,TASKS+40*i+4,1)==0]
 need(bool(free),'state20 requires at least one free slot; zero return is ambiguous when full')
 m=setup.Machine(raw,0x08076BB4,{0:function,1:0},mem).run();after=task_chain(m.mem);i=m.reg[0]
 need(i==free[0] and i in after and getmem(m.mem,TASKS+40*i,4)==function,'actual first free registration and active membership')
 need(set(after)==set(before)|{i},'admission preserves all old active membership')
 need(all(TASKS<=a and a+n<=TASKS+640 for a,n in m.external_writes()),'CreateTask writes only task array')
 return dict(task_id=i,active_before=len(before),active_after=len(after),field0=function,priority=0,all_prior_tasks_retained=True),m.mem

def task_admission_effects(raw):
 reports=[]
 for free in range(16):
  # 通常taskの他priority/fieldを保持したまま15activeから1freeを使う。
  active=[(i,(i*17)%256) for i in range(16) if i!=free]
  p,_=admit_party_task(raw,task_fixture(active));need(p['task_id']==free,'all16 possible free positions');reports.append(p)
 p,_=admit_party_task(raw,task_fixture([]));reports.append(p)
 return dict(status='PASS_CONTEXTUAL_TASK_ADMISSION',cases=len(reports),one_free_slot_is_sufficient=True,
  reset_tasks_required=False,zero_return_alone_is_success=False,
  actual_state20_snapshot_admitted=False,preconditions=['well formed task list at state20','one free task slot at state20','no task mutation during CreateTask'],
  inherited_instruction_binding_checked=True)

SOURCE=dict(repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',path='src/malloc.c',git_blob_sha='260c41d0d9f80afbf75fe3fdfbf11393e004bb14',
 url='https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/malloc.c')
def source_proof(data):
 need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==SOURCE['git_blob_sha'],'exact pinned public malloc source')
 return dict(**SOURCE,local='pret-malloc.c',source='src/malloc.c',**identity(data),role_ja='型/構造の説明用。実ROM一致は独立encoderとaddress-size-SHAで検査。')

PRIOR_REFS={'party_review': {'path': 'content/modernization/pr16_dex_hof_callback_party_review.json', 'size': 30492, 'sha256': '9aab39682b78ac5199357955cd634ef2ce14d0c4f0b60643dba944f5b7a31691'}, 'setup_review': {'path': 'content/modernization/pr16_dex_hof_lifetime_setup_review.json', 'size': 33229, 'sha256': '2a39c2c125df3a0b23d3bb6048deee5fb4a1911028e6153ac513bd45a6a9eba5'}, 'menu_review': {'path': 'content/modernization/pr16_dex_hof_lifetime_menu_review.json', 'size': 21519, 'sha256': '47d5a00dce7d7ee200bd4a4fe3cf6b90a280a5514efcbfbc3c5b47bbcc2fa973'}}

MAIL_BLOCK_NAMES=('read_mail_callback_writer','close_menu_same_task','close_menu_exit_consumer','close_menu_fallback_and_free','main_callback_setter','read_mail_target')

def bind_mail_blocks(raw):
 for name in MAIL_BLOCK_NAMES:
  for i in shared.BLOCKS[name]:
   need(chunk(raw,i.address,i.size)==shared.encoded(i),'mail composition exact inherited semantics')
   if i.kind=='literal':need(int.from_bytes(chunk(raw,i.args[1],4),'little')==shared.LITERALS[i.args[1]],'mail composition inherited literal')

def mail_copy_and_consumer(raw):
 """実object field writer→copy→実Free→main consumer→旧hit入口のphase別実行。"""
 bind_mail_blocks(raw)
 instructions=dict(INS)
 for name in MAIL_BLOCK_NAMES:
  for i in shared.BLOCKS[name]:instructions[i.address]=i
 first,size,_=allocate_case(raw,[(0,REQUEST+32)]);p=first.reg[0];mem=first.mem
 setmem(mem,HEAP_CELL,4,p)
 # action8の実table registrationを確認。初期PCの任意指定ではなく、既存menu consumerの登録先から始める。
 need(shared.LITERALS[0x08419DEC]==0x08124535 and int.from_bytes(chunk(raw,0x08419DEC,4),'little')==0x08124535,'actual ReadMail action8 table entry')
 writer=Machine(raw,0x08124534,{0:0},mem,instructions)
 assumptions=[]
 # PlaySEとBeginNormalPaletteFadeはこのphaseの明示未閉鎖契約。黙って無害化しない。
 while writer.pc!=0xFFFFFFF0:
  if writer.pc in (0x08071A70,0x0806FD2C):
   assumptions.append(dict(callee=writer.pc,phase='writer_to_close_task',required='normal return, ABI, preserve object pointer/epoch and chosen task identity',discharged=False))
   writer.reg[0]=U;writer.reg[1]=U;writer.reg[2]=U;writer.reg[3]=U;writer.pc=writer.reg[14]&~1
  else:writer.step()
 need(writer.read(p+4,4)==0x08124561 and writer.read(TASKS,4)==0x081202A5,'real field4 and same task field0 writes')
 need(writer.reg[13]==0x03007000,'writer stack balanced')
 setmem(writer.mem,0x020379EC+7,1,0);setmem(writer.mem,0x0203B014+8,1,0)
 close=Machine(raw,0x081202A4,{0:0},writer.mem,instructions)
 while close.pc!=0x081202EA:close.step()
 need(close.read(0x03003134,4)==0x08124561,'same exit field copied by real SetMainCallback2 before free')
 well_formed(close.mem,size)
 released=execute(raw,0x08002BC4,{0:p},close.mem);well_formed(released.mem,size)
 need(released.read(0x03003134,4)==0x08124561,'actual Free does not overwrite copied callback')
 need(released.read(p-HEADER,2)==0,'object epoch ended before ReadMail body')
 # main callback1=NULL、save-failed/helpのgate0という有限dispatch条件。
 setmem(released.mem,0x03003130,4,0);setmem(released.mem,0x0203B014+9,1,0)
 main=Machine(raw,0x08000510,memory=released.mem,instructions=instructions)
 while main.pc!=0x08124572:
  if main.pc in (0x080F6168,0x0813C034):
   assumptions.append(dict(callee=main.pc,phase='main_dispatch',required='return zero, ABI, preserve copied callback and cursor',discharged=False))
   main.reg[0]=0;main.reg[1]=U;main.reg[2]=U;main.reg[3]=U;main.pc=main.reg[14]&~1
  else:main.step()
 need(main.reg[0]==0x020241E4 and main.reg[1]==64,'ReadMail prefix produces selected Pokemon and field64 at BL crossing hit')
 need(chunk(raw,0x08124572,4)==shared.encoded(shared.Ins(0x08124572,'call',(0x0803F354,))),'whole GetMonData BL begins before odd legacy hit')
 return dict(status='PASS_CONDITIONAL_READ_MAIL_PHASE_COMPOSITION',root_table_slot=0x08419DEC,root_entry=0x08124534,
  object_exit_writer=0x08124548,copy_call=0x081202D0,last_object_read=0x081202CA,
  free_call_after_copy=0x081202EA,main_dispatch_call=0x08000536,main_callback=0x08124561,
  old_hit=shared.HIT,complete_instruction_window=dict(address=0x08124572,size=6),
  freed_object_needed_at_hit=False,actual_free_executed=True,selected_party_slot=0,
  getmondata_field_at_hit=64,source_byte_is_instruction_encoding=True,
  maximum_target_access_width_proven=False,donor_eligible=False,
  conditional_calls=assumptions,
  unclosed_intervals=['selected action8 table dispatch requires constructed menu/valid cursor','between writer close-task registration and its scheduler dispatch','remaining FreePartyPointers/DestroyTask/party scheduler tail/main-loop callbacks after copy before next dispatch'],
  natural_play_reachability=False,emits_typed_regions=False,universal_runtime_ready=False)


def compose_prior(raw,review,sources):
 """巨大な旧proofをコピーしない。原本identity・使用する境界のみ検証する。"""
 import pr16_dex_hof_callback_party_task as old_task
 import pr16_dex_hof_lifetime_menu as menu
 old={}
 for key,ref in PRIOR_REFS.items():
  need(key in sources,'explicit inherited review input: '+key);b=sources[key]
  need(identity(b)=={k:ref[k] for k in ('size','sha256')},'immutable full inherited review')
  old[key]=json.loads(b)
 shared.source_proof(old['party_review'],{k:sources[k] for k in ('BPRJ.ld','pret-party_menu.c')})
 # 各旧moduleの固定命令定義とliteral/selectorをcurrent inputへbindする。旧unit/effectsの再走ではない。
 for mod in (shared,old_task,setup,menu):
  for rows in mod.BLOCKS.values():
   for i in rows:need(chunk(raw,i.address,i.size)==mod.encoded(i),'inherited bound semantics for new composition')
  for a,value in mod.LITERALS.items():need(int.from_bytes(chunk(raw,a,4),'little')==value,'inherited exact literal role for new composition')
 for a,v in setup.TABLE.items():need(int.from_bytes(chunk(raw,a,4),'little')==v,'all23 inherited setup state targets')
 for a,n,value in shared.DATA_FIELDS.values():need(int.from_bytes(chunk(raw,a,n),'little')==value,'mail index/count fields')
 setup.cfg_proof()
 # 下記は全て上でbind済みの根/実field/実calleeへの接続。全callee効果の済印ではない。
 chain=[
  ('start_menu_action_table',0x0836B380,0x0806EC3D),
  ('field_party_main_callback',0x0806EC62,0x081277E9),
  ('field_party_constructor',0x08127800,0x0811F24C),
  ('constructor_alloc',0x0811F280,0x08002B9C),
  ('constructor_main_callback',0x0811F384,0x0811F3D9),
  ('setup_task',0x0811F5C4,0x08120319),
  ('setup_main_callback',0x0811F624,0x0811F3A9),
  ('ordinary_action_hook_default',0x09097AA8,0x0812053B),
  ('outer_menu_task',0x08123428,0x08123439),
  ('mail_action6_table',0x08419DDC,0x081244D1),
  ('read_action8_table',0x08419DEC,0x08124535),
  ('exit_callback_field4',0x0812455C,0x08124561),
  ('close_task_field0',0x081202A0,0x081202A5),
  ('copy_before_free',0x081202D0,0x08000544),
  ('next_main_dispatch',0x08000536,0x081C7AC8)]
 # chain label/addressは説明のみ。権限のある分類/TypedRegion生成には使わない。
 return dict(status='PASS_INHERITED_BOUNDARIES_COMPOSED_NO_DUPLICATED_PROOF',inherited_reviews=PRIOR_REFS,
  rooted_registration_chain=[dict(role=k,address=a,target=t) for k,a,t in chain],
  mail=mail_copy_and_consumer(raw),frontier=minimal_frontier(),emits_typed_regions=False,
  unclosed_minimal_ja=['setup成功continuation中のobject/callback field射影とepoch保存','mail選択taskのactive/list所属と有効cursorを各dispatchまで維持','copy後の残destructor/描画/main-loop callerがgMain.callback2と選択cursorを維持'],
  excluded_overrequirements_ja=['全ゲーム自然到達','全23helperの任意入力に対する停止性','heap全体不変','全16task空の保持','IRQ全禁止','ReadMail hitまで旧party allocationを生存保持'],
  universal_runtime_ready=False)


def _regions(raw,inherited,review,sources):
 proof=check_local(raw,review);proof['composition']=compose_prior(raw,review,sources)
 need(inherited['candidate']==CANDIDATE,'fixed accepted parent candidate; diagnostic raw identity reported separately')
 for hit in (0x08124573,0x08126B0B):
  original=next(h for h in inherited['hits'] if h['address']==hit)
  need(not original['accepted'] and not original['owner_candidates'],'only unchanged owner-external unknown targets')
 original=next(h for h in inherited['hits'] if h['address']==0x08124573)
 type_review=review['read_mail_type'];need({k:original[k] for k in ('address','size','sha256')}==type_review['hit'],'exact inherited ReadMail hit identity')
 source_proof(sources['pret-malloc.c'])
 phase=proof['composition']['mail'];need(phase['source_byte_is_instruction_encoding'] and phase['actual_free_executed'] and not phase['freed_object_needed_at_hit'],'real producer-copy-free-consumer phase')
 w=type_review['instruction_window'];need((w['address'],w['size'])==(0x08124572,6),'only complete BL and LDR crossing')
 evidence=dict(root=dict(kind='party_start_menu_action',table_slot=type_review['root_table'],entry=0x0806EC3C),
  instruction_window=w,instructions=[dict(address=0x08124572,size=4),dict(address=0x08124576,size=2)],
  root_verified=True,literal_pool_included=False,whole_function_range_classified=False,
  bl_return_observed=False,successor_type='static BL return successor',
  successor_boundary_ja='0x08124576のLDRはBL0x08124572の静的return successorとして型付けする。GetMonDataの復帰をこの実行で観測した意味ではない。',
  conditional_registration_type_proven=True,condition='successful ordinary party and mail selection using the registered callback/task fields',
  registration_chain=proof['composition']['rooted_registration_chain'],
  minimal_conditioned_ja=['well-formed successful568byte constructor allocation','setup/helper正常returnと各phaseの必要field保存','有効なparty/mail cursorとmail入力選択','CreateTask直前のvalid task list＋1free slotと登録taskのdispatch','copyまで同一object epoch、copy以後gMain.callback2と選択cursor保存'],
  full_story_reachability_claimed=False,universal_allocation_epoch_proven=False,all_opaque_effects_proven=False,
  old_allocation_required_at_hit=False,maximum_target_access_width_proven=False,indirect_reference_complete=False,donor_eligible=False,
  scope_ja='既受入storage/assetと同じ登録型に限る条件付き命令stream。任意PC seedではなく実StartMenu table→constructor/setup→mail action8→field4→gMain consumer。全動作・生存保証・領域退役の証明とは独立。')
 regions=[shared.d.TypedRegion(w['address'],w['address']+w['size'],'rooted_thumb_instruction_stream',evidence)]
 proof.update(status='PASS_ONE_CONDITIONAL_REGISTERED_READ_MAIL_TYPE',newly_classified=1,checked_unknown_hits=[0x08124573,0x08126B0B],
  newly_typed_hits=[0x08124573],retained_unknown_hits=[0x08126B0B],conditional_registration_type_proven=True,
  universal_allocation_epoch_proven=False,maximum_target_access_width_proven=False,indirect_reference_complete=False,donor_eligible=False)
 return regions,proof

def regions(raw,inherited,review,sources):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current candidate required for accepted new type')
 return _regions(raw,inherited,review,sources)

def protected_windows(review):
 need(review['inherited_reviews']==PRIOR_REFS,'fixed inherited references')
 return list(review['instruction_windows'].values())+list(review['literal_words'].values())+[review['read_mail_type'][k] for k in ('instruction_window','root_table','action_table')]

SOURCE_EXPECTED={'pret-malloc.c':{'size':6256,'sha256':'a81ff86e81b72f4a57d5c891e3f50d93e0c2a75a3e3ec37a48bdb84041ad369e'}}
