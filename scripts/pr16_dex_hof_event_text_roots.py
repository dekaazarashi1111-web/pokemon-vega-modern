"""現map7/0 object0から有限script根・実LOADWORD/標準4/文字byte consumer。外部I/Oなし。"""
import copy,hashlib,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_reference_gaps as gaps
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_runtime_party as rt
need,identity,chunk=d.need,d.identity,d.chunk
exact=engine.exact
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
HITS=(0x0818034F,)
KIND='rooted_event_adjacent_text_consumption'
TYPE_CATEGORY='data'
CTX=0x02000010
ROOT=dict(kind='current_map_object_registered_conditional_script_text',group=7,map=0,object=0,script=0x08180141,map_literal=0x08054B0C,dispatch=0x08069118,loadword=0x08069B74,callstd=0x08069A40,message=0x0806B0CC,byte_consumer=0x08008B4E,stop_after_eos=0x08068D92)
CLAIMS=dict(proof_scope='conditional_registered_event_script_to_actual_text_byte_reads',root_verified=True,root_verification_scope='current_registration_and_script_structure_only',registered_root_runtime_execution_proven=False,valid_suffix_context_is_entry_condition=True,structural_prefix_only=True,prefix_handler_runtime_effects_proven=False,selected_producer_consumer_machine_executed=True,full_story_reachability_claimed=False,actual_runtime_execution_observed=False,full_renderer_claimed=False,universal_heap_or_irq_lifetime_proven=False,opaque_callee_effects_proven=False,source_pointer_interpretation=False,whole_text_classified=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT=dict(entry='Current map7/0 object0 selection supplies script08180141; natural map/object interaction reachability is a separate obligation.',prefix='固定script byte列のgrammarと有限edgeだけを検査する。Python source転送例は現ROM handlerの実行証明ではなく、contextを進めない。root_verifiedは現登録とscript構造だけを意味する。',special='固定source転送意味ではRESULT8/0が左右pathを選ぶ、という別々の条件例だけを確認する。現ROM special344/waitstateの効果、結果の生成、自然到達は証明しない。',handoff='実suffixの入口条件は、現登録script中の構造上validな選択command contextが得られていること。検証では実InitScriptContextとSetupScriptへ選択PCを渡し、その条件を具体化する。登録rootからruntimeで到達したとは扱わず、text pointerはseedしない。',consumer='Actual dispatcher, LOADWORD operand reader/data0 store, CALLSTD4 stack push/pointer store, message(NULL), ShowFieldMessage and StringExpandPlaceholders execute with message state0. Stop immediately after complete EOS expansion, before rendering helpers.',memory='Context, stack, expanded-text output and message-state storage are aligned, disjoint and live for each finite invocation. No allocation, free, IRQ or arbitrary external call occurs inside the selected producer/consumer prefix. Universal lifetime and asynchronous effects are outside scope.',minimum='Only the 4-byte hit0818034F is classified. Root/script/consumer code, literal/table cells and both complete texts are evidence only; no other region is excluded.')
SOURCE_IDS={'BPRJ.ld': {'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'path': 'BPRJ.ld',
             'size': 68505,
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51'},
 'pret-scrcmd.c': {'local': 'pret-scrcmd.c',
                   'repository': 'pret/pokefirered',
                   'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'path': 'src/scrcmd.c',
                   'size': 56954,
                   'sha256': '898dad5a07ce0a125731b998654d86808885a8d48163d607478a5e70c1cac553',
                   'git_blob_sha': '97b695ee2f6fca80a3b78f52f6a444f696fe5814'}}
TEXTS=[{'address': 135791417,
  'size': 25,
  'sha256': '76a0778a7185be0db018cfdc27ccef1c543ca89818c7d74633ceab80ac0e5f78',
  'owner_id': 'OBJECT:7/0:0',
  'target_script_root': 135790913,
  'root_chain': [{'address': 134564620,
                  'size': 4,
                  'sha256': 'd672c5b39141ec15b78c62a82995e610593e06bd92fe2cb5aa5434696139c61e',
                  'role': 'map_groups_literal',
                  'value': 153899412},
                 {'address': 153899440,
                  'size': 4,
                  'sha256': 'b52cc5bd6dd8d58fbbf3f123475a4fcf3087c9ea1d6e1f42ad05092aa32dcdbf',
                  'role': 'group_slot',
                  'value': 137454836},
                 {'address': 137454836,
                  'size': 4,
                  'sha256': '6dd960094da200c7b3721acbde49bc3923bc290640b3965c37335ad1fb5881ab',
                  'role': 'map_slot',
                  'value': 137449464},
                 {'address': 137449464,
                  'size': 8,
                  'sha256': '2c5cabff02c2439d5774153eea8007b0008501dcd81c56cb5d3da7ecfe25ac6b',
                  'role': 'map_header',
                  'events': 137880424},
                 {'address': 137880424,
                  'size': 8,
                  'sha256': '66cbf769970bf2fc1ee6b775b82fde892997393b9b0b0bfd477be2c21ae579be',
                  'role': 'event_header',
                  'objects': 137880368},
                 {'address': 137880368,
                  'size': 24,
                  'sha256': '1e08ca20282a366786010e37eb744507b085abd3f4ae9e25ab99c6b41e6f27b5',
                  'role': 'object_record',
                  'script': 135790913,
                  'script_field': 137880384}],
  'path': [{'address': 135790913,
            'size': 1,
            'sha256': '189f40034be7a199f1fa9891668ee3ab6049f82d38c68be70f596eab2e1857b7',
            'opcode': 106},
           {'address': 135790914,
            'size': 1,
            'sha256': 'bbeebd879e1dff6918546dc0c179fdde505f2a21591c9a9c96e36b054ec5af83',
            'opcode': 90},
           {'address': 135790915,
            'size': 6,
            'sha256': 'dc0f66c38f2bdbe2d11df8eb7f4e4563089ff9e9dfc5f4d72588d53997a327d9',
            'opcode': 15},
           {'address': 135790921,
            'size': 2,
            'sha256': 'f0f639189843668f480629df87f02cbef73dfc70d2e4e33b280ca7142827b314',
            'opcode': 9},
           {'address': 135790923,
            'size': 5,
            'sha256': '0e9de4aacdbeb8156adf57b76bb52133d118f724fe361edcc019c5696bd8a7a5',
            'opcode': 103},
           {'address': 135790928,
            'size': 1,
            'sha256': '252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111',
            'opcode': 102},
           {'address': 135790929,
            'size': 5,
            'sha256': '8beb2c90780307b6489410b6d320dd42e641269a220e84431d45a355cd284af1',
            'opcode': 22},
           {'address': 135790934,
            'size': 3,
            'sha256': '59f87a0bb0bd5395d6dc59417a0f9d54c595bd3d165c3777e7fb02e68f7222dc',
            'opcode': 37},
           {'address': 135790937,
            'size': 1,
            'sha256': '265fda17a34611b1533d8a281ff680dc5791b0ce0a11c25b35e11c8e75685509',
            'opcode': 39},
           {'address': 135790938,
            'size': 5,
            'sha256': 'c771907ee3b56d884ce9c1351c0ff345a26a7ea4dc0270339065b00c61004209',
            'opcode': 25},
           {'address': 135790943,
            'size': 5,
            'sha256': '4fb15658f90bee04d12b1e4f79c5c52a6f398511af4c7494db997e6dfabcde0b',
            'opcode': 33},
           {'address': 135790948,
            'size': 6,
            'sha256': 'c697832fda325e71e5a01fc1e765ec313cec0f21a307427925dac1b8421396ed',
            'opcode': 6},
           {'address': 135790954,
            'size': 5,
            'sha256': '2cacec105048e37b1948945ff8d911dcabf1134f58354329d8b40e76dd8243bc',
            'opcode': 33},
           {'address': 135790959,
            'size': 6,
            'sha256': '892d6b1b86fd70db406f48b77f207e542964cfc27fac31944e5485c65f1efef0',
            'opcode': 6},
           {'address': 135790965,
            'size': 5,
            'sha256': '33ef8da5017564b5800257927ca9045a8edd8eadd7b4239cec158c2b5f89d8e3',
            'opcode': 33},
           {'address': 135790970,
            'size': 6,
            'sha256': 'd88e8ccc549e9447317bc3d5168c0a6ca7a23ca28a43358f50d46714ed209f5c',
            'opcode': 6},
           {'address': 135790976,
            'size': 5,
            'sha256': '17bf3c52dc66f04ca78a556eccf14908e75cc17ad5b37868eb9e17b4fbccf682',
            'opcode': 33},
           {'address': 135790981,
            'size': 6,
            'sha256': '9d478c656c5407ac1df25be5fb7b7565e3e5990708b79d3d68690f936ad08ed6',
            'opcode': 6},
           {'address': 135790987,
            'size': 5,
            'sha256': '39d56fe466edefcd6a900f8c62c0c82e620c5e720bb2028e2ccfd4cf6655ab96',
            'opcode': 33},
           {'address': 135790992,
            'size': 6,
            'sha256': 'de1a7212cfbe5bff9b5d3e6ebcf73efb36e44c7bb2aca3a2db5c631043d0e4f6',
            'opcode': 6},
           {'address': 135790998,
            'size': 5,
            'sha256': 'd3f9c3833ef73a23efec34b27d25c4ff2781798826c5ad32193296eec7e0ed92',
            'opcode': 33},
           {'address': 135791003,
            'size': 6,
            'sha256': '116d638a662f178c9a2bbf359e793591df07711f90dc82f14be9a506ae842006',
            'opcode': 6},
           {'address': 135791009,
            'size': 5,
            'sha256': 'dc3a3c2a31990fb952890ca7c05907cb3b166f7c4a5abaa0c5da56f1996452dc',
            'opcode': 33},
           {'address': 135791014,
            'size': 6,
            'sha256': '6208274b0222bd53acc7e47efccd90b6429f27de134e7d8bf15012c50470ced3',
            'opcode': 6},
           {'address': 135791020,
            'size': 5,
            'sha256': '3a4328348e8d837e4d765d9d3bbfbc55b2d31eb739276009d7cd237a9563d3bd',
            'opcode': 33},
           {'address': 135791025,
            'size': 6,
            'sha256': 'b6a21356e4cda0eff96d33bba8963075670fd6256318426675cc89c0360e6178',
            'opcode': 6},
           {'address': 135791031,
            'size': 5,
            'sha256': '82d600a81316644e391a194358ad2ec6c4a8a8cdc588814291bbbfc4cac73ad1',
            'opcode': 33},
           {'address': 135791036,
            'size': 6,
            'sha256': '074ec238e8c7c532fd144f71cf98415fd85ae1abe429e4c431419e6a4794eb16',
            'opcode': 6},
           {'address': 135791292,
            'size': 6,
            'sha256': '4316040331c98cc1b2d5a7a0b3d1f9e4294e39c769d68f8a7ef9ab4dd5ab3ab7',
            'opcode': 15}],
  'loadword_and_callstd': {'address': 135791292,
                           'size': 8,
                           'sha256': '47daa67a8ce0c8a0f2af34cffda52f0beaa8882069a99f68f199fb2eac18ba8b',
                           'pointer': 135791417},
  'special_result': 8},
 {'address': 135791442,
  'size': 78,
  'sha256': '66cc1204dce7df3f36beec31468577d6d8d7bd3a7b3235f6cbcd9fe0795cda36',
  'owner_id': 'OBJECT:7/0:0',
  'target_script_root': 135790913,
  'root_chain': [{'address': 134564620,
                  'size': 4,
                  'sha256': 'd672c5b39141ec15b78c62a82995e610593e06bd92fe2cb5aa5434696139c61e',
                  'role': 'map_groups_literal',
                  'value': 153899412},
                 {'address': 153899440,
                  'size': 4,
                  'sha256': 'b52cc5bd6dd8d58fbbf3f123475a4fcf3087c9ea1d6e1f42ad05092aa32dcdbf',
                  'role': 'group_slot',
                  'value': 137454836},
                 {'address': 137454836,
                  'size': 4,
                  'sha256': '6dd960094da200c7b3721acbde49bc3923bc290640b3965c37335ad1fb5881ab',
                  'role': 'map_slot',
                  'value': 137449464},
                 {'address': 137449464,
                  'size': 8,
                  'sha256': '2c5cabff02c2439d5774153eea8007b0008501dcd81c56cb5d3da7ecfe25ac6b',
                  'role': 'map_header',
                  'events': 137880424},
                 {'address': 137880424,
                  'size': 8,
                  'sha256': '66cbf769970bf2fc1ee6b775b82fde892997393b9b0b0bfd477be2c21ae579be',
                  'role': 'event_header',
                  'objects': 137880368},
                 {'address': 137880368,
                  'size': 24,
                  'sha256': '1e08ca20282a366786010e37eb744507b085abd3f4ae9e25ab99c6b41e6f27b5',
                  'role': 'object_record',
                  'script': 135790913,
                  'script_field': 137880384}],
  'path': [{'address': 135790913,
            'size': 1,
            'sha256': '189f40034be7a199f1fa9891668ee3ab6049f82d38c68be70f596eab2e1857b7',
            'opcode': 106},
           {'address': 135790914,
            'size': 1,
            'sha256': 'bbeebd879e1dff6918546dc0c179fdde505f2a21591c9a9c96e36b054ec5af83',
            'opcode': 90},
           {'address': 135790915,
            'size': 6,
            'sha256': 'dc0f66c38f2bdbe2d11df8eb7f4e4563089ff9e9dfc5f4d72588d53997a327d9',
            'opcode': 15},
           {'address': 135790921,
            'size': 2,
            'sha256': 'f0f639189843668f480629df87f02cbef73dfc70d2e4e33b280ca7142827b314',
            'opcode': 9},
           {'address': 135790923,
            'size': 5,
            'sha256': '0e9de4aacdbeb8156adf57b76bb52133d118f724fe361edcc019c5696bd8a7a5',
            'opcode': 103},
           {'address': 135790928,
            'size': 1,
            'sha256': '252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111',
            'opcode': 102},
           {'address': 135790929,
            'size': 5,
            'sha256': '8beb2c90780307b6489410b6d320dd42e641269a220e84431d45a355cd284af1',
            'opcode': 22},
           {'address': 135790934,
            'size': 3,
            'sha256': '59f87a0bb0bd5395d6dc59417a0f9d54c595bd3d165c3777e7fb02e68f7222dc',
            'opcode': 37},
           {'address': 135790937,
            'size': 1,
            'sha256': '265fda17a34611b1533d8a281ff680dc5791b0ce0a11c25b35e11c8e75685509',
            'opcode': 39},
           {'address': 135790938,
            'size': 5,
            'sha256': 'c771907ee3b56d884ce9c1351c0ff345a26a7ea4dc0270339065b00c61004209',
            'opcode': 25},
           {'address': 135790943,
            'size': 5,
            'sha256': '4fb15658f90bee04d12b1e4f79c5c52a6f398511af4c7494db997e6dfabcde0b',
            'opcode': 33},
           {'address': 135790948,
            'size': 6,
            'sha256': 'c697832fda325e71e5a01fc1e765ec313cec0f21a307427925dac1b8421396ed',
            'opcode': 6},
           {'address': 135791180,
            'size': 6,
            'sha256': '3300fa5cc03755fc735601faf032436c3bb1af622b90218df28e93f57ac65ad3',
            'opcode': 15}],
  'loadword_and_callstd': {'address': 135791180,
                           'size': 8,
                           'sha256': '671650288496167955c6959088ba9830198a2939b7fdae5acb36f267f9472e65',
                           'pointer': 135791442},
  'special_result': 0}]
FIXED_WINDOWS=[{'address': 134253384, 'size': 40, 'sha256': '30d10a27a1e38e96fd10f8307f3dc347d16a9478d84262cea28f3c5fe4803e89'},
 {'address': 134253432, 'size': 8, 'sha256': 'a51810c3f7c76fcc13e9e4980b883ea07640899f55c0cd297b0e908318f730b1'},
 {'address': 134253602, 'size': 18, 'sha256': '0c52bde8b003f5c29e3c6dbabf8c9a92e8d2af32d07a8e4be3204e5da8d29441'},
 {'address': 134564620, 'size': 4, 'sha256': 'd672c5b39141ec15b78c62a82995e610593e06bd92fe2cb5aa5434696139c61e'},
 {'address': 134647036, 'size': 22, 'sha256': '21a453e96949a0d9fb5171661fa50c374d49700b967be503ebc44c7f1c33c427'},
 {'address': 134647064, 'size': 12, 'sha256': '3de38ec5f04c42bb9b8db33a7ea7670511adf96ff701dcf02c1e71fbd5c2b4d1'},
 {'address': 134647176, 'size': 10, 'sha256': 'c9c63ee2cd5ea4486328dff3525d3236a7a09633b08d878b6c5d61d52b1c50f4'},
 {'address': 134647200, 'size': 4, 'sha256': 'f31d45fbff05c0a5cdec5375dee92c4759c03f5fdf6bb34ee1808fb384a32f24'},
 {'address': 134647916, 'size': 58, 'sha256': '57fcbf4f792dfa30088f1d3753300eac4042bd545395b5e587b1acac5834ffba'},
 {'address': 134647976, 'size': 10, 'sha256': '8db31238fb6265cfa04f9be46b7ef134e68c38c3e7ed68c633ea30e42082ce1f'},
 {'address': 134648088, 'size': 26, 'sha256': 'c23e12489eeb9a5ddc85d4216365fb60541ae3b9d43eb3181fe4fa0b7ca84ace'},
 {'address': 134648132, 'size': 40, 'sha256': '9a74d64cab74b8806fe9edfaac5a440ede9a61760ceea7f75a3791ff197d7462'},
 {'address': 134648212, 'size': 20, 'sha256': '77ef01de4a48da25e8f463a63a684fc5799bab3168a85d936768641bd0129ac8'},
 {'address': 134648272, 'size': 48, 'sha256': '1d6f67baf6aff67172ec8c2580bdd5ab743a7224f461ff4e68431c1d9e105f2c'},
 {'address': 134648796, 'size': 8, 'sha256': '1a7270f8c3d75390c0acd8169220e2342ae02bb3bd5a67ce43085a2e8cd3b8b1'},
 {'address': 134650432, 'size': 38, 'sha256': 'a56ab43f56bba187706c31510aa5bd742c77459127cba73001da353919fc3841'},
 {'address': 134650472, 'size': 8, 'sha256': 'b4cdb095c5a7cbb104afc8e9e7acb6439f60636ff45687974cb51b720f0ad173'},
 {'address': 134650740, 'size': 34, 'sha256': '6632a06bebc6c051ba0f1d400cb47767a9237d0bd2dcee6a9023e04b2a227b61'},
 {'address': 134656204, 'size': 26, 'sha256': 'ffd9c927490654600bb682ee6c17dbb27b44e381204466610ee88937136bdb5c'},
 {'address': 135671016, 'size': 4, 'sha256': '25dd52f3be6308884dd9180d47a4ca1860449f2bd0827e3b52dd0541da6c8476'},
 {'address': 135671040, 'size': 4, 'sha256': '589e15f487c95a94b42e75dd09c3ea3952ed1ad18639243d8b79d3f81e599983'},
 {'address': 135671392, 'size': 4, 'sha256': '920c41671abfc966bc6788c9868829592c7bfb3c951dc31e5dcc78f5e11a1d46'},
 {'address': 135673704, 'size': 4, 'sha256': '7cc413b64c6552062304957e0f82c5297595d5c4ce0e1eddb78feaa06a6f2aa9'},
 {'address': 135790913, 'size': 129, 'sha256': 'a490ab3bffae58f1f0c2a11ab4fba179bead5bf01eb43d9f8ba7189aae9ba43b'},
 {'address': 135791180, 'size': 8, 'sha256': '671650288496167955c6959088ba9830198a2939b7fdae5acb36f267f9472e65'},
 {'address': 135791292, 'size': 8, 'sha256': '47daa67a8ce0c8a0f2af34cffda52f0beaa8882069a99f68f199fb2eac18ba8b'},
 {'address': 135791417, 'size': 103, 'sha256': '738619c3b8ed5364a2b7db932fb8f08d10ad7f5b8a3d3a5212e5af5ef3a2e986'},
 {'address': 135867813, 'size': 8, 'sha256': 'f740301a394637a38744ce56918c9b5334c317b0e3ac36424549fef8b66166db'},
 {'address': 136084172, 'size': 2, 'sha256': 'bac8ca6ee9f77b46c7ab5824c7c59d99fd0ca53ae998ea2872b78bb6a5189cc5'},
 {'address': 137449464, 'size': 8, 'sha256': '2c5cabff02c2439d5774153eea8007b0008501dcd81c56cb5d3da7ecfe25ac6b'},
 {'address': 137454836, 'size': 4, 'sha256': '6dd960094da200c7b3721acbde49bc3923bc290640b3965c37335ad1fb5881ab'},
 {'address': 137880368, 'size': 24, 'sha256': '1e08ca20282a366786010e37eb744507b085abd3f4ae9e25ab99c6b41e6f27b5'},
 {'address': 137880424, 'size': 8, 'sha256': '66cbf769970bf2fc1ee6b775b82fde892997393b9b0b0bfd477be2c21ae579be'},
 {'address': 153899440, 'size': 4, 'sha256': 'b52cc5bd6dd8d58fbbf3f123475a4fcf3087c9ea1d6e1f42ad05092aa32dcdbf'}]
LITERALS={134650472: 135673688,
 134650476: 135673728,
 134647064: 33779664,
 134647200: 33692808,
 134253412: 134253416,
 134648796: 135670980,
 134648800: 135671824,
 135671040: 134650741,
 135671016: 134650433,
 135671392: 134656205,
 135673704: 135867813,
 134253416: 134253602,
 134253420: 134253602,
 134253432: 134253602,
 134253436: 134253608}
SPECS=[(134647916, 'push', (0, True)),
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
 (134656204, 'push', (16, True)),
 (134656206, 'addi', (4, 0, 0)),
 (134656208, 'call', (134648272,)),
 (134656212, 'imm', ('cmp', 0, 0)),
 (134656214, 'branch', (1, 134656218)),
 (134656216, 'mem', (True, 'word', 0, 4, 100)),
 (134656218, 'call', (134647036,)),
 (134656222, 'imm', ('mov', 0, 0)),
 (134656224, 'pop', (16, False)),
 (134656226, 'pop', (2, False)),
 (134656228, 'bx', (1,)),
 (134647036, 'push', (16, True)),
 (134647038, 'addi', (1, 0, 0)),
 (134647040, 'literal', (4, 134647064)),
 (134647042, 'mem', (True, 'byte', 0, 4, 0)),
 (134647044, 'imm', ('cmp', 0, 0)),
 (134647046, 'branch', (1, 134647068)),
 (134647048, 'addi', (0, 1, 0)),
 (134647050, 'call', (134647176,)),
 (134647054, 'imm', ('mov', 0, 2)),
 (134647056, 'mem', (False, 'byte', 0, 4, 0)),
 (134647068, 'imm', ('mov', 0, 0)),
 (134647070, 'pop', (16, False)),
 (134647072, 'pop', (2, False)),
 (134647074, 'bx', (1,)),
 (134647176, 'push', (0, True)),
 (134647178, 'addi', (1, 0, 0)),
 (134647180, 'literal', (0, 134647200)),
 (134647182, 'call', (134253384,)),
 (134253384, 'push', (48, True)),
 (134253386, 'addi', (4, 0, 0)),
 (134253388, 'addi', (5, 1, 0)),
 (134253390, 'mem', (True, 'byte', 2, 5, 0)),
 (134253392, 'imm', ('add', 5, 1)),
 (134253394, 'addi', (0, 2, 0)),
 (134253396, 'imm', ('sub', 0, 250)),
 (134253398, 'imm', ('cmp', 0, 5)),
 (134253400, 'branch', (8, 134253602)),
 (134253402, 'shift', ('lsl', 0, 0, 2)),
 (134253404, 'literal', (1, 134253412)),
 (134253406, 'add', (0, 0, 1)),
 (134253408, 'mem', (True, 'word', 0, 0, 0)),
 (134253410, 'movhi', (15, 0)),
 (134253602, 'mem', (False, 'byte', 2, 4, 0)),
 (134253604, 'imm', ('add', 4, 1)),
 (134253606, 'jump', (134253390,)),
 (134253608, 'imm', ('mov', 0, 255)),
 (134253610, 'mem', (False, 'byte', 0, 4, 0)),
 (134253612, 'addi', (0, 4, 0)),
 (134253614, 'pop', (48, False)),
 (134253616, 'pop', (2, False)),
 (134253618, 'bx', (1,))]
INS={a:party.Ins(a,k,args)for a,k,args in SPECS}
BLOCKS={'event_producer_and_byte_consumer':tuple(INS.values())}
WINDOWS={f'event_text_window_{j}':(r['address'],r['size'])for j,r in enumerate(FIXED_WINDOWS)}
encoded=engine.encoded

class Machine(rt.Machine):
 def __init__(self,*args,**kw):super().__init__(*args,**kw);self.byte_reads=[];self.visited=[]
 def read(self,a,n):
  v=super().read(a,n)
  if self.pc==ROOT['byte_consumer']:self.byte_reads.append((a,n))
  return v
 def step(self,*args,**kw):self.visited.append(self.pc);return super().step(*args,**kw)

def bind_semantics(raw):
 d.signed(raw,FIXED_WINDOWS)
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'exact event consumer instruction '+hex(i.address))
 for a,value in LITERALS.items():need(d.u32(raw,a)==value,'exact event consumer literal '+hex(a))
 for op,entry in((15,ROOT['loadword']),(9,ROOT['callstd']),(103,ROOT['message'])):
  need(d.u32(raw,0x08162CC4+4*op)==entry|1,'actual selected JP dispatch slot')
 std=d.u32(raw,0x08163768)
 need(std==0x08192DA5 and chunk(raw,std,8)==bytes((103,0,0,0,0,102,109,3)),'actual complete standard4 messageNULL/wait/return')
 for text in TEXTS:
  b=chunk(raw,text['address'],text['size']);need(b[-1]==255 and 255 not in b[:-1]and not set(b)&{248,249,252,253},'complete scalar/single-byte-control text with final EOS only')


def conditional_prefix(raw,text,result=None,completes=True):
 need(completes is True,'declared prefix completion boundaries')
 need(result is None or type(result)is int and result==text['special_result'],'exact conditional special result')
 result=text['special_result'];variables={};comparison=None;steps=[]
 need(text['target_script_root']==ROOT['script'],'only fixed registered script grammar')
 gaps.text_root(raw,text)
 pc=text['target_script_root']
 for row in text['path']:
  need(pc==row['address'],'source grammar path starts at registered root and advances exactly; no runtime context write')
  op=chunk(raw,pc,1)[0];n=row['size'];nxt=pc+n;value=chunk(raw,pc,n)
  def half(at):return int.from_bytes(value[at:at+2],'little')
  if pc==text['loadword_and_callstd']['address']:
   need(op==15,'conditional prefix stops before selected real LOADWORD producer');return dict(instructions=len(steps),source_condition_result=result,selected_pc=pc,branch_count=sum(1 for r in steps if r['opcode']==6),context_writes=0,runtime_reachability_proven=False)
  if op==22:need((half(1),half(3))==(0x8004,0),'exact setup variable');variables[half(1)]=half(3)
  elif op==37:need(half(1)==344,'only selected opaque special344')
  elif op==39:variables[0x800D]=result
  elif op==25:need((half(1),half(3))==(0x8000,0x800D)and half(3)in variables,'declared result copied through exact source operation');variables[half(1)]=variables[half(3)]
  elif op==33:
   need(half(1)in variables,'comparison reads produced variable');a,b=variables[half(1)],half(3);comparison=0 if a<b else 1 if a==b else 2
  elif op==6:
   need(value[1]==1 and comparison is not None,'selected equality condition with produced comparison')
   if comparison==1:nxt=int.from_bytes(value[2:6],'little')
  else:need(op in(106,90,15,9,103,102),'only listed conditional UI completion boundary')
  steps.append(dict(address=pc,opcode=op,next=nxt));pc=nxt
 need(False,'selected producer must be reached')


def consume_selected(raw,text,result=None,message_state=0,completes=True,context_override=None):
 need(type(message_state)is int and message_state==0,'idle message state is an explicit prerequisite')
 need(context_override is None,'caller cannot substitute selected text/context producer fields')
 mem={};reads=[];visited=[];events=[]
 def run(entry,regs,stop=0xFFFFFFF0):
  nonlocal mem
  m=Machine(raw,entry,regs,mem,instructions=INS)
  while m.pc!=stop:
   need(m.pc in INS,'no unmodeled callee inside selected producer/consumer prefix');m.step()
  mem=m.mem;reads.extend(m.byte_reads);visited.extend(m.visited);events.extend(m.writes)
  if stop in(0xFFFFFFF0,0x08069132):need(m.reg[13]==0x03007000,'balanced selected producer return')
  else:need(stop==ROOT['stop_after_eos']and m.reg[13]==0x03007000-20,'fixed three live caller frames at pre-render stop')
  return m
 prefix=conditional_prefix(raw,text,result,completes)
 # 条件付きsuffix入口の具体化。登録rootからruntimeで到達したという主張ではない。
 run(0x0806906C,{0:CTX,1:d.u32(raw,0x080693DC),2:d.u32(raw,0x080693E0)})
 run(0x080690A8,{0:CTX,1:prefix['selected_pc']})
 rt.setmem(mem,0x02036FD0,1,message_state)
 # Each opcode is fetched and dispatched by actual JP instructions. No selected pointer is injected.
 def dispatch(stop=0x08069132):return run(ROOT['dispatch'],{4:CTX,2:rt.getmem(mem,CTX+8,4)},stop)
 dispatch();need(rt.getmem(mem,CTX+100,4)==text['address']and rt.getmem(mem,CTX+8,4)==prefix['selected_pc']+6,'actual LOADWORD index0 writer creates exact text pointer')
 dispatch();need(rt.getmem(mem,CTX,1)==1 and rt.getmem(mem,CTX+12,4)==prefix['selected_pc']+8 and rt.getmem(mem,CTX+8,4)==0x08192DA5,'actual bounded CALLSTD4 pushes return and produces standard script pointer')
 dispatch(ROOT['stop_after_eos'])
 expected=[(text['address']+j,1)for j in range(text['size'])]
 need(reads==expected,'actual LDRB consumes every text byte including EOS in order')
 need(bytes(rt.getmem(mem,0x02021C88+j,1)for j in range(text['size']))==chunk(raw,text['address'],text['size']),'actual expansion output copies all scalar/control bytes including EOS')
 need(0x08069B8C in visited and 0x080691A0 in visited and 0x0806B0D8 in visited and 0x08008C2A in visited,'selected data0 store, standard pointer store, NULL fallback and EOS output execute')
 return dict(source_structural_prefix=prefix,valid_command_context_assumed=True,registered_root_runtime_execution_proven=False,executed_instructions=len(visited),byte_reads=len(reads),read_trace_identity=identity(json.dumps(reads,separators=(',',':')).encode()),includes_eos=True,stopped_before_display_helpers=True)


def compose_selected(raw,**kwargs):
 proofs=[consume_selected(raw,t,**kwargs)for t in TEXTS]
 return dict(status='PASS_TWO_CONDITIONAL_REGISTERED_EVENT_TEXT_CONSUMERS',invocations=proofs,complete_consumed_bytes=sum(t['size']for t in TEXTS),classified_bytes=4,actual_byte_consumer=ROOT['byte_consumer'],source_prefix_conditions=[t['special_result']for t in TEXTS],actual_runtime_execution_observed=False)


def protected_windows(review):
 need(exact(review['windows'],FIXED_WINDOWS),'immutable minimum event text evidence windows');return copy.deepcopy(FIXED_WINDOWS)

def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'closed fixed public source identities')
 for key,row in SOURCE_IDS.items():
  b=sources[key];need(identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'whole pinned source identity '+key)
 need(b'ScriptReadWord = 0x080691D0' in sources['BPRJ.ld']and b'StringExpandPlaceholders = 0x8008B48'in sources['BPRJ.ld'],'fixed JP consumer roles')
 source=sources['pret-scrcmd.c']
 for phrase in(b'ctx->data[index] = ScriptReadWord(ctx);',b'ScriptCall(ctx, *script);',b'if (sScriptConditionTable[condition][ctx->comparisonResult] == 1)',b'*destPtr = *srcPtr;',b'ctx->comparisonResult = Compare(value1, value2);'):
  need(phrase in source,'fixed source prefix/producer semantics')

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'only selected exact event hit')
 return dict(root=copy.deepcopy(ROOT),classified_window=dict(address=hit,size=4),texts=[{k:t[k]for k in('address','size','sha256')}for t in TEXTS],all_hit_bytes_consumed=True,includes_complete_eos=True,**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
 need(type(evidence)is dict and type(evidence.get('classified_window'))is dict,'closed event text witness');hit=evidence['classified_window'].get('address')
 need(type(hit)is int and hit in HITS and exact(evidence,evidence_template(hit)),'immutable exact minimum event text evidence');return hit,4

def make_review(raw,hits):
 by={h['address']:h for h in hits};need(all(h in by for h in HITS),'exact selected unknown supplied')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hits=[copy.deepcopy(by[h])for h in HITS],root=copy.deepcopy(ROOT),windows=copy.deepcopy(FIXED_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),texts=copy.deepcopy(TEXTS))

