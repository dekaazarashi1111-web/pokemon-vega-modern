"""実ChooseMove APIから登録text境界へ。手書き意味spec、公開serializer、有限条件だけ。"""
import ast,copy,csv,hashlib,io,json,re
import pr16_dex_hof_callback_party as p
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as live_engine
import pr16_dex_hof_animation_registered_roots as machine_engine
import pr16_dex_hof_toxic_orb_roots as layout_engine
import pr16_dex_hof_choose_limit_roots as charset_engine
import pr16_dex_hof_donor as d
from pr16_dex_hof_extra_roots import encoded,exact
need,identity,chunk=p.need,p.identity,p.chunk
CANDIDATE,DIAGNOSTIC=p.CANDIDATE,p.DIAGNOSTIC
KIND='registered_choosemove_minimum_text_boundaries'
TYPE_CATEGORY='data'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x09143266,0x09143415)
HELD_HITS=()
ENTRY=0x0802E1EC
NEWBS,CONTEXT,CHOOSE=0x0203DFB0,0x02010000,0x02022B28
BANK,CURSOR,FLAGS,DISPLAY=0x02023B24,0x02023F5C,0x02022AAC,0x020228FC
SPECS=[]
def block(a,specs):
 for k,*x in specs:
  if k=='regmem' and type(x[0])is bool:
   ld,w,rd,rb,ro=x;x=[{(True,'word'):'ldr',(True,'half'):'ldrh',(True,'byte'):'ldrb',(False,'word'):'str',(False,'half'):'strh',(False,'byte'):'strb'}[ld,w],rd,rb,ro]
  if k=='alu'and x[0]in('tst','sbc','adc','bic','eor'):k='alu_ext'
  if k=='adrsp':k='spaddr'
  SPECS.append((a,k,tuple(x)));a+=4 if k=='call'else 2
 return a
# 公開hook・QoL magic/inverse・通常manual-input枝・BattleUI trampoline。
block(ENTRY,[('literal',3,ENTRY+4),('bx',3)])
block(0x09377B40,[('push',247,True),('literal',4,0x09377BC8),('call',0x09378BD4),
 ('mem',True,'half',3,4,0),('imm','mov',5,2),('shift','lsl',2,3,0),('alu','and',2,5),
 ('spmem',False,2,4),('literal',6,0x09377BCC),('alu','tst',3,5),('branch',0,0x09377B68),
 ('mem',True,'half',3,4,0),('shift','lsl',3,3,30),('branch',4,0x09377BA2),('call',0x09377BE6)])
block(0x09377B68,[('literal',7,0x09377BD0),('mem',True,'byte',3,7,0),('imm','cmp',3,0),('branch',0,0x09377B58)])
block(0x09377BE6,[('bx',6)])
block(0x09378BD4,[('push',112,True),('literal',4,0x09378BFC),('literal',6,0x09378C00),
 ('mem',True,'word',3,4,0),('literal',5,0x09378C04),('compare',3,6),('branch',1,0x09378BE8),
 ('mem',True,'word',3,4,4),('compare',3,5),('branch',0,0x09378BF4)])
block(0x09378BF4,[('pop',112,False),('pop',1,False),('bx',0)])
block(0x09116F90,[('literal',3,0x09116F94),('bx',3)])
block(0x092CFE58,[('literal',3,0x092CFE94),('push',112,True),('mem',True,'half',5,3,0),('call',0x092CFEB8)])
block(0x092CFEB8,[('imm','mov',2,144),('push',240,True),('movhi',6,9),('movhi',7,10),('literal',3,0x092CFEC4),('bx',3)])
# move_menu.c HandleInputChooseMove:実全prologueと入力frameのfield同期。
block(0x09116F98,[('movhi',5,8),('movhi',14,11),('shift','lsl',2,2,2),('movhi',12,2),
 ('push',224,True),('literal',3,0x09117254),('literal',5,0x09117258),('movhi',9,3),
 ('literal',3,0x0911725C),('mem',True,'byte',0,5,0),('mem',True,'word',7,3,0),('spadd',-36),
 ('spmem',False,3,12),('add',3,7,0),('addhi',12,3),('movhi',6,12),('shift','lsl',4,0,9),
 ('imm','add',4,4),('imm','sub',2,237),('addhi',4,9),('imm','sub',2,255),
 ('regmem',True,'byte',1,4,2),('shift','lsl',1,1,31),('shift','lsr',1,1,31),('mem',False,'byte',1,6,0),
 ('imm','mov',1,137),('shift','lsl',1,1,2),('movhi',12,1),('addhi',12,3),('movhi',6,12),
 ('regmem',True,'byte',1,4,2),('shift','lsl',1,1,30),('shift','lsr',1,1,31),('mem',False,'byte',1,6,0),
 ('imm','mov',1,142),('shift','lsl',1,1,2),('movhi',12,1),('addhi',12,3),('movhi',6,12),
 ('regmem',True,'byte',1,4,2),('shift','lsl',1,1,29),('shift','lsr',1,1,31),('mem',False,'byte',1,6,0),
 ('literal',1,0x09117260),('movhi',12,1),('addhi',12,3),('movhi',6,12),
 ('regmem',True,'byte',1,4,2),('shift','lsl',1,1,28),('shift','lsr',1,1,31),('mem',False,'byte',1,6,0),
 ('imm','mov',1,155),('shift','lsl',1,1,2),('movhi',12,1),('addhi',12,3),('movhi',6,12),
 ('regmem',True,'byte',1,4,2),('shift','lsl',1,1,26),('shift','lsr',1,1,31),('mem',False,'byte',1,6,0),
 ('regmem',True,'byte',2,4,2),('shift','lsl',1,2,31),('branch',5,0x09117024)])
block(0x09117024,[('shift','lsl',1,2,30),('branch',5,0x09117036)])
block(0x09117036,[('shift','lsl',1,2,29),('branch',5,0x09117048)])
block(0x09117048,[('shift','lsl',1,2,28),('branch',5,0x09117058)])
block(0x09117058,[('shift','lsl',2,2,26),('branch',5,0x09117068)])
block(0x09117068,[('literal',3,0x09117268),('movhi',8,3),('call',0x09119120),
 ('imm','mov',3,145),('shift','lsl',3,3,2),('movhi',12,3),('imm','sub',3,239),('imm','sub',3,255),
 ('regmem',True,'byte',3,4,3),('add',7,7,0),('addhi',7,12),('spmem',True,6,12),('mem',False,'byte',3,7,0),
 ('mem',True,'byte',0,5,0),('mem',True,'word',7,6,0),('call',0x0911912A),
 ('literal',3,0x0911726C),('movhi',12,3),('imm','sub',3,227),('imm','sub',3,255),
 ('regmem',True,'byte',3,4,3),('add',7,7,0),('addhi',7,12),('mem',False,'byte',3,7,0),
 ('mem',True,'byte',0,5,0),('mem',True,'word',7,6,0),('call',0x0911912A),
 ('imm','mov',3,156),('shift','lsl',3,3,2),('movhi',12,3),('imm','sub',3,252),('imm','sub',3,255),
 ('regmem',True,'byte',3,4,3),('add',7,7,0),('addhi',7,12),('mem',False,'byte',3,7,0),
 ('literal',3,0x09117270),('movhi',10,3),('mem',True,'word',3,3,0),('shift','lsl',3,3,31),('branch',5,0x09117148)])
block(0x09117148,[('imm','mov',7,1),('imm','mov',2,1),('shift','lsl',1,7,0),('literal',3,0x0911728C),
 ('mem',True,'half',3,3,46),('movhi',8,2),('alu','and',1,3),('alu','tst',7,3),('branch',0,0x0911715C)])
block(0x0911715C,[('imm','mov',2,2),('alu','tst',2,3),('branch',1,0x091171D8),
 ('shift','lsl',1,3,26),('branch',4,0x09117168),('jump',0x09117432)])
block(0x09117432,[('shift','lsl',1,3,27),('branch',5,0x09117484)])
block(0x09117484,[('shift','lsl',1,3,25),('branch',4,0x0911748A),('jump',0x09117758)])
block(0x09117758,[('shift','lsl',1,3,24),('branch',4,0x09117818),('shift','lsl',2,3,29),('branch',4,0x09117762),('jump',0x091179DC)])
block(0x091179DC,[('shift','lsl',2,3,28),('branch',5,0x091179E2),('jump',0x09117B88)])
# START:Z関数を実行してfalse、Mega関数のcanMegaEvolve==false、DYNAMAX flag。
block(0x09117B88,[('call',0x09115A88),('imm','cmp',0,0),('branch',0,0x09117B94)])
block(0x09117B94,[('call',0x09115914),('imm','cmp',0,0),('branch',0,0x09117BA0)])
block(0x09117BA0,[('movhi',3,10),('mem',True,'word',3,3,0),('shift','lsl',3,3,1),('branch',4,0x09117BAC)])
block(0x09115914,[('push',112,True),('literal',4,0x091159B4),('mem',True,'byte',1,4,0),
 ('literal',2,0x091159B8),('shift','lsl',3,1,9),('add',3,3,2),('imm','mov',2,82),
 ('regmem',True,'byte',0,3,2),('imm','cmp',0,0),('branch',0,0x09115960)])
