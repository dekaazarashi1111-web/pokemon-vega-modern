"""Toxic Orbの実JP hookから最小Thumb型まで。条件付き有限証明だけ。"""
import ast, copy, csv, hashlib, io, json, re
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_animation_registered_roots as flags_engine
from pr16_dex_hof_extra_roots import exact, encoded
need, identity, chunk = d.need, d.identity, d.chunk
CANDIDATE, DIAGNOSTIC = party.CANDIDATE, party.DIAGNOSTIC
KIND='registered_toxic_orb_minimum_thumb'
KINDS=(KIND,)
TYPE_CATEGORY='code'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x090FA7BD,)
HELD_HITS=()
EXPECTED_HITS=[dict(address=0x090FA7BD,target=167701232,
 kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',size=4,
 sha256='8c1338e0813061a31944bb9d49ee72f8986c0d6d5e827d5d601d5820db881115',
 classification='UNCLASSIFIED',accepted=False,
 reason='no_complete_typed_asset_consumer_witness',owner_candidates=[])]
HOOK,ENTRY,HIT_CALL,STOP=0x08017A68,0x090F7F10,0x090FA7BC,0x08016A58
FLAGS,HITMARKER,BATTLESTRUCT=0x02022AAC,0x02023D30,0x02023F48
ORDER,ACTIVE,ATTACKER,TARGET=0x02023B3E,0x02023B24,0x02023CCB,0x02023CCC
DAMAGE,MONS,NEWBS,COUNT=0x02023CB0,0x02023B44,0x0203DFB0,0x02023B2C
LAST_ITEM,EFFECTBANK=0x02023CC8,0x02023CCE
# 有効API入力の一例。実save/RAM観測とは主張しない。
BATTLE_CONTEXT,NEW_CONTEXT=0x02011000,0x02012000
ROOT=dict(kind='public_jp_hook_registered_api_entry',hook=HOOK,
 hook_literal=0x08017A6C,registered_handler=ENTRY|1,entry=ENTRY,
 state_table=0x09166470,state=69,state_cell=0x09166584,state_target=0x090F80D8,
 substate=2,substate_call=0x090F80EC,toxic_gate=0x090F945E,
 toxic_call=0x090F949E,toxic_block=0x090FA774,
 hit_call=HIT_CALL,interwork=0x090FB594,leaf=STOP,
 static_successor=0x090FA7C0)
SPECS=[]
def block(address,specs):
 for kind,*args in specs:
  SPECS.append((address,kind,tuple(args)));address+=4 if kind=='call' else 2
 return address
# 公開hooksのTurnBasedEffects。r0登録値を実LDR/BXで読む。
block(HOOK,[('literal',0,0x08017A6C),('bx',0)])
# 関数入口の全prologueとSafari/turnEffectsTracker gate、全bank writer。
block(ENTRY,[
 ('push',240,True),('movhi',14,11),('movhi',7,10),('movhi',6,9),('movhi',5,8),
 ('push',224,True),('literal',3,0x090F8284),('mem',True,'word',3,3,0),
 ('spadd',-36),('shift','lsl',3,3,24),('branch',5,0x090F7F2A),('call',0x090F8F14),
 ('literal',7,0x090F8288),('literal',3,0x090F828C),('mem',True,'word',2,7,0),
 ('alu','orr',3,2),('mem',False,'word',3,7,0),('literal',3,0x090F8290),
 ('movhi',10,7),('movhi',11,3),('mem',True,'word',4,3,0),
 ('mem',True,'byte',3,4,0),('imm','cmp',3,74),('branch',9,0x090F7F46),
 ('call',0x090F8F0A),('mem',True,'byte',3,4,1),('literal',5,0x090F8294),
 ('literal',2,0x090F8298),('regmem','ldrb',0,5,3),('movhi',8,2),
 ('mem',False,'byte',0,2,0),('literal',2,0x090F829C),('mem',False,'byte',0,2,0),
 ('spmem',False,2,20),('imm','mov',2,0),('literal',6,0x090F82A0),
 ('literal',1,0x090F82A4),('mem',False,'byte',0,6,0),('mem',False,'word',2,1,0),
 ('mem',True,'byte',2,4,0),('spmem',False,3,12),('spmem',False,1,16),
 ('imm','cmp',2,74),('branch',9,0x090F7F70),('call',0x090F8F32),
 ('literal',7,0x090F82A8),('shift','lsl',1,2,2),('regmem','ldr',1,7,1),('movhi',15,1)])
# state69の実table dispatchからgNewBS +327のsubstate2へ。
block(0x090F80D8,[('imm','mov',1,72),('literal',2,0x090F82AC),('movhi',9,2),
 ('mem',True,'word',2,2,0),('imm','add',1,255),('shift','lsl',7,1,0),
 ('regmem','ldrb',1,2,1),('movhi',12,1),('imm','cmp',1,2),
 ('branch',1,0x090F80F0),('call',0x090F945E)])
# HPと三種のitem-effect selector。opaque戻り75を十分条件とする。
block(0x090F945E,[('imm','mov',1,88),('movhi',8,1),('literal',5,0x090F973C),
 ('movhi',1,8),('alu','mul',1,0),('movhi',8,5),('addhi',1,8),
 ('mem',True,'half',1,1,40),('spmem',False,5,12),('imm','cmp',1,0),
 ('branch',0,0x090F93D0),('call',0x090D3FEC),('imm','cmp',0,76),
 ('branch',1,0x090F9480),('call',0x090FA518),('imm','cmp',0,117),
 ('branch',1,0x090F9488),('call',0x090FA4BE),('imm','cmp',0,75),
 ('branch',0,0x090F9490),('call',0x090FA2FA),('mem',True,'byte',0,6,0),
 ('imm','mov',2,0),('shift','lsl',1,0,0),('call',0x090D7360),
 ('subi',5,0,0),('branch',0,0x090F94A2),('call',0x090FA774)])
