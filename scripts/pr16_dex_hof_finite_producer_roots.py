"""effect233/234の有限登録rootからopcode列とgoto/FF09境界だけを型にする。"""
from __future__ import annotations
import copy, hashlib, json, re
import pr16_dex_hof_battle_tail_roots as tail
import pr16_dex_hof_battle_script_roots as rooted
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as native
import pr16_dex_hof_runtime_party as rt
prior = rooted.prior
need, identity, chunk = d.need, d.identity, d.chunk
exact, encoded = rooted.exact, rooted.encoded
CANDIDATE, DIAGNOSTIC = rooted.CANDIDATE, rooted.DIAGNOSTIC
KIND = 'finite_registered_battle_opcode_and_tail'
TYPE_CATEGORY = 'data'
HITS = (0x0900739D, 0x09007432)
ROOTS = {233: 0x09007385, 234: 0x090073F9}
CURSOR = prior.CURSOR
SOURCE_IDS = copy.deepcopy(rooted.SOURCE_IDS)
SOURCE_ROLES = copy.deepcopy(rooted.SOURCE_ROLES)
COMMON_ROOT_SHA256 = rooted.COMMON_ROOT_SHA256
CLAIMS = dict(tail.CLAIMS, opcode_handler_success_proven=False,
              whole_dispatcher_classified=False, current_rom_identity_checked_by_local_diagnostic=False)
GRAMMAR = dict(tail.GRAMMAR, attackstringnoprotean=(0xFF26,2,()))
HEAL_PULSE = (
 (0x09007385,'attackcanceler',()),
 (0x09007386,'jumpifmove',(0,0x02023CAA,0x2A0,0x090073EE)),
 (0x09007392,'jumpifbehindsubstitute',(0,0x1000000,0x09008E11)),
 (0x0900739C,'attackstringnoprotean',()),
 (0x0900739E,'ppreduce',()),
 (0x0900739F,'jumpifcounter',(0,2,1,0,0x090073D1)),
)
TOPSY_TURVY = (
 (0x090073F9,'attackcanceler',()),
 (0x090073FA,'accuracycheck',(0x081BA91A,0)),
 (0x09007401,'jumpifbehindsubstitute',(0,0x1000000,0x09008E11)),
 (0x0900740B,'attackstring',()),
 (0x0900740C,'ppreduce',()),
 (0x0900740D,'jumpifmove',(0,0x02023CAA,0x2DF,0x09007434)),
 (0x09007419,'callasm',(0x090CA915,)),
 (0x0900741E,'attackanimation',()),
 (0x0900741F,'waitanimation',()),
 (0x09007420,'setword',(0x0203DF98,0x09007C80)),
 (0x09007429,'printstring',(0x184,)),
 (0x0900742C,'waitmessage',(0x40,)),
 (0x0900742F,'goto',(0x081BA90A,)),
)
ELECTRIFY = ((0x09007434,'jumpifcounter',(0,6,1,0,0x09008E13)),)
PROGRAM = HEAL_PULSE + TOPSY_TURVY + ELECTRIFY
MOVE_EFFECTS = {0x2A0:233,0x2DF:234}
# 登録consumerの独立意味のみ再利用。旧hit/旧programを再分類しない。
CONTROL_INS = dict(tail.CONTROL_INS)
POINTER_INS = {i.address:i for name in ('counter_pointer_read','bank_resolver','bank_return','target_bank')
               for i in rooted.BLOCKS[name]}
