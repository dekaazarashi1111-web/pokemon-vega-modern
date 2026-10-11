"""Fishing実登録・timeout局所診断。外側state7 producer未結合なので未知を維持する。"""
import copy,hashlib,json,re
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_extra_roots as common
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
HITS=HELD_HITS=INVESTIGATED_HITS=(0x0805D12F,)
CLASSIFIED_HITS=()
KIND='unresolved_fishing_timeout_root'
TYPE_CATEGORY='guard'
TASKS,MAIN,AVATAR,SPRITES=0x030050D0,0x03003130,0x02036FAC,0x020205B8
SOURCE_IDS = {'pret-field_player_avatar.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                'git_blob_sha': 'ef086dda3a6bf2d175861d6a7be1831790208ecb',
                                'local': 'pret-field_player_avatar.c',
                                'path': 'src/field_player_avatar.c',
                                'repository': 'pret/pokefirered',
                                'sha256': 'd36588c4d02385393a5e8dc74d78f907944ca556700b5c67b39f8304f4dde08e',
                                'size': 67969},
 'pret-task.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': '01503dc7ae78cf2348524bfb5bbb89183640f944',
                 'local': 'pret-task.c',
                 'path': 'src/task.c',
                 'repository': 'pret/pokefirered',
                 'sha256': '8bdd5205ec396be7b66d6e384a82309b3cab59783d46fb8c4c991b2172d4868b',
                 'size': 5029}}
