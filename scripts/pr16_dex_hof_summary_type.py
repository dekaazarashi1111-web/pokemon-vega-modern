"""Summary実登録根からの条件付き最小Thumb型。自然play・外部全効果は主張しない。"""
import copy
import hashlib
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_callback_party_task as task
import pr16_dex_hof_lifetime_setup as setup
import pr16_dex_hof_lifetime_menu as menu
import pr16_dex_hof_runtime_party as runtime
import pr16_dex_hof_party_takeitem as take
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
HIT=0x081357A7
KIND='rooted_summary_minimum_thumb'
BOUNDARY=dict(address=HIT-1,size=6,sha256='6570922a7580672b38c1f0668e9ee48e0e97e142d3bef31184dc55845cd2f2cc')
SUMMARY,SKILLS,MAIN,TASKS,PARTY,MONS,CURSOR=0x0203B0B4,0x0203B0B8,take.MAIN,take.TASKS,take.PARTY,take.MONS,take.CURSOR
SOURCE_IDS=copy.deepcopy(take.SOURCE_IDS)
SOURCE_IDS['pret-pokemon_summary_screen.c']=dict(local='pret-pokemon_summary_screen.c',repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',path='src/pokemon_summary_screen.c',size=171314,sha256='855a17fb555f5497dbb47f90a8c1b8cf620532d3bff96e8196d0790515508583',git_blob_sha='b3e3c7763d3e1c9cf2185cd7344fdf49ba78ae85',url='https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/pokemon_summary_screen.c')
BLOCKS={}
def put(name,address,specs):BLOCKS[name]=tuple(party.block(address,specs))
# 実operandによる独立Thumb encoding。ROM断片やopcode配列は保存しない。
put('summary_action_0',0x08123528,[
 ('push', 16, True),
 ('addi', 4, 0, 0),
 ('shift', 'lsl', 4, 4, 24),
 ('shift', 'lsr', 4, 4, 24),
 ('imm', 'mov', 0, 5),
 ('call', 134683248),
 ('literal', 0, 135411020),
 ('mem', True, 'word', 1, 0, 0),
 ('literal', 0, 135411024),
 ('mem', False, 'word', 0, 1, 4),
 ('addi', 0, 4, 0),
 ('call', 135397992),
 ('pop', 16, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('summary_callback_0',0x08123554,[
 ('push', 16, True),
 ('spadd', -4),
 ('literal', 4, 135411080),
 ('mem', True, 'byte', 1, 4, 8),
 ('imm', 'mov', 0, 15),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135411048),
 ('call', 135432620),
 ('literal', 0, 135411084),
 ('mem', True, 'byte', 1, 4, 9),
 ('literal', 2, 135411088),
 ('mem', True, 'byte', 2, 2, 0),
 ('imm', 'sub', 2, 1),
 ('shift', 'lsl', 2, 2, 24),
 ('shift', 'lsr', 2, 2, 24),
 ('literal', 3, 135411092),
 ('imm', 'mov', 4, 0),
 ('spmem', False, 4, 0),
 ('call', 135482596),
 ('spadd', 4),
 ('pop', 16, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('summary_constructor_0',0x08134CE4,[
 ('push', 240, True),
 ('movhi', 7, 10),
 ('movhi', 6, 9),
 ('movhi', 5, 8),
 ('push', 224, False),
 ('movhi', 8, 0),
 ('addi', 7, 3, 0),
 ('spmem', True, 0, 32),
 ('shift', 'lsl', 1, 1, 24),
 ('shift', 'lsr', 6, 1, 24),
 ('shift', 'lsl', 2, 2, 24),
 ('shift', 'lsr', 2, 2, 24),
 ('movhi', 9, 2),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('movhi', 10, 0),
 ('literal', 5, 135482664),
 ('literal', 0, 135482668),
 ('call', 134228912),
 ('mem', False, 'word', 0, 5, 0),
 ('literal', 4, 135482672),
 ('imm', 'mov', 0, 40),
 ('call', 134228912),
 ('mem', False, 'word', 0, 4, 0),
 ('mem', True, 'word', 5, 5, 0),
 ('imm', 'cmp', 5, 0),
 ('branch', 1, 135482676),
 ('addi', 0, 7, 0),
 ('call', 134219076),
 ('jump', 135483106),
])
put('summary_constructor_1',0x08134D34,[
 ('literal', 0, 135482720),
 ('mem', False, 'byte', 6, 0, 0),
 ('literal', 0, 135482724),
 ('imm', 'mov', 1, 0),
 ('mem', False, 'byte', 1, 0, 0),
 ('literal', 0, 135482728),
 ('mem', False, 'byte', 1, 0, 0),
 ('literal', 1, 135482732),
 ('add', 0, 5, 1),
 ('mem', False, 'word', 7, 0, 0),
 ('literal', 2, 135482736),
 ('add', 0, 5, 2),
 ('movhi', 3, 8),
 ('mem', False, 'word', 3, 0, 0),
 ('literal', 0, 135482740),
 ('comparehi', 8, 0),
 ('branch', 1, 135482748),
 ('literal', 0, 135482744),
 ('add', 1, 5, 0),
 ('imm', 'mov', 0, 1),
 ('jump', 135482754),
])
put('summary_constructor_2',0x08134D7C,[
 ('literal', 2, 135482796),
 ('add', 1, 5, 2),
 ('imm', 'mov', 0, 0),
 ('mem', False, 'word', 0, 1, 0),
 ('literal', 4, 135482800),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 3, 135482804),
 ('add', 0, 0, 3),
 ('imm', 'mov', 5, 0),
 ('movhi', 1, 9),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135482808),
 ('add', 0, 0, 1),
 ('movhi', 2, 10),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 3),
 ('branch', 12, 135482812),
 ('imm', 'cmp', 0, 2),
 ('branch', 10, 135482904),
 ('jump', 135482816),
])
put('summary_constructor_3',0x08134DBC,[
 ('imm', 'cmp', 0, 5),
 ('branch', 0, 135482860),
 ('imm', 'mov', 0, 6),
 ('call', 135444980),
 ('literal', 2, 135482852),
 ('mem', True, 'word', 0, 2, 0),
 ('imm', 'mov', 3, 199),
 ('shift', 'lsl', 3, 3, 6),
 ('add', 0, 0, 3),
 ('imm', 'mov', 1, 0),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 2, 0),
 ('imm', 'add', 3, 8),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 2, 0),
 ('literal', 2, 135482856),
 ('add', 0, 0, 2),
 ('jump', 135482938),
])
put('summary_constructor_4',0x08134DEC,[
 ('imm', 'mov', 0, 6),
 ('call', 135444980),
 ('mem', True, 'word', 0, 4, 0),
 ('imm', 'mov', 3, 199),
 ('shift', 'lsl', 3, 3, 6),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 5, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135482896),
 ('add', 0, 0, 1),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135482900),
 ('add', 0, 0, 2),
 ('mem', False, 'byte', 5, 0, 0),
 ('jump', 135482940),
])
put('summary_constructor_5',0x08134E18,[
 ('imm', 'mov', 0, 8),
 ('call', 135444980),
 ('mem', True, 'word', 0, 4, 0),
 ('imm', 'mov', 3, 199),
 ('shift', 'lsl', 3, 3, 6),
 ('add', 0, 0, 3),
 ('imm', 'mov', 1, 3),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135483120),
 ('add', 0, 0, 1),
 ('mem', False, 'byte', 5, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135483124),
 ('add', 0, 0, 2),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 0, 0),
 ('literal', 5, 135483128),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 3, 135483132),
 ('add', 0, 0, 3),
 ('imm', 'mov', 2, 0),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 1, 135483136),
 ('add', 0, 0, 1),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'add', 3, 8),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'add', 1, 8),
 ('add', 0, 0, 1),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'sub', 3, 64),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'sub', 1, 64),
 ('add', 0, 0, 1),
 ('imm', 'mov', 1, 2),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'add', 3, 8),
 ('add', 0, 0, 3),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'add', 3, 4),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'sub', 3, 28),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 2, 135483140),
 ('add', 0, 0, 2),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 4, 135483144),
 ('add', 0, 0, 4),
 ('call', 135500624),
 ('mem', True, 'word', 0, 5, 0),
 ('add', 0, 0, 4),
 ('imm', 'mov', 1, 45),
 ('call', 134476628),
 ('mem', True, 'word', 1, 5, 0),
 ('literal', 3, 135483148),
 ('add', 1, 1, 3),
 ('mem', False, 'byte', 0, 1, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('add', 0, 0, 4),
 ('imm', 'mov', 1, 4),
 ('call', 134476628),
 ('mem', True, 'word', 1, 5, 0),
 ('literal', 2, 135483152),
 ('add', 1, 1, 2),
 ('mem', False, 'byte', 0, 1, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('add', 2, 0, 2),
 ('mem', True, 'byte', 1, 2, 0),
 ('imm', 'cmp', 1, 1),
 ('branch', 1, 135483090),
 ('literal', 2, 135483148),
 ('add', 0, 0, 2),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 3, 135483156),
 ('add', 0, 0, 3),
 ('imm', 'mov', 1, 255),
 ('mem', False, 'byte', 1, 0, 0),
 ('literal', 0, 135483160),
 ('call', 134219076),
 ('pop', 56, False),
 ('movhi', 8, 3),
 ('movhi', 9, 4),
 ('movhi', 10, 5),
 ('pop', 240, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('summary_setup_0',0x081363FC,[
 ('push', 16, True),
 ('spadd', -4),
 ('literal', 0, 135488540),
 ('mem', True, 'word', 0, 0, 0),
 ('literal', 1, 135488544),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 15),
 ('branch', 9, 135488528),
 ('jump', 135489214),
 ('shift', 'lsl', 0, 0, 2),
 ('literal', 1, 135488548),
 ('add', 0, 0, 1),
 ('mem', True, 'word', 0, 0, 0),
 ('movhi', 15, 0),
])
put('summary_setup_1',0x08136468,[
 ('call', 135498060),
 ('jump', 135489224),
 ('call', 135492512),
 ('jump', 135489224),
 ('call', 135492488),
 ('jump', 135489224),
 ('call', 135489256),
 ('jump', 135488656),
 ('call', 135492296),
 ('jump', 135488656),
 ('call', 135498096),
 ('jump', 135489224),
 ('call', 135489588),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135488664),
 ('jump', 135489238),
 ('jump', 135489224),
 ('call', 135493392),
 ('jump', 135489224),
 ('call', 135494816),
 ('jump', 135489224),
 ('call', 135496616),
 ('call', 135500288),
 ('jump', 135489224),
 ('literal', 0, 135488724),
 ('mem', True, 'word', 0, 0, 0),
 ('literal', 2, 135488728),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'sub', 0, 2),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('imm', 'cmp', 0, 1),
 ('branch', 8, 135488736),
 ('literal', 1, 135488732),
 ('imm', 'mov', 0, 3),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134225984),
 ('jump', 135488748),
])
put('summary_setup_2',0x081364E0,[
 ('literal', 1, 135488756),
 ('imm', 'mov', 0, 3),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134225984),
 ('call', 135499008),
 ('jump', 135489224),
])
put('summary_setup_3',0x081364F8,[
 ('literal', 4, 135488784),
 ('mem', True, 'word', 1, 4, 0),
 ('literal', 2, 135488788),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135488796),
 ('imm', 'add', 2, 60),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('literal', 1, 135488792),
 ('jump', 135488882),
])
put('summary_setup_4',0x0813651C,[
 ('literal', 2, 135488840),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'sub', 0, 2),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('imm', 'cmp', 0, 1),
 ('branch', 8, 135488856),
 ('imm', 'add', 2, 52),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('literal', 1, 135488844),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134225984),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135488848),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('literal', 1, 135488852),
 ('jump', 135488882),
])
put('summary_setup_5',0x08136558,[
 ('literal', 2, 135488892),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('literal', 1, 135488896),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134225984),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135488900),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('literal', 1, 135488904),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134225984),
 ('jump', 135489224),
])
put('summary_setup_6',0x0813658C,[
 ('imm', 'mov', 0, 1),
 ('alu', 'neg', 0, 0),
 ('imm', 'mov', 1, 16),
 ('imm', 'mov', 2, 0),
 ('call', 134679672),
 ('literal', 0, 135488944),
 ('mem', True, 'word', 0, 0, 0),
 ('imm', 'mov', 2, 199),
 ('shift', 'lsl', 2, 2, 6),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135496912),
 ('call', 135497168),
 ('jump', 135489224),
])
put('summary_setup_7',0x081365B4,[
 ('imm', 'mov', 0, 1),
 ('alu', 'neg', 0, 0),
 ('imm', 'mov', 1, 0),
 ('spmem', False, 1, 0),
 ('imm', 'mov', 2, 16),
 ('imm', 'mov', 3, 0),
 ('call', 134675756),
 ('literal', 4, 135489068),
 ('mem', True, 'word', 0, 4, 0),
 ('imm', 'mov', 1, 192),
 ('shift', 'lsl', 1, 1, 6),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135489072),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135489076),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135489080),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135489084),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135489088),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135489092),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('jump', 135489224),
])
put('summary_setup_8',0x08136648,[
 ('imm', 'mov', 0, 0),
 ('call', 134226108),
 ('imm', 'mov', 0, 2),
 ('call', 134226108),
 ('imm', 'mov', 0, 1),
 ('call', 134226108),
 ('imm', 'mov', 0, 3),
 ('call', 134226108),
 ('jump', 135489224),
 ('literal', 0, 135489156),
 ('mem', True, 'word', 0, 0, 0),
 ('literal', 2, 135489160),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'sub', 0, 2),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('imm', 'cmp', 0, 1),
 ('branch', 8, 135489164),
 ('imm', 'mov', 0, 0),
 ('call', 135505596),
 ('imm', 'mov', 0, 0),
 ('call', 135506112),
 ('jump', 135489194),
])
put('summary_setup_9',0x0813668C,[
 ('imm', 'mov', 0, 0),
 ('call', 135504924),
 ('imm', 'mov', 0, 0),
 ('call', 135510124),
 ('imm', 'mov', 0, 0),
 ('call', 135505196),
 ('imm', 'mov', 0, 0),
 ('call', 135507992),
 ('imm', 'mov', 0, 0),
 ('call', 135508816),
 ('imm', 'mov', 0, 0),
 ('call', 135506832),
 ('imm', 'mov', 0, 0),
 ('call', 135509208),
 ('imm', 'mov', 0, 0),
 ('call', 135509648),
 ('jump', 135489224),
 ('call', 135498080),
 ('call', 135492908),
 ('jump', 135489238),
 ('literal', 0, 135489248),
 ('mem', True, 'word', 1, 0, 0),
 ('literal', 0, 135489252),
 ('add', 1, 1, 0),
 ('mem', True, 'byte', 0, 1, 0),
 ('imm', 'add', 0, 1),
 ('mem', False, 'byte', 0, 1, 0),
 ('spadd', 4),
 ('pop', 16, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('summary_finish_0',0x0813752C,[
 ('push', 16, True),
 ('literal', 4, 135492936),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135492940),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'sub', 0, 2),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('imm', 'cmp', 0, 1),
 ('branch', 8, 135492948),
 ('literal', 0, 135492944),
 ('jump', 135492950),
])
put('summary_finish_1',0x08137554,[
 ('literal', 0, 135492976),
 ('imm', 'mov', 1, 0),
 ('call', 134704052),
 ('mem', True, 'word', 1, 4, 0),
 ('literal', 2, 135492980),
 ('add', 1, 1, 2),
 ('mem', False, 'byte', 0, 1, 0),
 ('literal', 0, 135492984),
 ('call', 134219076),
 ('pop', 16, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('summary_scheduler_0',0x0813868C,[
 ('push', 0, True),
 ('call', 134704400),
 ('call', 134244056),
 ('call', 134244132),
 ('call', 134675572),
 ('pop', 1, False),
 ('bx', 0),
])
put('installed_summary_input_0',0x09378490,[
 ('push', 112, True),
 ('shift', 'lsl', 5, 0, 0),
 ('call', 154635220),
 ('literal', 3, 154633532),
 ('mem', True, 'word', 4, 3, 0),
 ('literal', 1, 154633536),
 ('shift', 'lsl', 0, 4, 0),
 ('call', 154635190),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 154633398),
 ('shift', 'lsl', 0, 5, 0),
 ('literal', 3, 154633540),
 ('call', 154633560),
 ('pop', 112, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('summary_interwork_0',0x09378558,[
 ('bx', 3),
])
put('summary_input_0',0x08135028,[
 ('push', 240, True),
 ('movhi', 7, 8),
 ('push', 128, False),
 ('spadd', -4),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('movhi', 8, 0),
 ('literal', 1, 135483476),
 ('mem', True, 'word', 0, 1, 0),
 ('literal', 2, 135483480),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('addi', 4, 1, 0),
 ('imm', 'cmp', 0, 5),
 ('branch', 9, 135483464),
 ('jump', 135484272),
 ('shift', 'lsl', 0, 0, 2),
 ('literal', 1, 135483484),
 ('add', 0, 0, 1),
 ('mem', True, 'word', 0, 0, 0),
 ('movhi', 15, 0),
])
put('summary_input_1',0x08135078,[
 ('imm', 'mov', 0, 1),
 ('alu', 'neg', 0, 0),
 ('imm', 'mov', 1, 0),
 ('spmem', False, 1, 0),
 ('imm', 'mov', 2, 16),
 ('imm', 'mov', 3, 0),
 ('call', 134675756),
 ('literal', 0, 135483536),
 ('mem', True, 'word', 0, 0, 0),
 ('jump', 135483582),
])
put('summary_input_2',0x08135094,[
 ('literal', 0, 135483568),
 ('mem', True, 'byte', 1, 0, 7),
 ('imm', 'mov', 0, 128),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483580),
 ('call', 135511880),
 ('literal', 0, 135483572),
 ('mem', True, 'word', 0, 0, 0),
 ('literal', 2, 135483576),
 ('add', 0, 0, 2),
 ('jump', 135484128),
])
put('summary_input_3',0x081350BC,[
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135483592),
 ('add', 0, 0, 1),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 0, 0),
 ('jump', 135484290),
])
put('summary_input_4',0x081350CC,[
 ('call', 135006460),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135483610),
 ('jump', 135484290),
 ('call', 134261864),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135483620),
 ('jump', 135484290),
 ('literal', 0, 135483688),
 ('call', 134704616),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 7, 0, 24),
 ('imm', 'cmp', 7, 0),
 ('branch', 0, 135483636),
 ('jump', 135484290),
 ('literal', 5, 135483692),
 ('mem', True, 'word', 0, 5, 0),
 ('imm', 'mov', 6, 199),
 ('shift', 'lsl', 6, 6, 6),
 ('add', 0, 0, 6),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 3),
 ('branch', 0, 135483876),
 ('imm', 'mov', 0, 1),
 ('call', 135483272),
 ('addi', 4, 0, 0),
 ('imm', 'cmp', 4, 1),
 ('branch', 1, 135483764),
 ('literal', 0, 135483696),
 ('call', 134704616),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135483704),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 2, 135483700),
 ('add', 0, 0, 2),
 ('mem', False, 'byte', 4, 0, 0),
 ('jump', 135484290),
])
put('summary_input_5',0x08135138,[
 ('mem', True, 'word', 0, 5, 0),
 ('add', 0, 0, 6),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 1),
 ('branch', 9, 135483716),
 ('jump', 135484290),
 ('imm', 'mov', 0, 5),
 ('call', 134683248),
 ('imm', 'mov', 0, 0),
 ('call', 134224336),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 1, 135483760),
 ('add', 0, 0, 1),
 ('mem', False, 'byte', 4, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('add', 0, 0, 6),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135498672),
 ('mem', True, 'word', 1, 5, 0),
 ('add', 1, 1, 6),
 ('mem', True, 'byte', 0, 1, 0),
 ('imm', 'add', 0, 1),
 ('mem', False, 'byte', 0, 1, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('jump', 135484048),
])
put('summary_input_6',0x08135174,[
 ('imm', 'mov', 0, 0),
 ('call', 135483272),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135483876),
 ('literal', 0, 135483800),
 ('call', 134704616),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 4, 0, 24),
 ('imm', 'cmp', 4, 0),
 ('branch', 0, 135483808),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 1, 135483804),
 ('add', 0, 0, 1),
 ('mem', False, 'byte', 7, 0, 0),
 ('jump', 135484290),
])
put('summary_input_7',0x081351A0,[
 ('mem', True, 'word', 0, 5, 0),
 ('add', 0, 0, 6),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483820),
 ('jump', 135484290),
 ('imm', 'mov', 0, 5),
 ('call', 134683248),
 ('imm', 'mov', 0, 0),
 ('call', 134224336),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 2, 135483868),
 ('add', 0, 0, 2),
 ('mem', False, 'byte', 4, 0, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('add', 0, 0, 6),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135498672),
 ('mem', True, 'word', 1, 5, 0),
 ('add', 1, 1, 6),
 ('mem', True, 'byte', 0, 1, 0),
 ('imm', 'sub', 0, 1),
 ('mem', False, 'byte', 0, 1, 0),
 ('mem', True, 'word', 0, 5, 0),
 ('literal', 1, 135483872),
 ('add', 0, 0, 1),
 ('jump', 135484052),
])
put('summary_input_8',0x081351E4,[
 ('literal', 0, 135483928),
 ('call', 134704616),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135483902),
 ('literal', 0, 135483932),
 ('call', 134704616),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483902),
 ('jump', 135484290),
 ('literal', 0, 135483936),
 ('mem', True, 'half', 1, 0, 46),
 ('imm', 'mov', 0, 64),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135483940),
 ('imm', 'mov', 1, 1),
 ('alu', 'neg', 1, 1),
 ('movhi', 0, 8),
 ('call', 135510280),
 ('jump', 135484290),
])
put('summary_input_9',0x08135224,[
 ('imm', 'mov', 0, 128),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135483958),
 ('movhi', 0, 8),
 ('imm', 'mov', 1, 1),
 ('call', 135510280),
 ('jump', 135484290),
 ('imm', 'mov', 0, 1),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135484068),
 ('literal', 4, 135483996),
 ('mem', True, 'word', 0, 4, 0),
 ('imm', 'mov', 5, 199),
 ('shift', 'lsl', 5, 5, 6),
 ('add', 0, 0, 5),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135484004),
 ('imm', 'mov', 0, 5),
 ('call', 134683248),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135484000),
 ('add', 0, 0, 2),
 ('jump', 135484084),
])
put('summary_input_10',0x08135264,[
 ('imm', 'cmp', 0, 2),
 ('branch', 0, 135484010),
 ('jump', 135484290),
 ('imm', 'mov', 0, 5),
 ('call', 134683248),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135484060),
 ('add', 0, 0, 1),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('add', 0, 0, 5),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135498672),
 ('mem', True, 'word', 1, 4, 0),
 ('add', 1, 1, 5),
 ('mem', True, 'byte', 0, 1, 0),
 ('imm', 'add', 0, 1),
 ('mem', False, 'byte', 0, 1, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135484064),
 ('add', 0, 0, 2),
 ('imm', 'mov', 1, 3),
 ('mem', False, 'byte', 1, 0, 0),
 ('jump', 135484290),
])
put('summary_input_11',0x081352A4,[
 ('imm', 'mov', 0, 2),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135484290),
 ('literal', 0, 135484092),
 ('mem', True, 'word', 0, 0, 0),
 ('literal', 1, 135484096),
 ('add', 0, 0, 1),
 ('imm', 'mov', 1, 4),
 ('mem', False, 'byte', 1, 0, 0),
 ('jump', 135484290),
])
put('summary_input_12',0x081352C4,[
 ('mem', True, 'word', 3, 4, 0),
 ('imm', 'mov', 2, 199),
 ('shift', 'lsl', 2, 2, 6),
 ('add', 0, 3, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 3),
 ('branch', 0, 135484144),
 ('literal', 0, 135484136),
 ('imm', 'mov', 1, 0),
 ('call', 134704052),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135484140),
 ('add', 0, 0, 1),
 ('imm', 'mov', 1, 2),
 ('mem', False, 'byte', 1, 0, 0),
 ('jump', 135484290),
])
put('summary_input_13',0x081352F0,[
 ('literal', 2, 135484176),
 ('literal', 1, 135484180),
 ('add', 0, 3, 1),
 ('mem', True, 'byte', 1, 0, 0),
 ('shift', 'lsl', 0, 1, 2),
 ('add', 0, 0, 1),
 ('shift', 'lsl', 0, 0, 3),
 ('add', 0, 0, 2),
 ('literal', 1, 135484184),
 ('mem', False, 'word', 1, 0, 0),
 ('literal', 2, 135484188),
 ('add', 1, 3, 2),
 ('imm', 'mov', 0, 2),
 ('mem', False, 'byte', 0, 1, 0),
 ('jump', 135484290),
])
put('summary_input_14',0x08135370,[
 ('literal', 0, 135484304),
 ('mem', True, 'byte', 1, 0, 7),
 ('imm', 'mov', 0, 128),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135484290),
 ('movhi', 0, 8),
 ('call', 135497228),
 ('spadd', 4),
 ('pop', 8, False),
 ('movhi', 8, 3),
 ('pop', 240, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('page_flip_input_0',0x08134F88,[
 ('push', 16, True),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 4, 0, 24),
 ('literal', 0, 135483316),
 ('mem', True, 'word', 1, 0, 0),
 ('literal', 2, 135483320),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483416),
 ('literal', 0, 135483324),
 ('add', 2, 1, 0),
 ('mem', True, 'byte', 1, 2, 0),
 ('addi', 0, 1, 0),
 ('imm', 'cmp', 0, 255),
 ('branch', 0, 135483328),
 ('compare', 0, 4),
 ('branch', 1, 135483328),
 ('imm', 'mov', 0, 255),
 ('mem', False, 'byte', 0, 2, 0),
 ('imm', 'mov', 0, 1),
 ('jump', 135483418),
])
put('page_flip_input_1',0x08134FC0,[
 ('addi', 0, 4, 0),
 ('call', 135483216),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483416),
 ('imm', 'cmp', 4, 0),
 ('branch', 0, 135483384),
 ('imm', 'cmp', 4, 1),
 ('branch', 1, 135483416),
 ('literal', 0, 135483376),
 ('mem', True, 'half', 1, 0, 46),
 ('imm', 'mov', 0, 16),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483312),
 ('literal', 0, 135483380),
 ('mem', True, 'word', 0, 0, 0),
 ('mem', True, 'byte', 0, 0, 19),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135483416),
 ('imm', 'mov', 0, 128),
 ('shift', 'lsl', 0, 0, 1),
 ('jump', 135483410),
])
put('page_flip_input_2',0x08134FF8,[
 ('literal', 0, 135483424),
 ('mem', True, 'half', 1, 0, 46),
 ('imm', 'mov', 0, 32),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483312),
 ('literal', 0, 135483428),
 ('mem', True, 'word', 0, 0, 0),
 ('mem', True, 'byte', 0, 0, 19),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135483416),
 ('imm', 'mov', 0, 128),
 ('shift', 'lsl', 0, 0, 2),
 ('alu', 'and', 0, 1),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135483312),
 ('imm', 'mov', 0, 0),
 ('pop', 16, False),
 ('pop', 2, False),
 ('bx', 1),
])
put('page_flip_task_0',0x08135394,[
 ('push', 240, True),
 ('spadd', -8),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('addi', 4, 0, 0),
 ('shift', 'lsl', 0, 4, 2),
 ('add', 0, 0, 4),
 ('shift', 'lsl', 0, 0, 3),
 ('literal', 6, 135484348),
 ('add', 7, 0, 6),
 ('imm', 'mov', 1, 0),
 ('signed_load', 'half', 0, 7, 1),
 ('imm', 'cmp', 0, 9),
 ('branch', 9, 135484338),
 ('jump', 135484924),
 ('shift', 'lsl', 0, 0, 2),
 ('literal', 1, 135484352),
 ('add', 0, 0, 1),
 ('mem', True, 'word', 0, 0, 0),
 ('movhi', 15, 0),
])
put('page_flip_task_1',0x081353EC,[
 ('call', 135486980),
 ('call', 135487156),
 ('literal', 4, 135484452),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135484456),
 ('add', 0, 0, 2),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 3, 135484460),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 1, 0, 0),
 ('mem', True, 'word', 0, 4, 0),
 ('imm', 'mov', 5, 199),
 ('shift', 'lsl', 5, 5, 6),
 ('add', 0, 0, 5),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135511828),
 ('mem', True, 'word', 0, 4, 0),
 ('add', 0, 0, 5),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135498268),
 ('jump', 135485016),
])
put('page_flip_task_2',0x08135430,[
 ('literal', 0, 135484592),
 ('mem', True, 'word', 1, 0, 0),
 ('imm', 'mov', 2, 199),
 ('shift', 'lsl', 2, 2, 6),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 3),
 ('branch', 0, 135484520),
 ('imm', 'cmp', 0, 2),
 ('branch', 1, 135484494),
 ('literal', 3, 135484596),
 ('add', 0, 1, 3),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135484520),
 ('imm', 'mov', 0, 30),
 ('spmem', False, 0, 0),
 ('imm', 'mov', 0, 20),
 ('spmem', False, 0, 4),
 ('imm', 'mov', 0, 0),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134227028),
 ('imm', 'mov', 0, 0),
 ('call', 134226108),
 ('imm', 'mov', 4, 30),
 ('spmem', False, 4, 0),
 ('imm', 'mov', 5, 2),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 1),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134227028),
 ('imm', 'mov', 6, 15),
 ('spmem', False, 6, 0),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 1),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 2),
 ('call', 134227028),
 ('spmem', False, 4, 0),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 2),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134227028),
 ('spmem', False, 6, 0),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 2),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 2),
 ('call', 134227028),
 ('jump', 135485016),
])
put('page_flip_task_3',0x081354B8,[
 ('call', 135488100),
 ('call', 135488344),
 ('call', 135499008),
 ('literal', 0, 135484632),
 ('mem', True, 'word', 0, 0, 0),
 ('imm', 'mov', 1, 199),
 ('shift', 'lsl', 1, 1, 6),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135496912),
 ('jump', 135485016),
])
put('page_flip_task_4',0x081354DC,[
 ('literal', 4, 135484676),
 ('mem', True, 'word', 0, 4, 0),
 ('imm', 'mov', 2, 192),
 ('shift', 'lsl', 2, 2, 6),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 3, 135484680),
 ('add', 0, 0, 3),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135484684),
 ('add', 0, 0, 1),
 ('jump', 135484870),
])
put('page_flip_task_5',0x08135510,[
 ('call', 134224224),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135484700),
 ('jump', 135485022),
 ('imm', 'mov', 0, 3),
 ('call', 134226108),
 ('imm', 'mov', 0, 2),
 ('call', 134226108),
 ('imm', 'mov', 0, 1),
 ('call', 134226108),
 ('jump', 135485016),
 ('call', 135486692),
 ('literal', 0, 135484740),
 ('mem', True, 'word', 0, 0, 0),
 ('literal', 2, 135484744),
 ('add', 0, 0, 2),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 0, 0),
 ('jump', 135485016),
])
put('page_flip_task_6',0x0813554C,[
 ('literal', 0, 135484772),
 ('mem', True, 'word', 0, 0, 0),
 ('literal', 3, 135484776),
 ('add', 0, 0, 3),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135487332),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135484770),
 ('jump', 135485022),
 ('jump', 135485016),
])
put('page_flip_task_7',0x0813556C,[
 ('call', 135493392),
 ('literal', 0, 135484816),
 ('mem', True, 'word', 0, 0, 0),
 ('imm', 'mov', 1, 199),
 ('shift', 'lsl', 1, 1, 6),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 3),
 ('branch', 0, 135484804),
 ('call', 135494816),
 ('call', 135496616),
 ('call', 135500288),
 ('jump', 135485016),
])
put('page_flip_task_8',0x08135594,[
 ('literal', 4, 135484880),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135484884),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 3, 135484888),
 ('add', 0, 0, 3),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135484892),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 2, 135484896),
 ('add', 0, 0, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'mov', 1, 2),
 ('call', 134233836),
 ('jump', 135485016),
])
put('page_flip_task_9',0x081355E4,[
 ('call', 134224224),
 ('shift', 'lsl', 0, 0, 24),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135485022),
 ('imm', 'mov', 0, 0),
 ('call', 134226108),
 ('imm', 'mov', 0, 0),
 ('call', 134224316),
 ('jump', 135485016),
 ('call', 135498716),
 ('literal', 5, 135484996),
 ('mem', True, 'word', 1, 5, 0),
 ('imm', 'mov', 3, 199),
 ('shift', 'lsl', 3, 3, 6),
 ('add', 0, 1, 3),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 3),
 ('branch', 1, 135484966),
 ('addi', 2, 6, 0),
 ('imm', 'sub', 2, 8),
 ('literal', 3, 135485000),
 ('add', 0, 1, 3),
 ('mem', True, 'byte', 1, 0, 0),
 ('shift', 'lsl', 0, 1, 2),
 ('add', 0, 0, 1),
 ('shift', 'lsl', 0, 0, 3),
 ('add', 0, 0, 2),
 ('literal', 1, 135485004),
 ('mem', False, 'word', 1, 0, 0),
 ('addi', 0, 4, 0),
 ('call', 134704288),
 ('imm', 'mov', 0, 0),
 ('mem', False, 'half', 0, 7, 0),
 ('mem', True, 'word', 1, 5, 0),
 ('literal', 2, 135485008),
 ('add', 1, 1, 2),
 ('mem', False, 'byte', 0, 1, 0),
 ('mem', True, 'word', 1, 5, 0),
 ('literal', 3, 135485012),
 ('add', 1, 1, 3),
 ('mem', False, 'byte', 0, 1, 0),
 ('jump', 135485022),
])
put('page_flip_task_10',0x08135658,[
 ('mem', True, 'half', 0, 7, 0),
 ('imm', 'add', 0, 1),
 ('mem', False, 'half', 0, 7, 0),
 ('spadd', 8),
 ('pop', 240, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('frominfo_prefix_0',0x08135668,[
 ('push', 112, True),
 ('spadd', -8),
 ('literal', 4, 135485064),
 ('mem', True, 'word', 0, 4, 0),
 ('literal', 1, 135485068),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('addi', 5, 4, 0),
 ('imm', 'cmp', 0, 11),
 ('branch', 9, 135485054),
 ('jump', 135485710),
 ('shift', 'lsl', 0, 0, 2),
 ('literal', 1, 135485072),
 ('add', 0, 0, 1),
 ('mem', True, 'word', 0, 0, 0),
 ('movhi', 15, 0),
])
put('frominfo_prefix_1',0x081356C4,[
 ('literal', 1, 135485160),
 ('mem', True, 'word', 0, 1, 0),
 ('literal', 2, 135485164),
 ('add', 0, 0, 2),
 ('imm', 'mov', 2, 1),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 1, 0),
 ('literal', 3, 135485168),
 ('add', 0, 0, 3),
 ('mem', False, 'byte', 2, 0, 0),
 ('mem', True, 'word', 0, 1, 0),
 ('imm', 'mov', 1, 199),
 ('shift', 'lsl', 1, 1, 6),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135498268),
 ('jump', 135485788),
])
put('frominfo_prefix_2',0x081356F4,[
 ('literal', 0, 135485300),
 ('mem', True, 'word', 1, 0, 0),
 ('imm', 'mov', 2, 199),
 ('shift', 'lsl', 2, 2, 6),
 ('add', 0, 1, 2),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 3),
 ('branch', 0, 135485228),
 ('imm', 'cmp', 0, 2),
 ('branch', 1, 135485202),
 ('literal', 3, 135485304),
 ('add', 0, 1, 3),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135485228),
 ('imm', 'mov', 0, 30),
 ('spmem', False, 0, 0),
 ('imm', 'mov', 0, 20),
 ('spmem', False, 0, 4),
 ('imm', 'mov', 0, 0),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134227028),
 ('imm', 'mov', 0, 0),
 ('call', 134226108),
 ('imm', 'mov', 4, 30),
 ('spmem', False, 4, 0),
 ('imm', 'mov', 5, 2),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 1),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134227028),
 ('imm', 'mov', 6, 15),
 ('spmem', False, 6, 0),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 1),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 2),
 ('call', 134227028),
 ('spmem', False, 4, 0),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 2),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 0),
 ('call', 134227028),
 ('spmem', False, 6, 0),
 ('spmem', False, 5, 4),
 ('imm', 'mov', 0, 2),
 ('imm', 'mov', 1, 0),
 ('imm', 'mov', 2, 0),
 ('imm', 'mov', 3, 2),
 ('call', 134227028),
 ('jump', 135485788),
])
put('frominfo_prefix_3',0x0813577C,[
 ('call', 135486980),
 ('literal', 0, 135485344),
 ('mem', True, 'word', 0, 0, 0),
 ('imm', 'mov', 1, 199),
 ('shift', 'lsl', 1, 1, 6),
 ('add', 0, 0, 1),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135511828),
 ('call', 135488344),
 ('call', 135499008),
 ('call', 135488100),
 ('jump', 135485788),
])
put('frominfo_prefix_4',0x081357A4,[
 ('literal', 0, 135485388),
 ('call', 135492988),
 ('literal', 0, 135485392),
])
put('frominfo_prefix_5',0x0813595C,[
 ('literal', 0, 135485812),
 ('mem', True, 'word', 1, 0, 0),
 ('literal', 0, 135485816),
 ('add', 1, 1, 0),
 ('mem', True, 'byte', 0, 1, 0),
 ('imm', 'add', 0, 1),
 ('mem', False, 'byte', 0, 1, 0),
 ('spadd', 8),
 ('pop', 112, False),
 ('pop', 1, False),
 ('bx', 0),
])
put('alloc_zero_wrapper_0',0x08002BB0,[
 ('push', 0, True),
 ('addi', 1, 0, 0),
 ('literal', 0, 134228928),
 ('mem', True, 'word', 0, 0, 0),
 ('call', 134228712),
 ('pop', 2, False),
 ('bx', 1),
])
put('alloc_zero_0',0x08002AE8,[
 ('push', 48, True),
 ('spadd', -4),
 ('addi', 4, 1, 0),
 ('call', 134228316),
 ('addi', 5, 0, 0),
 ('imm', 'cmp', 5, 0),
 ('branch', 0, 134228764),
 ('imm', 'mov', 0, 3),
 ('alu', 'and', 0, 4),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 134228742),
 ('shift', 'lsr', 0, 4, 2),
 ('imm', 'add', 0, 1),
 ('shift', 'lsl', 4, 0, 2),
 ('imm', 'mov', 0, 0),
 ('spmem', False, 0, 0),
 ('shift', 'lsl', 2, 4, 9),
 ('shift', 'lsr', 2, 2, 11),
 ('imm', 'mov', 0, 160),
 ('shift', 'lsl', 0, 0, 19),
 ('alu', 'orr', 2, 0),
 ('movhi', 0, 13),
 ('addi', 1, 5, 0),
 ('call', 136084104),
 ('addi', 0, 5, 0),
 ('spadd', 4),
 ('pop', 48, False),
 ('pop', 2, False),
 ('bx', 1),
])
NEW_WORDS = {134228928: 50334264, 135411020: 33796112, 135411024: 135411029, 135411080: 33796116, 135411084: 33702372, 135411088: 33701769, 135411092: 135411097, 135482664: 33796276, 135482668: 12980, 135482672: 33796280, 135482720: 33796320, 135482724: 33796321, 135482728: 33796322, 135482732: 12964, 135482736: 12960, 135482740: 33701772, 135482744: 12324, 135482796: 12324, 135482800: 33796276, 135482804: 12732, 135482808: 12724, 135482852: 33796276, 135482856: 12768, 135482896: 12744, 135482900: 12768, 135483120: 12744, 135483124: 12768, 135483128: 33796276, 135483132: 12828, 135483136: 12832, 135483140: 12760, 135483144: 12860, 135483148: 12716, 135483152: 12720, 135483156: 12972, 135483160: 135488509, 135483316: 33796276, 135483320: 12716, 135483324: 12972, 135483376: 50344240, 135483380: 50352204, 135483424: 50344240, 135483428: 50352204, 135483476: 33796276, 135483480: 12828, 135483484: 135483488, 135483488: 135483512, 135483492: 135483540, 135483496: 135483596, 135483500: 135484100, 135483536: 33796276, 135483568: 33782252, 135483572: 33796276, 135483576: 12828, 135483592: 12828, 135483688: 135510997, 135483692: 33796276, 135483696: 135484309, 135483700: 12972, 135483760: 12752, 135483800: 135484309, 135483804: 12972, 135483868: 12752, 135483872: 12828, 135483928: 135484309, 135483932: 135510997, 135483936: 50344240, 135483996: 33796276, 135484000: 12828, 135484060: 12752, 135484064: 12828, 135484092: 33796276, 135484096: 12828, 135484136: 135484309, 135484140: 12828, 135484176: 50352336, 135484180: 12312, 135484184: 135485033, 135484188: 12828, 135484304: 33782252, 135484348: 50352344, 135484352: 135484356, 135484356: 135484396, 135484360: 135484464, 135484364: 135484600, 135484368: 135484636, 135484372: 135484688, 135484376: 135484720, 135484380: 135484748, 135484384: 135484780, 135484388: 135484820, 135484392: 135484900, 135484452: 33796276, 135484456: 12768, 135484460: 12316, 135484592: 33796276, 135484596: 12752, 135484632: 33796276, 135484676: 33796276, 135484680: 12289, 135484684: 12290, 135484740: 33796276, 135484744: 12784, 135484772: 33796276, 135484776: 12752, 135484816: 33796276, 135484880: 33796276, 135484884: 12291, 135484888: 12292, 135484892: 12293, 135484896: 12294, 135484996: 33796276, 135485000: 12312, 135485004: 135500957, 135485008: 12768, 135485012: 12316, 135485064: 33796276, 135485068: 12848, 135485072: 135485076, 135485076: 135485124, 135485080: 135485172, 135485084: 135485308, 135485088: 135485348, 135485160: 33796276, 135485164: 12768, 135485168: 12316, 135485300: 33796276, 135485304: 12752, 135485344: 33796276, 135485388: 138281500, 135485392: 50344240, 135485812: 33796276, 135485816: 12848, 135488540: 33796276, 135488544: 12832, 135488548: 135488552, 135488552: 135488616, 135488556: 135488622, 135488560: 135488628, 135488564: 135488634, 135488568: 135488640, 135488572: 135488646, 135488576: 135488652, 135488580: 135488666, 135488584: 135488672, 135488588: 135488678, 135488592: 135488688, 135488596: 135488760, 135488600: 135488908, 135488604: 135488948, 135488608: 135489096, 135488612: 135489122, 135488724: 33796276, 135488728: 12724, 135488732: 138575160, 135488756: 138574912, 135488784: 33796276, 135488788: 12716, 135488792: 138574604, 135488840: 12724, 135488844: 138573936, 135488848: 12780, 135488852: 138574300, 135488892: 12776, 135488896: 138573000, 135488900: 12780, 135488904: 138573440, 135488944: 33796276, 135489068: 33796276, 135489072: 12289, 135489076: 12290, 135489080: 12294, 135489084: 12291, 135489088: 12292, 135489092: 12293, 135489156: 33796276, 135489160: 12724, 135489248: 33796276, 135489252: 12832, 135492936: 33796276, 135492940: 12724, 135492944: 135502761, 135492976: 154633361, 135492980: 12312, 135492984: 135497357, 138517932: 135410985, 154633532: 33796276, 154633536: 12960, 154633540: 135483433}
NEW_BLOCKS=dict(BLOCKS)
REUSED={scope:(mod,tuple(names)) for scope,(mod,names) in take.REUSED.items()}
REUSED['party']=(party,REUSED['party'][1]+('close_menu_same_task','close_menu_exit_consumer','close_menu_fallback_and_free'))
REUSED['menu']=(menu,REUSED['menu'][1]+('destroy_task_prefix','destroy_task_tail','is_task_active_prefix','is_task_active_tail'))
REUSED['runtime']=(runtime,tuple(runtime.BLOCKS))
for name,rows in take.BLOCKS.items():
 if name.startswith('outer_') or name=='choose_mon_return':BLOCKS['root_'+name]=rows
