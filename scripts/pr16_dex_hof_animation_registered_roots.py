"""実登録animation2件のserializer・callback最小型。自然play・描画成功は主張しない。"""
import ast,copy,hashlib,json,re
from collections import namedtuple
import pr16_dex_hof_extra_roots as prior
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_donor as d
need,identity,chunk=d.need,d.identity,d.chunk
exact,encoded=prior.exact,prior.encoded
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
KIND='registered_animation_minimum_thumb'
KINDS=(KIND,)
TYPE_CATEGORY='code'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x090C4BC1,0x090C5BFB)
HELD_HITS=()
EXPECTED_HITS=[{'accepted': False,
  'address': 151800769,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': '8bc8a2a29d457999ad631317c6163f12c090bc56797b56d2d3826058fd22ba3c',
  'size': 4,
  'target': 167709168},
 {'accepted': False,
  'address': 151804923,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': '2f22efc9b11c66c1aebe703c152c6822f524aaa05118bcd1d87f489c9cebc8e9',
  'size': 4,
  'target': 167700976}]
CURSOR,ARGS,ATTACKER,TARGET,BATTLE_FLAGS=0x02037E08,0x02037E36,0x02037E4E,0x02037E4F,0x02022AAC
SPRITES=0x020205B8
SOURCE_IDS={'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'cfru-anim_defines.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                         'git_blob_sha': 'fc4168cbc9f43ef084afb04ff4ec8c81f9390592',
                         'local': 'cfru-anim_defines.s',
                         'repository': 'kapibarasan000/CFRU-JP',
                         'sha256': '166cbae334e3c45cb0d694fb483b8ac13b9cc84dc4bd64eb8d04ee696c1e84e4',
                         'size': 33164,
                         'source': 'anim_defines.s',
                         'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/anim_defines.s'},
 'cfru-attack-anim-table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                              'git_blob_sha': '2049efe7d416113b0b5be496e6a9c5ed6b305d1a',
                              'local': 'cfru-attack-anim-table.s',
                              'repository': 'kapibarasan000/CFRU-JP',
                              'sha256': '9c5ef07b85c3a0cbf809ad18cfeddf59d548a970d2df12f480ea93b6de9febb2',
                              'size': 1232828,
                              'source': 'assembly/data/attack_anim_table.s',
                              'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/attack_anim_table.s'},
 'cfru-battle-anims.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                         'git_blob_sha': '096a8763a4260052566ed029f841bc68e561d269',
                         'local': 'cfru-battle-anims.c',
                         'repository': 'kapibarasan000/CFRU-JP',
                         'sha256': '4893fda793e75356672e8b1be3bca4bd54fe562774fd8b07ed9f8f9ba501aff3',
                         'size': 192535,
                         'source': 'src/battle_anims.c',
                         'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/battle_anims.c'},
 'pret-battle-anim-data.h': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                             'git_blob_sha': 'ec8dc3de772056de958bba1227e7172b500a0380',
                             'line_range': [352, 364],
                             'local': 'pret-battle-anim-data.h',
                             'repository': 'pret/pokefirered',
                             'sha256': 'c4cfe40d12623423e80d72946c4554783fc06b0d8cd80b48309295c475508ec1',
                             'size': 61792,
                             'source': 'src/data/battle_anim.h',
                             'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/data/battle_anim.h#L352-L364'},
 'pret-battle_anim.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                        'git_blob_sha': '30f9a7ad2482d1767f5c70ee30a3c85528605bb3',
                        'local': 'pret-battle_anim.c',
                        'repository': 'pret/pokefirered',
                        'sha256': '5883d9ee0483120ef67461952f5880499f322fb1c706cc213ca13c0c2b0e88c5',
                        'size': 46944,
                        'source': 'src/battle_anim.c',
                        'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/battle_anim.c'},
 'pret-gba-types.h': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                      'git_blob_sha': '35d02e26391d872b486ca051d51f8485f3a7a0e5',
                      'line_range': [55, 118],
                      'local': 'pret-gba-types.h',
                      'repository': 'pret/pokefirered',
                      'sha256': 'd83a5cb845180b881f3de081ef9c2694b2da017a406fd3d6b0830329cc64ed93',
                      'size': 4213,
                      'source': 'include/gba/types.h',
                      'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/include/gba/types.h#L55-L118'},
 'pret-sprite.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'git_blob_sha': 'd0198d53004775c8664dcccf57833e178833776e',
                   'line_range': [532, 610],
                   'local': 'pret-sprite.c',
                   'repository': 'pret/pokefirered',
                   'sha256': '2a804302eb5a89d31c3ec2f33dc645a80a0c645113d4b33b9bd571064c0286ae',
                   'size': 48783,
                   'source': 'src/sprite.c',
                   'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/sprite.c#L532-L610'},
 'pret-sprite.h': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'git_blob_sha': '6a1b272119ce6e3a8dcf45adf2eef8923a6d5175',
                   'line_range': [181, 242],
                   'local': 'pret-sprite.h',
                   'repository': 'pret/pokefirered',
                   'sha256': 'a77aa1c837dfb58cf60b3eac299c7cc29a23ce27735ba710b9e8eeed102bf773',
                   'size': 9368,
                   'source': 'include/sprite.h',
                   'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/include/sprite.h#L181-L242'}}