SPECS = [(134597500, 'push', (48, True)),
 (134597502, 'addi', (4, 0, 0)),
 (134597504, 'shift', ('lsl', 4, 4, 24)),
 (134597506, 'shift', ('lsr', 4, 4, 24)),
 (134597508, 'literal', (5, 134597560)),
 (134597510, 'addi', (0, 5, 0)),
 (134597512, 'imm', ('mov', 1, 255)),
 (134597514, 'call', (134704052,)),
 (134597518, 'shift', ('lsl', 0, 0, 24)),
 (134597520, 'shift', ('lsr', 0, 0, 24)),
 (134597522, 'literal', (2, 134597564)),
 (134597524, 'shift', ('lsl', 1, 0, 2)),
 (134597526, 'add', (1, 1, 0)),
 (134597528, 'shift', ('lsl', 1, 1, 3)),
 (134597530, 'add', (1, 1, 2)),
 (134597532, 'mem', (False, 'half', 4, 1, 38)),
 (134597534, 'call', (136084188,)),
 (134597538, 'imm', ('mov', 0, 2)),
 (134597540, 'call', (135607608,)),
 (134597544, 'imm', ('cmp', 0, 1)),
 (134597546, 'branch', (1, 134597552)),
 (134597548, 'call', (135346148,)),
 (134597552, 'pop', (48, False)),
 (134597554, 'pop', (1, False)),
 (134597556, 'bx', (0,)),
 (134597568, 'push', (48, True)),
 (134597570, 'shift', ('lsl', 0, 0, 24)),
 (134597572, 'shift', ('lsr', 0, 0, 24)),
 (134597574, 'literal', (5, 134597616)),
 (134597576, 'literal', (2, 134597620)),
 (134597578, 'shift', ('lsl', 1, 0, 2)),
 (134597580, 'add', (1, 1, 0)),
 (134597582, 'shift', ('lsl', 1, 1, 3)),
 (134597584, 'add', (4, 1, 2)),
 (134597586, 'imm', ('mov', 1, 8)),
 (134597588, 'signed_load', ('half', 0, 4, 1)),
 (134597590, 'shift', ('lsl', 0, 0, 2)),
 (134597592, 'add', (0, 0, 5)),
 (134597594, 'mem', (True, 'word', 1, 0, 0)),
 (134597596, 'addi', (0, 4, 0)),
 (134597598, 'call', (136084172,)),
 (134597602, 'shift', ('lsl', 0, 0, 24)),
 (134597604, 'imm', ('cmp', 0, 0)),
 (134597606, 'branch', (1, 134597586)),
 (134597608, 'pop', (48, False)),
 (134597610, 'pop', (1, False)),
 (134597612, 'bx', (0,)),
 (134597624, 'push', (16, True)),
 (134597626, 'addi', (4, 0, 0)),
 (134597628, 'call', (134648320,)),
 (134597632, 'literal', (1, 134597652)),
 (134597634, 'imm', ('mov', 0, 1)),
 (134597636, 'mem', (False, 'byte', 0, 1, 6)),
 (134597638, 'mem', (True, 'half', 0, 4, 8)),
 (134597640, 'imm', ('add', 0, 1)),
 (134597642, 'mem', (False, 'half', 0, 4, 8)),
 (134597644, 'imm', ('mov', 0, 0)),
 (134597646, 'pop', (16, False)),
 (134597648, 'pop', (2, False)),
 (134597650, 'bx', (1,)),
 (134598196, 'mem', (True, 'half', 1, 0, 8)),
 (134598198, 'imm', ('add', 1, 3)),
 (134598200, 'mem', (False, 'half', 1, 0, 8)),
 (134598202, 'imm', ('mov', 0, 0)),
 (134598204, 'bx', (14,)),
 (134598208, 'push', (16, True)),
 (134598210, 'spadd', (-8,)),
 (134598212, 'addi', (4, 0, 0)),
 (134598214, 'literal', (1, 134598272)),
 (134598216, 'movhi', (0, 13)),
 (134598218, 'imm', ('mov', 2, 6)),
 (134598220, 'call', (136093080,)),
 (134598224, 'literal', (0, 134598276)),
 (134598226, 'mem', (True, 'byte', 1, 0, 4)),
 (134598228, 'shift', ('lsl', 0, 1, 4)),
 (134598230, 'add', (0, 0, 1)),
 (134598232, 'shift', ('lsl', 0, 0, 2)),
 (134598234, 'literal', (1, 134598280)),
 (134598236, 'add', (0, 0, 1)),
 (134598238, 'call', (134599300,)),
 (134598242, 'mem', (True, 'half', 1, 4, 10)),
 (134598244, 'imm', ('add', 1, 1)),
 (134598246, 'mem', (False, 'half', 1, 4, 10)),
 (134598248, 'imm', ('mov', 2, 38)),
 (134598250, 'signed_load', ('half', 0, 4, 2)),
 (134598252, 'shift', ('lsl', 0, 0, 1)),
 (134598254, 'addhi', (0, 13)),
 (134598256, 'shift', ('lsl', 1, 1, 16)),
 (134598258, 'shift', ('asr', 1, 1, 16)),
 (134598260, 'imm', ('mov', 2, 0)),
 (134598262, 'signed_load', ('half', 0, 0, 2)),
 (134598264, 'compare', (1, 0)),
 (134598266, 'branch', (11, 134598284)),
 (134598268, 'imm', ('mov', 0, 12)),
 (134598270, 'jump', (134598300,)),
 (134598284, 'literal', (0, 134598312)),
 (134598286, 'mem', (True, 'half', 1, 0, 46)),
 (134598288, 'imm', ('mov', 0, 1)),
 (134598290, 'alu', ('and', 0, 1)),
 (134598292, 'imm', ('cmp', 0, 0)),
 (134598294, 'branch', (0, 134598302)),
 (134598296, 'mem', (True, 'half', 0, 4, 8)),
 (134598298, 'imm', ('add', 0, 1)),
 (134598300, 'mem', (False, 'half', 0, 4, 8)),
 (134598302, 'imm', ('mov', 0, 0)),
 (134598304, 'spadd', (8,)),
 (134598306, 'pop', (16, False)),
 (134598308, 'pop', (2, False)),
 (134598310, 'bx', (1,)),
 (134598904, 'push', (112, True)),
 (134598906, 'spadd', (-16,)),
 (134598908, 'addi', (6, 0, 0)),
 (134598910, 'literal', (4, 134599008)),
 (134598912, 'mem', (True, 'byte', 1, 4, 4)),
 (134598914, 'shift', ('lsl', 0, 1, 4)),
 (134598916, 'add', (0, 0, 1)),
 (134598918, 'shift', ('lsl', 0, 0, 2)),
 (134598920, 'literal', (5, 134599012)),
 (134598922, 'add', (0, 0, 5)),
 (134598924, 'call', (134599300,)),
 (134598928, 'mem', (True, 'byte', 0, 4, 4)),
 (134598930, 'shift', ('lsl', 4, 0, 4)),
 (134598932, 'add', (4, 4, 0)),
 (134598934, 'shift', ('lsl', 4, 4, 2)),
 (134598936, 'add', (4, 4, 5)),
 (134598938, 'call', (134594432,)),
 (134598942, 'shift', ('lsl', 0, 0, 24)),
 (134598944, 'shift', ('lsr', 0, 0, 24)),
 (134598946, 'call', (134622656,)),
 (134598950, 'addi', (1, 0, 0)),
 (134598952, 'shift', ('lsl', 1, 1, 24)),
 (134598954, 'shift', ('lsr', 1, 1, 24)),
 (134598956, 'addi', (0, 4, 0)),
 (134598958, 'call', (134250248,)),
 (134598962, 'literal', (2, 134599016)),
 (134704052, 'push', (240, True)),
 (134704054, 'addi', (2, 0, 0)),
 (134704056, 'shift', ('lsl', 1, 1, 24)),
 (134704058, 'shift', ('lsr', 1, 1, 24)),
 (134704060, 'imm', ('mov', 6, 0)),
 (134704062, 'literal', (7, 134704112)),
 (134704064, 'shift', ('lsl', 0, 6, 2)),
 (134704066, 'add', (0, 0, 6)),
 (134704068, 'shift', ('lsl', 5, 0, 3)),
 (134704070, 'add', (4, 5, 7)),
 (134704072, 'mem', (True, 'byte', 0, 4, 4)),
 (134704074, 'imm', ('cmp', 0, 0)),
 (134704076, 'branch', (1, 134704116)),
 (134704078, 'mem', (False, 'word', 2, 4, 0)),
 (134704080, 'mem', (False, 'byte', 1, 4, 7)),
 (134704082, 'addi', (0, 6, 0)),
 (134704084, 'call', (134704136,)),
 (134704088, 'addi', (0, 7, 0)),
 (134704090, 'imm', ('add', 0, 8)),
 (134704092, 'add', (0, 5, 0)),
 (134704094, 'imm', ('mov', 1, 0)),
 (134704096, 'imm', ('mov', 2, 32)),
 (134704098, 'call', (136093176,)),
 (134704102, 'imm', ('mov', 0, 1)),
 (134704104, 'mem', (False, 'byte', 0, 4, 4)),
 (134704106, 'addi', (0, 6, 0)),
 (134704108, 'jump', (134704128,)),
 (134704116, 'addi', (0, 6, 1)),
 (134704118, 'shift', ('lsl', 0, 0, 24)),
 (134704120, 'shift', ('lsr', 6, 0, 24)),
 (134704122, 'imm', ('cmp', 6, 15)),
 (134704124, 'branch', (9, 134704064)),
 (134704126, 'imm', ('mov', 0, 0)),
 (134704128, 'pop', (240, False)),
 (134704130, 'pop', (2, False)),
 (134704132, 'bx', (1,)),
 (134704136, 'push', (240, True)),
 (134704138, 'movhi', (7, 8)),
 (134704140, 'push', (128, False)),
 (134704142, 'shift', ('lsl', 0, 0, 24)),
 (134704144, 'shift', ('lsr', 4, 0, 24)),
 (134704146, 'call', (134704448,)),
 (134704150, 'shift', ('lsl', 0, 0, 24)),
 (134704152, 'shift', ('lsr', 1, 0, 24)),
 (134704154, 'imm', ('cmp', 1, 16)),
 (134704156, 'branch', (1, 134704184)),
 (134704158, 'literal', (1, 134704180)),
 (134704160, 'shift', ('lsl', 0, 4, 2)),
 (134704162, 'add', (0, 0, 4)),
 (134704164, 'shift', ('lsl', 0, 0, 3)),
 (134704166, 'add', (0, 0, 1)),
 (134704168, 'imm', ('mov', 1, 254)),
 (134704170, 'mem', (False, 'byte', 1, 0, 5)),
 (134704172, 'imm', ('mov', 1, 255)),
 (134704174, 'mem', (False, 'byte', 1, 0, 6)),
 (134704176, 'jump', (134704276,)),
 (134704184, 'literal', (6, 134704244)),
 (134704186, 'shift', ('lsl', 0, 4, 2)),
 (134704188, 'movhi', (12, 0)),
 (134704190, 'movhi', (8, 6)),
 (134704192, 'add', (0, 0, 4)),
 (134704194, 'shift', ('lsl', 0, 0, 3)),
 (134704196, 'add', (2, 0, 6)),
 (134704198, 'shift', ('lsl', 0, 1, 2)),
 (134704200, 'add', (0, 0, 1)),
 (134704202, 'shift', ('lsl', 5, 0, 3)),
 (134704204, 'movhi', (7, 8)),
 (134704206, 'add', (3, 5, 7)),
 (134704208, 'mem', (True, 'byte', 0, 2, 7)),
 (134704210, 'mem', (True, 'byte', 7, 3, 7)),
 (134704212, 'compare', (0, 7)),
 (134704214, 'branch', (2, 134704248)),
 (134704216, 'mem', (True, 'byte', 0, 3, 5)),
 (134704218, 'mem', (False, 'byte', 0, 2, 5)),
 (134704220, 'mem', (False, 'byte', 1, 2, 6)),
 (134704222, 'mem', (True, 'byte', 0, 3, 5)),
 (134704224, 'imm', ('cmp', 0, 254)),
 (134704226, 'branch', (0, 134704240)),
 (134704228, 'addi', (1, 0, 0)),
 (134704230, 'shift', ('lsl', 0, 1, 2)),
 (134704232, 'add', (0, 0, 1)),
 (134704234, 'shift', ('lsl', 0, 0, 3)),
 (134704236, 'addhi', (0, 8)),
 (134704238, 'mem', (False, 'byte', 4, 0, 6)),
 (134704240, 'mem', (False, 'byte', 4, 3, 5)),
 (134704242, 'jump', (134704276,)),
 (134704248, 'mem', (True, 'byte', 0, 3, 6)),
 (134704250, 'imm', ('cmp', 0, 255)),
 (134704252, 'branch', (0, 134704258)),
 (134704254, 'addi', (1, 0, 0)),
 (134704256, 'jump', (134704198,)),
 (134704258, 'movhi', (2, 12)),
 (134704260, 'add', (0, 2, 4)),
 (134704262, 'shift', ('lsl', 0, 0, 3)),
 (134704264, 'add', (0, 0, 6)),
 (134704266, 'mem', (False, 'byte', 1, 0, 5)),
 (134704268, 'add', (2, 5, 6)),
 (134704270, 'mem', (True, 'byte', 1, 2, 6)),
 (134704272, 'mem', (False, 'byte', 1, 0, 6)),
 (134704274, 'mem', (False, 'byte', 4, 2, 6)),
 (134704276, 'pop', (8, False)),
 (134704278, 'movhi', (8, 3)),
 (134704280, 'pop', (240, False)),
 (134704282, 'pop', (1, False)),
 (134704284, 'bx', (0,)),
 (134704400, 'push', (48, True)),
 (134704402, 'call', (134704448,)),
 (134704406, 'shift', ('lsl', 0, 0, 24)),
 (134704408, 'shift', ('lsr', 0, 0, 24)),
 (134704410, 'imm', ('cmp', 0, 16)),
 (134704412, 'branch', (0, 134704436)),
 (134704414, 'literal', (5, 134704444)),
 (134704416, 'shift', ('lsl', 4, 0, 2)),
 (134704418, 'add', (4, 4, 0)),
 (134704420, 'shift', ('lsl', 4, 4, 3)),
 (134704422, 'add', (4, 4, 5)),
 (134704424, 'mem', (True, 'word', 1, 4, 0)),
 (134704426, 'call', (136084172,)),
 (134704430, 'mem', (True, 'byte', 0, 4, 6)),
 (134704432, 'imm', ('cmp', 0, 255)),
 (134704434, 'branch', (1, 134704416)),
 (134704436, 'pop', (48, False)),
 (134704438, 'pop', (1, False)),
 (134704440, 'bx', (0,)),
 (134704448, 'push', (0, True)),
 (134704450, 'imm', ('mov', 2, 0)),
 (134704452, 'literal', (0, 134704504)),
 (134704454, 'mem', (True, 'byte', 1, 0, 4)),
 (134704456, 'addi', (3, 0, 0)),
 (134704458, 'imm', ('cmp', 1, 1)),
 (134704460, 'branch', (1, 134704468)),
 (134704462, 'mem', (True, 'byte', 0, 3, 5)),
 (134704464, 'imm', ('cmp', 0, 254)),
 (134704466, 'branch', (0, 134704498)),
 (134704468, 'addi', (0, 2, 1)),
 (134704470, 'shift', ('lsl', 0, 0, 24)),
 (134704472, 'shift', ('lsr', 2, 0, 24)),
 (134704474, 'imm', ('cmp', 2, 15)),
 (134704476, 'branch', (8, 134704498)),
 (134704478, 'shift', ('lsl', 0, 2, 2)),
 (134704480, 'add', (0, 0, 2)),
 (134704482, 'shift', ('lsl', 0, 0, 3)),
 (134704484, 'add', (1, 0, 3)),
 (134704486, 'mem', (True, 'byte', 0, 1, 4)),
 (134704488, 'imm', ('cmp', 0, 1)),
 (134704490, 'branch', (1, 134704468)),
 (134704492, 'mem', (True, 'byte', 0, 1, 5)),
 (134704494, 'imm', ('cmp', 0, 254)),
 (134704496, 'branch', (1, 134704468)),
 (134704498, 'addi', (0, 2, 0)),
 (134704500, 'pop', (2, False)),
 (134704502, 'bx', (1,)),
 (136084172, 'bx', (1,)),
 (136084188, 'bx', (5,)),
 (136093080, 'push', (48, True)),
 (136093082, 'addi', (5, 0, 0)),
 (136093084, 'addi', (4, 5, 0)),
 (136093086, 'addi', (3, 1, 0)),
 (136093088, 'imm', ('cmp', 2, 15)),
 (136093090, 'branch', (9, 136093144)),
 (136093144, 'imm', ('sub', 2, 1)),
 (136093146, 'imm', ('mov', 0, 1)),
 (136093148, 'alu', ('neg', 0, 0)),
 (136093150, 'compare', (2, 0)),
 (136093152, 'branch', (0, 136093170)),
 (136093154, 'addi', (1, 0, 0)),
 (136093156, 'mem', (True, 'byte', 0, 3, 0)),
 (136093158, 'mem', (False, 'byte', 0, 4, 0)),
 (136093160, 'imm', ('add', 3, 1)),
 (136093162, 'imm', ('add', 4, 1)),
 (136093164, 'imm', ('sub', 2, 1)),
 (136093166, 'compare', (2, 1)),
 (136093168, 'branch', (1, 136093156)),
 (136093170, 'addi', (0, 5, 0)),
 (136093172, 'pop', (48, True)),
 (136093176, 'push', (48, True)),
 (136093178, 'addi', (5, 0, 0)),
 (136093180, 'addi', (4, 1, 0)),
 (136093182, 'addi', (3, 5, 0)),
 (136093184, 'imm', ('cmp', 2, 3)),
 (136093186, 'branch', (9, 136093246)),
 (136093188, 'imm', ('mov', 0, 3)),
 (136093190, 'alu', ('and', 0, 5)),
 (136093192, 'imm', ('cmp', 0, 0)),
 (136093194, 'branch', (1, 136093246)),
 (136093196, 'addi', (1, 5, 0)),
 (136093198, 'imm', ('mov', 0, 255)),
 (136093200, 'alu', ('and', 4, 0)),
 (136093202, 'shift', ('lsl', 3, 4, 8)),
 (136093204, 'alu', ('orr', 3, 4)),
 (136093206, 'shift', ('lsl', 0, 3, 16)),
 (136093208, 'alu', ('orr', 3, 0)),
 (136093210, 'imm', ('cmp', 2, 15)),
 (136093212, 'branch', (9, 136093234)),
 (136093214, 'multiple', (False, 1, 8)),
 (136093216, 'multiple', (False, 1, 8)),
 (136093218, 'multiple', (False, 1, 8)),
 (136093220, 'multiple', (False, 1, 8)),
 (136093222, 'imm', ('sub', 2, 16)),
 (136093224, 'imm', ('cmp', 2, 15)),
 (136093226, 'branch', (8, 136093214)),
 (136093228, 'jump', (136093234,)),
 (136093230, 'multiple', (False, 1, 8)),
 (136093232, 'imm', ('sub', 2, 4)),
 (136093234, 'imm', ('cmp', 2, 3)),
 (136093236, 'branch', (8, 136093230)),
 (136093238, 'addi', (3, 1, 0)),
 (136093240, 'jump', (136093246,)),
 (136093242, 'mem', (False, 'byte', 4, 3, 0)),
 (136093244, 'imm', ('add', 3, 1)),
 (136093246, 'addi', (0, 2, 0)),
 (136093248, 'imm', ('sub', 2, 1)),
 (136093250, 'imm', ('cmp', 0, 0)),
 (136093252, 'branch', (1, 136093242)),
 (136093254, 'addi', (0, 5, 0)),
 (136093256, 'pop', (48, True))]