# held itemとstatus writer→実5引数Emit→実Mark leaf入口まで。
block(0x090FA774,[('imm','mov',2,88),('movhi',12,2),('spmem',True,4,12),
 ('mem',True,'byte',0,6,0),('movhi',2,12),('alu','mul',2,0),('movhi',12,4),
 ('addhi',2,12),('literal',3,0x090FA7E8),('mem',True,'half',2,2,46),
 ('imm','mov',1,75),('mem',False,'half',2,3,0),('call',0x090D4114),
 ('imm','mov',2,88),('mem',True,'byte',3,6,0),('alu','mul',2,3),
 ('shift','lsl',3,2,0),('movhi',12,4),('imm','mov',0,128),('add',1,4,2),
 ('mem',True,'word',2,1,76),('imm','add',3,76),('addhi',3,12),
 ('alu','orr',2,0),('mem',False,'word',2,1,76),('imm','mov',0,0),
 ('imm','mov',2,0),('imm','mov',1,40),('spmem',False,3,0),
 ('literal',4,0x090FA7F0),('imm','mov',3,4),('call',0x090FB596),
 ('mem',True,'byte',0,6,0),('literal',3,0x090FA7F4),('call',0x090FB594),
 ('literal',3,0x090FA7F8)])
block(0x090FB594,[('bx',3),('bx',4)])
INS={a:party.Ins(a,k,args)for a,k,args in SPECS}
need(len(INS)==len(SPECS),'独立Thumb命令非重複')
# opaque APIのsource対応を補強する独立手書きprefix。合成には実行しない。
ABI_SPECS=[]
def signature(address,specs):
 for kind,*args in specs:
  ABI_SPECS.append((address,kind,tuple(args)));address+=4 if kind=='call' else 2
signature(0x090D3FEC,[('imm','mov',3,88),('alu','mul',3,0),('literal',1,0x090D4038),
 ('add',3,1,3),('mem',True,'half',3,3,56),('shift','lsl',2,0,0),('push',16,True),
 ('imm','cmp',3,104),('branch',0,0x090D400C),('literal',3,0x090D403C),
 ('mem',True,'word',4,3,0),('add',3,4,0),('imm','add',3,52),
 ('mem',True,'byte',0,3,0),('imm','cmp',0,0),('branch',0,0x090D4010)])
signature(0x090D4114,[('literal',2,0x090D4124),('movhi',12,2),('literal',3,0x090D4128),
 ('mem',True,'word',3,3,0),('add',3,3,0),('addhi',3,12),('mem',False,'byte',1,3,0),('bx',14)])
signature(0x090D7360,[('push',248,True),('shift','lsl',3,2,0),('literal',2,0x090D73FC),
 ('mem',True,'byte',2,2,0),('shift','lsl',4,0,0),('compare',2,1),('branch',3,0x090D7392),
 ('imm','mov',2,88),('alu','mul',2,1),('literal',5,0x090D7400),('add',2,5,2),
 ('mem',True,'half',6,2,56),('imm','mov',1,88),('alu','mul',1,4),('add',1,5,1),
 ('mem',True,'half',7,1,56),('shift','lsl',2,6,0),('shift','lsl',1,7,0),
 ('shift','lsl',0,4,0),('call',0x090D6F18)])
# source normal branchを完全合成し、opaqueの都合よいitem戻り値にしない。
signature(0x090D400C,[('imm','mov',0,0),('pop',16,True),
 ('mem',True,'byte',3,4,4),('imm','cmp',3,0),('branch',1,0x090D400E),
 ('literal',3,0x090D4040),('mem',True,'word',3,3,0),('shift','lsl',3,3,5),
 ('branch',4,0x090D402C),('imm','mov',3,88),('alu','mul',3,2),
 ('add',1,1,3),('mem',True,'half',0,1,46),('call',0x0910FDD0),('jump',0x090D400E)])
signature(0x0910FDD0,[('literal',3,0x0910FDE8),('compare',0,3),
 ('branch',8,0x0910FDE4),('shift','lsl',3,0,2),('literal',2,0x0910FDEC),
 ('add',3,3,0),('shift','lsl',3,3,3),('add',3,3,2),
 ('mem',True,'byte',0,3,14),('bx',14),('literal',3,0x0910FDEC),('jump',0x0910FDE0)])
ABI_INS={a:party.Ins(a,k,args)for a,k,args in ABI_SPECS if 0x090D7360<=a<0x090D738A}
INS.update({a:party.Ins(a,k,args)for a,k,args in ABI_SPECS if a not in ABI_INS})
ITEM_ID,ITEM_TABLE,ITEM_EFFECT_FIELD=894,0x094537E0,0x0945C39E
WORDS={0x08017A6C:ENTRY|1,0x090F8284:FLAGS,0x090F8288:HITMARKER,
 0x090F828C:0x01000020,0x090F8290:BATTLESTRUCT,0x090F8294:ORDER,
 0x090F8298:TARGET,0x090F829C:ATTACKER,0x090F82A0:ACTIVE,0x090F82A4:DAMAGE,
 0x090F82A8:0x09166470,0x090F82AC:NEWBS,0x09166584:0x090F80D8,
 0x090F973C:MONS,0x090FA7E8:LAST_ITEM,0x090FA7F0:0x0800D9E5,
 0x090FA7F4:STOP|1,0x090FA7F8:EFFECTBANK,
 0x090D4038:MONS,0x090D403C:NEWBS,0x090D4124:665,0x090D4128:NEWBS,
 0x090D73FC:COUNT,0x090D7400:MONS,0x090D4040:FLAGS,0x0910FDE8:1043,0x0910FDEC:ITEM_TABLE}
EXTERNAL={0x090F9496:(0x090D7360,'CanBePoisoned',1),
 0x090FA7B4:(0x0800D9E4,'EmitSetMonData',None)}
PROFILE=dict(battle_flags=1,hitmarker=0,battle_context=BATTLE_CONTEXT,new_context=NEW_CONTEXT,
 turn_effects_tracker=69,turn_effects_bank=1,turn_order_bank=2,battlers_count=4,
 end_turn_substate=2,active_hp=1,held_item=ITEM_ID,initial_status1=0,active_ability=0,embargo_timer=0,magic_room_timer=0,
 item_effect_return=75,can_be_poisoned_return=1,normal_abi_returns=True,
 same_battle_context_epoch=True,same_newbs_epoch=True,same_stack_epoch=True)
