"""special057の実task/main/state producerからCurrent/Max15byteへの有限text consumer。"""
import ast,copy,hashlib,json,re
import pr16_dex_hof_callback_party as p
import pr16_dex_hof_callback_party_task as task
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as live
import pr16_dex_hof_field_text_roots as field
import pr16_dex_hof_minigame_text_roots as mini
import pr16_dex_hof_animation_registered_roots as machine
import pr16_dex_hof_critical_move_list_roots as critical
import pr16_dex_hof_toxic_orb_roots as layout
import pr16_dex_hof_donor as d
from pr16_dex_hof_extra_roots import encoded,exact
need,identity,chunk=p.need,p.identity,p.chunk
CANDIDATE,DIAGNOSTIC=p.CANDIDATE,p.DIAGNOSTIC
HIT=0x0914100D
HITS=CLASSIFIED_HITS=TARGET_HITS=(HIT,)
KIND='registered_frontier_records_minimum_text_consumption'
TYPE_CATEGORY='data'
MAIN,TASKS,CELL,ALLOC,TILEMAP=0x03003130,0x030050D0,0x0203DFB0,0x02010000,0x02011000
STATE=MAIN+0x438
ENTRY,TASK,CB,PRINT,STOP=0x0910412C,0x0910363C,0x09103E5C,0x091037D8,0xFFFFFFF0
TARGETS=(0x09141006,0x09141010)
SPECS=[]
def block(a,specs):
 for k,*x in specs:
  if k=='regmem'and type(x[0])is bool:
   ld,w,rd,rb,ro=x;x=[{(True,'word'):'ldr',(True,'half'):'ldrh',(True,'byte'):'ldrb',(False,'word'):'str',(False,'half'):'strh',(False,'byte'):'strb'}[ld,w],rd,rb,ro]
  if k=='alu'and x[0]in('adc','sbc','tst','bic','eor'):k='alu_ext'
  if k=='adrsp':k='spaddr'
  SPECS.append((a,k,tuple(x)));a+=4 if k=='call'else 2
 return a
# Reuse independent stock task registry, special/main readers and printer semantics.
# The original modules' ROM-derived data signatures are not used as specifications.
REUSE_RANGES=[(0x08000510,0x08000554),(0x08002CF0,0x08002E74),(0x0800575C,0x08005C5C),
 (0x080697BC,0x080697F4),(0x08076BB4,0x08076C9E),(0x08076D40,0x08076D7C),
 (0x081C7AC8,0x081C7AD0),(0x081C9DF8,0x081C9E50),(0x09378A30,0x09378A44)]
reused={}
for module in(mini,field,live):
 for a,i in module.INS.items():
  if any(lo<=a<hi for lo,hi in REUSE_RANGES)and not 0x08005B04<=a<0x08005B14:
   if a in reused:need(encoded(reused[a])==encoded(i),'shared semantics一致')
   reused[a]=i
for i in task.BLOCKS['run_tasks_field0_dispatch']:reused[i.address]=i
for a,i in sorted(reused.items()):block(a,[(i.kind,*i.args)])
# special057 source: facility field3 setter, FadeScreen and actual CreateTask.
block(ENTRY,[('push',16,True),('imm','mov',1,0),('imm','mov',0,3),('call',0x09126A28),
 ('imm','mov',1,0),('imm','mov',0,1),('literal',3,0x0910414C),('call',0x09104158),
 ('imm','mov',1,0),('literal',0,0x09104150),('literal',3,0x09104154),('call',0x09104158),('pop',16,True)])
for a,reg in[(0x09104158,3),(0x0910415C,5),(0x0910415E,6),(0x09104164,11)]:block(a,[('bx',reg)])
# Task_InitFrontierRecords: inactive-fade branch, real allocation assignment,
# independent layout20, battle type bounds, facility0/Tower, tier-list first byte.
block(TASK,[('literal',3,0x091036C4),('mem',True,'byte',3,3,7),('push',112,True),
 ('shift','lsl',4,0,0),('imm','cmp',3,127),('branch',9,0x0910364A),('pop',112,True),
 ('literal',3,0x091036C8),('imm','mov',0,20),('call',0x09104158),('literal',3,0x091036CC),
 ('imm','mov',1,6),('mem',True,'half',2,3,0),('imm','mov',3,0),('compare',1,2),('alu','adc',3,3),
 ('literal',5,0x091036D0),('alu','neg',3,3),('alu','and',2,3),('mem',False,'word',0,5,0),
 ('mem',False,'byte',2,0,8),('imm','mov',0,0),('call',0x091269B8),('mem',True,'word',3,5,0),
 ('mem',False,'byte',0,3,12),('imm','add',3,16),('shift','lsl',0,3,0),('imm','mov',2,4),
 ('literal',3,0x091036D4),('imm','mov',1,64),('call',0x09104158),('mem',True,'word',3,5,0),
 ('mem',True,'byte',2,3,12),('imm','cmp',2,2),('branch',0,0x091036BA),('imm','cmp',2,3),('branch',1,0x091036B2)])
block(0x09103692,[('mem',False,'byte',1,3,11),('mem',False,'word',2,3,4),('mem',True,'byte',2,2,0),
 ('mem',False,'byte',2,3,9),('literal',3,0x091036E0),('call',0x09104158),('literal',0,0x091036E4),
 ('literal',3,0x091036E8),('call',0x09104158),('shift','lsl',0,4,0),('literal',3,0x091036EC),
 ('call',0x09104158),('jump',0x09103648),('literal',2,0x091036F0),('mem',True,'byte',1,2,0),
 ('literal',2,0x091036F4),('jump',0x09103692)])
# All real CB state0..7 dispatches. Graphics calls are individually bounded ABI
# conditions. State increments and real SetMainCallback2 reset are not host-seeded.
block(CB,[('imm','mov',3,135),('push',112,True),('literal',4,0x0910407C),('shift','lsl',3,3,3),
 ('regmem',True,'byte',3,4,3),('spadd',-24),('imm','cmp',3,7),('branch',9,0x09103E6E),
 ('jump',0x09103FD8),('literal',2,0x09104080),('shift','lsl',3,3,2),('regmem',True,'word',3,2,3),('movhi',15,3)])
block(0x09103EF2,[('spadd',24),('pop',112,True)])
block(0x09103EF6,[('literal',3,0x091040B4),('call',0x09104158),('literal',3,0x091040B8),('call',0x09104158),
 ('literal',3,0x091040BC),('call',0x09104158),('literal',3,0x091040C0),('call',0x09104158),
 ('literal',3,0x091040C4),('call',0x09104158),('literal',3,0x091040C8),('call',0x09104158),
 ('imm','mov',2,135),('shift','lsl',2,2,3),('regmem',True,'byte',3,4,2),('imm','add',3,1),
 ('regmem',False,'byte',3,4,2),('jump',0x09103EF2)])
block(0x09103F26,[('imm','mov',0,128),('literal',5,0x0910409C),('literal',3,0x091040CC),('shift','lsl',0,0,5),
 ('mem',True,'word',6,5,0),('call',0x09104158),('literal',3,0x091040D0),('mem',False,'word',0,6,0),
 ('imm','mov',0,0),('call',0x09104158),('imm','mov',2,3),('imm','mov',0,0),('literal',1,0x091040D4),
 ('literal',3,0x091040D8),('call',0x09104158),('mem',True,'word',3,5,0),('imm','mov',0,2),
 ('mem',True,'word',1,3,0),('literal',3,0x091040DC),('call',0x09104158),('jump',0x09103F1A)])