block(0x09115960,[('pop',112,True)])
# Z分岐。dynamaxed=1の場合は正常falseへ実早期return。ResetではIsTerastal正常戻り0条件。
block(0x09115A88,[('push',240,True),('movhi',7,10),('movhi',6,9),('movhi',14,11),('movhi',5,8),
 ('literal',3,0x09115D9C),('movhi',9,3),('push',224,True),('literal',7,0x09115DA0),('literal',6,0x09115DA4),
 ('mem',True,'byte',0,7,0),('regmem',True,'byte',3,6,0),('shift','lsl',4,0,9),('imm','add',4,4),
 ('imm','add',3,44),('addhi',4,9),('shift','lsl',3,3,1),('regmem',True,'half',3,3,4),('movhi',11,3),
 ('literal',3,0x09115DA8),('mem',True,'word',2,3,0),('movhi',8,3),('imm','mov',3,146),
 ('shift','lsl',3,3,2),('regmem',True,'byte',3,2,3),('imm','mov',2,8),('shift','lsl',1,2,0),
 ('alu','and',1,3),('movhi',10,1),('spadd',-20),('alu','tst',2,3),('branch',1,0x09115B72),
 ('imm','mov',2,16),('imm','mov',3,84),('shift','lsl',5,2,0),('regmem',True,'byte',3,4,3),
 ('alu','and',5,3),('alu','tst',2,3),('branch',0,0x09115AE6),('movhi',0,10),('spadd',20),
 ('pop',240,False),('movhi',11,7),('movhi',10,6),('movhi',9,5),('movhi',8,4),('pop',240,True)])
# Maxの全4 cursor/text clear prefix・実move12byte record・effect dispatch。
block(0x09117BAC,[('mem',True,'byte',2,5,0),('shift','lsl',3,2,9),('imm','add',3,4),('addhi',3,9),
 ('shift','lsl',1,3,0),('movhi',12,1),('spmem',False,3,28),('literal',3,0x09117D64),('movhi',8,3),
 ('regmem',True,'byte',3,3,2),('imm','add',3,48),('shift','lsl',3,3,1),('addhi',3,12),
 ('mem',True,'half',3,3,4),('spmem',False,3,16),('spmem',True,3,12),('mem',True,'word',2,3,0),
 ('literal',3,0x09117D4C),('regmem',True,'byte',2,2,3),('imm','mov',3,2),('shift','lsl',1,2,0),
 ('alu','and',1,3),('alu','tst',2,3),('branch',0,0x09117BDE)])
block(0x09117BDE,[('spmem',True,3,16),('imm','cmp',3,0),('branch',1,0x09117BE8)])
block(0x09117BE8,[('literal',3,0x09117D50),('movhi',10,3),('literal',3,0x09117D54),('literal',4,0x09117D5C),
 ('spmem',False,3,20),('literal',3,0x09117D58),('spmem',False,3,24),('shift','lsl',3,4,0),
 ('shift','lsl',4,1,0),('movhi',11,3),('literal',7,0x09117D60),('spmem',True,6,12),
 ('shift','lsl',0,4,0),('spmem',True,3,20),('call',0x09119120),('spmem',True,1,24),
 ('movhi',0,11),('call',0x09119128),('addi',1,4,3),('shift','lsl',1,1,24),('imm','add',4,1),
 ('movhi',0,11),('shift','lsr',1,1,24),('shift','lsl',4,4,24),('call',0x0911912E),
 ('shift','lsr',4,4,24),('imm','cmp',4,4),('branch',1,0x09117C00),('imm','mov',2,12),
 ('spmem',True,1,16),('alu','mul',1,2),('literal',3,0x09117D70),('add',3,3,1),('mem',True,'byte',3,3,11),
 ('movhi',4,11),('movhi',11,3),('imm','mov',3,255),('mem',False,'byte',3,4,0),('movhi',3,11),
 ('spmem',False,6,12),('imm','cmp',3,48),('branch',9,0x09117C44)])
block(0x09117C44,[('literal',2,0x09117D94),('shift','lsl',3,3,2),('regmem',True,'word',3,2,3),('movhi',15,3)])
block(0x09117FDA,[('shift','lsl',0,4,0),('literal',1,0x091180FC),('call',0x09119128)])
block(0x09117FE4,[('shift','lsl',0,4,0),('literal',1,0x09118100),('call',0x09119128)])
for a,reg in [(0x09119120,3),(0x09119128,7),(0x0911912A,8),(0x0911912E,10)]:block(a,[('bx',reg)])
# StringCopyのsource1byte読取とEOSまでを完全実行。表示は不要。
block(0x08008900,[('push',0,True),('addi',3,0,0),('jump',0x0800890C),('mem',False,'byte',2,3,0),
 ('imm','add',3,1),('imm','add',1,1),('mem',True,'byte',2,1,0),('addi',0,2,0),('imm','cmp',0,255),
 ('branch',1,0x08008906),('imm','mov',0,255),('mem',False,'byte',0,3,0),('addi',0,3,0),('pop',2,False),('bx',1)])
WORDS={ENTRY+4:0x09377B41,0x09377BC8:0x0300315E,0x09377BCC:0x09116F91,0x09377BD0:0x0203B63D,
 0x09378BFC:0x0203B5E8,0x09378C00:0x51504F4C,0x09378C04:0xAEAFB0B3,
 0x09116F94:0x092CFE59,0x092CFE94:0x0300315E,0x092CFEC4:0x09116F99,
 0x09117254:CHOOSE-4,0x09117258:BANK,0x0911725C:NEWBS,0x09117260:590,0x09117268:0x08074969,
 0x0911726C:598,0x09117270:FLAGS,0x0911728C:0x03003130,
 0x091159B4:BANK,0x091159B8:CHOOSE,
 0x09115D9C:CHOOSE-4,0x09115DA0:BANK,0x09115DA4:CURSOR,0x09115DA8:NEWBS,
 0x09117D4C:609,0x09117D50:0x080D980D,0x09117D54:0x08030181,0x09117D58:0x09001CB5,
 0x09117D5C:DISPLAY,0x09117D60:0x08008901,0x09117D64:CURSOR,0x09117D70:0x090421F4,
 0x09117D94:0x09168404,0x0916848C:0x09117FE4,0x09168490:0x09117FDA,
 0x091180FC:0x09143418,0x09118100:0x09143407}
TEXTS=[dict(address=0x09143262,size=7,label='gText_NoContact',text='ひせっしょく'),
 dict(address=0x09143269,size=16,label='gText_ResetStats',text='さがった のうりょくを もどす'),
 dict(address=0x09143407,size=17,label='gText_MaxMoveHealTeam',text='みかたの たいりょくを かいふく'),
 dict(address=0x09143418,size=17,label='gText_MaxMoveSpite',text='さいごの わざのPPを 2へらす')]
CASES={'heal':dict(text=2,key=8,move=984,effect=34,endpoint=0x09117FEC),
 'spite':dict(text=3,key=8,move=988,effect=35,endpoint=0x09117FE2)}
def memory(case):
 need(case in CASES,'閉じた選択profile');c=CASES[case];m={}
 for a,n,v in[(0x0203B5E8,4,0x51504F4C),(0x0203B5EC,4,0xAEAFB0B3),(0x0203B63D,1,0),
  (0x0300315E,2,c['key']),(0x0300315C,2,0),(NEWBS,4,CONTEXT),(BANK,1,0),(CURSOR,1,0),(FLAGS,4,0x40000000),
  (CHOOSE+82,1,0),(CHOOSE+84,1,16 if case in('heal','spite')else 0),(CHOOSE+86,1,0),(CHOOSE+88,2,65535 if case=='reset'else 0),(CHOOSE+100,2,c['move']),
  (CHOOSE+116,1,0),(CHOOSE+117,1,0),(CONTEXT+584,1,0),(CONTEXT+609,1,0),(CHOOSE,2,97),(CHOOSE+76,1,0),(0x03003DD0,4,0x083E30E8),(0x03003E90,1,0)]:rt.setmem(m,a,n,v)
 return m
# START/Z status:実clear loop・Z effect1 tableからResetStatsを選ぶ。
block(0x09115AE6,[('call',0x091303AC),('movhi',3,11),('imm','cmp',3,0),('branch',0,0x09115AD6),
 ('imm','cmp',0,0),('branch',1,0x09115AD6),('literal',3,0x09115DAC),('spmem',False,3,8),
 ('literal',3,0x09115DB0),('spmem',False,3,12),('literal',3,0x09115DB4),('movhi',10,3),
 ('literal',3,0x09115DB8),('spmem',False,3,0),('literal',3,0x09115DBC),('spmem',False,3,4),
 ('movhi',3,10),('movhi',10,4),('shift','lsl',4,3,0),('shift','lsl',0,5,0),('spmem',True,3,8),
 ('call',0x09119120),('spmem',True,1,12),('spmem',True,3,0),('shift','lsl',0,4,0),('call',0x09119120),
 ('addi',1,5,3),('shift','lsl',1,1,24),('imm','add',5,1),('shift','lsl',0,4,0),('spmem',True,3,4),
 ('shift','lsr',1,1,24),('shift','lsl',5,5,24),('call',0x09119120),('shift','lsr',5,5,24),
 ('imm','cmp',5,4),('branch',1,0x09115B0E),('shift','lsl',3,4,0),('literal',1,0x09115DC0),
 ('movhi',4,10),('movhi',10,3),('mem',True,'byte',3,7,0),('regmem',True,'byte',2,6,3),
 ('comparehi',11,1),('branch',1,0x09115B84),('shift','lsl',2,2,1),('regmem',True,'half',1,2,4),
 ('shift','lsl',2,1,1),('literal',3,0x09115DC4),('add',2,2,1),('shift','lsl',2,2,2),('add',3,3,2),
 ('mem',True,'byte',3,3,11),('imm','cmp',3,5),('branch',1,0x09115B5E)])