CLAIMS=dict(proof_scope='conditional_registered_toxic_orb_minimum_thumb',
 conditional_registered_api_entry=True,actual_jp_hook_executed=True,
 complete_selected_entry_path=True,actual_runtime_execution_observed=False,
 whole_candidate_identity_checked_by_parent_required=True,
 full_story_reachability_claimed=False,all_end_turn_state_producers_proven=False,
 opaque_callee_effects_proven=False,held_item_effect_producer_proven=True,record_item_effect_writer_proven=True,
 hit_callee_entered=True,hit_callee_effects_proven=False,hit_callee_return_required=False,
 static_successor_executed=False,universal_heap_or_irq_lifetime_proven=False,
 whole_function_range_classified=False,padding_classified=False,
 indirect_reference_completeness_claimed=False,retirement_proven=False,
 donor_eligible=False,donor_leased=False)
CONTRACT=dict(
 entry_ja='公開TurnBasedEffectsのJP hook08017A68から実LDR/BXで開始する条件付きAPI入力。double battle flags1/Safari off、battle struct tracker69、turnEffectsBank1、turn order[1]=2、4bank中のbank2を実writerでactive/attacker/targetへ設定。全state producerや自然battle到達を主張しない。',
 structs_ja='固定CFRUの完全BattlePokemonとNewBattleStructを独立ARM32 scalar/array/bitfield/pointer layoutへ解決。stride88/hp40/item46/ability56/status76、tracker0/bank1、endTurn327、ai.itemEffects665を観測byteから採らない。',
 values_ja='同epochの有効battle/newBS object、substate2、HP1、公開current manifestのToxic Orb id894/status0/ability0/Embargo0/MagicRoom0を有効API例とする。実GetBankItemEffect→ItemId_GetHoldEffect→current table894の効果75とRecordItemEffectBattle writerを有限合成する。CanBePoisoned戻り1は同epochで相方Pastel Veil等の保護がない条件でのopaque十分条件。全毒可否helper効果は未証明。',
 abi_ja='2個のopaque callはsource宣言/呼出roleと実callee prefix又はJP linker symbolを束縛。通常ABIでcallee-saved/SP/LRを保存して復帰し、void戻りはUnknown、CanBePoisonedのscalar戻りだけ1。各callee本体の全副作用成功を受入にしない。',
 lifetime_ja='各opaque境界で残る実future read-before-write fieldだけを維持し、他のRAMをUnknownへ消去して同一pathをreplay。同battle context/同newBS allocation/同stack epochを明示条件とする。構造体の全域保持や普遍heap/IRQ寿命は要求も証明もしない。',
 item_extent_ja='独立manifestは999行、実sanitizer literalは1043だが選択row894は双方の有効範囲内。今回はrow894/holdEffect75だけを証明し、999から1044への拡張生成lineageや全item/sanitizer境界のsource一致を主張しない。',
 endpoint_ja='実status1|0x80 writer→EmitSetMonData(0,40,0,4,&status1)→実BL/BX→MarkBufferBankForExecution(bank2)入口で停止。Mark本体の成功/復帰、後続gEffectBank writer/BattleScriptExecuteを未主張。',
 minimum_ja='090FA7BDの4byte hitを覆うBL090FA7BCの4byteと静的successor LDR090FA7C0の2byteだけ。successorはencode/型のみで未実行。関数全域/literal/padding/隣接hitを分類しない。')

class Machine(flags_engine.Machine):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.role_reads=[];self.role_writes=[]
 def read(self,a,n):
  value=super().read(a,n)
  if self.pc in(0x090F7F4C,0x090F7F74,0x090F80E4,0x090F946C,0x090FA786,0x090FA79C,0x090D3FF4,0x090D4006,0x090D4010,0x090D4024,0x0910FDE0):
   self.role_reads.append((self.pc,a,n,value))
  return value
 def write(self,a,n,value):
  super().write(a,n,value)
  if a in(ACTIVE,ATTACKER,TARGET,DAMAGE,HITMARKER,LAST_ITEM,MONS+2*88+76,NEW_CONTEXT+665+2):
   self.role_writes.append((self.pc,a,n,value))

def preservation_contract(live,writes=(),events=None):
 need(type(live)is list and all(type(x)is list and len(x)==2 and all(type(y)is int for y in x)and x[1]>0 for x in live),'有限future-live射影')
 events={}if events is None else events
 need(type(events)is dict and set(events)<={'battle_context_epoch_changed','newbs_epoch_changed','stack_epoch_changed'}and all(type(v)is bool for v in events.values()),'閉じたepoch条件')
 need(not any(events.values()),'同battle/newBS/stack epoch維持')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(v)is int and 0<=v<1<<(8*n)and 0<=a<a+n<=1<<32,'有限opaque書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live byte破壊禁止')
 return True

