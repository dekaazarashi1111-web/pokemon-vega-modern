"""交換原文FD再帰とmailbox拒否の別rootを全文readerへ結ぶ条件付き最小型。"""
import copy,hashlib,json
from pathlib import Path
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_choose_limit_roots as printer
import pr16_dex_hof_menu_text as text
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_donor as d
need,identity,chunk=d.need,d.identity,d.chunk
exact=printer.exact
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=copy.deepcopy(printer.CANDIDATE)
HIT=0x083DE02B
KIND='rooted_jp_item_exchange_mail_minimum_text'
ENDPOINT=0x08120AF2
LEFT=dict(address=0x083DE016,size=24,sha256='d5a7d3df2c8c59c7e85d5125c435550afc96daeb6b44b2cc5a22ea11a4ff3b49',text='{STR_VAR_2}を あずかって\\n{STR_VAR_1}を もたせました！[FC][09]')
RIGHT=dict(address=0x083DE02E,size=38,sha256='8bdd256110b1a1dd65ce82874e572d7e975f890595196fab3de96d77e2b678e9',text='すでに どうぐを もっているので\\nメールを もたせることが できません[FC][09]')
ITEM_NAMES={2:'ハイパーボール',1:'マスターボール'}
STR1,STR2,STR4=0x02021C4C,0x02021C60,0x02021C88
SPECS={
'exchange_message':(0x08120D48,[('push',112,True),('addi',4,0,0),('addi',5,1,0),('addi',6,2,0),('shift','lsl',4,4,16),('shift','lsr',4,4,16),('shift','lsl',5,5,16),('shift','lsr',5,5,16),('shift','lsl',6,6,24),('shift','lsr',6,6,24),('literal',0,0x08120DA0),('imm','mov',1,9),('signed_load','byte',1,0,1),('imm','mov',0,100),('alu','mul',0,1),('literal',1,0x08120DA4),('add',0,0,1),('addi',1,5,0),('addi',2,4,0),('call',0x081254C4),('literal',1,0x08120DA8),('addi',0,4,0),('call',0x08099898),('literal',1,0x08120DAC),('addi',0,5,0),('call',0x08099898),('literal',4,0x08120DB0),('literal',1,0x08120DB4),('addi',0,4,0),('call',0x08008B48),('addi',0,4,0),('addi',1,6,0),('call',0x08120AE8)]),
'mailbox_rejection':(0x08127D3C,[('push',112,True),('shift','lsl',0,0,24),('shift','lsr',6,0,24),('literal',0,0x08127D88),('imm','mov',1,9),('signed_load','byte',1,0,1),('imm','mov',0,100),('alu','mul',1,0),('literal',0,0x08127D8C),('add',5,1,0),('literal',1,0x08127D90),('imm','mov',0,0),('mem',False,'byte',0,1,0),('literal',2,0x08127D94),('literal',0,0x08127D98),('mem',True,'half',1,0,0),('imm','add',1,6),('mem',True,'half',0,0,2),('add',1,1,0),('shift','lsl',0,1,3),('add',0,0,1),('shift','lsl',0,0,2),('literal',1,0x08127D9C),('add',0,0,1),('mem',True,'word',1,2,0),('add',4,1,0),('addi',0,5,0),('imm','mov',1,12),('call',0x0803F354),('imm','cmp',0,0),('branch',0,0x08127DA4),('literal',0,0x08127DA0),('imm','mov',1,1),('call',0x08120AE8)])}
BLOCKS={n:tuple(party.block(a,ops))for n,(a,ops)in SPECS.items()}
INS={a:i for a,i in printer.INS.items()if a not in(0x08124930,0x08124932)and not 0x09100000<=a<0x09200000}
for rows in BLOCKS.values():
 for i in rows:need(i.address not in INS,'新旧命令非重複');INS[i.address]=i