block(0x09115B5E,[('imm','mov',2,255),('movhi',1,10),('mem',False,'byte',2,1,0),
 ('imm','cmp',3,28),('branch',9,0x09115B6A)])
block(0x09115B6A,[('literal',1,0x09115DC8),('shift','lsl',2,3,2),('regmem',True,'word',2,1,2),('movhi',15,2)])
block(0x09115D36,[('movhi',0,10),('literal',1,0x09115E2C),('spmem',True,3,0),('call',0x09119120)])
# L詳細:Z/Max viewing0・details0、全4clearとmove-name表示の実call経由。
block(0x091179E2,[('shift','lsl',2,3,23),('branch',5,0x091179E8),('jump',0x09117C68),
 ('shift','lsl',3,3,22),('branch',4,0x091179F0)])
block(0x091179F0,[('imm','mov',2,146),('spmem',True,3,12),('mem',True,'word',3,3,0),
 ('shift','lsl',2,2,2),('regmem',True,'byte',2,3,2),('shift','lsl',1,2,28),('branch',5,0x09117A02)])
block(0x09117A02,[('literal',1,0x09117D4C),('regmem',True,'byte',3,3,1),('shift','lsl',3,3,30),
 ('branch',5,0x09117A0E)])
block(0x09117A0E,[('mem',True,'byte',3,5,0),('shift','lsl',3,3,9),('imm','add',3,4),
 ('shift','lsl',1,2,0),('addhi',9,3),('imm','mov',3,32),('alu','and',1,3),('alu','tst',2,3),('branch',0,0x09117A22)])
block(0x09117A22,[('literal',3,0x09117D50),('movhi',10,3),('literal',3,0x09117D54),('spmem',False,3,20),
 ('literal',3,0x09117D58),('spmem',False,3,24),('shift','lsl',3,5,0),('literal',4,0x09117D5C),
 ('shift','lsl',5,1,0),('movhi',8,4),('movhi',11,3),('literal',7,0x09117D60),('spmem',True,6,12),
 ('shift','lsl',4,5,24),('shift','lsr',4,4,24),('spmem',True,3,20),('shift','lsl',0,4,0),('call',0x09119120),
 ('spmem',True,1,24),('movhi',0,8),('call',0x09119128),('addi',1,4,3),('shift','lsl',1,1,24),
 ('movhi',0,8),('shift','lsr',1,1,24),('imm','add',5,1),('call',0x0911912E),('imm','cmp',5,4),('branch',1,0x09117A3C),
 ('literal',3,0x09117D64),('movhi',4,8),('movhi',8,3),('movhi',5,11),('movhi',2,8),
 ('mem',True,'byte',3,5,0),('regmem',True,'byte',0,2,3),('spmem',False,6,12),('call',0x09115750),
 ('shift','lsl',0,4,0),('imm','mov',1,3),('call',0x0911912E),('movhi',2,8),('mem',True,'byte',3,5,0),
 ('regmem',True,'byte',3,2,3),('addhi',3,9),('imm','add',3,76),('mem',True,'byte',3,3,0),
 ('literal',0,0x09117D68),('imm','cmp',3,0),('branch',0,0x09117A92)])
block(0x09117A92,[('imm','mov',1,4),('call',0x0911912E)])
# BattlePutTextOnWindow。window4既存resource・公開templateの全fieldを実copy。
block(0x080D980C,[('push',240,True),('spadd',-16),('addi',5,0,0),('shift','lsl',1,1,24),
 ('shift','lsr',7,1,24),('imm','mov',0,192),('alu','and',0,7),('addi',4,0,0),('imm','mov',0,63),
 ('alu','and',7,0),('imm','mov',0,128),('alu','and',0,4),('imm','cmp',0,0),('branch',1,0x080D9848),
 ('addi',0,7,0),('call',0x08003F6C),('addi',0,7,0),('imm','mov',1,3),('call',0x08003EEC),
 ('literal',0,0x080D9868),('shift','lsl',1,7,1),('add',1,1,7),('shift','lsl',1,1,2),
 ('add',1,1,0),('mem',True,'byte',1,1,0),('addi',0,7,0),('call',0x08004428),
 ('imm','mov',0,64),('alu','and',0,4),('imm','cmp',0,0),('branch',0,0x080D9870)])
block(0x080D9870,[('movhi',3,13),('literal',1,0x080D98F4),('shift','lsl',2,7,1),('add',0,2,7),
 ('shift','lsl',0,0,2),('add',0,0,1),('mem',True,'byte',0,0,1),('mem',False,'byte',0,3,5),
 ('addi',6,2,0),('spmem',False,5,0),('movhi',0,13),('mem',False,'byte',7,0,4),('movhi',1,13),
 ('literal',0,0x080D98F4),('movhi',12,0),('add',3,6,7),('shift','lsl',3,3,2),('addhi',3,12),
 ('mem',True,'byte',0,3,2),('mem',False,'byte',0,1,6),('mem',True,'byte',0,3,3),('mem',False,'byte',0,1,7),
 ('movhi',0,13),('mem',True,'byte',0,0,6),('mem',False,'byte',0,1,8),('movhi',0,13),('mem',True,'byte',0,0,7),
 ('mem',False,'byte',0,1,9),('mem',True,'byte',0,3,4),('mem',False,'byte',0,1,10),
 ('mem',True,'byte',0,3,5),('mem',False,'byte',0,1,11),('movhi',4,13),('mem',True,'byte',2,4,12),
 ('imm','mov',1,16),('alu','neg',1,1),('addi',0,1,0),('alu','and',0,2),('mem',False,'byte',0,4,12),
 ('movhi',2,13),('mem',True,'byte',0,3,7),('shift','lsl',0,0,4),('imm','mov',5,15),('mem',False,'byte',0,2,12),
 ('mem',True,'byte',2,3,8),('addi',0,5,0),('alu','and',0,2),('mem',True,'byte',2,4,13),('alu','and',1,2),
 ('alu','orr',1,0),('mem',False,'byte',1,4,13),('movhi',2,13),('mem',True,'byte',0,3,9),('shift','lsl',0,0,4),
 ('alu','and',1,5),('alu','orr',1,0),('mem',False,'byte',1,2,13),('movhi',3,12),('imm','cmp',7,24),('branch',1,0x080D98FC)])
block(0x080D98FC,[('literal',0,0x080D992C),('mem',True,'byte',1,0,0),('imm','mov',2,2),('alu','orr',1,2),
 ('mem',False,'byte',1,0,0),('addi',4,0,0),('literal',1,0x080D9930),('mem',True,'word',2,1,0),
 ('imm','mov',0,2),('alu','and',0,2),('addi',5,1,0),('imm','cmp',0,0),('branch',1,0x080D9924),
 ('imm','mov',0,128),('shift','lsl',0,0,9),('alu','and',2,0),('imm','cmp',2,0),('branch',0,0x080D9934)])
block(0x080D9934,[('mem',True,'byte',1,4,0),('imm','mov',0,5),('alu','neg',0,0),('alu','and',0,1),
 ('mem',False,'byte',0,4,0),('imm','cmp',7,0),('branch',0,0x080D9946),('imm','cmp',7,24),('branch',1,0x080D996C)])
block(0x080D996C,[('add',0,6,7),('shift','lsl',0,0,2),('add',0,0,3),('mem',True,'byte',3,0,6),
 ('mem',True,'byte',1,4,0),('imm','mov',0,2),('alu','neg',0,0),('alu','and',0,1),('mem',False,'byte',0,4,0),
 ('movhi',0,13),('addi',1,3,0),('imm','mov',2,0),('call',0x08002CF0),('spadd',16),('pop',240,False),('pop',1,False),('bx',0)])
WORDS.update({0x09115DAC:0x08030181,0x09115DB0:0x09001CB5,0x09115DB4:DISPLAY,
 0x09115DB8:0x08008901,0x09115DBC:0x080D980D,0x09115DC0:0xFFFF,0x09115DC4:0x090421F4,
 0x09115DC8:0x09168250,0x09168254:0x09115D36,0x09115E2C:0x09143269,0x09117D68:0x09143262,
 0x08005AE8:0x08005B04,0x080D9868:0x083C49F8,0x080D98F4:0x083C49F8,0x080D992C:0x03003E90,0x080D9930:FLAGS})
