"""Flash実producerからbadge不足文の全文consumerへ結ぶ条件付き最小型。"""
import copy
import hashlib
import json
from pathlib import Path
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_choose_limit_roots as printer
import pr16_dex_hof_stock_limit_roots as stock
import pr16_dex_hof_menu_text as text
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_donor as d

need, identity, chunk = d.need, d.identity, d.chunk
ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = copy.deepcopy(printer.CANDIDATE)
HIT = 0x083DDEE1
KIND = 'rooted_jp_field_badge_minimum_text'
TEXT = dict(address=0x083DDEC6, size=30,
            sha256='d1742b432af18c29e00c6906a7e5bc67d80ab3ff45ceb28ee87d0c05ff61236c',
            text='あたらしい バッジを てにするまで\\nまだ つかえません[FC][09]')
ENDPOINT = 0x08120AF2
SPECS = {
 'field_callback_prefix': (0x08124F08, [
  ('push',240,True),('shift','lsl',0,0,24),('shift','lsr',6,0,24),('call',0x081104C0),
  ('literal',5,0x08124F74),('mem',True,'word',1,5,0),('shift','lsl',0,0,24),('shift','lsr',0,0,24),
  ('imm','add',1,15),('add',1,1,0),('mem',True,'byte',0,1,0),('imm','sub',0,18),
  ('shift','lsl',0,0,24),('shift','lsr',4,0,24),('imm','mov',0,5),('call',0x08071A70),
  ('literal',1,0x08124F78),('shift','lsl',0,4,3),('add',7,0,1),('mem',True,'word',0,7,0),
  ('imm','cmp',0,0),('branch',1,0x08124F3A),('jump',0x08125118),
  ('mem',True,'word',0,5,0),('imm','add',0,12),('call',0x081224B0),
  ('mem',True,'word',0,5,0),('imm','add',0,13),('call',0x081224B0),
  ('call',0x080C08D8),('shift','lsl',0,0,24),('shift','lsr',0,0,24),
  ('imm','cmp',0,1),('branch',0,0x08124F5E),('call',0x0811B914),('imm','cmp',0,1),('branch',1,0x08124F80)]),
 'badge_missing_to_message': (0x08124F80, [
  ('imm','cmp',4,6),('branch',8,0x08124FBC),('imm','mov',1,130),('shift','lsl',1,1,4),
  ('add',0,4,1),('call',0x0806DEC4),('shift','lsl',0,0,24),('shift','lsr',0,0,24),
  ('imm','cmp',0,1),('branch',0,0x08124FBC),('literal',0,0x08124FB0),('imm','mov',1,1),('call',0x08120AE8)]),
}
BLOCKS = {name: tuple(party.block(a, ops)) for name,(a,ops) in SPECS.items()}
# 既受入printer命令だけを同じ意味で再利用。ENTER/CFRU selector本体は含めない。
INS = {a:i for a,i in printer.INS.items() if a != 0x08124930 and a != 0x08124932 and not 0x09100000 <= a < 0x09200000}
for rows in BLOCKS.values():
 for i in rows: need(i.address not in INS, '新旧命令窓非重複'); INS[i.address] = i
DATA_FIELDS = [(a,n,v) for a,n,v in printer.DATA_FIELDS if a != 0x08124934 and not 0x09100000 <= a < 0x09200000]
DATA_FIELDS += [(0x08124F74,4,0x0203B010),(0x08124F78,4,0x08419F18),
                (0x08124FB0,4,TEXT['address']),(0x08419F18,4,0x080CACF9)]
EXTERNAL = tuple((a,b) for a,b in printer.EXTERNAL if a < 0x09000000) + (
 (0x08124F28,0x08071A70),(0x08124F3E,0x081224B0),(0x08124F46,0x081224B0),
 (0x08124F4A,0x080C08D8),(0x08124F56,0x0811B914),(0x08124F8A,0x0806DEC4))
