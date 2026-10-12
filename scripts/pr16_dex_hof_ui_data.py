"""Fame Checkerの実constructor登録と有限setupからの条件付き最小Thumb型。"""
import copy,hashlib,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_lifetime_menu as menu
import pr16_dex_hof_runtime_party as runtime
import pr16_dex_hof_summary_type as summary
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
HIT=0x0812DAEF
KIND='rooted_fame_checker_minimum_thumb'
HITS=(HIT,)
TYPE_CATEGORY='code'
CELL,MAIN,SAVE=0x0203B070,0x03003130,0x03005048
BLOCKS={}
def put(name,address,specs):BLOCKS[name]=tuple(party.block(address,specs))
put('constructor',0x0812CB94,[('push', 48, True),('addi', 5, 0, 0),('imm', 'mov', 0, 0),('call', 134219508),('literal', 4, 135449560),('imm', 'mov', 0, 36),('call', 134228912),('mem', False, 'word', 0, 4, 0),('mem', False, 'word', 5, 0, 0),('imm', 'mov', 1, 0),('mem', False, 'byte', 1, 0, 9),('mem', True, 'word', 0, 4, 0),('mem', False, 'byte', 1, 0, 10),('mem', True, 'word', 0, 4, 0),('mem', False, 'byte', 1, 0, 11),('mem', True, 'word', 1, 4, 0),('imm', 'add', 1, 35),('mem', True, 'byte', 2, 1, 0),('imm', 'mov', 0, 2),('alu', 'neg', 0, 0),('alu', 'and', 0, 2),('mem', False, 'byte', 0, 1, 0),('imm', 'mov', 0, 199),('call', 134683248),('literal', 0, 135449564),('call', 134219076),('pop', 48, False),('pop', 1, False),('bx', 0)])
put('setup_dispatch',0x0812CBE0,[('push', 112, True),('movhi', 6, 8),('push', 64, False),('spadd', -12),('literal', 0, 135449604),('imm', 'mov', 1, 135),('shift', 'lsl', 1, 1, 3),('add', 0, 0, 1),('mem', True, 'byte', 0, 0, 0),('imm', 'cmp', 0, 7),('branch', 9, 135449592),('jump', 135450126),('shift', 'lsl', 0, 0, 2),('literal', 1, 135449608),('add', 0, 0, 1),('mem', True, 'word', 0, 0, 0),('movhi', 15, 0)])
put('setup_0_1_2',0x0812CC2C,[('imm', 'mov', 0, 0),('call', 134219508),('call', 135453748),('jump', 135450022),('call', 135454060),('jump', 135450022),('literal', 6, 135449752),('imm', 'mov', 4, 128),('shift', 'lsl', 4, 4, 4),('addi', 0, 4, 0),('call', 134228912),('mem', False, 'word', 0, 6, 0),('literal', 1, 135449756),('movhi', 8, 1),('imm', 'mov', 0, 128),('shift', 'lsl', 0, 0, 5),('call', 134228912),('movhi', 1, 8),('mem', False, 'word', 0, 1, 0),('literal', 5, 135449760),('addi', 0, 4, 0),('call', 134228912),('mem', False, 'word', 0, 5, 0),('imm', 'mov', 0, 0),('call', 134223384),('literal', 1, 135449764),('imm', 'mov', 0, 0),('imm', 'mov', 2, 4),('call', 134223448),('mem', True, 'word', 1, 6, 0),('imm', 'mov', 0, 3),('call', 134225824),('mem', True, 'word', 1, 5, 0),('imm', 'mov', 0, 2),('call', 134225824),('movhi', 0, 8),('mem', True, 'word', 1, 0, 0),('imm', 'mov', 0, 1),('call', 134225824),('call', 135454120),('jump', 135450022)])
put('setup_3',0x0812CCA8,[('literal', 1, 135449876),('imm', 'mov', 2, 165),('shift', 'lsl', 2, 2, 5),('imm', 'mov', 0, 3),('imm', 'mov', 3, 0),('call', 134223824),('literal', 1, 135449880),('imm', 'mov', 5, 32),('spmem', False, 5, 0),('spmem', False, 5, 4),('imm', 'mov', 0, 3),('imm', 'mov', 2, 0),('imm', 'mov', 3, 0),('call', 134226212),('literal', 4, 135449884),('addi', 0, 4, 0),('imm', 'mov', 1, 0),('imm', 'mov', 2, 64),('call', 134675344),('imm', 'add', 4, 32),('addi', 0, 4, 0),('imm', 'mov', 1, 16),('imm', 'mov', 2, 32),('call', 134675344),('literal', 1, 135449888),('spmem', False, 5, 0),('spmem', False, 5, 4),('imm', 'mov', 0, 2),('imm', 'mov', 2, 0),('imm', 'mov', 3, 0),('call', 134226212),('literal', 1, 135449892),('spmem', False, 5, 0),('spmem', False, 5, 4),('imm', 'mov', 0, 17),('spmem', False, 0, 8),('imm', 'mov', 0, 1),('imm', 'mov', 2, 30),('imm', 'mov', 3, 0),('call', 134226472),('imm', 'mov', 0, 2),('call', 135607500),('imm', 'mov', 1, 240),('imm', 'mov', 2, 32),('call', 134675344),('jump', 135450022)])
put('setup_4_5',0x0812CD28,[('call', 134224224),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('imm', 'cmp', 0, 1),('branch', 0, 135450126),('imm', 'mov', 0, 0),('call', 134224316),('imm', 'mov', 0, 1),('call', 134224316),('imm', 'mov', 0, 2),('call', 134224316),('imm', 'mov', 0, 3),('call', 134224316),('imm', 'mov', 0, 3),('call', 134226108),('imm', 'mov', 0, 2),('call', 134226108),('imm', 'mov', 0, 1),('call', 134226108),('jump', 135450022),('literal', 0, 135449984),('call', 134232816),('call', 134229032),('call', 135452328),('literal', 4, 135449988),('imm', 'mov', 0, 136),('call', 134228912),('mem', False, 'word', 0, 4, 0),('call', 135455508),('jump', 135450022)])
put('setup_6_call',0x0812CD88,[('call', 135450160),('imm', 'mov', 0, 0),('call', 135453116)])
put('setup_increment',0x0812CDA6,[('literal', 1, 135450040),('imm', 'mov', 0, 135),('shift', 'lsl', 0, 0, 3),('add', 1, 1, 0),('mem', True, 'byte', 0, 1, 0),('imm', 'add', 0, 1),('mem', False, 'byte', 0, 1, 0),('jump', 135450126)])
put('setup_return',0x0812CE0E,[('spadd', 12),('pop', 8, False),('movhi', 8, 3),('pop', 112, False),('pop', 1, False),('bx', 0)])
put('list_create',0x0812E314,[('push', 16, True),('call', 135455568),('call', 135456508),('literal', 4, 135455560),('mem', True, 'word', 3, 4, 0),('shift', 'lsl', 0, 0, 2),('mem', True, 'byte', 2, 3, 7),('imm', 'mov', 1, 3),('alu', 'and', 1, 2),('alu', 'orr', 1, 0),('mem', False, 'byte', 1, 3, 7),('literal', 0, 135455564),('imm', 'mov', 1, 0),('imm', 'mov', 2, 0),('call', 135297788),('mem', True, 'word', 1, 4, 0),('mem', False, 'byte', 0, 1, 8),('imm', 'mov', 0, 0),('call', 135456748),('pop', 16, False),('pop', 1, False),('bx', 0)])
put('list_template',0x0812E350,[('literal', 2, 135455672),('literal', 0, 135455676),('mem', True, 'word', 0, 0, 0),('mem', False, 'word', 0, 2, 0),('literal', 0, 135455680),('mem', False, 'word', 0, 2, 4),('imm', 'mov', 0, 0),('mem', False, 'word', 0, 2, 8),('imm', 'mov', 1, 0),('imm', 'mov', 0, 1),('mem', False, 'half', 0, 2, 12),('mem', False, 'half', 0, 2, 14),('mem', False, 'byte', 1, 2, 16),('mem', False, 'byte', 1, 2, 17),('imm', 'mov', 0, 10),('mem', False, 'byte', 0, 2, 18),('mem', False, 'byte', 1, 2, 19),('mem', True, 'byte', 1, 2, 20),('imm', 'sub', 0, 26),('alu', 'and', 0, 1),('imm', 'mov', 1, 4),('alu', 'orr', 0, 1),('imm', 'mov', 1, 15),('alu', 'and', 0, 1),('imm', 'mov', 1, 32),('alu', 'orr', 0, 1),('mem', False, 'byte', 0, 2, 20),('imm', 'mov', 0, 48),('mem', False, 'byte', 0, 2, 21),('mem', True, 'byte', 1, 2, 22),('imm', 'sub', 0, 56),('alu', 'and', 0, 1),('imm', 'mov', 1, 1),('alu', 'orr', 0, 1),('imm', 'mov', 1, 57),('alu', 'neg', 1, 1),('alu', 'and', 0, 1),('imm', 'mov', 1, 16),('alu', 'orr', 0, 1),('imm', 'mov', 3, 63),('alu', 'and', 0, 3),('mem', False, 'byte', 0, 2, 22),('mem', True, 'byte', 1, 2, 23),('imm', 'mov', 0, 64),('alu', 'neg', 0, 0),('alu', 'and', 0, 1),('imm', 'mov', 1, 2),('alu', 'orr', 0, 1),('alu', 'and', 0, 3),('mem', False, 'byte', 0, 2, 23),('bx', 14)])
put('list_population',0x0812E6FC,[('push', 240, True),('movhi', 7, 8),('push', 128, False),('imm', 'mov', 4, 0),('imm', 'mov', 6, 0),('literal', 0, 135456588),('movhi', 8, 0),('literal', 7, 135456592),('addi', 0, 6, 0),('call', 135452840),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 5, 0, 24),('literal', 0, 135456596),('mem', True, 'word', 0, 0, 0),('shift', 'lsl', 1, 5, 2),('add', 0, 0, 1),('literal', 1, 135456600),('add', 0, 0, 1),('mem', True, 'byte', 0, 0, 0),('shift', 'lsl', 0, 0, 30),('imm', 'cmp', 0, 0),('branch', 0, 135456656),('literal', 0, 135456604),('shift', 'lsl', 1, 5, 1),('add', 3, 1, 0),('mem', True, 'half', 0, 3, 0),('comparehi', 0, 8),('branch', 8, 135456616),('literal', 0, 135456608),('mem', True, 'word', 0, 0, 0),('shift', 'lsl', 2, 4, 3),('add', 2, 2, 0),('mem', True, 'half', 0, 3, 0),('shift', 'lsl', 0, 0, 5),('literal', 1, 135456612),('add', 0, 0, 1),('mem', False, 'word', 0, 2, 0),('mem', False, 'word', 4, 2, 4),('jump', 135456640)])
put('list_nontrainer_and_tail',0x0812E768,[('literal', 0, 135456712),('mem', True, 'word', 0, 0, 0),('shift', 'lsl', 1, 4, 3),('add', 1, 1, 0),('mem', True, 'half', 0, 3, 0),('literal', 2, 135456716),('add', 0, 0, 2),('shift', 'lsl', 0, 0, 2),('add', 0, 0, 7),('mem', True, 'word', 0, 0, 0),('mem', False, 'word', 0, 1, 0),('mem', False, 'word', 4, 1, 4),('literal', 0, 135456720),('mem', True, 'word', 0, 0, 0),('imm', 'add', 0, 12),('add', 0, 0, 4),('mem', False, 'byte', 5, 0, 0),('addi', 0, 4, 1),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 4, 0, 24),('addi', 0, 6, 1),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 6, 0, 24),('imm', 'cmp', 6, 15),('branch', 9, 135456524),('literal', 0, 135456712),('mem', True, 'word', 1, 0, 0),('shift', 'lsl', 0, 4, 3),('add', 0, 0, 1),('literal', 1, 135456724),('mem', False, 'word', 1, 0, 0),('mem', False, 'word', 4, 0, 4),('literal', 0, 135456720),('mem', True, 'word', 0, 0, 0),('imm', 'add', 0, 12),('add', 0, 0, 4),('imm', 'mov', 1, 255),('mem', False, 'byte', 1, 0, 0),('addi', 0, 4, 1),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 4, 0, 24),('literal', 1, 135456728),('mem', False, 'half', 4, 1, 12),('imm', 'cmp', 4, 4),('branch', 8, 135456732),('mem', False, 'half', 4, 1, 14),('jump', 135456736)])
put('list_return',0x0812E7DC,[('imm', 'mov', 0, 5),('mem', False, 'half', 0, 1, 14),('addi', 0, 4, 0),('pop', 8, False),('movhi', 8, 3),('pop', 240, False),('pop', 2, False),('bx', 1)])
put('person_index_adjust',0x0812D8A8,[('push', 16, True),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 4, 0, 24),('imm', 'mov', 0, 175),('shift', 'lsl', 0, 0, 1),('call', 134740804),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('imm', 'cmp', 0, 1),('branch', 1, 135452882),('imm', 'cmp', 4, 9),('branch', 1, 135452870),('imm', 'mov', 0, 15),('jump', 135452884),('imm', 'cmp', 4, 9),('branch', 9, 135452882),('subi', 0, 4, 1),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('jump', 135452884),('addi', 0, 4, 0),('pop', 16, False),('pop', 2, False),('bx', 1)])
put('icon_loop_prefix',0x0812D9BC,[('push', 240, True),('movhi', 7, 8),('push', 128, False),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('movhi', 8, 0),('imm', 'mov', 5, 0),('imm', 'mov', 6, 0),('literal', 7, 135453260),('literal', 0, 135453264),('mem', True, 'word', 1, 0, 0),('mem', True, 'word', 0, 7, 0),('imm', 'add', 0, 12),('addhi', 0, 8),('mem', True, 'byte', 2, 0, 0),('shift', 'lsl', 0, 2, 2),('add', 1, 1, 0),('literal', 0, 135453268),('add', 1, 1, 0),('mem', True, 'half', 0, 1, 0),('shift', 'lsl', 0, 0, 18),('shift', 'lsr', 0, 0, 20),('alu_ext', 'asr', 0, 6),('imm', 'mov', 1, 1),('alu', 'and', 0, 1),('imm', 'cmp', 0, 0),('branch', 0, 135453276),('literal', 1, 135453272),('shift', 'lsl', 0, 2, 1),('add', 0, 0, 2),('shift', 'lsl', 0, 0, 1),('add', 0, 0, 6),('add', 0, 0, 1),('mem', True, 'byte', 5, 0, 0),('addi', 0, 6, 0),('imm', 'mov', 1, 3),('call', 136086948),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('shift', 'lsl', 4, 0, 1),('add', 4, 4, 0),('shift', 'lsl', 4, 4, 4),('sub', 4, 4, 0),('imm', 'add', 4, 114),('shift', 'lsl', 4, 4, 16),('shift', 'asr', 4, 4, 16),('addi', 0, 6, 0),('imm', 'mov', 1, 3),('call', 136086828),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('shift', 'lsl', 3, 0, 3),('sub', 3, 3, 0),('shift', 'lsl', 3, 3, 2),('sub', 3, 3, 0),('imm', 'add', 3, 47),('shift', 'lsl', 3, 3, 16),('shift', 'asr', 3, 3, 16),('addi', 0, 5, 0),('addi', 1, 6, 0),('addi', 2, 4, 0),('call', 134603780),('mem', True, 'word', 1, 7, 0),('imm', 'add', 1, 29),('add', 1, 1, 6),('mem', False, 'byte', 0, 1, 0),('imm', 'mov', 5, 1),('jump', 135453364)])
put('icon_loop_suffix',0x0812DA5C,[('addi', 0, 6, 0),('imm', 'mov', 1, 3),('call', 136086948),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('shift', 'lsl', 4, 0, 1),('add', 4, 4, 0),('shift', 'lsl', 4, 4, 4),('sub', 4, 4, 0),('imm', 'add', 4, 114),('shift', 'lsl', 4, 4, 24),('shift', 'lsr', 4, 4, 24),('addi', 0, 6, 0),('imm', 'mov', 1, 3),('call', 136086828),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 0, 0, 24),('shift', 'lsl', 1, 0, 3),('sub', 1, 1, 0),('shift', 'lsl', 1, 1, 2),('sub', 1, 1, 0),('imm', 'add', 1, 31),('shift', 'lsl', 1, 1, 24),('shift', 'lsr', 1, 1, 24),('addi', 0, 4, 0),('call', 135454612),('mem', True, 'word', 1, 7, 0),('imm', 'add', 1, 29),('add', 1, 1, 6),('mem', False, 'byte', 0, 1, 0),('literal', 2, 135453412),('mem', True, 'word', 0, 7, 0),('imm', 'add', 0, 29),('add', 0, 0, 6),('mem', True, 'byte', 1, 0, 0),('shift', 'lsl', 0, 1, 4),('add', 0, 0, 1),('shift', 'lsl', 0, 0, 2),('add', 0, 0, 2),('imm', 'mov', 1, 255),('mem', False, 'half', 1, 0, 48),('addi', 0, 6, 1),('shift', 'lsl', 0, 0, 24),('shift', 'lsr', 6, 0, 24),('imm', 'cmp', 6, 5),('branch', 9, 135453134),('imm', 'cmp', 5, 1),('branch', 1, 135453428),('literal', 3, 135453416),('mem', True, 'word', 2, 3, 0),('mem', True, 'byte', 0, 2, 7),('imm', 'mov', 1, 1),('alu', 'orr', 0, 1),('mem', False, 'byte', 0, 2, 7),('mem', True, 'word', 0, 3, 0),('mem', True, 'byte', 1, 0, 7),('imm', 'mov', 0, 2),('alu', 'and', 0, 1),('imm', 'cmp', 0, 0),('branch', 0, 135453420),('imm', 'mov', 0, 1),('call', 135452892),('jump', 135453448)])
put('minimal_target',0x0812DAEC,[('imm', 'mov', 0, 0),('call', 135452892),('jump', 135453448)])
put('main_callback_store',0x08000544,[('literal', 1, 134219092),('mem', False, 'word', 0, 1, 4),('imm', 'mov', 0, 135),('shift', 'lsl', 0, 0, 3),('add', 1, 1, 0),('imm', 'mov', 0, 0),('mem', False, 'byte', 0, 1, 0),('bx', 14)])
LOCAL_WORDS={135449560: 33796208, 135449564: 135449569, 135449604: 50344240, 135449608: 135449612, 135449752: 33796196, 135449756: 33796200, 135449760: 33796204, 135449764: 138551048, 135449876: 138527724, 135449880: 138533068, 135449884: 138533004, 135449888: 138537164, 135449892: 138535116, 135449984: 138551064, 135449988: 33796212, 135450040: 50344240, 135455560: 33796208, 135455564: 50355968, 135455672: 50355968, 135455676: 33796212, 135455680: 135455685, 135456588: 65023, 135456592: 138549536, 135456596: 50352200, 135456600: 14932, 135456604: 138549486, 135456608: 33796212, 135456612: 154308724, 135456712: 33796212, 135456716: 4294902272, 135456720: 33796208, 135456724: 138270880, 135456728: 50355968, 135453260: 33796208, 135453264: 50352200, 135453268: 14932, 135453272: 138550096, 135453412: 33686968, 135453416: 33796208, 134219092: 50344240, 135449612: 135449644, 135449616: 135449656, 135449620: 135449662, 135449624: 135449768, 135449628: 135449896, 135449632: 135449952, 135449636: 135449992, 138549536: 138549518}
LOCAL_BLOCKS=dict(BLOCKS)
for name in ('alloc_zero_wrapper_0','alloc_zero_0'):BLOCKS[name]=summary.NEW_BLOCKS[name]
for name in ('put_header','alloc_scan_fit','alloc_split','alloc_scan_tail','main_callback_consumer','main_interwork'):BLOCKS['shared_'+name]=runtime.BLOCKS[name]
WORDS=dict(LOCAL_WORDS)
for rows in BLOCKS.values():
 for i in rows:
  if i.kind=='literal' and i.args[1] not in WORDS:WORDS[i.args[1]]=summary.ALL_WORDS.get(i.args[1],runtime.LITERALS.get(i.args[1]))