SPECS=[(134684620, 'push', [16, True]),
 (134684622, 'literal', [4, 134684668]),
 (134684624, 'literal', [0, 134684672]),
 (134684626, 'mem', [True, 'word', 0, 0, 0]),
 (134684628, 'mem', [True, 'byte', 0, 0, 0]),
 (134684630, 'shift', ['lsl', 0, 0, 2]),
 (134684632, 'add', [0, 0, 4]),
 (134684634, 'mem', [True, 'word', 0, 0, 0]),
 (134684636, 'call', [136084168]),
 (134685108, 'push', [240, True]),
 (134685110, 'literal', [4, 134685220]),
 (134685112, 'mem', [True, 'word', 1, 4, 0]),
 (134685114, 'addi', [3, 1, 1]),
 (134685116, 'mem', [False, 'word', 3, 4, 0]),
 (134685118, 'mem', [True, 'byte', 2, 1, 1]),
 (134685120, 'mem', [True, 'byte', 0, 3, 1]),
 (134685122, 'shift', ['lsl', 0, 0, 8]),
 (134685124, 'add', [2, 2, 0]),
 (134685126, 'mem', [True, 'byte', 0, 3, 2]),
 (134685128, 'shift', ['lsl', 0, 0, 16]),
 (134685130, 'add', [2, 2, 0]),
 (134685132, 'mem', [True, 'byte', 0, 3, 3]),
 (134685134, 'shift', ['lsl', 0, 0, 24]),
 (134685136, 'add', [6, 2, 0]),
 (134685138, 'addi', [0, 1, 5]),
 (134685140, 'mem', [False, 'word', 0, 4, 0]),
 (134685142, 'mem', [True, 'byte', 7, 1, 5]),
 (134685144, 'addi', [0, 1, 6]),
 (134685146, 'mem', [False, 'word', 0, 4, 0]),
 (134685148, 'mem', [True, 'byte', 0, 1, 6]),
 (134685150, 'imm', ['add', 1, 7]),
 (134685152, 'mem', [False, 'word', 1, 4, 0]),
 (134685154, 'imm', ['cmp', 0, 0]),
 (134685156, 'branch', [0, 134685188]),
 (134685158, 'addi', (5, 4, 0)),
 (134685160, 'literal', (4, 134685224)),
 (134685162, 'addi', (3, 0, 0)),
 (134685164, 'mem', (True, 'word', 2, 5, 0)),
 (134685166, 'mem', (True, 'byte', 1, 2, 0)),
 (134685168, 'mem', (True, 'byte', 0, 2, 1)),
 (134685170, 'shift', ('lsl', 0, 0, 8)),
 (134685172, 'alu', ('orr', 1, 0)),
 (134685174, 'mem', (False, 'half', 1, 4, 0)),
 (134685176, 'imm', ('add', 2, 2)),
 (134685178, 'mem', (False, 'word', 2, 5, 0)),
 (134685180, 'imm', ('add', 4, 2)),
 (134685182, 'imm', ('sub', 3, 1)),
 (134685184, 'imm', ('cmp', 3, 0)),
 (134685186, 'branch', (1, 134685164)),
 (134685188, 'addi', [0, 6, 0]),
 (134685190, 'addi', [1, 7, 0]),
 (134685192, 'call', [134704052]),
 (134685196, 'shift', ['lsl', 0, 0, 24]),
 (134685198, 'shift', ['lsr', 0, 0, 24]),
 (134685200, 'call', [136084192]),
 (136084168, 'bx', (0,)),
 (136084192, 'bx', (6,)),
 (151779204, 'literal', (3, 151779268)),
 (151779206, 'shift', ('lsl', 0, 0, 1)),
 (151779208, 'signed_load', ('half', 3, 0, 3)),
 (151779210, 'literal', (2, 151779272)),
 (151779212, 'mem', (True, 'word', 2, 2, 0)),
 (151779214, 'shift', ('lsl', 2, 2, 31)),
 (151779216, 'branch', (5, 151779236)),
 (151779218, 'imm', ('cmp', 3, 2)),
 (151779220, 'branch', (0, 151779256)),
 (151779222, 'imm', ('cmp', 3, 3)),
 (151779224, 'branch', (1, 151779240)),
 (151779226, 'literal', (3, 151779276)),
 (151779228, 'mem', (True, 'byte', 0, 3, 0)),
 (151779230, 'imm', ('mov', 3, 2)),
 (151779232, 'alu_ext', ('eor', 0, 3)),
 (151779234, 'jump', (151779248,)),
 (151779236, 'imm', ('mov', 2, 2)),
 (151779238, 'alu_ext', ('bic', 3, 2)),
 (151779240, 'imm', ('cmp', 3, 0)),
 (151779242, 'branch', (0, 151779250)),
 (151779244, 'literal', (3, 151779276)),
 (151779246, 'mem', (True, 'byte', 0, 3, 0)),
 (151779248, 'bx', (14,)),
 (151779250, 'literal', (3, 151779280)),
 (151779252, 'mem', (True, 'byte', 0, 3, 0)),
 (151779254, 'jump', (151779248,)),
 (151779256, 'literal', (3, 151779280)),
 (151779258, 'mem', (True, 'byte', 0, 3, 0)),
 (151779260, 'imm', ('mov', 3, 2)),
 (151779262, 'alu_ext', ('eor', 0, 3)),
 (151779264, 'jump', (151779248,)),
 (151800720, 'push', [112, True]),
 (151800722, 'shift', ['lsl', 4, 0, 0]),
 (151800724, 'imm', ['mov', 0, 2]),
 (151800726, 'call', [151779204]),
 (151800730, 'literal', [3, 151800816]),
 (151800732, 'shift', ['lsl', 5, 0, 0]),
 (151800734, 'call', [151808464]),
 (151800738, 'imm', ['cmp', 0, 0]),
 (151800740, 'branch', [1, 151800752]),
 (151800742, 'shift', ['lsl', 0, 4, 0]),
 (151800744, 'literal', [3, 151800820]),
 (151800746, 'call', [151808464]),
 (151800750, 'pop', [112, True]),
 (151800752, 'imm', ['mov', 1, 0]),
 (151800754, 'shift', ['lsl', 0, 5, 0]),
 (151800756, 'literal', [6, 151800824]),
 (151800758, 'call', [151808470]),
 (151800762, 'imm', ['mov', 1, 1]),
 (151800764, 'mem', [False, 'half', 0, 4, 32]),
 (151800766, 'shift', ['lsl', 0, 5, 0]),
 (151800768, 'call', [151808470]),
 (151800772, 'literal', [5, 151800828]),
 (151804864, 'push', [112, True]),
 (151804866, 'shift', ['lsl', 5, 0, 0]),
 (151804868, 'imm', ['mov', 0, 0]),
 (151804870, 'call', [151779204]),
 (151804874, 'literal', [3, 151804956]),
 (151804876, 'shift', ['lsl', 4, 0, 0]),
 (151804878, 'call', [151808464]),
 (151804882, 'imm', ['cmp', 0, 0]),
 (151804884, 'branch', [1, 151804896]),
 (151804886, 'shift', ['lsl', 0, 5, 0]),
 (151804888, 'literal', [3, 151804960]),
 (151804890, 'call', [151808464]),
 (151804894, 'pop', [112, True]),
 (151804896, 'literal', [3, 151804964]),
 (151804898, 'shift', ['lsl', 0, 4, 0]),
 (151804900, 'call', [151808464]),
 (151804904, 'imm', ['mov', 1, 1]),
 (151804906, 'imm', ['sub', 0, 1]),
 (151804908, 'shift', ['lsl', 0, 0, 24]),
 (151804910, 'shift', ['lsr', 0, 0, 24]),
 (151804912, 'compare', [1, 0]),
 (151804914, 'alu_ext', ['sbc', 1, 1]),
 (151804916, 'literal', [3, 151804968]),
 (151804918, 'shift', ['lsl', 0, 4, 0]),
 (151804920, 'alu_ext', ['neg', 1, 1]),
 (151804922, 'call', [151808464]),
 (151804926, 'literal', [3, 151804972]),
 (151808464, 'bx', (3,)),
 (151808470, 'bx', (6,))]
WORDS={134684020: 151299796,
 134684668: 137830284,
 134684672: 33783304,
 134685220: 33783304,
 134685224: 33783350,
 137830292: 134684865,
 137830296: 134685109,
 151779268: 33783350,
 151779272: 33696428,
 151779276: 33783375,
 151779280: 33783374,
 151800816: 134686101,
 151800820: 134684389,
 151800824: 134692841,
 151800828: 33783350,
 151804956: 134686101,
 151804960: 134684421,
 151804964: 134695293,
 151804968: 134686189,
 151804972: 33701028}
