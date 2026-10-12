"""effect32/65の実登録と有限serializerから回復/壁3境界12byteだけを型付けする。"""
from __future__ import annotations
import copy, hashlib, json, re
import pr16_dex_hof_battle_tail_roots as tail
import pr16_dex_hof_finite_producer_roots as finite
import pr16_dex_hof_battle_script_roots as rooted
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as native
import pr16_dex_hof_runtime_party as rt
prior = rooted.prior
need, identity, chunk = d.need, d.identity, d.chunk
exact, encoded = rooted.exact, rooted.encoded
CANDIDATE, DIAGNOSTIC = rooted.CANDIDATE, rooted.DIAGNOSTIC
KIND = 'registered_healing_veil_minimum_cross_field'
TYPE_CATEGORY = 'data'
HITS = (0x0900360B, 0x090036CD, 0x09003C02)
ROOTS = {32: 0x09003533, 65: 0x09003BE5}
CURSOR = prior.CURSOR
SOURCE_IDS = copy.deepcopy(rooted.SOURCE_IDS)
SOURCE_ROLES = copy.deepcopy(rooted.SOURCE_ROLES)
COMMON_ROOT_SHA256 = rooted.COMMON_ROOT_SHA256
CLAIMS = dict(finite.CLAIMS, set_target_partner_success_proven=False,
              recovery_or_status_effect_success_proven=False,
              set_reflect_or_aurora_veil_success_proven=False,
              natural_bank_value_generation_proven=False)