INS={i.address:i for rows in BLOCKS.values() for i in rows}
BOUNDARY={'address': 135453422, 'size': 6, 'sha256': '92a3560cfd8b4046b06eee90c567299d26d28851b350effe64eee27cf6992f45'}
SOURCE_IDS={'pret-main.c': {'local': 'pret-main.c', 'repository': 'pret/pokefirered', 'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788', 'path': 'src/main.c', 'size': 11699, 'sha256': '0bfa6c662b1cbd49bd31020b6c2509208004611e6701ad64badce22eca371139', 'git_blob_sha': '542b0f5d16dd93107523d11163bfcb70a42b707a', 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/main.c'}, 'pret-malloc.c': {'local': 'pret-malloc.c', 'repository': 'pret/pokefirered', 'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788', 'path': 'src/malloc.c', 'size': 6256, 'sha256': 'a81ff86e81b72f4a57d5c891e3f50d93e0c2a75a3e3ec37a48bdb84041ad369e', 'git_blob_sha': '260c41d0d9f80afbf75fe3fdfbf11393e004bb14', 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/malloc.c'}, 'pret-fame_checker.c': {'local': 'pret-fame_checker.c', 'repository': 'pret/pokefirered', 'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788', 'path': 'src/fame_checker.c', 'size': 69648, 'sha256': 'b09dc1fcbc1f8d1649df0f0be4f5a332135ba3d0f7041f1b2c784b0a0e35080c', 'git_blob_sha': 'b39771a49f420b5331ef8747b4fb1f27e8829ef4', 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/fame_checker.c'}}
# 上流の意味だけを名称参照。実operand・登録・main dispatch・producerは下で拘束する。
WINDOWS={name:(rows[0].address,sum(i.size for i in rows)) for name,rows in BLOCKS.items()}
WINDOWS.update({f'word_{a:08x}':(a,4) for a in sorted(WORDS)})
WINDOWS.update({'oak_trainer_index':(0x084218EE,2),'oak_graphics':(0x08421B50,1),'target_boundary':(HIT-1,6),'actual_BIOS_wrapper':(0x081C7A88,4)})
ROOT=dict(kind='actual_constructor_registration_then_main_callback_dispatch',constructor=0x0812CB94,allocation_call=0x0812CBA2,object_cell=CELL,requested_size=36,registration=0x0812CBCC,setup_callback=0x0812CBE1,main_dispatch=0x08000510,state_cell=MAIN+1080,setup_states=list(range(7)),population_call=0x0812E31A,person_writer=0x0812E788,icon_call=0x0812CD8E,icon_entry=0x0812D9BC,record_base_offset=0x3A54,hit_call=HIT-1,callee=0x0812D8DC,static_successor=HIT+3)
CLAIMS=dict(proof_scope='conditional_actual_constructor_registration_and_finite_main_dispatch',external_constructor_invocation_is_precondition=True,item_menu_invocation_proven=False,full_story_reachability_claimed=False,actual_runtime_execution_observed=False,universal_heap_or_irq_lifetime_proven=False,opaque_callee_effects_proven=False,bl_return_observed=False,whole_function_range_classified=False,maximum_target_access_width_proven=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT={
 'root':'UseFameChecker API invocation is a conditional entry; actual AllocZeroed(36), object stores, SetMainCallback2 and state0 are executed, then each frame uses the actual main callback consumer/interwork. Item table/Bag invocation and natural play are separate unresolved obligations.',
 'allocation':'actual first-fit allocator and AllocZeroed wrappers for requests36,2048,4096,2048,136; well-formed disjoint heap with successful fits; exact BIOS CpuSet zero-fill output is conditional. Object, buffers, list and caller stack are disjoint.',
 'records':'readable SaveBlock1 identity with 16 fame records; record0 pickState2 and flavor bit0, others pickState0; actual 16-row enumeration and AdjustGiovanniIndex wrapper with conditional FlagGet0 produce unlockedPersons[0]=0, then actual six-icon loop reads record0.',
 'state':'callback1 null and SaveFailed/Help callbacks return0 at the finite main dispatches; actual setup states0..5 normal continuations increment to6; actual table selects icon setup case6.',
 'resources':'each explicit external graphics/window/BG/list call has valid resources at its use; successful CreateObjectGraphicsSprite and PlaceQuestionMarkTile calls return distinct valid IDs0..5 in gSprites. Their implementation, rendering, and all IRQ effects remain conditional.',
 'arithmetic':'actual six loop positions0..5 call the real division/modulo targets with divisor3; normal scalar results i//3 and i%3 are explicit conditional arithmetic boundaries, not proved library-wide.',
 'liveness':'each normal Thumb ABI boundary preserves r4-r11, SP and the computed actual future-read-before-write memory projection only; all other existing RAM is destroyed in a second execution. Produced outputs are separate from preservation. No implicit whole heap/task/IRQ freeze.',
 'epoch':'allocation epochs and use-time resource validity are conditional; freeing/reinitializing an allocation while it remains live is rejected. No whole-play allocator lifetime claim.',
 'stop':'stop immediately before complete BL at0812DAEE after real record-derived result and constructor-produced inPickMode0; classify BL plus static branch successor only, no target return or whole function.'}
def exact(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)
def encoded(i):
 return summary.encoded(i)
def bind_semantics(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'ui semantic '+hex(i.address))
 for a,v in WORDS.items():need(type(v)is int and d.u32(raw,a)==v,'ui literal/table '+hex(a))
 need(int.from_bytes(chunk(raw,0x084218EE,2),'little')==0xFE00,'actual Oak nontrainer index')
 need(int.from_bytes(chunk(raw,0x08421B50,1),'little')==103,'actual sign icon selected by record0')
 for i in summary.BIOS_SEMANTICS:need(chunk(raw,i.address,i.size)==encoded(i),'actual BIOS boundary wrapper')
 need(identity(chunk(raw,HIT-1,6))=={k:BOUNDARY[k] for k in ('size','sha256')},'complete BL and static branch minimum')
def protected_windows(review):
 rows=review['windows'];need(type(rows)is list and len(rows)==len(WINDOWS),'closed ui window count')
 need(all(type(r)is dict and set(r)=={'label','address','size','sha256'} for r in rows),'address-size-SHA only')
 need(exact([(r['label'],r['address'],r['size'])for r in rows],[(k,*v)for k,v in WINDOWS.items()]),'exact ordered ui geometry')
 need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef'for c in r['sha256'])for r in rows),'SHA format')
 return [{k:r[k]for k in ('address','size','sha256')}for r in rows]
def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'closed source dependencies')
 for key,b in sources.items():
  need(identity(b)=={k:SOURCE_IDS[key][k]for k in ('size','sha256')},'source identity '+key)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==SOURCE_IDS[key]['git_blob_sha'],'source Git blob '+key)
 for token in ('void UseFameChecker(MainCallback savedCallback)','SetMainCallback2(MainCB2_LoadFameChecker);','CreateAllFlavorTextIcons(FAMECHECKER_OAK);','sFameCheckerData->unlockedPersons[nitems] = fameCheckerIdx;','gSaveBlock1Ptr->fameChecker[sFameCheckerData->unlockedPersons[who]].flavorTextFlags'):
  need(token in sources['pret-fame_checker.c'].decode(),'public Fame Checker role '+token)
 need('RunHelpSystemCallback()'in sources['pret-main.c'].decode(),'public main dispatch')
 need('AllocZeroed' in sources['pret-malloc.c'].decode(),'public allocation role')
class Machine(summary.Machine):
 def step(self,branch_choice=None):
  i=self.instructions[self.pc]
  if i.kind=='alu_ext'and i.args[0]=='asr':
   _,rd,rs=i.args;v,n=self.reg[rd],self.reg[rs]
   need(type(v)is int and type(n)is int and 0<=n<32,'bounded concrete arithmetic register shift')
   self.reg[rd]=((v if v<1<<31 else v-(1<<32))>>n)&0xFFFFFFFF;self.pc+=2;self.steps+=1;return
  return super().step(branch_choice)
EXTERNAL_CALLS={i.address:i.args[0]for i in INS.values()if i.kind=='call'and i.args[0]not in INS}
def _spans(cells):
 out=[]
 for a in sorted(cells):
  if out and out[-1][0]+out[-1][1]==a:out[-1][1]+=1
  else:out.append([a,1])
 return out
def _compose(raw,boundary_live=None,boundary_epochs=None,opaque_writes=None,epoch_events=None,normal_returns=True,zero_fill=True,resources_valid=True,save_flags=6,main_callback1=0):
 need(normal_returns is True and zero_fill is True and resources_valid is True,'conditional return, zero-fill and resource effects required')
 need(type(save_flags)is int and save_flags==6,'record0 pickState2 and one unlocked flavor bit profile')
 need(type(main_callback1)is int and main_callback1==0,'selected actual main requires null callback1')
 mem,_=runtime.heap_fixture([(0,runtime.LIMIT-16)])
 runtime.setmem(mem,MAIN,4,main_callback1)
 # This is an input SaveBlock record condition, not a fabricated UI producer.
 save_base=0x02022000;runtime.setmem(mem,SAVE,4,save_base)
 for ix in range(16):runtime.setmem(mem,save_base+0x3A54+4*ix,4,save_flags if ix==0 else 0)
 # The template has global zero initialization; actual initializer overwrites its fields.
 for a in range(0x03005F00,0x03005F18):mem[a]=0
 trace=[];boundaries=[];allocations=[];events=[];pointer=None;phase='constructor';sprite_ids=[];resource_uses=[]
 def run(entry,memory,stop=None,regs=None):
  nonlocal pointer
  m=Machine(raw,entry,registers=regs,memory=memory,instructions=INS);m.trace=trace
  while m.pc!=0xFFFFFFF0 and m.pc!=stop:
   if m.pc in INS:
    if m.pc==0x0812CBA8:
     pointer=m.read(CELL,4);need(type(pointer)is int and pointer==allocations[0]['pointer'],'actual object pointer store');events.append(dict(role='constructor_object',pointer=pointer,site=0x0812CBA6))
    if m.pc==0x0812E788:
     need(m.reg[5]==0 and m.reg[4]==0,'actual first record-derived person slot0');events.append(dict(role='actual_person_slot_writer',site=m.pc,index=m.reg[5],slot=m.reg[4]))
    if m.pc==0x0812D9BC:need(m.reg[0]==0 and m.read(pointer+12,1)==0,'actual setup call uses produced first person')
    m.step();continue
   site,target=m.reg[14]-5,m.pc
   need(EXTERNAL_CALLS.get(site)==target,'unlisted external boundary '+hex(site)+' -> '+hex(target))
   need(target!=runtime.ASSERT,'actual allocator assertion cannot be assumed to return')
   affected=(epoch_events or {}).get(site,{})
   if boundary_epochs is not None:
    live_epochs=boundary_epochs[len(boundaries)]
    need(not(affected.get('heap_reinitialized',False)and live_epochs),'live heap epoch reinitialization rejected')
    need(not any(p in affected.get('freed',())for p in live_epochs),'live allocated resource epoch freed')
   result=runtime.U;outputs=[];before=len(trace);resources=[]
   def use_resource(p):
    need(any(x['pointer']==p for x in allocations),'actual allocated resource identity')
    resources.append(p)
   if target==0x08001FA0:use_resource(m.reg[1])
   if target in (0x080017D0,0x08002124,0x08002228,0x080020BC):
    bg=m.reg[0];need(bg in (1,2,3),'selected BG resource')
    use_resource(m.read({1:0x0203B068,2:0x0203B06C,3:0x0203B064}[bg],4))
   if target in (0x080F6168,0x0813C034,0x08001960,0x0807FB44):result=0
   elif target==0x081C7A88:
    n=(m.reg[2]&0x1FFFF)*4;dest=m.reg[1]
    need(m.reg[2]>>24==5 and m.read(m.reg[0],4)==0 and n in (36,2048,4096,136),'actual finite zero fill request')
    need(runtime.ROOT+16<=dest and dest+n<=runtime.ROOT+runtime.LIMIT,'bounded nonalias destination')
    for old in allocations:need(dest+n<=old['pointer']or old['pointer']+old['size']<=dest,'distinct allocation extents')
    for j in range(n):m.mem[dest+j]=0
    trace.append(('write',dest,n));allocations.append(dict(pointer=dest,size=n));outputs=[dict(role='conditional_exact_word_zero_fill',address=dest,size=n)]
   elif target==0x08107AFC:
    need(m.reg[0]==0x03005F00,'actual initialized list template');use_resource(m.read(m.reg[0],4));result=0
    outputs=[dict(role='valid_list_menu_task',task_id=0,required_at_this_call=True)]
   elif target in (0x081C85A4,0x081C852C):
    x,y=m.reg[0],m.reg[1];need(type(x)is int and 0<=x<=5 and y==3,'six finite icon coordinate arithmetic')
    result=x%3 if target==0x081C85A4 else x//3
    outputs=[dict(role='conditional_arithmetic_scalar',dividend=x,divisor=y,result=result)]
   elif target==0x0805E404:
    need(tuple(m.reg[:4])==(103,0,114,47),'record0 icon arguments');result=0;sprite_ids.append(result)
    outputs=[dict(role='conditional_valid_object_sprite',sprite_id=result,graphics_id=103,resource_live_at_call=True)]
   elif target==0x0812DF94:
    ix=len(sprite_ids);need(1<=ix<=5,'five question marks follow visible flavor icon')
    need((m.reg[0],m.reg[1])==(114+47*(ix%3),31+27*(ix//3)),'actual question mark coordinates')
    result=ix;sprite_ids.append(result)
    outputs=[dict(role='conditional_valid_question_sprite',sprite_id=result,resource_live_at_call=True)]
   elif target==0x081534CC:
    need(m.reg[0]==2,'actual text palette selector');result=0x0203D000
    outputs=[dict(role='conditional_valid_palette_pointer',address=result,size=32,live_until_site=0x0812CD0E)]
   if target in (0x080019BC,0x080020BC):need(type(m.reg[0])is int and 0<=m.reg[0]<4,'bounded valid background')
   idx=len(boundaries);produced=[[a,n]for kind,a,n in trace[before:]if kind=='write']
   row=dict(index=idx,phase=phase,site=site,target=target,normal_return_assumed=True,effects_discharged=False,return_value=result if type(result)is int else 'unspecified',conditional_outputs=outputs,produced_memory_ranges=produced,use_time_allocation_resources=list(resources),allocation_count_at_boundary=len(allocations),graphics_and_list_resources_valid_at_use_assumed=target in (0x0805E404,0x0812DF94,0x08107AFC,0x08003AF0,0x0812D6A8,0x0812E7EC,0x0812CE30))
   boundaries.append(row);resource_uses.append(resources);trace.append(('boundary',idx,0))
   if boundary_live is not None:
    live={a+j for a,n in boundary_live[idx]for j in range(n)}
    for a,n,v in (opaque_writes or {}).get(site,[]):
     need(type(a)is int and type(n)is int and n>0,'bounded counterexample write')
     need(not any(a+j in live for j in range(n)),'opaque write intersects actual future-live projection')
     for j in range(n):m.mem[a+j]=(v>>(8*j))&255
    for a in list(m.mem):
     if a not in live:m.mem[a]=runtime.U
   for reg in (0,1,2,3,12):m.reg[reg]=runtime.U
   m.reg[0]=result;m.flag_pc=None;m.pc=m.reg[14]&~1
  if stop is None:need(m.reg[13]==0x03007000,'balanced selected phase stack')
  return m
 m=run(ROOT['constructor'],mem,regs={0:0})
 need(m.read(MAIN+4,4)==ROOT['setup_callback']and m.read(MAIN+1080,1)==0,'actual constructor registry and state0')
 events.append(dict(role='actual_callback_registered',callback=ROOT['setup_callback'],state=0))
 phase='setup'
 for state in range(7):
  need(m.read(MAIN+4,4)==ROOT['setup_callback']and m.read(MAIN+1080,1)==state,'actual registered callback and state producer')
  events.append(dict(role='main_dispatched_setup',state=state))
  m=run(ROOT['main_dispatch'],m.mem,stop=HIT-1 if state==6 else None)
 need(m.pc==HIT-1 and m.reg[0]==0,'target BL reached from actual no-pick-mode branch')
 need(sprite_ids==list(range(6)),'six distinct successful sprite outputs')
 need([a['size']for a in allocations]==[36,2048,4096,2048,136],'five actual allocations')
 live=set();per_boundary=[None]*len(boundaries)
 for kind,a,n in reversed(trace):
  if kind=='read':live.update(range(a,a+n))
  elif kind=='write':live.difference_update(range(a,a+n))
  else:per_boundary[a]=_spans(live)
 if boundary_live is not None:need(exact(per_boundary,boundary_live),'repeat exact future-read projection')
 epoch_projection=[None]*len(boundaries);future_resources=set()
 for i in reversed(range(len(boundaries))):
  future_resources.update(resource_uses[i]);used={a+j for a,n in per_boundary[i]for j in range(n)}
  existing={p['pointer']for p in allocations[:boundaries[i]['allocation_count_at_boundary']]}
  epoch_projection[i]=sorted(existing&(future_resources|{p['pointer']for p in allocations if any(p['pointer']<=a<p['pointer']+p['size']for a in used)}))
 if boundary_epochs is not None:need(exact(epoch_projection,boundary_epochs),'repeat exact use-time epoch projection')
 for i,row in enumerate(boundaries):
  out={a+j for a,n in row['produced_memory_ranges']for j in range(n)};used={a+j for a,n in per_boundary[i]for j in range(n)}
  row['preserve_projection']=_spans(used-out);row['produced_memory_ranges']=_spans(out&used);row['live_allocation_epochs']=epoch_projection[i]
 m.boundary_live=per_boundary;m.boundary_epochs=epoch_projection
 return m,dict(status='PASS_CONDITIONAL_REGISTERED_FAME_CHECKER_MINIMUM_THUMB',events=events,allocations=allocations,conditional_call_catalog=boundaries,live_projection_replay_checked=boundary_live is not None,live_projection_method='actual finite read-before-write at each opaque boundary, including saved ABI stack; all existing non-live RAM destroyed in replay',stopped_at=m.pc,callee_at_hit_executed=False,synthetic_contract_execution=True,**CLAIMS)
def compose_selected(raw,**kwargs):
 first,proof=_compose(raw,**kwargs)
 second,replay=_compose(raw,boundary_live=first.boundary_live,boundary_epochs=first.boundary_epochs,**kwargs)
 need(exact(proof['events'],replay['events']),'same registered producer chain under non-live destruction')
 return replay
def evidence_template():
 return dict(schema_version=1,root_verified=True,root=copy.deepcopy(ROOT),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),instruction_window=dict(BOUNDARY),instructions=[dict(address=HIT-1,size=4,role='complete_thumb_bl',callee=0x0812D8DC),dict(address=HIT+3,size=2,role='static_thumb_branch_return_successor',target=0x0812DB08)],literal_pool_included=False,type_classification_only=True)
def witness_geometry(e):
 need(exact(e,evidence_template()),'exact conditional UI minimum proof')
 need(HIT-1<=HIT and HIT+4<=HIT-1+6,'four hit bytes within complete instructions');return HIT-1,6
def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hit','root','windows','claims','input_contract'},'closed UI review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'integer schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE),'current candidate required')
 need(exact(review['diagnostic_input'],DIAGNOSTIC),'distinct old diagnostic')
 need(exact(review['root'],ROOT)and exact(review['claims'],CLAIMS)and exact(review['input_contract'],CONTRACT),'exact bounded contract')
 rows=[h for h in inherited['hits']if h['address']==HIT]
 need(len(rows)==1 and exact(rows[0],review['hit'])and rows[0]['accepted']is False and rows[0]['owner_candidates']==[],'unchanged owner-external unknown')
 need(type(rows[0]['size'])is int and rows[0]['size']==4 and rows[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','four-byte hit')
 d.signed(raw,rows[0]);sources_bind(review,sources);d.signed(raw,protected_windows(review));bind_semantics(raw)
 composition=compose_selected(raw);e=evidence_template();a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_ONE_CONDITIONAL_FAME_CHECKER_TYPE',count=1,hit=HIT,composition=composition,source_bindings=SOURCE_IDS,**CLAIMS)
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current required; diagnostic cannot classify current');return _regions(raw,inherited,review,sources)
def make_review(raw,hit):
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hit=copy.deepcopy(hit),root=copy.deepcopy(ROOT),windows=[dict(label=k,address=a,**identity(chunk(raw,a,n)))for k,(a,n)in WINDOWS.items()],claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT))