CASES.update({'reset':dict(text=1,key=8,move=97,effect=1,endpoint=0x09115D40),
 'contact':dict(text=0,key=512,move=97,effect=1,endpoint=0x09117A98)})

block(0x08002D50,[('imm','cmp',5,0),('branch',0,0x08002D7C)])
block(0x08002DA8,[('literal',0,0x08002DC8),('mem',True,'byte',0,0,4),('imm','mov',1,2),('call',0x08003EEC)])
INS={a:p.Ins(a,k,x)for a,k,x in SPECS}
need(len(INS)==len(SPECS),'手書き意味命令非重複')
def printer_core(a):return 0x08002CF0<=a<0x08006000 or a==0x081C7ACC or 0x09378A30<=a<0x09378B50
for a,i in live_engine.INS.items():
 if printer_core(a):
  need(a not in INS or INS[a]==i,'共通printer意味非衝突');INS[a]=i
for a,v in live_engine.LITERALS.items():
 if printer_core(a):WORDS[a]=v

EXTERNAL={(0x0911706C,0x08074968):('GetBattlerSide',0),
 (0x09117088,0x08074968):('GetBattlerSide',0),(0x091170A0,0x08074968):('GetBattlerSide',0),
 (0x09117C04,0x08030180):('MoveSelectionDestroyCursorAt',None),
 (0x09117C0C,0x08008900):('unselected_empty_StringCopy',None),
 (0x09117C1C,0x080D980C):('unselected_empty_BattlePutTextOnWindow',None)}
for site,target,role,result in[
 (0x09115AE6,0x091303AC,'IsTerastal',0),
 (0x09115B12,0x08030180,'MoveSelectionDestroyCursorAt',None),
 (0x09115B1C,0x08008900,'unselected_empty_StringCopy',None),
 (0x09115B2E,0x080D980C,'unselected_empty_BattlePutTextOnWindow',None),
 (0x09117A44,0x08030180,'MoveSelectionDestroyCursorAt',None),
 (0x09117A4C,0x08008900,'unselected_empty_StringCopy',None),
 (0x09117A5A,0x080D980C,'unselected_empty_BattlePutTextOnWindow',None),
 (0x09117A72,0x09115750,'unselected_MoveNameToDisplayedStringBattle',None),
 (0x09117A7A,0x080D980C,'unselected_move_name_BattlePutTextOnWindow',None),
 (0x080D982A,0x08003F6C,'PutWindowTilemap',None),
 (0x08002DAE,0x08003EEC,'CopyWindowToVram',None),
 (0x080D9832,0x08003EEC,'CopyWindowToVram',None),
 (0x080D9844,0x08004428,'FillWindowPixelBuffer',None),
 *[(a,t,'printer_leaf',None)for a,t in live_engine.EXTERNAL if printer_core(a)]]:
 EXTERNAL[(site,target)]=(role,result)
class Machine(machine_engine.Machine):
 def read(self,a,n):
  value=super().read(a,n)
  if self.pc==0x0800890C:self.reads.append((a,n))
  return value
 def step(self,branch_choice=None):
  i=self.instructions[self.pc]
  if i.kind=='comparehi':
   self.arith(self.reg[i.args[0]],self.reg[i.args[1]],True);self.pc+=2;self.steps+=1;return
  super().step(branch_choice)
def future_resources(trace,count):
 active=set();out=[None]*count
 for kind,a,n in reversed(trace):
  if kind=='resource':active.add(a)
  elif kind=='generation':active.discard(a)
  elif kind in('read','write'):
   if a<CONTEXT+1200 and CONTEXT<a+n:active.add('battle_context_epoch_changed')
   if a<0x03007000 and 0x03006000<a+n:active.add('stack_epoch_changed')
   if a<DISPLAY+256 and DISPLAY<a+n:active.add('display_buffer_epoch_changed')
   if a<0x02020030 and 0x02020010<a+n:active.add('printer_epoch_changed')
  elif kind=='boundary':out[a]=sorted(active)
 return out

def preserve(live,writes=(),events=None,required=()):
 need(type(live)is list and all(type(w)is list and len(w)==2 and type(w[0])is int and type(w[1])is int and w[1]>0 and 0<=w[0]<w[0]+w[1]<=1<<32 for w in live),'有限future-live射影')
 events={}if events is None else events
 need(type(events)is dict and set(events)<={'battle_context_epoch_changed','stack_epoch_changed','window_epoch_changed','display_buffer_epoch_changed','printer_epoch_changed'}and all(type(v)is bool for v in events.values()),'閉じたepoch条件')
 need(not any(events.get(k,False)for k in required),'future-use resource同epoch')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(v)is int and 0<=v<1<<(8*n)and 0<=a<a+n<=1<<32,'有限opaque書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live byte破壊禁止')
 return True

def _compose(raw,case,projections=None,opaque_writes=None,epoch_events=None,resources=None):
 c=CASES[case];row=TEXTS[c['text']];trace=[];boundaries=[];groups=[];visited=[];clears=[];destroys=[]
 m=Machine(raw,ENTRY,{},memory(case),instructions=INS,trace=trace)
 while m.pc!=c['endpoint']:
  need(m.steps<10000,'有限ChooseMove命令上限')
  key=((m.reg[14]&~1)-4,m.pc)if rt.concrete(m.reg[14])else(None,m.pc)
  if m.pc in INS and key not in EXTERNAL:
   if m.pc==0x09378A3C:trace.append(('generation','printer_epoch_changed',0))
   if case=='contact' and (0x080D980C<=m.pc<=0x080D998E or printer_core(m.pc)):trace.append(('resource','window_epoch_changed',0))
   visited.append(m.pc);m.step();continue
  need(key in EXTERNAL,'非登録opaque/branch逸脱 '+str(tuple(hex(x)for x in key)))
  role,value=EXTERNAL[key]
  if role in('GetBattlerSide','IsTerastal','unselected_MoveNameToDisplayedStringBattle'):need(m.reg[0]==0,'実bank0/slot0引数')
  elif role=='unselected_move_name_BattlePutTextOnWindow':need(m.reg[:2]==[DISPLAY,3],'実非対象move-name表示')
  elif role in('PutWindowTilemap','CopyWindowToVram','FillWindowPixelBuffer'):need(m.reg[0]==4,'実window4 consumer')
  elif role=='MoveSelectionDestroyCursorAt':
   need(m.reg[0]==len(destroys)and len(destroys)<4,'実cursor0..3');destroys.append(m.reg[0])
  elif role=='unselected_empty_StringCopy':need(m.reg[:2]==[DISPLAY,0x09001CB5],'実空text clear引数')
  elif role=='unselected_empty_BattlePutTextOnWindow':
   need(m.reg[:2]==[DISPLAY,len(clears)+3]and len(clears)<4,'実window3..6 clear引数');clears.append(m.reg[1])
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if projections is not None:
   need(index<len(projections),'完全boundary射影');live=projections[index]
   writes=(opaque_writes or {}).get(key,());events=(epoch_events or {}).get(key,{})
   preserve(live,writes,events,resources[index])
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   groups.append(dict(site=key[0],target=key[1],role=role,required_fields=[dict(address=a,size=n)for a,n in live],
    normal_abi_return_required=True,required_resource_epochs=resources[index],callee_effects_proven=False))
  for reg in(0,1,2,3,12):m.reg[reg]=rt.U
  if value is not None:m.reg[0]=value
  m.flags=(rt.U,)*4;m.flag_pc=None;m.pc=m.reg[14]&~1
 expected=[(row['address']+j,1)for j in range(row['size'])]
 need(m.reads==expected,'選択text全byte/EOSの実StringCopy読取')
 need(destroys==list(range(4))and clears==list(range(3,7)),'4cursor/4window選択prefix全通過')
 if case!='contact':need(bytes(m.mem.get(DISPLAY+j,0)for j in range(row['size']))==encode_text(row['text']),'実StringCopy同buffer書込/EOS')
 return dict(steps=m.steps,trace=trace,visited=visited,boundaries=boundaries,groups=groups,
  reads=m.reads,clears=clears,destroys=destroys,endpoint=m.pc)
def compose(raw,case,opaque_writes=None,epoch_events=None):
 need(set(opaque_writes or {})<=set(EXTERNAL)and set(epoch_events or {})<=set(EXTERNAL),'未知opaque条件拒否')
 first=_compose(raw,case);need(set(opaque_writes or {})<=set(first['boundaries'])and set(epoch_events or {})<=set(first['boundaries']),'未実行site条件を黙殺しない');live=live_engine.future_live([r for r in first['trace']if r[0]in('read','write','boundary')],len(first['boundaries']))
 resources=future_resources(first['trace'],len(first['boundaries']))
 second=_compose(raw,case,live,opaque_writes,epoch_events,resources)
 for key in('reads','visited','boundaries','endpoint'):need(first[key]==second[key],'非live全消去後同一path/消費 '+key)
 return dict(case=case,instruction_steps=second['steps'],visited=second['visited'],text_reads=second['reads'],
  conditional_call_groups=second['groups'],endpoint=second['endpoint'],cleared_windows=second['clears'],
  cursor_destroy_indices=second['destroys'],nonlive_ram_erased_at_every_boundary=True,
  actual_runtime_execution_observed=False)