block(0x09103F58,[('imm','mov',3,0),('imm','mov',2,0),('spmem',False,3,0),('literal',1,0x091040E0),
 ('literal',5,0x091040E4),('imm','mov',0,2),('call',0x0910415C),('literal',3,0x0910409C),
 ('mem',True,'word',3,3,0),('literal',0,0x091040E8),('mem',True,'word',1,3,0),('literal',3,0x091040EC),
 ('call',0x09104158),('imm','mov',2,32),('imm','mov',1,0),('literal',0,0x091040F0),('literal',5,0x091040F4),
 ('call',0x0910415C),('imm','mov',2,32),('imm','mov',1,240),('literal',0,0x091040F8),('call',0x0910415C),
 ('jump',0x09103F1A),('literal',3,0x091040FC),('call',0x09104158),('imm','cmp',0,0),('branch',1,0x09103EF2),
 ('literal',5,0x09104100),('call',0x0910415C),('imm','mov',0,1),('call',0x0910415C),('imm','mov',0,2),
 ('call',0x0910415C),('imm','mov',0,2),('literal',3,0x09104104),('call',0x09104158),('jump',0x09103F1A),
 ('literal',3,0x09104108),('literal',0,0x0910410C),('call',0x09104158),('literal',3,0x09104110),
 ('call',0x09104158),('jump',0x09103F1A),('imm','mov',3,0),('imm','mov',0,1),('imm','mov',2,16),
 ('imm','mov',1,0),('spmem',False,3,0),('literal',5,0x09104114),('alu','neg',0,0),('call',0x0910415C),('jump',0x09103F1A)])
block(0x09103FD8,[('imm','mov',0,0),('literal',3,0x09104088),('call',0x09104158),('imm','mov',5,0),
 ('imm','mov',1,192),('literal',3,0x09104118),('adrsp',0,16),('shift','lsl',6,3,0),('mem',False,'half',5,0,0),
 ('literal',2,0x0910411C),('shift','lsl',1,1,19),('multiple',False,6,7),('imm','mov',1,224),
 ('shift','lsl',6,3,0),('spmem',False,5,20),('literal',2,0x09104120),('adrsp',0,20),('shift','lsl',1,1,19),
 ('multiple',False,6,7),('imm','mov',0,18),('imm','mov',1,160),('addhi',0,13),('mem',False,'half',5,0,0),
 ('literal',2,0x09104124),('shift','lsl',1,1,19),('multiple',False,3,7),('imm','mov',1,130),
 ('literal',5,0x09104128),('imm','mov',0,0),('shift','lsl',1,1,5),('call',0x0910415C)])
a=0x0910401A
for reg in(14,12,10,8,28,30,24,26,20,22,16,18):a=block(a,[('imm','mov',1,0),('imm','mov',0,reg),('call',0x0910415C)])
need(a==0x0910407A,'source全12reg設定');block(a,[('jump',0x09103F1A)])
block(0x09103E76,[('literal',0,0x09104084),('literal',3,0x09104088),('call',0x09104158),('imm','mov',1,0),
 ('imm','mov',0,0),('literal',3,0x0910408C),('call',0x09104158),('literal',5,0x09104090),('shift','lsl',0,5,0),
 ('literal',3,0x09104094),('imm','add',0,28),('call',0x09104158),('shift','lsl',0,5,0),('literal',6,0x09104098),
 ('imm','add',0,36),('call',0x0910415E),('shift','lsl',0,5,0),('imm','add',0,44),('call',0x0910415E),
 ('shift','lsl',0,5,0),('imm','add',0,52),('call',0x0910415E),('call',PRINT)])
# PrintCurrentRecords complete prologue, CleanWindows21, MapName/tier unrelated
# render calls, then both selected pointers through real stack argument stores.
block(PRINT,[('push',240,True),('movhi',5,8),('movhi',14,11),('movhi',7,10),('movhi',6,9),('push',224,True),
 ('literal',3,0x09103B18),('mem',True,'word',3,3,0),('mem',True,'byte',3,3,9),('imm','mov',4,0),
 ('movhi',8,3),('literal',5,0x09103B1C),('spadd',-36),('shift','lsl',0,4,24),('imm','mov',1,0),
 ('shift','lsr',0,0,24),('imm','add',4,1),('call',0x0910415C),('imm','cmp',4,21),('branch',1,0x091037F2),
 ('literal',3,0x09103B20),('call',0x09104158),('literal',4,0x09103B24),('shift','lsl',1,0,0),('imm','mov',2,0),
 ('shift','lsl',0,4,0),('literal',3,0x09103B28),('call',0x09104158),('spmem',False,4,8),('literal',4,0x09103B2C),
 ('imm','mov',2,72),('movhi',12,4),('imm','mov',5,0),('addhi',2,12),('literal',6,0x09103B30),('imm','mov',3,6),
 ('imm','mov',1,1),('spmem',False,2,0),('movhi',10,2),('imm','mov',0,0),('imm','mov',2,0),('spmem',False,5,4),
 ('movhi',11,6),('spmem',False,4,24),('call',0x0910415E),('literal',6,0x09103B18),('mem',True,'word',3,6,0),
 ('movhi',0,8),('mem',True,'byte',1,3,8),('call',0x09101A9C),('shift','lsl',3,4,0),('imm','add',3,76),
 ('imm','mov',2,0),('imm','mov',1,0),('spmem',False,0,8),('spmem',False,3,0),('imm','mov',0,12),('imm','mov',3,4),
 ('spmem',False,5,4),('call',0x09104164),('literal',3,0x09103B34),('imm','add',4,80),('imm','mov',2,0),('imm','mov',1,0),
 ('spmem',False,3,20),('spmem',False,3,8),('imm','mov',0,5),('imm','mov',3,4),('spmem',False,5,4),('spmem',False,4,0),
 ('call',0x09104164),('literal',3,0x09103B38),('imm','mov',2,0),('imm','mov',1,0),('spmem',False,3,28),
 ('spmem',False,3,8),('imm','mov',0,6),('imm','mov',3,4),('spmem',False,5,4),('spmem',False,4,0),('call',0x09104164)])
# menu2.c AddTextPrinterParameterized3 builds complete template in stack.
block(0x0812ED24,[('push',112,True),('spadd',-16),('addi',4,1,0),('spmem',True,6,32),('spmem',True,5,36),
 ('spmem',True,1,40),('shift','lsl',4,4,24),('shift','lsr',4,4,24),('shift','lsl',5,5,24),('shift','lsr',5,5,24),
 ('spmem',False,1,0),('movhi',1,13),('mem',False,'byte',0,1,4),('movhi',0,13),('mem',False,'byte',4,0,5),
 ('mem',False,'byte',2,0,6),('mem',False,'byte',3,0,7),('mem',True,'byte',0,0,6),('mem',False,'byte',0,1,8),
 ('movhi',0,13),('mem',True,'byte',0,0,7),('mem',False,'byte',0,1,9),('addi',0,4,0),('imm','mov',1,2),('call',0x080F8A38),
 ('movhi',1,13),('mem',False,'byte',0,1,10),('addi',0,4,0),('imm','mov',1,3),('call',0x080F8A38),('movhi',1,13),
 ('mem',False,'byte',0,1,11),('movhi',3,13),('mem',True,'byte',2,3,12),('imm','mov',1,16),('alu','neg',1,1),
 ('addi',0,1,0),('alu','and',0,2),('mem',False,'byte',0,3,12),('movhi',2,13),('mem',True,'byte',0,6,1),
 ('shift','lsl',0,0,4),('imm','mov',4,15),('mem',False,'byte',0,2,12),('mem',True,'byte',2,6,0),('addi',0,4,0),
 ('alu','and',0,2),('mem',True,'byte',2,3,13),('alu','and',1,2),('alu','orr',1,0),('mem',False,'byte',1,3,13),
 ('movhi',2,13),('mem',True,'byte',0,6,2),('shift','lsl',0,0,4),('alu','and',1,4),('alu','orr',1,0),('mem',False,'byte',1,2,13),
 ('movhi',0,13),('addi',1,5,0),('imm','mov',2,0),('call',0x08002CF0),('spadd',16),('pop',112,False),('pop',1,False),('bx',0)])
# speed0 branch and post-EOS CopyWindowToVram, absent from older speed255 model.
block(0x08002D50,[('imm','cmp',5,0),('branch',0,0x08002D7C)])
block(0x08002DA8,[('literal',0,0x08002DC8),('mem',True,'byte',0,0,4),('imm','mov',1,2),('call',0x08003EEC)])
# font0 small: glyphId=0 and real RenderText dispatcher.
block(0x08005348,[('push',0,True),('addi',2,0,0),('addi',3,2,0),('imm','add',3,20),('mem',True,'byte',1,3,1),
 ('imm','mov',0,128),('alu','and',0,1),('imm','cmp',0,0),('branch',1,0x0800536C),('mem',True,'byte',1,2,20),
 ('imm','mov',0,16),('alu','neg',0,0),('alu','and',0,1),('mem',False,'byte',0,2,20),('mem',True,'byte',0,3,1),
 ('imm','mov',1,128),('alu','orr',0,1),('mem',False,'byte',0,3,1),('addi',0,2,0),('call',0x0800575C),
 ('shift','lsl',0,0,16),('shift','lsr',0,0,16),('pop',2,False),('bx',1)])
