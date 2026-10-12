"""参加拒否/取消の別実rootから21/12byte全文readerへ結ぶ条件付き最小型。"""
import copy,hashlib,json
from pathlib import Path
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_choose_limit_roots as printer
import pr16_dex_hof_menu_text as text
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_donor as d
need,identity,chunk=d.need,d.identity,d.chunk
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=copy.deepcopy(printer.CANDIDATE)
HIT=0x083DE6AB
KIND='rooted_jp_minigame_reject_cancel_minimum_text'
ENDPOINT=0x08120AF2
LEFT=dict(address=0x083DE699,size=21,sha256='af1310174d2d1c809a29cbfb81006855f9da9faa28f939d9077dd5ff40b6504a',text='その ポケモンは さんか できません[FC][09]')
RIGHT=dict(address=0x083DE6AE,size=12,sha256='cd57ad789c2cc627a53253e8615b240a2ca676303872eb3294a0dca271df8e41',text='さんかを やめますか？')
SPECS={
 'read_produced_minigame_flag':(0x081211C4,[('push',0,True),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('literal',1,0x081211E0),('imm','mov',2,14),('signed_load','half',1,1,2),('register_asr',1,0),('imm','mov',0,1),('alu','and',1,0),('imm','cmp',1,0),('branch',1,0x081211DC),('imm','mov',0,0),('pop',2,False),('bx',1)]),
 'entry_callback':(0x081211E4,[('push',48,True),('shift','lsl',0,0,24),('shift','lsr',4,0,24),('shift','lsl',1,1,24),('shift','lsr',5,1,24),('addi',0,5,0),('call',0x081211C4),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',1,0x08121214)]),
 'entry_rejected':(0x08121214,[('imm','mov',0,26),('call',0x08071A70),('literal',0,0x0812123C),('imm','mov',1,0),('call',0x08120AE8)]),
 'cancel_callback':(0x08121248,[('push',16,True),('addi',4,0,0),('shift','lsl',4,4,24),('shift','lsr',4,4,24),('literal',0,0x08121274),('imm','mov',1,1),('call',0x08120AE8)])}
BLOCKS={n:tuple(party.block(a,ops))for n,(a,ops)in SPECS.items()}
INS={a:i for a,i in printer.INS.items()if a not in(0x08124930,0x08124932)and not 0x09100000<=a<0x09200000}
for rows in BLOCKS.values():
 for i in rows:need(i.address not in INS,'新旧命令非重複');INS[i.address]=i
DATA_FIELDS=[(a,n,v)for a,n,v in printer.DATA_FIELDS if a!=0x08124934 and not 0x09100000<=a<0x09200000]
DATA_FIELDS += [(0x081211E0,4,0x0203B014),(0x0812123C,4,LEFT['address']),(0x08121274,4,RIGHT['address'])]
EXTERNAL=tuple((a,b)for a,b in printer.EXTERNAL if a<0x09000000)+((0x08121216,0x08071A70),)
CONTRACT=dict(
 root_ja='ChooseMonForWirelessMinigameのmenuType11/action13。state6でmode1/partyCount1/非egg・非Dodrioから実生成したminigameBitflag0を同task0/slot0に保持する。entryはaction13 cell、cancelはBと別hook09097AB4から入る。',
 reject_ja='081211C4が同producerの0203B022を実LDRSHしslot0で算術右shift/bit0を読む。拒否枝のPlaySE26正常戻り後、実literal083DE699をkeepOpen0で渡す。getter条件自体や自然root到達は未証明。',
 cancel_ja='B入力のHandleChooseMonCancelから別hook/stock action13を経る。実literal083DE6AEをkeepOpen1で渡す。右起点を旧候補083DE6B0へ置換しない。',
 abi_ja='各明示opaque siteは通常同期Thumb ABI復帰。r0-r3/r12/LR/flagsをUnknownへ破棄し、callee saved register/SP/saved stackと必要future-live RAMだけを保持。全callee効果とIRQは未証明。',
 printer_ja='有効window6/font2/text speed255、printer開始時new/heldKeys0。左FC09待機の正常戻り1を条件とし、左21byte/右12byteを実LDRBで各EOSまで読む。text pointerはhostで設定しない。',
 endpoint_ja='PartyMenuPrintTextからDisplayPartyMenuMessage内08120AF2へ戻った点で停止。API後半/各callback全体の正常復帰は主張しない。',
 lifetime_ja='同party object epochが必要読取まで有効、window6/fontは最終text読取まで有効。heap13352/保存退避/donor移管は別gate。')
CLAIMS=dict(conditional_finite_type_only=True,actual_runtime_execution_observed=False,full_story_reachability_claimed=False,opaque_callee_effects_proven=False,universal_heap_or_irq_lifetime_proven=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False,formal_rom_changed=False,formal_save_changed=False)


def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is dict:return all(type(k)is str for k in a)and set(a)==set(b)and all(exact(a[k],b[k])for k in a)
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 return type(a)in(str,int,bool,type(None))and a==b


def encoded(i):
 if i.kind=='register_asr':return (0x4100|(i.args[1]<<3)|i.args[0]).to_bytes(2,'little')
 return printer.encoded(i)


class Machine(printer.Machine):
 def step(self,*args,**kw):
  i=self.instructions[self.pc]
  if i.kind=='register_asr':
   rd,rs=i.args;v,n=self.reg[rd],self.reg[rs]
   if rt.concrete(v)and rt.concrete(n):
    n=n&255;v=v if v<1<<31 else v-(1<<32);self.reg[rd]=(v>>min(n,32))&rt.MASK
   else:self.reg[rd]=rt.U
   self.pc+=2;self.steps+=1;self.flags=(rt.U,)*4;self.flag_pc=None;return
  return super().step(*args,**kw)


def bind_callback(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'callback/printer意味 '+hex(i.address))
 for a,n,v in DATA_FIELDS:need(int.from_bytes(chunk(raw,a,n),'little')==v,'実literal/data幅 '+hex(a))
 for row in(LEFT,RIGHT):
  b=printer.encode_text(row['text']);need(identity(b)=={k:row[k]for k in('size','sha256')},'独立日本語serializer全文identity')
  need(chunk(raw,row['address'],row['size'])==b,'全文byte束縛')
 return True


def validate_effects(opaque_writes,epoch_events):
 known={s for s,_ in EXTERNAL}
 for mapping in(opaque_writes,epoch_events):
  need(mapping is None or type(mapping)is dict,'境界mapはNone/dict')
  need(all(type(k)is int and k in known for k in(mapping or {})),'既知実行site整数のみ')
 for rows in(opaque_writes or {}).values():
  need(type(rows)in(list,tuple),'write rows型')
  for row in rows:
   need(type(row)in(list,tuple)and len(row)==3 and all(type(x)is int for x in row),'write3整数')
   a,n,v=row;need(0<n<=4096 and 0<=a<a+n<=1<<32 and 0<=v<1<<(8*n),'write幅/値')
 for event in(epoch_events or {}).values():
  need(type(event)is dict and set(event)<= {'freed','heap_reinitialized','window_invalidated'},'閉epoch schema')
  need(all(type(event[k])is bool for k in('heap_reinitialized','window_invalidated')if k in event),'epoch bool')
  need('freed'not in event or type(event['freed'])is list and all(type(a)is int and 0<=a<1<<32 and a%4==0 for a in event['freed']),'Free整列住所list')


def _compose(raw,lane,producer_machine,boundary_live=None,opaque_writes=None,epoch_events=None,contract=None):
 import pr16_dex_hof_jp_minigame_roots as roots
 need(contract is None or exact(contract,CONTRACT),'固定条件契約')
 need(producer_machine.pc==roots.ENDPOINTS[lane],'同実producer入口')
 need(producer_machine.reg[0]==0 and(lane=='cancel'or producer_machine.reg[1]==0),'実producer task/slot引数')
 instructions={**roots.INS,**INS};trace=[]
 m=Machine(raw,producer_machine.pc,memory=producer_machine.mem,instructions=instructions,trace=trace);m.reg=list(producer_machine.reg)
 object_pointer=m.read(roots.HEAP,4)
 need(type(object_pointer)is int and object_pointer==roots.runtime.ROOT+roots.runtime.HEADER,'実producerから同allocation pointerを取得')
 for a,n,v in((0x03003DD0,4,0x083E30E8),(0x03003E90,1,0),(0x0300315C,2,0),(0x0300315E,2,0)):
  rt.setmem(m.mem,a,n,v)
 trace.clear();boundaries=[];groups={};api_seen=False;flag_read=False
 row=LEFT if lane=='entry'else RIGHT
 while m.pc!=ENDPOINT:
  need(m.steps<18000,'有限callback/printer命令予算')
  if m.pc in instructions:
   if m.pc==0x081211CE:
    need(lane=='entry'and m.reg[1:3]==[0x0203B014,14]and m.read(0x0203B022,2)==0,'state6実生成flag0の同RAM読取');flag_read=True
   if m.pc in(0x0812121E,0x08121254):
    need(m.reg[:2]==[row['address'],0 if lane=='entry'else 1],'実text/API引数keepOpen0/1');api_seen=True
   m.step();continue
  target=m.pc;site=(m.reg[14]&~1)-4;key=(site,target)
  need(key in EXTERNAL,'未証明callee/枝/dispatch拒否 '+hex(site))
  value=rt.U;outputs=[]
  def put(a,n,v):m.write(a,n,v);outputs.append((a,n,v if rt.concrete(v)else 'unspecified'))
  if target==0x08071A70:need(lane=='entry'and m.reg[0]==26,'拒否音ID26')
  elif target==0x080F8908:value=255
  elif target==0x0800564C:value=1
  elif target==0x08006354:put(0x03003E60,1,rt.U)
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if boundary_live is not None:
   need(index<len(boundary_live),'同boundary数');live=boundary_live[index];event=(epoch_events or {}).get(site,{})
   need(event.get('window_invalidated',False)is False,'window6最後まで有効')
   need(event.get('heap_reinitialized',False)is False and object_pointer not in event.get('freed',()),'本scopeの同object epoch')
   for a,n,v in(opaque_writes or {}).get(site,()):
    need(not any(a<b+z and b<a+n for b,z in live),'future-live RAMへのwrite拒否')
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   sig=(site,target,tuple(map(tuple,live)),tuple(outputs),value if rt.concrete(value)else None)
   groups[sig]=groups.get(sig,0)+1
  return_pc=m.reg[14]&~1
  for r in(0,1,2,3,12,14):m.reg[r]=rt.U
  m.reg[0]=value;m.pc=return_pc;m.flags=(rt.U,)*4;m.flag_pc=None
 need(api_seen and flag_read==(lane=='entry'),'実message BL/必要flag reader通過')
 need(m.reads==[(row['address']+j,1)for j in range(row['size'])],'全文glyph/左FC09/各EOSの実LDRB列')
 return dict(steps=m.steps,reads=m.reads,trace=trace,boundaries=boundaries,groups=groups,flag_read=flag_read)


def compose_selected(raw,lane,opaque_writes=None,epoch_events=None,contract=None):
 import pr16_dex_hof_jp_minigame_roots as roots
 need(type(lane)is str and lane in('entry','cancel'),'2独立経路だけ')
 validate_effects(opaque_writes,epoch_events);roots.bind_semantics(raw);bind_callback(raw)
 pp,machine=roots.compose_selected(raw,lane=lane,return_machine=True)
 first=_compose(raw,lane,machine,contract=contract)
 live=text.future_live(first['trace'],len(first['boundaries']))
 second=_compose(raw,lane,machine,live,opaque_writes,epoch_events,contract)
 need(first['reads']==second['reads']and first['boundaries']==second['boundaries'],'nonlive RAM消去後全文一致')
 executed={s for s,_ in first['boundaries']};need(set(opaque_writes or {})<=executed and set(epoch_events or {})<=executed,'別lane未実行siteを黙殺しない')
 groups=[]
 for(site,target,fields,outputs,value),count in second['groups'].items():
  allbytes={a+j for a,n in fields for j in range(n)};made={a+j for a,n,_ in outputs for j in range(n)}
  groups.append(dict(site=site,target=target,count=count,required_fields=[dict(address=a,size=n)for a,n in text.coalesce(allbytes-made)],produced_memory_ranges=[dict(address=a,size=n)for a,n in text.coalesce(allbytes&made)],conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs],return_value=value if value is not None else 'unspecified',normal_abi_return_required=True,effects_discharged=False))
 row=LEFT if lane=='entry'else RIGHT
 return dict(status='PASS_CONDITIONAL_ROOTED_JP_MINIGAME_TEXT',lane=lane,producer=pp,printer_text={k:row[k]for k in('address','size','sha256')},text_read_bytes=row['size'],read_trace_identity=identity(json.dumps(first['reads'],separators=(',',':')).encode()),callback_printer_steps=first['steps'],boundary_count=len(first['boundaries']),conditional_call_groups=groups,endpoint=ENDPOINT,text_pointer_host_seeded=False,produced_flag_read=first['flag_read'],keep_open=0 if lane=='entry'else 1,all_text_eos_bytes_consumed=True,nonlive_ram_erased_at_each_boundary=True,synthetic_contract_execution=True,**CLAIMS)


def evidence_template():
 return dict(root_verified=True,root_scope='registered_minigame_entry_and_cancel_conditional_roots',classified_window=dict(address=HIT,size=4),boundary_parts=[dict(address=HIT,size=3,role='参加拒否文FC09とEOS'),dict(address=HIT+3,size=1,role='取消文先頭glyph')],left_text={k:LEFT[k]for k in('address','size','sha256')},right_text={k:RIGHT[k]for k in('address','size','sha256')},entry=0x081281C0,setup_producer=0x081210D4,produced_flag_cell=0x0203B022,flag_reader=0x081211C4,reject_callback=0x081211E4,reject_message_call=0x0812121E,cancel_hook=0x09097AB4,cancel_callback=0x08121248,cancel_message_call=0x08121254,text_byte_reader=0x0800580E,control_operand_reader=0x08005876,endpoint=ENDPOINT,input_contract=copy.deepcopy(CONTRACT),complete_both_text_reads=True,pointer_host_seeded=False,**copy.deepcopy(CLAIMS))


def witness_geometry(evidence):
 need(exact(evidence,evidence_template()),'閉じた独立型厳密witness');return HIT,4


def bound_windows(raw):
 import pr16_dex_hof_jp_minigame_roots as roots
 ranges={(i.address,i.size)for i in INS.values()};ranges.update((a,n)for a,n,_ in DATA_FIELDS)
 ranges.update((i.address,i.size)for i in roots.INS.values());ranges.update(roots.WINDOWS.values())
 ranges.update(((LEFT['address'],LEFT['size']),(RIGHT['address'],RIGHT['size'])))
 return[dict(address=a,**identity(chunk(raw,a,n)))for a,n in sorted(ranges)]


def _regions(raw,inherited):
 need(exact(inherited['candidate'],CANDIDATE)and type(inherited['classified'])is int and type(inherited['unclassified'])is int and(inherited['classified'],inherited['unclassified'])==(781,93),'正式781親からだけ')
 hits=[h for h in inherited['hits']if h['address']==HIT]
 need(len(hits)==1 and hits[0]['accepted']is False and hits[0]['classification']=='UNCLASSIFIED'and hits[0]['owner_candidates']==[]and type(hits[0]['size'])is int and hits[0]['size']==4 and hits[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','唯一4byte unknownだけ')
 d.signed(raw,hits[0]);cases=[compose_selected(raw,lane)for lane in('entry','cancel')]
 evidence=evidence_template();a,n=witness_geometry(evidence)
 return[d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_CONDITIONAL_JP_MINIGAME_TEXT_TYPE',hit=HIT,cases=cases,protected_windows=bound_windows(raw),newly_classified=1,donor_safe_bytes=0,native_processes=0,old_full_rom_scan_runs=0,**copy.deepcopy(CLAIMS))


def regions(raw,inherited):
 need(identity(raw)==CANDIDATE,'正式0641全ROM identity gate');return _regions(raw,inherited)


def source_manifest():
 import pr16_dex_hof_jp_minigame_roots as roots
 out=roots.source_manifest()
 for name,row in printer.SOURCE_IDS.items():
  if name not in('cfru-charmap.tbl','cfru-string.py','pret-text.c'):continue
  row=copy.deepcopy(row);row.pop('local',None);out[name]=row
 for row in out.values():
  row['source']=row.get('source',row.get('path'));row.pop('path',None);row.pop('local',None)
 return out


def sources_bind(sources):
 import pr16_dex_hof_jp_minigame_roots as roots
 manifest=source_manifest();need(type(sources)is dict and set(sources)==set(manifest),'全固定source集合')
 for name,row in manifest.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'固定source全文identity')
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'固定Git blob')
 roots.sources_bind({k:sources[k]for k in roots.source_manifest()})
 body=sources['pret-party_menu.c'].decode()
 for token in('static bool8 IsMonAllowedInMinigame(u8 slot)','if (!((gPartyMenu.minigameBitflag >> slot) & 1))','DisplayPartyMenuMessage(gText_PkmnCantParticipate, FALSE);','DisplayPartyMenuMessage(gText_CancelParticipation, TRUE);'):
  need(token in body,'固定sourceの拒否/取消本文語義')
 return True