def encode_text(s):
 need(type(s)is str and all(ch in charset_engine.CHARSET for ch in s),'独立glyphのみ')
 return bytes([charset_engine.CHARSET[ch]for ch in s]+[255])
def fixed_parts():
 parts={a:(live_engine.encoded(i)if printer_core(a)else encoded(i))for a,i in INS.items()}
 for a,v in WORDS.items():need(a not in parts,'命令/literal非重複');parts[a]=v.to_bytes(4,'little')
 for a,n,v in charset_engine.DATA_FIELDS:
  if printer_core(a):
   value=v.to_bytes(n,'little');need(a not in parts or parts[a]==value,'共通printer field整合');parts[a]=value
 for row in TEXTS:parts[row['address']]=encode_text(row['text'])
 parts[0x083C4A28]=bytes([238,1,0,2,0,4,0,13,14,15,0,0])
 parts[0x083E30F4]=(0x0800537D).to_bytes(4,'little')
 for c in CASES.values():parts[0x090421F4+c['move']*12+11]=bytes([c['effect']])
 return parts
def bind(raw):
 for a,b in fixed_parts().items():need(chunk(raw,a,len(b))==b,'独立意味/source field不一致 '+hex(a))
 return True

SOURCE_IDS = {'choosemove-BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'choosemove-BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'choosemove-cfru-charmap.tbl': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                      'git_blob_sha': 'b841b842a93f886ee396c9b7f6529bb633964dbb',
                      'local': 'choosemove-cfru-charmap.tbl',
                      'repository': 'kapibarasan000/CFRU-JP',
                      'sha256': '35c1b978f7004129679751a79cf4b40d7edd2fcd678bc81a29483b64b75b7ed5',
                      'size': 1639,
                      'source': 'charmap.tbl',
                      'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/charmap.tbl'},
 'choosemove-cfru-hooks': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                'git_blob_sha': '51a0f10dd4cccad235b476edd534a0e3e7e612ad',
                'local': 'choosemove-cfru-hooks',
                'repository': 'kapibarasan000/CFRU-JP',
                'sha256': '19c730e12bcc8ee614b43745a1a6478429c1876a025fdce23b80a49599d8deb5',
                'size': 21787,
                'source': 'hooks',
                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/hooks'},
 'choosemove-cfru-include--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': '7add3e78535b105d9d08d3d601da4e1d784f526a',
                            'local': 'choosemove-cfru-include--battle.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': '8c6b332ef73bc545297b4f6c5bedc1ad11fa4470901f39cf386c1be53f4abdc9',
                            'size': 52228,
                            'source': 'include/battle.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle.h'},
 'choosemove-cfru-include--battle_controllers.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                        'git_blob_sha': '306d9ae6ce5956171207a4a779fb878883f271af',
                                        'local': 'choosemove-cfru-include--battle_controllers.h',
                                        'repository': 'kapibarasan000/CFRU-JP',
                                        'sha256': '95456edaefe281ebeaf55172635f8ccde14d5f4d0e6818f548ce0b37722ed9a1',
                                        'size': 11694,
                                        'source': 'include/battle_controllers.h',
                                        'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle_controllers.h'},
 'choosemove-cfru-include--constants--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                       'git_blob_sha': '6ebffb06ae7978281cf9bbd6b082182e4e481714',
                                       'local': 'choosemove-cfru-include--constants--battle.h',
                                       'repository': 'kapibarasan000/CFRU-JP',
                                       'sha256': '88681a4d9e3f34b8608417adf44f828b8c1a19669bba30e00fe22540e2936fb0',
                                       'size': 16608,
                                       'source': 'include/constants/battle.h',
                                       'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/battle.h'},
 'choosemove-cfru-include--gba--types.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                'git_blob_sha': '601fdf73ab404a2d1e0ccd5a4d0c3f5382ede8e0',
                                'local': 'choosemove-cfru-include--gba--types.h',
                                'repository': 'kapibarasan000/CFRU-JP',
                                'sha256': '467a0219173bd2f8e20e962a9eaa43eafba298f815dab6655ae1761367d43ae6',
                                'size': 4241,
                                'source': 'include/gba/types.h',
                                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/gba/types.h'},
 'choosemove-cfru-include--global.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': '574c09b9b6209f6bee6e1d3a2fb8866221af8900',
                            'local': 'choosemove-cfru-include--global.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': 'c2973e69e55633ce39c9fe1763c891e5530b4ac1dc15e82a666c1f1ea7201bc0',
                            'size': 19566,
                            'source': 'include/global.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/global.h'},
 'choosemove-cfru-include--new--dynamax.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                  'git_blob_sha': '44172f4de362d06376656a2e48b896f6e7f1b80a',
                                  'local': 'choosemove-cfru-include--new--dynamax.h',
                                  'repository': 'kapibarasan000/CFRU-JP',
                                  'sha256': '6ac0d6b45362c382cae65e3a168020cdda6b79900a922dede71ac87e8a58df5b',
                                  'size': 5148,
                                  'source': 'include/new/dynamax.h',
                                  'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/dynamax.h'},
 'choosemove-cfru-include--new--z_move_effects.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                         'git_blob_sha': 'a947a82a6d423797405dacd34c55d69635469756',
                                         'local': 'choosemove-cfru-include--new--z_move_effects.h',
                                         'repository': 'kapibarasan000/CFRU-JP',
                                         'sha256': '75669f5f8c4c58774e2d43d2ca1917116666b568f9c1cfbb78d305b89288c1f1',
                                         'size': 1020,
                                         'source': 'include/new/z_move_effects.h',
                                         'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/z_move_effects.h'},
 'choosemove-cfru-include--pokemon.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                             'git_blob_sha': 'b18f2ee2a1517efa8aeb742daedac9e778d73d7a',
                             'local': 'choosemove-cfru-include--pokemon.h',
                             'repository': 'kapibarasan000/CFRU-JP',
                             'sha256': 'd75972c66e85835a3fc9c859cb695c033995ba6627ba1d44f577b35136356c78',
                             'size': 29476,
                             'source': 'include/pokemon.h',
                             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/pokemon.h'},
 'choosemove-cfru-include--sprite.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': 'da7057376c71e2cbe3543f262a6e360e2eeaaf8a',
                            'local': 'choosemove-cfru-include--sprite.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': 'c848594606e7889276457e723c5189cbedbe71862a1b001ed9ec39299a8fe511',
                            'size': 11836,
                            'source': 'include/sprite.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/sprite.h'},
 'choosemove-cfru-scripts--string.py': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                             'git_blob_sha': '6f67bd402b7f85c7681d3049f49a956a9a8a78b8',
                             'local': 'choosemove-cfru-scripts--string.py',
                             'repository': 'kapibarasan000/CFRU-JP',
                             'sha256': '828d3813ed258a318f5d69f3fbabb05c9f0ef0975701f14875668c680a0f312e',
                             'size': 7959,
                             'source': 'scripts/string.py',
                             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/scripts/string.py'},
 'choosemove-cfru-src--move_menu.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                           'git_blob_sha': '5154ff0d103203d733a0c54f94cff320dfde1124',
                           'local': 'choosemove-cfru-src--move_menu.c',
                           'repository': 'kapibarasan000/CFRU-JP',
                           'sha256': '4d75ed407c017d2788b7b71c954082751be55d5f0fb6a62becc26d30b8394a52',
                           'size': 84120,
                           'source': 'src/move_menu.c',
                           'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/move_menu.c'},
 'choosemove-cfru-strings--general_battle_strings.string': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                                 'git_blob_sha': '32c2b30b5822d6be665031f9a27b30a4ae7e1592',
                                                 'local': 'choosemove-cfru-strings--general_battle_strings.string',
                                                 'repository': 'kapibarasan000/CFRU-JP',
                                                 'sha256': 'cb94fc213838166058f589d9683903bfd584f950ff6ff83144fc3b992a719ba8',
                                                 'size': 9483,
                                                 'source': 'strings/general_battle_strings.string',
                                                 'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/strings/general_battle_strings.string'},
 'choosemove-move_ids.csv': {'commit': 'b9be8c6c231df0aac1c5eb163b154a4ec8ff5787',
                  'git_blob_sha': '48e248aed492791bd1c90d7327764b62293683ec',
                  'local': 'choosemove-move_ids.csv',
                  'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                  'sha256': 'dba3c65af59ee2dcfa9eecdeeeb1cc189a990b52e27b1878bad6eaec8e104f20',
                  'size': 128694,
                  'source': 'manifests/move_ids.csv',
                  'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/b9be8c6c231df0aac1c5eb163b154a4ec8ff5787/manifests/move_ids.csv'},
 'choosemove-pret-battle_message.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                           'git_blob_sha': 'a6392be9a91cd8171d920ff45c684b627b0c98b1',
                           'local': 'choosemove-pret-battle_message.c',
                           'repository': 'pret/pokefirered',
                           'sha256': '257be289b56dbfe63da9cf956a87d91219d45eb72a47d2dff681caa684f2b6de',
                           'size': 151308,
                           'source': 'src/battle_message.c',
                           'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/battle_message.c'},
 'choosemove-pret-string_util.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                        'git_blob_sha': '5c26d151a61274caac3a16c3b9c4eb73bf9a9e26',
                        'local': 'choosemove-pret-string_util.c',
                        'repository': 'pret/pokefirered',
                        'sha256': 'ed9519d4eaf51ed660a522915366dc0ebf2916d592a91a1d7fc2a012e4f3f17e',
                        'size': 14320,
                        'source': 'src/string_util.c',
                        'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/string_util.c'},
 'choosemove-pret-text.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': 'f3eef07ce6dea8269980a5ecfdd6902c1c9c13d2',
                 'local': 'choosemove-pret-text.c',
                 'repository': 'pret/pokefirered',
                 'sha256': '5696f49443eeaaac74b530421ac7f0cbfc71996c557399583788111c322dd80c',
                 'size': 63210,
                 'source': 'src/text.c',
                 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/text.c'},
 'choosemove-project-overlays--battle_ui--battle_ui.c': {'commit': 'b9be8c6c231df0aac1c5eb163b154a4ec8ff5787',
                                              'git_blob_sha': 'e21b02abf274454492578df658ed6dc989ee978e',
                                              'local': 'choosemove-project-overlays--battle_ui--battle_ui.c',
                                              'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                              'sha256': '1712b63da4f63c0dcf7209e344f46f5d39793d166e5e3d704f1cf3714e8b5cd5',
                                              'size': 14621,
                                              'source': 'overlays/battle_ui/battle_ui.c',
                                              'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/b9be8c6c231df0aac1c5eb163b154a4ec8ff5787/overlays/battle_ui/battle_ui.c'},
 'choosemove-project-overlays--battle_ui--battle_ui_trampoline.S': {'commit': 'b9be8c6c231df0aac1c5eb163b154a4ec8ff5787',
                                                         'git_blob_sha': 'bb69ea63ff992f4d22a2fe62bcdc5422d629bd23',
                                                         'local': 'choosemove-project-overlays--battle_ui--battle_ui_trampoline.S',
                                                         'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                                         'sha256': '3dcf04f37000752f4dfb70e77b63f3d2433d1f89a5a6841cfba4b72dabdb30e0',
                                                         'size': 2274,
                                                         'source': 'overlays/battle_ui/battle_ui_trampoline.S',
                                                         'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/b9be8c6c231df0aac1c5eb163b154a4ec8ff5787/overlays/battle_ui/battle_ui_trampoline.S'},
 'choosemove-project-overlays--qol_production--qol_production.c': {'commit': 'b9be8c6c231df0aac1c5eb163b154a4ec8ff5787',
                                                        'git_blob_sha': 'd1ba686a3c2d7abf936edd0d17810d93a4357374',
                                                        'local': 'choosemove-project-overlays--qol_production--qol_production.c',
                                                        'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                                        'sha256': '6a07635ca20dcd37365a2393910eb610d4f9c5a682585149ecb1243738cce23a',
                                                        'size': 164877,
                                                        'source': 'overlays/qol_production/qol_production.c',
                                                        'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/b9be8c6c231df0aac1c5eb163b154a4ec8ff5787/overlays/qol_production/qol_production.c'}}