block(0x08005AFC,[('addi',0,3,0),('call',0x080062B4),('jump',0x08005B2A)])
INS={a:p.Ins(a,k,x)for a,k,x in SPECS};need(len(INS)==len(SPECS),'Frontier命令非重複')
# libc memset source aligned four-byte tail; independent repeated-byte value.
block(0x081C9E2E,[('multiple',False,1,8),('imm','sub',2,4)])
# DestroyTask single registered head/tail branch closes the scheduler's same slot.
block(0x08076CA0,[('push',16,True),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('literal',4,0x08076CD4),
 ('shift','lsl',1,0,2),('add',1,1,0),('shift','lsl',1,1,3),('add',2,1,4),('mem',True,'byte',0,2,4),
 ('imm','cmp',0,0),('branch',0,0x08076D0A),('imm','mov',0,0),('mem',False,'byte',0,2,4),
 ('mem',True,'byte',3,2,5),('imm','cmp',3,254),('branch',1,0x08076CD8),('mem',True,'byte',0,2,6),
 ('imm','cmp',0,255),('branch',0,0x08076D0A)])
block(0x08076D0A,[('pop',16,False),('pop',1,False),('bx',0)])
INS={a:p.Ins(a,k,x)for a,k,x in SPECS};need(len(INS)==len(SPECS),'Frontier命令非重複')
WORDS={}
for a,i in reused.items():
 if i.kind=='literal':
  key=i.args[1];values=[m.LITERALS[key]for m in(mini,field,live,task)if key in m.LITERALS]
  need(values and len(set(values))==1,'既存独立literal '+hex(key));WORDS[key]=values[0]
WORDS.update({0x08076CD4:TASKS,0x08076D3C:TASKS,0x081631C4:ENTRY|1,
 0x0910414C:0x08079F79,0x09104150:TASK|1,0x09104154:0x08076BB5,
 0x091036C4:0x020379EC,0x091036C8:0x08002BB1,0x091036CC:0x02036FEC,0x091036D0:CELL,
 0x091036D4:0x081C9DF9,0x091036E0:0x0807A765,0x091036E4:CB|1,0x091036E8:0x08000545,
 0x091036EC:0x08076CA1,0x091036F0:0x0916744B,0x091036F4:0x09167250,
 0x0910407C:MAIN,0x09104080:0x0916744C,0x09104084:0x09103E41,0x09104088:0x080006F5,
 0x0910408C:0x08004429,0x09104090:0x091674EC,0x09104094:0x0800E9E9,0x09104098:0x0800EA2D,
 0x0910409C:CELL,0x091040B4:0x08087A49,0x091040B8:0x08076B55,0x091040BC:0x0800668D,
 0x091040C0:0x080F7861,0x091040C4:0x0806FCCD,0x091040C8:0x0800846D,0x091040CC:0x08002B9D,
 0x091040D0:0x08001619,0x091040D4:0x091674E4,0x091040D8:0x08001659,0x091040DC:0x08001FA1,
 0x091040E0:0x091B84AC,0x091040E4:0x080F78D1,0x091040E8:0x091B8580,0x091040EC:0x0800E569,
 0x091040F0:0x091B865C,0x091040F4:0x0806FB91,0x091040F8:0x091674F0,0x091040FC:0x080F7885,
 0x09104100:0x080019BD,0x09104104:0x080020BD,0x09104108:0x08003AF1,0x0910410C:0x09167530,
 0x09104110:0x08002C29,0x09104114:0x0806FD2D,0x09104118:0x040000D4,
 0x0910411C:0x8100C000,0x09104120:0x85000100,0x09104124:0x81000200,0x09104128:0x08000A39,
 0x09103B18:CELL,0x09103B1C:0x08004429,0x09103B20:0x08055B21,0x09103B24:0x02021C88,
 0x09103B28:0x080C5F5D,0x09103B2C:0x0916746C,0x09103B30:0x0812ED25,0x09103B34:TARGETS[0],0x09103B38:TARGETS[1],
 0x083E30E8:0x08005349,0x08005AE4:0x08005AFC,0x0800577C:0x08005798,0x08005848:0x08005C54,0x08005844:0x0800584C})
for i,a in enumerate((0x09103FD8,0x09103EF6,0x09103F26,0x09103F58,0x09103F8E,0x09103FB4,0x09103FC4,0x09103E76)):WORDS[0x0916744C+i*4]=a
# Source-declared literal texts and colour bytes; no observed ROM text/hex fixture.
TEXT_DECLS=(('gText_CurrentStreak',TARGETS[0],'げんざい\\nさいこう'),('gText_MaxStreak',TARGETS[1],'さいこう'))
CHARMAP={'げ': 58, 'ん': 46, 'ざ': 60, 'い': 2, '\\n': 254, 'さ': 11, 'こ': 10, 'う': 3}
def serialize_text(text,charmap=CHARMAP):
 tokens=re.findall(r'\\n|.',text);need(''.join(tokens)==text and all(t in charmap for t in tokens),'独立文字grammar')
 return bytes([charmap[t]for t in tokens]+[255])
TEXT_PARTS={a:serialize_text(s)for _,a,s in TEXT_DECLS}
TEXTS=[dict(label=name,address=a,**identity(TEXT_PARTS[a]))for name,a,_ in TEXT_DECLS]
WINDOW_VALUES = [('WIN_BATTLE_FACILITY_NAME', (0, 1, 0, 10, 3, 15, 1)),
 ('WIN_BATTLE_TYPE', (0, 12, 0, 18, 3, 15, 31)),
 ('WIN_LEVEL_50', (0, 2, 5, 6, 2, 15, 85)),
 ('WIN_3V3_LEVEL_50', (0, 15, 5, 4, 2, 15, 97)),
 ('WIN_6V6_LEVEL_50', (0, 23, 5, 4, 2, 15, 105)),
 ('WIN_CURRENT_STREAK_LEVEL_50', (0, 2, 7, 10, 2, 15, 113)),
 ('WIN_MAX_STREAK_LEVEL_50', (0, 2, 9, 10, 2, 15, 133)),
 ('WIN_LEVEL_100', (0, 2, 12, 6, 2, 15, 153)),
 ('WIN_3V3_LEVEL_100', (0, 15, 12, 4, 2, 15, 165)),
 ('WIN_6V6_LEVEL_100', (0, 23, 12, 4, 2, 15, 173)),
 ('WIN_CURRENT_STREAK_LEVEL_100', (0, 2, 14, 10, 2, 15, 181)),
 ('WIN_MAX_STREAK_LEVEL_100', (0, 2, 16, 10, 2, 15, 201)),
 ('WIN_TIER', (0, 2, 3, 18, 2, 15, 221)),
 ('WIN_CURRENT_STREAK_3V3_LEVEL_50', (0, 15, 7, 4, 2, 15, 257)),
 ('WIN_MAX_STREAK_3V3_LEVEL_50', (0, 15, 9, 4, 2, 15, 265)),
 ('WIN_CURRENT_STREAK_6V6_LEVEL_50', (0, 23, 7, 4, 2, 15, 273)),
 ('WIN_MAX_STREAK_6V6_LEVEL_50', (0, 23, 9, 4, 2, 15, 281)),
 ('WIN_CURRENT_STREAK_3V3_LEVEL_100', (0, 15, 14, 4, 2, 15, 289)),
 ('WIN_MAX_STREAK_3V3_LEVEL_100', (0, 15, 16, 4, 2, 15, 297)),
 ('WIN_CURRENT_STREAK_6V6_LEVEL_100', (0, 23, 14, 4, 2, 15, 305)),
 ('WIN_MAX_STREAK_6V6_LEVEL_100', (0, 23, 16, 4, 2, 15, 313))]