WORDS = {134597560: 134597569,
 134597564: 50352336,
 134597616: 137492820,
 134597620: 50352336,
 134597652: 33779628,
 134598272: 137492898,
 134598276: 33779628,
 134598280: 33686968,
 134598312: 50344240,
 134599008: 33779628,
 134599012: 33686968,
 134599016: 138289936,
 134704112: 50352336,
 134704180: 50352336,
 134704244: 50352336,
 134704444: 50352336,
 134704504: 50352336,
 137492820: 134597625,
 137492824: 134597657,
 137492828: 134597809,
 137492832: 134597869,
 137492836: 134597945,
 137492840: 134598089,
 137492844: 134598197,
 137492848: 134598209,
 137492852: 134598317,
 137492856: 134598445,
 137492860: 134598537,
 137492864: 134598785,
 137492868: 134598905,
 137492872: 134599021,
 137492876: 134599065,
 137492880: 134599233}
TIMEOUTS = {'address': 137492898, 'size': 6, 'values': [36, 33, 30]}
INS={a:next(iter(party.block(a,[(kind,*args)])))for a,kind,args in SPECS}

exact,canonical,spans=common.exact,common.canonical,common.spans
FIXED_GEOMETRY=spans({a for i in INS.values()for a in range(i.address,i.address+i.size)}|{a+j for a in WORDS for j in range(4)}|set(range(TIMEOUTS['address'],TIMEOUTS['address']+6)))
ROOT=dict(constructor=0x0805CB7C,create_task_call=0x0805CB8A,registered_task=0x0805CBC1,rod_writer=0x0805CB9C,initial_interwork=0x0805CB9E,task_dispatch=0x08076D10,state_dispatch=0x0805CBC0,state_table=0x0831F954,initial_state_entry=0x0805CBF8,initial_state_writer=0x0805CC0A,bypass_entry=0x0805CE34,bypass_add=0x0805CE36,bypass_store=0x0805CE38,timeout_entry=0x0805CE40,timeout_increment=0x0805CE64,timeout_store=0x0805CE9C,timeout_value=12,consumer=0x0805D0F8,stop=0x0805D12E,local_instruction_geometry=[0x0805D12E,6])
CLAIMS=dict(proof_scope='diagnostic_actual_registration_and_unconnected_timeout_consumer',root_context_is_precondition=True,root_to_timeout_composed=False,full_story_reachability_claimed=False,unreachable_in_all_gameplay_proven=False,actual_runtime_execution_observed=False,universal_heap_or_irq_lifetime_proven=False,opaque_callee_effects_proven=False,hit_callee_executed=False,type_classification_only=False,classifications_added=0,donor_eligible=False,donor_leased=False)
CONTRACT={
 'root':'StartFishing API呼出、rod0/1/2、有効な空task listを前提とする。非active callback/dataを汚染し、実CreateTask/memsetだけがcallback/active/state0を作る。実初回dispatchがFishing1でstate1を書き、constructorはstack正常復帰する。QuestLog判定falseは条件である。',
 'bypass':'Fishing7入口のstep6は孤立した局所診断入力である。実add3/storeでstep9になり復帰する。StartFishing根からstep6まで全経路を実行した証明ではない。',
 'timeout':'別に確認した登録を保った局所suffix診断へstate7/frameCounter0、spriteId0、newKeys0を注入する。実RunTasks/状態dispatch、実byte-copyによるtimeout表のstackコピー、実加算/比較/storeで36/33/30frame後にstate12になる。次のscheduler frameでhit call直前へ至る。注入値は外側producerではなく、分類根拠に使えない。',
 'boundaries':'opaque呼出の正常復帰、ABI callee-saved registerと将来read-before-writeの具体的RAMだけの保存を条件とし、再実行では他RAMを全消去する。live時の同task世代および局所suffix中のavatar/sprite resource identityは条件である。普遍非同期効果は未証明。',
 'held':'固定sourceと実ROMのFishing7はstep+=3で、想定されたstep7を迂回する。state7を作る正当な外側writer、またはstate12へ至る別の独立根は未結合。全game不達、code型、退役、donor、paddingを主張しない。'}