SOURCE_IDS['choosemove-cfru-battle_moves.c'] = {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
 'git_blob_sha': '46a6e4b194479dc26080b9f26f275968d1307332',
 'local': 'choosemove-cfru-battle_moves.c',
 'repository': 'kapibarasan000/CFRU-JP',
 'sha256': '7c13282701ce28e47370a7be82cd1d8f489e7cbf4b5030ab677ab6b70c79470d',
 'size': 356184,
 'source': 'src/Tables/battle_moves.c',
 'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/Tables/battle_moves.c'}

def source_semantics(sources):
 texts={k:layout_engine.without_comments(v.decode('utf-8-sig'))for k,v in sources.items()}
 constants={}
 for name in('MAX_BATTLERS_COUNT','NUM_BATTLE_SIDES','POKEMON_NAME_LENGTH','PARTY_SIZE','BATTLE_STATS_NO','MAX_SPRITES','MAX_NUM_RAID_SHIELDS','MAX_MON_MOVES'):
  values=[]
  for text in texts.values():values+=re.findall(r'^\s*#define\s+'+name+r'\s+(\d+)\s*$',text,re.M)
  need(values and len(set(values))==1,'独立array macro '+name);constants[name]=int(values[0])
 choose,csize,_=layout_engine.layout(layout_engine.definition(texts['choosemove-cfru-include--battle_controllers.h'],'ChooseMoveStruct'),constants)
 new,nsize,_=layout_engine.layout(layout_engine.definition(texts['choosemove-cfru-include--battle.h'],'NewBattleStruct'),constants)
 moves,msize,_=layout_engine.layout(layout_engine.definition(texts['choosemove-cfru-include--pokemon.h'],'BattleMove'),constants)
 expected_choose={'moves':dict(offset=0,size=8),'makesContact':dict(offset=76,size=4),'canMegaEvolve':dict(offset=82,size=1),
  'zMoveUsed':dict(offset=84,bit=0,width_bits=1,type_size=1),'megaDone':dict(offset=84,bit=1,width_bits=1,type_size=1),
  'ultraDone':dict(offset=84,bit=2,width_bits=1,type_size=1),'dynamaxDone':dict(offset=84,bit=3,width_bits=1,type_size=1),
  'dynamaxed':dict(offset=84,bit=4,width_bits=1,type_size=1),'terastalDone':dict(offset=84,bit=5,width_bits=1,type_size=1),
  'zPartyIndex':dict(offset=86,size=1),'possibleZMoves':dict(offset=88,size=8),'possibleMaxMoves':dict(offset=100,size=8),
  'dynamaxPartyIndex':dict(offset=116,size=1),'terastalPartyIndex':dict(offset=117,size=1)}
 need({k:choose[k]for k in expected_choose}==expected_choose and csize==120,'独立ChooseMove120byte/field ABI')
 expected_new={'zMoveData.used':dict(offset=576,size=4),'megaData.done':dict(offset=548,size=4),
  'ultraData.done':dict(offset=568,size=4),'dynamaxData.used':dict(offset=590,size=4),
  'terastalData.done':dict(offset=620,size=4),'zMoveData.partyIndex':dict(offset=580,size=2),
  'dynamaxData.partyIndex':dict(offset=598,size=2),'terastalData.partyIndex':dict(offset=624,size=2),
  'zMoveData.viewing':dict(offset=584,bit=3,width_bits=1,type_size=1),
  'zMoveData.viewingDetails':dict(offset=584,bit=5,width_bits=1,type_size=1),
  'dynamaxData.viewing':dict(offset=609,bit=1,width_bits=1,type_size=1)}
 need({k:new[k]for k in expected_new}==expected_new,'独立NewBattleStruct selected field ABI')
 need(msize==12 and moves['z_move_effect']==dict(offset=11,size=1),'独立BattleMove12/+11byte')
 enum=re.search(r'enum\s+MaxMoveEffect\s*\{([^}]+)\}',texts['choosemove-cfru-include--new--dynamax.h']);need(enum is not None,'公開MaxMoveEffect enum')
 names=[x.strip()for x in enum[1].split(',')if x.strip()]
 need(all(re.fullmatch(r'[A-Za-z_]\w*',x)for x in names),'明示単純連番enum')
 enums={'MAX_EFFECT_HEAL_TEAM':names.index('MAX_EFFECT_HEAL_TEAM'),'MAX_EFFECT_SPITE':names.index('MAX_EFFECT_SPITE')}
 z=re.findall(r'^#define\s+Z_EFFECT_RESET_STATS\s+(\d+)\s*$',texts['choosemove-cfru-include--new--z_move_effects.h'],re.M)
 need(z==['1']and enums=={'MAX_EFFECT_HEAL_TEAM':34,'MAX_EFFECT_SPITE':35},'独立Z/Max enum')
 enums['Z_EFFECT_RESET_STATS']=1
 rows=list(csv.DictReader(io.StringIO(sources['choosemove-move_ids.csv'].decode())))
 fields=[]
 for key,number,symbol,effect in [('MOVE_KEY_AGILITY',97,'MOVE_AGILITY','Z_EFFECT_RESET_STATS'),
  ('MOVE_KEY_G_MAX_FINALE_P',984,'MOVE_G_MAX_FINALE_P','MAX_EFFECT_HEAL_TEAM'),
  ('MOVE_KEY_G_MAX_DEPLETION_P',988,'MOVE_G_MAX_DEPLETION_P','MAX_EFFECT_SPITE')]:
  selected=[r for r in rows if r['move_key']==key]
  need(len(selected)==1 and selected[0]['id']==str(number)and selected[0]['cfru_symbol']==symbol,'canonical現Move ID '+key)
  entries=re.findall(r'\['+symbol+r'\]\s*=\s*\{([^{}]+)\}',texts['choosemove-cfru-battle_moves.c'],re.S)
  need(len(entries)==1 and re.findall(r'\.z_move_effect\s*=\s*(\w+)',entries[0])==[effect],'公開move producer effect '+symbol)
  fields.append(dict(move_key=key,id=number,symbol=symbol,effect_name=effect,effect=enums[effect],address=0x090421F4+number*msize+moves['z_move_effect']['offset']))
 mapping={line[3:]:int(line[:2],16)for line in sources['choosemove-cfru-charmap.tbl'].decode('utf-8-sig').splitlines()if len(line)>=4 and line[2]=='='}
 need(exact(mapping,charset_engine.CHARSET),'公開日本語charmap全文')
 public=sources['choosemove-cfru-strings--general_battle_strings.string'].decode()
 for row in TEXTS:
  matches=re.findall(r'^#org @'+row['label']+r'\s*\n([^\n]+)',public,re.M)
  need(matches==[row['text']]and len(encode_text(matches[0]))==row['size'],'公開登録text全文/EOS '+row['label'])
 script=sources['choosemove-cfru-scripts--string.py'].decode()
 need('stringToWrite += "0xFF\\n\\n"'in script and 'CharMap = "charmap.tbl"'in script,'文字serializer EOS/charmap規約')
 return dict(choose_struct_size=csize,new_struct_size=nsize,choose_fields=expected_choose,new_fields=expected_new,
  battle_move_size=msize,effect_field=moves['z_move_effect'],move_producer_fields=fields,enum_values=enums,
  independent_source_text_bytes=sum(r['size']for r in TEXTS),source_comments_used=False,
  japanese_template_values_derived_from_english_source=False)

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'固定source閉集合')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'独立source全文 '+name)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立source Git blob '+name)
 roles={
  'choosemove-cfru-hooks':['HandleInputChooseMove 802E1EC 0'],
  'choosemove-project-qol_production.h':['#define VEGA_QOL_PRODUCTION_MAGIC 0x51504F4Cu'],
  'choosemove-project-build_battle_ui.py':['"HandleInputChooseMove": (0x09116F90, 0x119C)',"linked_symbols['HandleInputChooseMove']['address'] + 8 | 1"],
  'choosemove-project-qol_hooks.S':['VegaQolProduction_FixInstantTextSpeedHook:','cmp r5, #0x7f','ldr r0, =0x02020010','strb r1, [r0, #27]','ldr r3, =0x08002d15'],
  'choosemove-pret-text_printer.c':['sTempTextPrinter.printerTemplate = *textSubPrinter;','if (speed != TEXT_SKIP_DRAW && speed != 0)','RenderFont(&sTempTextPrinter) == RENDER_FINISH','CopyWindowToVram(sTempTextPrinter.printerTemplate.windowId, COPYWIN_GFX);'],
  'choosemove-project-overlays--qol_production--qol_production.c':['void VegaQolProduction_HandleInputChooseMoveAdapter(void)',
   'ensure_state();','state->magic == VEGA_QOL_PRODUCTION_MAGIC','state->inverse == ~VEGA_QOL_PRODUCTION_MAGIC',
   '|| !G_QOL_STATE->auto_active','FN_ORIGINAL_BATTLE_MOVE();','QOL_STATE_ADDRESS = 0x0203B5E8u','PTR(VoidFn, 0x09116F91u)'],
  'choosemove-project-overlays--battle_ui--battle_ui.c':['void VegaBattleUI_HandleInputChooseMove(void)','vega_battle_ui_handle_input_choose_move_trampoline();'],
  'choosemove-project-overlays--battle_ui--battle_ui_trampoline.S':['movs r2, #144','push {r4-r7, lr}','mov r6, r9','mov r7, r10','bx r3','.word VEGA_UI_HANDLE_CHOOSE_MOVE_CONTINUE_ADDRESS'],
  'choosemove-cfru-src--move_menu.c':['void HandleInputChooseMove(void)','gNewBS->zMoveData.used[gActiveBattler] = moveInfo->zMoveUsed;',
   'gNewBS->dynamaxData.partyIndex[SIDE(gActiveBattler)] = moveInfo->dynamaxPartyIndex;',
   'else if (gMain.newKeys & START_BUTTON)','if (!MoveSelectionDisplayZMove())','if (!TriggerMegaEvolution() && gBattleTypeFlags & BATTLE_TYPE_DYNAMAX)',
   'else if (gMain.newKeys & L_BUTTON)','if (!gNewBS->zMoveData.viewing && !gNewBS->dynamaxData.viewing)',
   'MoveSelectionDisplayDetails();','if (!moveInfo->canMegaEvolve)','if (moveInfo->dynamaxed || IsTerastal(gActiveBattler))',
   'u16 zmove = moveInfo->possibleZMoves[gMoveSelectionCursor[gActiveBattler]];',
   'u16 maxMove = moveInfo->possibleMaxMoves[gMoveSelectionCursor[gActiveBattler]];',
   'u8 maxEffect = gBattleMoves[maxMove].z_move_effect;',
   'MoveSelectionDestroyCursorAt(i);','StringCopy(gDisplayedStringBattle, StringNull);','BattlePutTextOnWindow(gDisplayedStringBattle, i + 3);',
   'case Z_EFFECT_RESET_STATS:','StringCopy(gDisplayedStringBattle, gText_ResetStats);',
   'case MAX_EFFECT_HEAL_TEAM:','StringCopy(gDisplayedStringBattle, gText_MaxMoveHealTeam);',
   'case MAX_EFFECT_SPITE:','StringCopy(gDisplayedStringBattle, gText_MaxMoveSpite);','string = gText_NoContact;','BattlePutTextOnWindow(string, 3 + 1);'],
  'choosemove-pret-string_util.c':['u8 *StringCopy(u8 *dest, const u8 *src)','while (*src != EOS)','*dest = *src;','*dest = EOS;'],
  'choosemove-pret-text.c':['currChar = *textPrinter->printerTemplate.currentChar;','textPrinter->printerTemplate.currentChar++;'],
  'choosemove-pret-battle_message.c':['void BattlePutTextOnWindow(const u8 *text, u8 windowId)',
   'printerTemplate.currentChar = text;','printerTemplate.windowId = windowId;','printerTemplate.fontId = sTextOnWindowsInfo_Normal[windowId].fontId;',
   'speed = sTextOnWindowsInfo_Normal[windowId].speed;','AddTextPrinter(&printerTemplate, speed, NULL);'],
  'choosemove-BPRJ.ld':['StringCopy = 0x8008900 | 1;','BattlePutTextOnWindow = 0x80D980C | 1;','GetBattlerSide = 0x8074968 | 1;','gBattleBufferA = 0x2022B24;']}
 for name,tokens in roles.items():
  source=sources[name].decode()
  for token in tokens:need(token in source,'独立source意味 '+name+' '+token)
 return source_semantics(sources)

