"""交換原文のFD03/FD02再帰・FC09 copyを有限な実Thumb意味で閉じる。

公開sourceの意味を固定し、既存event_text_rootsのFC/FD除外契約は変更しない。
本体への入口・CopyItemName出力・同期非再入は親が証明または明示する条件である。
"""
import copy
import hashlib
import json

import pr16_dex_hof_callback_party as party
import pr16_dex_hof_choose_limit_roots as printer
import pr16_dex_hof_donor as d
import pr16_dex_hof_menu_text as text
import pr16_dex_hof_runtime_party as rt

need, identity, chunk = d.need, d.identity, d.chunk
ENTRY, ENDPOINT = 0x08008B48, 0x08120D8C
VAR1, VAR2, VAR3, VAR4 = 0x02021C4C, 0x02021C60, 0x02021C74, 0x02021C88
# JPの隣接symbol geometryを上限にする。英語referenceのVAR1[32]を転用しない。
VARIABLE_CAPACITY, OUTPUT_CAPACITY = 20, 1000
TEXT = dict(address=0x083DE016, size=24,
            sha256='d5a7d3df2c8c59c7e85d5125c435550afc96daeb6b44b2cc5a22ea11a4ff3b49',
            text='{STR_VAR_2}を あずかって\\n{STR_VAR_1}を もたせました！[FC][09]')
EXAMPLE_STRINGS = {VAR1: 'ハイパーボール', VAR2: 'マスターボール'}
SPECS = {
 'expand_dispatch': (ENTRY, [
  ('push',48,True),('addi',4,0,0),('addi',5,1,0),
  ('mem',True,'byte',2,5,0),('imm','add',5,1),('addi',0,2,0),
  ('imm','sub',0,250),('imm','cmp',0,5),('branch',8,0x08008C22),
  ('shift','lsl',0,0,2),('literal',1,0x08008B64),('add',0,0,1),
  ('mem',True,'word',0,0,0),('movhi',15,0)]),
 'placeholder_recursive': (0x08008B80, [
  ('mem',True,'byte',0,5,0),('imm','add',5,1),('call',0x08008D5C),
  ('addi',1,0,0),('addi',0,4,0),('call',ENTRY),('addi',4,0,0),('jump',0x08008B4E)]),
 'extended_control_copy': (0x08008B94, [
  ('mem',False,'byte',2,4,0),('imm','add',4,1),('mem',True,'byte',2,5,0),
  ('imm','add',5,1),('mem',False,'byte',2,4,0),('imm','add',4,1),
  ('subi',0,2,4),('imm','cmp',0,20),('branch',8,0x08008C18),
  ('shift','lsl',0,0,2),('literal',1,0x08008BB0),('add',0,0,1),
  ('mem',True,'word',0,0,0),('movhi',15,0)]),
 'scalar_and_eos': (0x08008C22, [
  ('mem',False,'byte',2,4,0),('imm','add',4,1),('jump',0x08008B4E),
  ('imm','mov',0,255),('mem',False,'byte',0,4,0),('addi',0,4,0),
  ('pop',48,False),('pop',2,False),('bx',1)]),
 'variable1': (0x08008CA8, [('literal',0,0x08008CAC),('bx',14)]),
 'variable2': (0x08008CB0, [('literal',0,0x08008CB4),('bx',14)]),
 'placeholder_lookup': (0x08008D5C, [
  ('push',0,True),('imm','cmp',0,13),('branch',8,0x08008D74),
  ('literal',1,0x08008D70),('shift','lsl',0,0,2),('add',0,0,1),
  ('mem',True,'word',0,0,0),('call',0x081C7AC8),('jump',0x08008D76)]),
 'placeholder_lookup_return': (0x08008D76, [('pop',2,False),('bx',1)]),
 'placeholder_interwork': (0x081C7AC8, [('bx',0)]),
}
BLOCKS = {name: tuple(party.block(a,ops)) for name,(a,ops) in SPECS.items()}
INS = {i.address:i for rows in BLOCKS.values() for i in rows}
DATA_FIELDS = [
 (0x08008B64,4,0x08008B68),
 (0x08008B70,4,0x08008B94), # FC
 (0x08008B74,4,0x08008B80), # FD
 (0x08008B78,4,0x08008C22), # newline
 (0x08008B7C,4,0x08008C28), # EOS
 (0x08008BB0,4,0x08008BB4),
 (0x08008BC8,4,0x08008B4E), # FC09はoperandを追加copyせずloopへ
 (0x08008CAC,4,VAR1),(0x08008CB4,4,VAR2),
 (0x08008D70,4,0x081F1364),
 (0x081F136C,4,0x08008CA9),(0x081F1370,4,0x08008CB1),
]
encoded = printer.encoded
SOURCE_IDS = {
 'pret-string_util.c': dict(repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',source='src/string_util.c',
  size=14320,sha256='ed9519d4eaf51ed660a522915366dc0ebf2916d592a91a1d7fc2a012e4f3f17e',git_blob_sha='5c26d151a61274caac3a16c3b9c4eb73bf9a9e26'),
 'pret-characters.h': dict(repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',source='include/characters.h',
  size=12798,sha256='6787db76f83c4f8426c5adbfa7aa061c46585db9522f1fef00ad888616199b98',git_blob_sha='d00ecf0a3afcd9fc1fa9534c00f4b74793d5f06f'),
 'pret-charmap.txt': dict(repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',source='charmap.txt',
  size=21853,sha256='4da662317b3b5109a52064f9012d85b644d1dbf0f3f24243374aeef4cf25f061',git_blob_sha='b9d0ed9de00d05fc303bb987a5aa634b19009b47'),
 'cfru-charmap.tbl': copy.deepcopy(printer.SOURCE_IDS['cfru-charmap.tbl']),
}
for _row in SOURCE_IDS.values():
 _row.pop('local',None)