def encoded(i):return common.encoded(i)
def bind_semantics(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'fishing semantic '+hex(i.address))
 for a,v in WORDS.items():need(d.u32(raw,a)==v,'fishing literal/table '+hex(a))
 for j,v in enumerate(TIMEOUTS['values']):need(int.from_bytes(chunk(raw,TIMEOUTS['address']+j*2,2),'little')==v,'actual rod timeout value')

def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'closed fishing public sources')
 for key,b in sources.items():
  row=SOURCE_IDS[key];need(identity(b)=={k:row[k]for k in('size','sha256')},'whole fishing source identity')
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'whole fishing source Git blob')
 source=sources['pret-field_player_avatar.c'].decode()
 names=re.findall(r'\b(Fishing\d+)\s*,',source.split('static bool8 (*const sFishingStateFuncs[])(struct Task *) =',1)[1].split('};',1)[0])
 need(names==['Fishing'+str(n)for n in range(1,17)],'source ordered sixteen-state table')
 for token in ['u8 taskId = CreateTask(Task_Fishing, 0xFF);','gTasks[taskId].tFishingRod = rod;','Task_Fishing(taskId);','while (sFishingStateFuncs[gTasks[taskId].tStep](&gTasks[taskId]))','#define tStep              data[0]','#define tFrameCounter      data[1]','#define tFishingRod        data[15]','const s16 reelTimeouts[3] = {36, 33, 30};','if (task->tFrameCounter >= reelTimeouts[task->tFishingRod])','task->tStep = FISHING_GOT_AWAY;','#define FISHING_GOT_AWAY 12']:
  need(token in source,'public fishing semantic role '+token)
 bypass=source.split('static bool8 Fishing7(struct Task *task)\n{',1)[1].split('\n}',1)[0]
 need(bypass.strip()=='task->tStep += 3;\n    return FALSE;','source actual bypass, not expected increment1')
 for token in ['gTasks[taskId].func = func;','memset(gTasks[i].data, 0, sizeof(gTasks[i].data));','gTasks[taskId].func(taskId);']:need(token in sources['pret-task.c'].decode(),'public task producer role')
 return True