GRAMMAR = dict(tail.GRAMMAR, **{
 'setreflect': (0x7E,1,()),
 'printfromtable': (0x13,5,((1,4,'data_pointer'),)),
 'setdamageasrestorehalfmaxhp': (0x7B,6,((1,4,'script_pointer'),(5,1,'bank'))),
 'orword': (0x35,9,((1,4,'write_address'),(5,4,'mask'))),
 'graphicalhpupdate': (0x0B,2,((1,1,'bank'),)),
 'datahpupdate': (0x0C,2,((1,1,'bank'),)),
 'jumpiffainted': (0xE3,6,((1,1,'bank'),(2,4,'script_pointer'))),
 'cureprimarystatus': (0xFF02,7,((2,1,'bank'),(3,4,'script_pointer'))),
 'refreshhpbar': (0x98,2,((1,1,'bank'),)),
})
REFLECT = (
 (0x09003BE5,'attackcanceler',()),
 (0x09003BE6,'jumpifmove',(0,0x02023CAA,0x28A,0x09003C04)),
 (0x09003BF2,'attackstring',()), (0x09003BF3,'ppreduce',()),
 (0x09003BF4,'setreflect',()), (0x09003BF5,'attackanimation',()),
 (0x09003BF6,'waitanimation',()),
 (0x09003BF7,'printfromtable',(0x09167754,)),
 (0x09003BFC,'waitmessage',(0x40,)),
 (0x09003BFF,'goto',(0x081BA90A,)),
 (0x09003C04,'jumpifcounter',(1,16,1,0,0x09008E11)),
)
RECOVER = (
 (0x09003533,'attackcanceler',()),
 (0x09003534,'jumpifmove',(0,0x02023CAA,0x2A4,0x090035A2)),
 (0x09003540,'attackstring',()), (0x09003541,'ppreduce',()),
 (0x09003542,'jumpifmove',(0,0x02023CAA,0x1E3,0x09003592)),
 (0x0900354E,'jumpifmove',(0,0x02023CAA,0x30A,0x090035E2)),
 (0x0900355A,'jumpifmove',(0,0x02023CAA,0x323,0x09003681)),
 (0x09003566,'jumpifmove',(0,0x02023CAA,0x344,0x09003681)),
)
LIFE_DEW = (
 (0x090035E2,'callasm',(0x090CC8C1,)),
 (0x090035E7,'attackanimation',()), (0x090035E8,'waitanimation',()),
 (0x090035E9,'setdamageasrestorehalfmaxhp',(0x09003644,1)),
 (0x090035EF,'orword',(0x02023D30,0x100)),
 (0x090035F8,'graphicalhpupdate',(1,)), (0x090035FA,'datahpupdate',(1,)),
 (0x090035FC,'printstring',(0x4B,)), (0x090035FF,'waitmessage',(0x40,)),
 (0x09003602,'callasm',(0x090C8E35,)),
 (0x09003607,'jumpiffainted',(0,0x081BA90A)),
 (0x0900360D,'jumpifcounter',(0,2,1,0,0x090073D1)),
)
JUNGLE_HEALING = (
 (0x09003681,'callasm',(0x090CD065,)),
 (0x09003686,'attackanimation',()), (0x09003687,'waitanimation',()),
 (0x09003688,'setdamageasrestorehalfmaxhp',(0x090036A6,1)),
 (0x0900368E,'orword',(0x02023D30,0x100)),
 (0x09003697,'graphicalhpupdate',(1,)), (0x09003699,'datahpupdate',(1,)),
 (0x0900369B,'printstring',(0x4B,)), (0x0900369E,'waitmessage',(0x40,)),
 (0x090036A1,'goto',(0x090036AC,)),
 (0x090036A6,'printstring',(0x4C,)), (0x090036A9,'waitmessage',(0x40,)),
 (0x090036AC,'cureprimarystatus',(1,0x090036C4)),
 (0x090036B3,'refreshhpbar',(1,)),
 (0x090036B5,'setword',(0x0203DF98,0x0900793D)),
 (0x090036BE,'printstring',(0x184,)), (0x090036C1,'waitmessage',(0x40,)),
 (0x090036C4,'callasm',(0x090C8E35,)),
 (0x090036C9,'jumpiffainted',(0,0x081BA90A)),
 (0x090036CF,'jumpifcounter',(0,2,1,0,0x09003734)),
)
SEQUENCES = (REFLECT,RECOVER,LIFE_DEW,JUNGLE_HEALING)
PROGRAM = sum(SEQUENCES,())
MOVE_EFFECTS = {0x28A:65,0x2A4:32,0x1E3:32,0x30A:32,0x323:32,0x344:32}
CONTROL_INS = dict(tail.CONTROL_INS)
POINTER_INS = dict(tail.POINTER_INS)
DISPATCH_INS = dict(finite.DISPATCH_INS)
# E3の実JP handler・redirect・bank0を有限の独立意味へ結合する。
E3_ENTRY = 0x0802C514
E3_SLOT = 0x0903F7DC
CURSOR = 0x02023CD4
TARGET = 0x02023CCC
ATTACKER = 0x02023CCB
ACTIVE = 0x02023B24
MONS = 0x02023B44
MON_STRIDE, HP_OFFSET, HP_SIZE = 88, 40, 2
COMMANDS = (0x09003607, 0x090036C9)
BRANCH_POINTER = 0x081BA90A
E3_BLOCKS = {
 'entry_hp_and_taken': native.block(E3_ENTRY, [
  ('push',16,True), ('literal',4,0x0802C550), ('mem',True,'word',0,4,0),
  ('mem',True,'byte',0,0,1), ('call',0x08016634),
  ('literal',1,0x0802C554), ('mem',False,'byte',0,1,0),
  ('literal',2,0x0802C558), ('mem',True,'byte',1,1,0),
  ('imm','mov',0,88), ('alu','mul',0,1), ('add',0,0,2),
  ('mem',True,'half',0,0,40), ('imm','cmp',0,0), ('branch',1,0x0802C55C),
  ('mem',True,'word',2,4,0), ('mem',True,'byte',1,2,2),
  ('mem',True,'byte',0,2,3), ('shift','lsl',0,0,8), ('alu','orr',1,0),
  ('mem',True,'byte',0,2,4), ('shift','lsl',0,0,16), ('alu','orr',1,0),
  ('mem',True,'byte',0,2,5), ('shift','lsl',0,0,24), ('alu','orr',1,0),
  ('mem',False,'word',1,4,0), ('jump',0x0802C562)]),
 'next_and_return': native.block(0x0802C55C, [
  ('mem',True,'word',0,4,0), ('imm','add',0,6), ('mem',False,'word',0,4,0),
  ('pop',16,False), ('pop',1,False), ('bx',0)]),
 'legacy_bank_redirect': native.block(0x08016634,[('literal',1,0x08016638),('bx',1)]),
 **{name:rooted.BLOCKS[name] for name in ('bank_resolver','bank_return','target_bank')},
}
E3_INS = {i.address:i for block in E3_BLOCKS.values() for i in block}
E3_WORDS = {
 E3_SLOT:E3_ENTRY|1,
 0x0802C550:CURSOR, 0x0802C554:ACTIVE, 0x0802C558:MONS,
 0x08016638:0x090D3D2D,
 0x090D3D8C:0x09161410, 0x09161410:0x090D3D7E, 0x090D3DA4:TARGET,
}