DATA_FIELDS=[(a,n,v)for a,n,v in printer.DATA_FIELDS if a!=0x08124934 and not 0x09100000<=a<0x09200000]
DATA_FIELDS += [(0x08120DA0,4,0x0203B014),(0x08120DA4,4,0x020241E4),(0x08120DA8,4,STR1),(0x08120DAC,4,STR2),(0x08120DB0,4,STR4),(0x08120DB4,4,LEFT['address']), (0x08127D88,4,0x0203B014),(0x08127D8C,4,0x020241E4),(0x08127D90,4,0x0203B034),(0x08127D94,4,0x03005048),(0x08127D98,4,0x0203AA3C),(0x08127D9C,4,0x2CD0),(0x08127DA0,4,RIGHT['address'])]
EXTERNAL=tuple((a,b)for a,b in printer.EXTERNAL if a<0x09000000)+((0x08120D6E,0x081254C4),(0x08120D76,0x08099898),(0x08120D7E,0x08099898),(0x08127D74,0x0803F354))
CONTRACT=dict(
 root_ja='交換は登録前Task_SwitchItemsYesNoのtask0から実書込/RunTasks/Yes0/AddBagItem成功/新item2非mail。mailboxはChooseMonToGiveMailFromMailboxのaction7をconstructor/state20/同task/現hookで実選択する。自然到達は別義務。',
 names_ja='CopyItemNameの通常同期戻り条件はitem2→STR_VAR1のハイパーボール、item1→STR_VAR2のマスターボール。calleeの内部item table読取は本scopeの証明外。これらを自動生成された名前と主張しない。',
 expansion_ja='実DisplaySwitchedHeldItemMessageが原文083DE016とgStringVar4をBLへ渡す。FD03/FD02の実再帰、通常glyph/newline/FC09 copy/EOSを読み、原文と展開後RAMを別traceとする。',
 mailbox_ja='非eggかつheld item1の条件。manager cursor0/itemsAbove0/saveblock1 pointerの有限有効値からmail位置を計算するが、拒否枝ではmail本体を読取/変更しない。',
 abi_ja='各明示opaque siteは通常同期Thumb ABI復帰。r0-r3/r12/LR/flagsをUnknownへ破棄し、callee saved register/SP/saved stackと必要future-live RAMだけを保持。効果全体とIRQは未証明。',
 printer_ja='有効window6/font2/text speed255、printer開始時new/heldKeys0。FC09待機の正常戻り1を条件とし、展開後交換文とmailbox全38byteの実LDRBをEOSまで実行。',
 endpoint_ja='PartyMenuPrintTextからDisplayPartyMenuMessage内08120AF2へ戻った点で停止。API後半/各callback全体の正常復帰を主張しない。',
 lifetime_ja='同party object epochが最後の参照まで有効、window6/font/展開先RAMは最終text読取まで有効。heap13352/保存退避/donor移管は別gate。')
CLAIMS=dict(conditional_finite_type_only=True,actual_runtime_execution_observed=False,full_story_reachability_claimed=False,opaque_callee_effects_proven=False,universal_heap_or_irq_lifetime_proven=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False,formal_rom_changed=False,formal_save_changed=False)


def encode_left():
 parts=LEFT['text'].split('{STR_VAR_2}')
 need(len(parts)==2 and parts[0]=='','原文の先頭は独立STR_VAR2')
 middle=parts[1].split('{STR_VAR_1}')
 need(len(middle)==2,'原文の第二placeholderは独立STR_VAR1')
 return bytes((253,3))+printer.encode_text(middle[0])[:-1]+bytes((253,2))+printer.encode_text(middle[1])