def fixed_parts():
 parts={a:encoded(i)for a,i in INS.items()}
 for a,v in WORDS.items():need(a not in parts,'命令literal非重複');parts[a]=v.to_bytes(4,'little')
 parts.update(TEXT_PARTS)
 parts[0x083E30ED]=bytes([12])
 parts[0x09167530]=b''.join(bytes(row[:6])+row[6].to_bytes(2,'little')for _,row in WINDOW_VALUES)+bytes([255,0,0,0,0,0,0,0])
 parts[0x09167250]=bytes([0]);parts[0x0916744B]=bytes([8]);parts[0x091674BC]=bytes([0,2,3])
 return parts
ALL_WINDOWS=critical.merge_parts(fixed_parts())
WINDOWS={f'frontier_records_roots_{i}':(w['address'],w['size'])for i,w in enumerate(ALL_WINDOWS)}
def bind(raw):
 for a,b in fixed_parts().items():need(chunk(raw,a,len(b))==b,'独立意味/field/text '+hex(a))
 return True
PROFILE=dict(special=87,script_context=0x02014000,empty_task_registry=True,palette_inactive=True,var8000=0,
 facility_getter_result=0,allocation=ALLOC,allocation_size=20,tilemap=TILEMAP,tilemap_size=4096,
 free_temp_buffers_result=0,font_table=0x083E30E8,main_callback1=0,main_key_input=0,text_flags=0,
 normal_abi_return=True,epochs_required_only_at_live_resource_uses=True)
EXTERNAL={
 (0x080697BE,0x080691B8):('ScriptReadHalfword',87),
 (0x09104132,0x09126A28):('VegaFacilityStateSet',None),
 (0x0910413C,0x08079F78):('FadeScreen',None),
 (0x0910364E,0x08002BB0):('Calloc20',ALLOC),
 (0x0910366A,0x091269B8):('VegaFacilityStateGet',0),
 (0x0910369C,0x0807A764):('PlayRainStoppingSoundEffect',None),
 (0x08000512,0x080F6168):('main_link_gate',0),
 (0x0800051A,0x0813C034):('main_link_gate2',0),
 (0x09103FDC,0x080006F4):('SetVBlankCallback_null',None),
 (0x09103F7E,0x0806FB90):('LoadPalette_gfx',None),
 (0x09103F88,0x0806FB90):('LoadPalette_text',None),
 (0x09103F90,0x080F7884):('free_temp_tile_data_buffers_if_possible',0),
 (0x09103F9A,0x080019BC):('ShowBg0',None),
 (0x09103FA0,0x080019BC):('ShowBg1',None),
 (0x09103FA6,0x080019BC):('ShowBg2',None),
 (0x09103FAE,0x080020BC):('CopyBgTilemapBufferToVram',None),
 (0x09103FB8,0x08003AF0):('InitWindows',1),
 (0x09103FBE,0x08002C28):('DeactivateAllTextPrinters',None),
 (0x09103FD2,0x0806FD2C):('BeginNormalPaletteFade',None),
 (0x09103F30,0x08002B9C):('Malloc_tilemap4096',TILEMAP),
 (0x09103F3A,0x08001618):('ResetBgsAndClearDma3BusyFlags',None),
 (0x09103F46,0x08001658):('InitBgsFromTemplates',None),
 (0x09103F52,0x08001FA0):('SetBgTilemapBuffer',None),
 (0x09103F64,0x080F78D0):('decompress_and_copy_tile_data_to_vram',None),
 (0x09103F72,0x0800E568):('LZDecompressWram',None),
 (0x09103E7A,0x080006F4):('SetVBlankCallback_frontier',None),
 (0x09103E84,0x08004428):('FillWindowPixelBuffer0',None),
 (0x09103E90,0x0800E9E8):('LoadCompressedSpriteSheet',None),
 (0x09103E9A,0x0800EA2C):('LoadSpritePalette_bronze',None),
 (0x09103EA2,0x0800EA2C):('LoadSpritePalette_silver',None),
 (0x09103EAA,0x0800EA2C):('LoadSpritePalette_gold',None),
 (0x091037FA,0x08004428):('CleanWindows_each',None),
 (0x09103804,0x08055B20):('GetCurrentRegionMapSectionId',0),
 (0x09103812,0x080C5F5C):('GetMapName',None),
 (0x09103836,0x0812ED24):('WindowPrint_facility_unselected',None),
 (0x09103842,0x09101A9C):('GetFrontierTierName',0x02015000),
 (0x09103858,0x0812ED24):('WindowPrint_tier_unselected',None),
 (0x0812ED54,0x080F8A38):('GetFontAttribute_spacing',None),
 (0x0812ED60,0x080F8A38):('GetFontAttribute_line_spacing',None),
 (0x08002D48,0x08002E78):('GenerateFontHalfRowLookupTable',None),
 (0x08005AFE,0x080062B4):('DecompressGlyph_Small',None),
 (0x08005B2C,0x08002FE4):('CopyGlyphToWindow',None),
 (0x08002DAE,0x08003EEC):('CopyWindowToVram',None)}
for site,target,name in[(0x09103EF8,0x08087A48,'ScanlineEffect_Stop'),(0x09103EFE,0x08076B54,'ResetTasks'),
 (0x09103F04,0x0800668C,'ResetSpriteData'),(0x09103F0A,0x080F7860,'ResetTempTileDataBuffers'),
 (0x09103F10,0x0806FCCC,'ResetPaletteFade'),(0x09103F16,0x0800846C,'FreeAllSpritePalettes')]:EXTERNAL[(site,target)]=(name,None)
for site in[0x09104016]+list(range(0x0910401E,0x09104077,8)):EXTERNAL[(site,0x08000A38)]=('SetGpuReg',None)
BRIDGES=((STOP,0x08076D10),(STOP,0x08000510))

def memory():
 mem=rt.task_fixture([])
 for i in range(16):
  for j in list(range(4))+list(range(8,40)):mem[TASKS+i*40+j]=165
 for a,n,v in[(0x020379F3,1,0),(0x02036FEC,2,0),(MAIN,4,0),(STATE,1,165),
  (MAIN+44,2,0),(MAIN+46,2,0),(0x03003DD0,4,0x083E30E8),(0x03003E90,1,0)]:rt.setmem(mem,a,n,v)
 return mem

def preserve(live,writes=(),events=None,required_epochs=None):
 need(type(live)is list and all(type(w)is list and len(w)==2 and type(w[0])is int and type(w[1])is int and w[1]>0 and 0<=w[0]<w[0]+w[1]<=1<<32 for w in live),'有限live射影')
 events={}if events is None else events
 names={'allocation_epoch_changed','task_slot_epoch_changed','main_slot_epoch_changed','window_epoch_changed','printer_epoch_changed','stack_epoch_changed'}
 need(type(events)is dict and set(events)<=names and all(type(v)is bool for v in events.values()),'閉じたepoch events')
 required_epochs=names if required_epochs is None else set(required_epochs)
 need(required_epochs<=names and not any(events.get(k,False)for k in required_epochs),'実useに必要な同epoch')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(v)is int and 0<=a<a+n<=1<<32 and 0<=v<1<<(n*8),'有限opaque書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live破壊禁止')
 return True