INS = {**CONTROL_INS,**POINTER_INS,**DISPATCH_INS,**E3_INS}
WORDS = {
 0x08021E6C:CURSOR,0x08021F5C:CURSOR,0x08021F60:0x08021F64,
 0x08021F64:0x08021F7C,0x08021F68:0x08021F84,
 0x0911B0E0:CURSOR,0x090D3D8C:0x09161410,
 0x09161410:0x090D3D7E,0x09161414:0x090D3D84,
 0x090D3DA4:0x02023CCC,0x090D3DA8:0x02023CCB,
 prior.EFFECTS+32*4:ROOTS[32],prior.EFFECTS+65*4:ROOTS[65],
 prior.PRIMARY:0x090BD385,prior.PRIMARY+40*4:0x08021E51,
 prior.PRIMARY+42*4:0x08021F11,
 prior.SECONDARY+9*4:0x0911AF69,prior.PRIMARY+255*4:0x0911AA8D,
 0x080154AC:prior.PRIMARY,0x080154B0:CURSOR,
 0x0911AAA4:CURSOR,0x0911AAA8:prior.SECONDARY,
 **E3_WORDS,
}
Machine = tail.Machine

def source_proof(review,sources):
 """公開source全体identityと選択serializerの完全幅・順序を独立に閉じる。"""
 tail.source_proof(review,sources)
 macro=re.sub(r'@[^\n]*','',sources[SOURCE_ROLES['battle_script_macros.s']].decode())
 shapes={
 'setreflect':[(1,'0x7e')],
 'printfromtable':[(1,'0x13'),(4,'\\table')],
 'setdamageasrestorehalfmaxhp':[(1,'0x7b'),(4,'\\rom_address'),(1,'\\int')],
 'orword':[(1,'0x35'),(4,'\\pointer'),(4,'\\value')],
 'graphicalhpupdate':[(1,'0x0b'),(1,'\\bank')],
 'datahpupdate':[(1,'0x0c'),(1,'\\bank')],
 'jumpiffainted':[(1,'0xe3'),(1,'\\bank'),(4,'\\rom_address')],
 'cureprimarystatus':[(1,'0xFF'),(1,'0x02'),(1,'\\bank'),(4,'\\rom_address')],
 'refreshhpbar':[(1,'0x98'),(1,'\\bank')],
 }
 for name,shape in shapes.items():
  bodies=re.findall(r'\.macro\s+'+name+r'(?:[ \t][^\n]*)?\n(.*?)\.endm',macro,re.S)
  need(len(bodies)==1,'一意の公開serializer '+name);fields=[]
  for line in bodies[0].splitlines():
   if not line.strip():continue
   m=re.fullmatch(r'\s*\.(byte|2byte|4byte|word)\s+(.+)',line)
   need(m is not None,'有限直接serializerだけ')
   fields.extend(({'byte':1,'2byte':2,'4byte':4,'word':4}[m[1]],x.strip())for x in m[2].split(','))
  need(fields==shape and sum(n for n,_ in fields)==GRAMMAR[name][1],'完全operand幅 '+name)
 defs=sources[SOURCE_ROLES['asm_defines.s']].decode()
 for name,value in [('AURORA_VEIL_TIMERS',16),('HEAL_BLOCK_TIMERS',2),('HIT_MARKER',0x02023D30),('HITMARKER_IGNORE_SUBSTITUTE',0x100)]:
  m=re.search(r'^\.equ\s+'+name+r',\s*(\w+)',defs,re.M)
  need(m is not None and int(m[1],0)==value,'公開定数 '+name)
 src=sources[SOURCE_ROLES['assembly/battle_scripts/general_attack_battle_scripts.s']].decode()
 def lines(start,end):
  part=src.split(start+':',1)[1].split(end,1)[0]
  return [' '.join(x.split())for x in re.sub(r'@[^\n]*','',part).splitlines()
          if x.strip()and not x.strip().endswith(':')]
 need(lines('BS_065_Reflect','AuroraVeilBS:')==[
  'attackcanceler','jumpifmove MOVE_AURORAVEIL AuroraVeilBS','attackstring','ppreduce','setreflect',
  'attackanimation','waitanimation','printfromtable gReflectLightScreenSafeguardStringIds',
  'waitmessage DELAY_1SECOND','goto BS_MOVE_END'],'effect65の全10命令31byte')
 need(lines('AuroraVeilBS','attackstring')[0]==
  'jumpifcounter BANK_ATTACKER AURORA_VEIL_TIMERS NOTEQUALS 0 FAILED_PRE','AuroraVeil右FF09の独立根')
 need(lines('BS_032_Recover','RecoverBS:')==[
  'attackcanceler','jumpifmove MOVE_PURIFY PurifyBS','attackstring','ppreduce',
  'jumpifmove MOVE_ROOST RoostBS','jumpifmove MOVE_LIFEDEW LifeDewBS',
  'jumpifmove MOVE_JUNGLEHEALING JungleHealingBS','jumpifmove MOVE_LUNARBLESSING JungleHealingBS'],
  'effect32全5selector/8命令63byte')
 shared=['attackanimation','waitanimation']
 heal=['orword HIT_MARKER HITMARKER_IGNORE_SUBSTITUTE','graphicalhpupdate BANK_ATTACKER',
       'datahpupdate BANK_ATTACKER','printstring 0x4B','waitmessage DELAY_1SECOND']
 need(lines('LifeDewBS','jumpifability')==[
  'callasm TryFailLifeDew',*shared,'setdamageasrestorehalfmaxhp LifeDewAttackerFullHealthBS BANK_ATTACKER',*heal,
  'callasm SetTargetPartner','jumpiffainted BANK_TARGET BS_MOVE_END',
  'jumpifcounter BANK_TARGET HEAL_BLOCK_TIMERS NOTEQUALS 0x0 BattleScript_NoHealTargetAfterHealBlock'],
  'LifeDew独立prefix12命令53byte')
 need(lines('JungleHealingBS','jumpifability')==[
  'callasm TryFailJungleHealing',*shared,'setdamageasrestorehalfmaxhp JungleHealingAttackerFullHealthBS BANK_ATTACKER',*heal,
  'goto JungleHealingTryClearAttackerStatusBS','printstring 0x4C','waitmessage DELAY_1SECOND',
  'cureprimarystatus BANK_ATTACKER JungleHealingRestorePartnerHPBS','refreshhpbar BANK_ATTACKER',
  'setword BATTLE_STRING_LOADER PurifyString','printstring 0x184','waitmessage DELAY_1SECOND',
  'callasm SetTargetPartner','jumpiffainted BANK_TARGET BS_MOVE_END',
  'jumpifcounter BANK_TARGET HEAL_BLOCK_TIMERS NOTEQUALS 0x0 BattleScript_NoHealPartnerAfterHealBlock_JungleHealing'],
  'JungleHealing独立prefix20命令88byte。goto先はfallthroughではない')
 effects=sources[SOURCE_ROLES['assembly/data/move_effect_table.s']].decode().split('gBattleScriptsForMoveEffects:',1)[1].split('gSetStatusMoveEffects:',1)[0]
 words=lambda s:re.findall(r'^\s*\.word\s+(\S+)',s,re.M)
 need([words(effects)[e]for e in (32,65)]==['BS_032_Recover','BS_065_Reflect'],'独立の公開effect登録')
 table=sources[SOURCE_ROLES['assembly/data/battle_script_commands_table.s']].decode().split('gBattleScriptingCommandsTable:',1)[1].split('gBattleScriptingCommandsTable2:',1)[0]
 need(words(table)[0xE3]=='0x802C515','公開E3登録。現JP handlerの代用にはしない')
 e3_source_proof(sources)
 return True