SPRITE_SPECS=[(134684864, 'push', [240, True]),
 (134684866, 'literal', [5, 134684968]),
 (134684868, 'mem', [True, 'word', 1, 5, 0]),
 (134684870, 'addi', [3, 1, 1]),
 (134684872, 'mem', [False, 'word', 3, 5, 0]),
 (134684874, 'mem', [True, 'byte', 2, 1, 1]),
 (134684876, 'mem', [True, 'byte', 0, 3, 1]),
 (134684878, 'shift', ['lsl', 0, 0, 8]),
 (134684880, 'add', [2, 2, 0]),
 (134684882, 'mem', [True, 'byte', 0, 3, 2]),
 (134684884, 'shift', ['lsl', 0, 0, 16]),
 (134684886, 'add', [2, 2, 0]),
 (134684888, 'mem', [True, 'byte', 0, 3, 3]),
 (134684890, 'shift', ['lsl', 0, 0, 24]),
 (134684892, 'add', [7, 2, 0]),
 (134684894, 'addi', [0, 1, 5]),
 (134684896, 'mem', [False, 'word', 0, 5, 0]),
 (134684898, 'mem', [True, 'byte', 4, 1, 5]),
 (134684900, 'addi', [0, 1, 6]),
 (134684902, 'mem', [False, 'word', 0, 5, 0]),
 (134684904, 'mem', [True, 'byte', 0, 1, 6]),
 (134684906, 'imm', ['add', 1, 7]),
 (134684908, 'mem', [False, 'word', 1, 5, 0]),
 (134684910, 'imm', ['cmp', 0, 0]),
 (134684912, 'branch', [0, 134684944]),
 (134684914, 'addi', [6, 5, 0]),
 (134684916, 'literal', [5, 134684972]),
 (134684918, 'addi', [3, 0, 0]),
 (134684920, 'mem', [True, 'word', 2, 6, 0]),
 (134684922, 'mem', [True, 'byte', 1, 2, 0]),
 (134684924, 'mem', [True, 'byte', 0, 2, 1]),
 (134684926, 'shift', ['lsl', 0, 0, 8]),
 (134684928, 'alu', ['orr', 1, 0]),
 (134684930, 'mem', [False, 'half', 1, 5, 0]),
 (134684932, 'imm', ['add', 2, 2]),
 (134684934, 'mem', [False, 'word', 2, 6, 0]),
 (134684936, 'imm', ['add', 5, 2]),
 (134684938, 'imm', ['sub', 3, 1]),
 (134684940, 'imm', ['cmp', 3, 0]),
 (134684942, 'branch', [1, 134684920]),
 (134684944, 'imm', ['mov', 0, 128]),
 (134684946, 'alu', ['and', 0, 4]),
 (134684948, 'imm', ['cmp', 0, 0]),
 (134684950, 'branch', [0, 134684992]),
 (134684952, 'imm', ['mov', 0, 128]),
 (134684954, 'alu_ext', ['eor', 4, 0]),
 (134684956, 'imm', ['cmp', 4, 63]),
 (134684958, 'branch', [9, 134684976]),
 (134684976, 'alu', ['neg', 0, 4]),
 (134684978, 'shift', ['lsl', 0, 0, 24]),
 (134684980, 'shift', ['lsr', 4, 0, 24]),
 (134684982, 'literal', [0, 134684988]),
 (134684984, 'jump', [134685010]),
 (134685010, 'mem', [True, 'byte', 0, 0, 0]),
 (134685012, 'call', [134701056]),
 (134685016, 'shift', ['lsl', 0, 0, 24]),
 (134685018, 'shift', ['lsr', 0, 0, 24]),
 (134685020, 'shift', ['lsl', 1, 4, 24]),
 (134685022, 'shift', ['asr', 1, 1, 24]),
 (134685024, 'add', [0, 0, 1]),
 (134685026, 'shift', ['lsl', 0, 0, 16]),
 (134685028, 'shift', ['lsr', 6, 0, 16]),
 (134685030, 'shift', ['lsl', 0, 6, 16]),
 (134685032, 'shift', ['asr', 0, 0, 16]),
 (134685034, 'imm', ['cmp', 0, 2]),
 (134685036, 'branch', [12, 134685040]),
 (134685038, 'imm', ['mov', 6, 3]),
 (134685040, 'literal', [5, 134685100]),
 (134685042, 'mem', [True, 'byte', 0, 5, 0]),
 (134685044, 'imm', ['mov', 1, 2]),
 (134685046, 'call', [134691876]),
 (134685050, 'addi', [4, 0, 0]),
 (134685052, 'shift', ['lsl', 4, 4, 24]),
 (134685054, 'shift', ['lsr', 4, 4, 24]),
 (134685056, 'mem', [True, 'byte', 0, 5, 0]),
 (134685058, 'imm', ['mov', 1, 3]),
 (134685060, 'call', [134691876]),
 (134685064, 'addi', [2, 0, 0]),
 (134685066, 'shift', ['lsl', 2, 2, 24]),
 (134685068, 'shift', ['lsr', 2, 2, 24]),
 (134685070, 'shift', ['lsl', 3, 6, 24]),
 (134685072, 'shift', ['lsr', 3, 3, 24]),
 (134685074, 'addi', [0, 7, 0]),
 (134685076, 'addi', [1, 4, 0]),
 (134685078, 'call', [134245736]),
 (134245736, 'push', [240, True]),
 (134245738, 'movhi', [7, 10]),
 (134245740, 'movhi', [6, 9]),
 (134245742, 'movhi', [5, 8]),
 (134245744, 'push', [224, False]),
 (134245746, 'spadd', [-4]),
 (134245748, 'movhi', [10, 0]),
 (134245750, 'shift', ['lsl', 3, 3, 24]),
 (134245752, 'shift', ['lsr', 3, 3, 24]),
 (134245754, 'movhi', [9, 3]),
 (134245756, 'imm', ['mov', 3, 0]),
 (134245758, 'literal', [5, 134245848]),
 (134245760, 'shift', ['lsl', 1, 1, 16]),
 (134245762, 'movhi', [12, 1]),
 (134245764, 'shift', ['lsl', 2, 2, 16]),
 (134245766, 'movhi', [8, 2]),
 (134245768, 'shift', ['lsl', 0, 3, 4]),
 (134245770, 'add', [0, 0, 3]),
 (134245772, 'shift', ['lsl', 6, 0, 2]),
 (134245774, 'add', [4, 6, 5]),
 (134245776, 'addi', [7, 4, 0]),
 (134245778, 'imm', ['add', 7, 62]),
 (134245780, 'mem', [True, 'byte', 0, 7, 0]),
 (134245782, 'shift', ['lsl', 0, 0, 31]),
 (134245784, 'imm', ['cmp', 0, 0]),
 (134245786, 'branch', [1, 134245856]),
 (134245788, 'movhi', [0, 9]),
 (134245790, 'spmem', [False, 0, 0]),
 (134245792, 'addi', [0, 3, 0]),
 (134245794, 'movhi', [1, 10]),
 (134245796, 'movhi', [3, 12]),
 (134245798, 'shift', ['asr', 2, 3, 16]),
 (134245800, 'movhi', [5, 8]),
 (134245802, 'shift', ['asr', 3, 5, 16]),
 (134245804, 'call', [134245392]),
 (134245808, 'shift', ['lsl', 0, 0, 24]),
 (134245810, 'shift', ['lsr', 0, 0, 24]),
 (134245812, 'addi', [5, 0, 0]),
 (134245814, 'imm', ['cmp', 5, 64]),
 (134245816, 'branch', [0, 134245866]),
 (134245818, 'literal', [1, 134245852]),
 (134245820, 'add', [0, 6, 1]),
 (134245822, 'mem', [True, 'word', 1, 0, 0]),
 (134245824, 'addi', [0, 4, 0]),
 (134245826, 'call', [136084172]),
 (134245856, 'addi', [0, 3, 1]),
 (134245858, 'shift', ['lsl', 0, 0, 24]),
 (134245860, 'shift', ['lsr', 3, 0, 24]),
 (134245862, 'imm', ['cmp', 3, 63]),
 (134245864, 'branch', [9, 134245768]),
 (134245392, 'push', [240, True]),
 (134245394, 'movhi', [7, 10]),
 (134245396, 'movhi', [6, 9]),
 (134245398, 'movhi', [5, 8]),
 (134245400, 'push', [224, False]),
 (134245402, 'movhi', [8, 1]),
 (134245404, 'addi', [5, 2, 0]),
 (134245406, 'addi', [6, 3, 0]),
 (134245408, 'spmem', [True, 4, 32]),
 (134245410, 'shift', ['lsl', 0, 0, 24]),
 (134245412, 'shift', ['lsr', 0, 0, 24]),
 (134245414, 'movhi', [10, 0]),
 (134245416, 'shift', ['lsl', 5, 5, 16]),
 (134245418, 'shift', ['lsr', 5, 5, 16]),
 (134245420, 'shift', ['lsl', 6, 6, 16]),
 (134245422, 'shift', ['lsr', 6, 6, 16]),
 (134245424, 'shift', ['lsl', 4, 4, 24]),
 (134245426, 'shift', ['lsr', 4, 4, 24]),
 (134245428, 'shift', ['lsl', 0, 0, 4]),
 (134245430, 'addhi', [0, 10]),
 (134245432, 'shift', ['lsl', 0, 0, 2]),
 (134245434, 'literal', [1, 134245588]),
 (134245436, 'add', [7, 0, 1]),
 (134245438, 'addi', [0, 7, 0]),
 (134245440, 'call', [134246232]),
 (134245444, 'addi', [2, 7, 0]),
 (134245446, 'imm', ['add', 2, 62]),
 (134245448, 'mem', [True, 'byte', 0, 2, 0]),
 (134245450, 'imm', ['mov', 1, 1]),
 (134245452, 'alu', ['orr', 0, 1]),
 (134245454, 'mem', [False, 'byte', 0, 2, 0]),
 (134245456, 'imm', ['mov', 0, 63]),
 (134245458, 'add', [0, 0, 7]),
 (134245460, 'movhi', [9, 0]),
 (134245462, 'mem', [True, 'byte', 0, 0, 0]),
 (134245464, 'imm', ['mov', 1, 4]),
 (134245466, 'alu', ['orr', 0, 1]),
 (134245468, 'imm', ['mov', 1, 8]),
 (134245470, 'alu', ['orr', 0, 1]),
 (134245472, 'imm', ['mov', 1, 64]),
 (134245474, 'alu', ['orr', 0, 1]),
 (134245476, 'movhi', [1, 9]),
 (134245478, 'mem', [False, 'byte', 0, 1, 0]),
 (134245480, 'addi', [0, 7, 0]),
 (134245482, 'imm', ['add', 0, 67]),
 (134245484, 'mem', [False, 'byte', 4, 0, 0]),
 (134245486, 'movhi', [1, 8]),
 (134245488, 'mem', [True, 'word', 0, 1, 4]),
 (134245490, 'mem', [True, 'word', 1, 0, 4]),
 (134245492, 'mem', [True, 'word', 0, 0, 0]),
 (134245494, 'mem', [False, 'word', 0, 7, 0]),
 (134245496, 'mem', [False, 'word', 1, 7, 4]),
 (134245498, 'movhi', [1, 8]),
 (134245500, 'mem', [True, 'word', 0, 1, 8]),
 (134245502, 'mem', [False, 'word', 0, 7, 8]),
 (134245504, 'mem', [True, 'word', 0, 1, 16]),
 (134245506, 'mem', [False, 'word', 0, 7, 16]),
 (134245508, 'mem', [False, 'word', 1, 7, 20]),
 (134245510, 'mem', [True, 'word', 0, 1, 20]),
 (134245512, 'mem', [False, 'word', 0, 7, 28]),
 (134245514, 'mem', [False, 'half', 5, 7, 32]),
 (134245516, 'mem', [False, 'half', 6, 7, 34]),
 (134245518, 'mem', [True, 'byte', 3, 7, 1]),
 (134245520, 'shift', ['lsr', 1, 3, 6]),
 (134245522, 'mem', [True, 'byte', 2, 7, 3]),
 (134245524, 'shift', ['lsr', 2, 2, 6]),
 (134245526, 'shift', ['lsl', 3, 3, 30]),
 (134245528, 'shift', ['lsr', 3, 3, 30]),
 (134245530, 'addi', [0, 7, 0]),
 (134245532, 'call', [134246252]),
 (134245536, 'movhi', [0, 8]),
 (134245538, 'mem', [True, 'half', 1, 0, 0]),
 (134245540, 'literal', [4, 134245592]),
 (134245542, 'shift', ['lsr', 0, 4, 16]),
 (134245544, 'compare', [1, 0]),
 (134245546, 'branch', [1, 134245644]),
 (134245644, 'movhi', [1, 8]),
 (134245646, 'mem', [True, 'half', 0, 1, 0]),
 (134245648, 'call', [134251392]),
 (134245652, 'addi', [1, 7, 0]),
 (134245654, 'imm', ['add', 1, 64]),
 (134245656, 'mem', [False, 'half', 0, 1, 0]),
 (134245658, 'addi', [0, 7, 0]),
 (134245660, 'call', [134250628]),
 (134245664, 'mem', [True, 'byte', 0, 7, 1]),
 (134245666, 'shift', ['lsl', 0, 0, 30]),
 (134245668, 'shift', ['lsr', 0, 0, 30]),
 (134245670, 'imm', ['mov', 1, 1]),
 (134245672, 'alu', ['and', 0, 1]),
 (134245674, 'imm', ['cmp', 0, 0]),
 (134245676, 'branch', [0, 134245684]),
 (134245678, 'addi', [0, 7, 0]),
 (134245680, 'call', [134250888]),
 (134245684, 'movhi', [0, 8]),
 (134245686, 'mem', [True, 'half', 1, 0, 2]),
 (134245688, 'literal', [0, 134245732]),
 (134245690, 'compare', [1, 0]),
 (134245692, 'branch', [0, 134245714]),
 (134245694, 'movhi', [1, 8]),
 (134245696, 'mem', [True, 'half', 0, 1, 2]),
 (134245698, 'call', [134251876]),
 (134245702, 'shift', ['lsl', 0, 0, 4]),
 (134245704, 'mem', [True, 'byte', 2, 7, 5]),
 (134245706, 'imm', ['mov', 1, 15]),
 (134245708, 'alu', ['and', 1, 2]),
 (134245710, 'alu', ['orr', 1, 0]),
 (134245712, 'mem', [False, 'byte', 1, 7, 5]),
 (134245714, 'movhi', [0, 10]),
 (134245716, 'pop', [56, False]),
 (134245718, 'movhi', [8, 3]),
 (134245720, 'movhi', [9, 4]),
 (134245722, 'movhi', [10, 5]),
 (134245724, 'pop', [240, False]),
 (134245726, 'pop', [2, False]),
 (134245728, 'bx', [1]),
 (136084172, 'bx', [1])]