SOURCE_IDS['choosemove-project-qol_production.h'] = {'commit': 'c2059ee805d978575b319e7a113b3edf0a676f1e',
 'git_blob_sha': '72c81d3dbf656b5c1005dd38bb16afc1859408b6',
 'local': 'choosemove-project-qol_production.h',
 'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
 'sha256': 'd659645003fc4da6611815f2071e83185a334a78f7e9981533135a9aef6fde7f',
 'size': 7233,
 'source': 'overlays/qol_production/qol_production.h',
 'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/c2059ee805d978575b319e7a113b3edf0a676f1e/overlays/qol_production/qol_production.h'}

SOURCE_IDS['choosemove-project-build_battle_ui.py'] = {'commit': 'c2059ee805d978575b319e7a113b3edf0a676f1e',
 'git_blob_sha': '54a4d131d1b57b62d5d4df03d07eb509611bd4a0',
 'local': 'choosemove-project-build_battle_ui.py',
 'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
 'sha256': '7489c3aa28e1547eea0801ca7d8b532b8252cbf67ede2fe0d199c96587893ce6',
 'size': 54088,
 'source': 'scripts/build_battle_ui.py',
 'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/c2059ee805d978575b319e7a113b3edf0a676f1e/scripts/build_battle_ui.py'}

SOURCE_IDS['choosemove-project-qol_hooks.S'] = {'commit': 'c2059ee805d978575b319e7a113b3edf0a676f1e',
 'git_blob_sha': '50f7c241f24faea37885ed370774ac528bd58cf5',
 'local': 'choosemove-project-qol_hooks.S',
 'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
 'sha256': 'f98689fe9c02b1345ae63feddc861a9b28fbd35fd8e024b931e88f788f5ac4e5',
 'size': 9448,
 'source': 'overlays/qol_production/qol_production_hooks.S',
 'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/c2059ee805d978575b319e7a113b3edf0a676f1e/overlays/qol_production/qol_production_hooks.S'}