def bind_callback(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==printer.encoded(i),'callback/printer意味 '+hex(i.address))
 for a,n,v in DATA_FIELDS:need(int.from_bytes(chunk(raw,a,n),'little')==v,'実literal/data幅 '+hex(a))
 for row,b in ((LEFT,encode_left()),(RIGHT,printer.encode_text(RIGHT['text']))):
  need(identity(b)=={k:row[k]for k in('size','sha256')},'独立日本語serializer全文identity')
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
 import pr16_dex_hof_jp_item_roots as roots
 import pr16_dex_hof_jp_item_expand as expand
 need(contract is None or exact(contract,CONTRACT),'固定条件契約')
 entry=0x08120D48 if lane=='exchange'else 0x08127D3C
 need(producer_machine.pc==entry,'同実producer入口')
 need((producer_machine.reg[0:3]==[2,1,1]if lane=='exchange'else producer_machine.reg[0]==0),'実producer API引数')
 instructions={**roots.INS,**INS};trace=[]
 m=printer.Machine(raw,entry,memory=producer_machine.mem,instructions=instructions,trace=trace);m.reg=list(producer_machine.reg)
 object_pointer=roots.HEAP
 for a,n,v in((0x03003DD0,4,0x083E30E8),(0x03003E90,1,0),(0x0300315C,2,0),(0x0300315E,2,0)):
  rt.setmem(m.mem,a,n,v)
 if lane=='mailbox':
  for a,n,v in((0x03005048,4,0x02025000),(0x0203AA3C,2,0),(0x0203AA3E,2,0)):
   rt.setmem(m.mem,a,n,v)
 trace.clear();boundaries=[];groups={};api_seen=False;expanded=None;copies=[]
 while m.pc!=ENDPOINT:
  need(m.steps<18000,'有限callback/printer命令予算')
  if m.pc==0x08008B48:
   need(lane=='exchange'and expanded is None and m.reg[0:2]==[STR4,LEFT['address']],'実BL原文/出力引数')
   expanded,after=expand.expand_selected(raw,m,return_machine=True)
   trace[:]=after.trace
   m=printer.Machine(raw,after.pc,memory=after.mem,instructions=instructions,trace=trace);m.reg=list(after.reg)
   m.steps=after.steps
   need(m.pc==0x08120D8C,'展開実復帰PC')
   continue
  if m.pc in instructions:
   if m.pc in(0x08120D90,0x08127D80):
    expected=STR4 if lane=='exchange'else RIGHT['address']
    need(m.reg[:2]==[expected,1],'実text/API引数keepOpen1');api_seen=True
   m.step();continue
  target=m.pc;site=(m.reg[14]&~1)-4;key=(site,target)
  need(key in EXTERNAL,'未証明callee/枝/dispatch拒否 '+hex(site))
  value=rt.U;outputs=[]
  def put(a,n,v):m.write(a,n,v);outputs.append((a,n,v if rt.concrete(v)else 'unspecified'))
  if target==0x081254C4:need(lane=='exchange'and m.reg[:3]==[0x020241E4,1,2],'交換questlog実引数')
  elif target==0x08099898:
   item,dest=m.reg[:2];expected=(2,STR1)if not copies else(1,STR2)
   need(lane=='exchange'and len(copies)<2 and(item,dest)==expected,'CopyItemNameの実item/dest')
   b=printer.encode_text(ITEM_NAMES[item]);need(0<len(b)<=20,'JP独立symbol間隔内の条件出力')
   for off,v in enumerate(b):put(dest+off,1,v)
   copies.append(dict(item=item,address=dest,**identity(b),callee_effect_proven=False))
  elif target==0x0803F354:need(lane=='mailbox'and m.reg[:2]==[0x020241E4,12],'実選択mon held item getter');value=1
  elif target==0x080F8908:value=255
  elif target==0x0800564C:value=1
  elif target==0x08006354:put(0x03003E60,1,rt.U)
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if boundary_live is not None:
   need(index<len(boundary_live),'同boundary数');live=boundary_live[index]
   event=(epoch_events or {}).get(site,{})
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
 need(api_seen,'実message BL通過')
 if lane=='exchange':
  expected=printer.encode_text(ITEM_NAMES[1]+'を あずかって\\n'+ITEM_NAMES[2]+'を もたせました！[FC][09]')
  address=STR4;need(expanded is not None and len(copies)==2,'2名前条件出力と実原文展開')
 else:expected=printer.encode_text(RIGHT['text']);address=RIGHT['address'];need(expanded is None and not copies,'mailboxは直接ROM text')
 need(m.reads==[(address+j,1)for j in range(len(expected))],'全文glyph/newline/FC09/EOSの実LDRB列')
 return dict(steps=m.steps,reads=m.reads,trace=trace,boundaries=boundaries,groups=groups,expansion=expanded,
  item_name_outputs=copies,printer_text=dict(address=address,**identity(expected)))