def _compose(raw,projections=None,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(profile is None or exact(profile,PROFILE),'閉じた有限入力profile')
 need(contract is None or exact(contract,CONTRACT),'閉じたAPI契約')
 mem={};trace=[];visited=[];boundaries=[];groups=[];calls=[]
 for a,n,v in((FLAGS,4,1),(COUNT,1,4),(HITMARKER,4,0),(BATTLESTRUCT,4,BATTLE_CONTEXT),
  (BATTLE_CONTEXT,1,69),(BATTLE_CONTEXT+1,1,1),(ORDER+1,1,2),(NEWBS,4,NEW_CONTEXT),
  (NEW_CONTEXT+327,1,2),(NEW_CONTEXT+4,1,0),(NEW_CONTEXT+52+2,1,0),
  (MONS+176+40,2,1),(MONS+176+46,2,ITEM_ID),(MONS+176+56,2,0),(MONS+176+76,4,0)):
  rt.setmem(mem,a,n,v)
 m=Machine(raw,HOOK,{},mem,instructions=INS,trace=trace)
 while m.pc!=STOP:
  need(m.steps<250,'有限Toxic Orb合成')
  if m.pc in INS:
   if m.pc==0x090F9478:need(m.reg[0]==75,'実item readerから75復帰')
   if m.pc==0x090FA78C:need(m.reg[:2]==[2,75],'実RecordItemEffectBattle引数')
   visited.append(m.pc);m.step();continue
  site=(m.reg[14]&~1)-4
  need(site in EXTERNAL and m.pc==EXTERNAL[site][0],'閉じた実opaque境界 '+hex(site)+' '+hex(m.pc))
  target,name,value=EXTERNAL[site]
  args=(tuple(m.reg[:4]),None)
  if name=='GetBankItemEffect':need(m.reg[0]==2,'実bank ITEM_EFFECT引数')
  elif name=='CanBePoisoned':need(m.reg[:3]==[2,2,0],'実bank二つとFALSE引数')
  elif name=='RecordItemEffectBattle':need(m.reg[:2]==[2,75],'実item effect記録引数')
  elif name=='EmitSetMonData':
   pointer=m.read(m.reg[13],4);status=m.read(pointer,4)
   need(m.reg[:4]==[0,40,0,4]and pointer==MONS+176+76 and status==128,'実status writerと実5引数')
   args=(tuple(m.reg[:4]),pointer)
  calls.append(dict(site=site,target=target,source_role=name,
   arguments=[m.reg[j]for j in range({'GetBankItemEffect':1,'CanBePoisoned':3,'RecordItemEffectBattle':2,'EmitSetMonData':4}[name])],
   stack_data_pointer=args[1]))
  index=len(boundaries);boundaries.append((site,target));trace.append(('boundary',index,0))
  if projections is not None:
   need(index<len(projections),'全opaque境界の射影')
   live=projections[index];writes=(opaque_writes or {}).get(site,());events=(epoch_events or {}).get(site,{})
   preservation_contract(live,writes,events)
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   groups.append(dict(site=site,target=target,source_role=name,return_value=value,
    required_fields=[dict(address=a,size=n)for a,n in live],normal_abi_return_required=True,
    same_battle_context_epoch_required=True,same_newbs_epoch_required=True,
    same_stack_epoch_required=True,effects_discharged=False))
  for r in(0,1,2,3,12):m.reg[r]=rt.U
  if value is not None:m.reg[0]=value
  m.flags=(rt.U,)*4;m.flag_pc=None;m.pc=m.reg[14]&~1
 need(m.reg[0]==2 and m.reg[3]==STOP|1,'実MarkBufferBankForExecution(bank2)入口')
 need(visited[-2:]==[HIT_CALL,0x090FB594]and 0x090FA7C0 not in visited,'hit BL/BXのみ実行、successor未実行')
 need(len(boundaries)==2,'2opaque境界')
 need((0x0910FDE0,ITEM_EFFECT_FIELD,1,75)in m.role_reads,'current canonical item effect実消費')
 need((0x090D4120,NEW_CONTEXT+667,1,75)in m.role_writes,'実ai.itemEffects[2] writer')
 return dict(steps=m.steps,visited=visited,trace=trace,boundaries=boundaries,groups=groups,
  calls=calls,reads=m.role_reads,writes=m.role_writes,endpoint_arguments=[m.reg[0]])

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(set(opaque_writes or {})<=set(EXTERNAL)and set(epoch_events or {})<=set(EXTERNAL),'未知opaque境界を黙殺しない')
 first=_compose(raw,profile=profile,contract=contract)
 live=engine.future_live(first['trace'],len(first['boundaries']))
 replay=_compose(raw,live,opaque_writes,epoch_events,profile,contract)
 for k in('visited','reads','writes','calls','boundaries','endpoint_arguments'):
  need(exact(first[k],replay[k]),'非live RAM消去後同一有限path '+k)
 return dict(status='PASS_CONDITIONAL_TOXIC_ORB_ROOT',instruction_steps=first['steps'],
  endpoint=STOP,endpoint_arguments=first['endpoint_arguments'],conditional_call_groups=replay['groups'],
  actual_call_arguments=first['calls'],actual_role_reads=first['reads'],actual_role_writes=first['writes'],
  visited_identity=identity(json.dumps(first['visited'],separators=(',',':')).encode()),
  nonlive_ram_erased_at_each_boundary=True,internal_active_bank_host_seeded=False,
  internal_status_pointer_host_seeded=False,actual_runtime_execution_observed=False)

# source-only C layout resolver。コメントの0xoffsetは入力にしない。
def without_comments(text):return re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
def cexpr(text,constants):
 def visit(node):
  if isinstance(node,ast.Expression):return visit(node.body)
  if isinstance(node,ast.Constant):need(type(node.value)is int and node.value>=0,'非負C整数');return node.value
  if isinstance(node,ast.Name):need(node.id in constants,'既知macro '+node.id);return constants[node.id]
  need(isinstance(node,ast.BinOp)and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)),'閉じたC配列式')
  a,b=visit(node.left),visit(node.right)
  if isinstance(node.op,ast.Add):return a+b
  if isinstance(node.op,ast.Sub):return a-b
  if isinstance(node.op,ast.Mult):return a*b
  need(b>0 and a%b==0,'正確なC整数割算');return a//b
 return visit(ast.parse(text.strip(),mode='eval'))
def definition(text,name):
 m=re.search(r'\bstruct\s+'+re.escape(name)+r'\s*\{',text);need(m is not None,'公開struct '+name)
 start=m.end();depth=1;j=start
 while j<len(text)and depth:
  depth+=(text[j]=='{')-(text[j]=='}');j+=1
 need(depth==0,'完全struct終端')
 return text[start:j-1]
def split_declarations(body):
 out=[];start=depth=0
 for j,c in enumerate(body):
  depth+=(c=='{')-(c=='}');need(depth>=0,'struct brace')
  if c==';'and depth==0:out.append(body[start:j].strip());start=j+1
 need(depth==0 and not body[start:].strip(),'完全struct宣言列')
 return out

