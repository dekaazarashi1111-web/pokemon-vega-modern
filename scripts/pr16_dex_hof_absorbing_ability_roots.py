"""登録FF29→全wrapper→吸収特性dispatchの条件付き最小Thumb型。ROM byteを保存しない。"""
import ast,copy,hashlib,json,re
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_animation_registered_roots as flags_engine
from pr16_dex_hof_extra_roots import exact,encoded
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
KIND='registered_absorbing_ability_minimum_thumb';KINDS=(KIND,);TYPE_CATEGORY='code'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x090B69A9,);HELD_HITS=()
EXPECTED_HITS=[dict(address=0x090B69A9,target=167694576,kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',size=4,sha256='3f349309f12748a318dca9299d88b1192967d83085372223c533c897f490b2ad',classification='UNCLASSIFIED',accepted=False,reason='no_complete_typed_asset_consumer_witness',owner_candidates=[])]
ENTRY=0x0911AA8C;HANDLER=0x0911C7EC;PRIMARY_SLOT=0x0903F84C;SECONDARY_SLOT=0x0903F8F4
CURSOR=0x02023CD4;ATTACKER=0x02023CCB;TARGET=0x02023CCC;COUNT=0x02023B2C
MOVE=0x02023CAA;FLAGS=0x02022AAC;MONS=0x02023B44;NEWBS=0x0203DFB0;BSTRUCT=0x02023F48
LAST_ABILITY=0x0203DFAC;STATUSES=0x02023D5C;SCRIPTING=0x02023F24
CONTEXT=0x02010000;BATTLE_CONTEXT=0x02012000;SCRIPT=0x02013000
ROOT=dict(kind='primary_ff_registered_api_to_secondary29_absorbing_ability',primary_opcode=255,primary_slot=PRIMARY_SLOT,primary_entry=ENTRY,secondary_opcode=41,secondary_slot=SECONDARY_SLOT,handler=HANDLER,get_bank_call=0x0911C7FA,ability_call=0x0911C842,ability_entry=0x090B667C,stage77_wrapper=0x095D5874,stage72_entry=0x0953410C,stage72_wrapper=0x09533AD4,original_prologue=0x0953417C,original_continuation=0x090B6688,case3_slot=0x0915E924,case3_entry=0x090B6980,minimum_start=0x090B69A8,minimum_size=6)
SPECS=[]
def block(a,specs):
 for k,*args in specs:SPECS.append((a,k,tuple(args)));a+=4 if k=='call'else 2
 return a
# 固定公開FF dispatcherとFF29 sourceの順序に基づく手書き意味。decoderは入力にしない。
block(ENTRY,[('literal',3,0x0911AAA4),('push',16,True),('mem',True,'word',2,3,0),('addi',1,2,1),('mem',False,'word',1,3,0),('mem',True,'byte',2,2,1),('literal',3,0x0911AAA8),('shift','lsl',2,2,2),('regmem','ldr',3,2,3),('call',0x0911DC4C)])
block(0x0911DC4C,[('bx',3)])
block(HANDLER,[('push',240,True),('movhi',14,8),('push',0,True),('literal',5,0x0911CA30),('mem',True,'word',3,5,0),('spadd',-8),('mem',True,'byte',0,3,1),('call',0x090D3D2C),('mem',True,'word',1,5,0),('mem',True,'byte',2,1,3),('mem',True,'byte',3,1,2),('shift','lsl',2,2,8),('alu','orr',2,3),('mem',True,'byte',3,1,4),('shift','lsl',3,3,16),('alu','orr',3,2),('mem',True,'byte',2,1,5),('shift','lsl',2,2,24),('alu','orr',2,3),('literal',3,0x0911CA34),('movhi',8,2),('shift','lsl',2,0,2),('regmem','ldr',2,2,3),('literal',3,0x0911CA38),('shift','lsl',4,0,0),('literal',6,0x0911CA3C),('alu_ext','tst',2,3),('branch',0,0x0911C836)])
block(0x0911C836,[('mem',True,'half',3,6,0),('imm','mov',2,0),('spmem',False,3,0),('shift','lsl',1,4,0),('imm','mov',3,0),('imm','mov',0,3),('call',0x090B667C)])
# selector0はsource BS_GET_TARGET。実switch table→gBankTarget readerを最後まで実行。
block(0x090D3D2C,[('push',16,True),('imm','cmp',0,15),('branch',8,0x090D3D3A),('literal',3,0x090D3D8C),('shift','lsl',0,0,2),('regmem','ldr',3,3,0),('movhi',15,3)])
block(0x090D3D7E,[('literal',3,0x090D3DA4),('mem',True,'byte',0,3,0),('jump',0x090D3D3C)])
block(0x090D3D3C,[('pop',16,True)])
# actual hook preserves fourth argument in r12; normal route does not read Circus flags.
block(0x090B667C,[('movhi',12,3),('literal',3,0x090B6684),('bx',3)])
block(0x095D5874,[('literal',3,0x095D5894),('mem',True,'word',3,3,0),('shift','lsl',3,3,5),('branch',5,0x095D5890)])
block(0x095D5890,[('literal',3,0x095D58A0),('bx',3)])
block(0x0953410C,[('movhi',3,12),('push',4,False),('literal',2,0x09534160),('movhi',12,2),('pop',4,False),('bx',12)])
block(0x09533AD4,[('push',240,True),('shift','lsl',4,1,0),('spadd',-28),('spaddr',1,48),('mem',True,'half',5,1,0),('shift','lsl',1,4,0),('spmem',False,5,0),('shift','lsl',6,0,0),('call',0x0953417C)])
block(0x0953417C,[('push',240,True),('movhi',7,10),('movhi',6,9),('movhi',5,8),('movhi',14,11),('push',224,True),('push',8,False),('literal',3,0x09534194),('movhi',12,3),('pop',8,False),('bx',12)])
# OriginalAbilityBattleEffects prologue: all RAM/stack producers used below are modeled.
block(0x090B6688,[('spadd',-68),('spmem',False,2,16),('spaddr',2,104),('mem',True,'half',7,2,0),('imm','mov',2,0),('spmem',False,2,8),('spmem',False,2,20),('spmem',False,2,24),('literal',2,0x090B6924),('movhi',12,1),('spmem',False,1,12),('mem',True,'word',1,2,0),('movhi',8,2),('imm','mov',2,160),('shift','lsl',6,1,0),('shift','lsl',2,2,2),('shift','lsl',4,0,0),('alu','and',6,2),('alu_ext','tst',1,2),('branch',0,0x090B66B2)])
block(0x090B66B2,[('literal',5,0x090B6928),('literal',0,0x090B692C),('mem',True,'byte',2,5,0),('spmem',False,0,28),('mem',True,'byte',0,0,0),('spmem',False,5,32),('compare',0,2),('branch',8,0x090B66C6)])
block(0x090B66C6,[('literal',0,0x090B6930),('shift','lsl',5,0,0),('imm','mov',0,88),('alu','mul',2,0),('spmem',False,5,8),('regmem','ldrh',5,2,5),('spmem',False,5,48),('spmem',True,5,8),('movhi',12,5),('addhi',2,12),('mem',True,'word',2,2,72),('spmem',False,2,52),('literal',2,0x090B6934),('spmem',False,2,40),('mem',True,'byte',2,2,0),('alu','mul',2,0),('regmem','ldrh',5,2,5),('addhi',2,12),('mem',True,'word',2,2,72),('spmem',False,5,56),('spmem',False,2,60),('imm','cmp',3,0),('branch',0,0x090B673C)])
block(0x090B673C,[('spmem',True,3,12),('alu','mul',3,0),('shift','lsl',0,3,0),('addhi',0,12),('literal',2,0x090B6938),('mem',True,'half',3,0,56),('movhi',11,2),('mem',False,'half',3,2,0),('imm','cmp',7,0),('branch',1,0x090B66FE)])
block(0x090B66FE,[('literal',3,0x090B693C),('movhi',9,3),('mem',True,'word',3,3,0),('mem',True,'byte',3,3,19),('spmem',False,3,44),('imm','mov',3,160),('shift','lsl',3,3,8),('alu','and',1,3),('imm','mov',3,128),('shift','lsl',3,3,8),('compare',1,3),('branch',0,0x090B67DC),('imm','mov',2,178),('literal',3,0x090B6940),('mem',True,'word',1,3,0),('movhi',10,3),('imm','mov',3,1),('shift','lsl',2,2,1),('regmem','ldrb',2,1,2),('spmem',False,1,36),('alu_ext','tst',3,2),('branch',1,0x090B6752),('imm','cmp',4,20),('branch',8,0x090B67B4),('literal',3,0x090B6944),('shift','lsl',4,4,2),('regmem','ldr',3,3,4),('movhi',15,3)])
block(0x090B6980,[('imm','cmp',7,0),('branch',1,0x090B6986),('jump',0x090B67B4),('spmem',True,3,12),('literal',4,0x090B6CBC),('mem',False,'byte',3,4,23),('movhi',3,11),('mem',True,'half',1,3,0),('imm','cmp',1,115),('branch',1,0x090B6998),('call',0x090BA848),('branch',9,0x090B699E),('call',0x090BA39C),('imm','cmp',1,31),('branch',1,0x090B69A6),('call',0x090BA858),('branch',9,0x090B69AC),('call',0x090BA74C),('imm','cmp',1,11)])
INS={a:party.Ins(a,k,args)for a,k,args in SPECS};need(len(INS)==len(SPECS),'非重複手書き命令')
WORDS={PRIMARY_SLOT:ENTRY|1,SECONDARY_SLOT:HANDLER|1,0x0911AAA4:CURSOR,0x0911AAA8:0x0903F850,0x0911CA30:CURSOR,0x0911CA34:STATUSES,0x0911CA38:0x130480C0,0x0911CA3C:MOVE,0x090D3D8C:0x09161410,0x09161410:0x090D3D7E,0x090D3DA4:TARGET,0x090B6684:0x095D5875,0x095D5894:FLAGS,0x095D58A0:0x0953410D,0x09534160:0x09533AD5,0x09534194:0x090B6689,0x090B6924:FLAGS,0x090B6928:ATTACKER,0x090B692C:COUNT,0x090B6930:MONS,0x090B6934:TARGET,0x090B6938:LAST_ABILITY,0x090B693C:BSTRUCT,0x090B6940:NEWBS,0x090B6944:0x0915E918,0x0915E924:0x090B6980,0x090B6CBC:SCRIPTING}
PROFILE=dict(battle_flags=0,attacker=1,target=0,battlers_count=2,current_move=1,abilities=[32,10],target_statuses3=0,dynamic_move_type=0,skip_switchin_flag_byte=0,battle_context=BATTLE_CONTEXT,newbs_context=CONTEXT,script_buffer=SCRIPT,script_selector=0,same_context_epoch=True,same_stack_epoch=True)
CLAIMS=dict(proof_scope='conditional_registered_absorbing_ability_minimum_thumb',conditional_registered_api_entry=True,actual_secondary_dispatch_executed=True,whole_candidate_identity_checked_by_parent_required=True,actual_runtime_execution_observed=False,full_story_reachability_claimed=False,natural_battle_entry_reachability_claimed=False,full_script_prefix_executed=False,opaque_callee_effects_proven=False,universal_heap_or_irq_lifetime_proven=False,whole_function_range_classified=False,pointer_interpretation_claimed=False,retirement_proven=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT=dict(entry_ja='実primaryFF登録handler APIへ有効FF29/target selector0のRAM scriptを与える条件。FF実increment/table/BX→FF29実GetBankForBattleScript→AbilityBattleEffectsへ合成。自然script producer/通常playは未証明。',normal_ja='battle flags0の十分条件でStage77のbit26検査がnormal branchへ直接分岐。gBattleCircusFlags0203DFBCは読みさえせず、その値・producer・epochを仮定しない。',calls_ja='GetBankForBattleScriptとStage77/Stage72 wrappers・original prologue・case3 dispatcherを全命令実行し、途中opaque calleeは0。引数5番moveArgも実caller stack writer→全frame→readerで継承する。',memory_ja='API入口に列記fieldだけを与え、同script/battle/NewBattle/stack epochと同期実行を条件にする。3個の透明checkpointでfuture read-before-write射影以外のRAMをUnknownへ消去して同pathを再合成。IRQ/heap普遍寿命は保証しない。',minimum_ja='分類は090B69A8/6byteのみ。ability32では実BLへ到達してcalleeへ分岐、ability10ではBLを迂回して後続CMPを実行する。両ケースの命令fetch範囲の和が6byteを覆う。hit先calleeの効果や復帰は主張しない。')
CHECKPOINTS=(0x0911C7FE,0x09533AD4,0x090B6688)
class Machine(flags_engine.Machine):
 def __init__(self,*args,**kw):super().__init__(*args,**kw);self.all_reads=[]
 def read(self,a,n):
  v=super().read(a,n);self.all_reads.append((self.pc,a,n,v));return v

def preservation_contract(live,writes=(),events=None):
 events={}if events is None else events
 need(type(events)is dict and set(events)<={'battle_context_epoch_changed','newbs_epoch_changed','script_epoch_changed','stack_epoch_changed'}and all(type(v)is bool for v in events.values()),'閉じたepoch条件')
 need(not any(events.values()),'同期APIの同epochを維持')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(v)is int and 0<=v<1<<(8*n)and 0<=a<a+n<=1<<32,'有限外部書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live破壊禁止')
 return True

def _compose(raw,ability,projections=None,intervening_writes=None,epoch_events=None,profile=None,contract=None):
 need(type(ability)is int and ability in(32,10),'二有限ability入力だけ')
 need(profile is None or exact(profile,PROFILE),'閉じたAPI profile')
 need(contract is None or exact(contract,CONTRACT),'閉じたAPI条件')
 need(d.u32(raw,PRIMARY_SLOT)==ENTRY|1 and d.u32(raw,SECONDARY_SLOT)==HANDLER|1,'実FF/FF29登録')
 mem={};trace=[];visited=[];groups=[];fetches=[];checkpoints=[]
 for a,n,v in((CURSOR,4,SCRIPT),(SCRIPT,1,255),(SCRIPT+1,1,41),(SCRIPT+2,1,0),(ATTACKER,1,1),(TARGET,1,0),(COUNT,1,2),(MOVE,2,1),(FLAGS,4,0),(STATUSES,4,0),(MONS,2,1),(MONS+72,4,0),(MONS+56,2,ability),(MONS+88,2,1),(MONS+88+72,4,0),(NEWBS,4,CONTEXT),(CONTEXT+356,1,0),(BSTRUCT,4,BATTLE_CONTEXT),(BATTLE_CONTEXT+19,1,0)):
  rt.setmem(mem,a,n,v)
 # script failure pointer is decoded but never used on these prefixes; valid bounded value only.
 for j in range(4):rt.setmem(mem,SCRIPT+3+j,1,(SCRIPT>>(8*j))&255)
 m=Machine(raw,ENTRY,{},mem,instructions=INS,trace=trace)
 stop=0x090BA74C if ability==32 else 0x090B69AE
 while m.pc!=stop:
  need(m.steps<400,'有限registered ability prefix')
  need(m.pc in INS,'全callee命令を持つ閉じたprefix '+hex(m.pc))
  if m.pc in CHECKPOINTS:
   ix=len(checkpoints);checkpoints.append(m.pc);trace.append(('boundary',ix,0))
   if projections is not None:
    need(ix<len(projections),'全checkpoint射影');live=projections[ix]
    preservation_contract(live,(intervening_writes or {}).get(m.pc,()),(epoch_events or {}).get(m.pc,{}))
    for a,n,v in(intervening_writes or {}).get(m.pc,()):rt.setmem(m.mem,a,n,v)
    kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
    groups.append(dict(pc=m.pc,required_fields=[dict(address=a,size=n)for a,n in live],transparent_internal_checkpoint=True,opaque_callee=False,same_context_epoch_required=True))
  if m.pc in(0x090B667C,0x09533AD4,0x0953417C):
   need(m.reg[:4]==[3,0,0,0]and m.read(m.reg[13],2)==1,'実5引数を全wrapper前で保持')
  if m.pc==0x090B6980:need(m.reg[7]==1 and m.read(LAST_ABILITY,2)==ability,'実source field→gLastUsedAbility/case3')
  visited.append(m.pc);fetches.append((m.pc,INS[m.pc].size));m.step()
 need(checkpoints==list(CHECKPOINTS),'全内部checkpointを順に通る')
 need(not any(a<=0x0203DFBC<a+n for _,a,n,_ in m.all_reads),'normal branchはCircus flagsを読まない')
 need(m.reg[1]==ability,'実ability producerからhit gate')
 need((0x090B69A8 in visited)==(ability==32)and(0x090B69AC in visited)==(ability==10),'二pathの正確なhit coverage')
 return dict(steps=m.steps,trace=trace,visited=visited,fetches=fetches,checkpoints=checkpoints,groups=groups,reads=m.all_reads,stop=stop,minimum_stack_pointer=m.reg[13])

def compose_selected(raw,intervening_writes=None,epoch_events=None,profile=None,contract=None):
 need(set(intervening_writes or {})<=set(CHECKPOINTS)and set(epoch_events or {})<=set(CHECKPOINTS),'未知checkpoint禁止')
 out=[];coverage=set()
 for ability in(32,10):
  first=_compose(raw,ability,profile=profile,contract=contract)
  live=engine.future_live(first['trace'],len(first['checkpoints']))
  replay=_compose(raw,ability,live,intervening_writes,epoch_events,profile,contract)
  need(first['visited']==replay['visited']and first['fetches']==replay['fetches'],'非live消去後も同実path')
  for a,n in first['fetches']:coverage.update(range(a,a+n))
  out.append(dict(ability=ability,instruction_steps=first['steps'],endpoint=first['stop'],future_live_checkpoints=replay['groups'],executed_hit_call=ability==32,executed_successor_cmp=ability==10,trace_identity=identity(json.dumps(first['visited'],separators=(',',':')).encode())))
 need(set(range(0x090B69A8,0x090B69AE))<=coverage,'実fetch和が完全6byteを包含')
 return dict(status='PASS_CONDITIONAL_REGISTERED_ABSORBING_ABILITY',cases=out,opaque_calls=0,nonlive_ram_erased_at_each_checkpoint=True,internal_call_arguments_host_seeded=False,circus_flags_read=False,circus_flags_producer_required=False,minimum_executed_bytes=6,actual_runtime_execution_observed=False)

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
 sizes={'u8':1,'s8':1,'bool8':1,'u16':2,'item_t':2,'u32':4,'s32':4}
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

SOURCE_IDS = {'battle-assembly--data--battle_script_commands_table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                                           'git_blob_sha': '10e8cf9821e5be79798b3ab1d02ea3e44ce44f05',
                                                           'local': 'battle-assembly--data--battle_script_commands_table.s',
                                                           'repository': 'kapibarasan000/CFRU-JP',
                                                           'sha256': 'ef6615d20d0768e23828b941fcd2a4f04ba06507a7ed498ab51b8db10e71f5f6',
                                                           'size': 11083,
                                                           'source': 'assembly/data/battle_script_commands_table.s',
                                                           'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/battle_script_commands_table.s'},
 'battle-battle_script_macros.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                   'git_blob_sha': 'bc62b1a589d0569980bd723d8da6272f40f12817',
                                   'local': 'battle-battle_script_macros.s',
                                   'repository': 'kapibarasan000/CFRU-JP',
                                   'sha256': '203f55037871e670401692a2a08ba282745a442fc84fca0615fbe1b136f8f317',
                                   'size': 28316,
                                   'source': 'battle_script_macros.s',
                                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/battle_script_macros.s'},
 'battle-src--new_bs_commands.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                   'git_blob_sha': '78614276ea045eaa06781210d588dd6ea6995bf3',
                                   'local': 'battle-src--new_bs_commands.c',
                                   'repository': 'kapibarasan000/CFRU-JP',
                                   'sha256': '203c32caf217965e468bc2efee45809b05289c51201412250b2352e17643688b',
                                   'size': 63964,
                                   'source': 'src/new_bs_commands.c',
                                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/new_bs_commands.c'},
 'cfru-abilities.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                      'git_blob_sha': '73be02b9f4df796c4ddddb774882dcff36b0e369',
                      'local': 'cfru-abilities.h',
                      'repository': 'kapibarasan000/CFRU-JP',
                      'sha256': 'fa0f9fffe2192c6230e7b89162bfcb0745a4ce49af8f24f0d7de581ac4eb9f9c',
                      'size': 9550,
                      'source': 'include/constants/abilities.h',
                      'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/abilities.h'},
 'cfru-ability_battle_effects.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                   'git_blob_sha': 'bbd0efae494ac96763cf609d1af45ed9b129bbc8',
                                   'local': 'cfru-ability_battle_effects.c',
                                   'repository': 'kapibarasan000/CFRU-JP',
                                   'sha256': '760725330a1c94117de914f880807543ab97d97e502b1166d3278e0061144382',
                                   'size': 113039,
                                   'source': 'src/ability_battle_effects.c',
                                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/ability_battle_effects.c'},
 'cfru-include--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': '7add3e78535b105d9d08d3d601da4e1d784f526a',
                            'local': 'cfru-include--battle.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': '8c6b332ef73bc545297b4f6c5bedc1ad11fa4470901f39cf386c1be53f4abdc9',
                            'size': 52228,
                            'source': 'include/battle.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle.h'},
 'cfru-include--battle_script_commands.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                            'git_blob_sha': '20e03b257eb35f327fcc45c1e767402c7fe07286',
                                            'local': 'cfru-include--battle_script_commands.h',
                                            'repository': 'kapibarasan000/CFRU-JP',
                                            'sha256': '73eed110683fa096dff02fc64047fc605a809602009987fc3f7725b9be8a28cf',
                                            'size': 3373,
                                            'source': 'include/battle_script_commands.h',
                                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle_script_commands.h'},
 'cfru-include--battle_util.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                 'git_blob_sha': '444a9885fe3f2fe2301802279f4a5e622f678f30',
                                 'local': 'cfru-include--battle_util.h',
                                 'repository': 'kapibarasan000/CFRU-JP',
                                 'sha256': 'd5561a9dfc48b893202a62222fb023844f289b772115c71adccdc32c70d0675e',
                                 'size': 5033,
                                 'source': 'include/battle_util.h',
                                 'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle_util.h'},
 'cfru-include--constants--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                       'git_blob_sha': '6ebffb06ae7978281cf9bbd6b082182e4e481714',
                                       'local': 'cfru-include--constants--battle.h',
                                       'repository': 'kapibarasan000/CFRU-JP',
                                       'sha256': '88681a4d9e3f34b8608417adf44f828b8c1a19669bba30e00fe22540e2936fb0',
                                       'size': 16608,
                                       'source': 'include/constants/battle.h',
                                       'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/battle.h'},
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
                                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/defines_battle.h'},
 'stage72_ability_runtime.c': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                               'git_blob_sha': '449a454fd0b9da4b9bbce3f90400c2ae314772f7',
                               'local': 'stage72_ability_runtime.c',
                               'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                               'sha256': 'a00e37540d968ecda3c26ab4e7606a7c5efe249621067449921be120ed03a60b',
                               'size': 52635,
                               'source': 'overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c',
                               'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c'},
 'stage72_hooks.S': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                     'git_blob_sha': '85ec1fc2bbe8957fbddc9f57b4d3de47d753d234',
                     'local': 'stage72_hooks.S',
                     'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                     'sha256': '5250cf5f64bb16ac743ad7bf31ce8b572fd29f6265d07acacf7f30ca3cd9650a',
                     'size': 9372,
                     'source': 'overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S',
                     'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S'},
 'stage77_suppression.S': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                           'git_blob_sha': '7d28b40947a86bfde4031f626348c5f28e4bfbfa',
                           'local': 'stage77_suppression.S',
                           'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                           'sha256': '725a876b24385aab13994a89d5701de8e9e77a63358d03ab8ae1e7de8f5152e0',
                           'size': 4840,
                           'source': 'overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S',
                           'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S'}}