def bind_program(raw):
 rows=[]
 for a,name,values in PROGRAM:
  op,size,fields=GRAMMAR[name];b=chunk(raw,a,size)
  prefix=bytes([255,op&255]if op>255 else[op])
  need(b[:len(prefix)]==prefix,'登録root由来の実opcode')
  need(tuple(int.from_bytes(b[o:o+n],'little')for o,n,_ in fields)==values,'全operandの独立意味')
  rows.append(dict(address=a,name=name,opcode=op,size=size,
   fields=[dict(address=a+o,size=n,role=role,value=v)for(o,n,role),v in zip(fields,values)]))
 for sequence,n in zip(SEQUENCES,(41,63,53,88)):
  for left,right in zip(sequence,sequence[1:]):
   need(left[0]+GRAMMAR[left[1]][1]==right[0],'隣接serializer境界。自然実行successorとは別')
  need(sum(GRAMMAR[name][1]for _,name,_ in sequence)==n,'閉じた有限prefix長')
 for move,effect in MOVE_EFFECTS.items():
  need(chunk(raw,0x090421F4+12*move,1)[0]==effect,'現Move表のeffect producer')
 return rows

def semantic_bindings(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'独立JP命令意味 '+i.kind)
 for a,value in WORDS.items():need(d.u32(raw,a)==value,'真のslot/literalの独立値')
 return True