class Machine(common.Machine):pass

def preservation_contract(fields,writes,events=None,resources=()):
 if events is not None:
  need(type(events)is dict and set(events)=={'task_epoch_changed','avatar_sprite_epoch_changed'}and all(type(x)is bool for x in events.values()),'closed fishing epoch events')
  need(not(events['task_epoch_changed']and any(not rt.disjoint(a,n,TASKS,640)for a,n in fields)),'live fishing task epoch changed')
  need(not(events['avatar_sprite_epoch_changed']and 'avatar_sprite'in resources),'selected fishing avatar/sprite identity required')
 return common.preservation_contract(fields,writes)

def _case(raw,rod,projections=None,opaque_writes=None,epoch_events=None,normal_returns=True,resources_valid=True):
 need(type(rod)is int and rod in(0,1,2),'closed rod domain');need(normal_returns is True and resources_valid is True,'conditional normal returns and sprite resource')
 trace=[];boundaries=[];visited=set();events=[];phase='constructor'
 def boundary(m,site,target,result=rt.U):
  index=len(boundaries);trace.append(('boundary',index))
  if projections is not None:
   fields=projections[index];writes=(opaque_writes or{}).get(site,[]);epochs=(epoch_events or{}).get(site)
   preservation_contract(fields,writes,epochs,('avatar_sprite',)if phase=='injected_timeout'else())
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(j*8))&255
   live={a+j for a,n in fields for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in live}
  boundaries.append(dict(site=site,target=target,phase=phase,normal_abi_return_required=True,effects_discharged=False,return_value=result if rt.concrete(result)else 'unspecified',required_resource_epochs=['avatar_sprite']if phase=='injected_timeout'else []))
 def go(entry,memory,regs=None,stop=None):
  m=Machine(raw,entry,regs,memory,instructions=INS,trace=trace,visited=visited)
  while m.pc!=0xFFFFFFF0 and m.pc!=stop:
   if m.pc in INS:
    if m.pc in(0x08076BCE,0x0805CB9C,0x0805CC0A,0x0805CE38,0x0805CE66,0x0805CE9C):events.append([m.pc,phase])
    m.step();continue
   site=m.reg[14]-5;target=m.pc
   need(site in INS and INS[site].kind=='call'and INS[site].args[0]==target,'unlisted fishing external call')
   need(target in(0x08069200,0x08153538,0x0805D284,0x0805BF80,0x08062DC0),'closed fishing opaque callee '+hex(target)+' site '+hex(site))
   result=0 if target==0x08153538 else 1 if target in(0x0805BF80,0x08062DC0)else rt.U
   boundary(m,site,target,result)
   for r in(0,1,2,3,12):m.reg[r]=rt.U
   m.reg[0]=result;m.flag_pc=None;m.pc=m.reg[14]&~1
  if stop is None:need(m.reg[13]==0x03007000,'balanced fishing API/frame stack')
  return m
 mem=rt.task_fixture([])
 for slot in range(16):
  for off in range(40):
   if off!=4:mem[TASKS+40*slot+off]=0xA5
 m=go(ROOT['constructor'],mem,{0:rod})
 need(m.read(TASKS,4)==ROOT['registered_task']and m.read(TASKS+4,1)==1 and m.read(TASKS+7,1)==255 and m.read(TASKS+8,2)==1 and m.read(TASKS+10,2)==0 and m.read(TASKS+38,2)==rod,'actual registration/zero-data/initial-state producer')
 # 以下は根未結合の局所診断。injectionを隠して受入へ昇格してはならない。
 phase='isolated_bypass';m.write(TASKS+8,2,6);m=go(ROOT['bypass_entry'],m.mem,{0:TASKS})
 need(m.read(TASKS+8,2)==9 and m.reg[0]==0,'real step6 add3 returns step9')
 phase='injected_timeout';m.write(TASKS+8,2,7);m.write(TASKS+10,2,0);m.write(AVATAR+4,1,0);m.write(MAIN+46,2,0)
 counter=[]
 for frame in range(TIMEOUTS['values'][rod]+1):
  boundary(m,0,0);m=go(ROOT['task_dispatch'],m.mem,stop=ROOT['stop'])
  counter.append(m.read(TASKS+10,2))
  if m.pc==ROOT['stop']:break
 need(m.pc==ROOT['stop']and m.read(TASKS+8,2)==12 and counter==list(range(1,TIMEOUTS['values'][rod]+1))+[TIMEOUTS['values'][rod]],'actual finite timeout and later selected consumer')
 need(m.reg[0]==SPRITES and m.reg[1]==1,'actual selected sprite hit-call arguments')
 fields=common.project(trace,len(boundaries))
 if projections is not None:need(exact(fields,projections),'repeat minimal fishing live projection')
 for index,b in enumerate(boundaries):b['required_fields']=fields[index]
 return dict(trace=trace,boundaries=boundaries,projections=fields,visited=visited,events=events,rod=rod,timeout=TIMEOUTS['values'][rod],scheduler_frames=frame+1,stop=m.pc)