CONTRACT = dict(
 entry_ja='DisplaySwitchedHeldItemMessageの実BL08120D88直後を継承。r0=JP gStringVar4、r1=交換原文、LR=08120D8D。入口pointerを本関数で作らない。',
 variables_ja='CopyItemNameの条件付き出力はJP VAR1/2それぞれ20byte以内のglyphのみ＋EOS。実item名称の読み出し自体は本scope外。両bufferとstackへの同期非再入・非干渉を条件とする。',
 recursion_ja='原文FD03/FD02各1回だけを実GetExpandedPlaceholder tableと実calleeで解決し、同StringExpandPlaceholdersを再帰実行。変数内のFD/FC/他制御や未知byteは拒否。',
 output_ja='原文24byte全て、各placeholderのEOS込み全byteを実LDRBで読む。中間EOS2個は次の原文glyphで上書きされ、最終EOSはVAR4の1個だけとなる。',
 limit_ja='合成後EOSまで最大58byte。1000byte destination内で完結、元buffer/stackと非alias。描画・自然到達・全callback復帰・donor安全性は別scope。')


def encode_text(source=None):
 """公開serializerのSTR_VAR tokenだけを明示拡張。元serializerは変更しない。"""
 source=TEXT['text'] if source is None else source
 need(type(source)is str,'source textは文字列')
 out=bytearray()
 while source:
  token=next((t for t in ('{STR_VAR_1}','{STR_VAR_2}') if source.startswith(t)),None)
  if token:
   out.extend((253,2 if token=='{STR_VAR_1}' else 3));source=source[len(token):]
  else:
   pos=source.find('{STR_VAR_');part=source if pos<0 else source[:pos]
   need(bool(part),'未知placeholder tokenを拒否')
   out.extend(printer.encode_text(part)[:-1]);source=source[len(part):]
 out.append(255)
 return bytes(out)


def bind_semantics(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'交換展開の独立Thumb意味 '+hex(i.address))
 for a,n,value in DATA_FIELDS:need(int.from_bytes(chunk(raw,a,n),'little')==value,'展開literal/選択dispatch幅 '+hex(a))
 b=encode_text();need(identity(b)=={k:TEXT[k] for k in ('size','sha256')},'独立交換原文serializer identity')
 need(chunk(raw,TEXT['address'],TEXT['size'])==b,'交換原文全24byteの現物束縛')
 need(b[:2]==bytes((253,3)) and b[10:12]==bytes((253,2)) and b[-3:]==bytes((252,9,255)), '固定FD03/FD02/FC09/EOS境界')
 return True


def source_manifest():return copy.deepcopy(SOURCE_IDS)