CONTRACT = dict(
 profile_ja='先頭1匹の技slot0だけFlash148、他3slotはfield moveなし。非egg/非mail held item1、同task0。実4actions [0,18,3,2]からDown1とAでFlash18を選ぶ。',
 callback_ja='fieldMoveFuncは登録cellの非NULL確認だけ。本体はbadge拒否では呼ばない。link非active/UnionRoom外/FlagGet(0x820)の低byte0を有限条件とする。',
 printer_ja='有効window6/font2、text speed255、FC09待機の有限正常復帰1。全文30byteの通常glyph/newline/FC09 operand/EOSを実LDRBで読む。',
 abi_ja='各明示opaque siteは同期通常Thumb ABI復帰。r0-r3/r12/LRをUnknownへ破棄し、callee saved register/SP/保存stackと必要future-live RAMだけ保持。opaque effect自体や普遍IRQは未証明。',
 lifetime_ja='補助window2個の除去完了まで同party object epoch。window6/font資源は最後の読取まで有効。旧heap13352の保存前寿命・donor移管は別未完。',
 endpoint_ja='PartyMenuPrintTextからDisplayPartyMenuMessage内08120AF2への復帰で停止。後続API全体/全callback復帰は未実行。',
 right_ja='右先頭083DDEE4は現候補同identityの既存stock max3全27byte原本を再利用し、ENTER/旧max3 caseは再実行しない。')
CLAIMS = dict(conditional_finite_type_only=True, actual_runtime_execution_observed=False,
 full_story_reachability_claimed=False, opaque_callee_effects_proven=False,
 universal_heap_or_irq_lifetime_proven=False, indirect_reference_completeness_claimed=False,
 donor_eligible=False, donor_leased=False, formal_rom_changed=False, formal_save_changed=False)


def exact(a,b): return printer.exact(a,b)

def bind_callback(raw):
 for i in INS.values(): need(chunk(raw,i.address,i.size)==printer.encoded(i), '独立callback/printer意味 '+hex(i.address))
 for a,n,v in DATA_FIELDS: need(int.from_bytes(chunk(raw,a,n),'little')==v, '実literal/table幅 '+hex(a))
 encoded = printer.encode_text(TEXT['text'])
 need(identity(encoded)=={k:TEXT[k] for k in ('size','sha256')}, '独立日本語serializer identity')
 need(chunk(raw,TEXT['address'],TEXT['size'])==encoded, '現候補起点から全文30byte一致')
 need(encoded[-3:]==bytes((252,9,255)) and 255 not in encoded[:-1], 'FC09とEOS終端')
 return True


def _compose(raw, producer_machine, boundary_live=None, opaque_writes=None, epoch_events=None, contract=None):
 need(contract is None or exact(contract,CONTRACT), '固定条件付き契約')
 need(type(producer_machine.pc)is int and producer_machine.pc==0x08124F08 and type(producer_machine.reg[0])is int and producer_machine.reg[0]==0, '実producerから同taskのcallback入口')
 # producerの全RAM/register/stackを移し、text pointerはhostで設定しない。
 from pr16_dex_hof_jp_field_producer import INS as PRODUCER_INS
 instructions={**PRODUCER_INS, **INS}
 trace=[]; m=printer.Machine(raw,producer_machine.pc,memory=producer_machine.mem,instructions=instructions,trace=trace)
 m.reg=list(producer_machine.reg)
 object_pointer=m.read(0x0203B010,4)
 # window6の別資源条件。selectorはこれらを生産しないため明示inputである。
 for a,n,v in ((0x03003DD0,4,0x083E30E8),(0x03003E90,1,0)):
  rt.setmem(m.mem,a,n,v)
 trace.clear(); removed=0; boundaries=[]; groups={}; message_seen=False; function_seen=False
 while m.pc != ENDPOINT:
  if m.pc in instructions:
   if m.pc==0x08124F32:
    need(m.reg[7]==0x08419F18 and m.reg[4]==0,'producer選択から実Flash table index0');function_seen=True
   if m.pc==0x08124F9A:
    need((m.reg[0],m.reg[1])==(TEXT['address'],1),'実LDRが作る全文text/API引数');message_seen=True
   m.step();continue
  site=(m.reg[14]&~1)-4;target=m.pc;key=(site,target)
  need(key in EXTERNAL,'未証明callee/枝/間接dispatchを拒否 '+hex(site))
  value=rt.U;outputs=[];object_live=removed<2
  def put(a,n,v): m.write(a,n,v);outputs.append((a,n,v if rt.concrete(v)else 'unspecified'))
  if target==0x08071A70:need(m.reg[0]==5,'選択音ID5')
  elif target==0x081224B0:
   need(m.reg[0]==object_pointer+12+removed and removed<2,'同objectの補助window実引数')
   need(m.read(m.reg[0],1) in (0,1,255),'producerが定めた有効/未割当補助window条件')
   put(m.reg[0],1,255);removed+=1
  elif target in (0x080C08D8,0x0811B914):value=0
  elif target==0x0806DEC4:need(m.reg[0]==0x820,'実Flash badge flag0x820');value=0
  elif target==0x080F8908:value=255
  elif target==0x0800564C:value=1
  elif target==0x08006354:put(0x03003E60,1,rt.U)
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if boundary_live is not None:
   live=boundary_live[index];writes=(opaque_writes or {}).get(site,());event=(epoch_events or {}).get(site,{})
   need(set(event)<= {'freed','heap_reinitialized','window_invalidated'},'既知資源失効条件のみ')
   need(event.get('window_invalidated',False)is False,'最後のtext読取までwindow6有効')
   if object_live:need(event.get('heap_reinitialized',False)is False and object_pointer not in event.get('freed',()),'必要な同object epoch')
   for a,n,v in writes:
    need(type(a)is int and type(n)is int and type(v)is int and n>0 and 0<=a<a+n<=1<<32,'有限write')
    need(not any(a<b+z and b<a+n for b,z in live),'future-live RAMへのwrite拒否')
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   sig=(site,target,tuple(map(tuple,live)),tuple(outputs),value if rt.concrete(value)else None,object_live)
   groups[sig]=groups.get(sig,0)+1
  return_pc=m.reg[14]&~1
  for r in(0,1,2,3,12,14):m.reg[r]=rt.U
  m.reg[0]=value;m.pc=return_pc;m.flag_pc=None
 need(message_seen and function_seen and removed==2,'producer/cell/nonNULL/badge/APIを全通過')
 need(m.reads==[(TEXT['address']+j,1)for j in range(TEXT['size'])],'glyph/newline/FC09/EOS全文の実LDRB読取')
 return dict(steps=m.steps,reads=m.reads,trace=trace,boundaries=boundaries,groups=groups)