def layout(body,constants):
 """ARM32の明示scalar ABI。未対応C構文を推測して飛ばさない。"""
 fields={};bitpos=0;alignment=1
 sizes={'u8':1,'s8':1,'bool8':1,'u16':2,'item_t':2,'u32':4,'s32':4,'ItemUseFunc':4}
 for declaration in split_declarations(body):
  children=None
  if '{' in declaration:
   m=re.fullmatch(r'struct(?:\s+\w+)?\s*\{(.*)\}\s*(\w+)((?:\s*\[[^]]+\])*)',declaration,re.S)
   need(m is not None,'閉じたnested struct')
   nested,name,arrays=m.groups();children,size,align=layout(nested,constants);width=None
  else:
   m=re.fullmatch(r'((?:const\s+)?(?:struct\s+\w+|\w+)\s*\**?)\s+(\w+)((?:\s*\[[^]]+\])*)(?:\s*:\s*(\d+))?',declaration,re.S)
   if m is None:
    m=re.fullmatch(r'((?:const\s+)?(?:struct\s+\w+|\w+)\s*\*+)\s*(\w+)((?:\s*\[[^]]+\])*)(?:\s*:\s*(\d+))?',declaration,re.S)
   need(m is not None,'閉じたscalar宣言 '+declaration)
   typ,name,arrays,width=m.groups();typ=typ.strip()
   need('*'in typ or typ in sizes,'既知scalar ABI '+typ)
   size=4 if '*'in typ else sizes[typ];align=size
  need(name not in fields,'struct重複field');alignment=max(alignment,align)
  if width is not None:
   width=int(width);need(not arrays and 0<width<=size*8,'有界bitfield')
   if bitpos%(size*8)+width>size*8:bitpos=((bitpos+size*8-1)//(size*8))*(size*8)
   fields[name]=dict(offset=bitpos//8,bit=bitpos%8,width_bits=width,type_size=size);bitpos+=width
  else:
   count=1
   for expr in re.findall(r'\[([^]]+)\]',arrays):
    value=cexpr(expr,constants);need(value>0,'正のarray bound');count*=value
   offset=((bitpos+7)//8+align-1)//align*align
   fields[name]=dict(offset=offset,size=size*count)
   if children:
    for child,value in children.items():fields[name+'.'+child]={**value,'offset':offset+value['offset']}
   bitpos=(offset+size*count)*8
 size=((bitpos+7)//8+alignment-1)//alignment*alignment
 return fields,size,alignment

def source_layout(sources):
 texts={k:without_comments(v.decode())for k,v in sources.items()}
 constants={}
 for name in('MAX_BATTLERS_COUNT','NUM_BATTLE_SIDES','POKEMON_NAME_LENGTH','PARTY_SIZE',
  'BATTLE_STATS_NO','MAX_SPRITES','MAX_NUM_RAID_SHIELDS','MAX_MON_MOVES'):
  matches=[]
  for text in texts.values():matches+=re.findall(r'^\s*#define\s+'+name+r'\s+(\d+)\s*$',text,re.M)
  need(matches and len(set(matches))==1,'独立macro '+name);constants[name]=int(matches[0])
 pokemon,size,align=layout(definition(texts['cfru-include--pokemon.h'],'BattlePokemon'),constants)
 new,newsize,newalign=layout(definition(texts['cfru-include--battle.h'],'NewBattleStruct'),constants)
 battlebody=definition(texts['cfru-include--battle.h'],'BattleStruct')
 battle,_,_=layout(';'.join(split_declarations(battlebody)[:4])+';',constants)
 derived=dict(battle_pokemon=dict(size=size,alignment=align,
  fields={k:pokemon[k]for k in('species','hp','item','ability','personality','status1')}),
  battle_struct={k:battle[k]for k in('turnEffectsTracker','turnEffectsBank')},
  new_battle_struct=dict(size=newsize,alignment=newalign,
   fields={k:new[k]for k in('MagicRoomTimer','EmbargoTimers','endTurnBlockState','ai.itemEffects')}))
 need(size==88 and [pokemon[k]['offset']for k in('species','hp','item','ability','personality','status1')]==[0,40,46,56,72,76],'独立BattlePokemon layout')
 need([battle[k]['offset']for k in('turnEffectsTracker','turnEffectsBank')]==[0,1],'独立BattleStruct prefix')
 need([new[k]['offset']for k in('MagicRoomTimer','EmbargoTimers','endTurnBlockState','ai.itemEffects')]==[4,52,327,665],'独立NewBattleStruct layout')
 def enumeration(name,start):
  text=texts[name];m=re.search(r'enum(?:\s+\w+)?\s*\{\s*'+start+r'\s*,([^}]+)\}',text)
  need(m is not None,'公開enum '+start)
  names=[start]+[v.strip()for v in m.group(1).split(',')if v.strip()]
  need(all(re.fullmatch(r'[A-Za-z_]\w*',s)for s in names)and len(names)==len(set(names)),'閉じた連続enum')
  return {s:i for i,s in enumerate(names)}
 enums=dict(state=enumeration('cfru-end_turn.c','ET_Order')['ET_Block_B'],
  substate=enumeration('cfru-end_turn.c','ET_Uproar')['ET_Orbz'],
  request=enumeration('cfru-include--battle_controllers.h','REQUEST_ALL_BATTLE')['REQUEST_STATUS_BATTLE'])
 need(enums==dict(state=69,substate=2,request=40),'独立enum値')
 return dict(structs=derived,enum_values=enums,constants=constants,source_comments_used=False,
  abi='ARM32 scalar widths, natural alignment, allocation-unit bounded bitfields, 32-bit pointers')

SOURCE_IDS = {'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'cfru-end_turn.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                     'git_blob_sha': '22e1e8b7d89bde36013ab76cfb1cca363094ed80',
                     'local': 'cfru-end_turn.c',
                     'repository': 'kapibarasan000/CFRU-JP',
                     'sha256': 'c05d64d360cfc9120e0c9b55bb51027f6ddbe5146dc09da620b6e7c83f947e71',
                     'size': 69208,
                     'source': 'src/end_turn.c',
                     'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/end_turn.c'},
 'cfru-hooks': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                'git_blob_sha': '51a0f10dd4cccad235b476edd534a0e3e7e612ad',
                'local': 'cfru-hooks',
                'repository': 'kapibarasan000/CFRU-JP',
                'sha256': '19c730e12bcc8ee614b43745a1a6478429c1876a025fdce23b80a49599d8deb5',
                'size': 21787,
                'source': 'hooks',
                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/hooks'},
 'cfru-include--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': '7add3e78535b105d9d08d3d601da4e1d784f526a',
                            'local': 'cfru-include--battle.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': '8c6b332ef73bc545297b4f6c5bedc1ad11fa4470901f39cf386c1be53f4abdc9',
                            'size': 52228,
                            'source': 'include/battle.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle.h'},
 'cfru-include--battle_controllers.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                        'git_blob_sha': '306d9ae6ce5956171207a4a779fb878883f271af',
                                        'local': 'cfru-include--battle_controllers.h',
                                        'repository': 'kapibarasan000/CFRU-JP',
                                        'sha256': '95456edaefe281ebeaf55172635f8ccde14d5f4d0e6818f548ce0b37722ed9a1',
                                        'size': 11694,
                                        'source': 'include/battle_controllers.h',
                                        'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle_controllers.h'},
 'cfru-include--constants--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                       'git_blob_sha': '6ebffb06ae7978281cf9bbd6b082182e4e481714',
                                       'local': 'cfru-include--constants--battle.h',
                                       'repository': 'kapibarasan000/CFRU-JP',
                                       'sha256': '88681a4d9e3f34b8608417adf44f828b8c1a19669bba30e00fe22540e2936fb0',
                                       'size': 16608,
                                       'source': 'include/constants/battle.h',
                                       'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/battle.h'},
 'cfru-include--constants--hold_effects.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                             'git_blob_sha': 'd4239d5e56f037d8aa8d40d60dbbac8762f2c71e',
                                             'local': 'cfru-include--constants--hold_effects.h',
                                             'repository': 'kapibarasan000/CFRU-JP',
                                             'sha256': '779f5456f65683ee023f2b56fb3b69fb931d94cf17814e8c41a64097c64b8720',
                                             'size': 6450,
                                             'source': 'include/constants/hold_effects.h',
                                             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/hold_effects.h'},
 'cfru-include--gba--types.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                'git_blob_sha': '601fdf73ab404a2d1e0ccd5a4d0c3f5382ede8e0',
                                'local': 'cfru-include--gba--types.h',
                                'repository': 'kapibarasan000/CFRU-JP',
                                'sha256': '467a0219173bd2f8e20e962a9eaa43eafba298f815dab6655ae1761367d43ae6',
                                'size': 4241,
                                'source': 'include/gba/types.h',
                                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/gba/types.h'},
 'cfru-include--global.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': '574c09b9b6209f6bee6e1d3a2fb8866221af8900',
                            'local': 'cfru-include--global.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': 'c2973e69e55633ce39c9fe1763c891e5530b4ac1dc15e82a666c1f1ea7201bc0',
                            'size': 19566,
                            'source': 'include/global.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/global.h'},
 'cfru-include--new--Vanilla_functions_battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                                   'git_blob_sha': '1cc68cf9b1d44e16a912e84b8eb42c0e9160e135',
                                                   'local': 'cfru-include--new--Vanilla_functions_battle.h',
                                                   'repository': 'kapibarasan000/CFRU-JP',
                                                   'sha256': '5fb99f7ea02319dceefa94310e32543cf7c5d136f9afe2f755c7e3a9ae26193c',
                                                   'size': 10934,
                                                   'source': 'include/new/Vanilla_functions_battle.h',
                                                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/Vanilla_functions_battle.h'},
 'cfru-include--new--battle_util.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                      'git_blob_sha': '6a0382cf5ff974e2653e16b71b20377323d765da',
                                      'local': 'cfru-include--new--battle_util.h',
                                      'repository': 'kapibarasan000/CFRU-JP',
                                      'sha256': '5b934d1b648a7996efb43e95d0a2874bc5c2f32d0847ebaa6644af7507bb4f68',
                                      'size': 8339,
                                      'source': 'include/new/battle_util.h',
                                      'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/battle_util.h'},
 'cfru-include--pokemon.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                             'git_blob_sha': 'b18f2ee2a1517efa8aeb742daedac9e778d73d7a',
                             'local': 'cfru-include--pokemon.h',
                             'repository': 'kapibarasan000/CFRU-JP',
                             'sha256': 'd75972c66e85835a3fc9c859cb695c033995ba6627ba1d44f577b35136356c78',
                             'size': 29476,
                             'source': 'include/pokemon.h',
                             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/pokemon.h'},
 'cfru-include--sprite.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': 'da7057376c71e2cbe3543f262a6e360e2eeaaf8a',
                            'local': 'cfru-include--sprite.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': 'c848594606e7889276457e723c5189cbedbe71862a1b001ed9ec39299a8fe511',
                            'size': 11836,
                            'source': 'include/sprite.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/sprite.h'},
 'cfru-src--battle_util.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                             'git_blob_sha': '2ad6fd276a535f99a631ae01f38fe3f6bc0d15e5',
                             'local': 'cfru-src--battle_util.c',
                             'repository': 'kapibarasan000/CFRU-JP',
                             'sha256': '558c9a85d067e984c96bf83fb0c652a58df3b0b5fbf63620e4ea694195458ed3',
                             'size': 67724,
                             'source': 'src/battle_util.c',
                             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/battle_util.c'},
 'cfru-src--defines_battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                'git_blob_sha': 'cf9846c0e8d8c289f096bb15dcbc078cb9f75c71',
                                'local': 'cfru-src--defines_battle.h',
                                'repository': 'kapibarasan000/CFRU-JP',
                                'sha256': 'e85a4e7a35321a05972fa3742fe469619869127b545242f640c6c6cf061355de',
                                'size': 7098,
                                'source': 'src/defines_battle.h',
                                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/defines_battle.h'}}