def source_layout(sources):
 texts={k:without_comments(v.decode())for k,v in sources.items()};constants={}
 for name in('MAX_BATTLERS_COUNT','NUM_BATTLE_SIDES','POKEMON_NAME_LENGTH','PARTY_SIZE','BATTLE_STATS_NO','MAX_SPRITES','MAX_NUM_RAID_SHIELDS','MAX_MON_MOVES'):
  matches=[]
  for text in texts.values():matches+=re.findall(r'^\s*#define\s+'+name+r'\s+(\d+)\s*$',text,re.M)
  need(matches and len(set(matches))==1,'独立macro '+name);constants[name]=int(matches[0])
 pokemon,size,align=layout(definition(texts['cfru-include--pokemon.h'],'BattlePokemon'),constants)
 new,newsize,newalign=layout(definition(texts['cfru-include--battle.h'],'NewBattleStruct'),constants)
 def prefix(name,final):
  decls=split_declarations(definition(texts['cfru-include--battle.h'],name));end=[i for i,s in enumerate(decls)if re.search(r'\b'+final+r'\s*(?:\[[^]]+\])?$',s)]
  need(len(end)==1,'一意source prefix末尾');return layout(';'.join(decls[:end[0]+1])+';',constants)[0]
 battle=prefix('BattleStruct','dynamicMoveType');scripting=prefix('BattleScripting','bank')
 need(size==88 and [pokemon[k]['offset']for k in('species','ability','personality')]==[0,56,72],'完全BattlePokemon独立layout')
 need(battle['dynamicMoveType']==dict(offset=19,size=1),'BattleStruct全prefixからdynamic type19')
 need(new['skipCertainSwitchInAbilities']==dict(offset=356,bit=0,width_bits=1,type_size=1),'完全NewBattleStructからskip field/bit')
 need(scripting['bank']==dict(offset=23,size=1),'BattleScripting全prefixからbank23')
 return dict(battle_pokemon=dict(size=size,alignment=align,fields={k:pokemon[k]for k in('species','ability','personality')}),new_battle_struct=dict(size=newsize,alignment=newalign,skip=new['skipCertainSwitchInAbilities']),battle_struct=battle['dynamicMoveType'],battle_scripting=scripting['bank'],constants=constants,source_comments_used=False)