ALL_WORDS=dict(NEW_WORDS)
for scope,(mod,names) in REUSED.items():
 for name in names:
  rows=mod.BLOCKS[name];BLOCKS[scope+'_'+name]=rows
  for i in rows:
   if i.kind=='literal':ALL_WORDS[i.args[1]]=mod.LITERALS[i.args[1]]
for name,rows in BLOCKS.items():
 if name.startswith('root_'):
  for i in rows:
   if i.kind=='literal':ALL_WORDS[i.args[1]]=take.ALL_WORDS[i.args[1]]
ALL_WORDS.update(setup.TABLE);ALL_WORDS.update({0x0836B380:0x0806EC3D,0x08123320:0x0812334C})
FIELDS={k:v for k,v in take.FIELDS.items() if k.startswith('field_move_id_')}
def encoded(i):
 if i.kind=='swi':return (0xDF00|i.args[0]).to_bytes(2,'little')
 return setup.encoded(i) if i.kind=='multiple' else menu.encoded(i)
INS={}
for rows in BLOCKS.values():
 for i in rows:
  if i.address in INS:need(encoded(INS[i.address])==encoded(i),'consistent shared semantics')
  INS[i.address]=i
WINDOWS={name:(rows[0].address,sum(i.size for i in rows)) for name,rows in BLOCKS.items()}
WINDOWS.update({f'word_{a:08x}':(a,4) for a in sorted(ALL_WORDS)})
WINDOWS.update({k:(a,n) for k,(a,n,v) in FIELDS.items()});WINDOWS['minimal_boundary']=(HIT-1,6)
BIOS_SEMANTICS=tuple(party.block(0x081C7A88,[('swi',11),('bx',14)]))
WINDOWS['actual_CpuSet_BIOS_wrapper']=(0x081C7A88,4)
EXTERNAL_CALLS={i.address:i.args[0] for i in INS.values() if i.kind=='call' and i.args[0] not in INS}
ROOT=dict(kind='existing_startmenu_party_action0_to_installed_summary_input',start_menu_slot=0x0836B380,party_action=0,party_callback_cell=0x08419DAC,party_callback=0x08123529,exit_store=0x0812353C,exit_callback=0x08123555,exit_copy=0x081202D0,constructor=0x08134CE4,setup=0x081363FC,setup_finish=0x0813752C,installed_task=0x09378491,installed_task_literal=0x08137570,installed_interwork=0x09378558,actual_old_input_literal=0x09378544,old_input=0x08135028,normal_scheduler=0x0813868C,frominfo_store=0x08135302,frominfo=0x08135668,hit_call=HIT-1,callee=0x0813757C,static_successor=0x081357AA)
CLAIMS=dict(proof_scope='conditional_rooted_finite_summary_instruction_type',full_story_reachability_claimed=False,runtime_execution_observed=False,universal_allocation_epoch_proven=False,all_opaque_effects_proven=False,irq_noninterference_proven=False,bl_return_observed=False,whole_function_range_classified=False,maximum_target_access_width_proven=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT={
 'root':'actual StartMenuPokemon root; field party action0 selected by actual action builder and cursor0/A; slot0 non-egg, one mon, nonmail held item1, no field moves is a sufficient profile',
 'party':'same actual admitted task, linked active/function at each dispatch; null callback1, fade inactive and finite setup success; old party object epoch only through final exitCallback read/copy',
 'allocation':'two actual AllocZeroed wrappers, requests12980 and40, actual first-fit allocator; well-formed heap with adequate free fits and stack/global nonalias; selected zero-fill BIOS boundary has exact destination, count and word0 source; normal BIOS return and exact requested zero fill are conditional effects',
 'summary':'new object and skills allocation epochs, pointer cells and currently read controls/resources remain live until their last selected use; freeing old party allocation after callback copy is permitted',
 'mon':'BufferSelectedMonData normal return establishes readable currentMon at summary+0x323c; field45 and field4 getters on that copied mon return0; these effects are explicit new boundaries, not reused field11/45 proof on gPlayerParty',
 'setup':'actual states0..15 and default registration; wait helpers at states3,4,6 return success; window creation establishes valid distinct window IDs0..6, graphics/sprite/background resources valid at selected later calls; opaque resource creation/drawing effects remain conditional',
 'installed_hook':'actual09378490 calls helper09378bd4 then predicate09378bb6(summary,0x32a0); predicate returns0 with required fields preserved; literal09378544 and actual BX r3 enter08135028',
 'input':'normal mode0, non-egg/non-bad-egg; finite inactive fade/link gates; actual right key16 advances page0→1→2, then A key1 advances2→3; actual IsPageFlipInput/new-key consumer and FuncIsActiveTask scan; no universal input/environment reachability claim',
 'flip':'each page0→1 and1→2 creates a second actual task, admitted into the same valid list; states0..9 and default execute; DMA wait returns0 and flip-finished returns nonzero; actual DestroyTask removes the temporary task before next key',
 'frominfo':'page3 actual store changes same input task function to08135669; actual FromInfo states0,1,2 increment to3; stop before complete target BL; neither states4..11 nor target normal return is required',
 'callee_frame':'each listed call normal Thumb ABI return preserves r4-r11/SP/saved caller stack and only the phase current live memory projection; r0-r3/r12/flags poisoned unless specified output; resources may change in contracted role; no full heap, task-array, IRQ, or whole-program freeze',
 'external_effects':'all conditional call records have effects_discharged=false; output writes listed separately from preservation; resource validity is assumed at calls, not inferred from a zero-valued ID',
}
def exact(a,b):return take.exact(a,b)
def protected_windows(review):
 rows=review['windows'];need(type(rows)is list and len(rows)==len(WINDOWS),'closed window count')
 need(all(type(r)is dict and set(r)=={'label','address','size','sha256'} for r in rows),'address/size/SHA only')
 need(exact([(r['label'],r['address'],r['size']) for r in rows],[(k,*v) for k,v in WINDOWS.items()]),'fixed ordered window geometry')
 need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef' for c in r['sha256']) for r in rows),'SHA format')
 return [{k:r[k] for k in ('address','size','sha256')} for r in rows]
def bind_semantics(raw):
 for i in [*INS.values(),*BIOS_SEMANTICS]:need(chunk(raw,i.address,i.size)==encoded(i),'semantic instruction '+hex(i.address))
 for a,v in ALL_WORDS.items():need(d.u32(raw,a)==v,'literal/table role '+hex(a))
 for a,n,v in FIELDS.values():need(int.from_bytes(chunk(raw,a,n),'little')==v,'field-move roles')
 need(identity(chunk(raw,HIT-1,6))=={k:BOUNDARY[k] for k in ('size','sha256')},'exact complete BL and static LDR')
def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS) and exact(review['source_bindings'],SOURCE_IDS),'fixed closed source dependencies')
 for key,b in sources.items():
  need(identity(b)=={k:SOURCE_IDS[key][k] for k in ('size','sha256')},'fixed source '+key)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==SOURCE_IDS[key]['git_blob_sha'],'Git blob '+key)
 for token in ('void ShowPokemonSummaryScreen(', 'static void CB2_SetUpPSS(void)', 'Task_FlipPages_FromInfo', 'CreateTask(Task_PokeSum_FlipPages, 0);'):
  need(token in sources['pret-pokemon_summary_screen.c'].decode(),'public structural Summary source')
 need(json.loads(sources['runtime_review'])['inherited_reviews']==runtime.PRIOR_REFS,'exact accepted root review dependencies')