DISPATCH_BLOCKS = {
 'primary':native.block(0x08015492,[
  ('literal',1,0x080154AC),('literal',0,0x080154B0),
  ('mem',True,'word',0,0,0),('mem',True,'byte',0,0,0),
  ('shift','lsl',0,0,2),('add',0,0,1),('mem',True,'word',0,0,0),
  ('call',0x081C7AC8)]),
 'primary_trampoline':native.block(0x081C7AC8,[('bx',0)]),
 'secondary':native.block(0x0911AA8C,[
  ('literal',3,0x0911AAA4),('push',16,True),
  ('mem',True,'word',2,3,0),('addi',1,2,1),('mem',False,'word',1,3,0),
  ('mem',True,'byte',2,2,1),('literal',3,0x0911AAA8),
  ('shift','lsl',2,2,2),('loadreg',3,2,3),('call',0x0911DC4C)]),
 'secondary_trampoline':native.block(0x0911DC4C,[('bx',3)]),
}
DISPATCH_INS = {i.address:i for block in DISPATCH_BLOCKS.values()for i in block}
INS = {**CONTROL_INS,**POINTER_INS,**DISPATCH_INS}
WORDS = {
 0x08021E6C:CURSOR,0x08021F5C:CURSOR,0x08021F60:0x08021F64,
 0x08021F64:0x08021F7C,0x08021F68:0x08021F84,
 0x0911B0E0:CURSOR,0x090D3D8C:0x09161410,
 0x09161410:0x090D3D7E,0x090D3DA4:0x02023CCC,
 prior.EFFECTS+233*4:ROOTS[233],prior.EFFECTS+234*4:ROOTS[234],
 prior.PRIMARY:0x090BD385,prior.PRIMARY+3*4:0x09104B55,
 prior.SECONDARY+0x26*4:0x0911C54D,
 prior.SECONDARY+9*4:0x0911AF69,prior.PRIMARY+255*4:0x0911AA8D,
 0x080154AC:prior.PRIMARY,0x080154B0:CURSOR,
 0x0911AAA4:CURSOR,0x0911AAA8:prior.SECONDARY,
}
Machine = tail.Machine

def source_proof(review,sources):
 # 公開8sourceの全体identity・serializer意味を共通APIで再利用する。
 tail.source_proof(review,sources)
 macro=re.sub(r'@[^\n]*','',sources[SOURCE_ROLES['battle_script_macros.s']].decode())
 bodies=re.findall(r'\.macro\s+attackstringnoprotean(?:[ \t][^\n]*)?\n(.*?)\.endm',macro,re.S)
 need(len(bodies)==1,'追加opcodeのserializerは一意')
 rows=[line.strip()for line in bodies[0].splitlines()if line.strip()]
 need(rows==['.byte 0xFF, 0x26'],'FF26はoperandを持たない完全2byte命令')
 defs=sources[SOURCE_ROLES['asm_defines.s']].decode()
 for name,value in [('ELECTRIFY_TIMERS',6),('HEAL_BLOCK_TIMERS',2)]:
  m=re.search(r'^\.equ\s+'+name+r',\s*(\w+)',defs,re.M)
  need(m is not None and int(m[1],0)==value,'独立sourceのcounter定数')
 src=sources[SOURCE_ROLES['assembly/battle_scripts/general_attack_battle_scripts.s']].decode()
 compact=lambda s:[' '.join(x.split())for x in re.sub(r'@[^\n]*','',s).splitlines()if x.strip()]
 need(compact(src.split('BS_233_HealTarget:',1)[1].split('HealPulseBS:',1)[0])==[
  'attackcanceler','jumpifmove MOVE_POLLENPUFF PollenPuffBS'],'effect233 rootの完全serializer順序')
 need(compact(src.split('HealPulseBS:',1)[1])[:4]==[
  'jumpifbehindsubstitute BANK_TARGET FAILED_PRE','attackstringnoprotean','ppreduce',
  'jumpifcounter BANK_TARGET HEAL_BLOCK_TIMERS NOTEQUALS 0x0 BattleScript_NoHealTargetAfterHealBlock'],
  'HealPulse冒頭の全6命令型境界')
 need(compact(src.split('BS_234_TopsyTurvyElectrify:',1)[1].split('ElectrifyBS:',1)[0])==[
  'attackcanceler','accuracycheck BS_MOVE_MISSED 0x0','jumpifbehindsubstitute BANK_TARGET FAILED_PRE',
  'attackstring','ppreduce','jumpifmove MOVE_ELECTRIFY ElectrifyBS','callasm TopsyTurvyFunc',
  'attackanimation','waitanimation','setword BATTLE_STRING_LOADER TopsyTurvyString',
  'printstring 0x184','waitmessage DELAY_1SECOND','goto BS_MOVE_END'],
  'effect234の13命令59byteを固定source順序で閉じる')
 need(compact(src.split('ElectrifyBS:',1)[1])[0]==
  'jumpifcounter BANK_TARGET ELECTRIFY_TIMERS NOTEQUALS 0x0 FAILED','右命令の独立labelと全引数')
 effects=sources[SOURCE_ROLES['assembly/data/move_effect_table.s']].decode().split('gBattleScriptsForMoveEffects:',1)[1].split('gSetStatusMoveEffects:',1)[0]
 words=lambda s:re.findall(r'^\s*\.word\s+(\S+)',s,re.M)
 need([words(effects)[e]for e in ROOTS]==['BS_233_HealTarget','BS_234_TopsyTurvyElectrify'],'公開の実effect登録')
 table=sources[SOURCE_ROLES['assembly/data/battle_script_commands_table.s']].decode().split('gBattleScriptingCommandsTable:',1)[1]
 primary,secondary=table.split('gBattleScriptingCommandsTable2:',1)
 need(words(primary)[3]=='atk03_ppreduce'and words(secondary)[0x26]=='atkFF26_attackstringnoprotean',
      '新opcodeの公開dispatch登録')
 return True