def compose_selected(raw,rod=None,**kwargs):
 need(rod is None or type(rod)is int and rod in(0,1,2),'closed selected rod')
 for key in('opaque_writes','epoch_events'):
  value=kwargs.get(key);need(value is None or type(value)is dict and all(type(x)is int and(x==0 or x in INS and INS[x].kind=='call')for x in value),'closed fishing effect site')
 bind_semantics(raw);cases=[];sites=set()
 for r in(range(3)if rod is None else [rod]):
  first=_case(raw,r,**kwargs);second=_case(raw,r,projections=first['projections'],**kwargs)
  need(exact(first['events'],second['events']),'same local producer events after nonlive erasure');sites.update(x['site']for x in second['boundaries'])
  grouped={}
  for row in second['boundaries']:
   k=json.dumps(row,sort_keys=True,separators=(',',':'));grouped.setdefault(k,dict(**row,occurrences=0))['occurrences']+=1
  cases.append(dict(rod=r,timeout=second['timeout'],scheduler_frames=second['scheduler_frames'],stopped_at=second['stop'],initial_step_produced=1,isolated_bypass_input=6,isolated_bypass_output=9,injected_timeout_state=7,injected_timeout_counter=0,initial_free_task_data_poisoned=True,real_create_task_executed=True,real_timeout_memcpy_executed=True,nonlive_ram_erased_at_every_boundary=True,boundary_count=len(second['boundaries']),semantic_instruction_count=len(second['visited']),trace_identity=canonical(second['trace']),boundary_identity=canonical(second['boundaries']),events_identity=canonical(second['events']),conditional_call_catalog=list(grouped.values())))
 for key in('opaque_writes','epoch_events'):need(set(kwargs.get(key)or{})<=sites,'effect site was not an executed boundary')
 return dict(status='PASS_DIAGNOSTIC_FISHING_ROOT_GAP_HELD',cases=cases,**CLAIMS)