def _compose(raw,projections=None,opaque_writes=None,epoch_events=None,profile=None,future_access=None):
 need(profile is None or exact(profile,PROFILE),'限定入口profile')
 trace=[];boundaries=[];groups=[];visited=[];states=[];writes=[];task_dispatch=[];main_dispatch=[];clean=[];printers=[]
 m=machine.Machine(raw,0x080697BC,{0:PROFILE['script_context']},memory(),instructions=INS,trace=trace)
 phase='special';frames=0;allocated=False;tilemap=False;windows=False;task_live=False;main_live=False;printer_live=False
 def boundary(key,name,result=None,outputs=()):
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if projections is not None:
   need(index<len(projections),'全境界射影');live_fields=projections[index];effects=(epoch_events or {}).get(key,{})
   changes=(opaque_writes or {}).get(key,())
   access_fields=live_fields if future_access is None else future_access[index]
   overlaps=lambda a,n:any(a<b+s and b<a+n for b,s in access_fields)
   epochs=dict(allocation_epoch_changed=allocated and (overlaps(ALLOC,20)or overlaps(CELL,4)),
    task_slot_epoch_changed=task_live and overlaps(TASKS,40),main_slot_epoch_changed=main_live and overlaps(MAIN+4,4),
    window_epoch_changed=windows,printer_epoch_changed=printer_live,stack_epoch_changed=overlaps(0x03006000,0x1000))
   required={k for k,v in epochs.items()if v};preserve(live_fields,changes,effects,required)
   for a,n,v in changes:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live_fields for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   groups.append(dict(index=index,site=key[0],target=key[1],role=name,
    required_fields=[dict(address=a,size=n)for a,n in live_fields],normal_abi_return_required=True,
    same_allocation_epoch_required=epochs['allocation_epoch_changed'],same_task_slot_epoch_required=epochs['task_slot_epoch_changed'],same_main_slot_epoch_required=epochs['main_slot_epoch_changed'],
    same_window_epoch_required=epochs['window_epoch_changed'],same_printer_epoch_required=epochs['printer_epoch_changed'],same_stack_epoch_required=epochs['stack_epoch_changed'],
    required_epochs=sorted(required),
    conditional_outputs=[dict(address=a,size=n,value=v if rt.concrete(v)else'unspecified')for a,n,v in outputs],callee_effects_proven=False))
  for a,n,v in outputs:m.write(a,n,v)
  for reg in(0,1,2,3,12):m.reg[reg]=rt.U
  if result is not None:m.reg[0]=result
  m.flags=(rt.U,)*4;m.flag_pc=None
 while m.pc!=0x0910388A:
  need(m.steps<20000,'有限Frontier上限')
  if m.pc==STOP:
   need(m.reg[13]==0x03007000,'完全API正常復帰stack')
   if phase=='special':
    need(rt.getmem(m.mem,TASKS,4)==TASK|1 and rt.getmem(m.mem,TASKS+4,1)==1,'実task同slot登録')
    boundary(BRIDGES[0],'same_slot_RunTasks_API');m.pc=0x08076D10;phase='task'
   else:
    need(rt.getmem(m.mem,MAIN+4,4)==CB|1,'実main callback同slot登録')
    need(rt.getmem(m.mem,STATE,1)==frames,'実state0または実incrementの継続')
    boundary(BRIDGES[1],'same_slot_MainCallbacks_API');m.pc=0x08000510;phase='main';frames+=1
   m.reg[14]=STOP|1;continue
  external=m.pc not in INS
  if m.pc==0x0812ED24:
   key=((m.reg[14]&~1)-4,m.pc)
   if key in EXTERNAL:external=True
   else:
    text=m.read(m.reg[13]+8,4);window=m.reg[0]
    need(windows and allocated and text in TARGETS and window==(5 if text==TARGETS[0]else 6),'live window5/6と実text pointer')
    need(m.reg[1:4]==[0,0,4]and m.read(m.reg[13]+4,4)==0 and m.read(m.reg[13],4)==0x091674BC,'source font0位置/color/speed0')
    printers.append((key[0],window,text))
  if not external:
   pc=m.pc;visited.append(pc)
   if pc==CB:states.append(m.read(STATE,1))
   if pc==0x08076D28:task_dispatch.append((m.reg[4],m.reg[0]))
   if pc==0x08000530:main_dispatch.append((m.reg[4]+4,m.read(m.reg[4]+4,4)))
   before=len(m.writes);m.step()
   if pc==0x09378A3C:printer_live=True
   # Last use of this temporary-printer generation is the windowId load
   # before CopyWindowToVram. The next text creates a fresh generation.
   if pc==0x08002DAA:printer_live=False
   if len(m.writes)>before:
    for _,a,n in m.writes[before:]:
     if a==TASKS+4:task_live=rt.getmem(m.mem,a,1)==1
     if a==MAIN+4:main_live=True
     if a==STATE or a==MAIN+4 or a==TASKS or a==CELL:writes.append((pc,a,n,m.read(a,n)))
   continue
  key=((m.reg[14]&~1)-4,m.pc);need(key in EXTERNAL,'未知call '+str(tuple(hex(x)for x in key)))
  name,result=EXTERNAL[key];outputs=[]
  if name=='VegaFacilityStateSet':need(m.reg[:2]==[3,0],'source field3 setter引数')
  elif name=='FadeScreen':need(m.reg[:2]==[1,0],'source fade引数')
  elif name=='Calloc20':
   need(m.reg[0]==20 and not allocated,'20byte単一allocation')
   outputs=[(ALLOC+j,1,0)for j in range(20)]
  elif name=='VegaFacilityStateGet':need(m.reg[0]==0,'source facility field0')
  elif name=='Malloc_tilemap4096':need(m.reg[0]==4096 and allocated and not tilemap,'4096tilemap正常allocation条件');tilemap=True
  elif name=='InitWindows':need(m.reg[0]==0x09167530 and not windows,'source window templateで有効21window')
  elif name=='CleanWindows_each':need(windows and m.reg[:2]==[len(clean),0],'全21窓clear実loop');clean.append(m.reg[0])
  elif name=='GetFrontierTierName':need(m.reg[:2]==[0,0],'実producer tier/type')
  elif name.startswith('WindowPrint_'):need(m.read(m.reg[13]+8,4)not in TARGETS,'対象textをopaque化しない')
  elif name=='DecompressGlyph_Small':outputs=[(0x03003E60,1,rt.U)]
  elif name=='CopyWindowToVram':need(m.reg[0]in(5,6)and m.reg[1]==2 and windows,'実speed0 CopyWindow引数')
  elif name=='SetBgTilemapBuffer':need(m.reg[:2]==[2,TILEMAP]and tilemap,'実tilemap pointer writer/read')
  elif name=='SetVBlankCallback_null':need(m.reg[0]==0,'state0 VBlank解除')
  elif name=='SetVBlankCallback_frontier':need(m.reg[0]==0x09103E41,'state7 VBlank登録')
  boundary(key,name,result,outputs)
  if name=='Calloc20':allocated=True
  if name=='InitWindows':windows=True
  m.pc=m.reg[14]&~1
 need(states==list(range(8))and frames==8,'実state0から7全frame')
 need(clean==list(range(21)),'全21clearloop')
 need(printers==[(0x09103870,5,TARGETS[0]),(0x09103886,6,TARGETS[1])],'対象caller2本')
 need(m.reads==[(a+j,1)for a in TARGETS for j in range(len(TEXT_PARTS[a]))],'全15byte/EOS実LDRB')
 need(task_dispatch==[(TASKS,0)]and main_dispatch==[(MAIN+4,CB|1)]*8,'同task/main登録reader')
 return dict(steps=m.steps,trace=trace,boundaries=boundaries,groups=groups,visited=visited,states=states,
  writes=writes,reads=m.reads,printers=printers,clean_windows=clean,task_dispatch=task_dispatch,main_dispatch=main_dispatch)

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(contract is None or exact(contract,CONTRACT),'限定contract')
 allowed=set(EXTERNAL)|set(BRIDGES)
 need(set(opaque_writes or {})<=allowed and set(epoch_events or {})<=allowed,'未知境界条件拒否')
 bind(raw);first=_compose(raw,profile=profile);projections=live.future_live(first['trace'],len(first['boundaries']))
 access=future_access_projection(first['trace'],len(first['boundaries']))
 second=_compose(raw,projections,opaque_writes,epoch_events,profile,access)
 for k in('steps','visited','states','writes','reads','printers','clean_windows','task_dispatch','main_dispatch','boundaries'):
  need(first[k]==second[k],'非live消去で同path/producer/consumer '+k)
 groups={}
 for g in second['groups']:
  row={k:v for k,v in g.items()if k!='index'};signature=json.dumps(row,sort_keys=True,separators=(',',':'))
  if signature not in groups:groups[signature]={**row,'count':0}
  groups[signature]['count']+=1
 return dict(status='PASS_CONDITIONAL_FRONTIER_RECORDS_TEXT',instruction_steps=second['steps'],
  conditional_call_groups=list(groups.values()),boundary_count=len(second['boundaries']),
  boundary_trace_identity=identity(json.dumps(second['boundaries'],separators=(',',':')).encode()),
  ordered_boundary_group_identity=identity(json.dumps([{k:v for k,v in g.items()if k!='index'}for g in second['groups']],sort_keys=True,separators=(',',':')).encode()),
  visited_identity=identity(json.dumps(second['visited'],separators=(',',':')).encode()),unique_instructions=len(set(second['visited'])),state_sequence=second['states'],
  producer_writes=second['writes'],text_reads=second['reads'],printer_calls=second['printers'],
  clean_windows=second['clean_windows'],task_dispatch=second['task_dispatch'],main_dispatch=second['main_dispatch'],
  complete_consumed_bytes=15,includes_both_eos=True,includes_current_newline=True,
  task_or_main_pointer_host_seeded=False,state7_host_seeded=False,text_pointer_host_seeded=False,
  nonlive_ram_erased_at_every_boundary=True,actual_runtime_execution_observed=False)