class Machine(take.Machine):
 def read(self,a,n):
  value=super().read(a,n)
  if hasattr(self,'trace') and not 0x08000000<=a<0x0A000000:self.trace.append(('read',a,n))
  return value
 def write(self,a,n,value):
  super().write(a,n,value)
  if hasattr(self,'trace'):self.trace.append(('write',a,n))
 def step(self,branch_choice=None):
  i=self.instructions[self.pc];k,x=i.kind,i.args
  if k=='comparehi':self.cmp(self.reg[x[0]],self.reg[x[1]]);self.pc+=2;self.steps+=1;return
  if k=='regmem':
   op,rd,rb,ro=x;need(op in ('ldr','ldrb','ldrh'),'bounded selected register load');self.reg[rd]=self.read(self.reg[rb]+self.reg[ro],{'ldr':4,'ldrb':1,'ldrh':2}[op]);self.pc+=2;self.steps+=1;return
  return super().step(branch_choice)


def _compose(raw,stop_setup=None,hook_result=0,fields_preserved=True,zero_fill=True,normal_returns=True,boundary_live=None,opaque_writes=None,epoch_events=None):
 need(type(hook_result)is int and hook_result==0,'selected installed predicate returns0')
 need(all(x is True for x in (fields_preserved,zero_fill,normal_returns)),'conditional call contracts mandatory')
 if stop_setup is not None:need(type(stop_setup)is int and 0<=stop_setup<=15,'bounded setup prefix')
 p=runtime.ROOT+runtime.HEADER
 mem,size=runtime.heap_fixture([(0,runtime.LIMIT-16)])
 mem.update(runtime.task_fixture([]))
 for a,n in ((p,568),(PARTY,20),(MAIN,1100),(CURSOR,12)):
  for j in range(n):mem[a+j]=0
 runtime.setmem(mem,0x020379F3,1,0)
 # The actual summary callback reads gPlayerPartyCount from this fixed cell.
 runtime.setmem(mem,ALL_WORDS[0x08123590],1,1)
 # Ordinary non-L/R shortcut options for the actual page-key consumer.
 options=0x0203C000
 runtime.setmem(mem,ALL_WORDS[0x08134FF4],4,options);runtime.setmem(mem,options+19,1,0)
 phase='party_setup';selected=None;summary_pointer=None;flip_id=None
 catalog={};events=[];allocations=[];copied=False;trace=[];boundaries=[]
 def task_chain(memory):
  # The admission/list predicate reads active flags, then only live row controls.
  for j in range(16):trace.append(('read',TASKS+40*j+4,1))
  result=runtime.task_chain(memory)
  for j in result:trace.append(('read',TASKS+40*j,8))
  return result
 def heap_check(memory):
  trace.extend((('read',runtime.ROOT_CELL,4),('read',runtime.SIZE_CELL,4)))
  result=runtime.well_formed(memory,runtime.LIMIT)
  for a,u,n in result:trace.append(('read',a,16))
  return result

 setup_success={0x0811F4D4,0x0811F4FC,0x0811F558,0x0811F578}
 setup_calls={i.address for name in take.REUSED['setup'][1] if name.startswith('setup_') for i in setup.BLOCKS[name] if i.kind=='call'}
 root_external={0x0806EC54,0x0806EC58,0x0806EC5C,0x0811F37E}
 summary_setup_success={0x0813647A,0x08136480,0x0813648C}
 def record(site,target,result,outputs,live_index,produced):
  key=live_index
  row=dict(phase=phase,site=site,target=target,normal_return_assumed=True,effects_discharged=False,
   return_value=result if runtime.concrete(result) else 'unspecified',conditional_outputs=outputs,produced_memory_ranges=produced)
  if key in catalog:
   need(exact({k:v for k,v in catalog[key].items() if k!='count'},row),'stable shared call contract');catalog[key]['count']+=1
  else:catalog[key]=dict(row,count=1)
 def run(entry,memory,stop=None):
  nonlocal selected,summary_pointer,phase,flip_id,copied
  m=Machine(raw,entry,memory=memory,instructions=INS);m.trace=trace
  if entry==0x08000510:need(m.read(MAIN,4)==0,'callback1 null at actual dispatch')
  while m.pc!=0xFFFFFFF0 and m.pc!=stop:
   if m.pc in INS:
    if m.pc==0x0811F5C8:
     selected=m.reg[0];need(selected==0 and selected in task_chain(m.mem),'party selected task admitted')
     events.append(dict(role='party_task_admission',task_id=selected,site=0x0811F5C4))
    if m.pc==0x08123528:need(m.reg[0]==selected,'action0 same selected task');phase='party_exit'
    if m.pc==0x081202D4:
     need(m.read(MAIN+4,4)==0x08123555,'actual copy before free');copied=True;events.append(dict(role='party_exit_callback_copied',site=0x081202D0))
    if m.pc==0x08134CE4:
     phase='summary_constructor';need(tuple(m.reg[:4])==(MONS,0,0,0x08123599) and m.read(m.reg[13],4)==0,'actual normal Summary constructor arguments')
    if m.pc==0x08134D0C:summary_pointer=m.reg[0]
    if m.pc in (0x08134D0C,0x08134D16):
     n=0x32B4 if m.pc==0x08134D0C else 40
     need(type(m.reg[0])is int and m.reg[0]%4==0,'actual aligned AllocZeroed result');allocations.append(dict(pointer=m.reg[0],requested=n,zero_fill_conditional=True))
    if m.pc==0x0813755C:
     selected=m.reg[0];need(selected==0 and selected in task_chain(m.mem),'new Summary input task actual admission')
     events.append(dict(role='installed_summary_task_admission',task_id=selected,callback=0x09378491,site=0x08137558))
    if m.pc==0x09378490:need(m.reg[0]==selected,'installed wrapper same selected task')
    if m.pc==0x08135028:need(m.reg[0]==selected,'old handler receives actual installed wrapper task')
    if m.pc==0x081352DA:
     flip_id=m.reg[0];need(flip_id!=selected and flip_id in task_chain(m.mem),'temporary flip actual free-row admission');events.append(dict(role='temporary_flip_admission',task_id=flip_id,page=m.read(summary_pointer+0x31C0,1)))
    if m.pc==0x08135304:
     need(m.read(TASKS+selected*40,4)==0x08135669,'same selected task frominfo registration');events.append(dict(role='same_input_task_replaced',task_id=selected,site=0x08135302))
    m.step();continue
   site=(m.reg[14]&~1)-4;target=m.pc;result=runtime.U;outputs=[];effect_trace_start=len(trace)
   affected=(epoch_events or {}).get(site,{})
   live_epochs=[]
   if not copied:live_epochs.append(p)
   if summary_pointer is not None:live_epochs.append(summary_pointer)
   if len(allocations)>1:live_epochs.append(allocations[1]['pointer'])
   need(not affected.get('heap_reinitialized',False) and not any(q in affected.get('freed',()) for q in live_epochs),'conditional live allocation epoch cannot be replaced by ABA')
   need(EXTERNAL_CALLS.get(site)==target,'unlisted boundary '+hex(site)+' -> '+hex(target))
   if target in (0x080F6168,0x0813C034):result=0
   elif site in root_external:pass
   elif target==0x080C0918:result=0
   elif target==0x080C08D8:result=1 if phase=='party_setup' and site==0x0811F3F2 else 0
   elif site in setup_calls:result=1 if site in setup_success else runtime.U
   elif target==0x081206EC:need(site==0x0812033E,'selected mon input');result=1
   elif target==0x0803F354:
    field=m.reg[1]
    if site in (0x08134EA4,0x08134EB6):
     need(m.reg[0]==summary_pointer+0x323C and field in (45,4),'new copied-mon getters, not old party ABI');result=0
    elif site==0x08123350:need((m.reg[0],field)==(MONS,45),'selected party non-egg');result=0
    elif site==0x0812322C:need(m.reg[0]==MONS and field in (13,14,15,16),'field moves');result=0
    elif site==0x0812327A:need((m.reg[0],field)==(MONS+100,11),'selected one-mon profile');result=0
    elif site==0x0812329E:need((m.reg[0],field)==(MONS,12),'held item');result=1
    else:raise ValueError('unlisted mon getter')
   elif target==0x08097AE8:result=0
   elif target==0x081224B0:m.write(m.reg[0],1,255);outputs=[dict(address=m.reg[0],size=1,value=255)]
   elif target==0x08122628:
    need(m.reg[0]==0 and m.read(p+23,1)==3,'outer Summary row selection count3')
    outputs=take.selection_initialization(p,0,3,take.SELECTION_OUTPUT_SPEC)
    for f in outputs:m.write(f['address'],f['size'],f['value'])
   elif target==0x0811F878:
    need(copied,'party cleanup only after actual callback copy')
    # Conditional FreePartyPointers effect projection; actual Free machine establishes
    # this one output. Other cleanup callees and resources remain opaque.
    freed=Machine(raw,0x08002BC4,{0:p,13:m.reg[13]},m.mem,instructions=INS);freed.trace=trace
    while freed.pc!=0xFFFFFFF0:freed.step()
    need(freed.reg[13]==m.reg[13],'conditional cleanup Free stack balanced')
    heap_check(freed.mem);m.mem=freed.mem
    outputs=[dict(role='old_party_epoch_ended',pointer=p,heap_well_formed=True)]
   elif target==0x081C7A88:
    requested=(m.reg[2]&0x1FFFF)*4;dest=m.reg[1]
    need(m.reg[2]>>24==5 and m.read(m.reg[0],4)==0 and requested in (12980,40),'actual zero-fill BIOS arguments')
    need(runtime.ROOT+16<=dest and dest+requested<=runtime.ROOT+runtime.LIMIT,'zero-fill bounded and stack nonalias')
    for j in range(requested):m.mem[dest+j]=0
    trace.append(('write',dest,requested))
    outputs=[dict(role='conditional_CpuSet_word_fill',address=dest,size=requested,value=0)]
   elif site in summary_setup_success:result=1
   elif site==0x08136486:
    need(summary_pointer is not None,'window creation after constructor')
    outputs=[dict(address=summary_pointer+0x3000+j,size=1,value=j,role='conditional_valid_window_id') for j in range(7)]
    for f in outputs:m.write(f['address'],f['size'],f['value'])
   elif site==0x093784A0:
    need((m.reg[0],m.reg[1])==(summary_pointer,0x32A0),'actual installed predicate args');result=hook_result
   elif site in (0x081350CC,0x081350DA,0x08134FC2):result=0
   elif site in (0x08135510,0x081355E4):result=0
   elif site==0x08135556:result=1
   live_index=len(boundaries);boundaries.append((phase,site,target))
   produced=[[a,n] for kind,a,n in trace[effect_trace_start:] if kind=='write']
   trace.append(('boundary',live_index,0));record(site,target,result,outputs,live_index,produced)
   if boundary_live is not None:
    need(live_index<len(boundary_live),'replay boundary count')
    live=boundary_live[live_index]
    protected={a+j for a,n in live for j in range(n)}
    for a,n,value in (opaque_writes or {}).get(site,[]):
     need(type(a)is int and type(n)is int and n>0 and a+n<=1<<32,'bounded opaque write')
     need(not any(a+j in protected for j in range(n)),'opaque write intersects actual future-live projection')
     for j in range(n):m.mem[a+j]=(value>>(8*j))&255
    # All existing RAM outside the exact future-read-before-write projection may
    # be clobbered. Replay must still follow the same finite instruction chain.
    for a in m.mem.keys():
     if a not in protected:m.mem[a]=runtime.U

   for r in (0,1,2,3,12):m.reg[r]=runtime.U
   m.reg[0]=result;m.flag_pc=None;m.pc=m.reg[14]&~1
  if stop is None:need(m.reg[13]==0x03007000,'phase stack balanced')
  return m
 def frame(m,keys=0,stop=None):
  runtime.setmem(m.mem,MAIN+46,2,keys);runtime.setmem(m.mem,MAIN+48,2,0)
  trace.extend((('write',MAIN+46,2),('write',MAIN+48,2)))
  return run(0x08000510,m.mem,stop)
 def proof(m,status):
  # Preserve the published frontier controls for independent setup consumers.
  endpoint=[(MAIN,8),(SUMMARY,8),(summary_pointer+0x3220,1),(TASKS+40*selected,8)]
  if stop_setup is not None:
   endpoint += [(SUMMARY,8),(summary_pointer-16,8),(summary_pointer+0x31AC,0x3C),(summary_pointer+0x321C,0x18),(summary_pointer+0x32A0,16),(summary_pointer+0x3000,7),(summary_pointer+0x3024,4),(summary_pointer+0x323C,100)]
  live={a+j for a,n in endpoint for j in range(n)};per_boundary=[None]*len(boundaries)
  def spans(cells):
   out=[]
   for a in sorted(cells):
    if out and out[-1][0]+out[-1][1]==a:out[-1][1]+=1
    else:out.append([a,1])
   return out
  for kind,a,n in reversed(trace):
   if kind=='read':live.update(range(a,a+n))
   elif kind=='write':live.difference_update(range(a,a+n))
   else:per_boundary[a]=spans(live)
  if boundary_live is not None:need(exact(per_boundary,boundary_live),'replay live-read geometry identical')
  combined={};projections=[]
  for index,fields in enumerate(per_boundary):
   row=copy.deepcopy(catalog[index]);row.pop('count')
   output_cells={a+j for a,n in row['produced_memory_ranges'] for j in range(n)}
   preserved=spans({a+j for a,n in fields for j in range(n)}-output_cells)
   if preserved not in projections:projections.append(preserved)
   row['preserve_projection']=projections.index(preserved)
   # Only the actual effects needed by a future read are output obligations.
   row['produced_memory_ranges']=spans(output_cells & {a+j for a,n in fields for j in range(n)})
   key=json.dumps(row,sort_keys=True)
   if key in combined:combined[key]['count']+=1
   else:combined[key]=dict(row,count=1)
  m.boundary_live=per_boundary
  return dict(status=status,selected_task=selected,summary_pointer=summary_pointer,allocations=allocations,events=events,
   conditional_call_catalog=list(combined.values()),live_projection_catalog=projections,
   live_projection_method='exact finite RAM read-before-write including ABI stack, admission/list checks, and explicit endpoint fields; conditional outputs occur before boundary; all non-live RAM poisoned in replay',
   live_projection_replay_checked=boundary_live is not None,
   same_task_membership_checked=True,callee_at_hit_executed=False,actual_runtime_execution_observed=False,synthetic_contract_execution=True,allocation_epochs_conditional=True,
   stopped_at=m.pc,main_callback=m.read(MAIN+4,4),setup_state=m.read(summary_pointer+0x3220,1) if summary_pointer else None)

 m=run(d.u32(raw,ROOT['start_menu_slot'])&~1,mem)
 need(m.read(MAIN+4,4)==0x081277E9,'actual StartMenu constructor callback')
 m=frame(m);need(m.read(MAIN+4,4)==0x0811F3D9,'party constructor callback')
 for stage in range(24):
  need(m.read(MAIN+1080,1)==stage,'party setup state producer');m=frame(m)
 need(m.read(MAIN+4,4)==0x0811F3A9,'actual party scheduler')
 phase='party_menu';m=frame(m)
 need([m.read(p+15+j,1) for j in range(3)]==[0,3,2] and m.read(p+23,1)==3,'actual Summary first action producer')
 need(m.read(CURSOR+2,1)==0 and m.read(TASKS,4)==0x08123439,'actual selector/cursor0')
 m=frame(m,1);need(m.read(TASKS,4)==0x081202A5,'Summary action changes same task to close')
 m=frame(m);need(copied and m.read(MAIN+4,4)==0x08123555 and not task_chain(m.mem),'exit copy before old task removal')
 m=frame(m);need(summary_pointer is not None and m.read(MAIN+4,4)==0x081363FD,'actual Summary constructor setup registration')
 need([(r['requested']) for r in allocations]==[12980,40] and allocations[0]['pointer']!=allocations[1]['pointer'],'two distinct actual allocations')
 need((m.read(summary_pointer+0x31B4,1),m.read(summary_pointer+0x31C0,1),m.read(summary_pointer+0x31AC,1))==(0,0,0),'constructor normal/page0/non-egg')
 phase='summary_setup'
 for stage in range(17):
  need(m.read(summary_pointer+0x3220,1)==stage,'actual Summary setup state producer')
  if stage==stop_setup:
   slot=ALL_WORDS[0x08136428+4*stage];m=frame(m,stop=slot)
   return m,proof(m,'PASS_CONDITIONAL_ROOT_TO_SUMMARY_SETUP_PREFIX')
  m=frame(m)
 need(m.read(MAIN+4,4)==0x0813868D and m.read(TASKS,4)==0x09378491,'actual installed hook and Summary scheduler')
 need(m.read(summary_pointer+0x3018,1)==selected,'actual registered taskId store')
 phase='summary_input'
 for state in (0,1):
  need(m.read(summary_pointer+0x321C,1)==state,'input state producer from zeroed constructor');m=frame(m)
 need(m.read(summary_pointer+0x321C,1)==2,'actual normal input state')
 for page in (1,2):
  phase='summary_input';need(task_chain(m.mem)==[selected],'same input task only before Right')
  m=frame(m,16);need(m.read(summary_pointer+0x31C0,1)==page and m.read(summary_pointer+0x321C,1)==3,'actual Right increments page and state3')
  phase='page_flip';m=frame(m)
  need(flip_id is not None,'temporary flip admitted')
  for _ in range(11):
   if flip_id not in task_chain(m.mem):break
   m=frame(m)
  need(task_chain(m.mem)==[selected],'actual temporary task destroyed before next input')
  need(m.read(TASKS,4)==0x09378491,'installed input task retained')
  events.append(dict(role='temporary_flip_completed',page=page,task_id=flip_id));flip_id=None
 phase='summary_input';m=frame(m,1)
 need(m.read(summary_pointer+0x31C0,1)==3 and m.read(summary_pointer+0x321C,1)==3,'actual A page2→3 state3')
 m=frame(m);need(m.read(TASKS,4)==0x08135669,'same input task now FromInfo')
 phase='frominfo'
 for state in range(3):
  need(m.read(summary_pointer+0x3230,1)==state,'FromInfo state0/1/2 producer '+str((state,m.read(summary_pointer+0x3230,1))));m=frame(m)
 need(m.read(summary_pointer+0x3230,1)==3,'actual FromInfo increment to3')
 m=frame(m,stop=HIT-1);need(m.pc==HIT-1,'rooted complete BL boundary')
 result=proof(m,'PASS_CONDITIONAL_ROOTED_SUMMARY_MINIMUM_THUMB');result.update(reached_instruction=HIT-1,static_successor=HIT+3,frominfo_preceding_states=[0,1,2])
 return m,result