def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','texts'},'closed event review')
 need(type(review['schema_version'])is int and review['schema_version']==1,'exact event schema version')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'current/diagnostic identities remain separate')
 for key,expected in(('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('texts',TEXTS)):need(exact(review[key],expected),'exact conditional event '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(len(selected)==1 and [h['address']for h in selected]==list(HITS)and exact(selected,review['hits']),'same exact single inherited unknown')
 for h in selected:
  need(h['accepted']is False and h['owner_candidates']==[]and type(h['size'])is int and h['size']==4 and h['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','unowned unknown4byte hit');d.signed(raw,h)
 need(TEXTS[0]['address']+TEXTS[0]['size']==TEXTS[1]['address']==HITS[0]+3,'one exact left-final3/right-first1 crossing')
 protected_windows(review);sources_bind(review,sources);bind_semantics(raw)
 roots=[gaps.text_root(raw,t)for t in TEXTS];proof=compose_selected(raw)
 evidence=evidence_template(HITS[0]);a,n=witness_geometry(evidence)
 return [d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_CONDITIONAL_ROOTED_EVENT_TEXT_WINDOW',count=1,hits=list(HITS),root_paths=roots,composition=proof,protected_windows=len(FIXED_WINDOWS),protected_bytes=sum(w['size']for w in FIXED_WINDOWS),source_bindings=copy.deepcopy(SOURCE_IDS),**CLAIMS)

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current mandatory; diagnostic cannot classify current');return _regions(raw,inherited,review,sources)