SOURCE_IDS['choosemove-pret-text_printer.c'] = {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
 'git_blob_sha': 'e425ccb181b52d1f0827785e76c1793c2b2d693d',
 'local': 'choosemove-pret-text_printer.c',
 'repository': 'pret/pokefirered',
 'sha256': '075af562bb87de25773e9dcee93d8180c84083209aede0ed6f02343f94f5823e',
 'size': 16043,
 'source': 'src/text_printer.c',
 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/text_printer.c'}

ROOT=dict(kind='source_registered_ChooseMove_API_to_four_typed_text_consumers',entry=ENTRY,
 qol_adapter=0x09377B40,qol_guard=0x09378BD4,original_cfru_entry=0x09116F90,
 battle_ui_wrapper=0x092CFE58,trampoline=0x092CFEB8,continuation=0x09116F98,
 choose_data=CHOOSE,choose_stride=512,choose_struct_size=120,new_battle_struct_cell=NEWBS,
 contact_call=0x09117A94,contact_literal=0x09117D68,battle_window_api=0x080D980C,window_id=4,
 printer_call=0x080D9984,printer_api=0x08002CF0,printer_hook=0x09378A30,printer_byte_read=0x0800580E,
 z_dispatch=0x09115B6E,z_cell=0x09168254,reset_literal=0x09115E2C,
 max_dispatch=0x09117C48,max_cells=[0x0916848C,0x09168490],max_literals=[0x09118100,0x091180FC],
 string_copy=0x08008900,string_byte_read=0x0800890C)
CLAIMS=dict(conditional_registered_api_entry=True,complete_selected_caller_path=True,
 all_selected_text_bytes_and_eos_read=True,selected_pointer_host_seeded=False,
 source_only_independent_semantic_fixture=True,source_bound_move_producer_effects=True,
 source_bound_struct_layout=True,future_live_read_before_write_projection=True,
 future_resource_read_and_write_epochs=True,nonlive_ram_erased_at_every_boundary=True,
 current_candidate_measurement_required=True,actual_runtime_execution_observed=False,
 natural_battle_entry_proven=False,natural_all_prefix_success_proven=False,
 choose_move_emit_producer_proven=False,all_opaque_callee_effects_proven=False,
 final_graphics_or_move_effect_success_proven=False,universal_heap_or_irq_lifetime_proven=False,
 indirect_reference_completeness_proven=False,retirement_proven=False,donor_eligible=False,
 donor_leased=False,owner_transfer_proven=False)
CONTRACT=dict(
 entry_ja='実0802E1EC APIを有効stack/通常ABIで呼ぶ有限context。bank0/cursor0、NewBSの必要field、ChooseMove120byte配置、QoL magic/inverse/auto_active0はAPI入口条件。内部PC・text pointer・effectをhost注入しない。EmitChooseMoveや自然battle入口は未証明。',
 prefix_ja='QoL guardの実2比較、manual入力枝、BattleUIの実prologue trampoline、CFRU全prologue、5used/done field同期、3SIDE getter実引数とpartyIndex writer、single条件のHighlightPossibleTargets短絡、全key優先順を実行。',
 max_ja='START key・battle flag bit30・dynamaxed bit4=true・canMegaEvolve0・Z/Max viewing0。Z関数のfalse早期復帰とMegaのfalse復帰を実行し、選択possibleMaxMoves984/988から12byte stride/+11byteを実read。独立公開producer表のMAX_EFFECT_HEAL_TEAM/SPITE=34/35、実dispatch cellを通る。',
 reset_ja='START・非dynamaxed・Z viewing0・possibleZMoves[0]=FFFF・moves[0]=AGILITY97。IsTerastal(bank0)正常戻り0を有限条件とし、独立producer表Z_EFFECT_RESET_STATS1を実read/table dispatchする。',
 contact_ja='L key・Z/Max viewing0・details0・makesContact[0]=0。4cursor/4window clearとmove-nameの実callを通り、NoContact literalからBattlePutTextOnWindow window4へ配送する。',
 consumer_ja='StringCopyは全source byteとEOSを実LDRBし同DISPLAYへwriteして実復帰。NoContactは実window4 template→font1/speed0→AddTextPrinter→現QoL hook→temporary printer→font dispatch→RenderText全7byte/EOS→実復帰まで。日本語templateの10利用field/12strideは明示有限dataと実consumerで束縛し、英語pretのtemplate値やsizeから導出したとは主張しない。',
 opaque_ja='非対象cursor/空text・move-name表示、glyph decoder/copy・font lookup生成は正確なsite/target/引数に対する正常同期ABIのみ条件化。getter0/IsTerastal0以外の戻りとcaller-saved/NZCVをUnknownへ消去し、全副作用や描画成功を仮定しない。',
 epoch_ja='各境界の実将来read-before-write RAMだけを保持して非liveを消去。resourceは将来readとwriteの両方を逆向き集計し、NewBS/stack/DISPLAYの必要epochだけ維持。実hookのactive writerが生成するtemporary printer世代も、そのwriter後～最後のuseだけ同epoch。window4はNoContact printer期間のuseだけが根で、Max/Resetにwindow同epochを課さない。正常外部APIで必要な有効window3..6は各呼出の局所条件であり、全寿命の証明ではない。',
 minimum_ja='4有限caseの実消費和を09143266/09143415各4byteだけへ射影。隣接text全57byteは独立文字serializer証拠だが全extentを分類しない。命令/literal/table/templateも証拠であり新分類には含めない。')
from pr16_dex_hof_critical_move_list_roots import merge_parts
ALL_WINDOWS=merge_parts(fixed_parts())
WINDOWS={f'choosemove_text_roots_{j}':(w['address'],w['size'])for j,w in enumerate(ALL_WINDOWS)}

def compact_case(c):
 out={k:copy.deepcopy(v)for k,v in c.items()if k!='visited'}
 out['visited_identity']=identity(json.dumps(c['visited'],separators=(',',':')).encode())
 return out

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(profile is None or exact(profile,CASES),'有限profileの無断拡張禁止')
 need(contract is None or exact(contract,CONTRACT),'閉じたAPI/epoch契約')
 bind(raw);cases=[compose(raw,k,opaque_writes,epoch_events)for k in CASES]
 covered={a for c in cases for a,n in c['text_reads']}
 need(all(a in covered for hit in HITS for a in range(hit,hit+4)),'4case実消費和で全hit4byteずつ')
 need(sum(len(c['text_reads'])for c in cases)==57,'全4text57byte/EOS')
 return dict(status='PASS_CONDITIONAL_CHOOSEMOVE_FOUR_TEXT_CONSUMERS',cases=[compact_case(c)for c in cases],
  text_bytes_consumed=57,minimum_classified_bytes=8,source_pointer_host_seeded=False,
  actual_runtime_execution_observed=False)

def windows(raw):return[dict(address=w['address'],**identity(chunk(raw,w['address'],w['size'])))for w in ALL_WINDOWS]
measure=windows

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'ChooseMove限定hit')
 selected=TEXTS[:2]if hit==HITS[0]else TEXTS[2:]
 roles=[]
 for a in range(hit,hit+4):
  row=next(r for r in selected if r['address']<=a<r['address']+r['size']);offset=a-row['address']
  roles.append(dict(address=a,label=row['label'],offset=offset,role='EOS'if offset==row['size']-1 else'glyph'))
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=hit,size=4),
  texts=copy.deepcopy(selected),boundary_parts=roles,positive_cases=['contact','reset']if hit==HITS[0]else['heal','spite'],
  input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
 hit=evidence.get('classified_window',{}).get('address')if type(evidence)is dict else None
 need(type(hit)is int and hit in HITS and exact(evidence,evidence_template(hit)),'閉じたChooseMove4byte witness')
 return hit,4

def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'不変意味/source窓');return copy.deepcopy(ALL_WINDOWS)

def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS];need(exact(selected,EXPECTED_HITS),'親hit全field一致')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
  source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),
  windows=copy.deepcopy(ALL_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),
  finite_profiles=copy.deepcopy(CASES),texts=copy.deepcopy(TEXTS))
prepare_review=make_review

def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profiles','texts'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'現候補/旧診断分離')
 for k,v in [('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profiles',CASES),('texts',TEXTS)]:need(exact(review[k],v),'閉じたreview '+k)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS)and exact(selected,review['hits']),'親unknown全field保存')
 protected_windows(review);bind(raw);d.signed(raw,selected);semantics=sources_bind(review,sources)
 composition=compose_selected(raw)
 regions=[]
 for hit in HITS:
  e=evidence_template(hit);a,n=witness_geometry(e);regions.append(d.TypedRegion(a,a+n,KIND,e))
 return regions,dict(status='PASS_REGISTERED_CHOOSEMOVE_TEXT_ROOTS',count=2,hits=list(HITS),
  serialization=semantics,composition=composition,protected_windows=len(ALL_WINDOWS),
  protected_bytes=sum(w['size']for w in ALL_WINDOWS),**copy.deepcopy(CLAIMS))

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate');return _regions(raw,inherited,review,sources)
validate=_regions

EXPECTED_HITS = [{'accepted': False,
  'address': 152318566,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': '6f4e172e4fcd9a3d582f9bd6d633760e3659b4e2a441a4f9363376de8618367c',
  'size': 4,
  'target': 167708726},
 {'accepted': False,
  'address': 152318997,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': '4a05febfefaddb6dcaf3164a12d42f3d2853c9bc0f790c41a7b735cce2f5ec1a',
  'size': 4,
  'target': 167708700}]