SPECS+=SPRITE_SPECS
WORDS.update({134245588: 33686968,
 134245592: 4294901760,
 134245732: 65535,
 134245848: 33686968,
 134245852: 33686996,
 134684968: 33783304,
 134684972: 33783350,
 134684988: 33783375,
 134685100: 33783375})
SPRITE_DATA=[{'address': 137824960, 'sha256': 'ebe53f21c7afb5dc412bc181ef678b38639f59d32e31a0446bb907ec63fe13df', 'size': 8}]

INS={a:party.Ins(a,k,args)for a,k,args in SPECS}
need(len(INS)==len(SPECS),'命令spec非重複')

class Machine(engine.Machine):
 """独立意味spec用。NZCVを命令ごとに更新し、未定義flag分岐は拒否。"""
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.consumer_reads=[];self.consumer_writes=[]
 def read(self,a,n):
  v=super().read(a,n)
  if self.pc in(0x08006C86,0x08006DBE,0x090BF788,0x090BF7AE,0x090BF7B4):self.consumer_reads.append((self.pc,a,n,v))
  return v
 def write(self,a,n,v):
  super().write(a,n,v)
  if self.pc in(0x08006C88,0x08072102,0x080721F6):self.consumer_writes.append((self.pc,a,n,v))
 def nz(self,value,carry=None,overflow=None):
  _,_,c,v=self.flags
  self.flags=((value>>31,bool(value==0))if rt.concrete(value)else(rt.U,rt.U))+((c if carry is None else carry),(v if overflow is None else overflow))
 def arith(self,a,b,subtract=False,carry=0):
  if not all(rt.concrete(x)or type(x)is bool for x in(a,b,carry)):self.flags=(rt.U,)*4;return rt.U
  full=a-b-int(carry)if subtract else a+b+int(carry);value=full&rt.MASK
  self.nz(value,full>=0 if subtract else full>rt.MASK,bool((((a^b)&(a^value))if subtract else(~(a^b)&(a^value)))&0x80000000))
  return value
 def condition(self,c):
  n,z,carry,v=self.flags
  fields={0:(z,),1:(z,),2:(carry,),3:(carry,),4:(n,),5:(n,),6:(v,),7:(v,),8:(carry,z),9:(carry,z),10:(n,v),11:(n,v),12:(z,n,v),13:(z,n,v)}
  need(c in fields and all(rt.concrete(x)or type(x)is bool for x in fields[c]),'分岐に必要なNZCVが定義済み')
  return (lambda:z,lambda:not z,lambda:carry,lambda:not carry,lambda:bool(n),lambda:not n,lambda:v,lambda:not v,lambda:carry and not z,lambda:not carry or z,lambda:n==v,lambda:n!=v,lambda:not z and n==v,lambda:z or n!=v)[c]()
 def step(self,branch_choice=None):
  need(branch_choice is None,'分岐の外部指定禁止');i=self.instructions[self.pc];k,x=i.kind,i.args;r=self.reg;handled=True
  if k=='branch':self.pc=x[1]if self.condition(x[0])else self.pc+2;self.steps+=1;return
  if k=='shift':
   op,rd,rs,n=x;v=r[rs];carry=None
   if not rt.concrete(v):value=rt.U;carry=rt.U if n or op!='lsl'else None
   elif op=='lsl':value=(v<<n)&rt.MASK;carry=bool(v&(1<<(32-n)))if n else None
   else:
    n=n or 32;carry=bool(v&(1<<(n-1)));value=(v>>n)if op=='lsr'else((v if v<1<<31 else v-(1<<32))>>n)&rt.MASK
   r[rd]=value;self.nz(value,carry)
  elif k=='imm':
   op,rd,v=x
   if op=='mov':r[rd]=v;self.nz(v)
   elif op=='cmp':self.arith(r[rd],v,True)
   else:r[rd]=self.arith(r[rd],v,op=='sub')
  elif k in('add','addi','sub','subi'):
   rd,rs,rhs=x;r[rd]=self.arith(r[rs],rhs if k.endswith('i')else r[rhs],k.startswith('sub'))
  elif k=='compare':self.arith(r[x[0]],r[x[1]],True)
  elif k in('alu','alu_ext'):
   op,rd,rs=x;a,b=r[rd],r[rs]
   if op=='neg':r[rd]=self.arith(0,b,True)
   elif op in('adc','sbc'):r[rd]=self.arith(a,b,op=='sbc',(not self.flags[2])if op=='sbc'and type(self.flags[2])in(bool,int)else self.flags[2])
   else:
    need(op in('and','orr','eor','bic','mul','tst','mvn'),'閉じたALU意味')
    value=({'and':lambda:a&b,'orr':lambda:a|b,'eor':lambda:a^b,'bic':lambda:a&~b,'mul':lambda:a*b,'tst':lambda:a&b,'mvn':lambda:~b}[op]()&rt.MASK)if rt.concrete(a)and rt.concrete(b)else rt.U
    if op!='tst':r[rd]=value
    self.nz(value,rt.U if op=='mul'else None)
  elif k=='regmem':
   op,rd,rb,ro=x;need(rt.concrete(r[rb])and rt.concrete(r[ro]),'実index memory');a=r[rb]+r[ro];n={'str':4,'strh':2,'strb':1,'ldr':4,'ldrh':2,'ldrb':1}[op]
   if op.startswith('ldr'):r[rd]=self.read(a,n)
   else:self.write(a,n,r[rd])
  else:handled=False
  if handled:self.pc+=i.size;self.steps+=1
  else:super().step()