def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'source集合/immutable binder')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'固定公開source全文 '+name)
 text=sources['battle-assembly--data--battle_script_commands_table.s'].decode()
 pri,sec=text.split('gBattleScriptingCommandsTable2:\n')
 p=re.findall(r'^\.word\s+([^\s@]+)',pri.split('gBattleScriptingCommandsTable:\n')[1],re.M);s=re.findall(r'^\.word\s+([^\s@]+)',sec,re.M)
 need(len(p)==256 and p[255]=='atkFF_callsecondarytable'and s[41]=='atkFF29_trysetsleep','source登録FF/FF29')
 text=without_comments(sources['battle-battle_script_macros.s'].decode())
 need(re.search(r'\.macro\s+trysetsleep\s+bank\s+rom_address\s+\.byte\s+0xFF,\s*0x29\s+\.byte\s+\\bank\s+\.4byte\s+\\rom_address\s+\.endm',text)is not None,'独立FF29 script serializer')
 text=without_comments(sources['battle-src--new_bs_commands.c'].decode());need('gBattlescriptCurrInstr += 1;'in text and 'gBattleScriptingCommandsTable2[command]'in text and 'AbilityBattleEffects(ABILITYEFFECT_ABSORBING, bank, 0, 0, gCurrentMove)'in text,'dispatcher/handler正のcall意味')
 text=without_comments(sources['cfru-ability_battle_effects.c'].decode())
 for token in('u8 AbilityBattleEffects(u8 caseID, u8 bank, u16 ability, u16 special, u16 moveArg)','gLastUsedAbility = ABILITY(bank);','moveType = gBattleStruct->dynamicMoveType;','case ABILITYEFFECT_ABSORBING:','gBattleScripting.bank = bank;'):
  need(token in text,'source API/case3役割 '+token)
 defs=sources['cfru-src--defines_battle.h'].decode();need('#define ABILITY(bank) gBattleMons[bank].ability'in defs,'raw ability field source')
 for name,val,key in(('ABILITY_SERENEGRACE',32,'cfru-abilities.h'),('ABILITY_VOLTABSORB',10,'cfru-abilities.h'),('ABILITYEFFECT_ABSORBING',3,'cfru-include--battle_util.h'),('BS_GET_TARGET',0,'cfru-include--battle_script_commands.h')):
  values=re.findall(r'^#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+|\d+)\s*$',sources[key].decode(),re.M);need(len(values)==1 and int(values[0],0)==val,'独立有限入力scalar '+name)
 text=sources['cfru-src--battle_util.c'].decode();need(re.search(r'case BS_GET_TARGET:\s*ret = gBankTarget;\s*break;',text)is not None,'独立target selector consumer')
 text=without_comments(sources['stage72_ability_runtime.c'].decode())
 need(re.search(r'Stage72U8 Stage72_AbilityBattleEffects\(.*?\)\s*\{\s*Stage72U8 effect = Stage72_OriginalAbilityBattleEffects\(\s*caseId,\s*bank,\s*ability,\s*special,\s*moveArg\s*\);',text,re.S)is not None,'Stage72 wrapper全prefixの無条件same5引数')
 text=sources['stage72_hooks.S'].decode();need('STAGE72_R3_ENTRY Stage72_EntryAbilityBattleEffects, Stage72_AbilityBattleEffects'in text and 'STAGE72_JUMP_CONTINUATION 0x090B6689'in text,'Stage72公開original/continuation')
 text=sources['stage77_suppression.S'].decode();need('STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchAbilityBattleEffects, 0x0953410D, 0x0953417D'in text and 'lsls r3, r3, #5'in text and 'bpl 1f'in text,'Stage77 normal bit26 source')
 return source_layout(sources)