def protected_windows(review):
 rows=review['windows'];need(type(rows)is list and len(rows)==len(FIXED_GEOMETRY),'closed fishing windows')
 need(all(type(r)is dict and set(r)=={'address','size','sha256'}for r in rows),'address-size-SHA only')
 need(exact([[r['address'],r['size']]for r in rows],FIXED_GEOMETRY),'exact bounded fishing evidence geometry')
 need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef'for c in r['sha256'])for r in rows),'complete SHA format')
 return copy.deepcopy(rows)
def evidence_template(hit):raise ValueError('Fishing outer timeout producer unresolved; no type witness')
def witness_geometry(e):raise ValueError('Fishing unknown has no accepted geometry')
def make_review(raw,hits):
 by={h['address']:h for h in hits};return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hits=[copy.deepcopy(by[h])for h in INVESTIGATED_HITS],root=copy.deepcopy(ROOT),windows=[dict(address=a,**identity(chunk(raw,a,n)))for a,n in FIXED_GEOMETRY],claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT))
# 固定の局所診断全文identity。raw traceを含めず、入れ子の全field改変を拒否する。
COMPOSITION_IDENTITY={'size':11051,'sha256':'46aea815b5a023ad3a1b2019b7a9774529780bed5cd9341a2878da264c173fde'}
def held_proof_template(composition,current_candidate_measured=False):
 need(type(current_candidate_measured)is bool,'explicit current gate boolean')
 return dict(status='PASS_FISHING_HELD_UNKNOWN',count=0,hits=[],held_hits=list(HELD_HITS),protected_windows=len(FIXED_GEOMETRY),protected_bytes=sum(n for a,n in FIXED_GEOMETRY),composition=copy.deepcopy(composition),source_bindings=copy.deepcopy(SOURCE_IDS),all_inherited_fields_unchanged=True,current_candidate_measured=current_candidate_measured,**copy.deepcopy(CLAIMS))