ROOTS={
 'single':dict(hit=0x090C5BFB,script=0x090321B8,table_indices=[879],table_cells=[0x0904B490],command=0x09032234,opcode=3,handler=0x080721B4,callback=0x090C5BC0,callback_field=0x09032235,argument_index=0,stop=0x090C5BFA,static_successor=0x090C5BFE),
 'star':dict(hit=0x090C4BC1,script=0x090383A4,table_indices=[926,927],table_cells=[0x0904B54C,0x0904B550],call_field=0x090383DD,command=0x09038492,opcode=2,handler=0x080720C0,template=0x090386F0,callback=0x090C4B90,callback_field=0x09038704,argument_index=2,stop=0x090C4BC0,static_successor=0x090C4BC4,callback_writer=0x08006C88,callback_reader=0x08006DBE,callback_bx=0x081C7ACC)}
CLAIMS=dict(proof_scope='conditional_source_registered_animation_minimum_thumb',conditional_api_entry=True,complete_serializer_boundaries_proven=True,actual_opcode_consumer_proven=True,callback_pointer_host_seeded=False,complete_minimum_instruction_encoding_proven=True,whole_candidate_identity_checked_by_parent_required=True,actual_runtime_execution_observed=False,full_story_reachability_claimed=False,full_animation_prefix_executed=False,universal_heap_or_irq_lifetime_proven=False,opaque_callee_effects_proven=False,hit_callee_executed=False,hit_callee_return_required=False,static_successor_executed=False,whole_function_range_classified=False,padding_classified=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT=dict(
 entry_ja='実table cell879/926/927と完全source serializerから特定したcommandの処理時を条件付き入口にする。実opcode dispatcherから開始し完全callback/templateと全argを実byte readerで読む。公開index808/855/856や一律offsetを現在rootへ代用しない。先行command実行や自然move選択は未証明。',
 single_ja='CreateTaskはcallback/priorityを受け正常ABIで有効taskId0を返す有限条件。task callbackをRAMへhost seedしない。実r6/BXから即時callbackへ入り、実LoadBattleAnimTarget(0)が実arg0/attackerを読む。visible=1、position=0の十分条件でhit BL直前に達する。',
 star_ja='実commandの6argとtemplateをCreateSpriteAndAnimateへ渡す。最初のfree slot0、登録graphics資源とconstructor leafの有限成功を条件に、実InitSpriteのtemplate+20→同slot+28 writerと同期load/BXを実行。同slot epochを最終useまで保持。全constructor leaf effectsや自然資源準備は未証明。',
 context_ja='有限single-battle flags0、attacker0/target1。これらはsave観測でなく通常APIの有効入力条件。visibility=1、座標/priorityは有限正常戻り。LoadBattleAnimTargetは実source対応命令を通す。',
 memory_ja='各opaque境界は通常ABIのcallee-saved/SP/LRを保存。future read-before-write RAMと必要資源epochだけを条件化し、他のRAMはreplayでUnknownへ消去。未知site/余剰条件/必要live field破壊/同slot再利用は拒否、非live書換は許可する。',
 minimum_ja='各4byte hitを覆う完全BL4byteと静的successor LDR2byteだけを分類。hit BLを実行せず、そのcallee成功/描画/復帰を要求しない。隣接literal/function全域やdonor安全性は未分類。')
EXTERNAL={(0x08072208,0x08076BB4),(0x090C5BCE,0x08072594),(0x090C5BE4,0x0807497C),(0x090C4B9E,0x08072594),(0x090C4BB6,0x08073FE8)}

EXTERNAL.update({(134245660, 134250628), (134685060, 134691876), (134245648, 134251392), (134685012, 134701056), (134245532, 134246252), (134685046, 134691876), (134245680, 134250888), (134245440, 134246232), (134245698, 134251876)})

def preservation_contract(live,writes=(),events=None,sprite_live=False):
 need(type(live)is list and all(type(row)is list and len(row)==2 and all(type(v)is int for v in row)and row[1]>0 for row in live),'有限future-live射影')
 events={}if events is None else events
 need(type(events)is dict and set(events)<={'sprite_epoch_changed'}and all(type(v)is bool for v in events.values()),'閉じたresource epoch条件')
 need(not(sprite_live and events.get('sprite_epoch_changed',False)),'live同sprite slot epoch再利用禁止')
 for a,n,value in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(value)is int and 0<=value<1<<(8*n)and 0<=a<a+n<=1<<32,'有限opaque書込')
  need(not any(a<b+z and b<a+n for b,z in live),'future-live field破壊禁止')
  if sprite_live and a<=SPRITES+62<a+n:
   need(((value>>(8*(SPRITES+62-a)))&1)==1,'live同slot inUse clearはepoch破壊')
 return True