def compose_selected(raw, opaque_writes=None, epoch_events=None, contract=None):
 from pr16_dex_hof_jp_field_producer import compose_selected as producer, bind_semantics
 bind_semantics(raw);bind_callback(raw)
 known={s for s,_ in EXTERNAL}
 need(opaque_writes is None or type(opaque_writes)is dict,'write契約はNoneかdictだけ')
 need(epoch_events is None or type(epoch_events)is dict,'epoch契約はNoneかdictだけ')
 need(set(opaque_writes or {})<=known and set(epoch_events or {})<=known,'未実行siteを黙殺しない')
 for site,rows in (opaque_writes or {}).items():
  need(type(site)is int and type(rows)in(list,tuple),'write site/rows型')
  for row in rows:
   need(type(row)in(list,tuple) and len(row)==3 and all(type(x)is int for x in row),'write各3整数')
   a,n,value=row;need(n>0 and 0<=a<a+n<=1<<32,'有限write geometry')
 for site,event in (epoch_events or {}).items():
  need(type(site)is int and type(event)is dict and set(event)<= {'freed','heap_reinitialized','window_invalidated'},'epochの閉schema')
  for flag in ('heap_reinitialized','window_invalidated'):
   need(flag not in event or type(event[flag])is bool,'epoch flagはboolのみ')
  need('freed'not in event or type(event['freed'])is list and all(type(a)is int and 0<=a<1<<32 and a%4==0 for a in event['freed']),'Free先は整列整数list')
 pp, machine=producer(raw,return_machine=True)
 first=_compose(raw,machine,contract=contract)
 live=text.future_live(first['trace'],len(first['boundaries']))
 second=_compose(raw,machine,live,opaque_writes,epoch_events,contract)
 need(first['reads']==second['reads'] and first['boundaries']==second['boundaries'],'nonlive RAM消去後も全文同一')
 groups=[]
 for(site,target,fields,outputs,value,object_live),count in second['groups'].items():
  allbytes={a+j for a,n in fields for j in range(n)};made={a+j for a,n,_ in outputs for j in range(n)}
  groups.append(dict(site=site,target=target,count=count,required_fields=[dict(address=a,size=n)for a,n in text.coalesce(allbytes-made)],
   produced_memory_ranges=[dict(address=a,size=n)for a,n in text.coalesce(allbytes&made)],
   conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs],return_value=value if value is not None else 'unspecified',
   object_epoch_required=object_live,window6_epoch_required=True,normal_abi_return_required=True,effects_discharged=False))
 return dict(status='PASS_CONDITIONAL_ROOTED_FLASH_BADGE_TEXT',producer=pp,
  text_identity={k:TEXT[k]for k in('address','size','sha256')},text_read_bytes=30,
  read_trace_identity=identity(json.dumps(first['reads'],separators=(',',':')).encode()),
  callback_printer_steps=first['steps'],boundary_count=len(first['boundaries']),conditional_call_groups=groups,
  endpoint=ENDPOINT,field_function_called=False,text_pointer_host_seeded=False,
  all_fc09_eos_bytes_consumed=True,nonlive_ram_erased_at_each_boundary=True,
  synthetic_contract_execution=True,**CLAIMS)