def control_proof(raw):
 semantic_bindings(raw);bind_program(raw);result=[]
 for a,name,values in PROGRAM:
  if name not in ('jumpifmove','goto'):continue
  op=GRAMMAR[name][0]
  for edge in (('taken',)if name=='goto'else('taken','next')):
   value=None;target=values[-1]if edge=='taken'else a+12;writes=[]
   if name!='goto':
    value=values[2]if edge=='taken'else values[2]^1
    writes.append(dict(address=CURSOR,size=4,value=a+12))
   if edge=='taken':writes.append(dict(address=CURSOR,size=4,value=target))
   cursor,actual,trace,reads=prior.thumb_handler(raw,prior.HANDLERS[op],a,value)
   need(cursor==target and actual==writes,'実JP handlerのtaken/nextと全write')
   need(all(r['address']in CONTROL_INS for r in trace),'選択pathの全実命令を独立集合へ束縛')
   pointer=a+(1 if name=='goto'else 8)
   need(all(any(r['address']<=b<r['address']+r['size']for r in reads)for b in range(pointer,pointer+4)),
        '完全4byte target operandを実際に読む')
   result.append(dict(command=a,opcode=op,edge=edge,entry=prior.HANDLERS[op],next_cursor=target,
                      command_entry_condition=True,natural_entry_proven=False))
 return result

def dispatch_proof(raw):
 semantic_bindings(raw);bind_program(raw);proof=[]
 for a,name,_ in PROGRAM:
  if name not in ('jumpifmove','goto','jumpiffainted','jumpifcounter'):continue
  op,size,_=GRAMMAR[name];extended=op>255
  expected={42:prior.HANDLERS[42],40:prior.HANDLERS[40],0xE3:E3_ENTRY,0xFF09:0x0911AF68}[op]
  need(type(expected)is int,'E3実handlerを解決済み')
  mem={};rt.setmem(mem,CURSOR,4,a)
  m=Machine(raw,0x08015492,memory=mem,instructions=DISPATCH_INS)
  while m.pc!=expected:
   need(m.steps<32,'有限dispatchの停止');m.step()
  slots=[prior.PRIMARY+4*(255 if extended else op)];operands=[a]
  if extended:slots.append(prior.SECONDARY+4*(op&255));operands.append(a+1)
  need(all((cell,4)in m.reads for cell in slots),'実opcode由来の実table slot')
  need(all((cell,1)in m.reads for cell in operands),'完全opcodeをLDRBで読む')
  need(rt.getmem(m.mem,CURSOR,4)==a+int(extended),'secondaryだけがcursorを1byte進める')
  need([w for w in m.writes if w[1]==CURSOR]==([(0x0911AA94,CURSOR,4)]if extended else[]),'実cursor writeだけ')
  need(all(addr==CURSOR and n==4 or 0x03006F00<=addr<addr+n<=0x03007000 for _,addr,n in m.writes),'許容write閉集合')
  proof.append(dict(command=a,opcode=op,opcode_byte_reads=operands,handler=expected,
                    dispatch_slots=slots,cursor_at_handler=a+int(extended),steps=m.steps,
                    command_entry_condition=True,handler_executed=False,natural_entry_proven=False))
 return proof

def pointer_read_proof(raw):
 semantic_bindings(raw);bind_program(raw);proof=[]
 for a,name,values in PROGRAM:
  if name!='jumpifcounter':continue
  bank=values[0]
  for actual_bank in range(4):
   mem={};rt.setmem(mem,CURSOR,4,a+1)
   rt.setmem(mem,0x02023CCC,1,actual_bank if bank==0 else actual_bank^3)
   rt.setmem(mem,0x02023CCB,1,actual_bank if bank==1 else actual_bank^3)
   m=Machine(raw,0x0911AF68,memory=mem,instructions=POINTER_INS)
   while m.pc!=0x0911AF94:
    need(m.steps<64,'有限FF09 pointer-read停止');m.step()
   need(m.reg[4]==values[-1]and m.reg[0]==actual_bank,'完全pointerと実bank読取り')
   need((0x09161410+4*bank,4)in m.reads and(0x02023CCC-bank,1)in m.reads,'実bank slotとRAM')
   need((0x09161410+4*(1-bank),4)not in m.reads and(0x02023CCB+bank,1)not in m.reads,'別bank代入禁止')
   need(all((p,1)in m.reads for p in range(a+6,a+10)),'FF09 target完全4byteの実読取')
   need(m.calls==[(0x0911AF74,0x090D3D2C)],'未証明calleeのstubなし')
   need(rt.getmem(m.mem,CURSOR,4)==a+1,'pointer-readでcursor捏造なし')
   need(all(0x03006F00<=addr<addr+n<=0x03007000 for _,addr,n in m.writes),'正規stack以外へのwriteなし')
  proof.append(dict(command=a,handler=0x0911AF68,stop=0x0911AF94,pointer=values[-1],
                    pointer_bytes=4,bank_operand=bank,resolver_slot=0x09161410+4*bank,
                    bank_read_address=0x02023CCC-bank,distinct_bank_value_cases=4,
                    command_entry_condition=True,natural_entry_proven=False,counter_branch_executed=False))
 return proof