SOURCE_IDS = {'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'cfru-charmap.tbl': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                      'git_blob_sha': 'b841b842a93f886ee396c9b7f6529bb633964dbb',
                      'local': 'cfru-charmap.tbl',
                      'repository': 'kapibarasan000/CFRU-JP',
                      'sha256': '35c1b978f7004129679751a79cf4b40d7edd2fcd678bc81a29483b64b75b7ed5',
                      'size': 1639,
                      'source': 'charmap.tbl',
                      'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/charmap.tbl'},
 'cfru-frontier.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                     'git_blob_sha': '8c4e07b5e4553cdb23f2ca393e59672f8d671a2a',
                     'local': 'cfru-frontier.h',
                     'repository': 'kapibarasan000/CFRU-JP',
                     'sha256': 'aa62962fe7f2828a89b64fd8355e386c9ce72f16f0cff27db279d3448d971801',
                     'size': 11523,
                     'source': 'include/new/frontier.h',
                     'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/frontier.h'},
 'cfru-routinepointers': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                          'git_blob_sha': 'c0722629632ccc337a1710dfa11036fba64181a8',
                          'local': 'cfru-routinepointers',
                          'repository': 'kapibarasan000/CFRU-JP',
                          'sha256': 'dcc05504a939cb1876d1b569fb11a33021908bad4d9af7ed66ff74782b88ca24',
                          'size': 7381,
                          'source': 'routinepointers',
                          'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/routinepointers'},
 'cfru-src--frontier.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                          'git_blob_sha': '8879204faaf760cf6882acbe1833ad9f0e8055aa',
                          'local': 'cfru-src--frontier.c',
                          'repository': 'kapibarasan000/CFRU-JP',
                          'sha256': 'a33395bfaf81eec041a423d44d5620908e587a4f6e5614780b4bde393d7f4e06',
                          'size': 56750,
                          'source': 'src/frontier.c',
                          'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/frontier.c'},
 'cfru-src--frontier_records.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                  'git_blob_sha': '959106c76d097abe51f0489bc39fa79627e49efa',
                                  'local': 'cfru-src--frontier_records.c',
                                  'repository': 'kapibarasan000/CFRU-JP',
                                  'sha256': 'eb0ed3f1692ccd9a81420f60c533be7632bbf5835e8361e9a4ba0d4986e93084',
                                  'size': 22821,
                                  'source': 'src/frontier_records.c',
                                  'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/frontier_records.c'},
 'cfru-string.py': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                    'git_blob_sha': '6f67bd402b7f85c7681d3049f49a956a9a8a78b8',
                    'local': 'cfru-string.py',
                    'repository': 'kapibarasan000/CFRU-JP',
                    'sha256': '828d3813ed258a318f5d69f3fbabb05c9f0ef0975701f14875668c680a0f312e',
                    'size': 7959,
                    'source': 'scripts/string.py',
                    'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/scripts/string.py'},
 'cfru-strings--frontier_records.string': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                           'git_blob_sha': '97808cdbb80f035c6d5fc52d4eb6aa5fa35080f5',
                                           'local': 'cfru-strings--frontier_records.string',
                                           'repository': 'kapibarasan000/CFRU-JP',
                                           'sha256': 'd21a202e1477e03fb3cf55767efa2b6dad08bab10861485bbc29649bf48c35e5',
                                           'size': 6160,
                                           'source': 'strings/frontier_records.string',
                                           'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/strings/frontier_records.string'},
 'cfru-window.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                   'git_blob_sha': 'abf9660c5a9f451245147f3c65e99657537a2d93',
                   'local': 'cfru-window.h',
                   'repository': 'kapibarasan000/CFRU-JP',
                   'sha256': '82e2a7cb661ffe8a85d128752715bc16e6dc037a7eaac79d1a28ac9a3ac6dbe4',
                   'size': 4092,
                   'source': 'include/window.h',
                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/window.h'},
 'pret-main.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': '542b0f5d16dd93107523d11163bfcb70a42b707a',
                 'local': 'pret-main.c',
                 'repository': 'pret/pokefirered',
                 'sha256': '0bfa6c662b1cbd49bd31020b6c2509208004611e6701ad64badce22eca371139',
                 'size': 11699,
                 'source': 'src/main.c',
                 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/main.c'},
 'pret-menu2.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                  'git_blob_sha': 'e4e5eed54e4c99c60ea22938f2562226bcc580fb',
                  'local': 'pret-menu2.c',
                  'repository': 'pret/pokefirered',
                  'sha256': 'ee35028ff55a1062fd25df26aa6cb84b8bade79c696e9bc4ac1089a9a3a1a1d3',
                  'size': 32208,
                  'source': 'src/menu2.c',
                  'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/menu2.c'},
 'pret-new_menu_helpers.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                             'git_blob_sha': '08c032027cda2c34bf0dded37458adeb250aa553',
                             'local': 'pret-new_menu_helpers.c',
                             'repository': 'pret/pokefirered',
                             'sha256': 'd115f81a76f93ba1a34894acd58f266a1920215784176f94188e4bad8ba51b1c',
                             'size': 27834,
                             'source': 'src/new_menu_helpers.c',
                             'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/new_menu_helpers.c'},
 'pret-scrcmd.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'git_blob_sha': '97b695ee2f6fca80a3b78f52f6a444f696fe5814',
                   'local': 'pret-scrcmd.c',
                   'repository': 'pret/pokefirered',
                   'sha256': '898dad5a07ce0a125731b998654d86808885a8d48163d607478a5e70c1cac553',
                   'size': 56954,
                   'source': 'src/scrcmd.c',
                   'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/scrcmd.c'},
 'pret-task.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': '01503dc7ae78cf2348524bfb5bbb89183640f944',
                 'local': 'pret-task.c',
                 'repository': 'pret/pokefirered',
                 'sha256': '8bdd5205ec396be7b66d6e384a82309b3cab59783d46fb8c4c991b2172d4868b',
                 'size': 5029,
                 'source': 'src/task.c',
                 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/task.c'},
 'pret-text.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': 'f3eef07ce6dea8269980a5ecfdd6902c1c9c13d2',
                 'local': 'pret-text.c',
                 'repository': 'pret/pokefirered',
                 'sha256': '5696f49443eeaaac74b530421ac7f0cbfc71996c557399583788111c322dd80c',
                 'size': 63210,
                 'source': 'src/text.c',
                 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/text.c'},
 'pret-text.h': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': '7090a029bfc454e19e6425df631fda9db866ae0a',
                 'local': 'pret-text.h',
                 'repository': 'pret/pokefirered',
                 'sha256': 'ca0d1447747d042d92da4df693be353a5af5a26a6c9dcfdf1e3bbc0d01530299',
                 'size': 5585,
                 'source': 'include/text.h',
                 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/include/text.h'},
 'pret-text_printer.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                         'git_blob_sha': 'e425ccb181b52d1f0827785e76c1793c2b2d693d',
                         'local': 'pret-text_printer.c',
                         'repository': 'pret/pokefirered',
                         'sha256': '075af562bb87de25773e9dcee93d8180c84083209aede0ed6f02343f94f5823e',
                         'size': 16043,
                         'source': 'src/text_printer.c',
                         'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/text_printer.c'},
 'qol_production_hooks.S': {'commit': 'c2059ee805d978575b319e7a113b3edf0a676f1e',
                            'git_blob_sha': '50f7c241f24faea37885ed370774ac528bd58cf5',
                            'local': 'qol_production_hooks.S',
                            'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                            'sha256': 'f98689fe9c02b1345ae63feddc861a9b28fbd35fd8e024b931e88f788f5ac4e5',
                            'size': 9448,
                            'source': 'overlays/qol_production/qol_production_hooks.S',
                            'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/c2059ee805d978575b319e7a113b3edf0a676f1e/overlays/qol_production/qol_production_hooks.S'},
 'scripts--build_battle_core.py': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                                   'git_blob_sha': '09bde3df2e2d33701141da7cec6eb53a6562f91c',
                                   'local': 'scripts--build_battle_core.py',
                                   'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                   'sha256': 'e83f659b912e4f61f790ef648f30dd7e669f737da84f326c234dc491a6d135c0',
                                   'size': 239192,
                                   'source': 'scripts/build_battle_core.py',
                                   'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/scripts/build_battle_core.py'}}