REUSED = {
 'content/modernization/pr16_dex_hof_registered_boundary_batch_evidence/reference-chain.json':
  dict(size=97362,sha256='1918d7b42f9fe0a44bf11ecec37ebaffc9234a3369c7e801efe606a7939a344b'),
 'content/modernization/pr16_dex_hof_registered_boundary_batch_checkpoint.json':
  dict(size=101375,sha256='4d0c4108edcc85e109e44ea1f198dd8a717b7e3b902d603c3269b41d7fa1c0bf'),
 'content/modernization/pr16_dex_hof_stock_limit_roots_review.json':
  dict(size=13712,sha256='96af1a27e31c0e39aca3d4d4191caf7769d3240df5f9c840c7cf4b4d530e5bbc'),
 'content/modernization/pr16_dex_hof_jp_consumer_probe_evidence/measurement.json':
  dict(size=49671,sha256='c800071446877641d8745054163d5f67040dbfec5c442feb588c858cfc954436'),
 'content/modernization/pr16_dex_hof_party_takeitem_review.json':
  dict(size=44286,sha256='8b447bf029342589593928adb1888411802340df55184fe22de9ed77f4556238')}


def reused_right(raw,root=ROOT):
 rows={}
 for path,expected in REUSED.items():
  p=Path(root)/path;need(p.is_file() and not p.is_symlink(),'既存証拠regular file')
  b=p.read_bytes();need(identity(b)==expected,'旧原本の完全identity');rows[path]=json.loads(b)
 chain=rows[next(iter(REUSED))];cp=rows['content/modernization/pr16_dex_hof_registered_boundary_batch_checkpoint.json']
 need(chain['candidate']==cp['candidate']==CANDIDATE,'旧右text証拠も同0641')
 need(cp['delta_identity']==REUSED[next(iter(REUSED))],'原本cpからchain identityを束縛')
 proof=chain['proof']['data']['consumers'][stock.KIND]
 case=proof['composition']['cases'][1]
 need(case['maximum']==3 and case['complete_consumed_bytes']==27 and proof['composition']['all_two_eos_consumed']is True,'既受入右全27byteのpositive root')
 review=rows['content/modernization/pr16_dex_hof_stock_limit_roots_review.json']
 need(exact(review['texts'],stock.TEXTS),'旧独立serializerは不変')
 row=stock.TEXTS[0]
 need(row['address']==HIT+3 and identity(chunk(raw,row['address'],row['size']))=={k:row[k]for k in('size','sha256')},'右text全文現物identity')
 need(chunk(raw,row['address'],row['size'])==stock.encode_text(row['text']),'右日本語全文の独立serialize照合だけ')
 need(d.u32(raw,0x09169024)==row['address'],'旧max3登録pointerは同一')
 return dict(path=next(iter(REUSED)),identity=REUSED[next(iter(REUSED))],consumer=stock.KIND,maximum=3,
  complete_consumed_bytes=27,read_trace_identity=case['read_trace_identity'],table_cell=0x09169024,
  text_identity={k:row[k]for k in('address','size','sha256')},existing_execution_replayed=False)


def evidence_template():
 from pr16_dex_hof_jp_field_producer import ROOT as producer_root
 return dict(root_verified=True,root=copy.deepcopy(producer_root),
  classified_window=dict(address=HIT,size=4),
  boundary_parts=[dict(address=HIT,size=3,role='badge拒否文のFC09とEOS'),dict(address=HIT+3,size=1,role='既受入max3文先頭glyph')],
  left_text={k:TEXT[k]for k in('address','size','sha256')},
  right_text={k:stock.TEXTS[0][k]for k in('address','size','sha256')},
  reused_evidence=copy.deepcopy(REUSED),input_contract=copy.deepcopy(CONTRACT),
  message_call=0x08124F9A,text_byte_reader=0x0800580E,control_operand_reader=0x08005876,
  endpoint=ENDPOINT,complete_left_text_reads=True,right_existing_positive_case_reused=True,
  pointer_host_seeded=False,field_move_function_called=False,**copy.deepcopy(CLAIMS))