class E3Machine(rooted.Machine):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.reads=[];self.write_values=[];self.trace=[]
 def read(self,a,n):
  self.reads.append((self.pc,a,n));return super().read(a,n)
 def write(self,a,n,v):
  self.write_values.append((self.pc,a,n,v));return super().write(a,n,v)
 def step(self,branch_choice=None):
  self.trace.append(self.pc);return super().step(branch_choice)

def e3_source_proof(sources):
 """閉じた8sourceのwhole SHA/Git blobを検証し、その後E3の独立型根を検証。"""
 rooted.source_proof({'source_bindings':rooted.SOURCE_IDS},sources)
 macro=re.sub(r'@[^\n]*','',sources[rooted.SOURCE_ROLES['battle_script_macros.s']].decode())
 body=re.findall(r'\.macro\s+jumpiffainted(?:[ \t][^\n]*)?\n(.*?)\.endm',macro,re.S)
 need(len(body)==1,'独立jumpiffainted serializerは一意')
 fields=[]
 for line in body[0].splitlines():
  if not line.strip():continue
  m=re.fullmatch(r'\s*\.(byte|2byte|4byte|word)\s+(.+)',line)
  need(m is not None,'独立serializerは直接fieldだけ')
  fields.extend(({'byte':1,'2byte':2,'4byte':4,'word':4}[m[1]],x.strip())for x in m[2].split(','))
 need(fields==[(1,'0xe3'),(1,'\\bank'),(4,'\\rom_address')],'E3/1byte BANK/4byte pointerの独立serializer')
 need(re.search(r'^\.equ\s+BANK_TARGET,\s*0(?:x0)?\s*$',macro,re.M) is not None,'独立BANK_TARGET=0')
 need(re.search(r'^\.equ\s+BS_MOVE_END,\s*0x81BA90A\s*$',macro,re.M) is not None,'独立BS_MOVE_END')
 table=sources[rooted.SOURCE_ROLES['assembly/data/battle_script_commands_table.s']].decode().split('gBattleScriptingCommandsTable:',1)[1].split('gBattleScriptingCommandsTable2:',1)[0]
 # これは公開sourceの登録根。実ROMのJP値や命令をこの定数から仮定しない。
 need(re.findall(r'^\s*\.word\s+(\S+)',table,re.M)[0xE3]=='0x802C515','公開E3登録の独立slot ordinal')
 bprj=sources[rooted.SOURCE_ROLES['BPRJ.ld']].decode()
 for name,value in [('gBattleMons',MONS),('gActiveBattler',ACTIVE),('gBankTarget',TARGET),('gBattlescriptCurrInstr',CURSOR)]:
  m=re.search(r'^'+name+r'\s*=\s*(0x[0-9A-Fa-f]+);',bprj,re.M)
  need(m is not None and int(m[1],0)==value,'固定JP symbol '+name)
 general=sources[rooted.SOURCE_ROLES['src/general_bs_commands.c']].decode()
 need('EmitSetMonData(0, REQUEST_HP_BATTLE, 0, 2, &gBattleMons[gActiveBattler].hp);' in general,'独立HP fieldの2byte payload契約')
 script=sources[rooted.SOURCE_ROLES['assembly/battle_scripts/general_attack_battle_scripts.s']].decode()
 for label in ('LifeDewRestorePartnerHPBS','JungleHealingRestorePartnerHPBS'):
  rows=[x.strip()for x in re.sub(r'@[^\n]*','',script.split(label+':',1)[1]).splitlines()if x.strip()]
  need(rows[:2]==['callasm SetTargetPartner','jumpiffainted BANK_TARGET BS_MOVE_END'],'独立label直後E3命令')
 return True

def e3_bind(raw):
 need(E3_SLOT==rooted.prior.PRIMARY+0xE3*4,'実primary table indexからslotを導出')
 for a,value in E3_WORDS.items():need(d.u32(raw,a)==value,'実E3 slot/真のliteral/実bank slot')
 for i in E3_INS.values():need(chunk(raw,i.address,i.size)==rooted.encoded(i),'E3有限命令意味 '+i.kind)
 for a in COMMANDS:
  b=chunk(raw,a,6)
  need(b[0]==0xE3 and b[1]==0 and int.from_bytes(b[2:6],'little')==BRANCH_POINTER,'独立全6byte E3 commandの束縛')
 return True