PROFILE=dict(battle_flags=0,attacker=0,target=1,task_id=0,visibility=1,position=0,sprite_slot=0,normal_abi_returns=True,resources_valid=True)
def _compose(raw,case,boundary_live=None,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(type(case)is str and case in ROOTS,'二つの登録APIだけ')
 need(profile is None or exact(profile,PROFILE),'閉じた有限成功profile')
 need(contract is None or exact(contract,CONTRACT),'閉じた有限環境契約')
 root=ROOTS[case];trace=[];mem={};boundaries=[];groups=[];visited=[];sprite_resource=False
 for a,n,v in((CURSOR,4,root['command']),(ATTACKER,1,0),(TARGET,1,1),(BATTLE_FLAGS,4,0)):
  rt.setmem(mem,a,n,v)
 if case=='star':
  rt.setmem(mem,SPRITES+62,1,0)
 m=Machine(raw,0x08071FCC,{},mem,instructions=INS,trace=trace)
 while m.pc!=root['stop']:
  need(m.steps<3000,'有限登録consumer path')
  if m.pc in INS:
   visited.append(m.pc)
   if m.pc==root['callback']:
    need(m.reg[0]==(0 if case=='single'else SPRITES),'実consumerからcallback引数')
   if case=='star'and m.pc==0x08006C88:
    need(m.reg[0]==root['callback']|1 and m.reg[7]==SPRITES,'実template+20から同slot writer')
   if case=='star'and m.pc==0x08006DBE:
    need(sprite_resource and rt.getmem(m.mem,SPRITES+28,4)==root['callback']|1,'同slot callback保持')
   m.step();continue
  site=(m.reg[14]&~1)-4;target=m.pc;need((site,target)in EXTERNAL,'閉じた実callee境界 '+hex(site)+' '+hex(target));value=rt.U;outputs=[]
  if target==0x08076BB4:
   need(case=='single'and m.reg[0]==root['callback']|1 and m.reg[1]==10,'実complete callback/priority引数');value=0
  elif target==0x08072594:
   need(m.reg[0]==(0 if case=='single'else 1),'実LoadBattleAnimTargetのbank');value=1
  elif target==0x0807497C:need(m.reg[0]==0,'実attacker位置引数');value=0
  elif target==0x08073FE8:need(case=='star'and m.reg[:2]==[1,0],'先行target x座標引数');value=120
  elif target==0x08076000:need(m.reg[0]==1,'実target priority');value=30
  elif target==0x08073C24:
   need(m.reg[0]==1 and m.reg[1]in(2,3),'実target initial coordinates');value=120 if m.reg[1]==2 else 80
  elif target==0x08006F58:
   need(m.reg[0]==SPRITES,'選択slot ResetSprite成功');outputs=[(SPRITES+62,1,0),(SPRITES+63,1,0)];sprite_resource=True
  elif target in(0x08006F6C,0x08008084,0x08008188):need(m.reg[0]==SPRITES and sprite_resource,'同slot graphics helper')
  elif target in(0x08008380,0x08008564):need(m.reg[0]==10364,'実template tagの登録資源');value=0
  else:raise ValueError('未束縛opaque成功出力')
  index=len(boundaries);boundaries.append((site,target));trace.append(('boundary',index,0))
  if boundary_live is not None:
   need(index<len(boundary_live),'全opaque射影');live=boundary_live[index]
   writes=(opaque_writes or {}).get(site,());events=(epoch_events or {}).get(site,{})
   preservation_contract(live,writes,events,sprite_live=sprite_resource)
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   groups.append(dict(site=site,target=target,required_fields=[dict(address=a,size=n)for a,n in live],conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs],return_value=value if rt.concrete(value)else 'unspecified',sprite_epoch_required=sprite_resource,normal_abi_return_required=True,effects_discharged=False))
  for a,n,v in outputs:m.write(a,n,v)
  for r in(0,1,2,3,12):m.reg[r]=rt.U
  m.reg[0]=value;m.flags=(rt.U,)*4;m.flag_pc=None;m.pc=m.reg[14]&~1
 need(root['handler']in visited and root['callback']in visited and 0x090BF784 in visited,'登録opcode→実callback→実arg consumer')
 need(m.reg[:2]==([0,1]if case=='single'else[1,1]),'hit BLの実引数を生成')
 need((0x090BF788,ARGS+2*root['argument_index'],2,0 if case=='single'else 1)in m.consumer_reads,'実arg読取')
 if case=='star':
  need((0x08006C86,root['template']+20,4,root['callback']|1)in m.consumer_reads,'実template callback read')
  need((0x08006C88,SPRITES+28,4,root['callback']|1)in m.consumer_writes,'実同slot callback writer')
  need((0x08006DBE,SPRITES+28,4,root['callback']|1)in m.consumer_reads and root['callback_bx']in visited,'実同slot callback read/BX')
 return dict(steps=m.steps,trace=trace,boundaries=boundaries,groups=groups,visited=visited,writes=m.writes,registers=m.reg,consumer_reads=m.consumer_reads,consumer_writes=m.consumer_writes)

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 known={site for site,_ in EXTERNAL}
 need(set(opaque_writes or {})<=known and set(epoch_events or {})<=known,'未知境界siteを黙殺しない')
 rows=[]
 for case in ROOTS:
  first=_compose(raw,case,profile=profile,contract=contract);live=engine.future_live(first['trace'],len(first['boundaries']))
  replay=_compose(raw,case,live,opaque_writes,epoch_events,profile,contract)
  need(first['visited']==replay['visited']and first['boundaries']==replay['boundaries'],'非live全消去後も同一実path')
  rows.append(dict(case=case,instruction_steps=first['steps'],endpoint=ROOTS[case]['stop'],visited_identity=identity(json.dumps(first['visited'],separators=(',',':')).encode()),conditional_call_groups=replay['groups'],nonlive_ram_erased_at_each_boundary=True,callback_pointer_host_seeded=False,hit_callee_executed=False,consumer_reads=first['consumer_reads'],consumer_writes=first['consumer_writes']))
 return dict(status='PASS_TWO_REGISTERED_ANIMATION_MINIMUMS',cases=rows,callback_pointer_host_seeded=False,nonlive_ram_erased_at_each_boundary=True,actual_runtime_execution_observed=False)

# 実cellそのものを固定する。公開table indexからの換算はしない。
ACTUAL_REGISTRATIONS = (
    (879, 0x0904B490, 0x090321B8),
    (926, 0x0904B54C, 0x090383A4),
    (927, 0x0904B550, 0x090383A4),
)

# 未解決symbolは全4byte fieldを別系統で固定。公開source全fileの配置、
# report observed_valueの汎用コピー、部分byteや近傍一致による推定は禁止。
# 値は固定診断調査の登録field候補。受入には今回chunksで完全一致が必要。
REGISTERED_POINTER_FIELDS = {
    0x090321D3: ("AnimTask_FadeOutAllBanksExceptAttackerAndTarget", 0x090C5951),
    0x090321E5: ("GENESIS_RISING_1", 0x090322E0),
    0x0903220E: ("GENESIS_RISING_2", 0x09032374),
    0x09032213: ("GENESIS_RISING_1", 0x090322E0),
    0x0903221E: ("GENESIS_REVERSAL_WAVE", 0x09032417),
    0x09032223: ("GENESIS_REVERSAL_WAVE", 0x09032417),
    0x09032228: ("GENESIS_REVERSAL_WAVE", 0x09032417),
    0x09032235: ("AnimTask_SingleBankToBg", 0x090C5BC1),
    0x090383BF: ("AnimTask_DynamaxGrowth", 0x090C4EC5),
    0x090383CA: ("STARFALL_STAR_TWINKLE", 0x09038434),
    0x090383D0: ("STARFALL_STARS_FALL", 0x0903845A),
    0x090383DD: ("STARFALL_BEAMS_UP", 0x09038492),
    0x0903840B: ("STARFALL_TARGET_BEAM_UP", 0x0903862E),
    0x09038493: ("STARFALL_BEAM", 0x090386F0),
    0x090386F8: ("gAnimCmdTable_StarfallBeam", 0x0915FE10),
    0x09038700: ("gSpriteAffineAnimTable_StarfallBeam", 0x0915FDE0),
    0x09038704: ("SpriteCB_StarfallBeam", 0x090C4B91),
}

# label, address, command count, serialized bytes, prefix/full/inline
BLOCKS = (
    ("ANIM_GENESIS_SUPERNOVA", 0x090321B8, 22, 133, "prefix"),
    ("ANIM_MAX_STARFALL", 0x090383A4, 23, 144, "full"),
    ("STARFALL_BEAMS_UP", 0x09038492, 1, 19, "prefix"),
    ("STARFALL_BEAM", 0x090386F0, 1, 24, "inline"),
)
REQUIRED_WINDOWS = {
    **{address: 4 for _, address, _ in ACTUAL_REGISTRATIONS},
    **{address: size for _, address, _, size, _ in BLOCKS},
}
WINDOW_IDENTITIES = {
    0x0904B490: "0f5696161afcd57d9b3cf9f97d2f559ccd65f8b6a501df7b62fea6232f426df6",
    0x0904B54C: "6a0b47773dbb13bcf13af1e09a661fa19a7775a80475f86b6a4e20f139ff9cc8",
    0x0904B550: "6a0b47773dbb13bcf13af1e09a661fa19a7775a80475f86b6a4e20f139ff9cc8",
    0x090321B8: "6e91175aa8e15add0d3c5f4fd4ffd0369600796439a848b8532f01e873a61edf",
    0x090383A4: "709908b853ec82671db687fb455c2ff8e669974b1ce54db501de1f5b6edd0677",
    0x09038492: "5f7174295d2dc72cd43c13987c0d439f684c0cdd9ccef7439be0f077fdb5eef8",
    0x090386F0: "5065561fa4a075284920794de14c00014969b8efa5e2c3b6a9e6394e2ff6c33f",
}