def _checked_compose(raw,**kwargs):
 first,proof=_compose(raw,**kwargs)
 second,replay=_compose(raw,boundary_live=first.boundary_live,**kwargs)
 need(exact(proof['events'],replay['events']),'same producers and task phases under non-live clobber')
 return second,replay
def root_at_setup(raw,state=8):
 bind_semantics(raw);return _checked_compose(raw,stop_setup=state)
def compose_selected(raw,**kwargs):
 return _checked_compose(raw,**kwargs)[1]
def evidence_template():
 return dict(schema_version=1,root_verified=True,root=copy.deepcopy(ROOT),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),instruction_window=dict(BOUNDARY),instructions=[dict(address=HIT-1,size=4,role='complete_thumb_bl',callee=0x0813757C),dict(address=HIT+3,size=2,role='static_thumb_ldr_return_successor',literal=0x081357D0)],same_selected_task=True,literal_pool_included=False,type_classification_only=True)
def witness_geometry(e):
 need(exact(e,evidence_template()),'exact rooted conditional minimum geometry');need(BOUNDARY['address']<=HIT and HIT+4<=BOUNDARY['address']+6,'hit covered by two complete instructions');return HIT-1,6
def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hit','root','windows','claims','input_contract'},'closed review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'integer schema')
 need(exact(review['required_candidate'],CANDIDATE) and exact(inherited['candidate'],CANDIDATE),'current candidate required')
 need(exact(review['diagnostic_input'],DIAGNOSTIC),'diagnostic identity distinct')
 need(exact(review['root'],ROOT) and exact(review['claims'],CLAIMS) and exact(review['input_contract'],CONTRACT),'exact bounded contract')
 rows=[h for h in inherited['hits'] if h['address']==HIT]
 need(len(rows)==1 and exact(rows[0],review['hit']) and rows[0]['accepted'] is False and rows[0]['owner_candidates']==[],'one unchanged owner-external unknown')
 need(type(rows[0]['size'])is int and rows[0]['size']==4 and rows[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','four-byte unknown hit')
 d.signed(raw,rows[0]);sources_bind(review,sources);d.signed(raw,protected_windows(review));bind_semantics(raw)
 composition=compose_selected(raw);e=evidence_template();a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_ONE_CONDITIONAL_SUMMARY_MINIMUM_TYPE',count=1,hit=HIT,protected_windows=len(WINDOWS),protected_bytes=sum(n for a,n in WINDOWS.values()),composition=composition,source_bindings=SOURCE_IDS,**CLAIMS)
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current required; diagnostic cannot classify current');return _regions(raw,inherited,review,sources)
def make_review(raw,hit):
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hit=copy.deepcopy(hit),root=copy.deepcopy(ROOT),windows=[dict(label=k,address=a,**identity(chunk(raw,a,n))) for k,(a,n) in WINDOWS.items()],claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT))