def e3_proof(raw):
 """明示handler入口条件でtaken/nextを証明。prefix/callasm成功や自然到達は仮定しない。"""
 e3_bind(raw);proof=[]
 hp_cases=(0,1,255,256,32767,32768,65535)
 # CMP r0,0→BNEを全16bit入力について評価。実メモリ効果は下記の両edgeを全bankで実行。
 probe=E3Machine(raw,0x0802C530,instructions=E3_INS)
 for hp in range(65536):
  probe.pc=0x0802C530;probe.cmp(hp,0);probe.pc=0x0802C532
  need(probe.condition(1)==(hp!=0),'全halfword領域でzero/taken・nonzero/next')
 for a in COMMANDS:
  for bank in range(4):
   for hp in hp_cases:
    mem={};rt.setmem(mem,CURSOR,4,a);rt.setmem(mem,TARGET,1,bank)
    rt.setmem(mem,ATTACKER,1,bank^3);rt.setmem(mem,ACTIVE,1,0xEE)
    for other in range(4):
     rt.setmem(mem,MONS+MON_STRIDE*other+HP_OFFSET,HP_SIZE,hp if other==bank else(1 if hp==0 else 0))
    saved={r:0xDEAD0000+r for r in range(4,12)}
    m=E3Machine(raw,E3_ENTRY,registers=saved,memory=mem,instructions=E3_INS).run()
    edge='taken'if hp==0 else'next';target=BRANCH_POINTER if hp==0 else a+6
    need(rt.getmem(m.mem,CURSOR,4)==target and rt.getmem(m.mem,ACTIVE,1)==bank,'E3全効果: active battlerとcursor')
    external=[(p,b,n,v)for p,b,n,v in m.write_values if not 0x03006F00<=b<b+n<=0x03007000]
    expected=[(0x0802C522,ACTIVE,1,bank),(0x0802C54A if hp==0 else 0x0802C560,CURSOR,4,target)]
    need(external==expected,'全非stack writeはactive1byteとcursor4byteだけ')
    need(all(m.reg[r]==v for r,v in saved.items()),'callee-save registerと正常stackを保持')
    need(m.pc==0xFFFFFFF0 and m.reg[0]==0xFFFFFFF1 and m.reg[13]==0x03007000,'元LR保存値へのpop/bx returnとSP復元')
    reads={(b,n)for _,b,n in m.reads}
    need((0x09161410,4)in reads and(TARGET,1)in reads and(ATTACKER,1)not in reads,'実target bank slotと別RAM入力を区別')
    need((MONS+MON_STRIDE*bank+HP_OFFSET,HP_SIZE)in reads,'実半word HP fieldだけを選択')
    need(all((MONS+MON_STRIDE*other+HP_OFFSET,HP_SIZE)not in reads for other in range(4)if other!=bank),'他bank HPは読まない')
    pointers=[(p,b,n)for p,b,n in m.reads if a+2<=b<a+6]
    need(pointers==([(0x0802C536,a+2,1),(0x0802C538,a+3,1),(0x0802C53E,a+4,1),(0x0802C544,a+5,1)]if hp==0 else[]),'takenだけが全4byte pointerを読取り、nextは読まない')
    need(m.calls==[(0x0802C51C,0x08016634)],'未知callee成功契約を導入しない')
    need(all(p in m.trace for p in(0x08016634,0x08016636,0x090D3D2C,0x090D3D7E,0x090D3D3C)),'trampoline/実resolver/table target/returnを全て実行')
    need((0x0802C532 in m.trace)and(0x0802C55C in m.trace)==(hp!=0),'HP比較の実branch')
    proof.append(dict(command=a,edge=edge,entry=E3_ENTRY,bank=bank,hp=hp,next_cursor=target,steps=m.steps,
      full_pointer_read=hp==0,hp_address=MONS+MON_STRIDE*bank+HP_OFFSET,writes=[dict(address=b,size=n,value=v)for _,b,n,v in external]))
 return dict(status='PASS_CONDITIONAL_E3_BANK_TARGET_TAKEN_NEXT',primary_slot=E3_SLOT,entry=E3_ENTRY,
  legacy_resolver_entry=0x08016634,redirect_literal=0x08016638,actual_resolver_entry=0x090D3D2C,
  resolver_table_slot=0x09161410,bank_read=TARGET,hp_base=MONS,hp_stride=MON_STRIDE,hp_offset=HP_OFFSET,hp_width=HP_SIZE,
  hp_domain_count=65536,machine_cases=len(proof),models=proof,
  entry_preconditions=['CURSORはsource束縛済みのE3全6byte命令2件の一方を指す',
   'BANK_TARGET operandは0、実target RAM値は0..3',
   '選択bankのbattle-mon HP halfwordは0..65535',
   '有効で非aliasの専用stackと安定入力を仮定し、同時書換えなし'],
  public_us_address_alone_used_as_jp_evidence=False,natural_reachability_claimed=False,
  prefix_execution_claimed=False,callasm_success_claimed=False,move_effect_success_claimed=False,
  current_rom_identity_checked_by_local_model=False)