def sources_bind(sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS),'展開sourceの閉じた固定集合')
 for key,row in SOURCE_IDS.items():
  b=sources[key];need(type(b)is bytes and identity(b)=={k:row[k] for k in ('size','sha256')},'固定公開source全文identity')
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'固定公開Git blob')
 body=sources['pret-string_util.c'].decode();chars=sources['pret-characters.h'].decode();charmap=sources['pret-charmap.txt'].decode()
 for token in ('expandedString = GetExpandedPlaceholder(placeholderId);','dest = StringExpandPlaceholders(dest, expandedString);',
               'case EXT_CTRL_CODE_BEGIN:', 'case 0x09:', '*dest = EOS;', 'return gStringVar1;', 'return gStringVar2;',
               '[PLACEHOLDER_ID_STRING_VAR_1] = ExpandPlaceholder_StringVar1,', '[PLACEHOLDER_ID_STRING_VAR_2] = ExpandPlaceholder_StringVar2,'):
  need(token in body,'公開再帰/copy/lookupの独立意味')
 for token in ('#define PLACEHOLDER_ID_STRING_VAR_1  0x2','#define PLACEHOLDER_ID_STRING_VAR_2  0x3'):
  need(token in chars,'公開placeholder ID')
 for token in ('STR_VAR_1      = FD 02','STR_VAR_2      = FD 03'):
  need(token in charmap,'公開serializer token')
 # Japanese glyph encodingは既存参加数textの固定CFRU charmapと同じ表。
 need(b'\\n' in sources['cfru-charmap.tbl'],'固定日本語charmap')
 return True


def _variable(mem,address):
 values=[]
 for offset in range(VARIABLE_CAPACITY):
  value=mem.get(address+offset,rt.U)
  need(type(value)is int and 0<=value<=255,'placeholder全読取byteが具体値')
  values.append(value)
  if value==255:return bytes(values)
  need(value<0xF7,'placeholderはglyphのみ。再帰controlの暗黙拡大を拒否')
 raise ValueError('placeholderのEOSがJP隣接symbol前に存在すること')


class Machine(text.Machine):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.input_reads=[];self.output_writes=[];self.recursive_calls=[]
 def read(self,a,n):
  value=super().read(a,n)
  if self.pc in (0x08008B4E,0x08008B80,0x08008B98):
   need(n==1 and type(value)is int,'展開の全LDRBが具体値')
   self.input_reads.append((self.pc,a,n))
  return value
 def write(self,a,n,value):
  if self.pc in (0x08008B94,0x08008B9C,0x08008C22,0x08008C2A):
   need(type(a)is int and VAR4<=a<VAR4+OUTPUT_CAPACITY and n==1 and type(value)is int,'展開destination内の具体byteだけ')
   self.output_writes.append((self.pc,a,n,value & 255))
  super().write(a,n,value)
 def step(self,*args,**kw):
  if self.pc==0x08008B8C:
   need(self.reg[1] in (VAR2,VAR1),'固定placeholder calleeの実返り値')
   self.recursive_calls.append((self.reg[1],self.reg[0]))
  return super().step(*args,**kw)


