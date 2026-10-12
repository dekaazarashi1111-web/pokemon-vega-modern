"""登録2根の別message/標準2/ENDを束縛し、未接続placeholder境界を未知維持。外部I/Oなし。"""
import copy, hashlib, json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_runtime_party as rt
need, identity, chunk = d.need, d.identity, d.chunk
exact, encoded = engine.exact, engine.encoded
CANDIDATE, DIAGNOSTIC = party.CANDIDATE, party.DIAGNOSTIC
HITS = HELD_HITS = (0x0818DD5D,)
CLASSIFIED_HITS = ()
KIND = 'held_event_placeholder_unbound_roots'
TYPE_CATEGORY = 'guard'
CTX = 0x02000010
STANDARD2 = 0x08192D90
DISPATCH = 0x08069118
SOURCE_IDS = {'pret-std_msgbox.inc': {'local': 'pret-std_msgbox.inc',
                         'repository': 'pret/pokefirered',
                         'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                         'path': 'data/scripts/std_msgbox.inc',
                         'size': 1040,
                         'sha256': '090541cfc3a47272ea8203f0f6c18f19f8062d407388a23fcf103e93b196b431',
                         'git_blob_sha': '18ad553c85b66975e0c05763c6145082c8c13dde'},
 'pret-script.c': {'local': 'pret-script.c',
                   'repository': 'pret/pokefirered',
                   'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'path': 'src/script.c',
                   'size': 13713,
                   'sha256': '1cc4aade1f821e5f218ba7c191b1217e5a3cf942d0bfd0f32f775ce1f808437c',
                   'git_blob_sha': 'd0433bdda062b138e53d1a1d3184b4566ad7d9dc'},
 'pret-event_scripts.s': {'local': 'pret-event_scripts.s',
                          'repository': 'pret/pokefirered',
                          'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                          'path': 'data/event_scripts.s',
                          'size': 55643,
                          'sha256': '3b1bd10d26c0a74fb3452ab42fc9d14dfca785f8b71389db06c71f5dfdd50a27',
                          'git_blob_sha': '88d75946a7300ccf952f4a36c283966c6aebf5c0'},
 'pret-string_util.c': {'local': 'pret-string_util.c',
                        'repository': 'pret/pokefirered',
                        'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                        'path': 'src/string_util.c',
                        'size': 14320,
                        'sha256': 'ed9519d4eaf51ed660a522915366dc0ebf2916d592a91a1d7fc2a012e4f3f17e',
                        'git_blob_sha': '5c26d151a61274caac3a16c3b9c4eb73bf9a9e26'},
 'pret-characters.h': {'local': 'pret-characters.h',
                       'repository': 'pret/pokefirered',
                       'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                       'path': 'include/characters.h',
                       'size': 12798,
                       'sha256': '6787db76f83c4f8426c5adbfa7aa061c46585db9522f1fef00ad888616199b98',
                       'git_blob_sha': 'd00ecf0a3afcd9fc1fa9534c00f4b74793d5f06f'},
 'pret-scrcmd.c': {'local': 'pret-scrcmd.c',
                   'repository': 'pret/pokefirered',
                   'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'path': 'src/scrcmd.c',
                   'size': 56954,
                   'sha256': '898dad5a07ce0a125731b998654d86808885a8d48163d607478a5e70c1cac553',
                   'git_blob_sha': '97b695ee2f6fca80a3b78f52f6a444f696fe5814'},
 'BPRJ.ld': {'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'path': 'BPRJ.ld',
             'size': 68505,
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51'}}
ROOTS = [{'owner_id': 'OBJECT:3/10:0',
  'group': 3,
  'map': 10,
  'object': 0,
  'script': {'address': 135845930,
             'size': 9,
             'sha256': 'b1dab50abd98df4414ff33a4d0e27c3f9093728d50f81933f4221886a405541e'},
  'root_chain': [{'address': 134564620,
                  'size': 4,
                  'sha256': 'd672c5b39141ec15b78c62a82995e610593e06bd92fe2cb5aa5434696139c61e',
                  'role': 'map_groups_literal',
                  'value': 153899412},
                 {'address': 153899424,
                  'size': 4,
                  'sha256': '3e4115335b5bb8ce7241718cc2f21a58680b6254a105ff93bb7a8d8837aad1a1',
                  'role': 'group_slot',
                  'value': 137454500},
                 {'address': 137454540,
                  'size': 4,
                  'sha256': 'c3f6a2b8f2c4e974dbdf164787de192cb1bb676b20dc27cf71c6a88cc5f8b318',
                  'role': 'map_slot',
                  'value': 137447392},
                 {'address': 137447392,
                  'size': 8,
                  'sha256': '6726e5ea9c021e1ff492c0c16b12778b1d9b062119a90b41c0575d5c685d6d3c',
                  'role': 'map_header',
                  'events': 155155364},
                 {'address': 155155364,
                  'size': 8,
                  'sha256': '0ca556b3d8169c1e3f4f1df8b0c449f55defb20aa84bfa9cc207b953cbdcfba5',
                  'role': 'event_header',
                  'objects': 155154368},
                 {'address': 155154368,
                  'size': 24,
                  'sha256': 'c688d3ccb33104f99517ae73239cbbfb24d5a3a53b7cf8a9a6810da64eef9af0',
                  'role': 'object_record',
                  'script': 135845930,
                  'script_field': 155154384}],
  'text_pointer': 141172340,
  'standard_index': 2,
  'end_address': 135845938},
 {'owner_id': 'OBJECT:23/0:0',
  'group': 23,
  'map': 0,
  'object': 0,
  'script': {'address': 135845874,
             'size': 9,
             'sha256': '1c74068c33fe8c4cdc368be268ef5c9a35381c6523bfbefb4eb1e99c8438a396'},
  'root_chain': [{'address': 134564620,
                  'size': 4,
                  'sha256': 'd672c5b39141ec15b78c62a82995e610593e06bd92fe2cb5aa5434696139c61e',
                  'role': 'map_groups_literal',
                  'value': 153899412},
                 {'address': 153899504,
                  'size': 4,
                  'sha256': 'a4aadd2ad8ff1bea71bfdd435131adb2011173d29274658e84318109a2313bd2',
                  'role': 'group_slot',
                  'value': 137455196},
                 {'address': 137455196,
                  'size': 4,
                  'sha256': '9229c0b88678685244254e763ba5a114c363ac5a92b4faa5c84e5181edbdb165',
                  'role': 'map_slot',
                  'value': 137451984},
                 {'address': 137451984,
                  'size': 8,
                  'sha256': 'cc1b4d7ca6eed98c1ab28e3a7ef26b6abe22d7b4cff90dfebd9579b5d116ec40',
                  'role': 'map_header',
                  'events': 137894596},
                 {'address': 137894596,
                  'size': 8,
                  'sha256': '05e7ee83c0c26861fb5d37033a419d5a366349dedcf901341a291f006084f10c',
                  'role': 'event_header',
                  'objects': 137894532},
                 {'address': 137894532,
                  'size': 24,
                  'sha256': 'df21e3922351a1eea5b3aecb0efa06fc808b0cf604e03768e2e93e5c780dec27',
                  'role': 'object_record',
                  'script': 135845874,
                  'script_field': 137894548}],
  'text_pointer': 141172985,
  'standard_index': 2,
  'end_address': 135845882}]
TEXTS = [{'address': 135847204,
  'size': 60,
  'sha256': '62016c7e8fe39a33cb73f1fadd4a82a252d6ddd903c7d9cca9c6a4006ac11b36',
  'loadword_and_callstd': {'address': 135846705,
                           'size': 8,
                           'sha256': '421c43a67bf59a18d234bc122c6a4c66569d146e60085a6c2243b1d9b8778c7b',
                           'pointer': 135847204},
  'placeholder_offsets': [8]},
 {'address': 135847264,
  'size': 20,
  'sha256': '6ed0fcc70c1d88c5d44829620af9f2f4f525fb1495fa16870d2ff024255bb11d',
  'loadword_and_callstd': {'address': 135846736,
                           'size': 8,
                           'sha256': 'd18098111322ba655a21223ffbe163a50f7db22a73d827d4f6277d70e8728b61',
                           'pointer': 135847264},
  'placeholder_offsets': []}]
FIXED_WINDOWS = [{'address': 134564620, 'size': 4, 'sha256': 'd672c5b39141ec15b78c62a82995e610593e06bd92fe2cb5aa5434696139c61e'},
 {'address': 134647916, 'size': 58, 'sha256': '57fcbf4f792dfa30088f1d3753300eac4042bd545395b5e587b1acac5834ffba'},
 {'address': 134647976, 'size': 10, 'sha256': '8db31238fb6265cfa04f9be46b7ef134e68c38c3e7ed68c633ea30e42082ce1f'},
 {'address': 134647996, 'size': 8, 'sha256': 'bce16350e4c52dab581fe17c41f6632394764f9d7c18dc2412efcd39c1eb1749'},
 {'address': 134648088, 'size': 26, 'sha256': 'c23e12489eeb9a5ddc85d4216365fb60541ae3b9d43eb3181fe4fa0b7ca84ace'},
 {'address': 134648132, 'size': 74, 'sha256': '1cdca0fffa658d773652ac131036f64a31451b7c26cf790d272fe249bc8ce968'},
 {'address': 134648212, 'size': 36, 'sha256': '543edfb2cdca6e3d0eccae98577fa101cd1d6d484c4ed169ca175df37b2c0958'},
 {'address': 134648272, 'size': 48, 'sha256': '1d6f67baf6aff67172ec8c2580bdd5ab743a7224f461ff4e68431c1d9e105f2c'},
 {'address': 134648796, 'size': 8, 'sha256': '1a7270f8c3d75390c0acd8169220e2342ae02bb3bd5a67ce43085a2e8cd3b8b1'},
 {'address': 134649752, 'size': 12, 'sha256': '9a47103abf0365186c3b4c23e5190a921fc2033044242427672b25163af3f10f'},
 {'address': 134649992, 'size': 12, 'sha256': 'a4c7e59ae583466f83dc3a7b6daf913b26bb3096e77f19138290db0f0e725059'},
 {'address': 134650432, 'size': 38, 'sha256': 'a56ab43f56bba187706c31510aa5bd742c77459127cba73001da353919fc3841'},
 {'address': 134650472, 'size': 8, 'sha256': 'b4cdb095c5a7cbb104afc8e9e7acb6439f60636ff45687974cb51b720f0ad173'},
 {'address': 134650740, 'size': 34, 'sha256': '6632a06bebc6c051ba0f1d400cb47767a9237d0bd2dcee6a9023e04b2a227b61'},
 {'address': 135670988, 'size': 8, 'sha256': 'b6f1e69db796dcd7bf5e8f7ca7ddf66306cce52aa2c3460bcc9cf4d05197e1b9'},
 {'address': 135671016, 'size': 4, 'sha256': '25dd52f3be6308884dd9180d47a4ca1860449f2bd0827e3b52dd0541da6c8476'},
 {'address': 135671040, 'size': 4, 'sha256': '589e15f487c95a94b42e75dd09c3ea3952ed1ad18639243d8b79d3f81e599983'},
 {'address': 135673696, 'size': 4, 'sha256': 'eb2c9a4a236009aa968b05ca580b3779b1a5a8473b8ce1388624780ac8edada6'},
 {'address': 135845874, 'size': 9, 'sha256': '1c74068c33fe8c4cdc368be268ef5c9a35381c6523bfbefb4eb1e99c8438a396'},
 {'address': 135845930, 'size': 9, 'sha256': 'b1dab50abd98df4414ff33a4d0e27c3f9093728d50f81933f4221886a405541e'},
 {'address': 135846705, 'size': 8, 'sha256': '421c43a67bf59a18d234bc122c6a4c66569d146e60085a6c2243b1d9b8778c7b'},
 {'address': 135846736, 'size': 8, 'sha256': 'd18098111322ba655a21223ffbe163a50f7db22a73d827d4f6277d70e8728b61'},
 {'address': 135847204, 'size': 80, 'sha256': '944fbb868b87a65f00c4a22f0e27dbeb9eb0e42696c94cb81adf4d3ff2d6a41a'},
 {'address': 135867792, 'size': 11, 'sha256': '57beef7c67d2c2c3781ab6550f370524b454d0f8d027830ac0b812bed0184256'},
 {'address': 136084172, 'size': 2, 'sha256': 'bac8ca6ee9f77b46c7ab5824c7c59d99fd0ca53ae998ea2872b78bb6a5189cc5'},
 {'address': 137447392, 'size': 8, 'sha256': '6726e5ea9c021e1ff492c0c16b12778b1d9b062119a90b41c0575d5c685d6d3c'},
 {'address': 137451984, 'size': 8, 'sha256': 'cc1b4d7ca6eed98c1ab28e3a7ef26b6abe22d7b4cff90dfebd9579b5d116ec40'},
 {'address': 137454540, 'size': 4, 'sha256': 'c3f6a2b8f2c4e974dbdf164787de192cb1bb676b20dc27cf71c6a88cc5f8b318'},
 {'address': 137455196, 'size': 4, 'sha256': '9229c0b88678685244254e763ba5a114c363ac5a92b4faa5c84e5181edbdb165'},
 {'address': 137894532, 'size': 24, 'sha256': 'df21e3922351a1eea5b3aecb0efa06fc808b0cf604e03768e2e93e5c780dec27'},
 {'address': 137894596, 'size': 8, 'sha256': '05e7ee83c0c26861fb5d37033a419d5a366349dedcf901341a291f006084f10c'},
 {'address': 153899424, 'size': 4, 'sha256': '3e4115335b5bb8ce7241718cc2f21a58680b6254a105ff93bb7a8d8837aad1a1'},
 {'address': 153899504, 'size': 4, 'sha256': 'a4aadd2ad8ff1bea71bfdd435131adb2011173d29274658e84318109a2313bd2'},
 {'address': 155154368, 'size': 24, 'sha256': 'c688d3ccb33104f99517ae73239cbbfb24d5a3a53b7cf8a9a6810da64eef9af0'},
 {'address': 155155364, 'size': 8, 'sha256': '0ca556b3d8169c1e3f4f1df8b0c449f55defb20aa84bfa9cc207b953cbdcfba5'}]
LITERALS = {134650472: 135673688,
 134650476: 135673728,
 134648796: 135670980,
 134648800: 135671824,
 135670988: 134649753,
 135670992: 134649993,
 135671040: 134650741,
 135671016: 134650433,
 135673696: 135867792}
SPECS = [(134647916, 'push', (0, True)),
 (134647918, 'addi', (3, 0, 0)),
 (134647920, 'imm', ('mov', 0, 0)),
 (134647922, 'mem', (False, 'byte', 0, 3, 1)),
 (134647924, 'mem', (False, 'word', 0, 3, 8)),
 (134647926, 'mem', (False, 'byte', 0, 3, 0)),
 (134647928, 'mem', (False, 'word', 0, 3, 4)),
 (134647930, 'mem', (False, 'word', 1, 3, 92)),
 (134647932, 'mem', (False, 'word', 2, 3, 96)),
 (134647934, 'imm', ('mov', 2, 0)),
 (134647936, 'imm', ('mov', 1, 3)),
 (134647938, 'addi', (0, 3, 0)),
 (134647940, 'imm', ('add', 0, 112)),
 (134647942, 'mem', (False, 'word', 2, 0, 0)),
 (134647944, 'imm', ('sub', 0, 4)),
 (134647946, 'imm', ('sub', 1, 1)),
 (134647948, 'imm', ('cmp', 1, 0)),
 (134647950, 'branch', (10, 134647942)),
 (134647952, 'addi', (1, 3, 0)),
 (134647954, 'imm', ('add', 1, 12)),
 (134647956, 'imm', ('mov', 2, 0)),
 (134647958, 'addi', (0, 3, 0)),
 (134647960, 'imm', ('add', 0, 88)),
 (134647962, 'mem', (False, 'word', 2, 0, 0)),
 (134647964, 'imm', ('sub', 0, 4)),
 (134647966, 'compare', (0, 1)),
 (134647968, 'branch', (10, 134647962)),
 (134647970, 'pop', (1, False)),
 (134647972, 'bx', (0,)),
 (134647976, 'mem', (False, 'word', 1, 0, 8)),
 (134647978, 'imm', ('mov', 1, 1)),
 (134647980, 'mem', (False, 'byte', 1, 0, 1)),
 (134647982, 'imm', ('mov', 0, 1)),
 (134647984, 'bx', (14,)),
 (134648088, 'mem', (True, 'byte', 1, 2, 0)),
 (134648090, 'addi', (0, 2, 1)),
 (134648092, 'mem', (False, 'word', 0, 4, 8)),
 (134648094, 'shift', ('lsl', 1, 1, 2)),
 (134648096, 'mem', (True, 'word', 0, 4, 92)),
 (134648098, 'add', (1, 0, 1)),
 (134648100, 'mem', (True, 'word', 0, 4, 96)),
 (134648102, 'compare', (1, 0)),
 (134648104, 'branch', (2, 134648056)),
 (134648106, 'mem', (True, 'word', 1, 1, 0)),
 (134648108, 'addi', (0, 4, 0)),
 (134648110, 'call', (136084172,)),
 (136084172, 'bx', (1,)),
 (134650740, 'push', (48, True)),
 (134650742, 'addi', (4, 0, 0)),
 (134650744, 'mem', (True, 'word', 0, 4, 8)),
 (134650746, 'mem', (True, 'byte', 5, 0, 0)),
 (134650748, 'imm', ('add', 0, 1)),
 (134650750, 'mem', (False, 'word', 0, 4, 8)),
 (134650752, 'addi', (0, 4, 0)),
 (134650754, 'call', (134648272,)),
 (134650758, 'shift', ('lsl', 5, 5, 2)),
 (134650760, 'imm', ('add', 4, 100)),
 (134650762, 'add', (4, 4, 5)),
 (134650764, 'mem', (False, 'word', 0, 4, 0)),
 (134650766, 'imm', ('mov', 0, 0)),
 (134650768, 'pop', (48, False)),
 (134650770, 'pop', (2, False)),
 (134650772, 'bx', (1,)),
 (134648272, 'push', (112, True)),
 (134648274, 'addi', (3, 0, 0)),
 (134648276, 'mem', (True, 'word', 0, 3, 8)),
 (134648278, 'mem', (True, 'byte', 6, 0, 0)),
 (134648280, 'imm', ('add', 0, 1)),
 (134648282, 'mem', (False, 'word', 0, 3, 8)),
 (134648284, 'mem', (True, 'byte', 5, 0, 0)),
 (134648286, 'addi', (2, 0, 1)),
 (134648288, 'mem', (False, 'word', 2, 3, 8)),
 (134648290, 'mem', (True, 'byte', 4, 0, 1)),
 (134648292, 'addi', (1, 2, 1)),
 (134648294, 'mem', (False, 'word', 1, 3, 8)),
 (134648296, 'mem', (True, 'byte', 0, 2, 1)),
 (134648298, 'imm', ('add', 1, 1)),
 (134648300, 'mem', (False, 'word', 1, 3, 8)),
 (134648302, 'shift', ('lsl', 0, 0, 8)),
 (134648304, 'add', (0, 0, 4)),
 (134648306, 'shift', ('lsl', 0, 0, 8)),
 (134648308, 'add', (0, 0, 5)),
 (134648310, 'shift', ('lsl', 0, 0, 8)),
 (134648312, 'add', (0, 0, 6)),
 (134648314, 'pop', (112, False)),
 (134648316, 'pop', (2, False)),
 (134648318, 'bx', (1,)),
 (134650432, 'push', (0, True)),
 (134650434, 'addi', (2, 0, 0)),
 (134650436, 'mem', (True, 'word', 0, 2, 8)),
 (134650438, 'mem', (True, 'byte', 1, 0, 0)),
 (134650440, 'imm', ('add', 0, 1)),
 (134650442, 'mem', (False, 'word', 0, 2, 8)),
 (134650444, 'shift', ('lsl', 1, 1, 2)),
 (134650446, 'literal', (0, 134650472)),
 (134650448, 'add', (1, 1, 0)),
 (134650450, 'literal', (0, 134650476)),
 (134650452, 'compare', (1, 0)),
 (134650454, 'branch', (2, 134650464)),
 (134650456, 'mem', (True, 'word', 1, 1, 0)),
 (134650458, 'addi', (0, 2, 0)),
 (134650460, 'call', (134648212,)),
 (134650464, 'imm', ('mov', 0, 0)),
 (134650466, 'pop', (2, False)),
 (134650468, 'bx', (1,)),
 (134648212, 'push', (48, True)),
 (134648214, 'addi', (4, 0, 0)),
 (134648216, 'addi', (5, 1, 0)),
 (134648218, 'mem', (True, 'word', 1, 4, 8)),
 (134648220, 'call', (134648132,)),
 (134648224, 'mem', (False, 'word', 5, 4, 8)),
 (134648226, 'pop', (48, False)),
 (134648228, 'pop', (1, False)),
 (134648230, 'bx', (0,)),
 (134648132, 'push', (0, True)),
 (134648134, 'addi', (2, 0, 0)),
 (134648136, 'addi', (3, 1, 0)),
 (134648138, 'mem', (True, 'byte', 1, 2, 0)),
 (134648140, 'addi', (0, 1, 1)),
 (134648142, 'imm', ('cmp', 0, 19)),
 (134648144, 'branch', (12, 134648166)),
 (134648146, 'shift', ('lsl', 0, 1, 2)),
 (134648148, 'addi', (1, 2, 0)),
 (134648150, 'imm', ('add', 1, 12)),
 (134648152, 'add', (1, 1, 0)),
 (134648154, 'mem', (False, 'word', 3, 1, 0)),
 (134648156, 'mem', (True, 'byte', 0, 2, 0)),
 (134648158, 'imm', ('add', 0, 1)),
 (134648160, 'mem', (False, 'byte', 0, 2, 0)),
 (134648162, 'imm', ('mov', 0, 0)),
 (134648164, 'jump', (134648168,)),
 (134648166, 'imm', ('mov', 0, 1)),
 (134648168, 'pop', (2, False)),
 (134648170, 'bx', (1,)),
 (134647996, 'imm', ('mov', 1, 0)),
 (134647998, 'mem', (False, 'byte', 1, 0, 1)),
 (134648000, 'mem', (False, 'word', 1, 0, 8)),
 (134648002, 'bx', (14,)),
 (134649752, 'push', (0, True)),
 (134649754, 'call', (134647996,)),
 (134649758, 'imm', ('mov', 0, 0)),
 (134649760, 'pop', (2, False)),
 (134649762, 'bx', (1,)),
 (134649992, 'push', (0, True)),
 (134649994, 'call', (134648232,)),
 (134649998, 'imm', ('mov', 0, 0)),
 (134650000, 'pop', (2, False)),
 (134650002, 'bx', (1,)),
 (134648232, 'push', (16, True)),
 (134648234, 'addi', (4, 0, 0)),
 (134648236, 'call', (134648172,)),
 (134648240, 'mem', (False, 'word', 0, 4, 8)),
 (134648242, 'pop', (16, False)),
 (134648244, 'pop', (1, False)),
 (134648246, 'bx', (0,)),
 (134648172, 'push', (0, True)),
 (134648174, 'addi', (2, 0, 0)),
 (134648176, 'mem', (True, 'byte', 0, 2, 0)),
 (134648178, 'imm', ('cmp', 0, 0)),
 (134648180, 'branch', (0, 134648200)),
 (134648182, 'imm', ('sub', 0, 1)),
 (134648184, 'mem', (False, 'byte', 0, 2, 0)),
 (134648186, 'mem', (True, 'byte', 1, 2, 0)),
 (134648188, 'shift', ('lsl', 1, 1, 2)),
 (134648190, 'addi', (0, 2, 0)),
 (134648192, 'imm', ('add', 0, 12)),
 (134648194, 'add', (0, 0, 1)),
 (134648196, 'mem', (True, 'word', 0, 0, 0)),
 (134648198, 'jump', (134648202,)),
 (134648200, 'imm', ('mov', 0, 0)),
 (134648202, 'pop', (2, False)),
 (134648204, 'bx', (1,))]
INS = {a: party.Ins(a, kind, args) for a, kind, args in SPECS}
BLOCKS = {'registered_event_prefix_and_conditional_terminals': tuple(INS.values())}
WINDOWS = {f'event_placeholder_window_{j}': (r['address'], r['size']) for j, r in enumerate(FIXED_WINDOWS)}
ROOT = dict(kind='two_current_object_roots_end_after_other_message',
            registration_scope='only_OBJECT_3_10_0_and_OBJECT_23_0_0',
            map_literal=0x08054B0C, dispatch=DISPATCH, standard2=STANDARD2,
            standard2_slot=0x08163760, end_handler=0x08069798,
            return_handler=0x08069888, stop_script=0x080690BC)
PLACEHOLDER = dict(text=0x0818DD24, offset=8, id=3,
                   source_meaning='gStringVar2', public_jp_symbol=0x02021C60,
                   source_role='public_semantic_only_not_actual_branch_or_source_extent_proof',
                   actual_branch_bound=False, replacement_extent_bound=False,
                   replacement_eos_bound=False, replacement_producer_bound=False,
                   replacement_source_byte_consumer_executed=False)
CLAIMS = dict(proof_scope='two_registered_roots_and_conditional_terminal_probes_only',
              registration_bound=True, structural_prefix_only=True,
              registered_loadword_callstd_prefix_machine_executed=True,
              standard2_handler_runtime_effects_proven=False,
              conditional_return_probe_requires_standard2_completion_and_stack_preservation=True,
              conditional_return_and_end_machine_executed=True,
              selected_target_root_paths_bound=False, selected_target_consumer_executed=False,
              placeholder_branch_and_replacement_source_bound=False,
              all_roots_unreachable_claimed=False, whole_script_unreachable_claimed=False,
              full_story_reachability_claimed=False, actual_runtime_execution_observed=False,
              opaque_callee_effects_proven=False, universal_heap_or_irq_lifetime_proven=False,
              source_pointer_interpretation=False, whole_text_classified=False,
              indirect_reference_completeness_claimed=False, donor_eligible=False, donor_leased=False)
CONTRACT = dict(
    entry='現map登録2根だけを束縛。登録集合の完全性や自然object選択を証明しない。',
    prefix='実InitScriptContext/SetupScriptから各登録rootを渡し、実dispatcher/LOADWORD0/CALLSTD2を実行する。text pointerやstack return PCをhost注入しない。',
    standard='標準2の11byteを独立script encoderで束縛。lock/faceplayer/message(NULL)/waitmessage/waitbuttonpress/release/returnの構造だけを検査し、これらhandlerのruntime効果は実行しない。',
    terminal='標準2が完了してcontextとcall stackを保つという条件付きで、同prefixのstackを使って実return handlerを直接probeする。ENDは戻されたPCから実dispatcher経由で実行し、mode0/scriptPtr0を実storeする。標準2の自然完了を仮定から証明へ昇格しない。',
    boundary='左右LOADWORD0/CALLSTD4、60/20byteのEOS境界、左FD03は局所観測に限る。登録根からのpath、置換元producer/extent/EOS/実source-byte consumerは未完。Summary dynamic placeholderで代用しない。',
    memory='明示contextと実stackはaligned/disjoint/liveの有限条件。標準2中の副作用、IRQ、allocator、普遍lifetimeは証明しない。',
    minimum='型領域0、hit0x0818DD5Dは全fieldを未知のまま保持。保護窓は証拠でありdonor容量ではない。')
OBLIGATIONS = [
    '両対象LOADWORDへ接続する別の現登録rootと完全な有限script path。候補2根の近傍だけでは代用しない。',
    '左FD03の現GetExpandedPlaceholder分岐、gStringVar2生成元、有限置換元extent/EOS、実source-byte consumer。',
    'valid suffix contextを自然到達・special/flag効果と区別し、左右の完全消費が閉じるまで4byteも分類しない。',
    '全root不達・間接参照完全性・未使用・退役・owner移管・普遍lifetimeは別義務。']


def script_encoded(name, *args):
    """公開command grammarから独立直列化。観測byte列からの逆コピーではない。"""
    if name == 'loadword':
        index, pointer = args
        need(type(index) is int and 0 <= index < 4 and type(pointer) is int and 0x08000000 <= pointer < 0x0A000000, 'LOADWORD型operand')
        return bytes((15, index)) + pointer.to_bytes(4, 'little')
    if name == 'callstd':
        need(len(args) == 1 and type(args[0]) is int and 0 <= args[0] < 10, '標準script有効index')
        return bytes((9, args[0]))
    if name == 'message':
        need(args == (0,), '標準2はdata0を使うNULL message')
        return bytes((103,)) + (0).to_bytes(4, 'little')
    opcodes = {'end': 2, 'return': 3, 'lock': 106, 'faceplayer': 90,
               'waitmessage': 102, 'waitbuttonpress': 109, 'release': 108}
    need(name in opcodes and not args, '閉じた無operand命令')
    return bytes((opcodes[name],))


def standard2_encoded():
    return b''.join(script_encoded(name, *args) for name, args in
                    [('lock', ()), ('faceplayer', ()), ('message', (0,)),
                     ('waitmessage', ()), ('waitbuttonpress', ()), ('release', ()), ('return', ())])


def root_registration(raw, root):
    need(any(exact(root, r) for r in ROOTS), '選択2登録根だけ')
    chain = root['root_chain']; d.signed(raw, chain)
    groups, group, maprow, header, events, obj = chain
    need([r['role'] for r in chain] == ['map_groups_literal', 'group_slot', 'map_slot', 'map_header', 'event_header', 'object_record'], '登録field順序')
    for row in (groups, group, maprow):
        need(row['size'] == 4 and d.u32(raw, row['address']) == row['value'], '現root pointer実値')
    need(groups['address'] == 0x08054B0C and group['address'] == groups['value'] + root['group'] * 4 and maprow['address'] == group['value'] + root['map'] * 4 and header['address'] == maprow['value'], 'map登録pointer連鎖')
    need(header['size'] == 8 and d.u32(raw, header['address'] + 4) == header['events'] == events['address'] and events['size'] == 8 and d.u32(raw, events['address'] + 4) == events['objects'], '現events pointer連鎖')
    need(chunk(raw, events['address'], 1)[0] > root['object'] and obj['size'] == 24 and obj['address'] == events['objects'] + root['object'] * 24 and obj['script_field'] == obj['address'] + 16 and d.u32(raw, obj['script_field']) == obj['script'] == root['script']['address'], '24byte objectと実script field')
    return dict(owner_id=root['owner_id'], script=root['script']['address'], registration_bound=True)


def bind_semantics(raw):
    d.signed(raw, FIXED_WINDOWS)
    for ins in INS.values():
        need(chunk(raw, ins.address, ins.size) == encoded(ins), '独立Thumb encoderと実命令一致 ' + hex(ins.address))
    for address, value in LITERALS.items():
        need(d.u32(raw, address) == value, '実literal/dispatch/standard slot一致')
    for op, entry in ((2, 0x08069798), (3, 0x08069888), (9, 0x08069A40), (15, 0x08069B74)):
        need(d.u32(raw, 0x08162CC4 + 4 * op) == entry | 1, '現JP handler dispatch')
    need(d.u32(raw, 0x08163760) == STANDARD2 and chunk(raw, STANDARD2, 11) == standard2_encoded(), '現標準2の完全な分岐無しscript')
    for root in ROOTS:
        root_registration(raw, root)
        expect = script_encoded('loadword', 0, root['text_pointer']) + script_encoded('callstd', 2) + script_encoded('end')
        need(chunk(raw, root['script']['address'], 9) == expect and root['end_address'] == root['script']['address'] + 8, '登録scriptは別text LOADWORD0/標準2/END')
        need(root['text_pointer'] not in [t['address'] for t in TEXTS], '対象左右textをloadしない')
    for text in TEXTS:
        call = text['loadword_and_callstd']
        need(chunk(raw, call['address'], 8) == script_encoded('loadword', 0, text['address']) + script_encoded('callstd', 4), '対象は別の未接続LOADWORD0/標準4')
        b = chunk(raw, text['address'], text['size'])
        need(b[-1] == 255 and 255 not in b[:-1] and 248 not in b and 249 not in b and 252 not in b, '局所候補の有限EOS境界')
        need([j for j, value in enumerate(b) if value == 253] == text['placeholder_offsets'], '左placeholder位置だけを観測')
    need(chunk(raw, 0x0818DD2C, 2) == bytes((253, 3)), '左FD03、別dynamic placeholderで代用しない')
    need(TEXTS[0]['address'] + TEXTS[0]['size'] == TEXTS[1]['address'] == HITS[0] + 3, '左末尾3byte/右先頭1byte、型消費は未証明')


class Machine(rt.Machine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.visited = []; self.rom_reads = []
    def read(self, address, size):
        value = super().read(address, size)
        if 0x08000000 <= address < 0x0A000000:
            self.rom_reads.append((address, size))
        return value
    def step(self, *args, **kwargs):
        self.visited.append(self.pc); return super().step(*args, **kwargs)


def compose_selected(raw, root, initial_fields=None, standard2_completed=True):
    """登録prefix実行＋条件付きreturn/END probe。標準2のopaque handlerは実行しない。"""
    need(initial_fields is None, 'context/text/return PC直接seedを拒否')
    need(standard2_completed is True, 'terminal probeの明示条件、自然完了の証拠ではない')
    bind_semantics(raw); root_registration(raw, root)
    memory = {}; visited = []; reads = []; writes = []
    def run(entry, registers, stop=0xFFFFFFF0):
        nonlocal memory
        m = Machine(raw, entry, registers, memory, instructions=INS)
        while m.pc != stop:
            need(m.pc in INS, '閉じた実prefix/helper以外のcalleeを禁止'); m.step()
        need(m.reg[13] == 0x03007000, '各実probeのstack均衡')
        memory = m.mem; visited.extend(m.visited); reads.extend(m.rom_reads); writes.extend(m.writes)
        return m
    run(0x0806906C, {0: CTX, 1: d.u32(raw, 0x080693DC), 2: d.u32(raw, 0x080693E0)})
    run(0x080690A8, {0: CTX, 1: root['script']['address']})
    def dispatch():
        return run(DISPATCH, {4: CTX, 2: rt.getmem(memory, CTX + 8, 4)}, 0x08069132)
    dispatch()
    need(rt.getmem(memory, CTX + 100, 4) == root['text_pointer'] and rt.getmem(memory, CTX + 8, 4) == root['script']['address'] + 6, '実LOADWORDが別textをdata0へstore')
    dispatch()
    need(rt.getmem(memory, CTX, 1) == 1 and rt.getmem(memory, CTX + 12, 4) == root['end_address'] and rt.getmem(memory, CTX + 8, 4) == STANDARD2, '実CALLSTD2が正しいreturn PCをpush')
    prefix_steps = len(visited)
    # 標準2完了時にもこのcontext/stackが保たれる、という条件を明示する独立probe。
    # PCを書換えて標準2を実行したように見せない。RETURN handlerを直接呼ぶ。
    run(0x08069888, {0: CTX})
    need(rt.getmem(memory, CTX, 1) == 0 and rt.getmem(memory, CTX + 8, 4) == root['end_address'], '実popで元のENDへ復帰')
    dispatch()
    need(rt.getmem(memory, CTX + 1, 1) == 0 and rt.getmem(memory, CTX + 8, 4) == 0, '実END/StopScriptがmode0/NULLを書込')
    need(0x08069184 in visited and 0x080690BE in visited and 0x080690C0 in visited, '実pop・stop writer到達')
    target_ranges = [(t['address'], t['address'] + t['size']) for t in TEXTS]
    need(not any(a < end and start < a + n for a, n in reads for start, end in target_ranges), '対象text consumerをprobeへ混入しない')
    return dict(owner_id=root['owner_id'], script=root['script']['address'], text_pointer=root['text_pointer'],
                standard_index=2, standard_script=STANDARD2, return_address=root['end_address'],
                prefix_machine_instructions=prefix_steps, conditional_terminal_machine_instructions=len(visited) - prefix_steps,
                standard_script_structural_commands=7, standard_handlers_executed=False,
                terminal_probe_entry='direct_return_handler_with_prefix_stack_preserved_after_assumed_standard_completion',
                actual_end_dispatch_executed=True, terminal_mode=0, terminal_script_pointer=0,
                target_text_bytes_consumed=0, valid_target_suffix_context_established=False,
                root_to_target_structural_path_found=False, all_other_roots_excluded=False)


def sources_bind(review, sources):
    need(set(sources) == set(SOURCE_IDS) and exact(review['source_bindings'], SOURCE_IDS), '固定公開source集合のみ')
    for key, row in SOURCE_IDS.items():
        raw = sources[key]
        need(identity(raw) == {k: row[k] for k in ('size', 'sha256')} and hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == row['git_blob_sha'], '公開source全文size/SHA/Gitblob')
    phrases = {'pret-scrcmd.c': [b'StopScript(ctx);', b'ScriptCall(ctx, *script);'],
               'pret-script.c': [b'ctx->mode = SCRIPT_MODE_STOPPED;', b'ctx->scriptPtr = NULL;', b'ctx->scriptPtr = ScriptPop(ctx);'],
               'pret-std_msgbox.inc': [b'Std_MsgboxNPC::\n\tlock\n\tfaceplayer\n\tmessage 0x0\n\twaitmessage\n\twaitbuttonpress\n\trelease\n\treturn'],
               'pret-event_scripts.s': [b'.4byte Std_MsgboxNPC            @ MSGBOX_NPC'],
               'pret-string_util.c': [b'[PLACEHOLDER_ID_STRING_VAR_2] = ExpandPlaceholder_StringVar2,', b'return gStringVar2;', b'GetExpandedPlaceholder(placeholderId)'],
               'pret-characters.h': [b'#define PLACEHOLDER_ID_STRING_VAR_2  0x3'],
               'BPRJ.ld': [b'gStringVar2 = 0x2021C60;', b'GetExpandedPlaceholder = 0x8008D5C | 1;', b'StopScript = 0x80690BC | 1;']}
    for key, required in phrases.items():
        need(all(phrase in sources[key] for phrase in required), '公開source構造/未完placeholder義務対照')


def protected_windows(review):
    need(exact(review['windows'], FIXED_WINDOWS), '最小保護窓の不変契約'); return copy.deepcopy(FIXED_WINDOWS)


def evidence_template(hit):
    raise ValueError('登録path/placeholder消費が未完のguardから型witnessを作成しない')


def witness_geometry(evidence):
    raise ValueError('未知維持guardは型領域を返さない')


def make_review(raw, hits):
    selected = [h for h in hits if h.get('address') in HITS]
    need([h['address'] for h in selected] == list(HITS), '未知1hitの順序/重複/欠落を検査')
    return dict(schema_version=1, required_candidate=copy.deepcopy(CANDIDATE), diagnostic_input=copy.deepcopy(DIAGNOSTIC),
                source_bindings=copy.deepcopy(SOURCE_IDS), hits=copy.deepcopy(selected), windows=copy.deepcopy(FIXED_WINDOWS),
                root=copy.deepcopy(ROOT), roots=copy.deepcopy(ROOTS), claims=copy.deepcopy(CLAIMS), input_contract=copy.deepcopy(CONTRACT),
                texts=copy.deepcopy(TEXTS), placeholder=copy.deepcopy(PLACEHOLDER), required_obligations=list(OBLIGATIONS), classified_hits=[])


def held_proof_template(current_candidate_measured=False):
    need(type(current_candidate_measured) is bool, '明示current測定boolean')
    return dict(status='PASS_EVENT_PLACEHOLDER_ONE_HIT_REMAINS_UNKNOWN', count=0, hits=[], held_hits=list(HITS),
                new_classified_bytes=0, source_bindings=copy.deepcopy(SOURCE_IDS), root=copy.deepcopy(ROOT),
                registration_paths=[dict(owner_id=r['owner_id'], script=r['script']['address'], registration_bound=True) for r in ROOTS],
                conditional_root_probes=copy.deepcopy(CASE_PROOFS), placeholder=copy.deepcopy(PLACEHOLDER),
                required_obligations=list(OBLIGATIONS), protected_windows=len(FIXED_WINDOWS),
                protected_bytes=sum(w['size'] for w in FIXED_WINDOWS), all_inherited_fields_unchanged=True,
                current_candidate_measured=current_candidate_measured, **copy.deepcopy(CLAIMS))


def validate_held_proof(proof, current_candidate_measured=False):
    need(exact(proof, held_proof_template(current_candidate_measured)), '閉じた未知維持proof、型/自然到達へ昇格しない'); return True


def _regions(raw, inherited, review, sources):
    selected = [h for h in inherited['hits'] if h.get('address') in HITS]
    need(exact(review, make_review(None, selected)), '不変review、余分field/改変再seal拒否')
    need(exact(inherited['candidate'], CANDIDATE), 'current/diagnostic分離')
    for hit in selected:
        need(type(hit['address']) is int and hit['accepted'] is False and hit['owner_candidates'] == [] and type(hit['size']) is int and hit['size'] == 4 and hit['classification'] == 'UNCLASSIFIED' and hit['kind'] == 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS', '同一のowner無し未知4byte')
        d.signed(raw, hit)
        need(type(hit['target']) is int and hit['target'] == d.canonical(d.u32(raw, hit['address'])), '未知hitの観測u32 metadata一致')
    protected_windows(review); sources_bind(review, sources); bind_semantics(raw)
    proof = held_proof_template()
    proof['registration_paths'] = [root_registration(raw, root) for root in ROOTS]
    proof['conditional_root_probes'] = [compose_selected(raw, root) for root in ROOTS]
    validate_held_proof(proof); return [], proof


def regions(raw, inherited, review, sources, root=None):
    need(identity(raw) == inherited['candidate'] == CANDIDATE, 'whole current必須、診断のみでcurrent昇格しない')
    rows, proof = _regions(raw, inherited, review, sources)
    proof['current_candidate_measured'] = True; validate_held_proof(proof, True); return rows, proof

# 実機械の決定論的metadataのみを固定。ROM断片やprivate pathは含めない。
CASE_PROOFS = [{'owner_id': 'OBJECT:3/10:0',
  'script': 135845930,
  'text_pointer': 141172340,
  'standard_index': 2,
  'standard_script': 135867792,
  'return_address': 135845938,
  'prefix_machine_instructions': 237,
  'conditional_terminal_machine_instructions': 50,
  'standard_script_structural_commands': 7,
  'standard_handlers_executed': False,
  'terminal_probe_entry': 'direct_return_handler_with_prefix_stack_preserved_after_assumed_standard_completion',
  'actual_end_dispatch_executed': True,
  'terminal_mode': 0,
  'terminal_script_pointer': 0,
  'target_text_bytes_consumed': 0,
  'valid_target_suffix_context_established': False,
  'root_to_target_structural_path_found': False,
  'all_other_roots_excluded': False},
 {'owner_id': 'OBJECT:23/0:0',
  'script': 135845874,
  'text_pointer': 141172985,
  'standard_index': 2,
  'standard_script': 135867792,
  'return_address': 135845882,
  'prefix_machine_instructions': 237,
  'conditional_terminal_machine_instructions': 50,
  'standard_script_structural_commands': 7,
  'standard_handlers_executed': False,
  'terminal_probe_entry': 'direct_return_handler_with_prefix_stack_preserved_after_assumed_standard_completion',
  'actual_end_dispatch_executed': True,
  'terminal_mode': 0,
  'terminal_script_pointer': 0,
  'target_text_bytes_consumed': 0,
  'valid_target_suffix_context_established': False,
  'root_to_target_structural_path_found': False,
  'all_other_roots_excluded': False}]