def witness_geometry(evidence):
 need(exact(evidence,evidence_template()),'閉じた独立最小型witness')
 return HIT,4


def bound_windows(raw):
 from pr16_dex_hof_jp_field_producer import WINDOWS as producer_windows
 ranges=set(producer_windows.values())
 ranges.update((i.address,i.size)for i in INS.values())
 ranges.update((a,n)for a,n,_ in DATA_FIELDS)
 ranges.update(((TEXT['address'],30),(stock.TEXTS[0]['address'],27),(0x09169024,4)))
 return [dict(address=a,**identity(chunk(raw,a,n)))for a,n in sorted(ranges)]


def _regions(raw,inherited,root=ROOT):
 from pr16_dex_hof_jp_field_producer import bind_semantics
 need(exact(inherited['candidate'],CANDIDATE) and type(inherited['classified'])is int and type(inherited['unclassified'])is int and (inherited['classified'],inherited['unclassified'])==(779,95),'正式779親からだけ')
 hits=[h for h in inherited['hits']if h['address']==HIT]
 need(len(hits)==1 and hits[0]['accepted']is False and hits[0]['classification']=='UNCLASSIFIED'
      and hits[0]['owner_candidates']==[] and type(hits[0]['size'])is int and hits[0]['size']==4
      and hits[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','唯一の4byte unknownのみ')
 d.signed(raw,hits[0]);bind_semantics(raw);bind_callback(raw)
 composition=compose_selected(raw);right=reused_right(raw,root)
 evidence=evidence_template();a,n=witness_geometry(evidence)
 return [d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_CONDITIONAL_JP_FIELD_TEXT_TYPE',
  hit=HIT,composition=composition,reused_right=right,protected_windows=bound_windows(raw),
  newly_classified=1,donor_safe_bytes=0,native_processes=0,old_full_rom_scan_runs=0,**copy.deepcopy(CLAIMS))


def regions(raw,inherited,root=ROOT):
 need(identity(raw)==CANDIDATE,'正式0641全ROM identity gate')
 return _regions(raw,inherited,root)


def source_manifest():
 from pr16_dex_hof_jp_field_producer import SOURCE_IDS
 out=copy.deepcopy(SOURCE_IDS);out.update(copy.deepcopy(stock.SOURCE_IDS))
 out['pret-party_menu.h']=dict(repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',source='src/data/party_menu.h',size=36157,
  sha256='cfd30a7b5fdc0026da999a62d3ff72159cad88d9a921730c179d804ee026a9f7',git_blob_sha='6b4ebc1f7c0c5f72eb28f656c31be10f86e02094')
 for row in out.values():
  row['source']=row.get('source',row.get('path'));row.pop('path',None);row.pop('local',None)
 return out


def sources_bind(sources):
 from pr16_dex_hof_jp_field_producer import SOURCE_IDS, sources_bind as producer_bind
 manifest=source_manifest();need(type(sources)is dict and set(sources)==set(manifest),'閉じた10source集合')
 for key,row in manifest.items():
  b=sources[key];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'固定公開source全文identity')
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'固定公開Git blob')
 producer_bind({k:sources[k]for k in SOURCE_IDS})
 stock.sources_bind(dict(source_bindings=stock.SOURCE_IDS),{k:sources[k]for k in stock.SOURCE_IDS})
 body=sources['pret-party_menu.c'].decode();header=sources['pret-party_menu.h'].decode()
 for token in ('sPartyMenuInternal->actions[Menu_GetCursorPos()] - CURSOR_OPTION_FIELD_MOVES',
  'sFieldMoveCursorCallbacks[fieldMove].fieldMoveFunc == NULL',
  'MenuHelpers_IsLinkActive() == TRUE || InUnionRoom() == TRUE',
  'fieldMove <= FIELD_MOVE_WATERFALL && FlagGet(FLAG_BADGE01_GET + fieldMove) != TRUE',
  'DisplayPartyMenuMessage(gText_CantUseUntilNewBadge, TRUE);'):
  need(token in body,'独立公開sourceのbadge拒否語義')
 for token in ('[CURSOR_OPTION_FIELD_MOVES + FIELD_MOVE_FLASH]', '[FIELD_MOVE_FLASH]        = {SetUpFieldMove_Flash,',
  '[FIELD_MOVE_WATERFALL]    = {SetUpFieldMove_Waterfall,'):
  need(token in header,'独立登録tableのFlash/HM順序')
 return True