def _serializer_sources(sources):
 texts={}
 for name in ('cfru-anim_defines.s','cfru-attack-anim-table.s'):
  b=sources[name];row=SOURCE_IDS[name]
  need(identity(b)=={k:row[k]for k in('size','sha256')},'独立source serializer全文')
  texts[name]=b.decode()
 return texts

_Macro = namedtuple("_Macro", "params fields")


def _definitions(text):
    constants = {}
    for line in text.splitlines():
        clean = line.split("@", 1)[0].strip()
        if clean.startswith(".equ"):
            match = re.fullmatch(r"\.equ\s+(\w+),\s*(-?(?:0x[0-9a-fA-F]+|\d+))", clean)
            need(match is not None, "未対応equ式")
            symbol, scalar = match.groups()
            need(symbol not in constants or constants[symbol] == int(scalar, 0),
                     f"equ重複値が不一致: {symbol}")
            constants[symbol] = int(scalar, 0)
    macros = {}
    for match in re.finditer(r"\.macro\s+(\w+)[ \t]*([^\n]*)\n(.*?)\.endm", text, re.S):
        name, params, body = match.groups()
        fields = []
        for line in body.splitlines():
            clean = line.split("@", 1)[0].strip()
            if not clean:
                continue
            field = re.fullmatch(r"\.(byte|hword|word)\s+(\S+)", clean)
            # 今回使わないmacroにはbranch式がある。unsupportedは使用時に拒否。
            if field is None:
                fields = None
                break
            kind, expression = field.groups()
            fields.append(({"byte": 1, "hword": 2, "word": 4}[kind], expression))
        need(name not in macros, f"macro重複: {name}")
        macros[name] = _Macro(tuple(params.split()), tuple(fields) if fields is not None else ())
    return constants, macros


def _source_lines(text, label):
    matches = list(re.finditer(r"^" + re.escape(label) + r":([^\n]*)$", text, re.M))
    need(len(matches) == 1, f"source label不明/重複: {label}")
    match = matches[0]
    inline = match.group(1).split("@", 1)[0].strip()
    if inline:
        return [inline], True
    result = []
    for line in text[match.end():].splitlines():
        clean = line.split("@", 1)[0].strip()
        if not clean:
            continue
        if ":" in clean or clean.startswith("."):
            break
        result.append(clean)
    return result, False


def _scalar(expression, constants):
    """整数/equ/単項負号/ORだけを評価する。任意Python評価はしない。"""
    try:
        node = ast.parse(expression, mode="eval").body
    except (SyntaxError, ValueError) as error:
        raise ValueError("source数値式の構文不正") from error

    def visit(item):
        if isinstance(item, ast.Constant) and type(item.value) is int:
            return item.value
        if isinstance(item, ast.Name):
            if item.id not in constants:
                raise KeyError(item.id)
            return constants[item.id]
        if isinstance(item, ast.UnaryOp) and isinstance(item.op, ast.USub):
            return -visit(item.operand)
        if isinstance(item, ast.BinOp) and isinstance(item.op, ast.BitOr):
            return visit(item.left) | visit(item.right)
        raise ValueError("未許可source数値式")

    return visit(node)


def _command(line, address, constants, macros):
    normalized = re.sub(r"\s*\|\s*", "|", line).replace(",", " ")
    name, *tokens = normalized.split()
    need(name in macros and macros[name].fields, f"未対応macro: {name}")
    macro = macros[name]
    need(len(tokens) <= len(macro.params), f"macro引数過剰: {name}")
    args = dict(zip(macro.params, tokens))
    if name in ("launchtask", "launchtemplate"):
        need(len(tokens) >= 3, f"launch引数不足: {name}")
        count = _scalar(tokens[2], constants)
        need(0 <= count <= 9 and len(tokens) == 3 + count, f"launch ArgsNo不一致: {name}")
    else:
        need(len(tokens) == len(macro.params), f"macro引数数不一致: {name}")
    raw = bytearray()
    fields = []
    for width, expression in macro.fields:
        parameter = expression[1:] if expression.startswith("\\") else None
        if parameter is not None:
            need(parameter in macro.params, f"macro未定義parameter: {parameter}")
            if parameter not in args:
                need(name in ("launchtask", "launchtemplate") and "arg" in parameter,
                         "必須macro field欠落")
                continue
            expression = args[parameter]
        field_address = address + len(raw)
        try:
            value = _scalar(expression, constants)
            kind = "source_equ" if expression in constants else "source_numeric_expression"
            need(field_address not in REGISTERED_POINTER_FIELDS, "登録pointerがsource定数へ置換された")
        except KeyError:
            need(width == 4 and re.fullmatch(r"[A-Za-z_]\w*", expression) is not None,
                     f"未解決非pointer式: {expression}")
            binding = REGISTERED_POINTER_FIELDS.get(field_address)
            need(binding is not None and binding[0] == expression,
                     f"未結合source symbol: {expression}")
            value = binding[1]
            kind = "actual_registered_pointer_field"
        need(-(1 << (width * 8 - 1)) <= value < 1 << (width * 8), "field値が幅外")
        encoded = (value & ((1 << (width * 8)) - 1)).to_bytes(width, "little")
        raw.extend(encoded)
        fields.append({"address": field_address, "size": width, "source_expression": expression,
                       "source_macro_field": parameter or expression, "value": value,
                       "derivation": kind, "sha256": hashlib.sha256(encoded).hexdigest()})
    return bytes(raw), {"address": address, **identity(raw), "source": line,
                        "macro": name, "fields": fields}


def serialize_animation_sources(sources):
    """公開source＋明示登録束縛から内部期待bytesと非raw監査rowsを構築する。"""
    texts = _serializer_sources(sources)
    constants, macros = _definitions(texts['cfru-anim_defines.s'])
    chunks = {address: target.to_bytes(4, "little") for _, address, target in ACTUAL_REGISTRATIONS}
    rows = []
    pointer_addresses = set()
    for label, address, count, length, mode in BLOCKS:
        lines, inline = _source_lines(texts['cfru-attack-anim-table.s'], label)
        need(inline == (mode == "inline"), f"inline構造不一致: {label}")
        need(len(lines) >= count, f"command数不足: {label}")
        if mode in ("full", "inline"):
            need(len(lines) == count, f"command範囲不一致: {label}")
        encoded = bytearray()
        commands = []
        for line in lines[:count]:
            part, row = _command(line, address + len(encoded), constants, macros)
            encoded.extend(part)
            commands.append(row)
            pointer_addresses.update(field["address"] for field in row["fields"]
                                     if field["derivation"] == "actual_registered_pointer_field")
        need(len(encoded) == length, f"serializer範囲不一致: {label}")
        chunks[address] = bytes(encoded)
        rows.append({"label": label, "address": address, **identity(encoded),
                     "command_count": count, "extent": mode, "commands": commands})
    need(pointer_addresses == set(REGISTERED_POINTER_FIELDS), "登録pointer全fieldの被覆不一致")
    for address, encoded in chunks.items():
        need(hashlib.sha256(encoded).hexdigest() == WINDOW_IDENTITIES[address],
                 f"source再serializeと固定window identity不一致: {address:#010x}")
    # 注目fieldは位置・source引数・widthを個別に保証する。
    fields = {field["address"]: field for row in rows for command in row["commands"] for field in command["fields"]}
    for address, value in ((0x0903223B, 0), (0x0903849D, 1), (0x090386F0, 0x287C), (0x090386F2, 0x287C)):
        need(address in fields and fields[address]["size"] == 2 and fields[address]["value"] == value,
                 f"consumer引数/タグfield不一致: {address:#010x}")
    return chunks, rows