def validate_held_proof(proof,current_candidate_measured=False):
 need(type(proof)is dict and type(proof.get('composition'))is dict,'closed fishing held proof object')
 need(exact(canonical(proof['composition']),COMPOSITION_IDENTITY),'exact fixed diagnostic composition identity')
 need(exact(proof,held_proof_template(proof['composition'],current_candidate_measured)),'exact closed fishing unknown-retention proof')
 return True

def _regions(raw,inherited,review,sources):
 need(type(review)is dict and set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract'},'closed fishing review')
 need(type(review['schema_version'])is int and review['schema_version']==1,'integer schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'separate current/diagnostic identities')
 need(exact(review['root'],ROOT)and exact(review['claims'],CLAIMS)and exact(review['input_contract'],CONTRACT),'closed fishing root and held claims')
 rows=[h for a in INVESTIGATED_HITS for h in inherited['hits']if h['address']==a]
 need(len(rows)==1 and exact(rows,review['hits']),'exact inherited fishing hit')
 for h in rows:
  need(h['accepted']is False and h['owner_candidates']==[]and h['classification']=='UNCLASSIFIED','owner-external unknown stays unknown')
  need(type(h['size'])is int and h['size']==4 and h['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','four-byte inventory occurrence');d.signed(raw,h)
 sources_bind(review,sources);d.signed(raw,protected_windows(review));proof=compose_selected(raw)
 details=held_proof_template(proof);validate_held_proof(details);return [],details
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current gate; diagnostic cannot classify current')
 rows,proof=_regions(raw,inherited,review,sources);proof['current_candidate_measured']=True
 validate_held_proof(proof,True);return rows,proof