def future_access_projection(trace,count):
 """Byte保存はread-before-write、epochは将来read/writeの双方に依存する。"""
 access=set();out=[None]*count
 for kind,a,n in reversed(trace):
  if kind in('read','write'):access.update(range(a,a+n))
  elif kind=='boundary':out[a]=live.coalesce(access)
  else:need(False,'閉じたaccess trace')
 need(all(x is not None for x in out),'全境界future access');return out

EXPECTED_HITS=[dict(address=HIT,target=167707402,kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',size=4,
 sha256='07c248320b72bb4ce107d00d6b78fa17079db02cc08a3a42f41e3654a57cd6cd',classification='UNCLASSIFIED',
 accepted=False,reason='no_complete_typed_asset_consumer_witness',owner_candidates=[])]
ROOT=dict(kind='registered_special057_task_main_state_producer_text',special_dispatch=0x080697BC,
 special_id=87,special_cell=0x081631C4,constructor=ENTRY,task=TASK,task_writer=0x08076BCE,
 task_reader=0x08076D28,main_setter=0x08000544,main_writer=0x08000546,main_reader=0x08000530,
 callback=CB,state_address=STATE,state_table=0x0916744C,state_producer=0x09103F22,
 selected_state=7,state_cell=0x09167468,print_call=0x09103EAE,printer=0x0812ED24,
 selected_calls=[0x09103870,0x09103886],window_ids=[5,6],font=0,speed=0,
 current_hook=0x09378A30,actual_byte_read=0x0800580E,endpoint=0x0910388A)
CLAIMS=dict(conditional_registered_api_entry=True,complete_selected_caller_path=True,
 actual_task_registration_and_reader=True,actual_main_registration_and_reader=True,
 state0_to7_actual_producer=True,complete_selected_text_consumption=True,
 task_or_main_pointer_host_seeded=False,state7_host_seeded=False,text_pointer_host_seeded=False,
 same_epoch_required_at_actual_uses=True,nonlive_ram_erased_at_each_boundary=True,
 current_candidate_measurement_required=True,actual_runtime_execution_observed=False,
 full_natural_event_prefix_proven=False,all_opaque_callee_effects_proven=False,
 universal_heap_or_irq_lifetime_proven=False,full_graphics_success_proven=False,
 whole_text_table_classified=False,padding_classified=False,indirect_reference_completeness_proven=False,
 retirement_proven=False,donor_eligible=False,donor_leased=False,owner_transfer_proven=False)
CONTRACT=dict(
 entry_ja='special dispatcher080697BCの有効contextからScriptReadHalfword戻り87を有限入力条件にする。実cell081631C4、完全constructor、source VarSetのVegaFacilityStateSet(field3,0)rewrite、FadeScreenとCreateTaskを通す。自然event選択・fade全待機は未証明。',
 task_ja='初期有効空16slotを条件にしcallback/dataはpoison165。実CreateTask/InsertTask/memsetの登録とzero writerを実行し、同slotの実RunTasks reader/BXからTask_Initへ入る。非active paletteとVar8000=0、Calloc20正常有効戻り、facility getter0を条件化。独立layout20に実pointer/type/facility/tier/countを書き、実DestroyTaskで退役する。',
 main_ja='SetMainCallback2が実callbackとstate0を書き、実main readerから8frameを呼ぶ。各frameの本体全選択命令とgraphics call siteを繋ぎ実state++で0→7を生成。state7/table/text pointerはhost注入しない。main link gates0、tilemap4096正常allocation、temp buffer free0、InitWindows成功を有限条件にしcallee全効果は未証明。',
 mmio_ja='state0の実DmaFill descriptor書込3件は命令と引数だけをモデル化する。DMA完了、VRAM/OAM/PLTT消去・IRQ動作・画面成功は証明しない。SetGpuReg13callの正常ABIを条件化する。',
 windows_ja='source全21WindowTemplate+sentinelを独立serializeし実table09167530へ一致させる。InitWindows正常戻りでsource window0..20が有効になる有限resource条件。InitWindows前に旧window epochを要求しない。21clearと施設名/tier表示は明示opaque正常returnで、対象2callはWindowPrint→AddTextPrinter→現hook→font0→RenderTextへ実行する。',
 font_ja='初期gFonts03003DD0=083E30E8、キーhalfword0、gTextFlags0を有限API resource入力とする。font0の実function fieldとstruct offsetをsourceに束縛。JP実height12は有限resource field条件で、英pretのmaxLetterHeight13から独立生成された値とは扱わない。高さは改行のY算術だけに使い消費先を選ばない。',
 opaque_ja='全callの正常ABIはr4..r11/SP/LR、明示scalar結果、必要resourceだけ。caller-saved/NZCVをUnknownへ消去。Callocは新20bytezero allocation、glyph幅はunspecified u8、GetFontAttribute結果はunspecified。全RAM/heap/task/IRQを保存する条件にしない。',
 epoch_ja='各opaque/API境界のbyte保存は実future read-before-write RAM/stack最小射影。別のfuture read/write射影から存続allocation/task/main/stackの必要epochを決め、window/printerは実生成と最終useの有限世代に限定。temp printerは実hook active writerからCopyWindowToVram直前のwindowId読取08002DAAまでで、後続CopyWindowToVramでは旧printer epochを要求しない。生成前や実DestroyTask後の旧epochは要求しない。全非live消去replayで同path/producer/全15textbyteを再現する。',
 minimum_ja='Current10byteは改行254とEOS、Max5byteはEOSを含め全byteを実0800580E LDRBで読む。第2WindowPrint正常復帰の0910388Aで停止する。分類は境界hit0914100Dの4byteだけ。自然全prefix、全callee、普遍IRQ/heap寿命、donor/退役/owner移管は未主張。')