def compose_selected(raw,lane,opaque_writes=None,epoch_events=None,contract=None):
 import pr16_dex_hof_jp_item_roots as roots
 import pr16_dex_hof_jp_item_expand as expand
 need(type(lane)is str and lane in('exchange','mailbox'),'2独立rootだけ')
 validate_effects(opaque_writes,epoch_events);roots.bind_semantics(raw);bind_callback(raw);expand.bind_semantics(raw)
 pp,machine=roots.compose_selected(raw,lane=lane,return_machine=True)
 first=_compose(raw,lane,machine,contract=contract)
 live=text.future_live(first['trace'],len(first['boundaries']))
 second=_compose(raw,lane,machine,live,opaque_writes,epoch_events,contract)
 need(first['reads']==second['reads']and first['boundaries']==second['boundaries']and exact(first['expansion'],second['expansion']),'nonlive RAM消去後全文と展開一致')
 executed={s for s,_ in first['boundaries']};need(set(opaque_writes or {})<=executed and set(epoch_events or {})<=executed,'別lane未実行siteを黙殺しない')
 groups=[]
 for(site,target,fields,outputs,value),count in second['groups'].items():
  allbytes={a+j for a,n in fields for j in range(n)};made={a+j for a,n,_ in outputs for j in range(n)}
  groups.append(dict(site=site,target=target,count=count,required_fields=[dict(address=a,size=n)for a,n in text.coalesce(allbytes-made)],produced_memory_ranges=[dict(address=a,size=n)for a,n in text.coalesce(allbytes&made)],conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs],return_value=value if value is not None else 'unspecified',normal_abi_return_required=True,effects_discharged=False))
 return dict(status='PASS_CONDITIONAL_ROOTED_JP_ITEM_TEXT',lane=lane,producer=pp,expansion=first['expansion'],item_name_outputs=first['item_name_outputs'],printer_text=first['printer_text'],text_read_bytes=len(first['reads']),read_trace_identity=identity(json.dumps(first['reads'],separators=(',',':')).encode()),callback_printer_steps=first['steps'],boundary_count=len(first['boundaries']),conditional_call_groups=groups,endpoint=ENDPOINT,text_pointer_host_seeded=False,all_fc09_eos_bytes_consumed=True,nonlive_ram_erased_at_each_boundary=True,synthetic_contract_execution=True,**CLAIMS)


def evidence_template():
 return dict(root_verified=True,root_scope='two_separate_registered_conditional_item_roots',classified_window=dict(address=HIT,size=4),boundary_parts=[dict(address=HIT,size=3,role='交換原文FC09とEOS'),dict(address=HIT+3,size=1,role='mailbox拒否文先頭glyph')],left_text={k:LEFT[k]for k in('address','size','sha256')},right_text={k:RIGHT[k]for k in('address','size','sha256')},exchange_entry=0x081240D8,exchange_message=0x08120D48,mailbox_entry=0x08127D10,mailbox_callback=0x08127D3C,expand_entry=0x08008B48,text_byte_reader=0x0800580E,control_operand_reader=0x08005876,endpoint=ENDPOINT,input_contract=copy.deepcopy(CONTRACT),complete_original_and_expanded_reads=True,pointer_host_seeded=False,**copy.deepcopy(CLAIMS))