def bind_program(raw):
 rows=[]
 for a,name,values in PROGRAM:
  op,size,fields=GRAMMAR[name];b=chunk(raw,a,size)
  prefix=bytes([255,op&255]if op>255 else[op])
  need(b[:len(prefix)]==prefix,'source境界の実opcode')
  need(tuple(int.from_bytes(b[o:o+n],'little')for o,n,_ in fields)==values,'完全operandの独立意味')
  rows.append(dict(address=a,name=name,opcode=op,size=size,
   fields=[dict(address=a+o,size=n,role=role,value=v)for(o,n,role),v in zip(fields,values)]))
 for sequence in (HEAL_PULSE,TOPSY_TURVY+ELECTRIFY):
  for left,right in zip(sequence,sequence[1:]):
   need(left[0]+GRAMMAR[left[1]][1]==right[0],'隣接serializer境界。実行successorではない')
 need(sum(GRAMMAR[n][1]for _,n,_ in HEAL_PULSE)==36,'HealPulse prefix36byte')
 need(len(TOPSY_TURVY)==13 and sum(GRAMMAR[n][1]for _,n,_ in TOPSY_TURVY)==59,'TopsyTurvy全59byte')
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
   result.append(dict(command=a,opcode=op,edge=edge,entry=prior.HANDLERS[op],next_cursor=target))
 need(any(x['command']==0x09007386 and x['edge']=='next'and x['next_cursor']==0x09007392 for x in result),'HealPulseの非選択source境界')
 need(any(x['command']==0x0900740D and x['edge']=='taken'and x['next_cursor']==0x09007434 for x in result),'Electrifyの独立selector根')
 return result

def dispatch_proof(raw):
 """明示command-entry条件から実LDRB、実table slot、trampolineだけを実行する。"""
 semantic_bindings(raw);proof=[]
 for a,name,values in HEAL_PULSE[3:]:
  op,size,_=GRAMMAR[name];extended=op>255
  expected={0xFF26:0x0911C54C,3:0x09104B54,0xFF09:0x0911AF68}[op]
  mem={};rt.setmem(mem,CURSOR,4,a)
  m=Machine(raw,0x08015492,memory=mem,instructions=DISPATCH_INS)
  while m.pc!=expected:
   need(m.steps<32,'有限dispatchの停止');m.step()
  slots=[prior.PRIMARY+4*(255 if extended else op)]
  operands=[a]
  if extended:slots.append(prior.SECONDARY+4*(op&255));operands.append(a+1)
  need(all((cell,4)in m.reads for cell in slots),'実opcodeから実table slotを読む')
  need(all((cell,1)in m.reads for cell in operands),'実commandの全opcode byteをLDRBする')
  need(rt.getmem(m.mem,CURSOR,4)==a+int(extended),'secondaryだけがcursorを正確に1byte進める')
  writes=[w for w in m.writes if w[1]==CURSOR]
  need(writes==([(0x0911AA94,CURSOR,4)]if extended else[]),'cursor writeは実secondaryの1つだけ')
  need(all(addr==CURSOR and n==4 or 0x03006F00<=addr<addr+n<=0x03007000 for _,addr,n in m.writes),
       'dispatchのwriteはcursorと正規stackだけ')
  proof.append(dict(command=a,opcode=op,opcode_byte_reads=operands,handler=expected,
                    dispatch_slots=slots,cursor_at_handler=a+int(extended),steps=m.steps,
                    command_entry_condition=True,handler_executed=False))
 return proof