SOURCE_IDS.update({'cfru-include--item.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                          'git_blob_sha': '987a5aaa2cda9ee5e68300f67426f9c102b6cd26',
                          'local': 'cfru-include--item.h',
                          'repository': 'kapibarasan000/CFRU-JP',
                          'sha256': '45409d7ffc93c6a282cb8b934cd35f0ee0e9ae0b05bc4364353ba47ec5d7569a',
                          'size': 3438,
                          'source': 'include/item.h',
                          'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/item.h'},
 'cfru-item.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                 'git_blob_sha': 'ea5302c0dc2bb9fc92e665aab6015a27ff4275d7',
                 'local': 'cfru-item.c',
                 'repository': 'kapibarasan000/CFRU-JP',
                 'sha256': '885c2ae9fa78d145eec1eca4333104b6fdd90a1d5afbbe191e0bc3398e740922',
                 'size': 55431,
                 'source': 'src/item.c',
                 'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/item.c'},
 'manifests--item_ids.csv': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                             'git_blob_sha': '3ce2c8c6b0cd2353f3c9d029965b031545b1525f',
                             'local': 'manifests--item_ids.csv',
                             'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                             'sha256': 'f3c12e66256d29b675f1bd4f8e68bd0a90e20eb49b5715b8ecbfbc65aa8b2b90',
                             'size': 447424,
                             'source': 'manifests/item_ids.csv',
                             'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/manifests/item_ids.csv'},
 'scripts--build_battle_core.py': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                                   'git_blob_sha': '09bde3df2e2d33701141da7cec6eb53a6562f91c',
                                   'local': 'scripts--build_battle_core.py',
                                   'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                   'sha256': 'e83f659b912e4f61f790ef648f30dd7e669f737da84f326c234dc491a6d135c0',
                                   'size': 239192,
                                   'source': 'scripts/build_battle_core.py',
                                   'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/scripts/build_battle_core.py'},
 'scripts--build_id_spaces.py': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                                 'git_blob_sha': '46e0c760c43bcfc407515f89f97b7ac64c822976',
                                 'local': 'scripts--build_id_spaces.py',
                                 'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                 'sha256': '2b9cb736fffcf8df21344aa86d8919b997b74e64b882d14e6db9176e515d0fd6',
                                 'size': 86544,
                                 'source': 'scripts/build_id_spaces.py',
                                 'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/scripts/build_id_spaces.py'}})