def strict_equal(a,b):
 if type(a)is not type(b):return False
 if type(a)is dict:return set(a)==set(b)and all(strict_equal(a[k],b[k])for k in a)
 if type(a)is list:return len(a)==len(b)and all(strict_equal(x,y)for x,y in zip(a,b))
 return type(a)in(str,int,bool,type(None))and a==b


def witness_geometry(evidence):
 need(strict_equal(evidence,evidence_template()),'閉じた独立型厳密witness');return HIT,4


def bound_windows(raw):
 import pr16_dex_hof_jp_item_roots as roots
 import pr16_dex_hof_jp_item_expand as expand
 ranges={(i.address,i.size)for i in INS.values()}
 ranges.update((a,n)for a,n,_ in DATA_FIELDS)
 ranges.update((i.address,i.size)for i in roots.INS.values())
 ranges.update(roots.WINDOWS.values())
 ranges.update((i.address,i.size)for i in expand.INS.values())
 ranges.update((a,n)for a,n,_ in expand.DATA_FIELDS)
 ranges.update(((LEFT['address'],LEFT['size']),(RIGHT['address'],RIGHT['size'])))
 return[dict(address=a,**identity(chunk(raw,a,n)))for a,n in sorted(ranges)]


def _regions(raw,inherited):
 need(exact(inherited['candidate'],CANDIDATE)and type(inherited['classified'])is int and type(inherited['unclassified'])is int and(inherited['classified'],inherited['unclassified'])==(780,94),'正式780親からだけ')
 hits=[h for h in inherited['hits']if h['address']==HIT]
 need(len(hits)==1 and hits[0]['accepted']is False and hits[0]['classification']=='UNCLASSIFIED'and hits[0]['owner_candidates']==[]and type(hits[0]['size'])is int and hits[0]['size']==4 and hits[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','唯一4byte unknownだけ')
 d.signed(raw,hits[0]);cases=[compose_selected(raw,lane)for lane in('exchange','mailbox')]
 evidence=evidence_template();a,n=witness_geometry(evidence)
 return[d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_CONDITIONAL_JP_ITEM_TEXT_TYPE',hit=HIT,cases=cases,protected_windows=bound_windows(raw),newly_classified=1,donor_safe_bytes=0,native_processes=0,old_full_rom_scan_runs=0,**copy.deepcopy(CLAIMS))


def regions(raw,inherited):
 need(identity(raw)==CANDIDATE,'正式0641全ROM identity gate');return _regions(raw,inherited)


def source_manifest():
 import pr16_dex_hof_jp_item_roots as roots
 import pr16_dex_hof_jp_item_expand as expand
 out=roots.source_manifest()
 for name,row in printer.SOURCE_IDS.items():
  if name not in('cfru-charmap.tbl','cfru-string.py','pret-text.c'):continue
  row=copy.deepcopy(row);row.pop('local',None);out[name]=row
 out.update(expand.source_manifest())
 for row in out.values():
  row['source']=row.get('source',row.get('path'));row.pop('path',None);row.pop('local',None)
 return out


def sources_bind(sources):
 import pr16_dex_hof_jp_item_roots as roots
 import pr16_dex_hof_jp_item_expand as expand
 manifest=source_manifest();need(type(sources)is dict and set(sources)==set(manifest),'全固定source集合')
 for name,row in manifest.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'固定source全文identity')
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'固定Git blob')
 roots.sources_bind({k:sources[k]for k in roots.source_manifest()})
 expand.sources_bind({k:sources[k]for k in expand.source_manifest()})
 body=sources['pret-party_menu.c'].decode()
 for token in('CopyItemName(item, gStringVar1);','CopyItemName(item2, gStringVar2);','StringExpandPlaceholders(gStringVar4, gText_SwitchedPkmnItem);','DisplayPartyMenuMessage(gText_PkmnHoldingItemCantHoldMail, TRUE);'):
  need(token in body,'固定sourceの交換/mailbox本文語義')
 return True