def pointer_read_proof(raw):
 semantic_bindings(raw);proof=[]
 for a,_,values in (HEAL_PULSE[-1],ELECTRIFY[0]):
  for bank in range(4):
   mem={};rt.setmem(mem,CURSOR,4,a+1);rt.setmem(mem,0x02023CCC,1,bank)
   m=Machine(raw,0x0911AF68,memory=mem,instructions=POINTER_INS)
   while m.pc!=0x0911AF94:m.step()
   need(m.reg[4]==values[-1]and m.reg[0]==bank,'完全pointerと実bank0読取り')
   need((0x09161410,4)in m.reads and(0x02023CCC,1)in m.reads,'bank0の実slotと実RAM')
   need((0x09161414,4)not in m.reads and(0x02023CCB,1)not in m.reads,'別bankの代入ではない')
   need(m.calls==[(0x0911AF74,0x090D3D2C)],'未証明calleeをstubにしない')
   need(rt.getmem(m.mem,CURSOR,4)==a+1,'pointer読取りでcursorを捏造しない')
   need(all(0x03006F00<=addr<addr+n<=0x03007000 for _,addr,n in m.writes),'正規stack以外は書かない')
  proof.append(dict(command=a,handler=0x0911AF68,stop=0x0911AF94,pointer=values[-1],
                    pointer_bytes=4,bank_operand=0,resolver_slot=0x09161410,
                    bank_read_address=0x02023CCC,distinct_bank_value_cases=4))
 return proof

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'新2hitだけ')
 common=dict(hit=hit,kind=KIND,claims=copy.deepcopy(CLAIMS))
 if hit==HITS[0]:
  return dict(common,effect=233,root=ROOTS[233],commands=[
   dict(address=0x0900739C,size=2,opcode=0xFF26),dict(address=0x0900739E,size=1,opcode=3),
   dict(address=0x0900739F,size=10,opcode=0xFF09)],
   byte_roles=['attackstringnoprotean_secondary_opcode','ppreduce_primary_opcode',
               'jumpifcounter_primary_opcode','jumpifcounter_secondary_opcode'],
   whole_pointers=[dict(address=0x090073A5,size=4,value=0x090073D1)],
   consumer='conditional_actual_primary_secondary_dispatch')
 return dict(common,effect=234,root=ROOTS[234],commands=[
  dict(address=0x0900742F,size=5,opcode=40),dict(address=0x09007434,size=10,opcode=0xFF09)],
  byte_roles=['left_script_pointer_byte2','left_script_pointer_byte3','right_primary_opcode','right_secondary_opcode'],
  whole_pointers=[dict(address=0x09007430,size=4,value=0x081BA90A),
                  dict(address=0x0900743A,size=4,value=0x09008E13)],
  consumer='complete_goto_pointer_and_conditional_counter_pointer_read')

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
 need(type(review['schema_version'])is int and review['schema_version']==1,'schemaは厳密な整数')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'正式候補と診断入力は別identity')
 need(exact(review['claims'],CLAIMS),'型を自然到達/退役/owner移管へ昇格しない')
 common=review['common_root']
 need(hashlib.sha256(json.dumps(common,sort_keys=True,separators=(',',':')).encode()).hexdigest()==COMMON_ROOT_SHA256,'既受入共通登録根の独立digest')
 source_proof(review,sources);prior.root_consumers(raw,common)
 need([(w['address'],w['size'])for w in review['windows']]==own_geometry(),'最小有限窓の閉集合')
 for w in review['windows']:
  need(set(w)=={'address','size','sha256'},'窓はdigestのみ');d.signed(raw,w)
 bind_program(raw);controls=control_proof(raw);dispatch=dispatch_proof(raw);pointers=pointer_read_proof(raw)
 old=inherited['hits'];need(len({h['address']for h in old})==len(old),'親hitは重複禁止')
 by={h['address']:h for h in old};need(exact(review['hits'],[by[h]for h in HITS]),'親の未知行全fieldを保持')
 regions=[]
 for h in review['hits']:
  need(type(h['accepted'])is bool and h['accepted']is False and h['owner_candidates']==[] and h['classification']=='UNCLASSIFIED'and type(h['size'])is int and h['size']==4,'無所有の未知4byteだけ');d.signed(raw,h)
  evidence=evidence_template(h['address']);a,n=witness_geometry(evidence);regions.append(d.TypedRegion(a,a+n,KIND,evidence))
 return regions,dict(status='PASS_TWO_FINITE_REGISTERED_BATTLE_TYPES',count=2,hits=list(HITS),typed_bytes=8,
  heal_pulse_prefix_bytes=36,topsy_turvy_prefix_bytes=59,source_serialized_root=True,
  native_selector_models=controls,native_dispatch_models=dispatch,native_pointer_read_proofs=pointers,
  protected_windows=len(protected_windows(review)),protected_bytes=sum(w['size']for w in protected_windows(review)),**CLAIMS)

def regions(raw,inherited,review,sources):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'正式受入前にcurrent0641全体identityを要求')
 return _regions(raw,inherited,review,sources)