def source_item(sources):
 rows=list(csv.DictReader(io.StringIO(sources['manifests--item_ids.csv'].decode())))
 selected=[r for r in rows if r['item_key']=='ITEM_KEY_TOXIC_ORB']
 need(len(selected)==1,'独立current Toxic Orb行一つ')
 row=selected[0]
 for k,v in dict(id='894',cfru_id='680',cfru_symbol='ITEM_TOXIC_ORB',
  classification='CFRU_APPEND',hold_effect_key='ITEM_EFFECT_TOXIC_ORB').items():
  need(row[k]==v,'固定current item意味 '+k)
 macro=re.findall(r'^#define\s+ITEM_EFFECT_TOXIC_ORB\s+(\d+)\s*$',sources['cfru-include--constants--hold_effects.h'].decode(),re.M)
 need(macro==['75'],'独立hold effect75')
 fields,size,align=layout(definition(without_comments(sources['cfru-include--item.h'].decode()),'Item'),{})
 need(size==40 and fields['holdEffect']==dict(offset=14,size=1),'独立Item stride40/holdEffect14')
 a=ITEM_TABLE+int(row['id'])*size+fields['holdEffect']['offset'];need(a==ITEM_EFFECT_FIELD,'実tableからsource indexの選択field')
 return dict(canonical_id=int(row['id']),upstream_id=int(row['cfru_id']),symbol=row['cfru_symbol'],
  hold_effect_symbol=row['hold_effect_key'],hold_effect=int(macro[0]),table_address=ITEM_TABLE,
  item_stride=size,field_offset=14,field_address=a,
  expected={a:bytes([int(macro[0])])},observed_value_input=False)

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'閉じた固定source一覧')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'独立source全文 '+name)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立Git blob '+name)
 roles={
  'cfru-hooks':['TurnBasedEffects 08017A68 0'],
  'cfru-end_turn.c':['u8 TurnBasedEffects(void)','if (gBattleTypeFlags & BATTLE_TYPE_SAFARI)',
   'gHitMarker |= (HITMARKER_GRUDGE | HITMARKER_x20);',
   'gActiveBattler = gBankAttacker = gBankTarget = gBanksByTurnOrder[gBattleStruct->turnEffectsBank];',
   'gBattleMoveDamage = 0;', 'switch (gBattleStruct->turnEffectsTracker)',
   'case ET_Block_B:', 'switch(gNewBS->endTurnBlockState)', 'case ET_Orbz:',
   'u8 itemEffect = ITEM_EFFECT(gActiveBattler);', 'case ITEM_EFFECT_TOXIC_ORB:',
   'if (CanBePoisoned(gActiveBattler, gActiveBattler, FALSE))',
   'gLastUsedItem = ITEM(gActiveBattler);','RecordItemEffectBattle(gActiveBattler, itemEffect);',
   'gBattleMons[gActiveBattler].status1 |= STATUS1_TOXIC_POISON;',
   'EmitSetMonData(0, REQUEST_STATUS_BATTLE, 0, 4, &gBattleMons[gActiveBattler].status1);',
   'MarkBufferBankForExecution(gActiveBattler);'],
  'cfru-src--defines_battle.h':['#define ITEM_EFFECT(bank) GetBankItemEffect(bank)',
   '#define ITEM(bank) gBattleMons[bank].item','#define ABILITY(bank) gBattleMons[bank].ability',
   '#define BATTLER_ALIVE(bank) (gBattleMons[bank].hp > 0)'],
  'cfru-src--battle_util.c':['item_effect_t GetBankItemEffect(u8 bank)',
   'if (ABILITY(bank) != ABILITY_KLUTZ && !gNewBS->EmbargoTimers[bank] && !IsMagicRoomActive())',
   'return ItemId_GetHoldEffect(ITEM(bank));','void RecordItemEffectBattle(u8 bank, u8 itemEffect)',
   'gNewBS->ai.itemEffects[bank] = itemEffect;',
   'bool8 CanBePoisoned(u8 bankDef, u8 bankAtk, bool8 checkFlowerVeil)',
   'u16 atkAbility = (bankAtk > gBattlersCount) ? 0 : ABILITY(bankAtk);',
   'u16 defAbility = ABILITY(bankDef);',
   'CanBeGeneralStatused(bankDef, defAbility, atkAbility, checkFlowerVeil)',
   'ABILITY(PARTNER(bankDef)) == ABILITY_PASTELVEIL'],
  'cfru-include--new--battle_util.h':['item_effect_t GetBankItemEffect(u8 bank);',
   'void RecordItemEffectBattle(u8 bank, u8 itemEffect);',
   'bool8 CanBePoisoned(u8 bankDef, u8 bankAtk, bool8 checkFlowerVeil);'],
  'cfru-include--gba--types.h':['typedef uint8_t   u8;','typedef uint16_t u16;',
   'typedef uint32_t u32;','typedef u8  bool8;','typedef u8  item_effect_t;'],
  'cfru-include--pokemon.h':['void __attribute__((long_call)) EmitSetMonData(u8 a, u8 request, u8 c, u8 bytes, void *data);'],
  'cfru-include--new--Vanilla_functions_battle.h':['void __attribute__((long_call)) MarkBufferBankForExecution(u8 bank);'],
  'cfru-include--item.h':['typedef void (*ItemUseFunc)(u8);'],
  'cfru-item.c':['u8 ItemId_GetHoldEffect(u16 itemId)','return gItems[SanitizeItemId(itemId)].holdEffect;'],
  'scripts--build_id_spaces.py':["for row in model[\"items\"]:","#define {row['item_key']} {row['id']}u",
   'redefine_alias(alias["source_symbol"], alias["item_key"])',
   '_c_token(row["hold_effect_key"])'],
  'scripts--build_battle_core.py':['#define ITEMS_COUNT 999u',
   'extern const struct Item gItemData[];\\n#define gItems ((struct Item*) gItemData)'],
  'BPRJ.ld':['gBattleStruct = 0x2023F48;','gNewBS = 0x203DFB0;',
   'gBattleMons = 0x2023B44;', 'gActiveBattler = 0x2023B24;',
   'gBanksByTurnOrder = 0x2023B3E;', 'gBankAttacker = 0x2023CCB;',
   'gBankTarget = 0x2023CCC;', 'gHitMarker = 0x2023D30;',
   'gBattleMoveDamage = 0x2023CB0;', 'gLastUsedItem = 0x2023CC8;',
   'gEffectBank = 0x2023CCE;', 'EmitSetMonData = 0x800D9E4 | 1;',
   'MarkBufferBankForExecution = 0x8016A58 | 1;']}
 for name,tokens in roles.items():
  text=sources[name].decode()
  for token in tokens:need(token in text,'公開source意味 '+name+' '+token)
 return dict(layout=source_layout(sources),item={k:v for k,v in source_item(sources).items()if k!='expected'})