def source_semantics(sources):
 texts={k:layout.without_comments(v.decode('utf-8-sig'))for k,v in sources.items()}
 src=texts['cfru-src--frontier_records.c']
 fields,size,_=layout.layout(layout.definition(src,'FrontierRecords'),{'STAR_SPRITE_COUNT':4})
 expected={'tilemapPtr':(0,4),'tierList':(4,4),'battleType':(8,1),'battleTier':(9,1),'battleTierId':(10,1),
  'numTiers':(11,1),'facilityNum':(12,1),'scrollArrowDummy':(14,2),'starSpriteIds':(16,4)}
 need(size==20 and fields=={k:dict(offset=a,size=n)for k,(a,n)in expected.items()},'独立FrontierRecords layout20')
 enums=re.search(r'enum Windows\s*\{([^}]+)\}',src);need(enums is not None,'window enum source')
 names=[x.strip()for x in enums[1].split(',')if x.strip()]
 need(names[:21]==[k for k,_ in WINDOW_VALUES]and names[21:]==['WINDOW_COUNT'],'独立全21window enum')
 need(names.index('WIN_CURRENT_STREAK_LEVEL_50')==5 and names.index('WIN_MAX_STREAK_LEVEL_50')==6,'source window5/6')
 body=src.split('static const struct WindowTemplate sFrontierRecordsWinTemplates[WINDOW_COUNT + 1] =')[1].split('};',1)[0]
 rows=[]
 for name,body2 in re.findall(r'\[(WIN_\w+)\]\s*=\s*\{([^}]+)\}',body):
  values=dict((k,int(v))for k,v in re.findall(r'\.(\w+)\s*=\s*(\d+)',body2))
  need(set(values)=={'bg','tilemapLeft','tilemapTop','width','height','paletteNum','baseBlock'},'全window scalar fields')
  rows.append((name,tuple(values[k]for k in('bg','tilemapLeft','tilemapTop','width','height','paletteNum','baseBlock'))))
 need(rows==WINDOW_VALUES and body.count('DUMMY_WIN_TEMPLATE')==1,'独立全window serializer')
 wfields,wsize,_=layout.layout(layout.definition(texts['cfru-window.h'],'WindowTemplate'),{})
 need(wsize==8 and wfields['baseBlock']==dict(offset=6,size=2),'window struct stride8')
 dummy=re.search(r'#define DUMMY_WIN_TEMPLATE\s+([^#]+?)\n\}',texts['cfru-window.h'])
 need(dummy is not None and re.findall(r'0xFF|\b0\b',dummy[0])==['0xFF']+['0']*6,'sentinel七field')
 textsrc=sources['cfru-strings--frontier_records.string'].decode()
 cmap={line[3:]:int(line[:2],16)for line in sources['cfru-charmap.tbl'].decode('utf-8-sig').splitlines()if len(line)>=4 and line[2]=='='}
 for label,a,s in TEXT_DECLS:
  line=re.search(r'^#org @'+label+r'\s*\n([^\n]+)',textsrc,re.M);need(line is not None and line[1]==s,'独立text宣言 '+label)
  need(serialize_text(s,cmap)==TEXT_PARTS[a],'独立charmap serialize '+label)
 need({k:cmap[k]for k in CHARMAP}==CHARMAP,'全文固定charmapの選択値')
 tower=re.search(r'const u8 gBattleTowerTiers\[\]\s*=\s*\{([^}]+)\}',texts['cfru-src--frontier.c'])
 need(tower is not None,'tier table source');tiers=[x.strip()for x in tower[1].split(',')if x.strip()]
 need(len(tiers)==8 and tiers[0]=='BATTLE_FACILITY_STANDARD','source tier count8/first')
 formats=re.search(r'enum BattleTowerFormats\s*\{([^}]+)\}',texts['cfru-frontier.h']);need(formats is not None and formats[1].strip().startswith('BATTLE_FACILITY_STANDARD,'),'first tier enum0')
 font=re.search(r'\[FONT_SMALL\]\s*=\s*\{([^}]+)\}',texts['pret-new_menu_helpers.c']);need(font is not None and '.fontFunction = FontFunc_Small' in font[1]and '.maxLetterHeight = 13' in font[1],'公開font0 role/JP差分明示')
 fontbody=layout.definition(texts['pret-text.h'],'FontInfo').replace('u16 (*fontFunction)(struct TextPrinter *x);','u32 fontFunction;')
 ff,fs,_=layout.layout(fontbody,{})
 need(fs==12 and ff['fontFunction']==dict(offset=0,size=4)and ff['maxLetterHeight']==dict(offset=5,size=1),'独立FontInfo stride12/height offset5')
 return dict(frontier_struct_size=size,frontier_fields=fields,window_count=21,window_stride=8,
  window_template_serialized_bytes=176,tier_count=8,tier0=0,selected_text_bytes=15,
  font0_height_observed_resource_condition=12,font0_height_public_english_source=13,
  font0_height_independent_source_value=False,source_comments_used=False,static_decode_used_as_semantic_source=False)

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'固定source閉集合')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'全文source '+name)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'固定Git blob '+name)
 roles={
  'cfru-routinepointers':['sp057_ShowFrontierRecords 081631C4'],
  'cfru-src--frontier_records.c':['void sp057_ShowFrontierRecords(void)','VarSet(VAR_BATTLE_FACILITY_BATTLE_TYPE, BATTLE_FACILITY_SINGLE);','CreateTask(Task_InitFrontierRecords, 0);','sFrontierRecordsPtr = Calloc(sizeof(struct FrontierRecords));','sFrontierRecordsPtr->battleTier = sFrontierRecordsPtr->tierList[0];','SetMainCallback2(CB2_FrontierRecords);','switch (gMain.state)','gMain.state++;','PrintCurrentRecords();','WindowPrint(WIN_CURRENT_STREAK_LEVEL_50, 0, 0, 4, &generalColour, 0, gText_CurrentStreak);','WindowPrint(WIN_MAX_STREAK_LEVEL_50, 0, 0, 4, &generalColour, 0, gText_MaxStreak);','.bgColor = 0,','.fgColor = 2,','.shadowColor = 3,'],
  'scripts--build_battle_core.py':['VEGA_FACILITY_STATE_NUMBER','VEGA_FACILITY_STATE_BATTLE_TYPE','text, count = set_pattern.subn(rf"VegaFacilityStateSet({name}, \\1)", text)','#define BATTLE_FACILITY_NUM VegaFacilityStateGet(VEGA_FACILITY_STATE_NUMBER)'],
  'pret-scrcmd.c':['&gSpecials[ScriptReadHalfword(ctx)]','(*specialPtr)();'],
  'pret-task.c':['gTasks[i].func = func;','memset(gTasks[i].data, 0, sizeof(gTasks[i].data));','gTasks[taskId].func(taskId);','gTasks[taskId].isActive = FALSE;'],
  'pret-main.c':['gMain.callback2 = callback;','gMain.state = 0;','gMain.callback2();'],
  'pret-menu2.c':['void AddTextPrinterParameterized3(','printer.currentChar = str;','printer.fgColor = color[1];','AddTextPrinter(&printer, speed, NULL);'],
  'pret-text_printer.c':['sTempTextPrinter.printerTemplate = *textSubPrinter;','sTempTextPrinter.textSpeed = 0;','RenderFont(&sTempTextPrinter)','gFonts[textPrinter->printerTemplate.fontId].fontFunction(textPrinter)'],
  'pret-text.c':['u16 FontFunc_Small(','textPrinter->subUnion.sub.glyphId = FONT_SMALL;','currChar = *textPrinter->printerTemplate.currentChar;','case CHAR_NEWLINE:','case EOS:'],
  'qol_production_hooks.S':['VegaQolProduction_FixInstantTextSpeedHook:','cmp r5, #0x7f','bne 1f','ldr r0, =0x02020010','strb r1, [r0, #27]','ldr r3, =0x08002d15'],
  'cfru-string.py':['stringToWrite += "0xFF\\n\\n"','def ProcessString('],
  'BPRJ.ld':['WindowPrint = 0x812ED24 | 1;','SetMainCallback2 = 0x8000544 | 1;','CreateTask = 0x8076BB4 | 1;']}
 for name,tokens in roles.items():
  for token in tokens:need(token in sources[name].decode(),'独立source role '+name+' '+token)
 return source_semantics(sources)

def bind_semantics(raw,sources):
 bind(raw);d.signed(raw,ALL_WINDOWS);semantics=source_semantics(sources)
 return dict(instructions=len(INS),instruction_bytes=sum(i.size for i in INS.values()),source_semantics=semantics,
  public_source_count=len(SOURCE_IDS),source_serialized_text=True,rom_observed_values_as_source=False)

def evidence_template(hit):
 need(type(hit)is int and hit==HIT,'Frontier限定hit')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=HIT,size=4),
  texts=copy.deepcopy(TEXTS),actual_byte_consumer=0x0800580E,all_hit_bytes_consumed=True,
  includes_complete_eos=True,input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HIT)),'閉じたFrontier最小4byte witness');return HIT,4

def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'不変source窓');return copy.deepcopy(ALL_WINDOWS)

def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS];need(exact(selected,EXPECTED_HITS),'親hit全field一致')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
  source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),
  windows=copy.deepcopy(ALL_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE),texts=copy.deepcopy(TEXTS))
prepare_review=make_review

def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profile','texts'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'現候補/旧診断分離')
 for key,val in[('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE),('texts',TEXTS)]:need(exact(review[key],val),'閉じたreview '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS)and exact(selected,review['hits']),'親unknown全field保存')
 protected_windows(review);sources_bind(review,sources);serialization=bind_semantics(raw,sources);d.signed(raw,selected)
 composition=compose_selected(raw);e=evidence_template(HIT);a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_FRONTIER_RECORDS_ROOTS',count=1,hits=list(HITS),
  serialization=serialization,composition=composition,protected_windows=len(ALL_WINDOWS),protected_bytes=sum(w['size']for w in ALL_WINDOWS),**copy.deepcopy(CLAIMS))

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate');return _regions(raw,inherited,review,sources)
validate=_regions