OAM_FIELDS=(('y',8,0),('affineMode',2,3),('objMode',2,0),('mosaic',1,0),('bpp',1,0),('shape',2,0),('x',9,0),('matrixNum',5,0),('size',2,1),('tileNum',10,0),('priority',2,2),('paletteNum',4,0),('affineParam',16,0))
def encode_oam(sources):
 header=sources['pret-gba-types.h'].decode();data=sources['pret-battle-anim-data.h'].decode()
 body=header.split('struct OamData',1)[1].split('};',1)[0]
 fields=[(name,int(width)if width else 16)for _,name,width in re.findall(r'\bu(16|32)\s+(\w+)(?::(\d+))?\s*;',body)]
 need(fields==[(name,width)for name,width,_ in OAM_FIELDS],'独立OAM全bitfield幅/順序')
 body=data.split('const struct OamData gOamData_AffineDouble_ObjNormal_16x16 =',1)[1].split('};',1)[0]
 initial=dict(re.findall(r'\.(\w+)\s*=\s*([^,]+),',body))
 expected={'y':'0','affineMode':'ST_OAM_AFFINE_DOUBLE','objMode':'ST_OAM_OBJ_NORMAL','bpp':'ST_OAM_4BPP','shape':'SPRITE_SHAPE(16x16)','x':'0','size':'SPRITE_SIZE(16x16)','tileNum':'0','priority':'2','paletteNum':'0'}
 need(initial==expected,'独立OAM source initializer/省略zero')
 for symbol,value in [('ST_OAM_AFFINE_DOUBLE',3),('ST_OAM_OBJ_NORMAL',0),('ST_OAM_4BPP',0),('ST_OAM_SQUARE',0),('ST_OAM_SIZE_1',1)]:
  need(re.search(r'#define\s+'+symbol+r'\s+'+str(value)+r'\b',header),'独立OAM数値macro')
 for token in ('#define SPRITE_SIZE_16x16   ((ST_OAM_SIZE_1 << 2) | (ST_OAM_SQUARE))','#define SPRITE_SIZE(dim)  ((SPRITE_SIZE_##dim >> 2) & 0x03)','#define SPRITE_SHAPE(dim) (SPRITE_SIZE_##dim & 0x03)'):
  need(token in header,'独立OAM dimension macro')
 value=0;offset=0
 for _,width,part in OAM_FIELDS:need(0<=part<1<<width,'OAM field範囲');value|=part<<offset;offset+=width
 need(offset==64,'完全8byte OAM extent');return value.to_bytes(8,'little')

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'公開source閉集合')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'独立公開source全文 '+name)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立公開Git blob '+name)
 roles={
  'cfru-battle-anims.c':['static bank_t LoadBattleAnimTarget(u8 arg)','switch (gBattleAnimArgs[arg])','battler = gBattleAnimAttacker;','battler = gBattleAnimTarget;','void AnimTask_SingleBankToBg(u8 taskId)','MoveBattlerSpriteToBG(bank, toBg2);','void SpriteCB_StarfallBeam(struct Sprite* sprite)','InitSpritePosToGivenTarget(sprite, target);','sprite->pos1.x = GetBattlerSpriteCoord2(target, BATTLER_COORD_X);','sprite->pos1.y = GetBattlerSpriteCoord2(target, BATTLER_COORD_Y);'],
  'pret-battle_anim.c':['sScriptCmdTable[sBattleAnimScriptPtr[0]]();','gBattleAnimArgs[i] = T1_READ_16(sBattleAnimScriptPtr);','taskId = CreateTask(taskFunc, taskPriority);','taskFunc(taskId);','CreateSpriteAndAnimate('],
  'pret-sprite.c':['sprite->callback = template->callback;','gSprites[i].callback(sprite);'],
  'BPRJ.ld':['CreateSpriteAndAnimate = 0x8006D68 | 1;']}
 for name,tokens in roles.items():
  text=sources[name].decode()
  for token in tokens:need(token in text,'公開source意味 '+token)
 return True

def fixed_windows():
 parts={}
 for i in INS.values():parts[i.address]=encoded(i)
 for a,value in WORDS.items():
  need(a not in parts,'literalとcode非重複');parts[a]=value.to_bytes(4,'little')
 rows=[];start=None;end=None;data=b''
 for a,b in sorted(parts.items()):
  need(end is None or a>=end,'保護byte非重複')
  if end!=a:
   if start is not None:rows.append(dict(address=start,**identity(data)))
   start=a;data=b''
  data+=b;end=a+len(b)
 if start is not None:rows.append(dict(address=start,**identity(data)))
 rows += copy.deepcopy(SPRITE_DATA)
 rows += [dict(address=a,size=n,sha256=WINDOW_IDENTITIES[a])for a,n in REQUIRED_WINDOWS.items()]
 return sorted(rows,key=lambda w:(w['address'],w['size']))
FIXED_WINDOWS=fixed_windows()
SERIALIZER_LAYOUT=[dict(label=label,address=a,command_count=count,size=n,extent=extent)for label,a,count,n,extent in BLOCKS]

def bind_semantics(raw,sources):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'独立完全命令 '+hex(i.address))
 for a,v in WORDS.items():need(d.u32(raw,a)==v,'完全literal/dispatch登録field '+hex(a))
 encoded_chunks,rows=serialize_animation_sources(sources)
 for a,b in encoded_chunks.items():need(chunk(raw,a,len(b))==b,'全source serializer field '+hex(a))
 need(chunk(raw,0x08370AC0,8)==encode_oam(sources),'独立OAM全bitfield serializer')
 d.signed(raw,FIXED_WINDOWS)
 return dict(status='PASS_COMPLETE_SOURCE_SERIALIZATION',blocks=rows,source_numeric_or_equ_fields=sum(f['derivation']!='actual_registered_pointer_field'for r in rows for c in r['commands']for f in c['fields']),actual_registered_pointer_fields=len(REGISTERED_POINTER_FIELDS),complete_field_count=sum(len(c['fields'])for r in rows for c in r['commands']),complete_serialized_bytes=sum(n for _,_,_,n,_ in BLOCKS),public_table_index_translation_used=False,actual_registration_indices=[i for i,_,_ in ACTUAL_REGISTRATIONS],prior_commands_runtime_success_proven=False)

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'二つの最小型hitだけ')
 root=next(r for r in ROOTS.values()if r['hit']==hit)
 instructions=[INS[root['stop']],INS[root['static_successor']]]
 need([i.size for i in instructions]==[4,2]and instructions[0].kind=='call'and instructions[1].kind=='literal','完全BLと静的successor LDR')
 return dict(root=copy.deepcopy(root),root_verified=True,classified_window=dict(address=hit-1,size=6),complete_instructions=[dict(address=i.address,size=i.size,kind=i.kind,args=list(i.args),sha256=identity(encoded(i))['sha256'])for i in instructions],serializer_layout=copy.deepcopy(SERIALIZER_LAYOUT),input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
 hit=evidence.get('root',{}).get('hit')
 need(type(hit)is int and hit in HITS and exact(evidence,evidence_template(hit)),'全witness field完全一致')
 return hit-1,6

def protected_windows(review):
 need(exact(review['windows'],FIXED_WINDOWS),'固定新scope保護窓')
 return copy.deepcopy(FIXED_WINDOWS)

def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS),'固定親unknown2件全field')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),roots=copy.deepcopy(ROOTS),windows=copy.deepcopy(FIXED_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE),serializer_layout=copy.deepcopy(SERIALIZER_LAYOUT))

def _regions(raw,inherited,review,sources):
 need(type(review)is dict and set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','roots','windows','claims','input_contract','finite_profile','serializer_layout'},'閉じたreview schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'厳密schema版')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'current/diagnostic分離')
 for key,value in(('roots',ROOTS),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE),('serializer_layout',SERIALIZER_LAYOUT)):
  need(exact(review[key],value),'review全field '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(len(selected)==2 and [h['address']for h in selected]==list(HITS)and exact(selected,review['hits'])and exact(selected,EXPECTED_HITS),'元unknown全field')
 for h in selected:
  need(h['accepted']is False and h['classification']=='UNCLASSIFIED'and h['owner_candidates']==[]and type(h['size'])is int and h['size']==4 and h['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','元unknown完全4byte')
  d.signed(raw,h)
 protected_windows(review);sources_bind(review,sources);serialization=bind_semantics(raw,sources);composition=compose_selected(raw)
 regions=[]
 for hit in HITS:
  e=evidence_template(hit);a,n=witness_geometry(e);regions.append(d.TypedRegion(a,a+n,KIND,e))
 return regions,dict(status='PASS_REGISTERED_ANIMATION_MINIMUMS',count=2,hits=list(HITS),serialization=serialization,composition=composition,protected_windows=len(FIXED_WINDOWS),protected_bytes=sum(w['size']for w in FIXED_WINDOWS),**copy.deepcopy(CLAIMS))

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate')
 return _regions(raw,inherited,review,sources)