def fixed_parts():
 parts={i.address:encoded(i)for i in list(INS.values())+list(ABI_INS.values())}
 for a,v in WORDS.items():need(a not in parts,'命令/literal非重複');parts[a]=v.to_bytes(4,'little')
 return parts

def merge_parts(parts):
 rows=[];start=end=None;data=b''
 for a,b in sorted(parts.items()):
  need(end is None or a>=end,'保護窓非重複')
  if a!=end:
   if start is not None:rows.append(dict(address=start,**identity(data)))
   start=a;data=b''
  data+=b;end=a+len(b)
 if start is not None:rows.append(dict(address=start,**identity(data)))
 return rows
FIXED_WINDOWS=merge_parts(fixed_parts())
ITEM_WINDOWS=[dict(address=ITEM_EFFECT_FIELD,**identity(bytes([75])))]
ALL_WINDOWS=sorted(FIXED_WINDOWS+ITEM_WINDOWS,key=lambda r:r['address'])
WINDOWS={f'toxic_orb_{j}':(r['address'],r['size'])for j,r in enumerate(ALL_WINDOWS)}

def bind_semantics(raw,sources):
 for i in list(INS.values())+list(ABI_INS.values()):need(chunk(raw,i.address,i.size)==encoded(i),'独立命令 '+hex(i.address))
 for a,v in WORDS.items():need(d.u32(raw,a)==v,'独立symbol/literal '+hex(a))
 item=source_item(sources)
 for a,b in item['expected'].items():need(chunk(raw,a,len(b))==b,'source独立current item効果')
 d.signed(raw,ALL_WINDOWS)
 return dict(status='PASS_SOURCE_REGISTERED_TOXIC_ORB_ENCODING',
  executed_model_instruction_count=len(INS),opaque_signature_instruction_count=len(ABI_INS),
  instruction_bytes=sum(i.size for i in list(INS.values())+list(ABI_INS.values())),
  source_item={k:v for k,v in item.items()if k!='expected'},
  complete_item_table_or_sanitizer_extent_source_proven=False,
  actual_hook_and_state_registration=True)

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'Toxic Orb hitのみ')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,
  classified_window=dict(address=HIT_CALL,size=6),
  complete_instructions=[dict(address=HIT_CALL,size=4,kind='call',target=0x090FB594),
   dict(address=0x090FA7C0,size=2,kind='literal',register=3,literal=0x090FA7F8)],
  hit=dict(address=hit,size=4),input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))
def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HITS[0])),'全witness field一致')
 return HIT_CALL,6

def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'immutable新scope保護窓')
 return copy.deepcopy(ALL_WINDOWS)
def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS),'親unknown全field一致')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),
  diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),
  hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),windows=copy.deepcopy(ALL_WINDOWS),
  claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE))
prepare_review=make_review

def measure(raw):return [dict(address=w['address'],**identity(chunk(raw,w['address'],w['size'])))for w in ALL_WINDOWS]
def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profile'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'current/diagnostic分離')
 for k,v in(('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE)):
  need(exact(review[k],v),'review固定field '+k)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS)and exact(selected,review['hits']),'親unknown全field保持')
 protected_windows(review);source=sources_bind(review,sources)
 encoding=bind_semantics(raw,sources);d.signed(raw,selected);composition=compose_selected(raw)
 e=evidence_template(HITS[0]);a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_TOXIC_ORB_MINIMUM_THUMB',
  count=1,hits=list(HITS),source=source,encoding=encoding,composition=composition,
  protected_windows=len(ALL_WINDOWS),protected_bytes=sum(r['size']for r in ALL_WINDOWS),**copy.deepcopy(CLAIMS))
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate')
 return _regions(raw,inherited,review,sources)
validate=_regions