def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'新3hitだけ')
 effect=65 if hit==0x09003C02 else 32;left=hit-(3 if effect==65 else 4);right=hit+2
 pointer=0x09008E11 if effect==65 else 0x090073D1 if hit==0x0900360B else 0x09003734
 return dict(hit=hit,kind=KIND,effect=effect,root=ROOTS[effect],
  left_command=dict(address=left,size=5 if effect==65 else 6,opcode=40 if effect==65 else 0xE3),
  right_command=dict(address=right,size=10,opcode=0xFF09),
  byte_roles=['left_script_pointer_byte2','left_script_pointer_byte3','right_primary_opcode','right_secondary_opcode'],
  whole_pointers=[dict(address=hit-2,size=4,value=0x081BA90A),dict(address=right+6,size=4,value=pointer)],
  consumer_entry_condition='each_typed_command_entry_only',claims=copy.deepcopy(CLAIMS))

def witness_geometry(e):
 need(isinstance(e,dict)and type(e.get('hit'))is int and e['hit']in HITS,'最小の既知hit')
 need(exact(e,evidence_template(e['hit'])),'完全field/根/role/非昇格の型witness')
 for p in e['whole_pointers']:
  need(not d.DONOR_LO<=d.canonical(p['value'])<d.DONOR_HI,'実pointer全体はdonor外')
 return e['hit'],4

def own_geometry():
 rows={(i.address,i.size)for i in INS.values()}|{(a,4)for a in WORDS}|{(0x0913194E,2)}
 rows|={(a,GRAMMAR[n][1])for a,n,_ in PROGRAM}
 rows|={(0x090421F4+12*move,1)for move in MOVE_EFFECTS}
 return sorted(rows)

def protected_windows(review):
 return prior.protected_windows({'common_root':review['common_root'],'windows':review['windows']})

def make_review(raw,inherited,common_root):
 by={h['address']:h for h in inherited['hits']}
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
  source_bindings=copy.deepcopy(SOURCE_IDS),common_root=copy.deepcopy(common_root),
  hits=[copy.deepcopy(by[h])for h in HITS],
  windows=[dict(address=a,**identity(chunk(raw,a,n)))for a,n in own_geometry()],claims=copy.deepcopy(CLAIMS))

def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','common_root','hits','windows','claims'},'新reviewの閉schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'schemaは厳密整数')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'正式候補と旧診断入力は別identity')
 need(exact(review['claims'],CLAIMS),'型を自然到達/効果成功/退役/owner移管へ昇格しない')
 common=review['common_root']
 need(hashlib.sha256(json.dumps(common,sort_keys=True,separators=(',',':')).encode()).hexdigest()==COMMON_ROOT_SHA256,'受入済み共通rootの独立digest')
 source_proof(review,sources);prior.root_consumers(raw,common)
 need([(w['address'],w['size'])for w in review['windows']]==own_geometry(),'有限保護窓の閉集合')
 for w in review['windows']:
  need(set(w)=={'address','size','sha256'},'窓はaddress/size/digestのみ');d.signed(raw,w)
 bind_program(raw);controls=control_proof(raw);dispatch=dispatch_proof(raw);pointers=pointer_read_proof(raw)
 e3=e3_proof(raw)
 old=inherited['hits'];need(len({h['address']for h in old})==len(old),'親hitは重複禁止')
 by={h['address']:h for h in old};need(exact(review['hits'],[by[h]for h in HITS]),'親未知行の全field保持')
 regions=[]
 for h in review['hits']:
  need(type(h['accepted'])is bool and h['accepted']is False and h['owner_candidates']==[] and h['classification']=='UNCLASSIFIED'and type(h['size'])is int and h['size']==4,'無所有未知4byteだけ');d.signed(raw,h)
  evidence=evidence_template(h['address']);a,n=witness_geometry(evidence);regions.append(d.TypedRegion(a,a+n,KIND,evidence))
 return regions,dict(status='PASS_THREE_REGISTERED_HEALING_VEIL_TYPES',count=3,hits=list(HITS),typed_bytes=12,
  serializer_window_sizes=[41,63,53,88],source_serialized_root=True,
  native_selector_models=controls,native_dispatch_models=dispatch,native_pointer_read_proofs=pointers,
  native_jumpiffainted_models=e3,
  protected_windows=len(protected_windows(review)),protected_bytes=sum(w['size']for w in protected_windows(review)),**CLAIMS)

def regions(raw,inherited,review,sources):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'正式受入前にcurrent0641全体identityを要求')
 return _regions(raw,inherited,review,sources)