def expand_selected(raw,producer_machine,return_machine=False,contract=None):
 bind_semantics(raw)
 need(type(return_machine)is bool,'machine返却指定はbool')
 need(contract is None or printer.exact(contract,CONTRACT),'固定展開契約')
 p=producer_machine
 need(type(p.pc)is int and p.pc==ENTRY,'実BL直後の展開入口')
 need(all(type(p.reg[r])is int for r in (0,1,13,14)) and (p.reg[0],p.reg[1],p.reg[14])==(VAR4,TEXT['address'],ENDPOINT|1),'実callerの展開引数/LR')
 need(p.reg[13]%4==0 and 0x03000100<=p.reg[13]<=0x03008000,'有効非alias IWRAM stack')
 variables={a:_variable(p.mem,a) for a in (VAR1,VAR2)}
 m=Machine(raw,p.pc,memory=p.mem,instructions={**getattr(p,'instructions',{}),**INS},trace=getattr(p,'trace',[]))
 m.reg=list(p.reg);m.writes=list(p.writes);m.calls=list(p.calls);m.steps=p.steps;m.flags=p.flags;m.flag_pc=p.flag_pc
 m.reads=list(getattr(p,'reads',[]));start_steps=m.steps;start_sp=m.reg[13]
 while m.pc!=ENDPOINT:
  need(m.pc in INS,'展開の閉じた意味窓からのescapeを拒否')
  m.step();need(m.steps-start_steps<4096,'展開の有限命令上限')
 root_reads=[(a,n) for _,a,n in m.input_reads if TEXT['address']<=a<TEXT['address']+TEXT['size']]
 variable_reads={a:[(where,n) for _,where,n in m.input_reads if a<=where<a+VARIABLE_CAPACITY] for a in (VAR1,VAR2)}
 need(root_reads==[(TEXT['address']+j,1) for j in range(TEXT['size'])],'原文24byte/operand/EOSを順序どおり全読取')
 for a,b in variables.items():need(variable_reads[a]==[(a+j,1) for j in range(len(b))],'各placeholderのEOSを含む全読取')
 need(len(m.input_reads)==TEXT['size']+sum(map(len,variables.values())),'未帰属の余分なtext読取を拒否')
 original=encode_text()
 expected=variables[VAR2][:-1]+original[2:10]+variables[VAR1][:-1]+original[12:]
 need(len(expected)<=58 and expected[-1]==255 and 255 not in expected[:-1],'有限展開結果の唯一の最終EOS')
 output=bytes(rt.getmem(m.mem,VAR4+j,1) for j in range(len(expected)))
 need(output==expected,'実STRB出力が独立token連結と全文一致')
 need(m.reg[0]==VAR4+len(output)-1 and m.reg[13]==start_sp,'EOS位置の返り値とcaller stack復元')
 need(all(m.reg[r] is p.reg[r] or m.reg[r]==p.reg[r] for r in range(4,12)), 'callee-saved r4-r11を復元')
 need(m.recursive_calls==[(VAR2,VAR4),(VAR1,VAR4+len(variables[VAR2])-1+8)],'FD03/FD02順の実再帰callとdestination')
 for a,b in variables.items():need(bytes(rt.getmem(m.mem,a+j,1) for j in range(len(b)))==b,'placeholder入力を改変しない')
 eos_writes=[(a,n) for pc,a,n,value in m.output_writes if pc==0x08008C2A and value==255]
 need(eos_writes==[(VAR4+len(variables[VAR2])-1,1),(VAR4+len(variables[VAR2])-1+8+len(variables[VAR1])-1,1),(VAR4+len(output)-1,1)],'再帰EOS2個と最終EOSを分離')
 fc_writes=[(pc,a,n) for pc,a,n,_ in m.output_writes if pc in (0x08008B94,0x08008B9C)]
 need(fc_writes==[(0x08008B94,VAR4+len(output)-3,1),(0x08008B9C,VAR4+len(output)-2,1)],'FC09は2byteだけを実copy')
 def trace_identity(rows):return identity(json.dumps(rows,separators=(',',':')).encode())
 proof=dict(status='PASS_CONDITIONAL_ITEM_PLACEHOLDER_EXPANSION',entry=ENTRY,endpoint=ENDPOINT,steps=m.steps-start_steps,
  source_text={k:TEXT[k] for k in ('address','size','sha256')},source_read_trace=root_reads,source_read_trace_identity=trace_identity(root_reads),
  placeholder_reads=[dict(placeholder_id=pid,address=a,input_identity=identity(variables[a]),read_trace=variable_reads[a],
                         read_trace_identity=trace_identity(variable_reads[a]),eos_address=a+len(variables[a])-1) for pid,a in ((3,VAR2),(2,VAR1))],
  expanded_output=dict(address=VAR4,**identity(output),eos_address=m.reg[0],return_pointer=m.reg[0],final_eos_count=1),
  recursion_count=2,recursive_eos_writes=[dict(address=a,size=n) for a,n in eos_writes[:-1]],
  final_eos_write=dict(address=eos_writes[-1][0],size=1),fc09_copy_writes=[dict(instruction=pc,address=a,size=n) for pc,a,n in fc_writes],
  output_write_trace_identity=trace_identity(m.output_writes),all_source_bytes_read=True,all_placeholder_eos_read=True,
  source_pointer_host_seeded=False,placeholder_input_condition_only=True,actual_item_name_production_proven=False,
  printer_execution_proven=False,synthetic_contract_execution=True,actual_runtime_execution_observed=False,
  full_story_reachability_claimed=False,donor_eligible=False)
 return (proof,m) if return_machine else proof


def bound_windows(raw):
 ranges={(i.address,i.size) for i in INS.values()}|{(a,n) for a,n,_ in DATA_FIELDS}|{(TEXT['address'],TEXT['size'])}
 return [dict(address=a,**identity(chunk(raw,a,n))) for a,n in sorted(ranges)]