def fixed_parts():
 parts={i.address:encoded(i)for i in INS.values()}
 for a,v in WORDS.items():need(a not in parts,'code/data非重複');parts[a]=v.to_bytes(4,'little')
 return parts

def merge_parts(parts):
 out=[];start=end=None;data=b''
 for a,b in sorted(parts.items()):
  need(end is None or a>=end,'保護窓非重複')
  if a!=end:
   if start is not None:out.append(dict(address=start,**identity(data)))
   start=a;data=b''
  data+=b;end=a+len(b)
 if start is not None:out.append(dict(address=start,**identity(data)))
 return out
ALL_WINDOWS=FIXED_WINDOWS=merge_parts(fixed_parts())
WINDOWS={f'absorbing_ability_{i}':(r['address'],r['size'])for i,r in enumerate(ALL_WINDOWS)}

def bind_semantics(raw,sources=None):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'手書き完全命令再encode '+hex(i.address))
 for a,v in WORDS.items():need(d.u32(raw,a)==v,'実登録/literal/table '+hex(a))
 d.signed(raw,ALL_WINDOWS)
 return dict(instruction_count=len(INS),instruction_bytes=sum(i.size for i in INS.values()),data_fields=len(WORDS),observed_decoder_input_used=False)

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'吸収特性hitだけ')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=0x090B69A8,size=6),hit_address=hit,complete_instruction_fields=[dict(address=0x090B69A8,size=4,role='long_branch_to_ability_dispatch',covered_by_ability=32),dict(address=0x090B69AC,size=2,role='compare_ability_water_absorb',covered_by_ability=10)],input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HITS[0])),'全witness field一致');return 0x090B69A8,6

def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'immutable新scope窓');return copy.deepcopy(ALL_WINDOWS)

def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS];need(exact(selected,EXPECTED_HITS),'親unknown全field')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),windows=copy.deepcopy(ALL_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE))
prepare_review=make_review

def measure(raw):return [dict(address=w['address'],**identity(chunk(raw,w['address'],w['size'])))for w in ALL_WINDOWS]

def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profile'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'現候補/旧診断の分離')
 for key,value in(('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE)):need(exact(review[key],value),'review固定field '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS];need(exact(selected,EXPECTED_HITS)and exact(selected,review['hits']),'親unknown全fieldを保存')
 protected_windows(review);source=sources_bind(review,sources);semantics=bind_semantics(raw,sources);d.signed(raw,selected);composition=compose_selected(raw)
 e=evidence_template(HITS[0]);a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_ABSORBING_ABILITY',count=1,hits=list(HITS),source_layout=source,semantics=semantics,composition=composition,protected_windows=len(ALL_WINDOWS),protected_bytes=sum(w['size']for w in ALL_WINDOWS),**copy.deepcopy(CLAIMS))

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate');return _regions(raw,inherited,review,sources)
validate=_regions
